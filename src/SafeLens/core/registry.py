"""Decorator-based registries for pluggable SafeLens methods."""

from __future__ import annotations

from collections.abc import Callable
from difflib import get_close_matches
from typing import Any, TypeVar

from SafeLens.core.base import BaseAttributor, BaseMonitor, BaseProbe

ProbeT = TypeVar("ProbeT", bound=type[BaseProbe])
MonitorT = TypeVar("MonitorT", bound=type[BaseMonitor])
AttributorT = TypeVar("AttributorT", bound=type[BaseAttributor])

_PROBE_REGISTRY: dict[str, type[BaseProbe]] = {}
_MONITOR_REGISTRY: dict[str, type[BaseMonitor]] = {}
_ATTRIBUTOR_REGISTRY: dict[str, type[BaseAttributor]] = {}


class RegistryError(KeyError):
    """Raised when a method registry lookup or registration fails."""


def load_builtin_methods() -> None:
    """Import built-in plugins so their registration decorators run."""
    import SafeLens.attribution.captum  # noqa: F401
    import SafeLens.attribution.dummy  # noqa: F401
    import SafeLens.attribution.safety_heads  # noqa: F401
    import SafeLens.monitors.dummy  # noqa: F401
    import SafeLens.probes.dummy  # noqa: F401


def _register(
    registry: dict[str, type[Any]],
    kind: str,
    name: str,
    replace: bool = False,
) -> Callable[[type[Any]], type[Any]]:
    if not name or not name.strip():
        raise RegistryError(f"{kind} name must be a non-empty string")

    normalized = name.strip()

    def decorator(cls: type[Any]) -> type[Any]:
        if normalized in registry and not replace:
            raise RegistryError(f"{kind} '{normalized}' is already registered")
        registry[normalized] = cls
        cls.name = normalized
        return cls

    return decorator


def register_probe(name: str, replace: bool = False) -> Callable[[ProbeT], ProbeT]:
    """Register a probe class by name."""
    return _register(_PROBE_REGISTRY, "probe", name, replace)  # type: ignore[return-value]


def register_monitor(name: str, replace: bool = False) -> Callable[[MonitorT], MonitorT]:
    """Register a monitor class by name."""
    return _register(_MONITOR_REGISTRY, "monitor", name, replace)  # type: ignore[return-value]


def register_attributor(name: str, replace: bool = False) -> Callable[[AttributorT], AttributorT]:
    """Register an attributor class by name."""
    return _register(_ATTRIBUTOR_REGISTRY, "attributor", name, replace)  # type: ignore[return-value]


def get_probe(name: str) -> type[BaseProbe]:
    """Return a registered probe class."""
    try:
        return _PROBE_REGISTRY[name]
    except KeyError as exc:
        raise RegistryError(_unknown_name_message("probe", name, list_probes())) from exc


def get_monitor(name: str) -> type[BaseMonitor]:
    """Return a registered monitor class."""
    try:
        return _MONITOR_REGISTRY[name]
    except KeyError as exc:
        raise RegistryError(_unknown_name_message("monitor", name, list_monitors())) from exc


def get_attributor(name: str) -> type[BaseAttributor]:
    """Return a registered attributor class."""
    try:
        return _ATTRIBUTOR_REGISTRY[name]
    except KeyError as exc:
        raise RegistryError(_unknown_name_message("attributor", name, list_attributors())) from exc


def create_probe(name: str, config: dict[str, Any] | None = None) -> BaseProbe:
    """Instantiate a registered probe."""
    return get_probe(name)(config=config)


def create_monitor(name: str, config: dict[str, Any] | None = None) -> BaseMonitor:
    """Instantiate a registered monitor."""
    return get_monitor(name)(config=config)


def create_attributor(name: str, config: dict[str, Any] | None = None) -> BaseAttributor:
    """Instantiate a registered attributor."""
    return get_attributor(name)(config=config)


def list_probes() -> list[str]:
    """List registered probe names."""
    return sorted(_PROBE_REGISTRY)


def list_monitors() -> list[str]:
    """List registered monitor names."""
    return sorted(_MONITOR_REGISTRY)


def list_attributors() -> list[str]:
    """List registered attributor names."""
    return sorted(_ATTRIBUTOR_REGISTRY)


def _unknown_name_message(kind: str, name: str, available: list[str]) -> str:
    if not available:
        return (
            f"Unknown {kind} {name!r}. No {kind}s are registered. "
            "Import the plugin module or call load_builtin_methods() for built-ins."
        )
    suggestion = get_close_matches(name, available, n=1)
    hint = f" Did you mean {suggestion[0]!r}?" if suggestion else ""
    return f"Unknown {kind} {name!r}. Available {kind}s: {available}.{hint}"
