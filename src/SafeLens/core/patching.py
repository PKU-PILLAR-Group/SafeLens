"""Generic and component-level activation patching primitives."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from inspect import Parameter, signature
from itertools import product
from numbers import Integral
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
TransformerLensPatchSetter = Callable[[Any, Sequence[int], Any], Any]
AxisName = Literal["layer", "pos", "head_index", "head", "src_pos", "dest_pos"]
ActivationNameStyle = Literal["safelens", "transformer_lens"]

FULL_SLICE = slice(None)
PATTERN_COMPONENTS = {
    "pattern",
    "attn_scores",
    "decoder_pattern",
    "decoder_attn_scores",
    "cross_pattern",
    "cross_attn_scores",
}
PREFIXED_ATTENTION_LAYER_TYPES = {
    "cross_attn": "cross",
    "cross_attention": "cross",
    "encoder_decoder_attn": "cross",
    "decoder_attn": "decoder",
    "decoder_attention": "decoder",
}
ATTENTION_VECTOR_COMPONENTS = {"q", "k", "v", "z", "result", "pattern", "attn_scores"}
DECODER_TOP_LEVEL_COMPONENTS = {
    "resid_pre",
    "resid_mid",
    "resid_mid_cross",
    "resid_post",
    "attn_in",
    "attn_out",
    "q_input",
    "k_input",
    "v_input",
    "mlp_in",
    "mlp_out",
}
CROSS_TOP_LEVEL_COMPONENTS = {"cross_attn_in", "cross_attn_out"}
DECODER_MLP_COMPONENTS = {"pre", "post", "pre_linear"}

TRANSFORMER_LENS_ACTIVATION_TEMPLATES = {
    "resid_pre": "blocks.{layer}.hook_resid_pre",
    "resid_mid": "blocks.{layer}.hook_resid_mid",
    "resid_post": "blocks.{layer}.hook_resid_post",
    "attn_out": "blocks.{layer}.hook_attn_out",
    "mlp_out": "blocks.{layer}.hook_mlp_out",
    "pre": "blocks.{layer}.mlp.hook_pre",
    "pre_linear": "blocks.{layer}.mlp.hook_pre_linear",
    "post": "blocks.{layer}.mlp.hook_post",
    "q": "blocks.{layer}.attn.hook_q",
    "k": "blocks.{layer}.attn.hook_k",
    "v": "blocks.{layer}.attn.hook_v",
    "z": "blocks.{layer}.attn.hook_z",
    "result": "blocks.{layer}.attn.hook_result",
    "pattern": "blocks.{layer}.attn.hook_pattern",
    "attn_scores": "blocks.{layer}.attn.hook_attn_scores",
}


def make_df_from_ranges(
    column_max_ranges: Sequence[int],
    column_names: Sequence[str],
) -> Any:
    """Create a TransformerLens-style patch index table from axis ranges."""
    if len(column_max_ranges) != len(column_names):
        raise ValueError(
            "column_max_ranges and column_names must have the same length, got "
            f"{len(column_max_ranges)} and {len(column_names)}."
        )
    if any(int(size) < 0 for size in column_max_ranges):
        raise ValueError(f"column_max_ranges must be non-negative, got {column_max_ranges!r}.")

    rows = [
        dict(zip(column_names, values, strict=True))
        for values in product(*(range(int(size)) for size in column_max_ranges))
    ]
    try:
        import pandas as pd

        return pd.DataFrame(rows, columns=list(column_names))
    except ImportError:
        return rows


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
    explicit_ref = _explicit_activation_ref(component)
    if explicit_ref is not None and _same_layer_ref(layer, explicit_ref[0]):
        return component
    component = explicit_ref[1] if explicit_ref is not None else component
    layer_ref = _explicit_layer_ref(layer)
    if layer_ref is not None:
        layer_index, layer_component = layer_ref
        requested_component = _normalize_patch_component(component)
        if requested_component != layer_component:
            raise ValueError(
                f"Layer reference {layer!r} targets component {layer_component!r}, "
                f"but patch helper requested {requested_component!r}."
            )
        if isinstance(layer, str) and name_template is None:
            return layer
        layer = layer_index
        component = layer_component
    if name_template is not None:
        return name_template.format(layer=layer, component=component)
    if name_style == "transformer_lens":
        return transformer_lens_activation_name_for_component(component, layer)
    return f"{activation_name_for_layer(layer)}.{component}"


def transformer_lens_activation_name_for_component(component: str, layer: LayerRef) -> str:
    """Return a TransformerLens-style hook name for canonical SafeLens components."""
    normalized_component = _normalize_patch_component(component)
    try:
        from SafeLens.utils.model_bridge import transformer_lens_component_name

        return transformer_lens_component_name(normalized_component, int(layer))
    except (ImportError, TypeError, ValueError):
        template = TRANSFORMER_LENS_ACTIVATION_TEMPLATES.get(
            normalized_component,
            "blocks.{layer}.hook_{component}",
        )
        return template.format(layer=layer, component=normalized_component)


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
        return coerce_value_like(corrupted_activation, patch_value)

    patched = clone_patch_target(corrupted_activation)
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

    patched = clone_patch_target(corrupted_activation)
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


def _patch_run_return_type_kwargs(
    run_method: Callable[..., Any],
    metric: PatchMetric,
    model: ModelWrapper,
) -> dict[str, Any]:
    """Return extra kwargs for TL-style patch runs through wrapper run methods."""
    try:
        parameters = signature(run_method).parameters
    except (TypeError, ValueError):
        return {}
    return_type_param = parameters.get("return_type")
    if return_type_param is None:
        return {}
    if return_type_param.default == "model_output":
        return {}
    metric_return_type = _metric_return_type_hint(metric)
    if metric_return_type == "model_output":
        return {}
    if metric_return_type == "logits" or _patch_model_prefers_logits(model):
        return {"return_type": "logits"}
    return {}


def _metric_return_type_hint(metric: PatchMetric) -> Literal["logits", "model_output"] | None:
    """Infer whether a patch metric wants logits or a raw model output object."""
    try:
        parameters = list(signature(metric).parameters.values())
    except (TypeError, ValueError):
        return None
    positional_parameters = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.KEYWORD_ONLY,
        )
    ]
    if not positional_parameters:
        return None
    name = positional_parameters[0].name.lower()
    if "logit" in name:
        return "logits"
    if name in {"output", "outputs", "model_output", "model_outputs", "raw", "raw_output"}:
        return "model_output"
    return None


def _patch_model_prefers_logits(model: ModelWrapper) -> bool:
    uses_decoder_semantics = getattr(model, "_uses_decoder_text_input_semantics", None)
    if callable(uses_decoder_semantics):
        try:
            return bool(uses_decoder_semantics())
        except Exception:
            return False
    return False


def run_activation_patch(
    model: ModelWrapper,
    corrupted_batch: Any,
    clean_cache: ActivationCache,
    spec: PatchSpec,
    metric: PatchMetric,
    *,
    layers: Sequence[LayerRef] | None = None,
) -> PatchResult:
    """Run one patched corrupted forward pass and score it with a metric."""
    patch_hook = make_patch_hook(spec, clean_cache)
    wrapper_run_with_hooks = getattr(model, "run_with_hooks", None)
    if callable(wrapper_run_with_hooks) and layers is None:
        output = wrapper_run_with_hooks(
            corrupted_batch,
            fwd_hooks=[(spec.layer, patch_hook)],
            **_patch_run_return_type_kwargs(wrapper_run_with_hooks, metric, model),
        )
        cache = {}
    else:
        with temporary_hooks(model, [(spec.layer, patch_hook)]):
            output, cache = model.run_with_cache(
                corrupted_batch,
                layers=layers,
                **_patch_run_return_type_kwargs(model.run_with_cache, metric, model),
            )
    return PatchResult(
        spec=spec, metric=_metric_to_float(metric(output)), output=output, cache=cache
    )


def _metric_to_float(value: Any) -> float:
    """Convert scalar metric outputs, including tensor/array scalars, to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        item = getattr(value, "item", None)
        if callable(item):
            return float(item())
        raise


def generic_activation_patch(
    model: ModelWrapper,
    corrupted_batch: Any,
    clean_cache: ActivationCache,
    specs: Iterable[PatchSpec] | PatchMetric | None = None,
    metric: PatchMetric | PatchSetter | TransformerLensPatchSetter | None = None,
    activation_name: str | None = None,
    index_axis_names: Sequence[AxisName] | None = None,
    index_df: Any = None,
    return_index_df: bool = False,
    *,
    layers: Sequence[LayerRef] | None = None,
    patching_metric: PatchMetric | None = None,
    patch_setter: PatchSetter | TransformerLensPatchSetter | None = None,
    return_details: bool | None = None,
    return_metric_grid: bool = False,
    return_index_table: bool = False,
) -> Any:
    """Run a sequence of activation patches, similar to TransformerLens' generic patcher."""
    transformer_lens_style = specs is None and (
        patching_metric is not None or patch_setter is not None or activation_name is not None
    )
    if specs is not None and callable(specs) and not _looks_like_patch_specs(specs):
        if metric is not None and callable(metric) and patch_setter is None:
            if patching_metric is not None:
                raise TypeError("Pass patching_metric either positionally or by keyword, not both.")
            patching_metric = specs
            patch_setter = metric
            specs = None
            metric = None
            transformer_lens_style = True
        else:
            if patching_metric is not None:
                raise TypeError("Pass patching_metric either positionally or by keyword, not both.")
            patching_metric = specs
            specs = None
            transformer_lens_style = True
    if metric is not None and callable(metric) and specs is None and patch_setter is None:
        patch_setter = metric
        metric = None
        transformer_lens_style = True

    metric_fn = metric or patching_metric
    if metric_fn is None:
        raise TypeError("generic_activation_patch requires `metric` or `patching_metric`.")

    resolved_index_axis_names = index_axis_names
    if specs is None:
        if patch_setter is None or activation_name is None:
            raise TypeError(
                "TL-style generic_activation_patch requires `patch_setter` and "
                "`activation_name` when `specs` is not supplied."
            )
        flattened_output = index_df is not None
        if index_df is None:
            if index_axis_names is None:
                raise TypeError("Pass `index_axis_names` or `index_df` for TL-style patching.")
            index_df = infer_index_table(
                model,
                corrupted_batch,
                clean_cache,
                activation_name,
                index_axis_names,
                name_style="transformer_lens",
            )
        else:
            if index_axis_names is not None:
                raise ValueError("Pass either `index_axis_names` or explicit `index_df`, not both.")
            index_df, resolved_index_axis_names = normalize_index_table(
                index_df,
                index_axis_names,
            )
        specs = make_transformer_lens_patch_specs(
            activation_name,
            index_df,
            patch_setter=patch_setter,
        )
    elif patch_setter is not None or activation_name is not None or index_df is not None:
        raise TypeError(
            "Pass either SafeLens `specs` or TL-style `patch_setter`/`activation_name`, not both."
        )
    if isinstance(specs, PatchSpec):
        specs = [specs]

    if return_details is None:
        return_details = not transformer_lens_style
    if not return_details:
        return_metric_grid = True

    results = [
        run_activation_patch(
            model,
            corrupted_batch,
            clean_cache,
            spec,
            metric_fn,
            layers=layers,
        )
        for spec in specs
    ]
    return format_patch_results(
        results,
        resolved_index_axis_names,
        return_details=return_details,
        return_metric_grid=return_metric_grid,
        return_index_table=return_index_table,
        return_index_df=return_index_df,
        flatten_metric_output=locals().get("flattened_output", False),
    )


def _looks_like_patch_specs(value: Any) -> bool:
    if isinstance(value, PatchSpec):
        return True
    if callable(value):
        return False
    return isinstance(value, Iterable)


def patch_results_to_index_table(
    results: Sequence[PatchResult],
    index_axis_names: Sequence[AxisName] | None = None,
) -> list[dict[str, Any]]:
    """Return a dependency-free index table for a patch result sequence."""
    table: list[dict[str, Any]] = []
    for result_index, result in enumerate(results):
        index = normalize_index(result.spec.target_index)
        if index_axis_names is None:
            row: dict[str, Any] = {"patch_index": result_index}
            row.update({f"index_{axis_index}": value for axis_index, value in enumerate(index)})
        else:
            row = {}
            if index_axis_names and index_axis_names[0] == "layer":
                row["layer"] = (
                    index[0] if len(index) == len(index_axis_names) else result.spec.layer
                )
            for axis_index, axis_name in enumerate(index_axis_names):
                if axis_name == "layer" and "layer" in row:
                    continue
                source_index = axis_index if len(index) == len(index_axis_names) else axis_index - 1
                if 0 <= source_index < len(index):
                    row[axis_name] = index[source_index]
        table.append(row)
    return table


def patch_results_to_index_df(
    results: Sequence[PatchResult],
    index_axis_names: Sequence[AxisName] | None = None,
) -> Any:
    """Return a TransformerLens-style index DataFrame when pandas is available."""
    index_table = patch_results_to_index_table(results, index_axis_names)
    columns = list(index_axis_names or (index_table[0].keys() if index_table else ()))
    try:
        import pandas as pd

        return pd.DataFrame(index_table, columns=columns)
    except ImportError:
        return index_table


def patch_results_to_metric_grid(
    results: Sequence[PatchResult],
    index_axis_names: Sequence[AxisName] | None = None,
) -> Any:
    """Convert patch results to a TransformerLens-style metric grid."""
    if index_axis_names is None:
        return [result.metric for result in results]
    if not index_axis_names:
        return results[0].metric if results else 0.0

    index_table = patch_results_to_index_table(results, index_axis_names)
    axis_values = [
        _ordered_unique(row[axis_name] for row in index_table if axis_name in row)
        for axis_name in index_axis_names
    ]
    grid = make_nested_grid([len(values) for values in axis_values], fill_value=0.0)
    axis_lookup = [
        {value: position for position, value in enumerate(values)} for values in axis_values
    ]

    for result, row in zip(results, index_table, strict=True):
        coordinate = tuple(
            axis_lookup[axis_index][row[axis_name]]
            for axis_index, axis_name in enumerate(index_axis_names)
        )
        set_nested(grid, coordinate, result.metric)
    return grid


def format_patch_results(
    results: Sequence[PatchResult],
    index_axis_names: Sequence[AxisName] | None = None,
    *,
    return_details: bool = True,
    return_metric_grid: bool = False,
    return_index_table: bool = False,
    return_index_df: bool = False,
    flatten_metric_output: bool = False,
) -> Any:
    """Format patch results as details or TL-style metric outputs."""
    include_index = return_index_table or return_index_df
    if return_index_df:
        return_metric_grid = True
        return_details = False

    output = (
        patch_results_to_metric_grid(
            results,
            None if flatten_metric_output else index_axis_names,
        )
        if return_metric_grid or not return_details
        else list(results)
    )
    if include_index:
        if return_index_df:
            return output, patch_results_to_index_df(results, index_axis_names)
        return output, patch_results_to_index_table(results, index_axis_names)
    return output


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
    patch_setter: PatchSetter | TransformerLensPatchSetter,
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
    adapted_patch_setter = adapt_transformer_lens_patch_setter(patch_setter)

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
                    index_parts.append(_patch_index_layer_value(layer))
                else:
                    index_parts.append(axis_lookup[axis_name])
            specs.append(
                PatchSpec(
                    layer=activation_name,
                    activation_name=activation_name,
                    target_index=tuple(index_parts),
                    mode=mode,
                    scale=scale,
                    setter=adapted_patch_setter,
                )
            )

    return specs


def make_transformer_lens_patch_specs(
    activation_name: str,
    index_table: Sequence[Mapping[str, Any]],
    *,
    patch_setter: PatchSetter | TransformerLensPatchSetter,
) -> list[PatchSpec]:
    """Create specs for a TransformerLens-style `generic_activation_patch` call."""
    index_table, _columns = normalize_index_table(index_table)
    specs: list[PatchSpec] = []
    expected_columns: tuple[str, ...] | None = None
    for row in index_table:
        if "layer" not in row:
            raise ValueError("TL-style patch index rows must include a `layer` column.")
        columns = tuple(row.keys())
        if not columns or columns[0] != "layer":
            raise ValueError("TL-style patch index rows must have `layer` as the first column.")
        if expected_columns is None:
            expected_columns = columns
        elif columns != expected_columns:
            raise ValueError("TL-style patch index rows must all have the same columns.")
        layer = row["layer"]
        index = tuple(row[column] for column in columns)
        target_name = activation_name_for_component(
            activation_name,
            layer,
            name_style="transformer_lens",
        )
        specs.append(
            PatchSpec(
                layer=target_name,
                activation_name=target_name,
                target_index=index,
                setter=adapt_transformer_lens_patch_setter(patch_setter),
            )
        )
    return specs


def adapt_transformer_lens_patch_setter(
    patch_setter: PatchSetter | TransformerLensPatchSetter,
) -> PatchSetter:
    """Adapt TL-style `(activation, index, clean_activation)` setters to PatchSpec setters."""
    call_style = infer_patch_setter_call_style(patch_setter)

    def setter(corrupted_activation: Any, spec: PatchSpec, clean_cache: ActivationCache) -> Any:
        clean_activation = spec.value if spec.value is not None else clean_cache[spec.clean_name]
        index = normalize_index(spec.target_index)
        if call_style == "safelens":
            return patch_setter(corrupted_activation, spec, clean_cache)
        if call_style == "transformer_lens":
            return patch_setter(
                clone_patch_target_if_requires_grad(corrupted_activation),
                list(index),
                clean_activation,
            )
        inferred_call_style = infer_patch_setter_bind_style(patch_setter)
        if inferred_call_style == "safelens":
            return patch_setter(corrupted_activation, spec, clean_cache)
        return patch_setter(
            clone_patch_target_if_requires_grad(corrupted_activation),
            list(index),
            clean_activation,
        )

    return setter


def infer_patch_setter_call_style(
    patch_setter: PatchSetter | TransformerLensPatchSetter,
) -> Literal["safelens", "transformer_lens"] | None:
    """Infer patch-setter calling convention from common parameter names."""
    try:
        parameters = list(signature(patch_setter).parameters.values())
    except (TypeError, ValueError):
        return None

    positional_parameters = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.KEYWORD_ONLY,
        )
    ]
    names = [parameter.name for parameter in positional_parameters]
    second_name = names[1] if len(names) > 1 else ""
    third_name = names[2] if len(names) > 2 else ""

    if second_name in {"spec", "patch_spec"} or third_name in {"clean_cache", "cache"}:
        return "safelens"
    if second_name in {"index", "indices", "patch_index"} or third_name in {
        "clean_activation",
        "clean_act",
        "clean_value",
    }:
        return "transformer_lens"
    return None


def infer_patch_setter_bind_style(
    patch_setter: PatchSetter | TransformerLensPatchSetter,
) -> Literal["safelens", "transformer_lens"]:
    """Infer an ambiguous patch setter style without executing user code."""
    try:
        setter_signature = signature(patch_setter)
    except (TypeError, ValueError):
        return "transformer_lens"

    try:
        setter_signature.bind(None, (), None)
    except TypeError:
        tl_binds = False
    else:
        tl_binds = True
    try:
        setter_signature.bind(None, _BIND_STYLE_PATCH_SPEC_SENTINEL, ActivationCache())
    except TypeError:
        safelens_binds = False
    else:
        safelens_binds = True

    if not tl_binds and safelens_binds:
        return "safelens"
    return "transformer_lens"


_BIND_STYLE_PATCH_SPEC_SENTINEL = PatchSpec(layer=0)


def component_activation_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    *,
    component: str,
    patch_setter: PatchSetter | TransformerLensPatchSetter,
    index_axis_names: Sequence[AxisName] | None,
    activation_name: str | None = None,
    index_df: Any = None,
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
    return_details: bool = True,
    return_metric_grid: bool = False,
    return_index_table: bool = False,
    return_index_df: bool = False,
) -> Any:
    """Run a component-level activation patch grid."""
    patch_component = activation_name or component
    if index_df is not None:
        index_table, resolved_index_axis_names = normalize_index_table(
            index_df,
            index_axis_names,
        )
        specs = make_transformer_lens_patch_specs(
            patch_component,
            index_table,
            patch_setter=patch_setter,
        )
        results = generic_activation_patch(
            model,
            corrupted_batch,
            clean_cache,
            specs,
            metric,
            layers=cache_layers,
        )
        return format_patch_results(
            results,
            resolved_index_axis_names,
            return_details=return_details,
            return_metric_grid=return_metric_grid,
            return_index_table=return_index_table,
            return_index_df=return_index_df,
            flatten_metric_output=True,
        )

    if index_axis_names is None:
        raise TypeError("Pass `index_axis_names` when `index_df` is not supplied.")

    layer_values = list(
        layers
        if layers is not None
        else infer_layers(model, clean_cache, patch_component, name_style=name_style)
    )
    axis_values: dict[AxisName, Iterable[int]] = {}
    if "pos" in index_axis_names:
        axis_values["pos"] = _values_or_range(
            positions,
            infer_positions(
                corrupted_batch,
                clean_cache,
                patch_component,
                layer_values,
                axis_name="pos",
            ),
            "positions",
        )
    if "head" in index_axis_names:
        axis_values["head"] = _values_or_range(
            heads,
            infer_heads(model, clean_cache, patch_component, layer_values),
            "heads",
        )
    if "head_index" in index_axis_names:
        axis_values["head_index"] = _values_or_range(
            heads,
            infer_heads(model, clean_cache, patch_component, layer_values),
            "heads",
        )
    if "dest_pos" in index_axis_names:
        axis_values["dest_pos"] = _values_or_range(
            dest_positions,
            infer_positions(
                corrupted_batch,
                clean_cache,
                patch_component,
                layer_values,
                axis_name="dest_pos",
            ),
            "dest_positions",
        )
    if "src_pos" in index_axis_names:
        axis_values["src_pos"] = _values_or_range(
            source_positions,
            infer_positions(
                corrupted_batch,
                clean_cache,
                patch_component,
                layer_values,
                axis_name="src_pos",
            ),
            "source_positions",
        )
    specs = make_component_patch_specs(
        layer_values,
        patch_component,
        index_axis_names,
        axis_values,
        patch_setter=patch_setter,
        mode=mode,
        scale=scale,
        name_style=name_style,
        name_template=name_template,
    )
    results = generic_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        specs,
        metric,
        layers=cache_layers,
    )
    return format_patch_results(
        results,
        index_axis_names,
        return_details=return_details,
        return_metric_grid=return_metric_grid,
        return_index_table=return_index_table,
        return_index_df=return_index_df,
    )


def layer_pos_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec | Sequence[int],
    clean_cache: ActivationCache | Any,
) -> Any:
    """Patch activations shaped `[batch, pos, ...]` at one layer and position."""
    tl_output = maybe_apply_transformer_lens_patch_setter(
        corrupted_activation,
        spec,
        clean_cache,
        expected_length=2,
        setter_name="layer_pos_patch_setter",
        min_batched_rank=3,
        target_slice_fn=lambda index: (FULL_SLICE, index[1]),
        source_slice_fn=lambda index: (FULL_SLICE, index[1]),
    )
    if tl_output is not None:
        return tl_output
    index = require_patch_index(spec, 2, "layer_pos_patch_setter")
    source_index = source_index_or_target(spec, index)
    target_has_batch = patch_target_has_batch_dim(corrupted_activation, spec, clean_cache)
    source_has_batch = patch_source_has_batch_dim(corrupted_activation, spec, clean_cache)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=batch_prefixed_slice(target_has_batch, index[1]),
        source_slice=batch_prefixed_slice(source_has_batch, source_index[1]),
    )


def layer_pos_head_vector_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec | Sequence[int],
    clean_cache: ActivationCache | Any,
) -> Any:
    """Patch head vector activations shaped `[batch, pos, head, ...]`."""
    tl_output = maybe_apply_transformer_lens_patch_setter(
        corrupted_activation,
        spec,
        clean_cache,
        expected_length=3,
        setter_name="layer_pos_head_vector_patch_setter",
        min_batched_rank=4,
        target_slice_fn=lambda index: (FULL_SLICE, index[1], index[2]),
        source_slice_fn=lambda index: (FULL_SLICE, index[1], index[2]),
    )
    if tl_output is not None:
        return tl_output
    index = require_patch_index(spec, 3, "layer_pos_head_vector_patch_setter")
    source_index = source_index_or_target(spec, index)
    target_has_batch = patch_target_has_batch_dim(corrupted_activation, spec, clean_cache)
    source_has_batch = patch_source_has_batch_dim(corrupted_activation, spec, clean_cache)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=batch_prefixed_slice(target_has_batch, index[1], index[2]),
        source_slice=batch_prefixed_slice(source_has_batch, source_index[1], source_index[2]),
    )


def layer_head_vector_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec | Sequence[int],
    clean_cache: ActivationCache | Any,
) -> Any:
    """Patch a head vector across all positions for `[batch, pos, head, ...]`."""
    tl_output = maybe_apply_transformer_lens_patch_setter(
        corrupted_activation,
        spec,
        clean_cache,
        expected_length=2,
        setter_name="layer_head_vector_patch_setter",
        min_batched_rank=4,
        target_slice_fn=lambda index: (FULL_SLICE, FULL_SLICE, index[1]),
        source_slice_fn=lambda index: (FULL_SLICE, FULL_SLICE, index[1]),
    )
    if tl_output is not None:
        return tl_output
    index = require_patch_index(spec, 2, "layer_head_vector_patch_setter")
    source_index = source_index_or_target(spec, index)
    target_has_batch = patch_target_has_batch_dim(corrupted_activation, spec, clean_cache)
    source_has_batch = patch_source_has_batch_dim(corrupted_activation, spec, clean_cache)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=batch_prefixed_slice(target_has_batch, FULL_SLICE, index[1]),
        source_slice=batch_prefixed_slice(source_has_batch, FULL_SLICE, source_index[1]),
    )


def layer_head_pattern_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec | Sequence[int],
    clean_cache: ActivationCache | Any,
) -> Any:
    """Patch an attention pattern head shaped `[batch, head, dest_pos, src_pos]`."""
    tl_output = maybe_apply_transformer_lens_patch_setter(
        corrupted_activation,
        spec,
        clean_cache,
        expected_length=2,
        setter_name="layer_head_pattern_patch_setter",
        min_batched_rank=4,
        target_slice_fn=lambda index: (FULL_SLICE, index[1], FULL_SLICE, FULL_SLICE),
        source_slice_fn=lambda index: (FULL_SLICE, index[1], FULL_SLICE, FULL_SLICE),
    )
    if tl_output is not None:
        return tl_output
    index = require_patch_index(spec, 2, "layer_head_pattern_patch_setter")
    source_index = source_index_or_target(spec, index)
    target_has_batch = patch_target_has_batch_dim(corrupted_activation, spec, clean_cache)
    source_has_batch = patch_source_has_batch_dim(corrupted_activation, spec, clean_cache)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=batch_prefixed_slice(target_has_batch, index[1], FULL_SLICE, FULL_SLICE),
        source_slice=batch_prefixed_slice(
            source_has_batch,
            source_index[1],
            FULL_SLICE,
            FULL_SLICE,
        ),
    )


def layer_head_pos_pattern_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec | Sequence[int],
    clean_cache: ActivationCache | Any,
) -> Any:
    """Patch one destination position in an attention pattern."""
    tl_output = maybe_apply_transformer_lens_patch_setter(
        corrupted_activation,
        spec,
        clean_cache,
        expected_length=3,
        setter_name="layer_head_pos_pattern_patch_setter",
        min_batched_rank=4,
        target_slice_fn=lambda index: (FULL_SLICE, index[1], index[2], FULL_SLICE),
        source_slice_fn=lambda index: (FULL_SLICE, index[1], index[2], FULL_SLICE),
    )
    if tl_output is not None:
        return tl_output
    index = require_patch_index(spec, 3, "layer_head_pos_pattern_patch_setter")
    source_index = source_index_or_target(spec, index)
    target_has_batch = patch_target_has_batch_dim(corrupted_activation, spec, clean_cache)
    source_has_batch = patch_source_has_batch_dim(corrupted_activation, spec, clean_cache)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=batch_prefixed_slice(target_has_batch, index[1], index[2], FULL_SLICE),
        source_slice=batch_prefixed_slice(
            source_has_batch,
            source_index[1],
            source_index[2],
            FULL_SLICE,
        ),
    )


def layer_head_dest_src_pos_pattern_patch_setter(
    corrupted_activation: Any,
    spec: PatchSpec | Sequence[int],
    clean_cache: ActivationCache | Any,
) -> Any:
    """Patch one `(destination, source)` entry in an attention pattern."""
    tl_output = maybe_apply_transformer_lens_patch_setter(
        corrupted_activation,
        spec,
        clean_cache,
        expected_length=4,
        setter_name="layer_head_dest_src_pos_pattern_patch_setter",
        min_batched_rank=4,
        target_slice_fn=lambda index: (FULL_SLICE, index[1], index[2], index[3]),
        source_slice_fn=lambda index: (FULL_SLICE, index[1], index[2], index[3]),
    )
    if tl_output is not None:
        return tl_output
    index = require_patch_index(
        spec,
        4,
        "layer_head_dest_src_pos_pattern_patch_setter",
    )
    source_index = source_index_or_target(spec, index)
    target_has_batch = patch_target_has_batch_dim(corrupted_activation, spec, clean_cache)
    source_has_batch = patch_source_has_batch_dim(corrupted_activation, spec, clean_cache)
    return patch_slice(
        corrupted_activation,
        spec,
        clean_cache,
        target_slice=batch_prefixed_slice(target_has_batch, index[1], index[2], index[3]),
        source_slice=batch_prefixed_slice(
            source_has_batch,
            source_index[1],
            source_index[2],
            source_index[3],
        ),
    )


def get_act_patch_resid_pre(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch residual stream activations at the start of each block by position."""
    return _layer_pos_component_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_resid_pre"),
        "resid_pre",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_resid_mid(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch residual stream activations between attention and MLP by position."""
    return _layer_pos_component_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_resid_mid"),
        "resid_mid",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_resid_post(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch residual stream activations at the end of each block by position."""
    return _layer_pos_component_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_resid_post"),
        "resid_post",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_out(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention layer outputs by position."""
    return _layer_pos_component_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_out"),
        "attn_out",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_mlp_out(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch MLP layer outputs by position."""
    return _layer_pos_component_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_mlp_out"),
        "mlp_out",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_out_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention head outputs `z` by layer, position, and head."""
    return _head_vector_by_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_out_by_pos"),
        "z",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_q_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention queries by layer, position, and head."""
    return _head_vector_by_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_q_by_pos"),
        "q",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_k_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention keys by layer, position, and head."""
    return _head_vector_by_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_k_by_pos"),
        "k",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_v_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention values by layer, position, and head."""
    return _head_vector_by_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_v_by_pos"),
        "v",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_result_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch per-head attention result vectors by layer, position, and head."""
    return _head_vector_by_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_result_by_pos"),
        "result",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_out_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention head outputs `z` across all positions."""
    return _head_vector_all_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_out_all_pos"),
        "z",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_q_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention queries across all positions."""
    return _head_vector_all_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_q_all_pos"),
        "q",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_k_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention keys across all positions."""
    return _head_vector_all_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_k_all_pos"),
        "k",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_v_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention values across all positions."""
    return _head_vector_all_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_v_all_pos"),
        "v",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_result_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch per-head attention result vectors across all positions."""
    return _head_vector_all_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_result_all_pos"),
        "result",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_pattern_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch full attention patterns by layer and head."""
    return _head_pattern_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_pattern_all_pos"),
        "pattern",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_pattern_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention patterns by layer, head, and destination position."""
    return _head_pattern_by_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_pattern_by_pos"),
        "pattern",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_head_pattern_dest_src_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch attention patterns by layer, head, destination, and source position."""
    return _head_pattern_dest_src_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_pattern_dest_src_pos"),
        "pattern",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_scores_all_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch raw attention scores by layer and head."""
    return _head_pattern_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_scores_all_pos"),
        "attn_scores",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_scores_by_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch raw attention scores by layer, head, and destination position."""
    return _head_pattern_by_pos_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_scores_by_pos"),
        "attn_scores",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_attn_scores_dest_src_pos(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch raw attention scores by layer, head, destination, and source position."""
    return _head_pattern_dest_src_patch(
        model,
        corrupted_batch,
        clean_cache,
        _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_scores_dest_src_pos"),
        "attn_scores",
        _component_helper_kwargs(kwargs),
    )


def get_act_patch_block_every(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch residual pre, attention output, and MLP output by layer and position."""
    metric = _resolve_patching_metric(metric, kwargs, "get_act_patch_block_every")
    named_outputs = [
        (
            "resid_pre",
            get_act_patch_resid_pre(model, corrupted_batch, clean_cache, metric, **kwargs),
        ),
        (
            "attn_out",
            get_act_patch_attn_out(model, corrupted_batch, clean_cache, metric, **kwargs),
        ),
        ("mlp_out", get_act_patch_mlp_out(model, corrupted_batch, clean_cache, metric, **kwargs)),
    ]
    if _returns_details(kwargs):
        return dict(named_outputs)
    return _stack_named_metric_outputs(named_outputs)


def get_act_patch_attn_head_all_pos_every(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch `z`, `q`, `k`, `v`, and `pattern` by layer and head."""
    metric = _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_all_pos_every")
    named_outputs = [
        (
            "z",
            get_act_patch_attn_head_out_all_pos(
                model,
                corrupted_batch,
                clean_cache,
                metric,
                **kwargs,
            ),
        ),
        (
            "q",
            get_act_patch_attn_head_q_all_pos(
                model, corrupted_batch, clean_cache, metric, **kwargs
            ),
        ),
        (
            "k",
            get_act_patch_attn_head_k_all_pos(
                model, corrupted_batch, clean_cache, metric, **kwargs
            ),
        ),
        (
            "v",
            get_act_patch_attn_head_v_all_pos(
                model, corrupted_batch, clean_cache, metric, **kwargs
            ),
        ),
        (
            "pattern",
            get_act_patch_attn_head_pattern_all_pos(
                model,
                corrupted_batch,
                clean_cache,
                metric,
                **kwargs,
            ),
        ),
    ]
    if _returns_details(kwargs):
        return dict(named_outputs)
    return _stack_named_metric_outputs(_pad_kv_metric_outputs(named_outputs))


def get_act_patch_attn_head_by_pos_every(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric | None = None,
    **kwargs: Any,
) -> Any:
    """Patch `z`, `q`, `k`, `v`, and `pattern` by position where applicable."""
    metric = _resolve_patching_metric(metric, kwargs, "get_act_patch_attn_head_by_pos_every")
    pattern_output = get_act_patch_attn_head_pattern_by_pos(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        **kwargs,
    )
    named_outputs = [
        (
            "z",
            get_act_patch_attn_head_out_by_pos(
                model,
                corrupted_batch,
                clean_cache,
                metric,
                **kwargs,
            ),
        ),
        (
            "q",
            get_act_patch_attn_head_q_by_pos(model, corrupted_batch, clean_cache, metric, **kwargs),
        ),
        (
            "k",
            get_act_patch_attn_head_k_by_pos(model, corrupted_batch, clean_cache, metric, **kwargs),
        ),
        (
            "v",
            get_act_patch_attn_head_v_by_pos(model, corrupted_batch, clean_cache, metric, **kwargs),
        ),
        (
            "pattern",
            pattern_output,
        ),
    ]
    if _returns_details(kwargs):
        return dict(named_outputs)
    named_outputs[-1] = ("pattern", _move_metric_axis(pattern_output, 1, 2))
    return _stack_named_metric_outputs(_pad_kv_metric_outputs(named_outputs))


def _component_helper_kwargs(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    """Return helper kwargs with TransformerLens-style grid output by default."""
    helper_kwargs = dict(kwargs)
    helper_kwargs.setdefault("return_details", False)
    return helper_kwargs


def _component_patch_overrides(
    kwargs: dict[str, Any],
    *,
    default_component: str,
    default_patch_setter: PatchSetter,
    default_index_axis_names: Sequence[AxisName],
) -> tuple[str, PatchSetter | TransformerLensPatchSetter, Sequence[AxisName] | None]:
    """Extract TL partial-style override kwargs for component patch helpers."""
    activation_name = kwargs.pop("activation_name", default_component)
    patch_setter = kwargs.pop("patch_setter", default_patch_setter)
    index_axis_names = kwargs.pop("index_axis_names", default_index_axis_names)
    return activation_name, patch_setter, index_axis_names


def _resolve_patching_metric(
    metric: PatchMetric | None,
    kwargs: dict[str, Any],
    helper_name: str,
) -> PatchMetric:
    """Accept both SafeLens `metric` and TransformerLens `patching_metric` names."""
    patching_metric = kwargs.pop("patching_metric", None)
    if metric is not None and patching_metric is not None:
        raise TypeError(f"{helper_name} got both `metric` and `patching_metric`.")
    resolved_metric = metric if metric is not None else patching_metric
    if resolved_metric is None:
        raise TypeError(f"{helper_name} requires `metric` or `patching_metric`.")
    if not callable(resolved_metric):
        raise TypeError(f"{helper_name} expected a callable metric.")
    return resolved_metric


def _returns_details(kwargs: Mapping[str, Any]) -> bool:
    return kwargs.get("return_details") is True


def _split_metric_output(output: Any) -> tuple[Any, Any | None]:
    if isinstance(output, tuple) and len(output) == 2:
        return output[0], output[1]
    return output, None


def _replace_metric_output(output: Any, metric_output: Any) -> Any:
    _metric_output, index_table = _split_metric_output(output)
    if index_table is None:
        return metric_output
    return metric_output, index_table


def _stack_named_metric_outputs(named_outputs: Sequence[tuple[str, Any]]) -> Any:
    metric_outputs: list[Any] = []
    index_tables: dict[str, Any] = {}
    for name, output in named_outputs:
        metric_output, index_table = _split_metric_output(output)
        metric_outputs.append(metric_output)
        if index_table is not None:
            index_tables[name] = index_table

    stacked_output = _stack_metric_outputs(metric_outputs)
    if index_tables:
        return stacked_output, index_tables
    return stacked_output


def _stack_metric_outputs(metric_outputs: Sequence[Any]) -> Any:
    if not metric_outputs:
        return []
    try:
        import torch

        if any(hasattr(output, "shape") for output in metric_outputs):
            return torch.stack([torch.as_tensor(output) for output in metric_outputs], dim=0)
    except ImportError:
        pass
    except (AttributeError, RuntimeError, TypeError, ValueError):
        pass
    return [to_python_container(output) for output in metric_outputs]


def _pad_kv_metric_outputs(named_outputs: Sequence[tuple[str, Any]]) -> list[tuple[str, Any]]:
    metric_outputs = [_split_metric_output(output)[0] for _name, output in named_outputs]
    last_dim = max(
        (shape_of(output)[-1] for output in metric_outputs if shape_of(output)), default=0
    )
    padded_outputs: list[tuple[str, Any]] = []
    for name, output in named_outputs:
        if name in {"k", "v"}:
            metric_output, _index_table = _split_metric_output(output)
            output = _replace_metric_output(output, _pad_metric_last_dim(metric_output, last_dim))
        padded_outputs.append((name, output))
    return padded_outputs


def _pad_metric_last_dim(metric_output: Any, width: int) -> Any:
    shape = shape_of(metric_output)
    if not shape or shape[-1] >= width:
        return metric_output
    pad_width = width - shape[-1]
    try:
        import torch

        if hasattr(metric_output, "shape"):
            return torch.nn.functional.pad(metric_output, (0, pad_width))
    except ImportError:
        pass
    except (AttributeError, RuntimeError, TypeError, ValueError):
        pass
    return _pad_nested_last_dim(metric_output, pad_width)


def _pad_nested_last_dim(value: Any, pad_width: int) -> Any:
    if not is_sequence(value):
        return value
    value_list = [to_python_container(item) for item in value]
    if not value_list or not is_sequence(value_list[0]):
        return [*value_list, *([0.0] * pad_width)]
    return [_pad_nested_last_dim(item, pad_width) for item in value_list]


def _move_metric_axis(output: Any, source: int, destination: int) -> Any:
    metric_output, _index_table = _split_metric_output(output)
    return _replace_metric_output(output, _move_axis(metric_output, source, destination))


def _move_axis(value: Any, source: int, destination: int) -> Any:
    try:
        movedim = value.movedim
        if callable(movedim):
            return movedim(source, destination)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        pass

    shape = shape_of(value)
    rank = len(shape)
    if rank == 0:
        return value
    if source < 0:
        source += rank
    if destination < 0:
        destination += rank
    if source == destination:
        return value
    if not (0 <= source < rank and 0 <= destination < rank):
        raise ValueError(f"Cannot move axis {source} to {destination} for shape {shape!r}.")

    output_shape = list(shape)
    moved_dim = output_shape.pop(source)
    output_shape.insert(destination, moved_dim)

    def read_output(coordinate: tuple[int, ...]) -> Any:
        input_coordinate = list(coordinate)
        moved_coordinate = input_coordinate.pop(destination)
        input_coordinate.insert(source, moved_coordinate)
        return get_indexed(value, tuple(input_coordinate))

    return _build_nested_from_shape(tuple(output_shape), read_output)


def _build_nested_from_shape(
    shape: tuple[int, ...],
    value_fn: Callable[[tuple[int, ...]], Any],
    prefix: tuple[int, ...] = (),
) -> Any:
    if not shape:
        return value_fn(prefix)
    return [
        _build_nested_from_shape(shape[1:], value_fn, (*prefix, index)) for index in range(shape[0])
    ]


def _layer_pos_component_patch(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    metric: PatchMetric,
    component: str,
    kwargs: dict[str, Any],
) -> list[PatchResult]:
    activation_name, patch_setter, index_axis_names = _component_patch_overrides(
        kwargs,
        default_component=component,
        default_patch_setter=layer_pos_patch_setter,
        default_index_axis_names=("layer", "pos"),
    )
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=patch_setter,
        index_axis_names=index_axis_names,
        activation_name=activation_name,
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
    activation_name, patch_setter, index_axis_names = _component_patch_overrides(
        kwargs,
        default_component=component,
        default_patch_setter=layer_pos_head_vector_patch_setter,
        default_index_axis_names=("layer", "pos", "head"),
    )
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=patch_setter,
        index_axis_names=index_axis_names,
        activation_name=activation_name,
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
    activation_name, patch_setter, index_axis_names = _component_patch_overrides(
        kwargs,
        default_component=component,
        default_patch_setter=layer_head_vector_patch_setter,
        default_index_axis_names=("layer", "head"),
    )
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=patch_setter,
        index_axis_names=index_axis_names,
        activation_name=activation_name,
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
    activation_name, patch_setter, index_axis_names = _component_patch_overrides(
        kwargs,
        default_component=component,
        default_patch_setter=layer_head_pattern_patch_setter,
        default_index_axis_names=("layer", "head_index"),
    )
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=patch_setter,
        index_axis_names=index_axis_names,
        activation_name=activation_name,
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
    activation_name, patch_setter, index_axis_names = _component_patch_overrides(
        kwargs,
        default_component=component,
        default_patch_setter=layer_head_pos_pattern_patch_setter,
        default_index_axis_names=("layer", "head_index", "dest_pos"),
    )
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=patch_setter,
        index_axis_names=index_axis_names,
        activation_name=activation_name,
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
    activation_name, patch_setter, index_axis_names = _component_patch_overrides(
        kwargs,
        default_component=component,
        default_patch_setter=layer_head_dest_src_pos_pattern_patch_setter,
        default_index_axis_names=("layer", "head_index", "dest_pos", "src_pos"),
    )
    return component_activation_patch(
        model,
        corrupted_batch,
        clean_cache,
        metric,
        component=component,
        patch_setter=patch_setter,
        index_axis_names=index_axis_names,
        activation_name=activation_name,
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


def batch_prefixed_slice(has_batch_dim: bool, *indices: Any) -> tuple[Any, ...]:
    """Return a slice tuple with an optional leading batch axis."""
    if has_batch_dim:
        return (FULL_SLICE, *indices)
    return tuple(indices)


def patch_source_has_batch_dim(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache | Any,
) -> bool:
    """Return whether the clean activation used by a patch includes batch."""
    if spec.value is not None:
        clean_rank = len(shape_of(spec.value))
        corrupted_rank = len(shape_of(corrupted_activation))
        if corrupted_rank == clean_rank + 1:
            return False
        if clean_rank == corrupted_rank + 1:
            return True
    if isinstance(clean_cache, ActivationCache):
        return clean_cache.has_batch_dim
    return True


def patch_target_has_batch_dim(
    corrupted_activation: Any,
    spec: PatchSpec,
    clean_cache: ActivationCache | Any,
) -> bool:
    """Infer whether the current corrupted activation includes a batch axis."""
    clean_activation = spec.value if spec.value is not None else clean_cache[spec.clean_name]
    clean_rank = len(shape_of(clean_activation))
    corrupted_rank = len(shape_of(corrupted_activation))
    if spec.value is not None:
        if corrupted_rank == clean_rank + 1:
            return True
        if corrupted_rank + 1 == clean_rank:
            return False
    if patch_source_has_batch_dim(corrupted_activation, spec, clean_cache):
        return corrupted_rank + 1 != clean_rank
    return corrupted_rank == clean_rank + 1


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
    patch_value = broadcast_patch_value_to_slice(corrupted_activation, target_slice, patch_value)
    patched = clone_patch_target(corrupted_activation)
    if spec.mode == "replace":
        set_indexed(patched, target_slice, patch_value)
        return patched
    if spec.mode == "add":
        current_value = get_indexed(patched, target_slice)
        set_indexed(patched, target_slice, add_values(current_value, patch_value))
        return patched
    raise ValueError(f"Unsupported patch mode: {spec.mode}")


def broadcast_patch_value_to_slice(
    corrupted_activation: Any,
    target_slice: tuple[Any, ...],
    patch_value: Any,
) -> Any:
    """Broadcast a no-batch patch value across a batched target slice when needed."""
    target_shape = shape_of(get_indexed(corrupted_activation, target_slice))
    patch_shape = shape_of(patch_value)
    if target_shape == patch_shape or not target_shape:
        return patch_value
    if target_shape[1:] == patch_shape:
        return repeat_value_like(patch_value, target_shape[0])
    if patch_shape[1:] == target_shape and patch_shape[0] == 1:
        return get_indexed(patch_value, 0)
    return patch_value


def repeat_value_like(value: Any, times: int) -> Any:
    """Clone a value `times` times while preserving tensor/array backends when possible."""
    try:
        import torch

        if isinstance(value, torch.Tensor):
            return value.unsqueeze(0).expand((times, *value.shape)).clone()
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(value, np.ndarray):
            return np.broadcast_to(value, (times, *value.shape)).copy()
    except Exception:
        pass
    return [clone_activation(value) for _ in range(times)]


def maybe_apply_transformer_lens_patch_setter(
    corrupted_activation: Any,
    index_or_spec: Any,
    clean_activation_or_cache: Any,
    *,
    expected_length: int,
    setter_name: str,
    min_batched_rank: int,
    target_slice_fn: Callable[[tuple[Any, ...]], tuple[Any, ...]],
    source_slice_fn: Callable[[tuple[Any, ...]], tuple[Any, ...]],
) -> Any | None:
    """Apply a direct TL-style patch setter call when no PatchSpec is supplied."""
    if isinstance(index_or_spec, PatchSpec):
        return None
    index = normalize_index(index_or_spec)
    if len(index) != expected_length:
        raise ValueError(
            f"{setter_name} expects an index of length {expected_length}; got {index!r}."
        )
    patched = clone_patch_target(corrupted_activation)
    target_slice = _maybe_drop_batch_slice(
        target_slice_fn(index),
        corrupted_activation,
        clean_activation_or_cache,
        min_batched_rank=min_batched_rank,
    )
    source_slice = _maybe_drop_batch_slice(
        source_slice_fn(index),
        clean_activation_or_cache,
        corrupted_activation,
        min_batched_rank=min_batched_rank,
    )
    patch_value = get_indexed(clean_activation_or_cache, source_slice)
    patch_value = broadcast_patch_value_to_slice(corrupted_activation, target_slice, patch_value)
    set_indexed(patched, target_slice, patch_value)
    return patched


def _maybe_drop_batch_slice(
    index: tuple[Any, ...],
    value: Any,
    reference: Any,
    *,
    min_batched_rank: int,
) -> tuple[Any, ...]:
    """Drop a TL-style leading batch slice when this value has no batch axis."""
    if not index or index[0] != FULL_SLICE:
        return index
    value_rank = len(shape_of(value))
    if value_rank < min_batched_rank:
        return index[1:]
    reference_rank = len(shape_of(reference))
    if value_rank + 1 == reference_rank:
        return index[1:]
    return index


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
    normalized = expand_ellipsis_index(normalize_index(index), len(shape_of(value)))
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
    normalized = expand_ellipsis_index(normalize_index(index), len(shape_of(value)))
    replacement = coerce_value_like(value, replacement)
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


def expand_ellipsis_index(index: tuple[Any, ...], rank: int) -> tuple[Any, ...]:
    """Expand a single ellipsis into full slices for dependency-free indexing."""
    if Ellipsis not in index:
        return index
    if index.count(Ellipsis) > 1:
        raise IndexError("an index can only have a single ellipsis")
    consumed_dims = len([item for item in index if item is not None and item is not Ellipsis])
    fill = max(0, rank - consumed_dims)
    expanded: list[Any] = []
    for item in index:
        if item is Ellipsis:
            expanded.extend([FULL_SLICE] * fill)
        else:
            expanded.append(item)
    return tuple(expanded)


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
    """Scale tensor-like or nested Python sequence values."""
    if scale == 1.0:
        return value
    try:
        return value * scale
    except TypeError:
        if is_sequence(value):
            return [scale_value(item, scale) for item in value]
        return value


def add_values(left: Any, right: Any) -> Any:
    """Add tensor-like or nested Python sequence values elementwise."""
    right = coerce_value_like(left, right)
    if is_sequence(left) and is_sequence(right):
        return [
            add_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        ]
    try:
        return left + right
    except TypeError:
        return right


def coerce_value_like(reference: Any, value: Any) -> Any:
    """Coerce patch values to the target activation backend when possible."""
    if is_sequence(reference):
        return to_python_container(value)

    torch_value = coerce_torch_value_like(reference, value)
    if torch_value is not value:
        return torch_value

    numpy_value = coerce_numpy_value_like(reference, value)
    if numpy_value is not value:
        return numpy_value

    return value


def coerce_torch_value_like(reference: Any, value: Any) -> Any:
    """Return `value` as a torch tensor matching `reference`, if applicable."""
    try:
        import torch
    except ImportError:
        return value

    if not isinstance(reference, torch.Tensor):
        return value
    if isinstance(value, torch.Tensor):
        if value.dtype == reference.dtype and value.device == reference.device:
            return value
        return value.to(dtype=reference.dtype, device=reference.device)
    return torch.as_tensor(value, dtype=reference.dtype, device=reference.device)


def coerce_numpy_value_like(reference: Any, value: Any) -> Any:
    """Return `value` as a numpy array matching `reference`, if applicable."""
    try:
        import numpy as np
    except ImportError:
        return value

    if not isinstance(reference, np.ndarray):
        return value
    if isinstance(value, np.ndarray):
        return value.astype(reference.dtype, copy=False)
    return np.asarray(tensor_to_numpy_source(value), dtype=reference.dtype)


def tensor_to_numpy_source(value: Any) -> Any:
    """Detach/copy tensor-like values before numpy converts them."""
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    numpy = getattr(value, "numpy", None)
    if callable(numpy):
        return numpy()
    return value


def to_python_container(value: Any) -> Any:
    """Convert array/tensor/tuple values into mutable Python containers."""
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    if is_sequence(value):
        return [to_python_container(item) for item in value]
    return value


def mutable_patch_target(value: Any) -> Any:
    """Return a patchable target, converting immutable nested sequences to lists."""
    if isinstance(value, list):
        return [mutable_patch_target(item) for item in value]
    if is_sequence(value):
        return [mutable_patch_target(item) for item in value]
    return value


def clone_patch_target(value: Any) -> Any:
    """Clone a patch target and convert immutable nested sequences to lists."""
    return mutable_patch_target(clone_activation(value))


def clone_patch_target_if_requires_grad(value: Any) -> Any:
    """Clone gradient-tracked patch targets before TL-style in-place setters run."""
    if getattr(value, "requires_grad", False):
        return clone_patch_target(value)
    return value


def is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def infer_layers(
    model: ModelWrapper,
    clean_cache: ActivationCache,
    component: str,
    *,
    name_style: ActivationNameStyle = "safelens",
) -> list[LayerRef]:
    """Infer layer indices from model config or clean cache names."""
    layers_from_cache = infer_layers_from_cache(clean_cache, component, name_style=name_style)
    if layers_from_cache:
        return layers_from_cache

    if _component_uses_decoder_layer_count(component):
        n_decoder_layers = get_config_int(
            model,
            ("n_decoder_layers", "num_decoder_layers", "decoder_layers"),
        )
        if n_decoder_layers is not None:
            return list(range(n_decoder_layers))

    n_layers = get_config_int(model, ("n_layers", "num_hidden_layers", "num_layers"))
    if n_layers is not None:
        return list(range(n_layers))

    raise ValueError("Could not infer layers. Pass `layers=[...]` explicitly.")


def infer_layers_from_cache(
    clean_cache: ActivationCache,
    component: str,
    *,
    name_style: ActivationNameStyle = "safelens",
) -> list[LayerRef]:
    """Infer layer indices from SafeLens or TransformerLens-style activation names."""
    _ = name_style
    explicit_ref = _explicit_activation_ref(component)
    if explicit_ref is not None:
        explicit_layer, explicit_component = explicit_ref
        if component in clean_cache:
            return [explicit_layer]
        component = explicit_component
    layers: set[int] = set()
    for name in clean_cache:
        parsed = _layer_and_component_from_cache_name(name)
        if parsed is None:
            continue
        layer, cache_component = parsed
        if _normalize_patch_component(cache_component) == _normalize_patch_component(component):
            layers.add(layer)
    return sorted(layers)


def _component_uses_decoder_layer_count(component: str) -> bool:
    normalized = _normalize_patch_component(component)
    if normalized.startswith("decoder_") or normalized.startswith("cross_"):
        return True
    explicit_ref = _explicit_activation_ref(component)
    return explicit_ref is not None and (
        explicit_ref[1].startswith("decoder_") or explicit_ref[1].startswith("cross_")
    )


def _layer_and_component_from_cache_name(name: str) -> tuple[int, str] | None:
    safe_match = re.fullmatch(
        r"layer_(\d+)\.([a-zA-Z0-9_]+)(?:\.([a-zA-Z0-9_]+))?",
        name,
    )
    if safe_match is not None:
        return int(safe_match.group(1)), safe_match.group(3) or safe_match.group(2)

    block_match = re.fullmatch(
        r"(blocks|encoder|decoder)\.(\d+)\.(?:([a-zA-Z0-9_]+)\.)?hook_([a-zA-Z0-9_]+)",
        name,
    )
    if block_match is not None:
        stack = block_match.group(1)
        layer = int(block_match.group(2))
        layer_type = block_match.group(3)
        component = _component_from_transformer_lens_cache_name(
            stack,
            layer_type,
            block_match.group(4),
        )
        return layer, component

    return None


def _component_from_transformer_lens_cache_name(
    stack: str,
    layer_type: str | None,
    component: str,
) -> str:
    component = _normalize_patch_component(component)
    if component == "scores":
        component = "attn_scores"
    normalized_layer_type = {
        "a": "attn",
        "attention": "attn",
        "m": "mlp",
    }.get(layer_type or "", layer_type)
    attention_prefix = PREFIXED_ATTENTION_LAYER_TYPES.get(normalized_layer_type or "")
    if stack == "decoder" and normalized_layer_type == "attn":
        attention_prefix = "decoder"
    if attention_prefix is not None:
        if component == "out":
            return f"{attention_prefix}_attn_out"
        if component in ATTENTION_VECTOR_COMPONENTS:
            return f"{attention_prefix}_{component}"
    if (
        stack == "decoder"
        and normalized_layer_type == "mlp"
        and component in DECODER_MLP_COMPONENTS
    ):
        return f"decoder_{component}"
    if (
        stack == "decoder"
        and normalized_layer_type in {"ln1", "ln2", "ln3"}
        and component in {"scale", "normalized"}
    ):
        return f"decoder_{normalized_layer_type}_{component}"
    if stack == "decoder" and normalized_layer_type is None:
        if component in DECODER_TOP_LEVEL_COMPONENTS:
            return f"decoder_{component}"
        if component in CROSS_TOP_LEVEL_COMPONENTS:
            return component
    if stack == "encoder" and normalized_layer_type == "attn" and component == "out":
        return "attn_out"
    if stack == "encoder" and normalized_layer_type == "mlp" and component == "out":
        return "mlp_out"
    if (
        stack == "blocks"
        and normalized_layer_type == "decoder_mlp"
        and component in DECODER_MLP_COMPONENTS
    ):
        return f"decoder_{component}"
    return _normalize_component_for_layer_type(component, normalized_layer_type)


def _explicit_activation_ref(name: str) -> tuple[int, str] | None:
    parsed = _layer_and_component_from_cache_name(name)
    if parsed is None:
        return None
    layer, component = parsed
    return layer, _normalize_patch_component(component)


def _same_layer_ref(layer: LayerRef, explicit_layer: int) -> bool:
    layer_ref = _explicit_layer_ref(layer)
    if layer_ref is not None:
        return layer_ref[0] == explicit_layer
    try:
        return int(layer) == explicit_layer
    except (TypeError, ValueError):
        return False


def _explicit_layer_ref(layer: LayerRef) -> tuple[int, str] | None:
    if isinstance(layer, tuple):
        if len(layer) < 2 or not isinstance(layer[1], int):
            return None
        component = str(layer[0]).removeprefix("hook_")
        layer_type = str(layer[2]) if len(layer) >= 3 and layer[2] is not None else None
        component = _normalize_component_for_layer_type(component, layer_type)
        return int(layer[1]), _normalize_patch_component(component)
    if isinstance(layer, str):
        return _explicit_activation_ref(layer)
    return None


def _patch_index_layer_value(layer: LayerRef) -> LayerRef:
    layer_ref = _explicit_layer_ref(layer)
    if layer_ref is not None:
        return layer_ref[0]
    return layer


def _normalize_component_for_layer_type(component: str, layer_type: str | None) -> str:
    normalized_layer_type = {
        "a": "attn",
        "attention": "attn",
        "m": "mlp",
    }.get(layer_type or "", layer_type)
    if normalized_layer_type == "attn" and component == "out":
        return "attn_out"
    if normalized_layer_type == "mlp" and component == "out":
        return "mlp_out"
    return component


def _normalize_patch_component(component: str) -> str:
    aliases = {
        "attn": "pattern",
        "attn_logits": "attn_scores",
        "key": "k",
        "query": "q",
        "value": "v",
        "mlp_pre": "pre",
        "mlp_mid": "mid",
        "mlp_post": "post",
    }
    return aliases.get(component, component)


def infer_positions(
    corrupted_batch: Any,
    clean_cache: ActivationCache,
    component: str,
    layers: Sequence[LayerRef],
    *,
    axis_name: AxisName = "pos",
) -> int:
    """Infer sequence length from batch tensors or cached activations."""
    activation = first_component_activation(clean_cache, component, layers)
    normalized_component = _normalize_patch_component(component)
    if activation is not None:
        shape = shape_of(activation)
        has_batch_dim = getattr(clean_cache, "has_batch_dim", True)
        if normalized_component in PATTERN_COMPONENTS and len(shape) >= (4 if has_batch_dim else 3):
            if axis_name == "src_pos":
                return int(shape[-1])
            return int(shape[-2])
        if len(shape) >= (2 if has_batch_dim else 1):
            return int(shape[1 if has_batch_dim else 0])

    batch_positions = infer_positions_from_batch(corrupted_batch)
    if batch_positions is not None:
        return batch_positions

    raise ValueError("Could not infer positions. Pass `positions=[...]` explicitly.")


def infer_positions_from_batch(batch: Any) -> int | None:
    """Infer token positions from tokenized or embedded batch inputs."""
    if isinstance(batch, Mapping):
        for key in ("input_ids", "tokens", "token_ids"):
            if key in batch:
                positions = token_positions_from_value(batch[key])
                if positions is not None:
                    return positions
        for key in ("inputs_embeds", "input_embeds", "embeds"):
            if key in batch:
                positions = embed_positions_from_shape(shape_of(batch[key]))
                if positions is not None:
                    return positions
        return None

    if is_text_batch(batch):
        return None
    return token_positions_from_value(batch)


def token_positions_from_value(value: Any) -> int | None:
    """Return sequence length from token-id values, including scalar ids."""
    if isinstance(value, Integral):
        return 1
    shape = shape_of(value)
    if shape:
        return token_positions_from_shape(shape)
    if getattr(value, "shape", None) is not None:
        return 1
    return None


def token_positions_from_shape(shape: Sequence[int]) -> int | None:
    """Return sequence length from token-id shapes `[pos]` or `[batch, pos]`."""
    if len(shape) == 1:
        return int(shape[0])
    if len(shape) >= 2:
        return int(shape[-1])
    return None


def embed_positions_from_shape(shape: Sequence[int]) -> int | None:
    """Return sequence length from embedding shapes `[pos, d_model]` or `[batch, pos, d_model]`."""
    if len(shape) >= 2:
        return int(shape[-2])
    return None


def is_text_batch(value: Any) -> bool:
    """Return whether a value is raw text rather than token ids."""
    if isinstance(value, str | bytes):
        return True
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        if not value:
            return False
        return isinstance(value[0], str | bytes)
    return False


def infer_heads(
    model: ModelWrapper,
    clean_cache: ActivationCache,
    component: str,
    layers: Sequence[LayerRef],
) -> int:
    """Infer number of heads from model config or cached activations."""
    activation = first_component_activation(clean_cache, component, layers)
    normalized_component = _normalize_patch_component(component)
    if activation is not None:
        shape = shape_of(activation)
        has_batch_dim = getattr(clean_cache, "has_batch_dim", True)
        if normalized_component in PATTERN_COMPONENTS and len(shape) >= (2 if has_batch_dim else 1):
            return shape[1 if has_batch_dim else 0]
        if len(shape) >= (3 if has_batch_dim else 2):
            return shape[2 if has_batch_dim else 1]

    if normalized_component in {"k", "v", "decoder_k", "decoder_v", "cross_k", "cross_v"}:
        n_key_value_heads = get_model_key_value_heads(model)
        if n_key_value_heads is not None:
            return n_key_value_heads

    n_heads = get_config_int(model, ("n_heads", "num_attention_heads"))
    if n_heads is not None:
        return n_heads

    raise ValueError("Could not infer heads. Pass `heads=[...]` explicitly.")


def infer_index_table(
    model: ModelWrapper,
    corrupted_batch: Batch,
    clean_cache: ActivationCache,
    activation_name: str,
    index_axis_names: Sequence[AxisName],
    *,
    name_style: ActivationNameStyle = "safelens",
) -> list[dict[str, Any]]:
    """Infer a TL-style patch index table from axis names."""
    layers = infer_layers(model, clean_cache, activation_name, name_style=name_style)
    axis_values: dict[AxisName, Iterable[int]] = {"layer": layers}
    if "pos" in index_axis_names:
        axis_values["pos"] = range(
            infer_positions(
                corrupted_batch,
                clean_cache,
                activation_name,
                layers,
                axis_name="pos",
            )
        )
    if "head" in index_axis_names:
        axis_values["head"] = range(infer_heads(model, clean_cache, activation_name, layers))
    if "head_index" in index_axis_names:
        axis_values["head_index"] = range(infer_heads(model, clean_cache, activation_name, layers))
    if "dest_pos" in index_axis_names:
        axis_values["dest_pos"] = range(
            infer_positions(
                corrupted_batch,
                clean_cache,
                activation_name,
                layers,
                axis_name="dest_pos",
            )
        )
    if "src_pos" in index_axis_names:
        axis_values["src_pos"] = range(
            infer_positions(
                corrupted_batch,
                clean_cache,
                activation_name,
                layers,
                axis_name="src_pos",
            )
        )
    return make_index_table(index_axis_names, axis_values)


def make_index_table(
    index_axis_names: Sequence[AxisName],
    axis_values: Mapping[AxisName, Iterable[int]],
) -> list[dict[str, Any]]:
    """Create an ordered list of index rows from named axis values."""
    rows: list[dict[str, Any]] = []
    value_lists = [_axis_values(axis_values, axis_name) for axis_name in index_axis_names]
    for values in product(*value_lists):
        rows.append(dict(zip(index_axis_names, values, strict=True)))
    return rows


def normalize_index_table(
    index_df: Any,
    index_axis_names: Sequence[AxisName] | None = None,
) -> tuple[list[dict[str, Any]], Sequence[AxisName]]:
    """Normalize pandas-like, dict, or sequence index tables."""
    columns = list(index_axis_names) if index_axis_names is not None else None
    to_dict = getattr(index_df, "to_dict", None)
    if callable(to_dict):
        try:
            records = to_dict("records")
            if columns is None:
                columns = list(index_df.columns)
            return [dict(record) for record in records], tuple(columns)
        except TypeError:
            pass

    rows: list[dict[str, Any]] = []
    for row in index_df:
        if isinstance(row, Mapping):
            if columns is None:
                columns = list(row.keys())
            rows.append({column: row[column] for column in columns if column in row})
        else:
            if columns is None:
                raise ValueError("Pass `index_axis_names` when index rows are not mappings.")
            rows.append(dict(zip(columns, row, strict=True)))
    if columns is None:
        columns = []
    return rows, tuple(columns)


def first_component_activation(
    clean_cache: ActivationCache,
    component: str,
    layers: Sequence[LayerRef],
) -> Any:
    """Return the first activation matching a component and layer list."""
    layer_set = {_coerce_int_layer(layer) for layer in layers}
    layer_set.discard(None)
    if component in clean_cache:
        explicit_ref = _explicit_activation_ref(component)
        if explicit_ref is None or explicit_ref[0] in layer_set or not layer_set:
            return clean_cache[component]
        return None
    explicit_layer: int | None = None
    explicit_ref = _explicit_activation_ref(component)
    if explicit_ref is not None:
        explicit_layer = explicit_ref[0]
        component = explicit_ref[1]
        if layer_set and explicit_layer not in layer_set:
            return None
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
        parsed = _layer_and_component_from_cache_name(name)
        if parsed is None:
            continue
        layer, cache_component = parsed
        if layer_set and layer not in layer_set:
            continue
        if explicit_layer is not None and layer != explicit_layer:
            continue
        if _normalize_patch_component(cache_component) == _normalize_patch_component(component):
            return activation
    return None


def _coerce_int_layer(layer: Any) -> int | None:
    try:
        return int(layer)
    except (TypeError, ValueError):
        return None


def shape_of(value: Any) -> tuple[int, ...]:
    """Return a best-effort shape for tensor-like or nested-list values."""
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
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
    for owner in _expand_config_owners(owners):
        if owner is None:
            continue
        for name in names:
            value = _config_value(owner, name)
            if value is not None:
                return int(value)
    return None


def _expand_config_owners(owners: Sequence[Any]) -> list[Any]:
    expanded: list[Any] = []
    for owner in owners:
        if owner is None:
            continue
        expanded.append(owner)
        config = _config_value(owner, "config")
        if config is not None and config is not owner:
            expanded.append(config)
        for nested_name in ("text_config", "language_config", "decoder", "decoder_config"):
            nested = _config_value(owner, nested_name)
            if nested is not None:
                expanded.append(nested)
    return expanded


def _config_value(owner: Any, name: str) -> Any:
    if isinstance(owner, Mapping):
        return owner.get(name)
    try:
        return getattr(owner, name)
    except Exception:
        return None


def get_model_key_value_heads(model: Any) -> int | None:
    """Read K/V head count from SafeLens wrappers or raw Transformers models."""
    cfg = getattr(model, "cfg", None)
    cfg_n_kv_heads = getattr(cfg, "n_key_value_heads", None)
    if cfg_n_kv_heads is not None:
        return int(cfg_n_kv_heads)
    try:
        from SafeLens.utils.model_bridge import key_value_head_count

        wrapped_model = getattr(model, "model", None)
        for candidate in (wrapped_model, model):
            if candidate is None:
                continue
            n_key_value_heads = key_value_head_count(candidate)
            if n_key_value_heads is not None:
                return n_key_value_heads
    except ImportError:
        pass
    return get_config_int(model, ("n_key_value_heads", "num_key_value_heads", "num_kv_heads"))


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


def make_nested_grid(shape: Sequence[int], *, fill_value: float = 0.0) -> Any:
    """Create a nested-list metric grid with the requested shape."""
    if not shape:
        return fill_value
    return [make_nested_grid(shape[1:], fill_value=fill_value) for _ in range(shape[0])]


def _ordered_unique(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
