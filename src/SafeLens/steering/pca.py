"""Paired PCA steering vectors built from positive-minus-negative activations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from SafeLens.core.base import LayerRef, ModelWrapper
from SafeLens.steering.contrastive import ContrastiveSteeringVector, _ActivationHelper


class PCASteeringVector(ContrastiveSteeringVector):
    """Top uncentered principal direction of paired activation differences.

    For every aligned positive/negative pair this method computes ``h+ - h-``,
    stacks those differences as rows, and takes the first right singular vector.
    The vector is sign-aligned with the mean difference and therefore points
    toward the positive examples. The resulting vector has unit norm.
    """

    @classmethod
    def fit(
        cls,
        model: ModelWrapper,
        dataset: Sequence[Mapping[str, Any]],
        *,
        layer: LayerRef,
        label_key: str = "label",
        positive_label: Any = 1,
        pair_key: str | None = None,
        split_key: str = "split",
        train_split: Any = None,
        activation_reduce: str = "last_token",
    ) -> PCASteeringVector:
        """Fit PCA steering from one labeled dataset.

        When ``pair_key`` is provided, every pair value must occur exactly once
        with the positive label and once with a negative label. Without a pair
        key, positive and negative rows are paired in their respective input
        order and their counts must match.
        """
        rows = [
            row
            for row in dataset
            if train_split is None or row.get(split_key) == train_split
        ]
        if pair_key is None:
            positives = [row for row in rows if row.get(label_key) == positive_label]
            negatives = [row for row in rows if row.get(label_key) != positive_label]
            pairing = "class_order"
        else:
            positives, negatives = _paired_rows(
                rows,
                label_key=label_key,
                positive_label=positive_label,
                pair_key=pair_key,
            )
            pairing = f"key:{pair_key}"

        steering = cls.fit_pairs(
            model,
            positives,
            negatives,
            layer=layer,
            activation_reduce=activation_reduce,
        )
        steering.metadata.update(
            {
                "label_key": label_key,
                "positive_label": positive_label,
                "pair_key": pair_key,
                "pairing": pairing,
                "split_key": split_key,
                "train_split": train_split,
            }
        )
        return steering

    @classmethod
    def fit_pairs(
        cls,
        model: ModelWrapper,
        positive_rows: Sequence[Mapping[str, Any]],
        negative_rows: Sequence[Mapping[str, Any]],
        *,
        layer: LayerRef,
        activation_reduce: str = "last_token",
    ) -> PCASteeringVector:
        """Fit PCA steering from explicitly aligned positive and negative rows."""
        if not positive_rows or not negative_rows:
            raise ValueError("PCA steering requires at least one positive/negative pair")
        if len(positive_rows) != len(negative_rows):
            raise ValueError(
                "PCA steering requires equal positive and negative counts; "
                f"found {len(positive_rows)} and {len(negative_rows)}"
            )

        helper = _ActivationHelper(layer=layer, activation_reduce=activation_reduce)
        positives: list[Any] = []
        negatives: list[Any] = []
        for index, (positive_row, negative_row) in enumerate(
            zip(positive_rows, negative_rows, strict=True)
        ):
            positive = helper.activation_from_model(model, positive_row)
            negative = helper.activation_from_model(model, negative_row)
            if positive is None or negative is None:
                raise ValueError(f"Could not capture both activations for PCA pair {index}")
            positives.append(positive)
            negatives.append(negative)

        vector, diagnostics = _pca_direction_with_diagnostics(positives, negatives)
        return cls(
            layer=layer,
            vector=vector,
            activation_reduce=activation_reduce,
            metadata={
                "method": "pca_minus_neg",
                "positive_count": len(positives),
                "negative_count": len(negatives),
                "pair_count": len(positives),
                "centered": False,
                "normalized": True,
                "sign_aligned_to_mean": True,
                **diagnostics,
            },
        )


def pca_direction_from_pairs(
    positive_activations: Sequence[Any],
    negative_activations: Sequence[Any],
) -> Any:
    """Return the unit PCA-minus-negative direction for aligned activations."""
    vector, _diagnostics = _pca_direction_with_diagnostics(
        positive_activations,
        negative_activations,
    )
    return vector


def _paired_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    label_key: str,
    positive_label: Any,
    pair_key: str,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    pairs: dict[Any, dict[str, Mapping[str, Any]]] = {}
    order: list[Any] = []
    for index, row in enumerate(rows):
        if pair_key not in row:
            raise ValueError(f"PCA dataset row {index} is missing pair key {pair_key!r}")
        pair_id = row[pair_key]
        try:
            bucket = pairs.get(pair_id)
            if bucket is None:
                bucket = {}
                pairs[pair_id] = bucket
                order.append(pair_id)
        except TypeError as exc:
            raise ValueError(f"PCA pair key {pair_key!r} must contain hashable values") from exc
        side = "positive" if row.get(label_key) == positive_label else "negative"
        if side in bucket:
            raise ValueError(f"PCA pair {pair_id!r} has more than one {side} row")
        bucket[side] = row

    positives: list[Mapping[str, Any]] = []
    negatives: list[Mapping[str, Any]] = []
    for pair_id in order:
        bucket = pairs[pair_id]
        if set(bucket) != {"positive", "negative"}:
            raise ValueError(f"PCA pair {pair_id!r} must contain one positive and one negative row")
        positives.append(bucket["positive"])
        negatives.append(bucket["negative"])
    return positives, negatives


def _pca_direction_with_diagnostics(
    positive_activations: Sequence[Any],
    negative_activations: Sequence[Any],
) -> tuple[Any, dict[str, float]]:
    if not positive_activations or not negative_activations:
        raise ValueError("PCA steering requires at least one positive/negative pair")
    if len(positive_activations) != len(negative_activations):
        raise ValueError(
            "PCA steering requires equal positive and negative activation counts; "
            f"found {len(positive_activations)} and {len(negative_activations)}"
        )
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "PCA steering requires PyTorch; install SafeLens with the models extra"
        ) from exc

    positives = [_as_flat_float_tensor(value, torch) for value in positive_activations]
    negatives = [_as_flat_float_tensor(value, torch) for value in negative_activations]
    expected_shape = positives[0].shape
    if any(value.shape != expected_shape for value in [*positives, *negatives]):
        raise ValueError("All PCA steering activations must have the same final shape")

    differences = torch.stack(positives) - torch.stack(negatives)
    mean_difference = differences.mean(dim=0)
    _u, singular_values, vh = torch.linalg.svd(differences, full_matrices=False)
    vector = vh[0]
    alignment = float(torch.dot(vector, mean_difference).item())
    if alignment < 0:
        vector = -vector
        alignment = -alignment
    mean_norm = float(mean_difference.norm().item())
    cosine = alignment / mean_norm if mean_norm > 0 else 0.0
    return vector, {
        "top_singular_value": float(singular_values[0].item()),
        "cosine_to_mean_difference": cosine,
    }


def _as_flat_float_tensor(value: Any, torch: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.detach().float().cpu().reshape(-1)
    return torch.as_tensor(value, dtype=torch.float32).reshape(-1)
