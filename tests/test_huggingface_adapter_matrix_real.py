from __future__ import annotations

import math
import os
from collections.abc import Iterable
from typing import Any

import pytest

from SafeLens.core.base import ModelLoadConfig
from SafeLens.core.hooks import ActivationCache
from SafeLens.core.patching import (
    PatchResult,
    get_act_patch_attn_head_out_by_pos,
    get_act_patch_resid_pre,
)
from SafeLens.utils import HuggingFaceModelWrapper, build_model_wrapper

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_RUN_ADAPTER_MATRIX = os.environ.get("SAFELENS_RUN_HF_ADAPTER_MATRIX") == "1"
_CACHE_DIR = os.environ.get(
    "SAFELENS_HF_ADAPTER_MATRIX_CACHE",
    ".cache/safelens/test-hf-adapter-matrix",
)
_TEXT = "SafeLens checks a real adapter matrix."

_DECODER_CASES = (
    ("gpt2", "sshleifer/tiny-gpt2"),
    ("gpt_neox", "hf-internal-testing/tiny-random-GPTNeoXForCausalLM"),
    ("gptj", "hf-internal-testing/tiny-random-GPTJForCausalLM"),
    ("gpt_neo", "hf-internal-testing/tiny-random-GPTNeoForCausalLM"),
    ("bloom", "hf-internal-testing/tiny-random-BloomForCausalLM"),
    ("falcon", "hf-internal-testing/tiny-random-FalconForCausalLM"),
    ("mpt", "hf-internal-testing/tiny-random-MptForCausalLM"),
    ("phi", "hf-internal-testing/tiny-random-PhiForCausalLM"),
    ("opt", "hf-internal-testing/tiny-random-OPTForCausalLM"),
    ("llama", "hf-internal-testing/tiny-random-LlamaForCausalLM"),
    ("mistral", "hf-internal-testing/tiny-random-MistralForCausalLM"),
)
_TOKEN_ID_DECODER_CASES = (("mixtral", "hf-internal-testing/tiny-random-MixtralForCausalLM"),)
_ENCODER_CASES = (
    ("roberta", "hf-internal-testing/tiny-random-RobertaModel"),
    ("distilbert", "hf-internal-testing/tiny-random-DistilBertModel"),
)
_AUDIO_CASES = (
    ("wav2vec2", "hf-internal-testing/tiny-random-Wav2Vec2Model"),
    ("hubert", "hf-internal-testing/tiny-random-HubertModel"),
)
_HEAD_COMPONENTS = ("q", "k", "v", "z")
_COMMON_COMPONENTS = (
    "resid_pre",
    "resid_post",
    "attn_out",
    "mlp_out",
    *_HEAD_COMPONENTS,
)


def _skip_unless_enabled() -> None:
    if not _RUN_ADAPTER_MATRIX:
        pytest.skip("Set SAFELENS_RUN_HF_ADAPTER_MATRIX=1 to run real adapter matrix tests.")
    pytest.importorskip("torch")
    pytest.importorskip("transformers")


def _load_wrapper(model_id: str, *, source: str = "huggingface") -> HuggingFaceModelWrapper:
    wrapper = build_model_wrapper(
        ModelLoadConfig(
            source=source,
            name=model_id,
            device="cpu",
            dtype="float32",
            cache_dir=_CACHE_DIR,
            load_kwargs={"attn_implementation": "eager", "low_cpu_mem_usage": False},
        )
    )
    assert isinstance(wrapper, HuggingFaceModelWrapper)
    wrapper.load_model()
    return wrapper


def _metric(output: Any) -> float:
    if hasattr(output, "logits"):
        return float(output.logits.reshape(-1)[0].float().detach().cpu().item())
    if hasattr(output, "last_hidden_state"):
        return float(output.last_hidden_state.reshape(-1)[0].float().detach().cpu().item())
    raise AssertionError(f"Unsupported output type {type(output).__name__}")


def _assert_one_finite_result(results: Iterable[PatchResult]) -> None:
    result_list = list(results)
    assert len(result_list) == 1
    assert math.isfinite(result_list[0].metric)


def _token_id_batch() -> dict[str, Any]:
    torch = pytest.importorskip("torch")
    return {"input_ids": torch.tensor([[1, 2, 3, 4]])}


@pytest.mark.parametrize(("family", "model_id"), _DECODER_CASES)  # type: ignore[misc]
def test_real_decoder_adapter_matrix_caches_head_components_and_patches(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id)
    try:
        cache_layers = tuple(f"layer_0.{component}" for component in _COMMON_COMPONENTS)
        output, cache = wrapper.run_with_cache({"text": _TEXT}, layers=cache_layers)

        assert output.logits.ndim == 3
        assert set(cache_layers) <= set(cache)
        for component in _HEAD_COMPONENTS:
            activation = cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))
            assert activation.shape[0] == 1
            assert activation.shape[2] >= 1

        clean_cache = ActivationCache(cache)
        _assert_one_finite_result(
            get_act_patch_resid_pre(
                wrapper,
                {"text": "SafeLens checks a corrupted decoder adapter matrix."},
                clean_cache,
                _metric,
                layers=[0],
                positions=[0],
                cache_layers=[],
                return_details=True,
            )
        )
        _assert_one_finite_result(
            get_act_patch_attn_head_out_by_pos(
                wrapper,
                {"text": "SafeLens checks a corrupted decoder adapter matrix."},
                clean_cache,
                _metric,
                layers=[0],
                positions=[0],
                heads=[0],
                cache_layers=[],
                return_details=True,
            )
        )
        _attention_output, attention_cache = wrapper.run_with_cache(
            {"text": _TEXT},
            layers=("layer_0.pattern", "layer_0.attn_scores"),
        )
        for component in ("pattern", "attn_scores"):
            activation = attention_cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))
            assert activation.shape[0] == 1
    finally:
        wrapper.remove_hooks()


@pytest.mark.parametrize(("family", "model_id"), _TOKEN_ID_DECODER_CASES)  # type: ignore[misc]
def test_real_decoder_adapter_matrix_allows_token_id_batches_without_tokenizer(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id)
    batch = _token_id_batch()
    try:
        wrapper.tokenizer = None
        assert wrapper.tokenizer is None
        cache_layers = tuple(f"layer_0.{component}" for component in _COMMON_COMPONENTS)
        output, cache = wrapper.run_with_cache(batch, layers=cache_layers)

        assert output.logits.ndim == 3
        assert set(cache_layers) <= set(cache)
        for component in _HEAD_COMPONENTS:
            activation = cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))

        clean_cache = ActivationCache(cache)
        _assert_one_finite_result(
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
        with pytest.raises(ValueError, match="did not load a tokenizer"):
            wrapper.run_with_cache({"text": "needs tokenizer"}, layers=("layer_0.resid_pre",))
    finally:
        wrapper.remove_hooks()


@pytest.mark.parametrize(("family", "model_id"), _DECODER_CASES)  # type: ignore[misc]
def test_real_decoder_adapter_matrix_caches_attention_pattern_and_scores(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id)
    try:
        output, cache = wrapper.run_with_cache(
            {"text": _TEXT},
            layers=("layer_0.pattern", "layer_0.attn_scores"),
        )

        assert output.logits.ndim == 3
        for component in ("pattern", "attn_scores"):
            activation = cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))
            assert activation.shape[0] == 1
            assert activation.shape[-1] == activation.shape[-2]
    finally:
        wrapper.remove_hooks()


@pytest.mark.parametrize(("family", "model_id"), _ENCODER_CASES)  # type: ignore[misc]
def test_real_encoder_adapter_matrix_caches_head_components_and_patches(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    wrapper = _load_wrapper(model_id, source="transformer_lens")
    try:
        cache_layers = tuple(f"layer_0.{component}" for component in _COMMON_COMPONENTS)
        output, cache = wrapper.run_with_cache({"text": _TEXT}, layers=cache_layers)

        assert output.last_hidden_state.ndim == 3
        assert set(cache_layers) <= set(cache)
        for component in _HEAD_COMPONENTS:
            activation = cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))
            assert activation.shape[0] == 1

        clean_cache = ActivationCache(cache)
        _assert_one_finite_result(
            get_act_patch_resid_pre(
                wrapper,
                {"text": "SafeLens checks a corrupted encoder adapter matrix."},
                clean_cache,
                _metric,
                layers=[0],
                positions=[0],
                cache_layers=[],
                return_details=True,
            )
        )
        _assert_one_finite_result(
            get_act_patch_attn_head_out_by_pos(
                wrapper,
                {"text": "SafeLens checks a corrupted encoder adapter matrix."},
                clean_cache,
                _metric,
                layers=[0],
                positions=[0],
                heads=[0],
                cache_layers=[],
                return_details=True,
            )
        )
        _attention_output, attention_cache = wrapper.run_with_cache(
            {"text": _TEXT},
            layers=("layer_0.pattern", "layer_0.attn_scores"),
        )
        for component in ("pattern", "attn_scores"):
            activation = attention_cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))
            assert activation.shape[0] == 1
    finally:
        wrapper.remove_hooks()


@pytest.mark.parametrize(("family", "model_id"), _AUDIO_CASES)  # type: ignore[misc]
def test_real_audio_adapter_matrix_caches_head_components_and_patches(
    family: str,
    model_id: str,
) -> None:
    _skip_unless_enabled()
    np = pytest.importorskip("numpy")
    wrapper = _load_wrapper(model_id, source="transformer_lens")
    audio = np.zeros(4000, dtype=np.float32)
    batch = {"audio": audio, "sampling_rate": 16000}
    try:
        cache_layers = tuple(f"layer_0.{component}" for component in _COMMON_COMPONENTS)
        output, cache = wrapper.run_with_cache(batch, layers=cache_layers)

        assert output.last_hidden_state.ndim == 3
        assert set(cache_layers) <= set(cache)
        for component in _HEAD_COMPONENTS:
            activation = cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))
            assert activation.shape[0] == 1

        clean_cache = ActivationCache(cache)
        _assert_one_finite_result(
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
        _assert_one_finite_result(
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
        _attention_output, attention_cache = wrapper.run_with_cache(
            batch,
            layers=("layer_0.pattern", "layer_0.attn_scores"),
        )
        for component in ("pattern", "attn_scores"):
            activation = attention_cache[f"layer_0.{component}"]
            assert activation.ndim == 4, (family, component, tuple(activation.shape))
            assert activation.shape[0] == 1
    finally:
        wrapper.remove_hooks()
