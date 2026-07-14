import { GitCompareArrows, X } from "lucide-react";

export function MatrixComparisonSummary({
  label,
  primary,
  anchor,
  delta,
  deltaLabel,
  onClear
}: {
  label: string;
  primary: string;
  anchor?: string;
  delta?: string;
  deltaLabel: string;
  onClear: () => void;
}) {
  return (
    <div className="matrix-selection-summary specialized-comparison-summary" aria-label={`${label} selection summary`}>
      <span><b>Primary</b>{primary}</span>
      <span className={anchor ? "active" : ""}>
        <GitCompareArrows size={13} />
        <b>Anchor</b>
        {anchor ?? "none"}
      </span>
      <span><b>{delta ?? "n/a"}</b>{deltaLabel}</span>
      <button
        type="button"
        aria-label={`Clear ${label} comparison anchor`}
        title="Clear comparison anchor"
        disabled={!anchor}
        onClick={onClear}
      >
        <X size={13} />
      </button>
    </div>
  );
}
