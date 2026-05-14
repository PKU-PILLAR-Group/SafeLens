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
    run_report_json_schema,
    validate_pipeline_config_file,
    write_pipeline_config_json_schema,
)
from SafeLens.core.base import ModelLoadConfig
from SafeLens.pipelines.runner import PipelineRunner
from SafeLens.utils import (
    get_model_adapter_registry,
    list_architecture_adapters,
    transformer_lens_official_model_names,
)


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
        "--kind",
        choices=["pipeline-config", "run-report"],
        default="pipeline-config",
        help="Schema kind to emit",
    )
    schema_parser.add_argument(
        "--output",
        "-o",
        help="Optional output path. Prints to stdout when omitted.",
    )

    models_parser = subparsers.add_parser("models", help="inspect model adapter support")
    models_subparsers = models_parser.add_subparsers(dest="models_command", required=True)
    list_parser = models_subparsers.add_parser(
        "list-supported",
        help="list registered model adapters and their capabilities",
    )
    list_parser.add_argument("--json", action="store_true", help="Print JSON output")
    tl_list_parser = models_subparsers.add_parser(
        "list-transformerlens",
        help="list vendored TransformerLens-compatible model names",
    )
    tl_list_parser.add_argument("--json", action="store_true", help="Print JSON output")
    architecture_list_parser = models_subparsers.add_parser(
        "list-architectures",
        help="list SafeLens architecture bridge adapters",
    )
    architecture_list_parser.add_argument("--json", action="store_true", help="Print JSON output")

    inspect_parser = subparsers.add_parser(
        "inspect-model",
        help="inspect static adapter support for a model without downloading it",
    )
    inspect_parser.add_argument("--model", required=True, help="Model ID or local model path")
    inspect_parser.add_argument(
        "--source",
        help="Optional model source override, such as huggingface, modelscope, qwen3_dense, local",
    )
    inspect_parser.add_argument(
        "--cache-dir",
        help="Optional cache directory used in the resolved download plan",
    )
    inspect_parser.add_argument(
        "--local-dir",
        help="Optional local directory used by local or ModelScope adapters",
    )
    inspect_parser.add_argument("--json", action="store_true", help="Print JSON output")
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
        schema = (
            pipeline_config_json_schema()
            if args.kind == "pipeline-config"
            else run_report_json_schema()
        )
        if args.output:
            if args.kind == "pipeline-config":
                write_pipeline_config_json_schema(args.output)
            else:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output).write_text(
                    json.dumps(schema, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            print(f"Wrote JSON Schema to {args.output}")
        else:
            print(json.dumps(schema, indent=2, sort_keys=True))
    elif args.command == "models":
        if args.models_command == "list-transformerlens":
            models = transformer_lens_official_model_names()
            if args.json:
                print(json.dumps({"models": models, "count": len(models)}, indent=2))
            else:
                print(f"TransformerLens-compatible model names ({len(models)}):")
                for model_name in models:
                    print(f"- {model_name}")
        elif args.models_command == "list-architectures":
            adapters = list_architecture_adapters()
            if args.json:
                print(json.dumps({"architecture_adapters": adapters}, indent=2))
            else:
                print("SafeLens architecture bridge adapters:")
                for adapter in adapters:
                    components = ", ".join(adapter["supported_components"]) or "-"
                    print(f"- {adapter['name']}: {components}")
        else:
            registry = get_model_adapter_registry()
            adapters = registry.list_supported()
            if args.json:
                print(json.dumps({"adapters": adapters}, indent=2))
            else:
                _print_model_adapter_list(adapters)
    elif args.command == "inspect-model":
        registry = get_model_adapter_registry()
        source = args.source
        model_config = None
        if source is not None:
            model_config = ModelLoadConfig(
                source=source,
                name=args.model,
                cache_dir=args.cache_dir,
                local_dir=args.local_dir,
            )
        result = registry.inspect_model(args.model, source=source, config=model_config)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            _print_model_inspection(result)


def _print_model_adapter_list(adapters: list[dict[str, Any]]) -> None:
    print("Supported model adapters:")
    for adapter in adapters:
        capabilities = adapter["capabilities"]
        aliases = ", ".join(adapter["aliases"]) or "-"
        hooks = ", ".join(capabilities["supported_hooks"]) or "-"
        print(f"- {adapter['name']} ({adapter['display_name']})")
        print(f"  aliases: {aliases}")
        print(f"  hooks: {hooks}")
        print(f"  attention_pattern: {capabilities['supports_attention_pattern']}")
        print(f"  cache_policy: {capabilities['cache_policy']}")


def _print_model_inspection(result: dict[str, Any]) -> None:
    adapter = result["adapter"]
    print(f"Model: {result['model']}")
    print(f"Adapter: {adapter['name']} ({adapter['display_name']})")
    print(f"Supported: {result['supported']}")
    print(f"Family: {result['model_family']}")
    if result.get("parameter_size_b") is not None:
        print(f"Parameter size: {result['parameter_size_b']}B")
    print("Download plan:")
    for key, value in result["download_plan"].items():
        print(f"  {key}: {value}")
    warnings = result.get("warnings") or []
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    errors = result.get("errors") or []
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
