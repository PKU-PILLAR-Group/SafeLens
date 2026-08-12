from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/build_local_explorer_real_run.py"
SPEC = importlib.util.spec_from_file_location("build_local_explorer_real_run", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
_attention_cells = MODULE._attention_cells
_attribution_methods = MODULE._attribution_methods
_logit_lens_rows = MODULE._logit_lens_rows
_mlp_neurons = MODULE._mlp_neurons
_mlp_cells = MODULE._mlp_cells
_nla_compatibility = MODULE._nla_compatibility


def test_real_run_worker_uses_configured_gpu_and_dtype(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class FakeWrapper:
        def load_model(self) -> None:
            captured["loaded"] = True

    def fake_build(config):
        captured["config"] = config
        return FakeWrapper()

    monkeypatch.setenv("SAFELENS_EXPLORER_JOB_DEVICE", "cuda:0")
    monkeypatch.setenv("SAFELENS_EXPLORER_JOB_DTYPE", "bfloat16")
    monkeypatch.setattr(MODULE, "HuggingFaceModelWrapper", FakeWrapper)
    monkeypatch.setattr(MODULE, "build_model_wrapper", fake_build)

    wrapper = MODULE._load_wrapper("Qwen/Qwen2.5-7B-Instruct", "/tmp/model-cache")

    assert isinstance(wrapper, FakeWrapper)
    assert captured["loaded"] is True
    assert captured["config"].device == "cuda:0"
    assert captured["config"].dtype == "bfloat16"
    assert captured["config"].load_kwargs == {"low_cpu_mem_usage": True}


def test_real_run_worker_uses_complete_local_snapshot_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_id = "Qwen/Qwen2.5-7B-Instruct"
    repository = tmp_path / "models--Qwen--Qwen2.5-7B-Instruct"
    snapshot = repository / "snapshots" / "revision-1"
    snapshot.mkdir(parents=True)
    (repository / "refs").mkdir()
    (repository / "refs" / "main").write_text("revision-1", encoding="utf-8")
    for name in ["config.json", "tokenizer_config.json", "model-00001-of-00001.safetensors"]:
        (snapshot / name).write_text("cached", encoding="utf-8")
    captured = {}

    class FakeWrapper:
        def load_model(self) -> None:
            pass

    def fake_build(config):
        captured["config"] = config
        return FakeWrapper()

    monkeypatch.setattr(MODULE, "HuggingFaceModelWrapper", FakeWrapper)
    monkeypatch.setattr(MODULE, "build_model_wrapper", fake_build)

    MODULE._load_wrapper(model_id, str(tmp_path))

    assert captured["config"].load_kwargs == {
        "low_cpu_mem_usage": False,
        "local_files_only": True,
    }
    assert captured["config"].tokenizer_kwargs == {"local_files_only": True}
    assert captured["config"].source == "local"
    assert captured["config"].local_dir == str(snapshot)


def test_attention_cells_are_derived_from_matching_layer_patterns() -> None:
    cache = {
        "blocks.0.attn.hook_pattern": torch.tensor(
            [
                [
                    [[1.0, 0.0], [0.25, 0.75]],
                    [[0.6, 0.4], [0.5, 0.5]],
                ]
            ]
        )
    }

    cells = _attention_cells(cache, [0])

    assert [cell["tokenIndex"] for cell in cells] == [0, 1]
    assert [cell["value"] for cell in cells] == [0.8, 0.625]
    assert all(cell["layer"] == 0 for cell in cells)
    assert all(cell["sourceKey"] == "blocks.0.attn.hook_pattern" for cell in cells)
    assert all(cell["metric"] == "mean_head_max_source_attention" for cell in cells)


def test_mlp_cells_preserve_raw_values_and_normalize_for_display() -> None:
    cache = {
        "layer_0.post": torch.tensor(
            [
                [
                    [-1.0, 1.0],
                    [-2.0, 4.0],
                ]
            ]
        )
    }

    cells = _mlp_cells(cache, [0])

    assert [cell["rawValue"] for cell in cells] == [1.0, 3.0]
    assert [cell["value"] for cell in cells] == [0.0, 1.0]
    assert all(cell["sourceKey"] == "layer_0.post" for cell in cells)
    assert all(cell["metric"] == "mean_absolute_mlp_post_activation" for cell in cells)


def test_logit_lens_uses_final_norm_and_real_unembedding() -> None:
    class DoubleNorm(torch.nn.Module):
        def forward(self, value: torch.Tensor) -> torch.Tensor:
            return value * 2

    class FakeWrapper:
        W_U = torch.tensor([[1.0, 0.0, -1.0], [0.0, 1.0, -1.0]])
        b_U = torch.zeros(3)

        def __init__(self) -> None:
            self.model = type(
                "Model",
                (),
                {"transformer": type("Transformer", (), {"ln_f": DoubleNorm()})()},
            )()

        def to_single_str_token(self, token_id: int) -> str:
            return ["zero", "one", "two"][token_id]

    cache = {"layer_0.resid_post": torch.tensor([[[1.0, 0.0], [0.0, 1.0]]])}

    rows = _logit_lens_rows(
        FakeWrapper(),
        cache,
        [0],
        [0, 1],
        final_next_token_id=2,
        top_k=2,
    )

    assert len(rows) == 2
    assert rows[0]["targetTokenId"] == 1
    assert rows[0]["targetLogit"] == 0.0
    assert rows[0]["targetRank"] == 2
    assert rows[0]["topPredictions"][0] == {
        "tokenId": 0,
        "tokenText": "zero",
        "logit": 2.0,
        "probability": pytest.approx(0.8668133),
    }
    assert rows[1]["targetTokenId"] == 2
    assert rows[1]["targetRank"] == 3
    assert rows[1]["sourceKey"] == "layer_0.resid_post -> ln_final -> unembed"


def test_logit_lens_aligns_residual_with_bfloat16_final_norm() -> None:
    class BFloatNorm(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.weight = torch.nn.Parameter(torch.ones(2, dtype=torch.bfloat16))

        def forward(self, value: torch.Tensor) -> torch.Tensor:
            return value * self.weight

    class FakeWrapper:
        W_U = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
        b_U = torch.zeros(2)

        def __init__(self) -> None:
            self.model = type(
                "Model",
                (),
                {"transformer": type("Transformer", (), {"ln_f": BFloatNorm()})()},
            )()

        def to_single_str_token(self, token_id: int) -> str:
            return ["zero", "one"][token_id]

    rows = _logit_lens_rows(
        FakeWrapper(),
        {"layer_0.resid_post": torch.tensor([[[1.0, 0.0]]])},
        [0],
        [0],
        final_next_token_id=1,
        top_k=2,
    )

    assert rows[0]["targetTokenId"] == 1
    assert rows[0]["targetLogit"] == pytest.approx(0.0)
    assert rows[0]["topPredictions"][0]["tokenId"] == 0


def test_mlp_neurons_preserve_signed_token_profiles() -> None:
    cache = {"layer_0.post": torch.tensor([[[-2.0, 0.5], [1.0, -3.0], [4.0, 2.0]]])}

    neurons = _mlp_neurons(cache, [0])

    assert len(neurons) == 2
    first = next(neuron for neuron in neurons if neuron["neuron"] == 0)
    assert first["activationsByToken"] == [-2.0, 1.0, 4.0]
    assert first["positiveTopTokens"] == [2, 1, 0]
    assert first["negativeTopTokens"] == [0, 1, 2]
    assert first["maxAbsoluteActivation"] == 4.0
    assert first["topTokens"] == [2, 0, 1]


def test_attribution_methods_preserve_sign_and_unavailable_state() -> None:
    methods = _attribution_methods(
        layers=[0, 1],
        projection_by_layer={0: [-2.0, 1.0], 1: [-1.0, 3.0]},
        attention_track=[0.2, 0.8],
        risk_scores=[0.0, 1.0],
    )

    residual = next(method for method in methods if method["id"] == "residual_direction")
    assert residual["signed"] is True
    assert residual["rows"][0]["values"] == [-2.0, 1.0]
    assert residual["rows"][1]["sourceKey"].startswith("layer_1.resid_post")

    attention = next(method for method in methods if method["id"] == "final_attention_proxy")
    assert attention["signed"] is False
    assert attention["rows"][0]["layer"] == -1

    integrated_gradients = next(
        method for method in methods if method["id"] == "integrated_gradients"
    )
    assert integrated_gradients["available"] is False
    assert "Captum" in integrated_gradients["unavailableReason"]


def test_nla_compatibility_reports_each_failed_dimension(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeWrapper:
        name = "tiny/model"
        cfg = type("Config", (), {"d_model": 2})()

    monkeypatch.setattr(
        MODULE,
        "list_nla_profiles",
        lambda: [
            {
                "name": "large-l20",
                "base_model": "large/model",
                "layer": 20,
                "component": "resid_post",
                "d_model": 4096,
            }
        ],
    )

    result = _nla_compatibility(FakeWrapper(), [0, 1])

    assert result["modelName"] == "tiny/model"
    assert result["dModel"] == 2
    profile = result["profiles"][0]
    assert profile["status"] == "incompatible"
    assert profile["modelMatches"] is False
    assert profile["layerAvailable"] is False
    assert profile["dModelMatches"] is False
    assert "model requires large/model" in profile["reason"]
    assert "layer L20 is not cached" in profile["reason"]
    assert "d_model requires 4096" in profile["reason"]
