import { useEffect, useRef, useState } from "react";

import type { AsyncStatus } from "./AsyncStatePanel";

type JobProgressTone = "prompt" | "attribution" | "nla" | "causal";

interface JobProgressSnapshot {
  status: "idle" | "loading" | "ready" | "error" | "cancelled";
  stage: string;
  progress: number;
  createdAt: string;
  updatedAt: string;
}

interface JobProgressProps {
  job: JobProgressSnapshot | null;
  status: AsyncStatus;
  submitting: boolean;
  ariaLabel: string;
  tone: JobProgressTone;
}

export function JobProgress({
  job,
  status,
  submitting,
  ariaLabel,
  tone
}: JobProgressProps) {
  const mountedAt = useRef(performance.now());
  const active = status !== "error" && (
    submitting || job?.status === "idle" || job?.status === "loading"
  );
  const [now, setNow] = useState(() => performance.now());
  const observedSnapshot = useRef({ updatedAt: job?.updatedAt, at: performance.now() });

  if (observedSnapshot.current.updatedAt !== job?.updatedAt) {
    observedSnapshot.current = { updatedAt: job?.updatedAt, at: performance.now() };
  }

  useEffect(() => {
    if (!active) return;
    setNow(performance.now());
    const interval = window.setInterval(() => setNow(performance.now()), 1_000);
    return () => window.clearInterval(interval);
  }, [active]);

  const progress = clampProgress(job?.progress ?? 0);
  const stage = submitting ? "Submitting" : readableStage(job?.stage, status);
  const startedAt = parseTimestamp(job?.createdAt);
  const recordedEnd = parseTimestamp(job?.updatedAt);
  const recordedSeconds = startedAt !== null && recordedEnd !== null
    ? Math.max(0, Math.floor((recordedEnd - startedAt) / 1_000))
    : 0;
  const observedAt = job ? observedSnapshot.current.at : mountedAt.current;
  const liveSeconds = active ? Math.max(0, Math.floor((now - observedAt) / 1_000)) : 0;
  const elapsedSeconds = recordedSeconds + liveSeconds;
  const elapsed = formatElapsed(elapsedSeconds);

  return (
    <div className={`job-progress ${tone} ${active ? "active" : "terminal"}`} aria-label={ariaLabel}>
      <div className="job-progress-metrics">
        <div>
          <span>Stage</span>
          <strong title={stage}>{stage}</strong>
        </div>
        <div>
          <span>Progress</span>
          <strong>{progress}%</strong>
        </div>
        <div>
          <span>Elapsed</span>
          <time dateTime={`PT${elapsedSeconds}S`}>{elapsed}</time>
        </div>
      </div>
      <div
        className="job-progress-track"
        role="progressbar"
        aria-label={`${ariaLabel} completion`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progress}
        aria-valuetext={`${progress}% complete; ${stage}; elapsed ${elapsed}`}
      >
        <span style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

function clampProgress(value: number) {
  return Math.max(0, Math.min(100, Math.round(Number.isFinite(value) ? value : 0)));
}

function parseTimestamp(value: string | undefined) {
  if (!value) return null;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function readableStage(stage: string | undefined, status: AsyncStatus) {
  const value = stage?.trim() || status;
  return value
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase())
    .replace(/\b(nla|av|ar)\b/gi, (word) => word.toUpperCase());
}

function formatElapsed(totalSeconds: number) {
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const hours = Math.floor(totalSeconds / 3_600);
  const minutes = Math.floor((totalSeconds % 3_600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m ${seconds}s`;
}
