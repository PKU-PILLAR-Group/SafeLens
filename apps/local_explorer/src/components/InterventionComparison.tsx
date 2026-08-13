import { Activity, ArrowRight, GitCompareArrows, Pin } from "lucide-react";

import type { InterventionExperiment } from "../types";

interface InterventionComparisonProps {
  experiment: InterventionExperiment;
  onPin: () => void;
}

export function InterventionComparison({ experiment, onPin }: InterventionComparisonProps) {
  const originalKinds = tokenKinds(experiment, "original");
  const steeredKinds = tokenKinds(experiment, "steered");
  const isNeuron = experiment.mode === "neuron";
  return (
    <section className="surface intervention-comparison">
      <div className="surface-header intervention-comparison-header">
        <div>
          <h3>Original vs intervention</h3>
          <p>{isNeuron && experiment.feature ? `${experiment.feature.id} · ${experiment.feature.operation}` : `L${experiment.layer} · ${experiment.component}`} · factor {experiment.scale.toFixed(1)} · T{experiment.positionStart}–T{experiment.positionEnd - 1}</p>
        </div>
        <button className="icon-button" aria-label="Pin intervention comparison" title="Pin comparison" onClick={onPin}><Pin size={15} /></button>
      </div>

      <div className="intervention-delta-grid" aria-label="Intervention metric changes">
        <Metric label="Diagnostic logit delta" value={signed(experiment.deltas.targetLogit)} kind="causal" />
        <Metric label="Token edit distance" value={String(experiment.deltas.tokenEditDistance)} kind="causal" />
        <Metric label="Lexical risk delta" value={signed(experiment.deltas.lexicalRisk)} kind="derived proxy" />
        <Metric label="Max vocabulary delta" value={experiment.deltas.maxAbsLogit === undefined ? "not recorded" : experiment.deltas.maxAbsLogit.toFixed(6)} kind={experiment.deltas.effectStatus === "changed" ? "causal" : "unchanged"} />
      </div>

      <div className="intervention-output-compare">
        <OutputColumn side="original" title="Original" output={experiment.original} kinds={originalKinds} />
        <div className="intervention-output-arrow"><ArrowRight size={18} /><span className={experiment.deltas.generationChanged ? "changed" : "unchanged"}>{experiment.deltas.generationChanged ? "changed" : "unchanged"}</span></div>
        <OutputColumn side="steered" title="Steered" output={experiment.steered} kinds={steeredKinds} />
      </div>

      <div className="intervention-provenance-strip">
        {isNeuron ? <Activity size={15} /> : <GitCompareArrows size={15} />}
        <span><b>{experiment.vector.method}</b>{isNeuron ? `peak activation ${experiment.vector.rawNorm.toFixed(4)}` : `${experiment.vector.dimension}d contrast vector · norm ${experiment.vector.rawNorm.toFixed(4)}`}</span>
        <span><b>Objective</b>{visible(experiment.targetTokenText)} ({experiment.targetTokenId})</span>
        <span><b>Generation</b>seed {experiment.seed} · {experiment.maxNewTokens} tokens · temperature {experiment.temperature}</span>
      </div>
      <p className="intervention-probe-note">
        {experiment.deltas.generationChanged
          ? `Generation first diverged at output token ${experiment.deltas.firstDivergenceIndex ?? 0}.`
          : experiment.deltas.maxAbsLogit && experiment.deltas.maxAbsLogit > 0
            ? "Logits changed, but greedy decoding stayed on the same tokens in this generation window."
            : experiment.deltas.probeReason}
      </p>
    </section>
  );
}

function Metric({ label, value, kind }: { label: string; value: string; kind: string }) {
  return <span><em>{label}</em><strong>{value}</strong><i>{kind}</i></span>;
}

function OutputColumn({
  side,
  title,
  output,
  kinds
}: {
  side: "original" | "steered";
  title: string;
  output: InterventionExperiment["original"];
  kinds: Map<number, string>;
}) {
  return <article data-side={side}>
    <header><h4>{title}</h4><span>logit {output.targetLogit.toFixed(4)} · lexical {output.lexicalRisk.toFixed(4)}</span></header>
    <p>{output.text || "No continuation text"}</p>
    <div className="intervention-output-tokens">
      {output.tokens.map((token) => <span key={token.index} className={kinds.get(token.index) ?? "equal"} title={`token ${token.index} · id ${token.tokenId}`}><b>{token.index}</b>{visible(token.text)}</span>)}
    </div>
  </article>;
}

function tokenKinds(experiment: InterventionExperiment, side: "original" | "steered") {
  const result = new Map<number, string>();
  for (const row of experiment.diff) {
    const start = side === "original" ? row.originalStart : row.steeredStart;
    const end = side === "original" ? row.originalEnd : row.steeredEnd;
    for (let index = start; index < end; index += 1) result.set(index, row.kind);
  }
  return result;
}

function signed(value: number) {
  const magnitude = Math.abs(value) > 0 && Math.abs(value) < 0.001
    ? value.toExponential(2)
    : value.toFixed(4);
  return `${value > 0 ? "+" : ""}${magnitude}`;
}

function visible(value: string) {
  return value || "␠";
}
