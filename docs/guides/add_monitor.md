# How To Add A New Monitor

A monitor inspects each batch or generation step and emits a `MonitoringSignal`.
Use monitors for runtime checks such as entropy, refusal state, classifier
scores, or streaming safety policies.

```python
from typing import Any

from SafeLens.core.base import BaseMonitor, Batch, ModelWrapper, MonitoringSignal, SafetyReport
from SafeLens.core.registry import register_monitor


@register_monitor("threshold_monitor")
class ThresholdMonitor(BaseMonitor):
    def start_monitoring(self, model: ModelWrapper) -> None:
        self.signals: list[MonitoringSignal] = []

    def step(self, batch: Batch, model_output: Any = None) -> MonitoringSignal:
        risk = float(batch.get("risk_score", 0.0))
        threshold = float(self.config.get("threshold", 0.5))
        signal = MonitoringSignal(
            name=self.name,
            risk_score=risk,
            triggered=risk >= threshold,
            risk_category=["policy_violation"] if risk >= threshold else [],
        )
        self.signals.append(signal)
        return signal

    def report(self) -> SafetyReport:
        return SafetyReport(
            flagged=any(signal.triggered for signal in self.signals),
            monitoring_signals=self.signals,
        )
```

Use it in YAML:

```yaml
pipeline:
  monitors:
    - name: threshold_monitor
      config:
        threshold: 0.7
```
