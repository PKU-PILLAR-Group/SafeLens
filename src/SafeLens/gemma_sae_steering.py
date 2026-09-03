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
DEFAULT_GEMMA_9B_MODEL = GEMMA_SCOPE_9B_IT_MODEL
DEFAULT_GEMMA_9B_SAE_PATH = (
    ".cache/safelens/gemma-scope-9b-it-res/layer_9/width_131k/"
    "average_l0_121/params.npz"
)
_GEMMA_9B_SAE_RELATIVE_PATH = Path(
    "gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz"
)
HOOK_NAME = f"blocks.{GEMMA_SCOPE_9B_IT_LAYER}.hook_resid_post"

# These are the three layer-9 examples exposed by Neuronpedia's Gemma-2-9B-it
# steering page.  Strengths intentionally match that page's default settings.
GEMMA_9B_STEERING_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "id": "cats",
        "label": "Cats",
        "description": "Mentions and references to cats and related topics",
        "featureIndex": 62_610,
        "strength": 192.0,
    },
    {
        "id": "chinese",
        "label": "Chinese",
        "description": "Chinese characters and phrases, particularly technical terms",
        "featureIndex": 121_465,
        "strength": 74.0,
    },
    {
        "id": "pirate",
        "label": "Pirate",
        "description": "References to pirates and pirate-related themes",
        "featureIndex": 29_917,
        "strength": 166.0,
    },
)


@dataclass(frozen=True)
class SAEFeature:
    """One decoder direction and its requested coefficient."""

    feature_index: int
    strength: float

    def to_api(self) -> dict[str, float | int]:
        return {"featureIndex": self.feature_index, "strength": self.strength}


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
        configured_model = (
            os.environ.get("SAFELENS_GEMMA_2_9B_IT_MODEL_PATH")
            or os.environ.get("SAFELENS_GEMMA_2_9B_IT_MODEL")
        )
        if not configured_model:
            # Reuse the Explorer model resolver so the standalone endpoint and
            # the Chat model picker see the same local Gemma installation.
            from SafeLens.explorer_model import _configured_local_model_path

            local_model = _configured_local_model_path(GEMMA_SCOPE_9B_IT_MODEL)
            if local_model is not None:
                configured_model = str(local_model)
        return cls(
            model_path=(
                configured_model
                or DEFAULT_GEMMA_9B_MODEL
            ),
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
class GemmaSteeringRuntime:
    wrapper: HuggingFaceModelWrapper
    sae: GemmaScopeDecoder
    config: GemmaSteeringConfig
    lock: threading.RLock


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
        raise ValueError(
            "dtype must be one of float32, float16, or bfloat16"
        ) from exc


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
        raise ValueError(
            f"Expected {expected_width} SAE features, got shape {decoder.shape!r}"
        )
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
    return GemmaSteeringRuntime(wrapper=wrapper, sae=sae, config=config, lock=threading.RLock())


def get_gemma_steering_runtime(config: GemmaSteeringConfig | None = None) -> GemmaSteeringRuntime:
    """Get the process-resident model and SAE runtime."""

    selected = config or GemmaSteeringConfig.from_env()
    return _cached_runtime(
        selected.model_path,
        selected.sae_path,
        selected.device,
        selected.dtype,
    )


def clear_gemma_steering_runtime_cache() -> None:
    """Release cached references (useful for tests and controlled reloads)."""

    _cached_runtime.cache_clear()


def _make_decoder_hook(
    sae: GemmaScopeDecoder,
    features: Sequence[SAEFeature],
) -> Any:
    import torch

    # Build one direction once per request rather than summing for every token.
    direction = torch.zeros(sae.d_in, device=sae.W_dec.device, dtype=sae.W_dec.dtype)
    for feature in features:
        direction = direction + float(feature.strength) * sae.direction(feature.feature_index)

    def hook(activation: Any = None, **kwargs: Any) -> Any:
        value = kwargs.get("activation", activation)
        if value is None or not hasattr(value, "clone") or getattr(value, "ndim", 0) < 2:
            return value
        delta = direction.to(device=value.device, dtype=value.dtype)
        result = value.clone()
        if value.ndim >= 3:
            result += delta.view(1, 1, -1)
        else:
            result += delta.view(1, -1)
        return result

    return hook


def _render_generation_prompt(tokenizer: Any, prompt: str) -> str:
    """Render a plain user prompt with Gemma's instruction template once."""
    stripped = prompt.lstrip()
    if stripped.startswith((
        "<bos><start_of_turn>",
        "<start_of_turn>",
        "<|im_start|>",
        "<|begin_of_text|>",
    )):
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
    handle = wrapper.add_hook(HOOK_NAME, hook) if hook is not None else None
    try:
        generated_output = wrapper.generate(rendered_prompt, **generation_kwargs)
    finally:
        if handle is not None:
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
    config: GemmaSteeringConfig | None = None,
) -> dict[str, Any]:
    """Generate default and multi-feature steered continuations."""

    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not 1 <= max_new_tokens <= 512:
        raise ValueError("max_new_tokens must be between 1 and 512")
    if not 0 <= temperature <= 2:
        raise ValueError("temperature must be between 0 and 2")
    normalized: list[SAEFeature] = []
    for item in features:
        feature = item if isinstance(item, SAEFeature) else SAEFeature(
            feature_index=int(item["featureIndex"]), strength=float(item["strength"])
        )
        validate_feature_index(feature.feature_index)
        if not -9_000 <= feature.strength <= 9_000:
            raise ValueError("feature strength must be between -9000 and 9000")
        normalized.append(feature)
    runtime = get_gemma_steering_runtime(config)
    with runtime.lock:
        default = _generate(
            runtime.wrapper,
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            seed=seed,
        )
        steered = _generate(
            runtime.wrapper,
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            seed=seed,
            hook=_make_decoder_hook(runtime.sae, normalized) if normalized else None,
        )
    return {
        "modelName": GEMMA_SCOPE_9B_IT_MODEL,
        "modelPath": runtime.config.model_path,
        "saeRelease": GEMMA_SCOPE_9B_IT_RELEASE,
        "saeId": GEMMA_SCOPE_9B_IT_SAE_ID,
        "layer": GEMMA_SCOPE_9B_IT_LAYER,
        "hookName": HOOK_NAME,
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
    }


def runtime_status(config: GemmaSteeringConfig | None = None) -> dict[str, Any]:
    selected = config or GemmaSteeringConfig.from_env()
    sae_path = Path(selected.sae_path).expanduser()
    return {
        "modelName": GEMMA_SCOPE_9B_IT_MODEL,
        "modelPath": selected.model_path,
        "saePath": selected.sae_path,
        "saeUrl": GEMMA_SCOPE_9B_IT_SAE_URL,
        "release": GEMMA_SCOPE_9B_IT_RELEASE,
        "saeId": GEMMA_SCOPE_9B_IT_SAE_ID,
        "layer": GEMMA_SCOPE_9B_IT_LAYER,
        "hookName": HOOK_NAME,
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
    "GemmaSteeringConfig",
    "SAEFeature",
    "clear_gemma_steering_runtime_cache",
    "get_gemma_steering_runtime",
    "load_gemma_scope_decoder",
    "runtime_status",
    "steer_gemma_prompt",
    "validate_feature_index",
]
