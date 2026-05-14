from __future__ import annotations

import math
from typing import Any

from SafeLens.core.analysis import (
    cross_entropy_loss,
    direct_logit_attribution,
    logit_diff,
    logits_to_log_probs,
    mean_ablation_hook,
    replace_activation_hook,
    residual_stack_to_logits,
    softmax,
    topk_tokens,
    zero_ablation_hook,
)
from SafeLens.core.factored_matrix import FactoredMatrix
from SafeLens.core.hooked_root import HookedRoot
from SafeLens.core.kv_cache import KeyValueCache, KeyValueCacheEntry


def test_hooked_root_manages_temporary_and_permanent_hooks() -> None:
    root = HookedRoot()
    resid = root.add_hook_point("blocks.0.hook_resid_pre")

    with root.hooks(
        fwd_hooks=[("blocks.0.hook_resid_pre", lambda activation, _hook: activation + [1])]
    ):
        assert resid([0]) == [0, 1]

    assert resid([0]) == [0]

    root.add_perma_hook(
        "blocks.0.hook_resid_pre",
        lambda activation, _hook: activation + [2],
    )
    root.reset_hooks(including_permanent=True)

    assert resid([0]) == [0]


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

    assert probs == [0.5, 0.5]
    assert math.isclose(log_probs[0], -math.log(2.0))
    assert math.isclose(cross_entropy_loss([[0.0, 0.0]], [1]), math.log(2.0))
    assert topk_tokens([0.1, 0.9, 0.3], k=2) == ([1, 2], [0.9, 0.3])
    assert topk_tokens([[0.1, 0.9, 0.3], [0.4, 0.2, 0.8]], k=1) == [
        ([1], [0.9]),
        ([2], [0.8]),
    ]
    assert logit_diff([[1.0, 4.0], [7.0, 2.0]], 0, 1, pos=-1) == 5.0
    assert logit_diff([[[1.0, 4.0], [7.0, 2.0]]], 0, 1, pos=-1) == 5.0


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
