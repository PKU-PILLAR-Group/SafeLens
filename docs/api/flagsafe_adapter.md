# FlagSafe Adapter

The FlagSafe adapter converts internal `SafetyReport` objects into a simple
policy-style payload.

Current output fields include:

- `action`: `BLOCK` or `ALLOW`
- `reason`: risk categories
- `evidence`: token indices or other evidence references
- `score`: risk score
- `attribution_score`: optional attribution confidence

Minimal example:

```python
from SafeLens.adapters import FlagSafeAdapter
from SafeLens.core.base import SafetyReport

rule = FlagSafeAdapter.to_flagsafe_rule(
    SafetyReport(flagged=True, risk_score=0.9, risk_category=["jailbreak"])
)
```

::: SafeLens.adapters.flagsafe_adapter
