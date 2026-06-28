from __future__ import annotations

import builtins
from collections.abc import Mapping
from typing import Any, Literal

import pytest

from SafeLens.core.analysis import (
    detect_head,
    get_previous_token_head_detection_pattern,
    lm_cross_entropy_loss,
)
from SafeLens.core.factored_matrix import FactoredMatrix, matmul, transpose
from SafeLens.core.hooks import ActivationCache
from SafeLens.core.kv_cache import KeyValueCache
from SafeLens.core.patching import PatchSpec, run_activation_patch
from SafeLens.core.svd_interpreter import SVDInterpreter
from SafeLens.utils import (
    HuggingFaceModelWrapper,
    TransformerLensCompatibleModelWrapper,
    architecture_adapter_for_model,
    architecture_adapter_for_name,
    list_architecture_adapters,
    supported_transformer_component_names,
)
from SafeLens.utils.model_bridge import (
    ComponentHookContext,
    ComponentHookSpec,
    ComponentRef,
    apply_attention_result_patch,
    attention_head_count,
    attention_head_dim,
    call_component_hook,
    compute_attention_result_activation,
    extract_component_activation,
    key_value_head_count,
    merge_component_activation,
    replace_component_activation,
    reshape_attention_weight,
    reshape_joint_qkv_attention_weight,
    transformer_lens_component_name,
)
from SafeLens.utils.model_wrapper import (
    _append_sequence_values,
    _attention_mask_from_tokens,
    _candidate_hook_names,
    _concat_token_chunks,
    _default_cache_hook_names,
    _past_kv_cache_to_transformers_cache,
    _prepend_bos_token,
    _single_token_list,
    _slice_generated_suffix,
    _wrapper_looks_like_local_path,
)
from SafeLens.utils.transformer_lens_support import (
    is_transformer_lens_native_checkpoint,
    transformer_lens_official_model_names,
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
        self.weight: Any = weight
        self.bias: Any = bias

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)

    def register_forward_hook(self, hook_fn: Any, *, prepend: bool = False) -> _Handle:
        if prepend:
            self.forward_hooks.insert(0, hook_fn)
        else:
            self.forward_hooks.append(hook_fn)
        return _Handle(lambda: self.forward_hooks.remove(hook_fn))

    def register_forward_pre_hook(self, hook_fn: Any, *, prepend: bool = False) -> _Handle:
        if prepend:
            self.pre_hooks.insert(0, hook_fn)
        else:
            self.pre_hooks.append(hook_fn)
        return _Handle(lambda: self.pre_hooks.remove(hook_fn))

    def run_forward(self, output: Any, inputs: tuple[Any, ...] = ()) -> Any:
        current = output
        for hook_fn in list(self.forward_hooks):
            patched = hook_fn(self, inputs, current)
            if patched is not None:
                current = patched
        return current

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        _ = kwargs
        output = value
        weight = getattr(self, "weight", None)
        if weight is not None and hasattr(value, "matmul"):
            output = value.matmul(weight.T)
            bias = getattr(self, "bias", None)
            if bias is not None:
                output = output + bias
        return self.run_forward(output, inputs=(value,))

    def run_pre(self, value: Any) -> Any:
        inputs = (value,)
        for hook_fn in list(self.pre_hooks):
            patched = hook_fn(self, inputs)
            if patched is not None:
                inputs = patched
        return inputs[0]


class _FakeConv1DModule(_FakeModule):
    def __init__(self, weight: Any, bias: Any | None = None) -> None:
        super().__init__(weight, bias)
        shape = getattr(weight, "shape", None)
        if shape is not None and len(shape) == 2:
            self.nx = int(shape[0])
            self.nf = int(shape[1])


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
        self.mlp: Any = _FakeModule()


class _FakeConfig:
    model_type = "qwen3"
    num_attention_heads = 2
    num_key_value_heads = 2
    hidden_size = 4
    vocab_size = 151936
    max_position_embeddings = 32768
    intermediate_size = 16
    hidden_act = "silu"


class _FakeOffsetRmsConfig(_FakeConfig):
    rmsnorm_uses_offset = True


class _FakeBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeLayer()]


class _FakeQwenModel:
    config: Any
    model: Any

    def __init__(self) -> None:
        self.config = _FakeConfig()
        self.model = _FakeBackbone()

    def eval(self) -> _FakeQwenModel:
        return self

    def __call__(self, **kwargs: Any) -> Any:
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


class _FakeMambaConfig:
    model_type = "mamba"
    num_hidden_layers = 1
    hidden_size = 4
    intermediate_size = 8
    state_size = 3
    conv_kernel = 4
    time_step_rank = 2
    vocab_size = 32000


class _FakeMambaMixer:
    def __init__(self) -> None:
        self.in_proj = _FakeModule()
        self.conv1d = _FakeModule()
        self.x_proj = _FakeModule()
        self.dt_proj = _FakeModule()
        self.out_proj = _FakeModule()


class _FakeMambaLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.norm = _FakeModule()
        self.mixer = _FakeMambaMixer()


class _FakeMambaBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeMambaLayer()]


class _FakeMambaModel:
    def __init__(self) -> None:
        self.config = _FakeMambaConfig()
        self.backbone = _FakeMambaBackbone()

    def __call__(self, **_kwargs: Any) -> dict[str, Any]:
        mixer = self.backbone.layers[0].mixer
        ssm_in = mixer.in_proj.run_forward(["in"])
        ssm_out = mixer.out_proj.run_pre(["out"])
        return {"ssm_in": ssm_in, "ssm_out": ssm_out}


class _FakeMamba2Config(_FakeMambaConfig):
    model_type = "mamba2"
    num_heads = 2
    head_dim = 2
    n_groups = 1


class _FakeMamba2Mixer:
    def __init__(self) -> None:
        self.in_proj = _FakeModule()
        self.conv1d = _FakeModule()
        self.norm = _FakeModule()
        self.out_proj = _FakeModule()


class _FakeMamba2Layer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.norm = _FakeModule()
        self.mixer = _FakeMamba2Mixer()


class _FakeMamba2Backbone:
    def __init__(self) -> None:
        self.layers = [_FakeMamba2Layer()]


class _FakeMamba2Model:
    def __init__(self) -> None:
        self.config = _FakeMamba2Config()
        self.backbone = _FakeMamba2Backbone()


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


class _FakeOffsetRmsWeightedQwenModel(_FakeWeightedQwenModel):
    def __init__(self) -> None:
        super().__init__()
        self.config = _FakeOffsetRmsConfig()


class _FakeGemma3ConditionalBackbone:
    def __init__(self) -> None:
        self.language_model = _FakeWeightedBackbone()


class _FakeGemma3ConditionalModel(_FakeQwenModel):
    def __init__(self) -> None:
        self.config = type(
            "_FakeGemma3ConditionalConfig",
            (_FakeConfig,),
            {"model_type": "gemma3", "num_hidden_layers": 1},
        )()
        self.model = _FakeGemma3ConditionalBackbone()


class _FakeApertusConfig:
    model_type = "apertus"
    num_attention_heads = 4
    num_key_value_heads = 2
    hidden_size = 8
    num_hidden_layers = 1
    intermediate_size = 16
    vocab_size = 131072
    max_position_embeddings = 65536
    hidden_act = "xielu"


class _FakeApertusMlp:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.up_proj = _FakeModule(
            torch.arange(128, dtype=torch.float32).reshape(16, 8),
            torch.arange(16, dtype=torch.float32),
        )
        self.down_proj = _FakeModule(
            torch.arange(128, 256, dtype=torch.float32).reshape(8, 16),
            torch.arange(8, dtype=torch.float32),
        )


class _FakeApertusLayer(_FakeLayer):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        self.self_attn = type(
            "_ApertusAttention",
            (),
            {
                "q_proj": _FakeModule(
                    torch.arange(64, dtype=torch.float32).reshape(8, 8),
                    torch.arange(8, dtype=torch.float32),
                ),
                "k_proj": _FakeModule(
                    torch.arange(64, 96, dtype=torch.float32).reshape(4, 8),
                    torch.arange(4, dtype=torch.float32),
                ),
                "v_proj": _FakeModule(
                    torch.arange(96, 128, dtype=torch.float32).reshape(4, 8),
                    torch.arange(4, dtype=torch.float32),
                ),
                "o_proj": _FakeModule(
                    torch.arange(128, 192, dtype=torch.float32).reshape(8, 8),
                    torch.arange(8, dtype=torch.float32),
                ),
            },
        )()
        self.attention_layernorm = _FakeModule()
        self.feedforward_layernorm = _FakeModule()
        self.mlp = _FakeApertusMlp()


class _FakeApertusBackbone:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.embed_tokens = _FakeModule(torch.arange(40, dtype=torch.float32).reshape(5, 8))
        self.layers = [_FakeApertusLayer()]


class _FakeApertusModel:
    def __init__(self) -> None:
        self.config = _FakeApertusConfig()
        self.model = _FakeApertusBackbone()


class _FakeGptOssConfig:
    model_type = "gpt_oss"
    num_attention_heads = 4
    num_key_value_heads = 2
    hidden_size = 8
    head_dim = 2
    num_hidden_layers = 1
    intermediate_size = 4
    num_local_experts = 2
    num_experts_per_tok = 1
    vocab_size = 201088
    max_position_embeddings = 131072
    hidden_act = "silu"


class _FakeGptOssMlp(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        self.router = _FakeModule(
            torch.arange(16, dtype=torch.float32).reshape(2, 8),
            torch.arange(2, dtype=torch.float32),
        )
        self.experts = type(
            "_GptOssExperts",
            (),
            {
                "gate_up_proj": torch.arange(128, dtype=torch.float32).reshape(2, 8, 8),
                "down_proj": torch.arange(64, dtype=torch.float32).reshape(2, 4, 8),
            },
        )()


class _FakeGptOssLayer(_FakeLayer):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        self.self_attn = type(
            "_GptOssAttention",
            (),
            {
                "q_proj": _FakeModule(
                    torch.arange(64, dtype=torch.float32).reshape(8, 8),
                    torch.arange(8, dtype=torch.float32),
                ),
                "k_proj": _FakeModule(
                    torch.arange(64, 96, dtype=torch.float32).reshape(4, 8),
                    torch.arange(4, dtype=torch.float32),
                ),
                "v_proj": _FakeModule(
                    torch.arange(96, 128, dtype=torch.float32).reshape(4, 8),
                    torch.arange(4, dtype=torch.float32),
                ),
                "o_proj": _FakeModule(
                    torch.arange(128, 192, dtype=torch.float32).reshape(8, 8),
                    torch.arange(8, dtype=torch.float32),
                ),
            },
        )()
        self.input_layernorm = _FakeModule()
        self.post_attention_layernorm = _FakeModule()
        self.mlp = _FakeGptOssMlp()


class _FakeGptOssBackbone:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.embed_tokens = _FakeModule(torch.arange(40, dtype=torch.float32).reshape(5, 8))
        self.layers = [_FakeGptOssLayer()]


class _FakeGptOssModel:
    def __init__(self) -> None:
        self.config = _FakeGptOssConfig()
        self.model = _FakeGptOssBackbone()


class _FakeRoutedMoeConfig(_FakeConfig):
    model_type = "mixtral"
    num_attention_heads = 2
    num_key_value_heads = 2
    hidden_size = 4
    intermediate_size = 8
    num_local_experts = 2
    num_experts_per_tok = 1
    vocab_size = 32000
    max_position_embeddings = 32768


class _FakeRoutedMoeMlp(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        self.gate = _FakeModule(
            torch.arange(8, dtype=torch.float32).reshape(2, 4),
            torch.arange(2, dtype=torch.float32),
        )
        self.experts = [
            type(
                "_FakeRoutedExpert",
                (),
                {
                    "w1": _FakeModule(torch.arange(32, dtype=torch.float32).reshape(8, 4)),
                    "w2": _FakeModule(torch.arange(32, 64, dtype=torch.float32).reshape(4, 8)),
                    "w3": _FakeModule(torch.arange(64, 96, dtype=torch.float32).reshape(8, 4)),
                },
            )()
        ]


class _FakeRoutedMoeLayer(_FakeWeightedLayer):
    def __init__(self) -> None:
        super().__init__()
        self.mlp = _FakeRoutedMoeMlp()


class _FakeRoutedMoeBackbone(_FakeWeightedBackbone):
    def __init__(self) -> None:
        super().__init__()
        self.layers = [_FakeRoutedMoeLayer()]


class _FakeRoutedMoeModel(_FakeWeightedQwenModel):
    def __init__(self) -> None:
        self.config = _FakeRoutedMoeConfig()
        self.model = _FakeRoutedMoeBackbone()


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
            [
                [120, 121, 122, 123],
                [130, 131, 132, 133],
                [140, 141, 142, 143],
                [150, 151, 152, 153],
            ],
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
        self.embed_tokens = _FakeModule([[0, 1, 2, 3], [10, 11, 12, 13], [20, 21, 22, 23]])
        self.wte = self.embed_tokens
        self.wpe = _FakeModule([[30, 31, 32, 33], [40, 41, 42, 43]])
        self.layers = [_FakeListWeightedLayer()]


class _FakeListWeightedQwenModel(_FakeQwenModel):
    def __init__(self) -> None:
        self.config = _FakeConfig()
        self.model = _FakeListWeightedBackbone()


def _tuplify_nested(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_tuplify_nested(item) for item in value)
    return value


def _block_torch_and_numpy_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def blocked_import(
        name: str,
        globals_: Any | None = None,
        locals_: Any | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if name in {"torch", "numpy"} or name.startswith(("torch.", "numpy.")):
            raise ImportError(f"blocked optional dependency {name}")
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked_import)


def _require_component_ref(adapter: Any, name: str) -> ComponentRef:
    ref = adapter.parse_component_ref(name)
    assert ref is not None
    return ref


class _FakeTupleWeightedQwenModel(_FakeListWeightedQwenModel):
    def __init__(self) -> None:
        super().__init__()
        self.model.embed_tokens.weight = _tuplify_nested(self.model.embed_tokens.weight)
        self.model.wpe.weight = _tuplify_nested(self.model.wpe.weight)
        for layer in self.model.layers:
            for module in (
                layer.self_attn.q_proj,
                layer.self_attn.k_proj,
                layer.self_attn.v_proj,
                layer.self_attn.o_proj,
                layer.mlp.gate_proj,
                layer.mlp.up_proj,
                layer.mlp.down_proj,
            ):
                module.weight = _tuplify_nested(module.weight)
                module.bias = _tuplify_nested(module.bias)


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
        self.c_fc = _FakeConv1DModule(
            torch.arange(12, dtype=torch.float32).reshape(4, 3),
            torch.arange(3, dtype=torch.float32),
        )
        self.c_proj = _FakeConv1DModule(
            torch.arange(12, 24, dtype=torch.float32).reshape(3, 4),
            torch.arange(4, dtype=torch.float32),
        )


class _FakeGpt2Block(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        self.ln_1 = torch.nn.LayerNorm(6, elementwise_affine=False)
        self.ln_2 = torch.nn.LayerNorm(6, elementwise_affine=False)
        self.attn = _FakeGpt2Attention()
        self.mlp = _FakeGpt2Mlp()


class _FakeGpt2Transformer:
    def __init__(self) -> None:
        self.h: list[Any] = [_FakeGpt2Block()]


class _FakeGpt2Model:
    def __init__(self) -> None:
        self.config = _FakeGpt2Config()
        self.transformer = _FakeGpt2Transformer()


class _FakeHookableEmbedding(_FakeModule):
    def __init__(self, weight: Any) -> None:
        super().__init__(weight)

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        _ = kwargs
        torch = pytest.importorskip("torch")
        input_ids = value
        ids = input_ids if hasattr(input_ids, "shape") else torch.tensor(input_ids)
        embedded = self.weight[ids]
        return self.run_forward(embedded, inputs=(input_ids,))


class _FakeGpt2EmbeddingTransformer(_FakeGpt2Transformer):
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        super().__init__()
        self.wte = _FakeHookableEmbedding(torch.arange(60, dtype=torch.float32).reshape(10, 6))
        self.wpe = _FakeHookableEmbedding(
            torch.arange(600, 660, dtype=torch.float32).reshape(10, 6)
        )
        self.ln_f = torch.nn.LayerNorm(6, elementwise_affine=False)


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
        block = self.transformer.h[0]
        resid_pre = block.run_pre(embed + pos_embed)
        attn_input = block.ln_1(resid_pre)
        resid_mid = resid_pre + 1
        mlp_input = block.ln_2(resid_mid)
        logits = self.transformer.ln_f(resid_pre)
        return {
            "logits": logits,
            "resid_pre": resid_pre,
            "resid_mid": resid_mid,
            "attn_input": attn_input,
            "mlp_input": mlp_input,
        }


class _CallableGpt2Block(_FakeModule):
    def __init__(self, delta: float, layer_index: int) -> None:
        super().__init__()
        self.delta = delta
        self.layer_index = layer_index
        self.calls: list[dict[str, Any]] = []

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        hidden_states = value
        self.calls.append(kwargs)
        past_key_values = kwargs.get("past_key_values")
        if past_key_values is not None:
            torch = pytest.importorskip("torch")
            cache_keys = torch.full(
                (hidden_states.shape[0], 2, hidden_states.shape[1], 3), self.delta
            )
            cache_values = torch.full(
                (hidden_states.shape[0], 2, hidden_states.shape[1], 3), -self.delta
            )
            past_key_values.update(cache_keys, cache_values, self.layer_index)
        return self.run_forward(hidden_states + self.delta, inputs=(hidden_states,))


class _CallableGpt2Transformer(_FakeGpt2EmbeddingTransformer):
    def __init__(self) -> None:
        super().__init__()
        self.h = [_CallableGpt2Block(10.0, 0), _CallableGpt2Block(100.0, 1)]


class _FakeLmHead(_FakeModule):
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        super().__init__(torch.eye(6, dtype=torch.float32), torch.arange(6, dtype=torch.float32))

    def __call__(self, value: Any, **kwargs: Any) -> Any:
        _ = kwargs
        residual = value
        return self.run_forward(residual @ self.weight.T + self.bias, inputs=(residual,))


class _CallableGpt2Model(_FakeGpt2EmbeddingModel):
    def __init__(self) -> None:
        self.config = _FakeGpt2Config()
        self.config.n_layer = 2
        self.transformer = _CallableGpt2Transformer()
        self.lm_head = _FakeLmHead()
        self.calls: list[dict[str, Any]] = []

    def get_output_embeddings(self) -> _FakeLmHead:
        return self.lm_head

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        torch = pytest.importorskip("torch")
        self.calls.append(dict(kwargs))
        input_ids = kwargs["input_ids"]
        if not hasattr(input_ids, "shape"):
            input_ids = torch.tensor(input_ids)
        position_ids = torch.arange(input_ids.shape[-1]).unsqueeze(0).expand_as(input_ids)
        residual = self.transformer.wte(input_ids) + self.transformer.wpe(position_ids)
        for block in self.transformer.h:
            residual = block(
                residual,
                past_key_values=kwargs.get("past_key_values"),
                use_cache=kwargs.get("use_cache", False),
            )
        output = {"logits": self.lm_head(self.transformer.ln_f(residual))}
        if kwargs.get("use_cache"):
            output["past_key_values"] = kwargs.get("past_key_values")
        return output


class _FakeGptBigCodeConfig:
    model_type = "gpt_bigcode"
    n_head = 2
    num_key_value_heads = 1
    n_embd = 8
    n_layer = 1
    n_positions = 1024
    vocab_size = 49152
    n_inner = 16
    activation_function = "gelu_pytorch_tanh"


class _FakeGptBigCodeAttention:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.c_attn = _FakeModule(
            torch.arange(128, dtype=torch.float32).reshape(16, 8),
            torch.arange(16, dtype=torch.float32),
        )
        self.c_proj = _FakeModule(
            torch.arange(64, dtype=torch.float32).reshape(8, 8),
            torch.arange(8, dtype=torch.float32),
        )


class _FakeGptBigCodeMlp:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.c_fc = _FakeModule(
            torch.arange(128, dtype=torch.float32).reshape(16, 8),
            torch.arange(16, dtype=torch.float32),
        )
        self.c_proj = _FakeModule(
            torch.arange(128, 256, dtype=torch.float32).reshape(8, 16),
            torch.arange(8, dtype=torch.float32),
        )


class _FakeGptBigCodeBlock(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.ln_2 = _FakeModule()
        self.attn = _FakeGptBigCodeAttention()
        self.mlp = _FakeGptBigCodeMlp()


class _FakeGptBigCodeTransformer:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.wte = _FakeModule(torch.arange(40, dtype=torch.float32).reshape(5, 8))
        self.wpe = _FakeModule(torch.arange(48, dtype=torch.float32).reshape(6, 8))
        self.h = [_FakeGptBigCodeBlock()]


class _FakeGptBigCodeModel:
    def __init__(self) -> None:
        self.config = _FakeGptBigCodeConfig()
        self.transformer = _FakeGptBigCodeTransformer()


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
        self.input_layernorm = _FakeModule()
        self.post_attention_layernorm = _FakeModule()
        self.attention = _FakeGptNeoxAttention()
        self.mlp = _FakeGptNeoxMlp()


class _FakeGptNeoxBackbone:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.embed_in = _FakeModule(torch.arange(20, dtype=torch.float32).reshape(5, 4))
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
        torch = pytest.importorskip("torch")
        self.word_embeddings = _FakeModule(torch.arange(24, dtype=torch.float32).reshape(3, 8))
        self.h = [_FakeFalconMQABlock()]


class _FakeFalconMQAModel:
    def __init__(self) -> None:
        self.config = _FakeFalconMQAConfig()
        self.transformer = _FakeFalconMQATransformer()


class _FakeMptConfig:
    model_type = "mpt"
    n_heads = 2
    hidden_size = 4
    n_layers = 1


class _FakeMptAttention:
    def __init__(self) -> None:
        self.Wqkv = _FakeModule()
        self.out_proj = _FakeModule()


class _FakeMptMlp(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.up_proj = _FakeModule()
        self.down_proj = _FakeModule()


class _FakeMptBlock(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.norm_2 = _FakeModule()
        self.attn = _FakeMptAttention()
        self.ffn = _FakeMptMlp()


class _FakeMptTransformer:
    def __init__(self) -> None:
        self.blocks = [_FakeMptBlock()]


class _FakeMptModel:
    def __init__(self) -> None:
        self.config = _FakeMptConfig()
        self.transformer = _FakeMptTransformer()


class _FakeOptConfig:
    model_type = "opt"
    num_attention_heads = 2
    hidden_size = 4
    num_hidden_layers = 1
    ffn_dim = 3
    vocab_size = 5
    max_position_embeddings = 6


class _FakeOptDecoder:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.embed_tokens = _FakeModule(torch.arange(20, dtype=torch.float32).reshape(5, 4))
        self.embed_positions = _FakeModule(torch.arange(24, dtype=torch.float32).reshape(6, 4))
        self.layers = [_FakeModule()]


class _FakeOptBackbone:
    def __init__(self) -> None:
        self.decoder = _FakeOptDecoder()


class _FakeOptModel:
    def __init__(self) -> None:
        self.config = _FakeOptConfig()
        self.model = _FakeOptBackbone()

    def get_input_embeddings(self) -> _FakeModule:
        return self.model.decoder.embed_tokens


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
    num_hidden_layers = 1
    hidden_size = 4
    intermediate_size = 3


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
        self.intermediate = type("_FakeBertIntermediate", (), {"dense": _FakeModule()})()
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
    num_hidden_layers = 1
    dim = 4
    hidden_dim = 3


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
        self.ffn.lin1 = _FakeModule()
        self.ffn.lin2 = _FakeModule()


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
        self.intermediate_dense = _FakeModule()
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
    num_layers = 1
    num_heads = 2
    d_kv = 2
    d_model = 4
    d_ff = 3


class _FakeT5Model:
    config: Any

    def __init__(self) -> None:
        self.config = _FakeT5Config()


class _FakeNestedTextConfigT5Model(_FakeT5Model):
    def __init__(self) -> None:
        super().__init__()
        self.config = type(
            "_FakeNestedTextConfigT5WrapperConfig",
            (),
            {
                "model_type": "vision_text_wrapper",
                "text_config": _FakeT5Config(),
            },
        )()


class _FakeNestedTextConfigBertModel(_FakeBertModel):
    def __init__(self) -> None:
        super().__init__()
        self.config = type(
            "_FakeNestedTextConfigBertWrapperConfig",
            (),
            {
                "model_type": "vision_text_wrapper",
                "text_config": _FakeBertConfig(),
            },
        )()


class _FakeDictNestedTextConfigT5Model(_FakeT5Model):
    def __init__(self) -> None:
        super().__init__()
        self.config = {
            "model_type": "vision_text_wrapper",
            "text_config": {
                "model_type": "t5",
                "decoder_start_token_id": 0,
                "pad_token_id": 0,
                "num_layers": 1,
            },
        }


class _FakeWeightedBertModel(_FakeBertModel):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        layer: Any = self.encoder.layer[0]
        layer.intermediate.dense = _FakeModule(
            torch.arange(12, dtype=torch.float32).reshape(3, 4),
            torch.arange(3, dtype=torch.float32),
        )
        layer.output.dense = _FakeModule(
            torch.arange(12, 24, dtype=torch.float32).reshape(4, 3),
            torch.arange(4, dtype=torch.float32),
        )


class _FakeWeightedDistilBertModel(_FakeDistilBertModel):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        ffn = self.transformer.layer[0].ffn
        ffn.lin1 = _FakeModule(
            torch.arange(12, dtype=torch.float32).reshape(3, 4),
            torch.arange(3, dtype=torch.float32),
        )
        ffn.lin2 = _FakeModule(
            torch.arange(12, 24, dtype=torch.float32).reshape(4, 3),
            torch.arange(4, dtype=torch.float32),
        )


class _FakeT5Attention:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.q = _FakeModule(
            torch.arange(16, dtype=torch.float32).reshape(4, 4),
            torch.arange(4, dtype=torch.float32),
        )
        self.k = _FakeModule(
            torch.arange(16, 32, dtype=torch.float32).reshape(4, 4),
            torch.arange(4, 8, dtype=torch.float32),
        )
        self.v = _FakeModule(
            torch.arange(32, 48, dtype=torch.float32).reshape(4, 4),
            torch.arange(8, 12, dtype=torch.float32),
        )
        self.o = _FakeModule(
            torch.arange(48, 64, dtype=torch.float32).reshape(4, 4),
            torch.arange(12, 16, dtype=torch.float32),
        )


class _FakeT5DenseReluDense(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        torch = pytest.importorskip("torch")
        self.wi = _FakeModule(torch.arange(12, dtype=torch.float32).reshape(3, 4))
        self.wo = _FakeModule(torch.arange(12, 24, dtype=torch.float32).reshape(4, 3))


class _FakeT5FfnLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.layer_norm = _FakeModule()
        self.DenseReluDense = _FakeT5DenseReluDense()


class _FakeT5SelfAttentionLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.layer_norm = _FakeModule()
        self.SelfAttention = _FakeT5Attention()


class _FakeT5CrossAttentionLayer(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.layer_norm = _FakeModule()
        self.EncDecAttention = _FakeT5Attention()


class _FakeT5Block(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.layer = [_FakeT5SelfAttentionLayer(), _FakeT5FfnLayer()]


class _FakeT5DecoderBlock(_FakeModule):
    def __init__(self) -> None:
        super().__init__()
        self.layer = [
            _FakeT5SelfAttentionLayer(),
            _FakeT5CrossAttentionLayer(),
            _FakeT5FfnLayer(),
        ]


class _FakeT5Encoder:
    def __init__(self) -> None:
        self.block = [_FakeT5Block()]


class _FakeT5Decoder:
    def __init__(self) -> None:
        self.block = [_FakeT5DecoderBlock()]


class _FakeWeightedT5Model(_FakeT5Model):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = _FakeT5Encoder()
        self.decoder = _FakeT5Decoder()

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        torch = pytest.importorskip("torch")
        input_ids = kwargs["input_ids"]
        decoder_input_ids = kwargs["decoder_input_ids"]
        if not hasattr(input_ids, "shape"):
            input_ids = torch.tensor(input_ids)
        if not hasattr(decoder_input_ids, "shape"):
            decoder_input_ids = torch.tensor(decoder_input_ids)

        batch = int(input_ids.shape[0])
        encoder_pos = int(input_ids.shape[1])
        decoder_pos = int(decoder_input_ids.shape[1])
        encoder_hidden = torch.zeros(batch, encoder_pos, self.config.d_model)
        decoder_hidden = torch.zeros(batch, decoder_pos, self.config.d_model)

        encoder_block = self.encoder.block[0]
        encoder_hidden = encoder_block.run_pre(encoder_hidden)
        encoder_attn_in = encoder_block.layer[0].layer_norm.run_pre(encoder_hidden)
        encoder_self_attn = encoder_block.layer[0].SelfAttention
        encoder_q = encoder_self_attn.q(encoder_attn_in)
        encoder_k = encoder_self_attn.k(encoder_attn_in)
        encoder_v = encoder_self_attn.v(encoder_attn_in)
        encoder_mlp_in = encoder_block.layer[1].layer_norm.run_pre(encoder_q)
        encoder_mlp_out = encoder_block.layer[1].DenseReluDense.run_forward(
            encoder_mlp_in,
            inputs=(encoder_mlp_in,),
        )
        encoder_hidden = encoder_block.run_forward(encoder_mlp_out, inputs=(encoder_hidden,))

        decoder_block = self.decoder.block[0]
        decoder_hidden = decoder_block.run_pre(decoder_hidden)
        self_attn = decoder_block.layer[0].SelfAttention
        decoder_attn_in = decoder_block.layer[0].layer_norm.run_pre(decoder_hidden)
        decoder_q = self_attn.q(decoder_attn_in)
        decoder_k = self_attn.k(decoder_attn_in)
        decoder_v = self_attn.v(decoder_attn_in)
        decoder_z = self_attn.o.run_pre(decoder_q)
        decoder_z = self_attn.o.run_forward(decoder_z, inputs=(decoder_z,))
        decoder_mid = decoder_hidden + decoder_z
        decoder_mid = decoder_block.layer[1].run_pre(decoder_mid)
        cross_attn_in = decoder_block.layer[1].layer_norm.run_pre(decoder_mid)
        cross_attn = decoder_block.layer[1].EncDecAttention
        cross_q = cross_attn.q.run_forward(cross_attn_in)
        cross_z = cross_attn.o.run_pre(cross_q)
        cross_z = cross_attn.o.run_forward(cross_z, inputs=(cross_z,))
        decoder_mid_cross = decoder_mid + cross_z
        decoder_mid_cross = decoder_block.layer[2].run_pre(decoder_mid_cross)
        ffn = decoder_block.layer[2].DenseReluDense
        decoder_mlp_in = decoder_block.layer[2].layer_norm.run_pre(decoder_mid_cross)
        mlp_pre = ffn.wi.run_forward(decoder_mlp_in)
        mlp_out = ffn.run_forward(decoder_mlp_in, inputs=(decoder_mlp_in,))
        decoder_post = ffn.wo.run_pre(mlp_pre)
        decoder_post = decoder_block.run_forward(
            decoder_mid_cross + decoder_post,
            inputs=(decoder_hidden,),
        )

        return {
            "logits": decoder_post,
            "encoder_hidden": encoder_hidden,
            "encoder_attn_in": encoder_attn_in,
            "encoder_q": encoder_q,
            "encoder_k": encoder_k,
            "encoder_v": encoder_v,
            "encoder_mlp_in": encoder_mlp_in,
            "encoder_mlp_out": encoder_mlp_out,
            "decoder_attn_in": decoder_attn_in,
            "decoder_q": decoder_q,
            "decoder_k": decoder_k,
            "decoder_v": decoder_v,
            "cross_attn_in": cross_attn_in,
            "cross_q": cross_q,
            "cross_z": cross_z,
            "decoder_mlp_in": decoder_mlp_in,
            "mlp_out": mlp_out,
            "output_attentions": kwargs.get("output_attentions", False),
        }


class _FakeAsymmetricT5Config(_FakeT5Config):
    num_layers = 1
    num_decoder_layers = 2


class _FakeAsymmetricT5Model(_FakeWeightedT5Model):
    def __init__(self) -> None:
        self.config = _FakeAsymmetricT5Config()
        self.encoder = _FakeT5Encoder()
        self.decoder = _FakeT5Decoder()
        self.decoder.block.append(_FakeT5DecoderBlock())


class _TokenHelperTokenizer:
    bos_token_id = 0
    pad_token_id = 999
    padding_side = "left"


class _FakeEmbedding:
    def __init__(self, weight: Any, bias: Any | None = None) -> None:
        self.weight = weight
        self.bias = bias


class _FakeUnembeddingModel:
    def __init__(self, weight: Any, bias: Any | None = None) -> None:
        self._weight = weight
        self._bias = bias

    def get_output_embeddings(self) -> _FakeEmbedding | None:
        return _FakeEmbedding(self._weight, self._bias)


class _FakeTransformerLensNativeUnembedModel:
    def __init__(self, W_U: Any, b_U: Any | None = None) -> None:
        self.W_U = W_U
        self.b_U = b_U

    def get_output_embeddings(self) -> None:
        return None


class _FakeFinalNormUnembeddingModel(_FakeUnembeddingModel):
    def __init__(self, weight: Any, bias: Any | None = None, ln_final: Any | None = None) -> None:
        super().__init__(weight, bias)
        self.ln_f = ln_final


class _FakeNativeFinalNormUnembeddingModel(_FakeTransformerLensNativeUnembedModel):
    def __init__(self, W_U: Any, b_U: Any | None = None, ln_final: Any | None = None) -> None:
        super().__init__(W_U, b_U)
        self.ln_final = ln_final


class _FakeGenerateModel:
    def __init__(self) -> None:
        torch = pytest.importorskip("torch")
        self.calls: list[dict[str, Any]] = []
        self.embed = _FakeHookableEmbedding(
            torch.arange(256 * 3, dtype=torch.float32).reshape(256, 3)
        )

    def generate(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        input_ids: Any = kwargs.get("input_ids")
        input_embeds: Any = kwargs.get("inputs_embeds")
        try:
            import torch

            if hasattr(input_ids, "shape"):
                suffix = torch.full(
                    (input_ids.shape[0], 1),
                    ord("!"),
                    dtype=input_ids.dtype,
                    device=input_ids.device,
                )
                sequences = torch.cat([input_ids, suffix], dim=1)
                if kwargs.get("return_dict_in_generate"):
                    from transformers.generation.utils import GenerateDecoderOnlyOutput

                    payload: dict[str, Any] = {"sequences": sequences}
                    if kwargs.get("output_logits"):
                        payload["logits"] = (torch.zeros(input_ids.shape[0], 3),)
                    if kwargs.get("output_scores"):
                        payload["scores"] = (torch.ones(input_ids.shape[0], 3),)
                    return GenerateDecoderOnlyOutput(**payload)
                return sequences
            if hasattr(input_embeds, "shape"):
                sequences = torch.full(
                    (input_embeds.shape[0], 1),
                    ord("!"),
                    dtype=torch.long,
                    device=input_embeds.device,
                )
                if kwargs.get("return_dict_in_generate"):
                    from transformers.generation.utils import GenerateDecoderOnlyOutput

                    payload = {"sequences": sequences}
                    if kwargs.get("output_logits"):
                        payload["logits"] = (torch.zeros(input_embeds.shape[0], 3),)
                    if kwargs.get("output_scores"):
                        payload["scores"] = (torch.ones(input_embeds.shape[0], 3),)
                    return GenerateDecoderOnlyOutput(**payload)
                return sequences
        except ImportError:
            pass
        return [list(row) + [ord("!")] for row in input_ids]

    def get_input_embeddings(self) -> _FakeHookableEmbedding:
        return self.embed


class _FakeSeq2SeqGenerateConfig:
    model_type = "t5"
    is_encoder_decoder = True


class _FakeSeq2SeqGenerateModel:
    def __init__(self, sequences: Any | None = None) -> None:
        torch = pytest.importorskip("torch")
        self.config = _FakeSeq2SeqGenerateConfig()
        self.calls: list[dict[str, Any]] = []
        self.sequences = (
            sequences
            if sequences is not None
            else torch.tensor([[ord("x"), ord("y"), ord("z")]], dtype=torch.long)
        )
        self.embed = _FakeHookableEmbedding(
            torch.arange(256 * 3, dtype=torch.float32).reshape(256, 3)
        )

    def generate(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        pytest.importorskip("torch")
        reference: Any = kwargs.get("input_ids", kwargs.get("inputs_embeds"))
        sequences = self.sequences
        if hasattr(reference, "device"):
            sequences = sequences.to(reference.device)
        if kwargs.get("return_dict_in_generate"):
            from transformers.generation.utils import GenerateEncoderDecoderOutput

            return GenerateEncoderDecoderOutput(sequences=sequences)
        return sequences

    def get_input_embeddings(self) -> _FakeHookableEmbedding:
        return self.embed


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


class _FakeAudioProcessor:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        audio: Any,
        *,
        sampling_rate: int,
        return_tensors: str,
        **kwargs: Any,
    ) -> _FakeTokenizerOutput:
        torch = pytest.importorskip("torch")
        self.calls.append(
            {
                "audio": audio,
                "sampling_rate": sampling_rate,
                "return_tensors": return_tensors,
                "kwargs": dict(kwargs),
            }
        )
        return _FakeTokenizerOutput({"input_values": torch.tensor([[0.0, 1.0]])})


class _FakeTextTokenizer:
    bos_token: Any = "<bos>"
    bos_token_id: Any = 0
    eos_token: Any = "<eos>"
    eos_token_id: Any = 999
    pad_token: Any = "<pad>"
    pad_token_id: Any = 999
    padding_side: Any = "right"

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
                rows = [[self.eos_token_id] * (max_length - len(row)) + row for row in rows]
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
        truncation: bool = False,
        max_length: int | None = None,
    ) -> Any:
        _ = truncation, max_length
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


class _PlainGpt2Tokenizer(_FakeTextTokenizer):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        kwargs["add_special_tokens"] = False
        return super().__call__(*args, **kwargs)


class _PlainGpt2TokenizerWithoutPad(_FakeTokenizerWithoutPadToken):
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        kwargs["add_special_tokens"] = False
        return super().__call__(*args, **kwargs)


class _TinyTextTokenizer(_FakeTextTokenizer):
    pad_token_id = 9
    eos_token_id = 9
    _ids = {"a": 1, "b": 2, "c": 3}

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
            token_ids = [self._ids[char] for char in item]
            if add_special_tokens:
                token_ids = [self.bos_token_id, *token_ids]
            if truncation and max_length is not None:
                token_ids = token_ids[:max_length]
            rows.append(token_ids)
        if padding:
            max_length = max((len(row) for row in rows), default=0)
            if self.padding_side == "left":
                rows = [[self.pad_token_id] * (max_length - len(row)) + row for row in rows]
            else:
                rows = [row + [self.pad_token_id] * (max_length - len(row)) for row in rows]
        return _FakeTokenizerOutput({"input_ids": torch.tensor(rows)})


class _TokenizerMissingDefaults(_PlainGpt2Tokenizer):
    eos_token = "<eos>"
    eos_token_id = 999
    bos_token = None
    bos_token_id = None
    pad_token = None
    pad_token_id = None
    padding_side = None

    def encode(self, text: str) -> list[int]:
        return [ord(char) for char in text]


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


def test_architecture_adapter_maps_mamba_ssm_components() -> None:
    model = _FakeMambaModel()
    adapter = architecture_adapter_for_model(model, model_name="state-spaces/mamba-130m-hf")

    assert adapter.name == "mamba_ssm"
    assert (
        architecture_adapter_for_name(
            model_name="state-spaces/mamba-130m-hf",
            model_type="mamba",
        ).name
        == "mamba_ssm"
    )
    assert transformer_lens_component_name("ssm_in", 0) == "blocks.0.ssm.hook_in"
    assert adapter.parse_component_ref("blocks.0.ssm.hook_in").safelens_name == "layer_0.ssm_in"  # type: ignore[union-attr]
    assert adapter.parse_component_ref("blocks.0.ssm.hook_dt").safelens_name == "layer_0.ssm_dt"  # type: ignore[union-attr]
    assert "ssm_in" in adapter.supported_components()
    assert "pattern" not in adapter.supported_components()

    adapter.register_component_hook(
        model,
        "blocks.0.ssm.hook_in",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "blocks.0.ssm.hook_out",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )

    mixer = model.backbone.layers[0].mixer
    assert mixer.in_proj.run_forward(["x"]) == ["x", "ssm_in"]
    assert mixer.out_proj.run_pre(["x"]) == ["x", "ssm_out"]
    with pytest.raises(NotImplementedError, match="state-space model"):
        adapter.register_component_hook(model, "blocks.0.attn.hook_pattern", lambda **_kwargs: None)


def test_transformer_lens_compatible_wrapper_caches_mamba_ssm_hooks() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="state-spaces/mamba-130m-hf")
    wrapper.model = _FakeMambaModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.ssm.hook_in", "blocks.0.ssm.hook_out"],
    )

    assert output == {"ssm_in": ["in"], "ssm_out": ["out"]}
    assert cache == {
        "blocks.0.ssm.hook_in": ["in"],
        "blocks.0.ssm.hook_out": ["out"],
    }
    assert wrapper.cfg.normalization_type == "RMS"


def test_architecture_adapter_maps_mamba2_ssm_components() -> None:
    model = _FakeMamba2Model()
    adapter = architecture_adapter_for_model(model, model_name="state-spaces/mamba2-130m")

    assert adapter.name == "mamba2_ssm"
    assert (
        architecture_adapter_for_name(
            model_name="state-spaces/mamba2-130m",
            model_type="mamba2",
        ).name
        == "mamba2_ssm"
    )
    assert (
        _require_component_ref(adapter, "blocks.0.ssm.hook_inner_norm").safelens_name
        == "layer_0.ssm_inner_norm"
    )

    adapter.register_component_hook(
        model,
        "blocks.0.ssm.hook_inner_norm",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )

    assert model.backbone.layers[0].mixer.norm.run_pre(["x"]) == ["x", "ssm_inner_norm"]
    assert adapter.supported_components(for_cache=True) == (
        "resid_pre",
        "resid_post",
        "ln1_normalized",
        "ssm_in",
        "ssm_conv",
        "ssm_inner_norm",
        "ssm_out",
    )


def test_component_hook_accepts_positional_activation_with_extra_kwargs() -> None:
    ref = ComponentRef(layer=0, component="q", original="layer_0.q")

    def append_metadata(value: list[str], **kwargs: Any) -> list[str]:
        return value + [kwargs["component"], kwargs["hook"].name]

    output = call_component_hook(
        append_metadata,
        activation=["x"],
        component_ref=ref,
        architecture="llama_like_decoder",
    )

    assert output == ["x", "q", "blocks.0.attn.hook_q"]


def test_component_hook_passes_activation_and_context_to_variadic_positional_hooks() -> None:
    ref = ComponentRef(layer=0, component="q", original="layer_0.q")
    seen: list[tuple[Any, ...]] = []

    def variadic(*args: Any) -> list[str]:
        seen.append(args)
        activation, hook = args
        return activation + [hook.name]

    output = call_component_hook(
        variadic,
        activation=["x"],
        component_ref=ref,
        architecture="llama_like_decoder",
    )

    assert output == ["x", "blocks.0.attn.hook_q"]
    assert len(seen) == 1
    assert seen[0][0] == ["x"]
    assert isinstance(seen[0][1], ComponentHookContext)
    assert seen[0][1].name == "blocks.0.attn.hook_q"


def test_component_hook_prefers_keyword_metadata_for_variadic_keyword_hooks() -> None:
    ref = ComponentRef(layer=0, component="q", original="layer_0.q")
    seen: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def variadic(*args: Any, **kwargs: Any) -> list[str]:
        seen.append((args, kwargs))
        return kwargs["activation"] + [kwargs["component"], kwargs["hook"].name]

    output = call_component_hook(
        variadic,
        activation=["x"],
        component_ref=ref,
        architecture="llama_like_decoder",
    )

    assert output == ["x", "q", "blocks.0.attn.hook_q"]
    assert len(seen) == 1
    args, kwargs = seen[0]
    assert args == ()
    assert kwargs["activation"] == ["x"]
    assert kwargs["component"] == "q"
    assert isinstance(kwargs["hook"], ComponentHookContext)


def test_component_hook_propagates_internal_type_errors_with_alternate_names() -> None:
    ref = ComponentRef(layer=0, component="q", original="layer_0.q")

    def broken(value: list[str], point: ComponentHookContext) -> list[str]:
        _ = value, point
        raise TypeError("component hook inner bug")

    with pytest.raises(TypeError, match="component hook inner bug"):
        call_component_hook(
            broken,
            activation=["x"],
            component_ref=ref,
            architecture="llama_like_decoder",
        )


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


def test_t5_architecture_adapter_supports_decoder_and_cross_attention_paths() -> None:
    torch = pytest.importorskip("torch")
    model = _FakeWeightedT5Model()
    adapter = architecture_adapter_for_model(model, model_name="google-t5/t5-small")

    supported = set(adapter.supported_components(include_unsupported=True))
    assert {
        "decoder_q",
        "decoder_z",
        "decoder_result",
        "decoder_resid_mid_cross",
        "decoder_mlp_in",
        "decoder_q_input",
        "decoder_k_input",
        "decoder_v_input",
        "decoder_attn_in",
        "decoder_post",
        "cross_attn_in",
        "cross_attn_out",
        "cross_q",
        "cross_z",
        "cross_result",
        "q_input",
        "k_input",
        "v_input",
        "attn_in",
        "mlp_in",
    } <= supported
    assert (
        _require_component_ref(adapter, "encoder.0.hook_q_input").safelens_name
        == "layer_0.q_input"
    )
    assert (
        _require_component_ref(adapter, "encoder.0.hook_attn_in").safelens_name
        == "layer_0.attn_in"
    )
    assert _require_component_ref(adapter, "encoder.0.attn.hook_q").safelens_name == "layer_0.q"
    assert (
        _require_component_ref(adapter, "encoder.0.hook_mlp_in").safelens_name
        == "layer_0.mlp_in"
    )
    assert (
        _require_component_ref(adapter, "encoder.0.mlp.hook_post").safelens_name
        == "layer_0.post"
    )
    assert (
        _require_component_ref(adapter, "decoder.0.hook_q_input").safelens_name
        == "layer_0.decoder_q_input"
    )
    assert (
        _require_component_ref(adapter, "decoder.0.hook_attn_in").safelens_name
        == "layer_0.decoder_attn_in"
    )
    assert (
        _require_component_ref(adapter, "decoder.0.attn.hook_q").safelens_name
        == "layer_0.decoder_q"
    )
    assert (
        _require_component_ref(adapter, "decoder.0.cross_attn.hook_q").safelens_name
        == "layer_0.cross_q"
    )
    assert (
        _require_component_ref(adapter, "decoder.0.hook_mlp_in").safelens_name
        == "layer_0.decoder_mlp_in"
    )
    assert (
        _require_component_ref(adapter, "blocks.0.cross_attn.hook_q").safelens_name
        == "layer_0.cross_q"
    )
    assert (
        _require_component_ref(adapter, "layer_0.q_input").transformer_lens_name
        == "encoder.0.hook_q_input"
    )
    assert (
        _require_component_ref(adapter, "layer_0.q").transformer_lens_name
        == "encoder.0.attn.hook_q"
    )
    assert (
        _require_component_ref(adapter, "layer_0.mlp_in").transformer_lens_name
        == "encoder.0.hook_mlp_in"
    )
    assert transformer_lens_component_name("q_input", 0) == "blocks.0.hook_q_input"
    assert transformer_lens_component_name("attn_in", 0) == "blocks.0.hook_attn_in"
    assert transformer_lens_component_name("decoder_q", 0) == "decoder.0.attn.hook_q"
    assert transformer_lens_component_name("decoder_q_input", 0) == "decoder.0.hook_q_input"
    assert transformer_lens_component_name("decoder_attn_in", 0) == "decoder.0.hook_attn_in"
    assert transformer_lens_component_name("cross_attn_in", 0) == "decoder.0.hook_cross_attn_in"
    assert transformer_lens_component_name("cross_q", 0) == "decoder.0.cross_attn.hook_q"
    assert (
        transformer_lens_component_name("decoder_resid_mid_cross", 0)
        == "decoder.0.hook_resid_mid_cross"
    )
    assert transformer_lens_component_name("decoder_mlp_in", 0) == "decoder.0.hook_mlp_in"

    adapter.register_component_hook(
        model,
        "encoder.0.hook_mlp_in",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "decoder.0.attn.hook_q",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "decoder.0.cross_attn.hook_q",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "decoder.0.cross_attn.hook_z",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "decoder.0.mlp.hook_post",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "decoder.0.hook_resid_mid_cross",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )
    adapter.register_component_hook(
        model,
        "decoder.0.hook_mlp_in",
        lambda **kwargs: kwargs["activation"] + [kwargs["component"]],
    )

    encoder_block = model.encoder.block[0]
    decoder_block = model.decoder.block[0]
    self_attn = decoder_block.layer[0].SelfAttention
    cross_attn = decoder_block.layer[1].EncDecAttention
    ffn = decoder_block.layer[2].DenseReluDense

    input_tensor = torch.arange(4, dtype=torch.float32).reshape(1, 1, 4)
    seen_shapes: dict[str, tuple[int, ...]] = {}

    def constant_patch(name: str, value: float) -> Any:
        def hook(**kwargs: Any) -> Any:
            seen_shapes[name] = tuple(kwargs["activation"].shape)
            return torch.ones_like(kwargs["activation"]) * value

        return hook

    adapter.register_component_hook(
        model,
        "encoder.0.hook_q_input",
        constant_patch("q_input", 3),
    )
    assert torch.equal(encoder_block.layer[0].layer_norm.run_pre(input_tensor), input_tensor)
    encoder_q = encoder_block.layer[0].SelfAttention.q(input_tensor)
    assert seen_shapes["q_input"] == (1, 1, 2, 4)
    assert tuple(encoder_q.shape) == (1, 1, 4)
    isolated_model = _FakeWeightedT5Model()
    isolated_decoder_block = isolated_model.decoder.block[0]
    isolated_adapter = architecture_adapter_for_model(
        isolated_model,
        model_name="google-t5/t5-small",
    )
    isolated_adapter.register_component_hook(
        isolated_model,
        "decoder.0.hook_q_input",
        constant_patch("decoder_q_input", 4),
    )
    assert torch.equal(
        isolated_decoder_block.layer[0].layer_norm.run_pre(input_tensor), input_tensor
    )
    decoder_q = isolated_decoder_block.layer[0].SelfAttention.q(input_tensor)
    assert seen_shapes["decoder_q_input"] == (1, 1, 2, 4)
    assert tuple(decoder_q.shape) == (1, 1, 4)
    adapter.register_component_hook(
        model,
        "decoder.0.hook_cross_attn_in",
        constant_patch("cross_attn_in", 9),
    )
    assert torch.equal(
        decoder_block.layer[1].layer_norm.run_pre(input_tensor),
        torch.ones_like(input_tensor) * 9,
    )
    assert seen_shapes["cross_attn_in"] == (1, 1, 4)
    assert encoder_block.layer[1].layer_norm.run_pre(["x"]) == ["x", "mlp_in"]
    assert self_attn.q.run_forward(["x"]) == ["x", "decoder_q"]
    assert cross_attn.q.run_forward(["x"]) == ["x", "cross_q"]
    assert cross_attn.o.run_pre(["x"]) == ["x", "cross_z"]
    assert ffn.wo.run_pre(["x"]) == ["x", "decoder_post"]
    assert decoder_block.layer[2].run_pre(["x"]) == ["x", "decoder_resid_mid_cross"]
    assert decoder_block.layer[2].layer_norm.run_pre(["x"]) == ["x", "decoder_mlp_in"]


def test_t5_prefixed_attention_components_use_base_weight_shapes_and_cache_aliases() -> None:
    torch = pytest.importorskip("torch")
    model = _FakeWeightedT5Model()
    adapter = architecture_adapter_for_model(model, model_name="google-t5/t5-small")

    decoder_q = adapter.get_attention_weight(model, "decoder_q", 0)
    cross_q = adapter.get_attention_weight(model, "cross_q", 0)
    cross_z = adapter.get_attention_weight(model, "cross_z", 0)

    expected_q = reshape_attention_weight(
        model.decoder.block[0].layer[0].SelfAttention.q.weight,
        component="q",
        n_heads=2,
        packed_axis=0,
    )
    expected_z = reshape_attention_weight(
        model.decoder.block[0].layer[1].EncDecAttention.o.weight,
        component="z",
        n_heads=2,
        packed_axis=1,
    )
    assert torch.equal(decoder_q, expected_q)
    assert torch.equal(cross_q, expected_q)
    assert torch.equal(cross_z, expected_z)
    assert attention_head_dim(model) == 2

    cache = ActivationCache(
        {
            "encoder.0.hook_q_input": ["encoder_q_input"],
            "encoder.0.hook_attn_in": ["encoder_attn_in"],
            "encoder.0.attn.hook_q": ["encoder_q"],
            "encoder.0.hook_mlp_in": ["encoder_mlp_in"],
            "encoder.1.hook_q_input": ["encoder_last_q_input"],
            "encoder.1.attn.hook_q": ["encoder_last_q"],
            "decoder.0.hook_q_input": ["decoder_q_input"],
            "decoder.0.hook_attn_in": ["decoder_attn_in"],
            "decoder.0.hook_cross_attn_in": ["cross_attn_in"],
            "decoder.0.cross_attn.hook_q": ["cross_q"],
            "decoder.0.attn.hook_q": ["decoder_q"],
            "decoder.0.hook_resid_mid_cross": ["mid_cross"],
            "decoder.0.hook_mlp_in": ["decoder_mlp_in"],
            "decoder.1.hook_resid_pre": ["decoder_last_resid_pre"],
            "decoder.1.hook_mlp_in": ["decoder_last_mlp_in"],
        }
    )
    assert cache[("q_input", 0)] == ["encoder_q_input"]
    assert cache[("attn_in", 0)] == ["encoder_attn_in"]
    assert cache[("q", 0)] == ["encoder_q"]
    assert cache["layer_0.q"] == ["encoder_q"]
    assert cache[("mlp_in", 0)] == ["encoder_mlp_in"]
    assert cache["layer_0.mlp_in"] == ["encoder_mlp_in"]
    assert cache[("decoder_q_input", 0)] == ["decoder_q_input"]
    assert cache[("decoder_attn_in", 0)] == ["decoder_attn_in"]
    assert cache[("cross_attn_in", 0)] == ["cross_attn_in"]
    assert cache[("cross_q", 0)] == ["cross_q"]
    assert cache["layer_0.decoder_q"] == ["decoder_q"]
    assert cache[("decoder_resid_mid_cross", 0)] == ["mid_cross"]
    assert cache[("decoder_mlp_in", 0)] == ["decoder_mlp_in"]
    assert cache["layer_0.decoder_mlp_in"] == ["decoder_mlp_in"]
    assert cache[("q_input", -1)] == ["encoder_last_q_input"]
    assert cache[("q", -1)] == ["encoder_last_q"]
    assert cache[("decoder_resid_pre", -1)] == ["decoder_last_resid_pre"]
    assert cache[("decoder_mlp_in", -1)] == ["decoder_last_mlp_in"]
    assert ("decoder_mlp_in", -1) in cache


def test_transformer_lens_wrapper_runs_t5_decoder_cross_attention_cache_workflow() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.model = _FakeWeightedT5Model()

    with pytest.raises(AssertionError, match="use_split_qkv_input"):
        wrapper.run_with_cache(
            {"input_ids": [[1, 2, 3]], "decoder_input_ids": [[0, 4]]},
            layers=["encoder.0.hook_q_input"],
        )

    wrapper.set_use_split_qkv_input(True)
    wrapper.set_use_attn_in(True)
    wrapper.set_use_hook_mlp_in(True)

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2, 3]], "decoder_input_ids": [[0, 4]]},
        layers=[
            "encoder.0.hook_q_input",
            "encoder.0.hook_attn_in",
            "encoder.0.attn.hook_q",
            "decoder.0.hook_q_input",
            "decoder.0.hook_attn_in",
            "decoder.0.attn.hook_q",
            "decoder.0.hook_cross_attn_in",
            "decoder.0.cross_attn.hook_q",
            "decoder.0.cross_attn.hook_z",
            "decoder.0.hook_resid_mid_cross",
            "encoder.0.hook_mlp_in",
            "decoder.0.hook_mlp_in",
        ],
        return_cache_object=True,
    )
    assert isinstance(cache, ActivationCache)

    assert tuple(output["logits"].shape) == (1, 2, 4)
    assert tuple(cache[("q_input", 0)].shape) == (1, 3, 2, 4)
    assert tuple(cache[("attn_in", 0)].shape) == (1, 3, 2, 4)
    assert tuple(cache[("q", 0)].shape) == (1, 3, 2, 2)
    assert tuple(cache[("decoder_q_input", 0)].shape) == (1, 2, 2, 4)
    assert tuple(cache[("decoder_attn_in", 0)].shape) == (1, 2, 2, 4)
    assert tuple(cache[("decoder_q", 0)].shape) == (1, 2, 2, 2)
    assert tuple(cache[("cross_attn_in", 0)].shape) == (1, 2, 4)
    assert tuple(cache[("cross_q", 0)].shape) == (1, 2, 2, 2)
    assert tuple(cache[("cross_z", 0)].shape) == (1, 2, 2, 2)
    assert tuple(cache[("decoder_resid_mid_cross", 0)].shape) == (1, 2, 4)
    assert tuple(cache[("mlp_in", 0)].shape) == (1, 3, 4)
    assert tuple(cache[("decoder_mlp_in", 0)].shape) == (1, 2, 4)
    assert torch.equal(cache["encoder.0.hook_q_input"], cache[("q_input", 0)])
    assert torch.equal(cache["decoder.0.hook_q_input"], cache[("decoder_q_input", 0)])
    assert torch.equal(cache["decoder.0.hook_cross_attn_in"], cache[("cross_attn_in", 0)])
    assert torch.equal(cache["encoder.0.attn.hook_q"], cache[("q", 0)])
    assert torch.equal(cache["decoder.0.cross_attn.hook_q"], cache[("cross_q", 0)])
    assert torch.equal(cache["encoder.0.hook_mlp_in"], cache[("mlp_in", 0)])
    assert torch.equal(cache["decoder.0.hook_mlp_in"], cache[("decoder_mlp_in", 0)])


def test_transformer_lens_wrapper_runs_t5_decoder_cross_attention_patch_workflow() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.model = _FakeWeightedT5Model()
    wrapper.set_use_split_qkv_input(True)
    wrapper.set_use_attn_in(True)
    wrapper.set_use_hook_mlp_in(True)

    patched = wrapper.run_with_hooks(
        {"input_ids": [[1, 2, 3]], "decoder_input_ids": [[0, 4]]},
        fwd_hooks=[
            (
                "encoder.0.hook_q_input",
                lambda **kwargs: torch.ones_like(kwargs["activation"]) * 2,
            ),
            (
                "encoder.0.hook_k_input",
                lambda **kwargs: torch.ones_like(kwargs["activation"]) * 4,
            ),
            (
                "decoder.0.hook_attn_in",
                lambda **kwargs: torch.ones_like(kwargs["activation"]) * 6,
            ),
            (
                "decoder.0.hook_cross_attn_in",
                lambda **kwargs: torch.ones_like(kwargs["activation"]) * 8,
            ),
            (
                "decoder.0.cross_attn.hook_q",
                lambda **kwargs: torch.ones_like(kwargs["activation"]) * 7,
            ),
            (
                "encoder.0.hook_mlp_in",
                lambda **kwargs: torch.ones_like(kwargs["activation"]) * 3,
            ),
            (
                "decoder.0.hook_mlp_in",
                lambda **kwargs: torch.ones_like(kwargs["activation"]) * 5,
            ),
        ],
    )

    assert torch.all(patched["encoder_attn_in"] == 0)
    assert not torch.equal(patched["encoder_q"], patched["encoder_k"])
    assert torch.all(patched["decoder_attn_in"] == 0)
    assert torch.any(patched["decoder_q"] != 0)
    assert torch.any(patched["decoder_k"] != 0)
    assert torch.any(patched["decoder_v"] != 0)
    assert not torch.equal(patched["decoder_q"], patched["decoder_k"])
    assert not torch.equal(patched["decoder_k"], patched["decoder_v"])
    assert torch.all(patched["cross_q"] == 7)
    assert torch.all(patched["cross_attn_in"] == 8)
    assert torch.all(patched["encoder_mlp_in"] == 3)
    assert torch.all(patched["decoder_mlp_in"] == 5)


def test_t5_default_cache_names_exclude_prefixed_attention_scores() -> None:
    model = _FakeWeightedT5Model()
    adapter = architecture_adapter_for_model(model, model_name="google-t5/t5-small")

    names = _candidate_hook_names(model, adapter, for_cache=True)
    default_names = _default_cache_hook_names(model, adapter)

    assert "encoder.0.attn.hook_q" in names
    assert "encoder.0.attn.hook_q" in default_names
    assert "encoder.0.hook_q_input" in names
    assert "encoder.0.hook_q_input" not in default_names
    assert "encoder.0.hook_attn_in" in names
    assert "encoder.0.hook_attn_in" not in default_names
    assert "encoder.0.hook_mlp_in" in names
    assert "encoder.0.hook_mlp_in" not in default_names
    assert "decoder.0.hook_q_input" in names
    assert "decoder.0.hook_q_input" not in default_names
    assert "decoder.0.hook_cross_attn_in" in names
    assert "decoder.0.hook_cross_attn_in" not in default_names
    assert "decoder.0.hook_mlp_in" in names
    assert "decoder.0.hook_mlp_in" not in default_names
    assert "blocks.0.attn.hook_q" not in default_names
    assert "decoder.0.attn.hook_attn_scores" in names
    assert "decoder.0.cross_attn.hook_attn_scores" in names
    assert "decoder.0.attn.hook_attn_scores" not in default_names
    assert "decoder.0.cross_attn.hook_attn_scores" not in default_names
    assert "decoder.0.attn.hook_pattern" in default_names
    assert "decoder.0.cross_attn.hook_pattern" in default_names


def test_t5_hook_candidates_use_decoder_layer_count_when_asymmetric() -> None:
    model = _FakeAsymmetricT5Model()
    adapter = architecture_adapter_for_model(model, model_name="google-t5/t5-small")

    names = _candidate_hook_names(model, adapter, for_cache=True)
    default_names = _default_cache_hook_names(model, adapter)

    assert "encoder.1.attn.hook_q" not in default_names
    assert "decoder.1.attn.hook_q" in names
    assert "decoder.1.cross_attn.hook_q" in names
    assert "decoder.1.cross_attn.hook_q" in default_names


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
        "mamba_ssm",
        "mamba2_ssm",
    }.issubset(adapter_names)
    assert len(adapter_names) >= 10
    assert "result" not in supported_transformer_component_names()
    assert "result" in supported_transformer_component_names(include_attention=True)
    assert "cross_result" not in supported_transformer_component_names()
    assert "cross_result" not in supported_transformer_component_names(include_pattern=True)
    assert "cross_result" in supported_transformer_component_names(include_attention=True)
    assert "attn_scores" not in supported_transformer_component_names()
    assert "cross_attn_scores" not in supported_transformer_component_names()
    assert "pattern" in supported_transformer_component_names(include_pattern=True)
    assert "cross_pattern" in supported_transformer_component_names(include_pattern=True)
    assert "attn_scores" in supported_transformer_component_names(include_attention=True)
    assert "cross_attn_scores" in supported_transformer_component_names(include_attention=True)


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


def test_architecture_adapter_result_hook_preserves_structured_list_output() -> None:
    model = _FakeListWeightedQwenModel()
    attention = model.model.layers[0].self_attn
    adapter = architecture_adapter_for_model(model, model_name="Qwen/Qwen3-8B")
    z = [[[0.0, 1.0, 2.0, 3.0]]]

    def append_metadata_output(output: Any) -> list[Any]:
        return [output, {"present": True}]

    attention.o_proj.register_forward_hook(
        lambda _module, _inputs, output: append_metadata_output(output)
    )

    def zero_first_head(**kwargs: Any) -> Any:
        patched = [[list(pos_heads) for pos_heads in batch] for batch in kwargs["activation"]]
        for batch in patched:
            for pos_heads in batch:
                pos_heads[0] = [0.0 for _value in pos_heads[0]]
        return patched

    spec = adapter._spec_for_ref(_require_component_ref(adapter, "layer_0.result"), for_cache=False)
    original_output = append_metadata_output(z)
    original_result = compute_attention_result_activation(
        z,
        model,
        spec,
        module=attention.o_proj,
        component_ref=adapter.parse_component_ref("layer_0.result"),
        architecture=adapter.name,
    )
    patched_result = zero_first_head(activation=original_result)
    expected_hidden = apply_attention_result_patch(z, original_result, patched_result)
    adapter.register_component_hook(model, "layer_0.result", zero_first_head)

    output = attention.project(z)

    assert output == [expected_hidden, original_output[1]]


def test_bert_architecture_adapter_supports_automodel_paths() -> None:
    model = _FakeBertModel()
    adapter = architecture_adapter_for_model(model, model_name="google-bert/bert-base-uncased")

    assert {"pre", "pre_linear", "post"} <= set(adapter.supported_components())
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
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_pre_linear",
        lambda **kwargs: kwargs["activation"] + ["pre_linear"],
    )
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_post",
        lambda **kwargs: kwargs["activation"] + ["post"],
    )

    layer: Any = model.encoder.layer[0]
    assert layer.attention.self.query.run_forward(["x"]) == ["x", "q"]
    assert layer.attention.output.dense.run_pre(["x"]) == ["x", "z"]
    assert layer.intermediate.dense.run_forward(["x"]) == ["x", "pre_linear"]
    assert layer.output.dense.run_pre(["x"]) == ["x", "post"]


def test_distilbert_architecture_adapter_supports_encoder_paths() -> None:
    model = _FakeDistilBertModel()
    adapter = architecture_adapter_for_model(model, model_name="distilbert-base-uncased")

    assert adapter.name == "distilbert_encoder"
    assert {"pre", "pre_linear", "post"} <= set(adapter.supported_components())
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
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_pre_linear",
        lambda **kwargs: kwargs["activation"] + ["pre_linear"],
    )
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_post",
        lambda **kwargs: kwargs["activation"] + ["post"],
    )

    layer = model.transformer.layer[0]
    assert layer.attention.q_lin.run_forward(["x"]) == ["x", "q"]
    assert layer.attention.out_lin.run_pre(["x"]) == ["x", "z"]
    assert layer.ffn.lin1.run_forward(["x"]) == ["x", "pre_linear"]
    assert layer.ffn.lin2.run_pre(["x"]) == ["x", "post"]


def test_audio_architecture_adapter_supports_encoder_paths() -> None:
    model = _FakeAudioModel()
    adapter = architecture_adapter_for_model(model, model_name="facebook/wav2vec2-base")

    assert adapter.name == "audio_encoder"
    assert {"pre", "pre_linear", "post"} <= set(adapter.supported_components())
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
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_pre_linear",
        lambda **kwargs: kwargs["activation"] + ["pre_linear"],
    )
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_post",
        lambda **kwargs: kwargs["activation"] + ["post"],
    )

    layer = model.encoder.layers[0]
    assert layer.attention.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.attention.out_proj.run_pre(["x"]) == ["x", "z"]
    assert layer.feed_forward.intermediate_dense.run_forward(["x"]) == ["x", "pre_linear"]
    assert layer.feed_forward.output_dense.run_pre(["x"]) == ["x", "post"]


def test_apertus_architecture_adapter_supports_decoder_paths() -> None:
    model = _FakeApertusModel()
    adapter = architecture_adapter_for_model(model, model_name="swiss-ai/Apertus-8B-2509")

    assert adapter.name == "apertus_decoder"
    assert {"pre", "pre_linear", "post"} <= set(adapter.supported_components())
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
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_pre_linear",
        lambda **kwargs: kwargs["activation"] + ["pre_linear"],
    )
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_post",
        lambda **kwargs: kwargs["activation"] + ["post"],
    )
    adapter.register_component_hook(
        model,
        "layer_0.resid_mid",
        lambda **kwargs: kwargs["activation"] + ["mid"],
    )

    layer: Any = model.model.layers[0]
    assert layer.self_attn.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.self_attn.o_proj.run_pre(["x"]) == ["x", "z"]
    assert layer.mlp.up_proj.run_forward(["x"]) == ["x", "pre_linear"]
    assert layer.mlp.down_proj.run_pre(["x"]) == ["x", "post"]
    assert layer.feedforward_layernorm.run_pre(["x"]) == ["x", "mid"]


def test_gpt_oss_architecture_adapter_supports_attention_and_residual_paths() -> None:
    model = _FakeGptOssModel()
    adapter = architecture_adapter_for_model(model, model_name="openai/gpt-oss-20b")

    assert adapter.name == "gpt_oss_decoder"
    assert {"pre", "pre_linear", "post"} <= set(
        adapter.supported_components(include_unsupported=True)
    )
    assert {"pre", "pre_linear", "post"}.isdisjoint(adapter.supported_components())
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
    adapter.register_component_hook(
        model,
        "layer_0.mlp_out",
        lambda **kwargs: kwargs["activation"] + ["mlp_out"],
    )
    adapter.register_component_hook(
        model,
        "layer_0.resid_mid",
        lambda **kwargs: kwargs["activation"] + ["mid"],
    )

    layer: Any = model.model.layers[0]
    assert layer.self_attn.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.self_attn.o_proj.run_pre(["x"]) == ["x", "z"]
    assert layer.mlp.run_forward(["x"]) == ["x", "mlp_out"]
    assert layer.post_attention_layernorm.run_pre(["x"]) == ["x", "mid"]
    with pytest.raises(NotImplementedError, match="routed MoE experts"):
        adapter.register_component_hook(
            model,
            "blocks.0.mlp.hook_pre",
            lambda **kwargs: kwargs["activation"],
        )


def test_routed_moe_architecture_adapter_rejects_dense_mlp_internals() -> None:
    model = _FakeRoutedMoeModel()
    adapter = architecture_adapter_for_model(model, model_name="mistralai/Mixtral-8x7B-v0.1")

    assert adapter.name == "routed_moe_decoder"
    assert {"pre", "pre_linear", "post"} <= set(
        adapter.supported_components(include_unsupported=True)
    )
    assert {"pre", "pre_linear", "post"}.isdisjoint(adapter.supported_components())
    adapter.register_component_hook(
        model,
        "layer_0.q",
        lambda **kwargs: kwargs["activation"] + ["q"],
    )
    adapter.register_component_hook(
        model,
        "layer_0.mlp_out",
        lambda **kwargs: kwargs["activation"] + ["mlp_out"],
    )
    adapter.register_component_hook(
        model,
        "layer_0.resid_mid",
        lambda **kwargs: kwargs["activation"] + ["mid"],
    )

    layer = model.model.layers[0]
    assert layer.self_attn.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.mlp.run_forward(["x"]) == ["x", "mlp_out"]
    assert layer.post_attention_layernorm.run_pre(["x"]) == ["x", "mid"]
    with pytest.raises(NotImplementedError, match="multiple experts"):
        adapter.register_component_hook(
            model,
            "blocks.0.mlp.hook_pre",
            lambda **kwargs: kwargs["activation"],
        )


def test_llama_like_adapter_supports_gemma3_conditional_language_model_paths() -> None:
    model = _FakeGemma3ConditionalModel()
    adapter = architecture_adapter_for_model(model, model_name="google/gemma-3-4b-it")

    assert adapter.name == "llama_like_decoder"
    adapter.register_component_hook(
        model,
        "layer_0.q",
        lambda **kwargs: kwargs["activation"] + ["q"],
    )
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_pre_linear",
        lambda **kwargs: kwargs["activation"] + ["pre_linear"],
    )
    adapter.register_component_hook(
        model,
        "blocks.0.mlp.hook_post",
        lambda **kwargs: kwargs["activation"] + ["post"],
    )
    adapter.register_component_hook(
        model,
        "layer_0.resid_mid",
        lambda **kwargs: kwargs["activation"] + ["mid"],
    )

    layer = model.model.language_model.layers[0]
    assert layer.self_attn.q_proj.run_forward(["x"]) == ["x", "q"]
    assert layer.mlp.up_proj.run_forward(["x"]) == ["x", "pre_linear"]
    assert layer.mlp.down_proj.run_pre(["x"]) == ["x", "post"]
    assert layer.post_attention_layernorm.run_pre(["x"]) == ["x", "mid"]


def test_transformer_lens_hook_candidates_use_nested_text_config_layer_count() -> None:
    model = type(
        "_NestedConfigOnlyModel",
        (),
        {
            "config": type(
                "_NestedConfigOnlyConfig",
                (),
                {
                    "model_type": "vision_text_wrapper",
                    "text_config": type(
                        "_NestedTextConfig",
                        (),
                        {
                            "model_type": "gemma3",
                            "num_hidden_layers": 2,
                        },
                    )(),
                },
            )(),
        },
    )()
    adapter = architecture_adapter_for_model(model, model_name="./models/custom-gemma3")

    names = _candidate_hook_names(model, adapter, for_cache=True)

    assert adapter.name == "llama_like_decoder"
    assert "blocks.0.attn.hook_q" in names
    assert "blocks.1.attn.hook_q" in names


def test_transformer_lens_hook_candidates_use_dict_nested_text_config() -> None:
    model = type(
        "_DictNestedConfigOnlyModel",
        (),
        {
            "config": {
                "model_type": "vision_text_wrapper",
                "text_config": {
                    "model_type": "gemma3",
                    "num_hidden_layers": 2,
                },
            },
        },
    )()
    adapter = architecture_adapter_for_model(model, model_name="./models/custom-gemma3")

    names = _candidate_hook_names(model, adapter, for_cache=True)

    assert adapter.name == "llama_like_decoder"
    assert "blocks.0.attn.hook_q" in names
    assert "blocks.1.attn.hook_q" in names


def test_transformer_lens_cfg_and_head_helpers_use_dict_nested_text_config() -> None:
    model = type(
        "_DictNestedShapeConfigModel",
        (),
        {
            "config": {
                "model_type": "vision_text_wrapper",
                "text_config": {
                    "model_type": "gemma3",
                    "num_hidden_layers": 2,
                    "num_attention_heads": 4,
                    "num_key_value_heads": 2,
                    "hidden_size": 16,
                    "head_dim": 4,
                    "vocab_size": 128,
                    "max_position_embeddings": 64,
                    "intermediate_size": 32,
                    "hidden_act": "gelu",
                    "parallel_attn_mlp": True,
                },
            },
        },
    )()
    wrapper = TransformerLensCompatibleModelWrapper(name="./models/custom-gemma3")
    wrapper.model = model

    cfg = wrapper.cfg

    assert cfg.model_type == "gemma3"
    assert cfg.n_layers == 2
    assert cfg.n_heads == 4
    assert cfg.n_key_value_heads == 2
    assert cfg.d_model == 16
    assert cfg.d_head == 4
    assert cfg.d_vocab == 128
    assert cfg.n_ctx == 64
    assert cfg.d_mlp == 32
    assert cfg.act_fn == "gelu"
    assert cfg.normalization_type == "RMS"
    assert cfg.parallel_attn_mlp is True
    assert attention_head_count(model) == 4
    assert key_value_head_count(model) == 2
    assert attention_head_dim(model) == 4


def test_mpt_architecture_adapter_uses_down_proj_for_mlp_out() -> None:
    model = _FakeMptModel()
    adapter = architecture_adapter_for_model(model, model_name="mosaicml/mpt-7b")

    assert adapter.name == "mpt_decoder"
    adapter.register_component_hook(
        model,
        "layer_0.mlp_out",
        lambda **kwargs: kwargs["activation"] + ["mlp_out"],
    )

    layer = model.transformer.blocks[0]
    assert layer.ffn.run_forward(["residual_added_output"]) == ["residual_added_output"]
    assert layer.ffn.down_proj.run_forward(["pure_mlp_output"]) == [
        "pure_mlp_output",
        "mlp_out",
    ]


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
    assert architecture_adapter_for_name(model_name="ai-forever/mGPT").name == "gpt2_decoder"
    assert (
        architecture_adapter_for_name(model_name="roneneldan/TinyStories-33M").name
        == "gpt_neo_decoder"
    )
    assert (
        architecture_adapter_for_name(model_name="swiss-ai/Apertus-8B-2509").name
        == "apertus_decoder"
    )
    assert architecture_adapter_for_name(model_name="openai/gpt-oss-20b").name == "gpt_oss_decoder"
    assert (
        architecture_adapter_for_name(model_name="bigcode/santacoder").name == "gpt_bigcode_decoder"
    )
    assert architecture_adapter_for_name(model_name="facebook/opt-125m").name == "opt_decoder"


@pytest.mark.parametrize(
    "model_type, expected_adapter",
    [
        ("qwen3_moe", "routed_moe_decoder"),
        ("qwen2_moe", "routed_moe_decoder"),
        ("qwen3_5_moe", "routed_moe_decoder"),
        ("qwen3_5_moe_text", "routed_moe_decoder"),
        ("qwen3_omni_moe_text", "routed_moe_decoder"),
        ("qwen3_vl_moe_text", "routed_moe_decoder"),
        ("gemma3_text", "llama_like_decoder"),
        ("gemma3n_text", "llama_like_decoder"),
        ("gemma4_text", "llama_like_decoder"),
        ("qwen2_vl_text", "llama_like_decoder"),
        ("qwen2_5_vl_text", "llama_like_decoder"),
        ("qwen3_vl_text", "llama_like_decoder"),
        ("qwen3_5", "llama_like_decoder"),
        ("qwen3_5_text", "llama_like_decoder"),
        ("olmo3", "llama_like_decoder"),
    ],
)
def test_architecture_adapter_uses_exact_model_type_for_local_transformer_variants(
    model_type: str,
    expected_adapter: str,
) -> None:
    assert (
        architecture_adapter_for_name(
            model_name="./models/custom-transformerlens-target",
            model_type=model_type,
        ).name
        == expected_adapter
    )


@pytest.mark.parametrize(
    "model_name, expected_adapter",
    [
        ("neo", "gpt_neo_decoder"),
        ("neox", "gpt_neox_decoder"),
        ("opt", "opt_decoder"),
        ("mamba-130m", "mamba_ssm"),
        ("mamba-codestral", "mamba2_ssm"),
        ("w2v2-large", "audio_encoder"),
        ("yi-34b", "llama_like_decoder"),
        ("Qwen/Qwen2-57B-A14B", "routed_moe_decoder"),
        ("qwen3-30b-a3b", "routed_moe_decoder"),
        ("Qwen/Qwen3-235B-A22B", "routed_moe_decoder"),
    ],
)
def test_architecture_adapter_resolves_transformerlens_aliases_before_selection(
    model_name: str,
    expected_adapter: str,
) -> None:
    assert architecture_adapter_for_name(model_name=model_name).name == expected_adapter


def test_official_transformer_lens_model_names_use_specific_adapters_when_known() -> None:
    generic_names = [
        name
        for name in transformer_lens_official_model_names()
        if architecture_adapter_for_name(model_name=name).name == "generic_decoder"
    ]

    assert generic_names
    assert all(is_transformer_lens_native_checkpoint(name) for name in generic_names)
    assert "ai-forever/mGPT" not in generic_names
    assert not any("TinyStories" in name for name in generic_names)
    assert not any("Apertus" in name for name in generic_names)
    assert "openai/gpt-oss-20b" not in generic_names


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
    assert torch.equal(
        output["logits"], wrapper.model.transformer.ln_f(expected_embed + expected_pos)
    )


def test_transformer_lens_compatible_wrapper_caches_final_ln_scale_hook() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["ln_final.hook_scale"],
        return_cache_object=True,
    )

    resid = wrapper.model.transformer.wte(torch.tensor([[1, 2]])) + wrapper.model.transformer.wpe(
        torch.tensor([[0, 1]])
    )
    expected_scale = torch.sqrt(
        (resid - resid.mean(dim=-1, keepdim=True)).pow(2).mean(dim=-1, keepdim=True)
        + wrapper.model.transformer.ln_f.eps
    )

    assert isinstance(cache, ActivationCache)
    assert torch.allclose(cache["ln_final.hook_scale"], expected_scale)
    assert torch.allclose(output["logits"], wrapper.model.transformer.ln_f(resid))

    _sliced_output, sliced_cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["ln_final.hook_scale"],
        return_cache_object=True,
        remove_batch_dim=True,
        pos_slice=1,
    )
    assert isinstance(sliced_cache, ActivationCache)

    assert not sliced_cache.has_batch_dim
    assert sliced_cache["ln_final.hook_scale"].shape == (1, 1)
    assert torch.allclose(sliced_cache["ln_final.hook_scale"], expected_scale[0, [1]])


def test_transformer_lens_compatible_wrapper_prefers_decoder_final_norm_for_seq2seq() -> None:
    torch = pytest.importorskip("torch")

    class _Seq2SeqNormModel:
        def __init__(self) -> None:
            self.norm = _FakeModule()
            self.decoder: Any = type("Decoder", (), {"final_layer_norm": _FakeModule()})()

        def __call__(self, **_kwargs: Any) -> dict[str, Any]:
            encoder_resid = torch.tensor([[[1.0, 3.0], [5.0, 7.0]]])
            decoder_resid = torch.tensor([[[2.0, 6.0], [10.0, 18.0]]])
            self.norm(encoder_resid)
            self.decoder.final_layer_norm(decoder_resid)
            return {"logits": decoder_resid}

    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.model = _Seq2SeqNormModel()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]], "decoder_input_ids": [[0, 4]]},
        layers=["ln_final.hook_scale"],
        return_cache_object=True,
    )

    expected_decoder_scale = torch.sqrt(torch.tensor([[[4.0], [16.0]]]) + 1e-5)
    assert torch.allclose(cache["ln_final.hook_scale"], expected_decoder_scale)


def test_transformer_lens_compatible_wrapper_caches_layer_norm_scale_and_normalized_hooks() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=[
            "blocks.0.ln1.hook_scale",
            "blocks.0.ln1.hook_normalized",
            "blocks.0.ln2.hook_scale",
            "blocks.0.ln2.hook_normalized",
        ],
        return_cache_object=True,
    )

    resid_pre = output["resid_pre"]
    resid_mid = output["resid_mid"]
    ln1 = wrapper.model.transformer.h[0].ln_1
    ln2 = wrapper.model.transformer.h[0].ln_2
    expected_ln1_scale = torch.sqrt(
        (resid_pre - resid_pre.mean(dim=-1, keepdim=True)).pow(2).mean(dim=-1, keepdim=True)
        + ln1.eps
    )
    expected_ln2_scale = torch.sqrt(
        (resid_mid - resid_mid.mean(dim=-1, keepdim=True)).pow(2).mean(dim=-1, keepdim=True)
        + ln2.eps
    )

    assert torch.allclose(cache["blocks.0.ln1.hook_scale"], expected_ln1_scale)
    assert torch.allclose(cache["blocks.0.ln2.hook_scale"], expected_ln2_scale)
    assert torch.allclose(
        cache["blocks.0.ln1.hook_normalized"],
        (resid_pre - resid_pre.mean(dim=-1, keepdim=True)) / expected_ln1_scale,
    )
    assert torch.allclose(
        cache["blocks.0.ln2.hook_normalized"],
        (resid_mid - resid_mid.mean(dim=-1, keepdim=True)) / expected_ln2_scale,
    )


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
    assert torch.equal(
        output["logits"], wrapper.model.transformer.ln_f(expected_embed + expected_pos)
    )
    assert seen == [("hook_embed", 0)]
    assert wrapper.model.transformer.wte.forward_hooks == []
    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_callable_filters_with_no_matches_are_noops() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[(lambda _name: False, lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert output == {"q": ["q"]}
    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_patches_final_ln_scale_hook() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    seen: list[tuple[str, tuple[int, ...]]] = []

    def double_scale(activation: Any, hook: Any) -> Any:
        seen.append((hook.name, tuple(activation.shape)))
        return activation * 2

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("ln_final.hook_scale", double_scale)],
        return_type="model_output",
    )

    resid = wrapper.model.transformer.wte(torch.tensor([[1, 2]])) + wrapper.model.transformer.wpe(
        torch.tensor([[0, 1]])
    )
    expected = wrapper.model.transformer.ln_f(resid) / 2

    assert seen == [("ln_final.hook_scale", (1, 2, 1))]
    assert torch.allclose(output["logits"], expected)
    assert wrapper.model.transformer.ln_f._forward_hooks == {}
    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_patches_layer_norm_scale_hook() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    seen: list[tuple[str, tuple[int, ...]]] = []

    def double_scale(activation: Any, hook: Any) -> Any:
        seen.append((hook.name, tuple(activation.shape)))
        return activation * 2

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.ln1.hook_scale", double_scale)],
        return_type="model_output",
    )

    resid_pre = output["resid_pre"]
    ln1 = wrapper.model.transformer.h[0].ln_1
    original_norm = ln1(resid_pre)

    assert seen == [("blocks.0.ln1.hook_scale", (1, 2, 1))]
    assert torch.allclose(output["attn_input"], original_norm / 2)
    assert ln1._forward_pre_hooks == {}
    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_patches_layer_norm_normalized_hook() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.ln1.hook_normalized", lambda activation, _hook: activation * 0)],
        return_type="model_output",
    )

    assert torch.equal(output["attn_input"], torch.zeros_like(output["attn_input"]))


def test_transformer_lens_compatible_top_level_hook_propagates_internal_type_errors() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()

    def broken(value: Any, point: Any) -> Any:
        _ = value, point
        raise TypeError("top level hook inner bug")

    with pytest.raises(TypeError, match="top level hook inner bug"):
        wrapper.run_with_hooks(
            {"input_ids": [[1, 2]]},
            fwd_hooks=[("embed", broken)],
            return_type="model_output",
        )

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
    assert torch.equal(output["input_ids"], torch.tensor([[3, 4]]))
    assert output["q"] == ["q", "patched"]

    tuple_output = wrapper(
        {"input_ids": ((5, 6),), "attention_mask": ((1, 0),)},
        return_type="model_output",
    )

    assert torch.equal(tuple_output["input_ids"], torch.tensor([[5, 6]]))


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


def test_transformer_lens_compatible_wrapper_supports_detect_head_workflow() -> None:
    torch = pytest.importorskip("torch")

    class _TokenCacheQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            tokens = kwargs["input_ids"]
            scores = torch.full((tokens.shape[-1], tokens.shape[-1]), -20.0)
            scores[0, 0] = 20.0
            scores[1:, :-1] = torch.where(
                get_previous_token_head_detection_pattern(tokens)[1:, :-1] > 0,
                torch.tensor(20.0),
                scores[1:, :-1],
            )
            self.model.layers[0].self_attn.forward(scores.unsqueeze(0).unsqueeze(0))
            return {"logits": tokens}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _TokenCacheQwenModel()

    scores = detect_head(
        wrapper,
        torch.tensor([1, 2, 3]),
        "previous_token_head",
        heads=[(0, 0)],
        exclude_current_token=True,
    )

    assert tuple(scores.shape) == (1, 2)
    assert scores[0, 0] > 0.999
    assert scores[0, 1] == -1


def test_transformer_lens_compatible_wrapper_mapping_inputs_keep_legacy_empty_cache_default() -> (
    None
):
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


def test_transformer_lens_compatible_wrapper_accepts_external_cache_dict() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    external_cache: dict[str, Any] = {}

    cache = wrapper.add_caching_hooks(
        layers=["blocks.0.attn.hook_q"],
        cache=external_cache,
    )
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache.cache_dict is external_cache
    assert external_cache == {"blocks.0.attn.hook_q": ["q"]}
    assert cache[("q", 0)] == ["q"]

    wrapper.reset_hooks(including_permanent=True)


def test_transformer_lens_compatible_wrapper_cache_some_accepts_external_cache_dict() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    external_cache: dict[str, Any] = {}

    cache = wrapper.cache_some("blocks.0.attn.hook_q", cache=external_cache)
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache.cache_dict is external_cache
    assert external_cache == {"blocks.0.attn.hook_q": ["q"]}
    wrapper.reset_hooks(including_permanent=True)


def test_transformer_lens_compatible_wrapper_accepts_positional_cache_all_dict() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    external_cache: dict[str, Any] = {}

    cache = wrapper.cache_all(external_cache)
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache.cache_dict is external_cache
    assert "blocks.0.attn.hook_pattern" in external_cache
    assert cache[("pattern", 0)].ndim == 4
    wrapper.reset_hooks(including_permanent=True)


def test_transformer_lens_compatible_wrapper_accepts_positional_cache_some_dict() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    external_cache: dict[str, Any] = {}

    cache = wrapper.cache_some(external_cache, lambda name: name.endswith(".hook_q"))
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache.cache_dict is external_cache
    assert external_cache == {"blocks.0.attn.hook_q": ["q"]}
    wrapper.reset_hooks(including_permanent=True)


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


def test_transformer_lens_compatible_wrapper_is_caching_tracks_cache_lifecycle() -> None:
    class _StateAwareQwenModel(_FakeQwenModel):
        def __init__(self, owner: TransformerLensCompatibleModelWrapper) -> None:
            super().__init__()
            self.owner = owner
            self.seen_states: list[bool] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.seen_states.append(self.owner.is_caching)
            return super().__call__(**kwargs)

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _StateAwareQwenModel(wrapper)

    assert wrapper.is_caching is False
    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_q"],
    )

    assert wrapper.model.seen_states == [True]
    assert cache == {"blocks.0.attn.hook_q": ["q"]}
    assert wrapper.is_caching is False

    persistent_cache = wrapper.add_caching_hooks(layers=["blocks.0.attn.hook_q"])
    assert wrapper.is_caching is True
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")
    assert persistent_cache[("q", 0)] == ["q"]

    wrapper.reset_hooks(including_permanent=True)
    assert wrapper.is_caching is False


def test_transformer_lens_compatible_wrapper_run_with_cache_preserves_persistent_cache_state() -> (
    None
):
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    persistent_cache = wrapper.cache_some("blocks.0.attn.hook_q")
    assert wrapper.is_caching is True

    _output, temporary_cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_q"],
    )

    assert temporary_cache == {"blocks.0.attn.hook_q": ["q"]}
    assert persistent_cache[("q", 0)] == ["q"]
    assert wrapper.is_caching is True

    wrapper.reset_hooks(including_permanent=True)
    assert wrapper.is_caching is False


def test_transformer_lens_compatible_wrapper_permanent_non_cache_hook_does_not_mark_caching() -> (
    None
):
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_perma_hook("blocks.0.attn.hook_q", lambda activation, _hook: activation)

    assert wrapper.is_caching is False
    _output, temporary_cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_q"],
    )

    assert temporary_cache == {"blocks.0.attn.hook_q": ["q"]}
    assert wrapper.is_caching is False

    wrapper.reset_hooks(including_permanent=True)


def test_transformer_lens_compatible_wrapper_add_caching_hooks_rolls_back_on_invalid_layer() -> (
    None
):
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
    assert (
        wrapper({"input_ids": [[1, 2]], "return_loss": True}, return_type="logits") == "logit-value"
    )
    assert wrapper({"input_ids": [[1, 2]], "return_loss": True}, return_type="loss") == "loss-value"
    assert wrapper({"input_ids": [[1, 2]], "return_loss": True}, return_type=None) is None


def test_transformer_lens_compatible_wrapper_forward_alias_accepts_tl_kwargs() -> None:
    torch = pytest.importorskip("torch")

    class _EchoInputModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            return {"logits": kwargs["input_ids"]}

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _EchoInputModel()

    logits = wrapper.forward("ab", prepend_bos=False, padding_side="left")

    assert torch.equal(logits, torch.tensor([[97, 98]]))
    assert "prepend_bos" not in wrapper.model.calls[0]
    with pytest.raises(AssertionError, match="residual stream"):
        wrapper.forward(torch.tensor([[1, 2]]), start_at_layer=1)


def test_wrapper_forward_stop_at_layer_zero_returns_embedding_residual() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    wrapper.tokenizer = _TinyTextTokenizer()

    tokens = torch.tensor([[1, 2]])
    expected = wrapper.model.transformer.wte(tokens) + wrapper.model.transformer.wpe(
        torch.tensor([[0, 1]])
    )

    assert torch.equal(wrapper.forward(tokens, stop_at_layer=0), expected)
    assert torch.equal(
        wrapper.forward("ab", prepend_bos=False, stop_at_layer=0),
        expected,
    )


def test_transformer_lens_compatible_wrapper_call_accepts_partial_forward_kwargs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    wrapper.tokenizer = _TinyTextTokenizer()

    expected = wrapper.model.transformer.wte(
        torch.tensor([[1, 2]])
    ) + wrapper.model.transformer.wpe(torch.tensor([[0, 1]]))

    output = wrapper("ab", prepend_bos=False, stop_at_layer=0, truncate=False)

    assert torch.equal(output, expected)


def test_transformer_lens_compatible_wrapper_forward_runs_partial_layer_slice() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()

    tokens = torch.tensor([[1, 2]])
    embedded = wrapper.model.transformer.wte(tokens) + wrapper.model.transformer.wpe(
        torch.tensor([[0, 1]])
    )

    assert torch.equal(wrapper.forward(tokens, stop_at_layer=1), embedded + 10.0)

    residual_from_layer_one = torch.ones(1, 2, 6)
    assert torch.equal(
        wrapper.forward(residual_from_layer_one, start_at_layer=1, stop_at_layer=2),
        residual_from_layer_one + 100.0,
    )

    expected_residual = embedded + 110.0
    expected_logits = wrapper.model.lm_head(wrapper.model.transformer.ln_f(expected_residual))
    assert torch.allclose(wrapper.forward(tokens), wrapper.model(input_ids=tokens)["logits"])
    assert torch.allclose(
        wrapper.forward(embedded, start_at_layer=0, tokens=tokens),
        expected_logits,
    )

    logits, loss = wrapper.forward(
        embedded,
        start_at_layer=0,
        tokens=tokens,
        return_type="both",
    )
    assert torch.allclose(logits, expected_logits)
    assert torch.allclose(loss, wrapper.loss_fn(expected_logits, tokens))


def test_transformer_lens_compatible_wrapper_forward_uses_past_kv_cache() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache.init_cache(wrapper.cfg, device="cpu", batch_size=1)

    logits = wrapper.forward(torch.tensor([[1, 2]]), past_kv_cache=cache)

    assert logits.shape == (1, 2, 6)
    assert cache[0].keys is not None
    assert cache[1].values is not None
    cache0_keys = cache[0].keys
    cache1_values = cache[1].values
    assert cache0_keys is not None
    assert cache1_values is not None
    cache0_keys_tensor = torch.as_tensor(cache0_keys)
    cache1_values_tensor = torch.as_tensor(cache1_values)
    assert cache0_keys_tensor.shape == (1, 2, 2, 3)
    assert cache[0].past_keys is cache0_keys
    assert cache1_values_tensor.shape == (1, 2, 2, 3)
    assert torch.equal(cache0_keys_tensor[:, :, 0, :], torch.full((1, 2, 3), 10.0))
    assert torch.equal(cache1_values_tensor[:, -1, :, :], torch.full((1, 2, 3), -100.0))

    wrapper.forward(torch.tensor([[3]]), past_kv_cache=cache)

    assert cache[0].sequence_length == 3
    assert wrapper.model.transformer.h[0].calls[-1]["use_cache"] is True
    assert wrapper.model.transformer.h[0].calls[-1]["past_key_values"] is not None


def test_transformer_lens_compatible_wrapper_forward_preserves_cached_attention_mask() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache.init_cache(wrapper.cfg, device="cpu", batch_size=1)

    wrapper.forward(
        torch.tensor([[9, 1]]),
        attention_mask=torch.tensor([[0, 1]]),
        past_kv_cache=cache,
    )
    wrapper.forward(
        torch.tensor([[2]]),
        attention_mask=torch.tensor([[1]]),
        past_kv_cache=cache,
    )

    assert torch.equal(cache.previous_attention_mask, torch.tensor([[0, 1, 1]]))
    assert torch.equal(wrapper.model.calls[-1]["attention_mask"], torch.tensor([[0, 1, 1]]))


def test_transformer_lens_compatible_wrapper_partial_forward_updates_past_kv_cache() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache()

    residual = wrapper.forward(torch.tensor([[1, 2]]), stop_at_layer=1, past_kv_cache=cache)

    assert residual.shape == (1, 2, 6)
    assert cache[0].sequence_length == 2
    assert cache[0].keys is not None
    assert cache[0].keys.shape == (1, 2, 2, 3)
    assert wrapper.model.transformer.h[0].calls[-1]["past_key_values"] is not None


def test_transformer_lens_compatible_wrapper_partial_forward_slices_cached_position_ids() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache()

    wrapper.forward(torch.tensor([[1, 2]]), stop_at_layer=1, past_kv_cache=cache)
    wrapper.forward(torch.tensor([[3]]), stop_at_layer=1, past_kv_cache=cache)

    call = wrapper.model.transformer.h[0].calls[-1]
    assert torch.equal(call["attention_mask"], torch.tensor([[1, 1, 1]]))
    assert torch.equal(call["position_ids"], torch.tensor([[2]]))
    assert torch.equal(call["cache_position"], torch.tensor([2]))


def test_wrapper_forward_accepts_sparse_cache_after_partial_prefix() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache()

    wrapper.forward(torch.tensor([[1, 2]]), stop_at_layer=1, past_kv_cache=cache)
    loss = wrapper.forward(
        torch.tensor([[3, 4]]),
        past_kv_cache=cache,
        return_type="loss",
    )

    assert loss.ndim == 0
    assert torch.isfinite(loss)


def test_transformer_lens_compatible_wrapper_partial_forward_slices_cached_loss_mask() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache()
    cache[0].past_keys = torch.zeros(1, 2, 2, 3)
    cache[0].past_values = torch.zeros(1, 2, 2, 3)
    cache.previous_attention_mask = torch.tensor([[1, 1]])
    tokens = torch.tensor([[3, 4]])
    residual, _returned_tokens, _shortformer, attention_mask = wrapper.input_to_embed(
        tokens,
        past_kv_cache=cache,
    )

    loss = wrapper.forward(
        residual,
        start_at_layer=0,
        tokens=tokens,
        attention_mask=attention_mask,
        past_kv_cache=cache,
        return_type="loss",
    )

    assert loss.ndim == 0
    assert torch.isfinite(loss)


def test_transformer_lens_cache_bridge_preserves_sparse_layer_indices() -> None:
    torch = pytest.importorskip("torch")
    cache = KeyValueCache()
    cache[1].past_keys = torch.ones(1, 2, 2, 3)
    cache[1].past_values = torch.full((1, 2, 2, 3), 2.0)

    model_cache, _sync_back = _past_kv_cache_to_transformers_cache(cache)
    assert model_cache is not None

    assert len(model_cache.layers) == 2
    assert model_cache.layers[0].keys is None
    assert torch.equal(model_cache.layers[1].keys, torch.ones(1, 2, 2, 3).transpose(1, 2))


def test_transformer_lens_cache_bridge_respects_frozen_prefix_cache() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache.init_cache(wrapper.cfg, device="cpu", batch_size=1)

    wrapper.forward(torch.tensor([[1, 2]]), past_kv_cache=cache)
    assert cache[0].past_keys is not None
    assert cache[0].past_values is not None
    assert cache.previous_attention_mask is not None
    original_keys = cache[0].past_keys.clone()
    original_values = cache[0].past_values.clone()
    original_mask = cache.previous_attention_mask.clone()

    cache.freeze()
    wrapper.forward(torch.tensor([[3]]), past_kv_cache=cache)

    assert cache[0].sequence_length == 2
    assert torch.equal(cache[0].past_keys, original_keys)
    assert torch.equal(cache[0].past_values, original_values)
    assert torch.equal(cache.previous_attention_mask, original_mask)


def test_transformer_lens_cache_bridge_respects_frozen_sparse_entry() -> None:
    torch = pytest.importorskip("torch")
    cache = KeyValueCache()
    cache[0].past_keys = torch.ones(1, 2, 2, 3)
    cache[0].past_values = torch.full((1, 2, 2, 3), 2.0)
    cache[1].past_keys = torch.full((1, 2, 2, 3), 3.0)
    cache[1].past_values = torch.full((1, 2, 2, 3), 4.0)
    cache[1].frozen = True

    model_cache, sync_back = _past_kv_cache_to_transformers_cache(cache)
    assert model_cache is not None
    model_cache.update(torch.full((1, 2, 1, 3), 5.0), torch.full((1, 2, 1, 3), 6.0), 0)
    model_cache.update(torch.full((1, 2, 1, 3), 7.0), torch.full((1, 2, 1, 3), 8.0), 1)
    sync_back()

    assert cache[0].past_keys is not None
    assert cache[1].past_keys is not None
    assert cache[1].past_values is not None
    assert cache[0].past_keys.shape == (1, 3, 2, 3)
    assert torch.equal(cache[0].past_keys[:, -1], torch.full((1, 2, 3), 5.0))
    assert cache[1].past_keys.shape == (1, 2, 2, 3)
    assert torch.equal(cache[1].past_keys, torch.full((1, 2, 2, 3), 3.0))
    assert torch.equal(cache[1].past_values, torch.full((1, 2, 2, 3), 4.0))


def test_transformer_lens_compatible_run_with_cache_accepts_partial_forward_kwargs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()

    residual, cache = wrapper.run_with_cache(
        torch.tensor([[1, 2]]),
        layers=["hook_embed"],
        stop_at_layer=0,
    )

    assert torch.equal(
        residual, cache["hook_embed"] + wrapper.model.transformer.wpe(torch.tensor([[0, 1]]))
    )


def test_transformer_lens_compatible_run_with_hooks_accepts_partial_forward_kwargs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    residual = torch.zeros(1, 2, 6)

    output = wrapper.run_with_hooks(
        residual,
        start_at_layer=1,
        stop_at_layer=2,
        fwd_hooks=[
            (
                1,
                lambda _module, _inputs, activation: activation + 1.0,
            )
        ],
    )

    assert torch.equal(output, residual + 101.0)


def test_transformer_lens_compatible_run_with_hooks_partial_forward_keeps_backward_hooks() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _CallableGpt2Model()
    wrapper.tokenizer = _TinyTextTokenizer()
    residual = torch.zeros(1, 2, 6, requires_grad=True)

    loss = wrapper.run_with_hooks(
        residual,
        start_at_layer=1,
        stop_at_layer=2,
        return_type="logits",
        fwd_hooks=[(1, lambda _module, _inputs, activation: activation.sum())],
        bwd_hooks=[(1, lambda grad, _hook: grad * 3.0)],
    )
    loss.backward()

    assert torch.equal(residual.grad, torch.full_like(residual, 3.0))


def test_transformer_lens_compatible_wrapper_run_with_hooks_supports_backward_hooks() -> None:
    torch = pytest.importorskip("torch")

    class _DifferentiableLayer(_FakeModule):
        def __call__(self, value: Any, **kwargs: Any) -> Any:
            _ = kwargs
            return self.run_forward(value * 2, inputs=(value,))

    class _DifferentiableBackbone:
        def __init__(self) -> None:
            self.layers = [_DifferentiableLayer()]

    class _DifferentiableConfig(_FakeConfig):
        num_hidden_layers = 1
        hidden_size = 2
        num_attention_heads = 1

    class _DifferentiableModel:
        def __init__(self) -> None:
            self.config = _DifferentiableConfig()
            self.model = _DifferentiableBackbone()

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            x = kwargs["inputs_embeds"]
            resid = self.model.layers[0](x)
            return {"logits": resid.sum()}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _DifferentiableModel()
    x = torch.ones(1, 1, 2, requires_grad=True)
    seen_grads: list[Any] = []

    def scale_grad(grad: Any, hook: Any) -> Any:
        seen_grads.append((grad.detach().clone(), hook.name))
        return grad * 3

    loss = wrapper.run_with_hooks(
        {"inputs_embeds": x},
        bwd_hooks=[
            (
                "blocks.0.hook_resid_post",
                scale_grad,
            )
        ],
        return_type="logits",
    )
    loss.backward()

    assert seen_grads
    assert seen_grads[0][1] == "blocks.0.hook_resid_post"
    assert torch.equal(seen_grads[0][0], torch.ones(1, 1, 2))
    assert torch.equal(x.grad, torch.full_like(x, 6.0))


def test_transformer_lens_compatible_wrapper_hooks_context_supports_backward_hooks() -> None:
    torch = pytest.importorskip("torch")

    class _DifferentiableLayer(_FakeModule):
        def __call__(self, value: Any, **kwargs: Any) -> Any:
            _ = kwargs
            return self.run_forward(value + 1, inputs=(value,))

    class _DifferentiableBackbone:
        def __init__(self) -> None:
            self.layers = [_DifferentiableLayer()]

    class _DifferentiableModel:
        config = _FakeConfig()

        def __init__(self) -> None:
            self.model = _DifferentiableBackbone()

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            resid = self.model.layers[0](kwargs["inputs_embeds"])
            return {"logits": resid.sum()}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _DifferentiableModel()
    x = torch.ones(1, 1, 4, requires_grad=True)

    with wrapper.hooks(bwd_hooks=[("blocks.0.hook_resid_post", lambda grad, _hook: grad * 2)]):
        loss = wrapper({"inputs_embeds": x})
        loss.backward()

    assert torch.equal(x.grad, torch.full_like(x, 2.0))
    assert wrapper._hooks == []


def test_transformer_lens_compatible_run_with_cache_incl_bwd_caches_gradients() -> None:
    torch = pytest.importorskip("torch")

    class _DifferentiableLayer(_FakeModule):
        def __call__(self, value: Any, **kwargs: Any) -> Any:
            _ = kwargs
            return self.run_forward(value * 2, inputs=(value,))

    class _DifferentiableBackbone:
        def __init__(self) -> None:
            self.layers = [_DifferentiableLayer()]

    class _DifferentiableModel:
        config = _FakeConfig()

        def __init__(self) -> None:
            self.model = _DifferentiableBackbone()

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            resid = self.model.layers[0](kwargs["inputs_embeds"])
            return {"logits": resid.sum()}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _DifferentiableModel()
    x = torch.ones(1, 1, 4, requires_grad=True)

    output, cache = wrapper.run_with_cache(
        {"inputs_embeds": x},
        layers=["blocks.0.hook_resid_post"],
        return_type="logits",
        return_cache_object=True,
        incl_bwd=True,
    )

    assert torch.equal(output.detach(), torch.tensor(8.0))
    assert isinstance(cache, ActivationCache)
    assert torch.equal(cache["blocks.0.hook_resid_post"], torch.full_like(x, 2.0))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.ones_like(x))
    assert torch.equal(x.grad, torch.full_like(x, 2.0))
    assert wrapper._hooks == []


def test_transformer_lens_compatible_add_caching_hooks_incl_bwd_caches_gradients() -> None:
    torch = pytest.importorskip("torch")

    class _DifferentiableLayer(_FakeModule):
        def __call__(self, value: Any, **kwargs: Any) -> Any:
            _ = kwargs
            return self.run_forward(value + 1, inputs=(value,))

    class _DifferentiableBackbone:
        def __init__(self) -> None:
            self.layers = [_DifferentiableLayer()]

    class _DifferentiableModel:
        config = _FakeConfig()

        def __init__(self) -> None:
            self.model = _DifferentiableBackbone()

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            resid = self.model.layers[0](kwargs["inputs_embeds"])
            return {"logits": resid.sum()}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _DifferentiableModel()
    cache = wrapper.add_caching_hooks(
        layers=["blocks.0.hook_resid_post"],
        incl_bwd=True,
    )
    x = torch.ones(1, 1, 4, requires_grad=True)

    loss = wrapper({"inputs_embeds": x})
    loss.backward()

    assert torch.equal(cache["blocks.0.hook_resid_post"], torch.full_like(x, 2.0))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.ones_like(x))
    assert torch.equal(x.grad, torch.ones_like(x))

    wrapper.reset_hooks(including_permanent=True)
    assert wrapper._hooks == []


def test_transformer_lens_compatible_reset_hooks_filters_by_direction() -> None:
    torch = pytest.importorskip("torch")

    class _DifferentiableLayer(_FakeModule):
        def __call__(self, value: Any, **kwargs: Any) -> Any:
            _ = kwargs
            return self.run_forward(value + 1, inputs=(value,))

    class _DifferentiableBackbone:
        def __init__(self) -> None:
            self.layers = [_DifferentiableLayer()]

    class _DifferentiableModel:
        config = _FakeConfig()

        def __init__(self) -> None:
            self.model = _DifferentiableBackbone()

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            resid = self.model.layers[0](kwargs["inputs_embeds"])
            return {"logits": resid.sum(), "resid": resid}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _DifferentiableModel()
    wrapper.add_hook(
        "blocks.0.hook_resid_post",
        lambda activation, _hook: activation + 2,
        is_permanent=True,
    )
    wrapper.add_hook(
        "blocks.0.hook_resid_post",
        lambda grad, _hook: grad * 3,
        dir="bwd",
        is_permanent=True,
    )

    wrapper.reset_hooks(direction="fwd", including_permanent=True)
    x = torch.ones(1, 1, 4, requires_grad=True)
    loss = wrapper({"inputs_embeds": x})
    loss.backward()

    assert torch.equal(x.grad, torch.full_like(x, 3.0))

    wrapper.reset_hooks(dir="bwd", including_permanent=True)
    x = torch.ones(1, 1, 4, requires_grad=True)
    output = wrapper({"inputs_embeds": x}, return_type="model_output")

    assert torch.equal(output["resid"], torch.full_like(x, 2.0))
    assert x.grad is None
    assert wrapper._hooks == []


def test_transformer_lens_compatible_reset_hooks_rejects_invalid_direction() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    with pytest.raises(ValueError, match="Invalid hook direction"):
        wrapper.reset_hooks(direction="sideways")


def test_transformer_lens_compatible_run_with_cache_incl_bwd_requires_scalar_output() -> None:
    torch = pytest.importorskip("torch")

    class _VectorLogitsModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            x = kwargs["inputs_embeds"]
            resid = self.model.layers[0].run_forward(x)
            return {"logits": resid}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _VectorLogitsModel()
    x = torch.ones(1, 1, 4, requires_grad=True)

    with pytest.raises(ValueError, match="scalar"):
        wrapper.run_with_cache(
            {"inputs_embeds": x},
            layers=["blocks.0.hook_resid_post"],
            return_type="logits",
            incl_bwd=True,
        )

    assert wrapper._hooks == []


def test_transformer_lens_compatible_wrapper_low_level_embed_helpers_match_transformerlens() -> (
    None
):
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    wrapper.tokenizer = _TinyTextTokenizer()

    assert wrapper.get_pos_offset(None, batch_size=2) == 0

    class _CacheEntry:
        past_keys = torch.zeros(2, 3, 2, 3)

    assert wrapper.get_pos_offset([_CacheEntry()], batch_size=2) == 3

    tokens = torch.tensor([[1, 2]])
    expected_embed = wrapper.model.transformer.wte(tokens)
    expected_pos = wrapper.model.transformer.wpe(torch.tensor([[0, 1]]))
    expected_resid = expected_embed + expected_pos

    residual, returned_tokens, shortformer_pos_embed, attention_mask = wrapper.input_to_embed(
        tokens
    )

    assert torch.equal(returned_tokens, tokens)
    assert shortformer_pos_embed is None
    assert attention_mask is None
    assert torch.equal(residual, expected_resid)

    text_residual, text_tokens, text_shortformer, text_mask = wrapper.input_to_embed(
        "ab",
        prepend_bos=False,
    )

    assert torch.equal(text_tokens, torch.tensor([[1, 2]]))
    assert text_shortformer is None
    assert text_mask is None
    assert torch.equal(
        text_residual,
        wrapper.model.transformer.wte(text_tokens)
        + wrapper.model.transformer.wpe(torch.tensor([[0, 1]])),
    )

    left_tokens = wrapper.to_tokens(["a", "bc"], prepend_bos=False, padding_side="left")
    _left_resid, _left_tokens, _left_shortformer, left_mask = wrapper.input_to_embed(
        ["a", "bc"],
        prepend_bos=False,
        padding_side="left",
    )

    assert torch.equal(_left_tokens, left_tokens)
    assert _left_shortformer is None
    assert torch.equal(left_mask, torch.tensor([[0, 1], [1, 1]]))
    assert torch.equal(
        wrapper.get_residual(expected_embed, 0, tokens=tokens, return_shortformer_pos_embed=False),
        expected_resid,
    )


def test_transformer_lens_compatible_wrapper_uses_kv_cache_sequence_axis_for_position_offset() -> (
    None
):
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    wrapper.tokenizer = _TinyTextTokenizer()
    cache = KeyValueCache()
    cache[0].past_keys = torch.zeros(1, 5, 2, 3)
    cache[0].past_values = torch.zeros(1, 5, 2, 3)

    assert wrapper.get_pos_offset(cache, batch_size=1) == 5


def test_transformer_lens_compatible_wrapper_weight_processing_boundaries() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()

    assert wrapper.fold_layer_norm() is wrapper
    assert wrapper.center_writing_weights() is wrapper
    assert wrapper.fold_value_biases() is wrapper
    with pytest.raises(NotImplementedError, match="W_Q/W_K or W_V/W_O"):
        wrapper.refactor_factored_attn_matrices()
    assert wrapper.process_weights_(center_unembed=False) is wrapper
    with pytest.raises(NotImplementedError, match="initialize"):
        wrapper.init_weights()
    with pytest.raises(NotImplementedError, match="state dictionaries"):
        wrapper.load_and_process_state_dict({})
    with pytest.raises(NotImplementedError, match="state dictionaries"):
        wrapper.fill_missing_keys({})

    wrapper.load_sample_training_dataset()
    assert wrapper.dataset == []
    with pytest.raises(ValueError, match="No sample training dataset"):
        wrapper.sample_datapoint()
    wrapper.dataset = ["row"]
    assert wrapper.sample_datapoint() == "row"


def test_transformer_lens_compatible_wrapper_from_pretrained_loads_wrapper(
    monkeypatch: Any,
) -> None:
    created: list[TransformerLensCompatibleModelWrapper] = []
    process_calls: list[dict[str, Any]] = []

    def fake_load_model(self: TransformerLensCompatibleModelWrapper) -> Any:
        created.append(self)
        self.model = _FakeQwenModel()
        self._process_loaded_weights()
        return self.model

    def fake_process_weights(
        self: TransformerLensCompatibleModelWrapper,
        **kwargs: Any,
    ) -> TransformerLensCompatibleModelWrapper:
        process_calls.append(kwargs)
        return self

    monkeypatch.setattr(TransformerLensCompatibleModelWrapper, "load_model", fake_load_model)
    monkeypatch.setattr(
        TransformerLensCompatibleModelWrapper,
        "process_weights_",
        fake_process_weights,
    )

    wrapper = TransformerLensCompatibleModelWrapper.from_pretrained(
        "gpt2",
        dtype="float16",
        device="cpu",
        fold_ln=False,
        center_unembed=False,
        output_hidden_states=True,
    )

    assert wrapper is created[0]
    assert wrapper.name == "gpt2"
    assert wrapper.dtype == "float16"
    assert wrapper.device == "cpu"
    assert wrapper.load_kwargs == {"output_hidden_states": True}
    assert process_calls == [
        {
            "fold_ln": False,
            "center_writing_weights": True,
            "center_unembed": False,
            "fold_value_biases": True,
            "refactor_factored_attn_matrices": False,
        }
    ]


def test_transformer_lens_compatible_wrapper_from_pretrained_no_processing_disables_passes(
    monkeypatch: Any,
) -> None:
    process_calls: list[dict[str, Any]] = []

    def fake_load_model(self: TransformerLensCompatibleModelWrapper) -> Any:
        self.model = _FakeQwenModel()
        self._process_loaded_weights()
        return self.model

    def fake_process_weights(
        self: TransformerLensCompatibleModelWrapper,
        **kwargs: Any,
    ) -> TransformerLensCompatibleModelWrapper:
        process_calls.append(kwargs)
        return self

    monkeypatch.setattr(TransformerLensCompatibleModelWrapper, "load_model", fake_load_model)
    monkeypatch.setattr(
        TransformerLensCompatibleModelWrapper,
        "process_weights_",
        fake_process_weights,
    )

    wrapper = TransformerLensCompatibleModelWrapper.from_pretrained_no_processing(
        "gpt2",
        output_hidden_states=True,
    )

    assert wrapper.load_kwargs == {"output_hidden_states": True}
    assert process_calls == [
        {
            "fold_ln": False,
            "center_writing_weights": False,
            "center_unembed": False,
            "fold_value_biases": False,
            "refactor_factored_attn_matrices": False,
        }
    ]


def test_transformer_lens_compatible_wrapper_from_pretrained_skips_encoder_unembed(
    monkeypatch: Any,
) -> None:
    def fake_load_model(self: TransformerLensCompatibleModelWrapper) -> Any:
        self.model = _FakeWeightedBertModel()
        self._process_loaded_weights()
        return self.model

    monkeypatch.setattr(TransformerLensCompatibleModelWrapper, "load_model", fake_load_model)

    wrapper = TransformerLensCompatibleModelWrapper.from_pretrained(
        "bert-base-uncased",
        output_attentions=True,
    )

    assert isinstance(wrapper.model, _FakeWeightedBertModel)
    assert wrapper.load_kwargs == {"output_attentions": True}


def test_transformer_lens_compatible_wrapper_load_model_processes_weights_once(
    monkeypatch: Any,
) -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(
        name="Qwen/Qwen3-8B",
        process_weights_kwargs={
            "fold_ln": False,
            "center_writing_weights": True,
            "center_unembed": False,
            "fold_value_biases": True,
            "refactor_factored_attn_matrices": False,
        },
    )

    def fake_supported(self: TransformerLensCompatibleModelWrapper) -> bool:
        return True

    def fake_resolve(self: TransformerLensCompatibleModelWrapper) -> str:
        return "Qwen/Qwen3-8B"

    def fake_raise(self: TransformerLensCompatibleModelWrapper, pretrained_path: str) -> None:
        assert pretrained_path == "Qwen/Qwen3-8B"

    class _FakeTokenizer:
        @classmethod
        def from_pretrained(cls, *_args: Any, **_kwargs: Any) -> Any:
            return cls()

    def fake_from_pretrained(cls: Any, *_args: Any, **_kwargs: Any) -> Any:
        model = _FakeWeightedQwenModel()
        return model

    monkeypatch.setattr(
        TransformerLensCompatibleModelWrapper,
        "_is_supported_transformer_lens_target",
        fake_supported,
    )
    monkeypatch.setattr(
        TransformerLensCompatibleModelWrapper, "_resolve_pretrained_path", fake_resolve
    )
    monkeypatch.setattr(
        TransformerLensCompatibleModelWrapper,
        "_raise_if_native_transformer_lens_checkpoint",
        fake_raise,
    )
    monkeypatch.setattr(
        TransformerLensCompatibleModelWrapper,
        "_transformer_lens_model_kind",
        lambda self, **_kwargs: "decoder",
    )
    monkeypatch.setattr(
        TransformerLensCompatibleModelWrapper,
        "_load_text_tokenizer",
        lambda self, _cls, _path, _kwargs: _FakeTokenizer(),
    )
    transformers = pytest.importorskip("transformers")
    monkeypatch.setattr(
        transformers.AutoModelForCausalLM,
        "from_pretrained",
        classmethod(fake_from_pretrained),
    )

    model = wrapper.load_model()
    second_model = wrapper.load_model()

    assert model is not second_model
    assert torch.equal(
        model.model.embed_tokens.weight, torch.arange(20, dtype=torch.float32).reshape(5, 4)
    )
    assert torch.equal(
        second_model.model.embed_tokens.weight, torch.arange(20, dtype=torch.float32).reshape(5, 4)
    )
    assert torch.equal(model.model.layers[0].self_attn.v_proj.bias, torch.zeros(4))
    assert torch.equal(second_model.model.layers[0].self_attn.v_proj.bias, torch.zeros(4))
    assert wrapper._weights_processed is True


def test_transformer_lens_compatible_wrapper_call_uses_tokenization_kwargs_for_text() -> None:
    torch = pytest.importorskip("torch")

    class _EchoInputModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            return {"logits": kwargs["input_ids"]}

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _EchoInputModel()

    logits = wrapper("ab", prepend_bos=False, padding_side="left", truncate=False)

    assert torch.equal(
        logits, wrapper.to_tokens("ab", prepend_bos=False, padding_side="left", truncate=False)
    )
    call = wrapper.model.calls[0]
    assert "prepend_bos" not in call
    assert "padding_side" not in call
    assert "truncate" not in call


def test_transformer_lens_compatible_wrapper_call_tokenizes_tuple_text_batches() -> None:
    torch = pytest.importorskip("torch")

    class _EchoInputModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            return {"logits": kwargs["input_ids"]}

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _EchoInputModel()

    logits = wrapper(("a", "bc"), prepend_bos=False, padding_side="left")

    assert torch.equal(
        logits, wrapper.to_tokens(("a", "bc"), prepend_bos=False, padding_side="left")
    )
    assert torch.equal(wrapper.model.calls[0]["attention_mask"], torch.tensor([[0, 1], [1, 1]]))


def test_transformer_lens_compatible_wrapper_run_with_cache_uses_tokenization_kwargs_for_text() -> (
    None
):
    torch = pytest.importorskip("torch")

    class _EchoInputModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            return {"logits": kwargs["input_ids"]}

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _EchoInputModel()

    logits, _cache = wrapper.run_with_cache(
        {"text": "ab", "prepend_bos": False, "padding_side": "left", "truncate": False},
        return_type="logits",
    )

    assert torch.equal(
        logits, wrapper.to_tokens("ab", prepend_bos=False, padding_side="left", truncate=False)
    )
    call = wrapper.model.calls[0]
    assert "prepend_bos" not in call
    assert "padding_side" not in call
    assert "truncate" not in call


def test_transformer_lens_compatible_wrapper_run_with_hooks_uses_tokenization_kwargs_for_text() -> (
    None
):
    torch = pytest.importorskip("torch")

    class _EchoInputModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            return {"logits": kwargs["input_ids"]}

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _EchoInputModel()

    logits = wrapper.run_with_hooks(
        {"text": "ab", "prepend_bos": False, "padding_side": "left", "truncate": False},
        return_type="logits",
    )

    assert torch.equal(
        logits,
        wrapper.to_tokens("ab", prepend_bos=False, padding_side="left", truncate=False),
    )
    call = wrapper.model.calls[0]
    assert "prepend_bos" not in call
    assert "padding_side" not in call
    assert "truncate" not in call


def test_transformer_lens_compatible_run_with_hooks_text_kwargs_default_to_logits() -> None:
    torch = pytest.importorskip("torch")

    class _EchoInputModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            return {"logits": kwargs["input_ids"]}

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _EchoInputModel()

    logits = wrapper.run_with_hooks(
        "ab",
        prepend_bos=False,
        padding_side="left",
        truncate=False,
    )

    assert torch.equal(
        logits,
        wrapper.to_tokens("ab", prepend_bos=False, padding_side="left", truncate=False),
    )
    assert "prepend_bos" not in wrapper.model.calls[0]


def test_transformer_lens_compatible_wrapper_computes_lm_loss_from_logits() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            logits = torch.tensor(
                [
                    [
                        [0.0, 3.0, 0.0],
                        [0.0, 0.0, 3.0],
                        [3.0, 0.0, 0.0],
                    ]
                ],
                dtype=torch.float32,
            )
            return {"logits": logits}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwenModel()

    loss = wrapper(torch.tensor([0, 1, 2]), return_type="loss")
    per_token_loss = wrapper(
        torch.tensor([0, 1, 2]),
        return_type="loss",
        loss_per_token=True,
    )
    expected = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]),
        torch.tensor([1, 2]),
    )
    expected_per_token = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]),
        torch.tensor([1, 2]),
        reduction="none",
    ).unsqueeze(0)

    assert torch.allclose(loss, expected)
    assert torch.allclose(per_token_loss, expected_per_token)
    assert "loss_per_token" not in wrapper.model.calls[-1]


def test_transformer_lens_compatible_wrapper_loss_fn_matches_forward_loss() -> None:
    torch = pytest.importorskip("torch")

    logits = torch.tensor(
        [
            [
                [0.0, 3.0, 0.0],
                [0.0, 0.0, 3.0],
                [3.0, 0.0, 0.0],
            ]
        ],
        dtype=torch.float32,
    )
    tokens = torch.tensor([[0, 1, 2]])

    class _LogitsOnlyQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            return {"logits": logits}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwenModel()

    expected = wrapper(tokens, return_type="loss")
    expected_per_token = wrapper(tokens, return_type="loss", loss_per_token=True)

    assert torch.allclose(wrapper.loss_fn(logits, tokens), expected)
    assert torch.allclose(wrapper.loss_fn(logits, tokens, per_token=True), expected_per_token)


def test_transformer_lens_compatible_wrapper_loss_fn_masks_padding_transitions() -> None:
    torch = pytest.importorskip("torch")

    logits = torch.tensor(
        [
            [
                [4.0, 0.0, 0.0],
                [0.0, 4.0, 0.0],
                [0.0, 0.0, 4.0],
            ]
        ],
        dtype=torch.float32,
    )
    tokens = torch.tensor([[0, 1, 2]])
    attention_mask = torch.tensor([[0, 1, 1]])
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")

    expected_valid_loss = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 4.0, 0.0]]),
        torch.tensor([2]),
    )

    assert torch.allclose(
        wrapper.loss_fn(logits, tokens, attention_mask),
        expected_valid_loss,
    )
    assert torch.allclose(
        wrapper.loss_fn(logits, tokens, attention_mask, per_token=True),
        torch.tensor([[0.0, expected_valid_loss.item()]]),
    )


def test_transformer_lens_compatible_wrapper_loss_fn_accepts_python_lists() -> None:
    logits = [
        [
            [0.0, 3.0, 0.0],
            [0.0, 0.0, 3.0],
            [3.0, 0.0, 0.0],
        ]
    ]
    tokens = [[0, 1, 2]]
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")

    assert wrapper.loss_fn(logits, tokens) == lm_cross_entropy_loss(logits, tokens)
    assert wrapper.loss_fn(logits, tokens, per_token=True) == lm_cross_entropy_loss(
        logits,
        tokens,
        per_token=True,
    )


def test_transformer_lens_compatible_wrapper_both_returns_logits_and_computed_loss() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            logits = torch.tensor(
                [
                    [
                        [0.0, 3.0, 0.0],
                        [0.0, 0.0, 3.0],
                        [3.0, 0.0, 0.0],
                    ]
                ],
                dtype=torch.float32,
            )
            return {"logits": logits}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwenModel()

    logits, loss = wrapper(
        {"input_ids": [[0, 1, 2]], "attention_mask": [[1, 1, 0]]},
        return_type="both",
    )
    _logits, per_token_loss = wrapper(
        {"input_ids": [[0, 1, 2]], "attention_mask": [[1, 1, 0]]},
        return_type="both",
        loss_per_token=True,
    )
    expected = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 3.0, 0.0]]),
        torch.tensor([1]),
    )
    expected_per_token = torch.tensor([[expected.item(), 0.0]])

    assert torch.equal(logits, wrapper.model()["logits"])
    assert torch.allclose(loss, expected)
    assert torch.allclose(per_token_loss, expected_per_token)


def test_transformer_lens_compatible_wrapper_tensorizes_tuple_token_model_inputs() -> None:
    torch = pytest.importorskip("torch")

    class _StrictTensorQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            assert isinstance(kwargs["input_ids"], torch.Tensor)
            assert isinstance(kwargs["attention_mask"], torch.Tensor)
            logits = torch.nn.functional.one_hot(kwargs["input_ids"], num_classes=3).to(
                torch.float32
            )
            return {"logits": logits}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _StrictTensorQwenModel()

    per_token_loss = wrapper(
        {"input_ids": ((0, 1, 2),), "attention_mask": ((1, 1, 0),)},
        return_type="loss",
        loss_per_token=True,
    )

    assert isinstance(per_token_loss, torch.Tensor)
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[0, 1, 2]]))
    assert torch.equal(wrapper.model.calls[0]["attention_mask"], torch.tensor([[1, 1, 0]]))


def test_transformer_lens_compatible_wrapper_loss_masks_left_padding_transitions() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            logits = torch.tensor(
                [
                    [
                        [4.0, 0.0, 0.0],
                        [0.0, 4.0, 0.0],
                        [0.0, 0.0, 4.0],
                    ]
                ],
                dtype=torch.float32,
            )
            return {"logits": logits}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwenModel()

    per_token_loss = wrapper(
        {"input_ids": [[0, 1, 2]], "attention_mask": [[0, 1, 1]]},
        return_type="loss",
        loss_per_token=True,
    )
    loss = wrapper(
        {"input_ids": [[0, 1, 2]], "attention_mask": [[0, 1, 1]]},
        return_type="loss",
    )
    expected_valid_loss = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 4.0, 0.0]]),
        torch.tensor([2]),
    )

    assert torch.allclose(per_token_loss, torch.tensor([[0.0, expected_valid_loss.item()]]))
    assert torch.allclose(loss, expected_valid_loss)


def test_transformer_lens_compatible_run_with_hooks_supports_per_token_loss() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(kwargs)
            logits = torch.tensor(
                [
                    [
                        [0.0, 3.0, 0.0],
                        [0.0, 0.0, 3.0],
                        [3.0, 0.0, 0.0],
                    ]
                ],
                dtype=torch.float32,
            )
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            return {"logits": logits, "q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwenModel()

    per_token_loss = wrapper.run_with_hooks(
        {"input_ids": [[0, 1, 2]], "attention_mask": [[1, 1, 0]]},
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"])],
        return_type="loss",
        loss_per_token=True,
    )

    expected = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 3.0, 0.0]]),
        torch.tensor([1]),
    )
    assert torch.allclose(per_token_loss, torch.tensor([[expected.item(), 0.0]]))
    assert "loss_per_token" not in wrapper.model.calls[-1]
    assert wrapper.model.model.layers[0].self_attn.q_proj.run_forward(["q"]) == ["q"]


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


def test_transformer_lens_compatible_wrapper_names_filter_accepts_component_shorthands() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    for names_filter in ("q", "hook_q"):
        output, cache = wrapper.run_with_cache(
            {"input_ids": [[1, 2]]},
            names_filter=names_filter,
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


def test_transformer_lens_compatible_run_with_cache_reset_false_keeps_cache_hooks() -> None:
    class _KwargRecordingQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[dict[str, Any]] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.calls.append(dict(kwargs))
            return super().__call__(**kwargs)

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _KwargRecordingQwenModel()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter="blocks.0.attn.hook_q",
        reset_hooks_end=False,
        clear_contexts=True,
    )

    assert cache == {"blocks.0.attn.hook_q": ["q"]}
    assert "reset_hooks_end" not in wrapper.model.calls[0]
    assert "clear_contexts" not in wrapper.model.calls[0]
    assert wrapper.is_caching is True
    assert wrapper._hooks

    _next_output, next_cache = wrapper.run_with_cache({"input_ids": [[1, 2]]})

    assert next_cache == {}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}

    wrapper.reset_hooks()

    assert wrapper.is_caching is False
    assert wrapper._hooks == []


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


def test_transformer_lens_compatible_wrapper_cache_layers_accept_tuple_component_refs() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=[("q", 0)],
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
            activation = torch.arange(24, dtype=torch.float32).reshape(1, 3, 4, 2)
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
    assert tuple(cached.shape) == (1, 1, 4, 2)
    expected = torch.arange(24, dtype=torch.float32).reshape(1, 3, 4, 2)[:, [1]]
    assert torch.equal(cached.tensor, expected)
    assert cached.requires_grad is False
    assert moved_devices == ["cpu"]


def test_transformer_lens_compatible_wrapper_int_pos_slice_preserves_position_dimension() -> None:
    class _PosSliceQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            q_out = self.model.layers[0].self_attn.q_proj.run_forward([[["q0"], ["q1"], ["q2"]]])
            return {"q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _PosSliceQwenModel()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2, 3]]},
        layers=["blocks.0.attn.hook_q"],
        pos_slice=1,
        remove_batch_dim=True,
        return_cache_object=True,
    )

    assert cache["blocks.0.attn.hook_q"] == [["q1"]]


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


def test_transformer_lens_compatible_run_with_hooks_accepts_forward_positionals() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            logits = torch.tensor(
                [
                    [
                        [0.0, 3.0, 0.0],
                        [0.0, 0.0, 3.0],
                        [3.0, 0.0, 0.0],
                    ]
                ],
                dtype=torch.float32,
            )
            return {"logits": logits, "q": q_out}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwenModel()

    per_token_loss = wrapper.run_with_hooks(
        torch.tensor([0, 1, 2]),
        "loss",
        True,
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )
    expected = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]),
        torch.tensor([1, 2]),
        reduction="none",
    ).unsqueeze(0)

    assert torch.allclose(per_token_loss, expected)
    assert wrapper.model.model.layers[0].self_attn.q_proj.run_forward(["q"]) == ["q"]


def test_transformer_lens_compatible_add_hook_accepts_callable_name_filter() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    handle = wrapper.add_hook(
        lambda name: name.endswith(".hook_q"),
        lambda **kwargs: kwargs["activation"] + ["patched"],
    )

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "patched"]}
    handle.remove()
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


def test_transformer_lens_compatible_run_with_cache_accepts_forward_positionals() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            logits = torch.tensor(
                [
                    [
                        [0.0, 3.0, 0.0],
                        [0.0, 0.0, 3.0],
                        [3.0, 0.0, 0.0],
                    ]
                ],
                dtype=torch.float32,
            )
            return {"logits": logits}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwenModel()

    per_token_loss, cache = wrapper.run_with_cache(
        torch.tensor([0, 1, 2]),
        "loss",
        True,
        names_filter=lambda _name: False,
    )
    expected = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]),
        torch.tensor([1, 2]),
        reduction="none",
    ).unsqueeze(0)

    assert torch.allclose(per_token_loss, expected)
    assert cache == {}


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


def test_run_activation_patch_with_wrapper_mapping_inputs_scores_logits() -> None:
    torch = pytest.importorskip("torch")

    class _PatchLogitsQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(
                torch.zeros(1, 2, 2, dtype=torch.float32)
            )
            return {"logits": q_out.sum(dim=-1), "raw": kwargs["input_ids"]}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _PatchLogitsQwenModel()
    clean_cache = ActivationCache(
        {"blocks.0.attn.hook_q": torch.tensor([[[[5.0], [7.0]], [[11.0], [13.0]]]])}
    )

    def metric(logits: Any) -> float:
        assert not isinstance(logits, Mapping)
        return float(logits[0, 1])

    result = run_activation_patch(
        wrapper,
        {"input_ids": [[1, 2]]},
        clean_cache,
        PatchSpec(
            layer="blocks.0.attn.hook_q",
            activation_name="blocks.0.attn.hook_q",
        ),
        metric=metric,
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
    clean_cache = ActivationCache({"blocks.0.attn.hook_q": torch.tensor([[[[5.0], [7.0]]]])})

    result = run_activation_patch(
        wrapper,
        {"input_ids": [[1]]},
        clean_cache,
        PatchSpec(
            layer="blocks.0.attn.hook_q",
            activation_name="blocks.0.attn.hook_q",
        ),
        metric=lambda logits: float(logits[0, 0]),
        layers=["blocks.0.attn.hook_q"],
    )

    assert result.metric == 12.0
    assert torch.equal(result.output, torch.tensor([[12.0]]))
    assert torch.equal(
        result.cache["blocks.0.attn.hook_q"],
        torch.tensor([[[[5.0], [7.0]]]]),
    )
    assert wrapper._hooks == []


def test_run_activation_patch_with_wrapper_layers_preserves_encoder_model_output() -> None:
    torch = pytest.importorskip("torch")

    class _PatchEncoderQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> Any:
            _ = kwargs
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(
                torch.zeros(1, 1, 2, dtype=torch.float32)
            )
            return type(
                "_EncoderOutput",
                (),
                {"last_hidden_state": q_out.sum(dim=-1)},
            )()

    wrapper = TransformerLensCompatibleModelWrapper(name="bert-base-uncased")
    wrapper.model = _PatchEncoderQwenModel()
    clean_cache = ActivationCache({"blocks.0.attn.hook_q": torch.tensor([[[[5.0], [7.0]]]])})

    result = run_activation_patch(
        wrapper,
        {"input_ids": [[1]]},
        clean_cache,
        PatchSpec(
            layer="blocks.0.attn.hook_q",
            activation_name="blocks.0.attn.hook_q",
        ),
        metric=lambda output: float(output.last_hidden_state[0, 0]),
        layers=["blocks.0.attn.hook_q"],
    )

    assert result.metric == 12.0
    assert torch.equal(result.output.last_hidden_state, torch.tensor([[12.0]]))
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


def test_transformer_lens_compatible_wrapper_run_with_hooks_accepts_tuple_component_refs() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[(("q", 0), lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert output == {"q": ["q", "patched"]}


def test_transformer_lens_compatible_run_with_hooks_reset_false_remains_resettable() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    q_proj = wrapper.model.model.layers[0].self_attn.q_proj

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["kept"])],
        reset_hooks_end=False,
    )

    assert output == {"q": ["q", "kept"]}
    assert q_proj.run_forward(["q"]) == ["q", "kept"]
    assert wrapper._hooks

    wrapper.reset_hooks()

    assert q_proj.run_forward(["q"]) == ["q"]
    assert wrapper._hooks == []


def test_transformer_lens_compatible_run_with_hooks_reset_false_keeps_contexts() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    seen_contexts: list[Any] = []

    def record_context(activation: Any, hook: Any) -> Any:
        hook.ctx["seen"] = True
        seen_contexts.append(hook.ctx)
        return activation + ["kept"]

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.attn.hook_q", record_context)],
        reset_hooks_end=False,
        clear_contexts=True,
    )

    assert output == {"q": ["q", "kept"]}
    assert seen_contexts == [{"seen": True}]
    assert wrapper._hooks
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "kept"]}
    assert seen_contexts[-1] == {"seen": True}

    wrapper.reset_hooks(clear_contexts=True, including_permanent=True)

    assert wrapper._hooks == []
    assert seen_contexts[-1] == {}


def test_transformer_lens_compatible_wrapper_add_hook_accepts_shorthand_name() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook("q0", lambda **kwargs: kwargs["activation"] + ["patched"])

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "patched"]}


def test_transformer_lens_compatible_wrapper_add_hook_accepts_official_hook_keyword() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook(
        "blocks.0.attn.hook_q",
        hook=lambda activation, _hook: activation + ["patched"],
    )

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "patched"]}


def test_transformer_lens_compatible_wrapper_add_perma_hook_accepts_official_hook_keyword() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_perma_hook(
        "blocks.0.attn.hook_q",
        hook=lambda activation, _hook: activation + ["permanent"],
    )
    wrapper.add_hook(
        "blocks.0.attn.hook_q",
        hook=lambda activation, _hook: activation + ["temporary"],
    )

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "q": ["q", "permanent", "temporary"]
    }
    wrapper.reset_hooks()
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "permanent"]}


def test_transformer_lens_compatible_wrapper_add_hook_accepts_backward_direction() -> None:
    torch = pytest.importorskip("torch")

    class _GradQwenModel(_FakeQwenModel):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(
                kwargs["x"] * 2,
                inputs=(kwargs["x"],),
            )
            return {"loss": q_out.sum()}

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _GradQwenModel()
    x = torch.tensor([[1.0, 2.0]], requires_grad=True)

    wrapper.add_hook(
        "blocks.0.attn.hook_q",
        hook=lambda grad, _hook: grad * 3,
        dir="bwd",
    )
    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]], "x": x},
        return_cache_object=True,
        incl_bwd=True,
    )

    assert torch.equal(x.grad, torch.full_like(x, 6.0))
    assert isinstance(cache, ActivationCache)


def test_transformer_lens_compatible_wrapper_run_with_hooks_accepts_prepend_argument() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"])],
        prepend=True,
    )

    assert output == {"q": ["q", "patched"]}


def test_transformer_lens_compatible_wrapper_run_with_hooks_prepends_temporary_hook() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook(
        "blocks.0.attn.hook_q",
        lambda **kwargs: kwargs["activation"] + ["permanent"],
    )
    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[
            (
                "blocks.0.attn.hook_q",
                lambda **kwargs: kwargs["activation"] + ["temporary"],
            )
        ],
        prepend=True,
    )

    assert output == {"q": ["q", "temporary", "permanent"]}
    assert wrapper.model.model.layers[0].self_attn.q_proj.run_forward(["q"]) == [
        "q",
        "permanent",
    ]


def test_transformer_lens_compatible_wrapper_add_hook_accepts_tuple_component_refs() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    wrapper.add_hook(("q", 0), lambda **kwargs: kwargs["activation"] + ["patched"])

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

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q", "permanent", "temp"]}

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


def test_transformer_lens_compatible_wrapper_hooks_accepts_official_positional_lists() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    with wrapper.hooks(
        [("blocks.0.attn.hook_q", lambda activation, _hook: activation + ["temp"])],
        [],
    ):
        output = wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]

    assert output == {"q": ["q", "temp"]}
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {"q": ["q"]}


def test_transformer_lens_compatible_run_with_hooks_clear_contexts_clears_removed_hook() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    seen_contexts: list[Any] = []

    def record_context(activation: Any, hook: Any) -> Any:
        hook.ctx["seen"] = True
        seen_contexts.append(hook.ctx)
        return activation

    wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("blocks.0.attn.hook_q", record_context)],
        clear_contexts=True,
    )

    assert seen_contexts == [{}]
    assert wrapper._hooks == []


def test_transformer_lens_compatible_hooks_clear_contexts_clears_removed_hook() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    seen_contexts: list[Any] = []

    def record_context(activation: Any, hook: Any) -> Any:
        hook.ctx["seen"] = True
        seen_contexts.append(hook.ctx)
        return activation

    with wrapper.hooks(
        fwd_hooks=[("blocks.0.attn.hook_q", record_context)],
        clear_contexts=True,
    ):
        wrapper.run_with_cache({"input_ids": [[1, 2]]})

    assert seen_contexts == [{}]
    assert wrapper._hooks == []


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


def test_transformer_lens_compatible_remove_hooks_clears_removed_permanent_contexts() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    seen_contexts: list[Any] = []

    def record_context(activation: Any, hook: Any) -> Any:
        hook.ctx["seen"] = True
        seen_contexts.append(hook.ctx)
        return activation

    wrapper.add_perma_hook("blocks.0.attn.hook_q", record_context)
    wrapper.run_with_cache({"input_ids": [[1, 2]]})

    wrapper.remove_hooks()

    assert seen_contexts == [{}]
    assert wrapper._hooks == []


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


def test_transformer_lens_compatible_run_with_cache_reset_false_cleans_install_failure() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    q_proj = wrapper.model.model.layers[0].self_attn.q_proj

    with pytest.raises(KeyError):
        wrapper.run_with_cache(
            {"input_ids": [[1, 2]]},
            layers=["blocks.0.attn.hook_q", "blocks.99.attn.hook_q"],
            reset_hooks_end=False,
        )

    assert q_proj.forward_hooks == []
    assert wrapper._hooks == []
    assert wrapper.is_caching is False


def test_transformer_lens_encoder_decoder_inputs_get_decoder_start_token() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.model = _FakeT5Model()
    wrapper.tokenizer = _FakeT5Tokenizer()

    inputs = wrapper._prepare_model_inputs({"text": "translate this"})

    assert torch.equal(inputs["input_ids"], torch.tensor([[5, 6, 7]]))
    assert torch.equal(inputs["decoder_input_ids"], torch.tensor([[0]]))


def test_transformer_lens_local_wrapper_uses_loaded_config_for_input_family() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="./models/custom-local-model")
    wrapper.model = _FakeNestedTextConfigT5Model()
    wrapper.tokenizer = _FakeT5Tokenizer()

    inputs = wrapper._prepare_model_inputs({"text": "translate this"})

    assert torch.equal(inputs["input_ids"], torch.tensor([[5, 6, 7]]))
    assert torch.equal(inputs["decoder_input_ids"], torch.tensor([[0]]))


def test_transformer_lens_direct_existing_relative_local_name_is_runtime_supported(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "models" / "custom-local-model").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    wrapper = TransformerLensCompatibleModelWrapper(name="models/custom-local-model")

    assert wrapper._is_supported_transformer_lens_target() is True
    assert wrapper._resolve_pretrained_path() == "models/custom-local-model"


def test_transformer_lens_direct_existing_relative_pretrained_path_is_runtime_supported(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "models" / "custom-local-model").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    wrapper = TransformerLensCompatibleModelWrapper(
        name="custom-local-model",
        pretrained_path="models/custom-local-model",
    )

    assert wrapper._is_supported_transformer_lens_target() is True
    assert wrapper._resolve_pretrained_path() == "models/custom-local-model"


def test_wrapper_local_path_detection_preserves_remote_model_ids(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "models" / "custom-local-model").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    assert _wrapper_looks_like_local_path("models/custom-local-model")
    assert _wrapper_looks_like_local_path(r"models\\custom-local-model")
    assert not _wrapper_looks_like_local_path("org/model")


def test_transformer_lens_local_wrapper_uses_dict_loaded_config_for_input_family() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="./models/custom-local-model")
    wrapper.model = _FakeDictNestedTextConfigT5Model()
    wrapper.tokenizer = _FakeT5Tokenizer()

    inputs = wrapper._prepare_model_inputs({"text": "translate this"})

    assert torch.equal(inputs["input_ids"], torch.tensor([[5, 6, 7]]))
    assert torch.equal(inputs["decoder_input_ids"], torch.tensor([[0]]))


def test_transformer_lens_audio_alias_uses_resolved_family_for_inputs() -> None:
    torch = pytest.importorskip("torch")
    processor = _FakeAudioProcessor()
    wrapper = TransformerLensCompatibleModelWrapper(name="w2v2-large")
    wrapper.model = _FakeAudioModel()
    wrapper.tokenizer = processor

    inputs = wrapper._prepare_model_inputs(
        {
            "audio": [0.0, 0.5],
            "sampling_rate": 8000,
            "processor_kwargs": {"padding": True},
        }
    )

    assert torch.equal(inputs["input_values"], torch.tensor([[0.0, 1.0]]))
    assert processor.calls == [
        {
            "audio": [0.0, 0.5],
            "sampling_rate": 8000,
            "return_tensors": "pt",
            "kwargs": {"padding": True},
        }
    ]


def test_huggingface_wrapper_allows_tensor_inputs_when_tokenizer_is_missing() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="hf-internal-testing/tiny-random-mixtral")
    tokenizer = wrapper._load_text_tokenizer(_FailingTokenizer, "missing-tokenizer", {})

    assert tokenizer is None
    inputs = wrapper._prepare_model_inputs({"input_ids": torch.tensor([[1, 2, 3]])})
    assert torch.equal(inputs["input_ids"], torch.tensor([[1, 2, 3]]))
    inputs = wrapper._prepare_model_inputs(torch.tensor([1, 2, 3]))
    assert torch.equal(inputs["input_ids"], torch.tensor([[1, 2, 3]]))
    assert torch.equal(
        wrapper._prepare_model_inputs([1, 2, 3])["input_ids"], torch.tensor([[1, 2, 3]])
    )
    assert torch.equal(
        wrapper._prepare_model_inputs((1, 2, 3))["input_ids"], torch.tensor([[1, 2, 3]])
    )
    assert torch.equal(
        wrapper._prepare_model_inputs([])["input_ids"], torch.empty((1, 0), dtype=torch.long)
    )
    assert torch.equal(wrapper._prepare_model_inputs(7)["input_ids"], torch.tensor([[7]]))
    with pytest.raises(ValueError, match="did not load a tokenizer"):
        wrapper._prepare_model_inputs({"text": "needs tokenizer"})
    wrapper.model = _FakeQwenModel()
    with pytest.raises(RuntimeError, match="Tokenizer is not loaded"):
        wrapper.generate("needs tokenizer")


def test_transformer_lens_decoder_text_inputs_match_to_tokens_semantics() -> None:
    torch = pytest.importorskip("torch")

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()

    assert torch.equal(
        wrapper._prepare_model_inputs({"text": "ab"})["input_ids"],
        wrapper.to_tokens("ab"),
    )
    assert torch.equal(
        wrapper._prepare_model_inputs("ab")["input_ids"],
        wrapper.to_tokens("ab"),
    )
    assert torch.equal(
        wrapper._prepare_model_inputs(("a", "bc"))["input_ids"],
        wrapper.to_tokens(("a", "bc")),
    )
    assert torch.equal(
        wrapper._prepare_model_inputs({"text": "ab", "prepend_bos": False})["input_ids"],
        wrapper.to_tokens("ab", prepend_bos=False),
    )


def test_transformer_lens_decoder_accepts_empty_text_and_prompt_inputs() -> None:
    torch = pytest.importorskip("torch")

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()

    assert torch.equal(
        wrapper._prepare_model_inputs({"text": ""})["input_ids"],
        wrapper.to_tokens(""),
    )
    assert torch.equal(
        wrapper._prepare_model_inputs({"prompt": "", "prepend_bos": False})["input_ids"],
        wrapper.to_tokens("", prepend_bos=False),
    )


def test_huggingface_decoder_text_inputs_match_to_tokens_semantics() -> None:
    torch = pytest.importorskip("torch")

    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()

    assert torch.equal(
        wrapper._prepare_model_inputs({"text": "ab"})["input_ids"],
        wrapper.to_tokens("ab"),
    )


def test_huggingface_text_input_accepts_empty_string() -> None:
    torch = pytest.importorskip("torch")

    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()

    assert torch.equal(
        wrapper._prepare_model_inputs({"text": ""})["input_ids"],
        wrapper.to_tokens(""),
    )


def test_transformer_lens_decoder_text_batches_include_bos_aware_attention_mask() -> None:
    torch = pytest.importorskip("torch")

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2TokenizerWithoutPad()

    prepared = wrapper._prepare_model_inputs({"text": ["a", "bc"]})

    assert torch.equal(prepared["input_ids"], torch.tensor([[0, 97, 999], [0, 98, 99]]))
    assert torch.equal(prepared["attention_mask"], torch.tensor([[1, 1, 0], [1, 1, 1]]))
    assert wrapper.tokenizer.pad_token is None
    assert wrapper.tokenizer.pad_token_id is None


def test_transformer_lens_decoder_text_batches_mask_shared_bos_pad_left_padding() -> None:
    torch = pytest.importorskip("torch")

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    tokenizer = _TokenizerMissingDefaults()
    wrapper.set_tokenizer(tokenizer, default_padding_side="left")

    prepared = wrapper._prepare_model_inputs({"text": ["a", "bc"]})

    assert torch.equal(prepared["input_ids"], torch.tensor([[999, 999, 97], [999, 98, 99]]))
    assert torch.equal(prepared["attention_mask"], torch.tensor([[0, 1, 1], [1, 1, 1]]))


def test_huggingface_generate_uses_to_tokens_semantics() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    generated = wrapper.generate("ab", max_new_tokens=1, prepend_bos=False)

    assert generated == "ab!"
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[97, 98]]))
    assert wrapper.model.calls[0]["max_new_tokens"] == 1

    generated = wrapper.generate("ab", max_new_tokens=1)

    assert generated == "ab!"
    assert torch.equal(wrapper.model.calls[1]["input_ids"], torch.tensor([[0, 97, 98]]))

    wrapper.default_prepend_bos = False
    generated = wrapper.generate("ab", max_new_tokens=1, prepend_bos=None)

    assert generated == "ab!"
    assert torch.equal(wrapper.model.calls[2]["input_ids"], torch.tensor([[97, 98]]))


def test_huggingface_generate_left_pads_text_batches() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2TokenizerWithoutPad()
    wrapper.model = _FakeGenerateModel()

    generated = wrapper.generate(["a", "bc"], max_new_tokens=1)

    assert generated == ["a!", "bc!"]
    assert torch.equal(
        wrapper.model.calls[0]["input_ids"], torch.tensor([[999, 0, 97], [0, 98, 99]])
    )
    assert torch.equal(
        wrapper.model.calls[0]["attention_mask"], torch.tensor([[0, 1, 1], [1, 1, 1]])
    )
    assert wrapper.tokenizer.pad_token is None
    assert wrapper.tokenizer.pad_token_id is None


def test_huggingface_generate_can_return_tokens() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    output_tokens = wrapper.generate("ab", max_new_tokens=1, return_type="tokens")

    assert torch.equal(output_tokens, torch.tensor([[0, 97, 98, 33]]))


def test_huggingface_generate_can_return_embeds() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    output_embeds = wrapper.generate("ab", max_new_tokens=1, return_type="embeds")
    output_tokens = torch.tensor([[0, 97, 98, 33]])

    assert torch.equal(output_embeds, wrapper.model.get_input_embeddings().weight[output_tokens])


def test_huggingface_generate_preserves_structured_model_output() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    output = wrapper.generate(
        "ab",
        max_new_tokens=1,
        return_type="model_output",
        return_dict_in_generate=True,
        output_logits=True,
    )

    assert torch.equal(output.sequences, torch.tensor([[0, 97, 98, 33]]))
    assert len(output.logits) == 1
    assert output.logits[0].shape == (1, 3)


def test_huggingface_generate_model_output_wraps_plain_sequences() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    output = wrapper.generate("ab", max_new_tokens=1, return_type="model_output")

    assert torch.equal(output.sequences, torch.tensor([[0, 97, 98, 33]]))


def test_huggingface_generate_token_inputs_default_to_token_return() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    output_tokens = wrapper.generate(torch.tensor([97, 98]), max_new_tokens=1)

    assert torch.equal(output_tokens, torch.tensor([[97, 98, 33]]))
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[97, 98]]))


def test_huggingface_generate_tensor_return_type_alias_returns_tokens() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    wrapper.tokenizer = None

    output_tokens = wrapper.generate(
        torch.tensor([97, 98]),
        max_new_tokens=1,
        return_type="tensor",
    )

    assert torch.equal(output_tokens, torch.tensor([[97, 98, 33]]))
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[97, 98]]))


def test_huggingface_generate_tuple_token_inputs_are_tensorized() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    wrapper.tokenizer = None

    output_tokens = wrapper.generate((97, 98), max_new_tokens=1)

    assert torch.equal(output_tokens, torch.tensor([[97, 98, 33]]))
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[97, 98]]))


def test_huggingface_generate_token_inputs_include_attention_mask_when_tokenizer_available() -> (
    None
):
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2TokenizerWithoutPad()
    wrapper.model = _FakeGenerateModel()

    output_tokens = wrapper.generate(
        torch.tensor([[999, 0, 97], [0, 98, 99]]),
        max_new_tokens=1,
        padding_side="left",
    )

    assert torch.equal(output_tokens, torch.tensor([[999, 0, 97, 33], [0, 98, 99, 33]]))
    assert torch.equal(
        wrapper.model.calls[0]["attention_mask"], torch.tensor([[0, 1, 1], [1, 1, 1]])
    )


def test_huggingface_generate_accepts_transformerlens_generation_kwargs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()

    wrapper.generate(
        torch.tensor([97, 98]),
        max_new_tokens=1,
        stop_at_eos=False,
        use_past_kv_cache=False,
        freq_penalty=0.25,
        verbose=False,
    )

    call = wrapper.model.calls[0]
    assert call["eos_token_id"] is None
    assert call["use_cache"] is False
    assert call["frequency_penalty"] == 0.25
    assert "stop_at_eos" not in call
    assert "use_past_kv_cache" not in call
    assert "freq_penalty" not in call
    assert "verbose" not in call


def test_huggingface_generate_token_inputs_do_not_require_tokenizer() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    wrapper.tokenizer = None

    output_tokens = wrapper.generate(torch.tensor([97, 98]), max_new_tokens=1)

    assert torch.equal(output_tokens, torch.tensor([[97, 98, 33]]))
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[97, 98]]))


def test_huggingface_generate_token_inputs_embeds_do_not_require_tokenizer() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    wrapper.tokenizer = None

    output_embeds = wrapper.generate(
        torch.tensor([97, 98]),
        max_new_tokens=1,
        return_type="embeds",
    )
    output_tokens = torch.tensor([[97, 98, 33]])

    assert torch.equal(output_embeds, wrapper.model.get_input_embeddings().weight[output_tokens])


def test_huggingface_generate_token_inputs_str_return_requires_tokenizer() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    wrapper.tokenizer = None

    with pytest.raises(RuntimeError, match="Tokenizer is not loaded"):
        wrapper.generate(torch.tensor([97, 98]), max_new_tokens=1, return_type="str")


def test_huggingface_generate_embedding_inputs_default_to_embeds() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    input_embeds = torch.arange(6, dtype=torch.float32).reshape(1, 2, 3)

    output_embeds = wrapper.generate(input_embeds, max_new_tokens=1)

    generated_embeds = wrapper.model.get_input_embeddings().weight[torch.tensor([[33]])]
    assert torch.equal(output_embeds, torch.cat([input_embeds, generated_embeds], dim=1))
    assert torch.equal(wrapper.model.calls[0]["inputs_embeds"], input_embeds)
    assert "input_ids" not in wrapper.model.calls[0]


def test_huggingface_generate_seq2seq_embedding_inputs_return_decoder_embeds_only() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="google-t5/t5-small")
    wrapper.model = _FakeSeq2SeqGenerateModel()
    input_embeds = torch.arange(6, dtype=torch.float32).reshape(1, 2, 3)

    output_embeds = wrapper.generate(input_embeds, max_new_tokens=3)

    expected = wrapper.model.get_input_embeddings().weight[torch.tensor([[120, 121, 122]])]
    assert torch.equal(output_embeds, expected)
    assert output_embeds.shape == (1, 3, 3)
    assert torch.equal(wrapper.model.calls[0]["inputs_embeds"], input_embeds)
    assert "input_ids" not in wrapper.model.calls[0]


def test_huggingface_generate_embedding_inputs_can_return_new_tokens() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    input_embeds = torch.arange(6, dtype=torch.float32).reshape(1, 2, 3)

    output_tokens = wrapper.generate(input_embeds, max_new_tokens=1, return_type="tokens")

    assert torch.equal(output_tokens, torch.tensor([[33]]))


def test_huggingface_generate_embedding_inputs_str_return_decodes_new_tokens() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    input_embeds = torch.arange(6, dtype=torch.float32).reshape(1, 2, 3)

    output_text = wrapper.generate(input_embeds, max_new_tokens=1, return_type="str")

    assert output_text == "!"


def test_huggingface_generate_embedding_inputs_str_return_requires_tokenizer() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    input_embeds = torch.arange(6, dtype=torch.float32).reshape(1, 2, 3)

    with pytest.raises(RuntimeError, match="Tokenizer is not loaded"):
        wrapper.generate(input_embeds, max_new_tokens=1, return_type="str")


def test_huggingface_generate_rejects_integer_embedding_inputs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()

    with pytest.raises(TypeError, match="floating point"):
        wrapper.generate(torch.ones(1, 2, 3, dtype=torch.long), max_new_tokens=1)


def test_generation_helpers_accept_tuple_backed_token_containers() -> None:
    tokenizer = _TokenHelperTokenizer()

    assert _prepend_bos_token((97, 98), tokenizer) == [0, 97, 98]
    assert _prepend_bos_token(
        ((999, 97), (98, 99)),
        tokenizer,
        pad_token_id=999,
        padding_side="left",
    ) == [[999, 0, 97], [0, 98, 99]]
    torch = pytest.importorskip("torch")
    assert torch.equal(
        _prepend_bos_token(
            torch.tensor([[999, 999], [98, 99]]),
            tokenizer,
            pad_token_id=999,
            padding_side="left",
        ),
        torch.tensor([[999, 999, 0], [0, 98, 99]]),
    )
    assert _attention_mask_from_tokens(
        ((999, 0, 97), (0, 98, 99)),
        999,
        prepend_bos=True,
        padding_side="left",
        bos_token_id=0,
    ) == [[0, 1, 1], [1, 1, 1]]
    assert _append_sequence_values(((1, 2),), ((3,),)) == [[1, 2, 3]]
    assert _concat_token_chunks([((3,),), ((4,),)]) == [[3, 4]]
    assert _slice_generated_suffix(((1, 2, 3),), ((1, 2),)) == [[3]]


def test_huggingface_generate_stream_text_defaults_to_strings() -> None:
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    chunks = list(
        wrapper.generate_stream(
            "ab",
            max_new_tokens=3,
            max_tokens_per_yield=2,
            prepend_bos=False,
        )
    )

    assert chunks == ["!!", "!"]
    assert wrapper.model.calls[0]["input_ids"].tolist() == [[97, 98]]
    assert wrapper.model.calls[1]["input_ids"].tolist() == [[97, 98, 33]]
    assert wrapper.model.calls[2]["input_ids"].tolist() == [[97, 98, 33, 33]]


def test_huggingface_generate_stream_token_inputs_default_to_tensor_chunks() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()

    chunks = list(
        wrapper.generate_stream(
            torch.tensor([97, 98]),
            max_new_tokens=3,
            max_tokens_per_yield=2,
        )
    )

    assert len(chunks) == 2
    assert torch.equal(chunks[0], torch.tensor([[33, 33]]))
    assert torch.equal(chunks[1], torch.tensor([[33]]))


def test_huggingface_generate_stream_tuple_token_inputs_are_tensorized() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()

    chunks = list(
        wrapper.generate_stream(
            (97, 98),
            max_new_tokens=2,
            max_tokens_per_yield=2,
        )
    )

    assert len(chunks) == 1
    assert torch.equal(chunks[0], torch.tensor([[33, 33]]))
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[97, 98]]))
    assert torch.equal(wrapper.model.calls[1]["input_ids"], torch.tensor([[97, 98, 33]]))


def test_huggingface_generate_stream_token_inputs_extend_attention_mask() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2TokenizerWithoutPad()
    wrapper.model = _FakeGenerateModel()

    chunks = list(
        wrapper.generate_stream(
            torch.tensor([[999, 0, 97], [0, 98, 99]]),
            max_new_tokens=2,
            max_tokens_per_yield=2,
            padding_side="left",
        )
    )

    assert len(chunks) == 1
    assert torch.equal(chunks[0], torch.tensor([[33, 33], [33, 33]]))
    assert torch.equal(
        wrapper.model.calls[0]["attention_mask"], torch.tensor([[0, 1, 1], [1, 1, 1]])
    )
    assert torch.equal(
        wrapper.model.calls[1]["attention_mask"], torch.tensor([[0, 1, 1, 1], [1, 1, 1, 1]])
    )


def test_huggingface_generate_stream_token_inputs_can_return_strings() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeGenerateModel()

    chunks = list(
        wrapper.generate_stream(
            torch.tensor([97, 98]),
            max_new_tokens=2,
            max_tokens_per_yield=1,
            return_type="str",
        )
    )

    assert chunks == [["!"], ["!"]]


def test_huggingface_generate_stream_accepts_transformerlens_generation_kwargs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()

    list(
        wrapper.generate_stream(
            torch.tensor([97, 98]),
            max_new_tokens=1,
            stop_at_eos=False,
            use_past_kv_cache=False,
            freq_penalty=0.25,
            verbose=False,
        )
    )

    call = wrapper.model.calls[0]
    assert call["eos_token_id"] is None
    assert call["use_cache"] is False
    assert call["frequency_penalty"] == 0.25
    assert "stop_at_eos" not in call
    assert "use_past_kv_cache" not in call
    assert "freq_penalty" not in call
    assert "verbose" not in call


def test_huggingface_generate_stream_embedding_inputs_default_to_embeds() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()
    input_embeds = torch.arange(6, dtype=torch.float32).reshape(1, 2, 3)

    chunks = list(
        wrapper.generate_stream(
            input_embeds,
            max_new_tokens=2,
            max_tokens_per_yield=2,
        )
    )

    expected = wrapper.model.get_input_embeddings().weight[torch.tensor([[33, 33]])]
    assert len(chunks) == 1
    assert torch.equal(chunks[0], expected)
    assert wrapper.model.calls[0]["inputs_embeds"].shape == (1, 2, 3)
    assert wrapper.model.calls[1]["inputs_embeds"].shape == (1, 3, 3)


def test_huggingface_generate_stream_validates_inputs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = HuggingFaceModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()

    with pytest.raises(RuntimeError, match="Tokenizer is not loaded"):
        list(wrapper.generate_stream("ab", max_new_tokens=1))
    with pytest.raises(TypeError, match="single text string"):
        list(wrapper.generate_stream(["a", "b"], max_new_tokens=1))
    with pytest.raises(ValueError, match="max_tokens_per_yield"):
        list(wrapper.generate_stream(torch.tensor([1]), max_tokens_per_yield=0))
    with pytest.raises(ValueError, match="model_output"):
        list(wrapper.generate_stream(torch.tensor([1]), return_type="model_output"))


def test_transformer_lens_compatible_generate_stream_rejects_encoder_models() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="bert-base-uncased")
    wrapper.model = object()

    with pytest.raises(NotImplementedError, match="encoder"):
        list(wrapper.generate_stream([1], max_new_tokens=1))


def test_transformer_lens_encoder_decoder_generate_embedding_inputs_do_not_append_source() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.model = _FakeSeq2SeqGenerateModel()
    input_embeds = torch.arange(6, dtype=torch.float32).reshape(1, 2, 3)

    output_embeds = wrapper.generate(input_embeds, max_new_tokens=3)
    output_tokens = wrapper.generate(input_embeds, max_new_tokens=3, return_type="tokens")

    expected = wrapper.model.get_input_embeddings().weight[torch.tensor([[120, 121, 122]])]
    assert torch.equal(output_embeds, expected)
    assert output_embeds.shape == (1, 3, 3)
    assert torch.equal(output_tokens, torch.tensor([[120, 121, 122]]))
    assert torch.equal(wrapper.model.calls[0]["inputs_embeds"], input_embeds)
    assert torch.equal(wrapper.model.calls[1]["inputs_embeds"], input_embeds)


def test_transformer_lens_encoder_decoder_generate_stream_uses_single_seq2seq_call() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeSeq2SeqGenerateModel()

    chunks = list(
        wrapper.generate_stream(
            "ab",
            max_new_tokens=3,
            max_tokens_per_yield=2,
            prepend_bos=False,
            return_type="tokens",
        )
    )

    assert len(chunks) == 2
    assert torch.equal(chunks[0], torch.tensor([[120, 121]]))
    assert torch.equal(chunks[1], torch.tensor([[122]]))
    assert len(wrapper.model.calls) == 1
    assert torch.equal(wrapper.model.calls[0]["input_ids"], torch.tensor([[97, 98]]))


def test_transformer_lens_encoder_decoder_generate_stream_formats_text_chunks() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    wrapper.tokenizer = _PlainGpt2Tokenizer()
    wrapper.model = _FakeSeq2SeqGenerateModel()

    chunks = list(
        wrapper.generate_stream(
            "ab",
            max_new_tokens=3,
            max_tokens_per_yield=2,
            prepend_bos=False,
        )
    )

    assert chunks == ["xy", "z"]
    assert len(wrapper.model.calls) == 1


def test_transformer_lens_local_wrapper_uses_loaded_config_for_generation_family() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="./models/custom-local-model")
    wrapper.model = _FakeNestedTextConfigBertModel()

    with pytest.raises(NotImplementedError, match="encoder"):
        list(wrapper.generate_stream([1], max_new_tokens=1))


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
    assert wrapper.to_str_tokens(("a", "bc")) == [
        ["<bos>", "a"],
        ["<bos>", "b", "c"],
    ]
    assert wrapper.to_str_tokens(((0, 97), (0, 98))) == [["<bos>", "a"], ["<bos>", "b"]]
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
    assert wrapper.get_token_position(ord("b"), ((0, 97, 98),)) == 2
    assert _single_token_list(((0, 97),)) == [0, 97]
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


def test_transformer_lens_compatible_wrapper_resolves_default_prepend_bos() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()

    assert torch.equal(wrapper.to_tokens("ab", prepend_bos=None), torch.tensor([[0, 97, 98]]))
    wrapper.default_prepend_bos = False
    assert torch.equal(wrapper.to_tokens("ab", prepend_bos=None), torch.tensor([[97, 98]]))
    assert wrapper.to_str_tokens("ab", prepend_bos=None) == ["a", "b"]
    assert wrapper.get_token_position("b", "ab", prepend_bos=None) == 1
    assert torch.equal(wrapper.to_tokens("ab", prepend_bos=True), torch.tensor([[0, 97, 98]]))


def test_transformer_lens_compatible_wrapper_text_batches_use_default_prepend_bos() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTextTokenizer()
    wrapper.model = _FakeQwenModel()
    wrapper.default_prepend_bos = False

    inputs = wrapper._prepare_model_inputs({"text": "ab", "prepend_bos": None})

    assert torch.equal(inputs["input_ids"], torch.tensor([[97, 98]]))


def test_transformer_lens_compatible_wrapper_set_tokenizer_sets_defaults() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    tokenizer = _TokenizerMissingDefaults()

    wrapper.set_tokenizer(tokenizer, default_padding_side="left")

    assert wrapper.tokenizer is tokenizer
    assert tokenizer.padding_side == "left"
    assert tokenizer.pad_token == "<eos>"
    assert tokenizer.bos_token == "<eos>"
    assert tokenizer.pad_token_id == 999
    assert tokenizer.bos_token_id == 999
    assert wrapper.tokenizer_prepends_bos is False
    with pytest.raises(AssertionError, match="padding_side"):
        wrapper.set_tokenizer(tokenizer, default_padding_side="middle")


def test_transformer_lens_compatible_wrapper_device_dtype_helpers_return_self() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGenerateModel()

    assert wrapper.to("float16") is wrapper
    assert wrapper.dtype == "float16"
    assert wrapper.cpu() is wrapper
    assert wrapper.device == "cpu"
    assert wrapper.cuda(0) is wrapper
    assert wrapper.device == "cuda:0"
    assert wrapper.mps() is wrapper
    assert wrapper.device == "mps"
    assert wrapper.move_model_modules_to_device() is wrapper


def test_transformer_lens_compatible_wrapper_counts_total_parameters() -> None:
    torch = pytest.importorskip("torch")

    class _ParameterModel:
        def __init__(self) -> None:
            self.config = _FakeGpt2Config()
            self.params = [
                torch.zeros(2, 3),
                torch.zeros(4),
            ]

        def parameters(self) -> Any:
            return iter(self.params)

        def named_parameters(self) -> Any:
            return iter([("a", self.params[0]), ("b", self.params[1])])

    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _ParameterModel()

    assert wrapper.n_params_total == 10
    assert list(wrapper.named_parameters())[0][0] == "a"


def test_transformer_lens_compatible_wrapper_to_tokens_left_padding_keeps_bos_after_pads() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.tokenizer = _FakeTokenizerWithoutPadToken()

    tokens = wrapper.to_tokens(["a", "bc"], padding_side="left")

    assert torch.equal(tokens, torch.tensor([[999, 0, 97], [0, 98, 99]]))
    assert wrapper.tokenizer.pad_token is None
    assert wrapper.tokenizer.pad_token_id is None


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


def test_wrapper_residual_directions_for_python_tokens_with_torch_weight() -> None:
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

    list_directions = wrapper.tokens_to_residual_directions([[0, 2], [1, 0]])
    tuple_directions = wrapper.tokens_to_residual_directions(((0, 2), (1, 0)))

    expected = torch.tensor(
        [
            [[1.0, 10.0], [3.0, 30.0]],
            [[2.0, 20.0], [1.0, 10.0]],
        ]
    )
    assert torch.equal(list_directions, expected)
    assert torch.equal(tuple_directions, expected)


def test_wrapper_residual_directions_for_python_tokens_with_numpy_weight() -> None:
    np = pytest.importorskip("numpy")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    weight = np.array(
        [
            [1.0, 10.0],
            [2.0, 20.0],
            [3.0, 30.0],
        ]
    )
    wrapper.model = _FakeUnembeddingModel(weight)

    directions = wrapper.tokens_to_residual_directions([[0, 2], [1, 0]])

    assert np.array_equal(
        directions,
        np.array(
            [
                [[1.0, 10.0], [3.0, 30.0]],
                [[2.0, 20.0], [1.0, 10.0]],
            ]
        ),
    )


def test_transformer_lens_compatible_wrapper_residual_directions_for_list_tokens() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel([[1, 10], [2, 20], [3, 30]])

    directions = wrapper.tokens_to_residual_directions([[0, 2], [1, 0]])

    assert directions == [
        [[1, 10], [3, 30]],
        [[2, 20], [1, 10]],
    ]


def test_transformer_lens_compatible_wrapper_residual_directions_for_tuple_weight() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel(((1, 10), (2, 20), (3, 30)))

    directions = wrapper.tokens_to_residual_directions(((0, 2), (1, 0)))

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


def test_transformer_lens_compatible_wrapper_logit_attrs_keeps_batch_tokens_with_pos_slice() -> (
    None
):
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel([[1, 10], [2, 20], [3, 30]])
    cache = ActivationCache({}, model=wrapper)

    attrs = cache.logit_attrs(
        [[[10, 1], [60, 6]]],
        [0, 2],
        apply_ln=False,
        pos_slice=-1,
    )

    assert attrs == [[20.0, 360.0]]


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
    expected_u, expected_s, expected_vh = torch.linalg.svd(weight.T, full_matrices=False)
    assert torch.allclose(wrapper.W_U_U, expected_u)
    assert torch.allclose(wrapper.W_U_S, expected_s)
    assert torch.allclose(wrapper.W_U_V, expected_vh.T)


def test_transformer_lens_compatible_wrapper_exposes_list_unembed_matrix() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel([[1, 10], [2, 20], [3, 30]])

    assert wrapper.W_U == [[1, 2, 3], [10, 20, 30]]
    assert wrapper.b_U == [0, 0, 0]
    assert len(wrapper.W_U_U) == 2
    assert len(wrapper.W_U_S) == 2
    assert len(wrapper.W_U_V) == 3


def test_transformer_lens_compatible_wrapper_preserves_native_unembed_bias() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeTransformerLensNativeUnembedModel(
        [[1, 2, 3], [10, 20, 30]],
        [0.1, 0.2, 0.3],
    )

    assert wrapper.W_U == [[1, 2, 3], [10, 20, 30]]
    assert wrapper.b_U == [0.1, 0.2, 0.3]
    assert wrapper.tl_parameters()["unembed.b_U"] == [0.1, 0.2, 0.3]


def test_transformer_lens_compatible_wrapper_residual_directions_for_native_unembed() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeTransformerLensNativeUnembedModel([[1, 2, 3], [10, 20, 30]])

    assert wrapper.tokens_to_residual_directions([0, 2]) == [[1, 10], [3, 30]]


def test_transformer_lens_compatible_wrapper_center_unembed_centers_hf_embedding_columns() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeUnembeddingModel(
        [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]],
        [1.0, 2.0, 4.0],
    )

    assert wrapper.center_unembed() is wrapper

    assert wrapper.model._weight == [[-1.0, -10.0], [0.0, 0.0], [1.0, 10.0]]
    assert wrapper.W_U == [[-1.0, 0.0, 1.0], [-10.0, 0.0, 10.0]]
    assert wrapper.model._bias == pytest.approx([-4 / 3, -1 / 3, 5 / 3])
    assert wrapper.b_U == pytest.approx([-4 / 3, -1 / 3, 5 / 3])


def test_transformer_lens_compatible_wrapper_center_unembed_centers_native_w_u_rows() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeTransformerLensNativeUnembedModel(
        [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]],
        [1.0, 2.0, 4.0],
    )

    assert wrapper.center_unembed() is wrapper

    assert wrapper.model.W_U == [[-1.0, 0.0, 1.0], [-10.0, 0.0, 10.0]]
    assert wrapper.W_U == [[-1.0, 0.0, 1.0], [-10.0, 0.0, 10.0]]
    assert wrapper.model.b_U == pytest.approx([-4 / 3, -1 / 3, 5 / 3])
    assert wrapper.b_U == pytest.approx([-4 / 3, -1 / 3, 5 / 3])


def test_transformer_lens_compatible_wrapper_center_writing_weights_centers_torch_modules() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    backbone = wrapper.model.model
    layer = backbone.layers[0]

    assert wrapper.center_writing_weights() is wrapper

    assert torch.allclose(backbone.embed_tokens.weight.mean(dim=-1), torch.zeros(5))
    assert torch.allclose(backbone.wpe.weight.mean(dim=-1), torch.zeros(6))
    assert torch.allclose(
        layer.self_attn.o_proj.weight.mean(dim=0),
        torch.zeros(4),
    )
    assert torch.allclose(layer.self_attn.o_proj.bias.mean(), torch.tensor(0.0))
    assert torch.allclose(layer.mlp.down_proj.weight.mean(dim=0), torch.zeros(3))
    assert torch.allclose(layer.mlp.down_proj.bias.mean(), torch.tensor(0.0))
    assert torch.allclose(wrapper.W_O.mean(dim=-1), torch.zeros_like(wrapper.W_O.mean(dim=-1)))
    assert torch.allclose(
        wrapper.W_out.mean(dim=-1),
        torch.zeros_like(wrapper.W_out.mean(dim=-1)),
    )


def test_transformer_lens_compatible_wrapper_center_writing_weights_centers_list_modules() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeListWeightedQwenModel()

    assert wrapper.center_writing_weights() is wrapper

    assert wrapper.W_E == [[-1.5, -0.5, 0.5, 1.5]] * 3
    assert wrapper.W_pos == [[-1.5, -0.5, 0.5, 1.5]] * 2
    assert wrapper.W_O == [
        [
            [[-15.0, -5.0, 5.0, 15.0], [-15.0, -5.0, 5.0, 15.0]],
            [[-15.0, -5.0, 5.0, 15.0], [-15.0, -5.0, 5.0, 15.0]],
        ]
    ]
    assert wrapper.b_O == [[-1.5, -0.5, 0.5, 1.5]]
    assert wrapper.W_out == [
        [[-15.0, -5.0, 5.0, 15.0], [-15.0, -5.0, 5.0, 15.0], [-15.0, -5.0, 5.0, 15.0]]
    ]
    assert wrapper.b_out == [[-1.5, -0.5, 0.5, 1.5]]


def test_transformer_lens_compatible_wrapper_center_writing_weights_centers_native_weights() -> (
    None
):
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = type(
        "_NativeWritingWeights",
        (),
        {
            "W_O": [[[[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]]]],
            "b_O": [[1.0, 2.0, 3.0]],
            "W_out": [[[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]]],
            "b_out": [[10.0, 20.0, 30.0]],
            "config": type("_Config", (), {"num_hidden_layers": 0, "hidden_size": 3})(),
        },
    )()

    assert wrapper.center_writing_weights() is wrapper

    assert wrapper.model.W_O == [[[[-1.0, 0.0, 1.0], [-10.0, 0.0, 10.0]]]]
    assert wrapper.model.b_O == [[-1.0, 0.0, 1.0]]
    assert wrapper.model.W_out == [[[-1.0, 0.0, 1.0], [-10.0, 0.0, 10.0]]]
    assert wrapper.model.b_out == [[-10.0, 0.0, 10.0]]


def test_transformer_lens_compatible_wrapper_center_writing_weights_skips_olmo2_post_norm() -> None:
    class Olmo2ForCausalLM:
        W_O = [[[[1.0, 2.0, 3.0]]]]
        b_O = [[1.0, 2.0, 3.0]]
        W_out = [[[10.0, 20.0, 30.0]]]
        b_out = [[10.0, 20.0, 30.0]]
        config = type(
            "_Config",
            (),
            {
                "model_type": "olmo2",
                "num_hidden_layers": 0,
                "hidden_size": 3,
                "num_attention_heads": 1,
            },
        )()

    wrapper = TransformerLensCompatibleModelWrapper(name="allenai/OLMo-2-0425-1B")
    wrapper.model = Olmo2ForCausalLM()

    assert wrapper.center_writing_weights() is wrapper

    assert wrapper.model.W_O == [[[[1.0, 2.0, 3.0]]]]
    assert wrapper.model.b_O == [[1.0, 2.0, 3.0]]
    assert wrapper.model.W_out == [[[10.0, 20.0, 30.0]]]
    assert wrapper.model.b_out == [[10.0, 20.0, 30.0]]


def test_transformer_lens_compatible_wrapper_fold_layer_norm_folds_gpt2_joint_qkv() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()
    block = wrapper.model.transformer.h[0]
    block.ln_1 = torch.nn.LayerNorm(5)
    with torch.no_grad():
        block.ln_1.weight.copy_(torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0]))
        block.ln_1.bias.copy_(torch.tensor([0.5, -1.0, 1.5, -2.0, 2.5]))
    original_w_q = wrapper.W_Q[0].clone()
    original_b_q = wrapper.b_Q[0].clone()
    expected_w_q = original_w_q * block.ln_1.weight[None, :, None]
    expected_w_q = expected_w_q - expected_w_q.mean(dim=1, keepdim=True)
    expected_b_q = original_b_q + (original_w_q * block.ln_1.bias[None, :, None]).sum(dim=1)

    assert wrapper.fold_layer_norm() is wrapper

    assert torch.allclose(wrapper.W_Q[0], expected_w_q)
    assert torch.allclose(wrapper.b_Q[0], expected_b_q)
    assert torch.equal(block.ln_1.weight, torch.ones_like(block.ln_1.weight))
    assert torch.equal(block.ln_1.bias, torch.zeros_like(block.ln_1.bias))
    assert torch.allclose(wrapper.W_Q[0].mean(dim=1), torch.zeros_like(wrapper.W_Q[0].mean(dim=1)))


def test_transformer_lens_compatible_wrapper_fold_layer_norm_folds_rmsnorm_split_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    layer = wrapper.model.model.layers[0]
    layer.input_layernorm = _FakeModule()
    layer.input_layernorm.weight = torch.tensor([1.0, 2.0, 3.0, 4.0])
    layer.post_attention_layernorm.weight = torch.tensor([0.5, 1.5, 2.5, 3.5])
    layer.self_attn.k_proj.bias = None
    original_w_q = wrapper.W_Q[0].clone()
    original_q_bias = layer.self_attn.q_proj.bias.clone()
    original_w_k = wrapper.W_K[0].clone()
    original_w_in = wrapper.W_in[0].clone()
    original_w_gate = wrapper.W_gate[0].clone()

    assert wrapper.fold_layer_norm() is wrapper

    assert torch.allclose(
        wrapper.W_Q[0], original_w_q * torch.tensor([1.0, 2.0, 3.0, 4.0])[None, :, None]
    )
    assert torch.equal(layer.self_attn.q_proj.bias, original_q_bias)
    assert torch.allclose(
        wrapper.W_K[0], original_w_k * torch.tensor([1.0, 2.0, 3.0, 4.0])[None, :, None]
    )
    assert layer.self_attn.k_proj.bias is None
    assert torch.allclose(
        wrapper.W_in[0], original_w_in * torch.tensor([0.5, 1.5, 2.5, 3.5])[:, None]
    )
    assert torch.allclose(
        wrapper.W_gate[0], original_w_gate * torch.tensor([0.5, 1.5, 2.5, 3.5])[:, None]
    )
    assert torch.equal(layer.input_layernorm.weight, torch.ones_like(layer.input_layernorm.weight))
    assert torch.equal(
        layer.post_attention_layernorm.weight,
        torch.ones_like(layer.post_attention_layernorm.weight),
    )


def test_transformer_lens_compatible_wrapper_fold_layer_norm_uses_offset_rmsnorm_scale() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google/gemma-2b")
    wrapper.model = _FakeOffsetRmsWeightedQwenModel()
    layer = wrapper.model.model.layers[0]
    layer.input_layernorm = _FakeModule()
    layer.input_layernorm.weight = torch.tensor([1.0, 2.0, 3.0, 4.0])
    layer.post_attention_layernorm.weight = torch.tensor([0.5, 1.5, 2.5, 3.5])
    original_w_q = wrapper.W_Q[0].clone()
    original_w_in = wrapper.W_in[0].clone()
    original_w_gate = wrapper.W_gate[0].clone()

    assert wrapper.cfg.rmsnorm_uses_offset is True
    assert wrapper.fold_layer_norm() is wrapper

    assert torch.allclose(
        wrapper.W_Q[0], original_w_q * torch.tensor([2.0, 3.0, 4.0, 5.0])[None, :, None]
    )
    assert torch.allclose(
        wrapper.W_in[0], original_w_in * torch.tensor([1.5, 2.5, 3.5, 4.5])[:, None]
    )
    assert torch.allclose(
        wrapper.W_gate[0], original_w_gate * torch.tensor([1.5, 2.5, 3.5, 4.5])[:, None]
    )
    assert torch.equal(layer.input_layernorm.weight, torch.zeros_like(layer.input_layernorm.weight))
    assert torch.equal(
        layer.post_attention_layernorm.weight,
        torch.zeros_like(layer.post_attention_layernorm.weight),
    )


def test_transformer_lens_compatible_wrapper_fold_value_biases_folds_split_projection_bias() -> (
    None
):
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    attention = wrapper.model.model.layers[0].self_attn
    original_b_o = attention.o_proj.bias.clone()
    expected = original_b_o + torch.einsum("hd,hdm->m", wrapper.b_V[0], wrapper.W_O[0])

    assert wrapper.fold_value_biases() is wrapper

    assert torch.equal(attention.v_proj.bias, torch.zeros_like(attention.v_proj.bias))
    assert torch.equal(wrapper.b_V, torch.zeros_like(wrapper.b_V))
    assert torch.equal(attention.o_proj.bias, expected)
    assert torch.equal(wrapper.b_O[0], expected)


def test_transformer_lens_compatible_wrapper_fold_value_biases_creates_missing_output_bias() -> (
    None
):
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    attention = wrapper.model.model.layers[0].self_attn
    attention.v_proj = torch.nn.Linear(4, 4, bias=True)
    attention.o_proj = torch.nn.Linear(4, 4, bias=False)
    with torch.no_grad():
        attention.v_proj.bias.copy_(torch.arange(4, dtype=torch.float32))
        attention.o_proj.weight.copy_(torch.arange(16, dtype=torch.float32).reshape(4, 4))
    expected = torch.einsum("hd,hdm->m", wrapper.b_V[0], wrapper.W_O[0])

    assert wrapper.fold_value_biases() is wrapper

    assert attention.o_proj.bias is not None
    assert torch.equal(attention.v_proj.bias, torch.zeros_like(attention.v_proj.bias))
    assert torch.equal(attention.o_proj.bias, expected)
    assert torch.equal(wrapper.b_O[0], expected)


def test_transformer_lens_compatible_wrapper_fold_value_biases_repeats_gqa_value_biases() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="swiss-ai/Apertus-8B-2509")
    wrapper.model = _FakeApertusModel()
    attention = wrapper.model.model.layers[0].self_attn
    original_b_o = attention.o_proj.bias.clone()
    aligned_b_v = wrapper.b_V[0].repeat_interleave(2, dim=0)
    expected = original_b_o + torch.einsum("hd,hdm->m", aligned_b_v, wrapper.W_O[0])

    assert wrapper.fold_value_biases() is wrapper

    assert torch.equal(attention.v_proj.bias, torch.zeros_like(attention.v_proj.bias))
    assert torch.equal(wrapper.b_O[0], expected)


def test_transformer_lens_compatible_wrapper_fold_value_biases_zeros_joint_qkv_value_bias() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()
    attention = wrapper.model.transformer.h[0].attn
    attention.c_proj.weight = torch.arange(36, dtype=torch.float32).reshape(6, 6)
    attention.c_proj.bias = torch.arange(6, dtype=torch.float32)
    original_joint_bias = attention.c_attn.bias.clone()
    original_b_o = attention.c_proj.bias.clone()
    expected = original_b_o + torch.einsum("hd,hdm->m", wrapper.b_V[0], wrapper.W_O[0])

    assert wrapper.fold_value_biases() is wrapper

    assert torch.equal(attention.c_attn.bias[:12], original_joint_bias[:12])
    assert torch.equal(attention.c_attn.bias[12:], torch.zeros_like(original_joint_bias[12:]))
    assert torch.equal(wrapper.b_V, torch.zeros_like(wrapper.b_V))
    assert torch.equal(attention.c_proj.bias, expected)


def test_transformer_lens_compatible_wrapper_fold_value_biases_folds_native_weights() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = type(
        "_NativeValueBiasWeights",
        (),
        {
            "b_V": [[[1.0, 2.0], [3.0, 4.0]]],
            "W_O": [[[[1.0, 0.0, 10.0], [0.0, 1.0, 20.0]], [[2.0, 0.0, 30.0], [0.0, 2.0, 40.0]]]],
            "b_O": [[0.5, 1.5, 2.5]],
            "config": type(
                "_Config",
                (),
                {"num_hidden_layers": 0, "hidden_size": 3, "num_attention_heads": 2},
            )(),
        },
    )()

    assert wrapper.fold_value_biases() is wrapper

    assert wrapper.model.b_V == [[[0, 0], [0, 0]]]
    assert wrapper.model.b_O == [[7.5, 11.5, 302.5]]


def test_wrapper_refactor_factored_attn_matrices_refactors_native_ov() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = type(
        "_NativeOVWeights",
        (),
        {
            "W_V": torch.tensor([[[[2.0, 0.0], [0.0, 1.0]]]]),
            "W_O": torch.tensor([[[[1.0, 3.0], [2.0, 4.0]]]]),
            "config": type(
                "_Config",
                (),
                {"num_hidden_layers": 0, "hidden_size": 2, "num_attention_heads": 1},
            )(),
        },
    )()
    original_ov = torch.matmul(wrapper.model.W_V, wrapper.model.W_O)

    assert wrapper.refactor_factored_attn_matrices() is wrapper

    assert torch.allclose(torch.matmul(wrapper.model.W_V, wrapper.model.W_O), original_ov)
    eye = torch.eye(2)
    assert torch.allclose(
        torch.matmul(wrapper.model.W_O, wrapper.model.W_O.transpose(-1, -2)),
        eye.unsqueeze(0).unsqueeze(0),
    )


def test_wrapper_refactor_factored_attn_matrices_refactors_native_qk() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = type(
        "_NativeQKWeights",
        (),
        {
            "W_Q": torch.tensor([[[[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]]]),
            "W_K": torch.tensor([[[[2.0, 1.0], [0.0, 3.0], [4.0, 5.0]]]]),
            "b_Q": torch.tensor([[[0.5, 1.5]]]),
            "b_K": torch.tensor([[[2.5, 3.5]]]),
            "config": type(
                "_Config",
                (),
                {"num_hidden_layers": 0, "hidden_size": 3, "num_attention_heads": 1},
            )(),
        },
    )()
    original_qk = torch.matmul(
        torch.cat([wrapper.model.W_Q, wrapper.model.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.model.W_K, wrapper.model.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )

    assert wrapper.refactor_factored_attn_matrices() is wrapper

    refactored_qk = torch.matmul(
        torch.cat([wrapper.model.W_Q, wrapper.model.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.model.W_K, wrapper.model.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    assert wrapper.model.W_Q.shape == (1, 1, 3, 2)
    assert wrapper.model.W_K.shape == (1, 1, 3, 2)
    assert wrapper.model.b_Q.shape == (1, 1, 2)
    assert wrapper.model.b_K.shape == (1, 1, 2)
    assert torch.allclose(refactored_qk, original_qk, atol=1e-4)


def test_wrapper_refactor_factored_attn_matrices_rejects_rotary_qk() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = type(
        "_NativeRotaryQKWeights",
        (),
        {
            "W_Q": torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]]),
            "W_K": torch.tensor([[[[2.0, 1.0], [0.0, 3.0]]]]),
            "config": type(
                "_Config",
                (),
                {
                    "num_hidden_layers": 0,
                    "hidden_size": 2,
                    "num_attention_heads": 1,
                    "positional_embedding_type": "rotary",
                },
            )(),
        },
    )()

    with pytest.raises(AssertionError, match="rotary"):
        wrapper.refactor_factored_attn_matrices()

    dict_wrapper = TransformerLensCompatibleModelWrapper(name="./dict-rotary")
    dict_wrapper.model = type(
        "_NativeDictRotaryQKWeights",
        (),
        {
            "W_Q": torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]]),
            "W_K": torch.tensor([[[[2.0, 1.0], [0.0, 3.0]]]]),
            "config": {
                "num_hidden_layers": 0,
                "hidden_size": 2,
                "num_attention_heads": 1,
                "rope_parameters": {"partial_rotary_factor": 0.5},
            },
        },
    )()

    with pytest.raises(AssertionError, match="rotary"):
        dict_wrapper.refactor_factored_attn_matrices()


def test_wrapper_refactor_factored_attn_matrices_refactors_hf_split_projections() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    attention = wrapper.model.model.layers[0].self_attn
    original_q_shape = attention.q_proj.weight.shape
    original_o_shape = attention.o_proj.weight.shape
    original_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    original_ov = torch.matmul(wrapper.W_V, wrapper.W_O)

    assert wrapper.refactor_factored_attn_matrices() is wrapper

    refactored_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    refactored_ov = torch.matmul(wrapper.W_V, wrapper.W_O)
    assert attention.q_proj.weight.shape == original_q_shape
    assert attention.o_proj.weight.shape == original_o_shape
    assert torch.allclose(refactored_qk, original_qk, atol=1e-3)
    assert torch.allclose(refactored_ov, original_ov, atol=1e-2)
    assert torch.equal(wrapper.b_V, torch.zeros_like(wrapper.b_V))


def test_wrapper_refactor_factored_attn_matrices_preserves_low_precision_dtypes() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    attention = wrapper.model.model.layers[0].self_attn
    attention.q_proj = torch.nn.Linear(4, 4, bias=True, dtype=torch.float16)
    attention.k_proj = torch.nn.Linear(4, 4, bias=True, dtype=torch.float16)
    attention.v_proj = torch.nn.Linear(4, 4, bias=True, dtype=torch.float16)
    attention.o_proj = torch.nn.Linear(4, 4, bias=False, dtype=torch.float16)
    with torch.no_grad():
        attention.q_proj.weight.copy_(torch.arange(16, dtype=torch.float16).reshape(4, 4))
        attention.k_proj.weight.copy_(torch.arange(16, 32, dtype=torch.float16).reshape(4, 4))
        attention.v_proj.weight.copy_(torch.arange(32, 48, dtype=torch.float16).reshape(4, 4))
        attention.o_proj.weight.copy_(torch.arange(48, 64, dtype=torch.float16).reshape(4, 4))
        attention.q_proj.bias.copy_(torch.arange(4, dtype=torch.float16))
        attention.k_proj.bias.copy_(torch.arange(4, 8, dtype=torch.float16))
        attention.v_proj.bias.copy_(torch.arange(8, 12, dtype=torch.float16))

    original_qk = torch.matmul(
        torch.cat([wrapper.W_Q.float(), wrapper.b_Q.float().unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K.float(), wrapper.b_K.float().unsqueeze(-2)], dim=-2).transpose(
            -1, -2
        ),
    )

    assert wrapper.refactor_factored_attn_matrices() is wrapper

    refactored_qk = torch.matmul(
        torch.cat([wrapper.W_Q.float(), wrapper.b_Q.float().unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K.float(), wrapper.b_K.float().unsqueeze(-2)], dim=-2).transpose(
            -1, -2
        ),
    )
    assert attention.q_proj.weight.dtype == torch.float16
    assert attention.k_proj.weight.dtype == torch.float16
    assert attention.v_proj.weight.dtype == torch.float16
    assert attention.o_proj.weight.dtype == torch.float16
    assert attention.o_proj.bias is not None
    assert attention.o_proj.bias.dtype == torch.float16
    assert torch.allclose(refactored_qk, original_qk, rtol=1e-3, atol=3e-1)


def test_wrapper_refactor_factored_attn_matrices_creates_missing_output_bias() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    attention = wrapper.model.model.layers[0].self_attn
    attention.q_proj = torch.nn.Linear(4, 4, bias=True)
    attention.k_proj = torch.nn.Linear(4, 4, bias=True)
    attention.v_proj = torch.nn.Linear(4, 4, bias=True)
    attention.o_proj = torch.nn.Linear(4, 4, bias=False)
    with torch.no_grad():
        attention.q_proj.weight.copy_(torch.arange(16, dtype=torch.float32).reshape(4, 4))
        attention.k_proj.weight.copy_(torch.arange(16, 32, dtype=torch.float32).reshape(4, 4))
        attention.v_proj.weight.copy_(torch.arange(32, 48, dtype=torch.float32).reshape(4, 4))
        attention.o_proj.weight.copy_(torch.arange(48, 64, dtype=torch.float32).reshape(4, 4))
        attention.q_proj.bias.copy_(torch.arange(4, dtype=torch.float32))
        attention.k_proj.bias.copy_(torch.arange(4, 8, dtype=torch.float32))
        attention.v_proj.bias.copy_(torch.arange(8, 12, dtype=torch.float32))
    original_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    original_ov = torch.matmul(wrapper.W_V, wrapper.W_O)

    assert wrapper.refactor_factored_attn_matrices() is wrapper

    refactored_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    refactored_ov = torch.matmul(wrapper.W_V, wrapper.W_O)
    assert attention.o_proj.bias is not None
    assert torch.allclose(refactored_qk, original_qk, atol=1e-3)
    assert torch.allclose(refactored_ov, original_ov, atol=1e-2)
    assert torch.equal(wrapper.b_V, torch.zeros_like(wrapper.b_V))


def test_wrapper_refactor_factored_attn_matrices_refactors_gpt2_joint_qkv() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()
    attention = wrapper.model.transformer.h[0].attn
    attention.c_attn.weight = torch.arange(108, dtype=torch.float32).reshape(6, 18)
    attention.c_proj.weight = torch.arange(36, dtype=torch.float32).reshape(6, 6)
    attention.c_proj.bias = torch.arange(6, dtype=torch.float32)
    original_c_attn_shape = attention.c_attn.weight.shape
    original_c_proj_shape = attention.c_proj.weight.shape
    original_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    original_ov = torch.matmul(wrapper.W_V, wrapper.W_O)

    assert wrapper.refactor_factored_attn_matrices() is wrapper

    refactored_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    refactored_ov = torch.matmul(wrapper.W_V, wrapper.W_O)
    assert attention.c_attn.weight.shape == original_c_attn_shape
    assert attention.c_proj.weight.shape == original_c_proj_shape
    assert torch.allclose(refactored_qk, original_qk, atol=1e-2)
    assert torch.allclose(refactored_ov, original_ov, atol=1e-2)
    assert torch.equal(wrapper.b_V, torch.zeros_like(wrapper.b_V))


def test_wrapper_refactor_factored_attn_matrices_refactors_interleaved_joint_qkv() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="EleutherAI/pythia-70m")
    wrapper.model = _FakeGptNeoxModel()
    attention = wrapper.model.gpt_neox.layers[0].attention
    attention.dense = _FakeModule(
        torch.arange(16, dtype=torch.float32).reshape(4, 4),
        torch.arange(4, dtype=torch.float32),
    )
    original_qkv_shape = attention.query_key_value.weight.shape
    original_dense_shape = attention.dense.weight.shape
    original_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    original_ov = torch.matmul(wrapper.W_V, wrapper.W_O)

    assert wrapper.refactor_factored_attn_matrices() is wrapper

    refactored_qk = torch.matmul(
        torch.cat([wrapper.W_Q, wrapper.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.W_K, wrapper.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    refactored_ov = torch.matmul(wrapper.W_V, wrapper.W_O)
    assert attention.query_key_value.weight.shape == original_qkv_shape
    assert attention.dense.weight.shape == original_dense_shape
    assert torch.allclose(refactored_qk, original_qk, atol=1e-3)
    assert torch.allclose(refactored_ov, original_ov, atol=1e-2)
    assert torch.equal(wrapper.b_V, torch.zeros_like(wrapper.b_V))


def test_transformer_lens_compatible_wrapper_process_weights_can_request_native_refactor() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = type(
        "_NativeProcessRefactorWeights",
        (),
        {
            "W_Q": torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]]),
            "W_K": torch.tensor([[[[2.0, 1.0], [0.0, 3.0]]]]),
            "b_Q": torch.tensor([[[0.5, 1.5]]]),
            "b_K": torch.tensor([[[2.5, 3.5]]]),
            "W_V": torch.tensor([[[[2.0, 0.0], [0.0, 1.0]]]]),
            "W_O": torch.tensor([[[[1.0, 3.0], [2.0, 4.0]]]]),
            "config": type(
                "_Config",
                (),
                {"num_hidden_layers": 0, "hidden_size": 2, "num_attention_heads": 1},
            )(),
        },
    )()
    original_qk = torch.matmul(
        torch.cat([wrapper.model.W_Q, wrapper.model.b_Q.unsqueeze(-2)], dim=-2),
        torch.cat([wrapper.model.W_K, wrapper.model.b_K.unsqueeze(-2)], dim=-2).transpose(-1, -2),
    )
    original_ov = torch.matmul(wrapper.model.W_V, wrapper.model.W_O)

    assert (
        wrapper.process_weights_(
            center_writing_weights=False,
            center_unembed=False,
            fold_value_biases=False,
            refactor_factored_attn_matrices=True,
        )
        is wrapper
    )

    assert torch.allclose(
        torch.matmul(
            torch.cat([wrapper.model.W_Q, wrapper.model.b_Q.unsqueeze(-2)], dim=-2),
            torch.cat([wrapper.model.W_K, wrapper.model.b_K.unsqueeze(-2)], dim=-2).transpose(
                -1, -2
            ),
        ),
        original_qk,
        atol=1e-4,
    )
    assert torch.allclose(torch.matmul(wrapper.model.W_V, wrapper.model.W_O), original_ov)


def test_transformer_lens_compatible_wrapper_process_weights_runs_supported_passes() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    unembed = _FakeEmbedding(torch.tensor([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]))
    wrapper.model.get_output_embeddings = lambda: unembed
    attention = wrapper.model.model.layers[0].self_attn
    original_embedding = wrapper.model.model.embed_tokens.weight.clone()
    original_w_o = attention.o_proj.weight.clone()
    original_o_bias = attention.o_proj.bias.clone()
    expected_o_bias = original_o_bias + torch.einsum("hd,hdm->m", wrapper.b_V[0], wrapper.W_O[0])

    assert wrapper.process_weights_() is wrapper

    assert torch.allclose(wrapper.W_U.mean(dim=-1), torch.zeros(2))
    assert torch.equal(wrapper.model.model.embed_tokens.weight, original_embedding)
    assert torch.equal(attention.v_proj.bias, torch.zeros_like(attention.v_proj.bias))
    assert torch.equal(attention.o_proj.weight, original_w_o)
    assert torch.equal(attention.o_proj.bias, expected_o_bias)


def test_transformer_lens_compatible_wrapper_process_weights_centers_ln_writing_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2EmbeddingModel()
    block = wrapper.model.transformer.h[0]
    block.attn.c_proj.weight = torch.arange(36, dtype=torch.float32).reshape(6, 6)
    block.attn.c_proj.bias = torch.arange(6, dtype=torch.float32)
    block.mlp.c_proj.weight = torch.arange(18, dtype=torch.float32).reshape(3, 6)
    block.mlp.c_proj.bias = torch.arange(6, dtype=torch.float32)

    assert wrapper.process_weights_(center_unembed=False, fold_value_biases=False) is wrapper

    assert torch.allclose(wrapper.W_E.mean(dim=-1), torch.zeros(10))
    assert torch.allclose(wrapper.W_pos.mean(dim=-1), torch.zeros(10))
    assert torch.allclose(wrapper.W_O.mean(dim=-1), torch.zeros_like(wrapper.W_O.mean(dim=-1)))
    assert torch.allclose(wrapper.W_out.mean(dim=-1), torch.zeros_like(wrapper.W_out.mean(dim=-1)))
    assert torch.allclose(block.attn.c_proj.bias.mean(), torch.tensor(0.0))
    assert torch.allclose(block.mlp.c_proj.bias.mean(), torch.tensor(0.0))


def test_wrapper_process_weights_recenters_ln_b_o_after_value_folding() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()
    attention = wrapper.model.transformer.h[0].attn
    attention.c_proj.weight = torch.arange(36, dtype=torch.float32).reshape(6, 6)
    attention.c_proj.bias = torch.arange(6, dtype=torch.float32)

    assert wrapper.process_weights_(center_unembed=False) is wrapper

    assert torch.equal(attention.c_attn.bias[12:], torch.zeros_like(attention.c_attn.bias[12:]))
    assert torch.equal(wrapper.b_V, torch.zeros_like(wrapper.b_V))
    assert torch.allclose(attention.c_proj.bias.mean(), torch.tensor(0.0))


def test_transformer_lens_compatible_wrapper_process_weights_respects_disabled_passes() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    unembed = _FakeEmbedding(torch.tensor([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]))
    wrapper.model.get_output_embeddings = lambda: unembed
    original_embedding = wrapper.model.model.embed_tokens.weight.clone()
    original_v_bias = wrapper.model.model.layers[0].self_attn.v_proj.bias.clone()

    assert (
        wrapper.process_weights_(
            center_writing_weights=False,
            center_unembed=False,
            fold_value_biases=False,
        )
        is wrapper
    )

    assert torch.equal(unembed.weight, torch.tensor([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]))
    assert torch.equal(wrapper.model.model.embed_tokens.weight, original_embedding)
    assert torch.equal(wrapper.model.model.layers[0].self_attn.v_proj.bias, original_v_bias)


def test_transformer_lens_compatible_wrapper_process_weights_skips_olmo2_center_writing_pass() -> (
    None
):
    class Olmo2ForCausalLM:
        W_O = [[[[1.0, 2.0, 3.0]]]]
        b_O = [[1.0, 2.0, 3.0]]
        W_out = [[[10.0, 20.0, 30.0]]]
        b_out = [[10.0, 20.0, 30.0]]
        config = type(
            "_Config",
            (),
            {
                "model_type": "olmo2",
                "num_hidden_layers": 0,
                "hidden_size": 3,
                "num_attention_heads": 1,
            },
        )()

        def get_output_embeddings(self) -> None:
            return None

    wrapper = TransformerLensCompatibleModelWrapper(name="allenai/OLMo-2-0425-1B")
    wrapper.model = Olmo2ForCausalLM()

    assert wrapper.process_weights_(center_unembed=False, fold_value_biases=False) is wrapper

    assert wrapper.model.W_O == [[[[1.0, 2.0, 3.0]]]]
    assert wrapper.model.b_O == [[1.0, 2.0, 3.0]]
    assert wrapper.model.W_out == [[[10.0, 20.0, 30.0]]]
    assert wrapper.model.b_out == [[10.0, 20.0, 30.0]]


def test_wrapper_process_weights_skips_center_unembed_for_logit_softcap() -> None:
    class _SoftCapUnembeddingModel(_FakeUnembeddingModel):
        config = type(
            "_Config",
            (),
            {
                "output_logits_soft_cap": 30.0,
                "num_hidden_layers": 0,
                "hidden_size": 2,
                "num_attention_heads": 1,
            },
        )()

    wrapper = TransformerLensCompatibleModelWrapper(name="google/gemma-2-2b")
    wrapper.model = _SoftCapUnembeddingModel([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])

    assert (
        wrapper.process_weights_(center_writing_weights=False, fold_value_biases=False) is wrapper
    )

    assert wrapper.model._weight == [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]

    assert wrapper.center_unembed() is wrapper
    assert wrapper.model._weight == [[-1.0, -10.0], [0.0, 0.0], [1.0, 10.0]]


def test_transformer_lens_compatible_wrapper_process_weights_skips_shortformer_centering() -> None:
    class _ShortformerModel(_FakeUnembeddingModel):
        config = {
            "positional_embedding_type": "shortformer",
            "num_hidden_layers": 0,
            "hidden_size": 2,
            "num_attention_heads": 1,
        }

        def __init__(self) -> None:
            super().__init__(weight=None)
            self.input_embeddings = _FakeEmbedding([[1.0, 10.0], [2.0, 20.0]])

        def get_input_embeddings(self) -> _FakeEmbedding:
            return self.input_embeddings

        def get_output_embeddings(self) -> None:
            return None

    wrapper = TransformerLensCompatibleModelWrapper(name="stanford-crfm/shortformer")
    wrapper.model = _ShortformerModel()

    assert wrapper.process_weights_(fold_value_biases=False) is wrapper

    assert wrapper.model.input_embeddings.weight == [[1.0, 10.0], [2.0, 20.0]]


def test_transformer_lens_compatible_wrapper_process_weights_disables_incompatible_fold_ln() -> (
    None
):
    class _TrackingWrapper(TransformerLensCompatibleModelWrapper):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.fold_layer_norm_calls = 0

        def fold_layer_norm(
            self, *args: Any, **kwargs: Any
        ) -> TransformerLensCompatibleModelWrapper:
            self.fold_layer_norm_calls += 1
            return self

    shortformer_wrapper = _TrackingWrapper(name="stanford-crfm/shortformer")
    shortformer_wrapper.model = type(
        "_ShortformerNoLayers",
        (),
        {
            "config": {
                "positional_embedding_type": "shortformer",
                "num_hidden_layers": 0,
                "hidden_size": 2,
                "num_attention_heads": 1,
            },
            "get_output_embeddings": lambda self: None,
        },
    )()

    assert shortformer_wrapper.process_weights_(fold_value_biases=False) is shortformer_wrapper
    assert shortformer_wrapper.fold_layer_norm_calls == 0

    class Olmo2ForCausalLM:
        config = type(
            "_Config",
            (),
            {
                "model_type": "olmo2",
                "num_hidden_layers": 0,
                "hidden_size": 2,
                "num_attention_heads": 1,
            },
        )()

        def get_output_embeddings(self) -> None:
            return None

    olmo2_wrapper = _TrackingWrapper(name="allenai/OLMo-2-0425-1B")
    olmo2_wrapper.model = Olmo2ForCausalLM()

    assert (
        olmo2_wrapper.process_weights_(center_unembed=False, fold_value_biases=False)
        is olmo2_wrapper
    )
    assert olmo2_wrapper.fold_layer_norm_calls == 0


def test_transformer_lens_compatible_wrapper_process_weights_rejects_unknown_options() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()

    with pytest.raises(TypeError, match="unexpected"):
        wrapper.process_weights_(unexpected=True)


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


def test_transformer_lens_compatible_wrapper_exposes_apertus_gqa_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="swiss-ai/Apertus-8B-2509")
    wrapper.model = _FakeApertusModel()
    attention = wrapper.model.model.layers[0].self_attn

    expected_q = attention.q_proj.weight.reshape(4, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_k = attention.k_proj.weight.reshape(2, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_v = attention.v_proj.weight.reshape(2, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_o = attention.o_proj.weight.reshape(8, 4, 2).permute(1, 2, 0).unsqueeze(0)

    assert (
        architecture_adapter_for_name(model_name="swiss-ai/Apertus-8B-2509").name
        == "apertus_decoder"
    )
    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)
    assert torch.equal(wrapper.W_O, expected_o)
    assert torch.equal(wrapper.b_Q, attention.q_proj.bias.reshape(4, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_K, attention.k_proj.bias.reshape(2, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_V, attention.v_proj.bias.reshape(2, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_O, attention.o_proj.bias.unsqueeze(0))

    assert wrapper.cfg.n_key_value_heads == 2
    assert torch.equal(wrapper.QK.B, expected_k.repeat_interleave(2, dim=1).transpose(-2, -1))
    assert torch.equal(wrapper.OV.A, expected_v.repeat_interleave(2, dim=1))

    attention.k_proj.bias = None
    attention.v_proj.bias = None
    assert torch.equal(wrapper.b_K, torch.zeros(1, 2, 2))
    assert torch.equal(wrapper.b_V, torch.zeros(1, 2, 2))


def test_transformer_lens_compatible_wrapper_exposes_gpt_oss_gqa_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="openai/gpt-oss-20b")
    wrapper.model = _FakeGptOssModel()
    attention = wrapper.model.model.layers[0].self_attn

    expected_q = attention.q_proj.weight.reshape(4, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_k = attention.k_proj.weight.reshape(2, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_v = attention.v_proj.weight.reshape(2, 2, 8).permute(0, 2, 1).unsqueeze(0)
    expected_o = attention.o_proj.weight.reshape(8, 4, 2).permute(1, 2, 0).unsqueeze(0)

    assert architecture_adapter_for_name(model_name="openai/gpt-oss-20b").name == "gpt_oss_decoder"
    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)
    assert torch.equal(wrapper.W_O, expected_o)
    assert torch.equal(wrapper.b_Q, attention.q_proj.bias.reshape(4, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_K, attention.k_proj.bias.reshape(2, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_V, attention.v_proj.bias.reshape(2, 2).unsqueeze(0))
    assert torch.equal(wrapper.b_O, attention.o_proj.bias.unsqueeze(0))

    assert wrapper.cfg.n_key_value_heads == 2
    assert torch.equal(wrapper.QK.B, expected_k.repeat_interleave(2, dim=1).transpose(-2, -1))
    assert torch.equal(wrapper.OV.A, expected_v.repeat_interleave(2, dim=1))
    with pytest.raises(NotImplementedError, match="routed MoE experts"):
        _ = wrapper.W_in
    with pytest.raises(NotImplementedError, match="routed MoE experts"):
        _ = wrapper.W_out


def test_transformer_lens_compatible_wrapper_rejects_routed_moe_dense_mlp_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="mistralai/Mixtral-8x7B-v0.1")
    wrapper.model = _FakeRoutedMoeModel()
    attention = wrapper.model.model.layers[0].self_attn

    expected_q = attention.q_proj.weight.reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_o = attention.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0).unsqueeze(0)

    assert architecture_adapter_for_name(model_name="mistralai/Mixtral-8x7B-v0.1").name == (
        "routed_moe_decoder"
    )
    assert architecture_adapter_for_name(model_name="allenai/OLMoE-1B-7B-0924").name == (
        "routed_moe_decoder"
    )
    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_O, expected_o)
    with pytest.raises(NotImplementedError, match="multiple experts"):
        _ = wrapper.W_in
    with pytest.raises(NotImplementedError, match="multiple experts"):
        _ = wrapper.W_gate
    with pytest.raises(NotImplementedError, match="multiple experts"):
        _ = wrapper.W_out


def test_transformer_lens_compatible_wrapper_uses_routed_moe_adapter_for_local_qwen_moe_type() -> (
    None
):
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="./models/local-qwen-moe")
    wrapper.model = _FakeRoutedMoeModel()
    wrapper.model.config.model_type = "qwen3_moe"
    attention = wrapper.model.model.layers[0].self_attn

    expected_q = attention.q_proj.weight.reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)

    assert (
        architecture_adapter_for_model(
            wrapper.model,
            model_name=wrapper.name,
        ).name
        == "routed_moe_decoder"
    )
    assert torch.equal(wrapper.W_Q, expected_q)
    with pytest.raises(NotImplementedError, match="multiple experts"):
        _ = wrapper.W_in


def test_transformer_lens_compatible_wrapper_processes_qwen_moe_without_dense_mlp_internals() -> (
    None
):
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-30B-A3B")
    wrapper.model = _FakeRoutedMoeModel()
    wrapper.model.config.model_type = "qwen3_moe"
    unembed = _FakeEmbedding(torch.arange(12, dtype=torch.float32).reshape(3, 4))
    wrapper.model.get_output_embeddings = lambda: unembed
    attention = wrapper.model.model.layers[0].self_attn
    original_o_bias = attention.o_proj.bias.clone()
    expected_o_bias = original_o_bias + torch.einsum("hd,hdm->m", wrapper.b_V[0], wrapper.W_O[0])

    assert wrapper.process_weights_() is wrapper

    assert architecture_adapter_for_name(model_name=wrapper.name).name == "routed_moe_decoder"
    assert torch.allclose(wrapper.W_U.mean(dim=-1), torch.zeros(4))
    assert torch.equal(attention.v_proj.bias, torch.zeros_like(attention.v_proj.bias))
    assert torch.equal(attention.o_proj.bias, expected_o_bias)
    with pytest.raises(NotImplementedError, match="multiple experts"):
        _ = wrapper.W_in


def test_wrapper_accumulated_bias_matches_transformerlens_semantics() -> None:
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


def test_transformer_lens_compatible_wrapper_exposes_gemma3_conditional_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="google/gemma-3-4b-it")
    wrapper.model = _FakeGemma3ConditionalModel()
    layer = wrapper.model.model.language_model.layers[0]
    attention = layer.self_attn

    expected_q = attention.q_proj.weight.reshape(2, 2, 4).permute(0, 2, 1).unsqueeze(0)
    expected_o = attention.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0).unsqueeze(0)

    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_O, expected_o)
    assert torch.equal(wrapper.W_in, layer.mlp.up_proj.weight.T.unsqueeze(0))
    assert torch.equal(wrapper.W_gate, layer.mlp.gate_proj.weight.T.unsqueeze(0))
    assert torch.equal(wrapper.W_out, layer.mlp.down_proj.weight.T.unsqueeze(0))


def test_wrapper_all_composition_scores_match_transformerlens_mask() -> None:
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


def test_component_bridge_reshapes_attention_weights_for_tuple_backend() -> None:
    weight = tuple(tuple(row * 10 + col for col in range(4)) for row in range(4))

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
    assert cfg.use_attn_result is False
    assert cfg.use_split_qkv_input is False
    assert cfg.use_hook_mlp_in is False
    assert cfg.use_attn_in is False
    assert cfg.ungroup_grouped_query_attention is False
    assert cfg.attn_only is False
    assert cfg.parallel_attn_mlp is False
    assert cfg.to_dict()["n_layers"] == 1
    assert list(range(cfg.n_layers)) == [0]


def test_transformer_lens_compatible_wrapper_supports_transformerlens_runtime_toggles() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()

    with pytest.raises(AssertionError, match="use_attn_result"):
        wrapper.check_hooks_to_add(None, "blocks.0.attn.hook_result", None)
    with pytest.raises(AssertionError, match="use_split_qkv_input"):
        wrapper.check_hooks_to_add(None, "blocks.0.hook_q_input", None)
    with pytest.raises(AssertionError, match="use_hook_mlp_in"):
        wrapper.check_hooks_to_add(None, "blocks.0.hook_mlp_in", None)
    with pytest.raises(AssertionError, match="use_attn_in"):
        wrapper.check_hooks_to_add(None, "blocks.0.hook_attn_in", None)

    wrapper.set_use_attn_result(True)
    wrapper.set_use_split_qkv_input(True)
    wrapper.set_use_hook_mlp_in(True)
    wrapper.set_use_attn_in(True)
    wrapper.set_ungroup_grouped_query_attention(True)

    wrapper.check_hooks_to_add(None, "blocks.0.attn.hook_result", None)
    wrapper.check_hooks_to_add(None, "blocks.0.hook_q_input", None)
    wrapper.check_hooks_to_add(None, "blocks.0.hook_mlp_in", None)
    wrapper.check_hooks_to_add(None, "blocks.0.hook_attn_in", None)

    cfg = wrapper.cfg
    assert cfg.use_attn_result is True
    assert cfg.use_split_qkv_input is True
    assert cfg.use_hook_mlp_in is True
    assert cfg.use_attn_in is True
    assert cfg.ungroup_grouped_query_attention is True
    assert cfg.to_dict()["use_attn_result"] is True

    wrapper.set_use_attn_result(False)
    wrapper.set_use_split_qkv_input(False)
    wrapper.set_use_hook_mlp_in(False)
    wrapper.set_use_attn_in(False)
    wrapper.set_ungroup_grouped_query_attention(False)

    cfg = wrapper.cfg
    assert cfg.use_attn_result is False
    assert cfg.use_split_qkv_input is False
    assert cfg.use_hook_mlp_in is False
    assert cfg.use_attn_in is False
    assert cfg.ungroup_grouped_query_attention is False


def test_transformer_lens_runtime_hook_flags_are_checked_during_registration() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()

    with pytest.raises(AssertionError, match="use_split_qkv_input"):
        wrapper.add_hook("blocks.0.hook_q_input", lambda **_kwargs: None)
    with pytest.raises(AssertionError, match="use_hook_mlp_in"):
        wrapper.run_with_hooks(
            {"input_ids": [[1, 2]]},
            fwd_hooks=[("blocks.0.hook_mlp_in", lambda **_kwargs: None)],
        )
    with pytest.raises(AssertionError, match="use_attn_in"):
        wrapper.run_with_hooks(
            {"input_ids": [[1, 2]]},
            fwd_hooks=[("blocks.0.hook_attn_in", lambda **_kwargs: None)],
        )


def test_transformer_lens_compatible_wrapper_set_use_attn_in_rejects_gqa() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="swiss-ai/Apertus-8B-2509")
    wrapper.model = _FakeApertusModel()

    with pytest.raises(AssertionError, match="key/value heads are grouped"):
        wrapper.set_use_attn_in(True)

    wrapper.set_ungroup_grouped_query_attention(True)
    assert wrapper.cfg.ungroup_grouped_query_attention is True


def test_transformer_lens_compatible_wrapper_set_use_hook_mlp_in_rejects_attn_only() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()
    wrapper.model.config.attn_only = True

    with pytest.raises(AssertionError, match="attention-only"):
        wrapper.set_use_hook_mlp_in(True)


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


def test_transformer_lens_compatible_wrapper_exposes_gpt_bigcode_mqa_weights() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="bigcode/santacoder")
    wrapper.model = _FakeGptBigCodeModel()
    attention = wrapper.model.transformer.h[0].attn
    weight = attention.c_attn.weight

    expected_q = weight[:8].reshape(2, 4, 8).permute(0, 2, 1).unsqueeze(0)
    expected_k = weight[8:12].reshape(1, 4, 8).permute(0, 2, 1).unsqueeze(0)
    expected_v = weight[12:16].reshape(1, 4, 8).permute(0, 2, 1).unsqueeze(0)
    expected_o = attention.c_proj.weight.reshape(8, 2, 4).permute(1, 2, 0).unsqueeze(0)
    bias = attention.c_attn.bias

    assert (
        architecture_adapter_for_name(model_name="bigcode/santacoder").name == "gpt_bigcode_decoder"
    )
    assert torch.equal(wrapper.W_Q, expected_q)
    assert torch.equal(wrapper.W_K, expected_k)
    assert torch.equal(wrapper.W_V, expected_v)
    assert torch.equal(wrapper.W_O, expected_o)
    assert torch.equal(wrapper.b_Q, bias[:8].reshape(2, 4).unsqueeze(0))
    assert torch.equal(wrapper.b_K, bias[8:12].reshape(1, 4).unsqueeze(0))
    assert torch.equal(wrapper.b_V, bias[12:16].reshape(1, 4).unsqueeze(0))
    assert torch.equal(wrapper.b_O, attention.c_proj.bias.unsqueeze(0))

    assert wrapper.cfg.n_key_value_heads == 1
    assert torch.equal(wrapper.QK.B, expected_k.repeat_interleave(2, dim=1).transpose(-2, -1))
    assert tuple(wrapper.QK.shape) == (1, 2, 8, 8)


def test_transformer_lens_compatible_wrapper_gpt2_zero_mlp_bias_uses_conv1d_output_dim() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeGpt2Model()
    wrapper.model.transformer.h[0].mlp.c_fc.bias = None
    wrapper.model.transformer.h[0].mlp.c_proj.bias = None

    assert torch.equal(wrapper.b_in, torch.zeros(1, 3))
    assert torch.equal(wrapper.b_out, torch.zeros(1, 4))


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


def test_component_bridge_reshapes_joint_qkv_weights_for_tuple_backend() -> None:
    rows_weight = tuple(tuple(row * 10 + col for col in range(4)) for row in range(12))
    cols_weight = tuple(tuple(row * 100 + col for col in range(12)) for row in range(4))

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


def test_component_bridge_reshapes_grouped_interleaved_qkv_weights_for_list_backend() -> None:
    torch = pytest.importorskip("torch")
    rows_weight = torch.arange(8 * 3 * 5, dtype=torch.float32).reshape(8 * 3, 5)
    cols_weight = rows_weight.T.contiguous()

    for packed_axis, weight in ((0, rows_weight), (1, cols_weight)):
        for component in ("q", "k", "v"):
            expected = reshape_joint_qkv_attention_weight(
                weight,
                component=component,
                q_heads=4,
                kv_heads=2,
                qkv_layout="interleaved",
                packed_axis=packed_axis,
            )
            actual = reshape_joint_qkv_attention_weight(
                weight.tolist(),
                component=component,
                q_heads=4,
                kv_heads=2,
                qkv_layout="interleaved",
                packed_axis=packed_axis,
            )

            assert torch.equal(torch.tensor(actual, dtype=torch.float32), expected)


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


def test_transformer_lens_compatible_wrapper_fold_layer_norm_infers_neox_qkv_rows() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="EleutherAI/pythia-70m")
    wrapper.model = _FakeGptNeoxModel()
    layer = wrapper.model.gpt_neox.layers[0]
    layer.input_layernorm.weight = torch.tensor([1.0, 2.0, 3.0, 4.0])
    original_w_q = wrapper.W_Q[0].clone()
    expected_w_q = original_w_q * layer.input_layernorm.weight[None, :, None]
    expected_w_q = expected_w_q - expected_w_q.mean(dim=1, keepdim=True)

    assert wrapper.fold_layer_norm() is wrapper

    assert torch.allclose(wrapper.W_Q[0], expected_w_q)
    assert torch.equal(layer.input_layernorm.weight, torch.ones_like(layer.input_layernorm.weight))


def test_transformer_lens_compatible_wrapper_fold_layer_norm_folds_final_norm_into_hf_unembed() -> (
    None
):
    torch = pytest.importorskip("torch")
    ln_final = torch.nn.LayerNorm(2)
    with torch.no_grad():
        ln_final.weight.copy_(torch.tensor([2.0, 3.0]))
        ln_final.bias.copy_(torch.tensor([0.5, -1.0]))
    weight = torch.tensor([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
    bias = torch.tensor([0.1, 0.2, 0.3])
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeFinalNormUnembeddingModel(weight.clone(), bias.clone(), ln_final)
    expected_weight = weight * torch.tensor([2.0, 3.0])[None, :]
    expected_weight = expected_weight - expected_weight.mean(dim=-1, keepdim=True)
    expected_bias = bias + (weight * torch.tensor([0.5, -1.0])[None, :]).sum(dim=-1)

    assert wrapper.fold_layer_norm() is wrapper

    assert torch.allclose(wrapper.model._weight, expected_weight)
    assert torch.allclose(wrapper.W_U, expected_weight.T)
    assert torch.allclose(wrapper.model._bias, expected_bias)
    assert torch.equal(ln_final.weight, torch.ones_like(ln_final.weight))
    assert torch.equal(ln_final.bias, torch.zeros_like(ln_final.bias))


def test_wrapper_fold_layer_norm_folds_final_norm_into_native_unembed() -> None:
    torch = pytest.importorskip("torch")
    ln_final = torch.nn.LayerNorm(2)
    with torch.no_grad():
        ln_final.weight.copy_(torch.tensor([4.0, 5.0]))
        ln_final.bias.copy_(torch.tensor([1.5, -0.5]))
    weight = torch.tensor([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]])
    bias = torch.tensor([0.1, 0.2, 0.3])
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeNativeFinalNormUnembeddingModel(weight.clone(), bias.clone(), ln_final)
    expected_weight = weight * torch.tensor([4.0, 5.0])[:, None]
    expected_weight = expected_weight - expected_weight.mean(dim=0, keepdim=True)
    expected_bias = bias + (weight * torch.tensor([1.5, -0.5])[:, None]).sum(dim=0)

    assert wrapper.fold_layer_norm() is wrapper

    assert torch.allclose(wrapper.model.W_U, expected_weight)
    assert torch.allclose(wrapper.W_U, expected_weight)
    assert torch.allclose(wrapper.model.b_U, expected_bias)
    assert torch.equal(ln_final.weight, torch.ones_like(ln_final.weight))
    assert torch.equal(ln_final.bias, torch.zeros_like(ln_final.bias))


def test_wrapper_fold_layer_norm_does_not_create_final_unembed_bias() -> None:
    torch = pytest.importorskip("torch")
    ln_final = torch.nn.LayerNorm(2)
    with torch.no_grad():
        ln_final.weight.copy_(torch.tensor([2.0, 3.0]))
        ln_final.bias.copy_(torch.tensor([0.5, -1.0]))
    original_bias = ln_final.bias.detach().clone()
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeFinalNormUnembeddingModel(
        torch.tensor([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]),
        None,
        ln_final,
    )

    assert wrapper.fold_layer_norm() is wrapper

    assert wrapper.model._bias is None
    assert torch.equal(ln_final.bias, original_bias)


def test_wrapper_fold_layer_norm_does_not_create_native_final_unembed_bias() -> None:
    torch = pytest.importorskip("torch")
    ln_final = torch.nn.LayerNorm(2)
    with torch.no_grad():
        ln_final.weight.copy_(torch.tensor([4.0, 5.0]))
        ln_final.bias.copy_(torch.tensor([1.5, -0.5]))
    original_bias = ln_final.bias.detach().clone()
    wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    wrapper.model = _FakeNativeFinalNormUnembeddingModel(
        torch.tensor([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]]),
        None,
        ln_final,
    )

    assert wrapper.fold_layer_norm() is wrapper

    assert wrapper.model.b_U is None
    assert torch.equal(ln_final.bias, original_bias)


def test_transformer_lens_compatible_wrapper_fold_layer_norm_uses_offset_final_norm_scale() -> None:
    torch = pytest.importorskip("torch")
    ln_final = torch.nn.LayerNorm(2, elementwise_affine=True)
    with torch.no_grad():
        ln_final.weight.copy_(torch.tensor([1.0, 2.0]))
        ln_final.bias.zero_()
    weight = torch.tensor([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
    wrapper = TransformerLensCompatibleModelWrapper(name="google/gemma-2b")
    wrapper.model = _FakeFinalNormUnembeddingModel(weight.clone(), None, ln_final)
    wrapper.model.config = _FakeOffsetRmsConfig()
    expected_weight = weight * torch.tensor([2.0, 3.0])[None, :]

    assert wrapper.cfg.rmsnorm_uses_offset is True
    assert wrapper.fold_layer_norm(fold_biases=False, center_weights=False) is wrapper

    assert torch.allclose(wrapper.model._weight, expected_weight)
    assert torch.equal(ln_final.weight, torch.zeros_like(ln_final.weight))


def test_transformer_lens_compatible_wrapper_exposes_embeddings_from_architecture_paths() -> None:
    torch = pytest.importorskip("torch")

    neox_wrapper = TransformerLensCompatibleModelWrapper(name="EleutherAI/pythia-70m")
    neox_wrapper.model = _FakeGptNeoxModel()
    assert torch.equal(neox_wrapper.W_E, neox_wrapper.model.gpt_neox.embed_in.weight)

    falcon_wrapper = TransformerLensCompatibleModelWrapper(name="tiiuae/falcon-7b")
    falcon_wrapper.model = _FakeFalconMQAModel()
    assert torch.equal(
        falcon_wrapper.W_E,
        falcon_wrapper.model.transformer.word_embeddings.weight,
    )

    opt_wrapper = TransformerLensCompatibleModelWrapper(name="facebook/opt-125m")
    opt_wrapper.model = _FakeOptModel()
    decoder = opt_wrapper.model.model.decoder
    assert torch.equal(opt_wrapper.W_E, decoder.embed_tokens.weight)
    assert torch.equal(opt_wrapper.W_pos, decoder.embed_positions.weight)

    apertus_wrapper = TransformerLensCompatibleModelWrapper(name="swiss-ai/Apertus-8B-2509")
    apertus_wrapper.model = _FakeApertusModel()
    assert torch.equal(apertus_wrapper.W_E, apertus_wrapper.model.model.embed_tokens.weight)
    with pytest.raises(KeyError, match="positional embedding"):
        _ = apertus_wrapper.W_pos


def test_transformer_lens_compatible_wrapper_exposes_mlp_weights_from_adapter_specs() -> None:
    torch = pytest.importorskip("torch")

    gpt2_wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    gpt2_wrapper.model = _FakeGpt2Model()
    gpt2_mlp = gpt2_wrapper.model.transformer.h[0].mlp
    assert torch.equal(gpt2_wrapper.W_in, gpt2_mlp.c_fc.weight.unsqueeze(0))
    assert torch.equal(gpt2_wrapper.W_out, gpt2_mlp.c_proj.weight.unsqueeze(0))
    assert torch.equal(gpt2_wrapper.b_in, gpt2_mlp.c_fc.bias.unsqueeze(0))
    assert torch.equal(gpt2_wrapper.b_out, gpt2_mlp.c_proj.bias.unsqueeze(0))

    bigcode_wrapper = TransformerLensCompatibleModelWrapper(name="bigcode/santacoder")
    bigcode_wrapper.model = _FakeGptBigCodeModel()
    bigcode_mlp = bigcode_wrapper.model.transformer.h[0].mlp
    assert torch.equal(bigcode_wrapper.W_in, bigcode_mlp.c_fc.weight.T.unsqueeze(0))
    assert torch.equal(bigcode_wrapper.W_out, bigcode_mlp.c_proj.weight.T.unsqueeze(0))
    assert torch.equal(bigcode_wrapper.b_in, bigcode_mlp.c_fc.bias.unsqueeze(0))
    assert torch.equal(bigcode_wrapper.b_out, bigcode_mlp.c_proj.bias.unsqueeze(0))

    apertus_wrapper = TransformerLensCompatibleModelWrapper(name="swiss-ai/Apertus-8B-2509")
    apertus_wrapper.model = _FakeApertusModel()
    apertus_mlp = apertus_wrapper.model.model.layers[0].mlp
    assert torch.equal(apertus_wrapper.W_in, apertus_mlp.up_proj.weight.T.unsqueeze(0))
    assert torch.equal(apertus_wrapper.W_out, apertus_mlp.down_proj.weight.T.unsqueeze(0))
    assert torch.equal(apertus_wrapper.b_in, apertus_mlp.up_proj.bias.unsqueeze(0))
    assert torch.equal(apertus_wrapper.b_out, apertus_mlp.down_proj.bias.unsqueeze(0))

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

    bert_wrapper = TransformerLensCompatibleModelWrapper(name="google-bert/bert-base-uncased")
    bert_wrapper.model = _FakeWeightedBertModel()
    bert_layer = bert_wrapper.model.encoder.layer[0]
    assert torch.equal(bert_wrapper.W_in, bert_layer.intermediate.dense.weight.T.unsqueeze(0))
    assert torch.equal(bert_wrapper.W_out, bert_layer.output.dense.weight.T.unsqueeze(0))
    assert torch.equal(bert_wrapper.b_in, bert_layer.intermediate.dense.bias.unsqueeze(0))
    assert torch.equal(bert_wrapper.b_out, bert_layer.output.dense.bias.unsqueeze(0))

    distilbert_wrapper = TransformerLensCompatibleModelWrapper(name="distilbert-base-uncased")
    distilbert_wrapper.model = _FakeWeightedDistilBertModel()
    distilbert_ffn = distilbert_wrapper.model.transformer.layer[0].ffn
    assert torch.equal(distilbert_wrapper.W_in, distilbert_ffn.lin1.weight.T.unsqueeze(0))
    assert torch.equal(distilbert_wrapper.W_out, distilbert_ffn.lin2.weight.T.unsqueeze(0))
    assert torch.equal(distilbert_wrapper.b_in, distilbert_ffn.lin1.bias.unsqueeze(0))
    assert torch.equal(distilbert_wrapper.b_out, distilbert_ffn.lin2.bias.unsqueeze(0))

    t5_wrapper = TransformerLensCompatibleModelWrapper(name="google-t5/t5-small")
    t5_wrapper.model = _FakeWeightedT5Model()
    t5_ffn = t5_wrapper.model.encoder.block[0].layer[1].DenseReluDense
    assert torch.equal(t5_wrapper.W_in, t5_ffn.wi.weight.T.unsqueeze(0))
    assert torch.equal(t5_wrapper.W_out, t5_ffn.wo.weight.T.unsqueeze(0))
    assert torch.equal(
        t5_wrapper.b_in,
        torch.zeros(t5_ffn.wi.weight.shape[0], dtype=torch.float32).unsqueeze(0),
    )
    assert torch.equal(
        t5_wrapper.b_out,
        torch.zeros(t5_ffn.wo.weight.shape[0], dtype=torch.float32).unsqueeze(0),
    )


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
    assert torch.equal(
        wrapper.W_E_pos, torch.cat([model.embed_tokens.weight, model.wpe.weight], dim=0)
    )
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
    assert wrapper.W_in == [[[100, 110, 120], [101, 111, 121], [102, 112, 122], [103, 113, 123]]]
    assert wrapper.W_gate == [[[0, 10, 20], [1, 11, 21], [2, 12, 22], [3, 13, 23]]]
    assert wrapper.W_out == [[[30, 40, 50, 60], [31, 41, 51, 61], [32, 42, 52, 62]]]
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


def test_transformer_lens_compatible_wrapper_exposes_transformerlens_parameter_map() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeListWeightedQwenModel()
    torch = pytest.importorskip("torch")
    layer = wrapper.model.model.layers[0]
    layer.post_attention_layernorm.weight = torch.tensor([0.5, 1.5, 2.5, 3.5])

    params = wrapper.tl_parameters()

    assert params["embed.W_E"] == wrapper.W_E
    assert params["pos_embed.W_pos"] == wrapper.W_pos
    assert "unembed.W_U" not in params
    assert params["blocks.0.attn.W_Q"] == wrapper.W_Q[0]
    assert params["blocks.0.attn.W_K"] == wrapper.W_K[0]
    assert params["blocks.0.attn.W_V"] == wrapper.W_V[0]
    assert params["blocks.0.attn.W_O"] == wrapper.W_O[0]
    assert params["blocks.0.attn.b_Q"] == wrapper.b_Q[0]
    assert params["blocks.0.attn.b_O"] == wrapper.b_O[0]
    assert params["blocks.0.mlp.W_in"] == wrapper.W_in[0]
    assert params["blocks.0.mlp.W_gate"] == wrapper.W_gate[0]
    assert params["blocks.0.mlp.W_out"] == wrapper.W_out[0]
    assert params["blocks.0.mlp.b_in"] == wrapper.b_in[0]
    assert params["blocks.0.mlp.b_out"] == wrapper.b_out[0]
    assert torch.equal(params["blocks.0.ln2.w"], layer.post_attention_layernorm.weight)

    unembed_wrapper = TransformerLensCompatibleModelWrapper(name="gpt2")
    unembed_wrapper.model = _FakeUnembeddingModel([[1, 10], [2, 20], [3, 30]], [1, 2, 3])
    unembed_params = unembed_wrapper.tl_parameters()
    assert unembed_params["unembed.W_U"] == unembed_wrapper.W_U
    assert unembed_params["unembed.b_U"] == unembed_wrapper.b_U


def test_transformer_lens_parameter_map_preserves_sparse_layernorm_indices() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    wrapper.model.model.layers.append(_FakeWeightedLayer())
    wrapper.model.model.layers[0].post_attention_layernorm.weight = None
    wrapper.model.model.layers[1].post_attention_layernorm.weight = torch.tensor(
        [1.0, 2.0, 3.0, 4.0]
    )

    params = wrapper.tl_parameters()

    assert "blocks.0.ln2.w" not in params
    assert torch.equal(
        params["blocks.1.ln2.w"],
        wrapper.model.model.layers[1].post_attention_layernorm.weight,
    )


def test_svd_interpreter_projects_wrapper_circuit_singular_vectors() -> None:
    torch = pytest.importorskip("torch")

    class SvdConfig:
        n_layers = 1
        n_heads = 1
        d_vocab = 2

    class SvdModel:
        cfg = SvdConfig()

        def tl_parameters(self) -> dict[str, Any]:
            return {
                "blocks.0.attn.W_V": torch.tensor([[[2.0, 0.0], [0.0, 1.0]]]),
                "blocks.0.attn.W_O": torch.eye(2).unsqueeze(0),
                "blocks.0.mlp.W_in": torch.tensor([[3.0, 0.0], [0.0, 1.0]]),
                "blocks.0.mlp.W_out": torch.tensor([[4.0, 0.0], [0.0, 1.0]]),
                "unembed.W_U": torch.eye(2),
            }

    interpreter = SVDInterpreter(SvdModel())

    ov_vectors = interpreter.get_singular_vectors("OV", layer_index=0, head_index=0, num_vectors=2)
    w_in_vectors = interpreter.get_singular_vectors("w_in", layer_index=0, num_vectors=2)
    w_out_vectors = interpreter.get_singular_vectors("w_out", layer_index=0, num_vectors=2)

    expected = torch.tensor([[[1.0, 0.0]], [[0.0, 1.0]]])
    assert torch.allclose(ov_vectors, expected)
    assert torch.allclose(w_in_vectors, expected)
    assert torch.allclose(w_out_vectors, expected)
    assert interpreter.get_singular_vectors(
        "OV", layer_index=0, head_index=0, num_vectors=0
    ).shape == (
        2,
        1,
        0,
    )
    with pytest.raises(AssertionError, match="Head index optional"):
        interpreter.get_singular_vectors("OV", layer_index=0)
    assert torch.allclose(
        interpreter.get_singular_vectors("w_in", layer_index=0, head_index=0, num_vectors=2),
        expected,
    )


def test_svd_interpreter_uses_wrapper_layernorm_weight_for_w_in_vectors() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedQwenModel()
    wrapper.model.config.vocab_size = 4
    layer = wrapper.model.model.layers[0]
    layer.post_attention_layernorm.weight = torch.tensor([1.0, 2.0, 3.0, 4.0])
    wrapper.model.get_output_embeddings = lambda: _FakeEmbedding(
        torch.tensor(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
    )

    params = wrapper.tl_parameters()
    matrix = params["blocks.0.mlp.W_in"].T * params["blocks.0.ln2.w"]
    _u, _s, vh = torch.linalg.svd(matrix)
    expected = torch.stack(
        [vh[index].float() @ params["unembed.W_U"] for index in range(2)], dim=1
    ).unsqueeze(1)

    vectors = SVDInterpreter(wrapper).get_singular_vectors("w_in", layer_index=0, num_vectors=2)

    assert torch.allclose(vectors, expected)


def test_svd_interpreter_accepts_mixed_backend_layernorm_weight() -> None:
    torch = pytest.importorskip("torch")

    class SvdConfig:
        n_layers = 1
        n_heads = 1
        d_vocab = 2

    class SvdModel:
        cfg = SvdConfig()

        def tl_parameters(self) -> dict[str, Any]:
            return {
                "blocks.0.attn.W_V": torch.eye(2).unsqueeze(0),
                "blocks.0.attn.W_O": torch.eye(2).unsqueeze(0),
                "blocks.0.mlp.W_in": torch.tensor([[3.0, 0.0], [0.0, 1.0]]),
                "blocks.0.mlp.W_out": torch.tensor([[4.0, 0.0], [0.0, 1.0]]),
                "blocks.0.ln2.w": [1.0, 2.0],
                "unembed.W_U": torch.eye(2),
            }

    params = SvdModel().tl_parameters()
    matrix = params["blocks.0.mlp.W_in"].T * torch.tensor(params["blocks.0.ln2.w"])
    _u, _s, vh = torch.linalg.svd(matrix)
    expected = torch.stack(
        [vh[index].float() @ params["unembed.W_U"] for index in range(2)], dim=1
    ).unsqueeze(1)

    vectors = SVDInterpreter(SvdModel()).get_singular_vectors("w_in", layer_index=0, num_vectors=2)

    assert isinstance(vectors, torch.Tensor)
    assert torch.allclose(vectors, expected)


def test_svd_interpreter_projects_low_precision_torch_parameters_without_list_fallback() -> None:
    torch = pytest.importorskip("torch")

    class SvdConfig:
        n_layers = 1
        n_heads = 1
        d_vocab = 2

    class SvdModel:
        cfg = SvdConfig()

        def tl_parameters(self) -> dict[str, Any]:
            return {
                "blocks.0.attn.W_V": torch.eye(2, dtype=torch.float16).unsqueeze(0),
                "blocks.0.attn.W_O": torch.eye(2, dtype=torch.float16).unsqueeze(0),
                "blocks.0.mlp.W_in": torch.eye(2, dtype=torch.float16),
                "blocks.0.mlp.W_out": torch.eye(2, dtype=torch.float16),
                "unembed.W_U": torch.eye(2, dtype=torch.float16),
            }

    interpreter = SVDInterpreter(SvdModel())

    vector_cases: tuple[tuple[Literal["OV", "w_in", "w_out"], dict[str, Any]], ...] = (
        ("OV", {"head_index": 0}),
        ("w_in", {}),
        ("w_out", {}),
    )
    for vector_type, kwargs in vector_cases:
        vectors = interpreter.get_singular_vectors(
            vector_type, layer_index=0, num_vectors=2, **kwargs
        )

        assert isinstance(vectors, torch.Tensor)
        assert vectors.dtype == torch.float32
        assert tuple(vectors.shape) == (2, 1, 2)


def test_svd_interpreter_uses_wrapper_ov_circuit_for_grouped_query_heads() -> None:
    torch = pytest.importorskip("torch")

    class GqaConfig:
        n_layers = 1
        n_heads = 4
        d_vocab = 8

    class GqaModel:
        cfg = GqaConfig()

        @property
        def OV(self) -> FactoredMatrix:
            w_v = torch.tensor(
                [
                    [
                        [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 0.0]],
                        [[2.0, 0.0], [0.0, 2.0], [1.0, 3.0], [4.0, 1.0]],
                        [[3.0, 1.0], [1.0, 3.0], [2.0, 4.0], [5.0, 2.0]],
                        [[4.0, 1.0], [1.0, 4.0], [3.0, 5.0], [6.0, 2.0]],
                    ]
                ]
            )
            w_o = torch.arange(1, 1 + 4 * 2 * 4, dtype=torch.float32).reshape(1, 4, 2, 4)
            return FactoredMatrix(w_v, w_o)

        def tl_parameters(self) -> dict[str, Any]:
            return {
                "blocks.0.attn.W_V": torch.zeros(2, 4, 2),
                "blocks.0.attn.W_O": torch.zeros(4, 2, 4),
                "unembed.W_U": torch.eye(4, 8),
            }

    interpreter = SVDInterpreter(GqaModel())
    vectors = interpreter.get_singular_vectors("OV", layer_index=0, head_index=2, num_vectors=2)
    expected = interpreter._get_singular_vectors_from_matrix(
        transpose(interpreter.model.OV[0, 2].V),
        interpreter.params["unembed.W_U"],
        2,
    )

    assert tuple(vectors.shape) == (8, 1, 2)
    assert torch.allclose(vectors, expected)


def test_svd_interpreter_supports_list_backed_parameters() -> None:
    class SvdConfig:
        n_layers = 1
        n_heads = 1
        d_vocab = 2

    class SvdModel:
        cfg = SvdConfig()

        def tl_parameters(self) -> dict[str, Any]:
            return {
                "blocks.0.attn.W_V": [[[2.0, 0.0], [0.0, 1.0]]],
                "blocks.0.attn.W_O": [[[1.0, 0.0], [0.0, 1.0]]],
                "blocks.0.mlp.W_in": [[3.0, 0.0], [0.0, 1.0]],
                "blocks.0.mlp.W_out": [[4.0, 0.0], [0.0, 1.0]],
                "unembed.W_U": [[1.0, 0.0], [0.0, 1.0]],
            }

    interpreter = SVDInterpreter(SvdModel())

    assert interpreter.get_singular_vectors("OV", 0, head_index=0, num_vectors=2) == [
        [[1.0, 0.0]],
        [[0.0, 1.0]],
    ]
    assert interpreter.get_singular_vectors("OV", 0, head_index=0, num_vectors=0) == [
        [[]],
        [[]],
    ]


def test_svd_interpreter_handles_non_diagonal_lists_without_optional_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_torch_and_numpy_imports(monkeypatch)

    class SvdConfig:
        n_layers = 1
        n_heads = 1
        d_vocab = 2

    class SvdModel:
        cfg = SvdConfig()

        def tl_parameters(self) -> dict[str, Any]:
            return {
                "blocks.0.attn.W_V": [[[1.0, 0.0], [0.0, 1.0]]],
                "blocks.0.attn.W_O": [[[1.0, 0.0], [0.0, 1.0]]],
                "blocks.0.mlp.W_in": [[2.0, 1.0], [1.0, 2.0]],
                "blocks.0.mlp.W_out": [[2.0, 1.0], [1.0, 2.0]],
                "unembed.W_U": [[1.0, 0.0], [0.0, 1.0]],
            }

    vectors = SVDInterpreter(SvdModel()).get_singular_vectors(
        "w_out",
        layer_index=0,
        num_vectors=2,
    )

    root_half = 0.5**0.5
    assert vectors[0][0][0] == pytest.approx(root_half)
    assert vectors[0][0][1] == pytest.approx(root_half)
    assert vectors[1][0][0] == pytest.approx(root_half)
    assert vectors[1][0][1] == pytest.approx(-root_half)


def test_transformer_lens_compatible_wrapper_exposes_tuple_backed_circuit_helpers() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeTupleWeightedQwenModel()
    list_wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    list_wrapper.model = _FakeListWeightedQwenModel()

    assert _tuplify_nested(list_wrapper.W_E) == wrapper.W_E
    assert wrapper.W_E_pos == list_wrapper.W_E_pos
    assert wrapper.W_Q == list_wrapper.W_Q
    assert wrapper.W_K == list_wrapper.W_K
    assert wrapper.W_V == list_wrapper.W_V
    assert wrapper.W_O == list_wrapper.W_O
    assert wrapper.b_Q == list_wrapper.b_Q
    assert wrapper.b_O == list_wrapper.b_O
    assert wrapper.accumulated_bias(0) == [0, 0, 0, 0]
    assert wrapper.accumulated_bias(0, mlp_input=True) == [12, 13, 14, 15]
    assert wrapper.accumulated_bias(1) == [16, 18, 20, 22]
    assert wrapper.QK.AB == list_wrapper.QK.AB
    assert wrapper.OV.AB == list_wrapper.OV.AB
    assert wrapper.all_composition_scores("V") == list_wrapper.all_composition_scores("V")


def test_transformer_lens_compatible_wrapper_caches_attention_pattern() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_pattern"],
    )

    assert output["output_attentions"] is True
    assert getattr(cache["blocks.0.attn.hook_pattern"], "ndim", None) == 4


def test_transformer_lens_compatible_wrapper_uses_eager_attention_for_bert_patterns() -> None:
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    config = transformers.BertConfig(
        vocab_size=32,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=1,
        num_attention_heads=4,
    )
    model = transformers.BertModel(config)
    original_attention = model.config._attn_implementation
    wrapper = TransformerLensCompatibleModelWrapper(name="google-bert/bert-base-uncased")
    wrapper.model = model

    _output, cache = wrapper.run_with_cache(
        {"input_ids": torch.tensor([[1, 2, 3]])},
        layers=["blocks.0.attn.hook_pattern", "blocks.0.attn.hook_attn_scores"],
    )

    assert tuple(cache["blocks.0.attn.hook_pattern"].shape) == (1, 4, 3, 3)
    assert tuple(cache["blocks.0.attn.hook_attn_scores"].shape) == (1, 4, 3, 3)
    assert model.config._attn_implementation == original_attention


def test_transformer_lens_compatible_wrapper_restores_missing_attention_implementation() -> None:
    pytest.importorskip("torch")

    class _EagerSwitchQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.attention_calls: list[Any] = []

        def set_attn_implementation(self, value: Any) -> None:
            self.attention_calls.append(value)
            self.config._attn_implementation = value

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _EagerSwitchQwenModel()

    wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_pattern"],
    )

    assert wrapper.model.attention_calls == ["eager"]
    assert not hasattr(wrapper.model.config, "_attn_implementation")


def test_transformer_lens_compatible_wrapper_restores_none_attention_implementation() -> None:
    pytest.importorskip("torch")

    class _EagerSwitchQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.config._attn_implementation = None
            self.attention_calls: list[Any] = []

        def set_attn_implementation(self, value: Any) -> None:
            self.attention_calls.append(value)
            self.config._attn_implementation = value

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _EagerSwitchQwenModel()

    wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_pattern"],
    )

    assert wrapper.model.attention_calls == ["eager", None]
    assert wrapper.model.config._attn_implementation is None


def test_wrapper_restores_attention_implementation_after_failed_switch() -> None:
    pytest.importorskip("torch")

    class _FailingEagerSwitchQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            self.attention_calls: list[Any] = []

        def set_attn_implementation(self, value: Any) -> None:
            self.attention_calls.append(value)
            self.config._attn_implementation = value
            raise RuntimeError("unsupported attention backend")

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FailingEagerSwitchQwenModel()

    wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_pattern"],
    )

    assert wrapper.model.attention_calls == ["eager"]
    assert not hasattr(wrapper.model.config, "_attn_implementation")


def test_transformer_lens_compatible_wrapper_caches_mlp_post_for_neuron_decomposition() -> None:
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeWeightedNeuronQwenModel()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.mlp.hook_post"],
        return_cache_object=True,
    )

    assert output == {"post": [[[3.0, 4.0, 5.0]]]}
    assert isinstance(cache, ActivationCache)
    assert cache["layer_0.post"] == [[[3.0, 4.0, 5.0]]]
    torch = pytest.importorskip("torch")
    expected = torch.tensor([[[[36.0, 45.0, 54.0, 63.0], [70.0, 85.0, 100.0, 115.0]]]])
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
        fwd_hooks=[("blocks.0.mlp.hook_pre_linear", lambda **_kwargs: [[[40.0, 50.0, 60.0]]])],
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
    wrapper.set_use_attn_result(True)
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


def test_attention_softmax_cache_records_patched_scores_when_patch_hook_runs_first() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    scores = torch.zeros(1, 2, 2, 2)
    scores[..., 1] = 1.0

    def force_first_source(**kwargs: Any) -> Any:
        patched = torch.full_like(kwargs["activation"], -1000.0)
        patched[..., 0] = 1000.0
        return patched

    wrapper.add_hook("blocks.0.attn.hook_attn_scores", force_first_source)

    _output, cache = wrapper.run_with_cache(
        {"scores": scores},
        layers=[
            "blocks.0.attn.hook_attn_scores",
            "blocks.0.attn.hook_pattern",
        ],
    )

    expected_scores = torch.full_like(scores, -1000.0)
    expected_scores[..., 0] = 1000.0
    assert torch.equal(cache["blocks.0.attn.hook_attn_scores"], expected_scores)
    assert torch.allclose(
        cache["blocks.0.attn.hook_pattern"], torch.softmax(expected_scores, dim=-1)
    )


def test_attention_softmax_persistent_cache_records_original_scores_when_installed_first() -> None:
    torch = pytest.importorskip("torch")
    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeQwenModel()
    scores = torch.zeros(1, 2, 2, 2)
    scores[..., 1] = 1.0
    cache = wrapper.add_caching_hooks(
        layers=[
            "blocks.0.attn.hook_attn_scores",
            "blocks.0.attn.hook_pattern",
        ]
    )

    def force_first_source(**kwargs: Any) -> Any:
        patched = torch.full_like(kwargs["activation"], -1000.0)
        patched[..., 0] = 1000.0
        return patched

    wrapper.add_hook("blocks.0.attn.hook_attn_scores", force_first_source)
    wrapper._run_model_forward({"scores": scores}, return_type=None, loss_per_token=False)

    expected_pattern = torch.zeros_like(scores)
    expected_pattern[..., 0] = 1.0
    assert torch.equal(cache["blocks.0.attn.hook_attn_scores"], scores)
    assert torch.equal(cache["blocks.0.attn.hook_pattern"], expected_pattern)
    wrapper.remove_hooks()


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

    handle = wrapper.add_hook(
        "blocks.0.attn.hook_q", lambda **kwargs: kwargs["activation"] + ["patched"]
    )
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


def test_attention_softmax_hook_ignores_non_attention_softmax_inside_attention_module() -> None:
    torch = pytest.importorskip("torch")

    class _AttentionWithAuxiliarySoftmaxQwenModel(_FakeQwenModel):
        def __init__(self) -> None:
            super().__init__()
            attention = self.model.layers[0].self_attn
            original_forward = attention.forward

            def forward(scores: Any | None = None) -> Any:
                _ = torch.softmax(torch.zeros(1, 2, 3), dim=-1)
                return original_forward(scores)

            attention.forward = forward

    wrapper = TransformerLensCompatibleModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _AttentionWithAuxiliarySoftmaxQwenModel()
    seen_shapes: list[tuple[int, ...]] = []

    wrapper.add_hook(
        "blocks.0.attn.hook_attn_scores",
        lambda **kwargs: seen_shapes.append(tuple(kwargs["activation"].shape)),
    )
    wrapper.model.model.layers[0].self_attn.forward(torch.randn(1, 2, 3, 3))

    assert seen_shapes == [(1, 2, 3, 3)]


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


def test_component_bridge_preserves_list_module_outputs_when_replacing_payload() -> None:
    spec = ComponentHookSpec(
        component="resid_post",
        mode="forward_output",
        module_paths=("unused",),
        value="output",
    )
    output = [[[1, 2]], {"metadata": True}]

    assert extract_component_activation(output, spec, _FakeHeadModel()) == [[1, 2]]
    assert replace_component_activation(output, [[9, 9]], spec, _FakeHeadModel()) == [
        [[9, 9]],
        {"metadata": True},
    ]


def test_component_bridge_attention_pattern_skips_present_key_value_cache() -> None:
    torch = pytest.importorskip("torch")
    spec = ComponentHookSpec(
        component="pattern",
        mode="forward_output",
        module_paths=("unused",),
        value="attention_pattern",
    )
    key_cache = torch.full((1, 2, 3, 4), 7.0)
    value_cache = torch.full((1, 2, 3, 4), 8.0)
    pattern = torch.full((1, 2, 3, 3), 0.25)
    output = (torch.zeros(1, 3, 8), (key_cache, value_cache), pattern)

    activation = extract_component_activation(output, spec, _FakeHeadModel())

    assert torch.equal(activation, pattern)


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

    assert merged == [
        [[0, 1, 2, 3, 4, 5, 6, 7, -7, -7, -7, -7, -8, -8, -8, -8, 16, 17, 18, 19, 20, 21, 22, 23]]
    ]


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

    assert merged == [
        [[0, 1, 2, 3, 4, 5, 6, 7, -3, -3, -3, -3, 12, 13, 14, 15, 16, 17, 18, 19, -4, -4, -4, -4]]
    ]


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
            [
                [
                    [
                        -4,
                        -4,
                        -4,
                        -4,
                        -5,
                        -5,
                        -5,
                        -5,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        -6,
                        -6,
                        -6,
                        -6,
                        -7,
                        -7,
                        -7,
                        -7,
                        24,
                        25,
                        26,
                        27,
                        28,
                        29,
                        30,
                        31,
                    ]
                ]
            ],
        ),
        (
            "k",
            [[[[8, 9, 10, 11], [24, 25, 26, 27]]]],
            [[[[-8, -8, -8, -8], [-9, -9, -9, -9]]]],
            [
                [
                    [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        -8,
                        -8,
                        -8,
                        -8,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                        22,
                        23,
                        -9,
                        -9,
                        -9,
                        -9,
                        28,
                        29,
                        30,
                        31,
                    ]
                ]
            ],
        ),
        (
            "v",
            [[[[12, 13, 14, 15], [28, 29, 30, 31]]]],
            [[[[-10, -10, -10, -10], [-11, -11, -11, -11]]]],
            [
                [
                    [
                        0,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        -10,
                        -10,
                        -10,
                        -10,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                        22,
                        23,
                        24,
                        25,
                        26,
                        27,
                        -11,
                        -11,
                        -11,
                        -11,
                    ]
                ]
            ],
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
