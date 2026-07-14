import { useEffect, useState } from "react";
import { Check, CircleAlert, Clipboard } from "lucide-react";

import {
  jobFailureKindLabel,
  jobFailureRecovery,
  type JobFailure
} from "../jobFailure";

interface JobSnapshot {
  id: string;
  kind: string;
  status: string;
  stage: string;
  progress: number;
  createdAt: string;
  updatedAt: string;
}

interface JobFailureDetailsProps {
  failure: JobFailure;
  job: JobSnapshot | null;
  jobLabel: string;
}

export function JobFailureDetails({ failure, job, jobLabel }: JobFailureDetailsProps) {
  const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "failed">("idle");

  useEffect(() => setCopyStatus("idle"), [failure]);

  async function copyDiagnostics() {
    const diagnostics = {
      schemaVersion: "1.0",
      kind: "safelens-job-error",
      category: failure.kind,
      phase: failure.phase,
      code: failure.code,
      serverCode: failure.serverCode ?? null,
      httpStatus: failure.httpStatus ?? null,
      message: failure.message,
      job: job ? {
        id: job.id,
        kind: job.kind,
        status: job.status,
        stage: job.stage,
        progress: job.progress,
        createdAt: job.createdAt,
        updatedAt: job.updatedAt
      } : null,
      context: jobLabel,
      url: window.location.href,
      userAgent: navigator.userAgent,
      occurredAt: failure.occurredAt,
      copiedAt: new Date().toISOString()
    };
    try {
      await navigator.clipboard.writeText(JSON.stringify(diagnostics, null, 2));
      setCopyStatus("copied");
    } catch {
      setCopyStatus("failed");
    }
  }

  return (
    <details className={`job-failure-details ${failure.kind}`}>
      <summary>
        <CircleAlert size={14} aria-hidden="true" />
        <span>Failure diagnostics</span>
        <b>{jobFailureKindLabel(failure.kind)}</b>
      </summary>
      <p>{jobFailureRecovery(failure)}</p>
      <dl>
        <div><dt>Phase</dt><dd>{failure.phase}</dd></div>
        <div><dt>Code</dt><dd><code>{failure.serverCode ?? failure.code}</code></dd></div>
        {failure.httpStatus !== undefined && (
          <div><dt>HTTP</dt><dd>{failure.httpStatus}</dd></div>
        )}
        {job && (
          <div><dt>Job</dt><dd><code>{job.id}</code></dd></div>
        )}
      </dl>
      <div className="job-failure-actions">
        <button type="button" onClick={() => void copyDiagnostics()}>
          {copyStatus === "copied" ? <Check size={14} /> : <Clipboard size={14} />}
          {copyStatus === "copied" ? "Diagnostics copied" : "Copy diagnostics"}
        </button>
        <span className={copyStatus === "failed" ? "failed" : ""} aria-live="polite">
          {copyStatus === "failed" ? "Copy failed" : "Source Run unchanged"}
        </span>
      </div>
    </details>
  );
}
