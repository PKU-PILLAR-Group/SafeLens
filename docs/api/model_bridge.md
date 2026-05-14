# Model Bridge

SafeLens' model bridge follows the same abstraction pattern that makes
TransformerLens scale across many model families: an architecture adapter maps
provider-specific module paths onto canonical components such as `resid_pre`,
`attn_out`, `mlp_out`, `q`, `k`, `v`, and `z`.

The bridge is independent of TransformerLens. It is used by Transformers-backed
wrappers after the model is loaded.

Current architecture adapters:

- `llama_like_decoder`: Qwen, Qwen2, Qwen3, LLaMA, Mistral, Mixtral, Gemma,
  OLMo, StableLM, and Yi-style `model.layers` decoders.
- `gpt2_decoder`: GPT-2 and DistilGPT2-style `transformer.h` decoders.
- `gpt_neox_decoder`: GPT-NeoX and Pythia-style `gpt_neox.layers` decoders.
- `gptj_decoder`: GPT-J-style decoder blocks.
- `gpt_neo_decoder`: GPT-Neo-style decoder blocks.
- `joint_qkv_decoder`: BLOOM and Falcon-style joint QKV decoders.
- `mpt_decoder`: MPT-style decoder blocks.
- `phi_decoder`: Phi-style decoder blocks.
- `opt_decoder`: OPT-style decoder layers.
- `bert_encoder`: BERT-style encoder layers.
- `t5_encoder_decoder`: initial T5 encoder-stack component mapping.

Attention pattern caching uses returned attention weights when available.
Attention pattern patching and raw pre-softmax score hooks use eager softmax
instrumentation. If a model runs flash attention or SDPA without a Python
`torch.softmax` call, SafeLens raises a clear error and the model should be run
with an eager attention implementation for those hooks.

List the registered architecture adapters:

```bash
safelens models list-architectures
safelens models list-architectures --json
```

::: SafeLens.utils.model_bridge
