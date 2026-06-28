# pyright: reportMissingImports=false
"""Captum-based input attribution for response tokens."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from SafeLens.core.base import AttributionResult, BaseAttributor, Batch, ModelWrapper
from SafeLens.core.registry import register_attributor


def attribute_response_token_input(
    model: ModelWrapper,
    prompt: str,
    *,
    response: str | None = None,
    response_token_ids: Sequence[int] | Any | None = None,
    target_response_index: int,
    generation_kwargs: Mapping[str, Any] | None = None,
    n_steps: int = 32,
    internal_batch_size: int | None = None,
    include_special_tokens: bool = False,
) -> AttributionResult:
    """Attribute a response target token logit to all earlier input tokens.

    ``target_response_index`` is zero-based within the response tokens. When
    ``response`` and ``response_token_ids`` are omitted, the response is generated
    with the supplied SafeLens model wrapper.
    """
    attributor = CaptumInputAttributor(
        {
            "n_steps": n_steps,
            "internal_batch_size": internal_batch_size,
            "include_special_tokens": include_special_tokens,
        }
    )
    attributor.attach(model)
    try:
        return attributor.attribute_response_token_input(
            prompt,
            response=response,
            response_token_ids=response_token_ids,
            target_response_index=target_response_index,
            generation_kwargs=generation_kwargs,
        )
    finally:
        attributor.detach()


@register_attributor("captum_input_attributor")
class CaptumInputAttributor(BaseAttributor):
    """Compute input-token attribution for a selected response token with Captum."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        super().__init__(config)
        self.model: ModelWrapper | None = None

    def attach(self, model: ModelWrapper) -> None:
        self.model = model

    def detach(self) -> None:
        self.model = None

    def attribute_training(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        _ = batch, model_output
        return AttributionResult(
            method=self.name,
            attribution_score=0.0,
            details={
                "message": ("training attribution is not implemented for Captum input attribution")
            },
        )

    def attribute_input(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        _ = model_output
        prompt = batch.get("prompt", batch.get("text"))
        if prompt is None:
            raise ValueError("Captum input attribution requires batch['prompt'] or batch['text'].")
        target_response_index = batch.get(
            "target_response_index",
            batch.get("response_index", self.config.get("target_response_index")),
        )
        if target_response_index is None:
            raise ValueError(
                "Captum input attribution requires target_response_index in the batch or config."
            )
        return self.attribute_response_token_input(
            str(prompt),
            response=_optional_str(batch.get("response")),
            response_token_ids=batch.get("response_token_ids"),
            target_response_index=int(target_response_index),
            generation_kwargs=_optional_mapping(batch.get("generation_kwargs"))
            or _optional_mapping(self.config.get("generation_kwargs")),
        )

    def attribute_response_token_input(
        self,
        prompt: str,
        *,
        response: str | None = None,
        response_token_ids: Sequence[int] | Any | None = None,
        target_response_index: int,
        generation_kwargs: Mapping[str, Any] | None = None,
    ) -> AttributionResult:
        model = self._require_model()
        torch = _require_torch()
        layer_integrated_gradients = _load_layer_integrated_gradients()
        hf_model = _require_hf_model(model)
        embedding_layer = _require_input_embedding_layer(hf_model)

        if response is not None and response_token_ids is not None:
            raise ValueError("Pass either response or response_token_ids, not both.")
        if target_response_index < 0:
            raise ValueError("target_response_index must be non-negative.")

        prompt_tokens = _ensure_single_token_tensor(
            _model_to_tokens(model, prompt),
            torch=torch,
            device=_model_device(model),
        )
        response_tokens = self._resolve_response_tokens(
            model,
            prompt,
            prompt_tokens,
            response=response,
            response_token_ids=response_token_ids,
            target_response_index=target_response_index,
            generation_kwargs=generation_kwargs,
            torch=torch,
        )
        if target_response_index >= int(response_tokens.shape[1]):
            raise ValueError(
                "target_response_index is outside the available response tokens "
                f"({target_response_index} >= {int(response_tokens.shape[1])})."
            )

        combined_tokens = torch.cat([prompt_tokens, response_tokens], dim=1)
        prompt_length = int(prompt_tokens.shape[1])
        target_position = prompt_length + target_response_index
        if target_position <= 0:
            raise ValueError("The target token must have at least one preceding input token.")

        input_tokens = combined_tokens[:, :target_position]
        target_token_id = int(combined_tokens[0, target_position].item())
        target_logit_position = target_position - 1

        def forward_func(tokens: Any) -> Any:
            prefix = _ensure_single_token_tensor(
                tokens,
                torch=torch,
                device=input_tokens.device,
                allow_batch=True,
            )
            target_column = torch.full(
                (prefix.shape[0], 1),
                target_token_id,
                dtype=prefix.dtype,
                device=prefix.device,
            )
            scored_tokens = torch.cat([prefix, target_column], dim=1)
            logits = _call_model_logits(hf_model, scored_tokens)
            return logits[:, target_logit_position, target_token_id]

        lig = layer_integrated_gradients(forward_func, embedding_layer)
        lig_kwargs = {
            "n_steps": int(self.config.get("n_steps", 32)),
            "internal_batch_size": self.config.get("internal_batch_size"),
        }
        if lig_kwargs["internal_batch_size"] is None:
            lig_kwargs.pop("internal_batch_size")
        attributions = lig.attribute(input_tokens, **lig_kwargs)
        raw_scores, scores = _token_scores_from_attributions(
            attributions,
            torch=torch,
            token_count=int(input_tokens.shape[1]),
        )
        token_records = _build_token_attributions(
            model,
            input_tokens[0],
            scores,
            raw_scores,
            prompt_length=prompt_length,
            include_special_tokens=bool(self.config.get("include_special_tokens", False)),
        )
        attribution_score = max((abs(token.score) for token in token_records), default=0.0)

        return AttributionResult(
            method=self.name,
            attribution_score=min(1.0, float(attribution_score)),
            tokens=token_records,
            details={
                "target_token_id": target_token_id,
                "target_token_text": _decode_one_token(model, target_token_id),
                "target_response_index": target_response_index,
                "target_position": target_position,
                "input_token_count": int(input_tokens.shape[1]),
                "response_source": _response_source(response, response_token_ids),
            },
        )

    def _require_model(self) -> ModelWrapper:
        if self.model is None:
            raise RuntimeError("CaptumInputAttributor must be attached to a model first.")
        return self.model

    def _resolve_response_tokens(
        self,
        model: ModelWrapper,
        prompt: str,
        prompt_tokens: Any,
        *,
        response: str | None,
        response_token_ids: Sequence[int] | Any | None,
        target_response_index: int,
        generation_kwargs: Mapping[str, Any] | None,
        torch: Any,
    ) -> Any:
        if response_token_ids is not None:
            return _ensure_single_token_tensor(
                response_token_ids,
                torch=torch,
                device=prompt_tokens.device,
            )
        if response is not None:
            return _ensure_single_token_tensor(
                _model_to_tokens(model, response, prepend_bos=False),
                torch=torch,
                device=prompt_tokens.device,
            )

        kwargs = dict(generation_kwargs or {})
        kwargs.setdefault("max_new_tokens", target_response_index + 1)
        generated_tokens = _ensure_single_token_tensor(
            model.generate(prompt, return_type="tokens", **kwargs),
            torch=torch,
            device=prompt_tokens.device,
        )
        return _generated_response_suffix(
            generated_tokens,
            prompt_tokens,
            torch=torch,
        )


def _require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise ImportError(
            "Captum input attribution requires torch. Install SafeLens with "
            "`pip install -e '.[attribution]'`."
        ) from exc
    return torch


def _load_layer_integrated_gradients() -> Any:
    try:
        from captum.attr import LayerIntegratedGradients
    except ImportError as exc:
        raise ImportError(
            "Captum input attribution requires captum. Install SafeLens with "
            "`pip install -e '.[attribution]'`."
        ) from exc
    return LayerIntegratedGradients


def _model_to_tokens(model: ModelWrapper, text: str, *, prepend_bos: bool | None = None) -> Any:
    to_tokens = getattr(model, "to_tokens", None)
    if not callable(to_tokens):
        raise TypeError("Captum input attribution requires a model wrapper with `to_tokens`.")
    if prepend_bos is None:
        return to_tokens(text)
    return to_tokens(text, prepend_bos=prepend_bos)


def _require_hf_model(model: ModelWrapper) -> Any:
    hf_model = getattr(model, "model", None)
    if hf_model is None:
        raise TypeError("Captum input attribution requires a wrapper with a loaded `.model`.")
    return hf_model


def _require_input_embedding_layer(hf_model: Any) -> Any:
    get_input_embeddings = getattr(hf_model, "get_input_embeddings", None)
    if not callable(get_input_embeddings):
        raise TypeError("Captum input attribution requires model.get_input_embeddings().")
    embedding_layer = get_input_embeddings()
    if embedding_layer is None:
        raise TypeError("Captum input attribution could not resolve input embeddings.")
    return embedding_layer


def _call_model_logits(hf_model: Any, input_ids: Any) -> Any:
    output = hf_model(input_ids=input_ids)
    logits = (
        output.get("logits") if isinstance(output, Mapping) else getattr(output, "logits", None)
    )
    if logits is None and isinstance(output, tuple | list) and output:
        logits = output[0]
    if logits is None:
        raise RuntimeError("Model output does not expose logits.")
    return logits


def _ensure_single_token_tensor(
    tokens: Any,
    *,
    torch: Any,
    device: Any = None,
    allow_batch: bool = False,
) -> Any:
    if not isinstance(tokens, torch.Tensor):
        tokens = torch.as_tensor(tokens, dtype=torch.long, device=device)
    else:
        tokens = tokens.to(device=device) if device is not None else tokens
    if tokens.ndim == 0:
        tokens = tokens.reshape(1, 1)
    elif tokens.ndim == 1:
        tokens = tokens.unsqueeze(0)
    if tokens.ndim != 2 or (not allow_batch and int(tokens.shape[0]) != 1):
        raise ValueError(
            f"Expected token ids shaped [pos] or [1, pos], got {tuple(tokens.shape)!r}."
        )
    return tokens.to(dtype=torch.long)


def _generated_response_suffix(generated_tokens: Any, prompt_tokens: Any, *, torch: Any) -> Any:
    prompt_length = int(prompt_tokens.shape[1])
    if int(generated_tokens.shape[1]) >= prompt_length and torch.equal(
        generated_tokens[:, :prompt_length],
        prompt_tokens,
    ):
        return generated_tokens[:, prompt_length:]
    return generated_tokens


def _token_scores_from_attributions(
    attributions: Any, *, torch: Any, token_count: int
) -> tuple[list[float], list[float]]:
    values = attributions
    if isinstance(values, tuple | list):
        values = values[0]
    if values.ndim >= 2 and int(values.shape[1]) > token_count:
        values = values[:, :token_count, ...]
    if values.ndim == 3:
        values = values.sum(dim=-1)
    if values.ndim == 2:
        values = values[0]
    if values.ndim != 1:
        raise ValueError(f"Expected token attribution scores, got shape {tuple(values.shape)!r}.")
    if int(values.shape[0]) != token_count:
        raise ValueError(
            f"Expected {token_count} token attribution scores, got {int(values.shape[0])}."
        )
    raw_scores = [float(score) for score in values.detach().cpu().tolist()]
    max_abs = max((abs(score) for score in raw_scores), default=0.0)
    if max_abs == 0.0:
        return raw_scores, [0.0 for _ in raw_scores]
    return raw_scores, [score / max_abs for score in raw_scores]


def _build_token_attributions(
    model: ModelWrapper,
    input_tokens: Any,
    scores: Sequence[float],
    raw_scores: Sequence[float],
    *,
    prompt_length: int,
    include_special_tokens: bool,
) -> list[Any]:
    from SafeLens.core.base import TokenAttribution

    token_ids = [int(token_id) for token_id in input_tokens.detach().cpu().tolist()]
    special_ids = _special_token_ids(model) if not include_special_tokens else set()
    records: list[TokenAttribution] = []
    for index, (token_id, score, raw_score) in enumerate(
        zip(token_ids, scores, raw_scores, strict=True)
    ):
        if token_id in special_ids:
            continue
        records.append(
            TokenAttribution(
                token_index=index,
                token_text=_decode_one_token(model, token_id),
                score=float(score),
                source="input",
                metadata={
                    "token_id": token_id,
                    "raw_score": float(raw_score),
                    "segment": "prompt" if index < prompt_length else "response_context",
                },
            )
        )
    return records


def _decode_one_token(model: ModelWrapper, token_id: int) -> str | None:
    to_string = getattr(model, "to_string", None)
    if callable(to_string):
        try:
            return str(to_string([int(token_id)], skip_special_tokens=False))
        except TypeError:
            return str(to_string([int(token_id)]))
    tokenizer = getattr(model, "tokenizer", None)
    decode = getattr(tokenizer, "decode", None)
    if callable(decode):
        return str(decode([int(token_id)]))
    return None


def _special_token_ids(model: ModelWrapper) -> set[int]:
    tokenizer = getattr(model, "tokenizer", None)
    ids: set[int] = set()
    for name in (
        "bos_token_id",
        "eos_token_id",
        "pad_token_id",
        "cls_token_id",
        "sep_token_id",
        "unk_token_id",
    ):
        value = getattr(tokenizer, name, None)
        if value is not None:
            ids.add(int(value))
    all_special_ids = getattr(tokenizer, "all_special_ids", None)
    if all_special_ids is not None:
        ids.update(int(value) for value in all_special_ids if value is not None)
    return ids


def _model_device(model: ModelWrapper) -> Any:
    return getattr(model, "device", None)


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _response_source(response: str | None, response_token_ids: Any | None) -> str:
    if response_token_ids is not None:
        return "response_token_ids"
    if response is not None:
        return "response"
    return "generated"
