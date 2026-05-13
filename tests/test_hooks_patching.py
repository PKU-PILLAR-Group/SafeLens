from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any, cast

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper
from SafeLens.core.hooks import (
    ActivationCache,
    cache_activations,
    make_cache_hook,
    matches_names_filter,
    temporary_hooks,
)
from SafeLens.core.patching import (
    PatchSpec,
    activation_name_for_component,
    apply_patch,
    generic_activation_patch,
    get_act_patch_attn_head_out_by_pos,
    get_act_patch_attn_head_pattern_dest_src_pos,
    get_act_patch_block_every,
    get_act_patch_resid_pre,
    layer_head_vector_patch_setter,
    make_patch_specs,
    run_activation_patch,
)
from SafeLens.utils import DummyModelWrapper


class _Handle:
    def __init__(self, remove_fn: Callable[[], None]) -> None:
        self._remove_fn = remove_fn

    def remove(self) -> None:
        self._remove_fn()


class ToyWrapper(ModelWrapper):
    def __init__(self, activation: list[int]) -> None:
        self.activation = activation
        self.hooks: list[tuple[LayerRef, HookFn]] = []
        self.loaded = False

    def load_model(self) -> ToyWrapper:
        self.loaded = True
        return self

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> _Handle:
        item = (layer, hook_fn)
        self.hooks.append(item)
        return _Handle(lambda: self.hooks.remove(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        _ = layers
        activation = list(cast(list[int], batch.get("activation", self.activation)))
        for _layer, hook_fn in list(self.hooks):
            patched = hook_fn(None, None, activation)
            if patched is not None:
                activation = patched
        return {"activation": activation}, {"layer_0": activation}

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        _ = generation_kwargs
        return prompt

    def remove_hooks(self) -> None:
        self.hooks.clear()


class ComponentWrapper(ModelWrapper):
    def __init__(self, activation: Any) -> None:
        self.activation = activation
        self.hooks: list[tuple[LayerRef, HookFn]] = []

    def load_model(self) -> ComponentWrapper:
        return self

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> _Handle:
        item = (layer, hook_fn)
        self.hooks.append(item)
        return _Handle(lambda: self.hooks.remove(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        _ = layers
        activation = deepcopy(batch.get("activation", self.activation))
        cache: dict[str, Any] = {}
        for layer, hook_fn in list(self.hooks):
            patched = hook_fn(None, None, activation)
            if patched is not None:
                activation = patched
            cache[str(layer)] = activation
        return {"activation": activation}, cache

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        _ = generation_kwargs
        return prompt

    def remove_hooks(self) -> None:
        self.hooks.clear()


def _nested_sum(value: Any) -> float:
    if isinstance(value, list):
        return float(sum(_nested_sum(item) for item in value))
    return float(value)


def test_activation_cache_and_name_filter() -> None:
    cache = ActivationCache({"layer_0": [1], "layer_1": [2]})

    assert cache.get_activation("layer_0") == [1]
    assert cache.select("layer_1").to_dict() == {"layer_1": [2]}
    assert cache.select(lambda name: name.endswith("_0")).to_dict() == {"layer_0": [1]}
    assert matches_names_filter("layer_0", ["layer_0", "layer_2"])


def test_cache_hook_captures_torch_style_output() -> None:
    cache = ActivationCache()
    hook = make_cache_hook(cache, "layer_0", detach=False, clone=True)
    activation = [1, 2, 3]

    hook(None, None, activation)

    assert cache["layer_0"] == [1, 2, 3]
    assert cache["layer_0"] is not activation


def test_temporary_hooks_are_removed() -> None:
    model = ToyWrapper([1, 2, 3])

    with temporary_hooks(model, [(0, lambda *_args, **_kwargs: None)]):
        assert len(model.hooks) == 1

    assert model.hooks == []


def test_cache_activations_runs_with_temporary_hooks() -> None:
    model = ToyWrapper([1, 2, 3])

    output, cache = cache_activations(model, {"activation": [4, 5, 6]}, [0])

    assert output == {"activation": [4, 5, 6]}
    assert cache.to_dict() == {"layer_0": [4, 5, 6]}
    assert model.hooks == []


def test_dummy_wrapper_supports_activation_cache_hooks() -> None:
    model = DummyModelWrapper()

    output, cache = cache_activations(model, {"text": "hello"}, [0])

    assert output["text"] == "hello"
    assert cache.to_dict() == {"layer_0": {"batch": {"text": "hello"}}}


def test_dummy_wrapper_keeps_legacy_keyword_hooks() -> None:
    model = DummyModelWrapper()
    captured: dict[str, Any] = {}

    def legacy_hook(layer: LayerRef, batch: Batch, cache: dict[str, Any]) -> None:
        captured["layer"] = layer
        captured["batch"] = batch
        captured["cache"] = cache

    model.add_hook(0, legacy_hook)
    model.run_with_cache({"text": "hello"}, layers=[0])

    assert captured["layer"] == 0
    assert captured["batch"] == {"text": "hello"}
    assert captured["cache"] == {"layer_0": {"batch": {"text": "hello"}}}


def test_apply_patch_replaces_index_from_clean_cache() -> None:
    clean_cache = ActivationCache({"layer_0": [10, 20, 30]})
    spec = PatchSpec(layer=0, target_index=1)

    patched = apply_patch([0, 0, 0], spec, clean_cache)

    assert patched == [0, 20, 0]


def test_run_activation_patch_scores_patched_output() -> None:
    model = ToyWrapper([0, 0, 0])
    clean_cache = ActivationCache({"layer_0": [10, 20, 30]})
    spec = PatchSpec(layer=0, target_index=1)

    result = run_activation_patch(
        model,
        {"activation": [0, 0, 0]},
        clean_cache,
        spec,
        metric=lambda output: float(output["activation"][1]),
    )

    assert result.metric == 20.0
    assert result.output == {"activation": [0, 20, 0]}
    assert model.hooks == []


def test_generic_activation_patch_runs_patch_grid() -> None:
    model = ToyWrapper([0, 0, 0])
    clean_cache = ActivationCache({"layer_0": [10, 20, 30]})
    specs = make_patch_specs([0], target_indices=[0, 2])

    results = generic_activation_patch(
        model,
        {"activation": [0, 0, 0]},
        clean_cache,
        specs,
        metric=lambda output: float(sum(output["activation"])),
    )

    assert [result.metric for result in results] == [10.0, 30.0]


def test_component_activation_names_support_transformerlens_style() -> None:
    assert activation_name_for_component("resid_pre", 0) == "layer_0.resid_pre"
    assert (
        activation_name_for_component("q", 1, name_style="transformer_lens")
        == "blocks.1.attn.hook_q"
    )


def test_residual_stream_patch_runs_by_position() -> None:
    model = ComponentWrapper([[[0, 0], [0, 0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[10, 11], [20, 21]]]})

    results = get_act_patch_resid_pre(
        model,
        {"activation": [[[0, 0], [0, 0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[1],
    )

    assert len(results) == 1
    assert results[0].output["activation"] == [[[0, 0], [20, 21]]]
    assert results[0].metric == 41.0


def test_attention_head_vector_patch_runs_by_position() -> None:
    model = ComponentWrapper([[[[0], [0]], [[0], [0]]]])
    clean_cache = ActivationCache({"layer_0.z": [[[[10], [20]], [[30], [40]]]]})

    results = get_act_patch_attn_head_out_by_pos(
        model,
        {"activation": [[[[0], [0]], [[0], [0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[1],
        heads=[0],
    )

    assert results[0].output["activation"] == [[[[0], [0]], [[30], [0]]]]
    assert results[0].metric == 30.0


def test_attention_head_vector_patch_runs_all_positions() -> None:
    clean_cache = ActivationCache({"layer_0.z": [[[[10], [20]], [[30], [40]]]]})
    spec = PatchSpec(
        layer="layer_0.z",
        activation_name="layer_0.z",
        target_index=(0, 1),
        setter=layer_head_vector_patch_setter,
    )

    patched = apply_patch([[[[0], [0]], [[0], [0]]]], spec, clean_cache)

    assert patched == [[[[0], [20]], [[0], [40]]]]


def test_attention_pattern_patch_runs_by_dest_and_source_position() -> None:
    model = ComponentWrapper([[[[0, 0], [0, 0]], [[0, 0], [0, 0]]]])
    clean_cache = ActivationCache(
        {"layer_0.pattern": [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]}
    )

    results = get_act_patch_attn_head_pattern_dest_src_pos(
        model,
        {"activation": [[[[0, 0], [0, 0]], [[0, 0], [0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        heads=[1],
        dest_positions=[0],
        source_positions=[1],
    )

    assert results[0].output["activation"] == [[[[0, 0], [0, 0]], [[0, 6], [0, 0]]]]
    assert results[0].metric == 6.0


def test_block_every_patches_resid_attention_and_mlp_components() -> None:
    model = ComponentWrapper([[[0]]])
    clean_cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1]]],
            "layer_0.attn_out": [[[2]]],
            "layer_0.mlp_out": [[[3]]],
        }
    )

    results = get_act_patch_block_every(
        model,
        {"activation": [[[0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[0],
    )

    assert set(results) == {"resid_pre", "attn_out", "mlp_out"}
    assert [results[name][0].metric for name in ("resid_pre", "attn_out", "mlp_out")] == [
        1.0,
        2.0,
        3.0,
    ]
