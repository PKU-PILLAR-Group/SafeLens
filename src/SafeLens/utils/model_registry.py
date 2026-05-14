"""Model adapter registry, capability declarations, and cache planning."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from SafeLens.core.base import ModelLoadConfig, ModelWrapper

AdapterBuilder = Callable[[ModelLoadConfig], ModelWrapper]
AdapterInspector = Callable[[str, ModelLoadConfig | None], dict[str, Any]]
ModelNameMatcher = Callable[[str], bool]

DEFAULT_MODEL_CACHE_ROOT = ".cache/safelens/models"


@dataclass(frozen=True)
class ModelDownloadPlan:
    """Resolved loading and cache plan for one model backend."""

    source: str
    model_name: str
    pretrained_path: str
    cache_dir: str | None = None
    local_dir: str | None = None
    revision: str | None = None
    uses_network: bool = False
    provider: str = "local"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "source": self.source,
            "model_name": self.model_name,
            "pretrained_path": self.pretrained_path,
            "cache_dir": self.cache_dir,
            "local_dir": self.local_dir,
            "revision": self.revision,
            "uses_network": self.uses_network,
            "provider": self.provider,
        }


@dataclass(frozen=True)
class ModelAdapterCapabilities:
    """Static capabilities declared by a model adapter."""

    supported_hooks: tuple[str, ...] = ()
    supported_patches: tuple[str, ...] = ()
    supports_attention_pattern: bool = False
    supports_attention_scores: bool = False
    supports_local_path: bool = False
    supports_remote_download: bool = False
    cache_policy: str = "provider-default"
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "supported_hooks": list(self.supported_hooks),
            "supported_patches": list(self.supported_patches),
            "supports_attention_pattern": self.supports_attention_pattern,
            "supports_attention_scores": self.supports_attention_scores,
            "supports_local_path": self.supports_local_path,
            "supports_remote_download": self.supports_remote_download,
            "cache_policy": self.cache_policy,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ModelAdapterSpec:
    """Registered model adapter entry."""

    name: str
    display_name: str
    aliases: tuple[str, ...]
    description: str
    capabilities: ModelAdapterCapabilities
    build: AdapterBuilder
    inspect: AdapterInspector
    matches_model_name: ModelNameMatcher = lambda _model_name: False
    dependencies: tuple[str, ...] = ()
    model_name_patterns: tuple[str, ...] = ()
    priority: int = 0

    @property
    def all_names(self) -> tuple[str, ...]:
        """Return primary name and aliases."""
        return (self.name, *self.aliases)

    def to_dict(self) -> dict[str, Any]:
        """Return public metadata for CLI and docs."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "aliases": list(self.aliases),
            "description": self.description,
            "dependencies": list(self.dependencies),
            "model_name_patterns": list(self.model_name_patterns),
            "capabilities": self.capabilities.to_dict(),
        }


class ModelAdapterRegistry:
    """Registry for model adapters keyed by `model.source`."""

    def __init__(self) -> None:
        self._adapters: dict[str, ModelAdapterSpec] = {}
        self._aliases: dict[str, str] = {}

    def register(self, spec: ModelAdapterSpec, *, replace: bool = False) -> None:
        """Register one model adapter spec."""
        names = tuple(_normalize_source(name) for name in spec.all_names)
        for name in names:
            if not replace and (name in self._adapters or name in self._aliases):
                raise ValueError(f"Model adapter source {name!r} is already registered.")
        self._adapters[_normalize_source(spec.name)] = spec
        for alias in names[1:]:
            self._aliases[alias] = _normalize_source(spec.name)

    def get(self, source: str) -> ModelAdapterSpec:
        """Return the adapter for a `model.source` value."""
        normalized = _normalize_source(source)
        primary = self._aliases.get(normalized, normalized)
        try:
            return self._adapters[primary]
        except KeyError as exc:
            available = ", ".join(self.source_names())
            raise KeyError(
                f"Unsupported model source {source!r}. Available sources: {available}."
            ) from exc

    def source_names(self) -> list[str]:
        """Return primary source names and aliases."""
        return sorted({*self._adapters, *self._aliases})

    def list_supported(self) -> list[dict[str, Any]]:
        """Return supported adapter metadata."""
        return [
            spec.to_dict() for spec in sorted(self._adapters.values(), key=lambda item: item.name)
        ]

    def create(self, config: ModelLoadConfig) -> ModelWrapper:
        """Create a wrapper from a validated model config."""
        return self.get(config.source).build(config)

    def inspect_model(
        self,
        model_name: str,
        *,
        source: str | None = None,
        config: ModelLoadConfig | None = None,
    ) -> dict[str, Any]:
        """Inspect static adapter support for a model name without loading weights."""
        if source is not None:
            spec = self.get(source)
        else:
            spec = self._best_match(model_name)
        effective_config = config or ModelLoadConfig(source=spec.name, name=model_name)
        payload = spec.inspect(model_name, effective_config)
        payload.setdefault("model", model_name)
        payload.setdefault("source", spec.name)
        payload.setdefault("adapter", spec.to_dict())
        payload.setdefault("download_plan", resolve_model_download_plan(effective_config).to_dict())
        return payload

    def _best_match(self, model_name: str) -> ModelAdapterSpec:
        matches = [spec for spec in self._adapters.values() if spec.matches_model_name(model_name)]
        if not matches:
            if _looks_like_local_path(model_name):
                return self.get("local")
            return self.get("huggingface")
        return sorted(matches, key=lambda item: item.priority, reverse=True)[0]


BUILTIN_MODEL_ADAPTER_REGISTRY = ModelAdapterRegistry()


def get_model_adapter_registry() -> ModelAdapterRegistry:
    """Return the built-in model adapter registry."""
    return BUILTIN_MODEL_ADAPTER_REGISTRY


def resolve_model_download_plan(config: ModelLoadConfig) -> ModelDownloadPlan:
    """Resolve a unified provider/cache plan without downloading the model."""
    source = _normalize_source(config.source)
    if source in {"dummy", "mock", "none"} or config.name.lower() in {"dummy", "mock", "none"}:
        return ModelDownloadPlan(
            source="dummy",
            model_name=config.name,
            pretrained_path=config.name,
            uses_network=False,
            provider="memory",
        )
    if source == "local":
        pretrained_path = str(Path(config.local_dir or config.name).expanduser())
        return ModelDownloadPlan(
            source="local",
            model_name=config.name,
            pretrained_path=pretrained_path,
            local_dir=pretrained_path,
            revision=config.revision,
            uses_network=False,
            provider="local",
        )
    if source in {"huggingface", "hf", "qwen3", "qwen3_dense", "qwen3-dense"}:
        primary_source = "qwen3_dense" if source in {"qwen3", "qwen3-dense"} else source
        provider_cache = _cache_dir(config, "huggingface")
        return ModelDownloadPlan(
            source=primary_source,
            model_name=config.name,
            pretrained_path=config.name,
            cache_dir=provider_cache,
            revision=config.revision,
            uses_network=True,
            provider="huggingface",
        )
    if source in {"transformer_lens", "transformerlens", "tl", "hooked_transformer"}:
        from SafeLens.utils.transformer_lens_support import (
            resolve_transformer_lens_compatible_model_name,
        )

        if config.local_dir is not None or _looks_like_local_path(config.name):
            pretrained_path = str(Path(config.local_dir or config.name).expanduser())
            return ModelDownloadPlan(
                source="transformer_lens",
                model_name=config.name,
                pretrained_path=pretrained_path,
                local_dir=pretrained_path,
                revision=config.revision,
                uses_network=False,
                provider="local",
            )
        return ModelDownloadPlan(
            source="transformer_lens",
            model_name=config.name,
            pretrained_path=resolve_transformer_lens_compatible_model_name(config.name),
            cache_dir=_cache_dir(config, "transformer_lens_compatible"),
            revision=config.revision,
            uses_network=True,
            provider="huggingface",
        )
    if source in {"modelscope", "ms"}:
        return ModelDownloadPlan(
            source="modelscope",
            model_name=config.name,
            pretrained_path=config.local_dir or config.name,
            cache_dir=_cache_dir(config, "modelscope"),
            local_dir=config.local_dir,
            revision=config.revision,
            uses_network=True,
            provider="modelscope",
        )
    return ModelDownloadPlan(
        source=source,
        model_name=config.name,
        pretrained_path=config.name,
        cache_dir=config.cache_dir,
        local_dir=config.local_dir,
        revision=config.revision,
        uses_network=True,
        provider=source,
    )


def _cache_dir(config: ModelLoadConfig, provider: str) -> str:
    return config.cache_dir or str(Path(DEFAULT_MODEL_CACHE_ROOT) / provider)


def _normalize_source(source: str) -> str:
    return source.strip().lower().replace("-", "_")


def _looks_like_local_path(value: str) -> bool:
    path = Path(value).expanduser()
    return (
        value.startswith((".", "/", "~"))
        or path.exists()
        or any(separator in value for separator in ("/", "\\"))
        and not _looks_like_remote_model_id(value)
    )


def _looks_like_remote_model_id(value: str) -> bool:
    return bool(value and not value.startswith((".", "/", "~")) and value.count("/") == 1)
