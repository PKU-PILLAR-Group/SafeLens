# Model Adapter Registry

The model adapter registry declares which model backends SafeLens can build,
what capabilities each backend exposes, and how model cache/download plans are
resolved without loading weights.

List supported adapters:

```bash
safelens models list-supported
safelens models list-supported --json
```

Inspect a model name without downloading it:

```bash
safelens inspect-model --model Qwen/Qwen3-8B
safelens inspect-model --model Qwen/Qwen3-8B --json
```

Use it from Python:

```python
from SafeLens.utils import get_model_adapter_registry

registry = get_model_adapter_registry()
print(registry.list_supported())
print(registry.inspect_model("Qwen/Qwen3-8B"))
```

::: SafeLens.utils.model_registry
