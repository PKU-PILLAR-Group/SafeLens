# Model Wrapper

Model wrappers isolate the rest of the pipeline from model loading details.

Available wrappers:

- `DummyModelWrapper`: test and CI wrapper with no external dependencies.
- `HuggingFaceModelWrapper`: loads models directly with Transformers.
- `ModelScopeModelWrapper`: downloads a ModelScope snapshot, then loads it with
  Transformers.
- `TransformerLensModelWrapper`: loads `HookedTransformer` models and exposes
  TransformerLens HookPoint names for component-level activation patching.

Select a wrapper through `model.source` in the YAML config:

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
```

::: SafeLens.utils.model_wrapper
