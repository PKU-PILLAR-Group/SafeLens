"""Model wrapper implementations and hook helpers."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from inspect import Parameter, signature
from numbers import Integral
from typing import Any

from SafeLens.core.base import (
    Batch,
    HookFn,
    LayerRef,
    ModelLoadConfig,
    ModelWrapper,
)
from SafeLens.core.hooks import (
    ActivationCache,
    NamesFilter,
    activation_name_for_layer,
    make_cache_hook,
    matches_names_filter,
)
from SafeLens.utils.model_bridge import (
    ComponentHookContext,
    ComponentRef,
    architecture_adapter_for_model,
    list_architecture_adapters,
    supported_transformer_component_names,
    transformer_lens_component_name,
)
from SafeLens.utils.model_registry import (
    ModelAdapterCapabilities,
    ModelAdapterSpec,
    get_model_adapter_registry,
    resolve_model_download_plan,
)
from SafeLens.utils.transformer_lens_support import (
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
_QWEN3_CACHE_ONLY_COMPONENTS: set[str] = set()
_QWEN3_ATTENTION_COMPONENTS = {"pattern", "attn_scores"}
_QWEN3_COMPONENT_EXAMPLES = (
    "layer_0.resid_pre",
    "layer_0.resid_mid",
    "layer_0.resid_post",
    "layer_0.attn_out",
    "layer_0.mlp_out",
    "layer_0.q",
    "layer_0.k",
    "layer_0.v",
    "layer_0.z",
    "layer_0.result",
    "layer_0.pattern",
    "layer_0.attn_scores",
    "blocks.0.hook_resid_pre",
    "blocks.0.attn.hook_q",
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
    "blocks.N.attn.hook_q",
    "blocks.N.attn.hook_k",
    "blocks.N.attn.hook_v",
    "blocks.N.attn.hook_z",
    "blocks.N.attn.hook_pattern",
    "blocks.N.attn.hook_attn_scores",
    "blocks.N.attn.hook_result",
    "blocks.N.hook_attn_out",
    "blocks.N.mlp.hook_pre",
    "blocks.N.mlp.hook_post",
    "blocks.N.hook_mlp_out",
    "ln_final.hook_scale",
)
_TRANSFORMER_LENS_PATCH_COMPONENTS = (
    "resid_pre",
    "resid_mid",
    "resid_post",
    "attn_out",
    "mlp_out",
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
_DEFAULT_CACHE_EXCLUDED_COMPONENTS = {"attn_scores"}


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
    device: str | None = None
    dtype: str | None = None
    original_architecture: str | None = None

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


class _ManagedWrapperHookHandle:
    def __init__(
        self,
        handle: Any,
        remove_callback: Callable[[], None],
        *,
        is_permanent: bool = False,
        level: int | None = None,
    ) -> None:
        self._handle = handle
        self._remove_callback = remove_callback
        self.is_permanent = is_permanent
        self.level = level
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
        cache = {
            name: {"batch": dict(batch)} for name in selected_layers
        }
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

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        _ = generation_kwargs
        return f"{prompt} [dummy generation]"

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
    try:
        hook_signature = signature(hook_fn)
    except (TypeError, ValueError):
        return hook_fn(**hook_kwargs)

    parameters = hook_signature.parameters.values()
    if any(param.kind == Parameter.VAR_KEYWORD for param in parameters):
        return hook_fn(**hook_kwargs)

    parameters = hook_signature.parameters.values()
    accepted_names = {
        param.name
        for param in parameters
        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    required_names = {
        param.name
        for param in hook_signature.parameters.values()
        if param.default is Parameter.empty
        and param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    filtered_kwargs = {name: value for name, value in hook_kwargs.items() if name in accepted_names}
    if required_names.issubset(filtered_kwargs):
        return hook_fn(**filtered_kwargs)

    try:
        return hook_fn(activation, None)
    except TypeError:
        return hook_fn(None, None, activation)


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
        self.model: Any = None
        self.tokenizer: Any = None
        self._tokenizer_load_error: Exception | None = None
        self._hooks: list[Any] = []
        self._attention_hook_count = 0
        self._run_requires_output_attentions = False

    @property
    def cfg(self) -> TransformerLensConfigView:
        """Return a TransformerLens-style normalized config view."""
        return _make_transformer_lens_config_view(
            self._require_model(),
            model_name=self.name,
            device=self.device,
            dtype=self.dtype,
            tokenizer=self.tokenizer,
        )

    @property
    def W_U(self) -> Any:
        """Return an unembedding matrix shaped `[d_model, vocab]` when available."""
        weight = self._output_embedding_weight()
        if hasattr(weight, "T") and getattr(weight, "ndim", 0) == 2:
            return weight.T
        return weight

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
    def W_in(self) -> Any:
        """Return MLP input weights shaped `[layer, d_model, d_mlp]`."""
        return self._stack_mlp_weights("in")

    @property
    def W_out(self) -> Any:
        """Return MLP output weights shaped `[layer, d_mlp, d_model]`."""
        return self._stack_mlp_weights("out")

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

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        return self._add_managed_hook(layer, hook_fn)

    def add_perma_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        """Register a TransformerLens-style permanent hook."""
        return self._add_managed_hook(layer, hook_fn, is_permanent=True)

    def _add_managed_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        is_permanent: bool = False,
        level: int | None = None,
    ) -> _ManagedWrapperHookHandle:
        handle = self._register_hook(layer, hook_fn)
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
        *,
        return_type: str | None = "logits",
        **kwargs: Any,
    ) -> Any:
        """Run the wrapped model directly, returning logits by default like TransformerLens."""
        if kwargs:
            model_input = _merge_extra_model_kwargs(batch, kwargs)
        else:
            model_input = batch
        return self._run_model_forward(model_input, return_type=return_type)

    def _register_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        model = self._require_model()
        component_handle = self._try_register_component_hook(model, layer, hook_fn)
        if component_handle is not None:
            return component_handle
        module = self._resolve_layer(model, layer)
        return module.register_forward_hook(
            lambda mod, inputs, output: hook_fn(mod, inputs, output)
        )

    def run_with_cache(
        self,
        batch: Any,
        layers: Sequence[LayerRef] | None = None,
        *,
        names_filter: NamesFilter = None,
        return_cache_object: bool | object = _DEFAULT_RETURN_CACHE_OBJECT,
        remove_batch_dim: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        cache_all: bool | object = _DEFAULT_CACHE_ALL,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
    ) -> tuple[Any, dict[str, Any] | ActivationCache]:
        model = self._require_model()
        cache = ActivationCache(model=self, has_batch_dim=not remove_batch_dim)
        temp_handles: list[Any] = []
        resolved_return_type = _resolve_return_type(batch, return_type)
        resolved_cache_all = _resolve_cache_all(batch, layers, names_filter, cache_all)
        resolved_return_cache_object = _resolve_return_cache_object(batch, return_cache_object)

        try:
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

            model_inputs = self._prepare_model_inputs(batch)
            with _no_grad_context():
                raw_output = model(**model_inputs)
                output = _format_model_output(raw_output, resolved_return_type)
        finally:
            self._run_requires_output_attentions = False
            for handle in reversed(temp_handles):
                handle.remove()

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
        cache: ActivationCache | None = None,
    ) -> ActivationCache:
        """Install persistent forward cache hooks and return the live cache."""
        if incl_bwd:
            raise NotImplementedError(
                "Backward caching hooks for Transformers-backed wrappers are not yet implemented."
            )
        model = self._require_model()
        activation_cache = (
            cache
            if cache is not None
            else ActivationCache(model=self, has_batch_dim=not remove_batch_dim)
        )
        activation_cache.model = self
        if remove_batch_dim:
            activation_cache.has_batch_dim = False
        resolved_cache_all = True if cache_all is _DEFAULT_CACHE_ALL else bool(cache_all)
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
            managed_handle = self._track_hook_handle(handle, is_permanent=True)
            self._hooks.append(managed_handle)
        return activation_cache

    def cache_all(
        self,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | None = None,
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
        names_filter: NamesFilter,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | None = None,
    ) -> ActivationCache:
        """Permanently cache hook names matching a names filter until hooks are reset."""
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
        *,
        fwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        bwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
    ) -> Any:
        """Run one forward pass with temporary hooks, mirroring TransformerLens."""
        if list(bwd_hooks):
            raise NotImplementedError(
                "Backward hooks for Transformers-backed wrappers require a scalar-loss "
                "forward API and are not yet implemented."
            )
        handles: list[Any] = []
        try:
            for layer, hook_fn in self._expand_hook_specs(fwd_hooks):
                handles.append(self._add_managed_hook(layer, hook_fn))
            return self._run_model_forward(batch, return_type=return_type)
        finally:
            if reset_hooks_end:
                for handle in reversed(handles):
                    remove = getattr(handle, "remove", None)
                    if callable(remove):
                        remove()
                if clear_contexts:
                    self.clear_contexts()

    @contextmanager
    def hooks(
        self,
        *,
        fwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        bwd_hooks: Iterable[tuple[LayerRef | Callable[[str], bool], HookFn]] = (),
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
    ) -> Any:
        """Temporarily register hooks around arbitrary wrapper calls."""
        if list(bwd_hooks):
            raise NotImplementedError(
                "Backward hooks for Transformers-backed wrappers require a scalar-loss "
                "forward API and are not yet implemented."
            )
        handles: list[Any] = []
        try:
            for layer, hook_fn in self._expand_hook_specs(fwd_hooks):
                handles.append(self._add_managed_hook(layer, hook_fn))
            yield self
        finally:
            if reset_hooks_end:
                for handle in reversed(handles):
                    remove = getattr(handle, "remove", None)
                    if callable(remove):
                        remove()
                if clear_contexts:
                    self.clear_contexts()

    def _run_model_forward(
        self,
        batch: Any,
        *,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
    ) -> Any:
        """Run the wrapped model without adding temporary cache hooks."""
        model = self._require_model()
        resolved_return_type = _resolve_return_type(batch, return_type)
        try:
            model_inputs = self._prepare_model_inputs(batch)
            with _no_grad_context():
                raw_output = model(**model_inputs)
                return _format_model_output(raw_output, resolved_return_type)
        finally:
            self._run_requires_output_attentions = False

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        model = self._require_model()
        if self.tokenizer is None:
            detail = _tokenizer_error_detail(self._tokenizer_load_error)
            raise RuntimeError(
                "Tokenizer is not loaded, so text generation is unavailable. " f"{detail}"
            )

        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt")
        if self.device is not None:
            inputs = inputs.to(self.device)
        with torch.no_grad():
            output_ids = model.generate(**inputs, **generation_kwargs)
        return str(self.tokenizer.decode(output_ids[0], skip_special_tokens=True))

    def to_tokens(self, text: str | Sequence[str], *, prepend_bos: bool = True) -> Any:
        """Tokenize text into a tensor, mirroring TransformerLens' convenience method."""
        tokenizer = self._require_tokenizer_for_text("tokenization")
        tokenized = tokenizer(
            text,
            return_tensors="pt",
            add_special_tokens=False,
            padding=not isinstance(text, str),
        )
        tokens = tokenized["input_ids"] if isinstance(tokenized, dict) else tokenized.input_ids
        if prepend_bos:
            tokens = _prepend_bos_token(tokens, tokenizer)
        if self.device is not None:
            tokens = tokens.to(self.device)
        return tokens

    def to_string(self, tokens: Any, *, skip_special_tokens: bool = False) -> str | list[str]:
        """Decode token ids into text."""
        tokenizer = self._require_tokenizer_for_text("decoding")
        shape = _shape_of_token_ids(tokens)
        if shape is not None and len(shape) > 2:
            raise ValueError(f"Invalid token shape for decoding: {shape!r}.")
        if shape is not None and len(shape) == 2:
            batch_decode = getattr(tokenizer, "batch_decode", None)
            if callable(batch_decode):
                return list(batch_decode(tokens, skip_special_tokens=skip_special_tokens))
            return [
                str(tokenizer.decode(row, skip_special_tokens=skip_special_tokens))
                for row in tokens
            ]
        if isinstance(tokens, int):
            tokens = [tokens]
        return str(tokenizer.decode(tokens, skip_special_tokens=skip_special_tokens))

    def to_str_tokens(
        self,
        text_or_tokens: str | Any,
        *,
        prepend_bos: bool = True,
    ) -> list[str] | list[list[str]]:
        """Return per-token strings for text or token ids."""
        tokenizer = self._require_tokenizer_for_text("token string conversion")
        if isinstance(text_or_tokens, list) and text_or_tokens and isinstance(
            text_or_tokens[0],
            list | str,
        ):
            return [
                self.to_str_tokens(item, prepend_bos=prepend_bos)
                for item in text_or_tokens
            ]
        tokens = self.to_tokens(text_or_tokens, prepend_bos=prepend_bos) if isinstance(
            text_or_tokens, str
        ) else text_or_tokens
        shape = getattr(tokens, "shape", None)
        if shape is not None:
            shape_tuple = tuple(int(dim) for dim in shape)
            if len(shape_tuple) == 2 and shape_tuple[0] == 1:
                tokens = tokens[0]
            elif len(shape_tuple) > 1:
                raise ValueError(f"Invalid token shape for token string conversion: {shape_tuple!r}.")
        convert = getattr(tokenizer, "convert_ids_to_tokens", None)
        if callable(convert):
            converted = convert(tokens)
            if isinstance(converted, str):
                return [converted]
            return [str(token) for token in converted]
        token_list = tokens.tolist() if hasattr(tokens, "tolist") else list(tokens)
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
        prepend_bos: bool = True,
    ) -> int:
        """Return the first or last position of one token in a prompt or token sequence."""
        tokens = (
            self.to_tokens(text_or_tokens, prepend_bos=prepend_bos)
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
        _ = direction, dir
        for handle in reversed(list(self._hooks)):
            if handle.is_permanent and not including_permanent:
                continue
            if level is not None and handle.level != level:
                continue
            handle.remove()
        if clear_contexts:
            self.clear_contexts()

    def clear_contexts(self) -> None:
        """Clear mutable context dictionaries on component hook objects."""
        for handle in list(self._hooks):
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
        model = self._require_model()
        get_output_embeddings = getattr(model, "get_output_embeddings", None)
        embeddings = get_output_embeddings() if callable(get_output_embeddings) else None
        weight = getattr(embeddings, "weight", None)
        if weight is None:
            weight = getattr(model, "W_U", None)
            if weight is not None and hasattr(weight, "T") and getattr(weight, "ndim", 0) == 2:
                return weight.T
        if weight is None:
            raise RuntimeError(
                "Could not find output embedding weights for residual direction lookup."
            )
        return weight

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

    def _stack_mlp_weights(self, component: str) -> Any:
        model = self._require_model()
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        n_layers = _infer_model_layers(model)
        if n_layers <= 0:
            raise RuntimeError(f"Could not infer layer count for W_{component}.")
        weights = [adapter.get_mlp_weight(model, component, layer) for layer in range(n_layers)]
        return _stack_tensor_like(weights)

    def _prepare_model_inputs(self, batch: Any) -> dict[str, Any]:
        batch = _normalize_model_batch(batch)
        if "input_ids" in batch:
            model_inputs = dict(batch)
            model_inputs["input_ids"] = _ensure_token_batch_dim(model_inputs["input_ids"])
            return self._with_attention_flags(model_inputs)
        for token_key in ("tokens", "token_ids"):
            if token_key in batch:
                model_inputs = {
                    key: value
                    for key, value in batch.items()
                    if key not in {"tokens", "token_ids"}
                }
                model_inputs["input_ids"] = _ensure_token_batch_dim(batch[token_key])
                return self._with_attention_flags(model_inputs)
        if self.tokenizer is not None and "input_ids" not in batch:
            text = batch.get("text") or batch.get("prompt")
            if text is not None:
                tokenized = _tokenize_text_batch(self.tokenizer, text)
                if self.device is not None:
                    tokenized = tokenized.to(self.device)
                return self._with_attention_flags(dict(tokenized))
        if self.tokenizer is None and "input_ids" not in batch:
            text = batch.get("text") or batch.get("prompt")
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
    ) -> Any | None:
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        if adapter.parse_component_ref(layer) is None:
            return None
        requires_output_attentions = adapter.requires_output_attentions(layer)
        handle = adapter.register_component_hook(model, layer, hook_fn)
        if requires_output_attentions:
            self._attention_hook_count += 1
            return _TrackedAttentionHandle(handle, self._release_attention_hook)
        return handle

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
        if adapter.parse_component_ref(layer) is None:
            return None
        requires_output_attentions = adapter.requires_output_attentions(layer)
        if requires_output_attentions:
            if is_permanent:
                self._attention_hook_count += 1
            else:
                self._run_requires_output_attentions = True
        cache_name = activation_name_for_layer(layer) if isinstance(layer, int) else str(layer)

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
        if requires_output_attentions and is_permanent:
            return _TrackedAttentionHandle(handle, self._release_attention_hook)
        return handle

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
        return module.register_forward_hook(
            make_cache_hook(
                cache,
                cache_name,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
            )
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
                if not matched:
                    raise KeyError(f"No hook names matched filter {layer_or_filter!r}.")
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
        if layers is not None:
            selected = list(layers)
        elif names_filter is not None:
            selected = _filter_hook_names(
                _candidate_hook_names(model, adapter, for_cache=True),
                names_filter,
                adapter=adapter,
            )
            if not selected:
                raise KeyError(f"No hook names matched names_filter {names_filter!r}.")
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

        for path in ("model.layers", "transformer.h", "gpt_neox.layers"):
            target = model
            try:
                for part in path.split("."):
                    target = getattr(target, part)
                return target[layer]
            except (AttributeError, IndexError, TypeError):
                continue
        raise KeyError(
            f"Could not resolve layer index {layer} for model {type(model).__name__}. "
            "Known decoder-layer paths tried: model.layers, transformer.h, gpt_neox.layers."
        )


class TransformerLensCompatibleModelWrapper(HuggingFaceModelWrapper):
    """Independent Transformers wrapper for TransformerLens-compatible model IDs.

    The compatibility table mirrors TransformerLens' public support matrix, but
    this class never imports or delegates to TransformerLens. Decoder,
    encoder-decoder, encoder, and audio-encoder families are loaded through the
    closest Transformers auto class.
    """

    def load_model(self) -> Any:
        if not self._is_supported_transformer_lens_target():
            raise ValueError(
                f"Model {self.name!r} is not in SafeLens' vendored TransformerLens-compatible "
                "support table. Use source='huggingface' for generic Transformers loading, "
                "or source='local' for a local model directory."
            )
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
        pretrained_path = self._resolve_pretrained_path()
        pretrained_kwargs = self._pretrained_kwargs()
        kind = transformer_lens_model_kind(self.name)

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
        return self.model

    def _resolve_pretrained_path(self) -> str:
        raw_path = self.pretrained_path or self.name
        return resolve_transformer_lens_compatible_model_name(raw_path)

    def _is_supported_transformer_lens_target(self) -> bool:
        if _wrapper_looks_like_local_path(self.name):
            return True
        if self.pretrained_path is not None and _wrapper_looks_like_local_path(
            self.pretrained_path
        ):
            return True
        return is_transformer_lens_supported_model_name(self.name)

    def _prepare_model_inputs(self, batch: Any) -> dict[str, Any]:
        batch = _normalize_model_batch(batch)
        kind = transformer_lens_model_kind(self.name)
        model_kwargs = dict(batch.get("model_kwargs", {}))
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
                    getattr(config, "decoder_start_token_id", None),
                )
                if decoder_start_token_id is None:
                    decoder_start_token_id = getattr(config, "pad_token_id", None)
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

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        kind = transformer_lens_model_kind(self.name)
        if kind in {"encoder", "audio_encoder"}:
            raise NotImplementedError(
                f"{kind} models do not expose autoregressive text generation through "
                "the independent SafeLens Transformers wrapper."
            )
        return super().generate(prompt, **generation_kwargs)

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

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        return self._add_managed_hook(layer, hook_fn)

    def _register_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        component_ref = parse_qwen3_component_ref(layer)
        if component_ref is None:
            return super()._register_hook(layer, hook_fn)
        layer_index, component = component_ref
        return self._register_qwen3_component_hook(layer_index, component, hook_fn)

    def run_with_cache(
        self,
        batch: Any,
        layers: Sequence[LayerRef] | None = None,
        *,
        names_filter: NamesFilter = None,
        return_cache_object: bool | object = _DEFAULT_RETURN_CACHE_OBJECT,
        remove_batch_dim: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        cache_all: bool | object = _DEFAULT_CACHE_ALL,
        return_type: str | None | object = _DEFAULT_RETURN_TYPE,
    ) -> tuple[Any, dict[str, Any] | ActivationCache]:
        model = self._require_model()
        cache = ActivationCache(model=self, has_batch_dim=not remove_batch_dim)
        temp_handles: list[Any] = []
        resolved_return_type = _resolve_return_type(batch, return_type)
        resolved_cache_all = _resolve_cache_all(batch, layers, names_filter, cache_all)
        resolved_return_cache_object = _resolve_return_cache_object(batch, return_cache_object)

        try:
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

            model_inputs = self._prepare_model_inputs(batch)
            with _no_grad_context():
                raw_output = model(**model_inputs)
                output = _format_model_output(raw_output, resolved_return_type)
        finally:
            self._run_requires_output_attentions = False
            for handle in reversed(temp_handles):
                handle.remove()

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
                if not matched:
                    raise KeyError(f"No hook names matched filter {layer_or_filter!r}.")
                expanded.extend((name, hook_fn) for name in matched)
            else:
                expanded.append((layer_or_filter, hook_fn))
        return expanded

    def _register_qwen3_component_hook(
        self,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
    ) -> Any:
        if component in _QWEN3_ATTENTION_COMPONENTS or component == "result":
            handle = self._try_register_component_hook(
                self._require_model(),
                f"layer_{layer_index}.{component}",
                hook_fn,
            )
            if handle is None:
                raise KeyError(f"Could not resolve Qwen3 attention component {component!r}.")
            return handle
        if component not in _QWEN3_PATCHABLE_COMPONENTS:
            supported = ", ".join(qwen3_supported_hook_components(include_attention=True))
            examples = ", ".join(_QWEN3_COMPONENT_EXAMPLES[:4])
            raise KeyError(
                f"Unsupported Qwen3 dense component {component!r}. "
                f"Supported components: {supported}. Example hook names: {examples}."
            )

        qwen_layer = self._qwen3_layer(layer_index)
        if component == "resid_pre":
            return self._register_input_hook(qwen_layer, layer_index, component, hook_fn)
        if component == "resid_mid":
            return self._register_input_hook(
                qwen_layer.post_attention_layernorm,
                layer_index,
                component,
                hook_fn,
            )
        if component == "resid_post":
            return self._register_first_output_hook(qwen_layer, layer_index, component, hook_fn)
        if component == "attn_out":
            return self._register_first_output_hook(
                qwen_layer.self_attn,
                layer_index,
                component,
                hook_fn,
            )
        if component == "mlp_out":
            return self._register_tensor_output_hook(
                qwen_layer.mlp,
                layer_index,
                component,
                hook_fn,
            )
        if component in {"q", "k", "v"}:
            projection = getattr(qwen_layer.self_attn, f"{component}_proj")
            return self._register_head_projection_hook(
                projection,
                layer_index,
                component,
                hook_fn,
            )
        return self._register_z_hook(qwen_layer.self_attn.o_proj, layer_index, hook_fn)

    def _register_input_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
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

        return module.register_forward_pre_hook(pre_hook)

    def _register_first_output_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
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

        return module.register_forward_hook(forward_hook)

    def _register_tensor_output_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
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

        return module.register_forward_hook(forward_hook)

    def _register_head_projection_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
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

        return module.register_forward_hook(forward_hook)

    def _register_z_hook(self, module: Any, layer_index: int, hook_fn: HookFn) -> Any:
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

        return module.register_forward_pre_hook(pre_hook)

    def _qwen3_layer(self, layer_index: int) -> Any:
        layers = _get_qwen3_layers(self._require_model())
        try:
            return layers[layer_index]
        except IndexError as exc:
            raise KeyError(f"Unknown Qwen3 dense layer index {layer_index}.") from exc

    def _heads_for_component(self, component: str) -> int:
        config = getattr(self._require_model(), "config", None)
        if component in {"k", "v"}:
            n_key_value_heads = getattr(config, "num_key_value_heads", None)
            if n_key_value_heads is not None:
                return int(n_key_value_heads)
        n_heads = getattr(config, "num_attention_heads", None)
        if n_heads is None:
            raise ValueError("Qwen3 config does not expose num_attention_heads.")
        return int(n_heads)

    @staticmethod
    def _validate_loaded_qwen3_dense_model(model: Any) -> None:
        config = getattr(model, "config", None)
        model_type = str(getattr(config, "model_type", "")).lower()
        if model_type not in {"qwen3", ""}:
            raise ValueError(f"Expected a Qwen3 dense model, got model_type={model_type!r}.")
        if getattr(config, "num_experts", None) is not None:
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
    components = sorted(_QWEN3_PATCHABLE_COMPONENTS)
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
    if component not in _QWEN3_PATCHABLE_COMPONENTS:
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
    if layer_type == "mlp" and component in {"post", "hook_post"}:
        return "mlp_out"
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
    try:
        hook_signature = signature(hook_fn)
    except (TypeError, ValueError):
        return hook_fn(**hook_kwargs)

    parameters = hook_signature.parameters.values()
    if any(param.kind == Parameter.VAR_KEYWORD for param in parameters):
        return hook_fn(**hook_kwargs)

    parameters = hook_signature.parameters.values()
    accepted_names = {
        param.name
        for param in parameters
        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    required_names = {
        param.name
        for param in hook_signature.parameters.values()
        if param.default is Parameter.empty
        and param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    filtered_kwargs = {name: value for name, value in hook_kwargs.items() if name in accepted_names}
    if required_names.issubset(filtered_kwargs):
        return hook_fn(**filtered_kwargs)

    try:
        return hook_fn(activation, hook_context)
    except TypeError:
        return hook_fn(None, None, activation)


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


def _no_grad_context() -> Any:
    try:
        import torch

        return torch.no_grad()
    except ImportError:
        return nullcontext()


def _tokenizer_error_detail(error: Exception | None) -> str:
    if error is None:
        return "Call load_model() first or configure tokenizer files for the model."
    return f"Tokenizer load error: {type(error).__name__}: {error}"


def _prepend_bos_token(tokens: Any, tokenizer: Any) -> Any:
    bos_token_id = getattr(tokenizer, "bos_token_id", None)
    if bos_token_id is None:
        return tokens
    try:
        import torch

        if hasattr(tokens, "shape"):
            bos = torch.full(
                (tokens.shape[0], 1),
                int(bos_token_id),
                dtype=tokens.dtype,
                device=tokens.device,
            )
            return torch.cat([bos, tokens], dim=1)
    except ImportError:
        pass
    if isinstance(tokens, list):
        if tokens and isinstance(tokens[0], list):
            return [[bos_token_id, *row] for row in tokens]
        return [bos_token_id, *tokens]
    return tokens


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
    if _looks_like_token_ids(batch):
        return {"input_ids": _ensure_token_batch_dim(batch)}
    raise TypeError(
        "Model inputs must be a mapping, text string, or token ids shaped [pos] or [batch, pos]."
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
        row = values[0] if isinstance(values, list) else values
        return [int(token) for token in list(row)]
    raise ValueError(f"Expected a rank-1 token sequence or [1, pos], got shape {shape!r}.")


def _candidate_hook_names(model: Any, adapter: Any, *, for_cache: bool | None = None) -> list[str]:
    names: list[str] = []
    n_layers = _infer_model_layers(model)
    for layer in range(n_layers):
        for component in adapter.supported_components(for_cache=for_cache):
            names.append(transformer_lens_component_name(component, layer))
            names.append(f"layer_{layer}.{component}")
    named_modules = getattr(model, "named_modules", None)
    if callable(named_modules):
        names.extend(name for name, _module in named_modules())
    return list(dict.fromkeys(names))


def _default_cache_hook_names(model: Any, adapter: Any) -> list[str]:
    """Return TL-style component hook names for default full-cache runs."""
    names: list[str] = []
    n_layers = _infer_model_layers(model)
    for layer in range(n_layers):
        for component in adapter.supported_components(for_cache=True):
            if component in _DEFAULT_CACHE_EXCLUDED_COMPONENTS:
                continue
            names.append(transformer_lens_component_name(component, layer))
    return names


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


def _merge_extra_model_kwargs(batch: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_model_batch(batch)
    model_kwargs = dict(normalized.get("model_kwargs", {}))
    model_kwargs.update(kwargs)
    normalized["model_kwargs"] = model_kwargs
    return normalized


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
    aliases = {
        "logit": "logits",
        "logits": "logits",
        "loss": "loss",
        "model_output": "model_output",
        "raw": "model_output",
        "output": "model_output",
    }
    if normalized not in aliases:
        raise ValueError(
            "return_type must be one of 'logits', 'loss', 'model_output', 'raw', or None."
        )
    return aliases[normalized]


def _format_model_output(output: Any, return_type: str | None) -> Any:
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
        loss = _extract_output_field(output, "loss")
        if loss is None:
            raise RuntimeError("Model output does not expose loss.")
        return loss
    raise ValueError(f"Unsupported return_type {return_type!r}.")


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
    if isinstance(value, (str, bytes, Mapping, tuple, list)):
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
    return isinstance(value, (int, float, complex, bool))


def _make_transformer_lens_config_view(
    model: Any,
    *,
    model_name: str,
    device: str | None,
    dtype: str | None,
    tokenizer: Any | None,
) -> TransformerLensConfigView:
    config = getattr(model, "config", None)
    n_layers = _none_if_zero(_infer_model_layers(model))
    n_heads = _first_int_attr(config, model, names=("num_attention_heads", "n_head", "n_heads", "num_heads"))
    n_key_value_heads = _first_int_attr(config, model, names=("num_key_value_heads", "num_kv_heads", "n_head_kv"))
    d_model = _first_int_attr(config, model, names=("hidden_size", "n_embd", "d_model", "dim"))
    d_head = _first_int_attr(config, model, names=("head_dim", "d_head", "kv_channels"))
    if d_head is None and d_model is not None and n_heads:
        d_head = d_model // n_heads
    d_vocab = _first_int_attr(config, model, names=("vocab_size", "d_vocab"))
    if d_vocab is None:
        d_vocab = _vocab_size_from_tokenizer(tokenizer)
    n_ctx = _first_int_attr(
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
        config,
        model,
        names=("intermediate_size", "n_inner", "d_ff", "ffn_dim", "d_mlp"),
    )
    act_fn = _first_str_attr(
        config,
        model,
        names=("hidden_act", "activation_function", "activation", "act_fn"),
    )
    return TransformerLensConfigView(
        model_name=model_name,
        model_type=getattr(config, "model_type", None),
        n_layers=n_layers,
        n_heads=n_heads,
        n_key_value_heads=n_key_value_heads,
        d_model=d_model,
        d_head=d_head,
        d_vocab=d_vocab,
        n_ctx=n_ctx,
        d_mlp=d_mlp,
        act_fn=act_fn,
        normalization_type=_infer_normalization_type(model, config),
        device=device,
        dtype=dtype,
        original_architecture=type(model).__name__,
    )


def _infer_model_layers(model: Any) -> int:
    config = getattr(model, "config", None)
    for owner in (model, config):
        if owner is None:
            continue
        for name in ("num_hidden_layers", "n_layer", "n_layers", "num_layers"):
            value = getattr(owner, name, None)
            if value is not None:
                return int(value)
    for path in (
        "model.layers",
        "transformer.h",
        "gpt_neox.layers",
        "model.decoder.layers",
        "encoder.layer",
        "transformer.layer",
        "encoder.layers",
        "encoder.block",
    ):
        try:
            target = model
            for part in path.split("."):
                target = getattr(target, part)
            return len(target)
        except (AttributeError, TypeError):
            continue
    return 0


def _none_if_zero(value: int) -> int | None:
    return value if value > 0 else None


def _first_int_attr(*owners: Any, names: Sequence[str]) -> int | None:
    for owner in owners:
        if owner is None:
            continue
        for name in names:
            value = getattr(owner, name, None)
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
            value = getattr(owner, name, None)
            if value is not None:
                return str(value)
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


def _infer_normalization_type(model: Any, config: Any) -> str | None:
    explicit = _first_str_attr(config, model, names=("normalization_type", "norm_type"))
    if explicit is not None:
        return explicit
    model_type = (getattr(config, "model_type", "") or "").lower()
    if any(marker in model_type for marker in ("llama", "qwen", "mistral", "gemma", "t5")):
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
    return list(values)


def _wrapper_looks_like_local_path(value: str) -> bool:
    return value.startswith((".", "/", "~"))


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
            matches_model_name=lambda name: "qwen3" in name.lower(),
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
                "the TransformerLens supported model list."
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
                    "T5, Wav2Vec2/Hubert, and LLaMA-like decoder families.",
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
    return TransformerLensCompatibleModelWrapper(
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
    supported = is_transformer_lens_supported_model_name(model_name)
    resolved_model = resolve_transformer_lens_compatible_model_name(model_name)
    payload = _inspection_payload(
        model_name,
        config,
        supported=supported,
        model_family=f"transformer_lens_compatible_{transformer_lens_model_kind(model_name)}",
        resolved_pretrained_model=resolved_model,
        official_model_count=len(transformer_lens_official_model_names()),
        supported_model_examples=transformer_lens_official_model_names()[:20],
        architecture_bridge_adapters=[item["name"] for item in list_architecture_adapters()],
        bridge_components=list(supported_transformer_component_names(include_attention=True)),
        target_hook_examples=_TRANSFORMER_LENS_HOOK_COMPONENTS,
        warnings=(
            "SafeLens does not import TransformerLens for this adapter.",
            "Static inspection uses SafeLens' vendored TransformerLens support table; "
            "loading uses Transformers auto classes and may require a valid HF ID or local path.",
            "Component hooks use SafeLens architecture adapters. Attention pattern and score "
            "hooks use eager softmax instrumentation; flash or SDPA attention paths may need "
            "an eager attention implementation.",
        ),
    )
    if not supported:
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
