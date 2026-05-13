# SafeProbe

SafeProbe is the starter architecture for SafeLens safety research workflows. It provides:

- shared contracts for probes, monitors, attribution methods, model wrappers, and reports
- a decorator-based registry so research methods can plug into a common runner
- a runnable dummy vertical slice from YAML config to JSON safety report
- a FlagSafe adapter boundary for later integration
- CI, pre-commit, tests, and MkDocs scaffolding

## Quick Start

```bash
conda create -p ./.conda python=3.10 -y
conda run -p ./.conda python -m pip install -r requirements-dev.txt
conda run -p ./.conda python -m pip install -e . --no-build-isolation
conda run -p ./.conda pytest
conda run -p ./.conda safeprobe run --config examples/config.yaml
```

The default example uses `model.source: dummy`, so it does not download a model.
Install real model loading dependencies with:

```bash
conda run -p ./.conda python -m pip install -e ".[models]"
conda run -p ./.conda python -m pip install -e ".[modelscope]"
```

## Package Layout

```text
src/SafeLens/
  core/          base contracts and registry
  probes/        probe implementations
  monitors/      safety monitor implementations
  attribution/   attribution implementations
  steering/      steering vector methods
  pipelines/     YAML-driven runner
  utils/         model wrappers and hook utilities
  adapters/      external system adapters, including FlagSafe
  app/           future demo application entry points
```

## Running a Pipeline

```bash
safeprobe run --config examples/config.yaml
```

The runner loads the configured model wrapper, instantiates registered probes, monitors, and
attributors by name, scans the dataset, writes a report, and prints the summary.

Choose the model source in YAML:

```yaml
model:
  source: huggingface
  name: Qwen/Qwen2.5-0.5B-Instruct
```

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
  cache_dir: ./.cache/modelscope
```

Built-in dummy methods are registered under:

- `dummy_probe`
- `dummy_monitor`
- `dummy_attributor`

Real methods should subclass the relevant base class and register themselves with
`@register_probe`, `@register_monitor`, or `@register_attributor`.
