from __future__ import annotations

# ruff: noqa: E402
import argparse
import gc
import json
import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.core.hooks import ActivationCache
from SafeLens.explorer_model import load_explorer_hf_model
from SafeLens.explorer_sae import neuronpedia_feature_info
from SafeLens.explorer_workers.run_local_explorer_intervention import (
    _flat_token_ids,
    _load_sae,
    _sae_decoder_direction,
    _sae_dtype,
    _sae_feature_width,
)
from SafeLens.sae_profiles import get_sae_profile


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover active Gemma Scope SAE features for an Explorer run."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = _discover(payload["run"], payload["request"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")


def _discover(run: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    wrapper = load_explorer_hf_model(str(run["modelName"]))
    try:
        profile = get_sae_profile(
            model_name=str(run["modelName"]),
            release=str(request["saeRelease"]),
            sae_id=str(request["saeId"]),
        )
        if profile is None:
            raise ValueError("Model, release, and SAE ID are not an enabled Gemma Scope profile.")
        if int(request["layer"]) != profile.layer or request["component"] != profile.component:
            raise ValueError("Gemma Scope profile does not match the requested layer and site.")

        prompt_tokens = wrapper.to_tokens(str(run["prompt"]), prepend_bos=False)
        prompt_ids = _flat_token_ids(prompt_tokens)
        expected_ids = [int(token["tokenId"]) for token in run["tokens"]]
        if prompt_ids != expected_ids:
            raise ValueError("Source prompt token IDs no longer match the Explorer artifact.")

        start = int(request["positionStart"])
        end = int(request["positionEnd"])
        if not 0 <= start < end <= len(prompt_ids):
            raise ValueError("Feature discovery range must stay inside the source prompt.")
        limit = int(request.get("limit", 8))
        if not 1 <= limit <= 20:
            raise ValueError("Feature discovery limit must be between 1 and 20.")

        sae = _load_sae(
            wrapper,
            release=profile.release,
            sae_id=profile.sae_id,
            expected_model_name=profile.model_name,
        )
        activation_name = f"layer_{profile.layer}.{profile.component}"
        _output, cache_value = wrapper.run_with_cache(
            {"input_ids": prompt_tokens},
            layers=[activation_name],
        )
        cache = cast(ActivationCache, cache_value)
        activation = cache[activation_name]
        if getattr(activation, "ndim", 0) < 3:
            raise ValueError("SAE discovery requires batched token activations.")
        selected = activation[0, start:end, :]
        decoder = _sae_decoder_direction(sae, 0)
        if int(selected.shape[-1]) != int(decoder.shape[-1]):
            raise ValueError(
                "SAE input width does not match the selected residual stream: "
                f"{decoder.shape[-1]} != {selected.shape[-1]}."
            )

        with torch.no_grad():
            encoded = (
                sae.encode(selected.to(device=decoder.device, dtype=_sae_dtype(sae)))
                .float()
                .detach()
                .cpu()
            )
        width = _sae_feature_width(sae)
        if encoded.ndim != 2 or int(encoded.shape[-1]) != width:
            raise ValueError("SAE encoder returned an unexpected feature matrix.")

        rows = _rank_feature_rows(encoded, run["tokens"], start=start, limit=limit)
        if not rows:
            return _result(run, profile, start, end, [])

        def enrich(row: dict[str, Any]) -> dict[str, Any]:
            info = neuronpedia_feature_info(
                model_name=profile.model_name,
                layer=profile.layer,
                sae_id=profile.sae_id,
                feature_index=int(row["featureIndex"]),
            )
            return {
                **row,
                "label": str(info["label"]),
                "source": str(info["source"]),
                "url": info.get("url"),
                "positiveTokens": list(info.get("positiveTokens", [])),
                "negativeTokens": list(info.get("negativeTokens", [])),
            }

        with ThreadPoolExecutor(max_workers=min(8, len(rows))) as executor:
            candidates = list(executor.map(enrich, rows))
        return _result(run, profile, start, end, candidates)
    finally:
        wrapper.remove_hooks()
        gc.collect()
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass


def _recommended_delta(max_activation: float) -> float:
    # A delta near the observed peak often changes logits without crossing a
    # greedy decoding boundary. Two peak activations produced visible text
    # changes in calibration runs while leaving a lower-impact preset useful.
    magnitude = min(1_000.0, max(100.0, 2.0 * max_activation))
    step = 5.0 if magnitude < 100 else 25.0 if magnitude < 500 else 50.0
    return float(math.ceil(magnitude / step) * step)


def _rank_feature_rows(
    encoded: torch.Tensor,
    tokens: list[dict[str, Any]],
    *,
    start: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Rank positive SAE features and retain the token evidence used for selection."""
    max_values, peak_offsets = encoded.max(dim=0)
    positive_indices = (max_values > 0).nonzero(as_tuple=False).flatten()
    if positive_indices.numel() == 0:
        return []
    ranked = positive_indices[
        max_values[positive_indices].argsort(descending=True)[:limit]
    ].tolist()
    rows: list[dict[str, Any]] = []
    for raw_index in ranked:
        feature_index = int(raw_index)
        values = encoded[:, feature_index]
        peak_token_index = start + int(peak_offsets[feature_index].item())
        max_activation = float(max_values[feature_index].item())
        rows.append(
            {
                "featureIndex": feature_index,
                "maxActivation": max_activation,
                "meanActivation": float(values.mean().item()),
                "activeTokenCount": int((values > 0).sum().item()),
                "peakTokenIndex": peak_token_index,
                "peakTokenText": str(tokens[peak_token_index]["text"]),
                "recommendedDelta": _recommended_delta(max_activation),
            }
        )
    return rows


def _result(
    run: dict[str, Any],
    profile: Any,
    start: int,
    end: int,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "runId": str(run["runId"]),
        "sampleId": str(run["sampleId"]),
        "modelName": profile.model_name,
        "layer": profile.layer,
        "component": profile.component,
        "release": profile.release,
        "saeId": profile.sae_id,
        "positionStart": start,
        "positionEnd": end,
        "candidates": candidates,
    }


if __name__ == "__main__":
    main()
