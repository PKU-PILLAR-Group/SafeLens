import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  CircleStop,
  GitCompareArrows,
  LoaderCircle,
  Network,
  RefreshCw,
  ScanSearch,
  SlidersHorizontal,
  Sparkles
} from "lucide-react";

import type { RemoteRunSummary } from "../api/explorerClient";
import type { ExplorerRun } from "../types";
import { generatedResponseText } from "../generatedResponse";
import { ChatAnalysisWorkbench } from "./ChatAnalysisWorkbench";

export type AnalysisId = "steering" | "attribution" | "patching" | "neuron" | "feature" | "explanation" | "attention";

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
  remoteSummary?: RemoteRunSummary;
  analysisRuns: ExplorerRun[];
  active: boolean;
  showAnalysisControls: boolean;
  analysisOpen: AnalysisId | null;
  onRetry: () => void;
  onCancel: () => void;
  onToggleAnalysis: (mode: AnalysisId) => void;
  onRunReady: (run: ExplorerRun, job: { id: string; kind: "prompt-run" | "attribution" | "intervention" | "patching" | "nla" | "jlens" }) => void;
}

export function TurnCard({
  turn,
  remoteSummary,
  analysisRuns,
  active,
  showAnalysisControls,
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
        if (analysisOpen === "steering") return candidate.intervention?.mode === "direction";
        if (analysisOpen === "patching") return Boolean(candidate.patching);
        if (analysisOpen === "attribution") return candidate.attributionMethods.some(
              (method) => method.id === "integrated_gradients" && method.available
            );
        if (analysisOpen === "neuron") return candidate.intervention?.mode === "neuron";
        if (analysisOpen === "feature") return candidate.intervention?.mode === "sae_feature";
        if (analysisOpen === "explanation") {
          return candidate.nla.some((row) => row.status === "available") || candidate.jLens.length > 0;
        }
        return false;
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
              <p>{generatedResponseText(turn.run) || "The model run is complete and its internal activations are ready to inspect."}</p>
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
      {turn.run && showAnalysisControls && (
        <>
          <div className="chat-turn-explore-bar" aria-label="Explore this run">
            <button
              type="button"
              className={analysisOpen === "neuron" ? "active" : ""}
              aria-pressed={analysisOpen === "neuron"}
              onClick={() => onToggleAnalysis("neuron")}
            >
              <Activity size={16} /> Neuron
            </button>
            <button
              type="button"
              className={analysisOpen === "feature" ? "active" : ""}
              aria-pressed={analysisOpen === "feature"}
              onClick={() => onToggleAnalysis("feature")}
            >
              <Activity size={16} /> SAE
            </button>
            <button
              type="button"
              className={analysisOpen === "patching" ? "active" : ""}
              aria-pressed={analysisOpen === "patching"}
              onClick={() => onToggleAnalysis("patching")}
            >
              <GitCompareArrows size={16} /> Patch
            </button>
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
            <button
              type="button"
              className={analysisOpen === "explanation" ? "active" : ""}
              aria-pressed={analysisOpen === "explanation"}
              onClick={() => onToggleAnalysis("explanation")}
            >
              <Sparkles size={16} /> Explain
            </button>
            <button
              type="button"
              className={analysisOpen === "attention" ? "active" : ""}
              aria-pressed={analysisOpen === "attention"}
              onClick={() => onToggleAnalysis("attention")}
            >
              <Network size={16} /> Attention
            </button>
          </div>
          {analysisOpen && (
            <div className="chat-turn-analysis">
              <ChatAnalysisWorkbench
                key={`${turn.run.runId}:${turn.run.sampleId}:${analysisOpen}`}
                mode={analysisOpen}
                run={turn.run}
                remoteSummary={remoteSummary}
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
