# Model Wrapper

Model wrappers isolate the rest of the pipeline from model loading details.

Available wrappers:

- `DummyModelWrapper`: test and CI wrapper with no external dependencies.
- `HuggingFaceModelWrapper`: loads models directly with Transformers.
- `Qwen3DenseModelWrapper`: adapts Qwen3 dense models up to 35B with SafeLens
  component hooks for residual streams, MLP output, attention output, and
  `q/k/v/z` head vectors.
- `ModelScopeModelWrapper`: downloads a ModelScope snapshot, then loads it with
  Transformers.

Select a wrapper through `model.source` in the YAML config:

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
```

Minimal Python usage:

```python
from SafeLens.core.base import ModelLoadConfig
from SafeLens.utils import build_model_wrapper

model = build_model_wrapper(ModelLoadConfig(source="dummy", name="dummy"))
model.load_model()
output, cache = model.run_with_cache({"text": "hello"}, layers=[0])
```

::: SafeLens.utils.model_wrapper
