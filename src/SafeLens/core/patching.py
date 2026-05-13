"""Generic and component-level activation patching primitives."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import Any, Literal

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper
from SafeLens.core.hooks import (
    ActivationCache,
    activation_name_for_layer,
    clone_activation,
    extract_hook_output,
    has_hook_output,
    temporary_hooks,
)

PatchMode = Literal["replace", "add"]
PatchMetric = Callable[[Any], float]
PatchSetter = Callable[[Any, "PatchSpec", ActivationCache], Any]
AxisName = Literal["layer", "pos", "head_index", "head", "src_pos", "dest_pos"]
ActivationNameStyle = Literal["safelens", "transformer_lens"]

FULL_SLICE = slice(None)

TRANSFORMER_LENS_ACTIVATION_TEMPLATES = {
    "resid_pre": "blocks.{layer}.hook_resid_pre",
    "resid_mid": "blocks.{layer}.hook_resid_mid",
    "resid_post": "blocks.{layer}.hook_resid_post",
    "attn_out": "blocks.{layer}.hook_attn_out",
    "mlp_out": "blocks.{layer}.hook_mlp_out",
    "q": "blocks.{layer}.attn.hook_q",
    "k": "blocks.{layer}.attn.hook_k",
    "v": "blocks.{layer}.attn.hook_v",
    "z": "blocks.{layer}.attn.hook_z",
    "result": "blocks.{layer}.attn.hook_result",
    "pattern": "blocks.{layer}.attn.hook_pattern",
    "attn_scores": "blocks.{layer}.attn.hook_attn_scores",
}


@dataclass(frozen=True)
class PatchSpec:
    """Specification for one activation patch operation."""

    layer: LayerRef
    activation_name: str | None = None
    source_name: str | None = None
    target_index: Any = None
    source_index: Any = None
    mode: PatchMode = "replace"
    scale: float = 1.0
    value: Any = None
    setter: PatchSetter | None = None

    @property
    def target_name(self) -> str:
        """Activation name to patch in the corrupted run."""
        return self.activation_name or activation_name_for_layer(self.layer)

    @property
    def clean_name(self) -> str:
        """Activation name to read from the clean cache."""
        return self.source_name or self.target_name


@dataclass(frozen=True)
class PatchResult:
    """Result of one patched forward run."""

    spec: PatchSpec
    metric: float
    output: Any
    cache: dict[str, Any]


def activation_name_for_component(
    component: str,
    layer: LayerRef,
    *,
    name_style: ActivationNameStyle = "safelens",
    name_template: str | None = None,
) -> str:
    """Return a cache/hook name for a Transformer component at one layer."""
    if name_template is not None:
        return name_template.format(layer=layer, component=component)
    if name_style == "transformer_lens":
        template = TRANSFORMER_LENS_ACTIVATION_TEMPLATES.get(
            component,
            "blocks.{layer}.hook_{component}",
        )
        return template.format(layer=layer, component=component)
    return f"{activation_name_for_layer(layer)}.{component}"


def get_patch_value(spec: PatchSpec, clean_cache: ActivationCache) -> Any:
    """Read the patch value from an explicit value or the clean activation cache."""
    source = spec.value if spec.value is not None else clean_cache[spec.clean_name]
    source_index = spec.source_index if spec.source_index is not None else spec.target_index
    if source_index is None:
        return source
    return get_indexed(source, source_index)


def replace_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Replace the whole activation or a slice with the clean activation value."""
    patch_value = get_patch_value(spec, clean_cache)
    if spec.target_index is None:
        return patch_value

    patched = clone_activation(corrupted_activation)
    set_indexed(patched, spec.target_index, patch_value)
    return patched


def add_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Add a scaled patch value to the whole activation or to a selected slice."""
    patch_value = scale_value(get_patch_value(spec, clean_cache), spec.scale)

    if spec.target_index is None:
        return add_values(corrupted_activation, patch_value)

    patched = clone_activation(corrupted_activation)
    current_value = get_indexed(patched, spec.target_index)
    set_indexed(patched, spec.target_index, add_values(current_value, patch_value))
    return patched


def apply_patch(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Apply a patch spec to one corrupted activation."""
    if spec.setter is not None:
        return spec.setter(corrupted_activation, spec, clean_cache)
    if spec.mode == "replace":
        return replace_patch_setter(corrupted_activation, spec, clean_cache)
    if spec.mode == "add":
        return add_patch_setter(corrupted_activation, spec, clean_cache)
    raise ValueError(f"Unsupported patch mode: {spec.mode}")


def make_patch_hook(spec: PatchSpec, clean_cache: ActivationCache) -> HookFn:
    """Create a hook function that applies a patch to the current activation."""

    def patch_hook(*args: Any, **kwargs: Any) -> Any:
        if not has_hook_output(args, kwargs):
            return None
        activation = extract_hook_output(args, kwargs)
        return apply_patch(activation, spec, clean_cache)

    return patch_hook


def run_activation_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    spec: PatchSpec,
    metric: PatchMetric,
    *,
    layers: Sequence[LayerRef] | None = None,
) -> PatchResult:
    """Run one patched corrupted forward pass and score it with a metric."""
    with temporary_hooks(model, [(spec.layer, make_patch_hook(spec, clean_cache))]):
        output, cache = model.run_with_cache(corrupted_batch, layers=layers)
    return PatchResult(spec=spec, metric=float(metric(output)), output=output, cache=cache)


def generic_activation_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    specs: Iterable[PatchSpec],
    metric: PatchMetric,
    *,
    layers: Sequence[LayerRef] | None = None,
) -> list[PatchResult]:
    """Run a sequence of activation patches, similar to TransformerLens' generic patcher."""
    return [
        run_activation_patch(
            model,
            corrupted_batch,
            clean_cache,
            spec,
            metric,
            layers=layers,
        )
        for spec in specs
    ]


def make_patch_specs(
    layers: Iterable[LayerRef],
    *,
    activation_name: str | None = None,
    target_indices: Iterable[Any] | None = None,
    mode: PatchMode = "replace",
    scale: float = 1.0,
) -> list[PatchSpec]:
    """Create a simple grid of patch specs over layers and optional target indices."""
    indices = list(target_indices) if target_indices is not None else [None]
    return [
        PatchSpec(
            layer=layer,
            activation_name=activation_name,
            target_index=index,
            mode=mode,
            scale=scale,
        )
        for layer in layers
        for index in indices
    ]


def make_component_patch_specs(
    layers: Iterable[LayerRef],
    component: str,
    index_axis_names: Sequence[AxisName],
    axis_values: Mapping[AxisName, Iterable[int]],
    *,
    patch_setter: PatchSetter,
    mode: PatchMode = "replace",
    scale: float = 1.0,
    name_style: ActivationNameStyle = "safelens",
    name_template: str | None = None,
) -> list[PatchSpec]:
    """Create component-level patch specs using TransformerLens-style index axes."""
    layer_values = list(layers)
    non_layer_axis_names = [name for name in index_axis_names if name != "layer"]
    non_layer_values = [_axis_values(axis_values, name) for name in non_layer_axis_names]
    specs: list[PatchSpec] = []

    for layer in layer_values:
        activation_name = activation_name_for_component(
            component,
            layer,
            name_style=name_style,
            name_template=name_template,
        )
        for axis_index in product(*non_layer_values):
            index_parts: list[Any] = []
            axis_lookup = dict(zip(non_layer_axis_names, axis_index, strict=True))
            for axis_name in index_axis_names:
                if axis_name == "layer":
                    index_parts.append(layer)
                else:
                    index_parts.append(axis_lookup[axis_name])
            specs.append(
                PatchSpec(
                    layer=activation_name,
                    activation_name=activation_name,
                    target_index=tuple(index_parts),
                    mode=mode,
                    scale=scale,
                    setter=patch_setter,
                )
            )

    return specs


def component_activation_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    *,
    component: str,
    patch_setter: PatchSetter,
    index_axis_names: Sequence[AxisName],
    layers: Iterable[LayerRef] | None = None,
    positions: Iterable[int] | None = None,
    heads: Iterable[int] | None = None,
    dest_positions: Iterable[int] | None = None,
    source_positions: Iterable[int] | None = None,
    mode: PatchMode = "replace",
    scale: float = 1.0,
    name_style: ActivationNameStyle = "safelens",
    name_template: str | None = None,
    cache_layers: Sequence[LayerRef] | None = None,
) -> list[PatchResult]:
    """Run a component-level activation patch grid."""
    layer_values = list(
        layers
        if layers is not None
        else infer_layers(model, clean_cache, component, name_style=name_style)
    )
    axis_values: dict[AxisName, Iterable[int]] = {}
    if "pos" in index_axis_names:
        axis_values["pos"] = _values_or_range(
            positions,
            infer_positions(corrupted_batch, clean_cache, component, layer_values),
            "positions",
        )
    if "head" in index_axis_names:
        axis_values["head"] = _values_or_range(
            heads,
            infer_heads(model, clean_cache, component, layer_values),
            "heads",
        )
    if "head_index" in index_axis_names:
        axis_values["head_index"] = _values_or_range(
            heads,
            infer_heads(model, clean_cache, component, layer_values),
            "heads",
        )
    if "dest_pos" in index_axis_names:
        axis_values["dest_pos"] = _values_or_range(
            dest_positions,
            infer_positions(corrupted_batch, clean_cache, component, layer_values),
            "dest_positions",
        )
    if "src_pos" in index_axis_names:
        axis_values["src_pos"] = _values_or_range(
            source_positions,
            infer_positions(corrupted_batch, clean_cache, component, layer_values),
            "source_positions",
        )
    specs = make_component_patch_specs(
        layer_values,
        component,
        index_axis_names,
        axis_values,
        patch_setter=patch_setter,
        mode=mode,
        scale=scale,
        name_style=name_style,
        name_template=name_template,
    )
    return generic_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        specs,
        metric,
        layers=cache_layers,
    )


def layer_pos_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Patch activations shaped `[batch, pos, ...]` at one layer and position."""
    index = require_patch_index(spec, 2, "layer_pos_patch_setter")
    source_index = source_index_or_target(spec, index)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=(FULL_SLICE, index[1]),
        source_slice=(FULL_SLICE, source_index[1]),
    )


def layer_pos_head_vector_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Patch head vector activations shaped `[batch, pos, head, ...]`."""
    index = require_patch_index(spec, 3, "layer_pos_head_vector_patch_setter")
    source_index = source_index_or_target(spec, index)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=(FULL_SLICE, index[1], index[2]),
        source_slice=(FULL_SLICE, source_index[1], source_index[2]),
    )


def layer_head_vector_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Patch a head vector across all positions for `[batch, pos, head, ...]`."""
    index = require_patch_index(spec, 2, "layer_head_vector_patch_setter")
    source_index = source_index_or_target(spec, index)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=(FULL_SLICE, FULL_SLICE, index[1]),
        source_slice=(FULL_SLICE, FULL_SLICE, source_index[1]),
    )


def layer_head_pattern_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Patch an attention pattern head shaped `[batch, head, dest_pos, src_pos]`."""
    index = require_patch_index(spec, 2, "layer_head_pattern_patch_setter")
    source_index = source_index_or_target(spec, index)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=(FULL_SLICE, index[1], FULL_SLICE, FULL_SLICE),
        source_slice=(FULL_SLICE, source_index[1], FULL_SLICE, FULL_SLICE),
    )


def layer_head_pos_pattern_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Patch one destination position in an attention pattern."""
    index = require_patch_index(spec, 3, "layer_head_pos_pattern_patch_setter")
    source_index = source_index_or_target(spec, index)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=(FULL_SLICE, index[1], index[2], FULL_SLICE),
        source_slice=(FULL_SLICE, source_index[1], source_index[2], FULL_SLICE),
    )


def layer_head_dest_src_pos_pattern_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
) -> Any:
    """Patch one `(destination, source)` entry in an attention pattern."""
    index = require_patch_index(
        spec,
        4,
        "layer_head_dest_src_pos_pattern_patch_setter",
    )
    source_index = source_index_or_target(spec, index)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=(FULL_SLICE, index[1], index[2], index[3]),
        source_slice=(FULL_SLICE, source_index[1], source_index[2], source_index[3]),
    )


def get_act_patch_resid_pre(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch residual stream activations at the start of each block by position."""
    return _layer_pos_component_patch(
        model, corrupted_batch, clean_cache, metric, "resid_pre", kwargs
    )


def get_act_patch_resid_mid(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch residual stream activations between attention and MLP by position."""
    return _layer_pos_component_patch(
        model, corrupted_batch, clean_cache, metric, "resid_mid", kwargs
    )


def get_act_patch_resid_post(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch residual stream activations at the end of each block by position."""
    return _layer_pos_component_patch(
        model, corrupted_batch, clean_cache, metric, "resid_post", kwargs
    )


def get_act_patch_attn_out(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention layer outputs by position."""
    return _layer_pos_component_patch(
        model, corrupted_batch, clean_cache, metric, "attn_out", kwargs
    )


def get_act_patch_mlp_out(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch MLP layer outputs by position."""
    return _layer_pos_component_patch(
        model, corrupted_batch, clean_cache, metric, "mlp_out", kwargs
    )


def get_act_patch_attn_head_out_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention head outputs `z` by layer, position, and head."""
    return _head_vector_by_pos_patch(model, corrupted_batch, clean_cache, metric, "z", kwargs)


def get_act_patch_attn_head_q_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention queries by layer, position, and head."""
    return _head_vector_by_pos_patch(model, corrupted_batch, clean_cache, metric, "q", kwargs)


def get_act_patch_attn_head_k_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention keys by layer, position, and head."""
    return _head_vector_by_pos_patch(model, corrupted_batch, clean_cache, metric, "k", kwargs)


def get_act_patch_attn_head_v_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention values by layer, position, and head."""
    return _head_vector_by_pos_patch(model, corrupted_batch, clean_cache, metric, "v", kwargs)


def get_act_patch_attn_head_result_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch per-head attention result vectors by layer, position, and head."""
    return _head_vector_by_pos_patch(model, corrupted_batch, clean_cache, metric, "result", kwargs)


def get_act_patch_attn_head_out_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention head outputs `z` across all positions."""
    return _head_vector_all_pos_patch(model, corrupted_batch, clean_cache, metric, "z", kwargs)


def get_act_patch_attn_head_q_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention queries across all positions."""
    return _head_vector_all_pos_patch(model, corrupted_batch, clean_cache, metric, "q", kwargs)


def get_act_patch_attn_head_k_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention keys across all positions."""
    return _head_vector_all_pos_patch(model, corrupted_batch, clean_cache, metric, "k", kwargs)


def get_act_patch_attn_head_v_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention values across all positions."""
    return _head_vector_all_pos_patch(model, corrupted_batch, clean_cache, metric, "v", kwargs)


def get_act_patch_attn_head_result_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch per-head attention result vectors across all positions."""
    return _head_vector_all_pos_patch(model, corrupted_batch, clean_cache, metric, "result", kwargs)


def get_act_patch_attn_head_pattern_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch full attention patterns by layer and head."""
    return _head_pattern_patch(model, corrupted_batch, clean_cache, metric, "pattern", kwargs)


def get_act_patch_attn_head_pattern_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention patterns by layer, head, and destination position."""
    return _head_pattern_by_pos_patch(
        model, corrupted_batch, clean_cache, metric, "pattern", kwargs
    )


def get_act_patch_attn_head_pattern_dest_src_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch attention patterns by layer, head, destination, and source position."""
    return _head_pattern_dest_src_patch(
        model, corrupted_batch, clean_cache, metric, "pattern", kwargs
    )


def get_act_patch_attn_scores_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch raw attention scores by layer and head."""
    return _head_pattern_patch(model, corrupted_batch, clean_cache, metric, "attn_scores", kwargs)


def get_act_patch_attn_scores_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch raw attention scores by layer, head, and destination position."""
    return _head_pattern_by_pos_patch(
        model, corrupted_batch, clean_cache, metric, "attn_scores", kwargs
    )


def get_act_patch_attn_scores_dest_src_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> list[PatchResult]:
    """Patch raw attention scores by layer, head, destination, and source position."""
    return _head_pattern_dest_src_patch(
        model, corrupted_batch, clean_cache, metric, "attn_scores", kwargs
    )


def get_act_patch_block_every(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> dict[str, list[PatchResult]]:
    """Patch residual pre, attention output, and MLP output by layer and position."""
    return {
        "resid_pre": get_act_patch_resid_pre(model, corrupted_batch, clean_cache, metric, **kwargs),
        "attn_out": get_act_patch_attn_out(model, corrupted_batch, clean_cache, metric, **kwargs),
        "mlp_out": get_act_patch_mlp_out(model, corrupted_batch, clean_cache, metric, **kwargs),
    }


def get_act_patch_attn_head_all_pos_every(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> dict[str, list[PatchResult]]:
    """Patch `z`, `q`, `k`, `v`, and `pattern` by layer and head."""
    return {
        "z": get_act_patch_attn_head_out_all_pos(
            model,
            corrupted_batch,
            clean_cache,
            metric,
            **kwargs,
        ),
        "q": get_act_patch_attn_head_q_all_pos(
            model, corrupted_batch, clean_cache, metric, **kwargs
        ),
        "k": get_act_patch_attn_head_k_all_pos(
            model, corrupted_batch, clean_cache, metric, **kwargs
        ),
        "v": get_act_patch_attn_head_v_all_pos(
            model, corrupted_batch, clean_cache, metric, **kwargs
        ),
        "pattern": get_act_patch_attn_head_pattern_all_pos(
            model,
            corrupted_batch,
            clean_cache,
            metric,
            **kwargs,
        ),
    }


def get_act_patch_attn_head_by_pos_every(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    **kwargs: Any,
) -> dict[str, list[PatchResult]]:
    """Patch `z`, `q`, `k`, `v`, and `pattern` by position where applicable."""
    return {
        "z": get_act_patch_attn_head_out_by_pos(
            model,
            corrupted_batch,
            clean_cache,
            metric,
            **kwargs,
        ),
        "q": get_act_patch_attn_head_q_by_pos(
            model, corrupted_batch, clean_cache, metric, **kwargs
        ),
        "k": get_act_patch_attn_head_k_by_pos(
            model, corrupted_batch, clean_cache, metric, **kwargs
        ),
        "v": get_act_patch_attn_head_v_by_pos(
            model, corrupted_batch, clean_cache, metric, **kwargs
        ),
        "pattern": get_act_patch_attn_head_pattern_by_pos(
            model,
            corrupted_batch,
            clean_cache,
            metric,
            **kwargs,
        ),
    }


def _layer_pos_component_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    component: str,
    kwargs: dict[str, Any],
) -> list[PatchResult]:
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=layer_pos_patch_setter,
        index_axis_names=("layer", "pos"),
        **kwargs,
    )


def _head_vector_by_pos_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    component: str,
    kwargs: dict[str, Any],
) -> list[PatchResult]:
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=layer_pos_head_vector_patch_setter,
        index_axis_names=("layer", "pos", "head"),
        **kwargs,
    )


def _head_vector_all_pos_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    component: str,
    kwargs: dict[str, Any],
) -> list[PatchResult]:
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=layer_head_vector_patch_setter,
        index_axis_names=("layer", "head"),
        **kwargs,
    )


def _head_pattern_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    component: str,
    kwargs: dict[str, Any],
) -> list[PatchResult]:
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=layer_head_pattern_patch_setter,
        index_axis_names=("layer", "head_index"),
        **kwargs,
    )


def _head_pattern_by_pos_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    component: str,
    kwargs: dict[str, Any],
) -> list[PatchResult]:
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=layer_head_pos_pattern_patch_setter,
        index_axis_names=("layer", "head_index", "dest_pos"),
        **kwargs,
    )


def _head_pattern_dest_src_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    component: str,
    kwargs: dict[str, Any],
) -> list[PatchResult]:
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=layer_head_dest_src_pos_pattern_patch_setter,
        index_axis_names=("layer", "head_index", "dest_pos", "src_pos"),
        **kwargs,
    )


def require_patch_index(spec: PatchSpec, expected_length: int, setter_name: str) -> tuple[Any, ...]:
    """Return a normalized index tuple or raise a clear error."""
    index = normalize_index(spec.target_index)
    if len(index) != expected_length:
        raise ValueError(
            f"{setter_name} expects an index of length {expected_length}; got {index!r}."
        )
    return index


def source_index_or_target(spec: PatchSpec, target_index: tuple[Any, ...]) -> tuple[Any, ...]:
    """Return the source index if supplied, otherwise the target index."""
    if spec.source_index is None:
        return target_index
    source_index = normalize_index(spec.source_index)
    if len(source_index) != len(target_index):
        raise ValueError("source_index must have the same rank as target_index.")
    return source_index


def patch_slice(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache,
    *,
    target_slice: tuple[Any, ...],
    source_slice: tuple[Any, ...],
) -> Any:
    """Patch a target slice from the matching clean activation slice."""
    clean_activation = spec.value if spec.value is not None else clean_cache[spec.clean_name]
    patch_value = scale_value(get_indexed(clean_activation, source_slice), spec.scale)
    patched = clone_activation(corrupted_activation)
    if spec.mode == "replace":
        set_indexed(patched, target_slice, patch_value)
        return patched
    if spec.mode == "add":
        current_value = get_indexed(patched, target_slice)
        set_indexed(patched, target_slice, add_values(current_value, patch_value))
        return patched
    raise ValueError(f"Unsupported patch mode: {spec.mode}")


def normalize_index(index: Any) -> tuple[Any, ...]:
    """Normalize scalar/list/tuple indices to tuples."""
    if index is None:
        return ()
    if isinstance(index, tuple):
        return index
    if isinstance(index, list):
        return tuple(index)
    return (index,)


def get_indexed(value: Any, index: Any) -> Any:
    """Index tensor-like or nested-list values."""
    normalized = normalize_index(index)
    if len(normalized) == 1:
        try:
            return value[normalized[0]]
        except (TypeError, IndexError, KeyError):
            pass
    try:
        return value[normalized]
    except (TypeError, IndexError, KeyError):
        return get_nested(value, normalized)


def set_indexed(value: Any, index: Any, replacement: Any) -> None:
    """Assign into tensor-like or nested-list values."""
    normalized = normalize_index(index)
    if len(normalized) == 1:
        try:
            value[normalized[0]] = replacement
            return
        except (TypeError, IndexError, KeyError):
            pass
    try:
        value[normalized] = replacement
    except (TypeError, IndexError, KeyError):
        set_nested(value, normalized, replacement)


def get_nested(value: Any, index: tuple[Any, ...]) -> Any:
    """Index nested Python containers with full slices and integer indices."""
    if not index:
        return value
    head = index[0]
    tail = index[1:]
    if isinstance(head, slice):
        if head != FULL_SLICE:
            return [get_nested(item, tail) for item in value[head]]
        return [get_nested(item, tail) for item in value]
    return get_nested(value[head], tail)


def set_nested(value: Any, index: tuple[Any, ...], replacement: Any) -> None:
    """Assign into nested Python containers with full slices and integer indices."""
    if len(index) == 1:
        head = index[0]
        if isinstance(head, slice):
            replacement_items = list(replacement)
            target_range = (
                range(len(value)) if head == FULL_SLICE else range(*head.indices(len(value)))
            )
            for item_index, replacement_item in zip(target_range, replacement_items, strict=True):
                value[item_index] = replacement_item
            return
        value[head] = replacement
        return

    head = index[0]
    tail = index[1:]
    if isinstance(head, slice):
        target_range = range(len(value)) if head == FULL_SLICE else range(*head.indices(len(value)))
        replacement_items = list(replacement)
        for item_index, replacement_item in zip(target_range, replacement_items, strict=True):
            set_nested(value[item_index], tail, replacement_item)
        return
    set_nested(value[head], tail, replacement)


def scale_value(value: Any, scale: float) -> Any:
    """Scale tensor-like or nested-list values."""
    if scale == 1.0:
        return value
    try:
        return value * scale
    except TypeError:
        if isinstance(value, list):
            return [scale_value(item, scale) for item in value]
        return value


def add_values(left: Any, right: Any) -> Any:
    """Add tensor-like or nested-list values elementwise."""
    try:
        if isinstance(left, list) and isinstance(right, list):
            return [
                add_values(left_item, right_item)
                for left_item, right_item in zip(left, right, strict=True)
            ]
        return left + right
    except TypeError:
        return right


def infer_layers(
    model: ModelWrapper,
    clean_cache: ActivationCache,
    component: str,
    *,
    name_style: ActivationNameStyle = "safelens",
) -> list[LayerRef]:
    """Infer layer indices from model config or clean cache names."""
    n_layers = get_config_int(model, ("n_layers", "num_hidden_layers", "num_layers"))
    if n_layers is not None:
        return list(range(n_layers))

    layers_from_cache = infer_layers_from_cache(clean_cache, component, name_style=name_style)
    if layers_from_cache:
        return layers_from_cache

    raise ValueError("Could not infer layers. Pass `layers=[...]` explicitly.")


def infer_layers_from_cache(
    clean_cache: ActivationCache,
    component: str,
    *,
    name_style: ActivationNameStyle = "safelens",
) -> list[LayerRef]:
    """Infer layer indices from SafeLens or TransformerLens-style activation names."""
    layers: set[int] = set()
    for name in clean_cache:
        if name_style == "transformer_lens":
            match = re.search(r"blocks\.(\d+)\.", name)
        else:
            match = re.search(r"layer_(\d+)\.", name)
        if match is not None and component in name:
            layers.add(int(match.group(1)))
    return sorted(layers)


def infer_positions(
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    component: str,
    layers: Sequence[LayerRef],
) -> int:
    """Infer sequence length from batch tensors or cached activations."""
    for key in ("input_ids", "tokens"):
        if key in corrupted_batch:
            shape = shape_of(corrupted_batch[key])
            if len(shape) >= 2:
                return shape[-1]

    activation = first_component_activation(clean_cache, component, layers)
    if activation is not None:
        shape = shape_of(activation)
        if len(shape) >= 2:
            return shape[1]

    raise ValueError("Could not infer positions. Pass `positions=[...]` explicitly.")


def infer_heads(
    model: ModelWrapper,
    clean_cache: ActivationCache,
    component: str,
    layers: Sequence[LayerRef],
) -> int:
    """Infer number of heads from model config or cached activations."""
    if component in {"k", "v"}:
        n_key_value_heads = get_config_int(model, ("n_key_value_heads", "num_key_value_heads"))
        if n_key_value_heads is not None:
            return n_key_value_heads

    n_heads = get_config_int(model, ("n_heads", "num_attention_heads"))
    if n_heads is not None:
        return n_heads

    activation = first_component_activation(clean_cache, component, layers)
    if activation is not None:
        shape = shape_of(activation)
        if component in {"pattern", "attn_scores"} and len(shape) >= 2:
            return shape[1]
        if len(shape) >= 3:
            return shape[2]

    raise ValueError("Could not infer heads. Pass `heads=[...]` explicitly.")


def first_component_activation(
    clean_cache: ActivationCache,
    component: str,
    layers: Sequence[LayerRef],
) -> Any:
    """Return the first activation matching a component and layer list."""
    candidate_names = [
        activation_name_for_component(component, layer, name_style="safelens") for layer in layers
    ]
    candidate_names.extend(
        activation_name_for_component(component, layer, name_style="transformer_lens")
        for layer in layers
    )
    for name in candidate_names:
        if name in clean_cache:
            return clean_cache[name]
    for name, activation in clean_cache.items():
        if component in name:
            return activation
    return None


def shape_of(value: Any) -> tuple[int, ...]:
    """Return a best-effort shape for tensor-like or nested-list values."""
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            return (0,)
        return (len(value), *shape_of(value[0]))
    return ()


def get_config_int(model: Any, names: Sequence[str]) -> int | None:
    """Read an integer config value from wrapper/model cfg/config objects."""
    owners = [model, getattr(model, "cfg", None), getattr(model, "config", None)]
    wrapped_model = getattr(model, "model", None)
    if wrapped_model is not None:
        owners.extend(
            [
                wrapped_model,
                getattr(wrapped_model, "cfg", None),
                getattr(wrapped_model, "config", None),
            ]
        )
    for owner in owners:
        if owner is None:
            continue
        for name in names:
            value = getattr(owner, name, None)
            if value is not None:
                return int(value)
    return None


def _values_or_range(values: Iterable[int] | None, inferred_size: int, name: str) -> Iterable[int]:
    if values is not None:
        return values
    if inferred_size < 0:
        raise ValueError(f"Could not infer {name}.")
    return range(inferred_size)


def _axis_values(axis_values: Mapping[AxisName, Iterable[int]], axis_name: AxisName) -> list[int]:
    try:
        return list(axis_values[axis_name])
    except KeyError as exc:
        raise ValueError(f"Missing axis values for {axis_name!r}.") from exc
