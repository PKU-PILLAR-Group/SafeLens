from __future__ import annotations

import json
from pathlib import Path

import pytest

from SafeLens.cli import main
from SafeLens.config import (
    ConfigValidationError,
    pipeline_config_json_schema,
    validate_pipeline_config_file,
)


def test_pipeline_config_schema_contains_model_source_enum() -> None:
    schema = pipeline_config_json_schema()

    source_schema = schema["$defs"]["ModelLoadConfig"]["properties"]["source"]

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "qwen3_dense" in source_schema["enum"]
    assert "modelscope" in source_schema["enum"]
    assert "local" in source_schema["enum"]


def test_example_configs_validate() -> None:
    for config_name in (
        "config.yaml",
        "huggingface_config.yaml",
        "modelscope_config.yaml",
        "qwen3_dense_config.yaml",
        "local_model_config.yaml",
    ):
        config = validate_pipeline_config_file(Path("examples") / config_name)
        assert config.output.report_path


def test_validate_rejects_unknown_model_source(tmp_path: Path) -> None:
    config_path = tmp_path / "bad-source.yaml"
    config_path.write_text(
        """
model:
  source: hugging-face
  name: demo
pipeline:
  probes: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="Unsupported model.source"):
        validate_pipeline_config_file(config_path)


def test_validate_rejects_unknown_method_with_suggestion(tmp_path: Path) -> None:
    config_path = tmp_path / "bad-method.yaml"
    config_path.write_text(
        """
model:
  source: dummy
  name: dummy
pipeline:
  probes:
    - name: dummy_probee
      config: {}
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="dummy_probe"):
        validate_pipeline_config_file(config_path)


def test_validate_rejects_unsupported_qwen3_hook_name(tmp_path: Path) -> None:
    config_path = tmp_path / "bad-hook.yaml"
    config_path.write_text(
        """
model:
  source: qwen3_dense
  name: Qwen/Qwen3-8B
pipeline:
  probes:
    - name: dummy_probe
      config:
        layers:
          - layer_0.not_a_component
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="Supported components"):
        validate_pipeline_config_file(config_path)


def test_cli_validate_prints_summary(capsys: pytest.CaptureFixture[str]) -> None:
    main(["validate", "--config", "examples/config.yaml", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["valid"] is True
    assert payload["model"]["source"] == "dummy"


def test_cli_schema_writes_json_schema(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"

    main(["schema", "--output", str(schema_path)])

    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    assert payload["$defs"]["ModelLoadConfig"]["properties"]["source"]["enum"]
