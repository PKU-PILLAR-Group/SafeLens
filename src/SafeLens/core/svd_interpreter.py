"""TransformerLens-style SVD interpretation helpers."""

from __future__ import annotations

from typing import Any, Literal

from SafeLens.core.factored_matrix import (
    FactoredMatrix,
    matmul,
    multiply_values,
    shape_of,
    transpose,
)

OUTPUT_EMBEDDING = "unembed.W_U"
VECTOR_TYPES = ("OV", "w_in", "w_out")


class SVDInterpreter:
    """Dependency-free equivalent of TransformerLens' SVDInterpreter.

    The interpreter reads TransformerLens-style parameter names from models that
    expose ``tl_parameters()``. It can also consume ``named_parameters()`` from a
    HookedTransformer-like object without importing TransformerLens.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        self.cfg = getattr(model, "cfg", getattr(model, "config", None))
        tl_parameters = getattr(model, "tl_parameters", None)
        if callable(tl_parameters):
            self.params = dict(tl_parameters())
            return
        named_parameters = getattr(model, "named_parameters", None)
        if callable(named_parameters):
            self.params = {name: param for name, param in named_parameters()}
            return
        raise ValueError(
            "SVDInterpreter requires a model exposing tl_parameters() or named_parameters()."
        )

    def get_singular_vectors(
        self,
        vector_type: Literal["OV", "w_in", "w_out"],
        layer_index: int,
        num_vectors: int = 10,
        head_index: int | None = None,
    ) -> Any:
        """Return top singular directions projected through the unembedding.

        The return shape follows TransformerLens: ``[d_vocab, 1, num_vectors]``.
        ``head_index`` is required for ``"OV"`` and ignored for MLP matrices.
        """
        if num_vectors < 0:
            raise ValueError("num_vectors must be non-negative.")
        if head_index is None:
            if vector_type not in {"w_in", "w_out"}:
                raise AssertionError(
                    f"Head index optional only for w_in and w_out, got {vector_type}"
                )

        if vector_type == "OV":
            assert head_index is not None
            matrix = self._get_OV_matrix(layer_index, head_index)
            vh = transpose(matrix.V)
        elif vector_type == "w_in":
            vh = _svd_vh(self._get_w_in_matrix(layer_index))
        elif vector_type == "w_out":
            vh = _svd_vh(self._get_w_out_matrix(layer_index))
        else:
            raise ValueError(
                f"Vector type must be in {list(VECTOR_TYPES)}, instead got {vector_type}"
            )

        return self._get_singular_vectors_from_matrix(vh, self._get_output_embedding(), num_vectors)

    def _get_singular_vectors_from_matrix(
        self,
        vh: Any,
        embedding: Any,
        num_vectors: int = 10,
    ) -> Any:
        """Project right singular vectors into vocabulary space."""
        available_vectors = _first_dim(vh)
        if num_vectors > available_vectors:
            raise ValueError(
                f"Requested {num_vectors} singular vectors, "
                f"but only {available_vectors} are available."
            )
        expected_vocab = _cfg_int(self.cfg, "d_vocab", "vocab_size")
        if num_vectors == 0:
            result = _empty_singular_vector_stack(
                expected_vocab or _embedding_vocab_size(embedding),
                embedding,
            )
            if expected_vocab is not None and shape_of(result) != (expected_vocab, 1, 0):
                raise AssertionError(
                    f"Vectors shape should be {(expected_vocab, 1, 0)} but got {shape_of(result)}."
                )
            return result
        vectors = []
        for index in range(num_vectors):
            vector, aligned_embedding = _align_torch_matmul_dtypes(
                _to_float_if_tensor(_index_first_dim(vh, index)),
                embedding,
            )
            vectors.append(matmul(vector, aligned_embedding))
        result = _stack_vocab_vectors(vectors)
        shape = shape_of(result)
        if expected_vocab is not None and shape != (expected_vocab, 1, num_vectors):
            raise AssertionError(
                f"Vectors shape should be {(expected_vocab, 1, num_vectors)} but got {shape}."
            )
        return result

    def _get_OV_matrix(self, layer_index: int, head_index: int) -> FactoredMatrix:
        """Return one head's OV circuit matrix."""
        _validate_layer(self.cfg, layer_index)
        _validate_head(self.cfg, head_index)
        ov_matrix = getattr(self.model, "OV", None)
        if isinstance(ov_matrix, FactoredMatrix):
            return ov_matrix[layer_index, head_index]
        w_v = self._required_param(f"blocks.{layer_index}.attn.W_V")
        w_o = self._required_param(f"blocks.{layer_index}.attn.W_O")
        return FactoredMatrix(_index_first_dim(w_v, head_index), _index_first_dim(w_o, head_index))

    def _get_w_in_matrix(self, layer_index: int) -> Any:
        """Return one layer's input MLP matrix, matching TransformerLens orientation."""
        _validate_layer(self.cfg, layer_index)
        w_in = transpose(self._required_param(f"blocks.{layer_index}.mlp.W_in"))
        ln2_key = f"blocks.{layer_index}.ln2.w"
        if ln2_key in self.params:
            return multiply_values(w_in, self.params[ln2_key])
        return w_in

    def _get_w_out_matrix(self, layer_index: int) -> Any:
        """Return one layer's output MLP matrix."""
        _validate_layer(self.cfg, layer_index)
        return self._required_param(f"blocks.{layer_index}.mlp.W_out")

    def _get_output_embedding(self) -> Any:
        return self._required_param(OUTPUT_EMBEDDING)

    def _required_param(self, name: str) -> Any:
        try:
            return self.params[name]
        except KeyError as exc:
            raise KeyError(f"Model parameters do not include {name!r}.") from exc


def _svd_vh(matrix: Any) -> Any:
    try:
        import torch

        if isinstance(matrix, torch.Tensor):
            _u, _s, vh = torch.linalg.svd(matrix.float())
            return vh
    except Exception:
        pass
    try:
        import numpy as np

        _u, _s, vh = np.linalg.svd(np.asarray(matrix, dtype=float))
        return vh.tolist()
    except Exception as exc:
        raise RuntimeError("SVDInterpreter requires torch or numpy-compatible matrices.") from exc


def _stack_vocab_vectors(vectors: list[Any]) -> Any:
    if not vectors:
        return []
    first = vectors[0]
    try:
        import torch

        if isinstance(first, torch.Tensor):
            return torch.stack(vectors, dim=1).unsqueeze(1)
    except Exception:
        pass
    try:
        import numpy as np

        array = np.stack([np.asarray(vector, dtype=float) for vector in vectors], axis=1)
        return array[:, None, :].tolist()
    except Exception:
        vocab_size = len(first)
        return [
            [[vectors[vector_index][vocab_index] for vector_index in range(len(vectors))]]
            for vocab_index in range(vocab_size)
        ]


def _empty_singular_vector_stack(vocab_size: int | None, embedding: Any) -> Any:
    if vocab_size is None:
        return []
    try:
        import torch

        if isinstance(embedding, torch.Tensor):
            return embedding.new_empty((vocab_size, 1, 0))
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(embedding, "shape"):
            return np.empty((vocab_size, 1, 0)).tolist()
    except Exception:
        pass
    return [[[]] for _ in range(vocab_size)]


def _embedding_vocab_size(embedding: Any) -> int | None:
    shape = shape_of(embedding)
    if shape:
        return int(shape[-1])
    return None


def _index_first_dim(value: Any, index: int) -> Any:
    return value[index]


def _first_dim(value: Any) -> int:
    shape = shape_of(value)
    if not shape:
        raise ValueError("Cannot infer singular-vector count from a scalar.")
    return int(shape[0])


def _to_float_if_tensor(value: Any) -> Any:
    float_fn = getattr(value, "float", None)
    if callable(float_fn):
        return float_fn()
    return value


def _align_torch_matmul_dtypes(left: Any, right: Any) -> tuple[Any, Any]:
    try:
        import torch

        if not (isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor)):
            return left, right
        if left.dtype == right.dtype:
            return left, right
        target_dtype = torch.promote_types(left.dtype, right.dtype)
        if not torch.is_floating_point(torch.empty((), dtype=target_dtype)):
            target_dtype = torch.float32
        if target_dtype in {torch.float16, torch.bfloat16}:
            target_dtype = torch.float32
        return left.to(target_dtype), right.to(target_dtype)
    except Exception:
        return left, right


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


def _validate_layer(cfg: Any, layer_index: int) -> None:
    n_layers = _cfg_int(cfg, "n_layers", "num_hidden_layers", "n_layer", "num_layers")
    if n_layers is not None and not 0 <= int(layer_index) < n_layers:
        raise AssertionError(
            f"Layer index must be between 0 and {n_layers - 1} but got {layer_index}"
        )


def _validate_head(cfg: Any, head_index: int) -> None:
    n_heads = _cfg_int(cfg, "n_heads", "num_attention_heads", "n_head", "num_heads")
    if n_heads is not None and not 0 <= int(head_index) < n_heads:
        raise AssertionError(f"Head index must be between 0 and {n_heads - 1} but got {head_index}")
