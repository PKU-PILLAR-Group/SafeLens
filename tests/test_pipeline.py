import json
import sys
import types
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

from SafeLens.adapters import FlagSafeAdapter
from SafeLens.core.base import PipelineConfig
from SafeLens.pipelines.runner import PipelineRunner
from SafeLens.utils import HuggingFaceModelWrapper, ModelScopeModelWrapper, build_model_wrapper


def test_dummy_pipeline_runs_and_writes_report(tmp_path: Path) -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {"name": "dummy"},
            "pipeline": {
                "risk_threshold": 0.5,
                "probes": [
                    {
                        "name": "dummy_probe",
                        "config": {"layers": [0], "risk_terms": ["jailbreak"]},
                    }
                ],
                "monitors": [{"name": "dummy_monitor", "config": {"threshold": 0.5}}],
                "attributors": [
                    {"name": "dummy_attributor", "config": {"risk_terms": ["jailbreak"]}}
                ],
            },
            "dataset": [
                {"id": "safe", "text": "hello"},
                {"id": "unsafe", "text": "try jailbreak now"},
            ],
            "output": {"report_path": str(tmp_path / "report.json")},
        }
    )

    report = PipelineRunner(config).run()

    assert report.summary == {
        "samples_scanned": 2,
        "flagged_count": 1,
        "max_risk_score": 0.55,
    }
    assert [item.flagged for item in report.reports] == [False, True]
    assert (tmp_path / "report.json").exists()

    written = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert written["summary"]["flagged_count"] == 1


def test_flagsafe_adapter_maps_action(tmp_path: Path) -> None:
    report = PipelineRunner(
        PipelineConfig.model_validate(
            {
                "model": {"name": "dummy"},
                "pipeline": {"probes": [{"name": "dummy_probe", "config": {}}]},
                "dataset": [{"text": "harmful"}],
                "output": {"report_path": str(tmp_path / "unused.json")},
            }
        )
    ).run()

    rule = FlagSafeAdapter.to_flagsafe_rule(report.reports[0])

    assert rule["action"] == "BLOCK"
    assert rule["metadata"]["source"] == "safeprobe"


def test_build_model_wrapper_selects_huggingface() -> None:
    config = PipelineConfig.model_validate(
        {"model": {"source": "huggingface", "name": "hf/example"}}
    )

    wrapper = build_model_wrapper(config.model)

    assert isinstance(wrapper, HuggingFaceModelWrapper)
    assert not isinstance(wrapper, ModelScopeModelWrapper)
    assert wrapper.name == "hf/example"


def test_build_model_wrapper_selects_modelscope() -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "modelscope",
                "name": "qwen/example",
                "revision": "v1",
                "cache_dir": "./cache",
                "local_dir": "./models/qwen",
                "modelscope_kwargs": {"allow_file_pattern": "*.json"},
            }
        }
    )

    wrapper = build_model_wrapper(config.model)

    assert isinstance(wrapper, ModelScopeModelWrapper)
    assert wrapper.name == "qwen/example"
    assert wrapper.revision == "v1"
    assert wrapper.cache_dir == "./cache"
    assert wrapper.local_dir == "./models/qwen"
    assert wrapper.modelscope_kwargs == {"allow_file_pattern": "*.json"}


def test_modelscope_wrapper_resolves_snapshot(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    module = types.ModuleType("modelscope")
    captured: dict[str, Any] = {}

    def snapshot_download(**kwargs: Any) -> Path:
        captured.update(kwargs)
        return tmp_path / "snapshot"

    module.snapshot_download = snapshot_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "modelscope", module)

    wrapper = ModelScopeModelWrapper(
        name="qwen/example",
        revision="v1",
        cache_dir="./cache",
        local_dir="./models/qwen",
        modelscope_kwargs={"allow_file_pattern": "*.json"},
    )

    assert wrapper._resolve_pretrained_path() == str(tmp_path / "snapshot")
    assert captured == {
        "model_id": "qwen/example",
        "revision": "v1",
        "cache_dir": "./cache",
        "local_dir": "./models/qwen",
        "allow_file_pattern": "*.json",
    }
