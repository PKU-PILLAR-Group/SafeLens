import {
  ArrowRight,
  CircleAlert,
  Crosshair,
  FlaskConical,
  Scale,
  Waves
} from "lucide-react";

import type {
  ExplorerRun,
  MetricProvenance,
  WorkspaceView
} from "../types";

interface OverviewEvidenceGraphProps {
  run: ExplorerRun;
  selectedToken: number;
  selectedLayer: number;
  residualCell?: {
    norm: number;
    riskDirection: number;
    semanticDensity: number;
  };
  onNavigate: (view: WorkspaceView) => void;
}

interface EvidenceNode {
  id: string;
  label: string;
  value: string;
  detail: string;
  evidenceClass: MetricProvenance["kind"];
  view: WorkspaceView;
  direction: "supporting" | "contradicting";
}

export function OverviewEvidenceGraph({
  run,
  selectedToken,
  selectedLayer,
  residualCell,
  onNavigate
}: OverviewEvidenceGraphProps) {
  const token = run.tokens.find((item) => item.index === selectedToken) ?? run.tokens[0];
  const riskRank = [...run.tokens]
    .sort((left, right) => right.risk - left.risk || left.index - right.index)
    .findIndex((item) => item.index === token.index) + 1;
  const evidence = overviewEvidence(run, token.index, selectedLayer, residualCell);
  const supporting = evidence.filter((item) => item.direction === "supporting");
  const contradicting = evidence.filter((item) => item.direction === "contradicting");
  const patchingCell = run.patching?.cells.find(
    (cell) => cell.layer === selectedLayer && cell.tokenIndex === token.index
  );
  const availableAttribution = run.attributionMethods.find((method) => method.available);
  const limitations = [
    "The safety-direction score is run-relative and is not a calibrated probability of unsafe behavior.",
    patchingCell
      ? "The causal patch result is local to one corruption, component, layer, and token."
      : "No exact causal patch result is available for this token and layer.",
    availableAttribution
      ? `${availableAttribution.label} is available, but target and baseline choices still bound its interpretation.`
      : "No target-specific attribution method has been computed for this run."
  ];
  const recommendations: Array<{
    view: WorkspaceView;
    label: string;
    detail: string;
  }> = [
    {
      view: "residual",
      label: "Inspect residual trajectory",
      detail: "Check whether direction alignment persists across layers."
    },
    {
      view: "attribution",
      label: availableAttribution ? "Inspect signed attribution" : "Run target attribution",
      detail: availableAttribution
        ? `Open ${availableAttribution.label} at this token.`
        : "Compute a target-specific method and baseline."
    },
    {
      view: "patching",
      label: patchingCell ? "Inspect causal recovery" : "Run causal patching",
      detail: patchingCell
        ? "Review the exact patched score and recovery percentage."
        : "Test whether replacing this activation changes the target metric."
    }
  ];

  return (
    <section className="surface overview-evidence-map" aria-labelledby="overview-evidence-map-title">
      <div className="surface-header overview-evidence-heading">
        <div>
          <h3 id="overview-evidence-map-title">Evidence map</h3>
          <p>{visibleToken(token.text)} · token {token.index} · layer {selectedLayer}</p>
        </div>
        <span className="overview-confidence"><Crosshair size={13} /> exploratory</span>
      </div>

      <div className="overview-graph" aria-label="Evidence graph">
        <EvidenceColumn
          id="overview-supporting-title"
          label="Supporting evidence"
          tone="supporting"
          nodes={supporting}
          empty="No loaded measure currently supports this proxy direction."
          onNavigate={onNavigate}
        />

        <article className="overview-primary-finding" aria-labelledby="overview-primary-title">
          <span>Primary finding</span>
          <h4 id="overview-primary-title">
            Token {token.index} ranks {riskRank} of {run.tokens.length} by run-relative safety-direction proxy.
          </h4>
          <p>
            Score {token.risk.toFixed(3)} is exploratory derived evidence. It locates a candidate for analysis;
            it does not establish unsafe behavior or causality.
          </p>
          <dl>
            <div><dt>Evidence class</dt><dd>derived proxy</dd></div>
            <div><dt>Confidence</dt><dd>exploratory</dd></div>
            <div><dt>Token</dt><dd>{visibleToken(token.text)} · id {token.tokenId}</dd></div>
          </dl>
        </article>

        <EvidenceColumn
          id="overview-contradicting-title"
          label="Contradicting evidence"
          tone="contradicting"
          nodes={contradicting}
          empty="No contradictory measure is loaded; absence is not confirmation."
          onNavigate={onNavigate}
        />
      </div>

      <div className="overview-followup-grid">
        <section className="overview-limitations" aria-labelledby="overview-limitations-title">
          <header><CircleAlert size={16} /><h4 id="overview-limitations-title">Limitations</h4></header>
          <ul>
            {limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
          </ul>
        </section>
        <section className="overview-recommendations" aria-labelledby="overview-recommendations-title">
          <header><Waves size={16} /><h4 id="overview-recommendations-title">Recommended analysis</h4></header>
          <div>
            {recommendations.map((recommendation) => (
              <button key={recommendation.view} onClick={() => onNavigate(recommendation.view)}>
                <span><strong>{recommendation.label}</strong><small>{recommendation.detail}</small></span>
                {recommendation.view === "patching" ? <FlaskConical size={15} /> : <ArrowRight size={15} />}
              </button>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}

function EvidenceColumn({
  id,
  label,
  tone,
  nodes,
  empty,
  onNavigate
}: {
  id: string;
  label: string;
  tone: "supporting" | "contradicting";
  nodes: EvidenceNode[];
  empty: string;
  onNavigate: (view: WorkspaceView) => void;
}) {
  return (
    <section className={`overview-evidence-column ${tone}`} aria-labelledby={id}>
      <header><Scale size={14} /><h4 id={id}>{label}</h4><span>{nodes.length}</span></header>
      <div>
        {nodes.length > 0 ? nodes.map((node) => (
          <button key={node.id} className="overview-evidence-node" onClick={() => onNavigate(node.view)}>
            <span>{evidenceClassLabel(node.evidenceClass)}</span>
            <strong>{node.label}</strong>
            <b>{node.value}</b>
            <small>{node.detail}</small>
          </button>
        )) : (
          <div className="overview-evidence-empty" role="status">{empty}</div>
        )}
      </div>
    </section>
  );
}

function overviewEvidence(
  run: ExplorerRun,
  tokenIndex: number,
  layer: number,
  residualCell: OverviewEvidenceGraphProps["residualCell"]
) {
  const token = run.tokens.find((item) => item.index === tokenIndex) ?? run.tokens[0];
  const evidence: EvidenceNode[] = [];
  if (residualCell) {
    evidence.push({
      id: "residual-direction",
      label: "Residual direction",
      value: residualCell.riskDirection.toFixed(3),
      detail: `Normalized resid_post alignment at L${layer}; grouped against the 0.5 midpoint.`,
      evidenceClass: "derived_proxy",
      view: "residual",
      direction: residualCell.riskDirection >= 0.5 ? "supporting" : "contradicting"
    });
  }
  evidence.push({
    id: "token-attribution",
    label: "Attention proxy",
    value: token.attribution.toFixed(3),
    detail: "Run-relative descriptive signal grouped against the 0.5 midpoint; not causal attribution.",
    evidenceClass: "derived_proxy",
    view: "attribution",
    direction: token.attribution >= 0.5 ? "supporting" : "contradicting"
  });
  const patchingCell = run.patching?.cells.find(
    (cell) => cell.layer === layer && cell.tokenIndex === tokenIndex
  );
  if (patchingCell) {
    evidence.push({
      id: "causal-patching",
      label: "Activation patch effect",
      value: signedValue(patchingCell.causalEffect),
      detail: `Exact ${run.patching?.component} replacement; direction follows the causal-effect sign.`,
      evidenceClass: "causal",
      view: "patching",
      direction: patchingCell.causalEffect > 0 ? "supporting" : "contradicting"
    });
  }
  return evidence;
}

function evidenceClassLabel(value: MetricProvenance["kind"]) {
  if (value === "derived_proxy") return "derived proxy";
  if (value === "safety_method") return "safety output";
  return value === "causal" ? "causal evidence" : "raw";
}

function signedValue(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(3)}`;
}

function visibleToken(value: string) {
  return value.trim() ? value : "space";
}
