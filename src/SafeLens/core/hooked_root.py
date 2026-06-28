"""Hooked-root utilities inspired by TransformerLens' HookedRootModule."""

from __future__ import annotations

import warnings
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Literal, cast

from SafeLens.core.hooks import (
    ActivationCache,
    HookDirection,
    HookPoint,
    LensHandle,
    NamesFilter,
    make_cache_hook,
    matches_names_filter,
)

_MISSING = object()


class HookedRoot:
    """Small dependency-free root object for managing named `HookPoint`s."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.__class__.__name__
        self.hook_dict: dict[str, HookPoint] = {}
        self.mod_dict: dict[str, Any] = {}
        self.is_caching = False
        self.context_level = 0
        self._next_hook_level = 0

    def setup(
        self,
        hook_points: Mapping[str, HookPoint] | Iterable[HookPoint] | None = None,
    ) -> None:
        """Register hook points by name, or discover HookPoint attributes on this object."""
        if hook_points is None:
            self.hook_dict.clear()
            self.mod_dict.clear()
            for name, hook_point in self._iter_named_hook_points():
                hook_point.name = name
                self.hook_dict[name] = hook_point
                self.mod_dict[name] = hook_point
            return
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
        hook_specs_or_hook_point: Iterable[tuple[str, Callable[..., Any]]] | HookPoint,
        hook_point_name: str | None = None,
        hook: Callable[..., Any] | None = None,
        *,
        dir: Literal["fwd", "bwd"] = "fwd",
        is_permanent: bool = False,
        prepend: bool = False,
    ) -> None:
        """Validate that all hook names exist before adding any hooks."""
        _ = hook, dir, is_permanent, prepend
        if isinstance(hook_specs_or_hook_point, HookPoint):
            if hook_point_name is None:
                raise TypeError("hook_point_name is required when checking one HookPoint.")
            if self._resolve_hook_name(hook_point_name) is None:
                available = ", ".join(self.hook_dict)
                raise KeyError(f"Unknown hook point {hook_point_name!r}. Available: {available}")
            return
        missing = [
            name
            for name, _hook_fn in hook_specs_or_hook_point
            if self._resolve_hook_name(name) is None
        ]
        if missing:
            available = ", ".join(self.hook_dict)
            raise KeyError(f"Unknown hook point(s): {missing}. Available: {available}")

    def check_and_add_hook(
        self,
        name_or_hook_point: str | HookPoint,
        hook_point_name_or_hook_fn: str | Callable[..., Any] | object = _MISSING,
        hook: Callable[..., Any] | None = None,
        *,
        dir: Literal["fwd", "bwd"] = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
        alias_names: Iterable[str] | None = None,
    ) -> LensHandle:
        """Validate and add one hook."""
        if isinstance(name_or_hook_point, HookPoint):
            hook_point = name_or_hook_point
            if not isinstance(hook_point_name_or_hook_fn, str):
                raise TypeError("hook_point_name must be a string.")
            if hook is None:
                raise TypeError("hook is required when passing a HookPoint.")
            hook_point_name = hook_point_name_or_hook_fn
            self.check_hooks_to_add(
                hook_point,
                hook_point_name,
                hook,
                dir=dir,
                is_permanent=is_permanent,
                prepend=prepend,
            )
            return hook_point.add_hook(
                hook,
                dir=dir,
                is_permanent=is_permanent,
                level=level,
                prepend=prepend,
                alias_names=tuple(alias_names) if alias_names is not None else None,
            )
        name = name_or_hook_point
        candidate_hook: object
        if hook_point_name_or_hook_fn is _MISSING:
            candidate_hook = hook
        elif hook is not None:
            raise TypeError("Pass only one hook function.")
        else:
            candidate_hook = hook_point_name_or_hook_fn
        if not callable(candidate_hook):
            raise TypeError("hook must be callable.")
        hook_fn = candidate_hook
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
        hook_fn: Callable[..., Any] | None = None,
        *,
        hook: Callable[..., Any] | None = None,
        dir: Literal["fwd", "bwd"] = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
        alias_names: Iterable[str] | None = None,
    ) -> list[LensHandle]:
        """Add a hook to every hook point matching a names filter."""
        if hook_fn is not None and hook is not None:
            raise TypeError("Pass only one of `hook_fn` or `hook`.")
        resolved_hook = hook_fn if hook_fn is not None else hook
        if not callable(resolved_hook):
            raise TypeError("hook must be callable.")
        resolved_alias_names = tuple(alias_names) if alias_names is not None else None
        handles: list[LensHandle] = []
        for name in self._matching_hook_names(names_filter):
            hook_point = self.hook_dict[name]
            handles.append(
                hook_point.add_hook(
                    resolved_hook,
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
        hook_fn: Callable[..., Any] | None = None,
        *,
        hook: Callable[..., Any] | None = None,
        dir: Literal["fwd", "bwd"] = "fwd",
    ) -> list[LensHandle]:
        """Add permanent hooks to matching hook points."""
        return self.add_hook(names_filter, hook_fn, hook=hook, dir=dir, is_permanent=True)

    def remove_all_hook_fns(
        self,
        dir: HookDirection = "both",
        *,
        direction: HookDirection | None = None,
        including_permanent: bool = False,
        level: int | None = None,
    ) -> None:
        """Remove matching hooks from all hook points."""
        if direction is not None:
            dir = direction
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
        self.is_caching = self._has_active_cache_hooks()

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
        cache: ActivationCache | dict[str, Any] | None = None,
    ) -> tuple[
        ActivationCache,
        list[tuple[str, Callable[..., Any]]],
        list[tuple[str, Callable[..., Any]]],
    ]:
        """Create cache storage and forward/backward hook specs."""
        matching_names = self._matching_hook_names(names_filter)
        cache = _coerce_activation_cache(cache, model=self, has_batch_dim=not remove_batch_dim)
        cache.model = self
        cache.has_batch_dim = not remove_batch_dim
        self.is_caching = True
        fwd_hooks: list[tuple[str, Callable[..., Any]]] = []
        bwd_hooks: list[tuple[str, Callable[..., Any]]] = []
        for name in matching_names:
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
        cache: ActivationCache | dict[str, Any] | None = None,
    ) -> ActivationCache:
        """Add caching hooks and return the mutable cache."""
        previous_is_caching = self.is_caching
        activation_cache_arg = _coerce_activation_cache(
            cache,
            model=self,
            has_batch_dim=not remove_batch_dim,
        )
        previous_cache_model = activation_cache_arg.model
        previous_has_batch_dim = activation_cache_arg.has_batch_dim
        activation_cache, fwd_hooks, bwd_hooks = self.get_caching_hooks(
            names_filter,
            incl_bwd=incl_bwd,
            detach=detach,
            clone=clone,
            device=device,
            pos_slice=pos_slice,
            remove_batch_dim=remove_batch_dim,
            cache=activation_cache_arg,
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
            self.is_caching = previous_is_caching
            activation_cache.model = previous_cache_model
            activation_cache.has_batch_dim = previous_has_batch_dim
            raise
        return activation_cache

    def cache_all(
        self,
        cache: ActivationCache | dict[str, Any] | None = None,
        *,
        names_filter: NamesFilter = None,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
    ) -> ActivationCache:
        """Permanently cache all hook-point activations until hooks are reset."""
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

    def cache_some(
        self,
        cache_or_names_filter: ActivationCache | dict[str, Any] | NamesFilter = None,
        names_filter: NamesFilter = None,
        *,
        names: NamesFilter = None,
        incl_bwd: bool = False,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
        pos_slice: Any = None,
        remove_batch_dim: bool = False,
        cache: ActivationCache | dict[str, Any] | None = None,
    ) -> ActivationCache:
        """Permanently cache matching hook-point activations until hooks are reset."""
        if _looks_like_external_cache(cache_or_names_filter):
            if cache is not None:
                raise TypeError("Pass external cache either positionally or by keyword, not both.")
            cache = cast(ActivationCache | dict[str, Any], cache_or_names_filter)
        elif cache_or_names_filter is not None:
            if names_filter is not None:
                raise TypeError("Pass only one names filter.")
            names_filter = cast(NamesFilter, cache_or_names_filter)
        if names_filter is None:
            names_filter = names
        elif names is not None:
            raise TypeError("Pass only one of `names_filter` or `names`.")
        if names_filter is None:
            raise TypeError("cache_some() missing required argument: 'names_filter' or 'names'")
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

    def _enable_hook_with_name(
        self,
        name: str,
        hook: Callable[..., Any],
        dir: Literal["fwd", "bwd"],
    ) -> LensHandle:
        """TransformerLens-compatible internal helper for enabling one hook."""
        return self.check_and_add_hook(name, hook, dir=dir, level=self.context_level)

    def _enable_hooks_for_points(
        self,
        hook_points: Iterable[tuple[str, HookPoint]],
        enabled: Callable[[str], bool],
        hook: Callable[..., Any],
        dir: Literal["fwd", "bwd"],
    ) -> list[LensHandle]:
        """TransformerLens-compatible internal helper for enabling matched hooks."""
        handles: list[LensHandle] = []
        for hook_name, hook_point in hook_points:
            if enabled(hook_name):
                handles.append(
                    self.check_and_add_hook(
                        hook_point,
                        hook_name,
                        hook,
                        dir=dir,
                        level=self.context_level,
                    )
                )
        return handles

    def _enable_hook(
        self,
        name: NamesFilter,
        hook: Callable[..., Any],
        dir: Literal["fwd", "bwd"],
    ) -> list[LensHandle]:
        """TransformerLens-compatible internal hook enabling helper."""
        if isinstance(name, str):
            return [self._enable_hook_with_name(name=name, hook=hook, dir=dir)]
        if callable(name):
            return self._enable_hooks_for_points(
                self.hook_dict.items(),
                enabled=name,
                hook=hook,
                dir=dir,
            )
        handles: list[LensHandle] = []
        for hook_name in self._matching_hook_names(name):
            handles.append(self._enable_hook_with_name(name=hook_name, hook=hook, dir=dir))
        return handles

    @contextmanager
    def hooks(
        self,
        fwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        bwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        *,
        prepend: bool = False,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
    ) -> Iterator[HookedRoot]:
        """Temporarily add forward/backward hooks."""
        level: int | None = None
        try:
            self.context_level += 1
            self._next_hook_level += 1
            level = self._next_hook_level
            self._add_hook_specs(fwd_hooks, dir="fwd", level=level, prepend=prepend)
            self._add_hook_specs(bwd_hooks, dir="bwd", level=level, prepend=prepend)
            yield self
        finally:
            if reset_hooks_end and level is not None:
                self.reset_hooks(
                    clear_contexts=clear_contexts,
                    including_permanent=False,
                    level=level,
                )
            self.context_level -= 1

    def run_with_hooks(
        self,
        run_fn_or_input: Any = None,
        *args: Any,
        fwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        bwd_hooks: Iterable[tuple[NamesFilter, Callable[..., Any]]] = (),
        prepend: bool = False,
        reset_hooks_end: bool = True,
        clear_contexts: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Run an arbitrary callable with temporary hooks registered."""
        run_fn, run_args = self._resolve_run_callable(run_fn_or_input, args)
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
            prepend=prepend,
            reset_hooks_end=reset_hooks_end,
            clear_contexts=clear_contexts,
        ):
            return run_fn(*run_args, **kwargs)

    def run_with_cache(
        self,
        run_fn_or_input: Any = None,
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
        cache: ActivationCache | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> tuple[Any, ActivationCache]:
        """Run a callable while temporarily caching matching hook-point activations."""
        run_fn, run_args = self._resolve_run_callable(run_fn_or_input, args)
        external_cache = _coerce_activation_cache(
            cache,
            model=self,
            has_batch_dim=not remove_batch_dim,
        )
        previous_is_caching = self.is_caching
        previous_cache_model = external_cache.model
        previous_has_batch_dim = external_cache.has_batch_dim
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
            output = run_fn(*run_args, **kwargs)
            if incl_bwd:
                _backward_scalar_output(output)
        finally:
            if reset_hooks_end or not install_complete:
                for handle in reversed(handles):
                    handle.remove()
            if reset_hooks_end:
                self.is_caching = previous_is_caching
            if reset_hooks_end and clear_contexts:
                self.clear_contexts()
            if not install_complete:
                self.is_caching = previous_is_caching
                activation_cache.model = previous_cache_model
                activation_cache.has_batch_dim = previous_has_batch_dim
        if remove_batch_dim:
            activation_cache = activation_cache.remove_batch_dim()
        return output, activation_cache

    def _resolve_run_callable(
        self,
        run_fn_or_input: Any,
        args: tuple[Any, ...],
    ) -> tuple[Callable[..., Any], tuple[Any, ...]]:
        if callable(run_fn_or_input):
            return run_fn_or_input, args
        forward = getattr(self, "forward", None)
        if callable(forward):
            if run_fn_or_input is None and not args:
                return forward, ()
            if run_fn_or_input is None:
                return forward, args
            return forward, (run_fn_or_input, *args)
        if run_fn_or_input is None:
            raise TypeError(
                "run_with_hooks/run_with_cache require a callable or a `forward` method."
            )
        raise TypeError(
            "First argument must be callable unless this HookedRoot implements `forward`."
        )

    def _add_hook_specs(
        self,
        hook_specs: Iterable[tuple[NamesFilter, Callable[..., Any]]],
        *,
        dir: Literal["fwd", "bwd"],
        level: int | None,
        prepend: bool = False,
    ) -> list[LensHandle]:
        handles: list[LensHandle] = []
        try:
            for names_filter, hook_fn in hook_specs:
                if isinstance(names_filter, str):
                    handles.append(
                        self.check_and_add_hook(
                            str(names_filter),
                            hook_fn,
                            dir=dir,
                            level=level,
                            prepend=prepend,
                        )
                    )
                    continue
                matched = self.add_hook(
                    names_filter,
                    hook_fn,
                    dir=dir,
                    level=level,
                    prepend=prepend,
                )
                handles.extend(matched)
        except Exception:
            for handle in reversed(handles):
                handle.remove()
            raise
        return handles

    def _resolve_hook_name(self, name: str) -> str | None:
        if name in self.hook_dict:
            return name
        matches = [
            hook_name for hook_name in self.hook_dict if matches_names_filter(hook_name, name)
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    def _matching_hook_names(self, names_filter: NamesFilter) -> list[str]:
        if names_filter is None or callable(names_filter):
            return [name for name in self.hook_dict if matches_names_filter(name, names_filter)]
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

    def _has_active_cache_hooks(self) -> bool:
        return any(
            not handle.removed and handle.is_cache
            for hook_point in self.hook_points()
            for _hook_fn, handle in hook_point._matching_hook_records("both")
        )

    def _iter_named_hook_points(self) -> Iterator[tuple[str, HookPoint]]:
        seen: set[int] = set()

        def visit(prefix: str, value: Any) -> Iterator[tuple[str, HookPoint]]:
            value_id = id(value)
            if value_id in seen:
                return
            seen.add(value_id)
            if isinstance(value, HookPoint):
                yield prefix, value
                return
            if isinstance(value, HookedRoot):
                return
            if isinstance(value, Mapping):
                for key, item in value.items():
                    name = f"{prefix}.{key}" if prefix else str(key)
                    yield from visit(name, item)
                return
            if isinstance(value, str | bytes | int | float | bool | type(None)):
                return
            if isinstance(value, list | tuple):
                for index, item in enumerate(value):
                    name = f"{prefix}.{index}" if prefix else str(index)
                    yield from visit(name, item)
                return
            if not hasattr(value, "__dict__"):
                return
            for attr_name, item in vars(value).items():
                if attr_name.startswith("_") or attr_name in {"hook_dict", "mod_dict"}:
                    continue
                name = f"{prefix}.{attr_name}" if prefix else attr_name
                yield from visit(name, item)

        for attr_name, value in vars(self).items():
            if attr_name.startswith("_") or attr_name in {"hook_dict", "mod_dict"}:
                continue
            yield from visit(attr_name, value)


def _coerce_activation_cache(
    cache: ActivationCache | dict[str, Any] | None,
    *,
    model: Any,
    has_batch_dim: bool,
) -> ActivationCache:
    if cache is None:
        return ActivationCache(model=model, has_batch_dim=has_batch_dim)
    if isinstance(cache, ActivationCache):
        return cache
    return ActivationCache(cache, model=model, has_batch_dim=has_batch_dim, canonicalize=False)


def _looks_like_external_cache(value: Any) -> bool:
    return isinstance(value, ActivationCache) or isinstance(value, dict)


def _backward_scalar_output(output: Any) -> None:
    target = _scalar_backward_target(output)
    if target is None:
        raise ValueError("incl_bwd=True requires the run function to return a scalar loss.")
    backward = getattr(target, "backward", None)
    if callable(backward):
        backward()
        return
    raise ValueError("incl_bwd=True requires a differentiable scalar output with backward().")


def _scalar_backward_target(output: Any) -> Any | None:
    if _is_differentiable_scalar(output):
        return output
    if isinstance(output, Mapping):
        loss = output.get("loss")
        if _is_differentiable_scalar(loss):
            return loss
        return None
    if isinstance(output, tuple | list):
        for value in reversed(output):
            if _is_differentiable_scalar(value):
                return value
    return None


def _is_differentiable_scalar(value: Any) -> bool:
    if value is None or not _looks_like_scalar(value):
        return False
    return callable(getattr(value, "backward", None))


def _looks_like_scalar(value: Any) -> bool:
    if isinstance(value, str | bytes | Mapping | tuple | list):
        return False
    ndim = getattr(value, "ndim", None)
    if ndim is not None:
        try:
            return int(ndim) == 0
        except (TypeError, ValueError):
            pass
    dim = getattr(value, "dim", None)
    if callable(dim):
        try:
            return int(cast(Any, dim())) == 0
        except (TypeError, ValueError):
            pass
    shape = getattr(value, "shape", None)
    if shape is not None:
        try:
            return len(shape) == 0
        except TypeError:
            pass
    return isinstance(value, int | float | complex | bool)
