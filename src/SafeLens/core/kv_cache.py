"""TransformerLens-compatible key/value cache containers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


_MISSING = object()


@dataclass(init=False)
class KeyValueCacheEntry:
    """Cache entry for one layer's key and value activations."""

    keys: Any | None = None
    values: Any | None = None
    frozen: bool = False

    def __init__(
        self,
        keys: Any | None = None,
        values: Any | None = None,
        *,
        past_keys: Any = _MISSING,
        past_values: Any = _MISSING,
        frozen: bool = False,
    ) -> None:
        if past_keys is not _MISSING:
            keys = past_keys
        if past_values is not _MISSING:
            values = past_values
        self.keys = keys
        self.values = values
        self.frozen = bool(frozen)

    @classmethod
    def init_cache_entry(
        cls,
        cfg: Any,
        device: Any,
        batch_size: int = 1,
    ) -> KeyValueCacheEntry:
        """Create an empty TL-layout entry shaped ``[batch, 0, heads, d_head]``."""
        import torch

        n_heads = getattr(cfg, "n_key_value_heads", None)
        if n_heads is None:
            n_heads = getattr(cfg, "num_key_value_heads", None)
        if n_heads is None:
            n_heads = getattr(cfg, "n_heads", None)
        if n_heads is None:
            n_heads = getattr(cfg, "n_head", None)
        if n_heads is None:
            raise AttributeError("KV cache initialization requires cfg.n_heads.")
        d_head = getattr(cfg, "d_head", None)
        if d_head is None:
            hidden_size = getattr(cfg, "d_model", None)
            if hidden_size is None:
                hidden_size = getattr(cfg, "n_embd", None)
            if hidden_size is None:
                hidden_size = getattr(cfg, "hidden_size", None)
            if hidden_size is None:
                raise AttributeError("KV cache initialization requires cfg.d_head.")
            d_head = int(hidden_size) // int(n_heads)
        dtype = _torch_dtype_from_config(cfg, torch)
        return cls(
            past_keys=torch.empty(
                (int(batch_size), 0, int(n_heads), int(d_head)),
                device=device,
                dtype=dtype,
            ),
            past_values=torch.empty(
                (int(batch_size), 0, int(n_heads), int(d_head)),
                device=device,
                dtype=dtype,
            ),
        )

    @property
    def past_keys(self) -> Any | None:
        """TransformerLens name for cached keys."""
        return self.keys

    @past_keys.setter
    def past_keys(self, value: Any | None) -> None:
        self.keys = value

    @property
    def past_values(self) -> Any | None:
        """TransformerLens name for cached values."""
        return self.values

    @past_values.setter
    def past_values(self, value: Any | None) -> None:
        self.values = value

    def append(self, keys: Any, values: Any, *, dim: int = 1) -> tuple[Any, Any]:
        """Append new key/value tensors along the sequence dimension."""
        updated_keys = concat_values(self.keys, keys, dim=dim)
        updated_values = concat_values(self.values, values, dim=dim)
        if not self.frozen:
            self.keys = updated_keys
            self.values = updated_values
        return updated_keys, updated_values

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

    entries: dict[int, KeyValueCacheEntry] | list[KeyValueCacheEntry] = field(
        default_factory=dict
    )
    previous_attention_mask: Any | None = None
    frozen: bool = False

    @classmethod
    def init_cache(
        cls,
        cfg: Any,
        device: Any,
        batch_size: int = 1,
    ) -> KeyValueCache:
        """Create an empty cache following TransformerLens' ``init_cache`` API."""
        import torch

        n_layers = getattr(cfg, "n_layers", None)
        if n_layers is None:
            n_layers = getattr(cfg, "n_layer", None)
        if n_layers is None:
            num_hidden_layers = getattr(cfg, "num_hidden_layers", None)
            n_layers = 0 if num_hidden_layers is None else num_hidden_layers
        device_for_mask = device if device is not None else getattr(cfg, "device", None)
        if device_for_mask is None:
            device_for_mask = torch.device("cpu")

        entries = [
            KeyValueCacheEntry.init_cache_entry(
                cfg,
                _device_for_cache_layer(cfg, device, layer_index),
                batch_size=batch_size,
            )
            for layer_index in range(int(n_layers))
        ]
        return cls(
            entries=entries,
            previous_attention_mask=torch.empty(
                (int(batch_size), 0),
                device=device_for_mask,
                dtype=torch.int,
            ),
        )

    def __getitem__(self, layer: int) -> KeyValueCacheEntry:
        if isinstance(self.entries, Mapping):
            if layer not in self.entries:
                self.entries[layer] = KeyValueCacheEntry(frozen=self.frozen)
            return self.entries[layer]
        return self.entries[layer]

    def append(self, layer: int, keys: Any, values: Any, *, dim: int = 1) -> tuple[Any, Any]:
        """Append key/value activations for one layer."""
        return self[layer].append(keys, values, dim=dim)

    def freeze(self) -> None:
        """Prevent future appends from mutating this cache."""
        self.frozen = True
        for entry in _iter_entries(self.entries):
            entry.frozen = True

    def unfreeze(self) -> None:
        """Allow future appends to mutate this cache."""
        self.frozen = False
        for entry in _iter_entries(self.entries):
            entry.frozen = False

    def append_attention_mask(self, attention_mask: Any) -> Any:
        """Append a batch attention mask and return the full mask."""
        previous_attention_mask = self.previous_attention_mask
        if previous_attention_mask is None:
            previous_attention_mask = _empty_attention_mask_like(attention_mask)
        updated_attention_mask = concat_values(
            previous_attention_mask,
            attention_mask,
            dim=-1,
        )
        if not self.frozen:
            self.previous_attention_mask = updated_attention_mask
        return updated_attention_mask

    def to_dict(self) -> dict[int, dict[str, Any]]:
        """Return a serializable view."""
        if isinstance(self.entries, Mapping):
            return {layer: entry.to_dict() for layer, entry in self.entries.items()}
        return {layer: entry.to_dict() for layer, entry in enumerate(self.entries)}


TransformerLensKeyValueCacheEntry = KeyValueCacheEntry
TransformerLensKeyValueCache = KeyValueCache


def concat_values(old: Any | None, new: Any, *, dim: int = 1) -> Any:
    """Concatenate tensor-like or nested-list values."""
    if old is None:
        return new
    try:
        import torch

        if isinstance(old, torch.Tensor) or isinstance(new, torch.Tensor):
            if not isinstance(old, torch.Tensor):
                old = torch.as_tensor(
                    old,
                    dtype=getattr(new, "dtype", None),
                    device=getattr(new, "device", None),
                )
            if not isinstance(new, torch.Tensor):
                new = torch.as_tensor(new, dtype=old.dtype, device=old.device)
            return torch.cat([old, new.to(device=old.device, dtype=old.dtype)], dim=dim)
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(old, np.ndarray) or isinstance(new, np.ndarray):
            return np.concatenate([np.asarray(old), np.asarray(new)], axis=dim)
    except Exception:
        pass
    if dim < 0:
        shape = shape_of(old)
        if shape:
            dim += len(shape)
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
    if _is_sequence(value):
        if not value:
            return (0,)
        return (len(value), *shape_of(value[0]))
    return ()


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _iter_entries(
    entries: dict[int, KeyValueCacheEntry] | list[KeyValueCacheEntry],
) -> list[KeyValueCacheEntry]:
    if isinstance(entries, Mapping):
        return list(entries.values())
    return list(entries)


def _torch_dtype_from_config(cfg: Any, torch: Any) -> Any:
    dtype = getattr(cfg, "dtype", None)
    if dtype is None:
        return torch.get_default_dtype()
    if isinstance(dtype, torch.dtype):
        return dtype
    if isinstance(dtype, str):
        dtype_name = dtype.split(".")[-1]
        resolved = getattr(torch, dtype_name, None)
        if isinstance(resolved, torch.dtype):
            return resolved
    return dtype


def _device_for_cache_layer(cfg: Any, device: Any, layer_index: int) -> Any:
    n_devices = getattr(cfg, "n_devices", None)
    if n_devices is not None:
        try:
            from SafeLens.core.utilities import get_device_for_block_index

            return get_device_for_block_index(layer_index, cfg, device)
        except Exception:
            pass
    fallback_device = device if device is not None else getattr(cfg, "device", None)
    if fallback_device is not None:
        return fallback_device
    try:
        import torch

        return torch.device("cpu")
    except Exception:
        return "cpu"


def _empty_attention_mask_like(attention_mask: Any) -> Any:
    shape = shape_of(attention_mask)
    batch_size = int(shape[0]) if shape else 1
    try:
        import torch

        if isinstance(attention_mask, torch.Tensor):
            return torch.empty(
                (batch_size, 0),
                dtype=attention_mask.dtype,
                device=attention_mask.device,
            )
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(attention_mask, np.ndarray):
            return np.empty((batch_size, 0), dtype=attention_mask.dtype)
    except Exception:
        pass
    return [[] for _ in range(batch_size)]
