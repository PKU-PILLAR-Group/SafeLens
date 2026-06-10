"""Visualization helpers for SafeLens attribution results."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from SafeLens.core.base import AttributionResult


def render_input_attribution_html(
    attribution: AttributionResult,
    *,
    title: str = "Input Attribution",
) -> str:
    """Return an HTML document with input tokens colored by attribution score."""
    token_spans = "\n".join(_token_span(token) for token in attribution.tokens)
    payload = json.dumps(attribution.to_dict(), ensure_ascii=False, indent=2)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      color: #202124;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
      margin: 32px;
      max-width: 1100px;
    }}
    .tokens {{
      border: 1px solid #d8dee4;
      border-radius: 8px;
      padding: 16px;
    }}
    .token {{
      border-radius: 4px;
      display: inline-block;
      margin: 2px;
      padding: 3px 5px;
      white-space: pre-wrap;
    }}
    .legend {{
      color: #57606a;
      font-size: 13px;
      margin: 12px 0 20px;
    }}
    pre {{
      background: #f6f8fa;
      border-radius: 8px;
      overflow-x: auto;
      padding: 16px;
    }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <div class="legend">Red indicates positive attribution; blue indicates negative attribution.</div>
  <div class="tokens">
{token_spans}
  </div>
  <h2>Raw Result</h2>
  <pre>{html.escape(payload)}</pre>
</body>
</html>
"""


def save_input_attribution_html(
    attribution: AttributionResult,
    path: str | Path,
    *,
    title: str = "Input Attribution",
) -> Path:
    """Write an input-token attribution HTML visualization."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_input_attribution_html(attribution, title=title),
        encoding="utf-8",
    )
    return output_path


def plot_head_attribution(
    attribution: AttributionResult,
    path: str | Path,
    *,
    title: str = "Safety Head Attribution",
) -> Path:
    """Write a layer-by-head score heatmap for a safety-head attribution result."""
    heads = attribution.details.get("heads", [])
    if not heads:
        raise ValueError("Head attribution result does not contain details['heads'].")

    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        raise ImportError(
            "Head attribution visualization requires matplotlib and numpy."
        ) from exc

    max_layer = max(int(item["layer"]) for item in heads)
    max_head = max(int(item["head"]) for item in heads)
    scores = np.full((max_layer + 1, max_head + 1), np.nan, dtype=float)
    for item in heads:
        scores[int(item["layer"]), int(item["head"])] = float(item["score"])

    width = max(6.0, min(24.0, 0.45 * (max_head + 1) + 2.5))
    height = max(3.5, min(18.0, 0.35 * (max_layer + 1) + 2.5))
    fig, ax = plt.subplots(figsize=(width, height))
    masked = np.ma.masked_invalid(scores)
    image = ax.imshow(masked, aspect="auto", cmap="viridis")
    ax.set_title(title)
    ax.set_xlabel("Head")
    ax.set_ylabel("Layer")
    ax.set_xticks(range(max_head + 1))
    ax.set_yticks(range(max_layer + 1))
    ax.grid(which="major", color="white", linewidth=0.5, alpha=0.35)
    fig.colorbar(image, ax=ax, label="KL score")
    fig.tight_layout()

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def _token_span(token: Any) -> str:
    text = token.token_text if token.token_text is not None else f"<tok {token.token_index}>"
    score = float(token.score)
    background = _score_color(score)
    foreground = "#111827" if abs(score) < 0.75 else "#ffffff"
    title = (
        f"index={token.token_index}; score={score:.6g}; "
        f"raw={token.metadata.get('raw_score', score):.6g}"
    )
    return (
        f'    <span class="token" title="{html.escape(title)}" '
        f'style="background:{background};color:{foreground}">'
        f"{html.escape(str(text))}</span>"
    )


def _score_color(score: float) -> str:
    magnitude = max(0.0, min(1.0, abs(score)))
    alpha = 0.15 + 0.75 * magnitude
    if score >= 0:
        return f"rgba(190, 18, 60, {alpha:.3f})"
    return f"rgba(37, 99, 235, {alpha:.3f})"
