from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/run_local_explorer_intervention.py"
SPEC = importlib.util.spec_from_file_location("run_local_explorer_intervention", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_intervention_diff_distance_and_lexical_proxy_are_explicit() -> None:
    assert MODULE._levenshtein([1, 2, 3], [1, 4, 3, 5]) == 2
    assert MODULE._diff_rows([1, 2], [1, 3]) == [
        {
            "kind": "equal",
            "originalStart": 0,
            "originalEnd": 1,
            "steeredStart": 0,
            "steeredEnd": 1,
        },
        {
            "kind": "replace",
            "originalStart": 1,
            "originalEnd": 2,
            "steeredStart": 1,
            "steeredEnd": 2,
        },
    ]
    assert MODULE._lexical_risk("harm exploit neutral") == 0.66666667


def test_merge_intervention_result_preserves_causal_and_proxy_provenance() -> None:
    source = {
        "runId": "source-run",
        "sampleId": "sample-a",
        "metricProvenance": {},
        "metadata": {},
    }
    comparison = {
        "vector": {
            "method": "contrastive_mean_difference",
            "sourceKey": "layer_1.resid_post",
        },
        "layer": 1,
        "component": "resid_post",
        "scale": 1.5,
        "positionStart": 2,
        "positionEnd": 5,
        "targetTokenId": 42,
        "targetTokenText": " answer",
        "seed": 7,
        "maxNewTokens": 8,
        "temperature": 0.0,
        "original": {"text": "original"},
        "steered": {"text": "steered"},
        "deltas": {"targetLogit": 0.5},
    }

    derived = MODULE._merge_intervention_result(
        source,
        comparison,
        run_id="derived-run",
    )

    assert derived["runId"] == "derived-run"
    assert derived["intervention"] is comparison
    assert derived["metadata"]["parentRun"] == {
        "runId": "source-run",
        "sampleId": "sample-a",
    }
    assert derived["metricProvenance"]["interventionTargetLogitDelta"]["kind"] == "causal"
    assert derived["metricProvenance"]["interventionLexicalRiskDelta"]["kind"] == "derived_proxy"
