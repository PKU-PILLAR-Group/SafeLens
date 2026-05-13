"""Dummy monitor used to validate monitor integration."""

from __future__ import annotations

from typing import Any

from SafeLens.core.base import BaseMonitor, Batch, ModelWrapper, MonitoringSignal, SafetyReport
from SafeLens.core.registry import register_monitor


@register_monitor("dummy_monitor")
class DummyMonitor(BaseMonitor):
    """Simple risk-threshold monitor."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.signals: list[MonitoringSignal] = []

    def start_monitoring(self, model: ModelWrapper) -> None:
        _ = model
        self.signals.clear()

    def step(self, batch: Batch, model_output: Any = None) -> MonitoringSignal:
        threshold = float(self.config.get("threshold", 0.5))
        output_score = 0.0
        if isinstance(model_output, dict):
            output_score = float(model_output.get("risk_score", 0.0))
        risk_score = max(output_score, float(batch.get("risk_score", 0.0)))
        triggered = risk_score >= threshold

        signal = MonitoringSignal(
            name=self.name,
            risk_score=risk_score,
            triggered=triggered,
            risk_category=(
                self.config.get("risk_category", ["policy_violation"]) if triggered else []
            ),
            evidence_tokens=list(batch.get("evidence_tokens", [])),
            details={"threshold": threshold},
        )
        self.signals.append(signal)
        return signal

    def report(self) -> SafetyReport:
        max_risk = max((signal.risk_score for signal in self.signals), default=0.0)
        categories = sorted(
            {category for signal in self.signals for category in signal.risk_category}
        )
        evidence = sorted({token for signal in self.signals for token in signal.evidence_tokens})
        return SafetyReport(
            flagged=any(signal.triggered for signal in self.signals),
            risk_score=max_risk,
            risk_category=categories,
            evidence_tokens=evidence,
            monitoring_signals=list(self.signals),
        )
