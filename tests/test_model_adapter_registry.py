from __future__ import annotations

import pytest

from SafeLens.core.base import ModelLoadConfig, ModelWrapper
from SafeLens.utils import (
    HuggingFaceModelWrapper,
    LocalModelWrapper,
    ModelScopeModelWrapper,
    Qwen3DenseModelWrapper,
    TransformerLensCompatibleModelWrapper,
    build_model_wrapper,
    get_model_adapter_registry,
    is_transformer_lens_supported_model_name,
    resolve_model_download_plan,
)


def test_model_adapter_registry_lists_capabilities() -> None:
    registry = get_model_adapter_registry()
    adapters = {item["name"]: item for item in registry.list_supported()}

    assert {
        "dummy",
        "huggingface",
        "local",
        "modelscope",
        "qwen3_dense",
        "transformer_lens",
    }.issubset(adapters)
    assert "q" in adapters["qwen3_dense"]["capabilities"]["supported_hooks"]
    assert "result" in adapters["qwen3_dense"]["capabilities"]["supported_patches"]
    assert adapters["qwen3_dense"]["capabilities"]["supports_attention_pattern"] is True
    assert adapters["qwen3_dense"]["capabilities"]["supports_attention_scores"] is True
    assert "result" in adapters["transformer_lens"]["capabilities"]["supported_patches"]
    assert adapters["transformer_lens"]["capabilities"]["supports_attention_pattern"] is True
    assert adapters["transformer_lens"]["capabilities"]["supports_attention_scores"] is True
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


def test_model_adapter_registry_inspects_transformerlens_models_without_loading() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("gpt2")

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["download_plan"]["provider"] == "huggingface"
    assert payload["resolved_pretrained_model"] == "gpt2"
    assert payload["official_model_count"] >= 150
    assert "result" in payload["bridge_components"]


def test_transformerlens_supports_official_names_and_common_aliases() -> None:
    assert is_transformer_lens_supported_model_name("meta-llama/Llama-3.1-8B")
    assert is_transformer_lens_supported_model_name("gpt2-small")
    assert is_transformer_lens_supported_model_name("bert-base-uncased")


def test_unified_download_plan_defaults_cache_dirs() -> None:
    hf_plan = resolve_model_download_plan(ModelLoadConfig(source="huggingface", name="org/model"))
    ms_plan = resolve_model_download_plan(ModelLoadConfig(source="modelscope", name="org/model"))
    tl_plan = resolve_model_download_plan(ModelLoadConfig(source="transformer_lens", name="gpt2"))
    tl_local_plan = resolve_model_download_plan(
        ModelLoadConfig(source="transformer_lens", name="gpt2", local_dir="./models/gpt2")
    )
    local_plan = resolve_model_download_plan(
        ModelLoadConfig(source="local", name="./models/local-causal-lm")
    )

    assert hf_plan.cache_dir == ".cache/safelens/models/huggingface"
    assert hf_plan.uses_network is True
    assert ms_plan.cache_dir == ".cache/safelens/models/modelscope"
    assert ms_plan.uses_network is True
    assert tl_plan.cache_dir == ".cache/safelens/models/transformer_lens_compatible"
    assert tl_plan.uses_network is True
    assert tl_plan.provider == "huggingface"
    assert tl_local_plan.local_dir == "models/gpt2"
    assert tl_local_plan.uses_network is False
    assert tl_local_plan.provider == "local"
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
        build_model_wrapper(ModelLoadConfig(source="transformer_lens", name="gpt2")),
        TransformerLensCompatibleModelWrapper,
    )
    assert isinstance(
        build_model_wrapper(ModelLoadConfig(source="local", name="./models/local-causal-lm")),
        LocalModelWrapper,
    )


def test_transformerlens_wrapper_rejects_unsupported_model_before_auto_loading() -> None:
    wrapper = build_model_wrapper(
        ModelLoadConfig(
            source="transformer_lens",
            name="hf-internal-testing/tiny-random-CLIPModel",
        )
    )

    with pytest.raises(ValueError, match="not in SafeLens' vendored TransformerLens-compatible"):
        wrapper.load_model()


def test_all_registered_adapters_satisfy_model_wrapper_contract() -> None:
    registry = get_model_adapter_registry()
    configs = {
        "dummy": ModelLoadConfig(source="dummy", name="dummy"),
        "huggingface": ModelLoadConfig(source="huggingface", name="org/model"),
        "local": ModelLoadConfig(source="local", name="./models/local-causal-lm"),
        "modelscope": ModelLoadConfig(source="modelscope", name="org/model"),
        "qwen3_dense": ModelLoadConfig(source="qwen3_dense", name="Qwen/Qwen3-8B"),
        "transformer_lens": ModelLoadConfig(source="transformer_lens", name="gpt2"),
    }

    for source, config in configs.items():
        wrapper = registry.create(config)
        assert isinstance(wrapper, ModelWrapper), source
        assert callable(wrapper.load_model)
        assert callable(wrapper.add_hook)
        assert callable(wrapper.run_with_cache)
        assert callable(wrapper.generate)
        assert callable(wrapper.remove_hooks)
        assert callable(wrapper.reset_hooks)
        assert callable(wrapper.add_perma_hook)
