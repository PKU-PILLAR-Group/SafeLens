# FlagSafe Adapter

The FlagSafe adapter converts internal `SafetyReport` objects into a simple
policy-style payload.

Current output fields include:

- `action`: `BLOCK` or `ALLOW`
- `reason`: risk categories
- `evidence`: token indices or other evidence references
- `score`: risk score
- `attribution_score`: optional attribution confidence

::: SafeLens.adapters.flagsafe_adapter
