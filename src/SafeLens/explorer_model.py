"""Shared local-model loading policy for Explorer workers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from SafeLens.core.base import ModelLoadConfig, PipelineConfig
from SafeLens.utils import HuggingFaceModelWrapper, build_model_wrapper

DEFAULT_EXPLORER_MODEL_CACHE = ".cache/safelens/local-explorer-real-flow"
DEFAULT_MODELSCOPE_MODEL_CACHE = ".cache/safelens/modelscope"

# ModelScope mirrors the public Gemma 3 checkpoints under the same model IDs.
# Keep this table small and explicit so an unrelated Hugging Face model is not
# silently redirected to a provider with different revisions or files.
MODELSCOPE_MODEL_IDS: dict[str, str] = {
    "google/gemma-3-270m-it": "google/gemma-3-270m-it",
    "google/gemma-3-12b-it": "google/gemma-3-12b-it",
}


def explorer_job_device(configured: str | None = None) -> str:
    """Resolve the device used by local Explorer jobs.

    An explicit device remains authoritative, while an unset or ``auto``
    value selects the first CUDA device when one is available.  CUDA probing
    is intentionally lazy so importing SafeLens does not require PyTorch.
    """
    if configured is None:
        configured = os.environ.get("SAFELENS_EXPLORER_JOB_DEVICE", "")
    configured = configured.strip()
    if configured and configured.lower() != "auto":
        return configured
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda:0"
    except (ImportError, RuntimeError):
        # A CPU-only PyTorch build or an unavailable CUDA driver should not
        # prevent the local Explorer from starting.
        pass
    return "cpu"


def _configured_local_model_path(model_id: str) -> Path | None:
    """Resolve an explicit or host-local model directory for an Explorer model."""
    configured = os.environ.get("SAFELENS_EXPLORER_MODEL_PATHS", "").strip()
    if configured:
        try:
            mapping = json.loads(configured)
        except json.JSONDecodeError as exc:
            raise ValueError("SAFELENS_EXPLORER_MODEL_PATHS must be a JSON object") from exc
        if isinstance(mapping, dict) and isinstance(mapping.get(model_id), str):
            return Path(mapping[model_id]).expanduser()
    if model_id == "google/gemma-2-9b-it":
        explicit = (
            os.environ.get("SAFELENS_GEMMA_2_9B_IT_MODEL_PATH")
            or os.environ.get("SAFELENS_GEMMA_2_9B_IT_MODEL")
        )
        if explicit:
            return Path(explicit).expanduser()
        for candidate in ("/ssd/models/Gemma2-9b-it", "/ssd/models/gemma-2-9b-it"):
            path = Path(candidate)
            if path.is_dir():
                return path
    # Research workspaces commonly keep downloaded Hugging Face snapshots in a
    # shared model directory rather than the per-job cache. Discover those
    # directories so Explorer jobs can run offline without copying multi-GB
    # checkpoints or requiring a JSON environment override.
    model_roots = (
        Path("/workspace/model"),
        Path("/workspace/models"),
        Path("/ssd/models"),
        Path.cwd() / "models",
    )
    directory_names = (model_id.replace("/", "--"), model_id.rsplit("/", 1)[-1])
    for root in model_roots:
        for name in directory_names:
            candidate = root / name
            if candidate.is_dir() and (candidate / "config.json").is_file():
                return candidate
    return None


def explorer_model_source(model_id: str) -> str:
    """Resolve the provider used by local Explorer workers.

    ``auto`` keeps complete local snapshots offline and uses ModelScope for
    the Gemma profiles that are commonly unavailable from Hugging Face in the
    deployment environment. Set ``SAFELENS_EXPLORER_MODEL_SOURCE`` to
    ``huggingface`` or ``modelscope`` to force a provider.
    """
    configured = os.environ.get("SAFELENS_EXPLORER_MODEL_SOURCE", "auto").strip().lower()
    if configured in {"hf", "huggingface"}:
        return "huggingface"
    if configured in {"ms", "modelscope"}:
        return "modelscope"
    if configured not in {"", "auto", "local"}:
        raise ValueError(
            "SAFELENS_EXPLORER_MODEL_SOURCE must be one of auto, huggingface, modelscope."
        )
    if configured == "local":
        return "local"
    if model_id in MODELSCOPE_MODEL_IDS:
        try:
            import modelscope  # noqa: F401
        except ImportError:
            pass
        else:
            return "modelscope"
    return "huggingface"


def explorer_modelscope_id(model_id: str) -> str:
    """Return the ModelScope repository ID for a supported Explorer model."""
    return MODELSCOPE_MODEL_IDS.get(model_id, model_id)


def explorer_hf_model_config(
    model_id: str,
    *,
    cache_dir: str = DEFAULT_EXPLORER_MODEL_CACHE,
) -> ModelLoadConfig:
    """Build the consistent device, dtype, and offline-cache config used by Explorer jobs."""
    device = explorer_job_device()
    dtype = os.environ.get(
        "SAFELENS_EXPLORER_JOB_DTYPE",
        "float32" if device == "cpu" else "bfloat16",
    )
    local_snapshot = _configured_local_model_path(model_id)
    if local_snapshot is not None and not local_snapshot.is_dir():
        raise FileNotFoundError(f"Configured local model path does not exist: {local_snapshot}")
    local_snapshot = local_snapshot or complete_hf_snapshot(model_id, cache_dir)
    source = "local" if local_snapshot is not None else explorer_model_source(model_id)
    if source == "local" and local_snapshot is None:
        raise FileNotFoundError(
            f"No complete local snapshot for {model_id!r} in {cache_dir!r}."
        )
    provider_cache = cache_dir
    model_name = model_id
    if source == "modelscope":
        provider_cache = os.environ.get(
            "SAFELENS_EXPLORER_MODELSCOPE_CACHE",
            os.environ.get("MODELSCOPE_CACHE", DEFAULT_MODELSCOPE_MODEL_CACHE),
        )
        model_name = explorer_modelscope_id(model_id)
    load_kwargs: dict[str, Any] = {"low_cpu_mem_usage": device != "cpu"}
    tokenizer_kwargs: dict[str, Any] = {}
    if local_snapshot is not None:
        load_kwargs["local_files_only"] = True
        tokenizer_kwargs["local_files_only"] = True
    return PipelineConfig.model_validate(
        {
            "model": {
                "source": source,
                "name": model_name,
                "local_dir": str(local_snapshot) if local_snapshot is not None else None,
                "device": device,
                "dtype": dtype,
                "cache_dir": provider_cache,
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


def resolve_explorer_pretrained_path(
    model_id: str,
    *,
    cache_dir: str = DEFAULT_EXPLORER_MODEL_CACHE,
) -> tuple[str, bool, str]:
    """Resolve a Transformers path for workers that do not use SafeLens wrappers.

    Returns ``(path, local_files_only, source)``. ModelScope snapshots are
    materialized before handing the path to a raw Transformers/J-Lens loader,
    so those loaders never fall back to Hugging Face implicitly.
    """
    config = explorer_hf_model_config(model_id, cache_dir=cache_dir)
    if config.source == "local":
        if not config.local_dir:
            raise FileNotFoundError(f"No local snapshot configured for {model_id!r}.")
        return config.local_dir, True, config.source
    if config.source == "modelscope":
        provider_cache = config.cache_dir or DEFAULT_MODELSCOPE_MODEL_CACHE
        local_snapshot = complete_modelscope_snapshot(config.name, provider_cache)
        if local_snapshot is not None:
            return str(local_snapshot), True, config.source
        try:
            from modelscope import snapshot_download
        except ImportError as exc:
            raise ImportError(
                "ModelScope is required for this Explorer model. "
                "Install SafeLens with the 'modelscope' extra."
            ) from exc
        path = snapshot_download(
            model_id=config.name,
            cache_dir=config.cache_dir,
            revision=config.revision,
        )
        return str(path), True, config.source
    return config.name, False, config.source


def complete_modelscope_snapshot(model_id: str, cache_dir: str) -> Path | None:
    """Return a complete Transformers snapshot in the standard ModelScope cache layout."""
    snapshot = Path(cache_dir) / model_id
    required_metadata = (snapshot / "config.json", snapshot / "tokenizer_config.json")
    if not all(path.is_file() for path in required_metadata):
        return None
    weights = _snapshot_weight_files(snapshot)
    if not weights or not all(path.is_file() and path.stat().st_size > 0 for path in weights):
        return None
    return snapshot


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
