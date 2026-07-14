from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/run_local_explorer_attribution.py"
SPEC = importlib.util.spec_from_file_location("run_local_explorer_attribution", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_merge_result_separates_prompt_matrix_from_response_context(monkeypatch) -> None:
    monkeypatch.setattr(MODULE.importlib.metadata, "version", lambda _name: "0.9.test")
    run = {
        "runId": "source-run",
        "sampleId": "sample-a",
        "tokens": [
            {"index": 0, "text": "A", "tokenId": 10},
            {"index": 1, "text": "B", "tokenId": 11},
        ],
        "attributionMethods": [{"id": "integrated_gradients", "available": False}],
        "attributionTracks": [],
        "metricProvenance": {},
        "metadata": {},
    }
    result = {
        "tokens": [
            {
                "token_index": 0,
                "token_text": "A",
                "score": -0.5,
                "metadata": {"token_id": 10, "raw_score": -0.05},
            },
            {
                "token_index": 1,
                "token_text": "B",
                "score": 0.25,
                "metadata": {"token_id": 11, "raw_score": 0.025},
            },
            {
                "token_index": 2,
                "token_text": " response",
                "score": 1.0,
                "metadata": {"token_id": 12, "raw_score": 0.1},
            },
        ],
        "details": {
            "objective": "response_token_logit",
            "target_token_id": 13,
            "target_token_text": " target",
            "target_response_index": 1,
            "target_position": 3,
            "baseline": "pad_token",
            "baseline_token_id": 0,
            "baseline_token_text": "<pad>",
            "n_steps": 16,
            "convergence_delta": 0.001,
            "prepend_bos": False,
        },
    }

    derived = MODULE._merge_result(
        run,
        result,
        run_id="derived-run",
        response=" response target",
    )

    method = next(
        item for item in derived["attributionMethods"] if item["id"] == "integrated_gradients"
    )
    assert method["rows"][0]["values"] == [-0.5, 0.25]
    job = derived["metadata"]["attributionJobs"][0]
    assert job["rawValues"] == [-0.05, 0.025]
    assert job["responseContextAttributions"] == [
        {
            "tokenIndex": 2,
            "tokenText": " response",
            "tokenId": 12,
            "storedValue": 1.0,
            "rawValue": 0.1,
        }
    ]
    assert job["sourceRun"] == {"runId": "source-run", "sampleId": "sample-a"}
    assert derived["runId"] == "derived-run"
