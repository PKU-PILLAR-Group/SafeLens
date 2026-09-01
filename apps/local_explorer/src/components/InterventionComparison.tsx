import { Activity, ArrowRight, GitCompareArrows, Pin } from "lucide-react";

import type { InterventionExperiment } from "../types";

interface InterventionComparisonProps {
  experiment: InterventionExperiment;
  onPin: () => void;
}

export function InterventionComparison({ experiment, onPin }: InterventionComparisonProps) {
  const originalKinds = tokenKinds(experiment, "original");
  const steeredKinds = tokenKinds(experiment, "steered");
  const isFeature = experiment.mode === "neuron" || experiment.mode === "sae_feature";
  const layerLabel = experiment.sourceLayer !== undefined || experiment.injectLayer !== undefined
    ? `source L${experiment.sourceLayer ?? experiment.layer} → inject L${experiment.injectLayer ?? experiment.layer}`
    : `L${experiment.layer}`;
  return (
    <section className="surface intervention-comparison">
      <div className="surface-header intervention-comparison-header">
        <div>
          <h3>Original vs intervention</h3>
          <p>{isFeature && experiment.feature ? `${experiment.feature.id} · ${experiment.feature.operation}` : `${layerLabel} · ${experiment.component} · generation-time`}{experiment.mode === "sae_feature" && experiment.feature?.operation === "ablate" ? "" : ` · factor ${experiment.scale.toFixed(1)}`} · T{experiment.positionStart}–T{experiment.positionEnd - 1}</p>
        </div>
        <button className="icon-button" aria-label="Pin intervention comparison" title="Pin comparison" onClick={onPin}><Pin size={15} /></button>
      </div>

      {experiment.mode === "sae_feature" && experiment.feature && (
        <div className="intervention-concept-note">
          <span>Concept label</span>
          <strong>{experiment.feature.conceptLabel ?? experiment.feature.label}</strong>
          <small>
            {experiment.feature.conceptSource === "neuronpedia"
              ? "Neuronpedia explanation metadata; the checkpoint itself stores only the feature index."
              : "No canonical explanation is bundled with this SAE checkpoint."}
            {experiment.feature.conceptUrl && (
              <> <a href={featureCardUrl(experiment.feature.conceptUrl)} target="_blank" rel="noreferrer">Open feature card</a></>
            )}
          </small>
          {experiment.feature.operation === "add" && experiment.feature.baselineActivation <= 0 && (
            <small>Feature inactive in the selected prompt range; this run injects its decoder direction explicitly.</small>
          )}
        </div>
      )}

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
        {isFeature ? <Activity size={15} /> : <GitCompareArrows size={15} />}
        <span><b>{experiment.vector.method}</b>{isFeature ? `feature reference ${experiment.vector.rawNorm.toFixed(4)}` : `${experiment.vector.dimension}d contrast vector · norm ${experiment.vector.rawNorm.toFixed(4)}`}</span>
        <span><b>Objective</b>{visible(experiment.targetTokenText)} ({experiment.targetTokenId})</span>
        <span><b>Generation</b>seed {experiment.seed} · {experiment.maxNewTokens} tokens · temperature {experiment.temperature}</span>
      </div>
      <p className="intervention-probe-note">
        {experiment.deltas.generationChanged
          ? `Generation first diverged at output token ${experiment.deltas.firstDivergenceIndex ?? 0}.`
          : experiment.deltas.maxAbsLogit && experiment.deltas.maxAbsLogit > 0
            ? "Logits changed, but greedy decoding stayed on the same tokens in this generation window. Try another feature or layer, or use sampling to expose the changed distribution."
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

function featureCardUrl(value: string | null | undefined) {
  return value?.replace("/api/feature/", "/") ?? "";
}

function visible(value: string) {
  return value || "␠";
}
