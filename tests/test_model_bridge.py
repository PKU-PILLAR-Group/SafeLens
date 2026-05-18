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

    def forward(self, scores: Any | None = None) -> Any:
        try:
            import torch
        except ImportError:
            pattern = _FakeAttentionPattern()
        else:
            actual_scores = scores if scores is not None else torch.zeros(1, 2, 3, 3)
            pattern = torch.softmax(actual_scores, dim=-1)
        return self.run_forward((["attn"], pattern))


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
            output = self.model.layers[0].self_attn.forward(kwargs.get("scores"))
            return {"attention": output, "output_attentions": True}
        q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
        return {"q": q_out}


class _FakeTupleOutputModel(_FakeQwenModel):
    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        output = self.model.layers[0].run_forward((["hidden"], ["present"]))
        return {"layer": output}


class _FakeBertConfig:
    model_type = "bert"


class _FakeBertAttentionSelf(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.query = _FakeModule()
        self.key = _FakeModule()
        self.value = _FakeModule()


class _FakeBertAttentionOutput:
    def __init__(self) -> None:
        self.dense = _FakeModule()


class _FakeBertAttention:
    def __init__(self) -> None:
        self.self = _FakeBertAttentionSelf()
        self.output = _FakeBertAttentionOutput()


class _FakeBertLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.attention = _FakeBertAttention()
        self.intermediate = _FakeModule()
        self.output = _FakeBertAttentionOutput()


class _FakeBertEncoder:
    def __init__(self) -> None:
        self.layer = [_FakeBertLayer()]


class _FakeBertModel:
    def __init__(self) -> None:
        self.config = _FakeBertConfig()
        self.encoder = _FakeBertEncoder()


class _FakeT5Config:
    model_type = "t5"
    decoder_start_token_id = 0
    pad_token_id = 0


class _FakeT5Model:
    config = _FakeT5Config()


class _FakeTokenizerOutput(dict):
    def to(self, device: str) -> _FakeTokenizerOutput:
        _ = device
        return self


class _FakeT5Tokenizer:
    pad_token_id = 0

    def __call__(self, text: str, return_tensors: str) -> _FakeTokenizerOutput:
        _ = text, return_tensors
        torch = pytest.importorskip("torch")
        return _FakeTokenizerOutput({"input_ids": torch.tensor([[5, 6, 7]])})


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


def test_architecture_adapter_patches_attention_patterns() -> None:
    torch = pytest.importorskip("torch")
    model = _FakeQwenModel()
    adapter = architecture_adapter_for_model(model, model_name="Qwen/Qwen3-8B")

    def force_last_source(**kwargs: Any) -> Any:
        patched = torch.zeros_like(kwargs["activation"])
        patched[..., -1] = 1
        return patched

    adapter.register_component_hook(model, "layer_0.pattern", force_last_source)

    _tokens, pattern = model.model.layers[0].self_attn.forward(torch.zeros(1, 2, 3, 3))
    assert torch.all(pattern[..., -1] == 1)


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
    assert "result" not in supported_transformer_component_names()
    assert "result" not in supported_transformer_component_names(include_attention=True)
    assert "attn_scores" not in supported_transformer_component_names()
    assert "pattern" in supported_transformer_component_names(include_pattern=True)
    assert "attn_scores" in supported_transformer_component_names(include_attention=True)


def test_architecture_adapter_rejects_merged_attention_result_hooks() -> None:
    model = _FakeQwenModel()
    adapter = architecture_adapter_for_model(model, model_name="Qwen/Qwen3-8B")

    assert "result" not in adapter.supported_components()
    with pytest.raises(NotImplementedError, match="per-head TransformerLens result"):
        adapter.register_component_hook(model, "layer_0.result", lambda **kwargs: None)


def test_bert_architecture_adapter_supports_automodel_paths() -> None:
    model = _FakeBertModel()
    adapter = architecture_adapter_for_model(model, model_name="google-bert/bert-base-uncased")

    adapter.register_component_hook(
        model,
        "layer_0.q",
        lambda **kwargs: kwargs["activation"] + ["q"],
    )
    adapter.register_component_hook(
        model,
        "layer_0.z",
        lambda **kwargs: kwargs["activation"] + ["z"],
    )

    layer = model.encoder.layer[0]
    assert layer.attention.self.query.run_forward(["x"]) == ["x", "q"]
    assert layer.attention.output.dense.run_pre(["x"]) == ["x", "z"]


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


def test_transformer_component_cache_keeps_integer_layer_cache_names() -> None:
    class _FakeResidModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            resid = self.model.layers[0].run_forward(["resid"])
            return {"resid": resid}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeResidModel()

    output, cache = wrapper.run_with_cache({"text": "hello"}, layers=[0])

    assert output == {"resid": ["resid"]}
    assert cache == {"layer_0": ["resid"]}


def test_transformer_component_cache_extracts_first_tuple_output() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeTupleOutputModel()

    output, cache = wrapper.run_with_cache({"text": "hello"}, layers=["layer_0.resid_post"])

    assert output == {"layer": (["hidden"], ["present"])}
    assert cache == {"layer_0.resid_post": ["hidden"]}


def test_transformer_component_patch_preserves_tuple_outputs() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeTupleOutputModel()

    wrapper.add_hook("layer_0.resid_post", lambda **kwargs: kwargs["activation"] + ["patched"])
    output, _cache = wrapper.run_with_cache({"text": "hello"})

    assert output == {"layer": (["hidden", "patched"], ["present"])}


def test_transformer_lens_encoder_decoder_inputs_get_decoder_start_token() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.model = _FakeT5Model()
    wrapper.tokenizer = _FakeT5Tokenizer()

    inputs = wrapper._prepare_model_inputs({"text": "translate this"})

    assert torch.equal(inputs["input_ids"], torch.tensor([[5, 6, 7]]))
    assert torch.equal(inputs["decoder_input_ids"], torch.tensor([[0]]))


def test_transformer_lens_compatible_wrapper_caches_attention_pattern() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache({"text": "hello"}, layers=["blocks.0.attn.hook_pattern"])

    assert output["output_attentions"] is True
    assert getattr(cache["blocks.0.attn.hook_pattern"], "ndim", None) == 4


def test_transformer_lens_compatible_wrapper_caches_attention_scores() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    scores = torch.randn(1, 2, 3, 3)

    output, cache = wrapper.run_with_cache(
        {"scores": scores},
        layers=["blocks.0.attn.hook_attn_scores"],
    )

    assert output["output_attentions"] is True
    assert torch.equal(cache["blocks.0.attn.hook_attn_scores"], scores)


def test_transformer_lens_compatible_wrapper_patches_attention_scores() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    def force_first_source(**kwargs: Any) -> Any:
        patched = torch.full_like(kwargs["activation"], -1000.0)
        patched[..., 0] = 1000.0
        return patched

    wrapper.add_hook("blocks.0.attn.hook_attn_scores", force_first_source)

    _tokens, pattern = wrapper.model.model.layers[0].self_attn.forward(torch.zeros(1, 2, 1, 2))
    assert torch.all(pattern[..., 0] > 0.99)
