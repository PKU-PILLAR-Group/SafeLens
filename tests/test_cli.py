from __future__ import annotations

import json

import pytest

from SafeLens.cli import main


def test_cli_models_list_supported_json(capsys: pytest.CaptureFixture[str]) -> None:
    main(["models", "list-supported", "--json"])

    payload = json.loads(capsys.readouterr().out)
    adapter_names = {item["name"] for item in payload["adapters"]}

    assert "qwen3_dense" in adapter_names
    assert "huggingface" in adapter_names


def test_cli_inspect_model_infers_qwen3_adapter(capsys: pytest.CaptureFixture[str]) -> None:
    main(["inspect-model", "--model", "Qwen/Qwen3-8B", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert payload["source"] == "qwen3_dense"
    assert payload["supported"] is True
    assert payload["download_plan"]["cache_dir"] == ".cache/safelens/models/huggingface"


def test_cli_inspect_model_honors_source_override(capsys: pytest.CaptureFixture[str]) -> None:
    main(
        [
            "inspect-model",
            "--model",
            "./models/local-causal-lm",
            "--source",
            "local",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert payload["source"] == "local"
    assert payload["download_plan"]["uses_network"] is False
