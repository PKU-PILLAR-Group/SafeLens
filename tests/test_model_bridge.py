from __future__ import annotations

from typing import Any

import pytest

from SafeLens.utils import (
    TransformerLensCompatibleModelWrapper,
    architecture_adapter_for_model,
    architecture_adapter_for_name,
    list_architecture_adapters,
    supported_transformer_component_names,
)


class _Handle:
    def __init__(self, remove_fn: Any) -> None:
        self._remove_fn = remove_fn

    def remove(self) -> None:
        self._remove_fn()


class _FakeModule:
    def __init__(self) -> None:
        self.forward_hooks: list[Any] = []
        self.pre_hooks: list[Any] = []

    def register_forward_hook(self, hook_fn: Any) -> _Handle:
        self.forward_hooks.append(hook_fn)
        return _Handle(lambda: self.forward_hooks.remove(hook_fn))

    def register_forward_pre_hook(self, hook_fn: Any) -> _Handle:
        self.pre_hooks.append(hook_fn)
        return _Handle(lambda: self.pre_hooks.remove(hook_fn))

    def run_forward(self, output: Any) -> Any:
        current = output
        for hook_fn in list(self.forward_hooks):
            patched = hook_fn(self, (), current)
            if patched is not None:
                current = patched
        return current

    def run_pre(self, value: Any) -> Any:
        inputs = (value,)
        for hook_fn in list(self.pre_hooks):
            patched = hook_fn(self, inputs)
            if patched is not None:
                inputs = patched
        return inputs[0]


class _FakeAttentionPattern:
    shape = (1, 2, 3, 3)
    ndim = 4


class _FakeAttention(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.q_proj = _FakeModule()
        self.k_proj = _FakeModule()
        self.v_proj = _FakeModule()
        self.o_proj = _FakeModule()


class _FakeLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.post_attention_layernorm = _FakeModule()
        self.self_attn = _FakeAttention()
        self.mlp = _FakeModule()


class _FakeConfig:
    model_type = "qwen3"


class _FakeBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeLayer()]


class _FakeQwenModel:
    def __init__(self) -> None:
        self.config = _FakeConfig()
        self.model = _FakeBackbone()

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        if kwargs.get("output_attentions"):
            pattern = _FakeAttentionPattern()
            output = self.model.layers[0].self_attn.run_forward((["attn"], pattern))
            return {"attention": output, "output_attentions": True}
        q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
        return {"q": q_out}


def test_architecture_adapter_maps_qwen3_components() -> None:
    model = _FakeQwenModel()
    adapter = architecture_adapter_for_model(model, model_name="Qwen/Qwen3-8B")

    assert adapter.name == "llama_like_decoder"
    assert adapter.parse_component_ref("blocks.0.attn.hook_q").safelens_name == "layer_0.q"  # type: ignore[union-attr]
    assert "mlp_out" in adapter.supported_components()

    adapter.register_component_hook(
        model,
        "blocks.0.attn.hook_q",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "layer_0.z",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )

    layer = model.model.layers[0]
    assert layer.self_attn.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.self_attn.o_proj.run_pre(["x"]) == ["x", "z"]


def test_architecture_adapter_rejects_uninstrumented_attention_patterns() -> None:
    model = _FakeQwenModel()
    adapter = architecture_adapter_for_model(model, model_name="Qwen/Qwen3-8B")

    with pytest.raises(NotImplementedError, match="can cache 'pattern', but cannot patch"):
        adapter.register_component_hook(model, "layer_0.pattern", lambda **kwargs: kwargs)


def test_architecture_adapter_registry_covers_major_transformer_families() -> None:
    adapter_names = {item["name"] for item in list_architecture_adapters()}

    assert {
        "llama_like_decoder",
        "gpt2_decoder",
        "gpt_neox_decoder",
        "gptj_decoder",
        "gpt_neo_decoder",
        "joint_qkv_decoder",
        "mpt_decoder",
        "phi_decoder",
        "opt_decoder",
        "bert_encoder",
        "t5_encoder_decoder",
    }.issubset(adapter_names)
    assert len(adapter_names) >= 10
    assert "attn_scores" not in supported_transformer_component_names()
    assert "pattern" in supported_transformer_component_names(include_pattern=True)


def test_architecture_adapter_can_infer_from_model_name_without_loading_config() -> None:
    assert architecture_adapter_for_name(model_name="gpt2-small").name == "gpt2_decoder"
    assert (
        architecture_adapter_for_name(model_name="EleutherAI/pythia-70m").name == "gpt_neox_decoder"
    )
    assert (
        architecture_adapter_for_name(model_name="google-bert/bert-base-uncased").name
        == "bert_encoder"
    )
    assert architecture_adapter_for_name(model_name="EleutherAI/gpt-j-6B").name == "gptj_decoder"
    assert architecture_adapter_for_name(model_name="facebook/opt-125m").name == "opt_decoder"


def test_transformer_lens_compatible_wrapper_uses_architecture_bridge() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["hooked"])

    assert wrapper.model.model.layers[0].self_attn.q_proj.run_forward(["q"]) == ["q", "hooked"]


def test_transformer_lens_compatible_wrapper_caches_component_hooks() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache({"text": "hello"}, layers=["blocks.0.attn.hook_q"])

    assert output == {"q": ["q"]}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}


def test_transformer_lens_compatible_wrapper_caches_attention_pattern() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache({"text": "hello"}, layers=["blocks.0.attn.hook_pattern"])

    assert output["output_attentions"] is True
    assert isinstance(cache["blocks.0.attn.hook_pattern"], _FakeAttentionPattern)


def test_transformer_lens_compatible_wrapper_rejects_attention_pattern_patching() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    with pytest.raises(NotImplementedError, match="can cache 'pattern', but cannot patch"):
        wrapper.add_hook("blocks.0.attn.hook_pattern", lambda **kwargs: kwargs["activation"])
