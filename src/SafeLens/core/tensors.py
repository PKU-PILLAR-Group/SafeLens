"""TransformerLens-style tensor and slice utilities without a TL dependency."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from typing import Any, TypeAlias

SliceInput: TypeAlias = Any

_FULL_SLICE = slice(None)


def _numpy_module() -> Any | None:
    try:
        import numpy as np
    except ModuleNotFoundError:
        return None
    return np


def _require_numpy() -> Any:
    np = _numpy_module()
    if np is None:
        raise ImportError("numpy is required for this tensor utility.")
    return np


def _torch_module() -> Any | None:
    try:
        import torch
    except ModuleNotFoundError:
        return None
    return torch


def _is_torch_tensor(value: Any) -> bool:
    torch = _torch_module()
    if torch is None:
        return False
    return isinstance(value, torch.Tensor | torch.nn.parameter.Parameter)


def _is_numpy_array(value: Any) -> bool:
    np = _numpy_module()
    return np is not None and isinstance(value, np.ndarray)


def to_numpy(tensor: Any) -> Any:
    """Convert tensors, arrays, Python sequences, and scalars to a numpy array."""

    np = _require_numpy()
    if isinstance(tensor, np.ndarray):
        return tensor
    if isinstance(tensor, list | tuple | range):
        return np.array(tensor)
    if _is_torch_tensor(tensor):
        return tensor.detach().cpu().numpy()
    if isinstance(tensor, int | float | bool | str):
        return np.array(tensor)
    raise ValueError(f"Input to to_numpy has invalid type: {type(tensor)}")


class Slice:
    """TransformerLens-style slice object for slicing a chosen tensor dimension.

    Unlike raw Python indexing, ``Slice.unwrap(1)`` turns an integer into an
    array-style index so the sliced dimension is preserved.
    """

    slice: Any
    mode: str

    def __init__(self, input_slice: SliceInput = None) -> None:
        if isinstance(input_slice, Slice):
            self.slice = input_slice.slice
            self.mode = input_slice.mode
        elif isinstance(input_slice, tuple):
            self.slice = slice(*input_slice)
            self.mode = "slice"
        elif isinstance(input_slice, int):
            self.slice = input_slice
            self.mode = "int"
        elif isinstance(input_slice, slice):
            self.slice = input_slice
            self.mode = "slice"
        elif self._is_array_input(input_slice):
            self.slice = self._array_index(input_slice)
            self.mode = "array"
        elif input_slice is None:
            self.slice = _FULL_SLICE
            self.mode = "identity"
        else:
            raise ValueError(f"Invalid input_slice {input_slice!r}")

    @staticmethod
    def _is_array_input(value: Any) -> bool:
        return isinstance(value, list | range) or _is_numpy_array(value) or _is_torch_tensor(value)

    @staticmethod
    def _array_index(value: Any) -> Any:
        if _numpy_module() is not None:
            return to_numpy(value)
        if isinstance(value, range):
            return list(value)
        return value

    def apply(self, tensor: Any, dim: int = 0) -> Any:
        """Apply this slice to ``tensor`` along ``dim``."""

        shape = _shape_of(tensor)
        rank = len(shape)
        if rank == 0:
            return tensor
        normalized_dim = _normalize_dim(dim, rank)
        slices = [_FULL_SLICE] * rank
        slices[normalized_dim] = self.slice
        index = tuple(slices)
        try:
            return tensor[index]
        except (TypeError, IndexError, KeyError):
            return _get_nested(tensor, index)

    def indices(self, max_ctx: int | None = None) -> Any:
        """Return the selected indices as a numpy array."""

        np = _require_numpy()
        if self.mode == "int":
            return np.array([self.slice], dtype=np.int64)
        if max_ctx is None:
            raise ValueError("max_ctx must be specified if slice is not an integer")
        return np.arange(max_ctx, dtype=np.int64)[_numpy_index(self.slice)]

    def __repr__(self) -> str:
        return f"Slice: {self.slice} Mode: {self.mode} "

    @classmethod
    def unwrap(cls, slice_input: Slice | SliceInput) -> Slice:
        """Convert a Slice-like input to ``Slice`` while preserving integer dims."""

        if isinstance(slice_input, Slice):
            return slice_input
        if isinstance(slice_input, int):
            slice_input = [slice_input]
        return cls(slice_input)


def get_corner(tensor: Any, n: int = 3) -> Any:
    """Return the top-left ``n`` entries along every tensor dimension."""

    shape = _shape_of(tensor)
    if not shape:
        return tensor
    index = tuple(slice(n) for _ in shape)
    try:
        return tensor[index]
    except (TypeError, IndexError, KeyError):
        return _get_nested(tensor, index)


def remove_batch_dim(tensor: Any) -> Any:
    """Remove the leading dimension when it has size 1; otherwise return unchanged."""

    shape = _shape_of(tensor)
    if shape and shape[0] == 1:
        return _slice_dim(tensor, 0, dim=0)
    return tensor


def transpose(tensor: Any) -> Any:
    """Swap the final two dimensions of a tensor-like value."""

    tensor_transpose = getattr(tensor, "transpose", None)
    if callable(tensor_transpose):
        try:
            return tensor_transpose(-1, -2)
        except TypeError:
            pass

    swapaxes = getattr(tensor, "swapaxes", None)
    if callable(swapaxes):
        return swapaxes(-1, -2)

    shape = _shape_of(tensor)
    if len(shape) < 2:
        return tensor
    return _transpose_nested(tensor, len(shape))


def is_square(x: Any) -> bool:
    """Return whether ``x`` is a rank-2 square matrix."""

    shape = _shape_of(x)
    return len(shape) == 2 and shape[0] == shape[1]


def is_lower_triangular(x: Any) -> bool:
    """Return whether ``x`` is a lower-triangular square matrix."""

    if not is_square(x):
        return False
    tril = getattr(x, "tril", None)
    equal = getattr(x, "equal", None)
    if callable(tril) and callable(equal):
        return bool(equal(tril()))

    np = _numpy_module()
    if np is not None and isinstance(x, np.ndarray):
        return bool(np.array_equal(x, np.tril(x)))

    matrix = _to_nested_list(x)
    size = len(matrix)
    return all(matrix[row][col] == 0 for row in range(size) for col in range(row + 1, size))


def check_structure(t1: Any, t2: Any, *, verbose: bool = False) -> None:
    """Validate that two square tensors have matching row/column order structure."""

    assert is_square(t1)
    assert _shape_of(t1) == _shape_of(t2)

    left = _to_nested_list(t1)
    right = _to_nested_list(t2)
    n_rows, n_cols = _shape_of(t1)
    row_mismatch: list[int] = []
    col_mismatch: list[int] = []

    if verbose:
        print("Checking rows")
    for row_i in range(n_rows - 1):
        left_result = [left[row_i][col] >= left[row_i + 1][col] for col in range(n_cols)]
        right_result = [right[row_i][col] >= right[row_i + 1][col] for col in range(n_cols)]
        if left_result != right_result:
            row_mismatch.append(row_i)
            if verbose:
                print(f"\trows {row_i}:{row_i + 1}")
                print(f"\tt1: {left_result}")
                print(f"\tt2: {right_result}")

    if verbose:
        print("Checking columns")
    for col_i in range(n_cols - 1):
        left_result = [left[row][col_i] >= left[row][col_i + 1] for row in range(n_rows)]
        right_result = [right[row][col_i] >= right[row][col_i + 1] for row in range(n_rows)]
        if left_result != right_result:
            col_mismatch.append(col_i)
            if verbose:
                print(f"\tcolumns {col_i}:{col_i + 1}")
                print(f"\tt1: {left_result}")
                print(f"\tt2: {right_result}")

    if not row_mismatch and not col_mismatch:
        print("PASSED")
    elif row_mismatch:
        print(f"row mismatch: {row_mismatch}")
    else:
        print(f"column mismatch: {col_mismatch}")


def get_offset_position_ids(past_kv_pos_offset: int, attention_mask: Any) -> Any:
    """Return non-padding position ids shifted by ``past_kv_pos_offset``."""

    cumsum = getattr(attention_mask, "cumsum", None)
    masked_fill = getattr(attention_mask, "masked_fill", None)
    if callable(cumsum) and callable(masked_fill):
        shifted_position_ids = attention_mask.cumsum(dim=1) - 1
        position_ids = shifted_position_ids.masked_fill(shifted_position_ids < 0, 0)
        return position_ids[:, past_kv_pos_offset:]

    np = _numpy_module()
    if np is not None and isinstance(attention_mask, np.ndarray):
        shifted_position_ids = np.cumsum(attention_mask, axis=1) - 1
        position_ids = np.where(shifted_position_ids < 0, 0, shifted_position_ids)
        return position_ids[:, past_kv_pos_offset:]

    rows = _to_nested_list(attention_mask)
    position_ids = []
    for row in rows:
        running = 0
        output_row = []
        for item in row:
            running += int(item)
            output_row.append(max(running - 1, 0))
        position_ids.append(output_row[past_kv_pos_offset:])
    return position_ids


def get_cumsum_along_dim(tensor: Any, dim: int, reverse: bool = False) -> Any:
    """Return the cumulative sum of ``tensor`` along ``dim``."""

    torch_flip = getattr(tensor, "flip", None)
    torch_cumsum = getattr(tensor, "cumsum", None)
    if callable(torch_flip) and callable(torch_cumsum):
        if reverse:
            tensor = tensor.flip(dims=(dim,))
        result = tensor.cumsum(dim=dim)
        if reverse:
            result = result.flip(dims=(dim,))
        return result

    np = _numpy_module()
    if np is not None and isinstance(tensor, np.ndarray):
        result = np.flip(tensor, axis=dim) if reverse else tensor
        result = np.cumsum(result, axis=dim)
        return np.flip(result, axis=dim) if reverse else result

    shape = _shape_of(tensor)
    if not shape:
        return tensor
    normalized_dim = _normalize_dim(dim, len(shape))
    return _cumsum_nested(tensor, normalized_dim, reverse=reverse)


def repeat_along_head_dimension(tensor: Any, n_heads: int, clone_tensor: bool = True) -> Any:
    """Repeat ``[..., d_model]`` values along a new head dimension."""

    shape = _shape_of(tensor)
    if not shape:
        raise ValueError(
            "repeat_along_head_dimension expects a tensor with at least one dimension."
        )

    unsqueeze = getattr(tensor, "unsqueeze", None)
    if callable(unsqueeze):
        repeated = tensor.unsqueeze(-2).expand(*shape[:-1], n_heads, shape[-1])
        return repeated.clone() if clone_tensor else repeated

    np = _numpy_module()
    if np is not None and isinstance(tensor, np.ndarray):
        repeated = np.repeat(np.expand_dims(tensor, axis=-2), n_heads, axis=-2)
        return repeated.copy() if clone_tensor else repeated

    return _repeat_nested_along_new_penultimate_dim(tensor, len(shape), n_heads, clone_tensor)


def filter_dict_by_prefix(dictionary: dict[Any, Any], prefix: str) -> dict[Any, Any]:
    """Keep keys starting with ``prefix`` and strip that prefix plus separator."""

    search_prefix = prefix if prefix.endswith(".") else prefix + "."
    return {
        key[len(search_prefix) :]: value
        for key, value in dictionary.items()
        if isinstance(key, str) and key.startswith(search_prefix)
    }


def _shape_of(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        if not value:
            return (0,)
        return (len(value), *_shape_of(value[0]))
    return ()


def _normalize_dim(dim: int, rank: int) -> int:
    normalized = dim + rank if dim < 0 else dim
    if normalized < 0 or normalized >= rank:
        raise IndexError(f"Dimension {dim} is out of range for rank {rank}.")
    return normalized


def _numpy_index(index: Any) -> Any:
    np = _require_numpy()
    if isinstance(index, np.ndarray):
        return index
    if _is_torch_tensor(index):
        return index.detach().cpu().numpy()
    return index


def _slice_dim(value: Any, index: Any, *, dim: int) -> Any:
    return Slice(index).apply(value, dim=dim)


def _get_nested(value: Any, index: tuple[Any, ...]) -> Any:
    if not index:
        return value
    head = index[0]
    tail = index[1:]
    if isinstance(head, slice):
        if head == _FULL_SLICE:
            return [_get_nested(item, tail) for item in value]
        return [_get_nested(item, tail) for item in value[head]]
    indices = _explicit_indices(head, len(value) if isinstance(value, Sequence) else None)
    if indices is not None:
        return [_get_nested(value[position], tail) for position in indices]
    return _get_nested(value[head], tail)


def _explicit_indices(index: Any, size: int | None = None) -> list[int] | None:
    if isinstance(index, range):
        return [item % size if size is not None else item for item in index]
    tolist = getattr(index, "tolist", None)
    if callable(tolist):
        index = tolist()
    if isinstance(index, Sequence) and not isinstance(index, str | bytes):
        if index and all(isinstance(item, bool) for item in index):
            if size is not None and len(index) != size:
                raise IndexError(
                    f"Boolean index has length {len(index)} but dimension has length {size}."
                )
            return [
                position
                for position, include in enumerate(index)
                if include and (size is None or position < size)
            ]
        return [int(item) % size if size is not None else int(item) for item in index]
    return None


def _transpose_nested(value: Any, rank: int) -> Any:
    if rank == 2:
        rows = _to_nested_list(value)
        if not rows:
            return []
        return [[rows[row][col] for row in range(len(rows))] for col in range(len(rows[0]))]
    return [_transpose_nested(item, rank - 1) for item in value]


def _to_nested_list(value: Any) -> list[Any]:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [deepcopy(item) for item in value]
    return [value]


def _cumsum_nested(value: Any, dim: int, *, reverse: bool) -> Any:
    if dim == 0:
        sequence = list(value)
        if reverse:
            sequence = list(reversed(sequence))
        running: Any | None = None
        output = []
        for item in sequence:
            running = deepcopy(item) if running is None else _add_nested(running, item)
            output.append(deepcopy(running))
        if reverse:
            output.reverse()
        return output
    return [_cumsum_nested(item, dim - 1, reverse=reverse) for item in value]


def _add_nested(left: Any, right: Any) -> Any:
    if isinstance(left, Sequence) and not isinstance(left, str | bytes):
        return [
            _add_nested(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=False)
        ]
    return left + right


def _repeat_nested_along_new_penultimate_dim(
    value: Any,
    rank: int,
    n_heads: int,
    clone_tensor: bool,
) -> Any:
    if rank == 1:
        return [deepcopy(value) if clone_tensor else value for _ in range(n_heads)]
    return [
        _repeat_nested_along_new_penultimate_dim(item, rank - 1, n_heads, clone_tensor)
        for item in value
    ]
