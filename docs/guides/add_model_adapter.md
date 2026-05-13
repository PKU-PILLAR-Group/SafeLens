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

Adapter tests should use fake modules or tiny local objects. Do not make default
CI download model weights.
