import { useEffect, useMemo, useRef, useState } from "react";
import {
  Braces,
  BrainCircuit,
  Check,
  CheckSquare2,
  Database,
  FileText,
  MessageSquareText,
  PanelLeftClose,
  PanelLeftOpen,
  Paperclip,
  Play,
  LoaderCircle,
  MoreHorizontal,
  Pencil,
  Pin,
  Search,
  Square,
  SquarePen,
  Trash2,
  X
} from "lucide-react";

import { fetchPromptOptions } from "../api/explorerClient";
import { generatedResponseText } from "../generatedResponse";
import { useTurnManager } from "../state/useTurnManager";
import { loadPendingPromptTurn } from "../state/pendingPromptTurn";
import {
  listConversations,
  type ConversationSummary,
  type RemoteRunState,
  type RunRecord
} from "../state/useRunLibrary";
import type { ExplorerRun } from "../types";
import { TurnList } from "./TurnList";
import { JobCenter } from "./JobCenter";
import type { TurnView } from "../state/useTurnManager";
import type { AnalysisId } from "./TurnCard";

const DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct";
// Keep the picker useful while the API options request is in flight (or when
// a remote VS Code port-forward briefly drops that request). The server still
// remains the source of truth and replaces this list once it responds.
const FALLBACK_MODELS = [
  DEFAULT_MODEL,
  "sshleifer/tiny-gpt2",
  "google/gemma-3-12b-it",
  "google/gemma-3-270m-it",
  "google/gemma-2-9b-it"
];
const DEFAULT_MAX_NEW_TOKENS = 128;
const MAX_NEW_TOKENS_LIMIT = 512;
const HIDDEN_RUN_STORAGE_KEY = "safelens.localExplorer.hiddenWork.v1";
const HISTORY_COLLAPSED_STORAGE_KEY = "safelens.localExplorer.historyCollapsed.v1";
const CONVERSATION_META_STORAGE_KEY = "safelens.localExplorer.conversationMeta.v1";

interface ConversationMeta {
  title?: string;
  pinned?: boolean;
}

type ConversationMetaMap = Record<string, ConversationMeta>;

interface PendingConversationDeletion {
  items: ConversationSummary[];
  keys: Set<string>;
}

interface ExplorerHomeProps {
  records: RunRecord[];
  activeRecord: RunRecord & { run: ExplorerRun };
  remoteState: RemoteRunState;
  onOpenDatasetTest: () => void;
  onOpenDatasetJob: (jobId: string) => void;
  onSelectConversation: (key: string) => void;
  onRunReady: (run: ExplorerRun, job: { id: string; kind: "prompt-run" | "attribution" | "intervention" | "patching" | "nla" | "jlens" }) => void;
  onRemoveRuns: (keys: string[]) => void;
}

export function ExplorerHome({
  records,
  activeRecord,
  remoteState,
  onOpenDatasetTest,
  onOpenDatasetJob,
  onSelectConversation,
  onRunReady,
  onRemoveRuns
}: ExplorerHomeProps) {
  const [prompt, setPrompt] = useState("");
  const [sourceKey, setSourceKey] = useState(activeRecord.key);
  const [models, setModels] = useState(FALLBACK_MODELS);
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [maxNewTokens, setMaxNewTokens] = useState(DEFAULT_MAX_NEW_TOKENS);
  const [maxNewTokensLimit, setMaxNewTokensLimit] = useState(MAX_NEW_TOKENS_LIMIT);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [analysisOpen, setAnalysisOpen] = useState<{ turnId: string; mode: AnalysisId } | null>(null);
  const [hiddenRunKeys, setHiddenRunKeys] = useState<Set<string>>(loadHiddenRunKeys);
  const [pendingDelete, setPendingDelete] = useState<ConversationSummary[] | null>(null);
  const [pendingConversationKey, setPendingConversationKey] = useState<string | null>(null);
  const [historyNotice, setHistoryNotice] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyCollapsed, setHistoryCollapsed] = useState(loadHistoryCollapsed);
  const [selectingConversations, setSelectingConversations] = useState(false);
  const [selectedConversationIds, setSelectedConversationIds] = useState<Set<string>>(new Set());
  const [conversationQuery, setConversationQuery] = useState("");
  const [conversationMeta, setConversationMeta] = useState<ConversationMetaMap>(loadConversationMeta);
  const [undoDeletion, setUndoDeletion] = useState<PendingConversationDeletion | null>(null);
  const undoDeletionTimerRef = useRef<number | null>(null);

  const visibleRecords = useMemo(
    () => records.filter((record) => !hiddenRunKeys.has(record.key)),
    [hiddenRunKeys, records]
  );
  const conversations = useMemo(() => listConversations(visibleRecords), [visibleRecords]);
  const visibleConversations = useMemo(() => {
    const query = conversationQuery.trim().toLowerCase();
    if (!query) return conversations;
    return conversations.filter((conversation) => {
      const title = conversationMeta[conversation.conversationId]?.title ?? conversation.title;
      return `${title} ${conversation.firstRecord.modelName}`.toLowerCase().includes(query);
    });
  }, [conversationMeta, conversationQuery, conversations]);
  const displayedConversations = useMemo(() => {
    return visibleConversations
      .map((conversation) => ({
        ...conversation,
        title: conversationMeta[conversation.conversationId]?.title ?? conversation.title
      }))
      .sort((left, right) => {
        const leftPinned = conversationMeta[left.conversationId]?.pinned ? 1 : 0;
        const rightPinned = conversationMeta[right.conversationId]?.pinned ? 1 : 0;
        return rightPinned - leftPinned || right.lastUsedAt.localeCompare(left.lastUsedAt);
      });
  }, [conversationMeta, visibleConversations]);
  useEffect(() => {
    setSelectedConversationIds(new Set());
  }, [conversationQuery]);
  useEffect(() => {
    setSelectedConversationIds((current) => {
      const available = new Set(conversations.map((conversation) => conversation.conversationId));
      const next = new Set([...current].filter((id) => available.has(id)));
      return next.size === current.size ? current : next;
    });
    if (selectingConversations && conversations.length === 0) {
      setSelectingConversations(false);
    }
  }, [conversations, selectingConversations]);
  const selectedSource = visibleRecords.find((record) => record.key === sourceKey) ??
    visibleRecords.find((record) => record.key === activeRecord.key) ?? visibleRecords[0] ?? activeRecord;
  const pendingRestore = useMemo(() => {
    const pending = loadPendingPromptTurn();
    if (!pending) return null;
    const conversation = conversations.find(
      (item) => item.conversationId === pending.conversationId
    );
    const existingTurns = conversation
      ? turnsForConversation(conversation).filter((turn) => turn.id !== pending.turnId)
      : [];
    const pendingTurn: TurnView = {
      id: pending.turnId,
      prompt: pending.prompt,
      run: null,
      jobId: pending.jobId,
      status: "pending",
      startedAt: pending.startedAt
    };
    return {
      conversationId: pending.conversationId,
      turnId: pending.turnId,
      jobId: pending.jobId,
      model: pending.model,
      maxNewTokens: pending.maxNewTokens,
      turns: [...existingTurns, pendingTurn]
    };
  }, [conversations]);

  const turnsRef = useRef<TurnView[]>([]);
  const turnManager = useTurnManager({
    model,
    maxNewTokens,
    conversationId,
    onConversationStart: setConversationId,
    initialRestore: pendingRestore,
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
      setMaxNewTokensLimit(options.maxNewTokens);
      setMaxNewTokens((current) => Math.min(current, options.maxNewTokens));
    }).catch(() => {
      // Keep the local fallback list visible if the API is temporarily
      // unreachable. A later mount/request will refresh it from the server.
      setModels((current) => current.length > 0 ? current : FALLBACK_MODELS);
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!pendingRestore) return;
    if (models.includes(pendingRestore.model)) setModel(pendingRestore.model);
    setMaxNewTokens(Math.min(pendingRestore.maxNewTokens, maxNewTokensLimit));
  }, [maxNewTokensLimit, models, pendingRestore?.jobId]);

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
    return conversation.turnRecords
      .filter((record): record is RunRecord & { run: ExplorerRun } => record.run !== null)
      .map((record) => ({
        id: record.key,
        prompt: userPromptForRun(record.run),
        run: record.run,
        jobId: record.artifactId ?? null,
        status: "ready" as const,
        startedAt: record.importedAt
      }));
  }

  function restoreConversation(record: RunRecord & { run: ExplorerRun }) {
    setHistoryNotice(null);
    const conversation = conversations.find((item) =>
      item.records.some((candidate) => candidate.key === record.key)
    );
    const turns = conversation ? turnsForConversation(conversation) : [{
      id: record.key,
      prompt: userPromptForRun(record.run),
      run: record.run,
      jobId: record.artifactId ?? null,
      status: "ready" as const,
      startedAt: record.importedAt
    }];
    turnManager.hydrate(turns, conversation?.conversationId ?? record.key);
    setSourceKey(record.key);
    setPrompt("");
    setAnalysisOpen(null);
    const conversationRuns = conversation?.turnRecords
      .flatMap((candidate) => candidate.run ? [candidate.run] : []) ?? [];
    const configurationRun = conversationRuns[conversationRuns.length - 1] ?? record.run;
    const previousModel = conversationModel(configurationRun);
    if (previousModel) setModel(previousModel);
    const previousMaxNewTokens = conversationMaxNewTokens(configurationRun);
    if (previousMaxNewTokens) {
      setMaxNewTokens(Math.min(previousMaxNewTokens, maxNewTokensLimit));
    }
    setHistoryOpen(false);
  }

  function selectConversation(conversation: ConversationSummary) {
    const first = conversation.firstRecord;
    setHistoryNotice(null);
    setSelectingConversations(false);
    setSelectedConversationIds(new Set());
    if (first.run) {
      restoreConversation(first as RunRecord & { run: ExplorerRun });
      return;
    }
    if (!first.remoteSummary) {
      setHistoryNotice(
        "This conversation's run is not available in the current workspace. Start a new chat or reload the run."
      );
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
    setHistoryNotice(null);
    setPrompt("");
    setAnalysisOpen(null);
    setHistoryOpen(false);
    setSelectingConversations(false);
    setSelectedConversationIds(new Set());
  }

  function toggleHistoryCollapsed() {
    setHistoryCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(HISTORY_COLLAPSED_STORAGE_KEY, String(next));
      } catch {
        // The preference remains in memory when persistence is unavailable.
      }
      return next;
    });
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

  function removeConversationsHistory(items: ConversationSummary[]) {
    if (items.length === 0) return;
    const relatedKeys = conversationRelatedKeys(items, records);
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

  function updateConversationMeta(next: ConversationMetaMap) {
    setConversationMeta(next);
    try {
      window.localStorage.setItem(CONVERSATION_META_STORAGE_KEY, JSON.stringify(next));
    } catch {
      // The in-memory preference still applies for this tab.
    }
  }

  function renameConversation(conversationId: string, title: string) {
    updateConversationMeta({
      ...conversationMeta,
      [conversationId]: {
        ...conversationMeta[conversationId],
        title: title.trim() || undefined
      }
    });
  }

  function toggleConversationPin(conversationId: string) {
    updateConversationMeta({
      ...conversationMeta,
      [conversationId]: {
        ...conversationMeta[conversationId],
        pinned: !conversationMeta[conversationId]?.pinned
      }
    });
  }

  function exportConversation(conversation: ConversationSummary, format: "md" | "json") {
    const turns = conversation.turnRecords.flatMap((record) => {
      if (!record.run) return [];
      return [{
        prompt: userPromptForRun(record.run),
        response: generatedResponseText(record.run)
      }];
    });
    const filename = `safelens-${conversation.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "conversation"}`;
    if (format === "json") {
      downloadTextFile(
        `${filename}.json`,
        "application/json",
        JSON.stringify({
          conversationId: conversation.conversationId,
          title: conversation.title,
          model: conversation.firstRecord.modelName,
          turns
        }, null, 2)
      );
      return;
    }
    const markdown = [
      `# ${conversation.title}`,
      "",
      `Model: ${conversation.firstRecord.modelName}`,
      "",
      ...turns.flatMap((turn, index) => [
        `## Turn ${index + 1}`,
        "",
        "### User",
        turn.prompt,
        "",
        "### Assistant",
        turn.response || "No visible continuation.",
        ""
      ])
    ].join("\n");
    downloadTextFile(`${filename}.md`, "text/markdown", markdown);
  }

  function stageConversationDeletion(items: ConversationSummary[]) {
    if (items.length === 0) return;
    const relatedKeys = conversationRelatedKeys(items, records);
    const addedKeys = new Set([...relatedKeys].filter((key) => !hiddenRunKeys.has(key)));
    setHiddenRunKeys((current) => {
      const next = new Set(current);
      for (const key of relatedKeys) next.add(key);
      persistHiddenRunKeys(next);
      return next;
    });
    const mergedItems = [
      ...(undoDeletion?.items ?? []),
      ...items.filter((item) =>
        !(undoDeletion?.items ?? []).some(
          (existing) => existing.conversationId === item.conversationId
        )
      )
    ];
    const mergedKeys = new Set([...(undoDeletion?.keys ?? []), ...addedKeys]);
    setUndoDeletion({ items: mergedItems, keys: mergedKeys });
    if (undoDeletionTimerRef.current !== null) {
      window.clearTimeout(undoDeletionTimerRef.current);
    }
    undoDeletionTimerRef.current = window.setTimeout(() => {
      removeConversationsHistory(mergedItems);
      setUndoDeletion(null);
      undoDeletionTimerRef.current = null;
    }, 6000);
  }

  function undoConversationDeletion() {
    if (!undoDeletion) return;
    if (undoDeletionTimerRef.current !== null) {
      window.clearTimeout(undoDeletionTimerRef.current);
      undoDeletionTimerRef.current = null;
    }
    setHiddenRunKeys((current) => {
      const next = new Set(current);
      for (const key of undoDeletion.keys) next.delete(key);
      persistHiddenRunKeys(next);
      return next;
    });
    setUndoDeletion(null);
  }

  function toggleConversationSelection(conversationId: string) {
    setSelectedConversationIds((current) => {
      const next = new Set(current);
      if (next.has(conversationId)) next.delete(conversationId);
      else next.add(conversationId);
      return next;
    });
  }

  function selectAllConversations() {
    setSelectedConversationIds(
      new Set(displayedConversations.map((conversation) => conversation.conversationId))
    );
  }

  function clearConversationSelection() {
    setSelectedConversationIds(new Set());
  }

  function toggleConversationSelectionMode() {
    setSelectingConversations((current) => {
      if (current) setSelectedConversationIds(new Set());
      return !current;
    });
  }

  function requestDeleteConversations(items: ConversationSummary[]) {
    if (items.length > 0) setPendingDelete(items);
  }

  function deleteSelectedConversations() {
    requestDeleteConversations(
      conversations.filter((conversation) =>
        selectedConversationIds.has(conversation.conversationId)
      )
    );
  }

  return (
    <div className={`chat-home ${turnManager.turns.length > 0 ? "has-conversation" : "is-empty"} ${analysisOpen ? "has-analysis" : ""}`}>
      <header className="chat-home-header">
        <a className="chat-home-brand" href="/" aria-label="SafeLens home">
          <span><BrainCircuit size={22} /></span>
          <strong>SafeLens</strong>
        </a>
        <button className="chat-history-toggle" aria-label="Open chat history" title="Chat history" onClick={() => setHistoryOpen(true)}>
          <PanelLeftOpen size={18} />
        </button>
        <nav className="chat-home-nav" aria-label="SafeLens modes">
          <button onClick={onOpenDatasetTest}><Database size={16} /> Dataset test</button>
          <JobCenter inline onOpenDatasetJob={onOpenDatasetJob} />
          <span className={`chat-home-status ${remoteState.status}`}>
            <i />{remoteState.status === "ready" ? "Local workspace" : "Local mode"}
          </span>
        </nav>
      </header>

      <div className={`chat-home-body ${historyCollapsed ? "history-collapsed" : ""}`}>
        <ChatHistory
          open={historyOpen}
          collapsed={historyCollapsed}
          onToggleCollapsed={toggleHistoryCollapsed}
          conversations={displayedConversations}
          totalConversations={conversations.length}
          conversationMeta={conversationMeta}
          onRenameConversation={renameConversation}
          onTogglePin={toggleConversationPin}
          onExportConversation={exportConversation}
          query={conversationQuery}
          onQueryChange={setConversationQuery}
          activeKey={null}
          selecting={selectingConversations}
          selectedIds={selectedConversationIds}
          onToggleSelecting={toggleConversationSelectionMode}
          onToggleSelected={toggleConversationSelection}
          onSelectAll={selectAllConversations}
          onClearSelected={clearConversationSelection}
          onDeleteSelected={deleteSelectedConversations}
          onNew={startNewConversation}
          onSelect={selectConversation}
          onDelete={requestDeleteConversations}
          onClose={() => setHistoryOpen(false)}
        />
        <main className="chat-home-main">
          {(pendingConversationKey || historyNotice) && (
            <div
              className={`chat-history-notice ${remoteState.status === "error" || historyNotice ? "error" : ""}`}
              role="status"
            >
              {historyNotice ? (
                <span>{historyNotice}</span>
              ) : remoteState.status === "error" ? (
                <>
                  <span>Could not load this conversation. {remoteState.detail}</span>
                  <button
                    type="button"
                    onClick={() => pendingConversationKey && onSelectConversation(pendingConversationKey)}
                  >
                    Retry
                  </button>
                </>
              ) : (
                <span>Loading conversation from the workspace…</span>
              )}
            </div>
          )}
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
              records={visibleRecords}
              analysisRuns={visibleRecords.flatMap((record) => record.run ? [record.run] : [])}
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
          maxNewTokens={maxNewTokens}
          maxNewTokensLimit={maxNewTokensLimit}
          running={running}
          onPromptChange={setPrompt}
          onModelChange={setModel}
          onMaxNewTokensChange={setMaxNewTokens}
          onUseSourcePrompt={() => {
            const sourcePrompt = selectedSource.run?.prompt;
            if (sourcePrompt) setPrompt(sourcePrompt);
          }}
          onSubmit={submitPrompt}
        />
        </main>
      </div>
      {undoDeletion && (
        <div className="chat-undo-toast" role="status">
          <span>
            Removed {undoDeletion.items.length} conversation
            {undoDeletion.items.length === 1 ? "" : "s"} from Chat history.
          </span>
          <button type="button" onClick={undoConversationDeletion}>Undo</button>
        </div>
      )}
      {pendingDelete && (
        <DeleteConversationsDialog
          conversations={pendingDelete}
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => {
            stageConversationDeletion(pendingDelete);
            setPendingDelete(null);
            setSelectingConversations(false);
            setSelectedConversationIds(new Set());
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
  maxNewTokens,
  maxNewTokensLimit,
  running,
  onPromptChange,
  onModelChange,
  onMaxNewTokensChange,
  onUseSourcePrompt,
  onSubmit
}: {
  prompt: string;
  model: string;
  models: string[];
  maxNewTokens: number;
  maxNewTokensLimit: number;
  running: boolean;
  onPromptChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onMaxNewTokensChange: (value: number) => void;
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
          <select
            aria-label="Analysis model"
            aria-describedby="chat-model-capability"
            title={modelCapabilityHint(model)}
            value={model}
            onChange={(event) => onModelChange(event.target.value)}
          >
            {models.map((item) => <option key={item} value={item}>{shortModelName(item)}</option>)}
          </select>
          <span id="chat-model-capability" className="visually-hidden">
            {modelCapabilityHint(model)}
          </span>
        </label>
        <label className="chat-token-budget">
          <span>Max</span>
          <input
            aria-label="Maximum new tokens"
            type="number"
            min={1}
            max={maxNewTokensLimit}
            step={1}
            value={maxNewTokens}
            disabled={running}
            title="Maximum new tokens"
            onChange={(event) => onMaxNewTokensChange(
              clampInteger(event.target.value, 1, maxNewTokensLimit)
            )}
          />
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
  collapsed: collapsedPreference,
  onToggleCollapsed,
  conversations,
  totalConversations,
  conversationMeta,
  onRenameConversation,
  onTogglePin,
  onExportConversation,
  query,
  onQueryChange,
  activeKey,
  selecting,
  selectedIds,
  onToggleSelecting,
  onToggleSelected,
  onSelectAll,
  onClearSelected,
  onDeleteSelected,
  onNew,
  onSelect,
  onDelete,
  onClose
}: {
  open: boolean;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  conversations: ConversationSummary[];
  totalConversations: number;
  conversationMeta: ConversationMetaMap;
  onRenameConversation: (conversationId: string, title: string) => void;
  onTogglePin: (conversationId: string) => void;
  onExportConversation: (conversation: ConversationSummary, format: "md" | "json") => void;
  query: string;
  onQueryChange: (query: string) => void;
  activeKey: string | null;
  selecting: boolean;
  selectedIds: Set<string>;
  onToggleSelecting: () => void;
  onToggleSelected: (conversationId: string) => void;
  onSelectAll: () => void;
  onClearSelected: () => void;
  onDeleteSelected: () => void;
  onNew: () => void;
  onSelect: (conversation: ConversationSummary) => void;
  onDelete: (conversations: ConversationSummary[]) => void;
  onClose: () => void;
}) {
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [menuId, setMenuId] = useState<string | null>(null);
  const collapsed = collapsedPreference && !open;
  const allSelected = conversations.length > 0 && selectedIds.size === conversations.length;

  useEffect(() => {
    if (!menuId) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMenuId(null);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [menuId]);

  function startRename(conversation: ConversationSummary) {
    setMenuId(null);
    setRenamingId(conversation.conversationId);
    setRenameValue(conversation.title);
  }

  function saveRename(conversation: ConversationSummary) {
    onRenameConversation(conversation.conversationId, renameValue);
    setRenamingId(null);
    setRenameValue("");
  }
  return (
    <>
      <aside
        className={`chat-history ${open ? "open" : ""} ${collapsed ? "collapsed" : ""}`}
        aria-label="Chat history"
      >
        <header>
          {!collapsed && (
            <button className="chat-history-new" onClick={onNew}>
              <SquarePen size={17} /> New chat
            </button>
          )}
          <button
            className="chat-history-collapse"
            aria-label={collapsed ? "Expand chat history" : "Collapse chat history"}
            title={collapsed ? "Expand chat history" : "Collapse chat history"}
            aria-expanded={!collapsed}
            aria-controls="chat-history-recent"
            onClick={onToggleCollapsed}
          >
            {collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
          </button>
          <button className="chat-history-close" aria-label="Close chat history" onClick={onClose}>
            <X size={17} />
          </button>
        </header>
        {collapsed && (
          <button
            className="chat-history-collapsed-new"
            aria-label="New chat"
            title="New chat"
            onClick={onNew}
          >
            <SquarePen size={17} />
          </button>
        )}
        {!collapsed && (
          <nav id="chat-history-recent" aria-label="Conversation history">
            <div className="chat-history-section-heading">
              <span>Recent</span>
              {conversations.length > 0 && (
                <button
                  type="button"
                  className="chat-history-manage"
                  aria-label={selecting ? "Done selecting conversations" : "Manage conversations"}
                  onClick={onToggleSelecting}
                >
                  {selecting ? "Done" : "Manage"}
                </button>
              )}
            </div>
            {totalConversations > 0 && (
              <div className="chat-history-search">
                <Search size={14} />
                <input
                  aria-label="Search conversations"
                  placeholder="Search chats"
                  value={query}
                  onChange={(event) => onQueryChange(event.target.value)}
                />
                {query && (
                  <button
                    type="button"
                    aria-label="Clear conversation search"
                    onClick={() => onQueryChange("")}
                  >
                    <X size={13} />
                  </button>
                )}
              </div>
            )}
            {selecting && (
              <div className="chat-history-selection-toolbar" role="group" aria-label="Conversation selection">
                <button type="button" onClick={allSelected ? onClearSelected : onSelectAll}>
                  {allSelected ? "Clear all" : "Select all"}
                </button>
                <span>{selectedIds.size} selected</span>
                <button
                  type="button"
                  className="danger"
                  aria-label="Delete selected conversations"
                  disabled={selectedIds.size === 0}
                  onClick={onDeleteSelected}
                >
                  <Trash2 size={14} /> Delete
                </button>
              </div>
            )}
            {conversations.length ? conversations.map((conversation) => {
              const selected = selectedIds.has(conversation.conversationId);
              return (
                <div
                  key={conversation.conversationId}
                  className={`chat-history-row ${conversation.firstRecord.key === activeKey ? "active" : ""} ${selecting ? "selecting" : ""} ${selected ? "selected" : ""}`}
                >
                  {selecting && (
                    <button
                      type="button"
                      className="chat-history-select"
                      role="checkbox"
                      aria-checked={selected}
                      aria-label={`Select conversation ${conversation.title}`}
                      onClick={() => onToggleSelected(conversation.conversationId)}
                    >
                      {selected ? <CheckSquare2 size={16} /> : <Square size={16} />}
                    </button>
                  )}
                  <button
                    className="chat-history-open"
                    onClick={() => {
                      setMenuId(null);
                      if (selecting) onToggleSelected(conversation.conversationId);
                      else onSelect(conversation);
                    }}
                  >
                    <strong>{conversation.title}</strong>
                    <small>
                      {shortModelName(conversation.firstRecord.modelName)}
                      {conversation.turnCount > 1 ? ` · ${conversation.turnCount} turns` : ""}
                    </small>
                  </button>
                  {!selecting && (
                    <button
                      type="button"
                      className="chat-history-more"
                      aria-label={`Conversation actions for ${conversation.title}`}
                      aria-expanded={menuId === conversation.conversationId}
                      title="Conversation actions"
                      onClick={() => setMenuId((current) =>
                        current === conversation.conversationId ? null : conversation.conversationId
                      )}
                    >
                      <MoreHorizontal size={16} />
                    </button>
                  )}
                  {!selecting && menuId === conversation.conversationId && (
                    <div className="chat-history-menu" role="menu" aria-label={`Actions for ${conversation.title}`}>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          onTogglePin(conversation.conversationId);
                          setMenuId(null);
                        }}
                      >
                        <Pin size={13} fill={conversationMeta[conversation.conversationId]?.pinned ? "currentColor" : "none"} />
                        {conversationMeta[conversation.conversationId]?.pinned ? "Unpin" : "Pin"}
                      </button>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => startRename(conversation)}
                      >
                        <Pencil size={13} /> Rename
                      </button>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          onExportConversation(conversation, "md");
                          setMenuId(null);
                        }}
                      >
                        <FileText size={13} /> Export Markdown
                      </button>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          onExportConversation(conversation, "json");
                          setMenuId(null);
                        }}
                      >
                        <Braces size={13} /> Export JSON
                      </button>
                      <button
                        type="button"
                        role="menuitem"
                        className="danger"
                        onClick={() => {
                          setMenuId(null);
                          onDelete([conversation]);
                        }}
                      >
                        <Trash2 size={13} /> Delete
                      </button>
                    </div>
                  )}
                  {renamingId === conversation.conversationId && (
                    <form
                      className="chat-history-rename"
                      onSubmit={(event) => {
                        event.preventDefault();
                        saveRename(conversation);
                      }}
                    >
                      <input
                        autoFocus
                        aria-label={`New name for ${conversation.title}`}
                        maxLength={80}
                        value={renameValue}
                        onChange={(event) => setRenameValue(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === "Escape") {
                            setRenamingId(null);
                            setRenameValue("");
                          }
                        }}
                      />
                      <button type="submit" aria-label="Save conversation name">
                        <Check size={13} />
                      </button>
                      <button
                        type="button"
                        aria-label="Cancel conversation rename"
                        onClick={() => {
                          setRenamingId(null);
                          setRenameValue("");
                        }}
                      >
                        <X size={13} />
                      </button>
                    </form>
                  )}
                </div>
              );
            }) : (
              <p>{query ? "No conversations match your search." : "No conversations yet."}</p>
            )}
          </nav>
        )}
      </aside>
      {open && <button className="chat-history-backdrop" aria-label="Close chat history" onClick={onClose} />}
    </>
  );
}

function DeleteConversationsDialog({ conversations, onCancel, onConfirm }: {
  conversations: ConversationSummary[];
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const count = conversations.length;
  const title = count === 1 ? "Delete this conversation?" : `Delete ${count} conversations?`;
  return (
    <div className="chat-delete-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onCancel();
    }}>
      <section role="dialog" aria-modal="true" aria-labelledby="chat-delete-title" className="chat-delete-dialog">
        <header>
          <div>
            <span>Chat history</span>
            <h2 id="chat-delete-title">{title}</h2>
          </div>
          <button aria-label="Close remove confirmation" onClick={onCancel}><X size={18} /></button>
        </header>
        <p>
          This removes{" "}
          {count === 1
            ? <strong>{conversations[0].title}</strong>
            : <strong>{count} conversations</strong>}{" "}
          from Chat history. Workspace source files are not modified.
        </p>
        <footer>
          <button autoFocus onClick={onCancel}>Cancel</button>
          <button className="danger" onClick={onConfirm}>
            <Trash2 size={15} /> {count === 1 ? "Delete conversation" : `Delete ${count} conversations`}
          </button>
        </footer>
      </section>
    </div>
  );
}

function modelCapabilityHint(model: string) {
  if (model.includes("Qwen2.5-7B")) {
    return "Qwen2.5-7B supports neuron, residual, attention, patching, steering, NLA, and J-Lens analysis from bundled local artifacts.";
  }
  if (model.includes("gemma-2-9b")) {
    return "Gemma-2-9B-it adds Neuronpedia SAE presets on top of neuron, residual, attention, patching, and steering analysis.";
  }
  if (model.includes("gemma-3")) {
    return "Gemma-3 models support residual, attention, MLP, patching, and steering; SAE and NLA need matching local artifacts.";
  }
  if (model.includes("tiny-gpt2")) {
    return "tiny-gpt2 is a lightweight smoke-test model; deeper evidence depends on the local caches available for it.";
  }
  return "Available analyses depend on the local artifacts and NLA/SAE profiles bundled for this model.";
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

function conversationMaxNewTokens(run: ExplorerRun) {
  const promptRunner = run.metadata?.promptRunner;
  if (!promptRunner || typeof promptRunner !== "object") return null;
  const value = (promptRunner as Record<string, unknown>).maxNewTokens;
  return typeof value === "number" && Number.isInteger(value) && value > 0 ? value : null;
}

function clampInteger(value: string, minimum: number, maximum: number) {
  const parsed = Number(value);
  return Number.isInteger(parsed)
    ? Math.max(minimum, Math.min(maximum, parsed))
    : minimum;
}

function userPromptForRun(run: ExplorerRun) {
  const promptRunner = run.metadata?.promptRunner;
  if (promptRunner && typeof promptRunner === "object") {
    const value = (promptRunner as Record<string, unknown>).userPrompt;
    if (typeof value === "string" && value.trim()) return value;
  }
  return promptTextFromTemplate(run.prompt);
}

function promptTextFromTemplate(prompt: string) {
  const patterns = [
    /<\|im_start\|>user\n(.*?)<\|im_end\|>/gs,
    /<start_of_turn>user\n(.*?)<end_of_turn>/gs,
    /(?:^|\n)User:\s*(.*?)(?=\nAssistant:|$)/gs
  ];
  for (const pattern of patterns) {
    const matches = [...prompt.matchAll(pattern)];
    const value = matches[matches.length - 1]?.[1]?.trim();
    if (value) return value;
  }
  return prompt;
}

function conversationRelatedKeys(items: ConversationSummary[], records: RunRecord[]) {
  const relatedKeys = new Set<string>();
  for (const conversation of items) {
    for (const record of conversation.records) relatedKeys.add(record.key);
  }
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
  return relatedKeys;
}

function persistHiddenRunKeys(keys: Set<string>) {
  try {
    window.localStorage.setItem(HIDDEN_RUN_STORAGE_KEY, JSON.stringify([...keys]));
  } catch {
    // The current tab still hides the entries when storage is unavailable.
  }
}

function loadConversationMeta(): ConversationMetaMap {
  try {
    const value: unknown = JSON.parse(
      window.localStorage.getItem(CONVERSATION_META_STORAGE_KEY) ?? "{}"
    );
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    const result: ConversationMetaMap = {};
    for (const [key, entry] of Object.entries(value)) {
      if (!entry || typeof entry !== "object" || Array.isArray(entry)) continue;
      const record = entry as Record<string, unknown>;
      result[key] = {
        title: typeof record.title === "string" && record.title.trim() ? record.title : undefined,
        pinned: record.pinned === true
      };
    }
    return result;
  } catch {
    return {};
  }
}

function downloadTextFile(name: string, mime: string, content: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

function loadHiddenRunKeys() {
  try {
    const value: unknown = JSON.parse(window.localStorage.getItem(HIDDEN_RUN_STORAGE_KEY) ?? "[]");
    return new Set(Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : []);
  } catch {
    return new Set<string>();
  }
}

function loadHistoryCollapsed() {
  try {
    return window.localStorage.getItem(HISTORY_COLLAPSED_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}
