from __future__ import annotations

# ruff: noqa: E402
import argparse
import gc
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.core.hooks import ActivationCache
from SafeLens.core.patching import PatchSpec, run_activation_patch
from SafeLens.explorer_model import load_explorer_hf_model
from SafeLens.utils import HuggingFaceModelWrapper


def main() -> None:
    parser = argparse.ArgumentParser(description="Run aligned activation patching for Explorer.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    run = payload["run"]
    request = payload["request"]
    wrapper = _load_wrapper(str(run["modelName"]))
    try:
        clean_tokens = wrapper.to_tokens(str(run["prompt"]), prepend_bos=False)
        corrupted_tokens = wrapper.to_tokens(str(request["corruptedPrompt"]), prepend_bos=False)
        clean_ids = _flat_token_ids(clean_tokens)
        corrupted_ids = _flat_token_ids(corrupted_tokens)
        expected_ids = [int(token["tokenId"]) for token in run["tokens"]]
        if clean_ids != expected_ids:
            raise ValueError("Clean prompt token IDs no longer match the source Explorer artifact.")
        if len(clean_ids) != len(corrupted_ids):
            raise ValueError("Clean and corrupted prompts must have the same token count.")

        component = str(request["component"])
        head = int(request["head"]) if request.get("head") is not None else None
        if component == "z" and head is None:
            raise ValueError("Attention-head patching requires a head index.")
        layers = [int(layer) for layer in request["layers"]]
        positions = [int(position) for position in request["positions"]]
        target_token_id = int(request["targetTokenId"])
        activation_names = [f"layer_{layer}.{component}" for layer in layers]
        clean_logits, clean_cache_value = wrapper.run_with_cache(
            {"input_ids": clean_tokens},
            layers=activation_names,
            return_type="logits",
        )
        clean_cache = cast(ActivationCache, clean_cache_value)
        corrupted_logits, _ = wrapper.run_with_cache(
            {"input_ids": corrupted_tokens},
            layers=[],
            return_type="logits",
        )
        clean_score = _target_logit(clean_logits, target_token_id)
        corrupted_score = _target_logit(corrupted_logits, target_token_id)

        def target_logit(logits: Any) -> float:
            return _target_logit(logits, target_token_id)

        cells: list[dict[str, Any]] = []
        denominator = clean_score - corrupted_score
        for layer in layers:
            activation_name = f"layer_{layer}.{component}"
            for position in positions:
                result = run_activation_patch(
                    wrapper,
                    {"input_ids": corrupted_tokens},
                    clean_cache,
                    PatchSpec(
                        layer=activation_name,
                        activation_name=activation_name,
                        target_index=_patch_index(component, position, head),
                        source_index=_patch_index(component, position, head),
                    ),
                    target_logit,
                )
                patched_score = float(result.metric)
                causal_effect = patched_score - corrupted_score
                recovery = (
                    None
                    if math.isclose(denominator, 0.0, abs_tol=1e-10)
                    else 100.0 * causal_effect / denominator
                )
                cells.append(
                    {
                        "layer": layer,
                        "tokenIndex": position,
                        "patchedScore": round(patched_score, 10),
                        "causalEffect": round(causal_effect, 10),
                        "recoveryPercentage": (None if recovery is None else round(recovery, 8)),
                        "sourceKey": _patch_source_key(activation_name, head),
                    }
                )

        tokenizer = wrapper.tokenizer
        corrupted_rows = [
            {
                "index": index,
                "tokenId": token_id,
                "text": str(tokenizer.decode([token_id], clean_up_tokenization_spaces=False)),
                "changed": token_id != clean_ids[index],
            }
            for index, token_id in enumerate(corrupted_ids)
        ]
        target_text = str(tokenizer.decode([target_token_id], clean_up_tokenization_spaces=False))
        derived = _merge_patching_result(
            run,
            run_id=args.run_id,
            corrupted_prompt=str(request["corruptedPrompt"]),
            component=component,
            head=head,
            target_token_id=target_token_id,
            target_token_text=target_text,
            layers=layers,
            positions=positions,
            corrupted_tokens=corrupted_rows,
            clean_score=clean_score,
            corrupted_score=corrupted_score,
            cells=cells,
        )
    finally:
        wrapper.remove_hooks()
        del wrapper
        gc.collect()
        _empty_cuda_cache()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(derived, indent=2), encoding="utf-8")


def _load_wrapper(model_id: str) -> HuggingFaceModelWrapper:
    cache_dir = os.environ.get(
        "SAFELENS_EXPLORER_MODEL_CACHE",
        ".cache/safelens/local-explorer-real-flow",
    )
    return load_explorer_hf_model(model_id, cache_dir=cache_dir)


def _complete_hf_snapshot(model_id: str, cache_dir: str) -> Path | None:
    repository = Path(cache_dir) / f"models--{model_id.replace('/', '--')}"
    reference = repository / "refs" / "main"
    if not reference.is_file():
        return None
    revision = reference.read_text(encoding="utf-8").strip()
    snapshot = repository / "snapshots" / revision
    if (
        not (snapshot / "config.json").is_file()
        or not (snapshot / "tokenizer_config.json").is_file()
    ):
        return None
    weight_files: list[Path] = []
    for index_name in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        index_path = snapshot / index_name
        if not index_path.is_file():
            continue
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            filenames = set(index["weight_map"].values())
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            return None
        if not filenames or not all(isinstance(name, str) and name for name in filenames):
            return None
        weight_files.extend(snapshot / name for name in sorted(filenames))
    if not weight_files:
        weight_files = list(snapshot.glob("*.safetensors")) + list(
            snapshot.glob("pytorch_model*.bin")
        )
    if not weight_files or not all(
        path.is_file() and path.stat().st_size > 0 for path in weight_files
    ):
        return None
    return snapshot


def _empty_cuda_cache() -> None:
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _target_logit(logits: Any, target_token_id: int) -> float:
    try:
        value = logits[0, -1, target_token_id]
    except (IndexError, TypeError):
        value = logits[0][-1][target_token_id]
    item = getattr(value, "item", None)
    return float(item() if callable(item) else value)


def _flat_token_ids(tokens: Any) -> list[int]:
    value = tokens.detach().cpu().tolist() if hasattr(tokens, "detach") else tokens
    if value and isinstance(value[0], list):
        if len(value) != 1:
            raise ValueError("Patching jobs support one prompt at a time.")
        value = value[0]
    return [int(token_id) for token_id in value]


def _patch_index(component: str, position: int, head: int | None) -> tuple[Any, ...]:
    if component == "z":
        if head is None:
            raise ValueError("Attention-head patching requires a head index.")
        return (slice(None), position, head, slice(None))
    return (slice(None), position, slice(None))


def _patch_source_key(activation_name: str, head: int | None) -> str:
    return f"{activation_name}[head={head}]" if head is not None else activation_name


def _merge_patching_result(
    run: dict[str, Any],
    *,
    run_id: str,
    corrupted_prompt: str,
    component: str,
    head: int | None,
    target_token_id: int,
    target_token_text: str,
    layers: list[int],
    positions: list[int],
    corrupted_tokens: list[dict[str, Any]],
    clean_score: float,
    corrupted_score: float,
    cells: list[dict[str, Any]],
) -> dict[str, Any]:
    source_run = {"runId": run["runId"], "sampleId": run["sampleId"]}
    denominator = clean_score - corrupted_score
    head_selector = f",head={head}" if head is not None else ""
    source_key = f"activation_patching.{component}[target={target_token_id}{head_selector}]"
    run["patching"] = {
        "cleanPrompt": run["prompt"],
        "corruptedPrompt": corrupted_prompt,
        "component": component,
        **({"head": head} if head is not None else {}),
        "targetTokenId": target_token_id,
        "targetTokenText": target_token_text,
        "cleanScore": round(float(clean_score), 10),
        "corruptedScore": round(float(corrupted_score), 10),
        "denominator": round(float(denominator), 10),
        "layers": layers,
        "positions": positions,
        "corruptedTokens": corrupted_tokens,
        "cells": cells,
        "sourceRun": source_run,
        "sourceKey": source_key,
    }
    provenance = run.setdefault("metricProvenance", {})
    provenance["patchingCausalEffect"] = {
        "label": "Causal effect",
        "method": "Clean activation replacement into the positionally aligned corrupted run",
        "semantics": "Patched target-token logit minus the corrupted target-token logit.",
        "normalization": "none; raw logit difference",
        "kind": "causal",
    }
    provenance["patchingRecovery"] = {
        "label": "Recovery",
        "method": "Activation patching recovery ratio",
        "semantics": "Causal effect divided by the clean-corrupted target-logit difference.",
        "normalization": (
            "percentage; unavailable when the clean-corrupted denominator is near zero"
        ),
        "kind": "causal",
    }
    provenance["patchingPatchedScore"] = {
        "label": "Patched score",
        "method": "Activation patching forward pass",
        "semantics": "Raw target-token logit after one clean activation replacement.",
        "normalization": "none; raw logit",
        "kind": "causal",
    }
    run["runId"] = run_id
    metadata = run.setdefault("metadata", {})
    jobs = list(metadata.get("patchingJobs", []))
    jobs.append(
        {
            "jobVersion": "1.0",
            "method": "activation_replacement",
            "component": component,
            **({"head": head} if head is not None else {}),
            "layers": layers,
            "positions": positions,
            "targetTokenId": target_token_id,
            "targetTokenText": target_token_text,
            "cleanScore": clean_score,
            "corruptedScore": corrupted_score,
            "sourceRun": source_run,
            "sourceKey": source_key,
        }
    )
    metadata["patchingJobs"] = jobs
    metadata["parentRun"] = source_run
    return run


if __name__ == "__main__":
    main()
