"""Low-rank factored matrix utilities inspired by TransformerLens."""

from __future__ import annotations

import math
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

FULL_SLICE = slice(None)
_BACKEND_MATMUL_NOT_AVAILABLE = object()


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


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
        if self.ldim != self.rdim:
            raise ValueError(
                f"Can only take BA if ldim == rdim, got dense shape {self.shape}."
            )
        return matmul(self.B, self.A)

    @property
    def T(self) -> FactoredMatrix:
        """Return the transposed factored matrix."""
        return FactoredMatrix(transpose(self.B), transpose(self.A))

    @property
    def ndim(self) -> int:
        """Return the rank of the dense product."""
        return len(self.shape)

    @property
    def ldim(self) -> int:
        """Return the row dimension of the dense product."""
        return self.shape[-2]

    @property
    def rdim(self) -> int:
        """Return the column dimension of the dense product."""
        return self.shape[-1]

    @property
    def mdim(self) -> int:
        """Return the hidden dimension shared by the two factors."""
        return shape_of(self.B)[-2]

    @property
    def has_leading_dims(self) -> bool:
        """Return whether either factor has leading batch-like dimensions."""
        return len(shape_of(self.A)) > 2 or len(shape_of(self.B)) > 2

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the dense matrix shape."""
        left_shape = shape_of(self.A)
        right_shape = shape_of(self.B)
        leading_shape = broadcast_leading_shape(left_shape[:-2], right_shape[:-2])
        return leading_shape + (left_shape[-2], right_shape[-1])

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
        warnings.warn(
            "FactoredMatrix.Vh returns V (right singular vectors), not Vh. "
            "Use .V for the canonical name.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.svd()[2]

    @property
    def V(self) -> Any:
        """Return right singular vectors from `svd()`."""
        return self.svd()[2]

    @property
    def eigenvalues(self) -> Any:
        """Return eigenvalues of `BA`, matching the non-zero spectrum of `AB`."""
        input_matrix = self.BA
        try:
            import torch

            if isinstance(input_matrix, torch.Tensor):
                if input_matrix.dtype in {torch.bfloat16, torch.float16}:
                    input_matrix = input_matrix.to(torch.float32)
                return torch.linalg.eig(input_matrix).eigenvalues
        except ImportError:
            pass
        try:
            import numpy as np

            return np.linalg.eigvals(np.asarray(input_matrix)).tolist()
        except Exception as exc:
            raise RuntimeError(
                "FactoredMatrix.eigenvalues requires numpy-compatible data."
            ) from exc

    def __matmul__(self, other: Any) -> Any:
        """Multiply by another matrix/vector/factored matrix."""
        if isinstance(other, FactoredMatrix):
            return (self @ other.A) @ other.B
        if _is_vector_like(other):
            return matmul(self.AB, other)
        right_shape = shape_of(other)
        if len(right_shape) >= 2 and right_shape[-2] == self.shape[-1]:
            if self.rdim > self.mdim:
                return FactoredMatrix(self.A, matmul(self.B, other))
            return FactoredMatrix(self.AB, other)
        return matmul(self.AB, other)

    def __rmatmul__(self, other: Any) -> Any:
        """Left multiply the dense product."""
        if isinstance(other, FactoredMatrix):
            return other @ self
        if _is_vector_like(other):
            return matmul(other, self.AB)
        left_shape = shape_of(other)
        if len(left_shape) >= 2 and left_shape[-1] == self.shape[-2]:
            if self.ldim > self.mdim:
                return FactoredMatrix(matmul(other, self.A), self.B)
            return FactoredMatrix(other, self.AB)
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

            if isinstance(self.A, torch.Tensor) or isinstance(self.B, torch.Tensor):
                a = self.A if isinstance(self.A, torch.Tensor) else torch.as_tensor(
                    self.A,
                    dtype=getattr(self.B, "dtype", None),
                    device=getattr(self.B, "device", None),
                )
                b = self.B if isinstance(self.B, torch.Tensor) else torch.as_tensor(
                    self.B,
                    dtype=a.dtype,
                    device=a.device,
                )
                if not torch.is_floating_point(a) or a.dtype in {torch.bfloat16, torch.float16}:
                    a = a.to(torch.float32)
                if not torch.is_floating_point(b) or b.dtype in {torch.bfloat16, torch.float16}:
                    b = b.to(torch.float32)
                u_a, s_a, vh_a = torch.linalg.svd(a, full_matrices=False)
                u_b, s_b, vh_b = torch.linalg.svd(b, full_matrices=False)
                v_a = vh_a.transpose(-1, -2)
                v_b = vh_b.transpose(-1, -2)
                middle = s_a[..., :, None] * (v_a.transpose(-1, -2) @ u_b) * s_b[..., None, :]
                u_m, s_m, vh_m = torch.linalg.svd(middle, full_matrices=False)
                v_m = vh_m.transpose(-1, -2)
                return u_a @ u_m, s_m, v_b @ v_m
        except Exception:
            pass
        try:
            import numpy as np

            a = _promote_numpy_svd_array(np.asarray(self.A), np)
            b = _promote_numpy_svd_array(np.asarray(self.B), np)
            u_a, s_a, vh_a = np.linalg.svd(a, full_matrices=False)
            u_b, s_b, vh_b = np.linalg.svd(b, full_matrices=False)
            v_a = np.swapaxes(vh_a, -1, -2)
            v_b = np.swapaxes(vh_b, -1, -2)
            middle = s_a[..., :, None] * (np.swapaxes(v_a, -1, -2) @ u_b) * s_b[..., None, :]
            u_m, s_m, vh_m = np.linalg.svd(middle, full_matrices=False)
            v_m = np.swapaxes(vh_m, -1, -2)
            return (u_a @ u_m).tolist(), s_m.tolist(), (v_b @ v_m).tolist()
        except Exception as exc:
            raise RuntimeError("FactoredMatrix.svd requires numpy-compatible data.") from exc

    def norm(self) -> float:
        """Return the Frobenius norm without materializing the dense product."""
        return factored_frobenius_norm(self.A, self.B)

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
        left_index = expand_ellipsis((Ellipsis, slice(None, k), FULL_SLICE), len(shape_of(self.A)))
        right_index = expand_ellipsis((Ellipsis, FULL_SLICE, slice(None, k)), len(shape_of(self.B)))
        return matrix_corner(matmul(index_value(self.A, left_index), index_value(self.B, right_index)), k)

    def unsqueeze(self, dim: int | None = None, *, k: int | None = None) -> FactoredMatrix:
        """Add a leading dimension to both factors."""
        if dim is None:
            if k is None:
                raise TypeError("unsqueeze() missing required argument: 'dim' or 'k'")
            dim = k
        elif k is not None:
            raise TypeError("Pass only one of `dim` or `k`.")
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
    backend_result = _try_backend_matmul(left, right)
    if backend_result is not _BACKEND_MATMUL_NOT_AVAILABLE:
        return backend_result
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
    if len(left_shape) == 1 and len(right_shape) == 1:
        return sum(float(a) * float(b) for a, b in zip(left, right, strict=True))
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


def _try_backend_matmul(left: Any, right: Any) -> Any:
    """Try preserving torch/numpy backends when the other operand is a sequence."""
    torch_result = _try_torch_matmul(left, right)
    if torch_result is not _BACKEND_MATMUL_NOT_AVAILABLE:
        return torch_result
    return _try_numpy_matmul(left, right)


def _try_torch_matmul(left: Any, right: Any) -> Any:
    try:
        import torch
    except ImportError:
        return _BACKEND_MATMUL_NOT_AVAILABLE
    if not (isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor)):
        return _BACKEND_MATMUL_NOT_AVAILABLE
    try:
        if isinstance(left, torch.Tensor):
            left_tensor = left
        else:
            left_tensor = torch.as_tensor(
                left,
                dtype=getattr(right, "dtype", None),
                device=getattr(right, "device", None),
            )
        if isinstance(right, torch.Tensor):
            right_tensor = right
        else:
            right_tensor = torch.as_tensor(right, dtype=left_tensor.dtype, device=left_tensor.device)
        return left_tensor @ right_tensor
    except Exception:
        return _BACKEND_MATMUL_NOT_AVAILABLE


def _try_numpy_matmul(left: Any, right: Any) -> Any:
    if not (_is_numpy_backed(left) or _is_numpy_backed(right)):
        return _BACKEND_MATMUL_NOT_AVAILABLE
    try:
        import numpy as np

        left_array = left if _is_numpy_backed(left) else np.asarray(left, dtype=getattr(right, "dtype", None))
        right_array = right if _is_numpy_backed(right) else np.asarray(right, dtype=getattr(left_array, "dtype", None))
        return left_array @ right_array
    except Exception:
        return _BACKEND_MATMUL_NOT_AVAILABLE


def _is_numpy_backed(value: Any) -> bool:
    return type(value).__module__.split(".")[0] == "numpy"


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
    if _is_sequence(value):
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
    backend_result = _try_backend_elementwise(left, right, op="multiply")
    if backend_result is not _BACKEND_MATMUL_NOT_AVAILABLE:
        return backend_result
    left_shape = shape_of(left)
    right_shape = shape_of(right)
    if left_shape or right_shape:
        left_b, right_b = broadcast_pair(left, right)
        if _is_sequence(left_b) and _is_sequence(right_b):
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
    backend_result = _try_backend_elementwise(left, right, op="divide")
    if backend_result is not _BACKEND_MATMUL_NOT_AVAILABLE:
        return backend_result
    left_shape = shape_of(left)
    right_shape = shape_of(right)
    if left_shape or right_shape:
        left_b, right_b = broadcast_pair(left, right)
        if _is_sequence(left_b) and _is_sequence(right_b):
            return [
                divide_values(left_item, right_item)
                for left_item, right_item in zip(left_b, right_b, strict=True)
            ]
    return float(left) / float(right)


def _try_backend_elementwise(left: Any, right: Any, *, op: str) -> Any:
    torch_result = _try_torch_elementwise(left, right, op=op)
    if torch_result is not _BACKEND_MATMUL_NOT_AVAILABLE:
        return torch_result
    return _try_numpy_elementwise(left, right, op=op)


def _try_torch_elementwise(left: Any, right: Any, *, op: str) -> Any:
    try:
        import torch
    except ImportError:
        return _BACKEND_MATMUL_NOT_AVAILABLE
    if not (isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor)):
        return _BACKEND_MATMUL_NOT_AVAILABLE
    try:
        if isinstance(left, torch.Tensor):
            left_tensor = left
        else:
            left_tensor = torch.as_tensor(
                left,
                dtype=getattr(right, "dtype", None),
                device=getattr(right, "device", None),
            )
        if isinstance(right, torch.Tensor):
            right_tensor = right
        else:
            right_tensor = torch.as_tensor(right, dtype=left_tensor.dtype, device=left_tensor.device)
        if op == "multiply":
            return left_tensor * right_tensor
        if op == "divide":
            return left_tensor / right_tensor
    except Exception:
        return _BACKEND_MATMUL_NOT_AVAILABLE
    return _BACKEND_MATMUL_NOT_AVAILABLE


def _try_numpy_elementwise(left: Any, right: Any, *, op: str) -> Any:
    if not (_is_numpy_backed(left) or _is_numpy_backed(right)):
        return _BACKEND_MATMUL_NOT_AVAILABLE
    try:
        import numpy as np

        left_array = left if _is_numpy_backed(left) else np.asarray(left, dtype=getattr(right, "dtype", None))
        right_array = right if _is_numpy_backed(right) else np.asarray(right, dtype=getattr(left_array, "dtype", None))
        if op == "multiply":
            return left_array * right_array
        if op == "divide":
            return left_array / right_array
    except Exception:
        return _BACKEND_MATMUL_NOT_AVAILABLE
    return _BACKEND_MATMUL_NOT_AVAILABLE


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


def factored_frobenius_norm(left: Any, right: Any) -> Any:
    """Return `||left @ right||_F` from small Gram products."""
    try:
        import torch

        if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
            if not isinstance(left, torch.Tensor):
                left = torch.as_tensor(left, dtype=right.dtype, device=right.device)
            if not isinstance(right, torch.Tensor):
                right = torch.as_tensor(right, dtype=left.dtype, device=left.device)
            left_gram = transpose(left) @ left
            right_gram = right @ transpose(right)
            return torch.sqrt((left_gram * transpose(right_gram)).sum(dim=(-2, -1)))
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") or hasattr(right, "shape"):
            left_array = np.asarray(left)
            right_array = np.asarray(right)
            left_gram = np.swapaxes(left_array, -1, -2) @ left_array
            right_gram = right_array @ np.swapaxes(right_array, -1, -2)
            return np.sqrt((left_gram * np.swapaxes(right_gram, -1, -2)).sum(axis=(-2, -1))).tolist()
    except Exception:
        pass
    left_shape = shape_of(left)
    right_shape = shape_of(right)
    if len(left_shape) > 2 or len(right_shape) > 2:
        leading_shape = broadcast_leading_shape(left_shape[:-2], right_shape[:-2])
        left_b = broadcast_to_shape(left, leading_shape + left_shape[-2:])
        right_b = broadcast_to_shape(right, leading_shape + right_shape[-2:])
        return [
            factored_frobenius_norm(left_item, right_item)
            for left_item, right_item in zip(left_b, right_b, strict=True)
        ]
    left_gram = matmul(transpose(left), left)
    right_gram = matmul(right, transpose(right))
    return math.sqrt(
        sum(
            float(left_gram[row][col]) * float(right_gram[col][row])
            for row in range(len(left_gram))
            for col in range(len(left_gram[row]))
        )
    )


def transpose(matrix: Any) -> Any:
    """Transpose the final two dimensions of a matrix-like value."""
    shape = shape_of(matrix)
    if len(shape) >= 2 and not _is_sequence(matrix):
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
    if len(shape) > 2 and _is_sequence(matrix):
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


def _promote_numpy_svd_array(array: Any, np: Any) -> Any:
    dtype = getattr(array, "dtype", None)
    if dtype is not None and dtype == np.float16:
        return array.astype(np.float32)
    return array


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
    if _is_sequence(value):
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
    if not _is_sequence(value):
        return [[value]]
    if not value:
        return []
    if _is_sequence(value[0]):
        return [list(row) for row in value]
    return [list(value)]


def shape_of(value: Any) -> tuple[int, ...]:
    """Return best-effort shape for a tensor-like value."""
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if _is_sequence(value):
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
        if not _is_sequence(value):
            return value
        return [
            _broadcast_nested_axis(item, source_shape[1:], target_shape[1:])
            for item in value
        ]
    if source_dim == 1:
        item = value[0] if _is_sequence(value) else value
        broadcast_item = _broadcast_nested_axis(item, source_shape[1:], target_shape[1:])
        return [clone_nested(broadcast_item) for _ in range(target_dim)]
    raise ValueError(f"Cannot broadcast shape {source_shape} to {target_shape}.")


def clone_nested(value: Any) -> Any:
    if _is_sequence(value):
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
    if _is_sequence(value):
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
    if _is_sequence(value):
        if value and _is_sequence(value[0]):
            return list(value[0])
        return list(value)
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
