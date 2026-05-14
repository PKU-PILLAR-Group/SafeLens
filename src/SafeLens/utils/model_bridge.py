"""Architecture bridge primitives for Transformers-backed model adapters.

The design mirrors the useful part of TransformerLens' model bridge: keep model
loading provider-specific, but map each model family into a small canonical
component vocabulary that SafeLens hooks and patching code can target.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Any, Literal

from SafeLens.core.base import HookFn, LayerRef

HookMode = Literal["forward_output", "forward_input"]
ComponentValue = Literal["output", "attention_pattern", "attention_scores"]

CANONICAL_TRANSFORMER_COMPONENTS: tuple[str, ...] = (
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
)

_UNSUPPORTED_ATTENTION_REASON = (
    "this fallback adapter has no known attention module path for softmax instrumentation"
)


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


@dataclass(frozen=True)
class ComponentHookSpec:
    """How one canonical component maps to a HuggingFace module path."""

    component: str
    mode: HookMode
    module_paths: tuple[str, ...]
    value: ComponentValue = "output"
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

    def supported_components(self, *, include_unsupported: bool = False) -> tuple[str, ...]:
        return tuple(
            spec.component for spec in self._specs.values() if include_unsupported or spec.supported
        )

    def inspect(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_types": list(self.model_types),
            "model_name_markers": list(self.model_name_markers),
            "supported_components": list(self.supported_components()),
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
        if spec.mode == "forward_input":
            return module.register_forward_pre_hook(
                _make_component_input_hook(hook_fn, component_ref, self.name)
            )
        return module.register_forward_hook(
            _make_component_output_hook(hook_fn, component_ref, self.name, spec)
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

    def _make_ref(self, layer: int, component: str, original: LayerRef) -> ComponentRef | None:
        normalized = _normalize_component(component)
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


def transformer_lens_component_name(component: str, layer: int) -> str:
    """Return a TransformerLens-style hook name for a canonical component."""
    if component in {"q", "k", "v", "z", "pattern", "attn_scores", "result"}:
        hook_component = "attn_scores" if component == "attn_scores" else component
        return f"blocks.{layer}.attn.hook_{hook_component}"
    if component in {"pre", "post"}:
        return f"blocks.{layer}.mlp.hook_{component}"
    return f"blocks.{layer}.hook_{component}"


def supported_transformer_component_names(
    *,
    include_pattern: bool = False,
    include_attention: bool = False,
) -> tuple[str, ...]:
    """Return the canonical component vocabulary exposed by model bridges."""
    if include_attention:
        return CANONICAL_TRANSFORMER_COMPONENTS
    if include_pattern:
        return tuple(
            component
            for component in CANONICAL_TRANSFORMER_COMPONENTS
            if component != "attn_scores"
        )
    return tuple(
        component
        for component in CANONICAL_TRANSFORMER_COMPONENTS
        if component not in {"pattern", "attn_scores"}
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
) -> Callable[[Any, Any, Any], Any]:
    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        activation = extract_component_activation(output, spec)
        patched = call_component_hook(
            hook_fn,
            activation=activation,
            component_ref=component_ref,
            architecture=architecture,
        )
        if spec.value != "output":
            return None
        return output if patched is None else patched

    return hook


def _make_component_input_hook(
    hook_fn: HookFn,
    component_ref: ComponentRef,
    architecture: str,
) -> Callable[[Any, Any], Any]:
    def hook(_module: Any, inputs: Any) -> Any:
        if not inputs:
            return None
        activation = inputs[0]
        patched = call_component_hook(
            hook_fn,
            activation=activation,
            component_ref=component_ref,
            architecture=architecture,
        )
        if patched is None:
            return None
        return (patched, *tuple(inputs[1:]))

    return hook


def call_component_hook(
    hook_fn: HookFn,
    *,
    activation: Any,
    component_ref: ComponentRef,
    architecture: str,
) -> Any:
    """Call a user hook with SafeLens component metadata when accepted."""
    hook_kwargs = {
        "activation": activation,
        "output": activation,
        "component": component_ref.component,
        "layer": component_ref.layer,
        "hook_name": component_ref.safelens_name,
        "transformer_lens_name": component_ref.transformer_lens_name,
        "architecture": architecture,
        "hook": None,
    }
    try:
        hook_signature = signature(hook_fn)
    except (TypeError, ValueError):
        return hook_fn(activation, None)

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
        return hook_fn(activation)


def extract_component_activation(output: Any, spec: ComponentHookSpec) -> Any:
    """Extract the activation value for a component from a module hook output."""
    if spec.value == "output":
        return output
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

    original_forward = module.forward

    def wrapped_forward(*args: Any, **kwargs: Any) -> Any:
        original_torch_softmax = torch.softmax
        original_functional_softmax = functional.softmax
        captured = False

        def make_instrumented_softmax(original_softmax: Callable[..., Any]) -> Callable[..., Any]:
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
                if spec.value == "attention_scores":
                    patched_scores = call_component_hook(
                        hook_fn,
                        activation=scores,
                        component_ref=component_ref,
                        architecture=architecture,
                    )
                    if patched_scores is not None:
                        scores = patched_scores
                pattern = original_softmax(scores, *softmax_args, **softmax_kwargs)
                if spec.value == "attention_pattern":
                    patched_pattern = call_component_hook(
                        hook_fn,
                        activation=pattern,
                        component_ref=component_ref,
                        architecture=architecture,
                    )
                    if patched_pattern is not None:
                        return patched_pattern
                return pattern

            return instrumented_softmax

        torch.softmax = make_instrumented_softmax(original_torch_softmax)
        functional.softmax = make_instrumented_softmax(original_functional_softmax)
        try:
            output = original_forward(*args, **kwargs)
        finally:
            torch.softmax = original_torch_softmax
            functional.softmax = original_functional_softmax

        if not captured:
            raise RuntimeError(
                f"Attention instrumentation for {component_ref.safelens_name!r} did not "
                "observe an attention-shaped Python torch.softmax call. Use an eager "
                "attention implementation or a model adapter with explicit attention "
                "forward instrumentation."
            )
        return output

    module.forward = wrapped_forward
    return _ForwardPatchHandle(module, original_forward, wrapped_forward)


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
    if layer_type == "mlp" and normalized in {"pre", "post"}:
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
        _spec("q", "forward_output", "model.layers.{layer}.self_attn.q_proj"),
        _spec("k", "forward_output", "model.layers.{layer}.self_attn.k_proj"),
        _spec("v", "forward_output", "model.layers.{layer}.self_attn.v_proj"),
        _spec("z", "forward_input", "model.layers.{layer}.self_attn.o_proj"),
        _spec("result", "forward_output", "model.layers.{layer}.self_attn.o_proj"),
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
        _spec("q", "forward_output", "transformer.h.{layer}.attn.c_attn"),
        _spec("k", "forward_output", "transformer.h.{layer}.attn.c_attn"),
        _spec("v", "forward_output", "transformer.h.{layer}.attn.c_attn"),
        _spec("z", "forward_input", "transformer.h.{layer}.attn.c_proj"),
        _spec("result", "forward_output", "transformer.h.{layer}.attn.c_proj"),
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
        _spec(
            "q",
            "forward_output",
            "gpt_neox.layers.{layer}.attention.query_key_value",
        ),
        _spec("k", "forward_output", "gpt_neox.layers.{layer}.attention.query_key_value"),
        _spec("v", "forward_output", "gpt_neox.layers.{layer}.attention.query_key_value"),
        _spec("z", "forward_input", "gpt_neox.layers.{layer}.attention.dense"),
        _spec("result", "forward_output", "gpt_neox.layers.{layer}.attention.dense"),
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
        _spec("q", "forward_output", "transformer.h.{layer}.attn.q_proj"),
        _spec("k", "forward_output", "transformer.h.{layer}.attn.k_proj"),
        _spec("v", "forward_output", "transformer.h.{layer}.attn.v_proj"),
        _spec("z", "forward_input", "transformer.h.{layer}.attn.out_proj"),
        _spec("result", "forward_output", "transformer.h.{layer}.attn.out_proj"),
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
        _spec("q", "forward_output", "transformer.h.{layer}.attn.attention.q_proj"),
        _spec("k", "forward_output", "transformer.h.{layer}.attn.attention.k_proj"),
        _spec("v", "forward_output", "transformer.h.{layer}.attn.attention.v_proj"),
        _spec("z", "forward_input", "transformer.h.{layer}.attn.attention.out_proj"),
        _spec("result", "forward_output", "transformer.h.{layer}.attn.attention.out_proj"),
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
        _spec("resid_mid", "forward_input", "transformer.h.{layer}.post_attention_layernorm"),
        _spec("resid_post", "forward_output", "transformer.h.{layer}"),
        _spec(
            "attn_out",
            "forward_output",
            "transformer.h.{layer}.self_attention.dense",
        ),
        _spec("mlp_out", "forward_output", "transformer.h.{layer}.mlp"),
        _spec("q", "forward_output", "transformer.h.{layer}.self_attention.query_key_value"),
        _spec("k", "forward_output", "transformer.h.{layer}.self_attention.query_key_value"),
        _spec("v", "forward_output", "transformer.h.{layer}.self_attention.query_key_value"),
        _spec(
            "z",
            "forward_input",
            "transformer.h.{layer}.self_attention.dense",
        ),
        _spec(
            "result",
            "forward_output",
            "transformer.h.{layer}.self_attention.dense",
        ),
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
        _spec("q", "forward_output", "transformer.blocks.{layer}.attn.Wqkv"),
        _spec("k", "forward_output", "transformer.blocks.{layer}.attn.Wqkv"),
        _spec("v", "forward_output", "transformer.blocks.{layer}.attn.Wqkv"),
        _spec("z", "forward_input", "transformer.blocks.{layer}.attn.out_proj"),
        _spec("result", "forward_output", "transformer.blocks.{layer}.attn.out_proj"),
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
        _spec("q", "forward_output", "model.layers.{layer}.self_attn.q_proj"),
        _spec("k", "forward_output", "model.layers.{layer}.self_attn.k_proj"),
        _spec("v", "forward_output", "model.layers.{layer}.self_attn.v_proj"),
        _spec(
            "z",
            "forward_input",
            "model.layers.{layer}.self_attn.dense",
            "model.layers.{layer}.self_attn.o_proj",
        ),
        _spec(
            "result",
            "forward_output",
            "model.layers.{layer}.self_attn.dense",
            "model.layers.{layer}.self_attn.o_proj",
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
        _spec("q", "forward_output", "model.decoder.layers.{layer}.self_attn.q_proj"),
        _spec("k", "forward_output", "model.decoder.layers.{layer}.self_attn.k_proj"),
        _spec("v", "forward_output", "model.decoder.layers.{layer}.self_attn.v_proj"),
        _spec("z", "forward_input", "model.decoder.layers.{layer}.self_attn.out_proj"),
        _spec("result", "forward_output", "model.decoder.layers.{layer}.self_attn.out_proj"),
        _pattern_spec("model.decoder.layers.{layer}.self_attn"),
        _scores_spec("model.decoder.layers.{layer}.self_attn"),
    ),
)

BERT_ADAPTER = ArchitectureAdapter(
    name="bert_encoder",
    model_types=("bert",),
    model_name_markers=("bert-", "google-bert/"),
    component_specs=(
        _spec("resid_pre", "forward_input", "bert.encoder.layer.{layer}"),
        _spec("resid_mid", "forward_input", "bert.encoder.layer.{layer}.intermediate"),
        _spec("resid_post", "forward_output", "bert.encoder.layer.{layer}"),
        _spec("attn_out", "forward_output", "bert.encoder.layer.{layer}.attention.output.dense"),
        _spec("mlp_out", "forward_output", "bert.encoder.layer.{layer}.output.dense"),
        _spec("q", "forward_output", "bert.encoder.layer.{layer}.attention.self.query"),
        _spec("k", "forward_output", "bert.encoder.layer.{layer}.attention.self.key"),
        _spec("v", "forward_output", "bert.encoder.layer.{layer}.attention.self.value"),
        _spec("z", "forward_input", "bert.encoder.layer.{layer}.attention.output.dense"),
        _spec("result", "forward_output", "bert.encoder.layer.{layer}.attention.output.dense"),
        _pattern_spec("bert.encoder.layer.{layer}.attention.self"),
        _scores_spec("bert.encoder.layer.{layer}.attention.self"),
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
        _spec("q", "forward_output", "encoder.block.{layer}.layer.0.SelfAttention.q"),
        _spec("k", "forward_output", "encoder.block.{layer}.layer.0.SelfAttention.k"),
        _spec("v", "forward_output", "encoder.block.{layer}.layer.0.SelfAttention.v"),
        _spec("z", "forward_input", "encoder.block.{layer}.layer.0.SelfAttention.o"),
        _spec("result", "forward_output", "encoder.block.{layer}.layer.0.SelfAttention.o"),
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
    BERT_ADAPTER,
    T5_ENCODER_ADAPTER,
)
