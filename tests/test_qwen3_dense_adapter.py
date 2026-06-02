from __future__ import annotations

from typing import Any

import pytest

from SafeLens.core.analysis import zero_ablation_hook
from SafeLens.core.base import PipelineConfig
from SafeLens.core.hooks import ActivationCache
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
    def __init__(self, weight: Any | None = None) -> None:
        self.forward_hooks: list[Any] = []
        self.pre_hooks: list[Any] = []
        self.weight = weight

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
        torch = pytest.importorskip("torch")
        self.o_proj = _FakeModule(torch.arange(16, dtype=torch.float32).reshape(4, 4))

    def forward(self, scores: Any | None = None) -> Any:
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
        self.input_layernorm = _FakeModule()
        self.post_attention_layernorm = _FakeModule()
        self.self_attn = _FakeAttention()
        self.mlp = _FakeModule()


class _FakeConfig:
    model_type = "qwen3"
    num_attention_heads = 2
    num_key_value_heads = 1
    _attn_implementation = "sdpa"


class _FakeBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeLayer()]


class _FakeQwen3CausalLM:
    def __init__(self) -> None:
        self.model = _FakeBackbone()
        self.config = _FakeConfig()
        self.attn_implementation_calls: list[str] = []

    def set_attn_implementation(self, value: str) -> None:
        self.attn_implementation_calls.append(value)
        self.config._attn_implementation = value

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        if kwargs.get("output_attentions"):
            output = self.model.layers[0].self_attn.forward(kwargs.get("scores"))
            return {"attention": output, "output_attentions": True}
        if "z" in kwargs:
            attn_out = self.model.layers[0].self_attn.project(kwargs["z"])
            return {"attn_out": attn_out}
        mlp = self.model.layers[0].mlp
        first = mlp.run_forward(["first"])
        second = mlp.run_forward(["second"])
        return {"first": first, "second": second}


class _FakeGatedMlp:
    def __init__(self) -> None:
        self.gate_proj = _FakeModule()
        self.up_proj = _FakeModule()
        self.down_proj = _FakeModule()


class _FakeGatedLayer(_FakeLayer):
    def __init__(self) -> None:
        super().__init__()
        self.mlp = _FakeGatedMlp()


class _FakeGatedBackbone:
    def __init__(self) -> None:
        self.layers = [_FakeGatedLayer()]


class _FakeGatedQwen3CausalLM(_FakeQwen3CausalLM):
    def __init__(self) -> None:
        self.model = _FakeGatedBackbone()
        self.config = _FakeConfig()

    def __call__(self, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        mlp = self.model.layers[0].mlp
        gate = mlp.gate_proj.run_forward(["gate"])
        linear = mlp.up_proj.run_forward(["linear"])
        post = mlp.down_proj.run_pre(["post"])
        return {"gate": gate, "linear": linear, "post": post}


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
    assert parse_qwen3_component_ref("blocks.4.mlp.hook_pre") == (4, "pre")
    assert parse_qwen3_component_ref("blocks.5.mlp.hook_pre_linear") == (5, "pre_linear")
    assert parse_qwen3_component_ref("blocks.6.mlp.hook_post") == (6, "post")
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


def test_qwen3_gated_mlp_internal_hooks_patch_pre_linear_and_post() -> None:
    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeGatedQwen3CausalLM()

    wrapper.add_hook("blocks.0.mlp.hook_pre", lambda **kwargs: kwargs["activation"] + ["pre"])
    wrapper.add_hook(
        "blocks.0.mlp.hook_pre_linear",
        lambda **kwargs: kwargs["activation"] + ["pre_linear"],
    )
    wrapper.add_hook("blocks.0.mlp.hook_post", lambda **kwargs: kwargs["activation"] + ["post"])

    output = wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]

    assert output == {
        "gate": ["gate", "pre"],
        "linear": ["linear", "pre_linear"],
        "post": ["post", "post"],
    }


def test_qwen3_run_with_cache_captures_gated_mlp_pre_linear() -> None:
    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _FakeGatedQwen3CausalLM()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.mlp.hook_pre_linear"],
    )

    assert output == {"gate": ["gate"], "linear": ["linear"], "post": ["post"]}
    assert cache == {"blocks.0.mlp.hook_pre_linear": ["linear"]}


def test_qwen3_component_hooks_accept_standard_activation_hook_signature() -> None:
    wrapper = _wrapper_with_fake_model()
    layer = wrapper.model.model.layers[0]

    wrapper.add_hook("layer_0.mlp_out", zero_ablation_hook)

    assert layer.mlp.run_forward([1, 2, 3]) == [0, 0, 0]


def test_qwen3_component_hooks_receive_transformerlens_hook_context() -> None:
    wrapper = _wrapper_with_fake_model()
    layer = wrapper.model.model.layers[0]
    seen: list[tuple[str, int]] = []

    def append_hook_metadata(activation: Any, hook: Any) -> Any:
        seen.append((hook.name, hook.layer()))
        hook.ctx["seen"] = True
        return activation + [hook.name, hook.layer(), hook.ctx["seen"]]

    wrapper.add_hook("layer_0.mlp_out", append_hook_metadata)

    assert layer.mlp.run_forward(["x"]) == ["x", "blocks.0.hook_mlp_out", 0, True]
    assert seen == [("blocks.0.hook_mlp_out", 0)]


def test_qwen3_component_hooks_accept_positional_activation_with_extra_kwargs() -> None:
    wrapper = _wrapper_with_fake_model()
    layer = wrapper.model.model.layers[0]

    def append_metadata(value: list[str], **kwargs: Any) -> list[str]:
        return value + [kwargs["component"], kwargs["hook"].name]

    wrapper.add_hook("layer_0.mlp_out", append_metadata)

    assert layer.mlp.run_forward(["x"]) == ["x", "mlp_out", "blocks.0.hook_mlp_out"]


def test_qwen3_component_hooks_propagate_internal_type_errors_with_alternate_names() -> None:
    wrapper = _wrapper_with_fake_model()
    layer = wrapper.model.model.layers[0]

    def broken(value: list[str], point: Any) -> list[str]:
        _ = value, point
        raise TypeError("qwen3 hook inner bug")

    wrapper.add_hook("layer_0.mlp_out", broken)

    with pytest.raises(TypeError, match="qwen3 hook inner bug"):
        layer.mlp.run_forward(["x"])


def test_qwen3_component_hook_context_persists_across_calls() -> None:
    wrapper = _wrapper_with_fake_model()

    def count_calls(activation: Any, hook: Any) -> Any:
        hook.ctx["count"] = hook.ctx.get("count", 0) + 1
        return activation + [hook.ctx["count"]]

    wrapper.add_hook("layer_0.mlp_out", count_calls)

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first", 1],
        "second": ["second", 2],
    }
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first", 3],
        "second": ["second", 4],
    }


def test_qwen3_run_with_hooks_does_not_keep_temporary_handles() -> None:
    wrapper = _wrapper_with_fake_model()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert output == {"first": ["first", "patched"], "second": ["second", "patched"]}
    assert wrapper._hooks == []
    assert wrapper.model.model.layers[0].mlp.run_forward(["x"]) == ["x"]


def test_qwen3_run_with_hooks_callable_filters_with_no_matches_are_noops() -> None:
    wrapper = _wrapper_with_fake_model()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[(lambda _name: False, lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert output == {"first": ["first"], "second": ["second"]}
    assert wrapper._hooks == []


def test_qwen3_run_with_hooks_prepends_temporary_hook() -> None:
    wrapper = _wrapper_with_fake_model()

    wrapper.add_hook(
        "layer_0.mlp_out",
        lambda **kwargs: kwargs["activation"] + ["permanent"],
    )
    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[
            (
                "layer_0.mlp_out",
                lambda **kwargs: kwargs["activation"] + ["temporary"],
            )
        ],
        prepend=True,
    )

    assert output == {
        "first": ["first", "temporary", "permanent"],
        "second": ["second", "temporary", "permanent"],
    }
    assert wrapper.model.model.layers[0].mlp.run_forward(["x"]) == ["x", "permanent"]


def test_qwen3_run_with_hooks_accepts_transformerlens_shorthand_name() -> None:
    class _QProjectionQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            return {"q": q_out}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _QProjectionQwen3CausalLM()

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[("q0", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert output == {"q": ["q", "patched"]}
    assert wrapper.model.model.layers[0].self_attn.q_proj.run_forward(["q"]) == ["q"]


def test_qwen3_run_with_hooks_token_inputs_do_not_add_default_cache_hooks() -> None:
    torch = pytest.importorskip("torch")

    class _NoImplicitCacheQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            if kwargs.get("output_attentions"):
                raise AssertionError("run_with_hooks should not add default cache attention hooks")
            mlp_out = self.model.layers[0].mlp.run_forward(["mlp"])
            return {"logits": kwargs["input_ids"] * 10, "mlp": mlp_out}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _NoImplicitCacheQwen3CausalLM()

    logits = wrapper.run_with_hooks(
        torch.tensor([1, 2]),
        fwd_hooks=[("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )

    assert torch.equal(logits, torch.tensor([[10, 20]]))


def test_qwen3_run_with_hooks_accepts_forward_positionals() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            mlp_out = self.model.layers[0].mlp.run_forward(["mlp"])
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
            return {"logits": logits, "mlp": mlp_out}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwen3CausalLM()

    per_token_loss = wrapper.run_with_hooks(
        torch.tensor([0, 1, 2]),
        "loss",
        True,
        fwd_hooks=[("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["patched"])],
    )
    expected = torch.nn.functional.cross_entropy(
        torch.tensor([[0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]),
        torch.tensor([1, 2]),
        reduction="none",
    ).unsqueeze(0)

    assert torch.allclose(per_token_loss, expected)
    assert wrapper.model.model.layers[0].mlp.run_forward(["mlp"]) == ["mlp"]


def test_qwen3_add_hook_accepts_callable_name_filter() -> None:
    wrapper = _wrapper_with_fake_model()

    handle = wrapper.add_hook(
        lambda name: name == "layer_0.mlp_out",
        lambda **kwargs: kwargs["activation"] + ["patched"],
    )

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first", "patched"],
        "second": ["second", "patched"],
    }
    handle.remove()
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first"],
        "second": ["second"],
    }


def test_qwen3_run_with_cache_cleans_up_after_invalid_layer() -> None:
    wrapper = _wrapper_with_fake_model()
    mlp = wrapper.model.model.layers[0].mlp

    with pytest.raises(KeyError):
        wrapper.run_with_cache(
            {"input_ids": [[1, 2]]},
            layers=["layer_0.mlp_out", "layer_99.mlp_out"],
        )

    assert mlp.forward_hooks == []
    assert mlp.run_forward(["x"]) == ["x"]


def test_qwen3_run_with_cache_component_hooks_do_not_patch_outputs() -> None:
    wrapper = _wrapper_with_fake_model()

    output, cache = wrapper.run_with_cache({"input_ids": [[1, 2]]}, layers=["layer_0.mlp_out"])

    assert output == {"first": ["first"], "second": ["second"]}
    assert cache == {"layer_0.mlp_out": ["second"]}


def test_qwen3_run_with_cache_layers_accept_transformerlens_shorthand_name() -> None:
    class _QProjectionQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            q_out = self.model.layers[0].self_attn.q_proj.run_forward(["q"])
            return {"q": q_out}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _QProjectionQwen3CausalLM()

    output, cache = wrapper.run_with_cache({"input_ids": [[1, 2]]}, layers=["q0"])

    assert output == {"q": ["q"]}
    assert cache == {"blocks.0.attn.hook_q": ["q"]}


def test_qwen3_run_with_cache_accepts_single_string_layer() -> None:
    wrapper = _wrapper_with_fake_model()

    output, cache = wrapper.run_with_cache({"input_ids": [[1, 2]]}, layers="layer_0.mlp_out")

    assert output == {"first": ["first"], "second": ["second"]}
    assert cache == {"layer_0.mlp_out": ["second"]}


def test_qwen3_add_caching_hooks_accepts_single_string_layer() -> None:
    wrapper = _wrapper_with_fake_model()

    cache = wrapper.add_caching_hooks(layers="layer_0.mlp_out")
    output = wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]

    assert output == {"first": ["first"], "second": ["second"]}
    assert cache["layer_0.mlp_out"] == ["second"]


def test_qwen3_run_with_cache_accepts_forward_positionals() -> None:
    torch = pytest.importorskip("torch")

    class _LogitsOnlyQwen3CausalLM(_FakeQwen3CausalLM):
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

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _LogitsOnlyQwen3CausalLM()

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


def test_qwen3_run_with_cache_accepts_names_filter_and_cache_object() -> None:
    wrapper = _wrapper_with_fake_model()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        names_filter=lambda name: name == "layer_0.mlp_out",
        return_cache_object=True,
    )

    assert output == {"first": ["first"], "second": ["second"]}
    assert isinstance(cache, ActivationCache)
    assert cache["layer_0.mlp_out"] == ["second"]


def test_qwen3_token_inputs_cache_all_by_default() -> None:
    torch = pytest.importorskip("torch")

    class _TokenCacheQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            mlp = self.model.layers[0].mlp
            mlp_out = mlp.run_forward(["mlp"])
            return {"logits": kwargs["input_ids"] * 10, "mlp": mlp_out}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _TokenCacheQwen3CausalLM()

    logits, cache = wrapper.run_with_cache(torch.tensor([1, 2]))

    assert torch.equal(logits, torch.tensor([[10, 20]]))
    assert isinstance(cache, ActivationCache)
    assert cache[("mlp_out", 0)] == ["mlp"]


def test_qwen3_mapping_inputs_can_explicitly_cache_all() -> None:
    class _CacheAllQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            mlp = self.model.layers[0].mlp
            first = mlp.run_forward(["first"])
            second = mlp.run_forward(["second"])
            return {"first": first, "second": second}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _CacheAllQwen3CausalLM()

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        cache_all=True,
        return_cache_object=True,
    )

    assert output == {"first": ["first"], "second": ["second"]}
    assert isinstance(cache, ActivationCache)
    assert cache[("mlp_out", 0)] == ["second"]


def test_qwen3_persistent_cache_hooks() -> None:
    class _PersistentCacheQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            mlp = self.model.layers[0].mlp
            value = kwargs["input_ids"][0][-1]
            return {"mlp": mlp.run_forward(["mlp", value])}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _PersistentCacheQwen3CausalLM()

    cache = wrapper.cache_some(lambda name: name == "layer_0.mlp_out")

    assert wrapper({"input_ids": [[1, 2]]}, return_type="model_output") == {"mlp": ["mlp", 2]}
    assert cache["layer_0.mlp_out"] == ["mlp", 2]

    wrapper.reset_hooks()

    assert wrapper({"input_ids": [[1, 3]]}, return_type="model_output") == {"mlp": ["mlp", 3]}
    assert cache["layer_0.mlp_out"] == ["mlp", 3]

    wrapper.reset_hooks(including_permanent=True)
    wrapper({"input_ids": [[1, 4]]}, return_type="model_output")

    assert cache["layer_0.mlp_out"] == ["mlp", 3]


def test_qwen3_preserves_empty_external_cache_for_persistent_hooks() -> None:
    wrapper = _wrapper_with_fake_model()
    external_cache = ActivationCache()

    cache = wrapper.add_caching_hooks(layers=["layer_0.mlp_out"], cache=external_cache)
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache is external_cache
    assert external_cache.model is wrapper
    assert external_cache["layer_0.mlp_out"] == ["second"]


def test_qwen3_add_caching_hooks_defaults_to_cache_all() -> None:
    wrapper = _wrapper_with_fake_model()

    cache = wrapper.add_caching_hooks()
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache[("pattern", 0)].ndim == 4
    assert ("attn_scores", 0) not in cache

    wrapper.reset_hooks(including_permanent=True)
    empty_cache = wrapper.add_caching_hooks(cache_all=False)
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert empty_cache.to_dict() == {}


def test_qwen3_is_caching_tracks_cache_lifecycle() -> None:
    class _StateAwareQwen3CausalLM(_FakeQwen3CausalLM):
        def __init__(self, owner: Qwen3DenseModelWrapper) -> None:
            super().__init__()
            self.owner = owner
            self.seen_states: list[bool] = []

        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            self.seen_states.append(self.owner.is_caching)
            return super().__call__(**kwargs)

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _StateAwareQwen3CausalLM(wrapper)

    assert wrapper.is_caching is False
    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["layer_0.mlp_out"],
    )

    assert wrapper.model.seen_states == [True]
    assert output == {"first": ["first"], "second": ["second"]}
    assert cache == {"layer_0.mlp_out": ["second"]}
    assert wrapper.is_caching is False

    persistent_cache = wrapper.add_caching_hooks(layers=["layer_0.mlp_out"])
    assert wrapper.is_caching is True
    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")
    assert persistent_cache[("mlp_out", 0)] == ["second"]

    wrapper.reset_hooks(including_permanent=True)
    assert wrapper.is_caching is False


def test_qwen3_caching_hooks_remove_batch_dim() -> None:
    wrapper = _wrapper_with_fake_model()

    cache = wrapper.add_caching_hooks(
        layers=["layer_0.mlp_out"],
        remove_batch_dim=True,
    )

    wrapper({"input_ids": [[1, 2]]}, return_type="model_output")

    assert cache.has_batch_dim is False
    assert cache["layer_0.mlp_out"] == "second"


def test_qwen3_run_with_cache_incl_bwd_caches_gradients() -> None:
    torch = pytest.importorskip("torch")

    class _DifferentiableLayer(_FakeModule):
        def __call__(self, value: Any) -> Any:
            return self.run_forward(value * 3, inputs=(value,))

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

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _DifferentiableModel()
    x = torch.ones(1, 1, 2, requires_grad=True)

    output, cache = wrapper.run_with_cache(
        {"inputs_embeds": x},
        layers=["blocks.0.hook_resid_post"],
        return_type="logits",
        incl_bwd=True,
    )

    assert torch.equal(output.detach(), torch.tensor(6.0))
    assert torch.equal(cache["blocks.0.hook_resid_post"], torch.full_like(x, 3.0))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.ones_like(x))
    assert torch.equal(x.grad, torch.full_like(x, 3.0))
    assert wrapper._hooks == []


def test_qwen3_add_caching_hooks_incl_bwd_caches_gradients() -> None:
    torch = pytest.importorskip("torch")

    class _DifferentiableLayer(_FakeModule):
        def __call__(self, value: Any) -> Any:
            return self.run_forward(value + 2, inputs=(value,))

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

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _DifferentiableModel()
    cache = wrapper.add_caching_hooks(
        layers=["blocks.0.hook_resid_post"],
        incl_bwd=True,
    )
    x = torch.ones(1, 1, 2, requires_grad=True)

    loss = wrapper({"inputs_embeds": x})
    loss.backward()

    assert torch.equal(cache["blocks.0.hook_resid_post"], torch.full_like(x, 3.0))
    assert torch.equal(cache["blocks.0.hook_resid_post_grad"], torch.ones_like(x))
    assert torch.equal(x.grad, torch.ones_like(x))

    wrapper.reset_hooks(including_permanent=True)
    assert wrapper._hooks == []


def test_qwen3_run_with_cache_prepares_cached_values() -> None:
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

    class _TensorCacheQwen3CausalLM(_FakeQwen3CausalLM):
        def __call__(self, **kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            activation = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)
            activation.requires_grad_(True)
            mlp_out = self.model.layers[0].mlp.run_forward(_DeviceAwareTensor(activation))
            return {"mlp": mlp_out}

    wrapper = Qwen3DenseModelWrapper(name="Qwen/Qwen3-8B")
    wrapper.model = _TensorCacheQwen3CausalLM()

    _output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2, 3]]},
        layers=["layer_0.mlp_out"],
        pos_slice=1,
        detach=True,
        clone=True,
        device="cpu",
        return_cache_object=True,
    )

    cached = cache["layer_0.mlp_out"]
    assert isinstance(cached, _DeviceAwareTensor)
    assert tuple(cached.shape) == (1, 1, 4)
    expected = torch.arange(12, dtype=torch.float32).reshape(1, 3, 4)[:, [1]]
    assert torch.equal(cached.tensor, expected)
    assert cached.requires_grad is False
    assert moved_devices == ["cpu"]


def test_qwen3_run_with_hooks_filter_dedupes_safe_and_transformerlens_aliases() -> None:
    wrapper = _wrapper_with_fake_model()
    calls = 0

    def append_once(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return kwargs["activation"] + ["patched"]

    output = wrapper.run_with_hooks(
        {"input_ids": [[1, 2]]},
        fwd_hooks=[
            (
                lambda name: name.endswith(".mlp_out") or name.endswith(".hook_mlp_out"),
                append_once,
            )
        ],
    )

    assert output == {
        "first": ["first", "patched"],
        "second": ["second", "patched"],
    }
    assert calls == 2


def test_qwen3_permanent_hooks_survive_default_reset() -> None:
    wrapper = _wrapper_with_fake_model()

    wrapper.add_perma_hook("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["permanent"])
    wrapper.add_hook("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["temp"])

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first", "permanent", "temp"],
        "second": ["second", "permanent", "temp"],
    }

    wrapper.reset_hooks()

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first", "permanent"],
        "second": ["second", "permanent"],
    }

    wrapper.reset_hooks(including_permanent=True)

    assert wrapper._hooks == []
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first"],
        "second": ["second"],
    }


def test_qwen3_hooks_context_is_temporary() -> None:
    wrapper = _wrapper_with_fake_model()

    wrapper.add_perma_hook("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["permanent"])

    with wrapper.hooks(
        fwd_hooks=[("layer_0.mlp_out", lambda **kwargs: kwargs["activation"] + ["temp"])],
    ):
        output = wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]

    assert output == {
        "first": ["first", "permanent", "temp"],
        "second": ["second", "permanent", "temp"],
    }
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first", "permanent"],
        "second": ["second", "permanent"],
    }


def test_qwen3_run_with_cache_captures_attention_pattern() -> None:
    wrapper = _wrapper_with_fake_model()
    original_attention = wrapper.model.config._attn_implementation

    output, cache = wrapper.run_with_cache(
        {"input_ids": [[1, 2]]},
        layers=["blocks.0.attn.hook_pattern"],
    )

    assert output["output_attentions"] is True
    assert getattr(cache["blocks.0.attn.hook_pattern"], "ndim", None) == 4
    assert wrapper.model.attn_implementation_calls == ["eager", original_attention]
    assert wrapper.model.config._attn_implementation == original_attention


def test_qwen3_run_with_cache_captures_derived_attention_result() -> None:
    torch = pytest.importorskip("torch")
    wrapper = _wrapper_with_fake_model()
    z = torch.arange(4, dtype=torch.float32).reshape(1, 1, 4)

    output, cache = wrapper.run_with_cache(
        {"z": z},
        layers=["layer_0.result"],
    )

    z_by_head = z.reshape(1, 1, 2, 2)
    W_O = wrapper.model.model.layers[0].self_attn.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0)
    expected = torch.einsum("bphd,hdm->bphm", z_by_head, W_O)
    assert torch.equal(output["attn_out"], z)
    assert torch.equal(cache["layer_0.result"], expected)


def test_qwen3_run_with_cache_filter_can_select_transformerlens_result() -> None:
    torch = pytest.importorskip("torch")
    wrapper = _wrapper_with_fake_model()

    _output, cache = wrapper.run_with_cache(
        {"z": torch.zeros(1, 1, 4)},
        names_filter=lambda name: name.endswith(".hook_result"),
    )

    assert "blocks.0.attn.hook_result" in cache


def test_qwen3_add_hook_patches_derived_attention_result() -> None:
    torch = pytest.importorskip("torch")
    wrapper = _wrapper_with_fake_model()
    z = torch.arange(4, dtype=torch.float32).reshape(1, 1, 4)

    wrapper.add_hook("layer_0.result", lambda **kwargs: kwargs["activation"] * 0)

    original_result = torch.einsum(
        "bphd,hdm->bphm",
        z.reshape(1, 1, 2, 2),
        wrapper.model.model.layers[0].self_attn.o_proj.weight.reshape(4, 2, 2).permute(1, 2, 0),
    )
    output, _cache = wrapper.run_with_cache({"z": z})

    assert torch.equal(output["attn_out"], z - original_result.sum(dim=-2))


def test_qwen3_add_hook_accepts_transformerlens_shorthand_name() -> None:
    wrapper = _wrapper_with_fake_model()

    wrapper.add_hook("q0", lambda **kwargs: kwargs["activation"] + ["patched"])

    assert wrapper.model.model.layers[0].self_attn.q_proj.run_forward(["q"]) == [
        "q",
        "patched",
    ]


def test_qwen3_run_with_cache_captures_attention_scores() -> None:
    torch = pytest.importorskip("torch")
    wrapper = _wrapper_with_fake_model()
    scores = torch.randn(1, 2, 3, 3)

    output, cache = wrapper.run_with_cache(
        {"scores": scores},
        layers=["blocks.0.attn.hook_attn_scores"],
    )

    assert output["output_attentions"] is True
    assert torch.equal(cache["blocks.0.attn.hook_attn_scores"], scores)


def test_qwen3_run_with_cache_captures_attention_pattern_and_scores() -> None:
    torch = pytest.importorskip("torch")
    wrapper = _wrapper_with_fake_model()
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


def test_qwen3_attention_scores_hooks_patch_softmax_inputs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = _wrapper_with_fake_model()

    def force_first_source(**kwargs: Any) -> Any:
        patched = torch.full_like(kwargs["activation"], -1000.0)
        patched[..., 0] = 1000.0
        return patched

    wrapper.add_hook("layer_0.attn_scores", force_first_source)

    _tokens, pattern = wrapper.model.model.layers[0].self_attn.forward(torch.zeros(1, 2, 1, 2))
    assert torch.all(pattern[..., 0] > 0.99)


def test_qwen3_attention_hook_remove_clears_output_attentions_flag() -> None:
    wrapper = _wrapper_with_fake_model()

    handle = wrapper.add_hook("layer_0.pattern", lambda **_kwargs: None)
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]["output_attentions"] is True

    handle.remove()

    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first"],
        "second": ["second"],
    }
    assert wrapper._hooks == []


def test_qwen3_reset_hooks_clears_attention_output_flags() -> None:
    wrapper = _wrapper_with_fake_model()

    wrapper.add_hook("layer_0.pattern", lambda **_kwargs: None)
    wrapper.add_hook("layer_0.attn_scores", lambda **_kwargs: None)
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0]["output_attentions"] is True

    wrapper.reset_hooks()

    assert wrapper._hooks == []
    assert wrapper.run_with_cache({"input_ids": [[1, 2]]})[0] == {
        "first": ["first"],
        "second": ["second"],
    }


def test_qwen3_attention_pattern_hooks_patch_softmax_outputs() -> None:
    torch = pytest.importorskip("torch")
    wrapper = _wrapper_with_fake_model()

    def force_last_source(**kwargs: Any) -> Any:
        patched = torch.zeros_like(kwargs["activation"])
        patched[..., -1] = 1
        return patched

    wrapper.add_hook("layer_0.pattern", force_last_source)

    _tokens, pattern = wrapper.model.model.layers[0].self_attn.forward(torch.zeros(1, 2, 3, 3))
    assert torch.all(pattern[..., -1] == 1)
