import { useEffect, useMemo, useRef, useState } from "react";
import {
  BrainCircuit,
  MessageSquareText,
  PanelLeftOpen,
  Paperclip,
  Play,
  LoaderCircle,
  SquarePen,
  Trash2,
  X
} from "lucide-react";

import { fetchPromptOptions } from "../api/explorerClient";
import { useTurnManager } from "../state/useTurnManager";
import {
  listConversations,
  type ConversationSummary,
  type RemoteRunState,
  type RunRecord
} from "../state/useRunLibrary";
import type { ExplorerRun } from "../types";
import { TurnList } from "./TurnList";
import type { TurnView } from "../state/useTurnManager";
import type { AnalysisId } from "./TurnCard";

const DEFAULT_MODEL = "sshleifer/tiny-gpt2";
const HIDDEN_RUN_STORAGE_KEY = "safelens.localExplorer.hiddenWork.v1";

interface ExplorerHomeProps {
  records: RunRecord[];
  activeRecord: RunRecord & { run: ExplorerRun };
  remoteState: RemoteRunState;
  onSelectConversation: (key: string) => void;
  onRunReady: (run: ExplorerRun, job: { id: string; kind: "prompt-run" | "attribution" | "intervention" }) => void;
  onRemoveRuns: (keys: string[]) => void;
}

export function ExplorerHome({
  records,
  activeRecord,
  remoteState,
  onSelectConversation,
  onRunReady,
  onRemoveRuns
}: ExplorerHomeProps) {
  const [prompt, setPrompt] = useState("");
  const [sourceKey, setSourceKey] = useState(activeRecord.key);
  const [models, setModels] = useState([DEFAULT_MODEL]);
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [analysisOpen, setAnalysisOpen] = useState<{ turnId: string; mode: AnalysisId } | null>(null);
  const [hiddenRunKeys, setHiddenRunKeys] = useState<Set<string>>(loadHiddenRunKeys);
  const [pendingDelete, setPendingDelete] = useState<ConversationSummary | null>(null);
  const [pendingConversationKey, setPendingConversationKey] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  const visibleRecords = useMemo(
    () => records.filter((record) => !hiddenRunKeys.has(record.key)),
    [hiddenRunKeys, records]
  );
  const conversations = useMemo(() => listConversations(visibleRecords), [visibleRecords]);
  const selectedSource = visibleRecords.find((record) => record.key === sourceKey) ??
    visibleRecords.find((record) => record.key === activeRecord.key) ?? visibleRecords[0] ?? activeRecord;

  const turnsRef = useRef<TurnView[]>([]);
  const turnManager = useTurnManager({
    model,
    conversationId,
    onConversationStart: setConversationId,
    onRunReady: (run, job, turnId) => {
      const turnIndex = turnsRef.current.findIndex((turn) => turn.id === turnId);
      onRunReady({
        ...run,
        metadata: {
          ...run.metadata,
          ...(conversationId ? { conversationId } : {}),
          ...(turnIndex >= 0 ? { turnIndex } : {})
        }
      }, job);
    }
  });
  turnsRef.current = turnManager.turns;
  const running = turnManager.activeTurnId !== null;

  useEffect(() => {
    const controller = new AbortController();
    void fetchPromptOptions(controller.signal).then((options) => {
      setModels(options.models);
      setModel((current) => options.models.includes(current) ? current : options.models[0]);
    }).catch(() => undefined);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!visibleRecords.some((record) => record.key === sourceKey)) {
      setSourceKey(selectedSource.key);
    }
  }, [selectedSource.key, sourceKey, visibleRecords]);

  useEffect(() => {
    if (!pendingConversationKey || activeRecord.key !== pendingConversationKey) return;
    restoreConversation(activeRecord);
    setPendingConversationKey(null);
  }, [activeRecord, pendingConversationKey]);

  function turnsForConversation(conversation: ConversationSummary): TurnView[] {
    return conversation.records
      .filter((record): record is RunRecord & { run: ExplorerRun } => record.run !== null)
      .map((record) => ({
        id: record.key,
        prompt: record.run.prompt,
        run: record.run,
        jobId: record.artifactId ?? null,
        status: "ready" as const,
        startedAt: record.importedAt
      }));
  }

  function restoreConversation(record: RunRecord & { run: ExplorerRun }) {
    const conversation = conversations.find((item) =>
      item.records.some((candidate) => candidate.key === record.key)
    );
    const turns = conversation ? turnsForConversation(conversation) : [{
      id: record.key,
      prompt: record.run.prompt,
      run: record.run,
      jobId: record.artifactId ?? null,
      status: "ready" as const,
      startedAt: record.importedAt
    }];
    turnManager.hydrate(turns, conversation?.conversationId ?? record.key);
    setSourceKey(record.key);
    setPrompt("");
    setAnalysisOpen(null);
    const previousModel = conversationModel(record.run);
    if (previousModel) setModel(previousModel);
    setHistoryOpen(false);
  }

  function selectConversation(conversation: ConversationSummary) {
    const first = conversation.firstRecord;
    if (first.run) {
      restoreConversation(first as RunRecord & { run: ExplorerRun });
      return;
    }
    setPendingConversationKey(first.key);
    setSourceKey(first.key);
    setHistoryOpen(false);
    onSelectConversation(first.key);
  }

  function startNewConversation() {
    turnManager.reset();
    setConversationId(null);
    setPendingConversationKey(null);
    setPrompt("");
    setAnalysisOpen(null);
    setHistoryOpen(false);
  }

  function submitPrompt() {
    const cleaned = prompt.trim();
    if (!cleaned || running) return;
    setPrompt("");
    setAnalysisOpen(null);
    turnManager.submit(cleaned);
  }

  function toggleAnalysis(turnId: string, mode: AnalysisId) {
    setAnalysisOpen((current) =>
      current?.turnId === turnId && current.mode === mode
        ? null
        : { turnId, mode }
    );
  }

  function removeConversationHistory(conversation: ConversationSummary) {
    const relatedKeys = new Set(conversation.records.map((record) => record.key));
    let foundChild = true;
    while (foundChild) {
      foundChild = false;
      for (const candidate of records) {
        const parentKey = parentRunKey(candidate);
        if (parentKey && relatedKeys.has(parentKey) && !relatedKeys.has(candidate.key)) {
          relatedKeys.add(candidate.key);
          foundChild = true;
        }
      }
    }
    const fallback = visibleRecords.find((record) => !relatedKeys.has(record.key));
    if (fallback) setSourceKey(fallback.key);
    setHiddenRunKeys((current) => {
      const next = new Set(current);
      for (const key of relatedKeys) next.add(key);
      try {
        window.localStorage.setItem(HIDDEN_RUN_STORAGE_KEY, JSON.stringify([...next]));
      } catch {
        // The entry remains hidden for the current tab when persistence is unavailable.
      }
      return next;
    });
    const removableKeys = records
      .filter((record) => relatedKeys.has(record.key))
      .filter((record) => record.sourceType === "local" || record.sourceType === "generated")
      .map((record) => record.key);
    onRemoveRuns(removableKeys);
    const isCurrentConversation = turnManager.turns.some((turn) =>
      relatedKeys.has(turn.id)
    );
    if (isCurrentConversation) {
      turnManager.reset();
      setConversationId(null);
      setAnalysisOpen(null);
    }
    window.history.replaceState(null, "", "/");
  }

  return (
    <div className={`chat-home ${turnManager.turns.length > 0 ? "has-conversation" : "is-empty"}`}>
      <header className="chat-home-header">
        <a className="chat-home-brand" href="/" aria-label="SafeLens home">
          <span><BrainCircuit size={22} /></span>
          <strong>SafeLens</strong>
        </a>
        <button className="chat-history-toggle" aria-label="Open chat history" title="Chat history" onClick={() => setHistoryOpen(true)}>
          <PanelLeftOpen size={18} />
        </button>
        <span className={`chat-home-status ${remoteState.status}`}>
          <i />{remoteState.status === "ready" ? "Local workspace" : "Local mode"}
        </span>
      </header>

      <div className="chat-home-body">
        <ChatHistory
          open={historyOpen}
          conversations={conversations}
          activeKey={null}
          onNew={startNewConversation}
          onSelect={selectConversation}
          onDelete={setPendingDelete}
          onClose={() => setHistoryOpen(false)}
        />
        <main className="chat-home-main">
          {turnManager.turns.length === 0 ? (
            <section className="chat-home-welcome" aria-labelledby="chat-home-title">
              <div>
                <span><MessageSquareText size={19} /></span>
                <h1 id="chat-home-title">What would you like to inspect?</h1>
              </div>
            </section>
          ) : (
            <TurnList
              turns={turnManager.turns}
              activeTurnId={turnManager.activeTurnId}
              analysisOpen={analysisOpen}
              onRetry={turnManager.retry}
              onCancel={turnManager.cancel}
              onToggleAnalysis={toggleAnalysis}
              onRunReady={onRunReady}
            />
          )}

        <PromptComposer
          prompt={prompt}
          model={model}
          models={models}
          running={running}
          onPromptChange={setPrompt}
          onModelChange={setModel}
          onUseSourcePrompt={() => {
            const sourcePrompt = selectedSource.run?.prompt;
            if (sourcePrompt) setPrompt(sourcePrompt);
          }}
          onSubmit={submitPrompt}
        />
        </main>
      </div>
      {pendingDelete && (
        <DeleteConversationDialog
          conversation={pendingDelete}
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => {
            removeConversationHistory(pendingDelete);
            setPendingDelete(null);
          }}
        />
      )}
    </div>
  );
}

function parentRunKey(record: RunRecord) {
  const parent = record.run?.metadata?.parentRun;
  if (!parent || typeof parent !== "object" || Array.isArray(parent)) return null;
  const runId = "runId" in parent ? parent.runId : undefined;
  const sampleId = "sampleId" in parent ? parent.sampleId : undefined;
  return typeof runId === "string" && typeof sampleId === "string"
    ? `${runId}::${sampleId}`
    : null;
}

function PromptComposer({
  prompt,
  model,
  models,
  running,
  onPromptChange,
  onModelChange,
  onUseSourcePrompt,
  onSubmit
}: {
  prompt: string;
  model: string;
  models: string[];
  running: boolean;
  onPromptChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onUseSourcePrompt: () => void;
  onSubmit: () => void;
}) {
  return (
    <section className="chat-composer" aria-label="Run a SafeLens analysis">
      <textarea
        aria-label="Analysis prompt"
        placeholder="Ask SafeLens"
        value={prompt}
        maxLength={8_000}
        onChange={(event) => onPromptChange(event.target.value)}
        onKeyDown={(event) => {
          if ((event.metaKey || event.ctrlKey) && event.key === "Enter") onSubmit();
        }}
      />
      <div className="chat-composer-controls">
        <button className="chat-attach" aria-label="Use selected run prompt" title="Use selected run prompt" onClick={onUseSourcePrompt}>
          <Paperclip size={17} />
        </button>
        <label>
          <span>Model</span>
          <select aria-label="Analysis model" value={model} onChange={(event) => onModelChange(event.target.value)}>
            {models.map((item) => <option key={item} value={item}>{shortModelName(item)}</option>)}
          </select>
        </label>
        <button className="chat-run" aria-label="Run analysis" title="Run analysis" disabled={!prompt.trim() || running} onClick={onSubmit}>
          {running ? <LoaderCircle size={18} /> : <Play size={18} fill="currentColor" />}
        </button>
      </div>
    </section>
  );
}

function ChatHistory({
  open,
  conversations,
  activeKey,
  onNew,
  onSelect,
  onDelete,
  onClose
}: {
  open: boolean;
  conversations: ConversationSummary[];
  activeKey: string | null;
  onNew: () => void;
  onSelect: (conversation: ConversationSummary) => void;
  onDelete: (conversation: ConversationSummary) => void;
  onClose: () => void;
}) {
  return (
    <>
      <aside className={`chat-history ${open ? "open" : ""}`} aria-label="Chat history">
        <header>
          <button className="chat-history-new" onClick={onNew}>
            <SquarePen size={17} /> New chat
          </button>
          <button className="chat-history-close" aria-label="Close chat history" onClick={onClose}>
            <X size={17} />
          </button>
        </header>
        <nav aria-label="Conversation history">
          <span>Recent</span>
          {conversations.length ? conversations.map((conversation) => (
            <div key={conversation.conversationId} className={`chat-history-row ${conversation.firstRecord.key === activeKey ? "active" : ""}`}>
              <button className="chat-history-open" onClick={() => onSelect(conversation)}>
                <strong>{conversation.title}</strong>
                <small>
                  {shortModelName(conversation.firstRecord.modelName)}
                  {conversation.turnCount > 1 ? ` · ${conversation.turnCount} turns` : ""}
                </small>
              </button>
              <button
                className="chat-history-delete"
                aria-label={`Delete conversation ${conversation.title}`}
                title="Delete conversation"
                onClick={() => onDelete(conversation)}
              >
                <Trash2 size={15} />
              </button>
            </div>
          )) : (
            <p>No conversations yet.</p>
          )}
        </nav>
      </aside>
      {open && <button className="chat-history-backdrop" aria-label="Close chat history" onClick={onClose} />}
    </>
  );
}

function DeleteConversationDialog({ conversation, onCancel, onConfirm }: {
  conversation: ConversationSummary;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="chat-delete-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onCancel();
    }}>
      <section role="dialog" aria-modal="true" aria-labelledby="chat-delete-title" className="chat-delete-dialog">
        <header>
          <div>
            <span>Chat history</span>
            <h2 id="chat-delete-title">Delete this conversation?</h2>
          </div>
          <button aria-label="Close remove confirmation" onClick={onCancel}><X size={18} /></button>
        </header>
        <p>This removes <strong>{conversation.title}</strong> from Chat history. Workspace source files are not modified.</p>
        <footer>
          <button autoFocus onClick={onCancel}>Cancel</button>
          <button className="danger" onClick={onConfirm}><Trash2 size={15} /> Delete conversation</button>
        </footer>
      </section>
    </div>
  );
}

function shortModelName(model: string) {
  const parts = model.split("/");
  return parts[parts.length - 1] ?? model;
}

function conversationModel(run: ExplorerRun) {
  const promptRunner = run.metadata?.promptRunner;
  if (!promptRunner || typeof promptRunner !== "object") return null;
  const value = (promptRunner as Record<string, unknown>).model;
  return typeof value === "string" ? value : null;
}

function loadHiddenRunKeys() {
  try {
    const value: unknown = JSON.parse(window.localStorage.getItem(HIDDEN_RUN_STORAGE_KEY) ?? "[]");
    return new Set(Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : []);
  } catch {
    return new Set<string>();
  }
}
