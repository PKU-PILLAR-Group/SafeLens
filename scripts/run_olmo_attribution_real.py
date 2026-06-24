#!/usr/bin/env python3
"""Run real attribution smoke tests on a local OLMo HuggingFace checkpoint."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from SafeLens.attribution import (
    attribute_response_token_input,
    attribute_safety_heads,
    plot_head_attribution,
    save_input_attribution_html,
)
from SafeLens.core.base import ModelLoadConfig
from SafeLens.utils import build_model_wrapper

DEFAULT_MODEL_PATH = Path(
    "/workspace/cjh/projects/FlowManifold/models/huggingface.co/"
    "allenai/Olmo-3-7B-Think-SFT/step45000"
)
DEFAULT_DATA_PATH = Path("/tmp/SafetyHeadAttribution/exp_data/maliciousinstruct.csv")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sample = read_sample(Path(args.data_path), args.sample_index)
    model_path = Path(args.model_path).expanduser().resolve()
    model_config = build_local_model_config(model_path, args)

    if args.dry_run:
        write_dry_run_report(output_dir, model_config, sample, args)
        return

    wrapper = build_model_wrapper(model_config)
    wrapper.load_model()
    try:
        results: dict[str, Any] = {}

        if not args.skip_captum:
            input_attr = attribute_response_token_input(
                wrapper,
                sample,
                response=args.response,
                target_response_index=args.target_response_index,
                n_steps=args.captum_steps,
                internal_batch_size=args.captum_internal_batch_size,
            )
            input_json = output_dir / "input_attribution.json"
            input_json.write_text(
                json.dumps(input_attr.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            input_html = save_input_attribution_html(
                input_attr,
                output_dir / "input_attribution.html",
                title="OLMo Input Attribution",
            )
            results["input_attribution"] = {
                "json": str(input_json),
                "html": str(input_html),
                "score": input_attr.attribution_score,
                "token_count": len(input_attr.tokens),
                "target_token_text": input_attr.details.get("target_token_text"),
            }

        if not args.skip_safety_heads:
            head_attr = attribute_safety_heads(
                wrapper,
                {"text": sample},
                layers=parse_index_selector(args.layers),
                heads=parse_index_selector(args.heads),
                top_k=args.top_k,
            )
            head_json = output_dir / "head_attribution.json"
            head_json.write_text(
                json.dumps(head_attr.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            head_png = plot_head_attribution(
                head_attr,
                output_dir / "head_attribution.png",
                title="OLMo Safety Head Attribution",
            )
            results["head_attribution"] = {
                "json": str(head_json),
                "png": str(head_png),
                "score": head_attr.attribution_score,
                "head_count": head_attr.details.get("head_count"),
            }
    finally:
        wrapper.remove_hooks()

    write_summary_report(output_dir, model_config, sample, results, args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", default=str(DEFAULT_MODEL_PATH))
    parser.add_argument("--data-path", default=str(DEFAULT_DATA_PATH))
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--output-dir", default="test_reports/olmo_attribution_real")
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--device", default=None)
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--trust-remote-code", action="store_true", default=True)
    parser.add_argument("--response", default=" I cannot help with that.")
    parser.add_argument("--target-response-index", type=int, default=1)
    parser.add_argument("--captum-steps", type=int, default=4)
    parser.add_argument("--captum-internal-batch-size", type=int, default=None)
    parser.add_argument("--layers", default="0", help="Comma list, range like 0:4, or all.")
    parser.add_argument("--heads", default="0,1", help="Comma list, range like 0:8, or all.")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--skip-captum", action="store_true")
    parser.add_argument("--skip-safety-heads", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def build_local_model_config(model_path: Path, args: argparse.Namespace) -> ModelLoadConfig:
    load_kwargs: dict[str, Any] = {
        "local_files_only": True,
        "low_cpu_mem_usage": True,
    }
    if args.device_map and args.device_map.lower() != "none":
        load_kwargs["device_map"] = args.device_map
    return ModelLoadConfig(
        source="local",
        name=str(model_path),
        local_dir=str(model_path),
        dtype=args.dtype,
        device=args.device,
        trust_remote_code=bool(args.trust_remote_code),
        load_kwargs=load_kwargs,
        tokenizer_kwargs={"local_files_only": True},
    )


def read_sample(data_path: Path, sample_index: int) -> str:
    with data_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if sample_index < 0 or sample_index >= len(rows):
        raise IndexError(f"sample-index {sample_index} outside dataset size {len(rows)}.")
    row = rows[sample_index]
    if "input" not in row:
        raise KeyError(f"Expected CSV column 'input', got {sorted(row)}.")
    return row["input"]


def parse_index_selector(value: str) -> list[int] | None:
    normalized = str(value).strip().lower()
    if normalized in {"", "all", "none"}:
        return None
    if ":" in normalized:
        start_text, stop_text = normalized.split(":", 1)
        start = int(start_text) if start_text else 0
        stop = int(stop_text)
        return list(range(start, stop))
    return [int(item.strip()) for item in normalized.split(",") if item.strip()]


def write_dry_run_report(
    output_dir: Path,
    model_config: ModelLoadConfig,
    sample: str,
    args: argparse.Namespace,
) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": True,
        "model": model_config.to_dict(),
        "sample": sample,
        "layers": args.layers,
        "heads": args.heads,
    }
    (output_dir / "dry_run.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_summary_report(output_dir, model_config, sample, {"dry_run": payload}, args)


def write_summary_report(
    output_dir: Path,
    model_config: ModelLoadConfig,
    sample: str,
    results: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    summary_json = output_dir / "summary.json"
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": model_config.to_dict(),
        "sample": sample,
        "args": vars(args),
        "results": results,
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# OLMo Attribution Real-Scenario Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Model path: `{model_config.local_dir}`",
        f"- Data path: `{args.data_path}`",
        f"- Sample index: `{args.sample_index}`",
        f"- Sample: `{sample}`",
        f"- Summary JSON: `{summary_json}`",
        "",
        "## Outputs",
        "",
    ]
    for name, payload in results.items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(payload, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
