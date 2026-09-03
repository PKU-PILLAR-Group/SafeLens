# SafeLens Supported Models

This document summarizes the model backends and model families supported by the
current SafeLens codebase. It distinguishes between models with explicit
SafeLens architecture support and models that can be loaded through generic
Transformers-compatible backends.

## Backend Summary

| `model.source` | Aliases | What it supports | Remote download | Local path |
| --- | --- | --- | --- | --- |
| `qwen3_dense` | `qwen3`, `qwen3-dense` | Qwen3 dense language models up to 35B with explicit component hooks | Yes | No |
| `transformer_lens` | `transformerlens`, `tl`, `hooked_transformer` | TransformerLens-compatible model names and SafeLens architecture bridge families | Yes | Yes |
| `huggingface` | `hf` | Generic HuggingFace Transformers causal language models | Yes | No |
| `modelscope` | `ms` | ModelScope snapshot download, then Transformers loading | Yes | No |
| `local` | none | Local Transformers-compatible model directories | No | Yes |
| `dummy` | `mock`, `none` | In-memory test/CI model | No | No |

## Explicit Qwen3 Dense Support

Use `model.source: qwen3_dense` for the dedicated Qwen3 dense adapter.

Supported model pattern:

```text
Qwen/Qwen3-{0.6,1.7,4,8,14,32}B
```

Examples:

- `Qwen/Qwen3-0.6B`
- `Qwen/Qwen3-1.7B`
- `Qwen/Qwen3-4B`
- `Qwen/Qwen3-8B`
- `Qwen/Qwen3-14B`
- `Qwen/Qwen3-32B`

Unsupported by the dedicated Qwen3 dense adapter:

- Qwen3 models above 35B, such as `Qwen/Qwen3-72B`
- Qwen3 MoE/routed models, such as `Qwen/Qwen3-30B-A3B`
- Qwen3 VL, Coder, and other non-dense variants

The dedicated Qwen3 dense adapter exposes component-level hooks such as
`resid_pre`, `resid_mid`, `resid_post`, `attn_out`, `mlp_out`, `pre`,
`pre_linear`, `post`, `q`, `k`, `v`, `z`, `result`, `pattern`, and
`attn_scores`.

## TransformerLens-Compatible Support

Use `model.source: transformer_lens` for the SafeLens TransformerLens-compatible
adapter. This adapter does not depend on the TransformerLens runtime; it uses
SafeLens' own Transformers-based wrapper and architecture bridge.

The current vendored TransformerLens official-name list contains 247 model
names, plus 37 common aliases. Representative supported families include:

- GPT-2 and distilGPT-2: `gpt2`, `gpt2-medium`, `gpt2-large`, `gpt2-xl`,
  `distilgpt2`, `gpt2-small`
- GPT-J, GPT-Neo, GPT-NeoX, and Pythia: `EleutherAI/gpt-j-6B`,
  `EleutherAI/gpt-neo-*`, `EleutherAI/gpt-neox-20b`,
  `EleutherAI/pythia-*`, `pythia-70m`, `pythia-1b`, `pythia-12b`
- OPT, BLOOM, Falcon, MPT, and BigCode-style decoder models:
  `facebook/opt-*`, `bigscience/bloom-*`, `bigcode/santacoder`
- LLaMA-like decoder families: LLaMA 1/2/3, CodeLlama, Mistral, Mixtral,
  Qwen/Qwen2/Qwen2.5/Qwen3, Gemma, OLMo, StableLM, Yi, Phi, Apertus, and
  GPT-OSS-style models where the architecture bridge recognizes the model type
- Qwen MoE/routed models through the TransformerLens-compatible bridge:
  `Qwen/Qwen3-30B-A3B`, `Qwen/Qwen3-235B-A22B`
- BERT-like encoders: `google-bert/bert-*`, `FacebookAI/roberta-*`,
  `distilbert/distilbert-*`
- T5 encoder-decoder models: `google-t5/t5-small`, `google-t5/t5-base`,
  `google-t5/t5-large`
- Audio encoders: `facebook/wav2vec2-*`, `facebook/hubert-*`
- Mamba/SSM models: `state-spaces/mamba-*`,
  `mistralai/Mamba-Codestral-*`
- TransformerLens native educational checkpoints and aliases such as
  `solu-1l`, `solu-2l`, `gelu-2l`, `attn-only-2l`, `attn-only-3l`,
  `redwood_attn_2l`, and `othello-gpt`

Common aliases recognized by the compatibility layer include:

```text
gpt2-small, gpt2-xs, gpt-j, gptj, gpt-neo, gpt-neox, neox, pythia, opt,
bloom-560m, llama-7b, llama-13b, llama-30b, llama-65b, mistral-7b, mixtral,
mamba-130m, mamba-codestral, qwen3-8b, qwen3-14b, gemma-2b, gemma-7b,
phi-2, tiny-stories-1m, solu-1l, solu-2l, gelu-2l, attn-only-2l,
attn-only-3l, redwood_attn_2l, othello-gpt, bert-base-uncased, roberta-base,
distilbert-base-uncased, t5-small, hubert-base-ls960, wav2vec2-base
```

## Generic Transformers Backends

## Gemma Scope 2 SAE intervention

The Local Explorer has an explicit Gemma Scope 2 SAE profile for
`google/gemma-3-270m-it`. It uses the `gemma-scope-2-270m-it-res` SAELens
release on the `resid_post` site at layers 5, 9, 12, and 15 (the initial UI
checkpoint is the 16k, L0-small variant). This profile requires the matching
Gemma base model and the optional `sae` dependency; Gemma Scope dictionaries
must not be used with Qwen or another base model.

## Gemma-2-9B-it Neuronpedia SAE steering

The Explorer conversation `SAE` workbench also supports the public
Neuronpedia-style steering presets for `google/gemma-2-9b-it`. The presets use
the canonical Gemma Scope residual-stream dictionaries at layers 9, 20, and 31
and keep the existing **Find active features** scan available for prompt-driven
feature discovery. Select `gemma-2-9b-it` in the chat model picker, run a prompt,
and open `SAE`; there is no separate steering page.

The real-model installation requires the `models` and `sae` extras in addition
to `explorer`. Checkpoint paths, lazy downloads, GPU placement, and the ten
available modes (Cats, Chinese, Pirate, Shakespeare, Poetry, San Francisco,
Positivity, Negativity, Music, and British English) are documented in the
[Local Explorer setup guide](explorer_setup.md) and [Gemma Scope intervention
reference](gemma_scope_intervention.md).

The `huggingface`, `modelscope`, and `local` sources can load many
Transformers-compatible models beyond the explicit lists above.

### Local Explorer provider selection

Explorer workers use a complete local snapshot first. When the model is
`google/gemma-3-270m-it` or `google/gemma-3-12b-it` and the ModelScope package
is installed, `SAFELENS_EXPLORER_MODEL_SOURCE=auto` selects ModelScope instead
of starting a Hugging Face download. Set the variable to `huggingface` or
`modelscope` to force a provider. ModelScope snapshots are stored in
`MODELSCOPE_CACHE` (or `SAFELENS_EXPLORER_MODELSCOPE_CACHE`).

Use these when:

- The model is a standard Transformers causal LM and can be loaded by
  `AutoModelForCausalLM`.
- The model is hosted on HuggingFace Hub (`huggingface`) or ModelScope
  (`modelscope`).
- The model is already downloaded in a local Transformers directory (`local`).

Component-level hooks are best supported when the loaded architecture is
recognized by SafeLens' architecture bridge. Otherwise, module-name hooks and
integer decoder-layer hooks may still work, but high-level component names may
be limited.

## Architecture Bridge Families

SafeLens currently includes architecture adapters for:

- `llama_like_decoder`
- `routed_moe_decoder`
- `apertus_decoder`
- `gpt_oss_decoder`
- `gpt2_decoder`
- `gpt_bigcode_decoder`
- `gpt_neox_decoder`
- `gptj_decoder`
- `gpt_neo_decoder`
- `joint_qkv_decoder`
- `mpt_decoder`
- `phi_decoder`
- `opt_decoder`
- `bert_encoder`
- `distilbert_encoder`
- `t5_encoder_decoder`
- `audio_encoder`
- `mamba_ssm`
- `mamba2_ssm`

## How To Query Support

From the CLI:

```bash
safelens models list-supported
safelens models list-supported --json
safelens models list-architectures --json
safelens models list-transformerlens --json
safelens inspect-model --model Qwen/Qwen3-8B --json
safelens inspect-model --model gpt2 --json
```

From Python:

```python
from SafeLens.utils.model_wrapper import register_builtin_model_adapters
from SafeLens.utils import get_model_adapter_registry

register_builtin_model_adapters()
registry = get_model_adapter_registry()

print(registry.list_supported())
print(registry.inspect_model("Qwen/Qwen3-8B"))
print(registry.inspect_model("gpt2"))
```

## Notes

- "Supported" means the registry and wrappers know how to route, inspect, and
  load the model family. Actual runtime success still depends on installed
  dependencies, available memory, model access permissions, and provider
  availability.
- Attention `pattern` and `attn_scores` hooks require eager attention
  instrumentation; flash/SDPA execution paths may need an eager attention
  implementation.
- Attention `result` hooks are implemented by deriving per-head `z @ W_O`
  results and writing patched head-result deltas back to the merged attention
  output.
