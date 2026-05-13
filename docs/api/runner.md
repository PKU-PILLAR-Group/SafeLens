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
safeprobe run --config examples/config.yaml
```

::: SafeLens.pipelines.runner
