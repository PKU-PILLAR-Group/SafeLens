"""Architecture bridge primitives for Transformers-backed model adapters.

The design mirrors the useful part of TransformerLens' model bridge: keep model
loading provider-specific, but map each model family into a small canonical
component vocabulary that SafeLens hooks and patching code can target.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from inspect import Parameter, signature
from typing import Any, Literal

from SafeLens.core.base import HookFn, LayerRef

HookMode = Literal["forward_output", "forward_input"]
ComponentValue = Literal["output", "attention_pattern", "attention_scores"]
ComponentActivation = Literal["raw", "split_heads", "split_qkv_heads"]
QKVLayout = Literal["split", "interleaved"]

CANONICAL_TRANSFORMER_COMPONENTS: tuple[str, ...] = (
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
)

_UNSUPPORTED_ATTENTION_REASON = (
    "this fallback adapter has no known attention module path for softmax instrumentation"
)
_UNSUPPORTED_RESULT_REASON = (
    "TransformerLens result vectors are derived from z @ W_O for HuggingFace "
    "projection modules"
)
_ATTENTION_SOFTMAX_STATE_ATTR = "_safelens_attention_softmax_hook_state"
_HOOK_CONTEXTS_ATTR = "_safelens_hook_contexts"


@dataclass(frozen=True)
class ComponentRef:
    """One parsed reference to a canonical transformer component."""

    layer: int
    component: str
    original: LayerRef

    @property
    def safelens_name(self) -> str:
        return f"layer_{self.layer}.{self.component}"

    @property
    def transformer_lens_name(self) -> str:
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
            r"blocks\.(\d+)\.(?:([a-zA-Z0-9_]+)\.)?hook_([a-zA-Z0-9_]+)", layer
        )
        if block_match is not None:
            layer_type = block_match.group(2)
            return self._make_ref(
                int(block_match.group(1)),
                _normalize_component(block_match.group(3), layer_type=layer_type),
                layer,
            )

        return None

    def register_component_hook(self, model: Any, layer: LayerRef, hook_fn: HookFn) -> Any:
        return self.register_component_hook_for_mode(model, layer, hook_fn, for_cache=False)

    def register_component_hook_for_mode(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
        *,
        for_cache: bool,
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
            )
        if spec.component == "result" and not for_cache:
            hook = _make_attention_result_output_hook(
                hook_fn,
                component_ref,
                self.name,
                spec,
                model,
            )
            return _ComponentHookHandle(
                module.register_forward_hook(hook),
                _hook_contexts_for(hook),
            )
        if spec.mode == "forward_input":
            hook = _make_component_input_hook(hook_fn, component_ref, self.name, spec, model)
            return _ComponentHookHandle(
                module.register_forward_pre_hook(hook),
                _hook_contexts_for(hook),
            )
        hook = _make_component_output_hook(hook_fn, component_ref, self.name, spec, model)
        return _ComponentHookHandle(
            module.register_forward_hook(hook),
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
            return reshape_joint_qkv_attention_weight(
                weight,
                component=component,
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
        n_heads = head_count_for_component(model, component)
        return reshape_attention_weight(
            weight,
            component=component,
            n_heads=n_heads,
            packed_axis=preferred_attention_weight_packed_axis(
                module,
                architecture=self.name,
                component=component,
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
            return reshape_joint_qkv_attention_bias(
                bias,
                component=component,
                q_heads=head_count_for_component(model, "q"),
                kv_heads=head_count_for_component(model, "k"),
                qkv_layout=spec.qkv_layout,
            )
        if spec.activation != "split_heads":
            raise NotImplementedError(
                f"{self.name} cannot expose b_{component.upper()} from "
                f"{spec.activation!r} projections yet."
            )
        return reshape_attention_bias(
            bias,
            component=component,
            n_heads=head_count_for_component(model, component),
        )

    def get_embedding_weight(self, model: Any, *, positional: bool = False) -> Any:
        """Return token or positional embedding weights for common Transformers layouts."""
        paths = (
            (
                "transformer.wpe",
                "wpe",
                "model.embed_positions",
                "embed_positions",
                "model.wpe",
            )
            if positional
            else (
                "transformer.wte",
                "wte",
                "model.embed_tokens",
                "embed_tokens",
                "encoder.embed_tokens",
                "shared",
            )
        )
        kind = "positional embedding" if positional else "token embedding"
        return _weight_from_first_path(model, paths, kind=kind)

    def get_mlp_weight(self, model: Any, component: str, layer: int) -> Any:
        """Return a TransformerLens-shaped MLP weight matrix for one layer."""
        if component == "in":
            paths = self._mlp_weight_paths(
                layer,
                canonical_component="pre_linear",
                fallback_component="pre",
            )
        elif component == "gate":
            paths = (
                f"model.layers.{layer}.mlp.gate_proj",
                f"model.layers.{layer}.mlp.gate",
                f"model.layers.{layer}.mlp.w1",
            )
        elif component == "out":
            paths = self._mlp_weight_paths(layer, canonical_component="post")
        else:
            raise ValueError(f"Unsupported MLP weight component {component!r}.")
        weight = _weight_from_first_path(model, paths, kind=f"MLP {component} weight")
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
        return _bias_from_first_path(model, paths, kind=f"MLP {component} bias")

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
            raise KeyError(
                f"{self.name!r} does not declare MLP component {canonical_component!r}."
            )
        return tuple(template.format(layer=layer) for template in spec.module_paths)

    def _make_ref(self, layer: int, component: str, original: LayerRef) -> ComponentRef | None:
        normalized = component if component in self._aliases else _normalize_component(component)
        if normalized not in self._aliases:
            return None
        return ComponentRef(layer=layer, component=self._aliases[normalized], original=original)

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


def _weight_from_first_path(model: Any, paths: Sequence[str], *, kind: str) -> Any:
    attempted: list[str] = []
    for path in paths:
        attempted.append(path)
        try:
            module = resolve_module_path(model, path)
        except (AttributeError, IndexError, KeyError, TypeError):
            continue
        weight = getattr(module, "weight", None)
        if weight is not None:
            return weight
    attempted_paths = ", ".join(attempted)
    raise KeyError(f"Could not resolve {kind}. Tried module paths: {attempted_paths}.")


def _bias_from_first_path(model: Any, paths: Sequence[str], *, kind: str) -> Any:
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
            return zeros_like_last_dim(weight, axis=0)
    attempted_paths = ", ".join(attempted)
    raise KeyError(f"Could not resolve {kind}. Tried module paths: {attempted_paths}.")


def transpose_2d_weight(weight: Any) -> Any:
    """Return a rank-2 weight transposed without requiring tensor dependencies."""
    if hasattr(weight, "T") and getattr(weight, "ndim", 0) == 2:
        return weight.T
    if isinstance(weight, list):
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


def transformer_lens_component_name(component: str, layer: int) -> str:
    """Return a TransformerLens-style hook name for a canonical component."""
    if component in {"q", "k", "v", "z", "pattern", "attn_scores", "result"}:
        hook_component = "attn_scores" if component == "attn_scores" else component
        return f"blocks.{layer}.attn.hook_{hook_component}"
    if component in {"pre", "pre_linear", "post"}:
        return f"blocks.{layer}.mlp.hook_{component}"
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
        if include_result or component != "result"
    )
    if include_attention:
        return supported_components
    if include_pattern:
        return tuple(
            component
            for component in supported_components
            if component not in {"result", "attn_scores"}
        )
    return tuple(
        component
        for component in supported_components
        if component not in {"result", "pattern", "attn_scores"}
    )


def architecture_adapter_for_model(model: Any, *, model_name: str = "") -> ArchitectureAdapter:
    """Select a SafeLens architecture adapter for a loaded Transformers model."""
    config = getattr(model, "config", None)
    model_type = getattr(config, "model_type", None)
    return architecture_adapter_for_name(model_name=model_name, model_type=model_type)


def architecture_adapter_for_name(
    *,
    model_name: str,
    model_type: str | None = None,
) -> ArchitectureAdapter:
    """Select an architecture adapter from a model name and optional HF model_type."""
    for adapter in SUPPORTED_ARCHITECTURE_ADAPTERS:
        if adapter.supports_model(model_type=model_type, model_name=model_name):
            return adapter
    return GENERIC_DECODER_ADAPTER


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
        activation = extract_component_activation(output, spec, model)
        patched = call_component_hook(
            hook_fn,
            activation=activation,
            component_ref=component_ref,
            architecture=architecture,
            hook_context=hook_context,
        )
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
        if spec.component == "result":
            return None
        if patched is None:
            return None
        merged = merge_component_activation(patched, raw_activation, spec, model)
        return (merged, *tuple(inputs[1:]))

    _set_hook_contexts(hook, (hook_context,))
    return hook


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
        return merged_output

    _set_hook_contexts(hook, (hook_context,))
    return hook


def _set_hook_contexts(hook: Callable[..., Any], contexts: tuple[ComponentHookContext, ...]) -> None:
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
    return output


def first_output(output: Any) -> Any:
    """Return the tensor payload from common Transformers module outputs."""
    if isinstance(output, tuple):
        return output[0]
    return output


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
    if spec.component == "result":
        return compute_attention_result_activation(
            activation,
            model,
            spec,
            module=module,
            component_ref=component_ref,
            architecture=architecture,
        )
    if spec.activation == "split_heads":
        return split_heads(activation, head_count_for_component(model, spec.component))
    if spec.activation == "split_qkv_heads":
        return split_qkv_heads(activation, model, spec)
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
    n_heads = head_count_for_component(model, "z")
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


def add_values(left: Any, right: Any) -> Any:
    try:
        if hasattr(left, "shape") or hasattr(right, "shape"):
            return left + right
    except Exception:
        pass
    if isinstance(left, list) and isinstance(right, list):
        return [add_values(left_item, right_item) for left_item, right_item in zip(left, right)]
    return left + right


def subtract_values(left: Any, right: Any) -> Any:
    try:
        if hasattr(left, "shape") or hasattr(right, "shape"):
            return left - right
    except Exception:
        pass
    if isinstance(left, list) and isinstance(right, list):
        return [
            subtract_values(left_item, right_item)
            for left_item, right_item in zip(left, right)
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
    if isinstance(value, list):
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
    return activation


def split_heads(activation: Any, n_heads: int) -> Any:
    """Reshape `[batch, pos, hidden]` activations into `[batch, pos, head, head_dim]`."""
    shape = getattr(activation, "shape", None)
    reshape = getattr(activation, "reshape", None)
    if shape is None or not callable(reshape):
        if not isinstance(activation, list):
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
        if not isinstance(activation, list):
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
    component = spec.component
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
    component = spec.component
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
        if not isinstance(activation, list):
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
    if isinstance(qkv, list):
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
    if isinstance(qkv, list):
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
        if not isinstance(activation, list):
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
            raise ValueError(
                f"Expected {expected_heads} query heads, got {len(value)}."
            )
        return [
            [list(head) for head in value[group * q_per_group : (group + 1) * q_per_group]]
            for group in range(kv_heads)
        ]
    return [
        _split_nested_grouped_query_heads(item, kv_heads, q_per_group) for item in value
    ]


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
    weight: list[Any],
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
    weight: list[Any],
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
    if isinstance(value, list):
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


def _build_nested_from_shape(shape: tuple[int, ...], value_fn: Callable[[tuple[int, ...]], Any]) -> Any:
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
    config = getattr(model, "config", None)
    for name in ("num_attention_heads", "n_head", "n_heads", "num_heads"):
        value = getattr(config, name, None)
        if value is not None:
            return int(value)
    return None


def key_value_head_count(model: Any) -> int | None:
    """Read the configured key/value head count when it differs from query heads."""
    config = getattr(model, "config", None)
    if _is_falcon_multi_query_config(config):
        return 1
    for name in ("num_key_value_heads", "num_kv_heads", "n_head_kv"):
        value = getattr(config, name, None)
        if value is not None:
            return int(value)
    return None


def _is_falcon_multi_query_config(config: Any) -> bool:
    """Falcon MQA packs one shared K/V head even when num_kv_heads defaults to n_heads."""
    if str(getattr(config, "model_type", "")).lower() != "falcon":
        return False
    if bool(getattr(config, "new_decoder_architecture", False)):
        return False
    return bool(getattr(config, "multi_query", False))


def reshape_attention_weight(
    weight: Any,
    *,
    component: str,
    n_heads: int,
    packed_axis: int | None = 0,
) -> Any:
    """Convert HF linear weights to TransformerLens attention weight shapes."""
    shape = getattr(weight, "shape", None)
    reshape = getattr(weight, "reshape", None)
    if shape is None or not callable(reshape) or len(shape) != 2:
        if not isinstance(weight, list):
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
    if component == "z":
        return bias
    shape = getattr(bias, "shape", None)
    reshape = getattr(bias, "reshape", None)
    if shape is None or not callable(reshape):
        if not isinstance(bias, list):
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
    if isinstance(bias, list):
        if q_heads == kv_heads:
            component_index = {"q": 0, "k": 1, "v": 2}[component]
            view = _reshape_flat_list(list(bias), (q_heads, 3, head_dim))
            return _flatten_nested(_select_nested_axis(view, 1, component_index)), q_heads

        q_per_group = qkv_group_size(q_heads=q_heads, kv_heads=kv_heads)
        view = _reshape_flat_list(list(bias), (kv_heads, q_per_group + 2, head_dim))
        if component == "q":
            return _flatten_nested(_select_nested_axis_slice(view, 1, slice(0, q_per_group))), q_heads
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
    n_heads = head_count_for_component(model, component) if component != "z" else None
    d_model = _model_hidden_size(model)
    if d_model is None:
        raise ValueError(f"Could not infer hidden size for b_{component.upper()}.")
    if component == "z":
        return _zeros_vector(d_model, model)
    if n_heads is None or n_heads <= 0 or d_model % n_heads != 0:
        raise ValueError(
            f"Could not infer head dimension for b_{component.upper()} with "
            f"d_model={d_model}, n_heads={n_heads}."
        )
    return _zeros_matrix(n_heads, d_model // n_heads, model)


def _model_hidden_size(model: Any) -> int | None:
    config = getattr(model, "config", None)
    for name in ("hidden_size", "n_embd", "d_model", "dim"):
        value = getattr(config, name, None)
        if value is not None:
            return int(value)
    return None


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
        if not isinstance(weight, list):
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
        if isinstance(weight, list):
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
        if isinstance(weight, list):
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
    if isinstance(weight, list):
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
    if isinstance(weight, list):
        if q_heads == kv_heads:
            component_index = {"q": 0, "k": 1, "v": 2}[component]
            view = _reshape_flat_list(_flatten_nested(weight), (d_model, q_heads, 3, head_dim))
            return _flatten_nested_last_dims(
                _select_nested_axis(view, 2, component_index)
            ), q_heads

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
    state.records.append(record)
    return _AttentionSoftmaxHookHandle(state, record)


def _looks_like_attention_scores(
    input_tensor: Any,
    softmax_args: tuple[Any, ...],
    softmax_kwargs: dict[str, Any],
) -> bool:
    ndim = getattr(input_tensor, "ndim", None)
    if ndim is None or int(ndim) < 3:
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


def _find_attention_pattern(value: Any) -> Any | None:
    shape = getattr(value, "shape", None)
    ndim = getattr(value, "ndim", None)
    if shape is not None and ndim is not None and int(ndim) >= 4:
        return value
    if isinstance(value, dict):
        for key in ("attentions", "attention_weights", "attn_weights", "weights"):
            if key in value:
                found = _find_attention_pattern(value[key])
                if found is not None:
                    return found
        for item in value.values():
            found = _find_attention_pattern(item)
            if found is not None:
                return found
    if isinstance(value, tuple | list):
        for item in value:
            found = _find_attention_pattern(item)
            if found is not None:
                return found
    return None


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


def _normalize_component(component: str, *, layer_type: str | None = None) -> str:
    normalized = component.removeprefix("hook_")
    if normalized == "attn":
        return "pattern"
    if normalized == "scale":
        return "ln_scale"
    if layer_type == "attn" and normalized == "out":
        return "attn_out"
    if layer_type == "mlp" and normalized == "out":
        return "mlp_out"
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
    )


def _pattern_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec(
        "pattern",
        "forward_output",
        *module_paths,
        value="attention_pattern",
        patchable=True,
        cacheable=True,
    )


def _scores_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec(
        "attn_scores",
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


def _result_spec(*module_paths: str) -> ComponentHookSpec:
    return _spec(
        "result",
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
        "olmo",
        "olmo2",
        "olmoe",
        "phi3",
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
        _spec("resid_pre", "forward_input", "model.layers.{layer}"),
        _spec("resid_mid", "forward_input", "model.layers.{layer}.post_attention_layernorm"),
        _spec("resid_post", "forward_output", "model.layers.{layer}"),
        _spec("attn_out", "forward_output", "model.layers.{layer}.self_attn.o_proj"),
        _spec("mlp_out", "forward_output", "model.layers.{layer}.mlp"),
        _mlp_pre_spec("model.layers.{layer}.mlp.gate_proj", "model.layers.{layer}.mlp.up_proj"),
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
    ),
    notes=("Covers RoPE decoder families with model.layers and q/k/v/o projections.",),
)

GPT2_ADAPTER = ArchitectureAdapter(
    name="gpt2_decoder",
    model_types=("gpt2",),
    model_name_markers=("gpt2", "distilgpt2"),
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
    ),
    notes=("GPT-2 stores q/k/v in a joint c_attn projection; hooks see the joint tensor.",),
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
    model_name_markers=("gpt-neo",),
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
        _spec("mlp_out", "forward_output", "transformer.blocks.{layer}.ffn"),
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
        _result_spec("model.layers.{layer}.self_attn.dense", "model.layers.{layer}.self_attn.o_proj"),
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
        _result_spec("encoder.layer.{layer}.attention.output.dense", "bert.encoder.layer.{layer}.attention.output.dense"),
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
        _spec("resid_pre", "forward_input", "encoder.block.{layer}"),
        _spec("resid_mid", "forward_input", "encoder.block.{layer}.layer.1"),
        _spec("resid_post", "forward_output", "encoder.block.{layer}"),
        _spec("attn_out", "forward_output", "encoder.block.{layer}.layer.0.SelfAttention.o"),
        _spec("mlp_out", "forward_output", "encoder.block.{layer}.layer.1.DenseReluDense"),
        _spec(
            "q",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention.q",
            activation="split_heads",
        ),
        _spec(
            "k",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention.k",
            activation="split_heads",
        ),
        _spec(
            "v",
            "forward_output",
            "encoder.block.{layer}.layer.0.SelfAttention.v",
            activation="split_heads",
        ),
        _spec(
            "z",
            "forward_input",
            "encoder.block.{layer}.layer.0.SelfAttention.o",
            activation="split_heads",
        ),
        _result_spec("encoder.block.{layer}.layer.0.SelfAttention.o"),
        _pattern_spec("encoder.block.{layer}.layer.0.SelfAttention"),
        _scores_spec("encoder.block.{layer}.layer.0.SelfAttention"),
    ),
    notes=(
        "Initial bridge targets the encoder stack; decoder/cross-attention "
        "can be added as separate component families.",
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
    LLAMA_LIKE_ADAPTER,
    GPT2_ADAPTER,
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
