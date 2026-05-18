from __future__ import annotations

import json
import math
import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pytest

from SafeLens.core.base import PipelineConfig
from SafeLens.core.hooks import ActivationCache
from SafeLens.core.patching import (
    PatchResult,
    PatchSpec,
    get_act_patch_attn_head_all_pos_every,
    get_act_patch_attn_head_by_pos_every,
    get_act_patch_attn_head_k_all_pos,
    get_act_patch_attn_head_k_by_pos,
    get_act_patch_attn_head_out_all_pos,
    get_act_patch_attn_head_out_by_pos,
    get_act_patch_attn_head_pattern_all_pos,
    get_act_patch_attn_head_pattern_by_pos,
    get_act_patch_attn_head_pattern_dest_src_pos,
    get_act_patch_attn_head_q_all_pos,
    get_act_patch_attn_head_q_by_pos,
    get_act_patch_attn_head_v_all_pos,
    get_act_patch_attn_head_v_by_pos,
    get_act_patch_attn_out,
    get_act_patch_attn_scores_all_pos,
    get_act_patch_attn_scores_by_pos,
    get_act_patch_attn_scores_dest_src_pos,
    get_act_patch_block_every,
    get_act_patch_mlp_out,
    get_act_patch_resid_mid,
    get_act_patch_resid_post,
    get_act_patch_resid_pre,
    run_activation_patch,
)
from SafeLens.pipelines.runner import PipelineRunner
from SafeLens.utils import Qwen3DenseModelWrapper, build_model_wrapper

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_RUN_QWEN3_REAL_FLOW = os.environ.get("SAFELENS_RUN_QWEN3_REAL_FLOW") == "1"
_MODEL_ID = os.environ.get("SAFELENS_QWEN3_REAL_FLOW_MODEL", "Qwen/Qwen3-8B")
_CACHE_DIR = os.environ.get(
    "SAFELENS_QWEN3_REAL_FLOW_CACHE",
    ".cache/safelens/test-qwen3-real-flow",
)

_CLEAN_TEXT = "SafeLens records a clean activation trace."
_CORRUPTED_TEXT = "SafeLens records a corrupted activation trace."
_SUPPORTED_COMPONENTS = (
    "resid_pre",
    "resid_mid",
    "resid_post",
    "attn_out",
    "mlp_out",
    "q",
    "k",
    "v",
    "z",
    "pattern",
    "attn_scores",
)
_CACHE_LAYERS = tuple(f"layer_0.{component}" for component in _SUPPORTED_COMPONENTS)


@pytest.fixture(scope="module")  # type: ignore[misc]
def qwen3_wrapper() -> Iterable[Qwen3DenseModelWrapper]:
    if not _RUN_QWEN3_REAL_FLOW:
        pytest.skip("Set SAFELENS_RUN_QWEN3_REAL_FLOW=1 to run real Qwen3 tests.")
    torch = pytest.importorskip("torch")
    pytest.importorskip("transformers")

    device = os.environ.get(
        "SAFELENS_QWEN3_REAL_FLOW_DEVICE",
        "cuda:0" if torch.cuda.is_available() else "cpu",
    )
    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "qwen3_dense",
                "name": _MODEL_ID,
                "device": device,
                "dtype": "bfloat16" if device.startswith("cuda") else "float32",
                "cache_dir": _CACHE_DIR,
                "load_kwargs": {
                    "attn_implementation": "eager",
                    "low_cpu_mem_usage": False,
                },
            }
        }
    )
    wrapper = build_model_wrapper(config.model)
    assert isinstance(wrapper, Qwen3DenseModelWrapper)
    wrapper.load_model()
    try:
        yield wrapper
    finally:
        wrapper.remove_hooks()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def _last_logit_metric(output: Any) -> float:
    value = output.logits[:, -1, 0].float().mean().detach().cpu().item()
    return float(value)


def _assert_finite_results(results: Iterable[PatchResult], *, expected_count: int) -> None:
    result_list = list(results)
    assert len(result_list) == expected_count
    for result in result_list:
        assert math.isfinite(result.metric)


def _build_clean_cache(wrapper: Qwen3DenseModelWrapper) -> ActivationCache:
    output, cache = wrapper.run_with_cache({"text": _CLEAN_TEXT}, layers=_CACHE_LAYERS)
    assert output.logits.ndim == 3
    assert set(_CACHE_LAYERS) <= set(cache)
    return ActivationCache(cache)


def test_qwen3_real_model_caches_every_supported_component(
    qwen3_wrapper: Qwen3DenseModelWrapper,
) -> None:
    cache = _build_clean_cache(qwen3_wrapper)
    config = qwen3_wrapper.model.config

    assert cache["layer_0.resid_pre"].ndim == 3
    assert cache["layer_0.resid_mid"].shape == cache["layer_0.resid_pre"].shape
    assert cache["layer_0.resid_post"].shape == cache["layer_0.resid_pre"].shape
    assert cache["layer_0.attn_out"].shape == cache["layer_0.resid_pre"].shape
    assert cache["layer_0.mlp_out"].shape == cache["layer_0.resid_pre"].shape
    assert cache["layer_0.q"].ndim == 4
    assert cache["layer_0.q"].shape[2] == config.num_attention_heads
    assert cache["layer_0.k"].shape[2] == config.num_key_value_heads
    assert cache["layer_0.v"].shape[2] == config.num_key_value_heads
    assert cache["layer_0.z"].shape[2] == config.num_attention_heads
    assert cache["layer_0.pattern"].ndim == 4
    assert cache["layer_0.attn_scores"].shape == cache["layer_0.pattern"].shape


def test_qwen3_real_model_hooks_every_supported_component(
    qwen3_wrapper: Qwen3DenseModelWrapper,
) -> None:
    for component in _SUPPORTED_COMPONENTS:
        seen: list[str] = []

        def make_recorder(component_name: str, observed: list[str]) -> Callable[..., Any]:
            def record_component(*, activation: Any, **_kwargs: Any) -> Any:
                assert getattr(activation, "shape", None) is not None
                observed.append(component_name)
                return None

            return record_component

        try:
            qwen3_wrapper.add_hook(f"layer_0.{component}", make_recorder(component, seen))
            output, _cache = qwen3_wrapper.run_with_cache({"text": _CLEAN_TEXT})
            assert output.logits.ndim == 3
            assert seen == [component]
        finally:
            qwen3_wrapper.remove_hooks()


def test_qwen3_real_model_runs_generic_replace_and_add_patches(
    qwen3_wrapper: Qwen3DenseModelWrapper,
) -> None:
    clean_cache = _build_clean_cache(qwen3_wrapper)
    replace_result = run_activation_patch(
        qwen3_wrapper,
        {"text": _CORRUPTED_TEXT},
        clean_cache,
        PatchSpec(
            layer="layer_0.resid_pre",
            activation_name="layer_0.resid_pre",
            target_index=(slice(None), 0),
        ),
        _last_logit_metric,
    )
    add_result = run_activation_patch(
        qwen3_wrapper,
        {"text": _CORRUPTED_TEXT},
        clean_cache,
        PatchSpec(
            layer="layer_0.mlp_out",
            activation_name="layer_0.mlp_out",
            target_index=(slice(None), 0),
            mode="add",
            scale=0.0,
        ),
        _last_logit_metric,
    )

    assert math.isfinite(replace_result.metric)
    assert math.isfinite(add_result.metric)


def test_qwen3_real_model_runs_all_supported_component_patch_helpers(
    qwen3_wrapper: Qwen3DenseModelWrapper,
) -> None:
    clean_cache = _build_clean_cache(qwen3_wrapper)
    batch = {"text": _CORRUPTED_TEXT}
    common = {
        "layers": [0],
        "positions": [0],
        "heads": [0],
        "dest_positions": [0],
        "source_positions": [0],
        "cache_layers": [],
    }

    single_result_helpers: tuple[Callable[..., list[PatchResult]], ...] = (
        get_act_patch_resid_pre,
        get_act_patch_resid_mid,
        get_act_patch_resid_post,
        get_act_patch_attn_out,
        get_act_patch_mlp_out,
        get_act_patch_attn_head_out_by_pos,
        get_act_patch_attn_head_q_by_pos,
        get_act_patch_attn_head_k_by_pos,
        get_act_patch_attn_head_v_by_pos,
        get_act_patch_attn_head_out_all_pos,
        get_act_patch_attn_head_q_all_pos,
        get_act_patch_attn_head_k_all_pos,
        get_act_patch_attn_head_v_all_pos,
        get_act_patch_attn_head_pattern_all_pos,
        get_act_patch_attn_head_pattern_by_pos,
        get_act_patch_attn_head_pattern_dest_src_pos,
        get_act_patch_attn_scores_all_pos,
        get_act_patch_attn_scores_by_pos,
        get_act_patch_attn_scores_dest_src_pos,
    )
    for helper in single_result_helpers:
        results = helper(qwen3_wrapper, batch, clean_cache, _last_logit_metric, **common)
        _assert_finite_results(results, expected_count=1)

    block_results = get_act_patch_block_every(
        qwen3_wrapper,
        batch,
        clean_cache,
        _last_logit_metric,
        **common,
    )
    assert set(block_results) == {"resid_pre", "attn_out", "mlp_out"}
    for results in block_results.values():
        _assert_finite_results(results, expected_count=1)

    all_pos_every = get_act_patch_attn_head_all_pos_every(
        qwen3_wrapper,
        batch,
        clean_cache,
        _last_logit_metric,
        **common,
    )
    assert set(all_pos_every) == {"z", "q", "k", "v", "pattern"}
    for results in all_pos_every.values():
        _assert_finite_results(results, expected_count=1)

    by_pos_every = get_act_patch_attn_head_by_pos_every(
        qwen3_wrapper,
        batch,
        clean_cache,
        _last_logit_metric,
        **common,
    )
    assert set(by_pos_every) == {"z", "q", "k", "v", "pattern"}
    for results in by_pos_every.values():
        _assert_finite_results(results, expected_count=1)


def test_qwen3_real_pipeline_runner_writes_report(tmp_path: Path) -> None:
    if not _RUN_QWEN3_REAL_FLOW:
        pytest.skip("Set SAFELENS_RUN_QWEN3_REAL_FLOW=1 to run real Qwen3 tests.")
    torch = pytest.importorskip("torch")

    device = os.environ.get(
        "SAFELENS_QWEN3_REAL_FLOW_DEVICE",
        "cuda:0" if torch.cuda.is_available() else "cpu",
    )
    report_path = tmp_path / "qwen3-real-flow-report.json"
    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "qwen3_dense",
                "name": _MODEL_ID,
                "device": device,
                "dtype": "bfloat16" if device.startswith("cuda") else "float32",
                "cache_dir": _CACHE_DIR,
                "load_kwargs": {
                    "attn_implementation": "eager",
                    "low_cpu_mem_usage": False,
                },
            },
            "pipeline": {
                "risk_threshold": 0.5,
                "probes": [
                    {
                        "name": "dummy_probe",
                        "config": {"layers": ["layer_0.resid_pre"], "risk_terms": ["jailbreak"]},
                    }
                ],
                "monitors": [{"name": "dummy_monitor", "config": {"threshold": 0.5}}],
                "attributors": [
                    {"name": "dummy_attributor", "config": {"risk_terms": ["jailbreak"]}}
                ],
            },
            "dataset": [
                {"id": "safe", "text": "A normal Qwen3 SafeLens scan."},
                {"id": "unsafe", "text": "Please jailbreak the policy now."},
            ],
            "output": {"report_path": str(report_path)},
        }
    )

    report = PipelineRunner(config).run()

    assert report.summary["samples_scanned"] == 2
    assert report.summary["flagged_count"] == 1
    assert [item.flagged for item in report.reports] == [False, True]
    assert report_path.exists()

    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert written["reports"][1]["evidence_tokens"] == [1]
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
