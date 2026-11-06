import { useCallback, useEffect, useState } from "react";
import { Activity, RefreshCw, X } from "lucide-react";

import { cancelJob, fetchJobs, type JobSummary } from "../api/explorerClient";

interface JobCenterProps {
  onOpenDatasetJob?: (jobId: string) => void;
  inline?: boolean;
}

const JOB_KIND_LABELS: Record<string, string> = {
  "prompt-run": "Chat run",
  attribution: "Attribution",
  nla: "NLA",
  jlens: "J-Lens",
  patching: "Patching",
  intervention: "Intervention",
  "sae-discovery": "SAE discovery",
  "dataset-test": "Dataset test"
};

function activeJob(job: JobSummary) {
  return job.status === "idle" || job.status === "loading";
}

function jobStatusLabel(job: JobSummary) {
  if (job.status === "idle") return "Queued";
  if (job.status === "loading") return `Running ${job.progress}%`;
  if (job.status === "ready") return "Complete";
  if (job.status === "error") return "Failed";
  return "Cancelled";
}

function jobTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function datasetScore(job: JobSummary) {
  if (job.kind !== "dataset-test" || !job.result) return null;
  const metric = job.result.metric;
  if (!metric || typeof metric !== "object" || Array.isArray(metric)) return null;
  const accuracy = (metric as Record<string, unknown>).accuracy;
  return typeof accuracy === "number" ? `${(accuracy * 100).toFixed(2)}%` : null;
}

function datasetPartial(job: JobSummary) {
  if (job.kind !== "dataset-test" || !job.result) return false;
  const metric = job.result.metric;
  if (!metric || typeof metric !== "object" || Array.isArray(metric)) return false;
  const record = metric as Record<string, unknown>;
  return record.partial === true ||
    (Array.isArray(record.missingTasks) && record.missingTasks.length > 0);
}

export function JobCenter({ onOpenDatasetJob, inline = false }: JobCenterProps) {
  const [open, setOpen] = useState(false);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setJobs(await fetchJobs(30));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Local jobs are unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    void refresh();
    const timer = window.setInterval(() => void refresh(), 2500);
    return () => window.clearInterval(timer);
  }, [open, refresh]);

  useEffect(() => {
    if (!open) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  async function cancel(job: JobSummary) {
    try {
      await cancelJob(job.id);
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The job could not be cancelled.");
    }
  }

  const activeCount = jobs.filter(activeJob).length;

  return (
    <div className={`job-center${inline ? " inline" : ""}`}>
      <button
        type="button"
        className={`job-center-toggle${open ? " open" : ""}`}
        aria-label={open ? "Close job center" : "Open job center"}
        aria-expanded={open}
        aria-controls="job-center-panel"
        onClick={() => setOpen((current) => !current)}
      >
        <Activity size={16} />
        <span>Jobs</span>
        {activeCount > 0 && <b>{activeCount}</b>}
      </button>
      {open && (
        <section
          id="job-center-panel"
          className="job-center-panel"
          role="dialog"
          aria-label="Local job center"
        >
          <header>
            <div>
              <span>Local jobs</span>
              <h2>Activity</h2>
            </div>
            <div className="job-center-actions">
              <button
                type="button"
                aria-label="Refresh local jobs"
                disabled={loading}
                onClick={() => void refresh()}
              >
                <RefreshCw size={14} className={loading ? "spin" : ""} />
              </button>
              <button type="button" aria-label="Close job center panel" onClick={() => setOpen(false)}>
                <X size={15} />
              </button>
            </div>
          </header>
          {error && <p className="job-center-error" role="alert">{error}</p>}
          {!error && jobs.length === 0 && !loading && (
            <p className="job-center-empty">No local jobs yet. Start a chat run or dataset evaluation.</p>
          )}
          <div className="job-center-list">
            {jobs.map((job) => (
              <article key={job.id} className={`job-center-card ${job.status}`}>
                <header>
                  <span>{JOB_KIND_LABELS[job.kind] ?? job.kind}</span>
                  <b>{jobStatusLabel(job)}</b>
                </header>
                <p>{job.detail}</p>
                {activeJob(job) && (
                  <div className="job-center-progress">
                    <i style={{ width: `${job.progress}%` }} />
                  </div>
                )}
                <footer>
                  <small>{jobTime(job.createdAt)} · {job.id.slice(0, 8)}</small>
                  <div>
                    {datasetScore(job) && (
                      <strong>
                        {datasetPartial(job) ? "Partial · " : ""}
                        {datasetScore(job)}
                      </strong>
                    )}
                    {activeJob(job) && (
                      <button type="button" onClick={() => void cancel(job)}>Cancel</button>
                    )}
                    {job.kind === "dataset-test" && onOpenDatasetJob && (
                      <button
                        type="button"
                        onClick={() => {
                          onOpenDatasetJob(job.id);
                          setOpen(false);
                        }}
                      >
                        Open
                      </button>
                    )}
                  </div>
                </footer>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
