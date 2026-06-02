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


def test_cli_inspect_model_does_not_infer_transformerlens_from_family_marker(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["inspect-model", "--model", "org/qwen-this-does-not-exist", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert payload["source"] == "huggingface"
    assert payload["supported"] is True


def test_cli_inspect_model_transformerlens_override_rejects_unknown_family_marker(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(
        [
            "inspect-model",
            "--model",
            "org/qwen-this-does-not-exist",
            "--source",
            "transformer_lens",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is False
    assert payload["safelens_transformer_lens_compatible"] is False


def test_cli_inspect_model_flags_native_transformerlens_checkpoint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["inspect-model", "--model", "solu-1l", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is False
    assert payload["official_transformer_lens_supported"] is True
    assert payload["checkpoint_format"] == "transformer_lens_hooked_transformer"
    assert payload["transformers_loadable"] is False


def test_cli_inspect_model_reports_architecture_specific_transformerlens_components(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["inspect-model", "--model", "mamba-130m", "--source", "transformer_lens", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert payload["architecture_bridge_adapter"] == "mamba_ssm"
    assert "ssm_in" in payload["bridge_components"]
    assert "pattern" not in payload["bridge_components"]


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


def test_cli_lists_transformerlens_models(capsys: pytest.CaptureFixture[str]) -> None:
    main(["models", "list-transformerlens", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert payload["count"] >= 150
    assert "gpt2" in payload["models"]
    assert "meta-llama/Llama-3.1-8B" in payload["models"]


def test_cli_lists_architecture_bridge_adapters(capsys: pytest.CaptureFixture[str]) -> None:
    main(["models", "list-architectures", "--json"])

    payload = json.loads(capsys.readouterr().out)
    adapter_names = {item["name"] for item in payload["architecture_adapters"]}

    assert "llama_like_decoder" in adapter_names
    assert "gpt2_decoder" in adapter_names
