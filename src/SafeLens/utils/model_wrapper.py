"""Model wrapper implementations and hook helpers."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from inspect import Parameter, signature
from typing import Any

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelLoadConfig, ModelWrapper
from SafeLens.core.hooks import activation_name_for_layer

_QWEN3_DENSE_MAX_PARAMS_B = 35.0
_QWEN3_PATCHABLE_COMPONENTS = {
    "resid_pre",
    "resid_mid",
    "resid_post",
    "attn_out",
    "mlp_out",
    "q",
    "k",
    "v",
    "z",
}
_QWEN3_ATTENTION_COMPONENTS = {"pattern", "attn_scores"}


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


class Qwen3DenseModelWrapper(HuggingFaceModelWrapper):
    """Qwen3 dense wrapper exposing SafeLens component hook names.

    Supported model family: Qwen3 dense language models up to 35B parameters
    (`0.6B`, `1.7B`, `4B`, `8B`, `14B`, and `32B`). MoE variants such as
    `30B-A3B` and non-dense/VL/Coder variants are intentionally rejected.
    """

    def load_model(self) -> Any:
        validate_qwen3_dense_model_name(self.name)
        model = super().load_model()
        self._validate_loaded_qwen3_dense_model(model)
        return model

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        component_ref = parse_qwen3_component_ref(layer)
        if component_ref is None:
            return super().add_hook(layer, hook_fn)
        layer_index, component = component_ref
        handle = self._register_qwen3_component_hook(layer_index, component, hook_fn)
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
            component_ref = parse_qwen3_component_ref(layer)
            if component_ref is None:
                module = self._resolve_layer(model, layer)

                def cache_hook(
                    _module: Any,
                    _inputs: Any,
                    output: Any,
                    layer_ref: LayerRef = layer,
                ) -> None:
                    cache[activation_name_for_layer(layer_ref)] = output

                temp_handles.append(module.register_forward_hook(cache_hook))
                continue

            layer_index, component = component_ref
            cache_name = str(layer)
            temp_handles.append(
                self._register_qwen3_component_hook(
                    layer_index,
                    component,
                    lambda cache_key=cache_name, **kwargs: cache.setdefault(
                        cache_key,
                        kwargs["activation"],
                    ),
                )
            )

        try:
            import torch

            model_inputs = self._prepare_model_inputs(batch)
            with torch.no_grad():
                output = model(**model_inputs)
        finally:
            for handle in temp_handles:
                handle.remove()

        return output, cache

    def _register_qwen3_component_hook(
        self,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
    ) -> Any:
        if component in _QWEN3_ATTENTION_COMPONENTS:
            raise NotImplementedError(
                "Qwen3 dense attention pattern/scores hooks require attention-forward "
                "instrumentation and are not exposed by raw Transformers modules yet."
            )
        if component not in _QWEN3_PATCHABLE_COMPONENTS:
            raise KeyError(f"Unsupported Qwen3 dense component {component!r}.")

        qwen_layer = self._qwen3_layer(layer_index)
        if component == "resid_pre":
            return self._register_input_hook(qwen_layer, layer_index, component, hook_fn)
        if component == "resid_mid":
            return self._register_input_hook(
                qwen_layer.post_attention_layernorm,
                layer_index,
                component,
                hook_fn,
            )
        if component == "resid_post":
            return self._register_first_output_hook(qwen_layer, layer_index, component, hook_fn)
        if component == "attn_out":
            return self._register_first_output_hook(
                qwen_layer.self_attn,
                layer_index,
                component,
                hook_fn,
            )
        if component == "mlp_out":
            return self._register_tensor_output_hook(
                qwen_layer.mlp,
                layer_index,
                component,
                hook_fn,
            )
        if component in {"q", "k", "v"}:
            projection = getattr(qwen_layer.self_attn, f"{component}_proj")
            return self._register_head_projection_hook(
                projection,
                layer_index,
                component,
                hook_fn,
            )
        return self._register_z_hook(qwen_layer.self_attn.o_proj, layer_index, hook_fn)

    def _register_input_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
    ) -> Any:
        def pre_hook(_module: Any, inputs: tuple[Any, ...]) -> tuple[Any, ...] | None:
            if not inputs:
                return None
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=inputs[0],
                layer=layer_index,
                component=component,
            )
            if patched is None:
                return None
            return (patched, *inputs[1:])

        return module.register_forward_pre_hook(pre_hook)

    def _register_first_output_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
    ) -> Any:
        def forward_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            activation = _first_output(output)
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=activation,
                layer=layer_index,
                component=component,
            )
            if patched is None:
                return None
            return _replace_first_output(output, patched)

        return module.register_forward_hook(forward_hook)

    def _register_tensor_output_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
    ) -> Any:
        def forward_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=output,
                layer=layer_index,
                component=component,
            )
            return None if patched is None else patched

        return module.register_forward_hook(forward_hook)

    def _register_head_projection_hook(
        self,
        module: Any,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
    ) -> Any:
        def forward_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            n_heads = self._heads_for_component(component)
            activation = _split_qwen3_heads(output, n_heads)
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=activation,
                layer=layer_index,
                component=component,
            )
            if patched is None:
                return None
            return _merge_qwen3_heads(patched, output)

        return module.register_forward_hook(forward_hook)

    def _register_z_hook(self, module: Any, layer_index: int, hook_fn: HookFn) -> Any:
        def pre_hook(_module: Any, inputs: tuple[Any, ...]) -> tuple[Any, ...] | None:
            if not inputs:
                return None
            activation = _split_qwen3_heads(inputs[0], self._heads_for_component("z"))
            patched = _call_qwen3_component_hook(
                hook_fn,
                activation=activation,
                layer=layer_index,
                component="z",
            )
            if patched is None:
                return None
            return (_merge_qwen3_heads(patched, inputs[0]), *inputs[1:])

        return module.register_forward_pre_hook(pre_hook)

    def _qwen3_layer(self, layer_index: int) -> Any:
        layers = _get_qwen3_layers(self._require_model())
        try:
            return layers[layer_index]
        except IndexError as exc:
            raise KeyError(f"Unknown Qwen3 dense layer index {layer_index}.") from exc

    def _heads_for_component(self, component: str) -> int:
        config = getattr(self._require_model(), "config", None)
        if component in {"k", "v"}:
            n_key_value_heads = getattr(config, "num_key_value_heads", None)
            if n_key_value_heads is not None:
                return int(n_key_value_heads)
        n_heads = getattr(config, "num_attention_heads", None)
        if n_heads is None:
            raise ValueError("Qwen3 config does not expose num_attention_heads.")
        return int(n_heads)

    @staticmethod
    def _validate_loaded_qwen3_dense_model(model: Any) -> None:
        config = getattr(model, "config", None)
        model_type = str(getattr(config, "model_type", "")).lower()
        if model_type not in {"qwen3", ""}:
            raise ValueError(f"Expected a Qwen3 dense model, got model_type={model_type!r}.")
        if getattr(config, "num_experts", None) is not None:
            raise ValueError("Qwen3 MoE models are not supported by Qwen3DenseModelWrapper.")


def parse_qwen3_component_ref(layer: LayerRef) -> tuple[int, str] | None:
    """Parse SafeLens or TransformerLens-style Qwen3 component hook names."""
    if not isinstance(layer, str):
        return None

    safe_match = re.fullmatch(r"layer_(\d+)\.([a-z_]+)", layer)
    if safe_match is not None:
        return int(safe_match.group(1)), _normalize_qwen3_component(safe_match.group(2))

    block_match = re.fullmatch(r"blocks\.(\d+)\.(?:([a-z_]+)\.)?hook_([a-z_]+)", layer)
    if block_match is not None:
        layer_index = int(block_match.group(1))
        layer_type = block_match.group(2)
        component = _normalize_qwen3_component(block_match.group(3), layer_type=layer_type)
        return layer_index, component

    return None


def qwen3_dense_size_billion(model_name: str) -> float | None:
    """Return the parsed Qwen3 model size in billions when present in the name."""
    match = re.search(r"Qwen3[-_/](\d+(?:\.\d+)?)B", model_name, flags=re.IGNORECASE)
    if match is None:
        return None
    return float(match.group(1))


def is_supported_qwen3_dense_model_name(model_name: str) -> bool:
    """Return whether a model name looks like a supported Qwen3 <=35B dense model."""
    lowered = model_name.lower()
    if "qwen3" not in lowered:
        return False
    if any(marker in lowered for marker in ("moe", "-a", "_a", "coder", "vl")):
        return False
    size_b = qwen3_dense_size_billion(model_name)
    return size_b is None or size_b <= _QWEN3_DENSE_MAX_PARAMS_B


def validate_qwen3_dense_model_name(model_name: str) -> None:
    """Reject known unsupported Qwen3 MoE or >35B model names before loading."""
    lowered = model_name.lower()
    if "qwen3" not in lowered:
        return
    if any(marker in lowered for marker in ("moe", "-a", "_a", "coder", "vl")):
        raise ValueError(f"Unsupported Qwen3 non-dense model name: {model_name!r}.")
    size_b = qwen3_dense_size_billion(model_name)
    if size_b is not None and size_b > _QWEN3_DENSE_MAX_PARAMS_B:
        raise ValueError(
            f"Unsupported Qwen3 model size {size_b:g}B. "
            f"Only dense models <= {_QWEN3_DENSE_MAX_PARAMS_B:g}B are supported."
        )


def _normalize_qwen3_component(component: str, *, layer_type: str | None = None) -> str:
    aliases = {
        "hook_resid_pre": "resid_pre",
        "hook_resid_mid": "resid_mid",
        "hook_resid_post": "resid_post",
        "resid_pre": "resid_pre",
        "resid_mid": "resid_mid",
        "resid_post": "resid_post",
        "hook_attn_out": "attn_out",
        "attn_out": "attn_out",
        "hook_mlp_out": "mlp_out",
        "mlp_out": "mlp_out",
        "hook_q": "q",
        "hook_k": "k",
        "hook_v": "v",
        "hook_z": "z",
        "hook_pattern": "pattern",
        "hook_attn_scores": "attn_scores",
        "q": "q",
        "k": "k",
        "v": "v",
        "z": "z",
        "result": "z",
        "pattern": "pattern",
        "attn_scores": "attn_scores",
    }
    if layer_type == "mlp" and component in {"post", "hook_post"}:
        return "mlp_out"
    return aliases.get(component, component)


def _call_qwen3_component_hook(
    hook_fn: HookFn,
    *,
    activation: Any,
    layer: int,
    component: str,
) -> Any:
    try:
        return hook_fn(
            activation=activation,
            output=activation,
            layer=layer,
            component=component,
        )
    except TypeError:
        return hook_fn(None, None, activation)


def _get_qwen3_layers(model: Any) -> Any:
    base_model = getattr(model, "model", model)
    layers = getattr(base_model, "layers", None)
    if layers is None:
        raise KeyError("Could not find Qwen3 decoder layers at `model.layers`.")
    return layers


def _first_output(output: Any) -> Any:
    if isinstance(output, tuple):
        return output[0]
    return output


def _replace_first_output(output: Any, patched: Any) -> Any:
    if isinstance(output, tuple):
        return (patched, *output[1:])
    return patched


def _split_qwen3_heads(activation: Any, n_heads: int) -> Any:
    shape = getattr(activation, "shape", None)
    view = getattr(activation, "view", None)
    if shape is None or not callable(view):
        return activation
    head_dim = int(shape[-1]) // n_heads
    return activation.view(*shape[:-1], n_heads, head_dim)


def _merge_qwen3_heads(activation: Any, reference: Any) -> Any:
    shape = getattr(activation, "shape", None)
    reshape = getattr(activation, "reshape", None)
    if shape is None or not callable(reshape) or len(shape) < 2:
        return activation
    reference_shape = getattr(reference, "shape", None)
    hidden_size = int(shape[-2]) * int(shape[-1])
    if reference_shape is not None:
        hidden_size = int(reference_shape[-1])
    return activation.reshape(*shape[:-2], hidden_size)


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
    if source in {"qwen3", "qwen3_dense", "qwen3-dense"}:
        return Qwen3DenseModelWrapper(
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
        f"{config.source!r}. Expected one of: dummy, huggingface, qwen3_dense, modelscope."
    )
