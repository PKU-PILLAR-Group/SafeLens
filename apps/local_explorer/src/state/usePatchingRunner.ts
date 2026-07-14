import { useCallback, useEffect, useRef, useState } from "react";

import {
  cancelPatchingJob,
  patchingJobSchema,
  promptJobEventsUrl,
  submitPatchingJob,
  type PatchingJob,
  type PatchingRunInput
} from "../api/explorerClient";
import type { ExplorerRun } from "../types";
import {
  jobComputationFailure,
  jobFailureFromError,
  jobProtocolFailure,
  jobStreamFailure,
  type JobFailure
} from "../jobFailure";

export function usePatchingRunner(onRunReady: (run: ExplorerRun, job: PatchingJob) => void) {
  const [job, setJob] = useState<PatchingJob | null>(null);
  const [error, setError] = useState<JobFailure | null>(null);
  const streamRef = useRef<EventSource | null>(null);
  const activeRef = useRef<{ id: string; generation: number } | null>(null);
  const generationRef = useRef(0);
  const deliveredRef = useRef(new Set<string>());

  const closeStream = useCallback(() => {
    streamRef.current?.close();
    streamRef.current = null;
  }, []);

  const applySnapshot = useCallback((snapshot: PatchingJob, generation: number) => {
    if (activeRef.current?.id !== snapshot.id || activeRef.current.generation !== generation) return;
    setJob(snapshot);
    setError(snapshot.status === "error"
      ? jobComputationFailure(snapshot.kind, snapshot.error ?? snapshot.detail)
      : null);
    if (snapshot.status === "ready" && snapshot.result && !deliveredRef.current.has(snapshot.id)) {
      deliveredRef.current.add(snapshot.id);
      closeStream();
      onRunReady(snapshot.result as ExplorerRun, snapshot);
    } else if (snapshot.status === "error" || snapshot.status === "cancelled") {
      closeStream();
    }
  }, [closeStream, onRunReady]);

  const submit = useCallback(async (input: PatchingRunInput) => {
    closeStream();
    const generation = ++generationRef.current;
    activeRef.current = { id: "submitting", generation };
    setJob(null);
    setError(null);
    try {
      const submitted = await submitPatchingJob(input);
      if (activeRef.current?.generation !== generation) return;
      activeRef.current = { id: submitted.id, generation };
      setJob(submitted);
      const stream = new EventSource(promptJobEventsUrl(submitted.id));
      streamRef.current = stream;
      stream.addEventListener("job", (event) => {
        if (!(event instanceof MessageEvent)) return;
        let input: unknown;
        try {
          input = JSON.parse(event.data);
        } catch {
          closeStream();
          setError(jobProtocolFailure(
            "Patching progress stream returned invalid JSON.",
            "patching_stream_invalid_json"
          ));
          return;
        }
        const parsed = patchingJobSchema.safeParse(input);
        if (!parsed.success) {
          closeStream();
          setError(jobProtocolFailure(
            "Patching progress payload failed validation.",
            "patching_stream_invalid_schema"
          ));
          return;
        }
        applySnapshot(parsed.data, generation);
      });
      stream.onerror = () => {
        if (activeRef.current?.generation !== generation) return;
        closeStream();
        setError((current) => current ?? jobStreamFailure(
          "Patching progress stream disconnected. Retry the job."
        ));
      };
    } catch (caught) {
      if (activeRef.current?.generation !== generation) return;
      activeRef.current = null;
      setError(jobFailureFromError(caught, "submission", "Patching submission failed."));
    }
  }, [applySnapshot, closeStream]);

  const cancel = useCallback(async () => {
    const active = activeRef.current;
    if (!active || active.id === "submitting") return;
    try {
      applySnapshot(await cancelPatchingJob(active.id), active.generation);
    } catch (caught) {
      setError(jobFailureFromError(caught, "cancellation", "Patching cancellation failed."));
    }
  }, [applySnapshot]);

  const reset = useCallback(() => {
    closeStream();
    generationRef.current += 1;
    activeRef.current = null;
    setJob(null);
    setError(null);
  }, [closeStream]);

  useEffect(() => () => {
    const active = activeRef.current;
    closeStream();
    if (active && active.id !== "submitting") void cancelPatchingJob(active.id).catch(() => undefined);
  }, [closeStream]);

  return { job, error, submit, cancel, reset, submitting: activeRef.current?.id === "submitting" };
}
