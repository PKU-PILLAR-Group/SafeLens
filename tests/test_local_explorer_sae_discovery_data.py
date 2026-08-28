from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/run_local_explorer_sae_discovery.py"
SPEC = importlib.util.spec_from_file_location("run_local_explorer_sae_discovery", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_recommended_delta_tracks_real_activation_scale_with_bounds() -> None:
    assert MODULE._recommended_delta(0.01) == 100
    assert MODULE._recommended_delta(87.1) == 175
    assert MODULE._recommended_delta(402.1) == 850
    assert MODULE._recommended_delta(701.0) == 1_000
    assert MODULE._recommended_delta(1_500) == 1_000


def test_feature_ranking_retains_peak_token_and_activation_evidence() -> None:
    torch = pytest.importorskip("torch")
    encoded = torch.tensor(
        [
            [0.0, 2.0, 0.0, 5.0],
            [1.0, 0.0, 0.0, 3.0],
            [0.0, 4.0, 0.0, 0.0],
        ]
    )
    tokens = [
        {"text": "prefix"},
        {"text": " first"},
        {"text": " second"},
        {"text": " third"},
    ]

    rows = MODULE._rank_feature_rows(encoded, tokens, start=1, limit=2)

    assert [row["featureIndex"] for row in rows] == [3, 1]
    assert rows[0] == {
        "featureIndex": 3,
        "maxActivation": 5.0,
        "meanActivation": pytest.approx(8 / 3),
        "activeTokenCount": 2,
        "peakTokenIndex": 1,
        "peakTokenText": " first",
        "recommendedDelta": 100.0,
    }
    assert rows[1]["peakTokenIndex"] == 3
    assert rows[1]["peakTokenText"] == " third"


def test_feature_ranking_returns_empty_when_sae_has_no_positive_activation() -> None:
    torch = pytest.importorskip("torch")
    assert MODULE._rank_feature_rows(
        torch.zeros((2, 4)),
        [{"text": "a"}, {"text": "b"}],
        start=0,
        limit=3,
    ) == []
