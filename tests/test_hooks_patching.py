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
    PatchResult,
    PatchSpec,
    activation_name_for_component,
    apply_patch,
    format_patch_results,
    generic_activation_patch,
    get_act_patch_attn_head_all_pos_every,
    get_act_patch_attn_head_by_pos_every,
    get_act_patch_attn_head_k_by_pos,
    get_act_patch_attn_head_out_by_pos,
    get_act_patch_attn_head_pattern_dest_src_pos,
    get_act_patch_attn_head_result_all_pos,
    get_act_patch_attn_head_result_by_pos,
    get_act_patch_block_every,
    get_act_patch_resid_pre,
    get_indexed,
    infer_heads,
    infer_layers,
    infer_positions,
    layer_head_dest_src_pos_pattern_patch_setter,
    layer_head_pattern_patch_setter,
    layer_head_pos_pattern_patch_setter,
    layer_head_vector_patch_setter,
    layer_pos_head_vector_patch_setter,
    layer_pos_patch_setter,
    make_df_from_ranges,
    make_patch_hook,
    make_patch_specs,
    normalize_index_table,
    patch_results_to_index_df,
    patch_results_to_index_table,
    patch_results_to_metric_grid,
    run_activation_patch,
    set_indexed,
)
from SafeLens.core.tensors import Slice
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
        self.hooks.append(item)
        return _Handle(lambda: self.hooks.remove(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        _ = layers, kwargs
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
    cfg: Any

    def __init__(self, activation: Any) -> None:
        self.activation = activation
        self.hooks: list[tuple[LayerRef, HookFn]] = []
        self.n_layers: int | None = None

    def load_model(self) -> ComponentWrapper:
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
        self.hooks.append(item)
        return _Handle(lambda: self.hooks.remove(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        _ = layers, kwargs
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


class ComponentMapWrapper(ComponentWrapper):
    def __init__(self, activations: dict[str, Any]) -> None:
        super().__init__(activation=None)
        self.activations = activations

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        _ = layers, kwargs
        cache: dict[str, Any] = {}
        activation = None
        for layer, hook_fn in list(self.hooks):
            activation = deepcopy(batch.get(str(layer), self.activations[str(layer)]))
            patched = hook_fn(None, None, activation)
            if patched is not None:
                activation = patched
            cache[str(layer)] = activation
        return {"activation": activation}, cache


class TokenPatchWrapper(ModelWrapper):
    def __init__(self) -> None:
        self.hooks: list[tuple[LayerRef, HookFn]] = []
        self.run_with_hooks_batches: list[Any] = []

    def load_model(self) -> TokenPatchWrapper:
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
        self.hooks.append(item)
        return _Handle(lambda: self.hooks.remove(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        _ = layers, kwargs
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


class TransformerLensBlockWeightModel:
    def __init__(self, *, W_O: Any | None = None, W_out: Any | None = None) -> None:
        attn: Any = type("AttentionWeights", (), {})()
        mlp: Any = type("MlpWeights", (), {})()
        if W_O is not None:
            attn.W_O = W_O
        if W_out is not None:
            mlp.W_out = W_out
        self.blocks = [type("Block", (), {"attn": attn, "mlp": mlp})()]


class BiasOnlyModel:
    def accumulated_bias(
        self,
        layer: int,
        mlp_input: bool = False,
        include_mlp_biases: bool = True,
    ) -> Any:
        _ = mlp_input
        bias = [10.0 * layer, 100.0 * layer]
        if include_mlp_biases:
            bias = [bias[0] + layer, bias[1] + layer]
        return bias


class AttnOnlyModel:
    class Cfg:
        attn_only = True

    cfg = Cfg()


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


class LogitLensModel(LogitAttributionModel):
    def __init__(self) -> None:
        super().__init__()
        self.W_U = [[1, 0, 1], [0, 1, 1]]
        self.b_U = [0.5, -1.0, 10.0]


class DeviceMoveModel:
    def __init__(self) -> None:
        self.devices: list[Any] = []

    def to(self, device: Any) -> None:
        self.devices.append(device)


class _FakeSlice:
    def __init__(self, index: Any, mode: str | None = None) -> None:
        self.slice = index
        self.mode = mode or ("identity" if index is None else "slice")


def _nested_sum(value: Any) -> float:
    if isinstance(value, list):
        return float(sum(_nested_sum(item) for item in value))
    return float(value)


def _index_records(index_df: Any) -> list[dict[str, Any]]:
    records, _columns = normalize_index_table(index_df)
    return records


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
    hook.add_hook(lambda grad, _hook: grad + [4], "bwd")
    hook.remove_hooks()
    assert hook.has_hooks("bwd")
    hook.remove_hooks("bwd")
    assert not hook.has_hooks()
    hook.clear_context()
    assert hook.ctx == {}


def test_hook_point_including_permanent_removal_ignores_context_level() -> None:
    hook = HookPoint("blocks.0.hook_resid_pre")
    hook.add_hook(lambda activation, _hook: activation + ["temp-1"], level=1)
    hook.add_hook(lambda activation, _hook: activation + ["temp-2"], level=2)
    permanent = hook.add_perma_hook(lambda activation, _hook: activation + ["permanent"])
    permanent.context_level = 99

    hook.remove_hooks(including_permanent=True, level=1)

    assert hook([]) == ["temp-2"]
    assert permanent.removed


def test_hook_point_accepts_single_argument_hooks() -> None:
    hook = HookPoint("blocks.0.hook_resid_pre")
    hook.add_hook(lambda activation: activation + [1])

    assert hook([0]) == [0, 1]


def test_hook_point_accepts_official_positional_direction_argument() -> None:
    hook = HookPoint("blocks.0.hook_resid_pre")
    hook.add_perma_hook(lambda activation, _hook: activation + [1], "fwd")
    handle = hook.add_hook(lambda grad, _hook: grad + 2, "bwd")

    assert hook([0]) == [0, 1]
    assert hook.has_hooks("bwd")
    assert handle.context_level is None


def test_hook_point_accepts_official_hook_keyword_argument() -> None:
    hook = HookPoint("blocks.0.hook_resid_pre")

    hook.add_hook(hook=lambda activation, _hook: activation + [1])
    hook.add_perma_hook(hook=lambda activation, _hook: activation + [2])

    assert hook([0]) == [0, 1, 2]


def test_hook_point_accepts_alternate_positional_hook_names() -> None:
    hook = HookPoint("blocks.0.hook_resid_pre")

    def append_layer(value: list[int], point: HookPoint) -> list[int]:
        return value + [point.layer()]

    hook.add_hook(append_layer)

    assert hook([0]) == [0, 0]


def test_hook_point_accepts_positional_activation_with_extra_kwargs() -> None:
    hook = HookPoint("blocks.2.hook_resid_pre")

    def append_metadata(value: list[int], **kwargs: Any) -> list[int]:
        return value + [kwargs["hook"].layer(), kwargs["output"][0]]

    hook.add_hook(append_metadata)

    assert hook([9]) == [9, 2, 9]


def test_hook_point_passes_activation_and_hook_to_variadic_positional_hooks() -> None:
    hook = HookPoint("blocks.3.hook_resid_pre")
    seen: list[tuple[Any, ...]] = []

    def variadic(*args: Any) -> list[int]:
        seen.append(args)
        activation, point = args
        return activation + [point.layer()]

    hook.add_hook(variadic)

    assert hook([0]) == [0, 3]
    assert seen == [([0], hook)]


def test_hook_point_prefers_keyword_metadata_for_variadic_keyword_hooks() -> None:
    hook = HookPoint("blocks.4.hook_resid_pre")
    seen: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def variadic(*args: Any, **kwargs: Any) -> list[int]:
        seen.append((args, kwargs))
        return kwargs["activation"] + [kwargs["hook"].layer(), kwargs["output"][0]]

    hook.add_hook(variadic)

    assert hook([9]) == [9, 4, 9]
    assert seen == [((), {"activation": [9], "output": [9], "hook": hook})]


def test_hook_point_propagates_internal_type_errors_with_alternate_names() -> None:
    hook = HookPoint("blocks.0.hook_resid_pre")

    def broken(value: list[int], point: HookPoint) -> list[int]:
        _ = value, point
        raise TypeError("inner hook bug")

    hook.add_hook(broken)

    with pytest.raises(TypeError, match="inner hook bug"):
        hook([0])


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
    assert get_act_name("hook_q", 2, "attn") == "blocks.2.attn.hook_q"
    assert get_act_name("hook_resid_pre", 2) == "blocks.2.hook_resid_pre"
    assert get_act_name("attn", 1) == "blocks.1.attn.hook_pattern"
    assert get_act_name("scale", 0, "ln1") == "blocks.0.ln1.hook_scale"
    assert get_act_name("scale4b") == "blocks.4.hook_scale"
    assert get_act_name("normalized", 2, "b") == "blocks.2.hook_normalized"
    assert safelens_act_name("hook_q", 1) == "layer_1.q"
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
    assert cache[("hook_resid_pre", 0)] == [1]
    assert cache[("q", 1)] == [2]
    assert cache[("hook_q", 1, "attn")] == [2]
    assert cache.resolve_key(("mlp_out", 1)) == "layer_1.mlp_out"
    assert cache.keys_matching(lambda name: "layer_" in name) == [
        "layer_0.resid_pre",
        "layer_1.mlp_out",
    ]


def test_activation_cache_exposes_transformerlens_mapping_views() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [1],
            "blocks.1.attn.hook_q": [2],
        }
    )

    assert list(cache.keys()) == ["layer_0.resid_pre", "blocks.1.attn.hook_q"]
    assert list(cache.values()) == [[1], [2]]
    assert list(cache.items()) == [
        ("layer_0.resid_pre", [1]),
        ("blocks.1.attn.hook_q", [2]),
    ]
    assert cache[("resid_pre", 0)] == [1]


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


def test_activation_cache_canonicalizes_hook_prefix_tuple_writes() -> None:
    cache = ActivationCache()

    cache[("hook_q", 0, "attn")] = [1]
    cache[("hook_resid_pre", 0)] = [2]

    assert cache.to_dict() == {
        "layer_0.attn.q": [1],
        "layer_0.resid_pre": [2],
    }
    assert cache[("q", 0, "attn")] == [1]
    assert cache[("resid_pre", 0)] == [2]


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


def test_activation_cache_resolves_transformerlens_string_shorthands_to_safelens_keys() -> None:
    cache = ActivationCache(
        {
            "layer_0.q": [1],
            "layer_0.resid_pre": [2],
            "layer_1.mlp.post": [3],
        }
    )

    assert cache["q0"] == [1]
    assert cache["resid_pre0"] == [2]
    assert cache["post1m"] == [3]
    assert cache.keys_matching("q0") == ["layer_0.q"]
    assert cache.keys_matching(["resid_pre0", "post1m"]) == [
        "layer_0.resid_pre",
        "layer_1.mlp.post",
    ]


def test_activation_cache_canonicalizes_transformerlens_string_shorthand_storage() -> None:
    cache = ActivationCache(
        {
            "q0": [1],
            "post1m": [2],
            "scale4ln1": [3],
            "custom123": [4],
        }
    )

    assert cache.to_dict() == {
        "layer_0.q": [1],
        "layer_1.mlp.post": [2],
        "layer_4.ln1.scale": [3],
        "custom123": [4],
    }
    assert cache[("q", 0)] == [1]
    assert cache["blocks.0.attn.hook_q"] == [1]
    assert cache[("post", 1, "m")] == [2]
    assert cache["blocks.1.mlp.hook_post"] == [2]
    assert cache[("scale", 4, "ln1")] == [3]
    assert cache["blocks.4.ln1.hook_scale"] == [3]


def test_activation_cache_string_shorthand_writes_update_canonical_storage() -> None:
    cache = ActivationCache({"blocks.0.attn.hook_q": [1]})

    cache["q0"] = [2]
    cache["post1m"] = [3]

    assert cache.to_dict() == {
        "blocks.0.attn.hook_q": [2],
        "layer_1.mlp.post": [3],
    }
    assert cache[("q", 0)] == [2]
    assert cache["blocks.1.mlp.hook_post"] == [3]


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


def test_activation_cache_mutates_tuple_keys_through_canonical_names() -> None:
    cache = ActivationCache()

    cache[("resid_pre", 0)] = [1]
    cache[("q", 0)] = [2]
    cache[("post", 0, "m")] = [3]

    assert cache.to_dict() == {
        "layer_0.resid_pre": [1],
        "layer_0.q": [2],
        "layer_0.mlp.post": [3],
    }
    assert cache["blocks.0.hook_resid_pre"] == [1]
    assert cache["blocks.0.attn.hook_q"] == [2]
    assert cache["blocks.0.mlp.hook_post"] == [3]

    cache[("q", 0)] = [4]
    assert cache.to_dict()["layer_0.q"] == [4]

    del cache[("resid_pre", 0)]
    assert "layer_0.resid_pre" not in cache.to_dict()
    assert ("resid_pre", 0) not in cache


def test_activation_cache_tuple_key_mutation_updates_existing_transformerlens_names() -> None:
    cache = ActivationCache(
        {
            "blocks.0.hook_resid_post": [0],
            "blocks.1.hook_resid_post": [1],
        }
    )

    cache[("resid_post", -1)] = [9]
    del cache[("resid_post", 0)]

    assert cache.to_dict() == {"blocks.1.hook_resid_post": [9]}


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
    with pytest.raises(IndexError, match="Boolean index has length"):
        cache.apply_slice_to_batch_dim([True, False])


def test_activation_cache_batch_slice_matches_transformerlens_slice_inputs() -> None:
    cache = ActivationCache({"layer_0": [[[1]], [[2]], [[3]]]})

    identity = cache.apply_slice_to_batch_dim(None)
    ranged = cache.apply_slice_to_batch_dim((1, 3))

    assert identity.to_dict() == {"layer_0": [[[1]], [[2]], [[3]]]}
    assert identity.has_batch_dim
    assert ranged.to_dict() == {"layer_0": [[[2]], [[3]]]}
    assert ranged.has_batch_dim


def test_activation_cache_batch_slice_accepts_transformerlens_slice_like_object() -> None:
    cache = ActivationCache({"layer_0": [[[1]], [[2]], [[3]]]})

    identity = cache.apply_slice_to_batch_dim(_FakeSlice(None, mode="identity"))
    ranged = cache.apply_slice_to_batch_dim(_FakeSlice(slice(1, 3)))
    indexed = cache.apply_slice_to_batch_dim(_FakeSlice([2, 0], mode="array"))

    assert identity.to_dict() == {"layer_0": [[[1]], [[2]], [[3]]]}
    assert identity.has_batch_dim
    assert ranged.to_dict() == {"layer_0": [[[2]], [[3]]]}
    assert ranged.has_batch_dim
    assert indexed.to_dict() == {"layer_0": [[[3]], [[1]]]}
    assert indexed.has_batch_dim


def test_activation_cache_empty_batch_slice_is_noop_without_batch_dim() -> None:
    cache = ActivationCache({"layer_0": [[1], [2]]}, has_batch_dim=False)

    identity = cache.apply_slice_to_batch_dim(None)

    assert identity is not cache
    assert identity.to_dict() == {"layer_0": [[1], [2]]}
    assert not identity.has_batch_dim
    with pytest.raises(ValueError, match="without batch dim"):
        cache.apply_slice_to_batch_dim(0)


def test_activation_cache_remove_batch_dim_matches_transformerlens_shape_tolerance() -> None:
    cache = ActivationCache({"batched": [[1, 2]], "already_flat": [3, 4]})

    cache.remove_batch_dim()

    assert cache.to_dict() == {"batched": [1, 2], "already_flat": [3, 4]}
    assert not cache.has_batch_dim

    mixed_rank_cache = ActivationCache(
        {
            "batched": [[[1, 2]]],
            "already_matrix": [[3, 4], [5, 6]],
            "scalar": 7,
        }
    )

    mixed_rank_cache.remove_batch_dim()

    assert mixed_rank_cache.to_dict() == {
        "batched": [[1, 2]],
        "already_matrix": [[3, 4], [5, 6]],
        "scalar": 7,
    }
    assert not mixed_rank_cache.has_batch_dim

    multi_batch = ActivationCache({"layer_0": [[1], [2]]})
    try:
        multi_batch.remove_batch_dim()
    except ValueError as exc:
        assert "batch size > 1" in str(exc)
    else:
        raise AssertionError("Expected non-singleton batch removal to raise.")


def test_activation_cache_remove_batch_dim_leaves_ambiguous_non_singleton_when_batch_seen() -> None:
    cache = ActivationCache({"singleton": [[1, 2]], "multi": [[3], [4]]})

    cache.remove_batch_dim()

    assert cache.to_dict() == {"singleton": [1, 2], "multi": [[3], [4]]}
    assert not cache.has_batch_dim


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


def test_activation_cache_canonicalizes_top_level_embedding_constructor_aliases() -> None:
    cache = ActivationCache(
        {
            "embed": [[1, 0]],
            "pos_embed": [[0, 1]],
            "layer_0.attn_out": [[2, 0]],
            "layer_0.mlp_out": [[0, 3]],
        }
    )

    stack, labels = cache.decompose_resid(return_labels=True)

    assert cache.has_embed
    assert cache.has_pos_embed
    assert cache.to_dict()["hook_embed"] == [[1, 0]]
    assert cache.to_dict()["hook_pos_embed"] == [[0, 1]]
    assert labels == ["embed", "pos_embed", "0_attn_out", "0_mlp_out"]
    assert stack == [[[1, 0]], [[0, 1]], [[2, 0]], [[0, 3]]]

    cache.cache_dict = {"embed": [3], "pos_embed": [4]}

    assert cache.to_dict() == {"hook_embed": [3], "hook_pos_embed": [4]}
    assert cache.has_embed
    assert cache.has_pos_embed


def test_activation_cache_canonicalizes_top_level_embedding_writes() -> None:
    cache = ActivationCache()

    cache["embed"] = [1]
    cache[("pos_embed",)] = [2]

    assert cache.to_dict() == {"hook_embed": [1], "hook_pos_embed": [2]}
    assert cache.has_embed
    assert cache.has_pos_embed
    assert cache["hook_embed"] == [1]
    assert cache["pos_embed"] == [2]

    cache[("hook_embed",)] = [3]
    cache["hook_pos_embed"] = [4]

    assert cache.to_dict() == {"hook_embed": [3], "hook_pos_embed": [4]}


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


def test_activation_cache_stacks_numpy_backend_like_tensor_workflows() -> None:
    np = pytest.importorskip("numpy")
    cache = ActivationCache(
        {
            "hook_embed": np.array([[[1.0, 0.0], [0.5, 0.5]]]),
            "layer_0.resid_pre": np.array([[[1.0, 10.0], [2.0, 20.0]]]),
            "layer_0.resid_post": np.array([[[3.0, 30.0], [4.0, 40.0]]]),
            "layer_0.attn_out": np.array([[[2.0, 0.0], [0.0, 2.0]]]),
            "layer_0.mlp_out": np.array([[[0.0, 3.0], [3.0, 0.0]]]),
            "layer_0.result": np.array([[[[1.0, 10.0], [2.0, 20.0]]]]),
            "layer_0.post": np.array([[[5.0, 6.0]]]),
        }
    )

    resid_stack, resid_labels = cache.accumulated_resid(pos_slice=[1, 0], return_labels=True)
    decomp_stack, decomp_labels = cache.decompose_resid(return_labels=True)
    head_stack, head_labels = cache.stack_head_results(return_labels=True)
    neuron_stack, neuron_labels = cache.stack_neuron_results(return_labels=True)

    assert resid_labels == ["0_pre", "final_post"]
    assert isinstance(resid_stack, np.ndarray)
    assert resid_stack.shape == (2, 1, 2, 2)
    assert np.allclose(resid_stack[0], np.array([[[2.0, 20.0], [1.0, 10.0]]]))
    assert np.allclose(resid_stack[1], np.array([[[4.0, 40.0], [3.0, 30.0]]]))
    assert decomp_labels == ["embed", "0_attn_out", "0_mlp_out"]
    assert isinstance(decomp_stack, np.ndarray)
    assert decomp_stack.shape == (3, 1, 2, 2)
    assert head_labels == ["L0H0", "L0H1"]
    assert isinstance(head_stack, np.ndarray)
    assert head_stack.shape == (2, 1, 1, 2)
    assert neuron_labels == ["L0N0", "L0N1"]
    assert isinstance(neuron_stack, np.ndarray)
    assert neuron_stack.shape == (2, 1, 1)


def test_activation_cache_constructor_and_stack_activation_match_transformerlens_call_style() -> (
    None
):
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


def test_activation_cache_pos_slice_rejects_mismatched_boolean_mask() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1], [2], [3]]],
            "layer_0.resid_post": [[[4], [5], [6]]],
        }
    )

    with pytest.raises(IndexError, match="Boolean index has length"):
        cache.accumulated_resid(pos_slice=[True, False], return_labels=True)


def test_activation_cache_accumulated_resid_accepts_transformerlens_slice_like_object() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1], [2], [3]]],
            "layer_0.resid_post": [[[4], [5], [6]]],
        }
    )

    stack, labels = cache.accumulated_resid(
        pos_slice=_FakeSlice([2, 0], mode="array"),
        return_labels=True,
    )

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


def test_activation_cache_decoder_residual_decomposition_uses_prefixed_components() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[100, 100]]],
            "layer_0.resid_post": [[[200, 200]]],
            "layer_0.attn_out": [[[300, 300]]],
            "decoder.0.hook_resid_pre": [[[1, 10]]],
            "decoder.0.hook_resid_mid": [[[2, 20]]],
            "decoder.0.hook_resid_post": [[[3, 30]]],
            "decoder.0.hook_attn_out": [[[4, 40]]],
            "decoder.0.hook_cross_attn_out": [[[5, 50]]],
            "decoder.0.hook_mlp_out": [[[6, 60]]],
        }
    )

    default_stack, default_labels = cache.accumulated_resid(return_labels=True)
    decoder_stack, decoder_labels = cache.accumulated_resid(
        incl_mid=True,
        return_labels=True,
        stack="decoder",
    )
    decomp_stack, decomp_labels = cache.decompose_resid(
        incl_embeds=False,
        return_labels=True,
        stack="decoder",
    )

    assert default_labels == ["0_pre", "final_post"]
    assert default_stack == [[[[100, 100]]], [[[200, 200]]]]
    assert decoder_labels == ["0_pre", "0_mid", "final_post"]
    assert decoder_stack == [[[[1, 10]]], [[[2, 20]]], [[[3, 30]]]]
    assert decomp_labels == ["0_attn_out", "0_cross_attn_out", "0_mlp_out"]
    assert decomp_stack == [[[[4, 40]]], [[[5, 50]]], [[[6, 60]]]]


def test_activation_cache_decoder_residual_stack_uses_decoder_layer_count() -> None:
    class AsymmetricConfig:
        num_layers = 1
        num_decoder_layers = 2

    class AsymmetricModel:
        config = AsymmetricConfig()

    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[100]]],
            "layer_0.resid_post": [[[200]]],
            "decoder.0.hook_resid_pre": [[[1]]],
            "decoder.0.hook_resid_post": [[[2]]],
            "decoder.1.hook_resid_pre": [[[3]]],
            "decoder.1.hook_resid_post": [[[4]]],
        },
        model=AsymmetricModel(),
    )

    encoder_stack, encoder_labels = cache.accumulated_resid(return_labels=True)
    decoder_stack, decoder_labels = cache.accumulated_resid(
        return_labels=True,
        stack="decoder",
    )

    assert encoder_labels == ["0_pre", "final_post"]
    assert encoder_stack == [[[[100]]], [[[200]]]]
    assert decoder_labels == ["0_pre", "1_pre", "final_post"]
    assert decoder_stack == [[[[1]]], [[[3]]], [[[4]]]]


def test_activation_cache_decoder_negative_layer_keys_use_decoder_layer_count() -> None:
    class AsymmetricConfig:
        num_layers = 1
        num_decoder_layers = 2

    class AsymmetricModel:
        config = AsymmetricConfig()

    cache = ActivationCache(
        {
            "encoder.0.attn.hook_q": ["encoder_last"],
            "decoder.0.hook_resid_pre": ["decoder_first"],
            "decoder.1.hook_resid_pre": ["decoder_last"],
            "decoder.1.cross_attn.hook_q": ["cross_last"],
        },
        model=AsymmetricModel(),
    )

    assert cache[("q", -1)] == ["encoder_last"]
    assert cache[("decoder_resid_pre", -1)] == ["decoder_last"]
    assert cache[("cross_q", -1)] == ["cross_last"]


def test_activation_cache_decoder_layer_count_falls_back_to_decoder_cache_keys() -> None:
    cache = ActivationCache(
        {
            "decoder.0.hook_resid_pre": [[[1]]],
            "decoder.1.hook_resid_pre": [[[2]]],
            "decoder.1.hook_resid_post": [[[3]]],
        }
    )

    stack, labels = cache.accumulated_resid(return_labels=True, stack="decoder")

    assert labels == ["0_pre", "1_pre", "final_post"]
    assert stack == [[[[1]]], [[[2]]], [[[3]]]]


def test_activation_cache_decoder_layer_count_reads_nested_dict_configs() -> None:
    cache = ActivationCache(
        {
            "decoder.0.hook_resid_pre": [[[1]]],
            "decoder.1.hook_resid_pre": [[[2]]],
            "decoder.1.hook_resid_post": [[[3]]],
        },
        model=type(
            "NestedDictModel",
            (),
            {
                "config": {
                    "model_type": "wrapper",
                    "text_config": {"num_layers": 1, "num_decoder_layers": 2},
                }
            },
        )(),
    )

    stack, labels = cache.accumulated_resid(return_labels=True, stack="decoder")

    assert labels == ["0_pre", "1_pre", "final_post"]
    assert stack == [[[[1]]], [[[2]]], [[[3]]]]


def test_activation_cache_decoder_decompose_resid_uses_decoder_layernorm_scales() -> None:
    cache = ActivationCache(
        {
            "decoder.0.hook_attn_out": [[[10.0, 20.0]]],
            "decoder.0.hook_cross_attn_out": [[[30.0, 60.0]]],
            "decoder.0.ln1.hook_scale": [[[2.0, 2.0]]],
            "decoder.0.ln3.hook_scale": [[[10.0, 10.0]]],
            "blocks.0.ln2.hook_scale": [[[100.0, 100.0]]],
        },
        model=LogitAttributionModel(),
    )

    stack, labels = cache.decompose_resid(
        layer=0,
        mlp_input=True,
        mode="attn",
        apply_ln=True,
        incl_embeds=False,
        return_labels=True,
        stack="decoder",
    )

    assert labels == ["0_attn_out", "0_cross_attn_out"]
    assert stack == [[[[1.0, 2.0]]], [[[3.0, 6.0]]]]


def test_activation_cache_residual_decomposition_uses_top_level_write_aliases() -> None:
    cache = ActivationCache(
        {
            "layer_0.attn_out": [[2, 0]],
            "layer_0.mlp_out": [[0, 3]],
        }
    )
    cache["embed"] = [[1, 0]]
    cache["pos_embed"] = [[0, 1]]

    stack, labels = cache.decompose_resid(return_labels=True)

    assert labels == ["embed", "pos_embed", "0_attn_out", "0_mlp_out"]
    assert stack == [[[1, 0]], [[0, 1]], [[2, 0]], [[0, 3]]]


def test_activation_cache_residual_decomposition_respects_attn_only_models() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[1, 0]],
            "layer_0.attn_out": [[2, 0]],
            "layer_0.mlp_out": [[0, 99]],
            "layer_0.post": [[[123, 456]]],
        },
        model=AttnOnlyModel(),
    )

    stack, labels = cache.decompose_resid(return_labels=True)
    full_stack, full_labels = cache.get_full_resid_decomposition(return_labels=True)

    assert labels == ["embed", "0_attn_out"]
    assert stack == [[[1, 0]], [[2, 0]]]
    assert full_labels == ["0_attn_out", "embed"]
    assert full_stack == [[[2, 0]], [[1, 0]]]


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
    assert result_stack == [
        [[[[1.0, 2.0, 3.0], [15.0, 22.0, 4.0]], [[5.0, 6.0, 11.0], [31.0, 46.0, 8.0]]]]
    ]
    assert cache["layer_0.result"] == result_stack[0]
    assert cache["blocks.0.attn.hook_result"] == result_stack[0]
    assert cache.cache_dict["blocks.0.attn.hook_result"] == result_stack[0]
    assert head_labels == ["L0H0", "L0H1"]
    assert head_stack == [
        [[[1.0, 2.0, 3.0], [5.0, 6.0, 11.0]]],
        [[[15.0, 22.0, 4.0], [31.0, 46.0, 8.0]]],
    ]


def test_activation_cache_computes_head_results_from_transformerlens_block_w_o() -> None:
    cache = ActivationCache(
        {"blocks.0.attn.hook_z": [[[[1, 2], [3, 4]]]]},
        model=TransformerLensBlockWeightModel(
            W_O=[[[1, 0, 1], [0, 1, 1]], [[1, 2, 0], [3, 4, 1]]],
        ),
    )

    result_stack, labels = cache.compute_head_results(return_labels=True)

    assert labels == ["0_result"]
    assert result_stack == [[[[[1.0, 2.0, 3.0], [15.0, 22.0, 4.0]]]]]
    assert cache["blocks.0.attn.hook_result"] == result_stack[0]


def test_activation_cache_compute_head_results_reuses_cached_result_without_w_o() -> None:
    cache = ActivationCache({"blocks.0.attn.hook_result": [[[[1, 2]], [[3, 4]]]]})

    result_stack, labels = cache.compute_head_results(return_labels=True)
    sliced_stack = cache.compute_head_results(pos_slice=1)

    assert labels == ["0_result"]
    assert result_stack == [[[[[1, 2]], [[3, 4]]]]]
    assert sliced_stack == [[[[3, 4]]]]


def test_activation_cache_compute_head_results_reuses_result_and_computes_missing_z() -> None:
    cache = ActivationCache(
        {
            "blocks.0.attn.hook_result": [[[[1, 2]]]],
            "blocks.1.attn.hook_z": [[[[3, 4]]]],
        },
        model=HeadResultModel(W_O=[[[[0, 0], [0, 0]]], [[[1, 0], [0, 1]]]]),
    )

    result_stack, labels = cache.compute_head_results(return_labels=True)

    assert labels == ["0_result", "1_result"]
    assert result_stack == [[[[[1, 2]]]], [[[[3.0, 4.0]]]]]
    assert cache["blocks.1.attn.hook_result"] == [[[[3.0, 4.0]]]]


def test_activation_cache_compute_head_results_store_false_does_not_cache_aliases() -> None:
    cache = ActivationCache(
        {"blocks.0.attn.hook_z": [[[[1, 2]]]]},
        model=HeadResultModel(W_O=[[[[1, 0], [0, 1]]]]),
    )

    result_stack = cache.compute_head_results(store=False)

    assert result_stack == [[[[[1.0, 2.0]]]]]
    assert "layer_0.result" not in cache.cache_dict
    assert "blocks.0.attn.hook_result" not in cache.cache_dict


def test_activation_cache_stack_head_results_auto_computes_from_z() -> None:
    cache = ActivationCache(
        {"layer_0.z": [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]},
        model=HeadResultModel(W_O=[[[[1, 0, 1], [0, 1, 1]], [[1, 2, 0], [3, 4, 1]]]]),
    )

    head_stack, labels = cache.stack_head_results(pos_slice=[1], return_labels=True)

    assert labels == ["L0H0", "L0H1"]
    assert head_stack == [[[[5.0, 6.0, 11.0]]], [[[31.0, 46.0, 8.0]]]]
    assert cache["layer_0.result"] == [
        [
            [
                [1.0, 2.0, 3.0],
                [15.0, 22.0, 4.0],
            ],
            [
                [5.0, 6.0, 11.0],
                [31.0, 46.0, 8.0],
            ],
        ]
    ]


def test_activation_cache_stack_head_results_computes_missing_result_layers_from_z() -> None:
    cache = ActivationCache(
        {
            "layer_0.result": [[[[1, 10], [2, 20]]]],
            "layer_1.z": [[[[3, 4], [5, 6]]]],
        },
        model=HeadResultModel(
            W_O=[
                [[[0, 0], [0, 0]], [[0, 0], [0, 0]]],
                [[[1, 0], [0, 1]], [[1, 2], [3, 4]]],
            ]
        ),
    )

    head_stack, labels = cache.stack_head_results(return_labels=True)

    assert labels == ["L0H0", "L0H1", "L1H0", "L1H1"]
    assert head_stack == [
        [[[1, 10]]],
        [[[2, 20]]],
        [[[3.0, 4.0]]],
        [[[23.0, 34.0]]],
    ]
    assert cache["layer_1.result"] == [[[[3.0, 4.0], [23.0, 34.0]]]]


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


def test_activation_cache_stack_head_results_layer_zero_remainder_uses_resid_pre() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1, 2], [3, 4]]],
            "layer_0.resid_post": [[[10, 20], [30, 40]]],
            "layer_1.resid_post": [[[100, 200], [300, 400]]],
        }
    )

    head_stack, labels = cache.stack_head_results(
        layer=0,
        incl_remainder=True,
        pos_slice=[1],
        return_labels=True,
    )

    assert labels == ["remainder"]
    assert head_stack == [[[[3, 4]]]]


def test_activation_cache_stack_neuron_results_layer_zero_remainder_uses_resid_pre() -> None:
    cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1, 2], [3, 4]]],
            "layer_0.resid_post": [[[10, 20], [30, 40]]],
            "layer_1.resid_post": [[[100, 200], [300, 400]]],
        }
    )

    neuron_stack, labels = cache.stack_neuron_results(
        layer=0,
        incl_remainder=True,
        pos_slice=[1],
        return_labels=True,
    )

    assert labels == ["remainder"]
    assert neuron_stack == [[[[3, 4]]]]


def test_activation_cache_stack_head_results_layer_zero_returns_empty_stack() -> None:
    cache = ActivationCache({"hook_embed": [[[1, 2], [3, 4]]]})

    head_stack, labels = cache.stack_head_results(layer=0, return_labels=True)

    assert labels == []
    assert head_stack == []


def test_activation_cache_stack_head_results_requires_result_for_remainder() -> None:
    cache = ActivationCache(
        {
            "layer_0.q": [[[[1, 2]]]],
            "layer_0.resid_post": [[[3, 4]]],
        }
    )

    with pytest.raises(ValueError, match="residual-space `result`"):
        cache.stack_head_results(component="q", incl_remainder=True)


def test_activation_cache_stack_head_results_handles_attention_pattern_axes() -> None:
    cache = ActivationCache(
        {
            "layer_0.pattern": [
                [
                    [[1, 2, 3], [4, 5, 6]],
                    [[7, 8, 9], [10, 11, 12]],
                ]
            ],
            "layer_0.attn_scores": [
                [
                    [[-1, -2, -3], [-4, -5, -6]],
                    [[-7, -8, -9], [-10, -11, -12]],
                ]
            ],
        }
    )

    pattern_stack, pattern_labels = cache.stack_head_results(
        component="pattern",
        pos_slice=[1],
        return_labels=True,
    )
    scores_stack, scores_labels = cache.stack_head_results(
        component="attn_scores",
        pos_slice=1,
        return_labels=True,
    )

    assert pattern_labels == ["L0H0", "L0H1"]
    assert pattern_stack == [[[[4, 5, 6]]], [[[10, 11, 12]]]]
    assert scores_labels == ["L0H0", "L0H1"]
    assert scores_stack == [[[-4, -5, -6]], [[-10, -11, -12]]]


def test_activation_cache_empty_head_and_neuron_stacks_preserve_torch_shape() -> None:
    torch = pytest.importorskip("torch")
    cache = ActivationCache({"hook_embed": torch.zeros(1, 3, 2)})

    head_stack, head_labels = cache.stack_head_results(
        layer=0,
        pos_slice=slice(1, 3),
        return_labels=True,
    )
    neuron_stack, neuron_labels = cache.stack_neuron_results(
        layer=0,
        pos_slice=slice(1, 3),
        return_labels=True,
    )

    assert head_labels == []
    assert neuron_labels == []
    assert tuple(head_stack.shape) == (0, 1, 2, 2)
    assert tuple(neuron_stack.shape) == (0, 1, 2, 2)


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

    assert labels == ["L0H0", "embed"]
    assert stack == [[[[2, 0]]], [[1, 0]]]
    assert attrs == [12.0, 43.0]


def test_activation_cache_decoder_full_residual_decomposition_includes_self_and_cross_heads() -> (
    None
):
    cache = ActivationCache(
        {
            "decoder.0.attn.hook_result": [[[[1, 10], [2, 20]]]],
            "decoder.0.cross_attn.hook_result": [[[[3, 30], [4, 40]]]],
            "decoder.0.hook_mlp_out": [[[5, 50]]],
        }
    )

    stack, labels = cache.get_full_resid_decomposition(
        expand_neurons=True,
        return_labels=True,
        stack="decoder",
    )

    assert labels == [
        "L0H0_decoder",
        "L0H1_decoder",
        "L0H0_cross",
        "L0H1_cross",
        "0_mlp_out",
    ]
    assert stack == [
        [[[1, 10]]],
        [[[2, 20]]],
        [[[3, 30]]],
        [[[4, 40]]],
        [[[5, 50]]],
    ]


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


def test_activation_cache_gets_neuron_results_from_transformerlens_block_w_out() -> None:
    cache = ActivationCache(
        {"blocks.0.mlp.hook_post": [[[3, 4]]]},
        model=TransformerLensBlockWeightModel(W_out=[[1, 0], [0, 2]]),
    )

    result = cache.get_neuron_results(0)
    stack, labels = cache.stack_neuron_results(return_labels=True)

    assert result == [[[[3, 0], [0, 8]]]]
    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[[3, 0]]], [[[0, 8]]]]


def test_activation_cache_get_neuron_results_slices_numpy_arrays() -> None:
    np = pytest.importorskip("numpy")
    cache = ActivationCache(
        {"layer_0.post": np.array([[[3.0, 4.0, 5.0]]])},
        model=NeuronResultModel(W_out=np.array([[[1.0, 0.0], [0.0, 2.0], [3.0, 3.0]]])),
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


def test_activation_cache_neuron_results_projects_torch_weights_before_expansion() -> None:
    torch = pytest.importorskip("torch")
    cache = ActivationCache(
        {"layer_0.post": torch.tensor([[[3.0, 4.0]]])},
        model=NeuronResultModel(W_out=torch.tensor([[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]])),
    )

    projected_vector = cache.get_neuron_results(
        0,
        project_output_onto=torch.tensor([1.0, 0.0, -1.0]),
    )
    projected_matrix = cache.get_neuron_results(
        0,
        project_output_onto=torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]),
    )

    assert tuple(projected_vector.shape) == (1, 1, 2)
    torch.testing.assert_close(projected_vector, torch.tensor([[[-6.0, -8.0]]]))
    assert tuple(projected_matrix.shape) == (1, 1, 2, 2)
    torch.testing.assert_close(
        projected_matrix,
        torch.tensor([[[[12.0, 15.0], [40.0, 44.0]]]]),
    )


def test_activation_cache_stack_neuron_results_passes_projection_into_neuron_results() -> None:
    cache = ActivationCache(
        {"layer_0.post": [[[3, 4]]]},
        model=NeuronResultModel(W_out=[[[1, 2, 3], [4, 5, 6]]]),
    )
    seen_projections: list[Any] = []
    original = cache.get_neuron_results

    def tracking_get_neuron_results(*args: Any, **kwargs: Any) -> Any:
        seen_projections.append(kwargs.get("project_output_onto"))
        return original(*args, **kwargs)

    cache.get_neuron_results = tracking_get_neuron_results  # type: ignore[method-assign]

    stack, labels = cache.stack_neuron_results(
        project_output_onto=[1, 0, -1],
        return_labels=True,
    )

    assert seen_projections == [[1, 0, -1]]
    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[-6.0]], [[-8.0]]]


def test_activation_cache_stack_neuron_results_projects_after_layernorm() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2, 2, 2]]],
            "layer_0.post": [[[3, 4]]],
        },
        model=NeuronResultModel(W_out=[[[1, 2, 3], [4, 5, 6]]]),
    )
    seen_projections: list[Any] = []
    original = cache.get_neuron_results

    def tracking_get_neuron_results(*args: Any, **kwargs: Any) -> Any:
        seen_projections.append(kwargs.get("project_output_onto"))
        return original(*args, **kwargs)

    cache.get_neuron_results = tracking_get_neuron_results  # type: ignore[method-assign]

    stack, labels = cache.stack_neuron_results(
        apply_ln=True,
        project_output_onto=[1, 0, -1],
        return_labels=True,
    )

    assert seen_projections == [None]
    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[-3.0]], [[-4.0]]]


def test_activation_cache_stack_neuron_results_folds_layernorm_projection_matrix() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2.0]]],
            "layer_0.post": [[[3.0, 4.0]]],
        },
        model=type(
            "LayerNormNeuronProjectionModel",
            (),
            {
                "normalization_type": "LN",
                "W_out": [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]],
            },
        )(),
    )

    stack, labels = cache.stack_neuron_results(
        apply_ln=True,
        project_output_onto=[[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        return_labels=True,
    )

    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[[0.0, 1.5]]], [[[0.0, 2.0]]]]


def test_activation_cache_stack_neuron_results_folded_path_skips_neuron_expansion() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2.0]]],
            "layer_0.post": [[[3.0, 4.0]]],
        },
        model=NeuronResultModel(W_out=[[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]]),
    )

    def fail_get_neuron_results(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("folded LN projection path should not expand neuron results")

    cache.get_neuron_results = fail_get_neuron_results  # type: ignore[method-assign]

    stack, labels = cache.stack_neuron_results(
        apply_ln=True,
        project_output_onto=[1.0, 0.0, -1.0],
        return_labels=True,
    )

    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[-3.0]], [[-4.0]]]


def test_activation_cache_stack_neuron_results_folds_layernorm_vector_projection_shape() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2.0]]],
            "layer_0.post": [[[3.0, 4.0]]],
        },
        model=type(
            "LayerNormNeuronVectorProjectionModel",
            (),
            {
                "normalization_type": "LN",
                "W_out": [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]],
            },
        )(),
    )

    stack, labels = cache.stack_neuron_results(
        apply_ln=True,
        project_output_onto=[1.0, 0.0, -1.0],
        return_labels=True,
    )

    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[-3.0]], [[-4.0]]]


def test_activation_cache_cached_ln_scale_helper_slices_batch_and_position() -> None:
    cache = ActivationCache(
        {"blocks.0.ln1.hook_scale": [[[1.0], [2.0]], [[3.0], [4.0]]]},
        model=type("LayerNormScaleModel", (), {"n_layers": 1})(),
    )

    assert cache._get_cached_ln_scale(0, mlp_input=False, batch_slice=1, pos_slice=0) == [3.0]
    with pytest.raises(KeyError, match="Cached LN scale"):
        ActivationCache({}, model=type("NoScaleModel", (), {"n_layers": 1})())._get_cached_ln_scale(
            0,
            mlp_input=False,
        )


def test_activation_cache_stack_neuron_results_requires_output_weights_for_remainder() -> None:
    cache = ActivationCache(
        {
            "layer_0.post": [[[3, 5]]],
            "layer_0.resid_post": [[[11, 16]]],
        }
    )

    with pytest.raises(ValueError, match="W_out"):
        cache.stack_neuron_results(incl_remainder=True)


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


def test_activation_cache_full_decomposition_uses_mlp_out_without_output_weights() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[[1, 0]]],
            "layer_0.result": [[[[2, 0]]]],
            "layer_0.post": [[[10, 20, 30]]],
            "layer_0.mlp_out": [[[0, 3]]],
        }
    )

    stack, labels = cache.get_full_resid_decomposition(return_labels=True)

    assert labels == ["L0H0", "0_mlp_out", "embed"]
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


def test_activation_cache_full_decomposition_passes_projection_to_neuron_stack() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[[1.0, 2.0, 3.0]]],
            "layer_0.result": [[[[1.0, 0.0, 1.0]]]],
            "layer_0.post": [[[2.0]]],
        },
        model=NeuronResultModel(W_out=[[[3.0, 4.0, 5.0]]]),
    )
    seen: list[dict[str, Any]] = []
    original = cache.stack_neuron_results

    def tracking_stack_neuron_results(*args: Any, **kwargs: Any) -> Any:
        seen.append(
            {
                "project_output_onto": kwargs.get("project_output_onto"),
                "apply_ln": kwargs.get("apply_ln"),
            }
        )
        return original(*args, **kwargs)

    cache.stack_neuron_results = tracking_stack_neuron_results  # type: ignore[method-assign]

    stack, labels = cache.get_full_resid_decomposition(
        project_output_onto=[1.0, 0.0, -1.0],
        return_labels=True,
    )

    assert seen == [{"project_output_onto": [1.0, 0.0, -1.0], "apply_ln": False}]
    assert labels == ["L0H0", "L0N0", "embed"]
    assert stack == [[[0.0]], [[-4.0]], [[-2.0]]]


def test_activation_cache_full_decomposition_fuses_layernorm_projection_for_neurons() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2.0]]],
            "hook_embed": [[[3.0, 5.0, 7.0]]],
            "layer_0.result": [[[[1.0, 2.0, 3.0]]]],
            "layer_0.post": [[[4.0]]],
        },
        model=type(
            "LayerNormFullProjectionModel",
            (),
            {
                "normalization_type": "LN",
                "W_out": [[[2.0, 4.0, 8.0]]],
            },
        )(),
    )

    def fail_get_neuron_results(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("full decomposition should use folded LN projection for neurons")

    cache.get_neuron_results = fail_get_neuron_results  # type: ignore[method-assign]

    stack, labels = cache.get_full_resid_decomposition(
        apply_ln=True,
        project_output_onto=[1.0, 0.0, -1.0],
        return_labels=True,
    )

    assert labels == ["L0H0", "L0N0", "embed"]
    assert stack == [[[-1.0]], [[-12.0]], [[-2.0]]]


def test_activation_cache_full_decomposition_layernorm_projection_expands_bias_first() -> None:
    class LayerNormProjectionBiasModel:
        normalization_type = "LN"

        def accumulated_bias(
            self,
            layer: int,
            mlp_input: bool = False,
            include_mlp_biases: bool = True,
        ) -> Any:
            _ = layer, mlp_input, include_mlp_biases
            return [10.0, 40.0, 100.0]

    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2.0]]],
            "hook_embed": [[[3.0, 5.0, 7.0]]],
            "layer_0.result": [[[[1.0, 2.0, 3.0]]]],
        },
        model=LayerNormProjectionBiasModel(),
    )

    stack, labels = cache.get_full_resid_decomposition(
        apply_ln=True,
        project_output_onto=[1.0, 0.0, -1.0],
        return_labels=True,
    )

    assert labels == ["L0H0", "embed", "bias"]
    assert stack == [[[-1.0]], [[-2.0]], [[-45.0]]]


def test_activation_cache_full_decomposition_bias_tracks_neuron_expansion() -> None:
    cache = ActivationCache(
        {
            "hook_embed": [[[1.0, 2.0]]],
            "layer_0.attn_out": [[[3.0, 4.0]]],
            "layer_0.mlp_out": [[[5.0, 6.0]]],
            "layer_0.post": [[[1.0, 2.0]]],
            "layer_1.attn_out": [[[7.0, 8.0]]],
            "layer_1.mlp_out": [[[9.0, 10.0]]],
            "layer_1.post": [[[3.0, 4.0]]],
        },
        model=type(
            "BiasAndNeuronModel",
            (BiasOnlyModel,),
            {"W_out": [[[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.0], [0.0, 1.0]]]},
        )(),
    )

    expanded_stack, expanded_labels = cache.get_full_resid_decomposition(
        layer=2,
        expand_neurons=True,
        return_labels=True,
    )
    coarse_stack, coarse_labels = cache.get_full_resid_decomposition(
        layer=2,
        expand_neurons=False,
        return_labels=True,
    )

    assert expanded_labels == [
        "0_attn_out",
        "1_attn_out",
        "L0N0",
        "L0N1",
        "L1N0",
        "L1N1",
        "embed",
        "bias",
    ]
    assert coarse_labels == [
        "0_attn_out",
        "1_attn_out",
        "0_mlp_out",
        "1_mlp_out",
        "embed",
        "bias",
    ]
    assert expanded_stack[-1] == [[[22.0, 202.0]]]
    assert coarse_stack[-1] == [[[20.0, 200.0]]]


def test_activation_cache_coarse_full_decomposition_does_not_double_count_mlp_bias() -> None:
    class CoarseBiasModel:
        def accumulated_bias(
            self,
            layer: int,
            mlp_input: bool = False,
            include_mlp_biases: bool = True,
        ) -> Any:
            _ = mlp_input
            attn_bias = [10.0 * layer, 100.0 * layer]
            mlp_bias = [1.0 * layer, 2.0 * layer]
            if include_mlp_biases:
                return [attn_bias[0] + mlp_bias[0], attn_bias[1] + mlp_bias[1]]
            return attn_bias

    cache = ActivationCache(
        {
            "layer_0.attn_out": [[[3.0, 4.0]]],
            "layer_0.mlp_out": [[[6.0, 8.0]]],
            "layer_1.attn_out": [[[5.0, 6.0]]],
            "layer_1.mlp_out": [[[10.0, 12.0]]],
        },
        model=CoarseBiasModel(),
    )

    stack, labels = cache.get_full_resid_decomposition(
        layer=2,
        expand_neurons=False,
        return_labels=True,
    )

    summed = [sum(component[0][0][axis] for component in stack) for axis in range(2)]

    assert labels == ["0_attn_out", "1_attn_out", "0_mlp_out", "1_mlp_out", "bias"]
    assert stack[-1] == [[[20.0, 200.0]]]
    assert summed == [44.0, 230.0]


def test_activation_cache_full_decomposition_fallback_does_not_count_mlp_bias() -> None:
    class CoarseBiasModel:
        def accumulated_bias(
            self,
            layer: int,
            mlp_input: bool = False,
            include_mlp_biases: bool = True,
        ) -> Any:
            _ = mlp_input
            attn_bias = [10.0 * layer, 100.0 * layer]
            mlp_bias = [1.0 * layer, 2.0 * layer]
            if include_mlp_biases:
                return [attn_bias[0] + mlp_bias[0], attn_bias[1] + mlp_bias[1]]
            return attn_bias

    cache = ActivationCache(
        {
            "layer_0.attn_out": [[[3.0, 4.0]]],
            "layer_0.mlp_out": [[[6.0, 8.0]]],
            "layer_1.attn_out": [[[5.0, 6.0]]],
            "layer_1.mlp_out": [[[10.0, 12.0]]],
        },
        model=CoarseBiasModel(),
    )

    requested_expanded_stack, requested_expanded_labels = cache.get_full_resid_decomposition(
        layer=2,
        expand_neurons=True,
        return_labels=True,
    )
    coarse_stack, coarse_labels = cache.get_full_resid_decomposition(
        layer=2,
        expand_neurons=False,
        return_labels=True,
    )

    assert requested_expanded_labels == coarse_labels
    assert requested_expanded_stack == coarse_stack
    assert requested_expanded_stack[-1] == [[[20.0, 200.0]]]


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


def test_activation_cache_logit_attrs_applies_ln_to_tuple_backed_residuals() -> None:
    cache = ActivationCache({"ln_final.hook_scale": (((2.0,), (4.0,)),)})

    attrs = cache.logit_attrs(
        (((((8.0, 16.0), (8.0, 16.0)),),),),
        None,
        directions=((((1.0, 0.0), (0.0, 1.0)),),),
    )

    assert attrs == [[[[4.0, 4.0]]]]


def test_activation_cache_logit_attrs_accepts_string_tokens_and_checks_logit_diff_shape() -> None:
    cache = ActivationCache(model=LogitAttributionModel())

    assert cache.logit_attrs([[1, 2], [3, 4]], " yes", apply_ln=False) == [1.0, 3.0]
    assert cache.logit_attrs([[1, 2], [3, 4]], " yes", incorrect_tokens=" no", apply_ln=False) == [
        -1.0,
        -1.0,
    ]
    assert cache.logit_attrs([[1, 2], [3, 4]], " yes", " no", apply_ln=False) == [
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


def test_activation_cache_logit_attrs_accepts_transformerlens_positional_slices() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2], [4], [8]], [[10], [20], [40]]]},
        model=LogitAttributionModel(),
    )

    attrs = cache.logit_attrs(
        [
            [[[8, 16], [8, 16], [16, 24]], [[10, 10], [20, 20], [40, 40]]],
            [[[4, 8], [4, 8], [8, 12]], [[1, 2], [3, 4], [5, 6]]],
        ],
        [[1, 2, 3], [3, 2, 1]],
        None,
        [2, 0],
        0,
        True,
    )

    assert attrs == [[5.0, 4.0], [2.5, 2.0]]


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


def test_activation_cache_logit_attrs_slices_batchless_position_directions() -> None:
    cache = ActivationCache()

    attrs = cache.logit_attrs(
        [[[[10, 1], [20, 2]]]],
        None,
        directions=[[1, 0], [0, 1], [1, 1]],
        apply_ln=False,
        pos_slice=[2, 0],
    )

    assert attrs == [[[11.0, 20.0]]]


def test_activation_cache_logit_attrs_slices_batch_directions_without_pos_slice() -> None:
    cache = ActivationCache()

    attrs = cache.logit_attrs(
        [[[[10, 1]], [[20, 2]]]],
        None,
        directions=[[1, 0], [0, 1]],
        apply_ln=False,
        batch_slice=1,
    )

    assert attrs == [[2.0]]


def test_activation_cache_logit_attrs_slices_batch_then_position_directions() -> None:
    cache = ActivationCache()

    attrs = cache.logit_attrs(
        [
            [[10, 1, 0], [30, 3, 0]],
            [[50, 5, 0], [70, 7, 0]],
        ],
        None,
        directions=[
            [[1, 0, 0], [0, 1, 0]],
            [[1, 1, 0], [1, -1, 0]],
        ],
        apply_ln=False,
        batch_slice=1,
        pos_slice=0,
    )

    assert attrs == [33.0, 77.0]


def test_activation_cache_logit_attrs_applies_final_scale_to_batchless_pos_slice() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[2.0], [4.0]],
        },
        has_batch_dim=False,
    )

    attrs = cache.logit_attrs(
        [
            [8.0, 16.0],
            [4.0, 12.0],
        ],
        None,
        directions=[1.0, 0.0],
        apply_ln=True,
        pos_slice=1,
        has_batch_dim=False,
    )

    assert attrs == [2.0, 1.0]


def test_activation_cache_logit_attrs_keeps_batch_directions_with_pos_slice() -> None:
    cache = ActivationCache()

    attrs = cache.logit_attrs(
        [[[30, 3], [60, 6]]],
        None,
        directions=[[1, 0], [0, 1]],
        apply_ln=False,
        pos_slice=-1,
    )

    assert attrs == [[30.0, 6.0]]


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


def test_activation_cache_logit_attrs_slices_full_residual_stack_for_explicit_positions() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2], [4], [8]]]},
        model=LogitAttributionModel(),
    )

    attrs = cache.logit_attrs(
        [[[[4.0, 8.0], [8.0, 16.0], [16.0, 24.0]]]],
        [[1, 2, 3]],
        pos_slice=[2, 0],
    )

    assert attrs == [[[5.0, 2.0]]]


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


def test_activation_cache_logit_attrs_slices_batch_for_unstacked_residuals() -> None:
    cache = ActivationCache()

    attrs = cache.logit_attrs(
        [
            [[10.0, 1.0], [20.0, 2.0]],
            [[30.0, 3.0], [40.0, 4.0]],
        ],
        None,
        directions=[
            [[1.0, 0.0], [0.0, 1.0]],
            [[1.0, 1.0], [1.0, -1.0]],
        ],
        apply_ln=False,
        batch_slice=1,
    )

    assert attrs == [33.0, 36.0]


def test_activation_cache_logit_attrs_slices_torch_batch_for_unstacked_residuals() -> None:
    torch = pytest.importorskip("torch")
    cache = ActivationCache()

    attrs = cache.logit_attrs(
        torch.tensor(
            [
                [[10.0, 1.0], [20.0, 2.0]],
                [[30.0, 3.0], [40.0, 4.0]],
            ]
        ),
        None,
        directions=torch.tensor(
            [
                [[1.0, 0.0], [0.0, 1.0]],
                [[1.0, 1.0], [1.0, -1.0]],
            ]
        ),
        apply_ln=False,
        batch_slice=1,
    )

    assert torch.equal(attrs, torch.tensor([33.0, 36.0]))


def test_activation_cache_logit_attrs_slices_residual_pos_after_integer_batch_slice() -> None:
    torch = pytest.importorskip("torch")
    cache = ActivationCache(
        {
            "ln_final.hook_scale": torch.tensor(
                [
                    [[1.0], [2.0], [4.0]],
                    [[5.0], [10.0], [20.0]],
                ]
            )
        }
    )
    residual_stack = torch.arange(2 * 2 * 3 * 3, dtype=torch.float32).reshape(2, 2, 3, 3)

    attrs = cache.logit_attrs(
        residual_stack,
        None,
        directions=torch.ones(2, 3),
        batch_slice=1,
        pos_slice=[2, 0],
    )

    expected = (
        residual_stack[:, 1][:, [2, 0]] / torch.tensor([[[20.0], [5.0]]]) * torch.ones(2, 3)
    ).sum(dim=-1)
    assert torch.allclose(attrs, expected)


def test_activation_cache_apply_ln_slices_batch_and_position_scales() -> None:
    cache = ActivationCache({"ln_final.hook_scale": [[[2], [4]], [[8], [16]]]})

    assert cache.apply_ln_to_stack(
        [[[[0, 0]], [[16, 32]]]],
        layer=-1,
        batch_slice=1,
        pos_slice=slice(1, 2),
    ) == [[[1.0, 2.0]]]


def test_activation_cache_apply_ln_slices_position_scale_for_batchless_residual_override() -> None:
    cache = ActivationCache({"ln_final.hook_scale": [[[2.0], [4.0]]]})

    assert cache.apply_ln_to_stack(
        [[[8.0, 16.0], [4.0, 12.0]]],
        layer=-1,
        pos_slice=1,
        has_batch_dim=False,
    ) == [[[2.0, 4.0], [1.0, 3.0]]]


def test_activation_cache_logit_attrs_slices_position_scale_for_batchless_residual_override() -> (
    None
):
    cache = ActivationCache({"ln_final.hook_scale": [[[2.0], [4.0]]]})

    attrs = cache.logit_attrs(
        [[[8.0, 16.0], [4.0, 12.0]]],
        None,
        directions=[1.0, 0.0],
        pos_slice=1,
        has_batch_dim=False,
    )

    assert attrs == [1.0]


def test_activation_cache_canonicalizes_top_level_layernorm_scale_writes() -> None:
    cache = ActivationCache()

    cache["scale"] = [[[2]]]

    assert cache.to_dict() == {"ln_final.hook_scale": [[[2]]]}
    assert cache.apply_ln_to_stack([[[[8, 16]]]], layer=-1) == [[[[4.0, 8.0]]]]

    cache[("hook_scale",)] = [[[4]]]

    assert cache.to_dict() == {"ln_final.hook_scale": [[[4]]]}
    assert cache.apply_ln_to_stack([[[[8, 16]]]], layer=-1) == [[[[2.0, 4.0]]]]


def test_activation_cache_reads_top_level_layernorm_aliases() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2]]],
            "ln_final.hook_normalized": [[[1, -1]]],
        }
    )

    assert cache["scale"] == [[[2]]]
    assert cache["hook_scale"] == [[[2]]]
    assert cache[("scale",)] == [[[2]]]
    assert cache[("hook_scale",)] == [[[2]]]
    assert cache["normalized"] == [[[1, -1]]]
    assert cache["hook_normalized"] == [[[1, -1]]]
    assert cache[("hook_normalized",)] == [[[1, -1]]]
    assert cache.keys_matching("hook_scale") == ["ln_final.hook_scale"]
    assert cache.select("hook_normalized").to_dict() == {"ln_final.hook_normalized": [[[1, -1]]]}


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
    assert cache.apply_ln_to_stack(residual_stack, layer=0, mlp_input=True) == [[[[2.0, 4.0]]]]
    assert cache.apply_ln_to_stack(residual_stack, layer=-1) == [[[[0.08, 0.16]]]]


def test_activation_cache_decompose_resid_uses_mlp_input_layernorm_scale() -> None:
    cache = ActivationCache(
        {
            "layer_0.attn_out": [[[10.0, 20.0]]],
            "blocks.0.ln1.hook_scale": [[[2.0, 2.0]]],
            "blocks.0.ln2.hook_scale": [[[10.0, 10.0]]],
        }
    )

    stack, labels = cache.decompose_resid(
        layer=0,
        mlp_input=True,
        mode="attn",
        apply_ln=True,
        return_labels=True,
    )

    assert labels == ["0_attn_out"]
    assert stack == [[[[1.0, 2.0]]]]


def test_activation_cache_full_decomposition_uses_mlp_input_layernorm_scale() -> None:
    cache = ActivationCache(
        {
            "layer_0.result": [[[[10.0, 20.0]]]],
            "blocks.0.ln1.hook_scale": [[[2.0, 2.0]]],
            "blocks.0.ln2.hook_scale": [[[10.0, 10.0]]],
        }
    )

    stack, labels = cache.get_full_resid_decomposition(
        layer=0,
        mlp_input=True,
        expand_neurons=False,
        apply_ln=True,
        return_labels=True,
    )

    assert labels == ["L0H0"]
    assert stack == [[[[1.0, 2.0]]]]


def test_activation_cache_head_remainder_subtracts_tuple_backed_components() -> None:
    cache = ActivationCache(
        {
            "layer_0.result": ((((1.0, 2.0), (3.0, 4.0)),),),
            "layer_0.resid_post": (((10.0, 20.0),),),
        }
    )

    stack, labels = cache.stack_head_results(layer=1, incl_remainder=True, return_labels=True)

    assert labels == ["L0H0", "L0H1", "remainder"]
    assert stack == [[[[1.0, 2.0]]], [[[3.0, 4.0]]], [[[6.0, 14.0]]]]


def test_activation_cache_neuron_results_project_tuple_backed_outputs() -> None:
    class TupleNeuronModel:
        W_out = (((10.0, 0.0), (0.0, 20.0)),)

    cache = ActivationCache(
        {"layer_0.mlp.post": (((2.0, 3.0),),)},
        model=TupleNeuronModel(),
    )

    assert cache.get_neuron_results(0) == [[[[20.0, 0.0], [0.0, 60.0]]]]
    stack, labels = cache.stack_neuron_results(layer=1, return_labels=True)
    assert labels == ["L0N0", "L0N1"]
    assert stack == [[[[20.0, 0.0]]], [[[0.0, 60.0]]]]


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


def test_activation_cache_apply_ln_noops_for_explicit_non_layernorm_models() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2]]]},
        model=type("NoNormModel", (), {"normalization_type": "none"})(),
    )

    assert cache.apply_ln_to_stack([[[[8, 16]]]], layer=-1) == [[[[8, 16]]]]


def test_activation_cache_apply_ln_requires_scale_for_explicit_layernorm_models() -> None:
    cache = ActivationCache(model=LayerNormAttributionModel())

    with pytest.raises(KeyError, match="Cached LN scale"):
        cache.apply_ln_to_stack([[[[2.0, 6.0]]]], layer=-1)
    with pytest.raises(KeyError, match="Cached LN scale"):
        cache.logit_attrs([[[[2.0, 6.0]]]], " yes")


def test_activation_cache_apply_ln_requires_requested_intermediate_scale() -> None:
    cache = ActivationCache(
        {"blocks.0.ln2.hook_scale": [[[10.0]]]},
        model=LogitAttributionModel(),
    )

    with pytest.raises(KeyError, match="blocks\\.0\\.ln1\\.hook_scale"):
        cache.apply_ln_to_stack([[[[8.0, 16.0]]]], layer=0, mlp_input=False)


def test_activation_cache_logit_attrs_uses_centered_layernorm_for_ln_models() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2]]]},
        model=LayerNormAttributionModel(),
    )

    assert cache.logit_attrs([[[[2, 6]]]], " yes") == [[[-1.0]]]


def test_activation_cache_projects_residual_stack_to_logits() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[2], [4]]]},
        model=LogitLensModel(),
    )

    logits = cache.residual_stack_to_logits(
        [[[[8, 16], [4, 12]]]],
        pos_slice=1,
        use_unembed_bias=True,
    )

    assert logits == [[[1.5, 2.0, 14.0]]]


def test_activation_cache_residual_stack_to_logits_uses_top_level_scale_alias() -> None:
    cache = ActivationCache(model=LogitLensModel())
    cache["scale"] = [[[2], [4]]]

    logits = cache.residual_stack_to_logits(
        [[[[8, 16], [4, 12]]]],
        pos_slice=1,
        use_unembed_bias=True,
    )

    assert logits == [[[1.5, 2.0, 14.0]]]


def test_activation_cache_residual_stack_to_logits_slices_batch_then_position_axis() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[1], [1]], [[2], [2]]]},
        model=LogitLensModel(),
    )

    logits = cache.residual_stack_to_logits(
        [[[[1, 10], [2, 20]], [[3, 30], [4, 40]]]],
        apply_ln=False,
        batch_slice=1,
        pos_slice=0,
        use_unembed_bias=False,
    )

    assert logits == [[3.0, 30.0, 33.0]]


def test_activation_cache_residual_stack_to_logits_slices_batch_then_position_after_ln() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[1], [1]], [[2], [2]]]},
        model=LogitLensModel(),
    )

    logits = cache.residual_stack_to_logits(
        [[[[1, 10], [2, 20]], [[3, 30], [4, 40]]]],
        batch_slice=1,
        pos_slice=0,
        use_unembed_bias=False,
    )

    assert logits == [[1.5, 15.0, 16.5]]


def test_activation_cache_residual_stack_to_logits_accepts_explicit_position_indices_after_ln() -> (
    None
):
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[1.0], [2.0], [4.0]]]},
        model=LogitLensModel(),
    )

    logits = cache.residual_stack_to_logits(
        [[[[1.0, 10.0], [2.0, 20.0], [4.0, 40.0]]]],
        pos_slice=[2, 0],
        use_unembed_bias=False,
    )

    assert logits == [[[[1.0, 10.0, 11.0], [1.0, 10.0, 11.0]]]]


def test_activation_cache_residual_stack_to_logits_preserves_unwrapped_pos_after_ln() -> None:
    cache = ActivationCache(
        {"ln_final.hook_scale": [[[1.0], [2.0], [4.0]]]},
        model=LogitLensModel(),
    )

    logits = cache.residual_stack_to_logits(
        [[[[1.0, 10.0], [2.0, 20.0], [4.0, 40.0]]]],
        pos_slice=Slice.unwrap(2),
        use_unembed_bias=False,
    )

    assert logits == [[[[1.0, 10.0, 11.0]]]]


def test_activation_cache_accumulated_resid_to_logits_returns_labels() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2]]],
            "layer_0.resid_pre": [[[2, 4]]],
            "layer_0.resid_post": [[[6, 8]]],
        },
        model=LogitLensModel(),
    )

    logits, labels = cache.accumulated_resid_to_logits(return_labels=True)

    assert labels == ["0_pre", "final_post"]
    assert logits == [
        [[[1.5, 1.0, 13.0]]],
        [[[3.5, 3.0, 17.0]]],
    ]


def test_activation_cache_decompose_resid_to_logits_omits_bias_by_default() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2]]],
            "hook_embed": [[[2, 4]]],
            "layer_0.attn_out": [[[6, 8]]],
        },
        model=LogitLensModel(),
    )

    logits, labels = cache.decompose_resid_to_logits(return_labels=True)

    assert labels == ["embed", "0_attn_out"]
    assert logits == [
        [[[1.0, 2.0, 3.0]]],
        [[[3.0, 4.0, 7.0]]],
    ]


def test_activation_cache_decoder_residual_helpers_project_to_logits() -> None:
    cache = ActivationCache(
        {
            "ln_final.hook_scale": [[[2.0], [4.0]]],
            "decoder.0.hook_resid_pre": [[[2.0, 4.0], [8.0, 16.0]]],
            "decoder.0.hook_resid_post": [[[6.0, 8.0], [16.0, 32.0]]],
            "decoder.0.hook_attn_out": [[[10.0, 20.0], [20.0, 40.0]]],
            "decoder.0.hook_cross_attn_out": [[[30.0, 60.0], [40.0, 80.0]]],
            "decoder.0.hook_mlp_out": [[[50.0, 100.0], [60.0, 120.0]]],
        },
        model=LogitLensModel(),
    )

    accum_logits, accum_labels = cache.accumulated_resid_to_logits(
        pos_slice=1,
        return_labels=True,
        use_unembed_bias=False,
        stack="decoder",
    )
    decomp_logits, decomp_labels = cache.decompose_resid_to_logits(
        pos_slice=1,
        incl_embeds=False,
        return_labels=True,
        stack="decoder",
    )

    assert accum_labels == ["0_pre", "final_post"]
    assert accum_logits == [[[2.0, 4.0, 6.0]], [[4.0, 8.0, 12.0]]]
    assert decomp_labels == ["0_attn_out", "0_cross_attn_out", "0_mlp_out"]
    assert decomp_logits == [
        [[5.0, 10.0, 15.0]],
        [[10.0, 20.0, 30.0]],
        [[15.0, 30.0, 45.0]],
    ]


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


def test_dummy_wrapper_propagates_internal_type_errors_with_activation_signature() -> None:
    model = DummyModelWrapper()

    def broken(value: dict[str, Any], hook: Any) -> dict[str, Any]:
        _ = value, hook
        raise TypeError("dummy hook inner bug")

    model.add_hook(0, broken)

    with pytest.raises(TypeError, match="dummy hook inner bug"):
        model.run_with_cache({"text": "hello"}, layers=[0])


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


def test_patch_indexing_supports_ellipsis_for_list_backend() -> None:
    assert get_indexed([[1, 2, 3], [4, 5, 6]], (..., -1)) == [3, 6]

    value = [[0, 0, 0], [0, 0, 0]]
    set_indexed(value, (..., -1), [3, 6])

    assert value == [[0, 0, 3], [0, 0, 6]]


def test_apply_patch_replaces_and_adds_ellipsis_slices_for_list_backend() -> None:
    clean_cache = ActivationCache({"layer_0": [[1, 2, 3], [4, 5, 6]]})
    corrupted = [[0, 0, 0], [0, 0, 0]]

    replaced = apply_patch(
        corrupted,
        PatchSpec(layer=0, target_index=(..., -1)),
        clean_cache,
    )
    added = apply_patch(
        corrupted,
        PatchSpec(layer=0, target_index=(..., -1), mode="add", scale=2.0),
        clean_cache,
    )

    assert replaced == [[0, 0, 3], [0, 0, 6]]
    assert added == [[0, 0, 6.0], [0, 0, 12.0]]
    assert corrupted == [[0, 0, 0], [0, 0, 0]]


def test_apply_patch_replaces_and_adds_numpy_activation_slices() -> None:
    np = pytest.importorskip("numpy")
    clean_cache = ActivationCache({"layer_0.resid_pre": np.array([[[10.0, 20.0], [30.0, 40.0]]])})
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


def test_patch_hook_accepts_transformerlens_two_argument_call() -> None:
    hook_context = type("TransformerLensHookContext", (), {"name": "blocks.0.hook_resid_pre"})()
    hook = make_patch_hook(
        PatchSpec(layer="blocks.0.hook_resid_pre", target_index=1),
        ActivationCache({"blocks.0.hook_resid_pre": [10, 20, 30]}),
    )

    patched = hook([0, 0, 0], hook_context)

    assert patched == [0, 20, 0]


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


def test_generic_activation_patch_accepts_numpy_size_one_metric_outputs() -> None:
    np = pytest.importorskip("numpy")
    model = ToyWrapper([0, 0, 0])
    clean_cache = ActivationCache({"layer_0": [10, 20, 30]})
    spec = PatchSpec(layer=0, target_index=1)

    results = generic_activation_patch(
        model,
        {"activation": [0, 0, 0]},
        clean_cache,
        spec,
        metric=lambda output: np.array([sum(output["activation"])]),
    )

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
    metric_output, index_df = format_patch_results(
        results,
        ("layer", "pos"),
        return_details=False,
        return_index_df=True,
    )
    assert metric_output == [[10.0, 30.0]]
    assert _index_records(index_df) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 2}]


def test_return_index_df_uses_pandas_dataframe_when_available() -> None:
    pd = pytest.importorskip("pandas")
    results = [
        PatchResult(PatchSpec(layer=0, target_index=(0, 0)), 1.0, {}, {}),
        PatchResult(PatchSpec(layer=0, target_index=(0, 1)), 2.0, {}, {}),
    ]

    index_df = patch_results_to_index_df(results, ("layer", "pos"))

    assert isinstance(index_df, pd.DataFrame)
    assert list(index_df.columns) == ["layer", "pos"]
    assert _index_records(index_df) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_metric_output_helpers_accept_tuple_backed_metrics() -> None:
    from SafeLens.core.patching import (
        _move_axis,
        _pad_metric_last_dim,
        _stack_named_metric_outputs,
    )

    assert _stack_named_metric_outputs([("q", ((1, 2),)), ("k", ((3, 4),))]) == [
        [[1, 2]],
        [[3, 4]],
    ]
    assert _pad_metric_last_dim(((1, 2),), 4) == [[1, 2, 0.0, 0.0]]
    assert _move_axis(((1, 2), (3, 4)), 0, 1) == [[1, 3], [2, 4]]


def test_generic_activation_patch_accepts_transformerlens_style_call() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache(
        {
            "blocks.0.hook_resid_pre": [[[1], [2]]],
        }
    )

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
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
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_accepts_transformerlens_positional_signature() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
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
    )

    assert grid == [[1.0, 2.0]]
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_transformerlens_call_defaults_to_metric_grid() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
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


def test_generic_activation_patch_clones_gradient_tracked_activation_for_tl_setters() -> None:
    torch = pytest.importorskip("torch")
    corrupted = torch.zeros(1, 2, 1, requires_grad=True)
    model = ComponentWrapper(corrupted)
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": torch.tensor([[[1.0], [2.0]]])})

    def tl_inplace_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
        _layer, pos = index
        corrupted_activation[:, pos, :] = clean_activation[:, pos, :]
        return corrupted_activation

    grid = generic_activation_patch(
        model,
        {"activation": corrupted},
        clean_cache,
        patching_metric=lambda output: output["activation"].detach().sum(),
        patch_setter=tl_inplace_setter,
        activation_name="resid_pre",
        index_axis_names=("layer", "pos"),
    )

    assert torch.equal(torch.as_tensor(grid), torch.tensor([[1.0, 2.0]]))
    assert torch.equal(corrupted, torch.zeros_like(corrupted))


def test_generic_activation_patch_propagates_internal_type_errors_from_tl_setter() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def broken_tl_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
        _ = corrupted_activation, index, clean_activation
        raise TypeError("setter inner bug")

    with pytest.raises(TypeError, match="setter inner bug"):
        generic_activation_patch(
            model,
            {"activation": [[[0], [0]]]},
            clean_cache,
            patching_metric=lambda output: _nested_sum(output["activation"]),
            patch_setter=broken_tl_setter,
            activation_name="resid_pre",
            index_axis_names=("layer", "pos"),
        )


def test_generic_activation_patch_propagates_type_errors_from_ambiguous_setter() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def ambiguous_setter(corrupted_activation: Any, second: Any, third: Any) -> Any:
        _ = third
        if isinstance(second, list):
            raise TypeError("ambiguous setter inner bug")
        return corrupted_activation

    with pytest.raises(TypeError, match="ambiguous setter inner bug"):
        generic_activation_patch(
            model,
            {"activation": [[[0], [0]]]},
            clean_cache,
            patching_metric=lambda output: _nested_sum(output["activation"]),
            patch_setter=ambiguous_setter,
            activation_name="resid_pre",
            index_axis_names=("layer", "pos"),
        )


def test_generic_activation_patch_transformerlens_call_infers_layers_from_safelens_cache() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
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
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_infers_layers_from_encoder_decoder_cache_names() -> None:
    model = ComponentMapWrapper({"encoder.0.hook_q_input": [[[0], [0]]]})
    clean_cache = ActivationCache(
        {
            "encoder.0.hook_q_input": [[[3], [4]]],
            "decoder.0.attn.hook_q": [[[[5]]]],
            "decoder.0.cross_attn.hook_q": [[[[6]]]],
        }
    )

    def tl_layer_pos_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    grid, index_table = generic_activation_patch(
        model,
        {},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=tl_layer_pos_setter,
        activation_name="encoder.0.hook_q_input",
        index_axis_names=("layer", "pos"),
        return_details=False,
        return_index_df=True,
    )

    assert infer_layers(
        model,
        clean_cache,
        "q_input",
        name_style="transformer_lens",
    ) == [0]
    assert infer_layers(
        model,
        clean_cache,
        "decoder_q",
        name_style="transformer_lens",
    ) == [0]
    assert infer_layers(
        model,
        clean_cache,
        "cross_q",
        name_style="transformer_lens",
    ) == [0]
    assert grid == [[3.0, 4.0]]
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_infers_decoder_layers_from_model_config() -> None:
    class _Config:
        n_layers = 1
        num_decoder_layers = 2

    class _Seq2SeqModel(ComponentMapWrapper):
        cfg = _Config()

    model = _Seq2SeqModel(
        {
            "decoder.0.cross_attn.hook_q": [[[[0]], [[0]]]],
            "decoder.1.cross_attn.hook_q": [[[[0]], [[0]]]],
        }
    )
    clean_cache = ActivationCache()

    assert infer_layers(model, clean_cache, "resid_pre") == [0]
    assert infer_layers(model, clean_cache, "decoder_q") == [0, 1]
    assert infer_layers(model, clean_cache, "cross_q") == [0, 1]

    grid, index_table = generic_activation_patch(
        model,
        {},
        ActivationCache(
            {
                "decoder.0.cross_attn.hook_q": [[[[1]], [[2]]]],
                "decoder.1.cross_attn.hook_q": [[[[3]], [[4]]]],
            }
        ),
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=layer_pos_head_vector_patch_setter,
        activation_name="cross_q",
        index_axis_names=("layer", "pos", "head"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[[1.0], [2.0]], [[3.0], [4.0]]]
    assert _index_records(index_table) == [
        {"layer": 0, "pos": 0, "head": 0},
        {"layer": 0, "pos": 1, "head": 0},
        {"layer": 1, "pos": 0, "head": 0},
        {"layer": 1, "pos": 1, "head": 0},
    ]


def test_infer_layers_reads_nested_decoder_config_for_decoder_components() -> None:
    class _NestedConfigModel:
        config = {"num_layers": 1, "decoder": {"num_decoder_layers": 3}}

    model = _NestedConfigModel()

    assert infer_layers(model, ActivationCache(), "resid_pre") == [0]
    assert infer_layers(model, ActivationCache(), "decoder_resid_pre") == [0, 1, 2]
    assert infer_layers(model, ActivationCache(), "cross_q") == [0, 1, 2]


def test_generic_activation_patch_accepts_full_transformerlens_activation_name() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
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
        activation_name="blocks.0.hook_resid_pre",
        index_axis_names=("layer", "pos"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[1.0, 2.0]]
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_accepts_full_safelens_activation_name() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
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
        activation_name="layer_0.resid_pre",
        index_axis_names=("layer", "pos"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[1.0, 2.0]]
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_accepts_transformerlens_positional_call() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
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
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_accepts_explicit_transformerlens_index_table() -> None:
    model = ComponentWrapper([[[0], [0], [0]]])
    clean_cache = ActivationCache(
        {
            "blocks.0.hook_resid_pre": [[[10], [20], [30]]],
        }
    )

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
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
    assert _index_records(index_table) == [{"layer": 0, "pos": 2}, {"layer": 0, "pos": 0}]


def test_component_patch_helper_accepts_transformerlens_partial_style_overrides() -> None:
    model = ComponentWrapper([[[0], [0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[10], [20], [30]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    metrics, index_table = get_act_patch_resid_pre(
        model,
        {"activation": [[[0], [0], [0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=tl_layer_pos_setter,
        activation_name="resid_pre",
        index_axis_names=("layer", "pos"),
        index_df=[{"layer": 0, "pos": 2}, {"layer": 0, "pos": 0}],
        return_index_df=True,
    )

    assert metrics == [30.0, 10.0]
    assert _index_records(index_table) == [{"layer": 0, "pos": 2}, {"layer": 0, "pos": 0}]


def test_generic_activation_patch_requires_layer_first_in_explicit_tl_index_table() -> None:
    model = ComponentWrapper([[[0], [0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[10], [20], [30]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    with pytest.raises(ValueError, match="layer.*first column"):
        generic_activation_patch(
            model,
            {"activation": [[[0], [0], [0]]]},
            clean_cache,
            patching_metric=lambda output: _nested_sum(output["activation"]),
            patch_setter=tl_layer_pos_setter,
            activation_name="resid_pre",
            index_df=[{"pos": 2, "layer": 0}],
            return_details=False,
        )


def test_generic_activation_patch_rejects_explicit_tl_rows_with_mismatched_columns() -> None:
    model = ComponentWrapper([[[0], [0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[10], [20], [30]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    with pytest.raises(ValueError, match="same columns"):
        generic_activation_patch(
            model,
            {"activation": [[[0], [0], [0]]]},
            clean_cache,
            patching_metric=lambda output: _nested_sum(output["activation"]),
            patch_setter=tl_layer_pos_setter,
            activation_name="resid_pre",
            index_df=[{"layer": 0, "pos": 2}, {"layer": 0}],
            return_details=False,
        )


def test_make_df_from_ranges_matches_transformerlens_index_table_shape() -> None:
    index_df = make_df_from_ranges((2, 3), ("layer", "pos"))
    records, columns = normalize_index_table(index_df)

    assert tuple(columns) == ("layer", "pos")
    assert records == [
        {"layer": 0, "pos": 0},
        {"layer": 0, "pos": 1},
        {"layer": 0, "pos": 2},
        {"layer": 1, "pos": 0},
        {"layer": 1, "pos": 1},
        {"layer": 1, "pos": 2},
    ]


def test_make_transformer_lens_patch_specs_accepts_dataframe_index_tables() -> None:
    from SafeLens.core.patching import make_transformer_lens_patch_specs

    specs = make_transformer_lens_patch_specs(
        "resid_pre",
        make_df_from_ranges((1, 2), ("layer", "pos")),
        patch_setter=layer_pos_patch_setter,
    )

    assert [spec.layer for spec in specs] == [
        "blocks.0.hook_resid_pre",
        "blocks.0.hook_resid_pre",
    ]
    assert [spec.target_index for spec in specs] == [(0, 0), (0, 1)]


def test_generic_activation_patch_accepts_make_df_from_ranges_output() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[3], [4]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    metrics, index_table = generic_activation_patch(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=tl_layer_pos_setter,
        activation_name="resid_pre",
        index_df=make_df_from_ranges((1, 2), ("layer", "pos")),
        return_index_df=True,
    )

    assert metrics == [3.0, 4.0]
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_component_activation_patch_infers_index_shape_from_requested_layers() -> None:
    model = ComponentMapWrapper(
        {
            "layer_1.resid_pre": [[[0], [0], [0], [0]]],
        }
    )
    clean_cache = ActivationCache(
        {
            "layer_0.resid_pre": [[[1], [2]]],
            "layer_1.resid_pre": [[[10], [20], [30], [40]]],
        }
    )

    results = get_act_patch_resid_pre(
        model,
        {},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[1],
        return_details=True,
    )

    assert [result.spec.target_index for result in results] == [
        (1, 0),
        (1, 1),
        (1, 2),
        (1, 3),
    ]
    assert [result.metric for result in results] == [10.0, 20.0, 30.0, 40.0]


def test_infer_positions_accepts_direct_token_inputs() -> None:
    assert infer_positions(11, ActivationCache(), "resid_pre", [0]) == 1
    assert infer_positions([11, 12, 13], ActivationCache(), "resid_pre", [0]) == 3
    assert infer_positions([[11, 12], [13, 14]], ActivationCache(), "resid_pre", [0]) == 2
    assert infer_positions({"input_ids": 11}, ActivationCache(), "resid_pre", [0]) == 1
    assert infer_positions({"input_ids": [11, 12, 13]}, ActivationCache(), "resid_pre", [0]) == 3
    assert (
        infer_positions(
            {"tokens": [[11, 12, 13]]},
            ActivationCache(),
            "resid_pre",
            [0],
        )
        == 3
    )


def test_infer_positions_accepts_embedding_inputs() -> None:
    assert (
        infer_positions(
            {"inputs_embeds": [[[0.0, 0.1], [1.0, 1.1], [2.0, 2.1]]]},
            ActivationCache(),
            "resid_pre",
            [0],
        )
        == 3
    )
    assert (
        infer_positions(
            {"inputs_embeds": [[0.0, 0.1], [1.0, 1.1]]},
            ActivationCache(),
            "resid_pre",
            [0],
        )
        == 2
    )


def test_infer_positions_does_not_treat_raw_text_as_tokens() -> None:
    with pytest.raises(ValueError, match="positions"):
        infer_positions("hello", ActivationCache(), "resid_pre", [0])

    with pytest.raises(ValueError, match="positions"):
        infer_positions(["hello", "world"], ActivationCache(), "resid_pre", [0])


def test_generic_activation_patch_rejects_index_axis_names_with_explicit_index_table() -> None:
    model = ComponentWrapper([[[0], [0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[10], [20], [30]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any, index: Sequence[int], clean_activation: Any
    ) -> Any:
        patched = deepcopy(corrupted_activation)
        _layer, pos = index
        patched[0][pos] = clean_activation[0][pos]
        return patched

    with pytest.raises(ValueError, match="index_axis_names.*index_df"):
        generic_activation_patch(
            model,
            {"activation": [[[0], [0], [0]]]},
            clean_cache,
            patching_metric=lambda output: _nested_sum(output["activation"]),
            patch_setter=tl_layer_pos_setter,
            activation_name="resid_pre",
            index_axis_names=("layer", "pos"),
            index_df=[{"pos": 2, "layer": 0}, {"pos": 0, "layer": 0}],
            return_details=False,
            return_index_df=True,
        )


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
            if isinstance(second, list):
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


def test_transformerlens_patch_setter_adapter_passes_list_indices() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})
    seen_indices: list[Any] = []

    def tl_layer_pos_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
        seen_indices.append(index)
        assert isinstance(index, list)
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
    assert seen_indices == [[0, 0], [0, 1]]


def test_component_activation_names_support_transformerlens_style() -> None:
    assert activation_name_for_component("resid_pre", 0) == "layer_0.resid_pre"
    assert (
        activation_name_for_component("q", 1, name_style="transformer_lens")
        == "blocks.1.attn.hook_q"
    )
    assert (
        activation_name_for_component("post", 2, name_style="transformer_lens")
        == "blocks.2.mlp.hook_post"
    )
    assert (
        activation_name_for_component("pre_linear", 3, name_style="transformer_lens")
        == "blocks.3.mlp.hook_pre_linear"
    )
    assert (
        activation_name_for_component("decoder_q", 0, name_style="transformer_lens")
        == "decoder.0.attn.hook_q"
    )
    assert (
        activation_name_for_component("decoder_attn_in", 0, name_style="transformer_lens")
        == "decoder.0.hook_attn_in"
    )
    assert (
        activation_name_for_component("cross_q", 0, name_style="transformer_lens")
        == "decoder.0.cross_attn.hook_q"
    )
    assert (
        activation_name_for_component("cross_pattern", 0, name_style="transformer_lens")
        == "decoder.0.cross_attn.hook_pattern"
    )


def test_component_activation_names_accept_explicit_layer_refs() -> None:
    assert activation_name_for_component("resid_pre", ("resid_pre", 0)) == "layer_0.resid_pre"
    assert (
        activation_name_for_component("resid_pre", "blocks.0.hook_resid_pre")
        == "blocks.0.hook_resid_pre"
    )
    assert activation_name_for_component("post", ("post", 2, "mlp")) == "layer_2.post"

    with pytest.raises(ValueError, match="targets component"):
        activation_name_for_component("resid_pre", ("z", 0))


def test_generic_activation_patch_accepts_transformerlens_mlp_internal_names() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 1
    clean_cache = ActivationCache({"blocks.0.mlp.hook_post": [[[3], [4]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
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
        activation_name="post",
        index_axis_names=("layer", "pos"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[3.0, 4.0]]
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_generic_activation_patch_targets_cross_attention_transformerlens_name() -> None:
    model = ComponentMapWrapper({"decoder.0.cross_attn.hook_q": [[[[0], [0]], [[0], [0]]]]})
    clean_cache = ActivationCache({"decoder.0.cross_attn.hook_q": [[[[1], [2]], [[3], [4]]]]})

    grid, index_table = generic_activation_patch(
        model,
        {},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=layer_pos_head_vector_patch_setter,
        activation_name="cross_q",
        index_axis_names=("layer", "pos", "head"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[[1.0, 2.0], [3.0, 4.0]]]
    assert _index_records(index_table) == [
        {"layer": 0, "pos": 0, "head": 0},
        {"layer": 0, "pos": 0, "head": 1},
        {"layer": 0, "pos": 1, "head": 0},
        {"layer": 0, "pos": 1, "head": 1},
    ]


def test_generic_activation_patch_prefers_clean_cache_layers_over_model_config() -> None:
    model = ComponentWrapper([[[0], [0]]])
    model.n_layers = 2
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    def tl_layer_pos_setter(
        corrupted_activation: Any,
        index: Sequence[int],
        clean_activation: Any,
    ) -> Any:
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
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


def test_component_patch_helpers_accept_explicit_layer_refs() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[1], [2]]]})

    results = get_act_patch_resid_pre(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[("resid_pre", 0)],
        return_details=True,
    )

    assert [result.spec.target_index for result in results] == [(0, 0), (0, 1)]
    assert [result.spec.layer for result in results] == ["layer_0.resid_pre", "layer_0.resid_pre"]
    assert [result.metric for result in results] == [1.0, 2.0]


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


def test_patch_helpers_accept_transformerlens_patching_metric_keyword() -> None:
    model = ComponentWrapper([[[0], [0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1], [2]]]})

    grid = get_act_patch_resid_pre(
        model,
        {"activation": [[[0], [0]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[0, 1],
    )

    assert grid == [[1.0, 2.0]]


def test_patch_helpers_reject_duplicate_metric_names() -> None:
    model = ComponentWrapper([[[0]]])
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1]]]})

    with pytest.raises(TypeError, match="metric.*patching_metric"):
        get_act_patch_resid_pre(
            model,
            {"activation": [[[0]]]},
            clean_cache,
            metric=lambda output: _nested_sum(output["activation"]),
            patching_metric=lambda output: _nested_sum(output["activation"]),
            layers=[0],
        )


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
    assert _index_records(index_table) == [{"layer": 0, "pos": 0}, {"layer": 0, "pos": 1}]


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


def test_attention_k_patch_infers_kv_heads_from_cache_before_query_head_config() -> None:
    model = ComponentWrapper([[[[0]], [[0]]]])
    model.cfg = type("_Cfg", (), {"n_heads": 4})()
    clean_cache = ActivationCache({"layer_0.k": [[[[10]], [[20]]]]})

    grid, index_table = get_act_patch_attn_head_k_by_pos(
        model,
        {"activation": [[[[0]], [[0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        return_index_table=True,
    )

    assert grid == [[[10.0], [20.0]]]
    assert index_table == [
        {"layer": 0, "pos": 0, "head": 0},
        {"layer": 0, "pos": 1, "head": 0},
    ]


def test_attention_k_head_inference_does_not_match_component_substrings() -> None:
    model = ComponentWrapper([[[[0]], [[0]]]])
    model.cfg = type("_Cfg", (), {"n_heads": 2, "n_key_value_heads": 1})()
    clean_cache = ActivationCache({"blocks.0.hook_resid_pre": [[[0, 0, 0, 0]]]})

    assert infer_heads(model, clean_cache, "k", [0]) == 1


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


def test_attention_head_vector_patch_infers_no_batch_explicit_patch_values() -> None:
    spec = PatchSpec(
        layer="layer_0.z",
        activation_name="layer_0.z",
        target_index=(0, 1),
        value=[[[10], [20]], [[30], [40]]],
        setter=layer_head_vector_patch_setter,
    )

    patched = apply_patch([[[[0], [0]], [[0], [0]]]], spec, ActivationCache({}))

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
    clean_cache = ActivationCache({"layer_0.resid_pre": torch.tensor([[[1.0, 2.0], [3.0, 4.0]]])})
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch(corrupted, spec, clean_cache)

    assert patched == [[[0.0, 0.0], [3.0, 4.0]]]


def test_patch_setter_infers_no_batch_explicit_patch_values_for_batched_targets() -> None:
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        value=[[1.0, 2.0], [3.0, 4.0]],
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch([[[0.0, 0.0], [0.0, 0.0]]], spec, ActivationCache({}))

    assert patched == [[[0.0, 0.0], [3.0, 4.0]]]


def test_patch_setter_respects_no_batch_cache_metadata_for_same_rank_explicit_values() -> None:
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        value=[[1.0, 2.0], [3.0, 4.0]],
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch(
        [[0.0, 0.0], [0.0, 0.0]],
        spec,
        ActivationCache({}, has_batch_dim=False),
    )

    assert patched == [[0.0, 0.0], [3.0, 4.0]]


def test_patch_setter_squeezes_singleton_batch_clean_values_for_no_batch_targets() -> None:
    clean_cache = ActivationCache({"layer_0.resid_pre": [[[1.0, 2.0], [3.0, 4.0]]]})
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch([[0.0, 0.0], [0.0, 0.0]], spec, clean_cache)

    assert patched == [[0.0, 0.0], [3.0, 4.0]]


def test_patch_setter_accepts_tuple_clean_cache_values_without_tuple_leakage() -> None:
    clean_cache = ActivationCache({"layer_0.resid_pre": (((1.0, 2.0), (3.0, 4.0)),)})
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch([[[0.0, 0.0], [0.0, 0.0]]], spec, clean_cache)

    assert patched == [[[0.0, 0.0], [3.0, 4.0]]]
    assert isinstance(patched[0][1], list)


def test_tuple_backed_add_patch_setter_adds_elementwise() -> None:
    clean_cache = ActivationCache({"layer_0.resid_pre": (((1.0, 2.0), (3.0, 4.0)),)})
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        mode="add",
        scale=0.5,
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch([[[1.0, 1.0], [1.0, 1.0]]], spec, clean_cache)

    assert patched == [[[1.0, 1.0], [2.5, 3.0]]]


def test_patch_setter_converts_tuple_corrupted_activation_to_mutable_output() -> None:
    clean_cache = ActivationCache({"layer_0.resid_pre": (((1.0, 2.0), (3.0, 4.0)),)})
    spec = PatchSpec(
        layer="layer_0.resid_pre",
        activation_name="layer_0.resid_pre",
        target_index=(0, 1),
        setter=layer_pos_patch_setter,
    )

    patched = apply_patch((((0.0, 0.0), (0.0, 0.0)),), spec, clean_cache)

    assert patched == [[[0.0, 0.0], [3.0, 4.0]]]


def test_exported_patch_setter_direct_call_accepts_tuple_backed_inputs() -> None:
    patched = layer_pos_patch_setter(
        (((0.0, 0.0), (0.0, 0.0)),),
        (0, 1),
        (((1.0, 2.0), (3.0, 4.0)),),
    )

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


def test_exported_patch_setters_accept_transformerlens_no_batch_clean_activation() -> None:
    residual_clean = [[10], [20]]
    head_clean = [[[1], [2]], [[3], [4]]]
    pattern_clean = [[[1, 2, 3], [4, 5, 6]]]

    assert layer_pos_patch_setter([[[0], [0]]], (0, 1), residual_clean) == [[[0], [20]]]
    assert layer_head_vector_patch_setter(
        [[[[0], [0]], [[0], [0]]]],
        (0, 1),
        head_clean,
    ) == [[[[0], [2]], [[0], [4]]]]
    assert layer_head_dest_src_pos_pattern_patch_setter(
        [[[[0, 0, 0], [0, 0, 0]]]],
        (0, 0, 1, 2),
        pattern_clean,
    ) == [[[[0, 0, 0], [0, 0, 6]]]]


def test_exported_patch_setters_accept_transformerlens_no_batch_direct_call() -> None:
    assert layer_pos_patch_setter([[0], [0]], (0, 1), [[10], [20]]) == [[0], [20]]
    assert layer_pos_head_vector_patch_setter(
        [[[0], [0]], [[0], [0]]],
        (0, 1, 0),
        [[[1], [2]], [[3], [4]]],
    ) == [[[0], [0]], [[3], [0]]]
    assert layer_head_vector_patch_setter(
        [[[0], [0]], [[0], [0]]],
        (0, 1),
        [[[1], [2]], [[3], [4]]],
    ) == [[[0], [2]], [[0], [4]]]
    assert layer_head_pattern_patch_setter(
        [[[0, 0], [0, 0]], [[0, 0], [0, 0]]],
        (0, 1),
        [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
    ) == [[[0, 0], [0, 0]], [[5, 6], [7, 8]]]
    assert layer_head_pos_pattern_patch_setter(
        [[[0, 0], [0, 0]], [[0, 0], [0, 0]]],
        (0, 1, 0),
        [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
    ) == [[[0, 0], [0, 0]], [[5, 6], [0, 0]]]
    assert layer_head_dest_src_pos_pattern_patch_setter(
        [[[0, 0], [0, 0]], [[0, 0], [0, 0]]],
        (0, 1, 0, 1),
        [[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
    ) == [[[0, 0], [0, 0]], [[0, 6], [0, 0]]]


def test_exported_patch_setters_squeeze_singleton_batch_clean_for_no_batch_targets() -> None:
    assert layer_pos_patch_setter([[0], [0]], (0, 1), [[[10], [20]]]) == [[0], [20]]


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
    index_records = _index_records(index_table)
    assert index_records[0] == {"layer": 0, "head_index": 0, "dest_pos": 0, "src_pos": 0}
    assert index_records[-1] == {"layer": 0, "head_index": 0, "dest_pos": 1, "src_pos": 2}


def test_cross_attention_pattern_patch_infers_head_dest_and_source_axes() -> None:
    model = ComponentMapWrapper({"decoder.0.cross_attn.hook_pattern": [[[[0, 0, 0], [0, 0, 0]]]]})
    clean_cache = ActivationCache({"decoder.0.cross_attn.hook_pattern": [[[[1, 2, 3], [4, 5, 6]]]]})

    grid, index_table = generic_activation_patch(
        model,
        {},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        patch_setter=layer_head_dest_src_pos_pattern_patch_setter,
        activation_name="cross_pattern",
        index_axis_names=("layer", "head_index", "dest_pos", "src_pos"),
        return_details=False,
        return_index_df=True,
    )

    assert grid == [[[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]]]
    assert _index_records(index_table) == [
        {"layer": 0, "head_index": 0, "dest_pos": 0, "src_pos": 0},
        {"layer": 0, "head_index": 0, "dest_pos": 0, "src_pos": 1},
        {"layer": 0, "head_index": 0, "dest_pos": 0, "src_pos": 2},
        {"layer": 0, "head_index": 0, "dest_pos": 1, "src_pos": 0},
        {"layer": 0, "head_index": 0, "dest_pos": 1, "src_pos": 1},
        {"layer": 0, "head_index": 0, "dest_pos": 1, "src_pos": 2},
    ]


def test_attention_scores_patch_helpers_share_pattern_index_semantics_for_list_backend() -> None:
    from SafeLens.core.patching import (
        get_act_patch_attn_scores_all_pos,
        get_act_patch_attn_scores_by_pos,
        get_act_patch_attn_scores_dest_src_pos,
    )

    model = ComponentWrapper([[[[0, 0, 0], [0, 0, 0]]]])
    clean_cache = ActivationCache({"layer_0.attn_scores": [[[[1, 2, 3], [4, 5, 6]]]]})
    kwargs = {
        "layers": [0],
        "heads": [0],
        "dest_positions": [1],
        "source_positions": [2],
        "return_details": True,
    }

    all_pos = get_act_patch_attn_scores_all_pos(
        model,
        {"activation": [[[[0, 0, 0], [0, 0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        **kwargs,
    )
    by_pos = get_act_patch_attn_scores_by_pos(
        model,
        {"activation": [[[[0, 0, 0], [0, 0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        **kwargs,
    )
    dest_src = get_act_patch_attn_scores_dest_src_pos(
        model,
        {"activation": [[[[0, 0, 0], [0, 0, 0]]]]},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        **kwargs,
    )

    assert all_pos[0].output["activation"] == [[[[1, 2, 3], [4, 5, 6]]]]
    assert by_pos[0].output["activation"] == [[[[0, 0, 0], [4, 5, 6]]]]
    assert dest_src[0].output["activation"] == [[[[0, 0, 0], [0, 0, 6]]]]


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


def test_attention_head_every_accepts_transformerlens_patching_metric_keyword() -> None:
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

    all_pos_stack = get_act_patch_attn_head_all_pos_every(
        model,
        {"activation": [[[[0]]]]},
        clean_cache,
        patching_metric=lambda output: _nested_sum(output["activation"]),
        layers=[0],
        positions=[0],
        heads=[0],
        dest_positions=[0],
        source_positions=[0],
    )

    assert all_pos_stack == [[[1.0]], [[2.0]], [[3.0]], [[4.0]], [[5.0]]]


def test_attention_head_every_pads_grouped_key_value_heads_for_list_backend() -> None:
    model = ComponentMapWrapper(
        {
            "layer_0.z": [[[[0], [0], [0], [0]]]],
            "layer_0.q": [[[[0], [0], [0], [0]]]],
            "layer_0.k": [[[[0], [0]]]],
            "layer_0.v": [[[[0], [0]]]],
            "layer_0.pattern": [[[[0]], [[0]], [[0]], [[0]]]],
        }
    )
    clean_cache = ActivationCache(
        {
            "layer_0.z": [[[[1], [2], [3], [4]]]],
            "layer_0.q": [[[[10], [20], [30], [40]]]],
            "layer_0.k": [[[[100], [200]]]],
            "layer_0.v": [[[[1000], [2000]]]],
            "layer_0.pattern": [[[[5]], [[6]], [[7]], [[8]]]],
        }
    )
    kwargs = {
        "layers": [0],
        "positions": [0],
        "dest_positions": [0],
        "source_positions": [0],
    }

    all_pos_stack = get_act_patch_attn_head_all_pos_every(
        model,
        {},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        **kwargs,
    )
    by_pos_stack = get_act_patch_attn_head_by_pos_every(
        model,
        {},
        clean_cache,
        metric=lambda output: _nested_sum(output["activation"]),
        **kwargs,
    )

    assert all_pos_stack == [
        [[1.0, 2.0, 3.0, 4.0]],
        [[10.0, 20.0, 30.0, 40.0]],
        [[100.0, 200.0, 0.0, 0.0]],
        [[1000.0, 2000.0, 0.0, 0.0]],
        [[5.0, 6.0, 7.0, 8.0]],
    ]
    assert by_pos_stack == [
        [[[1.0, 2.0, 3.0, 4.0]]],
        [[[10.0, 20.0, 30.0, 40.0]]],
        [[[100.0, 200.0, 0.0, 0.0]]],
        [[[1000.0, 2000.0, 0.0, 0.0]]],
        [[[5.0, 6.0, 7.0, 8.0]]],
    ]
