import { useId, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock3,
  ChevronLeft,
  ChevronRight,
  Code2,
  Copy,
  Download,
  FlaskConical,
  GitCompareArrows,
  LayoutDashboard,
  Pin,
  Sparkles,
  SlidersHorizontal
} from "lucide-react";

import type { MetricProvenance } from "../types";

export type EvidenceStatus =
  | "available"
  | "unavailable"
  | "incompatible"
  | "not-computed"
  | "failed"
  | "loading"
  | "cancelled";

export interface InspectorEvidence {
  title: string;
  subtitle: string;
  status: EvidenceStatus;
  statusReason: string;
  primaryLabel: string;
  primaryValue: string;
  rawValue: string;
  displayValue: string;
  units: string;
  evidenceClass: MetricProvenance["kind"];
  method: string;
  normalization: string;
  cacheKey: string;
  shape: string;
  sourceArtifact: string;
  runId: string;
  sampleId: string;
  modelName: string;
  warnings: string[];
  reproduction: Record<string, unknown>;
}

export interface InspectorNextAction {
  id: string;
  kind: "attribution" | "nla" | "patching" | "intervention" | "overview";
  label: string;
  description: string;
}

interface EvidenceInspectorProps {
  evidence: InspectorEvidence;
  canPrevious: boolean;
  canNext: boolean;
  canPin: boolean;
  pinned: boolean;
  nextActions: InspectorNextAction[];
  onPrevious: () => void;
  onNext: () => void;
  onPin: () => void;
  onCompare: () => void;
  onExport: () => void;
  onNextAction: (actionId: string) => void;
  detailLevel?: "compact" | "full";
}

export function EvidenceInspector({
  evidence,
  canPrevious,
  canNext,
  canPin,
  pinned,
  nextActions,
  onPrevious,
  onNext,
  onPin,
  onCompare,
  onExport,
  onNextAction,
  detailLevel = "full"
}: EvidenceInspectorProps) {
  const [copied, setCopied] = useState<"cache" | "reproduction" | null>(null);
  const headingId = useId();
  const loading = evidence.status === "loading" || evidence.status === "cancelled";
  const full = detailLevel === "full";

  async function copy(kind: "cache" | "reproduction") {
    const value = kind === "cache"
      ? evidence.cacheKey
      : JSON.stringify(evidence.reproduction, null, 2);
    await navigator.clipboard.writeText(value);
    setCopied(kind);
    window.setTimeout(() => setCopied((current) => current === kind ? null : current), 1000);
  }

  return (
    <section className="inspector evidence-inspector" aria-label="Evidence inspector">
      <header className="inspector-title">
        <div className="inspector-heading">
          <StatusIcon status={evidence.status} />
          <div>
            <h2>{evidence.title}</h2>
            <p>{evidence.subtitle}</p>
          </div>
        </div>
        <div className="inspector-nav">
          <button aria-label="Previous token" title="Previous token" disabled={!canPrevious} onClick={onPrevious}>
            <ChevronLeft size={15} />
          </button>
          <button aria-label="Next token" title="Next token" disabled={!canNext} onClick={onNext}>
            <ChevronRight size={15} />
          </button>
        </div>
      </header>

      <section className="inspector-section inspector-summary-section" aria-labelledby={`${headingId}-summary`}>
        <div className="inspector-section-heading">
          <h3 id={`${headingId}-summary`}>Summary</h3>
          <span className={`evidence-status status-${evidence.status}`}>
            {statusLabel(evidence.status)}
          </span>
        </div>
        <div className="inspector-primary-value">
          <span>{evidence.primaryLabel}</span>
          <strong>{evidence.primaryValue}</strong>
          <em>{evidence.evidenceClass.replace("_", " ")}</em>
        </div>
        <p className="inspector-status-reason">{evidence.statusReason}</p>
        <div className="inspector-value-grid">
          <span><b>{evidence.rawValue}</b>raw / stored</span>
          <span><b>{evidence.displayValue}</b>displayed</span>
          <span><b>{evidence.units}</b>units</span>
        </div>
      </section>

      {full && <section className="inspector-section" aria-labelledby={`${headingId}-evidence`}>
        <div className="inspector-section-heading">
          <h3 id={`${headingId}-evidence`}>Evidence</h3>
          <span>{evidence.shape}</span>
        </div>
        <dl className="inspector-provenance-list">
          <div><dt>Method</dt><dd>{evidence.method}</dd></div>
          <div><dt>Normalization</dt><dd>{evidence.normalization}</dd></div>
          <div className="inspector-cache-row">
            <dt>Cache key</dt>
            <dd className="inspector-cache-value">
              <span>{evidence.cacheKey}</span>
              <button aria-label="Copy inspector cache key" disabled={loading || !evidence.cacheKey} onClick={() => void copy("cache")}>
                {copied === "cache" ? <Check size={13} /> : <Copy size={13} />}
              </button>
            </dd>
          </div>
          <div><dt>Source artifact</dt><dd>{evidence.sourceArtifact}</dd></div>
          <div><dt>Run / sample</dt><dd>{evidence.runId} / {evidence.sampleId}</dd></div>
          <div><dt>Model</dt><dd>{evidence.modelName}</dd></div>
        </dl>
        {evidence.warnings.length > 0 && (
          <div className="inspector-warning-list" aria-label="Evidence warnings">
            {evidence.warnings.map((warning) => (
              <p key={warning}><AlertTriangle size={13} />{warning}</p>
            ))}
          </div>
        )}
      </section>}

      <section className="inspector-section inspector-actions-section" aria-labelledby={`${headingId}-actions`}>
        <div className="inspector-section-heading">
          <h3 id={`${headingId}-actions`}>Actions</h3>
        </div>
        <div className="inspector-actions">
          <button
            className={pinned ? "active" : ""}
            disabled={!canPin}
            aria-label={pinned ? "Unpin inspector evidence" : "Pin inspector evidence"}
            onClick={onPin}
          >
            <Pin size={14} />{pinned ? "Unpin" : "Pin"}
          </button>
          <button disabled={loading} onClick={onCompare}><GitCompareArrows size={14} />Compare</button>
          <button disabled={loading} aria-label="Copy reproducible evidence context" onClick={() => void copy("reproduction")}>
            {copied === "reproduction" ? <Check size={14} /> : <Code2 size={14} />}Context
          </button>
          <button disabled={loading} onClick={onExport}><Download size={14} />Export</button>
        </div>
        {full && nextActions.length > 0 && (
          <div className="inspector-next-actions" aria-label="Recommended next analysis">
            <div>
              <strong>Recommended next analysis</strong>
              <span>{evidence.status === "available" ? "Strengthen or challenge this evidence." : "Resolve the current evidence gap."}</span>
            </div>
            {nextActions.map((action) => (
              <button
                key={action.id}
                type="button"
                className={`next-action-${action.kind}`}
                onClick={() => onNextAction(action.id)}
              >
                <NextActionIcon kind={action.kind} />
                <span><b>{action.label}</b>{action.description}</span>
                <ChevronRight size={14} />
              </button>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}

function NextActionIcon({ kind }: { kind: InspectorNextAction["kind"] }) {
  if (kind === "attribution") return <Activity size={15} />;
  if (kind === "nla") return <Sparkles size={15} />;
  if (kind === "patching") return <FlaskConical size={15} />;
  if (kind === "intervention") return <SlidersHorizontal size={15} />;
  return <LayoutDashboard size={15} />;
}

function StatusIcon({ status }: { status: EvidenceStatus }) {
  if (status === "loading" || status === "cancelled") return <Clock3 size={18} />;
  return status === "available"
    ? <CheckCircle2 size={18} />
    : <AlertTriangle size={18} />;
}

function statusLabel(status: EvidenceStatus) {
  if (status === "available") return "available";
  if (status === "not-computed") return "not computed";
  if (status === "loading") return "loading";
  return status;
}
