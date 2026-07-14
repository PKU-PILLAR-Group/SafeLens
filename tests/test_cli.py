from __future__ import annotations

import json
from pathlib import Path

import pytest

from SafeLens.cli import main


def test_cli_models_list_supported_json(capsys: pytest.CaptureFixture[str]) -> None:
    main(["models", "list-supported", "--json"])

    payload = json.loads(capsys.readouterr().out)
    adapter_names = {item["name"] for item in payload["adapters"]}

    assert "qwen3_dense" in adapter_names
    assert "huggingface" in adapter_names


def test_cli_run_uses_jsonl_override_and_writes_report(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "report.json"
    config_path = tmp_path / "config.yaml"
    input_path = tmp_path / "input.jsonl"
    config_path.write_text(
        f"""
model:
  source: dummy
  name: dummy
pipeline:
  risk_threshold: 0.5
  probes:
    - name: dummy_probe
      config:
        layers: [0]
        risk_terms: ["jailbreak"]
  monitors:
    - name: dummy_monitor
      config:
        threshold: 0.5
  attributors:
    - name: dummy_attributor
      config:
        risk_terms: ["jailbreak"]
dataset:
  - id: ignored
    text: "This dataset row should be overridden."
output:
  report_path: "{report_path}"
""",
        encoding="utf-8",
    )
    input_path.write_text(
        "\n".join(
            [
                json.dumps({"id": "safe-jsonl", "text": "hello"}),
                json.dumps({"id": "unsafe-jsonl", "text": "jailbreak attack"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    main(["run", "--config", str(config_path), "--input-jsonl", str(input_path)])

    stdout_summary = json.loads(capsys.readouterr().out)
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert stdout_summary == written["summary"]
    assert written["summary"] == {
        "samples_scanned": 2,
        "flagged_count": 1,
        "max_risk_score": 0.55,
    }
    assert [report["sample_id"] for report in written["reports"]] == [
        "safe-jsonl",
        "unsafe-jsonl",
    ]


def test_cli_run_rejects_non_object_jsonl(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    input_path = tmp_path / "input.jsonl"
    config_path.write_text("model:\n  source: dummy\n  name: dummy\n", encoding="utf-8")
    input_path.write_text("[1, 2, 3]\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["run", "--config", str(config_path), "--input-jsonl", str(input_path)])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "line 1" in captured.err
    assert "each row must be a JSON object" in captured.err


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


def test_cli_explorer_delegates_single_server_options(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from SafeLens import explorer_api

    received: dict[str, object] = {}

    def fake_serve_explorer(**kwargs: object) -> None:
        received.update(kwargs)

    monkeypatch.setattr(explorer_api, "serve_explorer", fake_serve_explorer)
    artifact_root = tmp_path / "artifacts"
    web_root = tmp_path / "web"

    main([
        "explorer",
        "--artifact-root", str(artifact_root),
        "--web-root", str(web_root),
        "--host", "0.0.0.0",
        "--port", "8080",
        "--allow-remote",
        "--no-browser",
        "--log-level", "warning",
    ])

    assert received == {
        "artifact_root": artifact_root,
        "host": "0.0.0.0",
        "port": 8080,
        "web_root": web_root,
        "open_browser": False,
        "allow_remote": True,
        "log_level": "warning",
    }
