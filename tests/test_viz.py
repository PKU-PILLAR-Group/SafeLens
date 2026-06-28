from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

import SafeLens
from SafeLens.core.base import (
    AttributionResult,
    MonitoringSignal,
    RunReport,
    SafetyReport,
    TokenAttribution,
)
from SafeLens.nla import NLAResult
from SafeLens.viz import (
    Visualization,
    colored_tokens,
    colored_tokens_multi,
    export_html,
    plot_activation_cache_browser,
    plot_activation_patching_browser,
    plot_activation_patching_grid,
    plot_attention_browser,
    plot_attention_heads,
    plot_attention_pattern,
    plot_attention_patterns,
    plot_bar,
    plot_cache_summary,
    plot_component_scores,
    plot_head_scores,
    plot_histogram,
    plot_line,
    plot_logit_lens,
    plot_mlp_component_browser,
    plot_mlp_logit_contribution_browser,
    plot_mlp_neuron_topk_browser,
    plot_mlp_output_direction_viewer,
    plot_model_performance,
    plot_neuron_activations,
    plot_next_token_browser,
    plot_nla_fidelity_heatmap,
    plot_nla_result_browser,
    plot_scatter,
    plot_text_neuron_activations,
    plot_text_neuron_browser,
    plot_token_log_probs,
    plot_topk_samples,
    plot_topk_samples_browser,
    plot_topk_tokens,
    plot_topk_tokens_browser,
    render_run_report,
    render_safety_report,
    to_circuitsvis_colored_tokens,
    to_circuitsvis_model_performance,
)


def assert_visualization(viz: Visualization, expected: str) -> None:
    assert expected in viz.html
    assert viz._repr_html_() == viz.html
    assert '<div class="safelens-viz' in viz.to_html()
    assert "<!doctype html>" in viz.to_html(full_document=True)


def test_colored_tokens_and_multi_track_export_html(tmp_path: Path) -> None:
    viz = colored_tokens(["A", "<B>"], [0.1, -0.2], labels=["low", "high"])
    assert_visualization(viz, "&lt;B&gt;")
    assert viz.data["values"] == [0.1, -0.2]

    multi = colored_tokens_multi(["A", "B"], [[1, -1], [0.5, 0.0]], labels=["pos", "neg"])
    assert_visualization(multi, "pos")
    assert multi.data["labels"] == ["pos", "neg"]
    assert 'data-track="1"' in multi.html
    assert "safelens-interactive-tokens" in multi.html

    output_path = export_html(viz, tmp_path / "tokens.html")
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").startswith("<!doctype html>")

    with pytest.raises(ValueError, match="rectangular"):
        colored_tokens_multi(["A", "B"], [[1.0], [0.5, 0.0]])

    with pytest.raises(ValueError, match="finite"):
        colored_tokens(["A"], [float("nan")])


def test_attention_visualizations_accept_rank_variants() -> None:
    pattern = [[0.8, 0.2], [0.1, 0.9]]
    viz = plot_attention_pattern(pattern, tokens=["A", "B"], layer=0, head=1)
    assert_visualization(viz, "Attention Pattern")
    assert viz.data["matrix"] == pattern

    heads = plot_attention_heads(
        [[[0.8, 0.2], [0.1, 0.9]], [[0.5, 0.5], [0.4, 0.6]]],
        tokens=["A", "B"],
        head_names=["copy", "previous"],
    )
    assert_visualization(heads, "copy")
    assert len(heads.data["heads"]) == 2
    assert 'data-head="1"' in heads.html
    assert "safelens-attention-head-browser" in heads.html

    with pytest.raises(ValueError, match="tokens length"):
        plot_attention_pattern(pattern, tokens=["A"])
    with pytest.raises(ValueError, match="head"):
        plot_attention_pattern([pattern], head=2)
    with pytest.raises(ValueError, match="batch_index"):
        plot_attention_heads([[pattern]], batch_index=2)


def test_heatmap_line_scatter_and_component_plots() -> None:
    patch = plot_activation_patching_grid(
        [[1.0, -1.0], [0.5, 0.25]],
        layers=[0, 1],
        positions=[0, 1],
    )
    assert_visualization(patch, "Activation Patching")

    patch_browser = plot_activation_patching_browser(
        [
            [[1.0, -1.0], [0.5, 0.25]],
            [[0.0, 0.1], [0.2, 0.3]],
        ],
        layers=["L0", "L1"],
        positions=["A", "B"],
        slice_labels=["resid_pre", "mlp_out"],
    )
    assert_visualization(patch_browser, "Activation Patching Browser")
    assert 'data-filter="slice"' in patch_browser.html
    assert patch_browser.data["shape"] == (2, 2, 2)

    named_patch_browser = plot_activation_patching_browser(
        [[[1.0, -1.0], [0.5, 0.25]]],
        layers=["L0", "L1"],
        positions=["A", "B"],
        slice_axis_name='component type" onclick="bad',
    )
    assert 'data-filter="component-type--onclick--bad"' in named_patch_browser.html

    head_scores = plot_head_scores([[0.1, 0.2]], layers=["L0"], heads=["H0", "H1"])
    assert_visualization(head_scores, "Head Scores")

    logit_lens = plot_logit_lens([[1.0, 2.0], [3.0, 4.0]], layers=[0, 1], tokens=["A", "B"])
    assert_visualization(logit_lens, "Logit Lens")

    neurons = plot_neuron_activations([[0.1, -0.1], [0.2, 0.3]], tokens=["A", "B"])
    assert_visualization(neurons, "Neuron Activations")

    line = plot_line([[0.0, 1.0], [1.0, 0.0]], x=["a", "b"], series_labels=["up", "down"])
    assert_visualization(line, "Line Plot")

    scatter = plot_scatter([0, 1], [1, 0], labels=["p0", "p1"])
    assert_visualization(scatter, "Scatter Plot")

    bar = plot_bar({"L0H0": 0.2, "L0H1": -0.1}, top_k=2)
    assert_visualization(bar, "Bar Chart")
    assert 'data-filter="query"' in bar.html

    histogram = plot_histogram([[0.0, 0.5], [1.0, 1.5]], bins=2)
    assert_visualization(histogram, "Histogram")
    assert histogram.data["counts"] == [2, 2]

    patterns = plot_attention_patterns(
        [[[0.8, 0.2], [0.1, 0.9]]],
        tokens=["A", "B"],
    )
    assert_visualization(patterns, "Attention Patterns")

    browser = plot_attention_browser(
        [[[[0.8, 0.2], [0.1, 0.9]]]],
        tokens=["A", "B"],
        layer_labels=["L0"],
        head_labels=["H0"],
    )
    assert_visualization(browser, "Attention Browser")
    assert 'data-filter="matrix"' in browser.html
    assert 'data-filter="mode"' in browser.html
    assert browser.data["shape"] == (1, 1, 2, 2)

    cross_browser = plot_attention_browser(
        [[[0.5, 0.3, 0.2], [0.1, 0.7, 0.2]]],
        head_labels=["cross"],
    )
    assert_visualization(cross_browser, "Attention Browser")
    assert cross_browser.data["x_labels"] == ["0", "1", "2"]
    assert cross_browser.data["y_labels"] == ["0", "1"]

    component_scores = plot_component_scores({"L0H0": 0.2, "L0H1": -0.1})
    assert_visualization(component_scores, "Component Scores")

    renamed_component_scores = plot_component_scores(
        {"raw_a": [0.2, 0.4], "raw_b": [-0.1, -0.3]},
        component_names=["L0H0", "L0H1"],
        value_names=["mean", "max"],
    )
    assert renamed_component_scores.data["y_labels"] == ["L0H0", "L0H1"]
    assert renamed_component_scores.data["x_labels"] == ["mean", "max"]
    assert "raw_a" not in renamed_component_scores.html

    cache_summary = plot_cache_summary({"blocks.0.hook_resid_post": [[1.0, 2.0]]})
    assert_visualization(cache_summary, "Activation Cache Summary")
    assert 'data-filter="query"' in cache_summary.html

    cache_browser = plot_activation_cache_browser(
        {
            "layer_0.resid_post": [[[1.0, 2.0], [3.0, 4.0]]],
            "layer_1.resid_post": [[[0.5, 0.25], [0.125, 0.0]]],
            "layer_0.pattern": [[[[1.0, 0.0], [0.0, 1.0]]]],
            ("resid_post", 2): [[[2.0, 1.0], [0.0, -1.0]]],
        },
        keys=["layer_0.resid_post", "layer_1.resid_post", "layer_0.pattern", ("resid_post", 2)],
        y_labels=["A", "B"],
        x_labels=["d0", "d1"],
        x_axis="Residual dimension",
        y_axis="Token",
    )
    assert_visualization(cache_browser, "Activation Cache Browser")
    assert 'data-filter="activation"' in cache_browser.html
    assert "Residual dimension" in cache_browser.html
    assert cache_browser.data["skipped"][0]["key"] == "layer_0.pattern"
    assert "('resid_post', 2)" in cache_browser.data["keys"]


def test_token_log_probs_text_neurons_and_topk_views() -> None:
    log_probs = [
        [-3.0, -0.1, -2.0],
        [-2.0, -3.0, -0.2],
        [-0.5, -1.0, -2.0],
    ]
    token_log_probs = plot_token_log_probs([0, 1, 2], log_probs, lambda idx: f"T{idx}", top_k=2)
    assert_visualization(token_log_probs, "Token Log Probabilities")
    assert token_log_probs.data["prompt"] == ["T0", "T1", "T2"]
    with pytest.raises(ValueError, match="top_k"):
        plot_token_log_probs([0, 1], [[0.0, 1.0], [1.0, 0.0]], lambda idx: f"T{idx}", top_k=0)

    performance = plot_model_performance(
        [0, 1, 2],
        ["T0", "T1", "T2"],
        [
            [1.0, 4.0, 2.0],
            [2.0, 1.0, 5.0],
            [3.0, 2.0, 1.0],
        ],
    )
    assert_visualization(performance, "Model Performance")
    assert performance.data["labels"] == ["logits", "log_probs", "probs"]

    next_token_browser = plot_next_token_browser(
        [0, 1, 2],
        [
            [1.0, 4.0, 2.0],
            [2.0, 1.0, 5.0],
            [3.0, 2.0, 1.0],
        ],
        lambda idx: f"T{idx}",
        top_k=2,
    )
    assert_visualization(next_token_browser, "Next Token Browser")
    assert 'data-filter="position"' in next_token_browser.html
    assert 'data-filter="metric"' in next_token_browser.html
    assert len(next_token_browser.data["positions"]) == 2

    text_neurons = plot_text_neuron_activations(
        ["A", "B"],
        [
            [[0.1, 0.2], [0.3, 0.4]],
            [[0.5, 0.6], [0.7, 0.8]],
        ],
        layer=1,
        neuron=0,
    )
    assert_visualization(text_neurons, "layer 1, neuron 0")
    with pytest.raises(ValueError, match="layer"):
        plot_text_neuron_activations(["A"], [[[0.1]]], layer=1)
    with pytest.raises(ValueError, match="neuron"):
        plot_text_neuron_activations(["A"], [[[0.1]]], neuron=1)

    text_browser = plot_text_neuron_browser(
        ["A", "B"],
        [
            [[0.1, 0.2], [0.3, 0.4]],
            [[0.5, 0.6], [0.7, 0.8]],
        ],
        layer_labels=["L0", "L1"],
        neuron_labels=["N0", "N1"],
    )
    assert_visualization(text_browser, "Text Neuron Browser")
    assert 'data-filter="layer"' in text_browser.html
    assert "click a token to inspect its value" in text_browser.html
    assert "data-token-index" in text_browser.html
    assert text_browser.data["shape"] == (2, 2, 2)

    mlp_browser = plot_mlp_component_browser(
        ["A", "B"],
        {
            "mlp_out": [
                [[0.1, -0.2], [0.3, -0.4]],
                [[0.5, -0.6], [0.7, -0.8]],
            ],
            "post": [
                [[1.1, 1.2], [1.3, 1.4]],
                [[1.5, 1.6], [1.7, 1.8]],
            ],
        },
        layer_labels=["L0", "L1"],
        dimension_labels={
            "mlp_out": ["resid_d0", "resid_d1"],
            "post": ["mlp_n0", "mlp_n1"],
        },
    )
    assert_visualization(mlp_browser, "MLP Component Browser")
    assert 'data-filter="component"' in mlp_browser.html
    assert 'data-filter="dimension"' in mlp_browser.html
    assert "click a token to inspect its MLP value" in mlp_browser.html
    assert "mlp_n1" in mlp_browser.html
    assert mlp_browser.data["shape"] == (2, 1, 2, 2, 2)

    mlp_topk = plot_mlp_neuron_topk_browser(
        ["A", "B"],
        [
            [[0.1, -0.2, 0.9], [0.3, -0.4, 0.5]],
            [[0.5, -0.6, 0.2], [0.7, -0.8, 0.1]],
        ],
        layer_labels=["L0", "L1"],
        neuron_labels=["mlp_n0", "mlp_n1", "mlp_n2"],
        max_k=2,
    )
    assert_visualization(mlp_topk, "MLP Neuron Top-K Browser")
    assert 'data-filter="mode"' in mlp_topk.html
    assert "safelens-rank-list" in mlp_topk.html
    assert mlp_topk.data["shape"] == (2, 2, 3)

    direction_viewer = plot_mlp_output_direction_viewer(
        [
            [
                [0.1, -0.4, 0.3],
                [-0.2, 0.5, 0.0],
            ]
        ],
        layer_labels=["L0"],
        neuron_labels=["mlp_n0", "mlp_n1"],
        residual_labels=["resid_d0", "resid_d1", "resid_d2"],
        vocab_positive=[[[("safe", 1.2), ("answer", 0.8)], [("block", 0.7)]]],
        vocab_negative=[[[("unsafe", -1.1)], [("ignore", -0.6)]]],
        max_items=2,
    )
    assert_visualization(direction_viewer, "MLP Output Direction Viewer")
    assert "Positive residual directions" in direction_viewer.html
    assert "Promoted vocab tokens" in direction_viewer.html
    assert direction_viewer.data["shape"] == (1, 2, 3)
    assert direction_viewer.data["has_vocab"] is True

    contribution_browser = plot_mlp_logit_contribution_browser(
        {
            "actual next token": [[0.1, -0.2], [0.3, -0.4]],
            "model top token": [[0.5, 0.6], [-0.7, 0.8]],
        },
        layer_labels=["L0", "L1"],
        token_labels=["A", "B"],
    )
    assert_visualization(contribution_browser, "MLP Logit Contribution Browser")
    assert 'data-filter="target"' in contribution_browser.html
    assert contribution_browser.data["matrix_labels"] == ["actual next token", "model top token"]

    variable_length_text_browser = plot_text_neuron_browser(
        [["A", "B", "C"], ["D"]],
        [
            [
                [[0.1], [0.2]],
                [[0.3], [0.4]],
                [[0.5], [0.6]],
            ],
            [
                [[0.7], [0.8]],
            ],
        ],
        sample_labels=["long", "short"],
        layer_labels=["L0", "L1"],
        neuron_labels=["N0"],
    )
    assert_visualization(variable_length_text_browser, "Text Neuron Browser")
    assert variable_length_text_browser.data["shape"] == (3, 2, 1)
    assert variable_length_text_browser.data["sample_labels"] == ["long", "short"]

    top_tokens = plot_topk_tokens(["A", "B"], [[[0.1, 0.2], [0.4, -0.3]]], max_k=1)
    assert_visualization(top_tokens, "Top-K Tokens")
    assert top_tokens.data["rows"][0][3] == "B=0.4"
    with pytest.raises(ValueError, match="max_k"):
        plot_topk_tokens(["A", "B"], [[[0.1], [0.4]]], max_k=0)

    multi_sample_top_tokens = plot_topk_tokens(
        [["A", "B"], ["C", "D"]],
        [
            [[[0.1], [0.4]]],
            [[[0.7], [0.2]]],
        ],
        sample_labels=["s0", "s1"],
        neuron_labels=["n0"],
        max_k=1,
    )
    assert_visualization(multi_sample_top_tokens, "s1")
    assert multi_sample_top_tokens.data["sample_labels"] == ["s0", "s1"]

    top_token_browser = plot_topk_tokens_browser(
        [["A", "B"], ["C", "D"]],
        [
            [[[0.1], [0.4]]],
            [[[0.7], [0.2]]],
        ],
        sample_labels=["s0", "s1"],
        neuron_labels=["n0"],
        max_k=1,
    )
    assert_visualization(top_token_browser, "Top-K Token Browser")
    assert 'data-filter="kind"' in top_token_browser.html

    variable_shape_top_tokens = plot_topk_tokens(
        [["a", "b", "c", "d", "e"], ["f", "g", "h"]],
        [
            [
                [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11], [12, 13, 14]],
                [[15, 16, 17], [18, 19, 20], [21, 22, 23], [24, 25, 26], [27, 28, 29]],
            ],
            [
                [[0, 1], [2, 3], [4, 5]],
                [[6, 7], [8, 9], [10, 11]],
            ],
        ],
        max_k=1,
    )
    assert_visualization(variable_shape_top_tokens, "Top-K Tokens")
    assert len(variable_shape_top_tokens.data["rows"]) == 10
    assert variable_shape_top_tokens.data["neuron_labels"] == ["0", "1", "2"]

    top_samples = plot_topk_samples(
        [[[["A", "B"], ["C", "D"]]]],
        [[[[0.1, 0.7], [0.8, 0.2]]]],
    )
    assert_visualization(top_samples, "Top-K Samples")
    assert top_samples.data["rows"][0][3] == 1
    with pytest.raises(ValueError, match="token dimension"):
        plot_topk_samples([[[["A", "B"], ["C"]]]], [[[[0.1, 0.7], [0.8, 0.2]]]])
    with pytest.raises(ValueError, match="sample dimension"):
        plot_topk_samples(
            [[[["A"], ["B"]], [["C"]]]],
            [[[[0.1], [0.2]], [[0.3]]]],
        )

    top_sample_browser = plot_topk_samples_browser(
        [[[["A", "B"], ["C", "D"]]]],
        [[[[0.1, 0.7], [0.8, 0.2]]]],
    )
    assert_visualization(top_sample_browser, "Top-K Sample Browser")
    assert 'data-filter="neuron"' in top_sample_browser.html


def test_nla_result_visualizations() -> None:
    rows: list[NLAResult | dict[str, Any]] = [
        NLAResult(
            explanation="This activation tracks safe refusal language.",
            sample_id="demo",
            token_index=0,
            token="Safe",
            source="layer_20.resid_post",
            model_name="Qwen/Qwen2.5-7B-Instruct",
            layer=20,
            component="resid_post",
            profile="qwen2.5-7b-l20",
            activation_norm=123.0,
            mse_nrm=0.2,
            cosine=0.9,
        ),
        {
            "explanation": "This activation is weaker and less reconstructable.",
            "sample_id": "demo",
            "token_index": 1,
            "token": "Lens",
            "source": "layer_20.resid_post",
            "model_name": "Qwen/Qwen2.5-7B-Instruct",
            "layer": 20,
            "component": "resid_post",
            "activation_norm": 80.0,
            "mse_nrm": 1.2,
            "cosine": 0.4,
        },
    ]

    browser = plot_nla_result_browser(rows)
    assert_visualization(browser, "NLA Result Browser")
    assert "safelens-nla-browser" in browser.html
    assert 'data-filter="metric"' in browser.html
    assert "safe refusal language" in browser.html
    assert browser.data["rows"][0]["cosine"] == 0.9

    heatmap = plot_nla_fidelity_heatmap(rows, metric="cosine")
    assert_visualization(heatmap, "NLA Fidelity Heatmap")
    assert heatmap.data["metric"] == "cosine"
    assert heatmap.data["x_labels"] == ["0: Safe", "1: Lens"]

    with pytest.raises(ValueError, match="metric"):
        plot_nla_fidelity_heatmap(rows, metric="missing")


def test_report_renderers() -> None:
    report = SafetyReport(
        sample_id="unsafe",
        flagged=True,
        risk_score=0.9,
        risk_category=["demo"],
        evidence_tokens=[1],
        monitoring_signals=[MonitoringSignal(name="monitor", risk_score=0.9, triggered=True)],
        attributions=[
            AttributionResult(
                method="dummy",
                attribution_score=0.8,
                tokens=[TokenAttribution(token_index=1, score=0.8, token_text="bad")],
            )
        ],
    )
    safety = render_safety_report(report)
    assert_visualization(safety, "unsafe")

    run = render_run_report(RunReport(reports=[report], summary={"flagged_count": 1}))
    assert_visualization(run, "flagged_count")
    assert run.data["reports"][0]["sample_id"] == "unsafe"


def test_top_level_exports_and_circuitsvis_bridge_error() -> None:
    assert SafeLens.Visualization is Visualization
    assert SafeLens.plot_activation_cache_browser is plot_activation_cache_browser
    assert SafeLens.plot_activation_patching_browser is plot_activation_patching_browser
    assert SafeLens.plot_attention_browser is plot_attention_browser
    assert SafeLens.plot_attention_pattern is plot_attention_pattern
    assert SafeLens.plot_bar is plot_bar
    assert SafeLens.plot_histogram is plot_histogram
    assert SafeLens.plot_next_token_browser is plot_next_token_browser
    assert SafeLens.plot_mlp_component_browser is plot_mlp_component_browser
    assert SafeLens.plot_mlp_neuron_topk_browser is plot_mlp_neuron_topk_browser
    assert SafeLens.plot_mlp_output_direction_viewer is plot_mlp_output_direction_viewer
    assert SafeLens.plot_mlp_logit_contribution_browser is plot_mlp_logit_contribution_browser
    assert SafeLens.plot_text_neuron_browser is plot_text_neuron_browser
    assert SafeLens.plot_topk_tokens_browser is plot_topk_tokens_browser
    assert SafeLens.plot_nla_result_browser is plot_nla_result_browser
    assert SafeLens.plot_nla_fidelity_heatmap is plot_nla_fidelity_heatmap

    if importlib.util.find_spec("circuitsvis") is None:
        with pytest.raises(ImportError, match="circuitsvis is not installed"):
            to_circuitsvis_colored_tokens(["A"], [1.0])
        with pytest.raises(ImportError, match="circuitsvis is not installed"):
            to_circuitsvis_model_performance([0, 1], ["A", "B"], [[0.0, 1.0], [1.0, 0.0]])
