"""Command-line entry point for SafeLens."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        dataset = _load_jsonl(args.input_jsonl)
        report = PipelineRunner.from_yaml(args.config).run(dataset=dataset)
        print(json.dumps(report.summary, indent=2))


if __name__ == "__main__":
    main()
