import { useCallback, useEffect, useRef, useState } from "react";

import {
  cancelInterventionJob,
  interventionJobSchema,
  promptJobEventsUrl,
  submitInterventionJob,
  type InterventionJob,
  type InterventionRunInput
} from "../api/explorerClient";
import type { ExplorerRun } from "../types";
import {
  jobComputationFailure,
  jobFailureFromError,
  jobProtocolFailure,
  jobStreamFailure,
  type JobFailure
} from "../jobFailure";

export function useInterventionRunner(
  onRunReady: (run: ExplorerRun, job: InterventionJob) => void
) {
  const [job, setJob] = useState<InterventionJob | null>(null);
  const [error, setError] = useState<JobFailure | null>(null);
  const streamRef = useRef<EventSource | null>(null);
  const activeRef = useRef<{ id: string; generation: number } | null>(null);
  const generationRef = useRef(0);
  const deliveredRef = useRef(new Set<string>());

  const closeStream = useCallback(() => {
    streamRef.current?.close();
    streamRef.current = null;
  }, []);

  const applySnapshot = useCallback((snapshot: InterventionJob, generation: number) => {
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

  const submit = useCallback(async (input: InterventionRunInput) => {
    closeStream();
    const generation = ++generationRef.current;
    activeRef.current = { id: "submitting", generation };
    setJob(null);
    setError(null);
    try {
      const submitted = await submitInterventionJob(input);
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
            "Intervention progress stream returned invalid JSON.",
            "intervention_stream_invalid_json"
          ));
          return;
        }
        const parsed = interventionJobSchema.safeParse(input);
        if (!parsed.success) {
          closeStream();
          setError(jobProtocolFailure(
            "Intervention progress payload failed validation.",
            "intervention_stream_invalid_schema"
          ));
          return;
        }
        applySnapshot(parsed.data, generation);
      });
      stream.onerror = () => {
        if (activeRef.current?.generation !== generation) return;
        closeStream();
        setError((current) => current ?? jobStreamFailure(
          "Intervention progress stream disconnected. Retry the job."
        ));
      };
    } catch (caught) {
      if (activeRef.current?.generation !== generation) return;
      activeRef.current = null;
      setError(jobFailureFromError(caught, "submission", "Intervention submission failed."));
    }
  }, [applySnapshot, closeStream]);

  const cancel = useCallback(async () => {
    const active = activeRef.current;
    if (!active || active.id === "submitting") return;
    try {
      applySnapshot(await cancelInterventionJob(active.id), active.generation);
    } catch (caught) {
      setError(jobFailureFromError(caught, "cancellation", "Intervention cancellation failed."));
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
    if (active && active.id !== "submitting") void cancelInterventionJob(active.id).catch(() => undefined);
  }, [closeStream]);

  return { job, error, submit, cancel, reset, submitting: activeRef.current?.id === "submitting" };
}
