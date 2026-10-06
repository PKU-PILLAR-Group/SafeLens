from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper
from SafeLens.steering import (
    ContrastiveSteeringVector,
    PCASteeringVector,
    add_steering_vector,
    pca_direction_from_pairs,
)


def test_contrastive_steering_vector_fits_saves_and_loads(tmp_path: Path) -> None:
    model = _TextActivationModel()
    dataset = [
        {"id": "safe-train", "text": "safe example", "label": 0, "split": "train"},
        {"id": "unsafe-train", "text": "unsafe example", "label": 1, "split": "train"},
        {"id": "safe-test", "text": "safe eval", "label": 0, "split": "test"},
    ]

    steering = ContrastiveSteeringVector.fit(
        model,
        dataset,
        layer="layer_0.resid_post",
        train_split="train",
        normalize=False,
    )
    path = tmp_path / "steering.json"
    steering.save(path)
    loaded = ContrastiveSteeringVector.load(path)

    assert json.loads(path.read_text(encoding="utf-8"))["vector"] == [4.0, 4.0]
    assert loaded.vector == [4.0, 4.0]
    assert loaded.metadata["positive_count"] == 1
    assert loaded.metadata["negative_count"] == 1


def test_contrastive_steering_vector_apply_patches_generation() -> None:
    model = _TextActivationModel()
    steering = ContrastiveSteeringVector(
        layer="layer_0.resid_post",
        vector=[1.0, 2.0],
    )

    handle = steering.apply(model, scale=2.0)
    try:
        assert model.generate("safe prompt") == [0.0, 2.0]
    finally:
        handle.remove()

    assert model.generate("safe prompt") == [-2.0, -2.0]


def test_add_steering_vector_can_patch_last_token_only() -> None:
    activation = [[[1.0, 1.0], [2.0, 2.0]]]

    patched = add_steering_vector(
        activation,
        [1.0, 3.0],
        scale=1.0,
        position="last_token",
    )

    assert patched == [[[1.0, 1.0], [3.0, 5.0]]]


def test_add_steering_vector_can_patch_a_half_open_position_range() -> None:
    activation = [[[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]]

    patched = add_steering_vector(
        activation,
        [1.0, 3.0],
        scale=2.0,
        position=(1, 3),
    )

    assert patched == [[[1.0, 1.0], [4.0, 8.0], [5.0, 9.0]]]


def test_add_steering_vector_range_is_noop_for_short_incremental_sequence() -> None:
    torch = pytest.importorskip("torch")
    activation = torch.tensor([[[1.0, 2.0]]])

    patched = add_steering_vector(activation, [3.0, 4.0], position=(2, 4))

    assert torch.equal(patched, activation)


def test_pca_direction_uses_uncentered_pairs_and_mean_orientation() -> None:
    torch = pytest.importorskip("torch")

    vector = pca_direction_from_pairs(
        [torch.tensor([2.0, 1.0]), torch.tensor([4.0, 2.0])],
        [torch.tensor([0.0, 1.0]), torch.tensor([0.0, 2.0])],
    )

    assert torch.allclose(vector, torch.tensor([1.0, 0.0]))
    assert torch.allclose(vector.norm(), torch.tensor(1.0))


def test_pca_steering_fits_pairs_saves_loads_and_overrides_injection_layer(
    tmp_path: Path,
) -> None:
    torch = pytest.importorskip("torch")
    model = _TextActivationModel()
    steering = PCASteeringVector.fit_pairs(
        model,
        [{"text": "unsafe one"}, {"text": "unsafe two"}],
        [{"text": "safe one"}, {"text": "safe two"}],
        layer="source_layer",
    )
    path = tmp_path / "pca-steering.json"
    steering.save(path)
    loaded = PCASteeringVector.load(path)

    assert loaded.metadata["method"] == "pca_minus_neg"
    assert loaded.metadata["pair_count"] == 2
    assert loaded.metadata["centered"] is False
    assert torch.allclose(torch.as_tensor(loaded.vector).norm(), torch.tensor(1.0))
    output = loaded.generate(model, "safe prompt", layer="injection_layer", scale=2.0)
    expected = -2.0 + 2.0 / (2.0**0.5)
    assert output == pytest.approx([expected, expected])
    assert model._hooks == []


def test_pca_steering_can_pair_labeled_rows_by_key() -> None:
    model = _TextActivationModel()
    dataset = [
        {"text": "safe b", "label": 0, "pair": "b", "split": "train"},
        {"text": "unsafe a", "label": 1, "pair": "a", "split": "train"},
        {"text": "safe a", "label": 0, "pair": "a", "split": "train"},
        {"text": "unsafe b", "label": 1, "pair": "b", "split": "train"},
        {"text": "safe ignored", "label": 0, "pair": "c", "split": "test"},
    ]

    steering = PCASteeringVector.fit(
        model,
        dataset,
        layer="layer_0.resid_post",
        pair_key="pair",
        train_split="train",
    )

    assert steering.metadata["pair_count"] == 2
    assert steering.metadata["pairing"] == "key:pair"


def test_pca_steering_rejects_incomplete_pairs() -> None:
    with pytest.raises(ValueError, match="one positive and one negative"):
        PCASteeringVector.fit(
            _TextActivationModel(),
            [{"text": "unsafe", "label": 1, "pair": "a"}],
            layer="layer_0.resid_post",
            pair_key="pair",
        )


class _Handle:
    def __init__(self, remove_fn: Any) -> None:
        self._remove_fn = remove_fn

    def remove(self) -> None:
        self._remove_fn()


class _TextActivationModel(ModelWrapper):
    device = "cpu"

    def __init__(self) -> None:
        self._hooks: list[tuple[LayerRef, Any]] = []

    def load_model(self) -> _TextActivationModel:
        return self

    def add_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn | None = None,
        *,
        hook: HookFn | None = None,
        dir: str = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
    ) -> _Handle:
        _ = dir, is_permanent, level, prepend
        resolved_hook = hook_fn or hook
        if resolved_hook is None:
            raise TypeError("add_hook requires hook_fn or hook")
        item = (layer, resolved_hook)
        self._hooks.append(item)
        return _Handle(lambda: self._hooks.remove(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        **kwargs: Any,
    ) -> tuple[list[float], dict[str, Any]]:
        _ = kwargs
        selected_layers = list(layers or [layer for layer, _hook in self._hooks])
        activation = self._activation_for_text(str(batch.get("text", "")))
        for layer, hook in list(self._hooks):
            if layer in selected_layers:
                patched = hook(activation=activation, layer=layer)
                if patched is not None:
                    activation = patched
        return activation, {str(layer): activation for layer in selected_layers}

    def generate(self, prompt: str, **generation_kwargs: Any) -> list[float]:
        _ = generation_kwargs
        output, _cache = self.run_with_cache(
            {"text": prompt},
            layers=[layer for layer, _hook in self._hooks],
        )
        return output

    def remove_hooks(self) -> None:
        self._hooks.clear()

    @staticmethod
    def _activation_for_text(text: str) -> list[float]:
        return [2.0, 2.0] if "unsafe" in text else [-2.0, -2.0]
