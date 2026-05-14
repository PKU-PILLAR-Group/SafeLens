# How To Add A New Model Adapter

A model adapter implements the `ModelWrapper` contract. It should hide loading,
tokenization, hook registration, cached inference, and generation details from
probes and monitors.

Minimal adapter skeleton:

```python
from collections.abc import Sequence
from typing import Any

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper


class MyModelWrapper(ModelWrapper):
    def load_model(self) -> Any:
        self.model = object()
        return self.model

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        raise NotImplementedError("Expose concrete hook points here.")

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        return {"text": batch.get("text", "")}, {}

    def generate(self, prompt: str, **generation_kwargs: Any) -> Any:
        return prompt

    def remove_hooks(self) -> None:
        pass
```

Then wire it into `build_model_wrapper` with a new `model.source` value and
document:

- supported model IDs and size limits
- supported hook names
- unsupported components
- required optional dependencies
- whether `trust_remote_code` is needed

For Transformers-backed models, prefer adding a SafeLens architecture adapter
instead of writing a full wrapper. The adapter maps HuggingFace module paths to
canonical hook components:

```python
from SafeLens.utils.model_bridge import ArchitectureAdapter, ComponentHookSpec

adapter = ArchitectureAdapter(
    name="my_decoder",
    model_types=("my_model_type",),
    model_name_markers=("my-org/my-model",),
    component_specs=(
        ComponentHookSpec("resid_pre", "forward_input", ("model.layers.{layer}",)),
        ComponentHookSpec("resid_post", "forward_output", ("model.layers.{layer}",)),
        ComponentHookSpec("q", "forward_output", ("model.layers.{layer}.self_attn.q_proj",)),
    ),
)
```

This is the same shape of abstraction used by TransformerLens: keep a canonical
component vocabulary, then write small family-specific mappings from the
provider model to that vocabulary.

SafeLens uses `ModelAdapterRegistry` for built-in adapters. A production adapter
should register a `ModelAdapterSpec` with capability metadata:

```python
from SafeLens.utils.model_registry import ModelAdapterCapabilities, ModelAdapterSpec

spec = ModelAdapterSpec(
    name="my_adapter",
    display_name="My Adapter",
    aliases=("my",),
    description="Short adapter description.",
    dependencies=("torch>=2",),
    capabilities=ModelAdapterCapabilities(
        supported_hooks=("integer decoder layer refs",),
        supported_patches=("module output replace",),
        supports_attention_pattern=False,
        supports_remote_download=True,
    ),
    build=lambda config: MyModelWrapper(),
    inspect=lambda model_name, config: {
        "model": model_name,
        "source": "my_adapter",
        "supported": True,
        "model_family": "my_family",
    },
)
```

Adapter tests should use fake modules or tiny local objects. Do not make default
CI download model weights.
