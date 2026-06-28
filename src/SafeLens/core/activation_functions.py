"""TransformerLens-style activation functions without importing TransformerLens."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Any

_torch: Any
_nn: Any
_F: Any

try:
    import torch as _torch
    import torch.nn as _nn
    import torch.nn.functional as _F
except ModuleNotFoundError:
    _torch = None
    _nn = None
    _F = None


ActivationFunction = Callable[..., Any]


def gelu_new(input: Any) -> Any:
    """GPT-2 GeLU approximation used by TransformerLens."""

    if _is_torch_tensor(input):
        return (
            0.5
            * input
            * (
                1.0
                + _torch.tanh(
                    math.sqrt(2.0 / math.pi) * (input + 0.044715 * _torch.pow(input, 3.0))
                )
            )
        )
    return _elementwise(input, _gelu_new_scalar)


def gelu_fast(input: Any) -> Any:
    """Fast GeLU approximation used by several TransformerLens checkpoints."""

    if _is_torch_tensor(input):
        return (
            0.5
            * input
            * (1.0 + _torch.tanh(input * 0.7978845608 * (1.0 + 0.044715 * input * input)))
        )
    return _elementwise(input, _gelu_fast_scalar)


def gelu_pytorch_tanh(input: Any) -> Any:
    """PyTorch GeLU tanh approximation, with Python/numpy fallbacks."""

    if _is_torch_tensor(input):
        return _F.gelu(input, approximate="tanh")
    return _elementwise(input, _gelu_new_scalar)


def gelu(input: Any) -> Any:
    """Standard exact GeLU activation."""

    if _is_torch_tensor(input):
        return _F.gelu(input)
    return _elementwise(input, lambda value: 0.5 * value * (1.0 + math.erf(value / math.sqrt(2.0))))


def silu(input: Any) -> Any:
    """SiLU / swish activation."""

    if _is_torch_tensor(input):
        return _F.silu(input)
    return _elementwise(input, lambda value: value / (1.0 + math.exp(-value)))


def relu(input: Any) -> Any:
    """ReLU activation."""

    if _is_torch_tensor(input):
        return _F.relu(input)
    return _elementwise(input, lambda value: max(0.0, value))


def solu(input: Any) -> Any:
    """SoLU activation: input times softmax over the final dimension."""

    if _is_torch_tensor(input):
        return input * _F.softmax(input, dim=-1)

    np = _numpy_module()
    if np is not None and isinstance(input, np.ndarray):
        shifted = input - np.max(input, axis=-1, keepdims=True)
        exp_values = np.exp(shifted)
        return input * exp_values / np.sum(exp_values, axis=-1, keepdims=True)

    if _is_sequence(input) and input and _is_sequence(input[0]):
        return [solu(item) for item in input]
    values = [float(item) for item in input]
    max_value = max(values)
    exp_values = [math.exp(value - max_value) for value in values]
    total = sum(exp_values)
    return [value * exp_value / total for value, exp_value in zip(values, exp_values, strict=True)]


def xielu(input: Any) -> Any:
    """Fixed-parameter xIELU activation used by TransformerLens."""

    if _is_torch_tensor(input):
        eps = _torch.tensor(-1e-6, dtype=input.dtype, device=input.device)
        return _torch.where(
            input > 0,
            0.8 * input * input + 0.5 * input,
            (_torch.expm1(_torch.min(input, eps)) - input) * 0.8 + 0.5 * input,
        )
    return _elementwise(input, _xielu_scalar)


if _nn is not None:

    class _XIELUModule(_nn.Module):  # type: ignore[misc]
        """Trainable xIELU activation matching TransformerLens' parameterization."""

        def __init__(
            self,
            alpha_p_init: float = 0.8,
            alpha_n_init: float = 0.8,
            beta_init: float = 0.5,
            eps: float = -1e-6,
        ) -> None:
            super().__init__()
            self.alpha_p = _nn.Parameter(
                _torch.log(_torch.expm1(_torch.tensor(alpha_p_init, dtype=_torch.float32)))
            )
            self.alpha_n = _nn.Parameter(
                _torch.log(
                    _torch.expm1(_torch.tensor(alpha_n_init - beta_init, dtype=_torch.float32))
                )
            )
            self.beta: Any
            self.eps: Any
            self.register_buffer("beta", _torch.tensor(beta_init, dtype=_torch.float32))
            self.register_buffer("eps", _torch.tensor(eps, dtype=_torch.float32))

        def forward(self, input: Any) -> Any:
            alpha_p = _F.softplus(self.alpha_p)
            alpha_n = self.beta + _F.softplus(self.alpha_n)
            return _torch.where(
                input > 0,
                alpha_p * input * input + self.beta * input,
                (_torch.expm1(_torch.min(input, self.eps)) - input) * alpha_n + self.beta * input,
            )

    XIELU: Any = _XIELUModule

else:

    class _MissingXIELU:
        """Placeholder that reports the optional torch dependency when constructed."""

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise ImportError("torch is required to instantiate XIELU.")

    XIELU = _MissingXIELU


SUPPORTED_ACTIVATIONS: dict[str, ActivationFunction] = {
    "solu": solu,
    "solu_ln": solu,
    "gelu_new": gelu_new,
    "gelu_fast": gelu_fast,
    "silu": silu,
    "relu": relu,
    "gelu": gelu,
    "gelu_pytorch_tanh": gelu_pytorch_tanh,
    "xielu": xielu,
}


def _gelu_new_scalar(value: float) -> float:
    return (
        0.5 * value * (1.0 + math.tanh(math.sqrt(2.0 / math.pi) * (value + 0.044715 * value**3.0)))
    )


def _gelu_fast_scalar(value: float) -> float:
    return 0.5 * value * (1.0 + math.tanh(value * 0.7978845608 * (1.0 + 0.044715 * value * value)))


def _xielu_scalar(value: float) -> float:
    return (
        0.8 * value * value + 0.5 * value
        if value > 0
        else (math.expm1(min(value, -1e-6)) - value) * 0.8 + 0.5 * value
    )


def _elementwise(value: Any, fn: Callable[[float], float]) -> Any:
    np = _numpy_module()
    if np is not None and isinstance(value, np.ndarray):
        vectorized = np.vectorize(lambda item: fn(float(item)))
        return vectorized(value)
    if _is_sequence(value):
        return [_elementwise(item, fn) for item in value]
    return fn(float(value))


def _numpy_module() -> Any | None:
    try:
        import numpy as np
    except ModuleNotFoundError:
        return None
    return np


def _is_torch_tensor(value: Any) -> bool:
    return _torch is not None and isinstance(value, _torch.Tensor)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)
