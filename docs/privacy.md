# Privacy And Security

SafeLens configs, reports, and experiments can reference sensitive assets. Keep
the repository free of private or large artifacts.

Do not commit:

- API keys, access tokens, or `.env` files.
- Private prompts, private datasets, private annotations, or safety reports that
  expose user data.
- Model weights or tokenizer artifacts such as `*.pt`, `*.pth`, `*.bin`,
  `*.safetensors`, `*.gguf`, or `*.onnx`.
- Experiment directories such as `outputs/`, `checkpoints/`, `wandb/`,
  `mlruns/`, and `runs/`.

Use local ignored paths for models and generated outputs:

```yaml
model:
  source: local
  local_dir: ./models/local-causal-lm

output:
  report_path: ./outputs/safety_scan.json
```

Be careful with `trust_remote_code: true`. Only enable it for model repositories
you trust and have reviewed.
