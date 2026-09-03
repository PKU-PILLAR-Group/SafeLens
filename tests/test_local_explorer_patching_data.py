from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/run_local_explorer_patching.py"
SPEC = importlib.util.spec_from_file_location("run_local_explorer_patching", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_merge_patching_result_preserves_causal_scores_and_parent_provenance() -> None:
    source = {
        "runId": "source-run",
        "sampleId": "sample-a",
        "prompt": "clean prompt",
        "metricProvenance": {},
        "metadata": {},
    }
    cells = [
        {
            "layer": 1,
            "tokenIndex": 2,
            "patchedScore": 3.5,
            "causalEffect": 1.0,
            "recoveryPercentage": 50.0,
            "sourceKey": "layer_1.resid_post",
        }
    ]

    derived = MODULE._merge_patching_result(
        source,
        run_id="derived-run",
        corrupted_prompt="corrupt prompt",
        component="resid_post",
        head=None,
        target_token_id=42,
        target_token_text=" answer",
        layers=[1],
        positions=[2],
        corrupted_tokens=[{"index": 0, "tokenId": 8, "text": "x", "changed": True}],
        clean_score=4.5,
        corrupted_score=2.5,
        cells=cells,
    )

    assert derived["runId"] == "derived-run"
    assert derived["patching"]["denominator"] == 2.0
    assert derived["patching"]["cells"] == cells
    assert derived["metadata"]["parentRun"] == {
        "runId": "source-run",
        "sampleId": "sample-a",
    }
    assert derived["metricProvenance"]["patchingRecovery"]["kind"] == "causal"
    assert derived["metricProvenance"]["patchingCausalEffect"]["kind"] == "causal"


def test_target_logit_and_flat_token_helpers_are_shape_strict() -> None:
    assert MODULE._target_logit([[[1.0, 2.0], [3.0, 4.0]]], 1) == 4.0
    assert MODULE._flat_token_ids([[5, 6]]) == [5, 6]


def test_attention_head_patch_uses_position_head_vector_index_and_provenance() -> None:
    index = MODULE._patch_index("z", 3, 7)
    assert index[0] == slice(None)
    assert index[1:3] == (3, 7)
    assert index[3] == slice(None)

    derived = MODULE._merge_patching_result(
        {
            "runId": "source-run",
            "sampleId": "sample-a",
            "prompt": "clean prompt",
            "metricProvenance": {},
            "metadata": {},
        },
        run_id="head-derived-run",
        corrupted_prompt="corrupt prompt",
        component="z",
        head=7,
        target_token_id=42,
        target_token_text=" answer",
        layers=[5],
        positions=[3],
        corrupted_tokens=[{"index": 0, "tokenId": 8, "text": "x", "changed": True}],
        clean_score=4.5,
        corrupted_score=2.5,
        cells=[
            {
                "layer": 5,
                "tokenIndex": 3,
                "patchedScore": 3.5,
                "causalEffect": 1.0,
                "recoveryPercentage": 50.0,
                "sourceKey": "layer_5.z[head=7]",
            }
        ],
    )

    assert derived["patching"]["component"] == "z"
    assert derived["patching"]["head"] == 7
    assert derived["patching"]["sourceKey"] == "activation_patching.z[target=42,head=7]"
    assert derived["metadata"]["patchingJobs"][-1]["head"] == 7
