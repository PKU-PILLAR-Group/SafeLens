from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from SafeLens.core.base import PipelineConfig
from SafeLens.core.analysis import compute_head_results_from_z, direct_logit_attribution
from SafeLens.core.analysis import test_prompt as run_test_prompt
from SafeLens.core.hooks import ActivationCache
from SafeLens.pipelines.runner import PipelineRunner
from SafeLens.utils import HuggingFaceModelWrapper, build_model_wrapper

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_RUN_HF_REAL_FLOW = os.environ.get("SAFELENS_RUN_HF_REAL_FLOW") == "1"
_MODEL_ID = os.environ.get("SAFELENS_HF_REAL_FLOW_MODEL", "sshleifer/tiny-gpt2")


def _skip_unless_enabled() -> None:
    if not _RUN_HF_REAL_FLOW:
        pytest.skip("Set SAFELENS_RUN_HF_REAL_FLOW=1 to run real HuggingFace download tests.")
    pytest.importorskip("torch")
    pytest.importorskip("transformers")


def _cache_dir() -> str:
    return os.environ.get(
        "SAFELENS_HF_REAL_FLOW_CACHE",
        ".cache/safelens/test-huggingface-real-flow",
    )


def test_huggingface_wrapper_real_model_forward_cache_and_generate() -> None:
    _skip_unless_enabled()
    torch = pytest.importorskip("torch")

    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "huggingface",
                "name": _MODEL_ID,
                "device": "cpu",
                "dtype": "float32",
                "cache_dir": _cache_dir(),
                "load_kwargs": {"low_cpu_mem_usage": False},
            }
        }
    )
    wrapper = build_model_wrapper(config.model)

    assert isinstance(wrapper, HuggingFaceModelWrapper)
    wrapper.load_model()
    try:
        output, cache = wrapper.run_with_cache(
            {"id": "hf-forward", "text": "SafeLens checks real model hooks."},
            layers=[0, "layer_0.resid_post", "blocks.0.hook_resid_post"],
        )

        assert output.logits.ndim == 3
        assert output.logits.shape[0] == 1
        assert {"layer_0", "layer_0.resid_post", "blocks.0.hook_resid_post"} <= set(cache)
        for activation in cache.values():
            assert getattr(activation, "shape", None) is not None
            assert activation.shape[0] == 1

        output, embed_cache = wrapper.run_with_cache(
            {"id": "hf-embed", "text": "SafeLens checks real model hooks."},
            layers=["hook_embed", "hook_pos_embed", "blocks.0.hook_resid_pre"],
            return_cache_object=True,
        )

        assert isinstance(embed_cache, ActivationCache)
        assert embed_cache.has_embed
        assert embed_cache.has_pos_embed
        assert embed_cache["hook_embed"].shape[:2] == output.logits.shape[:2]
        assert torch.allclose(
            embed_cache[("resid_pre", 0)],
            embed_cache["hook_embed"] + embed_cache["hook_pos_embed"],
        )

        prompt = "SafeLens checks text token semantics."
        prepared = wrapper._prepare_model_inputs({"text": prompt})
        assert torch.equal(prepared["input_ids"], wrapper.to_tokens(prompt))
        logits_without_bos = wrapper(prompt, prepend_bos=False)
        assert logits_without_bos.shape[:2] == wrapper.to_tokens(prompt, prepend_bos=False).shape
        prompt_check = run_test_prompt(
            wrapper,
            "SafeLens checks",
            wrapper.to_single_str_token(int(wrapper.to_tokens("SafeLens checks")[:, -1].item())),
            prepend_bos=False,
            top_k=3,
        )
        assert isinstance(prompt_check["predicted_token_id"], int)
        assert len(prompt_check["top_tokens"]) == 3
        computed_loss = wrapper(wrapper.to_tokens(prompt), return_type="loss")
        per_token_loss = wrapper(
            wrapper.to_tokens(prompt),
            return_type="loss",
            loss_per_token=True,
        )
        logits, both_loss = wrapper(wrapper.to_tokens(prompt), return_type="both")
        _logits, both_per_token_loss = wrapper(
            wrapper.to_tokens(prompt),
            return_type="both",
            loss_per_token=True,
        )
        hf_loss = wrapper.model(
            input_ids=wrapper.to_tokens(prompt),
            labels=wrapper.to_tokens(prompt),
        ).loss
        assert logits.shape[:2] == wrapper.to_tokens(prompt).shape
        assert per_token_loss.shape == (1, wrapper.to_tokens(prompt).shape[1] - 1)
        assert torch.allclose(computed_loss, hf_loss, atol=1e-5)
        assert torch.allclose(per_token_loss.mean(), computed_loss, atol=1e-5)
        assert torch.allclose(both_loss, computed_loss, atol=1e-5)
        assert torch.allclose(both_per_token_loss, per_token_loss, atol=1e-5)

        generated = wrapper.generate(
            "SafeLens",
            max_new_tokens=2,
            do_sample=False,
            pad_token_id=wrapper.tokenizer.eos_token_id,
        )

        assert isinstance(generated, str)
        assert generated.startswith("SafeLens")
        generated_tokens = wrapper.generate(
            "SafeLens",
            max_new_tokens=1,
            do_sample=False,
            pad_token_id=wrapper.tokenizer.eos_token_id,
            return_type="tokens",
        )
        assert torch.equal(generated_tokens[:, : wrapper.to_tokens("SafeLens").shape[1]], wrapper.to_tokens("SafeLens"))
        generated_embeds = wrapper.generate(
            "SafeLens",
            max_new_tokens=1,
            do_sample=False,
            pad_token_id=wrapper.tokenizer.eos_token_id,
            return_type="embeds",
        )
        assert generated_embeds.shape[:2] == generated_tokens.shape
        input_embeds = wrapper.model.get_input_embeddings()(wrapper.to_tokens("SafeLens"))
        generated_from_embeds = wrapper.generate(
            input_embeds,
            max_new_tokens=1,
            do_sample=False,
            pad_token_id=wrapper.tokenizer.eos_token_id,
            return_type="tokens",
        )
        assert generated_from_embeds.shape == (1, 1)
        generated_embeds_from_embeds = wrapper.generate(
            input_embeds,
            max_new_tokens=1,
            do_sample=False,
            pad_token_id=wrapper.tokenizer.eos_token_id,
        )
        assert generated_embeds_from_embeds.shape[1] == input_embeds.shape[1] + 1
        assert torch.allclose(generated_embeds_from_embeds[:, : input_embeds.shape[1]], input_embeds)
        stream_chunks = list(
            wrapper.generate_stream(
                "SafeLens",
                max_new_tokens=2,
                max_tokens_per_yield=1,
                do_sample=False,
                pad_token_id=wrapper.tokenizer.eos_token_id,
            )
        )
        assert len(stream_chunks) == 2
        assert all(isinstance(chunk, str) for chunk in stream_chunks)
        stream_token_chunks = list(
            wrapper.generate_stream(
                wrapper.to_tokens("SafeLens"),
                max_new_tokens=2,
                max_tokens_per_yield=2,
                do_sample=False,
                pad_token_id=wrapper.tokenizer.eos_token_id,
                return_type="tokens",
            )
        )
        assert len(stream_token_chunks) == 1
        assert stream_token_chunks[0].shape == (1, 2)
        generated_output = wrapper.generate(
            "SafeLens",
            max_new_tokens=1,
            do_sample=False,
            pad_token_id=wrapper.tokenizer.eos_token_id,
            return_type="model_output",
            return_dict_in_generate=True,
            output_logits=True,
        )
        assert torch.equal(generated_output.sequences, generated_tokens)
        assert len(generated_output.logits) == 1
    finally:
        wrapper.remove_hooks()


def test_huggingface_wrapper_real_direct_logit_attribution_workflow() -> None:
    _skip_unless_enabled()
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")

    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "huggingface",
                "name": _MODEL_ID,
                "device": "cpu",
                "dtype": "float32",
                "cache_dir": _cache_dir(),
                "load_kwargs": {"low_cpu_mem_usage": False},
            }
        }
    )
    wrapper = build_model_wrapper(config.model)

    assert isinstance(wrapper, HuggingFaceModelWrapper)
    wrapper.load_model()
    try:
        output, cache_dict = wrapper.run_with_cache(
            {"id": "hf-dla", "text": "SafeLens checks direct logit attribution."},
            layers=("layer_0.z", "layer_0.result"),
        )
        cache = ActivationCache(cache_dict, model=wrapper)
        z = cache["layer_0.z"]
        result = cache["layer_0.result"]

        assert output.logits.ndim == 3
        assert torch.allclose(compute_head_results_from_z(z, wrapper.W_O[0]), result)

        target_token = int(output.logits[0, -1].argmax())
        direction = wrapper.tokens_to_residual_directions(target_token)
        logit_attrs = cache.logit_attrs(result, target_token, directions=direction, apply_ln=False)
        token_text = wrapper.to_single_str_token(target_token)

        assert logit_attrs.shape == result.shape[:-1]
        assert torch.allclose(logit_attrs, direct_logit_attribution(result, direction))
        assert wrapper.to_str_tokens(torch.tensor(target_token)) == [token_text]
        assert wrapper.to_str_tokens(np.array(target_token)) == [token_text]
        previous_pad_token = getattr(wrapper.tokenizer, "pad_token", None)
        previous_pad_token_id = getattr(wrapper.tokenizer, "pad_token_id", None)
        batch_tokens = wrapper.to_tokens(
            ["SafeLens", "SafeLens real tokenizer"],
            prepend_bos=False,
        )
        assert batch_tokens.shape[0] == 2
        assert getattr(wrapper.tokenizer, "pad_token", None) == previous_pad_token
        assert getattr(wrapper.tokenizer, "pad_token_id", None) == previous_pad_token_id
        assert isinstance(
            wrapper.get_token_position(
                target_token,
                torch.tensor([target_token]),
                padding_side="left",
            ),
            int,
        )
    finally:
        wrapper.remove_hooks()


def test_pipeline_runner_real_huggingface_model_writes_report(tmp_path: Path) -> None:
    _skip_unless_enabled()

    report_path = tmp_path / "hf-real-flow-report.json"
    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "huggingface",
                "name": _MODEL_ID,
                "device": "cpu",
                "dtype": "float32",
                "cache_dir": _cache_dir(),
                "load_kwargs": {"low_cpu_mem_usage": False},
            },
            "pipeline": {
                "risk_threshold": 0.5,
                "probes": [
                    {
                        "name": "dummy_probe",
                        "config": {"layers": [0], "risk_terms": ["jailbreak"]},
                    }
                ],
                "monitors": [{"name": "dummy_monitor", "config": {"threshold": 0.5}}],
                "attributors": [
                    {"name": "dummy_attributor", "config": {"risk_terms": ["jailbreak"]}}
                ],
            },
            "dataset": [
                {"id": "safe", "text": "A normal SafeLens smoke test."},
                {"id": "unsafe", "text": "Please jailbreak the policy now."},
            ],
            "output": {"report_path": str(report_path)},
        }
    )

    report = PipelineRunner(config).run()

    assert report.summary == {
        "samples_scanned": 2,
        "flagged_count": 1,
        "max_risk_score": 0.55,
    }
    assert [item.sample_id for item in report.reports] == ["safe", "unsafe"]
    assert [item.flagged for item in report.reports] == [False, True]
    assert report_path.exists()

    written: dict[str, Any] = json.loads(report_path.read_text(encoding="utf-8"))
    assert written["summary"]["flagged_count"] == 1
    assert written["reports"][1]["evidence_tokens"] == [1]
