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
- `cache_activations`: runs a model and captures selected layer activations.
- `activation_name_for_layer`: standardizes cache names such as `layer_0`.
- `get_act_name`: TransformerLens-style shorthand names such as `("q", 2)` to
  `blocks.2.attn.hook_q`.
- `safelens_act_name`: SafeLens-style shorthand names such as `layer_2.q`.

Activation cache helpers copied in spirit from TransformerLens:

| Helper | Purpose |
| --- | --- |
| Tuple key lookup | Read `cache[("resid_pre", 0)]` or `cache[("q", 2)]`. |
| `keys_matching` / `select` | Filter activations by names or predicates. |
| `apply_to_values`, `detach`, `cpu`, `to` | Transform all cached values. |
| `remove_batch_dim` | Remove a singleton batch dimension. |
| `apply_slice_to_batch_dim` | Slice all cached activations along batch. |
| `stack_activation` | Stack one activation type across layers. |
| `accumulated_resid` | Build a logit-lens residual stream stack. |
| `decompose_resid` | Split residual stream into embed, attention, and MLP terms. |
| `stack_head_results` | Stack per-head attention result vectors. |
| `stack_neuron_results` | Stack per-neuron MLP activations. |
| `get_full_resid_decomposition` | Combine residual, head, and neuron components. |
| `apply_ln_to_stack` | Apply cached layer-norm scale when available. |
| `logit_attrs` | Attribute residual components to token directions. |

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
