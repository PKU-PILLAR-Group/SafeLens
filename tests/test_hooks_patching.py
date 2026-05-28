from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any, cast

import pytest

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper
from SafeLens.core.hooks import (
    ActivationCache,
    HookPoint,
    cache_activations,
    get_act_name,
    make_cache_hook,
    matches_names_filter,
    safelens_act_name,
    temporary_hooks,
)
from SafeLens.core.patching import (
    PatchSpec,
    activation_name_for_component,
    apply_patch,
    format_patch_results,
    generic_activation_patch,
    get_act_patch_attn_head_all_pos_every,
    get_act_patch_attn_head_by_pos_every,
    get_act_patch_attn_head_out_by_pos,
    get_act_patch_attn_head_pattern_dest_src_pos,
    get_act_patch_attn_head_result_all_pos,
    get_act_patch_attn_head_result_by_pos,
    get_act_patch_block_every,
    get_act_patch_resid_pre,
    layer_head_dest_src_pos_pattern_patch_setter,
    layer_head_pattern_patch_setter,
    layer_head_pos_pattern_patch_setter,
    layer_head_vector_patch_setter,
    layer_pos_head_vector_patch_setter,
    layer_pos_patch_setter,
    make_patch_specs,
    patch_results_to_index_table,
    patch_results_to_metric_grid,
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


class TokenPatchWrapper(ModelWrapper):
    def __init__(self) -> None:
        self.hooks: list[tuple[LayerRef, HookFn]] = []
        self.run_with_hooks_batches: list[Any] = []

    def load_model(self) -> TokenPatchWrapper:
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
        return {"activation": list(batch["activation"])}, {}

    def run_with_hooks(
        self,
        batch: Any,
        *,
        fwd_hooks: Sequence[tuple[LayerRef, HookFn]] = (),
        return_type: str | None = "model_output",
    ) -> dict[str, Any]:
        self.run_with_hooks_batches.append(batch)
        activation = list(batch)
        for _layer, hook_fn in fwd_hooks:
            patched = hook_fn(activation=activation)
            if patched is not None:
                activation = patched
        return {"activation": activation, "return_type": return_type}

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        _ = generation_kwargs
        return prompt

    def remove_hooks(self) -> None:
        self.hooks.clear()


class HeadResultModel:
    def __init__(self, W_O: Any) -> None:
        self.W_O = W_O


class NeuronResultModel:
    def __init__(self, W_out: Any) -> None:
        self.W_out = W_out


class LogitAttributionModel:
    def __init__(self) -> None:
        self.normalization_type = "RMS"
        self.directions = {
            1: [1, 0],
            2: [0, 1],
            3: [1, 1],
        }

    def to_single_token(self, text: str) -> int:
        return {" yes": 1, " no": 2, " maybe": 3}[text]

    def tokens_to_residual_directions(self, tokens: Any) -> Any:
        if isinstance(tokens, int):
            return self.directions[tokens]
        if isinstance(tokens, list):
            return [self.tokens_to_residual_directions(token) for token in tokens]
        return self.directions[int(tokens)]


class LayerNormAttributionModel(LogitAttributionModel):
    def __init__(self) -> None:
        super().__init__()
        self.normalization_type = "LN"


class DeviceMoveModel:
    def __init__(self) -> None:
        self.devices: list[Any] = []

    def to(self, device: Any) -> None:
        self.devices.append(device)


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


def test_hook_point_runs_orders_and_removes_hooks() -> None:
    hook = HookPoint("blocks.3.attn.hook_q")
    hook.ctx["seen"] = True
    hook.add_hook(lambda activation, _hook: activation + [2])
    hook.add_hook(lambda activation, _hook: activation + [1], prepend=True, level=1)
    permanent = hook.add_perma_hook(lambda activation, _hook: activation + [3])

    assert hook([0]) == [0, 1, 2, 3]
    assert hook.layer() == 3
    assert hook.has_hooks()

    hook.remove_hooks(level=1)
    assert hook([0]) == [0, 2, 3]
    hook.remove_hooks()
    assert hook([0]) == [0, 3]
    hook.remove_hooks(including_permanent=True)
    assert hook([0]) == [0]
    assert permanent.removed
    hook.clear_context()
    assert hook.ctx == {}


def test_hook_point_accepts_single_argument_hooks() -> None:
    hook = HookPoint("blocks.0.hook_resid_pre")
    hook.add_hook(lambda activation: activation + [1])

    assert hook([0]) == [0, 1]


def test_model_wrapper_reset_hooks_alias_uses_remove_hooks() -> None:
    wrapper = ToyWrapper([1])
    wrapper.add_hook(0, lambda _mod, _inputs, activation: activation + [2])

    wrapper.reset_hooks()

    assert wrapper.hooks == []
    assert wrapper.run_with_cache({})[0] == {"activation": [1]}


def test_dummy_wrapper_inherits_reset_hooks_alias() -> None:
    wrapper = DummyModelWrapper()
    wrapper.add_hook(0, lambda **kwargs: kwargs["activation"] | {"patched": True})

    wrapper.reset_hooks()

    output, cache = wrapper.run_with_cache({"text": "hello"})
    assert output == {"text": "hello", "risk_score": 0.0}
    assert cache == {}


def test_hook_point_alias_names_match_transformerlens_call_shape() -> None:
    hook = HookPoint("blocks.0.attn.hook_q")
    seen_names: list[str] = []

    def record_alias(activation: list[int], hook: HookPoint) -> list[int]:
        seen_names.append(str(hook.name))
        return activation + [hook.layer()]

    hook.add_hook(
        record_alias,
        alias_names=["blocks.0.attn.hook_q", "layer_1.q"],
    )

    assert hook([9]) == [9, 0, 1]
    assert seen_names == ["blocks.0.attn.hook_q", "layer_1.q"]


def test_activation_name_shorthands_resolve_to_transformerlens_and_safelens_names() -> None:
    assert get_act_name("q", 2) == "blocks.2.attn.hook_q"
    assert get_act_name("attn", 1) == "blocks.1.attn.hook_pattern"
    assert get_act_name("scale", 0, "ln1") == "blocks.0.ln1.hook_scale"
    assert get_act_name("scale4b") == "blocks.4.hook_scale"
    assert get_act_name("normalized", 2, "b") == "blocks.2.hook_normalized"
    assert safelens_act_name("attn", 1) == "layer_1.pattern"


def test_activation_cache_resolves_tuple_keys_and_matching_keys() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [1],
            "blocks.1.attn.hook_q": [2],
            "layer_1.mlp_out": [3],
        }
    )

    assert cache[("resid_pre", 0)] == [1]
    assert cache[("q", 1)] == [2]
    assert cache.resolve_key(("mlp_out", 1)) == "layer_1.mlp_out"
    assert cache.keys_matching(lambda name: "layer_" in name) == [
        "layer_0.resid_pre",
        "layer_1.mlp_out",
    ]


def test_activation_cache_resolves_transformerlens_block_layer_type_alias() -> None:
    cache = ActivationCache(
        {
            "blocks.0.hook_resid_pre": [1],
            "blocks.0.hook_normalized": [2],
        }
    )

    assert cache[("resid_pre", 0, "b")] == [1]
    assert cache[("normalized", 0, "b")] == [2]


def test_activation_cache_resolves_tuple_layer_type_aliases_to_safelens_nested_keys() -> None:
    cache = ActivationCache(
        {
            "layer_0.attn.q": [1],
            "layer_0.mlp.post": [2],
        }
    )

    assert cache[("q", 0, "a")] == [1]
    assert cache[("post", 0, "m")] == [2]


def test_activation_cache_resolves_tuple_component_keys_to_safelens_nested_keys() -> None:
    cache = ActivationCache(
        {
            "layer_0.attn.q": [1],
            "layer_0.mlp.post": [2],
        }
    )

    assert cache[("q", 0)] == [1]
    assert cache[("post", 0)] == [2]


def test_activation_cache_resolves_full_transformerlens_names_to_safelens_cache_keys() -> None:
    cache = ActivationCache(
        {
            "layer_0.q": [1],
            "layer_0.mlp_out": [2],
            "layer_0.post": [3],
        }
    )

    assert cache["blocks.0.attn.hook_q"] == [1]
    assert cache["blocks.0.hook_mlp_out"] == [2]
    assert cache["blocks.0.mlp.hook_post"] == [3]
    assert "blocks.0.attn.hook_q" in cache


def test_activation_cache_resolves_safelens_names_to_transformerlens_cache_keys() -> None:
    cache = ActivationCache(
        {
            "blocks.0.attn.hook_q": [1],
            "blocks.0.hook_mlp_out": [2],
            "blocks.0.mlp.hook_post": [3],
        }
    )

    assert cache["layer_0.q"] == [1]
    assert cache["layer_0.mlp_out"] == [2]
    assert cache["layer_0.post"] == [3]
    assert "layer_0.q" in cache


def test_activation_cache_string_filters_match_equivalent_cache_names() -> None:
    cache = ActivationCache(
        {
            "layer_0.q": [1],
            "blocks.1.hook_mlp_out": [2],
            "layer_2.resid_pre": [3],
        }
    )

    assert cache.keys_matching("blocks.0.attn.hook_q") == ["layer_0.q"]
    assert cache.keys_matching(["layer_1.mlp_out", "blocks.2.hook_resid_pre"]) == [
        "blocks.1.hook_mlp_out",
        "layer_2.resid_pre",
    ]
    assert cache.select("blocks.0.attn.hook_q").to_dict() == {"layer_0.q": [1]}


def test_activation_cache_resolves_negative_layer_tuple_keys() -> None:
    cache = ActivationCache(
        {
            "blocks.0.hook_resid_post": [0],
            "blocks.1.hook_resid_post": [1],
        }
    )

    assert cache[("resid_post", -1)] == [1]


def test_activation_cache_batch_dim_helpers() -> None:
    cache = ActivationCache({"layer_0": [[1, 2]], "scalar": 9})
    without_batch = cache.remove_batch_dim()

    assert without_batch is cache
    assert without_batch.to_dict() == {"layer_0": [1, 2], "scalar": 9}
    assert not without_batch.has_batch_dim

    batched = ActivationCache({"layer_0": [[[1], [2]], [[3], [4]]]})
    sliced = batched.apply_slice_to_batch_dim(1)

    assert sliced.to_dict() == {"layer_0": [[3], [4]]}
    assert not sliced.has_batch_dim


def test_activation_cache_batch_slice_accepts_explicit_indices_and_masks() -> None:
    cache = ActivationCache({"layer_0": [[[1]], [[2]], [[3]]]})

    assert cache.apply_slice_to_batch_dim([2, 0]).to_dict() == {"layer_0": [[[3]], [[1]]]}
    assert cache.apply_slice_to_batch_dim([True, False, True]).to_dict() == {
        "layer_0": [[[1]], [[3]]]
    }


def test_activation_cache_batch_slice_matches_transformerlens_slice_inputs() -> None:
    cache = ActivationCache({"layer_0": [[[1]], [[2]], [[3]]]})

    identity = cache.apply_slice_to_batch_dim(None)
    ranged = cache.apply_slice_to_batch_dim((1, 3))

    assert identity.to_dict() == {"layer_0": [[[1]], [[2]], [[3]]]}
    assert identity.has_batch_dim
    assert ranged.to_dict() == {"layer_0": [[[2]], [[3]]]}
    assert ranged.has_batch_dim


def test_activation_cache_remove_batch_dim_matches_transformerlens_shape_tolerance() -> None:
    cache = ActivationCache({"batched": [[1, 2]], "already_flat": [3, 4]})

    cache.remove_batch_dim()

    assert cache.to_dict() == {"batched": [1, 2], "already_flat": [3, 4]}
    assert not cache.has_batch_dim

    multi_batch = ActivationCache({"layer_0": [[1], [2]]})
    try:
        multi_batch.remove_batch_dim()
    except ValueError as exc:
        assert "batch size > 1" in str(exc)
    else:
        raise AssertionError("Expected non-singleton batch removal to raise.")


def test_activation_cache_remove_batch_dim_is_atomic_for_mixed_invalid_shapes() -> None:
    cache = ActivationCache({"singleton": [[1, 2]], "multi": [[3], [4]]})

    try:
        cache.remove_batch_dim()
    except ValueError as exc:
        assert "multi" in str(exc)
    else:
        raise AssertionError("Expected mixed invalid batch removal to raise.")

    assert cache.to_dict() == {"singleton": [[1, 2]], "multi": [[3], [4]]}
    assert cache.has_batch_dim


def test_activation_cache_exposes_transformerlens_cache_dict_and_embed_flags() -> None:
    cache = ActivationCache({"hook_embed": [1]})

    assert cache.cache_dict is cache._cache
    assert cache.has_embed
    assert not cache.has_pos_embed

    cache.cache_dict["hook_pos_embed"] = [2]
    assert cache["hook_pos_embed"] == [2]
    assert cache.has_pos_embed

    cache.cache_dict = {"layer_0": [3]}
    assert cache.to_dict() == {"layer_0": [3]}
    assert not cache.has_embed


def test_activation_cache_to_mutates_in_place_and_optionally_moves_model() -> None:
    model = DeviceMoveModel()
    cache = ActivationCache({"layer_0": [1]}, model=model)

    returned = cache.to("cpu", move_model=True)

    assert returned is cache
    assert cache.to_dict() == {"layer_0": [1]}
    assert model.devices == ["cpu"]


def test_activation_cache_stack_activation_and_accumulated_resid() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[1, 10]],
            "layer_0.resid_mid": [[2, 20]],
            "layer_1.resid_pre": [[3, 30]],
            "layer_1.resid_post": [[4, 40]],
        }
    )

    assert cache.stack_activation("resid_pre") == [[[1, 10]], [[3, 30]]]

    stack, labels = cache.accumulated_resid(incl_mid=True, return_labels=True)

    assert labels == ["0_pre", "0_mid", "1_pre", "final_post"]
    assert stack == [[[1, 10]], [[2, 20]], [[3, 30]], [[4, 40]]]


def test_activation_cache_constructor_and_stack_activation_match_transformerlens_call_style() -> None:
    cache = ActivationCache(
        {
            "blocks.0.attn.hook_q": [1],
            "blocks.1.attn.hook_q": [2],
        },
        None,
        False,
    )

    assert not cache.has_batch_dim
    assert cache.stack_activation("q", 2, "attn") == [[1], [2]]
    assert cache.stack_activation("q", 2, sublayer_type="attn") == [[1], [2]]


def test_activation_cache_accumulated_resid_accepts_explicit_position_indices() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1], [2], [3]]],
            "layer_0.resid_post": [[[4], [5], [6]]],
        }
    )

    stack, labels = cache.accumulated_resid(pos_slice=[2, 0], return_labels=True)

    assert labels == ["0_pre", "final_post"]
    assert stack == [[[[3], [1]]], [[[6], [4]]]]


def test_activation_cache_pos_slice_uses_transformerlens_dims_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[1, 10], [2, 20], [3, 30]],
            "layer_0.resid_post": [[4, 40], [5, 50], [6, 60]],
            "layer_0.result": [
                [[1, 10], [2, 20]],
                [[3, 30], [4, 40]],
                [[5, 50], [6, 60]],
            ],
        },
        has_batch_dim=False,
    )

    residual_stack, residual_labels = cache.accumulated_resid(
        pos_slice=[2, 0],
        return_labels=True,
    )
    head_stack, head_labels = cache.stack_head_results(
        pos_slice=[2, 0],
        return_labels=True,
    )

    assert residual_labels == ["0_pre", "final_post"]
    assert residual_stack == [
        [[3, 30], [1, 10]],
        [[6, 60], [4, 40]],
    ]
    assert head_labels == ["L0H0", "L0H1"]
    assert head_stack == [
        [[5, 50], [1, 10]],
        [[6, 60], [2, 20]],
    ]


def test_activation_cache_accumulated_resid_applies_ln_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[2], [4], [8]],
            "layer_0.resid_pre": [[2, 4], [8, 16], [16, 24]],
            "layer_0.resid_post": [[4, 8], [16, 32], [32, 48]],
        },
        has_batch_dim=False,
    )

    stack, labels = cache.accumulated_resid(
        apply_ln=True,
        pos_slice=[2, 0],
        return_labels=True,
    )

    assert labels == ["0_pre", "final_post"]
    assert stack == [
        [[2.0, 3.0], [1.0, 2.0]],
        [[4.0, 6.0], [2.0, 4.0]],
    ]


def test_activation_cache_stack_head_results_accepts_int_pos_slice_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "layer_0.result": [
                [[1, 10], [2, 20]],
                [[3, 30], [4, 40]],
                [[5, 50], [6, 60]],
            ],
        },
        has_batch_dim=False,
    )

    head_stack, head_labels = cache.stack_head_results(pos_slice=1, return_labels=True)

    assert head_labels == ["L0H0", "L0H1"]
    assert head_stack == [[3, 30], [4, 40]]


def test_activation_cache_stack_head_results_applies_ln_to_int_pos_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[2], [4], [8]],
            "layer_0.result": [
                [[1, 10], [2, 20]],
                [[3, 30], [4, 40]],
                [[5, 50], [6, 60]],
            ],
        },
        has_batch_dim=False,
    )

    head_stack, head_labels = cache.stack_head_results(
        pos_slice=1,
        apply_ln=True,
        return_labels=True,
    )

    assert head_labels == ["L0H0", "L0H1"]
    assert head_stack == [[0.75, 7.5], [1.0, 10.0]]


def test_activation_cache_tuple_pos_and_neuron_slices_match_transformerlens_ranges() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1], [2], [3], [4]]],
            "layer_0.resid_post": [[[5], [6], [7], [8]]],
            "layer_0.post": [[[10, 20, 30, 40]]],
        }
    )

    residual_stack, residual_labels = cache.accumulated_resid(
        pos_slice=(1, 3),
        return_labels=True,
    )
    neuron_stack, neuron_labels = cache.stack_neuron_results(
        neuron_slice=(1, 3),
        return_labels=True,
    )

    assert residual_labels == ["0_pre", "final_post"]
    assert residual_stack == [[[[2], [3]]], [[[6], [7]]]]
    assert neuron_labels == ["L0N1", "L0N2"]
    assert neuron_stack == [[[20]], [[30]]]


def test_activation_cache_accepts_transformerlens_positional_helper_args() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[[1, 0], [2, 0]]],
            "layer_0.resid_pre": [[[1, 0], [2, 0]]],
            "layer_0.resid_mid": [[[3, 0], [4, 0]]],
            "layer_0.resid_post": [[[5, 0], [6, 0]]],
            "layer_0.attn_out": [[[0, 1], [0, 2]]],
            "layer_0.mlp_out": [[[7, 0], [8, 0]]],
            "layer_0.result": [[[[1, 0]], [[2, 0]]]],
            "layer_0.post": [[[3]]],
            "ln_final.hook_scale": [[[1], [1]]],
        },
        model=NeuronResultModel(W_out=[[[0, 1]]]),
    )

    accum_stack, accum_labels = cache.accumulated_resid(0, False, False, [1], True, True)
    resid_stack, resid_labels = cache.decompose_resid(1, False, "attn", False, [1], False, True)
    head_stack, head_labels = cache.stack_head_results(1, True, False, [1], False)
    neuron_stack, neuron_labels = cache.stack_neuron_results(1, [1], None, True, False, False)
    full_stack, full_labels = cache.get_full_resid_decomposition(
        1,
        False,
        False,
        False,
        [1],
        True,
    )

    assert accum_labels == ["0_pre", "0_mid"]
    assert accum_stack == [[[[2, 0]]], [[[4, 0]]]]
    assert resid_labels == ["0_attn_out"]
    assert resid_stack == [[[[0, 2]]]]
    assert head_labels == ["L0H0"]
    assert head_stack == [[[[2, 0]]]]
    assert neuron_labels == ["L0N0"]
    assert neuron_stack == [[[[0, 3]]]]
    assert full_labels == ["L0H0", "0_mlp_out", "embed"]
    assert full_stack == [[[[2, 0]]], [[[8, 0]]], [[[2, 0]]]]


def test_activation_cache_residual_decomposition() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[1, 0]],
            "hook_pos_embed": [[0, 1]],
            "layer_0.attn_out": [[2, 0]],
            "layer_0.mlp_out": [[0, 3]],
        }
    )

    stack, labels = cache.decompose_resid(return_labels=True)

    assert labels == ["embed", "pos_embed", "0_attn_out", "0_mlp_out"]
    assert stack == [[[1, 0]], [[0, 1]], [[2, 0]], [[0, 3]]]


def test_activation_cache_head_and_neuron_decomposition() -> None:
    cache = ActivationCache(
        {
            "layer_0.result": [[[[1, 10], [2, 20]]]],
            "layer_0.post": [[[5, 6]]],
        }
    )

    head_stack, head_labels = cache.stack_head_results(return_labels=True)
    neuron_stack, neuron_labels = cache.stack_neuron_results(return_labels=True)

    assert head_labels == ["L0H0", "L0H1"]
    assert head_stack == [[[[1, 10]]], [[[2, 20]]]]
    assert neuron_labels == ["L0N0", "L0N1"]
    assert neuron_stack == [[[5]], [[6]]]


def test_activation_cache_computes_head_results_from_z_and_w_o() -> None:
    cache = ActivationCache(
        {"layer_0.z": [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]},
        model=HeadResultModel(W_O=[[[[1, 0, 1], [0, 1, 1]], [[1, 2, 0], [3, 4, 1]]]]),
    )

    result_stack, labels = cache.compute_head_results(return_labels=True)
    head_stack, head_labels = cache.stack_head_results(return_labels=True)

    assert labels == ["0_result"]
    assert result_stack == [[[[[1.0, 2.0, 3.0], [15.0, 22.0, 4.0]], [[5.0, 6.0, 11.0], [31.0, 46.0, 8.0]]]]]
    assert cache["layer_0.result"] == result_stack[0]
    assert head_labels == ["L0H0", "L0H1"]
    assert head_stack == [[[[1.0, 2.0, 3.0], [5.0, 6.0, 11.0]]], [[[15.0, 22.0, 4.0], [31.0, 46.0, 8.0]]]]


def test_activation_cache_stack_head_results_auto_computes_from_z() -> None:
    cache = ActivationCache(
        {"layer_0.z": [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]},
        model=HeadResultModel(W_O=[[[[1, 0, 1], [0, 1, 1]], [[1, 2, 0], [3, 4, 1]]]]),
    )

    head_stack, labels = cache.stack_head_results(pos_slice=[1], return_labels=True)

    assert labels == ["L0H0", "L0H1"]
    assert head_stack == [[[[5.0, 6.0, 11.0]]], [[[31.0, 46.0, 8.0]]]]
    assert cache["layer_0.result"] == [
        [[
            [1.0, 2.0, 3.0],
            [15.0, 22.0, 4.0],
        ], [
            [5.0, 6.0, 11.0],
            [31.0, 46.0, 8.0],
        ]]
    ]


def test_activation_cache_stack_head_results_auto_computes_from_z_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "layer_0.z": [
                [[1, 2], [3, 4]],
                [[5, 6], [7, 8]],
            ]
        },
        model=HeadResultModel(W_O=[[[[1, 0, 1], [0, 1, 1]], [[1, 2, 0], [3, 4, 1]]]]),
        has_batch_dim=False,
    )

    head_stack, labels = cache.stack_head_results(pos_slice=1, return_labels=True)

    assert labels == ["L0H0", "L0H1"]
    assert head_stack == [[5.0, 6.0, 11.0], [31.0, 46.0, 8.0]]
    assert cache["layer_0.result"] == [
        [
            [1.0, 2.0, 3.0],
            [15.0, 22.0, 4.0],
        ],
        [
            [5.0, 6.0, 11.0],
            [31.0, 46.0, 8.0],
        ],
    ]


def test_activation_cache_stack_head_results_layer_zero_remainder() -> None:
    cache = ActivationCache({"layer_0.resid_post": [[[1, 2], [3, 4]]]})

    head_stack, labels = cache.stack_head_results(
        layer=0,
        incl_remainder=True,
        pos_slice=[1],
        return_labels=True,
    )

    assert labels == ["remainder"]
    assert head_stack == [[[[3, 4]]]]


def test_activation_cache_full_residual_decomposition_and_logit_attrs() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[1, 0]],
            "layer_0.result": [[[[2, 0]]]],
            "layer_0.post": [[[0, 3]]],
        }
    )

    stack, labels = cache.get_full_resid_decomposition(return_labels=True)
    attrs = cache.logit_attrs([[1, 2], [3, 4]], [[10, 1], [1, 10]], apply_ln=False)

    assert labels == ["L0H0", "L0N0", "L0N1", "embed"]
    assert stack == [[[[2, 0]]], [[0]], [[3]], [[1, 0]]]
    assert attrs == [12.0, 43.0]


def test_activation_cache_full_decomposition_prefers_fine_residual_components() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[[9, 9]]],
            "hook_pos_embed": [[[8, 8]]],
            "layer_0.attn_out": [[[100, 100]]],
            "layer_0.mlp_out": [[[200, 200]]],
            "layer_0.result": [[[[1, 10], [2, 20]]]],
            "layer_0.post": [[[3, 4]]],
        },
        model=NeuronResultModel(W_out=[[[1, 0], [0, 2]]]),
    )

    stack, labels = cache.get_full_resid_decomposition(return_labels=True)

    assert labels == ["L0H0", "L0H1", "L0N0", "L0N1", "embed", "pos_embed"]
    assert stack == [
        [[[1, 10]]],
        [[[2, 20]]],
        [[[3, 0]]],
        [[[0, 8]]],
        [[[9, 9]]],
        [[[8, 8]]],
    ]


def test_activation_cache_full_decomposition_accepts_int_pos_slice_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[9, 9], [8, 8]],
            "layer_0.result": [
                [[1, 10], [2, 20]],
                [[3, 30], [4, 40]],
            ],
            "layer_0.post": [
                [5, 6],
                [7, 8],
            ],
        },
        model=NeuronResultModel(W_out=[[[1, 0], [0, 2]]]),
        has_batch_dim=False,
    )

    stack, labels = cache.get_full_resid_decomposition(pos_slice=1, return_labels=True)

    assert labels == ["L0H0", "L0H1", "L0N0", "L0N1", "embed"]
    assert stack == [
        [3, 30],
        [4, 40],
        [7, 0],
        [0, 16],
        [8, 8],
    ]


def test_activation_cache_gets_and_slices_neuron_results() -> None:
    cache = ActivationCache(
        {"layer_0.post": [[[3, 4, 5]]]},
        model=NeuronResultModel(W_out=[[[1, 0], [0, 2], [3, 3]]]),
    )

    assert cache.get_neuron_results(0) == [[[[3, 0], [0, 8], [15, 15]]]]
    assert cache.get_neuron_results(0, neuron_slice=[2, 0]) == [[[[15, 15], [3, 0]]]]

    stack, labels = cache.stack_neuron_results(neuron_slice=slice(1, None), return_labels=True)

    assert labels == ["L0N1", "L0N2"]
    assert stack == [[[[0, 8]]], [[[15, 15]]]]


def test_activation_cache_get_neuron_results_slices_numpy_arrays() -> None:
    np = pytest.importorskip("numpy")
    cache = ActivationCache(
        {"layer_0.post": np.array([[[3.0, 4.0, 5.0]]])},
        model=NeuronResultModel(
            W_out=np.array([[[1.0, 0.0], [0.0, 2.0], [3.0, 3.0]]])
        ),
    )

    result = cache.get_neuron_results(0, neuron_slice=[2, 0])

    assert np.array_equal(result, np.array([[[[15.0, 15.0], [3.0, 0.0]]]]))


def test_activation_cache_stack_neuron_results_accepts_int_pos_slice_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "layer_0.post": [
                [3, 4, 5],
                [6, 7, 8],
            ],
        },
        model=NeuronResultModel(W_out=[[[1, 0], [0, 2], [3, 3]]]),
        has_batch_dim=False,
    )

    stack, labels = cache.stack_neuron_results(pos_slice=1, return_labels=True)

    assert labels == ["L0N0", "L0N1", "L0N2"]
    assert stack == [[6, 0], [0, 14], [24, 24]]


def test_activation_cache_stack_neuron_results_applies_ln_to_int_pos_without_batch_dim() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[2], [4], [8]],
            "layer_0.post": [
                [3, 4],
                [6, 8],
                [9, 10],
            ],
        },
        model=NeuronResultModel(W_out=[[[1, 0], [0, 2]]]),
        has_batch_dim=False,
    )

    stack, labels = cache.stack_neuron_results(
        pos_slice=1,
        apply_ln=True,
        return_labels=True,
    )

    assert labels == ["L0N0", "L0N1"]
    assert stack == [[1.5, 0.0], [0.0, 4.0]]


def test_activation_cache_neuron_results_project_output_onto_directions() -> None:
    cache = ActivationCache(
        {"layer_0.post": [[[3, 4]]]},
        model=NeuronResultModel(W_out=[[[1, 2, 3], [4, 5, 6]]]),
    )

    assert cache.get_neuron_results(0, project_output_onto=[1, 0, -1]) == [[[-6.0, -8.0]]]

    stack, labels = cache.stack_neuron_results(
        project_output_onto=[[1, 0], [0, 1], [1, 1]],
        return_labels=True,
    )

    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[[12.0, 15.0]]], [[[40.0, 44.0]]]]


def test_activation_cache_head_and_neuron_stacks_support_remainder_and_layernorm() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2]]],
            "layer_0.result": [[[[2, 0], [0, 4]]]],
            "layer_0.post": [[[3, 5]]],
            "layer_0.resid_post": [[[11, 16]]],
        },
        model=NeuronResultModel(W_out=[[[1, 0], [0, 1]]]),
    )

    head_stack, head_labels = cache.stack_head_results(
        incl_remainder=True,
        apply_ln=True,
        return_labels=True,
    )
    neuron_stack, neuron_labels = cache.stack_neuron_results(
        incl_remainder=True,
        apply_ln=True,
        return_labels=True,
    )

    assert head_labels == ["L0H0", "L0H1", "remainder"]
    assert head_stack == [[[[1.0, 0.0]]], [[[0.0, 2.0]]], [[[4.5, 6.0]]]]
    assert neuron_labels == ["L0N0", "L0N1", "remainder"]
    assert neuron_stack == [[[[1.5, 0.0]]], [[[0.0, 2.5]]], [[[4.0, 5.5]]]]


def test_activation_cache_full_decomposition_falls_back_to_layer_outputs() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[[1, 0]]],
            "layer_0.attn_out": [[[2, 0]]],
            "layer_0.mlp_out": [[[0, 3]]],
        }
    )

    stack, labels = cache.get_full_resid_decomposition(return_labels=True)

    assert labels == ["0_attn_out", "0_mlp_out", "embed"]
    assert stack == [[[[2, 0]]], [[[0, 3]]], [[[1, 0]]]]


def test_activation_cache_full_decomposition_projects_output_directions() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[[1, 2, 3]]],
            "layer_0.result": [[[[1, 0, 1]]]],
            "layer_0.post": [[[2]]],
        },
        model=NeuronResultModel(W_out=[[[3, 4, 5]]]),
    )

    stack, labels = cache.get_full_resid_decomposition(
        project_output_onto=[1, 0, -1],
        return_labels=True,
    )

    assert labels == ["L0H0", "L0N0", "embed"]
    assert stack == [[[0.0]], [[-4.0]], [[-2.0]]]


def test_activation_cache_logit_attrs_broadcasts_directions_over_component_axis() -> None:
    cache = ActivationCache()
    residual_stack = [
        [[[1, 2], [3, 4]]],
        [[[10, 20], [30, 40]]],
    ]
    token_directions = [[[1, 0], [0, 1]]]

    assert cache.logit_attrs(residual_stack, token_directions, apply_ln=False) == [
        [[1.0, 4.0]],
        [[10.0, 40.0]],
    ]


def test_activation_cache_logit_attrs_accepts_torch_residuals_with_python_directions() -> None:
    torch = pytest.importorskip("torch")
    cache = ActivationCache()
    residual_stack = torch.tensor(
        [
            [[[1.0, 2.0], [3.0, 4.0]]],
            [[[10.0, 20.0], [30.0, 40.0]]],
        ]
    )

    attrs = cache.logit_attrs(
        residual_stack,
        [[[1.0, 0.0], [0.0, 1.0]]],
        apply_ln=False,
    )

    assert torch.equal(attrs, torch.tensor([[[1.0, 4.0]], [[10.0, 40.0]]]))


def test_activation_cache_logit_attrs_accepts_numpy_residuals_with_python_directions() -> None:
    np = pytest.importorskip("numpy")
    cache = ActivationCache()
    residual_stack = np.array(
        [
            [[[1.0, 2.0], [3.0, 4.0]]],
            [[[10.0, 20.0], [30.0, 40.0]]],
        ]
    )

    attrs = cache.logit_attrs(
        residual_stack,
        [[[1.0, 0.0], [0.0, 1.0]]],
        apply_ln=False,
    )

    assert np.array_equal(attrs, np.array([[[1.0, 4.0]], [[10.0, 40.0]]]))


def test_activation_cache_logit_attrs_accepts_string_tokens_and_checks_logit_diff_shape() -> None:
    cache = ActivationCache(model=LogitAttributionModel())

    assert cache.logit_attrs([[1, 2], [3, 4]], " yes", apply_ln=False) == [1.0, 3.0]
    assert cache.logit_attrs([[1, 2], [3, 4]], " yes", incorrect_tokens=" no", apply_ln=False) == [
        -1.0,
        -1.0,
    ]
    try:
        cache.logit_attrs([[1, 2]], [1, 2], incorrect_tokens=1, apply_ln=False)
    except ValueError as exc:
        assert "same shape" in str(exc)
    else:
        raise AssertionError("Expected mismatched logit-difference token shapes to raise.")


def test_activation_cache_logit_attrs_slices_positions_and_layernorm_scales() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2], [4], [8]]]},
        model=LogitAttributionModel(),
    )

    attrs = cache.logit_attrs(
        [[[[8, 16], [8, 16]]]],
        [[1, 2, 3]],
        pos_slice=slice(1, 3),
    )

    assert attrs == [[[4.0, 3.0]]]


def test_activation_cache_logit_attrs_broadcasts_single_token_direction_with_pos_slice() -> None:
    cache = ActivationCache(model=LogitAttributionModel())

    assert cache.logit_attrs(
        [[[[2, 3], [4, 5]]]],
        " yes",
        apply_ln=False,
        pos_slice=[0],
    ) == [[[2.0, 4.0]]]
    assert cache.logit_attrs(
        [[[[2, 3], [4, 5]]]],
        " yes",
        directions=[1, 0],
        apply_ln=False,
        pos_slice=slice(0, 1),
    ) == [[[2.0, 4.0]]]


def test_activation_cache_logit_attrs_accepts_explicit_position_indices() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2], [4], [8]]]},
        model=LogitAttributionModel(),
    )

    attrs = cache.logit_attrs(
        [[[[16, 24], [8, 16]]]],
        [[1, 2, 3]],
        pos_slice=[2, 0],
    )

    assert attrs == [[[5.0, 4.0]]]


def test_activation_cache_logit_attrs_uses_cache_batch_dim_by_default() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[2], [4], [8]]},
        model=LogitAttributionModel(),
        has_batch_dim=False,
    )

    attrs = cache.logit_attrs(
        [[[16, 24], [8, 16]]],
        [1, 2, 3],
        pos_slice=[2, 0],
    )

    assert attrs == [[5.0, 4.0]]


def test_activation_cache_apply_ln_slices_batch_and_position_scales() -> None:
    cache = ActivationCache({"ln_final.hook_scale": [[[2], [4]], [[8], [16]]]})

    assert cache.apply_ln_to_stack(
        [[[[0, 0]], [[16, 32]]]],
        layer=-1,
        batch_slice=1,
        pos_slice=slice(1, 2),
    ) == [[[1.0, 2.0]]]


def test_activation_cache_apply_ln_prefers_layer_scales_for_intermediate_layers() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[100]]],
            "blocks.0.ln1.hook_scale": [[[2]]],
            "blocks.0.ln2.hook_scale": [[[4]]],
        }
    )

    residual_stack = [[[[8, 16]]]]

    assert cache.apply_ln_to_stack(residual_stack, layer=0) == [[[[4.0, 8.0]]]]
    assert cache.apply_ln_to_stack(residual_stack, layer=0, mlp_input=True) == [
        [[[2.0, 4.0]]]
    ]
    assert cache.apply_ln_to_stack(residual_stack, layer=-1) == [[[[0.08, 0.16]]]]


def test_activation_cache_apply_ln_centers_layernorm_components_only() -> None:
    ln_cache = ActivationCache(
        {"ln_final.hook_scale": [[[2], [4]]]},
        model=LayerNormAttributionModel(),
    )
    rms_cache = ActivationCache(
        {"ln_final.hook_scale": [[[2], [4]]]},
        model=LogitAttributionModel(),
    )

    assert ln_cache.apply_ln_to_stack([[[[2, 6], [6, 14]]]], layer=-1) == [
        [[[-1.0, 1.0], [-1.0, 1.0]]]
    ]
    assert rms_cache.apply_ln_to_stack([[[[2, 6], [6, 14]]]], layer=-1) == [
        [[[1.0, 3.0], [1.5, 3.5]]]
    ]


def test_activation_cache_logit_attrs_uses_centered_layernorm_for_ln_models() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2]]]},
        model=LayerNormAttributionModel(),
    )

    assert cache.logit_attrs([[[[2, 6]]]], " yes") == [[[-1.0]]]


def test_activation_cache_apply_ln_and_value_transforms() -> None:
    cache = ActivationCache({"ln_final.hook_scale": [2, 4], "layer_0": [1, 2]})

    assert cache.apply_ln_to_stack([8, 16], scale_key="ln_final.hook_scale") == [4.0, 4.0]
    assert cache.apply_to_values(lambda value: value + [9]).to_dict()["layer_0"] == [1, 2, 9]
    assert cache.detach().to_dict() == cache.to_dict()


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


def test_dummy_wrapper_accepts_activation_hook_signature() -> None:
    model = DummyModelWrapper()

    model.add_hook(0, lambda activation, hook: {"patched": activation["batch"], "hook": hook})
    _output, cache = model.run_with_cache({"text": "hello"}, layers=[0])

    assert cache["layer_0"] == {"patched": {"text": "hello"}, "hook": None}


def test_dummy_wrapper_accepts_transformerlens_cache_options() -> None:
    model = DummyModelWrapper()

    model.add_hook(0, lambda activation, _hook: {"patched": activation["batch"]})
    _output, cache = model.run_with_cache(
        {"text": "hello"},
        layers=[0, 1],
        names_filter="layer_0",
        return_cache_object=True,
    )

    assert isinstance(cache, ActivationCache)
    assert cache["layer_0"] == {"patched": {"text": "hello"}}
    assert "layer_1" not in cache


def test_apply_patch_replaces_index_from_clean_cache() -> None:
    clean_cache = ActivationCache({"layer_0": [10, 20, 30]})
    spec = PatchSpec(layer=0, target_index=1)

    patched = apply_patch([0, 0, 0], spec, clean_cache)

    assert patched == [0, 20, 0]


def test_apply_patch_replaces_and_adds_numpy_activation_slices() -> None:
    np = pytest.importorskip("numpy")
    clean_cache = ActivationCache(
        {"layer_0.resid_pre": np.array([[[10.0, 20.0], [30.0, 40.0]]])}
    )
    corrupted = np.zeros((1, 2, 2), dtype=np.float32)

    replaced = apply_patch(
        corrupted,
        PatchSpec(
            layer="layer_0.resid_pre",
            activation_name="layer_0.resid_pre",
            target_index=(slice(None), 1),
        ),
        clean_cache,
    )
    added = apply_patch(
        corrupted,
        PatchSpec(
            layer="layer_0.resid_pre",
            activation_name="layer_0.resid_pre",
            target_index=(slice(None), 1),
            mode="add",
            scale=0.5,
        ),
        clean_cache,
    )

    assert np.array_equal(replaced, np.array([[[0.0, 0.0], [30.0, 40.0]]], dtype=np.float32))
    assert np.array_equal(added, np.array([[[0.0, 0.0], [15.0, 20.0]]], dtype=np.float32))
    assert replaced.dtype == corrupted.dtype
    assert added.dtype == corrupted.dtype
    assert np.array_equal(corrupted, np.zeros((1, 2, 2), dtype=np.float32))


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


def test_run_activation_patch_accepts_direct_token_inputs_with_wrapper_hooks() -> None:
    model = TokenPatchWrapper()
    clean_cache = ActivationCache({"layer_0": [10, 20, 30]})
    spec = PatchSpec(layer=0, target_index=1)

    result = run_activation_patch(
        model,
        [0, 0, 0],
        clean_cache,
        spec,
        metric=lambda output: float(output["activation"][1]),
    )

    assert result.metric == 20.0
    assert result.output == {"activation": [0, 20, 0], "return_type": "model_output"}
    assert result.cache == {}
    assert model.run_with_hooks_batches == [[0, 0, 0]]
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


def test_generic_activation_patch_accepts_single_patch_spec() -> None:
    model = ToyWrapper([0, 0, 0])
    clean_cache = ActivationCache({"layer_0": [10, 20, 30]})
    spec = PatchSpec(layer=0, target_index=1)

    results = generic_activation_patch(
        model,
        {"activation": [0, 0, 0]},
        clean_cache,
        spec,
        metric=lambda output: float(sum(output["activation"])),
    )

    assert len(results) == 1
    assert results[0].metric == 20.0


def test_patch_results_format_as_transformerlens_metric_grid_and_index_table() -> None:
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

    assert patch_results_to_metric_grid(results, ("layer", "pos")) == [[10.0, 30.0]]
    assert patch_results_to_index_table(results, ("layer", "pos")) == [
        {"layer": 0, "pos": 0},
        {"layer": 0, "pos": 2},
    ]
    assert format_patch_results(
        results,
        ("layer", "pos"),
        return_details=False,
        return_index_df=True,
    ) == (
        [[10.0, 30.0]],
        [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 2}],
    )


def test_generic_activation_patch_accepts_transformerlens_style_call() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache(
        {
            "blocks.0.hook_resid_pre": [[[1], [2]]],
        }
    )

    def tl_layer_pos_setter(corrupted_activation: Any, index: Sequence[int], clean_activation: Any) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    grid, index_table = generic_activation_patch(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=tl_layer_pos_setter,
        activation_name="resid_pre",
        index_axis_names=("layer", "pos"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[1.0, 2.0]]
    assert index_table == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_transformerlens_call_defaults_to_metric_grid() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(corrupted_activation: Any, index: Sequence[int], clean_activation: Any) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    grid = generic_activation_patch(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=tl_layer_pos_setter,
        activation_name="resid_pre",
        index_axis_names=("layer", "pos"),
    )

    assert grid == [[1.0, 2.0]]


def test_generic_activation_patch_transformerlens_call_infers_layers_from_safelens_cache() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(corrupted_activation: Any, index: Sequence[int], clean_activation: Any) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    grid, index_table = generic_activation_patch(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=tl_layer_pos_setter,
        activation_name="resid_pre",
        index_axis_names=("layer", "pos"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[1.0, 2.0]]
    assert index_table == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_accepts_transformerlens_positional_call() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(corrupted_activation: Any, index: Sequence[int], clean_activation: Any) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    grid, index_table = generic_activation_patch(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        lambda output: _nested_sum(output["activation"]),
        tl_layer_pos_setter,
        "resid_pre",
        ("layer", "pos"),
        None,
        True,
        return_details=False,
    )

    assert grid == [[1.0, 2.0]]
    assert index_table == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_accepts_explicit_transformerlens_index_table() -> None:
    model = ComponentWrapper([[[0], [0], [0]]])
    clean_cache = ActivationCache(
        {
            "blocks.0.hook_resid_pre": [[[10], [20], [30]]],
        }
    )

    def tl_layer_pos_setter(corrupted_activation: Any, index: Sequence[int], clean_activation: Any) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    metrics, index_table = generic_activation_patch(
        model,
        {"activation": [[[0], [0], [0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=tl_layer_pos_setter,
        activation_name="resid_pre",
        index_df=[{"layer": 0, "pos": 2}, {"layer": 0, "pos": 0}],
        return_details=False,
        return_index_df=True,
    )

    assert metrics == [30.0, 10.0]
    assert index_table == [{"layer": 0, "pos": 2}, {"layer": 0, "pos": 0}]


def test_transformerlens_patch_setter_internal_type_errors_propagate() -> None:
    model = ComponentWrapper([[[0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1]]]})

    def broken_tl_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
        _ = corrupted_activation, index, clean_activation
        raise TypeError("inner tl setter bug")

    with pytest.raises(TypeError, match="inner tl setter bug"):
        generic_activation_patch(
            model,
            {"activation": [[[0]]]},
            clean_cache,
            patching_metric=lambda output: _nested_sum(output["activation"]),
            patch_setter=broken_tl_setter,
            activation_name="resid_pre",
            index_axis_names=("layer", "pos"),
        )


def test_transformerlens_patch_setter_adapter_accepts_safelens_style_setters() -> None:
    model = ComponentWrapper([[[0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1]]]})

    def safelens_setter(
        corrupted_activation: Any,
        spec: PatchSpec,
        clean_cache: ActivationCache,
    ) -> Any:
        _ = clean_cache
        patched = deepcopy(corrupted_activation)
        patched[0][spec.target_index[1]] = [9]
        return patched

    grid = generic_activation_patch(
        model,
        {"activation": [[[0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=safelens_setter,
        activation_name="resid_pre",
        index_axis_names=("layer", "pos"),
    )

    assert grid == [[9.0]]


def test_transformerlens_patch_setter_adapter_preserves_original_unknown_style_error() -> None:
    model = ComponentWrapper([[[0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1]]]})

    class UnknownStyleSetter:
        def __call__(self, activation: Any, second: Any, third: Any) -> Any:
            _ = activation, third
            if isinstance(second, tuple):
                raise TypeError("tl-style failure")
            raise TypeError("safelens-style failure")

    with pytest.raises(TypeError, match="tl-style failure"):
        generic_activation_patch(
            model,
            {"activation": [[[0]]]},
            clean_cache,
            patching_metric=lambda output: _nested_sum(output["activation"]),
            patch_setter=UnknownStyleSetter(),
            activation_name="resid_pre",
            index_axis_names=("layer", "pos"),
        )


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
        return_details=True,
    )

    assert len(results) == 1
    assert results[0].output["activation"] == [[[0, 0], [20, 21]]]
    assert results[0].metric == 41.0


def test_residual_stream_patch_defaults_to_transformerlens_metric_grid() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1], [2]]]})

    grid = get_act_patch_resid_pre(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[0, 1],
    )

    assert grid == [[1.0, 2.0]]


def test_residual_stream_patch_infers_positions_from_cache_without_batch_dim() -> None:
    model = ComponentWrapper([[0, 0], [0, 0]])
    clean_cache = ActivationCache(
        {"layer_0.resid_pre": [[1, 10], [2, 20]]},
        has_batch_dim=False,
    )

    grid = get_act_patch_resid_pre(
        model,
        {"activation": [[0, 0], [0, 0]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
    )

    assert grid == [[11.0, 22.0]]


def test_residual_stream_patch_uses_no_batch_clean_cache_for_batched_activation() -> None:
    model = ComponentWrapper([[[0, 0], [0, 0]]])
    clean_cache = ActivationCache(
        {"layer_0.resid_pre": [[1, 10], [2, 20]]},
        has_batch_dim=False,
    )

    grid = get_act_patch_resid_pre(
        model,
        {"activation": [[[0, 0], [0, 0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
    )

    assert grid == [[11.0, 22.0]]


def test_residual_stream_patch_can_return_metric_grid_and_index_table() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1], [2]]]})

    grid, index_table = get_act_patch_resid_pre(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[0, 1],
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[1.0, 2.0]]
    assert index_table == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


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
        return_details=True,
    )

    assert results[0].output["activation"] == [[[[0], [0]], [[30], [0]]]]
    assert results[0].metric == 30.0


def test_attention_head_vector_patch_infers_axes_from_cache_without_batch_dim() -> None:
    model = ComponentWrapper([[[0], [0]], [[0], [0]]])
    clean_cache = ActivationCache(
        {
            "layer_0.z": [
                [[10], [20]],
                [[30], [40]],
            ]
        },
        has_batch_dim=False,
    )

    grid = get_act_patch_attn_head_out_by_pos(
        model,
        {"activation": [[[0], [0]], [[0], [0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
    )

    assert grid == [[[10.0, 20.0], [30.0, 40.0]]]


def test_attention_head_result_patch_helpers_require_per_head_result_shape() -> None:
    model = ComponentWrapper([[[[0], [0]], [[0], [0]]]])
    clean_cache = ActivationCache({"layer_0.result": [[[[10], [20]], [[30], [40]]]]})

    by_pos = get_act_patch_attn_head_result_by_pos(
        model,
        {"activation": [[[[0], [0]], [[0], [0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[1],
        heads=[0],
        return_details=True,
    )
    all_pos = get_act_patch_attn_head_result_all_pos(
        model,
        {"activation": [[[[0], [0]], [[0], [0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        heads=[1],
        return_details=True,
    )

    assert by_pos[0].output["activation"] == [[[[0], [0]], [[30], [0]]]]
    assert by_pos[0].metric == 30.0
    assert all_pos[0].output["activation"] == [[[[0], [20]], [[0], [40]]]]
    assert all_pos[0].metric == 60.0


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


def test_torch_patch_setter_accepts_list_clean_cache_values() -> None:
    torch = pytest.importorskip("torch")
    corrupted = torch.zeros(1, 2, 2, dtype=torch.float32)
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1.0, 2.0], [3.0, 4.0]]]})
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch(corrupted, spec, clean_cache)

    assert torch.equal(patched, torch.tensor([[[0.0, 0.0], [3.0, 4.0]]]))
    assert patched.dtype == corrupted.dtype


def test_torch_add_patch_setter_coerces_list_patch_values() -> None:
    torch = pytest.importorskip("torch")
    corrupted = torch.ones(1, 2, 2, dtype=torch.float32)
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1.0, 2.0], [3.0, 4.0]]]})
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        mode="add",
        scale=0.5,
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch(corrupted, spec, clean_cache)

    assert torch.allclose(patched, torch.tensor([[[1.0, 1.0], [2.5, 3.0]]]))
    assert patched.dtype == corrupted.dtype


def test_list_patch_setter_accepts_torch_clean_cache_values() -> None:
    torch = pytest.importorskip("torch")
    corrupted = [[[0.0, 0.0], [0.0, 0.0]]]
    clean_cache = ActivationCache(
        {"layer_0.resid_pre": torch.tensor([[[1.0, 2.0], [3.0, 4.0]]])}
    )
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch(corrupted, spec, clean_cache)

    assert patched == [[[0.0, 0.0], [3.0, 4.0]]]


def test_exported_patch_setters_accept_transformerlens_call_shape() -> None:
    residual_clean = [[[10], [20]]]
    head_clean = [[[[1], [2]], [[3], [4]]]]
    pattern_clean = [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]

    assert layer_pos_patch_setter([[[0], [0]]], (0, 1), residual_clean) == [[[0], [20]]]
    assert layer_pos_head_vector_patch_setter(
        [[[[0], [0]], [[0], [0]]]],
        (0, 1, 0),
        head_clean,
    ) == [[[[0], [0]], [[3], [0]]]]
    assert layer_head_vector_patch_setter(
        [[[[0], [0]], [[0], [0]]]],
        (0, 1),
        head_clean,
    ) == [[[[0], [2]], [[0], [4]]]]
    assert layer_head_pattern_patch_setter(
        [[[[0, 0], [0, 0]], [[0, 0], [0, 0]]]],
        (0, 1),
        pattern_clean,
    ) == [[[[0, 0], [0, 0]], [[5, 6], [7, 8]]]]
    assert layer_head_pos_pattern_patch_setter(
        [[[[0, 0], [0, 0]], [[0, 0], [0, 0]]]],
        (0, 1, 0),
        pattern_clean,
    ) == [[[[0, 0], [0, 0]], [[5, 6], [0, 0]]]]
    assert layer_head_dest_src_pos_pattern_patch_setter(
        [[[[0, 0], [0, 0]], [[0, 0], [0, 0]]]],
        (0, 1, 0, 1),
        pattern_clean,
    ) == [[[[0, 0], [0, 0]], [[0, 6], [0, 0]]]]


def test_attention_pattern_patch_runs_by_dest_and_source_position() -> None:
    model = ComponentWrapper([[[[0, 0], [0, 0]], [[0, 0], [0, 0]]]])
    clean_cache = ActivationCache({"layer_0.pattern": [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]})

    results = get_act_patch_attn_head_pattern_dest_src_pos(
        model,
        {"activation": [[[[0, 0], [0, 0]], [[0, 0], [0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        heads=[1],
        dest_positions=[0],
        source_positions=[1],
        return_details=True,
    )

    assert results[0].output["activation"] == [[[[0, 0], [0, 0]], [[0, 6], [0, 0]]]]
    assert results[0].metric == 6.0


def test_attention_pattern_patch_infers_dest_and_source_positions_from_pattern_shape() -> None:
    model = ComponentWrapper([[[[0, 0, 0], [0, 0, 0]]]])
    clean_cache = ActivationCache({"layer_0.pattern": [[[[1, 2, 3], [4, 5, 6]]]]})

    results = get_act_patch_attn_head_pattern_dest_src_pos(
        model,
        {"activation": [[[[0, 0, 0], [0, 0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        heads=[0],
        return_details=True,
    )

    assert len(results) == 6
    assert [result.spec.target_index for result in results] == [
        (0, 0, 0, 0),
        (0, 0, 0, 1),
        (0, 0, 0, 2),
        (0, 0, 1, 0),
        (0, 0, 1, 1),
        (0, 0, 1, 2),
    ]
    assert results[-1].output["activation"] == [[[[0, 0, 0], [0, 0, 6]]]]


def test_attention_pattern_patch_uses_no_batch_clean_cache_for_batched_activation() -> None:
    model = ComponentWrapper([[[[0, 0, 0], [0, 0, 0]]]])
    clean_cache = ActivationCache(
        {"layer_0.pattern": [[[1, 2, 3], [4, 5, 6]]]},
        has_batch_dim=False,
    )

    results = get_act_patch_attn_head_pattern_dest_src_pos(
        model,
        {"activation": [[[[0, 0, 0], [0, 0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        heads=[0],
        dest_positions=[1],
        source_positions=[2],
        return_details=True,
    )

    assert results[0].output["activation"] == [[[[0, 0, 0], [0, 0, 6]]]]
    assert results[0].metric == 6.0


def test_attention_pattern_patch_prefers_pattern_shape_over_token_length() -> None:
    model = ComponentWrapper([[[[0, 0, 0], [0, 0, 0]]]])
    clean_cache = ActivationCache({"layer_0.pattern": [[[[1, 2, 3], [4, 5, 6]]]]})

    results = get_act_patch_attn_head_pattern_dest_src_pos(
        model,
        {"input_ids": [[10, 11, 12, 13, 14]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        heads=[0],
        return_details=True,
    )

    assert len(results) == 6
    assert results[-1].spec.target_index == (0, 0, 1, 2)
    assert results[-1].output["activation"] == [[[[0, 0, 0], [0, 0, 6]]]]


def test_attention_pattern_patch_can_return_transformerlens_metric_grid() -> None:
    model = ComponentWrapper([[[[0, 0, 0], [0, 0, 0]]]])
    clean_cache = ActivationCache({"layer_0.pattern": [[[[1, 2, 3], [4, 5, 6]]]]})

    grid, index_table = get_act_patch_attn_head_pattern_dest_src_pos(
        model,
        {"activation": [[[[0, 0, 0], [0, 0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        heads=[0],
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]]]
    assert index_table[0] == {"layer": 0, "head_index": 0, "dest_pos": 0, "src_pos": 0}
    assert index_table[-1] == {"layer": 0, "head_index": 0, "dest_pos": 1, "src_pos": 2}


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
        return_details=True,
    )

    assert set(results) == {"resid_pre", "attn_out", "mlp_out"}
    assert [results[name][0].metric for name in ("resid_pre", "attn_out", "mlp_out")] == [
        1.0,
        2.0,
        3.0,
    ]


def test_block_every_defaults_to_transformerlens_metric_stack() -> None:
    model = ComponentWrapper([[[0]]])
    clean_cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1]]],
            "layer_0.attn_out": [[[2]]],
            "layer_0.mlp_out": [[[3]]],
        }
    )

    stack = get_act_patch_block_every(
        model,
        {"activation": [[[0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[0],
    )

    assert stack == [[[1.0]], [[2.0]], [[3.0]]]


def test_attention_head_every_defaults_to_transformerlens_metric_stacks() -> None:
    model = ComponentWrapper([[[[0]]]])
    clean_cache = ActivationCache(
        {
            "layer_0.z": [[[[1]]]],
            "layer_0.q": [[[[2]]]],
            "layer_0.k": [[[[3]]]],
            "layer_0.v": [[[[4]]]],
            "layer_0.pattern": [[[[5]]]],
        }
    )
    kwargs = {
        "layers": [0],
        "positions": [0],
        "heads": [0],
        "dest_positions": [0],
        "source_positions": [0],
    }

    all_pos_stack = get_act_patch_attn_head_all_pos_every(
        model,
        {"activation": [[[[0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        **kwargs,
    )
    by_pos_stack = get_act_patch_attn_head_by_pos_every(
        model,
        {"activation": [[[[0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        **kwargs,
    )

    assert all_pos_stack == [[[1.0]], [[2.0]], [[3.0]], [[4.0]], [[5.0]]]
    assert by_pos_stack == [[[[1.0]]], [[[2.0]]], [[[3.0]]], [[[4.0]]], [[[5.0]]]]
