from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from SafeLens.nla import get_nla_profile

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/run_local_explorer_nla.py"
SPEC = importlib.util.spec_from_file_location("run_local_explorer_nla", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_complete_hf_snapshot_requires_model_tokenizer_and_weights(tmp_path: Path) -> None:
    repository = tmp_path / "models--Qwen--Qwen2.5-7B-Instruct"
    snapshot = repository / "snapshots" / "revision-1"
    snapshot.mkdir(parents=True)
    (repository / "refs").mkdir()
    (repository / "refs" / "main").write_text("revision-1\n", encoding="utf-8")
    (snapshot / "config.json").write_text("{}", encoding="utf-8")
    (snapshot / "tokenizer_config.json").write_text("{}", encoding="utf-8")

    assert MODULE._complete_hf_snapshot("Qwen/Qwen2.5-7B-Instruct", str(tmp_path)) is None

    weight = snapshot / "model-00001-of-00001.safetensors"
    weight.write_bytes(b"weights")
    assert MODULE._complete_hf_snapshot(
        "Qwen/Qwen2.5-7B-Instruct",
        str(tmp_path),
    ) == snapshot

    weight.write_bytes(b"")
    assert MODULE._complete_hf_snapshot("Qwen/Qwen2.5-7B-Instruct", str(tmp_path)) is None


def test_complete_hf_snapshot_requires_every_indexed_shard(tmp_path: Path) -> None:
    repository = tmp_path / "models--Qwen--Qwen2.5-7B-Instruct"
    snapshot = repository / "snapshots" / "revision-1"
    snapshot.mkdir(parents=True)
    (repository / "refs").mkdir()
    (repository / "refs" / "main").write_text("revision-1\n", encoding="utf-8")
    (snapshot / "config.json").write_text("{}", encoding="utf-8")
    (snapshot / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (snapshot / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "weight_map": {
                    "first": "model-00001-of-00002.safetensors",
                    "second": "model-00002-of-00002.safetensors",
                }
            }
        ),
        encoding="utf-8",
    )
    (snapshot / "model-00002-of-00002.safetensors").write_bytes(b"second")

    assert MODULE._complete_hf_snapshot("Qwen/Qwen2.5-7B-Instruct", str(tmp_path)) is None

    (snapshot / "model-00001-of-00002.safetensors").write_bytes(b"first")
    assert MODULE._complete_hf_snapshot(
        "Qwen/Qwen2.5-7B-Instruct",
        str(tmp_path),
    ) == snapshot


def test_localize_nla_profile_uses_complete_cached_pair(tmp_path: Path) -> None:
    profile = get_nla_profile("qwen2.5-7b-l20")
    for repo_id in (profile.av_repo, profile.ar_repo):
        assert repo_id is not None
        repository = tmp_path / f"models--{repo_id.replace('/', '--')}"
        snapshot = repository / "snapshots" / "revision-1"
        snapshot.mkdir(parents=True)
        (repository / "refs").mkdir()
        (repository / "refs" / "main").write_text("revision-1\n", encoding="utf-8")
        (snapshot / "config.json").write_text("{}", encoding="utf-8")
        (snapshot / "tokenizer_config.json").write_text("{}", encoding="utf-8")
        (snapshot / "model.safetensors").write_bytes(b"weights")

    localized, local_files_only = MODULE._localize_nla_profile(profile, str(tmp_path))

    assert local_files_only is True
    assert Path(localized.av_repo).name == "revision-1"
    assert localized.ar_repo is not None
    assert Path(localized.ar_repo).name == "revision-1"
    assert profile.av_repo == "kitft/nla-qwen2.5-7b-L20-av"


def test_merge_nla_results_replaces_only_exact_profile_positions() -> None:
    profile = get_nla_profile("qwen2.5-7b-l20")
    run = {
        "runId": "source-run",
        "sampleId": "sample-a",
        "tokens": [
            {"index": 0, "text": "A"},
            {"index": 1, "text": "B"},
        ],
        "nla": [
            {
                "tokenIndex": 0,
                "layer": 20,
                "component": "resid_post",
                "status": "unavailable",
            },
            {
                "tokenIndex": 1,
                "layer": 20,
                "component": "resid_post",
                "status": "unavailable",
            },
        ],
        "nlaCompatibility": {
            "profiles": [
                {
                    "name": profile.name,
                    "status": "artifact_missing",
                    "reason": "not run",
                }
            ]
        },
        "metadata": {},
    }
    results = [
        {
            "explanation": "feature A",
            "cosine": 0.9,
            "mse_nrm": 0.05,
            "activation_norm": 12.0,
        }
    ]

    derived = MODULE._merge_results(
        run,
        results,
        profile=profile,
        positions=[0],
        revision="requested-main",
        actor_checkpoint="/cache/models--av/snapshots/actor-sha",
        reconstructor_checkpoint="/cache/models--ar/snapshots/ar-sha",
        run_id="derived-run",
        max_new_tokens=64,
    )

    exact = next(row for row in derived["nla"] if row["tokenIndex"] == 0)
    untouched = next(row for row in derived["nla"] if row["tokenIndex"] == 1)
    assert exact["status"] == "available"
    assert exact["cosine"] == 0.9
    assert exact["mse"] == 0.05
    assert exact["profile"] == profile.name
    assert untouched["status"] == "unavailable"
    assert derived["nlaCompatibility"]["profiles"][0]["status"] == "compatible"
    job = derived["metadata"]["nlaJobs"][0]
    assert job["requestedRevision"] == "requested-main"
    assert job["actorRevision"] == "actor-sha"
    assert job["reconstructorRevision"] == "ar-sha"
    assert job["trustRemoteCode"] is False
    assert derived["metadata"]["parentRun"] == {
        "runId": "source-run",
        "sampleId": "sample-a",
    }


def test_merge_nla_results_requires_ar_fidelity() -> None:
    profile = get_nla_profile("qwen2.5-7b-l20")
    run = {
        "runId": "source-run",
        "sampleId": "sample-a",
        "tokens": [{"index": 0, "text": "A"}],
        "nla": [],
        "nlaCompatibility": {"profiles": [{"name": profile.name}]},
        "metadata": {},
    }
    with pytest.raises(ValueError, match="AR fidelity is required"):
        MODULE._merge_results(
            run,
            [
                {
                    "explanation": "feature A",
                    "cosine": None,
                    "mse_nrm": None,
                    "activation_norm": 12.0,
                }
            ],
            profile=profile,
            positions=[0],
            revision="main",
            actor_checkpoint=None,
            reconstructor_checkpoint=None,
            run_id="derived-run",
            max_new_tokens=64,
        )
