import { useMemo, useState } from "react";
import { RefreshCw, RotateCcw, Send, SlidersHorizontal, Square, Terminal } from "lucide-react";

import { AsyncStatePanel, type AsyncStatus } from "./AsyncStatePanel";
import { JobProgress } from "./JobProgress";
import { JobFailureDetails } from "./JobFailureDetails";
import { usePromptRunner } from "../state/usePromptRunner";
import type { JobFailure } from "../jobFailure";
import type { ExplorerRun } from "../types";
import type { PromptJob, PromptRunInput } from "../api/explorerClient";

const DEFAULT_MODEL = "sshleifer/tiny-gpt2";

interface PromptRunnerPanelProps {
  run: ExplorerRun;
  onRunReady: (run: ExplorerRun, job: PromptJob) => void;
}

export function PromptRunnerPanel({ run, onRunReady }: PromptRunnerPanelProps) {
  const [prompt, setPrompt] = useState(run.prompt);
  const [template, setTemplate] = useState<PromptRunInput["template"]>("plain");
  const [seed, setSeed] = useState(0);
  const [maxNewTokens, setMaxNewTokens] = useState(8);
  const [temperature, setTemperature] = useState(0);
  const runner = usePromptRunner(onRunReady);
  const isRunning = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const status = promptStatus(runner.job, runner.error, runner.submitting);
  const activeProvenance = useMemo(() => promptProvenance(run), [run]);

  function submit() {
    const cleaned = prompt.trim();
    if (!cleaned || isRunning) return;
    void runner.submit({
      prompt: cleaned,
      template,
      model: DEFAULT_MODEL,
      seed,
      maxNewTokens,
      temperature
    });
  }

  return (
    <section className="panel-section prompt-runner-panel">
      <div className="section-heading">
        <Terminal size={16} />
        <span>Prompt runner</span>
        {isRunning && <b>{runner.job?.progress ?? 0}%</b>}
      </div>

      <label className="prompt-runner-prompt">
        <span>Prompt</span>
        <textarea
          aria-label="Prompt runner text"
          aria-describedby={!prompt.trim() ? "prompt-runner-required" : undefined}
          aria-invalid={!prompt.trim() || undefined}
          value={prompt}
          maxLength={8_000}
          onChange={(event) => setPrompt(event.target.value)}
          disabled={isRunning}
        />
        {!prompt.trim() && (
          <span id="prompt-runner-required" className="field-error" role="alert">
            Prompt text is required.
          </span>
        )}
      </label>

      <div className="prompt-runner-grid">
        <label>
          <span>Template</span>
          <select
            aria-label="Prompt template"
            value={template}
            disabled={isRunning}
            onChange={(event) => setTemplate(event.target.value as PromptRunInput["template"])}
          >
            <option value="plain">Plain</option>
            <option value="chat">User / Assistant</option>
          </select>
        </label>
        <label>
          <span>Seed</span>
          <input
            aria-label="Generation seed"
            type="number"
            min={0}
            max={2_147_483_647}
            value={seed}
            disabled={isRunning}
            onChange={(event) => setSeed(clampNumber(event.target.value, 0, 2_147_483_647))}
          />
        </label>
        <label>
          <span>New tokens</span>
          <input
            aria-label="Maximum new tokens"
            type="number"
            min={1}
            max={64}
            value={maxNewTokens}
            disabled={isRunning}
            onChange={(event) => setMaxNewTokens(clampNumber(event.target.value, 1, 64))}
          />
        </label>
        <label>
          <span>Temperature</span>
          <input
            aria-label="Generation temperature"
            type="number"
            min={0}
            max={2}
            step={0.1}
            value={temperature}
            disabled={isRunning}
            onChange={(event) => setTemperature(clampNumber(event.target.value, 0, 2))}
          />
        </label>
      </div>

      <div className="prompt-runner-model">
        <SlidersHorizontal size={13} />
        <span>Local model</span>
        <strong>{DEFAULT_MODEL}</strong>
      </div>

      <div className="prompt-runner-actions">
        {isRunning ? (
          <button className="prompt-cancel-button" onClick={() => void runner.cancel()}>
            <Square size={13} /> Cancel
          </button>
        ) : (
          <button className="prompt-run-button" onClick={submit} disabled={!prompt.trim()}>
            {runner.error ? <RefreshCw size={13} /> : <Send size={13} />}
            {runner.error ? "Retry analysis" : "Run analysis"}
          </button>
        )}
        {(runner.error || runner.job?.status === "cancelled") && (
          <button className="prompt-reset-button" aria-label="Reset prompt job" onClick={runner.reset}>
            <RotateCcw size={13} />
          </button>
        )}
      </div>

      {(runner.job || runner.submitting || runner.error) && (
        <>
          <AsyncStatePanel
            status={status}
            label={promptStatusLabel(runner.job, runner.error, runner.submitting)}
            detail={runner.error?.message ?? runner.job?.detail ?? "Submitting the prompt job."}
            ariaLabel="Prompt job status"
            onCancel={isRunning ? () => void runner.cancel() : undefined}
            cancelLabel="Cancel prompt job"
          />
          <JobProgress
            job={runner.job}
            status={status}
            submitting={runner.submitting}
            ariaLabel="Prompt job progress"
            tone="prompt"
          />
          {runner.error && (
            <JobFailureDetails failure={runner.error} job={runner.job} jobLabel="Prompt job" />
          )}
        </>
      )}

      {activeProvenance && (
        <details className="prompt-run-provenance">
          <summary>Current generated run</summary>
          <dl>
            <div><dt>Model</dt><dd>{activeProvenance.model}</dd></div>
            <div><dt>Seed</dt><dd>{activeProvenance.seed}</dd></div>
            <div><dt>Template</dt><dd>{activeProvenance.template}</dd></div>
            <div><dt>Sampling</dt><dd>{activeProvenance.temperature > 0 ? `T=${activeProvenance.temperature}` : "greedy"}</dd></div>
          </dl>
        </details>
      )}
    </section>
  );
}

function promptStatus(job: PromptJob | null, error: JobFailure | null, submitting: boolean): AsyncStatus {
  if (error) return "error";
  if (submitting) return "loading";
  return job?.status ?? "idle";
}

function promptStatusLabel(job: PromptJob | null, error: JobFailure | null, submitting: boolean) {
  if (error) return error.title;
  if (submitting) return "Submitting prompt job";
  if (!job) return "Prompt runner idle";
  if (job.status === "idle") return "Prompt job queued";
  if (job.status === "loading") return "Prompt job running";
  if (job.status === "ready") return "Prompt run ready";
  if (job.status === "cancelled") return "Prompt job cancelled";
  return "Prompt job failed";
}

function clampNumber(value: string, minimum: number, maximum: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(minimum, Math.min(maximum, parsed)) : minimum;
}

function promptProvenance(run: ExplorerRun) {
  const candidate = run.metadata?.promptRunner;
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return null;
  const value = candidate as Record<string, unknown>;
  if (typeof value.model !== "string" || typeof value.seed !== "number") return null;
  return {
    model: value.model,
    seed: value.seed,
    template: typeof value.template === "string" ? value.template : "plain",
    temperature: typeof value.temperature === "number" ? value.temperature : 0
  };
}
