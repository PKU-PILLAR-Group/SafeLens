from __future__ import annotations

import json
from pathlib import Path

import pytest

from SafeLens.explorer_sae import (
    GEMMA_SCOPE_2_270M_IT_RELEASE,
    GEMMA_SCOPE_2_270M_IT_REPO,
    explorer_sae_converter,
    explorer_sae_source,
    gemma_3_sae_modelscope_loader,
    load_local_gemma_scope_sae,
    neuronpedia_feature_info,
)


def test_explorer_sae_source_can_force_huggingface(monkeypatch) -> None:
    monkeypatch.setenv("SAFELENS_EXPLORER_SAE_SOURCE", "huggingface")

    assert explorer_sae_source(GEMMA_SCOPE_2_270M_IT_RELEASE) == "huggingface"
    assert explorer_sae_converter(GEMMA_SCOPE_2_270M_IT_RELEASE) is None


def test_local_jump_relu_sae_adapter_matches_published_formula(tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    torch = pytest.importorskip("torch")
    checkpoint = tmp_path / "params.npz"
    np.savez(
        checkpoint,
        W_enc=np.array([[1.0, -1.0], [0.5, 0.5]], dtype=np.float32),
        W_dec=np.array([[2.0, 0.0], [0.0, 3.0]], dtype=np.float32),
        b_enc=np.array([0.0, 0.0], dtype=np.float32),
        b_dec=np.array([0.25, -0.5], dtype=np.float32),
        threshold=np.array([0.5, 0.1], dtype=np.float32),
    )
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH", str(checkpoint))
    try:
        sae = load_local_gemma_scope_sae(
            model_name="google/gemma-2-9b-it",
            release="gemma-scope-9b-it-res-canonical",
            sae_id="layer_9/width_131k/canonical",
            device="cpu",
            dtype=torch.float32,
        )
        encoded = sae.encode(torch.tensor([[1.0, 0.0], [0.0, 1.0]]))
        assert torch.equal(encoded, torch.tensor([[1.0, 0.0], [0.0, 0.5]]))
        decoded = sae.decode(encoded)
        assert torch.allclose(decoded, torch.tensor([[2.25, -0.5], [0.25, 1.0]]))
        assert next(sae.parameters()).dtype == torch.float32
    finally:
        monkeypatch.undo()


def test_neuronpedia_feature_info_returns_explanation_and_logit_evidence(
    monkeypatch, tmp_path: Path
) -> None:
    payload = {
        "explanations": [{"description": "descriptive adjectives"}],
        "pos_str": [" enough", "ly"],
        "neg_str": [" Own", " trains"],
    }

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, _size):
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setenv("SAFELENS_EXPLORER_FEATURE_LABEL_CACHE", str(tmp_path))
    monkeypatch.setattr("SafeLens.explorer_sae.urlopen", lambda *args, **kwargs: Response())

    info = neuronpedia_feature_info(
        model_name="google/gemma-3-270m-it",
        layer=9,
        sae_id="layer_9_width_16k_l0_small",
        feature_index=2,
    )

    assert info["label"] == "descriptive adjectives"
    assert info["source"] == "neuronpedia"
    assert info["positiveTokens"] == [" enough", "ly"]
    assert info["negativeTokens"] == [" Own", " trains"]


def test_neuronpedia_feature_info_has_explicit_index_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SAFELENS_EXPLORER_FEATURE_LABEL_CACHE", str(tmp_path))
    monkeypatch.setattr(
        "SafeLens.explorer_sae.urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
    )

    info = neuronpedia_feature_info(
        model_name="google/gemma-3-270m-it",
        layer=9,
        sae_id="layer_9_width_16k_l0_small",
        feature_index=2,
    )

    assert info["label"] == "Gemma Scope feature 2"
    assert info["source"] == "index"


def test_gemma_scope_modelscope_loader_uses_only_checkpoint_files(
    monkeypatch,
    tmp_path: Path,
) -> None:
    torch = pytest.importorskip("torch")
    save_file = pytest.importorskip("safetensors.torch").save_file
    pytest.importorskip("modelscope")
    folder = Path("resid_post/layer_12_width_16k_l0_small")
    checkpoint = tmp_path / folder
    checkpoint.mkdir(parents=True)
    (checkpoint / "config.json").write_text(
        json.dumps(
            {
                "architecture": "jump_relu",
                "model_name": "google/gemma-3-270m-it",
                "hf_hook_point_in": "model.layers.12.output",
            }
        ),
        encoding="utf-8",
    )
    save_file(
        {
            "w_enc": torch.zeros(4, 8),
            "w_dec": torch.zeros(8, 4),
            "b_enc": torch.zeros(8),
            "b_dec": torch.zeros(4),
            "threshold": torch.ones(8),
        },
        checkpoint / "params.safetensors",
    )
    calls: list[dict[str, object]] = []

    def fake_snapshot_download(**kwargs):
        calls.append(kwargs)
        return tmp_path

    monkeypatch.setenv(
        "SAFELENS_EXPLORER_SAE_MODELSCOPE_CACHE",
        str(tmp_path / "empty-cache"),
    )
    monkeypatch.setattr("modelscope.snapshot_download", fake_snapshot_download)

    config, state, sparsity = gemma_3_sae_modelscope_loader(
        GEMMA_SCOPE_2_270M_IT_REPO,
        folder.as_posix(),
    )

    assert calls[0]["allow_patterns"] == [
        f"{folder}/config.json",
        f"{folder}/params.safetensors",
    ]
    assert config["hook_name"] == "blocks.12.hook_resid_post"
    assert config["d_in"] == 4
    assert config["d_sae"] == 8
    assert state["W_enc"].shape == (4, 8)
    assert state["W_dec"].shape == (8, 4)
    assert sparsity is None


def test_gemma_scope_modelscope_loader_reuses_complete_local_checkpoint(
    monkeypatch,
    tmp_path: Path,
) -> None:
    torch = pytest.importorskip("torch")
    save_file = pytest.importorskip("safetensors.torch").save_file
    pytest.importorskip("modelscope")
    repo = tmp_path / GEMMA_SCOPE_2_270M_IT_REPO
    folder = Path("resid_post/layer_12_width_16k_l0_small")
    checkpoint = repo / folder
    checkpoint.mkdir(parents=True)
    (checkpoint / "config.json").write_text(
        json.dumps(
            {
                "architecture": "jump_relu",
                "model_name": "google/gemma-3-270m-it",
                "hf_hook_point_in": "model.layers.12.output",
            }
        ),
        encoding="utf-8",
    )
    save_file(
        {
            "w_enc": torch.zeros(4, 8),
            "w_dec": torch.zeros(8, 4),
            "b_enc": torch.zeros(8),
            "b_dec": torch.zeros(4),
            "threshold": torch.ones(8),
        },
        checkpoint / "params.safetensors",
    )
    monkeypatch.setenv("SAFELENS_EXPLORER_SAE_MODELSCOPE_CACHE", str(tmp_path))
    monkeypatch.setattr(
        "modelscope.snapshot_download",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("network lookup")),
    )

    config, _, _ = gemma_3_sae_modelscope_loader(
        GEMMA_SCOPE_2_270M_IT_REPO,
        folder.as_posix(),
    )

    assert config["hook_name"] == "blocks.12.hook_resid_post"
