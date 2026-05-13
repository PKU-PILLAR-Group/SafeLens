# Configuration

SafeLens pipelines are configured with YAML. A minimal config has four sections:

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

Validate a config without loading a real model:

```bash
safelens validate --config examples/config.yaml
```

Generate the JSON Schema used by editors and CI:

```bash
safelens schema --output schemas/pipeline-config.schema.json
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

### Qwen3 Dense

Use `qwen3_dense` for Qwen3 dense decoder-only models up to 35B parameters:

```yaml
model:
  source: qwen3_dense
  name: Qwen/Qwen3-8B
  dtype: bfloat16
  device: cuda
  trust_remote_code: true
```

The wrapper exposes component hooks for `resid_pre`, `resid_mid`, `resid_post`,
`attn_out`, `mlp_out`, `q`, `k`, `v`, and `z`. Supported dense sizes by name are
`0.6B`, `1.7B`, `4B`, `8B`, `14B`, and `32B`; MoE variants such as
`Qwen3-30B-A3B` are rejected.

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

### Local

Use `local` for a local Transformers-compatible model directory:

```yaml
model:
  source: local
  name: ./models/local-causal-lm
  local_dir: ./models/local-causal-lm
  dtype: float16
  device: cpu
```

Keep model directories outside git. The default `.gitignore` excludes `models/`
and common weight files.

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

## Example Configs

| File | Purpose |
| --- | --- |
| `examples/config.yaml` | Dependency-free dummy pipeline for CI and demos. |
| `examples/huggingface_config.yaml` | Direct Transformers/HuggingFace loading. |
| `examples/modelscope_config.yaml` | ModelScope snapshot download plus Transformers loading. |
| `examples/qwen3_dense_config.yaml` | Qwen3 Dense component hook examples. |
| `examples/local_model_config.yaml` | Local model directory loading. |
