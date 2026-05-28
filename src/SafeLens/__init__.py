"""SafeLens package."""

from SafeLens.core.base import (
    AttributionResult,
    BaseAttributor,
    BaseMethodConfig,
    BaseMonitor,
    BaseProbe,
    MethodSpec,
    ModelLoadConfig,
    ModelWrapper,
    MonitoringSignal,
    OutputConfig,
    PipelineConfig,
    PipelineSectionConfig,
    ProbeResult,
    RunReport,
    SafetyReport,
    TokenAttribution,
)
from SafeLens.core.analysis import (
    attention_pattern_score,
    induction_attention_score,
    previous_token_attention_score,
)
from SafeLens.core.factored_matrix import FactoredMatrix, composition_scores
from SafeLens.core.hooked_root import HookedRoot
from SafeLens.core.hooks import ActivationCache, HookPoint
from SafeLens.core.kv_cache import KeyValueCache, KeyValueCacheEntry
from SafeLens.core.patching import PatchResult, PatchSpec

__all__ = [
    "AttributionResult",
    "ActivationCache",
    "attention_pattern_score",
    "BaseAttributor",
    "BaseMethodConfig",
    "BaseMonitor",
    "BaseProbe",
    "FactoredMatrix",
    "composition_scores",
    "HookPoint",
    "HookedRoot",
    "induction_attention_score",
    "KeyValueCache",
    "KeyValueCacheEntry",
    "MethodSpec",
    "ModelLoadConfig",
    "ModelWrapper",
    "MonitoringSignal",
    "OutputConfig",
    "PipelineConfig",
    "PipelineSectionConfig",
    "PatchResult",
    "PatchSpec",
    "ProbeResult",
    "previous_token_attention_score",
    "RunReport",
    "SafetyReport",
    "TokenAttribution",
]
