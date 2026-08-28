"""Natural Language Autoencoder loading and inference helpers.

The public NLA checkpoints are ordinary HuggingFace model directories with an
extra ``nla_meta.yaml`` sidecar. This module keeps the sidecar contract explicit
and exposes a small runtime that can verbalize activation vectors with AV
weights and optionally score the text with AR weights.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

INJECT_PLACEHOLDER = "<INJECT>"
EXPLANATION_RE = re.compile(r"<explanation>\s*(.*?)\s*</explanation>", re.DOTALL)
EXPLANATION_END_TAG = "</explanation>"
SCALE_SQRT_D = "sqrt_d_model"
_FINAL_LAYER_NORM_ATTRS = ("norm", "final_layernorm", "ln_f")


@dataclass(frozen=True, slots=True)
class NLAProfile:
    """Metadata for a supported public NLA checkpoint pair."""

    name: str
    base_model: str
    layer: int
    component: str
    d_model: int
    av_repo: str
    ar_repo: str | None
    av_revision: str | None = None
    ar_revision: str | None = None
    gated: bool = False
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NLAConfig:
    """Parsed ``nla_meta.yaml`` sidecar fields used at inference time."""

    d_model: int
    role: str | None = None
    injection_char: str | None = None
    injection_token_id: int | None = None
    injection_left_neighbor_id: int | None = None
    injection_right_neighbor_id: int | None = None
    actor_prompt_template: str | None = None
    critic_prompt_template: str | None = None
    critic_suffix_ids: tuple[int, ...] | None = None
    injection_scale: float | None = None
    mse_scale: float | None = None

    @property
    def sqrt_d(self) -> float:
        return math.sqrt(self.d_model)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NLAActorOutput:
    """Actor verbalization output before optional AR scoring."""

    explanation: str
    raw_text: str
    prompt_token_count: int
    activation_norm: float
    generated_token_count: int
    generation_complete: bool
    finish_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NLAResult:
    """One NLA explanation row suitable for downstream visualization."""

    explanation: str
    raw_text: str = ""
    sample_id: str = "0"
    token_index: int | None = None
    token: str | None = None
    source: str = "activation"
    model_name: str = ""
    layer: int | None = None
    component: str = "resid_post"
    profile: str | None = None
    activation_norm: float | None = None
    mse_nrm: float | None = None
    cosine: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metadata"] = dict(self.metadata)
        return payload


NLA_SUPPORTED_PROFILES: tuple[NLAProfile, ...] = (
    NLAProfile(
        name="qwen2.5-7b-l20",
        base_model="Qwen/Qwen2.5-7B-Instruct",
        layer=20,
        component="resid_post",
        d_model=3584,
        av_repo="kitft/nla-qwen2.5-7b-L20-av",
        ar_repo="kitft/nla-qwen2.5-7b-L20-ar",
        av_revision="b88469162777ae6553bc14208eb0cb579336f8f4",
        ar_revision="e2c9e57eac213d37a31612087f645ab6332c1bb6",
        description="Public Qwen2.5-7B-Instruct NLA pair trained on layer 20 residuals.",
    ),
    NLAProfile(
        name="gemma3-12b-l32",
        base_model="google/gemma-3-12b-it",
        layer=32,
        component="resid_post",
        d_model=3840,
        av_repo="kitft/nla-gemma3-12b-L32-av",
        ar_repo="kitft/nla-gemma3-12b-L32-ar",
        gated=True,
        description="Public Gemma-3-12B-IT NLA pair trained on layer 32 residuals.",
    ),
)

_NLA_PROFILE_ALIASES = {profile.name: profile for profile in NLA_SUPPORTED_PROFILES} | {
    "qwen2.5-7b": NLA_SUPPORTED_PROFILES[0],
    "qwen": NLA_SUPPORTED_PROFILES[0],
    "gemma3-12b": NLA_SUPPORTED_PROFILES[1],
    "gemma": NLA_SUPPORTED_PROFILES[1],
}


def list_nla_profiles() -> list[dict[str, Any]]:
    """Return the public NLA profiles SafeLens knows how to load."""

    return [profile.to_dict() for profile in NLA_SUPPORTED_PROFILES]


def get_nla_profile(name: str) -> NLAProfile:
    """Resolve a supported NLA profile by name or short alias."""

    key = name.strip().lower()
    try:
        return _NLA_PROFILE_ALIASES[key]
    except KeyError as exc:
        supported = ", ".join(profile.name for profile in NLA_SUPPORTED_PROFILES)
        raise ValueError(f"unknown NLA profile {name!r}; supported profiles: {supported}") from exc


def load_nla_config(
    sidecar_source: str | Path,
    tokenizer: Any | None = None,
    *,
    validate_tokenizer: bool = True,
    injection_scale_override: float | None = None,
) -> NLAConfig:
    """Load and optionally validate an NLA sidecar.

    ``sidecar_source`` may be either a checkpoint directory containing
    ``nla_meta.yaml`` or the sidecar path itself.
    """

    meta_path = _sidecar_path_for(sidecar_source)
    if not meta_path.exists():
        raise FileNotFoundError(
            f"no nla_meta.yaml found for {sidecar_source!r}; NLA checkpoints ship "
            "this sidecar next to config.json and model weights."
        )
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    if not isinstance(meta, Mapping):
        raise ValueError(f"{meta_path} is not a valid NLA sidecar mapping.")

    kind = meta.get("kind")
    if kind not in {"nla_model", "nla_dataset"}:
        raise ValueError(f"unknown NLA sidecar kind {kind!r}.")

    extraction = meta.get("extraction", {})
    if not isinstance(extraction, Mapping):
        raise ValueError("nla_meta.yaml field 'extraction' must be a mapping.")
    d_model = int(meta["d_model"] if kind == "nla_model" else extraction["d_model"])
    tokens = meta.get("tokens", {})
    templates = meta.get("prompt_templates", {})
    if not isinstance(tokens, Mapping) or not isinstance(templates, Mapping):
        raise ValueError("nla_meta.yaml fields 'tokens' and 'prompt_templates' must be mappings.")

    injection_scale = _resolve_target_scale(extraction.get("injection_scale"), d_model)
    if injection_scale_override is not None:
        injection_scale = float(injection_scale_override)
    mse_scale = _resolve_target_scale(extraction.get("mse_scale", SCALE_SQRT_D), d_model)
    critic_suffix = tokens.get("critic_suffix_ids")

    cfg = NLAConfig(
        d_model=d_model,
        role=_optional_str(meta.get("role")),
        injection_char=_optional_str(tokens.get("injection_char")),
        injection_token_id=_optional_int(tokens.get("injection_token_id")),
        injection_left_neighbor_id=_optional_int(tokens.get("injection_left_neighbor_id")),
        injection_right_neighbor_id=_optional_int(tokens.get("injection_right_neighbor_id")),
        actor_prompt_template=_optional_str(templates.get("av") or templates.get("actor")),
        critic_prompt_template=_optional_str(templates.get("ar") or templates.get("critic")),
        critic_suffix_ids=tuple(map(int, critic_suffix)) if critic_suffix else None,
        injection_scale=injection_scale,
        mse_scale=mse_scale,
    )

    if validate_tokenizer and tokenizer is not None:
        validate_nla_tokenizer(cfg, tokenizer)
    return cfg


def validate_nla_tokenizer(config: NLAConfig, tokenizer: Any) -> None:
    """Assert that tokenizer and sidecar agree on injection token placement."""

    required = (
        config.injection_char,
        config.injection_token_id,
        config.injection_left_neighbor_id,
        config.injection_right_neighbor_id,
        config.actor_prompt_template,
    )
    if any(value is None for value in required):
        raise ValueError("actor sidecar is missing injection token or prompt metadata.")

    live_ids = tokenizer.encode(config.injection_char, add_special_tokens=False)
    if live_ids != [config.injection_token_id]:
        raise ValueError(
            f"tokenizer drift for NLA injection char {config.injection_char!r}: "
            f"got {live_ids}, sidecar expects [{config.injection_token_id}]."
        )
    unk_token_id = getattr(tokenizer, "unk_token_id", None)
    if unk_token_id is not None and live_ids[0] == unk_token_id:
        raise ValueError(f"NLA injection char {config.injection_char!r} maps to UNK.")

    input_ids = build_nla_prompt_input_ids(tokenizer, config)
    positions = find_nla_injection_positions(input_ids, config)
    if len(positions) != 1:
        raise ValueError(
            f"canonical NLA prompt has {len(positions)} valid injection sites; expected 1."
        )


def build_nla_prompt_input_ids(
    tokenizer: Any,
    config: NLAConfig,
    *,
    prompt: str | None = None,
) -> list[int]:
    """Tokenize the actor prompt, preserving the sidecar chat-template contract."""

    if config.injection_char is None:
        raise ValueError("NLA config has no injection_char.")
    if prompt is None:
        if config.actor_prompt_template is None:
            raise ValueError("NLA config has no actor prompt template.")
        content = config.actor_prompt_template.format(injection_char=config.injection_char)
    else:
        if INJECT_PLACEHOLDER not in prompt:
            raise ValueError(f"custom NLA prompt must contain {INJECT_PLACEHOLDER!r}.")
        content = prompt.replace(INJECT_PLACEHOLDER, config.injection_char)

    apply_chat_template = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply_chat_template):
        ids = apply_chat_template(
            [{"role": "user", "content": content}],
            tokenize=True,
            add_generation_prompt=True,
        )
        input_ids_attr = getattr(ids, "input_ids", None)
        if input_ids_attr is not None:
            ids = input_ids_attr
        elif isinstance(ids, Mapping):
            ids = ids.get("input_ids", ids)
        detach = getattr(ids, "detach", None)
        if callable(detach):
            ids = cast(Any, detach()).cpu().tolist()
        if isinstance(ids, Sequence) and not isinstance(ids, str | bytes):
            if ids and isinstance(ids[0], Sequence) and not isinstance(ids[0], int):
                if len(ids) != 1:
                    raise ValueError(
                        "chat template tokenization returned a batched sequence; expected 1 row."
                    )
                ids = ids[0]
            return [int(token_id) for token_id in ids]
        raise TypeError(
            f"tokenizer.apply_chat_template returned unsupported type {type(ids).__name__}."
        )
    encoded = tokenizer(content, add_special_tokens=True)
    input_ids_attr = getattr(encoded, "input_ids", None)
    input_ids = encoded["input_ids"] if isinstance(encoded, Mapping) else input_ids_attr
    detach = getattr(input_ids, "detach", None)
    if callable(detach):
        input_ids = cast(Any, detach()).cpu().tolist()
    if isinstance(input_ids, Sequence) and not isinstance(input_ids, str | bytes):
        if input_ids and isinstance(input_ids[0], Sequence) and not isinstance(input_ids[0], int):
            if len(input_ids) != 1:
                raise ValueError("tokenizer returned a batched input_ids sequence; expected 1 row.")
            input_ids = input_ids[0]
        return [int(token_id) for token_id in input_ids]
    raise TypeError(f"tokenizer returned unsupported input_ids type {type(input_ids).__name__}.")


def find_nla_injection_positions(
    input_ids: Sequence[int] | Sequence[Sequence[int]] | Any,
    config: NLAConfig,
) -> list[tuple[int, int]]:
    """Return ``(batch_index, token_index)`` pairs matching the sidecar marker."""

    if (
        config.injection_token_id is None
        or config.injection_left_neighbor_id is None
        or config.injection_right_neighbor_id is None
    ):
        raise ValueError("NLA config is missing injection token ids.")
    rows = _as_token_rows(input_ids)
    positions: list[tuple[int, int]] = []
    for batch_idx, row in enumerate(rows):
        for pos, token_id in enumerate(row):
            if token_id != config.injection_token_id or pos == 0 or pos == len(row) - 1:
                continue
            if (
                row[pos - 1] == config.injection_left_neighbor_id
                and row[pos + 1] == config.injection_right_neighbor_id
            ):
                positions.append((batch_idx, pos))
    return positions


def normalize_nla_activation(vector: Any, target_scale: float | None) -> Any:
    """Scale activation vectors to the target L2 norm used by NLA."""

    torch = _require_torch()
    tensor = vector if torch.is_tensor(vector) else torch.as_tensor(vector, dtype=torch.float32)
    if target_scale is None:
        return tensor
    norm = tensor.float().norm(dim=-1, keepdim=True).clamp_min(1e-12)
    return tensor / (norm / float(target_scale)).to(tensor.dtype)


def inject_nla_vectors(input_ids: Any, embeddings: Any, vectors: Any, config: NLAConfig) -> Any:
    """Clone ``embeddings`` and overwrite valid NLA marker positions with vectors."""

    torch = _require_torch()
    ids = input_ids if torch.is_tensor(input_ids) else torch.as_tensor(input_ids, dtype=torch.long)
    if ids.ndim == 1:
        ids = ids.unsqueeze(0)
    if ids.ndim != 2:
        raise ValueError("input_ids must have shape [seq] or [batch, seq].")
    if not torch.is_tensor(embeddings):
        raise TypeError("embeddings must be a torch.Tensor.")
    if embeddings.shape[:2] != ids.shape:
        raise ValueError("embeddings must have shape [batch, seq, d_model].")
    vecs = vectors if torch.is_tensor(vectors) else torch.as_tensor(vectors, dtype=embeddings.dtype)
    if vecs.ndim == 1:
        vecs = vecs.unsqueeze(0)
    if vecs.ndim != 2 or vecs.shape[-1] != embeddings.shape[-1]:
        raise ValueError("vectors must have shape [d_model] or [n, d_model].")

    positions = find_nla_injection_positions(ids, config)
    if len(positions) != vecs.shape[0]:
        raise ValueError(
            f"found {len(positions)} valid NLA injection sites, expected {vecs.shape[0]}."
        )
    output = embeddings.clone()
    vecs = vecs.to(device=output.device, dtype=output.dtype)
    for vec_idx, (batch_idx, pos) in enumerate(positions):
        output[batch_idx, pos] = vecs[vec_idx]
    return output


class NLAActivationVerbalizer:
    """Activation verbalizer (AV): activation vector -> explanation text."""

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        config: NLAConfig,
        *,
        checkpoint: str | Path | None = None,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.checkpoint = str(checkpoint) if checkpoint is not None else None

    @classmethod
    def from_pretrained(
        cls,
        checkpoint: str | Path,
        *,
        cache_dir: str | Path | None = None,
        local_files_only: bool = False,
        token: str | bool | None = None,
        revision: str | None = None,
        device: str | None = None,
        device_map: str | Mapping[str, Any] | None = None,
        dtype: str | Any | None = None,
        trust_remote_code: bool = True,
        injection_scale_override: float | None = None,
        **model_kwargs: Any,
    ) -> NLAActivationVerbalizer:
        """Load an AV checkpoint from a local path or HuggingFace repo id."""

        torch = _require_torch()
        transformers = _require_transformers()
        checkpoint_path = _resolve_checkpoint_path(
            checkpoint,
            cache_dir=cache_dir,
            local_files_only=local_files_only,
            token=token,
            revision=revision,
        )
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            str(checkpoint_path),
            trust_remote_code=trust_remote_code,
            token=token,
            local_files_only=local_files_only,
        )
        config = load_nla_config(
            checkpoint_path,
            tokenizer=tokenizer,
            injection_scale_override=injection_scale_override,
        )
        if config.injection_scale is None:
            raise ValueError("actor NLA checkpoint must define extraction.injection_scale.")

        resolved_dtype = _resolve_torch_dtype(dtype, torch)
        if resolved_dtype is not None:
            model_kwargs.setdefault("torch_dtype", resolved_dtype)
        if device_map is not None:
            model_kwargs.setdefault("device_map", device_map)
        model_kwargs.setdefault("trust_remote_code", trust_remote_code)
        model_kwargs.setdefault("local_files_only", local_files_only)
        if token is not None:
            model_kwargs.setdefault("token", token)
        model = transformers.AutoModelForCausalLM.from_pretrained(
            str(checkpoint_path), **model_kwargs
        )
        model = _unwrap_language_model_if_present(model)
        model.eval()
        if device is not None and device_map is None:
            model.to(device)
        return cls(model, tokenizer, config, checkpoint=checkpoint_path)

    def build_inputs(self, activation: Any, *, prompt: str | None = None) -> dict[str, Any]:
        """Build ``inputs_embeds`` with the activation injected at the NLA marker."""

        torch = _require_torch()
        vector = torch.as_tensor(activation, dtype=torch.float32)
        if vector.ndim != 1 or vector.numel() != self.config.d_model:
            raise ValueError(
                f"activation must be a rank-1 vector of length {self.config.d_model}; "
                f"got shape {tuple(vector.shape)}."
            )
        input_ids = build_nla_prompt_input_ids(self.tokenizer, self.config, prompt=prompt)
        embed_layer = self.model.get_input_embeddings()
        device = _module_device(embed_layer)
        ids = torch.tensor([input_ids], dtype=torch.long, device=device)
        with torch.no_grad():
            embeddings = embed_layer(ids)
        scaled = normalize_nla_activation(
            vector.to(device=embeddings.device, dtype=embeddings.dtype),
            self.config.injection_scale,
        )
        injected = inject_nla_vectors(ids, embeddings, scaled, self.config)
        attention_mask = torch.ones(ids.shape, dtype=torch.long, device=ids.device)
        return {
            "inputs_embeds": injected,
            "attention_mask": attention_mask,
            "prompt_token_count": len(input_ids),
            "activation_norm": float(vector.float().norm().item()),
        }

    def explain(
        self,
        activation: Any,
        *,
        prompt: str | None = None,
        extract_explanation: bool = True,
        **generation_kwargs: Any,
    ) -> NLAActorOutput:
        """Generate an explanation for one activation vector."""

        torch = _require_torch()
        model_device = _module_device(self.model)
        inputs = self.build_inputs(activation, prompt=prompt)
        inputs_embeds = inputs["inputs_embeds"].to(model_device)
        attention_mask = inputs["attention_mask"].to(model_device)
        generation_kwargs.setdefault("max_new_tokens", 256)
        generation_kwargs.setdefault("do_sample", False)
        max_new_tokens = int(generation_kwargs["max_new_tokens"])
        _append_nla_stopping_criterion(generation_kwargs, self.tokenizer)
        if getattr(self.tokenizer, "pad_token_id", None) is None:
            eos_token_id = getattr(self.tokenizer, "eos_token_id", None)
            if eos_token_id is not None:
                generation_kwargs.setdefault("pad_token_id", eos_token_id)

        with torch.inference_mode():
            generated = self.model.generate(
                inputs_embeds=inputs_embeds,
                attention_mask=attention_mask,
                **generation_kwargs,
            )
        if hasattr(generated, "sequences"):
            generated = generated.sequences
        if torch.is_tensor(generated):
            generated_ids = generated[0].detach().cpu().tolist()
        else:
            generated_ids = list(
                generated[0] if generated and isinstance(generated[0], Sequence) else generated
            )
        raw_text = self.tokenizer.decode(generated_ids, skip_special_tokens=False)
        explanation = extract_nla_explanation(raw_text) if extract_explanation else raw_text.strip()
        generation_complete, finish_reason = _nla_generation_status(
            raw_text,
            generated_ids,
            max_new_tokens=max_new_tokens,
            eos_token_id=generation_kwargs.get(
                "eos_token_id",
                getattr(self.tokenizer, "eos_token_id", None),
            ),
        )
        return NLAActorOutput(
            explanation=explanation,
            raw_text=raw_text,
            prompt_token_count=int(inputs["prompt_token_count"]),
            activation_norm=float(inputs["activation_norm"]),
            generated_token_count=len(generated_ids),
            generation_complete=generation_complete,
            finish_reason=finish_reason,
        )

    def generate(self, activation: Any, **generation_kwargs: Any) -> str:
        """Return only the extracted explanation text for one activation."""

        return self.explain(activation, **generation_kwargs).explanation


class NLAActivationReconstructor:
    """Activation reconstructor (AR): explanation text -> activation vector."""

    def __init__(
        self,
        model: Any,
        value_head: Any,
        tokenizer: Any,
        config: NLAConfig,
        *,
        checkpoint: str | Path | None = None,
    ) -> None:
        self.model = model
        self.value_head = value_head
        self.tokenizer = tokenizer
        self.config = config
        self.checkpoint = str(checkpoint) if checkpoint is not None else None

    @classmethod
    def from_pretrained(
        cls,
        checkpoint: str | Path,
        *,
        cache_dir: str | Path | None = None,
        local_files_only: bool = False,
        token: str | bool | None = None,
        revision: str | None = None,
        device: str | None = None,
        dtype: str | Any | None = None,
        trust_remote_code: bool = True,
        **model_kwargs: Any,
    ) -> NLAActivationReconstructor:
        """Load an AR checkpoint from a local path or HuggingFace repo id."""

        torch = _require_torch()
        transformers = _require_transformers()
        load_file = _require_safetensors_load_file()
        checkpoint_path = _resolve_checkpoint_path(
            checkpoint,
            cache_dir=cache_dir,
            local_files_only=local_files_only,
            token=token,
            revision=revision,
        )
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            str(checkpoint_path),
            trust_remote_code=trust_remote_code,
            token=token,
            local_files_only=local_files_only,
        )
        config = load_nla_config(checkpoint_path, tokenizer=tokenizer, validate_tokenizer=False)
        if config.critic_prompt_template is None:
            raise ValueError("AR NLA checkpoint must define prompt_templates.ar or .critic.")
        if config.mse_scale is None:
            raise ValueError("AR NLA checkpoint must define a numeric extraction.mse_scale.")

        resolved_dtype = _resolve_torch_dtype(dtype, torch)
        if resolved_dtype is not None:
            model_kwargs.setdefault("torch_dtype", resolved_dtype)
        model_kwargs.setdefault("trust_remote_code", trust_remote_code)
        model_kwargs.setdefault("local_files_only", local_files_only)
        if token is not None:
            model_kwargs.setdefault("token", token)
        model = transformers.AutoModelForCausalLM.from_pretrained(
            str(checkpoint_path), **model_kwargs
        )
        model = _unwrap_language_model_if_present(model)
        model.eval()
        _strip_language_model_for_reconstruction(model, torch)

        hidden_size = _hidden_size_from_config(getattr(model, "config", None), config.d_model)
        value_head_dtype = None if resolved_dtype == "auto" else resolved_dtype
        value_head = torch.nn.Linear(
            hidden_size,
            hidden_size,
            bias=False,
            dtype=value_head_dtype,
        )
        head_path = Path(checkpoint_path) / "value_head.safetensors"
        if not head_path.exists():
            raise FileNotFoundError(
                f"no value_head.safetensors found in AR checkpoint {checkpoint_path}."
            )
        value_head.load_state_dict(load_file(str(head_path)))
        value_head.eval()
        if device is not None:
            model.to(device)
        _align_module_to_reference(value_head, model)
        return cls(model, value_head, tokenizer, config, checkpoint=checkpoint_path)

    def reconstruct(self, explanation: str) -> Any:
        """Reconstruct a raw activation vector from explanation text."""

        torch = _require_torch()
        if self.config.critic_prompt_template is None:
            raise ValueError("NLA config has no critic prompt template.")
        prompt = self.config.critic_prompt_template.format(explanation=explanation)
        encoded = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=True)
        input_ids = encoded["input_ids"].to(_module_device(self.model))
        attention_mask = encoded.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(input_ids.device)
        with torch.inference_mode():
            output = _inner_language_model(self.model)(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
            )
            hidden = output.last_hidden_state[0, -1].to(_module_device(self.value_head))
            return self.value_head(hidden).float().detach().cpu()

    def score(self, explanation: str, original_activation: Any) -> tuple[float, float]:
        """Return ``(mse_nrm, cosine)`` for an explanation and original vector."""

        torch = _require_torch()
        pred = self.reconstruct(explanation)
        gold = torch.as_tensor(original_activation, dtype=torch.float32, device=pred.device)
        if gold.ndim != 1 or gold.numel() != self.config.d_model:
            raise ValueError(
                f"original_activation must be length {self.config.d_model}; "
                f"got shape {tuple(gold.shape)}."
            )
        mse_scale = self.config.mse_scale
        pred_n = normalize_nla_activation(pred.float(), mse_scale)
        gold_n = normalize_nla_activation(gold.float(), mse_scale)
        mse = ((pred_n - gold_n) ** 2).mean().item()
        denom = pred_n.norm().clamp_min(1e-12) * gold_n.norm().clamp_min(1e-12)
        cosine = (pred_n @ gold_n / denom).item()
        return float(mse), float(cosine)


class NLAClient:
    """Combined AV/AR client for activation explanations and visualization rows."""

    def __init__(
        self,
        verbalizer: NLAActivationVerbalizer,
        reconstructor: NLAActivationReconstructor | None = None,
        *,
        profile: NLAProfile | None = None,
    ) -> None:
        self.verbalizer = verbalizer
        self.reconstructor = reconstructor
        self.profile = profile

    @classmethod
    def from_profile(
        cls,
        profile: str | NLAProfile,
        *,
        load_reconstructor: bool = True,
        cache_dir: str | Path | None = None,
        local_files_only: bool = False,
        token: str | bool | None = None,
        revision: str | None = None,
        reconstructor_revision: str | None = None,
        device: str | None = None,
        dtype: str | Any | None = None,
        trust_remote_code: bool = True,
        actor_kwargs: Mapping[str, Any] | None = None,
        reconstructor_kwargs: Mapping[str, Any] | None = None,
    ) -> NLAClient:
        """Load an official NLA profile pair from HuggingFace."""

        resolved = get_nla_profile(profile) if isinstance(profile, str) else profile
        verbalizer = NLAActivationVerbalizer.from_pretrained(
            resolved.av_repo,
            cache_dir=cache_dir,
            local_files_only=local_files_only,
            token=token,
            revision=revision,
            device=device,
            dtype=dtype,
            trust_remote_code=trust_remote_code,
            **dict(actor_kwargs or {}),
        )
        reconstructor = None
        if load_reconstructor and resolved.ar_repo is not None:
            reconstructor = NLAActivationReconstructor.from_pretrained(
                resolved.ar_repo,
                cache_dir=cache_dir,
                local_files_only=local_files_only,
                token=token,
                revision=(
                    reconstructor_revision
                    if reconstructor_revision is not None
                    else revision
                ),
                device=device,
                dtype=dtype,
                trust_remote_code=trust_remote_code,
                **dict(reconstructor_kwargs or {}),
            )
        return cls(verbalizer, reconstructor, profile=resolved)

    def explain_activation(
        self,
        activation: Any,
        *,
        sample_id: str = "0",
        token_index: int | None = None,
        token: str | None = None,
        source: str = "activation",
        prompt: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        **generation_kwargs: Any,
    ) -> NLAResult:
        """Explain one activation vector and optionally compute AR fidelity."""

        actor_output = self.verbalizer.explain(activation, prompt=prompt, **generation_kwargs)
        mse_nrm = None
        cosine = None
        if self.reconstructor is not None and actor_output.generation_complete:
            mse_nrm, cosine = self.reconstructor.score(actor_output.explanation, activation)
        profile = self.profile
        result_metadata = dict(metadata or {})
        result_metadata["prompt_token_count"] = actor_output.prompt_token_count
        result_metadata["generated_token_count"] = actor_output.generated_token_count
        result_metadata["generation_complete"] = actor_output.generation_complete
        result_metadata["finish_reason"] = actor_output.finish_reason
        return NLAResult(
            explanation=actor_output.explanation,
            raw_text=actor_output.raw_text,
            sample_id=str(sample_id),
            token_index=token_index,
            token=token,
            source=source,
            model_name=profile.base_model if profile is not None else "",
            layer=profile.layer if profile is not None else None,
            component=profile.component if profile is not None else "resid_post",
            profile=profile.name if profile is not None else None,
            activation_norm=actor_output.activation_norm,
            mse_nrm=mse_nrm,
            cosine=cosine,
            metadata=result_metadata,
        )

    def explain_activations(
        self,
        activations: Any,
        *,
        tokens: Sequence[Any] | None = None,
        positions: Sequence[int] | None = None,
        batch_index: int = 0,
        sample_id: str = "0",
        source: str = "activation",
        prompt: str | None = None,
        metadata_by_position: Mapping[int, Mapping[str, Any]] | None = None,
        **generation_kwargs: Any,
    ) -> list[NLAResult]:
        """Explain selected positions from a ``[seq, d]`` or ``[batch, seq, d]`` tensor."""

        torch = _require_torch()
        tensor = activations if torch.is_tensor(activations) else torch.as_tensor(activations)
        if tensor.ndim == 3:
            tensor = tensor[batch_index]
        if tensor.ndim != 2 or tensor.shape[-1] != self.verbalizer.config.d_model:
            raise ValueError("activations must have shape [seq, d_model] or [batch, seq, d_model].")
        selected_positions = (
            list(positions) if positions is not None else list(range(tensor.shape[0]))
        )
        token_labels = [str(token) for token in tokens] if tokens is not None else None
        results = []
        for pos in selected_positions:
            token_label = (
                token_labels[pos] if token_labels is not None and pos < len(token_labels) else None
            )
            row_metadata = (
                metadata_by_position.get(int(pos), {}) if metadata_by_position is not None else {}
            )
            results.append(
                self.explain_activation(
                    tensor[pos],
                    sample_id=sample_id,
                    token_index=int(pos),
                    token=token_label,
                    source=source,
                    prompt=prompt,
                    metadata=row_metadata,
                    **generation_kwargs,
                )
            )
        return results

    def explain_cache(
        self,
        cache: Mapping[Any, Any],
        *,
        activation_name: Any | None = None,
        tokens: Sequence[Any] | None = None,
        positions: Sequence[int] | None = None,
        batch_index: int = 0,
        sample_id: str = "0",
        prompt: str | None = None,
        metadata_by_position: Mapping[int, Mapping[str, Any]] | None = None,
        **generation_kwargs: Any,
    ) -> list[NLAResult]:
        """Explain activations from a SafeLens/TransformerLens-style cache."""

        activation = _cache_activation_for_profile(cache, self.profile, activation_name)
        source = (
            str(activation_name)
            if activation_name is not None
            else _default_cache_key_label(self.profile)
        )
        return self.explain_activations(
            activation,
            tokens=tokens,
            positions=positions,
            batch_index=batch_index,
            sample_id=sample_id,
            source=source,
            prompt=prompt,
            metadata_by_position=metadata_by_position,
            **generation_kwargs,
        )


def extract_nla_explanation(text: str) -> str:
    """Extract ``<explanation>...</explanation>`` payload, or return raw text."""

    match = EXPLANATION_RE.search(text)
    if match:
        return match.group(1).strip()
    cleaned = text.strip()
    if "<explanation>" in cleaned:
        cleaned = cleaned.split("<explanation>", 1)[1]
    if "</explanation>" in cleaned:
        cleaned = cleaned.split("</explanation>", 1)[0]
    return cleaned.strip()


def _append_nla_stopping_criterion(
    generation_kwargs: dict[str, Any],
    tokenizer: Any,
) -> None:
    """Stop generation as soon as the AV output contract is complete."""

    transformers = _require_transformers()

    # StoppingCriteriaList only requires callable criteria; avoiding a direct
    # optional-class inheritance keeps this runtime compatible with all
    # supported Transformers versions and with static type checking.
    class _StopAfterExplanation:
        def __call__(self, input_ids: Any, scores: Any, **kwargs: Any) -> Any:
            del scores, kwargs
            complete = [
                EXPLANATION_END_TAG
                in tokenizer.decode(row.detach().cpu().tolist(), skip_special_tokens=False)
                for row in input_ids
            ]
            return input_ids.new_tensor(complete, dtype=_require_torch().bool)

    existing = generation_kwargs.get("stopping_criteria")
    criteria = list(existing) if existing is not None else []
    criteria.append(_StopAfterExplanation())
    generation_kwargs["stopping_criteria"] = transformers.StoppingCriteriaList(criteria)


def _nla_generation_status(
    raw_text: str,
    generated_ids: Sequence[int],
    *,
    max_new_tokens: int,
    eos_token_id: int | Sequence[int] | None,
) -> tuple[bool, str]:
    """Return whether the AV contract completed and why decoding stopped."""

    if EXPLANATION_END_TAG in raw_text:
        return True, "end_tag"
    eos_ids = (
        {int(eos_token_id)}
        if isinstance(eos_token_id, int)
        else {int(token_id) for token_id in eos_token_id or ()}
    )
    if generated_ids and int(generated_ids[-1]) in eos_ids:
        return False, "eos"
    if len(generated_ids) >= max_new_tokens:
        return False, "length"
    return False, "unknown"


def _resolve_target_scale(raw: Any, d_model: int) -> float | None:
    if raw is None or raw in {"raw", "none"}:
        return None
    if raw == SCALE_SQRT_D:
        return math.sqrt(d_model)
    return float(raw)


def _sidecar_path_for(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.name == "nla_meta.yaml":
        return candidate
    return candidate / "nla_meta.yaml"


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _as_token_rows(input_ids: Any) -> list[list[int]]:
    detach = getattr(input_ids, "detach", None)
    if callable(detach):
        input_ids = cast(Any, detach()).cpu().tolist()
    if not isinstance(input_ids, Sequence) or isinstance(input_ids, str | bytes):
        raise TypeError("input_ids must be a token id sequence.")
    if input_ids and isinstance(input_ids[0], Sequence) and not isinstance(input_ids[0], int):
        return [[int(token_id) for token_id in row] for row in input_ids]
    return [[int(token_id) for token_id in input_ids]]


def _resolve_checkpoint_path(
    checkpoint: str | Path,
    *,
    cache_dir: str | Path | None,
    local_files_only: bool,
    token: str | bool | None,
    revision: str | None,
) -> Path:
    candidate = Path(checkpoint)
    if candidate.exists():
        return candidate
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise ImportError(
            "Loading NLA checkpoints from HuggingFace requires huggingface_hub. "
            "Install SafeLens with the 'nla' extra."
        ) from exc
    return Path(
        snapshot_download(
            repo_id=str(checkpoint),
            cache_dir=str(cache_dir) if cache_dir is not None else None,
            local_files_only=local_files_only,
            token=token,
            revision=revision,
        )
    )


def _require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise ImportError(
            "NLA inference requires torch. Install SafeLens with the 'nla' extra."
        ) from exc
    return torch


def _require_transformers() -> Any:
    try:
        import transformers
    except ImportError as exc:
        raise ImportError(
            "NLA model loading requires transformers. Install SafeLens with the 'nla' extra."
        ) from exc
    return transformers


def _require_safetensors_load_file() -> Any:
    try:
        from safetensors.torch import load_file
    except ImportError as exc:
        raise ImportError(
            "NLA AR reconstruction requires safetensors. Install SafeLens with the 'nla' extra."
        ) from exc
    return load_file


def _resolve_torch_dtype(dtype: str | Any | None, torch: Any) -> Any | None:
    if dtype is None:
        return None
    if not isinstance(dtype, str):
        return dtype
    normalized = dtype.lower().replace("torch.", "")
    try:
        return {
            "auto": "auto",
            "float32": torch.float32,
            "fp32": torch.float32,
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
        }[normalized]
    except KeyError as exc:
        raise ValueError(f"unsupported torch dtype string {dtype!r}.") from exc


def _module_device(module: Any) -> Any:
    parameters = getattr(module, "parameters", None)
    if callable(parameters):
        try:
            parameter_iter = iter(cast(Iterable[Any], parameters()))
            return next(parameter_iter).device
        except (StopIteration, TypeError):
            pass
    weight = getattr(module, "weight", None)
    if weight is not None and hasattr(weight, "device"):
        return weight.device
    torch = _require_torch()
    return torch.device("cpu")


def _align_module_to_reference(module: Any, reference: Any) -> None:
    parameters = getattr(reference, "parameters", None)
    if not callable(parameters):
        module.to(_module_device(reference))
        return
    try:
        parameter = next(iter(cast(Iterable[Any], parameters())))
    except (StopIteration, TypeError):
        module.to(_module_device(reference))
        return
    module.to(device=parameter.device, dtype=parameter.dtype)


def _strip_language_model_for_reconstruction(model: Any, torch: Any) -> None:
    if hasattr(model, "lm_head"):
        model.lm_head = torch.nn.Identity()
    inner = _inner_language_model(model)
    for attr in _FINAL_LAYER_NORM_ATTRS:
        if hasattr(inner, attr):
            setattr(inner, attr, torch.nn.Identity())
            return
    raise ValueError(
        f"could not find final layernorm on {type(inner).__name__}; "
        f"tried {_FINAL_LAYER_NORM_ATTRS!r}."
    )


def _unwrap_language_model_if_present(model: Any) -> Any:
    language_model = getattr(model, "language_model", None)
    return language_model if language_model is not None else model


def _inner_language_model(model: Any) -> Any:
    language_model = getattr(model, "language_model", None)
    if language_model is not None:
        if hasattr(language_model, "model"):
            return language_model.model
        return language_model
    if hasattr(model, "model"):
        return model.model
    if hasattr(model, "transformer"):
        return model.transformer
    raise ValueError(f"{type(model).__name__} has no recognized inner language-model module.")


def _hidden_size_from_config(config: Any, default: int) -> int:
    if config is None:
        return default
    text_config = getattr(config, "text_config", config)
    return int(getattr(text_config, "hidden_size", default))


def _cache_activation_for_profile(
    cache: Mapping[Any, Any],
    profile: NLAProfile | None,
    activation_name: Any | None,
) -> Any:
    if activation_name is not None:
        return cache[activation_name]
    if profile is None:
        raise ValueError("activation_name is required when the NLA client has no profile.")
    candidate_keys = (
        f"layer_{profile.layer}.{profile.component}",
        f"blocks.{profile.layer}.hook_{profile.component}",
        (profile.component, profile.layer),
    )
    for key in candidate_keys:
        if key in cache:
            return cache[key]
    raise KeyError(
        "could not find an NLA-compatible activation in cache; tried "
        + ", ".join(map(str, candidate_keys))
    )


def _default_cache_key_label(profile: NLAProfile | None) -> str:
    if profile is None:
        return "activation"
    return f"layer_{profile.layer}.{profile.component}"


__all__ = [
    "EXPLANATION_RE",
    "INJECT_PLACEHOLDER",
    "NLAActivationReconstructor",
    "NLAActivationVerbalizer",
    "NLAActorOutput",
    "NLAClient",
    "NLAConfig",
    "NLAProfile",
    "NLAResult",
    "NLA_SUPPORTED_PROFILES",
    "build_nla_prompt_input_ids",
    "extract_nla_explanation",
    "find_nla_injection_positions",
    "get_nla_profile",
    "inject_nla_vectors",
    "list_nla_profiles",
    "load_nla_config",
    "normalize_nla_activation",
    "validate_nla_tokenizer",
]
