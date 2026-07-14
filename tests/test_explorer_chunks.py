from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from SafeLens.explorer_chunks import build_explorer_sidecar, sidecar_manifest_path


def _artifact(path: Path, *, marker: str = "v1") -> Path:
    tokens = [
        {
            "index": index,
            "text": f"t{index}",
            "tokenId": index,
            "source": "prompt",
            "risk": index / 4,
            "attribution": index / 4,
        }
        for index in range(4)
    ]
    sample = {
        "runId": "physical-run",
        "sampleId": "physical-sample",
        "modelName": "test/model",
        "modelSource": "test",
        "prompt": marker,
        "tokens": tokens,
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
                    [destination * 10 + source for source in range(4)] for destination in range(4)
                ],
            }
        ],
        "mlpNeurons": [
            {
                "id": "L1N0",
                "layer": 1,
                "activationsByToken": [0.0, 0.1, 0.2, 0.3],
            }
        ],
        "attributionTracks": [{"name": "track", "values": [0.0, 0.1, 0.2, 0.3]}],
        "attributionMethods": [
            {
                "id": "method",
                "rows": [{"layer": 1, "values": [0.0, 0.1, 0.2, 0.3]}],
            }
        ],
        "logitLens": [],
        "attentionCells": [],
        "mlpCells": [],
        "nla": [],
    }
    path.write_text(
        json.dumps({"schema_version": "1.0", "samples": [sample]}),
        encoding="utf-8",
    )
    return path


def test_builds_checksum_verified_physical_blocks_and_atomic_manifest(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path / "run.explorer.json")
    manifest_path = build_explorer_sidecar(artifact, block_size=2)
    assert manifest_path == sidecar_manifest_path(artifact)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["protocol"] == "safelens-physical-chunks-v1"
    assert manifest["block_size"] == 2
    assert manifest["samples"][0]["base"]["prompt"] == "v1"
    components = manifest["samples"][0]["components"]
    assert len(components["residualCells"]["blocks"]) == 2
    assert len(components["attentionHeads"]["blocks"]) == 4
    assert "residualCells" not in manifest["samples"][0]["base"]

    for component in components.values():
        for block in component["blocks"]:
            block_path = manifest_path.parent / block["path"]
            payload = block_path.read_bytes()
            assert len(payload) == block["sizeBytes"]
            assert hashlib.sha256(payload).hexdigest() == block["sha256"]

    first_sha = manifest["source"]["sha256"]
    _artifact(artifact, marker="v2")
    assert build_explorer_sidecar(artifact, block_size=2) == manifest_path
    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert updated["source"]["sha256"] != first_sha
    assert updated["samples"][0]["base"]["prompt"] == "v2"


def test_rejects_invalid_sidecar_sources_and_block_sizes(tmp_path: Path) -> None:
    source = tmp_path / "not-an-explorer.json"
    source.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="explorer.json"):
        build_explorer_sidecar(source)
    artifact = _artifact(tmp_path / "run.explorer.json")
    with pytest.raises(ValueError, match="block_size"):
        build_explorer_sidecar(artifact, block_size=513)
