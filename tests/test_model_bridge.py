from __future__ import annotations

from typing import Any

import pytest

from SafeLens.core.hooks import ActivationCache
from SafeLens.core.patching import PatchSpec, run_activation_patch
from SafeLens.utils import (
    TransformerLensCompatibleModelWrapper,
    architecture_adapter_for_model,
    architecture_adapter_for_name,
    list_architecture_adapters,
    supported_transformer_component_names,
)
from SafeLens.utils.model_bridge import (
    ComponentHookSpec,
    extract_component_activation,
    merge_component_activation,
)


class _Handle:
    def __init__(self, remove_fn: Any) -> None:
        self._remove_fn = remove_fn

    def remove(self) -> None:
        self._remove_fn()


class _FakeModule:
    def __init__(self, weight: Any | None = None) -> None:
        self.forward_hooks: list[Any] = []
        self.pre_hooks: list[Any] = []
        self.weight = weight

    def register_forward_hook(self, hook_fn: Any) -> _Handle:
        self.forward_hooks.append(hook_fn)
        return _Handle(lambda: self.forward_hooks.remove(hook_fn))

    def register_forward_pre_hook(self, hook_fn: Any) -> _Handle:
        self.pre_hooks.append(hook_fn)
        return _Handle(lambda: self.pre_hooks.remove(hook_fn))

    def run_forward(self, output: Any, inputs: tuple[Any, ...] = ()) -> Any:
        current = output
        for hook_fn in list(self.forward_hooks):
            patched = hook_fn(self, inputs, current)
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
        pattern: Any
        try:
            import torch
        except ImportError:
            pattern = _FakeAttentionPattern()
        else:
            actual_scores = scores if scores is not None else torch.zeros(1, 2, 3, 3)
            pattern = torch.softmax(actual_scores, dim=-1)
        return self.run_forward((["attn"], pattern))

    def project(self, z: Any) -> Any:
        projected = self.o_proj.run_pre(z)
        return self.o_proj.run_forward(projected, inputs=(projected,))


class _FakeLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.post_attention_layernorm = _FakeModule()
        self.self_attn = _FakeAttention()
        self.mlp = _FakeModule()


class _FakeConfig:
    model_type = "qwen3"
    num_attention_heads = 2
    num_key_value_heads = 2
    hidden_size = 4
    vocab_size = 151936
    max_position_embeddings = 32768
    intermediate_size = 16
    hidden_act = "silu"


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
        if kwargs.get("return_loss"):
            return {"loss": "loss-value", "logits": "logit-value"}
        if "z" in kwargs:
            attn_out = self.model.layers[0].self_attn.project(kwargs["z"])
            return {"attn_out": attn_out}
        q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
        return {"q": q_out}


class _FakeWeightedAttention(_FakeAttention):
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        super().__init__()
        self.q_proj = _FakeModule(torch.arange(16, dtype=torch.float32).reshape(4, 4))
        self.k_proj = _FakeModule(torch.arange(16, 32, dtype=torch.float32).reshape(4, 4))
        self.v_proj = _FakeModule(torch.arange(32, 48, dtype=torch.float32).reshape(4, 4))
        self.o_proj = _FakeModule(torch.arange(48, 64, dtype=torch.float32).reshape(4, 4))


class _FakeWeightedLayer(_FakeLayer):
    def __init__(self) -> None:
        super().__init__()
        self.self_attn = _FakeWeightedAttention()
        torch = pytest.importorskip("torch")
        self.mlp = type(
            "_WeightedMlp",
            (),
            {
                "gate_proj": _FakeModule(torch.arange(12, dtype=torch.float32).reshape(3, 4)),
                "down_proj": _FakeModule(torch.arange(12, 24, dtype=torch.float32).reshape(4, 3)),
            },
        )()


class _FakeWeightedBackbone:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.embed_tokens = _FakeModule(torch.arange(20, dtype=torch.float32).reshape(5, 4))
        self.wte = self.embed_tokens
        self.wpe = _FakeModule(torch.arange(24, dtype=torch.float32).reshape(6, 4))
        self.layers = [_FakeWeightedLayer()]


class _FakeWeightedQwenModel(_FakeQwenModel):
    def __init__(self) -> None:
        self.config = _FakeConfig()
        self.model = _FakeWeightedBackbone()


class _FakeGpt2Config:
    model_type = "gpt2"
    n_head = 2
    n_embd = 6
    n_layer = 1
    n_positions = 1024
    vocab_size = 50257
    activation_function = "gelu_new"


class _FakeGpt2Attention:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.c_attn = _FakeModule(torch.arange(90, dtype=torch.float32).reshape(5, 18))
        self.c_proj = _FakeModule(torch.arange(30, dtype=torch.float32).reshape(6, 5))


class _FakeGpt2Block:
    def __init__(self) -> None:
        self.attn = _FakeGpt2Attention()


class _FakeGpt2Transformer:
    def __init__(self) -> None:
        self.h = [_FakeGpt2Block()]


class _FakeGpt2Model:
    def __init__(self) -> None:
        self.config = _FakeGpt2Config()
        self.transformer = _FakeGpt2Transformer()


class _FakeGptNeoxConfig:
    model_type = "gpt_neox"
    num_attention_heads = 2


class _FakeGptNeoxAttention:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.query_key_value = _FakeModule(torch.arange(48, dtype=torch.float32).reshape(12, 4))


class _FakeGptNeoxLayer:
    def __init__(self) -> None:
        self.attention = _FakeGptNeoxAttention()


class _FakeGptNeoxBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeGptNeoxLayer()]


class _FakeGptNeoxModel:
    def __init__(self) -> None:
        self.config = _FakeGptNeoxConfig()
        self.gpt_neox = _FakeGptNeoxBackbone()


class _FakeHeadConfig:
    num_attention_heads = 2


class _FakeHeadModel:
    config = _FakeHeadConfig()


class _FakeGroupedHeadConfig:
    num_attention_heads = 4
    num_key_value_heads = 2


class _FakeGroupedHeadModel:
    config = _FakeGroupedHeadConfig()


class _FakeTupleOutputModel(_FakeQwenModel):
    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        output = self.model.layers[0].run_forward((["hidden"], ["present"]))
        return {"layer": output}


class _FakeBertConfig:
    model_type = "bert"
    num_attention_heads = 1


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


class _FakeDistilBertConfig:
    model_type = "distilbert"
    num_attention_heads = 1


class _FakeDistilBertAttention:
    def __init__(self) -> None:
        self.q_lin = _FakeModule()
        self.k_lin = _FakeModule()
        self.v_lin = _FakeModule()
        self.out_lin = _FakeModule()


class _FakeDistilBertLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.attention = _FakeDistilBertAttention()
        self.ffn = _FakeModule()


class _FakeDistilBertTransformer:
    def __init__(self) -> None:
        self.layer = [_FakeDistilBertLayer()]


class _FakeDistilBertModel:
    def __init__(self) -> None:
        self.config = _FakeDistilBertConfig()
        self.transformer = _FakeDistilBertTransformer()


class _FakeAudioConfig:
    model_type = "wav2vec2"
    num_attention_heads = 1


class _FakeAudioAttention:
    def __init__(self) -> None:
        self.q_proj = _FakeModule()
        self.k_proj = _FakeModule()
        self.v_proj = _FakeModule()
        self.out_proj = _FakeModule()


class _FakeAudioFeedForward:
    def __init__(self) -> None:
        self.output_dense = _FakeModule()


class _FakeAudioLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.attention = _FakeAudioAttention()
        self.feed_forward = _FakeAudioFeedForward()


class _FakeAudioEncoder:
    def __init__(self) -> None:
        self.layers = [_FakeAudioLayer()]


class _FakeAudioModel:
    def __init__(self) -> None:
        self.config = _FakeAudioConfig()
        self.encoder = _FakeAudioEncoder()


class _FakeT5Config:
    model_type = "t5"
    decoder_start_token_id = 0
    pad_token_id = 0


class _FakeT5Model:
    config = _FakeT5Config()


class _FakeEmbedding:
    def __init__(self, weight: Any) -> None:
        self.weight = weight


class _FakeUnembeddingModel:
    def __init__(self, weight: Any) -> None:
        self._weight = weight

    def get_output_embeddings(self) -> _FakeEmbedding:
        return _FakeEmbedding(self._weight)


class _FakeTokenizerOutput(dict[str, Any]):
    def to(self, device: str) -> _FakeTokenizerOutput:
        _ = device
        return self


class _FakeT5Tokenizer:
    pad_token_id = 0

    def __call__(self, text: str, return_tensors: str) -> _FakeTokenizerOutput:
        _ = text, return_tensors
        torch = pytest.importorskip("torch")
        return _FakeTokenizerOutput({"input_ids": torch.tensor([[5, 6, 7]])})


class _FakeTextTokenizer:
    bos_token_id = 0
    eos_token_id = 999

    def __call__(
        self,
        text: str,
        return_tensors: str,
        add_special_tokens: bool = True,
        padding: bool = False,
    ) -> Any:
        _ = return_tensors
        torch = pytest.importorskip("torch")
        texts = [text] if isinstance(text, str) else list(text)
        rows = []
        for item in texts:
            token_ids = [ord(char) for char in item]
            if add_special_tokens:
                token_ids = [self.bos_token_id, *token_ids]
            rows.append(token_ids)
        if padding:
            max_length = max((len(row) for row in rows), default=0)
            rows = [row + [self.eos_token_id] * (max_length - len(row)) for row in rows]
        return _FakeTokenizerOutput({"input_ids": torch.tensor(rows)})

    def decode(self, tokens: Any, skip_special_tokens: bool = False) -> str:
        token_list = tokens.tolist() if hasattr(tokens, "tolist") else list(tokens)
        if not isinstance(token_list, list):
            token_list = [token_list]
        if token_list and isinstance(token_list[0], list):
            token_list = token_list[0]
        pieces = []
        for token in token_list:
            if skip_special_tokens and token in {self.bos_token_id, self.eos_token_id}:
                continue
            if token == self.bos_token_id:
                pieces.append("<bos>")
            elif token == self.eos_token_id:
                pieces.append("<eos>")
            else:
                pieces.append(chr(int(token)))
        return "".join(pieces)

    def batch_decode(self, tokens: Any, skip_special_tokens: bool = False) -> list[str]:
        rows = tokens.tolist() if hasattr(tokens, "tolist") else tokens
        return [self.decode(row, skip_special_tokens=skip_special_tokens) for row in rows]

    def convert_ids_to_tokens(self, tokens: Any) -> Any:
        token_list = tokens.tolist() if hasattr(tokens, "tolist") else tokens
        if isinstance(token_list, int):
            return self.decode([token_list])
        return [self.decode([token]) for token in token_list]


class _FakeTokenizerAddsMultipleSpecialTokens(_FakeTextTokenizer):
    def __call__(
        self,
        text: str,
        return_tensors: str,
        add_special_tokens: bool = True,
        padding: bool = False,
    ) -> Any:
        output = super().__call__(
            text,
            return_tensors=return_tensors,
            add_special_tokens=False,
            padding=padding,
        )
        if add_special_tokens:
            torch = pytest.importorskip("torch")
            raw_ids = output["input_ids"][0].tolist()
            output["input_ids"] = torch.tensor([[self.bos_token_id, *raw_ids, self.eos_token_id]])
        return output


class _FailingTokenizer:
    @classmethod
    def from_pretrained(cls, *_args: Any, **_kwargs: Any) -> Any:
        raise OSError("missing tokenizer files")


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
    assert "result" in supported_transformer_component_names(include_attention=True)
    assert "attn_scores" not in supported_transformer_component_names()
    assert "pattern" in supported_transformer_component_names(include_pattern=True)
    assert "attn_scores" in supported_transformer_component_names(include_attention=True)


def test_architecture_adapter_patches_derived_attention_result_hooks() -> None:
    torch = pytest.importorskip("torch")
    model = _FakeQwenModel()
    weighted_attention = _FakeWeightedAttention()
    model.model.layers[0].self_attn = weighted_attention
    adapter = architecture_adapter_for_model(model, model_name="Qwen/Qwen3-8B")
    z = torch.arange(4, dtype=torch.float32).reshape(1, 1, 4)

    def zero_first_head(**kwargs: Any) -> Any:
        patched = kwargs["activation"].clone()
        patched[..., 0, :] = 0
        return patched

    assert "result" in adapter.supported_components()
    assert "result" in adapter.supported_components(for_cache=True)
    adapter.register_component_hook(model, "layer_0.result", zero_first_head)

    original_result = torch.einsum(
        "bphd,hdm->bphm",
        z.reshape(1, 1, 2, 2),
        weighted_attention.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0),
    )
    expected = z - original_result[..., 0, :]
    assert torch.equal(weighted_attention.project(z), expected)


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


def test_distilbert_architecture_adapter_supports_encoder_paths() -> None:
    model = _FakeDistilBertModel()
    adapter = architecture_adapter_for_model(model, model_name="distilbert-base-uncased")

    assert adapter.name == "distilbert_encoder"
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

    layer = model.transformer.layer[0]
    assert layer.attention.q_lin.run_forward(["x"]) == ["x", "q"]
    assert layer.attention.out_lin.run_pre(["x"]) == ["x", "z"]


def test_audio_architecture_adapter_supports_encoder_paths() -> None:
    model = _FakeAudioModel()
    adapter = architecture_adapter_for_model(model, model_name="facebook/wav2vec2-base")

    assert adapter.name == "audio_encoder"
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

    layer = model.encoder.layers[0]
    assert layer.attention.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.attention.out_proj.run_pre(["x"]) == ["x", "z"]


def test_architecture_adapter_can_infer_from_model_name_without_loading_config() -> None:
    assert architecture_adapter_for_name(model_name="gpt2-small").name == "gpt2_decoder"
    assert (
        architecture_adapter_for_name(model_name="EleutherAI/pythia-70m").name == "gpt_neox_decoder"
    )
    assert (
        architecture_adapter_for_name(model_name="google-bert/bert-base-uncased").name
        == "bert_encoder"
    )
    assert (
        architecture_adapter_for_name(model_name="FacebookAI/roberta-base").name == "bert_encoder"
    )
    assert (
        architecture_adapter_for_name(model_name="distilbert/distilbert-base-uncased").name
        == "distilbert_encoder"
    )
    assert (
        architecture_adapter_for_name(model_name="facebook/wav2vec2-base").name == "audio_encoder"
    )
    assert (
        architecture_adapter_for_name(model_name="facebook/hubert-base-ls960").name
        == "audio_encoder"
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

    output, cache = wrapper.run_with_cache({"input_ids": [[1, 2]]}, layers=["blocks.0.attn.hook_q"])

    assert output == {"q": ["q"]}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}


def test_transformer_lens_compatible_wrapper_accepts_token_inputs_directly() -> None:
    torch = pytest.importorskip("torch")

    class _EchoTokensQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            logits = kwargs["input_ids"] * 10
            return {"input_ids": kwargs["input_ids"], "logits": logits, "q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _EchoTokensQwenModel()

    output, cache = wrapper.run_with_cache(
        torch.tensor([1, 2]),
        layers=["blocks.0.attn.hook_q"],
    )

    assert torch.equal(output, torch.tensor([[10, 20]]))
    assert cache == {"blocks.0.attn.hook_q": ["q"]}

    output, _cache = wrapper.run_with_cache(
        torch.tensor([1, 2]),
        return_type="model_output",
    )
    assert torch.equal(output["input_ids"], torch.tensor([[1, 2]]))

    output = wrapper.run_with_hooks(
        [3, 4],
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"])],
        return_type="model_output",
    )
    assert output["input_ids"] == [[3, 4]]
    assert output["q"] == ["q", "patched"]


def test_transformer_lens_compatible_wrapper_token_inputs_cache_all_by_default() -> None:
    torch = pytest.importorskip("torch")

    class _TokenCacheQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            logits = kwargs["input_ids"] * 10
            return {"logits": logits, "q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _TokenCacheQwenModel()

    logits, cache = wrapper.run_with_cache(torch.tensor([1, 2]))

    assert torch.equal(logits, torch.tensor([[10, 20]]))
    assert isinstance(cache, ActivationCache)
    assert cache[("q", 0)] == ["q"]
    assert cache.model is wrapper


def test_transformer_lens_compatible_wrapper_default_cache_skips_attention_scores() -> None:
    torch = pytest.importorskip("torch")

    class _TokenCacheQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            if kwargs.get("output_attentions"):
                self.model.layers[0].self_attn.forward(torch.zeros(1, 2, 1, 2))
            return {"logits": kwargs["input_ids"], "q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _TokenCacheQwenModel()

    _logits, cache = wrapper.run_with_cache(torch.tensor([1, 2]))

    assert isinstance(cache, ActivationCache)
    assert ("pattern", 0) in cache
    assert ("attn_scores", 0) not in cache


def test_transformer_lens_compatible_wrapper_mapping_inputs_keep_legacy_empty_cache_default() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache({"input_ids": [[1, 2]]})

    assert output == {"q": ["q"]}
    assert cache == {}


def test_transformer_lens_compatible_wrapper_mapping_inputs_can_explicitly_cache_all() -> None:
    class _CacheAllQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            return {"q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _CacheAllQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        cache_all=True,
        return_cache_object=True,
    )

    assert output == {"q": ["q"]}
    assert isinstance(cache, ActivationCache)
    assert cache[("q", 0)] == ["q"]


def test_transformer_lens_compatible_wrapper_persistent_cache_hooks() -> None:
    class _PersistentCacheQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(
                ["q", kwargs["input_ids"][0][-1]]
            )
            return {"q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _PersistentCacheQwenModel()

    cache = wrapper.cache_some(lambda name: name.endswith(".hook_q"))
    assert isinstance(cache, ActivationCache)

    assert wrapper({"input_ids": [[1, 2]]}, return_type="model_output") == {"q": ["q", 2]}
    assert cache[("q", 0)] == ["q", 2]

    wrapper.reset_hooks()

    assert wrapper({"input_ids": [[1, 3]]}, return_type="model_output") == {"q": ["q", 3]}
    assert cache[("q", 0)] == ["q", 3]

    wrapper.reset_hooks(including_permanent=True)
    wrapper({"input_ids": [[1, 4]]}, return_type="model_output")

    assert cache[("q", 0)] == ["q", 3]


def test_transformer_lens_compatible_wrapper_preserves_empty_external_cache() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    external_cache = ActivationCache()

    cache = wrapper.add_caching_hooks(
        layers=["blocks.0.attn.hook_q"],
        cache=external_cache,
    )
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache is external_cache
    assert external_cache.model is wrapper
    assert external_cache[("q", 0)] == ["q"]


def test_transformer_lens_compatible_wrapper_add_caching_hooks_defaults_to_cache_all() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    cache = wrapper.add_caching_hooks()
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache[("pattern", 0)].ndim == 4
    assert ("attn_scores", 0) not in cache

    wrapper.reset_hooks(including_permanent=True)
    empty_cache = wrapper.add_caching_hooks(cache_all=False)
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert empty_cache.to_dict() == {}


def test_transformer_lens_compatible_wrapper_caching_hooks_remove_batch_dim() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    cache = wrapper.add_caching_hooks(
        layers=["blocks.0.attn.hook_q"],
        remove_batch_dim=True,
    )

    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache.has_batch_dim is False
    assert cache["blocks.0.attn.hook_q"] == "q"


def test_transformer_lens_compatible_wrapper_call_returns_logits_by_default() -> None:
    class _LogitQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            return {"loss": "loss-value", "logits": "logit-value"}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitQwenModel()

    assert wrapper([1, 2]) == "logit-value"
    assert wrapper({"input_ids": [[1, 2]], "return_loss": True}, return_type="logits") == "logit-value"
    assert wrapper({"input_ids": [[1, 2]], "return_loss": True}, return_type="loss") == "loss-value"
    assert wrapper({"input_ids": [[1, 2]], "return_loss": True}, return_type=None) is None


def test_transformer_lens_compatible_wrapper_call_does_not_cache_token_inputs() -> None:
    torch = pytest.importorskip("torch")

    class _NoImplicitCacheQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            if kwargs.get("output_attentions"):
                raise AssertionError("__call__ should not add default cache attention hooks")
            return {"logits": kwargs["input_ids"] * 10}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _NoImplicitCacheQwenModel()

    assert torch.equal(wrapper(torch.tensor([1, 2])), torch.tensor([[10, 20]]))


def test_transformer_lens_compatible_wrapper_extracts_tuple_logits_after_loss() -> None:
    torch = pytest.importorskip("torch")

    class _TupleQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> tuple[Any, ...]:
            logits = torch.tensor([[[1.0, 2.0]]])
            if kwargs.get("return_loss"):
                return torch.tensor(0.5), logits
            return (logits,)

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _TupleQwenModel()

    output, _cache = wrapper.run_with_cache([1, 2])
    assert torch.equal(output, torch.tensor([[[1.0, 2.0]]]))

    output, _cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]], "return_loss": True},
        return_type="logits",
    )
    assert torch.equal(output, torch.tensor([[[1.0, 2.0]]]))

    output, _cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]], "return_loss": True},
        return_type="loss",
    )
    assert torch.equal(output, torch.tensor(0.5))


def test_transformer_lens_compatible_wrapper_run_with_cache_accepts_names_filter() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter=lambda name: name == "blocks.0.attn.hook_q",
    )

    assert output == {"q": ["q"]}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}


def test_transformer_lens_compatible_wrapper_names_filter_dedupes_aliases_for_cache() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter=lambda name: name.endswith(".q") or name.endswith(".hook_q"),
    )

    assert output == {"q": ["q"]}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}


def test_transformer_lens_compatible_wrapper_run_with_cache_can_return_activation_cache() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter="blocks.0.attn.hook_q",
        return_cache_object=True,
    )

    assert isinstance(cache, ActivationCache)
    assert cache[("q", 0)] == ["q"]
    assert cache.model is wrapper


def test_transformer_lens_compatible_wrapper_string_names_filter_matches_aliases() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter="layer_0.q",
    )

    assert output == {"q": ["q"]}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}


def test_transformer_lens_compatible_wrapper_can_patch_from_cache_by_hook_name() -> None:
    clean_wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    clean_wrapper.model = _FakeQwenModel()
    _clean_output, clean_cache = clean_wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter=lambda name: name.endswith(".q") or name.endswith(".hook_q"),
        return_cache_object=True,
    )

    corrupted_wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    corrupted_wrapper.model = _FakeQwenModel()

    def patch_from_clean_cache(activation: Any, hook: Any) -> Any:
        return clean_cache[hook.name] + ["patched"]

    output = corrupted_wrapper.run_with_hooks(
        {"input_ids": [[3, 4]]},
        fwd_hooks=[("blocks.0.attn.hook_q", patch_from_clean_cache)],
    )

    assert output == {"q": ["q", "patched"]}


def test_transformer_lens_compatible_wrapper_run_with_cache_remove_batch_dim() -> None:
    class _BatchDimQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            q_out = self.model.layers[0].self_attn.q_proj.run_forward([[["q0"], ["q1"]]])
            return {"q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _BatchDimQwenModel()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_q"],
        remove_batch_dim=True,
        return_cache_object=True,
    )

    assert isinstance(cache, ActivationCache)
    assert cache.has_batch_dim is False
    assert cache["blocks.0.attn.hook_q"] == [["q0"], ["q1"]]


def test_transformer_lens_compatible_wrapper_empty_cache_preserves_remove_batch_dim_flag() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        remove_batch_dim=True,
        return_cache_object=True,
    )

    assert isinstance(cache, ActivationCache)
    assert cache.cache_dict == {}
    assert cache.has_batch_dim is False


def test_transformer_lens_compatible_wrapper_run_with_cache_prepares_cached_values() -> None:
    torch = pytest.importorskip("torch")
    moved_devices: list[str] = []

    class _DeviceAwareTensor:
        def __init__(self, tensor: Any) -> None:
            self.tensor = tensor
            self.requires_grad = tensor.requires_grad
            self.shape = tensor.shape

        @property
        def ndim(self) -> int:
            return self.tensor.ndim

        def __getitem__(self, index: Any) -> _DeviceAwareTensor:
            return _DeviceAwareTensor(self.tensor[index])

        def detach(self) -> _DeviceAwareTensor:
            return _DeviceAwareTensor(self.tensor.detach())

        def clone(self) -> _DeviceAwareTensor:
            return _DeviceAwareTensor(self.tensor.clone())

        def to(self, device: str) -> _DeviceAwareTensor:
            moved_devices.append(device)
            return self

    class _TensorCacheQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            activation = torch.arange(12, dtype=torch.float32).reshape(1, 3, 2, 2)
            activation.requires_grad_(True)
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(
                _DeviceAwareTensor(activation)
            )
            return {"q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _TensorCacheQwenModel()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2, 3]]},
        layers=["blocks.0.attn.hook_q"],
        pos_slice=1,
        detach=True,
        clone=True,
        device="cpu",
        return_cache_object=True,
    )

    cached = cache["blocks.0.attn.hook_q"]
    assert isinstance(cached, _DeviceAwareTensor)
    assert tuple(cached.shape) == (1, 2, 2)
    assert cached.requires_grad is False
    assert moved_devices == ["cpu"]


def test_transformer_component_cache_keeps_integer_layer_cache_names() -> None:
    class _FakeResidModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            resid = self.model.layers[0].run_forward(["resid"])
            return {"resid": resid}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeResidModel()

    output, cache = wrapper.run_with_cache({"input_ids": [[1, 2]]}, layers=[0])

    assert output == {"resid": ["resid"]}
    assert cache == {"layer_0": ["resid"]}


def test_transformer_component_cache_extracts_first_tuple_output() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeTupleOutputModel()

    output, cache = wrapper.run_with_cache({"input_ids": [[1, 2]]}, layers=["layer_0.resid_post"])

    assert output == {"layer": (["hidden"], ["present"])}
    assert cache == {"layer_0.resid_post": ["hidden"]}


def test_transformer_component_patch_preserves_tuple_outputs() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeTupleOutputModel()

    wrapper.add_hook("layer_0.resid_post", lambda **kwargs: kwargs["activation"] + ["patched"])
    output, _cache = wrapper.run_with_cache({"input_ids": [[1, 2]]})

    assert output == {"layer": (["hidden", "patched"], ["present"])}


def test_transformer_lens_compatible_wrapper_run_with_hooks_is_temporary() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert output == {"q": ["q", "patched"]}
    assert wrapper.model.model.layers[0].self_attn.q_proj.run_forward(["q"]) == ["q"]
    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_run_with_hooks_does_not_cache_token_inputs() -> None:
    torch = pytest.importorskip("torch")

    class _NoImplicitCacheQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            if kwargs.get("output_attentions"):
                raise AssertionError("run_with_hooks should not add default cache attention hooks")
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            return {"logits": kwargs["input_ids"] * 10, "q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _NoImplicitCacheQwenModel()

    logits = wrapper.run_with_hooks(
        torch.tensor([1, 2]),
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert torch.equal(logits, torch.tensor([[10, 20]]))


def test_run_activation_patch_with_wrapper_token_inputs_scores_logits() -> None:
    torch = pytest.importorskip("torch")

    class _PatchLogitsQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(
                torch.zeros(1, 2, 2, dtype=torch.float32)
            )
            return {"logits": q_out.sum(dim=-1)}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _PatchLogitsQwenModel()
    clean_cache = ActivationCache(
        {"blocks.0.attn.hook_q": torch.tensor([[[[5.0], [7.0]], [[11.0], [13.0]]]])}
    )

    result = run_activation_patch(
        wrapper,
        torch.tensor([1, 2]),
        clean_cache,
        PatchSpec(
            layer="blocks.0.attn.hook_q",
            activation_name="blocks.0.attn.hook_q",
        ),
        metric=lambda logits: float(logits[0, 1]),
    )

    assert result.metric == 24.0
    assert torch.equal(result.output, torch.tensor([[12.0, 24.0]]))
    assert result.cache == {}
    assert wrapper._hooks == []


def test_run_activation_patch_with_wrapper_layers_preserves_cache() -> None:
    torch = pytest.importorskip("torch")

    class _PatchLogitsQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(
                torch.zeros(1, 1, 2, dtype=torch.float32)
            )
            return {"logits": q_out.sum(dim=-1)}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _PatchLogitsQwenModel()
    clean_cache = ActivationCache(
        {"blocks.0.attn.hook_q": torch.tensor([[[[5.0], [7.0]]]])}
    )

    result = run_activation_patch(
        wrapper,
        {"input_ids": [[1]]},
        clean_cache,
        PatchSpec(
            layer="blocks.0.attn.hook_q",
            activation_name="blocks.0.attn.hook_q",
        ),
        metric=lambda output: float(output["logits"][0, 0]),
        layers=["blocks.0.attn.hook_q"],
    )

    assert result.metric == 12.0
    assert torch.equal(result.output["logits"], torch.tensor([[12.0]]))
    assert torch.equal(
        result.cache["blocks.0.attn.hook_q"],
        torch.tensor([[[[5.0], [7.0]]]]),
    )
    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_component_hooks_receive_hook_context() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    seen: list[tuple[str, int]] = []

    def append_hook_metadata(activation: Any, hook: Any) -> Any:
        seen.append((hook.name, hook.layer()))
        hook.ctx["seen"] = True
        return activation + [hook.name, hook.layer(), hook.ctx["seen"]]

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.attn.hook_q", append_hook_metadata)],
    )

    assert output == {"q": ["q", "blocks.0.attn.hook_q", 0, True]}
    assert seen == [("blocks.0.attn.hook_q", 0)]


def test_transformer_lens_compatible_wrapper_hook_context_persists_across_calls() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    def count_calls(activation: Any, hook: Any) -> Any:
        hook.ctx["count"] = hook.ctx.get("count", 0) + 1
        return activation + [hook.ctx["count"]]

    wrapper.add_hook("blocks.0.attn.hook_q", count_calls)

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", 1]}
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", 2]}


def test_transformer_lens_compatible_wrapper_run_with_hooks_accepts_name_filter() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[(lambda name: name.endswith(".hook_q"), lambda **kwargs: ["filtered"])],
    )

    assert output == {"q": ["filtered"]}


def test_transformer_lens_compatible_wrapper_run_with_hooks_filter_dedupes_aliases() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    calls = 0

    def append_once(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return kwargs["activation"] + ["patched"]

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[(lambda name: name.endswith(".q") or name.endswith(".hook_q"), append_once)],
    )

    assert output == {"q": ["q", "patched"]}
    assert calls == 1


def test_transformer_lens_compatible_wrapper_permanent_hooks_survive_default_reset() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_perma_hook(
        "blocks.0.attn.hook_q",
        lambda **kwargs: kwargs["activation"] + ["permanent"],
    )
    wrapper.add_hook("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["temp"])

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "q": ["q", "permanent", "temp"]
    }

    wrapper.reset_hooks()

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "permanent"]}

    wrapper.reset_hooks(including_permanent=True)

    assert wrapper._hooks == []
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


def test_transformer_lens_compatible_wrapper_hooks_context_is_temporary() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_perma_hook(
        "blocks.0.attn.hook_q",
        lambda **kwargs: kwargs["activation"] + ["permanent"],
    )

    with wrapper.hooks(
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["temp"])],
    ):
        output = wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]

    assert output == {"q": ["q", "permanent", "temp"]}
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "permanent"]}


def test_transformer_lens_compatible_wrapper_reset_hooks_can_clear_contexts() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    def count_calls(activation: Any, hook: Any) -> Any:
        hook.ctx["count"] = hook.ctx.get("count", 0) + 1
        return activation + [hook.ctx["count"]]

    wrapper.add_perma_hook("blocks.0.attn.hook_q", count_calls)

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", 1]}
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", 2]}

    wrapper.reset_hooks()

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", 1]}


def test_transformer_lens_compatible_run_with_hooks_attention_flag_is_temporary() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.attn.hook_pattern", lambda **_kwargs: None)],
    )

    assert output["output_attentions"] is True
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


def test_transformer_lens_compatible_run_with_cache_cleans_up_after_invalid_layer() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    q_proj = wrapper.model.model.layers[0].self_attn.q_proj

    with pytest.raises(KeyError):
        wrapper.run_with_cache(
            {"input_ids": [[1, 2]]},
            layers=["blocks.0.attn.hook_q", "blocks.99.attn.hook_q"],
        )

    assert q_proj.forward_hooks == []
    assert q_proj.run_forward(["q"]) == ["q"]


def test_transformer_lens_encoder_decoder_inputs_get_decoder_start_token() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.model = _FakeT5Model()
    wrapper.tokenizer = _FakeT5Tokenizer()

    inputs = wrapper._prepare_model_inputs({"text": "translate this"})

    assert torch.equal(inputs["input_ids"], torch.tensor([[5, 6, 7]]))
    assert torch.equal(inputs["decoder_input_ids"], torch.tensor([[0]]))


def test_huggingface_wrapper_allows_tensor_inputs_when_tokenizer_is_missing() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="hf-internal-testing/tiny-random-mixtral")
    tokenizer = wrapper._load_text_tokenizer(_FailingTokenizer, "missing-tokenizer", {})

    assert tokenizer is None
    inputs = wrapper._prepare_model_inputs({"input_ids": torch.tensor([[1, 2, 3]])})
    assert torch.equal(inputs["input_ids"], torch.tensor([[1, 2, 3]]))
    inputs = wrapper._prepare_model_inputs(torch.tensor([1, 2, 3]))
    assert torch.equal(inputs["input_ids"], torch.tensor([[1, 2, 3]]))
    assert wrapper._prepare_model_inputs([1, 2, 3])["input_ids"] == [[1, 2, 3]]
    assert wrapper._prepare_model_inputs(7)["input_ids"] == [[7]]
    with pytest.raises(ValueError, match="did not load a tokenizer"):
        wrapper._prepare_model_inputs({"text": "needs tokenizer"})
    wrapper.model = _FakeQwenModel()
    with pytest.raises(RuntimeError, match="Tokenizer is not loaded"):
        wrapper.generate("needs tokenizer")


def test_transformer_lens_compatible_wrapper_tokenization_helpers() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()

    tokens = wrapper.to_tokens("ab")

    assert torch.equal(tokens, torch.tensor([[0, 97, 98]]))
    assert torch.equal(wrapper.to_tokens("ab", prepend_bos=False), torch.tensor([[97, 98]]))
    assert wrapper.to_string(tokens[0], skip_special_tokens=True) == "ab"
    assert wrapper.to_string(tokens, skip_special_tokens=True) == ["ab"]
    assert wrapper.to_string(ord("a")) == "a"
    assert wrapper.to_string([0, 97, 98], skip_special_tokens=True) == "ab"
    assert wrapper.to_string([[0, 97], [0, 98]], skip_special_tokens=True) == ["a", "b"]
    with pytest.raises(ValueError, match="Invalid token shape"):
        wrapper.to_string([[[0, 97]]], skip_special_tokens=True)
    assert wrapper.to_str_tokens("ab") == ["<bos>", "a", "b"]
    assert wrapper.to_str_tokens([0, 97]) == ["<bos>", "a"]
    assert wrapper.to_str_tokens([[0, 97], [0, 98]]) == [["<bos>", "a"], ["<bos>", "b"]]
    with pytest.raises(ValueError, match="Invalid token shape"):
        wrapper.to_str_tokens(torch.tensor([[0, 97], [0, 98]]))
    assert wrapper.to_single_token("z") == ord("z")
    assert wrapper.to_single_str_token(ord("z")) == "z"
    with pytest.raises(ValueError, match="single token"):
        wrapper.to_single_token("zz")
    assert wrapper.get_token_position("a", "abca", mode="first") == 1
    assert wrapper.get_token_position("a", "abca", mode="last") == 4
    assert wrapper.get_token_position(ord("b"), torch.tensor([[0, 97, 98]])) == 2
    assert wrapper.get_token_position(ord("b"), [0, 97, 98]) == 2
    with pytest.raises(ValueError, match="does not occur"):
        wrapper.get_token_position("z", "abc")
    with pytest.raises(ValueError, match="mode"):
        wrapper.get_token_position("a", "abc", mode="middle")


def test_transformer_lens_compatible_wrapper_tokenizes_text_batches() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()

    tokens = wrapper.to_tokens(["ab", "cd"])

    assert torch.equal(tokens, torch.tensor([[0, 97, 98], [0, 99, 100]]))
    assert wrapper.to_string(tokens, skip_special_tokens=True) == ["ab", "cd"]


def test_transformer_lens_compatible_wrapper_pads_uneven_text_batches() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()

    tokens = wrapper.to_tokens(["a", "bc"])

    assert torch.equal(tokens, torch.tensor([[0, 97, 999], [0, 98, 99]]))
    assert wrapper.to_string(tokens, skip_special_tokens=True) == ["a", "bc"]


def test_transformer_lens_compatible_wrapper_to_tokens_prepends_only_bos() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTokenizerAddsMultipleSpecialTokens()

    tokens = wrapper.to_tokens("ab", prepend_bos=True)

    assert torch.equal(tokens, torch.tensor([[0, 97, 98]]))


def test_transformer_lens_compatible_wrapper_residual_directions() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    weight = torch.tensor(
        [
            [1.0, 10.0],
            [2.0, 20.0],
            [3.0, 30.0],
        ]
    )
    wrapper.model = _FakeUnembeddingModel(weight)

    directions = wrapper.tokens_to_residual_directions(torch.tensor([[0, 2]]))

    assert torch.equal(directions, torch.tensor([[[1.0, 10.0], [3.0, 30.0]]]))


def test_transformer_lens_compatible_wrapper_residual_directions_accept_scalar_tokens() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()
    weight = torch.eye(128)
    wrapper.model = _FakeUnembeddingModel(weight)

    assert torch.equal(wrapper.tokens_to_residual_directions("z"), weight[ord("z")])
    assert torch.equal(wrapper.tokens_to_residual_directions(ord("z")), weight[ord("z")])
    assert torch.equal(
        wrapper.tokens_to_residual_directions(torch.tensor(ord("z"))),
        weight[ord("z")],
    )
    with pytest.raises(ValueError, match="single token"):
        wrapper.tokens_to_residual_directions("zz")


def test_transformer_lens_compatible_wrapper_exposes_unembed_matrix() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    weight = torch.tensor(
        [
            [1.0, 10.0],
            [2.0, 20.0],
            [3.0, 30.0],
        ]
    )
    wrapper.model = _FakeUnembeddingModel(weight)

    assert torch.equal(wrapper.W_U, weight.T)


def test_transformer_lens_compatible_wrapper_exposes_attention_weight_matrices() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    attention = wrapper.model.model.layers[0].self_attn

    expected_q = attention.q_proj.weight.reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_k = attention.k_proj.weight.reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_v = attention.v_proj.weight.reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_o = attention.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0).unsqueeze(0)

    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)
    assert torch.equal(wrapper.W_O, expected_o)


def test_transformer_lens_compatible_wrapper_exposes_transformerlens_cfg_view() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()

    cfg = wrapper.cfg

    assert cfg.model_name == "Qwen/Qwen3-8B"
    assert cfg.model_type == "qwen3"
    assert cfg.n_layers == 1
    assert cfg.n_heads == 2
    assert cfg.n_key_value_heads == 2
    assert cfg.d_model == 4
    assert cfg.d_head == 2
    assert cfg.d_vocab == 151936
    assert cfg.n_ctx == 32768
    assert cfg.d_mlp == 16
    assert cfg.act_fn == "silu"
    assert cfg.normalization_type == "RMS"
    assert cfg.to_dict()["n_layers"] == 1
    assert list(range(cfg.n_layers)) == [0]


def test_transformer_lens_compatible_wrapper_exposes_gpt2_joint_qkv_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()
    attention = wrapper.model.transformer.h[0].attn
    weight = attention.c_attn.weight

    expected_q = weight[:, :6].reshape(5, 2, 3).permute(1, 0, 2).unsqueeze(0)
    expected_k = weight[:, 6:12].reshape(5, 2, 3).permute(1, 0, 2).unsqueeze(0)
    expected_v = weight[:, 12:].reshape(5, 2, 3).permute(1, 0, 2).unsqueeze(0)
    expected_o = attention.c_proj.weight.reshape(2, 3, 5).unsqueeze(0)

    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)
    assert torch.equal(wrapper.W_O, expected_o)

    cfg = wrapper.cfg
    assert cfg.n_layers == 1
    assert cfg.n_heads == 2
    assert cfg.d_model == 6
    assert cfg.d_head == 3
    assert cfg.d_vocab == 50257
    assert cfg.n_ctx == 1024
    assert cfg.act_fn == "gelu_new"
    assert cfg.normalization_type == "LN"


def test_transformer_lens_compatible_wrapper_exposes_neox_joint_qkv_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="EleutherAI/pythia-70m")
    wrapper.model = _FakeGptNeoxModel()
    weight = wrapper.model.gpt_neox.layers[0].attention.query_key_value.weight
    interleaved = weight.reshape(2, 3, 2, 4)

    expected_q = interleaved[:, 0].reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_k = interleaved[:, 1].reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_v = interleaved[:, 2].reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)

    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)


def test_transformer_lens_compatible_wrapper_exposes_embedding_and_mlp_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    model = wrapper.model.model
    mlp = model.layers[0].mlp

    assert torch.equal(wrapper.W_E, model.embed_tokens.weight)
    assert torch.equal(wrapper.W_pos, model.wpe.weight)
    assert torch.equal(wrapper.W_in, mlp.gate_proj.weight.T.unsqueeze(0))
    assert torch.equal(wrapper.W_out, mlp.down_proj.weight.T.unsqueeze(0))


def test_transformer_lens_compatible_wrapper_caches_attention_pattern() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_pattern"],
    )

    assert output["output_attentions"] is True
    assert getattr(cache["blocks.0.attn.hook_pattern"], "ndim", None) == 4


def test_transformer_lens_compatible_wrapper_caches_derived_attention_result() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    z = torch.arange(4, dtype=torch.float32).reshape(1, 1, 4)

    output, cache = wrapper.run_with_cache(
        {"z": z},
        layers=["blocks.0.attn.hook_result"],
    )

    z_by_head = z.reshape(1, 1, 2, 2)
    W_O = wrapper.model.model.layers[0].self_attn.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0)
    expected = torch.einsum("bphd,hdm->bphm", z_by_head, W_O)
    assert torch.equal(output["attn_out"], z)
    assert torch.equal(cache["blocks.0.attn.hook_result"], expected)


def test_transformer_lens_compatible_wrapper_cache_filter_can_select_result() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()

    _output, cache = wrapper.run_with_cache(
        {"z": torch.zeros(1, 1, 4)},
        names_filter=lambda name: name.endswith(".hook_result"),
    )

    assert set(cache) == {"blocks.0.attn.hook_result"}


def test_transformer_lens_compatible_hook_filter_can_patch_result() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    z = torch.arange(4, dtype=torch.float32).reshape(1, 1, 4)

    output = wrapper.run_with_hooks(
        {"z": z},
        fwd_hooks=[
            (
                lambda name: name.endswith(".hook_result"),
                lambda **kwargs: kwargs["activation"] * 0,
            )
        ],
    )

    original_result = torch.einsum(
        "bphd,hdm->bphm",
        z.reshape(1, 1, 2, 2),
        wrapper.model.model.layers[0].self_attn.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0),
    )
    expected = z - original_result.sum(dim=-2)
    assert torch.equal(output["attn_out"], expected)


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


def test_transformer_lens_compatible_wrapper_caches_attention_pattern_and_scores() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    scores = torch.randn(1, 2, 3, 3)

    output, cache = wrapper.run_with_cache(
        {"scores": scores},
        layers=[
            "blocks.0.attn.hook_pattern",
            "blocks.0.attn.hook_attn_scores",
        ],
    )

    assert output["output_attentions"] is True
    assert torch.equal(cache["blocks.0.attn.hook_attn_scores"], scores)
    assert torch.allclose(cache["blocks.0.attn.hook_pattern"], torch.softmax(scores, dim=-1))


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


def test_attention_hook_remove_clears_output_attentions_flag() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    handle = wrapper.add_hook("blocks.0.attn.hook_pattern", lambda **_kwargs: None)
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]["output_attentions"] is True

    handle.remove()

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}
    assert wrapper._hooks == []


def test_transformer_lens_compatible_handle_remove_untracks_hook() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    handle = wrapper.add_hook("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"])
    assert wrapper._hooks == [handle]

    handle.remove()

    assert wrapper._hooks == []
    assert wrapper.model.model.layers[0].self_attn.q_proj.forward_hooks == []
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


def test_remove_hooks_clears_multiple_attention_output_flags() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook("blocks.0.attn.hook_pattern", lambda **_kwargs: None)
    wrapper.add_hook("blocks.0.attn.hook_attn_scores", lambda **_kwargs: None)
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]["output_attentions"] is True

    wrapper.remove_hooks()

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


def test_transformer_lens_compatible_reset_hooks_clears_attention_output_flags() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook("blocks.0.attn.hook_pattern", lambda **_kwargs: None)
    wrapper.add_hook("blocks.0.attn.hook_attn_scores", lambda **_kwargs: None)
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]["output_attentions"] is True

    wrapper.reset_hooks()

    assert wrapper._hooks == []
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


def test_attention_softmax_hook_handles_remove_independently() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    score_calls = 0
    pattern_calls = 0

    def record_scores(**_kwargs: Any) -> None:
        nonlocal score_calls
        score_calls += 1

    def record_pattern(**_kwargs: Any) -> None:
        nonlocal pattern_calls
        pattern_calls += 1

    score_handle = wrapper.add_hook("blocks.0.attn.hook_attn_scores", record_scores)
    pattern_handle = wrapper.add_hook("blocks.0.attn.hook_pattern", record_pattern)

    score_handle.remove()
    wrapper.model.model.layers[0].self_attn.forward(torch.randn(1, 2, 3, 3))

    assert score_calls == 0
    assert pattern_calls == 1

    pattern_handle.remove()
    wrapper.model.model.layers[0].self_attn.forward(torch.randn(1, 2, 3, 3))

    assert score_calls == 0
    assert pattern_calls == 1


def test_component_bridge_splits_and_merges_head_projections() -> None:
    torch = pytest.importorskip("torch")
    spec = ComponentHookSpec(
        component="q",
        mode="forward_output",
        module_paths=("unused",),
        activation="split_heads",
    )
    raw = torch.arange(16).reshape(1, 2, 8)

    activation = extract_component_activation(raw, spec, _FakeHeadModel())

    assert activation.shape == (1, 2, 2, 4)
    patched = activation.clone()
    patched[:, :, 1, :] = -1
    merged = merge_component_activation(patched, raw, spec, _FakeHeadModel())
    assert merged.shape == raw.shape
    assert torch.equal(merged[:, :, :4], raw[:, :, :4])
    assert torch.all(merged[:, :, 4:] == -1)


def test_component_bridge_splits_and_merges_split_qkv_projection() -> None:
    torch = pytest.importorskip("torch")
    spec = ComponentHookSpec(
        component="k",
        mode="forward_output",
        module_paths=("unused",),
        activation="split_qkv_heads",
    )
    raw = torch.arange(48).reshape(1, 2, 24)

    activation = extract_component_activation(raw, spec, _FakeHeadModel())

    assert activation.shape == (1, 2, 2, 4)
    assert torch.equal(activation.reshape(1, 2, 8), raw[..., 8:16])
    patched = torch.full_like(activation, -7)
    merged = merge_component_activation(patched, raw, spec, _FakeHeadModel())
    assert torch.equal(merged[..., :8], raw[..., :8])
    assert torch.all(merged[..., 8:16] == -7)
    assert torch.equal(merged[..., 16:], raw[..., 16:])


def test_component_bridge_splits_and_merges_interleaved_qkv_projection() -> None:
    torch = pytest.importorskip("torch")
    spec = ComponentHookSpec(
        component="v",
        mode="forward_output",
        module_paths=("unused",),
        activation="split_qkv_heads",
        qkv_layout="interleaved",
    )
    raw = torch.arange(48).reshape(1, 2, 24)

    activation = extract_component_activation(raw, spec, _FakeHeadModel())

    assert activation.shape == (1, 2, 2, 4)
    assert torch.equal(activation, raw.reshape(1, 2, 2, 3, 4)[..., 2, :])
    patched = torch.full_like(activation, -3)
    merged = merge_component_activation(patched, raw, spec, _FakeHeadModel())
    expected = raw.reshape(1, 2, 2, 3, 4).clone()
    expected[..., 2, :] = -3
    assert torch.equal(merged, expected.reshape_as(raw))


def test_component_bridge_splits_and_merges_grouped_interleaved_qkv_projection() -> None:
    torch = pytest.importorskip("torch")
    spec = ComponentHookSpec(
        component="k",
        mode="forward_output",
        module_paths=("unused",),
        activation="split_qkv_heads",
        qkv_layout="interleaved",
    )
    raw = torch.arange(64).reshape(1, 2, 32)

    activation = extract_component_activation(raw, spec, _FakeGroupedHeadModel())

    assert activation.shape == (1, 2, 2, 4)
    grouped = raw.reshape(1, 2, 2, 4, 4)
    assert torch.equal(activation, grouped[..., -2, :])
    patched = torch.full_like(activation, -5)
    merged = merge_component_activation(patched, raw, spec, _FakeGroupedHeadModel())
    expected = grouped.clone()
    expected[..., -2, :] = -5
    assert torch.equal(merged, expected.reshape_as(raw))
