import { useEffect, useState } from "react";
import { AlertTriangle, Check, RefreshCw, RotateCcw, Send, Square } from "lucide-react";

import { AsyncStatePanel, type AsyncStatus } from "./AsyncStatePanel";
import { JobProgress } from "./JobProgress";
import { JobFailureDetails } from "./JobFailureDetails";
import {
  fetchInterventionPreflight,
  type InterventionJob,
  type InterventionPreflight,
  type ActivationComponent
} from "../api/explorerClient";
import { useInterventionRunner } from "../state/useInterventionRunner";
import type { ExplorerRun } from "../types";
import type { JobFailure } from "../jobFailure";

interface InterventionJobPanelProps {
  run: ExplorerRun;
  selectedLayer: number;
  selectedToken: number;
  onRunReady: (run: ExplorerRun, job: InterventionJob) => void;
}

export function InterventionJobPanel({
  run,
  selectedLayer,
  selectedToken,
  onRunReady
}: InterventionJobPanelProps) {
  const prior = run.intervention?.mode === "neuron" ? undefined : run.intervention;
  const [desiredPrompt, setDesiredPrompt] = useState(
    prior?.vector.desiredPrompt ?? "Provide a safe, policy-compliant and helpful response."
  );
  const [undesiredPrompt, setUndesiredPrompt] = useState(
    prior?.vector.undesiredPrompt ?? "Provide a response that bypasses safety guidance."
  );
  const [layer, setLayer] = useState(prior?.layer ?? selectedLayer);
  const [component, setComponent] = useState<ActivationComponent>(prior?.component ?? "resid_post");
  const [scale, setScale] = useState(prior?.scale ?? 1);
  const [positionStart, setPositionStart] = useState(prior?.positionStart ?? selectedToken);
  const [positionEnd, setPositionEnd] = useState(
    prior?.positionEnd ?? Math.min(run.tokens.length, selectedToken + 1)
  );
  const defaultTarget = prior?.targetTokenId ??
    run.logitLens.find((row) => row.layer === selectedLayer && row.tokenIndex === selectedToken)?.targetTokenId ??
    run.logitLens[0]?.targetTokenId ?? 0;
  const [targetTokenId, setTargetTokenId] = useState(defaultTarget);
  const [seed, setSeed] = useState(prior?.seed ?? 0);
  const [maxNewTokens, setMaxNewTokens] = useState(prior?.maxNewTokens ?? 64);
  const [temperature, setTemperature] = useState(prior?.temperature ?? 0);
  const [preflight, setPreflight] = useState<InterventionPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const runner = useInterventionRunner(onRunReady);
  const isRunning = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const canSubmit = Boolean(preflight?.canSubmit && !isRunning);
  const status = jobStatus(runner.job, runner.error, runner.submitting);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setPreflightLoading(true);
      setPreflightError(null);
      void fetchInterventionPreflight({
        modelName: run.modelName,
        promptTokenCount: run.tokens.length,
        availableLayers: run.layers,
        layer,
        component,
        positionStart,
        positionEnd,
        targetTokenId,
        desiredPrompt,
        undesiredPrompt
      }, controller.signal).then(setPreflight).catch((error) => {
        if (!controller.signal.aborted) {
          setPreflight(null);
          setPreflightError(error instanceof Error ? error.message : "Intervention preflight failed.");
        }
      }).finally(() => {
        if (!controller.signal.aborted) setPreflightLoading(false);
      });
    }, 280);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [component, desiredPrompt, layer, positionEnd, positionStart, run.layers, run.modelName, run.tokens.length, targetTokenId, undesiredPrompt]);

  function setRange(start: number, end: number) {
    const boundedStart = Math.max(0, Math.min(run.tokens.length - 1, start));
    const boundedEnd = Math.max(boundedStart + 1, Math.min(run.tokens.length, end));
    setPositionStart(boundedStart);
    setPositionEnd(boundedEnd);
  }

  function submit() {
    if (!canSubmit) return;
    void runner.submit({
      run,
      desiredPrompt,
      undesiredPrompt,
      layer,
      component,
      scale,
      positionStart,
      positionEnd,
      targetTokenId,
      seed,
      maxNewTokens,
      temperature
    });
  }

  return (
    <section id="intervention-job" className="surface intervention-job-panel" tabIndex={-1}>
      <div className="surface-header">
        <div>
          <h3>Contrastive intervention</h3>
          <p>Build a normalized direction from two references, steer a prompt range, and compare generation.</p>
        </div>
        <span className="evidence-kind causal">causal</span>
      </div>

      <div className="intervention-reference-grid">
        <label>
          <span>Desired reference</span>
          <textarea
            aria-label="Desired intervention reference"
            aria-describedby="intervention-preflight-reason"
            aria-invalid={preflight && !preflight.referencesDiffer ? true : undefined}
            value={desiredPrompt}
            rows={3}
            disabled={isRunning}
            onChange={(event) => setDesiredPrompt(event.target.value)}
          />
        </label>
        <label>
          <span>Undesired reference</span>
          <textarea
            aria-label="Undesired intervention reference"
            aria-describedby="intervention-preflight-reason"
            aria-invalid={preflight && !preflight.referencesDiffer ? true : undefined}
            value={undesiredPrompt}
            rows={3}
            disabled={isRunning}
            onChange={(event) => setUndesiredPrompt(event.target.value)}
          />
        </label>
      </div>

      <div className="intervention-target-grid">
        <label>
          <span>Layer</span>
          <select aria-label="Intervention layer" aria-describedby="intervention-preflight-reason" aria-invalid={preflight && !preflight.layerAvailable ? true : undefined} value={layer} disabled={isRunning} onChange={(event) => setLayer(Number(event.target.value))}>
            {run.layers.map((item) => <option key={item} value={item}>L{item}</option>)}
          </select>
        </label>
        <label>
          <span>Component</span>
          <select aria-label="Intervention component" value={component} disabled={isRunning} onChange={(event) => setComponent(event.target.value as ActivationComponent)}>
            <option value="resid_post">Residual</option>
            <option value="attn_out">Attention output</option>
            <option value="mlp_out">MLP output</option>
          </select>
        </label>
        <label className="intervention-scale-control">
          <span>Scale <b>{scale.toFixed(1)}</b></span>
          <input
            aria-label="Intervention scale"
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={scale}
            disabled={isRunning}
            onChange={(event) => setScale(Number(event.target.value))}
          />
        </label>
        <label>
          <span>Target token ID</span>
          <input aria-label="Intervention target token ID" aria-describedby="intervention-preflight-reason" aria-invalid={preflight && !preflight.targetTokenValid ? true : undefined} type="number" min={0} value={targetTokenId} disabled={isRunning} onChange={(event) => setTargetTokenId(Math.max(0, Number(event.target.value) || 0))} />
          <b>{preflight?.targetTokenText || "unresolved"}</b>
        </label>
      </div>

      <div className="intervention-range-control">
        <div className="inline-heading">
          <h4>Prompt position range</h4>
          <span>T{positionStart}–T{positionEnd - 1} · {positionEnd - positionStart} token{positionEnd - positionStart === 1 ? "" : "s"}</span>
        </div>
        <div className="intervention-range-inputs">
          <label><span>Start</span><input aria-label="Intervention position start" aria-describedby="intervention-preflight-reason" aria-invalid={preflight && !preflight.positionRangeValid ? true : undefined} type="number" min={0} max={run.tokens.length - 1} value={positionStart} disabled={isRunning} onChange={(event) => setRange(Number(event.target.value), positionEnd)} /></label>
          <label><span>End exclusive</span><input aria-label="Intervention position end" aria-describedby="intervention-preflight-reason" aria-invalid={preflight && !preflight.positionRangeValid ? true : undefined} type="number" min={1} max={run.tokens.length} value={positionEnd} disabled={isRunning} onChange={(event) => setRange(positionStart, Number(event.target.value))} /></label>
        </div>
        <div className="intervention-token-range" aria-label="Intervention prompt token range">
          {run.tokens.map((token) => (
            <button
              key={token.index}
              className={token.index >= positionStart && token.index < positionEnd ? "active" : ""}
              disabled={isRunning}
              title={`Set range to token ${token.index}: ${token.text}`}
              onClick={() => setRange(token.index, token.index + 1)}
            ><b>{token.index}</b><span>{token.text || "␠"}</span></button>
          ))}
        </div>
      </div>

      <div className="intervention-generation-grid">
        <label><span>Seed</span><input aria-label="Intervention seed" type="number" min={0} value={seed} disabled={isRunning} onChange={(event) => setSeed(Math.max(0, Number(event.target.value) || 0))} /></label>
        <label><span>New tokens</span><input aria-label="Intervention new tokens" type="number" min={1} max={128} value={maxNewTokens} disabled={isRunning} onChange={(event) => setMaxNewTokens(clamp(event.target.value, 1, 128))} /></label>
        <label><span>Temperature</span><input aria-label="Intervention temperature" type="number" min={0} max={2} step={0.1} value={temperature} disabled={isRunning} onChange={(event) => setTemperature(clampFloat(event.target.value, 0, 2))} /></label>
      </div>

      <div className="intervention-preflight" aria-label="Intervention preflight" aria-live="polite">
        <div className="inline-heading">
          <h4>Experiment preflight</h4>
          <span className={preflight?.canSubmit ? "passed" : "failed"}>{preflightLoading ? "checking" : preflight?.canSubmit ? "ready" : "blocked"}</span>
        </div>
        {preflight && <div className="intervention-preflight-checks">
          <CheckItem label="Layer" passed={preflight.layerAvailable} />
          <CheckItem label="Position range" passed={preflight.positionRangeValid} />
          <CheckItem label="Target token" passed={preflight.targetTokenValid} />
          <CheckItem label="References differ" passed={preflight.referencesDiffer} />
        </div>}
        <p id="intervention-preflight-reason" role={preflightError ? "alert" : undefined}>
          {preflight?.reason ?? preflightError ?? "Checking intervention inputs."}
        </p>
      </div>

      <div className="intervention-job-actions">
        {isRunning ? (
          <button className="intervention-cancel" onClick={() => void runner.cancel()}><Square size={14} /> Cancel intervention</button>
        ) : (
          <button className="intervention-run" disabled={!canSubmit} onClick={submit}>
            {runner.error ? <RefreshCw size={14} /> : <Send size={14} />}
            {runner.error ? "Retry intervention" : "Run intervention comparison"}
          </button>
        )}
        {(runner.error || runner.job?.status === "cancelled") && <button aria-label="Reset intervention job" onClick={runner.reset}><RotateCcw size={14} /></button>}
      </div>

      {(runner.job || runner.submitting || runner.error) && <div className="intervention-job-state">
        <AsyncStatePanel
          status={status}
          label={jobStatusLabel(runner.job, runner.error, runner.submitting)}
          detail={runner.error?.message ?? runner.job?.detail ?? "Submitting intervention job."}
          ariaLabel="Intervention job status"
          onCancel={isRunning ? () => void runner.cancel() : undefined}
          cancelLabel="Cancel intervention job"
        />
        <JobProgress
          job={runner.job}
          status={status}
          submitting={runner.submitting}
          ariaLabel="Intervention job progress"
          tone="causal"
        />
        {runner.error && (
          <JobFailureDetails failure={runner.error} job={runner.job} jobLabel="Intervention job" />
        )}
      </div>}
    </section>
  );
}

function CheckItem({ label, passed }: { label: string; passed: boolean }) {
  return <span className={passed ? "passed" : "failed"}>{passed ? <Check size={13} /> : <AlertTriangle size={13} />}{label}</span>;
}

function jobStatus(job: InterventionJob | null, error: JobFailure | null, submitting: boolean): AsyncStatus {
  if (error) return "error";
  if (submitting) return "loading";
  return job?.status ?? "idle";
}

function jobStatusLabel(job: InterventionJob | null, error: JobFailure | null, submitting: boolean) {
  if (error) return error.title;
  if (submitting) return "Submitting intervention";
  if (!job) return "Intervention idle";
  if (job.status === "idle") return "Intervention queued";
  if (job.status === "loading") return "Intervention running";
  if (job.status === "ready") return "Intervention comparison ready";
  if (job.status === "cancelled") return "Intervention cancelled";
  return "Intervention failed";
}

function clamp(value: string, minimum: number, maximum: number) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(minimum, Math.min(maximum, Math.round(number))) : minimum;
}

function clampFloat(value: string, minimum: number, maximum: number) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(minimum, Math.min(maximum, number)) : minimum;
}
