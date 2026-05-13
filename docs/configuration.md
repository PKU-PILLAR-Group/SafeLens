# Configuration

SafeProbe pipelines are configured with YAML. A minimal config has four sections:

```yaml
model:
  source: dummy
  name: dummy
  dtype: float32

pipeline:
  risk_threshold: 0.5
  probes:
    - name: dummy_probe
      config:
        layers: [0]
  monitors: []
  attributors: []

dataset:
  - id: sample-1
    text: "Explain safety monitoring."

output:
  report_path: "./safety_scan.json"
```

## Model Sources

`model.source` controls how the model is loaded.

### Dummy

Use `dummy` for tests, CI, and architecture demos:

```yaml
model:
  source: dummy
  name: dummy
```

This path does not download any model.

### HuggingFace

Use `huggingface` to load directly through Transformers:

```yaml
model:
  source: huggingface
  name: Qwen/Qwen2.5-0.5B-Instruct
  dtype: float16
  device: cpu
  trust_remote_code: true
  cache_dir: ./.cache/huggingface
```

Install dependencies with:

```bash
python -m pip install -e ".[models]"
```

### ModelScope

Use `modelscope` to download with ModelScope first, then load the local snapshot
with Transformers:

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
  dtype: float16
  device: cpu
  trust_remote_code: true
  cache_dir: ./.cache/modelscope
  local_dir: ./models/qwen2.5-0.5b
```

Install dependencies with:

```bash
python -m pip install -e ".[modelscope]"
```

Additional ModelScope arguments can be passed through `modelscope_kwargs`:

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
  modelscope_kwargs:
    allow_file_pattern: "*.json"
```

## Method Lists

Each method is loaded from a registry by `name`:

```yaml
pipeline:
  probes:
    - name: dummy_probe
      config:
        layers: [0]
        risk_terms: ["jailbreak", "attack"]
  monitors:
    - name: dummy_monitor
      config:
        threshold: 0.5
  attributors:
    - name: dummy_attributor
      config:
        risk_terms: ["jailbreak", "attack"]
```
