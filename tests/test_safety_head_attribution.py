from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from SafeLens.attribution import SafetyHeadAttributor, attribute_safety_heads
from SafeLens.attribution.safety_heads import _activation_norms
from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper
from SafeLens.core.hooks import ActivationCache

torch = pytest.importorskip("torch")


class _FakeCfg:
    n_layers = 1
    n_heads = 2


class _SafetyHeadWrapper(ModelWrapper):
    cfg = _FakeCfg()

    def __init__(self) -> None:
        self.activation = torch.tensor([[[[1.0, 0.0], [0.0, 1.0]], [[2.0, 0.0], [0.0, 3.0]]]])
        self.hook_calls: list[str] = []

    def load_model(self) -> _SafetyHeadWrapper:
        return self

    def add_hook(
        self,
        layer: LayerRef,
        hook_fn: HookFn | None = None,
        *,
        hook: HookFn | None = None,
        dir: str = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
    ) -> Any:
        _ = layer, hook_fn, hook, dir, is_permanent, level, prepend
        raise NotImplementedError

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
        *,
        return_cache_object: bool = False,
        return_type: str = "logits",
        **kwargs: Any,
    ) -> tuple[Any, Any]:
        _ = batch, layers, return_type, kwargs
        logits = self._logits_from_activation(self.activation)
        cache = ActivationCache({"layer_0.result": self.activation}, model=self)
        return logits, cache if return_cache_object else cache.cache_dict

    def run_with_hooks(
        self,
        batch: Any,
        *,
        fwd_hooks: Any,
        return_type: str = "logits",
        **kwargs: Any,
    ) -> Any:
        _ = batch, return_type, kwargs
        activation = self.activation
        for name, hook in fwd_hooks:
            self.hook_calls.append(str(name))
            patched = hook(activation=activation)
            if patched is not None:
                activation = patched
        return self._logits_from_activation(activation)

    def generate(self, prompt: str, **generation_kwargs: Any) -> Any:
        _ = prompt, generation_kwargs
        raise NotImplementedError

    def remove_hooks(self) -> None:
        return None

    @staticmethod
    def _logits_from_activation(activation: Any) -> Any:
        summed = activation.sum(dim=(1, 2, 3))
        head0 = activation[:, :, 0, :].sum(dim=(1, 2))
        head1 = activation[:, :, 1, :].sum(dim=(1, 2))
        return torch.stack([summed, head0, head1], dim=-1).unsqueeze(1)


def test_attribute_safety_heads_scores_zero_ablation_kl() -> None:
    wrapper = _SafetyHeadWrapper()

    result = attribute_safety_heads(wrapper, {"input_ids": [[1, 2]]}, layers=[0])

    heads = result.details["heads"]
    assert result.method == "safety_head_attributor"
    assert result.details["component"] == "result"
    assert result.details["score_type"] == "kl"
    assert [(head["layer"], head["head"]) for head in heads] == [(0, 1), (0, 0)]
    assert all(head["score"] > 0.0 for head in heads)
    assert [head["activation_name"] for head in heads] == ["layer_0.result", "layer_0.result"]
    assert wrapper.hook_calls == ["layer_0.result", "layer_0.result"]


def test_safety_head_attributor_filters_heads_and_top_k() -> None:
    attributor = SafetyHeadAttributor({"layers": [0], "heads": [0], "top_k": 1})
    attributor.attach(_SafetyHeadWrapper())

    result = attributor.attribute_input({"input_ids": [[1, 2]]})

    assert result.details["head_count"] == 1
    assert result.details["heads"][0]["head"] == 0


def test_safety_head_attributor_supports_scale_ablation() -> None:
    attributor = SafetyHeadAttributor(
        {
            "layers": [0],
            "heads": [0],
            "ablation_mode": "scale",
            "scale_factor": 0.5,
        }
    )
    attributor.attach(_SafetyHeadWrapper())

    result = attributor.attribute_input({"input_ids": [[1, 2]]})

    head = result.details["heads"][0]
    assert head["ablation_mode"] == "scale"
    assert head["scale_factor"] == 0.5
    assert head["score"] > 0.0


def test_safety_head_attributor_requires_attached_model() -> None:
    with pytest.raises(RuntimeError, match="attached"):
        SafetyHeadAttributor({"layers": [0]}).attribute_input({"input_ids": [[1, 2]]})


def test_safety_head_attributor_requires_supported_batch_keys() -> None:
    attributor = SafetyHeadAttributor({"layers": [0]})
    attributor.attach(_SafetyHeadWrapper())

    with pytest.raises(ValueError, match="text/prompt or token ids"):
        attributor.attribute_input({"id": "missing-input"})


def test_activation_norms_accepts_sequence_of_tensors() -> None:
    values = [
        torch.tensor([[3.0, 4.0]], dtype=torch.float32),
        torch.tensor([[5.0, 12.0]], dtype=torch.float32),
    ]

    norms = _activation_norms(values)

    assert norms == [5.0, 13.0]
