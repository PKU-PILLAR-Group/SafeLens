# Qwen3 Dense Support Matrix

SafeLens currently adapts Qwen3 dense decoder-only language models up to 35B
parameters. MoE, VL, and Coder variants are intentionally rejected by the Qwen3
Dense wrapper.

## Model Names

| Model family | Status | Notes |
| --- | --- | --- |
| `Qwen3-0.6B` | Supported | Dense |
| `Qwen3-1.7B` | Supported | Dense |
| `Qwen3-4B` | Supported | Dense |
| `Qwen3-8B` | Supported | Dense |
| `Qwen3-14B` | Supported | Dense |
| `Qwen3-32B` | Supported | Dense and <=35B |
| `Qwen3-30B-A3B` | Not supported | MoE |
| `Qwen3-72B` | Not supported | Above current dense adapter limit |
| Qwen3 VL or Coder variants | Not supported | Different architecture surface |

## Component Hooks

| Component | SafeLens name | TransformerLens-style name | Status |
| --- | --- | --- | --- |
| Residual stream before block | `layer_0.resid_pre` | `blocks.0.hook_resid_pre` | Supported |
| Residual stream after attention | `layer_0.resid_mid` | `blocks.0.hook_resid_mid` | Supported |
| Residual stream after block | `layer_0.resid_post` | `blocks.0.hook_resid_post` | Supported |
| Attention output | `layer_0.attn_out` | `blocks.0.hook_attn_out` | Supported |
| MLP output | `layer_0.mlp_out` | `blocks.0.hook_mlp_out` | Supported |
| Query head vector | `layer_0.q` | `blocks.0.attn.hook_q` | Supported |
| Key head vector | `layer_0.k` | `blocks.0.attn.hook_k` | Supported |
| Value head vector | `layer_0.v` | `blocks.0.attn.hook_v` | Supported |
| Attention output head vector | `layer_0.z` | `blocks.0.attn.hook_z` | Supported |
| Attention pattern | `layer_0.pattern` | `blocks.0.attn.hook_pattern` | Cache supported; patching planned |
| Attention scores | `layer_0.attn_scores` | `blocks.0.attn.hook_attn_scores` | Planned |

## Example Config

```yaml
model:
  source: qwen3_dense
  name: Qwen/Qwen3-8B
  dtype: bfloat16
  device: cuda

pipeline:
  probes:
    - name: dummy_probe
      config:
        layers:
          - layer_0.resid_pre
          - layer_0.attn_out
          - blocks.0.attn.hook_q
```
