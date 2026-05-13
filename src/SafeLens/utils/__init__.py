"""Utility helpers."""

from SafeLens.utils.model_registry import (
    ModelAdapterCapabilities,
    ModelAdapterRegistry,
    ModelAdapterSpec,
    ModelDownloadPlan,
    get_model_adapter_registry,
    resolve_model_download_plan,
)
from SafeLens.utils.model_wrapper import (
    DummyModelWrapper,
    HuggingFaceModelWrapper,
    LocalModelWrapper,
    ModelScopeModelWrapper,
    Qwen3DenseModelWrapper,
    build_model_wrapper,
    is_supported_qwen3_dense_model_name,
    parse_qwen3_component_ref,
    qwen3_dense_size_billion,
    qwen3_hook_name_examples,
    qwen3_supported_hook_components,
    register_builtin_model_adapters,
    validate_qwen3_dense_model_name,
    validate_qwen3_hook_ref,
)

__all__ = [
    "DummyModelWrapper",
    "HuggingFaceModelWrapper",
    "LocalModelWrapper",
    "ModelAdapterCapabilities",
    "ModelAdapterRegistry",
    "ModelAdapterSpec",
    "ModelDownloadPlan",
    "ModelScopeModelWrapper",
    "Qwen3DenseModelWrapper",
    "build_model_wrapper",
    "get_model_adapter_registry",
    "is_supported_qwen3_dense_model_name",
    "parse_qwen3_component_ref",
    "qwen3_hook_name_examples",
    "qwen3_dense_size_billion",
    "qwen3_supported_hook_components",
    "register_builtin_model_adapters",
    "resolve_model_download_plan",
    "validate_qwen3_hook_ref",
    "validate_qwen3_dense_model_name",
]
