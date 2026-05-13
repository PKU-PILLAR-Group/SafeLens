from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

from SafeLens.adapters import FlagSafeAdapter
from SafeLens.core.base import PipelineConfig
from SafeLens.pipelines.runner import PipelineRunner
from SafeLens.utils import (
    HuggingFaceModelWrapper,
    ModelScopeModelWrapper,
    TransformerLensModelWrapper,
    build_model_wrapper,
)


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
    assert rule["metadata"]["source"] == "safelens"


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


def test_build_model_wrapper_selects_transformerlens() -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "transformer_lens",
                "name": "gpt2-small",
                "dtype": "auto",
                "device": "cpu",
            }
        }
    )

    wrapper = build_model_wrapper(config.model)

    assert isinstance(wrapper, TransformerLensModelWrapper)
    assert wrapper.name == "gpt2-small"
    assert wrapper.dtype == "auto"
    assert wrapper.device == "cpu"


def test_transformerlens_wrapper_runs_with_cache(monkeypatch: MonkeyPatch) -> None:
    module = types.ModuleType("transformer_lens")

    class FakeHookedTransformer:
        def __init__(self) -> None:
            self.hooks: list[Any] = []
            self.reset_count = 0

        @classmethod
        def from_pretrained(cls, name: str, **kwargs: Any) -> FakeHookedTransformer:
            assert name == "gpt2-small"
            assert kwargs == {"device": "cpu"}
            return cls()

        def add_hook(self, name: str, hook_fn: Any) -> None:
            self.hooks.append((name, hook_fn))

        def run_with_cache(
            self,
            model_input: Any,
            names_filter: list[str] | None = None,
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            activation = {"value": 1}
            for _name, hook_fn in self.hooks:
                activation = hook_fn(activation, object())
            cache_name = (names_filter or ["blocks.0.hook_resid_pre"])[0]
            return {"input": model_input, "activation": activation}, {cache_name: activation}

        def generate(self, prompt: str, **generation_kwargs: Any) -> str:
            _ = generation_kwargs
            return prompt

        def reset_hooks(self) -> None:
            self.reset_count += 1
            self.hooks.clear()

    module.HookedTransformer = FakeHookedTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "transformer_lens", module)

    wrapper = TransformerLensModelWrapper(name="gpt2-small", dtype="auto", device="cpu")
    wrapper.add_hook(
        "blocks.0.hook_resid_pre",
        lambda **kwargs: {"value": kwargs["activation"]["value"] + 1},
    )
    output, cache = wrapper.run_with_cache(
        {"text": "hello"},
        layers=["blocks.0.hook_resid_pre"],
    )

    assert output == {"input": "hello", "activation": {"value": 2}}
    assert cache == {"blocks.0.hook_resid_pre": {"value": 2}}
    wrapper.remove_hooks()
    assert wrapper.model.reset_count == 1


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
