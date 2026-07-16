import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Check,
  CircleOff,
  KeyRound,
  RefreshCw,
  RotateCcw,
  Send,
  Square
} from "lucide-react";

import { AsyncStatePanel, type AsyncStatus } from "./AsyncStatePanel";
import { JobProgress } from "./JobProgress";
import { JobFailureDetails } from "./JobFailureDetails";
import {
  fetchNlaPreflight,
  fetchNlaProfiles,
  type NLAJob,
  type NLAPreflight,
  type NLAProfile
} from "../api/explorerClient";
import { useNlaRunner } from "../state/useNlaRunner";
import type { ExplorerRun } from "../types";
import type { JobFailure } from "../jobFailure";

interface NLAJobPanelProps {
  run: ExplorerRun;
  selectedToken: number;
  onRunReady: (run: ExplorerRun, job: NLAJob) => void;
}

export function NLAJobPanel({ run, selectedToken, onRunReady }: NLAJobPanelProps) {
  const availableRows = run.nla.filter((row) => row.status === "available").length;
  const [profiles, setProfiles] = useState<NLAProfile[]>([]);
  const [profileName, setProfileName] = useState(
    run.nlaCompatibility.profiles.find((profile) => profile.status !== "incompatible")?.name ??
    run.nlaCompatibility.profiles[0]?.name ?? ""
  );
  const [preflight, setPreflight] = useState<NLAPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(true);
  const [positions, setPositions] = useState<number[]>([selectedToken]);
  const [revision, setRevision] = useState("main");
  const [maxNewTokens, setMaxNewTokens] = useState(96);
  const [confirmGatedAccess, setConfirmGatedAccess] = useState(false);
  const [setupOpen, setSetupOpen] = useState(availableRows === 0);
  const runner = useNlaRunner(onRunReady);
  const profile = profiles.find((candidate) => candidate.name === profileName);
  const isRunning = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const canSubmit = Boolean(
    preflight?.canSubmit && positions.length > 0 && revision.trim() &&
    (!preflight.gated || confirmGatedAccess) && !isRunning
  );
  const provenance = useMemo(() => latestNlaJob(run), [run]);
  const status = jobStatus(runner.job, runner.error, runner.submitting);

  useEffect(() => {
    const controller = new AbortController();
    void fetchNlaProfiles(controller.signal).then((items) => {
      setProfiles(items);
      setProfileName((current) => current || items[0]?.name || "");
    }).catch((error) => {
      if (!controller.signal.aborted) setPreflightError(
        error instanceof Error ? error.message : "Could not load NLA profiles."
      );
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!profileName) return;
    const controller = new AbortController();
    setPreflightLoading(true);
    setPreflightError(null);
    void fetchNlaPreflight({
      modelName: run.modelName,
      dModel: run.nlaCompatibility.dModel,
      availableLayers: run.nlaCompatibility.availableLayers,
      profile: profileName
    }, controller.signal).then((result) => {
      setPreflight(result);
      setConfirmGatedAccess(false);
    }).catch((error) => {
      if (!controller.signal.aborted) {
        setPreflight(null);
        setPreflightError(error instanceof Error ? error.message : "NLA preflight failed.");
      }
    }).finally(() => {
      if (!controller.signal.aborted) setPreflightLoading(false);
    });
    return () => controller.abort();
  }, [profileName, run.modelName, run.nlaCompatibility.dModel, run.nlaCompatibility.availableLayers]);

  useEffect(() => {
    setPositions((current) => current.length === 1 ? [selectedToken] : current);
  }, [selectedToken]);

  function togglePosition(position: number) {
    setPositions((current) => {
      if (current.includes(position)) return current.length === 1
        ? current
        : current.filter((value) => value !== position);
      return current.length >= 8 ? current : [...current, position].sort((a, b) => a - b);
    });
  }

  function submit() {
    if (!canSubmit) return;
    void runner.submit({
      run,
      profile: profileName,
      positions,
      revision: revision.trim(),
      maxNewTokens,
      loadReconstructor: true,
      confirmGatedAccess
    });
  }

  return (
    <section id="nla-job" className="surface nla-job-panel" tabIndex={-1}>
      <div className="surface-header nla-job-header">
        <div>
          <span className="nla-module-kicker">Natural Language Autoencoder</span>
          <h3>Explain an internal activation</h3>
          <p>Select exact token positions, generate a natural-language explanation, and verify it with reconstruction fidelity.</p>
        </div>
        <span className={`nla-module-state ${availableRows > 0 ? "ready" : preflight?.canSubmit ? "compatible" : "blocked"}`}>
          {availableRows > 0 ? `${availableRows} results` : preflightLoading ? "checking" : preflight?.canSubmit ? "ready to run" : "setup required"}
        </span>
      </div>

      <div className="nla-job-summary" aria-label="NLA run summary">
        <span><small>Model</small><strong>{run.modelName}</strong></span>
        <span><small>Profile</small><strong>{profileName || "loading"}</strong></span>
        <span><small>Target</small><strong>{preflight ? `L${preflight.layer} · ${preflight.component}` : "checking"}</strong></span>
        <span><small>Width</small><strong>d_model {run.nlaCompatibility.dModel}</strong></span>
      </div>

      {availableRows > 0 && (
        <div className="nla-existing-actions">
          <span>Exact explanations and reconstruction metrics are loaded below.</span>
          <button onClick={() => setSetupOpen((current) => !current)}>
            {setupOpen ? "Hide generation setup" : "Generate more positions"}
          </button>
        </div>
      )}

      {(availableRows === 0 || setupOpen) && <>
      <div className="nla-step-heading"><b>1</b><span>Profile and decoder</span></div>

      <div className="nla-job-setup">
        <label>
          <span>Profile</span>
          <select
            aria-label="NLA profile"
            value={profileName}
            disabled={isRunning || profiles.length === 0}
            onChange={(event) => setProfileName(event.target.value)}
          >
            {profiles.map((candidate) => (
              <option key={candidate.name} value={candidate.name}>
                {candidate.name}{candidate.gated ? " · gated" : ""}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Checkpoint revision</span>
          <input
            aria-label="NLA checkpoint revision"
            aria-describedby={!revision.trim() ? "nla-revision-error" : undefined}
            aria-invalid={!revision.trim() || undefined}
            value={revision}
            maxLength={128}
            disabled={isRunning}
            onChange={(event) => setRevision(event.target.value)}
          />
          {!revision.trim() && (
            <span id="nla-revision-error" className="field-error" role="alert">
              Checkpoint revision is required.
            </span>
          )}
        </label>
        <label>
          <span>Explanation tokens</span>
          <input
            aria-label="NLA maximum new tokens"
            type="number"
            min={8}
            max={256}
            value={maxNewTokens}
            disabled={isRunning}
            onChange={(event) => setMaxNewTokens(clamp(event.target.value, 8, 256))}
          />
        </label>
        <div className="nla-profile-artifacts">
          <span>AV / AR</span>
          <strong title={`${profile?.av_repo ?? ""} · ${profile?.ar_repo ?? ""}`}>
            {profile ? `${shortRepo(profile.av_repo)} + ${shortRepo(profile.ar_repo)}` : "loading profiles"}
          </strong>
        </div>
      </div>

      <div className="nla-preflight" aria-label="NLA job preflight">
        <div className="inline-heading">
          <h4>Compatibility preflight</h4>
          <span className={`nla-preflight-status ${preflight?.status ?? "loading"}`}>
            {preflightLoading ? "checking" : preflight?.status.replace("_", " ") ?? "unavailable"}
          </span>
        </div>
        {preflight ? (
          <div className="nla-preflight-checks">
            <PreflightCheck label="Model" passed={preflight.modelMatches} value={preflight.baseModel} />
            <PreflightCheck label="Layer" passed={preflight.layerAvailable} value={`L${preflight.layer}`} />
            <PreflightCheck label="d_model" passed={preflight.dModelMatches} value={String(preflight.dModel)} />
            <PreflightCheck
              label="Access"
              passed={!preflight.gated || preflight.tokenConfigured}
              value={preflight.gated ? (preflight.tokenConfigured ? "token configured" : "HF token required") : "public"}
            />
          </div>
        ) : (
          <div className="nla-preflight-placeholder">{preflightError ?? "Checking the selected profile."}</div>
        )}
        <p>{preflight?.reason ?? preflightError}</p>
      </div>

      <div className="nla-position-picker">
        <div className="inline-heading">
          <h4><b>2</b> Choose exact token positions</h4>
          <span>{positions.length}/8 selected</span>
        </div>
        <div role="group" aria-label="NLA token positions">
          {run.tokens.map((token) => (
            <button
              key={token.index}
              className={positions.includes(token.index) ? "active" : ""}
              aria-pressed={positions.includes(token.index)}
              title={`token ${token.index}: ${token.text}`}
              disabled={isRunning || (!positions.includes(token.index) && positions.length >= 8)}
              onClick={() => togglePosition(token.index)}
            >
              <b>{token.index}</b><span>{token.text || "␠"}</span>
            </button>
          ))}
        </div>
      </div>

      {preflight?.gated && (
        <label className="nla-gated-confirmation">
          <input
            type="checkbox"
            checked={confirmGatedAccess}
            disabled={!preflight.tokenConfigured || isRunning}
            onChange={(event) => setConfirmGatedAccess(event.target.checked)}
          />
          <KeyRound size={14} />
          <span>I confirm local access to this gated AV/AR profile.</span>
        </label>
      )}

      <div className="nla-job-actions">
        {isRunning ? (
          <button className="nla-job-cancel" onClick={() => void runner.cancel()}>
            <Square size={14} /> Cancel NLA job
          </button>
        ) : (
          <button className="nla-job-run" aria-label="Run exact NLA" disabled={!canSubmit} onClick={submit}>
            {runner.error ? <RefreshCw size={14} /> : <Send size={14} />}
            {runner.error ? "Retry NLA generation" : `Generate ${positions.length} explanation${positions.length === 1 ? "" : "s"}`}
          </button>
        )}
        {(runner.error || runner.job?.status === "cancelled") && (
          <button aria-label="Reset NLA job" onClick={runner.reset}><RotateCcw size={14} /></button>
        )}
      </div>

      {!preflightLoading && preflight && !preflight.canSubmit && !runner.job && (
        <div className="nla-job-blocked" role="status">
          {preflight.status === "authorization_required" ? <KeyRound size={17} /> : <CircleOff size={17} />}
          <span>{preflight.reason}</span>
        </div>
      )}

      {(runner.job || runner.submitting || runner.error) && (
        <div className="nla-job-state">
          <AsyncStatePanel
            status={status}
            label={jobStatusLabel(runner.job, runner.error, runner.submitting)}
            detail={runner.error?.message ?? runner.job?.detail ?? "Submitting NLA job."}
            ariaLabel="NLA job status"
            onCancel={isRunning ? () => void runner.cancel() : undefined}
            cancelLabel="Cancel NLA job"
          />
          <JobProgress
            job={runner.job}
            status={status}
            submitting={runner.submitting}
            ariaLabel="NLA job progress"
            tone="nla"
          />
          {runner.error && (
            <JobFailureDetails failure={runner.error} job={runner.job} jobLabel="NLA job" />
          )}
        </div>
      )}
      </>}

      {provenance && (
        <details className="nla-job-provenance">
          <summary><Check size={13} /> Current exact NLA artifact</summary>
          <dl>
            <div><dt>Profile</dt><dd>{String(provenance.profile)}</dd></div>
            <div><dt>Layer / component</dt><dd>L{String(provenance.layer)} · {String(provenance.component)}</dd></div>
            <div><dt>Actor revision</dt><dd>{String(provenance.actorRevision)}</dd></div>
            <div><dt>AR revision</dt><dd>{String(provenance.reconstructorRevision)}</dd></div>
          </dl>
        </details>
      )}
    </section>
  );
}

function PreflightCheck({ label, passed, value }: { label: string; passed: boolean; value: string }) {
  return (
    <div className={passed ? "passed" : "failed"}>
      {passed ? <Check size={14} /> : <AlertTriangle size={14} />}
      <span>{label}</span><strong>{value}</strong>
    </div>
  );
}

function latestNlaJob(run: ExplorerRun) {
  const jobs = run.metadata?.nlaJobs;
  if (!Array.isArray(jobs) || jobs.length === 0) return null;
  const value = jobs[jobs.length - 1];
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function jobStatus(job: NLAJob | null, error: JobFailure | null, submitting: boolean): AsyncStatus {
  if (error) return "error";
  if (submitting) return "loading";
  return job?.status ?? "idle";
}

function jobStatusLabel(job: NLAJob | null, error: JobFailure | null, submitting: boolean) {
  if (error) return error.title;
  if (submitting) return "Submitting NLA job";
  if (!job) return "NLA idle";
  if (job.status === "idle") return "NLA job queued";
  if (job.status === "loading") return "NLA job running";
  if (job.status === "ready") return "NLA artifact ready";
  if (job.status === "cancelled") return "NLA job cancelled";
  return "NLA job failed";
}

function shortRepo(value: string | null | undefined) {
  return value?.split("/").pop() ?? "none";
}

function clamp(value: string, minimum: number, maximum: number) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(minimum, Math.min(maximum, number)) : minimum;
}
