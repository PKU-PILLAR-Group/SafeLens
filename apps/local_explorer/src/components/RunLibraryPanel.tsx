import { useEffect, useId, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Database,
  FileJson,
  GitMerge,
  HardDrive,
  PackageOpen,
  Search,
  Sparkles,
  Trash2,
  Upload,
  X
} from "lucide-react";

import { AsyncStatePanel } from "./AsyncStatePanel";
import { AdaptiveRunSelector } from "./AdaptiveRunSelector";
import { formatArtifactIssues, parseExplorerArtifact } from "../schemas/explorerArtifact";
import {
  explorerSessionSchema,
  isExplorerSessionCandidate,
  type ExplorerSession
} from "../schemas/explorerSession";
import type {
  LoadedRunRecord,
  RemoteRunState,
  RunLibraryMessage,
  RunRecord,
  RunSourceAlternative
} from "../state/useRunLibrary";
import type { ExplorerRun } from "../types";
import { useModalDialog } from "../state/useModalDialog";

const MAX_FILE_BYTES = 4 * 1024 * 1024;
const RUN_WINDOW_SIZE = 8;
type SourceFilter = "all" | Exclude<RunRecord["sourceType"], "bundled">;

interface RunLibraryPanelProps {
  records: RunRecord[];
  activeRecord: LoadedRunRecord;
  message: RunLibraryMessage | null;
  remoteState: RemoteRunState;
  onMessage: (message: RunLibraryMessage | null) => void;
  onSelect: (key: string) => void;
  onAdd: (runs: ExplorerRun[], sourceName: string, schemaVersion: string) => boolean;
  onRemove: (key: string) => void;
  onRestoreSession: (session: ExplorerSession) => void;
  onRefreshRemote: () => void;
  onCancelRemote: () => void;
}

export function RunLibraryPanel({
  records,
  activeRecord,
  message,
  remoteState,
  onMessage,
  onSelect,
  onAdd,
  onRemove,
  onRestoreSession,
  onRefreshRemote,
  onCancelRemote
}: RunLibraryPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");
  const [windowStart, setWindowStart] = useState(0);
  const [pendingRemoval, setPendingRemoval] = useState<RunRecord | null>(null);
  const panelRef = useRef<HTMLElement>(null);
  const externalRecords = useMemo(
    () => records
      .filter((record) =>
        record.sourceType !== "bundled" ||
        record.sourceAlternatives?.some((source) => source.sourceType !== "bundled")
      )
      .sort(compareRecentRecords),
    [records]
  );
  const filteredRecords = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return externalRecords.filter((record) => {
      if (
        sourceFilter !== "all" &&
        record.sourceType !== sourceFilter &&
        !record.sourceAlternatives?.some((source) => source.sourceType === sourceFilter)
      ) return false;
      if (!normalized) return true;
      return [
        record.runId,
        record.sampleId,
        record.modelName,
        record.sourceName,
        sourceLabel(record.sourceType),
        ...runSearchTimeValues(record.lastUsedAt),
        ...runSearchTimeValues(record.importedAt),
        ...(record.sourceAlternatives ?? []).flatMap((source) => [
          source.sourceName,
          source.modelName,
          sourceLabel(source.sourceType),
          ...runSearchTimeValues(source.importedAt)
        ])
      ].some((value) => value.toLowerCase().includes(normalized));
    });
  }, [externalRecords, query, sourceFilter]);
  const clampedWindowStart = Math.min(
    windowStart,
    Math.max(0, filteredRecords.length - RUN_WINDOW_SIZE)
  );
  const visibleRecords = filteredRecords.slice(
    clampedWindowStart,
    clampedWindowStart + RUN_WINDOW_SIZE
  );

  useEffect(() => {
    setWindowStart(0);
  }, [query, sourceFilter]);

  async function importFile(file: File | undefined) {
    if (!file) return;
    if (file.size > MAX_FILE_BYTES) {
      onMessage({
        tone: "error",
        title: "Artifact is too large for local JSON loading",
        details: [`${formatBytes(file.size)} exceeds the ${formatBytes(MAX_FILE_BYTES)} limit.`]
      });
      return;
    }
    let input: unknown;
    try {
      input = JSON.parse(await file.text());
    } catch (error) {
      onMessage({
        tone: "error",
        title: "Artifact is not valid JSON",
        details: [file.name],
        diagnostics: [{
          path: "artifact",
          issueType: "invalid_json",
          expected: "valid JSON document",
          actual: error instanceof Error ? error.message : "JSON parsing failed",
          message: "The file could not be parsed before schema validation."
        }]
      });
      return;
    }
    if (isExplorerSessionCandidate(input)) {
      const session = explorerSessionSchema.safeParse(input);
      if (!session.success) {
        onMessage({
          tone: "error",
          title: "Analysis session validation failed",
          details: [file.name],
          diagnostics: formatArtifactIssues(session.error.issues, input)
        });
        return;
      }
      onRestoreSession(session.data as ExplorerSession);
      return;
    }
    const parsed = parseExplorerArtifact(input);
    if (!parsed.success) {
      onMessage({
        tone: "error",
        title: "Artifact schema validation failed",
        details: [file.name],
        diagnostics: parsed.diagnostics
      });
      return;
    }
    onAdd(parsed.runs, file.name, parsed.schemaVersion);
  }

  function confirmRemoval() {
    if (!pendingRemoval) return;
    const key = pendingRemoval.key;
    setPendingRemoval(null);
    onRemove(key);
    window.requestAnimationFrame(() => {
      const selector = panelRef.current
        ?.querySelector<HTMLElement>('[aria-label="Run and sample selector"]');
      if (selector?.isConnected && selector.getClientRects().length > 0) {
        selector.focus();
        return;
      }
      const mobileTrigger = Array.from(
        document.querySelectorAll<HTMLElement>('[aria-label="Open run library"]')
      ).find((element) => element.getClientRects().length > 0);
      mobileTrigger?.focus();
    });
  }

  return <>
    <section ref={panelRef} className="panel-section run-library-panel">
      <div className="section-heading">
        <FileJson size={16} />
        <span>Run library</span>
        <b>{records.length}</b>
      </div>

      <div className="run-library-controls">
        <label>
          <span>Run / sample</span>
          <AdaptiveRunSelector
            records={records}
            ariaLabel="Run and sample selector"
            value={activeRecord.key}
            onChange={onSelect}
          />
        </label>
        <button className="import-artifact-button" onClick={() => inputRef.current?.click()}>
          <Upload size={14} /> Import JSON
        </button>
        <input
          ref={inputRef}
          className="visually-hidden"
          type="file"
          accept="application/json,.json"
          aria-label="Import Explorer artifact JSON"
          onChange={(event) => {
            void importFile(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </div>

      <AsyncStatePanel
        status={remoteState.status}
        label={remoteStatusLabel(remoteState)}
        detail={remoteState.detail}
        ariaLabel="Workspace API status"
        onCancel={onCancelRemote}
        onRetry={onRefreshRemote}
        cancelLabel="Cancel workspace discovery"
        retryLabel="Retry workspace discovery"
      />

      {remoteState.diagnostics.length > 0 && (
        <details className="workspace-diagnostics">
          <summary>{remoteState.diagnostics.length} workspace diagnostic{remoteState.diagnostics.length === 1 ? "" : "s"}</summary>
          {remoteState.diagnostics.map((detail, index) => (
            <span key={`${index}-${detail}`}>{detail}</span>
          ))}
        </details>
      )}

      <div className="active-run-card">
        <div>
          <strong>{activeRecord.sampleId}</strong>
          <SourceBadge record={activeRecord} />
        </div>
        <span>{activeRecord.modelName}</span>
        <span>
          {activeRecord.tokenCount} tokens · {activeRecord.layerCount} layers
        </span>
        <SourceResolution record={activeRecord} />
      </div>

      {message && (
        <div className={`run-library-message ${message.tone}`} role={message.tone === "error" ? "alert" : "status"}>
          {message.tone === "error" ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}
          <div>
            <strong>{message.title}</strong>
            {message.details.map((detail) => <span key={detail}>{detail}</span>)}
            {message.diagnostics && message.diagnostics.length > 0 && (
              <ol className="artifact-diagnostic-list" aria-label="Artifact validation diagnostics">
                {message.diagnostics.map((diagnostic, index) => (
                  <li key={`${diagnostic.path}-${diagnostic.issueType}-${index}`}>
                    <div className="artifact-diagnostic-heading">
                      <code>{diagnostic.path}</code>
                      <span>{diagnostic.issueType}</span>
                    </div>
                    <dl>
                      <div>
                        <dt>Expected</dt>
                        <dd>{diagnostic.expected}</dd>
                      </div>
                      <div>
                        <dt>Actual</dt>
                        <dd>{diagnostic.actual}</dd>
                      </div>
                    </dl>
                    <p>{diagnostic.message}</p>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      )}

      {externalRecords.length > 0 && (
        <div className="run-browser">
          <div className="run-browser-filters">
            <label>
              <span><Search size={12} /> Find run</span>
              <input
                type="search"
                value={query}
                placeholder="run, sample, model, date"
                aria-label="Search available runs"
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <label>
              <span>Source</span>
              <select
                aria-label="Filter runs by source"
                value={sourceFilter}
                onChange={(event) => setSourceFilter(event.target.value as SourceFilter)}
              >
                <option value="all">All</option>
                <option value="remote">Workspace</option>
                <option value="local">Imported</option>
                <option value="generated">Generated</option>
              </select>
            </label>
          </div>

          {filteredRecords.length > 0 ? <>
            <div className="run-browser-window" aria-label="Run browser window" aria-live="polite">
              <span>
                {clampedWindowStart + 1}-{Math.min(clampedWindowStart + RUN_WINDOW_SIZE, filteredRecords.length)} of {filteredRecords.length}
              </span>
              <div>
                <button
                  aria-label="Previous run window"
                  title="Previous runs"
                  disabled={clampedWindowStart === 0}
                  onClick={() => setWindowStart(Math.max(0, clampedWindowStart - RUN_WINDOW_SIZE))}
                ><ChevronLeft size={14} /></button>
                <button
                  aria-label="Next run window"
                  title="Next runs"
                  disabled={clampedWindowStart + RUN_WINDOW_SIZE >= filteredRecords.length}
                  onClick={() => setWindowStart(clampedWindowStart + RUN_WINDOW_SIZE)}
                ><ChevronRight size={14} /></button>
              </div>
            </div>
            <div className="recent-run-list" aria-label="Available workspace and imported runs">
              {visibleRecords.map((record) => (
            <div
              key={record.key}
              className={`${record.key === activeRecord.key ? "active" : ""} ${record.sourceType} ${record.sourceType === "local" || record.sourceType === "generated" ? "removable" : "read-only"}`}
            >
              <button onClick={() => onSelect(record.key)}>
                <span className="recent-run-heading">
                  <strong>{record.runId}</strong>
                  <SourceBadge record={record} compact />
                </span>
                <span className="recent-run-context">
                  {record.sampleId} · {record.modelName}
                </span>
                <span className="recent-run-dimensions">
                  {record.tokenCount} tokens · {record.layerCount} layers · {record.sourceName}
                </span>
                <span className="recent-run-times">
                  <Clock3 size={10} aria-hidden="true" />
                  <RunTimestamp label="Opened" value={record.lastUsedAt} empty="not opened" />
                  <RunTimestamp label="Updated" value={record.importedAt} empty="unknown" />
                </span>
                {Boolean(record.sourceAlternatives?.length) && (
                  <span className="run-source-conflict-summary">
                    <GitMerge size={11} aria-hidden="true" />
                    <b>{1 + (record.sourceAlternatives?.length ?? 0)} sources</b>
                    <span>
                      using {sourceLabel(record.sourceType)} over {sourceListLabel(record.sourceAlternatives ?? [])}
                    </span>
                  </span>
                )}
              </button>
              {(record.sourceType === "local" || record.sourceType === "generated") && (
                <button
                  aria-label={`Review removal of browser artifact ${record.runId} ${record.sampleId}`}
                  title="Review browser artifact removal"
                  onClick={() => setPendingRemoval(record)}
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>
              ))}
            </div>
          </> : (
            <div className="run-browser-empty" role="status">
              <Search size={15} /> No runs match this filter.
            </div>
          )}
        </div>
      )}
    </section>
    {pendingRemoval && (
      <RunRemovalDialog
        record={pendingRemoval}
        active={pendingRemoval.key === activeRecord.key}
        onCancel={() => setPendingRemoval(null)}
        onConfirm={confirmRemoval}
      />
    )}
  </>;
}

function RunRemovalDialog({
  record,
  active,
  onCancel,
  onConfirm
}: {
  record: RunRecord;
  active: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const titleId = useId();
  const dialogRef = useRef<HTMLElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  useModalDialog({
    open: true,
    dialogRef,
    initialFocusRef: cancelButtonRef,
    onClose: onCancel
  });

  return createPortal(
    <div
      className="run-removal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onCancel();
      }}
    >
      <section
        ref={dialogRef}
        className="run-removal-dialog"
        role="dialog"
        tabIndex={-1}
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <header>
          <div>
            <span><HardDrive size={13} /> Browser storage</span>
            <h2 id={titleId}>Remove browser artifact?</h2>
          </div>
          <button aria-label="Close removal confirmation" onClick={onCancel}>
            <X size={18} />
          </button>
        </header>
        <p>
          This removes the saved browser copy from this profile. Workspace files and the bundled
          package remain unchanged.
        </p>
        <dl className="run-removal-metadata">
          <div><dt>Run</dt><dd>{record.runId}</dd></div>
          <div><dt>Sample</dt><dd>{record.sampleId}</dd></div>
          <div><dt>Source</dt><dd>{record.sourceName}</dd></div>
          <div><dt>Type</dt><dd>{record.sourceType === "generated" ? "Generated result" : "Imported artifact"}</dd></div>
          <div><dt>Shape</dt><dd>{record.tokenCount} tokens · {record.layerCount} layers</dd></div>
        </dl>
        {active && (
          <div className="run-removal-active-note">
            <AlertTriangle size={14} />
            <span>This is the active Run. SafeLens will return to the bundled Run.</span>
          </div>
        )}
        <footer>
          <button ref={cancelButtonRef} onClick={onCancel}>Cancel</button>
          <button className="destructive" onClick={onConfirm}>
            <Trash2 size={14} /> Remove browser copy
          </button>
        </footer>
      </section>
    </div>,
    document.body
  );
}

function SourceBadge({ record, compact = false }: { record: RunRecord; compact?: boolean }) {
  const Icon = sourceIcon(record.sourceType);
  const conflictCount = 1 + (record.sourceAlternatives?.length ?? 0);
  return (
    <span className={`status-pill status-${record.sourceType}${compact ? " compact" : ""}`}>
      <Icon size={compact ? 9 : 11} aria-hidden="true" />
      <span>
        {sourceLabel(record.sourceType)}{record.hydration?.mode === "partial" ? " · range" : ""}
      </span>
      {conflictCount > 1 && <b>{conflictCount} sources</b>}
    </span>
  );
}

function RunTimestamp({
  label,
  value,
  empty
}: {
  label: string;
  value?: string;
  empty: string;
}) {
  const timestamp = value ? Date.parse(value) : Number.NaN;
  return (
    <span>
      <b>{label}</b>
      {Number.isFinite(timestamp) && value ? (
        <time dateTime={new Date(timestamp).toISOString()}>{recentTimeLabel(value)}</time>
      ) : (
        <em>{value && value !== "unknown" ? value : empty}</em>
      )}
    </span>
  );
}

function SourceResolution({ record }: { record: RunRecord }) {
  const alternatives = record.sourceAlternatives ?? [];
  if (alternatives.length === 0) return null;
  const selectedSource: RunSourceAlternative = {
    sourceType: record.sourceType,
    sourceName: record.sourceName,
    importedAt: record.importedAt,
    artifactId: record.artifactId,
    modelName: record.modelName,
    tokenCount: record.tokenCount,
    layerCount: record.layerCount,
    loaded: record.run !== null
  };
  return (
    <details className="run-source-resolution">
      <summary>
        <GitMerge size={12} aria-hidden="true" />
        <span>{1 + alternatives.length} indexed sources</span>
        <b>using {sourceLabel(record.sourceType)}</b>
      </summary>
      <div className="source-priority-rule">
        <span>Selection priority</span>
        <b>Bundled → browser artifact → workspace API</b>
      </div>
      <div className="source-candidate-list" role="list" aria-label="Run source candidates">
        <SourceCandidate source={selectedSource} selected selectedRecord={record} />
        {alternatives.map((source, index) => (
          <SourceCandidate
            key={`${source.sourceType}:${source.sourceName}:${source.artifactId ?? index}`}
            source={source}
            selected={false}
            selectedRecord={record}
          />
        ))}
      </div>
      <p>Lower-priority duplicates stay indexed, but values are never mixed across artifacts.</p>
    </details>
  );
}

function SourceCandidate({
  source,
  selected,
  selectedRecord
}: {
  source: RunSourceAlternative;
  selected: boolean;
  selectedRecord: RunRecord;
}) {
  const Icon = sourceIcon(source.sourceType);
  const metadataDiffers =
    source.modelName !== selectedRecord.modelName ||
    source.tokenCount !== selectedRecord.tokenCount ||
    source.layerCount !== selectedRecord.layerCount;
  return (
    <div className={`${selected ? "selected" : "shadowed"}${metadataDiffers ? " metadata-diff" : ""}`} role="listitem">
      <Icon size={12} aria-hidden="true" />
      <span>
        <b>{sourceLabel(source.sourceType)} · {source.sourceName}</b>
        <small>
          {source.modelName} · {source.tokenCount} tokens · {source.layerCount} layers · {sourceTimeLabel(source.importedAt)}
        </small>
      </span>
      <em>{selected ? "selected" : metadataDiffers ? "metadata differs" : "lower priority"}</em>
    </div>
  );
}

function sourceIcon(sourceType: RunRecord["sourceType"]) {
  if (sourceType === "bundled") return PackageOpen;
  if (sourceType === "local") return Upload;
  if (sourceType === "generated") return Sparkles;
  return Database;
}

function sourceListLabel(sources: RunSourceAlternative[]) {
  return [...new Set(sources.map((source) => sourceLabel(source.sourceType)))].join(" + ");
}

function sourceTimeLabel(value: string) {
  const parsed = new Date(value);
  if (!Number.isFinite(parsed.getTime())) return value;
  return `${parsed.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

function recentTimeLabel(value: string) {
  const parsed = new Date(value);
  if (!Number.isFinite(parsed.getTime())) return value;
  return `${parsed.toISOString().slice(5, 16).replace("T", " ")} UTC`;
}

function compareRecentRecords(left: RunRecord, right: RunRecord) {
  const leftUsed = left.lastUsedAt ? Date.parse(left.lastUsedAt) : Number.NaN;
  const rightUsed = right.lastUsedAt ? Date.parse(right.lastUsedAt) : Number.NaN;
  if (Number.isFinite(leftUsed) !== Number.isFinite(rightUsed)) {
    return Number.isFinite(rightUsed) ? 1 : -1;
  }
  if (Number.isFinite(leftUsed) && Number.isFinite(rightUsed) && leftUsed !== rightUsed) {
    return rightUsed - leftUsed;
  }
  const leftUpdated = Date.parse(left.importedAt);
  const rightUpdated = Date.parse(right.importedAt);
  return (Number.isFinite(rightUpdated) ? rightUpdated : 0) -
    (Number.isFinite(leftUpdated) ? leftUpdated : 0);
}

function runSearchTimeValues(value: string | undefined): string[] {
  if (!value) return [];
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return [value];
  const date = new Date(timestamp);
  return [value, date.toISOString(), date.toUTCString(), recentTimeLabel(value)];
}

function sourceLabel(sourceType: RunRecord["sourceType"]) {
  if (sourceType === "bundled") return "bundled";
  if (sourceType === "local") return "local";
  if (sourceType === "generated") return "generated";
  return "workspace";
}

function remoteStatusLabel(state: RemoteRunState) {
  switch (state.status) {
    case "idle": return "Workspace discovery idle";
    case "loading": return "Connecting to workspace";
    case "ready": return `${state.rootName} · ${state.loadedCount} ready`;
    case "empty": return `${state.rootName} · no runs found`;
    case "error": {
      if (state.failureKind === "offline") return "Workspace offline";
      if (state.failureKind === "api") return "Workspace API error";
      if (state.failureKind === "validation") return "Workspace schema error";
      return "Workspace data error";
    }
    case "cancelled": return "Workspace discovery cancelled";
  }
}

function formatBytes(bytes: number) {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
