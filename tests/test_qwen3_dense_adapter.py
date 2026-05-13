from __future__ import annotations

from typing import Any

import pytest

from SafeLens.core.base import PipelineConfig
from SafeLens.utils import (
    Qwen3DenseModelWrapper,
    build_model_wrapper,
    is_supported_qwen3_dense_model_name,
    parse_qwen3_component_ref,
    qwen3_dense_size_billion,
    validate_qwen3_dense_model_name,
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
        self.input_layernorm = _FakeModule()
        self.post_attention_layernorm = _FakeModule()
        self.self_attn = _FakeAttention()
        self.mlp = _FakeModule()


class _FakeConfig:
    model_type = "qwen3"
    num_attention_heads = 2
    num_key_value_heads = 1


class _FakeBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeLayer()]


class _FakeQwen3CausalLM:
    def __init__(self) -> None:
        self.model = _FakeBackbone()
        self.config = _FakeConfig()


def _wrapper_with_fake_model() -> Qwen3DenseModelWrapper:
    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwen3CausalLM()
    return wrapper


def test_build_model_wrapper_selects_qwen3_dense() -> None:
    config = PipelineConfig.model_validate(
        {"model": {"source": "qwen3_dense", "name": "Qwen/Qwen3-8B"}}
    )

    wrapper = build_model_wrapper(config.model)

    assert isinstance(wrapper, Qwen3DenseModelWrapper)
    assert wrapper.name == "Qwen/Qwen3-8B"


def test_qwen3_dense_name_validation() -> None:
    assert qwen3_dense_size_billion("Qwen/Qwen3-32B") == 32.0
    assert is_supported_qwen3_dense_model_name("Qwen/Qwen3-14B")
    assert not is_supported_qwen3_dense_model_name("Qwen/Qwen3-30B-A3B")

    with pytest.raises(ValueError, match="non-dense"):
        validate_qwen3_dense_model_name("Qwen/Qwen3-30B-A3B")

    with pytest.raises(ValueError, match="Only dense models"):
        validate_qwen3_dense_model_name("Qwen/Qwen3-72B")


def test_qwen3_component_name_parser_supports_safe_and_transformerlens_styles() -> None:
    assert parse_qwen3_component_ref("layer_0.resid_pre") == (0, "resid_pre")
    assert parse_qwen3_component_ref("layer_1.q") == (1, "q")
    assert parse_qwen3_component_ref("blocks.2.attn.hook_q") == (2, "q")
    assert parse_qwen3_component_ref("blocks.3.hook_mlp_out") == (3, "mlp_out")
    assert parse_qwen3_component_ref("model.layers.0") is None


def test_qwen3_residual_component_hooks_patch_inputs_and_outputs() -> None:
    wrapper = _wrapper_with_fake_model()
    layer = wrapper.model.model.layers[0]

    wrapper.add_hook("layer_0.resid_pre", lambda **kwargs: kwargs["activation"] + ["pre"])
    wrapper.add_hook("layer_0.resid_mid", lambda **kwargs: kwargs["activation"] + ["mid"])
    wrapper.add_hook("layer_0.resid_post", lambda **kwargs: kwargs["activation"] + ["post"])

    assert layer.run_pre(["x"]) == ["x", "pre"]
    assert layer.post_attention_layernorm.run_pre(["x"]) == ["x", "mid"]
    assert layer.run_forward(["x"]) == ["x", "post"]


def test_qwen3_attention_and_mlp_component_hooks_patch_outputs() -> None:
    wrapper = _wrapper_with_fake_model()
    layer = wrapper.model.model.layers[0]

    wrapper.add_hook("layer_0.attn_out", lambda **kwargs: kwargs["activation"] + ["attn"])
    wrapper.add_hook("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["mlp"])
    wrapper.add_hook("layer_0.q", lambda **kwargs: kwargs["activation"] + ["q"])
    wrapper.add_hook("blocks.0.attn.hook_k", lambda **kwargs: kwargs["activation"] + ["k"])
    wrapper.add_hook("layer_0.z", lambda **kwargs: kwargs["activation"] + ["z"])

    assert layer.self_attn.run_forward(["x"]) == ["x", "attn"]
    assert layer.mlp.run_forward(["x"]) == ["x", "mlp"]
    assert layer.self_attn.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.self_attn.k_proj.run_forward(["x"]) == ["x", "k"]
    assert layer.self_attn.o_proj.run_pre(["x"]) == ["x", "z"]


def test_qwen3_attention_pattern_hooks_are_explicitly_unsupported() -> None:
    wrapper = _wrapper_with_fake_model()

    with pytest.raises(NotImplementedError, match="attention-forward"):
        wrapper.add_hook("layer_0.pattern", lambda **kwargs: kwargs["activation"])
