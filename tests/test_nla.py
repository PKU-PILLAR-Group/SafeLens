from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

import SafeLens
from SafeLens.nla import (
    INJECT_PLACEHOLDER,
    NLAActorOutput,
    NLAClient,
    NLAResult,
    _append_nla_stopping_criterion,
    _nla_generation_status,
    build_nla_prompt_input_ids,
    extract_nla_explanation,
    find_nla_injection_positions,
    get_nla_profile,
    inject_nla_vectors,
    list_nla_profiles,
    load_nla_config,
    normalize_nla_activation,
)


class _TinyNLATokenizer:
    unk_token_id = 0

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        del add_special_tokens
        if text == "X":
            return [99]
        return [ord(ch) % 97 + 3 for ch in text]

    def apply_chat_template(
        self,
        messages: list[dict[str, Any]],
        tokenize: bool,
        add_generation_prompt: bool,
    ) -> list[int]:
        assert tokenize is True
        assert add_generation_prompt is True
        content = messages[0]["content"]
        assert "<concept>X</concept>" in content
        return [11, 29, 99, 522, 13]


def _write_sidecar(path: Path) -> None:
    payload = {
        "kind": "nla_model",
        "role": "av",
        "d_model": 4,
        "extraction": {"injection_scale": 3.0, "mse_scale": "sqrt_d_model"},
        "tokens": {
            "injection_char": "X",
            "injection_token_id": 99,
            "injection_left_neighbor_id": 29,
            "injection_right_neighbor_id": 522,
        },
        "prompt_templates": {"av": "Probe <concept>{injection_char}</concept>."},
    }
    path.mkdir()
    (path / "nla_meta.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_nla_sidecar_tokenizer_validation_and_injection(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    checkpoint = tmp_path / "nla-av"
    _write_sidecar(checkpoint)

    config = load_nla_config(checkpoint, tokenizer=_TinyNLATokenizer())

    assert config.d_model == 4
    assert config.injection_scale == 3.0
    assert config.mse_scale == 2.0
    assert build_nla_prompt_input_ids(_TinyNLATokenizer(), config) == [11, 29, 99, 522, 13]
    assert build_nla_prompt_input_ids(
        _TinyNLATokenizer(),
        config,
        prompt=f"custom <concept>{INJECT_PLACEHOLDER}</concept>",
    ) == [11, 29, 99, 522, 13]
    assert find_nla_injection_positions([11, 29, 99, 522, 13], config) == [(0, 2)]

    vector = torch.tensor([3.0, 4.0, 0.0, 0.0])
    scaled = normalize_nla_activation(vector, config.injection_scale)
    assert torch.allclose(scaled.norm(), torch.tensor(3.0))

    embeddings = torch.zeros(1, 5, 4)
    injected = inject_nla_vectors(torch.tensor([[11, 29, 99, 522, 13]]), embeddings, vector, config)
    assert torch.equal(injected[0, 2], vector)
    assert torch.equal(injected[0, 1], torch.zeros(4))

    assert extract_nla_explanation("x <explanation>semantic feature</explanation> y") == (
        "semantic feature"
    )
    assert extract_nla_explanation("<explanation>semantic feature without close") == (
        "semantic feature without close"
    )


def test_nla_profiles_and_top_level_exports() -> None:
    profiles = list_nla_profiles()

    assert profiles[0]["name"] == "qwen2.5-7b-l20"
    assert profiles[0]["av_revision"] == "b88469162777ae6553bc14208eb0cb579336f8f4"
    assert profiles[0]["ar_revision"] == "e2c9e57eac213d37a31612087f645ab6332c1bb6"
    assert get_nla_profile("qwen").av_repo == "kitft/nla-qwen2.5-7b-L20-av"
    assert SafeLens.NLAResult is NLAResult
    assert SafeLens.NLAClient.__name__ == "NLAClient"
    assert SafeLens.list_nla_profiles()[1]["name"] == "gemma3-12b-l32"

    with pytest.raises(ValueError, match="unknown NLA profile"):
        get_nla_profile("missing")


@pytest.mark.parametrize(
    ("raw_text", "generated_ids", "maximum", "eos_token_id", "expected"),
    [
        ("<explanation>complete</explanation>", [4, 5], 256, 2, (True, "end_tag")),
        ("<explanation>cut off", [4] * 96, 96, 2, (False, "length")),
        ("<explanation>ended early", [4, 2], 256, 2, (False, "eos")),
        ("<explanation>unknown", [4, 5], 256, [2, 3], (False, "unknown")),
    ],
)
def test_nla_generation_status_requires_closing_tag(
    raw_text: str,
    generated_ids: list[int],
    maximum: int,
    eos_token_id: int | list[int],
    expected: tuple[bool, str],
) -> None:
    assert (
        _nla_generation_status(
            raw_text,
            generated_ids,
            max_new_tokens=maximum,
            eos_token_id=eos_token_id,
        )
        == expected
    )


def test_nla_stopping_criterion_detects_the_complete_contract() -> None:
    torch = pytest.importorskip("torch")

    class _Tokenizer:
        @staticmethod
        def decode(ids: list[int], skip_special_tokens: bool) -> str:
            assert skip_special_tokens is False
            return "prefix </explanation>" if 9 in ids else "prefix"

    kwargs: dict[str, Any] = {}
    _append_nla_stopping_criterion(kwargs, _Tokenizer())

    stopped = kwargs["stopping_criteria"](
        torch.tensor([[1, 9], [1, 2]], dtype=torch.long),
        None,
    )
    assert stopped.tolist() == [True, False]


def test_nla_client_does_not_reconstruct_an_incomplete_explanation() -> None:
    class _Verbalizer:
        @staticmethod
        def explain(_activation: Any, **_kwargs: Any) -> NLAActorOutput:
            return NLAActorOutput(
                explanation="unfinished thought",
                raw_text="<explanation>unfinished thought",
                prompt_token_count=12,
                activation_norm=3.0,
                generated_token_count=96,
                generation_complete=False,
                finish_reason="length",
            )

    class _Reconstructor:
        @staticmethod
        def score(_explanation: str, _activation: Any) -> tuple[float, float]:
            raise AssertionError("incomplete explanations must not be reconstructed")

    result = NLAClient(_Verbalizer(), _Reconstructor()).explain_activation([1.0])  # type: ignore[arg-type]

    assert result.cosine is None
    assert result.mse_nrm is None
    assert result.metadata["generation_complete"] is False
    assert result.metadata["finish_reason"] == "length"
