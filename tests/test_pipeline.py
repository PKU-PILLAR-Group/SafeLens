from __future__ import annotations

import json
import sys
import types
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch

from SafeLens.adapters import FlagSafeAdapter
from SafeLens.core.base import (
    AttributionResult,
    BaseAttributor,
    Batch,
    LayerRef,
    ModelWrapper,
    PipelineConfig,
)
from SafeLens.core.registry import register_attributor
from SafeLens.pipelines.runner import PipelineRunner
from SafeLens.probes.linear import LinearProbe
from SafeLens.utils import (
    HuggingFaceModelWrapper,
    ModelScopeModelWrapper,
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


def test_pipeline_runner_calls_attributor_lifecycle(tmp_path: Path) -> None:
    events: list[str] = []

    @register_attributor("lifecycle_test_attributor", replace=True)
    class LifecycleTestAttributor(BaseAttributor):
        def attach(self, model: ModelWrapper) -> None:
            events.append(f"attach:{type(model).__name__}")

        def detach(self) -> None:
            events.append("detach")

        def attribute_training(self, batch: Batch, model_output: Any = None) -> AttributionResult:
            _ = batch, model_output
            return AttributionResult(method=self.name, attribution_score=0.0)

        def attribute_input(self, batch: Batch, model_output: Any = None) -> AttributionResult:
            _ = batch, model_output
            events.append("attribute")
            return AttributionResult(method=self.name, attribution_score=0.0)

    config = PipelineConfig.model_validate(
        {
            "model": {"name": "dummy"},
            "pipeline": {"attributors": [{"name": "lifecycle_test_attributor"}]},
            "dataset": [{"id": "sample", "text": "hello"}],
            "output": {"report_path": str(tmp_path / "report.json")},
        }
    )

    PipelineRunner(config).run()

    assert events == ["attach:DummyModelWrapper", "attribute", "detach"]


def test_dummy_probe_reports_string_component_layers(tmp_path: Path) -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {"name": "dummy"},
            "pipeline": {
                "probes": [
                    {
                        "name": "dummy_probe",
                        "config": {"layers": ["layer_0.resid_pre"]},
                    }
                ],
            },
            "dataset": [{"id": "sample", "text": "hello"}],
            "output": {"report_path": str(tmp_path / "report.json")},
        }
    )

    report = PipelineRunner(config).run()

    assert report.reports[0].probe_results[0].critical_layers == ["layer_0.resid_pre"]


def test_linear_probe_trains_from_feature_examples(tmp_path: Path) -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {"name": "dummy"},
            "pipeline": {
                "risk_threshold": 0.5,
                "probes": [
                    {
                        "name": "linear_probe",
                        "config": {
                            "layers": [0],
                            "threshold": 0.5,
                            "train_data": [
                                {"features": [2.0, 2.0], "label": 1},
                                {"features": [1.0, 2.0], "label": 1},
                                {"features": [-2.0, -2.0], "label": 0},
                                {"features": [-1.0, -2.0], "label": 0},
                            ],
                        },
                    }
                ],
            },
            "dataset": [
                {"id": "safe", "features": [-3.0, -1.0]},
                {"id": "unsafe", "features": [3.0, 1.0]},
            ],
            "output": {"report_path": str(tmp_path / "report.json")},
        }
    )

    report = PipelineRunner(config).run()

    assert [item.flagged for item in report.reports] == [False, True]
    assert report.reports[0].probe_results[0].details["method"] == "linear_probe"
    assert report.reports[1].probe_results[0].details["trained"] is True
    assert report.reports[1].probe_results[0].details["training_loss"] < 0.7


def test_linear_probe_uses_explicit_weights(tmp_path: Path) -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {"name": "dummy"},
            "pipeline": {
                "risk_threshold": 0.5,
                "probes": [
                    {
                        "name": "linear_probe",
                        "config": {"weights": [1.0, 0.0], "bias": 0.0},
                    }
                ],
            },
            "dataset": [
                {"id": "negative", "features": [-2.0, 5.0]},
                {"id": "positive", "features": [2.0, -5.0]},
            ],
            "output": {"report_path": str(tmp_path / "report.json")},
        }
    )

    report = PipelineRunner(config).run()

    assert report.reports[0].probe_results[0].risk_score < 0.5
    assert report.reports[1].probe_results[0].risk_score > 0.5


def test_linear_probe_can_train_from_pipeline_dataset(tmp_path: Path) -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {"name": "dummy"},
            "pipeline": {
                "risk_threshold": 0.5,
                "probes": [
                    {
                        "name": "linear_probe",
                        "config": {
                            "train_from_dataset": True,
                            "threshold": 0.5,
                        },
                    }
                ],
            },
            "dataset": [
                {"id": "safe-train", "features": [-2.0, -2.0], "label": 0},
                {"id": "safe-test", "features": [-3.0, -1.0], "label": 0},
                {"id": "unsafe-train", "features": [2.0, 2.0], "label": 1},
                {"id": "unsafe-test", "features": [3.0, 1.0], "label": 1},
            ],
            "output": {"report_path": str(tmp_path / "report.json")},
        }
    )

    report = PipelineRunner(config).run()

    assert report.summary["flagged_count"] == 2
    assert report.reports[0].probe_results[0].details["trained"] is True
    assert report.reports[0].probe_results[0].details["training_loss"] < 0.7


def test_linear_probe_uses_train_and_eval_splits(tmp_path: Path) -> None:
    config = PipelineConfig.model_validate(
        {
            "model": {"name": "dummy"},
            "pipeline": {
                "risk_threshold": 0.5,
                "probes": [
                    {
                        "name": "linear_probe",
                        "config": {
                            "train_from_dataset": True,
                            "train_split": "train",
                            "eval_split": "test",
                            "threshold": 0.5,
                        },
                    }
                ],
            },
            "dataset": [
                {"id": "safe-train", "features": [-2.0, -2.0], "label": 0, "split": "train"},
                {"id": "unsafe-train", "features": [2.0, 2.0], "label": 1, "split": "train"},
                {"id": "safe-test", "features": [-3.0, -1.0], "label": 0, "split": "test"},
                {"id": "unsafe-test", "features": [3.0, 1.0], "label": 1, "split": "test"},
            ],
            "output": {"report_path": str(tmp_path / "report.json")},
        }
    )

    report = PipelineRunner(config).run()

    assert [item.sample_id for item in report.reports] == ["safe-test", "unsafe-test"]
    assert [item.flagged for item in report.reports] == [False, True]


def test_linear_probe_can_train_from_text_dataset_activations() -> None:
    dataset = [
        {"id": "safe-train", "text": "safe example", "label": 0},
        {"id": "safe-test", "text": "another safe example", "label": 0},
        {"id": "unsafe-train", "text": "unsafe example", "label": 1},
        {"id": "unsafe-test", "text": "another unsafe example", "label": 1},
    ]
    model = _TextActivationModel()
    probe = LinearProbe(
        {
            "train_from_dataset": True,
            "layers": ["layer_0.resid_post"],
            "threshold": 0.5,
        }
    )

    probe.set_dataset(dataset)
    probe.attach(model, ["layer_0.resid_post"])

    results = []
    for row in dataset:
        model.run_with_cache(row)
        results.append(probe.detect(row))

    assert [result.risk_score >= 0.5 for result in results] == [False, False, True, True]
    assert results[0].details["feature_source"] == "activation"
    assert results[0].details["trained"] is True


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


class _Handle:
    def remove(self) -> None:
        return None


class _TextActivationModel(ModelWrapper):
    device = "cpu"

    def __init__(self) -> None:
        self._hooks: list[tuple[LayerRef, Any]] = []

    def load_model(self) -> _TextActivationModel:
        return self

    def add_hook(self, layer: LayerRef, hook_fn: Any) -> _Handle:
        self._hooks.append((layer, hook_fn))
        return _Handle()

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        _ = kwargs
        selected_layers = list(layers or [layer for layer, _hook in self._hooks])
        text = str(batch.get("text", ""))
        activation = [2.0, 2.0] if "unsafe" in text else [-2.0, -2.0]
        cache = {str(layer): activation for layer in selected_layers}
        for layer, hook in self._hooks:
            if layer in selected_layers:
                hook(activation=activation, layer=layer)
        return {"text": text}, cache

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        _ = generation_kwargs
        return prompt

    def remove_hooks(self) -> None:
        self._hooks.clear()


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
