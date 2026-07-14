import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  ExplorerApiError,
  fetchRemoteRun,
  fetchRemoteRunMetadata,
  fetchRemoteRunIndex,
  type RemoteRunSummary
} from "../api/explorerClient";
import { explorerRunSchema, type ArtifactDiagnostic } from "../schemas/explorerArtifact";
import type { ExplorerRun, PinnedEvidence, WorkspaceView } from "../types";
import type { AsyncStatus } from "../components/AsyncStatePanel";
import {
  buildPartialExplorerRun,
  fetchViewChunks,
  hydrateView,
  hydrationScope,
  isViewHydrated,
  mergeRunChunk,
  type RunHydration
} from "./remoteHydration";

const STORAGE_KEY = "safelens.localExplorer.importedRuns.v1";
const USAGE_STORAGE_KEY = "safelens.localExplorer.runUsage.v1";
const MAX_IMPORTED_RUNS = 6;
const MAX_USAGE_RECORDS = 100;
type RunHistoryMode = "push" | "replace" | "none";
type RunContextTransition = "fresh" | "restored";
const RUN_CONTEXT_TRANSITION_KEY = "safelensRunContextTransition";

export interface RunRecord {
  key: string;
  run: ExplorerRun | null;
  runId: string;
  sampleId: string;
  modelName: string;
  tokenCount: number;
  layerCount: number;
  sourceName: string;
  importedAt: string;
  sourceType: "bundled" | "local" | "remote" | "generated";
  artifactId?: string;
  builtIn: boolean;
  remoteSummary?: RemoteRunSummary;
  hydration?: RunHydration;
  sourceAlternatives?: RunSourceAlternative[];
  lastUsedAt?: string;
}

export interface RunSourceAlternative {
  sourceType: RunRecord["sourceType"];
  sourceName: string;
  importedAt: string;
  artifactId?: string;
  modelName: string;
  tokenCount: number;
  layerCount: number;
  loaded: boolean;
}

export interface LoadedRunRecord extends RunRecord {
  run: ExplorerRun;
}

export interface RunLibraryMessage {
  tone: "success" | "error";
  title: string;
  details: string[];
  diagnostics?: ArtifactDiagnostic[];
}

export interface RemoteRunState {
  status: AsyncStatus;
  failureKind?: "offline" | "api" | "validation" | "unknown";
  rootName: string;
  loadedCount: number;
  diagnostics: string[];
  detail: string;
}

export function useRunLibrary(builtInRun: ExplorerRun) {
  const builtInRecord = useMemo<RunRecord>(() => ({
    key: runKey(builtInRun),
    run: builtInRun,
    runId: builtInRun.runId,
    sampleId: builtInRun.sampleId,
    modelName: builtInRun.modelName,
    tokenCount: builtInRun.tokens.length,
    layerCount: builtInRun.layers.length,
    sourceName: "bundled real model cache",
    importedAt: "built in",
    sourceType: "bundled",
    builtIn: true,
    hydration: { mode: "full" }
  }), [builtInRun]);
  const [importedRecords, setImportedRecords] = useState<RunRecord[]>(loadImportedRecords);
  const [remoteRecords, setRemoteRecords] = useState<RunRecord[]>([]);
  const [remoteState, setRemoteState] = useState<RemoteRunState>({
    status: "idle",
    rootName: "workspace",
    loadedCount: 0,
    diagnostics: [],
    detail: "Workspace discovery has not started."
  });
  const remoteRequestRef = useRef<{ controller: AbortController; id: number } | null>(null);
  const remoteSampleRequestRef = useRef<{ controller: AbortController; key: string } | null>(null);
  const hydrationRequestRef = useRef<{ controller: AbortController; scope: string } | null>(null);
  const prefetchControllersRef = useRef(new Map<string, AbortController>());
  const prefetchScopesRef = useRef(new Set<string>());
  const prefetchGenerationRef = useRef(0);
  const [runUsage, setRunUsage] = useState<Record<string, string>>(loadRunUsage);
  const initialRequestedKey = requestedRunKey();
  const initialRequestedKeyRef = useRef(
    initialRequestedKey === builtInRecord.key ? undefined : initialRequestedKey
  );
  const nextRequestId = useRef(0);
  const records = useMemo(
    () => {
      const selected = new Map<string, RunRecord>();
      for (const record of [builtInRecord, ...importedRecords, ...remoteRecords]) {
        const current = selected.get(record.key);
        if (!current) {
          selected.set(record.key, {
            ...record,
            lastUsedAt: runUsage[record.key],
            sourceAlternatives: []
          });
          continue;
        }
        current.sourceAlternatives = [
          ...(current.sourceAlternatives ?? []),
          runSourceAlternative(record)
        ];
      }
      return [...selected.values()];
    },
    [builtInRecord, importedRecords, remoteRecords, runUsage]
  );
  const [activeKey, setActiveKey] = useState(
    () => initialRequestedKeyRef.current ?? builtInRecord.key
  );
  const [message, setMessage] = useState<RunLibraryMessage | null>(null);
  const activeRecord = (
    records.find((record) => record.key === activeKey && record.run !== null) ??
    records.find((record) => record.run !== null) ??
    builtInRecord
  ) as LoadedRunRecord;
  const requestedRecord = records.find((record) => record.key === activeKey);
  const resolvingRequestedRun =
    activeRecord.key !== activeKey && (
      remoteState.status === "idle" ||
      remoteState.status === "loading" ||
      requestedRecord?.run === null
    );

  useEffect(() => {
    const usedAt = new Date().toISOString();
    setRunUsage((current) => {
      const next = Object.fromEntries(
        Object.entries({ ...current, [activeRecord.key]: usedAt })
          .sort((left, right) => right[1].localeCompare(left[1]))
          .slice(0, MAX_USAGE_RECORDS)
      );
      try {
        window.localStorage.setItem(USAGE_STORAGE_KEY, JSON.stringify(next));
      } catch {
        // Recent ordering remains available for this tab when persistence is unavailable.
      }
      return next;
    });
  }, [activeRecord.key]);

  const refreshRemote = useCallback(async () => {
    remoteRequestRef.current?.controller.abort();
    const controller = new AbortController();
    const id = ++nextRequestId.current;
    remoteRequestRef.current = { controller, id };
    setRemoteState((current) => ({
      ...current,
      status: "loading",
      failureKind: undefined,
      diagnostics: [],
      detail: "Connecting to the local workspace API..."
    }));
    try {
      const result = await fetchRemoteRunIndex(controller.signal);
      if (remoteRequestRef.current?.id !== id) return;
      let recordsFromApi = result.summaries.map<RunRecord>((summary) => ({
        key: runKey(summary),
        run: null,
        runId: summary.runId,
        sampleId: summary.sampleId,
        modelName: summary.modelName,
        tokenCount: summary.tokenCount,
        layerCount: summary.layerCount,
        sourceName: summary.sourceName,
        importedAt: summary.modifiedAt,
        sourceType: "remote",
        artifactId: summary.artifactId,
        builtIn: false,
        remoteSummary: summary
      }));
      const requestedKey = initialRequestedKeyRef.current;
      const requested = recordsFromApi.find((record) => record.key === requestedKey);
      if (requested?.remoteSummary) {
        const loaded = await loadRemoteSummary(
          requested.remoteSummary,
          controller.signal,
          requestedSelectionContext()
        );
        if (remoteRequestRef.current?.id !== id) return;
        recordsFromApi = recordsFromApi.map((record) =>
          record.key === requested.key ? { ...record, ...loaded } : record
        );
        if (initialRequestedKeyRef.current === requested.key) {
          setActiveKey(requested.key);
          initialRequestedKeyRef.current = undefined;
        }
      }
      setRemoteRecords(recordsFromApi);
      setRemoteState({
        status: recordsFromApi.length ? "ready" : "empty",
        rootName: result.rootName || "workspace",
        loadedCount: recordsFromApi.length,
        diagnostics: result.diagnostics,
        detail: recordsFromApi.length === 0
          ? "No Explorer artifacts were found. Bundled and imported runs remain available."
          : result.diagnostics.length
          ? `${recordsFromApi.length} sample${recordsFromApi.length === 1 ? "" : "s"} indexed with diagnostics.`
          : `${recordsFromApi.length} workspace sample${recordsFromApi.length === 1 ? "" : "s"} indexed; samples load on selection.`
      });
    } catch (error) {
      if (remoteRequestRef.current?.id !== id) return;
      if (controller.signal.aborted) {
        setRemoteState((current) => ({
          ...current,
          status: "cancelled",
          failureKind: undefined,
          detail: "Workspace discovery was cancelled. Bundled and imported runs remain available."
        }));
        return;
      }
      setRemoteState((current) => ({
        ...current,
        status: "error",
        failureKind: remoteFailureKind(error),
        diagnostics: [error instanceof Error ? error.message : "Workspace discovery failed."],
        detail: error instanceof TypeError
          ? "Workspace API is offline. Bundled and imported runs remain available."
          : error instanceof ExplorerApiError
            ? error.message
            : "Workspace discovery failed. Bundled and imported runs remain available."
      }));
    } finally {
      if (remoteRequestRef.current?.id === id) remoteRequestRef.current = null;
    }
  }, []);

  const cancelRemote = useCallback(() => {
    const cancellingDiscovery = Boolean(remoteRequestRef.current);
    remoteRequestRef.current?.controller.abort();
    remoteSampleRequestRef.current?.controller.abort();
    hydrationRequestRef.current?.controller.abort();
    cancelPrefetch();
    setRemoteRecords((current) => current.map((item) =>
      item.hydration?.mode === "partial" && item.hydration.loadingScope
        ? {
            ...item,
            hydration: {
              ...item.hydration,
              cancelledScopes: [...new Set([
                ...item.hydration.cancelledScopes,
                item.hydration.loadingScope
              ])],
              loadingScope: undefined
            }
          }
        : item
    ));
    setRemoteState((current) => ({
      ...current,
      status: "cancelled",
      failureKind: undefined,
      detail: cancellingDiscovery
        ? "Workspace discovery was cancelled. Bundled and imported runs remain available."
        : "Workspace loading was cancelled. Loaded ranges remain available."
    }));
  }, []);

  useEffect(() => {
    void refreshRemote();
    return () => {
      const pending = remoteRequestRef.current;
      remoteRequestRef.current = null;
      pending?.controller.abort();
      remoteSampleRequestRef.current?.controller.abort();
      remoteSampleRequestRef.current = null;
      hydrationRequestRef.current?.controller.abort();
      hydrationRequestRef.current = null;
      cancelPrefetch();
    };
  }, [refreshRemote]);

  useEffect(() => {
    if (resolvingRequestedRun) return;
    const params = new URLSearchParams(window.location.search);
    params.set("run", activeRecord.runId);
    params.set("sample", activeRecord.sampleId);
    writeLocation(params, "replace");
  }, [activeRecord.key, activeRecord.runId, activeRecord.sampleId, resolvingRequestedRun]);

  async function loadRemoteSummary(
    summary: RemoteRunSummary,
    signal: AbortSignal,
    context: { view: WorkspaceView; layer?: number; tokenIndex?: number; sourceTokenIndex?: number }
  ): Promise<Pick<RunRecord, "run" | "hydration">> {
    if (summary.chunkProtocol !== "safelens-chunks-v1") {
      return { run: await fetchRemoteRun(summary, signal), hydration: { mode: "full" } };
    }
    const metadata = await fetchRemoteRunMetadata(summary, signal);
    const shell = buildPartialExplorerRun(metadata);
    const layer = shell.layers.includes(context.layer ?? -1)
      ? context.layer as number
      : shell.layers[shell.layers.length - 1] ?? 0;
    const tokenIndex = Math.max(
      0,
      Math.min(shell.tokens.length - 1, context.tokenIndex ?? topTokenIndex(shell))
    );
    const run = await hydrateView(
      shell,
      summary,
      context.view,
      layer,
      tokenIndex,
      signal,
      context.sourceTokenIndex ?? tokenIndex
    );
    return {
      run,
      hydration: {
        mode: "partial",
        metadata,
        loadedScopes: [hydrationScope(
          context.view,
          layer,
          tokenIndex,
          context.sourceTokenIndex ?? tokenIndex
        )],
        errors: {},
        cancelledScopes: []
      }
    };
  }

  function cancelPrefetch() {
    prefetchGenerationRef.current += 1;
    for (const controller of prefetchControllersRef.current.values()) controller.abort();
    prefetchControllersRef.current.clear();
    prefetchScopesRef.current.clear();
  }

  function scheduleAdjacentPrefetch(
    record: LoadedRunRecord,
    view: WorkspaceView,
    layer: number,
    tokenIndex: number,
    sourceTokenIndex: number
  ) {
    if (
      record.hydration?.mode !== "partial" ||
      !record.remoteSummary ||
      record.run.tokens.length <= 512
    ) return;
    const blockStart = Math.floor(tokenIndex / 512) * 512;
    const targets = [blockStart - 1, blockStart + 512].filter(
      (target) => target >= 0 && target < record.run.tokens.length
    );
    const generation = prefetchGenerationRef.current;
    for (const target of targets) {
      const scope = hydrationScope(view, layer, target, sourceTokenIndex);
      const key = `${record.key}:${scope}`;
      if (
        record.hydration.loadedScopes.includes(scope) ||
        prefetchScopesRef.current.has(key)
      ) continue;
      prefetchScopesRef.current.add(key);
      const runWhenIdle = () => {
        if (generation !== prefetchGenerationRef.current) return;
        const controller = new AbortController();
        prefetchControllersRef.current.set(key, controller);
        void fetchViewChunks(
          record.run,
          record.remoteSummary!,
          view,
          layer,
          target,
          controller.signal,
          sourceTokenIndex
        ).then((chunks) => {
          if (generation !== prefetchGenerationRef.current) return;
          setRemoteRecords((current) => current.map((item) => {
            if (item.key !== record.key || !item.run || item.hydration?.mode !== "partial") return item;
            return {
              ...item,
              run: chunks.reduce((run, chunk) => mergeRunChunk(run, chunk), item.run),
              hydration: {
                ...item.hydration,
                loadedScopes: [...new Set([...item.hydration.loadedScopes, scope])]
              }
            };
          }));
        }).catch(() => {
          // Prefetch failures remain silent; foreground navigation retries with visible state.
          prefetchScopesRef.current.delete(key);
        }).finally(() => {
          prefetchControllersRef.current.delete(key);
        });
      };
      const requestIdle = (window as Window & {
        requestIdleCallback?: (callback: () => void, options?: { timeout: number }) => number;
      }).requestIdleCallback;
      if (requestIdle) {
        requestIdle(runWhenIdle, { timeout: 1_000 });
      } else {
        globalThis.setTimeout(runWhenIdle, 0);
      }
    }
  }

  function ensureViewHydrated(
    view: WorkspaceView,
    layer: number,
    tokenIndex: number,
    sourceTokenIndex = tokenIndex
  ) {
    const record = activeRecord;
    if (record.hydration?.mode !== "partial" || !record.remoteSummary) return;
    const partialHydration = record.hydration;
    if (isViewHydrated(record.hydration, view, layer, tokenIndex, sourceTokenIndex)) {
      scheduleAdjacentPrefetch(record, view, layer, tokenIndex, sourceTokenIndex);
      return;
    }
    const scope = hydrationScope(view, layer, tokenIndex, sourceTokenIndex);
    if (hydrationRequestRef.current?.scope === scope) return;
    cancelPrefetch();
    hydrationRequestRef.current?.controller.abort();
    const controller = new AbortController();
    hydrationRequestRef.current = { controller, scope };
    setRemoteRecords((current) => current.map((item) =>
      item.key === record.key && item.hydration?.mode === "partial"
        ? {
            ...item,
            hydration: {
              ...item.hydration,
              loadingScope: scope,
              cancelledScopes: item.hydration.cancelledScopes.filter((item) => item !== scope)
            }
          }
        : item
    ));
    setRemoteState((current) => ({
      ...current,
      status: "loading",
      detail: `Loading ${view} range data for L${layer}, token ${tokenIndex}...`
    }));
    void hydrateView(
      record.run,
      record.remoteSummary,
      view,
      layer,
      tokenIndex,
      controller.signal,
      sourceTokenIndex
    ).then((run) => {
      if (hydrationRequestRef.current?.scope !== scope) return;
      setRemoteRecords((current) => current.map((item) => {
        if (item.key !== record.key || item.hydration?.mode !== "partial") return item;
        return {
          ...item,
          run,
          hydration: {
            ...item.hydration,
            loadedScopes: [...new Set([...item.hydration.loadedScopes, scope])],
            loadingScope: undefined,
            errors: omitKey(item.hydration.errors, scope),
            cancelledScopes: item.hydration.cancelledScopes.filter((item) => item !== scope)
          }
        };
      }));
      scheduleAdjacentPrefetch(
        { ...record, run, hydration: {
          ...partialHydration,
          loadedScopes: [...new Set([...partialHydration.loadedScopes, scope])],
          errors: omitKey(partialHydration.errors, scope),
          cancelledScopes: partialHydration.cancelledScopes.filter((item) => item !== scope)
        } },
        view,
        layer,
        tokenIndex,
        sourceTokenIndex
      );
      setRemoteState((current) => ({
        ...current,
        status: "ready",
        detail: `${current.loadedCount} workspace sample${current.loadedCount === 1 ? "" : "s"} indexed; selected range loaded.`
      }));
    }).catch((error) => {
      if (hydrationRequestRef.current?.scope !== scope || controller.signal.aborted) return;
      setRemoteRecords((current) => current.map((item) =>
        item.key === record.key && item.hydration?.mode === "partial"
          ? {
              ...item,
              hydration: {
                ...item.hydration,
                loadingScope: undefined,
                errors: {
                  ...item.hydration.errors,
                  [scope]: error instanceof Error ? error.message : "View data loading failed."
                },
                cancelledScopes: item.hydration.cancelledScopes.filter((item) => item !== scope)
              }
            }
          : item
      ));
      setRemoteState((current) => ({
        ...current,
        status: "error",
        diagnostics: [error instanceof Error ? error.message : "View data loading failed."],
        detail: `${view} range loading failed. Other loaded ranges remain available.`
      }));
    }).finally(() => {
      if (hydrationRequestRef.current?.scope === scope) hydrationRequestRef.current = null;
    });
  }

  function viewHydration(
    view: WorkspaceView,
    layer: number,
    tokenIndex: number,
    sourceTokenIndex = tokenIndex
  ) {
    const hydration = activeRecord.hydration;
    const scope = hydrationScope(view, layer, tokenIndex, sourceTokenIndex);
    return {
      partial: hydration?.mode === "partial",
      ready: isViewHydrated(hydration, view, layer, tokenIndex, sourceTokenIndex),
      loading: hydration?.mode === "partial" && hydration.loadingScope === scope,
      error: hydration?.mode === "partial" ? hydration.errors[scope] : undefined,
      cancelled: hydration?.mode === "partial" && hydration.cancelledScopes.includes(scope)
    };
  }

  async function loadFullActiveRun() {
    const record = activeRecord;
    if (record.hydration?.mode !== "partial" || !record.remoteSummary) return record.run;
    cancelPrefetch();
    hydrationRequestRef.current?.controller.abort();
    const controller = new AbortController();
    const scope = "full-run";
    hydrationRequestRef.current = { controller, scope };
    setRemoteState((current) => ({
      ...current,
      status: "loading",
      detail: `Loading the complete ${record.runId} artifact for export or experiments...`
    }));
    try {
      const run = await fetchRemoteRun(record.remoteSummary, controller.signal);
      if (hydrationRequestRef.current?.scope !== scope) return record.run;
      setRemoteRecords((current) => current.map((item) =>
        item.key === record.key ? { ...item, run, hydration: { mode: "full" } } : item
      ));
      setRemoteState((current) => ({
        ...current,
        status: "ready",
        detail: `${current.loadedCount} workspace sample${current.loadedCount === 1 ? "" : "s"} indexed; active sample fully loaded.`
      }));
      return run;
    } catch (error) {
      if (!controller.signal.aborted) {
        setRemoteState((current) => ({
          ...current,
          status: "error",
          diagnostics: [error instanceof Error ? error.message : "Full Run loading failed."],
          detail: "The complete artifact could not be loaded. Range visualization remains available."
        }));
      }
      throw error;
    } finally {
      if (hydrationRequestRef.current?.scope === scope) hydrationRequestRef.current = null;
    }
  }

  function selectRun(
    key: string,
    restore?: PinnedEvidence,
    historyMode: RunHistoryMode = "push"
  ) {
    const record = records.find((item) => item.key === key);
    if (!record) return;
    initialRequestedKeyRef.current = undefined;
    cancelPrefetch();
    remoteSampleRequestRef.current?.controller.abort();
    remoteSampleRequestRef.current = null;
    hydrationRequestRef.current?.controller.abort();
    hydrationRequestRef.current = null;
    if (record.run) {
      if (historyMode !== "none") {
        writeRunLocation(record, restore, historyMode);
      }
      setActiveKey(key);
      setMessage(null);
      return;
    }
    if (!record.remoteSummary) return;
    const controller = new AbortController();
    remoteSampleRequestRef.current = { controller, key };
    setActiveKey(key);
    setMessage(null);
    setRemoteState((current) => ({
      ...current,
      status: "loading",
      detail: `Loading ${record.runId} / ${record.sampleId} on demand...`
    }));
    const context = restore
      ? {
          view: restore.view,
          layer: restore.layer,
          tokenIndex: restore.tokenIndex,
          sourceTokenIndex: restore.sourceTokenIndex
        }
      : historyMode === "none"
        ? requestedSelectionContext()
        : { view: "overview" as WorkspaceView };
    void loadRemoteSummary(record.remoteSummary, controller.signal, context).then((loaded) => {
      if (remoteSampleRequestRef.current?.key !== key) return;
      if (historyMode !== "none") {
        writeRunLocation(record, restore, historyMode);
      }
      setRemoteRecords((current) => current.map((item) =>
        item.key === key ? { ...item, ...loaded } : item
      ));
      setRemoteState((current) => ({
        ...current,
        status: "ready",
        detail: `${current.loadedCount} workspace sample${current.loadedCount === 1 ? "" : "s"} indexed; selected sample loaded.`
      }));
    }).catch((error) => {
      if (remoteSampleRequestRef.current?.key !== key) return;
      setActiveKey(activeRecord.key);
      if (controller.signal.aborted) {
        setRemoteState((current) => ({
          ...current,
          status: "cancelled",
          detail: "Workspace sample loading was cancelled. The current analysis remains available."
        }));
        return;
      }
      setRemoteState((current) => ({
        ...current,
        status: "error",
        diagnostics: [error instanceof Error ? error.message : "Workspace sample loading failed."],
        detail: "The selected sample could not be loaded. The current analysis remains available."
      }));
    }).finally(() => {
      if (remoteSampleRequestRef.current?.key === key) remoteSampleRequestRef.current = null;
    });
  }

  function addRuns(runs: ExplorerRun[], sourceName: string, schemaVersion: string) {
    const importedAt = new Date().toISOString();
    const additions = runs.map<RunRecord>((run) => ({
      key: runKey(run),
      run,
      runId: run.runId,
      sampleId: run.sampleId,
      modelName: run.modelName,
      tokenCount: run.tokens.length,
      layerCount: run.layers.length,
      sourceName,
      importedAt,
      sourceType: "local",
      builtIn: false,
      hydration: { mode: "full" }
    }));
    const additionKeys = new Set(additions.map((record) => record.key));
    const next = [
      ...additions,
      ...importedRecords.filter((record) => !additionKeys.has(record.key))
    ].slice(0, MAX_IMPORTED_RUNS);

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch (error) {
      setMessage({
        tone: "error",
        title: "Artifact validated but could not be persisted",
        details: [error instanceof Error ? error.message : "Local storage quota was exceeded."]
      });
      return false;
    }
    initialRequestedKeyRef.current = undefined;
    setImportedRecords(next);
    const nextActiveRecord = additions[0];
    if (nextActiveRecord.key !== activeKey) {
      writeRunLocation(nextActiveRecord, undefined, "push");
      setActiveKey(nextActiveRecord.key);
    }
    setMessage({
      tone: "success",
      title: `${runs.length} sample${runs.length === 1 ? "" : "s"} loaded`,
      details: [`${sourceName} · schema ${schemaVersion}`]
    });
    return true;
  }

  function addGeneratedRun(
    run: ExplorerRun,
    jobId: string,
    restore?: {
      view: WorkspaceView;
      trackName?: string;
      metric: string;
      tokenIndex?: number;
      layer?: number;
      kind: "attribution" | "nla" | "patching" | "intervention";
    }
  ) {
    initialRequestedKeyRef.current = undefined;
    const record: RunRecord = {
      key: runKey(run),
      run,
      runId: run.runId,
      sampleId: run.sampleId,
      modelName: run.modelName,
      tokenCount: run.tokens.length,
      layerCount: run.layers.length,
      sourceName: `${restore?.kind ?? "prompt"} job ${jobId.slice(0, 8)}`,
      importedAt: new Date().toISOString(),
      sourceType: "generated",
      artifactId: jobId,
      builtIn: false,
      hydration: { mode: "full" }
    };
    const next = [record, ...importedRecords.filter((item) => item.key !== record.key)]
      .slice(0, MAX_IMPORTED_RUNS);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch (error) {
      setMessage({
        tone: "error",
        title: "Generated run is ready but could not be persisted",
        details: [error instanceof Error ? error.message : "Local storage quota was exceeded."]
      });
    }
    setImportedRecords(next);
    writeGeneratedRunLocation(record, restore, "push");
    setActiveKey(record.key);
    setMessage({
      tone: "success",
      title: `${restore?.kind === "nla" ? "NLA" : restore?.kind === "attribution" ? "Attribution" : restore?.kind === "patching" ? "Activation patching" : restore?.kind === "intervention" ? "Intervention comparison" : "Prompt analysis"} added to the Run Library`,
      details: [`${run.runId} / ${run.sampleId} · job ${jobId.slice(0, 8)}`]
    });
  }

  function removeRun(key: string) {
    initialRequestedKeyRef.current = undefined;
    const next = importedRecords.filter((record) => record.key !== key);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // Removing data remains useful even if persistence is unavailable.
    }
    setImportedRecords(next);
    setRunUsage((current) => {
      if (!(key in current)) return current;
      const nextUsage = { ...current };
      delete nextUsage[key];
      try {
        window.localStorage.setItem(USAGE_STORAGE_KEY, JSON.stringify(nextUsage));
      } catch {
        // The in-memory recent index still drops the removed browser artifact.
      }
      return nextUsage;
    });
    if (activeKey === key) {
      writeRunLocation(builtInRecord, undefined, "replace");
      setActiveKey(builtInRecord.key);
    }
  }

  useEffect(() => {
    function restoreRunFromHistory() {
      const key = requestedRunKey() ?? builtInRecord.key;
      if (key === activeKey) return;
      selectRun(key, undefined, "none");
    }

    window.addEventListener("popstate", restoreRunFromHistory);
    return () => window.removeEventListener("popstate", restoreRunFromHistory);
  }, [activeKey, builtInRecord.key, records]);

  return {
    records,
    activeRecord,
    message,
    setMessage,
    selectRun,
    addRuns,
    addGeneratedRun,
    removeRun,
    remoteState,
    refreshRemote,
    cancelRemote,
    ensureViewHydrated,
    viewHydration,
    loadFullActiveRun
  };
}

function writeGeneratedRunLocation(
  record: RunRecord,
  restore: {
    view: WorkspaceView;
    trackName?: string;
    metric: string;
    tokenIndex?: number;
    layer?: number;
    kind: "attribution" | "nla" | "patching" | "intervention";
  } | undefined,
  historyMode: Exclude<RunHistoryMode, "none">
) {
  const params = new URLSearchParams(window.location.search);
  clearSelectionParams(params);
  params.set("run", record.runId);
  params.set("sample", record.sampleId);
  if (!restore) {
    writeLocation(params, historyMode, { key: record.key, kind: "fresh" });
    return;
  }
  params.set("view", restore.view);
  if (restore.trackName) params.set("track", restore.trackName);
  if (restore.tokenIndex !== undefined) params.set("token", String(restore.tokenIndex));
  if (restore.layer !== undefined) params.set("layer", String(restore.layer));
  params.set("metric", restore.metric);
  params.set("normalization", restore.view === "intervention" ? "raw" : "normalized");
  writeLocation(params, historyMode, { key: record.key, kind: "restored" });
}

function runSourceAlternative(record: RunRecord): RunSourceAlternative {
  return {
    sourceType: record.sourceType,
    sourceName: record.sourceName,
    importedAt: record.importedAt,
    artifactId: record.artifactId,
    modelName: record.modelName,
    tokenCount: record.tokenCount,
    layerCount: record.layerCount,
    loaded: record.run !== null
  };
}

function writeRunLocation(
  record: RunRecord,
  evidence: PinnedEvidence | undefined,
  historyMode: Exclude<RunHistoryMode, "none">
) {
  const params = new URLSearchParams(window.location.search);
  clearSelectionParams(params);
  params.set("run", record.runId);
  params.set("sample", record.sampleId);
  if (!evidence) {
    writeLocation(params, historyMode, { key: record.key, kind: "fresh" });
    return;
  }
  params.set("view", evidence.view);
  params.set("token", String(evidence.tokenIndex));
  params.set("layer", String(evidence.layer));
  params.set("metric", evidence.metric);
  params.set("normalization", evidence.normalization);
  if (evidence.headId) params.set("head", evidence.headId);
  if (evidence.neuronId) params.set("neuron", evidence.neuronId);
  if (evidence.trackName) params.set("track", evidence.trackName);
  if (evidence.view === "nla" && isNlaComponent(evidence.component)) {
    params.set("nlaComponent", evidence.component);
  }
  if (evidence.sourceTokenIndex !== undefined) {
    params.set("source", String(evidence.sourceTokenIndex));
    params.set("target", String(evidence.tokenIndex));
    params.set("edge", "incoming");
  }
  writeLocation(params, historyMode, { key: record.key, kind: "restored" });
}

function clearSelectionParams(params: URLSearchParams) {
  for (const key of [
    "view", "token", "source", "target", "range", "layer", "head", "neuron",
    "track", "metric", "normalization", "edge", "nlaComponent", "mode"
  ]) {
    params.delete(key);
  }
}

function writeLocation(
  params: URLSearchParams,
  historyMode: Exclude<RunHistoryMode, "none">,
  transition?: { key: string; kind: RunContextTransition }
) {
  const nextLocation = `${window.location.pathname}?${params.toString()}${window.location.hash}`;
  const currentLocation = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (nextLocation === currentLocation) return;
  const nextState = transition
    ? { ...(window.history.state ?? {}), [RUN_CONTEXT_TRANSITION_KEY]: transition }
    : window.history.state;
  if (historyMode === "push") {
    window.history.pushState(nextState, "", nextLocation);
  } else {
    window.history.replaceState(nextState, "", nextLocation);
  }
}

export function consumeRunContextTransition(key: string): RunContextTransition | undefined {
  const state = window.history.state as Record<string, unknown> | null;
  const transition = state?.[RUN_CONTEXT_TRANSITION_KEY];
  if (!transition || typeof transition !== "object") return undefined;
  const candidate = transition as { key?: unknown; kind?: unknown };
  if (
    candidate.key !== key ||
    (candidate.kind !== "fresh" && candidate.kind !== "restored")
  ) {
    return undefined;
  }
  const nextState = { ...(state ?? {}) };
  delete nextState[RUN_CONTEXT_TRANSITION_KEY];
  window.history.replaceState(nextState, "", window.location.href);
  return candidate.kind;
}

function isNlaComponent(value: string): value is "resid_post" | "attn_result" | "mlp_out" {
  return value === "resid_post" || value === "attn_result" || value === "mlp_out";
}

function remoteFailureKind(
  error: unknown
): NonNullable<RemoteRunState["failureKind"]> {
  if (error instanceof TypeError) return "offline";
  if (error instanceof ExplorerApiError) {
    return error.code.startsWith("invalid_") ? "validation" : "api";
  }
  return "unknown";
}

export function runKey(run: Pick<ExplorerRun, "runId" | "sampleId">) {
  return `${run.runId}::${run.sampleId}`;
}

function requestedRunKey() {
  const params = new URLSearchParams(window.location.search);
  const runId = params.get("run");
  const sampleId = params.get("sample");
  return runId && sampleId ? `${runId}::${sampleId}` : undefined;
}

function loadRunUsage(): Record<string, string> {
  try {
    const stored = JSON.parse(window.localStorage.getItem(USAGE_STORAGE_KEY) ?? "{}");
    if (!stored || typeof stored !== "object" || Array.isArray(stored)) return {};
    return Object.fromEntries(
      Object.entries(stored)
        .filter((entry): entry is [string, string] =>
          typeof entry[0] === "string" &&
          typeof entry[1] === "string" &&
          Number.isFinite(Date.parse(entry[1]))
        )
        .sort((left, right) => right[1].localeCompare(left[1]))
        .slice(0, MAX_USAGE_RECORDS)
    );
  } catch {
    return {};
  }
}

function loadImportedRecords(): RunRecord[] {
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
    if (!Array.isArray(stored)) return [];
    return stored.flatMap((candidate): RunRecord[] => {
      if (!candidate || typeof candidate !== "object") return [];
      const parsed = explorerRunSchema.safeParse(candidate.run);
      if (!parsed.success) return [];
      const run = parsed.data as ExplorerRun;
      return [{
        key: runKey(run),
        run,
        runId: run.runId,
        sampleId: run.sampleId,
        modelName: run.modelName,
        tokenCount: run.tokens.length,
        layerCount: run.layers.length,
        sourceName: typeof candidate.sourceName === "string" ? candidate.sourceName : "local artifact",
        importedAt: typeof candidate.importedAt === "string" ? candidate.importedAt : "unknown",
        sourceType: candidate.sourceType === "generated" ? "generated" : "local",
        artifactId: typeof candidate.artifactId === "string" ? candidate.artifactId : undefined,
        builtIn: false,
        hydration: { mode: "full" }
      }];
    }).slice(0, MAX_IMPORTED_RUNS);
  } catch {
    return [];
  }
}

function requestedSelectionContext(): {
  view: WorkspaceView;
  layer?: number;
  tokenIndex?: number;
  sourceTokenIndex?: number;
} {
  const params = new URLSearchParams(window.location.search);
  const requestedView = params.get("view");
  const views: WorkspaceView[] = [
    "overview", "residual", "attention", "mlp", "nla", "patching", "intervention", "attribution"
  ];
  const layer = params.has("layer") ? Number(params.get("layer")) : Number.NaN;
  const tokenIndex = params.has("token") ? Number(params.get("token")) : Number.NaN;
  const sourceTokenIndex = params.has("source") ? Number(params.get("source")) : Number.NaN;
  return {
    view: views.includes(requestedView as WorkspaceView)
      ? requestedView as WorkspaceView
      : "overview",
    layer: Number.isInteger(layer) ? layer : undefined,
    tokenIndex: Number.isInteger(tokenIndex) ? tokenIndex : undefined,
    sourceTokenIndex: Number.isInteger(sourceTokenIndex) ? sourceTokenIndex : undefined
  };
}

function topTokenIndex(run: ExplorerRun) {
  return run.tokens.reduce(
    (best, token) => token.risk > run.tokens[best].risk ? token.index : best,
    run.tokens[0]?.index ?? 0
  );
}

function omitKey(values: Record<string, string>, key: string) {
  return Object.fromEntries(Object.entries(values).filter(([item]) => item !== key));
}
