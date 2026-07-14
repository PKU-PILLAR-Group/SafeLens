import { useCallback, useEffect, useRef, useState } from "react";

import {
  cancelPromptJob,
  promptJobEventsUrl,
  promptJobSchema,
  submitPromptJob,
  type PromptJob,
  type PromptRunInput
} from "../api/explorerClient";
import type { ExplorerRun } from "../types";
import {
  jobComputationFailure,
  jobFailureFromError,
  jobProtocolFailure,
  jobStreamFailure,
  type JobFailure
} from "../jobFailure";

interface PromptRunnerState {
  job: PromptJob | null;
  error: JobFailure | null;
}

export function usePromptRunner(onRunReady: (run: ExplorerRun, job: PromptJob) => void) {
  const [state, setState] = useState<PromptRunnerState>({ job: null, error: null });
  const streamRef = useRef<EventSource | null>(null);
  const activeRef = useRef<{ id: string; generation: number } | null>(null);
  const generationRef = useRef(0);
  const deliveredRef = useRef(new Set<string>());

  const closeStream = useCallback(() => {
    streamRef.current?.close();
    streamRef.current = null;
  }, []);

  const applySnapshot = useCallback((snapshot: PromptJob, generation: number) => {
    if (activeRef.current?.id !== snapshot.id || activeRef.current.generation !== generation) return;
    setState({
      job: snapshot,
      error: snapshot.status === "error"
        ? jobComputationFailure(snapshot.kind, snapshot.error ?? snapshot.detail)
        : null
    });
    if (snapshot.status === "ready" && snapshot.result && !deliveredRef.current.has(snapshot.id)) {
      deliveredRef.current.add(snapshot.id);
      closeStream();
      onRunReady(snapshot.result as ExplorerRun, snapshot);
    } else if (snapshot.status === "error" || snapshot.status === "cancelled") {
      closeStream();
    }
  }, [closeStream, onRunReady]);

  const submit = useCallback(async (input: PromptRunInput) => {
    closeStream();
    const generation = ++generationRef.current;
    activeRef.current = { id: "submitting", generation };
    setState({ job: null, error: null });
    try {
      const submitted = await submitPromptJob(input);
      if (activeRef.current?.generation !== generation) return;
      activeRef.current = { id: submitted.id, generation };
      setState({ job: submitted, error: null });
      const stream = new EventSource(promptJobEventsUrl(submitted.id));
      streamRef.current = stream;
      stream.addEventListener("job", (event) => {
        if (!(event instanceof MessageEvent)) return;
        let input: unknown;
        try {
          input = JSON.parse(event.data);
        } catch {
          closeStream();
          setState((current) => ({
            ...current,
            error: jobProtocolFailure(
              "Prompt progress stream returned invalid JSON.",
              "prompt_stream_invalid_json"
            )
          }));
          return;
        }
        const parsed = promptJobSchema.safeParse(input);
        if (!parsed.success) {
          closeStream();
          setState((current) => ({
            ...current,
            error: jobProtocolFailure(
              "Prompt progress payload failed validation.",
              "prompt_stream_invalid_schema"
            )
          }));
          return;
        }
        applySnapshot(parsed.data, generation);
      });
      stream.onerror = () => {
        if (activeRef.current?.generation !== generation) return;
        closeStream();
        setState((current) => ({
          ...current,
          error: current.job?.status === "ready" || current.job?.status === "cancelled"
            ? current.error
            : current.error ?? jobStreamFailure("Prompt progress stream disconnected. Retry the job.")
        }));
      };
    } catch (error) {
      if (activeRef.current?.generation !== generation) return;
      activeRef.current = null;
      setState({
        job: null,
        error: jobFailureFromError(error, "submission", "Prompt job submission failed.")
      });
    }
  }, [applySnapshot, closeStream]);

  const cancel = useCallback(async () => {
    const active = activeRef.current;
    if (!active || active.id === "submitting") return;
    try {
      const snapshot = await cancelPromptJob(active.id);
      applySnapshot(snapshot, active.generation);
    } catch (error) {
      setState((current) => ({
        ...current,
        error: jobFailureFromError(error, "cancellation", "Prompt job cancellation failed.")
      }));
    }
  }, [applySnapshot]);

  const reset = useCallback(() => {
    closeStream();
    generationRef.current += 1;
    activeRef.current = null;
    setState({ job: null, error: null });
  }, [closeStream]);

  useEffect(() => () => {
    const active = activeRef.current;
    closeStream();
    if (active && active.id !== "submitting") void cancelPromptJob(active.id).catch(() => undefined);
  }, [closeStream]);

  return { ...state, submit, cancel, reset, submitting: activeRef.current?.id === "submitting" };
}
