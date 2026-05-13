"""Model wrapper implementations and hook helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from inspect import Parameter, signature
from typing import Any

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelLoadConfig, ModelWrapper
from SafeLens.core.hooks import activation_name_for_layer


class _RemovableHandle:
    def __init__(self, remove_fn: Callable[[], None]) -> None:
        self._remove_fn = remove_fn
        self._removed = False

    def remove(self) -> None:
        if not self._removed:
            self._remove_fn()
            self._removed = True


class DummyModelWrapper(ModelWrapper):
    """Small in-memory model wrapper used by tests and architecture demos."""

    def __init__(self, name: str = "dummy") -> None:
        self.name = name
        self.loaded = False
        self._hooks: list[tuple[LayerRef, HookFn]] = []

    def load_model(self) -> DummyModelWrapper:
        self.loaded = True
        return self

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> _RemovableHandle:
        item = (layer, hook_fn)
        self._hooks.append(item)
        return _RemovableHandle(lambda: self._remove_hook(item))

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not self.loaded:
            self.load_model()

        selected_layers = list(layers or [layer for layer, _ in self._hooks])
        cache = {
            activation_name_for_layer(layer): {"batch": dict(batch)} for layer in selected_layers
        }
        model_output = {
            "text": batch.get("text") or batch.get("prompt") or "",
            "risk_score": float(batch.get("risk_score", 0.0)),
        }

        for layer, hook_fn in list(self._hooks):
            if not selected_layers or layer in selected_layers:
                name = activation_name_for_layer(layer)
                activation = cache.get(name, {"batch": dict(batch)})
                patched = _call_dummy_hook(
                    hook_fn,
                    layer=layer,
                    batch=batch,
                    cache=cache,
                    activation=activation,
                )
                if patched is not None:
                    cache[name] = patched

        return model_output, cache

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        _ = generation_kwargs
        return f"{prompt} [dummy generation]"

    def remove_hooks(self) -> None:
        self._hooks.clear()

    def _remove_hook(self, item: tuple[LayerRef, HookFn]) -> None:
        if item in self._hooks:
            self._hooks.remove(item)


def _call_dummy_hook(
    hook_fn: HookFn,
    *,
    layer: LayerRef,
    batch: Batch,
    cache: dict[str, Any],
    activation: Any,
) -> Any:
    hook_kwargs = {
        "layer": layer,
        "batch": batch,
        "cache": cache,
        "activation": activation,
        "output": activation,
    }
    try:
        hook_signature = signature(hook_fn)
    except (TypeError, ValueError):
        return hook_fn(**hook_kwargs)

    parameters = hook_signature.parameters.values()
    if any(param.kind == Parameter.VAR_KEYWORD for param in parameters):
        return hook_fn(**hook_kwargs)

    parameters = hook_signature.parameters.values()
    accepted_names = {
        param.name
        for param in parameters
        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    required_names = {
        param.name
        for param in hook_signature.parameters.values()
        if param.default is Parameter.empty
        and param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    filtered_kwargs = {name: value for name, value in hook_kwargs.items() if name in accepted_names}
    if filtered_kwargs and required_names.issubset(hook_kwargs):
        return hook_fn(**filtered_kwargs)

    return hook_fn(None, None, activation)


class HuggingFaceModelWrapper(ModelWrapper):
    """Transformers-based model wrapper with forward hook support."""

    def __init__(
        self,
        name: str,
        dtype: str = "float32",
        device: str | None = None,
        revision: str | None = None,
        cache_dir: str | None = None,
        trust_remote_code: bool = False,
        load_kwargs: dict[str, Any] | None = None,
        tokenizer_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.dtype = dtype
        self.device = device
        self.revision = revision
        self.cache_dir = cache_dir
        self.trust_remote_code = trust_remote_code
        self.load_kwargs = load_kwargs or {}
        self.tokenizer_kwargs = tokenizer_kwargs or {}
        self.model: Any = None
        self.tokenizer: Any = None
        self._hooks: list[Any] = []

    def load_model(self) -> Any:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ImportError(
                "HuggingFaceModelWrapper requires model dependencies. "
                "Install them with `pip install -e '.[models]'`."
            ) from exc

        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
            "auto": "auto",
        }
        torch_dtype = dtype_map.get(self.dtype, self.dtype)
        pretrained_path = self._resolve_pretrained_path()
        pretrained_kwargs = self._pretrained_kwargs()

        self.tokenizer = AutoTokenizer.from_pretrained(
            pretrained_path,
            trust_remote_code=self.trust_remote_code,
            **pretrained_kwargs,
            **self.tokenizer_kwargs,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            pretrained_path,
            torch_dtype=torch_dtype,
            trust_remote_code=self.trust_remote_code,
            **pretrained_kwargs,
            **self.load_kwargs,
        )
        if self.device is not None:
            self.model.to(self.device)
        self.model.eval()
        return self.model

    def _resolve_pretrained_path(self) -> str:
        return self.name

    def _pretrained_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.revision is not None:
            kwargs["revision"] = self.revision
        if self.cache_dir is not None:
            kwargs["cache_dir"] = self.cache_dir
        return kwargs

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        model = self._require_model()
        module = self._resolve_layer(model, layer)
        handle = module.register_forward_hook(
            lambda mod, inputs, output: hook_fn(mod, inputs, output)
        )
        self._hooks.append(handle)
        return handle

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        model = self._require_model()
        cache: dict[str, Any] = {}
        temp_handles: list[Any] = []

        for layer in layers or []:
            module = self._resolve_layer(model, layer)

            def cache_hook(
                _module: Any,
                _inputs: Any,
                output: Any,
                layer_ref: LayerRef = layer,
            ) -> None:
                cache[activation_name_for_layer(layer_ref)] = output

            temp_handles.append(module.register_forward_hook(cache_hook))

        try:
            import torch

            model_inputs = self._prepare_model_inputs(batch)
            with torch.no_grad():
                output = model(**model_inputs)
        finally:
            for handle in temp_handles:
                handle.remove()

        return output, cache

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        model = self._require_model()
        if self.tokenizer is None:
            raise RuntimeError("Tokenizer is not loaded. Call load_model() first.")

        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt")
        if self.device is not None:
            inputs = inputs.to(self.device)
        with torch.no_grad():
            output_ids = model.generate(**inputs, **generation_kwargs)
        return str(self.tokenizer.decode(output_ids[0], skip_special_tokens=True))

    def remove_hooks(self) -> None:
        for handle in self._hooks:
            handle.remove()
        self._hooks.clear()

    def _require_model(self) -> Any:
        if self.model is None:
            self.load_model()
        return self.model

    def _prepare_model_inputs(self, batch: Batch) -> dict[str, Any]:
        if self.tokenizer is not None and "input_ids" not in batch:
            text = batch.get("text") or batch.get("prompt")
            if text is not None:
                tokenized = self.tokenizer(str(text), return_tensors="pt")
                if self.device is not None:
                    tokenized = tokenized.to(self.device)
                return dict(tokenized)
        return dict(batch)

    @staticmethod
    def _resolve_layer(model: Any, layer: LayerRef) -> Any:
        if isinstance(layer, str):
            modules = dict(model.named_modules())
            if layer not in modules:
                raise KeyError(f"Unknown module '{layer}'")
            return modules[layer]

        for path in ("model.layers", "transformer.h", "gpt_neox.layers"):
            target = model
            try:
                for part in path.split("."):
                    target = getattr(target, part)
                return target[layer]
            except (AttributeError, IndexError, TypeError):
                continue
        raise KeyError(f"Could not resolve layer index {layer} for model {type(model).__name__}")


class ModelScopeModelWrapper(HuggingFaceModelWrapper):
    """ModelScope-backed wrapper that downloads a snapshot, then loads it with Transformers."""

    def __init__(
        self,
        name: str,
        dtype: str = "float32",
        device: str | None = None,
        revision: str | None = None,
        cache_dir: str | None = None,
        local_dir: str | None = None,
        trust_remote_code: bool = False,
        load_kwargs: dict[str, Any] | None = None,
        tokenizer_kwargs: dict[str, Any] | None = None,
        modelscope_kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            dtype=dtype,
            device=device,
            revision=revision,
            cache_dir=cache_dir,
            trust_remote_code=trust_remote_code,
            load_kwargs=load_kwargs,
            tokenizer_kwargs=tokenizer_kwargs,
        )
        self.local_dir = local_dir
        self.modelscope_kwargs = modelscope_kwargs or {}

    def _resolve_pretrained_path(self) -> str:
        try:
            from modelscope import snapshot_download
        except ImportError as exc:
            raise ImportError(
                "ModelScopeModelWrapper requires ModelScope dependencies. "
                "Install them with `pip install -e '.[modelscope]'`."
            ) from exc

        kwargs = dict(self.modelscope_kwargs)
        if self.revision is not None:
            kwargs["revision"] = self.revision
        if self.cache_dir is not None:
            kwargs["cache_dir"] = self.cache_dir
        if self.local_dir is not None:
            kwargs["local_dir"] = self.local_dir
        return str(snapshot_download(model_id=self.name, **kwargs))

    def _pretrained_kwargs(self) -> dict[str, Any]:
        return {}


def build_model_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    """Build the configured model wrapper."""
    source = config.source.lower()
    if source in {"dummy", "mock", "none"} or config.name.lower() in {"dummy", "mock", "none"}:
        return DummyModelWrapper(name=config.name)
    if source in {"huggingface", "hf"}:
        return HuggingFaceModelWrapper(
            name=config.name,
            dtype=config.dtype,
            device=config.device,
            revision=config.revision,
            cache_dir=config.cache_dir,
            trust_remote_code=config.trust_remote_code,
            load_kwargs=config.load_kwargs,
            tokenizer_kwargs=config.tokenizer_kwargs,
        )
    if source in {"modelscope", "ms"}:
        return ModelScopeModelWrapper(
            name=config.name,
            dtype=config.dtype,
            device=config.device,
            revision=config.revision,
            cache_dir=config.cache_dir,
            local_dir=config.local_dir,
            trust_remote_code=config.trust_remote_code,
            load_kwargs=config.load_kwargs,
            tokenizer_kwargs=config.tokenizer_kwargs,
            modelscope_kwargs=config.modelscope_kwargs,
        )
    raise ValueError(
        "Unsupported model source "
        f"{config.source!r}. Expected one of: dummy, huggingface, modelscope."
    )
