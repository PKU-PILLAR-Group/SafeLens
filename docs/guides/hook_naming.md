# Hook Naming Convention

SafeLens supports two naming styles.

## SafeLens Style

Use `layer_{index}.{component}`:

```text
layer_0.resid_pre
layer_0.resid_mid
layer_0.resid_post
layer_0.attn_out
layer_0.mlp_out
layer_0.q
layer_0.k
layer_0.v
layer_0.z
```

## TransformerLens Style

Use `blocks.{index}...hook_{component}`:

```text
blocks.0.hook_resid_pre
blocks.0.hook_resid_mid
blocks.0.hook_resid_post
blocks.0.hook_attn_out
blocks.0.hook_mlp_out
blocks.0.attn.hook_q
blocks.0.attn.hook_k
blocks.0.attn.hook_v
blocks.0.attn.hook_z
```

## Validation

Static validation checks Qwen3 Dense component hooks without loading the model:

```bash
safelens validate --config examples/qwen3_dense_config.yaml
```

Raw HuggingFace module names are model-specific and can only be fully checked
after the model is loaded. Use integer layer indices for portable configs when
you do not need component-level hooks.
