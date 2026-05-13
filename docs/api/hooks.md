# Hooks And Activation Cache

SafeLens provides a lightweight hook layer inspired by TransformerLens, but without
requiring TransformerLens as a dependency.

Design reference:
[TransformerLens hook points](https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.hook_points.html)
and
[ActivationCache](https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.ActivationCache.html).

Core utilities:

- `ActivationCache`: dictionary-like activation store.
- `make_cache_hook`: creates a hook that captures an activation.
- `temporary_hooks`: registers hooks for one context and always removes them.
- `run_with_hooks`: runs a model with temporary hooks.
- `cache_activations`: runs a model and captures selected layer activations.
- `activation_name_for_layer`: standardizes cache names such as `layer_0`.

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
