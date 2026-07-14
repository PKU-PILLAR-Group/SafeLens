"""Contrastive steering vectors built from positive and negative activations."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, TypeAlias, cast

from SafeLens.core.base import LayerRef, ModelWrapper

SteeringPosition: TypeAlias = str | tuple[int, int]


class ContrastiveSteeringVector:
    """Mean-positive-minus-mean-negative activation steering vector."""

    def __init__(
        self,
        *,
        layer: LayerRef,
        vector: Any,
        activation_reduce: str = "last_token",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.layer = layer
        self.vector = vector
        self.activation_reduce = activation_reduce
        self.metadata = dict(metadata or {})

    @classmethod
    def fit(
        cls,
        model: ModelWrapper,
        dataset: Sequence[Mapping[str, Any]],
        *,
        layer: LayerRef,
        label_key: str = "label",
        positive_label: Any = 1,
        split_key: str = "split",
        train_split: Any = None,
        activation_reduce: str = "last_token",
        normalize: bool = True,
    ) -> ContrastiveSteeringVector:
        """Build a steering vector from labeled text/prompt rows."""
        positives: list[Any] = []
        negatives: list[Any] = []
        helper = _ActivationHelper(layer=layer, activation_reduce=activation_reduce)

        for row in dataset:
            if train_split is not None and row.get(split_key) != train_split:
                continue
            activation = helper.activation_from_model(model, row)
            if activation is None:
                continue
            if row.get(label_key) == positive_label:
                positives.append(activation)
            else:
                negatives.append(activation)

        if not positives or not negatives:
            raise ValueError(
                "contrastive steering requires at least one positive and one negative sample"
            )

        vector = _subtract_values(_mean_values(positives), _mean_values(negatives))
        if normalize:
            vector = _normalize_value(vector)
        return cls(
            layer=layer,
            vector=vector,
            activation_reduce=activation_reduce,
            metadata={
                "method": "contrastive_mean_difference",
                "positive_count": len(positives),
                "negative_count": len(negatives),
                "label_key": label_key,
                "positive_label": positive_label,
                "split_key": split_key,
                "train_split": train_split,
                "normalized": normalize,
            },
        )

    @classmethod
    def load(cls, path: str | Path) -> ContrastiveSteeringVector:
        """Load a saved steering vector JSON file."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            layer=payload["layer"],
            vector=payload["vector"],
            activation_reduce=payload.get("activation_reduce", "last_token"),
            metadata=payload.get("metadata", {}),
        )

    def save(self, path: str | Path) -> None:
        """Save the steering vector as JSON."""
        payload = {
            "layer": self.layer,
            "vector": _to_jsonable(self.vector),
            "activation_reduce": self.activation_reduce,
            "metadata": self.metadata,
        }
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def apply(
        self,
        model: ModelWrapper,
        *,
        scale: float = 1.0,
        position: SteeringPosition = "all",
        layer: LayerRef | None = None,
        prepend: bool = False,
    ) -> Any:
        """Install a forward hook that adds this vector to the target activation."""
        target_layer = self.layer if layer is None else layer

        def hook(activation: Any = None, **kwargs: Any) -> Any:
            value = kwargs.get("activation", activation)
            return add_steering_vector(value, self.vector, scale=scale, position=position)

        return model.add_hook(target_layer, hook, prepend=prepend)

    def generate(
        self,
        model: ModelWrapper,
        prompt: Any,
        *,
        scale: float = 1.0,
        position: SteeringPosition = "all",
        remove_after: bool = True,
        **generation_kwargs: Any,
    ) -> Any:
        """Generate with a temporary steering hook."""
        handle = self.apply(model, scale=scale, position=position)
        try:
            return model.generate(prompt, **generation_kwargs)
        finally:
            if remove_after:
                handle.remove()


def add_steering_vector(
    activation: Any,
    vector: Any,
    *,
    scale: float = 1.0,
    position: SteeringPosition = "all",
) -> Any:
    """Return activation plus a steering vector, preserving common tensor backends."""
    if activation is None:
        return None
    if _is_torch_tensor(activation):
        return _add_torch_vector(activation, vector, scale=scale, position=position)
    return _add_python_vector(activation, vector, scale=scale, position=position)


class _ActivationHelper:
    def __init__(self, *, layer: LayerRef, activation_reduce: str) -> None:
        self.layer = layer
        self.activation_reduce = activation_reduce

    def activation_from_model(self, model: ModelWrapper, row: Mapping[str, Any]) -> Any | None:
        _output, cache = model.run_with_cache(row, layers=[self.layer])
        activation = self._activation_from_cache(cache)
        if activation is None:
            return None
        return self.reduce_activation(activation)

    def _activation_from_cache(self, cache: Any) -> Any | None:
        cache_dict = _cache_to_dict(cache)
        if not cache_dict:
            return None
        layer_text = str(self.layer)
        for key, value in cache_dict.items():
            if str(key) == layer_text:
                return value
        return next(reversed(cache_dict.values()))

    def reduce_activation(self, activation: Any) -> Any:
        shape = getattr(activation, "shape", None)
        if shape is not None:
            rank = len(shape)
            if self.activation_reduce == "mean":
                mean = getattr(activation, "mean", None)
                if callable(mean) and rank >= 2:
                    dims = tuple(range(rank - 1))
                    if "torch" in type(activation).__module__:
                        return mean(dim=dims)
                    return mean(axis=dims)
            if self.activation_reduce == "last_token" and rank >= 3:
                return activation[0, -1, :]
            if self.activation_reduce == "last_token" and rank >= 2:
                return activation[-1, :]
            return activation

        if self.activation_reduce == "mean":
            rows = _flatten_rows(activation)
            return _mean_python_vectors(rows) if rows else activation
        if self.activation_reduce == "last_token":
            return _last_nested_vector(activation)
        return activation


def _cache_to_dict(cache: Any) -> dict[Any, Any]:
    to_dict = getattr(cache, "to_dict", None)
    if callable(to_dict):
        result = to_dict()
        if isinstance(result, Mapping):
            return dict(result)
        try:
            return dict(cast(Iterable[tuple[Any, Any]], result))
        except TypeError:
            return {}
    if isinstance(cache, Mapping):
        return dict(cache)
    items = getattr(cache, "items", None)
    if callable(items):
        try:
            return dict(cast(Iterable[tuple[Any, Any]], items()))
        except TypeError:
            return {}
    return {}


def _mean_values(values: Sequence[Any]) -> Any:
    first = values[0]
    if _is_torch_tensor(first):
        torch = _torch_module()
        stacked = torch.stack([_as_torch_value(value, first) for value in values])
        return stacked.mean(dim=0)
    return _mean_python_vectors([_as_python_vector(value) for value in values])


def _subtract_values(left: Any, right: Any) -> Any:
    if _is_torch_tensor(left):
        right_value = _as_torch_value(right, left)
        return left - right_value
    return [float(a) - float(b) for a, b in zip(left, right, strict=True)]


def _normalize_value(value: Any) -> Any:
    if _is_torch_tensor(value):
        norm = value.norm()
        if float(norm.detach().cpu().item()) == 0.0:
            return value
        return value / norm
    norm = math.sqrt(sum(float(item) * float(item) for item in value))
    if norm == 0.0:
        return value
    return [float(item) / norm for item in value]


def _add_torch_vector(
    activation: Any,
    vector: Any,
    *,
    scale: float,
    position: SteeringPosition,
) -> Any:
    vector_tensor = _as_torch_value(vector, activation).to(
        device=activation.device,
        dtype=activation.dtype,
    )
    if position == "all":
        return activation + scale * vector_tensor
    if position == "last_token":
        patched = activation.clone()
        if patched.ndim >= 3:
            patched[:, -1, :] = patched[:, -1, :] + scale * vector_tensor
        elif patched.ndim >= 2:
            patched[-1, :] = patched[-1, :] + scale * vector_tensor
        else:
            patched = patched + scale * vector_tensor
        return patched
    if isinstance(position, tuple):
        start, end = _validate_position_range(position)
        patched = activation.clone()
        sequence_axis = -2 if patched.ndim >= 2 else None
        if sequence_axis is None or start >= patched.shape[sequence_axis]:
            return patched
        bounded_end = min(end, int(patched.shape[sequence_axis]))
        if patched.ndim >= 3:
            patched[:, start:bounded_end, :] += scale * vector_tensor
        elif patched.ndim == 2:
            patched[start:bounded_end, :] += scale * vector_tensor
        else:
            patched += scale * vector_tensor
        return patched
    raise ValueError("position must be 'all', 'last_token', or a (start, end) range")


def _add_python_vector(
    activation: Any,
    vector: Any,
    *,
    scale: float,
    position: SteeringPosition,
) -> Any:
    vector_values = _as_python_vector(vector)
    if position == "all":
        return _add_vector_to_all_final_vectors(activation, vector_values, scale)
    if position == "last_token":
        return _add_vector_to_last_final_vector(activation, vector_values, scale)
    if isinstance(position, tuple):
        start, end = _validate_position_range(position)
        return _add_vector_to_position_range(activation, vector_values, scale, start, end)
    raise ValueError("position must be 'all', 'last_token', or a (start, end) range")


def _validate_position_range(position: tuple[int, int]) -> tuple[int, int]:
    start, end = position
    if start < 0 or end <= start:
        raise ValueError("position range must satisfy 0 <= start < end")
    return start, end


def _add_vector_to_position_range(
    value: Any,
    vector: Sequence[float],
    scale: float,
    start: int,
    end: int,
) -> Any:
    if _is_final_vector(value):
        return value
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return value
    output = list(value)
    if output and _is_final_vector(output[0]):
        for index in range(start, min(end, len(output))):
            output[index] = _add_vector_to_all_final_vectors(output[index], vector, scale)
        return output
    return [_add_vector_to_position_range(item, vector, scale, start, end) for item in output]


def _add_vector_to_all_final_vectors(value: Any, vector: Sequence[float], scale: float) -> Any:
    if _is_final_vector(value):
        return [
            float(item) + scale * float(delta) for item, delta in zip(value, vector, strict=True)
        ]
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_add_vector_to_all_final_vectors(item, vector, scale) for item in value]
    return value


def _add_vector_to_last_final_vector(value: Any, vector: Sequence[float], scale: float) -> Any:
    if _is_final_vector(value):
        return [
            float(item) + scale * float(delta) for item, delta in zip(value, vector, strict=True)
        ]
    if isinstance(value, Sequence) and not isinstance(value, str | bytes) and value:
        output = list(value)
        output[-1] = _add_vector_to_last_final_vector(output[-1], vector, scale)
        return output
    return value


def _as_torch_value(value: Any, reference: Any) -> Any:
    if _is_torch_tensor(value):
        return value.to(device=reference.device, dtype=reference.dtype)
    torch = _torch_module()
    return torch.tensor(value, dtype=reference.dtype, device=reference.device)


def _as_python_vector(value: Any) -> list[float]:
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    vector = _last_nested_vector(value)
    if vector is None:
        raise ValueError("Could not convert activation to a numeric vector")
    return [float(item) for item in vector]


def _to_jsonable(value: Any) -> Any:
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    return value


def _mean_python_vectors(rows: Sequence[Sequence[float]]) -> list[float]:
    width = len(rows[0])
    totals = [0.0] * width
    for row in rows:
        if len(row) != width:
            raise ValueError("steering vector activations must share one dimension")
        for index, value in enumerate(row):
            totals[index] += float(value)
    return [value / len(rows) for value in totals]


def _flatten_rows(value: Any) -> list[list[float]]:
    if isinstance(value, str | bytes):
        return []
    if not isinstance(value, Sequence) or not value:
        return []
    if _is_final_vector(value):
        return [[float(item) for item in value]]
    rows: list[list[float]] = []
    for item in value:
        rows.extend(_flatten_rows(item))
    return rows


def _last_nested_vector(value: Any) -> list[Any] | None:
    if isinstance(value, str | bytes):
        return None
    if isinstance(value, Sequence):
        if not value:
            return None
        if _is_final_vector(value):
            return list(value)
        return _last_nested_vector(value[-1])
    return None


def _is_final_vector(value: Any) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, str | bytes)
        and all(not isinstance(item, Sequence) or isinstance(item, str | bytes) for item in value)
    )


def _torch_module() -> Any:
    import torch

    return torch


def _is_torch_tensor(value: Any) -> bool:
    return "torch" in type(value).__module__ and hasattr(value, "detach")
