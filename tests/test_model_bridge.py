from __future__ import annotations

from typing import Any

import pytest

from SafeLens.core.factored_matrix import FactoredMatrix, matmul, transpose
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
    reshape_attention_weight,
    reshape_joint_qkv_attention_weight,
)


class _Handle:
    def __init__(self, remove_fn: Any) -> None:
        self._remove_fn = remove_fn

    def remove(self) -> None:
        self._remove_fn()


class _FakeModule:
    def __init__(self, weight: Any | None = None, bias: Any | None = None) -> None:
        self.forward_hooks: list[Any] = []
        self.pre_hooks: list[Any] = []
        self.weight = weight
        self.bias = bias

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
        self.q_proj = _FakeModule(
            torch.arange(16, dtype=torch.float32).reshape(4, 4),
            torch.arange(4, dtype=torch.float32),
        )
        self.k_proj = _FakeModule(
            torch.arange(16, 32, dtype=torch.float32).reshape(4, 4),
            torch.arange(4, 8, dtype=torch.float32),
        )
        self.v_proj = _FakeModule(
            torch.arange(32, 48, dtype=torch.float32).reshape(4, 4),
            torch.arange(8, 12, dtype=torch.float32),
        )
        self.o_proj = _FakeModule(
            torch.arange(48, 64, dtype=torch.float32).reshape(4, 4),
            torch.arange(12, 16, dtype=torch.float32),
        )


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
                "up_proj": _FakeModule(
                    torch.arange(24, 36, dtype=torch.float32).reshape(3, 4),
                    torch.arange(3, dtype=torch.float32),
                ),
                "down_proj": _FakeModule(
                    torch.arange(12, 24, dtype=torch.float32).reshape(4, 3),
                    torch.arange(4, dtype=torch.float32),
                ),
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


class _FakeWeightedNeuronQwenModel(_FakeWeightedQwenModel):
    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        layer = self.model.layers[0]
        post = layer.mlp.down_proj.run_pre([[[3.0, 4.0, 5.0]]])
        return {"post": post}


class _FakeWeightedGatedNeuronQwenModel(_FakeWeightedQwenModel):
    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        layer = self.model.layers[0]
        gate = layer.mlp.gate_proj.run_forward([[[1.0, 2.0, 3.0]]])
        linear = layer.mlp.up_proj.run_forward([[[4.0, 5.0, 6.0]]])
        post = layer.mlp.down_proj.run_pre([[[7.0, 8.0, 9.0]]])
        return {"gate": gate, "linear": linear, "post": post}


class _FakeWeightedGatedPreLinearOnlyQwenModel(_FakeWeightedQwenModel):
    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        layer = self.model.layers[0]
        linear = layer.mlp.up_proj.run_forward([[[4.0, 5.0, 6.0]]])
        return {"linear": linear}


class _FakeListWeightedLayer(_FakeLayer):
    def __init__(self) -> None:
        super().__init__()
        self.self_attn.q_proj = _FakeModule(
            [[0, 1, 2, 3], [10, 11, 12, 13], [20, 21, 22, 23], [30, 31, 32, 33]],
            [0, 1, 2, 3],
        )
        self.self_attn.k_proj = _FakeModule(
            [[40, 41, 42, 43], [50, 51, 52, 53], [60, 61, 62, 63], [70, 71, 72, 73]],
            [4, 5, 6, 7],
        )
        self.self_attn.v_proj = _FakeModule(
            [[80, 81, 82, 83], [90, 91, 92, 93], [100, 101, 102, 103], [110, 111, 112, 113]],
            [8, 9, 10, 11],
        )
        self.self_attn.o_proj = _FakeModule(
            [[120, 121, 122, 123], [130, 131, 132, 133], [140, 141, 142, 143], [150, 151, 152, 153]],
            [12, 13, 14, 15],
        )
        self.mlp = type(
            "_ListWeightedMlp",
            (),
            {
                "gate_proj": _FakeModule([[0, 1, 2, 3], [10, 11, 12, 13], [20, 21, 22, 23]]),
                "up_proj": _FakeModule(
                    [[100, 101, 102, 103], [110, 111, 112, 113], [120, 121, 122, 123]],
                    [1, 2, 3],
                ),
                "down_proj": _FakeModule(
                    [[30, 31, 32], [40, 41, 42], [50, 51, 52], [60, 61, 62]],
                    [4, 5, 6, 7],
                ),
            },
        )()


class _FakeListWeightedBackbone:
    def __init__(self) -> None:
        self.embed_tokens = _FakeModule(
            [[0, 1, 2, 3], [10, 11, 12, 13], [20, 21, 22, 23]]
        )
        self.wte = self.embed_tokens
        self.wpe = _FakeModule([[30, 31, 32, 33], [40, 41, 42, 43]])
        self.layers = [_FakeListWeightedLayer()]


class _FakeListWeightedQwenModel(_FakeQwenModel):
    def __init__(self) -> None:
        self.config = _FakeConfig()
        self.model = _FakeListWeightedBackbone()


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
        self.c_attn = _FakeModule(
            torch.arange(90, dtype=torch.float32).reshape(5, 18),
            torch.arange(18, dtype=torch.float32),
        )
        self.c_proj = _FakeModule(
            torch.arange(30, dtype=torch.float32).reshape(6, 5),
            torch.arange(6, dtype=torch.float32),
        )


class _FakeGpt2Mlp:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.c_fc = _FakeModule(
            torch.arange(12, dtype=torch.float32).reshape(4, 3),
            torch.arange(3, dtype=torch.float32),
        )
        self.c_proj = _FakeModule(
            torch.arange(12, 24, dtype=torch.float32).reshape(3, 4),
            torch.arange(4, dtype=torch.float32),
        )


class _FakeGpt2Block(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.attn = _FakeGpt2Attention()
        self.mlp = _FakeGpt2Mlp()


class _FakeGpt2Transformer:
    def __init__(self) -> None:
        self.h = [_FakeGpt2Block()]


class _FakeGpt2Model:
    def __init__(self) -> None:
        self.config = _FakeGpt2Config()
        self.transformer = _FakeGpt2Transformer()


class _FakeHookableEmbedding(_FakeModule):
    def __init__(self, weight: Any) -> None:
        super().__init__(weight)

    def __call__(self, input_ids: Any) -> Any:
        torch = pytest.importorskip("torch")
        ids = input_ids if hasattr(input_ids, "shape") else torch.tensor(input_ids)
        embedded = self.weight[ids]
        return self.run_forward(embedded, inputs=(input_ids,))


class _FakeGpt2EmbeddingTransformer(_FakeGpt2Transformer):
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        super().__init__()
        self.wte = _FakeHookableEmbedding(torch.arange(60, dtype=torch.float32).reshape(10, 6))
        self.wpe = _FakeHookableEmbedding(torch.arange(600, 660, dtype=torch.float32).reshape(10, 6))


class _FakeGpt2EmbeddingModel:
    def __init__(self) -> None:
        self.config = _FakeGpt2Config()
        self.transformer = _FakeGpt2EmbeddingTransformer()

    def get_input_embeddings(self) -> _FakeHookableEmbedding:
        return self.transformer.wte

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        torch = pytest.importorskip("torch")
        input_ids = kwargs["input_ids"]
        if not hasattr(input_ids, "shape"):
            input_ids = torch.tensor(input_ids)
        position_ids = torch.arange(input_ids.shape[-1]).unsqueeze(0).expand_as(input_ids)
        embed = self.transformer.wte(input_ids)
        pos_embed = self.transformer.wpe(position_ids)
        resid_pre = self.transformer.h[0].run_pre(embed + pos_embed)
        return {"logits": resid_pre, "resid_pre": resid_pre}


class _FakeGptNeoxConfig:
    model_type = "gpt_neox"
    num_attention_heads = 2


class _FakeGptNeoxAttention:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.query_key_value = _FakeModule(
            torch.arange(48, dtype=torch.float32).reshape(12, 4),
            torch.arange(12, dtype=torch.float32),
        )


class _FakeGptNeoxMlp:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.dense_h_to_4h = _FakeModule(
            torch.arange(12, dtype=torch.float32).reshape(3, 4),
            torch.arange(3, dtype=torch.float32),
        )
        self.dense_4h_to_h = _FakeModule(
            torch.arange(12, 24, dtype=torch.float32).reshape(4, 3),
            torch.arange(4, dtype=torch.float32),
        )


class _FakeGptNeoxLayer:
    def __init__(self) -> None:
        self.attention = _FakeGptNeoxAttention()
        self.mlp = _FakeGptNeoxMlp()


class _FakeGptNeoxBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeGptNeoxLayer()]


class _FakeGptNeoxModel:
    def __init__(self) -> None:
        self.config = _FakeGptNeoxConfig()
        self.gpt_neox = _FakeGptNeoxBackbone()


class _FakeFalconMQAConfig:
    model_type = "falcon"
    num_attention_heads = 4
    num_kv_heads = 4
    hidden_size = 8
    num_hidden_layers = 1
    vocab_size = 65024
    max_position_embeddings = 2048
    multi_query = True
    new_decoder_architecture = False


class _FakeFalconMQAAttention:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.query_key_value = _FakeModule(
            torch.arange(96, dtype=torch.float32).reshape(12, 8),
            torch.arange(12, dtype=torch.float32),
        )
        self.dense = _FakeModule(
            torch.arange(64, dtype=torch.float32).reshape(8, 8),
            torch.arange(8, dtype=torch.float32),
        )


class _FakeFalconMlp:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.dense_h_to_4h = _FakeModule(
            torch.arange(16, dtype=torch.float32).reshape(4, 4),
            torch.arange(4, dtype=torch.float32),
        )
        self.dense_4h_to_h = _FakeModule(
            torch.arange(16, 32, dtype=torch.float32).reshape(4, 4),
            torch.arange(4, 8, dtype=torch.float32),
        )


class _FakeFalconMQABlock:
    def __init__(self) -> None:
        self.self_attention = _FakeFalconMQAAttention()
        self.mlp = _FakeFalconMlp()


class _FakeFalconMQATransformer:
    def __init__(self) -> None:
        self.h = [_FakeFalconMQABlock()]


class _FakeFalconMQAModel:
    def __init__(self) -> None:
        self.config = _FakeFalconMQAConfig()
        self.transformer = _FakeFalconMQATransformer()


class _FakeHeadConfig:
    num_attention_heads = 2


class _FakeHeadModel:
    config = _FakeHeadConfig()


class _FakeGroupedHeadConfig:
    num_attention_heads = 4
    num_key_value_heads = 2


class _FakeGroupedHeadModel:
    config = _FakeGroupedHeadConfig()


class _TinyContextConfig:
    n_ctx = 4


class _TinyContextModel:
    config = _TinyContextConfig()


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
    def __init__(self, weight: Any, bias: Any | None = None) -> None:
        self.weight = weight
        self.bias = bias


class _FakeUnembeddingModel:
    def __init__(self, weight: Any, bias: Any | None = None) -> None:
        self._weight = weight
        self._bias = bias

    def get_output_embeddings(self) -> _FakeEmbedding:
        return _FakeEmbedding(self._weight, self._bias)


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
    padding_side = "right"

    def __call__(
        self,
        text: str,
        return_tensors: str,
        add_special_tokens: bool = True,
        padding: bool = False,
        truncation: bool = False,
        max_length: int | None = None,
    ) -> Any:
        _ = return_tensors
        torch = pytest.importorskip("torch")
        texts = [text] if isinstance(text, str) else list(text)
        rows = []
        for item in texts:
            token_ids = [ord(char) for char in item]
            if add_special_tokens:
                token_ids = [self.bos_token_id, *token_ids]
            if truncation and max_length is not None:
                token_ids = token_ids[:max_length]
            rows.append(token_ids)
        if padding:
            max_length = max((len(row) for row in rows), default=0)
            if self.padding_side == "left":
                rows = [
                    [self.eos_token_id] * (max_length - len(row)) + row
                    for row in rows
                ]
            else:
                rows = [row + [self.eos_token_id] * (max_length - len(row)) for row in rows]
        return _FakeTokenizerOutput({"input_ids": torch.tensor(rows)})

    def decode(
        self,
        tokens: Any,
        skip_special_tokens: bool = False,
        clean_up_tokenization_spaces: bool = False,
    ) -> str:
        _ = clean_up_tokenization_spaces
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

    def batch_decode(
        self,
        tokens: Any,
        skip_special_tokens: bool = False,
        clean_up_tokenization_spaces: bool = False,
    ) -> list[str]:
        _ = clean_up_tokenization_spaces
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


class _FakeTokenizerWithoutPadToken(_FakeTextTokenizer):
    pad_token = None
    pad_token_id = None
    eos_token = "<eos>"

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("padding") and self.pad_token is None and self.pad_token_id is None:
            raise ValueError("Asking to pad but the tokenizer does not have a padding token.")
        return super().__call__(*args, **kwargs)


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


def test_transformer_lens_compatible_wrapper_caches_top_level_embedding_hooks() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["hook_embed", "hook_pos_embed", "blocks.0.hook_resid_pre"],
        return_cache_object=True,
    )

    assert isinstance(cache, ActivationCache)
    assert cache.has_embed
    assert cache.has_pos_embed
    expected_embed = wrapper.model.transformer.wte.weight[torch.tensor([[1, 2]])]
    expected_pos = wrapper.model.transformer.wpe.weight[torch.tensor([[0, 1]])]
    assert torch.equal(cache["hook_embed"], expected_embed)
    assert torch.equal(cache["embed"], expected_embed)
    assert torch.equal(cache["hook_pos_embed"], expected_pos)
    assert torch.equal(cache["pos_embed"], expected_pos)
    assert torch.equal(cache[("resid_pre", 0)], expected_embed + expected_pos)
    assert torch.equal(output["logits"], expected_embed + expected_pos)


def test_transformer_lens_compatible_wrapper_patches_top_level_embedding_hook() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    seen: list[tuple[str, int | str]] = []

    def patch_embed(activation: Any, hook: Any) -> Any:
        seen.append((hook.name, hook.ctx.get("count", 0)))
        hook.ctx["count"] = hook.ctx.get("count", 0) + 1
        return activation + 10

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("embed", patch_embed)],
        return_type="model_output",
    )

    expected_embed = wrapper.model.transformer.wte.weight[torch.tensor([[1, 2]])] + 10
    expected_pos = wrapper.model.transformer.wpe.weight[torch.tensor([[0, 1]])]
    assert torch.equal(output["logits"], expected_embed + expected_pos)
    assert seen == [("hook_embed", 0)]
    assert wrapper.model.transformer.wte.forward_hooks == []
    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_filters_top_level_embedding_aliases() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()

    _output, cache = wrapper.run_with_cache(
        torch.tensor([1, 2]),
        names_filter=["embed", "hook_embed"],
        return_cache_object=True,
    )

    assert isinstance(cache, ActivationCache)
    assert set(cache.to_dict()) == {"hook_embed"}
    assert torch.equal(cache["embed"], wrapper.model.transformer.wte.weight[torch.tensor([[1, 2]])])


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


def test_transformer_lens_compatible_wrapper_add_caching_hooks_rolls_back_on_invalid_layer() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    q_proj = wrapper.model.model.layers[0].self_attn.q_proj
    original_model = object()
    external_cache = ActivationCache({"existing": ["value"]}, model=original_model)

    with pytest.raises(KeyError):
        wrapper.add_caching_hooks(
            layers=["blocks.0.attn.hook_q", "blocks.99.attn.hook_q"],
            remove_batch_dim=True,
            cache=external_cache,
        )

    assert wrapper._hooks == []
    assert q_proj.forward_hooks == []
    assert q_proj.run_forward(["q"]) == ["q"]
    assert external_cache.model is original_model
    assert external_cache.has_batch_dim is True
    assert external_cache.to_dict() == {"existing": ["value"]}


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


def test_transformer_lens_compatible_wrapper_string_names_filter_matches_shorthands() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter="q0",
    )

    assert output == {"q": ["q"]}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}


def test_transformer_lens_compatible_wrapper_cache_layers_accept_shorthand_name() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["q0"],
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


def test_transformer_lens_compatible_wrapper_run_with_hooks_accepts_shorthand_name() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("q0", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert output == {"q": ["q", "patched"]}


def test_transformer_lens_compatible_wrapper_add_hook_accepts_shorthand_name() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook("q0", lambda **kwargs: kwargs["activation"] + ["patched"])

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "patched"]}


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
    assert wrapper.to_str_tokens(torch.tensor(ord("a"))) == ["a"]
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
    assert wrapper.get_token_position("a", "abca", padding_side="left") == 1
    assert wrapper.tokenizer.padding_side == "right"
    assert wrapper.get_token_position(ord("b"), torch.tensor([[0, 97, 98]])) == 2
    assert wrapper.get_token_position(ord("b"), [0, 97, 98]) == 2
    with pytest.raises(ValueError, match="does not occur"):
        wrapper.get_token_position("z", "abc")
    with pytest.raises(ValueError, match="mode"):
        wrapper.get_token_position("a", "abc", mode="middle")


def test_transformer_lens_compatible_wrapper_to_tokens_accepts_transformerlens_kwargs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()
    wrapper.model = _TinyContextModel()
    wrapper.device = "cpu"

    tokens = wrapper.to_tokens(
        "abcd",
        prepend_bos=True,
        truncate=True,
        move_to_device=False,
    )

    assert torch.equal(tokens, torch.tensor([[0, 97, 98, 99]]))

    batch = wrapper.to_tokens(
        ["a", "bc"],
        padding_side="left",
        prepend_bos=False,
    )

    assert torch.equal(batch, torch.tensor([[999, 97], [98, 99]]))
    assert wrapper.tokenizer.padding_side == "right"
    assert wrapper.to_str_tokens("ab", padding_side="left") == ["<bos>", "a", "b"]


def test_transformer_lens_compatible_wrapper_to_str_tokens_accepts_numpy_scalar() -> None:
    np = pytest.importorskip("numpy")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()

    assert wrapper.to_str_tokens(np.array(ord("a"))) == ["a"]


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


def test_transformer_lens_compatible_wrapper_temporarily_uses_eos_as_pad_token() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTokenizerWithoutPadToken()

    tokens = wrapper.to_tokens(["a", "bc"], prepend_bos=False)

    assert torch.equal(tokens, torch.tensor([[97, 999], [98, 99]]))
    assert wrapper.tokenizer.pad_token is None
    assert wrapper.tokenizer.pad_token_id is None


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


def test_transformer_lens_compatible_wrapper_residual_directions_for_list_tokens() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel([[1, 10], [2, 20], [3, 30]])

    directions = wrapper.tokens_to_residual_directions([[0, 2], [1, 0]])

    assert directions == [
        [[1, 10], [3, 30]],
        [[2, 20], [1, 10]],
    ]


def test_transformer_lens_compatible_wrapper_logit_attrs_uses_list_token_directions() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel([[1, 10], [2, 20], [3, 30]])
    cache = ActivationCache({}, model=wrapper)

    attrs = cache.logit_attrs(
        [[[[1, 1], [10, 1]], [[2, 2], [3, 1]]]],
        [[0, 2]],
        apply_ln=False,
    )

    assert attrs == [[[11.0, 60.0], [22.0, 39.0]]]


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
    bias = torch.tensor([0.1, 0.2, 0.3])
    wrapper.model = _FakeUnembeddingModel(weight, bias)

    assert torch.equal(wrapper.W_U, weight.T)
    assert torch.equal(wrapper.b_U, bias)


def test_transformer_lens_compatible_wrapper_exposes_list_unembed_matrix() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel([[1, 10], [2, 20], [3, 30]])

    assert wrapper.W_U == [[1, 2, 3], [10, 20, 30]]
    assert wrapper.b_U == [0, 0, 0]


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
    assert torch.equal(wrapper.b_Q, attention.q_proj.bias.reshape(2, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_K, attention.k_proj.bias.reshape(2, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_V, attention.v_proj.bias.reshape(2, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_O, attention.o_proj.bias.unsqueeze(0))

    qk = wrapper.QK
    assert isinstance(qk, FactoredMatrix)
    assert torch.equal(qk.A, expected_q)
    assert torch.equal(qk.B, expected_k.transpose(-2, -1))
    assert torch.equal(qk.AB, torch.matmul(expected_q, expected_k.transpose(-2, -1)))

    ov = wrapper.OV
    assert isinstance(ov, FactoredMatrix)
    assert torch.equal(ov.A, expected_v)
    assert torch.equal(ov.B, expected_o)
    assert torch.equal(ov.AB, torch.matmul(expected_v, expected_o))


def test_transformer_lens_compatible_wrapper_accumulated_bias_matches_transformerlens_semantics() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()

    assert torch.equal(wrapper.accumulated_bias(0), torch.zeros(4))
    assert torch.equal(wrapper.accumulated_bias(0, mlp_input=True), wrapper.b_O[0])
    assert torch.equal(wrapper.accumulated_bias(1), wrapper.b_O[0] + wrapper.b_out[0])
    assert torch.equal(
        wrapper.accumulated_bias(1, include_mlp_biases=False),
        wrapper.b_O[0],
    )
    with pytest.raises(AssertionError, match="beyond the final layer"):
        wrapper.accumulated_bias(1, mlp_input=True)
    with pytest.raises(ValueError, match="between 0 and 1"):
        wrapper.accumulated_bias(2)


def test_transformer_lens_compatible_wrapper_all_composition_scores_match_transformerlens_mask() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    wrapper.model.model.layers.append(_FakeWeightedLayer())

    assert wrapper.all_head_labels() == ["L0H0", "L0H1", "L1H0", "L1H1"]

    for mode in ("Q", "K", "V"):
        scores = wrapper.all_composition_scores(mode)

        assert tuple(scores.shape) == (2, 2, 2, 2)
        assert torch.all(scores[0, :, 0, :] == 0)
        assert torch.all(scores[1, :, 0, :] == 0)
        assert torch.all(scores[1, :, 1, :] == 0)
        assert torch.any(scores[0, :, 1, :] > 0)

    with pytest.raises(ValueError, match=r"Q.*K.*V"):
        wrapper.all_composition_scores("Z")


def test_component_bridge_reshapes_attention_weights_for_list_backend() -> None:
    weight = [[row * 10 + col for col in range(4)] for row in range(4)]

    assert reshape_attention_weight(weight, component="q", n_heads=2, packed_axis=0) == [
        [[0, 10], [1, 11], [2, 12], [3, 13]],
        [[20, 30], [21, 31], [22, 32], [23, 33]],
    ]
    assert reshape_attention_weight(weight, component="z", n_heads=2, packed_axis=1) == [
        [[0, 10, 20, 30], [1, 11, 21, 31]],
        [[2, 12, 22, 32], [3, 13, 23, 33]],
    ]


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


def test_component_bridge_reshapes_joint_qkv_weights_for_list_backend() -> None:
    rows_weight = [[row * 10 + col for col in range(4)] for row in range(12)]
    cols_weight = [[row * 100 + col for col in range(12)] for row in range(4)]

    assert reshape_joint_qkv_attention_weight(
        rows_weight,
        component="q",
        q_heads=2,
        kv_heads=2,
        qkv_layout="interleaved",
        packed_axis=0,
    ) == [
        [[0, 10], [1, 11], [2, 12], [3, 13]],
        [[60, 70], [61, 71], [62, 72], [63, 73]],
    ]
    assert reshape_joint_qkv_attention_weight(
        rows_weight,
        component="v",
        q_heads=2,
        kv_heads=2,
        qkv_layout="interleaved",
        packed_axis=0,
    ) == [
        [[40, 50], [41, 51], [42, 52], [43, 53]],
        [[100, 110], [101, 111], [102, 112], [103, 113]],
    ]
    assert reshape_joint_qkv_attention_weight(
        cols_weight,
        component="k",
        q_heads=2,
        kv_heads=2,
        qkv_layout="split",
        packed_axis=1,
    ) == [
        [[4, 5], [104, 105], [204, 205], [304, 305]],
        [[6, 7], [106, 107], [206, 207], [306, 307]],
    ]


def test_transformer_lens_compatible_wrapper_exposes_neox_joint_qkv_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="EleutherAI/pythia-70m")
    wrapper.model = _FakeGptNeoxModel()
    weight = wrapper.model.gpt_neox.layers[0].attention.query_key_value.weight
    interleaved = weight.reshape(2, 3, 2, 4)

    expected_q = interleaved[:, 0].reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_k = interleaved[:, 1].reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_v = interleaved[:, 2].reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    bias = wrapper.model.gpt_neox.layers[0].attention.query_key_value.bias.reshape(2, 3, 2)

    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)
    assert torch.equal(wrapper.b_Q, bias[:, 0].unsqueeze(0))
    assert torch.equal(wrapper.b_K, bias[:, 1].unsqueeze(0))
    assert torch.equal(wrapper.b_V, bias[:, 2].unsqueeze(0))


def test_transformer_lens_compatible_wrapper_exposes_mlp_weights_from_adapter_specs() -> None:
    torch = pytest.importorskip("torch")

    gpt2_wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    gpt2_wrapper.model = _FakeGpt2Model()
    gpt2_mlp = gpt2_wrapper.model.transformer.h[0].mlp
    assert torch.equal(gpt2_wrapper.W_in, gpt2_mlp.c_fc.weight.T.unsqueeze(0))
    assert torch.equal(gpt2_wrapper.W_out, gpt2_mlp.c_proj.weight.T.unsqueeze(0))
    assert torch.equal(gpt2_wrapper.b_in, gpt2_mlp.c_fc.bias.unsqueeze(0))
    assert torch.equal(gpt2_wrapper.b_out, gpt2_mlp.c_proj.bias.unsqueeze(0))

    neox_wrapper = TransformerLensCompatibleModelWrapper(name="EleutherAI/pythia-70m")
    neox_wrapper.model = _FakeGptNeoxModel()
    neox_mlp = neox_wrapper.model.gpt_neox.layers[0].mlp
    assert torch.equal(neox_wrapper.W_in, neox_mlp.dense_h_to_4h.weight.T.unsqueeze(0))
    assert torch.equal(neox_wrapper.W_out, neox_mlp.dense_4h_to_h.weight.T.unsqueeze(0))
    assert torch.equal(neox_wrapper.b_in, neox_mlp.dense_h_to_4h.bias.unsqueeze(0))
    assert torch.equal(neox_wrapper.b_out, neox_mlp.dense_4h_to_h.bias.unsqueeze(0))

    falcon_wrapper = TransformerLensCompatibleModelWrapper(name="tiiuae/falcon-7b")
    falcon_wrapper.model = _FakeFalconMQAModel()
    falcon_mlp = falcon_wrapper.model.transformer.h[0].mlp
    assert torch.equal(falcon_wrapper.W_in, falcon_mlp.dense_h_to_4h.weight.T.unsqueeze(0))
    assert torch.equal(falcon_wrapper.W_out, falcon_mlp.dense_4h_to_h.weight.T.unsqueeze(0))
    assert torch.equal(falcon_wrapper.b_in, falcon_mlp.dense_h_to_4h.bias.unsqueeze(0))
    assert torch.equal(falcon_wrapper.b_out, falcon_mlp.dense_4h_to_h.bias.unsqueeze(0))


def test_transformer_lens_compatible_wrapper_exposes_falcon_multi_query_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="tiiuae/falcon-7b")
    wrapper.model = _FakeFalconMQAModel()
    attention = wrapper.model.transformer.h[0].self_attention
    weight = attention.query_key_value.weight
    grouped = weight.reshape(1, 6, 2, 8)

    expected_q = grouped[:, :4].reshape(8, 8).reshape(4, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_k = grouped[:, -2].reshape(1, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_v = grouped[:, -1].reshape(1, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_o = attention.dense.weight.reshape(8, 4, 2).permute(1, 2, 0).unsqueeze(0)
    bias = attention.query_key_value.bias.reshape(1, 6, 2)

    assert wrapper.cfg.n_key_value_heads == 1
    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)
    assert torch.equal(wrapper.W_O, expected_o)
    assert torch.equal(wrapper.b_Q, bias[:, :4].reshape(1, 4, 2))
    assert torch.equal(wrapper.b_K, bias[:, -2].reshape(1, 1, 2))
    assert torch.equal(wrapper.b_V, bias[:, -1].reshape(1, 1, 2))
    assert torch.equal(wrapper.b_O, attention.dense.bias.unsqueeze(0))

    repeated_k = expected_k.repeat_interleave(4, dim=1)
    qk = wrapper.QK
    assert torch.equal(qk.A, expected_q)
    assert torch.equal(qk.B, repeated_k.transpose(-2, -1))
    assert tuple(qk.shape) == (1, 4, 8, 8)

    repeated_v = expected_v.repeat_interleave(4, dim=1)
    ov = wrapper.OV
    assert torch.equal(ov.A, repeated_v)
    assert torch.equal(ov.B, expected_o)
    assert tuple(ov.shape) == (1, 4, 8, 8)


def test_transformer_lens_compatible_wrapper_exposes_embedding_and_mlp_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    model = wrapper.model.model
    mlp = model.layers[0].mlp

    assert torch.equal(wrapper.W_E, model.embed_tokens.weight)
    assert torch.equal(wrapper.W_pos, model.wpe.weight)
    assert torch.equal(wrapper.W_E_pos, torch.cat([model.embed_tokens.weight, model.wpe.weight], dim=0))
    assert torch.equal(wrapper.W_in, mlp.up_proj.weight.T.unsqueeze(0))
    assert torch.equal(wrapper.W_gate, mlp.gate_proj.weight.T.unsqueeze(0))
    assert torch.equal(wrapper.W_out, mlp.down_proj.weight.T.unsqueeze(0))
    assert torch.equal(wrapper.b_in, mlp.up_proj.bias.unsqueeze(0))
    assert torch.equal(wrapper.b_out, mlp.down_proj.bias.unsqueeze(0))


def test_transformer_lens_compatible_wrapper_exposes_list_embedding_and_mlp_weights() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeListWeightedQwenModel()
    attention = wrapper.model.model.layers[0].self_attn

    assert wrapper.W_E == [[0, 1, 2, 3], [10, 11, 12, 13], [20, 21, 22, 23]]
    assert wrapper.W_pos == [[30, 31, 32, 33], [40, 41, 42, 43]]
    assert wrapper.W_E_pos == [
        [0, 1, 2, 3],
        [10, 11, 12, 13],
        [20, 21, 22, 23],
        [30, 31, 32, 33],
        [40, 41, 42, 43],
    ]
    assert wrapper.W_in == [
        [[100, 110, 120], [101, 111, 121], [102, 112, 122], [103, 113, 123]]
    ]
    assert wrapper.W_gate == [
        [[0, 10, 20], [1, 11, 21], [2, 12, 22], [3, 13, 23]]
    ]
    assert wrapper.W_out == [
        [[30, 40, 50, 60], [31, 41, 51, 61], [32, 42, 52, 62]]
    ]
    assert wrapper.W_Q == [
        reshape_attention_weight(attention.q_proj.weight, component="q", n_heads=2)
    ]
    assert wrapper.W_K == [
        reshape_attention_weight(attention.k_proj.weight, component="k", n_heads=2)
    ]
    assert wrapper.W_V == [
        reshape_attention_weight(attention.v_proj.weight, component="v", n_heads=2)
    ]
    assert wrapper.W_O == [
        reshape_attention_weight(attention.o_proj.weight, component="z", n_heads=2, packed_axis=1)
    ]
    assert wrapper.b_Q == [[[0, 1], [2, 3]]]
    assert wrapper.b_K == [[[4, 5], [6, 7]]]
    assert wrapper.b_V == [[[8, 9], [10, 11]]]
    assert wrapper.b_O == [[12, 13, 14, 15]]
    assert wrapper.b_in == [[1, 2, 3]]
    assert wrapper.b_out == [[4, 5, 6, 7]]
    assert wrapper.accumulated_bias(0) == [0, 0, 0, 0]
    assert wrapper.accumulated_bias(0, mlp_input=True) == [12, 13, 14, 15]
    assert wrapper.accumulated_bias(1) == [16, 18, 20, 22]

    qk = wrapper.QK
    assert isinstance(qk, FactoredMatrix)
    assert qk.A == wrapper.W_Q
    assert qk.B == transpose(wrapper.W_K)
    assert qk.AB == matmul(wrapper.W_Q, transpose(wrapper.W_K))

    ov = wrapper.OV
    assert isinstance(ov, FactoredMatrix)
    assert ov.A == wrapper.W_V
    assert ov.B == wrapper.W_O
    assert ov.AB == matmul(wrapper.W_V, wrapper.W_O)


def test_transformer_lens_compatible_wrapper_caches_attention_pattern() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_pattern"],
    )

    assert output["output_attentions"] is True
    assert getattr(cache["blocks.0.attn.hook_pattern"], "ndim", None) == 4


def test_transformer_lens_compatible_wrapper_caches_mlp_post_for_neuron_decomposition() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedNeuronQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.mlp.hook_post"],
        return_cache_object=True,
    )

    assert output == {"post": [[[3.0, 4.0, 5.0]]]}
    assert cache["layer_0.post"] == [[[3.0, 4.0, 5.0]]]
    torch = pytest.importorskip("torch")
    expected = torch.tensor(
        [[[[36.0, 45.0, 54.0, 63.0], [70.0, 85.0, 100.0, 115.0]]]]
    )
    assert torch.equal(cache.get_neuron_results(0, neuron_slice=[0, 2]), expected)


def test_transformer_lens_compatible_wrapper_cache_object_resolves_mlp_pre_linear() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedGatedPreLinearOnlyQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.mlp.hook_pre_linear"],
        return_cache_object=True,
    )

    assert output == {"linear": [[[4.0, 5.0, 6.0]]]}
    assert cache["layer_0.pre_linear"] == [[[4.0, 5.0, 6.0]]]


def test_transformer_lens_compatible_wrapper_caches_gated_mlp_pre_linear() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedGatedNeuronQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=[
            "blocks.0.mlp.hook_pre",
            "blocks.0.mlp.hook_pre_linear",
            "blocks.0.mlp.hook_post",
        ],
    )

    assert output == {
        "gate": [[[1.0, 2.0, 3.0]]],
        "linear": [[[4.0, 5.0, 6.0]]],
        "post": [[[7.0, 8.0, 9.0]]],
    }
    assert cache["blocks.0.mlp.hook_pre"] == [[[1.0, 2.0, 3.0]]]
    assert cache["blocks.0.mlp.hook_pre_linear"] == [[[4.0, 5.0, 6.0]]]
    assert cache["blocks.0.mlp.hook_post"] == [[[7.0, 8.0, 9.0]]]


def test_transformer_lens_compatible_wrapper_patches_gated_mlp_pre_linear() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedGatedNeuronQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[
            ("blocks.0.mlp.hook_pre_linear", lambda **_kwargs: [[[40.0, 50.0, 60.0]]])
        ],
    )

    assert output["gate"] == [[[1.0, 2.0, 3.0]]]
    assert output["linear"] == [[[40.0, 50.0, 60.0]]]
    assert output["post"] == [[[7.0, 8.0, 9.0]]]


def test_transformer_lens_compatible_wrapper_attention_cache_failure_does_not_set_flag() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    with pytest.raises(KeyError):
        wrapper.add_caching_hooks(
            layers=["blocks.99.attn.hook_pattern"],
        )

    assert wrapper._attention_hook_count == 0
    assert wrapper._hooks == []
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


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


def test_component_bridge_splits_and_merges_head_projections_for_list_backend() -> None:
    spec = ComponentHookSpec(
        component="q",
        mode="forward_output",
        module_paths=("unused",),
        activation="split_heads",
    )
    raw = [[[0, 1, 2, 3, 4, 5, 6, 7]]]

    activation = extract_component_activation(raw, spec, _FakeHeadModel())

    assert activation == [[[[0, 1, 2, 3], [4, 5, 6, 7]]]]
    patched = [[[[0, 1, 2, 3], [-1, -1, -1, -1]]]]
    merged = merge_component_activation(patched, raw, spec, _FakeHeadModel())

    assert merged == [[[0, 1, 2, 3, -1, -1, -1, -1]]]


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


def test_component_bridge_splits_and_merges_split_qkv_projection_for_list_backend() -> None:
    spec = ComponentHookSpec(
        component="k",
        mode="forward_output",
        module_paths=("unused",),
        activation="split_qkv_heads",
    )
    raw = [[[index for index in range(24)]]]

    activation = extract_component_activation(raw, spec, _FakeHeadModel())

    assert activation == [[[[8, 9, 10, 11], [12, 13, 14, 15]]]]
    patched = [[[[-7, -7, -7, -7], [-8, -8, -8, -8]]]]
    merged = merge_component_activation(patched, raw, spec, _FakeHeadModel())

    assert merged == [[[0, 1, 2, 3, 4, 5, 6, 7, -7, -7, -7, -7, -8, -8, -8, -8, 16, 17, 18, 19, 20, 21, 22, 23]]]


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


def test_component_bridge_splits_and_merges_interleaved_qkv_projection_for_list_backend() -> None:
    spec = ComponentHookSpec(
        component="v",
        mode="forward_output",
        module_paths=("unused",),
        activation="split_qkv_heads",
        qkv_layout="interleaved",
    )
    raw = [[[index for index in range(24)]]]

    activation = extract_component_activation(raw, spec, _FakeHeadModel())

    assert activation == [[[[8, 9, 10, 11], [20, 21, 22, 23]]]]
    patched = [[[[-3, -3, -3, -3], [-4, -4, -4, -4]]]]
    merged = merge_component_activation(patched, raw, spec, _FakeHeadModel())

    assert merged == [[[0, 1, 2, 3, 4, 5, 6, 7, -3, -3, -3, -3, 12, 13, 14, 15, 16, 17, 18, 19, -4, -4, -4, -4]]]


@pytest.mark.parametrize(
    ("component", "selector", "patch_value"),
    (
        ("q", (slice(None), slice(None), slice(None), slice(0, 2), slice(None)), -4),
        ("k", (slice(None), slice(None), slice(None), -2, slice(None)), -5),
        ("v", (slice(None), slice(None), slice(None), -1, slice(None)), -6),
    ),
)
def test_component_bridge_splits_and_merges_grouped_interleaved_qkv_projection(
    component: str,
    selector: tuple[Any, ...],
    patch_value: int,
) -> None:
    torch = pytest.importorskip("torch")
    spec = ComponentHookSpec(
        component=component,
        mode="forward_output",
        module_paths=("unused",),
        activation="split_qkv_heads",
        qkv_layout="interleaved",
    )
    raw = torch.arange(64).reshape(1, 2, 32)

    activation = extract_component_activation(raw, spec, _FakeGroupedHeadModel())

    grouped = raw.reshape(1, 2, 2, 4, 4)
    expected_activation = grouped[selector]
    if component == "q":
        expected_activation = expected_activation.reshape(1, 2, 4, 4)
    assert activation.shape == expected_activation.shape
    assert torch.equal(activation, expected_activation)
    patched = torch.full_like(activation, patch_value)
    merged = merge_component_activation(patched, raw, spec, _FakeGroupedHeadModel())
    expected = grouped.clone()
    expected[selector] = patch_value
    assert torch.equal(merged, expected.reshape_as(raw))


@pytest.mark.parametrize(
    ("component", "expected_activation", "patched", "expected_merged"),
    (
        (
            "q",
            [[[[0, 1, 2, 3], [4, 5, 6, 7], [16, 17, 18, 19], [20, 21, 22, 23]]]],
            [[[[-4, -4, -4, -4], [-5, -5, -5, -5], [-6, -6, -6, -6], [-7, -7, -7, -7]]]],
            [[[-4, -4, -4, -4, -5, -5, -5, -5, 8, 9, 10, 11, 12, 13, 14, 15, -6, -6, -6, -6, -7, -7, -7, -7, 24, 25, 26, 27, 28, 29, 30, 31]]],
        ),
        (
            "k",
            [[[[8, 9, 10, 11], [24, 25, 26, 27]]]],
            [[[[-8, -8, -8, -8], [-9, -9, -9, -9]]]],
            [[[0, 1, 2, 3, 4, 5, 6, 7, -8, -8, -8, -8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, -9, -9, -9, -9, 28, 29, 30, 31]]],
        ),
        (
            "v",
            [[[[12, 13, 14, 15], [28, 29, 30, 31]]]],
            [[[[-10, -10, -10, -10], [-11, -11, -11, -11]]]],
            [[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, -10, -10, -10, -10, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, -11, -11, -11, -11]]],
        ),
    ),
)
def test_component_bridge_splits_and_merges_grouped_interleaved_qkv_projection_for_list_backend(
    component: str,
    expected_activation: list[Any],
    patched: list[Any],
    expected_merged: list[Any],
) -> None:
    spec = ComponentHookSpec(
        component=component,
        mode="forward_output",
        module_paths=("unused",),
        activation="split_qkv_heads",
        qkv_layout="interleaved",
    )
    raw = [[[index for index in range(32)]]]

    activation = extract_component_activation(raw, spec, _FakeGroupedHeadModel())
    merged = merge_component_activation(patched, raw, spec, _FakeGroupedHeadModel())

    assert activation == expected_activation
    assert merged == expected_merged
