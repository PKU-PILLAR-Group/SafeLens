"""Small analysis helpers for logits, losses, ablations, and head detection."""

from __future__ import annotations

import logging
import math
import random
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

from SafeLens.core.hooks import ActivationCache, HookPoint, clone_activation

HEAD_NAMES = ("previous_token_head", "duplicate_token_head", "induction_head")
ERROR_MEASURES = ("abs", "mul")

INVALID_HEAD_NAME_ERR = (
    f"detection_pattern must be a Tensor or one of head names: {list(HEAD_NAMES)}; got %s"
)
SEQ_LEN_ERR = "The sequence must be non-empty and must fit within the model's context window."
DET_PAT_NOT_SQUARE_ERR = (
    "The detection pattern must be a lower triangular matrix of shape "
    "(sequence_length, sequence_length); sequence_length=%d; got detection pattern of shape %s"
)


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
    if _is_sequence(values) and not values:
        return []
    if _is_sequence(values) and values and _is_sequence(values[0]):
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
    if _is_sequence(probs) and probs and _is_sequence(probs[0]):
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
    losses = negate_values(lm_log_probs(logits, tokens))
    if attention_mask is not None:
        mask = causal_lm_loss_mask(attention_mask)
        if per_token:
            return zero_mask_values(losses, mask)
        losses = mask_values(losses, mask)
    if per_token:
        return losses
    values = [float(value) for value in flatten(losses) if is_valid_number(value)]
    if not values:
        return float("nan")
    return sum(values) / len(values)


def lm_accuracy(
    logits: Any,
    tokens: Any,
    attention_mask: Any | None = None,
    *,
    per_token: bool = False,
) -> Any:
    """Return next-token prediction accuracy for causal language modeling."""
    predictions = argmax_last_dim(slice_second_last_dim(logits, stop=-1))
    targets = slice_last_dim(tokens, start=1)
    correct = equal_values(predictions, targets)
    if attention_mask is None:
        if per_token:
            return correct
        values = flatten(correct)
        if not values:
            return float("nan")
        return sum(float(value) for value in values) / len(values)
    masked = mask_values(correct, causal_lm_loss_mask(attention_mask))
    if per_token:
        return masked
    values = [float(value) for value in flatten(masked) if is_valid_number(value)]
    if not values:
        return float("nan")
    return sum(values) / len(values)


def topk_tokens(logits: Any, k: int = 5) -> Any:
    """Return top-k token indices and values for the final dimension."""
    k = _clamp_top_k(logits, k)
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
    if _is_sequence(logits) and logits and _is_sequence(logits[0]):
        return [topk_tokens(row, k=k) for row in logits]
    pairs = sorted(enumerate(logits), key=lambda item: float(item[1]), reverse=True)[:k]
    return [index for index, _value in pairs], [value for _index, value in pairs]


def logits_to_df(logits: Any, tokenizer: Any | None = None, top_k: int | None = None) -> Any:
    """Convert a 1-D logit vector into a probability-sorted pandas DataFrame."""

    import pandas as pd

    values = [float(value) for value in _as_flat_list(logits)]
    log_probs = _log_softmax_vector(values)
    probabilities = [math.exp(value) for value in log_probs]
    order = sorted(range(len(values)), key=lambda index: probabilities[index], reverse=True)
    if top_k is not None:
        order = order[:top_k]

    data: dict[str, Any] = {"token_index": order}
    if tokenizer is not None:
        data["token_string"] = [_decode_token_for_dataframe(tokenizer, index) for index in order]
    data["logit"] = [values[index] for index in order]
    data["log_prob"] = [log_probs[index] for index in order]
    data["probability"] = [probabilities[index] for index in order]
    return pd.DataFrame(data)


def sample_logits(
    final_logits: Any,
    top_k: int | None = None,
    top_p: float | None = None,
    temperature: float = 1.0,
    freq_penalty: float = 0.0,
    repetition_penalty: float = 1.0,
    tokens: Any | None = None,
) -> Any:
    """Sample token IDs from final logits with TransformerLens-style controls."""

    if top_k is not None:
        assert top_k > 0, "top_k has to be greater than 0"
    if top_p is not None:
        assert 1.0 >= top_p > 0.0, "top_p has to be in (0, 1]"
    assert temperature >= 0.0, "temperature has to be non-negative"
    assert freq_penalty >= 0.0, "freq_penalty has to be non-negative"
    assert repetition_penalty > 0.0, "repetition_penalty has to be greater than 0"

    torch_result = _sample_logits_torch(
        final_logits,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        freq_penalty=freq_penalty,
        repetition_penalty=repetition_penalty,
        tokens=tokens,
    )
    if torch_result is not None:
        return torch_result

    return _sample_logits_python(
        final_logits,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        freq_penalty=freq_penalty,
        repetition_penalty=repetition_penalty,
        tokens=tokens,
    )


def _clamp_top_k(logits: Any, k: int) -> int:
    if k < 0:
        raise ValueError("k must be non-negative.")
    shape = getattr(logits, "shape", None)
    if shape is not None and len(shape) > 0:
        return min(k, int(shape[-1]))
    value = logits
    while _is_sequence(value) and value and _is_sequence(value[0]):
        value = value[0]
    if _is_sequence(value):
        return min(k, len(value))
    return k


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
        return float(cast(Any, item() if callable(item) else value))

    if _is_sequence(logits) and logits and _is_sequence(logits[0]):
        if logits[0] and _is_sequence(logits[0][0]):
            row = logits[0][pos]
        else:
            row = logits[pos]
    else:
        row = logits
    return float(row[correct_token]) - float(row[incorrect_token])


def test_prompt(
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run a TransformerLens-style prompt sanity check.

    Supports both SafeLens' structured call shape
    ``test_prompt(model, prompt, correct_token, incorrect_token=None, ...)`` and
    TransformerLens' exploratory call shape
    ``test_prompt(prompt, answer, model, ...)``. Both return a structured result;
    TL-style calls additionally include answer-token ranks.
    """
    if len(args) >= 3 and isinstance(args[0], str) and not isinstance(args[2], str | int):
        return _test_prompt_transformerlens(*args, **kwargs)
    return _test_prompt_structured(*args, **kwargs)


def _test_prompt_structured(
    model: Any,
    prompt: str,
    correct_token: str | int,
    incorrect_token: str | int | None = None,
    *,
    prepend_bos: bool = True,
    top_k: int = 10,
    return_type: str = "logits",
    print_details: bool = False,
) -> dict[str, Any]:
    """Run a TransformerLens-style next-token prompt sanity check.

    The helper mirrors the common ``transformer_lens.utils.test_prompt`` workflow
    without depending on TransformerLens: run a prompt, inspect final-position
    logits, compare a correct token against an optional incorrect token, and
    return top-k predictions in a structured form.
    """
    correct_token_id = _resolve_single_token(model, correct_token)
    incorrect_token_id = (
        None if incorrect_token is None else _resolve_single_token(model, incorrect_token)
    )
    logits = model(prompt, return_type=return_type, prepend_bos=prepend_bos)
    final_logits = _final_position_logits(logits)
    predicted_token_id = _argmax_token_id(final_logits)
    top_indices, top_values = topk_tokens(final_logits, k=top_k)
    top_token_ids = _as_int_list(top_indices)
    top_token_values = [float(value) for value in _as_flat_list(top_values)]
    result = {
        "prompt": prompt,
        "correct_token": correct_token,
        "correct_token_id": correct_token_id,
        "correct_logit": _index_last_dim_float(final_logits, correct_token_id),
        "predicted_token_id": predicted_token_id,
        "predicted_token": _decode_single_token_if_possible(model, predicted_token_id),
        "is_correct": predicted_token_id == correct_token_id,
        "top_tokens": [
            {
                "token_id": token_id,
                "token": _decode_single_token_if_possible(model, token_id),
                "logit": logit_value,
            }
            for token_id, logit_value in zip(top_token_ids, top_token_values, strict=False)
        ],
        "logits": logits,
    }
    if incorrect_token_id is not None:
        result.update(
            {
                "incorrect_token": incorrect_token,
                "incorrect_token_id": incorrect_token_id,
                "incorrect_logit": _index_last_dim_float(final_logits, incorrect_token_id),
            }
        )
        result["logit_diff"] = float(result["correct_logit"]) - float(result["incorrect_logit"])
    if print_details:
        _print_test_prompt_result(result)
    return result


test_prompt.__test__ = False  # type: ignore[attr-defined]


def _test_prompt_transformerlens(
    prompt: str,
    answer: str | Sequence[str],
    model: Any,
    prepend_space_to_answer: bool = True,
    print_details: bool = True,
    prepend_bos: bool | None = None,
    top_k: int = 10,
) -> dict[str, Any]:
    answers = [answer] if isinstance(answer, str) else list(answer)
    using_multiple_answers = len(answers) > 1
    if prepend_space_to_answer:
        answers = [
            candidate if str(candidate).startswith(" ") else f" {candidate}"
            for candidate in answers
        ]

    prompt_tokens = _model_to_tokens(model, prompt, prepend_bos=prepend_bos)
    answer_tokens = _model_to_tokens(model, answers, prepend_bos=False)
    if using_multiple_answers:
        answer_tokens = _slice_last_dim(answer_tokens, stop=1)
    repeated_prompt_tokens = _repeat_rows(prompt_tokens, _shape_of(answer_tokens)[0])
    tokens = _concat_second_dim(repeated_prompt_tokens, answer_tokens)

    prompt_str_tokens = _model_to_str_tokens(model, prompt, prepend_bos=prepend_bos)
    answer_str_tokens_list = [
        _model_to_str_tokens(model, candidate, prepend_bos=False) for candidate in answers
    ]
    prompt_length = len(prompt_str_tokens)
    answer_length = 1 if using_multiple_answers else len(answer_str_tokens_list[0])
    logits = model(tokens)
    probabilities = softmax(logits)

    answer_ranks: list[list[tuple[str, int]]] = []
    token_results: list[dict[str, Any]] = []
    for token_position in range(prompt_length, prompt_length + answer_length):
        answer_token_ids = _column(tokens, token_position)
        answer_strings = [
            candidate[token_position - prompt_length] for candidate in answer_str_tokens_list
        ]
        token_logits = _select_second_dim(logits, token_position - 1)
        token_probabilities = _select_second_dim(probabilities, token_position - 1)
        ranks = [
            _rank_token(_row(token_probabilities, row_index), int(token_id))
            for row_index, token_id in enumerate(answer_token_ids)
        ]
        answer_ranks.append(
            [
                (answer_string, rank)
                for answer_string, rank in zip(answer_strings, ranks, strict=False)
            ]
        )
        token_result = {
            "position": token_position,
            "answer_token_ids": [int(token_id) for token_id in answer_token_ids],
            "answer_tokens": answer_strings,
            "answer_ranks": ranks,
            "top_tokens": _top_token_records(model, _row(token_logits, 0), k=top_k),
        }
        if using_multiple_answers:
            token_result["top_tokens_by_answer"] = [
                _top_token_records(model, _row(token_logits, row_index), k=top_k)
                for row_index in range(len(answer_token_ids))
            ]
        token_results.append(token_result)

    result = {
        "prompt": prompt,
        "answer": answer,
        "answers": answers,
        "tokens": tokens,
        "logits": logits,
        "prompt_tokens": prompt_tokens,
        "answer_tokens": answer_tokens,
        "prompt_str_tokens": prompt_str_tokens,
        "answer_str_tokens": answer_str_tokens_list,
        "answer_ranks": [row[0] for row in answer_ranks]
        if not using_multiple_answers
        else answer_ranks,
        "token_results": token_results,
        "is_correct": all(rank == 0 for row in answer_ranks for _token, rank in row),
    }
    if print_details:
        _print_transformerlens_test_prompt_result(result)
    return result


def residual_stack_to_logits(
    residual_stack: Any,
    unembed: Any,
    unembed_bias: Any | None = None,
) -> Any:
    """Project residual components through an unembedding matrix and optional bias."""
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
            logits = residual_stack @ unembed
            return _add_unembed_bias(logits, unembed_bias)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(residual_stack, "shape") or hasattr(unembed, "shape"):
            logits = np.matmul(residual_stack, unembed)
            return _add_unembed_bias(logits, unembed_bias)
    except Exception:
        pass
    logits = matmul_last_dim(residual_stack, unembed)
    return _add_unembed_bias(logits, unembed_bias)


def direct_logit_attribution(residual_stack: Any, token_directions: Any) -> Any:
    """Project residual components onto token directions."""
    return dot_last_dim(residual_stack, token_directions)


def compute_head_results_from_z(
    z: Any,
    W_O: Any,
    *,
    has_layer_axis: bool | None = None,
) -> Any:
    """Project per-head `z` activations through `W_O` into residual-space results.

    `z` is expected to end in `[head, d_head]`, and `W_O` should be shaped
    `[head, d_head, d_model]` or `[layer, head, d_head, d_model]`.
    Leading batch/position dimensions are preserved. When `z` is stacked by
    layer but omits an explicit batch dimension, pass `has_layer_axis=True` to
    disambiguate the leading axis from a batch/position axis.
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
            if _has_aligned_layer_axis(z, W_O, has_layer_axis=has_layer_axis):
                return torch.einsum("l...hd,lhdm->l...hm", z, W_O)
            W_O = _normalize_w_o_for_z(z, W_O, has_layer_axis=has_layer_axis)
            return torch.einsum("...hd,hdm->...hm", z, W_O)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(z, "shape") and hasattr(W_O, "shape"):
            if _has_aligned_layer_axis(z, W_O, has_layer_axis=has_layer_axis):
                return np.einsum("l...hd,lhdm->l...hm", z, W_O)
            W_O = _normalize_w_o_for_z(z, W_O, has_layer_axis=has_layer_axis)
            return np.einsum("...hd,hdm->...hm", z, W_O)
    except Exception:
        pass

    W_O = _normalize_w_o_for_z(z, W_O, has_layer_axis=has_layer_axis)
    return _head_results_from_nested(z, W_O, has_layer_axis=has_layer_axis)


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
            numpy_diag = np.diagonal(array, offset=offset, axis1=-2, axis2=-1)
            numpy_diag = _slice_diagonal_by_dest_pos(numpy_diag, offset, min_dest_pos)
            if numpy_diag.shape[-1] == 0:
                return np.zeros(array.shape[:-2], dtype=array.dtype)
            return numpy_diag.mean(axis=-1)
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


def detect_head(
    model: Any,
    seq: str | Sequence[str] | Any,
    detection_pattern: Any,
    heads: Sequence[tuple[int, int]] | Mapping[int, Sequence[int]] | None = None,
    cache: ActivationCache | Mapping[Any, Any] | None = None,
    *,
    exclude_bos: bool = False,
    exclude_current_token: bool = False,
    error_measure: str = "mul",
) -> Any:
    """Search cached attention patterns for TransformerLens-style head patterns.

    This mirrors ``transformer_lens.head_detector.detect_head`` without depending
    on TransformerLens. ``detection_pattern`` can be one of
    ``"previous_token_head"``, ``"duplicate_token_head"``, ``"induction_head"``,
    or an explicit square lower-triangular pattern. Returned scores are shaped
    ``[n_layers, n_heads]`` and unselected heads are set to ``-1``.
    """
    if error_measure not in ERROR_MEASURES:
        raise ValueError(
            f"Invalid error_measure={error_measure!r}; valid values are {ERROR_MEASURES}"
        )
    if isinstance(detection_pattern, str) and _is_string_sequence(seq) and cache is None:
        scores = [
            detect_head(
                model,
                item,
                detection_pattern,
                heads=heads,
                cache=None,
                exclude_bos=exclude_bos,
                exclude_current_token=exclude_current_token,
                error_measure=error_measure,
            )
            for item in seq
        ]
        return _mean_score_matrices(scores)

    tokens = _tokenize_head_detector_sequence(model, seq)
    seq_len = _sequence_length(tokens)
    cfg = _model_cfg(model)
    n_ctx = _cfg_int(cfg, "n_ctx")
    if seq_len <= 1 or (n_ctx is not None and seq_len >= n_ctx):
        raise ValueError(SEQ_LEN_ERR)

    if isinstance(detection_pattern, str):
        if detection_pattern not in HEAD_NAMES:
            raise ValueError(INVALID_HEAD_NAME_ERR % detection_pattern)
        detection_pattern = _named_head_detection_pattern(detection_pattern, tokens)

    detection_pattern = _move_pattern_to_token_device(detection_pattern, tokens, cfg)
    _validate_detection_pattern(detection_pattern, seq_len)
    if error_measure == "mul" and not _pattern_values_are_binary(detection_pattern):
        logging.warning(
            "Using detection pattern with values other than 0 or 1 with error_measure 'mul'"
        )

    if cache is None:
        run_with_cache = getattr(model, "run_with_cache", None)
        if not callable(run_with_cache):
            raise TypeError("detect_head requires `cache` or a model with `run_with_cache`.")
        cache_result = run_with_cache(tokens, remove_batch_dim=True)
        if not isinstance(cache_result, tuple | list) or len(cache_result) < 2:
            raise TypeError("model.run_with_cache must return an (output, cache) pair.")
        cache = cache_result[1]
        if cache is None:
            raise TypeError("model.run_with_cache returned None for cache.")
    resolved_cache = _ensure_activation_cache(cache, model)
    n_layers, n_heads = _infer_head_score_shape(model, resolved_cache, heads)
    layer_to_heads = _normalize_head_selection(heads, n_layers=n_layers, n_heads=n_heads)
    matches = _make_head_score_matrix(n_layers, n_heads, cfg, tokens, resolved_cache)

    for layer, layer_heads in layer_to_heads.items():
        layer_patterns = _normalize_cached_layer_attention_pattern(
            _get_cached_attention_pattern(resolved_cache, layer),
            n_heads=n_heads,
            seq_len=seq_len,
        )
        for head in layer_heads:
            head_pattern = _index_head_attention_pattern(layer_patterns, head)
            score = compute_head_attention_similarity_score(
                head_pattern,
                detection_pattern=detection_pattern,
                exclude_bos=exclude_bos,
                exclude_current_token=exclude_current_token,
                error_measure=error_measure,
            )
            _set_head_score(matches, layer, head, score)
    return matches


def get_previous_token_head_detection_pattern(tokens: Any) -> Any:
    """Return a lower-triangular pattern for attention to the previous token."""
    seq_len = _sequence_length(tokens)
    try:
        import torch

        if isinstance(tokens, torch.Tensor):
            pattern = torch.zeros((seq_len, seq_len), dtype=torch.float32, device=tokens.device)
            if seq_len > 1:
                pattern[1:, :-1] = torch.eye(
                    seq_len - 1, dtype=pattern.dtype, device=pattern.device
                )
            return torch.tril(pattern)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(tokens, "shape"):
            numpy_pattern = np.zeros((seq_len, seq_len), dtype=float)
            if seq_len > 1:
                numpy_pattern[1:, :-1] = np.eye(seq_len - 1)
            return np.tril(numpy_pattern)
    except Exception:
        pass
    return [[1.0 if dest == src + 1 else 0.0 for src in range(seq_len)] for dest in range(seq_len)]


def get_duplicate_token_head_detection_pattern(tokens: Any) -> Any:
    """Return a pattern whose entries mark earlier equal tokens."""
    values = _token_sequence_values(tokens)
    seq_len = len(values)
    try:
        import torch

        if isinstance(tokens, torch.Tensor):
            token_tensor = torch.as_tensor(values, device=tokens.device)
            pattern = token_tensor[:, None].eq(token_tensor[None, :]).to(torch.float32)
            pattern.fill_diagonal_(0)
            return torch.tril(pattern)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(tokens, "shape"):
            token_array = np.asarray(values)
            pattern = (token_array[:, None] == token_array[None, :]).astype(float)
            np.fill_diagonal(pattern, 0)
            return np.tril(pattern)
    except Exception:
        pass
    return [
        [1.0 if dest > src and values[dest] == values[src] else 0.0 for src in range(seq_len)]
        for dest in range(seq_len)
    ]


def get_induction_head_detection_pattern(tokens: Any) -> Any:
    """Return a duplicate-token pattern shifted right for induction heads."""
    duplicate_pattern = get_duplicate_token_head_detection_pattern(tokens)
    try:
        import torch

        if isinstance(duplicate_pattern, torch.Tensor):
            shifted = torch.roll(duplicate_pattern, shifts=1, dims=1)
            shifted[:, 0] = 0
            return torch.tril(shifted)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(duplicate_pattern, "shape"):
            numpy_shifted = np.roll(np.asarray(duplicate_pattern), shift=1, axis=1)
            numpy_shifted[:, 0] = 0
            return np.tril(numpy_shifted)
    except Exception:
        pass
    seq_len = len(duplicate_pattern)
    return [
        [
            float(src > 0 and dest >= src and duplicate_pattern[dest][src - 1])
            for src in range(seq_len)
        ]
        for dest in range(seq_len)
    ]


def get_supported_heads() -> list[str]:
    """Print and return supported TransformerLens-style head detector names."""
    heads = [str(name) for name in HEAD_NAMES]
    print(f"Supported heads: {heads}")
    return heads


def compute_head_attention_similarity_score(
    attention_pattern: Any,
    detection_pattern: Any,
    *,
    exclude_bos: bool,
    exclude_current_token: bool,
    error_measure: str,
) -> float:
    """Compute similarity between a single head pattern and a detector pattern."""
    if error_measure not in ERROR_MEASURES:
        raise ValueError(
            f"Invalid error_measure={error_measure!r}; valid values are {ERROR_MEASURES}"
        )
    _validate_square_attention_pattern(attention_pattern)
    try:
        import torch

        if isinstance(attention_pattern, torch.Tensor) or isinstance(
            detection_pattern, torch.Tensor
        ):
            attention = _as_torch_float_tensor(attention_pattern, like=detection_pattern).clone()
            detection = _as_torch_float_tensor(detection_pattern, like=attention)
            if error_measure == "mul":
                if exclude_bos:
                    attention[:, 0] = 0
                if exclude_current_token:
                    attention.fill_diagonal_(0)
                return float(((attention * detection).sum() / attention.sum()).item())
            abs_diff = (attention - detection).abs()
            if not torch.allclose(abs_diff, torch.tril(abs_diff)):
                raise AssertionError(
                    "Attention pattern and detection pattern differ above the diagonal."
                )
            if exclude_bos:
                abs_diff[:, 0] = 0
            if exclude_current_token:
                abs_diff.fill_diagonal_(0)
            return 1 - round(float(abs_diff.mean().item() * len(abs_diff)), 3)
    except ImportError:
        pass
    try:
        import numpy as np

        if hasattr(attention_pattern, "shape") or hasattr(detection_pattern, "shape"):
            attention = np.asarray(attention_pattern, dtype=float).copy()
            detection = np.asarray(detection_pattern, dtype=float)
            if error_measure == "mul":
                if exclude_bos:
                    attention[:, 0] = 0
                if exclude_current_token:
                    np.fill_diagonal(attention, 0)
                denominator = attention.sum()
                return float(
                    np.nan if denominator == 0 else (attention * detection).sum() / denominator
                )
            numpy_abs_diff = np.abs(attention - detection)
            if not np.allclose(numpy_abs_diff, np.tril(numpy_abs_diff)):
                raise AssertionError(
                    "Attention pattern and detection pattern differ above the diagonal."
                )
            if exclude_bos:
                numpy_abs_diff[:, 0] = 0
            if exclude_current_token:
                np.fill_diagonal(numpy_abs_diff, 0)
            return 1 - round(float(numpy_abs_diff.mean() * len(numpy_abs_diff)), 3)
    except ImportError:
        pass

    attention = _nested_float_matrix(attention_pattern)
    detection = _nested_float_matrix(detection_pattern)
    if error_measure == "mul":
        numerator = 0.0
        denominator = 0.0
        for dest, row in enumerate(attention):
            for src, value in enumerate(row):
                if exclude_bos and src == 0:
                    value = 0.0
                if exclude_current_token and src == dest:
                    value = 0.0
                numerator += value * detection[dest][src]
                denominator += value
        return numerator / denominator if denominator else float("nan")

    nested_abs_diff: list[list[float]] = []
    for dest, row in enumerate(attention):
        diff_row = []
        for src, value in enumerate(row):
            diff = abs(value - detection[dest][src])
            if src > dest and diff:
                raise AssertionError(
                    "Attention pattern and detection pattern differ above the diagonal."
                )
            if exclude_bos and src == 0:
                diff = 0.0
            if exclude_current_token and src == dest:
                diff = 0.0
            diff_row.append(diff)
        nested_abs_diff.append(diff_row)
    total = sum(sum(row) for row in nested_abs_diff)
    size = len(nested_abs_diff)
    return 1 - round(total / max(1, size * size) * size, 3)


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


def _is_string_sequence(value: Any) -> bool:
    return _is_sequence(value) and all(isinstance(item, str) for item in value)


def _tokenize_head_detector_sequence(model: Any, seq: Any) -> Any:
    if isinstance(seq, str):
        to_tokens = getattr(model, "to_tokens", None)
        if not callable(to_tokens):
            raise TypeError("String sequences require a model with `to_tokens`.")
        tokens = to_tokens(seq)
        return _move_tokens_to_cfg_device(tokens, _model_cfg(model))
    if _is_string_sequence(seq):
        to_tokens = getattr(model, "to_tokens", None)
        if not callable(to_tokens):
            raise TypeError("String sequences require a model with `to_tokens`.")
        tokens = to_tokens(seq)
        return _move_tokens_to_cfg_device(tokens, _model_cfg(model))
    return _move_tokens_to_cfg_device(seq, _model_cfg(model))


def _move_tokens_to_cfg_device(tokens: Any, cfg: Any) -> Any:
    device = getattr(cfg, "device", None)
    to = getattr(tokens, "to", None)
    if device is not None and callable(to):
        try:
            return to(device)
        except Exception:
            return tokens
    return tokens


def _model_cfg(model: Any) -> Any:
    try:
        cfg = getattr(model, "cfg", None)
    except Exception:
        cfg = None
    return cfg if cfg is not None else getattr(model, "config", None)


def _cfg_int(cfg: Any, *names: str) -> int | None:
    if cfg is None:
        return None
    for name in names:
        value = getattr(cfg, name, None)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _sequence_length(tokens: Any) -> int:
    shape = _shape_of(tokens)
    if not shape:
        return 0
    return int(shape[-1])


def _token_sequence_values(tokens: Any) -> list[Any]:
    value = tokens
    shape = _shape_of(value)
    if len(shape) >= 2:
        value = value[0]
    detach = getattr(value, "detach", None)
    if callable(detach):
        value = detach()
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    while _is_sequence(value) and value:
        sequence_value = cast(Sequence[Any], value)
        if not _is_sequence(sequence_value[0]):
            break
        value = sequence_value[0]
    if _is_sequence(value):
        return list(cast(Sequence[Any], value))
    return [value]


def _named_head_detection_pattern(name: str, tokens: Any) -> Any:
    if name == "previous_token_head":
        return get_previous_token_head_detection_pattern(tokens)
    if name == "duplicate_token_head":
        return get_duplicate_token_head_detection_pattern(tokens)
    if name == "induction_head":
        return get_induction_head_detection_pattern(tokens)
    raise ValueError(INVALID_HEAD_NAME_ERR % name)


def _move_pattern_to_token_device(pattern: Any, tokens: Any, cfg: Any) -> Any:
    try:
        import torch

        if isinstance(tokens, torch.Tensor):
            if isinstance(pattern, torch.Tensor):
                return pattern.to(device=tokens.device)
            return torch.as_tensor(pattern, dtype=torch.float32, device=tokens.device)
    except Exception:
        pass
    device = getattr(cfg, "device", None)
    to = getattr(pattern, "to", None)
    if device is not None and callable(to):
        try:
            return to(device)
        except Exception:
            pass
    return pattern


def _validate_detection_pattern(pattern: Any, seq_len: int) -> None:
    shape = _shape_of(pattern)
    if shape != (seq_len, seq_len) or not _is_lower_triangular(pattern):
        raise ValueError(DET_PAT_NOT_SQUARE_ERR % (seq_len, shape))


def _validate_square_attention_pattern(pattern: Any) -> None:
    shape = _shape_of(pattern)
    if len(shape) != 2 or shape[0] != shape[1]:
        raise AssertionError(f"Attention pattern is not square; got shape {shape!r}")


def _is_lower_triangular(pattern: Any) -> bool:
    try:
        import torch

        if isinstance(pattern, torch.Tensor):
            return bool(torch.allclose(pattern, torch.tril(pattern)))
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(pattern, "shape"):
            array = np.asarray(pattern)
            return bool(np.allclose(array, np.tril(array)))
    except Exception:
        pass
    matrix = _nested_float_matrix(pattern)
    return all(
        abs(value) == 0 for row_index, row in enumerate(matrix) for value in row[row_index + 1 :]
    )


def _pattern_values_are_binary(pattern: Any) -> bool:
    try:
        import torch

        if isinstance(pattern, torch.Tensor):
            detached_pattern = cast(Any, pattern.detach().cpu())
            unique_values = set(detached_pattern.unique().tolist())
            return unique_values.issubset({0, 1})
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(pattern, "shape"):
            return set(np.asarray(pattern).reshape(-1).tolist()).issubset({0, 1})
    except Exception:
        pass
    return set(float(value) for value in flatten(pattern)).issubset({0.0, 1.0})


def _ensure_activation_cache(
    cache: ActivationCache | Mapping[Any, Any], model: Any
) -> ActivationCache:
    if isinstance(cache, ActivationCache):
        if cache.model is None:
            cache.model = model
        return cache
    return ActivationCache(dict(cache), model=model)


def _infer_head_score_shape(
    model: Any,
    cache: ActivationCache,
    heads: Sequence[tuple[int, int]] | Mapping[int, Sequence[int]] | None,
) -> tuple[int, int]:
    cfg = _model_cfg(model)
    n_layers = _cfg_int(cfg, "n_layers", "num_hidden_layers", "n_layer", "num_layers")
    n_heads = _cfg_int(cfg, "n_heads", "num_attention_heads", "n_head", "num_heads")
    cache_layers: list[int] = []
    cache_head_counts: list[int] = []
    for key in cache:
        layer = _parse_pattern_cache_layer(key)
        if layer is None:
            continue
        cache_layers.append(layer)
        pattern = _get_raw_cache_value(cache, key)
        shape = _shape_of(pattern)
        if len(shape) == 4:
            cache_head_counts.append(int(shape[1]))
        elif len(shape) == 3:
            cache_head_counts.append(int(shape[0]))
        elif len(shape) == 2:
            cache_head_counts.append(1)
    head_layers, head_indices = _heads_bounds(heads)
    if n_layers is None:
        candidates = cache_layers + head_layers
        n_layers = max(candidates) + 1 if candidates else 0
    if n_heads is None:
        candidates = cache_head_counts + [head + 1 for head in head_indices]
        n_heads = max(candidates) if candidates else 0
    if n_layers <= 0 or n_heads <= 0:
        raise ValueError("Could not infer number of layers and heads for head detection.")
    return int(n_layers), int(n_heads)


def _parse_pattern_cache_layer(key: Any) -> int | None:
    if isinstance(key, tuple) and key:
        if (
            str(key[0])
            in {
                "pattern",
                "attn",
                "hook_pattern",
                "decoder_pattern",
                "cross_pattern",
            }
            and len(key) >= 2
        ):
            try:
                return int(key[1])
            except (TypeError, ValueError):
                return None
    if not isinstance(key, str):
        return None
    match = re.search(r"(?:blocks\.|encoder\.|decoder\.|layer_)(\d+)", key)
    if match is None or "pattern" not in key:
        return None
    return int(match.group(1))


def _heads_bounds(
    heads: Sequence[tuple[int, int]] | Mapping[int, Sequence[int]] | None,
) -> tuple[list[int], list[int]]:
    if heads is None:
        return [], []
    if isinstance(heads, Mapping):
        layers = [int(layer) for layer in heads]
        head_indices = [int(head) for layer_heads in heads.values() for head in layer_heads]
        return layers, head_indices
    layers = [int(layer) for layer, _head in heads]
    head_indices = [int(head) for _layer, head in heads]
    return layers, head_indices


def _normalize_head_selection(
    heads: Sequence[tuple[int, int]] | Mapping[int, Sequence[int]] | None,
    *,
    n_layers: int,
    n_heads: int,
) -> dict[int, list[int]]:
    if heads is None:
        return {layer: list(range(n_heads)) for layer in range(n_layers)}
    if isinstance(heads, Mapping):
        layer_to_heads = {
            int(layer): [int(head) for head in layer_heads] for layer, layer_heads in heads.items()
        }
    else:
        layer_to_heads = {}
        for layer, head in heads:
            layer_to_heads.setdefault(int(layer), []).append(int(head))
    for layer, layer_heads in layer_to_heads.items():
        if layer < 0 or layer >= n_layers:
            raise ValueError(f"Head layer index {layer} is outside [0, {n_layers}).")
        for head in layer_heads:
            if head < 0 or head >= n_heads:
                raise ValueError(f"Head index {head} is outside [0, {n_heads}).")
    return layer_to_heads


def _make_head_score_matrix(
    n_layers: int,
    n_heads: int,
    cfg: Any,
    tokens: Any,
    cache: ActivationCache,
) -> Any:
    first_pattern = _first_cached_attention_pattern(cache)
    try:
        import torch

        if isinstance(tokens, torch.Tensor) or isinstance(first_pattern, torch.Tensor):
            dtype = _torch_dtype_from_cfg(cfg, default=torch.float32)
            device = getattr(tokens, "device", None)
            if device is None and isinstance(first_pattern, torch.Tensor):
                device = first_pattern.device
            if device is None:
                device = getattr(cfg, "device", None)
            return -torch.ones((n_layers, n_heads), dtype=dtype, device=device)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(tokens, "shape") or hasattr(first_pattern, "shape"):
            return -np.ones((n_layers, n_heads), dtype=float)
    except Exception:
        pass
    return [[-1.0 for _head in range(n_heads)] for _layer in range(n_layers)]


def _torch_dtype_from_cfg(cfg: Any, *, default: Any) -> Any:
    try:
        import torch
    except Exception:
        return default
    dtype = getattr(cfg, "dtype", None)
    if dtype is None:
        return default
    if isinstance(dtype, torch.dtype):
        return dtype
    return {
        "float16": torch.float16,
        "torch.float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "torch.bfloat16": torch.bfloat16,
        "float32": torch.float32,
        "torch.float32": torch.float32,
        "float64": torch.float64,
        "torch.float64": torch.float64,
    }.get(str(dtype), default)


def _first_cached_attention_pattern(cache: ActivationCache) -> Any | None:
    for key in cache:
        if _parse_pattern_cache_layer(key) is not None:
            return _get_raw_cache_value(cache, key)
    return None


def _get_cached_attention_pattern(cache: ActivationCache, layer: int) -> Any:
    keys = [
        ("pattern", layer, "attn"),
        ("pattern", layer),
        ("decoder_pattern", layer),
        ("cross_pattern", layer),
        f"blocks.{layer}.attn.hook_pattern",
        f"encoder.{layer}.attn.hook_pattern",
        f"decoder.{layer}.attn.hook_pattern",
        f"decoder.{layer}.cross_attn.hook_pattern",
        f"layer_{layer}.pattern",
        f"layer_{layer}.attn.pattern",
        f"layer_{layer}.decoder_pattern",
        f"layer_{layer}.cross_pattern",
    ]
    raw_cache = getattr(cache, "cache_dict", getattr(cache, "_cache", {}))
    for key in keys:
        if key in raw_cache:
            return raw_cache[key]
        try:
            return cache[tuple(key)]
        except KeyError:
            continue
    raise KeyError(f"Could not find cached attention pattern for layer {layer}.")


def _get_raw_cache_value(cache: ActivationCache, key: Any) -> Any:
    raw_cache = getattr(cache, "cache_dict", getattr(cache, "_cache", {}))
    return raw_cache[key]


def _normalize_cached_layer_attention_pattern(pattern: Any, *, n_heads: int, seq_len: int) -> Any:
    shape = _shape_of(pattern)
    if len(shape) == 4:
        if shape[0] != 1:
            raise ValueError(
                "detect_head expects cached attention patterns without batch dim "
                "or with batch size 1; "
                f"got shape {shape!r}."
            )
        return pattern[0]
    if len(shape) == 3:
        return pattern
    if len(shape) == 2 and n_heads == 1:
        return [pattern]
    raise ValueError(
        "Cached attention pattern must be shaped [head, q_pos, k_pos] or "
        f"[1, head, q_pos, k_pos], got {shape!r} for sequence length {seq_len}."
    )


def _index_head_attention_pattern(layer_patterns: Any, head: int) -> Any:
    return layer_patterns[head]


def _set_head_score(scores: Any, layer: int, head: int, score: float) -> None:
    try:
        scores[layer, head] = score
        return
    except Exception:
        pass
    scores[layer][head] = score


def _mean_score_matrices(scores: Sequence[Any]) -> Any:
    if not scores:
        return []
    first = scores[0]
    try:
        import torch

        if isinstance(first, torch.Tensor):
            return torch.stack(list(scores)).mean(0)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(first, "shape"):
            return np.stack([np.asarray(score) for score in scores]).mean(axis=0)
    except Exception:
        pass
    n_layers, n_heads = _shape_of(first)
    return [
        [
            sum(float(score[layer][head]) for score in scores) / len(scores)
            for head in range(n_heads)
        ]
        for layer in range(n_layers)
    ]


def _as_torch_float_tensor(value: Any, *, like: Any = None) -> Any:
    import torch

    if isinstance(value, torch.Tensor):
        if value.dtype.is_floating_point:
            return value
        return value.to(dtype=torch.float32)
    dtype = torch.float32
    device = None
    if isinstance(like, torch.Tensor):
        dtype = like.dtype if like.dtype.is_floating_point else torch.float32
        device = like.device
    return torch.as_tensor(value, dtype=dtype, device=device)


def _nested_float_matrix(value: Any) -> list[list[float]]:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if not _is_sequence(value):
        raise ValueError("Expected a matrix-like value.")
    return [[float(item) for item in row] for row in value]


def _model_to_tokens(model: Any, text: Any, *, prepend_bos: bool | None) -> Any:
    to_tokens = getattr(model, "to_tokens", None)
    if not callable(to_tokens):
        raise TypeError("TL-style test_prompt requires a model with `to_tokens`.")
    try:
        return to_tokens(text, prepend_bos=prepend_bos)
    except TypeError:
        if prepend_bos is None:
            return to_tokens(text)
        raise


def _model_to_str_tokens(model: Any, text: Any, *, prepend_bos: bool | None) -> list[str]:
    to_str_tokens = getattr(model, "to_str_tokens", None)
    if callable(to_str_tokens):
        try:
            return list(cast(Sequence[str], to_str_tokens(text, prepend_bos=prepend_bos)))
        except TypeError:
            if prepend_bos is None:
                return list(cast(Sequence[str], to_str_tokens(text)))
            raise
    tokens = _model_to_tokens(model, text, prepend_bos=prepend_bos)
    if _is_sequence(text) and not isinstance(text, str | bytes):
        first_row = _row(tokens, 0)
        return [
            str(_decode_single_token_if_possible(model, int(token_id)))
            for token_id in first_row
        ]
    row = _row(tokens, 0) if _rank(tokens) >= 2 else tokens
    return [str(_decode_single_token_if_possible(model, int(token_id))) for token_id in row]


def _slice_last_dim(value: Any, *, stop: int) -> Any:
    try:
        return value[..., :stop]
    except Exception:
        pass
    rank = _rank(value)
    if rank <= 1:
        return value[:stop]
    if rank == 2:
        return [row[:stop] for row in value]
    return [_slice_last_dim(item, stop=stop) for item in value]


def _repeat_rows(value: Any, repeats: int) -> Any:
    shape = _shape_of(value)
    if shape and shape[0] == repeats:
        return value
    repeat = getattr(value, "repeat", None)
    if callable(repeat):
        try:
            return repeat(repeats, 1)
        except Exception:
            pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.repeat(value, repeats, axis=0)
    except Exception:
        pass
    rows = _rows(value)
    if len(rows) == repeats:
        return rows
    if len(rows) != 1:
        raise ValueError(
            f"Cannot repeat prompt rows: got {len(rows)} prompt rows for {repeats} answers."
        )
    return [clone_nested_like(rows[0]) for _ in range(repeats)]


def _concat_second_dim(left: Any, right: Any) -> Any:
    try:
        import torch

        if (
            hasattr(left, "shape")
            and hasattr(right, "shape")
            and type(left).__module__.split(".")[0] == "torch"
        ):
            return torch.cat((left, right), dim=1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") and hasattr(right, "shape"):
            return np.concatenate((left, right), axis=1)
    except Exception:
        pass
    left_rows = _rows(left)
    right_rows = _rows(right)
    if len(left_rows) != len(right_rows):
        raise ValueError("Cannot concatenate token batches with different batch sizes.")
    return [
        list(left_row) + list(right_row)
        for left_row, right_row in zip(left_rows, right_rows, strict=True)
    ]


def _select_second_dim(value: Any, index: int) -> Any:
    try:
        return value[:, index]
    except Exception:
        pass
    return [row[index] for row in _rows(value)]


def _column(value: Any, index: int) -> list[int]:
    selected = _select_second_dim(value, index)
    tolist = getattr(selected, "tolist", None)
    if callable(tolist):
        selected = tolist()
    if not _is_sequence(selected):
        return [int(cast(Any, selected))]
    return [int(item) for item in cast(Sequence[Any], selected)]


def _row(value: Any, index: int) -> Any:
    try:
        return value[index]
    except Exception:
        pass
    return _rows(value)[index]


def _rows(value: Any) -> list[Any]:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if not _is_sequence(value):
        return [[value]]
    if value and _is_sequence(value[0]):
        return [row for row in value]
    return [value]


def _rank(value: Any) -> int:
    return len(_shape_of(value))


def _rank_token(probabilities: Any, token_id: int) -> int:
    row = [float(value) for value in _as_flat_list(probabilities)]
    token_probability = row[token_id]
    return sum(1 for value in row if value > token_probability)


def _top_token_records(model: Any, logits: Any, *, k: int) -> list[dict[str, Any]]:
    top_indices, top_values = topk_tokens(logits, k=k)
    top_token_ids = _as_int_list(top_indices)
    return [
        {
            "token_id": token_id,
            "token": _decode_single_token_if_possible(model, token_id),
            "logit": float(value),
        }
        for token_id, value in zip(top_token_ids, _as_flat_list(top_values), strict=False)
    ]


def clone_nested_like(value: Any) -> Any:
    if _is_sequence(value):
        return [clone_nested_like(item) for item in value]
    return value


def _resolve_single_token(model: Any, token: str | int) -> int:
    if isinstance(token, str):
        to_single_token = getattr(model, "to_single_token", None)
        if callable(to_single_token):
            return int(cast(Any, to_single_token(token)))
        try:
            return int(token)
        except ValueError as exc:
            raise TypeError(
                "String tokens require a model with `to_single_token`, or an integer string."
            ) from exc
    return int(token)


def _final_position_logits(logits: Any) -> Any:
    shape = getattr(logits, "shape", None)
    if shape is not None:
        if len(shape) >= 3:
            return logits[0, -1]
        if len(shape) == 2:
            return logits[-1]
        return logits
    if _is_sequence(logits) and logits and _is_sequence(logits[0]):
        if logits[0] and _is_sequence(logits[0][0]):
            return logits[0][-1]
        return logits[-1]
    return logits


def _argmax_token_id(logits: Any) -> int:
    argmax = argmax_last_dim(logits)
    item = getattr(argmax, "item", None)
    return int(cast(Any, item() if callable(item) else argmax))


def _index_last_dim_float(values: Any, index: int) -> float:
    try:
        value = values[index]
    except Exception:
        value = gather_last_dim(values, index)
    item = getattr(value, "item", None)
    return float(cast(Any, item() if callable(item) else value))


def _as_flat_list(value: Any) -> list[Any]:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if _is_sequence(value):
        if value and _is_sequence(value[0]):
            flattened: list[Any] = []
            for item in value:
                flattened.extend(_as_flat_list(item))
            return flattened
        return value
    return [value]


def _as_int_list(value: Any) -> list[int]:
    return [int(item) for item in _as_flat_list(value)]


def _decode_token_for_dataframe(tokenizer: Any, token_id: int) -> str:
    decode = getattr(tokenizer, "decode", None)
    if callable(decode):
        return str(decode([token_id]))
    to_string = getattr(tokenizer, "to_string", None)
    if callable(to_string):
        decoded = to_string([token_id])
        if isinstance(decoded, list):
            return str(decoded[0])
        return str(decoded)
    return str(token_id)


def _log_softmax_vector(values: Sequence[float]) -> list[float]:
    max_value = max(values) if values else 0.0
    log_total = math.log(sum(math.exp(value - max_value) for value in values))
    return [float(value - max_value - log_total) for value in values]


def _sample_logits_torch(
    final_logits: Any,
    *,
    top_k: int | None,
    top_p: float | None,
    temperature: float,
    freq_penalty: float,
    repetition_penalty: float,
    tokens: Any | None,
) -> Any | None:
    try:
        import torch
    except Exception:
        return None

    if not isinstance(final_logits, torch.Tensor):
        return None

    logits = final_logits.to(torch.float32).clone()
    single_row = logits.ndim == 1
    logits_for_sampling = logits.unsqueeze(0) if single_row else logits
    token_history = None
    if tokens is not None and (repetition_penalty != 1.0 or freq_penalty > 0):
        token_history = _coerce_token_history_torch(
            tokens,
            batch_size=int(logits_for_sampling.shape[0]),
            device=logits_for_sampling.device,
        )

    if repetition_penalty != 1.0 and token_history is not None:
        assert (
            len(token_history.shape) == 2
        ), "Repetition penalty do not support input in the form of embeddings"
        logits_for_sampling = _apply_repetition_penalty_torch(
            logits_for_sampling,
            token_history,
            repetition_penalty,
        )

    if temperature == 0.0:
        sample = logits_for_sampling.argmax(dim=-1)
        return sample.squeeze(0) if single_row else sample

    logits_for_sampling = logits_for_sampling / temperature
    if freq_penalty > 0:
        assert (
            token_history is not None
        ), "Must provide input_tokens if applying a frequency penalty"
        assert (
            len(token_history.shape) == 2
        ), "Frequency penalty do not support input in the form of embeddings"
        for batch_index in range(logits_for_sampling.shape[0]):
            token_counts = torch.bincount(
                _valid_token_ids_torch(
                    token_history[batch_index],
                    int(logits_for_sampling.shape[-1]),
                ),
                minlength=logits_for_sampling.shape[-1],
            )[: logits_for_sampling.shape[-1]]
            logits_for_sampling[batch_index] = logits_for_sampling[batch_index] - (
                freq_penalty * token_counts
            )

    if top_k is not None:
        top_k = min(int(top_k), int(logits_for_sampling.shape[-1]))
        top_logits, _top_idx = logits_for_sampling.topk(top_k, dim=-1)
        indices_to_remove = logits_for_sampling < top_logits[..., -1].unsqueeze(-1)
        logits_for_sampling = logits_for_sampling.masked_fill(indices_to_remove, -float("inf"))
    elif top_p is not None:
        sorted_logits, sorted_indices = torch.sort(logits_for_sampling, descending=True)
        cumulative_probs = sorted_logits.softmax(dim=-1).cumsum(dim=-1)
        sorted_indices_to_remove = cumulative_probs > top_p
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0
        indices_to_remove = sorted_indices_to_remove.scatter(
            -1,
            sorted_indices,
            sorted_indices_to_remove,
        )
        logits_for_sampling = logits_for_sampling.masked_fill(indices_to_remove, -float("inf"))

    categorical = cast(Any, torch.distributions.categorical.Categorical)
    sample = categorical(
        logits=logits_for_sampling.to(torch.float32)
    ).sample()
    return sample.squeeze(0) if single_row else sample


def _coerce_token_history_torch(tokens: Any, *, batch_size: int, device: Any) -> Any:
    import torch

    token_history = tokens if isinstance(tokens, torch.Tensor) else torch.as_tensor(tokens)
    if token_history.ndim == 0:
        token_history = token_history.reshape(1, 1)
    elif token_history.ndim == 1:
        token_history = token_history.unsqueeze(0)
    if len(token_history.shape) == 2:
        if int(token_history.shape[0]) == batch_size:
            pass
        elif int(token_history.shape[0]) == 1:
            token_history = token_history.expand(batch_size, -1)
        else:
            raise ValueError("tokens batch dimension must match final_logits batch dimension.")
        return token_history.to(device=device, dtype=torch.long)
    return token_history.to(device=device, dtype=torch.long)


def _apply_repetition_penalty_torch(logits: Any, tokens: Any, penalty: float) -> Any:
    import torch

    logits = logits.clone()
    for batch_idx in range(logits.shape[0]):
        unique_tokens = _valid_token_ids_torch(
            tokens[batch_idx].reshape(-1).unique(),
            int(logits.shape[-1]),
        )
        if unique_tokens.numel() == 0:
            continue
        score = logits[batch_idx, unique_tokens]
        logits[batch_idx, unique_tokens] = torch.where(score > 0, score / penalty, score * penalty)
    return logits


def _valid_token_ids_torch(tokens: Any, vocab_size: int) -> Any:
    import torch

    token_ids = tokens.reshape(-1).to(dtype=torch.long)
    return token_ids[(token_ids >= 0) & (token_ids < vocab_size)]


def _sample_logits_python(
    final_logits: Any,
    *,
    top_k: int | None,
    top_p: float | None,
    temperature: float,
    freq_penalty: float,
    repetition_penalty: float,
    tokens: Any | None,
) -> list[int]:
    logits_batch = _ensure_batch_logits(final_logits)
    token_batch = None if tokens is None else _ensure_batch_tokens(tokens, len(logits_batch))
    samples: list[int] = []
    for batch_index, logits_row in enumerate(logits_batch):
        row = [float(value) for value in logits_row]
        row_tokens = None if token_batch is None else token_batch[batch_index]
        if repetition_penalty != 1.0 and row_tokens is not None:
            row = _apply_repetition_penalty_to_row(row, row_tokens, repetition_penalty)
        if temperature == 0.0:
            samples.append(_argmax_list(row))
            continue
        row = [value / temperature for value in row]
        if freq_penalty > 0:
            assert (
                row_tokens is not None
            ), "Must provide input_tokens if applying a frequency penalty"
            counts = _token_counts(row_tokens, len(row))
            row = [value - freq_penalty * counts[index] for index, value in enumerate(row)]
        if top_k is not None:
            row = _filter_logits_top_k(row, top_k)
        elif top_p is not None:
            row = _filter_logits_top_p(row, top_p)
        samples.append(_sample_from_logits_row(row))
    return samples


def _ensure_batch_logits(final_logits: Any) -> list[list[float]]:
    value = (
        final_logits.tolist() if callable(getattr(final_logits, "tolist", None)) else final_logits
    )
    if not _is_sequence(value):
        raise ValueError("final_logits must be a vector or a batch of vectors.")
    if value and _is_sequence(value[0]):
        return [[float(item) for item in row] for row in value]
    return [[float(item) for item in value]]


def _ensure_batch_tokens(tokens: Any, batch_size: int) -> list[list[int]]:
    value = tokens.tolist() if callable(getattr(tokens, "tolist", None)) else tokens
    if not _is_sequence(value):
        value = [int(value)]
    sequence_value = cast(Sequence[Any], value)
    if sequence_value and _is_sequence(sequence_value[0]):
        rows = [[int(item) for item in cast(Sequence[Any], row)] for row in sequence_value]
    else:
        rows = [[int(item) for item in sequence_value]]
    if len(rows) == batch_size:
        return rows
    if len(rows) == 1:
        return rows * batch_size
    raise ValueError("tokens batch dimension must match final_logits batch dimension.")


def _apply_repetition_penalty_to_row(
    row: list[float], tokens: Sequence[int], penalty: float
) -> list[float]:
    output = row.copy()
    for token_id in set(int(token) for token in tokens if 0 <= int(token) < len(output)):
        score = output[token_id]
        output[token_id] = score / penalty if score > 0 else score * penalty
    return output


def _token_counts(tokens: Sequence[int], vocab_size: int) -> list[int]:
    counts = [0] * vocab_size
    for token in tokens:
        token_id = int(token)
        if 0 <= token_id < vocab_size:
            counts[token_id] += 1
    return counts


def _filter_logits_top_k(row: list[float], top_k: int) -> list[float]:
    threshold = sorted(row, reverse=True)[min(top_k, len(row)) - 1]
    return [value if value >= threshold else -float("inf") for value in row]


def _filter_logits_top_p(row: list[float], top_p: float) -> list[float]:
    probabilities = [math.exp(value) for value in _log_softmax_vector(row)]
    ordered_indices = sorted(range(len(row)), key=lambda index: row[index], reverse=True)
    removed = [False] * len(row)
    cumulative = 0.0
    previous_removed = False
    for position, index in enumerate(ordered_indices):
        current_removed = cumulative + probabilities[index] > top_p
        removed[index] = False if position == 0 else previous_removed
        cumulative += probabilities[index]
        previous_removed = current_removed
    return [-float("inf") if removed[index] else value for index, value in enumerate(row)]


def _sample_from_logits_row(row: list[float]) -> int:
    max_value = max(row)
    weights = [
        0.0 if math.isinf(value) and value < 0 else math.exp(value - max_value) for value in row
    ]
    total = sum(weights)
    if total <= 0:
        return _argmax_list(row)
    threshold = random.random() * total
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if cumulative >= threshold:
            return index
    return len(row) - 1


def _argmax_list(row: Sequence[float]) -> int:
    return max(range(len(row)), key=lambda index: row[index])


def _decode_single_token_if_possible(model: Any, token_id: int) -> str | int:
    to_single_str_token = getattr(model, "to_single_str_token", None)
    if callable(to_single_str_token):
        try:
            return str(to_single_str_token(int(token_id)))
        except Exception:
            pass
    to_string = getattr(model, "to_string", None)
    if callable(to_string):
        try:
            decoded = to_string([int(token_id)])
            if isinstance(decoded, list):
                return str(decoded[0])
            return str(decoded)
        except Exception:
            pass
    return int(token_id)


def _print_test_prompt_result(result: dict[str, Any]) -> None:
    predicted = result["predicted_token"]
    correct = result["correct_token"]
    print(f"Prompt: {result['prompt']!r}")
    print(f"Predicted token: {predicted!r} (id {result['predicted_token_id']})")
    print(f"Correct token: {correct!r} (id {result['correct_token_id']})")
    if "logit_diff" in result:
        print(f"Logit diff: {result['logit_diff']:.4f}")
    print("Top tokens:")
    for item in result["top_tokens"]:
        print(f"  {item['token']!r} ({item['token_id']}): {item['logit']:.4f}")


def _print_transformerlens_test_prompt_result(result: dict[str, Any]) -> None:
    answers = list(result.get("answers", []))
    print(f"Prompt: {result['prompt']!r}")
    print(f"Tokenized prompt: {result.get('prompt_str_tokens', [])!r}")
    if len(answers) == 1:
        print(f"Answer: {answers[0]!r}")
    else:
        print(f"Answers: {answers!r}")
    for item in result.get("token_results", []):
        tokens = item.get("answer_tokens", [])
        ranks = item.get("answer_ranks", [])
        if len(tokens) == 1:
            rank = ranks[0] if ranks else "unknown"
            print(f"Answer token at position {item['position']}: " f"{tokens[0]!r}, rank {rank}")
        else:
            rank_details = ", ".join(
                f"{token!r}: rank {rank}" for token, rank in zip(tokens, ranks, strict=False)
            )
            print(f"Answer tokens at position {item['position']}: {rank_details}")
        top_tokens_by_answer = item.get("top_tokens_by_answer")
        if top_tokens_by_answer:
            for answer_token, top_tokens in zip(tokens, top_tokens_by_answer, strict=False):
                print(f"Top tokens for {answer_token!r}:")
                for top_token in top_tokens:
                    print(
                        f"  {top_token['token']!r} "
                        f"({top_token['token_id']}): {top_token['logit']:.4f}"
                    )
        elif item.get("top_tokens"):
            print("Top tokens:")
            for top_token in item["top_tokens"]:
                print(
                    f"  {top_token['token']!r} "
                    f"({top_token['token_id']}): {top_token['logit']:.4f}"
                )


def gather_last_dim(values: Any, indices: Any) -> Any:
    """Gather values at final-dimension indices."""
    try:
        import torch

        if hasattr(values, "shape"):
            if not hasattr(indices, "shape"):
                indices = torch.as_tensor(indices, dtype=torch.long, device=values.device)
            else:
                indices = indices.to(device=values.device, dtype=torch.long)
            if indices.ndim == 0:
                return values[..., int(indices.item())]
            return values.gather(-1, indices.unsqueeze(-1)).squeeze(-1)
    except Exception:
        pass
    try:
        if hasattr(values, "shape") and hasattr(indices, "shape"):
            if len(getattr(indices, "shape", ())) == 0:
                item = getattr(indices, "item", None)
                index = int(cast(Any, item() if callable(item) else indices))
                return values[..., index]
            return values.gather(-1, indices.unsqueeze(-1)).squeeze(-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(values, "shape") or hasattr(indices, "shape"):
            values_array = np.asarray(values)
            index_array = np.asarray(indices)
            if index_array.ndim == 0:
                return values_array[..., int(index_array.item())]
            return np.take_along_axis(
                values_array, np.expand_dims(index_array, -1), axis=-1
            ).squeeze(-1)
    except Exception:
        pass
    if _is_sequence(indices):
        if indices and _is_sequence(indices[0]):
            return [
                gather_last_dim(value_row, index_row)
                for value_row, index_row in zip(values, indices, strict=True)
            ]
        return [row[index] for row, index in zip(values, indices, strict=True)]
    if _is_sequence(values) and values and _is_sequence(values[0]):
        return [gather_last_dim(value_row, indices) for value_row in values]
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
    if _is_sequence(values) and _is_sequence(mask):
        return [
            mask_values(value_item, mask_item)
            for value_item, mask_item in zip(values, mask, strict=False)
        ]
    return values if bool(mask) else None


def zero_mask_values(values: Any, mask: Any) -> Any:
    """Set values to zero wherever mask is false."""
    try:
        import torch

        if hasattr(values, "shape"):
            if not hasattr(mask, "shape"):
                mask = torch.as_tensor(mask, dtype=torch.bool, device=values.device)
            else:
                mask = mask.to(device=values.device, dtype=torch.bool)
            return torch.where(mask, values, torch.zeros_like(values))
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(values, "shape") or hasattr(mask, "shape"):
            return np.where(np.asarray(mask).astype(bool), np.asarray(values), 0)
    except Exception:
        pass
    if _is_sequence(values) and _is_sequence(mask):
        return [
            zero_mask_values(value_item, mask_item)
            for value_item, mask_item in zip(values, mask, strict=False)
        ]
    return values if bool(mask) else 0.0


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
    if _is_sequence(values):
        if not values:
            return []
        if values and _is_sequence(values[0]):
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
    if _is_sequence(left) and _is_sequence(right):
        return [
            equal_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=False)
        ]
    return 1.0 if left == right else 0.0


def flatten(value: Any) -> list[Any]:
    """Flatten nested lists or tensor-like values."""
    if hasattr(value, "shape"):
        try:
            return list(value.reshape(-1))
        except Exception:
            pass
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if _is_sequence(value):
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
    if _is_sequence(value):
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
    if _is_sequence(left) and _is_sequence(right):
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
            return [
                _dot_nested(l_item, r_item) for l_item, r_item in zip(left, right, strict=False)
            ]
        return [_dot_nested(l_item, right) for l_item in left]
    return left


def _head_results_from_nested(
    z: Any,
    W_O: Any,
    *,
    has_layer_axis: bool | None = None,
) -> Any:
    if _shape_of(z) == ():
        return z
    shape = _shape_of(z)
    w_o_shape = _shape_of(W_O)
    if _has_aligned_layer_axis(z, W_O, has_layer_axis=has_layer_axis):
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
                "Pass W_O[layer] or call compute_head_results_from_z(..., "
                "has_layer_axis=True) for layer-stacked z."
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


def _normalize_w_o_for_z(
    z: Any,
    W_O: Any,
    *,
    has_layer_axis: bool | None = None,
) -> Any:
    if _has_aligned_layer_axis(z, W_O, has_layer_axis=has_layer_axis):
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
                "Pass W_O[layer] or call compute_head_results_from_z(..., "
                "has_layer_axis=True) for layer-stacked z."
            )
    return W_O


def _has_aligned_layer_axis(
    z: Any,
    W_O: Any,
    *,
    has_layer_axis: bool | None = None,
) -> bool:
    z_shape = _shape_of(z)
    w_o_shape = _shape_of(W_O)
    if len(w_o_shape) != 4 or z_shape[-2:] != w_o_shape[1:3]:
        return False
    if has_layer_axis is not None:
        return bool(has_layer_axis) and len(z_shape) >= 3 and z_shape[0] == w_o_shape[0]
    # [batch, pos, head, d_head] is more common than a batchless layer stack,
    # so only infer a layer axis automatically when both batch and pos axes are
    # present after the layer axis. Shorter shapes can opt in with
    # has_layer_axis=True.
    return len(z_shape) >= 5 and z_shape[0] == w_o_shape[0]


def matmul_last_dim(left: Any, right: Any) -> Any:
    """Multiply `left[..., d] @ right[d, out]` for nested-list values."""
    if _shape_of(left) == ():
        return left
    if _is_vector(left):
        return _matvec(left, right)
    return [matmul_last_dim(item, right) for item in left]


def _add_unembed_bias(logits: Any, unembed_bias: Any | None) -> Any:
    if unembed_bias is None:
        return logits
    try:
        import torch

        if isinstance(logits, torch.Tensor):
            if not isinstance(unembed_bias, torch.Tensor):
                unembed_bias = torch.as_tensor(
                    unembed_bias,
                    dtype=logits.dtype,
                    device=logits.device,
                )
            else:
                unembed_bias = unembed_bias.to(dtype=logits.dtype, device=logits.device)
            return logits + unembed_bias
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(logits, np.ndarray):
            return logits + np.asarray(unembed_bias, dtype=logits.dtype)
    except Exception:
        pass
    if _is_sequence(logits):
        if _is_vector(logits):
            if _is_sequence(unembed_bias):
                return [
                    float(logit) + float(bias)
                    for logit, bias in zip(logits, unembed_bias, strict=True)
                ]
            return [float(logit) + float(unembed_bias) for logit in logits]
        return [_add_unembed_bias(item, unembed_bias) for item in logits]
    try:
        return logits + unembed_bias
    except TypeError:
        pass
    try:
        return float(logits) + float(unembed_bias)
    except (TypeError, ValueError):
        return logits


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
    return _is_sequence(value) and (not value or not _is_sequence(value[0]))


def _shape_of(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if _is_sequence(value):
        if not value:
            return (0,)
        return (len(value), *_shape_of(value[0]))
    return ()


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


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
    if _is_sequence(left) and _is_sequence(right):
        return [
            and_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=False)
        ]
    return bool(left) and bool(right)
