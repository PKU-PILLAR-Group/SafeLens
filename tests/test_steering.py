from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from SafeLens.core.base import Batch, LayerRef, ModelWrapper
from SafeLens.steering import ContrastiveSteeringVector, add_steering_vector


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

    def add_hook(self, layer: LayerRef, hook_fn: Any, **kwargs: Any) -> _Handle:
        _ = kwargs
        item = (layer, hook_fn)
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
