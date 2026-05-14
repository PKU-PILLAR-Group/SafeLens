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

::: SafeLens.utils.model_wrapper
