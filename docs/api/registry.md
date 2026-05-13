# Registry

The registry module provides decorator-based plugin registration.

Use these decorators for new methods:

- `@register_probe("name")`
- `@register_monitor("name")`
- `@register_attributor("name")`

The pipeline runner calls `create_probe`, `create_monitor`, and
`create_attributor` to instantiate methods from YAML.

Minimal example:

```python
from collections.abc import Sequence
from typing import Any

from SafeLens.core.base import BaseProbe, Batch, ModelWrapper, ProbeResult
from SafeLens.core.registry import create_probe, register_probe


@register_probe("constant_probe")
class ConstantProbe(BaseProbe):
    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        pass

    def detect(self, batch: Batch) -> ProbeResult:
        return ProbeResult(risk_score=0.0, critical_layers=[])

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        pass

    def detach(self) -> None:
        pass


probe = create_probe("constant_probe")
```

::: SafeLens.core.registry
