"""Dummy probe used to validate the pipeline contract."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from SafeLens.core.base import BaseProbe, Batch, LayerRef, ModelWrapper, ProbeResult
from SafeLens.core.registry import register_probe


@register_probe("dummy_probe")
class DummyProbe(BaseProbe):
    """Keyword-based probe that behaves like a real plugin without model dependencies."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.layers: list[LayerRef] = []
        self._handles: list[Any] = []
        self._intervention_applied = False

    def attach(self, model: ModelWrapper, layers: Sequence[LayerRef]) -> None:
        self.layers = list(layers or self.config.get("layers", []))
        for layer in self.layers:
            self._handles.append(model.add_hook(layer, self._capture_activation))

    def detect(self, batch: Batch) -> ProbeResult:
        text = str(batch.get("text") or batch.get("prompt") or "")
        risk_terms = self.config.get("risk_terms", ["jailbreak", "attack", "harmful"])
        terms = [str(term).lower() for term in risk_terms]
        tokens = text.split()
        matches = [
            index
            for index, token in enumerate(tokens)
            if any(term in token.lower() for term in terms)
        ]

        if "risk_score" in batch:
            risk_score = max(0.0, min(1.0, float(batch["risk_score"])))
        else:
            baseline = float(self.config.get("baseline_risk", 0.05))
            risk_score = max(0.0, min(1.0, baseline + 0.5 * len(matches)))

        category_threshold = float(self.config.get("category_threshold", 0.5))
        risk_category = self.config.get("risk_category", ["policy_violation"])
        if not matches and risk_score < category_threshold:
            risk_category = []

        return ProbeResult(
            risk_score=risk_score,
            critical_layers=list(self.layers),
            intervention_applied=self._intervention_applied,
            details={
                "method": self.name,
                "matched_terms": [tokens[index] for index in matches],
                "evidence_tokens": matches,
                "risk_category": risk_category,
            },
        )

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        _ = batch, direction, scale
        self._intervention_applied = True

    def detach(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        self.layers = []

    @staticmethod
    def _capture_activation(*args: Any, **kwargs: Any) -> None:
        _ = args, kwargs
