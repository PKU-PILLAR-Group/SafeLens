# Hooks And Activation Cache

SafeLens provides a lightweight hook layer inspired by TransformerLens, but without
requiring TransformerLens as a dependency.

Design reference:
[TransformerLens hook points](https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.hook_points.html)
and
[ActivationCache](https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.ActivationCache.html).

Core utilities:

- `HookPoint`: dependency-free identity hook point with temporary/permanent hooks,
  context storage, prepend ordering, direction filters, and layer-name parsing.
- `HookedRoot`: root-level manager for named hook points, temporary hooks, and
  activation caching hooks.
- `ActivationCache`: dictionary-like activation store.
- `make_cache_hook`: creates a hook that captures an activation.
- `temporary_hooks`: registers hooks for one context and always removes them.
- `run_with_hooks`: runs a model with temporary hooks.
- `HookedRoot.run_with_cache`: runs a callable while temporarily caching named
  hook-point activations.
- `HookedRoot.cache_all` / `cache_some`: install persistent cache hooks until
  `reset_hooks()` removes them.
- `cache_activations`: runs a model and captures selected layer activations.
- `activation_name_for_layer`: standardizes cache names such as `layer_0`.
- `get_act_name`: TransformerLens-style shorthand names such as `("q", 2)` to
  `blocks.2.attn.hook_q`, including layer-type aliases such as `a`, `m`, and
  `b`.
- `safelens_act_name`: SafeLens-style shorthand names such as `layer_2.q`.

Cache hooks follow TransformerLens' `pos_slice` conventions: head-vector
activations such as `hook_q`, `hook_k`, `hook_v`, `hook_z`, and `hook_result`
slice the `[pos]` axis before the head axis, while residual streams and
attention patterns/scores slice the destination-position axis.
ActivationCache decomposition helpers use the same negative-dimension position
semantics, so position slicing still targets `[pos]` after `remove_batch_dim`.

Activation cache helpers copied in spirit from TransformerLens:

| Helper | Purpose |
| --- | --- |
| `cache_dict`, `has_embed`, `has_pos_embed` | TransformerLens-compatible cache mapping and embed-presence attributes. |
| Tuple key lookup | Read `cache[("resid_pre", 0)]` or `cache[("q", 2)]`. |
| `keys_matching` / `select` | Filter activations by names or predicates. |
| `apply_to_values`, `detach`, `cpu`, `to` | Transform all cached values; `to` mutates in place like TransformerLens. |
| `remove_batch_dim` | Remove a singleton batch dimension. |
| `apply_slice_to_batch_dim` | Slice all cached activations along batch. |
| `stack_activation` | Stack one activation type across layers. |
| `accumulated_resid` | Build a logit-lens residual stream stack. |
| `decompose_resid` | Split residual stream into embed, attention, and MLP terms. |
| `stack_head_results` | Stack per-head attention result vectors. |
| `compute_head_results` | Compute per-head result vectors from cached `z` and model `W_O`. |
| `stack_neuron_results` | Stack per-neuron MLP residual contributions when `model.W_out` is available, optionally projected onto output directions. |
| `get_full_resid_decomposition` | Stack head results, neuron/MLP terms, embeddings, optional model bias, and optional output-direction projections. |
| `apply_ln_to_stack` | Apply cached normalization scale with optional batch/position slicing, LN centering, or recomputed final LN for logit lens. |
| `logit_attrs` | Attribute residual components to token directions, token strings, or logit differences. |

Example:

```python
from SafeLens.core.hooks import cache_activations
from SafeLens.core.base import ModelLoadConfig
from SafeLens.utils import build_model_wrapper

model = build_model_wrapper(ModelLoadConfig(source="dummy", name="dummy"))
output, cache = cache_activations(model, {"text": "hello"}, layers=[0])

activation = cache["layer_0"]
```

::: SafeLens.core.hooks
