from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/run_local_explorer_jlens.py"
SPEC = importlib.util.spec_from_file_location("run_local_explorer_jlens", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Tokenizer:
    def decode(self, token_ids: list[int], clean_up_tokenization_spaces: bool = False) -> str:
        assert clean_up_tokenization_spaces is False
        return f"token-{token_ids[0]}"


def test_jlens_result_row_uses_the_exact_selected_position_and_next_token() -> None:
    run = {
        "tokens": [
            {"index": 0, "tokenId": 1, "text": "A"},
            {"index": 1, "tokenId": 2, "text": "B"},
        ]
    }
    row = MODULE._result_row(
        run,
        _Tokenizer(),
        torch.tensor([0.1, 0.5, 1.5, -0.2]),
        torch.tensor([0.2, 0.4, 0.6, 0.8]),
        layer=3,
        position=0,
        top_k=3,
        lens_source="research/lens",
        filename="model/lens.pt",
        revision="revision-1",
        n_prompts=128,
    )

    assert row["layer"] == 3
    assert row["tokenIndex"] == 0
    assert row["targetTokenId"] == 2
    assert row["targetTokenText"] == "token-2"
    assert row["targetRank"] == 1
    assert [prediction["tokenId"] for prediction in row["topPredictions"]] == [2, 1, 0]
    assert [prediction["tokenId"] for prediction in row["modelTopPredictions"]] == [3, 2, 1]
    assert row["nPrompts"] == 128


def test_jlens_worker_detects_a_complete_huggingface_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "models--test--model" / "snapshots" / "revision-1"
    snapshot.mkdir(parents=True)
    reference = tmp_path / "models--test--model" / "refs" / "main"
    reference.parent.mkdir(parents=True)
    reference.write_text("revision-1", encoding="utf-8")
    (snapshot / "config.json").write_text("{}", encoding="utf-8")
    (snapshot / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (snapshot / "model.safetensors").write_bytes(b"weights")

    assert MODULE._complete_hf_snapshot("test/model", str(tmp_path)) == snapshot


def test_jlens_worker_rejects_a_partial_sharded_snapshot(tmp_path: Path) -> None:
    snapshot = tmp_path / "models--test--model" / "snapshots" / "revision-1"
    snapshot.mkdir(parents=True)
    reference = tmp_path / "models--test--model" / "refs" / "main"
    reference.parent.mkdir(parents=True)
    reference.write_text("revision-1", encoding="utf-8")
    (snapshot / "config.json").write_text("{}", encoding="utf-8")
    (snapshot / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    (snapshot / "model.safetensors.index.json").write_text(
        '{"weight_map":{"a":"model-00001-of-00002.safetensors",'
        '"b":"model-00002-of-00002.safetensors"}}',
        encoding="utf-8",
    )
    (snapshot / "model-00001-of-00002.safetensors").write_bytes(b"weights")

    assert MODULE._complete_hf_snapshot("test/model", str(tmp_path)) is None


def test_jlens_worker_finds_a_pinned_cached_checkpoint(tmp_path: Path) -> None:
    revision = "abc123"
    filename = "model/lens.pt"
    checkpoint = (
        tmp_path
        / "models--research--lens"
        / "snapshots"
        / revision
        / filename
    )
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"weights")

    assert MODULE._cached_lens_checkpoint(
        "research/lens",
        filename=filename,
        revision=revision,
        cache_dir=str(tmp_path),
    ) == checkpoint
