"""Hooked-root utilities inspired by TransformerLens' HookedRootModule."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Literal
import warnings

from SafeLens.core.hooks import (
    ActivationCache,
    HookDirection,
    HookPoint,
    LensHandle,
    NamesFilter,
    make_cache_hook,
    matches_names_filter,
)


class HookedRoot:
    """Small dependency-free root object for managing named `HookPoint`s."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__
        self.hook_dict: dict[str, HookPoint] = {}
        self.mod_dict: dict[str, Any] = {}
        self.context_level = 0
        self._next_hook_level = 0

    def setup(self, hook_points: Mapping[str, HookPoint] | Iterable[HookPoint]) -> None:
        """Register hook points by name."""
        if isinstance(hook_points, Mapping):
            for name, hook_point in hook_points.items():
                hook_point.name = str(name)
                self.hook_dict[str(name)] = hook_point
                self.mod_dict[str(name)] = hook_point
            return
        for hook_point in hook_points:
            if hook_point.name is None:
                raise ValueError("Cannot register an unnamed HookPoint.")
            self.hook_dict[hook_point.name] = hook_point
            self.mod_dict[hook_point.name] = hook_point

    def add_hook_point(self, name: str, hook_point: HookPoint | None = None) -> HookPoint:
        """Create or register one named hook point."""
        point = hook_point or HookPoint(name)
        point.name = name
        self.hook_dict[name] = point
        self.mod_dict[name] = point
        return point

    def hook_points(self) -> list[HookPoint]:
        """Return registered hook points in insertion order."""
        return list(self.hook_dict.values())

    def list_hooks(
        self,
        name_filter: NamesFilter = None,
        dir: HookDirection = "both",
        including_permanent: bool = True,
    ) -> dict[str, list[LensHandle]]:
        """Return active hooks grouped by hook-point name."""
        hooks_by_name: dict[str, list[LensHandle]] = {}
        for name in self._matching_hook_names(name_filter):
            hook_point = self.hook_dict[name]
            handles: list[LensHandle] = []
            if dir in ("fwd", "both"):
                handles.extend(handle for _hook_fn, handle in hook_point.fwd_hooks)
            if dir in ("bwd", "both"):
                handles.extend(handle for _hook_fn, handle in hook_point.bwd_hooks)
            if dir not in ("fwd", "bwd", "both"):
                raise ValueError(f"Invalid hook direction {dir!r}.")
            if not including_permanent:
                handles = [handle for handle in handles if not handle.is_permanent]
            if handles:
                hooks_by_name[name] = handles
        return hooks_by_name

    def check_hooks_to_add(
        self,
        hook_specs: Iterable[tuple[str, Callable[..., Any]]],
    ) -> None:
        """Validate that all hook names exist before adding any hooks."""
        missing = [name for name, _hook_fn in hook_specs if self._resolve_hook_name(name) is None]
        if missing:
            available = ", ".join(self.hook_dict)
            raise KeyError(f"Unknown hook point(s): {missing}. Available: {available}")

    def check_and_add_hook(
        self,
        name: str,
        hook_fn: Callable[..., Any],
        *,
        dir: Literal["fwd", "bwd"] = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
        alias_names: Iterable[str] | None = None,
    ) -> LensHandle:
        """Validate and add one hook."""
        resolved_name = self._resolve_hook_name(name)
        if resolved_name is None:
            available = ", ".join(self.hook_dict)
            raise KeyError(f"Unknown hook point {name!r}. Available: {available}")
        return self.hook_dict[resolved_name].add_hook(
            hook_fn,
            dir=dir,
            is_permanent=is_permanent,
            level=level,
            prepend=prepend,
            alias_names=tuple(alias_names) if alias_names is not None else None,
        )

    def add_hook(
        self,
        names_filter: NamesFilter,
        hook_fn: Callable[..., Any],
        *,
        dir: Literal["fwd", "bwd"] = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
        alias_names: Iterable[str] | None = None,
    ) -> list[LensHandle]:
        """Add a hook to every hook point matching a names filter."""
        resolved_alias_names = tuple(alias_names) if alias_names is not None else None
        handles: list[LensHandle] = []
        for name in self._matching_hook_names(names_filter):
            hook_point = self.hook_dict[name]
            handles.append(
                hook_point.add_hook(
                    hook_fn,
                    dir=dir,
                    is_permanent=is_permanent,
                    level=level,
                    prepend=prepend,
                    alias_names=resolved_alias_names,
                )
            )
        return handles

    def add_perma_hook(
        self,
        names_filter: NamesFilter,
        hook_fn: Callable[..., Any],
        *,
        dir: Literal["fwd", "bwd"] = "fwd",
    ) -> list[LensHandle]:
        """Add permanent hooks to matching hook points."""
        return self.add_hook(names_filter, hook_fn, dir=dir, is_permanent=True)

    def remove_all_hook_fns(
        self,
        dir: HookDirection = "both",
        *,
        including_permanent: bool = False,
        level: int | None = None,
    ) -> None:
        """Remove matching hooks from all hook points."""
        for hook_point in self.hook_points():
            hook_point.remove_hooks(
                dir=dir,
                including_permanent=including_permanent,
                level=level,
            )

    def reset_hooks(
        self,
        *,
        clear_contexts: bool = True,
        direction: HookDirection | None = None,
        dir: HookDirection | None = None,
        including_permanent: bool = False,
        level: int | None = None,
    ) -> None:
        """Remove hooks and optionally clear hook contexts."""
        hook_direction = direction or dir or "both"
        self.remove_all_hook_fns(
            hook_direction,
            including_permanent=including_permanent,
            level=level,
        )
        if clear_contexts:
            self.clear_contexts()

    def clear_contexts(self) -> None:
        """Clear context dictionaries on all hook points."""
        for hook_point in self.hook_points():
            hook_point.clear_context()

    def get_caching_hooks(
        self,
        names_filter: NamesFilter = None,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | None = None,
    ) -> tuple[
        ActivationCache,
        list[tuple[str, Callable[..., Any]]],
        list[tuple[str, Callable[..., Any]]],
    ]:
        """Create cache storage and forward/backward hook specs."""
        cache = ActivationCache(has_batch_dim=not remove_batch_dim) if cache is None else cache
        if remove_batch_dim:
            cache.has_batch_dim = False
        fwd_hooks: list[tuple[str, Callable[..., Any]]] = []
        bwd_hooks: list[tuple[str, Callable[..., Any]]] = []
        for name in self._matching_hook_names(names_filter):
            fwd_hooks.append(
                (
                    name,
                    make_cache_hook(
                        cache,
                        name,
                        detach=detach,
                        clone=clone,
                        device=device,
                        pos_slice=pos_slice,
                        remove_batch_dim=remove_batch_dim,
                    ),
                )
            )
            if incl_bwd:
                bwd_hooks.append(
                    (
                        name,
                        make_cache_hook(
                            cache,
                            f"{name}_grad",
                            detach=detach,
                            clone=clone,
                            device=device,
                            pos_slice=pos_slice,
                            remove_batch_dim=remove_batch_dim,
                        ),
                    )
                )
        return cache, fwd_hooks, bwd_hooks

    def add_caching_hooks(
        self,
        names_filter: NamesFilter = None,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | None = None,
    ) -> ActivationCache:
        """Add caching hooks and return the mutable cache."""
        previous_cache_model = cache.model if cache is not None else None
        previous_has_batch_dim = cache.has_batch_dim if cache is not None else not remove_batch_dim
        activation_cache, fwd_hooks, bwd_hooks = self.get_caching_hooks(
            names_filter,
            incl_bwd=incl_bwd,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
            cache=cache,
        )
        if remove_batch_dim:
            activation_cache.has_batch_dim = False
        handles: list[LensHandle] = []
        try:
            for name, hook_fn in fwd_hooks:
                handles.append(self.check_and_add_hook(name, hook_fn))
            for name, hook_fn in bwd_hooks:
                handles.append(self.check_and_add_hook(name, hook_fn, dir="bwd"))
        except Exception:
            for handle in reversed(handles):
                handle.remove()
            activation_cache.model = previous_cache_model
            activation_cache.has_batch_dim = previous_has_batch_dim
            raise
        return activation_cache

    def cache_all(
        self,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | None = None,
    ) -> ActivationCache:
        """Permanently cache all hook-point activations until hooks are reset."""
        return self.add_caching_hooks(
            None,
            incl_bwd=incl_bwd,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
            cache=cache,
        )

    def cache_some(
        self,
        names_filter: NamesFilter,
        *,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | None = None,
    ) -> ActivationCache:
        """Permanently cache matching hook-point activations until hooks are reset."""
        return self.add_caching_hooks(
            names_filter,
            incl_bwd=incl_bwd,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
            cache=cache,
        )

    @contextmanager
    def hooks(
        self,
        fwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        bwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        *,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
    ) -> Iterator[HookedRoot]:
        """Temporarily add forward/backward hooks."""
        try:
            self.context_level += 1
            self._next_hook_level += 1
            level = self._next_hook_level
            self._add_hook_specs(fwd_hooks, dir="fwd", level=level)
            self._add_hook_specs(bwd_hooks, dir="bwd", level=level)
            yield self
        finally:
            if reset_hooks_end:
                self.reset_hooks(
                    clear_contexts=clear_contexts,
                    including_permanent=False,
                    level=level,
                )
            self.context_level -= 1

    def run_with_hooks(
        self,
        run_fn: Callable[..., Any],
        *args: Any,
        fwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        bwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Run an arbitrary callable with temporary hooks registered."""
        bwd_hook_specs = list(bwd_hooks)
        if bwd_hook_specs and reset_hooks_end:
            warnings.warn(
                "Hooks will be reset at the end of run_with_hooks. This removes the "
                "backward hooks before a backward pass can occur.",
                UserWarning,
                stacklevel=2,
            )
        with self.hooks(
            fwd_hooks=fwd_hooks,
            bwd_hooks=bwd_hook_specs,
            reset_hooks_end=reset_hooks_end,
            clear_contexts=clear_contexts,
        ):
            return run_fn(*args, **kwargs)

    def run_with_cache(
        self,
        run_fn: Callable[..., Any],
        *args: Any,
        names_filter: NamesFilter = None,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        cache: ActivationCache | None = None,
        **kwargs: Any,
    ) -> tuple[Any, ActivationCache]:
        """Run a callable while temporarily caching matching hook-point activations."""
        external_cache = cache
        previous_cache_model = external_cache.model if external_cache is not None else None
        previous_has_batch_dim = (
            external_cache.has_batch_dim if external_cache is not None else not remove_batch_dim
        )
        try:
            activation_cache, fwd_hooks, bwd_hooks = self.get_caching_hooks(
                names_filter,
                incl_bwd=incl_bwd,
                detach=detach,
                clone=clone,
                device=device,
                pos_slice=pos_slice,
                remove_batch_dim=remove_batch_dim,
                cache=external_cache,
            )
        except Exception:
            if external_cache is not None:
                external_cache.model = previous_cache_model
                external_cache.has_batch_dim = previous_has_batch_dim
            raise
        level = id(activation_cache)
        handles: list[LensHandle] = []
        install_complete = False
        try:
            handles.extend(self._add_hook_specs(fwd_hooks, dir="fwd", level=level))
            handles.extend(self._add_hook_specs(bwd_hooks, dir="bwd", level=level))
            install_complete = True
            output = run_fn(*args, **kwargs)
            if incl_bwd:
                backward = getattr(output, "backward", None)
                if not callable(backward):
                    raise ValueError(
                        "incl_bwd=True requires the run function to return a scalar loss."
                    )
                backward()
        finally:
            if reset_hooks_end:
                for handle in reversed(handles):
                    handle.remove()
            if clear_contexts:
                self.clear_contexts()
            if not install_complete and external_cache is not None:
                activation_cache.model = previous_cache_model
                activation_cache.has_batch_dim = previous_has_batch_dim
        if remove_batch_dim:
            activation_cache = activation_cache.remove_batch_dim()
        return output, activation_cache

    def _add_hook_specs(
        self,
        hook_specs: Iterable[tuple[NamesFilter, Callable[..., Any]]],
        *,
        dir: Literal["fwd", "bwd"],
        level: int | None,
    ) -> list[LensHandle]:
        handles: list[LensHandle] = []
        try:
            for names_filter, hook_fn in hook_specs:
                if isinstance(names_filter, str):
                    handles.append(
                        self.check_and_add_hook(str(names_filter), hook_fn, dir=dir, level=level)
                    )
                    continue
                matched = self.add_hook(names_filter, hook_fn, dir=dir, level=level)
                if not matched:
                    raise KeyError(f"No hook points matched filter {names_filter!r}.")
                handles.extend(matched)
        except Exception:
            for handle in reversed(handles):
                handle.remove()
            raise
        return handles

    def _resolve_hook_name(self, name: str) -> str | None:
        if name in self.hook_dict:
            return name
        matches = [hook_name for hook_name in self.hook_dict if matches_names_filter(hook_name, name)]
        if len(matches) == 1:
            return matches[0]
        return None

    def _matching_hook_names(self, names_filter: NamesFilter) -> list[str]:
        if names_filter is None or callable(names_filter):
            return [
                name for name in self.hook_dict if matches_names_filter(name, names_filter)
            ]
        if isinstance(names_filter, str):
            resolved = self._resolve_hook_name(names_filter)
            return [] if resolved is None else [resolved]

        matches: list[str] = []
        seen: set[str] = set()
        for candidate in names_filter:
            resolved = self._resolve_hook_name(str(candidate))
            if resolved is None or resolved in seen:
                continue
            seen.add(resolved)
            matches.append(resolved)
        return matches
