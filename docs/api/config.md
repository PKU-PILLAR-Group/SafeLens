# Config Validation

The config module validates YAML pipeline files without loading real models.
Use it in CI, examples, and local development before running expensive model
downloads.

Minimal example:

```python
from SafeLens.config import config_summary, validate_pipeline_config_file

config = validate_pipeline_config_file("examples/config.yaml")
print(config_summary(config))
```

Generate the JSON Schema:

```python
from SafeLens.config import write_pipeline_config_json_schema

write_pipeline_config_json_schema("schemas/pipeline-config.schema.json")
```

::: SafeLens.config
