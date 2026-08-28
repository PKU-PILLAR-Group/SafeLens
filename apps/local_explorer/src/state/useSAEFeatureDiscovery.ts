import { useCallback, useEffect, useRef, useState } from "react";

import {
  cancelSAEFeatureDiscoveryJob,
  promptJobEventsUrl,
  saeFeatureDiscoveryJobSchema,
  submitSAEFeatureDiscoveryJob,
  type SAEFeatureDiscoveryInput,
  type SAEFeatureDiscoveryJob,
  type SAEFeatureDiscoveryResult
} from "../api/explorerClient";
import {
  jobComputationFailure,
  jobFailureFromError,
  jobProtocolFailure,
  jobStreamFailure,
  type JobFailure
} from "../jobFailure";

export function useSAEFeatureDiscovery(
  onReady: (result: SAEFeatureDiscoveryResult) => void
) {
  const [job, setJob] = useState<SAEFeatureDiscoveryJob | null>(null);
  const [error, setError] = useState<JobFailure | null>(null);
  const streamRef = useRef<EventSource | null>(null);
  const activeRef = useRef<{ id: string; generation: number } | null>(null);
  const generationRef = useRef(0);

  const closeStream = useCallback(() => {
    streamRef.current?.close();
    streamRef.current = null;
  }, []);

  const applySnapshot = useCallback((snapshot: SAEFeatureDiscoveryJob, generation: number) => {
    if (activeRef.current?.id !== snapshot.id || activeRef.current.generation !== generation) return;
    setJob(snapshot);
    setError(snapshot.status === "error"
      ? jobComputationFailure(snapshot.kind, snapshot.error ?? snapshot.detail)
      : null);
    if (snapshot.status === "ready" && snapshot.result) {
      closeStream();
      activeRef.current = null;
      onReady(snapshot.result);
    } else if (snapshot.status === "error" || snapshot.status === "cancelled") {
      closeStream();
      activeRef.current = null;
    }
  }, [closeStream, onReady]);

  const submit = useCallback(async (input: SAEFeatureDiscoveryInput) => {
    closeStream();
    const generation = ++generationRef.current;
    activeRef.current = { id: "submitting", generation };
    setJob(null);
    setError(null);
    try {
      const submitted = await submitSAEFeatureDiscoveryJob(input);
      if (activeRef.current?.generation !== generation) return;
      activeRef.current = { id: submitted.id, generation };
      setJob(submitted);
      const stream = new EventSource(promptJobEventsUrl(submitted.id));
      streamRef.current = stream;
      stream.addEventListener("job", (event) => {
        if (!(event instanceof MessageEvent)) return;
        let payload: unknown;
        try {
          payload = JSON.parse(event.data);
        } catch {
          closeStream();
          setError(jobProtocolFailure(
            "SAE discovery progress stream returned invalid JSON.",
            "sae_discovery_stream_invalid_json"
          ));
          return;
        }
        const parsed = saeFeatureDiscoveryJobSchema.safeParse(payload);
        if (!parsed.success) {
          closeStream();
          setError(jobProtocolFailure(
            "SAE discovery progress payload failed validation.",
            "sae_discovery_stream_invalid_schema"
          ));
          return;
        }
        applySnapshot(parsed.data, generation);
      });
      stream.onerror = () => {
        if (activeRef.current?.generation !== generation) return;
        closeStream();
        setError((current) => current ?? jobStreamFailure(
          "SAE discovery progress stream disconnected. Retry the scan."
        ));
      };
    } catch (caught) {
      if (activeRef.current?.generation !== generation) return;
      activeRef.current = null;
      setError(jobFailureFromError(caught, "submission", "SAE feature discovery failed."));
    }
  }, [applySnapshot, closeStream]);

  const cancel = useCallback(async () => {
    const active = activeRef.current;
    if (!active || active.id === "submitting") return;
    try {
      applySnapshot(await cancelSAEFeatureDiscoveryJob(active.id), active.generation);
    } catch (caught) {
      setError(jobFailureFromError(caught, "cancellation", "SAE discovery cancellation failed."));
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
    if (active && active.id !== "submitting") {
      void cancelSAEFeatureDiscoveryJob(active.id).catch(() => undefined);
    }
  }, [closeStream]);

  return {
    job,
    error,
    submit,
    cancel,
    reset,
    running: activeRef.current !== null
  };
}
