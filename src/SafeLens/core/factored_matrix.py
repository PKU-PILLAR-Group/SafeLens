"""Low-rank factored matrix utilities inspired by TransformerLens."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FactoredMatrix:
    """Represent a matrix as a product `A @ B`."""

    A: Any
    B: Any

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
        """Return right singular vectors from `svd()`."""
        return self.svd()[2]

    @property
    def eigenvalues(self) -> Any:
        """Return eigenvalues of the dense product."""
        try:
            import numpy as np

            return np.linalg.eigvals(np.asarray(self.AB)).tolist()
        except Exception as exc:
            raise RuntimeError(
                "FactoredMatrix.eigenvalues requires numpy-compatible data."
            ) from exc

    def __matmul__(self, other: Any) -> Any:
        """Multiply by another matrix/vector/factored matrix."""
        if isinstance(other, FactoredMatrix):
            return FactoredMatrix(self.A, matmul(matmul(self.B, other.A), other.B))
        return matmul(self.AB, other)

    def __rmatmul__(self, other: Any) -> Any:
        """Left multiply the dense product."""
        return matmul(other, self.AB)

    def __getitem__(self, index: Any) -> FactoredMatrix:
        """Index leading dimensions by indexing both factors."""
        return FactoredMatrix(self.A[index], self.B[index])

    def to_dense_right(self, right: Any) -> Any:
        """Return dense `(A @ B) @ right`."""
        return matmul(self.AB, right)

    def svd(self) -> tuple[Any, Any, Any]:
        """Return SVD of the dense product."""
        try:
            import numpy as np

            u, s, vh = np.linalg.svd(np.asarray(self.AB), full_matrices=False)
            return u.tolist(), s.tolist(), vh.tolist()
        except Exception as exc:
            raise RuntimeError("FactoredMatrix.svd requires numpy-compatible data.") from exc

    def norm(self) -> float:
        """Return the Frobenius norm."""
        return math.sqrt(sum(float(value) ** 2 for row in as_2d(self.AB) for value in row))

    def collapse_l(self) -> Any:
        """Collapse the left side of the factorization."""
        return self.AB

    def collapse_r(self) -> Any:
        """Collapse the right side of the factorization."""
        return self.AB

    def make_even(self) -> FactoredMatrix:
        """Return an equivalent more balanced factorization using SVD."""
        u, s, vh = self.svd()
        sqrt_s = [math.sqrt(float(value)) for value in s]
        left = [[float(value) * sqrt_s[col] for col, value in enumerate(row)] for row in u]
        right = [
            [sqrt_s[row_index] * float(value) for value in row] for row_index, row in enumerate(vh)
        ]
        return FactoredMatrix(left, right)

    def get_corner(self, k: int = 3) -> Any:
        """Return the top-left dense corner."""
        dense = as_2d(self.AB)
        return [row[:k] for row in dense[:k]]


def matmul(left: Any, right: Any) -> Any:
    """Matrix multiply tensor-like or nested-list values."""
    try:
        return left @ right
    except Exception:
        pass
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


def transpose(matrix: Any) -> Any:
    """Transpose a 2D matrix-like value."""
    transpose_fn = getattr(matrix, "T", None)
    if transpose_fn is not None and not isinstance(matrix, list):
        return transpose_fn
    rows = as_2d(matrix)
    return [list(col) for col in zip(*rows, strict=True)]


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
