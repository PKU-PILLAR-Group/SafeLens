# Factored Matrix

`FactoredMatrix` represents a matrix as `A @ B`. This mirrors the common
TransformerLens pattern for composing projection matrices without immediately
materializing every dense product.

Supported operations:

- Dense product through `.AB` and reverse product through `.BA`.
- Transpose through `.T`.
- Matrix/vector multiplication with `@`.
- Factored composition with another `FactoredMatrix`.
- Frobenius norm with `.norm()`.
- SVD-backed `.U`, `.S`, `.Vh`, `.make_even()`, and `.eigenvalues` when NumPy
  compatible data is available.
- Lightweight list and tensor-like fallbacks for projects that do not install
  TransformerLens.

Example:

```python
from SafeLens.core.factored_matrix import FactoredMatrix

W_QK = FactoredMatrix([[1, 2], [3, 4]], [[2, 0], [0, 2]])

assert W_QK.AB == [[2.0, 4.0], [6.0, 8.0]]
assert W_QK @ [1, 1] == [6.0, 14.0]
```

::: SafeLens.core.factored_matrix
