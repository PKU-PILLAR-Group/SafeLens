"""Provider-aware loading helpers for Explorer sparse autoencoders."""

from __future__ import annotations

import importlib.util
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from SafeLens.explorer_model import DEFAULT_MODELSCOPE_MODEL_CACHE
from SafeLens.sae_profiles import (
    GEMMA_SCOPE_9B_IT_MODEL,
    GEMMA_SCOPE_9B_IT_RELEASE,
    GEMMA_SCOPE_9B_IT_SAE_FOLDERS,
    GEMMA_SCOPE_9B_IT_SAE_ID,
)

GEMMA_SCOPE_2_270M_IT_RELEASE = "gemma-scope-2-270m-it-res"
GEMMA_SCOPE_2_270M_IT_REPO = "google/gemma-scope-2-270m-it"
GEMMA_SCOPE_2_270M_IT_MODEL = "google/gemma-3-270m-it"
NEURONPEDIA_GEMMA_MODEL = "gemma-3-270m-it"
NEURONPEDIA_GEMMA_9B_MODEL = "gemma-2-9b-it"

SAEConverter = Callable[
    [str, str, str, bool, dict[str, Any] | None],
    tuple[dict[str, Any], dict[str, Any], None],
]


@dataclass
class LocalJumpReLUSAE:
    """Small SAE Lens-compatible wrapper for official Gemma Scope weights.

    Gemma Scope publishes JumpReLU parameters directly.  Keeping this adapter
    local avoids making the Explorer intervention workflow depend on the
    optional ``sae_lens`` package merely to run ``encode`` and ``decode``.
    """

    W_enc: Any
    W_dec: Any
    b_enc: Any
    b_dec: Any
    threshold: Any
    model_name: str
    release: str
    sae_id: str

    @property
    def cfg(self) -> Any:
        class _Config:
            pass

        config = _Config()
        config.model_name = self.model_name
        config.metadata = {"model_name": self.model_name}
        return config

    def encode(self, activation: Any) -> Any:
        import torch

        x = activation.to(device=self.W_enc.device, dtype=torch.float32)
        pre = x @ self.W_enc.float() + self.b_enc.float()
        return pre * (pre > self.threshold.float())

    def decode(self, features: Any) -> Any:
        x = features.to(device=self.W_dec.device, dtype=self.W_dec.dtype)
        return x @ self.W_dec + self.b_dec.to(device=x.device, dtype=x.dtype)

    def parameters(self):
        # The worker only uses this to determine the SAE dtype.
        yield self.W_dec


def explorer_sae_source(release: str) -> str:
    """Choose the checkpoint provider for an Explorer SAE release."""
    configured = os.environ.get("SAFELENS_EXPLORER_SAE_SOURCE", "auto").strip().lower()
    if configured in {"hf", "huggingface"}:
        return "huggingface"
    if configured in {"ms", "modelscope"}:
        return "modelscope"
    if configured not in {"", "auto"}:
        raise ValueError(
            "SAFELENS_EXPLORER_SAE_SOURCE must be one of auto, huggingface, modelscope."
        )
    if (
        release == GEMMA_SCOPE_2_270M_IT_RELEASE
        and importlib.util.find_spec("modelscope") is not None
    ):
        return "modelscope"
    return "huggingface"


def explorer_sae_converter(release: str) -> SAEConverter | None:
    """Return a custom SAE Lens converter when the release uses ModelScope."""
    if explorer_sae_source(release) == "modelscope":
        if release != GEMMA_SCOPE_2_270M_IT_RELEASE:
            raise ValueError(f"No ModelScope SAE mapping is configured for {release!r}.")
        return gemma_3_sae_modelscope_loader
    return None


def neuronpedia_feature_info(
    *,
    model_name: str,
    layer: int,
    sae_id: str,
    feature_index: int,
) -> dict[str, Any]:
    """Resolve an optional human explanation without sending prompt data off-box.

    Gemma Scope weights contain no feature descriptions. Neuronpedia stores
    descriptions and positive/negative logit token evidence separately, so
    only the model/checkpoint/index are sent. The response is cached locally
    and a missing network connection degrades to an explicit index-only label.
    """
    url = _neuronpedia_feature_url(model_name, layer, sae_id, feature_index)
    fallback: dict[str, Any] = {
        "label": f"Gemma Scope feature {feature_index}",
        "source": "index",
        "url": url,
        "positiveTokens": [],
        "negativeTokens": [],
        "maxActApprox": None,
        "vectorDefaultSteerStrength": None,
    }
    if url is None:
        return fallback
    api_url = url.replace(
        "https://www.neuronpedia.org/",
        "https://www.neuronpedia.org/api/feature/",
        1,
    )
    cache_path = _feature_info_cache_path(model_name, layer, sae_id, feature_index)
    cached = _read_feature_info_cache(cache_path)
    if cached is not None and (
        "maxActApprox" in cached and "vectorDefaultSteerStrength" in cached
    ):
        cached_url = cached.get("url")
        if isinstance(cached_url, str) and "/api/feature/" in cached_url:
            cached["url"] = cached_url.replace("/api/feature/", "/", 1)
            _write_feature_info_cache(cache_path, cached)
        return cached
    source = os.environ.get("SAFELENS_EXPLORER_FEATURE_LABEL_SOURCE", "auto").strip().lower()
    if source in {"", "auto", "neuronpedia"}:
        try:
            request = Request(
                api_url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "SafeLens Local Explorer feature metadata",
                },
            )
            with urlopen(
                request,
                timeout=float(os.environ.get("SAFELENS_EXPLORER_FEATURE_LABEL_TIMEOUT", "2")),
            ) as response:
                payload = json.loads(response.read(2_000_000).decode("utf-8"))
            explanation = next(
                (
                    item.get("description")
                    for item in payload.get("explanations", [])
                    if isinstance(item, dict)
                    and isinstance(item.get("description"), str)
                    and item["description"].strip()
                ),
                None,
            )
            if explanation:
                info = {
                    "label": explanation.strip(),
                    "source": "neuronpedia",
                    "url": url,
                    "positiveTokens": _string_list(payload.get("pos_str")),
                    "negativeTokens": _string_list(payload.get("neg_str")),
                    "maxActApprox": _finite_number(payload.get("maxActApprox")),
                    "vectorDefaultSteerStrength": _finite_number(
                        payload.get("vectorDefaultSteerStrength")
                    ),
                }
                _write_feature_info_cache(cache_path, info)
                return info
        except (OSError, URLError, ValueError, TypeError, KeyError):
            pass
    return fallback


def _neuronpedia_feature_url(
    model_name: str,
    layer: int,
    sae_id: str,
    feature_index: int,
) -> str | None:
    if model_name == GEMMA_SCOPE_9B_IT_MODEL and (
        sae_id == GEMMA_SCOPE_9B_IT_SAE_ID
        or (sae_id.startswith("layer_") and "width_131k" in sae_id)
    ):
        return f"https://www.neuronpedia.org/{NEURONPEDIA_GEMMA_9B_MODEL}/{layer}-gemmascope-res-131k/{feature_index}"
    if (
        model_name != GEMMA_SCOPE_2_270M_IT_MODEL
        or not sae_id.startswith("layer_")
        or "width_16k" not in sae_id
    ):
        return None
    return (
        f"https://www.neuronpedia.org/{NEURONPEDIA_GEMMA_MODEL}/"
        f"{layer}-gemmascope-2-res-16k/{feature_index}"
    )


def _feature_info_cache_path(
    model_name: str,
    layer: int,
    sae_id: str,
    feature_index: int,
) -> Path:
    root = Path(
        os.environ.get(
            "SAFELENS_EXPLORER_FEATURE_LABEL_CACHE",
            ".cache/safelens/feature-labels",
        )
    )
    safe_model = model_name.replace("/", "--")
    return root / f"{safe_model}--L{layer}--{sae_id}--F{feature_index}.json"


def _read_feature_info_cache(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("label"), str):
        return None
    return payload


def _write_feature_info_cache(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)][:8]


def _finite_number(value: Any) -> float | None:
    """Normalize optional Neuronpedia numeric metadata without leaking NaN."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    return number if number == number and abs(number) != float("inf") else None


def gemma_3_sae_modelscope_loader(
    repo_id: str,
    folder_name: str,
    device: str = "cpu",
    force_download: bool = False,
    cfg_overrides: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], None]:
    """Load one Gemma Scope checkpoint from its official ModelScope mirror."""
    if repo_id != GEMMA_SCOPE_2_270M_IT_REPO:
        raise ValueError(f"Unsupported ModelScope Gemma Scope repository: {repo_id!r}.")
    folder = Path(folder_name)
    if folder.is_absolute() or ".." in folder.parts or len(folder.parts) != 2:
        raise ValueError(f"Invalid Gemma Scope checkpoint path: {folder_name!r}.")
    if folder.parts[0] != "resid_post":
        raise ValueError(f"Unsupported Gemma Scope activation site: {folder.parts[0]!r}.")

    try:
        from modelscope import snapshot_download
    except ImportError as exc:
        raise ImportError(
            "ModelScope is required for this Gemma Scope checkpoint. "
            "Install SafeLens with the 'modelscope' extra."
        ) from exc

    cache_dir = os.environ.get(
        "SAFELENS_EXPLORER_SAE_MODELSCOPE_CACHE",
        os.environ.get(
            "SAFELENS_EXPLORER_MODELSCOPE_CACHE",
            os.environ.get("MODELSCOPE_CACHE", DEFAULT_MODELSCOPE_MODEL_CACHE),
        ),
    )
    relative_config = folder / "config.json"
    relative_weights = folder / "params.safetensors"
    snapshot = Path(cache_dir) / repo_id
    if force_download or not all(
        (snapshot / relative_path).is_file()
        for relative_path in (relative_config, relative_weights)
    ):
        snapshot = Path(
            snapshot_download(
                model_id=repo_id,
                cache_dir=cache_dir,
                allow_patterns=[relative_config.as_posix(), relative_weights.as_posix()],
            )
        )
    config_path = snapshot / relative_config
    weights_path = snapshot / relative_weights
    if not config_path.is_file() or not weights_path.is_file():
        raise FileNotFoundError(f"Incomplete Gemma Scope checkpoint at {snapshot / folder}.")

    raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    if raw_config.get("architecture") != "jump_relu":
        raise ValueError(
            f"Unexpected Gemma Scope architecture: {raw_config.get('architecture')!r}."
        )
    layer_match = re.search(r"layer_(\d+)", folder.name)
    if layer_match is None:
        raise ValueError(f"Could not infer a layer from {folder_name!r}.")

    from safetensors import safe_open
    from safetensors.torch import load_file

    with safe_open(weights_path, framework="pt", device="cpu") as weights:
        d_in, d_sae = weights.get_slice("w_enc").get_shape()

    layer = int(layer_match.group(1))
    config: dict[str, Any] = {
        "architecture": "jumprelu",
        "d_in": d_in,
        "d_sae": d_sae,
        "dtype": "float32",
        "model_name": str(raw_config["model_name"])
        .replace("-v3", "-3")
        .replace("-270m-pt", "-270m"),
        "hook_name": f"blocks.{layer}.hook_resid_post",
        "hook_head_index": None,
        "finetuning_scaling_factor": False,
        "sae_lens_training_version": None,
        "prepend_bos": True,
        "dataset_path": "monology/pile-uncopyrighted",
        "context_size": 1024,
        "apply_b_dec_to_input": False,
        "normalize_activations": "none",
        "reshape_activations": "none",
        "hf_hook_name": raw_config.get("hf_hook_point_in"),
        "device": device,
    }
    if cfg_overrides is not None:
        config.update(cfg_overrides)

    raw_state = load_file(str(weights_path), device=device)
    state = {
        "W_enc": raw_state["w_enc"].float(),
        "W_dec": raw_state["w_dec"].float(),
        "b_enc": raw_state["b_enc"].float(),
        "b_dec": raw_state["b_dec"].float(),
        "threshold": raw_state["threshold"].float(),
    }
    return config, state, None


def _gemma_scope_9b_checkpoint_path(layer: int = 9) -> Path:
    """Return the canonical local 9B checkpoint path used by the SAE demo."""
    configured = os.environ.get("SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH") or os.environ.get(
        "SAFELENS_GEMMA_SAE_PATH"
    )
    try:
        folder = GEMMA_SCOPE_9B_IT_SAE_FOLDERS[int(layer)]
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Unsupported Gemma Scope 9B layer: {layer}") from exc
    relative = Path(f"gemma-scope-9b-it-res/{folder}/params.npz")
    candidates = []
    if configured and layer == 9:
        candidates.append(Path(configured).expanduser())
    configured_root = os.environ.get("SAFELENS_GEMMA_SAE_CACHE")
    if configured_root:
        candidates.append(Path(configured_root).expanduser() / relative)
    candidates.extend(
        [
            Path("/ssd/yqy/cache/safelens") / relative,
            Path(".cache/safelens") / relative,
        ]
    )
    return next((candidate for candidate in candidates if candidate.is_file()), candidates[-1])


def _gemma_scope_270m_checkpoint_paths(sae_id: str) -> tuple[Path, Path]:
    """Resolve a cached 270M config and weights pair across known cache layouts."""
    folder = Path("resid_post") / sae_id
    cache_root = Path(
        os.environ.get(
            "SAFELENS_EXPLORER_SAE_CACHE",
            os.environ.get("SAFELENS_EXPLORER_MODELSCOPE_CACHE", ".cache/safelens/explorer-sae"),
        )
    ).expanduser()
    candidates = (
        cache_root / GEMMA_SCOPE_2_270M_IT_REPO / folder,
        cache_root
        / "models"
        / GEMMA_SCOPE_2_270M_IT_REPO.replace("/", "--")
        / "snapshots"
        / "master"
        / folder,
        cache_root / folder,
    )
    for candidate in candidates:
        config_path = candidate / "config.json"
        weights_path = candidate / "params.safetensors"
        if config_path.is_file() and weights_path.is_file():
            return config_path, weights_path
    hf_snapshots = cache_root / (
        "models--" + GEMMA_SCOPE_2_270M_IT_REPO.replace("/", "--")
    ) / "snapshots"
    for snapshot in sorted(hf_snapshots.glob("*/"), reverse=True):
        candidate = snapshot / folder
        if (candidate / "config.json").is_file() and (candidate / "params.safetensors").is_file():
            return candidate / "config.json", candidate / "params.safetensors"
    return candidates[0] / "config.json", candidates[0] / "params.safetensors"


def _gemma_scope_270m_cache_root() -> Path:
    return Path(
        os.environ.get(
            "SAFELENS_EXPLORER_SAE_CACHE",
            os.environ.get("SAFELENS_EXPLORER_MODELSCOPE_CACHE", ".cache/safelens/explorer-sae"),
        )
    ).expanduser()


def _download_gemma_scope_270m_checkpoint(sae_id: str, cache_root: Path) -> tuple[Path, Path]:
    """Download only the selected public 270M Gemma Scope dictionary."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError(
            "Gemma Scope 270M weights are not cached and huggingface_hub is unavailable."
        ) from exc
    folder = Path("resid_post") / sae_id
    snapshot = Path(
        snapshot_download(
            repo_id=GEMMA_SCOPE_2_270M_IT_REPO,
            cache_dir=str(cache_root),
            allow_patterns=[
                (folder / "config.json").as_posix(),
                (folder / "params.safetensors").as_posix(),
            ],
        )
    )
    return snapshot / folder / "config.json", snapshot / folder / "params.safetensors"


def load_local_gemma_scope_sae(
    *,
    model_name: str,
    release: str,
    sae_id: str,
    device: str,
    dtype: Any = None,
) -> LocalJumpReLUSAE:
    """Load an official Gemma Scope checkpoint without importing SAE Lens."""
    import torch

    if model_name == GEMMA_SCOPE_9B_IT_MODEL and release == GEMMA_SCOPE_9B_IT_RELEASE:
        try:
            layer = int(sae_id.split("/", 1)[0].removeprefix("layer_"))
        except (AttributeError, ValueError):
            layer = -1
        expected_sae_id = f"layer_{layer}/width_131k/canonical"
        if sae_id != expected_sae_id or layer not in GEMMA_SCOPE_9B_IT_SAE_FOLDERS:
            raise ValueError(f"Unsupported Gemma Scope 9B SAE ID: {sae_id!r}.")
        checkpoint = _gemma_scope_9b_checkpoint_path(layer)
        if not checkpoint.is_file():
            raise FileNotFoundError(
                f"Gemma Scope 9B checkpoint not found at {checkpoint}. "
                "Set SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH or download the canonical params.npz."
            )
        import numpy as np

        try:
            with np.load(checkpoint, allow_pickle=False) as payload:
                arrays = {
                    name: np.ascontiguousarray(payload[name])
                    for name in ("W_enc", "W_dec", "b_enc", "b_dec", "threshold")
                }
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ValueError(
                f"Could not read Gemma Scope 9B checkpoint {checkpoint}: {exc}"
            ) from exc
        target_dtype = dtype or torch.float32
        return LocalJumpReLUSAE(
            W_enc=torch.from_numpy(arrays["W_enc"]).to(device=device, dtype=torch.float32),
            W_dec=torch.from_numpy(arrays["W_dec"]).to(device=device, dtype=target_dtype),
            b_enc=torch.from_numpy(arrays["b_enc"]).to(device=device, dtype=torch.float32),
            b_dec=torch.from_numpy(arrays["b_dec"]).to(device=device, dtype=target_dtype),
            threshold=torch.from_numpy(arrays["threshold"]).to(device=device, dtype=torch.float32),
            model_name=model_name,
            release=release,
            sae_id=sae_id,
        )

    if model_name != GEMMA_SCOPE_2_270M_IT_MODEL or release != GEMMA_SCOPE_2_270M_IT_RELEASE:
        raise ValueError(f"Unsupported local Gemma Scope profile: {model_name}/{release}/{sae_id}.")
    config_path, weights_path = _gemma_scope_270m_checkpoint_paths(sae_id)
    if not config_path.is_file() or not weights_path.is_file():
        cache_root = _gemma_scope_270m_cache_root()
        config_path, weights_path = _download_gemma_scope_270m_checkpoint(sae_id, cache_root)
    raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    if raw_config.get("architecture") != "jump_relu":
        raise ValueError(
            f"Unexpected Gemma Scope architecture: {raw_config.get('architecture')!r}."
        )
    from safetensors.torch import load_file

    raw_state = load_file(str(weights_path), device=device)
    target_dtype = dtype or torch.float32
    required = ("w_enc", "w_dec", "b_enc", "b_dec", "threshold")
    if any(name not in raw_state for name in required):
        raise ValueError(f"Gemma Scope checkpoint is missing one of: {', '.join(required)}")
    return LocalJumpReLUSAE(
        W_enc=raw_state["w_enc"].to(dtype=torch.float32),
        W_dec=raw_state["w_dec"].to(dtype=target_dtype),
        b_enc=raw_state["b_enc"].to(dtype=torch.float32),
        b_dec=raw_state["b_dec"].to(dtype=target_dtype),
        threshold=raw_state["threshold"].to(dtype=torch.float32),
        model_name=model_name,
        release=release,
        sae_id=sae_id,
    )


def gemma_scope_local_checkpoint_available(*, model_name: str, release: str, sae_id: str) -> bool:
    """Check for a local fallback checkpoint without downloading during preflight."""
    if model_name == GEMMA_SCOPE_9B_IT_MODEL and release == GEMMA_SCOPE_9B_IT_RELEASE:
        try:
            layer = int(sae_id.split("/", 1)[0].removeprefix("layer_"))
        except (AttributeError, ValueError):
            return False
        return (
            sae_id == f"layer_{layer}/width_131k/canonical"
            and layer in GEMMA_SCOPE_9B_IT_SAE_FOLDERS
            and _gemma_scope_9b_checkpoint_path(layer).is_file()
        )
    if model_name == GEMMA_SCOPE_2_270M_IT_MODEL and release == GEMMA_SCOPE_2_270M_IT_RELEASE:
        config_path, weights_path = _gemma_scope_270m_checkpoint_paths(sae_id)
        return config_path.is_file() and weights_path.is_file()
    return False
