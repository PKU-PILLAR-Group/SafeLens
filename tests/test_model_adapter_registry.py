from __future__ import annotations

from SafeLens.core.base import ModelLoadConfig, ModelWrapper
from SafeLens.utils import (
    HuggingFaceModelWrapper,
    LocalModelWrapper,
    ModelScopeModelWrapper,
    Qwen3DenseModelWrapper,
    build_model_wrapper,
    get_model_adapter_registry,
    resolve_model_download_plan,
)


def test_model_adapter_registry_lists_capabilities() -> None:
    registry = get_model_adapter_registry()
    adapters = {item["name"]: item for item in registry.list_supported()}

    assert {"dummy", "huggingface", "local", "modelscope", "qwen3_dense"}.issubset(adapters)
    assert "q" in adapters["qwen3_dense"]["capabilities"]["supported_hooks"]
    assert adapters["qwen3_dense"]["capabilities"]["supports_attention_pattern"] is False
    assert adapters["local"]["capabilities"]["supports_remote_download"] is False


def test_model_adapter_registry_inspects_qwen3_dense_without_loading() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("Qwen/Qwen3-8B")

    assert payload["source"] == "qwen3_dense"
    assert payload["supported"] is True
    assert payload["parameter_size_b"] == 8.0
    assert payload["download_plan"]["provider"] == "huggingface"


def test_model_adapter_registry_reports_unsupported_qwen3_dense_size() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("Qwen/Qwen3-72B")

    assert payload["source"] == "qwen3_dense"
    assert payload["supported"] is False
    assert "Only dense models" in payload["errors"][0]


def test_unified_download_plan_defaults_cache_dirs() -> None:
    hf_plan = resolve_model_download_plan(ModelLoadConfig(source="huggingface", name="org/model"))
    ms_plan = resolve_model_download_plan(ModelLoadConfig(source="modelscope", name="org/model"))
    local_plan = resolve_model_download_plan(
        ModelLoadConfig(source="local", name="./models/local-causal-lm")
    )

    assert hf_plan.cache_dir == ".cache/safelens/models/huggingface"
    assert hf_plan.uses_network is True
    assert ms_plan.cache_dir == ".cache/safelens/models/modelscope"
    assert ms_plan.uses_network is True
    assert local_plan.local_dir == "models/local-causal-lm"
    assert local_plan.uses_network is False


def test_build_model_wrapper_uses_registered_adapters() -> None:
    assert isinstance(
        build_model_wrapper(ModelLoadConfig(source="huggingface", name="org/model")),
        HuggingFaceModelWrapper,
    )
    assert isinstance(
        build_model_wrapper(ModelLoadConfig(source="modelscope", name="org/model")),
        ModelScopeModelWrapper,
    )
    assert isinstance(
        build_model_wrapper(ModelLoadConfig(source="qwen3_dense", name="Qwen/Qwen3-8B")),
        Qwen3DenseModelWrapper,
    )
    assert isinstance(
        build_model_wrapper(ModelLoadConfig(source="local", name="./models/local-causal-lm")),
        LocalModelWrapper,
    )


def test_all_registered_adapters_satisfy_model_wrapper_contract() -> None:
    registry = get_model_adapter_registry()
    configs = {
        "dummy": ModelLoadConfig(source="dummy", name="dummy"),
        "huggingface": ModelLoadConfig(source="huggingface", name="org/model"),
        "local": ModelLoadConfig(source="local", name="./models/local-causal-lm"),
        "modelscope": ModelLoadConfig(source="modelscope", name="org/model"),
        "qwen3_dense": ModelLoadConfig(source="qwen3_dense", name="Qwen/Qwen3-8B"),
    }

    for source, config in configs.items():
        wrapper = registry.create(config)
        assert isinstance(wrapper, ModelWrapper), source
        assert callable(wrapper.load_model)
        assert callable(wrapper.add_hook)
        assert callable(wrapper.run_with_cache)
        assert callable(wrapper.generate)
        assert callable(wrapper.remove_hooks)
