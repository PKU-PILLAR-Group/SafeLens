import { X } from "lucide-react";

export function MatrixRangeSummary({
  label,
  range,
  onClear
}: {
  label: string;
  range?: [number, number];
  onClear: () => void;
}) {
  return (
    <div className={`range-summary matrix-range-summary ${range ? "" : "idle"}`} aria-label={`${label} range summary`}>
      <span>{range ? `${label} range ${range[0]}–${range[1]}` : `${label} range · all tokens`}</span>
      <button
        type="button"
        aria-label={`Clear ${label.toLowerCase()} range`}
        title="Clear token range"
        disabled={!range}
        onClick={onClear}
      >
        <X size={13} />
      </button>
    </div>
  );
}
