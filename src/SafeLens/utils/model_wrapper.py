"""Model wrapper implementations and hook helpers."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from contextlib import nullcontext
from inspect import Parameter, signature
from typing import Any

from SafeLens.core.base import (
    Batch,
    HookFn,
    LayerRef,
    ModelLoadConfig,
    ModelWrapper,
)
from SafeLens.core.hooks import activation_name_for_layer
from SafeLens.utils.model_bridge import (
    architecture_adapter_for_model,
    list_architecture_adapters,
    supported_transformer_component_names,
)
from SafeLens.utils.model_registry import (
    ModelAdapterCapabilities,
    ModelAdapterSpec,
    get_model_adapter_registry,
    resolve_model_download_plan,
)
from SafeLens.utils.transformer_lens_support import (
    is_transformer_lens_supported_model_name,
    resolve_transformer_lens_compatible_model_name,
    transformer_lens_model_kind,
    transformer_lens_official_model_names,
)

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
_QWEN3_COMPONENT_EXAMPLES = (
    "layer_0.resid_pre",
    "layer_0.resid_mid",
    "layer_0.resid_post",
    "layer_0.attn_out",
    "layer_0.mlp_out",
    "layer_0.q",
    "layer_0.k",
    "layer_0.v",
    "layer_0.z",
    "layer_0.pattern",
    "layer_0.attn_scores",
    "blocks.0.hook_resid_pre",
    "blocks.0.attn.hook_q",
    "blocks.0.attn.hook_pattern",
    "blocks.0.attn.hook_attn_scores",
)
_TRANSFORMER_LENS_HOOK_COMPONENTS = (
    "hook_embed",
    "hook_pos_embed",
    "blocks.N.hook_resid_pre",
    "blocks.N.hook_resid_mid",
    "blocks.N.hook_resid_post",
    "blocks.N.attn.hook_q",
    "blocks.N.attn.hook_k",
    "blocks.N.attn.hook_v",
    "blocks.N.attn.hook_z",
    "blocks.N.attn.hook_pattern",
    "blocks.N.attn.hook_attn_scores",
    "blocks.N.attn.hook_result",
    "blocks.N.hook_attn_out",
    "blocks.N.mlp.hook_pre",
    "blocks.N.mlp.hook_post",
    "blocks.N.hook_mlp_out",
    "ln_final.hook_scale",
)
_TRANSFORMER_LENS_PATCH_COMPONENTS = (
    "resid_pre",
    "resid_mid",
    "resid_post",
    "attn_out",
    "mlp_out",
    "q",
    "k",
    "v",
    "z",
    "pattern",
    "attn_scores",
)


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
        "hook": None,
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
    if required_names.issubset(filtered_kwargs):
        return hook_fn(**filtered_kwargs)

    try:
        return hook_fn(activation, None)
    except TypeError:
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
        pretrained_path: str | None = None,
    ) -> None:
        self.name = name
        self.dtype = dtype
        self.device = device
        self.revision = revision
        self.cache_dir = cache_dir
        self.trust_remote_code = trust_remote_code
        self.load_kwargs = load_kwargs or {}
        self.tokenizer_kwargs = tokenizer_kwargs or {}
        self.pretrained_path = pretrained_path
        self.model: Any = None
        self.tokenizer: Any = None
        self._tokenizer_load_error: Exception | None = None
        self._hooks: list[Any] = []
        self._requires_output_attentions = False
        self._run_requires_output_attentions = False

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

        self.tokenizer = self._load_text_tokenizer(
            AutoTokenizer,
            pretrained_path,
            pretrained_kwargs,
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
        return self.pretrained_path or self.name

    def _pretrained_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.revision is not None:
            kwargs["revision"] = self.revision
        if self.cache_dir is not None:
            kwargs["cache_dir"] = self.cache_dir
        return kwargs

    def _load_text_tokenizer(
        self,
        tokenizer_cls: Any,
        pretrained_path: str,
        pretrained_kwargs: dict[str, Any],
    ) -> Any | None:
        try:
            tokenizer = tokenizer_cls.from_pretrained(
                pretrained_path,
                trust_remote_code=self.trust_remote_code,
                **pretrained_kwargs,
                **self.tokenizer_kwargs,
            )
        except Exception as exc:
            self._tokenizer_load_error = exc
            return None
        self._tokenizer_load_error = None
        return tokenizer

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        model = self._require_model()
        component_handle = self._try_register_component_hook(model, layer, hook_fn)
        if component_handle is not None:
            self._hooks.append(component_handle)
            return component_handle
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
            component_handle = self._try_register_component_cache_hook(model, layer, cache)
            if component_handle is not None:
                temp_handles.append(component_handle)
                continue
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
            model_inputs = self._prepare_model_inputs(batch)
            with _no_grad_context():
                output = model(**model_inputs)
        finally:
            self._run_requires_output_attentions = False
            for handle in reversed(temp_handles):
                handle.remove()

        return output, cache

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        model = self._require_model()
        if self.tokenizer is None:
            detail = _tokenizer_error_detail(self._tokenizer_load_error)
            raise RuntimeError(
                "Tokenizer is not loaded, so text generation is unavailable. " f"{detail}"
            )

        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt")
        if self.device is not None:
            inputs = inputs.to(self.device)
        with torch.no_grad():
            output_ids = model.generate(**inputs, **generation_kwargs)
        return str(self.tokenizer.decode(output_ids[0], skip_special_tokens=True))

    def remove_hooks(self) -> None:
        for handle in reversed(self._hooks):
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
                return self._with_attention_flags(dict(tokenized))
        if self.tokenizer is None and "input_ids" not in batch:
            text = batch.get("text") or batch.get("prompt")
            if text is not None:
                detail = _tokenizer_error_detail(self._tokenizer_load_error)
                raise ValueError(
                    "This model did not load a tokenizer, so text batches cannot be "
                    f"tokenized. Provide `input_ids` or `inputs_embeds` directly. {detail}"
                )
        return self._with_attention_flags(dict(batch))

    def _try_register_component_hook(
        self,
        model: Any,
        layer: LayerRef,
        hook_fn: HookFn,
    ) -> Any | None:
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        if adapter.parse_component_ref(layer) is None:
            return None
        requires_output_attentions = adapter.requires_output_attentions(layer)
        handle = adapter.register_component_hook(model, layer, hook_fn)
        if requires_output_attentions:
            self._requires_output_attentions = True
        return handle

    def _try_register_component_cache_hook(
        self,
        model: Any,
        layer: LayerRef,
        cache: dict[str, Any],
    ) -> Any | None:
        adapter = architecture_adapter_for_model(model, model_name=self.name)
        if adapter.parse_component_ref(layer) is None:
            return None
        if adapter.requires_output_attentions(layer):
            self._run_requires_output_attentions = True
        cache_name = activation_name_for_layer(layer) if isinstance(layer, int) else str(layer)

        def cache_component(*, activation: Any, **_kwargs: Any) -> None:
            cache[cache_name] = activation

        return adapter.register_component_hook_for_mode(
            model,
            layer,
            cache_component,
            for_cache=True,
        )

    def _with_attention_flags(self, model_inputs: dict[str, Any]) -> dict[str, Any]:
        if self._requires_output_attentions or self._run_requires_output_attentions:
            model_inputs.setdefault("output_attentions", True)
        return model_inputs

    @staticmethod
    def _resolve_layer(model: Any, layer: LayerRef) -> Any:
        if isinstance(layer, str):
            modules = dict(model.named_modules())
            if layer not in modules:
                examples = ", ".join(list(modules)[:8])
                raise KeyError(
                    f"Unknown module or hook name {layer!r}. Use an integer layer index, "
                    "a module name from model.named_modules(), or a component hook name "
                    "supported by the selected model adapter. "
                    f"First available module names: {examples}"
                )
            return modules[layer]

        for path in ("model.layers", "transformer.h", "gpt_neox.layers"):
            target = model
            try:
                for part in path.split("."):
                    target = getattr(target, part)
                return target[layer]
            except (AttributeError, IndexError, TypeError):
                continue
        raise KeyError(
            f"Could not resolve layer index {layer} for model {type(model).__name__}. "
            "Known decoder-layer paths tried: model.layers, transformer.h, gpt_neox.layers."
        )


class TransformerLensCompatibleModelWrapper(HuggingFaceModelWrapper):
    """Independent Transformers wrapper for TransformerLens-compatible model IDs.

    The compatibility table mirrors TransformerLens' public support matrix, but
    this class never imports or delegates to TransformerLens. Decoder,
    encoder-decoder, encoder, and audio-encoder families are loaded through the
    closest Transformers auto class.
    """

    def load_model(self) -> Any:
        if not self._is_supported_transformer_lens_target():
            raise ValueError(
                f"Model {self.name!r} is not in SafeLens' vendored TransformerLens-compatible "
                "support table. Use source='huggingface' for generic Transformers loading, "
                "or source='local' for a local model directory."
            )
        try:
            import torch
            from transformers import (
                AutoFeatureExtractor,
                AutoModel,
                AutoModelForCausalLM,
                AutoModelForSeq2SeqLM,
                AutoProcessor,
                AutoTokenizer,
            )
        except ImportError as exc:
            raise ImportError(
                "TransformerLensCompatibleModelWrapper requires SafeLens model "
                "dependencies. Install them with `pip install -e '.[models]'`."
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
        kind = transformer_lens_model_kind(self.name)

        if kind == "audio_encoder":
            self.tokenizer = self._load_audio_processor(
                (AutoProcessor, AutoFeatureExtractor),
                pretrained_path,
                pretrained_kwargs,
            )
            self.model = AutoModel.from_pretrained(
                pretrained_path,
                torch_dtype=torch_dtype,
                trust_remote_code=self.trust_remote_code,
                **pretrained_kwargs,
                **self.load_kwargs,
            )
        else:
            self.tokenizer = self._load_text_tokenizer(
                AutoTokenizer,
                pretrained_path,
                pretrained_kwargs,
            )
            model_cls: Any
            if kind == "encoder_decoder":
                model_cls = AutoModelForSeq2SeqLM
            elif kind == "encoder":
                model_cls = AutoModel
            else:
                model_cls = AutoModelForCausalLM
            self.model = model_cls.from_pretrained(
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
        raw_path = self.pretrained_path or self.name
        return resolve_transformer_lens_compatible_model_name(raw_path)

    def _is_supported_transformer_lens_target(self) -> bool:
        if _wrapper_looks_like_local_path(self.name):
            return True
        if self.pretrained_path is not None and _wrapper_looks_like_local_path(
            self.pretrained_path
        ):
            return True
        return is_transformer_lens_supported_model_name(self.name)

    def _prepare_model_inputs(self, batch: Batch) -> dict[str, Any]:
        kind = transformer_lens_model_kind(self.name)
        model_kwargs = dict(batch.get("model_kwargs", {}))
        if kind == "encoder_decoder" and "encoder_tokens" in batch and "decoder_tokens" in batch:
            return self._with_attention_flags(
                {
                    "input_ids": batch["encoder_tokens"],
                    "decoder_input_ids": batch["decoder_tokens"],
                    **model_kwargs,
                }
            )
        if kind == "encoder_decoder":
            prepared = super()._prepare_model_inputs(batch)
            prepared.update(model_kwargs)
            if not any(
                key in prepared for key in ("decoder_input_ids", "decoder_inputs_embeds", "labels")
            ):
                input_ids = prepared.get("input_ids")
                if input_ids is None:
                    raise ValueError(
                        "Encoder-decoder models require input_ids or explicit decoder inputs."
                    )
                config = getattr(self._require_model(), "config", None)
                decoder_start_token_id = batch.get(
                    "decoder_start_token_id",
                    getattr(config, "decoder_start_token_id", None),
                )
                if decoder_start_token_id is None:
                    decoder_start_token_id = getattr(config, "pad_token_id", None)
                if decoder_start_token_id is None:
                    decoder_start_token_id = getattr(self.tokenizer, "pad_token_id", None)
                if decoder_start_token_id is None:
                    raise ValueError(
                        "Encoder-decoder models require decoder_input_ids when no "
                        "decoder_start_token_id or pad_token_id is available."
                    )
                prepared["decoder_input_ids"] = input_ids.new_full(
                    (input_ids.shape[0], 1),
                    int(decoder_start_token_id),
                )
            return self._with_attention_flags(prepared)
        if kind != "audio_encoder":
            prepared = super()._prepare_model_inputs(batch)
            prepared.update(model_kwargs)
            return self._with_attention_flags(prepared)

        if self.tokenizer is None:
            return dict(batch)
        audio = _first_present(batch, ("audio", "wave", "raw_audio"))
        if audio is None:
            return model_kwargs
        processor_kwargs = dict(batch.get("processor_kwargs", {}))
        sampling_rate = batch.get("sampling_rate", 16000)
        processed = self.tokenizer(
            audio,
            sampling_rate=sampling_rate,
            return_tensors="pt",
            **processor_kwargs,
        )
        if self.device is not None:
            processed = processed.to(self.device)
        return self._with_attention_flags({**dict(processed), **model_kwargs})

    def generate(self, prompt: str, **generation_kwargs: Any) -> str:
        kind = transformer_lens_model_kind(self.name)
        if kind in {"encoder", "audio_encoder"}:
            raise NotImplementedError(
                f"{kind} models do not expose autoregressive text generation through "
                "the independent SafeLens Transformers wrapper."
            )
        return super().generate(prompt, **generation_kwargs)

    def _load_audio_processor(
        self,
        processor_classes: tuple[Any, Any],
        pretrained_path: str,
        pretrained_kwargs: dict[str, Any],
    ) -> Any:
        last_error: Exception | None = None
        for processor_cls in processor_classes:
            try:
                return processor_cls.from_pretrained(
                    pretrained_path,
                    trust_remote_code=self.trust_remote_code,
                    **pretrained_kwargs,
                    **self.tokenizer_kwargs,
                )
            except Exception as exc:
                last_error = exc
        raise RuntimeError(
            f"Could not load an audio processor for {pretrained_path!r}."
        ) from last_error


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
            if component in _QWEN3_ATTENTION_COMPONENTS:
                component_handle = self._try_register_component_cache_hook(
                    model,
                    layer,
                    cache,
                )
                if component_handle is not None:
                    temp_handles.append(component_handle)
                    continue
                raise KeyError(f"Could not resolve Qwen3 attention component {layer!r}.")
            temp_handles.append(
                self._register_qwen3_component_hook(
                    layer_index,
                    component,
                    _make_qwen3_cache_hook(cache, cache_name),
                )
            )

        try:
            model_inputs = self._prepare_model_inputs(batch)
            with _no_grad_context():
                output = model(**model_inputs)
        finally:
            self._run_requires_output_attentions = False
            for handle in reversed(temp_handles):
                handle.remove()

        return output, cache

    def _register_qwen3_component_hook(
        self,
        layer_index: int,
        component: str,
        hook_fn: HookFn,
    ) -> Any:
        if component in _QWEN3_ATTENTION_COMPONENTS:
            handle = self._try_register_component_hook(
                self._require_model(),
                f"layer_{layer_index}.{component}",
                hook_fn,
            )
            if handle is None:
                raise KeyError(f"Could not resolve Qwen3 attention component {component!r}.")
            return handle
        if component not in _QWEN3_PATCHABLE_COMPONENTS:
            supported = ", ".join(qwen3_supported_hook_components(include_attention=True))
            examples = ", ".join(_QWEN3_COMPONENT_EXAMPLES[:4])
            raise KeyError(
                f"Unsupported Qwen3 dense component {component!r}. "
                f"Supported components: {supported}. Example hook names: {examples}."
            )

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


def qwen3_supported_hook_components(*, include_attention: bool = False) -> list[str]:
    """Return component names accepted by the Qwen3 dense adapter."""
    components = sorted(_QWEN3_PATCHABLE_COMPONENTS)
    if include_attention:
        components.extend(sorted(_QWEN3_ATTENTION_COMPONENTS))
    return components


def qwen3_hook_name_examples() -> list[str]:
    """Return example SafeLens and TransformerLens-style Qwen3 hook names."""
    return list(_QWEN3_COMPONENT_EXAMPLES)


def validate_qwen3_hook_ref(layer: LayerRef) -> None:
    """Validate a static Qwen3 dense layer or component hook reference."""
    if isinstance(layer, int):
        if layer < 0:
            raise ValueError("Qwen3 layer indices must be non-negative integers.")
        return
    if not isinstance(layer, str):
        raise ValueError(
            f"Qwen3 hook references must be integers or strings, got {type(layer).__name__}."
        )

    component_ref = parse_qwen3_component_ref(layer)
    if component_ref is None:
        if layer.startswith("layer_") or layer.startswith("blocks."):
            examples = ", ".join(_QWEN3_COMPONENT_EXAMPLES[:6])
            raise ValueError(
                f"Invalid Qwen3 hook name {layer!r}. Expected SafeLens names such as "
                f"`layer_0.resid_pre` or TransformerLens-style names such as "
                f"`blocks.0.attn.hook_q`. Examples: {examples}."
            )
        return

    _layer_index, component = component_ref
    if component in _QWEN3_ATTENTION_COMPONENTS:
        return
    if component not in _QWEN3_PATCHABLE_COMPONENTS:
        supported = ", ".join(qwen3_supported_hook_components(include_attention=True))
        examples = ", ".join(_QWEN3_COMPONENT_EXAMPLES[:6])
        raise ValueError(
            f"Unsupported Qwen3 hook component {component!r} in {layer!r}. "
            f"Supported components: {supported}. Examples: {examples}."
        )


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
    hook_kwargs = {
        "activation": activation,
        "output": activation,
        "hook": None,
        "layer": layer,
        "component": component,
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
    if required_names.issubset(filtered_kwargs):
        return hook_fn(**filtered_kwargs)

    try:
        return hook_fn(activation, None)
    except TypeError:
        return hook_fn(None, None, activation)


def _make_qwen3_cache_hook(cache: dict[str, Any], cache_name: str) -> HookFn:
    def cache_hook(*, activation: Any, **_kwargs: Any) -> None:
        cache[cache_name] = activation
        return None

    return cache_hook


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


def _no_grad_context() -> Any:
    try:
        import torch

        return torch.no_grad()
    except ImportError:
        return nullcontext()


def _tokenizer_error_detail(error: Exception | None) -> str:
    if error is None:
        return "Call load_model() first or configure tokenizer files for the model."
    return f"Tokenizer load error: {type(error).__name__}: {error}"


def _wrapper_looks_like_local_path(value: str) -> bool:
    return value.startswith((".", "/", "~"))


def _first_present(batch: Batch, keys: Sequence[str]) -> Any:
    for key in keys:
        if key in batch:
            return batch[key]
    return None


class LocalModelWrapper(HuggingFaceModelWrapper):
    """Transformers-compatible local directory wrapper with no provider download."""


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
    register_builtin_model_adapters()
    if config.name.lower() in {"dummy", "mock", "none"}:
        return DummyModelWrapper(name=config.name)
    return get_model_adapter_registry().create(config)


_MODEL_ADAPTERS_REGISTERED = False


def register_builtin_model_adapters() -> None:
    """Register SafeLens built-in model adapters once."""
    global _MODEL_ADAPTERS_REGISTERED
    if _MODEL_ADAPTERS_REGISTERED:
        return

    registry = get_model_adapter_registry()
    registry.register(
        ModelAdapterSpec(
            name="dummy",
            display_name="Dummy",
            aliases=("mock", "none"),
            description="In-memory adapter for tests, CI, and architecture demos.",
            dependencies=(),
            model_name_patterns=("dummy", "mock", "none"),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=("integer layer refs", "string layer refs"),
                supported_patches=("replace", "add"),
                supports_local_path=False,
                supports_remote_download=False,
                cache_policy="no external cache",
                notes=("Does not download or execute model code.",),
            ),
            build=_build_dummy_wrapper,
            inspect=_inspect_dummy_model,
            matches_model_name=lambda name: name.lower() in {"dummy", "mock", "none"},
            priority=100,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="qwen3_dense",
            display_name="Qwen3 Dense",
            aliases=("qwen3", "qwen3-dense"),
            description="Qwen3 dense <=35B adapter with component-level hooks.",
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=("Qwen/Qwen3-{0.6,1.7,4,8,14,32}B",),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=tuple(qwen3_supported_hook_components(include_attention=True)),
                supported_patches=(
                    "resid_pre",
                    "resid_mid",
                    "resid_post",
                    "attn_out",
                    "mlp_out",
                    "q",
                    "k",
                    "v",
                    "z",
                    "pattern",
                    "attn_scores",
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=False,
                supports_remote_download=True,
                cache_policy="SafeLens cache_dir -> .cache/safelens/models/huggingface",
                notes=(
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_qwen3_dense_wrapper,
            inspect=_inspect_qwen3_dense_model,
            matches_model_name=lambda name: "qwen3" in name.lower(),
            priority=200,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="transformer_lens",
            display_name="TransformerLens-Compatible Transformers",
            aliases=("transformerlens", "tl", "hooked_transformer"),
            description=(
                "Independent SafeLens adapter for model families mirrored from "
                "the TransformerLens supported model list."
            ),
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=(
                "gpt2",
                "EleutherAI/pythia-*",
                "meta-llama/*",
                "Qwen/Qwen*",
                "google/gemma-*",
                "google-bert/bert-*",
                "FacebookAI/roberta-*",
                "distilbert/distilbert-*",
                "google-t5/t5-*",
                "facebook/wav2vec2-*",
                "facebook/hubert-*",
            ),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=True,
                supports_remote_download=True,
                cache_policy=(
                    "SafeLens cache_dir -> .cache/safelens/models/transformer_lens_compatible"
                ),
                notes=(
                    "No TransformerLens runtime dependency is used.",
                    "Decoder, encoder-decoder, encoder, and audio-encoder families "
                    "load through Transformers auto classes.",
                    "SafeLens architecture adapters map HF module paths to canonical "
                    "components for GPT-2, GPT-J, GPT-Neo, GPT-NeoX/Pythia, "
                    "BLOOM/Falcon, MPT, Phi, OPT, BERT/RoBERTa, DistilBERT, "
                    "T5, Wav2Vec2/Hubert, and LLaMA-like decoder families.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_transformer_lens_compatible_wrapper,
            inspect=_inspect_transformer_lens_compatible_model,
            matches_model_name=is_transformer_lens_supported_model_name,
            priority=90,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="huggingface",
            display_name="HuggingFace Transformers",
            aliases=("hf",),
            description="Generic Transformers causal language model adapter.",
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=("organization/model-name",),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer decoder layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=False,
                supports_remote_download=True,
                cache_policy="SafeLens cache_dir -> .cache/safelens/models/huggingface",
                notes=(
                    "Component hooks use SafeLens architecture adapters when the "
                    "loaded Transformers architecture is recognized.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_huggingface_wrapper,
            inspect=_inspect_huggingface_model,
            matches_model_name=lambda name: "/" in name and not name.startswith((".", "/", "~")),
            priority=10,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="modelscope",
            display_name="ModelScope",
            aliases=("ms",),
            description="ModelScope snapshot download followed by Transformers loading.",
            dependencies=("modelscope>=1.15", "torch>=2", "transformers>=5.8"),
            model_name_patterns=("namespace/model-name",),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer decoder layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=False,
                supports_remote_download=True,
                cache_policy="SafeLens cache_dir -> .cache/safelens/models/modelscope",
                notes=(
                    "Use modelscope_kwargs for provider-specific snapshot filters.",
                    "Component hooks use SafeLens architecture adapters when the "
                    "loaded Transformers architecture is recognized.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_modelscope_wrapper,
            inspect=_inspect_modelscope_model,
            matches_model_name=lambda _name: False,
            priority=5,
        )
    )
    registry.register(
        ModelAdapterSpec(
            name="local",
            display_name="Local Transformers Directory",
            aliases=(),
            description="Local Transformers-compatible model directory.",
            dependencies=("torch>=2", "transformers>=5.8"),
            model_name_patterns=("./models/local-causal-lm", "/abs/path/to/model"),
            capabilities=ModelAdapterCapabilities(
                supported_hooks=(
                    "integer decoder layer refs",
                    "model.named_modules() names",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supported_patches=(
                    "module output replace",
                    "module output add",
                    *supported_transformer_component_names(include_attention=True),
                ),
                supports_attention_pattern=True,
                supports_attention_scores=True,
                supports_local_path=True,
                supports_remote_download=False,
                cache_policy="No provider download; local_dir or name is used directly.",
                notes=(
                    "Keep local model paths and weights out of git.",
                    "Component hooks use SafeLens architecture adapters when the "
                    "loaded Transformers architecture is recognized.",
                    "Attention pattern and score hooks use eager softmax instrumentation; "
                    "flash or SDPA paths may need an eager attention implementation.",
                ),
            ),
            build=_build_local_wrapper,
            inspect=_inspect_local_model,
            matches_model_name=lambda name: name.startswith((".", "/", "~")),
            priority=50,
        )
    )
    _MODEL_ADAPTERS_REGISTERED = True


def _build_dummy_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    return DummyModelWrapper(name=config.name)


def _build_huggingface_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return HuggingFaceModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
    )


def _build_local_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return LocalModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=None,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
    )


def _build_qwen3_dense_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return Qwen3DenseModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
    )


def _build_transformer_lens_compatible_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return TransformerLensCompatibleModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        pretrained_path=plan.pretrained_path,
    )


def _build_modelscope_wrapper(config: ModelLoadConfig) -> ModelWrapper:
    plan = resolve_model_download_plan(config)
    return ModelScopeModelWrapper(
        name=config.name,
        dtype=config.dtype,
        device=config.device,
        revision=config.revision,
        cache_dir=plan.cache_dir,
        local_dir=config.local_dir,
        trust_remote_code=config.trust_remote_code,
        load_kwargs=config.load_kwargs,
        tokenizer_kwargs=config.tokenizer_kwargs,
        modelscope_kwargs=config.modelscope_kwargs,
    )


def _inspect_dummy_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    return _inspection_payload(model_name, config, supported=True, model_family="dummy")


def _inspect_huggingface_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    return _inspection_payload(
        model_name,
        config,
        supported=True,
        model_family="generic_transformers",
        warnings=("Only module-level hooks are known statically for generic HF models.",),
    )


def _inspect_modelscope_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    return _inspection_payload(
        model_name,
        config,
        supported=True,
        model_family="modelscope_transformers",
        warnings=("ModelScope support downloads a snapshot before Transformers loading.",),
    )


def _inspect_local_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    local_path = config.local_dir if config is not None and config.local_dir else model_name
    return _inspection_payload(
        model_name,
        config,
        supported=True,
        model_family="local_transformers",
        local_path=local_path,
        warnings=("Static inspection does not verify that the local path exists.",),
    )


def _inspect_qwen3_dense_model(model_name: str, config: ModelLoadConfig | None) -> dict[str, Any]:
    errors: list[str] = []
    try:
        validate_qwen3_dense_model_name(model_name)
    except ValueError as exc:
        errors.append(str(exc))
    size_b = qwen3_dense_size_billion(model_name)
    payload = _inspection_payload(
        model_name,
        config,
        supported=not errors,
        model_family="qwen3_dense",
        parameter_size_b=size_b,
        supported_dense_limit_b=_QWEN3_DENSE_MAX_PARAMS_B,
        supported_hook_examples=qwen3_hook_name_examples(),
        warnings=(
            "Attention pattern and score hooks use eager softmax instrumentation; "
            "flash or SDPA attention paths may need an eager attention implementation.",
        ),
    )
    if errors:
        payload["errors"] = errors
    return payload


def _inspect_transformer_lens_compatible_model(
    model_name: str,
    config: ModelLoadConfig | None,
) -> dict[str, Any]:
    supported = is_transformer_lens_supported_model_name(model_name)
    resolved_model = resolve_transformer_lens_compatible_model_name(model_name)
    payload = _inspection_payload(
        model_name,
        config,
        supported=supported,
        model_family=f"transformer_lens_compatible_{transformer_lens_model_kind(model_name)}",
        resolved_pretrained_model=resolved_model,
        official_model_count=len(transformer_lens_official_model_names()),
        supported_model_examples=transformer_lens_official_model_names()[:20],
        architecture_bridge_adapters=[item["name"] for item in list_architecture_adapters()],
        bridge_components=list(supported_transformer_component_names(include_attention=True)),
        target_hook_examples=_TRANSFORMER_LENS_HOOK_COMPONENTS,
        warnings=(
            "SafeLens does not import TransformerLens for this adapter.",
            "Static inspection uses SafeLens' vendored TransformerLens support table; "
            "loading uses Transformers auto classes and may require a valid HF ID or local path.",
            "Component hooks use SafeLens architecture adapters. Attention pattern and score "
            "hooks use eager softmax instrumentation; flash or SDPA attention paths may need "
            "an eager attention implementation.",
        ),
    )
    if not supported:
        payload["errors"] = [
            "Model name is not in the vendored TransformerLens support table. "
            "Use source=huggingface or source=local if this is a plain Transformers model."
        ]
    return payload


def _inspection_payload(
    model_name: str,
    config: ModelLoadConfig | None,
    *,
    supported: bool,
    model_family: str,
    warnings: tuple[str, ...] = (),
    **extra: Any,
) -> dict[str, Any]:
    effective_config = config or ModelLoadConfig(source="huggingface", name=model_name)
    return {
        "model": model_name,
        "source": effective_config.source,
        "supported": supported,
        "model_family": model_family,
        "download_plan": resolve_model_download_plan(effective_config).to_dict(),
        "warnings": list(warnings),
        **extra,
    }


register_builtin_model_adapters()
