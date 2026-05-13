# Development

This page describes how to add a new method without changing the pipeline runner.

## Add A Probe

Create a class that subclasses `BaseProbe` and register it with a unique name:

```python
from collections.abc import Sequence
from typing import Any

from SafeLens.core.base import BaseProbe, Batch, ModelWrapper, ProbeResult
from SafeLens.core.registry import register_probe


@register_probe("linear_probe")
class LinearProbe(BaseProbe):
    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        ...

    def detect(self, batch: Batch) -> ProbeResult:
        return ProbeResult(risk_score=0.0, critical_layers=[])

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        ...

    def detach(self) -> None:
        ...
```

Then reference it in YAML:

```yaml
pipeline:
  probes:
    - name: linear_probe
      config:
        layers: [12, 18]
```

## Add A Monitor

Monitors subclass `BaseMonitor` and emit `MonitoringSignal` objects from `step`.
Use monitors for generation-time or per-batch checks such as entropy, refusal
signals, or policy classifier scores.

## Add An Attributor

Attributors subclass `BaseAttributor` and return `AttributionResult`. They can
attribute either input tokens or training examples.

## Run Checks

Use the same commands as CI:

```bash
ruff check .
mypy src tests examples
pytest -q
mkdocs build --strict
```
