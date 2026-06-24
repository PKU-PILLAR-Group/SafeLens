"""Dependency-light visualization primitives for interpretability workflows."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from html import escape
from itertools import count
from pathlib import Path
from typing import Any

from SafeLens.core.base import RunReport, SafetyReport

Number = int | float
_VIZ_ID_COUNTER = count()
_TOPK_SAMPLE_HEADERS = ["layer", "neuron", "rank", "sample", "max_token", "max_value"]


@dataclass(slots=True)
class Visualization:
    """Notebook-displayable visualization payload.

    `Visualization` keeps a plain data payload next to HTML so tests, scripts,
    and non-notebook callers can consume the same result without parsing markup.
    """

    html: str
    data: dict[str, Any] = field(default_factory=dict)
    title: str | None = None

    def _repr_html_(self) -> str:
        return self.html

    def to_html(self, *, full_document: bool = False) -> str:
        if not full_document:
            return self.html
        title = escape(self.title or "SafeLens Visualization")
        return (
            '<!doctype html><html><head><meta charset="utf-8">'
            f"<title>{title}</title></head><body>{self.html}</body></html>"
        )

    def save_html(self, path: str | Path, *, full_document: bool = True) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_html(full_document=full_document), encoding="utf-8")
        return output_path


def export_html(
    visualization: Visualization,
    path: str | Path,
    *,
    full_document: bool = True,
) -> Path:
    """Write a visualization to an HTML file."""

    return visualization.save_html(path, full_document=full_document)


def colored_tokens(
    tokens: Sequence[Any],
    values: Sequence[Any],
    *,
    title: str | None = "Token Attributions",
    labels: Sequence[str] | None = None,
    color: str = "red_blue",
) -> Visualization:
    """Render token-level scalar values as colored spans.

    This mirrors the most common CircuitsVis token-highlighting workflow while
    remaining usable without JavaScript or optional packages.
    """

    token_list = [str(token) for token in tokens]
    value_list = [_scalar(value) for value in values]
    if len(token_list) != len(value_list):
        raise ValueError("tokens and values must have the same length.")
    label_list = [str(label) for label in labels] if labels is not None else None
    if label_list is not None and len(label_list) != len(token_list):
        raise ValueError("labels must have the same length as tokens.")

    min_value, max_value = _value_range(value_list)
    spans = []
    for idx, (token, value) in enumerate(zip(token_list, value_list, strict=True)):
        background, foreground = _value_color(value, min_value, max_value, color=color)
        label = label_list[idx] if label_list is not None else f"{value:.4g}"
        spans.append(
            '<span class="safelens-token" '
            f'title="{escape(label)}" '
            f'style="background:{background};color:{foreground};'
            "padding:0.15rem 0.22rem;margin:0.08rem;border-radius:4px;"
            'display:inline-block;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;">'
            f"{escape(token)}</span>"
        )
    html = _wrap_panel("tokens", title, "".join(spans) + _legend(min_value, max_value))
    return Visualization(
        html=html,
        title=title,
        data={"tokens": token_list, "values": value_list, "labels": label_list},
    )


def colored_tokens_multi(
    tokens: Sequence[Any],
    values: Any,
    *,
    labels: Sequence[str] | None = None,
    title: str | None = "Token Attributions",
) -> Visualization:
    """Render multiple token-level value tracks with an interactive selector."""

    token_list = [str(token) for token in tokens]
    matrix = _as_2d_numbers(values)
    if len(matrix) != len(token_list):
        raise ValueError("values must have one row per token.")
    if not matrix:
        raise ValueError("values must be non-empty.")
    width = len(matrix[0])
    label_list = (
        [str(label) for label in labels]
        if labels is not None
        else [f"value_{idx}" for idx in range(width)]
    )
    if len(label_list) != width:
        raise ValueError("labels length must match the value column count.")

    viz_id = _next_viz_id("tokens-multi")
    columns = [[row[col_idx] for row in matrix] for col_idx in range(width)]
    colors = []
    for track_values in columns:
        min_value, max_value = _value_range(track_values)
        colors.append(
            [_value_color(value, min_value, max_value, color="red_blue") for value in track_values]
        )
    buttons = "".join(
        '<button type="button" '
        f'class="safelens-control-button{" is-active" if idx == 0 else ""}" '
        f'data-track="{idx}">{escape(label)}</button>'
        for idx, label in enumerate(label_list)
    )
    token_spans = []
    for idx, token in enumerate(token_list):
        background, foreground = colors[0][idx]
        token_spans.append(
            '<span class="safelens-token safelens-live-token" '
            f'data-token-index="{idx}" '
            f'title="{escape(label_list[0])}: {columns[0][idx]:.6g}" '
            f'style="background:{background};color:{foreground};">'
            f"{escape(token)}</span>"
        )
    body = (
        f'<div id="{viz_id}" class="safelens-interactive-tokens">'
        f'<div class="safelens-controls">{buttons}</div>'
        '<div class="safelens-token-strip">'
        f"{''.join(token_spans)}</div>"
        '<div class="safelens-focus-readout" data-role="readout"></div>'
        f"{_json_script(viz_id, {'labels': label_list, 'values': columns, 'colors': colors})}"
        f"{_tokens_multi_script(viz_id)}</div>"
    )
    html = _wrap_panel("tokens-multi", title, body)
    return Visualization(
        html=html,
        title=title,
        data={"tokens": token_list, "values": matrix, "labels": label_list},
    )


def plot_attention_pattern(
    pattern: Any,
    *,
    tokens: Sequence[Any] | None = None,
    layer: int | None = None,
    head: int | None = None,
    batch_index: int = 0,
    title: str | None = None,
) -> Visualization:
    """Render an attention pattern heatmap.

    Accepts `[query, key]`, `[head, query, key]`, or `[batch, head, query, key]`
    shaped inputs. If a head dimension is present, `head` selects the displayed
    head and defaults to zero.
    """

    matrix = _select_attention_matrix(pattern, batch_index=batch_index, head=head)
    label_tokens = [str(token) for token in tokens] if tokens is not None else None
    if label_tokens is not None and (
        len(label_tokens) != len(matrix) or len(label_tokens) != len(matrix[0])
    ):
        raise ValueError("tokens length must match the query/key dimensions.")
    resolved_title = title or _component_title("Attention Pattern", layer=layer, head=head)
    if len(matrix) == len(matrix[0]):
        labels = label_tokens or [str(idx) for idx in range(len(matrix))]
        viz = _attention_patterns_widget(
            [matrix],
            ["Head 0" if head is None else f"Head {head}"],
            labels,
            title=resolved_title,
            kind="attention-pattern",
            include_overview=False,
        )
        viz.data.update({"matrix": matrix, "x_labels": labels, "y_labels": labels})
        return viz
    return _heatmap(
        matrix,
        title=resolved_title,
        x_labels=label_tokens,
        y_labels=label_tokens,
        x_axis="Key",
        y_axis="Query",
        color="blue",
    )


def plot_attention_heads(
    attention: Any,
    *,
    tokens: Sequence[Any] | None = None,
    head_names: Sequence[str] | None = None,
    batch_index: int = 0,
    title: str | None = "Attention Heads",
) -> Visualization:
    """Render a set of attention heads as stacked heatmaps.

    Accepts `[head, query, key]` or `[batch, head, query, key]` shaped inputs.
    """

    data = _to_nested(attention)
    shape = _shape(data)
    if len(shape) == 2:
        heads = [_as_2d_numbers(data)]
    elif len(shape) == 3:
        heads = [_as_2d_numbers(head) for head in data]
    elif len(shape) == 4:
        if batch_index < 0 or batch_index >= shape[0]:
            raise ValueError("batch_index is outside the attention batch dimension.")
        heads = [_as_2d_numbers(head) for head in data[batch_index]]
    else:
        raise ValueError("attention heads must have rank 2, 3, or 4.")

    names = (
        [str(name) for name in head_names]
        if head_names is not None
        else [f"head {idx}" for idx in range(len(heads))]
    )
    if len(names) != len(heads):
        raise ValueError("head_names length must match the number of heads.")
    token_labels = [str(token) for token in tokens] if tokens is not None else None

    for matrix in heads:
        if token_labels is not None and (
            len(token_labels) != len(matrix) or len(token_labels) != len(matrix[0])
        ):
            raise ValueError("tokens length must match each attention head matrix.")
    first = heads[0]
    if len(first) == len(first[0]) and all(len(matrix) == len(matrix[0]) for matrix in heads):
        labels = token_labels or [str(idx) for idx in range(len(first))]
        return _attention_patterns_widget(
            heads,
            names,
            labels,
            title=title,
            kind="attention-heads",
            include_overview=len(heads) > 1,
        )
    x_labels = token_labels or [str(idx) for idx in range(len(first[0]))]
    y_labels = token_labels or [str(idx) for idx in range(len(first))]
    return _matrix_browser(
        heads,
        names,
        x_labels=x_labels,
        y_labels=y_labels,
        title=title,
        kind="attention-heads",
        selector_label="head",
        color="blue",
        allow_transpose=False,
        x_axis="Key",
        y_axis="Query",
    )


def plot_attention_patterns(
    attention: Any,
    *,
    tokens: Sequence[Any] | None = None,
    head_names: Sequence[str] | None = None,
    batch_index: int = 0,
    title: str | None = "Attention Patterns",
) -> Visualization:
    """Render attention head patterns using the legacy CircuitsVis naming."""

    return plot_attention_heads(
        attention,
        tokens=tokens,
        head_names=head_names,
        batch_index=batch_index,
        title=title,
    )


def plot_attention_browser(
    attention: Any,
    *,
    tokens: Sequence[Any] | None = None,
    batch_labels: Sequence[Any] | None = None,
    layer_labels: Sequence[Any] | None = None,
    head_labels: Sequence[Any] | None = None,
    rank4_axis: str = "layer",
    title: str | None = "Attention Browser",
) -> Visualization:
    """Interactively browse attention matrices across batches, layers, and heads.

    Accepts `[query, key]`, `[head, query, key]`, `[layer, head, query, key]`,
    `[batch, head, query, key]` when `rank4_axis="batch"`, or
    `[batch, layer, head, query, key]`.
    """

    matrices, labels, shape = _attention_browser_matrices(
        attention,
        batch_labels=batch_labels,
        layer_labels=layer_labels,
        head_labels=head_labels,
        rank4_axis=rank4_axis,
    )
    first = matrices[0]
    height = len(first)
    width = len(first[0]) if height else 0
    token_labels = [str(token) for token in tokens] if tokens is not None else None
    if token_labels is not None and (len(token_labels) != height or len(token_labels) != width):
        raise ValueError("tokens length must match the query/key dimensions.")
    x_labels = token_labels or [str(idx) for idx in range(width)]
    y_labels = token_labels or [str(idx) for idx in range(height)]
    viz = _matrix_browser(
        matrices,
        labels,
        x_labels=x_labels,
        y_labels=y_labels,
        title=title,
        kind="attention-browser",
        selector_label="matrix",
        color="blue",
        allow_transpose=True,
        x_axis="Key",
        y_axis="Query",
    )
    viz.data.update({"shape": shape, "tokens": token_labels})
    return viz


def plot_activation_patching_grid(
    values: Any,
    *,
    layers: Sequence[Any] | None = None,
    positions: Sequence[Any] | None = None,
    title: str | None = "Activation Patching",
) -> Visualization:
    """Render a layer-by-position activation patching score grid."""

    matrix = _as_2d_numbers(values)
    y_labels = [str(layer) for layer in layers] if layers is not None else None
    x_labels = [str(pos) for pos in positions] if positions is not None else None
    if y_labels is not None and len(y_labels) != len(matrix):
        raise ValueError("layers length must match the number of rows.")
    if x_labels is not None and matrix and len(x_labels) != len(matrix[0]):
        raise ValueError("positions length must match the number of columns.")
    return _heatmap(
        matrix,
        title=title,
        x_labels=x_labels,
        y_labels=y_labels,
        x_axis="Position",
        y_axis="Layer",
        color="red_blue",
    )


def plot_activation_patching_browser(
    values: Any,
    *,
    layers: Sequence[Any] | None = None,
    positions: Sequence[Any] | None = None,
    slice_labels: Sequence[Any] | None = None,
    slice_axis_name: str = "slice",
    title: str | None = "Activation Patching Browser",
) -> Visualization:
    """Interactively browse activation patching score grids.

    Accepts `[layer, position]` or `[slice, layer, position]` values.
    """

    data = _to_nested(values)
    shape = _shape(data)
    if len(shape) == 2:
        matrices = [_as_2d_numbers(data)]
        labels = ["scores"]
    elif len(shape) == 3:
        matrices = [_as_2d_numbers(item) for item in data]
        labels = _labels_or_indices(slice_labels, len(matrices), slice_axis_name)
    else:
        raise ValueError("values must have shape [layer, position] or [slice, layer, position].")
    y_labels = [str(layer) for layer in layers] if layers is not None else None
    x_labels = [str(pos) for pos in positions] if positions is not None else None
    if y_labels is not None and len(y_labels) != len(matrices[0]):
        raise ValueError("layers length must match the number of rows.")
    if x_labels is not None and matrices[0] and len(x_labels) != len(matrices[0][0]):
        raise ValueError("positions length must match the number of columns.")
    resolved_y = y_labels or [str(idx) for idx in range(len(matrices[0]))]
    resolved_x = x_labels or [str(idx) for idx in range(len(matrices[0][0]))]
    viz = _matrix_browser(
        matrices,
        labels,
        x_labels=resolved_x,
        y_labels=resolved_y,
        title=title,
        kind="activation-patching-browser",
        selector_label=slice_axis_name,
        color="red_blue",
        allow_transpose=False,
        x_axis="Position",
        y_axis="Layer",
    )
    viz.data.update({"shape": shape, "slice_axis_name": slice_axis_name})
    return viz


def plot_line(
    values: Any,
    *,
    x: Sequence[Any] | None = None,
    series_labels: Sequence[str] | None = None,
    title: str | None = "Line Plot",
    x_axis: str = "Index",
    y_axis: str = "Value",
) -> Visualization:
    """Render one or more numeric series as an HTML table plus inline bars."""

    matrix = _as_2d_numbers(values)
    if len(matrix) == 1:
        series = matrix
    else:
        series = matrix
    width = len(series[0])
    if any(len(row) != width for row in series):
        raise ValueError("all line series must have the same length.")
    x_labels = [str(value) for value in x] if x is not None else [str(i) for i in range(width)]
    if len(x_labels) != width:
        raise ValueError("x length must match the series length.")
    labels = (
        [str(label) for label in series_labels]
        if series_labels is not None
        else [f"series {idx}" for idx in range(len(series))]
    )
    if len(labels) != len(series):
        raise ValueError("series_labels length must match the number of series.")

    values_flat = [value for row in series for value in row]
    min_value, max_value = _value_range(values_flat)
    rows = []
    for label, row in zip(labels, series, strict=True):
        cells = [f"<th>{escape(label)}</th>"]
        for value in row:
            pct = _normalized_percent(value, min_value, max_value)
            cells.append(
                "<td>"
                f'<div class="safelens-bar" style="width:{pct:.2f}%"></div>'
                f"<span>{value:.4g}</span></td>"
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")
    header = "<tr><th></th>" + "".join(f"<th>{escape(label)}</th>" for label in x_labels) + "</tr>"
    body = (
        f'<div class="safelens-axis">{escape(y_axis)} by {escape(x_axis)}</div>'
        f'<table class="safelens-line-table">{header}{"".join(rows)}</table>'
        + _legend(min_value, max_value)
    )
    return Visualization(
        html=_wrap_panel("line", title, body),
        title=title,
        data={
            "series": series,
            "x": x_labels,
            "series_labels": labels,
            "x_axis": x_axis,
            "y_axis": y_axis,
        },
    )


def plot_scatter(
    x: Sequence[Any],
    y: Sequence[Any],
    *,
    labels: Sequence[Any] | None = None,
    title: str | None = "Scatter Plot",
    x_axis: str = "x",
    y_axis: str = "y",
) -> Visualization:
    """Render scatter data as a coordinate table."""

    x_values = [_scalar(value) for value in x]
    y_values = [_scalar(value) for value in y]
    if len(x_values) != len(y_values):
        raise ValueError("x and y must have the same length.")
    label_values = (
        [str(label) for label in labels]
        if labels is not None
        else [str(idx) for idx in range(len(x_values))]
    )
    if len(label_values) != len(x_values):
        raise ValueError("labels length must match x and y.")
    rows = [
        [label, x_value, y_value]
        for label, x_value, y_value in zip(label_values, x_values, y_values, strict=True)
    ]
    return Visualization(
        html=_wrap_panel(
            "scatter",
            title,
            _html_table(["label", x_axis, y_axis], rows),
        ),
        title=title,
        data={"x": x_values, "y": y_values, "labels": label_values},
    )


def plot_bar(
    values: Mapping[Any, Any] | Sequence[Any],
    *,
    labels: Sequence[Any] | None = None,
    top_k: int | None = None,
    sort: bool = True,
    title: str | None = "Bar Chart",
) -> Visualization:
    """Render scalar values as a searchable, sortable bar table."""

    if isinstance(values, Mapping):
        names = [str(key) for key in values.keys()]
        scalar_values = [_scalar(value) for value in values.values()]
    else:
        scalar_values = [_scalar(value) for value in values]
        names = (
            [str(label) for label in labels]
            if labels is not None
            else [str(idx) for idx in range(len(scalar_values))]
        )
    if len(names) != len(scalar_values):
        raise ValueError("labels length must match the number of values.")
    rows = list(zip(names, scalar_values, strict=True))
    if sort:
        rows.sort(key=lambda item: item[1], reverse=True)
    if top_k is not None:
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        rows = rows[:top_k]
    min_value, max_value = _value_range([value for _, value in rows] or [0.0])
    viz_id = _next_viz_id("bar")
    body = _bar_table(viz_id, rows, min_value=min_value, max_value=max_value, include_filter=True)
    return Visualization(
        html=_wrap_panel("bar", title, body),
        title=title,
        data={
            "labels": [label for label, _ in rows],
            "values": [value for _, value in rows],
            "top_k": top_k,
            "sorted": sort,
        },
    )


def plot_histogram(
    values: Any,
    *,
    bins: int = 20,
    title: str | None = "Histogram",
) -> Visualization:
    """Render a numeric distribution as a binned bar table."""

    if bins < 1:
        raise ValueError("bins must be at least 1.")
    flat_values = [_scalar(value) for value in _flatten_nested(_to_nested(values))]
    if not flat_values:
        raise ValueError("values must contain at least one numeric item.")
    min_value, max_value = _value_range(flat_values)
    if math.isclose(min_value, max_value):
        counts = [len(flat_values)]
        labels = [f"{min_value:.6g}"]
    else:
        width = (max_value - min_value) / bins
        counts = [0 for _ in range(bins)]
        for value in flat_values:
            index = min(bins - 1, int((value - min_value) / width))
            counts[index] += 1
        labels = [
            f"{min_value + idx * width:.6g} to {min_value + (idx + 1) * width:.6g}"
            for idx in range(bins)
        ]
    rows = list(zip(labels, [float(count) for count in counts], strict=True))
    viz_id = _next_viz_id("histogram")
    body = _bar_table(
        viz_id,
        rows,
        min_value=0.0,
        max_value=float(max(counts) if counts else 0),
        include_filter=False,
        value_header="count",
    )
    return Visualization(
        html=_wrap_panel("histogram", title, body),
        title=title,
        data={
            "bins": labels,
            "counts": counts,
            "min": min_value,
            "max": max_value,
            "num_values": len(flat_values),
        },
    )


def plot_head_scores(
    scores: Any,
    *,
    layers: Sequence[Any] | None = None,
    heads: Sequence[Any] | None = None,
    title: str | None = "Head Scores",
) -> Visualization:
    """Render a layer-by-head score heatmap."""

    matrix = _as_2d_numbers(scores)
    y_labels = [str(layer) for layer in layers] if layers is not None else None
    x_labels = [str(head) for head in heads] if heads is not None else None
    if y_labels is not None and len(y_labels) != len(matrix):
        raise ValueError("layers length must match the number of rows.")
    if x_labels is not None and matrix and len(x_labels) != len(matrix[0]):
        raise ValueError("heads length must match the number of columns.")
    return _heatmap(
        matrix,
        title=title,
        x_labels=x_labels,
        y_labels=y_labels,
        x_axis="Head",
        y_axis="Layer",
        color="red_blue",
    )


def plot_token_log_probs(
    token_indices: Any,
    log_probs: Any,
    to_string: Any,
    *,
    top_k: int = 10,
    title: str | None = "Token Log Probabilities",
) -> Visualization:
    """Render next-token log probabilities and top-k predictions.

    This mirrors CircuitsVis' `logits.token_log_probs` component in a static
    form. `token_indices` may include a batch dimension of size one.
    """

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")
    token_list = _flatten_rank_one(token_indices)
    log_prob_rows = _maybe_remove_single_batch(log_probs)
    matrix = _as_2d_numbers(log_prob_rows)
    if len(matrix) != len(token_list):
        raise ValueError("log_probs must contain one row per token position.")
    if len(token_list) < 2:
        raise ValueError("at least two tokens are required for next-token log probabilities.")

    prompt = [str(to_string(int(token))) for token in token_list]
    correct_values = []
    detail_rows = []
    for pos, row in enumerate(matrix[:-1]):
        target = int(token_list[pos + 1])
        if target < 0 or target >= len(row):
            raise ValueError(f"target token id {target} is outside the log-prob vocabulary.")
        ranked = sorted(enumerate(row), key=lambda item: item[1], reverse=True)
        rank_lookup = {token_id: rank for rank, (token_id, _value) in enumerate(ranked, start=1)}
        top_predictions = [
            f"{to_string(token_id)} ({value:.4g})" for token_id, value in ranked[:top_k]
        ]
        correct_log_prob = row[target]
        correct_values.append(correct_log_prob)
        detail_rows.append(
            [
                pos,
                prompt[pos + 1],
                correct_log_prob,
                rank_lookup[target],
                "; ".join(map(str, top_predictions)),
            ]
        )

    token_viz = colored_tokens(prompt[1:], correct_values, title=None)
    viz_id = _next_viz_id("token-log-probs")
    body = token_viz.html + (
        f'<div id="{viz_id}" class="safelens-token-log-prob-table">'
        + _interactive_table(
            viz_id,
            ["position", "target", "correct_log_prob", "rank", f"top_{top_k}"],
            detail_rows,
            include_filter=True,
        )
        + "</div>"
    )
    return Visualization(
        html=_wrap_panel("token-log-probs", title, body),
        title=title,
        data={
            "prompt": prompt,
            "correct_log_probs": correct_values,
            "details": detail_rows,
            "top_k": top_k,
        },
    )


def plot_model_performance(
    token_indices: Any,
    str_tokens: Sequence[Any],
    logits: Any,
    *,
    title: str | None = "Model Performance",
) -> Visualization:
    """Render correct-token logits, log-probs, and probabilities.

    This is the dependency-light equivalent of CircuitsVis'
    `tokens.visualize_model_performance` helper.
    """

    token_list = [int(token) for token in _flatten_rank_one(token_indices)]
    string_tokens = [str(token) for token in str_tokens]
    logit_rows = _maybe_remove_single_batch(logits)
    matrix = _as_2d_numbers(logit_rows)
    if len(token_list) != len(string_tokens):
        raise ValueError("token_indices and str_tokens must have the same length.")
    if len(matrix) != len(token_list):
        raise ValueError("logits must contain one row per token.")
    if len(token_list) < 2:
        raise ValueError("at least two tokens are required to visualize model performance.")

    values = []
    rows = []
    for pos, row in enumerate(matrix[:-1]):
        target = token_list[pos + 1]
        if target < 0 or target >= len(row):
            raise ValueError(f"target token id {target} is outside the logit vocabulary.")
        log_probs = _log_softmax(row)
        probs = [math.exp(value) for value in log_probs]
        value_row = [row[target], log_probs[target], probs[target]]
        values.append(value_row)
        rows.append([pos, string_tokens[pos + 1], *value_row])

    labels = ["logits", "log_probs", "probs"]
    token_viz = colored_tokens_multi(string_tokens[1:], values, labels=labels, title=None)
    body = token_viz.html + _html_table(
        ["position", "target", *labels],
        rows,
    )
    return Visualization(
        html=_wrap_panel("model-performance", title, body),
        title=title,
        data={"tokens": string_tokens, "values": values, "labels": labels, "rows": rows},
    )


def plot_next_token_browser(
    token_indices: Any,
    logits: Any,
    to_string: Any | None = None,
    *,
    top_k: int = 10,
    title: str | None = "Next Token Browser",
) -> Visualization:
    """Interactively inspect next-token predictions at each prompt position."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")
    token_list = [int(token) for token in _flatten_rank_one(token_indices)]
    matrix = _as_2d_numbers(_maybe_remove_single_batch(logits))
    if len(matrix) != len(token_list):
        raise ValueError("logits must contain one row per token position.")
    if len(token_list) < 2:
        raise ValueError("at least two tokens are required for next-token browsing.")
    stringify = to_string or (lambda idx: str(idx))
    prompt = [str(stringify(token)) for token in token_list]
    positions = []
    for pos, row in enumerate(matrix[:-1]):
        target = token_list[pos + 1]
        if target < 0 or target >= len(row):
            raise ValueError(f"target token id {target} is outside the vocabulary.")
        log_probs = _log_softmax(row)
        ranked = sorted(enumerate(row), key=lambda item: item[1], reverse=True)
        rank_lookup = {token_id: rank for rank, (token_id, _value) in enumerate(ranked, start=1)}
        predictions = []
        for rank, (token_id, logit_value) in enumerate(ranked[:top_k], start=1):
            log_prob = log_probs[token_id]
            predictions.append(
                {
                    "rank": rank,
                    "token_id": token_id,
                    "token": str(stringify(token_id)),
                    "logit": logit_value,
                    "log_prob": log_prob,
                    "prob": math.exp(log_prob),
                    "is_target": token_id == target,
                }
            )
        target_log_prob = log_probs[target]
        positions.append(
            {
                "position": pos,
                "context_token": prompt[pos],
                "target_token": prompt[pos + 1],
                "target_token_id": target,
                "target_rank": rank_lookup[target],
                "target_logit": row[target],
                "target_log_prob": target_log_prob,
                "target_prob": math.exp(target_log_prob),
                "predictions": predictions,
            }
        )

    viz_id = _next_viz_id("next-token-browser")
    position_labels = [f"{item['position']} -> {item['target_token']}" for item in positions]
    controls = (
        '<div class="safelens-controls">'
        f"{_select_control(viz_id, 'position', position_labels)}"
        '<label class="safelens-control-label">metric '
        '<select class="safelens-select" data-filter="metric">'
        '<option value="logit">logit</option>'
        '<option value="log_prob">log_prob</option>'
        '<option value="prob">prob</option>'
        "</select></label></div>"
    )
    body = (
        f'<div id="{viz_id}" class="safelens-next-token-browser">'
        f'{controls}<div class="safelens-focus-readout" data-role="readout"></div>'
        '<table class="safelens-summary safelens-interactive-table" data-role="predictions">'
        '<thead><tr><th>rank</th><th>token</th><th>token_id</th><th data-role="metric-head">'
        "logit</th><th>target</th></tr></thead><tbody></tbody></table>"
        f"{_json_script(viz_id, {'prompt': prompt, 'positions': positions})}"
        f"{_next_token_browser_script(viz_id)}</div>"
    )
    return Visualization(
        html=_wrap_panel("next-token-browser", title, body),
        title=title,
        data={"prompt": prompt, "positions": positions, "top_k": top_k},
    )


def plot_neuron_activations(
    activations: Any,
    *,
    tokens: Sequence[Any] | None = None,
    neurons: Sequence[Any] | None = None,
    title: str | None = "Neuron Activations",
) -> Visualization:
    """Render neuron activations across tokens.

    Accepts either `[pos]` or `[pos, neuron]`; one-dimensional data is displayed
    as a single neuron column.
    """

    matrix = _as_2d_numbers(activations)
    if matrix and len(matrix) == 1 and tokens is not None and len(tokens) == len(matrix[0]):
        matrix = [[value] for value in matrix[0]]
    y_labels = [str(token) for token in tokens] if tokens is not None else None
    x_labels = [str(neuron) for neuron in neurons] if neurons is not None else None
    if y_labels is not None and len(y_labels) != len(matrix):
        raise ValueError("tokens length must match the number of activation rows.")
    if x_labels is not None and matrix and len(x_labels) != len(matrix[0]):
        raise ValueError("neurons length must match the number of activation columns.")
    return _heatmap(
        matrix,
        title=title,
        x_labels=x_labels,
        y_labels=y_labels,
        x_axis="Neuron",
        y_axis="Token",
        color="red_blue",
    )


def plot_text_neuron_activations(
    tokens: Sequence[Any],
    activations: Any,
    *,
    layer: int = 0,
    neuron: int = 0,
    title: str | None = "Text Neuron Activations",
) -> Visualization:
    """Render one layer/neuron slice from token-layer-neuron activations."""

    token_samples = _token_samples(tokens)
    data = _to_nested(activations)
    shape = _shape(data)
    if len(shape) == 3:
        activation_samples = [data]
    elif len(shape) == 4:
        activation_samples = data
    else:
        raise ValueError(
            "activations must have shape [token, layer, neuron] or [sample, token, layer, neuron]."
        )
    if len(token_samples) != len(activation_samples):
        raise ValueError("tokens and activations must contain the same number of samples.")

    sections = []
    values_by_sample = []
    for sample_idx, (token_list, sample_acts) in enumerate(
        zip(token_samples, activation_samples, strict=True)
    ):
        sample_shape = _shape(sample_acts)
        if len(sample_shape) != 3:
            raise ValueError("each activation sample must have shape [token, layer, neuron].")
        if len(token_list) != sample_shape[0]:
            raise ValueError("tokens length must match each activation sample's token dimension.")
        if layer < 0 or layer >= sample_shape[1]:
            raise ValueError("layer is outside the activation layer dimension.")
        if neuron < 0 or neuron >= sample_shape[2]:
            raise ValueError("neuron is outside the activation neuron dimension.")
        values = [
            _scalar(sample_acts[token_idx][layer][neuron]) for token_idx in range(sample_shape[0])
        ]
        sample_title = None if len(activation_samples) == 1 else f"sample {sample_idx}"
        sections.append(colored_tokens(token_list, values, title=sample_title).html)
        values_by_sample.append(values)

    resolved_title = f"{title} - layer {layer}, neuron {neuron}" if title else None
    return Visualization(
        html=_wrap_panel("text-neuron-activations", resolved_title, "".join(sections)),
        title=resolved_title,
        data={
            "tokens": token_samples,
            "values": values_by_sample,
            "layer": layer,
            "neuron": neuron,
        },
    )


def plot_text_neuron_browser(
    tokens: Sequence[Any],
    activations: Any,
    *,
    sample_labels: Sequence[Any] | None = None,
    layer_labels: Sequence[Any] | None = None,
    neuron_labels: Sequence[Any] | None = None,
    title: str | None = "Text Neuron Browser",
) -> Visualization:
    """Interactively browse token activations by sample, layer, and neuron."""

    token_samples, activation_samples, shape = _normalize_text_neuron_inputs(
        tokens,
        activations,
    )
    sample_names = _labels_or_indices(sample_labels, len(activation_samples), "sample")
    layer_names = _labels_or_indices(layer_labels, shape[1], "layer")
    neuron_names = _labels_or_indices(neuron_labels, shape[2], "neuron")
    all_values = [
        _scalar(value)
        for sample in activation_samples
        for token_values in sample
        for layer_values in token_values
        for value in layer_values
    ]
    min_value, max_value = _value_range(all_values)
    viz_id = _next_viz_id("text-neuron-browser")
    payload = {
        "tokens": token_samples,
        "activations": activation_samples,
        "sampleLabels": sample_names,
        "layerLabels": layer_names,
        "neuronLabels": neuron_names,
        "min": min_value,
        "max": max_value,
    }
    controls = (
        '<div class="safelens-controls">'
        f"{_select_control(viz_id, 'sample', sample_names)}"
        f"{_select_control(viz_id, 'layer', layer_names)}"
        f"{_select_control(viz_id, 'neuron', neuron_names)}"
        "</div>"
    )
    body = (
        f'<div id="{viz_id}" class="safelens-text-neuron-browser">'
        f'{controls}<div class="safelens-token-strip" data-role="tokens"></div>'
        '<div class="safelens-focus-readout" data-role="readout"></div>'
        f"{_json_script(viz_id, payload)}"
        f"{_text_neuron_browser_script(viz_id)}</div>"
    )
    return Visualization(
        html=_wrap_panel("text-neuron-browser", title, body),
        title=title,
        data={
            "tokens": token_samples,
            "shape": shape,
            "sample_labels": sample_names,
            "layer_labels": layer_names,
            "neuron_labels": neuron_names,
        },
    )


def plot_topk_tokens(
    tokens: Sequence[Any],
    activations: Any,
    *,
    max_k: int = 10,
    sample_labels: Sequence[Any] | None = None,
    layer_labels: Sequence[Any] | None = None,
    neuron_labels: Sequence[Any] | None = None,
    title: str | None = "Top-K Tokens",
) -> Visualization:
    """Render top and bottom token activations.

    Accepts `[layer, token, neuron]` for one sample or
    `[sample, layer, token, neuron]` for multiple samples.
    """

    rows, metadata = _topk_token_rows(
        tokens,
        activations,
        max_k=max_k,
        sample_labels=sample_labels,
        layer_labels=layer_labels,
        neuron_labels=neuron_labels,
    )
    return Visualization(
        html=_wrap_panel(
            "topk-tokens",
            title,
            _html_table(["sample", "layer", "neuron", "top", "bottom"], rows),
        ),
        title=title,
        data={
            "tokens": metadata["tokens"],
            "sample_labels": metadata["sample_labels"],
            "layer_labels": metadata["layer_labels"],
            "neuron_labels": metadata["neuron_labels"],
            "rows": rows,
            "max_k": max_k,
        },
    )


def plot_topk_tokens_browser(
    tokens: Sequence[Any],
    activations: Any,
    *,
    max_k: int = 10,
    sample_labels: Sequence[Any] | None = None,
    layer_labels: Sequence[Any] | None = None,
    neuron_labels: Sequence[Any] | None = None,
    title: str | None = "Top-K Token Browser",
) -> Visualization:
    """Interactively filter top and bottom token activations."""

    rows, metadata = _topk_token_rows(
        tokens,
        activations,
        max_k=max_k,
        sample_labels=sample_labels,
        layer_labels=layer_labels,
        neuron_labels=neuron_labels,
    )
    viz_id = _next_viz_id("topk-token-browser")
    body = (
        f'<div id="{viz_id}" class="safelens-topk-browser">'
        '<div class="safelens-controls">'
        f"{_select_control(viz_id, 'sample', metadata['sample_labels'], include_all=True)}"
        f"{_select_control(viz_id, 'layer', metadata['layer_labels'], include_all=True)}"
        '<select class="safelens-select" data-filter="kind">'
        '<option value="both">top and bottom</option>'
        '<option value="top">top only</option>'
        '<option value="bottom">bottom only</option>'
        "</select>"
        '<input class="safelens-input" data-filter="query" placeholder="filter" />'
        "</div>"
        f"{_interactive_table(viz_id, ['sample', 'layer', 'neuron', 'top', 'bottom'], rows)}"
        f"{_topk_token_browser_script(viz_id)}</div>"
    )
    return Visualization(
        html=_wrap_panel("topk-token-browser", title, body),
        title=title,
        data={**metadata, "rows": rows, "max_k": max_k},
    )


def plot_logit_lens(
    logits_or_scores: Any,
    *,
    layers: Sequence[Any] | None = None,
    tokens: Sequence[Any] | None = None,
    title: str | None = "Logit Lens",
) -> Visualization:
    """Render logit-lens scores as a layer-by-token heatmap."""

    matrix = _as_2d_numbers(logits_or_scores)
    y_labels = [str(layer) for layer in layers] if layers is not None else None
    x_labels = [str(token) for token in tokens] if tokens is not None else None
    if y_labels is not None and len(y_labels) != len(matrix):
        raise ValueError("layers length must match the number of rows.")
    if x_labels is not None and matrix and len(x_labels) != len(matrix[0]):
        raise ValueError("tokens length must match the number of columns.")
    return _heatmap(
        matrix,
        title=title,
        x_labels=x_labels,
        y_labels=y_labels,
        x_axis="Token",
        y_axis="Layer",
        color="red_blue",
    )


def plot_component_scores(
    scores: Mapping[Any, Any] | Any,
    *,
    component_names: Sequence[Any] | None = None,
    value_names: Sequence[Any] | None = None,
    title: str | None = "Component Scores",
) -> Visualization:
    """Render a component-by-value score heatmap."""

    if isinstance(scores, Mapping):
        raw_values = [_to_nested(value) for value in scores.values()]
        if raw_values and all(_shape(value) == () for value in raw_values):
            matrix = [[_scalar(value)] for value in raw_values]
        else:
            matrix = _as_2d_numbers(raw_values)
        component_labels = (
            [str(name) for name in component_names]
            if component_names is not None
            else [str(key) for key in scores.keys()]
        )
    else:
        matrix = _as_2d_numbers(scores)
        component_labels = (
            [str(name) for name in component_names]
            if component_names is not None
            else [str(idx) for idx in range(len(matrix))]
        )
    if component_names is not None and len(component_names) != len(matrix):
        raise ValueError("component_names length must match the number of rows.")
    value_labels = [str(name) for name in value_names] if value_names is not None else None
    if value_labels is not None and matrix and len(value_labels) != len(matrix[0]):
        raise ValueError("value_names length must match the number of columns.")
    return _heatmap(
        matrix,
        title=title,
        x_labels=value_labels,
        y_labels=component_labels,
        x_axis="Value",
        y_axis="Component",
        color="red_blue",
    )


def plot_cache_summary(
    cache: Mapping[Any, Any],
    *,
    title: str | None = "Activation Cache Summary",
) -> Visualization:
    """Render a searchable summary of cached activations."""

    rows = []
    for key, value in cache.items():
        rows.append(
            [
                str(key),
                _display_shape(value),
                str(getattr(value, "dtype", "")),
                str(getattr(value, "device", "")),
                type(value).__name__,
            ]
        )
    viz_id = _next_viz_id("cache-summary")
    table = _interactive_table(
        viz_id,
        ["name", "shape", "dtype", "device", "type"],
        rows,
        include_filter=True,
    )
    body = f'<div id="{viz_id}" class="safelens-cache-summary">{table}</div>'
    return Visualization(
        html=_wrap_panel("cache-summary", title, body),
        title=title,
        data={"rows": rows},
    )


def plot_activation_cache_browser(
    cache: Mapping[Any, Any],
    *,
    keys: Sequence[Any] | None = None,
    batch_index: int = 0,
    max_rows: int | None = None,
    max_columns: int | None = 64,
    x_labels: Sequence[Any] | None = None,
    y_labels: Sequence[Any] | None = None,
    x_axis: str = "Feature",
    y_axis: str = "Token",
    title: str | None = "Activation Cache Browser",
) -> Visualization:
    """Interactively browse same-shaped rank-2 or batched rank-3 cache entries."""

    selected_keys = list(keys) if keys is not None else list(cache)
    matrices = []
    matrix_labels = []
    skipped: list[dict[str, Any]] = []
    target_shape: tuple[int, int] | None = None
    for key in selected_keys:
        key_label = str(key)
        try:
            value = cache[key]
        except (KeyError, TypeError, IndexError):
            if key_label not in cache:
                skipped.append({"key": key_label, "reason": "missing"})
                continue
            value = cache[key_label]
        data = _to_nested(value)
        shape = _shape(data)
        if len(shape) == 3:
            if batch_index < 0 or batch_index >= shape[0]:
                skipped.append(
                    {"key": key_label, "shape": shape, "reason": "batch_index out of range"}
                )
                continue
            matrix_data = data[batch_index]
        elif len(shape) == 2:
            matrix_data = data
        else:
            skipped.append({"key": key_label, "shape": shape, "reason": "rank is not 2 or 3"})
            continue
        matrix = _as_2d_numbers(matrix_data)
        if max_rows is not None:
            if max_rows < 1:
                raise ValueError("max_rows must be at least 1 when provided.")
            matrix = matrix[:max_rows]
        if max_columns is not None:
            if max_columns < 1:
                raise ValueError("max_columns must be at least 1 when provided.")
            matrix = [row[:max_columns] for row in matrix]
        current_shape = (len(matrix), len(matrix[0]) if matrix else 0)
        if target_shape is None:
            target_shape = current_shape
        if current_shape != target_shape:
            skipped.append({"key": key_label, "shape": shape, "reason": "matrix shape differs"})
            continue
        matrices.append(matrix)
        matrix_labels.append(key_label)
    if not matrices or target_shape is None:
        raise ValueError("cache did not contain any compatible rank-2 or rank-3 matrices.")
    resolved_y = (
        [str(label) for label in y_labels]
        if y_labels is not None
        else [str(idx) for idx in range(target_shape[0])]
    )
    resolved_x = (
        [str(label) for label in x_labels]
        if x_labels is not None
        else [str(idx) for idx in range(target_shape[1])]
    )
    if len(resolved_y) != target_shape[0]:
        raise ValueError("y_labels length must match the displayed matrix rows.")
    if len(resolved_x) != target_shape[1]:
        raise ValueError("x_labels length must match the displayed matrix columns.")
    viz = _matrix_browser(
        matrices,
        matrix_labels,
        x_labels=resolved_x,
        y_labels=resolved_y,
        title=title,
        kind="activation-cache-browser",
        selector_label="activation",
        color="red_blue",
        allow_transpose=True,
        x_axis=x_axis,
        y_axis=y_axis,
    )
    viz.data.update(
        {
            "keys": matrix_labels,
            "skipped": skipped,
            "batch_index": batch_index,
            "max_rows": max_rows,
            "max_columns": max_columns,
        }
    )
    return viz


def render_safety_report(report: SafetyReport | Mapping[str, Any]) -> Visualization:
    """Render one `SafetyReport` as a compact HTML panel."""

    payload = report.to_dict() if isinstance(report, SafetyReport) else dict(report)
    rows = [
        ("sample_id", payload.get("sample_id")),
        ("flagged", payload.get("flagged")),
        ("risk_score", payload.get("risk_score")),
        ("risk_category", ", ".join(map(str, payload.get("risk_category", [])))),
        ("evidence_tokens", payload.get("evidence_tokens", [])),
        ("attribution_score", payload.get("attribution_score")),
    ]
    body = _summary_table(rows)
    body += _details_block("Probe Results", payload.get("probe_results", []))
    body += _details_block("Monitoring Signals", payload.get("monitoring_signals", []))
    body += _details_block("Attributions", payload.get("attributions", []))
    return Visualization(
        html=_wrap_panel("report", "Safety Report", body),
        title="Safety Report",
        data=payload,
    )


def render_run_report(report: RunReport | Mapping[str, Any]) -> Visualization:
    """Render an aggregate `RunReport` with summary and per-sample rows."""

    payload = report.to_dict() if isinstance(report, RunReport) else dict(report)
    summary = payload.get("summary", {})
    reports = list(payload.get("reports", []))
    rows = [
        [
            item.get("sample_id", ""),
            item.get("flagged", False),
            item.get("risk_score", 0.0),
            ", ".join(map(str, item.get("risk_category", []))),
            item.get("evidence_tokens", []),
        ]
        for item in reports
    ]
    body = _summary_table((key, value) for key, value in summary.items())
    body += _html_table(
        ["sample_id", "flagged", "risk_score", "risk_category", "evidence_tokens"],
        rows,
    )
    return Visualization(
        html=_wrap_panel("run-report", "Run Report", body),
        title="Run Report",
        data=payload,
    )


def plot_topk_samples(
    tokens: Any,
    activations: Any,
    *,
    layer_labels: Sequence[Any] | None = None,
    neuron_labels: Sequence[Any] | None = None,
    title: str | None = "Top-K Samples",
) -> Visualization:
    """Render sample rankings for `[layer, neuron, sample, token]` activations."""

    rows, metadata = _topk_sample_rows(
        tokens,
        activations,
        layer_labels=layer_labels,
        neuron_labels=neuron_labels,
    )
    return Visualization(
        html=_wrap_panel(
            "topk-samples",
            title,
            _html_table(_TOPK_SAMPLE_HEADERS, rows),
        ),
        title=title,
        data={
            "rows": rows,
            "layer_labels": metadata["layer_labels"],
            "neuron_labels": metadata["neuron_labels"],
        },
    )


def plot_topk_samples_browser(
    tokens: Any,
    activations: Any,
    *,
    layer_labels: Sequence[Any] | None = None,
    neuron_labels: Sequence[Any] | None = None,
    title: str | None = "Top-K Sample Browser",
) -> Visualization:
    """Interactively filter sample rankings by layer and neuron."""

    rows, metadata = _topk_sample_rows(
        tokens,
        activations,
        layer_labels=layer_labels,
        neuron_labels=neuron_labels,
    )
    viz_id = _next_viz_id("topk-sample-browser")
    body = (
        f'<div id="{viz_id}" class="safelens-topk-browser">'
        '<div class="safelens-controls">'
        f"{_select_control(viz_id, 'layer', metadata['layer_labels'], include_all=True)}"
        f"{_select_control(viz_id, 'neuron', metadata['neuron_labels'], include_all=True)}"
        '<input class="safelens-input" data-filter="query" placeholder="filter" />'
        "</div>"
        f"{_interactive_table(viz_id, _TOPK_SAMPLE_HEADERS, rows)}"
        f"{_topk_sample_browser_script(viz_id)}</div>"
    )
    return Visualization(
        html=_wrap_panel("topk-sample-browser", title, body),
        title=title,
        data={**metadata, "rows": rows},
    )


def to_circuitsvis_colored_tokens(
    tokens: Sequence[Any],
    values: Sequence[Any],
    **kwargs: Any,
) -> Any:
    """Render colored tokens with CircuitsVis when it is installed.

    This intentionally keeps CircuitsVis optional. Callers who want the native
    CircuitsVis object can install `circuitsvis` and use this bridge.
    """

    try:
        from circuitsvis.tokens import colored_tokens as circuitsvis_colored_tokens
    except ImportError as exc:
        raise ImportError(
            "circuitsvis is not installed. Install SafeLens with the optional "
            "visualization dependencies or call SafeLens.viz.colored_tokens instead."
        ) from exc
    return circuitsvis_colored_tokens(list(tokens), list(values), **kwargs)


def to_circuitsvis_colored_tokens_multi(
    tokens: Sequence[Any],
    values: Any,
    *,
    labels: Sequence[str] | None = None,
    **kwargs: Any,
) -> Any:
    """Render multi-track colored tokens with CircuitsVis when installed."""

    try:
        from circuitsvis.tokens import colored_tokens_multi as circuitsvis_colored_tokens_multi
    except ImportError as exc:
        raise _circuitsvis_import_error("colored_tokens_multi") from exc
    return circuitsvis_colored_tokens_multi(
        list(tokens),
        values,
        labels=list(labels) if labels else None,
        **kwargs,
    )


def to_circuitsvis_attention_pattern(
    tokens: Sequence[Any],
    attention: Any,
    **kwargs: Any,
) -> Any:
    """Render one attention pattern with CircuitsVis when installed."""

    try:
        from circuitsvis.attention import attention_pattern as circuitsvis_attention_pattern
    except ImportError as exc:
        raise _circuitsvis_import_error("attention_pattern") from exc
    return circuitsvis_attention_pattern(list(map(str, tokens)), attention, **kwargs)


def to_circuitsvis_attention_heads(
    attention: Any,
    tokens: Sequence[Any],
    *,
    attention_head_names: Sequence[str] | None = None,
    **kwargs: Any,
) -> Any:
    """Render a set of attention heads with CircuitsVis when installed."""

    try:
        from circuitsvis.attention import attention_heads as circuitsvis_attention_heads
    except ImportError as exc:
        raise _circuitsvis_import_error("attention_heads") from exc
    return circuitsvis_attention_heads(
        attention,
        list(map(str, tokens)),
        attention_head_names=list(attention_head_names) if attention_head_names else None,
        **kwargs,
    )


def to_circuitsvis_attention_patterns(
    tokens: Sequence[Any],
    attention: Any,
    **kwargs: Any,
) -> Any:
    """Render attention patterns with CircuitsVis' legacy component when installed."""

    try:
        from circuitsvis.attention import attention_patterns as circuitsvis_attention_patterns
    except ImportError as exc:
        raise _circuitsvis_import_error("attention_patterns") from exc
    return circuitsvis_attention_patterns(list(map(str, tokens)), attention, **kwargs)


def to_circuitsvis_text_neuron_activations(
    tokens: Any,
    activations: Any,
    **kwargs: Any,
) -> Any:
    """Render text neuron activations with CircuitsVis when installed."""

    try:
        from circuitsvis.activations import (
            text_neuron_activations as circuitsvis_text_neuron_activations,
        )
    except ImportError as exc:
        raise _circuitsvis_import_error("text_neuron_activations") from exc
    return circuitsvis_text_neuron_activations(tokens, activations, **kwargs)


def to_circuitsvis_token_log_probs(
    token_indices: Any,
    log_probs: Any,
    to_string: Any,
    *,
    top_k: int = 10,
) -> Any:
    """Render token log-probability diagnostics with CircuitsVis when installed."""

    try:
        from circuitsvis.logits import token_log_probs as circuitsvis_token_log_probs
    except ImportError as exc:
        raise _circuitsvis_import_error("token_log_probs") from exc
    return circuitsvis_token_log_probs(token_indices, log_probs, to_string, top_k=top_k)


def to_circuitsvis_topk_tokens(
    tokens: Any,
    activations: Any,
    **kwargs: Any,
) -> Any:
    """Render top-k token activations with CircuitsVis when installed."""

    try:
        from circuitsvis.topk_tokens import topk_tokens as circuitsvis_topk_tokens
    except ImportError as exc:
        raise _circuitsvis_import_error("topk_tokens") from exc
    return circuitsvis_topk_tokens(tokens, activations, **kwargs)


def to_circuitsvis_model_performance(
    token_indices: Any,
    str_tokens: Sequence[str],
    logits: Any,
) -> Any:
    """Render CircuitsVis' combined logits/log-probs/probs model performance view."""

    try:
        from circuitsvis.tokens import (
            visualize_model_performance as circuitsvis_model_performance,
        )
    except ImportError as exc:
        raise _circuitsvis_import_error("visualize_model_performance") from exc
    return circuitsvis_model_performance(token_indices, list(str_tokens), logits)


def to_circuitsvis_topk_samples(
    tokens: Any,
    activations: Any,
    **kwargs: Any,
) -> Any:
    """Render top-k sample activations with CircuitsVis when installed."""

    try:
        from circuitsvis.topk_samples import topk_samples as circuitsvis_topk_samples
    except ImportError as exc:
        raise _circuitsvis_import_error("topk_samples") from exc
    return circuitsvis_topk_samples(tokens, activations, **kwargs)


def _attention_patterns_widget(
    heads: Sequence[Sequence[Sequence[Number]]],
    head_names: Sequence[str],
    tokens: Sequence[str],
    *,
    title: str | None,
    kind: str,
    include_overview: bool,
) -> Visualization:
    normalized = [_as_2d_numbers(head) for head in heads]
    if not normalized:
        raise ValueError("attention visualization needs at least one head.")
    size = len(normalized[0])
    if size == 0 or len(normalized[0][0]) == 0:
        raise ValueError("attention heads must be non-empty.")
    if any(len(head) != size or any(len(row) != size for row in head) for head in normalized):
        raise ValueError("attention pattern heads must be square and same-shaped.")
    if len(head_names) != len(normalized):
        raise ValueError("head_names length must match the number of heads.")
    token_labels = [str(token) for token in tokens]
    if len(token_labels) != size:
        raise ValueError("tokens length must match the attention dimensions.")

    viz_id = _next_viz_id(kind)
    overview = (
        '<button type="button" class="safelens-cv-head-button is-active" '
        'data-head="overview">'
        '<span class="safelens-cv-head-label">Overview</span>'
        f"{_attention_overview_svg(normalized)}"
        "</button>"
        if include_overview
        else ""
    )
    buttons = []
    for idx, (name, matrix) in enumerate(zip(head_names, normalized, strict=True)):
        active = " is-active" if idx == 0 and not include_overview else ""
        head_color = _attention_head_color(idx, len(normalized))
        buttons.append(
            f'<button type="button" class="safelens-cv-head-button{active}" data-head="{idx}">'
            f'<span class="safelens-cv-head-badge" style="background:{head_color};">'
            f"{escape(name)}</span>"
            f"{_attention_image_svg(matrix, head_index=idx, head_count=len(normalized), size=92)}"
            "</button>"
        )
    payload = {
        "heads": normalized,
        "headNames": list(head_names),
        "tokens": token_labels,
        "includeOverview": include_overview,
    }
    body = (
        f'<div id="{viz_id}" class="safelens-attention-head-browser safelens-cv-attention">'
        '<div class="safelens-cv-layout">'
        '<section class="safelens-cv-main">'
        '<div class="safelens-cv-section-title" data-role="focus-title"></div>'
        '<div class="safelens-cv-image-frame" data-role="attention-image"></div>'
        '<div class="safelens-focus-readout" data-role="readout"></div>'
        "</section>"
        '<aside class="safelens-cv-selector">'
        '<div class="safelens-cv-section-title">Head selector '
        "<span>(hover to view, click to lock)</span></div>"
        f'<div class="safelens-cv-head-grid">{overview}{"".join(buttons)}</div>'
        "</aside>"
        "</div>"
        '<div class="safelens-cv-token-panel">'
        '<label class="safelens-control-label">tokens '
        '<select class="safelens-select" data-role="token-view">'
        '<option value="destination_to_source">Source <- Destination</option>'
        '<option value="source_to_destination">Destination <- Source</option>'
        "</select></label>"
        '<div class="safelens-cv-token-strip" data-role="tokens"></div>'
        "</div>"
        f"{_json_script(viz_id, payload)}"
        f"{_attention_patterns_script(viz_id)}</div>"
    )
    return Visualization(
        html=_wrap_panel(kind, title, body),
        title=title,
        data={"heads": normalized, "head_names": list(head_names), "tokens": token_labels},
    )


def _attention_head_color(head_index: int, head_count: int, alpha: float = 1.0) -> str:
    hue = round((head_index / max(head_count, 1)) * 360)
    return f"hsla({hue}, 70%, 50%, {alpha:.3g})"


def _attention_cell_color(value: float, head_index: int, head_count: int) -> str:
    hue = round((head_index / max(head_count, 1)) * 360)
    intensity = max(0.0, min(1.0, value))
    lightness = 98 - 70 * intensity
    return f"hsl({hue}, 82%, {lightness:.3g}%)"


def _attention_image_svg(
    matrix: Sequence[Sequence[Number]],
    *,
    head_index: int,
    head_count: int,
    size: int,
) -> str:
    rows = _as_2d_numbers(matrix)
    height = len(rows)
    width = len(rows[0]) if height else 0
    cell = max(1.0, size / max(width, height, 1))
    svg_width = max(1, round(width * cell, 3))
    svg_height = max(1, round(height * cell, 3))
    parts = [
        (
            '<svg class="safelens-cv-attention-image" '
            f'width="{svg_width}" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}" aria-hidden="true">'
        )
    ]
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            parts.append(
                f'<rect x="{col_idx * cell:.3g}" y="{row_idx * cell:.3g}" '
                f'width="{cell:.3g}" height="{cell:.3g}" '
                f'fill="{_attention_cell_color(value, head_index, head_count)}"></rect>'
            )
    parts.append("</svg>")
    return "".join(parts)


def _attention_overview_svg(heads: Sequence[Sequence[Sequence[float]]], size: int = 92) -> str:
    height = len(heads[0])
    width = len(heads[0][0]) if height else 0
    cell = max(1.0, size / max(width, height, 1))
    svg_width = max(1, round(width * cell, 3))
    svg_height = max(1, round(height * cell, 3))
    parts = [
        (
            '<svg class="safelens-cv-attention-image" '
            f'width="{svg_width}" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}" aria-hidden="true">'
        )
    ]
    for row_idx in range(height):
        for col_idx in range(width):
            best_head = max(range(len(heads)), key=lambda idx: heads[idx][row_idx][col_idx])
            value = heads[best_head][row_idx][col_idx]
            parts.append(
                f'<rect x="{col_idx * cell:.3g}" y="{row_idx * cell:.3g}" '
                f'width="{cell:.3g}" height="{cell:.3g}" '
                f'fill="{_attention_cell_color(value, best_head, len(heads))}"></rect>'
            )
    parts.append("</svg>")
    return "".join(parts)


def _svg_heatmap(
    rows: Sequence[Sequence[float]],
    x_labels: Sequence[str],
    y_labels: Sequence[str],
    *,
    min_value: float,
    max_value: float,
    color: str,
    x_axis: str,
    y_axis: str,
) -> str:
    height = len(rows)
    width = len(rows[0]) if height else 0
    max_x_label = max((len(label) for label in x_labels), default=1)
    max_y_label = max((len(label) for label in y_labels), default=1)
    if max(width, height) <= 10:
        cell = 48
    elif max(width, height) <= 16:
        cell = 36
    else:
        cell = 28
    left = min(180, max(78, max_y_label * 7 + 28))
    top = min(220, max(96, max_x_label * 7 + 52))
    right = 24
    bottom = 46
    svg_width = left + width * cell + right
    svg_height = top + height * cell + bottom
    show_values = width * height <= 144 and cell >= 28

    parts = [
        (
            '<svg class="safelens-heatmap-svg" '
            f'width="{svg_width}" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}" '
            'role="img" aria-label="SafeLens heatmap">'
        ),
        '<rect class="safelens-heatmap-background" width="100%" height="100%"></rect>',
    ]
    if x_axis:
        parts.append(
            f'<text class="safelens-axis-label" x="{left + width * cell / 2:.1f}" '
            f'y="{svg_height - 10}" text-anchor="middle">{escape(x_axis)}</text>'
        )
    if y_axis:
        y_mid = top + height * cell / 2
        parts.append(
            f'<text class="safelens-axis-label" x="16" y="{y_mid:.1f}" '
            f'text-anchor="middle" transform="rotate(-90 16 {y_mid:.1f})">{escape(y_axis)}</text>'
        )

    for col_idx, label in enumerate(x_labels):
        x = left + col_idx * cell + cell / 2
        y = top - 48
        parts.append(
            f'<text class="safelens-heatmap-label safelens-x-label" '
            f'x="{x:.1f}" y="{y:.1f}" text-anchor="end" '
            f'transform="rotate(-45 {x:.1f} {y:.1f})">{escape(label)}</text>'
        )
    for row_idx, label in enumerate(y_labels):
        y = top + row_idx * cell + cell / 2 + 4
        parts.append(
            f'<text class="safelens-heatmap-label safelens-y-label" '
            f'x="{left - 10}" y="{y:.1f}" text-anchor="end">{escape(label)}</text>'
        )

    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            background, foreground = _value_color(value, min_value, max_value, color=color)
            x = left + col_idx * cell
            y = top + row_idx * cell
            row_label = escape(y_labels[row_idx], quote=True)
            col_label = escape(x_labels[col_idx], quote=True)
            parts.append(
                '<rect class="safelens-heatmap-cell" '
                f'x="{x:.1f}" y="{y:.1f}" width="{cell - 1}" height="{cell - 1}" rx="3" '
                f'fill="{background}" data-row="{row_idx}" data-col="{col_idx}" '
                f'data-row-label="{row_label}" data-col-label="{col_label}" '
                f'data-value="{value:.12g}"><title>'
                f"{escape(y_labels[row_idx])} x {escape(x_labels[col_idx])}: {value:.6g}"
                "</title></rect>"
            )
            if show_values:
                parts.append(
                    f'<text class="safelens-heatmap-value" x="{x + cell / 2:.1f}" '
                    f'y="{y + cell / 2 + 3:.1f}" text-anchor="middle" '
                    f'fill="{foreground}">{value:.3g}</text>'
                )
    parts.append("</svg>")
    return "".join(parts)


def _mini_heatmap_svg(
    matrix: Sequence[Sequence[Number]],
    *,
    min_value: float,
    max_value: float,
    color: str,
) -> str:
    rows = _as_2d_numbers(matrix)
    height = len(rows)
    width = len(rows[0]) if height else 0
    cell = 9
    gap = 1
    svg_width = max(1, width * (cell + gap) - gap)
    svg_height = max(1, height * (cell + gap) - gap)
    parts = [
        (
            '<svg class="safelens-mini-heatmap" '
            f'width="{svg_width}" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}" aria-hidden="true">'
        )
    ]
    for row_idx, row in enumerate(rows):
        for col_idx, value in enumerate(row):
            background, _foreground = _value_color(value, min_value, max_value, color=color)
            parts.append(
                f'<rect x="{col_idx * (cell + gap)}" y="{row_idx * (cell + gap)}" '
                f'width="{cell}" height="{cell}" rx="1.5" fill="{background}"></rect>'
            )
    parts.append("</svg>")
    return "".join(parts)


def _heatmap(
    matrix: Sequence[Sequence[Number]],
    *,
    title: str | None,
    x_labels: Sequence[str] | None = None,
    y_labels: Sequence[str] | None = None,
    x_axis: str = "",
    y_axis: str = "",
    color: str = "red_blue",
) -> Visualization:
    rows = [list(map(float, row)) for row in matrix]
    if not rows or not rows[0]:
        raise ValueError("heatmap data must be a non-empty 2D matrix.")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("heatmap rows must all have the same length.")
    values = [value for row in rows for value in row]
    min_value, max_value = _value_range(values)
    x_names = list(x_labels) if x_labels is not None else [str(i) for i in range(width)]
    y_names = list(y_labels) if y_labels is not None else [str(i) for i in range(len(rows))]

    viz_id = _next_viz_id("heatmap")
    svg = _svg_heatmap(
        rows,
        x_names,
        y_names,
        min_value=min_value,
        max_value=max_value,
        color=color,
        x_axis=x_axis,
        y_axis=y_axis,
    )
    body = (
        f'<div id="{viz_id}" class="safelens-heatmap-widget">'
        '<div class="safelens-heatmap-scroller">'
        f"{svg}</div>"
        '<div class="safelens-focus-readout" data-role="readout"></div>'
        + _legend(min_value, max_value, color=color)
        + _heatmap_focus_script(viz_id)
        + "</div>"
    )
    return Visualization(
        html=_wrap_panel("heatmap", title, body),
        title=title,
        data={
            "matrix": rows,
            "x_labels": x_names,
            "y_labels": y_names,
            "x_axis": x_axis,
            "y_axis": y_axis,
        },
    )


def _matrix_browser(
    matrices: Sequence[Sequence[Sequence[Number]]],
    matrix_labels: Sequence[str],
    *,
    x_labels: Sequence[str],
    y_labels: Sequence[str],
    title: str | None,
    kind: str,
    selector_label: str,
    color: str,
    allow_transpose: bool,
    x_axis: str,
    y_axis: str,
) -> Visualization:
    normalized = [_as_2d_numbers(matrix) for matrix in matrices]
    if not normalized:
        raise ValueError("matrix browser needs at least one matrix.")
    height = len(normalized[0])
    width = len(normalized[0][0]) if height else 0
    if not height or not width:
        raise ValueError("matrix browser matrices must be non-empty.")
    if any(
        len(matrix) != height or any(len(row) != width for row in matrix) for matrix in normalized
    ):
        raise ValueError("all matrices must have the same shape.")
    if len(matrix_labels) != len(normalized):
        raise ValueError("matrix_labels length must match the number of matrices.")
    if len(x_labels) != width:
        raise ValueError("x_labels length must match the matrix width.")
    if len(y_labels) != height:
        raise ValueError("y_labels length must match the matrix height.")

    values = [value for matrix in normalized for row in matrix for value in row]
    min_value, max_value = _value_range(values)
    viz_id = _next_viz_id(kind)
    mode_control = ""
    if allow_transpose:
        mode_control = (
            '<label class="safelens-control-label">view '
            '<select class="safelens-select" data-filter="mode">'
            '<option value="normal">query to key</option>'
            '<option value="transpose">key to query</option>'
            "</select></label>"
        )
    payload = {
        "matrices": normalized,
        "matrixLabels": list(matrix_labels),
        "xLabels": list(x_labels),
        "yLabels": list(y_labels),
        "min": min_value,
        "max": max_value,
        "color": color,
        "xAxis": x_axis,
        "yAxis": y_axis,
    }
    body = (
        f'<div id="{viz_id}" class="safelens-matrix-browser">'
        '<div class="safelens-controls">'
        f"{_select_control(viz_id, selector_label, matrix_labels)}"
        f"{mode_control}</div>"
        '<div class="safelens-heatmap-scroller" data-role="matrix"></div>'
        '<div class="safelens-focus-readout" data-role="readout"></div>'
        f"{_legend(min_value, max_value, color=color)}"
        f"{_json_script(viz_id, payload)}"
        f"{_matrix_browser_script(viz_id)}</div>"
    )
    return Visualization(
        html=_wrap_panel(kind, title, body),
        title=title,
        data={
            "matrices": normalized,
            "matrix_labels": list(matrix_labels),
            "x_labels": list(x_labels),
            "y_labels": list(y_labels),
        },
    )


def _next_viz_id(kind: str) -> str:
    safe_kind = "".join(char if char.isalnum() else "-" for char in kind).strip("-")
    return f"safelens-{safe_kind}-{next(_VIZ_ID_COUNTER)}"


def _json_payload(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        default=str,
        allow_nan=False,
    ).replace("</", "<\\/")


def _json_script(viz_id: str, payload: Any) -> str:
    return f'<script type="application/json" id="{viz_id}-data">{_json_payload(payload)}</script>'


def _heatmap_focus_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  if (!root) return;
  const cells = Array.from(root.querySelectorAll(".safelens-heatmap-cell"));
  const readout = root.querySelector('[data-role="readout"]');
  let pinned = null;
  function setFocus(cell) {{
    const row = cell.dataset.row;
    const col = cell.dataset.col;
    cells.forEach((candidate) => {{
      candidate.classList.toggle("safelens-cell-focus", candidate === cell);
      candidate.classList.toggle("safelens-row-focus", candidate.dataset.row === row);
      candidate.classList.toggle("safelens-col-focus", candidate.dataset.col === col);
    }});
    if (readout) {{
      readout.textContent = `${{cell.dataset.rowLabel}} x ${{cell.dataset.colLabel}}: ` +
        `${{formatValue(Number(cell.dataset.value))}}`;
    }}
  }}
  function clearFocus() {{
    if (pinned) {{
      setFocus(pinned);
      return;
    }}
    cells.forEach((cell) => {{
      cell.classList.remove("safelens-cell-focus", "safelens-row-focus", "safelens-col-focus");
    }});
    if (readout) readout.textContent = "";
  }}
  cells.forEach((cell) => {{
    cell.addEventListener("mouseenter", () => setFocus(cell));
    cell.addEventListener("mouseleave", clearFocus);
    cell.addEventListener("click", () => {{
      pinned = pinned === cell ? null : cell;
      clearFocus();
    }});
  }});
}})();
</script>
"""


def _matrix_browser_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  const dataNode = document.getElementById("{viz_id}-data");
  if (!root || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const matrixSelect = root.querySelector(".safelens-select");
  const modeSelect = root.querySelector('[data-filter="mode"]');
  const host = root.querySelector('[data-role="matrix"]');
  const readout = root.querySelector('[data-role="readout"]');
  const SVG_NS = "http://www.w3.org/2000/svg";
  let pinned = null;
  function valueColor(value) {{
    const minValue = data.min;
    const maxValue = data.max;
    if (data.color === "blue") {{
      const intensity = Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue || 1)));
      const red = Math.round(248 - 211 * intensity);
      const green = Math.round(250 - 151 * intensity);
      const blue = Math.round(252 - 17 * intensity);
      const lum = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;
      return [`rgb(${{red}},${{green}},${{blue}})`, lum > 0.58 ? "#111827" : "#ffffff"];
    }}
    const midpoint = minValue <= 0 && maxValue >= 0 ? 0 : (minValue + maxValue) / 2;
    let red, green, blue, intensity, denominator;
    if (value >= midpoint) {{
      denominator = maxValue - midpoint || 1;
      intensity = Math.min(1, (value - midpoint) / denominator);
      red = Math.round(255 - 30 * intensity);
      green = Math.round(255 - 226 * intensity);
      blue = Math.round(255 - 109 * intensity);
    }} else {{
      denominator = midpoint - minValue || 1;
      intensity = Math.min(1, (midpoint - value) / denominator);
      red = Math.round(255 - 218 * intensity);
      green = Math.round(255 - 156 * intensity);
      blue = Math.round(255 - 20 * intensity);
    }}
    const lum = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;
    return [`rgb(${{red}},${{green}},${{blue}})`, lum > 0.58 ? "#111827" : "#ffffff"];
  }}
  function svgEl(tag, attrs = {{}}, text = null) {{
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== null) node.textContent = text;
    return node;
  }}
  function transpose(matrix) {{
    return matrix[0].map((_, col) => matrix.map((row) => row[col]));
  }}
  function formatValue(value) {{
    const absValue = Math.abs(value);
    if (absValue === 0) return "0";
    if (absValue >= 0.01 && absValue < 1000) {{
      return value.toFixed(3).replace(/(\\.\\d*?[1-9])0+$/, "$1").replace(/\\.0+$/, "");
    }}
    return value.toExponential(2);
  }}
  function focusCell(cell) {{
    const row = cell.dataset.row;
    const col = cell.dataset.col;
    host.querySelectorAll(".safelens-heatmap-cell").forEach((candidate) => {{
      candidate.classList.toggle("safelens-cell-focus", candidate === cell);
      candidate.classList.toggle("safelens-row-focus", candidate.dataset.row === row);
      candidate.classList.toggle("safelens-col-focus", candidate.dataset.col === col);
    }});
    if (readout) {{
      readout.textContent = `${{cell.dataset.rowLabel}} x ${{cell.dataset.colLabel}}: ` +
        `${{Number(cell.dataset.value).toPrecision(6)}}`;
    }}
  }}
  function clearFocus() {{
    if (pinned) {{
      focusCell(pinned);
      return;
    }}
    host.querySelectorAll(".safelens-heatmap-cell").forEach((cell) => {{
      cell.classList.remove("safelens-cell-focus", "safelens-row-focus", "safelens-col-focus");
    }});
    if (readout) readout.textContent = "";
  }}
  function renderHeatmap(matrix, xLabels, yLabels, xAxis, yAxis) {{
    const height = matrix.length;
    const width = height ? matrix[0].length : 0;
    const maxX = xLabels.reduce((acc, label) => Math.max(acc, String(label).length), 1);
    const maxY = yLabels.reduce((acc, label) => Math.max(acc, String(label).length), 1);
    const cell = Math.max(24, Math.min(48, Math.floor(720 / Math.max(width, 1))));
    const left = Math.min(180, Math.max(78, maxY * 7 + 28));
    const top = Math.min(220, Math.max(96, maxX * 7 + 52));
    const right = 24;
    const bottom = 46;
    const svgWidth = left + width * cell + right;
    const svgHeight = top + height * cell + bottom;
    const showValues = width * height <= 144 && cell >= 28;
    const svg = svgEl("svg", {{
      class: "safelens-heatmap-svg",
      width: svgWidth,
      height: svgHeight,
      viewBox: `0 0 ${{svgWidth}} ${{svgHeight}}`,
      role: "img",
      "aria-label": "SafeLens heatmap",
    }});
    svg.appendChild(svgEl("rect", {{
      class: "safelens-heatmap-background",
      width: "100%",
      height: "100%",
    }}));
    if (xAxis) {{
      svg.appendChild(svgEl("text", {{
        class: "safelens-axis-label",
        x: left + (width * cell) / 2,
        y: svgHeight - 10,
        "text-anchor": "middle",
      }}, xAxis));
    }}
    if (yAxis) {{
      const yMid = top + (height * cell) / 2;
      svg.appendChild(svgEl("text", {{
        class: "safelens-axis-label",
        x: 16,
        y: yMid,
        "text-anchor": "middle",
        transform: `rotate(-90 16 ${{yMid}})`,
      }}, yAxis));
    }}
    xLabels.forEach((label, colIndex) => {{
      const x = left + colIndex * cell + cell / 2;
      const y = top - 48;
      svg.appendChild(svgEl("text", {{
        class: "safelens-heatmap-label safelens-x-label",
        x,
        y,
        "text-anchor": "end",
        transform: `rotate(-45 ${{x}} ${{y}})`,
      }}, label));
    }});
    yLabels.forEach((label, rowIndex) => {{
      svg.appendChild(svgEl("text", {{
        class: "safelens-heatmap-label safelens-y-label",
        x: left - 10,
        y: top + rowIndex * cell + cell / 2 + 4,
        "text-anchor": "end",
      }}, label));
    }});
    matrix.forEach((row, rowIndex) => {{
      row.forEach((value, colIndex) => {{
        const number = Number(value);
        const colors = valueColor(number);
        const x = left + colIndex * cell;
        const y = top + rowIndex * cell;
        const rect = svgEl("rect", {{
          class: "safelens-heatmap-cell",
          x,
          y,
          width: cell - 1,
          height: cell - 1,
          rx: 3,
          fill: colors[0],
          "data-row": rowIndex,
          "data-col": colIndex,
          "data-row-label": yLabels[rowIndex],
          "data-col-label": xLabels[colIndex],
          "data-value": number,
        }});
        rect.appendChild(svgEl(
          "title",
          {{}},
          `${{yLabels[rowIndex]}} x ${{xLabels[colIndex]}}: ${{formatValue(number)}}`,
        ));
        svg.appendChild(rect);
        if (showValues) {{
          svg.appendChild(svgEl("text", {{
            class: "safelens-heatmap-value",
            x: x + cell / 2,
            y: y + cell / 2 + 3,
            "text-anchor": "middle",
            fill: colors[1],
          }}, formatValue(number)));
        }}
      }});
    }});
    host.textContent = "";
    host.appendChild(svg);
    host.querySelectorAll(".safelens-heatmap-cell").forEach((cell) => {{
      cell.addEventListener("mouseenter", () => focusCell(cell));
      cell.addEventListener("mouseleave", clearFocus);
      cell.addEventListener("click", () => {{
        pinned = pinned === cell ? null : cell;
        clearFocus();
      }});
    }});
  }}
  function render() {{
    pinned = null;
    const matrixIndex = Number(matrixSelect.value);
    const transposed = modeSelect && modeSelect.value === "transpose";
    const matrix = transposed ? transpose(data.matrices[matrixIndex]) : data.matrices[matrixIndex];
    const xLabels = transposed ? data.yLabels : data.xLabels;
    const yLabels = transposed ? data.xLabels : data.yLabels;
    renderHeatmap(
      matrix,
      xLabels,
      yLabels,
      transposed ? data.yAxis : data.xAxis,
      transposed ? data.xAxis : data.yAxis,
    );
    clearFocus();
  }}
  matrixSelect.addEventListener("change", render);
  if (modeSelect) modeSelect.addEventListener("change", render);
  render();
}})();
</script>
"""


def _attention_patterns_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  const dataNode = document.getElementById("{viz_id}-data");
  if (!root || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const imageHost = root.querySelector('[data-role="attention-image"]');
  const readout = root.querySelector('[data-role="readout"]');
  const titleNode = root.querySelector('[data-role="focus-title"]');
  const tokenHost = root.querySelector('[data-role="tokens"]');
  const tokenViewSelect = root.querySelector('[data-role="token-view"]');
  const headButtons = Array.from(root.querySelectorAll("[data-head]"));
  const SVG_NS = "http://www.w3.org/2000/svg";
  let hoveredHead = null;
  let lockedHead = data.includeOverview ? null : 0;
  let hoveredToken = null;
  let lockedToken = null;

  function svgEl(tag, attrs = {{}}, text = null) {{
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== null) node.textContent = text;
    return node;
  }}
  function clamp01(value) {{
    return Math.max(0, Math.min(1, Number(value)));
  }}
  function headColor(head, alpha = 1) {{
    const hue = Math.round((head / Math.max(data.heads.length, 1)) * 360);
    return `hsla(${{hue}}, 70%, 50%, ${{alpha}})`;
  }}
  function attentionColor(value, head) {{
    const hue = Math.round((head / Math.max(data.heads.length, 1)) * 360);
    const lightness = 98 - 70 * clamp01(value);
    return `hsl(${{hue}}, 82%, ${{lightness}}%)`;
  }}
  function textColorFor(value) {{
    return clamp01(value) > 0.58 ? "#ffffff" : "#111827";
  }}
  function formatValue(value) {{
    const number = Number(value);
    const absValue = Math.abs(number);
    if (absValue === 0) return "0";
    if (absValue >= 0.01 && absValue < 1000) {{
      return number.toFixed(3).replace(/(\\.\\d*?[1-9])0+$/, "$1").replace(/\\.0+$/, "");
    }}
    return number.toExponential(2);
  }}
  function activeHead() {{
    return hoveredHead !== null ? hoveredHead : lockedHead;
  }}
  function activeToken() {{
    return hoveredToken !== null ? hoveredToken : lockedToken;
  }}
  function parseHead(value) {{
    return value === "overview" ? null : Number(value);
  }}
  function bestHeadForCell(dest, src) {{
    let bestHead = 0;
    let bestValue = data.heads[0][dest][src];
    for (let head = 1; head < data.heads.length; head += 1) {{
      const value = data.heads[head][dest][src];
      if (value > bestValue) {{
        bestValue = value;
        bestHead = head;
      }}
    }}
    return [bestHead, bestValue];
  }}
  function cellInfo(head, dest, src) {{
    if (head === null) {{
      const [bestHead, bestValue] = bestHeadForCell(dest, src);
      return {{ head: bestHead, value: bestValue }};
    }}
    return {{ head, value: data.heads[head][dest][src] }};
  }}
  function tokenValue(head, tokenIndex, focusToken, view) {{
    const size = data.tokens.length;
    if (focusToken !== null) {{
      if (view === "destination_to_source") {{
        return cellInfo(head, focusToken, tokenIndex);
      }}
      return cellInfo(head, tokenIndex, focusToken);
    }}
    let total = 0;
    let bestHead = 0;
    let count = 0;
    if (view === "destination_to_source") {{
      for (let src = 0; src <= tokenIndex; src += 1) {{
        const info = cellInfo(head, tokenIndex, src);
        total += info.value;
        bestHead = info.value >= (head === null ? data.heads[bestHead][tokenIndex][src] : -1)
          ? info.head
          : bestHead;
        count += 1;
      }}
    }} else {{
      for (let dest = tokenIndex; dest < size; dest += 1) {{
        const info = cellInfo(head, dest, tokenIndex);
        total += info.value;
        bestHead = info.value >= (head === null ? data.heads[bestHead][dest][tokenIndex] : -1)
          ? info.head
          : bestHead;
        count += 1;
      }}
    }}
    return {{ head: head === null ? bestHead : head, value: total / Math.max(count, 1) }};
  }}
  function renderImage() {{
    const head = activeHead();
    const rows = data.tokens.length;
    const cols = data.tokens.length;
    const cell = Math.max(8, Math.min(54, Math.floor(520 / Math.max(cols, 1))));
    const width = cols * cell;
    const height = rows * cell;
    const svg = svgEl("svg", {{
      class: "safelens-cv-main-image",
      width,
      height,
      viewBox: `0 0 ${{width}} ${{height}}`,
      role: "img",
      "aria-label": "attention pattern",
    }});
    const token = activeToken();
    for (let dest = 0; dest < rows; dest += 1) {{
      for (let src = 0; src < cols; src += 1) {{
        const info = cellInfo(head, dest, src);
        const rect = svgEl("rect", {{
          x: src * cell,
          y: dest * cell,
          width: cell,
          height: cell,
          fill: attentionColor(info.value, info.head),
          class: "safelens-cv-cell",
          "data-dest": dest,
          "data-src": src,
          "data-head": info.head,
          "data-value": info.value,
        }});
        if (token !== null && (token === dest || token === src)) {{
          rect.classList.add("is-token-focused");
        }}
        rect.appendChild(svgEl(
          "title",
          {{}},
          `${{data.headNames[info.head]}} | dest ${{dest}} ${{data.tokens[dest]}} <- ` +
            `src ${{src}} ${{data.tokens[src]}}: ${{formatValue(info.value)}}`,
        ));
        rect.addEventListener("mouseenter", () => {{
          if (readout) {{
            readout.textContent =
              `${{data.headNames[info.head]}} | dest ${{dest}} ${{data.tokens[dest]}} <- ` +
              `src ${{src}} ${{data.tokens[src]}}: ${{formatValue(info.value)}}`;
          }}
        }});
        rect.addEventListener("mouseleave", () => {{
          if (readout) readout.textContent = "";
        }});
        svg.appendChild(rect);
      }}
    }}
    imageHost.textContent = "";
    imageHost.appendChild(svg);
    if (titleNode) {{
      titleNode.textContent = head === null
        ? "Attention Patterns"
        : `${{data.headNames[head]}} Zoomed`;
    }}
  }}
  function renderTokens() {{
    const head = activeHead();
    const token = activeToken();
    const view = tokenViewSelect.value;
    tokenHost.textContent = "";
    data.tokens.forEach((label, tokenIndex) => {{
      const info = tokenValue(head, tokenIndex, token, view);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "safelens-cv-token";
      if (token === tokenIndex) button.classList.add("is-active");
      button.style.background = attentionColor(info.value, info.head);
      button.style.color = textColorFor(info.value);
      button.textContent = label;
      button.title = `${{label}}: ${{formatValue(info.value)}}`;
      button.addEventListener("mouseenter", () => {{
        hoveredToken = tokenIndex;
        render();
      }});
      button.addEventListener("mouseleave", () => {{
        hoveredToken = null;
        render();
      }});
      button.addEventListener("click", () => {{
        lockedToken = lockedToken === tokenIndex ? null : tokenIndex;
        render();
      }});
      tokenHost.appendChild(button);
    }});
  }}
  function renderButtons() {{
    const head = activeHead();
    headButtons.forEach((button) => {{
      const buttonHead = parseHead(button.dataset.head);
      const active = buttonHead === head || (buttonHead === null && head === null);
      button.classList.toggle("is-active", active);
      if (buttonHead !== null) {{
        button.style.setProperty("--safelens-head-color", headColor(buttonHead));
        button.style.setProperty("--safelens-head-glow", headColor(buttonHead, 0.35));
      }}
    }});
  }}
  function render() {{
    renderButtons();
    renderImage();
    renderTokens();
  }}
  headButtons.forEach((button) => {{
    button.addEventListener("mouseenter", () => {{
      hoveredHead = parseHead(button.dataset.head);
      render();
    }});
    button.addEventListener("mouseleave", () => {{
      hoveredHead = null;
      render();
    }});
    button.addEventListener("click", () => {{
      const clicked = parseHead(button.dataset.head);
      lockedHead = lockedHead === clicked ? (data.includeOverview ? null : 0) : clicked;
      render();
    }});
  }});
  tokenViewSelect.addEventListener("change", render);
  render();
}})();
</script>
"""


def _attention_heads_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  const dataNode = document.getElementById("{viz_id}-data");
  if (!root || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const buttons = Array.from(root.querySelectorAll("[data-head]"));
  const host = root.querySelector('[data-role="matrix"]');
  const readout = root.querySelector('[data-role="readout"]');
  const title = root.querySelector('[data-role="head-title"]');
  const SVG_NS = "http://www.w3.org/2000/svg";
  let pinned = null;
  function valueColor(value) {{
    const minValue = data.min;
    const maxValue = data.max;
    const intensity = Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue || 1)));
    const red = Math.round(248 - 211 * intensity);
    const green = Math.round(250 - 151 * intensity);
    const blue = Math.round(252 - 17 * intensity);
    const lum = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;
    return [`rgb(${{red}},${{green}},${{blue}})`, lum > 0.58 ? "#111827" : "#ffffff"];
  }}
  function svgEl(tag, attrs = {{}}, text = null) {{
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== null) node.textContent = text;
    return node;
  }}
  function formatValue(value) {{
    const absValue = Math.abs(value);
    if (absValue === 0) return "0";
    if (absValue >= 0.01 && absValue < 1000) {{
      return value.toFixed(3).replace(/(\\.\\d*?[1-9])0+$/, "$1").replace(/\\.0+$/, "");
    }}
    return value.toExponential(2);
  }}
  function focusCell(cell) {{
    const row = cell.dataset.row;
    const col = cell.dataset.col;
    host.querySelectorAll(".safelens-heatmap-cell").forEach((candidate) => {{
      candidate.classList.toggle("safelens-cell-focus", candidate === cell);
      candidate.classList.toggle("safelens-row-focus", candidate.dataset.row === row);
      candidate.classList.toggle("safelens-col-focus", candidate.dataset.col === col);
    }});
    if (readout) {{
      readout.textContent = `${{cell.dataset.rowLabel}} -> ${{cell.dataset.colLabel}}: ` +
        `${{formatValue(Number(cell.dataset.value))}}`;
    }}
  }}
  function clearFocus() {{
    if (pinned) {{
      focusCell(pinned);
      return;
    }}
    host.querySelectorAll(".safelens-heatmap-cell").forEach((cell) => {{
      cell.classList.remove("safelens-cell-focus", "safelens-row-focus", "safelens-col-focus");
    }});
    if (readout) readout.textContent = "";
  }}
  function renderHeatmap(matrix) {{
    const xLabels = data.xLabels;
    const yLabels = data.yLabels;
    const height = matrix.length;
    const width = height ? matrix[0].length : 0;
    const maxX = xLabels.reduce((acc, label) => Math.max(acc, String(label).length), 1);
    const maxY = yLabels.reduce((acc, label) => Math.max(acc, String(label).length), 1);
    const cell = Math.max(24, Math.min(48, Math.floor(720 / Math.max(width, 1))));
    const left = Math.min(180, Math.max(78, maxY * 7 + 28));
    const top = Math.min(220, Math.max(96, maxX * 7 + 52));
    const right = 24;
    const bottom = 46;
    const svgWidth = left + width * cell + right;
    const svgHeight = top + height * cell + bottom;
    const showValues = width * height <= 144 && cell >= 28;
    const svg = svgEl("svg", {{
      class: "safelens-heatmap-svg",
      width: svgWidth,
      height: svgHeight,
      viewBox: `0 0 ${{svgWidth}} ${{svgHeight}}`,
      role: "img",
      "aria-label": "SafeLens attention head heatmap",
    }});
    svg.appendChild(svgEl("rect", {{
      class: "safelens-heatmap-background",
      width: "100%",
      height: "100%",
    }}));
    svg.appendChild(svgEl("text", {{
      class: "safelens-axis-label",
      x: left + (width * cell) / 2,
      y: svgHeight - 10,
      "text-anchor": "middle",
    }}, data.xAxis));
    const yMid = top + (height * cell) / 2;
    svg.appendChild(svgEl("text", {{
      class: "safelens-axis-label",
      x: 16,
      y: yMid,
      "text-anchor": "middle",
      transform: `rotate(-90 16 ${{yMid}})`,
    }}, data.yAxis));
    xLabels.forEach((label, colIndex) => {{
      const x = left + colIndex * cell + cell / 2;
      const y = top - 48;
      svg.appendChild(svgEl("text", {{
        class: "safelens-heatmap-label safelens-x-label",
        x,
        y,
        "text-anchor": "end",
        transform: `rotate(-45 ${{x}} ${{y}})`,
      }}, label));
    }});
    yLabels.forEach((label, rowIndex) => {{
      svg.appendChild(svgEl("text", {{
        class: "safelens-heatmap-label safelens-y-label",
        x: left - 10,
        y: top + rowIndex * cell + cell / 2 + 4,
        "text-anchor": "end",
      }}, label));
    }});
    matrix.forEach((row, rowIndex) => {{
      row.forEach((value, colIndex) => {{
        const number = Number(value);
        const colors = valueColor(number);
        const x = left + colIndex * cell;
        const y = top + rowIndex * cell;
        const rect = svgEl("rect", {{
          class: "safelens-heatmap-cell",
          x,
          y,
          width: cell - 1,
          height: cell - 1,
          rx: 3,
          fill: colors[0],
          "data-row": rowIndex,
          "data-col": colIndex,
          "data-row-label": yLabels[rowIndex],
          "data-col-label": xLabels[colIndex],
          "data-value": number,
        }});
        rect.appendChild(svgEl(
          "title",
          {{}},
          `${{yLabels[rowIndex]}} -> ${{xLabels[colIndex]}}: ${{formatValue(number)}}`,
        ));
        svg.appendChild(rect);
        if (showValues) {{
          svg.appendChild(svgEl("text", {{
            class: "safelens-heatmap-value",
            x: x + cell / 2,
            y: y + cell / 2 + 3,
            "text-anchor": "middle",
            fill: colors[1],
          }}, formatValue(number)));
        }}
      }});
    }});
    host.textContent = "";
    host.appendChild(svg);
    host.querySelectorAll(".safelens-heatmap-cell").forEach((cell) => {{
      cell.addEventListener("mouseenter", () => focusCell(cell));
      cell.addEventListener("mouseleave", clearFocus);
      cell.addEventListener("click", () => {{
        pinned = pinned === cell ? null : cell;
        clearFocus();
      }});
    }});
  }}
  function showHead(index) {{
    pinned = null;
    const headIndex = Number(index);
    buttons.forEach((button) => {{
      button.classList.toggle("is-active", Number(button.dataset.head) === headIndex);
    }});
    if (title) title.textContent = data.headNames[headIndex];
    renderHeatmap(data.heads[headIndex]);
    clearFocus();
  }}
  buttons.forEach((button) => {{
    button.addEventListener("mouseenter", () => showHead(button.dataset.head));
    button.addEventListener("click", () => showHead(button.dataset.head));
  }});
  showHead(0);
}})();
</script>
"""


def _tokens_multi_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  const dataNode = document.getElementById("{viz_id}-data");
  if (!root || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const buttons = Array.from(root.querySelectorAll("[data-track]"));
  const tokens = Array.from(root.querySelectorAll("[data-token-index]"));
  const readout = root.querySelector('[data-role="readout"]');
  function showTrack(track) {{
    const idx = Number(track);
    buttons.forEach((button) => {{
      button.classList.toggle("is-active", Number(button.dataset.track) === idx);
    }});
    tokens.forEach((token) => {{
      const tokenIdx = Number(token.dataset.tokenIndex);
      const colors = data.colors[idx][tokenIdx];
      token.style.background = colors[0];
      token.style.color = colors[1];
      token.title = `${{data.labels[idx]}}: ${{Number(data.values[idx][tokenIdx]).toPrecision(6)}}`;
    }});
    if (readout) readout.textContent = data.labels[idx];
  }}
  buttons.forEach((button) => {{
    button.addEventListener("mouseenter", () => showTrack(button.dataset.track));
    button.addEventListener("click", () => showTrack(button.dataset.track));
  }});
  showTrack(0);
}})();
</script>
"""


def _head_selector_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  if (!root) return;
  const buttons = Array.from(root.querySelectorAll("[data-head]"));
  const panels = Array.from(root.querySelectorAll("[data-head-panel]"));
  function showHead(head) {{
    buttons.forEach((button) => {{
      button.classList.toggle("is-active", button.dataset.head === String(head));
    }});
    panels.forEach((panel) => {{
      panel.classList.toggle("safelens-hidden", panel.dataset.headPanel !== String(head));
    }});
  }}
  buttons.forEach((button) => {{
    button.addEventListener("mouseenter", () => showHead(button.dataset.head));
    button.addEventListener("click", () => showHead(button.dataset.head));
  }});
  showHead(0);
}})();
</script>
"""


def _text_neuron_browser_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  const dataNode = document.getElementById("{viz_id}-data");
  if (!root || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const tokenContainer = root.querySelector('[data-role="tokens"]');
  const readout = root.querySelector('[data-role="readout"]');
  const sampleSelect = root.querySelector('[data-filter="sample"]');
  const layerSelect = root.querySelector('[data-filter="layer"]');
  const neuronSelect = root.querySelector('[data-filter="neuron"]');
  function valueColor(value) {{
    const minValue = data.min;
    const maxValue = data.max;
    const midpoint = minValue <= 0 && maxValue >= 0 ? 0 : (minValue + maxValue) / 2;
    let red, green, blue, intensity, denominator;
    if (value >= midpoint) {{
      denominator = maxValue - midpoint || 1;
      intensity = Math.min(1, (value - midpoint) / denominator);
      red = 255;
      green = Math.round(245 - 105 * intensity);
      blue = Math.round(245 - 125 * intensity);
    }} else {{
      denominator = midpoint - minValue || 1;
      intensity = Math.min(1, (midpoint - value) / denominator);
      red = Math.round(245 - 125 * intensity);
      green = Math.round(248 - 88 * intensity);
      blue = 255;
    }}
    const luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;
    return [`rgb(${{red}},${{green}},${{blue}})`, luminance > 0.58 ? "#111827" : "#ffffff"];
  }}
  function render() {{
    const sample = Number(sampleSelect.value);
    const layer = Number(layerSelect.value);
    const neuron = Number(neuronSelect.value);
    tokenContainer.innerHTML = "";
    data.tokens[sample].forEach((token, tokenIdx) => {{
      const value = Number(data.activations[sample][tokenIdx][layer][neuron]);
      const colors = valueColor(value);
      const span = document.createElement("span");
      span.className = "safelens-token safelens-live-token";
      span.textContent = token;
      span.style.background = colors[0];
      span.style.color = colors[1];
      span.title = `${{token}}: ${{value.toPrecision(6)}}`;
      tokenContainer.appendChild(span);
    }});
    if (readout) {{
      readout.textContent =
        `${{data.sampleLabels[sample]}} / ${{data.layerLabels[layer]}} / ` +
        `${{data.neuronLabels[neuron]}}`;
    }}
  }}
  [sampleSelect, layerSelect, neuronSelect].forEach((select) => {{
    select.addEventListener("change", render);
  }});
  render();
}})();
</script>
"""


def _table_filter_sort_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  if (!root) return;
  const table = root.querySelector('[data-role="table"]');
  if (!table) return;
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr[data-row]"));
  const queryInput = root.querySelector('[data-filter="query"]');
  function applyQuery() {{
    const query = queryInput ? queryInput.value.toLowerCase() : "";
    rows.forEach((row) => {{
      row.classList.toggle("safelens-hidden", query && !row.dataset.rowText.includes(query));
    }});
  }}
  if (queryInput) queryInput.addEventListener("input", applyQuery);
  table.querySelectorAll("th[data-sort-index]").forEach((header) => {{
    header.addEventListener("click", () => {{
      const index = Number(header.dataset.sortIndex);
      const direction = header.dataset.direction === "asc" ? "desc" : "asc";
      header.dataset.direction = direction;
      rows.sort((left, right) => {{
        const a = left.children[index].textContent.trim();
        const b = right.children[index].textContent.trim();
        const aNum = Number(a);
        const bNum = Number(b);
        const comparison = Number.isFinite(aNum) && Number.isFinite(bNum)
          ? aNum - bNum
          : a.localeCompare(b);
        return direction === "asc" ? comparison : -comparison;
      }});
      rows.forEach((row) => tbody.appendChild(row));
    }});
  }});
  applyQuery();
}})();
</script>
"""


def _next_token_browser_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  const dataNode = document.getElementById("{viz_id}-data");
  if (!root || !dataNode) return;
  const data = JSON.parse(dataNode.textContent);
  const positionSelect = root.querySelector('[data-filter="position"]');
  const metricSelect = root.querySelector('[data-filter="metric"]');
  const readout = root.querySelector('[data-role="readout"]');
  const metricHead = root.querySelector('[data-role="metric-head"]');
  const tbody = root.querySelector('[data-role="predictions"] tbody');
  function formatValue(value, metric) {{
    if (metric === "prob") return Number(value).toPrecision(5);
    return Number(value).toPrecision(6);
  }}
  function render() {{
    const position = data.positions[Number(positionSelect.value)];
    const metric = metricSelect.value;
    metricHead.textContent = metric;
    tbody.innerHTML = "";
    position.predictions.forEach((prediction) => {{
      const tr = document.createElement("tr");
      if (prediction.is_target) tr.classList.add("safelens-target-row");
      const cells = [
        prediction.rank,
        prediction.token,
        prediction.token_id,
        formatValue(prediction[metric], metric),
        prediction.is_target ? "yes" : "",
      ];
      cells.forEach((value) => {{
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      }});
      tbody.appendChild(tr);
    }});
    if (readout) {{
      readout.textContent =
        `position ${{position.position}} predicts "${{position.target_token}}" ` +
        `(rank ${{position.target_rank}}, log_prob ` +
        `${{Number(position.target_log_prob).toPrecision(6)}})`;
    }}
  }}
  positionSelect.addEventListener("change", render);
  metricSelect.addEventListener("change", render);
  render();
}})();
</script>
"""


def _topk_token_browser_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  if (!root) return;
  const rows = Array.from(root.querySelectorAll("tr[data-row]"));
  const sampleSelect = root.querySelector('[data-filter="sample"]');
  const layerSelect = root.querySelector('[data-filter="layer"]');
  const kindSelect = root.querySelector('[data-filter="kind"]');
  const queryInput = root.querySelector('[data-filter="query"]');
  function applyFilters() {{
    const sample = sampleSelect.value;
    const layer = layerSelect.value;
    const kind = kindSelect.value;
    const query = queryInput.value.toLowerCase();
    const sampleLabel = sampleSelect.options[sampleSelect.selectedIndex].text;
    const layerLabel = layerSelect.options[layerSelect.selectedIndex].text;
    rows.forEach((row) => {{
      const sampleMatch = sample === "__all__" || row.dataset.sample === sampleLabel;
      const layerMatch = layer === "__all__" || row.dataset.layer === layerLabel;
      const queryMatch = !query || row.dataset.rowText.includes(query);
      row.classList.toggle("safelens-hidden", !(sampleMatch && layerMatch && queryMatch));
      row.children[3].classList.toggle("safelens-hidden", kind === "bottom");
      row.children[4].classList.toggle("safelens-hidden", kind === "top");
    }});
  }}
  [sampleSelect, layerSelect, kindSelect].forEach((select) => {{
    select.addEventListener("change", applyFilters);
  }});
  queryInput.addEventListener("input", applyFilters);
  applyFilters();
}})();
</script>
"""


def _topk_sample_browser_script(viz_id: str) -> str:
    return f"""
<script>
(function() {{
  const root = document.getElementById("{viz_id}");
  if (!root) return;
  const rows = Array.from(root.querySelectorAll("tr[data-row]"));
  const layerSelect = root.querySelector('[data-filter="layer"]');
  const neuronSelect = root.querySelector('[data-filter="neuron"]');
  const queryInput = root.querySelector('[data-filter="query"]');
  function applyFilters() {{
    const layer = layerSelect.value;
    const neuron = neuronSelect.value;
    const query = queryInput.value.toLowerCase();
    const layerLabel = layerSelect.options[layerSelect.selectedIndex].text;
    const neuronLabel = neuronSelect.options[neuronSelect.selectedIndex].text;
    rows.forEach((row) => {{
      const layerMatch = layer === "__all__" || row.dataset.layer === layerLabel;
      const neuronMatch = neuron === "__all__" || row.dataset.neuron === neuronLabel;
      const queryMatch = !query || row.dataset.rowText.includes(query);
      row.classList.toggle("safelens-hidden", !(layerMatch && neuronMatch && queryMatch));
    }});
  }}
  [layerSelect, neuronSelect].forEach((select) => {{
    select.addEventListener("change", applyFilters);
  }});
  queryInput.addEventListener("input", applyFilters);
  applyFilters();
}})();
</script>
"""


def _select_attention_matrix(
    pattern: Any,
    *,
    batch_index: int,
    head: int | None,
) -> list[list[float]]:
    data = _to_nested(pattern)
    shape = _shape(data)
    if len(shape) == 2:
        return _as_2d_numbers(data)
    if len(shape) == 3:
        head_index = 0 if head is None else head
        if head_index < 0 or head_index >= shape[0]:
            raise ValueError("head is outside the attention head dimension.")
        return _as_2d_numbers(data[head_index])
    if len(shape) == 4:
        if batch_index < 0 or batch_index >= shape[0]:
            raise ValueError("batch_index is outside the attention batch dimension.")
        head_index = 0 if head is None else head
        if head_index < 0 or head_index >= shape[1]:
            raise ValueError("head is outside the attention head dimension.")
        return _as_2d_numbers(data[batch_index][head_index])
    raise ValueError("attention pattern must have rank 2, 3, or 4.")


def _attention_browser_matrices(
    attention: Any,
    *,
    batch_labels: Sequence[Any] | None,
    layer_labels: Sequence[Any] | None,
    head_labels: Sequence[Any] | None,
    rank4_axis: str,
) -> tuple[list[list[list[float]]], list[str], tuple[int, ...]]:
    data = _to_nested(attention)
    shape = _shape(data)
    if len(shape) == 2:
        return [_as_2d_numbers(data)], ["attention"], shape
    if len(shape) == 3:
        heads = _labels_or_indices(head_labels, shape[0], "head")
        return [_as_2d_numbers(head_data) for head_data in data], heads, shape
    if len(shape) == 4:
        if rank4_axis == "layer":
            layers = _labels_or_indices(layer_labels, shape[0], "layer")
            heads = _labels_or_indices(head_labels, shape[1], "head")
            matrices = []
            labels = []
            for layer_idx, layer_data in enumerate(data):
                for head_idx, head_data in enumerate(layer_data):
                    matrices.append(_as_2d_numbers(head_data))
                    labels.append(f"{layers[layer_idx]} / {heads[head_idx]}")
            return matrices, labels, shape
        if rank4_axis == "batch":
            batches = _labels_or_indices(batch_labels, shape[0], "batch")
            heads = _labels_or_indices(head_labels, shape[1], "head")
            matrices = []
            labels = []
            for batch_idx, batch_data in enumerate(data):
                for head_idx, head_data in enumerate(batch_data):
                    matrices.append(_as_2d_numbers(head_data))
                    labels.append(f"{batches[batch_idx]} / {heads[head_idx]}")
            return matrices, labels, shape
        raise ValueError('rank4_axis must be either "layer" or "batch".')
    if len(shape) == 5:
        batches = _labels_or_indices(batch_labels, shape[0], "batch")
        layers = _labels_or_indices(layer_labels, shape[1], "layer")
        heads = _labels_or_indices(head_labels, shape[2], "head")
        matrices = []
        labels = []
        for batch_idx, batch_data in enumerate(data):
            for layer_idx, layer_data in enumerate(batch_data):
                for head_idx, head_data in enumerate(layer_data):
                    matrices.append(_as_2d_numbers(head_data))
                    labels.append(f"{batches[batch_idx]} / {layers[layer_idx]} / {heads[head_idx]}")
        return matrices, labels, shape
    raise ValueError("attention browser data must have rank 2, 3, 4, or 5.")


def _as_2d_numbers(values: Any) -> list[list[float]]:
    data = _to_nested(values)
    shape = _shape(data)
    if len(shape) == 0:
        return [[_scalar(data)]]
    if len(shape) == 1:
        return [[_scalar(value) for value in data]]
    if len(shape) != 2:
        raise ValueError(f"expected a rank-1 or rank-2 numeric value, got shape {shape}.")
    rows = [[_scalar(value) for value in row] for row in data]
    if rows:
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError("rank-2 numeric values must be rectangular.")
    return rows


def _to_nested(value: Any) -> Any:
    if hasattr(value, "detach") and callable(value.detach):
        value = value.detach()
    if hasattr(value, "cpu") and callable(value.cpu):
        value = value.cpu()
    if hasattr(value, "tolist") and callable(value.tolist):
        return value.tolist()
    if isinstance(value, Mapping):
        return {key: _to_nested(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return value
    if isinstance(value, Sequence):
        return [_to_nested(item) for item in value]
    return value


def _flatten_nested(value: Any) -> list[Any]:
    if isinstance(value, Mapping):
        items = value.values()
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = value
    else:
        return [value]
    flattened = []
    for item in items:
        flattened.extend(_flatten_nested(item))
    return flattened


def _maybe_remove_single_batch(value: Any) -> Any:
    data = _to_nested(value)
    shape = _shape(data)
    if len(shape) == 3 and shape[0] == 1:
        return data[0]
    return data


def _flatten_rank_one(value: Any) -> list[float]:
    data = _to_nested(value)
    shape = _shape(data)
    if len(shape) == 2 and shape[0] == 1:
        data = data[0]
        shape = _shape(data)
    if len(shape) != 1:
        raise ValueError(
            f"expected a rank-1 value or batch size one rank-2 value, got shape {shape}."
        )
    return [_scalar(item) for item in data]


def _normalize_text_neuron_inputs(
    tokens: Sequence[Any],
    activations: Any,
) -> tuple[list[list[str]], list[list[list[list[float]]]], tuple[int, int, int]]:
    token_samples = _token_samples(tokens)
    data = _to_nested(activations)
    shape = _shape(data)
    if len(shape) == 3:
        activation_samples = [data]
    elif len(shape) == 4:
        activation_samples = data
    else:
        raise ValueError(
            "activations must have shape [token, layer, neuron] or [sample, token, layer, neuron]."
        )
    if len(token_samples) != len(activation_samples):
        raise ValueError("tokens and activations must contain the same number of samples.")
    sample_shape = _shape(activation_samples[0])
    if len(sample_shape) != 3:
        raise ValueError("each activation sample must have shape [token, layer, neuron].")
    layer_count = sample_shape[1]
    neuron_count = sample_shape[2]

    normalized = []
    max_token_count = 0
    for token_list, sample_acts in zip(token_samples, activation_samples, strict=True):
        current_shape = _shape(sample_acts)
        if len(current_shape) != 3:
            raise ValueError("each activation sample must have shape [token, layer, neuron].")
        if current_shape[1] != layer_count or current_shape[2] != neuron_count:
            raise ValueError(
                "all activation samples must have the same layer and neuron dimensions."
            )
        if len(token_list) != current_shape[0]:
            raise ValueError("tokens length must match each activation sample's token dimension.")
        max_token_count = max(max_token_count, current_shape[0])
        sample_values = []
        for token_values in sample_acts:
            if not isinstance(token_values, Sequence) or isinstance(token_values, (str, bytes)):
                raise ValueError("each token activation must contain layer values.")
            if len(token_values) != layer_count:
                raise ValueError("all token activations must have the same layer dimension.")
            layer_values_list = []
            for layer_values in token_values:
                if not isinstance(layer_values, Sequence) or isinstance(layer_values, (str, bytes)):
                    raise ValueError("each layer activation must contain neuron values.")
                if len(layer_values) != neuron_count:
                    raise ValueError("all layer activations must have the same neuron dimension.")
                layer_values_list.append([_scalar(value) for value in layer_values])
            sample_values.append(layer_values_list)
        normalized.append(sample_values)
    return token_samples, normalized, (max_token_count, layer_count, neuron_count)


def _labels_or_indices(
    labels: Sequence[Any] | None,
    size: int,
    name: str,
) -> list[str]:
    if labels is None:
        return [str(idx) for idx in range(size)]
    label_list = [str(label) for label in labels]
    if len(label_list) != size:
        raise ValueError(f"{name}_labels length must match the {name} dimension.")
    return label_list


def _select_control(
    viz_id: str,
    name: str,
    labels: Sequence[str],
    *,
    include_all: bool = False,
) -> str:
    options = []
    if include_all:
        options.append('<option value="__all__">all</option>')
    options.extend(
        f'<option value="{idx}">{escape(label)}</option>' for idx, label in enumerate(labels)
    )
    safe_name = _data_attr_name(name) or "value"
    return (
        f'<label class="safelens-control-label" for="{viz_id}-{safe_name}">'
        f"{escape(name)} "
        f'<select id="{viz_id}-{safe_name}" class="safelens-select" '
        f'data-filter="{safe_name}">{"".join(options)}</select></label>'
    )


def _interactive_table(
    viz_id: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    *,
    include_filter: bool = False,
) -> str:
    controls = ""
    if include_filter:
        controls = (
            '<div class="safelens-controls">'
            '<input class="safelens-input" data-filter="query" placeholder="filter" />'
            "</div>"
        )
    header_html = (
        "<tr>"
        + "".join(
            f'<th data-sort-index="{idx}">{escape(header)}</th>'
            for idx, header in enumerate(headers)
        )
        + "</tr>"
    )
    body_rows = []
    attr_names = [_data_attr_name(header) for header in headers]
    for row in rows:
        row_text = " ".join(_display_value(value) for value in row).lower()
        attrs = [
            'data-row="1"',
            f'data-row-text="{escape(row_text, quote=True)}"',
        ]
        attrs.extend(
            f'data-{attr}="{escape(_display_value(value), quote=True)}"'
            for attr, value in zip(attr_names, row, strict=False)
        )
        cells = "".join(f"<td>{escape(_display_value(value))}</td>" for value in row)
        body_rows.append(f"<tr {' '.join(attrs)}>{cells}</tr>")
    table = (
        f'<table class="safelens-summary safelens-interactive-table" '
        f'data-role="table" id="{viz_id}-table">'
        f"<thead>{header_html}</thead><tbody>{''.join(body_rows)}</tbody></table>"
    )
    return controls + table + _table_filter_sort_script(viz_id)


def _bar_table(
    viz_id: str,
    rows: Sequence[tuple[str, float]],
    *,
    min_value: float,
    max_value: float,
    include_filter: bool,
    value_header: str = "value",
) -> str:
    controls = ""
    if include_filter:
        controls = (
            '<div class="safelens-controls">'
            '<input class="safelens-input" data-filter="query" placeholder="filter" />'
            "</div>"
        )
    scale = max(abs(min_value), abs(max_value)) or 1.0
    body_rows = []
    for label, value in rows:
        pct = min(100.0, abs(value) / scale * 100.0)
        color = "#2563eb" if value >= 0 else "#dc2626"
        row_text = f"{label} {value:.12g}".lower()
        body_rows.append(
            '<tr data-row="1" '
            f'data-row-text="{escape(row_text, quote=True)}" '
            f'data-label="{escape(label, quote=True)}" '
            f'data-value="{value:.12g}">'
            f"<td>{escape(label)}</td>"
            f"<td>{value:.6g}</td>"
            "<td>"
            f'<div class="safelens-bar" style="width:{pct:.2f}%;background:{color};"></div>'
            "</td></tr>"
        )
    table = (
        f'<table class="safelens-summary safelens-interactive-table" '
        f'data-role="table" id="{viz_id}-table">'
        "<thead><tr>"
        '<th data-sort-index="0">label</th>'
        f'<th data-sort-index="1">{escape(value_header)}</th>'
        "<th>bar</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )
    return controls + table + _table_filter_sort_script(viz_id)


def _data_attr_name(name: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in name).strip("-")


def _topk_token_rows(
    tokens: Sequence[Any],
    activations: Any,
    *,
    max_k: int,
    sample_labels: Sequence[Any] | None,
    layer_labels: Sequence[Any] | None,
    neuron_labels: Sequence[Any] | None,
) -> tuple[list[list[Any]], dict[str, Any]]:
    if max_k < 1:
        raise ValueError("max_k must be at least 1.")
    token_samples = _token_samples(tokens)
    data = _to_nested(activations)
    shape = _shape(data)
    if len(shape) == 3:
        activation_samples = [data]
    elif len(shape) == 4:
        activation_samples = data
    else:
        raise ValueError(
            "activations must have shape [layer, token, neuron] or [sample, layer, token, neuron]."
        )
    if len(token_samples) != len(activation_samples):
        raise ValueError("tokens and activations must contain the same number of samples.")

    sample_names = _labels_or_indices(sample_labels, len(activation_samples), "sample")
    sample_shape = _shape(activation_samples[0])
    if len(sample_shape) != 3:
        raise ValueError("each activation sample must have shape [layer, token, neuron].")
    layer_names = _labels_or_indices(layer_labels, sample_shape[0], "layer")
    provided_neuron_names = [str(label) for label in neuron_labels] if neuron_labels else None
    max_neuron_count = 0

    rows = []
    for sample_name, token_list, sample_acts in zip(
        sample_names,
        token_samples,
        activation_samples,
        strict=True,
    ):
        current_shape = _shape(sample_acts)
        if len(current_shape) != 3:
            raise ValueError("each activation sample must have shape [layer, token, neuron].")
        if current_shape[0] != sample_shape[0]:
            raise ValueError("all activation samples must have the same layer dimension.")
        if not token_list:
            raise ValueError("each sample must contain at least one token.")
        sample_neuron_count = current_shape[2]
        if provided_neuron_names is not None and len(provided_neuron_names) != sample_neuron_count:
            raise ValueError("neuron_labels length must match each sample's neuron dimension.")
        neuron_names = (
            provided_neuron_names
            if provided_neuron_names is not None
            else [str(idx) for idx in range(sample_neuron_count)]
        )
        max_neuron_count = max(max_neuron_count, sample_neuron_count)
        limit = min(max_k, len(token_list))
        for layer_idx in range(current_shape[0]):
            layer_acts = sample_acts[layer_idx]
            if not isinstance(layer_acts, Sequence) or isinstance(layer_acts, (str, bytes)):
                raise ValueError("each layer activation must contain token values.")
            if len(layer_acts) != len(token_list):
                raise ValueError(
                    "tokens length must match each activation sample's token dimension."
                )
            for token_values in layer_acts:
                if not isinstance(token_values, Sequence) or isinstance(token_values, (str, bytes)):
                    raise ValueError("each token activation must contain neuron values.")
                if len(token_values) != sample_neuron_count:
                    raise ValueError(
                        "all token activations in a sample must have the same neuron dimension."
                    )
            for neuron_idx in range(sample_neuron_count):
                token_scores = [
                    (token_idx, _scalar(sample_acts[layer_idx][token_idx][neuron_idx]))
                    for token_idx in range(len(token_list))
                ]
                top = sorted(token_scores, key=lambda item: item[1], reverse=True)[:limit]
                bottom = sorted(token_scores, key=lambda item: item[1])[:limit]
                rows.append(
                    [
                        sample_name,
                        layer_names[layer_idx],
                        neuron_names[neuron_idx],
                        "; ".join(f"{token_list[idx]}={value:.4g}" for idx, value in top),
                        "; ".join(f"{token_list[idx]}={value:.4g}" for idx, value in bottom),
                    ]
                )
    return rows, {
        "tokens": token_samples,
        "sample_labels": sample_names,
        "layer_labels": layer_names,
        "neuron_labels": provided_neuron_names
        if provided_neuron_names is not None
        else [str(idx) for idx in range(max_neuron_count)],
    }


def _topk_sample_rows(
    tokens: Any,
    activations: Any,
    *,
    layer_labels: Sequence[Any] | None,
    neuron_labels: Sequence[Any] | None,
) -> tuple[list[list[Any]], dict[str, Any]]:
    token_data = _to_nested(tokens)
    activation_data = _to_nested(activations)
    shape = _shape(activation_data)
    if len(shape) != 4:
        raise ValueError("activations must have shape [layer, neuron, sample, token].")
    layer_names = _labels_or_indices(layer_labels, shape[0], "layer")
    neuron_names = _labels_or_indices(neuron_labels, shape[1], "neuron")

    rows = []
    if not isinstance(token_data, Sequence) or isinstance(token_data, (str, bytes)):
        raise ValueError("tokens must have shape [layer, neuron, sample, token].")
    if len(token_data) != shape[0]:
        raise ValueError("tokens must match activations on the layer dimension.")
    for layer_idx in range(shape[0]):
        layer_activations = activation_data[layer_idx]
        layer_tokens = token_data[layer_idx]
        if not isinstance(layer_activations, Sequence) or isinstance(
            layer_activations, (str, bytes)
        ):
            raise ValueError("each activation layer must contain neuron values.")
        if not isinstance(layer_tokens, Sequence) or isinstance(layer_tokens, (str, bytes)):
            raise ValueError("each token layer must contain neuron token values.")
        if len(layer_activations) != shape[1] or len(layer_tokens) != shape[1]:
            raise ValueError("tokens and activations must match on the neuron dimension.")
        for neuron_idx in range(shape[1]):
            neuron_activations = layer_activations[neuron_idx]
            neuron_tokens = layer_tokens[neuron_idx]
            if not isinstance(neuron_activations, Sequence) or isinstance(
                neuron_activations, (str, bytes)
            ):
                raise ValueError("each activation neuron must contain sample values.")
            if not isinstance(neuron_tokens, Sequence) or isinstance(neuron_tokens, (str, bytes)):
                raise ValueError("each token neuron must contain sample token values.")
            if len(neuron_activations) != shape[2] or len(neuron_tokens) != shape[2]:
                raise ValueError("tokens and activations must match on the sample dimension.")
            sample_scores = []
            for sample_idx in range(shape[2]):
                sample_values_raw = neuron_activations[sample_idx]
                sample_tokens_raw = neuron_tokens[sample_idx]
                if not isinstance(sample_values_raw, Sequence) or isinstance(
                    sample_values_raw, (str, bytes)
                ):
                    raise ValueError("each activation sample must contain token values.")
                if not isinstance(sample_tokens_raw, Sequence) or isinstance(
                    sample_tokens_raw, (str, bytes)
                ):
                    raise ValueError("each token sample must contain token strings.")
                sample_values = [_scalar(value) for value in sample_values_raw]
                if not sample_values:
                    raise ValueError("sample token dimension must be non-empty.")
                sample_tokens = [str(token) for token in sample_tokens_raw]
                if len(sample_tokens) != len(sample_values):
                    raise ValueError("tokens and activations must match on the token dimension.")
                max_value = max(sample_values)
                max_token = sample_tokens[sample_values.index(max_value)]
                sample_scores.append((sample_idx, max_token, max_value))
            for rank, (sample_idx, max_token, max_value) in enumerate(
                sorted(sample_scores, key=lambda item: item[2], reverse=True),
                start=1,
            ):
                rows.append(
                    [
                        layer_names[layer_idx],
                        neuron_names[neuron_idx],
                        rank,
                        sample_idx,
                        max_token,
                        max_value,
                    ]
                )
    return rows, {"layer_labels": layer_names, "neuron_labels": neuron_names}


def _token_samples(tokens: Sequence[Any]) -> list[list[str]]:
    data = _to_nested(tokens)
    if not isinstance(data, Sequence) or isinstance(data, (str, bytes)):
        raise ValueError("tokens must be a sequence.")
    if data and isinstance(data[0], Sequence) and not isinstance(data[0], (str, bytes)):
        return [[str(token) for token in sample] for sample in data]
    return [[str(token) for token in data]]


def _log_softmax(values: Sequence[float]) -> list[float]:
    if not values:
        raise ValueError("logit rows must be non-empty.")
    max_value = max(values)
    log_denom = max_value + math.log(sum(math.exp(value - max_value) for value in values))
    return [value - log_denom for value in values]


def _shape(value: Any) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return ()
    if not value:
        return (0,)
    return (len(value), *_shape(value[0]))


def _scalar(value: Any) -> float:
    if hasattr(value, "item") and callable(value.item):
        value = value.item()
    scalar = float(value)
    if not math.isfinite(scalar):
        raise ValueError("visualization values must be finite numbers.")
    return scalar


def _value_range(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        spread = abs(min_value) if min_value else 1.0
        return min_value - spread, max_value + spread
    return min_value, max_value


def _normalized_percent(value: float, min_value: float, max_value: float) -> float:
    denominator = max_value - min_value
    if denominator == 0:
        return 100.0
    return max(0.0, min(100.0, 100.0 * (value - min_value) / denominator))


def _value_color(
    value: float,
    min_value: float,
    max_value: float,
    *,
    color: str,
) -> tuple[str, str]:
    if color == "blue":
        denominator = max_value - min_value or 1.0
        intensity = max(0.0, min(1.0, (value - min_value) / denominator))
        red = int(248 - 211 * intensity)
        green = int(250 - 151 * intensity)
        blue = int(252 - 17 * intensity)
    else:
        midpoint = 0.0 if min_value <= 0.0 <= max_value else (min_value + max_value) / 2.0
        if value >= midpoint:
            denominator = max_value - midpoint or 1.0
            intensity = min(1.0, (value - midpoint) / denominator)
            red = int(255 - 30 * intensity)
            green = int(255 - 226 * intensity)
            blue = int(255 - 109 * intensity)
        else:
            denominator = midpoint - min_value or 1.0
            intensity = min(1.0, (midpoint - value) / denominator)
            red = int(255 - 218 * intensity)
            green = int(255 - 156 * intensity)
            blue = int(255 - 20 * intensity)
    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255.0
    foreground = "#111827" if luminance > 0.58 else "#ffffff"
    return f"rgb({red},{green},{blue})", foreground


def _component_title(base: str, *, layer: int | None = None, head: int | None = None) -> str:
    parts = [base]
    if layer is not None:
        parts.append(f"layer {layer}")
    if head is not None:
        parts.append(f"head {head}")
    return " - ".join(parts)


def _legend(min_value: float, max_value: float, *, color: str = "red_blue") -> str:
    gradient_class = (
        "safelens-legend-gradient safelens-legend-gradient-blue"
        if color == "blue"
        else "safelens-legend-gradient safelens-legend-gradient-red-blue"
    )
    return (
        '<div class="safelens-legend">'
        f"<span>{min_value:.4g}</span>"
        f'<span class="{gradient_class}"></span>'
        f"<span>{max_value:.4g}</span></div>"
    )


def _wrap_panel(kind: str, title: str | None, body: str) -> str:
    title_html = f"<h3>{escape(title)}</h3>" if title else ""
    return (
        "<style>"
        ".safelens-viz{font-family:Inter,ui-sans-serif,system-ui,sans-serif;"
        "line-height:1.35;color:#111827;background:#ffffff;border:1px solid #e5e7eb;"
        "border-radius:6px;padding:0.8rem;margin:0.75rem 0;box-sizing:border-box;}"
        ".safelens-viz *{box-sizing:border-box;}"
        ".safelens-viz h3{font-size:1rem;font-weight:650;margin:0 0 0.65rem 0;color:#0f172a;}"
        ".safelens-controls{display:flex;flex-wrap:wrap;gap:0.45rem;margin:0.4rem 0 0.65rem 0;}"
        ".safelens-control-label{display:inline-flex;align-items:center;gap:0.35rem;"
        "font-size:0.78rem;color:#475569;}"
        ".safelens-control-button{border:1px solid #d9dee8;background:#ffffff;"
        "color:#111827;border-radius:5px;padding:0.3rem 0.5rem;font-size:0.78rem;"
        "cursor:pointer;}"
        ".safelens-control-button:hover,.safelens-control-button.is-active{"
        "background:#0f172a;color:#ffffff;border-color:#0f172a;}"
        ".safelens-select,.safelens-input{border:1px solid #d9dee8;border-radius:5px;"
        "padding:0.3rem 0.42rem;font-size:0.8rem;background:#ffffff;color:#111827;}"
        ".safelens-hidden{display:none!important;}"
        ".safelens-token-strip{display:flex;flex-wrap:wrap;gap:0.08rem;margin:0.35rem 0;}"
        ".safelens-token{padding:0.15rem 0.22rem;margin:0.08rem;border-radius:4px;"
        "display:inline-block;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;}"
        ".safelens-live-token{transition:background 120ms ease,color 120ms ease;}"
        ".safelens-heatmap-scroller{overflow:auto;background:#ffffff;border:1px solid #edf0f5;"
        "border-radius:6px;padding:0.35rem;max-width:100%;width:max-content;margin:0 auto;}"
        ".safelens-heatmap-svg{display:block;background:#ffffff;width:auto;height:auto;"
        "max-width:none;margin:0 auto;}"
        ".safelens-heatmap-background{fill:#ffffff;}"
        ".safelens-heatmap-label{font-size:11px;fill:#334155;"
        "font-family:ui-monospace,SFMono-Regular,Consolas,monospace;}"
        ".safelens-axis-label{font-size:12px;fill:#475569;font-weight:600;}"
        ".safelens-heatmap-value{font-size:10px;font-weight:650;pointer-events:none;"
        "font-family:ui-monospace,SFMono-Regular,Consolas,monospace;}"
        ".safelens-heatmap-cell{cursor:crosshair;stroke:#ffffff;stroke-width:1;"
        "transition:stroke 80ms ease,stroke-width 80ms ease;}"
        ".safelens-heatmap-cell.safelens-row-focus,.safelens-heatmap-cell.safelens-col-focus{"
        "stroke:#64748b;stroke-width:1.6;}"
        ".safelens-heatmap-cell.safelens-cell-focus{stroke:#0f172a;stroke-width:2.4;}"
        ".safelens-axis{font-size:0.78rem;color:#4b5563;margin:0.25rem 0;}"
        ".safelens-x-axis{margin-left:2.4rem;}"
        ".safelens-focus-readout{min-height:1rem;font-size:0.78rem;color:#374151;"
        "margin:0.3rem 0;}"
        ".safelens-legend{display:grid;grid-template-columns:auto minmax(7rem,14rem) auto;"
        "align-items:center;gap:0.45rem;font-size:0.75rem;color:#4b5563;margin-top:0.45rem;}"
        ".safelens-legend-gradient{display:block;height:0.45rem;border-radius:999px;"
        "border:1px solid #e5e7eb;}"
        ".safelens-legend-gradient-blue{background:linear-gradient(90deg,#f8fafc,#60a5fa,#2563eb);}"
        ".safelens-legend-gradient-red-blue{background:linear-gradient(90deg,#2563eb,#ffffff,#e11d48);}"
        ".safelens-head-strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(108px,1fr));"
        "gap:0.55rem;margin:0.25rem 0 0.75rem 0;}"
        ".safelens-head-thumb{display:flex;flex-direction:column;gap:0.35rem;text-align:left;"
        "border:1px solid #e5e7eb;background:#ffffff;border-radius:6px;padding:0.4rem;"
        "cursor:pointer;color:#111827;}"
        ".safelens-head-thumb:hover,.safelens-head-thumb.is-active{border-color:#2563eb;"
        "box-shadow:0 0 0 2px rgba(37,99,235,0.12);}"
        ".safelens-head-thumb-title{font-size:0.76rem;font-weight:650;white-space:nowrap;"
        "overflow:hidden;text-overflow:ellipsis;}"
        ".safelens-mini-heatmap{width:100%;height:auto;display:block;background:#ffffff;}"
        ".safelens-head-detail-title{font-size:0.86rem;font-weight:650;color:#0f172a;"
        "margin:0 0 0.35rem 0;}"
        ".safelens-cv-attention{background:#ffffff;}"
        ".safelens-cv-layout{display:grid;grid-template-columns:max-content minmax(18rem,1fr);"
        "gap:1.25rem;align-items:start;}"
        ".safelens-cv-main{min-width:0;}"
        ".safelens-cv-selector{min-width:14rem;}"
        ".safelens-cv-section-title{font-size:0.86rem;font-weight:700;color:#111827;"
        "margin:0 0 0.45rem 0;}"
        ".safelens-cv-section-title span{font-weight:400;color:#64748b;}"
        ".safelens-cv-image-frame{display:inline-block;background:#ffffff;border:1px solid #d9dee8;"
        "padding:0.3rem;line-height:0;max-width:100%;overflow:auto;}"
        ".safelens-cv-main-image,.safelens-cv-attention-image{display:block;background:#ffffff;"
        "image-rendering:pixelated;shape-rendering:crispEdges;}"
        ".safelens-cv-cell{stroke:#ffffff;stroke-width:0.25;cursor:crosshair;}"
        ".safelens-cv-cell.is-token-focused{stroke:rgba(15,23,42,0.62);stroke-width:0.8;}"
        ".safelens-cv-head-grid{display:flex;flex-wrap:wrap;gap:0.55rem;align-items:flex-start;}"
        ".safelens-cv-head-button{position:relative;border:1px solid #d9dee8;background:#ffffff;"
        "padding:0.25rem;margin:0;cursor:pointer;line-height:0;color:#111827;}"
        ".safelens-cv-head-button:hover,.safelens-cv-head-button.is-active{border-color:var(--safelens-head-color,#1d4ed8);"
        "box-shadow:0 0 4px 3px var(--safelens-head-glow,rgba(29,78,216,0.22));}"
        ".safelens-cv-head-label{display:block;font-size:0.7rem;font-weight:700;line-height:1.1;"
        "margin-bottom:0.2rem;color:#111827;}"
        ".safelens-cv-head-badge{position:absolute;top:0;right:0;z-index:1;max-width:90%;"
        "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#ffffff;font-size:0.68rem;"
        "font-weight:700;line-height:1.1;padding:0.12rem 0.2rem;}"
        ".safelens-cv-token-panel{margin-top:0.85rem;}"
        ".safelens-cv-token-strip{display:flex;flex-wrap:wrap;align-items:center;gap:0;margin-top:0.4rem;}"
        ".safelens-cv-token{border:0;border-right:1px solid #d9dee8;margin:0 0 0.2rem 0;"
        "padding:0.22rem 0.34rem;font-size:0.82rem;"
        "font-family:ui-monospace,SFMono-Regular,Consolas,monospace;"
        "cursor:pointer;min-height:1.55rem;}"
        ".safelens-cv-token:hover,.safelens-cv-token.is-active{"
        "box-shadow:0 0 0 2px rgba(15,23,42,0.22);"
        "position:relative;z-index:1;}"
        "@media(max-width:760px){.safelens-cv-layout{grid-template-columns:1fr;}.safelens-cv-selector{min-width:0;}}"
        ".safelens-summary{border-collapse:collapse;font-size:0.86rem;margin:0.35rem 0;}"
        ".safelens-summary th,.safelens-summary td{border:1px solid #e5e7eb;"
        "padding:0.35rem 0.5rem;text-align:left;vertical-align:top;}"
        ".safelens-summary th{background:#ffffff;color:#334155;font-weight:650;}"
        ".safelens-line-table{border-collapse:collapse;font-size:0.82rem;margin:0.35rem 0;}"
        ".safelens-line-table th,.safelens-line-table td{border:1px solid #e5e7eb;"
        "min-width:3.2rem;padding:0.35rem;text-align:left;vertical-align:middle;}"
        ".safelens-line-table th{background:#ffffff;color:#334155;}"
        ".safelens-bar{height:0.45rem;background:#2563eb;border-radius:2px;margin-bottom:0.15rem;}"
        ".safelens-track{margin:0.4rem 0;}"
        "details.safelens-details{margin:0.4rem 0;}"
        "details.safelens-details pre{white-space:pre-wrap;background:#ffffff;"
        "border:1px solid #e5e7eb;padding:0.5rem;}"
        "</style>"
        f'<div class="safelens-viz safelens-viz-{escape(kind)}">{title_html}{body}</div>'
    )


def _summary_table(rows: Any) -> str:
    html_rows = []
    for key, value in rows:
        html_rows.append(
            f"<tr><th>{escape(str(key))}</th><td>{escape(_display_value(value))}</td></tr>"
        )
    return f'<table class="safelens-summary">{"".join(html_rows)}</table>'


def _html_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    header_html = "<tr>" + "".join(f"<th>{escape(header)}</th>" for header in headers) + "</tr>"
    row_html = []
    for row in rows:
        row_html.append(
            "<tr>" + "".join(f"<td>{escape(_display_value(value))}</td>" for value in row) + "</tr>"
        )
    return f'<table class="safelens-summary">{header_html}{"".join(row_html)}</table>'


def _details_block(title: str, payload: Any) -> str:
    if not payload:
        return ""
    import json

    serialized = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    return (
        '<details class="safelens-details"><summary>'
        f"{escape(title)}</summary><pre>{escape(serialized)}</pre></details>"
    )


def _display_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, (list, tuple, dict)):
        return str(value)
    if value is None:
        return ""
    return str(value)


def _display_shape(value: Any) -> str:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return "x".join(map(str, tuple(shape)))
    return "x".join(map(str, _shape(_to_nested(value))))


def _circuitsvis_import_error(component: str) -> ImportError:
    return ImportError(
        "circuitsvis is not installed. Install SafeLens with the optional "
        f"visualization dependencies to use the native CircuitsVis {component!r} bridge, "
        "or use the dependency-light SafeLens.viz fallback functions."
    )
