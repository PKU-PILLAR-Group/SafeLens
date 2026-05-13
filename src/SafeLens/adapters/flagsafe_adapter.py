"""FlagSafe adapter boundary."""

from __future__ import annotations

from typing import Any

from SafeLens.core.base import SafetyReport


class FlagSafeAdapter:
    """Convert SafeLens reports to a FlagSafe-compatible policy payload."""

    @staticmethod
    def to_flagsafe_rule(report: SafetyReport) -> dict[str, Any]:
        """Convert one report into an allow/block rule."""
        return {
            "action": "BLOCK" if report.flagged else "ALLOW",
            "reason": report.risk_category,
            "evidence": report.evidence_tokens,
            "score": report.risk_score,
            "attribution_score": report.attribution_score,
            "metadata": {
                "sample_id": report.sample_id,
                "source": "safelens",
            },
        }

    @staticmethod
    def to_flagsafe_batch(reports: list[SafetyReport]) -> list[dict[str, Any]]:
        """Convert several reports into FlagSafe rules."""
        return [FlagSafeAdapter.to_flagsafe_rule(report) for report in reports]
