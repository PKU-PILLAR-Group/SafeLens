"""Small analysis helpers for logits, losses, ablations, and head detection."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from SafeLens.core.hooks import HookPoint, clone_activation


def softmax(values: Any) -> Any:
    """Apply softmax over the final dimension."""
    try:
        import torch

        if hasattr(values, "shape"):
            return torch.softmax(values, dim=-1)
    except Exception:
        pass
    if values and isinstance(values[0], list):
        return [softmax(row) for row in values]
    max_value = max(float(value) for value in values)
    exps = [math.exp(float(value) - max_value) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def log_softmax(values: Any) -> Any:
    """Apply log-softmax over the final dimension."""
    try:
        import torch

        if hasattr(values, "shape"):
            return torch.log_softmax(values, dim=-1)
    except Exception:
        pass
    probs = softmax(values)
    if probs and isinstance(probs[0], list):
        return [log_softmax(row) for row in values]
    return [math.log(float(prob)) for prob in probs]


def logits_to_log_probs(logits: Any, tokens: Any | None = None) -> Any:
    """Convert logits to log probabilities, optionally gathering token log-probs."""
    log_probs = log_softmax(logits)
    if tokens is None:
        return log_probs
    return gather_last_dim(log_probs, tokens)


def per_token_cross_entropy_loss(logits: Any, tokens: Any) -> Any:
    """Return negative log-probability for each target token."""
    gathered = logits_to_log_probs(logits, tokens)
    return negate_values(gathered)


def cross_entropy_loss(logits: Any, tokens: Any) -> float:
    """Return mean cross-entropy loss."""
    losses = flatten(per_token_cross_entropy_loss(logits, tokens))
    return sum(float(loss) for loss in losses) / max(1, len(losses))


def topk_tokens(logits: Any, k: int = 5) -> Any:
    """Return top-k token indices and values for the final dimension."""
    try:
        import torch

        if hasattr(logits, "shape"):
            values, indices = torch.topk(logits, k, dim=-1)
            return indices, values
    except Exception:
        pass
    if logits and isinstance(logits[0], list):
        return [topk_tokens(row, k=k) for row in logits]
    pairs = sorted(enumerate(logits), key=lambda item: float(item[1]), reverse=True)[:k]
    return [index for index, _value in pairs], [value for _index, value in pairs]


def logit_diff(logits: Any, correct_token: int, incorrect_token: int, *, pos: int = -1) -> float:
    """Return logit difference at one position."""
    shape = getattr(logits, "shape", None)
    if shape is not None:
        if len(shape) >= 3:
            value = logits[0, pos, correct_token] - logits[0, pos, incorrect_token]
        elif len(shape) == 2:
            value = logits[pos, correct_token] - logits[pos, incorrect_token]
        else:
            value = logits[correct_token] - logits[incorrect_token]
        item = getattr(value, "item", None)
        return float(item() if callable(item) else value)

    if isinstance(logits, list) and logits and isinstance(logits[0], list):
        if logits[0] and isinstance(logits[0][0], list):
            row = logits[0][pos]
        else:
            row = logits[pos]
    else:
        row = logits
    return float(row[correct_token]) - float(row[incorrect_token])


def residual_stack_to_logits(residual_stack: Any, unembed: Any) -> Any:
    """Project residual components through an unembedding matrix."""
    from SafeLens.core.factored_matrix import matmul

    return matmul(residual_stack, unembed)


def direct_logit_attribution(residual_stack: Any, token_directions: Any) -> Any:
    """Project residual components onto token directions."""
    return dot_last_dim(residual_stack, token_directions)


def zero_ablation_hook(activation: Any, hook: HookPoint | None = None) -> Any:
    """Hook that replaces an activation with zeros."""
    _ = hook
    try:
        import torch

        if hasattr(activation, "shape"):
            return torch.zeros_like(activation)
    except Exception:
        pass
    return map_values(activation, lambda _value: 0)


def mean_ablation_hook(activation: Any, hook: HookPoint | None = None) -> Any:
    """Hook that replaces values with the activation mean."""
    _ = hook
    try:
        import torch

        if hasattr(activation, "shape"):
            return torch.zeros_like(activation) + activation.float().mean()
    except Exception:
        pass
    values = [float(value) for value in flatten(activation)]
    mean_value = sum(values) / max(1, len(values))
    return map_values(activation, lambda _value: mean_value)


def replace_activation_hook(replacement: Any) -> Callable[[Any, HookPoint | None], Any]:
    """Return a hook that replaces the full activation."""

    def hook(_activation: Any, _hook: HookPoint | None = None) -> Any:
        return clone_activation(replacement)

    return hook


def gather_last_dim(values: Any, indices: Any) -> Any:
    """Gather values at final-dimension indices."""
    try:
        if hasattr(values, "shape") and hasattr(indices, "shape"):
            return values.gather(-1, indices.unsqueeze(-1)).squeeze(-1)
    except Exception:
        pass
    if isinstance(indices, list):
        if indices and isinstance(indices[0], list):
            return [
                gather_last_dim(value_row, index_row)
                for value_row, index_row in zip(values, indices, strict=True)
            ]
        return [row[index] for row, index in zip(values, indices, strict=True)]
    return values[indices]


def flatten(value: Any) -> list[Any]:
    """Flatten nested lists or tensor-like values."""
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if isinstance(value, list):
        result: list[Any] = []
        for item in value:
            result.extend(flatten(item))
        return result
    return [value]


def negate_values(value: Any) -> Any:
    """Negate nested values."""
    try:
        return -value
    except Exception:
        pass
    return map_values(value, lambda item: -float(item))


def map_values(value: Any, fn: Callable[[Any], Any]) -> Any:
    """Map over nested list leaves."""
    try:
        import torch

        if hasattr(value, "shape"):
            return torch.zeros_like(value) if fn(1) == 0 else value
    except Exception:
        pass
    if isinstance(value, list):
        return [map_values(item, fn) for item in value]
    return fn(value)


def dot_last_dim(left: Any, right: Any) -> Any:
    """Dot product over final dimension."""
    try:
        return (left * right).sum(dim=-1)
    except Exception:
        pass
    if isinstance(left, list) and isinstance(right, list):
        if left and isinstance(left[0], list):
            return [
                dot_last_dim(l_item, r_item) for l_item, r_item in zip(left, right, strict=True)
            ]
        return sum(
            float(l_item) * float(r_item) for l_item, r_item in zip(left, right, strict=True)
        )
    return left
