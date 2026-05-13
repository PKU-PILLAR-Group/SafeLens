"""Configuration schema generation and static validation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from SafeLens.core.base import LayerRef, MethodSpec, PipelineConfig
from SafeLens.core.registry import (
    RegistryError,
    get_attributor,
    get_monitor,
    get_probe,
    load_builtin_methods,
)
from SafeLens.utils import validate_qwen3_hook_ref


class ConfigValidationError(ValueError):
    """Raised when a SafeLens YAML config fails static validation."""


def pipeline_config_json_schema() -> dict[str, Any]:
    """Return the JSON Schema for SafeLens YAML pipeline configs."""
    schema = PipelineConfig.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema


def write_pipeline_config_json_schema(path: str | Path) -> None:
    """Write the pipeline config JSON Schema to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(pipeline_config_json_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config file into a dictionary."""
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise ConfigValidationError(f"Could not parse YAML config {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigValidationError(
            f"Config {config_path} must be a YAML mapping at the top level."
        )
    return raw


def validate_pipeline_config_file(path: str | Path) -> PipelineConfig:
    """Load and statically validate a SafeLens pipeline config file."""
    raw = load_yaml_config(path)
    try:
        config = PipelineConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigValidationError(format_pydantic_errors(exc)) from exc

    errors = [
        *validate_registered_methods(config),
        *validate_static_hook_names(config),
    ]
    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise ConfigValidationError(f"Invalid SafeLens config:\n{joined}")
    return config


def validate_registered_methods(config: PipelineConfig) -> list[str]:
    """Return registry errors for method names referenced by a config."""
    load_builtin_methods()
    errors: list[str] = []
    sections = (
        ("pipeline.probes", config.pipeline.probes, get_probe),
        ("pipeline.monitors", config.pipeline.monitors, get_monitor),
        ("pipeline.attributors", config.pipeline.attributors, get_attributor),
    )
    for section, specs, getter in sections:
        for index, spec in enumerate(specs):
            try:
                getter(spec.name)
            except RegistryError as exc:
                errors.append(f"{section}[{index}].name: {exc.args[0]}")
    return errors


def validate_static_hook_names(config: PipelineConfig) -> list[str]:
    """Return static hook-name errors that can be checked without loading a model."""
    if config.model.source not in {"qwen3", "qwen3_dense", "qwen3-dense"}:
        return []

    errors: list[str] = []
    for section, specs in (
        ("pipeline.probes", config.pipeline.probes),
        ("pipeline.monitors", config.pipeline.monitors),
        ("pipeline.attributors", config.pipeline.attributors),
    ):
        for spec_index, spec in enumerate(specs):
            for key_path, layer_ref in iter_layer_refs(spec):
                try:
                    validate_qwen3_hook_ref(layer_ref)
                except ValueError as exc:
                    errors.append(f"{section}[{spec_index}].config.{key_path}: {exc}")
    return errors


def iter_layer_refs(spec: MethodSpec) -> Iterable[tuple[str, LayerRef]]:
    """Yield layer or hook references from a method config."""
    config = spec.config
    if "layers" in config:
        layers = config["layers"]
        if isinstance(layers, list):
            for index, layer in enumerate(layers):
                if isinstance(layer, int | str):
                    yield f"layers[{index}]", layer
        elif isinstance(layers, int | str):
            yield "layers", layers
    if "layer" in config and isinstance(config["layer"], int | str):
        yield "layer", config["layer"]
    for key in ("hook", "hook_name", "activation_name"):
        value = config.get(key)
        if isinstance(value, str):
            yield key, value


def format_pydantic_errors(exc: ValidationError) -> str:
    """Format Pydantic errors for CLI users."""
    lines = ["Invalid SafeLens config:"]
    for error in exc.errors():
        loc = ".".join(str(part) for part in error.get("loc", ())) or "<root>"
        lines.append(f"- {loc}: {error.get('msg', 'invalid value')}")
    return "\n".join(lines)


def config_summary(config: PipelineConfig) -> dict[str, Any]:
    """Return a small serializable summary of a validated config."""
    return {
        "model": {
            "source": config.model.source,
            "name": config.model.name,
        },
        "methods": {
            "probes": [spec.name for spec in config.pipeline.probes],
            "monitors": [spec.name for spec in config.pipeline.monitors],
            "attributors": [spec.name for spec in config.pipeline.attributors],
        },
        "dataset_size": len(config.dataset),
        "report_path": config.output.report_path,
    }
