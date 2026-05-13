"""Hooked-root utilities inspired by TransformerLens' HookedRootModule."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Literal

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

    def check_hooks_to_add(
        self,
        hook_specs: Iterable[tuple[str, Callable[..., Any]]],
    ) -> None:
        """Validate that all hook names exist before adding any hooks."""
        missing = [name for name, _hook_fn in hook_specs if name not in self.hook_dict]
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
    ) -> LensHandle:
        """Validate and add one hook."""
        if name not in self.hook_dict:
            available = ", ".join(self.hook_dict)
            raise KeyError(f"Unknown hook point {name!r}. Available: {available}")
        return self.hook_dict[name].add_hook(
            hook_fn,
            dir=dir,
            is_permanent=is_permanent,
            level=level,
            prepend=prepend,
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
    ) -> list[LensHandle]:
        """Add a hook to every hook point matching a names filter."""
        handles: list[LensHandle] = []
        for name, hook_point in self.hook_dict.items():
            if matches_names_filter(name, names_filter):
                handles.append(
                    hook_point.add_hook(
                        hook_fn,
                        dir=dir,
                        is_permanent=is_permanent,
                        level=level,
                        prepend=prepend,
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
        including_permanent: bool = False,
    ) -> None:
        """Remove hooks and optionally clear hook contexts."""
        self.remove_all_hook_fns(including_permanent=including_permanent)
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
    ) -> tuple[
        ActivationCache,
        list[tuple[str, Callable[..., Any]]],
        list[tuple[str, Callable[..., Any]]],
    ]:
        """Create cache storage and forward/backward hook specs."""
        cache = ActivationCache()
        fwd_hooks: list[tuple[str, Callable[..., Any]]] = []
        bwd_hooks: list[tuple[str, Callable[..., Any]]] = []
        for name in self.hook_dict:
            if matches_names_filter(name, names_filter):
                fwd_hooks.append(
                    (
                        name,
                        make_cache_hook(
                            cache,
                            name,
                            detach=detach,
                            clone=clone,
                            device=device,
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
    ) -> ActivationCache:
        """Add caching hooks and return the mutable cache."""
        cache = ActivationCache()
        for name in self.hook_dict:
            if matches_names_filter(name, names_filter):
                self.check_and_add_hook(
                    name,
                    make_cache_hook(cache, name, detach=detach, clone=clone, device=device),
                )
                if incl_bwd:
                    self.check_and_add_hook(
                        name,
                        make_cache_hook(
                            cache,
                            f"{name}_grad",
                            detach=detach,
                            clone=clone,
                            device=device,
                        ),
                        dir="bwd",
                    )
        return cache

    @contextmanager
    def hooks(
        self,
        fwd_hooks: Iterable[tuple[str, Callable[..., Any]]] = (),
        bwd_hooks: Iterable[tuple[str, Callable[..., Any]]] = (),
        *,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
    ) -> Iterator[None]:
        """Temporarily add forward/backward hooks."""
        level = id(fwd_hooks) ^ id(bwd_hooks)
        handles: list[LensHandle] = []
        try:
            for name, hook_fn in fwd_hooks:
                handles.append(self.check_and_add_hook(name, hook_fn, level=level))
            for name, hook_fn in bwd_hooks:
                handles.append(self.check_and_add_hook(name, hook_fn, dir="bwd", level=level))
            yield
        finally:
            if reset_hooks_end:
                for handle in reversed(handles):
                    handle.remove()
            if clear_contexts:
                self.clear_contexts()

    def run_with_hooks(
        self,
        run_fn: Callable[..., Any],
        *args: Any,
        fwd_hooks: Iterable[tuple[str, Callable[..., Any]]] = (),
        bwd_hooks: Iterable[tuple[str, Callable[..., Any]]] = (),
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Run an arbitrary callable with temporary hooks registered."""
        with self.hooks(
            fwd_hooks=fwd_hooks,
            bwd_hooks=bwd_hooks,
            reset_hooks_end=reset_hooks_end,
            clear_contexts=clear_contexts,
        ):
            return run_fn(*args, **kwargs)
