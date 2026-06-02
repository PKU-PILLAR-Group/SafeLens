from __future__ import annotations

from typing import Any

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
    is_transformer_lens_native_checkpoint,
    is_transformer_lens_official_model_name,
    is_transformer_lens_supported_model_name,
    resolve_model_download_plan,
    resolve_transformer_lens_compatible_model_name,
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


def test_model_adapter_registry_flags_native_transformerlens_checkpoints_without_loading() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("solu-1l")

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is False
    assert payload["official_transformer_lens_supported"] is True
    assert payload["checkpoint_format"] == "transformer_lens_hooked_transformer"
    assert payload["transformers_loadable"] is False
    assert payload["resolved_pretrained_model"] == "NeelNanda/SoLU_1L512W_C4_Code"
    assert "HookedTransformer checkpoint" in payload["warnings"][-1]
    assert "Transformers-compatible checkpoints" in payload["errors"][0]


def test_transformerlens_supports_official_names_and_common_aliases() -> None:
    assert is_transformer_lens_supported_model_name("meta-llama/Llama-3.1-8B")
    assert is_transformer_lens_supported_model_name("gpt2-small")
    assert is_transformer_lens_supported_model_name("bert-base-uncased")
    assert is_transformer_lens_supported_model_name("state-spaces/mamba-2.8b-hf")
    assert is_transformer_lens_supported_model_name("solu-1l")
    assert is_transformer_lens_supported_model_name("solu-2l")
    assert is_transformer_lens_supported_model_name("gelu-2l")
    assert is_transformer_lens_supported_model_name("attn-only-3l")
    assert is_transformer_lens_supported_model_name("attn-only-demo")
    assert is_transformer_lens_native_checkpoint("solu-1l")
    assert is_transformer_lens_native_checkpoint("solu-2l")
    assert is_transformer_lens_native_checkpoint("gelu-2l")
    assert is_transformer_lens_native_checkpoint("attn-only-3l")
    assert is_transformer_lens_native_checkpoint("attn-only-demo")
    assert is_transformer_lens_native_checkpoint("ArthurConmy/redwood_attn_2l")
    assert is_transformer_lens_native_checkpoint("Baidicoot/Othello-GPT-Transformer-Lens")
    assert not is_transformer_lens_native_checkpoint("gpt2-small")
    assert is_transformer_lens_official_model_name("gpt2-small")
    assert is_transformer_lens_official_model_name("llama-7b-hf")
    assert is_transformer_lens_official_model_name("llama-30b")
    assert not is_transformer_lens_official_model_name("mamba-130m")
    assert not is_transformer_lens_supported_model_name("qwen-this-does-not-exist")
    assert not is_transformer_lens_supported_model_name("llama-this-does-not-exist")


def test_transformerlens_aliases_resolve_to_loadable_official_ids() -> None:
    aliases = {
        "distillgpt2": "distilgpt2",
        "yi-34b": "01-ai/Yi-34B",
        "mgpt": "ai-forever/mGPT",
        "olmo-1b": "allenai/OLMo-1B-hf",
        "santacoder": "bigcode/santacoder",
        "gpt-neo-small": "EleutherAI/gpt-neo-125M",
        "pythia-70m": "EleutherAI/pythia-70m",
        "pythia-125m": "EleutherAI/pythia-160m",
        "pythia-125m-deduped": "EleutherAI/pythia-160m-deduped",
        "bloom-1b1": "bigscience/bloom-1b1",
        "opt-xxl": "facebook/opt-13b",
        "CodeLlama-7b-instruct": "codellama/CodeLlama-7b-Instruct-hf",
        "llama-2-7b": "meta-llama/Llama-2-7b-hf",
        "llama-7b-hf": "huggyllama/llama-7b",
        "llama-30b-hf": "huggyllama/llama-30b",
        "mixtral-8x7b": "mistralai/Mixtral-8x7B-v0.1",
        "mixtral-instruct": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "mamba-130m": "state-spaces/mamba-130m-hf",
        "mamba-codestral": "mistralai/Mamba-Codestral-7B-v0.1",
        "olmoe": "allenai/OLMoE-1B-7B-0924",
        "apertus": "swiss-ai/Apertus-8B-2509",
        "apertus-instruct": "swiss-ai/Apertus-8B-Instruct-2509",
        "qwen-14b": "Qwen/Qwen-14B",
        "qwen2.5-7b-instruct": "Qwen/Qwen2.5-7B-Instruct",
        "qwen3-1.7b": "Qwen/Qwen3-1.7B",
        "gemma-2-9b": "google/gemma-2-9b",
        "gemma-3-270m": "google/gemma-3-270m",
        "medgemma-4b-it": "google/medgemma-4b-it",
        "phi-3": "microsoft/Phi-3-mini-4k-instruct",
        "stablelm-base-3b": "stabilityai/stablelm-base-alpha-3b",
        "tiny-stories-instruct-1M": "roneneldan/TinyStories-Instruct-1M",
        "stanford-gpt2-small-a": "stanford-crfm/alias-gpt2-small-x21",
        "bert-large-cased": "google-bert/bert-large-cased",
        "t5-base": "google-t5/t5-base",
        "w2v2-base": "facebook/wav2vec2-base",
        "w2v2-large": "facebook/wav2vec2-large",
        "solu-2l": "NeelNanda/SoLU_2L512W_C4_Code",
        "solu-2l-pile": "NeelNanda/SoLU_2L_v10_old",
        "gelu-2l": "NeelNanda/GELU_2L512W_C4_Code",
        "attn-only-3l": "NeelNanda/Attn_Only_3L512W_C4_Code",
        "attn-only-demo": "NeelNanda/Attn-Only-2L512W-Shortformer-6B-big-lr",
    }

    for alias, expected in aliases.items():
        assert is_transformer_lens_supported_model_name(alias)
        assert resolve_transformer_lens_compatible_model_name(alias) == expected


@pytest.mark.parametrize(
    "model_name, expected_resolved",
    [
        ("meta-llama/llama-3.1-8b", "meta-llama/Llama-3.1-8B"),
        (
            "meta-llama/meta-llama-3-8b-instruct",
            "meta-llama/Meta-Llama-3-8B-Instruct",
        ),
        (
            "mistralai/mistral-small-24b-base-2501",
            "mistralai/Mistral-Small-24B-Base-2501",
        ),
    ],
)
def test_transformerlens_full_official_ids_resolve_to_canonical_case(
    model_name: str,
    expected_resolved: str,
) -> None:
    assert is_transformer_lens_supported_model_name(model_name)
    assert resolve_transformer_lens_compatible_model_name(model_name) == expected_resolved


def test_model_adapter_registry_inspects_transformerlens_aliases_as_resolved_models() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("pythia-70m")

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["resolved_pretrained_model"] == "EleutherAI/pythia-70m"
    assert payload["checkpoint_format"] == "huggingface_transformers"


@pytest.mark.parametrize(
    "model_name, expected_resolved",
    [
        ("mamba-130m", "state-spaces/mamba-130m-hf"),
        ("state-spaces/mamba-130m-hf", "state-spaces/mamba-130m-hf"),
        ("state-spaces/mamba-2.8b-hf", "state-spaces/mamba-2.8b-hf"),
        ("mamba-codestral", "mistralai/Mamba-Codestral-7B-v0.1"),
    ],
)
def test_model_adapter_registry_inspects_safelens_transformerlens_bridge_extensions(
    model_name: str,
    expected_resolved: str,
) -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model(model_name)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["official_transformer_lens_supported"] is False
    assert payload["safelens_transformer_lens_compatible"] is True
    assert payload["resolved_pretrained_model"] == expected_resolved
    assert payload["checkpoint_format"] == "huggingface_transformers"
    assert payload["download_plan"]["pretrained_path"] == expected_resolved


@pytest.mark.parametrize(
    "model_name, expected_resolved",
    [
        ("Qwen/Qwen2-57B-A14B", "Qwen/Qwen2-57B-A14B"),
        ("qwen3-30b-a3b", "Qwen/Qwen3-30B-A3B"),
        ("Qwen/Qwen3-235B-A22B", "Qwen/Qwen3-235B-A22B"),
    ],
)
def test_model_adapter_registry_routes_qwen_moe_names_to_transformerlens_bridge(
    model_name: str,
    expected_resolved: str,
) -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model(model_name)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["official_transformer_lens_supported"] is False
    assert payload["safelens_transformer_lens_compatible"] is True
    assert payload["resolved_pretrained_model"] == expected_resolved
    assert payload["architecture_bridge_adapter"] == "routed_moe_decoder"
    assert "pre" not in payload["bridge_components"]
    assert "mlp_out" in payload["bridge_components"]


def test_model_adapter_registry_does_not_infer_transformerlens_from_family_markers() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("org/qwen-this-does-not-exist")

    assert payload["source"] == "huggingface"
    assert payload["supported"] is True


def test_model_adapter_registry_source_override_rejects_unknown_transformerlens_marker() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model(
        "org/qwen-this-does-not-exist",
        source="transformer_lens",
    )

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is False
    assert payload["official_transformer_lens_supported"] is False
    assert payload["safelens_transformer_lens_compatible"] is False
    assert "vendored TransformerLens support table" in payload["errors"][0]


@pytest.mark.parametrize(
    "model_name, expected_resolved",
    [
        ("yi-34b", "01-ai/Yi-34B"),
        ("qwen-14b", "Qwen/Qwen-14B"),
        ("llama-2-7b", "meta-llama/Llama-2-7b-hf"),
        ("llama-30b-hf", "huggyllama/llama-30b"),
        ("stablelm-base-3b", "stabilityai/stablelm-base-alpha-3b"),
        ("w2v2-large", "facebook/wav2vec2-large"),
    ],
)
def test_model_adapter_registry_inspects_official_transformerlens_short_aliases(
    model_name: str,
    expected_resolved: str,
) -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model(model_name)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["resolved_pretrained_model"] == expected_resolved
    assert payload["official_transformer_lens_supported"] is True
    assert payload["download_plan"]["pretrained_path"] == expected_resolved
    assert payload["checkpoint_format"] == "huggingface_transformers"


def test_model_adapter_registry_uses_resolved_alias_for_transformerlens_model_family() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("w2v2-large")

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["model_family"] == "transformer_lens_compatible_audio_encoder"
    assert payload["resolved_pretrained_model"] == "facebook/wav2vec2-large"


@pytest.mark.parametrize(
    "model_name, expected_family, expected_resolved",
    [
        (
            "bert-base-uncased",
            "transformer_lens_compatible_encoder",
            "google-bert/bert-base-uncased",
        ),
        ("t5-small", "transformer_lens_compatible_encoder_decoder", "google-t5/t5-small"),
    ],
)
def test_model_adapter_registry_reports_transformerlens_non_decoder_families(
    model_name: str,
    expected_family: str,
    expected_resolved: str,
) -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model(model_name)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["model_family"] == expected_family
    assert payload["resolved_pretrained_model"] == expected_resolved


def test_model_adapter_registry_reports_architecture_specific_transformerlens_components() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("mamba-130m")

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["model_family"] == "transformer_lens_compatible_decoder"
    assert payload["resolved_pretrained_model"] == "state-spaces/mamba-130m-hf"
    assert payload["architecture_bridge_adapter"] == "mamba_ssm"
    assert "ssm_in" in payload["bridge_components"]
    assert "pattern" not in payload["bridge_components"]
    assert "attn_scores" not in payload["bridge_components"]


@pytest.mark.parametrize(
    "model_name, expected_resolved",
    [
        ("solu-1l", "NeelNanda/SoLU_1L512W_C4_Code"),
        ("solu-2l", "NeelNanda/SoLU_2L512W_C4_Code"),
        ("gelu-2l", "NeelNanda/GELU_2L512W_C4_Code"),
        ("attn-only-3l", "NeelNanda/Attn_Only_3L512W_C4_Code"),
        ("attn-only-demo", "NeelNanda/Attn-Only-2L512W-Shortformer-6B-big-lr"),
    ],
)
def test_model_adapter_registry_marks_transformerlens_native_aliases_as_native_checkpoints(
    model_name: str,
    expected_resolved: str,
) -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model(model_name)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is False
    assert payload["official_transformer_lens_supported"] is True
    assert payload["checkpoint_format"] == "transformer_lens_hooked_transformer"
    assert payload["transformers_loadable"] is False
    assert payload["resolved_pretrained_model"] == expected_resolved


def test_model_adapter_registry_inspects_transformerlens_local_path_as_supported() -> None:
    registry = get_model_adapter_registry()

    payload = registry.inspect_model("./models/local-tl", source="transformer_lens")

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["official_transformer_lens_supported"] is True
    assert payload["transformers_loadable"] is True
    assert payload["resolved_pretrained_model"] == "models/local-tl"
    assert payload["download_plan"]["provider"] == "local"
    assert payload["download_plan"]["uses_network"] is False
    assert payload["local_path"] == "models/local-tl"
    assert "errors" not in payload


def test_model_adapter_registry_inspects_existing_relative_transformerlens_path_as_local(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = get_model_adapter_registry()
    (tmp_path / "models" / "local-tl").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    payload = registry.inspect_model("models/local-tl", source="transformer_lens")

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["download_plan"]["provider"] == "local"
    assert payload["download_plan"]["pretrained_path"] == "models/local-tl"
    assert payload["local_path"] == "models/local-tl"
    assert "errors" not in payload


def test_model_adapter_registry_inspects_transformerlens_local_dir_as_supported() -> None:
    registry = get_model_adapter_registry()
    config = ModelLoadConfig(
        source="transformer_lens",
        name="custom-local-model",
        local_dir="./models/local-tl",
    )

    payload = registry.inspect_model("custom-local-model", source="transformer_lens", config=config)

    assert payload["source"] == "transformer_lens"
    assert payload["supported"] is True
    assert payload["official_transformer_lens_supported"] is True
    assert payload["transformers_loadable"] is True
    assert payload["resolved_pretrained_model"] == "models/local-tl"
    assert payload["download_plan"]["pretrained_path"] == "models/local-tl"
    assert payload["download_plan"]["provider"] == "local"
    assert payload["local_path"] == "models/local-tl"
    assert "errors" not in payload


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


def test_transformerlens_build_model_wrapper_resolves_legacy_llama_alias_to_loadable_id() -> None:
    wrapper = build_model_wrapper(ModelLoadConfig(source="transformer_lens", name="llama-7b-hf"))

    assert isinstance(wrapper, TransformerLensCompatibleModelWrapper)
    assert wrapper.name == "llama-7b-hf"
    assert wrapper.pretrained_path == "huggyllama/llama-7b"


def test_transformerlens_build_model_wrapper_splits_processing_kwargs() -> None:
    wrapper = build_model_wrapper(
        ModelLoadConfig(
            source="transformer_lens",
            name="gpt2",
            load_kwargs={
                "low_cpu_mem_usage": False,
                "fold_ln": False,
                "center_unembed": False,
            },
        )
    )

    assert isinstance(wrapper, TransformerLensCompatibleModelWrapper)
    assert wrapper.load_kwargs == {"low_cpu_mem_usage": False}
    assert wrapper._process_weights_kwargs == {
        "fold_ln": False,
        "center_writing_weights": True,
        "center_unembed": False,
        "fold_value_biases": True,
        "refactor_factored_attn_matrices": False,
    }


def test_transformerlens_local_dir_wrapper_is_supported_runtime_target() -> None:
    wrapper = build_model_wrapper(
        ModelLoadConfig(
            source="transformer_lens",
            name="custom-local-model",
            local_dir="./models/local-tl",
        )
    )

    assert isinstance(wrapper, TransformerLensCompatibleModelWrapper)
    assert wrapper.pretrained_path == "models/local-tl"
    assert wrapper._resolve_pretrained_path() == "models/local-tl"
    assert wrapper._is_supported_transformer_lens_target() is True


def test_transformerlens_local_dir_named_like_alias_is_not_resolved_remotely() -> None:
    wrapper = build_model_wrapper(
        ModelLoadConfig(
            source="transformer_lens",
            name="custom-local-model",
            local_dir="gpt2-small",
        )
    )

    assert isinstance(wrapper, TransformerLensCompatibleModelWrapper)
    assert wrapper.pretrained_path == "gpt2-small"
    assert wrapper._resolve_pretrained_path() == "gpt2-small"
    assert wrapper._is_supported_transformer_lens_target() is True


def test_transformerlens_wrapper_rejects_unsupported_model_before_auto_loading() -> None:
    wrapper = build_model_wrapper(
        ModelLoadConfig(
            source="transformer_lens",
            name="hf-internal-testing/tiny-random-CLIPModel",
        )
    )

    with pytest.raises(ValueError, match="not in SafeLens' vendored TransformerLens-compatible"):
        wrapper.load_model()


def test_transformerlens_wrapper_rejects_native_checkpoint_before_auto_loading() -> None:
    for model_name in ("solu-1l", "gelu-2l", "attn-only-demo"):
        wrapper = build_model_wrapper(ModelLoadConfig(source="transformer_lens", name=model_name))

        with pytest.raises(NotImplementedError, match="TransformerLens-native checkpoint"):
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
