"""Shared contracts for SafeProbe methods, reports, and pipelines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

Batch = Mapping[str, Any]
HookFn = Callable[..., Any]
LayerRef = int | str


class SerializableModel(BaseModel):
    """Pydantic base model with a stable dictionary export helper."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return self.model_dump(mode="json")


class ProbeResult(SerializableModel):
    """Result returned by an endogenous safety probe."""

    risk_score: float = Field(ge=0.0, le=1.0)
    critical_layers: list[int] = Field(default_factory=list)
    intervention_applied: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class MonitoringSignal(SerializableModel):
    """Per-step safety signal emitted by a monitor."""

    name: str
    risk_score: float = Field(ge=0.0, le=1.0)
    triggered: bool = False
    risk_category: list[str] = Field(default_factory=list)
    evidence_tokens: list[int] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class TokenAttribution(SerializableModel):
    """Token-level attribution evidence."""

    token_index: int = Field(ge=0)
    score: float
    token_text: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttributionResult(SerializableModel):
    """Attribution output for input or training-data influence."""

    method: str
    attribution_score: float = Field(ge=0.0, le=1.0)
    tokens: list[TokenAttribution] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class SafetyReport(SerializableModel):
    """Standard report shape consumed by downstream adapters such as FlagSafe."""

    sample_id: str | None = None
    flagged: bool = False
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_category: list[str] = Field(default_factory=list)
    evidence_tokens: list[int] = Field(default_factory=list)
    attribution_score: float | None = Field(default=None, ge=0.0, le=1.0)
    probe_results: list[ProbeResult] = Field(default_factory=list)
    monitoring_signals: list[MonitoringSignal] = Field(default_factory=list)
    attributions: list[AttributionResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunReport(SerializableModel):
    """Aggregate report written by a pipeline run."""

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reports: list[SafetyReport] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class BaseMethodConfig(SerializableModel):
    """Base configuration class for pluggable methods."""

    enabled: bool = True
    params: dict[str, Any] = Field(default_factory=dict)


class MethodSpec(SerializableModel):
    """Name and config payload for a registered method."""

    name: str
    config: dict[str, Any] = Field(default_factory=dict)


class ModelLoadConfig(SerializableModel):
    """Configuration for model wrapper construction."""

    name: str = "dummy"
    source: str = "huggingface"
    dtype: str = "float32"
    device: str | None = None
    revision: str | None = None
    cache_dir: str | None = None
    local_dir: str | None = None
    trust_remote_code: bool = False
    load_kwargs: dict[str, Any] = Field(default_factory=dict)
    tokenizer_kwargs: dict[str, Any] = Field(default_factory=dict)
    modelscope_kwargs: dict[str, Any] = Field(default_factory=dict)


class PipelineSectionConfig(SerializableModel):
    """Registered methods and runner behavior."""

    probes: list[MethodSpec] = Field(default_factory=list)
    monitors: list[MethodSpec] = Field(default_factory=list)
    attributors: list[MethodSpec] = Field(default_factory=list)
    risk_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class OutputConfig(SerializableModel):
    """Output configuration for generated reports."""

    report_path: str = "./safety_scan.json"


class PipelineConfig(SerializableModel):
    """Top-level YAML config for `safeprobe run`."""

    model: ModelLoadConfig = Field(default_factory=ModelLoadConfig)
    pipeline: PipelineSectionConfig = Field(default_factory=PipelineSectionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    dataset: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("dataset")
    @classmethod
    def validate_dataset(cls, value: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return [dict(item) for item in value]


class ModelWrapper(ABC):
    """Abstract model interface used by probes, monitors, and attributors."""

    @abstractmethod
    def load_model(self) -> Any:
        """Load and return the underlying model object."""

    @abstractmethod
    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        """Register a forward hook on a target layer."""

    @abstractmethod
    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        """Run inference and optionally return cached activations for selected layers."""

    @abstractmethod
    def generate(self, prompt: str, **generation_kwargs: Any) -> Any:
        """Generate text or model outputs from a prompt."""

    @abstractmethod
    def remove_hooks(self) -> None:
        """Remove all active hooks managed by this wrapper."""


class BaseProbe(ABC):
    """Base class for endogenous safety probes."""

    name: ClassVar[str] = ""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})

    @abstractmethod
    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        """Register hooks on target layers."""

    @abstractmethod
    def detect(self, batch: Batch) -> ProbeResult:
        """Compute safety risk from the current batch and cached state."""

    @abstractmethod
    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        """Apply an activation-space intervention."""

    @abstractmethod
    def detach(self) -> None:
        """Remove probe hooks and clear runtime state."""


class BaseMonitor(ABC):
    """Base class for generation-time safety monitors."""

    name: ClassVar[str] = ""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})

    @abstractmethod
    def start_monitoring(self, model: ModelWrapper) -> None:
        """Initialize monitor state for a model run."""

    @abstractmethod
    def step(self, batch: Batch, model_output: Any = None) -> MonitoringSignal:
        """Inspect one batch or generation step and emit a safety signal."""

    @abstractmethod
    def report(self) -> SafetyReport:
        """Return the monitor's aggregate safety report."""


class BaseAttributor(ABC):
    """Base class for input and training-data attribution methods."""

    name: ClassVar[str] = ""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})

    @abstractmethod
    def attribute_training(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        """Estimate influential training examples or sources for the batch."""

    @abstractmethod
    def attribute_input(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        """Estimate input-token contribution to the observed risk."""
