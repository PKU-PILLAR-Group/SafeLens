# How To Add A New Probe

A probe inspects model activations or batch content and returns a `ProbeResult`.
Register it once, then reference it from YAML by name.

```python
from collections.abc import Sequence
from typing import Any

from SafeLens.core.base import BaseProbe, Batch, ModelWrapper, ProbeResult
from SafeLens.core.registry import register_probe


@register_probe("keyword_probe")
class KeywordProbe(BaseProbe):
    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        self.layers = list(layers)

    def detect(self, batch: Batch) -> ProbeResult:
        text = str(batch.get("text", "")).lower()
        risk = 1.0 if "jailbreak" in text else 0.0
        return ProbeResult(
            risk_score=risk,
            critical_layers=self.layers,
            details={"risk_category": ["jailbreak"] if risk else []},
        )

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        self.config["last_intervention_scale"] = scale

    def detach(self) -> None:
        self.layers = []
```

Use it in YAML:

```yaml
pipeline:
  probes:
    - name: keyword_probe
      config:
        layers: [0, 1]
```

Validation catches unregistered names:

```bash
safelens validate --config examples/config.yaml
```
