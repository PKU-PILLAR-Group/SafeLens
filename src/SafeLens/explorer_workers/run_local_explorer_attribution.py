from __future__ import annotations

# ruff: noqa: E402
import argparse
import gc
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.attribution import attribute_response_token_input
from SafeLens.explorer_model import load_explorer_hf_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Captum IG for one Explorer sample.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    job_input = json.loads(args.input.read_text(encoding="utf-8"))
    run = job_input["run"]
    request = job_input["request"]
    if run.get("modelName") != args.model:
        raise ValueError("Requested model does not match the source Explorer run.")
    wrapper = load_explorer_hf_model(args.model)
    try:
        result = attribute_response_token_input(
            wrapper,
            str(run["prompt"]),
            response=request["response"],
            target_response_index=int(request["targetResponseIndex"]),
            n_steps=int(request["nSteps"]),
            internal_batch_size=int(
                os.environ.get("SAFELENS_EXPLORER_ATTRIBUTION_INTERNAL_BATCH_SIZE", "1")
            ),
            baseline=request["baseline"],
            prepend_bos=False,
        )
        derived = _merge_result(
            run,
            result.model_dump(mode="json"),
            run_id=args.run_id,
            response=request["response"],
        )
    finally:
        wrapper.remove_hooks()
        del wrapper
        gc.collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(derived, indent=2), encoding="utf-8")


def _merge_result(
    run: dict[str, Any],
    result: dict[str, Any],
    *,
    run_id: str,
    response: str,
) -> dict[str, Any]:
    token_count = len(run["tokens"])
    normalized_values = [0.0] * token_count
    raw_values = [0.0] * token_count
    response_context_attributions: list[dict[str, Any]] = []
    for token in result["tokens"]:
        index = int(token["token_index"])
        if index >= token_count:
            response_context_attributions.append(
                {
                    "tokenIndex": index,
                    "tokenText": token.get("token_text"),
                    "tokenId": token.get("metadata", {}).get("token_id"),
                    "storedValue": float(token["score"]),
                    "rawValue": float(token.get("metadata", {}).get("raw_score", 0.0)),
                }
            )
            continue
        expected_id = int(run["tokens"][index]["tokenId"])
        observed_id = int(token.get("metadata", {}).get("token_id", expected_id))
        if expected_id != observed_id:
            raise ValueError(
                f"Prompt token alignment failed at position {index}: "
                f"Explorer token id {expected_id} != Captum token id {observed_id}."
            )
        normalized_values[index] = round(float(token["score"]), 8)
        raw_values[index] = round(float(token.get("metadata", {}).get("raw_score", 0.0)), 10)

    details = result["details"]
    target_text = details.get("target_token_text") or str(details["target_token_id"])
    source_key = (
        f"captum.layer_integrated_gradients[target={details['target_token_id']},"
        f"response_index={details['target_response_index']}]"
    )
    method = {
        "id": "integrated_gradients",
        "label": "Integrated Gradients",
        "description": (
            f"Signed input attribution to the logit for response token {target_text!r} at "
            f"response index {details['target_response_index']}."
        ),
        "evidenceKind": "causal",
        "signed": True,
        "normalization": (
            "raw embedding attribution; stored values normalized by max absolute over "
            "prompt plus preceding response context"
        ),
        "available": True,
        "rows": [
            {
                "layer": -1,
                "label": "Input",
                "values": normalized_values,
                "sourceKey": source_key,
            }
        ],
    }
    methods = [
        existing
        for existing in run.get("attributionMethods", [])
        if existing.get("id") != "integrated_gradients"
    ]
    methods.append(method)
    run["attributionMethods"] = methods
    tracks = [
        track
        for track in run.get("attributionTracks", [])
        if track.get("name") != "Integrated Gradients"
    ]
    tracks.append({"name": "Integrated Gradients", "values": normalized_values})
    run["attributionTracks"] = tracks
    run["metricProvenance"]["integratedGradients"] = {
        "label": "Integrated Gradients",
        "method": f"Captum LayerIntegratedGradients {importlib.metadata.version('captum')}",
        "semantics": "Signed contribution of preceding input tokens to one response-token logit.",
        "normalization": (
            "raw scores retained in job metadata; matrix stores the prompt slice of values "
            "max-absolute normalized across all preceding context"
        ),
        "kind": "causal",
    }
    source_run = {"runId": run["runId"], "sampleId": run["sampleId"]}
    run["runId"] = run_id
    metadata = run.setdefault("metadata", {})
    jobs = list(metadata.get("attributionJobs", []))
    jobs.append(
        {
            "jobVersion": "1.0",
            "method": "captum_layer_integrated_gradients",
            "methodVersion": importlib.metadata.version("captum"),
            "objective": details["objective"],
            "targetTokenId": details["target_token_id"],
            "targetTokenText": target_text,
            "targetResponseIndex": details["target_response_index"],
            "targetPosition": details["target_position"],
            "response": response,
            "baseline": details["baseline"],
            "baselineTokenId": details["baseline_token_id"],
            "baselineTokenText": details["baseline_token_text"],
            "nSteps": details["n_steps"],
            "convergenceDelta": details["convergence_delta"],
            "prependBos": details["prepend_bos"],
            "rawValues": raw_values,
            "responseContextAttributions": response_context_attributions,
            "sourceRun": source_run,
            "sourceKey": source_key,
        }
    )
    metadata["attributionJobs"] = jobs
    metadata["parentRun"] = source_run
    return run


if __name__ == "__main__":
    main()
