# Core

The core module defines the contracts that all methods share.

Most contributors should start with these classes:

- `ModelWrapper`: abstraction for model loading, hooks, cached inference, and generation.
- `BaseProbe`: interface for endogenous probes.
- `BaseMonitor`: interface for runtime safety monitors.
- `BaseAttributor`: interface for input or training-data attribution.
- `SafetyReport`: standard report format consumed by adapters such as FlagSafe.
- `PipelineConfig`: validated YAML configuration model.

::: SafeLens.core.base
