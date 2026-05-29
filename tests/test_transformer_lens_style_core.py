from __future__ import annotations

import math
from typing import Any

import pytest

from SafeLens.core.analysis import (
    attention_pattern_score,
    compute_head_results_from_z,
    cross_entropy_loss,
    direct_logit_attribution,
    induction_attention_score,
    lm_accuracy,
    lm_cross_entropy_loss,
    lm_log_probs,
    logit_diff,
    logits_to_log_probs,
    mean_ablation_hook,
    previous_token_attention_score,
    replace_activation_hook,
    residual_stack_to_logits,
    softmax,
    test_prompt as run_test_prompt,
    topk_tokens,
    zero_ablation_hook,
)
from SafeLens.core.factored_matrix import FactoredMatrix, composition_scores, matmul, transpose
from SafeLens.core.hooks import ActivationCache, HookPoint
from SafeLens.core.hooked_root import HookedRoot
from SafeLens.core.kv_cache import KeyValueCache, KeyValueCacheEntry


def assert_nested_close(left: Any, right: Any, *, abs_tol: float = 1e-9) -> None:
    if isinstance(left, list) and isinstance(right, list):
        assert len(left) == len(right)
        for left_item, right_item in zip(left, right, strict=True):
            assert_nested_close(left_item, right_item, abs_tol=abs_tol)
        return
    assert math.isclose(float(left), float(right), abs_tol=abs_tol)


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
            fwd_hooks=[
                ("blocks.0.hook_resid_pre", lambda activation, _hook: activation + ["temp"])
            ]
        ):
            assert resid([]) == ["outer", "kept", "temp"]
        assert resid([]) == ["outer", "kept"]

    assert resid([]) == ["kept"]
    root.reset_hooks()
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
    root.reset_hooks(direction="both", including_permanent=True)
    assert not resid.has_hooks()
    assert not mlp.has_hooks()


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

    cache, fwd_hooks, bwd_hooks = root.get_caching_hooks("blocks.0.hook_resid_pre")

    assert bwd_hooks == []
    with root.hooks(fwd_hooks=fwd_hooks):
        resid([9])

    assert cache.to_dict() == {"blocks.0.hook_resid_pre": [9]}


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


def test_hooked_root_names_filters_match_equivalent_safelens_names() -> None:
    root = HookedRoot()
    q_hook = root.add_hook_point("blocks.0.attn.hook_q")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    cache, fwd_hooks, _ = root.get_caching_hooks("layer_0.q")
    with root.hooks(fwd_hooks=fwd_hooks):
        q_hook([1])
        mlp([2])

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

    assert cache["blocks.0.attn.hook_q"] == [[3, 30], [4, 40]]
    assert cache["blocks.0.attn.hook_pattern"] == [[4, 5, 6], [10, 11, 12]]
    assert cache["blocks.0.hook_resid_pre"] == [2, 20]


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


def test_hooked_root_hooks_accept_name_filters() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    mlp = root.add_hook_point("blocks.0.hook_mlp_out")

    with root.hooks(fwd_hooks=[(lambda name: "resid" in name, lambda act, _hook: act + [9])]):
        assert resid([1]) == [1, 9]
        assert mlp([1]) == [1]


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

    assert cache.to_dict() == {"blocks.0.hook_resid_pre": [2, 20]}


def test_hooked_root_run_with_cache_preserves_external_empty_cache() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")
    external_cache = ActivationCache()

    _output, cache = root.run_with_cache(lambda: resid([1]), cache=external_cache)

    assert cache is external_cache
    assert external_cache.to_dict() == {"blocks.0.hook_resid_pre": [1]}


def test_hook_point_backward_hooks_transform_gradients() -> None:
    torch = pytest.importorskip("torch")
    hook = HookPoint("blocks.0.hook_resid_post")
    hook.add_hook(lambda grad, _hook: grad * 3, dir="bwd")
    value = torch.tensor([2.0], requires_grad=True)

    output = hook(value)
    (output * 5).sum().backward()

    assert torch.equal(value.grad, torch.tensor([15.0]))


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


def test_factored_matrix_dense_ops_and_composition() -> None:
    left = FactoredMatrix([[1, 2], [3, 4]], [[2, 0], [0, 2]])
    right = FactoredMatrix([[1, 0], [0, 1]], [[1], [2]])
    composed = left @ right

    assert left.AB == [[2.0, 4.0], [6.0, 8.0]]
    assert left.BA == [[2.0, 4.0], [6.0, 8.0]]
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
    assert matrix.V == matrix.Vh

    even = matrix.make_even()
    assert_nested_close(even.AB, matrix.AB)
    assert_nested_close(FactoredMatrix(matrix.U, matrix.collapse_l()).AB, matrix.AB)
    assert_nested_close(FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB, matrix.AB)


def test_factored_matrix_svd_returns_v_not_vh_for_nonsymmetric_matrices() -> None:
    matrix = FactoredMatrix([[1, 2], [3, 5]], [[7, 11], [13, 17]])

    reconstructed = FactoredMatrix(matrix.U, matrix.collapse_l()).AB
    reconstructed_from_right = FactoredMatrix(matrix.collapse_r(), transpose(matrix.V)).AB
    direct_svd_reconstruction = matmul(matrix.collapse_r(), transpose(matrix.V))

    assert matrix.V == matrix.Vh
    assert_nested_close(reconstructed, matrix.AB)
    assert_nested_close(reconstructed_from_right, matrix.AB)
    assert_nested_close(direct_svd_reconstruction, matrix.AB)
    assert_nested_close(matrix.make_even().AB, matrix.AB)


def test_factored_matrix_rectangular_eigenvalues_use_inner_product() -> None:
    matrix = FactoredMatrix([[1, 2], [3, 4], [5, 6]], [[7, 8, 9], [10, 11, 12]])

    assert len(matrix.eigenvalues) == 2
    assert_nested_close(
        sorted(matrix.eigenvalues),
        [0.16994755741637846, 211.83005244258362],
        abs_tol=1e-8,
    )


def test_factored_matrix_unsqueeze_repr_and_index_guards() -> None:
    matrix = FactoredMatrix([[1, 0], [0, 1]], [[2, 0], [0, 3]])
    batched = matrix.unsqueeze(0)

    assert repr(matrix) == "FactoredMatrix: Shape((2, 2)), Hidden Dim(2)"
    assert batched.shape == (1, 2, 2)
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
    entry.append([[[3]]], [[[30]]])

    assert entry.sequence_length == 3
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
    assert lm_accuracy(logits, tokens) == 1.0


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
    assert per_token_loss[0][1] is None
    assert lm_accuracy(logits, tokens, attention_mask) == 1.0


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

    expected_log_probs = torch.log_softmax(logits[:, :-1], dim=-1).gather(
        -1,
        tokens[:, 1:].unsqueeze(-1),
    ).squeeze(-1)

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

    expected = np.array([
        2.0 - math.log(math.exp(0.0) + math.exp(2.0) + math.exp(0.0)),
        3.0 - math.log(math.exp(0.0) + math.exp(0.0) + math.exp(3.0)),
    ])
    same_token_expected = np.array([
        2.0 - math.log(math.exp(0.0) + math.exp(2.0) + math.exp(0.0)),
        0.0 - math.log(math.exp(0.0) + math.exp(0.0) + math.exp(3.0)),
    ])
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

    assert compute_head_results_from_z(z, W_O) == [
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

    assert compute_head_results_from_z(z, W_O) == [
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

    assert torch.equal(compute_head_results_from_z(z, W_O), expected)


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

    assert torch.equal(compute_head_results_from_z(z, W_O), expected)


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
