# TransformerLens Support

SafeLens vendors TransformerLens' official model-name table for static
inspection and adapter selection. Runtime loading stays inside SafeLens through
`TransformerLensCompatibleModelWrapper`, which uses Transformers auto classes
and SafeLens architecture adapters. It does not import `transformer-lens`.

List the vendored names:

```bash
safelens models list-transformerlens
safelens models list-transformerlens --json
```

Use the compatibility adapter:

```yaml
model:
  source: transformer_lens
  name: gpt2
```

Component hooks are resolved by `SafeLens.utils.model_bridge`. The current
bridge covers GPT-2, GPT-J, GPT-Neo, GPT-NeoX/Pythia, BLOOM/Falcon, MPT, Phi,
OPT, BERT, T5 encoder-stack, and LLaMA-like decoder families including
Qwen/Qwen2/Qwen3, LLaMA, Mistral, Mixtral, Gemma, OLMo, StableLM, and Yi.

::: SafeLens.utils.transformer_lens_support
