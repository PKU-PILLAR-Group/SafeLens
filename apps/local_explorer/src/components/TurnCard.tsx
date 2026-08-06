import {
  BrainCircuit,
  CheckCircle2,
  CircleStop,
  LoaderCircle,
  RefreshCw,
  ScanSearch,
  SlidersHorizontal
} from "lucide-react";

import type { ExplorerRun } from "../types";
import { ChatAnalysisWorkbench } from "./ChatAnalysisWorkbench";

export type AnalysisId = "steering" | "attribution";

export interface TurnView {
  id: string;
  prompt: string;
  run: ExplorerRun | null;
  jobId: string | null;
  status: "pending" | "ready" | "error" | "cancelled";
  errorMessage?: string;
  startedAt: string;
}

interface TurnCardProps {
  turn: TurnView;
  analysisRuns: ExplorerRun[];
  active: boolean;
  analysisOpen: AnalysisId | null;
  onRetry: () => void;
  onCancel: () => void;
  onToggleAnalysis: (mode: AnalysisId) => void;
  onRunReady: (run: ExplorerRun, job: { id: string; kind: "prompt-run" | "attribution" | "intervention" }) => void;
}

export function TurnCard({
  turn,
  analysisRuns,
  active,
  analysisOpen,
  onRetry,
  onCancel,
  onToggleAnalysis,
  onRunReady
}: TurnCardProps) {
  const savedRun = turn.run && analysisOpen
    ? analysisRuns.find((candidate) => {
        const parent = candidate.metadata?.parentRun;
        if (!parent || typeof parent !== "object" || Array.isArray(parent)) return false;
        const source = parent as Record<string, unknown>;
        const belongsToTurn = source.runId === turn.run?.runId && source.sampleId === turn.run?.sampleId;
        if (!belongsToTurn) return false;
        return analysisOpen === "steering"
          ? Boolean(candidate.intervention)
          : candidate.attributionMethods.some(
              (method) => method.id === "integrated_gradients" && method.available
            );
      })
    : undefined;
  return (
    <article className="chat-turn-card" aria-label="Conversation turn">
      <div className="chat-user-message">{turn.prompt}</div>
      <div className="chat-assistant-message">
        <span className="chat-assistant-mark"><BrainCircuit size={20} /></span>
        <div>
          {turn.run ? (
            <>
              <p>{generatedResponse(turn.run)}</p>
              <span className="chat-run-ready"><CheckCircle2 size={14} /> Activation cache ready</span>
            </>
          ) : turn.status === "error" ? (
            <>
              <p>{turn.errorMessage ?? "The analysis job failed."}</p>
              <button onClick={onRetry}>Retry</button>
            </>
          ) : (
            <div className="chat-job-progress">
              <span><LoaderCircle size={16} /> Running the analysis...</span>
              <i><b style={{ width: `${active ? 50 : 4}%` }} /></i>
              <small>{active ? "in progress" : "queued"}</small>
              {active && <button aria-label="Cancel analysis" onClick={onCancel}><CircleStop size={16} /></button>}
              {turn.status === "cancelled" && (
                <button aria-label="Retry analysis" title="Retry analysis" onClick={onRetry}>
                  <RefreshCw size={15} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
      {turn.run && (
        <>
          <div className="chat-turn-explore-bar" aria-label="Explore this run">
            <button
              type="button"
              className={analysisOpen === "steering" ? "active" : ""}
              aria-pressed={analysisOpen === "steering"}
              onClick={() => onToggleAnalysis("steering")}
            >
              <SlidersHorizontal size={16} /> Steer
            </button>
            <button
              type="button"
              className={analysisOpen === "attribution" ? "active" : ""}
              aria-pressed={analysisOpen === "attribution"}
              onClick={() => onToggleAnalysis("attribution")}
            >
              <ScanSearch size={16} /> Attribute
            </button>
          </div>
          {analysisOpen && (
            <div className="chat-turn-analysis">
              <ChatAnalysisWorkbench
                key={`${turn.run.runId}:${turn.run.sampleId}:${analysisOpen}`}
                mode={analysisOpen}
                run={turn.run}
                savedRun={savedRun}
                suggestionQuery={turn.prompt}
                onRunReady={onRunReady}
              />
            </div>
          )}
        </>
      )}
    </article>
  );
}

function generatedResponse(run: ExplorerRun) {
  const generated = run.metadata?.generatedContinuation;
  if (typeof generated !== "string" || !generated.trim()) {
    return "The model run is complete and its internal activations are ready to inspect.";
  }
  const promptRunner = run.metadata?.promptRunner;
  const userPrompt = promptRunner && typeof promptRunner === "object"
    ? (promptRunner as Record<string, unknown>).userPrompt
    : undefined;
  const response = generated.startsWith(run.prompt)
    ? generated.slice(run.prompt.length).trim()
    : typeof userPrompt === "string" && generated.startsWith(userPrompt)
      ? generated.slice(userPrompt.length).trim()
      : generated.trim();
  return response || "The model run is complete and its internal activations are ready to inspect.";
}
