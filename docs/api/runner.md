# Pipeline Runner

The pipeline runner is the executable vertical slice:

1. Load `PipelineConfig` from YAML.
2. Build the configured model wrapper.
3. Instantiate registered probes, monitors, and attributors.
4. Run each dataset item.
5. Aggregate `SafetyReport` objects into a `RunReport`.
6. Write the report JSON to `output.report_path`.

Run it with:

```bash
safelens run --config examples/config.yaml
```

Validate before running:

```bash
safelens validate --config examples/config.yaml
```

Use the runner from Python:

```python
from SafeLens.pipelines import run_from_config

report = run_from_config("examples/config.yaml")
print(report.summary)
```

::: SafeLens.pipelines.runner
