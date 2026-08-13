import { useMemo, useState } from "react";
import { Activity, RefreshCw, RotateCcw, Send, Square } from "lucide-react";

import { AsyncStatePanel, type AsyncStatus } from "./AsyncStatePanel";
import { JobProgress } from "./JobProgress";
import { JobFailureDetails } from "./JobFailureDetails";
import { useAttributionRunner } from "../state/useAttributionRunner";
import type { JobFailure } from "../jobFailure";
import type { AttributionJob, AttributionRunInput } from "../api/explorerClient";
import type { ExplorerRun } from "../types";
import { generatedResponseText, trimGeneratedTurn } from "../generatedResponse";

interface AttributionJobPanelProps {
  run: ExplorerRun;
  onRunReady: (run: ExplorerRun, job: AttributionJob) => void;
}

export function AttributionJobPanel({ run, onRunReady }: AttributionJobPanelProps) {
  const [response, setResponse] = useState(() => inferredResponse(run));
  const [targetResponseIndex, setTargetResponseIndex] = useState(0);
  const [baseline, setBaseline] = useState<AttributionRunInput["baseline"]>("pad_token");
  const [nSteps, setNSteps] = useState(32);
  const runner = useAttributionRunner(onRunReady);
  const isRunning = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const status = attributionStatus(runner.job, runner.error, runner.submitting);
  const provenance = useMemo(() => latestAttributionProvenance(run), [run]);

  function submit() {
    if (!response.trim() || isRunning) return;
    void runner.submit({
      run,
      response,
      objective: "response_token_logit",
      targetResponseIndex,
      baseline,
      nSteps
    });
  }

  return (
    <section id="attribution-job" className="surface attribution-job-panel" tabIndex={-1}>
      <div className="surface-header attribution-job-header">
        <div>
          <h3>Integrated Gradients job</h3>
          <p>Attribute one response-token logit to the preceding input tokens.</p>
        </div>
        <span className="evidence-kind attribution-kind-causal">causal</span>
      </div>

      <div className="attribution-job-form">
        <label className="attribution-response-field">
          <span>Response</span>
          <textarea
            aria-label="Attribution response text"
            aria-describedby={!response.trim() ? "attribution-response-required" : undefined}
            aria-invalid={!response.trim() || undefined}
            value={response}
            maxLength={4_000}
            disabled={isRunning}
            placeholder="Enter the model response containing the target token"
            onChange={(event) => setResponse(event.target.value)}
          />
          {!response.trim() && (
            <span id="attribution-response-required" className="field-error" role="alert">
              Response text is required.
            </span>
          )}
        </label>
        <div className="attribution-job-parameters">
          <label>
            <span>Target index</span>
            <input
              aria-label="Target response token index"
              type="number"
              min={0}
              max={63}
              value={targetResponseIndex}
              disabled={isRunning}
              onChange={(event) => setTargetResponseIndex(clamp(event.target.value, 0, 63))}
            />
          </label>
          <label>
            <span>Baseline</span>
            <select
              aria-label="Attribution baseline"
              value={baseline}
              disabled={isRunning}
              onChange={(event) => setBaseline(event.target.value as AttributionRunInput["baseline"])}
            >
              <option value="pad_token">Pad token</option>
              <option value="zero_token_id">Token ID 0</option>
            </select>
          </label>
          <label>
            <span>Integration steps</span>
            <select
              aria-label="Attribution integration steps"
              value={nSteps}
              disabled={isRunning}
              onChange={(event) => setNSteps(Number(event.target.value))}
            >
              {[8, 16, 32, 64, 128].map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </label>
          <div className="attribution-objective">
            <span>Objective</span>
            <strong>Response token logit</strong>
          </div>
        </div>
      </div>

      <div className="attribution-job-actions">
        {isRunning ? (
          <button className="attribution-cancel-button" onClick={() => void runner.cancel()}>
            <Square size={14} /> Cancel attribution
          </button>
        ) : (
          <button className="attribution-run-button" disabled={!response.trim()} onClick={submit}>
            {runner.error ? <RefreshCw size={14} /> : <Send size={14} />}
            {runner.error ? "Retry Integrated Gradients" : "Run Integrated Gradients"}
          </button>
        )}
        {(runner.error || runner.job?.status === "cancelled") && (
          <button aria-label="Reset attribution job" onClick={runner.reset}>
            <RotateCcw size={14} />
          </button>
        )}
      </div>

      {(runner.job || runner.submitting || runner.error) && (
        <div className="attribution-job-state">
          <AsyncStatePanel
            status={status}
            label={attributionStatusLabel(runner.job, runner.error, runner.submitting)}
            detail={runner.error?.message ?? runner.job?.detail ?? "Submitting attribution job."}
            ariaLabel="Attribution job status"
            onCancel={isRunning ? () => void runner.cancel() : undefined}
            cancelLabel="Cancel attribution job"
          />
          <JobProgress
            job={runner.job}
            status={status}
            submitting={runner.submitting}
            ariaLabel="Attribution job progress"
            tone="attribution"
          />
          {runner.error && (
            <JobFailureDetails failure={runner.error} job={runner.job} jobLabel="Attribution job" />
          )}
        </div>
      )}

      {provenance && (
        <details className="attribution-job-provenance">
          <summary><Activity size={13} /> Current Captum result</summary>
          <dl>
            <div><dt>Target</dt><dd>{provenance.targetTokenText} · response[{provenance.targetResponseIndex}]</dd></div>
            <div><dt>Baseline</dt><dd>{provenance.baseline}</dd></div>
            <div><dt>Steps</dt><dd>{provenance.nSteps}</dd></div>
            <div><dt>Convergence Δ</dt><dd>{formatDelta(provenance.convergenceDelta)}</dd></div>
          </dl>
        </details>
      )}
    </section>
  );
}

function inferredResponse(run: ExplorerRun) {
  const jobs = run.metadata?.attributionJobs;
  if (Array.isArray(jobs) && jobs.length > 0) {
    const latest = jobs[jobs.length - 1];
    if (latest && typeof latest === "object" && !Array.isArray(latest)) {
      const response = (latest as Record<string, unknown>).response;
      if (typeof response === "string") return trimGeneratedTurn(response);
    }
  }
  return generatedResponseText(run);
}

function latestAttributionProvenance(run: ExplorerRun) {
  const jobs = run.metadata?.attributionJobs;
  if (!Array.isArray(jobs) || jobs.length === 0) return null;
  const value = jobs[jobs.length - 1];
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  return value as Record<string, unknown> & {
    targetTokenText?: string;
    targetResponseIndex?: number;
    baseline?: string;
    nSteps?: number;
    convergenceDelta?: number | null;
  };
}

function attributionStatus(
  job: AttributionJob | null,
  error: JobFailure | null,
  submitting: boolean
): AsyncStatus {
  if (error) return "error";
  if (submitting) return "loading";
  return job?.status ?? "idle";
}

function attributionStatusLabel(job: AttributionJob | null, error: JobFailure | null, submitting: boolean) {
  if (error) return error.title;
  if (submitting) return "Submitting attribution job";
  if (!job) return "Attribution idle";
  if (job.status === "idle") return "Attribution queued";
  if (job.status === "loading") return "Attribution running";
  if (job.status === "ready") return "Attribution ready";
  if (job.status === "cancelled") return "Attribution cancelled";
  return "Attribution failed";
}

function clamp(value: string, minimum: number, maximum: number) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(minimum, Math.min(maximum, number)) : minimum;
}

function formatDelta(value: unknown) {
  return typeof value === "number" ? value.toExponential(3) : "not reported";
}
