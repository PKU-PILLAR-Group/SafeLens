"""YAML-driven pipeline runner."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

from SafeLens.core.base import (
    AttributionResult,
    MonitoringSignal,
    PipelineConfig,
    ProbeResult,
    RunReport,
    SafetyReport,
)
from SafeLens.core.registry import create_attributor, create_monitor, create_probe
from SafeLens.utils import build_model_wrapper


def load_builtin_methods() -> None:
    """Import built-in plugins so their registration decorators run."""
    import SafeLens.attribution.dummy  # noqa: F401
    import SafeLens.monitors.dummy  # noqa: F401
    import SafeLens.probes.dummy  # noqa: F401


def load_pipeline_config(path: str | Path) -> PipelineConfig:
    """Load and validate a YAML pipeline config."""
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return PipelineConfig.model_validate(raw)


class PipelineRunner:
    """Instantiate registered methods and execute a full safety scan."""

    def __init__(self, config: PipelineConfig) -> None:
        load_builtin_methods()
        self.config = config
        self.model = build_model_wrapper(config.model)
        self.probes = [create_probe(spec.name, spec.config) for spec in config.pipeline.probes]
        self.monitors = [
            create_monitor(spec.name, spec.config) for spec in config.pipeline.monitors
        ]
        self.attributors = [
            create_attributor(spec.name, spec.config) for spec in config.pipeline.attributors
        ]

    @classmethod
    def from_yaml(cls, path: str | Path) -> PipelineRunner:
        """Construct a runner from a YAML file."""
        return cls(load_pipeline_config(path))

    def setup(self) -> None:
        """Load the model and attach configured runtime hooks."""
        self.model.load_model()
        for probe, spec in zip(self.probes, self.config.pipeline.probes, strict=True):
            layers = spec.config.get("layers", [])
            probe.attach(self.model, layers)
        for monitor in self.monitors:
            monitor.start_monitoring(self.model)

    def run(self, dataset: Iterable[Mapping[str, Any]] | None = None) -> RunReport:
        """Run the configured safety pipeline and write a JSON report."""
        self.setup()
        try:
            batches = list(dataset if dataset is not None else self.config.dataset)
            if not batches:
                batches = [{"id": "demo", "text": "This is a benign SafeLens demo sample."}]

            reports = [self._run_one(index, batch) for index, batch in enumerate(batches)]
            run_report = RunReport(reports=reports, summary=self._summarize(reports))
            self._write_report(run_report)
            return run_report
        finally:
            for probe in self.probes:
                probe.detach()
            self.model.remove_hooks()

    def _run_one(self, index: int, batch: Mapping[str, Any]) -> SafetyReport:
        model_output, _cache = self.model.run_with_cache(batch)
        probe_results = [probe.detect(batch) for probe in self.probes]
        monitoring_signals = [monitor.step(batch, model_output) for monitor in self.monitors]
        attributions = [
            attributor.attribute_input(batch, model_output) for attributor in self.attributors
        ]
        return self._build_report(index, batch, probe_results, monitoring_signals, attributions)

    def _build_report(
        self,
        index: int,
        batch: Mapping[str, Any],
        probe_results: list[ProbeResult],
        monitoring_signals: list[MonitoringSignal],
        attributions: list[AttributionResult],
    ) -> SafetyReport:
        max_probe_score = max((result.risk_score for result in probe_results), default=0.0)
        max_monitor_score = max((signal.risk_score for signal in monitoring_signals), default=0.0)
        risk_score = max(max_probe_score, max_monitor_score)
        categories = self._collect_categories(probe_results, monitoring_signals)
        evidence_tokens = self._collect_evidence(probe_results, monitoring_signals, attributions)
        attribution_score = max((item.attribution_score for item in attributions), default=0.0)
        flagged = risk_score >= self.config.pipeline.risk_threshold or any(
            signal.triggered for signal in monitoring_signals
        )

        return SafetyReport(
            sample_id=str(batch.get("id", index)),
            flagged=flagged,
            risk_score=risk_score,
            risk_category=categories if categories else (["unknown"] if flagged else []),
            evidence_tokens=evidence_tokens,
            attribution_score=attribution_score,
            probe_results=probe_results,
            monitoring_signals=monitoring_signals,
            attributions=attributions,
            metadata={"input_keys": sorted(batch.keys())},
        )

    @staticmethod
    def _collect_categories(
        probe_results: list[ProbeResult],
        monitoring_signals: list[MonitoringSignal],
    ) -> list[str]:
        categories: set[str] = set()
        for result in probe_results:
            raw_category = result.details.get("risk_category", [])
            if isinstance(raw_category, str):
                categories.add(raw_category)
            else:
                categories.update(str(category) for category in raw_category)
        for signal in monitoring_signals:
            categories.update(signal.risk_category)
        return sorted(categories)

    @staticmethod
    def _collect_evidence(
        probe_results: list[ProbeResult],
        monitoring_signals: list[MonitoringSignal],
        attributions: list[AttributionResult],
    ) -> list[int]:
        tokens: set[int] = set()
        for result in probe_results:
            tokens.update(int(token) for token in result.details.get("evidence_tokens", []))
        for signal in monitoring_signals:
            tokens.update(signal.evidence_tokens)
        for attribution in attributions:
            tokens.update(token.token_index for token in attribution.tokens)
        return sorted(tokens)

    @staticmethod
    def _summarize(reports: list[SafetyReport]) -> dict[str, Any]:
        return {
            "samples_scanned": len(reports),
            "flagged_count": sum(1 for report in reports if report.flagged),
            "max_risk_score": max((report.risk_score for report in reports), default=0.0),
        }

    def _write_report(self, run_report: RunReport) -> None:
        path = Path(self.config.output.report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(run_report.to_dict(), indent=2), encoding="utf-8")


def run_from_config(
    config_path: str | Path,
    dataset: Iterable[Mapping[str, Any]] | None = None,
) -> RunReport:
    """Convenience function for one-shot execution."""
    return PipelineRunner.from_yaml(config_path).run(dataset=dataset)
