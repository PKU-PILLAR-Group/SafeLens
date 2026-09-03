"""Cached Gemma-2-9B-it + GemmaScope SAE steering runtime.

The Local Explorer's original intervention workflow is artifact-oriented and
keeps the 270M Gemma Scope integration for backwards compatibility.  This
module is the small, prompt-in/prompt-out runtime used by the dedicated SAE
steering demo.  It deliberately applies decoder directions directly at
``blocks.9.hook_resid_post`` so one request can combine several features.
"""

from __future__ import annotations

import os
import random
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from SafeLens.sae_profiles import (
    GEMMA_SCOPE_9B_IT_LAYER,
    GEMMA_SCOPE_9B_IT_MODEL,
    GEMMA_SCOPE_9B_IT_RELEASE,
    GEMMA_SCOPE_9B_IT_SAE_ID,
    GEMMA_SCOPE_9B_IT_WIDTH,
)
from SafeLens.utils.model_wrapper import HuggingFaceModelWrapper

GEMMA_SCOPE_9B_IT_SAE_URL = (
    "https://huggingface.co/google/gemma-scope-9b-it-res/resolve/main/"
    "layer_9/width_131k/average_l0_121/params.npz?download=true"
)
GEMMA_SCOPE_9B_IT_SAE_REPO = "google/gemma-scope-9b-it-res"
DEFAULT_GEMMA_9B_MODEL = GEMMA_SCOPE_9B_IT_MODEL
DEFAULT_GEMMA_9B_SAE_PATH = (
    ".cache/safelens/gemma-scope-9b-it-res/layer_9/width_131k/" "average_l0_121/params.npz"
)
_GEMMA_9B_SAE_RELATIVE_PATH = Path(
    "gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz"
)
HOOK_NAME = f"blocks.{GEMMA_SCOPE_9B_IT_LAYER}.hook_resid_post"

# These are the public feature presets exposed by Neuronpedia's Gemma-2-9B-it
# steering page. Feature IDs, layers, and strengths match its public preset API.
GEMMA_9B_STEERING_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "id": "cats",
        "label": "Cats",
        "description": "Mentions and references to cats and related topics",
        "featureIndex": 62_610,
        "strength": 192.0,
        "layer": 9,
        "features": [{"featureIndex": 62_610, "strength": 192.0, "layer": 9}],
    },
    {
        "id": "chinese",
        "label": "Chinese",
        "description": "Chinese characters and phrases, particularly technical terms",
        "featureIndex": 121_465,
        "strength": 74.0,
        "layer": 9,
        "features": [{"featureIndex": 121_465, "strength": 74.0, "layer": 9}],
    },
    {
        "id": "pirate",
        "label": "Pirate",
        "description": "References to pirates and pirate-related themes",
        "featureIndex": 29_917,
        "strength": 166.0,
        "layer": 9,
        "features": [
            {"featureIndex": 77_558, "strength": 66.0, "layer": 31},
            {"featureIndex": 29_917, "strength": 166.0, "layer": 9},
        ],
    },
    {
        "id": "shakespeare",
        "label": "Shakespeare",
        "description": "Famous quotes or phrases from Shakespeare's works",
        "featureIndex": 57_285,
        "strength": 226.0,
        "layer": 20,
        "features": [{"featureIndex": 57_285, "strength": 226.0, "layer": 20}],
    },
    {
        "id": "poetry",
        "label": "Poetry",
        "description": "Rhyming words or phrases at the end of lines in poetic or lyrical text",
        "featureIndex": 80_360,
        "strength": 202.0,
        "layer": 20,
        "features": [{"featureIndex": 80_360, "strength": 202.0, "layer": 20}],
    },
    {
        "id": "san-francisco",
        "label": "San Francisco",
        "description": "References to San Francisco and its landmarks",
        "featureIndex": 116_871,
        "strength": 200.0,
        "layer": 20,
        "features": [{"featureIndex": 116_871, "strength": 200.0, "layer": 20}],
    },
    {
        "id": "positivity",
        "label": "Positivity",
        "description": "Expressions of positive sentiment and appreciation",
        "featureIndex": 111_712,
        "strength": 160.0,
        "layer": 20,
        "features": [{"featureIndex": 111_712, "strength": 160.0, "layer": 20}],
    },
    {
        "id": "negativity",
        "label": "Negativity",
        "description": "Descriptions of negative or distressing situations",
        "featureIndex": 120_550,
        "strength": 112.0,
        "layer": 20,
        "features": [{"featureIndex": 120_550, "strength": 112.0, "layer": 20}],
    },
    {
        "id": "music",
        "label": "Music",
        "description": "Instances and descriptions of music and audio-related experiences",
        "featureIndex": 61_962,
        "strength": 170.5,
        "layer": 20,
        "features": [{"featureIndex": 61_962, "strength": 170.5, "layer": 20}],
    },
    {
        "id": "british-english",
        "label": "British English",
        "description": "British English*",
        "featureIndex": 90_098,
        "strength": 60.0,
        "layer": 20,
        "features": [{"featureIndex": 90_098, "strength": 60.0, "layer": 20}],
    },
)

GEMMA_9B_SAE_FOLDERS: dict[int, str] = {
    9: "layer_9/width_131k/average_l0_121",
    20: "layer_20/width_131k/average_l0_81",
    31: "layer_31/width_131k/average_l0_109",
}


@dataclass(frozen=True)
class SAEFeature:
    """One decoder direction and its requested coefficient."""

    feature_index: int
    strength: float
    layer: int = GEMMA_SCOPE_9B_IT_LAYER

    def to_api(self) -> dict[str, float | int]:
        return {
            "featureIndex": self.feature_index,
            "strength": self.strength,
            "layer": self.layer,
        }


@dataclass(frozen=True)
class GemmaSteeringConfig:
    """Runtime paths and tensor placement, all overridable through env vars."""

    model_path: str = DEFAULT_GEMMA_9B_MODEL
    sae_path: str = DEFAULT_GEMMA_9B_SAE_PATH
    device: str = "cpu"
    dtype: str = "float32"

    @classmethod
    def from_env(cls) -> GemmaSteeringConfig:
        from SafeLens.explorer_model import explorer_job_device

        configured_device = os.environ.get("SAFELENS_GEMMA_SAE_DEVICE")
        if configured_device is None:
            configured_device = os.environ.get("SAFELENS_EXPLORER_JOB_DEVICE")
        device = explorer_job_device(configured_device)
        default_dtype = "bfloat16" if device.lower().startswith("cuda") else "float32"
        configured_model = os.environ.get("SAFELENS_GEMMA_2_9B_IT_MODEL_PATH") or os.environ.get(
            "SAFELENS_GEMMA_2_9B_IT_MODEL"
        )
        if not configured_model:
            # Reuse the Explorer model resolver so the standalone endpoint and
            # the Chat model picker see the same local Gemma installation.
            from SafeLens.explorer_model import _configured_local_model_path

            local_model = _configured_local_model_path(GEMMA_SCOPE_9B_IT_MODEL)
            if local_model is not None:
                configured_model = str(local_model)
        return cls(
            model_path=(configured_model or DEFAULT_GEMMA_9B_MODEL),
            sae_path=(
                os.environ.get("SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH")
                or os.environ.get("SAFELENS_GEMMA_SAE_PATH")
                or _default_gemma_sae_path()
            ),
            device=device,
            dtype=(
                os.environ.get("SAFELENS_GEMMA_SAE_DTYPE")
                or os.environ.get("SAFELENS_EXPLORER_JOB_DTYPE")
                or default_dtype
            ).strip(),
        )

    def to_api(self) -> dict[str, str]:
        return {
            "modelPath": self.model_path,
            "saePath": self.sae_path,
            "device": self.device,
            "dtype": self.dtype,
        }


@dataclass
class GemmaScopeDecoder:
    """The decoder matrix needed by direct SAE steering."""

    W_dec: Any
    width: int
    d_in: int
    dtype: str
    device: str
    source_path: str

    @property
    def feature_count(self) -> int:
        return self.width

    def direction(self, feature_index: int) -> Any:
        validate_feature_index(feature_index, self.width)
        return self.W_dec[feature_index]


@dataclass
class GemmaScopeEncoder:
    """JumpReLU encoder parameters used to measure prompt feature activity."""

    W_enc: Any
    b_enc: Any
    threshold: Any
    width: int
    d_in: int
    dtype: str
    device: str
    source_path: str

    def encode(self, activation: Any) -> Any:
        """Encode residual activations with the published GemmaScope formula."""
        import torch

        x = activation.to(device=self.W_enc.device, dtype=torch.float32)
        pre = x @ self.W_enc.float() + self.b_enc.float()
        return pre * (pre > self.threshold.float())


@dataclass
class GemmaSteeringRuntime:
    wrapper: HuggingFaceModelWrapper
    sae: GemmaScopeDecoder
    config: GemmaSteeringConfig
    lock: threading.RLock
    encoder: GemmaScopeEncoder | None = None
    decoders: dict[int, GemmaScopeDecoder] | None = None

    def decoder_for_layer(self, layer: int) -> GemmaScopeDecoder:
        """Load a Neuronpedia layer dictionary on first use."""
        if self.decoders is None:
            self.decoders = {GEMMA_SCOPE_9B_IT_LAYER: self.sae}
        if layer in self.decoders:
            return self.decoders[layer]
        checkpoint = _gemma_scope_layer_path(layer)
        if not checkpoint.is_file():
            checkpoint = _download_gemma_scope_layer(layer)
        decoder = load_gemma_scope_decoder(
            checkpoint,
            device=self.config.device,
            dtype=self.config.dtype,
            expected_width=GEMMA_SCOPE_9B_IT_WIDTH,
        )
        if decoder.d_in != self.sae.d_in:
            raise ValueError(
                f"Gemma Scope L{layer} decoder width {decoder.d_in} does not match "
                f"model hidden size {self.sae.d_in}."
            )
        self.decoders[layer] = decoder
        return decoder


def validate_feature_index(feature_index: int, width: int = GEMMA_SCOPE_9B_IT_WIDTH) -> None:
    if isinstance(feature_index, bool) or not isinstance(feature_index, int):
        raise ValueError("featureIndex must be an integer")
    if feature_index < 0 or feature_index >= width:
        raise ValueError(f"featureIndex must be between 0 and {width - 1}")


def parse_dtype(dtype: str) -> Any:
    import torch

    normalized = dtype.strip().lower().replace("torch.", "")
    values = {
        "float32": torch.float32,
        "fp32": torch.float32,
        "float16": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
    }
    try:
        return values[normalized]
    except KeyError as exc:
        raise ValueError("dtype must be one of float32, float16, or bfloat16") from exc


def _default_gemma_sae_path() -> str:
    """Resolve an explicit cache or the standard SafeLens host cache."""
    configured_root = os.environ.get("SAFELENS_GEMMA_SAE_CACHE")
    candidates: list[Path] = []
    if configured_root:
        candidates.append(Path(configured_root).expanduser() / _GEMMA_9B_SAE_RELATIVE_PATH)
    candidates.extend(
        [
            Path("/ssd/yqy/cache/safelens") / _GEMMA_9B_SAE_RELATIVE_PATH,
            Path(DEFAULT_GEMMA_9B_SAE_PATH).expanduser(),
        ]
    )
    default_path = candidates[-1]
    return str(next((path for path in candidates if path.is_file()), default_path))


def _gemma_scope_layer_path(layer: int) -> Path:
    """Resolve one Neuronpedia Gemma Scope layer's public checkpoint."""
    try:
        folder = GEMMA_9B_SAE_FOLDERS[int(layer)]
    except (KeyError, ValueError) as exc:
        raise ValueError(
            f"Neuronpedia Gemma Scope presets require one of layers {sorted(GEMMA_9B_SAE_FOLDERS)}."
        ) from exc
    relative = Path(GEMMA_SCOPE_9B_IT_SAE_REPO.split("/", 1)[-1]) / f"{folder}/params.npz"
    candidates: list[Path] = []
    configured_root = os.environ.get("SAFELENS_GEMMA_SAE_CACHE")
    if configured_root:
        candidates.append(Path(configured_root).expanduser() / relative)
    candidates.extend(
        [
            Path("/ssd/yqy/cache/safelens") / relative,
            Path(".cache/safelens") / relative,
        ]
    )
    # The layer-9 path may be explicitly overridden by the existing setting.
    if layer == GEMMA_SCOPE_9B_IT_LAYER:
        configured = os.environ.get("SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH") or os.environ.get(
            "SAFELENS_GEMMA_SAE_PATH"
        )
        if configured:
            candidates.insert(0, Path(configured).expanduser())
    return next((path for path in candidates if path.is_file()), candidates[-1])


def _download_gemma_scope_layer(layer: int) -> Path:
    """Download a selected layer lazily from the public Gemma Scope repo."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is required to download the Neuronpedia Gemma Scope checkpoint."
        ) from exc
    folder = GEMMA_9B_SAE_FOLDERS[layer]
    cache_root = Path(os.environ.get("SAFELENS_GEMMA_SAE_CACHE", ".cache/safelens")).expanduser()
    local_dir = cache_root / GEMMA_SCOPE_9B_IT_SAE_REPO.split("/", 1)[-1]
    local_dir.mkdir(parents=True, exist_ok=True)
    # ``local_dir`` keeps the downloaded file at the same stable path that
    # ``_gemma_scope_layer_path`` resolves on subsequent requests.  The HF
    # cache remains available for deduplication, but is not used as the
    # runtime path (its snapshot hash changes between revisions).
    return Path(
        hf_hub_download(
            repo_id=GEMMA_SCOPE_9B_IT_SAE_REPO,
            filename=f"{folder}/params.npz",
            cache_dir=str(cache_root / "huggingface"),
            local_dir=str(local_dir),
        )
    )


def _npz_array(payload: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in payload:
            return payload[name]
    raise ValueError(f"SAE params.npz is missing one of: {', '.join(names)}")


def load_gemma_scope_decoder(
    path: str | os.PathLike[str],
    *,
    device: str = "cpu",
    dtype: str = "float32",
    expected_width: int | None = None,
) -> GemmaScopeDecoder:
    """Load and validate the canonical GemmaScope NPZ checkpoint.

    Only ``W_dec`` is materialized because direct steering does not need the
    encoder.  This keeps the resident footprint around 1.9 GB for float32,
    or roughly half that when ``bfloat16`` is selected.
    """

    import numpy as np
    import torch

    checkpoint = Path(path).expanduser()
    if not checkpoint.is_file():
        raise FileNotFoundError(
            f"GemmaScope SAE checkpoint not found at {checkpoint}. "
            f"Download it from {GEMMA_SCOPE_9B_IT_SAE_URL}"
        )
    try:
        with np.load(checkpoint, allow_pickle=False) as payload:
            raw_decoder = _npz_array(payload, "W_dec", "w_dec", "decoder")
            decoder = np.asarray(raw_decoder)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"Could not read GemmaScope SAE checkpoint {checkpoint}: {exc}") from exc
    if decoder.ndim != 2:
        raise ValueError(f"SAE decoder must be rank-2, got shape {decoder.shape!r}")
    # Published checkpoints use [features, d_model]. Accept the transposed
    # form as well so manually converted checkpoints remain usable.
    if (
        expected_width is not None
        and decoder.shape[0] != expected_width
        and decoder.shape[1] == expected_width
    ):
        decoder = decoder.T
    if expected_width is not None and decoder.shape[0] != expected_width:
        raise ValueError(f"Expected {expected_width} SAE features, got shape {decoder.shape!r}")
    target_dtype = parse_dtype(dtype)
    tensor = torch.from_numpy(np.ascontiguousarray(decoder)).to(device=device, dtype=target_dtype)
    return GemmaScopeDecoder(
        W_dec=tensor,
        width=int(tensor.shape[0]),
        d_in=int(tensor.shape[1]),
        dtype=str(target_dtype).replace("torch.", ""),
        device=str(tensor.device),
        source_path=str(checkpoint),
    )


def load_gemma_scope_encoder(
    path: str | os.PathLike[str],
    *,
    device: str = "cpu",
    expected_width: int | None = None,
    expected_d_in: int | None = None,
) -> GemmaScopeEncoder:
    """Load the encoder side of the canonical JumpReLU checkpoint.

    The encoder is intentionally loaded separately from the decoder. The
    steering path only needs ``W_dec``; prompt scans opt into the additional
    roughly 1.9 GiB ``W_enc`` allocation.
    """

    import numpy as np
    import torch

    checkpoint = Path(path).expanduser()
    if not checkpoint.is_file():
        raise FileNotFoundError(
            f"GemmaScope SAE checkpoint not found at {checkpoint}. "
            f"Download it from {GEMMA_SCOPE_9B_IT_SAE_URL}"
        )
    try:
        with np.load(checkpoint, allow_pickle=False) as payload:
            encoder = np.asarray(_npz_array(payload, "W_enc", "w_enc", "encoder"))
            b_enc = np.asarray(_npz_array(payload, "b_enc"))
            threshold = np.asarray(_npz_array(payload, "threshold"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(
            f"Could not read GemmaScope encoder checkpoint {checkpoint}: {exc}"
        ) from exc
    if encoder.ndim != 2:
        raise ValueError(f"SAE encoder must be rank-2, got shape {encoder.shape!r}")
    if (
        expected_width is not None
        and encoder.shape[1] != expected_width
        and encoder.shape[0] == expected_width
    ):
        encoder = encoder.T
    if expected_width is not None and encoder.shape[1] != expected_width:
        raise ValueError(f"Expected {expected_width} SAE features, got shape {encoder.shape!r}")
    if expected_d_in is not None and encoder.shape[0] != expected_d_in:
        raise ValueError(
            f"Expected encoder input width {expected_d_in}, got shape {encoder.shape!r}"
        )
    width = int(encoder.shape[1])
    if b_enc.shape != (width,) or threshold.shape != (width,):
        raise ValueError(
            "GemmaScope encoder bias/threshold shape does not match the feature width: "
            f"{b_enc.shape!r}, {threshold.shape!r}, width={width}"
        )
    target_device = torch.device(device)
    w_tensor = torch.from_numpy(np.ascontiguousarray(encoder)).to(
        device=target_device, dtype=torch.float32
    )
    b_tensor = torch.from_numpy(np.ascontiguousarray(b_enc)).to(
        device=target_device, dtype=torch.float32
    )
    threshold_tensor = torch.from_numpy(np.ascontiguousarray(threshold)).to(
        device=target_device, dtype=torch.float32
    )
    return GemmaScopeEncoder(
        W_enc=w_tensor,
        b_enc=b_tensor,
        threshold=threshold_tensor,
        width=width,
        d_in=int(encoder.shape[0]),
        dtype="float32",
        device=str(w_tensor.device),
        source_path=str(checkpoint),
    )


def _load_model(config: GemmaSteeringConfig) -> HuggingFaceModelWrapper:
    model_path = Path(config.model_path).expanduser()
    identifier = str(model_path) if model_path.is_dir() else config.model_path
    local_only = model_path.is_dir()
    wrapper = HuggingFaceModelWrapper.from_pretrained(
        identifier,
        dtype=config.dtype,
        device=config.device,
        load_kwargs={"local_files_only": True, "low_cpu_mem_usage": config.device != "cpu"}
        if local_only
        else {"low_cpu_mem_usage": config.device != "cpu"},
        tokenizer_kwargs={"local_files_only": True} if local_only else {},
    )
    return wrapper


@lru_cache(maxsize=2)
def _cached_runtime(
    model_path: str,
    sae_path: str,
    device: str,
    dtype: str,
) -> GemmaSteeringRuntime:
    config = GemmaSteeringConfig(model_path, sae_path, device, dtype)
    wrapper = _load_model(config)
    sae = load_gemma_scope_decoder(
        sae_path,
        device=device,
        dtype=dtype,
        expected_width=GEMMA_SCOPE_9B_IT_WIDTH,
    )
    if int(getattr(wrapper.cfg, "d_model", sae.d_in) or sae.d_in) != sae.d_in:
        raise ValueError(
            "GemmaScope decoder width does not match Gemma-2-9B-it hidden size: "
            f"{sae.d_in} != {getattr(wrapper.cfg, 'd_model', None)}"
        )
    print(
        "SafeLens GemmaScope SAE ready: "
        f"model={GEMMA_SCOPE_9B_IT_MODEL} features={sae.feature_count} "
        f"hook={HOOK_NAME} device={sae.device} dtype={sae.dtype}",
        flush=True,
    )
    return GemmaSteeringRuntime(
        wrapper=wrapper,
        sae=sae,
        config=config,
        lock=threading.RLock(),
        decoders={GEMMA_SCOPE_9B_IT_LAYER: sae},
    )


def get_gemma_steering_runtime(config: GemmaSteeringConfig | None = None) -> GemmaSteeringRuntime:
    """Get the process-resident model and SAE runtime."""

    selected = config or GemmaSteeringConfig.from_env()
    return _cached_runtime(
        selected.model_path,
        selected.sae_path,
        selected.device,
        selected.dtype,
    )


def _runtime_encoder(runtime: GemmaSteeringRuntime) -> GemmaScopeEncoder:
    """Load prompt-scan weights once, only when a scan is requested."""
    if runtime.encoder is None:
        runtime.encoder = load_gemma_scope_encoder(
            runtime.config.sae_path,
            device=runtime.config.device,
            expected_width=runtime.sae.width,
            expected_d_in=runtime.sae.d_in,
        )
    return runtime.encoder


def clear_gemma_steering_runtime_cache() -> None:
    """Release cached references (useful for tests and controlled reloads)."""

    _cached_runtime.cache_clear()


def _make_decoder_hook(
    sae: GemmaScopeDecoder,
    features: Sequence[SAEFeature],
    *,
    steer_position: str = "all",
    prompt_position: int | None = None,
) -> Any:
    import torch

    # Build one direction once per request rather than summing for every token.
    direction = torch.zeros(sae.d_in, device=sae.W_dec.device, dtype=sae.W_dec.dtype)
    for feature in features:
        direction = direction + float(feature.strength) * sae.direction(feature.feature_index)

    invocation_count = 0

    def hook(activation: Any = None, **kwargs: Any) -> Any:
        nonlocal invocation_count
        value = kwargs.get("activation", activation)
        if value is None or not hasattr(value, "clone") or getattr(value, "ndim", 0) < 2:
            return value
        is_prompt_pass = invocation_count == 0
        invocation_count += 1
        if steer_position == "prompt" and not is_prompt_pass:
            return value
        if steer_position == "generated" and is_prompt_pass:
            return value
        if steer_position == "prompt_position" and not is_prompt_pass:
            return value
        delta = direction.to(device=value.device, dtype=value.dtype)
        result = value.clone()
        if value.ndim >= 3:
            sequence_length = int(value.shape[-2])
            if steer_position == "prompt_position":
                if prompt_position is None or not 0 <= prompt_position < sequence_length:
                    return result
                result[:, prompt_position, :] += delta
            else:
                result += delta.view(1, 1, -1)
        else:
            if steer_position == "prompt":
                return result
            if steer_position == "prompt_position":
                return result
            result += delta.view(1, -1)
        return result

    return hook


def _render_generation_prompt(tokenizer: Any, prompt: str) -> str:
    """Render a plain user prompt with Gemma's instruction template once."""
    stripped = prompt.lstrip()
    if stripped.startswith(
        (
            "<bos><start_of_turn>",
            "<start_of_turn>",
            "<|im_start|>",
            "<|begin_of_text|>",
        )
    ):
        return stripped
    apply_chat_template = getattr(tokenizer, "apply_chat_template", None)
    if not callable(apply_chat_template):
        return prompt
    try:
        rendered = apply_chat_template(
            [{"role": "user", "content": prompt.strip()}],
            tokenize=False,
            add_generation_prompt=True,
        )
    except (TypeError, ValueError):
        return prompt
    return rendered if isinstance(rendered, str) and rendered else prompt


def _generate(
    wrapper: HuggingFaceModelWrapper,
    prompt: str,
    *,
    max_new_tokens: int,
    temperature: float,
    seed: int,
    hook: Any | None = None,
    hooks: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    import torch

    random.seed(seed)
    torch.manual_seed(seed)
    rendered_prompt = _render_generation_prompt(wrapper.tokenizer, prompt)
    prompt_tokens = wrapper.to_tokens(rendered_prompt, prepend_bos=False)
    prompt_count = int(prompt_tokens.shape[-1])
    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "pad_token_id": getattr(wrapper.tokenizer, "eos_token_id", None),
        "prepend_bos": False,
        "return_type": "model_output",
        "return_dict_in_generate": True,
        "use_cache": True,
    }
    if temperature > 0:
        generation_kwargs["temperature"] = temperature
    active_hooks = dict(hooks or {})
    if hook is not None:
        active_hooks.setdefault(HOOK_NAME, hook)
    handles = [wrapper.add_hook(name, callback) for name, callback in active_hooks.items()]
    try:
        generated_output = wrapper.generate(rendered_prompt, **generation_kwargs)
    finally:
        for handle in reversed(handles):
            handle.remove()
    sequences = getattr(generated_output, "sequences", generated_output)
    generated_ids = sequences.detach().cpu().tolist() if hasattr(sequences, "detach") else sequences
    if generated_ids and isinstance(generated_ids[0], list):
        generated_ids = generated_ids[0]
    continuation_ids = [int(value) for value in generated_ids[prompt_count:]]
    tokenizer = wrapper.tokenizer
    # Gemma's instruction template has a turn terminator distinct from the
    # tokenizer EOS id. Keep control markers out of the user-facing answer and
    # token strip even when Transformers returns both markers in the sequence.
    stop_ids = {int(eos) for eos in (getattr(tokenizer, "eos_token_id", None),) if eos is not None}
    end_turn_id = getattr(tokenizer, "convert_tokens_to_ids", lambda _value: None)("<end_of_turn>")
    if isinstance(end_turn_id, int) and end_turn_id >= 0:
        stop_ids.add(end_turn_id)
    for stop_position, token_id in enumerate(continuation_ids):
        if token_id in stop_ids:
            continuation_ids = continuation_ids[:stop_position]
            break
    continuation_text = str(
        tokenizer.decode(
            continuation_ids,
            # Special turn/eos markers are control tokens, not part of the
            # assistant answer shown in the comparison columns.
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
    )
    return {
        "text": continuation_text,
        "tokenIds": continuation_ids,
        "tokens": [
            {
                "index": index,
                "tokenId": token_id,
                "text": str(tokenizer.decode([token_id], clean_up_tokenization_spaces=False)),
            }
            for index, token_id in enumerate(continuation_ids)
        ],
    }


def steer_gemma_prompt(
    prompt: str,
    features: Sequence[SAEFeature | Mapping[str, Any]],
    *,
    max_new_tokens: int = 64,
    temperature: float = 0.0,
    seed: int = 0,
    steer_position: str = "all",
    prompt_position: int | None = None,
    config: GemmaSteeringConfig | None = None,
) -> dict[str, Any]:
    """Generate default and multi-feature steered continuations."""

    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not 1 <= max_new_tokens <= 512:
        raise ValueError("max_new_tokens must be between 1 and 512")
    if not 0 <= temperature <= 2:
        raise ValueError("temperature must be between 0 and 2")
    if steer_position not in {"all", "prompt", "generated", "prompt_position"}:
        raise ValueError("steer_position must be one of all, prompt, generated, prompt_position")
    if prompt_position is not None and (
        prompt_position < 0 or not isinstance(prompt_position, int)
    ):
        raise ValueError("prompt_position must be a non-negative integer")
    normalized: list[SAEFeature] = []
    for item in features:
        feature = (
            item
            if isinstance(item, SAEFeature)
            else SAEFeature(
                feature_index=int(item["featureIndex"]),
                strength=float(item["strength"]),
                layer=int(item.get("layer", GEMMA_SCOPE_9B_IT_LAYER)),
            )
        )
        if feature.layer < 0 or feature.layer >= 42:
            raise ValueError("feature layer must be between 0 and 41")
        validate_feature_index(feature.feature_index)
        if not -9_000 <= feature.strength <= 9_000:
            raise ValueError("feature strength must be between -9000 and 9000")
        normalized.append(feature)
    runtime = get_gemma_steering_runtime(config)
    with runtime.lock:
        if steer_position == "prompt_position":
            rendered_prompt = _render_generation_prompt(runtime.wrapper.tokenizer, prompt)
            token_count = int(
                runtime.wrapper.to_tokens(rendered_prompt, prepend_bos=False).shape[-1]
            )
            if prompt_position is None or prompt_position >= token_count:
                raise ValueError(
                    "promptPosition must be within the rendered prompt token range "
                    f"[0, {token_count - 1}]"
                )
        default = _generate(
            runtime.wrapper,
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            seed=seed,
        )
        hooks: dict[str, Any] = {}
        for layer in sorted({feature.layer for feature in normalized}):
            layer_features = [feature for feature in normalized if feature.layer == layer]
            decoder = runtime.decoder_for_layer(layer)
            for feature in layer_features:
                validate_feature_index(feature.feature_index, decoder.width)
            hooks[f"blocks.{layer}.hook_resid_post"] = _make_decoder_hook(
                decoder,
                layer_features,
                steer_position=steer_position,
                prompt_position=prompt_position,
            )
        steered = _generate(
            runtime.wrapper,
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            seed=seed,
            hooks=hooks,
        )
    layers = sorted({feature.layer for feature in normalized})
    hook_names = [f"blocks.{layer}.hook_resid_post" for layer in layers]
    return {
        "modelName": GEMMA_SCOPE_9B_IT_MODEL,
        "modelPath": runtime.config.model_path,
        "saeRelease": GEMMA_SCOPE_9B_IT_RELEASE,
        "saeId": GEMMA_SCOPE_9B_IT_SAE_ID,
        "layer": GEMMA_SCOPE_9B_IT_LAYER,
        "hookName": ",".join(hook_names) or HOOK_NAME,
        "layers": layers,
        "hooks": hook_names,
        "featureCount": runtime.sae.feature_count,
        "hiddenSize": runtime.sae.d_in,
        "features": [feature.to_api() for feature in normalized],
        "prompt": prompt,
        "default": default,
        "steered": steered,
        "generationChanged": default["tokenIds"] != steered["tokenIds"],
        "seed": seed,
        "maxNewTokens": max_new_tokens,
        "temperature": temperature,
        "steerPosition": steer_position,
        "promptPosition": prompt_position,
    }


def scan_gemma_prompt(
    prompt: str,
    *,
    limit: int = 12,
    config: GemmaSteeringConfig | None = None,
) -> dict[str, Any]:
    """Return the strongest real JumpReLU activations for a prompt.

    This follows Neuronpedia's activation semantics and reports one row per
    feature with its peak token, mean activation, and active-token coverage.
    """

    import torch

    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not 1 <= limit <= 32:
        raise ValueError("limit must be between 1 and 32")
    runtime = get_gemma_steering_runtime(config)
    with runtime.lock:
        encoder = _runtime_encoder(runtime)
        # Neuronpedia's activation endpoints scan the raw prompt. Do not wrap
        # it in Gemma's chat template here: template control tokens can
        # dominate the ranking and are not evidence about the user's text.
        prompt_tokens = runtime.wrapper.to_tokens(prompt.strip(), prepend_bos=False)
        _output, cache_value = runtime.wrapper.run_with_cache(
            {"input_ids": prompt_tokens}, layers=[HOOK_NAME]
        )
        try:
            activation = cache_value[HOOK_NAME]
        except (KeyError, TypeError) as exc:
            raise RuntimeError(f"SAE hook activation {HOOK_NAME!r} was not captured") from exc
        if getattr(activation, "ndim", 0) < 3:
            raise RuntimeError(
                "Expected batched residual activations, got "
                f"{getattr(activation, 'shape', None)!r}"
            )
        activation = activation[0]
        with torch.no_grad():
            encoded = encoder.encode(activation)
            max_values, peak_offsets = encoded.max(dim=0)
            positive_indices = (max_values > 0).nonzero(as_tuple=False).flatten()
            ranked = positive_indices[
                max_values[positive_indices].argsort(descending=True)[:limit]
            ].tolist()
            token_ids = [int(value) for value in prompt_tokens[0].detach().cpu().tolist()]
            token_texts = [str(value) for value in runtime.wrapper.to_str_tokens(prompt_tokens)]
            features: list[dict[str, Any]] = []
            for raw_index in ranked:
                feature_index = int(raw_index)
                values = encoded[:, feature_index]
                peak_index = int(peak_offsets[feature_index].item())
                features.append(
                    {
                        "featureIndex": feature_index,
                        "maxActivation": float(max_values[feature_index].item()),
                        "meanActivation": float(values.mean().item()),
                        "activeTokenCount": int((values > 0).sum().item()),
                        "peakTokenIndex": peak_index,
                        "peakTokenText": (
                            token_texts[peak_index] if peak_index < len(token_texts) else ""
                        ),
                    }
                )
    return {
        "modelName": GEMMA_SCOPE_9B_IT_MODEL,
        "saeRelease": GEMMA_SCOPE_9B_IT_RELEASE,
        "saeId": GEMMA_SCOPE_9B_IT_SAE_ID,
        "layer": GEMMA_SCOPE_9B_IT_LAYER,
        "hookName": HOOK_NAME,
        "featureCount": runtime.sae.feature_count,
        "prompt": prompt,
        "tokens": [
            {"index": index, "tokenId": token_id, "text": token_texts[index]}
            for index, token_id in enumerate(token_ids)
        ],
        "features": features,
    }


def runtime_status(config: GemmaSteeringConfig | None = None) -> dict[str, Any]:
    selected = config or GemmaSteeringConfig.from_env()
    sae_path = Path(selected.sae_path).expanduser()
    supported_layers = sorted(GEMMA_9B_SAE_FOLDERS)
    supported_hooks = [f"blocks.{layer}.hook_resid_post" for layer in supported_layers]
    return {
        "modelName": GEMMA_SCOPE_9B_IT_MODEL,
        "modelPath": selected.model_path,
        "saePath": selected.sae_path,
        "saeUrl": GEMMA_SCOPE_9B_IT_SAE_URL,
        "release": GEMMA_SCOPE_9B_IT_RELEASE,
        "saeId": GEMMA_SCOPE_9B_IT_SAE_ID,
        "layer": GEMMA_SCOPE_9B_IT_LAYER,
        "hookName": HOOK_NAME,
        "layers": supported_layers,
        "hooks": supported_hooks,
        "featureCount": GEMMA_SCOPE_9B_IT_WIDTH,
        "device": selected.device,
        "dtype": selected.dtype,
        "checkpointPresent": sae_path.is_file(),
        "presets": [dict(item) for item in GEMMA_9B_STEERING_PRESETS],
    }


__all__ = [
    "DEFAULT_GEMMA_9B_MODEL",
    "DEFAULT_GEMMA_9B_SAE_PATH",
    "GEMMA_9B_STEERING_PRESETS",
    "GEMMA_SCOPE_9B_IT_SAE_URL",
    "GemmaScopeDecoder",
    "GemmaScopeEncoder",
    "GemmaSteeringConfig",
    "SAEFeature",
    "clear_gemma_steering_runtime_cache",
    "get_gemma_steering_runtime",
    "load_gemma_scope_decoder",
    "load_gemma_scope_encoder",
    "runtime_status",
    "steer_gemma_prompt",
    "scan_gemma_prompt",
    "validate_feature_index",
]
