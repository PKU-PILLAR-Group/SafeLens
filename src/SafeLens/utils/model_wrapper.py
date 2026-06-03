"""Model wrapper implementations and hook helpers."""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from inspect import Parameter, signature
from numbers import Integral
from pathlib import Path
from typing import Any

from SafeLens.core.base import (
    Batch,
    HookFn,
    LayerRef,
    ModelLoadConfig,
    ModelWrapper,
)
from SafeLens.core.factored_matrix import (
    FactoredMatrix,
    composition_scores,
    shape_of,
    svd_nested,
    transpose,
)
from SafeLens.core.hook_call import call_user_hook
from SafeLens.core.hooks import (
    ActivationCache,
    NamesFilter,
    activation_name_for_layer,
    make_cache_hook,
    matches_names_filter,
)
from SafeLens.core.kv_cache import KeyValueCacheEntry
from SafeLens.core.utilities import get_rotary_pct_from_config
from SafeLens.utils.model_bridge import (
    ComponentHookContext,
    ComponentRef,
    _is_transformers_conv1d_module,
    _register_module_forward_hook,
    _register_module_forward_pre_hook,
    architecture_adapter_for_model,
    architecture_adapter_for_name,
    call_component_hook,
    extract_component_activation,
    extract_qkv_bias,
    first_output,
    head_count_for_component,
    is_qwen_routed_moe_model_name,
    key_value_head_count,
    list_architecture_adapters,
    merge_component_activation,
    preferred_attention_weight_packed_axis,
    preferred_qkv_weight_packed_axis,
    qkv_group_size,
    qkv_weight_bounds,
    reshape_attention_bias,
    reshape_attention_weight,
    reshape_joint_qkv_attention_bias,
    reshape_joint_qkv_attention_weight,
    resolve_module_path,
    supported_transformer_component_names,
    transform_component_activation,
    transformer_lens_component_name,
    transpose_2d_weight,
    zeros_for_attention_bias,
    zeros_like_last_dim,
)
from SafeLens.utils.model_registry import (
    ModelAdapterCapabilities,
    ModelAdapterSpec,
    get_model_adapter_registry,
    resolve_model_download_plan,
)
from SafeLens.utils.transformer_lens_support import (
    is_transformer_lens_native_checkpoint,
    is_transformer_lens_official_model_name,
    is_transformer_lens_supported_model_name,
    resolve_transformer_lens_compatible_model_name,
    transformer_lens_model_kind,
    transformer_lens_official_model_names,
)

_QWEN3_DENSE_MAX_PARAMS_B = 35.0
_QWEN3_PATCHABLE_COMPONENTS = {
    "resid_pre",
    "resid_mid",
    "resid_post",
    "attn_out",
    "mlp_out",
    "q",
    "k",
    "v",
    "z",
    "result",
}
_QWEN3_EXPLICIT_COMPONENTS = {"pre", "pre_linear", "post"}
_QWEN3_CACHE_ONLY_COMPONENTS: set[str] = set()
_QWEN3_ATTENTION_COMPONENTS = {"pattern", "attn_scores"}
_QWEN3_COMPONENT_EXAMPLES = (
    "layer_0.resid_pre",
    "layer_0.resid_mid",
    "layer_0.resid_post",
    "layer_0.attn_out",
    "layer_0.mlp_out",
    "layer_0.pre",
    "layer_0.pre_linear",
    "layer_0.post",
    "layer_0.q",
    "layer_0.k",
    "layer_0.v",
    "layer_0.z",
    "layer_0.result",
    "layer_0.pattern",
    "layer_0.attn_scores",
    "blocks.0.hook_resid_pre",
    "blocks.0.attn.hook_q",
    "blocks.0.mlp.hook_pre",
    "blocks.0.mlp.hook_pre_linear",
    "blocks.0.mlp.hook_post",
    "blocks.0.attn.hook_result",
    "blocks.0.attn.hook_pattern",
    "blocks.0.attn.hook_attn_scores",
)
_TRANSFORMER_LENS_HOOK_COMPONENTS = (
    "hook_embed",
    "hook_pos_embed",
    "blocks.N.hook_resid_pre",
    "blocks.N.hook_resid_mid",
    "blocks.N.hook_resid_post",
    "blocks.N.hook_attn_in",
    "blocks.N.hook_q_input",
    "blocks.N.hook_k_input",
    "blocks.N.hook_v_input",
    "blocks.N.attn.hook_q",
    "blocks.N.attn.hook_k",
    "blocks.N.attn.hook_v",
    "blocks.N.attn.hook_z",
    "blocks.N.attn.hook_pattern",
    "blocks.N.attn.hook_attn_scores",
    "blocks.N.attn.hook_result",
    "blocks.N.hook_attn_out",
    "blocks.N.hook_mlp_in",
    "blocks.N.mlp.hook_pre",
    "blocks.N.mlp.hook_pre_linear",
    "blocks.N.mlp.hook_post",
    "blocks.N.hook_mlp_out",
    "ln_final.hook_scale",
)
_TRANSFORMER_LENS_RUNTIME_FLAG_DEFAULTS = {
    "use_attn_result": False,
    "use_split_qkv_input": False,
    "use_hook_mlp_in": False,
    "use_attn_in": False,
    "ungroup_grouped_query_attention": False,
}
_TRANSFORMER_LENS_PATCH_COMPONENTS = (
    "embed",
    "pos_embed",
    "resid_pre",
    "resid_mid",
    "resid_post",
    "attn_in",
    "attn_out",
    "mlp_in",
    "mlp_out",
    "q_input",
    "k_input",
    "v_input",
    "pre",
    "pre_linear",
    "post",
    "q",
    "k",
    "v",
    "z",
    "pattern",
    "attn_scores",
)
_DEFAULT_RETURN_TYPE = object()
_DEFAULT_CACHE_ALL = object()
_DEFAULT_RETURN_CACHE_OBJECT = object()
_DEFAULT_LOSS_PER_TOKEN = object()
_MISSING_ATTENTION_IMPLEMENTATION = object()
_DEFAULT_CACHE_EXCLUDED_COMPONENTS = {"attn_scores"}
_RETURN_TYPE_ALIASES = {
    "logit": "logits",
    "logits": "logits",
    "loss": "loss",
    "both": "both",
    "model_output": "model_output",
    "raw": "model_output",
    "output": "model_output",
}
_TL_FORWARD_POSITIONAL_ARG_NAMES = (
    "return_type",
    "loss_per_token",
    "prepend_bos",
    "padding_side",
    "start_at_layer",
    "tokens",
    "shortformer_pos_embed",
    "attention_mask",
    "stop_at_layer",
    "past_kv_cache",
)
_TOP_LEVEL_HOOK_ALIASES = {
    "hook_embed": "hook_embed",
    "embed": "hook_embed",
    "hook_pos_embed": "hook_pos_embed",
    "pos_embed": "hook_pos_embed",
    "ln_final.hook_scale": "ln_final.hook_scale",
    "hook_scale": "ln_final.hook_scale",
}
_TOKEN_EMBEDDING_MODULE_PATHS = (
    "transformer.wte",
    "wte",
    "transformer.word_embeddings",
    "word_embeddings",
    "gpt_neox.embed_in",
    "model.embed_tokens",
    "model.decoder.embed_tokens",
    "decoder.embed_tokens",
    "embed_tokens",
    "encoder.embed_tokens",
    "shared",
    "bert.embeddings.word_embeddings",
    "roberta.embeddings.word_embeddings",
    "distilbert.embeddings.word_embeddings",
    "embeddings.word_embeddings",
)
_POSITION_EMBEDDING_MODULE_PATHS = (
    "transformer.wpe",
    "wpe",
    "model.wpe",
    "model.embed_positions",
    "model.decoder.embed_positions",
    "decoder.embed_positions",
    "embed_positions",
    "bert.embeddings.position_embeddings",
    "roberta.embeddings.position_embeddings",
    "distilbert.embeddings.position_embeddings",
    "embeddings.position_embeddings",
)
_FINAL_NORM_MODULE_PATHS = (
    "ln_final",
    "final_layer_norm",
    "ln_f",
    "transformer.ln_f",
    "gpt_neox.final_layer_norm",
    "decoder.final_layer_norm",
    "model.ln_final",
    "model.final_layer_norm",
    "model.ln_f",
    "model.transformer.ln_f",
    "model.gpt_neox.final_layer_norm",
    "model.decoder.final_layer_norm",
    "norm",
    "model.norm",
    "model.model.norm",
    "model.model.final_layer_norm",
)


@dataclass(frozen=True)
class TransformerLensConfigView:
    """Small read-only TransformerLens-style config view for wrapped HF models."""

    model_name: str
    model_type: str | None = None
    n_layers: int | None = None
    n_heads: int | None = None
    n_key_value_heads: int | None = None
    d_model: int | None = None
    d_head: int | None = None
    d_vocab: int | None = None
    n_ctx: int | None = None
    d_mlp: int | None = None
    act_fn: str | None = None
    normalization_type: str | None = None
    positional_embedding_type: str | None = None
    device: str | None = None
    dtype: str | None = None
    original_architecture: str | None = None
    use_attn_result: bool = False
    use_split_qkv_input: bool = False
    use_hook_mlp_in: bool = False
    use_attn_in: bool = False
    ungroup_grouped_query_attention: bool = False
    attn_only: bool = False
    parallel_attn_mlp: bool = False
    rmsnorm_uses_offset: bool = False

    @property
    def n_params(self) -> None:
        return None

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


class _RemovableHandle:
    def __init__(self, remove_fn: Callable[[], None]) -> None:
        self._remove_fn = remove_fn
        self._removed = False

    def remove(self) -> None:
        if not self._removed:
            self._remove_fn()
            self._removed = True


class _TrackedAttentionHandle:
    def __init__(self, handle: Any, remove_callback: Callable[[], None]) -> None:
        self._handle = handle
        self._remove_callback = remove_callback
        self.hook_contexts = tuple(getattr(handle, "hook_contexts", ()))
        self._removed = False

    def remove(self) -> None:
        if self._removed:
            return
        try:
            remove = getattr(self._handle, "remove", None)
            if callable(remove):
                remove()
        finally:
            self._remove_callback()
            self._removed = True


class _HookHandleWithContexts:
    def __init__(self, handle: Any, hook_contexts: Sequence[Any]) -> None:
        self._handle = handle
        self.hook_contexts = tuple(hook_contexts)

    def remove(self) -> None:
        remove = getattr(self._handle, "remove", None)
        if callable(remove):
            remove()


class _BackwardHookRegistrationHandle:
    def __init__(self, handle: Any, hook_contexts: Sequence[Any]) -> None:
        self._handle = handle
        self.hook_contexts = tuple(hook_contexts)
        self.is_backward = True

    def remove(self) -> None:
        remove = getattr(self._handle, "remove", None)
        if callable(remove):
            remove()


class _TopLevelHookContext:
    """Small HookPoint-like object for TL top-level embedding hooks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.component = _top_level_component_name(name)
        self.safelens_name = self.component
        self.ctx: dict[str, Any] = {}

    def layer(self) -> int:
        raise ValueError(f"Top-level hook {self.name!r} has no layer index.")


class _RawHookContext:
    """HookPoint-like context for plain named-module hooks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.safelens_name = name
        self.ctx: dict[str, Any] = {}

    def layer(self) -> int:
        match = re.search(r"(?:blocks\.|layer_)(\d+)", self.name)
        if match is None:
            raise ValueError(f"Cannot infer layer from hook name {self.name!r}.")
        return int(match.group(1))


class _ManagedWrapperHookHandle:
    def __init__(
        self,
        handle: Any,
        remove_callback: Callable[[], None],
        *,
        is_permanent: bool = False,
        level: int | None = None,
        is_cache: bool = False,
    ) -> None:
        self._handle = handle
        self._remove_callback = remove_callback
        self.is_permanent = is_permanent
        self.level = level
        self.is_cache = is_cache
        self.hook_contexts = tuple(getattr(handle, "hook_contexts", ()))
        self.is_backward = bool(getattr(handle, "is_backward", False))
        self._removed = False

    def remove(self) -> None:
        if self._removed:
            return
        try:
            remove = getattr(self._handle, "remove", None)
            if callable(remove):
                remove()
        finally:
            self._remove_callback()
            self._removed = True


class _CompositeWrapperHookHandle:
    def __init__(self, handles: Iterable[Any]) -> None:
        self.handles = tuple(handles)
        self.hook_contexts = tuple(
            hook_context
            for handle in self.handles
            for hook_context in getattr(handle, "hook_contexts", ())
        )
        self.is_backward = any(getattr(handle, "is_backward", False) for handle in self.handles)
        self._removed = False

    def remove(self) -> None:
        if self._removed:
            return
        _remove_wrapper_handles(self.handles)
        self._removed = True


def _resolve_hook_argument(
    hook_fn: HookFn | None = None,
    *,
    hook: HookFn | None = None,
) -> HookFn:
    if hook_fn is not None and hook is not None:
        raise TypeError("Pass only one of `hook_fn` or `hook`.")
    resolved_hook = hook_fn if hook_fn is not None else hook
    if not callable(resolved_hook):
        raise TypeError("hook must be callable.")
    return resolved_hook


class DummyModelWrapper(ModelWrapper):
    """Small in-memory model wrapper used by tests and architecture demos."""

    def __init__(self, name: str = "dummy") -> None:
        self.name = name
        self.loaded = False
        self._hooks: list[tuple[LayerRef, HookFn]] = []

    def load_model(self) -> DummyModelWrapper:
        self.loaded = True
        return self

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> _RemovableHandle:
        item = (layer, hook_fn)
        self._hooks.append(item)
        return _RemovableHandle(lambda: self._remove_hook(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        *,
        names_filter: NamesFilter = None,
        return_cache_object: bool = False,
        remove_batch_dim: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any] | ActivationCache]:
        if not self.loaded:
            self.load_model()

        candidate_layers = list(layers or [layer for layer, _ in self._hooks])
        selected_layers = _filter_hook_names(
            [activation_name_for_layer(layer) for layer in candidate_layers],
            names_filter,
        )
        cache = {name: {"batch": dict(batch)} for name in selected_layers}
        model_output = {
            "text": batch.get("text") or batch.get("prompt") or "",
            "risk_score": float(batch.get("risk_score", 0.0)),
        }

        for layer, hook_fn in list(self._hooks):
            name = activation_name_for_layer(layer)
            if name in selected_layers:
                activation = cache.get(name, {"batch": dict(batch)})
                patched = _call_dummy_hook(
                    hook_fn,
                    layer=layer,
                    batch=batch,
                    cache=cache,
                    activation=activation,
                )
                if patched is not None:
                    cache[name] = patched

        return model_output, _format_cache_result(
            cache,
            model=self,
            return_cache_object=return_cache_object,
            remove_batch_dim=remove_batch_dim,
        )

    def generate(self, prompt: str | Sequence[str], **generation_kwargs: Any) -> str | list[str]:
        _ = generation_kwargs
        return f"{prompt} [dummy generation]"

    def generate_stream(
        self,
        prompt: str | Sequence[str],
        *,
        max_new_tokens: int = 10,
        max_tokens_per_yield: int = 25,
        **generation_kwargs: Any,
    ) -> Iterable[str | list[str]]:
        generated = self.generate(prompt, max_new_tokens=max_new_tokens, **generation_kwargs)
        if isinstance(generated, list):
            yield generated
        else:
            for start in range(0, len(generated), max_tokens_per_yield):
                yield generated[start : start + max_tokens_per_yield]

    def remove_hooks(self) -> None:
        self._hooks.clear()

    def _remove_hook(self, item: tuple[LayerRef, HookFn]) -> None:
        if item in self._hooks:
            self._hooks.remove(item)


def _call_dummy_hook(
    hook_fn: HookFn,
    *,
    layer: LayerRef,
    batch: Batch,
    cache: dict[str, Any],
    activation: Any,
) -> Any:
    hook_kwargs = {
        "layer": layer,
        "batch": batch,
        "cache": cache,
        "activation": activation,
        "output": activation,
        "hook": None,
    }
    return call_user_hook(
        hook_fn,
        hook_kwargs,
        positional_arg_options=((activation, None), (None, None, activation), (activation,)),
        uninspectable="kwargs",
    )


def _remove_wrapper_handles(handles: Iterable[Any]) -> None:
    for handle in reversed(list(handles)):
        remove = getattr(handle, "remove", None)
        if callable(remove):
            remove()


def _keep_wrapper_handles(
    wrapper: Any,
    handles: Iterable[Any],
    *,
    is_cache: bool = False,
) -> None:
    for handle in handles:
        if isinstance(handle, _ManagedWrapperHookHandle):
            managed_handle = handle
        else:
            managed_handle = wrapper._track_hook_handle(
                handle,
                is_permanent=False,
                is_cache=is_cache,
            )
        wrapper._hooks.append(managed_handle)


class HuggingFaceModelWrapper(ModelWrapper):
    """Transformers-based model wrapper with forward hook support."""

    def __init__(
        self,
        name: str,
        dtype: str = "float32",
        device: str | None = None,
        revision: str | None = None,
        cache_dir: str | None = None,
        trust_remote_code: bool = False,
        load_kwargs: dict[str, Any] | None = None,
        tokenizer_kwargs: dict[str, Any] | None = None,
        pretrained_path: str | None = None,
        pretrained_path_is_local: bool = False,
    ) -> None:
        self.name = name
        self.dtype = dtype
        self.device = device
        self.revision = revision
        self.cache_dir = cache_dir
        self.trust_remote_code = trust_remote_code
        self.load_kwargs = load_kwargs or {}
        self.tokenizer_kwargs = tokenizer_kwargs or {}
        self.pretrained_path = pretrained_path
        self._pretrained_path_is_local = bool(pretrained_path_is_local)
        self.model: Any = None
        self.tokenizer: Any = None
        self._tokenizer_load_error: Exception | None = None
        self._hooks: list[Any] = []
        self.is_caching = False
        self._temporary_backward_hook_depth = 0
        self._attention_hook_count = 0
        self._run_requires_output_attentions = False
        self._transformer_lens_runtime_flags = dict(_TRANSFORMER_LENS_RUNTIME_FLAG_DEFAULTS)

    @property
    def cfg(self) -> TransformerLensConfigView:
        """Return a TransformerLens-style normalized config view."""
        return _make_transformer_lens_config_view(
            self._require_model(),
            model_name=self.name,
            device=self.device,
            dtype=self.dtype,
            tokenizer=self.tokenizer,
            runtime_flags=self._transformer_lens_runtime_flags,
        )

    def set_use_attn_result(self, use_attn_result: bool) -> None:
        """Mirror TransformerLens' runtime switch for per-head attention results."""
        self._set_transformer_lens_runtime_flag("use_attn_result", use_attn_result)

    def set_use_split_qkv_input(self, use_split_qkv_input: bool) -> None:
        """Mirror TransformerLens' runtime switch for split Q/K/V input hooks."""
        self._set_transformer_lens_runtime_flag("use_split_qkv_input", use_split_qkv_input)

    def set_use_hook_mlp_in(self, use_hook_mlp_in: bool) -> None:
        """Mirror TransformerLens' runtime switch for MLP input hooks."""
        if bool(use_hook_mlp_in) and self.cfg.attn_only:
            raise AssertionError("Cannot use hook_mlp_in on attention-only models.")
        self._set_transformer_lens_runtime_flag("use_hook_mlp_in", use_hook_mlp_in)

    def set_use_attn_in(self, use_attn_in: bool) -> None:
        """Mirror TransformerLens' runtime switch for attention input hooks."""
        if bool(use_attn_in) and self._has_grouped_query_attention():
            raise AssertionError(
                "Cannot use attn_in hooks when key/value heads are grouped; "
                "SafeLens exposes the config switch but does not synthesize missing HF hooks."
            )
        self._set_transformer_lens_runtime_flag("use_attn_in", use_attn_in)

    def set_ungroup_grouped_query_attention(self, ungroup_grouped_query_attention: bool) -> None:
        """Mirror TransformerLens' grouped-query attention compatibility switch."""
        self._set_transformer_lens_runtime_flag(
            "ungroup_grouped_query_attention",
            ungroup_grouped_query_attention,
        )

    def _set_transformer_lens_runtime_flag(self, name: str, value: bool) -> None:
        if name not in _TRANSFORMER_LENS_RUNTIME_FLAG_DEFAULTS:
            raise KeyError(f"Unknown TransformerLens runtime flag {name!r}.")
        self._transformer_lens_runtime_flags[name] = bool(value)

    def _has_grouped_query_attention(self) -> bool:
        cfg = self.cfg
        return (
            cfg.n_heads is not None
            and cfg.n_key_value_heads is not None
            and cfg.n_key_value_heads < cfg.n_heads
        )

    def _uses_decoder_text_input_semantics(self) -> bool:
        return transformer_lens_model_kind(self.name) == "decoder"

    def check_hooks_to_add(
        self,
        hook_point: Any,
        hook_point_name: str,
        hook: Any,
        dir: str = "fwd",
        is_permanent: bool = False,
        prepend: bool = False,
    ) -> None:
        """Validate TransformerLens runtime-hook flags before adding hooks."""
        _ = hook_point, hook, dir, is_permanent, prepend
        if hook_point_name.endswith("attn.hook_result") or hook_point_name.endswith("hook_result"):
            assert (
                self.cfg.use_attn_result
            ), f"Cannot add hook {hook_point_name} if use_attn_result_hook is False"
        if hook_point_name.endswith(("hook_q_input", "hook_k_input", "hook_v_input")):
            assert (
                self.cfg.use_split_qkv_input
            ), f"Cannot add hook {hook_point_name} if use_split_qkv_input is False"
        if hook_point_name.endswith("mlp_in"):
            assert (
                self.cfg.use_hook_mlp_in
            ), f"Cannot add hook {hook_point_name} if use_hook_mlp_in is False"
        if hook_point_name.endswith("attn_in"):
            assert (
                self.cfg.use_attn_in
            ), f"Cannot add hook {hook_point_name} if use_attn_in is False"

    def get_pos_offset(self, past_kv_cache: Any, batch_size: int) -> int:
        """Return the positional offset implied by a TransformerLens KV cache."""
        if past_kv_cache is None:
            return 0
        cached_batch_size = _past_kv_cache_batch_size(past_kv_cache)
        if cached_batch_size is not None:
            assert int(cached_batch_size) == int(batch_size)
        return _past_kv_cache_length(past_kv_cache)

    def get_residual(
        self,
        embed: Any,
        pos_offset: int,
        prepend_bos: bool | None = None,
        attention_mask: Any | None = None,
        tokens: Any | None = None,
        return_shortformer_pos_embed: bool = True,
        device: Any = None,
    ) -> Any:
        """Convert token embeddings into the first residual stream."""
        model = self._require_model()
        resolved_device = self.device if device is None else device
        if tokens is None:
            tokens = _ones_token_batch_like_embedding(embed, device=resolved_device)
        else:
            tokens = _coerce_token_model_input(
                _ensure_token_batch_dim(tokens), device=resolved_device
            )

        position_type = _infer_positional_embedding_type(model)
        if position_type == "standard":
            pos_module = _positional_embeddings_module(model)
            if pos_module is None:
                residual = embed
                shortformer_pos_embed = None
            else:
                pos_embed = _call_position_embedding_module(
                    pos_module,
                    tokens,
                    pos_offset=pos_offset,
                    attention_mask=attention_mask,
                    device=resolved_device,
                )
                residual = _add_tensor_like_values(embed, pos_embed)
                shortformer_pos_embed = None
        elif position_type == "shortformer":
            pos_module = _positional_embeddings_module(model)
            if pos_module is None:
                raise NotImplementedError(
                    "SafeLens cannot compute shortformer positional embeddings without "
                    "a resolvable positional embedding module."
                )
            shortformer_pos_embed = _call_position_embedding_module(
                pos_module,
                tokens,
                pos_offset=pos_offset,
                attention_mask=attention_mask,
                device=resolved_device,
            )
            residual = embed
        elif position_type in {"rotary", "alibi", None}:
            residual = embed
            shortformer_pos_embed = None
        else:
            raise ValueError(f"Invalid positional_embedding_type {position_type!r}.")

        if return_shortformer_pos_embed:
            return residual, shortformer_pos_embed
        return residual

    def input_to_embed(
        self,
        input: Any,
        prepend_bos: bool | None = None,
        padding_side: str | None = None,
        truncate: bool | None = None,
        attention_mask: Any | None = None,
        past_kv_cache: Any | None = None,
    ) -> tuple[Any, Any, Any | None, Any | None]:
        """Convert token/text input to TL-style `(residual, tokens, pos_embed, mask)`."""
        model = self._require_model()
        if isinstance(input, Mapping):
            if prepend_bos is None and "prepend_bos" in input:
                prepend_bos = input["prepend_bos"]
            if padding_side is None and "padding_side" in input:
                padding_side = input["padding_side"]
            if truncate is None and "truncate" in input:
                truncate = input["truncate"]
            if attention_mask is None and "attention_mask" in input:
                attention_mask = input["attention_mask"]
            if "input_ids" in input:
                input = input["input_ids"]
            elif "tokens" in input:
                input = input["tokens"]
            elif "token_ids" in input:
                input = input["token_ids"]
            else:
                text = _text_or_prompt_value(input)
                if text is not None:
                    input = text
        if isinstance(input, str) or _is_text_batch(input):
            resolved_truncate = True if truncate is None else bool(truncate)
            tokens = self.to_tokens(
                input,
                prepend_bos=prepend_bos,
                padding_side=padding_side,
                truncate=resolved_truncate,
            )
        else:
            tokens = input
        tokens = _coerce_token_model_input(_ensure_token_batch_dim(tokens), device=self.device)

        if attention_mask is None:
            effective_padding_side = str(
                padding_side or getattr(self.tokenizer, "padding_side", "right")
            )
            needs_mask = effective_padding_side == "left" or past_kv_cache is not None
            if needs_mask and self.tokenizer is not None:
                resolved_prepend_bos = _resolve_default_prepend_bos(self, prepend_bos)
                attention_mask = _attention_mask_from_tokens(
                    tokens,
                    _tokenizer_effective_pad_token_id(self.tokenizer),
                    prepend_bos=resolved_prepend_bos,
                    padding_side=effective_padding_side,
                    bos_token_id=getattr(self.tokenizer, "bos_token_id", None),
                )
        if attention_mask is not None:
            attention_mask = _coerce_token_model_input(
                _ensure_token_batch_dim(attention_mask),
                device=self.device,
            )
            if _shape_of_token_ids(attention_mask) != _shape_of_token_ids(tokens):
                raise AssertionError(
                    f"Attention mask shape {_shape_of_token_ids(attention_mask)!r} "
                    f"does not match tokens shape {_shape_of_token_ids(tokens)!r}."
                )
            append_attention_mask = getattr(past_kv_cache, "append_attention_mask", None)
            if callable(append_attention_mask):
                attention_mask = append_attention_mask(attention_mask)
            elif past_kv_cache is not None:
                attention_mask = _extend_attention_mask_for_past_cache(
                    attention_mask, past_kv_cache
                )

        pos_offset = self.get_pos_offset(past_kv_cache, _token_batch_size(tokens))
        embed_module = _input_embeddings_module(model)
        if embed_module is None:
            raise RuntimeError("Could not resolve an input embedding module.")
        embed = embed_module(tokens)
        residual, shortformer_pos_embed = self.get_residual(
            embed,
            pos_offset,
            prepend_bos=prepend_bos,
            attention_mask=attention_mask,
            tokens=tokens,
            return_shortformer_pos_embed=True,
            device=self.device,
        )
        return residual, tokens, shortformer_pos_embed, attention_mask

    def set_tokenizer(self, tokenizer: Any, default_padding_side: str | None = None) -> None:
        """Set the tokenizer used by TransformerLens-style token helpers."""
        if default_padding_side not in {"right", "left", None}:
            raise AssertionError(
                f"padding_side must be 'right', 'left' or None, got {default_padding_side!r}"
            )
        self.tokenizer = tokenizer
        if default_padding_side is not None:
            _set_attr_if_possible(tokenizer, "padding_side", default_padding_side)
        elif getattr(tokenizer, "padding_side", None) is None:
            _set_attr_if_possible(tokenizer, "padding_side", "right")

        eos_token = getattr(tokenizer, "eos_token", None)
        if eos_token is None:
            eos_token = "<|endoftext|>"
            _set_attr_if_possible(tokenizer, "eos_token", eos_token)
        if getattr(tokenizer, "pad_token", None) is None:
            _set_attr_if_possible(tokenizer, "pad_token", eos_token)
        if getattr(tokenizer, "bos_token", None) is None:
            _set_attr_if_possible(tokenizer, "bos_token", eos_token)
        eos_token_id = getattr(tokenizer, "eos_token_id", None)
        if getattr(tokenizer, "pad_token_id", None) is None and eos_token_id is not None:
            _set_attr_if_possible(tokenizer, "pad_token_id", eos_token_id)
        if getattr(tokenizer, "bos_token_id", None) is None and eos_token_id is not None:
            _set_attr_if_possible(tokenizer, "bos_token_id", eos_token_id)
        self.tokenizer_prepends_bos = _tokenizer_prepends_bos(tokenizer)

    def to(self, device_or_dtype: Any, print_details: bool = True) -> HuggingFaceModelWrapper:
        """Move the underlying model or change dtype, returning ``self`` like PyTorch/TL."""
        _ = print_details
        target = _coerce_to_target(device_or_dtype)
        to_fn = getattr(self.model, "to", None)
        if callable(to_fn):
            to_fn(target)
        _update_wrapper_device_dtype(self, device_or_dtype, target)
        return self

    def cuda(self, device: int | Any | None = None) -> HuggingFaceModelWrapper:
        if isinstance(device, int):
            return self.to(f"cuda:{device}")
        if device is None:
            return self.to("cuda")
        return self.to(device)

    def cpu(self) -> HuggingFaceModelWrapper:
        return self.to("cpu")

    def mps(self) -> HuggingFaceModelWrapper:
        return self.to("mps")

    def move_model_modules_to_device(self) -> HuggingFaceModelWrapper:
        """Compatibility no-op unless a wrapper device has been set."""
        if self.device is not None:
            return self.to(self.device)
        return self

    def init_weights(self) -> None:
        """Unsupported HookedTransformer weight-initialization helper."""
        raise NotImplementedError(
            "SafeLens wraps pretrained Transformers modules and does not initialize "
            "HookedTransformer-format weights."
        )

    def load_and_process_state_dict(self, *args: Any, **kwargs: Any) -> None:
        """Unsupported HookedTransformer weight-processing helper."""
        _ = args, kwargs
        raise NotImplementedError(
            "SafeLens' dependency-free wrapper does not load or process "
            "HookedTransformer-format state dictionaries."
        )

    def fill_missing_keys(self, *args: Any, **kwargs: Any) -> None:
        """Unsupported HookedTransformer state-dict helper."""
        _ = args, kwargs
        raise NotImplementedError(
            "SafeLens' dependency-free wrapper does not mutate HookedTransformer-format "
            "state dictionaries."
        )

    def fold_layer_norm(self, *args: Any, **kwargs: Any) -> HuggingFaceModelWrapper:
        """Fold LayerNorm/RMSNorm affine parameters into reader weights in place."""
        _ = args
        fold_biases_override = kwargs.pop("fold_biases", None)
        center_weights_override = kwargs.pop("center_weights", None)
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"Unexpected fold_layer_norm keyword argument(s): {unexpected}.")
        model = self._require_model()
        normalization_type = self.cfg.normalization_type or "LN"
        is_rms_norm = normalization_type in {"RMS", "RMSPre"}
        fold_biases = (
            (not is_rms_norm) if fold_biases_override is None else bool(fold_biases_override)
        )
        center_weights = (
            (not is_rms_norm) if center_weights_override is None else bool(center_weights_override)
        )
        _fold_layer_norm_weights_in_model(
            model,
            model_name=self.name,
            fold_biases=fold_biases,
            center_weights=center_weights,
            rmsnorm_uses_offset=self.cfg.rmsnorm_uses_offset,
        )
        return self

    def center_writing_weights(self, *args: Any, **kwargs: Any) -> HuggingFaceModelWrapper:
        """Center weights and biases that write directly to the residual stream."""
        _ = args, kwargs
        model = self._require_model()
        if _is_olmo2_post_norm_model(model):
            return self
        config = getattr(model, "config", None)
        _center_module_weight(_input_embeddings_module(model), axis=-1)
        try:
            positional_embeddings = _positional_embeddings_module(model)
        except KeyError:
            positional_embeddings = None
        if positional_embeddings is not None:
            _center_module_weight(positional_embeddings, axis=-1)

        native_w_o = getattr(model, "W_O", None)
        if native_w_o is not None:
            model.W_O = _center_residual_stream_weight(native_w_o, d_model=self.cfg.d_model)
        native_b_o = getattr(model, "b_O", None)
        if native_b_o is not None:
            model.b_O = _center_residual_stream_bias(native_b_o)
        native_w_out = getattr(model, "W_out", None)
        if native_w_out is not None:
            model.W_out = _center_residual_stream_weight(native_w_out, d_model=self.cfg.d_model)
        native_b_out = getattr(model, "b_out", None)
        if native_b_out is not None:
            model.b_out = _center_residual_stream_bias(native_b_out)

        adapter = architecture_adapter_for_model(model, model_name=self.name)
        for layer in range(_infer_model_layers(model)):
            try:
                attention_ref = adapter.parse_component_ref(
                    transformer_lens_component_name("z", layer)
                )
                if attention_ref is not None:
                    attention_module = adapter.get_component(model, attention_ref)
                    _center_attention_output_module(
                        attention_module,
                        architecture=adapter.name,
                    )
            except (KeyError, NotImplementedError, ValueError):
                pass
            if _config_attr(config, "attn_only", False):
                continue
            try:
                mlp_ref = adapter.parse_component_ref(
                    transformer_lens_component_name("post", layer)
                )
                if mlp_ref is not None:
                    mlp_module = adapter.get_component(model, mlp_ref)
                    _center_mlp_output_module(mlp_module, d_model=self.cfg.d_model)
            except (KeyError, NotImplementedError, ValueError):
                pass
        return self

    def center_unembed(self, *args: Any, **kwargs: Any) -> HuggingFaceModelWrapper:
        """Center unembedding directions, matching TransformerLens weight processing."""
        _ = args, kwargs
        model = self._require_model()
        native_weight = getattr(model, "W_U", None)
        if native_weight is not None:
            centered = _center_unembed_weight(native_weight, weight_layout="d_model_vocab")
            try:
                model.W_U = centered
            except Exception as exc:
                raise RuntimeError("Could not update native TransformerLens W_U.") from exc
            native_bias = getattr(model, "b_U", None)
            if native_bias is not None:
                try:
                    model.b_U = _center_bias_like(native_bias)
                except Exception as exc:
                    raise RuntimeError("Could not update native TransformerLens b_U.") from exc
            return self

        embeddings = self._output_embeddings()
        weight = getattr(embeddings, "weight", None)
        if weight is None:
            raise RuntimeError("Could not find unembedding weights to center.")
        centered = _center_unembed_weight(weight, weight_layout="vocab_d_model")
        updated = False
        try:
            embeddings.weight = centered
            updated = True
        except Exception as exc:
            data = getattr(weight, "data", None)
            if data is None:
                raise RuntimeError("Could not update output embedding weight.") from exc
            data.copy_(centered)
            updated = True
        if updated and hasattr(model, "_weight"):
            try:
                model._weight = centered
            except Exception:
                pass
        bias = getattr(embeddings, "bias", None)
        if bias is not None:
            centered_bias = _center_bias_like(bias)
            _set_module_bias(embeddings, centered_bias)
            if hasattr(model, "_bias"):
                try:
                    model._bias = centered_bias
                except Exception:
                    pass
        return self

    def fold_value_biases(self, *args: Any, **kwargs: Any) -> HuggingFaceModelWrapper:
        """Fold attention value biases into output biases and clear value biases."""
        _ = args, kwargs
        model = self._require_model()
        native_b_v = getattr(model, "b_V", None)
        native_w_o = getattr(model, "W_O", None)
        if native_b_v is not None and native_w_o is not None:
            native_b_o = getattr(model, "b_O", None)
            folded_bias, zero_b_v = _fold_value_bias_tensor_like(
                native_b_v,
                native_w_o,
                native_b_o,
                target_heads=self.cfg.n_heads,
            )
            model.b_O = folded_bias
            model.b_V = zero_b_v

        adapter = architecture_adapter_for_model(model, model_name=self.name)
        for layer in range(_infer_model_layers(model)):
            try:
                value_ref = adapter.parse_component_ref(transformer_lens_component_name("v", layer))
                output_ref = adapter.parse_component_ref(
                    transformer_lens_component_name("z", layer)
                )
                if value_ref is None or output_ref is None:
                    continue
                value_spec = adapter._spec_for_ref(value_ref, for_cache=True)
                value_module = adapter.get_component(model, value_ref)
                output_module = adapter.get_component(model, output_ref)
                _fold_value_bias_modules(
                    model,
                    value_module=value_module,
                    output_module=output_module,
                    value_spec=value_spec,
                    architecture=adapter.name,
                )
            except (KeyError, NotImplementedError, ValueError):
                pass
        return self

    def refactor_factored_attn_matrices(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> HuggingFaceModelWrapper:
        """Refactor native attention QK/OV matrices into SVD-based factorizations."""
        _ = args, kwargs
        model = self._require_model()
        if _uses_rotary_embeddings(model):
            raise AssertionError(
                "You can't refactor the QK circuit when using rotary embeddings "
                "(the QK matrix depends on query/key position)."
            )
        refactored = False
        native_w_q = getattr(model, "W_Q", None)
        native_w_k = getattr(model, "W_K", None)
        if native_w_q is not None and native_w_k is not None:
            native_b_q = getattr(model, "b_Q", None)
            native_b_k = getattr(model, "b_K", None)
            refactored_w_q, refactored_b_q, refactored_w_k, refactored_b_k = _refactor_qk_matrices(
                native_w_q,
                native_b_q,
                native_w_k,
                native_b_k,
            )
            model.W_Q = refactored_w_q
            model.W_K = refactored_w_k
            if native_b_q is not None:
                model.b_Q = refactored_b_q
            if native_b_k is not None:
                model.b_K = refactored_b_k
            refactored = True
        native_w_v = getattr(model, "W_V", None)
        native_w_o = getattr(model, "W_O", None)
        if native_w_v is not None and native_w_o is not None:
            native_b_v = getattr(model, "b_V", None)
            if native_b_v is not None:
                native_b_o = getattr(model, "b_O", None)
                folded_bias, zero_b_v = _fold_value_bias_tensor_like(
                    native_b_v,
                    native_w_o,
                    native_b_o,
                    target_heads=self.cfg.n_heads,
                )
                model.b_O = folded_bias
                model.b_V = zero_b_v
            refactored_w_v, refactored_w_o = _refactor_ov_matrices(native_w_v, native_w_o)
            model.W_V = refactored_w_v
            model.W_O = refactored_w_o
            refactored = True
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        for layer in range(_infer_model_layers(model)):
            if _refactor_split_attention_layer(model, adapter=adapter, layer=layer):
                refactored = True
            elif _refactor_joint_qkv_attention_layer(model, adapter=adapter, layer=layer):
                refactored = True
        if not refactored:
            raise NotImplementedError(
                "refactor_factored_attn_matrices currently requires native TL-shaped "
                "W_Q/W_K or W_V/W_O attributes, HF split q/k/v/o projection modules, "
                "or joint QKV projection modules with matching query/key/value head counts. "
                "Grouped-query refactor writeback for this experimental TL pass is not "
                "implemented yet."
            )
        return self

    def process_weights_(
        self,
        fold_ln: bool = True,
        center_writing_weights: bool = True,
        center_unembed: bool = True,
        fold_value_biases: bool = True,
        refactor_factored_attn_matrices: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> HuggingFaceModelWrapper:
        """Run supported in-place TransformerLens-style weight processing passes."""
        _ = args
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"Unexpected process_weights_ keyword argument(s): {unexpected}.")
        model = self._require_model()
        has_shortformer_positional_embeddings = (
            _infer_positional_embedding_type(model) == "shortformer"
        )
        has_olmo2_post_norm = _is_olmo2_post_norm_model(model)
        center_writing_weights_by_default = _can_center_writing_weights_by_default(model)
        should_center_writing_weights = (
            center_writing_weights
            and not has_shortformer_positional_embeddings
            and not has_olmo2_post_norm
            and center_writing_weights_by_default
        )
        if fold_ln and not has_shortformer_positional_embeddings and not has_olmo2_post_norm:
            self.fold_layer_norm()
        if should_center_writing_weights:
            self.center_writing_weights()
        if (
            center_unembed
            and not has_shortformer_positional_embeddings
            and not _has_output_logits_soft_cap(model)
            and self._transformer_lens_model_kind() not in {"encoder", "audio_encoder"}
        ):
            self.center_unembed()
        if fold_value_biases:
            self.fold_value_biases()
            if should_center_writing_weights:
                self._center_attention_output_biases_after_value_folding()
        if refactor_factored_attn_matrices:
            self.refactor_factored_attn_matrices()
        return self

    def _center_attention_output_biases_after_value_folding(self) -> None:
        model = self._require_model()
        native_b_o = getattr(model, "b_O", None)
        if native_b_o is not None:
            model.b_O = _center_residual_stream_bias(native_b_o)

        adapter = architecture_adapter_for_model(model, model_name=self.name)
        for layer in range(_infer_model_layers(model)):
            try:
                attention_ref = adapter.parse_component_ref(
                    transformer_lens_component_name("z", layer)
                )
                if attention_ref is None:
                    continue
                attention_module = adapter.get_component(model, attention_ref)
                _center_module_bias(attention_module)
            except (KeyError, NotImplementedError, ValueError):
                continue

    def load_sample_training_dataset(self, *args: Any, **kwargs: Any) -> None:
        """Store an empty sample dataset placeholder for TL notebook compatibility."""
        _ = args, kwargs
        self.dataset = []

    def sample_datapoint(self, *args: Any, **kwargs: Any) -> Any:
        """Return one datapoint from a previously loaded sample dataset."""
        _ = args, kwargs
        dataset = getattr(self, "dataset", None)
        if not dataset:
            raise ValueError("No sample training dataset is loaded.")
        try:
            import random

            return random.choice(dataset)
        except Exception:
            return dataset[0]

    def parameters(self, *args: Any, **kwargs: Any) -> Any:
        """Proxy parameter iteration to the wrapped model when available."""
        model = self._require_model()
        parameters = getattr(model, "parameters", None)
        if callable(parameters):
            return parameters(*args, **kwargs)
        return iter(())

    def named_parameters(self, *args: Any, **kwargs: Any) -> Any:
        """Proxy named parameter iteration to the wrapped model when available."""
        model = self._require_model()
        named_parameters = getattr(model, "named_parameters", None)
        if callable(named_parameters):
            return named_parameters(*args, **kwargs)
        return iter(())

    @property
    def n_params_total(self) -> int:
        """Return the wrapped model's total parameter count."""
        model = self._require_model()
        num_parameters = getattr(model, "num_parameters", None)
        if callable(num_parameters):
            try:
                return int(num_parameters())
            except TypeError:
                pass
        return sum(_parameter_numel(parameter) for parameter in self.parameters())

    @property
    def W_U(self) -> Any:
        """Return an unembedding matrix shaped `[d_model, vocab]` when available."""
        weight = self._output_embedding_weight()
        return transpose_2d_weight(weight)

    @property
    def b_U(self) -> Any:
        """Return unembedding bias shaped `[vocab]` when available, else zeros."""
        embeddings = self._output_embeddings()
        bias = getattr(embeddings, "bias", None)
        if bias is not None:
            return bias
        model = self._require_model()
        bias = getattr(model, "b_U", None)
        if bias is not None:
            return bias
        return zeros_like_last_dim(self._output_embedding_weight(), axis=0)

    @property
    def W_E(self) -> Any:
        """Return token embedding weights shaped `[vocab, d_model]`."""
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        return adapter.get_embedding_weight(model)

    @property
    def W_pos(self) -> Any:
        """Return positional embedding weights when available."""
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        return adapter.get_embedding_weight(model, positional=True)

    @property
    def W_E_pos(self) -> Any:
        """Return concatenated token and positional embeddings."""
        return _concat_first_dim(self.W_E, self.W_pos)

    @property
    def W_Q(self) -> Any:
        """Return query weights shaped `[layer, head, d_model, d_head]`."""
        return self._stack_attention_weights("q")

    @property
    def W_K(self) -> Any:
        """Return key weights shaped `[layer, head, d_model, d_head]`."""
        return self._stack_attention_weights("k")

    @property
    def W_V(self) -> Any:
        """Return value weights shaped `[layer, head, d_model, d_head]`."""
        return self._stack_attention_weights("v")

    @property
    def W_O(self) -> Any:
        """Return output weights shaped `[layer, head, d_head, d_model]`."""
        return self._stack_attention_weights("z")

    @property
    def b_Q(self) -> Any:
        """Return query biases shaped `[layer, head, d_head]`."""
        return self._stack_attention_biases("q")

    @property
    def b_K(self) -> Any:
        """Return key biases shaped `[layer, head, d_head]`."""
        return self._stack_attention_biases("k")

    @property
    def b_V(self) -> Any:
        """Return value biases shaped `[layer, head, d_head]`."""
        return self._stack_attention_biases("v")

    @property
    def b_O(self) -> Any:
        """Return attention output biases shaped `[layer, d_model]`."""
        return self._stack_attention_biases("z")

    @property
    def QK(self) -> FactoredMatrix:
        """Return the TransformerLens-style QK circuit as a factored matrix."""
        w_q = self.W_Q
        w_k = _repeat_key_value_heads_to_query_heads(
            self.W_K,
            target_heads=_stacked_attention_head_count(w_q),
            tensor_name="W_K",
        )
        return FactoredMatrix(w_q, transpose(w_k))

    @property
    def OV(self) -> FactoredMatrix:
        """Return the TransformerLens-style OV circuit as a factored matrix."""
        w_o = self.W_O
        w_v = _repeat_key_value_heads_to_query_heads(
            self.W_V,
            target_heads=_stacked_attention_head_count(w_o),
            tensor_name="W_V",
        )
        return FactoredMatrix(w_v, w_o)

    @property
    def W_U_U(self) -> Any:
        """Return the left singular vectors of the unembedding matrix."""
        return _svd_component(self.W_U, "U")

    @property
    def W_U_S(self) -> Any:
        """Return the singular values of the unembedding matrix."""
        return _svd_component(self.W_U, "S")

    @property
    def W_U_V(self) -> Any:
        """Return the right singular vectors of the unembedding matrix."""
        return _svd_component(self.W_U, "V")

    @property
    def W_in(self) -> Any:
        """Return MLP input weights shaped `[layer, d_model, d_mlp]`."""
        return self._stack_mlp_weights("in")

    @property
    def W_gate(self) -> Any:
        """Return gated-MLP gate weights shaped `[layer, d_model, d_mlp]`."""
        return self._stack_mlp_weights("gate")

    @property
    def W_out(self) -> Any:
        """Return MLP output weights shaped `[layer, d_mlp, d_model]`."""
        return self._stack_mlp_weights("out")

    @property
    def b_in(self) -> Any:
        """Return MLP input biases shaped `[layer, d_mlp]`."""
        return self._stack_mlp_biases("in")

    @property
    def b_out(self) -> Any:
        """Return MLP output biases shaped `[layer, d_model]`."""
        return self._stack_mlp_biases("out")

    def tl_parameters(self) -> dict[str, Any]:
        """Return a TransformerLens-style parameter mapping for analysis helpers."""
        parameters: dict[str, Any] = {}
        try:
            parameters["embed.W_E"] = self.W_E
        except KeyError:
            pass
        try:
            parameters["unembed.W_U"] = self.W_U
            parameters["unembed.b_U"] = self.b_U
        except RuntimeError:
            pass
        try:
            parameters["pos_embed.W_pos"] = self.W_pos
        except KeyError:
            pass

        cfg = self.cfg
        n_layers = int(cfg.n_layers or 0)
        stacked: dict[str, Any] = {}
        for template, getter in (
            ("blocks.{layer}.attn.W_Q", lambda: self.W_Q),
            ("blocks.{layer}.attn.W_K", lambda: self.W_K),
            ("blocks.{layer}.attn.W_V", lambda: self.W_V),
            ("blocks.{layer}.attn.W_O", lambda: self.W_O),
            ("blocks.{layer}.attn.b_Q", lambda: self.b_Q),
            ("blocks.{layer}.attn.b_K", lambda: self.b_K),
            ("blocks.{layer}.attn.b_V", lambda: self.b_V),
            ("blocks.{layer}.attn.b_O", lambda: self.b_O),
        ):
            try:
                stacked[template] = getter()
            except (KeyError, RuntimeError, ValueError):
                pass
        try:
            stacked.update(
                {
                    "blocks.{layer}.mlp.W_in": self.W_in,
                    "blocks.{layer}.mlp.W_out": self.W_out,
                    "blocks.{layer}.mlp.b_in": self.b_in,
                    "blocks.{layer}.mlp.b_out": self.b_out,
                }
            )
        except (KeyError, RuntimeError, ValueError):
            pass
        try:
            stacked["blocks.{layer}.mlp.W_gate"] = self.W_gate
        except (KeyError, RuntimeError, ValueError):
            pass
        for template, value in stacked.items():
            for layer_index in range(min(n_layers, _stack_first_dim(value))):
                parameters[template.format(layer=layer_index)] = value[layer_index]
        try:
            parameters.update(self._layer_norm_parameters())
        except (KeyError, RuntimeError, ValueError, NotImplementedError):
            pass
        return parameters

    def _layer_norm_parameters(self) -> dict[str, Any]:
        """Return TransformerLens-style per-layer norm affine weights when present."""
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        n_layers = int(self.cfg.n_layers or 0)
        norm_parameters: dict[str, Any] = {}
        for component, norm_name in (("ln1_scale", "ln1"), ("ln2_scale", "ln2")):
            for layer_index in range(n_layers):
                try:
                    norm_module = _norm_module_for_layer(
                        model,
                        adapter=adapter,
                        layer=layer_index,
                        component=component,
                    )
                except (KeyError, NotImplementedError, ValueError, AttributeError, IndexError):
                    continue
                weight = _norm_affine_weight(
                    norm_module,
                    rmsnorm_uses_offset=self.cfg.rmsnorm_uses_offset,
                )
                if weight is not None:
                    norm_parameters[f"blocks.{layer_index}.{norm_name}.w"] = weight
        return norm_parameters

    def accumulated_bias(
        self,
        layer: int,
        mlp_input: bool = False,
        include_mlp_biases: bool = True,
    ) -> Any:
        """Return accumulated attention/MLP output biases before a layer."""
        b_o = self.b_O
        n_layers = _stack_first_dim(b_o)
        if layer < 0 or layer > n_layers:
            raise ValueError(f"layer must be between 0 and {n_layers}, got {layer}.")

        accumulated = zeros_like_last_dim(b_o, axis=-1)
        b_out = self.b_out if include_mlp_biases else None
        for layer_index in range(layer):
            accumulated = _add_tensor_like_values(accumulated, b_o[layer_index])
            if b_out is not None:
                accumulated = _add_tensor_like_values(accumulated, b_out[layer_index])
        if mlp_input:
            assert layer < n_layers, "Cannot include attn_bias from beyond the final layer"
            accumulated = _add_tensor_like_values(accumulated, b_o[layer])
        return accumulated

    def all_composition_scores(self, mode: str) -> Any:
        """Return all TransformerLens-style head composition scores."""
        left = self.OV
        if mode == "Q":
            right = self.QK
        elif mode == "K":
            right = self.QK.T
        elif mode == "V":
            right = self.OV
        else:
            raise ValueError(f"mode must be one of ['Q', 'K', 'V'] not {mode}")

        scores = composition_scores(left, right, broadcast_dims=True)
        return _mask_composition_scores_to_future_layers(scores)

    def all_head_labels(self) -> list[str]:
        """Return TransformerLens-style labels for all attention heads."""
        weight_shape = shape_of(self.W_Q)
        if len(weight_shape) < 2:
            raise ValueError(f"Could not infer layer/head counts from W_Q shape {weight_shape}.")
        n_layers, n_heads = int(weight_shape[0]), int(weight_shape[1])
        return [f"L{layer}H{head}" for layer in range(n_layers) for head in range(n_heads)]

    def load_model(self) -> Any:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "HuggingFaceModelWrapper requires model dependencies. "
                "Install them with `pip install -e '.[models]'`."
            ) from exc

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
            "auto": "auto",
        }
        torch_dtype = dtype_map.get(self.dtype, self.dtype)
        pretrained_path = self._resolve_pretrained_path()
        pretrained_kwargs = self._pretrained_kwargs()

        self.tokenizer = self._load_text_tokenizer(
            AutoTokenizer,
            pretrained_path,
            pretrained_kwargs,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            pretrained_path,
            torch_dtype=torch_dtype,
            trust_remote_code=self.trust_remote_code,
            **pretrained_kwargs,
            **self.load_kwargs,
        )
        if self.device is not None:
            self.model.to(self.device)
        self.model.eval()
        return self.model

    @classmethod
    def from_pretrained(cls, model_name: str, **kwargs: Any) -> HuggingFaceModelWrapper:
        """Build and load a wrapper from a pretrained Transformers model id/path."""
        wrapper = cls(
            name=model_name,
            dtype=str(kwargs.pop("dtype", "float32")),
            device=kwargs.pop("device", None),
            revision=kwargs.pop("revision", None),
            cache_dir=kwargs.pop("cache_dir", None),
            trust_remote_code=bool(kwargs.pop("trust_remote_code", False)),
            load_kwargs=dict(kwargs.pop("load_kwargs", {})),
            tokenizer_kwargs=dict(kwargs.pop("tokenizer_kwargs", {})),
            pretrained_path=kwargs.pop("pretrained_path", None),
        )
        wrapper.load_kwargs.update(kwargs)
        wrapper.load_model()
        return wrapper

    @classmethod
    def from_pretrained_no_processing(
        cls,
        model_name: str,
        **kwargs: Any,
    ) -> HuggingFaceModelWrapper:
        """Alias for ``from_pretrained``; SafeLens does not apply TL weight processing."""
        return cls.from_pretrained(model_name, **kwargs)

    def _resolve_pretrained_path(self) -> str:
        return self.pretrained_path or self.name

    def _pretrained_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.revision is not None:
            kwargs["revision"] = self.revision
        if self.cache_dir is not None:
            kwargs["cache_dir"] = self.cache_dir
        return kwargs

    def _load_text_tokenizer(
        self,
        tokenizer_cls: Any,
        pretrained_path: str,
        pretrained_kwargs: dict[str, Any],
    ) -> Any | None:
        try:
            tokenizer = tokenizer_cls.from_pretrained(
                pretrained_path,
                trust_remote_code=self.trust_remote_code,
                **pretrained_kwargs,
                **self.tokenizer_kwargs,
            )
        except Exception as exc:
            self._tokenizer_load_error = exc
            return None
        self._tokenizer_load_error = None
        return tokenizer

    def add_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn | None = None,
        *,
        hook: HookFn | None = None,
        dir: str = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
    ) -> Any:
        """Register a TransformerLens-style hook on a component or module."""
        resolved_hook = _resolve_hook_argument(hook_fn, hook=hook)
        if dir == "fwd":
            return self._add_managed_hook(
                layer,
                resolved_hook,
                is_permanent=is_permanent,
                level=level,
                prepend=prepend,
            )
        if dir == "bwd":
            return self._add_managed_backward_hook(
                layer,
                resolved_hook,
                is_permanent=is_permanent,
                level=level,
                prepend=prepend,
            )
        raise ValueError(f"Invalid hook direction {dir!r}.")

    def add_perma_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn | None = None,
        *,
        hook: HookFn | None = None,
        dir: str = "fwd",
    ) -> Any:
        """Register a TransformerLens-style permanent hook."""
        return self.add_hook(layer, hook_fn, hook=hook, dir=dir, is_permanent=True)

    def _add_managed_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
    ) -> _ManagedWrapperHookHandle:
        if callable(layer) and not isinstance(layer, str):
            handles: list[Any] = []
            try:
                for expanded_layer, _hook_fn in self._expand_hook_specs(((layer, hook_fn),)):
                    handles.append(self._register_hook(expanded_layer, hook_fn, prepend=prepend))
            except Exception:
                _remove_wrapper_handles(handles)
                raise
            if not handles:
                return self._track_hook_handle(
                    _CompositeWrapperHookHandle(()),
                    is_permanent=is_permanent,
                    level=level,
                )
            handle: Any = _CompositeWrapperHookHandle(handles)
        else:
            handle = self._register_hook(layer, hook_fn, prepend=prepend)
        managed_handle = self._track_hook_handle(
            handle,
            is_permanent=is_permanent,
            level=level,
        )
        self._hooks.append(managed_handle)
        return managed_handle

    def _add_managed_backward_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
    ) -> _ManagedWrapperHookHandle:
        if callable(layer) and not isinstance(layer, str):
            handles: list[Any] = []
            try:
                for expanded_layer, _hook_fn in self._expand_hook_specs(((layer, hook_fn),)):
                    handles.append(
                        self._register_backward_hook(expanded_layer, hook_fn, prepend=prepend)
                    )
            except Exception:
                _remove_wrapper_handles(handles)
                raise
            if not handles:
                return self._track_hook_handle(
                    _CompositeWrapperHookHandle(()),
                    is_permanent=is_permanent,
                    level=level,
                )
            handle: Any = _CompositeWrapperHookHandle(handles)
        else:
            handle = self._register_backward_hook(layer, hook_fn, prepend=prepend)
        managed_handle = self._track_hook_handle(
            handle,
            is_permanent=is_permanent,
            level=level,
        )
        self._hooks.append(managed_handle)
        return managed_handle

    def __call__(
        self,
        batch: Any,
        *forward_args: Any,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
        **kwargs: Any,
    ) -> Any:
        """Run the wrapped model directly, returning logits by default like TransformerLens."""
        call_kwargs = _merge_transformer_lens_forward_positionals(
            forward_args,
            kwargs,
            return_type=return_type,
            default_return_type="logits",
        )
        resolved_call_return_type = call_kwargs.pop("return_type", "logits")
        loss_per_token = bool(call_kwargs.pop("loss_per_token", False))
        forward_keys = {
            "prepend_bos",
            "padding_side",
            "truncate",
            "start_at_layer",
            "tokens",
            "shortformer_pos_embed",
            "attention_mask",
            "stop_at_layer",
            "past_kv_cache",
        }
        forward_kwargs = {
            key: call_kwargs.pop(key) for key in list(call_kwargs) if key in forward_keys
        }
        if forward_kwargs:
            if call_kwargs:
                model_input = _merge_extra_model_kwargs(batch, call_kwargs)
            else:
                model_input = batch
            return self.forward(
                model_input,
                return_type=resolved_call_return_type,
                loss_per_token=loss_per_token,
                **forward_kwargs,
            )
        if call_kwargs:
            model_input = _merge_extra_model_kwargs(batch, call_kwargs)
        else:
            model_input = batch
        return self._run_model_forward(
            model_input,
            return_type=resolved_call_return_type,
            loss_per_token=loss_per_token,
        )

    def forward(
        self,
        input: Any,
        return_type: str | None = "logits",
        loss_per_token: bool = False,
        prepend_bos: bool | None = None,
        padding_side: str | None = None,
        truncate: bool | None = None,
        start_at_layer: int | None = None,
        tokens: Any | None = None,
        shortformer_pos_embed: Any | None = None,
        attention_mask: Any | None = None,
        stop_at_layer: int | None = None,
        past_kv_cache: Any | None = None,
    ) -> Any:
        """TransformerLens-style explicit forward method."""
        if start_at_layer is not None or stop_at_layer is not None:
            return self._run_partial_layer_forward(
                input,
                return_type=return_type,
                loss_per_token=loss_per_token,
                prepend_bos=prepend_bos,
                padding_side=padding_side,
                truncate=truncate,
                start_at_layer=start_at_layer,
                tokens=tokens,
                shortformer_pos_embed=shortformer_pos_embed,
                attention_mask=attention_mask,
                stop_at_layer=stop_at_layer,
                past_kv_cache=past_kv_cache,
            )
        if shortformer_pos_embed is not None:
            raise NotImplementedError(
                "SafeLens' Transformers wrapper does not synthesize "
                "shortformer positional embeddings."
            )
        batch = input
        extra_kwargs: dict[str, Any] = {}
        if prepend_bos is not None:
            extra_kwargs["prepend_bos"] = prepend_bos
        if padding_side is not None:
            extra_kwargs["padding_side"] = padding_side
        if truncate is not None:
            extra_kwargs["truncate"] = truncate
        if attention_mask is not None:
            extra_kwargs["attention_mask"] = attention_mask
        if tokens is not None:
            extra_kwargs["tokens"] = tokens
        if past_kv_cache is not None:
            extra_kwargs["past_kv_cache"] = past_kv_cache
        if extra_kwargs:
            batch = _merge_extra_model_kwargs(batch, extra_kwargs)
        return self._run_model_forward(
            batch,
            return_type=return_type,
            loss_per_token=loss_per_token,
        )

    def _run_partial_layer_forward(
        self,
        input: Any,
        *,
        return_type: str | None,
        loss_per_token: bool,
        prepend_bos: bool | None,
        padding_side: str | None,
        truncate: bool | None,
        start_at_layer: int | None,
        tokens: Any | None,
        shortformer_pos_embed: Any | None,
        attention_mask: Any | None,
        stop_at_layer: int | None,
        past_kv_cache: Any | None,
    ) -> Any:
        """Run a TransformerLens-style layer slice over decoder blocks."""
        model = self._require_model()
        if self._uses_decoder_text_input_semantics() is False:
            raise NotImplementedError(
                "SafeLens partial-layer forward currently supports decoder-only "
                "TransformerLens-style models."
            )
        model_cache, sync_back = _past_kv_cache_to_transformers_cache(past_kv_cache)

        if start_at_layer is None:
            residual, tokens, shortformer_pos_embed, attention_mask = self.input_to_embed(
                input,
                prepend_bos=prepend_bos,
                padding_side=padding_side,
                truncate=truncate,
                attention_mask=attention_mask,
                past_kv_cache=past_kv_cache,
            )
            start_at_layer = 0
        else:
            _assert_residual_stream_input(input)
            residual = input
            if tokens is not None:
                tokens = _coerce_token_model_input(
                    _ensure_token_batch_dim(tokens), device=self.device
                )
            if attention_mask is not None:
                attention_mask = _coerce_token_model_input(
                    _ensure_token_batch_dim(attention_mask),
                    device=self.device,
                )

        blocks = _decoder_layer_modules(model)
        indexed_blocks = list(enumerate(blocks))
        pos_offset = _past_kv_position_offset_for_partial_forward(
            past_kv_cache,
            attention_mask,
        )
        position_ids = (
            _position_ids_for_forward(
                tokens,
                attention_mask=attention_mask,
                pos_offset=pos_offset,
                device=self.device,
            )
            if tokens is not None
            else None
        )
        cache_position = (
            _cache_position_for_forward(tokens, pos_offset=pos_offset, device=self.device)
            if tokens is not None
            else None
        )

        with (
            _grad_context(enabled=self._has_active_backward_hooks()),
            _temporary_eager_attention(
                model,
                enabled=self._run_requires_output_attentions or self._attention_hook_count > 0,
            ),
        ):
            try:
                for layer_index, block in indexed_blocks[start_at_layer:stop_at_layer]:
                    residual = _call_decoder_block(
                        block,
                        residual,
                        layer_index=layer_index,
                        attention_mask=attention_mask,
                        position_ids=position_ids,
                        cache_position=cache_position,
                        past_key_values=model_cache,
                        past_kv_cache_entry=_past_kv_cache_entry_at(past_kv_cache, layer_index),
                        shortformer_pos_embed=shortformer_pos_embed,
                        output_attentions=(
                            self._run_requires_output_attentions or self._attention_hook_count > 0
                        ),
                    )
            finally:
                self._run_requires_output_attentions = False

        if sync_back is not None:
            sync_back()
        if stop_at_layer is not None:
            return residual

        final_norm = _final_norm_module(model)
        if final_norm is not None and callable(final_norm):
            residual = final_norm(residual)
        if return_type is None:
            return None
        resolved_return_type = _normalize_return_type(return_type)
        logits = _unembed_residual(model, residual)
        return _format_model_output(
            {"logits": logits},
            resolved_return_type,
            model_inputs=_loss_model_inputs_for_partial_forward(
                tokens,
                attention_mask,
                return_type=resolved_return_type,
            ),
            loss_per_token=loss_per_token,
        )

    def _bridge_past_kv_cache(
        self,
        model_inputs: dict[str, Any],
        past_kv_cache: Any,
    ) -> tuple[dict[str, Any], Callable[[Any], None] | None]:
        model_cache, sync_back = _past_kv_cache_to_transformers_cache(past_kv_cache)
        if model_cache is None:
            return model_inputs, None
        bridged_inputs = dict(model_inputs)
        bridged_inputs["past_key_values"] = model_cache
        bridged_inputs["use_cache"] = True
        if "attention_mask" in bridged_inputs:
            append_attention_mask = getattr(past_kv_cache, "append_attention_mask", None)
            if callable(append_attention_mask):
                bridged_inputs["attention_mask"] = append_attention_mask(
                    bridged_inputs["attention_mask"]
                )
            else:
                bridged_inputs["attention_mask"] = _extend_attention_mask_for_past_cache(
                    bridged_inputs["attention_mask"],
                    past_kv_cache,
                )
        return bridged_inputs, lambda output: _sync_past_kv_cache_from_model_output(
            past_kv_cache,
            model_cache,
            output,
            sync_back,
        )

    def loss_fn(
        self,
        logits: Any,
        tokens: Any,
        attention_mask: Any | None = None,
        per_token: bool = False,
    ) -> Any:
        """Compute TransformerLens-style next-token cross-entropy loss."""
        return _extract_or_compute_loss(
            {"logits": logits},
            _loss_model_inputs(tokens, attention_mask),
            logits=logits,
            loss_per_token=per_token,
        )

    def _register_hook(self, layer: LayerRef, hook_fn: HookFn, *, prepend: bool = False) -> Any:
        model = self._require_model()
        layer = self._resolve_hook_layer_ref(model, layer, for_cache=False)
        self.check_hooks_to_add(None, str(layer), hook_fn, dir="fwd", prepend=prepend)
        top_level_handle = self._try_register_top_level_hook(
            model,
            layer,
            hook_fn,
            prepend=prepend,
        )
        if top_level_handle is not None:
            return top_level_handle
        component_handle = self._try_register_component_hook(
            model,
            layer,
            hook_fn,
            prepend=prepend,
        )
        if component_handle is not None:
            return component_handle
        module = self._resolve_layer(model, layer)
        return _register_module_forward_hook(
            module,
            lambda mod, inputs, output: hook_fn(mod, inputs, output),
            prepend=prepend,
        )

    def _register_backward_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        model = self._require_model()
        layer = self._resolve_hook_layer_ref(model, layer, for_cache=False)
        self.check_hooks_to_add(None, str(layer), hook_fn, dir="bwd", prepend=prepend)
        top_level_handle = self._try_register_top_level_backward_hook(
            model,
            layer,
            hook_fn,
            prepend=prepend,
        )
        if top_level_handle is not None:
            return top_level_handle
        component_handle = self._try_register_component_backward_hook(
            model,
            layer,
            hook_fn,
            prepend=prepend,
        )
        if component_handle is not None:
            return component_handle
        module = self._resolve_layer(model, layer)
        return _register_raw_activation_backward_hook(
            module,
            hook_fn,
            hook_context=_RawHookContext(
                activation_name_for_layer(layer) if isinstance(layer, int) else str(layer)
            ),
            use_input=False,
            prepend=prepend,
        )

    def run_with_cache(
        self,
        batch: Any,
        *model_args: Any,
        layers: Sequence[LayerRef] | LayerRef | None = None,
        names_filter: NamesFilter = None,
        return_cache_object: bool | object = _DEFAULT_RETURN_CACHE_OBJECT,
        remove_batch_dim: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        cache_all: bool | object = _DEFAULT_CACHE_ALL,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
        loss_per_token: bool | object = _DEFAULT_LOSS_PER_TOKEN,
        incl_bwd: bool = False,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        **forward_kwargs: Any,
    ) -> tuple[Any, dict[str, Any] | ActivationCache]:
        model = self._require_model()
        cache = ActivationCache(model=self, has_batch_dim=not remove_batch_dim)
        temp_handles: list[Any] = []
        install_complete = False
        layers, forward_args = _split_run_with_cache_positionals(model_args, layers=layers)
        forward_options = _merge_transformer_lens_forward_positionals(
            forward_args,
            forward_kwargs,
            return_type=return_type,
            loss_per_token=loss_per_token,
        )
        forward_return_type = forward_options.pop("return_type", _DEFAULT_RETURN_TYPE)
        forward_loss_per_token = bool(forward_options.pop("loss_per_token", False))
        resolved_return_type = _resolve_return_type(batch, forward_return_type)
        resolved_cache_all = _resolve_cache_all(batch, layers, names_filter, cache_all)
        resolved_return_cache_object = _resolve_return_cache_object(batch, return_cache_object)

        try:
            self.is_caching = True
            for layer in self._cache_layers(
                model,
                layers,
                names_filter,
                cache_all=resolved_cache_all,
            ):
                temp_handles.append(
                    self._register_cache_hook(
                        model,
                        layer,
                        cache,
                        detach=detach,
                        clone=clone,
                        device=device,
                        pos_slice=pos_slice,
                        remove_batch_dim=remove_batch_dim,
                    )
                )
                if incl_bwd:
                    cache_name = self._cache_name_for_layer(model, layer, for_cache=True)
                    temp_handles.append(
                        self._register_backward_hook(
                            layer,
                            make_cache_hook(
                                cache,
                                f"{cache_name}_grad",
                                detach=detach,
                                clone=clone,
                                device=device,
                                pos_slice=pos_slice,
                                remove_batch_dim=remove_batch_dim,
                            ),
                            prepend=False,
                        )
                    )

            install_complete = True
            if forward_options:
                with self._temporary_backward_hook_context(enabled=incl_bwd):
                    output = self.forward(
                        batch,
                        return_type=resolved_return_type,
                        loss_per_token=forward_loss_per_token,
                        **forward_options,
                    )
            else:
                output = self._run_model_forward(
                    batch,
                    return_type=resolved_return_type,
                    loss_per_token=forward_loss_per_token,
                    enable_grad=incl_bwd,
                )
            if incl_bwd:
                _backward_scalar_output(output)
        finally:
            if reset_hooks_end or not install_complete:
                _remove_wrapper_handles(temp_handles)
                if clear_contexts:
                    self._clear_hook_contexts_for_handles(temp_handles)
                    self.clear_contexts()
            else:
                _keep_wrapper_handles(self, temp_handles, is_cache=True)
            self.is_caching = _wrapper_has_active_permanent_cache_hooks(self._hooks)

        return output, _format_cache_result(
            cache,
            model=self,
            return_cache_object=resolved_return_cache_object,
            remove_batch_dim=False,
        )

    def add_caching_hooks(
        self,
        names_filter: NamesFilter = None,
        *,
        layers: Sequence[LayerRef] | None = None,
        cache_all: bool | object = _DEFAULT_CACHE_ALL,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | dict[str, Any] | None = None,
    ) -> ActivationCache:
        """Install persistent forward cache hooks and return the live cache."""
        model = self._require_model()
        previous_is_caching = self.is_caching
        activation_cache = _coerce_activation_cache(
            cache,
            model=self,
            has_batch_dim=not remove_batch_dim,
        )
        previous_cache_model = activation_cache.model
        previous_has_batch_dim = activation_cache.has_batch_dim
        activation_cache.model = self
        if remove_batch_dim:
            activation_cache.has_batch_dim = False
        resolved_cache_all = True if cache_all is _DEFAULT_CACHE_ALL else bool(cache_all)
        installed_handles: list[_ManagedWrapperHookHandle] = []
        try:
            for layer in self._cache_layers(
                model,
                layers,
                names_filter,
                cache_all=resolved_cache_all,
            ):
                handle = self._register_cache_hook(
                    model,
                    layer,
                    activation_cache,
                    detach=detach,
                    clone=clone,
                    device=device,
                    pos_slice=pos_slice,
                    remove_batch_dim=remove_batch_dim,
                    is_permanent=True,
                )
                managed_handle = self._track_hook_handle(
                    handle,
                    is_permanent=True,
                    is_cache=True,
                )
                self._hooks.append(managed_handle)
                installed_handles.append(managed_handle)
                if incl_bwd:
                    cache_name = self._cache_name_for_layer(model, layer, for_cache=True)
                    bwd_handle = self._register_backward_hook(
                        layer,
                        make_cache_hook(
                            activation_cache,
                            f"{cache_name}_grad",
                            detach=detach,
                            clone=clone,
                            device=device,
                            pos_slice=pos_slice,
                            remove_batch_dim=remove_batch_dim,
                        ),
                        prepend=False,
                    )
                    managed_bwd_handle = self._track_hook_handle(
                        bwd_handle,
                        is_permanent=True,
                        is_cache=True,
                    )
                    self._hooks.append(managed_bwd_handle)
                    installed_handles.append(managed_bwd_handle)
        except Exception:
            for handle in reversed(installed_handles):
                handle.remove()
            self.is_caching = previous_is_caching
            activation_cache.model = previous_cache_model
            activation_cache.has_batch_dim = previous_has_batch_dim
            raise
        self.is_caching = True
        return activation_cache

    def cache_all(
        self,
        cache: ActivationCache | dict[str, Any] | None = None,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
    ) -> ActivationCache:
        """Permanently cache all supported component hooks until hooks are reset."""
        return self.add_caching_hooks(
            None,
            cache_all=True,
            incl_bwd=incl_bwd,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
            cache=cache,
        )

    def cache_some(
        self,
        cache_or_names_filter: ActivationCache | dict[str, Any] | NamesFilter,
        names_filter: NamesFilter = None,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | dict[str, Any] | None = None,
    ) -> ActivationCache:
        """Permanently cache hook names matching a names filter until hooks are reset."""
        if _looks_like_external_cache(cache_or_names_filter):
            if cache is not None:
                raise TypeError("Pass external cache either positionally or by keyword, not both.")
            cache = cache_or_names_filter
        else:
            if names_filter is not None:
                raise TypeError("Pass only one names filter.")
            names_filter = cache_or_names_filter
        if names_filter is None:
            raise TypeError("cache_some() missing required argument: 'names_filter' or 'names'")
        return self.add_caching_hooks(
            names_filter,
            incl_bwd=incl_bwd,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
            cache=cache,
        )

    def run_with_hooks(
        self,
        batch: Any,
        *model_args: Any,
        fwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        bwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        prepend: bool = False,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
        loss_per_token: bool | object = _DEFAULT_LOSS_PER_TOKEN,
        **forward_kwargs: Any,
    ) -> Any:
        """Run one forward pass with temporary hooks, mirroring TransformerLens."""
        bwd_hook_specs = list(bwd_hooks)
        handles: list[Any] = []
        forward_options = _merge_transformer_lens_forward_positionals(
            model_args,
            forward_kwargs,
            return_type=return_type,
            loss_per_token=loss_per_token,
        )
        forward_return_type = forward_options.pop("return_type", _DEFAULT_RETURN_TYPE)
        forward_loss_per_token = bool(forward_options.pop("loss_per_token", False))
        try:
            for layer, hook_fn in self._expand_hook_specs(fwd_hooks):
                handles.append(self._add_managed_hook(layer, hook_fn, prepend=prepend))
            for layer, hook_fn in self._expand_hook_specs(bwd_hook_specs):
                handles.append(self._add_managed_backward_hook(layer, hook_fn, prepend=prepend))
            if forward_options:
                resolved_return_type = _resolve_return_type(batch, forward_return_type)
                with self._temporary_backward_hook_context(enabled=bool(bwd_hook_specs)):
                    return self.forward(
                        batch,
                        return_type=resolved_return_type,
                        loss_per_token=forward_loss_per_token,
                        **forward_options,
                    )
            return self._run_model_forward(
                batch,
                return_type=forward_return_type,
                loss_per_token=forward_loss_per_token,
                enable_grad=bool(bwd_hook_specs),
            )
        finally:
            if reset_hooks_end:
                _remove_wrapper_handles(handles)
                if clear_contexts:
                    self._clear_hook_contexts_for_handles(handles)
                    self.clear_contexts()

    @contextmanager
    def hooks(
        self,
        fwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        bwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        *,
        prepend: bool = False,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
    ) -> Any:
        """Temporarily register hooks around arbitrary wrapper calls."""
        handles: list[Any] = []
        try:
            for layer, hook_fn in self._expand_hook_specs(fwd_hooks):
                handles.append(self._add_managed_hook(layer, hook_fn, prepend=prepend))
            for layer, hook_fn in self._expand_hook_specs(bwd_hooks):
                handles.append(self._add_managed_backward_hook(layer, hook_fn, prepend=prepend))
            yield self
        finally:
            if reset_hooks_end:
                _remove_wrapper_handles(handles)
                if clear_contexts:
                    self._clear_hook_contexts_for_handles(handles)
                    self.clear_contexts()

    def _run_model_forward(
        self,
        batch: Any,
        *,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
        loss_per_token: bool = False,
        enable_grad: bool = False,
    ) -> Any:
        """Run the wrapped model without adding temporary cache hooks."""
        model = self._require_model()
        resolved_return_type = _resolve_return_type(batch, return_type)
        model_inputs = self._prepare_model_inputs(batch)
        past_kv_cache = model_inputs.pop("past_kv_cache", None)
        cache_bridge = None
        if past_kv_cache is not None:
            model_inputs, cache_bridge = self._bridge_past_kv_cache(model_inputs, past_kv_cache)
        try:
            with (
                _grad_context(enabled=enable_grad or self._has_active_backward_hooks()),
                _temporary_eager_attention(
                    model,
                    enabled=self._run_requires_output_attentions or self._attention_hook_count > 0,
                ),
            ):
                raw_output = model(**model_inputs)
                formatted_output = _format_model_output(
                    raw_output,
                    resolved_return_type,
                    model_inputs=model_inputs,
                    loss_per_token=loss_per_token,
                )
                if cache_bridge is not None:
                    cache_bridge(raw_output)
                return formatted_output
        finally:
            self._run_requires_output_attentions = False

    def _has_active_backward_hooks(self) -> bool:
        return self._temporary_backward_hook_depth > 0 or any(
            getattr(handle, "is_backward", False) for handle in self._hooks
        )

    @contextmanager
    def _temporary_backward_hook_context(self, *, enabled: bool) -> Any:
        if not enabled:
            yield
            return
        self._temporary_backward_hook_depth += 1
        try:
            yield
        finally:
            self._temporary_backward_hook_depth = max(
                0,
                self._temporary_backward_hook_depth - 1,
            )

    def _cache_name_for_layer(
        self,
        model: Any,
        layer: LayerRef,
        *,
        for_cache: bool | None,
    ) -> str:
        resolved_layer = self._resolve_hook_layer_ref(model, layer, for_cache=for_cache)
        top_level_name = _canonical_top_level_hook_name(resolved_layer)
        if top_level_name is not None:
            return top_level_name
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        component_ref = adapter.parse_component_ref(resolved_layer)
        if component_ref is not None:
            if isinstance(resolved_layer, tuple):
                return component_ref.transformer_lens_name
            return (
                activation_name_for_layer(resolved_layer)
                if isinstance(resolved_layer, int)
                else str(resolved_layer)
            )
        return (
            activation_name_for_layer(resolved_layer)
            if isinstance(resolved_layer, int)
            else str(resolved_layer)
        )

    def _uses_encoder_decoder_generation_semantics(self) -> bool:
        model = getattr(self, "model", None)
        config = _core_model_config(_config_attr(model, "config"))
        return bool(_config_attr(config, "is_encoder_decoder", False))

    def _generation_should_append_input_embeds(self) -> bool:
        return not self._uses_encoder_decoder_generation_semantics()

    def generate(self, prompt: Any = "", **generation_kwargs: Any) -> Any:
        model = self._require_model()

        import torch

        prepend_bos = _resolve_default_prepend_bos(
            self,
            generation_kwargs.pop("prepend_bos", None),
        )
        input_is_text = isinstance(prompt, str) or _is_text_batch(prompt)
        input_is_embeds = _looks_like_input_embeds(prompt)
        default_padding_side = "left" if _is_text_batch(prompt) else None
        padding_side = generation_kwargs.pop("padding_side", default_padding_side)
        truncate = bool(generation_kwargs.pop("truncate", True))
        return_type = generation_kwargs.pop("return_type", "input")
        _normalize_transformer_lens_generation_kwargs(generation_kwargs, model=model)
        normalized_return_type = _normalize_generate_return_type(
            return_type,
            prompt=prompt,
            input_is_text=input_is_text,
            input_is_embeds=input_is_embeds,
        )
        if self.tokenizer is None and (input_is_text or normalized_return_type == "str"):
            detail = _tokenizer_error_detail(self._tokenizer_load_error)
            raise RuntimeError(
                f"Tokenizer is not loaded, so text generation is unavailable. {detail}"
            )
        if input_is_text:
            input_ids = self.to_tokens(
                prompt,
                prepend_bos=prepend_bos,
                padding_side=padding_side,
                truncate=truncate,
            )
        elif _looks_like_token_ids(prompt):
            input_ids = _ensure_token_batch_dim(prompt)
            if not isinstance(input_ids, torch.Tensor):
                input_ids = torch.as_tensor(input_ids, dtype=torch.long)
            if self.device is not None:
                to_fn = getattr(input_ids, "to", None)
                if callable(to_fn):
                    input_ids = to_fn(self.device)
        elif input_is_embeds:
            input_ids = None
            input_embeds = prompt
            if not isinstance(input_embeds, torch.Tensor):
                input_embeds = torch.as_tensor(input_embeds)
            if not torch.is_floating_point(input_embeds):
                raise TypeError(
                    "generate embedding inputs must be floating point tensors shaped "
                    "[batch, pos, hidden]."
                )
            if self.device is not None:
                input_embeds = input_embeds.to(self.device)
        else:
            raise TypeError(
                "generate input must be a text string, list of strings, token ids shaped "
                "[pos] or [batch, pos], or embeddings shaped [batch, pos, hidden]."
            )
        inputs = {"inputs_embeds": input_embeds} if input_is_embeds else {"input_ids": input_ids}
        if not input_is_embeds:
            attention_mask = _generation_attention_mask_from_tokens(
                input_ids,
                tokenizer=self.tokenizer,
                prepend_bos=prepend_bos,
                padding_side=padding_side,
            )
            if attention_mask is not None:
                inputs["attention_mask"] = attention_mask
        with torch.no_grad():
            generated_output = model.generate(**inputs, **generation_kwargs)
        output_ids = _generated_sequences(generated_output)
        if normalized_return_type == "model_output":
            return _normalize_generated_model_output(generated_output, output_ids)
        if normalized_return_type == "tokens":
            return output_ids
        if normalized_return_type == "embeds":
            output_embeds = _tokens_to_input_embeddings(model, output_ids)
            if input_is_embeds and self._generation_should_append_input_embeds():
                return _append_sequence_values(input_embeds, output_embeds)
            return output_embeds
        return _decode_generated_sequences(
            self.tokenizer,
            output_ids,
            force_batch=_is_text_batch(prompt),
        )

    def generate_stream(
        self,
        prompt: Any = "",
        *,
        max_new_tokens: int = 10,
        max_tokens_per_yield: int = 25,
        **generation_kwargs: Any,
    ) -> Iterable[Any]:
        model = self._require_model()
        if max_new_tokens < 0:
            raise ValueError("max_new_tokens must be non-negative.")
        if max_tokens_per_yield <= 0:
            raise ValueError("max_tokens_per_yield must be positive.")

        import torch

        prepend_bos = _resolve_default_prepend_bos(
            self,
            generation_kwargs.pop("prepend_bos", None),
        )
        input_is_text = isinstance(prompt, str)
        if _is_text_batch(prompt):
            raise TypeError(
                "generate_stream supports a single text string or token ids; pass token ids "
                "for batched streaming inputs."
            )
        input_is_embeds = _looks_like_input_embeds(prompt)
        padding_side = generation_kwargs.pop("padding_side", None)
        truncate = bool(generation_kwargs.pop("truncate", True))
        return_type = generation_kwargs.pop("return_type", "input")
        _normalize_transformer_lens_generation_kwargs(generation_kwargs, model=model)
        normalized_return_type = _normalize_generate_return_type(
            return_type,
            prompt=prompt,
            input_is_text=input_is_text,
            input_is_embeds=input_is_embeds,
            token_return_name="tensor",
        )
        if normalized_return_type == "model_output":
            raise ValueError("generate_stream does not support return_type='model_output'.")
        if self.tokenizer is None and (input_is_text or normalized_return_type == "str"):
            detail = _tokenizer_error_detail(self._tokenizer_load_error)
            raise RuntimeError(
                f"Tokenizer is not loaded, so streaming text generation is unavailable. {detail}"
            )

        if input_is_text:
            tokens = self.to_tokens(
                prompt,
                prepend_bos=prepend_bos,
                padding_side=padding_side,
                truncate=truncate,
            )
        elif _looks_like_token_ids(prompt):
            tokens = _ensure_token_batch_dim(prompt)
            if not isinstance(tokens, torch.Tensor):
                tokens = torch.as_tensor(tokens, dtype=torch.long)
            if self.device is not None:
                tokens = tokens.to(self.device)
        elif input_is_embeds:
            input_embeds = prompt if isinstance(prompt, torch.Tensor) else torch.as_tensor(prompt)
            if not torch.is_floating_point(input_embeds):
                raise TypeError(
                    "generate_stream embedding inputs must be floating point tensors shaped "
                    "[batch, pos, hidden]."
                )
            if self.device is not None:
                input_embeds = input_embeds.to(self.device)
            yield from self._generate_stream_from_embeds(
                model,
                input_embeds,
                max_new_tokens=max_new_tokens,
                max_tokens_per_yield=max_tokens_per_yield,
                return_type=normalized_return_type,
                generation_kwargs=generation_kwargs,
            )
            return
        else:
            raise TypeError(
                "generate_stream input must be a text string, token ids shaped [pos] or "
                "[batch, pos], or embeddings shaped [batch, pos, hidden]."
            )

        yield from self._generate_stream_from_tokens(
            model,
            tokens,
            max_new_tokens=max_new_tokens,
            max_tokens_per_yield=max_tokens_per_yield,
            return_type=normalized_return_type,
            generation_kwargs=generation_kwargs,
            text_output_is_single=input_is_text,
            padding_side=padding_side,
        )

    def _generate_stream_from_tokens(
        self,
        model: Any,
        tokens: Any,
        *,
        max_new_tokens: int,
        max_tokens_per_yield: int,
        return_type: str,
        generation_kwargs: dict[str, Any],
        text_output_is_single: bool,
        padding_side: str | None,
    ) -> Iterable[Any]:
        import torch

        if self._uses_encoder_decoder_generation_semantics():
            yield from self._generate_encoder_decoder_stream_from_tokens(
                tokens,
                max_new_tokens=max_new_tokens,
                max_tokens_per_yield=max_tokens_per_yield,
                return_type=return_type,
                generation_kwargs=generation_kwargs,
                text_output_is_single=text_output_is_single,
                padding_side=padding_side,
            )
            return

        current_tokens = tokens
        accumulated: list[Any] = []
        with torch.no_grad():
            for _index in range(max_new_tokens):
                attention_mask = _generation_attention_mask_from_tokens(
                    current_tokens,
                    tokenizer=self.tokenizer,
                    prepend_bos=False,
                    padding_side=padding_side,
                )
                step_kwargs = dict(generation_kwargs)
                if attention_mask is not None:
                    step_kwargs["attention_mask"] = attention_mask
                step_output = model.generate(
                    input_ids=current_tokens,
                    max_new_tokens=1,
                    **step_kwargs,
                )
                step_sequences = _generated_sequences(step_output)
                new_tokens = _slice_generated_suffix(step_sequences, current_tokens)
                accumulated.append(new_tokens)
                current_tokens = _append_sequence_values(current_tokens, new_tokens)
                if len(accumulated) >= max_tokens_per_yield:
                    yield self._format_stream_chunk(
                        accumulated,
                        return_type=return_type,
                        text_output_is_single=text_output_is_single,
                    )
                    accumulated = []
        if accumulated:
            yield self._format_stream_chunk(
                accumulated,
                return_type=return_type,
                text_output_is_single=text_output_is_single,
            )

    def _generate_stream_from_embeds(
        self,
        model: Any,
        input_embeds: Any,
        *,
        max_new_tokens: int,
        max_tokens_per_yield: int,
        return_type: str,
        generation_kwargs: dict[str, Any],
    ) -> Iterable[Any]:
        import torch

        if self._uses_encoder_decoder_generation_semantics():
            yield from self._generate_encoder_decoder_stream_from_embeds(
                input_embeds,
                max_new_tokens=max_new_tokens,
                max_tokens_per_yield=max_tokens_per_yield,
                return_type=return_type,
                generation_kwargs=generation_kwargs,
            )
            return

        current_embeds = input_embeds
        accumulated: list[Any] = []
        with torch.no_grad():
            for _index in range(max_new_tokens):
                step_output = model.generate(
                    inputs_embeds=current_embeds,
                    max_new_tokens=1,
                    **generation_kwargs,
                )
                step_sequences = _generated_sequences(step_output)
                new_tokens = _normalize_generated_new_tokens(step_sequences)
                accumulated.append(new_tokens)
                new_embeds = _tokens_to_input_embeddings(model, new_tokens)
                current_embeds = _append_sequence_values(current_embeds, new_embeds)
                if len(accumulated) >= max_tokens_per_yield:
                    yield self._format_stream_chunk(
                        accumulated,
                        return_type=return_type,
                        text_output_is_single=False,
                    )
                    accumulated = []
        if accumulated:
            yield self._format_stream_chunk(
                accumulated,
                return_type=return_type,
                text_output_is_single=False,
            )

    def _generate_encoder_decoder_stream_from_tokens(
        self,
        tokens: Any,
        *,
        max_new_tokens: int,
        max_tokens_per_yield: int,
        return_type: str,
        generation_kwargs: dict[str, Any],
        text_output_is_single: bool,
        padding_side: str | None,
    ) -> Iterable[Any]:
        if max_new_tokens == 0:
            return
        output_tokens = self.generate(
            tokens,
            max_new_tokens=max_new_tokens,
            return_type="tokens",
            prepend_bos=False,
            padding_side=padding_side,
            **generation_kwargs,
        )
        for chunk in _iter_generated_token_chunks(output_tokens, max_tokens_per_yield):
            yield self._format_stream_chunk(
                [chunk],
                return_type=return_type,
                text_output_is_single=text_output_is_single,
            )

    def _generate_encoder_decoder_stream_from_embeds(
        self,
        input_embeds: Any,
        *,
        max_new_tokens: int,
        max_tokens_per_yield: int,
        return_type: str,
        generation_kwargs: dict[str, Any],
    ) -> Iterable[Any]:
        if max_new_tokens == 0:
            return
        output_tokens = self.generate(
            input_embeds,
            max_new_tokens=max_new_tokens,
            return_type="tokens",
            **generation_kwargs,
        )
        for chunk in _iter_generated_token_chunks(output_tokens, max_tokens_per_yield):
            yield self._format_stream_chunk(
                [chunk],
                return_type=return_type,
                text_output_is_single=False,
            )

    def _format_stream_chunk(
        self,
        chunks: Sequence[Any],
        *,
        return_type: str,
        text_output_is_single: bool,
    ) -> Any:
        combined_tokens = _concat_token_chunks(chunks)
        if return_type == "str":
            return _decode_generated_sequences(
                self.tokenizer,
                combined_tokens,
                force_batch=not text_output_is_single,
            )
        if return_type in {"tokens", "tensor"}:
            return combined_tokens
        if return_type == "embeds":
            return _tokens_to_input_embeddings(self._require_model(), combined_tokens)
        raise ValueError(
            "generate_stream return_type must be 'input', 'str', 'tokens', or 'embeds'."
        )

    def to_tokens(
        self,
        text: str | Sequence[str],
        *,
        prepend_bos: bool | None = None,
        padding_side: str | None = None,
        move_to_device: bool = True,
        truncate: bool = True,
    ) -> Any:
        """Tokenize text into a tensor, mirroring TransformerLens' convenience method."""
        tokenizer = self._require_tokenizer_for_text("tokenization")
        prepend_bos = _resolve_default_prepend_bos(self, prepend_bos)
        token_kwargs: dict[str, Any] = {
            "return_tensors": "pt",
            "add_special_tokens": False,
            "padding": not isinstance(text, str),
        }
        with (
            _temporary_tokenizer_padding_side(tokenizer, padding_side),
            _temporary_tokenizer_pad_token(tokenizer, enabled=bool(token_kwargs["padding"])),
        ):
            effective_pad_token_id = _tokenizer_effective_pad_token_id(tokenizer)
            effective_padding_side = str(getattr(tokenizer, "padding_side", "right"))
            if truncate:
                n_ctx = _tokenization_context_length(self.model, tokenizer)
                token_kwargs["truncation"] = True
                if n_ctx is not None:
                    max_length = int(n_ctx) - (1 if prepend_bos else 0)
                    if max_length > 0:
                        token_kwargs["max_length"] = max_length
            tokenized = _call_tokenizer_with_supported_kwargs(
                tokenizer,
                text,
                token_kwargs,
            )
        tokens = tokenized["input_ids"] if isinstance(tokenized, dict) else tokenized.input_ids
        if prepend_bos:
            tokens = _prepend_bos_token(
                tokens,
                tokenizer,
                pad_token_id=effective_pad_token_id,
                padding_side=effective_padding_side,
            )
        if move_to_device and self.device is not None:
            tokens = tokens.to(self.device)
        return tokens

    def to_string(
        self,
        tokens: Any,
        *,
        skip_special_tokens: bool = False,
        clean_up_tokenization_spaces: bool = False,
    ) -> str | list[str]:
        """Decode token ids into text."""
        tokenizer = self._require_tokenizer_for_text("decoding")
        shape = _shape_of_token_ids(tokens)
        if shape is not None and len(shape) > 2:
            raise ValueError(f"Invalid token shape for decoding: {shape!r}.")
        if shape is not None and len(shape) == 2:
            batch_decode = getattr(tokenizer, "batch_decode", None)
            if callable(batch_decode):
                return list(
                    _call_decode_with_supported_kwargs(
                        batch_decode,
                        tokens,
                        {
                            "skip_special_tokens": skip_special_tokens,
                            "clean_up_tokenization_spaces": clean_up_tokenization_spaces,
                        },
                    )
                )
            return [
                str(
                    _call_decode_with_supported_kwargs(
                        tokenizer.decode,
                        row,
                        {
                            "skip_special_tokens": skip_special_tokens,
                            "clean_up_tokenization_spaces": clean_up_tokenization_spaces,
                        },
                    )
                )
                for row in tokens
            ]
        if isinstance(tokens, int):
            tokens = [tokens]
        return str(
            _call_decode_with_supported_kwargs(
                tokenizer.decode,
                tokens,
                {
                    "skip_special_tokens": skip_special_tokens,
                    "clean_up_tokenization_spaces": clean_up_tokenization_spaces,
                },
            )
        )

    def to_str_tokens(
        self,
        text_or_tokens: str | Any,
        *,
        prepend_bos: bool | None = None,
        padding_side: str | None = None,
    ) -> list[str] | list[list[str]]:
        """Return per-token strings for text or token ids."""
        tokenizer = self._require_tokenizer_for_text("token string conversion")
        resolved_prepend_bos = _resolve_default_prepend_bos(self, prepend_bos)
        if (
            isinstance(text_or_tokens, Sequence)
            and not isinstance(text_or_tokens, str | bytes)
            and text_or_tokens
            and isinstance(
                text_or_tokens[0],
                Sequence | str,
            )
        ):
            return [
                self.to_str_tokens(
                    item,
                    prepend_bos=resolved_prepend_bos,
                    padding_side=padding_side,
                )
                for item in text_or_tokens
            ]
        tokens = (
            self.to_tokens(
                text_or_tokens,
                prepend_bos=resolved_prepend_bos,
                padding_side=padding_side,
            )
            if isinstance(text_or_tokens, str)
            else text_or_tokens
        )
        shape = getattr(tokens, "shape", None)
        if shape is not None:
            shape_tuple = tuple(int(dim) for dim in shape)
            if len(shape_tuple) == 2 and shape_tuple[0] == 1:
                tokens = tokens[0]
            elif len(shape_tuple) > 1:
                raise ValueError(
                    f"Invalid token shape for token string conversion: {shape_tuple!r}."
                )
        token_list = _single_token_list(tokens)
        batch_decode = getattr(tokenizer, "batch_decode", None)
        if callable(batch_decode):
            return [
                str(token)
                for token in _call_decode_with_supported_kwargs(
                    batch_decode,
                    [[token] for token in token_list],
                    {"clean_up_tokenization_spaces": False},
                )
            ]
        convert = getattr(tokenizer, "convert_ids_to_tokens", None)
        if callable(convert):
            converted = convert(token_list)
            if isinstance(converted, str):
                return [converted]
            return [str(token) for token in converted]
        return [str(tokenizer.decode([token])) for token in token_list]

    def to_single_token(self, text: str) -> int:
        """Return the single token id for text or raise when it tokenizes to multiple ids."""
        tokens = self.to_tokens(text, prepend_bos=False)
        shape = getattr(tokens, "shape", None)
        token_values = tokens.reshape(-1).tolist() if shape is not None else list(tokens)
        if len(token_values) != 1:
            raise ValueError(
                f"Expected {text!r} to tokenize to a single token, got {token_values}."
            )
        return int(token_values[0])

    def to_single_str_token(self, token: int) -> str:
        """Return the string for a single token id."""
        if not isinstance(token, int):
            raise TypeError(f"Expected an integer token id, got {type(token)!r}.")
        tokens = self.to_str_tokens([token])
        if len(tokens) != 1 or isinstance(tokens[0], list):
            raise ValueError(f"Expected token id {token!r} to decode to one string token.")
        return str(tokens[0])

    def get_token_position(
        self,
        single_token: str | int | Any,
        text_or_tokens: str | Any,
        *,
        mode: str = "first",
        prepend_bos: bool | None = None,
        padding_side: str | None = None,
    ) -> int:
        """Return the first or last position of one token in a prompt or token sequence."""
        tokens = (
            self.to_tokens(
                text_or_tokens,
                prepend_bos=prepend_bos,
                padding_side=padding_side,
            )
            if isinstance(text_or_tokens, str)
            else text_or_tokens
        )
        token_values = _flatten_single_token_sequence(tokens)
        if isinstance(single_token, str):
            token_id = self.to_single_token(single_token)
        else:
            item = getattr(single_token, "item", None)
            token_id = int(item()) if callable(item) else int(single_token)
        positions = [index for index, value in enumerate(token_values) if int(value) == token_id]
        if not positions:
            raise ValueError("The token does not occur in the prompt.")
        if mode == "first":
            return positions[0]
        if mode == "last":
            return positions[-1]
        raise ValueError(f"mode must be 'first' or 'last', not {mode!r}.")

    def tokens_to_residual_directions(self, tokens: Any) -> Any:
        """Map token ids to unembedding residual directions."""
        weight = self._output_embedding_weight()
        if isinstance(tokens, str):
            tokens = self.to_single_token(tokens)
        elif isinstance(tokens, int):
            pass
        else:
            numel = getattr(tokens, "numel", None)
            item = getattr(tokens, "item", None)
            if callable(numel) and callable(item):
                try:
                    if int(numel()) == 1:
                        tokens = int(item())
                except Exception:
                    pass
        try:
            if isinstance(weight, Sequence) and not isinstance(weight, str | bytes):
                return _gather_sequence_residual_directions(weight, tokens)
            tokens = _coerce_tokens_for_weight_index(weight, tokens)
            return weight[tokens]
        except Exception as exc:
            raise RuntimeError(
                "Could not index residual directions with the provided tokens."
            ) from exc

    def remove_hooks(self) -> None:
        self.reset_hooks(including_permanent=True)

    def reset_hooks(
        self,
        *,
        clear_contexts: bool = True,
        direction: Any = None,
        dir: Any = None,
        including_permanent: bool = False,
        level: int | None = None,
    ) -> None:
        """Remove wrapper-managed hooks using TransformerLens reset semantics."""
        hook_direction = _normalize_hook_direction(direction or dir or "both")
        removed_handles: list[_ManagedWrapperHookHandle] = []
        for handle in reversed(list(self._hooks)):
            if handle.is_permanent and not including_permanent:
                continue
            if level is not None and handle.level != level:
                continue
            if not _managed_handle_matches_direction(handle, hook_direction):
                continue
            removed_handles.append(handle)
            handle.remove()
        if clear_contexts:
            self._clear_hook_contexts_for_handles(removed_handles)
            self.clear_contexts()
        self.is_caching = _wrapper_has_active_permanent_cache_hooks(self._hooks)

    def clear_contexts(self) -> None:
        """Clear mutable context dictionaries on component hook objects."""
        self._clear_hook_contexts_for_handles(list(self._hooks))

    @staticmethod
    def _clear_hook_contexts_for_handles(handles: Iterable[Any]) -> None:
        for handle in handles:
            for hook_context in getattr(handle, "hook_contexts", ()):
                clear = getattr(getattr(hook_context, "ctx", None), "clear", None)
                if callable(clear):
                    clear()

    def _track_hook_handle(
        self,
        handle: Any,
        *,
        is_permanent: bool = False,
        level: int | None = None,
        is_cache: bool = False,
    ) -> _ManagedWrapperHookHandle:
        managed_handle: _ManagedWrapperHookHandle

        def untrack() -> None:
            if managed_handle in self._hooks:
                self._hooks.remove(managed_handle)

        managed_handle = _ManagedWrapperHookHandle(
            handle,
            untrack,
            is_permanent=is_permanent,
            level=level,
            is_cache=is_cache,
        )
        return managed_handle

    def _require_model(self) -> Any:
        if self.model is None:
            self.load_model()
        return self.model

    def _require_tokenizer_for_text(self, operation: str) -> Any:
        if self.tokenizer is None:
            detail = _tokenizer_error_detail(self._tokenizer_load_error)
            raise RuntimeError(f"Tokenizer is not loaded, so {operation} is unavailable. {detail}")
        return self.tokenizer

    def _output_embedding_weight(self) -> Any:
        embeddings = self._output_embeddings()
        weight = getattr(embeddings, "weight", None)
        model = self._require_model()
        if weight is None:
            weight = getattr(model, "W_U", None)
            if weight is not None:
                return transpose_2d_weight(weight)
        if weight is None:
            raise RuntimeError(
                "Could not find output embedding weights for residual direction lookup."
            )
        return weight

    def _output_embeddings(self) -> Any:
        model = self._require_model()
        get_output_embeddings = getattr(model, "get_output_embeddings", None)
        return get_output_embeddings() if callable(get_output_embeddings) else None

    def _stack_attention_weights(self, component: str) -> Any:
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        n_layers = _infer_model_layers(model)
        if n_layers <= 0:
            raise RuntimeError(f"Could not infer layer count for W_{component.upper()}.")
        weights = [
            adapter.get_attention_weight(model, component, layer) for layer in range(n_layers)
        ]
        return _stack_tensor_like(weights)

    def _stack_attention_biases(self, component: str) -> Any:
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        n_layers = _infer_model_layers(model)
        if n_layers <= 0:
            raise RuntimeError(f"Could not infer layer count for b_{component.upper()}.")
        biases = [adapter.get_attention_bias(model, component, layer) for layer in range(n_layers)]
        return _stack_tensor_like(biases)

    def _stack_mlp_weights(self, component: str) -> Any:
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        n_layers = _infer_model_layers(model)
        if n_layers <= 0:
            raise RuntimeError(f"Could not infer layer count for W_{component}.")
        weights = [adapter.get_mlp_weight(model, component, layer) for layer in range(n_layers)]
        return _stack_tensor_like(weights)

    def _stack_mlp_biases(self, component: str) -> Any:
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        n_layers = _infer_model_layers(model)
        if n_layers <= 0:
            raise RuntimeError(f"Could not infer layer count for b_{component}.")
        biases = [adapter.get_mlp_bias(model, component, layer) for layer in range(n_layers)]
        return _stack_tensor_like(biases)

    def _prepare_model_inputs(self, batch: Any) -> dict[str, Any]:
        batch = _normalize_model_batch(batch)
        model_kwargs = _model_kwargs_without_tokenization(batch)
        if "input_ids" in batch:
            model_inputs = {
                key: value
                for key, value in batch.items()
                if key not in {"model_kwargs", "prepend_bos", "padding_side", "truncate"}
            }
            model_inputs.update(model_kwargs)
            model_inputs["input_ids"] = _coerce_token_model_input(
                _ensure_token_batch_dim(model_inputs["input_ids"]),
                device=self.device,
            )
            _coerce_token_mask_fields(model_inputs, device=self.device)
            return self._with_attention_flags(model_inputs)
        for token_key in ("tokens", "token_ids"):
            if token_key in batch:
                model_inputs = {
                    key: value
                    for key, value in batch.items()
                    if key
                    not in {
                        "tokens",
                        "token_ids",
                        "model_kwargs",
                        "prepend_bos",
                        "padding_side",
                        "truncate",
                    }
                }
                model_inputs.update(model_kwargs)
                model_inputs["input_ids"] = _coerce_token_model_input(
                    _ensure_token_batch_dim(batch[token_key]),
                    device=self.device,
                )
                _coerce_token_mask_fields(model_inputs, device=self.device)
                return self._with_attention_flags(model_inputs)
        if self.tokenizer is not None and "input_ids" not in batch:
            text = _text_or_prompt_value(batch)
            if text is not None:
                if self._uses_decoder_text_input_semantics():
                    prepared = _prepare_text_inputs_with_to_tokens(self, batch)
                    if prepared is not None:
                        return self._with_attention_flags(prepared)
                tokenized = _tokenize_text_batch(self.tokenizer, text)
                if self.device is not None:
                    tokenized = tokenized.to(self.device)
                return self._with_attention_flags(dict(tokenized))
        if self.tokenizer is None and "input_ids" not in batch:
            text = _text_or_prompt_value(batch)
            if text is not None:
                detail = _tokenizer_error_detail(self._tokenizer_load_error)
                raise ValueError(
                    "This model did not load a tokenizer, so text batches cannot be "
                    f"tokenized. Provide `input_ids` or `inputs_embeds` directly. {detail}"
                )
        return self._with_attention_flags(dict(batch))

    def _try_register_component_hook(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any | None:
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        if adapter.parse_component_ref(layer) is None:
            return None
        requires_output_attentions = adapter.requires_output_attentions(layer)
        handle = adapter.register_component_hook(model, layer, hook_fn, prepend=prepend)
        if requires_output_attentions:
            self._attention_hook_count += 1
            return _TrackedAttentionHandle(handle, self._release_attention_hook)
        return handle

    def _try_register_component_backward_hook(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any | None:
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        component_ref = adapter.parse_component_ref(layer)
        if component_ref is None:
            return None
        spec = adapter._spec_for_ref(component_ref, for_cache=False)
        module = adapter.get_component(model, component_ref)
        if spec.value in {"attention_pattern", "attention_scores"}:
            raise NotImplementedError(
                "Backward hooks for attention pattern/scores require custom attention "
                "softmax instrumentation and are not yet supported."
            )
        if spec.component == "result":
            raise NotImplementedError(
                "Backward hooks for derived attention result activations are not yet supported."
            )
        hook_context = ComponentHookContext(component_ref)
        if spec.mode == "forward_input":
            hook = _make_component_input_backward_registration_hook(
                hook_fn,
                component_ref,
                adapter.name,
                spec,
                model,
                hook_context,
            )
            return _BackwardHookRegistrationHandle(
                _register_module_forward_pre_hook(module, hook, prepend=prepend),
                (hook_context,),
            )
        hook = _make_component_output_backward_registration_hook(
            hook_fn,
            component_ref,
            adapter.name,
            spec,
            model,
            hook_context,
        )
        return _BackwardHookRegistrationHandle(
            _register_module_forward_hook(module, hook, prepend=prepend),
            (hook_context,),
        )

    def _try_register_top_level_hook(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any | None:
        hook_name = _canonical_top_level_hook_name(layer)
        if hook_name is None:
            return None
        module = _resolve_top_level_hook_module(model, hook_name)
        if module is None:
            return None
        hook_context = _TopLevelHookContext(hook_name)

        def hook(_module: Any, _inputs: Any, output: Any) -> Any:
            activation = (
                _final_norm_scale_from_hook(_module, _inputs, output)
                if hook_name == "ln_final.hook_scale"
                else output
            )
            patched = _call_top_level_hook(
                hook_fn,
                activation=activation,
                hook_name=hook_name,
                hook_context=hook_context,
            )
            if hook_name == "ln_final.hook_scale":
                if patched is None:
                    return None
                return _replace_final_norm_output_from_scale(_module, _inputs, output, patched)
            return None if patched is None else patched

        return _HookHandleWithContexts(
            _register_module_forward_hook(module, hook, prepend=prepend),
            (hook_context,),
        )

    def _try_register_top_level_backward_hook(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any | None:
        hook_name = _canonical_top_level_hook_name(layer)
        if hook_name is None:
            return None
        if hook_name == "ln_final.hook_scale":
            raise NotImplementedError(
                "Backward hooks for derived normalization scale activations are not yet supported."
            )
        module = _resolve_top_level_hook_module(model, hook_name)
        if module is None:
            return None
        hook_context = _TopLevelHookContext(hook_name)
        hook = _make_raw_output_backward_registration_hook(
            hook_fn,
            hook_context,
            hook_name=hook_name,
        )
        return _BackwardHookRegistrationHandle(
            _register_module_forward_hook(module, hook, prepend=prepend),
            (hook_context,),
        )

    def _resolve_hook_layer_ref(
        self,
        model: Any,
        layer: LayerRef,
        *,
        for_cache: bool | None,
    ) -> LayerRef:
        if not isinstance(layer, str):
            return layer
        top_level_name = _canonical_top_level_hook_name(layer)
        if top_level_name is not None and _top_level_hook_is_resolvable(model, top_level_name):
            return top_level_name
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        if adapter.parse_component_ref(layer) is not None:
            return layer
        matched = _filter_hook_names(
            _candidate_hook_names(model, adapter, for_cache=for_cache),
            layer,
            adapter=adapter,
        )
        if len(matched) == 1:
            return matched[0]
        return layer

    def _try_register_component_cache_hook(
        self,
        model: Any,
        layer: LayerRef,
        cache: ActivationCache,
        *,
        detach: bool,
        clone: bool,
        device: Any,
        pos_slice: Any,
        remove_batch_dim: bool,
        is_permanent: bool = False,
    ) -> Any | None:
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        component_ref = adapter.parse_component_ref(layer)
        if component_ref is None:
            return None
        if isinstance(layer, tuple):
            cache_name = component_ref.transformer_lens_name
        else:
            cache_name = activation_name_for_layer(layer) if isinstance(layer, int) else str(layer)
        if _cache_hook_requires_runtime_flag(cache_name):
            self.check_hooks_to_add(None, cache_name, None)

        handle = adapter.register_component_hook_for_mode(
            model,
            layer,
            make_cache_hook(
                cache,
                cache_name,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
            ),
            for_cache=True,
        )
        requires_output_attentions = adapter.requires_output_attentions(layer)
        if requires_output_attentions and is_permanent:
            self._attention_hook_count += 1
            return _TrackedAttentionHandle(handle, self._release_attention_hook)
        if requires_output_attentions:
            self._run_requires_output_attentions = True
        return handle

    def _try_register_top_level_cache_hook(
        self,
        model: Any,
        layer: LayerRef,
        cache: ActivationCache,
        *,
        detach: bool,
        clone: bool,
        device: Any,
        pos_slice: Any,
        remove_batch_dim: bool,
    ) -> Any | None:
        hook_name = _canonical_top_level_hook_name(layer)
        if hook_name is None:
            return None
        module = _resolve_top_level_hook_module(model, hook_name)
        if module is None:
            return None
        if hook_name == "ln_final.hook_scale":
            return _register_module_forward_hook(
                module,
                make_final_norm_scale_cache_hook(
                    cache,
                    hook_name,
                    detach=detach,
                    clone=clone,
                    device=device,
                    pos_slice=pos_slice,
                    remove_batch_dim=remove_batch_dim,
                ),
                prepend=False,
            )
        return _register_module_forward_hook(
            module,
            make_cache_hook(
                cache,
                hook_name,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
            ),
            prepend=False,
        )

    def _register_cache_hook(
        self,
        model: Any,
        layer: LayerRef,
        cache: ActivationCache,
        *,
        detach: bool,
        clone: bool,
        device: Any,
        pos_slice: Any,
        remove_batch_dim: bool,
        is_permanent: bool = False,
    ) -> Any:
        layer = self._resolve_hook_layer_ref(model, layer, for_cache=True)
        top_level_handle = self._try_register_top_level_cache_hook(
            model,
            layer,
            cache,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
        )
        if top_level_handle is not None:
            return top_level_handle
        component_handle = self._try_register_component_cache_hook(
            model,
            layer,
            cache,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
            is_permanent=is_permanent,
        )
        if component_handle is not None:
            return component_handle
        module = self._resolve_layer(model, layer)
        cache_name = activation_name_for_layer(layer)
        return _register_module_forward_hook(
            module,
            make_cache_hook(
                cache,
                cache_name,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
            ),
            prepend=False,
        )

    def _with_attention_flags(self, model_inputs: dict[str, Any]) -> dict[str, Any]:
        if self._attention_hook_count > 0 or self._run_requires_output_attentions:
            model_inputs.setdefault("output_attentions", True)
        return model_inputs

    def _release_attention_hook(self) -> None:
        self._attention_hook_count = max(0, self._attention_hook_count - 1)

    def _expand_hook_specs(
        self,
        hook_specs: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]],
    ) -> list[tuple[LayerRef, HookFn]]:
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        names = _candidate_hook_names(model, adapter, for_cache=False)
        expanded: list[tuple[LayerRef, HookFn]] = []
        for layer_or_filter, hook_fn in hook_specs:
            if callable(layer_or_filter) and not isinstance(layer_or_filter, str):
                matched = _filter_hook_names(names, layer_or_filter, adapter=adapter)
                expanded.extend((name, hook_fn) for name in matched)
                continue
            if isinstance(layer_or_filter, str):
                matched = _filter_hook_names(names, layer_or_filter, adapter=adapter)
                if matched:
                    expanded.extend((name, hook_fn) for name in matched)
                    continue
            expanded.append((layer_or_filter, hook_fn))
        return expanded

    def _cache_layers(
        self,
        model: Any,
        layers: Sequence[LayerRef] | None,
        names_filter: NamesFilter,
        *,
        cache_all: bool = False,
    ) -> list[LayerRef]:
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        normalized_layers = _normalize_cache_layers_arg(layers)
        if normalized_layers is not None:
            selected = normalized_layers
        elif names_filter is not None:
            selected = _filter_hook_names(
                _candidate_hook_names(model, adapter, for_cache=True),
                names_filter,
                adapter=adapter,
            )
        elif cache_all:
            selected = _default_cache_hook_names(model, adapter)
        else:
            selected = []
        return selected

    @staticmethod
    def _resolve_layer(model: Any, layer: LayerRef) -> Any:
        if isinstance(layer, str):
            modules = dict(model.named_modules())
            if layer not in modules:
                examples = ", ".join(list(modules)[:8])
                raise KeyError(
                    f"Unknown module or hook name {layer!r}. Use an integer layer index, "
                    "a module name from model.named_modules(), or a component hook name "
                    "supported by the selected model adapter. "
                    f"First available module names: {examples}"
                )
            return modules[layer]

        for path in (
            "model.layers",
            "model.language_model.layers",
            "transformer.h",
            "gpt_neox.layers",
        ):
            target = model
            try:
                for part in path.split("."):
                    target = getattr(target, part)
                return target[layer]
            except (AttributeError, IndexError, TypeError):
                continue
        raise KeyError(
            f"Could not resolve layer index {layer} for model {type(model).__name__}. "
            "Known decoder-layer paths tried: model.layers, model.language_model.layers, "
            "transformer.h, gpt_neox.layers."
        )


class TransformerLensCompatibleModelWrapper(HuggingFaceModelWrapper):
    """Independent Transformers wrapper for TransformerLens-compatible model IDs.

    The compatibility table mirrors TransformerLens' public support matrix, but
    this class never imports or delegates to TransformerLens. Decoder,
    encoder-decoder, encoder, and audio-encoder families are loaded through the
    closest Transformers auto class.
    """

    def __init__(
        self,
        *args: Any,
        process_weights_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._process_weights_kwargs = (
            dict(process_weights_kwargs)
            if process_weights_kwargs is not None
            else _default_transformer_lens_process_kwargs()
        )
        self._weights_processed = False

    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        **kwargs: Any,
    ) -> TransformerLensCompatibleModelWrapper:
        """Build and load a dependency-free TransformerLens-compatible wrapper."""
        process_kwargs = _extract_transformer_lens_process_kwargs(kwargs)
        wrapper = cls(
            name=model_name,
            dtype=str(kwargs.pop("dtype", "float32")),
            device=kwargs.pop("device", None),
            revision=kwargs.pop("revision", None),
            cache_dir=kwargs.pop("cache_dir", None),
            trust_remote_code=bool(kwargs.pop("trust_remote_code", False)),
            load_kwargs=dict(kwargs.pop("load_kwargs", {})),
            tokenizer_kwargs=dict(kwargs.pop("tokenizer_kwargs", {})),
            pretrained_path=kwargs.pop("pretrained_path", None),
            process_weights_kwargs=process_kwargs,
        )
        wrapper.load_kwargs.update(_filter_transformer_lens_load_kwargs(kwargs))
        wrapper.load_model()
        return wrapper

    @classmethod
    def from_pretrained_no_processing(
        cls,
        model_name: str,
        **kwargs: Any,
    ) -> TransformerLensCompatibleModelWrapper:
        """Build a TransformerLens-compatible wrapper without TL weight processing."""
        kwargs.setdefault("fold_ln", False)
        kwargs.setdefault("center_writing_weights", False)
        kwargs.setdefault("center_unembed", False)
        kwargs.setdefault("fold_value_biases", False)
        kwargs.setdefault("refactor_factored_attn_matrices", False)
        return cls.from_pretrained(model_name, **kwargs)

    def load_model(self) -> Any:
        if not self._is_supported_transformer_lens_target():
            raise ValueError(
                f"Model {self.name!r} is not in SafeLens' vendored TransformerLens-compatible "
                "support table. Use source='huggingface' for generic Transformers loading, "
                "or source='local' for a local model directory."
            )
        pretrained_path = self._resolve_pretrained_path()
        self._raise_if_native_transformer_lens_checkpoint(pretrained_path)
        try:
            import torch
            from transformers import (
                AutoFeatureExtractor,
                AutoModel,
                AutoModelForCausalLM,
                AutoModelForSeq2SeqLM,
                AutoProcessor,
                AutoTokenizer,
            )
        except ImportError as exc:
            raise ImportError(
                "TransformerLensCompatibleModelWrapper requires SafeLens model "
                "dependencies. Install them with `pip install -e '.[models]'`."
            ) from exc

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
            "auto": "auto",
        }
        torch_dtype = dtype_map.get(self.dtype, self.dtype)
        pretrained_kwargs = self._pretrained_kwargs()
        kind = self._transformer_lens_model_kind(
            pretrained_path=pretrained_path,
            probe_pretrained_path=True,
        )

        if kind == "audio_encoder":
            self.tokenizer = self._load_audio_processor(
                (AutoProcessor, AutoFeatureExtractor),
                pretrained_path,
                pretrained_kwargs,
            )
            self.model = AutoModel.from_pretrained(
                pretrained_path,
                torch_dtype=torch_dtype,
                trust_remote_code=self.trust_remote_code,
                **pretrained_kwargs,
                **self.load_kwargs,
            )
        else:
            self.tokenizer = self._load_text_tokenizer(
                AutoTokenizer,
                pretrained_path,
                pretrained_kwargs,
            )
            model_cls: Any
            if kind == "encoder_decoder":
                model_cls = AutoModelForSeq2SeqLM
            elif kind == "encoder":
                model_cls = AutoModel
            else:
                model_cls = AutoModelForCausalLM
            self.model = model_cls.from_pretrained(
                pretrained_path,
                torch_dtype=torch_dtype,
                trust_remote_code=self.trust_remote_code,
                **pretrained_kwargs,
                **self.load_kwargs,
            )

        if self.device is not None:
            self.model.to(self.device)
        self.model.eval()
        self._weights_processed = False
        self._process_loaded_weights()
        return self.model

    def _process_loaded_weights(self) -> None:
        if self._weights_processed:
            return
        self.process_weights_(**self._process_weights_kwargs)
        self._weights_processed = True

    def _transformer_lens_model_kind(
        self,
        *,
        pretrained_path: str | None = None,
        probe_pretrained_path: bool = False,
    ) -> str:
        model = getattr(self, "model", None)
        config = _core_model_config(_config_attr(model, "config"))
        model_type = _config_attr(config, "model_type")
        if isinstance(model_type, str) and model_type:
            return transformer_lens_model_kind(model_type)

        candidate = pretrained_path or self.pretrained_path or self.name
        if probe_pretrained_path and candidate:
            try:
                from transformers import AutoConfig
            except ImportError:
                pass
            else:
                try:
                    inferred_config = AutoConfig.from_pretrained(
                        candidate,
                        trust_remote_code=self.trust_remote_code,
                        **self._pretrained_kwargs(),
                    )
                except Exception:
                    pass
                else:
                    inferred_model_type = _config_attr(
                        _core_model_config(inferred_config),
                        "model_type",
                    )
                    if isinstance(inferred_model_type, str) and inferred_model_type:
                        return transformer_lens_model_kind(inferred_model_type)

        return transformer_lens_model_kind(candidate)

    def _resolve_pretrained_path(self) -> str:
        raw_path = self.pretrained_path or self.name
        if self._pretrained_path_is_local or _wrapper_looks_like_local_path(raw_path):
            return raw_path
        return resolve_transformer_lens_compatible_model_name(raw_path)

    def _raise_if_native_transformer_lens_checkpoint(self, pretrained_path: str) -> None:
        if (
            _wrapper_looks_like_local_path(self.name)
            or self._pretrained_path_is_local
            or self.pretrained_path is not None
            and _wrapper_looks_like_local_path(self.pretrained_path)
        ):
            return
        if not (
            is_transformer_lens_native_checkpoint(self.name)
            or is_transformer_lens_native_checkpoint(pretrained_path)
        ):
            return
        raise NotImplementedError(
            f"Model {self.name!r} resolves to TransformerLens-native checkpoint "
            f"{pretrained_path!r}. That repository stores HookedTransformer config "
            "and .pth weights rather than a HuggingFace Transformers model with a "
            "`model_type` config. SafeLens' transformer_lens source is dependency-free "
            "and currently loads only Transformers-compatible checkpoints; use a "
            "Transformers model id/local directory or convert the checkpoint to "
            "Transformers format before loading."
        )

    def _is_supported_transformer_lens_target(self) -> bool:
        if _wrapper_looks_like_local_path(self.name):
            return True
        if self._pretrained_path_is_local:
            return True
        if self.pretrained_path is not None and _wrapper_looks_like_local_path(
            self.pretrained_path
        ):
            return True
        return is_transformer_lens_supported_model_name(self.name)

    def _prepare_model_inputs(self, batch: Any) -> dict[str, Any]:
        batch = _normalize_model_batch(batch)
        kind = self._transformer_lens_model_kind()
        model_kwargs = _model_kwargs_without_tokenization(batch)
        if kind == "encoder_decoder" and "encoder_tokens" in batch and "decoder_tokens" in batch:
            return self._with_attention_flags(
                {
                    "input_ids": batch["encoder_tokens"],
                    "decoder_input_ids": batch["decoder_tokens"],
                    **model_kwargs,
                }
            )
        if kind == "encoder_decoder":
            prepared = super()._prepare_model_inputs(batch)
            prepared.update(model_kwargs)
            if not any(
                key in prepared for key in ("decoder_input_ids", "decoder_inputs_embeds", "labels")
            ):
                input_ids = prepared.get("input_ids")
                if input_ids is None:
                    raise ValueError(
                        "Encoder-decoder models require input_ids or explicit decoder inputs."
                    )
                config = getattr(self._require_model(), "config", None)
                decoder_start_token_id = batch.get(
                    "decoder_start_token_id",
                    _config_attr(config, "decoder_start_token_id"),
                )
                if decoder_start_token_id is None:
                    decoder_start_token_id = _config_attr(config, "pad_token_id")
                if decoder_start_token_id is None:
                    decoder_start_token_id = getattr(self.tokenizer, "pad_token_id", None)
                if decoder_start_token_id is None:
                    raise ValueError(
                        "Encoder-decoder models require decoder_input_ids when no "
                        "decoder_start_token_id or pad_token_id is available."
                    )
                prepared["decoder_input_ids"] = input_ids.new_full(
                    (input_ids.shape[0], 1),
                    int(decoder_start_token_id),
                )
            return self._with_attention_flags(prepared)
        if kind == "decoder":
            prepared = self._prepare_decoder_text_inputs(batch)
            if prepared is None:
                prepared = super()._prepare_model_inputs(batch)
            prepared.update(model_kwargs)
            return self._with_attention_flags(prepared)
        if kind != "audio_encoder":
            prepared = super()._prepare_model_inputs(batch)
            prepared.update(model_kwargs)
            return self._with_attention_flags(prepared)

        if self.tokenizer is None:
            return dict(batch)
        audio = _first_present(batch, ("audio", "wave", "raw_audio"))
        if audio is None:
            return model_kwargs
        processor_kwargs = dict(batch.get("processor_kwargs", {}))
        sampling_rate = batch.get("sampling_rate", 16000)
        processed = self.tokenizer(
            audio,
            sampling_rate=sampling_rate,
            return_tensors="pt",
            **processor_kwargs,
        )
        if self.device is not None:
            processed = processed.to(self.device)
        return self._with_attention_flags({**dict(processed), **model_kwargs})

    def _prepare_decoder_text_inputs(self, batch: Mapping[str, Any]) -> dict[str, Any] | None:
        return _prepare_text_inputs_with_to_tokens(self, batch)

    def _uses_decoder_text_input_semantics(self) -> bool:
        return self._transformer_lens_model_kind() == "decoder"

    def _uses_encoder_decoder_generation_semantics(self) -> bool:
        return self._transformer_lens_model_kind() == "encoder_decoder"

    def generate(self, prompt: Any = "", **generation_kwargs: Any) -> Any:
        kind = self._transformer_lens_model_kind()
        if kind in {"encoder", "audio_encoder"}:
            raise NotImplementedError(
                f"{kind} models do not expose autoregressive text generation through "
                "the independent SafeLens Transformers wrapper."
            )
        return super().generate(prompt, **generation_kwargs)

    def generate_stream(self, prompt: Any = "", **generation_kwargs: Any) -> Iterable[Any]:
        kind = self._transformer_lens_model_kind()
        if kind in {"encoder", "audio_encoder"}:
            raise NotImplementedError(
                f"{kind} models do not expose autoregressive text generation through "
                "the independent SafeLens Transformers wrapper."
            )
        return super().generate_stream(prompt, **generation_kwargs)

    def _load_audio_processor(
        self,
        processor_classes: tuple[Any, Any],
        pretrained_path: str,
        pretrained_kwargs: dict[str, Any],
    ) -> Any:
        last_error: Exception | None = None
        for processor_cls in processor_classes:
            try:
                return processor_cls.from_pretrained(
                    pretrained_path,
                    trust_remote_code=self.trust_remote_code,
                    **pretrained_kwargs,
                    **self.tokenizer_kwargs,
                )
            except Exception as exc:
                last_error = exc
        raise RuntimeError(
            f"Could not load an audio processor for {pretrained_path!r}."
        ) from last_error


HookedTransformer = TransformerLensCompatibleModelWrapper


class Qwen3DenseModelWrapper(HuggingFaceModelWrapper):
    """Qwen3 dense wrapper exposing SafeLens component hook names.

    Supported model family: Qwen3 dense language models up to 35B parameters
    (`0.6B`, `1.7B`, `4B`, `8B`, `14B`, and `32B`). MoE variants such as
    `30B-A3B` and non-dense/VL/Coder variants are intentionally rejected.
    """

    def load_model(self) -> Any:
        validate_qwen3_dense_model_name(self.name)
        model = super().load_model()
        self._validate_loaded_qwen3_dense_model(model)
        return model

    def add_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn | None = None,
        *,
        hook: HookFn | None = None,
        dir: str = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
    ) -> Any:
        """Register a TransformerLens-style hook on a Qwen3 component or module."""
        resolved_hook = _resolve_hook_argument(hook_fn, hook=hook)
        if dir == "fwd":
            return self._add_managed_hook(
                layer,
                resolved_hook,
                is_permanent=is_permanent,
                level=level,
                prepend=prepend,
            )
        if dir == "bwd":
            return self._add_managed_backward_hook(
                layer,
                resolved_hook,
                is_permanent=is_permanent,
                level=level,
                prepend=prepend,
            )
        raise ValueError(f"Invalid hook direction {dir!r}.")

    def _register_hook(self, layer: LayerRef, hook_fn: HookFn, *, prepend: bool = False) -> Any:
        layer = self._resolve_hook_layer_ref(
            self._require_model(),
            layer,
            for_cache=False,
        )
        self.check_hooks_to_add(None, str(layer), hook_fn, dir="fwd", prepend=prepend)
        component_ref = parse_qwen3_component_ref(layer)
        if component_ref is None:
            return super()._register_hook(layer, hook_fn, prepend=prepend)
        layer_index, component = component_ref
        return self._register_qwen3_component_hook(
            layer_index,
            component,
            hook_fn,
            prepend=prepend,
        )

    def run_with_cache(
        self,
        batch: Any,
        *model_args: Any,
        layers: Sequence[LayerRef] | LayerRef | None = None,
        names_filter: NamesFilter = None,
        return_cache_object: bool | object = _DEFAULT_RETURN_CACHE_OBJECT,
        remove_batch_dim: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        cache_all: bool | object = _DEFAULT_CACHE_ALL,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
        loss_per_token: bool | object = _DEFAULT_LOSS_PER_TOKEN,
        incl_bwd: bool = False,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        **forward_kwargs: Any,
    ) -> tuple[Any, dict[str, Any] | ActivationCache]:
        model = self._require_model()
        cache = ActivationCache(model=self, has_batch_dim=not remove_batch_dim)
        temp_handles: list[Any] = []
        install_complete = False
        layers, forward_args = _split_run_with_cache_positionals(model_args, layers=layers)
        forward_options = _merge_transformer_lens_forward_positionals(
            forward_args,
            forward_kwargs,
            return_type=return_type,
            loss_per_token=loss_per_token,
        )
        forward_return_type = forward_options.pop("return_type", _DEFAULT_RETURN_TYPE)
        forward_loss_per_token = bool(forward_options.pop("loss_per_token", False))
        resolved_return_type = _resolve_return_type(batch, forward_return_type)
        resolved_cache_all = _resolve_cache_all(batch, layers, names_filter, cache_all)
        resolved_return_cache_object = _resolve_return_cache_object(batch, return_cache_object)

        try:
            self.is_caching = True
            for layer in self._cache_layers(
                model,
                layers,
                names_filter,
                cache_all=resolved_cache_all,
            ):
                temp_handles.append(
                    self._register_cache_hook(
                        model,
                        layer,
                        cache,
                        detach=detach,
                        clone=clone,
                        device=device,
                        pos_slice=pos_slice,
                        remove_batch_dim=remove_batch_dim,
                    )
                )
                if incl_bwd:
                    cache_name = self._cache_name_for_layer(model, layer, for_cache=True)
                    temp_handles.append(
                        self._register_backward_hook(
                            layer,
                            make_cache_hook(
                                cache,
                                f"{cache_name}_grad",
                                detach=detach,
                                clone=clone,
                                device=device,
                                pos_slice=pos_slice,
                                remove_batch_dim=remove_batch_dim,
                            ),
                            prepend=False,
                        )
                    )

            install_complete = True
            if forward_options:
                with self._temporary_backward_hook_context(enabled=incl_bwd):
                    output = self.forward(
                        batch,
                        return_type=resolved_return_type,
                        loss_per_token=forward_loss_per_token,
                        **forward_options,
                    )
            else:
                output = self._run_model_forward(
                    batch,
                    return_type=resolved_return_type,
                    loss_per_token=forward_loss_per_token,
                    enable_grad=incl_bwd,
                )
            if incl_bwd:
                _backward_scalar_output(output)
        finally:
            if reset_hooks_end or not install_complete:
                _remove_wrapper_handles(temp_handles)
                if clear_contexts:
                    self._clear_hook_contexts_for_handles(temp_handles)
                    self.clear_contexts()
            else:
                _keep_wrapper_handles(self, temp_handles, is_cache=True)
            self.is_caching = _wrapper_has_active_permanent_cache_hooks(self._hooks)

        return output, _format_cache_result(
            cache,
            model=self,
            return_cache_object=resolved_return_cache_object,
            remove_batch_dim=False,
        )

    def _register_cache_hook(
        self,
        model: Any,
        layer: LayerRef,
        cache: ActivationCache,
        *,
        detach: bool,
        clone: bool,
        device: Any,
        pos_slice: Any,
        remove_batch_dim: bool,
        is_permanent: bool = False,
    ) -> Any:
        layer = self._resolve_hook_layer_ref(model, layer, for_cache=True)
        component_ref = parse_qwen3_component_ref(layer)
        if component_ref is None:
            return super()._register_cache_hook(
                model,
                layer,
                cache,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
                is_permanent=is_permanent,
            )

        layer_index, component = component_ref
        cache_name = str(layer)
        cache_hook = make_cache_hook(
            cache,
            cache_name,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
        )
        if (
            component in _QWEN3_ATTENTION_COMPONENTS
            or component in _QWEN3_CACHE_ONLY_COMPONENTS
            or component == "result"
        ):
            component_handle = self._try_register_component_cache_hook(
                model,
                layer,
                cache,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
                is_permanent=is_permanent,
            )
            if component_handle is not None:
                return component_handle
            raise KeyError(f"Could not resolve Qwen3 attention component {layer!r}.")
        return self._register_qwen3_component_hook(layer_index, component, cache_hook)

    def _expand_hook_specs(
        self,
        hook_specs: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]],
    ) -> list[tuple[LayerRef, HookFn]]:
        specs = list(hook_specs)
        if not specs:
            return []
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        names = _candidate_hook_names(model, adapter, for_cache=False)
        expanded: list[tuple[LayerRef, HookFn]] = []
        for layer_or_filter, hook_fn in specs:
            if callable(layer_or_filter) and not isinstance(layer_or_filter, str):
                matched = _filter_hook_names(names, layer_or_filter, adapter=adapter)
                expanded.extend((name, hook_fn) for name in matched)
                continue
            if isinstance(layer_or_filter, str):
                matched = _filter_hook_names(names, layer_or_filter, adapter=adapter)
                if matched:
                    expanded.extend((name, hook_fn) for name in matched)
                    continue
                expanded.append((layer_or_filter, hook_fn))
            else:
                expanded.append((layer_or_filter, hook_fn))
        return expanded

    def _register_qwen3_component_hook(
        self,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        if component in _QWEN3_ATTENTION_COMPONENTS or component == "result":
            handle = self._try_register_component_hook(
                self._require_model(),
                f"layer_{layer_index}.{component}",
                hook_fn,
                prepend=prepend,
            )
            if handle is None:
                raise KeyError(f"Could not resolve Qwen3 attention component {component!r}.")
            return handle
        if (
            component not in _QWEN3_PATCHABLE_COMPONENTS
            and component not in _QWEN3_EXPLICIT_COMPONENTS
        ):
            supported = ", ".join(qwen3_supported_hook_components(include_attention=True))
            examples = ", ".join(_QWEN3_COMPONENT_EXAMPLES[:4])
            raise KeyError(
                f"Unsupported Qwen3 dense component {component!r}. "
                f"Supported components: {supported}. Example hook names: {examples}."
            )

        qwen_layer = self._qwen3_layer(layer_index)
        if component == "resid_pre":
            return self._register_input_hook(
                qwen_layer,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component == "resid_mid":
            return self._register_input_hook(
                qwen_layer.post_attention_layernorm,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component == "resid_post":
            return self._register_first_output_hook(
                qwen_layer,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component == "attn_out":
            return self._register_first_output_hook(
                qwen_layer.self_attn,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component == "mlp_out":
            return self._register_tensor_output_hook(
                qwen_layer.mlp,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component == "pre":
            return self._register_tensor_output_hook(
                qwen_layer.mlp.gate_proj,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component == "pre_linear":
            return self._register_tensor_output_hook(
                qwen_layer.mlp.up_proj,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component == "post":
            return self._register_input_hook(
                qwen_layer.mlp.down_proj,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        if component in {"q", "k", "v"}:
            projection = getattr(qwen_layer.self_attn, f"{component}_proj")
            return self._register_head_projection_hook(
                projection,
                layer_index,
                component,
                hook_fn,
                prepend=prepend,
            )
        return self._register_z_hook(
            qwen_layer.self_attn.o_proj,
            layer_index,
            hook_fn,
            prepend=prepend,
        )

    def _register_input_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        hook_context = _qwen3_hook_context(layer_index, component)

        def pre_hook(_module: Any, inputs: tuple[Any, ...]) -> tuple[Any, ...] | None:
            if not inputs:
                return None
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=inputs[0],
                layer=layer_index,
                component=component,
                hook_context=hook_context,
            )
            if patched is None:
                return None
            return (patched, *inputs[1:])

        return _register_module_forward_pre_hook(module, pre_hook, prepend=prepend)

    def _register_first_output_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        hook_context = _qwen3_hook_context(layer_index, component)

        def forward_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            activation = _first_output(output)
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=activation,
                layer=layer_index,
                component=component,
                hook_context=hook_context,
            )
            if patched is None:
                return None
            return _replace_first_output(output, patched)

        return _register_module_forward_hook(module, forward_hook, prepend=prepend)

    def _register_tensor_output_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        hook_context = _qwen3_hook_context(layer_index, component)

        def forward_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=output,
                layer=layer_index,
                component=component,
                hook_context=hook_context,
            )
            return None if patched is None else patched

        return _register_module_forward_hook(module, forward_hook, prepend=prepend)

    def _register_head_projection_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        hook_context = _qwen3_hook_context(layer_index, component)

        def forward_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            n_heads = self._heads_for_component(component)
            activation = _split_qwen3_heads(output, n_heads)
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=activation,
                layer=layer_index,
                component=component,
                hook_context=hook_context,
            )
            if patched is None:
                return None
            return _merge_qwen3_heads(patched, output)

        return _register_module_forward_hook(module, forward_hook, prepend=prepend)

    def _register_z_hook(
        self,
        module: Any,
        layer_index: int,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        hook_context = _qwen3_hook_context(layer_index, "z")

        def pre_hook(_module: Any, inputs: tuple[Any, ...]) -> tuple[Any, ...] | None:
            if not inputs:
                return None
            activation = _split_qwen3_heads(inputs[0], self._heads_for_component("z"))
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=activation,
                layer=layer_index,
                component="z",
                hook_context=hook_context,
            )
            if patched is None:
                return None
            return (_merge_qwen3_heads(patched, inputs[0]), *inputs[1:])

        return _register_module_forward_pre_hook(module, pre_hook, prepend=prepend)

    def _qwen3_layer(self, layer_index: int) -> Any:
        layers = _get_qwen3_layers(self._require_model())
        try:
            return layers[layer_index]
        except IndexError as exc:
            raise KeyError(f"Unknown Qwen3 dense layer index {layer_index}.") from exc

    def _heads_for_component(self, component: str) -> int:
        config = getattr(self._require_model(), "config", None)
        if component in {"k", "v"}:
            n_key_value_heads = _config_attr(config, "num_key_value_heads")
            if n_key_value_heads is not None:
                return int(n_key_value_heads)
        n_heads = _config_attr(config, "num_attention_heads")
        if n_heads is None:
            raise ValueError("Qwen3 config does not expose num_attention_heads.")
        return int(n_heads)

    @staticmethod
    def _validate_loaded_qwen3_dense_model(model: Any) -> None:
        config = getattr(model, "config", None)
        model_type = str(_config_attr(config, "model_type", "")).lower()
        if model_type not in {"qwen3", ""}:
            raise ValueError(f"Expected a Qwen3 dense model, got model_type={model_type!r}.")
        if _config_attr(config, "num_experts") is not None:
            raise ValueError("Qwen3 MoE models are not supported by Qwen3DenseModelWrapper.")


def parse_qwen3_component_ref(layer: LayerRef) -> tuple[int, str] | None:
    """Parse SafeLens or TransformerLens-style Qwen3 component hook names."""
    if not isinstance(layer, str):
        return None

    safe_match = re.fullmatch(r"layer_(\d+)\.([a-z_]+)", layer)
    if safe_match is not None:
        return int(safe_match.group(1)), _normalize_qwen3_component(safe_match.group(2))

    block_match = re.fullmatch(r"blocks\.(\d+)\.(?:([a-z_]+)\.)?hook_([a-z_]+)", layer)
    if block_match is not None:
        layer_index = int(block_match.group(1))
        layer_type = block_match.group(2)
        component = _normalize_qwen3_component(block_match.group(3), layer_type=layer_type)
        return layer_index, component

    return None


def qwen3_supported_hook_components(
    *,
    include_attention: bool = False,
    for_cache: bool = False,
) -> list[str]:
    """Return component names accepted by the Qwen3 dense adapter."""
    components = sorted(_QWEN3_PATCHABLE_COMPONENTS | _QWEN3_EXPLICIT_COMPONENTS)
    if include_attention:
        attention_components = set(_QWEN3_ATTENTION_COMPONENTS)
        if for_cache:
            attention_components.update(_QWEN3_CACHE_ONLY_COMPONENTS)
        components.extend(sorted(attention_components))
    return components


def qwen3_hook_name_examples() -> list[str]:
    """Return example SafeLens and TransformerLens-style Qwen3 hook names."""
    return list(_QWEN3_COMPONENT_EXAMPLES)


def validate_qwen3_hook_ref(layer: LayerRef) -> None:
    """Validate a static Qwen3 dense layer or component hook reference."""
    if isinstance(layer, int):
        if layer < 0:
            raise ValueError("Qwen3 layer indices must be non-negative integers.")
        return
    if not isinstance(layer, str):
        raise ValueError(
            f"Qwen3 hook references must be integers or strings, got {type(layer).__name__}."
        )

    component_ref = parse_qwen3_component_ref(layer)
    if component_ref is None:
        if layer.startswith("layer_") or layer.startswith("blocks."):
            examples = ", ".join(_QWEN3_COMPONENT_EXAMPLES[:6])
            raise ValueError(
                f"Invalid Qwen3 hook name {layer!r}. Expected SafeLens names such as "
                f"`layer_0.resid_pre` or TransformerLens-style names such as "
                f"`blocks.0.attn.hook_q`. Examples: {examples}."
            )
        return

    _layer_index, component = component_ref
    if component in _QWEN3_ATTENTION_COMPONENTS or component in _QWEN3_CACHE_ONLY_COMPONENTS:
        return
    if component not in _QWEN3_PATCHABLE_COMPONENTS and component not in _QWEN3_EXPLICIT_COMPONENTS:
        supported = ", ".join(qwen3_supported_hook_components(include_attention=True))
        examples = ", ".join(_QWEN3_COMPONENT_EXAMPLES[:6])
        raise ValueError(
            f"Unsupported Qwen3 hook component {component!r} in {layer!r}. "
            f"Supported components: {supported}. Examples: {examples}."
        )


def qwen3_dense_size_billion(model_name: str) -> float | None:
    """Return the parsed Qwen3 model size in billions when present in the name."""
    match = re.search(r"Qwen3[-_/](\d+(?:\.\d+)?)B", model_name, flags=re.IGNORECASE)
    if match is None:
        return None
    return float(match.group(1))


def is_supported_qwen3_dense_model_name(model_name: str) -> bool:
    """Return whether a model name looks like a supported Qwen3 <=35B dense model."""
    lowered = model_name.lower()
    if "qwen3" not in lowered:
        return False
    if any(marker in lowered for marker in ("moe", "-a", "_a", "coder", "vl")):
        return False
    size_b = qwen3_dense_size_billion(model_name)
    return size_b is None or size_b <= _QWEN3_DENSE_MAX_PARAMS_B


def validate_qwen3_dense_model_name(model_name: str) -> None:
    """Reject known unsupported Qwen3 MoE or >35B model names before loading."""
    lowered = model_name.lower()
    if "qwen3" not in lowered:
        return
    if any(marker in lowered for marker in ("moe", "-a", "_a", "coder", "vl")):
        raise ValueError(f"Unsupported Qwen3 non-dense model name: {model_name!r}.")
    size_b = qwen3_dense_size_billion(model_name)
    if size_b is not None and size_b > _QWEN3_DENSE_MAX_PARAMS_B:
        raise ValueError(
            f"Unsupported Qwen3 model size {size_b:g}B. "
            f"Only dense models <= {_QWEN3_DENSE_MAX_PARAMS_B:g}B are supported."
        )


def _normalize_qwen3_component(component: str, *, layer_type: str | None = None) -> str:
    aliases = {
        "hook_resid_pre": "resid_pre",
        "hook_resid_mid": "resid_mid",
        "hook_resid_post": "resid_post",
        "resid_pre": "resid_pre",
        "resid_mid": "resid_mid",
        "resid_post": "resid_post",
        "hook_attn_out": "attn_out",
        "attn_out": "attn_out",
        "hook_mlp_out": "mlp_out",
        "mlp_out": "mlp_out",
        "pre": "pre",
        "hook_pre": "pre",
        "pre_linear": "pre_linear",
        "hook_pre_linear": "pre_linear",
        "post": "post",
        "hook_post": "post",
        "hook_q": "q",
        "hook_k": "k",
        "hook_v": "v",
        "hook_z": "z",
        "hook_result": "result",
        "hook_pattern": "pattern",
        "hook_attn_scores": "attn_scores",
        "q": "q",
        "k": "k",
        "v": "v",
        "z": "z",
        "result": "result",
        "pattern": "pattern",
        "attn_scores": "attn_scores",
    }
    if layer_type == "mlp" and component in {"pre", "hook_pre"}:
        return "pre"
    if layer_type == "mlp" and component in {"pre_linear", "hook_pre_linear"}:
        return "pre_linear"
    if layer_type == "mlp" and component in {"post", "hook_post"}:
        return "post"
    return aliases.get(component, component)


def _call_qwen3_component_hook(
    hook_fn: HookFn,
    *,
    activation: Any,
    layer: int,
    component: str,
    hook_context: ComponentHookContext | None = None,
) -> Any:
    component_ref = ComponentRef(
        layer=layer,
        component=component,
        original=f"layer_{layer}.{component}",
    )
    if hook_context is None:
        hook_context = ComponentHookContext(component_ref)
    hook_kwargs = {
        "activation": activation,
        "output": activation,
        "hook": hook_context,
        "layer": layer,
        "component": component,
        "hook_name": component_ref.safelens_name,
        "transformer_lens_name": component_ref.transformer_lens_name,
    }
    return call_user_hook(
        hook_fn,
        hook_kwargs,
        positional_arg_options=(
            (activation, hook_context),
            (None, None, activation),
            (activation,),
        ),
        uninspectable="kwargs",
    )


def _qwen3_hook_context(layer: int, component: str) -> ComponentHookContext:
    return ComponentHookContext(
        ComponentRef(layer=layer, component=component, original=f"layer_{layer}.{component}")
    )


def _get_qwen3_layers(model: Any) -> Any:
    base_model = getattr(model, "model", model)
    layers = getattr(base_model, "layers", None)
    if layers is None:
        raise KeyError("Could not find Qwen3 decoder layers at `model.layers`.")
    return layers


def _first_output(output: Any) -> Any:
    if isinstance(output, tuple):
        return output[0]
    return output


def _replace_first_output(output: Any, patched: Any) -> Any:
    if isinstance(output, tuple):
        return (patched, *output[1:])
    return patched


def _split_qwen3_heads(activation: Any, n_heads: int) -> Any:
    shape = getattr(activation, "shape", None)
    view = getattr(activation, "view", None)
    if shape is None or not callable(view):
        return activation
    head_dim = int(shape[-1]) // n_heads
    return activation.view(*shape[:-1], n_heads, head_dim)


def _merge_qwen3_heads(activation: Any, reference: Any) -> Any:
    shape = getattr(activation, "shape", None)
    reshape = getattr(activation, "reshape", None)
    if shape is None or not callable(reshape) or len(shape) < 2:
        return activation
    reference_shape = getattr(reference, "shape", None)
    hidden_size = int(shape[-2]) * int(shape[-1])
    if reference_shape is not None:
        hidden_size = int(reference_shape[-1])
    return activation.reshape(*shape[:-2], hidden_size)


def _grad_context(*, enabled: bool = False) -> Any:
    try:
        import torch

        return torch.enable_grad() if enabled else torch.no_grad()
    except ImportError:
        return nullcontext()


def _no_grad_context() -> Any:
    return _grad_context(enabled=False)


@contextmanager
def _temporary_eager_attention(model: Any, *, enabled: bool) -> Any:
    if not enabled:
        yield
        return
    config = getattr(model, "config", None)
    original = (
        config._attn_implementation
        if config is not None and hasattr(config, "_attn_implementation")
        else _MISSING_ATTENTION_IMPLEMENTATION
    )
    if original == "eager":
        yield
        return
    set_attention = getattr(model, "set_attn_implementation", None)
    if not callable(set_attention):
        yield
        return
    try:
        set_attention("eager")
    except Exception:
        _restore_attention_implementation(config, set_attention, original)
        yield
        return
    try:
        yield
    finally:
        _restore_attention_implementation(config, set_attention, original)


def _restore_attention_implementation(config: Any, set_attention: Any, original: Any) -> None:
    if config is None:
        return
    if original is _MISSING_ATTENTION_IMPLEMENTATION:
        if hasattr(config, "_attn_implementation"):
            try:
                delattr(config, "_attn_implementation")
            except Exception:
                pass
        return
    try:
        set_attention(original)
    except Exception:
        config._attn_implementation = original


def _tokenizer_error_detail(error: Exception | None) -> str:
    if error is None:
        return "Call load_model() first or configure tokenizer files for the model."
    return f"Tokenizer load error: {type(error).__name__}: {error}"


def _tokenization_context_length(model: Any, tokenizer: Any) -> int | None:
    config = getattr(model, "config", None)
    for source in (config, tokenizer):
        if source is None:
            continue
        for attr in (
            "n_ctx",
            "n_positions",
            "max_position_embeddings",
            "seq_length",
            "model_max_length",
        ):
            context_length = _reasonable_context_length(getattr(source, attr, None))
            if context_length is not None:
                return context_length
    return None


def _reasonable_context_length(value: Any) -> int | None:
    try:
        context_length = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if context_length <= 0 or context_length >= 10**9:
        return None
    return context_length


@contextmanager
def _temporary_tokenizer_padding_side(tokenizer: Any, padding_side: str | None) -> Any:
    if padding_side is None or not hasattr(tokenizer, "padding_side"):
        yield
        return
    previous = tokenizer.padding_side
    tokenizer.padding_side = padding_side
    try:
        yield
    finally:
        tokenizer.padding_side = previous


@contextmanager
def _temporary_tokenizer_pad_token(tokenizer: Any, *, enabled: bool) -> Any:
    if not enabled or not _tokenizer_needs_pad_token(tokenizer):
        yield
        return
    fallback_token = getattr(tokenizer, "eos_token", None)
    fallback_token_id = getattr(tokenizer, "eos_token_id", None)
    if fallback_token is None and fallback_token_id is None:
        fallback_token = getattr(tokenizer, "bos_token", None)
        fallback_token_id = getattr(tokenizer, "bos_token_id", None)
    if fallback_token is None and fallback_token_id is None:
        yield
        return

    previous_token = getattr(tokenizer, "pad_token", None)
    previous_token_id = getattr(tokenizer, "pad_token_id", None)
    changed_token = hasattr(tokenizer, "pad_token")
    changed_token_id = hasattr(tokenizer, "pad_token_id")
    if changed_token:
        tokenizer.pad_token = fallback_token
    if changed_token_id:
        tokenizer.pad_token_id = fallback_token_id
    try:
        yield
    finally:
        if changed_token:
            tokenizer.pad_token = previous_token
        if changed_token_id:
            tokenizer.pad_token_id = previous_token_id


def _tokenizer_needs_pad_token(tokenizer: Any) -> bool:
    return (
        getattr(tokenizer, "pad_token", None) is None
        and getattr(
            tokenizer,
            "pad_token_id",
            None,
        )
        is None
    )


def _call_tokenizer_with_supported_kwargs(
    tokenizer: Any,
    text: Any,
    kwargs: dict[str, Any],
) -> Any:
    current_kwargs = dict(kwargs)
    fallback_keys = ("max_length", "truncation", "padding", "add_special_tokens")
    while True:
        try:
            return tokenizer(text, **current_kwargs)
        except TypeError:
            removable = next((key for key in fallback_keys if key in current_kwargs), None)
            if removable is None:
                raise
            current_kwargs.pop(removable, None)


def _call_decode_with_supported_kwargs(
    decode_fn: Any,
    tokens: Any,
    kwargs: dict[str, Any],
) -> Any:
    current_kwargs = dict(kwargs)
    fallback_keys = ("clean_up_tokenization_spaces", "skip_special_tokens")
    while True:
        try:
            return decode_fn(tokens, **current_kwargs)
        except TypeError:
            removable = next((key for key in fallback_keys if key in current_kwargs), None)
            if removable is None:
                raise
            current_kwargs.pop(removable, None)


def _resolve_default_prepend_bos(
    wrapper: HuggingFaceModelWrapper,
    prepend_bos: bool | None,
) -> bool:
    """Resolve TransformerLens-style default BOS behavior."""
    if prepend_bos is not None:
        return bool(prepend_bos)
    model = getattr(wrapper, "model", None)
    for owner in (wrapper, model, getattr(model, "config", None)):
        if owner is None:
            continue
        value = getattr(owner, "default_prepend_bos", None)
        if value is not None:
            return bool(value)
    return True


def _normalize_hook_direction(direction: Any) -> str:
    if direction is None:
        return "both"
    normalized = str(direction).lower()
    if normalized not in {"fwd", "bwd", "both"}:
        raise ValueError(f"Invalid hook direction {direction!r}.")
    return normalized


def _managed_handle_matches_direction(
    handle: _ManagedWrapperHookHandle,
    direction: str,
) -> bool:
    if direction == "both":
        return True
    is_backward = bool(getattr(handle, "is_backward", False))
    return is_backward if direction == "bwd" else not is_backward


def _wrapper_has_active_permanent_cache_hooks(handles: Iterable[Any]) -> bool:
    return any(
        not bool(getattr(handle, "_removed", False)) and bool(getattr(handle, "is_cache", False))
        for handle in handles
    )


def _set_attr_if_possible(target: Any, name: str, value: Any) -> None:
    try:
        setattr(target, name, value)
    except Exception:
        pass


def _tokenizer_prepends_bos(tokenizer: Any) -> bool:
    encode = getattr(tokenizer, "encode", None)
    if callable(encode):
        try:
            return len(encode("")) > 0
        except Exception:
            pass
    try:
        tokenized = _call_tokenizer_with_supported_kwargs(
            tokenizer,
            "",
            {"return_tensors": "pt", "add_special_tokens": True},
        )
        input_ids = tokenized["input_ids"] if isinstance(tokenized, dict) else tokenized.input_ids
        shape = getattr(input_ids, "shape", None)
        if shape is not None:
            return int(shape[-1]) > 0
        return bool(_single_token_list(input_ids))
    except Exception:
        return False


def _coerce_to_target(device_or_dtype: Any) -> Any:
    try:
        import torch

        if isinstance(device_or_dtype, str):
            dtype = _torch_dtype_from_string(torch, device_or_dtype)
            if dtype is not None:
                return dtype
        return device_or_dtype
    except Exception:
        return device_or_dtype


def _update_wrapper_device_dtype(
    wrapper: HuggingFaceModelWrapper,
    device_or_dtype: Any,
    target: Any,
) -> None:
    try:
        import torch

        if isinstance(target, torch.dtype):
            wrapper.dtype = _string_from_torch_dtype(target)
            return
        if isinstance(target, torch.device):
            wrapper.device = str(target)
            return
    except Exception:
        pass
    if isinstance(device_or_dtype, str):
        lowered = device_or_dtype.lower()
        if _is_dtype_string(lowered):
            wrapper.dtype = lowered
        else:
            wrapper.device = device_or_dtype


def _torch_dtype_from_string(torch_module: Any, value: str) -> Any | None:
    normalized = value.lower()
    dtype_map = {
        "float16": torch_module.float16,
        "fp16": torch_module.float16,
        "half": torch_module.float16,
        "bfloat16": torch_module.bfloat16,
        "bf16": torch_module.bfloat16,
        "float32": torch_module.float32,
        "fp32": torch_module.float32,
        "float": torch_module.float32,
        "float64": torch_module.float64,
        "fp64": torch_module.float64,
        "double": torch_module.float64,
    }
    return dtype_map.get(normalized)


def _string_from_torch_dtype(dtype: Any) -> str:
    text = str(dtype)
    return text.removeprefix("torch.")


def _is_dtype_string(value: str) -> bool:
    return value in {
        "float16",
        "fp16",
        "half",
        "bfloat16",
        "bf16",
        "float32",
        "fp32",
        "float",
        "float64",
        "fp64",
        "double",
    }


def _parameter_numel(parameter: Any) -> int:
    numel = getattr(parameter, "numel", None)
    if callable(numel):
        try:
            return int(numel())
        except Exception:
            pass
    shape = getattr(parameter, "shape", None)
    if shape is not None:
        total = 1
        for dim in shape:
            total *= int(dim)
        return total
    if isinstance(parameter, Sequence) and not isinstance(parameter, str | bytes):
        return len(_single_token_list(parameter))
    return 1


def _filter_transformer_lens_load_kwargs(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    ignored = {
        "fold_ln",
        "center_writing_weights",
        "center_unembed",
        "refactor_factored_attn_matrices",
        "fold_value_biases",
        "move_to_device",
        "n_devices",
        "default_prepend_bos",
        "default_padding_side",
        "first_n_layers",
        "n_ctx",
        "checkpoint_index",
        "checkpoint_value",
        "checkpoint_label",
        "hf_model",
        "tokenizer",
    }
    return {key: value for key, value in kwargs.items() if key not in ignored}


def _default_transformer_lens_process_kwargs() -> dict[str, Any]:
    return {
        "fold_ln": True,
        "center_writing_weights": True,
        "center_unembed": True,
        "fold_value_biases": True,
        "refactor_factored_attn_matrices": False,
    }


def _extract_transformer_lens_process_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    process_kwargs = _default_transformer_lens_process_kwargs()
    for key in tuple(process_kwargs):
        if key in kwargs:
            process_kwargs[key] = bool(kwargs.pop(key))
    return process_kwargs


def _split_transformer_lens_load_kwargs(
    kwargs: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    load_kwargs = dict(kwargs)
    process_kwargs = _extract_transformer_lens_process_kwargs(load_kwargs)
    return _filter_transformer_lens_load_kwargs(load_kwargs), process_kwargs


def _text_or_prompt_value(batch: Mapping[str, Any]) -> Any:
    if "text" in batch:
        return batch["text"]
    if "prompt" in batch:
        return batch["prompt"]
    return None


def _prepare_text_inputs_with_to_tokens(
    wrapper: HuggingFaceModelWrapper,
    batch: Mapping[str, Any],
) -> dict[str, Any] | None:
    if any(key in batch for key in ("input_ids", "tokens", "token_ids", "inputs_embeds")):
        return None
    text = _text_or_prompt_value(batch)
    if text is None:
        return None
    if wrapper.tokenizer is None:
        detail = _tokenizer_error_detail(wrapper._tokenizer_load_error)
        raise ValueError(
            "This model did not load a tokenizer, so text batches cannot be "
            f"tokenized. Provide `input_ids` or `inputs_embeds` directly. {detail}"
        )

    prepend_bos = _resolve_default_prepend_bos(wrapper, batch.get("prepend_bos"))
    padding_side = batch.get("padding_side")
    truncate = bool(batch.get("truncate", True))
    input_ids = wrapper.to_tokens(
        text,
        prepend_bos=prepend_bos,
        padding_side=padding_side,
        truncate=truncate,
    )
    prepared: dict[str, Any] = {"input_ids": input_ids}
    if "attention_mask" in batch:
        prepared["attention_mask"] = _ensure_token_batch_dim(batch["attention_mask"])
    elif not isinstance(text, str):
        attention_mask = _attention_mask_from_tokens(
            input_ids,
            _tokenizer_effective_pad_token_id(wrapper.tokenizer),
            prepend_bos=prepend_bos,
            padding_side=str(padding_side or getattr(wrapper.tokenizer, "padding_side", "right")),
            bos_token_id=getattr(wrapper.tokenizer, "bos_token_id", None),
        )
        if attention_mask is not None:
            prepared["attention_mask"] = attention_mask
    return prepared


def _is_text_batch(value: Any) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, str | bytes)
        and bool(value)
        and all(isinstance(item, str) for item in value)
    )


def _looks_like_input_embeds(value: Any) -> bool:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return len(tuple(int(dim) for dim in shape)) == 3
    return False


def _normalize_generate_return_type(
    return_type: Any,
    *,
    prompt: Any,
    input_is_text: bool,
    input_is_embeds: bool = False,
    token_return_name: str = "tokens",
) -> str:
    if return_type is None:
        return "str"
    if not isinstance(return_type, str):
        raise ValueError(f"Unsupported generate return_type {return_type!r}.")
    normalized = return_type.lower()
    if normalized == "input":
        if input_is_embeds:
            return "embeds"
        return "str" if input_is_text else token_return_name
    if normalized in {"str", "string", "text"}:
        return "str"
    if normalized in {"tokens", "token"}:
        return "tokens"
    if normalized in {"tensor", "tensors"}:
        return token_return_name
    if normalized == "embeds":
        return "embeds"
    if normalized in {"model_output", "raw", "output"}:
        return "model_output"
    raise ValueError(
        "generate return_type must be one of 'input', 'str', 'tokens', 'tensor', "
        "'embeds', or 'model_output'."
    )


def _normalize_transformer_lens_generation_kwargs(
    generation_kwargs: dict[str, Any],
    *,
    model: Any,
) -> None:
    generation_kwargs.pop("verbose", None)
    stop_at_eos = generation_kwargs.pop("stop_at_eos", None)
    if stop_at_eos is False and "eos_token_id" not in generation_kwargs:
        generation_kwargs["eos_token_id"] = None
    use_past_kv_cache = generation_kwargs.pop("use_past_kv_cache", None)
    if use_past_kv_cache is not None and "use_cache" not in generation_kwargs:
        generation_kwargs["use_cache"] = bool(use_past_kv_cache)
    if "freq_penalty" in generation_kwargs and "frequency_penalty" not in generation_kwargs:
        generation_kwargs["frequency_penalty"] = generation_kwargs.pop("freq_penalty")
    elif "freq_penalty" in generation_kwargs:
        generation_kwargs.pop("freq_penalty")
    accepted = _accepted_generate_kwargs(model)
    if accepted is not None:
        for key in ("frequency_penalty",):
            if key in generation_kwargs and key not in accepted:
                generation_kwargs.pop(key, None)


def _generation_attention_mask_from_tokens(
    tokens: Any,
    *,
    tokenizer: Any | None,
    prepend_bos: bool,
    padding_side: str | None,
) -> Any | None:
    if tokenizer is None:
        return None
    return _attention_mask_from_tokens(
        tokens,
        _tokenizer_effective_pad_token_id(tokenizer),
        prepend_bos=prepend_bos,
        padding_side=str(padding_side or getattr(tokenizer, "padding_side", "right")),
        bos_token_id=getattr(tokenizer, "bos_token_id", None),
    )


def _accepted_generate_kwargs(model: Any) -> set[str] | None:
    generate = getattr(model, "generate", None)
    try:
        parameters = signature(generate).parameters.values()
    except (TypeError, ValueError):
        return None
    if any(param.kind == Parameter.VAR_KEYWORD for param in parameters):
        return None
    return {
        param.name
        for param in parameters
        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }


def _generated_sequences(generated_output: Any) -> Any:
    sequences = getattr(generated_output, "sequences", None)
    return generated_output if sequences is None else sequences


def _normalize_generated_model_output(generated_output: Any, sequences: Any) -> Any:
    if getattr(generated_output, "sequences", None) is not None:
        return generated_output
    try:
        from transformers.generation.utils import GenerateDecoderOnlyOutput

        return GenerateDecoderOnlyOutput(sequences=sequences)
    except Exception:
        try:
            from transformers.utils import ModelOutput

            return ModelOutput(sequences=sequences)
        except Exception:
            return {"sequences": sequences}


def _tokens_to_input_embeddings(model: Any, tokens: Any) -> Any:
    embedding_module = _input_embedding_module(model)
    if embedding_module is None:
        raise RuntimeError(
            "Could not resolve an input embedding module for generate(return_type='embeds')."
        )
    return embedding_module(tokens)


def _ones_token_batch_like_embedding(embed: Any, *, device: Any = None) -> Any:
    shape = getattr(embed, "shape", None)
    if shape is not None and len(tuple(int(dim) for dim in shape)) >= 2:
        batch_size, pos_length = int(shape[0]), int(shape[1])
        try:
            import torch

            return torch.ones(
                (batch_size, pos_length),
                dtype=torch.long,
                device=getattr(embed, "device", None) if device is None else device,
            )
        except Exception:
            pass
        return [[1 for _ in range(pos_length)] for _ in range(batch_size)]
    raise ValueError(f"Expected embeddings shaped [batch, pos, d_model], got {shape!r}.")


def _token_batch_size(tokens: Any) -> int:
    shape = _shape_of_token_ids(tokens)
    if shape is None:
        return 1
    if not shape:
        return 1
    return int(shape[0])


def _position_ids_like_tokens(tokens: Any, *, pos_offset: int = 0, device: Any = None) -> Any:
    shape = _shape_of_token_ids(tokens)
    if shape is None or len(shape) < 2:
        raise ValueError(f"Expected tokens shaped [batch, pos], got {shape!r}.")
    batch_size, pos_length = int(shape[0]), int(shape[1])
    try:
        import torch

        token_device = getattr(tokens, "device", None)
        target_device = token_device if device is None else device
        positions = torch.arange(
            int(pos_offset),
            int(pos_offset) + pos_length,
            dtype=torch.long,
            device=target_device,
        )
        return positions.unsqueeze(0).expand(batch_size, pos_length)
    except Exception:
        return [
            [int(pos_offset) + position for position in range(pos_length)]
            for _ in range(batch_size)
        ]


def _call_position_embedding_module(
    module: Any,
    tokens: Any,
    *,
    pos_offset: int = 0,
    attention_mask: Any | None = None,
    device: Any = None,
) -> Any:
    position_ids = _position_ids_like_tokens(tokens, pos_offset=pos_offset, device=device)
    call_attempts = (
        (tokens, pos_offset, attention_mask),
        (tokens, pos_offset),
        (position_ids,),
        (tokens,),
    )
    last_error: Exception | None = None
    for args in call_attempts:
        try:
            return module(*args)
        except TypeError as exc:
            last_error = exc
            continue
    weight = getattr(module, "weight", None)
    if weight is not None:
        return weight[position_ids]
    raise RuntimeError("Could not compute positional embeddings.") from last_error


def _is_hf_past_kv_cache(cache: Any) -> bool:
    try:
        from transformers.cache_utils import Cache as TransformersCache

        return isinstance(cache, TransformersCache)
    except Exception:
        return hasattr(cache, "layers") and hasattr(cache, "get_seq_length")


def _past_kv_cache_entries(cache: Any) -> list[Any]:
    if cache is None:
        return []
    if hasattr(cache, "layers"):
        layers = cache.layers
        try:
            return list(layers)
        except TypeError:
            pass
    entries = getattr(cache, "entries", None)
    if isinstance(entries, Mapping):
        return [entries[index] for index in sorted(entries)]
    if isinstance(entries, Sequence) and not isinstance(entries, str | bytes | bytearray):
        try:
            return list(entries)
        except TypeError:
            pass
    if isinstance(cache, Sequence) and not isinstance(cache, str | bytes | bytearray):
        try:
            return list(cache)
        except TypeError:
            pass
    return []


def _past_kv_cache_length(cache: Any) -> int:
    if cache is None:
        return 0
    get_seq_length = getattr(cache, "get_seq_length", None)
    if callable(get_seq_length):
        try:
            return int(get_seq_length())
        except TypeError:
            try:
                return int(get_seq_length(0))
            except Exception:
                pass
        except Exception:
            pass
    entry = _first_past_kv_cache_entry(cache)
    if entry is None:
        return 0
    for attr_name, axis in (
        ("past_keys", 1),
        ("keys", 2),
    ):
        entry_value = getattr(entry, attr_name, None)
        shape = getattr(entry_value, "shape", None)
        if shape is not None and len(tuple(int(dim) for dim in shape)) > axis:
            return int(shape[axis])
        sequence_length = getattr(entry, "sequence_length", None)
        if attr_name == "keys" and callable(sequence_length):
            try:
                return int(sequence_length())
            except Exception:
                pass
        if attr_name == "keys" and sequence_length is not None and not callable(sequence_length):
            try:
                return int(sequence_length)
            except Exception:
                pass
    return 0


def _past_kv_cache_batch_size(cache: Any) -> int | None:
    entry = _first_past_kv_cache_entry(cache)
    if entry is None:
        return None
    keys, values, _needs_transpose = _cache_entry_tensor_pair(entry)
    for value in (keys, values):
        shape = getattr(value, "shape", None)
        if shape is not None and len(tuple(int(dim) for dim in shape)) >= 1:
            return int(shape[0])
    return None


def _first_past_kv_cache_entry(cache: Any) -> Any | None:
    entries = _past_kv_cache_entries(cache)
    return entries[0] if entries else None


def _past_kv_cache_entry_at(cache: Any, layer_index: int) -> Any | None:
    if cache is None:
        return None
    if hasattr(cache, "layers"):
        try:
            layers = list(cache.layers)
            if 0 <= layer_index < len(layers):
                return layers[layer_index]
        except Exception:
            pass
    entries = getattr(cache, "entries", None)
    if isinstance(entries, Mapping):
        return entries.get(layer_index)
    if isinstance(entries, Sequence) and not isinstance(entries, str | bytes | bytearray):
        try:
            return entries[layer_index]
        except Exception:
            return None
    if isinstance(cache, Sequence) and not isinstance(cache, str | bytes | bytearray):
        try:
            return cache[layer_index]
        except Exception:
            return None
    return None


def _cache_entry_tensor_pair(entry: Any) -> tuple[Any | None, Any | None, bool]:
    if hasattr(entry, "past_keys") or hasattr(entry, "past_values"):
        return getattr(entry, "past_keys", None), getattr(entry, "past_values", None), True
    return getattr(entry, "keys", None), getattr(entry, "values", None), False


def _transpose_cache_sequence_axis(value: Any) -> Any:
    if value is None:
        return None
    try:
        import torch

        if isinstance(value, torch.Tensor) and value.ndim >= 4:
            return value.transpose(1, 2)
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(value, np.ndarray) and value.ndim >= 4:
            return np.swapaxes(value, 1, 2)
    except Exception:
        pass
    return value


def _past_kv_cache_to_transformers_cache(cache: Any) -> tuple[Any | None, Callable[[], None]]:
    if cache is None or _is_hf_past_kv_cache(cache):
        return cache, lambda: None
    entries = _past_kv_cache_entries(cache)
    try:
        from transformers.cache_utils import DynamicCache
    except Exception as exc:
        raise ImportError(
            "TransformerLens cache support requires transformers.cache_utils.DynamicCache."
        ) from exc
    if not entries:
        model_cache = DynamicCache()

        def sync_back() -> None:
            _sync_past_kv_cache_from_transformers_cache(cache, model_cache, ())

        return model_cache, sync_back
    metadata: list[tuple[Any, Any | None, bool]] = []
    model_cache = DynamicCache()
    for entry in entries:
        keys, values, needs_transpose = _cache_entry_tensor_pair(entry)
        if needs_transpose:
            keys = _transpose_cache_sequence_axis(keys)
            values = _transpose_cache_sequence_axis(values)
        entry_index = _entry_cache_index(cache, entry)
        if keys is not None and values is not None:
            layer_index = len(metadata) if entry_index is None else int(entry_index)
            model_cache.update(keys, values, layer_index)
        metadata.append((entry, entry_index, needs_transpose))

    def sync_back() -> None:
        _sync_past_kv_cache_from_transformers_cache(cache, model_cache, metadata)

    return model_cache, sync_back


def _entry_cache_index(cache: Any, entry: Any) -> Any:
    entries = getattr(cache, "entries", None)
    if isinstance(entries, Mapping):
        for index, candidate in entries.items():
            if candidate is entry:
                return index
    if isinstance(cache, Sequence) and not isinstance(cache, str | bytes | bytearray):
        try:
            for index, candidate in enumerate(cache):
                if candidate is entry:
                    return index
        except TypeError:
            pass
    return None


def _sync_past_kv_cache_from_transformers_cache(
    original_cache: Any,
    model_cache: Any,
    metadata: Sequence[tuple[Any, Any | None, bool]],
) -> None:
    if bool(getattr(original_cache, "frozen", False)):
        return
    model_layers = list(getattr(model_cache, "layers", []))
    if not model_layers:
        return
    if hasattr(original_cache, "entries") and isinstance(original_cache.entries, Mapping):
        for layer_index, layer_cache in enumerate(model_layers):
            entry = original_cache.entries.get(layer_index)
            if entry is None:
                entry = KeyValueCacheEntry()
                original_cache.entries[layer_index] = entry
            if bool(getattr(entry, "frozen", False)):
                continue
            keys = _transpose_cache_sequence_axis(layer_cache.keys)
            values = _transpose_cache_sequence_axis(layer_cache.values)
            if hasattr(entry, "past_keys"):
                entry.past_keys = keys
            else:
                entry.keys = keys
            if hasattr(entry, "past_values"):
                entry.past_values = values
            else:
                entry.values = values
        return
    cache_entries = getattr(original_cache, "entries", None)
    if isinstance(cache_entries, list):
        for layer_index, layer_cache in enumerate(model_layers):
            if layer_index >= len(cache_entries):
                break
            entry = cache_entries[layer_index]
            if bool(getattr(entry, "frozen", False)):
                continue
            keys = _transpose_cache_sequence_axis(layer_cache.keys)
            values = _transpose_cache_sequence_axis(layer_cache.values)
            if hasattr(entry, "past_keys"):
                entry.past_keys = keys
            else:
                entry.keys = keys
            if hasattr(entry, "past_values"):
                entry.past_values = values
            else:
                entry.values = values
        return
    for entry, entry_index, needs_transpose in metadata:
        if entry_index is None:
            continue
        if int(entry_index) >= len(model_layers):
            continue
        if bool(getattr(entry, "frozen", False)):
            continue
        layer_cache = model_layers[int(entry_index)]
        keys = layer_cache.keys
        values = layer_cache.values
        if needs_transpose:
            keys = _transpose_cache_sequence_axis(keys)
            values = _transpose_cache_sequence_axis(values)
        if hasattr(entry, "past_keys"):
            entry.past_keys = keys
        if hasattr(entry, "past_values"):
            entry.past_values = values
        if hasattr(entry, "keys") and not hasattr(entry, "past_keys"):
            entry.keys = keys
        if hasattr(entry, "values") and not hasattr(entry, "past_values"):
            entry.values = values


def _sync_past_kv_cache_from_model_output(
    original_cache: Any,
    model_cache: Any,
    output: Any,
    sync_back: Callable[[], None],
) -> None:
    if output is None:
        sync_back()
        return
    output_cache = None
    if isinstance(output, Mapping):
        output_cache = output.get("past_key_values")
    else:
        output_cache = getattr(output, "past_key_values", None)
        if output_cache is None and isinstance(output, tuple | list) and len(output) >= 2:
            output_cache = output[1]
    if output_cache is None:
        output_cache = model_cache
    _ = output_cache
    sync_back()


def _extend_attention_mask_for_past_cache(attention_mask: Any, past_kv_cache: Any) -> Any:
    past_length = _past_kv_cache_length(past_kv_cache)
    if past_length <= 0:
        return attention_mask
    try:
        import torch

        if isinstance(attention_mask, torch.Tensor):
            prefix = torch.ones(
                (attention_mask.shape[0], past_length),
                dtype=attention_mask.dtype,
                device=attention_mask.device,
            )
            return torch.cat([prefix, attention_mask], dim=-1)
    except Exception:
        pass
    if _is_sequence(attention_mask):
        if attention_mask and _is_sequence(attention_mask[0]):
            prefix = [[1] * past_length for _ in attention_mask]
            return [
                prefix_row + list(row)
                for prefix_row, row in zip(prefix, attention_mask, strict=True)
            ]
        return [1] * past_length + list(attention_mask)
    return attention_mask


def _assert_residual_stream_input(input: Any) -> None:
    shape = getattr(input, "shape", None)
    if shape is not None:
        if len(tuple(int(dim) for dim in shape)) != 3:
            raise AssertionError(
                "start_at_layer requires residual stream input shaped [batch, pos, d_model]."
            )
        return
    if not _is_sequence(input) or len(shape_of(input)) != 3:
        raise AssertionError(
            "start_at_layer requires residual stream input shaped [batch, pos, d_model]."
        )


def _residual_batch_size(residual: Any) -> int:
    shape = getattr(residual, "shape", None)
    if shape is not None and len(tuple(int(dim) for dim in shape)) >= 1:
        return int(shape[0])
    residual_shape = shape_of(residual)
    return int(residual_shape[0]) if residual_shape else 1


def _decoder_layer_modules(model: Any) -> Sequence[Any]:
    for path in (
        "model.layers",
        "model.language_model.layers",
        "transformer.h",
        "gpt_neox.layers",
    ):
        try:
            target = model
            for part in path.split("."):
                target = getattr(target, part)
            return target
        except (AttributeError, TypeError):
            continue
    raise KeyError(
        f"Could not resolve decoder blocks for model {type(model).__name__}. "
        "Known decoder-layer paths tried: model.layers, model.language_model.layers, "
        "transformer.h, gpt_neox.layers."
    )


def _position_ids_for_forward(
    tokens: Any,
    *,
    attention_mask: Any | None,
    pos_offset: int,
    device: Any,
) -> Any:
    shape = _shape_of_token_ids(tokens)
    if shape is None or len(shape) < 2:
        raise ValueError(f"Expected tokens shaped [batch, pos], got {shape!r}.")
    pos_length = int(shape[1])
    if attention_mask is None:
        return _position_ids_like_tokens(tokens, pos_offset=pos_offset, device=device)
    try:
        if hasattr(attention_mask, "shape"):
            mask = attention_mask.to(device=device)
            position_ids = (mask.long().cumsum(-1) - 1).masked_fill(mask == 0, 0)
            if int(mask.shape[-1]) == pos_length:
                position_ids = position_ids + int(pos_offset)
            elif int(mask.shape[-1]) > pos_length:
                position_ids = position_ids[..., -pos_length:]
            return position_ids
    except Exception:
        pass
    return _position_ids_like_tokens(tokens, pos_offset=pos_offset, device=device)


def _past_kv_position_offset_for_partial_forward(
    past_kv_cache: Any, attention_mask: Any | None
) -> int:
    past_length = _past_kv_cache_length(past_kv_cache)
    if past_length <= 0:
        return 0
    return past_length


def _cache_position_for_forward(tokens: Any, *, pos_offset: int, device: Any) -> Any:
    shape = _shape_of_token_ids(tokens)
    if shape is None or len(shape) < 2:
        return None
    pos_length = int(shape[1])
    try:
        import torch

        return torch.arange(
            int(pos_offset),
            int(pos_offset) + pos_length,
            dtype=torch.long,
            device=device,
        )
    except Exception:
        return [int(pos_offset) + position for position in range(pos_length)]


def _call_decoder_block(
    block: Any,
    residual: Any,
    *,
    layer_index: int,
    attention_mask: Any | None,
    position_ids: Any | None,
    cache_position: Any | None,
    past_key_values: Any | None,
    past_kv_cache_entry: Any | None,
    shortformer_pos_embed: Any | None,
    output_attentions: bool,
) -> Any:
    common_kwargs = {
        "attention_mask": attention_mask,
        "position_ids": position_ids,
        "cache_position": cache_position,
        "past_key_values": past_key_values,
        "past_key_value": past_kv_cache_entry,
        "past_kv_cache_entry": past_kv_cache_entry,
        "shortformer_pos_embed": shortformer_pos_embed,
        "output_attentions": output_attentions,
        "use_cache": past_key_values is not None or past_kv_cache_entry is not None,
    }
    attempts = (
        {key: value for key, value in common_kwargs.items() if value is not None},
        {
            key: value
            for key, value in common_kwargs.items()
            if value is not None and key not in {"past_kv_cache_entry", "shortformer_pos_embed"}
        },
        {
            key: value
            for key, value in common_kwargs.items()
            if value is not None
            and key
            not in {
                "past_kv_cache_entry",
                "shortformer_pos_embed",
                "cache_position",
            }
        },
        {
            key: value
            for key, value in common_kwargs.items()
            if value is not None
            and key
            not in {
                "past_kv_cache_entry",
                "shortformer_pos_embed",
                "cache_position",
                "past_key_value",
                "use_cache",
            }
        },
        {},
    )
    last_error: Exception | None = None
    for kwargs in attempts:
        try:
            output = block(residual, **kwargs)
            return first_output(output)
        except TypeError as exc:
            last_error = exc
            continue
    run_forward = getattr(block, "run_forward", None)
    if callable(run_forward):
        return run_forward(residual, inputs=(residual,))
    raise RuntimeError(f"Could not run decoder block {layer_index}.") from last_error


def _final_norm_module(model: Any) -> Any | None:
    return _first_module_from_paths(model, _FINAL_NORM_MODULE_PATHS)


def _unembed_residual(model: Any, residual: Any) -> Any:
    output_embeddings = None
    get_output_embeddings = getattr(model, "get_output_embeddings", None)
    if callable(get_output_embeddings):
        try:
            output_embeddings = get_output_embeddings()
        except Exception:
            output_embeddings = None
    if output_embeddings is None:
        for path in ("lm_head", "embed_out", "output_projection", "model.lm_head"):
            try:
                output_embeddings = resolve_module_path(model, path)
                break
            except (AttributeError, IndexError, KeyError, TypeError):
                continue
    if output_embeddings is not None and callable(output_embeddings):
        return output_embeddings(residual)

    weight = getattr(output_embeddings, "weight", None) if output_embeddings is not None else None
    bias = getattr(output_embeddings, "bias", None) if output_embeddings is not None else None
    if weight is None:
        weight = getattr(model, "W_U", None)
        if weight is not None:
            bias = getattr(model, "b_U", bias)
            from SafeLens.core.analysis import residual_stack_to_logits

            return residual_stack_to_logits(residual, weight, bias)
    if weight is not None:
        from SafeLens.core.analysis import residual_stack_to_logits

        return residual_stack_to_logits(residual, transpose_2d_weight(weight), bias)
    raise RuntimeError("Could not resolve an unembedding module or weight for partial forward.")


def _loss_model_inputs_for_partial_forward(
    tokens: Any | None,
    attention_mask: Any | None,
    *,
    return_type: str | None,
) -> dict[str, Any] | None:
    if return_type not in {"loss", "both"}:
        return None
    if tokens is None:
        raise AssertionError("tokens must be passed when return_type is 'loss' or 'both'.")
    return _loss_model_inputs(tokens, _slice_attention_mask_to_token_length(attention_mask, tokens))


def _slice_attention_mask_to_token_length(attention_mask: Any | None, tokens: Any) -> Any | None:
    if attention_mask is None:
        return None
    token_shape = _shape_of_token_ids(tokens)
    mask_shape = _shape_of_token_ids(attention_mask)
    if token_shape is None or mask_shape is None or len(token_shape) < 2 or len(mask_shape) < 2:
        return attention_mask
    token_length = int(token_shape[-1])
    mask_length = int(mask_shape[-1])
    if mask_length <= token_length:
        return attention_mask
    try:
        if hasattr(attention_mask, "shape"):
            return attention_mask[..., -token_length:]
    except Exception:
        pass
    if _is_sequence(attention_mask):
        if attention_mask and _is_sequence(attention_mask[0]):
            return [list(row)[-token_length:] for row in attention_mask]
        return list(attention_mask)[-token_length:]
    return attention_mask


def _slice_generated_suffix(generated_sequences: Any, input_tokens: Any) -> Any:
    input_shape = _shape_of_token_ids(input_tokens)
    if input_shape is None or len(input_shape) < 2:
        raise ValueError(
            f"Expected generated input tokens shaped [batch, pos], got {input_shape!r}."
        )
    input_length = int(input_shape[1])
    shape = getattr(generated_sequences, "shape", None)
    if shape is not None:
        if len(tuple(int(dim) for dim in shape)) == 1:
            return generated_sequences.unsqueeze(1)
        if int(shape[1]) <= input_length:
            return generated_sequences
        return generated_sequences[:, input_length:]
    sequences = _to_python_sequence_container(generated_sequences)
    return [list(row)[input_length:] or list(row) for row in sequences]


def _normalize_generated_new_tokens(tokens: Any) -> Any:
    shape = getattr(tokens, "shape", None)
    if shape is not None and len(tuple(int(dim) for dim in shape)) == 1:
        return tokens.unsqueeze(1)
    return tokens


def _concat_token_chunks(chunks: Sequence[Any]) -> Any:
    if not chunks:
        return []
    first = chunks[0]
    try:
        import torch

        if hasattr(first, "shape"):
            return torch.cat(list(chunks), dim=1)
    except ImportError:
        pass
    rows: list[list[Any]] = []
    for chunk in chunks:
        chunk_rows = _to_python_sequence_container(chunk)
        if chunk_rows and not _is_sequence(chunk_rows[0]):
            chunk_rows = [chunk_rows]
        if not rows:
            rows = [list(row) for row in chunk_rows]
        else:
            for row_index, row in enumerate(chunk_rows):
                rows[row_index].extend(row)
    return rows


def _iter_generated_token_chunks(tokens: Any, chunk_size: int) -> Iterable[Any]:
    shape = getattr(tokens, "shape", None)
    if shape is not None:
        rank = len(tuple(int(dim) for dim in shape))
        sequence_length = int(shape[1]) if rank >= 2 else int(shape[0])
        for start in range(0, sequence_length, chunk_size):
            if rank == 1:
                yield tokens[start : start + chunk_size].unsqueeze(0)
            else:
                yield tokens[:, start : start + chunk_size]
        return

    rows = _to_python_sequence_container(tokens)
    if rows and not _is_sequence(rows[0]):
        rows = [rows]
    sequence_length = max((len(row) for row in rows), default=0)
    for start in range(0, sequence_length, chunk_size):
        yield [list(row)[start : start + chunk_size] for row in rows]


def _append_sequence_values(prefix: Any, suffix: Any) -> Any:
    try:
        import torch

        if hasattr(prefix, "shape") or hasattr(suffix, "shape"):
            if not hasattr(prefix, "shape"):
                prefix = torch.as_tensor(prefix, dtype=getattr(suffix, "dtype", None))
            if not hasattr(suffix, "shape"):
                suffix = torch.as_tensor(
                    suffix,
                    dtype=getattr(prefix, "dtype", None),
                    device=getattr(prefix, "device", None),
                )
            return torch.cat([prefix, suffix.to(device=prefix.device, dtype=prefix.dtype)], dim=1)
    except ImportError:
        pass
    if _is_sequence(prefix) and _is_sequence(suffix):
        return [
            list(prefix_row) + list(suffix_row)
            for prefix_row, suffix_row in zip(prefix, suffix, strict=False)
        ]
    raise TypeError("Could not append generated embeddings to the input embeddings.")


def _decode_generated_sequences(
    tokenizer: Any,
    output_ids: Any,
    *,
    force_batch: bool = False,
) -> str | list[str]:
    batch_decode = getattr(tokenizer, "batch_decode", None)
    if force_batch:
        if callable(batch_decode):
            return [
                str(text)
                for text in _call_decode_with_supported_kwargs(
                    batch_decode,
                    output_ids,
                    {"skip_special_tokens": True},
                )
            ]
        return [str(tokenizer.decode(row, skip_special_tokens=True)) for row in output_ids]
    return str(tokenizer.decode(output_ids[0], skip_special_tokens=True))


def _prepend_bos_token(
    tokens: Any,
    tokenizer: Any,
    *,
    pad_token_id: int | None = None,
    padding_side: str | None = None,
) -> Any:
    bos_token_id = getattr(tokenizer, "bos_token_id", None)
    if bos_token_id is None:
        return tokens
    if pad_token_id is None:
        pad_token_id = getattr(tokenizer, "pad_token_id", None)
    if padding_side is None:
        padding_side = getattr(tokenizer, "padding_side", None)
    try:
        import torch

        if hasattr(tokens, "shape"):
            bos = torch.full(
                (tokens.shape[0], 1),
                int(bos_token_id),
                dtype=tokens.dtype,
                device=tokens.device,
            )
            if padding_side == "left" and pad_token_id is not None:
                pad_mask = tokens == int(pad_token_id)
                non_pad_mask = ~pad_mask
                first_non_pad = non_pad_mask.to(dtype=torch.long).argmax(dim=1)
                first_non_pad = first_non_pad.masked_fill(
                    ~non_pad_mask.any(dim=1),
                    tokens.shape[1],
                )
                rows = []
                for row_index in range(tokens.shape[0]):
                    insert_at = int(first_non_pad[row_index].item())
                    row = tokens[row_index]
                    rows.append(torch.cat([row[:insert_at], bos[row_index], row[insert_at:]]))
                return torch.stack(rows, dim=0)
            return torch.cat([bos, tokens], dim=1)
    except ImportError:
        pass
    if _is_sequence(tokens):
        if tokens and _is_sequence(tokens[0]):
            if padding_side == "left" and pad_token_id is not None:
                rows = []
                for row in tokens:
                    insert_at = next(
                        (
                            index
                            for index, token in enumerate(row)
                            if int(token) != int(pad_token_id)
                        ),
                        len(row),
                    )
                    rows.append([*row[:insert_at], bos_token_id, *row[insert_at:]])
                return rows
            return [[bos_token_id, *row] for row in tokens]
        return [bos_token_id, *tokens]
    return tokens


def _tokenizer_effective_pad_token_id(tokenizer: Any) -> int | None:
    pad_token_id = getattr(tokenizer, "pad_token_id", None)
    if pad_token_id is not None:
        return int(pad_token_id)
    eos_token_id = getattr(tokenizer, "eos_token_id", None)
    if eos_token_id is not None:
        return int(eos_token_id)
    bos_token_id = getattr(tokenizer, "bos_token_id", None)
    if bos_token_id is not None:
        return int(bos_token_id)
    return None


def _attention_mask_from_tokens(
    tokens: Any,
    pad_token_id: int | None,
    *,
    prepend_bos: bool,
    padding_side: str = "right",
    bos_token_id: int | None = None,
) -> Any | None:
    if pad_token_id is None:
        return None
    try:
        import torch

        if hasattr(tokens, "shape"):
            mask = (tokens != int(pad_token_id)).to(dtype=torch.long)
            if prepend_bos and bos_token_id is not None and mask.shape[-1] > 0:
                if padding_side == "left":
                    if int(bos_token_id) == int(pad_token_id):
                        non_pad_mask = tokens != int(pad_token_id)
                        first_non_pad = non_pad_mask.to(dtype=torch.long).argmax(dim=1)
                        bos_positions = first_non_pad - 1
                        bos_positions = bos_positions.masked_fill(
                            ~non_pad_mask.any(dim=1),
                            tokens.shape[1] - 1,
                        )
                        for row_index, bos_position in enumerate(bos_positions.tolist()):
                            if bos_position >= 0:
                                mask[row_index, int(bos_position)] = 1
                    else:
                        mask = mask | (tokens == int(bos_token_id)).to(dtype=torch.long)
                else:
                    mask[..., 0] = 1
            return mask
    except ImportError:
        pass
    if _is_sequence(tokens):
        if tokens and _is_sequence(tokens[0]):
            mask_rows = [
                [0 if int(token) == int(pad_token_id) else 1 for token in row] for row in tokens
            ]
            if prepend_bos:
                for row in mask_rows:
                    if row and padding_side != "left":
                        row[0] = 1
            if prepend_bos and padding_side == "left" and bos_token_id is not None:
                for row_mask, row_tokens in zip(mask_rows, tokens, strict=False):
                    if int(bos_token_id) == int(pad_token_id):
                        non_pad_indices = [
                            index
                            for index, token in enumerate(row_tokens)
                            if int(token) != int(pad_token_id)
                        ]
                        bos_index = (
                            (non_pad_indices[0] - 1) if non_pad_indices else len(row_tokens) - 1
                        )
                        if bos_index >= 0:
                            row_mask[bos_index] = 1
                    else:
                        for index, token in enumerate(row_tokens):
                            if int(token) == int(bos_token_id):
                                row_mask[index] = 1
            return mask_rows
        mask = [0 if int(token) == int(pad_token_id) else 1 for token in tokens]
        if prepend_bos and mask and padding_side != "left":
            mask[0] = 1
        if prepend_bos and padding_side == "left" and bos_token_id is not None:
            if int(bos_token_id) == int(pad_token_id):
                non_pad_indices = [
                    index for index, token in enumerate(tokens) if int(token) != int(pad_token_id)
                ]
                bos_index = (non_pad_indices[0] - 1) if non_pad_indices else len(tokens) - 1
                if bos_index >= 0:
                    mask[bos_index] = 1
            else:
                for index, token in enumerate(tokens):
                    if int(token) == int(bos_token_id):
                        mask[index] = 1
        return mask
    return None


def _tokenize_text_batch(tokenizer: Any, text: Any) -> Any:
    kwargs = {"return_tensors": "pt"}
    if not isinstance(text, str):
        kwargs["padding"] = True
    try:
        return tokenizer(text, **kwargs)
    except TypeError:
        kwargs.pop("padding", None)
        return tokenizer(text, **kwargs)


def _normalize_model_batch(batch: Any) -> dict[str, Any]:
    if isinstance(batch, Mapping):
        return dict(batch)
    if isinstance(batch, str):
        return {"text": batch}
    if _is_text_batch(batch):
        return {"text": batch}
    if _looks_like_token_ids(batch):
        return {"input_ids": _ensure_token_batch_dim(batch)}
    raise TypeError(
        "Model inputs must be a mapping, text string or batch, or token ids shaped "
        "[pos] or [batch, pos]."
    )


def _looks_like_token_ids(value: Any) -> bool:
    if isinstance(value, Integral):
        return True
    if isinstance(value, str | bytes):
        return False
    shape = getattr(value, "shape", None)
    if shape is not None:
        return len(tuple(int(dim) for dim in shape)) <= 2
    if isinstance(value, Sequence):
        return True
    return False


def _ensure_token_batch_dim(tokens: Any) -> Any:
    shape = getattr(tokens, "shape", None)
    if shape is not None:
        rank = len(tuple(int(dim) for dim in shape))
        if rank == 0:
            unsqueeze = getattr(tokens, "unsqueeze", None)
            return unsqueeze(0).unsqueeze(0) if callable(unsqueeze) else [[tokens]]
        if rank == 1:
            unsqueeze = getattr(tokens, "unsqueeze", None)
            return unsqueeze(0) if callable(unsqueeze) else [tokens]
        return tokens
    if isinstance(tokens, Integral):
        return [[int(tokens)]]
    if isinstance(tokens, Sequence) and not isinstance(tokens, str | bytes):
        token_list = list(tokens)
        if not token_list:
            return [[]]
        if isinstance(token_list[0], Sequence) and not isinstance(token_list[0], str | bytes):
            return token_list
        return [token_list]
    return tokens


def _coerce_token_model_input(tokens: Any, *, device: Any = None) -> Any:
    """Convert Python token containers to model-ready integer tensors when torch is available."""
    try:
        import torch

        if isinstance(tokens, torch.Tensor):
            return tokens.to(device) if device is not None else tokens
        tensor = torch.as_tensor(tokens, dtype=torch.long)
        return tensor.to(device) if device is not None else tensor
    except Exception:
        return tokens


def _coerce_token_mask_fields(model_inputs: dict[str, Any], *, device: Any = None) -> None:
    for key in ("attention_mask", "position_ids", "token_type_ids", "labels"):
        if key in model_inputs:
            model_inputs[key] = _coerce_token_model_input(model_inputs[key], device=device)


def _shape_of_token_ids(tokens: Any) -> tuple[int, ...] | None:
    shape = getattr(tokens, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(tokens, Sequence) and not isinstance(tokens, str | bytes):
        token_list = list(tokens)
        if not token_list:
            return (0,)
        child_shape = _shape_of_token_ids(token_list[0])
        if child_shape is None:
            return (len(token_list),)
        return (len(token_list), *child_shape)
    return None


def _flatten_single_token_sequence(tokens: Any) -> list[int]:
    shape = _shape_of_token_ids(tokens)
    values = tokens.tolist() if hasattr(tokens, "tolist") else tokens
    if shape is None:
        return [int(values)]
    if len(shape) == 0:
        return [int(values)]
    if len(shape) == 1:
        return [int(token) for token in list(values)]
    if len(shape) == 2 and shape[0] == 1:
        row = values[0] if _is_sequence(values) else values
        return [int(token) for token in list(row)]
    raise ValueError(f"Expected a rank-1 token sequence or [1, pos], got shape {shape!r}.")


def _single_token_list(tokens: Any) -> list[int]:
    shape = _shape_of_token_ids(tokens)
    values = tokens.tolist() if hasattr(tokens, "tolist") else tokens
    if shape is None or len(shape) == 0:
        return [int(values)]
    if len(shape) == 1:
        return [int(token) for token in list(values)]
    if len(shape) == 2 and shape[0] == 1:
        row = values[0] if _is_sequence(values) else values
        return [int(token) for token in list(row)]
    raise ValueError(f"Invalid token shape for token string conversion: {shape!r}.")


def _canonical_top_level_hook_name(layer: LayerRef) -> str | None:
    if not isinstance(layer, str):
        return None
    return _TOP_LEVEL_HOOK_ALIASES.get(layer)


def _top_level_component_name(name: str) -> str:
    if name == "hook_embed":
        return "embed"
    if name == "hook_pos_embed":
        return "pos_embed"
    if name == "ln_final.hook_scale":
        return "scale"
    return name.removeprefix("hook_")


def _top_level_hook_is_resolvable(model: Any, name: str) -> bool:
    return _resolve_top_level_hook_module(model, name) is not None


def _top_level_hook_names(model: Any) -> list[str]:
    return [
        name
        for name in ("hook_embed", "hook_pos_embed", "ln_final.hook_scale")
        if _top_level_hook_is_resolvable(model, name)
    ]


def _resolve_top_level_hook_module(model: Any, name: str) -> Any | None:
    hook_name = _canonical_top_level_hook_name(name)
    if hook_name is None:
        return None
    if hook_name == "hook_embed":
        return _input_embedding_module(model)
    if hook_name == "hook_pos_embed":
        return _first_module_from_paths(model, _POSITION_EMBEDDING_MODULE_PATHS)
    if hook_name == "ln_final.hook_scale":
        return _first_module_from_paths(model, _FINAL_NORM_MODULE_PATHS)
    return None


def _input_embedding_module(model: Any) -> Any | None:
    get_input_embeddings = getattr(model, "get_input_embeddings", None)
    if callable(get_input_embeddings):
        try:
            module = get_input_embeddings()
        except Exception:
            module = None
        if _is_hookable_module(module):
            return module
    return _first_module_from_paths(model, _TOKEN_EMBEDDING_MODULE_PATHS)


def _first_module_from_paths(model: Any, paths: Sequence[str]) -> Any | None:
    for path in paths:
        try:
            module = resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
        if _is_hookable_module(module):
            return module
    return None


def _is_hookable_module(module: Any) -> bool:
    return module is not None and callable(getattr(module, "register_forward_hook", None))


def make_final_norm_scale_cache_hook(
    cache: ActivationCache,
    name: str,
    *,
    detach: bool = True,
    clone: bool = False,
    device: Any = None,
    pos_slice: Any = None,
    remove_batch_dim: bool = False,
) -> HookFn:
    """Create a cache hook for TransformerLens-style final norm scales."""
    normalized_pos_slice = _normalize_cache_pos_slice(pos_slice)

    def cache_hook(module: Any, inputs: tuple[Any, ...], output: Any) -> None:
        scale = _final_norm_scale_from_hook(module, inputs, output)
        if remove_batch_dim:
            scale = _remove_singleton_batch(scale)
            cache.has_batch_dim = False
        if normalized_pos_slice is not None:
            scale = _slice_tensor_like_dim(
                scale,
                normalized_pos_slice,
                dim=_cache_pos_dim_for_name(name, scale),
            )
        cache.store(name, scale, detach=detach, clone=clone, device=device)
        return None

    return cache_hook


def _final_norm_scale_from_hook(module: Any, inputs: tuple[Any, ...], output: Any) -> Any:
    source = inputs[0] if inputs else output
    scale = _final_norm_scale_from_input(module, source)
    if scale is not None:
        return scale
    return output


def _final_norm_scale_from_input(module: Any, source: Any) -> Any | None:
    try:
        import torch

        if isinstance(source, torch.Tensor):
            epsilon = float(getattr(module, "variance_epsilon", getattr(module, "eps", 1e-5)))
            source_float = source.float() if not torch.is_floating_point(source) else source
            if _module_is_centered_layer_norm(module):
                centered = source_float - source_float.mean(dim=-1, keepdim=True)
                variance = centered.pow(2).mean(dim=-1, keepdim=True)
            else:
                variance = source_float.pow(2).mean(dim=-1, keepdim=True)
            return torch.sqrt(variance + epsilon).to(dtype=source.dtype, device=source.device)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(source, "shape") and type(source).__module__.split(".")[0] == "numpy":
            array = np.asarray(source)
            epsilon = float(getattr(module, "variance_epsilon", getattr(module, "eps", 1e-5)))
            if _module_is_centered_layer_norm(module):
                array = array - array.mean(axis=-1, keepdims=True)
            return np.sqrt(np.mean(array * array, axis=-1, keepdims=True) + epsilon)
    except Exception:
        pass
    return _nested_final_norm_scale(module, source)


def _replace_final_norm_output_from_scale(
    module: Any,
    inputs: tuple[Any, ...],
    output: Any,
    patched_scale: Any,
) -> Any:
    if not inputs:
        return output
    source = inputs[0]
    try:
        import torch

        if isinstance(source, torch.Tensor):
            if not isinstance(patched_scale, torch.Tensor):
                patched_scale = torch.as_tensor(
                    patched_scale,
                    dtype=source.dtype,
                    device=source.device,
                )
            base = source.float() if not torch.is_floating_point(source) else source
            if _module_is_centered_layer_norm(module):
                base = base - base.mean(dim=-1, keepdim=True)
            normalized = base / patched_scale
            weight = getattr(module, "weight", None)
            if isinstance(weight, torch.Tensor):
                normalized = normalized * weight
            bias = getattr(module, "bias", None)
            if isinstance(bias, torch.Tensor):
                normalized = normalized + bias
            return normalized.to(dtype=getattr(output, "dtype", source.dtype))
    except Exception:
        pass
    return output


def _module_is_centered_layer_norm(module: Any) -> bool:
    try:
        import torch

        if isinstance(module, torch.nn.LayerNorm):
            return True
    except Exception:
        pass
    module_name = type(module).__name__.lower()
    if "layernorm" in module_name or "layer_norm" in module_name:
        return True
    return "rms" not in module_name


def _nested_final_norm_scale(module: Any, source: Any) -> Any | None:
    shape = shape_of(source)
    if not shape:
        return None
    epsilon = float(getattr(module, "variance_epsilon", getattr(module, "eps", 1e-5)))

    def scale_vector(vector: Any) -> list[float]:
        values = [float(item) for item in list(vector)]
        if not values:
            return [0.0]
        if _module_is_centered_layer_norm(module):
            mean = sum(values) / len(values)
            values = [value - mean for value in values]
        variance = sum(value * value for value in values) / len(values)
        return [math.sqrt(variance + epsilon)]

    return _map_nested_final_vectors(source, scale_vector)


def _map_nested_final_vectors(value: Any, fn: Callable[[Any], Any]) -> Any:
    if not _is_sequence(value):
        return value
    if not value or not _is_sequence(value[0]):
        return fn(value)
    return [_map_nested_final_vectors(item, fn) for item in value]


def _slice_tensor_like_dim(value: Any, index: Any, *, dim: int) -> Any:
    index = _normalize_wrapper_slice_index(index)
    shape = shape_of(value)
    if dim < 0:
        dim = len(shape) + dim
    normalized = tuple(index if axis == dim else slice(None) for axis in range(len(shape)))
    try:
        return value[normalized]
    except Exception:
        pass
    return _slice_nested_dim(value, index, dim)


def _normalize_wrapper_slice_index(index: Any) -> Any:
    if index is None:
        return slice(None)
    slice_value = getattr(index, "slice", None)
    mode = getattr(index, "mode", None)
    if mode == "identity":
        return slice(None)
    if slice_value is not None:
        return slice_value
    if isinstance(index, tuple):
        return slice(*index)
    return index


def _slice_nested_dim(value: Any, index: Any, dim: int) -> Any:
    if dim <= 0:
        return value[index]
    return [_slice_nested_dim(item, index, dim - 1) for item in value]


def _cache_pos_dim_for_name(name: str, activation: Any) -> int:
    shape = shape_of(activation)
    if not shape:
        return 0
    if name == "ln_final.hook_scale":
        return 1 if len(shape) >= 3 else 0
    return -2


def _remove_singleton_batch(value: Any) -> Any:
    shape = shape_of(value)
    if shape and shape[0] != 1:
        raise ValueError(f"Expected singleton batch dimension, got shape {shape!r}.")
    return _slice_tensor_like_dim(value, 0, dim=0)


def _call_top_level_hook(
    hook_fn: HookFn,
    *,
    activation: Any,
    hook_name: str,
    hook_context: _TopLevelHookContext,
) -> Any:
    component = _top_level_component_name(hook_name)
    hook_kwargs = {
        "activation": activation,
        "output": activation,
        "component": component,
        "layer": None,
        "hook_name": component,
        "transformer_lens_name": hook_name,
        "hook": hook_context,
    }
    return call_user_hook(
        hook_fn,
        hook_kwargs,
        positional_arg_options=((activation, hook_context), (activation,)),
    )


def _call_top_level_backward_hook(
    hook_fn: HookFn,
    *,
    grad: Any,
    hook_name: str,
    hook_context: _TopLevelHookContext,
) -> Any:
    component = _top_level_component_name(hook_name)
    hook_kwargs = {
        "activation": grad,
        "grad": grad,
        "output": grad,
        "component": component,
        "layer": None,
        "hook_name": component,
        "transformer_lens_name": hook_name,
        "hook": hook_context,
    }
    return call_user_hook(
        hook_fn,
        hook_kwargs,
        positional_arg_options=((grad, hook_context), (grad,)),
    )


def _call_raw_backward_hook(
    hook_fn: HookFn,
    *,
    grad: Any,
    hook_context: _RawHookContext,
) -> Any:
    hook_kwargs = {
        "activation": grad,
        "grad": grad,
        "output": grad,
        "hook": hook_context,
        "hook_name": hook_context.name,
        "transformer_lens_name": hook_context.name,
    }
    return call_user_hook(
        hook_fn,
        hook_kwargs,
        positional_arg_options=((grad, hook_context), (grad,)),
    )


def _make_raw_output_backward_registration_hook(
    hook_fn: HookFn,
    hook_context: _TopLevelHookContext,
    *,
    hook_name: str,
) -> Callable[[Any, Any, Any], None]:
    def hook(_module: Any, _inputs: Any, output: Any) -> None:
        tensor = first_output(output)
        _register_tensor_backward_hook(
            tensor,
            lambda grad: _call_top_level_backward_hook(
                hook_fn,
                grad=grad,
                hook_name=hook_name,
                hook_context=hook_context,
            ),
        )
        return None

    return hook


def _register_raw_activation_backward_hook(
    module: Any,
    hook_fn: HookFn,
    *,
    hook_context: _RawHookContext | None,
    use_input: bool,
    prepend: bool = False,
) -> _BackwardHookRegistrationHandle:
    if hook_context is None:
        hook_context = _RawHookContext(getattr(module, "name", type(module).__name__))

    if use_input:

        def pre_hook(_module: Any, inputs: Any) -> None:
            if not inputs:
                return None
            tensor = first_output(inputs[0])
            _register_tensor_backward_hook(
                tensor,
                lambda grad: _call_raw_backward_hook(
                    hook_fn,
                    grad=grad,
                    hook_context=hook_context,
                ),
            )
            return None

        return _BackwardHookRegistrationHandle(
            _register_module_forward_pre_hook(module, pre_hook, prepend=prepend),
            (hook_context,),
        )

    def hook(_module: Any, _inputs: Any, output: Any) -> None:
        tensor = first_output(output)
        _register_tensor_backward_hook(
            tensor,
            lambda grad: _call_raw_backward_hook(
                hook_fn,
                grad=grad,
                hook_context=hook_context,
            ),
        )
        return None

    return _BackwardHookRegistrationHandle(
        _register_module_forward_hook(module, hook, prepend=prepend),
        (hook_context,),
    )


def _make_component_output_backward_registration_hook(
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: Any,
    model: Any,
    hook_context: ComponentHookContext,
) -> Callable[[Any, Any, Any], None]:
    def hook(module: Any, _inputs: Any, output: Any) -> None:
        raw_output = first_output(output)
        activation = extract_component_activation(output, spec, model)
        _register_component_tensor_backward_hook(
            raw_output,
            activation,
            hook_fn=hook_fn,
            component_ref=component_ref,
            architecture=architecture,
            spec=spec,
            model=model,
            hook_context=hook_context,
            module=module,
        )
        return None

    return hook


def _make_component_input_backward_registration_hook(
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: Any,
    model: Any,
    hook_context: ComponentHookContext,
) -> Callable[[Any, Any], None]:
    def hook(module: Any, inputs: Any) -> None:
        if not inputs:
            return None
        raw_activation = inputs[0]
        activation = transform_component_activation(
            raw_activation,
            spec,
            model,
            module=module,
            component_ref=component_ref,
            architecture=architecture,
        )
        _register_component_tensor_backward_hook(
            raw_activation,
            activation,
            hook_fn=hook_fn,
            component_ref=component_ref,
            architecture=architecture,
            spec=spec,
            model=model,
            hook_context=hook_context,
            module=module,
        )
        return None

    return hook


def _register_component_tensor_backward_hook(
    raw_activation: Any,
    activation: Any,
    *,
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: Any,
    model: Any,
    hook_context: ComponentHookContext,
    module: Any,
) -> None:
    if raw_activation is activation:
        _register_tensor_backward_hook(
            raw_activation,
            lambda grad: call_component_hook(
                hook_fn,
                activation=grad,
                component_ref=component_ref,
                architecture=architecture,
                hook_context=hook_context,
            ),
        )
        return

    def activation_grad_hook(grad: Any) -> Any:
        patched = call_component_hook(
            hook_fn,
            activation=grad,
            component_ref=component_ref,
            architecture=architecture,
            hook_context=hook_context,
        )
        return grad if patched is None else patched

    def raw_grad_hook(raw_grad: Any) -> Any:
        try:
            with _grad_context(enabled=True):
                detached_raw = raw_activation.detach().requires_grad_(True)
                transformed = transform_component_activation(
                    detached_raw,
                    spec,
                    model,
                    module=module,
                    component_ref=component_ref,
                    architecture=architecture,
                )
                transformed.backward(activation_grad_hook(activation.detach()), retain_graph=False)
                return detached_raw.grad
        except Exception:
            merged = merge_component_activation(
                activation_grad_hook(
                    transform_component_activation(
                        raw_grad,
                        spec,
                        model,
                        module=module,
                        component_ref=component_ref,
                        architecture=architecture,
                    )
                ),
                raw_grad,
                spec,
                model,
            )
            return merged

    _register_tensor_backward_hook(raw_activation, raw_grad_hook)


def _register_tensor_backward_hook(tensor: Any, hook_fn: Callable[[Any], Any]) -> None:
    register_hook = getattr(tensor, "register_hook", None)
    requires_grad = getattr(tensor, "requires_grad", False)
    if not callable(register_hook) or not requires_grad:
        return

    def tensor_hook(grad: Any) -> Any:
        patched = hook_fn(grad)
        return grad if patched is None else patched

    try:
        register_hook(tensor_hook)
    except RuntimeError:
        return


def _backward_scalar_output(output: Any) -> None:
    target = _scalar_backward_target(output)
    if target is None:
        raise ValueError("incl_bwd=True requires the selected model output to be a scalar loss.")
    backward = getattr(target, "backward", None)
    if callable(backward):
        backward()
        return
    raise ValueError("incl_bwd=True requires a differentiable scalar output with backward().")


def _scalar_backward_target(output: Any) -> Any | None:
    if _is_differentiable_scalar(output):
        return output
    if isinstance(output, Mapping):
        loss = output.get("loss")
        if _is_differentiable_scalar(loss):
            return loss
        return None
    if isinstance(output, tuple | list):
        for value in reversed(output):
            if _is_differentiable_scalar(value):
                return value
    return None


def _is_differentiable_scalar(value: Any) -> bool:
    if value is None or not _looks_like_scalar_loss(value):
        return False
    backward = getattr(value, "backward", None)
    return callable(backward)


def _candidate_hook_names(model: Any, adapter: Any, *, for_cache: bool | None = None) -> list[str]:
    names: list[str] = _top_level_hook_names(model)
    n_layers = _infer_model_layers(model)
    for layer in range(n_layers):
        for component in adapter.supported_components(for_cache=for_cache):
            names.append(_adapter_transformer_lens_component_name(adapter, component, layer))
            names.append(f"layer_{layer}.{component}")
    named_modules = getattr(model, "named_modules", None)
    if callable(named_modules):
        names.extend(name for name, _module in named_modules())
    return list(dict.fromkeys(names))


def _default_cache_hook_names(model: Any, adapter: Any) -> list[str]:
    """Return TL-style component hook names for default full-cache runs."""
    names: list[str] = _top_level_hook_names(model)
    n_layers = _infer_model_layers(model)
    for layer in range(n_layers):
        for component in adapter.supported_components(for_cache=True):
            if _default_cache_excludes_component(component):
                continue
            name = _adapter_transformer_lens_component_name(adapter, component, layer)
            if not _component_hook_is_resolvable(model, adapter, name):
                continue
            names.append(name)
    return names


def _adapter_transformer_lens_component_name(adapter: Any, component: str, layer: int) -> str:
    parse_component_ref = getattr(adapter, "parse_component_ref", None)
    if callable(parse_component_ref):
        component_ref = parse_component_ref(f"layer_{layer}.{component}")
        if component_ref is not None:
            return component_ref.transformer_lens_name
    return transformer_lens_component_name(component, layer)


def _default_cache_excludes_component(component: str) -> bool:
    return (
        component in _DEFAULT_CACHE_EXCLUDED_COMPONENTS
        or component.endswith("_attn_scores")
        or component == "mlp_in"
        or component.endswith("_mlp_in")
        or component == "attn_in"
        or component.endswith("_attn_in")
        or component in {"q_input", "k_input", "v_input"}
        or component.endswith(("_q_input", "_k_input", "_v_input"))
    )


def _cache_hook_requires_runtime_flag(name: str) -> bool:
    return name.endswith(
        (
            "hook_q_input",
            "hook_k_input",
            "hook_v_input",
            "hook_attn_in",
            "hook_cross_attn_in",
            "hook_mlp_in",
        )
    )


def _component_hook_is_resolvable(model: Any, adapter: Any, name: str) -> bool:
    component_ref = adapter.parse_component_ref(name)
    if component_ref is None:
        return False
    try:
        adapter.get_component(model, component_ref)
    except (KeyError, NotImplementedError):
        return False
    return True


def _filter_hook_names(
    names: Sequence[str],
    names_filter: NamesFilter,
    *,
    adapter: Any = None,
) -> list[str]:
    matched = [name for name in names if matches_names_filter(name, names_filter)]
    return _dedupe_hook_aliases(matched, adapter)


def _dedupe_hook_aliases(names: Sequence[str], adapter: Any = None) -> list[str]:
    seen: set[tuple[Any, ...]] = set()
    deduped: list[str] = []
    for name in names:
        key = _canonical_hook_key(name, adapter)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(name)
    return deduped


def _canonical_hook_key(name: str, adapter: Any = None) -> tuple[Any, ...]:
    top_level_name = _canonical_top_level_hook_name(name)
    if top_level_name is not None:
        return ("top_level", top_level_name)
    if adapter is not None:
        component_ref = adapter.parse_component_ref(name)
        if component_ref is not None:
            return ("component", component_ref.layer, component_ref.component)
    return ("name", name)


def _format_cache_result(
    cache: dict[str, Any] | ActivationCache,
    *,
    model: Any,
    return_cache_object: bool,
    remove_batch_dim: bool,
) -> dict[str, Any] | ActivationCache:
    if isinstance(cache, ActivationCache):
        activation_cache = cache
        activation_cache.model = model
        if remove_batch_dim:
            activation_cache.remove_batch_dim()
        if return_cache_object:
            return activation_cache
        return activation_cache.cache_dict
    if not return_cache_object and not remove_batch_dim:
        return cache
    activation_cache = ActivationCache(cache, model=model, has_batch_dim=True)
    if remove_batch_dim:
        activation_cache.remove_batch_dim()
    if return_cache_object:
        return activation_cache
    return activation_cache.cache_dict


def _coerce_activation_cache(
    cache: ActivationCache | dict[str, Any] | None,
    *,
    model: Any,
    has_batch_dim: bool,
) -> ActivationCache:
    if cache is None:
        return ActivationCache(model=model, has_batch_dim=has_batch_dim)
    if isinstance(cache, ActivationCache):
        return cache
    return ActivationCache(cache, model=model, has_batch_dim=has_batch_dim, canonicalize=False)


def _looks_like_external_cache(value: Any) -> bool:
    return isinstance(value, ActivationCache) or isinstance(value, dict)


def _normalize_cache_pos_slice(pos_slice: Any) -> Any:
    if isinstance(pos_slice, int):
        return [pos_slice]
    return pos_slice


def _merge_extra_model_kwargs(batch: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_model_batch(batch)
    tokenization_kwargs = _pop_tokenization_kwargs(kwargs)
    normalized.update(tokenization_kwargs)
    model_kwargs = dict(normalized.get("model_kwargs", {}))
    model_kwargs.update(kwargs)
    normalized["model_kwargs"] = model_kwargs
    return normalized


def _merge_transformer_lens_forward_positionals(
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
    *,
    return_type: str | None | object = _DEFAULT_RETURN_TYPE,
    loss_per_token: bool | object = _DEFAULT_LOSS_PER_TOKEN,
    default_return_type: str | None | object = _DEFAULT_RETURN_TYPE,
) -> dict[str, Any]:
    if len(args) > len(_TL_FORWARD_POSITIONAL_ARG_NAMES):
        raise TypeError(
            "Too many positional forward arguments. Expected at most "
            f"{len(_TL_FORWARD_POSITIONAL_ARG_NAMES)} after the model input."
        )
    merged = dict(kwargs)
    for name, value in zip(_TL_FORWARD_POSITIONAL_ARG_NAMES, args, strict=False):
        if name in merged:
            raise TypeError(f"Got multiple values for forward argument {name!r}.")
        merged[name] = value
    if return_type is not _DEFAULT_RETURN_TYPE:
        if "return_type" in merged:
            raise TypeError("Got multiple values for forward argument 'return_type'.")
        merged["return_type"] = return_type
    elif default_return_type is not _DEFAULT_RETURN_TYPE and "return_type" not in merged:
        merged["return_type"] = default_return_type
    if loss_per_token is not _DEFAULT_LOSS_PER_TOKEN:
        if "loss_per_token" in merged:
            raise TypeError("Got multiple values for forward argument 'loss_per_token'.")
        merged["loss_per_token"] = loss_per_token
    return merged


def _split_run_with_cache_positionals(
    model_args: Sequence[Any],
    *,
    layers: Sequence[LayerRef] | LayerRef | None,
) -> tuple[list[LayerRef] | None, tuple[Any, ...]]:
    normalized_layers = _normalize_cache_layers_arg(layers)
    if not model_args:
        return normalized_layers, ()
    if normalized_layers is not None:
        return normalized_layers, tuple(model_args)

    first, *rest = model_args
    if _looks_like_positional_return_type(first):
        return None, tuple(model_args)
    return _normalize_cache_layers_arg(first), tuple(rest)


def _normalize_cache_layers_arg(
    layers: Sequence[LayerRef] | LayerRef | None,
) -> list[LayerRef] | None:
    if layers is None:
        return None
    if isinstance(layers, str | int):
        return [layers]
    if _is_tuple_component_ref(layers):
        return [layers]
    return list(layers)


def _looks_like_positional_return_type(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.lower() in _RETURN_TYPE_ALIASES
    return False


def _is_tuple_component_ref(value: Any) -> bool:
    return (
        isinstance(value, tuple)
        and len(value) >= 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    )


def _pop_tokenization_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    tokenization_kwargs: dict[str, Any] = {}
    for key in ("prepend_bos", "padding_side", "truncate"):
        if key in kwargs:
            tokenization_kwargs[key] = kwargs.pop(key)
    return tokenization_kwargs


def _model_kwargs_without_tokenization(batch: Mapping[str, Any]) -> dict[str, Any]:
    model_kwargs = dict(batch.get("model_kwargs", {}))
    for key in ("prepend_bos", "padding_side", "truncate"):
        model_kwargs.pop(key, None)
    return model_kwargs


def _resolve_return_type(batch: Any, return_type: str | None | object) -> str | None:
    if return_type is not _DEFAULT_RETURN_TYPE:
        return _normalize_return_type(return_type)
    if isinstance(batch, Mapping):
        return "model_output"
    return "logits"


def _resolve_cache_all(
    batch: Any,
    layers: Sequence[LayerRef] | None,
    names_filter: NamesFilter,
    cache_all: bool | object,
) -> bool:
    if cache_all is not _DEFAULT_CACHE_ALL:
        return bool(cache_all)
    if layers is not None or names_filter is not None:
        return False
    return not isinstance(batch, Mapping)


def _resolve_return_cache_object(batch: Any, return_cache_object: bool | object) -> bool:
    if return_cache_object is not _DEFAULT_RETURN_CACHE_OBJECT:
        return bool(return_cache_object)
    return not isinstance(batch, Mapping)


def _normalize_return_type(return_type: str | None | object) -> str | None:
    if return_type is None:
        return None
    if not isinstance(return_type, str):
        raise ValueError(f"Unsupported return_type {return_type!r}.")
    normalized = return_type.lower()
    if normalized not in _RETURN_TYPE_ALIASES:
        raise ValueError(
            "return_type must be one of 'logits', 'loss', 'both', 'model_output', 'raw', or None."
        )
    return _RETURN_TYPE_ALIASES[normalized]


def _format_model_output(
    output: Any,
    return_type: str | None,
    *,
    model_inputs: Mapping[str, Any] | None = None,
    loss_per_token: bool = False,
) -> Any:
    if return_type is None:
        return None
    if return_type == "model_output":
        return output
    if return_type == "logits":
        logits = _extract_output_field(output, "logits")
        if logits is None:
            raise RuntimeError("Model output does not expose logits.")
        return logits
    if return_type == "loss":
        return _extract_or_compute_loss(
            output,
            model_inputs,
            loss_per_token=loss_per_token,
        )
    if return_type == "both":
        logits = _extract_output_field(output, "logits")
        if logits is None:
            raise RuntimeError("Model output does not expose logits.")
        return logits, _extract_or_compute_loss(
            output,
            model_inputs,
            logits=logits,
            loss_per_token=loss_per_token,
        )
    raise ValueError(f"Unsupported return_type {return_type!r}.")


def _extract_or_compute_loss(
    output: Any,
    model_inputs: Mapping[str, Any] | None,
    *,
    logits: Any | None = None,
    loss_per_token: bool = False,
) -> Any:
    loss = _extract_output_field(output, "loss")
    if loss is not None and not loss_per_token:
        return loss
    if logits is None:
        logits = _extract_output_field(output, "logits")
    if logits is None or model_inputs is None:
        raise RuntimeError("Model output does not expose loss.")
    input_ids = model_inputs.get("input_ids")
    if input_ids is None:
        raise RuntimeError(
            "Model output does not expose loss and causal LM loss cannot be computed "
            "without input_ids."
        )
    try:
        import torch
        import torch.nn.functional as F
    except ImportError:
        from SafeLens.core.analysis import lm_cross_entropy_loss

        return lm_cross_entropy_loss(
            logits,
            input_ids,
            model_inputs.get("attention_mask"),
            per_token=loss_per_token,
        )
    if not isinstance(logits, torch.Tensor):
        from SafeLens.core.analysis import lm_cross_entropy_loss

        return lm_cross_entropy_loss(
            logits,
            input_ids,
            model_inputs.get("attention_mask"),
            per_token=loss_per_token,
        )
    try:
        tokens = input_ids
        if not isinstance(tokens, torch.Tensor):
            tokens = torch.as_tensor(tokens, device=logits.device)
        else:
            tokens = tokens.to(logits.device)
        if tokens.shape[-1] < 2:
            empty_loss = logits.new_zeros((*tokens.shape[:-1], 0))
            return empty_loss if loss_per_token else logits.new_tensor(0.0)
        shifted_logits = logits[:, :-1, :].contiguous()
        shifted_tokens = tokens[:, 1:].contiguous()
        per_token_loss = F.cross_entropy(
            shifted_logits.view(-1, shifted_logits.shape[-1]),
            shifted_tokens.view(-1),
            reduction="none",
        ).view_as(shifted_tokens)
        attention_mask = model_inputs.get("attention_mask")
        if attention_mask is not None:
            if not isinstance(attention_mask, torch.Tensor):
                attention_mask = torch.as_tensor(attention_mask, device=logits.device)
            else:
                attention_mask = attention_mask.to(logits.device)
            loss_mask = (attention_mask[:, :-1].bool() & attention_mask[:, 1:].bool()).to(
                dtype=per_token_loss.dtype
            )
            if loss_per_token:
                return per_token_loss * loss_mask
            denominator = loss_mask.sum().clamp_min(1)
            return (per_token_loss * loss_mask).sum() / denominator
        if loss_per_token:
            return per_token_loss
        return per_token_loss.mean()
    except Exception as exc:
        raise RuntimeError(
            "Model output does not expose loss and SafeLens could not compute causal LM loss."
        ) from exc


def _loss_model_inputs(tokens: Any, attention_mask: Any | None) -> dict[str, Any]:
    model_inputs: dict[str, Any] = {"input_ids": tokens}
    if attention_mask is not None:
        model_inputs["attention_mask"] = attention_mask
    return model_inputs


def _extract_output_field(output: Any, field: str) -> Any:
    if isinstance(output, Mapping):
        return output.get(field)
    value = getattr(output, field, None)
    if value is not None:
        return value
    if isinstance(output, tuple | list):
        if not output:
            return None
        if field == "loss":
            return output[0]
        if field == "logits":
            if len(output) > 1 and _looks_like_scalar_loss(output[0]):
                return output[1]
            return output[0]
    return None


def _looks_like_scalar_loss(value: Any) -> bool:
    if isinstance(value, str | bytes | Mapping | tuple | list):
        return False
    ndim = getattr(value, "ndim", None)
    if ndim is not None:
        try:
            return int(ndim) == 0
        except (TypeError, ValueError):
            pass
    dim = getattr(value, "dim", None)
    if callable(dim):
        try:
            return int(dim()) == 0
        except (TypeError, ValueError):
            pass
    shape = getattr(value, "shape", None)
    if shape is not None:
        try:
            return len(shape) == 0
        except TypeError:
            pass
    return isinstance(value, int | float | complex | bool)


def _make_transformer_lens_config_view(
    model: Any,
    *,
    model_name: str,
    device: str | None,
    dtype: str | None,
    tokenizer: Any | None,
    runtime_flags: Mapping[str, bool] | None = None,
) -> TransformerLensConfigView:
    config = getattr(model, "config", None)
    core_config = _core_model_config(config)
    flags = {
        **_TRANSFORMER_LENS_RUNTIME_FLAG_DEFAULTS,
        **(dict(runtime_flags) if runtime_flags is not None else {}),
    }
    n_layers = _none_if_zero(_infer_model_layers(model))
    n_heads = _first_int_attr(
        core_config,
        config,
        model,
        names=("num_attention_heads", "n_head", "n_heads", "num_heads"),
    )
    n_key_value_heads = key_value_head_count(model)
    d_model = _first_int_attr(
        core_config, config, model, names=("hidden_size", "n_embd", "d_model", "dim")
    )
    d_head = _first_int_attr(
        core_config, config, model, names=("head_dim", "d_head", "kv_channels")
    )
    if d_head is None and d_model is not None and n_heads:
        d_head = d_model // n_heads
    d_vocab = _first_int_attr(core_config, config, model, names=("vocab_size", "d_vocab"))
    if d_vocab is None:
        d_vocab = _vocab_size_from_tokenizer(tokenizer)
    n_ctx = _first_int_attr(
        core_config,
        config,
        model,
        names=(
            "max_position_embeddings",
            "n_positions",
            "n_ctx",
            "seq_length",
            "max_sequence_length",
        ),
    )
    d_mlp = _first_int_attr(
        core_config,
        config,
        model,
        names=("intermediate_size", "n_inner", "d_ff", "ffn_dim", "d_mlp"),
    )
    act_fn = _first_str_attr(
        core_config,
        config,
        model,
        names=("hidden_act", "activation_function", "activation", "act_fn"),
    )
    attn_only = bool(
        _first_bool_attr(core_config, config, model, names=("attn_only", "attention_only")) or False
    )
    parallel_attn_mlp = bool(
        _first_bool_attr(
            core_config,
            config,
            model,
            names=("parallel_attn_mlp", "parallel_attn", "use_parallel_residual"),
        )
        or False
    )
    return TransformerLensConfigView(
        model_name=model_name,
        model_type=_config_attr(core_config, "model_type") or _config_attr(config, "model_type"),
        n_layers=n_layers,
        n_heads=n_heads,
        n_key_value_heads=n_key_value_heads,
        d_model=d_model,
        d_head=d_head,
        d_vocab=d_vocab,
        n_ctx=n_ctx,
        d_mlp=d_mlp,
        act_fn=act_fn,
        normalization_type=_infer_normalization_type(model, core_config, fallback_config=config),
        positional_embedding_type=_infer_positional_embedding_type(model),
        device=device,
        dtype=dtype,
        original_architecture=type(model).__name__,
        use_attn_result=bool(flags["use_attn_result"]),
        use_split_qkv_input=bool(flags["use_split_qkv_input"]),
        use_hook_mlp_in=bool(flags["use_hook_mlp_in"]),
        use_attn_in=bool(flags["use_attn_in"]),
        ungroup_grouped_query_attention=bool(flags["ungroup_grouped_query_attention"]),
        attn_only=attn_only,
        parallel_attn_mlp=parallel_attn_mlp,
        rmsnorm_uses_offset=bool(
            _first_bool_attr(
                core_config,
                config,
                model,
                names=("rmsnorm_uses_offset", "rms_norm_uses_offset"),
            )
            or False
        ),
    )


def _core_model_config(config: Any) -> Any:
    return _config_attr(config, "text_config") or _config_attr(config, "language_config") or config


def _config_attr(config: Any, name: str, default: Any = None) -> Any:
    if isinstance(config, Mapping):
        return config.get(name, default)
    return getattr(config, name, default)


def _is_olmo2_post_norm_model(model: Any) -> bool:
    config = _config_attr(model, "config")
    core_config = _core_model_config(config)
    markers = [type(model).__name__, _config_attr(model, "name_or_path", "")]
    for owner in (model, config, core_config):
        if owner is None:
            continue
        markers.extend(
            str(_config_attr(owner, name, ""))
            for name in ("original_architecture", "architectures", "model_type", "_name_or_path")
        )
    return any("olmo2" in marker.replace("-", "").replace("_", "").lower() for marker in markers)


def _has_output_logits_soft_cap(model: Any) -> bool:
    config = _config_attr(model, "config")
    core_config = _core_model_config(config)
    for owner in (model, config, core_config):
        if owner is None:
            continue
        for name in (
            "output_logits_soft_cap",
            "output_logit_soft_cap",
            "output_logits_softcap",
            "output_logit_softcap",
            "final_logit_softcapping",
            "final_logits_softcapping",
            "final_logit_soft_cap",
            "final_logits_soft_cap",
            "final_logit_softcap",
            "final_logits_softcap",
            "logits_soft_cap",
            "logits_softcap",
            "logit_soft_cap",
            "logit_softcap",
        ):
            value = _config_attr(owner, name)
            if value is None:
                continue
            try:
                return float(value) > 0.0
            except (TypeError, ValueError):
                continue
    return False


def _can_center_writing_weights_by_default(model: Any) -> bool:
    config = _config_attr(model, "config")
    core_config = _core_model_config(config)
    normalization_type = _infer_normalization_type(model, core_config, fallback_config=config)
    if normalization_type not in {"LN", "LNPre"}:
        return False
    return not any(
        bool(_config_attr(owner, "final_rms", False))
        for owner in (model, config, core_config)
        if owner is not None
    )


def _infer_model_layers(model: Any) -> int:
    config = _config_attr(model, "config")
    core_config = _core_model_config(config)
    candidates: list[int] = []
    for owner in (model, config, core_config):
        if owner is None:
            continue
        for name in (
            "num_hidden_layers",
            "n_layer",
            "n_layers",
            "num_layers",
            "num_decoder_layers",
        ):
            value = _config_attr(owner, name)
            if value is not None:
                try:
                    candidates.append(int(value))
                except (TypeError, ValueError):
                    continue
    for path in (
        "model.layers",
        "model.language_model.layers",
        "transformer.h",
        "gpt_neox.layers",
        "model.decoder.layers",
        "encoder.layer",
        "transformer.layer",
        "encoder.layers",
        "encoder.block",
        "decoder.block",
    ):
        try:
            target = model
            for part in path.split("."):
                target = getattr(target, part)
            candidates.append(len(target))
        except (AttributeError, TypeError):
            continue
    return max(candidates, default=0)


def _none_if_zero(value: int) -> int | None:
    return value if value > 0 else None


def _first_int_attr(*owners: Any, names: Sequence[str]) -> int | None:
    for owner in owners:
        if owner is None:
            continue
        for name in names:
            value = _config_attr(owner, name)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
    return None


def _first_str_attr(*owners: Any, names: Sequence[str]) -> str | None:
    for owner in owners:
        if owner is None:
            continue
        for name in names:
            value = _config_attr(owner, name)
            if value is not None:
                return str(value)
    return None


def _first_bool_attr(*owners: Any, names: Sequence[str]) -> bool | None:
    for owner in owners:
        if owner is None:
            continue
        for name in names:
            value = _config_attr(owner, name)
            if value is None:
                continue
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"true", "1", "yes"}:
                    return True
                if lowered in {"false", "0", "no"}:
                    return False
            return bool(value)
    return None


def _vocab_size_from_tokenizer(tokenizer: Any | None) -> int | None:
    if tokenizer is None:
        return None
    for name in ("vocab_size", "n_vocab"):
        value = getattr(tokenizer, name, None)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    length = getattr(tokenizer, "__len__", None)
    if callable(length):
        try:
            return int(length())
        except (TypeError, ValueError):
            return None
    return None


def _infer_normalization_type(
    model: Any,
    config: Any,
    *,
    fallback_config: Any = None,
) -> str | None:
    explicit = _first_str_attr(
        config,
        fallback_config,
        model,
        names=("normalization_type", "norm_type"),
    )
    if explicit is not None:
        return explicit
    model_type = str(_config_attr(config, "model_type", "") or "").lower()
    if not model_type:
        model_type = str(_config_attr(fallback_config, "model_type", "") or "").lower()
    if any(marker in model_type for marker in ("llama", "qwen", "mistral", "gemma", "t5")):
        return "RMS"
    if model_type in {"mamba", "mamba2"}:
        return "RMS"
    if any(marker in model_type for marker in ("gpt", "bert", "roberta", "opt")):
        return "LN"
    return None


def _stack_tensor_like(values: Sequence[Any]) -> Any:
    if not values:
        return []
    first = values[0]
    if type(first).__module__.split(".")[0] == "torch":
        try:
            import torch

            return torch.stack(list(values))
        except ImportError:
            pass
    return [_to_python_sequence_container(value) for value in values]


def _svd_component(matrix: Any, component: str) -> Any:
    """Return one SVD component while preserving tensor backends when possible."""
    try:
        import torch

        if isinstance(matrix, torch.Tensor):
            u, s, vh = torch.linalg.svd(matrix, full_matrices=False)
            if component == "U":
                return u
            if component == "S":
                return s
            if component == "V":
                return vh.transpose(-1, -2)
    except Exception:
        pass
    try:
        import numpy as np

        array = np.asarray(matrix)
        u, s, vh = np.linalg.svd(array, full_matrices=False)
        if component == "U":
            return u.tolist()
        if component == "S":
            return s.tolist()
        if component == "V":
            return np.swapaxes(vh, -1, -2).tolist()
    except Exception:
        u, s, v = svd_nested(matrix)
        if component == "U":
            return u
        if component == "S":
            return s
        if component == "V":
            return v
    raise ValueError(f"Unknown SVD component {component!r}.")


def _stacked_attention_head_count(value: Any) -> int:
    shape = shape_of(value)
    if len(shape) < 2:
        raise ValueError(f"Expected stacked attention weights with a head dimension, got {shape}.")
    return int(shape[1])


def _stack_first_dim(value: Any) -> int:
    shape = shape_of(value)
    if shape:
        return int(shape[0])
    return len(value)


def _repeat_key_value_heads_to_query_heads(
    value: Any,
    *,
    target_heads: int,
    tensor_name: str,
) -> Any:
    shape = shape_of(value)
    if len(shape) < 2:
        raise ValueError(f"{tensor_name} must include layer and head dimensions, got {shape}.")
    source_heads = int(shape[1])
    if source_heads == target_heads:
        return value
    if source_heads <= 0 or target_heads % source_heads != 0:
        raise ValueError(
            f"Cannot align {tensor_name} with {source_heads} key/value heads "
            f"to {target_heads} query heads."
        )
    repeats = target_heads // source_heads
    repeat_interleave = getattr(value, "repeat_interleave", None)
    if callable(repeat_interleave):
        try:
            return repeat_interleave(repeats, dim=1)
        except Exception:
            pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.repeat(value, repeats, axis=1)
    except Exception:
        pass
    if _is_sequence(value):
        return [
            [
                _clone_tensor_like(head_value)
                for head_value in layer_value
                for _repeat_index in range(repeats)
            ]
            for layer_value in value
        ]
    raise TypeError(f"Cannot repeat {tensor_name} heads for value type {type(value).__name__}.")


def _clone_tensor_like(value: Any) -> Any:
    clone = getattr(value, "clone", None)
    if callable(clone):
        try:
            return clone()
        except Exception:
            pass
    copy = getattr(value, "copy", None)
    if callable(copy):
        try:
            return copy()
        except Exception:
            pass
    if _is_sequence(value):
        return [_clone_tensor_like(item) for item in value]
    return value


def _add_tensor_like_values(left: Any, right: Any) -> Any:
    if _is_sequence(left) and _is_sequence(right):
        return [
            _add_tensor_like_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        ]
    if _is_sequence(left):
        coerced_left = _coerce_sequence_to_tensor_like(left, right)
        if coerced_left is not None:
            return coerced_left + right
    if _is_sequence(right):
        coerced_right = _coerce_sequence_to_tensor_like(right, left)
        if coerced_right is not None:
            return left + coerced_right
    try:
        return left + right
    except Exception:
        pass
    if _is_sequence(left) or _is_sequence(right):
        raise TypeError(
            f"Cannot add values of types {type(left).__name__} and {type(right).__name__}."
        )
    return float(left) + float(right)


def _input_embeddings_module(model: Any) -> Any | None:
    get_input_embeddings = getattr(model, "get_input_embeddings", None)
    if callable(get_input_embeddings):
        try:
            embeddings = get_input_embeddings()
        except Exception:
            embeddings = None
        if embeddings is not None:
            return embeddings
    for path in (
        "transformer.wte",
        "wte",
        "transformer.word_embeddings",
        "word_embeddings",
        "gpt_neox.embed_in",
        "model.embed_tokens",
        "model.decoder.embed_tokens",
        "decoder.embed_tokens",
        "embed_tokens",
        "encoder.embed_tokens",
        "shared",
        "bert.embeddings.word_embeddings",
        "roberta.embeddings.word_embeddings",
        "distilbert.embeddings.word_embeddings",
        "embeddings.word_embeddings",
    ):
        try:
            return resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
    return None


def _positional_embeddings_module(model: Any) -> Any | None:
    for path in (
        "transformer.wpe",
        "wpe",
        "model.wpe",
        "model.embed_positions",
        "model.decoder.embed_positions",
        "decoder.embed_positions",
        "embed_positions",
        "bert.embeddings.position_embeddings",
        "roberta.embeddings.position_embeddings",
        "distilbert.embeddings.position_embeddings",
        "embeddings.position_embeddings",
    ):
        try:
            return resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
    return None


def _center_attention_output_module(module: Any, *, architecture: str) -> None:
    weight = getattr(module, "weight", None)
    if weight is not None:
        packed_axis = preferred_attention_weight_packed_axis(
            module,
            architecture=architecture,
            component="z",
        )
        axis = 1 - packed_axis if packed_axis in {0, 1} else -1
        _set_module_weight(module, _center_tensor_like(weight, axis=axis))
    bias = getattr(module, "bias", None)
    if bias is not None:
        _set_module_bias(module, _center_bias_like(bias))


def _center_mlp_output_module(module: Any, *, d_model: int | None) -> None:
    weight = getattr(module, "weight", None)
    if weight is not None:
        axis = _residual_axis_from_d_model(weight, d_model=d_model)
        _set_module_weight(module, _center_tensor_like(weight, axis=axis))
    bias = getattr(module, "bias", None)
    if bias is not None:
        _set_module_bias(module, _center_bias_like(bias))


def _center_module_weight(module: Any | None, *, axis: int) -> None:
    if module is None:
        return
    weight = getattr(module, "weight", None)
    if weight is None:
        return
    _set_module_weight(module, _center_tensor_like(weight, axis=axis))


def _center_module_bias(module: Any | None) -> None:
    if module is None:
        return
    bias = getattr(module, "bias", None)
    if bias is None:
        return
    _set_module_bias(module, _center_bias_like(bias))


def _fold_layer_norm_weights_in_model(
    model: Any,
    *,
    model_name: str,
    fold_biases: bool,
    center_weights: bool,
    rmsnorm_uses_offset: bool = False,
) -> None:
    adapter = architecture_adapter_for_model(model, model_name=model_name)
    for layer in range(_infer_model_layers(model)):
        try:
            ln1_module = _norm_module_for_layer(
                model, adapter=adapter, layer=layer, component="ln1_scale"
            )
        except (KeyError, NotImplementedError, ValueError):
            ln1_module = None
        try:
            ln2_module = _norm_module_for_layer(
                model, adapter=adapter, layer=layer, component="ln2_scale"
            )
        except (KeyError, NotImplementedError, ValueError):
            ln2_module = None

        mlp_norm_module = ln2_module if ln2_module is not None else ln1_module
        shared_input_norm = ln1_module is not None and mlp_norm_module is ln1_module
        attention_folded = False
        mlp_folded = False
        if ln1_module is not None:
            attention_folded = _fold_attention_layer_norm(
                model,
                adapter=adapter,
                layer=layer,
                norm_module=ln1_module,
                fold_biases=fold_biases,
                center_weights=center_weights,
                set_identity=not shared_input_norm,
                rmsnorm_uses_offset=rmsnorm_uses_offset,
            )

        if mlp_norm_module is not None:
            mlp_folded = _fold_mlp_layer_norm(
                model,
                adapter=adapter,
                layer=layer,
                norm_module=mlp_norm_module,
                fold_biases=fold_biases,
                center_weights=center_weights,
                set_identity=not shared_input_norm,
                rmsnorm_uses_offset=rmsnorm_uses_offset,
            )
        if shared_input_norm and (attention_folded or mlp_folded):
            _set_norm_module_to_identity(
                ln1_module,
                fold_biases=fold_biases,
                rmsnorm_uses_offset=rmsnorm_uses_offset,
            )
    _fold_final_layer_norm_into_unembed(
        model,
        fold_biases=fold_biases,
        center_weights=center_weights,
        rmsnorm_uses_offset=rmsnorm_uses_offset,
    )


def _norm_module_for_layer(model: Any, *, adapter: Any, layer: int, component: str) -> Any:
    component_ref = adapter.parse_component_ref(transformer_lens_component_name(component, layer))
    if component_ref is None:
        raise KeyError(f"Unknown norm component {component!r}.")
    return adapter.get_component(model, component_ref)


def _fold_attention_layer_norm(
    model: Any,
    *,
    adapter: Any,
    layer: int,
    norm_module: Any,
    fold_biases: bool,
    center_weights: bool,
    set_identity: bool,
    rmsnorm_uses_offset: bool,
) -> bool:
    if _fold_split_attention_layer_norm(
        model,
        adapter=adapter,
        layer=layer,
        norm_module=norm_module,
        fold_biases=fold_biases,
        center_weights=center_weights,
        set_identity=set_identity,
        rmsnorm_uses_offset=rmsnorm_uses_offset,
    ):
        return True
    return _fold_joint_qkv_attention_layer_norm(
        model,
        adapter=adapter,
        layer=layer,
        norm_module=norm_module,
        fold_biases=fold_biases,
        center_weights=center_weights,
        set_identity=set_identity,
        rmsnorm_uses_offset=rmsnorm_uses_offset,
    )


def _fold_split_attention_layer_norm(
    model: Any,
    *,
    adapter: Any,
    layer: int,
    norm_module: Any,
    fold_biases: bool,
    center_weights: bool,
    set_identity: bool,
    rmsnorm_uses_offset: bool,
) -> bool:
    try:
        modules_and_specs = {
            component: _attention_module_and_spec(
                model, adapter=adapter, component=component, layer=layer
            )
            for component in ("q", "k", "v")
        }
    except (KeyError, NotImplementedError, ValueError):
        return False
    if any(spec.activation != "split_heads" for _module, spec in modules_and_specs.values()):
        return False

    folded_any = False
    for component, (module, _spec) in modules_and_specs.items():
        had_bias = getattr(module, "bias", None) is not None
        weight = _module_weight_to_tl(model, module, component=component, architecture=adapter.name)
        bias = _module_bias_to_tl(model, module, component=component)
        folded_weight, folded_bias = _fold_layer_norm_into_attention_weight(
            weight,
            bias,
            norm_module=norm_module,
            fold_biases=fold_biases,
            center_weights=center_weights,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
        _set_module_weight(
            module,
            _tl_attention_weight_to_module(
                folded_weight,
                module,
                component=component,
                architecture=adapter.name,
            ),
        )
        if fold_biases and (had_bias or _norm_affine_bias(norm_module) is not None):
            _set_module_bias(
                module,
                _tl_attention_bias_to_module(folded_bias, module, component=component),
            )
        folded_any = True
    if folded_any and set_identity:
        _set_norm_module_to_identity(
            norm_module,
            fold_biases=fold_biases,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
    return folded_any


def _fold_joint_qkv_attention_layer_norm(
    model: Any,
    *,
    adapter: Any,
    layer: int,
    norm_module: Any,
    fold_biases: bool,
    center_weights: bool,
    set_identity: bool,
    rmsnorm_uses_offset: bool,
) -> bool:
    try:
        q_module, q_spec = _attention_module_and_spec(
            model, adapter=adapter, component="q", layer=layer
        )
        k_module, k_spec = _attention_module_and_spec(
            model, adapter=adapter, component="k", layer=layer
        )
        v_module, v_spec = _attention_module_and_spec(
            model, adapter=adapter, component="v", layer=layer
        )
    except (KeyError, NotImplementedError, ValueError):
        return False
    if not (q_module is k_module is v_module):
        return False
    if {q_spec.activation, k_spec.activation, v_spec.activation} != {"split_qkv_heads"}:
        return False
    if len({q_spec.qkv_layout, k_spec.qkv_layout, v_spec.qkv_layout}) != 1:
        return False
    qkv_layout = q_spec.qkv_layout
    q_heads = head_count_for_component(model, "q")
    kv_heads = head_count_for_component(model, "k")
    packed_axis = preferred_qkv_weight_packed_axis(q_module, architecture=adapter.name)
    if packed_axis is None:
        try:
            packed_axis = _infer_joint_qkv_packed_axis(q_module, q_heads=q_heads, kv_heads=kv_heads)
        except ValueError:
            return False
    if packed_axis not in {0, 1}:
        return False

    folded_weights: dict[str, Any] = {}
    folded_biases: dict[str, Any] = {}
    had_bias = getattr(q_module, "bias", None) is not None
    for component in ("q", "k", "v"):
        weight = _joint_qkv_module_weight_to_tl(
            q_module,
            component=component,
            q_heads=q_heads,
            kv_heads=kv_heads,
            qkv_layout=qkv_layout,
            packed_axis=packed_axis,
        )
        bias = _joint_qkv_module_bias_to_tl(
            model,
            q_module,
            component=component,
            q_heads=q_heads,
            kv_heads=kv_heads,
            qkv_layout=qkv_layout,
        )
        folded_weight, folded_bias = _fold_layer_norm_into_attention_weight(
            weight,
            bias,
            norm_module=norm_module,
            fold_biases=fold_biases,
            center_weights=center_weights,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
        folded_weights[component] = folded_weight
        folded_biases[component] = folded_bias

    _set_module_weight(
        q_module,
        _merge_split_joint_qkv_weights(
            folded_weights["q"],
            folded_weights["k"],
            folded_weights["v"],
            packed_axis=packed_axis,
            qkv_layout=qkv_layout,
        ),
    )
    if fold_biases and (had_bias or _norm_affine_bias(norm_module) is not None):
        _set_module_bias(
            q_module,
            _merge_split_joint_qkv_biases(
                folded_biases["q"],
                folded_biases["k"],
                folded_biases["v"],
                qkv_layout=qkv_layout,
            ),
        )
    if set_identity:
        _set_norm_module_to_identity(
            norm_module,
            fold_biases=fold_biases,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
    return True


def _fold_layer_norm_into_attention_weight(
    weight: Any,
    bias: Any,
    *,
    norm_module: Any,
    fold_biases: bool,
    center_weights: bool,
    rmsnorm_uses_offset: bool,
) -> tuple[Any, Any]:
    norm_weight = _norm_affine_weight(norm_module, rmsnorm_uses_offset=rmsnorm_uses_offset)
    norm_bias = _norm_affine_bias(norm_module)
    original_weight = weight
    if norm_weight is not None:
        weight = _multiply_reader_weight_by_norm(weight, norm_weight, reader_axis=1)
    if fold_biases and norm_bias is not None:
        bias = _add_tensor_like_values(
            bias,
            _reader_weight_bias_contribution(original_weight, norm_bias, reader_axis=1),
        )
    if center_weights:
        weight = _center_tensor_like(weight, axis=1)
    return weight, bias


def _fold_mlp_layer_norm(
    model: Any,
    *,
    adapter: Any,
    layer: int,
    norm_module: Any,
    fold_biases: bool,
    center_weights: bool,
    set_identity: bool,
    rmsnorm_uses_offset: bool,
) -> bool:
    folded_any = False
    for component in ("in", "gate"):
        try:
            module, weight = _mlp_input_module_and_tl_weight(
                model,
                adapter=adapter,
                layer=layer,
                component=component,
            )
        except (KeyError, NotImplementedError, ValueError):
            continue
        folded_weight, folded_bias = _fold_layer_norm_into_mlp_weight(
            weight,
            getattr(module, "bias", None),
            norm_module=norm_module,
            fold_biases=fold_biases,
            center_weights=center_weights and component == "in",
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
        _set_mlp_input_weight(module, folded_weight)
        if fold_biases and folded_bias is not None:
            _set_module_bias(module, folded_bias)
        folded_any = True
    if folded_any and set_identity:
        _set_norm_module_to_identity(
            norm_module,
            fold_biases=fold_biases,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
    return folded_any


def _mlp_input_module_and_tl_weight(
    model: Any,
    *,
    adapter: Any,
    layer: int,
    component: str,
) -> tuple[Any, Any]:
    if component == "in":
        paths = adapter._mlp_weight_paths(
            layer,
            canonical_component="pre_linear",
            fallback_component="pre",
        )
    elif component == "gate":
        paths = (
            f"model.language_model.layers.{layer}.mlp.gate",
            f"model.language_model.layers.{layer}.mlp.gate_proj",
            f"model.language_model.layers.{layer}.mlp.w1",
            f"model.layers.{layer}.mlp.gate",
            f"model.layers.{layer}.mlp.gate_proj",
            f"model.layers.{layer}.mlp.w1",
            f"model.decoder.layers.{layer}.mlp.gate_proj",
            f"decoder.layers.{layer}.mlp.gate_proj",
        )
    else:
        raise ValueError(f"Unsupported MLP input component {component!r}.")
    module = _module_from_first_path(model, paths, kind=f"MLP {component} weight")
    weight = getattr(module, "weight", None)
    if weight is None:
        raise KeyError(f"MLP {component} module has no weight.")
    if _is_transformers_conv1d_module(module):
        return module, weight
    return module, transpose_2d_weight(weight)


def _module_from_first_path(model: Any, paths: Sequence[str], *, kind: str) -> Any:
    attempted: list[str] = []
    for path in paths:
        attempted.append(path)
        try:
            module = resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
        if getattr(module, "weight", None) is not None:
            return module
    attempted_paths = ", ".join(attempted)
    raise KeyError(f"Could not resolve {kind}. Tried module paths: {attempted_paths}.")


def _fold_layer_norm_into_mlp_weight(
    weight: Any,
    bias: Any | None,
    *,
    norm_module: Any,
    fold_biases: bool,
    center_weights: bool,
    rmsnorm_uses_offset: bool,
) -> tuple[Any, Any]:
    norm_weight = _norm_affine_weight(norm_module, rmsnorm_uses_offset=rmsnorm_uses_offset)
    norm_bias = _norm_affine_bias(norm_module)
    original_weight = weight
    if norm_weight is not None:
        weight = _multiply_reader_weight_by_norm(weight, norm_weight, reader_axis=0)
    if fold_biases and norm_bias is not None:
        folded_bias = _reader_weight_bias_contribution(original_weight, norm_bias, reader_axis=0)
        bias = folded_bias if bias is None else _add_tensor_like_values(bias, folded_bias)
    if center_weights:
        weight = _center_tensor_like(weight, axis=0)
    return weight, bias


def _set_mlp_input_weight(module: Any, tl_weight: Any) -> None:
    if _is_transformers_conv1d_module(module):
        _set_module_weight(module, tl_weight)
    else:
        _set_module_weight(module, transpose_2d_weight(tl_weight))


def _multiply_reader_weight_by_norm(weight: Any, norm_weight: Any, *, reader_axis: int) -> Any:
    if type(weight).__module__.split(".")[0] == "torch":
        try:
            view_shape = [1] * weight.ndim
            view_shape[reader_axis] = int(norm_weight.shape[0])
            return weight * norm_weight.reshape(view_shape).to(
                dtype=weight.dtype,
                device=weight.device,
            )
        except Exception:
            pass
    if type(weight).__module__.split(".")[0] == "numpy":
        try:
            import numpy as np

            view_shape = [1] * len(weight.shape)
            view_shape[reader_axis] = int(norm_weight.shape[0])
            return weight * np.asarray(norm_weight).reshape(view_shape)
        except Exception:
            pass
    values = _to_python_sequence_container(weight)
    scales = _to_python_sequence_container(norm_weight)
    return _multiply_nested_axis(values, scales, axis=reader_axis)


def _reader_weight_bias_contribution(weight: Any, norm_bias: Any, *, reader_axis: int) -> Any:
    if type(weight).__module__.split(".")[0] == "torch":
        try:
            bias = norm_bias.to(dtype=weight.dtype, device=weight.device)
            broadcast = _broadcast_shape_for_axis(weight.ndim, reader_axis, bias.shape[0])
            return (weight * bias.reshape(broadcast)).sum(dim=reader_axis)
        except Exception:
            pass
    if type(weight).__module__.split(".")[0] == "numpy":
        try:
            import numpy as np

            bias = np.asarray(norm_bias)
            return np.sum(
                weight
                * bias.reshape(
                    _broadcast_shape_for_axis(len(weight.shape), reader_axis, bias.shape[0])
                ),
                axis=reader_axis,
            )
        except Exception:
            pass
    values = _to_python_sequence_container(weight)
    biases = _to_python_sequence_container(norm_bias)
    return _sum_nested_weighted_axis(values, biases, axis=reader_axis)


def _broadcast_shape_for_axis(ndim: int, axis: int, size: int) -> tuple[int, ...]:
    if axis < 0:
        axis = ndim + axis
    shape = [1] * ndim
    shape[axis] = int(size)
    return tuple(shape)


def _multiply_nested_axis(value: Any, scales: Sequence[Any], *, axis: int) -> Any:
    if axis < 0:
        axis = len(shape_of(value)) + axis
    if axis == 0:
        return [_multiply_nested_scalars(item, scales[index]) for index, item in enumerate(value)]
    return [_multiply_nested_axis(item, scales, axis=axis - 1) for item in value]


def _sum_nested_weighted_axis(value: Any, weights: Sequence[Any], *, axis: int) -> Any:
    if axis < 0:
        axis = len(shape_of(value)) + axis
    if axis == 0:
        weighted = [
            _multiply_nested_scalars(item, weights[index]) for index, item in enumerate(value)
        ]
        return _sum_nested_values(weighted)
    return [_sum_nested_weighted_axis(item, weights, axis=axis - 1) for item in value]


def _multiply_nested_scalars(value: Any, scalar: Any) -> Any:
    if _is_sequence(value):
        return [_multiply_nested_scalars(item, scalar) for item in value]
    return float(value) * float(scalar)


def _sum_nested_values(values: Sequence[Any]) -> Any:
    if not values:
        return 0
    total = values[0]
    for value in values[1:]:
        total = _add_tensor_like_values(total, value)
    return total


def _norm_affine_weight(module: Any, *, rmsnorm_uses_offset: bool = False) -> Any | None:
    weight = getattr(module, "weight", None)
    if weight is None:
        return None
    return _effective_rmsnorm_weight(module, weight, rmsnorm_uses_offset=rmsnorm_uses_offset)


def _norm_affine_bias(module: Any) -> Any | None:
    return getattr(module, "bias", None)


def _effective_rmsnorm_weight(
    module: Any,
    weight: Any,
    *,
    rmsnorm_uses_offset: bool = False,
) -> Any:
    if not (bool(rmsnorm_uses_offset) or bool(getattr(module, "rmsnorm_uses_offset", False))):
        return weight
    try:
        return weight + 1.0
    except Exception:
        return _add_tensor_like_values(weight, _ones_like_tensor_value(weight))


def _set_norm_module_to_identity(
    module: Any,
    *,
    fold_biases: bool,
    rmsnorm_uses_offset: bool = False,
) -> None:
    weight = getattr(module, "weight", None)
    if weight is not None:
        if bool(rmsnorm_uses_offset) or bool(getattr(module, "rmsnorm_uses_offset", False)):
            _set_module_weight(module, _zero_like_tensor_value(weight))
        else:
            _set_module_weight(module, _ones_like_tensor_value(weight))
    bias = getattr(module, "bias", None)
    if fold_biases and bias is not None:
        _set_module_bias(module, _zero_like_tensor_value(bias))


def _fold_final_layer_norm_into_unembed(
    model: Any,
    *,
    fold_biases: bool,
    center_weights: bool,
    rmsnorm_uses_offset: bool = False,
) -> bool:
    norm_module = _final_norm_module_for_weight_processing(model)
    if (
        norm_module is None
        or _norm_affine_weight(
            norm_module,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
        is None
    ):
        return False
    native_weight = getattr(model, "W_U", None)
    if native_weight is not None:
        folded_weight = _fold_final_norm_into_tl_unembed_weight(
            native_weight,
            norm_module,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
        if center_weights:
            folded_weight = _center_tensor_like(folded_weight, axis=0)
        model.W_U = folded_weight
        native_norm_bias_folded = False
        if fold_biases:
            native_bias = getattr(model, "b_U", None)
            final_bias = _fold_final_norm_bias_into_tl_unembed_bias(
                native_weight,
                native_bias,
                norm_module,
            )
            if final_bias is not None:
                model.b_U = final_bias
                native_norm_bias_folded = (
                    native_bias is not None and _norm_affine_bias(norm_module) is not None
                )
        _set_norm_module_to_identity(
            norm_module,
            fold_biases=native_norm_bias_folded,
            rmsnorm_uses_offset=rmsnorm_uses_offset,
        )
        return True

    embeddings = _output_embeddings_from_model(model)
    weight = getattr(embeddings, "weight", None)
    if weight is None:
        return False
    folded_weight = _fold_final_norm_into_hf_unembed_weight(
        weight,
        norm_module,
        rmsnorm_uses_offset=rmsnorm_uses_offset,
    )
    if center_weights:
        folded_weight = _center_tensor_like(folded_weight, axis=-1)
    _set_module_weight(embeddings, folded_weight)
    if hasattr(model, "_weight"):
        try:
            model._weight = folded_weight
        except Exception:
            pass
    hf_norm_bias_folded = False
    if fold_biases:
        embeddings_bias = getattr(embeddings, "bias", None)
        final_bias = _fold_final_norm_bias_into_hf_unembed_bias(
            weight,
            embeddings_bias,
            norm_module,
        )
        if final_bias is not None:
            _set_module_bias(embeddings, final_bias)
            hf_norm_bias_folded = (
                embeddings_bias is not None and _norm_affine_bias(norm_module) is not None
            )
            if hasattr(model, "_bias"):
                try:
                    model._bias = final_bias
                except Exception:
                    pass
    _set_norm_module_to_identity(
        norm_module,
        fold_biases=hf_norm_bias_folded,
        rmsnorm_uses_offset=rmsnorm_uses_offset,
    )
    return True


def _final_norm_module_for_weight_processing(model: Any) -> Any | None:
    for path in _FINAL_NORM_MODULE_PATHS:
        try:
            module = resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
        if module is not None and getattr(module, "weight", None) is not None:
            return module
    return None


def _output_embeddings_from_model(model: Any) -> Any | None:
    get_output_embeddings = getattr(model, "get_output_embeddings", None)
    if not callable(get_output_embeddings):
        return None
    try:
        return get_output_embeddings()
    except Exception:
        return None


def _fold_final_norm_into_hf_unembed_weight(
    weight: Any,
    norm_module: Any,
    *,
    rmsnorm_uses_offset: bool = False,
) -> Any:
    norm_weight = _norm_affine_weight(norm_module, rmsnorm_uses_offset=rmsnorm_uses_offset)
    if norm_weight is None:
        return weight
    return _multiply_reader_weight_by_norm(weight, norm_weight, reader_axis=-1)


def _fold_final_norm_into_tl_unembed_weight(
    weight: Any,
    norm_module: Any,
    *,
    rmsnorm_uses_offset: bool = False,
) -> Any:
    norm_weight = _norm_affine_weight(norm_module, rmsnorm_uses_offset=rmsnorm_uses_offset)
    if norm_weight is None:
        return weight
    return _multiply_reader_weight_by_norm(weight, norm_weight, reader_axis=0)


def _fold_final_norm_bias_into_hf_unembed_bias(
    weight: Any,
    bias: Any | None,
    norm_module: Any,
) -> Any | None:
    norm_bias = _norm_affine_bias(norm_module)
    if norm_bias is None or bias is None:
        return bias
    folded = _reader_weight_bias_contribution(weight, norm_bias, reader_axis=-1)
    return _add_tensor_like_values(bias, folded)


def _fold_final_norm_bias_into_tl_unembed_bias(
    weight: Any,
    bias: Any | None,
    norm_module: Any,
) -> Any | None:
    norm_bias = _norm_affine_bias(norm_module)
    if norm_bias is None or bias is None:
        return bias
    folded = _reader_weight_bias_contribution(weight, norm_bias, reader_axis=0)
    return _add_tensor_like_values(bias, folded)


def _ones_like_tensor_value(value: Any) -> Any:
    if type(value).__module__.split(".")[0] == "torch":
        try:
            import torch

            return torch.ones_like(value)
        except Exception:
            pass
    if type(value).__module__.split(".")[0] == "numpy":
        try:
            import numpy as np

            return np.ones_like(value)
        except Exception:
            pass
    if _is_sequence(value):
        return [_ones_like_tensor_value(item) for item in value]
    return 1


def _infer_joint_qkv_packed_axis(module: Any, *, q_heads: int, kv_heads: int) -> int:
    weight = getattr(module, "weight", None)
    shape = shape_of(weight)
    if len(shape) != 2:
        raise ValueError(f"Cannot infer packed QKV axis from shape {shape}.")
    total_heads = q_heads + 2 * kv_heads
    if total_heads <= 0:
        raise ValueError("QKV head count must be positive.")
    packed_on_rows = int(shape[0]) % total_heads == 0
    packed_on_columns = int(shape[1]) % total_heads == 0
    if packed_on_rows:
        return 0
    if packed_on_columns:
        return 1
    raise ValueError(f"Cannot infer packed QKV axis from shape {shape}.")


def _fold_value_bias_modules(
    model: Any,
    *,
    value_module: Any,
    output_module: Any,
    value_spec: Any,
    architecture: str,
) -> None:
    value_bias = getattr(value_module, "bias", None)
    if value_bias is None:
        return
    output_weight = getattr(output_module, "weight", None)
    if output_weight is None:
        raise RuntimeError("Cannot fold value biases without attention output weights.")
    output_bias = getattr(output_module, "bias", None)
    if output_bias is None:
        output_bias = zeros_like_last_dim(
            output_weight,
            axis=_output_bias_axis(output_module, architecture=architecture),
        )
    b_v = _value_bias_to_tl_shape(
        model, value_module, value_bias, value_spec, architecture=architecture
    )
    w_o = reshape_attention_weight(
        output_weight,
        component="z",
        n_heads=head_count_for_component(model, "z"),
        packed_axis=preferred_attention_weight_packed_axis(
            output_module,
            architecture=architecture,
            component="z",
        ),
    )
    folded_bias, _zero_b_v = _fold_value_bias_tensor_like(
        b_v,
        w_o,
        output_bias,
        target_heads=head_count_for_component(model, "z"),
    )
    _set_module_bias(output_module, folded_bias)
    _zero_value_bias_module(model, value_module, value_bias, value_spec, architecture=architecture)


def _refactor_split_attention_layer(model: Any, *, adapter: Any, layer: int) -> bool:
    try:
        modules_and_specs = {
            component: _attention_module_and_spec(
                model, adapter=adapter, component=component, layer=layer
            )
            for component in ("q", "k", "v", "z")
        }
    except (KeyError, NotImplementedError, ValueError):
        return False
    if any(spec.activation != "split_heads" for _module, spec in modules_and_specs.values()):
        return False

    q_module, _q_spec = modules_and_specs["q"]
    k_module, _k_spec = modules_and_specs["k"]
    v_module, _v_spec = modules_and_specs["v"]
    o_module, _o_spec = modules_and_specs["z"]
    if head_count_for_component(model, "q") != head_count_for_component(model, "k"):
        return False

    w_q = _module_weight_to_tl(model, q_module, component="q", architecture=adapter.name)
    w_k = _module_weight_to_tl(model, k_module, component="k", architecture=adapter.name)
    b_q = _module_bias_to_tl(model, q_module, component="q")
    b_k = _module_bias_to_tl(model, k_module, component="k")
    w_q_refactored, b_q_refactored, w_k_refactored, b_k_refactored = _refactor_qk_matrices(
        w_q,
        b_q,
        w_k,
        b_k,
    )
    _set_module_weight(
        q_module,
        _tl_attention_weight_to_module(
            w_q_refactored,
            q_module,
            component="q",
            architecture=adapter.name,
        ),
    )
    _set_module_weight(
        k_module,
        _tl_attention_weight_to_module(
            w_k_refactored,
            k_module,
            component="k",
            architecture=adapter.name,
        ),
    )
    _set_module_bias(
        q_module, _tl_attention_bias_to_module(b_q_refactored, q_module, component="q")
    )
    _set_module_bias(
        k_module, _tl_attention_bias_to_module(b_k_refactored, k_module, component="k")
    )

    b_v = _module_bias_to_tl(model, v_module, component="v")
    w_o = _module_weight_to_tl(model, o_module, component="z", architecture=adapter.name)
    output_bias = getattr(o_module, "bias", None)
    if output_bias is None:
        output_bias = zeros_like_last_dim(
            o_module.weight,
            axis=_output_bias_axis(o_module, architecture=adapter.name),
        )
    folded_bias, zero_b_v = _fold_value_bias_tensor_like(
        b_v,
        w_o,
        output_bias,
        target_heads=head_count_for_component(model, "z"),
    )
    _set_module_bias(v_module, _tl_attention_bias_to_module(zero_b_v, v_module, component="v"))
    _set_module_bias(o_module, folded_bias)

    w_v = _module_weight_to_tl(model, v_module, component="v", architecture=adapter.name)
    w_v_refactored, w_o_refactored = _refactor_ov_matrices(w_v, w_o)
    _set_module_weight(
        v_module,
        _tl_attention_weight_to_module(
            w_v_refactored,
            v_module,
            component="v",
            architecture=adapter.name,
        ),
    )
    _set_module_weight(
        o_module,
        _tl_attention_weight_to_module(
            w_o_refactored,
            o_module,
            component="z",
            architecture=adapter.name,
        ),
    )
    return True


def _refactor_joint_qkv_attention_layer(model: Any, *, adapter: Any, layer: int) -> bool:
    try:
        q_module, q_spec = _attention_module_and_spec(
            model, adapter=adapter, component="q", layer=layer
        )
        k_module, k_spec = _attention_module_and_spec(
            model, adapter=adapter, component="k", layer=layer
        )
        v_module, v_spec = _attention_module_and_spec(
            model, adapter=adapter, component="v", layer=layer
        )
        o_module, o_spec = _attention_module_and_spec(
            model, adapter=adapter, component="z", layer=layer
        )
    except (KeyError, NotImplementedError, ValueError):
        return False
    if not (q_module is k_module is v_module):
        return False
    if {q_spec.activation, k_spec.activation, v_spec.activation} != {"split_qkv_heads"}:
        return False
    if len({q_spec.qkv_layout, k_spec.qkv_layout, v_spec.qkv_layout}) != 1:
        return False
    if o_spec.activation != "split_heads":
        return False

    qkv_layout = q_spec.qkv_layout
    q_heads = head_count_for_component(model, "q")
    kv_heads = head_count_for_component(model, "k")
    if q_heads != kv_heads:
        return False
    packed_axis = preferred_qkv_weight_packed_axis(q_module, architecture=adapter.name)
    if packed_axis is None:
        try:
            qkv_weight_shape = shape_of(q_module.weight)
            total_heads = q_heads + 2 * kv_heads
            if len(qkv_weight_shape) == 2:
                if int(qkv_weight_shape[0]) % total_heads == 0:
                    packed_axis = 0
                elif int(qkv_weight_shape[1]) % total_heads == 0:
                    packed_axis = 1
        except Exception:
            packed_axis = None
    if packed_axis not in {0, 1}:
        return False
    w_q = _joint_qkv_module_weight_to_tl(
        q_module,
        component="q",
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
        packed_axis=packed_axis,
    )
    w_k = _joint_qkv_module_weight_to_tl(
        q_module,
        component="k",
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
        packed_axis=packed_axis,
    )
    w_v = _joint_qkv_module_weight_to_tl(
        q_module,
        component="v",
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
        packed_axis=packed_axis,
    )
    b_q = _joint_qkv_module_bias_to_tl(
        model,
        q_module,
        component="q",
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
    )
    b_k = _joint_qkv_module_bias_to_tl(
        model,
        q_module,
        component="k",
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
    )
    b_v = _joint_qkv_module_bias_to_tl(
        model,
        q_module,
        component="v",
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
    )

    if not _qkv_ov_shapes_are_refactorable(
        model, w_q, w_k, w_v, o_module, architecture=adapter.name
    ):
        return False
    w_q_refactored, b_q_refactored, w_k_refactored, b_k_refactored = _refactor_qk_matrices(
        w_q,
        b_q,
        w_k,
        b_k,
    )
    w_o = _module_weight_to_tl(model, o_module, component="z", architecture=adapter.name)
    output_bias = getattr(o_module, "bias", None)
    if output_bias is None:
        output_bias = zeros_like_last_dim(
            o_module.weight,
            axis=_output_bias_axis(o_module, architecture=adapter.name),
        )
    folded_bias, zero_b_v = _fold_value_bias_tensor_like(
        b_v,
        w_o,
        output_bias,
        target_heads=head_count_for_component(model, "z"),
    )
    w_v_refactored, w_o_refactored = _refactor_ov_matrices(w_v, w_o)
    _set_module_weight(
        q_module,
        _merge_split_joint_qkv_weights(
            w_q_refactored,
            w_k_refactored,
            w_v_refactored,
            packed_axis=packed_axis,
            qkv_layout=qkv_layout,
        ),
    )
    _set_module_bias(
        q_module,
        _merge_split_joint_qkv_biases(
            b_q_refactored,
            b_k_refactored,
            zero_b_v,
            qkv_layout=qkv_layout,
        ),
    )
    _set_module_bias(o_module, folded_bias)
    _set_module_weight(
        o_module,
        _tl_attention_weight_to_module(
            w_o_refactored,
            o_module,
            component="z",
            architecture=adapter.name,
        ),
    )
    return True


def _qkv_ov_shapes_are_refactorable(
    model: Any,
    w_q: Any,
    w_k: Any,
    w_v: Any,
    o_module: Any,
    *,
    architecture: str,
) -> bool:
    try:
        w_o = _module_weight_to_tl(
            model,
            o_module,
            component="z",
            architecture=architecture,
        )
    except Exception:
        return False
    shape_q = shape_of(w_q)
    shape_k = shape_of(w_k)
    shape_v = shape_of(w_v)
    shape_o = shape_of(w_o)
    if len(shape_q) != 3 or len(shape_k) != 3 or len(shape_v) != 3 or len(shape_o) != 3:
        return False
    output_bias = getattr(o_module, "bias", None)
    if output_bias is not None:
        bias_shape = shape_of(output_bias)
        if not bias_shape or int(bias_shape[-1]) != int(shape_o[-1]):
            return False
    return (
        shape_q[0] == shape_k[0] == shape_v[0] == shape_o[0]
        and shape_q[2] == shape_k[2] == shape_v[2] == shape_o[1]
        and shape_v[1] == shape_o[2]
    )


def _attention_module_and_spec(
    model: Any, *, adapter: Any, component: str, layer: int
) -> tuple[Any, Any]:
    component_ref = adapter.parse_component_ref(transformer_lens_component_name(component, layer))
    if component_ref is None:
        raise KeyError(f"Unknown attention component {component!r}.")
    spec = adapter._spec_for_ref(component_ref, for_cache=True)
    return adapter.get_component(model, component_ref), spec


def _module_weight_to_tl(model: Any, module: Any, *, component: str, architecture: str) -> Any:
    weight = getattr(module, "weight", None)
    if weight is None:
        raise KeyError(f"Attention component {component!r} has no weight.")
    return reshape_attention_weight(
        weight,
        component=component,
        n_heads=head_count_for_component(model, component),
        packed_axis=preferred_attention_weight_packed_axis(
            module,
            architecture=architecture,
            component=component,
        ),
    )


def _module_bias_to_tl(model: Any, module: Any, *, component: str) -> Any:
    bias = getattr(module, "bias", None)
    if bias is None:
        return zeros_for_attention_bias(model, component)
    return reshape_attention_bias(
        bias,
        component=component,
        n_heads=head_count_for_component(model, component),
    )


def _joint_qkv_module_weight_to_tl(
    module: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: str,
    packed_axis: int | None,
) -> Any:
    weight = getattr(module, "weight", None)
    if weight is None:
        raise KeyError(f"Joint QKV component {component!r} has no weight.")
    return reshape_joint_qkv_attention_weight(
        weight,
        component=component,
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
        packed_axis=packed_axis,
    )


def _joint_qkv_module_bias_to_tl(
    model: Any,
    module: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: str,
) -> Any:
    bias = getattr(module, "bias", None)
    if bias is None:
        return zeros_for_attention_bias(model, component)
    return reshape_joint_qkv_attention_bias(
        bias,
        component=component,
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
    )


def _tl_attention_weight_to_module(
    weight: Any,
    module: Any,
    *,
    component: str,
    architecture: str,
) -> Any:
    packed_axis = preferred_attention_weight_packed_axis(
        module,
        architecture=architecture,
        component=component,
    )
    if component in {"q", "k", "v"}:
        if packed_axis == 0:
            return _reshape_tl_qkv_weight_for_rows(weight)
        if packed_axis == 1:
            return _reshape_tl_qkv_weight_for_columns(weight)
    if component == "z":
        if packed_axis == 0:
            return _reshape_tl_o_weight_for_rows(weight)
        if packed_axis == 1:
            return _reshape_tl_o_weight_for_columns(weight)
    raise ValueError(f"Unsupported attention weight layout for component {component!r}.")


def _tl_attention_bias_to_module(bias: Any, module: Any, *, component: str) -> Any:
    _ = module
    if component == "z":
        return bias
    return _flatten_leading_dims(bias)


def _merge_split_joint_qkv_weights(
    w_q: Any,
    w_k: Any,
    w_v: Any,
    *,
    packed_axis: int | None,
    qkv_layout: str,
) -> Any:
    if qkv_layout == "interleaved":
        return _merge_interleaved_joint_qkv_weights(
            w_q,
            w_k,
            w_v,
            packed_axis=packed_axis,
        )
    if qkv_layout != "split":
        raise ValueError(f"Unsupported QKV layout {qkv_layout!r}.")
    q_weight = _reshape_tl_qkv_weight_for_joint(w_q, packed_axis=packed_axis)
    k_weight = _reshape_tl_qkv_weight_for_joint(w_k, packed_axis=packed_axis)
    v_weight = _reshape_tl_qkv_weight_for_joint(w_v, packed_axis=packed_axis)
    return _concat_qkv_packed(q_weight, k_weight, v_weight, axis=packed_axis)


def _merge_split_joint_qkv_biases(
    b_q: Any,
    b_k: Any,
    b_v: Any,
    *,
    qkv_layout: str,
) -> Any:
    if qkv_layout == "interleaved":
        return _merge_interleaved_joint_qkv_biases(b_q, b_k, b_v)
    if qkv_layout != "split":
        raise ValueError(f"Unsupported QKV layout {qkv_layout!r}.")
    return _concat_qkv_packed(
        _flatten_leading_dims(b_q),
        _flatten_leading_dims(b_k),
        _flatten_leading_dims(b_v),
        axis=0,
    )


def _merge_interleaved_joint_qkv_weights(
    w_q: Any,
    w_k: Any,
    w_v: Any,
    *,
    packed_axis: int | None,
) -> Any:
    shape_q = shape_of(w_q)
    shape_k = shape_of(w_k)
    shape_v = shape_of(w_v)
    if shape_q != shape_k or shape_q != shape_v or len(shape_q) != 3:
        raise ValueError(
            "Interleaved joint QKV weight merge requires matching "
            f"[head, d_model, d_head] shapes, got {shape_q}, {shape_k}, {shape_v}."
        )
    n_heads, d_model, d_head = shape_q
    module = type(w_q).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            if packed_axis == 0:
                return torch.stack(
                    [
                        w_q.permute(0, 2, 1),
                        w_k.permute(0, 2, 1),
                        w_v.permute(0, 2, 1),
                    ],
                    dim=1,
                ).reshape(n_heads * 3 * d_head, d_model)
            if packed_axis == 1:
                return torch.stack([w_q, w_k, w_v], dim=2).reshape(d_model, n_heads * 3 * d_head)
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            if packed_axis == 0:
                return np.reshape(
                    np.stack(
                        [
                            np.swapaxes(w_q, 1, 2),
                            np.swapaxes(w_k, 1, 2),
                            np.swapaxes(w_v, 1, 2),
                        ],
                        axis=1,
                    ),
                    (n_heads * 3 * d_head, d_model),
                )
            if packed_axis == 1:
                return np.reshape(
                    np.stack([w_q, w_k, w_v], axis=2), (d_model, n_heads * 3 * d_head)
                )
        except Exception:
            pass
    if packed_axis == 0:
        q_values = _to_python_sequence_container(w_q)
        k_values = _to_python_sequence_container(w_k)
        v_values = _to_python_sequence_container(w_v)
        return [
            [source[head][model_dim][head_dim] for model_dim in range(d_model)]
            for head in range(n_heads)
            for source in (q_values, k_values, v_values)
            for head_dim in range(d_head)
        ]
    if packed_axis == 1:
        q_values = _to_python_sequence_container(w_q)
        k_values = _to_python_sequence_container(w_k)
        v_values = _to_python_sequence_container(w_v)
        return [
            [
                source[head][model_dim][head_dim]
                for head in range(n_heads)
                for source in (q_values, k_values, v_values)
                for head_dim in range(d_head)
            ]
            for model_dim in range(d_model)
        ]
    raise ValueError(
        f"packed_axis must be 0 or 1 for interleaved QKV weights, got {packed_axis!r}."
    )


def _merge_interleaved_joint_qkv_biases(b_q: Any, b_k: Any, b_v: Any) -> Any:
    shape_q = shape_of(b_q)
    shape_k = shape_of(b_k)
    shape_v = shape_of(b_v)
    if shape_q != shape_k or shape_q != shape_v or len(shape_q) != 2:
        raise ValueError(
            "Interleaved joint QKV bias merge requires matching [head, d_head] "
            f"shapes, got {shape_q}, {shape_k}, {shape_v}."
        )
    n_heads, d_head = shape_q
    module = type(b_q).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            return torch.stack([b_q, b_k, b_v], dim=1).reshape(n_heads * 3 * d_head)
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            return np.reshape(np.stack([b_q, b_k, b_v], axis=1), (n_heads * 3 * d_head,))
        except Exception:
            pass
    q_values = _to_python_sequence_container(b_q)
    k_values = _to_python_sequence_container(b_k)
    v_values = _to_python_sequence_container(b_v)
    return [
        source[head][head_dim]
        for head in range(n_heads)
        for source in (q_values, k_values, v_values)
        for head_dim in range(d_head)
    ]


def _reshape_tl_qkv_weight_for_joint(weight: Any, *, packed_axis: int | None) -> Any:
    if packed_axis == 0:
        return _reshape_tl_qkv_weight_for_rows(weight)
    if packed_axis == 1:
        return _reshape_tl_qkv_weight_for_columns(weight)
    raise ValueError(f"packed_axis must be 0 or 1 for joint QKV weights, got {packed_axis!r}.")


def _concat_qkv_packed(q_value: Any, k_value: Any, v_value: Any, *, axis: int | None) -> Any:
    if axis not in {0, 1}:
        raise ValueError(f"packed axis must be 0 or 1, got {axis!r}.")
    module = type(q_value).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            return torch.cat([q_value, k_value, v_value], dim=axis)
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            return np.concatenate([q_value, k_value, v_value], axis=axis)
        except Exception:
            pass
    q_values = _to_python_sequence_container(q_value)
    k_values = _to_python_sequence_container(k_value)
    v_values = _to_python_sequence_container(v_value)
    if axis == 0:
        return [*q_values, *k_values, *v_values]
    return [
        [*q_row, *k_row, *v_row]
        for q_row, k_row, v_row in zip(q_values, k_values, v_values, strict=True)
    ]


def _reshape_tl_qkv_weight_for_rows(weight: Any) -> Any:
    module = type(weight).__module__.split(".")[0]
    shape = shape_of(weight)
    if len(shape) != 3:
        raise ValueError(f"Expected TL q/k/v weight shape [head, d_model, d_head], got {shape}.")
    n_heads, d_model, d_head = shape
    if module == "torch":
        return weight.permute(0, 2, 1).reshape(n_heads * d_head, d_model)
    if module == "numpy":
        try:
            import numpy as np

            return np.reshape(np.swapaxes(weight, 1, 2), (n_heads * d_head, d_model))
        except Exception:
            pass
    values = _to_python_sequence_container(weight)
    return [
        [values[head][model_dim][head_dim] for model_dim in range(d_model)]
        for head in range(n_heads)
        for head_dim in range(d_head)
    ]


def _reshape_tl_qkv_weight_for_columns(weight: Any) -> Any:
    module = type(weight).__module__.split(".")[0]
    shape = shape_of(weight)
    if len(shape) != 3:
        raise ValueError(f"Expected TL q/k/v weight shape [head, d_model, d_head], got {shape}.")
    n_heads, d_model, d_head = shape
    if module == "torch":
        return weight.permute(1, 0, 2).reshape(d_model, n_heads * d_head)
    if module == "numpy":
        try:
            import numpy as np

            return np.reshape(np.swapaxes(weight, 0, 1), (d_model, n_heads * d_head))
        except Exception:
            pass
    values = _to_python_sequence_container(weight)
    return [
        [values[head][model_dim][head_dim] for head in range(n_heads) for head_dim in range(d_head)]
        for model_dim in range(d_model)
    ]


def _reshape_tl_o_weight_for_rows(weight: Any) -> Any:
    module = type(weight).__module__.split(".")[0]
    shape = shape_of(weight)
    if len(shape) != 3:
        raise ValueError(f"Expected TL output weight shape [head, d_head, d_model], got {shape}.")
    n_heads, d_head, d_model = shape
    if module == "torch":
        return weight.reshape(n_heads * d_head, d_model)
    if module == "numpy":
        try:
            import numpy as np

            return np.reshape(weight, (n_heads * d_head, d_model))
        except Exception:
            pass
    values = _to_python_sequence_container(weight)
    return [list(values[head][head_dim]) for head in range(n_heads) for head_dim in range(d_head)]


def _reshape_tl_o_weight_for_columns(weight: Any) -> Any:
    module = type(weight).__module__.split(".")[0]
    shape = shape_of(weight)
    if len(shape) != 3:
        raise ValueError(f"Expected TL output weight shape [head, d_head, d_model], got {shape}.")
    n_heads, d_head, d_model = shape
    if module == "torch":
        return weight.permute(2, 0, 1).reshape(d_model, n_heads * d_head)
    if module == "numpy":
        try:
            import numpy as np

            return np.reshape(np.moveaxis(weight, 2, 0), (d_model, n_heads * d_head))
        except Exception:
            pass
    values = _to_python_sequence_container(weight)
    return [
        [values[head][head_dim][model_dim] for head in range(n_heads) for head_dim in range(d_head)]
        for model_dim in range(d_model)
    ]


def _flatten_leading_dims(value: Any) -> Any:
    module = type(value).__module__.split(".")[0]
    shape = shape_of(value)
    if len(shape) <= 1:
        return value
    if module == "torch":
        return value.reshape(math.prod(shape))
    if module == "numpy":
        try:
            return value.reshape(math.prod(shape))
        except Exception:
            pass
    return _flatten_nested(_to_python_sequence_container(value))


def _refactor_ov_matrices(w_v: Any, w_o: Any) -> tuple[Any, Any]:
    """Return an equivalent TL OV factorization using `W_V=U*S`, `W_O=V.T`."""
    ov = FactoredMatrix(w_v, w_o)
    return ov.collapse_r(), transpose(ov.V)


def _refactor_qk_matrices(
    w_q: Any,
    b_q: Any | None,
    w_k: Any,
    b_k: Any | None,
) -> tuple[Any, Any, Any, Any]:
    """Return an equivalent TL QK factorization, preserving optional biases."""
    effective_w_q = _append_attention_bias_as_input(w_q, b_q)
    effective_w_k = _append_attention_bias_as_input(w_k, b_k)
    refactored_q, refactored_k_t = (
        FactoredMatrix(
            effective_w_q,
            transpose(effective_w_k),
        )
        .make_even()
        .pair
    )
    refactored_k = transpose(refactored_k_t)
    return (
        _slice_penultimate_dim(refactored_q, slice(None, -1)),
        _slice_penultimate_dim(refactored_q, -1),
        _slice_penultimate_dim(refactored_k, slice(None, -1)),
        _slice_penultimate_dim(refactored_k, -1),
    )


def _append_attention_bias_as_input(weight: Any, bias: Any | None) -> Any:
    if bias is None:
        bias = _zero_attention_bias_like_weight(weight)
    module = type(weight).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            if not isinstance(bias, torch.Tensor):
                bias = torch.as_tensor(bias, dtype=weight.dtype, device=weight.device)
            return torch.cat([weight, bias.unsqueeze(-2)], dim=-2)
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            return np.concatenate([weight, np.expand_dims(bias, axis=-2)], axis=-2)
        except Exception:
            pass
    if _is_sequence(weight):
        return [
            _append_attention_bias_as_input(weight_item, bias_item)
            for weight_item, bias_item in zip(weight, bias, strict=True)
        ]
    raise TypeError(f"Cannot append attention bias for weight type {type(weight).__name__}.")


def _zero_attention_bias_like_weight(weight: Any) -> Any:
    shape = shape_of(weight)
    if len(shape) < 2:
        raise ValueError(f"Attention weight must be at least rank-2, got {shape}.")
    module = type(weight).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            return torch.zeros(
                (*shape[:-2], shape[-1]),
                dtype=getattr(weight, "dtype", None),
                device=getattr(weight, "device", None),
            )
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            return np.zeros((*shape[:-2], shape[-1]), dtype=getattr(weight, "dtype", None))
        except Exception:
            pass
    if _is_sequence(weight):
        if len(shape) == 2:
            return [_zero_like_tensor_value(item) for item in weight[0]]
        return [_zero_attention_bias_like_weight(item) for item in weight]
    raise TypeError(f"Cannot create zero attention bias for weight type {type(weight).__name__}.")


def _slice_penultimate_dim(value: Any, selector: Any) -> Any:
    try:
        return value[..., selector, :]
    except Exception:
        pass
    shape = shape_of(value)
    if len(shape) < 2:
        raise ValueError(f"Expected rank >= 2 value, got {shape}.")
    if len(shape) == 2:
        return value[selector]
    if _is_sequence(value):
        return [_slice_penultimate_dim(item, selector) for item in value]
    raise TypeError(f"Cannot slice penultimate dimension of {type(value).__name__}.")


def _uses_rotary_embeddings(model: Any) -> bool:
    config = _config_attr(model, "config")
    core_config = _core_model_config(config)
    for owner in (core_config, config, model):
        if owner is None:
            continue
        positional_type = _config_attr(owner, "positional_embedding_type")
        if isinstance(positional_type, str) and positional_type.lower() == "rotary":
            return True
        position_type = _config_attr(owner, "position_embedding_type")
        if isinstance(position_type, str) and position_type.lower() in {"rotary", "rope"}:
            return True
        if _config_attr(owner, "rotary_emb") is not None:
            return True
        rope_scaling = _config_attr(owner, "rope_scaling")
        if rope_scaling:
            return True
        if (
            _config_attr(owner, "rope_theta") is not None
            or _config_attr(owner, "rotary_dim") is not None
        ):
            return True
        if (
            _config_attr(owner, "rotary_pct") is not None
            or _config_attr(owner, "rope_parameters") is not None
        ):
            return float(get_rotary_pct_from_config(owner)) > 0.0
    return False


def _infer_positional_embedding_type(model: Any) -> str | None:
    config = _config_attr(model, "config")
    core_config = _core_model_config(config)
    for owner in (core_config, config, model):
        if owner is None:
            continue
        positional_type = _config_attr(owner, "positional_embedding_type")
        if isinstance(positional_type, str) and positional_type:
            return positional_type.lower()
        position_type = _config_attr(owner, "position_embedding_type")
        if isinstance(position_type, str) and position_type:
            normalized = position_type.lower()
            if normalized in {"rotary", "rope"}:
                return "rotary"
            if normalized == "absolute":
                return "standard"
            return normalized
    if _uses_rotary_embeddings(model):
        return "rotary"
    if _positional_embeddings_module(model) is not None:
        return "standard"
    return None


def _value_bias_to_tl_shape(
    model: Any,
    module: Any,
    bias: Any,
    spec: Any,
    *,
    architecture: str,
) -> Any:
    if spec.activation == "split_qkv_heads":
        component_bias, n_heads = extract_qkv_bias(
            bias,
            component="v",
            q_heads=head_count_for_component(model, "q"),
            kv_heads=head_count_for_component(model, "k"),
            qkv_layout=spec.qkv_layout,
        )
        return reshape_attention_bias(component_bias, component="v", n_heads=n_heads)
    return reshape_attention_bias(
        bias,
        component="v",
        n_heads=head_count_for_component(model, "v"),
    )


def _zero_value_bias_module(
    model: Any,
    module: Any,
    bias: Any,
    spec: Any,
    *,
    architecture: str,
) -> None:
    if spec.activation != "split_qkv_heads":
        _set_module_bias(module, _zero_like_tensor_value(bias))
        return
    q_heads = head_count_for_component(model, "q")
    kv_heads = head_count_for_component(model, "k")
    zeroed = _zero_joint_qkv_value_bias(
        bias,
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=spec.qkv_layout,
    )
    _set_module_bias(module, zeroed)


def _zero_joint_qkv_value_bias(
    bias: Any,
    *,
    q_heads: int,
    kv_heads: int,
    qkv_layout: str,
) -> Any:
    shape = shape_of(bias)
    if len(shape) != 1:
        raise ValueError(f"Joint QKV bias must be rank 1, got shape {shape}.")
    total_heads = q_heads + 2 * kv_heads
    if total_heads <= 0 or int(shape[0]) % total_heads != 0:
        raise ValueError(
            "Cannot split joint QKV bias with length "
            f"{shape[0]}, q_heads={q_heads}, kv_heads={kv_heads}."
        )
    head_dim = int(shape[0]) // total_heads
    zeroed = _clone_tensor_like(bias)
    if qkv_layout == "split":
        start, stop = qkv_weight_bounds(head_dim, q_heads=q_heads, kv_heads=kv_heads)["v"]
        return _set_flat_slice_to_zero(zeroed, start, stop)
    if qkv_layout == "interleaved":
        return _zero_interleaved_value_bias(
            zeroed,
            head_dim=head_dim,
            q_heads=q_heads,
            kv_heads=kv_heads,
        )
    raise ValueError(f"Unsupported QKV layout {qkv_layout!r}.")


def _zero_interleaved_value_bias(
    bias: Any,
    *,
    head_dim: int,
    q_heads: int,
    kv_heads: int,
) -> Any:
    if type(bias).__module__.split(".")[0] == "torch":
        try:
            if q_heads == kv_heads:
                view = bias.reshape(q_heads, 3, head_dim)
                view[:, 2, :] = 0
                return bias
            q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
            view = bias.reshape(kv_heads, q_per_group + 2, head_dim)
            view[:, -1, :] = 0
            return bias
        except Exception:
            pass
    if type(bias).__module__.split(".")[0] == "numpy":
        try:
            if q_heads == kv_heads:
                view = bias.reshape(q_heads, 3, head_dim)
                view[:, 2, :] = 0
                return bias
            q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
            view = bias.reshape(kv_heads, q_per_group + 2, head_dim)
            view[:, -1, :] = 0
            return bias
        except Exception:
            pass
    values = _to_python_sequence_container(bias)
    if q_heads == kv_heads:
        view = _reshape_flat_sequence(values, (q_heads, 3, head_dim))
        for head in range(q_heads):
            view[head][2] = [_zero_like_tensor_value(item) for item in view[head][2]]
        return _flatten_nested(view)
    q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
    view = _reshape_flat_sequence(values, (kv_heads, q_per_group + 2, head_dim))
    for head in range(kv_heads):
        view[head][-1] = [_zero_like_tensor_value(item) for item in view[head][-1]]
    return _flatten_nested(view)


def _set_flat_slice_to_zero(value: Any, start: int, stop: int) -> Any:
    if type(value).__module__.split(".")[0] == "torch":
        try:
            value[start:stop] = 0
            return value
        except Exception:
            pass
    if type(value).__module__.split(".")[0] == "numpy":
        try:
            value[start:stop] = 0
            return value
        except Exception:
            pass
    values = _to_python_sequence_container(value)
    return [
        _zero_like_tensor_value(item) if start <= index < stop else item
        for index, item in enumerate(values)
    ]


def _fold_value_bias_tensor_like(
    b_v: Any,
    w_o: Any,
    b_o: Any | None,
    *,
    target_heads: int | None,
) -> tuple[Any, Any]:
    aligned_b_v = _align_value_bias_heads(b_v, target_heads=target_heads)
    contribution = _value_bias_output_contribution(aligned_b_v, w_o)
    if b_o is None:
        b_o = zeros_like_last_dim(w_o, axis=-1)
    folded_bias = _add_tensor_like_values(b_o, contribution)
    return folded_bias, _zero_like_tensor_value(b_v)


def _align_value_bias_heads(b_v: Any, *, target_heads: int | None) -> Any:
    if target_heads is None:
        return b_v
    shape = shape_of(b_v)
    if len(shape) < 2:
        return b_v
    source_heads = int(shape[-2])
    if source_heads == int(target_heads):
        return b_v
    if source_heads <= 0 or int(target_heads) % source_heads != 0:
        raise ValueError(
            f"Cannot align value bias with {source_heads} heads to {target_heads} heads."
        )
    repeats = int(target_heads) // source_heads
    return _repeat_value_bias_heads(b_v, repeats=repeats)


def _repeat_value_bias_heads(value: Any, *, repeats: int) -> Any:
    repeat_interleave = getattr(value, "repeat_interleave", None)
    if callable(repeat_interleave):
        try:
            return repeat_interleave(repeats, dim=-2)
        except Exception:
            pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.repeat(value, repeats, axis=-2)
    except Exception:
        pass
    if _is_sequence(value):
        shape = shape_of(value)
        axis = len(shape) - 2
        return _repeat_nested_axis(value, axis=axis, repeats=repeats)
    raise TypeError(f"Cannot repeat value bias heads for type {type(value).__name__}.")


def _repeat_nested_axis(value: Any, *, axis: int, repeats: int) -> Any:
    if axis == 0:
        return [_clone_tensor_like(item) for item in value for _repeat_index in range(repeats)]
    return [_repeat_nested_axis(item, axis=axis - 1, repeats=repeats) for item in value]


def _value_bias_output_contribution(b_v: Any, w_o: Any) -> Any:
    if (
        type(b_v).__module__.split(".")[0] == "torch"
        or type(w_o).__module__.split(".")[0] == "torch"
    ):
        try:
            import torch

            if not hasattr(b_v, "shape"):
                b_v = torch.as_tensor(
                    b_v,
                    dtype=getattr(w_o, "dtype", None),
                    device=getattr(w_o, "device", None),
                )
            if not hasattr(w_o, "shape"):
                w_o = torch.as_tensor(
                    w_o,
                    dtype=getattr(b_v, "dtype", None),
                    device=getattr(b_v, "device", None),
                )
            return torch.einsum("...hd,...hdm->...m", b_v, w_o)
        except Exception:
            pass
    if (
        type(b_v).__module__.split(".")[0] == "numpy"
        or type(w_o).__module__.split(".")[0] == "numpy"
    ):
        try:
            import numpy as np

            return np.einsum("...hd,...hdm->...m", b_v, w_o)
        except Exception:
            pass
    return _value_bias_output_contribution_nested(b_v, w_o)


def _value_bias_output_contribution_nested(b_v: Any, w_o: Any) -> list[float]:
    b_v_values = _to_python_sequence_container(b_v)
    w_o_values = _to_python_sequence_container(w_o)
    shape_b = shape_of(b_v_values)
    shape_w = shape_of(w_o_values)
    if len(shape_b) > 2 and len(shape_w) > 3:
        if shape_b[:-2] != shape_w[:-3]:
            raise ValueError(f"Cannot fold b_V shape {shape_b} with W_O shape {shape_w}.")
        return [
            _value_bias_output_contribution_nested(b_item, w_item)
            for b_item, w_item in zip(b_v_values, w_o_values, strict=True)
        ]
    if len(shape_b) != 2 or len(shape_w) != 3:
        raise ValueError(
            "Expected b_V [head, d_head] and W_O [head, d_head, d_model], "
            f"got {shape_b} and {shape_w}."
        )
    if shape_b[0] != shape_w[0] or shape_b[1] != shape_w[1]:
        raise ValueError(f"Cannot fold b_V shape {shape_b} with W_O shape {shape_w}.")
    d_model = int(shape_w[2])
    return [
        sum(
            float(b_v_values[head][head_dim]) * float(w_o_values[head][head_dim][model_dim])
            for head in range(int(shape_b[0]))
            for head_dim in range(int(shape_b[1]))
        )
        for model_dim in range(d_model)
    ]


def _output_bias_axis(module: Any, *, architecture: str) -> int:
    packed_axis = preferred_attention_weight_packed_axis(
        module,
        architecture=architecture,
        component="z",
    )
    return 1 - packed_axis if packed_axis in {0, 1} else -1


def _center_residual_stream_weight(weight: Any, *, d_model: int | None) -> Any:
    return _center_tensor_like(weight, axis=_residual_axis_from_d_model(weight, d_model=d_model))


def _center_residual_stream_bias(bias: Any) -> Any:
    return _center_bias_like(bias)


def _residual_axis_from_d_model(weight: Any, *, d_model: int | None) -> int:
    shape = shape_of(weight)
    if len(shape) >= 1 and d_model is not None:
        if int(shape[-1]) == int(d_model):
            return -1
        if int(shape[0]) == int(d_model):
            return 0
    return -1


def _center_tensor_like(value: Any, *, axis: int) -> Any:
    module = type(value).__module__.split(".")[0]
    if module == "torch":
        try:
            return value - value.mean(dim=axis, keepdim=True)
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            return value - np.mean(value, axis=axis, keepdims=True)
        except Exception:
            pass
    if _is_sequence(value):
        return _center_nested_along_axis(value, axis=axis)
    raise TypeError(f"Cannot center value of type {type(value).__name__}.")


def _center_bias_like(value: Any) -> Any:
    module = type(value).__module__.split(".")[0]
    if module == "torch":
        try:
            return value - value.mean()
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            return value - np.mean(value)
        except Exception:
            pass
    if _is_sequence(value):
        flattened = [float(item) for item in _flatten_nested(value)]
        if not flattened:
            return _to_python_sequence_container(value)
        mean = sum(flattened) / len(flattened)
        return _map_nested_scalars(value, lambda item: float(item) - mean)
    return float(value) - float(value)


def _center_nested_along_axis(value: Any, *, axis: int) -> Any:
    shape = shape_of(value)
    if not shape:
        return float(value) - float(value)
    if axis < 0:
        axis = len(shape) + axis
    if axis < 0 or axis >= len(shape):
        raise ValueError(f"Cannot center shape {shape} along axis {axis}.")
    return _center_nested_axis(_to_python_sequence_container(value), axis)


def _center_nested_axis(value: Any, axis: int) -> Any:
    if axis == 0:
        if not _is_sequence(value):
            return 0.0
        rows = [_to_python_sequence_container(row) for row in value]
        if not rows:
            return []
        mean = _nested_mean_same_shape(rows)
        return [_subtract_nested(row, mean) for row in rows]
    if not _is_sequence(value):
        raise ValueError("Cannot center a scalar along a non-zero axis.")
    return [_center_nested_axis(item, axis - 1) for item in value]


def _nested_mean_same_shape(values: Sequence[Any]) -> Any:
    first = values[0]
    if _is_sequence(first):
        width = len(first)
        if any(not _is_sequence(value) or len(value) != width for value in values):
            raise ValueError("Cannot center ragged nested values.")
        return [
            _nested_mean_same_shape([value[index] for value in values]) for index in range(width)
        ]
    return sum(float(value) for value in values) / len(values)


def _subtract_nested(value: Any, mean: Any) -> Any:
    if _is_sequence(value) and _is_sequence(mean):
        return [
            _subtract_nested(item, mean_item) for item, mean_item in zip(value, mean, strict=True)
        ]
    return float(value) - float(mean)


def _map_nested_scalars(value: Any, fn: Callable[[Any], Any]) -> Any:
    if _is_sequence(value):
        return [_map_nested_scalars(item, fn) for item in value]
    return fn(value)


def _flatten_nested(value: Any) -> list[Any]:
    if _is_sequence(value):
        flattened: list[Any] = []
        for item in value:
            flattened.extend(_flatten_nested(item))
        return flattened
    return [value]


def _reshape_flat_sequence(values: Sequence[Any], dims: tuple[int, ...]) -> Any:
    if not dims:
        if len(values) != 1:
            raise ValueError("Cannot reshape non-scalar sequence into scalar.")
        return values[0]
    expected = math.prod(dims)
    if len(values) != expected:
        raise ValueError(f"Cannot reshape sequence of length {len(values)} into {dims}.")
    if len(dims) == 1:
        return list(values)
    stride = math.prod(dims[1:])
    return [
        _reshape_flat_sequence(values[index * stride : (index + 1) * stride], dims[1:])
        for index in range(dims[0])
    ]


def _set_module_weight(module: Any, value: Any) -> None:
    _set_module_tensor_attr(module, "weight", value)


def _set_module_bias(module: Any, value: Any) -> None:
    _set_module_tensor_attr(module, "bias", value)


def _set_module_tensor_attr(module: Any, attr: str, value: Any) -> None:
    current = getattr(module, attr, None)
    data = getattr(current, "data", None)
    if data is not None and _module_accepts_registered_parameter(module):
        copy_value = value
        to_fn = getattr(copy_value, "to", None)
        if callable(to_fn):
            copy_value = to_fn(device=data.device, dtype=data.dtype)
        data.copy_(copy_value)
        return
    try:
        setattr(module, attr, value)
        return
    except Exception as exc:
        if current is None and _module_accepts_registered_parameter(module):
            _register_module_parameter(module, attr, value)
            return
        raise RuntimeError(f"Could not update module {attr}.") from exc


def _module_accepts_registered_parameter(module: Any) -> bool:
    try:
        import torch
    except Exception:
        return False
    return isinstance(module, torch.nn.Module)


def _register_module_parameter(module: Any, attr: str, value: Any) -> None:
    import torch

    tensor = value if isinstance(value, torch.Tensor) else torch.as_tensor(value)
    module.register_parameter(attr, torch.nn.Parameter(tensor.detach().clone()))


def _center_unembed_weight(weight: Any, *, weight_layout: str) -> Any:
    """Center unembed columns for TL-style W_U or HF output-embedding weights."""
    dim = 0 if weight_layout == "vocab_d_model" else -1
    module = type(weight).__module__.split(".")[0]
    if module == "torch":
        try:
            return weight - weight.mean(dim=dim, keepdim=True)
        except Exception:
            pass
    if module == "numpy":
        try:
            import numpy as np

            return weight - np.mean(weight, axis=dim, keepdims=True)
        except Exception:
            pass
    if _is_sequence(weight):
        if weight_layout == "vocab_d_model":
            return _center_vocab_d_model_nested(weight)
        return [_center_vector_nested(row) for row in weight]
    raise TypeError(f"Cannot center unembedding weight of type {type(weight).__name__}.")


def _center_vocab_d_model_nested(weight: Sequence[Any]) -> list[list[float]]:
    rows = [list(row) for row in weight]
    if not rows:
        return []
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Cannot center ragged unembedding weight.")
    means = [sum(float(row[col]) for row in rows) / len(rows) for col in range(width)]
    return [[float(value) - means[col] for col, value in enumerate(row)] for row in rows]


def _center_vector_nested(vector: Sequence[Any]) -> list[float]:
    values = [float(value) for value in vector]
    if not values:
        return []
    mean = sum(values) / len(values)
    return [value - mean for value in values]


def _coerce_sequence_to_tensor_like(value: Sequence[Any], like: Any) -> Any | None:
    module = type(like).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            return torch.as_tensor(
                list(value),
                dtype=getattr(like, "dtype", None),
                device=getattr(like, "device", None),
            )
        except Exception:
            return None
    if module == "numpy":
        try:
            import numpy as np

            return np.asarray(list(value), dtype=getattr(like, "dtype", None))
        except Exception:
            return None
    return None


def _mask_composition_scores_to_future_layers(scores: Any) -> Any:
    shape = shape_of(scores)
    if len(shape) < 4:
        raise ValueError(
            f"Composition scores must have shape [layer, head, layer, head], got {shape}."
        )
    left_layers, right_layers = int(shape[0]), int(shape[2])

    if type(scores).__module__.split(".")[0] == "torch":
        try:
            import torch

            left_layer = torch.arange(left_layers, device=getattr(scores, "device", None))
            right_layer = torch.arange(right_layers, device=getattr(scores, "device", None))
            mask = left_layer[:, None, None, None] < right_layer[None, None, :, None]
            return torch.where(mask, scores, torch.zeros_like(scores))
        except Exception:
            pass
    if type(scores).__module__.split(".")[0] == "numpy":
        try:
            import numpy as np

            left_layer = np.arange(left_layers)
            right_layer = np.arange(right_layers)
            mask = left_layer[:, None, None, None] < right_layer[None, None, :, None]
            return np.where(mask, scores, np.zeros_like(scores))
        except Exception:
            pass
    if _is_sequence(scores):
        return [
            [
                [
                    [
                        score if left_layer < right_layer else _zero_like_tensor_value(score)
                        for score in right_head_scores
                    ]
                    for right_layer, right_head_scores in enumerate(left_head_scores)
                ]
                for left_head_scores in left_layer_scores
            ]
            for left_layer, left_layer_scores in enumerate(scores)
        ]
    raise TypeError(f"Cannot mask composition scores for value type {type(scores).__name__}.")


def _zero_like_tensor_value(value: Any) -> Any:
    if _is_sequence(value):
        return [_zero_like_tensor_value(item) for item in value]
    zeros_like = getattr(value, "zeros_like", None)
    if callable(zeros_like):
        try:
            return zeros_like(value)
        except Exception:
            pass
    try:
        return value * 0
    except Exception:
        return 0


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _concat_first_dim(left: Any, right: Any) -> Any:
    if type(left).__module__.split(".")[0] == "torch":
        try:
            import torch

            return torch.cat([left, right], dim=0)
        except ImportError:
            pass
    if _is_sequence(left) and _is_sequence(right):
        return [
            *_to_python_sequence_container(left),
            *_to_python_sequence_container(right),
        ]
    concatenate = getattr(left, "concatenate", None)
    if callable(concatenate):
        return concatenate([left, right], axis=0)
    return [*left, *right]


def _gather_sequence_residual_directions(weight: Sequence[Any], tokens: Any) -> Any:
    tolist = getattr(tokens, "tolist", None)
    if callable(tolist):
        tokens = tolist()
    if isinstance(tokens, Integral):
        return _to_python_sequence_container(weight[int(tokens)])
    if isinstance(tokens, Sequence) and not isinstance(tokens, str | bytes):
        return [_gather_sequence_residual_directions(weight, token) for token in tokens]
    item = getattr(tokens, "item", None)
    if callable(item):
        return _to_python_sequence_container(weight[int(item())])
    return _to_python_sequence_container(weight[int(tokens)])


def _to_python_sequence_container(value: Any) -> Any:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_to_python_sequence_container(item) for item in value]
    return value


def _coerce_tokens_for_weight_index(weight: Any, tokens: Any) -> Any:
    """Convert Python token containers into backend index arrays before advanced indexing."""
    if isinstance(tokens, Integral):
        return int(tokens)
    item = getattr(tokens, "item", None)
    shape = getattr(tokens, "shape", None)
    if callable(item) and shape is not None and len(tuple(int(dim) for dim in shape)) == 0:
        return int(item())
    if not isinstance(tokens, Sequence) or isinstance(tokens, str | bytes):
        return tokens
    try:
        import torch

        if isinstance(weight, torch.Tensor):
            return torch.as_tensor(tokens, dtype=torch.long, device=weight.device)
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(weight, np.ndarray):
            return np.asarray(tokens, dtype=np.int64)
    except Exception:
        pass
    return tokens


def _wrapper_looks_like_local_path(value: str) -> bool:
    path = Path(value).expanduser()
    return (
        value.startswith((".", "/", "~"))
        or path.exists()
        or any(separator in value for separator in ("/", "\\"))
        and not _wrapper_looks_like_remote_model_id(value)
    )


def _wrapper_looks_like_remote_model_id(value: str) -> bool:
    return bool(value and not value.startswith((".", "/", "~")) and value.count("/") == 1)


def _first_present(batch: Batch, keys: Sequence[str]) -> Any:
    for key in keys:
        if key in batch:
            return batch[key]
    return None


class LocalModelWrapper(HuggingFaceModelWrapper):
    """Transformers-compatible local directory wrapper with no provider download."""


class ModelScopeModelWrapper(HuggingFaceModelWrapper):
    """ModelScope-backed wrapper that downloads a snapshot, then loads it with Transformers."""

    def __init__(
        self,
        name: str,
        dtype: str = "float32",
        device: str | None = None,
        revision: str | None = None,
        cache_dir: str | None = None,
        local_dir: str | None = None,
        trust_remote_code: bool = False,
        load_kwargs: dict[str, Any] | None = None,
        tokenizer_kwargs: dict[str, Any] | None = None,
        modelscope_kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            dtype=dtype,
            device=device,
            revision=revision,
            cache_dir=cache_dir,
            trust_remote_code=trust_remote_code,
            load_kwargs=load_kwargs,
            tokenizer_kwargs=tokenizer_kwargs,
        )
        self.local_dir = local_dir
        self.modelscope_kwargs = modelscope_kwargs or {}

    def _resolve_pretrained_path(self) -> str:
        try:
            from modelscope import snapshot_download
        except ImportError as exc:
            raise ImportError(
                "ModelScopeModelWrapper requires ModelScope dependencies. "
                "Install them with `pip install -e '.[modelscope]'`."
            ) from exc

        kwargs = dict(self.modelscope_kwargs)
        if self.revision is not None:
            kwargs["revision"] = self.revision
        if self.cache_dir is not None:
            kwargs["cache_dir"] = self.cache_dir
        if self.local_dir is not None:
            kwargs["local_dir"] = self.local_dir
        return str(snapshot_download(model_id=self.name, **kwargs))

    def _pretrained_kwargs(self) -> dict[str, Any]:
        return {}


def build_model_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    """Build the configured model wrapper."""
    register_builtin_model_adapters()
    if config.name.lower() in {"dummy", "mock", "none"}:
        return DummyModelWrapper(name=config.name)
    return get_model_adapter_registry().create(config)


_MODEL_ADAPTERS_REGISTERED = False


def register_builtin_model_adapters() -> None:
    """Register SafeLens built-in model adapters once."""
    global _MODEL_ADAPTERS_REGISTERED
    if _MODEL_ADAPTERS_REGISTERED:
        return

    registry = get_model_adapter_registry()
    registry.register(
        ModelAdapterSpec(
            name="dummy",
            display_name="Dummy",
            aliases=("mock", "none"),
            description="In-memory adapter for tests, CI, and architecture demos.",
            dependencies=(),
            model_name_patterns=("dummy", "mock", "none"),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=("integer layer refs", "string layer refs"),
                supported_patches=("replace", "add"),
                supports_local_path=False,
                supports_remote_download=False,
                cache_policy="no external cache",
                notes=("Does not download or execute model code.",),
            ),
            build=_build_dummy_wrapper,
            inspect=_inspect_dummy_model,
            matches_model_name=lambda name: name.lower() in {"dummy", "mock", "none"},
            priority=100,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="qwen3_dense",
            display_name="Qwen3 Dense",
            aliases=("qwen3", "qwen3-dense"),
            description="Qwen3 dense <=35B adapter with component-level hooks.",
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=("Qwen/Qwen3-{0.6,1.7,4,8,14,32}B",),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=tuple(qwen3_supported_hook_components(include_attention=True)),
                supported_patches=(
                    "resid_pre",
                    "resid_mid",
                    "resid_post",
                    "attn_out",
                    "mlp_out",
                    "pre",
                    "pre_linear",
                    "post",
                    "q",
                    "k",
                    "v",
                    "z",
                    "result",
                    "pattern",
                    "attn_scores",
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=False,
                supports_remote_download=True,
                cache_policy="SafeLens cache_dir -> .cache/safelens/models/huggingface",
                notes=(
                    "Attention result hooks are implemented by deriving per-head "
                    "z @ W_O results and writing patched head-result deltas back "
                    "to the merged attention output.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_qwen3_dense_wrapper,
            inspect=_inspect_qwen3_dense_model,
            matches_model_name=lambda name: (
                "qwen3" in name.lower() and not is_qwen_routed_moe_model_name(name)
            ),
            priority=200,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="transformer_lens",
            display_name="TransformerLens-Compatible Transformers",
            aliases=("transformerlens", "tl", "hooked_transformer"),
            description=(
                "Independent SafeLens adapter for model families mirrored from "
                "TransformerLens supported models and architecture bridge coverage."
            ),
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=(
                "gpt2",
                "EleutherAI/pythia-*",
                "meta-llama/*",
                "Qwen/Qwen*",
                "google/gemma-*",
                "google-bert/bert-*",
                "FacebookAI/roberta-*",
                "distilbert/distilbert-*",
                "google-t5/t5-*",
                "facebook/wav2vec2-*",
                "facebook/hubert-*",
                "state-spaces/mamba-*",
                "mistralai/Mamba-Codestral-*",
            ),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=True,
                supports_remote_download=True,
                cache_policy=(
                    "SafeLens cache_dir -> .cache/safelens/models/transformer_lens_compatible"
                ),
                notes=(
                    "No TransformerLens runtime dependency is used.",
                    "Decoder, encoder-decoder, encoder, and audio-encoder families "
                    "load through Transformers auto classes.",
                    "SafeLens architecture adapters map HF module paths to canonical "
                    "components for GPT-2, GPT-J, GPT-Neo, GPT-NeoX/Pythia, "
                    "BLOOM/Falcon, MPT, Phi, OPT, BERT/RoBERTa, DistilBERT, "
                    "T5, Wav2Vec2/Hubert, Mamba/Mamba2 SSMs, and LLaMA-like "
                    "decoder families.",
                    "Attention result hooks are implemented by deriving per-head "
                    "z @ W_O results and writing patched head-result deltas back "
                    "to the merged attention output.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_transformer_lens_compatible_wrapper,
            inspect=_inspect_transformer_lens_compatible_model,
            matches_model_name=is_transformer_lens_supported_model_name,
            priority=90,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="huggingface",
            display_name="HuggingFace Transformers",
            aliases=("hf",),
            description="Generic Transformers causal language model adapter.",
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=("organization/model-name",),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer decoder layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=False,
                supports_remote_download=True,
                cache_policy="SafeLens cache_dir -> .cache/safelens/models/huggingface",
                notes=(
                    "Component hooks use SafeLens architecture adapters when the "
                    "loaded Transformers architecture is recognized.",
                    "Attention result hooks are implemented by deriving per-head "
                    "z @ W_O results and writing patched head-result deltas back "
                    "to the merged attention output.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_huggingface_wrapper,
            inspect=_inspect_huggingface_model,
            matches_model_name=lambda name: "/" in name and not name.startswith((".", "/", "~")),
            priority=10,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="modelscope",
            display_name="ModelScope",
            aliases=("ms",),
            description="ModelScope snapshot download followed by Transformers loading.",
            dependencies=("modelscope>=1.15", "torch>=2", "transformers>=5.8"),
            model_name_patterns=("namespace/model-name",),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer decoder layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=False,
                supports_remote_download=True,
                cache_policy="SafeLens cache_dir -> .cache/safelens/models/modelscope",
                notes=(
                    "Use modelscope_kwargs for provider-specific snapshot filters.",
                    "Component hooks use SafeLens architecture adapters when the "
                    "loaded Transformers architecture is recognized.",
                    "Attention result hooks are implemented by deriving per-head "
                    "z @ W_O results and writing patched head-result deltas back "
                    "to the merged attention output.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_modelscope_wrapper,
            inspect=_inspect_modelscope_model,
            matches_model_name=lambda _name: False,
            priority=5,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="local",
            display_name="Local Transformers Directory",
            aliases=(),
            description="Local Transformers-compatible model directory.",
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=("./models/local-causal-lm", "/abs/path/to/model"),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer decoder layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=True,
                supports_remote_download=False,
                cache_policy="No provider download; local_dir or name is used directly.",
                notes=(
                    "Keep local model paths and weights out of git.",
                    "Component hooks use SafeLens architecture adapters when the "
                    "loaded Transformers architecture is recognized.",
                    "Attention result hooks are implemented by deriving per-head "
                    "z @ W_O results and writing patched head-result deltas back "
                    "to the merged attention output.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_local_wrapper,
            inspect=_inspect_local_model,
            matches_model_name=lambda name: name.startswith((".", "/", "~")),
            priority=50,
        )
    )
    _MODEL_ADAPTERS_REGISTERED = True


def _build_dummy_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    return DummyModelWrapper(name=config.name)


def _build_huggingface_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return HuggingFaceModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
    )


def _build_local_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return LocalModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=None,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
        pretrained_path_is_local=plan.provider == "local",
    )


def _build_qwen3_dense_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return Qwen3DenseModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
    )


def _build_transformer_lens_compatible_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    load_kwargs, process_kwargs = _split_transformer_lens_load_kwargs(config.load_kwargs)
    return TransformerLensCompatibleModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
        pretrained_path_is_local=plan.provider == "local",
        process_weights_kwargs=process_kwargs,
    )


def _build_modelscope_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return ModelScopeModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        local_dir=config.local_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        modelscope_kwargs=config.modelscope_kwargs,
    )


def _inspect_dummy_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    return _inspection_payload(model_name, config, supported=True, model_family="dummy")


def _inspect_huggingface_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    return _inspection_payload(
        model_name,
        config,
        supported=True,
        model_family="generic_transformers",
        warnings=("Only module-level hooks are known statically for generic HF models.",),
    )


def _inspect_modelscope_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    return _inspection_payload(
        model_name,
        config,
        supported=True,
        model_family="modelscope_transformers",
        warnings=("ModelScope support downloads a snapshot before Transformers loading.",),
    )


def _inspect_local_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    local_path = config.local_dir if config is not None and config.local_dir else model_name
    return _inspection_payload(
        model_name,
        config,
        supported=True,
        model_family="local_transformers",
        local_path=local_path,
        warnings=("Static inspection does not verify that the local path exists.",),
    )


def _inspect_qwen3_dense_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    errors: list[str] = []
    try:
        validate_qwen3_dense_model_name(model_name)
    except ValueError as exc:
        errors.append(str(exc))
    size_b = qwen3_dense_size_billion(model_name)
    payload = _inspection_payload(
        model_name,
        config,
        supported=not errors,
        model_family="qwen3_dense",
        parameter_size_b=size_b,
        supported_dense_limit_b=_QWEN3_DENSE_MAX_PARAMS_B,
        supported_hook_examples=qwen3_hook_name_examples(),
        warnings=(
            "Attention pattern and score hooks use eager softmax instrumentation; "
            "flash or SDPA attention paths may need an eager attention implementation.",
        ),
    )
    if errors:
        payload["errors"] = errors
    return payload


def _inspect_transformer_lens_compatible_model(
    model_name: str,
    config: ModelLoadConfig | None,
) -> dict[str, Any]:
    effective_config = config or ModelLoadConfig(source="transformer_lens", name=model_name)
    download_plan = resolve_model_download_plan(effective_config)
    local_target = download_plan.provider == "local"
    compatible_supported = local_target or is_transformer_lens_supported_model_name(model_name)
    official_supported = local_target or is_transformer_lens_official_model_name(model_name)
    resolved_model = (
        download_plan.pretrained_path
        if local_target
        else resolve_transformer_lens_compatible_model_name(model_name)
    )
    native_checkpoint = not local_target and (
        is_transformer_lens_native_checkpoint(model_name)
        or (resolved_model != model_name and is_transformer_lens_native_checkpoint(resolved_model))
    )
    supported = compatible_supported and not native_checkpoint
    warnings = [
        "SafeLens does not import TransformerLens for this adapter.",
        "Static inspection uses SafeLens' vendored TransformerLens support table; "
        "loading uses Transformers auto classes and may require a valid HF ID or local path.",
        "Component hooks use SafeLens architecture adapters. Attention pattern and score "
        "hooks use eager softmax instrumentation; flash or SDPA attention paths may need "
        "an eager attention implementation.",
    ]
    if native_checkpoint:
        warnings.append(
            "This name resolves to a TransformerLens-native HookedTransformer checkpoint "
            "repo with .pth weights, not a HuggingFace Transformers model directory."
        )
    if local_target:
        warnings.append("Static inspection does not verify that the local path exists.")
    architecture_adapter = (
        None if native_checkpoint else architecture_adapter_for_name(model_name=resolved_model)
    )
    bridge_components = (
        supported_transformer_component_names(include_attention=True)
        if architecture_adapter is None
        else architecture_adapter.supported_components(include_unsupported=False)
    )
    payload = _inspection_payload(
        model_name,
        effective_config,
        supported=supported,
        model_family=(
            "transformer_lens_native_checkpoint"
            if native_checkpoint
            else f"transformer_lens_compatible_{transformer_lens_model_kind(resolved_model)}"
        ),
        resolved_pretrained_model=resolved_model,
        official_transformer_lens_supported=official_supported,
        safelens_transformer_lens_compatible=compatible_supported,
        checkpoint_format=(
            "transformer_lens_hooked_transformer"
            if native_checkpoint
            else "huggingface_transformers"
        ),
        transformers_loadable=supported,
        local_path=download_plan.local_dir if local_target else None,
        official_model_count=len(transformer_lens_official_model_names()),
        supported_model_examples=transformer_lens_official_model_names()[:20],
        architecture_bridge_adapter=(
            architecture_adapter.name if architecture_adapter is not None else None
        ),
        architecture_bridge_adapters=[item["name"] for item in list_architecture_adapters()],
        bridge_components=list(bridge_components),
        target_hook_examples=_TRANSFORMER_LENS_HOOK_COMPONENTS,
        warnings=tuple(warnings),
    )
    if native_checkpoint:
        payload["errors"] = [
            "SafeLens' dependency-free transformer_lens source loads only "
            "Transformers-compatible checkpoints. Convert this HookedTransformer "
            "checkpoint or choose a Transformers model id/local directory."
        ]
    elif not compatible_supported:
        payload["errors"] = [
            "Model name is not in the vendored TransformerLens support table. "
            "Use source=huggingface or source=local if this is a plain Transformers model."
        ]
    return payload


def _inspection_payload(
    model_name: str,
    config: ModelLoadConfig | None,
    *,
    supported: bool,
    model_family: str,
    warnings: tuple[str, ...] = (),
    **extra: Any,
) -> dict[str, Any]:
    effective_config = config or ModelLoadConfig(source="huggingface", name=model_name)
    return {
        "model": model_name,
        "source": effective_config.source,
        "supported": supported,
        "model_family": model_family,
        "download_plan": resolve_model_download_plan(effective_config).to_dict(),
        "warnings": list(warnings),
        **extra,
    }


register_builtin_model_adapters()
