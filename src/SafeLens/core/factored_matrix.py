"""Low-rank factored matrix utilities inspired by TransformerLens."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

FULL_SLICE = slice(None)


@dataclass(frozen=True)
class FactoredMatrix:
    """Represent a matrix as a product `A @ B`."""

    A: Any
    B: Any

    def __post_init__(self) -> None:
        left_shape = shape_of(self.A)
        right_shape = shape_of(self.B)
        if len(left_shape) < 2 or len(right_shape) < 2:
            raise ValueError(f"FactoredMatrix factors must be at least rank-2, got {left_shape} and {right_shape}.")
        if left_shape[-1] != right_shape[-2]:
            raise ValueError(f"FactoredMatrix inner dimensions must match, got {left_shape} and {right_shape}.")
        leading_shape = broadcast_leading_shape(left_shape[:-2], right_shape[:-2])
        object.__setattr__(self, "A", broadcast_to_shape(self.A, leading_shape + left_shape[-2:]))
        object.__setattr__(self, "B", broadcast_to_shape(self.B, leading_shape + right_shape[-2:]))

    @property
    def pair(self) -> tuple[Any, Any]:
        """Return the matrix factors."""
        return self.A, self.B

    @property
    def AB(self) -> Any:
        """Return the dense product `A @ B`."""
        return matmul(self.A, self.B)

    @property
    def BA(self) -> Any:
        """Return the reverse dense product `B @ A`."""
        return matmul(self.B, self.A)

    @property
    def T(self) -> FactoredMatrix:
        """Return the transposed factored matrix."""
        return FactoredMatrix(transpose(self.B), transpose(self.A))

    @property
    def ndim(self) -> int:
        """Return the rank of the dense product."""
        return len(shape_of(self.AB))

    @property
    def ldim(self) -> int:
        """Return the row dimension of the dense product."""
        return self.shape[-2]

    @property
    def rdim(self) -> int:
        """Return the column dimension of the dense product."""
        return self.shape[-1]

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the dense matrix shape."""
        return shape_of(self.AB)

    @property
    def U(self) -> Any:
        """Return left singular vectors from `svd()`."""
        return self.svd()[0]

    @property
    def S(self) -> Any:
        """Return singular values from `svd()`."""
        return self.svd()[1]

    @property
    def Vh(self) -> Any:
        """Deprecated alias for right singular vectors from `svd()`."""
        return self.svd()[2]

    @property
    def V(self) -> Any:
        """Return right singular vectors from `svd()`."""
        return self.svd()[2]

    @property
    def eigenvalues(self) -> Any:
        """Return eigenvalues of `BA`, matching the non-zero spectrum of `AB`."""
        try:
            import numpy as np

            return np.linalg.eigvals(np.asarray(self.BA)).tolist()
        except Exception as exc:
            raise RuntimeError(
                "FactoredMatrix.eigenvalues requires numpy-compatible data."
            ) from exc

    def __matmul__(self, other: Any) -> Any:
        """Multiply by another matrix/vector/factored matrix."""
        if isinstance(other, FactoredMatrix):
            left_leading = shape_of(self.A)[:-2]
            right_leading = shape_of(other.A)[:-2]
            leading_shape = broadcast_leading_shape(left_leading, right_leading)
            left_a = broadcast_to_shape(self.A, leading_shape + shape_of(self.A)[-2:])
            left_b = broadcast_to_shape(self.B, leading_shape + shape_of(self.B)[-2:])
            right_a = broadcast_to_shape(other.A, leading_shape + shape_of(other.A)[-2:])
            right_b = broadcast_to_shape(other.B, leading_shape + shape_of(other.B)[-2:])
            return FactoredMatrix(left_a, matmul(matmul(left_b, right_a), right_b))
        if _is_vector_like(other):
            return matmul(self.AB, other)
        right_shape = shape_of(other)
        if len(right_shape) >= 2 and right_shape[-2] == self.shape[-1]:
            return FactoredMatrix(self.A, matmul(self.B, other))
        return matmul(self.AB, other)

    def __rmatmul__(self, other: Any) -> Any:
        """Left multiply the dense product."""
        if isinstance(other, FactoredMatrix):
            return other @ self
        if _is_vector_like(other):
            return matmul(other, self.AB)
        left_shape = shape_of(other)
        if len(left_shape) >= 2 and left_shape[-1] == self.shape[-2]:
            return FactoredMatrix(matmul(other, self.A), self.B)
        return matmul(other, self.AB)

    def __mul__(self, scalar: Any) -> FactoredMatrix:
        """Scale the factored matrix by multiplying the left factor."""
        if not _is_scalar_like(scalar):
            raise TypeError("FactoredMatrix scalar multiplication expects a scalar.")
        return FactoredMatrix(scale_values(self.A, scalar), self.B)

    def __rmul__(self, scalar: Any) -> FactoredMatrix:
        """Right scalar multiplication."""
        return self * scalar

    def __getitem__(self, index: Any) -> FactoredMatrix:
        """Index leading, row, and column dimensions while preserving factored rank."""
        normalized = expand_ellipsis(normalize_index(index), len(self.shape))
        indexed_dims = len([item for item in normalized if item is not None])
        leading_dims = max(0, len(self.shape) - 2)
        if indexed_dims <= leading_dims:
            return FactoredMatrix(index_value(self.A, normalized), index_value(self.B, normalized))
        if indexed_dims == leading_dims + 1:
            row_index = convert_int_to_slice(normalized, -1)
            return FactoredMatrix(index_value(self.A, row_index), index_value(self.B, row_index[:-1]))
        if indexed_dims == leading_dims + 2:
            row_col_index = convert_int_to_slice(convert_int_to_slice(normalized, -1), -2)
            return FactoredMatrix(
                index_value(self.A, row_col_index[:-1]),
                index_value(self.B, row_col_index[:-2] + (FULL_SLICE, row_col_index[-1])),
            )
        raise ValueError(f"{normalized!r} is too long an index for a FactoredMatrix with shape {self.shape}.")

    def __repr__(self) -> str:
        """Return a TransformerLens-style summary."""
        return f"FactoredMatrix: Shape({self.shape}), Hidden Dim({shape_of(self.B)[-2]})"

    def to_dense_right(self, right: Any) -> Any:
        """Return dense `(A @ B) @ right`."""
        return matmul(self.AB, right)

    def svd(self) -> tuple[Any, Any, Any]:
        """Return `(U, S, V)` with right singular vectors in `V`, matching TransformerLens."""
        try:
            import torch

            if isinstance(self.AB, torch.Tensor):
                u, s, vh = torch.linalg.svd(self.AB, full_matrices=False)
                return u, s, vh.transpose(-1, -2)
        except Exception:
            pass
        try:
            import numpy as np

            u, s, vh = np.linalg.svd(np.asarray(self.AB), full_matrices=False)
            return u.tolist(), s.tolist(), np.swapaxes(vh, -1, -2).tolist()
        except Exception as exc:
            raise RuntimeError("FactoredMatrix.svd requires numpy-compatible data.") from exc

    def norm(self) -> float:
        """Return the Frobenius norm."""
        return frobenius_norm(self.AB)

    def collapse_l(self) -> Any:
        """Collapse the left orthogonal factor using the SVD."""
        return scale_rows(transpose(self.V), self.S)

    def collapse_r(self) -> Any:
        """Collapse the right orthogonal factor using the SVD."""
        return scale_columns(self.U, self.S)

    def make_even(self) -> FactoredMatrix:
        """Return an equivalent more balanced factorization using SVD."""
        left, right = _make_even_factors(*self.svd())
        return FactoredMatrix(left, right)

    def get_corner(self, k: int = 3) -> Any:
        """Return the top-left dense corner."""
        return matrix_corner(self.AB, k)

    def unsqueeze(self, dim: int) -> FactoredMatrix:
        """Add a leading dimension to both factors."""
        return FactoredMatrix(unsqueeze_dim(self.A, dim), unsqueeze_dim(self.B, dim))

    def squeeze(self, dim: int | None = None) -> FactoredMatrix:
        """Remove singleton dimensions from both factors."""
        return FactoredMatrix(squeeze_dim(self.A, dim), squeeze_dim(self.B, dim))


def matmul(left: Any, right: Any) -> Any:
    """Matrix multiply tensor-like or nested-list values."""
    try:
        return left @ right
    except Exception:
        pass
    left_shape = shape_of(left)
    right_shape = shape_of(right)
    if len(left_shape) > 2 and len(right_shape) > 2:
        leading_shape = broadcast_leading_shape(left_shape[:-2], right_shape[:-2])
        left_b = broadcast_to_shape(left, leading_shape + left_shape[-2:])
        right_b = broadcast_to_shape(right, leading_shape + right_shape[-2:])
        return [
            matmul(left_item, right_item)
            for left_item, right_item in zip(left_b, right_b, strict=True)
        ]
    if len(left_shape) > 2 and len(right_shape) == 1:
        return [matmul(item, right) for item in left]
    if len(left_shape) == 1 and len(right_shape) > 2:
        return [matmul(left, item) for item in right]
    if len(left_shape) > 2 and len(right_shape) == 2:
        return [matmul(item, right) for item in left]
    if len(left_shape) == 2 and len(right_shape) > 2:
        left_b = broadcast_to_shape(left, right_shape[:-2] + left_shape)
        return [
            matmul(left_item, right_item)
            for left_item, right_item in zip(left_b, right, strict=True)
        ]
    if len(left_shape) == 1 and len(right_shape) == 2:
        right_t = transpose(right)
        return [
            sum(float(a) * float(b) for a, b in zip(left, col, strict=True))
            for col in right_t
        ]
    left_rows = as_2d(left)
    right_rows = as_2d(right)
    if len(right_rows) == 1 and len(left_rows[0]) != 1:
        vector = right_rows[0]
        return [
            sum(float(a) * float(b) for a, b in zip(row, vector, strict=True)) for row in left_rows
        ]
    right_t = transpose(right_rows)
    return [
        [sum(float(a) * float(b) for a, b in zip(row, col, strict=True)) for col in right_t]
        for row in left_rows
    ]


def composition_scores(
    left: FactoredMatrix,
    right: FactoredMatrix,
    broadcast_dims: bool = True,
) -> Any:
    """Return TransformerLens-style composition scores for two factored matrices."""
    if broadcast_dims:
        left_leading = left.ndim - 2
        right_leading = right.ndim - 2
        for dim in range(left_leading):
            right = right.unsqueeze(dim)
        for dim in range(right_leading):
            left = left.unsqueeze(dim + left_leading)
    if left.rdim != right.ldim:
        raise ValueError(
            "Composition scores require left.rdim == right.ldim, "
            f"got left shape {left.shape} and right shape {right.shape}."
        )

    collapsed_left = left.collapse_l()
    collapsed_right = right.collapse_r()
    composed = matmul(collapsed_left, collapsed_right)
    denominator = multiply_values(frobenius_norm(collapsed_left), frobenius_norm(collapsed_right))
    return divide_values(frobenius_norm(composed), denominator)


def scale_values(value: Any, scalar: Any) -> Any:
    """Scale tensor-like or nested-list values by a scalar."""
    if isinstance(value, list):
        return [scale_values(item, scalar) for item in value]
    try:
        return value * scalar
    except TypeError:
        pass
    return float(value) * float(scalar)


def multiply_values(left: Any, right: Any) -> Any:
    """Multiply tensor-like or nested values elementwise."""
    try:
        return left * right
    except Exception:
        pass
    left_shape = shape_of(left)
    right_shape = shape_of(right)
    if left_shape or right_shape:
        left_b, right_b = broadcast_pair(left, right)
        if isinstance(left_b, list) and isinstance(right_b, list):
            return [
                multiply_values(left_item, right_item)
                for left_item, right_item in zip(left_b, right_b, strict=True)
            ]
    return float(left) * float(right)


def divide_values(left: Any, right: Any) -> Any:
    """Divide tensor-like or nested values elementwise."""
    try:
        return left / right
    except Exception:
        pass
    left_shape = shape_of(left)
    right_shape = shape_of(right)
    if left_shape or right_shape:
        left_b, right_b = broadcast_pair(left, right)
        if isinstance(left_b, list) and isinstance(right_b, list):
            return [
                divide_values(left_item, right_item)
                for left_item, right_item in zip(left_b, right_b, strict=True)
            ]
    return float(left) / float(right)


def broadcast_pair(left: Any, right: Any) -> tuple[Any, Any]:
    """Broadcast two tensor-like or nested values to a shared shape."""
    target_shape = broadcast_leading_shape(shape_of(left), shape_of(right))
    return broadcast_to_shape(left, target_shape), broadcast_to_shape(right, target_shape)


def scale_rows(matrix: Any, row_scales: Any) -> Any:
    """Multiply each row of a matrix-like value by the matching scale."""
    try:
        return row_scales[..., :, None] * matrix
    except Exception:
        pass
    matrix_shape = shape_of(matrix)
    scale_shape = shape_of(row_scales)
    if len(matrix_shape) > 2 or len(scale_shape) > 1:
        return [
            scale_rows(matrix_item, scale_item)
            for matrix_item, scale_item in zip(matrix, row_scales, strict=True)
        ]
    rows = as_2d(matrix)
    scales = _as_1d(row_scales)
    return [
        [float(value) * float(scales[row_index]) for value in row]
        for row_index, row in enumerate(rows)
    ]


def scale_columns(matrix: Any, column_scales: Any) -> Any:
    """Multiply each column of a matrix-like value by the matching scale."""
    try:
        return matrix * column_scales[..., None, :]
    except Exception:
        pass
    matrix_shape = shape_of(matrix)
    scale_shape = shape_of(column_scales)
    if len(matrix_shape) > 2 or len(scale_shape) > 1:
        return [
            scale_columns(matrix_item, scale_item)
            for matrix_item, scale_item in zip(matrix, column_scales, strict=True)
        ]
    rows = as_2d(matrix)
    scales = _as_1d(column_scales)
    return [
        [float(value) * float(scales[col_index]) for col_index, value in enumerate(row)]
        for row in rows
    ]


def frobenius_norm(value: Any) -> Any:
    """Return Frobenius norm per leading dimension."""
    try:
        import torch

        if isinstance(value, torch.Tensor):
            return torch.linalg.matrix_norm(value, ord="fro", dim=(-2, -1))
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            array = np.asarray(value)
            return np.linalg.norm(array, axis=(-2, -1)).tolist()
    except Exception:
        pass
    shape = shape_of(value)
    if len(shape) <= 2:
        return math.sqrt(sum(float(item) ** 2 for item in flatten_values(value)))
    return [frobenius_norm(item) for item in value]


def transpose(matrix: Any) -> Any:
    """Transpose the final two dimensions of a matrix-like value."""
    shape = shape_of(matrix)
    if len(shape) >= 2 and not isinstance(matrix, list):
        matrix_transpose = getattr(matrix, "mT", None)
        if matrix_transpose is not None:
            return matrix_transpose
        swapaxes = getattr(matrix, "swapaxes", None)
        if callable(swapaxes):
            try:
                return swapaxes(-1, -2)
            except Exception:
                pass
        transpose_fn = getattr(matrix, "transpose", None)
        if callable(transpose_fn):
            try:
                return transpose_fn(-1, -2)
            except Exception:
                pass
        transpose_attr = getattr(matrix, "T", None)
        if transpose_attr is not None and len(shape) == 2:
            return transpose_attr
    if len(shape) > 2 and isinstance(matrix, list):
        return [transpose(item) for item in matrix]
    rows = as_2d(matrix)
    return [list(col) for col in zip(*rows, strict=True)]


def matrix_corner(matrix: Any, k: int = 3) -> Any:
    """Return a top-left corner over the final two matrix dimensions."""
    shape = shape_of(matrix)
    if len(shape) < 2:
        return matrix
    try:
        return matrix[..., :k, :k]
    except Exception:
        pass
    if len(shape) > 2:
        return [matrix_corner(item, k) for item in matrix]
    rows = as_2d(matrix)
    return [row[:k] for row in rows[:k]]


def _make_even_factors(u: Any, s: Any, v: Any) -> tuple[Any, Any]:
    try:
        import torch

        if isinstance(u, torch.Tensor) or isinstance(s, torch.Tensor) or isinstance(v, torch.Tensor):
            if not isinstance(u, torch.Tensor):
                u = torch.as_tensor(
                    u,
                    dtype=getattr(s, "dtype", getattr(v, "dtype", None)),
                    device=getattr(s, "device", getattr(v, "device", None)),
                )
            if not isinstance(s, torch.Tensor):
                s = torch.as_tensor(s, dtype=u.dtype, device=u.device)
            if not isinstance(v, torch.Tensor):
                v = torch.as_tensor(v, dtype=u.dtype, device=u.device)
            sqrt_s = torch.sqrt(s)
            return u * sqrt_s[..., None, :], sqrt_s[..., :, None] * transpose(v)
    except Exception:
        pass
    u_shape = shape_of(u)
    s_shape = shape_of(s)
    if len(u_shape) > 2 or len(s_shape) > 1:
        left_items: list[Any] = []
        right_items: list[Any] = []
        for u_item, s_item, v_item in zip(u, s, v, strict=True):
            left_item, right_item = _make_even_factors(u_item, s_item, v_item)
            left_items.append(left_item)
            right_items.append(right_item)
        return left_items, right_items
    sqrt_s = [math.sqrt(float(value)) for value in s]
    left = [[float(value) * sqrt_s[col] for col, value in enumerate(row)] for row in u]
    right = [
        [sqrt_s[row_index] * float(value) for value in row]
        for row_index, row in enumerate(transpose(v))
    ]
    return left, right


def unsqueeze_dim(value: Any, dim: int) -> Any:
    """Unsqueeze tensor-like or nested-list values."""
    unsqueeze = getattr(value, "unsqueeze", None)
    if callable(unsqueeze):
        return unsqueeze(dim)
    shape = shape_of(value)
    rank = len(shape)
    if dim < 0:
        dim = rank + dim + 1
    if dim <= 0:
        return [value]
    if isinstance(value, list):
        return [unsqueeze_dim(item, dim - 1) for item in value]
    return [value]


def squeeze_dim(value: Any, dim: int | None = None) -> Any:
    """Squeeze tensor-like or nested-list values."""
    squeeze = getattr(value, "squeeze", None)
    if callable(squeeze):
        return squeeze() if dim is None else squeeze(dim)
    shape = shape_of(value)
    if dim is None:
        result = value
        for axis in reversed([index for index, size in enumerate(shape) if size == 1]):
            result = squeeze_dim(result, axis)
        return result
    if dim < 0:
        dim = len(shape) + dim
    if not shape or shape[dim] != 1:
        raise ValueError(f"Cannot squeeze dimension {dim} with shape {shape}.")
    return squeeze_nested_dim(value, dim)


def squeeze_nested_dim(value: Any, dim: int) -> Any:
    if dim == 0:
        return value[0]
    return [squeeze_nested_dim(item, dim - 1) for item in value]


def as_2d(value: Any) -> list[list[Any]]:
    """Convert a tensor-like value to a 2D Python list."""
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if not isinstance(value, list):
        return [[value]]
    if not value:
        return []
    if isinstance(value[0], list):
        return value
    return [value]


def shape_of(value: Any) -> tuple[int, ...]:
    """Return best-effort shape for a tensor-like value."""
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, list):
        if not value:
            return (0,)
        return (len(value), *shape_of(value[0]))
    return ()


def broadcast_leading_shape(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    result: list[int] = []
    max_len = max(len(left), len(right))
    padded_left = (1,) * (max_len - len(left)) + left
    padded_right = (1,) * (max_len - len(right)) + right
    for left_dim, right_dim in zip(padded_left, padded_right, strict=True):
        if left_dim == 1:
            result.append(right_dim)
        elif right_dim == 1 or right_dim == left_dim:
            result.append(left_dim)
        else:
            raise ValueError(f"Cannot broadcast leading dimensions {left} and {right}.")
    return tuple(result)


def broadcast_to_shape(value: Any, target_shape: tuple[int, ...]) -> Any:
    shape = shape_of(value)
    if shape == target_shape:
        return value
    module = type(value).__module__.split(".")[0]
    if module == "numpy":
        try:
            import numpy as np

            return np.broadcast_to(value, target_shape)
        except Exception:
            pass
    broadcast_to = getattr(value, "broadcast_to", None)
    if callable(broadcast_to):
        try:
            return broadcast_to(target_shape)
        except Exception:
            pass
    expand = getattr(value, "expand", None)
    if callable(expand):
        try:
            return expand(target_shape)
        except Exception:
            try:
                return expand(*target_shape)
            except Exception:
                pass
    return _broadcast_nested(value, shape, target_shape)


def _broadcast_nested(value: Any, source_shape: tuple[int, ...], target_shape: tuple[int, ...]) -> Any:
    if source_shape == target_shape:
        return value
    if len(source_shape) < len(target_shape):
        for _ in range(len(target_shape) - len(source_shape)):
            value = [value]
        source_shape = (1,) * (len(target_shape) - len(source_shape)) + source_shape
    if len(source_shape) != len(target_shape):
        raise ValueError(f"Cannot broadcast shape {source_shape} to {target_shape}.")
    return _broadcast_nested_axis(value, source_shape, target_shape)


def _broadcast_nested_axis(value: Any, source_shape: tuple[int, ...], target_shape: tuple[int, ...]) -> Any:
    if not target_shape:
        return value
    source_dim = source_shape[0]
    target_dim = target_shape[0]
    if source_dim == target_dim:
        if not isinstance(value, list):
            return value
        return [
            _broadcast_nested_axis(item, source_shape[1:], target_shape[1:])
            for item in value
        ]
    if source_dim == 1:
        item = value[0] if isinstance(value, list) else value
        broadcast_item = _broadcast_nested_axis(item, source_shape[1:], target_shape[1:])
        return [clone_nested(broadcast_item) for _ in range(target_dim)]
    raise ValueError(f"Cannot broadcast shape {source_shape} to {target_shape}.")


def clone_nested(value: Any) -> Any:
    if isinstance(value, list):
        return [clone_nested(item) for item in value]
    clone = getattr(value, "copy", None)
    if callable(clone):
        try:
            return clone()
        except Exception:
            pass
    return value


def flatten_values(value: Any) -> list[Any]:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if isinstance(value, list):
        result: list[Any] = []
        for item in value:
            result.extend(flatten_values(item))
        return result
    return [value]


def normalize_index(index: Any) -> tuple[Any, ...]:
    if isinstance(index, tuple):
        return index
    return (index,)


def expand_ellipsis(index: tuple[Any, ...], rank: int) -> tuple[Any, ...]:
    if Ellipsis not in index:
        return index
    if index.count(Ellipsis) > 1:
        raise IndexError("an index can only have a single ellipsis")
    consumed_dims = len([item for item in index if item is not None and item is not Ellipsis])
    fill = max(0, rank - consumed_dims)
    expanded: list[Any] = []
    for item in index:
        if item is Ellipsis:
            expanded.extend([FULL_SLICE] * fill)
        else:
            expanded.append(item)
    return tuple(expanded)


def convert_int_to_slice(index: tuple[Any, ...], axis: int) -> tuple[Any, ...]:
    values = list(index)
    if axis < 0:
        axis = len(values) + axis
    if 0 <= axis < len(values) and isinstance(values[axis], int):
        item = values[axis]
        values[axis] = slice(item, None if item == -1 else item + 1)
    return tuple(values)


def index_value(value: Any, index: tuple[Any, ...]) -> Any:
    if not index:
        return value
    try:
        return value[index]
    except Exception:
        pass
    return index_nested(value, index)


def index_nested(value: Any, index: tuple[Any, ...]) -> Any:
    if not index:
        return value
    head = index[0]
    tail = index[1:]
    if head is None:
        return [index_nested(value, tail)]
    if isinstance(head, slice):
        return [index_nested(item, tail) for item in value[head]]
    return index_nested(value[head], tail)


def _as_1d(value: Any) -> list[Any]:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if isinstance(value, list):
        if value and isinstance(value[0], list):
            return value[0]
        return value
    return [value]


def _is_scalar_like(value: Any) -> bool:
    shape = shape_of(value)
    if shape == ():
        return True
    if shape in {(1,), (1, 1)}:
        return True
    numel = getattr(value, "numel", None)
    if callable(numel):
        try:
            return int(numel()) == 1
        except Exception:
            return False
    return False


def _is_vector_like(value: Any) -> bool:
    shape = shape_of(value)
    return len(shape) == 1
