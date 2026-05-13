"""Hook and activation-cache primitives inspired by TransformerLens."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, MutableMapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Protocol

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper

NamesFilter = str | Sequence[str] | Callable[[str], bool] | None

_MISSING = object()


class RemovableHandle(Protocol):
    """Protocol for PyTorch-style removable hook handles."""

    def remove(self) -> None:
        """Remove a registered hook."""


def activation_name_for_layer(layer: LayerRef) -> str:
    """Return the canonical cache name for a layer reference."""
    if isinstance(layer, int):
        return f"layer_{layer}"
    return layer


def matches_names_filter(name: str, names_filter: NamesFilter = None) -> bool:
    """Return whether an activation name matches a TransformerLens-style names filter."""
    if names_filter is None:
        return True
    if isinstance(names_filter, str):
        return name == names_filter
    if callable(names_filter):
        return bool(names_filter(name))
    return name in names_filter


class ActivationCache(MutableMapping[str, Any]):
    """Dictionary-like activation cache with small tensor-friendly helpers."""

    def __init__(self, cache_dict: dict[str, Any] | None = None) -> None:
        self._cache = dict(cache_dict or {})

    def __getitem__(self, key: str) -> Any:
        return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def __delitem__(self, key: str) -> None:
        del self._cache[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._cache)

    def __len__(self) -> int:
        return len(self._cache)

    def store(
        self,
        name: str,
        activation: Any,
        *,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
    ) -> None:
        """Store an activation, optionally detaching, cloning, or moving it."""
        self._cache[name] = prepare_activation_for_cache(
            activation,
            detach=detach,
            clone=clone,
            device=device,
        )

    def get_activation(self, name: str) -> Any:
        """Return one cached activation."""
        return self._cache[name]

    def select(self, names_filter: NamesFilter) -> ActivationCache:
        """Return a new cache containing only matching activation names."""
        return ActivationCache(
            {
                name: value
                for name, value in self._cache.items()
                if matches_names_filter(name, names_filter)
            }
        )

    def clone(self) -> ActivationCache:
        """Return a cloned copy when activations support `.clone()`, otherwise deep-copy values."""
        return ActivationCache(
            {name: clone_activation(value) for name, value in self._cache.items()}
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary view copy."""
        return dict(self._cache)


def clone_activation(activation: Any) -> Any:
    """Clone tensor-like values and deep-copy everything else."""
    clone = getattr(activation, "clone", None)
    if callable(clone):
        return clone()
    return deepcopy(activation)


def prepare_activation_for_cache(
    activation: Any,
    *,
    detach: bool = True,
    clone: bool = False,
    device: Any = None,
) -> Any:
    """Prepare an activation for caching without requiring a torch dependency."""
    value = activation
    detach_fn = getattr(value, "detach", None)
    if detach and callable(detach_fn):
        value = detach_fn()
    if clone:
        value = clone_activation(value)
    to_fn = getattr(value, "to", None)
    if device is not None and callable(to_fn):
        value = to_fn(device)
    return value


def extract_hook_output(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """Extract an activation from either PyTorch-style or keyword-style hook calls."""
    if len(args) >= 3:
        return args[2]
    if "output" in kwargs:
        return kwargs["output"]
    if "activation" in kwargs:
        return kwargs["activation"]
    return _MISSING


def has_hook_output(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    """Return whether a hook call contains an activation output."""
    return extract_hook_output(args, kwargs) is not _MISSING


def make_cache_hook(
    cache: ActivationCache,
    name: str,
    *,
    detach: bool = True,
    clone: bool = False,
    device: Any = None,
) -> HookFn:
    """Create a hook that stores its activation in an `ActivationCache`."""

    def cache_hook(*args: Any, **kwargs: Any) -> None:
        activation = extract_hook_output(args, kwargs)
        if activation is _MISSING:
            return None
        cache.store(name, activation, detach=detach, clone=clone, device=device)
        return None

    return cache_hook


@contextmanager
def temporary_hooks(
    model: ModelWrapper,
    hooks: Iterable[tuple[LayerRef, HookFn]],
) -> Iterator[list[Any]]:
    """Register hooks for one context and always remove them afterward."""
    handles: list[Any] = []
    try:
        for layer, hook_fn in hooks:
            handles.append(model.add_hook(layer, hook_fn))
        yield handles
    finally:
        for handle in reversed(handles):
            remove = getattr(handle, "remove", None)
            if callable(remove):
                remove()


def run_with_hooks(
    model: ModelWrapper,
    batch: Batch,
    hooks: Iterable[tuple[LayerRef, HookFn]],
    *,
    layers: Sequence[LayerRef] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Run a model with temporary hooks and remove them when the run finishes."""
    with temporary_hooks(model, hooks):
        return model.run_with_cache(batch, layers=layers)


def cache_activations(
    model: ModelWrapper,
    batch: Batch,
    layers: Sequence[LayerRef],
    *,
    names_filter: NamesFilter = None,
    detach: bool = True,
    clone: bool = False,
    device: Any = None,
) -> tuple[Any, ActivationCache]:
    """Run a model while caching selected layer activations through temporary hooks."""
    cache = ActivationCache()
    hooks = []
    for layer in layers:
        name = activation_name_for_layer(layer)
        if matches_names_filter(name, names_filter):
            hooks.append(
                (
                    layer,
                    make_cache_hook(cache, name, detach=detach, clone=clone, device=device),
                )
            )
    output, _ = run_with_hooks(model, batch, hooks)
    return output, cache
