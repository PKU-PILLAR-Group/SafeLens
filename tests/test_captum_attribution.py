from __future__ import annotations

from typing import Any

import pytest

import SafeLens.attribution.captum as captum_module
from SafeLens.attribution import CaptumInputAttributor, attribute_response_token_input

torch = pytest.importorskip("torch")


class _FakeLayerIntegratedGradients:
    def __init__(self, forward_func: Any, layer: Any) -> None:
        self.forward_func = forward_func
        self.layer = layer

    def attribute(self, inputs: Any, **kwargs: Any) -> Any:
        _ = kwargs
        output = self.forward_func(inputs)
        assert output.shape == (1,)
        pos = int(inputs.shape[1])
        return torch.arange(pos * 2, dtype=torch.float32, device=inputs.device).reshape(1, pos, 2)


class _FakeTokenizer:
    bos_token_id = 0
    eos_token_id = 99
    pad_token_id = 0
    all_special_ids = [0, 99]


class _TinyCausalModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embed = torch.nn.Embedding(128, 2)
        self.proj = torch.nn.Linear(2, 128, bias=False)

    def get_input_embeddings(self) -> Any:
        return self.embed

    def forward(self, input_ids: Any) -> dict[str, Any]:
        hidden = self.embed(input_ids)
        return {"logits": self.proj(hidden)}


class _FakeWrapper:
    device = None

    def __init__(self) -> None:
        self.model = _TinyCausalModel()
        self.tokenizer = _FakeTokenizer()
        self.generate_calls: list[dict[str, Any]] = []

    def to_tokens(
        self,
        text: str,
        *,
        prepend_bos: bool | None = None,
        padding_side: str | None = None,
        move_to_device: bool = True,
        truncate: bool = True,
    ) -> Any:
        _ = padding_side, move_to_device, truncate
        ids = [ord(char) - 96 for char in text]
        if prepend_bos:
            ids = [0, *ids]
        return torch.tensor([ids], dtype=torch.long)

    def to_string(
        self,
        tokens: Any,
        *,
        skip_special_tokens: bool = False,
        clean_up_tokenization_spaces: bool = False,
    ) -> str:
        _ = clean_up_tokenization_spaces
        values = tokens if isinstance(tokens, list) else tokens.tolist()
        chars = []
        for token_id in values:
            if skip_special_tokens and int(token_id) in self.tokenizer.all_special_ids:
                continue
            chars.append(chr(int(token_id) + 96) if int(token_id) > 0 else "<bos>")
        return "".join(chars)

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        self.generate_calls.append(kwargs)
        prompt_tokens = self.to_tokens(prompt)
        suffix = torch.tensor([[7, 8]], dtype=torch.long)
        return torch.cat([prompt_tokens, suffix], dim=1)


@pytest.fixture()
def fake_captum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        captum_module,
        "_load_layer_integrated_gradients",
        lambda: _FakeLayerIntegratedGradients,
    )


def test_attribute_response_token_input_uses_exact_response_token_ids(fake_captum: None) -> None:
    wrapper = _FakeWrapper()

    result = attribute_response_token_input(
        wrapper,
        "ab",
        response_token_ids=[3, 4],
        target_response_index=1,
        include_special_tokens=True,
    )

    assert result.method == "captum_input_attributor"
    assert result.details["target_token_id"] == 4
    assert result.details["target_position"] == 3
    assert result.details["response_source"] == "response_token_ids"
    assert [token.metadata["token_id"] for token in result.tokens] == [1, 2, 3]
    assert [token.metadata["segment"] for token in result.tokens] == [
        "prompt",
        "prompt",
        "response_context",
    ]
    assert [token.metadata["raw_score"] for token in result.tokens] == [1.0, 5.0, 9.0]
    assert [round(token.score, 6) for token in result.tokens] == [
        round(1.0 / 9.0, 6),
        round(5.0 / 9.0, 6),
        1.0,
    ]


def test_attribute_response_token_input_tokenizes_external_response_text(fake_captum: None) -> None:
    wrapper = _FakeWrapper()
    result = attribute_response_token_input(
        wrapper,
        "ab",
        response="cd",
        target_response_index=0,
        include_special_tokens=True,
    )

    assert result.details["target_token_id"] == 3
    assert result.details["response_source"] == "response"
    assert [token.metadata["token_id"] for token in result.tokens] == [1, 2]


def test_attribute_response_token_input_can_generate_response_tokens(fake_captum: None) -> None:
    wrapper = _FakeWrapper()

    result = attribute_response_token_input(
        wrapper,
        "ab",
        target_response_index=1,
        generation_kwargs={"temperature": 0.0},
        include_special_tokens=True,
    )

    assert wrapper.generate_calls == [
        {"return_type": "tokens", "temperature": 0.0, "max_new_tokens": 2}
    ]
    assert result.details["target_token_id"] == 8
    assert result.details["response_source"] == "generated"
    assert [token.metadata["token_id"] for token in result.tokens] == [1, 2, 7]


def test_attribute_response_token_input_validates_target_index(fake_captum: None) -> None:
    with pytest.raises(ValueError, match="outside the available response tokens"):
        attribute_response_token_input(
            _FakeWrapper(),
            "ab",
            response_token_ids=[3],
            target_response_index=2,
        )


def test_captum_attributor_attribute_input_reads_batch_contract(fake_captum: None) -> None:
    attributor = CaptumInputAttributor({"target_response_index": 0, "include_special_tokens": True})
    attributor.attach(_FakeWrapper())

    result = attributor.attribute_input({"prompt": "ab", "response_token_ids": [3]})

    assert result.details["target_token_id"] == 3
    assert [token.metadata["token_id"] for token in result.tokens] == [1, 2]


def test_load_layer_integrated_gradients_reports_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = __import__

    def blocked_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "captum.attr":
            raise ImportError("blocked captum")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked_import)

    with pytest.raises(ImportError, match=r"\.\[attribution\]"):
        captum_module._load_layer_integrated_gradients()
