"""Build immutable physical chunk sidecars for Explorer JSON artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

MANIFEST_PROTOCOL = "safelens-physical-chunks-v1"
CHUNK_COMPONENTS = (
    "residualCells",
    "logitLens",
    "jLens",
    "attentionHeads",
    "attentionCells",
    "mlpNeurons",
    "mlpCells",
    "attributionTracks",
    "attributionMethods",
    "nla",
    "patching",
    "intervention",
)


def sidecar_manifest_path(artifact_path: Path) -> Path:
    if not artifact_path.name.endswith(".explorer.json"):
        raise ValueError("Explorer sidecars require a *.explorer.json source artifact")
    return artifact_path.with_name(artifact_path.name.removesuffix(".json") + ".manifest.json")


def build_explorer_sidecar(artifact_path: Path, *, block_size: int = 512) -> Path:
    if block_size < 1 or block_size > 512:
        raise ValueError("block_size must be between 1 and 512")
    if not artifact_path.name.endswith(".explorer.json"):
        raise ValueError("Explorer sidecars require a *.explorer.json source artifact")
    artifact_path = artifact_path.expanduser().resolve(strict=True)
    encoded = artifact_path.read_bytes()
    source_sha = hashlib.sha256(encoded).hexdigest()
    payload = json.loads(encoded)
    samples = _extract_samples(payload)
    source_stat = artifact_path.stat()
    manifest_samples: list[dict[str, Any]] = []
    for sample in samples:
        token_count = len(sample["tokens"])
        sample_key = hashlib.sha256(
            f"{sample['runId']}\0{sample['sampleId']}".encode()
        ).hexdigest()[:16]
        component_manifests: dict[str, Any] = {}
        for component in CHUNK_COMPONENTS:
            blocks = []
            destination_ranges = list(_ranges(token_count, block_size))
            source_ranges = (
                destination_ranges if component == "attentionHeads" else [(0, token_count)]
            )
            for token_start, token_end in destination_ranges:
                for source_start, source_end in source_ranges:
                    data = _slice_component(
                        sample,
                        component,
                        token_start=token_start,
                        token_end=token_end,
                        source_start=source_start,
                        source_end=source_end,
                    )
                    relative = _block_relative_path(
                        source_sha,
                        sample_key,
                        component,
                        token_start,
                        token_end,
                        source_start if component == "attentionHeads" else None,
                        source_end if component == "attentionHeads" else None,
                    )
                    block_path = artifact_path.parent / relative
                    block_bytes = json.dumps(
                        data,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode("utf-8")
                    checksum = hashlib.sha256(block_bytes).hexdigest()
                    _write_immutable(block_path, block_bytes, checksum)
                    blocks.append(
                        {
                            "path": relative.as_posix(),
                            "tokenStart": token_start,
                            "tokenEnd": token_end,
                            "sourceStart": source_start if component == "attentionHeads" else None,
                            "sourceEnd": source_end if component == "attentionHeads" else None,
                            "sizeBytes": len(block_bytes),
                            "sha256": checksum,
                        }
                    )
            component_manifests[component] = {
                "component": component,
                "itemCount": _item_count(sample.get(component)),
                "rangeAxis": _range_axis(component),
                "layerFilter": component not in {"attributionTracks", "intervention"},
                "selectorFilter": component
                in {
                    "attentionHeads",
                    "mlpNeurons",
                    "attributionTracks",
                    "attributionMethods",
                    "nla",
                    "jLens",
                },
                "blocks": blocks,
            }
        manifest_samples.append(
            {
                "runId": sample["runId"],
                "sampleId": sample["sampleId"],
                "modelName": sample["modelName"],
                "modelSource": sample["modelSource"],
                "tokenCount": token_count,
                "layerCount": len(sample["layers"]),
                "base": {
                    key: value for key, value in sample.items() if key not in CHUNK_COMPONENTS
                },
                "components": component_manifests,
            }
        )
    manifest = {
        "schema_version": "1.0",
        "protocol": MANIFEST_PROTOCOL,
        "block_size": block_size,
        "source": {
            "path": artifact_path.name,
            "sizeBytes": len(encoded),
            "mtimeNs": source_stat.st_mtime_ns,
            "sha256": source_sha,
        },
        "samples": manifest_samples,
    }
    manifest_path = sidecar_manifest_path(artifact_path)
    temporary = manifest_path.with_name(f".{manifest_path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    os.replace(temporary, manifest_path)
    return manifest_path


def _extract_samples(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("artifact root must be an object")
    if "schema_version" in payload:
        if payload.get("schema_version") != "1.0":
            raise ValueError("sidecars require schema_version 1.0")
        samples = payload.get("samples")
    else:
        samples = [payload]
    if not isinstance(samples, list) or not samples:
        raise ValueError("artifact must contain at least one sample")
    for sample in samples:
        if not isinstance(sample, dict):
            raise ValueError("each sample must be an object")
        for key in ("runId", "sampleId", "modelName", "modelSource", "tokens", "layers"):
            if key not in sample:
                raise ValueError(f"sample is missing {key}")
        if not sample["tokens"] or not sample["layers"]:
            raise ValueError("sample tokens and layers must be non-empty")
    return samples


def _slice_component(
    sample: dict[str, Any],
    component: str,
    *,
    token_start: int,
    token_end: int,
    source_start: int,
    source_end: int,
) -> Any:
    value = sample.get(component)
    if component == "intervention":
        return value
    if component == "patching":
        if not isinstance(value, dict):
            return value
        return {
            **value,
            "cells": _position_rows(value.get("cells"), token_start, token_end),
            "positions": [
                item for item in value.get("positions", []) if token_start <= item < token_end
            ],
            "corruptedTokens": [
                item
                for item in value.get("corruptedTokens", [])
                if token_start <= item.get("index", -1) < token_end
            ],
            "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
        }
    if component in {"residualCells", "logitLens", "jLens", "attentionCells", "mlpCells", "nla"}:
        return _position_rows(value, token_start, token_end)
    if component == "attentionHeads":
        return [
            {
                **head,
                "distributionByToken": [
                    row[source_start:source_end]
                    for row in head.get("distributionByToken", [])[token_start:token_end]
                ],
                "chunk": {
                    "destinationStart": token_start,
                    "destinationEnd": token_end,
                    "sourceStart": source_start,
                    "sourceEnd": source_end,
                },
            }
            for head in value or []
        ]
    if component == "mlpNeurons":
        return [
            {
                **neuron,
                "activationsByToken": neuron.get("activationsByToken", [])[token_start:token_end],
                "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
            }
            for neuron in value or []
        ]
    if component == "attributionTracks":
        return [
            {
                **track,
                "values": track.get("values", [])[token_start:token_end],
                "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
            }
            for track in value or []
        ]
    if component == "attributionMethods":
        return [
            {
                **method,
                "rows": [
                    {
                        **row,
                        "values": row.get("values", [])[token_start:token_end],
                        "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
                    }
                    for row in method.get("rows", [])
                ],
            }
            for method in value or []
        ]
    raise ValueError(f"unsupported component {component}")


def _position_rows(value: Any, start: int, end: int) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [
        row for row in value if isinstance(row, dict) and start <= row.get("tokenIndex", -1) < end
    ]


def _ranges(token_count: int, block_size: int) -> Iterator[tuple[int, int]]:
    for start in range(0, token_count, block_size):
        yield start, min(token_count, start + block_size)


def _block_relative_path(
    source_sha: str,
    sample_key: str,
    component: str,
    token_start: int,
    token_end: int,
    source_start: int | None,
    source_end: int | None,
) -> Path:
    filename = f"t{token_start}-{token_end}"
    if source_start is not None and source_end is not None:
        filename += f"-s{source_start}-{source_end}"
    return Path(".safelens-blocks") / source_sha / sample_key / component / f"{filename}.json"


def _write_immutable(path: Path, payload: bytes, checksum: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise ValueError(f"immutable block checksum conflict at {path}")
        return
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def _item_count(value: Any) -> int:
    return len(value) if isinstance(value, list) else int(value is not None)


def _range_axis(component: str) -> str:
    if component == "attentionHeads":
        return "token-square"
    if component in {"mlpNeurons", "attributionTracks", "attributionMethods"}:
        return "token-values"
    if component == "intervention":
        return "none"
    return "token"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build immutable physical chunks and an atomic Explorer sidecar manifest."
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--block-size", type=int, default=512)
    args = parser.parse_args(argv)
    print(build_explorer_sidecar(args.artifact, block_size=args.block_size))


if __name__ == "__main__":
    main()
