import { useCallback, useEffect, useRef, useState } from "react";

import type { PromptJob } from "../api/explorerClient";
import { usePromptRunner } from "./usePromptRunner";
import type { ExplorerRun } from "../types";
import type { TurnView } from "../components/TurnCard";

export type { TurnView };

interface UseTurnManagerOptions {
  model: string;
  conversationId: string | null;
  onConversationStart: (id: string) => void;
  onRunReady: (run: ExplorerRun, job: PromptJob, turnId: string) => void;
}

export function useTurnManager({
  model,
  conversationId,
  onConversationStart,
  onRunReady
}: UseTurnManagerOptions) {
  const [turns, setTurns] = useState<TurnView[]>([]);
  const [activeTurnId, setActiveTurnId] = useState<string | null>(null);
  const conversationIdRef = useRef(conversationId);
  conversationIdRef.current = conversationId;
  const activeTurnIdRef = useRef<string | null>(null);
  activeTurnIdRef.current = activeTurnId;

  const handleRunReady = useCallback((run: ExplorerRun, job: PromptJob) => {
    const turnId = activeTurnIdRef.current;
    if (!turnId) return;
    setTurns((current) => current.map((turn) =>
      turn.id === turnId
        ? { ...turn, run, status: "ready" as const, jobId: job.id }
        : turn
    ));
    setActiveTurnId(null);
    onRunReady(run, job, turnId);
  }, [onRunReady]);

  const runner = usePromptRunner(handleRunReady);

  useEffect(() => {
    if (!runner.error || !activeTurnId) return;
    const message = runner.error.message;
    setTurns((current) => current.map((turn) =>
      turn.id === activeTurnId
        ? { ...turn, status: "error" as const, errorMessage: message }
        : turn
    ));
    setActiveTurnId(null);
  }, [activeTurnId, runner.error]);

  useEffect(() => {
    if (!runner.job || !activeTurnId) return;
    if (runner.job.status === "cancelled") {
      setTurns((current) => current.map((turn) =>
        turn.id === activeTurnId
          ? { ...turn, status: "cancelled" as const }
          : turn
      ));
      setActiveTurnId(null);
    }
  }, [activeTurnId, runner.job]);

  const submit = useCallback((prompt: string) => {
    if (activeTurnIdRef.current) return;
    if (!conversationIdRef.current) {
      onConversationStart(crypto.randomUUID());
    }
    const turn: TurnView = {
      id: crypto.randomUUID(),
      prompt,
      run: null,
      jobId: null,
      status: "pending",
      startedAt: new Date().toISOString()
    };
    setTurns((current) => [...current, turn]);
    setActiveTurnId(turn.id);
    void runner.submit({
      prompt,
      template: "chat",
      model,
      seed: 0,
      maxNewTokens: 8,
      temperature: 0
    });
  }, [model, onConversationStart, runner]);

  const cancel = useCallback((turnId: string) => {
    if (activeTurnIdRef.current !== turnId) return;
    void runner.cancel();
  }, [runner]);

  const retry = useCallback((turnId: string) => {
    if (activeTurnIdRef.current) return;
    const turn = turns.find((item) => item.id === turnId);
    if (!turn || turn.status === "pending") return;
    setTurns((current) => current.map((item) =>
      item.id === turnId
        ? { ...item, status: "pending" as const, errorMessage: undefined, run: null }
        : item
    ));
    setActiveTurnId(turnId);
    void runner.submit({
      prompt: turn.prompt,
      template: "chat",
      model,
      seed: 0,
      maxNewTokens: 8,
      temperature: 0
    });
  }, [model, runner, turns]);

  const reset = useCallback(() => {
    runner.reset();
    setTurns([]);
    setActiveTurnId(null);
  }, [runner]);

  const hydrate = useCallback((nextTurns: TurnView[], nextConversationId: string) => {
    runner.reset();
    setTurns(nextTurns);
    setActiveTurnId(null);
    onConversationStart(nextConversationId);
  }, [onConversationStart, runner]);

  return {
    turns,
    activeTurnId,
    submit,
    cancel,
    retry,
    reset,
    hydrate
  };
}
