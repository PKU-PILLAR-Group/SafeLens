from __future__ import annotations

from pathlib import Path

from SafeLens.attribution import (
    plot_head_attribution,
    render_input_attribution_html,
    save_input_attribution_html,
)
from SafeLens.core.base import AttributionResult, TokenAttribution


def test_render_input_attribution_html_colors_tokens() -> None:
    result = AttributionResult(
        method="captum_input_attributor",
        attribution_score=1.0,
        tokens=[
            TokenAttribution(
                token_index=0,
                token_text="safe",
                score=0.5,
                metadata={"raw_score": 2.0},
            ),
            TokenAttribution(
                token_index=1,
                token_text="risk",
                score=-1.0,
                metadata={"raw_score": -4.0},
            ),
        ],
    )

    html = render_input_attribution_html(result)

    assert "safe" in html
    assert "risk" in html
    assert "rgba(190, 18, 60" in html
    assert "rgba(37, 99, 235" in html


def test_save_input_attribution_html_writes_file(tmp_path: Path) -> None:
    result = AttributionResult(
        method="captum_input_attributor",
        attribution_score=1.0,
        tokens=[TokenAttribution(token_index=0, token_text="hello", score=1.0)],
    )

    path = save_input_attribution_html(result, tmp_path / "input.html")

    assert path.exists()
    assert "hello" in path.read_text(encoding="utf-8")


def test_plot_head_attribution_writes_png(tmp_path: Path) -> None:
    result = AttributionResult(
        method="safety_head_attributor",
        attribution_score=0.5,
        details={
            "heads": [
                {"layer": 0, "head": 0, "score": 0.1},
                {"layer": 0, "head": 1, "score": 0.5},
                {"layer": 1, "head": 0, "score": 0.2},
            ]
        },
    )

    path = plot_head_attribution(result, tmp_path / "heads.png")

    assert path.exists()
    assert path.stat().st_size > 0
