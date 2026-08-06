import { useCallback, useEffect, useRef, useState } from "react";

import type { PromptJob, PromptMessage } from "../api/explorerClient";
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
  const turnsRef = useRef<TurnView[]>([]);
  turnsRef.current = turns;
  const conversationIdRef = useRef(conversationId);
  conversationIdRef.current = conversationId;
  const activeTurnIdRef = useRef<string | null>(null);
  activeTurnIdRef.current = activeTurnId;

  function contextMessages(sourceTurns: TurnView[], excludeId?: string): PromptMessage[] {
    return sourceTurns
      .filter((turn) => turn.id !== excludeId && turn.run && turn.status === "ready")
      .flatMap((turn) => {
        const response = generatedResponse(turn.run!);
        return response ? [
          { role: "user" as const, content: turn.prompt },
          { role: "assistant" as const, content: response }
        ] : [];
      });
  }

  const handleRunReady = useCallback((run: ExplorerRun, job: PromptJob) => {
    const turnId = activeTurnIdRef.current;
    if (!turnId) return;
    const turnIndex = turnsRef.current.findIndex((turn) => turn.id === turnId);
    const conversation = conversationIdRef.current;
    const persistedRun: ExplorerRun = {
      ...run,
      metadata: {
        ...run.metadata,
        ...(conversation ? { conversationId: conversation } : {}),
        ...(turnIndex >= 0 ? { turnIndex } : {})
      }
    };
    setTurns((current) => current.map((turn) =>
      turn.id === turnId
        ? { ...turn, run: persistedRun, status: "ready" as const, jobId: job.id }
        : turn
    ));
    setActiveTurnId(null);
    onRunReady(persistedRun, job, turnId);
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
    const hadConversation = Boolean(conversationIdRef.current);
    const nextConversationId = conversationIdRef.current ?? crypto.randomUUID();
    conversationIdRef.current = nextConversationId;
    if (!hadConversation) onConversationStart(nextConversationId);
    const messages = contextMessages(turns);
    const turn: TurnView = {
      id: crypto.randomUUID(),
      prompt,
      run: null,
      jobId: null,
      status: "pending",
      startedAt: new Date().toISOString()
    };
    setTurns((current) => [...current, turn]);
    activeTurnIdRef.current = turn.id;
    setActiveTurnId(turn.id);
    void runner.submit({
      prompt,
      template: "chat",
      model,
      seed: 0,
      maxNewTokens: 8,
      temperature: 0,
      messages
    });
  }, [conversationId, model, onConversationStart, runner, turns]);

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
    activeTurnIdRef.current = turnId;
    setActiveTurnId(turnId);
    const turnIndex = turns.findIndex((item) => item.id === turnId);
    void runner.submit({
      prompt: turn.prompt,
      template: "chat",
      model,
      seed: 0,
      maxNewTokens: 8,
      temperature: 0,
      messages: contextMessages(turns.slice(0, Math.max(0, turnIndex)), turnId)
    });
  }, [model, runner, turns]);

  const reset = useCallback(() => {
    runner.reset();
    activeTurnIdRef.current = null;
    setTurns([]);
    setActiveTurnId(null);
  }, [runner]);

  const hydrate = useCallback((nextTurns: TurnView[], nextConversationId: string) => {
    runner.reset();
    activeTurnIdRef.current = null;
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

function generatedResponse(run: ExplorerRun): string {
  const generated = run.metadata?.generatedContinuation;
  if (typeof generated !== "string" || !generated.trim()) return "";
  const userPrompt = run.metadata?.promptRunner;
  const promptRunner = userPrompt && typeof userPrompt === "object"
    ? userPrompt as Record<string, unknown>
    : undefined;
  const sourcePrompt = typeof promptRunner?.userPrompt === "string"
    ? promptRunner.userPrompt
    : run.prompt;
  return (generated.startsWith(run.prompt) ? generated.slice(run.prompt.length) : generated.startsWith(sourcePrompt) ? generated.slice(sourcePrompt.length) : generated).trim();
}
