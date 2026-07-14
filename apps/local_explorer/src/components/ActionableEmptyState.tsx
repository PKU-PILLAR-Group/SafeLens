import { ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

interface ActionableEmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  facts: Array<{ label: string; value: string }>;
  actionLabel: string;
  actionIcon: ReactNode;
  onAction: () => void;
  className?: string;
  compact?: boolean;
}

export function ActionableEmptyState({
  icon,
  title,
  description,
  facts,
  actionLabel,
  actionIcon,
  onAction,
  className = "",
  compact = false
}: ActionableEmptyStateProps) {
  return (
    <section
      className={`analysis-empty actionable-empty ${compact ? "compact" : ""} ${className}`.trim()}
      aria-label={title}
    >
      <span className="empty-icon" aria-hidden="true">{icon}</span>
      <strong>{title}</strong>
      <p>{description}</p>
      <dl className="actionable-empty-facts">
        {facts.map((fact) => (
          <div key={`${fact.label}:${fact.value}`}>
            <dt>{fact.label}</dt>
            <dd>{fact.value}</dd>
          </div>
        ))}
      </dl>
      <button type="button" className="actionable-empty-primary" onClick={onAction}>
        {actionIcon}
        <span>{actionLabel}</span>
        <ChevronRight size={15} aria-hidden="true" />
      </button>
    </section>
  );
}
