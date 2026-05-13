# SafeProbe

SafeProbe is the infrastructure layer for SafeLens safety experiments. It gives the
team a shared contract for model loading, probes, monitors, attribution methods,
pipeline execution, report generation, and future FlagSafe integration.

The first working vertical slice is intentionally small: it uses a dummy model and
dummy safety methods so the architecture can be tested without downloading a real
model.

## What Is Included

- Core abstract interfaces for `ModelWrapper`, `BaseProbe`, `BaseMonitor`, and
  `BaseAttributor`.
- Serializable report models such as `ProbeResult`, `MonitoringSignal`,
  `AttributionResult`, `SafetyReport`, and `RunReport`.
- A plugin registry for loading probes, monitors, and attributors by name.
- A YAML-driven pipeline runner exposed through `safeprobe run`.
- Model loading wrappers for dummy, HuggingFace, and ModelScope sources.
- A FlagSafe adapter boundary for converting internal reports to policy payloads.
- Tests, Ruff, mypy, pre-commit, GitHub Actions, and MkDocs configuration.

## Quick Start

Run the dependency-free dummy pipeline:

```bash
safeprobe run --config examples/config.yaml
```

The command writes `safety_scan.json` and prints a summary like:

```json
{
  "samples_scanned": 2,
  "flagged_count": 1,
  "max_risk_score": 1.0
}
```

## Next Steps

- Read [Configuration](configuration.md) to choose `dummy`, `huggingface`, or
  `modelscope` model sources.
- Read [Development](development.md) to add a new probe, monitor, or attributor.
- Read the API reference for the exact class contracts.
