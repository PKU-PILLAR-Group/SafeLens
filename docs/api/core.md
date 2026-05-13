# Core

The core module defines the contracts that all methods share.

Most contributors should start with these classes:

- `ModelWrapper`: abstraction for model loading, hooks, cached inference, and generation.
- `BaseProbe`: interface for endogenous probes.
- `BaseMonitor`: interface for runtime safety monitors.
- `BaseAttributor`: interface for input or training-data attribution.
- `SafetyReport`: standard report format consumed by adapters such as FlagSafe.
- `PipelineConfig`: validated YAML configuration model.

Minimal `BaseProbe`:

```python
from collections.abc import Sequence
from typing import Any

from SafeLens.core.base import BaseProbe, Batch, ModelWrapper, ProbeResult


class AlwaysSafeProbe(BaseProbe):
    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        self.layers = list(layers)

    def detect(self, batch: Batch) -> ProbeResult:
        return ProbeResult(risk_score=0.0, critical_layers=self.layers)

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        pass

    def detach(self) -> None:
        self.layers = []
```

Minimal `BaseMonitor`:

```python
from typing import Any

from SafeLens.core.base import BaseMonitor, Batch, ModelWrapper, MonitoringSignal, SafetyReport


class AlwaysSafeMonitor(BaseMonitor):
    def start_monitoring(self, model: ModelWrapper) -> None:
        self.signals: list[MonitoringSignal] = []

    def step(self, batch: Batch, model_output: Any = None) -> MonitoringSignal:
        signal = MonitoringSignal(name="always_safe", risk_score=0.0)
        self.signals.append(signal)
        return signal

    def report(self) -> SafetyReport:
        return SafetyReport(monitoring_signals=self.signals)
```

Minimal `BaseAttributor`:

```python
from typing import Any

from SafeLens.core.base import AttributionResult, BaseAttributor, Batch


class EmptyAttributor(BaseAttributor):
    def attribute_training(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        return AttributionResult(method="empty", attribution_score=0.0)

    def attribute_input(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        return AttributionResult(method="empty", attribution_score=0.0)
```

::: SafeLens.core.base
