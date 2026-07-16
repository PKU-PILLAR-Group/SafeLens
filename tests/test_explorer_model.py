from __future__ import annotations

import json
from pathlib import Path

from SafeLens.explorer_model import complete_hf_snapshot, explorer_hf_model_config


def _write_snapshot(cache: Path, *, missing_second_shard: bool = False) -> Path:
    repository = cache / "models--Qwen--Qwen2.5-7B-Instruct"
    snapshot = repository / "snapshots" / "revision-1"
    snapshot.mkdir(parents=True)
    (repository / "refs").mkdir()
    (repository / "refs" / "main").write_text("revision-1", encoding="utf-8")
    (snapshot / "config.json").write_text("{}", encoding="utf-8")
    (snapshot / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    first = "model-00001-of-00002.safetensors"
    second = "model-00002-of-00002.safetensors"
    (snapshot / first).write_text("weights", encoding="utf-8")
    if not missing_second_shard:
        (snapshot / second).write_text("weights", encoding="utf-8")
    (snapshot / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"layer.0": first, "layer.1": second}}),
        encoding="utf-8",
    )
    return snapshot


def test_explorer_model_config_uses_gpu_dtype_and_complete_local_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    snapshot = _write_snapshot(tmp_path)
    monkeypatch.setenv("SAFELENS_EXPLORER_JOB_DEVICE", "cuda:0")
    monkeypatch.setenv("SAFELENS_EXPLORER_JOB_DTYPE", "bfloat16")

    config = explorer_hf_model_config(
        "Qwen/Qwen2.5-7B-Instruct",
        cache_dir=str(tmp_path),
    )

    assert config.device == "cuda:0"
    assert config.dtype == "bfloat16"
    assert config.source == "local"
    assert config.local_dir == str(snapshot)
    assert config.load_kwargs == {"low_cpu_mem_usage": True, "local_files_only": True}
    assert config.tokenizer_kwargs == {"local_files_only": True}


def test_complete_hf_snapshot_rejects_a_missing_indexed_weight_shard(tmp_path: Path) -> None:
    _write_snapshot(tmp_path, missing_second_shard=True)

    assert complete_hf_snapshot("Qwen/Qwen2.5-7B-Instruct", str(tmp_path)) is None
