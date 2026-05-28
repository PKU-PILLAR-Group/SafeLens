# Factored Matrix

`FactoredMatrix` represents a matrix as `A @ B`. This mirrors the common
TransformerLens pattern for composing projection matrices without immediately
materializing every dense product.

Supported operations:

- Dense product through `.AB` and reverse product through `.BA`.
- Transpose through `.T`.
- Matrix/vector multiplication with `@`; left matrix multiplication preserves a
  factored result, right matrix multiplication preserves a factored result, and
  vector multiplication returns a vector.
- Scalar multiplication with `*`.
- Factored composition with another `FactoredMatrix`.
- Frobenius norm with `.norm()`; leading dimensions are preserved.
- SVD-backed `.U`, `.S`, `.V`, `.Vh`, `.collapse_l()`, `.collapse_r()`,
  `.make_even()`, and `.eigenvalues` when NumPy compatible data is available.
- `.svd()` returns `(U, S, V)`, with `.Vh` retained as a TransformerLens
  compatibility alias for `.V`.
- Torch tensor inputs keep tensor outputs for SVD, collapse, even-factor, norm,
  and composition-score workflows.
- Rectangular matrix eigenvalues are computed from `BA`, matching
  TransformerLens' non-zero spectrum convention.
- `unsqueeze(dim)` and `squeeze(dim)` for leading-dimension shape management.
- TransformerLens-style indexing over leading, row, and column dimensions while
  preserving a factored matrix result.
- Singleton leading dimensions are broadcast on construction, matching
  TransformerLens' layer/head batching behavior.
- `composition_scores(left, right)` for QK/OV-style circuit composition
  analysis, with optional pairwise leading-dimension broadcasting.
- Lightweight list and tensor-like fallbacks for projects that do not install
  TransformerLens.

Example:

```python
from SafeLens.core.factored_matrix import FactoredMatrix, composition_scores

W_QK = FactoredMatrix([[1, 2], [3, 4]], [[2, 0], [0, 2]])

assert W_QK.AB == [[2.0, 4.0], [6.0, 8.0]]
assert W_QK @ [1, 1] == [6.0, 14.0]
assert 0 <= composition_scores(W_QK, W_QK) <= 1
```

::: SafeLens.core.factored_matrix
