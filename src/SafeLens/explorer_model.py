"""Shared local-model loading policy for Explorer workers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from SafeLens.core.base import ModelLoadConfig, PipelineConfig
from SafeLens.utils import HuggingFaceModelWrapper, build_model_wrapper

DEFAULT_EXPLORER_MODEL_CACHE = ".cache/safelens/local-explorer-real-flow"


def explorer_hf_model_config(
    model_id: str,
    *,
    cache_dir: str = DEFAULT_EXPLORER_MODEL_CACHE,
) -> ModelLoadConfig:
    """Build the consistent device, dtype, and offline-cache config used by Explorer jobs."""
    device = os.environ.get("SAFELENS_EXPLORER_JOB_DEVICE", "cpu")
    dtype = os.environ.get(
        "SAFELENS_EXPLORER_JOB_DTYPE",
        "float32" if device == "cpu" else "bfloat16",
    )
    local_snapshot = complete_hf_snapshot(model_id, cache_dir)
    load_kwargs: dict[str, Any] = {"low_cpu_mem_usage": device != "cpu"}
    tokenizer_kwargs: dict[str, Any] = {}
    if local_snapshot is not None:
        load_kwargs["local_files_only"] = True
        tokenizer_kwargs["local_files_only"] = True
    return PipelineConfig.model_validate(
        {
            "model": {
                "source": "local" if local_snapshot is not None else "huggingface",
                "name": model_id,
                "local_dir": str(local_snapshot) if local_snapshot is not None else None,
                "device": device,
                "dtype": dtype,
                "cache_dir": cache_dir,
                "trust_remote_code": False,
                "load_kwargs": load_kwargs,
                "tokenizer_kwargs": tokenizer_kwargs,
            }
        }
    ).model


def load_explorer_hf_model(
    model_id: str,
    *,
    cache_dir: str = DEFAULT_EXPLORER_MODEL_CACHE,
) -> HuggingFaceModelWrapper:
    """Load one Hugging Face model using the shared Explorer runtime policy."""
    wrapper = build_model_wrapper(explorer_hf_model_config(model_id, cache_dir=cache_dir))
    if not isinstance(wrapper, HuggingFaceModelWrapper):
        raise TypeError(f"expected HuggingFaceModelWrapper, got {type(wrapper).__name__}")
    wrapper.load_model()
    return wrapper


def complete_hf_snapshot(model_id: str, cache_dir: str) -> Path | None:
    """Return a complete local Hugging Face snapshot, including all indexed weight shards."""
    repository = Path(cache_dir) / f"models--{model_id.replace('/', '--')}"
    reference = repository / "refs" / "main"
    if not reference.is_file():
        return None
    revision = reference.read_text(encoding="utf-8").strip()
    snapshot = repository / "snapshots" / revision
    required_metadata = (snapshot / "config.json", snapshot / "tokenizer_config.json")
    if not all(path.is_file() for path in required_metadata):
        return None
    weights = _snapshot_weight_files(snapshot)
    if not weights or not all(path.is_file() and path.stat().st_size > 0 for path in weights):
        return None
    return snapshot


def _snapshot_weight_files(snapshot: Path) -> list[Path]:
    for index_name in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        index_path = snapshot / index_name
        if not index_path.is_file():
            continue
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
            weight_map = payload["weight_map"]
            filenames = sorted({str(value) for value in weight_map.values()})
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            return []
        return [snapshot / filename for filename in filenames]
    return sorted(snapshot.glob("*.safetensors")) + sorted(snapshot.glob("pytorch_model*.bin"))
