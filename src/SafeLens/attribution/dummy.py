"""Dummy attribution method used for end-to-end runner validation."""

from __future__ import annotations

from typing import Any

from SafeLens.core.base import AttributionResult, BaseAttributor, Batch, TokenAttribution
from SafeLens.core.registry import register_attributor


@register_attributor("dummy_attributor")
class DummyAttributor(BaseAttributor):
    """Assigns attribution scores to configured keyword matches."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def attribute_training(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        _ = batch, model_output
        return AttributionResult(
            method=self.name,
            attribution_score=0.0,
            details={"message": "training attribution is not implemented in the dummy method"},
        )

    def attribute_input(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        _ = model_output
        risk_terms = self.config.get("risk_terms", ["jailbreak", "attack", "harmful"])
        terms = [str(term).lower() for term in risk_terms]
        tokens = str(batch.get("text") or batch.get("prompt") or "").split()
        attributions = [
            TokenAttribution(
                token_index=index,
                token_text=token,
                score=1.0,
                source="input",
            )
            for index, token in enumerate(tokens)
            if any(term in token.lower() for term in terms)
        ]
        score = 1.0 if attributions else 0.0
        return AttributionResult(method=self.name, attribution_score=score, tokens=attributions)
