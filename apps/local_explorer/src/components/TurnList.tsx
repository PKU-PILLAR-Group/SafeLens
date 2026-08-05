import { useEffect, useRef } from "react";

import type { TurnView } from "../state/useTurnManager";
import type { ExplorerRun } from "../types";
import { TurnCard, type AnalysisId } from "./TurnCard";

interface TurnListProps {
  turns: TurnView[];
  activeTurnId: string | null;
  analysisOpen: { turnId: string; mode: AnalysisId } | null;
  onRetry: (turnId: string) => void;
  onCancel: (turnId: string) => void;
  onToggleAnalysis: (turnId: string, mode: AnalysisId) => void;
  onRunReady: (run: ExplorerRun, job: { id: string; kind: "prompt-run" | "attribution" | "intervention" }) => void;
}

export function TurnList({
  turns,
  activeTurnId,
  analysisOpen,
  onRetry,
  onCancel,
  onToggleAnalysis,
  onRunReady
}: TurnListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [turns.length]);

  return (
    <div className="chat-turn-list" aria-label="Conversation turns">
      {turns.map((turn) => (
        <TurnCard
          key={turn.id}
          turn={turn}
          active={turn.id === activeTurnId}
          analysisOpen={analysisOpen?.turnId === turn.id ? analysisOpen.mode : null}
          onRetry={() => onRetry(turn.id)}
          onCancel={() => onCancel(turn.id)}
          onToggleAnalysis={(mode) => onToggleAnalysis(turn.id, mode)}
          onRunReady={onRunReady}
        />
      ))}
      <div ref={endRef} />
    </div>
  );
}
