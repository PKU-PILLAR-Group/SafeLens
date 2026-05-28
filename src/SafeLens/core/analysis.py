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
    try:
        import numpy as np

        if hasattr(values, "shape"):
            array = np.asarray(values)
            shifted = array - np.max(array, axis=-1, keepdims=True)
            exps = np.exp(shifted)
            return exps / np.sum(exps, axis=-1, keepdims=True)
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
    try:
        import numpy as np

        if hasattr(values, "shape"):
            probs = softmax(values)
            return np.log(probs)
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


def lm_log_probs(logits: Any, tokens: Any, attention_mask: Any | None = None) -> Any:
    """Return next-token log-probabilities for causal language modeling.

    Logits at position `i` are gathered at token `i + 1`, matching
    TransformerLens' language-model loss convention.
    """
    shifted_logits = slice_second_last_dim(logits, stop=-1)
    shifted_tokens = slice_last_dim(tokens, start=1)
    log_probs = logits_to_log_probs(shifted_logits, shifted_tokens)
    if attention_mask is None:
        return log_probs
    return mask_values(log_probs, causal_lm_loss_mask(attention_mask))


def lm_cross_entropy_loss(
    logits: Any,
    tokens: Any,
    attention_mask: Any | None = None,
    *,
    per_token: bool = False,
) -> Any:
    """Return causal LM cross-entropy using logits before each target token."""
    losses = negate_values(lm_log_probs(logits, tokens, attention_mask))
    if per_token:
        return losses
    values = [float(value) for value in flatten(losses) if is_valid_number(value)]
    return sum(values) / max(1, len(values))


def lm_accuracy(logits: Any, tokens: Any, attention_mask: Any | None = None) -> Any:
    """Return next-token prediction accuracy for causal language modeling."""
    predictions = argmax_last_dim(slice_second_last_dim(logits, stop=-1))
    targets = slice_last_dim(tokens, start=1)
    correct = equal_values(predictions, targets)
    if attention_mask is None:
        values = flatten(correct)
        return sum(float(value) for value in values) / max(1, len(values))
    masked = mask_values(correct, causal_lm_loss_mask(attention_mask))
    values = [float(value) for value in flatten(masked) if is_valid_number(value)]
    return sum(values) / max(1, len(values))


def topk_tokens(logits: Any, k: int = 5) -> Any:
    """Return top-k token indices and values for the final dimension."""
    try:
        import torch

        if hasattr(logits, "shape"):
            values, indices = torch.topk(logits, k, dim=-1)
            return indices, values
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(logits, "shape"):
            array = np.asarray(logits)
            sorted_indices = np.argsort(array, axis=-1)[..., ::-1][..., :k]
            sorted_values = np.take_along_axis(array, sorted_indices, axis=-1)
            return sorted_indices, sorted_values
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
    try:
        import torch

        if hasattr(residual_stack, "shape") or hasattr(unembed, "shape"):
            if not hasattr(residual_stack, "shape"):
                residual_stack = torch.as_tensor(
                    residual_stack,
                    dtype=getattr(unembed, "dtype", None),
                    device=getattr(unembed, "device", None),
                )
            if not hasattr(unembed, "shape"):
                unembed = torch.as_tensor(
                    unembed,
                    dtype=getattr(residual_stack, "dtype", None),
                    device=getattr(residual_stack, "device", None),
                )
            return residual_stack @ unembed
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(residual_stack, "shape") or hasattr(unembed, "shape"):
            return np.matmul(residual_stack, unembed)
    except Exception:
        pass
    return matmul_last_dim(residual_stack, unembed)


def direct_logit_attribution(residual_stack: Any, token_directions: Any) -> Any:
    """Project residual components onto token directions."""
    return dot_last_dim(residual_stack, token_directions)


def compute_head_results_from_z(z: Any, W_O: Any) -> Any:
    """Project per-head `z` activations through `W_O` into residual-space results.

    `z` is expected to end in `[head, d_head]`, and `W_O` should be shaped
    `[head, d_head, d_model]` or `[layer, head, d_head, d_model]`.
    Leading batch/position dimensions are preserved.
    """
    try:
        import torch

        if hasattr(z, "shape") or hasattr(W_O, "shape"):
            if not hasattr(z, "shape"):
                z = torch.as_tensor(
                    z,
                    dtype=getattr(W_O, "dtype", None),
                    device=getattr(W_O, "device", None),
                )
            if not hasattr(W_O, "shape"):
                W_O = torch.as_tensor(
                    W_O,
                    dtype=getattr(z, "dtype", None),
                    device=getattr(z, "device", None),
                )
            if _has_aligned_layer_axis(z, W_O):
                return torch.einsum("l...hd,lhdm->l...hm", z, W_O)
            W_O = _normalize_w_o_for_z(z, W_O)
            return torch.einsum("...hd,hdm->...hm", z, W_O)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(z, "shape") and hasattr(W_O, "shape"):
            if _has_aligned_layer_axis(z, W_O):
                return np.einsum("l...hd,lhdm->l...hm", z, W_O)
            W_O = _normalize_w_o_for_z(z, W_O)
            return np.einsum("...hd,hdm->...hm", z, W_O)
    except Exception:
        pass

    W_O = _normalize_w_o_for_z(z, W_O)
    return _head_results_from_nested(z, W_O)


def attention_pattern_score(
    pattern: Any,
    offset: int = -1,
    *,
    min_dest_pos: int | None = None,
) -> Any:
    """Average attention paid to a fixed source-position offset.

    `pattern` is expected to end in `[dest_pos, src_pos]`, with any number of
    leading batch/layer/head dimensions preserved. `offset=-1` scores previous
    token attention. Causal induction heads also attend backwards in the
    attention matrix, so induction-style matching is the same negative diagonal
    shifted by the repeat length in repeated-token prompts. `min_dest_pos`
    excludes diagonal entries before a destination position, which is useful for
    skipping the first copy of a repeated prompt.
    """
    try:
        import torch

        if hasattr(pattern, "shape") and isinstance(pattern, torch.Tensor):
            diag = torch.diagonal(pattern, offset=offset, dim1=-2, dim2=-1)
            diag = _slice_diagonal_by_dest_pos(diag, offset, min_dest_pos)
            if diag.shape[-1] == 0:
                return torch.zeros(pattern.shape[:-2], dtype=pattern.dtype, device=pattern.device)
            return diag.mean(dim=-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(pattern, "shape"):
            array = np.asarray(pattern)
            diag = np.diagonal(array, offset=offset, axis1=-2, axis2=-1)
            diag = _slice_diagonal_by_dest_pos(diag, offset, min_dest_pos)
            if diag.shape[-1] == 0:
                return np.zeros(array.shape[:-2], dtype=array.dtype)
            return diag.mean(axis=-1)
    except Exception:
        pass
    return _attention_pattern_score_nested(pattern, offset, min_dest_pos)


def previous_token_attention_score(pattern: Any) -> Any:
    """Score attention to the immediately previous token."""
    return attention_pattern_score(pattern, offset=-1)


def induction_attention_score(
    pattern: Any,
    *,
    offset: int = -1,
    repeat_length: int | None = None,
) -> Any:
    """Score induction-head style attention on a causal backward diagonal.

    For the minimal `[A][B][A] -> [B]` setup this is the previous-token
    diagonal (`offset=-1`). For a repeated sequence of length `N`, induction
    attention from the second copy to the next token after the first copy is on
    `offset=1-N`.
    """
    if repeat_length is not None:
        if repeat_length < 2:
            raise ValueError("repeat_length must be at least 2 for induction attention.")
        offset = 1 - repeat_length
        return attention_pattern_score(pattern, offset=offset, min_dest_pos=repeat_length)
    return attention_pattern_score(pattern, offset=offset)


def zero_ablation_hook(activation: Any, hook: HookPoint | None = None) -> Any:
    """Hook that replaces an activation with zeros."""
    _ = hook
    try:
        import torch

        if hasattr(activation, "shape"):
            return torch.zeros_like(activation)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(activation, "shape"):
            return np.zeros_like(activation)
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
    try:
        import numpy as np

        if hasattr(activation, "shape"):
            return np.zeros_like(activation) + np.asarray(activation, dtype=float).mean()
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
        import torch

        if hasattr(values, "shape"):
            if not hasattr(indices, "shape"):
                indices = torch.as_tensor(indices, dtype=torch.long, device=values.device)
            else:
                indices = indices.to(device=values.device, dtype=torch.long)
            return values.gather(-1, indices.unsqueeze(-1)).squeeze(-1)
    except Exception:
        pass
    try:
        if hasattr(values, "shape") and hasattr(indices, "shape"):
            return values.gather(-1, indices.unsqueeze(-1)).squeeze(-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(values, "shape") or hasattr(indices, "shape"):
            values_array = np.asarray(values)
            index_array = np.asarray(indices)
            return np.take_along_axis(values_array, np.expand_dims(index_array, -1), axis=-1).squeeze(-1)
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


def slice_last_dim(value: Any, *, start: int | None = None, stop: int | None = None) -> Any:
    """Slice the last dimension of tensor-like or nested-list values."""
    try:
        if hasattr(value, "shape"):
            return value[..., slice(start, stop)]
    except Exception:
        pass
    return _slice_nested_dim(value, slice(start, stop), dim=-1)


def slice_second_last_dim(value: Any, *, start: int | None = None, stop: int | None = None) -> Any:
    """Slice the second-last dimension of tensor-like or nested-list values."""
    try:
        if hasattr(value, "shape"):
            return value[..., slice(start, stop), :]
    except Exception:
        pass
    return _slice_nested_dim(value, slice(start, stop), dim=-2)


def causal_lm_loss_mask(attention_mask: Any) -> Any:
    """Return mask for valid causal LM targets from an input attention mask."""
    try:
        import torch

        if hasattr(attention_mask, "shape"):
            if isinstance(attention_mask, torch.Tensor):
                return attention_mask[..., :-1].bool() & attention_mask[..., 1:].bool()
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(attention_mask, "shape"):
            mask = np.asarray(attention_mask).astype(bool)
            return mask[..., :-1] & mask[..., 1:]
    except Exception:
        pass
    previous_mask = slice_last_dim(attention_mask, stop=-1)
    next_mask = slice_last_dim(attention_mask, start=1)
    return and_values(previous_mask, next_mask)


def mask_values(values: Any, mask: Any) -> Any:
    """Set values to `None` wherever mask is false."""
    try:
        import torch

        if hasattr(values, "shape"):
            if not hasattr(mask, "shape"):
                mask = torch.as_tensor(mask, dtype=torch.bool, device=values.device)
            else:
                mask = mask.to(device=values.device, dtype=torch.bool)
            if values.dtype.is_floating_point:
                fill_value = torch.full_like(values, float("nan"))
                return torch.where(mask, values, fill_value)
            return torch.where(mask, values.float(), torch.full_like(values.float(), float("nan")))
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(values, "shape") or hasattr(mask, "shape"):
            values_array = np.asarray(values)
            mask_array = np.asarray(mask).astype(bool)
            float_values = values_array.astype(float, copy=False)
            return np.where(mask_array, float_values, np.full_like(float_values, np.nan))
    except Exception:
        pass
    if isinstance(values, list) and isinstance(mask, list):
        return [mask_values(value_item, mask_item) for value_item, mask_item in zip(values, mask)]
    return values if bool(mask) else None


def argmax_last_dim(values: Any) -> Any:
    """Return argmax indices over the final dimension."""
    try:
        if hasattr(values, "shape"):
            return values.argmax(dim=-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(values, "shape"):
            return np.asarray(values).argmax(axis=-1)
    except Exception:
        pass
    if isinstance(values, list):
        if values and isinstance(values[0], list):
            return [argmax_last_dim(item) for item in values]
        return max(range(len(values)), key=lambda index: float(values[index]))
    return values


def equal_values(left: Any, right: Any) -> Any:
    """Elementwise equality returning numeric 0/1 values for list backends."""
    try:
        import torch

        if hasattr(left, "shape") and isinstance(left, torch.Tensor):
            if not hasattr(right, "shape"):
                right = torch.as_tensor(right, device=left.device)
            else:
                right = right.to(device=left.device)
            return left == right
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") or hasattr(right, "shape"):
            return np.asarray(left) == np.asarray(right)
    except Exception:
        pass
    if isinstance(left, list) and isinstance(right, list):
        return [equal_values(left_item, right_item) for left_item, right_item in zip(left, right)]
    return 1.0 if left == right else 0.0


def flatten(value: Any) -> list[Any]:
    """Flatten nested lists or tensor-like values."""
    try:
        import torch

        if hasattr(value, "shape"):
            return [item for item in value.reshape(-1)]
    except Exception:
        pass
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if isinstance(value, list):
        result: list[Any] = []
        for item in value:
            result.extend(flatten(item))
        return result
    return [value]


def is_valid_number(value: Any) -> bool:
    """Return whether a flattened scalar should contribute to an aggregate."""
    if value is None:
        return False
    try:
        return not math.isnan(float(value))
    except (TypeError, ValueError):
        return True


def negate_values(value: Any) -> Any:
    """Negate nested values."""
    if value is None:
        return None
    try:
        return -value
    except Exception:
        pass
    return map_values(value, lambda item: None if item is None else -float(item))


def map_values(value: Any, fn: Callable[[Any], Any]) -> Any:
    """Map over nested list leaves."""
    try:
        import torch

        if hasattr(value, "shape"):
            try:
                mapped = fn(value)
            except Exception:
                return torch.zeros_like(value) if fn(1) == 0 else value
            if mapped is None:
                return None
            if hasattr(mapped, "shape"):
                return mapped
            if mapped == 0:
                return torch.zeros_like(value)
            return mapped
    except Exception:
        pass
    if isinstance(value, list):
        return [map_values(item, fn) for item in value]
    return fn(value)


def dot_last_dim(left: Any, right: Any) -> Any:
    """Dot product over final dimension."""
    try:
        import torch

        if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
            if not isinstance(left, torch.Tensor):
                left = torch.as_tensor(
                    left,
                    dtype=getattr(right, "dtype", None),
                    device=getattr(right, "device", None),
                )
            if not isinstance(right, torch.Tensor):
                right = torch.as_tensor(
                    right,
                    dtype=getattr(left, "dtype", None),
                    device=getattr(left, "device", None),
                )
            return (left * right).sum(dim=-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") or hasattr(right, "shape"):
            return (np.asarray(left) * np.asarray(right)).sum(axis=-1)
    except Exception:
        pass
    try:
        return (left * right).sum(dim=-1)
    except Exception:
        pass
    return _dot_nested(left, right)


def _dot_nested(left: Any, right: Any) -> Any:
    if isinstance(left, list) and isinstance(right, list):
        if _is_vector(left) and _is_vector(right):
            return sum(
                float(l_item) * float(r_item) for l_item, r_item in zip(left, right, strict=True)
            )
        if _is_vector(right):
            return [_dot_nested(l_item, right) for l_item in left]
        if _is_vector(left):
            return [_dot_nested(left, r_item) for r_item in right]
        left_shape = _shape_of(left)
        right_shape = _shape_of(right)
        if len(right_shape) < len(left_shape) and left_shape[-len(right_shape) :] == right_shape:
            return [_dot_nested(l_item, right) for l_item in left]
        if len(left_shape) < len(right_shape) and right_shape[-len(left_shape) :] == left_shape:
            return [_dot_nested(left, r_item) for r_item in right]
        if len(left) == len(right):
            return [_dot_nested(l_item, r_item) for l_item, r_item in zip(left, right)]
        return [_dot_nested(l_item, right) for l_item in left]
    return left


def _head_results_from_nested(z: Any, W_O: Any) -> Any:
    if _shape_of(z) == ():
        return z
    shape = _shape_of(z)
    w_o_shape = _shape_of(W_O)
    if _has_aligned_layer_axis(z, W_O):
        return [
            _head_results_from_nested(layer_z, W_O[layer_index])
            for layer_index, layer_z in enumerate(z)
        ]
    if len(w_o_shape) == 4 and len(shape) >= 2 and shape[-2:] == w_o_shape[1:3]:
        if w_o_shape[0] == 1:
            W_O = W_O[0]
        else:
            raise ValueError(
                "W_O has a layer dimension but z has no matching leading layer axis. "
                "Pass W_O[layer] or z shaped [layer, ..., head, d_head]."
            )
    if len(shape) == 2:
        return [_matvec(head_z, W_O[head_index]) for head_index, head_z in enumerate(z)]
    return [_head_results_from_nested(item, W_O) for item in z]


def _attention_pattern_score_nested(
    pattern: Any,
    offset: int,
    min_dest_pos: int | None = None,
) -> Any:
    shape = _shape_of(pattern)
    if len(shape) < 2:
        raise ValueError(f"Attention pattern must have at least two dimensions, got {shape!r}.")
    if len(shape) > 2:
        return [_attention_pattern_score_nested(item, offset, min_dest_pos) for item in pattern]

    dest_len, src_len = shape
    values: list[float] = []
    for dest_pos in range(dest_len):
        if min_dest_pos is not None and dest_pos < min_dest_pos:
            continue
        src_pos = dest_pos + offset
        if 0 <= src_pos < src_len:
            values.append(float(pattern[dest_pos][src_pos]))
    if not values:
        return 0.0
    return sum(values) / len(values)


def _slice_diagonal_by_dest_pos(diag: Any, offset: int, min_dest_pos: int | None) -> Any:
    if min_dest_pos is None:
        return diag
    start_dest = max(0, -offset)
    start = max(0, min_dest_pos - start_dest)
    return diag[..., start:]


def _normalize_w_o_for_z(z: Any, W_O: Any) -> Any:
    if _has_aligned_layer_axis(z, W_O):
        return W_O
    z_shape = _shape_of(z)
    w_o_shape = _shape_of(W_O)
    if len(w_o_shape) == 4 and len(z_shape) >= 2:
        expected_head_shape = w_o_shape[1:3]
        if z_shape[-2:] == expected_head_shape:
            if w_o_shape[0] == 1:
                return W_O[0]
            raise ValueError(
                "W_O has a layer dimension but z has no matching leading layer axis. "
                "Pass W_O[layer] or z shaped [layer, ..., head, d_head]."
            )
    return W_O


def _has_aligned_layer_axis(z: Any, W_O: Any) -> bool:
    z_shape = _shape_of(z)
    w_o_shape = _shape_of(W_O)
    return (
        len(w_o_shape) == 4
        and len(z_shape) >= 5
        and z_shape[0] == w_o_shape[0]
        and z_shape[-2:] == w_o_shape[1:3]
    )


def matmul_last_dim(left: Any, right: Any) -> Any:
    """Multiply `left[..., d] @ right[d, out]` for nested-list values."""
    if _shape_of(left) == ():
        return left
    if _is_vector(left):
        return _matvec(left, right)
    return [matmul_last_dim(item, right) for item in left]


def _matvec(vector: Any, matrix: Any) -> list[float]:
    matrix_rows = matrix.tolist() if hasattr(matrix, "tolist") else matrix
    vector_values = vector.tolist() if hasattr(vector, "tolist") else vector
    if not matrix_rows:
        return []
    return [
        sum(
            float(vector_values[row_index]) * float(row[col_index])
            for row_index, row in enumerate(matrix_rows)
        )
        for col_index in range(len(matrix_rows[0]))
    ]


def _is_vector(value: Any) -> bool:
    return isinstance(value, list) and (not value or not isinstance(value[0], list))


def _shape_of(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, list):
        if not value:
            return (0,)
        return (len(value), *_shape_of(value[0]))
    return ()


def _slice_nested_dim(value: Any, index: slice, *, dim: int) -> Any:
    shape = _shape_of(value)
    rank = len(shape)
    if rank == 0:
        return value
    if dim < 0:
        dim = rank + dim
    if dim == 0:
        return value[index]
    return [_slice_nested_dim(item, index, dim=dim - 1) for item in value]


def and_values(left: Any, right: Any) -> Any:
    """Elementwise boolean and for nested-list masks."""
    try:
        if hasattr(left, "shape") or hasattr(right, "shape"):
            return left.bool() & right.bool()
    except Exception:
        pass
    if isinstance(left, list) and isinstance(right, list):
        return [and_values(left_item, right_item) for left_item, right_item in zip(left, right)]
    return bool(left) and bool(right)
