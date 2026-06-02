"""Architecture bridge primitives for Transformers-backed model adapters.

The design mirrors the useful part of TransformerLens' model bridge: keep model
loading provider-specific, but map each model family into a small canonical
component vocabulary that SafeLens hooks and patching code can target.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from SafeLens.core.base import HookFn, LayerRef
from SafeLens.core.hook_call import call_user_hook
from SafeLens.core.tensors import repeat_along_head_dimension
from SafeLens.core.utilities import complex_attn_linear
from SafeLens.utils.transformer_lens_support import resolve_transformer_lens_compatible_model_name

HookMode = Literal["forward_output", "forward_input"]
ComponentValue = Literal["output", "attention_pattern", "attention_scores", "norm_scale"]
ComponentActivation = Literal["raw", "split_heads", "split_qkv_heads", "repeat_heads"]
QKVLayout = Literal["split", "interleaved"]

CANONICAL_TRANSFORMER_COMPONENTS: tuple[str, ...] = (
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
    "result",
    "pattern",
    "attn_scores",
    "ln1_scale",
    "ln2_scale",
    "ln1_normalized",
    "ln2_normalized",
    "decoder_resid_pre",
    "decoder_resid_mid",
    "decoder_resid_mid_cross",
    "decoder_resid_post",
    "decoder_attn_in",
    "decoder_attn_out",
    "cross_attn_in",
    "cross_attn_out",
    "decoder_mlp_in",
    "decoder_mlp_out",
    "decoder_q_input",
    "decoder_k_input",
    "decoder_v_input",
    "decoder_pre",
    "decoder_pre_linear",
    "decoder_post",
    "decoder_q",
    "decoder_k",
    "decoder_v",
    "decoder_z",
    "decoder_result",
    "decoder_pattern",
    "decoder_attn_scores",
    "cross_q",
    "cross_k",
    "cross_v",
    "cross_z",
    "cross_result",
    "cross_pattern",
    "cross_attn_scores",
    "decoder_ln1_scale",
    "decoder_ln2_scale",
    "decoder_ln3_scale",
    "decoder_ln1_normalized",
    "decoder_ln2_normalized",
    "decoder_ln3_normalized",
    "ssm_in",
    "ssm_conv",
    "ssm_x",
    "ssm_dt",
    "ssm_out",
    "ssm_inner_norm",
)

_UNSUPPORTED_ATTENTION_REASON = (
    "this fallback adapter has no known attention module path for softmax instrumentation"
)
_UNSUPPORTED_RESULT_REASON = (
    "TransformerLens result vectors are derived from z @ W_O for HuggingFace " "projection modules"
)
_UNSUPPORTED_SSM_ATTENTION_REASON = "state-space model adapters do not expose attention activations"
_ATTENTION_SOFTMAX_STATE_ATTR = "_safelens_attention_softmax_hook_state"
_HOOK_CONTEXTS_ATTR = "_safelens_hook_contexts"
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
class ComponentRef:
    """One parsed reference to a canonical transformer component."""

    layer: int
    component: str
    original: LayerRef
    transformer_lens_name_override: str | None = None

    @property
    def safelens_name(self) -> str:
        return f"layer_{self.layer}.{self.component}"

    @property
    def transformer_lens_name(self) -> str:
        if self.transformer_lens_name_override is not None:
            return self.transformer_lens_name_override
        return transformer_lens_component_name(self.component, self.layer)


class ComponentHookContext:
    """Small TransformerLens-style hook object passed to component hooks."""

    def __init__(self, component_ref: ComponentRef) -> None:
        self.name = component_ref.transformer_lens_name
        self.component = component_ref.component
        self.ctx: dict[str, Any] = {}
        self._layer = component_ref.layer
        self.safelens_name = component_ref.safelens_name

    def layer(self) -> int:
        return self._layer


@dataclass(frozen=True)
class ComponentHookSpec:
    """How one canonical component maps to a HuggingFace module path."""

    component: str
    mode: HookMode
    module_paths: tuple[str, ...]
    value: ComponentValue = "output"
    activation: ComponentActivation = "raw"
    qkv_layout: QKVLayout = "split"
    aliases: tuple[str, ...] = ()
    patchable: bool = True
    cacheable: bool = True
    supported: bool = True
    unsupported_reason: str | None = None
    transformer_lens_name_template: str | None = None

    def all_names(self) -> tuple[str, ...]:
        return (self.component, *self.aliases)


class ArchitectureAdapter:
    """Map one architecture family onto SafeLens' canonical component names."""

    def __init__(
        self,
        *,
        name: str,
        model_types: Sequence[str],
        component_specs: Sequence[ComponentHookSpec],
        model_name_markers: Sequence[str] = (),
        notes: Sequence[str] = (),
    ) -> None:
        self.name = name
        self.model_types = tuple(model_types)
        self.model_name_markers = tuple(marker.lower() for marker in model_name_markers)
        self.notes = tuple(notes)
        self._specs = {spec.component: spec for spec in component_specs}
        self._aliases: dict[str, str] = {}
        for spec in component_specs:
            for alias in spec.all_names():
                self._aliases[alias] = spec.component

    def supports_model(self, *, model_type: str | None, model_name: str) -> bool:
        lowered_model_type = (model_type or "").lower()
        lowered_model_name = model_name.lower()
        return lowered_model_type in self.model_types or any(
            marker in lowered_model_name for marker in self.model_name_markers
        )

    def supported_components(
        self,
        *,
        include_unsupported: bool = False,
        for_cache: bool | None = None,
    ) -> tuple[str, ...]:
        components: list[str] = []
        for spec in self._specs.values():
            if not include_unsupported and not spec.supported:
                continue
            if for_cache is True and not spec.cacheable:
                continue
            if for_cache is False and not spec.patchable:
                continue
            if for_cache is None and not include_unsupported and not spec.patchable:
                continue
            components.append(spec.component)
        return tuple(components)

    def inspect(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_types": list(self.model_types),
            "model_name_markers": list(self.model_name_markers),
            "supported_components": list(self.supported_components()),
            "cacheable_components": list(self.supported_components(for_cache=True)),
            "patchable_components": list(self.supported_components(for_cache=False)),
            "target_components": list(self.supported_components(include_unsupported=True)),
            "notes": list(self.notes),
        }

    def parse_component_ref(self, layer: LayerRef) -> ComponentRef | None:
        if isinstance(layer, int):
            return ComponentRef(layer=layer, component="resid_post", original=layer)
        if isinstance(layer, tuple):
            if not layer:
                return None
            component = str(layer[0])
            layer_index = layer[1] if len(layer) >= 2 else None
            layer_type = str(layer[2]) if len(layer) >= 3 and layer[2] is not None else None
            if not isinstance(layer_index, int):
                return None
            return self._make_ref(
                layer_index,
                _normalize_component(component, layer_type=layer_type),
                layer,
            )
        if not isinstance(layer, str):
            return None

        safe_match = re.fullmatch(r"layer_(\d+)\.([a-zA-Z0-9_]+)", layer)
        if safe_match is not None:
            return self._make_ref(
                int(safe_match.group(1)),
                safe_match.group(2),
                layer,
            )

        block_match = re.fullmatch(
            r"(blocks|encoder|decoder)\.(\d+)\.(?:([a-zA-Z0-9_]+)\.)?hook_([a-zA-Z0-9_]+)",
            layer,
        )
        if block_match is not None:
            stack = block_match.group(1)
            layer_type = block_match.group(3)
            return self._make_ref(
                int(block_match.group(2)),
                _normalize_component(
                    block_match.group(4),
                    layer_type=layer_type,
                    stack=stack if stack in {"encoder", "decoder"} else None,
                ),
                layer,
            )

        return None

    def register_component_hook(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        prepend: bool = False,
    ) -> Any:
        return self.register_component_hook_for_mode(
            model,
            layer,
            hook_fn,
            for_cache=False,
            prepend=prepend,
        )

    def register_component_hook_for_mode(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        for_cache: bool,
        prepend: bool = False,
    ) -> Any:
        component_ref = self.parse_component_ref(layer)
        if component_ref is None:
            raise KeyError(f"Layer reference {layer!r} is not a component hook name.")
        spec = self._spec_for_ref(component_ref, for_cache=for_cache)
        module = self.get_component(model, component_ref)
        if spec.value == "attention_scores" or (
            spec.value == "attention_pattern" and not for_cache
        ):
            return _register_attention_softmax_hook(
                module,
                hook_fn,
                component_ref,
                self.name,
                spec,
                prepend=prepend,
            )
        if _is_attention_result_component(spec.component) and not for_cache:
            hook = _make_attention_result_output_hook(
                hook_fn,
                component_ref,
                self.name,
                spec,
                model,
            )
            return _ComponentHookHandle(
                _register_module_forward_hook(module, hook, prepend=prepend),
                _hook_contexts_for(hook),
            )
        if spec.value == "norm_scale" or spec.component.endswith("_normalized"):
            hook = _make_component_output_hook(hook_fn, component_ref, self.name, spec, model)
            return _ComponentHookHandle(
                _register_module_forward_hook(module, hook, prepend=prepend),
                _hook_contexts_for(hook),
            )
        t5_input_handle = _try_register_t5_attention_input_patch(
            model,
            hook_fn,
            component_ref,
            self.name,
            spec,
            prepend=prepend,
            for_cache=for_cache,
        )
        if t5_input_handle is not None:
            return t5_input_handle
        if spec.mode == "forward_input":
            hook = _make_component_input_hook(hook_fn, component_ref, self.name, spec, model)
            return _ComponentHookHandle(
                _register_module_forward_pre_hook(module, hook, prepend=prepend),
                _hook_contexts_for(hook),
            )
        hook = _make_component_output_hook(hook_fn, component_ref, self.name, spec, model)
        return _ComponentHookHandle(
            _register_module_forward_hook(module, hook, prepend=prepend),
            _hook_contexts_for(hook),
        )

    def requires_output_attentions(self, layer: LayerRef) -> bool:
        component_ref = self.parse_component_ref(layer)
        if component_ref is None:
            return False
        spec = self._specs.get(component_ref.component)
        return spec is not None and spec.value in {"attention_pattern", "attention_scores"}

    def get_component(self, model: Any, component_ref: ComponentRef) -> Any:
        spec = self._spec_for_ref(component_ref, for_cache=True)
        attempted_paths: list[str] = []
        for template in spec.module_paths:
            path = template.format(layer=component_ref.layer)
            attempted_paths.append(path)
            try:
                return resolve_module_path(model, path)
            except (AttributeError, IndexError, KeyError, TypeError):
                continue
        attempted = ", ".join(attempted_paths)
        raise KeyError(
            f"Could not resolve component {component_ref.component!r} for architecture "
            f"{self.name!r}. Tried module paths: {attempted}."
        )

    def get_attention_weight(self, model: Any, component: str, layer: int) -> Any:
        """Return a TransformerLens-shaped attention weight tensor for one layer."""
        component_ref = self._make_ref(layer, component, component)
        if component_ref is None:
            raise KeyError(f"Unknown attention component {component!r}.")
        spec = self._spec_for_ref(component_ref, for_cache=True)
        module = self.get_component(model, component_ref)
        weight = getattr(module, "weight", None)
        if weight is None:
            raise KeyError(f"Component {component!r} at layer {layer} has no weight.")
        if spec.activation == "split_qkv_heads":
            base_component = _attention_base_component(component)
            return reshape_joint_qkv_attention_weight(
                weight,
                component=base_component,
                q_heads=head_count_for_component(model, "q"),
                kv_heads=head_count_for_component(model, "k"),
                qkv_layout=spec.qkv_layout,
                packed_axis=preferred_qkv_weight_packed_axis(module, architecture=self.name),
            )
        if spec.activation != "split_heads":
            raise NotImplementedError(
                f"{self.name} cannot expose W_{component.upper()} from "
                f"{spec.activation!r} projections yet."
            )
        base_component = _attention_base_component(component)
        n_heads = head_count_for_component(model, base_component)
        return reshape_attention_weight(
            weight,
            component=base_component,
            n_heads=n_heads,
            packed_axis=preferred_attention_weight_packed_axis(
                module,
                architecture=self.name,
                component=base_component,
            ),
        )

    def get_attention_bias(self, model: Any, component: str, layer: int) -> Any:
        """Return a TransformerLens-shaped attention bias for one layer."""
        component_ref = self._make_ref(layer, component, component)
        if component_ref is None:
            raise KeyError(f"Unknown attention component {component!r}.")
        spec = self._spec_for_ref(component_ref, for_cache=True)
        module = self.get_component(model, component_ref)
        bias = getattr(module, "bias", None)
        if bias is None:
            return zeros_for_attention_bias(model, component)
        if spec.activation == "split_qkv_heads":
            base_component = _attention_base_component(component)
            return reshape_joint_qkv_attention_bias(
                bias,
                component=base_component,
                q_heads=head_count_for_component(model, "q"),
                kv_heads=head_count_for_component(model, "k"),
                qkv_layout=spec.qkv_layout,
            )
        if spec.activation != "split_heads":
            raise NotImplementedError(
                f"{self.name} cannot expose b_{component.upper()} from "
                f"{spec.activation!r} projections yet."
            )
        base_component = _attention_base_component(component)
        return reshape_attention_bias(
            bias,
            component=base_component,
            n_heads=head_count_for_component(model, base_component),
        )

    def get_embedding_weight(self, model: Any, *, positional: bool = False) -> Any:
        """Return token or positional embedding weights for common Transformers layouts."""
        paths = _POSITION_EMBEDDING_MODULE_PATHS if positional else _TOKEN_EMBEDDING_MODULE_PATHS
        kind = "positional embedding" if positional else "token embedding"
        try:
            return _weight_from_first_path(model, paths, kind=kind)
        except KeyError as path_error:
            if positional:
                raise
            embedding_weight = _input_embedding_weight_from_model(model)
            if embedding_weight is not None:
                return embedding_weight
            raise path_error

    def get_mlp_weight(self, model: Any, component: str, layer: int) -> Any:
        """Return a TransformerLens-shaped MLP weight matrix for one layer."""
        if component == "in":
            paths = self._mlp_weight_paths(
                layer,
                canonical_component="pre_linear",
                fallback_component="pre",
            )
        elif component == "gate":
            self._raise_if_mlp_component_unsupported("pre")
            paths = (
                *self._mlp_weight_paths(layer, canonical_component="pre"),
                f"model.language_model.layers.{layer}.mlp.gate",
                f"model.language_model.layers.{layer}.mlp.w1",
                f"model.layers.{layer}.mlp.gate",
                f"model.layers.{layer}.mlp.w1",
            )
        elif component == "out":
            paths = self._mlp_weight_paths(layer, canonical_component="post")
        else:
            raise ValueError(f"Unsupported MLP weight component {component!r}.")
        module, weight = _module_weight_from_first_path(
            model,
            paths,
            kind=f"MLP {component} weight",
        )
        if _is_transformers_conv1d_module(module):
            return weight
        return transpose_2d_weight(weight)

    def get_mlp_bias(self, model: Any, component: str, layer: int) -> Any:
        """Return a TransformerLens-shaped MLP bias vector for one layer."""
        if component == "in":
            paths = self._mlp_weight_paths(
                layer,
                canonical_component="pre_linear",
                fallback_component="pre",
            )
        elif component == "out":
            paths = self._mlp_weight_paths(layer, canonical_component="post")
        else:
            raise ValueError(f"Unsupported MLP bias component {component!r}.")
        zero_axis = 1 if self.name == "gpt2_decoder" else 0
        return _bias_from_first_path(
            model,
            paths,
            kind=f"MLP {component} bias",
            zero_axis=zero_axis,
        )

    def _raise_if_mlp_component_unsupported(self, canonical_component: str) -> None:
        spec = self._specs.get(canonical_component)
        if spec is not None and not spec.supported:
            reason = spec.unsupported_reason or f"component {spec.component!r} is not supported"
            raise NotImplementedError(f"{self.name} does not expose {spec.component!r}: {reason}.")

    def _mlp_weight_paths(
        self,
        layer: int,
        *,
        canonical_component: str,
        fallback_component: str | None = None,
    ) -> tuple[str, ...]:
        spec = self._specs.get(canonical_component)
        if spec is None and fallback_component is not None:
            spec = self._specs.get(fallback_component)
        if spec is None:
            raise KeyError(f"{self.name!r} does not declare MLP component {canonical_component!r}.")
        if not spec.supported:
            reason = spec.unsupported_reason or f"component {spec.component!r} is not supported"
            raise NotImplementedError(f"{self.name} does not expose {spec.component!r}: {reason}.")
        return tuple(template.format(layer=layer) for template in spec.module_paths)

    def _make_ref(self, layer: int, component: str, original: LayerRef) -> ComponentRef | None:
        normalized = component if component in self._aliases else _normalize_component(component)
        if normalized not in self._aliases:
            return None
        canonical_component = self._aliases[normalized]
        spec = self._specs.get(canonical_component)
        transformer_lens_name_override = None
        if spec is not None and spec.transformer_lens_name_template is not None:
            transformer_lens_name_override = spec.transformer_lens_name_template.format(layer=layer)
        return ComponentRef(
            layer=layer,
            component=canonical_component,
            original=original,
            transformer_lens_name_override=transformer_lens_name_override,
        )

    def _spec_for_ref(self, component_ref: ComponentRef, *, for_cache: bool) -> ComponentHookSpec:
        spec = self._specs[component_ref.component]
        if not spec.supported:
            reason = spec.unsupported_reason or f"component {spec.component!r} is not supported"
            raise NotImplementedError(f"{self.name} does not expose {spec.component!r}: {reason}.")
        if for_cache and not spec.cacheable:
            raise NotImplementedError(f"{self.name} cannot cache {spec.component!r}.")
        if not for_cache and not spec.patchable:
            if spec.unsupported_reason:
                raise NotImplementedError(
                    f"{self.name} can cache {spec.component!r}, but cannot patch it: "
                    f"{spec.unsupported_reason}."
                )
            raise NotImplementedError(
                f"{self.name} can cache {spec.component!r}, but cannot patch it "
                "without instrumenting the attention computation before value mixing."
            )
        return spec


def resolve_module_path(model: Any, path: str) -> Any:
    """Resolve a dotted module path with integer list indexes."""
    target = model
    for part in path.split("."):
        if part.isdigit():
            target = target[int(part)]
        else:
            target = getattr(target, part)
    return target


def _register_module_forward_hook(
    module: Any,
    hook: Callable[..., Any],
    *,
    prepend: bool = False,
) -> Any:
    register = module.register_forward_hook
    try:
        return register(hook, prepend=prepend)
    except TypeError:
        return register(hook)


def _register_module_forward_pre_hook(
    module: Any,
    hook: Callable[..., Any],
    *,
    prepend: bool = False,
) -> Any:
    register = module.register_forward_pre_hook
    try:
        return register(hook, prepend=prepend)
    except TypeError:
        return register(hook)


def _weight_from_first_path(model: Any, paths: Sequence[str], *, kind: str) -> Any:
    return _module_weight_from_first_path(model, paths, kind=kind)[1]


def _module_weight_from_first_path(
    model: Any,
    paths: Sequence[str],
    *,
    kind: str,
) -> tuple[Any, Any]:
    attempted: list[str] = []
    for path in paths:
        attempted.append(path)
        try:
            module = resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
        weight = getattr(module, "weight", None)
        if weight is not None:
            return module, weight
    attempted_paths = ", ".join(attempted)
    raise KeyError(f"Could not resolve {kind}. Tried module paths: {attempted_paths}.")


def _is_transformers_conv1d_module(module: Any) -> bool:
    module_type = type(module)
    if module_type.__name__ == "Conv1D" and "transformers" in module_type.__module__:
        return True
    return hasattr(module, "nf") and hasattr(module, "nx")


def _input_embedding_weight_from_model(model: Any) -> Any | None:
    get_input_embeddings = getattr(model, "get_input_embeddings", None)
    if not callable(get_input_embeddings):
        return None
    try:
        embeddings = get_input_embeddings()
    except Exception:
        return None
    return getattr(embeddings, "weight", None)


def _bias_from_first_path(
    model: Any,
    paths: Sequence[str],
    *,
    kind: str,
    zero_axis: int = 0,
) -> Any:
    attempted: list[str] = []
    for path in paths:
        attempted.append(path)
        try:
            module = resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
        bias = getattr(module, "bias", None)
        if bias is not None:
            return bias
        weight = getattr(module, "weight", None)
        if weight is not None:
            return zeros_like_last_dim(weight, axis=zero_axis)
    attempted_paths = ", ".join(attempted)
    raise KeyError(f"Could not resolve {kind}. Tried module paths: {attempted_paths}.")


def transpose_2d_weight(weight: Any) -> Any:
    """Return a rank-2 weight transposed without requiring tensor dependencies."""
    if hasattr(weight, "T") and getattr(weight, "ndim", 0) == 2:
        return weight.T
    if _is_sequence(weight):
        shape = _nested_shape(weight)
        if len(shape) != 2:
            return weight
        return [list(column) for column in zip(*weight, strict=True)]
    return weight


def zeros_like_last_dim(value: Any, *, axis: int = -1) -> Any:
    shape = getattr(value, "shape", None)
    if shape is not None:
        try:
            import torch

            return torch.zeros(
                int(shape[axis]),
                dtype=getattr(value, "dtype", None),
                device=getattr(value, "device", None),
            )
        except ImportError:
            pass
    nested_shape = _nested_shape(value)
    if not nested_shape:
        return 0
    if axis < 0:
        axis = len(nested_shape) + axis
    return [0 for _ in range(nested_shape[axis])]


_ATTENTION_HOOK_COMPONENTS = frozenset({"q", "k", "v", "z", "pattern", "attn_scores", "result"})
_ATTENTION_INPUT_COMPONENTS = frozenset({"q_input", "k_input", "v_input", "attn_in"})
_ATTENTION_PREFIXES = ("decoder", "cross")


def _prefixed_attention_component(component: str) -> tuple[str, str] | None:
    for prefix in _ATTENTION_PREFIXES:
        prefix_text = f"{prefix}_"
        if not component.startswith(prefix_text):
            continue
        base_component = component.removeprefix(prefix_text)
        if base_component in _ATTENTION_HOOK_COMPONENTS:
            return prefix, base_component
        if prefix == "decoder" and base_component in _ATTENTION_INPUT_COMPONENTS:
            return prefix, base_component
    return None


def _attention_base_component(component: str) -> str:
    prefixed = _prefixed_attention_component(component)
    if prefixed is None:
        return component
    return prefixed[1]


def _is_attention_result_component(component: str) -> bool:
    return _attention_base_component(component) == "result"


def _is_attention_pattern_component(component: str) -> bool:
    return _attention_base_component(component) == "pattern"


def _is_attention_scores_component(component: str) -> bool:
    return _attention_base_component(component) == "attn_scores"


def transformer_lens_component_name(component: str, layer: int) -> str:
    """Return a TransformerLens-style hook name for a canonical component."""
    if component in {"q_input", "k_input", "v_input", "attn_in"}:
        return f"blocks.{layer}.hook_{component}"
    if component in {"decoder_q_input", "decoder_k_input", "decoder_v_input", "decoder_attn_in"}:
        return f"decoder.{layer}.hook_{component.removeprefix('decoder_')}"
    prefixed_attention = _prefixed_attention_component(component)
    if prefixed_attention is not None:
        prefix, base_component = prefixed_attention
        layer_type = "attn" if prefix == "decoder" else "cross_attn"
        return f"decoder.{layer}.{layer_type}.hook_{base_component}"
    if component in _ATTENTION_HOOK_COMPONENTS:
        hook_component = "attn_scores" if component == "attn_scores" else component
        return f"blocks.{layer}.attn.hook_{hook_component}"
    if component in {"pre", "pre_linear", "post"}:
        return f"blocks.{layer}.mlp.hook_{component}"
    if component in {"decoder_pre", "decoder_pre_linear", "decoder_post"}:
        return f"decoder.{layer}.mlp.hook_{component.removeprefix('decoder_')}"
    if component in {"ln1_scale", "ln1_normalized"}:
        hook_component = "scale" if component == "ln1_scale" else "normalized"
        return f"blocks.{layer}.ln1.hook_{hook_component}"
    if component in {"ln2_scale", "ln2_normalized"}:
        hook_component = "scale" if component == "ln2_scale" else "normalized"
        return f"blocks.{layer}.ln2.hook_{hook_component}"
    if component in {"decoder_ln1_scale", "decoder_ln1_normalized"}:
        hook_component = "scale" if component == "decoder_ln1_scale" else "normalized"
        return f"decoder.{layer}.ln1.hook_{hook_component}"
    if component in {"decoder_ln2_scale", "decoder_ln2_normalized"}:
        hook_component = "scale" if component == "decoder_ln2_scale" else "normalized"
        return f"decoder.{layer}.ln2.hook_{hook_component}"
    if component in {"decoder_ln3_scale", "decoder_ln3_normalized"}:
        hook_component = "scale" if component == "decoder_ln3_scale" else "normalized"
        return f"decoder.{layer}.ln3.hook_{hook_component}"
    if component.startswith("decoder_"):
        return f"decoder.{layer}.hook_{component.removeprefix('decoder_')}"
    if component in {"cross_attn_in", "cross_attn_out"}:
        return f"decoder.{layer}.hook_{component}"
    if component.startswith("ssm_"):
        return f"blocks.{layer}.ssm.hook_{component.removeprefix('ssm_')}"
    return f"blocks.{layer}.hook_{component}"


def supported_transformer_component_names(
    *,
    include_pattern: bool = False,
    include_attention: bool = False,
    include_result: bool = True,
) -> tuple[str, ...]:
    """Return the canonical component vocabulary exposed by model bridges."""
    supported_components = tuple(
        component
        for component in CANONICAL_TRANSFORMER_COMPONENTS
        if include_result or not _is_attention_result_component(component)
    )
    if include_attention:
        return supported_components
    if include_pattern:
        return tuple(
            component
            for component in supported_components
            if not _is_attention_result_component(component)
            and not _is_attention_scores_component(component)
        )
    return tuple(
        component
        for component in supported_components
        if not _is_attention_result_component(component)
        and not _is_attention_pattern_component(component)
        and not _is_attention_scores_component(component)
    )


def architecture_adapter_for_model(model: Any, *, model_name: str = "") -> ArchitectureAdapter:
    """Select a SafeLens architecture adapter for a loaded Transformers model."""
    config = _model_config(model)
    model_type = _config_attr(config, "model_type")
    return architecture_adapter_for_name(model_name=model_name, model_type=model_type)


def architecture_adapter_for_name(
    *,
    model_name: str,
    model_type: str | None = None,
) -> ArchitectureAdapter:
    """Select an architecture adapter from a model name and optional HF model_type."""
    resolved_model_name = resolve_transformer_lens_compatible_model_name(model_name)
    lowered_model_type = (model_type or "").lower()
    if lowered_model_type in {"", "qwen2_moe", "qwen3_moe"} and is_qwen_routed_moe_model_name(
        resolved_model_name
    ):
        return ROUTED_MOE_ADAPTER
    for adapter in SUPPORTED_ARCHITECTURE_ADAPTERS:
        if adapter.supports_model(model_type=model_type, model_name=resolved_model_name):
            return adapter
    return GENERIC_DECODER_ADAPTER


def is_qwen_routed_moe_model_name(model_name: str) -> bool:
    """Return whether a Qwen model name clearly denotes a routed MoE checkpoint."""
    lowered = resolve_transformer_lens_compatible_model_name(model_name).lower()
    if "qwen" not in lowered:
        return False
    return "moe" in lowered or re.search(r"[-_/]a\d+(?:\.\d+)?b(?:[-_/]|$)", lowered) is not None


def list_architecture_adapters() -> list[dict[str, Any]]:
    """Return public metadata for SafeLens' architecture bridge adapters."""
    return [adapter.inspect() for adapter in SUPPORTED_ARCHITECTURE_ADAPTERS]


def _make_component_output_hook(
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: ComponentHookSpec,
    model: Any,
) -> Callable[[Any, Any, Any], Any]:
    hook_context = ComponentHookContext(component_ref)

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        if spec.value == "norm_scale":
            activation = norm_scale_from_input(_module, inputs=_inputs, output=output)
            if activation is None:
                return None
        elif spec.component.endswith("_normalized") and _inputs:
            activation = normalized_output_from_scale(_module, _inputs[0])
        else:
            activation = extract_component_activation(output, spec, model)
        patched = call_component_hook(
            hook_fn,
            activation=activation,
            component_ref=component_ref,
            architecture=architecture,
            hook_context=hook_context,
        )
        if spec.value == "norm_scale":
            if patched is None or not _inputs:
                return None
            return norm_module_output_from_scale(_module, _inputs[0], patched, output)
        if spec.component.endswith("_normalized"):
            if patched is None:
                return None
            return apply_norm_affine(_module, patched, output)
        if spec.value != "output":
            return None
        if patched is None:
            return None
        return replace_component_activation(output, patched, spec, model)

    _set_hook_contexts(hook, (hook_context,))
    return hook


def _make_component_input_hook(
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: ComponentHookSpec,
    model: Any,
) -> Callable[[Any, Any], Any]:
    hook_context = ComponentHookContext(component_ref)

    def hook(_module: Any, inputs: Any) -> Any:
        if not inputs:
            return None
        raw_activation = inputs[0]
        activation = transform_component_activation(
            raw_activation,
            spec,
            model,
            module=_module,
            component_ref=component_ref,
            architecture=architecture,
        )
        patched = call_component_hook(
            hook_fn,
            activation=activation,
            component_ref=component_ref,
            architecture=architecture,
            hook_context=hook_context,
        )
        if _is_attention_result_component(spec.component):
            return None
        if patched is None:
            return None
        merged = merge_component_activation(patched, raw_activation, spec, model)
        return (merged, *tuple(inputs[1:]))

    _set_hook_contexts(hook, (hook_context,))
    return hook


def _try_register_t5_attention_input_patch(
    model: Any,
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: ComponentHookSpec,
    *,
    prepend: bool,
    for_cache: bool,
) -> _ComponentHookHandle | None:
    if for_cache or architecture != "t5_encoder_decoder" or spec.activation != "repeat_heads":
        return None
    base_component = _attention_base_component(spec.component)
    if base_component not in {"q_input", "k_input", "v_input", "attn_in"}:
        return None
    try:
        input_module = resolve_module_path(
            model,
            _t5_attention_input_norm_path(spec.component, component_ref.layer),
        )
        projection_components = _t5_attention_input_projection_components(base_component)
        projection_modules = {
            projection_component: resolve_module_path(
                model,
                _t5_attention_projection_path(
                    spec.component,
                    projection_component,
                    component_ref.layer,
                ),
            )
            for projection_component in projection_components
        }
    except (AttributeError, IndexError, KeyError, TypeError):
        return None

    hook_context = ComponentHookContext(component_ref)
    state: dict[str, list[Any]] = {}

    def input_hook(_module: Any, inputs: Any) -> None:
        if not inputs:
            return None
        raw_activation = inputs[0]
        activation = transform_component_activation(
            raw_activation,
            spec,
            model,
            module=_module,
            component_ref=component_ref,
            architecture=architecture,
        )
        patched = call_component_hook(
            hook_fn,
            activation=activation,
            component_ref=component_ref,
            architecture=architecture,
            hook_context=hook_context,
        )
        for projection_component in projection_components:
            state.setdefault(projection_component, []).append(
                activation if patched is None else patched
            )
        return None

    def make_projection_hook(projection_component: str) -> Callable[[Any, Any, Any], Any]:
        def projection_hook(_module: Any, inputs: Any, output: Any) -> Any:
            pending_inputs = state.get(projection_component)
            if not pending_inputs:
                return None
            patched_input = pending_inputs.pop(0)
            if not pending_inputs:
                state.pop(projection_component, None)
            return _project_t5_attention_input(
                patched_input,
                output,
                projection_component,
                model,
                architecture=architecture,
                module=_module,
                component=_t5_projection_component_for_input(
                    spec.component,
                    projection_component,
                ),
                norm_module=input_module,
            )

        return projection_hook

    _set_hook_contexts(input_hook, (hook_context,))
    projection_hooks = {
        projection_component: make_projection_hook(projection_component)
        for projection_component in projection_components
    }
    for projection_hook in projection_hooks.values():
        _set_hook_contexts(projection_hook, (hook_context,))
    handles = [
        _register_module_forward_pre_hook(input_module, input_hook, prepend=prepend),
        *[
            _register_module_forward_hook(
                projection_modules[projection_component],
                projection_hooks[projection_component],
                prepend=prepend,
            )
            for projection_component in projection_components
        ],
    ]
    return _ComponentHookHandle(_CompositeComponentHookHandle(handles), (hook_context,))


def _project_t5_attention_input(
    patched_input: Any,
    output: Any,
    projection_component: str,
    model: Any,
    *,
    architecture: str,
    module: Any,
    component: str,
    norm_module: Any,
) -> Any:
    normalized_input = norm_module(patched_input)
    projection_spec = ComponentHookSpec(
        component=component,
        mode="forward_output",
        module_paths=(),
        activation="split_heads",
    )
    W = _reshape_attention_projection_weight(
        getattr(module, "weight", None),
        model,
        projection_component,
        architecture=architecture,
        module=module,
    )
    b = reshape_attention_bias(
        getattr(module, "bias", None),
        component=projection_component,
        n_heads=head_count_for_component(model, projection_component),
    )
    projected = complex_attn_linear(normalized_input, W, b)
    return merge_component_activation(projected, output, projection_spec, model)


def _t5_attention_input_projection_components(component: str) -> tuple[str, ...]:
    if component == "attn_in":
        return ("q", "k", "v")
    return (component.removesuffix("_input"),)


def _t5_projection_component_for_input(component: str, projection_component: str) -> str:
    if component.startswith("decoder_"):
        return f"decoder_{projection_component}"
    return projection_component


def _t5_attention_input_norm_path(component: str, layer: int) -> str:
    if component.startswith("decoder_"):
        return f"decoder.block.{layer}.layer.0.layer_norm"
    return f"encoder.block.{layer}.layer.0.layer_norm"


def _t5_attention_projection_path(component: str, projection_component: str, layer: int) -> str:
    if component.startswith("decoder_"):
        return f"decoder.block.{layer}.layer.0.SelfAttention.{projection_component}"
    return f"encoder.block.{layer}.layer.0.SelfAttention.{projection_component}"


def _reshape_attention_projection_weight(
    weight: Any,
    model: Any,
    component: str,
    *,
    architecture: str,
    module: Any,
) -> Any:
    if weight is None:
        raise KeyError(f"Cannot patch {component}_input: projection module has no weight.")
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


def _make_attention_result_output_hook(
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: ComponentHookSpec,
    model: Any,
) -> Callable[[Any, Any, Any], Any]:
    hook_context = ComponentHookContext(component_ref)

    def hook(module: Any, inputs: Any, output: Any) -> Any:
        if not inputs:
            return None
        raw_z = inputs[0]
        raw_output = first_output(output)
        activation = compute_attention_result_activation(
            raw_z,
            model,
            spec,
            module=module,
            component_ref=component_ref,
            architecture=architecture,
        )
        patched = call_component_hook(
            hook_fn,
            activation=activation,
            component_ref=component_ref,
            architecture=architecture,
            hook_context=hook_context,
        )
        if patched is None:
            return None
        merged_output = apply_attention_result_patch(raw_output, activation, patched)
        if isinstance(output, tuple):
            return (merged_output, *output[1:])
        if _is_structured_list_output(output):
            return [merged_output, *output[1:]]
        return merged_output

    _set_hook_contexts(hook, (hook_context,))
    return hook


def _set_hook_contexts(
    hook: Callable[..., Any], contexts: tuple[ComponentHookContext, ...]
) -> None:
    setattr(hook, _HOOK_CONTEXTS_ATTR, contexts)


def _hook_contexts_for(value: Any) -> tuple[ComponentHookContext, ...]:
    contexts = getattr(value, _HOOK_CONTEXTS_ATTR, ())
    return tuple(context for context in contexts if isinstance(context, ComponentHookContext))


def call_component_hook(
    hook_fn: HookFn,
    *,
    activation: Any,
    component_ref: ComponentRef,
    architecture: str,
    hook_context: ComponentHookContext | None = None,
) -> Any:
    """Call a user hook with SafeLens component metadata when accepted."""
    if hook_context is None:
        hook_context = ComponentHookContext(component_ref)
    hook_kwargs = {
        "activation": activation,
        "output": activation,
        "component": component_ref.component,
        "layer": component_ref.layer,
        "hook_name": component_ref.safelens_name,
        "transformer_lens_name": component_ref.transformer_lens_name,
        "architecture": architecture,
        "hook": hook_context,
    }
    return call_user_hook(
        hook_fn,
        hook_kwargs,
        positional_arg_options=((activation, hook_context), (activation,)),
    )


def extract_component_activation(output: Any, spec: ComponentHookSpec, model: Any) -> Any:
    """Extract the activation value for a component from a module hook output."""
    if spec.value == "output":
        return transform_component_activation(first_output(output), spec, model)
    if spec.value == "attention_pattern":
        pattern = _find_attention_pattern(output)
        if pattern is None:
            raise RuntimeError(
                f"Could not find attention pattern in output for component {spec.component!r}. "
                "Ensure the forward pass was called with output_attentions=True and the "
                "selected Transformers attention implementation returns attention weights."
            )
        return pattern
    if spec.value == "attention_scores":
        scores = _find_attention_scores(output)
        if scores is None:
            raise RuntimeError(
                f"Could not find attention scores in output for component {spec.component!r}. "
                "Use eager attention softmax instrumentation for pre-softmax scores."
            )
        return scores
    if spec.value == "norm_scale":
        scale = norm_scale_from_input(model, inputs=(), output=output)
        if scale is None:
            raise RuntimeError(
                f"Could not compute normalization scale for component {spec.component!r}."
            )
        return scale
    return output


def first_output(output: Any) -> Any:
    """Return the tensor payload from common Transformers module outputs."""
    if isinstance(output, tuple):
        return output[0]
    if _is_structured_list_output(output):
        return output[0]
    return output


def _is_structured_list_output(output: Any) -> bool:
    """Return true for list outputs shaped like [activation, metadata, ...]."""
    if not isinstance(output, list) or len(output) < 2:
        return False
    return _looks_like_tensor_payload(output[0]) and not _looks_like_tensor_payload(output[1])


def _looks_like_tensor_payload(value: Any) -> bool:
    if hasattr(value, "shape"):
        return True
    if isinstance(value, Mapping) or isinstance(value, str | bytes):
        return False
    if _is_sequence(value):
        if not value:
            return False
        first = value[0]
        return _is_scalar_payload(first) or _looks_like_tensor_payload(first)
    return _is_scalar_payload(value)


def _is_scalar_payload(value: Any) -> bool:
    return isinstance(value, int | float | bool | complex)


def replace_component_activation(
    output: Any,
    patched: Any,
    spec: ComponentHookSpec,
    model: Any,
) -> Any:
    """Replace the tensor payload while preserving tuple/list module output shape."""
    if spec.value != "output":
        return output
    raw_output = first_output(output)
    merged = merge_component_activation(patched, raw_output, spec, model)
    if isinstance(output, tuple):
        return (merged, *output[1:])
    if _is_structured_list_output(output):
        return [merged, *output[1:]]
    return merged


def transform_component_activation(
    activation: Any,
    spec: ComponentHookSpec,
    model: Any,
    *,
    module: Any | None = None,
    component_ref: ComponentRef | None = None,
    architecture: str | None = None,
) -> Any:
    """Convert raw HF projection tensors into SafeLens component activation shape."""
    if _is_attention_result_component(spec.component):
        return compute_attention_result_activation(
            activation,
            model,
            spec,
            module=module,
            component_ref=component_ref,
            architecture=architecture,
        )
    if spec.activation == "split_heads":
        return split_heads(
            activation,
            head_count_for_component(model, _attention_base_component(spec.component)),
        )
    if spec.activation == "split_qkv_heads":
        return split_qkv_heads(activation, model, spec)
    if spec.activation == "repeat_heads":
        return repeat_along_head_dimension(
            activation,
            head_count_for_component(model, _attention_base_component(spec.component)),
        )
    if spec.component.endswith("_normalized"):
        return normalized_output_from_scale(module or model, activation)
    return activation


def compute_attention_result_activation(
    activation: Any,
    model: Any,
    spec: ComponentHookSpec,
    *,
    module: Any | None,
    component_ref: ComponentRef | None,
    architecture: str | None,
) -> Any:
    """Compute TransformerLens-style per-head `result` from merged `z` input."""
    if module is None:
        raise ValueError("Computing attention result activations requires the output module.")
    if component_ref is None:
        raise ValueError("Computing attention result activations requires a component ref.")
    weight = getattr(module, "weight", None)
    if weight is None:
        raise KeyError(
            f"Cannot compute {component_ref.safelens_name!r}: output projection has no weight."
        )
    base_component = _attention_base_component(spec.component)
    z_component = "z" if base_component == "result" else base_component
    n_heads = head_count_for_component(model, z_component)
    z_activation = split_heads(activation, n_heads)
    W_O = reshape_attention_weight(
        weight,
        component="z",
        n_heads=n_heads,
        packed_axis=preferred_attention_weight_packed_axis(
            module,
            architecture=architecture or "",
            component="z",
        ),
    )
    from SafeLens.core.analysis import compute_head_results_from_z

    return compute_head_results_from_z(z_activation, W_O)


def apply_attention_result_patch(output: Any, original_result: Any, patched_result: Any) -> Any:
    """Apply a patched per-head `result` tensor to the merged attention output."""
    delta = subtract_values(patched_result, original_result)
    merged_delta = sum_attention_heads(delta)
    return add_values(output, merged_delta)


def sum_attention_heads(value: Any) -> Any:
    """Sum the head axis in a TransformerLens `result` tensor."""
    try:
        import torch

        if hasattr(value, "shape") and isinstance(value, torch.Tensor):
            return value.sum(dim=-2)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.asarray(value).sum(axis=-2)
    except Exception:
        pass
    shape = getattr(value, "shape", None)
    if shape is not None:
        value = value.tolist()
    return _sum_nested_head_axis(value)


def first_attention_head(value: Any) -> Any:
    """Select the first head from a TransformerLens input tensor."""
    try:
        import torch

        if hasattr(value, "shape") and isinstance(value, torch.Tensor):
            return value.select(dim=-2, index=0)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.asarray(value).take(indices=0, axis=-2)
    except Exception:
        pass
    shape = getattr(value, "shape", None)
    if shape is not None:
        value = value.tolist()
    return _select_nested_penultimate_dim(value, 0)


def add_values(left: Any, right: Any) -> Any:
    try:
        if hasattr(left, "shape") or hasattr(right, "shape"):
            return left + right
    except Exception:
        pass
    if _is_sequence(left) and _is_sequence(right):
        return [
            add_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=False)
        ]
    return left + right


def subtract_values(left: Any, right: Any) -> Any:
    try:
        if hasattr(left, "shape") or hasattr(right, "shape"):
            return left - right
    except Exception:
        pass
    if _is_sequence(left) and _is_sequence(right):
        return [
            subtract_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=False)
        ]
    return left - right


def _sum_nested_head_axis(value: Any) -> Any:
    shape = _nested_shape(value)
    if len(shape) < 2:
        raise ValueError(f"Attention result must have at least head and d_model axes, got {shape}.")
    if len(shape) == 2:
        if not value:
            return []
        width = len(value[0])
        return [sum(float(head[col]) for head in value) for col in range(width)]
    return [_sum_nested_head_axis(item) for item in value]


def _nested_shape(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if _is_sequence(value):
        if not value:
            return (0,)
        return (len(value), *_nested_shape(value[0]))
    return ()


def merge_component_activation(
    activation: Any,
    reference: Any,
    spec: ComponentHookSpec,
    model: Any,
) -> Any:
    """Merge a patched SafeLens component activation back into the raw HF tensor shape."""
    if spec.activation == "split_heads":
        return merge_heads(activation, reference)
    if spec.activation == "split_qkv_heads":
        return merge_qkv_heads(activation, reference, model, spec)
    if spec.activation == "repeat_heads":
        return first_attention_head(activation)
    return activation


def norm_scale_from_input(
    module: Any, inputs: Sequence[Any] = (), output: Any | None = None
) -> Any | None:
    """Return TransformerLens-style norm scale `[batch, pos, 1]` for a norm module input."""
    source = inputs[0] if inputs else output
    if source is None:
        return None
    try:
        import torch

        if isinstance(source, torch.Tensor):
            epsilon = float(getattr(module, "variance_epsilon", getattr(module, "eps", 1e-5)))
            source_float = source.float() if not torch.is_floating_point(source) else source
            if module_uses_centered_layer_norm(module):
                source_float = source_float - source_float.mean(dim=-1, keepdim=True)
            return torch.sqrt(source_float.pow(2).mean(dim=-1, keepdim=True) + epsilon).to(
                dtype=source.dtype,
                device=source.device,
            )
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(source, "shape") and type(source).__module__.split(".")[0] == "numpy":
            array = np.asarray(source)
            epsilon = float(getattr(module, "variance_epsilon", getattr(module, "eps", 1e-5)))
            if module_uses_centered_layer_norm(module):
                array = array - array.mean(axis=-1, keepdims=True)
            return np.sqrt(np.mean(array * array, axis=-1, keepdims=True) + epsilon)
    except Exception:
        pass
    shape = _nested_shape(source)
    if len(shape) < 1:
        return None
    epsilon = float(getattr(module, "variance_epsilon", getattr(module, "eps", 1e-5)))

    def scale_vector(vector: Any) -> list[float]:
        values = [float(item) for item in vector]
        if module_uses_centered_layer_norm(module):
            mean = sum(values) / max(1, len(values))
            values = [value - mean for value in values]
        variance = sum(value * value for value in values) / max(1, len(values))
        return [math.sqrt(variance + epsilon)]

    return _map_nested_vectors(source, scale_vector)


def normalized_output_from_scale(module: Any, source: Any, scale: Any | None = None) -> Any:
    """Return normalized norm input before affine weights, matching TL hook_normalized."""
    if scale is None:
        scale = norm_scale_from_input(module, inputs=(source,), output=None)
    try:
        import torch

        if isinstance(source, torch.Tensor):
            if not isinstance(scale, torch.Tensor):
                scale = torch.as_tensor(scale, dtype=source.dtype, device=source.device)
            else:
                scale = scale.to(dtype=source.dtype, device=source.device)
            source_float = source.float() if not torch.is_floating_point(source) else source
            if module_uses_centered_layer_norm(module):
                source_float = source_float - source_float.mean(dim=-1, keepdim=True)
            return (source_float / scale).to(dtype=source.dtype, device=source.device)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(source, "shape") or hasattr(scale, "shape"):
            array = np.asarray(source)
            if module_uses_centered_layer_norm(module):
                array = array - array.mean(axis=-1, keepdims=True)
            return array / np.asarray(scale)
    except Exception:
        pass
    if scale is None:
        return source
    return _divide_by_scale_nested(source, scale, centered=module_uses_centered_layer_norm(module))


def norm_module_output_from_scale(
    module: Any, source: Any, scale: Any, reference_output: Any
) -> Any:
    """Recompute a norm module output from a patched TL-style scale."""
    normalized = normalized_output_from_scale(module, source, scale)
    return apply_norm_affine(module, normalized, reference_output)


def apply_norm_affine(module: Any, normalized: Any, reference_output: Any | None = None) -> Any:
    """Apply PyTorch/HF norm affine weights to a normalized activation."""
    weight = _first_existing_attr(module, "weight", "w")
    bias = _first_existing_attr(module, "bias", "b")
    try:
        import torch

        if isinstance(normalized, torch.Tensor):
            output = normalized
            if weight is not None:
                output = output * weight.to(dtype=output.dtype, device=output.device)
            if bias is not None:
                output = output + bias.to(dtype=output.dtype, device=output.device)
            if reference_output is not None and isinstance(reference_output, torch.Tensor):
                output = output.to(dtype=reference_output.dtype, device=reference_output.device)
            return output
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(normalized, "shape"):
            output = np.asarray(normalized)
            if weight is not None:
                output = output * np.asarray(weight)
            if bias is not None:
                output = output + np.asarray(bias)
            return output
    except Exception:
        pass
    output = normalized
    if weight is not None:
        output = _multiply_last_dim_nested(output, weight)
    if bias is not None:
        output = _add_last_dim_nested(output, bias)
    return output


def _first_existing_attr(owner: Any, *names: str) -> Any | None:
    for name in names:
        value = getattr(owner, name, None)
        if value is not None:
            return value
    return None


def module_uses_centered_layer_norm(module: Any) -> bool:
    """Return whether a norm module mean-centers like LayerNorm."""
    try:
        import torch

        if isinstance(module, torch.nn.LayerNorm):
            return True
    except Exception:
        pass
    class_name = type(module).__name__.lower()
    if "rms" in class_name:
        return False
    return "layernorm" in class_name or "layer_norm" in class_name or class_name == "layernorm"


def _map_nested_vectors(value: Any, fn: Callable[[Any], Any]) -> Any:
    shape = _nested_shape(value)
    if len(shape) <= 1:
        return fn(value)
    return [_map_nested_vectors(item, fn) for item in value]


def _divide_by_scale_nested(source: Any, scale: Any, *, centered: bool) -> Any:
    source_shape = _nested_shape(source)
    scale_shape = _nested_shape(scale)
    if len(source_shape) <= 1:
        values = [float(item) for item in source]
        if centered:
            mean = sum(values) / max(1, len(values))
            values = [value - mean for value in values]
        denominator = float(scale[0] if _is_sequence(scale) else scale)
        return [value / denominator for value in values]
    if scale_shape and len(scale_shape) < len(source_shape):
        return [_divide_by_scale_nested(item, scale, centered=centered) for item in source]
    return [
        _divide_by_scale_nested(source_item, scale_item, centered=centered)
        for source_item, scale_item in zip(source, scale, strict=True)
    ]


def _multiply_last_dim_nested(value: Any, weights: Any) -> Any:
    if not _is_sequence(value):
        return value
    if _nested_shape(value) and len(_nested_shape(value)) == 1:
        weight_values = weights.tolist() if hasattr(weights, "tolist") else weights
        return [
            float(item) * float(weight) for item, weight in zip(value, weight_values, strict=True)
        ]
    return [_multiply_last_dim_nested(item, weights) for item in value]


def _add_last_dim_nested(value: Any, bias: Any) -> Any:
    if not _is_sequence(value):
        return value
    if _nested_shape(value) and len(_nested_shape(value)) == 1:
        bias_values = bias.tolist() if hasattr(bias, "tolist") else bias
        return [
            float(item) + float(bias_item)
            for item, bias_item in zip(value, bias_values, strict=True)
        ]
    return [_add_last_dim_nested(item, bias) for item in value]


def split_heads(activation: Any, n_heads: int) -> Any:
    """Reshape `[batch, pos, hidden]` activations into `[batch, pos, head, head_dim]`."""
    shape = getattr(activation, "shape", None)
    reshape = getattr(activation, "reshape", None)
    if shape is None or not callable(reshape):
        if not _is_sequence(activation):
            return activation
        nested_shape = _nested_shape(activation)
        if len(nested_shape) < 3:
            return activation
        hidden_size = nested_shape[-1]
        if n_heads <= 0 or hidden_size % n_heads != 0:
            return activation
        return _split_nested_last_dim(activation, n_heads)
    if len(shape) < 3:
        return activation
    hidden_size = int(shape[-1])
    if n_heads <= 0 or hidden_size % n_heads != 0:
        raise ValueError(
            f"Cannot split activation with final dimension {hidden_size} into {n_heads} heads."
        )
    return activation.reshape(*shape[:-1], n_heads, hidden_size // n_heads)


def merge_heads(activation: Any, reference: Any) -> Any:
    """Flatten `[batch, pos, head, head_dim]` back to the reference final dimension."""
    shape = getattr(activation, "shape", None)
    reshape = getattr(activation, "reshape", None)
    reference_shape = getattr(reference, "shape", None)
    if shape is None or not callable(reshape):
        if not _is_sequence(activation):
            return activation
        nested_shape = _nested_shape(activation)
        if len(nested_shape) < 4:
            return activation
        return _merge_nested_last_two_dims(activation)
    if len(shape) < 4:
        return activation
    hidden_size = int(shape[-2]) * int(shape[-1])
    if reference_shape is not None:
        hidden_size = int(reference_shape[-1])
    return activation.reshape(*shape[:-2], hidden_size)


def split_qkv_heads(activation: Any, model: Any, spec: ComponentHookSpec) -> Any:
    """Extract one component from a joint QKV projection and split it into heads."""
    component = _attention_base_component(spec.component)
    q_heads = head_count_for_component(model, "q")
    kv_heads = head_count_for_component(model, "k")
    if spec.qkv_layout == "interleaved":
        return split_interleaved_qkv_heads(
            activation,
            component,
            q_heads=q_heads,
            kv_heads=kv_heads,
        )
    q_slice, k_slice, v_slice = split_qkv_slices(activation, q_heads=q_heads, kv_heads=kv_heads)
    component_slice = {"q": q_slice, "k": k_slice, "v": v_slice}[component]
    return split_heads(component_slice, q_heads if component == "q" else kv_heads)


def merge_qkv_heads(
    activation: Any,
    reference: Any,
    model: Any,
    spec: ComponentHookSpec,
) -> Any:
    """Replace one split-head component in a raw joint QKV projection tensor."""
    component = _attention_base_component(spec.component)
    q_heads = head_count_for_component(model, "q")
    kv_heads = head_count_for_component(model, "k")
    if spec.qkv_layout == "interleaved":
        return merge_interleaved_qkv_heads(
            activation,
            reference,
            component,
            q_heads=q_heads,
            kv_heads=kv_heads,
        )
    q_slice, k_slice, v_slice = split_qkv_slices(reference, q_heads=q_heads, kv_heads=kv_heads)
    component_slice = {"q": q_slice, "k": k_slice, "v": v_slice}[component]
    merged_component = merge_heads(activation, component_slice)
    patched = clone_tensor_like(reference)
    target = {"q": 0, "k": 1, "v": 2}[component]
    start, stop = split_qkv_slice_bounds(reference, q_heads=q_heads, kv_heads=kv_heads)[target]
    if getattr(patched, "shape", None) is None:
        return _replace_nested_last_dim_slice(patched, start, stop, merged_component)
    patched[..., start:stop] = merged_component
    return patched


def split_qkv_slices(activation: Any, *, q_heads: int, kv_heads: int) -> tuple[Any, Any, Any]:
    bounds = split_qkv_slice_bounds(activation, q_heads=q_heads, kv_heads=kv_heads)
    if getattr(activation, "shape", None) is None:
        return tuple(_slice_nested_last_dim(activation, start, stop) for start, stop in bounds)
    return tuple(activation[..., start:stop] for start, stop in bounds)


def split_qkv_slice_bounds(
    activation: Any,
    *,
    q_heads: int,
    kv_heads: int,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    shape = getattr(activation, "shape", None)
    total_heads = q_heads + 2 * kv_heads
    if shape is None:
        if not _is_sequence(activation):
            raise ValueError("Cannot split a joint QKV activation without a shape.")
        nested_shape = _nested_shape(activation)
        if not nested_shape:
            raise ValueError("Cannot split a joint QKV activation without a shape.")
        hidden_size = nested_shape[-1]
    else:
        hidden_size = int(shape[-1])
    if total_heads <= 0 or hidden_size % total_heads != 0:
        raise ValueError(
            "Cannot split joint QKV activation with final dimension "
            f"{hidden_size} into q_heads={q_heads}, kv_heads={kv_heads}."
        )
    head_dim = hidden_size // total_heads
    q_stop = q_heads * head_dim
    k_stop = q_stop + kv_heads * head_dim
    v_stop = k_stop + kv_heads * head_dim
    return ((0, q_stop), (q_stop, k_stop), (k_stop, v_stop))


def split_interleaved_qkv_heads(
    activation: Any,
    component: str,
    *,
    q_heads: int,
    kv_heads: int,
) -> Any:
    qkv = interleaved_qkv_view(activation, q_heads=q_heads, kv_heads=kv_heads)
    component_index = {"q": 0, "k": 1, "v": 2}[component]
    if _is_sequence(qkv):
        if q_heads != kv_heads and component_index in {1, 2}:
            offset = -2 if component == "k" else -1
            return _select_nested_penultimate_dim(qkv, offset)
        if q_heads != kv_heads:
            q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
            return _merge_nested_grouped_query_heads(qkv, q_per_group)
        return _select_nested_penultimate_dim(qkv, component_index)
    if q_heads != kv_heads and component_index in {1, 2}:
        offset = -2 if component == "k" else -1
        return qkv[..., offset, :]
    if q_heads != kv_heads:
        q_per_group = q_heads // kv_heads
        return qkv[..., :-2, :].reshape(*activation.shape[:-1], kv_heads * q_per_group, -1)
    return qkv[..., component_index, :]


def merge_interleaved_qkv_heads(
    activation: Any,
    reference: Any,
    component: str,
    *,
    q_heads: int,
    kv_heads: int,
) -> Any:
    qkv = clone_tensor_like(interleaved_qkv_view(reference, q_heads=q_heads, kv_heads=kv_heads))
    component_index = {"q": 0, "k": 1, "v": 2}[component]
    if _is_sequence(qkv):
        if q_heads != kv_heads and component_index in {1, 2}:
            offset = -2 if component == "k" else -1
            return _flatten_nested_interleaved_qkv(
                _replace_nested_penultimate_dim(qkv, offset, activation)
            )
        if q_heads != kv_heads:
            q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
            grouped_activation = _split_nested_grouped_query_heads(
                activation,
                kv_heads,
                q_per_group,
            )
            return _flatten_nested_interleaved_qkv(
                _replace_nested_grouped_query_heads(qkv, grouped_activation, q_per_group)
            )
        return _flatten_nested_interleaved_qkv(
            _replace_nested_penultimate_dim(qkv, component_index, activation)
        )
    if q_heads != kv_heads and component_index in {1, 2}:
        offset = -2 if component == "k" else -1
        qkv[..., offset, :] = activation
    elif q_heads != kv_heads:
        q_per_group = q_heads // kv_heads
        qkv[..., :-2, :] = activation.reshape(*qkv.shape[:-3], kv_heads, q_per_group, -1)
    else:
        qkv[..., component_index, :] = activation
    return qkv.reshape(*reference.shape)


def interleaved_qkv_view(activation: Any, *, q_heads: int, kv_heads: int) -> Any:
    shape = getattr(activation, "shape", None)
    reshape = getattr(activation, "reshape", None)
    if shape is None or not callable(reshape):
        if not _is_sequence(activation):
            return activation
        nested_shape = _nested_shape(activation)
        if not nested_shape:
            return activation
        hidden_size = nested_shape[-1]
        if q_heads == kv_heads:
            total_heads = q_heads
            if total_heads <= 0 or hidden_size % (3 * total_heads) != 0:
                raise ValueError(
                    "Cannot split interleaved QKV activation with final dimension "
                    f"{hidden_size} into {total_heads} heads."
                )
            head_dim = hidden_size // (3 * total_heads)
            return _reshape_nested_last_dim(activation, total_heads, 3, head_dim)

        total_groups = q_heads + 2 * kv_heads
        if total_groups <= 0 or hidden_size % total_groups != 0:
            raise ValueError(
                "Cannot split grouped interleaved QKV activation with final dimension "
                f"{hidden_size}, q_heads={q_heads}, kv_heads={kv_heads}."
            )
        q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
        head_dim = hidden_size // total_groups
        return _reshape_nested_last_dim(activation, kv_heads, q_per_group + 2, head_dim)
    hidden_size = int(shape[-1])
    if q_heads == kv_heads:
        total_heads = q_heads
        if total_heads <= 0 or hidden_size % (3 * total_heads) != 0:
            raise ValueError(
                "Cannot split interleaved QKV activation with final dimension "
                f"{hidden_size} into {total_heads} heads."
            )
        head_dim = hidden_size // (3 * total_heads)
        return activation.reshape(*shape[:-1], total_heads, 3, head_dim)

    total_groups = q_heads + 2 * kv_heads
    if total_groups <= 0 or hidden_size % total_groups != 0:
        raise ValueError(
            "Cannot split grouped interleaved QKV activation with final dimension "
            f"{hidden_size}, q_heads={q_heads}, kv_heads={kv_heads}."
        )
    q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
    head_dim = hidden_size // total_groups
    return activation.reshape(*shape[:-1], kv_heads, q_per_group + 2, head_dim)


def clone_tensor_like(value: Any) -> Any:
    clone = getattr(value, "clone", None)
    if callable(clone):
        return clone()
    copy = getattr(value, "copy", None)
    if callable(copy):
        return copy()
    return value


def _split_nested_last_dim(value: Any, n_heads: int) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 1:
        head_dim = shape[0] // n_heads
        return [
            list(value[head_index * head_dim : (head_index + 1) * head_dim])
            for head_index in range(n_heads)
        ]
    return [_split_nested_last_dim(item, n_heads) for item in value]


def _merge_nested_last_two_dims(value: Any) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 2:
        merged: list[Any] = []
        for item in value:
            merged.extend(item)
        return merged
    return [_merge_nested_last_two_dims(item) for item in value]


def _slice_nested_last_dim(value: Any, start: int, stop: int) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 1:
        return list(value[start:stop])
    return [_slice_nested_last_dim(item, start, stop) for item in value]


def _replace_nested_last_dim_slice(value: Any, start: int, stop: int, replacement: Any) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 1:
        return [*value[:start], *replacement, *value[stop:]]
    return [
        _replace_nested_last_dim_slice(item, start, stop, replacement_item)
        for item, replacement_item in zip(value, replacement, strict=True)
    ]


def _reshape_nested_last_dim(value: Any, *dims: int) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 1:
        values = list(value)
        return _reshape_flat_list(values, dims)
    return [_reshape_nested_last_dim(item, *dims) for item in value]


def _reshape_flat_list(values: list[Any], dims: tuple[int, ...]) -> Any:
    if not dims:
        if len(values) != 1:
            raise ValueError("Cannot reshape list: scalar target has multiple values.")
        return values[0]
    dim = dims[0]
    if dim <= 0:
        raise ValueError(f"Cannot reshape list with non-positive dimension {dim}.")
    if len(dims) == 1:
        if len(values) != dim:
            raise ValueError(f"Cannot reshape {len(values)} values into shape {dims}.")
        return list(values)
    stride = _product(dims[1:])
    if len(values) != dim * stride:
        raise ValueError(f"Cannot reshape {len(values)} values into shape {dims}.")
    return [
        _reshape_flat_list(values[index * stride : (index + 1) * stride], dims[1:])
        for index in range(dim)
    ]


def _select_nested_penultimate_dim(value: Any, index: int) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 2:
        return list(value[index])
    return [_select_nested_penultimate_dim(item, index) for item in value]


def _replace_nested_penultimate_dim(value: Any, index: int, replacement: Any) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 2:
        replaced = [list(item) for item in value]
        replaced[index] = list(replacement)
        return replaced
    return [
        _replace_nested_penultimate_dim(item, index, replacement_item)
        for item, replacement_item in zip(value, replacement, strict=True)
    ]


def _merge_nested_grouped_query_heads(value: Any, q_per_group: int) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 3:
        merged: list[Any] = []
        for group in value:
            for head in group[:q_per_group]:
                merged.append(list(head))
        return merged
    return [_merge_nested_grouped_query_heads(item, q_per_group) for item in value]


def _split_nested_grouped_query_heads(value: Any, kv_heads: int, q_per_group: int) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 2:
        expected_heads = kv_heads * q_per_group
        if len(value) != expected_heads:
            raise ValueError(f"Expected {expected_heads} query heads, got {len(value)}.")
        return [
            [list(head) for head in value[group * q_per_group : (group + 1) * q_per_group]]
            for group in range(kv_heads)
        ]
    return [_split_nested_grouped_query_heads(item, kv_heads, q_per_group) for item in value]


def _replace_nested_grouped_query_heads(value: Any, replacement: Any, q_per_group: int) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 3:
        return [
            [*replacement_group, *group[q_per_group:]]
            for group, replacement_group in zip(value, replacement, strict=True)
        ]
    return [
        _replace_nested_grouped_query_heads(item, replacement_item, q_per_group)
        for item, replacement_item in zip(value, replacement, strict=True)
    ]


def _flatten_nested_interleaved_qkv(value: Any) -> Any:
    shape = _nested_shape(value)
    if len(shape) == 3:
        flattened: list[Any] = []
        for group in value:
            for component in group:
                flattened.extend(component)
        return flattened
    return [_flatten_nested_interleaved_qkv(item) for item in value]


def _product(values: tuple[int, ...]) -> int:
    result = 1
    for value in values:
        result *= value
    return result


def _reshape_attention_weight_list(
    weight: Sequence[Any],
    *,
    component: str,
    n_heads: int,
    packed_axis: int | None,
) -> Any:
    shape = _nested_shape(weight)
    if len(shape) != 2:
        raise ValueError(f"Cannot reshape attention weight for component {component!r}.")
    axis = packed_axis
    if axis is None:
        axis = infer_attention_weight_packed_axis(weight, n_heads=n_heads)
    if axis not in {0, 1}:
        raise ValueError(f"packed_axis must be 0, 1, or None, got {packed_axis!r}.")
    packed_dim = shape[axis]
    other_dim = shape[1 - axis]
    if n_heads <= 0 or packed_dim % n_heads != 0:
        raise ValueError(
            f"Cannot split packed dimension {packed_dim} into {n_heads} heads for {component!r}."
        )
    head_dim = packed_dim // n_heads
    if component in {"q", "k", "v"}:
        if axis == 0:
            return _permute_nested(
                _reshape_flat_list(_flatten_nested(weight), (n_heads, head_dim, other_dim)),
                (0, 2, 1),
            )
        return _permute_nested(
            _reshape_flat_list(_flatten_nested(weight), (other_dim, n_heads, head_dim)),
            (1, 0, 2),
        )
    if component == "z":
        if axis == 0:
            return _reshape_flat_list(_flatten_nested(weight), (n_heads, head_dim, other_dim))
        return _permute_nested(
            _reshape_flat_list(_flatten_nested(weight), (other_dim, n_heads, head_dim)),
            (1, 2, 0),
        )
    raise ValueError(f"Unsupported attention weight component {component!r}.")


def _reshape_joint_qkv_attention_weight_list(
    weight: Sequence[Any],
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
    packed_axis: int | None,
) -> Any:
    shape = _nested_shape(weight)
    if len(shape) != 2:
        raise ValueError(f"Cannot reshape joint QKV weight for component {component!r}.")
    if component not in {"q", "k", "v"}:
        raise ValueError(f"Joint QKV weights only expose q/k/v, got {component!r}.")
    axis = packed_axis
    if axis is None:
        axis = infer_qkv_weight_packed_axis(weight, q_heads=q_heads, kv_heads=kv_heads)
    if axis == 0:
        component_weight, n_heads = extract_qkv_weight_rows(
            weight,
            component=component,
            q_heads=q_heads,
            kv_heads=kv_heads,
            qkv_layout=qkv_layout,
        )
        return _reshape_attention_weight_list(
            component_weight,
            component=component,
            n_heads=n_heads,
            packed_axis=0,
        )
    if axis == 1:
        component_weight, n_heads = extract_qkv_weight_columns(
            weight,
            component=component,
            q_heads=q_heads,
            kv_heads=kv_heads,
            qkv_layout=qkv_layout,
        )
        return _reshape_attention_weight_list(
            component_weight,
            component=component,
            n_heads=n_heads,
            packed_axis=1,
        )
    raise ValueError(f"packed_axis must be 0, 1, or None, got {packed_axis!r}.")


def _flatten_nested(value: Any) -> list[Any]:
    if _is_sequence(value):
        flattened: list[Any] = []
        for item in value:
            flattened.extend(_flatten_nested(item))
        return flattened
    return [value]


def _permute_nested(value: Any, order: tuple[int, ...]) -> Any:
    shape = _nested_shape(value)
    if len(shape) != len(order):
        raise ValueError(f"Cannot permute shape {shape} with order {order}.")
    output_shape = tuple(shape[axis] for axis in order)
    inverse_order = tuple(order.index(axis) for axis in range(len(order)))
    return _build_nested_from_shape(
        output_shape,
        lambda output_index: _get_nested_index(
            value,
            tuple(output_index[inverse_order[axis]] for axis in range(len(order))),
        ),
    )


def _build_nested_from_shape(
    shape: tuple[int, ...], value_fn: Callable[[tuple[int, ...]], Any]
) -> Any:
    def build(prefix: tuple[int, ...], remaining: tuple[int, ...]) -> Any:
        if not remaining:
            return value_fn(prefix)
        return [build((*prefix, index), remaining[1:]) for index in range(remaining[0])]

    return build((), shape)


def _get_nested_index(value: Any, index: tuple[int, ...]) -> Any:
    current = value
    for axis_index in index:
        current = current[axis_index]
    return current


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _weight_shape(weight: Any) -> tuple[int, int]:
    shape = getattr(weight, "shape", None)
    if shape is not None:
        return int(shape[0]), int(shape[1])
    nested_shape = _nested_shape(weight)
    if len(nested_shape) != 2:
        raise ValueError(f"Expected a rank-2 weight matrix, got shape {nested_shape}.")
    return nested_shape


def _select_nested_axis(value: Any, axis: int, index: int) -> Any:
    if axis == 0:
        return value[index]
    return [_select_nested_axis(item, axis - 1, index) for item in value]


def _select_nested_axis_slice(value: Any, axis: int, index: slice) -> Any:
    if axis == 0:
        return value[index]
    return [_select_nested_axis_slice(item, axis - 1, index) for item in value]


def _flatten_nested_interleaved_qkv_weight_rows(value: Any) -> list[Any]:
    shape = _nested_shape(value)
    if len(shape) == 3:
        rows: list[Any] = []
        for head_group in value:
            rows.extend([list(row) for row in head_group])
        return rows
    if len(shape) == 4:
        rows = []
        for group in value:
            for head_group in group:
                rows.extend([list(row) for row in head_group])
        return rows
    return [list(row) for row in value]


def _flatten_nested_last_dims(value: Any) -> list[Any]:
    shape = _nested_shape(value)
    if len(shape) == 3:
        return [_flatten_nested(item) for item in value]
    if len(shape) == 4:
        return [_flatten_nested(item) for item in value]
    return value


def head_count_for_component(model: Any, component: str) -> int:
    """Read the configured attention head count for one component."""
    component = _attention_base_component(component)
    if component in {"k", "v"}:
        n_key_value_heads = key_value_head_count(model)
        if n_key_value_heads is not None:
            return n_key_value_heads
    n_heads = attention_head_count(model)
    if n_heads is not None:
        return n_heads
    config = getattr(model, "config", None)
    raise ValueError(
        f"Could not infer attention head count for component {component!r} "
        f"from {type(config).__name__}."
    )


def attention_head_count(model: Any) -> int | None:
    """Read the configured query/output attention head count."""
    config = _model_config(model)
    for name in ("num_attention_heads", "n_head", "n_heads", "num_heads"):
        value = _config_attr(config, name)
        if value is not None:
            return int(value)
    return None


def key_value_head_count(model: Any) -> int | None:
    """Read the configured key/value head count when it differs from query heads."""
    config = _model_config(model)
    if _is_falcon_multi_query_config(config):
        return 1
    for name in ("num_key_value_heads", "num_kv_heads", "n_head_kv"):
        value = _config_attr(config, name)
        if value is not None:
            return int(value)
    return None


def _is_falcon_multi_query_config(config: Any) -> bool:
    """Falcon MQA packs one shared K/V head even when num_kv_heads defaults to n_heads."""
    if str(_config_attr(config, "model_type", "")).lower() != "falcon":
        return False
    if bool(_config_attr(config, "new_decoder_architecture", False)):
        return False
    return bool(_config_attr(config, "multi_query", False))


def reshape_attention_weight(
    weight: Any,
    *,
    component: str,
    n_heads: int,
    packed_axis: int | None = 0,
) -> Any:
    """Convert HF linear weights to TransformerLens attention weight shapes."""
    component = _attention_base_component(component)
    shape = getattr(weight, "shape", None)
    reshape = getattr(weight, "reshape", None)
    if shape is None or not callable(reshape) or len(shape) != 2:
        if not _is_sequence(weight):
            raise ValueError(f"Cannot reshape attention weight for component {component!r}.")
        return _reshape_attention_weight_list(
            weight,
            component=component,
            n_heads=n_heads,
            packed_axis=packed_axis,
        )
    axis = packed_axis
    if axis is None:
        axis = infer_attention_weight_packed_axis(weight, n_heads=n_heads)
    if axis not in {0, 1}:
        raise ValueError(f"packed_axis must be 0, 1, or None, got {packed_axis!r}.")
    packed_dim = int(shape[axis])
    other_dim = int(shape[1 - axis])
    if n_heads <= 0 or packed_dim % n_heads != 0:
        raise ValueError(
            f"Cannot split packed dimension {packed_dim} into {n_heads} heads for {component!r}."
        )
    head_dim = packed_dim // n_heads
    if component in {"q", "k", "v"}:
        if axis == 0:
            return weight.reshape(n_heads, head_dim, other_dim).permute(0, 2, 1)
        return weight.reshape(other_dim, n_heads, head_dim).permute(1, 0, 2)
    if component == "z":
        if axis == 0:
            return weight.reshape(n_heads, head_dim, other_dim)
        return weight.reshape(other_dim, n_heads, head_dim).permute(1, 2, 0)
    raise ValueError(f"Unsupported attention weight component {component!r}.")


def reshape_attention_bias(
    bias: Any,
    *,
    component: str,
    n_heads: int,
) -> Any:
    """Convert a packed projection bias to TransformerLens attention bias shape."""
    component = _attention_base_component(component)
    if component == "z":
        return bias
    shape = getattr(bias, "shape", None)
    reshape = getattr(bias, "reshape", None)
    if shape is None or not callable(reshape):
        if not _is_sequence(bias):
            return bias
        if n_heads <= 0 or len(bias) % n_heads != 0:
            raise ValueError(
                f"Cannot split attention bias of length {len(bias)} into {n_heads} heads."
            )
        head_dim = len(bias) // n_heads
        return [
            list(bias[head_index * head_dim : (head_index + 1) * head_dim])
            for head_index in range(n_heads)
        ]
    if len(shape) == 2:
        return bias
    if len(shape) != 1:
        raise ValueError(f"Cannot reshape attention bias for component {component!r}.")
    if n_heads <= 0 or int(shape[0]) % n_heads != 0:
        raise ValueError(
            f"Cannot split attention bias of length {int(shape[0])} into {n_heads} heads."
        )
    return bias.reshape(n_heads, int(shape[0]) // n_heads)


def reshape_joint_qkv_attention_bias(
    bias: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
) -> Any:
    """Convert a joint QKV projection bias to TransformerLens attention bias shape."""
    component_bias, n_heads = extract_qkv_bias(
        bias,
        component=component,
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
    )
    return reshape_attention_bias(component_bias, component=component, n_heads=n_heads)


def extract_qkv_bias(
    bias: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
) -> tuple[Any, int]:
    shape = getattr(bias, "shape", None)
    length = int(shape[0]) if shape is not None else len(bias)
    total_heads = q_heads + 2 * kv_heads
    if total_heads <= 0 or length % total_heads != 0:
        raise ValueError(
            "Cannot split joint QKV bias with length "
            f"{length}, q_heads={q_heads}, kv_heads={kv_heads}."
        )
    head_dim = length // total_heads
    if qkv_layout == "split":
        bounds = qkv_weight_bounds(head_dim, q_heads=q_heads, kv_heads=kv_heads)
        start, stop = bounds[component]
        n_heads = q_heads if component == "q" else kv_heads
        return bias[start:stop], n_heads
    if qkv_layout == "interleaved":
        return extract_interleaved_qkv_bias(
            bias,
            component=component,
            head_dim=head_dim,
            q_heads=q_heads,
            kv_heads=kv_heads,
        )
    raise ValueError(f"Unsupported QKV layout {qkv_layout!r}.")


def extract_interleaved_qkv_bias(
    bias: Any,
    *,
    component: str,
    head_dim: int,
    q_heads: int,
    kv_heads: int,
) -> tuple[Any, int]:
    if _is_sequence(bias):
        if q_heads == kv_heads:
            component_index = {"q": 0, "k": 1, "v": 2}[component]
            view = _reshape_flat_list(list(bias), (q_heads, 3, head_dim))
            return _flatten_nested(_select_nested_axis(view, 1, component_index)), q_heads

        q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
        view = _reshape_flat_list(list(bias), (kv_heads, q_per_group + 2, head_dim))
        if component == "q":
            return _flatten_nested(
                _select_nested_axis_slice(view, 1, slice(0, q_per_group))
            ), q_heads
        offset = -2 if component == "k" else -1
        return _flatten_nested(_select_nested_axis(view, 1, offset)), kv_heads
    if q_heads == kv_heads:
        component_index = {"q": 0, "k": 1, "v": 2}[component]
        view = bias.reshape(q_heads, 3, head_dim)
        return view[:, component_index, :].reshape(q_heads * head_dim), q_heads

    q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
    view = bias.reshape(kv_heads, q_per_group + 2, head_dim)
    if component == "q":
        return view[:, :q_per_group, :].reshape(q_heads * head_dim), q_heads
    offset = -2 if component == "k" else -1
    return view[:, offset, :].reshape(kv_heads * head_dim), kv_heads


def zeros_for_attention_bias(model: Any, component: str) -> Any:
    """Return a zero attention bias with the TransformerLens shape for one component."""
    component = _attention_base_component(component)
    n_heads = head_count_for_component(model, component) if component != "z" else None
    d_model = _model_hidden_size(model)
    if d_model is None:
        raise ValueError(f"Could not infer hidden size for b_{component.upper()}.")
    if component == "z":
        return _zeros_vector(d_model, model)
    d_head = attention_head_dim(model)
    if n_heads is None or n_heads <= 0 or d_head is None or d_head <= 0:
        raise ValueError(
            f"Could not infer head dimension for b_{component.upper()} with "
            f"d_model={d_model}, n_heads={n_heads}, d_head={d_head}."
        )
    return _zeros_matrix(n_heads, d_head, model)


def _model_hidden_size(model: Any) -> int | None:
    config = _model_config(model)
    for name in ("hidden_size", "n_embd", "d_model", "dim"):
        value = _config_attr(config, name)
        if value is not None:
            return int(value)
    return None


def attention_head_dim(model: Any) -> int | None:
    """Read the per-query-head dimension used by q/k/v projections."""
    config = _model_config(model)
    for name in ("head_dim", "d_head", "d_kv", "kv_channels"):
        value = _config_attr(config, name)
        if value is not None:
            return int(value)
    d_model = _model_hidden_size(model)
    n_heads = attention_head_count(model)
    if d_model is not None and n_heads:
        return d_model // n_heads
    return None


def _model_config(model: Any) -> Any:
    config = _config_attr(model, "config")
    return _config_attr(config, "text_config") or _config_attr(config, "language_config") or config


def _config_attr(config: Any, name: str, default: Any = None) -> Any:
    if isinstance(config, Mapping):
        return config.get(name, default)
    return getattr(config, name, default)


def _zeros_vector(length: int, model: Any) -> Any:
    try:
        import torch

        return torch.zeros(length)
    except ImportError:
        _ = model
        return [0 for _ in range(length)]


def _zeros_matrix(rows: int, cols: int, model: Any) -> Any:
    try:
        import torch

        return torch.zeros(rows, cols)
    except ImportError:
        _ = model
        return [[0 for _ in range(cols)] for _ in range(rows)]


def preferred_attention_weight_packed_axis(
    module: Any,
    *,
    architecture: str,
    component: str,
) -> int | None:
    """Return the likely packed axis for architecture-specific attention weights."""
    module_type = type(module).__name__.lower()
    if component == "z":
        if architecture == "gpt2_decoder" or module_type == "conv1d":
            return 0
        return 1
    if module_type == "conv1d":
        return 1
    return 0


def infer_attention_weight_packed_axis(weight: Any, *, n_heads: int) -> int:
    shape = getattr(weight, "shape", None)
    if shape is None or len(shape) != 2:
        raise ValueError("Cannot infer attention weight axis without a 2D shape.")
    packed_on_rows = int(shape[0]) % n_heads == 0
    packed_on_columns = int(shape[1]) % n_heads == 0
    if packed_on_rows and not packed_on_columns:
        return 0
    if packed_on_columns and not packed_on_rows:
        return 1
    if packed_on_rows:
        return 0
    raise ValueError(
        f"Cannot infer attention weight axis from shape {tuple(shape)} with n_heads={n_heads}."
    )


def reshape_joint_qkv_attention_weight(
    weight: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
    packed_axis: int | None = None,
) -> Any:
    """Convert joint QKV projection weights to TransformerLens attention shapes."""
    shape = getattr(weight, "shape", None)
    reshape = getattr(weight, "reshape", None)
    if shape is None or not callable(reshape) or len(shape) != 2:
        if not _is_sequence(weight):
            raise ValueError(f"Cannot reshape joint QKV weight for component {component!r}.")
        return _reshape_joint_qkv_attention_weight_list(
            weight,
            component=component,
            q_heads=q_heads,
            kv_heads=kv_heads,
            qkv_layout=qkv_layout,
            packed_axis=packed_axis,
        )
    if component not in {"q", "k", "v"}:
        raise ValueError(f"Joint QKV weights only expose q/k/v, got {component!r}.")

    axis = packed_axis
    if axis is None:
        axis = infer_qkv_weight_packed_axis(weight, q_heads=q_heads, kv_heads=kv_heads)
    if axis == 0:
        return reshape_joint_qkv_weight_packed_rows(
            weight,
            component=component,
            q_heads=q_heads,
            kv_heads=kv_heads,
            qkv_layout=qkv_layout,
        )
    if axis == 1:
        return reshape_joint_qkv_weight_packed_columns(
            weight,
            component=component,
            q_heads=q_heads,
            kv_heads=kv_heads,
            qkv_layout=qkv_layout,
        )
    raise ValueError(f"packed_axis must be 0, 1, or None, got {packed_axis!r}.")


def preferred_qkv_weight_packed_axis(module: Any, *, architecture: str) -> int | None:
    """Return the likely packed axis for architecture-specific joint QKV weights."""
    if architecture == "gpt2_decoder":
        return 1
    module_type = type(module).__name__.lower()
    if module_type == "conv1d":
        return 1
    return None


def infer_qkv_weight_packed_axis(weight: Any, *, q_heads: int, kv_heads: int) -> int:
    shape = getattr(weight, "shape", None)
    if shape is None or len(shape) != 2:
        raise ValueError("Cannot infer packed QKV weight axis without a 2D shape.")
    total_heads = q_heads + 2 * kv_heads
    packed_on_rows = int(shape[0]) % total_heads == 0
    packed_on_columns = int(shape[1]) % total_heads == 0
    if packed_on_rows and not packed_on_columns:
        return 0
    if packed_on_columns and not packed_on_rows:
        return 1
    if packed_on_rows:
        return 0
    raise ValueError(
        "Cannot infer packed QKV weight axis from shape "
        f"{tuple(shape)} with q_heads={q_heads}, kv_heads={kv_heads}."
    )


def reshape_joint_qkv_weight_packed_rows(
    weight: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
) -> Any:
    """Handle linear-style joint weights shaped `[qkv_out, d_model]`."""
    packed_dim = int(weight.shape[0])
    d_model = int(weight.shape[1])
    component_weight, n_heads = extract_qkv_weight_rows(
        weight,
        component=component,
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
    )
    head_dim = packed_dim // (q_heads + 2 * kv_heads)
    return component_weight.reshape(n_heads, head_dim, d_model).permute(0, 2, 1)


def reshape_joint_qkv_weight_packed_columns(
    weight: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
) -> Any:
    """Handle Conv1D-style joint weights shaped `[d_model, qkv_out]`."""
    packed_dim = int(weight.shape[1])
    d_model = int(weight.shape[0])
    component_weight, n_heads = extract_qkv_weight_columns(
        weight,
        component=component,
        q_heads=q_heads,
        kv_heads=kv_heads,
        qkv_layout=qkv_layout,
    )
    head_dim = packed_dim // (q_heads + 2 * kv_heads)
    return component_weight.reshape(d_model, n_heads, head_dim).permute(1, 0, 2)


def extract_qkv_weight_rows(
    weight: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
) -> tuple[Any, int]:
    total_heads = q_heads + 2 * kv_heads
    weight_shape = _weight_shape(weight)
    packed_dim = int(weight_shape[0])
    if total_heads <= 0 or packed_dim % total_heads != 0:
        raise ValueError(
            "Cannot split joint QKV weight rows with output dimension "
            f"{packed_dim}, q_heads={q_heads}, kv_heads={kv_heads}."
        )
    head_dim = packed_dim // total_heads
    if qkv_layout == "split":
        bounds = qkv_weight_bounds(head_dim, q_heads=q_heads, kv_heads=kv_heads)
        start, stop = bounds[component]
        n_heads = q_heads if component == "q" else kv_heads
        if _is_sequence(weight):
            return [list(row) for row in weight[start:stop]], n_heads
        return weight[start:stop, :], n_heads
    if qkv_layout == "interleaved":
        return extract_interleaved_qkv_weight_rows(
            weight,
            component=component,
            head_dim=head_dim,
            q_heads=q_heads,
            kv_heads=kv_heads,
        )
    raise ValueError(f"Unsupported QKV layout {qkv_layout!r}.")


def extract_qkv_weight_columns(
    weight: Any,
    *,
    component: str,
    q_heads: int,
    kv_heads: int,
    qkv_layout: QKVLayout,
) -> tuple[Any, int]:
    total_heads = q_heads + 2 * kv_heads
    weight_shape = _weight_shape(weight)
    packed_dim = int(weight_shape[1])
    if total_heads <= 0 or packed_dim % total_heads != 0:
        raise ValueError(
            "Cannot split joint QKV weight columns with output dimension "
            f"{packed_dim}, q_heads={q_heads}, kv_heads={kv_heads}."
        )
    head_dim = packed_dim // total_heads
    if qkv_layout == "split":
        bounds = qkv_weight_bounds(head_dim, q_heads=q_heads, kv_heads=kv_heads)
        start, stop = bounds[component]
        n_heads = q_heads if component == "q" else kv_heads
        if _is_sequence(weight):
            return [list(row[start:stop]) for row in weight], n_heads
        return weight[:, start:stop], n_heads
    if qkv_layout == "interleaved":
        return extract_interleaved_qkv_weight_columns(
            weight,
            component=component,
            head_dim=head_dim,
            q_heads=q_heads,
            kv_heads=kv_heads,
        )
    raise ValueError(f"Unsupported QKV layout {qkv_layout!r}.")


def qkv_weight_bounds(
    head_dim: int,
    *,
    q_heads: int,
    kv_heads: int,
) -> dict[str, tuple[int, int]]:
    q_stop = q_heads * head_dim
    k_stop = q_stop + kv_heads * head_dim
    v_stop = k_stop + kv_heads * head_dim
    return {"q": (0, q_stop), "k": (q_stop, k_stop), "v": (k_stop, v_stop)}


def extract_interleaved_qkv_weight_rows(
    weight: Any,
    *,
    component: str,
    head_dim: int,
    q_heads: int,
    kv_heads: int,
) -> tuple[Any, int]:
    d_model = int(_weight_shape(weight)[1])
    if _is_sequence(weight):
        if q_heads == kv_heads:
            component_index = {"q": 0, "k": 1, "v": 2}[component]
            view = _reshape_flat_list(_flatten_nested(weight), (q_heads, 3, head_dim, d_model))
            return _flatten_nested_interleaved_qkv_weight_rows(
                _select_nested_axis(view, 1, component_index)
            ), q_heads

        q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
        view = _reshape_flat_list(
            _flatten_nested(weight),
            (kv_heads, q_per_group + 2, head_dim, d_model),
        )
        if component == "q":
            return _flatten_nested_interleaved_qkv_weight_rows(
                _select_nested_axis_slice(view, 1, slice(0, q_per_group))
            ), q_heads
        offset = -2 if component == "k" else -1
        return _flatten_nested_interleaved_qkv_weight_rows(
            _select_nested_axis(view, 1, offset)
        ), kv_heads
    if q_heads == kv_heads:
        component_index = {"q": 0, "k": 1, "v": 2}[component]
        view = weight.reshape(q_heads, 3, head_dim, d_model)
        return view[:, component_index, :, :].reshape(q_heads * head_dim, d_model), q_heads

    q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
    view = weight.reshape(kv_heads, q_per_group + 2, head_dim, d_model)
    if component == "q":
        return view[:, :q_per_group, :, :].reshape(q_heads * head_dim, d_model), q_heads
    offset = -2 if component == "k" else -1
    return view[:, offset, :, :].reshape(kv_heads * head_dim, d_model), kv_heads


def extract_interleaved_qkv_weight_columns(
    weight: Any,
    *,
    component: str,
    head_dim: int,
    q_heads: int,
    kv_heads: int,
) -> tuple[Any, int]:
    d_model = int(_weight_shape(weight)[0])
    if _is_sequence(weight):
        if q_heads == kv_heads:
            component_index = {"q": 0, "k": 1, "v": 2}[component]
            view = _reshape_flat_list(_flatten_nested(weight), (d_model, q_heads, 3, head_dim))
            return _flatten_nested_last_dims(_select_nested_axis(view, 2, component_index)), q_heads

        q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
        view = _reshape_flat_list(
            _flatten_nested(weight),
            (d_model, kv_heads, q_per_group + 2, head_dim),
        )
        if component == "q":
            return _flatten_nested_last_dims(
                _select_nested_axis_slice(view, 2, slice(0, q_per_group))
            ), q_heads
        offset = -2 if component == "k" else -1
        return _flatten_nested_last_dims(_select_nested_axis(view, 2, offset)), kv_heads
    if q_heads == kv_heads:
        component_index = {"q": 0, "k": 1, "v": 2}[component]
        view = weight.reshape(d_model, q_heads, 3, head_dim)
        return view[:, :, component_index, :].reshape(d_model, q_heads * head_dim), q_heads

    q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
    view = weight.reshape(d_model, kv_heads, q_per_group + 2, head_dim)
    if component == "q":
        return view[:, :, :q_per_group, :].reshape(d_model, q_heads * head_dim), q_heads
    offset = -2 if component == "k" else -1
    return view[:, :, offset, :].reshape(d_model, kv_heads * head_dim), kv_heads


def qkv_group_size(*, q_heads: int, kv_heads: int) -> int:
    if kv_heads <= 0 or q_heads % kv_heads != 0:
        raise ValueError(
            f"Grouped QKV requires q_heads to be a multiple of kv_heads, got "
            f"q_heads={q_heads}, kv_heads={kv_heads}."
        )
    return q_heads // kv_heads


def _register_attention_softmax_hook(
    module: Any,
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
    spec: ComponentHookSpec,
    *,
    prepend: bool = False,
) -> Any:
    try:
        import torch
        import torch.nn.functional as functional
    except ImportError as exc:
        raise ImportError(
            "Attention score instrumentation requires torch. "
            "Install model dependencies with `pip install -e '.[models]'`."
        ) from exc

    state = getattr(module, _ATTENTION_SOFTMAX_STATE_ATTR, None)
    if state is None:
        original_forward = module.forward
        state = _AttentionSoftmaxHookState(module=module, original_forward=original_forward)

        def wrapped_forward(*args: Any, **kwargs: Any) -> Any:
            active_records = list(state.records)
            if not active_records:
                return state.original_forward(*args, **kwargs)

            original_torch_softmax = torch.softmax
            original_functional_softmax = functional.softmax
            captured = False

            def make_instrumented_softmax(
                original_softmax: Callable[..., Any],
            ) -> Callable[..., Any]:
                def instrumented_softmax(
                    input_tensor: Any,
                    *softmax_args: Any,
                    **softmax_kwargs: Any,
                ) -> Any:
                    nonlocal captured
                    if not _looks_like_attention_scores(input_tensor, softmax_args, softmax_kwargs):
                        return original_softmax(input_tensor, *softmax_args, **softmax_kwargs)
                    captured = True
                    scores = input_tensor
                    for record in active_records:
                        if record.spec.value != "attention_scores":
                            continue
                        patched_scores = call_component_hook(
                            record.hook_fn,
                            activation=scores,
                            component_ref=record.component_ref,
                            architecture=record.architecture,
                            hook_context=record.hook_context,
                        )
                        if patched_scores is not None:
                            scores = patched_scores

                    pattern = original_softmax(scores, *softmax_args, **softmax_kwargs)
                    for record in active_records:
                        if record.spec.value != "attention_pattern":
                            continue
                        patched_pattern = call_component_hook(
                            record.hook_fn,
                            activation=pattern,
                            component_ref=record.component_ref,
                            architecture=record.architecture,
                            hook_context=record.hook_context,
                        )
                        if patched_pattern is not None:
                            pattern = patched_pattern
                    return pattern

                return instrumented_softmax

            torch.softmax = make_instrumented_softmax(original_torch_softmax)
            functional.softmax = make_instrumented_softmax(original_functional_softmax)
            try:
                output = state.original_forward(*args, **kwargs)
            finally:
                torch.softmax = original_torch_softmax
                functional.softmax = original_functional_softmax

            if not captured:
                components = ", ".join(
                    record.component_ref.safelens_name for record in active_records
                )
                raise RuntimeError(
                    f"Attention instrumentation for {components!r} did not observe an "
                    "attention-shaped Python torch.softmax call. Use an eager attention "
                    "implementation or a model adapter with explicit attention forward "
                    "instrumentation."
                )
            return output

        state.wrapped_forward = wrapped_forward
        module.forward = wrapped_forward
        setattr(module, _ATTENTION_SOFTMAX_STATE_ATTR, state)

    record = _AttentionSoftmaxHookRecord(
        hook_fn=hook_fn,
        component_ref=component_ref,
        architecture=architecture,
        spec=spec,
        hook_context=ComponentHookContext(component_ref),
    )
    if prepend:
        state.records.insert(0, record)
    else:
        state.records.append(record)
    return _AttentionSoftmaxHookHandle(state, record)


def _looks_like_attention_scores(
    input_tensor: Any,
    softmax_args: tuple[Any, ...],
    softmax_kwargs: dict[str, Any],
) -> bool:
    ndim = getattr(input_tensor, "ndim", None)
    if ndim is None or int(ndim) < 4:
        return False
    dim = softmax_kwargs.get("dim")
    if dim is None and softmax_args:
        dim = softmax_args[0]
    if dim is None:
        return False
    try:
        dim_index = int(dim)
    except (TypeError, ValueError):
        return False
    return dim_index in {-1, int(ndim) - 1}


class _ForwardPatchHandle:
    def __init__(self, module: Any, original_forward: Any, wrapped_forward: Any) -> None:
        self._module = module
        self._original_forward = original_forward
        self._wrapped_forward = wrapped_forward
        self._removed = False

    def remove(self) -> None:
        if self._removed:
            return
        if getattr(self._module, "forward", None) is self._wrapped_forward:
            self._module.forward = self._original_forward
        self._removed = True


class _ComponentHookHandle:
    def __init__(self, handle: Any, hook_contexts: Sequence[ComponentHookContext]) -> None:
        self._handle = handle
        self.hook_contexts = tuple(hook_contexts)

    def remove(self) -> None:
        remove = getattr(self._handle, "remove", None)
        if callable(remove):
            remove()


class _CompositeComponentHookHandle:
    def __init__(self, handles: Sequence[Any]) -> None:
        self._handles = tuple(handles)

    def remove(self) -> None:
        for handle in self._handles:
            remove = getattr(handle, "remove", None)
            if callable(remove):
                remove()


@dataclass(eq=False)
class _AttentionSoftmaxHookRecord:
    hook_fn: HookFn
    component_ref: ComponentRef
    architecture: str
    spec: ComponentHookSpec
    hook_context: ComponentHookContext


@dataclass
class _AttentionSoftmaxHookState:
    module: Any
    original_forward: Any
    wrapped_forward: Any | None = None
    records: list[_AttentionSoftmaxHookRecord] = field(default_factory=list)


class _AttentionSoftmaxHookHandle:
    def __init__(
        self,
        state: _AttentionSoftmaxHookState,
        record: _AttentionSoftmaxHookRecord,
    ) -> None:
        self._state = state
        self._record = record
        self.hook_contexts = (record.hook_context,)
        self._removed = False

    def remove(self) -> None:
        if self._removed:
            return
        try:
            self._state.records.remove(self._record)
        except ValueError:
            pass
        if not self._state.records:
            if getattr(self._state.module, "forward", None) is self._state.wrapped_forward:
                self._state.module.forward = self._state.original_forward
                if getattr(self._state.module, _ATTENTION_SOFTMAX_STATE_ATTR, None) is self._state:
                    delattr(self._state.module, _ATTENTION_SOFTMAX_STATE_ATTR)
        self._removed = True


def _find_attention_pattern(
    value: Any,
    *,
    skip_kv_cache_sequences: bool = True,
) -> Any | None:
    if _looks_like_attention_pattern(value):
        return value
    if isinstance(value, dict):
        for key in ("attentions", "attention_weights", "attn_weights", "weights"):
            if key in value:
                found = _find_attention_pattern(value[key], skip_kv_cache_sequences=False)
                if found is not None:
                    return found
        for item in value.values():
            found = _find_attention_pattern(
                item,
                skip_kv_cache_sequences=skip_kv_cache_sequences,
            )
            if found is not None:
                return found
    if isinstance(value, tuple | list):
        if skip_kv_cache_sequences and _looks_like_key_value_cache_sequence(value):
            return None
        for item in reversed(value):
            if _looks_like_attention_pattern(item):
                return item
        for item in reversed(value):
            found = _find_attention_pattern(
                item,
                skip_kv_cache_sequences=skip_kv_cache_sequences,
            )
            if found is not None:
                return found
    return None


def _looks_like_attention_pattern(value: Any) -> bool:
    if hasattr(value, "shape"):
        return len(_nested_shape(value)) >= 4
    if isinstance(value, Mapping) or isinstance(value, str | bytes):
        return False
    if not _is_sequence(value):
        return False
    if not _contains_only_scalar_payloads(value):
        return False
    return len(_nested_shape(value)) >= 4


def _contains_only_scalar_payloads(value: Any) -> bool:
    if _is_scalar_payload(value):
        return True
    if isinstance(value, Mapping) or isinstance(value, str | bytes):
        return False
    if not _is_sequence(value):
        return False
    return all(_contains_only_scalar_payloads(item) for item in value)


def _looks_like_key_value_cache_sequence(value: Any) -> bool:
    if not isinstance(value, tuple | list) or len(value) not in {2, 4}:
        return False
    shapes = [_nested_shape(item) for item in value]
    if len(shapes) < 2 or any(len(shape) < 4 for shape in shapes[:2]):
        return False
    return shapes[0][:-1] == shapes[1][:-1]


def _find_attention_scores(value: Any) -> Any | None:
    if isinstance(value, dict):
        for key in ("attn_scores", "attention_scores", "scores"):
            if key in value:
                return value[key]
        for item in value.values():
            found = _find_attention_scores(item)
            if found is not None:
                return found
    if isinstance(value, tuple | list):
        for item in value:
            found = _find_attention_scores(item)
            if found is not None:
                return found
    return None


def _normalize_component(
    component: str,
    *,
    layer_type: str | None = None,
    stack: str | None = None,
) -> str:
    normalized = component.removeprefix("hook_")
    if layer_type in {"cross_attn", "cross_attention", "encoder_decoder_attn"}:
        if normalized == "attn":
            return "cross_pattern"
        if normalized == "scores":
            return "cross_attn_scores"
        if normalized == "out":
            return "cross_attn_out"
        if normalized in _ATTENTION_HOOK_COMPONENTS:
            return f"cross_{normalized}"
    if layer_type in {"decoder_attn", "decoder_attention"}:
        if normalized == "attn":
            return "decoder_pattern"
        if normalized == "scores":
            return "decoder_attn_scores"
        if normalized == "out":
            return "decoder_attn_out"
        if normalized in _ATTENTION_HOOK_COMPONENTS:
            return f"decoder_{normalized}"
    if stack == "decoder" and layer_type == "attn":
        if normalized == "attn":
            return "decoder_pattern"
        if normalized == "scores":
            return "decoder_attn_scores"
        if normalized == "out":
            return "decoder_attn_out"
        if normalized in _ATTENTION_HOOK_COMPONENTS:
            return f"decoder_{normalized}"
    if stack == "decoder" and layer_type == "mlp":
        if normalized == "out":
            return "decoder_mlp_out"
        if normalized in {"pre", "pre_linear", "post"}:
            return f"decoder_{normalized}"
    if stack == "decoder" and layer_type in {"ln1", "ln2", "ln3"}:
        if normalized == "scale":
            return f"decoder_{layer_type}_scale"
        if normalized == "normalized":
            return f"decoder_{layer_type}_normalized"
    if stack == "decoder" and layer_type is None:
        decoder_aliases = {
            "attn_out": "decoder_attn_out",
            "attn_in": "decoder_attn_in",
            "mlp_in": "decoder_mlp_in",
            "mlp_out": "decoder_mlp_out",
            "q_input": "decoder_q_input",
            "k_input": "decoder_k_input",
            "v_input": "decoder_v_input",
            "cross_attn_in": "cross_attn_in",
            "cross_attn_out": "cross_attn_out",
            "resid_mid_cross": "decoder_resid_mid_cross",
            "resid_pre": "decoder_resid_pre",
            "resid_mid": "decoder_resid_mid",
            "resid_post": "decoder_resid_post",
        }
        if normalized in decoder_aliases:
            return decoder_aliases[normalized]
    if stack == "encoder" and layer_type == "attn" and normalized == "out":
        return "attn_out"
    if stack == "encoder" and layer_type == "mlp" and normalized == "out":
        return "mlp_out"
    if stack == "encoder" and layer_type is None:
        encoder_aliases = {
            "attn_in": "attn_in",
            "mlp_in": "mlp_in",
            "q_input": "q_input",
            "k_input": "k_input",
            "v_input": "v_input",
        }
        if normalized in encoder_aliases:
            return encoder_aliases[normalized]
    if normalized == "attn":
        return "pattern"
    if normalized == "scale":
        if layer_type == "ln1":
            return "ln1_scale"
        if layer_type == "ln2":
            return "ln2_scale"
        return "ln_scale"
    if normalized == "normalized":
        if layer_type == "ln1":
            return "ln1_normalized"
        if layer_type == "ln2":
            return "ln2_normalized"
        return "normalized"
    if layer_type == "attn" and normalized == "out":
        return "attn_out"
    if layer_type == "mlp" and normalized == "out":
        return "mlp_out"
    if layer_type == "ssm":
        return normalized if normalized.startswith("ssm_") else f"ssm_{normalized}"
    if layer_type == "mlp" and normalized in {"pre", "pre_linear", "post"}:
        return normalized
    aliases = {
        "attn_scores": "attn_scores",
        "scores": "attn_scores",
        "post": "resid_post",
        "pre": "resid_pre",
    }
    return aliases.get(normalized, normalized)


def _spec(
    component: str,
    mode: HookMode,
    *module_paths: str,
    value: ComponentValue = "output",
    activation: ComponentActivation = "raw",
    qkv_layout: QKVLayout = "split",
    aliases: Sequence[str] = (),
    patchable: bool = True,
    cacheable: bool = True,
    supported: bool = True,
    unsupported_reason: str | None = None,
    transformer_lens_name_template: str | None = None,
) -> ComponentHookSpec:
    return ComponentHookSpec(
        component=component,
        mode=mode,
        module_paths=tuple(module_paths),
        value=value,
        activation=activation,
        qkv_layout=qkv_layout,
        aliases=tuple(aliases),
        patchable=patchable,
        cacheable=cacheable,
        supported=supported,
        unsupported_reason=unsupported_reason,
        transformer_lens_name_template=transformer_lens_name_template,
    )


def _pattern_spec(*module_paths: str) -> ComponentHookSpec:
    return _attention_pattern_spec("pattern", *module_paths)


def _attention_pattern_spec(component: str, *module_paths: str) -> ComponentHookSpec:
    return _spec(
        component,
        "forward_output",
        *module_paths,
        value="attention_pattern",
        patchable=True,
        cacheable=True,
    )


def _scores_spec(*module_paths: str) -> ComponentHookSpec:
    return _attention_scores_spec("attn_scores", *module_paths)


def _attention_scores_spec(component: str, *module_paths: str) -> ComponentHookSpec:
    return _spec(
        component,
        "forward_output",
        *module_paths,
        value="attention_scores",
        patchable=True,
        cacheable=True,
    )


def _unsupported_attention_scores_spec() -> ComponentHookSpec:
    return _spec(
        "attn_scores",
        "forward_output",
        "",
        supported=False,
        unsupported_reason=_UNSUPPORTED_ATTENTION_REASON,
    )


def _unsupported_mlp_weight_spec(component: str, reason: str) -> ComponentHookSpec:
    return _spec(
        component,
        "forward_output",
        supported=False,
        unsupported_reason=reason,
    )


def _result_spec(*module_paths: str) -> ComponentHookSpec:
    return _attention_result_spec("result", *module_paths)


def _attention_result_spec(component: str, *module_paths: str) -> ComponentHookSpec:
    return _spec(
        component,
        "forward_input",
        *module_paths,
        activation="split_heads",
        patchable=True,
        cacheable=True,
        unsupported_reason=_UNSUPPORTED_RESULT_REASON,
    )


def _mlp_pre_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec("pre", "forward_output", *module_paths)


def _mlp_pre_linear_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec("pre_linear", "forward_output", *module_paths)


def _mlp_post_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec("post", "forward_input", *module_paths)


def _ln1_scale_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec(
        "ln1_scale",
        "forward_input",
        *module_paths,
        value="norm_scale",
        aliases=("scale",),
    )


def _ln2_scale_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec(
        "ln2_scale",
        "forward_input",
        *module_paths,
        value="norm_scale",
        aliases=("ln_scale",),
    )


def _ln1_normalized_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec("ln1_normalized", "forward_input", *module_paths, aliases=("normalized",))


def _ln2_normalized_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec("ln2_normalized", "forward_input", *module_paths)


def _t5_encoder_hook_template(component: str, *, layer_type: str | None = None) -> str:
    if layer_type is None:
        return f"encoder.{{layer}}.hook_{component}"
    return f"encoder.{{layer}}.{layer_type}.hook_{component}"


_LLAMA_LIKE_LAYER_PATHS = (
    "model.layers.{layer}",
    "model.language_model.layers.{layer}",
)
_LLAMA_LIKE_INPUT_NORM_PATHS = tuple(
    f"{layer_path}.input_layernorm" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_POST_ATTENTION_NORM_PATHS = tuple(
    f"{layer_path}.post_attention_layernorm" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_ATTN_OUT_PATHS = tuple(
    f"{layer_path}.self_attn.o_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_MLP_PATHS = tuple(f"{layer_path}.mlp" for layer_path in _LLAMA_LIKE_LAYER_PATHS)
_LLAMA_LIKE_MLP_GATE_PATHS = tuple(
    f"{layer_path}.mlp.gate_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_MLP_UP_PATHS = tuple(
    f"{layer_path}.mlp.up_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_MLP_DOWN_PATHS = tuple(
    f"{layer_path}.mlp.down_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_Q_PROJ_PATHS = tuple(
    f"{layer_path}.self_attn.q_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_K_PROJ_PATHS = tuple(
    f"{layer_path}.self_attn.k_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_V_PROJ_PATHS = tuple(
    f"{layer_path}.self_attn.v_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_O_PROJ_PATHS = tuple(
    f"{layer_path}.self_attn.o_proj" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)
_LLAMA_LIKE_SELF_ATTN_PATHS = tuple(
    f"{layer_path}.self_attn" for layer_path in _LLAMA_LIKE_LAYER_PATHS
)


LLAMA_LIKE_ADAPTER = ArchitectureAdapter(
    name="llama_like_decoder",
    model_types=(
        "llama",
        "qwen",
        "qwen2",
        "qwen3",
        "mistral",
        "mixtral",
        "gemma",
        "gemma2",
        "gemma3",
        "gemma3_text",
        "gemma3n_text",
        "gemma4_text",
        "olmo",
        "olmo2",
        "olmo3",
        "phi3",
        "qwen2_vl_text",
        "qwen2_5_vl_text",
        "qwen3_vl_text",
        "qwen3_5",
        "qwen3_5_text",
        "stablelm",
        "yi",
    ),
    model_name_markers=(
        "llama",
        "qwen",
        "mistral",
        "mixtral",
        "gemma",
        "olmo",
        "stablelm",
        "/yi-",
        "01-ai/yi",
    ),
    component_specs=(
        _spec("resid_pre", "forward_input", *_LLAMA_LIKE_LAYER_PATHS),
        _spec("resid_mid", "forward_input", *_LLAMA_LIKE_POST_ATTENTION_NORM_PATHS),
        _spec("resid_post", "forward_output", *_LLAMA_LIKE_LAYER_PATHS),
        _spec("attn_out", "forward_output", *_LLAMA_LIKE_ATTN_OUT_PATHS),
        _spec("mlp_out", "forward_output", *_LLAMA_LIKE_MLP_PATHS),
        _mlp_pre_spec(*_LLAMA_LIKE_MLP_GATE_PATHS, *_LLAMA_LIKE_MLP_UP_PATHS),
        _mlp_pre_linear_spec(*_LLAMA_LIKE_MLP_UP_PATHS),
        _mlp_post_spec(*_LLAMA_LIKE_MLP_DOWN_PATHS),
        _spec("q", "forward_output", *_LLAMA_LIKE_Q_PROJ_PATHS, activation="split_heads"),
        _spec("k", "forward_output", *_LLAMA_LIKE_K_PROJ_PATHS, activation="split_heads"),
        _spec("v", "forward_output", *_LLAMA_LIKE_V_PROJ_PATHS, activation="split_heads"),
        _spec("z", "forward_input", *_LLAMA_LIKE_O_PROJ_PATHS, activation="split_heads"),
        _result_spec(*_LLAMA_LIKE_O_PROJ_PATHS),
        _pattern_spec(*_LLAMA_LIKE_SELF_ATTN_PATHS),
        _scores_spec(*_LLAMA_LIKE_SELF_ATTN_PATHS),
        _ln1_scale_spec(*_LLAMA_LIKE_INPUT_NORM_PATHS),
        _ln2_scale_spec(*_LLAMA_LIKE_POST_ATTENTION_NORM_PATHS),
        _ln1_normalized_spec(*_LLAMA_LIKE_INPUT_NORM_PATHS),
        _ln2_normalized_spec(*_LLAMA_LIKE_POST_ATTENTION_NORM_PATHS),
    ),
    notes=(
        "Covers RoPE decoder families with model.layers or model.language_model.layers "
        "and q/k/v/o projections.",
    ),
)

APERTUS_ADAPTER = ArchitectureAdapter(
    name="apertus_decoder",
    model_types=("apertus",),
    model_name_markers=("apertus",),
    component_specs=(
        _spec("resid_pre", "forward_input", "model.layers.{layer}"),
        _spec("resid_mid", "forward_input", "model.layers.{layer}.feedforward_layernorm"),
        _spec("resid_post", "forward_output", "model.layers.{layer}"),
        _spec("attn_out", "forward_output", "model.layers.{layer}.self_attn.o_proj"),
        _spec("mlp_out", "forward_output", "model.layers.{layer}.mlp"),
        _mlp_pre_spec("model.layers.{layer}.mlp.up_proj"),
        _mlp_pre_linear_spec("model.layers.{layer}.mlp.up_proj"),
        _mlp_post_spec("model.layers.{layer}.mlp.down_proj"),
        _spec(
            "q", "forward_output", "model.layers.{layer}.self_attn.q_proj", activation="split_heads"
        ),
        _spec(
            "k", "forward_output", "model.layers.{layer}.self_attn.k_proj", activation="split_heads"
        ),
        _spec(
            "v", "forward_output", "model.layers.{layer}.self_attn.v_proj", activation="split_heads"
        ),
        _spec(
            "z", "forward_input", "model.layers.{layer}.self_attn.o_proj", activation="split_heads"
        ),
        _result_spec("model.layers.{layer}.self_attn.o_proj"),
        _pattern_spec("model.layers.{layer}.self_attn"),
        _scores_spec("model.layers.{layer}.self_attn"),
        _ln1_scale_spec("model.layers.{layer}.attention_layernorm"),
        _ln2_scale_spec("model.layers.{layer}.feedforward_layernorm"),
        _ln1_normalized_spec("model.layers.{layer}.attention_layernorm"),
        _ln2_normalized_spec("model.layers.{layer}.feedforward_layernorm"),
    ),
    notes=(
        "Apertus follows LLaMA-style q/k/v/o projections but uses "
        "attention_layernorm/feedforward_layernorm names and an ungated MLP.",
    ),
)

GPT_OSS_MOE_MLP_REASON = "GPT-OSS uses routed MoE experts rather than a single dense MLP matrix."
ROUTED_MOE_MLP_REASON = (
    "routed MoE layers use multiple experts rather than a single dense MLP matrix"
)

ROUTED_MOE_ADAPTER = ArchitectureAdapter(
    name="routed_moe_decoder",
    model_types=(
        "mixtral",
        "olmoe",
        "qwen2_moe",
        "qwen3_moe",
        "qwen3_5_moe",
        "qwen3_5_moe_text",
        "qwen3_omni_moe_text",
        "qwen3_vl_moe_text",
    ),
    model_name_markers=("mixtral", "olmoe", "qwen2-moe", "qwen3-moe"),
    component_specs=(
        _spec("resid_pre", "forward_input", "model.layers.{layer}"),
        _spec("resid_mid", "forward_input", "model.layers.{layer}.post_attention_layernorm"),
        _spec("resid_post", "forward_output", "model.layers.{layer}"),
        _spec("attn_out", "forward_output", "model.layers.{layer}.self_attn.o_proj"),
        _spec("mlp_out", "forward_output", "model.layers.{layer}.mlp"),
        _unsupported_mlp_weight_spec("pre", ROUTED_MOE_MLP_REASON),
        _unsupported_mlp_weight_spec("pre_linear", ROUTED_MOE_MLP_REASON),
        _unsupported_mlp_weight_spec("post", ROUTED_MOE_MLP_REASON),
        _spec(
            "q", "forward_output", "model.layers.{layer}.self_attn.q_proj", activation="split_heads"
        ),
        _spec(
            "k", "forward_output", "model.layers.{layer}.self_attn.k_proj", activation="split_heads"
        ),
        _spec(
            "v", "forward_output", "model.layers.{layer}.self_attn.v_proj", activation="split_heads"
        ),
        _spec(
            "z", "forward_input", "model.layers.{layer}.self_attn.o_proj", activation="split_heads"
        ),
        _result_spec("model.layers.{layer}.self_attn.o_proj"),
        _pattern_spec("model.layers.{layer}.self_attn"),
        _scores_spec("model.layers.{layer}.self_attn"),
        _ln1_scale_spec("model.layers.{layer}.input_layernorm"),
        _ln2_scale_spec("model.layers.{layer}.post_attention_layernorm"),
        _ln1_normalized_spec("model.layers.{layer}.input_layernorm"),
        _ln2_normalized_spec("model.layers.{layer}.post_attention_layernorm"),
    ),
    notes=(
        "Covers routed MoE decoder families with standard q/k/v/o attention projections; "
        "dense neuron-level MLP matrices are intentionally not exposed.",
    ),
)

GPT_OSS_ADAPTER = ArchitectureAdapter(
    name="gpt_oss_decoder",
    model_types=("gpt_oss",),
    model_name_markers=("gpt-oss", "gpt_oss"),
    component_specs=(
        _spec("resid_pre", "forward_input", "model.layers.{layer}"),
        _spec("resid_mid", "forward_input", "model.layers.{layer}.post_attention_layernorm"),
        _spec("resid_post", "forward_output", "model.layers.{layer}"),
        _spec("attn_out", "forward_output", "model.layers.{layer}.self_attn.o_proj"),
        _spec("mlp_out", "forward_output", "model.layers.{layer}.mlp"),
        _unsupported_mlp_weight_spec("pre", GPT_OSS_MOE_MLP_REASON),
        _unsupported_mlp_weight_spec("pre_linear", GPT_OSS_MOE_MLP_REASON),
        _unsupported_mlp_weight_spec("post", GPT_OSS_MOE_MLP_REASON),
        _spec(
            "q", "forward_output", "model.layers.{layer}.self_attn.q_proj", activation="split_heads"
        ),
        _spec(
            "k", "forward_output", "model.layers.{layer}.self_attn.k_proj", activation="split_heads"
        ),
        _spec(
            "v", "forward_output", "model.layers.{layer}.self_attn.v_proj", activation="split_heads"
        ),
        _spec(
            "z", "forward_input", "model.layers.{layer}.self_attn.o_proj", activation="split_heads"
        ),
        _result_spec("model.layers.{layer}.self_attn.o_proj"),
        _pattern_spec("model.layers.{layer}.self_attn"),
        _scores_spec("model.layers.{layer}.self_attn"),
        _ln1_scale_spec("model.layers.{layer}.input_layernorm"),
        _ln2_scale_spec("model.layers.{layer}.post_attention_layernorm"),
        _ln1_normalized_spec("model.layers.{layer}.input_layernorm"),
        _ln2_normalized_spec("model.layers.{layer}.post_attention_layernorm"),
    ),
    notes=(
        "GPT-OSS exposes standard q/k/v/o attention projections with GQA; "
        "MLP internals are routed experts, so dense W_in/W_out are intentionally not exposed.",
    ),
)

GPT2_ADAPTER = ArchitectureAdapter(
    name="gpt2_decoder",
    model_types=("gpt2",),
    model_name_markers=("gpt2", "distilgpt2", "mgpt"),
    component_specs=(
        _spec("resid_pre", "forward_input", "transformer.h.{layer}"),
        _spec("resid_mid", "forward_input", "transformer.h.{layer}.ln_2"),
        _spec("resid_post", "forward_output", "transformer.h.{layer}"),
        _spec("attn_out", "forward_output", "transformer.h.{layer}.attn.c_proj"),
        _spec("mlp_out", "forward_output", "transformer.h.{layer}.mlp"),
        _mlp_pre_spec("transformer.h.{layer}.mlp.c_fc"),
        _mlp_post_spec("transformer.h.{layer}.mlp.c_proj"),
        _spec(
            "q",
            "forward_output",
            "transformer.h.{layer}.attn.c_attn",
            activation="split_qkv_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "transformer.h.{layer}.attn.c_attn",
            activation="split_qkv_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "transformer.h.{layer}.attn.c_attn",
            activation="split_qkv_heads",
        ),
        _spec("z", "forward_input", "transformer.h.{layer}.attn.c_proj", activation="split_heads"),
        _result_spec("transformer.h.{layer}.attn.c_proj"),
        _pattern_spec("transformer.h.{layer}.attn"),
        _scores_spec("transformer.h.{layer}.attn"),
        _ln1_scale_spec("transformer.h.{layer}.ln_1"),
        _ln2_scale_spec("transformer.h.{layer}.ln_2"),
        _ln1_normalized_spec("transformer.h.{layer}.ln_1"),
        _ln2_normalized_spec("transformer.h.{layer}.ln_2"),
    ),
    notes=("GPT-2 stores q/k/v in a joint c_attn projection; hooks see the joint tensor.",),
)

GPT_BIGCODE_ADAPTER = ArchitectureAdapter(
    name="gpt_bigcode_decoder",
    model_types=("gpt_bigcode",),
    model_name_markers=("bigcode/", "santacoder", "starcoder"),
    component_specs=(
        _spec("resid_pre", "forward_input", "transformer.h.{layer}"),
        _spec("resid_mid", "forward_input", "transformer.h.{layer}.ln_2"),
        _spec("resid_post", "forward_output", "transformer.h.{layer}"),
        _spec("attn_out", "forward_output", "transformer.h.{layer}.attn.c_proj"),
        _spec("mlp_out", "forward_output", "transformer.h.{layer}.mlp"),
        _mlp_pre_spec("transformer.h.{layer}.mlp.c_fc"),
        _mlp_post_spec("transformer.h.{layer}.mlp.c_proj"),
        _spec(
            "q",
            "forward_output",
            "transformer.h.{layer}.attn.c_attn",
            activation="split_qkv_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "transformer.h.{layer}.attn.c_attn",
            activation="split_qkv_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "transformer.h.{layer}.attn.c_attn",
            activation="split_qkv_heads",
        ),
        _spec("z", "forward_input", "transformer.h.{layer}.attn.c_proj", activation="split_heads"),
        _result_spec("transformer.h.{layer}.attn.c_proj"),
        _pattern_spec("transformer.h.{layer}.attn"),
        _scores_spec("transformer.h.{layer}.attn"),
        _ln1_scale_spec("transformer.h.{layer}.ln_1"),
        _ln2_scale_spec("transformer.h.{layer}.ln_2"),
        _ln1_normalized_spec("transformer.h.{layer}.ln_1"),
        _ln2_normalized_spec("transformer.h.{layer}.ln_2"),
    ),
    notes=(
        "GPT-BigCode/SantaCoder packs query plus shared key/value heads in c_attn; "
        "num_key_value_heads controls the split.",
    ),
)

GPT_NEOX_ADAPTER = ArchitectureAdapter(
    name="gpt_neox_decoder",
    model_types=("gpt_neox",),
    model_name_markers=("gpt-neox", "pythia"),
    component_specs=(
        _spec("resid_pre", "forward_input", "gpt_neox.layers.{layer}"),
        _spec("resid_mid", "forward_input", "gpt_neox.layers.{layer}.post_attention_layernorm"),
        _spec("resid_post", "forward_output", "gpt_neox.layers.{layer}"),
        _spec("attn_out", "forward_output", "gpt_neox.layers.{layer}.attention.dense"),
        _spec("mlp_out", "forward_output", "gpt_neox.layers.{layer}.mlp"),
        _mlp_pre_spec("gpt_neox.layers.{layer}.mlp.dense_h_to_4h"),
        _mlp_post_spec("gpt_neox.layers.{layer}.mlp.dense_4h_to_h"),
        _spec(
            "q",
            "forward_output",
            "gpt_neox.layers.{layer}.attention.query_key_value",
            activation="split_qkv_heads",
            qkv_layout="interleaved",
        ),
        _spec(
            "k",
            "forward_output",
            "gpt_neox.layers.{layer}.attention.query_key_value",
            activation="split_qkv_heads",
            qkv_layout="interleaved",
        ),
        _spec(
            "v",
            "forward_output",
            "gpt_neox.layers.{layer}.attention.query_key_value",
            activation="split_qkv_heads",
            qkv_layout="interleaved",
        ),
        _spec(
            "z",
            "forward_input",
            "gpt_neox.layers.{layer}.attention.dense",
            activation="split_heads",
        ),
        _result_spec("gpt_neox.layers.{layer}.attention.dense"),
        _pattern_spec("gpt_neox.layers.{layer}.attention"),
        _scores_spec("gpt_neox.layers.{layer}.attention"),
        _ln1_scale_spec("gpt_neox.layers.{layer}.input_layernorm"),
        _ln2_scale_spec("gpt_neox.layers.{layer}.post_attention_layernorm"),
        _ln1_normalized_spec("gpt_neox.layers.{layer}.input_layernorm"),
        _ln2_normalized_spec("gpt_neox.layers.{layer}.post_attention_layernorm"),
    ),
    notes=("GPT-NeoX/Pythia q/k/v are exposed through a joint query_key_value module.",),
)

GPTJ_ADAPTER = ArchitectureAdapter(
    name="gptj_decoder",
    model_types=("gptj",),
    model_name_markers=("gpt-j", "gptj"),
    component_specs=(
        _spec("resid_pre", "forward_input", "transformer.h.{layer}"),
        _spec("resid_post", "forward_output", "transformer.h.{layer}"),
        _spec("attn_out", "forward_output", "transformer.h.{layer}.attn.out_proj"),
        _spec("mlp_out", "forward_output", "transformer.h.{layer}.mlp"),
        _mlp_pre_spec("transformer.h.{layer}.mlp.fc_in"),
        _mlp_post_spec("transformer.h.{layer}.mlp.fc_out"),
        _spec("q", "forward_output", "transformer.h.{layer}.attn.q_proj", activation="split_heads"),
        _spec("k", "forward_output", "transformer.h.{layer}.attn.k_proj", activation="split_heads"),
        _spec("v", "forward_output", "transformer.h.{layer}.attn.v_proj", activation="split_heads"),
        _spec(
            "z", "forward_input", "transformer.h.{layer}.attn.out_proj", activation="split_heads"
        ),
        _result_spec("transformer.h.{layer}.attn.out_proj"),
        _pattern_spec("transformer.h.{layer}.attn"),
        _scores_spec("transformer.h.{layer}.attn"),
    ),
    notes=("GPT-J uses parallel attention/MLP blocks, so resid_mid is not declared.",),
)

GPT_NEO_ADAPTER = ArchitectureAdapter(
    name="gpt_neo_decoder",
    model_types=("gpt_neo",),
    model_name_markers=("gpt-neo", "tinystories", "tiny-stories"),
    component_specs=(
        _spec("resid_pre", "forward_input", "transformer.h.{layer}"),
        _spec("resid_mid", "forward_input", "transformer.h.{layer}.ln_2"),
        _spec("resid_post", "forward_output", "transformer.h.{layer}"),
        _spec("attn_out", "forward_output", "transformer.h.{layer}.attn.attention.out_proj"),
        _spec("mlp_out", "forward_output", "transformer.h.{layer}.mlp"),
        _mlp_pre_spec("transformer.h.{layer}.mlp.c_fc"),
        _mlp_post_spec("transformer.h.{layer}.mlp.c_proj"),
        _spec(
            "q",
            "forward_output",
            "transformer.h.{layer}.attn.attention.q_proj",
            activation="split_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "transformer.h.{layer}.attn.attention.k_proj",
            activation="split_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "transformer.h.{layer}.attn.attention.v_proj",
            activation="split_heads",
        ),
        _spec(
            "z",
            "forward_input",
            "transformer.h.{layer}.attn.attention.out_proj",
            activation="split_heads",
        ),
        _result_spec("transformer.h.{layer}.attn.attention.out_proj"),
        _pattern_spec("transformer.h.{layer}.attn.attention"),
        _scores_spec("transformer.h.{layer}.attn.attention"),
    ),
)

JOINT_QKV_DECODER_ADAPTER = ArchitectureAdapter(
    name="joint_qkv_decoder",
    model_types=("bloom", "falcon"),
    model_name_markers=("bloom", "falcon"),
    component_specs=(
        _spec("resid_pre", "forward_input", "transformer.h.{layer}"),
        _spec(
            "resid_mid",
            "forward_input",
            "transformer.h.{layer}.post_attention_layernorm",
            "transformer.h.{layer}.ln_mlp",
        ),
        _spec("resid_post", "forward_output", "transformer.h.{layer}"),
        _spec(
            "attn_out",
            "forward_output",
            "transformer.h.{layer}.self_attention.dense",
        ),
        _spec("mlp_out", "forward_output", "transformer.h.{layer}.mlp"),
        _mlp_pre_spec(
            "transformer.h.{layer}.mlp.dense_h_to_4h",
        ),
        _mlp_post_spec(
            "transformer.h.{layer}.mlp.dense_4h_to_h",
        ),
        _spec(
            "q",
            "forward_output",
            "transformer.h.{layer}.self_attention.query_key_value",
            activation="split_qkv_heads",
            qkv_layout="interleaved",
        ),
        _spec(
            "k",
            "forward_output",
            "transformer.h.{layer}.self_attention.query_key_value",
            activation="split_qkv_heads",
            qkv_layout="interleaved",
        ),
        _spec(
            "v",
            "forward_output",
            "transformer.h.{layer}.self_attention.query_key_value",
            activation="split_qkv_heads",
            qkv_layout="interleaved",
        ),
        _spec(
            "z",
            "forward_input",
            "transformer.h.{layer}.self_attention.dense",
            activation="split_heads",
        ),
        _result_spec("transformer.h.{layer}.self_attention.dense"),
        _pattern_spec("transformer.h.{layer}.self_attention"),
        _scores_spec("transformer.h.{layer}.self_attention"),
    ),
    notes=("BLOOM/Falcon expose q/k/v through a joint query_key_value module.",),
)

MPT_ADAPTER = ArchitectureAdapter(
    name="mpt_decoder",
    model_types=("mpt",),
    model_name_markers=("mpt-", "mosaicml/mpt"),
    component_specs=(
        _spec("resid_pre", "forward_input", "transformer.blocks.{layer}"),
        _spec("resid_mid", "forward_input", "transformer.blocks.{layer}.norm_2"),
        _spec("resid_post", "forward_output", "transformer.blocks.{layer}"),
        _spec("attn_out", "forward_output", "transformer.blocks.{layer}.attn.out_proj"),
        _spec("mlp_out", "forward_output", "transformer.blocks.{layer}.ffn.down_proj"),
        _mlp_pre_spec("transformer.blocks.{layer}.ffn.up_proj"),
        _mlp_post_spec("transformer.blocks.{layer}.ffn.down_proj"),
        _spec(
            "q",
            "forward_output",
            "transformer.blocks.{layer}.attn.Wqkv",
            activation="split_qkv_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "transformer.blocks.{layer}.attn.Wqkv",
            activation="split_qkv_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "transformer.blocks.{layer}.attn.Wqkv",
            activation="split_qkv_heads",
        ),
        _spec(
            "z",
            "forward_input",
            "transformer.blocks.{layer}.attn.out_proj",
            activation="split_heads",
        ),
        _result_spec("transformer.blocks.{layer}.attn.out_proj"),
        _pattern_spec("transformer.blocks.{layer}.attn"),
        _scores_spec("transformer.blocks.{layer}.attn"),
    ),
    notes=("MPT exposes q/k/v through Wqkv; hooks see the joint projection tensor.",),
)

PHI_ADAPTER = ArchitectureAdapter(
    name="phi_decoder",
    model_types=("phi", "phi-msft"),
    model_name_markers=("microsoft/phi", "phi-"),
    component_specs=(
        _spec("resid_pre", "forward_input", "model.layers.{layer}"),
        _spec("resid_post", "forward_output", "model.layers.{layer}"),
        _spec(
            "attn_out",
            "forward_output",
            "model.layers.{layer}.self_attn.dense",
            "model.layers.{layer}.self_attn.o_proj",
        ),
        _spec("mlp_out", "forward_output", "model.layers.{layer}.mlp"),
        _mlp_pre_spec("model.layers.{layer}.mlp.fc1", "model.layers.{layer}.mlp.gate_up_proj"),
        _mlp_post_spec("model.layers.{layer}.mlp.fc2", "model.layers.{layer}.mlp.down_proj"),
        _spec(
            "q", "forward_output", "model.layers.{layer}.self_attn.q_proj", activation="split_heads"
        ),
        _spec(
            "k", "forward_output", "model.layers.{layer}.self_attn.k_proj", activation="split_heads"
        ),
        _spec(
            "v", "forward_output", "model.layers.{layer}.self_attn.v_proj", activation="split_heads"
        ),
        _spec(
            "z",
            "forward_input",
            "model.layers.{layer}.self_attn.dense",
            "model.layers.{layer}.self_attn.o_proj",
            activation="split_heads",
        ),
        _result_spec(
            "model.layers.{layer}.self_attn.dense", "model.layers.{layer}.self_attn.o_proj"
        ),
        _pattern_spec("model.layers.{layer}.self_attn"),
        _scores_spec("model.layers.{layer}.self_attn"),
    ),
    notes=("Phi variants differ in output projection name; both dense and o_proj are tried.",),
)

OPT_ADAPTER = ArchitectureAdapter(
    name="opt_decoder",
    model_types=("opt",),
    model_name_markers=("facebook/opt", "opt-"),
    component_specs=(
        _spec("resid_pre", "forward_input", "model.decoder.layers.{layer}"),
        _spec("resid_mid", "forward_input", "model.decoder.layers.{layer}.final_layer_norm"),
        _spec("resid_post", "forward_output", "model.decoder.layers.{layer}"),
        _spec("attn_out", "forward_output", "model.decoder.layers.{layer}.self_attn.out_proj"),
        _spec("mlp_out", "forward_output", "model.decoder.layers.{layer}.fc2"),
        _mlp_pre_spec("model.decoder.layers.{layer}.fc1"),
        _mlp_post_spec("model.decoder.layers.{layer}.fc2"),
        _spec(
            "q",
            "forward_output",
            "model.decoder.layers.{layer}.self_attn.q_proj",
            activation="split_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "model.decoder.layers.{layer}.self_attn.k_proj",
            activation="split_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "model.decoder.layers.{layer}.self_attn.v_proj",
            activation="split_heads",
        ),
        _spec(
            "z",
            "forward_input",
            "model.decoder.layers.{layer}.self_attn.out_proj",
            activation="split_heads",
        ),
        _result_spec("model.decoder.layers.{layer}.self_attn.out_proj"),
        _pattern_spec("model.decoder.layers.{layer}.self_attn"),
        _scores_spec("model.decoder.layers.{layer}.self_attn"),
    ),
)

BERT_ADAPTER = ArchitectureAdapter(
    name="bert_encoder",
    model_types=("bert", "roberta"),
    model_name_markers=("bert-", "google-bert/", "roberta"),
    component_specs=(
        _spec("resid_pre", "forward_input", "encoder.layer.{layer}", "bert.encoder.layer.{layer}"),
        _spec(
            "resid_mid",
            "forward_input",
            "encoder.layer.{layer}.intermediate",
            "bert.encoder.layer.{layer}.intermediate",
        ),
        _spec(
            "resid_post",
            "forward_output",
            "encoder.layer.{layer}",
            "bert.encoder.layer.{layer}",
        ),
        _spec(
            "attn_out",
            "forward_output",
            "encoder.layer.{layer}.attention.output.dense",
            "bert.encoder.layer.{layer}.attention.output.dense",
        ),
        _spec(
            "mlp_out",
            "forward_output",
            "encoder.layer.{layer}.output.dense",
            "bert.encoder.layer.{layer}.output.dense",
        ),
        _mlp_pre_spec(
            "encoder.layer.{layer}.intermediate.dense",
            "bert.encoder.layer.{layer}.intermediate.dense",
        ),
        _mlp_pre_linear_spec(
            "encoder.layer.{layer}.intermediate.dense",
            "bert.encoder.layer.{layer}.intermediate.dense",
        ),
        _mlp_post_spec(
            "encoder.layer.{layer}.output.dense",
            "bert.encoder.layer.{layer}.output.dense",
        ),
        _spec(
            "q",
            "forward_output",
            "encoder.layer.{layer}.attention.self.query",
            "bert.encoder.layer.{layer}.attention.self.query",
            activation="split_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "encoder.layer.{layer}.attention.self.key",
            "bert.encoder.layer.{layer}.attention.self.key",
            activation="split_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "encoder.layer.{layer}.attention.self.value",
            "bert.encoder.layer.{layer}.attention.self.value",
            activation="split_heads",
        ),
        _spec(
            "z",
            "forward_input",
            "encoder.layer.{layer}.attention.output.dense",
            "bert.encoder.layer.{layer}.attention.output.dense",
            activation="split_heads",
        ),
        _result_spec(
            "encoder.layer.{layer}.attention.output.dense",
            "bert.encoder.layer.{layer}.attention.output.dense",
        ),
        _pattern_spec(
            "encoder.layer.{layer}.attention.self",
            "bert.encoder.layer.{layer}.attention.self",
        ),
        _scores_spec(
            "encoder.layer.{layer}.attention.self",
            "bert.encoder.layer.{layer}.attention.self",
        ),
    ),
)

DISTILBERT_ADAPTER = ArchitectureAdapter(
    name="distilbert_encoder",
    model_types=("distilbert",),
    model_name_markers=("distilbert",),
    component_specs=(
        _spec("resid_pre", "forward_input", "transformer.layer.{layer}"),
        _spec("resid_mid", "forward_input", "transformer.layer.{layer}.ffn"),
        _spec("resid_post", "forward_output", "transformer.layer.{layer}"),
        _spec("attn_out", "forward_output", "transformer.layer.{layer}.attention.out_lin"),
        _spec("mlp_out", "forward_output", "transformer.layer.{layer}.ffn.lin2"),
        _mlp_pre_spec("transformer.layer.{layer}.ffn.lin1"),
        _mlp_pre_linear_spec("transformer.layer.{layer}.ffn.lin1"),
        _mlp_post_spec("transformer.layer.{layer}.ffn.lin2"),
        _spec(
            "q",
            "forward_output",
            "transformer.layer.{layer}.attention.q_lin",
            activation="split_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "transformer.layer.{layer}.attention.k_lin",
            activation="split_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "transformer.layer.{layer}.attention.v_lin",
            activation="split_heads",
        ),
        _spec(
            "z",
            "forward_input",
            "transformer.layer.{layer}.attention.out_lin",
            activation="split_heads",
        ),
        _result_spec("transformer.layer.{layer}.attention.out_lin"),
        _pattern_spec("transformer.layer.{layer}.attention"),
        _scores_spec("transformer.layer.{layer}.attention"),
    ),
)

AUDIO_ENCODER_ADAPTER = ArchitectureAdapter(
    name="audio_encoder",
    model_types=("wav2vec2", "hubert"),
    model_name_markers=("wav2vec2", "hubert"),
    component_specs=(
        _spec("resid_pre", "forward_input", "encoder.layers.{layer}"),
        _spec("resid_mid", "forward_input", "encoder.layers.{layer}.feed_forward"),
        _spec("resid_post", "forward_output", "encoder.layers.{layer}"),
        _spec("attn_out", "forward_output", "encoder.layers.{layer}.attention.out_proj"),
        _spec("mlp_out", "forward_output", "encoder.layers.{layer}.feed_forward.output_dense"),
        _mlp_pre_spec("encoder.layers.{layer}.feed_forward.intermediate_dense"),
        _mlp_pre_linear_spec("encoder.layers.{layer}.feed_forward.intermediate_dense"),
        _mlp_post_spec("encoder.layers.{layer}.feed_forward.output_dense"),
        _spec(
            "q",
            "forward_output",
            "encoder.layers.{layer}.attention.q_proj",
            activation="split_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "encoder.layers.{layer}.attention.k_proj",
            activation="split_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "encoder.layers.{layer}.attention.v_proj",
            activation="split_heads",
        ),
        _spec(
            "z",
            "forward_input",
            "encoder.layers.{layer}.attention.out_proj",
            activation="split_heads",
        ),
        _result_spec("encoder.layers.{layer}.attention.out_proj"),
        _pattern_spec("encoder.layers.{layer}.attention"),
        _scores_spec("encoder.layers.{layer}.attention"),
    ),
)

T5_ENCODER_ADAPTER = ArchitectureAdapter(
    name="t5_encoder_decoder",
    model_types=("t5",),
    model_name_markers=("t5-", "google-t5/"),
    component_specs=(
        _spec(
            "resid_pre",
            "forward_input",
            "encoder.block.{layer}",
            transformer_lens_name_template=_t5_encoder_hook_template("resid_pre"),
        ),
        _spec(
            "resid_mid",
            "forward_input",
            "encoder.block.{layer}.layer.1",
            transformer_lens_name_template=_t5_encoder_hook_template("resid_mid"),
        ),
        _spec(
            "resid_post",
            "forward_output",
            "encoder.block.{layer}",
            transformer_lens_name_template=_t5_encoder_hook_template("resid_post"),
        ),
        _spec(
            "attn_in",
            "forward_input",
            "encoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("attn_in"),
        ),
        _spec(
            "attn_out",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention.o",
            transformer_lens_name_template=_t5_encoder_hook_template("attn_out"),
        ),
        _spec(
            "mlp_in",
            "forward_input",
            "encoder.block.{layer}.layer.1.layer_norm",
            transformer_lens_name_template=_t5_encoder_hook_template("mlp_in"),
        ),
        _spec(
            "mlp_out",
            "forward_output",
            "encoder.block.{layer}.layer.1.DenseReluDense",
            transformer_lens_name_template=_t5_encoder_hook_template("mlp_out"),
        ),
        _spec(
            "pre",
            "forward_output",
            "encoder.block.{layer}.layer.1.DenseReluDense.wi",
            "encoder.block.{layer}.layer.1.DenseReluDense.wi_0",
            transformer_lens_name_template=_t5_encoder_hook_template("pre", layer_type="mlp"),
        ),
        _spec(
            "pre_linear",
            "forward_output",
            "encoder.block.{layer}.layer.1.DenseReluDense.wi",
            "encoder.block.{layer}.layer.1.DenseReluDense.wi_1",
            transformer_lens_name_template=_t5_encoder_hook_template(
                "pre_linear",
                layer_type="mlp",
            ),
        ),
        _spec(
            "post",
            "forward_input",
            "encoder.block.{layer}.layer.1.DenseReluDense.wo",
            transformer_lens_name_template=_t5_encoder_hook_template("post", layer_type="mlp"),
        ),
        _spec(
            "q_input",
            "forward_input",
            "encoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("q_input"),
        ),
        _spec(
            "k_input",
            "forward_input",
            "encoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("k_input"),
        ),
        _spec(
            "v_input",
            "forward_input",
            "encoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("v_input"),
        ),
        _spec(
            "q",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention.q",
            activation="split_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("q", layer_type="attn"),
        ),
        _spec(
            "k",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention.k",
            activation="split_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("k", layer_type="attn"),
        ),
        _spec(
            "v",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention.v",
            activation="split_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("v", layer_type="attn"),
        ),
        _spec(
            "z",
            "forward_input",
            "encoder.block.{layer}.layer.0.SelfAttention.o",
            activation="split_heads",
            transformer_lens_name_template=_t5_encoder_hook_template("z", layer_type="attn"),
        ),
        _spec(
            "result",
            "forward_input",
            "encoder.block.{layer}.layer.0.SelfAttention.o",
            activation="split_heads",
            patchable=True,
            cacheable=True,
            unsupported_reason=_UNSUPPORTED_RESULT_REASON,
            transformer_lens_name_template=_t5_encoder_hook_template(
                "result",
                layer_type="attn",
            ),
        ),
        _spec(
            "pattern",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention",
            value="attention_pattern",
            patchable=True,
            cacheable=True,
            transformer_lens_name_template=_t5_encoder_hook_template(
                "pattern",
                layer_type="attn",
            ),
        ),
        _spec(
            "attn_scores",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention",
            value="attention_scores",
            patchable=True,
            cacheable=True,
            transformer_lens_name_template=_t5_encoder_hook_template(
                "attn_scores",
                layer_type="attn",
            ),
        ),
        _spec("decoder_resid_pre", "forward_input", "decoder.block.{layer}"),
        _spec("decoder_resid_mid", "forward_input", "decoder.block.{layer}.layer.1"),
        _spec("decoder_resid_mid_cross", "forward_input", "decoder.block.{layer}.layer.2"),
        _spec("decoder_resid_post", "forward_output", "decoder.block.{layer}"),
        _spec(
            "decoder_attn_in",
            "forward_input",
            "decoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
        ),
        _spec(
            "decoder_attn_out",
            "forward_output",
            "decoder.block.{layer}.layer.0.SelfAttention.o",
        ),
        _spec(
            "cross_attn_in",
            "forward_input",
            "decoder.block.{layer}.layer.1.layer_norm",
        ),
        _spec(
            "cross_attn_out",
            "forward_output",
            "decoder.block.{layer}.layer.1.EncDecAttention.o",
        ),
        _spec(
            "decoder_mlp_in",
            "forward_input",
            "decoder.block.{layer}.layer.2.layer_norm",
        ),
        _spec(
            "decoder_mlp_out",
            "forward_output",
            "decoder.block.{layer}.layer.2.DenseReluDense",
        ),
        _spec(
            "decoder_pre",
            "forward_output",
            "decoder.block.{layer}.layer.2.DenseReluDense.wi",
            "decoder.block.{layer}.layer.2.DenseReluDense.wi_0",
        ),
        _spec(
            "decoder_pre_linear",
            "forward_output",
            "decoder.block.{layer}.layer.2.DenseReluDense.wi",
            "decoder.block.{layer}.layer.2.DenseReluDense.wi_1",
        ),
        _spec("decoder_post", "forward_input", "decoder.block.{layer}.layer.2.DenseReluDense.wo"),
        _spec(
            "decoder_q_input",
            "forward_input",
            "decoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
        ),
        _spec(
            "decoder_k_input",
            "forward_input",
            "decoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
        ),
        _spec(
            "decoder_v_input",
            "forward_input",
            "decoder.block.{layer}.layer.0.layer_norm",
            activation="repeat_heads",
        ),
        _spec(
            "decoder_q",
            "forward_output",
            "decoder.block.{layer}.layer.0.SelfAttention.q",
            activation="split_heads",
        ),
        _spec(
            "decoder_k",
            "forward_output",
            "decoder.block.{layer}.layer.0.SelfAttention.k",
            activation="split_heads",
        ),
        _spec(
            "decoder_v",
            "forward_output",
            "decoder.block.{layer}.layer.0.SelfAttention.v",
            activation="split_heads",
        ),
        _spec(
            "decoder_z",
            "forward_input",
            "decoder.block.{layer}.layer.0.SelfAttention.o",
            activation="split_heads",
        ),
        _attention_result_spec("decoder_result", "decoder.block.{layer}.layer.0.SelfAttention.o"),
        _attention_pattern_spec("decoder_pattern", "decoder.block.{layer}.layer.0.SelfAttention"),
        _attention_scores_spec(
            "decoder_attn_scores",
            "decoder.block.{layer}.layer.0.SelfAttention",
        ),
        _spec(
            "cross_q",
            "forward_output",
            "decoder.block.{layer}.layer.1.EncDecAttention.q",
            activation="split_heads",
        ),
        _spec(
            "cross_k",
            "forward_output",
            "decoder.block.{layer}.layer.1.EncDecAttention.k",
            activation="split_heads",
        ),
        _spec(
            "cross_v",
            "forward_output",
            "decoder.block.{layer}.layer.1.EncDecAttention.v",
            activation="split_heads",
        ),
        _spec(
            "cross_z",
            "forward_input",
            "decoder.block.{layer}.layer.1.EncDecAttention.o",
            activation="split_heads",
        ),
        _attention_result_spec("cross_result", "decoder.block.{layer}.layer.1.EncDecAttention.o"),
        _attention_pattern_spec("cross_pattern", "decoder.block.{layer}.layer.1.EncDecAttention"),
        _attention_scores_spec(
            "cross_attn_scores",
            "decoder.block.{layer}.layer.1.EncDecAttention",
        ),
        _spec(
            "decoder_ln1_scale",
            "forward_input",
            "decoder.block.{layer}.layer.0.layer_norm",
            value="norm_scale",
        ),
        _spec(
            "decoder_ln2_scale",
            "forward_input",
            "decoder.block.{layer}.layer.1.layer_norm",
            value="norm_scale",
        ),
        _spec(
            "decoder_ln3_scale",
            "forward_input",
            "decoder.block.{layer}.layer.2.layer_norm",
            value="norm_scale",
        ),
        _spec(
            "decoder_ln1_normalized",
            "forward_input",
            "decoder.block.{layer}.layer.0.layer_norm",
        ),
        _spec(
            "decoder_ln2_normalized",
            "forward_input",
            "decoder.block.{layer}.layer.1.layer_norm",
        ),
        _spec(
            "decoder_ln3_normalized",
            "forward_input",
            "decoder.block.{layer}.layer.2.layer_norm",
        ),
    ),
    notes=(
        "Maps HuggingFace T5 encoder, decoder self-attention, cross-attention, "
        "and decoder feed-forward component families.",
    ),
)

MAMBA_ADAPTER = ArchitectureAdapter(
    name="mamba_ssm",
    model_types=("mamba",),
    component_specs=(
        _spec("resid_pre", "forward_input", "backbone.layers.{layer}", "model.layers.{layer}"),
        _spec("resid_post", "forward_output", "backbone.layers.{layer}", "model.layers.{layer}"),
        _ln1_normalized_spec("backbone.layers.{layer}.norm", "model.layers.{layer}.norm"),
        _spec(
            "ssm_in",
            "forward_output",
            "backbone.layers.{layer}.mixer.in_proj",
            "model.layers.{layer}.mixer.in_proj",
            aliases=("in",),
        ),
        _spec(
            "ssm_conv",
            "forward_output",
            "backbone.layers.{layer}.mixer.conv1d",
            "model.layers.{layer}.mixer.conv1d",
            aliases=("conv",),
        ),
        _spec(
            "ssm_x",
            "forward_output",
            "backbone.layers.{layer}.mixer.x_proj",
            "model.layers.{layer}.mixer.x_proj",
            aliases=("x",),
        ),
        _spec(
            "ssm_dt",
            "forward_output",
            "backbone.layers.{layer}.mixer.dt_proj",
            "model.layers.{layer}.mixer.dt_proj",
            aliases=("dt",),
        ),
        _spec(
            "ssm_out",
            "forward_input",
            "backbone.layers.{layer}.mixer.out_proj",
            "model.layers.{layer}.mixer.out_proj",
            aliases=("out",),
        ),
        _spec(
            "pattern",
            "forward_output",
            "",
            supported=False,
            unsupported_reason=_UNSUPPORTED_SSM_ATTENTION_REASON,
        ),
        _spec(
            "attn_scores",
            "forward_output",
            "",
            supported=False,
            unsupported_reason=_UNSUPPORTED_SSM_ATTENTION_REASON,
        ),
    ),
    model_name_markers=("state-spaces/mamba-",),
    notes=(
        "State-space adapter for HuggingFace Mamba models. It exposes residual, "
        "normalization, and mixer projection hooks; attention hooks are unsupported.",
    ),
)

MAMBA2_ADAPTER = ArchitectureAdapter(
    name="mamba2_ssm",
    model_types=("mamba2",),
    component_specs=(
        _spec("resid_pre", "forward_input", "backbone.layers.{layer}", "model.layers.{layer}"),
        _spec("resid_post", "forward_output", "backbone.layers.{layer}", "model.layers.{layer}"),
        _ln1_normalized_spec("backbone.layers.{layer}.norm", "model.layers.{layer}.norm"),
        _spec(
            "ssm_in",
            "forward_output",
            "backbone.layers.{layer}.mixer.in_proj",
            "model.layers.{layer}.mixer.in_proj",
            aliases=("in",),
        ),
        _spec(
            "ssm_conv",
            "forward_output",
            "backbone.layers.{layer}.mixer.conv1d",
            "model.layers.{layer}.mixer.conv1d",
            aliases=("conv",),
        ),
        _spec(
            "ssm_inner_norm",
            "forward_input",
            "backbone.layers.{layer}.mixer.norm",
            "model.layers.{layer}.mixer.norm",
            aliases=("inner_norm",),
        ),
        _spec(
            "ssm_out",
            "forward_input",
            "backbone.layers.{layer}.mixer.out_proj",
            "model.layers.{layer}.mixer.out_proj",
            aliases=("out",),
        ),
        _spec(
            "pattern",
            "forward_output",
            "",
            supported=False,
            unsupported_reason=_UNSUPPORTED_SSM_ATTENTION_REASON,
        ),
        _spec(
            "attn_scores",
            "forward_output",
            "",
            supported=False,
            unsupported_reason=_UNSUPPORTED_SSM_ATTENTION_REASON,
        ),
    ),
    model_name_markers=("mistralai/mamba-codestral",),
    notes=(
        "State-space adapter for HuggingFace Mamba2 models. It exposes residual, "
        "normalization, and mixer projection hooks; attention hooks are unsupported.",
    ),
)

GENERIC_DECODER_ADAPTER = ArchitectureAdapter(
    name="generic_decoder",
    model_types=(),
    component_specs=(
        _spec(
            "resid_pre",
            "forward_input",
            "model.layers.{layer}",
            "transformer.h.{layer}",
            "gpt_neox.layers.{layer}",
        ),
        _spec(
            "resid_post",
            "forward_output",
            "model.layers.{layer}",
            "transformer.h.{layer}",
            "gpt_neox.layers.{layer}",
        ),
        _unsupported_attention_scores_spec(),
    ),
    notes=("Fallback adapter for integer layer and residual hooks when architecture is unknown.",),
)

SUPPORTED_ARCHITECTURE_ADAPTERS: tuple[ArchitectureAdapter, ...] = (
    MAMBA2_ADAPTER,
    MAMBA_ADAPTER,
    ROUTED_MOE_ADAPTER,
    LLAMA_LIKE_ADAPTER,
    APERTUS_ADAPTER,
    GPT_OSS_ADAPTER,
    GPT2_ADAPTER,
    GPT_BIGCODE_ADAPTER,
    GPT_NEOX_ADAPTER,
    GPTJ_ADAPTER,
    GPT_NEO_ADAPTER,
    JOINT_QKV_DECODER_ADAPTER,
    MPT_ADAPTER,
    PHI_ADAPTER,
    OPT_ADAPTER,
    DISTILBERT_ADAPTER,
    AUDIO_ENCODER_ADAPTER,
    BERT_ADAPTER,
    T5_ENCODER_ADAPTER,
)
