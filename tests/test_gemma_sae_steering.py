from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch

from SafeLens.gemma_sae_steering import (
    GEMMA_9B_STEERING_PRESETS,
    GemmaSteeringConfig,
    SAEFeature,
    _make_decoder_hook,
    load_gemma_scope_decoder,
    validate_feature_index,
)
from SafeLens.sae_profiles import (
    GEMMA_SCOPE_9B_IT_MODEL,
    GEMMA_SCOPE_9B_IT_RELEASE,
    GEMMA_SCOPE_9B_IT_SAE_ID,
    list_sae_profiles,
)


def test_gemma_scope_decoder_reads_npz_and_preserves_feature_directions(tmp_path: Path) -> None:
    path = tmp_path / "params.npz"
    decoder = np.arange(24, dtype=np.float32).reshape(8, 3)
    np.savez(path, W_dec=decoder)

    loaded = load_gemma_scope_decoder(path, expected_width=8)

    assert loaded.feature_count == 8
    assert loaded.d_in == 3
    torch.testing.assert_close(loaded.direction(2), torch.from_numpy(decoder[2]))


def test_decoder_hook_combines_multiple_features_on_all_sequence_positions(tmp_path: Path) -> None:
    path = tmp_path / "params.npz"
    decoder = np.zeros((8, 3), dtype=np.float32)
    decoder[1] = [1, 2, 3]
    decoder[4] = [4, 5, 6]
    np.savez(path, W_dec=decoder)
    sae = load_gemma_scope_decoder(path, expected_width=8)
    hook = _make_decoder_hook(sae, [SAEFeature(1, 2), SAEFeature(4, -0.5)])

    value = torch.zeros(2, 5, 3)
    result = hook(value)

    expected = torch.tensor([0.0, 1.5, 3.0]).reshape(1, 1, 3)
    assert result.shape == value.shape
    torch.testing.assert_close(result, expected.expand_as(value))


def test_gemma_feature_index_range_and_presets() -> None:
    validate_feature_index(0)
    validate_feature_index(131_071)
    with pytest.raises(ValueError, match="between 0"):
        validate_feature_index(131_072)
    assert {item["featureIndex"] for item in GEMMA_9B_STEERING_PRESETS} == {
        62_610,
        121_465,
        29_917,
    }


def test_gemma_steering_config_reads_all_runtime_environment(monkeypatch) -> None:
    monkeypatch.setenv("SAFELENS_GEMMA_2_9B_IT_MODEL_PATH", "/models/gemma")
    monkeypatch.setenv("SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH", "/sae/params.npz")
    monkeypatch.setenv("SAFELENS_GEMMA_SAE_DEVICE", "cuda:0")
    monkeypatch.setenv("SAFELENS_GEMMA_SAE_DTYPE", "bfloat16")

    config = GemmaSteeringConfig.from_env()

    assert config.model_path == "/models/gemma"
    assert config.sae_path == "/sae/params.npz"
    assert config.device == "cuda:0"
    assert config.dtype == "bfloat16"


def test_gemma_steering_config_auto_selects_cuda(monkeypatch) -> None:
    monkeypatch.delenv("SAFELENS_GEMMA_SAE_DEVICE", raising=False)
    monkeypatch.delenv("SAFELENS_EXPLORER_JOB_DEVICE", raising=False)
    monkeypatch.delenv("SAFELENS_GEMMA_SAE_DTYPE", raising=False)
    monkeypatch.delenv("SAFELENS_EXPLORER_JOB_DTYPE", raising=False)
    monkeypatch.setattr("torch.cuda.is_available", lambda: True)

    config = GemmaSteeringConfig.from_env()

    assert config.device == "cuda:0"
    assert config.dtype == "bfloat16"


def test_canonical_gemma_9b_profile_matches_gemmascope_contract() -> None:
    profiles = list_sae_profiles(model_name=GEMMA_SCOPE_9B_IT_MODEL)
    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.release == GEMMA_SCOPE_9B_IT_RELEASE == "gemma-scope-9b-it-res-canonical"
    assert profile.sae_id == GEMMA_SCOPE_9B_IT_SAE_ID == "layer_9/width_131k/canonical"
    assert profile.layer == 9
    assert profile.width == 131_072
    assert profile.component == "resid_post"
    assert profile.architecture == "jump_relu"
