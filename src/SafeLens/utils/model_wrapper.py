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
from SafeLens.core.factored_matrix import (
    FactoredMatrix,
    composition_scores,
    shape_of,
    transpose,
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
    key_value_head_count,
    list_architecture_adapters,
    resolve_module_path,
    supported_transformer_component_names,
    transpose_2d_weight,
    transformer_lens_component_name,
    zeros_like_last_dim,
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
    "blocks.N.attn.hook_q",
    "blocks.N.attn.hook_k",
    "blocks.N.attn.hook_v",
    "blocks.N.attn.hook_z",
    "blocks.N.attn.hook_pattern",
    "blocks.N.attn.hook_attn_scores",
    "blocks.N.attn.hook_result",
    "blocks.N.hook_attn_out",
    "blocks.N.mlp.hook_pre",
    "blocks.N.mlp.hook_pre_linear",
    "blocks.N.mlp.hook_post",
    "blocks.N.hook_mlp_out",
    "ln_final.hook_scale",
)
_TRANSFORMER_LENS_PATCH_COMPONENTS = (
    "embed",
    "pos_embed",
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
    "pattern",
    "attn_scores",
)
_DEFAULT_RETURN_TYPE = object()
_DEFAULT_CACHE_ALL = object()
_DEFAULT_RETURN_CACHE_OBJECT = object()
_DEFAULT_CACHE_EXCLUDED_COMPONENTS = {"attn_scores"}
_TOP_LEVEL_HOOK_ALIASES = {
    "hook_embed": "hook_embed",
    "embed": "hook_embed",
    "hook_pos_embed": "hook_pos_embed",
    "pos_embed": "hook_pos_embed",
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


class _HookHandleWithContexts:
    def __init__(self, handle: Any, hook_contexts: Sequence[Any]) -> None:
        self._handle = handle
        self.hook_contexts = tuple(hook_contexts)

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
        return transpose_2d_weight(weight)

    @property
    def b_U(self) -> Any:
        """Return unembedding bias shaped `[vocab]` when available, else zeros."""
        embeddings = self._output_embeddings()
        bias = getattr(embeddings, "bias", None)
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
        layer = self._resolve_hook_layer_ref(model, layer, for_cache=False)
        top_level_handle = self._try_register_top_level_hook(model, layer, hook_fn)
        if top_level_handle is not None:
            return top_level_handle
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
                managed_handle = self._track_hook_handle(handle, is_permanent=True)
                self._hooks.append(managed_handle)
                installed_handles.append(managed_handle)
        except Exception:
            for handle in reversed(installed_handles):
                handle.remove()
            activation_cache.model = previous_cache_model
            activation_cache.has_batch_dim = previous_has_batch_dim
            raise
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

    def to_tokens(
        self,
        text: str | Sequence[str],
        *,
        prepend_bos: bool = True,
        padding_side: str | None = None,
        move_to_device: bool = True,
        truncate: bool = True,
    ) -> Any:
        """Tokenize text into a tensor, mirroring TransformerLens' convenience method."""
        tokenizer = self._require_tokenizer_for_text("tokenization")
        token_kwargs: dict[str, Any] = {
            "return_tensors": "pt",
            "add_special_tokens": False,
            "padding": not isinstance(text, str),
        }
        with (
            _temporary_tokenizer_padding_side(tokenizer, padding_side),
            _temporary_tokenizer_pad_token(tokenizer, enabled=bool(token_kwargs["padding"])),
        ):
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
            tokens = _prepend_bos_token(tokens, tokenizer)
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
        prepend_bos: bool = True,
        padding_side: str | None = None,
    ) -> list[str] | list[list[str]]:
        """Return per-token strings for text or token ids."""
        tokenizer = self._require_tokenizer_for_text("token string conversion")
        if isinstance(text_or_tokens, list) and text_or_tokens and isinstance(
            text_or_tokens[0],
            list | str,
        ):
            return [
                self.to_str_tokens(
                    item,
                    prepend_bos=prepend_bos,
                    padding_side=padding_side,
                )
                for item in text_or_tokens
            ]
        tokens = (
            self.to_tokens(
                text_or_tokens,
                prepend_bos=prepend_bos,
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
                raise ValueError(f"Invalid token shape for token string conversion: {shape_tuple!r}.")
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
        prepend_bos: bool = True,
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
            if isinstance(weight, list):
                return _gather_list_residual_directions(weight, tokens)
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
        biases = [
            adapter.get_attention_bias(model, component, layer) for layer in range(n_layers)
        ]
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

    def _try_register_top_level_hook(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
    ) -> Any | None:
        hook_name = _canonical_top_level_hook_name(layer)
        if hook_name is None:
            return None
        module = _resolve_top_level_hook_module(model, hook_name)
        if module is None:
            return None
        hook_context = _TopLevelHookContext(hook_name)

        def hook(_module: Any, _inputs: Any, output: Any) -> Any:
            patched = _call_top_level_hook(
                hook_fn,
                activation=output,
                hook_name=hook_name,
                hook_context=hook_context,
            )
            return None if patched is None else patched

        return _HookHandleWithContexts(
            module.register_forward_hook(hook),
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
        if adapter.parse_component_ref(layer) is None:
            return None
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
        return module.register_forward_hook(
            make_cache_hook(
                cache,
                hook_name,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
            )
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
        layer = self._resolve_hook_layer_ref(
            self._require_model(),
            layer,
            for_cache=False,
        )
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
                if not matched:
                    raise KeyError(f"No hook names matched filter {layer_or_filter!r}.")
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
        if component not in _QWEN3_PATCHABLE_COMPONENTS and component not in _QWEN3_EXPLICIT_COMPONENTS:
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
        if component == "pre":
            return self._register_tensor_output_hook(
                qwen_layer.mlp.gate_proj,
                layer_index,
                component,
                hook_fn,
            )
        if component == "pre_linear":
            return self._register_tensor_output_hook(
                qwen_layer.mlp.up_proj,
                layer_index,
                component,
                hook_fn,
            )
        if component == "post":
            return self._register_input_hook(
                qwen_layer.mlp.down_proj,
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
    previous = getattr(tokenizer, "padding_side")
    setattr(tokenizer, "padding_side", padding_side)
    try:
        yield
    finally:
        setattr(tokenizer, "padding_side", previous)


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
        setattr(tokenizer, "pad_token", fallback_token)
    if changed_token_id:
        setattr(tokenizer, "pad_token_id", fallback_token_id)
    try:
        yield
    finally:
        if changed_token:
            setattr(tokenizer, "pad_token", previous_token)
        if changed_token_id:
            setattr(tokenizer, "pad_token_id", previous_token_id)


def _tokenizer_needs_pad_token(tokenizer: Any) -> bool:
    return getattr(tokenizer, "pad_token", None) is None and getattr(
        tokenizer,
        "pad_token_id",
        None,
    ) is None


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


def _single_token_list(tokens: Any) -> list[int]:
    shape = _shape_of_token_ids(tokens)
    values = tokens.tolist() if hasattr(tokens, "tolist") else tokens
    if shape is None or len(shape) == 0:
        return [int(values)]
    if len(shape) == 1:
        return [int(token) for token in list(values)]
    if len(shape) == 2 and shape[0] == 1:
        row = values[0] if isinstance(values, list) else values
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
    return name.removeprefix("hook_")


def _top_level_hook_is_resolvable(model: Any, name: str) -> bool:
    return _resolve_top_level_hook_module(model, name) is not None


def _top_level_hook_names(model: Any) -> list[str]:
    return [
        name
        for name in ("hook_embed", "hook_pos_embed")
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
    try:
        hook_signature = signature(hook_fn)
    except (TypeError, ValueError):
        return hook_fn(activation, hook_context)

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
        return hook_fn(activation)


def _candidate_hook_names(model: Any, adapter: Any, *, for_cache: bool | None = None) -> list[str]:
    names: list[str] = _top_level_hook_names(model)
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
    names: list[str] = _top_level_hook_names(model)
    n_layers = _infer_model_layers(model)
    for layer in range(n_layers):
        for component in adapter.supported_components(for_cache=True):
            if component in _DEFAULT_CACHE_EXCLUDED_COMPONENTS:
                continue
            name = transformer_lens_component_name(component, layer)
            if not _component_hook_is_resolvable(model, adapter, name):
                continue
            names.append(name)
    return names


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
    n_key_value_heads = key_value_head_count(model)
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
    if isinstance(value, list):
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
    if isinstance(value, list):
        return [_clone_tensor_like(item) for item in value]
    return value


def _add_tensor_like_values(left: Any, right: Any) -> Any:
    if isinstance(left, list) and isinstance(right, list):
        return [
            _add_tensor_like_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        ]
    if isinstance(left, list):
        coerced_left = _coerce_list_to_tensor_like(left, right)
        if coerced_left is not None:
            return coerced_left + right
    if isinstance(right, list):
        coerced_right = _coerce_list_to_tensor_like(right, left)
        if coerced_right is not None:
            return left + coerced_right
    try:
        return left + right
    except Exception:
        pass
    if isinstance(left, list) or isinstance(right, list):
        raise TypeError(
            f"Cannot add values of types {type(left).__name__} and {type(right).__name__}."
        )
    return float(left) + float(right)


def _coerce_list_to_tensor_like(value: list[Any], like: Any) -> Any | None:
    module = type(like).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            return torch.as_tensor(
                value,
                dtype=getattr(like, "dtype", None),
                device=getattr(like, "device", None),
            )
        except Exception:
            return None
    if module == "numpy":
        try:
            import numpy as np

            return np.asarray(value, dtype=getattr(like, "dtype", None))
        except Exception:
            return None
    return None


def _mask_composition_scores_to_future_layers(scores: Any) -> Any:
    shape = shape_of(scores)
    if len(shape) < 4:
        raise ValueError(f"Composition scores must have shape [layer, head, layer, head], got {shape}.")
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
    if isinstance(scores, list):
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
    raise TypeError(
        f"Cannot mask composition scores for value type {type(scores).__name__}."
    )


def _zero_like_tensor_value(value: Any) -> Any:
    if isinstance(value, list):
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


def _concat_first_dim(left: Any, right: Any) -> Any:
    if type(left).__module__.split(".")[0] == "torch":
        try:
            import torch

            return torch.cat([left, right], dim=0)
        except ImportError:
            pass
    if isinstance(left, list) and isinstance(right, list):
        return [*left, *right]
    concatenate = getattr(left, "concatenate", None)
    if callable(concatenate):
        return concatenate([left, right], axis=0)
    return [*left, *right]


def _gather_list_residual_directions(weight: list[Any], tokens: Any) -> Any:
    tolist = getattr(tokens, "tolist", None)
    if callable(tolist):
        tokens = tolist()
    if isinstance(tokens, Integral):
        return list(weight[int(tokens)])
    if isinstance(tokens, Sequence) and not isinstance(tokens, str | bytes):
        return [_gather_list_residual_directions(weight, token) for token in tokens]
    item = getattr(tokens, "item", None)
    if callable(item):
        return list(weight[int(item())])
    return list(weight[int(tokens)])


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
