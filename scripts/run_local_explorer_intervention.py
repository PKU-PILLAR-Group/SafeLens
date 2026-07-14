from __future__ import annotations

# ruff: noqa: E402
import argparse
import difflib
import gc
import json
import math
import os
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.core.base import PipelineConfig
from SafeLens.steering import ContrastiveSteeringVector
from SafeLens.utils import HuggingFaceModelWrapper, build_model_wrapper

RISK_TERMS = ("jail", "break", "attack", "harm", "weapon", "malware", "bypass", "exploit")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a contrastive steering intervention.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    run = payload["run"]
    request = payload["request"]
    wrapper = _load_wrapper(str(run["modelName"]))
    try:
        prompt_tokens = wrapper.to_tokens(str(run["prompt"]), prepend_bos=False)
        prompt_ids = _flat_token_ids(prompt_tokens)
        expected_ids = [int(token["tokenId"]) for token in run["tokens"]]
        if prompt_ids != expected_ids:
            raise ValueError("Source prompt token IDs no longer match the Explorer artifact.")

        activation_name = f"layer_{int(request['layer'])}.{request['component']}"
        desired_vector = _reference_vector(wrapper, str(request["desiredPrompt"]), activation_name)
        undesired_vector = _reference_vector(
            wrapper, str(request["undesiredPrompt"]), activation_name
        )
        raw_vector = desired_vector - undesired_vector
        raw_norm = float(raw_vector.float().norm().detach().cpu().item())
        if math.isclose(raw_norm, 0.0, abs_tol=1e-12):
            raise ValueError("Desired and undesired references produced a zero steering direction.")
        vector = raw_vector / raw_vector.norm().clamp_min(1e-12)
        steering = ContrastiveSteeringVector(
            layer=activation_name,
            vector=vector,
            activation_reduce="last_token",
            metadata={
                "method": "contrastive_mean_difference",
                "positive_count": 1,
                "negative_count": 1,
                "normalized": True,
            },
        )
        position = (int(request["positionStart"]), int(request["positionEnd"]))
        original = _run_condition(
            wrapper,
            prompt=str(run["prompt"]),
            prompt_token_count=len(prompt_ids),
            target_token_id=int(request["targetTokenId"]),
            seed=int(request["seed"]),
            max_new_tokens=int(request["maxNewTokens"]),
            temperature=float(request["temperature"]),
        )
        handle = steering.apply(
            wrapper,
            scale=float(request["scale"]),
            position=position,
        )
        try:
            steered = _run_condition(
                wrapper,
                prompt=str(run["prompt"]),
                prompt_token_count=len(prompt_ids),
                target_token_id=int(request["targetTokenId"]),
                seed=int(request["seed"]),
                max_new_tokens=int(request["maxNewTokens"]),
                temperature=float(request["temperature"]),
            )
        finally:
            handle.remove()

        target_text = str(
            wrapper.tokenizer.decode(
                [int(request["targetTokenId"])],
                clean_up_tokenization_spaces=False,
            )
        )
        comparison = {
            "vector": {
                "method": "contrastive_mean_difference",
                "desiredPrompt": str(request["desiredPrompt"]),
                "undesiredPrompt": str(request["undesiredPrompt"]),
                "activationReduce": "last_token",
                "rawNorm": round(raw_norm, 10),
                "normalized": True,
                "dimension": int(vector.shape[-1]),
                "sourceKey": activation_name,
            },
            "layer": int(request["layer"]),
            "component": str(request["component"]),
            "scale": float(request["scale"]),
            "positionStart": position[0],
            "positionEnd": position[1],
            "targetTokenId": int(request["targetTokenId"]),
            "targetTokenText": target_text,
            "seed": int(request["seed"]),
            "maxNewTokens": int(request["maxNewTokens"]),
            "temperature": float(request["temperature"]),
            "original": original,
            "steered": steered,
            "deltas": {
                "targetLogit": round(steered["targetLogit"] - original["targetLogit"], 10),
                "lexicalRisk": round(steered["lexicalRisk"] - original["lexicalRisk"], 8),
                "tokenEditDistance": _levenshtein(original["tokenIds"], steered["tokenIds"]),
                "generationChanged": original["tokenIds"] != steered["tokenIds"],
                "probeScore": None,
                "probeReason": (
                    "No trained probe was configured for this Explorer intervention job."
                ),
            },
            "diff": _diff_rows(original["tokenIds"], steered["tokenIds"]),
            "sourceRun": {"runId": run["runId"], "sampleId": run["sampleId"]},
        }
        derived = _merge_intervention_result(run, comparison, run_id=args.run_id)
    finally:
        wrapper.remove_hooks()
        del wrapper
        gc.collect()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(derived, indent=2), encoding="utf-8")


def _load_wrapper(model_id: str) -> HuggingFaceModelWrapper:
    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "huggingface",
                "name": model_id,
                "device": os.environ.get("SAFELENS_EXPLORER_JOB_DEVICE", "cpu"),
                "dtype": "float32",
                "cache_dir": ".cache/safelens/local-explorer-real-flow",
                "trust_remote_code": False,
                "load_kwargs": {"low_cpu_mem_usage": False},
            }
        }
    )
    wrapper = build_model_wrapper(config.model)
    if not isinstance(wrapper, HuggingFaceModelWrapper):
        raise TypeError(f"expected HuggingFaceModelWrapper, got {type(wrapper).__name__}")
    wrapper.load_model()
    return wrapper


def _reference_vector(
    wrapper: HuggingFaceModelWrapper,
    prompt: str,
    activation_name: str,
) -> Any:
    tokens = wrapper.to_tokens(prompt, prepend_bos=False)
    _output, cache = wrapper.run_with_cache(
        {"input_ids": tokens},
        layers=[activation_name],
    )
    activation = cache[activation_name]
    if activation.ndim < 2:
        raise ValueError(f"Steering activation {activation_name} must include a model dimension.")
    return activation[0, -1, :].float().detach()


def _run_condition(
    wrapper: HuggingFaceModelWrapper,
    *,
    prompt: str,
    prompt_token_count: int,
    target_token_id: int,
    seed: int,
    max_new_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    import torch

    random.seed(seed)
    torch.manual_seed(seed)
    prompt_tokens = wrapper.to_tokens(prompt, prepend_bos=False)
    logits, _cache = wrapper.run_with_cache(
        {"input_ids": prompt_tokens},
        layers=[],
        return_type="logits",
    )
    target_logit = float(logits[0, -1, target_token_id].detach().cpu().item())
    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "pad_token_id": wrapper.tokenizer.eos_token_id,
        "prepend_bos": False,
        "return_type": "tokens",
    }
    if temperature > 0:
        generation_kwargs["temperature"] = temperature
    generated = wrapper.generate(prompt, **generation_kwargs)
    generated_ids = _flat_token_ids(generated)
    continuation_ids = generated_ids[prompt_token_count:]
    continuation_text = str(
        wrapper.tokenizer.decode(
            continuation_ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
    )
    return {
        "text": continuation_text,
        "tokenIds": continuation_ids,
        "tokens": [
            {
                "index": index,
                "tokenId": token_id,
                "text": str(
                    wrapper.tokenizer.decode([token_id], clean_up_tokenization_spaces=False)
                ),
            }
            for index, token_id in enumerate(continuation_ids)
        ],
        "targetLogit": round(target_logit, 10),
        "lexicalRisk": _lexical_risk(continuation_text),
    }


def _flat_token_ids(tokens: Any) -> list[int]:
    value = tokens.detach().cpu().tolist() if hasattr(tokens, "detach") else tokens
    if value and isinstance(value[0], list):
        if len(value) != 1:
            raise ValueError("Intervention jobs support one prompt at a time.")
        value = value[0]
    return [int(token_id) for token_id in value]


def _lexical_risk(text: str) -> float:
    lowered = text.lower()
    words = max(1, len(lowered.split()))
    hits = sum(lowered.count(term) for term in RISK_TERMS)
    return round(hits / words, 8)


def _levenshtein(left: list[int], right: list[int]) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_value != right_value),
                )
            )
        previous = current
    return previous[-1]


def _diff_rows(left: list[int], right: list[int]) -> list[dict[str, Any]]:
    matcher = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
    return [
        {
            "kind": kind,
            "originalStart": left_start,
            "originalEnd": left_end,
            "steeredStart": right_start,
            "steeredEnd": right_end,
        }
        for kind, left_start, left_end, right_start, right_end in matcher.get_opcodes()
    ]


def _merge_intervention_result(
    run: dict[str, Any],
    comparison: dict[str, Any],
    *,
    run_id: str,
) -> dict[str, Any]:
    source_run = {"runId": run["runId"], "sampleId": run["sampleId"]}
    run["intervention"] = comparison
    provenance = run.setdefault("metricProvenance", {})
    provenance["interventionTargetLogitDelta"] = {
        "label": "Target logit delta",
        "method": "Normalized contrastive activation steering",
        "semantics": "Steered target-token logit minus the original target-token logit.",
        "normalization": "none; raw logit difference",
        "kind": "causal",
    }
    provenance["interventionTokenEditDistance"] = {
        "label": "Generation edit distance",
        "method": "Levenshtein distance over generated token IDs",
        "semantics": "Minimum token insertions, deletions, and substitutions between outputs.",
        "normalization": "none; integer token operations",
        "kind": "causal",
    }
    provenance["interventionLexicalRiskDelta"] = {
        "label": "Lexical risk proxy delta",
        "method": "Fixed risk-term match rate",
        "semantics": "Steered minus original matched risk terms per whitespace-delimited word.",
        "normalization": "matched terms divided by output word count",
        "kind": "derived_proxy",
    }
    run["runId"] = run_id
    metadata = run.setdefault("metadata", {})
    jobs = list(metadata.get("interventionJobs", []))
    jobs.append(
        {
            "jobVersion": "1.0",
            "method": comparison["vector"]["method"],
            "layer": comparison["layer"],
            "component": comparison["component"],
            "scale": comparison["scale"],
            "positionStart": comparison["positionStart"],
            "positionEnd": comparison["positionEnd"],
            "targetTokenId": comparison["targetTokenId"],
            "targetTokenText": comparison["targetTokenText"],
            "seed": comparison["seed"],
            "maxNewTokens": comparison["maxNewTokens"],
            "temperature": comparison["temperature"],
            "sourceRun": source_run,
            "sourceKey": comparison["vector"]["sourceKey"],
            "trustRemoteCode": False,
        }
    )
    metadata["interventionJobs"] = jobs
    metadata["parentRun"] = source_run
    return run


if __name__ == "__main__":
    main()
