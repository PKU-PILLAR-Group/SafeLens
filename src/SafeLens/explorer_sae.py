"""Provider-aware loading helpers for Explorer sparse autoencoders."""

from __future__ import annotations

import importlib.util
import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from SafeLens.explorer_model import DEFAULT_MODELSCOPE_MODEL_CACHE

GEMMA_SCOPE_2_270M_IT_RELEASE = "gemma-scope-2-270m-it-res"
GEMMA_SCOPE_2_270M_IT_REPO = "google/gemma-scope-2-270m-it"
GEMMA_SCOPE_2_270M_IT_MODEL = "google/gemma-3-270m-it"
NEURONPEDIA_GEMMA_MODEL = "gemma-3-270m-it"

SAEConverter = Callable[
    [str, str, str, bool, dict[str, Any] | None],
    tuple[dict[str, Any], dict[str, Any], None],
]


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
    if cached is not None:
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
