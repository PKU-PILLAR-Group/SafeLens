from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from SafeLens.explorer_api import (
    PromptMessage,
    _read_artifact_cached,
    _read_physical_block_cached,
    _render_prompt,
    create_app,
)
from SafeLens.explorer_chunks import build_explorer_sidecar


def _sample(*, run_id: str = "run-a", sample_id: str = "sample-a") -> dict[str, object]:
    return {
        "runId": run_id,
        "sampleId": sample_id,
        "modelName": "test/model",
        "modelSource": "test",
        "prompt": "fixture prompt",
        "tokens": [{"index": 0, "text": "test"}],
        "layers": [0],
        "payloadMarker": "served-exactly",
    }


def _write_artifact(root: Path, name: str, samples: list[dict[str, object]]) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": "1.0", "samples": samples}),
        encoding="utf-8",
    )
    return path


def _wait_for_job(client: TestClient, job_id: str, status: str) -> dict[str, object]:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        snapshot = client.get(f"/api/jobs/{job_id}").json()
        if snapshot["status"] == status:
            return snapshot
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} did not reach {status}")


def test_explorer_api_indexes_and_serves_exact_samples(tmp_path: Path) -> None:
    _write_artifact(
        tmp_path,
        "nested/runs.explorer.json",
        [_sample(), _sample(run_id="run-a", sample_id="sample-b")],
    )
    client = TestClient(create_app(tmp_path))

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "artifactAccessReadOnly": True,
        "promptJobsEnabled": True,
        "attributionJobsEnabled": True,
        "nlaJobsEnabled": True,
        "jLensJobsEnabled": True,
        "patchingJobsEnabled": True,
        "interventionJobsEnabled": True,
        "rootExists": True,
        "artifactCount": 1,
    }

    response = client.get("/api/runs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schemaVersion"] == "1.0"
    assert payload["rootName"] == tmp_path.name
    assert [(row["runId"], row["sampleId"]) for row in payload["runs"]] == [
        ("run-a", "sample-a"),
        ("run-a", "sample-b"),
    ]
    assert all(row["sourceName"] == "nested/runs.explorer.json" for row in payload["runs"])
    assert all(row["chunkProtocol"] == "safelens-chunks-v1" for row in payload["runs"])
    assert all(row["promptPreview"] == "fixture prompt" for row in payload["runs"])

    sample = client.get("/api/runs/run-a/samples/sample-b")
    assert sample.status_code == 200
    assert sample.json()["payloadMarker"] == "served-exactly"
    assert sample.headers["cache-control"] == "no-store"
    assert sample.headers["etag"].startswith('"')
    assert sample.headers["x-safelens-artifact"]


def test_explorer_api_serves_metadata_and_range_filtered_chunks(tmp_path: Path) -> None:
    sample = _sample(run_id="chunk-run", sample_id="chunk-sample")
    sample.update(
        {
            "tokens": [
                {"index": index, "text": f"t{index}", "tokenId": index} for index in range(4)
            ],
            "layers": [0, 1],
            "prompt": "chunk fixture",
            "residualCells": [
                {"layer": layer, "tokenIndex": token, "rawDirection": layer + token / 10}
                for layer in [0, 1]
                for token in range(4)
            ],
            "attentionHeads": [
                {
                    "id": "L1H0",
                    "layer": 1,
                    "head": 0,
                    "distributionByToken": [
                        [destination * 10 + source for source in range(4)]
                        for destination in range(4)
                    ],
                }
            ],
            "mlpNeurons": [
                {
                    "id": "L1N0002",
                    "layer": 1,
                    "neuron": 2,
                    "activationsByToken": [0.0, 0.1, 0.2, 0.3],
                }
            ],
            "attributionMethods": [
                {
                    "id": "residual_direction",
                    "rows": [
                        {"layer": layer, "label": f"L{layer}", "values": [0.0, 0.1, 0.2, 0.3]}
                        for layer in [0, 1]
                    ],
                }
            ],
            "nla": [
                {
                    "layer": 1,
                    "tokenIndex": 2,
                    "component": "resid_post",
                    "cosine": 0.9,
                }
            ],
        }
    )
    _write_artifact(tmp_path, "chunk.explorer.json", [sample])
    client = TestClient(create_app(tmp_path))

    metadata = client.get("/api/runs/chunk-run/samples/chunk-sample/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["protocol"] == "safelens-chunks-v1"
    assert metadata.json()["base"]["tokens"] == sample["tokens"]
    assert "residualCells" not in metadata.json()["base"]
    descriptors = {row["component"]: row for row in metadata.json()["chunks"]}
    assert descriptors["residualCells"] == {
        "component": "residualCells",
        "itemCount": 8,
        "rangeAxis": "token",
        "layerFilter": True,
        "selectorFilter": False,
    }
    metadata_etag = metadata.headers["etag"]
    assert (
        client.get(
            "/api/runs/chunk-run/samples/chunk-sample/metadata",
            headers={"If-None-Match": metadata_etag},
        ).status_code
        == 304
    )

    residual = client.get(
        "/api/runs/chunk-run/samples/chunk-sample/chunks/residualCells",
        params={"tokenStart": 1, "tokenEnd": 3, "layer": 1},
    )
    assert residual.status_code == 200
    assert residual.json()["tokenRange"] == [1, 3]
    assert [(row["layer"], row["tokenIndex"]) for row in residual.json()["data"]] == [
        (1, 1),
        (1, 2),
    ]
    assert (
        client.get(
            "/api/runs/chunk-run/samples/chunk-sample/chunks/residualCells",
            params={"tokenStart": 1, "tokenEnd": 3, "layer": 1},
            headers={"If-None-Match": residual.headers["etag"]},
        ).status_code
        == 304
    )

    attention = client.get(
        "/api/runs/chunk-run/samples/chunk-sample/chunks/attentionHeads",
        params={"tokenStart": 1, "tokenEnd": 3, "layer": 1, "selector": "L1H0"},
    ).json()["data"][0]
    assert attention["distributionByToken"] == [[11, 12], [21, 22]]
    assert attention["chunk"] == {
        "destinationStart": 1,
        "destinationEnd": 3,
        "sourceStart": 1,
        "sourceEnd": 3,
    }
    cross_block_attention = client.get(
        "/api/runs/chunk-run/samples/chunk-sample/chunks/attentionHeads",
        params={
            "tokenStart": 2,
            "tokenEnd": 4,
            "sourceStart": 0,
            "sourceEnd": 2,
            "layer": 1,
            "selector": "L1H0",
        },
    ).json()
    assert cross_block_attention["sourceRange"] == [0, 2]
    assert cross_block_attention["data"][0]["distributionByToken"] == [[20, 21], [30, 31]]

    attribution = client.get(
        "/api/runs/chunk-run/samples/chunk-sample/chunks/attributionMethods",
        params={
            "tokenStart": 2,
            "tokenEnd": 4,
            "layer": 1,
            "selector": "residual_direction",
        },
    ).json()["data"][0]
    assert attribution["rows"] == [
        {
            "layer": 1,
            "label": "L1",
            "values": [0.2, 0.3],
            "chunk": {"tokenStart": 2, "tokenEnd": 4},
        }
    ]

    invalid = client.get(
        "/api/runs/chunk-run/samples/chunk-sample/chunks/nla",
        params={"tokenStart": 3, "tokenEnd": 5},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "invalid_chunk_range"


def test_explorer_api_reuses_parsed_artifacts_and_invalidates_on_file_change(
    tmp_path: Path, monkeypatch
) -> None:
    artifact = _write_artifact(tmp_path, "cached.explorer.json", [_sample()])
    _read_artifact_cached.cache_clear()
    original_read_text = Path.read_text
    reads = 0

    def counted_read_text(path: Path, *args, **kwargs):
        nonlocal reads
        if path == artifact:
            reads += 1
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted_read_text)
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/runs").status_code == 200
    assert client.get("/api/runs/run-a/samples/sample-a/metadata").status_code == 200
    assert client.get("/api/runs/run-a/samples/sample-a").status_code == 200
    assert reads == 1

    replacement = _sample(run_id="run-b", sample_id="sample-b")
    artifact.write_text(
        json.dumps({"schema_version": "1.0", "samples": [replacement]}),
        encoding="utf-8",
    )
    payload = client.get("/api/runs").json()
    assert [(row["runId"], row["sampleId"]) for row in payload["runs"]] == [("run-b", "sample-b")]
    assert reads == 2


def test_explorer_api_prefers_physical_sidecars_and_verifies_blocks(
    tmp_path: Path, monkeypatch
) -> None:
    sample = _sample(run_id="physical-run", sample_id="physical-sample")
    sample.update(
        {
            "tokens": [
                {"index": index, "text": f"t{index}", "tokenId": index} for index in range(4)
            ],
            "layers": [0, 1],
            "residualCells": [
                {"layer": layer, "tokenIndex": token, "value": layer + token}
                for layer in [0, 1]
                for token in range(4)
            ],
            "attentionHeads": [
                {
                    "id": "L1H0",
                    "layer": 1,
                    "distributionByToken": [
                        [destination * 10 + source for source in range(4)]
                        for destination in range(4)
                    ],
                }
            ],
        }
    )
    artifact = _write_artifact(tmp_path, "physical.explorer.json", [sample])
    manifest_path = build_explorer_sidecar(artifact, block_size=4)
    _read_artifact_cached.cache_clear()
    _read_physical_block_cached.cache_clear()
    original_read_bytes = Path.read_bytes
    source_reads = 0

    def counted_read_bytes(path: Path, *args, **kwargs):
        nonlocal source_reads
        if path == artifact:
            source_reads += 1
        return original_read_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    client = TestClient(create_app(tmp_path))
    index = client.get("/api/runs")
    assert index.status_code == 200
    assert (
        index.json()["runs"][0]["artifactId"]
        == json.loads(manifest_path.read_text(encoding="utf-8"))["source"]["sha256"][:16]
    )
    metadata = client.get("/api/runs/physical-run/samples/physical-sample/metadata")
    assert metadata.headers["x-safelens-storage"] == "physical"
    assert "residualCells" not in metadata.json()["base"]
    residual = client.get(
        "/api/runs/physical-run/samples/physical-sample/chunks/residualCells",
        params={"tokenStart": 1, "tokenEnd": 3, "layer": 1},
    )
    assert residual.headers["x-safelens-storage"] == "physical"
    assert [row["tokenIndex"] for row in residual.json()["data"]] == [1, 2]
    attention = client.get(
        "/api/runs/physical-run/samples/physical-sample/chunks/attentionHeads",
        params={
            "tokenStart": 2,
            "tokenEnd": 4,
            "sourceStart": 0,
            "sourceEnd": 2,
            "layer": 1,
        },
    )
    assert attention.json()["data"][0]["distributionByToken"] == [[20, 21], [30, 31]]
    assert source_reads == 0

    full = client.get("/api/runs/physical-run/samples/physical-sample")
    assert full.headers["x-safelens-storage"] == "physical-source"
    assert full.json()["payloadMarker"] == "served-exactly"
    assert source_reads == 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    block = manifest["samples"][0]["components"]["residualCells"]["blocks"][0]
    block_path = manifest_path.parent / block["path"]
    block_path.write_bytes(b"x" * block["sizeBytes"])
    _read_physical_block_cached.cache_clear()
    corrupt = client.get(
        "/api/runs/physical-run/samples/physical-sample/chunks/residualCells",
        params={"tokenStart": 0, "tokenEnd": 1},
    )
    assert corrupt.status_code == 409
    assert corrupt.json()["detail"]["code"] == "chunk_checksum_mismatch"


def test_stale_physical_manifest_falls_back_to_embedded_artifact(tmp_path: Path) -> None:
    artifact = _write_artifact(tmp_path, "stale.explorer.json", [_sample()])
    build_explorer_sidecar(artifact, block_size=2)
    replacement = _sample()
    replacement["payloadMarker"] = "updated-after-sidecar"
    artifact.write_text(
        json.dumps({"schema_version": "1.0", "samples": [replacement]}),
        encoding="utf-8",
    )
    client = TestClient(create_app(tmp_path))
    index = client.get("/api/runs").json()
    assert index["runs"][0]["runId"] == "run-a"
    assert any(row["code"] == "stale_chunk_manifest" for row in index["diagnostics"])
    metadata = client.get("/api/runs/run-a/samples/sample-a/metadata")
    assert metadata.headers["x-safelens-storage"] == "embedded"
    assert metadata.json()["base"]["payloadMarker"] == "updated-after-sidecar"


def test_physical_manifest_cannot_reference_blocks_outside_artifact_root(tmp_path: Path) -> None:
    artifact = _write_artifact(tmp_path, "escape.explorer.json", [_sample()])
    manifest_path = build_explorer_sidecar(artifact, block_size=2)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    block = manifest["samples"][0]["components"]["residualCells"]["blocks"][0]
    outside = tmp_path.parent / f"{tmp_path.name}-outside.json"
    outside.write_text("[]", encoding="utf-8")
    block.update(
        {
            "path": f"../{outside.name}",
            "sizeBytes": outside.stat().st_size,
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
        }
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    client = TestClient(create_app(tmp_path))
    response = client.get(
        "/api/runs/run-a/samples/sample-a/chunks/residualCells",
        params={"tokenStart": 0, "tokenEnd": 1},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_chunk_path"


def test_full_physical_source_verifies_checksum_even_when_stat_is_unchanged(
    tmp_path: Path,
) -> None:
    artifact = _write_artifact(tmp_path, "tampered.explorer.json", [_sample()])
    build_explorer_sidecar(artifact, block_size=2)
    stat = artifact.stat()
    encoded = artifact.read_bytes()
    replacement = encoded.replace(b"served-exactly", b"tampered-value", 1)
    assert len(replacement) == len(encoded)
    artifact.write_bytes(replacement)
    os.utime(artifact, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    client = TestClient(create_app(tmp_path))
    response = client.get("/api/runs/run-a/samples/sample-a")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "physical_source_checksum_mismatch"


def test_prompt_job_completes_with_progress_and_sse_snapshot(tmp_path: Path) -> None:
    def runner(payload, cancel_event, progress):
        assert not cancel_event.is_set()
        progress(45, "forward", "Collecting activations.")
        return {
            **_sample(run_id="prompt-run", sample_id=f"seed-{payload.seed}"),
            "prompt": payload.prompt,
            "metadata": {
                "promptRunner": {
                    "model": payload.model,
                    "template": payload.template,
                    "seed": payload.seed,
                    "maxNewTokens": payload.maxNewTokens,
                    "temperature": payload.temperature,
                }
            },
        }

    client = TestClient(create_app(tmp_path, prompt_runner=runner))
    response = client.post(
        "/api/jobs/prompt",
        json={
            "prompt": "Explain this result.",
            "template": "chat",
            "model": "sshleifer/tiny-gpt2",
            "seed": 17,
            "maxNewTokens": 12,
            "temperature": 0.4,
        },
    )

    assert response.status_code == 202
    job_id = response.json()["id"]
    snapshot = _wait_for_job(client, job_id, "ready")
    assert snapshot["progress"] == 100
    assert snapshot["result"]["sampleId"] == "seed-17"
    assert snapshot["result"]["metadata"]["promptRunner"]["temperature"] == 0.4

    with client.stream("GET", f"/api/jobs/{job_id}/events") as stream:
        assert stream.status_code == 200
        body = "\n".join(stream.iter_lines())
    assert "event: job" in body
    assert '"status":"ready"' in body


def test_chat_prompt_renders_prior_turns_in_order() -> None:
    rendered = _render_prompt(
        "What follows?",
        "chat",
        [
            PromptMessage(role="user", content="First question?"),
            PromptMessage(role="assistant", content="First answer."),
        ],
    )

    assert rendered == (
        "User: First question?\n"
        "Assistant: First answer.\n"
        "User: What follows?\n"
        "Assistant:"
    )


def test_prompt_job_rejects_unapproved_models(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, prompt_runner=lambda *_args: {}))
    response = client.post(
        "/api/jobs/prompt",
        json={"prompt": "test", "model": "remote/custom-model"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "model_not_allowed"


def test_prompt_options_include_registered_nla_base_models(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, prompt_runner=lambda *_args: {}))

    response = client.get("/api/prompt/options")

    assert response.status_code == 200
    assert response.json()["models"] == [
        "Qwen/Qwen2.5-7B-Instruct",
        "sshleifer/tiny-gpt2",
        "google/gemma-3-12b-it",
    ]
    assert response.json()["maxNewTokens"] == 512


def test_prompt_job_can_cancel_a_running_worker(tmp_path: Path) -> None:
    started = threading.Event()

    def runner(_payload, cancel_event, progress):
        progress(20, "model", "Loading model.")
        started.set()
        assert cancel_event.wait(timeout=2)
        raise RuntimeError("cancelled by test")

    client = TestClient(create_app(tmp_path, prompt_runner=runner))
    response = client.post("/api/jobs/prompt", json={"prompt": "cancel me"})
    job_id = response.json()["id"]
    assert started.wait(timeout=1)

    cancelled = client.delete(f"/api/jobs/{job_id}")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["result"] is None
    assert _wait_for_job(client, job_id, "cancelled")["stage"] == "cancelled"


def test_prompt_job_reports_how_many_local_jobs_are_ahead(tmp_path: Path) -> None:
    started = threading.Event()
    release = threading.Event()

    def runner(payload, _cancel_event, _progress):
        if payload.prompt == "first":
            started.set()
            assert release.wait(timeout=2)
        return _sample(run_id=f"run-{payload.prompt}")

    client = TestClient(create_app(tmp_path, prompt_runner=runner))
    first = client.post("/api/jobs/prompt", json={"prompt": "first"}).json()
    assert started.wait(timeout=1)
    second = client.post("/api/jobs/prompt", json={"prompt": "second"}).json()

    assert second["status"] == "idle"
    assert second["progress"] == 0
    assert second["detail"] == "Queued behind 1 local model job."

    release.set()
    assert _wait_for_job(client, first["id"], "ready")["progress"] == 100
    assert _wait_for_job(client, second["id"], "ready")["progress"] == 100


def test_attribution_job_uses_shared_queue_contract_and_returns_derived_run(
    tmp_path: Path,
) -> None:
    source = _sample()
    source.update({"prompt": "source prompt", "modelName": "sshleifer/tiny-gpt2"})

    def runner(payload, cancel_event, progress):
        assert payload.objective == "response_token_logit"
        assert payload.baseline == "pad_token"
        assert not cancel_event.is_set()
        progress(55, "integrated-gradients", "Computing signed token scores.")
        return {
            **payload.run,
            "runId": "run-a-ig-derived",
            "metadata": {
                "parentRun": {"runId": "run-a", "sampleId": "sample-a"},
                "attributionJobs": [
                    {
                        "objective": payload.objective,
                        "baseline": payload.baseline,
                        "nSteps": payload.nSteps,
                        "targetResponseIndex": payload.targetResponseIndex,
                    }
                ],
            },
        }

    client = TestClient(create_app(tmp_path, attribution_runner=runner))
    response = client.post(
        "/api/jobs/attribution",
        json={
            "run": source,
            "response": " derived response",
            "objective": "response_token_logit",
            "targetResponseIndex": 0,
            "baseline": "pad_token",
            "nSteps": 16,
        },
    )
    assert response.status_code == 202
    assert response.json()["kind"] == "attribution"
    snapshot = _wait_for_job(client, response.json()["id"], "ready")
    assert snapshot["result"]["runId"] == "run-a-ig-derived"
    assert snapshot["request"]["nSteps"] == 16
    assert "run" not in snapshot["request"]
    assert snapshot["request"]["sourceRun"] == {
        "runId": "run-a",
        "sampleId": "sample-a",
        "modelName": "sshleifer/tiny-gpt2",
    }
    assert snapshot["result"]["metadata"]["attributionJobs"][0] == {
        "objective": "response_token_logit",
        "baseline": "pad_token",
        "nSteps": 16,
        "targetResponseIndex": 0,
    }


def test_attribution_job_rejects_invalid_run_and_unapproved_model(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path, attribution_runner=lambda *_args: {}))
    invalid = client.post(
        "/api/jobs/attribution",
        json={"run": {}, "response": "x", "targetResponseIndex": 0},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "invalid_sample"

    source = _sample()
    source["modelName"] = "remote/custom-model"
    unapproved = client.post(
        "/api/jobs/attribution",
        json={"run": source, "response": "x", "targetResponseIndex": 0},
    )
    assert unapproved.status_code == 422
    assert unapproved.json()["detail"]["code"] == "model_not_allowed"


def test_nla_preflight_reports_structural_and_authorization_checks(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    client = TestClient(create_app(tmp_path))

    profiles = client.get("/api/nla/profiles")
    assert profiles.status_code == 200
    assert profiles.json()[0]["name"] == "qwen2.5-7b-l20"

    incompatible = client.post(
        "/api/nla/preflight",
        json={
            "modelName": "sshleifer/tiny-gpt2",
            "dModel": 2,
            "availableLayers": [0, 1],
            "profile": "qwen2.5-7b-l20",
        },
    ).json()
    assert incompatible["status"] == "incompatible"
    assert incompatible["canSubmit"] is False
    assert incompatible["modelMatches"] is False
    assert incompatible["layerAvailable"] is False
    assert incompatible["dModelMatches"] is False

    compatible = client.post(
        "/api/nla/preflight",
        json={
            "modelName": "Qwen/Qwen2.5-7B-Instruct",
            "dModel": 3584,
            "availableLayers": [20],
            "profile": "qwen2.5-7b-l20",
        },
    ).json()
    assert compatible["status"] == "compatible"
    assert compatible["canSubmit"] is True
    assert compatible["gated"] is False

    gated = client.post(
        "/api/nla/preflight",
        json={
            "modelName": "google/gemma-3-12b-it",
            "dModel": 3840,
            "availableLayers": [32],
            "profile": "gemma3-12b-l32",
        },
    ).json()
    assert gated["status"] == "authorization_required"
    assert gated["tokenConfigured"] is False
    assert gated["canSubmit"] is False

    unknown = client.post(
        "/api/nla/preflight",
        json={
            "modelName": "model",
            "dModel": 1,
            "availableLayers": [0],
            "profile": "missing",
        },
    )
    assert unknown.status_code == 422
    assert unknown.json()["detail"]["code"] == "unknown_nla_profile"


def test_nla_job_queues_only_after_compatible_preflight(tmp_path: Path) -> None:
    source = _sample()
    source.update(
        {
            "prompt": "source prompt",
            "modelName": "Qwen/Qwen2.5-7B-Instruct",
            "nlaCompatibility": {"dModel": 3584, "availableLayers": [20], "profiles": []},
        }
    )

    def runner(payload, cancel_event, progress):
        assert payload.profile == "qwen2.5-7b-l20"
        assert payload.positions == [0]
        assert not cancel_event.is_set()
        progress(60, "nla-av-ar", "Explaining exact activation.")
        return {
            **payload.run,
            "runId": "run-a-nla-derived",
            "metadata": {
                "parentRun": {"runId": "run-a", "sampleId": "sample-a"},
                "nlaJobs": [{"profile": payload.profile, "positions": payload.positions}],
            },
        }

    client = TestClient(create_app(tmp_path, nla_runner=runner))
    response = client.post(
        "/api/jobs/nla",
        json={
            "run": source,
            "profile": "qwen2.5-7b-l20",
            "positions": [0],
            "revision": "test-revision",
            "maxNewTokens": 64,
            "loadReconstructor": True,
        },
    )
    assert response.status_code == 202
    assert response.json()["kind"] == "nla"
    assert "run" not in response.json()["request"]
    assert response.json()["request"]["preflight"]["status"] == "compatible"
    snapshot = _wait_for_job(client, response.json()["id"], "ready")
    assert snapshot["result"]["runId"] == "run-a-nla-derived"

    incompatible = {**source, "modelName": "sshleifer/tiny-gpt2"}
    rejected = client.post(
        "/api/jobs/nla",
        json={
            "run": incompatible,
            "profile": "qwen2.5-7b-l20",
            "positions": [0],
        },
    )
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "incompatible"


def test_nla_job_hydrates_chunked_workspace_run_before_worker(tmp_path: Path) -> None:
    source = _sample()
    source.update(
        {
            "prompt": "source prompt",
            "modelName": "Qwen/Qwen2.5-7B-Instruct",
            "nlaCompatibility": {"dModel": 3584, "availableLayers": [20], "profiles": []},
            "payloadMarker": "complete-workspace-run",
            "attentionHeads": [{"id": "L0H0"}],
            "mlpNeurons": [{"id": "L0N0"}],
            "residualCells": [{"layer": 0}],
            "logitLens": [{"layer": 0}],
            "attentionCells": [{"layer": 0}],
            "mlpCells": [{"layer": 0}],
            "attributionMethods": [{"id": "method"}],
        }
    )
    _write_artifact(tmp_path, "workspace.explorer.json", [source])
    chunked = {
        **source,
        "payloadMarker": "partial-run",
        "attentionHeads": [{"id": "__chunk_pending__"}],
        "mlpNeurons": [],
        "attentionCells": [],
        "mlpCells": [],
        "attributionMethods": [{"id": "__chunk_pending__"}],
    }

    def runner(payload, _cancel_event, _progress):
        assert payload.run["payloadMarker"] == "complete-workspace-run"
        assert payload.run["attentionHeads"] == [{"id": "L0H0"}]
        return {**payload.run, "runId": "run-a-nla-derived"}

    client = TestClient(create_app(tmp_path, nla_runner=runner))
    response = client.post(
        "/api/jobs/nla",
        json={
            "run": chunked,
            "profile": "qwen2.5-7b-l20",
            "positions": [0],
            "loadReconstructor": True,
        },
    )

    assert response.status_code == 202
    snapshot = _wait_for_job(client, response.json()["id"], "ready")
    assert snapshot["result"]["payloadMarker"] == "complete-workspace-run"


def test_jlens_preflight_and_job_use_an_independent_derived_run(tmp_path: Path) -> None:
    source = _sample()
    source.update(
        {
            "tokens": [{"index": 0, "tokenId": 7, "text": "test"}],
            "jLens": [],
        }
    )

    def runner(payload, cancel_event, progress):
        assert payload.layer == 0
        assert payload.position == 0
        assert payload.lensSource == "research/lens"
        assert payload.filename == "test-model/lens.pt"
        assert not cancel_event.is_set()
        progress(65, "jlens", "Applying the fitted average Jacobian.")
        return {
            **payload.run,
            "runId": "run-a-jlens-derived",
            "jLens": [{"layer": 0, "tokenIndex": 0}],
            "metadata": {
                "parentRun": {"runId": "run-a", "sampleId": "sample-a"},
                "jLensJobs": [{"layer": payload.layer, "position": payload.position}],
            },
        }

    client = TestClient(
        create_app(
            tmp_path,
            jlens_runner=runner,
            allowed_models=("test/model",),
        )
    )
    options = client.get("/api/jlens/options")
    assert options.status_code == 200
    assert options.json()["packageInstalled"] is True
    assert options.json()["defaultModel"] == "Qwen/Qwen2.5-7B-Instruct"
    assert options.json()["defaultSource"] == "neuronpedia/jacobian-lens"
    assert options.json()["profiles"][0]["defaultLayer"] == 20

    preflight_payload = {
        "modelName": "test/model",
        "availableLayers": [0],
        "layer": 0,
        "tokenCount": 1,
        "position": 0,
        "lensSource": "research/lens",
        "filename": "test-model/lens.pt",
        "revision": "revision-1",
    }
    preflight = client.post("/api/jlens/preflight", json=preflight_payload)
    assert preflight.status_code == 200
    assert preflight.json()["canSubmit"] is True

    outside = client.post(
        "/api/jlens/preflight",
        json={**preflight_payload, "lensSource": str(tmp_path.parent / "outside-lens.pt")},
    )
    assert outside.status_code == 200
    assert outside.json()["canSubmit"] is False
    assert "artifact root" in outside.json()["reason"]

    response = client.post(
        "/api/jobs/jlens",
        json={
            "run": source,
            "layer": 0,
            "position": 0,
            "lensSource": "research/lens",
            "filename": "test-model/lens.pt",
            "revision": "revision-1",
            "topK": 8,
        },
    )
    assert response.status_code == 202
    assert response.json()["kind"] == "jlens"
    assert "run" not in response.json()["request"]
    snapshot = _wait_for_job(client, response.json()["id"], "ready")
    assert snapshot["result"]["runId"] == "run-a-jlens-derived"

    rejected = client.post(
        "/api/jobs/jlens",
        json={
            "run": source,
            "layer": 1,
            "position": 0,
            "lensSource": "research/lens",
        },
    )
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "jlens_preflight_failed"


def test_registered_qwen_jlens_preflight_enforces_model_width_layer_and_revision(
    tmp_path: Path,
) -> None:
    from SafeLens.jlens_profiles import QWEN25_7B_INSTRUCT_JLENS

    client = TestClient(
        create_app(
            tmp_path,
            jlens_runner=lambda *_args: {},
            allowed_models=("Qwen/Qwen2.5-7B-Instruct", "test/model"),
        )
    )
    payload = {
        "modelName": "Qwen/Qwen2.5-7B-Instruct",
        "dModel": 3584,
        "availableLayers": list(range(28)),
        "layer": 20,
        "tokenCount": 6,
        "position": 5,
        "lensSource": QWEN25_7B_INSTRUCT_JLENS.source,
        "filename": QWEN25_7B_INSTRUCT_JLENS.filename,
        "revision": QWEN25_7B_INSTRUCT_JLENS.revision,
    }

    ready = client.post("/api/jlens/preflight", json=payload)
    assert ready.status_code == 200
    assert ready.json()["canSubmit"] is True
    assert ready.json()["lensDModel"] == 3584
    assert ready.json()["fittedLayers"] == list(range(27))

    wrong_model = client.post(
        "/api/jlens/preflight",
        json={**payload, "modelName": "test/model"},
    )
    assert wrong_model.json()["canSubmit"] is False
    assert "fits Qwen/Qwen2.5-7B-Instruct" in wrong_model.json()["reason"]

    wrong_revision = client.post(
        "/api/jlens/preflight",
        json={**payload, "revision": "main"},
    )
    assert wrong_revision.json()["canSubmit"] is False
    assert "pinned checkpoint revision" in wrong_revision.json()["reason"]

    unfitted_layer = client.post(
        "/api/jlens/preflight",
        json={**payload, "layer": 27},
    )
    assert unfitted_layer.json()["canSubmit"] is False
    assert "not fitted" in unfitted_layer.json()["reason"]


class _PatchingTokenizer:
    vocab_size = 100

    def __len__(self) -> int:
        return self.vocab_size

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        assert add_special_tokens is False
        return {
            "clean prompt": [11, 12],
            "corrupt prompt": [11, 13],
            "too many tokens": [11, 13, 14],
        }[text]

    def decode(self, token_ids: list[int], clean_up_tokenization_spaces: bool = False) -> str:
        assert clean_up_tokenization_spaces is False
        return f"token-{token_ids[0]}"


def test_tokenize_endpoint_uses_the_selected_model_tokenizer(tmp_path: Path) -> None:
    loaded: list[str] = []

    def loader(model_name: str):
        loaded.append(model_name)
        return _PatchingTokenizer()

    client = TestClient(create_app(tmp_path, patching_tokenizer_loader=loader))
    response = client.post(
        "/api/tokenize",
        json={"modelName": "sshleifer/tiny-gpt2", "text": "clean prompt"},
    )

    assert response.status_code == 200
    assert loaded == ["sshleifer/tiny-gpt2"]
    assert response.json() == {
        "modelName": "sshleifer/tiny-gpt2",
        "text": "clean prompt",
        "tokens": [
            {"index": 0, "tokenId": 11, "text": "token-11"},
            {"index": 1, "tokenId": 12, "text": "token-12"},
        ],
        "truncated": False,
    }

    rejected = client.post(
        "/api/tokenize",
        json={"modelName": "remote/custom-model", "text": "clean prompt"},
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "model_not_allowed"


def test_patching_preflight_reports_exact_alignment_and_rejects_unapproved_model(
    tmp_path: Path,
) -> None:
    loaded: list[str] = []

    def loader(model_name: str):
        loaded.append(model_name)
        return _PatchingTokenizer()

    client = TestClient(create_app(tmp_path, patching_tokenizer_loader=loader))
    response = client.post(
        "/api/patching/preflight",
        json={
            "modelName": "sshleifer/tiny-gpt2",
            "cleanPrompt": "clean prompt",
            "corruptedPrompt": "corrupt prompt",
            "cleanTokenIds": [11, 12],
            "layers": [0, 1],
            "component": "resid_post",
            "targetTokenId": 42,
        },
    )
    assert response.status_code == 200
    assert response.json()["canSubmit"] is True
    assert response.json()["changedPositions"] == [1]
    assert response.json()["corruptedTokens"][1] == {
        "index": 1,
        "tokenId": 13,
        "text": "token-13",
        "changed": True,
    }

    misaligned = client.post(
        "/api/patching/preflight",
        json={
            "modelName": "sshleifer/tiny-gpt2",
            "cleanPrompt": "clean prompt",
            "corruptedPrompt": "too many tokens",
            "cleanTokenIds": [11, 12],
            "layers": [0],
            "component": "mlp_out",
            "targetTokenId": 42,
        },
    ).json()
    assert misaligned["canSubmit"] is False
    assert misaligned["tokenCountMatches"] is False

    rejected = client.post(
        "/api/patching/preflight",
        json={
            "modelName": "remote/custom",
            "cleanPrompt": "clean prompt",
            "corruptedPrompt": "corrupt prompt",
            "cleanTokenIds": [11, 12],
            "layers": [0],
            "component": "resid_post",
            "targetTokenId": 42,
        },
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "model_not_allowed"
    assert loaded == ["sshleifer/tiny-gpt2", "sshleifer/tiny-gpt2"]


def test_patching_job_uses_shared_queue_and_returns_derived_causal_run(tmp_path: Path) -> None:
    source = _sample()
    source.update(
        {
            "prompt": "clean prompt",
            "modelName": "sshleifer/tiny-gpt2",
            "tokens": [
                {"index": 0, "text": "clean", "tokenId": 11},
                {"index": 1, "text": " prompt", "tokenId": 12},
            ],
            "layers": [0, 1],
        }
    )

    def runner(payload, cancel_event, progress):
        assert payload.component == "attn_out"
        assert payload.layers == [1]
        assert payload.positions == [1]
        assert not cancel_event.is_set()
        progress(60, "patch-grid", "Evaluating causal cells.")
        return {
            **payload.run,
            "runId": "run-a-patch-derived",
            "patching": {"cells": [{"layer": 1, "tokenIndex": 1, "causalEffect": 0.5}]},
        }

    client = TestClient(
        create_app(
            tmp_path,
            patching_runner=runner,
            patching_tokenizer_loader=lambda _model: _PatchingTokenizer(),
        )
    )
    response = client.post(
        "/api/jobs/patching",
        json={
            "run": source,
            "corruptedPrompt": "corrupt prompt",
            "component": "attn_out",
            "layers": [1],
            "positions": [1],
            "targetTokenId": 42,
        },
    )
    assert response.status_code == 202
    assert response.json()["kind"] == "patching"
    assert "run" not in response.json()["request"]
    assert response.json()["request"]["preflight"]["changedPositions"] == [1]
    snapshot = _wait_for_job(client, response.json()["id"], "ready")
    assert snapshot["result"]["runId"] == "run-a-patch-derived"

    invalid = client.post(
        "/api/jobs/patching",
        json={
            "run": source,
            "corruptedPrompt": "too many tokens",
            "component": "resid_post",
            "layers": [0],
            "positions": [0],
            "targetTokenId": 42,
        },
    )
    assert invalid.status_code == 409
    assert invalid.json()["detail"]["code"] == "patching_preflight_failed"


def test_attention_head_patching_validates_layer_and_head_before_queue(tmp_path: Path) -> None:
    source = _sample()
    source.update(
        {
            "prompt": "clean prompt",
            "modelName": "sshleifer/tiny-gpt2",
            "tokens": [
                {"index": 0, "text": "clean", "tokenId": 11},
                {"index": 1, "text": " prompt", "tokenId": 12},
            ],
            "layers": [0, 1],
            "metadata": {
                "attentionHeadCoverage": {
                    "availableByLayer": {"0": 4, "1": 4},
                }
            },
        }
    )

    def runner(payload, cancel_event, progress):
        assert payload.component == "z"
        assert payload.layers == [1]
        assert payload.head == 3
        assert not cancel_event.is_set()
        progress(60, "patch-grid", "Evaluating one attention-head patch.")
        return {
            **payload.run,
            "runId": "run-a-head-patch-derived",
            "patching": {
                "component": "z",
                "head": 3,
                "cells": [{"layer": 1, "tokenIndex": 1, "causalEffect": 0.5}],
            },
        }

    client = TestClient(
        create_app(
            tmp_path,
            patching_runner=runner,
            patching_tokenizer_loader=lambda _model: _PatchingTokenizer(),
        )
    )
    base_request = {
        "run": source,
        "corruptedPrompt": "corrupt prompt",
        "component": "z",
        "layers": [1],
        "positions": [1],
        "targetTokenId": 42,
    }

    missing = client.post("/api/jobs/patching", json=base_request)
    assert missing.status_code == 422
    assert missing.json()["detail"]["code"] == "invalid_attention_head"

    multiple_layers = client.post(
        "/api/jobs/patching",
        json={**base_request, "layers": [0, 1], "head": 0},
    )
    assert multiple_layers.status_code == 422
    assert multiple_layers.json()["detail"]["code"] == "invalid_head_patch_layer"

    out_of_range = client.post(
        "/api/jobs/patching",
        json={**base_request, "head": 4},
    )
    assert out_of_range.status_code == 422
    assert out_of_range.json()["detail"]["code"] == "invalid_attention_head"

    accepted = client.post(
        "/api/jobs/patching",
        json={**base_request, "head": 3},
    )
    assert accepted.status_code == 202
    assert accepted.json()["request"]["head"] == 3
    snapshot = _wait_for_job(client, accepted.json()["id"], "ready")
    assert snapshot["result"]["patching"]["head"] == 3


def test_intervention_preflight_checks_layer_range_target_and_references(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            tmp_path,
            intervention_tokenizer_loader=lambda _model: _PatchingTokenizer(),
        )
    )
    request = {
        "modelName": "sshleifer/tiny-gpt2",
        "promptTokenCount": 2,
        "availableLayers": [0, 1],
        "layer": 1,
        "component": "resid_post",
        "positionStart": 0,
        "positionEnd": 2,
        "targetTokenId": 42,
        "desiredPrompt": "desired behavior",
        "undesiredPrompt": "undesired behavior",
    }
    ready = client.post("/api/intervention/preflight", json=request)
    assert ready.status_code == 200
    assert ready.json()["canSubmit"] is True
    assert ready.json()["targetTokenText"] == "token-42"

    blocked = client.post(
        "/api/intervention/preflight",
        json={
            **request,
            "layer": 9,
            "positionEnd": 3,
            "undesiredPrompt": "desired behavior",
        },
    ).json()
    assert blocked["canSubmit"] is False
    assert blocked["layerAvailable"] is False
    assert blocked["positionRangeValid"] is False
    assert blocked["referencesDiffer"] is False


def test_neuron_intervention_preflight_requires_a_real_cached_neuron(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            tmp_path,
            intervention_tokenizer_loader=lambda _model: _PatchingTokenizer(),
        )
    )
    request = {
        "mode": "neuron",
        "modelName": "sshleifer/tiny-gpt2",
        "promptTokenCount": 2,
        "availableLayers": [0, 1],
        "layer": 1,
        "component": "mlp_out",
        "positionStart": 0,
        "positionEnd": 2,
        "targetTokenId": 42,
        "neuron": 7,
        "availableNeurons": [3, 7],
        "desiredPrompt": "Enhance selected MLP neuron",
        "undesiredPrompt": "Suppress selected MLP neuron",
    }
    ready = client.post("/api/intervention/preflight", json=request)
    assert ready.status_code == 200
    assert ready.json()["mode"] == "neuron"
    assert ready.json()["featureAvailable"] is True
    assert ready.json()["referencesDiffer"] is True

    blocked = client.post(
        "/api/intervention/preflight",
        json={**request, "neuron": 99},
    )
    assert blocked.status_code == 200
    assert blocked.json()["canSubmit"] is False
    assert blocked.json()["featureAvailable"] is False


def test_intervention_job_queues_only_after_authoritative_preflight(tmp_path: Path) -> None:
    source = _sample()
    source.update(
        {
            "prompt": "clean prompt",
            "modelName": "sshleifer/tiny-gpt2",
            "tokens": [
                {"index": 0, "text": "clean", "tokenId": 11},
                {"index": 1, "text": " prompt", "tokenId": 12},
            ],
            "layers": [0, 1],
        }
    )

    def runner(payload, cancel_event, progress):
        assert payload.layer == 1
        assert payload.positionStart == 0
        assert payload.positionEnd == 2
        assert payload.scale == 1.5
        assert not cancel_event.is_set()
        progress(65, "generation", "Comparing deterministic outputs.")
        return {
            **payload.run,
            "runId": "run-a-intervention-derived",
            "intervention": {
                "original": {"text": " original"},
                "steered": {"text": " steered"},
            },
        }

    client = TestClient(
        create_app(
            tmp_path,
            intervention_runner=runner,
            intervention_tokenizer_loader=lambda _model: _PatchingTokenizer(),
        )
    )
    response = client.post(
        "/api/jobs/intervention",
        json={
            "run": source,
            "desiredPrompt": "desired behavior",
            "undesiredPrompt": "undesired behavior",
            "layer": 1,
            "component": "resid_post",
            "scale": 1.5,
            "positionStart": 0,
            "positionEnd": 2,
            "targetTokenId": 42,
            "seed": 7,
            "maxNewTokens": 8,
            "temperature": 0,
        },
    )
    assert response.status_code == 202
    assert response.json()["kind"] == "intervention"
    assert "run" not in response.json()["request"]
    assert "neuron" not in response.json()["request"]
    assert response.json()["request"]["preflight"]["canSubmit"] is True
    snapshot = _wait_for_job(client, response.json()["id"], "ready")
    assert snapshot["result"]["runId"] == "run-a-intervention-derived"

    invalid = client.post(
        "/api/jobs/intervention",
        json={
            "run": source,
            "desiredPrompt": "same",
            "undesiredPrompt": "same",
            "layer": 1,
            "component": "resid_post",
            "scale": 1,
            "positionStart": 0,
            "positionEnd": 2,
            "targetTokenId": 42,
        },
    )
    assert invalid.status_code == 409
    assert invalid.json()["detail"]["code"] == "intervention_preflight_failed"


def test_explorer_api_reports_invalid_artifacts_without_hiding_valid_runs(
    tmp_path: Path,
) -> None:
    _write_artifact(tmp_path, "valid.explorer.json", [_sample()])
    (tmp_path / "broken.explorer.json").write_text("{broken", encoding="utf-8")
    (tmp_path / "wrong-version.explorer.json").write_text(
        json.dumps({"schema_version": "9.0", "samples": []}), encoding="utf-8"
    )
    client = TestClient(create_app(tmp_path))

    payload = client.get("/api/runs").json()

    assert len(payload["runs"]) == 1
    assert {item["code"] for item in payload["diagnostics"]} == {
        "artifact_read_error",
        "unsupported_schema",
    }


def test_explorer_api_enforces_size_limit_and_ignores_non_artifact_files(
    tmp_path: Path,
) -> None:
    _write_artifact(tmp_path, "oversized.explorer.json", [_sample()])
    (tmp_path / "ordinary.json").write_text(json.dumps(_sample()), encoding="utf-8")
    client = TestClient(create_app(tmp_path, max_file_bytes=20))

    payload = client.get("/api/runs").json()

    assert payload["runs"] == []
    assert payload["diagnostics"][0]["code"] == "artifact_too_large"


def test_explorer_api_deduplicates_samples_and_returns_structured_404(tmp_path: Path) -> None:
    _write_artifact(tmp_path, "first.explorer.json", [_sample()])
    _write_artifact(tmp_path, "second.explorer.json", [_sample()])
    client = TestClient(create_app(tmp_path))

    assert len(client.get("/api/runs").json()["runs"]) == 1
    missing = client.get("/api/runs/missing/samples/none")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "sample_not_found"


def test_explorer_api_missing_root_is_an_empty_offline_safe_index(tmp_path: Path) -> None:
    missing_root = tmp_path / "not-created"
    client = TestClient(create_app(missing_root))

    assert client.get("/api/health").json()["rootExists"] is False
    assert client.get("/api/runs").json()["runs"] == []


def test_explorer_api_allows_local_frontend_cors(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/api/runs", headers={"Origin": "http://127.0.0.1:7860"})

    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:7860"


def test_explorer_api_serves_frontend_assets_and_spa_fallback(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    web_root = tmp_path / "web"
    assets = web_root / "assets"
    assets.mkdir(parents=True)
    (web_root / "index.html").write_text(
        '<!doctype html><div id="root"></div><script src="/assets/app-abc.js"></script>',
        encoding="utf-8",
    )
    (assets / "app-abc.js").write_text("window.explorerReady = true;", encoding="utf-8")
    client = TestClient(create_app(artifact_root, web_root=web_root))

    index = client.get("/")
    assert index.status_code == 200
    assert index.headers["content-type"].startswith("text/html")
    assert index.headers["cache-control"] == "no-cache"
    assert 'id="root"' in index.text

    deep_link = client.get("/analysis/attention?token=10")
    assert deep_link.status_code == 200
    assert deep_link.text == index.text

    asset = client.get("/assets/app-abc.js")
    assert asset.status_code == 200
    assert asset.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert asset.headers["x-content-type-options"] == "nosniff"
    asset_head = client.head("/assets/app-abc.js")
    assert asset_head.status_code == 200
    assert asset_head.content == b""
    assert asset_head.headers["cache-control"] == "public, max-age=31536000, immutable"

    missing_asset = client.get("/assets/missing.js")
    assert missing_asset.status_code == 404
    assert missing_asset.headers["content-type"].startswith("application/json")
    missing_api = client.get("/api/not-a-real-route")
    assert missing_api.status_code == 404
    assert missing_api.headers["content-type"].startswith("application/json")


def test_explorer_api_does_not_serve_files_outside_web_root(tmp_path: Path) -> None:
    web_root = tmp_path / "web"
    web_root.mkdir()
    (web_root / "index.html").write_text("explorer-index", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("not-public", encoding="utf-8")
    client = TestClient(create_app(tmp_path / "artifacts", web_root=web_root))

    response = client.get("/assets/../secret.txt")

    assert response.status_code == 200
    assert response.text == "explorer-index"
    assert "not-public" not in response.text
