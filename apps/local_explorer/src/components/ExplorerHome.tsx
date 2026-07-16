import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleStop,
  LoaderCircle,
  MessageSquareText,
  PanelLeftOpen,
  Paperclip,
  Play,
  RefreshCw,
  ScanSearch,
  SlidersHorizontal,
  SquarePen,
  Trash2,
  X
} from "lucide-react";

import { fetchPromptOptions, type PromptJob } from "../api/explorerClient";
import { usePromptRunner } from "../state/usePromptRunner";
import type { RemoteRunState, RunRecord } from "../state/useRunLibrary";
import type { ExplorerRun } from "../types";
import { ChatAnalysisWorkbench } from "./ChatAnalysisWorkbench";

type AnalysisId = "steering" | "attribution";

interface AnalysisDirection {
  id: AnalysisId;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const DEFAULT_MODEL = "sshleifer/tiny-gpt2";
const HIDDEN_RUN_STORAGE_KEY = "safelens.localExplorer.hiddenWork.v1";

const analysisDirections: AnalysisDirection[] = [
  {
    id: "steering",
    title: "Steering",
    description: "Apply a contrastive direction and compare the generated response.",
    icon: <SlidersHorizontal size={20} />
  },
  {
    id: "attribution",
    title: "Input attribution",
    description: "Measure which input tokens support or suppress a response token.",
    icon: <ScanSearch size={20} />
  }
];

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
  const [submittedPrompt, setSubmittedPrompt] = useState("");
  const [resultRun, setResultRun] = useState<ExplorerRun | null>(null);
  const [sourceKey, setSourceKey] = useState(activeRecord.key);
  const [models, setModels] = useState([DEFAULT_MODEL]);
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [selectedGroupId, setSelectedGroupId] = useState<AnalysisId | null>(null);
  const [hiddenRunKeys, setHiddenRunKeys] = useState<Set<string>>(loadHiddenRunKeys);
  const [pendingDelete, setPendingDelete] = useState<RunRecord | null>(null);
  const [pendingConversationKey, setPendingConversationKey] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  const handleRunReady = useCallback((run: ExplorerRun, job: PromptJob) => {
    setResultRun(run);
    onRunReady(run, job);
  }, [onRunReady]);
  const runner = usePromptRunner(handleRunReady);
  const running = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const displayRun = resultRun ?? activeRecord.run;
  const visibleRecords = useMemo(
    () => records.filter((record) => !hiddenRunKeys.has(record.key)),
    [hiddenRunKeys, records]
  );
  const conversations = useMemo(
    () => visibleRecords.filter(isConversationRecord).sort((left, right) =>
      conversationTimestamp(right).localeCompare(conversationTimestamp(left))
    ),
    [visibleRecords]
  );
  const selectedSource = visibleRecords.find((record) => record.key === sourceKey) ??
    visibleRecords.find((record) => record.key === activeRecord.key) ?? visibleRecords[0] ?? activeRecord;
  const savedAnalysisRuns = useMemo(
    () => visibleRecords
      .filter((record) => parentRunKey(record) === sourceKey && record.run)
      .sort((left, right) => conversationTimestamp(right).localeCompare(conversationTimestamp(left))),
    [sourceKey, visibleRecords]
  );
  const savedAnalysisRun = selectedGroupId === "steering"
    ? savedAnalysisRuns.find((record) => record.run?.intervention)?.run ?? undefined
    : selectedGroupId === "attribution"
      ? savedAnalysisRuns.find((record) => record.run?.attributionMethods.some(
        (method) => method.id === "integrated_gradients" && method.available
      ))?.run ?? undefined
      : undefined;

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
    if (!resultRun) return;
    const generated = records.find(
      (record) => record.runId === resultRun.runId && record.sampleId === resultRun.sampleId
    );
    if (generated) setSourceKey(generated.key);
  }, [records, resultRun]);

  useEffect(() => {
    if (!pendingConversationKey || activeRecord.key !== pendingConversationKey) return;
    restoreConversation(activeRecord);
    setPendingConversationKey(null);
  }, [activeRecord, pendingConversationKey]);

  function restoreConversation(record: RunRecord & { run: ExplorerRun }) {
    runner.reset();
    setSourceKey(record.key);
    setSubmittedPrompt(record.run.prompt);
    setPrompt("");
    setResultRun(record.run);
    setSelectedGroupId(null);
    const previousModel = conversationModel(record.run);
    if (previousModel) setModel(previousModel);
    setHistoryOpen(false);
  }

  function selectConversation(record: RunRecord) {
    if (record.run) {
      restoreConversation(record as RunRecord & { run: ExplorerRun });
      return;
    }
    setPendingConversationKey(record.key);
    setSourceKey(record.key);
    setHistoryOpen(false);
    onSelectConversation(record.key);
  }

  function startNewConversation() {
    runner.reset();
    setPendingConversationKey(null);
    setSubmittedPrompt("");
    setResultRun(null);
    setPrompt("");
    setSelectedGroupId(null);
    setHistoryOpen(false);
  }

  function submitPrompt() {
    const cleaned = prompt.trim();
    if (!cleaned || running) return;
    setSubmittedPrompt(cleaned);
    setPrompt("");
    setResultRun(null);
    setSelectedGroupId(null);
    void runner.submit({
      prompt: cleaned,
      template: "chat",
      model,
      seed: 0,
      maxNewTokens: 8,
      temperature: 0
    });
  }

  function retryPrompt() {
    if (!submittedPrompt || running) return;
    setResultRun(null);
    void runner.submit({
      prompt: submittedPrompt,
      template: "chat",
      model,
      seed: 0,
      maxNewTokens: 8,
      temperature: 0
    });
  }

  function useSourcePrompt() {
    const sourcePrompt = selectedSource.run?.prompt;
    if (sourcePrompt) setPrompt(sourcePrompt);
  }

  function removeRunHistory(key: string) {
    const relatedKeys = new Set([key]);
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
    const fallback = visibleRecords.find((record) => record.key !== key);
    if (sourceKey === key && fallback) setSourceKey(fallback.key);
    setHiddenRunKeys((current) => {
      const next = new Set(current);
      next.add(key);
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
    window.history.replaceState(null, "", "/");
  }

  return (
    <div className={`chat-home ${submittedPrompt ? "has-conversation" : "is-empty"}`}>
      <header className="chat-home-header">
        <a className="chat-home-brand" href="/" aria-label="SafeLens home">
          <span><BrainCircuit size={20} /></span>
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
          records={conversations}
          activeKey={resultRun ? sourceKey : null}
          onNew={startNewConversation}
          onSelect={selectConversation}
          onDelete={setPendingDelete}
          onClose={() => setHistoryOpen(false)}
        />
        <main className="chat-home-main">
          {!submittedPrompt ? (
            <section className="chat-home-welcome" aria-labelledby="chat-home-title">
              <div>
                <span><MessageSquareText size={19} /></span>
                <h1 id="chat-home-title">What would you like to inspect?</h1>
              </div>
            </section>
          ) : (
            <Conversation
              prompt={submittedPrompt}
              run={resultRun}
              job={runner.job}
              error={runner.error?.message}
              running={running}
              onCancel={() => {
                setPrompt(submittedPrompt);
                void runner.cancel();
              }}
              onRetry={retryPrompt}
            />
          )}

          {resultRun && (
            <section className="chat-analysis" aria-label="Analysis directions">
              <header>
                <span>Explore this run</span>
                <p>Steer the response or trace it back to the input.</p>
              </header>
              <div className="chat-analysis-directions">
                {analysisDirections.map((direction) => (
                  <button
                    key={direction.id}
                    className={selectedGroupId === direction.id ? "active" : ""}
                    aria-pressed={selectedGroupId === direction.id}
                    onClick={() => setSelectedGroupId(direction.id)}
                  >
                    <span>{direction.icon}</span>
                    <strong>{direction.title}</strong>
                    <small>{direction.description}</small>
                    <ChevronRight size={17} />
                  </button>
                ))}
              </div>
              {selectedGroupId && (
                <ChatAnalysisWorkbench
                  key={`${displayRun.runId}:${displayRun.sampleId}:${selectedGroupId}`}
                  mode={selectedGroupId}
                  run={displayRun}
                  savedRun={savedAnalysisRun}
                  onRunReady={onRunReady}
                />
              )}
            </section>
          )}

        <PromptComposer
          prompt={prompt}
          model={model}
          models={models}
          running={running}
          onPromptChange={setPrompt}
          onModelChange={setModel}
          onUseSourcePrompt={useSourcePrompt}
          onSubmit={submitPrompt}
        />
        </main>
      </div>
      {pendingDelete && (
        <DeleteRunDialog
          record={pendingDelete}
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => {
            const removingCurrent = pendingDelete.key === sourceKey && Boolean(resultRun);
            removeRunHistory(pendingDelete.key);
            setPendingDelete(null);
            if (removingCurrent) startNewConversation();
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
  records,
  activeKey,
  onNew,
  onSelect,
  onDelete,
  onClose
}: {
  open: boolean;
  records: RunRecord[];
  activeKey: string | null;
  onNew: () => void;
  onSelect: (record: RunRecord) => void;
  onDelete: (record: RunRecord) => void;
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
          {records.length ? records.map((record) => (
            <div key={record.key} className={`chat-history-row ${record.key === activeKey ? "active" : ""}`}>
              <button className="chat-history-open" onClick={() => onSelect(record)}>
                <strong>{conversationTitle(record)}</strong>
                <small>{shortModelName(record.modelName)}</small>
              </button>
              <button
                className="chat-history-delete"
                aria-label={`Delete conversation ${record.runId} ${record.sampleId}`}
                title="Delete conversation"
                onClick={() => onDelete(record)}
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

function Conversation({
  prompt,
  run,
  job,
  error,
  running,
  onCancel,
  onRetry
}: {
  prompt: string;
  run: ExplorerRun | null;
  job: PromptJob | null;
  error?: string;
  running: boolean;
  onCancel: () => void;
  onRetry: () => void;
}) {
  return (
    <section className="chat-conversation" aria-label="Analysis conversation">
      <div className="chat-user-message">{prompt}</div>
      <div className="chat-assistant-message">
        <span className="chat-assistant-mark"><BrainCircuit size={18} /></span>
        <div>
          {run ? (
            <>
              <p>{generatedResponse(run)}</p>
              <span className="chat-run-ready"><CheckCircle2 size={14} /> Activation cache ready</span>
            </>
          ) : error ? (
            <>
              <p>{error}</p>
              <button onClick={onRetry}>Retry</button>
            </>
          ) : (
            <div className="chat-job-progress">
              <span><LoaderCircle size={16} /> {job?.detail ?? "Submitting the analysis..."}</span>
              <i><b style={{ width: `${job?.progress ?? 4}%` }} /></i>
              <small>{job?.progress ?? 0}%</small>
              {running && <button aria-label="Cancel analysis" onClick={onCancel}><CircleStop size={16} /></button>}
              {job?.status === "cancelled" && (
                <button aria-label="Retry analysis" title="Retry analysis" onClick={onRetry}>
                  <RefreshCw size={15} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function DeleteRunDialog({ record, onCancel, onConfirm }: {
  record: RunRecord;
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
        <p>This removes <strong>{conversationTitle(record)}</strong> from Chat history. Workspace source files are not modified.</p>
        <footer>
          <button autoFocus onClick={onCancel}>Cancel</button>
          <button className="danger" onClick={onConfirm}><Trash2 size={15} /> Delete conversation</button>
        </footer>
      </section>
    </div>
  );
}

function generatedResponse(run: ExplorerRun) {
  const generated = run.metadata?.generatedContinuation;
  if (typeof generated !== "string" || !generated.trim()) return "The model run is complete and its internal activations are ready to inspect.";
  const response = generated.startsWith(run.prompt) ? generated.slice(run.prompt.length).trim() : generated.trim();
  return response || "The model run is complete and its internal activations are ready to inspect.";
}

function shortModelName(model: string) {
  const parts = model.split("/");
  return parts[parts.length - 1] ?? model;
}

function isConversationRecord(record: RunRecord) {
  if (record.builtIn) return true;
  if (record.sourceType === "remote") return /(^|\/)generated\/prompt-[^/]+\.explorer\.json$/i.test(record.sourceName);
  return record.sourceName.startsWith("prompt job ");
}

function conversationTitle(record: RunRecord) {
  const prompt = (record.run?.prompt ?? record.remoteSummary?.promptPreview)?.trim().replace(/\s+/g, " ");
  if (!prompt) return record.runId;
  return prompt.length > 46 ? `${prompt.slice(0, 45).trimEnd()}...` : prompt;
}

function conversationTimestamp(record: RunRecord) {
  if (record.lastUsedAt) return record.lastUsedAt;
  if (record.importedAt !== "built in") return record.importedAt;
  return "0000-00-00T00:00:00.000Z";
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
