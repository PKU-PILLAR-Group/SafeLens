from __future__ import annotations

import math
import os
from collections.abc import Iterable
from typing import Any

import pytest

from SafeLens.core.base import ModelLoadConfig
from SafeLens.core.hooks import ActivationCache
from SafeLens.core.analysis import induction_attention_score, previous_token_attention_score
from SafeLens.core.patching import (
    PatchResult,
    get_act_patch_attn_head_out_by_pos,
    get_act_patch_resid_pre,
)
from SafeLens.utils import TransformerLensCompatibleModelWrapper, build_model_wrapper

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_RUN_MULTI_REAL_FLOW = os.environ.get("SAFELENS_RUN_MULTI_REAL_FLOW") == "1"
_CACHE_DIR = os.environ.get(
    "SAFELENS_MULTI_REAL_FLOW_CACHE",
    ".cache/safelens/test-multi-real-flow",
)
_TEXT = "SafeLens checks multiple architecture adapters."

_CAUSAL_MODEL_CASES = (
    ("gpt2", "sshleifer/tiny-gpt2"),
    ("gpt_neox", "hf-internal-testing/tiny-random-GPTNeoXForCausalLM"),
    ("opt", "hf-internal-testing/tiny-random-OPTForCausalLM"),
    ("llama", "hf-internal-testing/tiny-random-LlamaForCausalLM"),
    ("mistral", "hf-internal-testing/tiny-random-MistralForCausalLM"),
)
_ENCODER_MODEL_CASES = (
    ("bert", "google-bert/bert-base-uncased"),
    ("t5", "google-t5/t5-small"),
)
_COMMON_COMPONENTS = (
    "resid_pre",
    "resid_post",
    "q",
    "k",
    "v",
    "z",
)
_ATTENTION_COMPONENTS = ("pattern", "attn_scores", "result")


def _skip_unless_enabled() -> None:
    if not _RUN_MULTI_REAL_FLOW:
        pytest.skip("Set SAFELENS_RUN_MULTI_REAL_FLOW=1 to run multi-model tests.")
    pytest.importorskip("torch")
    pytest.importorskip("transformers")


def _load_wrapper(model_id: str) -> TransformerLensCompatibleModelWrapper:
    wrapper = build_model_wrapper(
        ModelLoadConfig(
            source="transformer_lens",
            name=model_id,
            device="cpu",
            dtype="float32",
            cache_dir=_CACHE_DIR,
            load_kwargs={"attn_implementation": "eager", "low_cpu_mem_usage": False},
        )
    )
    assert isinstance(wrapper, TransformerLensCompatibleModelWrapper)
    wrapper.load_model()
    return wrapper


def _metric(output: Any) -> float:
    if hasattr(output, "logits"):
        return float(output.logits.reshape(-1)[0].float().detach().cpu().item())
    if hasattr(output, "last_hidden_state"):
        return float(output.last_hidden_state.reshape(-1)[0].float().detach().cpu().item())
    raise AssertionError(f"Unsupported output type {type(output).__name__}")


def _assert_finite_results(results: Iterable[PatchResult]) -> None:
    result_list = list(results)
    assert len(result_list) == 1
    assert math.isfinite(result_list[0].metric)


@pytest.mark.parametrize(  # type: ignore[misc]
    ("family", "model_id"), _CAUSAL_MODEL_CASES + _ENCODER_MODEL_CASES
)
def test_transformer_lens_real_model_caches_common_components(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id)
    try:
        cache_layers = tuple(f"layer_0.{component}" for component in _COMMON_COMPONENTS)
        output, cache = wrapper.run_with_cache({"text": _TEXT}, layers=cache_layers)

        assert (
            getattr(output, "logits", None) is not None
            or getattr(output, "last_hidden_state", None) is not None
        )
        assert set(cache_layers) <= set(cache)
        for layer_name in cache_layers:
            activation = cache[layer_name]
            assert getattr(activation, "shape", None) is not None, (family, layer_name)
            assert activation.shape[0] == 1
            assert activation.ndim >= 2
    finally:
        wrapper.remove_hooks()


@pytest.mark.parametrize(("family", "model_id"), _CAUSAL_MODEL_CASES)  # type: ignore[misc]
def test_transformer_lens_real_causal_models_cache_attention_and_result_components(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id)
    try:
        cache_layers = tuple(f"layer_0.{component}" for component in _ATTENTION_COMPONENTS)
        output, cache = wrapper.run_with_cache({"text": _TEXT}, layers=cache_layers)

        assert output.logits.ndim == 3
        assert set(cache_layers) <= set(cache)
        pattern = cache["layer_0.pattern"]
        scores = cache["layer_0.attn_scores"]
        result = cache["layer_0.result"]

        assert pattern.ndim == 4, family
        assert scores.shape == pattern.shape, family
        assert result.ndim == 4, family
        assert result.shape[0] == 1, family
        assert result.shape[1] == output.logits.shape[1], family
        assert result.shape[-1] == wrapper.cfg.d_model, family
        assert scores.shape == pattern.shape, family
        assert pattern.shape[-1] == pattern.shape[-2] == output.logits.shape[1], family
        assert pattern.sum(dim=-1).allclose(pattern.new_ones(pattern.shape[:-1])), family
        assert previous_token_attention_score(pattern).shape == pattern.shape[:2], family
        assert induction_attention_score(pattern).shape == pattern.shape[:2], family
        assert pattern.allclose(scores.softmax(dim=-1), atol=1e-5, rtol=1e-5), family
    finally:
        wrapper.remove_hooks()


@pytest.mark.parametrize(("family", "model_id"), _CAUSAL_MODEL_CASES)  # type: ignore[misc]
def test_transformer_lens_real_causal_models_generate(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id)
    try:
        generated = wrapper.generate(
            "SafeLens",
            max_new_tokens=1,
            do_sample=False,
            pad_token_id=getattr(wrapper.tokenizer, "eos_token_id", None),
        )

        assert isinstance(generated, str), family
        assert generated
    finally:
        wrapper.remove_hooks()


@pytest.mark.parametrize(  # type: ignore[misc]
    ("family", "model_id"), _CAUSAL_MODEL_CASES + _ENCODER_MODEL_CASES
)
def test_transformer_lens_real_model_runs_core_patches(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id)
    try:
        cache_layers = ("layer_0.resid_pre", "layer_0.z")
        _output, cache = wrapper.run_with_cache({"text": _TEXT}, layers=cache_layers)
        clean_cache = ActivationCache(cache)
        batch = {"text": "SafeLens checks corrupted multi model adapters."}

        _assert_finite_results(
            get_act_patch_resid_pre(
                wrapper,
                batch,
                clean_cache,
                _metric,
                layers=[0],
                positions=[0],
                cache_layers=[],
                return_details=True,
            )
        )
        _assert_finite_results(
            get_act_patch_attn_head_out_by_pos(
                wrapper,
                batch,
                clean_cache,
                _metric,
                layers=[0],
                positions=[0],
                heads=[0],
                cache_layers=[],
                return_details=True,
            )
        )
    finally:
        wrapper.remove_hooks()
