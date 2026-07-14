import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  Inbox,
  LoaderCircle,
  PauseCircle,
  RefreshCw,
  X
} from "lucide-react";

export type AsyncStatus = "idle" | "loading" | "ready" | "empty" | "error" | "cancelled";

interface AsyncStatePanelProps {
  status: AsyncStatus;
  label: string;
  detail: string;
  ariaLabel: string;
  onRetry?: () => void;
  onCancel?: () => void;
  retryLabel?: string;
  cancelLabel?: string;
}

export function AsyncStatePanel({
  status,
  label,
  detail,
  ariaLabel,
  onRetry,
  onCancel,
  retryLabel,
  cancelLabel
}: AsyncStatePanelProps) {
  const Icon = statusIcon(status);
  const cancellable = status === "loading" && onCancel;
  const retryable = (status === "empty" || status === "error" || status === "cancelled") && onRetry;

  return (
    <div
      className={`async-state-panel ${status} ${cancellable || retryable ? "has-action" : ""}`}
      aria-label={ariaLabel}
      aria-live="polite"
      aria-busy={status === "loading"}
    >
      <div className="async-state-icon" aria-hidden="true">
        <Icon className={status === "loading" ? "spin" : undefined} size={15} />
      </div>
      <div className="async-state-copy">
        <strong>{label}</strong>
        <span>{detail}</span>
      </div>
      {cancellable ? (
        <button
          className="async-state-action"
          aria-label={cancelLabel ?? `Cancel ${ariaLabel.toLowerCase()}`}
          title="Cancel"
          onClick={onCancel}
        >
          <X size={14} />
        </button>
      ) : retryable ? (
        <button
          className="async-state-action"
          aria-label={retryLabel ?? `Retry ${ariaLabel.toLowerCase()}`}
          title="Retry"
          onClick={onRetry}
        >
          <RefreshCw size={14} />
        </button>
      ) : null}
    </div>
  );
}

function statusIcon(status: AsyncStatus) {
  switch (status) {
    case "idle": return PauseCircle;
    case "loading": return LoaderCircle;
    case "ready": return CheckCircle2;
    case "empty": return Inbox;
    case "error": return AlertTriangle;
    case "cancelled": return Ban;
  }
}
