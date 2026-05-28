# Model Wrapper

Model wrappers isolate the rest of the pipeline from model loading details.

Available wrappers:

- `DummyModelWrapper`: test and CI wrapper with no external dependencies.
- `HuggingFaceModelWrapper`: loads models directly with Transformers.
- `LocalModelWrapper`: loads a local Transformers-compatible model directory.
- `Qwen3DenseModelWrapper`: adapts Qwen3 dense models up to 35B with SafeLens
  component hooks for residual streams, MLP output, attention output, and
  `q/k/v/z` head vectors.
- `TransformerLensCompatibleModelWrapper`: independent Transformers-based
  adapter for model families mirrored from the TransformerLens official support
  table. It uses SafeLens architecture adapters for component hooks and does
  not import or require TransformerLens.
- `ModelScopeModelWrapper`: downloads a ModelScope snapshot, then loads it with
  Transformers.

Select a wrapper through `model.source` in the YAML config:

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
```

Adapters also declare static capabilities through `ModelAdapterRegistry`.

```bash
safelens models list-supported --json
```

Static inspection does not load model weights:

```bash
safelens inspect-model --model Qwen/Qwen3-8B --json
safelens inspect-model --model gpt2 --json
safelens models list-transformerlens --json
```

Minimal Python usage:

```python
from SafeLens.core.base import ModelLoadConfig
from SafeLens.utils import build_model_wrapper

model = build_model_wrapper(ModelLoadConfig(source="dummy", name="dummy"))
model.load_model()
output, cache = model.run_with_cache({"text": "hello"}, layers=[0])
```

Transformers-backed wrappers additionally accept TransformerLens-style cache
options: `names_filter` expands over supported hook names, `pos_slice` slices
the position axis before storage, `detach`/`clone`/`device` prepare cached
activations for memory-friendly analysis, `remove_batch_dim` removes a singleton
batch axis from cached activations, and `return_cache_object=True` returns an
`ActivationCache`.
When called with token ids or text directly, `run_with_cache(tokens)` follows
TransformerLens and caches all architecture-bridge component hooks by default,
returning an `ActivationCache`. Pre-softmax `attn_scores` are intentionally not
enabled by the default cache because many Transformers models use SDPA/flash
paths rather than a Python `torch.softmax`; request them explicitly with
`names_filter` when an eager attention path is available. Mapping inputs keep
the older SafeLens default of no implicit cache hooks; pass `cache_all=True` to
opt into the same component cache.
TransformerLens-style attention `result` names are supported when the
architecture exposes `z` and `W_O`; patching them writes the summed per-head
result delta back to the merged attention output.

```python
output, cache = model.run_with_cache(
    {"text": "hello"},
    names_filter=lambda name: name.endswith("hook_resid_post"),
    pos_slice=-1,
    device="cpu",
    return_cache_object=True,
    remove_batch_dim=True,
)

tokens = model.to_tokens("hello")
logits, cache = model.run_with_cache(tokens)
resid_pre = cache["resid_pre", 0]
logits, cache = model.run_with_cache(tokens, names_filter="blocks.0.hook_resid_post")
raw_output, cache = model.run_with_cache(tokens, return_type="model_output")
raw_output, full_cache = model.run_with_cache({"input_ids": tokens}, cache_all=True)
```

The same wrappers can install persistent cache hooks, matching
TransformerLens' `cache_all()` and `cache_some()` workflows. These hooks are
permanent by default, so a plain `reset_hooks()` keeps them active while
clearing temporary hooks; use `reset_hooks(including_permanent=True)` or
`remove_hooks()` to stop caching.

```python
cache = model.cache_some(lambda name: name.endswith("hook_resid_post"))
model(tokens)
resid_post = cache["resid_post", 0]
model.reset_hooks(including_permanent=True)
```

Transformers-backed wrappers support a TransformerLens-style temporary hook
entrypoint. `run_with_hooks()` and direct calls such as `model(tokens)` do not
install default cache hooks; use `run_with_cache()` when activations should be
stored. Persistent hooks registered with `add_hook()` can be cleared with either
`reset_hooks()` or `remove_hooks()`. Like TransformerLens, `add_perma_hook()`
registers hooks that survive a default `reset_hooks()` call; pass
`including_permanent=True` or call `remove_hooks()` to clear them. The `hooks()`
context manager installs temporary hooks around arbitrary wrapper calls.

```python
logits = model.run_with_hooks(
    tokens,
    fwd_hooks=[("blocks.0.hook_resid_post", my_hook)],
)
raw_output = model.run_with_hooks(tokens, fwd_hooks=[], return_type="model_output")
logits = model(tokens)
model.add_perma_hook("blocks.0.hook_resid_post", debug_hook)
model.reset_hooks()
model.reset_hooks(including_permanent=True)
```

Transformers-backed wrappers also expose common TransformerLens-style text and
attribution helpers when a tokenizer or output embedding is available:

```python
tokens = model.to_tokens("hello", prepend_bos=False)
batch_tokens = model.to_tokens(["short", "longer"])
text = model.to_string(tokens)
texts = model.to_string([[1, 2], [3, 4]])
pieces = model.to_str_tokens("hello")
token_id = model.to_single_token(" hello")
token_text = model.to_single_str_token(token_id)
position = model.get_token_position(" hello", "well hello there")
directions = model.tokens_to_residual_directions(tokens)
single_direction = model.tokens_to_residual_directions(" hello")
```

The same wrappers expose a lightweight TransformerLens-style `cfg` view for
common analysis loops:

```python
cfg = model.cfg
for layer in range(cfg.n_layers):
    for head in range(cfg.n_heads):
        ...
```

For supported Transformers layouts, the wrapper exposes TransformerLens-shaped
weight matrices. Split and joint-QKV attention projections are normalized into
the same shapes, including GPT-2-style `Conv1D` packed columns and
GPT-NeoX/Pythia-style packed rows:

```python
W_E = model.W_E      # [vocab, d_model]
W_U = model.W_U      # [d_model, vocab]
W_pos = model.W_pos  # [pos, d_model], when the architecture has learned positions
W_Q = model.W_Q  # [layer, head, d_model, d_head]
W_K = model.W_K
W_V = model.W_V
W_O = model.W_O  # [layer, head, d_head, d_model]
W_in = model.W_in    # [layer, d_model, d_mlp]
W_out = model.W_out  # [layer, d_mlp, d_model]
```

::: SafeLens.utils.model_wrapper
