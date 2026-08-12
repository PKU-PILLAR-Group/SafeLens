import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Check, RefreshCw, RotateCcw, Send, Square } from "lucide-react";

import { AsyncStatePanel, type AsyncStatus } from "./AsyncStatePanel";
import { JobProgress } from "./JobProgress";
import { JobFailureDetails } from "./JobFailureDetails";
import {
  fetchPatchingPreflight,
  type PatchingComponent,
  type PatchingJob,
  type PatchingPreflight
} from "../api/explorerClient";
import { usePatchingRunner } from "../state/usePatchingRunner";
import type { ExplorerRun } from "../types";
import type { JobFailure } from "../jobFailure";

interface PatchingJobPanelProps {
  run: ExplorerRun;
  selectedToken: number;
  selectedLayer: number;
  onRunReady: (run: ExplorerRun, job: PatchingJob) => void;
}

export function PatchingJobPanel({
  run,
  selectedToken,
  selectedLayer,
  onRunReady
}: PatchingJobPanelProps) {
  const [corruptedPrompt, setCorruptedPrompt] = useState(run.patching?.corruptedPrompt ?? run.prompt);
  const [component, setComponent] = useState<PatchingComponent>(run.patching?.component ?? "resid_post");
  const [layers, setLayers] = useState<number[]>([selectedLayer]);
  const [head, setHead] = useState(run.patching?.head ?? 0);
  const [positions, setPositions] = useState<number[]>([selectedToken]);
  const defaultTarget = run.patching?.targetTokenId ??
    run.logitLens.find((row) => row.layer === selectedLayer && row.tokenIndex === selectedToken)?.targetTokenId ??
    run.logitLens[0]?.targetTokenId ?? 0;
  const [targetTokenId, setTargetTokenId] = useState(defaultTarget);
  const [preflight, setPreflight] = useState<PatchingPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const runner = usePatchingRunner(onRunReady);
  const isRunning = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const canSubmit = Boolean(preflight?.canSubmit && layers.length && positions.length && !isRunning);
  const sourceTokenIds = useMemo(() => run.tokens.map((token) => token.tokenId), [run.tokens]);
  const status = jobStatus(runner.job, runner.error, runner.submitting);
  const headCount = attentionHeadCount(run, layers[0] ?? selectedLayer);

  useEffect(() => {
    setHead((current) => Math.min(current, Math.max(0, headCount - 1)));
  }, [headCount]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setPreflightLoading(true);
      setPreflightError(null);
      void fetchPatchingPreflight({
        modelName: run.modelName,
        cleanPrompt: run.prompt,
        corruptedPrompt,
        cleanTokenIds: sourceTokenIds,
        layers: run.layers,
        component,
        targetTokenId
      }, controller.signal).then((result) => {
        setPreflight(result);
        setPositions((current) => {
          const valid = current.filter((position) => position < result.cleanTokenCount);
          return valid.length ? valid : result.changedPositions.slice(0, 8);
        });
      }).catch((error) => {
        if (!controller.signal.aborted) {
          setPreflight(null);
          setPreflightError(error instanceof Error ? error.message : "Patching preflight failed.");
        }
      }).finally(() => {
        if (!controller.signal.aborted) setPreflightLoading(false);
      });
    }, 280);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [component, corruptedPrompt, run.layers, run.modelName, run.prompt, sourceTokenIds, targetTokenId]);

  function toggleLayer(layer: number) {
    if (component === "z") {
      setLayers([layer]);
      return;
    }
    setLayers((current) => current.includes(layer)
      ? current.length === 1 ? current : current.filter((item) => item !== layer)
      : [...current, layer].sort((a, b) => a - b));
  }

  function selectComponent(next: PatchingComponent) {
    setComponent(next);
    if (next === "z") setLayers((current) => [current[0] ?? selectedLayer]);
  }

  function togglePosition(position: number) {
    setPositions((current) => current.includes(position)
      ? current.length === 1 ? current : current.filter((item) => item !== position)
      : [...current, position].sort((a, b) => a - b));
  }

  function submit() {
    if (!canSubmit) return;
    void runner.submit({
      run,
      corruptedPrompt,
      component,
      layers,
      positions,
      ...(component === "z" ? { head } : {}),
      targetTokenId
    });
  }

  return (
    <section id="patching-job" className="surface patching-job-panel" tabIndex={-1}>
      <div className="surface-header">
        <div>
          <h3>Activation patching experiment</h3>
          <p>Replace one clean activation in an aligned corrupted run and measure target-logit recovery.</p>
        </div>
        <span className="evidence-kind causal">causal</span>
      </div>

      <div className="patching-prompts">
        <label>
          <span>Clean prompt</span>
          <textarea value={run.prompt} readOnly rows={3} aria-label="Clean patching prompt" />
        </label>
        <label>
          <span>Corrupted prompt</span>
          <textarea
            value={corruptedPrompt}
            rows={3}
            disabled={isRunning}
            aria-label="Corrupted patching prompt"
            aria-describedby="patching-preflight-reason"
            aria-invalid={preflight && (
              !preflight.promptsDiffer || !preflight.tokenCountMatches || preflight.changedPositions.length === 0
            ) ? true : undefined}
            onChange={(event) => setCorruptedPrompt(event.target.value)}
          />
        </label>
      </div>

      <div className="patching-objective-row">
        <div>
          <span className="control-label">Component</span>
          <div className="patching-segmented" role="group" aria-label="Patching component">
            {(["resid_post", "attn_out", "z", "mlp_out"] as const).map((item) => (
              <button
                key={item}
                className={component === item ? "active" : ""}
                aria-pressed={component === item}
                disabled={isRunning}
                onClick={() => selectComponent(item)}
              >{componentLabel(item)}</button>
            ))}
          </div>
        </div>
        {component === "z" && (
          <label>
            <span>Attention head</span>
            <select aria-label="Patching attention head" value={head} disabled={isRunning} onChange={(event) => setHead(Number(event.target.value))}>
              {Array.from({ length: headCount }, (_, index) => <option key={index} value={index}>H{index}</option>)}
            </select>
          </label>
        )}
        <label>
          <span>Target token ID</span>
          <input
            type="number"
            min={0}
            value={targetTokenId}
            disabled={isRunning}
            aria-label="Patching target token ID"
            aria-describedby="patching-preflight-reason"
            aria-invalid={preflight && !preflight.targetTokenValid ? true : undefined}
            onChange={(event) => setTargetTokenId(Math.max(0, Number(event.target.value) || 0))}
          />
          <b>{preflight?.targetTokenText || "unresolved"}</b>
        </label>
      </div>

      <div className="patching-preflight" aria-label="Patching preflight" aria-live="polite">
        <div className="inline-heading">
          <h4>Alignment preflight</h4>
          <span className={preflight?.canSubmit ? "passed" : "failed"}>
            {preflightLoading ? "checking" : preflight?.canSubmit ? "ready" : "blocked"}
          </span>
        </div>
        {preflight && (
          <div className="patching-preflight-checks">
            <CheckItem label="Prompt differs" passed={preflight.promptsDiffer} />
            <CheckItem label="Token count" passed={preflight.tokenCountMatches} />
            <CheckItem label="Target token" passed={preflight.targetTokenValid} />
            <CheckItem label="Changed positions" passed={preflight.changedPositions.length > 0} />
          </div>
        )}
        <p id="patching-preflight-reason" role={preflightError ? "alert" : undefined}>
          {preflight?.reason ?? preflightError ?? "Checking tokenizer alignment."}
        </p>
      </div>

      {preflight && preflight.corruptedTokens.length > 0 && (
        <div className="patching-alignment">
          <div className="inline-heading">
            <h4>Position alignment</h4>
            <span>{preflight.changedPositions.length} changed</span>
          </div>
          <div className="patching-token-pairs" role="list" aria-label="Clean and corrupted token alignment">
            {preflight.corruptedTokens.map((token) => (
              <button
                key={token.index}
                className={`${token.changed ? "changed" : ""} ${positions.includes(token.index) ? "active" : ""}`}
                aria-pressed={positions.includes(token.index)}
                disabled={isRunning || !preflight.tokenCountMatches}
                onClick={() => togglePosition(token.index)}
              >
                <b>{token.index}</b>
                <span>{run.tokens[token.index]?.text || "␠"}</span>
                <i>{token.text || "␠"}</i>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="patching-layer-picker">
        <div className="inline-heading"><h4>Patch grid layers</h4><span>{component === "z" ? `H${head} · one layer` : `${layers.length} selected`}</span></div>
        <div role="group" aria-label="Patching layers">
          {run.layers.map((layer) => (
            <button
              key={layer}
              className={layers.includes(layer) ? "active" : ""}
              aria-pressed={layers.includes(layer)}
              disabled={isRunning}
              onClick={() => toggleLayer(layer)}
            >L{layer}</button>
          ))}
        </div>
      </div>

      <div className="patching-job-actions">
        {isRunning ? (
          <button className="patching-cancel" onClick={() => void runner.cancel()}>
            <Square size={14} /> Cancel experiment
          </button>
        ) : (
          <button className="patching-run" disabled={!canSubmit} onClick={submit}>
            {runner.error ? <RefreshCw size={14} /> : <Send size={14} />}
            {runner.error ? "Retry" : "Run"} {layers.length * positions.length} patches
          </button>
        )}
        {(runner.error || runner.job?.status === "cancelled") && (
          <button aria-label="Reset patching job" onClick={runner.reset}><RotateCcw size={14} /></button>
        )}
      </div>

      {(runner.job || runner.submitting || runner.error) && (
        <div className="patching-job-state">
          <AsyncStatePanel
            status={status}
            label={jobStatusLabel(runner.job, runner.error, runner.submitting)}
            detail={runner.error?.message ?? runner.job?.detail ?? "Submitting activation patching job."}
            ariaLabel="Patching job status"
            onCancel={isRunning ? () => void runner.cancel() : undefined}
            cancelLabel="Cancel patching job"
          />
          <JobProgress
            job={runner.job}
            status={status}
            submitting={runner.submitting}
            ariaLabel="Patching job progress"
            tone="causal"
          />
          {runner.error && (
            <JobFailureDetails failure={runner.error} job={runner.job} jobLabel="Patching job" />
          )}
        </div>
      )}
    </section>
  );
}

function CheckItem({ label, passed }: { label: string; passed: boolean }) {
  return <span className={passed ? "passed" : "failed"}>
    {passed ? <Check size={13} /> : <AlertTriangle size={13} />}{label}
  </span>;
}

function componentLabel(component: PatchingComponent) {
  if (component === "resid_post") return "Residual";
  if (component === "attn_out") return "Attention output";
  if (component === "z") return "Attention head";
  return "MLP output";
}

function attentionHeadCount(run: ExplorerRun, layer: number) {
  const coverage = run.metadata?.attentionHeadCoverage;
  if (coverage && typeof coverage === "object" && !Array.isArray(coverage)) {
    const byLayer = (coverage as Record<string, unknown>).availableByLayer;
    if (byLayer && typeof byLayer === "object" && !Array.isArray(byLayer)) {
      const count = Number((byLayer as Record<string, unknown>)[String(layer)]);
      if (Number.isInteger(count) && count > 0) return count;
    }
  }
  const heads = run.attentionHeads
    .filter((item) => item.layer === layer && !item.aggregation && !item.difference && !item.rollout)
    .map((item) => item.head);
  return heads.length > 0 ? Math.max(...heads) + 1 : 1;
}

function jobStatus(job: PatchingJob | null, error: JobFailure | null, submitting: boolean): AsyncStatus {
  if (error) return "error";
  if (submitting) return "loading";
  return job?.status ?? "idle";
}

function jobStatusLabel(job: PatchingJob | null, error: JobFailure | null, submitting: boolean) {
  if (error) return error.title;
  if (submitting) return "Submitting patching job";
  if (!job) return "Patching idle";
  if (job.status === "idle") return "Patching queued";
  if (job.status === "loading") return "Patching job running";
  if (job.status === "ready") return "Causal grid ready";
  if (job.status === "cancelled") return "Patching cancelled";
  return "Patching failed";
}
