"""Minimal key/value cache containers for autoregressive analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KeyValueCacheEntry:
    """Cache entry for one layer's key and value activations."""

    keys: Any | None = None
    values: Any | None = None

    def append(self, keys: Any, values: Any, *, dim: int = 1) -> None:
        """Append new key/value tensors along the sequence dimension."""
        self.keys = concat_values(self.keys, keys, dim=dim)
        self.values = concat_values(self.values, values, dim=dim)

    @property
    def sequence_length(self) -> int:
        """Return cached sequence length when shape is available."""
        shape = shape_of(self.keys)
        return int(shape[1]) if len(shape) >= 2 else 0

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable view."""
        return {"keys": self.keys, "values": self.values, "sequence_length": self.sequence_length}


@dataclass
class KeyValueCache:
    """Dictionary-like key/value cache keyed by layer index."""

    entries: dict[int, KeyValueCacheEntry] = field(default_factory=dict)

    def __getitem__(self, layer: int) -> KeyValueCacheEntry:
        if layer not in self.entries:
            self.entries[layer] = KeyValueCacheEntry()
        return self.entries[layer]

    def append(self, layer: int, keys: Any, values: Any, *, dim: int = 1) -> None:
        """Append key/value activations for one layer."""
        self[layer].append(keys, values, dim=dim)

    def to_dict(self) -> dict[int, dict[str, Any]]:
        """Return a serializable view."""
        return {layer: entry.to_dict() for layer, entry in self.entries.items()}


def concat_values(old: Any | None, new: Any, *, dim: int = 1) -> Any:
    """Concatenate tensor-like or nested-list values."""
    if old is None:
        return new
    try:
        import torch

        if hasattr(old, "shape") and hasattr(new, "shape"):
            return torch.cat([old, new], dim=dim)
    except Exception:
        pass
    if dim == 0:
        return list(old) + list(new)
    return [
        concat_values(old_item, new_item, dim=dim - 1)
        for old_item, new_item in zip(old, new, strict=True)
    ]


def shape_of(value: Any) -> tuple[int, ...]:
    """Return best-effort shape."""
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, list):
        if not value:
            return (0,)
        return (len(value), *shape_of(value[0]))
    return ()
