from __future__ import annotations

import math
from typing import Any

import pytest

import SafeLens.core.analysis as analysis
from SafeLens.core.activation_functions import (
    SUPPORTED_ACTIVATIONS,
    XIELU,
    gelu_fast,
    gelu_new,
    gelu_pytorch_tanh,
    silu,
    solu,
    xielu,
)
from SafeLens.core.analysis import (
    HEAD_NAMES,
    attention_pattern_score,
    compute_head_attention_similarity_score,
    compute_head_results_from_z,
    cross_entropy_loss,
    detect_head,
    direct_logit_attribution,
    get_duplicate_token_head_detection_pattern,
    get_induction_head_detection_pattern,
    get_previous_token_head_detection_pattern,
    get_supported_heads,
    induction_attention_score,
    lm_accuracy,
    lm_cross_entropy_loss,
    lm_log_probs,
    logit_diff,
    logits_to_df,
    logits_to_log_probs,
    mean_ablation_hook,
    previous_token_attention_score,
    replace_activation_hook,
    residual_stack_to_logits,
    sample_logits,
    softmax,
    topk_tokens,
    zero_ablation_hook,
)
from SafeLens.core.analysis import (
    test_prompt as run_test_prompt,
)
from SafeLens.core.factored_matrix import FactoredMatrix, composition_scores, matmul, transpose
from SafeLens.core.hooked_root import HookedRoot
from SafeLens.core.hooks import ActivationCache, HookPoint
from SafeLens.core.kv_cache import (
    KeyValueCache,
    KeyValueCacheEntry,
    TransformerLensKeyValueCache,
    TransformerLensKeyValueCacheEntry,
)
from SafeLens.core.tensors import (
    Slice,
    filter_dict_by_prefix,
    get_corner,
    get_cumsum_along_dim,
    get_offset_position_ids,
    is_lower_triangular,
    is_square,
    remove_batch_dim,
    repeat_along_head_dimension,
    to_numpy,
)
from SafeLens.core.tensors import (
    transpose as tensor_transpose,
)
from SafeLens.core.utilities import (
    USE_DEFAULT_VALUE,
    LocallyOverridenDefaults,
    batch_addmm,
    calc_fan_in_and_fan_out,
    call_hf_with_retry,
    complex_attn_linear,
    count_unique_devices,
    find_embedding_device,
    get_attention_mask,
    get_best_available_device,
    get_device,
    get_device_for_block_index,
    get_input_with_manually_prepended_bos,
    get_matrix_corner,
    get_nested_attr,
    get_rotary_pct_from_config,
    get_tokens_with_bos_removed,
    init_xavier_uniform_,
    is_library_available,
    override_or_use_default_value,
    resolve_device_map,
    select_compatible_kwargs,
    set_nested_attr,
    simple_attn_linear,
    tokenize_and_concatenate,
    vanilla_addmm,
)


def assert_nested_close(left: Any, right: Any, *, abs_tol: float = 1e-9) -> None:
    if isinstance(left, list) and isinstance(right, list):
        assert len(left) == len(right)
        for left_item, right_item in zip(left, right, strict=True):
            assert_nested_close(left_item, right_item, abs_tol=abs_tol)
        return
    assert math.isclose(float(left), float(right), abs_tol=abs_tol)


def test_top_level_exports_common_transformerlens_helpers() -> None:
    import SafeLens
    import SafeLens.core as core
    import SafeLens.utils as utils

    patching_exports = [
        "generic_activation_patch",
        "get_act_patch_resid_pre",
        "get_act_patch_resid_mid",
        "get_act_patch_resid_post",
        "get_act_patch_attn_out",
        "get_act_patch_mlp_out",
        "get_act_patch_attn_head_out_by_pos",
        "get_act_patch_attn_head_q_by_pos",
        "get_act_patch_attn_head_k_by_pos",
        "get_act_patch_attn_head_v_by_pos",
        "get_act_patch_attn_head_pattern_by_pos",
        "get_act_patch_attn_head_pattern_dest_src_pos",
        "get_act_patch_attn_head_out_all_pos",
        "get_act_patch_attn_head_q_all_pos",
        "get_act_patch_attn_head_k_all_pos",
        "get_act_patch_attn_head_v_all_pos",
        "get_act_patch_attn_head_pattern_all_pos",
        "get_act_patch_attn_scores_by_pos",
        "get_act_patch_attn_scores_dest_src_pos",
        "get_act_patch_attn_scores_all_pos",
        "get_act_patch_block_every",
        "get_act_patch_attn_head_all_pos_every",
        "get_act_patch_attn_head_by_pos_every",
        "make_df_from_ranges",
        "run_activation_patch",
    ]
    analysis_exports = [
        "batch_addmm",
        "call_hf_with_retry",
        "complex_attn_linear",
        "compute_head_results_from_z",
        "cross_entropy_loss",
        "direct_logit_attribution",
        "lm_accuracy",
        "lm_cross_entropy_loss",
        "lm_log_probs",
        "log_softmax",
        "logit_diff",
        "logits_to_log_probs",
        "mean_ablation_hook",
        "per_token_cross_entropy_loss",
        "replace_activation_hook",
        "residual_stack_to_logits",
        "simple_attn_linear",
        "softmax",
        "test_prompt",
        "topk_tokens",
        "vanilla_addmm",
        "zero_ablation_hook",
        "sort_devices_based_on_available_memory",
    ]

    for module in (SafeLens, core):
        assert module.ActivationCache is ActivationCache
        assert module.HookPoint is HookPoint
        assert module.HookedRoot is HookedRoot
        assert module.TransformerLensKeyValueCache is TransformerLensKeyValueCache
        assert module.TransformerLensKeyValueCacheEntry is TransformerLensKeyValueCacheEntry
        assert module.TransformerLensKeyValueCache is KeyValueCache
        assert module.TransformerLensKeyValueCacheEntry is KeyValueCacheEntry
        for export_name in [*patching_exports, *analysis_exports]:
            assert callable(getattr(module, export_name))
            assert export_name in module.__all__
        assert "TransformerLensKeyValueCache" in module.__all__
        assert "TransformerLensKeyValueCacheEntry" in module.__all__
    assert SafeLens.HookedTransformer is utils.TransformerLensCompatibleModelWrapper
    assert utils.HookedTransformer is utils.TransformerLensCompatibleModelWrapper
    assert "HookedTransformer" in SafeLens.__all__
    assert "HookedTransformer" in utils.__all__


def test_hooked_root_manages_temporary_and_permanent_hooks() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    with root.hooks(
        fwd_hooks=[("blocks.0.hook_resid_pre", lambda activation, _hook: activation + [1])]
    ) as hooked_root:
        assert hooked_root is root
        assert resid([0]) == [0, 1]

    assert resid([0]) == [0]

    root.add_perma_hook(
        "blocks.0.hook_resid_pre",
        lambda activation, _hook: activation + [2],
    )
    root.reset_hooks(including_permanent=True)

    assert resid([0]) == [0]


def test_hooked_root_setup_discovers_hookpoint_attributes() -> None:
    class Block:
        def __init__(self) -> None:
            self.hook_resid_pre = HookPoint()

    root = HookedRoot()
    root.blocks = [Block()]
    root.extra_hooks = {"mlp": HookPoint()}

    root.setup()

    assert set(root.hook_dict) == {"blocks.0.hook_resid_pre", "extra_hooks.mlp"}
    assert root.blocks[0].hook_resid_pre.name == "blocks.0.hook_resid_pre"
    with root.hooks(
        fwd_hooks=[("blocks.0.hook_resid_pre", lambda activation, _hook: activation + [1])]
    ):
        assert root.blocks[0].hook_resid_pre([0]) == [0, 1]


def test_hooked_root_nested_hooks_keep_context_levels_separate() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    with root.hooks(
        fwd_hooks=[("blocks.0.hook_resid_pre", lambda activation, _hook: activation + [1])]
    ):
        assert resid([0]) == [0, 1]
        with root.hooks(
            fwd_hooks=[("blocks.0.hook_resid_pre", lambda activation, _hook: activation + [2])],
            reset_hooks_end=False,
        ):
            assert resid([0]) == [0, 1, 2]
        assert resid([0]) == [0, 1, 2]

    assert resid([0]) == [0, 2]
    root.reset_hooks()
    assert resid([0]) == [0]


def test_hooked_root_preserved_nested_hooks_do_not_share_future_context_level() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    with root.hooks(
        fwd_hooks=[("blocks.0.hook_resid_pre", lambda activation, _hook: activation + ["outer"])]
    ):
        with root.hooks(
            fwd_hooks=[
                ("blocks.0.hook_resid_pre", lambda activation, _hook: activation + ["kept"])
            ],
            reset_hooks_end=False,
        ):
            assert resid([]) == ["outer", "kept"]
        with root.hooks(
            fwd_hooks=[("blocks.0.hook_resid_pre", lambda activation, _hook: activation + ["temp"])]
        ):
            assert resid([]) == ["outer", "kept", "temp"]
        assert resid([]) == ["outer", "kept"]

    assert resid([]) == ["kept"]
    root.reset_hooks()
    assert resid([]) == []


def test_hooked_root_preserved_hooks_keep_contexts_until_explicit_reset() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    def record_context(activation: list[str], hook: HookPoint) -> list[str]:
        hook.ctx["seen"] = True
        return activation + ["hooked"]

    with root.hooks(
        fwd_hooks=[("blocks.0.hook_resid_pre", record_context)],
        reset_hooks_end=False,
        clear_contexts=True,
    ):
        assert resid([]) == ["hooked"]
        assert resid.ctx == {"seen": True}

    assert resid.has_hooks()
    assert resid.ctx == {"seen": True}
    assert resid([]) == ["hooked"]
    assert resid.ctx == {"seen": True}
    root.reset_hooks(clear_contexts=True)
    assert resid.ctx == {}
    assert resid([]) == []


def test_hooked_root_lists_hooks_and_resets_by_direction_and_level() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_post")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    root.check_and_add_hook(
        "blocks.0.hook_resid_post",
        lambda activation, _hook: activation + [1],
        level=1,
    )
    root.check_and_add_hook(
        "blocks.0.hook_resid_post",
        lambda activation, _hook: activation + [2],
        dir="bwd",
        level=2,
    )
    root.add_perma_hook("blocks.0.hook_mlp_out", lambda activation, _hook: activation + [3])

    all_hooks = root.list_hooks()
    assert set(all_hooks) == {"blocks.0.hook_resid_post", "blocks.0.hook_mlp_out"}
    assert len(all_hooks["blocks.0.hook_resid_post"]) == 2
    assert list(root.list_hooks(name_filter=lambda name: "mlp" in name)) == [
        "blocks.0.hook_mlp_out"
    ]
    assert root.list_hooks(including_permanent=False) == {
        "blocks.0.hook_resid_post": all_hooks["blocks.0.hook_resid_post"]
    }

    root.reset_hooks(direction="fwd", level=1, clear_contexts=False)

    assert not resid.has_hooks("fwd")
    assert resid.has_hooks("bwd")
    assert mlp.has_hooks("fwd")
    root.remove_all_hook_fns(direction="bwd")
    assert not resid.has_hooks("bwd")
    assert mlp.has_hooks("fwd")

    root.reset_hooks(direction="both", including_permanent=True)
    assert not resid.has_hooks()
    assert not mlp.has_hooks()


def test_hooked_root_check_and_add_hook_accepts_official_hookpoint_signature() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    seen: list[str] = []

    root.check_hooks_to_add(
        resid,
        "blocks.0.hook_resid_pre",
        lambda activation, _hook: activation,
        dir="fwd",
    )
    root.check_and_add_hook(
        resid,
        "blocks.0.hook_resid_pre",
        lambda activation, _hook: seen.append("second") or activation + [2],
    )
    root.check_and_add_hook(
        resid,
        "blocks.0.hook_resid_pre",
        lambda activation, _hook: seen.append("first") or activation + [1],
        prepend=True,
    )

    assert resid([0]) == [0, 1, 2]
    assert seen == ["first", "second"]


def test_hooked_root_hooks_context_accepts_prepend() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    seen: list[str] = []
    root.add_hook(
        "blocks.0.hook_resid_pre",
        lambda activation, _hook: seen.append("base") or activation + ["base"],
    )

    with root.hooks(
        fwd_hooks=[
            (
                "blocks.0.hook_resid_pre",
                lambda activation, _hook: seen.append("temp") or activation + ["temp"],
            )
        ],
        prepend=True,
    ):
        assert resid([]) == ["temp", "base"]

    assert seen == ["temp", "base"]
    assert resid([]) == ["base"]
    root.reset_hooks()


def test_hooked_root_enable_hook_helpers_match_transformerlens_internals() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")
    root.context_level = 3

    handles = root._enable_hook(
        lambda name: name.endswith("resid_pre"),
        lambda activation, _hook: activation + [1],
        "fwd",
    )
    bwd_handle = root._enable_hook_with_name(
        "blocks.0.hook_mlp_out",
        lambda grad, _hook: grad + [2],
        "bwd",
    )

    assert resid([0]) == [0, 1]
    assert mlp.has_hooks("bwd", level=3)
    assert [handle.context_level for handle in handles] == [3]
    assert bwd_handle.context_level == 3

    root.reset_hooks(level=3)
    assert resid([0]) == [0]
    assert not mlp.has_hooks("bwd")


def test_hooked_root_caching_hooks_capture_hookpoint_activations() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    mlp = root.add_hook_point("blocks.0.mlp.hook_post")

    cache = root.add_caching_hooks(lambda name: "resid" in name, clone=True)
    resid([1, 2, 3])
    mlp([4, 5, 6])

    assert cache.to_dict() == {"blocks.0.hook_resid_pre": [1, 2, 3]}


def test_hooked_root_get_caching_hooks_returns_live_cache() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    assert root.is_caching is False
    cache, fwd_hooks, bwd_hooks = root.get_caching_hooks("blocks.0.hook_resid_pre")

    assert root.is_caching is True
    assert bwd_hooks == []
    with root.hooks(fwd_hooks=fwd_hooks):
        resid([9])

    assert cache.to_dict() == {"blocks.0.hook_resid_pre": [9]}
    root.reset_hooks()
    assert root.is_caching is False


def test_hooked_root_is_caching_tracks_cache_lifecycle_like_transformerlens() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    persistent_cache = root.add_caching_hooks("blocks.0.hook_resid_pre")
    assert root.is_caching is True
    resid([1])
    assert persistent_cache.to_dict() == {"blocks.0.hook_resid_pre": [1]}

    root.reset_hooks()
    assert root.is_caching is False

    _output, temporary_cache = root.run_with_cache(lambda: resid([2]))
    assert temporary_cache.to_dict() == {"blocks.0.hook_resid_pre": [2]}
    assert root.is_caching is False

    _output, kept_cache = root.run_with_cache(lambda: resid([3]), reset_hooks_end=False)
    assert kept_cache.to_dict() == {"blocks.0.hook_resid_pre": [3]}
    assert root.is_caching is True

    root.reset_hooks()
    assert root.is_caching is False


def test_hooked_root_run_with_cache_preserves_outer_cache_state() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    persistent_cache = root.add_caching_hooks("blocks.0.hook_resid_pre")
    assert root.is_caching is True

    _output, temporary_cache = root.run_with_cache(lambda: resid([4]))

    assert temporary_cache.to_dict() == {"blocks.0.hook_resid_pre": [4]}
    assert persistent_cache.to_dict() == {"blocks.0.hook_resid_pre": [4]}
    assert root.is_caching is True

    root.reset_hooks()
    assert root.is_caching is False


def test_hooked_root_temporary_hooks_preserve_outer_cache_state() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    persistent_cache = root.cache_all()

    with root.hooks(
        fwd_hooks=[
            (
                "blocks.0.hook_resid_pre",
                lambda activation, _hook: activation + ["temporary"],
            )
        ]
    ):
        assert root.is_caching is True
        assert resid(["inside"]) == ["inside", "temporary"]

    assert root.is_caching is True
    assert persistent_cache.to_dict() == {"blocks.0.hook_resid_pre": ["inside"]}
    resid(["after"])
    assert persistent_cache.to_dict() == {"blocks.0.hook_resid_pre": ["after"]}

    output = root.run_with_hooks(
        lambda: resid(["patched"]),
        fwd_hooks=[
            (
                "blocks.0.hook_resid_pre",
                lambda activation, _hook: activation + ["patched"],
            )
        ],
    )

    assert output == ["patched", "patched"]
    assert root.is_caching is True
    assert persistent_cache.to_dict() == {
        "blocks.0.hook_resid_pre": ["patched"],
    }

    root.reset_hooks()
    assert root.is_caching is False
    assert not resid.has_hooks()


def test_hooked_root_run_with_cache_reset_false_keeps_contexts_until_reset() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    resid.ctx["seen"] = True
    output, cache = root.run_with_cache(
        lambda: resid(["input"]),
        reset_hooks_end=False,
        clear_contexts=True,
    )

    assert output == ["input"]
    assert cache.to_dict() == {"blocks.0.hook_resid_pre": ["input"]}
    assert resid.ctx == {"seen": True}
    assert resid.has_hooks()

    root.reset_hooks(clear_contexts=True)

    assert resid.ctx == {}
    assert resid([]) == []


def test_hooked_root_is_caching_rolls_back_after_cache_hook_install_failure() -> None:
    root = HookedRoot()
    root.add_hook_point("blocks.0.hook_resid_pre")

    original_check_and_add = root.check_and_add_hook
    calls = 0

    def fail_after_first_add(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise RuntimeError("boom")
        return original_check_and_add(*args, **kwargs)

    root.check_and_add_hook = fail_after_first_add  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="boom"):
        root.add_caching_hooks("blocks.0.hook_resid_pre", incl_bwd=True)

    assert root.is_caching is False


def test_hooked_root_run_with_cache_is_caching_rolls_back_after_install_failure() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    original_check_and_add = root.check_and_add_hook
    calls = 0

    def fail_after_first_add(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise RuntimeError("boom")
        return original_check_and_add(*args, **kwargs)

    root.check_and_add_hook = fail_after_first_add  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="boom"):
        root.run_with_cache(
            lambda: None,
            names_filter="blocks.0.hook_resid_pre",
            incl_bwd=True,
            reset_hooks_end=False,
        )

    assert root.is_caching is False
    assert not resid.has_hooks()


def test_hooked_root_caching_helpers_mark_empty_remove_batch_dim_cache() -> None:
    root = HookedRoot()
    root.add_hook_point("blocks.0.hook_resid_pre")

    cache, _fwd_hooks, _bwd_hooks = root.get_caching_hooks(
        "blocks.0.hook_resid_pre",
        remove_batch_dim=True,
    )
    persistent_cache = root.add_caching_hooks(
        "blocks.0.hook_resid_pre",
        remove_batch_dim=True,
    )

    assert cache.has_batch_dim is False
    assert persistent_cache.has_batch_dim is False
    assert cache.to_dict() == {}
    assert persistent_cache.to_dict() == {}


def test_hooked_root_add_caching_hooks_rolls_back_external_cache_metadata() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    original_model = object()
    external_cache = ActivationCache({"existing": [1]}, model=original_model)

    original_check_and_add = root.check_and_add_hook
    calls = 0

    def fail_after_first_add(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise RuntimeError("boom")
        return original_check_and_add(*args, **kwargs)

    root.check_and_add_hook = fail_after_first_add  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="boom"):
        root.add_caching_hooks(
            "blocks.0.hook_resid_pre",
            incl_bwd=True,
            remove_batch_dim=True,
            cache=external_cache,
        )

    assert not resid.has_hooks()
    assert external_cache.model is original_model
    assert external_cache.has_batch_dim is True
    assert external_cache.to_dict() == {"existing": [1]}


def test_hooked_root_run_with_cache_rolls_back_external_cache_metadata_on_install_failure() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    original_model = object()
    external_cache = ActivationCache({"existing": [1]}, model=original_model)

    original_check_and_add = root.check_and_add_hook
    calls = 0

    def fail_after_first_add(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise RuntimeError("boom")
        return original_check_and_add(*args, **kwargs)

    root.check_and_add_hook = fail_after_first_add  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="boom"):
        root.run_with_cache(
            lambda: resid([1]),
            names_filter="blocks.0.hook_resid_pre",
            incl_bwd=True,
            remove_batch_dim=True,
            cache=external_cache,
        )

    assert not resid.has_hooks()
    assert external_cache.model is original_model
    assert external_cache.has_batch_dim is True
    assert external_cache.to_dict() == {"existing": [1]}


def test_hooked_root_get_caching_hooks_does_not_mutate_external_cache_on_filter_error() -> None:
    root = HookedRoot()
    root.add_hook_point("blocks.0.hook_resid_pre")
    original_model = object()
    external_cache = ActivationCache({"existing": [1]}, model=original_model)

    with pytest.raises(TypeError):
        root.get_caching_hooks(123, remove_batch_dim=True, cache=external_cache)  # type: ignore[arg-type]

    assert root.is_caching is False
    assert external_cache.model is original_model
    assert external_cache.has_batch_dim is True
    assert external_cache.to_dict() == {"existing": [1]}


def test_hooked_root_names_filters_match_equivalent_safelens_names() -> None:
    root = HookedRoot()
    q_hook = root.add_hook_point("blocks.0.attn.hook_q")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    cache, fwd_hooks, _ = root.get_caching_hooks("layer_0.q")
    with root.hooks(fwd_hooks=fwd_hooks):
        q_hook([1])
        mlp([2])

    assert cache.to_dict() == {"blocks.0.attn.hook_q": [1]}


def test_hooked_root_names_filters_match_transformerlens_component_shorthands() -> None:
    root = HookedRoot()
    q_hook = root.add_hook_point("blocks.0.attn.hook_q")
    k_hook = root.add_hook_point("blocks.0.attn.hook_k")

    cache, fwd_hooks, _ = root.get_caching_hooks("q")
    with root.hooks(fwd_hooks=fwd_hooks):
        q_hook([1])
        k_hook([2])

    assert cache.to_dict() == {"blocks.0.attn.hook_q": [1]}


def test_hooked_root_caching_hooks_can_remove_batch_dim_on_write() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    cache, fwd_hooks, _ = root.get_caching_hooks(
        "blocks.0.hook_resid_pre",
        remove_batch_dim=True,
    )
    with root.hooks(fwd_hooks=fwd_hooks):
        resid([[[1, 10], [2, 20]]])

    assert cache.has_batch_dim is False
    assert cache.to_dict() == {"blocks.0.hook_resid_pre": [[1, 10], [2, 20]]}


def test_hooked_root_cache_pos_slice_uses_transformerlens_component_dimensions() -> None:
    root = HookedRoot()
    q_hook = root.add_hook_point("blocks.0.attn.hook_q")
    pattern_hook = root.add_hook_point("blocks.0.attn.hook_pattern")
    resid_hook = root.add_hook_point("blocks.0.hook_resid_pre")

    cache, fwd_hooks, _ = root.get_caching_hooks(
        lambda name: name.startswith("blocks.0"),
        pos_slice=1,
        remove_batch_dim=True,
    )

    with root.hooks(fwd_hooks=fwd_hooks):
        q_hook([[[[1, 10], [2, 20]], [[3, 30], [4, 40]]]])
        pattern_hook([[[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]]])
        resid_hook([[[1, 10], [2, 20]]])

    assert cache["blocks.0.attn.hook_q"] == [[[3, 30], [4, 40]]]
    assert cache["blocks.0.attn.hook_pattern"] == [[[4, 5, 6]], [[10, 11, 12]]]
    assert cache["blocks.0.hook_resid_pre"] == [[2, 20]]


def test_hooked_root_run_with_cache_matches_transformerlens_style_entrypoint() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    def run() -> list[int]:
        hidden = resid([1, 2])
        return mlp(hidden + [3])

    output, cache = root.run_with_cache(
        run,
        names_filter=lambda name: "resid" in name,
        clone=True,
    )

    assert output == [1, 2, 3]
    assert cache.to_dict() == {"blocks.0.hook_resid_pre": [1, 2]}
    assert resid([0]) == [0]


def test_hooked_root_run_helpers_can_call_forward_like_transformerlens() -> None:
    class ToyRoot(HookedRoot):
        def __init__(self) -> None:
            super().__init__()
            self.hook_resid = HookPoint()
            self.setup()

        def forward(self, value: list[int], scale: int = 1) -> list[int]:
            return self.hook_resid([item * scale for item in value])

    root = ToyRoot()

    output = root.run_with_hooks(
        [1],
        scale=3,
        fwd_hooks=[("hook_resid", lambda activation, _hook: activation + [9])],
    )
    cached_output, cache = root.run_with_cache([2], scale=4)

    assert output == [3, 9]
    assert cached_output == [8]
    assert cache["hook_resid"] == [8]


def test_hooked_root_caching_helpers_accept_transformerlens_style_external_dict() -> None:
    class ToyRoot(HookedRoot):
        def __init__(self) -> None:
            super().__init__()
            self.hook_resid = HookPoint()
            self.setup()

        def forward(self, value: list[int]) -> list[int]:
            return self.hook_resid(value)

    root = ToyRoot()
    external_cache: dict[str, Any] = {}

    output, cache = root.run_with_cache([1, 2], cache=external_cache)

    assert output == [1, 2]
    assert cache.cache_dict is external_cache
    assert external_cache == {"hook_resid": [1, 2]}

    persistent_cache: dict[str, Any] = {}
    live_cache = root.cache_some(lambda name: name == "hook_resid", cache=persistent_cache)
    root.forward([3])

    assert live_cache.cache_dict is persistent_cache
    assert persistent_cache == {"hook_resid": [3]}
    root.reset_hooks(including_permanent=True)


def test_hooked_root_cache_deprecated_transformerlens_positional_cache_signatures() -> None:
    class ToyRoot(HookedRoot):
        def __init__(self) -> None:
            super().__init__()
            self.hook_resid = HookPoint()
            self.hook_mlp = HookPoint()
            self.setup()

        def forward(self, value: list[int]) -> list[int]:
            return self.hook_mlp(self.hook_resid(value))

    root = ToyRoot()
    all_cache: dict[str, Any] = {}

    all_live_cache = root.cache_all(all_cache)
    root.forward([1])

    assert all_live_cache.cache_dict is all_cache
    assert all_cache == {"hook_resid": [1], "hook_mlp": [1]}
    root.reset_hooks(including_permanent=True)

    some_cache: dict[str, Any] = {}
    some_live_cache = root.cache_some(some_cache, lambda name: name == "hook_mlp")
    root.forward([2])

    assert some_live_cache.cache_dict is some_cache
    assert some_cache == {"hook_mlp": [2]}
    root.reset_hooks(including_permanent=True)


def test_hooked_root_run_with_hooks_accepts_prepend() -> None:
    class ToyRoot(HookedRoot):
        def __init__(self) -> None:
            super().__init__()
            self.hook_resid = HookPoint()
            self.setup()

        def forward(self, value: list[str]) -> list[str]:
            return self.hook_resid(value)

    root = ToyRoot()
    root.add_hook("hook_resid", lambda activation, _hook: activation + ["base"])

    output = root.run_with_hooks(
        [],
        fwd_hooks=[("hook_resid", lambda activation, _hook: activation + ["temp"])],
        prepend=True,
    )

    assert output == ["temp", "base"]
    assert root.hook_resid([]) == ["base"]
    root.reset_hooks()


def test_hooked_root_hooks_accept_name_filters() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    with root.hooks(fwd_hooks=[(lambda name: "resid" in name, lambda act, _hook: act + [9])]):
        assert resid([1]) == [1, 9]
        assert mlp([1]) == [1]


def test_hooked_root_callable_filters_with_no_matches_are_noops_like_transformerlens() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    with root.hooks(fwd_hooks=[(lambda _name: False, lambda act, _hook: act + [9])]):
        assert resid([1]) == [1]

    output = root.run_with_hooks(
        lambda: resid([2]),
        fwd_hooks=[(lambda _name: False, lambda act, _hook: act + [9])],
    )

    assert output == [2]
    assert not resid.has_hooks()


def test_hooked_root_hooks_accept_equivalent_safelens_string_filters() -> None:
    root = HookedRoot()
    q_hook = root.add_hook_point("blocks.0.attn.hook_q")

    with root.hooks(fwd_hooks=[("layer_0.q", lambda act, _hook: act + [9])]):
        assert q_hook([1]) == [1, 9]


def test_hooked_root_string_hook_specs_prefer_exact_names_over_aliases() -> None:
    root = HookedRoot()
    tl_q = root.add_hook_point("blocks.0.attn.hook_q")
    safe_q = root.add_hook_point("layer_0.q")

    with root.hooks(fwd_hooks=[("layer_0.q", lambda act, _hook: act + [9])]):
        assert tl_q([1]) == [1]
        assert safe_q([1]) == [1, 9]


def test_hooked_root_direct_string_filters_prefer_exact_names_over_aliases() -> None:
    root = HookedRoot()
    tl_q = root.add_hook_point("blocks.0.attn.hook_q")
    safe_q = root.add_hook_point("layer_0.q")

    handles = root.add_hook("layer_0.q", lambda act, _hook: act + [9])
    cache, fwd_hooks, _ = root.get_caching_hooks("layer_0.q")

    with root.hooks(fwd_hooks=fwd_hooks):
        assert tl_q([1]) == [1]
        assert safe_q([1]) == [1, 9]

    assert cache.to_dict() == {"layer_0.q": [1, 9]}
    for handle in handles:
        handle.remove()


def test_hooked_root_add_hook_accepts_official_hook_keyword() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    root.add_hook(
        "blocks.0.hook_resid_pre",
        hook=lambda activation, _hook: activation + [1],
    )
    root.add_perma_hook(
        "blocks.0.hook_resid_pre",
        hook=lambda activation, _hook: activation + [2],
    )

    assert resid([0]) == [0, 1, 2]
    root.reset_hooks(including_permanent=True)
    assert resid([0]) == [0]


def test_hooked_root_add_hook_passes_alias_names_to_hookpoint() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    seen_names: list[str] = []

    def record_alias(activation: list[int], hook: HookPoint) -> list[int]:
        seen_names.append(str(hook.name))
        return activation + [hook.layer()]

    handles = root.add_hook(
        "blocks.0.hook_resid_pre",
        record_alias,
        alias_names=["blocks.0.hook_resid_pre", "layer_2.resid_pre"],
    )

    assert resid([5]) == [5, 0, 2]
    assert seen_names == ["blocks.0.hook_resid_pre", "layer_2.resid_pre"]
    for handle in handles:
        handle.remove()
    assert resid([5]) == [5]


def test_hooked_root_alias_hook_keeps_earlier_alias_patch_when_later_alias_observes() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    seen_names: list[str] = []

    def patch_first_alias_only(activation: list[int], hook: HookPoint) -> list[int] | None:
        seen_names.append(str(hook.name))
        if hook.name == "blocks.0.hook_resid_pre":
            return activation + [1]
        return None

    handles = root.add_hook(
        "blocks.0.hook_resid_pre",
        patch_first_alias_only,
        alias_names=["blocks.0.hook_resid_pre", "layer_0.resid_pre"],
    )

    assert resid([5]) == [5, 1]
    assert seen_names == ["blocks.0.hook_resid_pre", "layer_0.resid_pre"]
    for handle in handles:
        handle.remove()


def test_hooked_root_hooks_clean_up_partial_adds_after_invalid_spec() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    with pytest.raises(KeyError):
        with root.hooks(
            fwd_hooks=[
                ("blocks.0.hook_resid_pre", lambda activation, _hook: activation + [1]),
                ("blocks.99.hook_resid_pre", lambda activation, _hook: activation + [99]),
            ]
        ):
            pass

    assert resid([0]) == [0]
    assert not resid.has_hooks()


def test_hooked_root_cache_all_and_cache_some_persist_until_reset() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    all_cache = root.cache_all()
    resid([1])
    mlp([2])

    assert set(all_cache) == {"blocks.0.hook_resid_pre", "blocks.0.hook_mlp_out"}

    root.reset_hooks()
    filtered_cache = root.cache_some(lambda name: name.endswith("resid_pre"))
    resid([3])
    mlp([4])

    assert filtered_cache.to_dict() == {"blocks.0.hook_resid_pre": [3]}

    root.reset_hooks()
    named_cache = root.cache_some(names="blocks.0.hook_mlp_out")
    resid([5])
    mlp([6])

    assert named_cache.to_dict() == {"blocks.0.hook_mlp_out": [6]}


def test_hooked_root_persistent_cache_helpers_remove_batch_dim() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    all_cache = root.cache_all(remove_batch_dim=True)
    resid([[[1], [2]]])
    mlp([[[3], [4]]])

    assert all_cache.has_batch_dim is False
    assert all_cache.to_dict() == {
        "blocks.0.hook_resid_pre": [[1], [2]],
        "blocks.0.hook_mlp_out": [[3], [4]],
    }

    root.reset_hooks()
    filtered_cache = root.cache_some(
        lambda name: name.endswith("resid_pre"),
        remove_batch_dim=True,
    )
    resid([[[5], [6]]])
    mlp([[[7], [8]]])

    assert filtered_cache.has_batch_dim is False
    assert filtered_cache.to_dict() == {"blocks.0.hook_resid_pre": [[5], [6]]}


def test_hooked_root_run_with_cache_can_slice_positions_and_remove_batch_dim() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    _output, cache = root.run_with_cache(
        lambda: resid([[[1, 10], [2, 20], [3, 30]]]),
        pos_slice=1,
        remove_batch_dim=True,
    )

    assert cache.to_dict() == {"blocks.0.hook_resid_pre": [[2, 20]]}


def test_hooked_root_run_with_cache_preserves_external_empty_cache() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    root.normalization_type = "none"
    root.W_U = [[1.0, 0.0], [0.0, 1.0]]
    external_cache = ActivationCache()

    _output, cache = root.run_with_cache(lambda: resid([1]), cache=external_cache)

    assert cache is external_cache
    assert cache.model is root
    assert cache.residual_stack_to_logits(
        [[[[1.0, 2.0]]]],
        apply_ln=False,
        use_unembed_bias=False,
    ) == [[[[1.0, 2.0]]]]
    assert external_cache.to_dict() == {"blocks.0.hook_resid_pre": [1]}


def test_hook_point_backward_hooks_transform_gradients() -> None:
    torch = pytest.importorskip("torch")
    hook = HookPoint("blocks.0.hook_resid_post")
    hook.add_hook(lambda grad, _hook: grad * 3, dir="bwd")
    value = torch.tensor([2.0], requires_grad=True)

    output = hook(value)
    (output * 5).sum().backward()

    assert torch.equal(value.grad, torch.tensor([15.0]))


def test_hook_point_lens_handles_expose_transformerlens_introspection_fields() -> None:
    hook = HookPoint("blocks.0.hook_resid_post")

    def append_one(activation: list[int], _hook: HookPoint) -> list[int]:
        return activation + [1]

    handle = hook.add_hook(append_one, level=7)
    permanent = hook.add_perma_hook(lambda activation, _hook: activation + [2])

    assert handle.context_level == 7
    assert handle.level == 7
    assert handle.user_hook is append_one
    assert handle.hook is handle
    assert permanent.is_permanent is True
    assert repr(hook) == "HookPoint(name='blocks.0.hook_resid_post', 2 fwd)"

    handle.context_level = 8
    assert handle.level == 8
    handle.remove()
    assert handle.removed is True
    assert repr(hook) == "HookPoint(name='blocks.0.hook_resid_post', 1 fwd)"


def test_hook_point_backward_scale_matches_transformerlens_sum_workflow() -> None:
    torch = pytest.importorskip("torch")
    hook = HookPoint("blocks.0.hook_resid_post")
    observed: list[Any] = []

    def record_scaled_sum(grad: Any, _hook: HookPoint) -> Any:
        observed.append(grad.sum())
        return None

    hook.backward_scale = 0.25
    hook.add_hook(record_scaled_sum, dir="bwd")
    value = torch.tensor([1.0, 2.0], requires_grad=True)

    hook(value).sum().backward()

    assert torch.equal(observed[0], torch.tensor(0.5))
    assert torch.equal(value.grad, torch.ones_like(value))


def test_hook_point_enable_reshape_converts_and_reverts_hook_values() -> None:
    class ListConversion:
        def __init__(self) -> None:
            self.converted: list[Any] = []
            self.reverted: list[Any] = []

        def convert(self, activation: list[int]) -> tuple[int, ...]:
            self.converted.append(activation)
            return tuple(activation)

        def revert(self, activation: tuple[int, ...]) -> list[int]:
            self.reverted.append(activation)
            return list(activation)

    hook = HookPoint("blocks.0.hook_resid_post")
    conversion = ListConversion()
    hook.enable_reshape(conversion)

    def append_seen(activation: tuple[int, ...], hook: HookPoint) -> tuple[int, ...]:
        hook.ctx["saw_tuple"] = isinstance(activation, tuple)
        return (*activation, hook.layer())

    hook.add_hook(append_seen)

    assert hook.forward([7]) == [7, 0]
    assert hook.ctx["saw_tuple"] is True
    assert conversion.converted == [[7]]
    assert conversion.reverted == [(7, 0)]


def test_hook_point_enable_reshape_preserves_original_output_without_hook_return() -> None:
    class ListConversion:
        def convert(self, activation: list[int]) -> tuple[int, ...]:
            return tuple(activation)

        def revert(self, activation: tuple[int, ...]) -> list[int]:
            return list(activation)

    hook = HookPoint("blocks.0.hook_resid_post")
    hook.enable_reshape(ListConversion())
    seen: list[tuple[int, ...]] = []

    def observe(activation: tuple[int, ...], _hook: HookPoint) -> None:
        seen.append(activation)
        return None

    hook.add_hook(observe)

    assert hook([7]) == [7]
    assert seen == [(7,)]


def test_hook_point_enable_reshape_converts_and_reverts_backward_hooks() -> None:
    torch = pytest.importorskip("torch")

    class TupleConversion:
        def __init__(self) -> None:
            self.converted: list[Any] = []
            self.reverted: list[Any] = []

        def convert(self, activation: Any) -> tuple[Any, ...]:
            self.converted.append(activation)
            return (activation,)

        def revert(self, activation: tuple[Any, ...]) -> Any:
            self.reverted.append(activation)
            return activation[0]

    hook = HookPoint("blocks.0.hook_resid_post")
    conversion = TupleConversion()
    seen: list[Any] = []
    hook.enable_reshape(conversion)

    def double_tuple_grad(grad: tuple[Any, ...], _hook: HookPoint) -> tuple[Any, ...]:
        seen.append(grad)
        return (grad[0] * 2,)

    hook.add_hook(double_tuple_grad, dir="bwd")
    value = torch.tensor([3.0], requires_grad=True)

    (hook(value) * 5).sum().backward()

    assert len(seen) == 1
    assert isinstance(seen[0], tuple)
    assert torch.equal(seen[0][0], torch.tensor([5.0]))
    assert torch.equal(value.grad, torch.tensor([10.0]))
    assert torch.equal(conversion.converted[0], torch.tensor([5.0]))
    assert torch.equal(conversion.reverted[0][0], torch.tensor([10.0]))


def test_hooked_root_backward_caching_hooks_capture_gradients() -> None:
    torch = pytest.importorskip("torch")
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_post")
    cache, fwd_hooks, bwd_hooks = root.get_caching_hooks(
        "blocks.0.hook_resid_post",
        incl_bwd=True,
        detach=False,
    )
    value = torch.tensor([2.0], requires_grad=True)

    with root.hooks(fwd_hooks=fwd_hooks, bwd_hooks=bwd_hooks):
        output = resid(value)
        (output * 5).sum().backward()

    assert torch.equal(cache["blocks.0.hook_resid_post"], torch.tensor([2.0]))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.tensor([5.0]))


def test_hooked_root_backward_cache_pos_slice_uses_activation_name_before_grad_suffix() -> None:
    torch = pytest.importorskip("torch")
    root = HookedRoot()
    q_hook = root.add_hook_point("blocks.0.attn.hook_q")
    cache, fwd_hooks, bwd_hooks = root.get_caching_hooks(
        "blocks.0.attn.hook_q",
        incl_bwd=True,
        detach=False,
        pos_slice=1,
    )
    value = torch.arange(8.0, requires_grad=True).reshape(1, 2, 2, 2)
    value.retain_grad()

    with root.hooks(fwd_hooks=fwd_hooks, bwd_hooks=bwd_hooks):
        output = q_hook(value)
        (output * torch.arange(8.0).reshape(1, 2, 2, 2)).sum().backward()

    assert torch.equal(cache["blocks.0.attn.hook_q"], value[:, [1]])
    assert torch.equal(cache["blocks.0.attn.hook_q_grad"], value.grad[:, [1]])


def test_hooked_root_run_with_cache_incl_bwd_runs_backward_and_caches_gradients() -> None:
    torch = pytest.importorskip("torch")
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_post")
    value = torch.tensor([2.0], requires_grad=True)

    output, cache = root.run_with_cache(lambda: (resid(value) * 5).sum(), incl_bwd=True)

    assert torch.equal(output, torch.tensor(10.0))
    assert torch.equal(value.grad, torch.tensor([5.0]))
    assert torch.equal(cache["blocks.0.hook_resid_post"], torch.tensor([2.0]))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.tensor([5.0]))
    assert not resid.has_hooks()


def test_hooked_root_run_with_cache_incl_bwd_uses_loss_from_tuple_output() -> None:
    torch = pytest.importorskip("torch")
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_post")
    value = torch.tensor([2.0], requires_grad=True)

    output, cache = root.run_with_cache(
        lambda: (resid(value) * 7, (resid(value) * 3).sum()),
        incl_bwd=True,
    )

    assert torch.equal(output[0], torch.tensor([14.0]))
    assert torch.equal(output[1], torch.tensor(6.0))
    assert torch.equal(value.grad, torch.tensor([3.0]))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.tensor([3.0]))
    assert not resid.has_hooks()


def test_hooked_root_run_with_cache_incl_bwd_uses_loss_from_mapping_output() -> None:
    torch = pytest.importorskip("torch")
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_post")
    value = torch.tensor([2.0], requires_grad=True)

    output, cache = root.run_with_cache(
        lambda: {"logits": resid(value) * 11, "loss": (resid(value) * 4).sum()},
        incl_bwd=True,
    )

    assert torch.equal(output["logits"], torch.tensor([22.0]))
    assert torch.equal(output["loss"], torch.tensor(8.0))
    assert torch.equal(value.grad, torch.tensor([4.0]))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.tensor([4.0]))
    assert not resid.has_hooks()


def test_hooked_root_run_with_hooks_warns_when_backward_hooks_reset_before_backward() -> None:
    torch = pytest.importorskip("torch")
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_post")
    value = torch.tensor([2.0], requires_grad=True)

    with pytest.warns(UserWarning, match="backward hooks before a backward pass"):
        output = root.run_with_hooks(
            lambda: (resid(value) * 5).sum(),
            bwd_hooks=[("blocks.0.hook_resid_post", lambda grad, _hook: grad * 3)],
        )

    output.backward()

    assert torch.equal(value.grad, torch.tensor([5.0]))
    assert not resid.has_hooks()


def test_hooked_root_run_with_hooks_keeps_backward_hooks_when_reset_disabled() -> None:
    torch = pytest.importorskip("torch")
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_post")
    value = torch.tensor([2.0], requires_grad=True)

    output = root.run_with_hooks(
        lambda: (resid(value) * 5).sum(),
        bwd_hooks=[("blocks.0.hook_resid_post", lambda grad, _hook: grad * 3)],
        reset_hooks_end=False,
    )
    output.backward()

    assert torch.equal(value.grad, torch.tensor([15.0]))
    assert resid.has_hooks("bwd")
    root.reset_hooks()
    assert not resid.has_hooks()


def test_activation_cache_apply_ln_can_recompute_final_layernorm() -> None:
    torch = pytest.importorskip("torch")

    class FinalLayerNormModel:
        def __init__(self) -> None:
            self.n_layers = 0
            self.normalization_type = "LN"
            self.ln_final = torch.nn.LayerNorm(3, elementwise_affine=False)

    model = FinalLayerNormModel()
    cache = ActivationCache(
        {"ln_final.hook_scale": torch.full((1, 1, 1), 100.0)},
        model=model,
    )
    residual_stack = torch.tensor([[[[1.0, 2.0, 3.0]]], [[[2.0, 2.0, 2.0]]]])

    recomputed = cache.apply_ln_to_stack(residual_stack, layer=-1, recompute_ln=True)

    expected = torch.stack([model.ln_final(component) for component in residual_stack])
    assert torch.allclose(recomputed, expected)
    assert not torch.allclose(
        recomputed,
        cache.apply_ln_to_stack(residual_stack, layer=-1),
    )


def test_activation_cache_decoder_apply_ln_recomputes_decoder_final_layernorm() -> None:
    torch = pytest.importorskip("torch")

    class ScaleNorm(torch.nn.Module):
        def __init__(self, scale: float) -> None:
            super().__init__()
            self.scale = scale

        def forward(self, activation: Any) -> Any:
            return activation * self.scale

    class Seq2SeqFinalLayerNormModel:
        def __init__(self) -> None:
            self.n_layers = 0
            self.decoder_n_layers = 0
            self.normalization_type = "LN"
            self.ln_final = ScaleNorm(10.0)
            self.decoder = type("Decoder", (), {"final_layer_norm": ScaleNorm(100.0)})()

    model = Seq2SeqFinalLayerNormModel()
    cache = ActivationCache(
        {"ln_final.hook_scale": torch.ones(1, 1, 1)},
        model=model,
    )
    residual_stack = torch.tensor([[[[1.0, 2.0]]]])

    encoder_recomputed = cache.apply_ln_to_stack(
        residual_stack,
        layer=-1,
        recompute_ln=True,
    )
    decoder_recomputed = cache.apply_ln_to_stack(
        residual_stack,
        layer=-1,
        recompute_ln=True,
        stack="decoder",
    )

    assert torch.equal(encoder_recomputed, residual_stack * 10.0)
    assert torch.equal(decoder_recomputed, residual_stack * 100.0)


def test_activation_cache_accumulated_resid_recomputes_final_layernorm() -> None:
    torch = pytest.importorskip("torch")

    class FinalLayerNormModel:
        def __init__(self) -> None:
            self.n_layers = 1
            self.normalization_type = "LN"
            self.ln_final = torch.nn.LayerNorm(3, elementwise_affine=False)

    model = FinalLayerNormModel()
    cache = ActivationCache(
        {
            "blocks.0.hook_resid_pre": torch.tensor([[[1.0, 2.0, 3.0]]]),
            "blocks.0.hook_resid_post": torch.tensor([[[2.0, 2.0, 2.0]]]),
            "ln_final.hook_scale": torch.full((1, 1, 1), 100.0),
        },
        model=model,
    )

    stack, labels = cache.accumulated_resid(apply_ln=True, return_labels=True)

    raw_stack = torch.stack(
        [
            cache["blocks.0.hook_resid_pre"],
            cache["blocks.0.hook_resid_post"],
        ]
    )
    expected = torch.stack([model.ln_final(component) for component in raw_stack])
    assert labels == ["0_pre", "final_post"]
    assert torch.allclose(stack, expected)
    assert not torch.allclose(
        stack,
        cache.apply_ln_to_stack(raw_stack, layer=-1),
    )


def test_activation_cache_toggle_autodiff_matches_transformerlens_helper() -> None:
    torch = pytest.importorskip("torch")
    cache = ActivationCache()
    previous = torch.is_grad_enabled()

    try:
        cache.toggle_autodiff(False)
        assert not torch.is_grad_enabled()
        cache.toggle_autodiff(True)
        assert torch.is_grad_enabled()
    finally:
        torch.set_grad_enabled(previous)


def test_slice_applies_transformerlens_modes_to_lists_and_indices() -> None:
    values = [[1, 2, 3, 4], [5, 6, 7, 8]]

    assert Slice(1).apply(values, dim=1) == [2, 6]
    assert Slice.unwrap(1).apply(values, dim=1) == [[2], [6]]
    assert Slice((1, 3)).apply(values, dim=1) == [[2, 3], [6, 7]]
    assert Slice([0, 2]).apply(values, dim=1) == [[1, 3], [5, 7]]
    assert Slice([True, False, True, False]).apply(values, dim=1) == [[1, 3], [5, 7]]
    assert Slice(None).apply(values, dim=0) == values
    assert Slice(1).indices().tolist() == [1]
    assert Slice((1, 4, 2)).indices(6).tolist() == [1, 3]
    assert Slice([0, 2]).indices(4).tolist() == [0, 2]
    with pytest.raises(IndexError, match="Boolean index has length"):
        Slice([True, False, True]).apply(values, dim=1)


def test_slice_applies_transformerlens_modes_to_torch_tensors() -> None:
    torch = pytest.importorskip("torch")
    tensor = torch.arange(6).reshape(2, 3)

    assert torch.equal(Slice(1).apply(tensor, dim=1), torch.tensor([1, 4]))
    assert torch.equal(Slice.unwrap(1).apply(tensor, dim=1), torch.tensor([[1], [4]]))
    assert torch.equal(Slice([0, 2]).apply(tensor, dim=1), torch.tensor([[0, 2], [3, 5]]))


def test_hooked_root_cache_pos_slice_accepts_public_slice_object() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    cache, fwd_hooks, _ = root.get_caching_hooks(
        "blocks.0.hook_resid_pre",
        pos_slice=Slice.unwrap(1),
        remove_batch_dim=True,
    )
    with root.hooks(fwd_hooks=fwd_hooks):
        resid([[[1, 10], [2, 20], [3, 30]]])

    assert cache["blocks.0.hook_resid_pre"] == [[2, 20]]


def test_transformerlens_tensor_utilities_work_without_transformerlens_dependency() -> None:
    assert to_numpy([1, 2]).tolist() == [1, 2]
    assert get_corner([[1, 2, 3], [4, 5, 6]], n=1) == [[1]]
    assert remove_batch_dim([[[1, 2], [3, 4]]]) == [[1, 2], [3, 4]]
    assert remove_batch_dim([[1, 2], [3, 4]]) == [[1, 2], [3, 4]]
    assert tensor_transpose([[[1, 2], [3, 4]]]) == [[[1, 3], [2, 4]]]
    assert is_square([[1, 0], [2, 3]])
    assert not is_square([[1, 0, 0], [2, 3, 0]])
    assert is_lower_triangular([[1, 0, 0], [2, 3, 0], [4, 5, 6]])
    assert not is_lower_triangular([[1, 7], [2, 3]])
    assert get_offset_position_ids(1, [[0, 0, 1, 1], [0, 1, 1, 1]]) == [
        [0, 0, 1],
        [0, 1, 2],
    ]
    assert get_cumsum_along_dim([[1, 2, 3], [4, 5, 6]], dim=1) == [[1, 3, 6], [4, 9, 15]]
    assert get_cumsum_along_dim([[1, 2, 3], [4, 5, 6]], dim=1, reverse=True) == [
        [6, 5, 3],
        [15, 11, 6],
    ]
    assert repeat_along_head_dimension([[[1, 2], [3, 4]]], 2) == [
        [[[1, 2], [1, 2]], [[3, 4], [3, 4]]]
    ]
    assert filter_dict_by_prefix({"a.b": 1, "a.c": 2, "ab.d": 3}, "a") == {"b": 1, "c": 2}


def test_transformerlens_tensor_utilities_support_torch_tensors() -> None:
    torch = pytest.importorskip("torch")
    matrix = torch.tensor([[1, 0], [2, 3]])
    mask = torch.tensor([[0, 1, 1], [1, 1, 1]])
    values = torch.tensor([[[1, 2], [3, 4]]])

    assert is_lower_triangular(matrix)
    assert torch.equal(get_offset_position_ids(1, mask), torch.tensor([[0, 1], [1, 2]]))
    assert torch.equal(
        get_cumsum_along_dim(torch.tensor([[1, 2, 3]]), dim=1), torch.tensor([[1, 3, 6]])
    )
    assert repeat_along_head_dimension(values, 2).shape == (1, 2, 2, 2)


def test_activation_functions_match_transformerlens_scalar_formulas() -> None:
    values = [-1.0, 0.0, 2.0]
    expected_gelu_new = [
        0.5 * value * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (value + 0.044715 * value**3)))
        for value in values
    ]

    assert_nested_close(gelu_new(values), expected_gelu_new)
    assert_nested_close(gelu_pytorch_tanh(values), expected_gelu_new)
    assert_nested_close(silu(values), [value / (1.0 + math.exp(-value)) for value in values])
    assert set(SUPPORTED_ACTIVATIONS) >= {
        "solu",
        "solu_ln",
        "gelu_new",
        "gelu_fast",
        "silu",
        "relu",
        "gelu",
        "gelu_pytorch_tanh",
        "xielu",
    }
    assert gelu_fast(0.0) == 0.0
    assert xielu(2.0) == 4.2


def test_activation_functions_support_torch_tensors() -> None:
    torch = pytest.importorskip("torch")
    values = torch.tensor([[-1.0, 0.0, 2.0]])

    assert torch.allclose(gelu_new(values), SUPPORTED_ACTIVATIONS["gelu_new"](values))
    assert torch.allclose(solu(values), values * torch.softmax(values, dim=-1))
    assert torch.allclose(xielu(values), SUPPORTED_ACTIVATIONS["xielu"](values))
    module = XIELU()
    assert torch.allclose(module(values), xielu(values), atol=1e-6)


def test_transformerlens_utility_helpers_cover_defaults_and_nested_attrs() -> None:
    class _Cfg:
        default_prepend_bos = True

    class _Tokenizer:
        padding_side = "right"

    class _Model:
        cfg = _Cfg()
        tokenizer = _Tokenizer()

    model = _Model()

    assert get_nested_attr(model, "cfg.default_prepend_bos") is True
    set_nested_attr(model, "tokenizer.padding_side", "left")
    assert model.tokenizer.padding_side == "left"
    assert override_or_use_default_value(True, USE_DEFAULT_VALUE) is True
    assert override_or_use_default_value(True, False) is False

    with LocallyOverridenDefaults(model, prepend_bos=False, padding_side="right"):
        assert model.cfg.default_prepend_bos is False
        assert model.tokenizer.padding_side == "right"

    assert model.cfg.default_prepend_bos is True
    assert model.tokenizer.padding_side == "left"


def test_transformerlens_device_library_and_initialization_helpers() -> None:
    assert is_library_available("math")
    assert not is_library_available("definitely_missing_safelens_dependency")
    assert get_device() in {"cpu", "cuda", "mps"}
    assert calc_fan_in_and_fan_out(type("_TensorLike", (), {"shape": (2, 3, 4)})()) == (3, 8)

    torch = pytest.importorskip("torch")
    param = torch.empty(2, 3)
    initialized = init_xavier_uniform_(param, gain=1.0)
    assert initialized is param
    assert torch.all(param <= 1.0955)
    assert torch.all(param >= -1.0955)


def test_transformerlens_tokenizer_and_hf_lite_utilities() -> None:
    class _LegacyConfig:
        rotary_pct = 0.25

    class _RopeConfig:
        rope_parameters = {"partial_rotary_factor": 0.5}

    class _Tokenizer:
        bos_token = "<bos>"
        bos_token_id = 1
        eos_token_id = 2
        pad_token_id = 0
        pad_token = "<pad>"
        padding_side = "right"

        def __call__(self, text: list[str], add_special_tokens: bool = False) -> dict[str, Any]:
            assert add_special_tokens is False
            return {"input_ids": [[ord(char) % 10 for char in item] for item in text]}

    class _Dataset:
        features = {"text": object(), "meta": object()}

        def __init__(self) -> None:
            self.removed: list[str] = []
            self.formatted = False
            self.tokens: Any = None

        def remove_columns(self, key: str) -> Any:
            self.removed.append(key)
            return self

        def map(self, fn: Any, **kwargs: Any) -> Any:
            assert kwargs["batched"] is True
            assert kwargs["remove_columns"] == ["text"]
            self.tokens = fn({"text": ["ab", "c"]})["tokens"]
            return self

        def set_format(self, *, type: str, columns: list[str]) -> None:
            assert type == "torch"
            assert columns == ["tokens"]
            self.formatted = True

    tokenizer = _Tokenizer()
    dataset = _Dataset()

    assert get_rotary_pct_from_config(_LegacyConfig()) == 0.25
    assert get_rotary_pct_from_config(_RopeConfig()) == 0.5
    assert get_rotary_pct_from_config({"rotary_pct": 0.75}) == 0.75
    assert (
        get_rotary_pct_from_config({"rope_parameters": {"partial_rotary_factor": 0.125}}) == 0.125
    )
    assert get_rotary_pct_from_config(None) == 1.0
    assert select_compatible_kwargs({"a": 1, "b": 2}, lambda a: a) == {"a": 1}
    assert get_input_with_manually_prepended_bos("<bos>", ["a", "b"]) == ["<bos>a", "<bos>b"]
    assert get_tokens_with_bos_removed(tokenizer, [[1, 9, 0], [1, 8, 0]]) == [[9, 0], [8, 0]]
    assert get_attention_mask(tokenizer, [[1, 9, 0], [1, 0, 0]], prepend_bos=True) == [
        [1, 1, 0],
        [1, 0, 0],
    ]

    tokenized = tokenize_and_concatenate(dataset, tokenizer, max_length=4, num_proc=1)

    assert tokenized is dataset
    assert dataset.removed == ["meta"]
    assert dataset.formatted
    assert dataset.tokens == [[1, 7, 8, 2]]


def test_transformerlens_left_padding_token_helpers_match_bos_edge_case() -> None:
    class _Tokenizer:
        bos_token_id = 0
        pad_token_id = 0
        padding_side = "left"

    tokenizer = _Tokenizer()

    assert get_tokens_with_bos_removed(tokenizer, [[0, 0, 5, 6], [0, 7, 8, 9]]) == [
        [0, 5, 6],
        [7, 8, 9],
    ]
    assert get_attention_mask(tokenizer, [[0, 0, 5, 6], [0, 7, 8, 9]], prepend_bos=True) == [
        [0, 1, 1, 1],
        [1, 1, 1, 1],
    ]


def test_transformerlens_multi_device_helpers_cover_non_cuda_paths() -> None:
    torch = pytest.importorskip("torch")

    class _Cfg:
        device = "cpu"
        n_devices = 4
        n_layers = 8

    class _Model:
        hf_device_map = {"embed": "cpu", "block.0": "cpu"}

    assert get_best_available_device(_Cfg()) == torch.device("cpu")
    assert get_device_for_block_index(7, _Cfg()) == torch.device("cpu")
    assert resolve_device_map(None, None, "cpu") == (None, None)
    assert resolve_device_map(1, None, None, max_memory={0: "1GiB"}) == (None, {0: "1GiB"})
    assert resolve_device_map(None, {"blocks.0": 0}, None) == ({"blocks.0": 0}, None)
    with pytest.raises(ValueError, match="mutually exclusive"):
        resolve_device_map(None, {"blocks.0": 0}, "cuda")
    with pytest.raises(ValueError, match="not supported"):
        resolve_device_map(None, {"blocks.0": "cpu"}, None)

    model = _Model()
    assert count_unique_devices(model) == 1
    assert find_embedding_device(model) == torch.device("cpu")
    assert count_unique_devices(object()) == 1


def test_safelens_utils_reexports_transformerlens_style_helpers() -> None:
    import SafeLens.utils as utils

    assert utils.Slice.unwrap(1).apply([[1, 2], [3, 4]], dim=1) == [[2], [4]]
    assert utils.get_act_name("k6") == "blocks.6.attn.hook_k"
    assert utils.to_numpy([1, 2]).tolist() == [1, 2]
    assert utils.calc_fan_in_and_fan_out(type("_TensorLike", (), {"shape": (4,)})()) == (1, 4)
    assert utils.get_input_with_manually_prepended_bos("<s>", "hello") == "<s>hello"
    assert utils.resolve_device_map(None, None, "cpu") == (None, None)
    assert utils.sort_devices_based_on_available_memory([(1, 4), (0, 8)]) == [(0, 8), (1, 4)]
    assert utils.get_hf_token() is None
    for name in (
        "batch_addmm",
        "call_hf_with_retry",
        "complex_attn_linear",
        "download_file_from_hf",
        "get_dataset",
        "get_matrix_corner",
        "simple_attn_linear",
        "vanilla_addmm",
    ):
        assert callable(getattr(utils, name))


def test_transformerlens_attention_and_addmm_utilities_match_torch_formulas() -> None:
    torch = pytest.importorskip("torch")

    input_tensor = torch.tensor(
        [
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        ]
    )
    weights = torch.tensor(
        [
            [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
            [[2.0, 0.0], [0.0, 2.0], [1.0, -1.0]],
        ]
    )
    bias = torch.tensor([[0.5, -0.5], [1.0, 2.0]])

    simple = simple_attn_linear(input_tensor, weights, bias)
    expected_simple = torch.einsum("bpd,hde->bphe", input_tensor, weights) + bias

    head_input = input_tensor.unsqueeze(2).expand(-1, -1, weights.shape[0], -1)
    complex_result = complex_attn_linear(head_input, weights, bias)
    expected_complex = torch.einsum("bphd,hde->bphe", head_input, weights) + bias

    addmm_bias = torch.tensor([0.25, -0.5])
    mat1 = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    mat2 = torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, -1.0]])
    batched_x = mat1.view(1, 2, 3)

    assert torch.allclose(simple, expected_simple)
    assert torch.allclose(complex_result, expected_complex)
    assert torch.allclose(
        vanilla_addmm(addmm_bias, mat1, mat2), torch.addmm(addmm_bias, mat1, mat2)
    )
    assert torch.allclose(
        batch_addmm(addmm_bias, mat2, batched_x),
        torch.addmm(addmm_bias, mat1, mat2).view(1, 2, 2),
    )


def test_transformerlens_hf_retry_and_matrix_corner_utilities() -> None:
    calls = {"count": 0}

    class _Response:
        status_code = 429
        headers = {"Retry-After": "0"}

    class _RateLimit(Exception):
        response = _Response()

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            raise _RateLimit()
        return "ok"

    matrix = FactoredMatrix([[1, 2, 3], [4, 5, 6]], [[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    assert call_hf_with_retry(flaky, max_attempts=2, base_delay=0) == "ok"
    assert calls["count"] == 2
    assert get_matrix_corner(matrix, n=2) == [[1, 2], [4, 5]]


def test_factored_matrix_dense_ops_and_composition() -> None:
    left = FactoredMatrix([[1, 2], [3, 4]], [[2, 0], [0, 2]])
    right = FactoredMatrix([[1, 0], [0, 1]], [[1], [2]])
    composed = left @ right

    assert left.AB == [[2.0, 4.0], [6.0, 8.0]]
    assert left.BA == [[2.0, 4.0], [6.0, 8.0]]
    assert left.mdim == 2
    assert left.has_leading_dims is False
    assert left.T.AB == [[2.0, 6.0], [4.0, 8.0]]
    assert composed.AB == [[10.0], [22.0]]
    assert (left @ [1, 1]) == [6.0, 14.0]
    assert math.isclose(left.norm(), math.sqrt(120.0))
    assert left.get_corner(1) == [[2.0]]
    assert matmul([[[1, 2], [3, 4]]], [[1], [2]]) == [[[5.0], [11.0]]]


def test_factored_matrix_list_backend_batched_matrix_vector_products() -> None:
    batched = [
        [[1, 2], [3, 4]],
        [[5, 6], [7, 8]],
    ]
    identity = [
        [[1, 0], [0, 1]],
        [[1, 0], [0, 1]],
    ]

    assert matmul(batched, [10, 1]) == [[12.0, 34.0], [56.0, 78.0]]
    assert matmul([10, 1], batched) == [[13.0, 24.0], [57.0, 68.0]]
    assert FactoredMatrix(batched, identity) @ [10, 1] == [[12.0, 34.0], [56.0, 78.0]]
    assert [10, 1] @ FactoredMatrix(identity, batched) == [[13.0, 24.0], [57.0, 68.0]]


def test_factored_matrix_composes_nontrivial_factors_once() -> None:
    left = FactoredMatrix([[1, 2]], [[3, 4], [5, 6]])
    right = FactoredMatrix([[7, 8], [9, 10]], [[11], [12]])

    assert (left @ right).AB == matmul(left.AB, right.AB)


def test_factored_matrix_composition_matches_transformerlens_hidden_dim_collapse() -> None:
    left = FactoredMatrix([[1, 0, 0], [0, 1, 0]], [[1, 2], [3, 4], [5, 6]])
    right_matrix = [[1], [2]]
    right = FactoredMatrix([[1, 0], [0, 1]], [[1], [2]])
    left_matrix = [[1, 2], [3, 4], [5, 6]]

    right_result = left @ right_matrix
    factored_result = left @ right
    left_result = left_matrix @ left

    assert isinstance(right_result, FactoredMatrix)
    assert isinstance(factored_result, FactoredMatrix)
    assert isinstance(left_result, FactoredMatrix)
    assert right_result.AB == matmul(left.AB, right_matrix)
    assert factored_result.AB == matmul(left.AB, right.AB)
    assert left_result.AB == matmul(left_matrix, left.AB)
    assert right_result.mdim == min(left.ldim, left.rdim)
    assert factored_result.mdim == min(left.ldim, left.rdim)
    assert left_result.mdim == min(left.ldim, left.rdim)


def test_factored_matrix_composition_preserves_standard_leading_broadcast() -> None:
    left = FactoredMatrix(
        [
            [[[1, 0], [0, 1]]],
            [[[2, 0], [0, 2]]],
        ],
        [
            [[[1, 0], [0, 1]]],
            [[[1, 0], [0, 1]]],
        ],
    )
    right = FactoredMatrix(
        [
            [[[1, 0], [0, 1]], [[0, 1], [1, 0]], [[2, 0], [0, 1]]],
        ],
        [
            [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 0], [0, 1]]],
        ],
    )

    composed = left @ right

    assert composed.shape == (2, 3, 2, 2)
    assert composed.AB == matmul(left.AB, right.AB)


def test_factored_matrix_left_matrix_multiply_preserves_factored_form() -> None:
    matrix = FactoredMatrix([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    left_matrix = [[2, 0], [0, 3]]
    left_vector = [2, 3]

    factored = left_matrix @ matrix

    assert isinstance(factored, FactoredMatrix)
    assert factored.AB == matmul(left_matrix, matrix.AB)
    assert left_vector @ matrix == matmul(left_vector, matrix.AB)


def test_factored_matrix_right_matrix_multiply_preserves_factored_form() -> None:
    matrix = FactoredMatrix([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    right_matrix = [[2, 0], [0, 3]]
    right_vector = [2, 3]

    factored = matrix @ right_matrix

    assert isinstance(factored, FactoredMatrix)
    assert factored.AB == matmul(matrix.AB, right_matrix)
    assert matrix @ right_vector == matmul(matrix.AB, right_vector)


def test_factored_matrix_scalar_multiplication_and_svd_aliases() -> None:
    matrix = FactoredMatrix([[1, 0], [0, 2]], [[3, 0], [0, 4]])

    assert (2 * matrix).AB == [[6.0, 0.0], [0.0, 16.0]]
    assert (matrix * 3).AB == [[9.0, 0.0], [0.0, 24.0]]
    with pytest.warns(DeprecationWarning, match="Vh returns V"):
        assert matrix.V == matrix.Vh

    even = matrix.make_even()
    assert_nested_close(even.AB, matrix.AB)
    assert_nested_close(FactoredMatrix(matrix.U, matrix.collapse_l()).AB, matrix.AB)
    assert_nested_close(FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB, matrix.AB)


def test_factored_matrix_accepts_tuple_backed_factors_across_core_workflow() -> None:
    matrix = FactoredMatrix(((1, 2), (3, 4)), ((5, 6), (7, 8)))

    assert matrix.shape == (2, 2)
    assert matrix.AB == [[19.0, 22.0], [43.0, 50.0]]
    assert matrix @ (10, 1) == [212.0, 480.0]
    assert (10, 1) @ matrix == [233.0, 270.0]
    assert (2 * matrix).AB == [[38.0, 44.0], [86.0, 100.0]]
    assert matrix.T.AB == [[19.0, 43.0], [22.0, 50.0]]
    assert matrix[:, 1].AB == [[22.0], [50.0]]
    assert matrix[0].AB == [[19.0, 22.0]]
    assert matrix.unsqueeze(0).shape == (1, 2, 2)
    assert matrix.unsqueeze(k=0).shape == (1, 2, 2)
    assert matrix.get_corner(1) == [[19.0]]


def test_factored_matrix_tuple_backed_broadcast_and_composition_scores() -> None:
    matrix = FactoredMatrix(
        (((1, 0), (0, 1)),),
        (((2, 0), (0, 3)), ((4, 0), (0, 5))),
    )

    assert matrix.shape == (2, 2, 2)
    assert matrix.AB == [
        [[2.0, 0.0], [0.0, 3.0]],
        [[4.0, 0.0], [0.0, 5.0]],
    ]

    left = FactoredMatrix(
        (
            ((1, 0), (0, 1)),
            ((2, 0), (0, 2)),
        ),
        (
            ((1, 0), (0, 1)),
            ((1, 0), (0, 1)),
        ),
    )
    right = FactoredMatrix(
        (
            ((1, 0), (0, 1)),
            ((0, 1), (1, 0)),
            ((2, 0), (0, 1)),
        ),
        (
            ((1, 0), (0, 1)),
            ((1, 0), (0, 1)),
            ((1, 0), (0, 1)),
        ),
    )

    assert_nested_close(
        composition_scores(left, right),
        [
            [0.7071067811865475, 0.7071067811865475, 0.7071067811865475],
            [0.7071067811865475, 0.7071067811865475, 0.7071067811865475],
        ],
    )


def test_factored_matrix_svd_returns_v_not_vh_for_nonsymmetric_matrices() -> None:
    matrix = FactoredMatrix([[1, 2], [3, 5]], [[7, 11], [13, 17]])

    reconstructed = FactoredMatrix(matrix.U, matrix.collapse_l()).AB
    reconstructed_from_right = FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB
    direct_svd_reconstruction = matmul(matrix.collapse_r(), transpose(matrix.V))

    with pytest.warns(DeprecationWarning, match="Vh returns V"):
        assert matrix.V == matrix.Vh
    assert_nested_close(reconstructed, matrix.AB)
    assert_nested_close(reconstructed_from_right, matrix.AB)
    assert_nested_close(direct_svd_reconstruction, matrix.AB)
    assert_nested_close(matrix.make_even().AB, matrix.AB)


def test_factored_matrix_rectangular_eigenvalues_use_inner_product() -> None:
    matrix = FactoredMatrix([[1, 2], [3, 4], [5, 6]], [[7, 8, 9], [10, 11, 12]])
    non_square = FactoredMatrix([[1, 2], [3, 4], [5, 6]], [[7, 8, 9, 10], [11, 12, 13, 14]])

    assert len(matrix.eigenvalues) == 2
    assert_nested_close(
        sorted(matrix.eigenvalues),
        [0.16994755741637846, 211.83005244258362],
        abs_tol=1e-8,
    )
    with pytest.raises(ValueError, match="ldim == rdim"):
        _ = non_square.BA


def test_factored_matrix_numpy_eigenvalues_drop_negligible_imaginary_parts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    np = pytest.importorskip("numpy")

    def fake_eigvals(_matrix: Any) -> Any:
        return np.asarray([1.0 + 0.0j, 2.0 + 1e-14j, 3.0 + 0.5j])

    monkeypatch.setattr(np.linalg, "eigvals", fake_eigvals)

    eigenvalues = FactoredMatrix([[1, 0], [0, 1]], [[1, 0], [0, 1]]).eigenvalues

    assert eigenvalues[:2] == [1.0, 2.0]
    assert eigenvalues[2] == 3.0 + 0.5j


def test_factored_matrix_unsqueeze_repr_and_index_guards() -> None:
    matrix = FactoredMatrix([[1, 0], [0, 1]], [[2, 0], [0, 3]])
    batched = matrix.unsqueeze(0)

    assert repr(matrix) == "FactoredMatrix: Shape((2, 2)), Hidden Dim(2)"
    assert batched.shape == (1, 2, 2)
    assert batched.mdim == 2
    assert batched.has_leading_dims is True
    assert batched[0].AB == matrix.AB
    assert batched.squeeze(0).AB == matrix.AB
    assert batched.squeeze().AB == matrix.AB


def test_factored_matrix_indexes_rows_and_columns_like_transformerlens() -> None:
    matrix = FactoredMatrix([[1, 2], [3, 4]], [[5, 6, 7], [8, 9, 10]])

    assert matrix[1].AB == [matrix.AB[1]]
    assert matrix[-1].AB == [matrix.AB[-1]]
    assert matrix[:, 2].AB == [[27.0], [61.0]]
    assert matrix[:, -1].AB == [[27.0], [61.0]]
    assert matrix[1, 2].AB == [[61.0]]
    assert matrix[1, -1].AB == [[61.0]]
    assert matrix[...].AB == matrix.AB
    assert matrix[..., -1].AB == [[27.0], [61.0]]
    with pytest.raises(ValueError, match="too long"):
        _ = matrix[0, 0, 0]


def test_factored_matrix_indexes_batched_rows_and_columns_like_transformerlens() -> None:
    matrix = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
            [[2, 0], [0, 2]],
        ],
        [
            [[3, 4, 5], [6, 7, 8]],
            [[1, 2, 3], [4, 5, 6]],
        ],
    )

    assert matrix[-1].AB == matrix.AB[-1]
    assert matrix[..., -1].AB == [
        [[5.0], [8.0]],
        [[6.0], [12.0]],
    ]
    assert matrix[-1, :, -1].AB == [[6.0], [12.0]]
    assert matrix[...].AB == matrix.AB


def test_factored_matrix_norm_preserves_leading_dimensions() -> None:
    batched = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
            [[2, 0], [0, 2]],
        ],
        [
            [[3, 0], [0, 4]],
            [[1, 0], [0, 2]],
        ],
    )

    assert_nested_close(batched.norm(), [5.0, math.sqrt(20.0)])


def test_factored_matrix_norm_does_not_materialize_dense_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    matrix = FactoredMatrix([[1, 2, 3], [4, 5, 6]], [[7, 8], [9, 10], [11, 12]])
    expected = math.sqrt(sum(value * value for row in matrix.AB for value in row))

    def fail_ab(_self: FactoredMatrix) -> Any:
        raise AssertionError("norm should not materialize AB")

    monkeypatch.setattr(FactoredMatrix, "AB", property(fail_ab))

    assert math.isclose(matrix.norm(), expected)


def test_factored_matrix_get_corner_does_not_materialize_dense_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    matrix = FactoredMatrix(
        [[1, 2, 3], [4, 5, 6]],
        [[7, 8, 9, 10], [11, 12, 13, 14], [15, 16, 17, 18]],
    )

    def fail_ab(_self: FactoredMatrix) -> Any:
        raise AssertionError("get_corner should not materialize AB")

    monkeypatch.setattr(FactoredMatrix, "AB", property(fail_ab))

    assert matrix.get_corner(2) == [[74.0, 80.0], [173.0, 188.0]]


def test_factored_matrix_broadcasts_singleton_leading_dimensions() -> None:
    matrix = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
        ],
        [
            [[2, 0], [0, 3]],
            [[4, 0], [0, 5]],
        ],
    )

    assert matrix.shape == (2, 2, 2)
    assert matrix.A == [
        [[1, 0], [0, 1]],
        [[1, 0], [0, 1]],
    ]
    assert matrix.AB == [
        [[2.0, 0.0], [0.0, 3.0]],
        [[4.0, 0.0], [0.0, 5.0]],
    ]
    assert matrix[1].AB == [[4.0, 0.0], [0.0, 5.0]]


def test_factored_matrix_numpy_broadcast_preserves_expected_leading_shape() -> None:
    np = pytest.importorskip("numpy")
    left = np.array([[[1.0, 0.0], [0.0, 1.0]]])
    right = np.array([[[2.0, 0.0], [0.0, 3.0]], [[4.0, 0.0], [0.0, 5.0]]])

    matrix = FactoredMatrix(left, right)

    assert matrix.shape == (2, 2, 2)
    assert getattr(matrix.A, "shape", None) == (2, 2, 2)
    assert getattr(matrix.B, "shape", None) == (2, 2, 2)
    assert_nested_close(matrix.AB.tolist(), right.tolist())


def test_factored_matrix_numpy_general_leading_broadcast_shape() -> None:
    np = pytest.importorskip("numpy")
    left = np.ones((2, 1, 2, 2))
    right = np.ones((1, 3, 2, 2))

    matrix = FactoredMatrix(left, right)

    assert matrix.shape == (2, 3, 2, 2)
    assert getattr(matrix.A, "shape", None) == (2, 3, 2, 2)
    assert getattr(matrix.B, "shape", None) == (2, 3, 2, 2)
    assert getattr(matrix.AB, "shape", None) == (2, 3, 2, 2)


def test_factored_matrix_mixed_torch_factor_preserves_tensor_backend_and_grad() -> None:
    torch = pytest.importorskip("torch")
    right = torch.eye(2, requires_grad=True)
    matrix = FactoredMatrix([[1.0, 2.0], [3.0, 4.0]], right)

    dense = matrix.AB
    product = matrix @ torch.ones(2)

    assert isinstance(dense, torch.Tensor)
    assert isinstance(product, torch.Tensor)
    assert torch.equal(dense, torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    dense.sum().backward()
    assert torch.equal(right.grad, torch.tensor([[4.0, 4.0], [6.0, 6.0]]))


def test_factored_matrix_matmul_matches_vector_dot_product_semantics() -> None:
    assert matmul([1, 2, 3], [4, 5, 6]) == 32.0


def test_factored_matrix_transpose_swaps_only_matrix_axes_for_batched_factors() -> None:
    matrix = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
            [[2, 0], [0, 2]],
        ],
        [
            [[3, 4, 5], [6, 7, 8]],
            [[1, 2, 3], [4, 5, 6]],
        ],
    )

    transposed = matrix.T

    assert transposed.shape == (2, 3, 2)
    assert transposed.AB == [
        [[3.0, 6.0], [4.0, 7.0], [5.0, 8.0]],
        [[2.0, 8.0], [4.0, 10.0], [6.0, 12.0]],
    ]


def test_factored_matrix_batched_svd_helpers_reconstruct_dense_product() -> None:
    matrix = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
            [[2, 0], [0, 2]],
        ],
        [
            [[3, 4, 5], [6, 7, 8]],
            [[1, 2, 3], [4, 5, 6]],
        ],
    )

    assert_nested_close(FactoredMatrix(matrix.U, matrix.collapse_l()).AB, matrix.AB)
    assert_nested_close(FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB, matrix.AB)
    assert_nested_close(matrix.make_even().AB, matrix.AB)


def test_factored_matrix_get_corner_preserves_batched_leading_dimensions() -> None:
    matrix = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
            [[2, 0], [0, 2]],
        ],
        [
            [[3, 4, 5], [6, 7, 8]],
            [[1, 2, 3], [4, 5, 6]],
        ],
    )

    assert matrix.get_corner(2) == [
        [[3.0, 4.0], [6.0, 7.0]],
        [[2.0, 4.0], [8.0, 10.0]],
    ]


def test_factored_matrix_torch_transpose_swaps_only_matrix_axes_for_batched_factors() -> None:
    torch = pytest.importorskip("torch")
    matrix = FactoredMatrix(
        torch.tensor(
            [
                [[1.0, 0.0], [0.0, 1.0]],
                [[2.0, 0.0], [0.0, 2.0]],
            ]
        ),
        torch.tensor(
            [
                [[3.0, 4.0, 5.0], [6.0, 7.0, 8.0]],
                [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            ]
        ),
    )

    assert torch.equal(matrix.T.AB, matrix.AB.transpose(-1, -2))


def test_factored_matrix_torch_get_corner_preserves_batched_leading_dimensions() -> None:
    torch = pytest.importorskip("torch")
    matrix = FactoredMatrix(
        torch.tensor(
            [
                [[1.0, 0.0], [0.0, 1.0]],
                [[2.0, 0.0], [0.0, 2.0]],
            ]
        ),
        torch.tensor(
            [
                [[3.0, 4.0, 5.0], [6.0, 7.0, 8.0]],
                [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            ]
        ),
    )

    assert torch.equal(
        matrix.get_corner(2),
        torch.tensor(
            [
                [[3.0, 4.0], [6.0, 7.0]],
                [[2.0, 4.0], [8.0, 10.0]],
            ]
        ),
    )


def test_factored_matrix_torch_batched_svd_helpers_reconstruct_dense_product() -> None:
    torch = pytest.importorskip("torch")
    matrix = FactoredMatrix(
        torch.tensor(
            [
                [[1.0, 0.0], [0.0, 1.0]],
                [[2.0, 0.0], [0.0, 2.0]],
            ]
        ),
        torch.tensor(
            [
                [[3.0, 4.0, 5.0], [6.0, 7.0, 8.0]],
                [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            ]
        ),
    )

    expected = torch.as_tensor(matrix.AB)

    assert isinstance(matrix.U, torch.Tensor)
    assert isinstance(matrix.S, torch.Tensor)
    assert isinstance(matrix.V, torch.Tensor)
    assert isinstance(matrix.collapse_l(), torch.Tensor)
    assert isinstance(matrix.collapse_r(), torch.Tensor)
    assert isinstance(matrix.make_even().A, torch.Tensor)
    assert torch.allclose(FactoredMatrix(matrix.U, matrix.collapse_l()).AB, expected)
    assert torch.allclose(FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB, expected)
    assert torch.allclose(matrix.make_even().AB, expected)


def test_factored_matrix_torch_low_precision_svd_helpers_promote_for_decomposition() -> None:
    torch = pytest.importorskip("torch")
    matrix = FactoredMatrix(
        torch.tensor([[1.0, 0.0], [0.0, 2.0]], dtype=torch.float16),
        torch.tensor([[3.0, 0.0], [0.0, 4.0]], dtype=torch.float16),
    )

    expected = matrix.AB.float()

    assert matrix.S.dtype == torch.float32
    assert torch.allclose(FactoredMatrix(matrix.U, matrix.collapse_l()).AB, expected)
    assert torch.allclose(FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB, expected)
    assert torch.allclose(matrix.make_even().AB, expected)


def test_factored_matrix_numpy_low_precision_svd_helpers_promote_for_decomposition() -> None:
    np = pytest.importorskip("numpy")
    matrix = FactoredMatrix(
        np.array([[1.0, 0.0], [0.0, 2.0]], dtype=np.float16),
        np.array([[3.0, 0.0], [0.0, 4.0]], dtype=np.float16),
    )

    expected = np.asarray(matrix.AB, dtype=np.float32)

    assert np.asarray(matrix.S).dtype != np.float16
    assert_nested_close(FactoredMatrix(matrix.U, matrix.collapse_l()).AB, expected.tolist())
    assert_nested_close(
        FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB,
        expected.tolist(),
    )
    assert_nested_close(matrix.make_even().AB, expected.tolist())


def test_factored_matrix_torch_svd_preserves_inner_rank_for_wide_products() -> None:
    torch = pytest.importorskip("torch")
    matrix = FactoredMatrix(
        torch.arange(12, dtype=torch.float32).reshape(3, 4),
        torch.arange(20, dtype=torch.float32).reshape(4, 5),
    )

    assert matrix.U.shape == (3, 3)
    assert matrix.S.shape == (3,)
    assert matrix.V.shape == (5, 3)
    assert matrix.collapse_r().shape == (3, 3)
    assert matrix.collapse_l().shape == (3, 5)
    assert matrix.make_even().shape == matrix.shape
    assert torch.allclose(matrix.make_even().AB, matrix.AB, atol=1e-4)


def test_factored_matrix_torch_eigenvalues_preserve_tensor_semantics() -> None:
    torch = pytest.importorskip("torch")
    matrix = FactoredMatrix(
        torch.eye(2, requires_grad=True),
        torch.tensor([[2.0, 0.0], [0.0, 3.0]], requires_grad=True),
    )

    eigenvalues = matrix.eigenvalues

    assert isinstance(eigenvalues, torch.Tensor)
    assert torch.allclose(torch.sort(eigenvalues.real).values, torch.tensor([2.0, 3.0]))
    assert eigenvalues.requires_grad is True


def test_factored_matrix_torch_eigenvalues_cast_low_precision_to_float32() -> None:
    torch = pytest.importorskip("torch")
    matrix = FactoredMatrix(
        torch.eye(2, dtype=torch.float16),
        torch.tensor([[2.0, 0.0], [0.0, 3.0]], dtype=torch.float16),
    )

    eigenvalues = matrix.eigenvalues

    assert isinstance(eigenvalues, torch.Tensor)
    assert eigenvalues.dtype == torch.complex64
    assert torch.allclose(torch.sort(eigenvalues.real).values, torch.tensor([2.0, 3.0]))


def test_factored_matrix_composition_scores_match_dense_identity_case() -> None:
    left = FactoredMatrix([[1, 0], [0, 1]], [[2, 0], [0, 3]])
    right = FactoredMatrix([[2, 0], [0, 3]], [[1, 0], [0, 1]])

    assert math.isclose(
        float(composition_scores(left, right)),
        0.7576044462920081,
        abs_tol=1e-12,
    )


def test_factored_matrix_composition_scores_broadcast_leading_dimensions() -> None:
    left = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
            [[2, 0], [0, 2]],
        ],
        [
            [[1, 0], [0, 1]],
            [[1, 0], [0, 1]],
        ],
    )
    right = FactoredMatrix(
        [
            [[1, 0], [0, 1]],
            [[0, 1], [1, 0]],
            [[2, 0], [0, 1]],
        ],
        [
            [[1, 0], [0, 1]],
            [[1, 0], [0, 1]],
            [[1, 0], [0, 1]],
        ],
    )

    scores = composition_scores(left, right)

    assert len(scores) == 2
    assert len(scores[0]) == 3
    assert_nested_close(
        scores,
        [
            [0.7071067811865475, 0.7071067811865475, 0.7071067811865475],
            [0.7071067811865475, 0.7071067811865475, 0.7071067811865475],
        ],
    )


def test_factored_matrix_torch_composition_scores_preserve_leading_axes() -> None:
    torch = pytest.importorskip("torch")
    left = FactoredMatrix(
        torch.eye(2).repeat(2, 1, 1),
        torch.eye(2).repeat(2, 1, 1),
    )
    right = FactoredMatrix(
        torch.eye(2).repeat(3, 1, 1),
        torch.eye(2).repeat(3, 1, 1),
    )

    scores = composition_scores(left, right)

    assert isinstance(scores, torch.Tensor)
    assert torch.allclose(
        scores,
        torch.full((2, 3), 0.7071067811865475),
    )


def test_kv_cache_appends_sequence_axis() -> None:
    entry = KeyValueCacheEntry(keys=[[[1], [2]]], values=[[[10], [20]]])
    updated_keys, updated_values = entry.append([[[3]]], [[[30]]])

    assert entry.sequence_length == 3
    assert updated_keys == entry.past_keys
    assert updated_values == entry.past_values
    assert entry.to_dict() == {
        "keys": [[[1], [2], [3]]],
        "values": [[[10], [20], [30]]],
        "sequence_length": 3,
    }

    cache = KeyValueCache()
    cache.append(0, [[[1]]], [[[2]]])
    cache.append(0, [[[3]]], [[[4]]])

    assert cache[0].keys == [[[1], [3]]]
    assert cache.to_dict()[0]["sequence_length"] == 2


def test_kv_cache_accepts_tuple_backed_entries() -> None:
    entry = KeyValueCacheEntry(keys=(((1,), (2,)),), values=(((10,), (20,)),))

    assert entry.sequence_length == 2

    entry.append(((((3,),),)), (((30,),),))

    assert entry.sequence_length == 3
    assert entry.to_dict() == {
        "keys": [[(1,), (2,), (3,)]],
        "values": [[(10,), (20,), (30,)]],
        "sequence_length": 3,
    }


def test_kv_cache_preserves_numpy_arrays_when_appending() -> None:
    np = pytest.importorskip("numpy")
    entry = KeyValueCacheEntry(
        keys=np.array([[[1], [2]]]),
        values=np.array([[[10], [20]]]),
    )

    entry.append(np.array([[[3]]]), np.array([[[30]]]))

    assert isinstance(entry.keys, np.ndarray)
    assert isinstance(entry.values, np.ndarray)
    assert entry.sequence_length == 3
    assert entry.keys.tolist() == [[[1], [2], [3]]]
    assert entry.values.tolist() == [[[10], [20], [30]]]


def test_kv_cache_entry_matches_transformerlens_aliases_and_freeze() -> None:
    torch = pytest.importorskip("torch")
    entry = KeyValueCacheEntry(
        past_keys=torch.zeros(1, 5, 2, 3),
        past_values=torch.ones(1, 5, 2, 3),
    )

    assert entry.keys is entry.past_keys
    assert entry.values is entry.past_values
    assert entry.sequence_length == 5

    replacement_keys = torch.full((1, 4, 2, 3), 2.0)
    replacement_values = torch.full((1, 4, 2, 3), 3.0)
    entry.past_keys = replacement_keys
    entry.past_values = replacement_values

    assert entry.keys is replacement_keys
    assert entry.values is replacement_values
    assert entry.sequence_length == 4

    entry.frozen = True
    updated_keys, updated_values = entry.append(
        torch.full((1, 1, 2, 3), 4.0),
        torch.full((1, 1, 2, 3), 5.0),
    )

    assert updated_keys.shape == (1, 5, 2, 3)
    assert updated_values.shape == (1, 5, 2, 3)
    assert entry.keys is replacement_keys
    assert entry.values is replacement_values


def test_kv_cache_init_cache_attention_mask_and_freeze_match_transformerlens() -> None:
    torch = pytest.importorskip("torch")

    class _Cfg:
        n_layers = 2
        n_heads = 3
        n_key_value_heads = None
        d_head = 4
        dtype = torch.float16
        device = "cpu"

    cache = KeyValueCache.init_cache(_Cfg(), device="cpu", batch_size=2)

    assert len(cache.entries) == 2
    assert cache[0].past_keys.shape == (2, 0, 3, 4)
    assert cache[0].past_keys.dtype is torch.float16
    assert cache[1].past_values.shape == (2, 0, 3, 4)
    assert cache.previous_attention_mask.shape == (2, 0)
    assert cache.previous_attention_mask.dtype is torch.int

    first_mask = torch.tensor([[1, 1], [1, 0]], dtype=torch.int64)
    full_mask = cache.append_attention_mask(first_mask)
    expected_first_mask = first_mask.to(dtype=cache.previous_attention_mask.dtype)

    assert torch.equal(full_mask, expected_first_mask)
    assert torch.equal(cache.previous_attention_mask, expected_first_mask)

    cache.freeze()
    assert cache.frozen is True
    assert cache[0].frozen is True
    second_mask = torch.tensor([[1], [1]], dtype=torch.int64)
    frozen_mask = cache.append_attention_mask(second_mask)

    assert frozen_mask.shape == (2, 3)
    assert torch.equal(cache.previous_attention_mask, expected_first_mask)

    cache.unfreeze()
    assert cache.frozen is False
    assert cache[0].frozen is False
    updated_mask = cache.append_attention_mask(second_mask)

    assert updated_mask.shape == (2, 3)
    assert torch.equal(cache.previous_attention_mask, updated_mask)


def test_kv_cache_appends_list_attention_masks_along_last_axis() -> None:
    cache = KeyValueCache()

    assert cache.append_attention_mask([[1, 1], [1, 0]]) == [[1, 1], [1, 0]]
    assert cache.append_attention_mask([[1], [1]]) == [[1, 1, 1], [1, 0, 1]]


def test_logit_loss_and_token_helpers() -> None:
    probs = softmax([0.0, 0.0])
    log_probs = logits_to_log_probs([[0.0, 0.0]], [1])
    same_token_log_probs = logits_to_log_probs([[0.0, 2.0, 0.0], [0.0, 0.0, 3.0]], 1)

    assert probs == [0.5, 0.5]
    assert math.isclose(log_probs[0], -math.log(2.0))
    assert len(same_token_log_probs) == 2
    assert math.isclose(
        same_token_log_probs[0],
        2.0 - math.log(math.exp(0.0) + math.exp(2.0) + math.exp(0.0)),
    )
    assert math.isclose(
        same_token_log_probs[1],
        0.0 - math.log(math.exp(0.0) + math.exp(0.0) + math.exp(3.0)),
    )
    assert math.isclose(cross_entropy_loss([[0.0, 0.0]], [1]), math.log(2.0))
    assert topk_tokens([0.1, 0.9, 0.3], k=2) == ([1, 2], [0.9, 0.3])
    assert topk_tokens([[0.1, 0.9, 0.3], [0.4, 0.2, 0.8]], k=1) == [
        ([1], [0.9]),
        ([2], [0.8]),
    ]
    assert logit_diff([[1.0, 4.0], [7.0, 2.0]], 0, 1, pos=-1) == 5.0
    assert logit_diff([[[1.0, 4.0], [7.0, 2.0]]], 0, 1, pos=-1) == 5.0


def test_topk_tokens_clamps_k_to_vocab_size_across_backends() -> None:
    indices, values = topk_tokens([1, 2], k=5)

    assert indices == [1, 0]
    assert values == [2, 1]

    torch = pytest.importorskip("torch")
    torch_indices, torch_values = topk_tokens(torch.tensor([[1.0, 2.0]]), k=5)

    assert torch.equal(torch_indices, torch.tensor([[1, 0]]))
    assert torch.equal(torch_values, torch.tensor([[2.0, 1.0]]))


def test_topk_tokens_clamps_numpy_k_to_vocab_size() -> None:
    np = pytest.importorskip("numpy")

    indices, values = topk_tokens(np.array([[1.0, 2.0]]), k=5)

    assert np.array_equal(indices, np.array([[1, 0]]))
    assert np.array_equal(values, np.array([[2.0, 1.0]]))


def test_topk_tokens_rejects_negative_k() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        topk_tokens([1, 2], k=-1)


def test_logits_to_df_sorts_probabilities_and_decodes_tokens() -> None:
    pandas = pytest.importorskip("pandas")

    class _Tokenizer:
        def decode(self, tokens: list[int]) -> str:
            return {0: "zero", 1: "one", 2: "two"}[tokens[0]]

    frame = logits_to_df([0.0, 3.0, 1.0], tokenizer=_Tokenizer(), top_k=2)

    assert isinstance(frame, pandas.DataFrame)
    assert frame["token_index"].tolist() == [1, 2]
    assert frame["token_string"].tolist() == ["one", "two"]
    assert frame["logit"].tolist() == [3.0, 1.0]
    assert frame["probability"].iloc[0] > frame["probability"].iloc[1]


def test_sample_logits_python_greedy_applies_penalties_and_filters() -> None:
    assert sample_logits([[0.0, 2.0, 1.0]], temperature=0.0) == [1]
    assert sample_logits(
        [[0.0, 2.0, 1.9]],
        temperature=0.0,
        repetition_penalty=2.0,
        tokens=[[1]],
    ) == [2]
    assert sample_logits(
        [[0.0, 2.0, 1.9]],
        temperature=0.0,
        freq_penalty=2.0,
        tokens=[[1]],
    ) == [1]


def test_sample_logits_torch_matches_transformerlens_controls() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[0.0, 2.0, 1.9]])

    greedy = sample_logits(logits, temperature=0.0)
    penalized = sample_logits(
        logits,
        temperature=0.0,
        repetition_penalty=2.0,
        tokens=torch.tensor([[1]]),
    )

    assert torch.equal(greedy, torch.tensor([1]))
    assert torch.equal(penalized, torch.tensor([2]))
    with pytest.raises(AssertionError, match="top_k"):
        sample_logits(logits, top_k=0)
    with pytest.raises(AssertionError, match="top_p"):
        sample_logits(logits, top_p=1.5)


def test_sample_logits_torch_accepts_sequence_token_history_for_penalties(monkeypatch: Any) -> None:
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")
    logits = torch.tensor([[0.0, 2.0, 1.9]])

    list_penalized = sample_logits(
        logits,
        temperature=0.0,
        repetition_penalty=2.0,
        tokens=[[1]],
    )
    numpy_penalized = sample_logits(
        logits,
        temperature=0.0,
        repetition_penalty=2.0,
        tokens=np.array([[1]]),
    )
    vector_penalized = sample_logits(
        torch.tensor([0.0, 2.0, 1.9]),
        temperature=0.0,
        repetition_penalty=2.0,
        tokens=[1],
    )

    monkeypatch.setattr(
        torch.distributions.categorical.Categorical,
        "sample",
        lambda self: self.logits.argmax(dim=-1),
    )
    list_frequency_penalized = sample_logits(
        logits,
        temperature=1.0,
        freq_penalty=3.0,
        tokens=[[1]],
    )
    numpy_frequency_penalized = sample_logits(
        logits,
        temperature=1.0,
        freq_penalty=3.0,
        tokens=np.array([[1]]),
    )

    assert torch.equal(list_penalized, torch.tensor([2]))
    assert torch.equal(numpy_penalized, torch.tensor([2]))
    assert torch.equal(vector_penalized, torch.tensor(2))
    assert torch.equal(list_frequency_penalized, torch.tensor([2]))
    assert torch.equal(numpy_frequency_penalized, torch.tensor([2]))


def test_sample_logits_torch_clamps_top_k_to_vocab_size(monkeypatch: Any) -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[0.0, 1.0, 2.0]])

    monkeypatch.setattr(
        torch.distributions.categorical.Categorical,
        "sample",
        lambda self: self.logits.argmax(dim=-1),
    )

    assert torch.equal(sample_logits(logits, top_k=10), torch.tensor([2]))


def test_sample_logits_torch_penalties_ignore_invalid_token_history(monkeypatch: Any) -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[0.0, 2.0, 1.9]])
    token_history = torch.tensor([[-100, 1, 99]])

    monkeypatch.setattr(
        torch.distributions.categorical.Categorical,
        "sample",
        lambda self: self.logits.argmax(dim=-1),
    )

    repetition_penalized = sample_logits(
        logits,
        temperature=0.0,
        repetition_penalty=2.0,
        tokens=token_history,
    )
    frequency_penalized = sample_logits(
        logits,
        freq_penalty=3.0,
        tokens=token_history,
    )

    assert torch.equal(repetition_penalized, torch.tensor([2]))
    assert torch.equal(frequency_penalized, torch.tensor([2]))


def test_sample_logits_torch_promotes_integer_logits_for_penalties() -> None:
    torch = pytest.importorskip("torch")

    sample = sample_logits(
        torch.tensor([[0, 2, 3]]),
        temperature=0.0,
        repetition_penalty=2.0,
        tokens=torch.tensor([[2]]),
    )

    assert torch.equal(sample, torch.tensor([1]))


def test_sample_logits_python_top_p_keeps_only_first_token_when_it_exceeds_threshold(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(analysis.random, "random", lambda: 0.999999)

    assert analysis.sample_logits([[10.0, 0.0, -10.0]], top_p=0.5) == [0]


def test_sample_logits_rejects_invalid_sampling_controls() -> None:
    logits = [[0.0, 1.0]]

    with pytest.raises(AssertionError, match="temperature"):
        sample_logits(logits, temperature=-0.1)
    with pytest.raises(AssertionError, match="freq_penalty"):
        sample_logits(logits, freq_penalty=-0.1)
    with pytest.raises(AssertionError, match="repetition_penalty"):
        sample_logits(logits, repetition_penalty=0.0)


def test_prompt_returns_structured_next_token_check() -> None:
    class _PromptModel:
        def __call__(self, prompt: str, *, return_type: str, prepend_bos: bool) -> Any:
            assert prompt == "The answer is"
            assert return_type == "logits"
            assert prepend_bos is False
            return [[[0.0, 1.0, 2.0], [0.0, 4.0, 1.0]]]

        def to_single_token(self, token: str) -> int:
            return {" yes": 1, " no": 2}[token]

        def to_single_str_token(self, token: int) -> str:
            return {0: "<bos>", 1: " yes", 2: " no"}[token]

    result = run_test_prompt(
        _PromptModel(),
        "The answer is",
        " yes",
        " no",
        prepend_bos=False,
        top_k=2,
    )

    assert result["correct_token_id"] == 1
    assert result["incorrect_token_id"] == 2
    assert result["predicted_token_id"] == 1
    assert result["predicted_token"] == " yes"
    assert result["is_correct"] is True
    assert result["logit_diff"] == 3.0
    assert result["top_tokens"] == [
        {"token_id": 1, "token": " yes", "logit": 4.0},
        {"token_id": 2, "token": " no", "logit": 1.0},
    ]


def test_prompt_accepts_tuple_backed_logits() -> None:
    class _PromptModel:
        def __call__(self, prompt: str, *, return_type: str, prepend_bos: bool) -> Any:
            assert prompt == "The answer is"
            assert return_type == "logits"
            assert prepend_bos is False
            return (((0.0, 1.0, 2.0), (0.0, 4.0, 1.0)),)

        def to_single_token(self, token: str) -> int:
            return {" yes": 1, " no": 2}[token]

        def to_single_str_token(self, token: int) -> str:
            return {0: "<bos>", 1: " yes", 2: " no"}[token]

    result = run_test_prompt(
        _PromptModel(),
        "The answer is",
        " yes",
        " no",
        prepend_bos=False,
        top_k=2,
    )

    assert result["predicted_token_id"] == 1
    assert result["logit_diff"] == 3.0
    assert result["top_tokens"] == [
        {"token_id": 1, "token": " yes", "logit": 4.0},
        {"token_id": 2, "token": " no", "logit": 1.0},
    ]


def test_prompt_accepts_transformerlens_argument_order_and_answer_ranks() -> None:
    torch = pytest.importorskip("torch")

    class _TLPromptModel:
        def to_tokens(self, text: Any, prepend_bos: bool | None = None) -> Any:
            mapping = {"<bos>": 0, "The": 1, " answer": 2, " road": 3, " car": 4}
            if isinstance(text, list):
                return torch.tensor([[mapping[item]] for item in text])
            tokens = (
                [mapping["The"], mapping[" answer"]] if text == "The answer" else [mapping[text]]
            )
            if prepend_bos:
                tokens = [mapping["<bos>"], *tokens]
            return torch.tensor([tokens])

        def to_str_tokens(self, text: Any, prepend_bos: bool | None = None) -> list[str]:
            if isinstance(text, list):
                return [self.to_str_tokens(item, prepend_bos=prepend_bos)[0] for item in text]
            if text == "The answer":
                tokens = ["The", " answer"]
                return ["<bos>", *tokens] if prepend_bos else tokens
            if text.startswith(" "):
                return [text]
            return [f" {text}"]

        def to_string(self, token: Any) -> str:
            item = int(
                token.item()
                if hasattr(token, "item")
                else token[0]
                if isinstance(token, list)
                else token
            )
            return {0: "<bos>", 1: "The", 2: " answer", 3: " road", 4: " car"}[item]

        def __call__(self, tokens: Any) -> Any:
            logits = torch.zeros(tokens.shape[0], tokens.shape[1], 5)
            logits[:, -2, 3] = 5.0
            logits[:, -2, 4] = 1.0
            return logits

    result = run_test_prompt(
        "The answer",
        "road",
        _TLPromptModel(),
        print_details=False,
        prepend_bos=False,
        top_k=2,
    )

    assert result["prompt_str_tokens"] == ["The", " answer"]
    assert result["answer_str_tokens"] == [[" road"]]
    assert result["answer_ranks"] == [(" road", 0)]
    assert result["token_results"][0]["top_tokens"][0]["token"] == " road"
    assert result["is_correct"] is True


def test_prompt_transformerlens_order_returns_all_single_answer_token_ranks() -> None:
    torch = pytest.importorskip("torch")

    class _MultiTokenAnswerModel:
        def to_tokens(self, text: Any, prepend_bos: bool | None = None) -> Any:
            mapping = {"Q": 1, " red": 2, " car": 3, " blue": 4}
            if isinstance(text, list):
                return torch.tensor(
                    [
                        [mapping[" red"], mapping[" car"]]
                        if item == " red car"
                        else [mapping[item]]
                        for item in text
                    ]
                )
            if text == "Q":
                return torch.tensor([[mapping["Q"]]])
            if text == " red car":
                return torch.tensor([[mapping[" red"], mapping[" car"]]])
            raise KeyError(text)

        def to_str_tokens(self, text: Any, prepend_bos: bool | None = None) -> list[str]:
            if text == "Q":
                return ["Q"]
            if text == " red car":
                return [" red", " car"]
            raise KeyError(text)

        def to_string(self, token: Any) -> str:
            item = int(token.item() if hasattr(token, "item") else token)
            return {1: "Q", 2: " red", 3: " car", 4: " blue"}[item]

        def __call__(self, tokens: Any) -> Any:
            logits = torch.zeros(tokens.shape[0], tokens.shape[1], 5)
            logits[:, 0, 2] = 5.0
            logits[:, 0, 4] = 4.0
            logits[:, 1, 3] = 6.0
            logits[:, 1, 4] = 1.0
            return logits

    result = run_test_prompt(
        "Q",
        "red car",
        _MultiTokenAnswerModel(),
        print_details=False,
        prepend_bos=False,
        top_k=2,
    )

    assert result["answer_str_tokens"] == [[" red", " car"]]
    assert result["answer_ranks"] == [(" red", 0), (" car", 0)]
    assert [item["answer_tokens"] for item in result["token_results"]] == [[" red"], [" car"]]
    assert result["is_correct"] is True


def test_prompt_transformerlens_order_supports_multiple_answers() -> None:
    torch = pytest.importorskip("torch")

    class _MultiAnswerModel:
        def to_tokens(self, text: Any, prepend_bos: bool | None = None) -> Any:
            mapping = {"Q": 1, " yes": 2, " no": 3}
            if isinstance(text, list):
                return torch.tensor([[mapping[item]] for item in text])
            return torch.tensor([[mapping[text]]])

        def to_str_tokens(self, text: Any, prepend_bos: bool | None = None) -> list[str]:
            if isinstance(text, list):
                return [self.to_str_tokens(item, prepend_bos=prepend_bos)[0] for item in text]
            return [text if text.startswith(" ") else f" {text}" if text != "Q" else text]

        def to_string(self, token: Any) -> str:
            item = int(token.item() if hasattr(token, "item") else token)
            return {1: "Q", 2: " yes", 3: " no"}[item]

        def __call__(self, tokens: Any) -> Any:
            logits = torch.zeros(tokens.shape[0], tokens.shape[1], 4)
            logits[:, 0, 2] = 3.0
            logits[:, 0, 3] = 5.0
            return logits

    result = run_test_prompt(
        "Q",
        ["yes", "no"],
        _MultiAnswerModel(),
        print_details=False,
        prepend_bos=False,
        top_k=2,
    )

    assert result["answers"] == [" yes", " no"]
    assert result["answer_ranks"] == [[(" yes", 1), (" no", 0)]]
    assert result["is_correct"] is False


def test_prompt_transformerlens_order_records_top_tokens_for_each_answer_row() -> None:
    torch = pytest.importorskip("torch")

    class _MultiAnswerTopKModel:
        def to_tokens(self, text: Any, prepend_bos: bool | None = None) -> Any:
            mapping = {"Q": 1, " yes": 2, " no": 3}
            if isinstance(text, list):
                return torch.tensor([[mapping[item]] for item in text])
            return torch.tensor([[mapping[text]]])

        def to_str_tokens(self, text: Any, prepend_bos: bool | None = None) -> list[str]:
            if isinstance(text, list):
                return [self.to_str_tokens(item, prepend_bos=prepend_bos)[0] for item in text]
            return [text if text == "Q" else text if text.startswith(" ") else f" {text}"]

        def to_string(self, token: Any) -> str:
            item = int(token.item() if hasattr(token, "item") else token)
            return {1: "Q", 2: " yes", 3: " no"}[item]

        def __call__(self, tokens: Any) -> Any:
            logits = torch.zeros(tokens.shape[0], tokens.shape[1], 4)
            logits[0, 0, 2] = 5.0
            logits[0, 0, 3] = 1.0
            logits[1, 0, 2] = 1.0
            logits[1, 0, 3] = 5.0
            return logits

    result = run_test_prompt(
        "Q",
        ["yes", "no"],
        _MultiAnswerTopKModel(),
        print_details=False,
        prepend_bos=False,
        top_k=1,
    )

    token_result = result["token_results"][0]
    assert token_result["top_tokens"][0]["token_id"] == 2
    assert [top_tokens[0]["token_id"] for top_tokens in token_result["top_tokens_by_answer"]] == [
        2,
        3,
    ]


def test_prompt_transformerlens_order_prints_details_by_default(capsys: Any) -> None:
    torch = pytest.importorskip("torch")

    class _TLPromptModel:
        def to_tokens(self, text: Any, prepend_bos: bool | None = None) -> Any:
            mapping = {"Q": 1, " yes": 2}
            if isinstance(text, list):
                return torch.tensor([[mapping[item]] for item in text])
            return torch.tensor([[mapping[text]]])

        def to_str_tokens(self, text: Any, prepend_bos: bool | None = None) -> list[str]:
            if isinstance(text, list):
                return [self.to_str_tokens(item, prepend_bos=prepend_bos)[0] for item in text]
            return [text if text == "Q" else text if text.startswith(" ") else f" {text}"]

        def to_string(self, token: Any) -> str:
            item = int(token.item() if hasattr(token, "item") else token)
            return {1: "Q", 2: " yes"}[item]

        def __call__(self, tokens: Any) -> Any:
            logits = torch.zeros(tokens.shape[0], tokens.shape[1], 3)
            logits[:, 0, 2] = 4.0
            return logits

    result = run_test_prompt("Q", "yes", _TLPromptModel(), prepend_bos=False)

    printed = capsys.readouterr().out
    assert result["answer_ranks"] == [(" yes", 0)]
    assert "Answer token at position 1" in printed
    assert "' yes'" in printed


def test_causal_lm_log_probs_and_loss_shift_targets() -> None:
    logits = [
        [
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 3.0],
            [4.0, 0.0, 0.0],
        ]
    ]
    tokens = [[0, 1, 2]]
    expected_log_probs = [
        [
            2.0 - math.log(math.exp(0.0) + math.exp(2.0) + math.exp(0.0)),
            3.0 - math.log(math.exp(0.0) + math.exp(0.0) + math.exp(3.0)),
        ]
    ]

    actual_log_probs = lm_log_probs(logits, tokens)

    assert math.isclose(actual_log_probs[0][0], expected_log_probs[0][0])
    assert math.isclose(actual_log_probs[0][1], expected_log_probs[0][1])
    assert math.isclose(
        lm_cross_entropy_loss(logits, tokens),
        -sum(expected_log_probs[0]) / 2,
    )
    per_token_loss = lm_cross_entropy_loss(logits, tokens, per_token=True)
    assert math.isclose(per_token_loss[0][0], -expected_log_probs[0][0])
    assert math.isclose(per_token_loss[0][1], -expected_log_probs[0][1])
    assert lm_accuracy(logits, tokens) == 1.0
    assert lm_accuracy(logits, tokens, per_token=True) == [[1.0, 1.0]]


def test_causal_lm_metrics_accept_tuple_token_and_mask_inputs() -> None:
    logits = (
        (
            (0.0, 4.0),
            (5.0, 0.0),
            (0.0, 5.0),
        ),
    )
    tokens = ((0, 1, 0),)
    attention_mask = ((1, 1, 0),)
    first_log_prob = 4.0 - math.log(math.exp(0.0) + math.exp(4.0))

    log_probs = lm_log_probs(logits, tokens, attention_mask)

    assert math.isclose(log_probs[0][0], first_log_prob)
    assert log_probs[0][1] is None
    assert math.isclose(lm_cross_entropy_loss(logits, tokens, attention_mask), -first_log_prob)
    assert lm_accuracy(logits, tokens, attention_mask) == 1.0


def test_causal_lm_loss_masks_padding_boundaries() -> None:
    logits = [
        [
            [0.0, 4.0],
            [5.0, 0.0],
            [0.0, 5.0],
        ]
    ]
    tokens = [[0, 1, 0]]
    attention_mask = [[1, 1, 0]]
    first_log_prob = 4.0 - math.log(math.exp(0.0) + math.exp(4.0))

    actual_log_probs = lm_log_probs(logits, tokens, attention_mask)

    assert math.isclose(actual_log_probs[0][0], first_log_prob)
    assert actual_log_probs[0][1] is None
    assert math.isclose(
        lm_cross_entropy_loss(logits, tokens, attention_mask),
        -first_log_prob,
    )
    per_token_loss = lm_cross_entropy_loss(logits, tokens, attention_mask, per_token=True)
    assert math.isclose(per_token_loss[0][0], -first_log_prob)
    assert per_token_loss[0][1] == 0.0
    assert lm_accuracy(logits, tokens, attention_mask) == 1.0
    assert lm_accuracy(logits, tokens, attention_mask, per_token=True) == [[1.0, None]]


def test_causal_lm_metrics_return_nan_when_mask_has_no_valid_targets() -> None:
    logits = [
        [
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
        ]
    ]
    tokens = [[0, 1, 0]]
    attention_mask = [[0, 0, 0]]

    assert lm_cross_entropy_loss(logits, tokens, attention_mask, per_token=True) == [[0.0, 0.0]]
    assert math.isnan(lm_cross_entropy_loss(logits, tokens, attention_mask))
    assert math.isnan(lm_accuracy(logits, tokens, attention_mask))
    assert lm_accuracy(logits, tokens, attention_mask, per_token=True) == [[None, None]]


def test_causal_lm_metrics_return_nan_when_sequence_has_no_targets() -> None:
    logits = [[[0.0, 0.0]]]
    tokens = [[0]]

    assert lm_log_probs(logits, tokens) == [[]]
    assert lm_cross_entropy_loss(logits, tokens, per_token=True) == [[]]
    assert math.isnan(lm_cross_entropy_loss(logits, tokens))
    assert math.isnan(lm_accuracy(logits, tokens))


def test_causal_lm_loss_matches_torch_cross_entropy() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor(
        [
            [
                [0.0, 2.0, 0.0],
                [0.0, 0.0, 3.0],
                [4.0, 0.0, 0.0],
            ]
        ]
    )
    tokens = torch.tensor([[0, 1, 2]])
    expected = torch.nn.functional.cross_entropy(
        logits[:, :-1].reshape(-1, 3),
        tokens[:, 1:].reshape(-1),
    )

    expected_log_probs = (
        torch.log_softmax(logits[:, :-1], dim=-1)
        .gather(
            -1,
            tokens[:, 1:].unsqueeze(-1),
        )
        .squeeze(-1)
    )

    assert torch.allclose(lm_log_probs(logits, tokens), expected_log_probs)
    assert math.isclose(lm_cross_entropy_loss(logits, tokens), float(expected), rel_tol=1e-6)
    assert lm_accuracy(logits, tokens) == 1.0


def test_causal_lm_loss_accepts_torch_logits_with_python_token_lists() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor(
        [
            [
                [0.0, 2.0, 0.0],
                [0.0, 0.0, 3.0],
                [4.0, 0.0, 0.0],
            ]
        ]
    )
    tokens = [[0, 1, 2]]
    expected = torch.nn.functional.cross_entropy(
        logits[:, :-1].reshape(-1, 3),
        torch.tensor(tokens)[:, 1:].reshape(-1),
    )

    assert math.isclose(lm_cross_entropy_loss(logits, tokens), float(expected), rel_tol=1e-6)
    assert lm_cross_entropy_loss(logits, tokens) > 0


def test_causal_lm_metrics_accept_torch_logits_with_python_masks() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor(
        [
            [
                [0.0, 4.0],
                [5.0, 0.0],
                [0.0, 5.0],
            ]
        ]
    )
    tokens = [[0, 1, 0]]
    attention_mask = [[1, 1, 0]]
    first_log_prob = 4.0 - math.log(math.exp(0.0) + math.exp(4.0))

    log_probs = lm_log_probs(logits, tokens, attention_mask)

    assert torch.allclose(
        log_probs,
        torch.tensor([[first_log_prob, float("nan")]]),
        equal_nan=True,
    )
    assert math.isclose(
        lm_cross_entropy_loss(logits, tokens, attention_mask),
        -first_log_prob,
        rel_tol=1e-6,
        abs_tol=1e-6,
    )
    assert lm_accuracy(logits, tokens, attention_mask) == 1.0


def test_causal_lm_torch_metrics_return_nan_when_mask_has_no_valid_targets() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.zeros(1, 3, 2)
    tokens = torch.tensor([[0, 1, 0]])
    attention_mask = torch.zeros(1, 3, dtype=torch.long)

    per_token_loss = lm_cross_entropy_loss(logits, tokens, attention_mask, per_token=True)

    assert torch.equal(per_token_loss, torch.zeros(1, 2))
    assert math.isnan(lm_cross_entropy_loss(logits, tokens, attention_mask))
    assert math.isnan(lm_accuracy(logits, tokens, attention_mask))
    assert torch.isnan(lm_accuracy(logits, tokens, attention_mask, per_token=True)).all()


def test_causal_lm_torch_metrics_return_nan_when_sequence_has_no_targets() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.zeros(1, 1, 2)
    tokens = torch.tensor([[0]])

    assert lm_log_probs(logits, tokens).shape == (1, 0)
    assert lm_cross_entropy_loss(logits, tokens, per_token=True).shape == (1, 0)
    assert math.isnan(lm_cross_entropy_loss(logits, tokens))
    assert math.isnan(lm_accuracy(logits, tokens))


def test_numpy_logit_helpers_preserve_array_backend() -> None:
    np = pytest.importorskip("numpy")
    logits = np.array([[0.0, 1.0, 2.0], [3.0, 0.0, 1.0]])

    probs = softmax(logits)
    indices, values = topk_tokens(logits, k=2)

    assert np.allclose(probs.sum(axis=-1), np.ones(2))
    assert np.array_equal(indices, np.array([[2, 1], [0, 2]]))
    assert np.array_equal(values, np.array([[2.0, 1.0], [3.0, 1.0]]))


def test_numpy_logit_helpers_gather_token_log_probs_on_last_dim() -> None:
    np = pytest.importorskip("numpy")
    logits = np.array([[0.0, 2.0, 0.0], [0.0, 0.0, 3.0]])
    tokens = np.array([1, 2])

    log_probs = logits_to_log_probs(logits, tokens)
    same_token_log_probs = logits_to_log_probs(logits, 1)

    expected = np.array(
        [
            2.0 - math.log(math.exp(0.0) + math.exp(2.0) + math.exp(0.0)),
            3.0 - math.log(math.exp(0.0) + math.exp(0.0) + math.exp(3.0)),
        ]
    )
    same_token_expected = np.array(
        [
            2.0 - math.log(math.exp(0.0) + math.exp(2.0) + math.exp(0.0)),
            0.0 - math.log(math.exp(0.0) + math.exp(0.0) + math.exp(3.0)),
        ]
    )
    assert np.allclose(log_probs, expected)
    assert np.allclose(same_token_log_probs, same_token_expected)
    assert math.isclose(cross_entropy_loss(logits, tokens), float(-expected.mean()))


def test_torch_logit_helpers_gather_scalar_token_on_last_dim() -> None:
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[0.0, 2.0, 0.0], [0.0, 0.0, 3.0]])

    log_probs = logits_to_log_probs(logits, 1)
    expected = torch.log_softmax(logits, dim=-1)[..., 1]

    assert torch.allclose(log_probs, expected)


def test_causal_lm_metrics_accept_numpy_logits_and_masks() -> None:
    np = pytest.importorskip("numpy")
    logits = np.array(
        [
            [
                [0.0, 4.0],
                [5.0, 0.0],
                [0.0, 5.0],
            ]
        ]
    )
    tokens = np.array([[0, 1, 0]])
    attention_mask = np.array([[1, 1, 0]])
    first_log_prob = 4.0 - math.log(math.exp(0.0) + math.exp(4.0))

    log_probs = lm_log_probs(logits, tokens, attention_mask)

    assert np.allclose(log_probs, np.array([[first_log_prob, np.nan]]), equal_nan=True)
    assert math.isclose(lm_cross_entropy_loss(logits, tokens, attention_mask), -first_log_prob)
    assert lm_accuracy(logits, tokens, attention_mask) == 1.0


def test_causal_lm_numpy_metrics_return_nan_when_mask_has_no_valid_targets() -> None:
    np = pytest.importorskip("numpy")
    logits = np.zeros((1, 3, 2))
    tokens = np.array([[0, 1, 0]])
    attention_mask = np.zeros((1, 3), dtype=int)

    per_token_loss = lm_cross_entropy_loss(logits, tokens, attention_mask, per_token=True)

    assert np.array_equal(per_token_loss, np.zeros((1, 2)))
    assert math.isnan(lm_cross_entropy_loss(logits, tokens, attention_mask))
    assert math.isnan(lm_accuracy(logits, tokens, attention_mask))
    assert np.isnan(lm_accuracy(logits, tokens, attention_mask, per_token=True)).all()


def test_numpy_ablation_hooks_preserve_activation_shape() -> None:
    np = pytest.importorskip("numpy")
    activation = np.array([[1.0, 3.0], [5.0, 7.0]])

    zeroed = zero_ablation_hook(activation)
    meaned = mean_ablation_hook(activation)

    assert np.array_equal(zeroed, np.zeros_like(activation))
    assert np.array_equal(meaned, np.full_like(activation, 4.0))


def test_residual_projection_and_ablation_hooks() -> None:
    assert residual_stack_to_logits([[1, 2], [3, 4]], [[1], [2]]) == [
        [5.0],
        [11.0],
    ]
    assert direct_logit_attribution([[1, 2], [3, 4]], [[10, 1], [1, 10]]) == [
        12.0,
        43.0,
    ]
    assert zero_ablation_hook([1, [2, 3]]) == [0, [0, 0]]
    assert mean_ablation_hook([1, 3, 5]) == [3.0, 3.0, 3.0]

    replacement_hook = replace_activation_hook({"x": [1]})
    replaced: dict[str, Any] = replacement_hook({"x": [0]}, None)
    replaced["x"].append(2)

    assert replacement_hook({"x": [0]}, None) == {"x": [1]}


def test_tuple_backed_logit_lens_helpers_match_list_semantics() -> None:
    logits = ((0.1, 0.9, 0.3), (0.4, 0.2, 0.8))
    residual_stack = (
        (((1, 2), (3, 4)),),
        (((10, 20), (30, 40)),),
    )
    token_directions = (((1, 0), (0, 1)),)

    assert topk_tokens(logits, k=1) == [([1], [0.9]), ([2], [0.8])]
    assert logit_diff(((1.0, 4.0), (7.0, 2.0)), 0, 1, pos=-1) == 5.0
    assert residual_stack_to_logits(residual_stack, ((1, 0, 1), (0, 1, 1))) == [
        [[[1.0, 2.0, 3.0], [3.0, 4.0, 7.0]]],
        [[[10.0, 20.0, 30.0], [30.0, 40.0, 70.0]]],
    ]
    assert direct_logit_attribution(residual_stack, token_directions) == [
        [[1.0, 4.0]],
        [[10.0, 40.0]],
    ]


def test_attention_pattern_scores_preserve_leading_dimensions() -> None:
    pattern = [
        [
            [
                [0.0, 0.0, 0.0],
                [0.8, 0.0, 0.0],
                [0.0, 0.6, 0.0],
            ],
            [
                [0.0, 0.0, 0.0],
                [0.7, 0.0, 0.0],
                [0.0, 0.0, 0.0],
            ],
        ]
    ]

    assert previous_token_attention_score(pattern) == [[0.7, 0.35]]
    assert induction_attention_score(pattern) == [[0.7, 0.35]]
    assert attention_pattern_score(pattern, offset=1) == [[0.0, 0.0]]
    assert attention_pattern_score(pattern, offset=-1, min_dest_pos=2) == [[0.6, 0.0]]


def test_induction_attention_score_uses_causal_previous_diagonal() -> None:
    pattern = [
        [
            [
                [0.0, 0.0, 0.0, 0.0],
                [0.9, 0.0, 0.0, 0.0],
                [0.0, 0.8, 0.0, 0.0],
                [0.0, 0.0, 0.7, 0.0],
            ]
        ]
    ]

    assert_nested_close(induction_attention_score(pattern), [[0.8]])
    assert attention_pattern_score(pattern, offset=1) == [[0.0]]


def test_induction_attention_score_can_target_repeated_sequence_length() -> None:
    pattern = [
        [
            [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.95, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.85, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.75, 0.0, 0.0],
            ]
        ]
    ]

    assert_nested_close(induction_attention_score(pattern, repeat_length=3), [[0.85]])
    with pytest.raises(ValueError, match="repeat_length"):
        induction_attention_score(pattern, repeat_length=1)


def test_attention_pattern_scores_accept_numpy_and_torch_patterns() -> None:
    np = pytest.importorskip("numpy")
    pattern = np.array(
        [
            [
                [
                    [0.0, 0.0, 0.0],
                    [0.4, 0.0, 0.0],
                    [0.0, 0.8, 0.0],
                ]
            ]
        ]
    )

    assert np.allclose(previous_token_attention_score(pattern), np.array([[0.6]]))
    assert np.allclose(induction_attention_score(pattern), np.array([[0.6]]))

    torch = pytest.importorskip("torch")
    torch_pattern = torch.as_tensor(pattern)
    torch_score = previous_token_attention_score(torch_pattern)
    torch_induction_score = induction_attention_score(torch_pattern)

    assert tuple(torch_score.shape) == (1, 1)
    assert torch.allclose(torch_score, torch.tensor([[0.6]], dtype=torch_pattern.dtype))
    assert torch.allclose(
        torch_induction_score,
        torch.tensor([[0.6]], dtype=torch_pattern.dtype),
    )


def test_head_detection_patterns_match_transformerlens_semantics() -> None:
    tokens = [[0, 1, 2, 1, 3, 2]]

    assert HEAD_NAMES == (
        "previous_token_head",
        "duplicate_token_head",
        "induction_head",
    )
    assert get_supported_heads() == list(HEAD_NAMES)
    assert get_previous_token_head_detection_pattern(tokens) == [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    ]
    assert get_duplicate_token_head_detection_pattern(tokens) == [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    ]
    assert get_induction_head_detection_pattern(tokens) == [
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    ]


def test_head_attention_similarity_scores_match_transformerlens_error_measures() -> None:
    attention_pattern = [
        [1.0, 0.0, 0.0, 0.0],
        [0.7, 0.3, 0.0, 0.0],
        [0.0, 0.8, 0.2, 0.0],
        [0.0, 0.0, 0.9, 0.1],
    ]
    detection_pattern = get_previous_token_head_detection_pattern([[0, 1, 2, 3]])

    assert math.isclose(
        compute_head_attention_similarity_score(
            attention_pattern,
            detection_pattern,
            exclude_bos=False,
            exclude_current_token=False,
            error_measure="mul",
        ),
        0.6,
    )
    assert math.isclose(
        compute_head_attention_similarity_score(
            attention_pattern,
            detection_pattern,
            exclude_bos=False,
            exclude_current_token=True,
            error_measure="mul",
        ),
        1.0,
    )
    assert math.isclose(
        compute_head_attention_similarity_score(
            attention_pattern,
            detection_pattern,
            exclude_bos=False,
            exclude_current_token=False,
            error_measure="abs",
        ),
        0.45,
    )
    with pytest.raises(ValueError, match="error_measure"):
        compute_head_attention_similarity_score(
            attention_pattern,
            detection_pattern,
            exclude_bos=False,
            exclude_current_token=False,
            error_measure="bad",
        )


def test_detect_head_scores_cached_attention_patterns_and_selected_heads() -> None:
    torch = pytest.importorskip("torch")

    class _Cfg:
        n_layers = 2
        n_heads = 2
        n_ctx = 16
        dtype = torch.float32
        device = "cpu"

    class _HeadDetectorModel:
        cfg = _Cfg()

    model = _HeadDetectorModel()
    tokens = torch.tensor([[0, 1, 2, 3]])
    previous = get_previous_token_head_detection_pattern(tokens)
    current = torch.eye(4)
    cache = ActivationCache(
        {
            "blocks.0.attn.hook_pattern": torch.stack([previous, current]),
            "blocks.1.attn.hook_pattern": torch.stack([current, previous]),
        },
        model=model,
        has_batch_dim=False,
    )

    scores = detect_head(model, tokens, "previous_token_head", cache=cache)

    assert tuple(scores.shape) == (2, 2)
    assert torch.allclose(scores, torch.tensor([[1.0, 0.0], [0.0, 1.0]]))

    selected = detect_head(
        model,
        tokens,
        "previous_token_head",
        heads=[(1, 1)],
        cache=cache,
    )

    assert torch.allclose(selected, torch.tensor([[-1.0, -1.0], [-1.0, 1.0]]))
    with pytest.raises(ValueError, match="detection_pattern"):
        detect_head(model, tokens, "not_a_head", cache=cache)


def test_detect_head_supports_duplicate_and_induction_patterns() -> None:
    torch = pytest.importorskip("torch")

    class _Cfg:
        n_layers = 1
        n_heads = 1
        n_ctx = 32
        dtype = torch.float32
        device = "cpu"

    class _HeadDetectorModel:
        cfg = _Cfg()

    model = _HeadDetectorModel()
    tokens = torch.tensor([[0, 1, 2, 1, 3, 2]])
    duplicate = get_duplicate_token_head_detection_pattern(tokens)
    induction = get_induction_head_detection_pattern(tokens)

    duplicate_scores = detect_head(
        model,
        tokens,
        "duplicate_token_head",
        cache=ActivationCache(
            {"layer_0.pattern": duplicate.unsqueeze(0)}, model=model, has_batch_dim=False
        ),
    )
    induction_scores = detect_head(
        model,
        tokens,
        "induction_head",
        cache=ActivationCache(
            {"layer_0.pattern": induction.unsqueeze(0)}, model=model, has_batch_dim=False
        ),
    )

    assert torch.allclose(duplicate_scores, torch.ones(1, 1))
    assert torch.allclose(induction_scores, torch.ones(1, 1))


def test_detect_head_runs_model_when_cache_is_not_supplied() -> None:
    torch = pytest.importorskip("torch")

    class _Cfg:
        n_layers = 1
        n_heads = 1
        n_ctx = 16
        dtype = torch.float32
        device = "cpu"

    class _HeadDetectorModel:
        cfg = _Cfg()

        def __init__(self) -> None:
            self.seen_tokens = None

        def to_tokens(self, seq: Any) -> Any:
            assert seq == "abcd"
            return torch.tensor([[0, 1, 2, 3]])

        def run_with_cache(self, tokens: Any, remove_batch_dim: bool = False) -> Any:
            self.seen_tokens = (tokens.clone(), remove_batch_dim)
            pattern = get_previous_token_head_detection_pattern(tokens).unsqueeze(0)
            cache = ActivationCache(
                {"blocks.0.attn.hook_pattern": pattern}, model=self, has_batch_dim=False
            )
            return torch.zeros(1), cache

    model = _HeadDetectorModel()

    scores = detect_head(model, "abcd", "previous_token_head")

    assert torch.allclose(scores, torch.ones(1, 1))
    assert model.seen_tokens is not None
    assert model.seen_tokens[1] is True


def test_detect_head_accepts_decoder_and_cross_attention_pattern_cache_names() -> None:
    torch = pytest.importorskip("torch")

    class _Cfg:
        n_layers = 1
        n_heads = 1
        n_ctx = 16
        dtype = torch.float32
        device = "cpu"

    class _HeadDetectorModel:
        cfg = _Cfg()

    model = _HeadDetectorModel()
    tokens = torch.tensor([[0, 1, 2, 3]])
    pattern = get_previous_token_head_detection_pattern(tokens).unsqueeze(0)

    for cache_key in (
        "decoder.0.attn.hook_pattern",
        "decoder.0.cross_attn.hook_pattern",
        "blocks.0.decoder_attn.hook_pattern",
        "blocks.0.cross_attn.hook_pattern",
        "layer_0.decoder_pattern",
        "layer_0.cross_pattern",
    ):
        scores = detect_head(
            model,
            tokens,
            "previous_token_head",
            cache=ActivationCache({cache_key: pattern}, model=model, has_batch_dim=False),
        )

        assert torch.allclose(scores, torch.ones(1, 1))


def test_residual_stack_to_logits_preserves_logit_lens_leading_axes() -> None:
    residual_stack = [
        [[[1, 2], [3, 4]]],
        [[[10, 20], [30, 40]]],
    ]
    unembed = [[1, 0, 1], [0, 1, 1]]

    assert residual_stack_to_logits(residual_stack, unembed) == [
        [[[1.0, 2.0, 3.0], [3.0, 4.0, 7.0]]],
        [[[10.0, 20.0, 30.0], [30.0, 40.0, 70.0]]],
    ]


def test_residual_stack_to_logits_can_add_unembed_bias() -> None:
    residual_stack = [
        [[[1, 2], [3, 4]]],
        [[[10, 20], [30, 40]]],
    ]
    unembed = ((1, 0, 1), (0, 1, 1))
    unembed_bias = (0.5, -1.0, 10.0)

    assert residual_stack_to_logits(residual_stack, unembed, unembed_bias) == [
        [[[1.5, 1.0, 13.0], [3.5, 3.0, 17.0]]],
        [[[10.5, 19.0, 40.0], [30.5, 39.0, 80.0]]],
    ]


def test_residual_stack_to_logits_adds_numpy_unembed_bias() -> None:
    np = pytest.importorskip("numpy")
    residual_stack = np.array([[[1.0, 2.0], [3.0, 4.0]]])
    unembed = [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]]
    unembed_bias = np.array([0.5, -1.0, 10.0])

    logits = residual_stack_to_logits(residual_stack, unembed, unembed_bias)

    assert isinstance(logits, np.ndarray)
    assert np.allclose(
        logits,
        np.array([[[1.5, 1.0, 13.0], [3.5, 3.0, 17.0]]]),
    )


def test_residual_stack_to_logits_adds_torch_unembed_bias() -> None:
    torch = pytest.importorskip("torch")
    residual_stack = torch.tensor([[[1.0, 2.0], [3.0, 4.0]]])
    unembed = [[1.0, 0.0, 1.0], [0.0, 1.0, 1.0]]
    unembed_bias = torch.tensor([0.5, -1.0, 10.0])

    logits = residual_stack_to_logits(residual_stack, unembed, unembed_bias)

    assert torch.allclose(
        logits,
        torch.tensor([[[1.5, 1.0, 13.0], [3.5, 3.0, 17.0]]]),
    )


def test_residual_stack_to_logits_coerces_bias_to_tensor_backend() -> None:
    torch = pytest.importorskip("torch")
    residual_stack = [[1.0, 2.0]]
    unembed = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
    unembed_bias = [0.5, -1.0]

    logits = residual_stack_to_logits(residual_stack, unembed, unembed_bias)

    assert isinstance(logits, torch.Tensor)
    assert torch.allclose(logits, torch.tensor([[1.5, 1.0]]))


def test_residual_stack_to_logits_adds_list_bias_elementwise() -> None:
    assert residual_stack_to_logits([[1.0, 2.0]], [[1.0, 0.0], [0.0, 1.0]], [0.5, -1.0]) == [
        [1.5, 1.0]
    ]


def test_head_results_from_z_supports_direct_logit_attribution_workflow() -> None:
    z = [[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]]
    W_O = [
        [[1, 0, 1], [0, 1, 1]],
        [[1, 2, 0], [3, 4, 1]],
    ]

    result = compute_head_results_from_z(z, W_O)

    assert result == [[[[1.0, 2.0, 3.0], [15.0, 22.0, 4.0]], [[5.0, 6.0, 11.0], [31.0, 46.0, 8.0]]]]
    assert direct_logit_attribution(result, [1, 0, -1]) == [[[-2.0, 11.0], [-6.0, 23.0]]]


def test_head_results_from_z_accepts_single_layer_full_w_o() -> None:
    z = [[[[1, 2], [3, 4]]]]
    W_O = [[[[1, 0], [0, 1]], [[2, 0], [0, 2]]]]

    assert compute_head_results_from_z(z, W_O) == [[[[1.0, 2.0], [6.0, 8.0]]]]


def test_head_results_from_z_aligns_explicit_layer_axis() -> None:
    z = [
        [[[[1, 2], [3, 4]]]],
        [[[[5, 6], [7, 8]]]],
    ]
    W_O = [
        [[[1, 0], [0, 1]], [[2, 0], [0, 2]]],
        [[[0, 1], [1, 0]], [[3, 0], [0, 3]]],
    ]

    assert compute_head_results_from_z(z, W_O) == [
        [[[[1.0, 2.0], [6.0, 8.0]]]],
        [[[[6.0, 5.0], [21.0, 24.0]]]],
    ]


def test_head_results_from_z_aligns_batchless_explicit_layer_axis() -> None:
    z = [
        [[[1, 2], [3, 4]]],
        [[[5, 6], [7, 8]]],
    ]
    W_O = [
        [[[1, 0], [0, 1]], [[2, 0], [0, 2]]],
        [[[0, 1], [1, 0]], [[3, 0], [0, 3]]],
    ]

    assert compute_head_results_from_z(z, W_O, has_layer_axis=True) == [
        [[[1.0, 2.0], [6.0, 8.0]]],
        [[[6.0, 5.0], [21.0, 24.0]]],
    ]


def test_head_results_from_z_aligns_batchless_single_position_layer_axis() -> None:
    z = [
        [[1, 2], [3, 4]],
        [[5, 6], [7, 8]],
    ]
    W_O = [
        [[[1, 0], [0, 1]], [[2, 0], [0, 2]]],
        [[[0, 1], [1, 0]], [[3, 0], [0, 3]]],
    ]

    assert compute_head_results_from_z(z, W_O, has_layer_axis=True) == [
        [[1.0, 2.0], [6.0, 8.0]],
        [[6.0, 5.0], [21.0, 24.0]],
    ]


def test_head_results_from_z_torch_aligns_explicit_layer_axis() -> None:
    torch = pytest.importorskip("torch")
    z = torch.tensor(
        [
            [[[[1.0, 2.0], [3.0, 4.0]]]],
            [[[[5.0, 6.0], [7.0, 8.0]]]],
        ]
    )
    W_O = torch.tensor(
        [
            [[[1.0, 0.0], [0.0, 1.0]], [[2.0, 0.0], [0.0, 2.0]]],
            [[[0.0, 1.0], [1.0, 0.0]], [[3.0, 0.0], [0.0, 3.0]]],
        ]
    )

    expected = torch.einsum("l...hd,lhdm->l...hm", z, W_O)

    assert torch.equal(compute_head_results_from_z(z, W_O), expected)


def test_head_results_from_z_rejects_ambiguous_batch_axis_matching_w_o_layers() -> None:
    torch = pytest.importorskip("torch")
    z = torch.arange(2 * 1 * 2 * 2, dtype=torch.float32).reshape(2, 1, 2, 2)
    W_O = torch.arange(2 * 2 * 2 * 2, dtype=torch.float32).reshape(2, 2, 2, 2)

    with pytest.raises(ValueError, match="has_layer_axis=True"):
        compute_head_results_from_z(z, W_O)


def test_head_results_from_z_torch_aligns_batchless_explicit_layer_axis() -> None:
    torch = pytest.importorskip("torch")
    z = torch.tensor(
        [
            [[[1.0, 2.0], [3.0, 4.0]]],
            [[[5.0, 6.0], [7.0, 8.0]]],
        ]
    )
    W_O = torch.tensor(
        [
            [[[1.0, 0.0], [0.0, 1.0]], [[2.0, 0.0], [0.0, 2.0]]],
            [[[0.0, 1.0], [1.0, 0.0]], [[3.0, 0.0], [0.0, 3.0]]],
        ]
    )

    expected = torch.einsum("l...hd,lhdm->l...hm", z, W_O)

    assert torch.equal(compute_head_results_from_z(z, W_O, has_layer_axis=True), expected)


def test_head_results_from_z_torch_aligns_batchless_single_position_layer_axis() -> None:
    torch = pytest.importorskip("torch")
    z = torch.tensor(
        [
            [[1.0, 2.0], [3.0, 4.0]],
            [[5.0, 6.0], [7.0, 8.0]],
        ]
    )
    W_O = torch.tensor(
        [
            [[[1.0, 0.0], [0.0, 1.0]], [[2.0, 0.0], [0.0, 2.0]]],
            [[[0.0, 1.0], [1.0, 0.0]], [[3.0, 0.0], [0.0, 3.0]]],
        ]
    )

    expected = torch.einsum("l...hd,lhdm->l...hm", z, W_O)

    assert torch.equal(compute_head_results_from_z(z, W_O, has_layer_axis=True), expected)


def test_head_results_from_z_requires_layer_selection_for_multi_layer_w_o() -> None:
    z = [[[[1, 2], [3, 4]]]]
    W_O = [
        [[[1, 0], [0, 1]], [[2, 0], [0, 2]]],
        [[[0, 1], [1, 0]], [[3, 0], [0, 3]]],
    ]

    with pytest.raises(ValueError, match="W_O has a layer dimension"):
        compute_head_results_from_z(z, W_O)


def test_direct_logit_attribution_broadcasts_token_directions_over_component_axis() -> None:
    residual_stack = [
        [[[1, 2], [3, 4]]],
        [[[10, 20], [30, 40]]],
    ]
    token_directions = [[[1, 0], [0, 1]]]

    assert direct_logit_attribution(residual_stack, token_directions) == [
        [[1.0, 4.0]],
        [[10.0, 40.0]],
    ]


def test_direct_logit_attribution_accepts_torch_residuals_with_python_directions() -> None:
    torch = pytest.importorskip("torch")
    residual_stack = torch.tensor(
        [
            [[[1.0, 2.0], [3.0, 4.0]]],
            [[[10.0, 20.0], [30.0, 40.0]]],
        ]
    )

    attrs = direct_logit_attribution(residual_stack, [[[1.0, 0.0], [0.0, 1.0]]])

    assert torch.equal(attrs, torch.tensor([[[1.0, 4.0]], [[10.0, 40.0]]]))


def test_direct_logit_attribution_accepts_numpy_residuals_with_python_directions() -> None:
    np = pytest.importorskip("numpy")
    residual_stack = np.array(
        [
            [[[1.0, 2.0], [3.0, 4.0]]],
            [[[10.0, 20.0], [30.0, 40.0]]],
        ]
    )

    attrs = direct_logit_attribution(residual_stack, [[[1.0, 0.0], [0.0, 1.0]]])

    assert np.array_equal(attrs, np.array([[[1.0, 4.0]], [[10.0, 40.0]]]))
