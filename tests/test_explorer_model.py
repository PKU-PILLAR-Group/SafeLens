from __future__ import annotations

import json
from pathlib import Path

from SafeLens.explorer_model import (
    complete_hf_snapshot,
    complete_modelscope_snapshot,
    explorer_hf_model_config,
    explorer_job_device,
    resolve_explorer_pretrained_path,
)


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


def test_explorer_job_device_auto_prefers_cuda(monkeypatch) -> None:
    monkeypatch.delenv("SAFELENS_EXPLORER_JOB_DEVICE", raising=False)
    monkeypatch.setattr("torch.cuda.is_available", lambda: True)

    assert explorer_job_device() == "cuda:0"
    assert explorer_job_device("auto") == "cuda:0"


def test_explorer_job_device_auto_falls_back_to_cpu(monkeypatch) -> None:
    monkeypatch.delenv("SAFELENS_EXPLORER_JOB_DEVICE", raising=False)
    monkeypatch.setattr("torch.cuda.is_available", lambda: False)

    assert explorer_job_device() == "cpu"
    assert explorer_job_device("auto") == "cpu"


def test_explorer_job_device_preserves_explicit_device(monkeypatch) -> None:
    monkeypatch.setattr("torch.cuda.is_available", lambda: False)

    assert explorer_job_device("cpu") == "cpu"
    assert explorer_job_device("cuda:1") == "cuda:1"


def test_explorer_model_config_uses_gpu_dtype_and_complete_local_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    snapshot = _write_snapshot(tmp_path)
    monkeypatch.setenv("SAFELENS_EXPLORER_JOB_DEVICE", "cuda:0")
    monkeypatch.setenv("SAFELENS_EXPLORER_JOB_DTYPE", "bfloat16")
    monkeypatch.setenv(
        "SAFELENS_EXPLORER_MODEL_PATHS",
        json.dumps({"Qwen/Qwen2.5-7B-Instruct": str(snapshot)}),
    )

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


def test_modelscope_resolver_uses_complete_snapshot_without_network(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cache = tmp_path / "modelscope"
    snapshot = cache / "google" / "gemma-3-270m-it"
    snapshot.mkdir(parents=True)
    (snapshot / "config.json").write_text("{}", encoding="utf-8")
    (snapshot / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (snapshot / "model.safetensors").write_text("weights", encoding="utf-8")
    monkeypatch.setenv("MODELSCOPE_CACHE", str(cache))
    monkeypatch.setattr(
        "modelscope.snapshot_download",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("network lookup")),
    )

    assert complete_modelscope_snapshot("google/gemma-3-270m-it", str(cache)) == snapshot
    assert resolve_explorer_pretrained_path("google/gemma-3-270m-it") == (
        str(snapshot),
        True,
        "modelscope",
    )


def test_explorer_model_config_prefers_modelscope_for_cached_gemma_provider(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("SAFELENS_EXPLORER_MODEL_SOURCE", raising=False)
    monkeypatch.setenv("MODELSCOPE_CACHE", str(tmp_path / "modelscope"))

    config = explorer_hf_model_config(
        "google/gemma-3-270m-it",
        cache_dir=str(tmp_path / "hf"),
    )

    assert config.source == "modelscope"
    assert config.name == "google/gemma-3-270m-it"
    assert config.cache_dir == str(tmp_path / "modelscope")


def test_explorer_model_config_can_force_huggingface(monkeypatch) -> None:
    monkeypatch.setenv("SAFELENS_EXPLORER_MODEL_SOURCE", "huggingface")

    config = explorer_hf_model_config(
        "google/gemma-3-270m-it",
        cache_dir="/tmp/no-safelens-model",
    )

    assert config.source == "huggingface"
    assert config.name == "google/gemma-3-270m-it"
