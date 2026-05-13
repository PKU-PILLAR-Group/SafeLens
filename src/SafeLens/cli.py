"""Command-line entry point for SafeLens."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from SafeLens.config import (
    ConfigValidationError,
    config_summary,
    pipeline_config_json_schema,
    validate_pipeline_config_file,
    write_pipeline_config_json_schema,
)
from SafeLens.pipelines.runner import PipelineRunner


def _load_jsonl(path: str | None) -> list[dict[str, Any]] | None:
    if path is None:
        return None
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safelens")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run a safety pipeline")
    run_parser.add_argument("--config", required=True, help="Path to YAML pipeline config")
    run_parser.add_argument("--input-jsonl", help="Optional JSONL dataset override")

    validate_parser = subparsers.add_parser(
        "validate",
        help="validate a YAML pipeline config without loading a model",
    )
    validate_parser.add_argument("--config", required=True, help="Path to YAML pipeline config")
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable validation summary",
    )

    schema_parser = subparsers.add_parser(
        "schema",
        help="print or write the JSON Schema for YAML pipeline configs",
    )
    schema_parser.add_argument(
        "--output",
        "-o",
        help="Optional output path. Prints to stdout when omitted.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        dataset = _load_jsonl(args.input_jsonl)
        report = PipelineRunner.from_yaml(args.config).run(dataset=dataset)
        print(json.dumps(report.summary, indent=2))
    elif args.command == "validate":
        try:
            config = validate_pipeline_config_file(args.config)
        except ConfigValidationError as exc:
            parser.exit(1, f"{exc}\n")
        summary = config_summary(config)
        if args.json:
            print(json.dumps({"valid": True, **summary}, indent=2))
        else:
            print(f"Config is valid: {args.config}")
            print(json.dumps(summary, indent=2))
    elif args.command == "schema":
        if args.output:
            write_pipeline_config_json_schema(args.output)
            print(f"Wrote JSON Schema to {args.output}")
        else:
            print(json.dumps(pipeline_config_json_schema(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
