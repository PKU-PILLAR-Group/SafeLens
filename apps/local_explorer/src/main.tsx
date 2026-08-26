import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  CircleHelp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Database,
  Crosshair,
  Download,
  FlaskConical,
  GitCompareArrows,
  Layers3,
  Network,
  PackageOpen,
  Pin,
  Info,
  Search,
  Save,
  SlidersHorizontal,
  Sparkles,
  Waves,
  X
} from "lucide-react";
import { realRun } from "./realRunData";
import { formatMetricDelta, formatMetricNumber, metricDisplayLabel } from "./metricFormatting";
import { MatrixHeatmap } from "./components/MatrixHeatmap";
import { RunLibraryPanel } from "./components/RunLibraryPanel";
import { PromptRunnerPanel } from "./components/PromptRunnerPanel";
import { TokenTimeline, type TimelineState } from "./components/TokenTimeline";
import {
  EvidenceInspector,
  type InspectorEvidence,
  type InspectorNextAction
} from "./components/EvidenceInspector";
import { ViewErrorBoundary } from "./components/ViewErrorBoundary";
import { retryableLazy } from "./components/retryableLazy";
import { AdaptiveRunSelector } from "./components/AdaptiveRunSelector";
import { OverviewEvidenceGraph } from "./components/OverviewEvidenceGraph";
import { QuickActionsDialog } from "./components/QuickActionsDialog";
import { ActionableEmptyState } from "./components/ActionableEmptyState";
import { ExplorerHome } from "./components/ExplorerHome";
import { DatasetTestScreen } from "./components/DatasetTestScreen";
import {
  LayerSelector,
  SelectionWorkbench,
  WorkspaceTabs
} from "./components/WorkspaceNavigation";
import { useExplorerSelection } from "./state/useExplorerSelection";
import { useModalDialog } from "./state/useModalDialog";
import { recordExplorerPerformance, useExplorerPerformance } from "./state/useExplorerPerformance";
import {
  attentionAggregationLabel,
  attentionDifferenceId,
  attentionHeadLabel,
  attentionHeadMetric,
  attentionHeadProvenance,
  attentionHeadSourceKey,
  isAttentionDifferenceAvailable,
  parseAttentionAggregation,
  parseAttentionRollout,
  resolveAttentionHead
} from "./attentionAggregation";
import {
  MatrixViewportSessionProvider,
  type MatrixViewportKey,
  type MatrixViewportSnapshot,
  type MatrixViewportSnapshots
} from "./state/matrixViewportSession";
import { consumeRunContextTransition, runKey, useRunLibrary } from "./state/useRunLibrary";
import {
  EXPLORER_SESSION_KIND,
  type ExplorerSession
} from "./schemas/explorerSession";
import type {
  AttentionHead,
  AttentionMatrixSnapshot,
  AttributionMethod,
  ComponentKind,
  EvidenceAssessment,
  EvidenceProfileSnapshot,
  ExplorerRun,
  ExplorerSelectionState,
  MetricProvenance,
  MLPNeuron,
  NLARow,
  NormalizationMode,
  InterventionGenerationSnapshot,
  PinnedEvidence,
  WorkspaceView
} from "./types";

interface PinCellOverrides {
  sourceTokenIndex?: number;
  neuronId?: string;
  nlaComponent?: NLARow["component"];
}
import type { PatchingMetric } from "./components/PatchingCausalMatrix";
import "./styles.css";

const AttentionPatternMatrix = retryableLazy(
  () => import("./components/AttentionPatternMatrix"), "AttentionPatternMatrix"
);
const ResidualLogitLens = retryableLazy(
  () => import("./components/ResidualLogitLens"), "ResidualLogitLens"
);
const MLPActivationMatrix = retryableLazy(
  () => import("./components/MLPActivationMatrix"), "MLPActivationMatrix"
);
const SignedAttributionMatrix = retryableLazy(
  () => import("./components/SignedAttributionMatrix"), "SignedAttributionMatrix"
);
const NLAFidelityMatrix = retryableLazy(
  () => import("./components/NLAFidelityMatrix"), "NLAFidelityMatrix"
);
const AttributionJobPanel = retryableLazy(
  () => import("./components/AttributionJobPanel"), "AttributionJobPanel"
);
const NLAJobPanel = retryableLazy(
  () => import("./components/NLAJobPanel"), "NLAJobPanel"
);
const PatchingJobPanel = retryableLazy(
  () => import("./components/PatchingJobPanel"), "PatchingJobPanel"
);
const PatchingCausalMatrix = retryableLazy(
  () => import("./components/PatchingCausalMatrix"), "PatchingCausalMatrix"
);
const InterventionJobPanel = retryableLazy(
  () => import("./components/InterventionJobPanel"), "InterventionJobPanel"
);
const InterventionComparison = retryableLazy(
  () => import("./components/InterventionComparison"), "InterventionComparison"
);
const CompareDrawer = retryableLazy(loadCompareDrawer, "CompareDrawer");

function loadCompareDrawer() {
  return import("./components/CompareDrawer");
}

function preloadCompareDrawer() {
  void loadCompareDrawer().catch(() => undefined);
}

const ExplorerRunContext = createContext<ExplorerRun>(realRun);
type EvidenceFilter = "top" | "neighborhood" | "all";
type WorkspaceLayout = "focus" | "dense";
type AppScreen = "home" | "explorer" | "dataset-test";
type ContextNotice = {
  id: number;
  kind: "run" | "selection";
  message: string;
  visible: boolean;
};

function formatScore(value: number, metric = "tokenRisk") {
  return formatMetricNumber(value, metric, "compact");
}

function formatSignedScore(value: number) {
  return formatMetricDelta(value, "attribution", "compact");
}

function useExplorerRun() {
  return useContext(ExplorerRunContext);
}

function initialWorkspaceLayout(): WorkspaceLayout {
  const queryLayout = new URLSearchParams(window.location.search).get("layout");
  if (queryLayout === "focus" || queryLayout === "dense") return queryLayout;
  const stored = window.sessionStorage.getItem("safelens-workspace-layout") ??
    window.localStorage.getItem("safelens-workspace-layout");
  return stored === "dense" ? "dense" : "focus";
}

function screenFromLocation(): AppScreen {
  const path = window.location.pathname.replace(/\/+$/, "");
  if (path === "/dataset-test") return "dataset-test";
  if (path === "/explorer") return "explorer";
  const params = new URLSearchParams(window.location.search);
  const explorerKeys = [
    "view", "mode", "run", "sample", "token", "layer", "head", "neuron", "track", "metric"
  ];
  return explorerKeys.some((key) => params.has(key)) ? "explorer" : "home";
}

function App() {
  const [screen, setScreen] = useState<AppScreen>(screenFromLocation);
  const library = useRunLibrary(realRun, screen === "explorer");
  const run = library.activeRecord.run;
  const [pendingSession, setPendingSession] = useState<ExplorerSession | null>(null);
  const [contextNotice, setContextNotice] = useState<ContextNotice | null>(null);
  const noticeSequenceRef = React.useRef(0);
  const pendingNoticeTimerRef = React.useRef<number | null>(null);
  const dismissNoticeTimerRef = React.useRef<number | null>(null);
  const previousRunKeyRef = React.useRef(library.activeRecord.key);

  const announceContextChange = React.useCallback((
    message: string,
    kind: ContextNotice["kind"] = "selection"
  ) => {
    if (pendingNoticeTimerRef.current !== null) {
      window.clearTimeout(pendingNoticeTimerRef.current);
    }
    if (dismissNoticeTimerRef.current !== null) {
      window.clearTimeout(dismissNoticeTimerRef.current);
    }
    pendingNoticeTimerRef.current = window.setTimeout(() => {
      const id = ++noticeSequenceRef.current;
      setContextNotice({ id, kind, message, visible: true });
      dismissNoticeTimerRef.current = window.setTimeout(() => {
        setContextNotice((current) =>
          current?.id === id ? { ...current, visible: false } : current
        );
      }, 1900);
      pendingNoticeTimerRef.current = null;
    }, kind === "run" ? 0 : 60);
  }, []);

  useEffect(() => {
    if (previousRunKeyRef.current === library.activeRecord.key) return;
    previousRunKeyRef.current = library.activeRecord.key;
    announceContextChange(
      runChangeMessage(
        library.activeRecord.run,
        pendingSession,
        consumeRunContextTransition(library.activeRecord.key)
      ),
      "run"
    );
  }, [announceContextChange, library.activeRecord.key, library.activeRecord.run, pendingSession]);

  useEffect(() => () => {
    if (pendingNoticeTimerRef.current !== null) {
      window.clearTimeout(pendingNoticeTimerRef.current);
    }
    if (dismissNoticeTimerRef.current !== null) {
      window.clearTimeout(dismissNoticeTimerRef.current);
    }
  }, []);

  useEffect(() => {
    function restoreScreen() {
      setScreen(screenFromLocation());
    }
    window.addEventListener("popstate", restoreScreen);
    return () => window.removeEventListener("popstate", restoreScreen);
  }, []);

  function openExplorer(key: string, view: WorkspaceView = "overview", setup?: "prompt") {
    const record = library.records.find((item) => item.key === key) ?? library.activeRecord;
    const params = new URLSearchParams();
    params.set("run", record.runId);
    params.set("sample", record.sampleId);
    params.set("layout", "focus");
    params.set("view", view);
    if (setup) params.set("setup", setup);
    window.history.pushState(null, "", `/explorer?${params.toString()}`);
    library.selectRun(record.key, undefined, "none");
    setScreen("explorer");
  }

  function openHome() {
    window.history.pushState(null, "", "/");
    setScreen("home");
  }

  function openDatasetTest() {
    window.history.pushState(null, "", "/dataset-test");
    setScreen("dataset-test");
  }

  return (
    <ExplorerRunContext.Provider value={run}>
      {screen === "home" ? (
        <ExplorerHome
          records={library.records}
          activeRecord={library.activeRecord}
          remoteState={library.remoteState}
          onOpenDatasetTest={openDatasetTest}
          onSelectConversation={(key) => library.selectRun(key, undefined, "none")}
          onRunReady={(generatedRun, job) => library.addGeneratedRun(
            generatedRun,
            job.id,
            undefined,
            {
              kind: job.kind === "prompt-run" ? "prompt" : job.kind,
              updateLocation: false,
              conversationId: generatedRun.metadata?.conversationId as string | undefined,
              turnIndex: generatedRun.metadata?.turnIndex as number | undefined
            }
          )}
          onRemoveRuns={library.removeRuns}
        />
      ) : screen === "dataset-test" ? (
        <DatasetTestScreen onOpenChat={openHome} />
      ) : (
        <ExplorerWorkspace
          key={library.activeRecord.key}
          run={run}
          library={library}
          pendingSession={pendingSession}
          onQueueSession={setPendingSession}
          onSessionApplied={() => setPendingSession(null)}
          onContextChange={announceContextChange}
          contextNotice={contextNotice}
          onOpenHome={openHome}
        />
      )}
    </ExplorerRunContext.Provider>
  );
}

function ExplorerWorkspace({
  run,
  library,
  pendingSession,
  onQueueSession,
  onSessionApplied,
  onContextChange,
  contextNotice,
  onOpenHome
}: {
  run: ExplorerRun;
  library: ReturnType<typeof useRunLibrary>;
  pendingSession: ExplorerSession | null;
  onQueueSession: (session: ExplorerSession) => void;
  onSessionApplied: () => void;
  onContextChange: (message: string, kind?: ContextNotice["kind"]) => void;
  contextNotice: ContextNotice | null;
  onOpenHome: () => void;
}) {
  const [compareOpen, setCompareOpen] = useState(false);
  const [workspaceLayout, setWorkspaceLayout] = useState<WorkspaceLayout>(initialWorkspaceLayout);
  const [compareBaselineId, setCompareBaselineId] = useState<string | undefined>();
  const [libraryOpen, setLibraryOpen] = useState(
    () => new URLSearchParams(window.location.search).get("setup") === "prompt"
  );
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [inspectorExpanded, setInspectorExpanded] = useState(false);
  const [quickActionsOpen, setQuickActionsOpen] = useState(false);
  const [selectionActivated, setSelectionActivated] = useState(false);
  const [selectionMenuOpen, setSelectionMenuOpen] = useState(false);
  const [focusSupplementOpen, setFocusSupplementOpen] = useState(false);
  const [focusExperimentOpen, setFocusExperimentOpen] = useState(false);
  const libraryTriggerButton = React.useRef<HTMLButtonElement>(null);
  const libraryReturnTarget = React.useRef<HTMLElement | null>(null);
  const inspectorReturnTarget = React.useRef<HTMLElement | null>(null);
  const inspectorRestoreFocus = React.useRef(true);
  const compareTriggerButton = React.useRef<HTMLButtonElement>(null);
  const quickActionsTriggerButton = React.useRef<HTMLButtonElement>(null);
  const compareReturnTarget = React.useRef<HTMLElement | null>(null);
  const libraryCloseButton = React.useRef<HTMLButtonElement>(null);
  const inspectorCloseButton = React.useRef<HTMLButtonElement>(null);
  const libraryDialog = React.useRef<HTMLElement>(null);
  const inspectorDialog = React.useRef<HTMLElement>(null);
  const inspectorGesture = React.useRef<{
    pointerId: number;
    startY: number;
  } | null>(null);
  const analysisWorkspaceRef = React.useRef<HTMLElement>(null);
  const rolloutLoadRef = React.useRef<string | null>(null);
  const evidenceTokens = topEvidenceTokens(run.tokens);
  const defaultLayer = run.layers[run.layers.length - 1] ?? 0;
  const initialSourceArtifact =
    `${library.activeRecord.sourceName} · ${library.activeRecord.sourceType}` +
    `${library.activeRecord.hydration?.mode === "partial" ? " · range chunk" : ""}`;
  const selection = useExplorerSelection({
    runId: run.runId,
    sampleId: run.sampleId,
    tokenIndex: evidenceTokens[0] ?? run.tokens[0]?.index ?? 0,
    tokenIndices: run.tokens.map((token) => token.index),
    layers: run.layers,
    layer: defaultLayer,
    view: "overview",
    headId: run.attentionHeads.find((head) => head.layer === defaultLayer)?.id ?? "",
    nlaComponent: run.nla.find((row) => row.layer === defaultLayer)?.component ?? "resid_post",
    neuronId: run.mlpNeurons.find((neuron) => neuron.layer === defaultLayer)?.id ?? "",
    trackName: run.attributionMethods.find((method) => method.available)?.id ?? "",
    metric: "residual_direction",
    initialPinnedItems: buildInitialOverviewPins(
      run,
      evidenceTokens,
      defaultLayer,
      initialSourceArtifact
    )
  });
  const { state: selectionState } = selection;
  const selectedToken = selectionState.tokenIndex;
  const selectedSourceToken = selectionState.sourceTokenIndex ?? selectedToken;
  const selectedLayer = selectionState.layer;
  const selectedNlaComponent = selectionState.nlaComponent;
  const view = selectionState.view;
  const component = componentForView(view);
  const matrixMetric = resolveMatrixMetric(component, selectionState.metric);
  const selectedHeadId = selectionState.headId;
  const attentionEdgeMode = selectionState.attentionEdgeMode;
  const selectedNeuronId = selectionState.neuronId;
  const selectedTrack = selectionState.trackName;
  const pinned = selectionState.pinnedItems;
  const [hoveredToken, setHoveredToken] = useState<number | null>(null);
  const [pulseToken, setPulseToken] = useState<number | null>(null);
  const [evidenceFilter, setEvidenceFilter] = useState<EvidenceFilter>("top");
  const [timeline, setTimeline] = useState<TimelineState>({
    mode: "token",
    metric: "risk",
    query: ""
  });
  const [matrixViewports, setMatrixViewports] = useState<MatrixViewportSnapshots>({});
  const hydration = library.viewHydration(
    view,
    selectedLayer,
    selectedToken,
    selectedSourceToken
  );
  const nlaDataHydration = library.viewHydration("nla", selectedLayer, selectedToken);

  useExplorerPerformance({
    rootRef: analysisWorkspaceRef,
    view,
    ready: hydration.ready
  });

  useEffect(() => {
    if (
      !pendingSession ||
      pendingSession.workspace.runId !== run.runId ||
      pendingSession.workspace.sampleId !== run.sampleId
    ) {
      return;
    }
    selection.restoreSession(
      sanitizeSessionSelection(pendingSession, run, selectionState)
    );
    setEvidenceFilter(pendingSession.filters.evidence);
    setTimeline(sanitizeSessionTimeline(pendingSession, run));
    setMatrixViewports(sanitizeSessionMatrixViewports(pendingSession.matrices));
    setCompareBaselineId(
      pendingSession.pinnedItems.some((item) => item.id === pendingSession.compare?.baselineId)
        ? pendingSession.compare?.baselineId
        : pendingSession.pinnedItems[0]?.id
    );
    setCompareOpen(false);
    setInspectorOpen(false);
    library.setMessage({
      tone: "success",
      title: "Analysis session restored",
      details: [`${run.runId} / ${run.sampleId} · ${workspaceViewLabel(pendingSession.selection.view)}`]
    });
    onSessionApplied();
  }, [pendingSession, run.runId, run.sampleId]);

  useEffect(() => {
    library.ensureViewHydrated(view, selectedLayer, selectedToken, selectedSourceToken);
  }, [library.activeRecord.key, view, selectedLayer, selectedToken, selectedSourceToken]);

  useEffect(() => {
    if (!pinned.some((item) => item.id === compareBaselineId)) {
      setCompareBaselineId(pinned[0]?.id);
    }
  }, [compareBaselineId, pinned]);

  const layerHeads = useMemo(
    () => run.attentionHeads.filter((head) => head.layer === selectedLayer),
    [run.attentionHeads, selectedLayer]
  );
  const layerNeurons = useMemo(
    () => run.mlpNeurons.filter((neuron) => neuron.layer === selectedLayer),
    [run.mlpNeurons, selectedLayer]
  );
  const rolloutRequested = Boolean(parseAttentionRollout(selectedHeadId));
  const rolloutPending = rolloutRequested && hydration.partial;
  const selectedHead = useMemo(
    () => rolloutPending
      ? layerHeads[0] ?? run.attentionHeads[0]
      : resolveAttentionHead(
          layerHeads,
          selectedHeadId,
          run.attentionHeads,
          selectedLayer,
          run.layers
        ) ?? layerHeads[0] ?? run.attentionHeads[0],
    [layerHeads, rolloutPending, run.attentionHeads, run.layers, selectedHeadId, selectedLayer]
  );
  const selectedAttributionMethod =
    run.attributionMethods.find((method) => method.id === selectedTrack) ??
    run.attributionMethods.find((method) => method.available) ??
    run.attributionMethods[0];
  const selectedAttributionRow =
    selectedAttributionMethod.rows.find((row) => row.layer === selectedLayer) ??
    selectedAttributionMethod.rows[0];
  const selectedTrackData = {
    name: selectedAttributionMethod.label,
    values: selectedAttributionRow?.values ?? run.tokens.map(() => 0)
  };
  const selectedTokenInfo = run.tokens[selectedToken];
  const residualCell = run.residualCells.find(
    (cell) => cell.layer === selectedLayer && cell.tokenIndex === selectedToken
  );
  const nlaRow = matchingNla(run.nla, selectedToken, selectedLayer, selectedNlaComponent);
  const topNeuron =
    layerNeurons.find((neuron) => neuron.id === selectedNeuronId) ??
    [...layerNeurons].sort(
      (left, right) =>
        Math.abs(right.activationsByToken[selectedToken] ?? 0) -
        Math.abs(left.activationsByToken[selectedToken] ?? 0)
    )[0];

  const aggregateRisk = useMemo(
    () => run.tokens.reduce((max, token) => Math.max(max, token.risk), 0),
    [run.tokens]
  );
  const meanAttribution = useMemo(
    () =>
      run.tokens.reduce((total, token) => total + token.attribution, 0) /
      Math.max(1, run.tokens.length),
    [run.tokens]
  );
  const nlaMetric =
    !nlaDataHydration.ready || !nlaRow || nlaRow.status === "unavailable"
      ? "n/a"
      : formatScore(nlaRow.cosine, "nla_cosine");
  const selectedTokenPosition = run.tokens.findIndex((token) => token.index === selectedToken);
  const inspectorEvidence = hydration.ready
    ? buildInspectorEvidence({
        run,
        view,
        selectedToken,
        selectedSourceToken,
        selectedLayer,
        selectedNlaComponent,
        selectedHead,
        selectedNeuron: topNeuron,
        selectedAttributionMethod,
        metric: selectionState.metric,
        normalization: selectionState.normalization,
        sourceArtifact: `${library.activeRecord.sourceName} · ${library.activeRecord.sourceType}${hydration.partial ? " · range chunk" : ""}`
      })
    : loadingInspectorEvidence(
        run,
        view,
        selectedLayer,
        selectedToken,
      hydration.error,
      hydration.cancelled
    );
  const inspectorNextActions = buildInspectorNextActions(view, inspectorEvidence);
  const pinnedTokenIndices = pinned
    .filter((item) => item.runId === run.runId && item.sampleId === run.sampleId)
    .map((item) => item.tokenIndex);
  const currentPinnedId = buildPinnedEvidence(selectedToken).id;
  const isCurrentPinned = pinned.some((item) => item.id === currentPinnedId);
  const canPinCurrent =
    hydration.ready &&
    !rolloutPending &&
    inspectorEvidence.status === "available" &&
    (view !== "attribution" || selectedAttributionMethod.available) &&
    (view !== "nla" || nlaRow?.status === "available") &&
    (view !== "intervention" || Boolean(run.intervention));
  const showSupplementalEvidence = workspaceLayout === "dense" || focusSupplementOpen;
  const contextSummary = selectionContextSummary({
    view,
    tokenText: selectedTokenInfo.text,
    tokenIndex: selectedToken,
    sourceTokenIndex: selectedSourceToken,
    tokenRange: selectionState.tokenRange,
    layer: selectedLayer,
    metric: selectionState.metric,
    normalization: selectionState.normalization,
    headId: selectedHead.id,
    neuronId: topNeuron?.id,
    nlaComponent: selectedNlaComponent,
    attributionMethod: selectedAttributionMethod.label,
    attentionEdgeMode
  });
  const previousContextSignatureRef = React.useRef(contextSummary.signature);

  useEffect(() => {
    if (previousContextSignatureRef.current === contextSummary.signature) return;
    previousContextSignatureRef.current = contextSummary.signature;
    onContextChange(contextSummary.message);
  }, [contextSummary.message, contextSummary.signature, onContextChange]);

  useEffect(() => {
    if (!inspectorOpen) setInspectorExpanded(false);
  }, [inspectorOpen]);

  useEffect(() => {
    if (!inspectorOpen) return;
    inspectorDialog.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [inspectorExpanded, inspectorOpen]);

  useEffect(() => {
    function updateInspectorGesture(event: PointerEvent) {
      const gesture = inspectorGesture.current;
      if (!gesture || gesture.pointerId !== event.pointerId) return;
      const delta = gesture.startY - event.clientY;
      if (delta >= 48) {
        inspectorGesture.current = null;
        setInspectorExpanded(true);
      } else if (delta <= -48) {
        inspectorGesture.current = null;
        setInspectorExpanded(false);
      }
    }
    function finishInspectorGesture(event: PointerEvent) {
      const gesture = inspectorGesture.current;
      if (!gesture || gesture.pointerId !== event.pointerId) return;
      inspectorGesture.current = null;
      const delta = gesture.startY - event.clientY;
      if (delta >= 48) setInspectorExpanded(true);
      if (delta <= -48) setInspectorExpanded(false);
    }
    function cancelInspectorGesture(event: PointerEvent) {
      if (inspectorGesture.current?.pointerId === event.pointerId) {
        inspectorGesture.current = null;
      }
    }
    window.addEventListener("pointermove", updateInspectorGesture);
    window.addEventListener("pointerup", finishInspectorGesture);
    window.addEventListener("pointercancel", cancelInspectorGesture);
    return () => {
      window.removeEventListener("pointermove", updateInspectorGesture);
      window.removeEventListener("pointerup", finishInspectorGesture);
      window.removeEventListener("pointercancel", cancelInspectorGesture);
    };
  }, []);

  useModalDialog({
    open: libraryOpen,
    dialogRef: libraryDialog,
    initialFocusRef: libraryCloseButton,
    returnFocusRef: libraryReturnTarget,
    onClose: () => setLibraryOpen(false)
  });
  useModalDialog({
    open: inspectorOpen,
    dialogRef: inspectorDialog,
    initialFocusRef: inspectorCloseButton,
    returnFocusRef: inspectorReturnTarget,
    restoreFocusRef: inspectorRestoreFocus,
    onClose: () => setInspectorOpen(false)
  });

  useEffect(() => {
    if (!rolloutPending && (!hydration.partial || (view === "attention" && hydration.ready)) && selectedHead.id !== selectedHeadId) {
      selection.selectHead(selectedHead.id, "replace");
    }
  }, [hydration.partial, hydration.ready, rolloutPending, selectedHead.id, selectedHeadId, view]);

  useEffect(() => {
    if (view !== "attention" || !rolloutPending) return;
    const loadKey = `${library.activeRecord.key}:${selectedLayer}`;
    if (rolloutLoadRef.current === loadKey) return;
    void loadAttentionRollout(loadKey);
  }, [library.activeRecord.key, rolloutPending, selectedLayer, view]);

  useEffect(() => {
    if ((!hydration.partial || (view === "mlp" && hydration.ready)) && topNeuron && topNeuron.id !== selectedNeuronId) {
      selection.selectNeuron(topNeuron.id, "replace");
    }
  }, [hydration.partial, hydration.ready, selectedNeuronId, topNeuron?.id, view]);

  useEffect(() => {
    if ((!hydration.partial || (view === "attribution" && hydration.ready)) && selectedAttributionMethod.id !== selectedTrack) {
      selection.selectTrack(selectedAttributionMethod.id, "replace");
    }
  }, [hydration.partial, hydration.ready, selectedAttributionMethod.id, selectedTrack, view]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented || compareOpen || libraryOpen || inspectorOpen || quickActionsOpen) return;
      const target = event.target as HTMLElement | null;
      const editable = target?.closest("input, textarea, select, [contenteditable='true']") ||
        target?.isContentEditable;
      if (
        event.altKey && event.shiftKey && !event.ctrlKey && !event.metaKey &&
        event.key.toLowerCase() === "c"
      ) {
        if (editable || pinned.length === 0) return;
        event.preventDefault();
        compareReturnTarget.current = compareTriggerButton.current;
        preloadCompareDrawer();
        setCompareOpen(true);
        return;
      }
      if (
        target?.closest("input, textarea, select, button, a, [role='button'], [role='tab'], [role='radio'], [role='grid']") ||
        editable
      ) {
        return;
      }
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
        return;
      }
      const direction = event.key === "ArrowLeft" ? -1 : 1;
      const nextPosition = Math.max(
        0,
        Math.min(run.tokens.length - 1, selectedTokenPosition + direction)
      );
      if (nextPosition === selectedTokenPosition) {
        return;
      }
      event.preventDefault();
      const tokenIndex = run.tokens[nextPosition].index;
      selection.selectToken(tokenIndex);
      pulseSelectionToken(tokenIndex, setPulseToken);
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [compareOpen, inspectorOpen, libraryOpen, pinned.length, quickActionsOpen, run.tokens, selectedTokenPosition]);

  function selectEvidenceToken(tokenIndex: number) {
    focusToken(tokenIndex);
  }

  function focusToken(tokenIndex: number) {
    selection.selectToken(tokenIndex);
    if (workspaceLayout === "focus") {
      setSelectionActivated(true);
      setSelectionMenuOpen(false);
    }
    recordExplorerPerformance("selection-commit", { view, token: tokenIndex });
    pulseSelectionToken(tokenIndex, setPulseToken);
  }

  function runInspectorNextAction(actionId: string) {
    const target = inspectorActionTarget(actionId);
    if (!target) return;
    inspectorRestoreFocus.current = false;
    setInspectorOpen(false);
    selection.selectView(target.view);
    if (!target.anchorId) {
      window.requestAnimationFrame(() => {
        analysisWorkspaceRef.current?.scrollIntoView({ block: "start" });
      });
      return;
    }
    void openJobSetup(target.anchorId);
  }

  async function openJobSetup(anchorId: string) {
    setInspectorOpen(false);
    setFocusExperimentOpen(true);
    if (hydration.partial) {
      try {
        await library.loadFullActiveRun();
      } catch (error) {
        library.setMessage({
          tone: "error",
          title: "Experiment setup could not be opened",
          details: [error instanceof Error ? error.message : "The complete Run could not be loaded."]
        });
        return;
      }
    }
    window.requestAnimationFrame(() => focusElementWhenAvailable(anchorId));
  }

  async function pinToken(
    tokenIndex: number,
    layer = selectedLayer,
    overrides: PinCellOverrides = {}
  ) {
    if (!canPinCurrent) {
      return;
    }
    const pinSourceToken = overrides.sourceTokenIndex ?? selectedSourceToken;
    const pinNeuron = overrides.neuronId
      ? run.mlpNeurons.find((candidate) => candidate.id === overrides.neuronId)
      : topNeuron;
    let evidence = buildPinnedEvidence(tokenIndex, layer, overrides);
    if (pinned.some((item) => item.id === evidence.id)) {
      selection.togglePin(evidence);
      return;
    }
    if (view === "attention" && hydration.partial) {
      try {
        const completeRun = await library.loadFullActiveRun();
        const completeLayerHeads = completeRun.attentionHeads.filter((head) => head.layer === layer);
        const completeHead = resolveAttentionHead(
          completeLayerHeads,
          selectedHead.id,
          completeRun.attentionHeads,
          layer,
          completeRun.layers
        );
        if (!completeHead) throw new Error(`Attention head ${selectedHead.id} is missing from the complete artifact.`);
        const completeTokens = completeRun.tokens.filter((candidate) => candidate.index <= tokenIndex);
        const profile = buildEvidenceProfile({
          kind: "attention_source_profile",
          label: `${attentionHeadLabel(completeHead)} · destination token ${tokenIndex}`,
          axis: "source_token",
          signed: Boolean(completeHead.difference),
          tokens: completeTokens,
          values: completeHead.distributionByToken[tokenIndex] ?? [],
          preserveTokenIndex: pinSourceToken
        });
        const matrix = completeHead.difference
          ? undefined
          : buildAttentionMatrixSnapshot(
              completeHead,
              completeRun.tokens,
              pinSourceToken,
              tokenIndex
            );
        if (!profile || (!completeHead.difference && !matrix)) {
          throw new Error("The complete artifact does not contain a valid attention matrix.");
        }
        evidence = {
          ...evidence,
          profile,
          ...(matrix ? { matrix } : {}),
          assessment: inspectorEvidenceAssessment(buildInspectorEvidence({
            run: completeRun,
            view,
            selectedToken: tokenIndex,
            selectedSourceToken: pinSourceToken,
            selectedLayer: layer,
            selectedNlaComponent,
            selectedHead: completeHead,
            selectedNeuron: topNeuron,
            selectedAttributionMethod,
            metric: evidence.metric,
            normalization: evidence.normalization,
            sourceArtifact: `${library.activeRecord.sourceName} · ${library.activeRecord.sourceType} · full artifact`
          }))
        };
      } catch (error) {
        library.setMessage({
          tone: "error",
          title: "Attention matrix pin failed",
          details: [error instanceof Error ? error.message : "The complete attention artifact could not be loaded."]
        });
        return;
      }
    }
    if (view === "mlp" && hydration.partial) {
      try {
        const completeRun = await library.loadFullActiveRun();
        const completeNeuron = completeRun.mlpNeurons.find((candidate) => candidate.id === pinNeuron?.id);
        if (!completeNeuron) throw new Error(`MLP neuron ${pinNeuron?.id ?? "unknown"} is missing from the complete artifact.`);
        const completeMetric = resolveMlpMetric(selectionState.metric);
        const values = completeNeuron.activationsByToken.map((value) =>
          mlpMetricValue(value, completeNeuron.maxAbsoluteActivation, completeMetric)
        );
        const profile = buildEvidenceProfile({
          kind: "mlp_activation_profile",
          label: `${completeNeuron.id} · ${mlpMetricLabel(completeMetric)}`,
          axis: "token",
          signed: completeMetric === "mlp_signed_activation",
          tokens: completeRun.tokens,
          values,
          preserveTokenIndex: tokenIndex
        });
        if (!profile) throw new Error("The complete artifact does not contain a valid MLP activation profile.");
        evidence = {
          ...evidence,
          profile,
          assessment: inspectorEvidenceAssessment(buildInspectorEvidence({
            run: completeRun,
            view,
            selectedToken: tokenIndex,
            selectedSourceToken: pinSourceToken,
            selectedLayer: layer,
            selectedNlaComponent,
            selectedHead,
            selectedNeuron: completeNeuron,
            selectedAttributionMethod,
            metric: evidence.metric,
            normalization: evidence.normalization,
            sourceArtifact: `${library.activeRecord.sourceName} · ${library.activeRecord.sourceType} · full artifact`
          }))
        };
      } catch (error) {
        library.setMessage({
          tone: "error",
          title: "MLP profile pin failed",
          details: [error instanceof Error ? error.message : "The complete MLP artifact could not be loaded."]
        });
        return;
      }
    }
    selection.togglePin(evidence);
  }

  async function loadAttentionRollout(
    loadKey = `${library.activeRecord.key}:${selectedLayer}`
  ) {
    rolloutLoadRef.current = loadKey;
    try {
      await library.loadFullActiveRun();
      if (rolloutLoadRef.current === loadKey) rolloutLoadRef.current = null;
    } catch (error) {
      if (rolloutLoadRef.current !== loadKey) return;
      rolloutLoadRef.current = null;
      const fallbackHead = layerHeads[0]?.id;
      if (fallbackHead) selection.selectHead(fallbackHead, "replace");
      library.setMessage({
        tone: "error",
        title: "Attention rollout loading failed",
        details: [error instanceof Error ? error.message : "The complete attention artifact could not be loaded."]
      });
    }
  }

  function cancelAttentionRollout() {
    rolloutLoadRef.current = null;
    library.cancelRemote();
    const fallbackHead = layerHeads[0]?.id;
    if (fallbackHead) selection.selectHead(fallbackHead, "replace");
  }

  function restoreEvidence(evidence: PinnedEvidence) {
    if (evidence.runId === run.runId && evidence.sampleId === run.sampleId) {
      selection.restorePin(evidence);
      return;
    }
    library.selectRun(runKey(evidence), evidence);
  }

  function buildPinnedEvidence(
    tokenIndex: number,
    layer = selectedLayer,
    overrides: PinCellOverrides = {}
  ): PinnedEvidence {
    const token = run.tokens.find((item) => item.index === tokenIndex) ?? run.tokens[0];
    const pinSourceToken = overrides.sourceTokenIndex ?? selectedSourceToken;
    const pinNeuron = overrides.neuronId
      ? run.mlpNeurons.find((candidate) => candidate.id === overrides.neuronId)
      : topNeuron;
    const pinNlaComponent = overrides.nlaComponent ?? selectedNlaComponent;
    const pinAttributionRow = selectedAttributionMethod.rows.find((row) => row.layer === layer)
      ?? selectedAttributionRow;
    const componentCell = matrixCellsForComponent(run, component, matrixMetric).find(
      (cell) => cell.row === layer && cell.column === tokenIndex
    );
    const patchingCell = run.patching?.cells.find(
      (cell) => cell.layer === layer && cell.tokenIndex === tokenIndex
    );
    const intervention = run.intervention;
    const exactNla = matchingNla(run.nla, tokenIndex, layer, pinNlaComponent);
    const metric =
      view === "overview"
        ? "tokenRisk"
        : view === "attention"
          ? attentionHeadMetric(selectedHead)
        : view === "mlp"
          ? resolveMlpMetric(selectionState.metric)
        : view === "attribution"
          ? selectedTrack
        : view === "nla"
            ? selectionState.metric
          : view === "patching"
            ? selectionState.metric
          : view === "intervention"
            ? "intervention_logit_delta"
            : matrixMetric;
    const pinNormalization: NormalizationMode =
      view === "attention" || view === "intervention" ||
      (view === "mlp" && metric !== "mlp_normalized_activation")
        ? "raw"
        : selectionState.normalization;
    const value =
      view === "overview"
        ? token.risk
        : view === "attention"
          ? selectedHead.distributionByToken[tokenIndex]?.[pinSourceToken] ?? 0
        : view === "mlp"
          ? mlpMetricValue(
              pinNeuron?.activationsByToken[tokenIndex] ?? 0,
              pinNeuron?.maxAbsoluteActivation ?? 1,
              metric
            )
        : view === "attribution"
          ? pinAttributionRow?.values[tokenIndex] ?? 0
        : view === "nla"
            ? resolveNlaMetric(metric) === "mse"
              ? exactNla?.mse ?? 0
              : resolveNlaMetric(metric) === "fve"
                ? exactNla?.fve ?? 0
                : exactNla?.cosine ?? 0
          : view === "patching"
            ? patchingMetricValue(patchingCell, selectionState.metric) ?? 0
          : view === "intervention"
            ? intervention?.deltas.targetLogit ?? 0
            : selectionState.normalization === "raw"
              ? componentCell?.rawValue ?? 0
              : componentCell?.value ?? 0;
    const headId = view === "attention" ? selectedHead.id : undefined;
    const neuronId = view === "mlp" ? pinNeuron?.id : undefined;
    const trackName = view === "attribution" ? selectedTrack : undefined;
    const provenance: MetricProvenance = view === "attribution"
      ? {
          label: selectedAttributionMethod.label,
          method: selectedAttributionMethod.id,
          semantics: selectedAttributionMethod.description,
          normalization: selectedAttributionMethod.normalization,
          kind: selectedAttributionMethod.evidenceKind
        }
      : view === "nla"
        ? {
            label: "NLA fidelity",
            method: "exact NLA decoder reconstruction",
            semantics: "Exact token/layer/component reconstruction fidelity for a compatible profile.",
            normalization: "stored method metric",
            kind: "safety_method"
          }
        : view === "patching"
          ? patchingProvenance(run, selectionState.metric)
        : view === "intervention"
          ? interventionProvenance(run)
        : view === "attention"
          ? attentionHeadProvenance(selectedHead, run.metricProvenance.attentionHeatmap)
          : evidenceProvenance(run, view, metric);
    const sourceKey = view === "attention"
      ? attentionHeadSourceKey(selectedHead)
      : view === "mlp"
        ? `layer_${pinNeuron?.layer ?? layer}.post[:, ${pinNeuron?.neuron ?? 0}]`
        : view === "attribution"
          ? pinAttributionRow?.sourceKey
          : view === "nla"
            ? exactNla?.source
          : view === "patching"
            ? patchingCell?.sourceKey
          : view === "intervention"
            ? intervention?.vector.sourceKey
            : componentCell?.sourceKey ?? `layer_${layer}.resid_post[${tokenIndex}]`;
    const profile = view === "attention" && !hydration.partial
      ? buildEvidenceProfile({
          kind: "attention_source_profile",
          label: `${attentionHeadLabel(selectedHead)} · destination token ${tokenIndex}`,
          axis: "source_token",
          signed: Boolean(selectedHead.difference),
          tokens: run.tokens.filter((candidate) => candidate.index <= tokenIndex),
          values: selectedHead.distributionByToken[tokenIndex] ?? [],
          preserveTokenIndex: pinSourceToken
        })
      : view === "attribution" && selectedAttributionMethod.signed
        ? buildEvidenceProfile({
            kind: "signed_attribution_profile",
            label: `${selectedAttributionMethod.label} · L${layer}`,
            axis: "token",
            signed: true,
            tokens: run.tokens,
            values: pinAttributionRow?.values ?? [],
            preserveTokenIndex: tokenIndex
          })
        : view === "mlp" && pinNeuron && !hydration.partial
          ? buildEvidenceProfile({
              kind: "mlp_activation_profile",
              label: `${pinNeuron.id} · ${mlpMetricLabel(metric)}`,
              axis: "token",
              signed: metric === "mlp_signed_activation",
              tokens: run.tokens,
              values: pinNeuron.activationsByToken.map((activation) =>
                mlpMetricValue(activation, pinNeuron.maxAbsoluteActivation, metric)
              ),
              preserveTokenIndex: tokenIndex
            })
        : undefined;
    const matrix: AttentionMatrixSnapshot | undefined = view === "attention" && !hydration.partial && !selectedHead.difference
      ? buildAttentionMatrixSnapshot(
          selectedHead,
          run.tokens,
          pinSourceToken,
          tokenIndex
        )
      : undefined;
    const generation: InterventionGenerationSnapshot | undefined =
      view === "intervention" && intervention
        ? {
            schemaVersion: "1.0",
            sourceRun: intervention.sourceRun,
            layer: intervention.layer,
            component: intervention.component,
            scale: intervention.scale,
            positionStart: intervention.positionStart,
            positionEnd: intervention.positionEnd,
            targetTokenId: intervention.targetTokenId,
            targetTokenText: intervention.targetTokenText,
            seed: intervention.seed,
            maxNewTokens: intervention.maxNewTokens,
            temperature: intervention.temperature,
            original: {
              text: intervention.original.text,
              tokens: intervention.original.tokens,
              targetLogit: intervention.original.targetLogit,
              lexicalRisk: intervention.original.lexicalRisk
            },
            steered: {
              text: intervention.steered.text,
              tokens: intervention.steered.tokens,
              targetLogit: intervention.steered.targetLogit,
              lexicalRisk: intervention.steered.lexicalRisk
            },
            tokenEditDistance: intervention.deltas.tokenEditDistance,
            generationChanged: intervention.deltas.generationChanged,
            diff: intervention.diff
          }
        : undefined;
    const assessment = inspectorEvidenceAssessment(buildInspectorEvidence({
      run,
      view,
      selectedToken: tokenIndex,
      selectedSourceToken: pinSourceToken,
      selectedLayer: layer,
      selectedNlaComponent: pinNlaComponent,
      selectedHead,
      selectedNeuron: pinNeuron,
      selectedAttributionMethod,
      metric,
      normalization: pinNormalization,
      sourceArtifact: `${library.activeRecord.sourceName} · ${library.activeRecord.sourceType}${hydration.partial ? " · range chunk" : ""}`
    }));
    return {
      id: [
        run.runId,
        run.sampleId,
        tokenIndex,
        layer,
        view,
        metric,
        pinNormalization,
        headId ?? "-",
        neuronId ?? "-",
        view === "attention"
          ? pinSourceToken
          : view === "nla"
            ? pinNlaComponent
            : "-"
      ].join(":"),
      runId: run.runId,
      sampleId: run.sampleId,
      tokenIndex,
      tokenText: token.text,
      tokenId: token.tokenId,
      tokenSource: token.source,
      modelName: run.modelName,
      modelSource: run.modelSource,
      layer,
      view,
      component: view === "nla" ? exactNla?.component ?? pinNlaComponent : component,
      metric,
      value,
      normalization: pinNormalization,
      headId,
      neuronId,
      trackName,
      sourceTokenIndex: view === "attention" ? pinSourceToken : undefined,
      sourceKey,
      provenance,
      profile,
      matrix,
      generation,
      assessment,
      capturedAt: new Date().toISOString()
    };
  }

  function exportCurrentView() {
    const payload = {
      exportedAt: new Date().toISOString(),
      runId: run.runId,
      sampleId: run.sampleId,
      model: { name: run.modelName, source: run.modelSource },
      selection: {
        view,
        normalization: selectionState.normalization,
        tokenRange: selectionState.tokenRange,
        token: selectedTokenInfo,
        layer: selectedLayer,
        component,
        nlaComponent: view === "nla" ? selectedNlaComponent : undefined,
        attentionHead: component === "attention"
          ? hydration.partial
            ? {
                id: selectedHead.id,
                layer: selectedHead.layer,
                head: selectedHead.head,
                role: selectedHead.role,
                entropy: selectedHead.entropy,
                riskContribution: selectedHead.riskContribution,
                aggregation: selectedHead.aggregation,
                difference: selectedHead.difference,
                rollout: selectedHead.rollout,
                memberHeadIds: selectedHead.memberHeadIds,
                partial: true
              }
            : selectedHead
          : undefined,
        attentionPair:
          view === "attention"
            ? {
                sourceToken: run.tokens[selectedSourceToken],
                destinationToken: selectedTokenInfo,
                probability: selectedHead.difference
                  ? undefined
                  : selectedHead.distributionByToken[selectedToken]?.[selectedSourceToken] ?? 0,
                probabilityDelta: selectedHead.difference
                  ? selectedHead.distributionByToken[selectedToken]?.[selectedSourceToken] ?? 0
                  : undefined,
                aggregation: selectedHead.aggregation,
                difference: selectedHead.difference,
                rollout: selectedHead.rollout,
                memberHeadIds: selectedHead.memberHeadIds
              }
            : undefined,
        mlpNeuron: component === "mlp" && topNeuron
          ? hydration.partial
            ? {
                id: topNeuron.id,
                layer: topNeuron.layer,
                neuron: topNeuron.neuron,
                label: topNeuron.label,
                selectedActivation: topNeuron.activationsByToken[selectedToken],
                maxAbsoluteActivation: topNeuron.maxAbsoluteActivation,
                partial: true
              }
            : topNeuron
          : undefined,
        nla: nlaRow,
        residual: residualCell,
        attributionTrack: hydration.partial
          ? {
              name: selectedTrackData.name,
              tokenIndex: selectedToken,
              value: selectedTrackData.values[selectedToken],
              partial: true
            }
          : selectedTrackData,
        patching: run.patching,
        intervention: run.intervention,
        pinnedEvidence: pinned
      },
      metricProvenance: run.metricProvenance,
      activeMetricProvenance: view === "attention"
        ? attentionHeadProvenance(selectedHead, run.metricProvenance.attentionHeatmap)
        : evidenceProvenance(run, view, selectionState.metric),
      evidenceAssessment: inspectorEvidenceAssessment(inspectorEvidence),
      dataAccess: hydration.partial
        ? {
            protocol: "safelens-chunks-v1",
            scope: `${workspaceViewLabel(view)} · L${selectedLayer} · token ${selectedToken}`,
            completeArtifact: false
          }
        : { completeArtifact: true }
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${run.runId}-token-${selectedToken}-layer-${selectedLayer}.json`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  async function exportRunArtifact() {
    let exportRun: ExplorerRun;
    try {
      exportRun = await library.loadFullActiveRun();
    } catch (error) {
      library.setMessage({
        tone: "error",
        title: "Complete artifact export failed",
        details: [error instanceof Error ? error.message : "The full Run could not be loaded."]
      });
      return;
    }
    const payload = {
      schema_version: "1.0",
      run: {
        run_id: exportRun.runId,
        model_name: exportRun.modelName,
        model_source: exportRun.modelSource
      },
      samples: [exportRun],
      metrics: Object.keys(exportRun.metricProvenance),
      artifacts: { embedded: true }
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${exportRun.runId}-${exportRun.sampleId}-explorer-artifact.json`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function exportAnalysisSession() {
    const { pinnedItems, ...sessionSelection } = selectionState;
    const payload: ExplorerSession = {
      kind: EXPLORER_SESSION_KIND,
      schemaVersion: "1.0",
      exportedAt: new Date().toISOString(),
      workspace: {
        runId: run.runId,
        sampleId: run.sampleId,
        modelName: run.modelName,
        modelSource: run.modelSource,
        sourceName: library.activeRecord.sourceName,
        artifactId: library.activeRecord.artifactId
      },
      selection: sessionSelection,
      pinnedItems,
      timeline,
      compare: { baselineId: compareBaselineId },
      activeEvidenceAssessment: inspectorEvidenceAssessment(inspectorEvidence),
      matrices: matrixViewports,
      filters: { evidence: evidenceFilter }
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${run.runId}-${run.sampleId}-analysis-session.json`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function restoreAnalysisSession(session: ExplorerSession) {
    const key = runKey(session.workspace);
    if (!library.records.some((record) => record.key === key)) {
      library.setMessage({
        tone: "error",
        title: "Analysis session Run is not available",
        details: [`Load ${session.workspace.runId} / ${session.workspace.sampleId} before restoring this session.`]
      });
      return;
    }
    onQueueSession(session);
    setLibraryOpen(false);
    if (key !== library.activeRecord.key) library.selectRun(key);
  }

  return (
    <MatrixViewportSessionProvider
      snapshots={matrixViewports}
      onChange={(key, snapshot) => setMatrixViewports((current) => ({
        ...current,
        [key]: snapshot
      }))}
    >
    <div className={`app-shell layout-${workspaceLayout}`}>
      <a className="skip-link" href="#analysis-workspace">Skip to analysis workspace</a>
      <header className="topbar">
        <button className="brand-block" type="button" aria-label="Return to SafeLens home" onClick={onOpenHome}>
          <div className="brand-mark">
            <BrainCircuit size={22} />
          </div>
          <div>
            <h1>SafeLens Local Explorer</h1>
            <p>{run.runId}</p>
          </div>
        </button>
        <div className="run-status" title="Select an available local run and sample">
          <Database size={15} />
          <div className="run-status-selection">
            <span className="mobile-current-run">
              <em>Run</em>
              <strong title={run.runId}>{run.runId}</strong>
            </span>
            <span className="run-sample-selection">
              <em className="mobile-run-context-label">Sample</em>
              <AdaptiveRunSelector
                records={library.records}
                ariaLabel="Quick run selector"
                value={library.activeRecord.key}
                onChange={library.selectRun}
                formatNativeLabel={(record) => record.sampleId}
              />
            </span>
          </div>
          <b className="run-layer-count">{run.layers.length} layers</b>
          <button
            ref={libraryTriggerButton}
            className="mobile-run-library-trigger"
            aria-label="Open run library"
            title="Open run library"
            onClick={(event) => {
              libraryReturnTarget.current = event.currentTarget;
              setLibraryOpen(true);
            }}
          >
            <Database size={16} />
          </button>
        </div>
        <div className="run-meta">
          <Metric label="Max safety proxy" shortLabel="Safety max" value={formatScore(aggregateRisk)} tone="danger" />
          <Metric label="Mean attention proxy" shortLabel="Attention mean" value={formatScore(meanAttribution, "attention_probability")} tone="blue" />
          <Metric label="NLA cosine" shortLabel="NLA cosine" value={nlaMetric} tone="green" />
        </div>
        <div className="topbar-actions">
          <button
            className="icon-button desktop-inspector-trigger"
            title="Inspect selected evidence"
            aria-label="Inspect selected evidence"
            onClick={(event) => {
              inspectorReturnTarget.current = event.currentTarget;
              setInspectorOpen(true);
            }}
          >
            <Info size={18} />
          </button>
          <button
            className="icon-button layout-toggle"
            title={`Switch to ${workspaceLayout === "focus" ? "dense" : "focus"} layout`}
            aria-label={`Switch to ${workspaceLayout === "focus" ? "dense" : "focus"} layout`}
            aria-pressed={workspaceLayout === "dense"}
            onClick={() => setWorkspaceLayout((current) => {
              const next = current === "focus" ? "dense" : "focus";
              window.localStorage.setItem("safelens-workspace-layout", next);
              window.sessionStorage.setItem("safelens-workspace-layout", next);
              return next;
            })}
          >
            <Layers3 size={18} />
          </button>
          <button
            ref={compareTriggerButton}
            className="icon-button compare-trigger"
            title="Compare pinned evidence"
            aria-label={`Compare pinned evidence (${pinned.length})`}
            aria-keyshortcuts="Alt+Shift+C"
            onPointerEnter={preloadCompareDrawer}
            onFocus={preloadCompareDrawer}
            onClick={(event) => {
              compareReturnTarget.current = event.currentTarget;
              setCompareOpen(true);
            }}
          >
            <GitCompareArrows size={18} />
            <span>{pinned.length}</span>
          </button>
          <button
            className="icon-button session-export"
            title="Export analysis session"
            aria-label="Export analysis session"
            onClick={exportAnalysisSession}
          >
            <Save size={18} />
          </button>
          <button
            className="icon-button artifact-export"
            title="Export current Explorer artifact"
            aria-label="Export current Explorer artifact"
            onClick={() => void exportRunArtifact()}
          >
            <PackageOpen size={18} />
          </button>
          <button
            className="icon-button current-evidence-export"
            title="Export current evidence as JSON"
            aria-label="Export current evidence as JSON"
            onClick={exportCurrentView}
          >
            <Download size={18} />
          </button>
          <button
            ref={quickActionsTriggerButton}
            className="icon-button"
            title="Open quick actions"
            aria-label="Open quick actions"
            onClick={() => setQuickActionsOpen(true)}
          >
            <CircleHelp size={18} />
          </button>
        </div>
      </header>
      <ContextChangeNotice notice={contextNotice} />

      <div className="workspace-context-bar">
        <nav aria-label="Workspace breadcrumb">
          <button type="button" onClick={onOpenHome}>Home</button>
          <ChevronRight size={13} aria-hidden="true" />
          <span>Interpretability Explorer</span>
          <ChevronRight size={13} aria-hidden="true" />
          <strong>{workspaceViewLabel(view)}</strong>
        </nav>
        <div className="workspace-context-meta">
          <span className="context-run-pill">
            <Database size={13} aria-hidden="true" />
            <b>{run.modelName}</b>
          </span>
          <span className="context-state-pill">
            <span aria-hidden="true" />
            {library.activeRecord.sourceType === "bundled" ? "Bundled cache" : "Local workspace"}
          </span>
        </div>
      </div>

      <main className="workspace">
        <aside className="left-panel">
          <RunLibraryPanel
            records={library.records}
            activeRecord={library.activeRecord}
            message={library.message}
            remoteState={library.remoteState}
            onMessage={library.setMessage}
            onSelect={library.selectRun}
            onAdd={library.addRuns}
            onRemove={library.removeRun}
            onRestoreSession={restoreAnalysisSession}
            onRefreshRemote={() => void library.refreshRemote()}
            onCancelRemote={library.cancelRemote}
          />

          <PromptRunnerPanel
            run={run}
            onRunReady={(generatedRun, job) => library.addGeneratedRun(generatedRun, job.id)}
          />

          <section className="panel-section provenance-panel">
            <div className="section-heading">
              <Search size={16} />
              <span>Data provenance</span>
            </div>
            <ProvenanceList />
          </section>

          <section className="panel-section">
            <div className="section-heading">
              <Crosshair size={16} />
              <span>Evidence</span>
            </div>
            <div className="evidence-list">
              {evidenceTokens.map((tokenIndex) => (
                <button key={tokenIndex} onClick={() => selectEvidenceToken(tokenIndex)}>
                  <span>{run.tokens[tokenIndex].text}</span>
                  <b>{formatScore(run.tokens[tokenIndex].risk)}</b>
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section
          id="analysis-workspace"
          ref={analysisWorkspaceRef}
          className="main-panel"
          tabIndex={-1}
          aria-label="Analysis workspace"
          aria-keyshortcuts="ArrowLeft ArrowRight"
        >
          <div className="main-header">
            <div>
              <h2>{workspaceLayout === "dense" ? "Token Timeline" : workspaceViewLabel(view)}</h2>
              <p>
                token {selectedTokenInfo.index} · id {selectedTokenInfo.tokenId} · safety proxy{" "}
                {formatScore(selectedTokenInfo.risk)}
              </p>
            </div>
            <div className="selection-trail" aria-label="Current selection">
              <span>{selectedTokenInfo.text}</span>
              <span>L{selectedLayer}</span>
              <span>{selectionComponentLabel(component, selectedHead, topNeuron)}</span>
            </div>
            <LayerSelector
              layers={run.layers}
              selectedLayer={selectedLayer}
              onSelect={selection.selectLayer}
            />
            <WorkspaceTabs view={view} setView={selection.selectView} />
          </div>

          {view !== "nla" && <TokenTimeline
            run={run}
            selectedToken={selectedToken}
            selectedLayer={selectedLayer}
            selectedRange={selectionState.tokenRange}
            setSelectedToken={focusToken}
            setSelectedRange={selection.selectRange}
            hoveredToken={hoveredToken}
            setHoveredToken={setHoveredToken}
            pulseToken={pulseToken}
            pinToken={pinToken}
            pinned={pinnedTokenIndices}
            timeline={timeline}
            onTimelineChange={setTimeline}
          />}
          <SelectionWorkbench
            visible={workspaceLayout === "focus" && selectionActivated}
            tokenText={selectedTokenInfo.text}
            tokenIndex={selectedToken}
            layer={selectedLayer}
            score={formatScore(selectedTokenInfo.risk)}
            view={view}
            menuOpen={selectionMenuOpen}
            contextOpen={focusSupplementOpen}
            pinned={isCurrentPinned}
            canPin={canPinCurrent}
            pinnedCount={pinned.length}
            onToggleMenu={() => setSelectionMenuOpen((current) => !current)}
            onSelectView={(nextView) => {
              setSelectionMenuOpen(false);
              setFocusExperimentOpen(false);
              selection.selectView(nextView);
              window.requestAnimationFrame(() => {
                document.getElementById("analysis-panel")?.scrollIntoView({ block: "start", behavior: "smooth" });
              });
            }}
            onInspect={(trigger) => {
              inspectorReturnTarget.current = trigger;
              setInspectorOpen(true);
            }}
            onToggleContext={() => setFocusSupplementOpen((current) => !current)}
            onPin={() => void pinToken(selectedToken)}
            onPreloadCompare={preloadCompareDrawer}
            onCompare={(trigger) => {
              compareReturnTarget.current = trigger;
              preloadCompareDrawer();
              setCompareOpen(true);
            }}
            onDismiss={() => {
              setSelectionActivated(false);
              setSelectionMenuOpen(false);
            }}
          />
          <div
            className={`mobile-selection-summary ${view === "nla" ? "nla-selection-summary" : ""}`}
            role="region"
            aria-label="Current evidence actions"
          >
            <span><b>{view === "nla" ? `P${selectedToken}` : selectedTokenInfo.text}</b>{view === "nla" ? "position" : "token"}</span>
            <span><b>L{selectedLayer}</b>layer</span>
            <span><b>{view === "nla" ? selectedNlaComponent : formatScore(selectedTokenInfo.risk)}</b>{view === "nla" ? "component" : "safety proxy"}</span>
            <button
              className={isCurrentPinned ? "active" : ""}
              aria-label={isCurrentPinned ? "Unpin current evidence" : "Pin current evidence"}
              aria-pressed={isCurrentPinned}
              disabled={!canPinCurrent}
              title={isCurrentPinned ? "Unpin current evidence" : "Pin current evidence"}
              onClick={() => pinToken(selectedToken)}
            >
              <Pin size={17} />
            </button>
            <button
              aria-label={`Open evidence comparison (${pinned.length})`}
              title="Compare pinned evidence"
              disabled={!pinned.length}
              onPointerDown={preloadCompareDrawer}
              onFocus={preloadCompareDrawer}
              onClick={(event) => {
                compareReturnTarget.current = event.currentTarget;
                setCompareOpen(true);
              }}
            >
              <GitCompareArrows size={17} />
            </button>
            <button
              aria-label="Open evidence inspector"
              title="Open evidence inspector"
              onClick={(event) => {
                inspectorReturnTarget.current = event.currentTarget;
                setInspectorOpen(true);
              }}
            >
              <Info size={17} />
            </button>
          </div>
          {hydration.ready ? (
            <EvidenceSummary
              selectedToken={selectedToken}
              selectedSourceToken={selectedSourceToken}
              selectedLayer={selectedLayer}
              view={view}
              component={component}
              selectedHead={selectedHead}
              neuron={topNeuron}
              nlaRow={nlaRow}
              attributionMethod={selectedAttributionMethod.label}
              attributionEvidenceKind={selectedAttributionMethod.evidenceKind}
              attributionAvailable={selectedAttributionMethod.available}
            />
          ) : (
            <div className="hydration-selection-summary" aria-label="Selected range loading status">
              <Activity size={14} />
              <span><b>{workspaceViewLabel(view)}</b> L{selectedLayer} · token {selectedToken}</span>
              <em>{hydration.error ? "load failed" : "loading range"}</em>
            </div>
          )}

          <ViewErrorBoundary
            resetKey={`${run.runId}:${run.sampleId}:${view}:${selectedLayer}:${selectedHead.id}:${topNeuron?.id ?? "-"}:${selectedTrack}`}
            viewLabel={workspaceViewLabel(view)}
            onOpenOverview={() => selection.selectView("overview")}
          >
          <React.Suspense fallback={<ViewModuleFallback view={view} />}>
          <div
            id="analysis-panel"
            className={`analysis-grid ${view === "overview" ? "overview-analysis-grid" : ""} ${view === "attention" ? "attention-analysis-grid" : ""} ${view === "patching" || view === "intervention" ? "patching-analysis-grid" : ""}`}
            role="tabpanel"
            aria-labelledby={`analysis-tab-${view}`}
          >
            <div className="left-analysis-stack">
              {workspaceLayout === "focus" && focusExperimentOpen &&
                ["attribution", "patching", "intervention"].includes(view) && (
                <div className="focus-experiment-toolbar" role="region" aria-label="Experiment setup controls">
                  <span><FlaskConical size={15} /> Experiment setup</span>
                  <button aria-label="Close experiment setup" onClick={() => setFocusExperimentOpen(false)}>
                    <X size={15} />
                  </button>
                </div>
              )}
              {hydration.partial && ["attribution", "patching", "intervention"].includes(view) && (
                <FullHydrationGate
                  onLoad={() => void library.loadFullActiveRun().catch(() => undefined)}
                />
              )}
              {!hydration.partial && (workspaceLayout === "dense" || focusExperimentOpen) && view === "attribution" && (
                <AttributionJobPanel
                  run={run}
                  onRunReady={(derivedRun, job) => library.addGeneratedRun(
                    derivedRun,
                    job.id,
                    {
                      view: "attribution",
                      trackName: "integrated_gradients",
                      metric: "integrated_gradients",
                      kind: "attribution"
                    }
                  )}
                />
              )}
              {view === "nla" && (
                <NLAJobPanel
                  run={run}
                  selectedToken={selectedToken}
                  onRunReady={(derivedRun, job) => library.addGeneratedRun(
                    derivedRun,
                    job.id,
                    {
                      view: "nla",
                      metric: "nla_cosine",
                      tokenIndex: job.request.positions[0],
                      kind: "nla"
                    }
                  )}
                />
              )}
              {!hydration.partial && (workspaceLayout === "dense" || focusExperimentOpen) && view === "patching" && (
                <PatchingJobPanel
                  run={run}
                  selectedToken={selectedToken}
                  selectedLayer={selectedLayer}
                  onRunReady={(derivedRun, job) => library.addGeneratedRun(
                    derivedRun,
                    job.id,
                    {
                      view: "patching",
                      metric: "patching_recovery",
                      tokenIndex: job.request.positions[0],
                      layer: job.request.layers[0],
                      kind: "patching"
                    }
                  )}
                />
              )}
              {!hydration.partial && (workspaceLayout === "dense" || focusExperimentOpen) && view === "intervention" && (
                <InterventionJobPanel
                  run={run}
                  selectedLayer={selectedLayer}
                  selectedToken={selectedToken}
                  onRunReady={(derivedRun, job) => library.addGeneratedRun(
                    derivedRun,
                    job.id,
                    {
                      view: "intervention",
                      metric: "intervention_logit_delta",
                      tokenIndex: job.request.positionStart,
                      layer: job.request.layer,
                      kind: "intervention"
                    }
                  )}
                />
              )}
              {rolloutPending ? (
                <AttentionRolloutLoading
                  layer={selectedLayer}
                  onCancel={cancelAttentionRollout}
                />
              ) : !hydration.ready ? (
                <ViewChunkState
                  view={view}
                  loading={hydration.loading}
                  error={hydration.error}
                  cancelled={hydration.cancelled}
                  onCancel={library.cancelRemote}
                  onRetry={() => library.ensureViewHydrated(
                    view,
                    selectedLayer,
                    selectedToken,
                    selectedSourceToken
                  )}
                />
              ) : view === "attention" ? (
                <AttentionPatternMatrix
                  heads={layerHeads}
                  selectedHead={selectedHead}
                  tokens={run.tokens}
                  selectedSource={selectedSourceToken}
                  selectedDestination={selectedToken}
                  edgeMode={attentionEdgeMode}
                  selectedRange={selectionState.tokenRange}
                  onHeadChange={selection.selectHead}
                  onEdgeModeChange={selection.selectAttentionEdgeMode}
                  onSelectPair={selection.selectAttentionPair}
                  onRangeSelect={selection.selectRange}
                  onHoverSource={setHoveredToken}
                  onPin={() => pinToken(selectedToken)}
                  onPinPair={(source, destination) => {
                    void pinToken(destination, selectedLayer, { sourceTokenIndex: source });
                  }}
                />
              ) : view === "mlp" ? (
                <MLPActivationMatrix
                  tokens={run.tokens}
                  neurons={layerNeurons}
                  selectedToken={selectedToken}
                  selectedNeuronId={topNeuron?.id ?? ""}
                  partialProfiles={hydration.partial}
                  metric={resolveMlpMetric(selectionState.metric)}
                  selectedRange={selectionState.tokenRange}
                  onMetricChange={(metric) => {
                    selection.selectMetric(metric);
                    selection.setNormalization(
                      metric === "mlp_normalized_activation" ? "normalized" : "raw"
                    );
                  }}
                  onSelectToken={focusToken}
                  onSelectNeuron={selection.selectNeuron}
                  onRangeSelect={selection.selectRange}
                  onHoverToken={setHoveredToken}
                  onPin={() => pinToken(selectedToken)}
                  onPinActivation={(token, neuronId) => {
                    void pinToken(token, selectedLayer, { neuronId });
                  }}
                />
              ) : view === "nla" ? (
                <NLAFidelityMatrix
                  rows={run.nla}
                  compatibility={run.nlaCompatibility}
                  layers={run.layers}
                  tokens={run.tokens}
                  selectedToken={selectedToken}
                  selectedLayer={selectedLayer}
                  selectedComponent={selectedNlaComponent}
                  metric={resolveNlaMetric(selectionState.metric)}
                  selectedRange={selectionState.tokenRange}
                  onMetricChange={(metric) => selection.selectMetric(`nla_${metric}`)}
                  onSelectCell={(layer, token, nlaComponent) => {
                    selection.selectLayer(layer);
                    selection.selectNlaComponent(nlaComponent);
                    focusToken(token);
                  }}
                  onRangeSelect={selection.selectRange}
                  onHoverToken={setHoveredToken}
                  onPin={canPinCurrent ? () => pinToken(selectedToken) : undefined}
                  onPinCell={(layer, token, nlaComponent) => {
                    void pinToken(token, layer, { nlaComponent });
                  }}
                />
              ) : view === "attribution" ? (
                <SignedAttributionMatrix
                  methods={run.attributionMethods}
                  selectedMethod={selectedAttributionMethod}
                  tokens={run.tokens}
                  selectedToken={selectedToken}
                  selectedLayer={selectedLayer}
                  normalization={selectionState.normalization}
                  selectedRange={selectionState.tokenRange}
                  onMethodChange={selection.selectTrack}
                  onNormalizationChange={selection.setNormalization}
                  onSelectCell={(layer, token) => {
                    if (layer >= 0) selection.selectLayer(layer);
                    focusToken(token);
                  }}
                  onRangeSelect={selection.selectRange}
                  onHoverToken={setHoveredToken}
                  onPin={() => pinToken(selectedToken)}
                  onPinCell={(layer, token) => {
                    void pinToken(token, layer >= 0 ? layer : selectedLayer);
                  }}
                  onConfigureIntegratedGradients={() => void openJobSetup("attribution-job")}
                />
              ) : view === "patching" ? (
                run.patching ? (
                  <PatchingCausalMatrix
                    experiment={run.patching}
                    tokens={run.tokens}
                    selectedToken={selectedToken}
                    selectedLayer={selectedLayer}
                    metric={resolvePatchingMetric(selectionState.metric)}
                    selectedRange={selectionState.tokenRange}
                    onMetricChange={(metric) => selection.selectMetric(`patching_${metric}`)}
                    onSelectCell={(layer, token) => {
                      selection.selectLayer(layer);
                      focusToken(token);
                    }}
                    onRangeSelect={selection.selectRange}
                    onPin={() => pinToken(selectedToken)}
                    onPinCell={(layer, token) => {
                      void pinToken(token, layer);
                    }}
                  />
                ) : (
                  <ActionableEmptyState
                    className="surface patching-empty"
                    icon={<FlaskConical size={20} />}
                    title="No causal patch grid in this run"
                    description="Create an aligned corrupted prompt and measure the exact replacement effect in a derived Run."
                    facts={[
                      { label: "Selection", value: `L${selectedLayer} / token ${selectedToken}` },
                      { label: "Component", value: "residual stream" }
                    ]}
                    actionLabel="Configure causal patching"
                    actionIcon={<FlaskConical size={16} />}
                    onAction={() => void openJobSetup("patching-job")}
                  />
                )
              ) : view === "intervention" ? (
                run.intervention ? (
                  <InterventionComparison
                    experiment={run.intervention}
                    onPin={() => pinToken(selectedToken)}
                  />
                ) : (
                  <ActionableEmptyState
                    className="surface intervention-empty"
                    icon={<SlidersHorizontal size={20} />}
                    title="No intervention comparison in this run"
                    description="Define a contrastive direction and generate a matched original-versus-steered derived Run."
                    facts={[
                      { label: "Selection", value: `L${selectedLayer} / token ${selectedToken}` },
                      { label: "Comparison", value: "matched generation" }
                    ]}
                    actionLabel="Configure intervention"
                    actionIcon={<SlidersHorizontal size={16} />}
                    onAction={() => void openJobSetup("intervention-job")}
                  />
                )
              ) : (
                <LayerHeatmap
                  selectedLayer={selectedLayer}
                  selectedToken={selectedToken}
                  hoveredToken={hoveredToken}
                  setHoveredToken={setHoveredToken}
                  setSelectedLayer={selection.selectLayer}
                  setSelectedToken={focusToken}
                  component={component}
                  metric={matrixMetric}
                  normalization={selectionState.normalization}
                  selectedRange={selectionState.tokenRange}
                  setMetric={selection.selectMetric}
                  setNormalization={selection.setNormalization}
                  setSelectedRange={selection.selectRange}
                  pinCurrent={() => pinToken(selectedToken)}
                  pinCell={(layer, tokenIndex) => pinToken(tokenIndex, layer)}
                />
              )}
              {showSupplementalEvidence && hydration.ready && view !== "patching" && view !== "intervention" && <TraceEvidence
                selectedToken={selectedToken}
                selectedLayer={selectedLayer}
                component={component}
                selectedHead={selectedHead}
                neuron={topNeuron}
                residualCell={residualCell}
              />}
              {showSupplementalEvidence && <ModelDigest metadata={run.metadata} />}
              {showSupplementalEvidence && <PinnedStrip
                pinned={pinned}
                restorePin={restoreEvidence}
                availableRunKeys={new Set(library.records.map((record) => record.key))}
                openCompare={() => setCompareOpen(true)}
              />}
            </div>
            {showSupplementalEvidence && hydration.ready && view !== "patching" && view !== "intervention" && <InteractionPanel
              view={view}
              setSelectedView={selection.selectView}
              selectedLayer={selectedLayer}
              setSelectedLayer={selection.selectLayer}
              selectedToken={selectedToken}
              selectedNlaComponent={selectedNlaComponent}
              selectedSourceToken={selectedSourceToken}
              setSelectedToken={focusToken}
              setSelectedSourceToken={selection.selectSourceToken}
              selectedHead={selectedHead}
              selectedHeadId={selectedHead.id}
              setSelectedHeadId={selection.selectHead}
              selectedTrack={selectedTrack}
              setSelectedTrack={selection.selectTrack}
              selectedTrackData={selectedTrackData}
              selectedAttributionMethod={selectedAttributionMethod}
              metric={matrixMetric}
              normalization={selectionState.normalization}
              residualCell={residualCell}
              neuron={topNeuron}
              evidenceFilter={evidenceFilter}
              setEvidenceFilter={setEvidenceFilter}
              onConfigureJob={(anchorId) => void openJobSetup(anchorId)}
            />}
          </div>
          </React.Suspense>
          </ViewErrorBoundary>

        </section>

        <aside className="right-panel">
          <EvidenceInspector
            evidence={inspectorEvidence}
            canPrevious={selectedTokenPosition > 0}
            canNext={selectedTokenPosition < run.tokens.length - 1}
            canPin={canPinCurrent}
            pinned={isCurrentPinned}
            nextActions={inspectorNextActions}
            onPrevious={() => focusToken(run.tokens[selectedTokenPosition - 1].index)}
            onNext={() => focusToken(run.tokens[selectedTokenPosition + 1].index)}
            onPin={() => pinToken(selectedToken)}
            onCompare={() => {
              compareReturnTarget.current = compareTriggerButton.current;
              setInspectorOpen(false);
              setCompareOpen(true);
            }}
            onExport={exportCurrentView}
            onNextAction={runInspectorNextAction}
          />
        </aside>
      </main>
      <QuickActionsDialog
        open={quickActionsOpen}
        returnFocusRef={quickActionsTriggerButton}
        context={{
          runId: run.runId,
          sampleId: run.sampleId,
          view: workspaceViewLabel(view),
          layer: selectedLayer,
          token: selectedToken,
          tokenText: selectedTokenInfo.text
        }}
        pinnedCount={pinned.length}
        onClose={() => setQuickActionsOpen(false)}
        onOverview={() => {
          setQuickActionsOpen(false);
          selection.selectView("overview");
          window.requestAnimationFrame(() => analysisWorkspaceRef.current?.focus());
        }}
        onRuns={() => {
          setQuickActionsOpen(false);
          libraryReturnTarget.current = quickActionsTriggerButton.current;
          window.requestAnimationFrame(() => setLibraryOpen(true));
        }}
        onTokenSearch={() => {
          setQuickActionsOpen(false);
          window.requestAnimationFrame(() => {
            document.getElementById("token-timeline-search")?.focus();
          });
        }}
        onCompare={() => {
          setQuickActionsOpen(false);
          compareReturnTarget.current = compareTriggerButton.current;
          preloadCompareDrawer();
          window.requestAnimationFrame(() => setCompareOpen(true));
        }}
        onExportSession={() => {
          setQuickActionsOpen(false);
          exportAnalysisSession();
        }}
        onExportArtifact={() => {
          setQuickActionsOpen(false);
          void exportRunArtifact();
        }}
        onExportEvidence={() => {
          setQuickActionsOpen(false);
          exportCurrentView();
        }}
      />
      {libraryOpen && (
        <div
          className="mobile-library-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setLibraryOpen(false);
          }}
        >
          <aside
            ref={libraryDialog}
            className="mobile-library-drawer"
            role="dialog"
            tabIndex={-1}
            aria-modal="true"
            aria-labelledby="mobile-library-title"
          >
            <header>
              <div>
                <span>Data workspace</span>
                <h2 id="mobile-library-title">Runs and samples</h2>
              </div>
              <button
                ref={libraryCloseButton}
                aria-label="Close run library"
                onClick={() => setLibraryOpen(false)}
              >
                <X size={18} />
              </button>
            </header>
            <RunLibraryPanel
              records={library.records}
              activeRecord={library.activeRecord}
              message={library.message}
              remoteState={library.remoteState}
              onMessage={library.setMessage}
              onSelect={(key) => {
                library.selectRun(key);
                setLibraryOpen(false);
              }}
              onAdd={(runs, sourceName, schemaVersion) => {
                const added = library.addRuns(runs, sourceName, schemaVersion);
                if (added) setLibraryOpen(false);
                return added;
              }}
              onRemove={library.removeRun}
              onRestoreSession={restoreAnalysisSession}
              onRefreshRemote={() => void library.refreshRemote()}
              onCancelRemote={library.cancelRemote}
            />
            <PromptRunnerPanel
              run={run}
              onRunReady={(generatedRun, job) => {
                library.addGeneratedRun(generatedRun, job.id);
                setLibraryOpen(false);
              }}
            />
            <section className="panel-section mobile-drawer-secondary">
              <div className="section-heading">
                <Search size={16} />
                <span>Data provenance</span>
              </div>
              <ProvenanceList />
            </section>
            <section className="panel-section mobile-drawer-secondary">
              <div className="section-heading">
                <Crosshair size={16} />
                <span>Evidence</span>
              </div>
              <div className="evidence-list">
                {evidenceTokens.map((tokenIndex) => (
                  <button
                    key={tokenIndex}
                    onClick={() => {
                      selectEvidenceToken(tokenIndex);
                      setLibraryOpen(false);
                    }}
                  >
                    <span>{run.tokens[tokenIndex].text}</span>
                    <b>{formatScore(run.tokens[tokenIndex].risk)}</b>
                  </button>
                ))}
              </div>
            </section>
          </aside>
        </div>
      )}
      {inspectorOpen && (
        <div
          className="mobile-inspector-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setInspectorOpen(false);
          }}
        >
          <aside
            ref={inspectorDialog}
            className="mobile-inspector-drawer"
            data-detail-level={inspectorExpanded ? "full" : "compact"}
            role="dialog"
            tabIndex={-1}
            aria-modal="true"
            aria-labelledby="mobile-inspector-title"
          >
            <header
              onPointerDown={(event) => {
                if (event.button !== 0 || (event.target as HTMLElement).closest("button")) return;
                inspectorGesture.current = {
                  pointerId: event.pointerId,
                  startY: event.clientY
                };
                event.currentTarget.setPointerCapture(event.pointerId);
              }}
            >
              <div>
                <span>{inspectorExpanded ? "Full provenance" : "Selected evidence"}</span>
                <h2 id="mobile-inspector-title">Evidence details</h2>
              </div>
              <div className="mobile-inspector-header-actions">
                <button
                  aria-label={inspectorExpanded ? "Show compact evidence summary" : "Show full evidence details"}
                  aria-expanded={inspectorExpanded}
                  onClick={() => setInspectorExpanded((current) => !current)}
                >
                  {inspectorExpanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
                </button>
                <button
                  ref={inspectorCloseButton}
                  aria-label="Close evidence inspector"
                  onClick={() => setInspectorOpen(false)}
                >
                  <X size={18} />
                </button>
              </div>
            </header>
            <EvidenceInspector
              evidence={inspectorEvidence}
              canPrevious={selectedTokenPosition > 0}
              canNext={selectedTokenPosition < run.tokens.length - 1}
              canPin={canPinCurrent}
              pinned={isCurrentPinned}
              nextActions={inspectorNextActions}
              onPrevious={() => focusToken(run.tokens[selectedTokenPosition - 1].index)}
              onNext={() => focusToken(run.tokens[selectedTokenPosition + 1].index)}
              onPin={() => pinToken(selectedToken)}
              onCompare={() => {
                compareReturnTarget.current = inspectorReturnTarget.current;
                setInspectorOpen(false);
                setCompareOpen(true);
              }}
              onExport={exportCurrentView}
              onNextAction={runInspectorNextAction}
              detailLevel={inspectorExpanded ? "full" : "compact"}
            />
          </aside>
        </div>
      )}
      {compareOpen && (
        <ViewErrorBoundary
          variant="dialog"
          resetKey={`${runKey(run)}:${pinned.map((item) => item.id).join("|")}:${compareBaselineId ?? "-"}`}
          viewLabel="Evidence comparison"
          onDismiss={() => {
            setCompareOpen(false);
            window.requestAnimationFrame(() => compareReturnTarget.current?.focus());
          }}
        >
          <React.Suspense fallback={<CompareDrawerFallback />}>
            <CompareDrawer
              open
              pinned={pinned}
              tokens={run.tokens}
              metricProvenance={run.metricProvenance}
              currentRunKey={runKey(run)}
              availableRunKeys={new Set(library.records.map((record) => record.key))}
              baselineId={compareBaselineId}
              returnFocusRef={compareReturnTarget}
              onClose={() => setCompareOpen(false)}
              onRestore={restoreEvidence}
              onRemove={selection.togglePin}
              onBaselineChange={setCompareBaselineId}
            />
          </React.Suspense>
        </ViewErrorBoundary>
      )}
    </div>
    </MatrixViewportSessionProvider>
  );
}

function CompareDrawerFallback() {
  return (
    <div className="compare-backdrop">
      <aside
        className="compare-drawer compare-drawer-loading"
        role="dialog"
        aria-modal="true"
        aria-label="Loading evidence comparison"
      >
        <Activity size={20} />
        <strong>Preparing evidence comparison</strong>
        <span role="status">Loading comparison visualization.</span>
      </aside>
    </div>
  );
}

function ContextChangeNotice({ notice }: { notice: ContextNotice | null }) {
  const statusLabel = notice?.kind === "run" ? "Run changed" : "Context updated";
  return (
    <>
      <div
        className="visually-hidden"
        role="log"
        aria-live="polite"
        aria-atomic="true"
        aria-label="Analysis context changes"
      >
        {notice ? `${statusLabel}: ${notice.message}` : ""}
      </div>
      <div
        className={`context-change-notice${notice?.visible ? " visible" : ""}`}
        aria-hidden="true"
        data-kind={notice?.kind ?? "selection"}
      >
        <CheckCircle2 size={18} />
        <span>{statusLabel}</span>
        <strong>{notice?.message ?? ""}</strong>
      </div>
    </>
  );
}

function runChangeMessage(
  run: ExplorerRun,
  session: ExplorerSession | null,
  transition?: "fresh" | "restored"
) {
  const views: WorkspaceView[] = [
    "overview", "residual", "attention", "mlp", "nla", "patching", "intervention", "attribution"
  ];
  const params = new URLSearchParams(window.location.search);
  const sessionMatches = session?.workspace.runId === run.runId &&
    session.workspace.sampleId === run.sampleId;
  const requestedView = sessionMatches ? session.selection.view : params.get("view");
  const view = views.includes(requestedView as WorkspaceView)
    ? requestedView as WorkspaceView
    : "overview";
  const requestedToken = sessionMatches
    ? session.selection.targetTokenIndex ?? session.selection.tokenIndex
    : locationInteger(params, "target") ?? locationInteger(params, "token");
  const token = requestedToken !== undefined && run.tokens.some((item) => item.index === requestedToken)
    ? requestedToken
    : topEvidenceTokens(run.tokens)[0] ?? run.tokens[0]?.index ?? 0;
  const requestedLayer = sessionMatches
    ? session.selection.layer
    : locationInteger(params, "layer");
  const layer = requestedLayer !== undefined && run.layers.includes(requestedLayer)
    ? requestedLayer
    : run.layers[run.layers.length - 1] ?? 0;
  const hasExplicitContext = sessionMatches || [
    "view", "token", "target", "layer", "head", "neuron", "track", "metric", "normalization"
  ].some((key) => params.has(key));
  const contextKind = sessionMatches
    ? "session context"
    : transition === "fresh"
      ? "fresh selection"
      : transition === "restored" || hasExplicitContext
      ? "restored context"
      : "fresh selection";
  return `${run.sampleId} · ${workspaceViewLabel(view)} · T${token} · L${layer} · ${contextKind}`;
}

function locationInteger(params: URLSearchParams, key: string) {
  const value = params.get(key);
  return value !== null && /^\d+$/.test(value) ? Number(value) : undefined;
}

function loadingInspectorEvidence(
  run: ExplorerRun,
  view: WorkspaceView,
  layer: number,
  token: number,
  error?: string,
  cancelled = false
): InspectorEvidence {
  return {
    title: run.tokens[token]?.text || `token ${token}`,
    subtitle: `${workspaceViewLabel(view)} · L${layer}`,
    status: error ? "failed" : cancelled ? "cancelled" : "loading",
    statusReason: error ?? (cancelled ? "Artifact range loading was cancelled." : "Loading the selected artifact range."),
    primaryLabel: workspaceViewLabel(view),
    primaryValue: error ? "load failed" : cancelled ? "cancelled" : "loading",
    rawValue: "pending",
    displayValue: "pending",
    units: "pending",
    evidenceClass: "raw",
    method: "artifact chunk hydration",
    normalization: "pending",
    cacheKey: "",
    shape: "current viewport range",
    sourceArtifact: "workspace chunk protocol",
    runId: run.runId,
    sampleId: run.sampleId,
    modelName: run.modelName,
    warnings: error ? [error] : [],
    reproduction: { runId: run.runId, sampleId: run.sampleId, view, layer, token }
  };
}

function inspectorEvidenceAssessment(evidence: InspectorEvidence): EvidenceAssessment {
  return {
    schemaVersion: "1.0",
    status: evidence.status,
    statusReason: evidence.statusReason,
    primaryLabel: evidence.primaryLabel,
    primaryValue: evidence.primaryValue,
    rawValue: evidence.rawValue,
    displayValue: evidence.displayValue,
    units: evidence.units,
    evidenceClass: evidence.evidenceClass,
    method: evidence.method,
    normalization: evidence.normalization,
    cacheKey: evidence.cacheKey,
    shape: evidence.shape,
    sourceArtifact: evidence.sourceArtifact,
    warnings: [...evidence.warnings],
    reproduction: structuredClone(evidence.reproduction)
  };
}

function buildInitialOverviewPins(
  run: ExplorerRun,
  tokenIndices: number[],
  layer: number,
  sourceArtifact: string
): PinnedEvidence[] {
  const selectedHead = run.attentionHeads.find((head) => head.layer === layer);
  const selectedNeuron = run.mlpNeurons.find((neuron) => neuron.layer === layer);
  const selectedAttributionMethod = run.attributionMethods.find((method) => method.available) ??
    run.attributionMethods[0];
  return tokenIndices.map((tokenIndex) => {
    const token = run.tokens.find((candidate) => candidate.index === tokenIndex) ?? run.tokens[0];
    const base: PinnedEvidence = {
      id: `${run.runId}:${run.sampleId}:${tokenIndex}:${layer}:overview:tokenRisk:normalized:-:-:-`,
      runId: run.runId,
      sampleId: run.sampleId,
      tokenIndex,
      tokenText: token.text,
      tokenId: token.tokenId,
      tokenSource: token.source,
      modelName: run.modelName,
      modelSource: run.modelSource,
      layer,
      view: "overview",
      component: "resid_post",
      metric: "tokenRisk",
      value: token.risk,
      normalization: "normalized",
      sourceKey: `layer_${layer}.resid_post[${tokenIndex}]`,
      provenance: run.metricProvenance.tokenRisk
    };
    if (!selectedHead || !selectedAttributionMethod) return base;
    return {
      ...base,
      assessment: inspectorEvidenceAssessment(buildInspectorEvidence({
        run,
        view: "overview",
        selectedToken: tokenIndex,
        selectedSourceToken: tokenIndex,
        selectedLayer: layer,
        selectedNlaComponent: "resid_post",
        selectedHead,
        selectedNeuron,
        selectedAttributionMethod,
        metric: "tokenRisk",
        normalization: "normalized",
        sourceArtifact
      }))
    };
  });
}

function ViewChunkState({
  view,
  loading,
  error,
  cancelled,
  onCancel,
  onRetry
}: {
  view: WorkspaceView;
  loading: boolean;
  error?: string;
  cancelled: boolean;
  onCancel: () => void;
  onRetry: () => void;
}) {
  const cancelStartedAt = React.useRef<number | null>(null);

  React.useEffect(() => {
    if (!cancelled || cancelStartedAt.current === null) return;
    recordExplorerPerformance("cancel-feedback", {
      latencyMs: performance.now() - cancelStartedAt.current
    });
    cancelStartedAt.current = null;
  }, [cancelled]);

  function requestCancel() {
    cancelStartedAt.current = performance.now();
    recordExplorerPerformance("cancel-request");
    onCancel();
  }

  return (
    <div className={`surface view-chunk-state ${error ? "error" : cancelled ? "cancelled" : "loading"}`} role={error ? "alert" : "status"}>
      {error ? <AlertTriangle size={20} /> : <Activity size={20} />}
      <div>
        <strong>{error
          ? `${workspaceViewLabel(view)} data could not be loaded`
          : cancelled
            ? `${workspaceViewLabel(view)} loading cancelled`
            : `Loading ${workspaceViewLabel(view)} data`}</strong>
        <p>{error ?? (cancelled
          ? "Previously loaded ranges remain available."
          : loading ? "Requesting the selected layer and token range." : "Preparing the artifact request.")}</p>
      </div>
      {(error || cancelled) && <button onClick={onRetry}>Retry</button>}
      {!error && !cancelled && loading && <button onClick={requestCancel}>Cancel</button>}
      {!error && !cancelled && <AnalysisLoadingSkeleton view={view} />}
    </div>
  );
}

function ViewModuleFallback({ view }: { view: WorkspaceView }) {
  return (
    <div
      className="surface view-module-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={`Loading ${workspaceViewLabel(view)} view`}
    >
      <Activity className="spin" size={20} aria-hidden="true" />
      <div>
        <strong>Preparing {workspaceViewLabel(view)} view</strong>
        <p>The analysis surface is loading its visualization module.</p>
      </div>
      <AnalysisLoadingSkeleton view={view} />
    </div>
  );
}

function AnalysisLoadingSkeleton({ view }: { view: WorkspaceView }) {
  return (
    <div
      className="analysis-loading-skeleton"
      data-loading-view={view}
      aria-hidden="true"
    >
      <div className="analysis-loading-toolbar">
        <span />
        <span />
        <span />
      </div>
      <div className="analysis-loading-stage">
        <span className="analysis-loading-axis analysis-loading-axis-y" />
        <span className="analysis-loading-axis analysis-loading-axis-x" />
        <div className="analysis-loading-grid" />
        <span className="analysis-loading-viewport" />
      </div>
      <div className="analysis-loading-footer">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

function FullHydrationGate({ onLoad }: { onLoad: () => void }) {
  return (
    <div className="surface full-hydration-gate" role="status">
      <Database size={18} />
      <div>
        <strong>Full Run required for experiments</strong>
        <p>Current visualization uses validated range chunks.</p>
      </div>
      <button onClick={onLoad}>Load full Run</button>
    </div>
  );
}

function AttentionRolloutLoading({ layer, onCancel }: { layer: number; onCancel: () => void }) {
  return (
    <div className="surface full-hydration-gate attention-rollout-loading" role="status">
      <Activity size={18} className="spin" />
      <div>
        <strong>Loading complete attention for rollout</strong>
        <p>Computing retained-head mean + identity residual through L{layer} requires every preceding layer.</p>
      </div>
      <button onClick={onCancel}>Cancel</button>
    </div>
  );
}

function Metric({
  label,
  shortLabel,
  value,
  tone
}: {
  label: string;
  shortLabel: string;
  value: string;
  tone: string;
}) {
  return (
    <div className={`metric metric-${tone}`} aria-label={`${label} metric`}>
      <span className="metric-label-full" aria-hidden="true">{label}</span>
      <span className="metric-label-short" aria-hidden="true">{shortLabel}</span>
      <strong>{value}</strong>
    </div>
  );
}

function pulseSelectionToken(
  tokenIndex: number,
  setPulseToken: React.Dispatch<React.SetStateAction<number | null>>
) {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    setPulseToken(null);
    return;
  }
  setPulseToken(tokenIndex);
  window.setTimeout(() => {
    setPulseToken((current) => (current === tokenIndex ? null : current));
  }, 560);
}

function ProvenanceList() {
  const explorerRun = useExplorerRun();
  const availableNlaRows = explorerRun.nla.filter((row) => row.status !== "unavailable").length;
  const items = [
    ["Real model cache", "tokens, residuals, attention, MLP", "Directly captured model data."],
    [
      "Safety proxy",
      "residual direction projection",
      explorerRun.metricProvenance.tokenRisk.semantics
    ],
    [
      "Attention proxy",
      "descriptive, not causal attribution",
      explorerRun.metricProvenance.tokenAttribution.semantics
    ],
    [
      "NLA",
      availableNlaRows > 0 ? `${availableNlaRows} exact fidelity rows` : "no compatible result artifact",
      availableNlaRows > 0
        ? "Exact NLA rows are available for this run."
        : "Compatibility diagnostics explain why NLA rows are unavailable."
    ]
  ];

  return (
    <div className="provenance-list">
      {items.map(([label, value, detail]) => (
        <span key={label} title={detail}>
          <b>{label}</b>
          <i>{value}</i>
        </span>
      ))}
    </div>
  );
}

function ModelDigest({ metadata }: { metadata?: Record<string, unknown> }) {
  const nextToken = metadataText(metadata, "nextToken", "n/a");
  const targetDirection = metadataText(metadata, "riskDirectionToken", "n/a");
  const generated = metadataText(metadata, "generatedContinuation", "n/a");

  return (
    <section className="surface digest-panel">
      <div className="surface-header">
        <div>
          <h3>Model output</h3>
          <p>Real forward-pass metadata</p>
        </div>
        <Activity size={18} />
      </div>
      <div className="digest-grid">
        <span>
          <b>{nextToken}</b>
          next token
        </span>
        <span>
          <b>{targetDirection}</b>
          target direction
        </span>
        <span>
          <b>{generated}</b>
          greedy continuation
        </span>
      </div>
    </section>
  );
}

function TraceEvidence({
  selectedToken,
  selectedLayer,
  component,
  selectedHead,
  neuron,
  residualCell
}: {
  selectedToken: number;
  selectedLayer: number;
  component: ComponentKind;
  selectedHead: AttentionHead;
  neuron?: MLPNeuron;
  residualCell?: { norm: number; riskDirection: number; semanticDensity: number };
}) {
  const explorerRun = useExplorerRun();
  const token = explorerRun.tokens[selectedToken];
  const rows =
    component === "attention"
      ? selectedHead.difference
        ? [
            ["attention head (diff)", attentionHeadLabel(selectedHead)],
            ["selected", selectedHead.difference.selectedHeadId],
            ["baseline", selectedHead.difference.baselineHeadId],
            ["evidence", "derived signed proxy"]
          ]
        : selectedHead.rollout
        ? [
            ["attention path", attentionHeadLabel(selectedHead)],
            ["layers", selectedHead.rollout.layers.map((layer) => `L${layer}`).join(" → ")],
            ["members", `${selectedHead.rollout.memberHeadIds.length} retained heads`],
            ["evidence", "derived path proxy"]
          ]
        : selectedHead.aggregation
        ? [
            ["aggregation", attentionAggregationLabel(selectedHead.aggregation)],
            ["members", selectedHead.memberHeadIds?.join(" · ") ?? "retained heads"],
            ["evidence", "derived proxy"]
          ]
        : [
            ["attention head", selectedHead.id],
            ["keyword mass", formatScore(selectedHead.riskContribution)],
            ["entropy", formatScore(selectedHead.entropy)]
          ]
      : component === "mlp" && neuron
        ? [
            ["MLP neuron", neuron.id],
            ["activation", formatScore(neuron.activation, "mlp_signed_activation")],
            ["top tokens", neuron.topTokens.map((index) => explorerRun.tokens[index].text).join(" · ")]
          ]
        : [
            ["residual stream", "resid_post"],
            ["norm", (residualCell?.norm ?? 0).toFixed(1)],
            ["direction", formatScore(residualCell?.riskDirection ?? 0, "residual_direction")]
          ];

  return (
    <section className="surface trace-panel">
      <div className="surface-header">
        <div>
          <h3>Trace evidence</h3>
          <p>
            {token.text} · L{selectedLayer}
          </p>
        </div>
        <Crosshair size={18} />
      </div>
      <div className="trace-grid">
        {rows.map(([label, value]) => (
          <span key={label}>
            <b>{value}</b>
            {label}
          </span>
        ))}
      </div>
    </section>
  );
}

function EvidenceSummary({
  selectedToken,
  selectedSourceToken,
  selectedLayer,
  view,
  component,
  selectedHead,
  neuron,
  nlaRow,
  attributionMethod,
  attributionEvidenceKind,
  attributionAvailable
}: {
  selectedToken: number;
  selectedSourceToken: number;
  selectedLayer: number;
  view: WorkspaceView;
  component: ComponentKind;
  selectedHead: AttentionHead;
  neuron?: MLPNeuron;
  nlaRow?: NLARow;
  attributionMethod: string;
  attributionEvidenceKind: MetricProvenance["kind"];
  attributionAvailable: boolean;
}) {
  const explorerRun = useExplorerRun();
  const token = explorerRun.tokens[selectedToken];
  const items = [
    { label: "Selected signal", value: `${token.text} · ${formatScore(token.risk)}` },
    { label: "Context", value: `L${selectedLayer} · ${workspaceViewLabel(view)}` },
    {
      label: "Evidence",
      value:
        view === "attention"
          ? `${attentionHeadLabel(selectedHead)} · ${selectedSourceToken}→${selectedToken}`
          : view === "attribution"
            ? attributionMethod
          : view === "patching"
            ? explorerRun.patching?.component ?? "experiment setup"
          : view === "intervention"
            ? explorerRun.intervention?.component ?? "experiment setup"
          : selectionComponentLabel(component, selectedHead, neuron)
    },
    {
      label: "Evidence class",
      value:
        view === "attention"
          ? selectedHead.aggregation || selectedHead.difference || selectedHead.rollout ? "derived proxy" : "raw attention"
          : view === "attribution"
            ? attributionAvailable
              ? attributionEvidenceKind.replace("_", " ")
              : "method unavailable"
          : view === "nla"
            ? nlaRow?.status === "available"
              ? "NLA explanation"
              : "unavailable"
          : view === "patching"
            ? explorerRun.patching ? "causal" : "not computed"
          : view === "intervention"
            ? explorerRun.intervention ? "causal intervention" : "not computed"
            : "derived proxy"
    }
  ];

  return (
    <section className="evidence-summary" aria-label="Current evidence summary">
      {items.map((item) => (
        <span key={item.label}>
          <em>{item.label}</em>
          <i>{item.value}</i>
        </span>
      ))}
    </section>
  );
}

function LayerHeatmap({
  selectedLayer,
  selectedToken,
  hoveredToken,
  setHoveredToken,
  setSelectedLayer,
  setSelectedToken,
  component,
  metric,
  normalization,
  selectedRange,
  setMetric,
  setNormalization,
  setSelectedRange,
  pinCurrent,
  pinCell
}: {
  selectedLayer: number;
  selectedToken: number;
  hoveredToken: number | null;
  setHoveredToken: (token: number | null) => void;
  setSelectedLayer: (layer: number) => void;
  setSelectedToken: (token: number) => void;
  component: ComponentKind;
  metric: string;
  normalization: NormalizationMode;
  selectedRange?: [number, number];
  setMetric: (metric: string) => void;
  setNormalization: (normalization: NormalizationMode) => void;
  setSelectedRange: (range?: [number, number]) => void;
  pinCurrent: () => void;
  pinCell: (layer: number, token: number) => void;
}) {
  const explorerRun = useExplorerRun();
  const cells = matrixCellsForComponent(explorerRun, component, metric);
  const provenance = matrixProvenance(explorerRun, component, metric);
  return (
    <MatrixHeatmap
      title={provenance.label}
      subtitle={provenance.semantics}
      rows={explorerRun.layers}
      columns={explorerRun.tokens}
      cells={cells}
      metric={metric}
      metricOptions={matrixMetricOptions(component)}
      provenance={provenance}
      normalization={normalization}
      selectedRow={selectedLayer}
      selectedColumn={selectedToken}
      selectedRange={selectedRange}
      hoveredColumn={hoveredToken}
      color={component}
      onMetricChange={setMetric}
      onNormalizationChange={setNormalization}
      onSelectCell={(layer, tokenIndex) => {
        setSelectedLayer(layer);
        setSelectedToken(tokenIndex);
      }}
      onRangeSelect={setSelectedRange}
      onHoverColumn={setHoveredToken}
      onPin={pinCurrent}
      onPinCell={pinCell}
    />
  );
}

function InteractionPanel({
  view,
  setSelectedView,
  selectedLayer,
  setSelectedLayer,
  selectedToken,
  selectedNlaComponent,
  selectedSourceToken,
  setSelectedToken,
  setSelectedSourceToken,
  selectedHead,
  selectedHeadId,
  setSelectedHeadId,
  selectedTrack,
  setSelectedTrack,
  selectedTrackData,
  selectedAttributionMethod,
  metric,
  normalization,
  residualCell,
  neuron,
  evidenceFilter,
  setEvidenceFilter,
  onConfigureJob
}: {
  view: WorkspaceView;
  setSelectedView: (view: WorkspaceView) => void;
  selectedLayer: number;
  setSelectedLayer: (layer: number) => void;
  selectedToken: number;
  selectedNlaComponent: NLARow["component"];
  selectedSourceToken: number;
  setSelectedToken: (token: number) => void;
  setSelectedSourceToken: (token: number) => void;
  selectedHead: AttentionHead;
  selectedHeadId: string;
  setSelectedHeadId: (id: string) => void;
  selectedTrack: string;
  setSelectedTrack: (track: string) => void;
  selectedTrackData: { name: string; values: number[] };
  selectedAttributionMethod: AttributionMethod;
  metric: string;
  normalization: NormalizationMode;
  residualCell?: {
    norm: number;
    rawDirection: number;
    riskDirection: number;
    semanticDensity: number;
  };
  neuron?: MLPNeuron;
  evidenceFilter: EvidenceFilter;
  setEvidenceFilter: (filter: EvidenceFilter) => void;
  onConfigureJob: (anchorId: string) => void;
}) {
  const explorerRun = useExplorerRun();
  if (view === "overview") {
    return (
      <OverviewEvidenceGraph
        run={explorerRun}
        selectedToken={selectedToken}
        selectedLayer={selectedLayer}
        residualCell={residualCell}
        onNavigate={setSelectedView}
      />
    );
  }

  if (view === "residual") {
    return (
      <ResidualEvidence
        selectedToken={selectedToken}
        selectedLayer={selectedLayer}
        setSelectedLayer={setSelectedLayer}
        metric={metric}
        normalization={normalization}
        residualCell={residualCell}
      />
    );
  }

  if (view === "mlp") {
    return (
      <MLPEvidence selectedToken={selectedToken} selectedLayer={selectedLayer} neuron={neuron} />
    );
  }

  if (view === "nla") {
    const exactRow = matchingNla(
      explorerRun.nla,
      selectedToken,
      selectedLayer,
      selectedNlaComponent
    );
    const activationViews: Array<{
      view: Extract<WorkspaceView, "residual" | "attention" | "mlp">;
      label: string;
      component: NLARow["component"];
      icon: React.ReactNode;
    }> = [
      { view: "residual", label: "Residual", component: "resid_post", icon: <Waves size={16} /> },
      { view: "attention", label: "Attention", component: "attn_result", icon: <Network size={16} /> },
      { view: "mlp", label: "MLP", component: "mlp_out", icon: <BrainCircuit size={16} /> }
    ];
    return (
      <section className="surface nla-evidence-detail">
        <div className="surface-header">
          <div>
            <h3>Exact NLA evidence</h3>
            <p>token {selectedToken} · layer {selectedLayer} · {selectedNlaComponent} · strict match</p>
          </div>
          <Sparkles size={18} />
        </div>
        {!exactRow ? (
          <ActionableEmptyState
            compact
            icon={<Sparkles size={18} />}
            title="No exact NLA artifact row"
            description="Nearby tokens, layers, or components are intentionally not substituted. Compute this exact selection instead."
            facts={[
              { label: "Selection", value: `L${selectedLayer} / token ${selectedToken}` },
              { label: "Component", value: selectedNlaComponent }
            ]}
            actionLabel="Configure exact NLA"
            actionIcon={<Sparkles size={16} />}
            onAction={() => onConfigureJob("nla-job")}
          />
        ) : exactRow.status === "unavailable" ? (
          <>
            <div className="nla-exact-facts">
              <span><b>{exactRow.token}</b>token {exactRow.tokenIndex}</span>
              <span><b>L{exactRow.layer}</b>{exactRow.component}</span>
              <span><b>{exactRow.activationNorm.toFixed(4)}</b>activation norm</span>
              <span><b>unavailable</b>decoder status</span>
            </div>
            <ActionableEmptyState
              compact
              icon={<Sparkles size={18} />}
              title="Activation is cached; NLA decoding is unavailable"
              description={exactRow.explanation}
              facts={[
                { label: "Source", value: exactRow.source ?? "not stored" },
                { label: "Activation norm", value: exactRow.activationNorm.toFixed(4) }
              ]}
              actionLabel="Configure exact NLA"
              actionIcon={<Sparkles size={16} />}
              onAction={() => onConfigureJob("nla-job")}
            />
          </>
        ) : (
          <>
            <div className="nla-exact-facts">
              <span><b>{exactRow.cosine.toFixed(4)}</b>cosine</span>
              <span><b>{exactRow.mse.toFixed(4)}</b>MSE</span>
              <span><b>{exactRow.fve?.toFixed(4) ?? "n/a"}</b>FVE</span>
              <span><b>{exactRow.activationNorm.toFixed(4)}</b>activation norm</span>
            </div>
            <NLARowCard row={exactRow} />
          </>
        )}
        <div className="nla-cross-view-links" role="group" aria-label="Activation context views">
          <div>
            <strong>Activation context</strong>
            <span>Keep token {selectedToken} and L{selectedLayer} while changing evidence view.</span>
          </div>
          {activationViews.map((target) => (
            <button
              key={target.view}
              type="button"
              aria-label={`Open ${target.label} at layer ${selectedLayer}, token ${selectedToken}`}
              onClick={() => setSelectedView(target.view)}
            >
              {target.icon}
              <span>
                <b>{target.label}</b>
                {target.component === selectedNlaComponent ? "component context" : "same token / layer"}
              </span>
              <ChevronRight size={15} />
            </button>
          ))}
        </div>
      </section>
    );
  }

  if (view === "attention") {
    const row = selectedHead.distributionByToken[selectedToken] ?? [];
    const selectedHeadLabel = attentionHeadLabel(selectedHead);
    const evidenceCandidates =
      row.slice(0, selectedToken + 1).map((value, index) => ({
        tokenIndex: index,
        score: value,
        reason: attentionReason(explorerRun, index, selectedToken)
      }));
    const evidenceRows = selectedHead.difference
      ? filterEvidenceRowsByMagnitude(evidenceCandidates, selectedToken, evidenceFilter)
      : filterEvidenceRows(evidenceCandidates, selectedToken, evidenceFilter);
    return (
      <section className="surface attention-distribution">
        <div className="surface-header">
          <div>
            <h3>Attention distribution</h3>
            <p>{selectedHeadLabel} · destination token {selectedToken} row</p>
          </div>
          <Network size={18} />
        </div>
        <div className="head-picker">
          {(selectedHead.aggregation || selectedHead.difference || selectedHead.rollout) && (
            <span className="aggregate-head-label">{selectedHeadLabel}</span>
          )}
          {explorerRun.attentionHeads
            .filter((head) => head.layer === selectedLayer)
            .map((head) => (
            <button
              key={head.id}
              className={
                selectedHead.difference?.selectedHeadId === head.id || selectedHeadId === head.id
                  ? "active"
                  : ""
              }
              onClick={() => {
                if (!selectedHead.difference) {
                  setSelectedHeadId(head.id);
                  return;
                }
                const baseline = selectedHead.difference.baselineHeadId === head.id
                  ? explorerRun.attentionHeads.find((candidate) =>
                      candidate.layer === selectedLayer && candidate.id !== head.id
                    )?.id ?? selectedHead.difference.baselineHeadId
                  : selectedHead.difference.baselineHeadId;
                setSelectedHeadId(attentionDifferenceId(head.id, baseline));
              }}
            >
              {head.id}
            </button>
          ))}
        </div>
        <EvidenceFilterBar filter={evidenceFilter} setFilter={setEvidenceFilter} />
        <EvidenceTable
          rows={evidenceRows}
          selectedToken={selectedSourceToken}
          onSelectToken={setSelectedSourceToken}
          scoreTone={selectedHead.difference ? "attention-difference" : "attention"}
        />
      </section>
    );
  }

  const attributionEntries = selectedTrackData.values.map((value, tokenIndex) => ({
    tokenIndex,
    value
  }));
  const positiveEntries = [...attributionEntries]
    .filter((entry) => entry.value > 0)
    .sort((left, right) => right.value - left.value)
    .slice(0, 5);
  const negativeEntries = [...attributionEntries]
    .filter((entry) => entry.value < 0)
    .sort((left, right) => left.value - right.value)
    .slice(0, 5);
  const attributionJob = selectedAttributionMethod.id === "integrated_gradients"
    ? latestAttributionJob(explorerRun.metadata)
    : undefined;
  const rawAttributionValues = Array.isArray(attributionJob?.rawValues) &&
    attributionJob.rawValues.length === selectedTrackData.values.length &&
    attributionJob.rawValues.every((value) => typeof value === "number" && Number.isFinite(value))
      ? attributionJob.rawValues as number[]
      : undefined;
  const accountingValues = rawAttributionValues ?? selectedTrackData.values;
  const methodSnapshots = explorerRun.attributionMethods.map((method) => {
    const row = method.rows.find((candidate) => candidate.layer === selectedLayer) ??
      method.rows.find((candidate) => candidate.layer < 0);
    return {
      method,
      row,
      value: row?.values[selectedToken]
    };
  });
  return (
    <section className="surface attribution-distribution">
      <div className="surface-header">
        <div>
          <h3>Attribution evidence</h3>
          <p>{selectedAttributionMethod.label}</p>
        </div>
        <BarChart3 size={18} />
      </div>
      <div className="attribution-method-compare-heading">
        <div>
          <strong>Selected-token method snapshots</strong>
          <span>Within-method values only; different methods and scales do not produce a direct delta.</span>
        </div>
        <b>token {selectedToken}</b>
      </div>
      <div className="attribution-method-catalog" aria-label="Attribution methods">
        {methodSnapshots.map(({ method, row, value }) => (
          <button
            key={method.id}
            className={`${selectedTrack === method.id ? "active" : ""} ${method.available ? "" : "unavailable"}`}
            aria-pressed={selectedTrack === method.id}
            onClick={() => setSelectedTrack(method.id)}
          >
            <span>
              <strong>{method.label}</strong>
              <small>
                {row ? (row.layer < 0 ? row.label : `L${row.layer}`) : "no exact row"}
              </small>
            </span>
            <b>{method.available && value !== undefined ? formatSignedScore(value) : "n/a"}</b>
            <em>
              {method.available ? `${method.signed ? "signed" : "unsigned"} · ${method.evidenceKind.replace("_", " ")}` : "not run"}
            </em>
          </button>
        ))}
      </div>
      {!selectedAttributionMethod.available ? (
        selectedAttributionMethod.id === "integrated_gradients" ? (
          <ActionableEmptyState
            compact
            icon={<Activity size={18} />}
            title="Method output unavailable"
            description={selectedAttributionMethod.unavailableReason ?? "No target-specific attribution output was computed."}
            facts={[
              { label: "Method", value: selectedAttributionMethod.label },
              { label: "Token", value: String(selectedToken) }
            ]}
            actionLabel="Configure Integrated Gradients"
            actionIcon={<Activity size={16} />}
            onAction={() => onConfigureJob("attribution-job")}
          />
        ) : (
          <div className="analysis-empty compact">
            <span className="empty-icon"><AlertTriangle size={18} /></span>
            <strong>Method output unavailable</strong>
            <p>{selectedAttributionMethod.unavailableReason}</p>
          </div>
        )
      ) : (
        <>
          <div className="attribution-selected-value">
            <span>Selected token</span>
            <strong>{explorerRun.tokens[selectedToken].text}</strong>
            <b>{(selectedTrackData.values[selectedToken] ?? 0).toFixed(6)}</b>
            <i>{selectedAttributionMethod.signed ? "signed stored value" : "unsigned proxy"}</i>
          </div>
          <AttributionAccounting
            values={accountingValues}
            signed={selectedAttributionMethod.signed}
            basis={rawAttributionValues ? "raw job values" : "stored method row"}
            selectedToken={selectedToken}
            job={attributionJob}
          />
          <div className="attribution-polarity-lists">
            <AttributionPolarityList
              title="Top positive"
              entries={positiveEntries}
              selectedToken={selectedToken}
              onSelectToken={setSelectedToken}
            />
            {selectedAttributionMethod.signed && (
              <AttributionPolarityList
                title="Top negative"
                entries={negativeEntries}
                selectedToken={selectedToken}
                onSelectToken={setSelectedToken}
              />
            )}
          </div>
          <div className="provenance-note">
            <b>{selectedAttributionMethod.evidenceKind.replace("_", " ")}</b>
            <p>{selectedAttributionMethod.description}</p>
            <span>{selectedAttributionMethod.normalization}</span>
          </div>
        </>
      )}
    </section>
  );
}

function AttributionAccounting({
  values,
  signed,
  basis,
  selectedToken,
  job
}: {
  values: number[];
  signed: boolean;
  basis: string;
  selectedToken: number;
  job?: Record<string, unknown>;
}) {
  const positive = values.reduce((total, value) => total + Math.max(0, value), 0);
  const negative = values.reduce((total, value) => total + Math.min(0, value), 0);
  const net = positive + negative;
  const absolute = positive + Math.abs(negative);
  const cancellation = absolute > 1e-12
    ? Math.max(0, Math.min(1, 1 - Math.abs(net) / absolute))
    : 0;
  const peak = values.reduce((maximum, value) => Math.max(maximum, Math.abs(value)), 0);
  const selectedMagnitude = Math.abs(values[selectedToken] ?? 0);
  const selectedShare = absolute > 1e-12 ? selectedMagnitude / absolute : 0;
  const targetText = typeof job?.targetTokenText === "string"
    ? job.targetTokenText
    : typeof job?.targetTokenId === "number"
      ? `token ${job.targetTokenId}`
      : "not recorded";
  const targetIndex = typeof job?.targetResponseIndex === "number"
    ? `response[${job.targetResponseIndex}]`
    : "response index not recorded";
  const baseline = typeof job?.baseline === "string" ? job.baseline : "not recorded";
  const steps = typeof job?.nSteps === "number" ? String(job.nSteps) : "not recorded";
  const convergence = typeof job?.convergenceDelta === "number"
    ? job.convergenceDelta.toExponential(3)
    : "not recorded";

  return (
    <section className="attribution-accounting" aria-label="Attribution accounting">
      <header>
        <div>
          <strong>Attribution accounting</strong>
          <span>{basis} · {values.length} input positions</span>
        </div>
        <b>{signed ? "signed balance" : "unsigned mass"}</b>
      </header>
      <div className="attribution-accounting-metrics">
        {signed ? (
          <>
            <span><b>{formatAttributionTotal(positive)}</b>positive sum</span>
            <span><b>{formatAttributionTotal(negative)}</b>negative sum</span>
            <span><b>{formatAttributionTotal(net)}</b>net sum</span>
            <span><b>{(cancellation * 100).toFixed(1)}%</b>sign cancellation</span>
          </>
        ) : (
          <>
            <span><b>{formatAttributionTotal(absolute)}</b>stored mass</span>
            <span><b>{formatAttributionTotal(peak)}</b>peak magnitude</span>
            <span><b>{(selectedShare * 100).toFixed(1)}%</b>selected share</span>
            <span><b>none</b>sign semantics</span>
          </>
        )}
      </div>
      {job ? (
        <div className="attribution-objective-context">
          <Crosshair size={16} />
          <span><b>{targetText}</b>{targetIndex}</span>
          <span><b>{baseline}</b>baseline</span>
          <span><b>{steps}</b>integration steps</span>
          <span><b>{convergence}</b>convergence delta</span>
        </div>
      ) : (
        <div className="attribution-objective-context proxy">
          <AlertTriangle size={16} />
          <span>
            <b>No target/baseline contract</b>
            This method is a run-relative diagnostic, not a target-specific completeness attribution.
          </span>
        </div>
      )}
      <p>
        Sum and cancellation are accounting checks within this method. They do not prove completeness,
        causal sufficiency, or comparability with another attribution scale.
      </p>
    </section>
  );
}

function formatAttributionTotal(value: number) {
  const absolute = Math.abs(value);
  return absolute > 0 && absolute < 0.0001
    ? value.toExponential(3)
    : formatSignedScore(value);
}

function AttributionPolarityList({
  title,
  entries,
  selectedToken,
  onSelectToken
}: {
  title: string;
  entries: Array<{ tokenIndex: number; value: number }>;
  selectedToken: number;
  onSelectToken: (token: number) => void;
}) {
  const explorerRun = useExplorerRun();
  return (
    <div className="attribution-polarity-list">
      <span>{title}</span>
      {entries.length > 0 ? entries.map((entry) => (
        <button
          key={entry.tokenIndex}
          className={entry.tokenIndex === selectedToken ? "active" : ""}
          onClick={() => onSelectToken(entry.tokenIndex)}
        >
          <strong>{explorerRun.tokens[entry.tokenIndex].text}</strong>
          <b>{entry.value.toFixed(6)}</b>
        </button>
      )) : <p>No values in this direction.</p>}
    </div>
  );
}

function ResidualEvidence({
  selectedToken,
  selectedLayer,
  setSelectedLayer,
  metric,
  normalization,
  residualCell
}: {
  selectedToken: number;
  selectedLayer: number;
  setSelectedLayer: (layer: number) => void;
  metric: string;
  normalization: NormalizationMode;
  residualCell?: {
    norm: number;
    rawDirection: number;
    riskDirection: number;
    semanticDensity: number;
  };
}) {
  const explorerRun = useExplorerRun();
  const provenance = matrixProvenance(explorerRun, "residual", metric);
  const selectedValue =
    metric === "residual_norm"
      ? normalization === "raw"
        ? residualCell?.norm ?? 0
        : residualCell?.semanticDensity ?? 0
      : normalization === "raw"
        ? residualCell?.rawDirection ?? 0
        : residualCell?.riskDirection ?? 0;
  const logitLensRows = explorerRun.logitLens.filter(
    (row) => row.tokenIndex === selectedToken
  );
  return (
    <section className="surface component-evidence">
      <div className="surface-header">
        <div>
          <h3>Residual evidence</h3>
          <p>layer_{selectedLayer}.resid_post · token {selectedToken}</p>
        </div>
        <Waves size={18} />
      </div>
      <div className="component-metric-grid">
        <span><b>{selectedValue.toFixed(normalization === "raw" ? 6 : 3)}</b>selected metric</span>
        <span><b>{formatScore(residualCell?.riskDirection ?? 0, "residual_direction")}</b>direction alignment</span>
        <span><b>{(residualCell?.norm ?? 0).toFixed(3)}</b>activation norm</span>
      </div>
      <div className="provenance-note">
        <b>{provenance.label}</b>
        <p>{provenance.semantics}</p>
        <span>{provenance.normalization}</span>
      </div>
      <ResidualLogitLens
        rows={logitLensRows}
        selectedLayer={selectedLayer}
        onSelectLayer={setSelectedLayer}
      />
    </section>
  );
}

function MLPEvidence({
  selectedToken,
  selectedLayer,
  neuron
}: {
  selectedToken: number;
  selectedLayer: number;
  neuron?: MLPNeuron;
}) {
  const explorerRun = useExplorerRun();
  const cell = explorerRun.mlpCells.find(
    (item) => item.layer === selectedLayer && item.tokenIndex === selectedToken
  );
  const layerNeurons = explorerRun.mlpNeurons.filter((item) => item.layer === selectedLayer);
  const signedActivation = neuron?.activationsByToken[selectedToken] ?? 0;
  return (
    <section className="surface component-evidence">
      <div className="surface-header">
        <div>
          <h3>MLP activation</h3>
          <p>layer_{selectedLayer}.post · token {selectedToken}</p>
        </div>
        <Layers3 size={18} />
      </div>
      <div className="component-metric-grid">
        <span><b>{signedActivation.toFixed(6)}</b>signed neuron activation</span>
        <span><b>{Math.abs(signedActivation).toFixed(6)}</b>absolute activation</span>
        <span><b>{neuron?.id ?? "none"}</b>selected retained neuron</span>
      </div>
      {neuron && (
        <div className="mlp-polarity-summary">
          <div>
            <span>Top positive tokens</span>
            <p>{neuron.positiveTopTokens.map((index) => explorerRun.tokens[index].text).join(" · ")}</p>
          </div>
          <div>
            <span>Top negative tokens</span>
            <p>{neuron.negativeTopTokens.map((index) => explorerRun.tokens[index].text).join(" · ")}</p>
          </div>
        </div>
      )}
      <div className="provenance-note">
        <b>Raw MLP post activation</b>
        <p>
          Signed activation describes neuron response only; it is not target-logit contribution,
          probe contribution, or causal ablation effect.
        </p>
        <span>layer_{selectedLayer}.post · {layerNeurons.length} retained neurons · aggregate mean |activation| {(cell?.rawValue ?? 0).toFixed(6)}</span>
      </div>
      <div className="ranked-components">
        {layerNeurons.slice(0, 8).map((item) => (
          <span key={item.id} className={item.id === neuron?.id ? "active" : ""}>
            <b>{item.id}</b>
            <i>{(item.activationsByToken[selectedToken] ?? 0).toFixed(4)}</i>
          </span>
        ))}
      </div>
    </section>
  );
}

function EvidenceFilterBar({
  filter,
  setFilter
}: {
  filter: EvidenceFilter;
  setFilter: (filter: EvidenceFilter) => void;
}) {
  const filters: Array<{ id: EvidenceFilter; label: string }> = [
    { id: "top", label: "Top" },
    { id: "neighborhood", label: "Nearby" },
    { id: "all", label: "All" }
  ];

  return (
    <div className="evidence-filter" aria-label="Evidence filter">
      {filters.map((item) => (
        <button
          key={item.id}
          className={filter === item.id ? "active" : ""}
          onClick={() => setFilter(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

function EvidenceTable({
  rows,
  selectedToken,
  onSelectToken,
  scoreTone
}: {
  rows: Array<{ tokenIndex: number; score: number; reason: string }>;
  selectedToken: number;
  onSelectToken: (token: number) => void;
  scoreTone: "attention" | "attention-difference" | "attribution";
}) {
  const explorerRun = useExplorerRun();
  return (
    <div className="evidence-table">
      <div className="evidence-table-head">
        <span>source token</span>
        <span>score</span>
        <span>why it matters</span>
      </div>
      {rows.map((row) => {
        const token = explorerRun.tokens[row.tokenIndex];
        return (
          <button
            key={`${row.tokenIndex}-${row.reason}`}
            className={selectedToken === row.tokenIndex ? "evidence-row selected" : "evidence-row"}
            onClick={() => onSelectToken(row.tokenIndex)}
            style={{ "--score": Math.abs(row.score) } as React.CSSProperties}
          >
            <span className="source-token">{token.text}</span>
            <span className={`score-cell score-${scoreTone} ${row.score < 0 ? "negative" : "positive"}`}>
              <i />
              <b>{scoreTone === "attention-difference"
                ? formatMetricDelta(row.score, "attention_retained_head_difference", "compact")
                : formatScore(row.score, "attention_probability")}</b>
            </span>
            <span className="reason-cell">{row.reason}</span>
          </button>
        );
      })}
    </div>
  );
}

function NLARowCard({ row }: { row: NLARow }) {
  const explorerRun = useExplorerRun();
  const statusUnavailable = row.status === "unavailable";
  return (
    <article className={statusUnavailable ? "nla-card nla-card-muted" : "nla-card"}>
      <div className="nla-card-header">
        <div>
          <strong>{explorerRun.tokens[row.tokenIndex].text}</strong>
          <span>
            L{row.layer} · {row.component}
          </span>
        </div>
        <span className={`status-pill ${statusUnavailable ? "status-warn" : "status-live"}`}>
          {statusUnavailable ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
          {statusUnavailable ? "not run" : "ready"}
        </span>
      </div>
      <p>{nlaSummary(row)}</p>
      <div className="mini-metrics">
        {statusUnavailable ? (
          <span>Qwen/Gemma NLA profiles required</span>
        ) : (
          <>
            <span>cos {formatScore(row.cosine, "nla_cosine")}</span>
            <span>mse {formatScore(row.mse, "nla_mse")}</span>
          </>
        )}
        <span>norm {row.activationNorm.toFixed(1)}</span>
      </div>
      <details className="detail-disclosure">
        <summary>
          <span>Full NLA message</span>
          <ChevronDown size={14} />
        </summary>
        <p>{row.explanation}</p>
      </details>
    </article>
  );
}

function PinnedStrip({
  pinned,
  restorePin,
  availableRunKeys,
  openCompare
}: {
  pinned: PinnedEvidence[];
  restorePin: (evidence: PinnedEvidence) => void;
  availableRunKeys: Set<string>;
  openCompare: () => void;
}) {
  return (
    <section className="pinned-strip">
      <div className="pinned-strip-heading">
        <span><GitCompareArrows size={14} /> Pinned evidence</span>
        <button onClick={openCompare}>Compare all ({pinned.length})</button>
      </div>
      <div className="pinned-strip-items">
        {pinned.map((evidence) => {
          const available = availableRunKeys.has(runKey(evidence));
          return <button
            key={evidence.id}
            disabled={!available}
            title={available ? "Restore evidence context" : "Source run is not loaded"}
            onClick={() => restorePin(evidence)}
          >
            <strong>{evidence.tokenText}</strong>
            <span>{evidence.runId} / {evidence.sampleId}</span>
            <span>
              L{evidence.layer} · {workspaceViewLabel(evidence.view)}
              {evidence.view === "nla" ? ` · ${evidence.component}` : ""}
            </span>
            <span>{metricDisplayLabel(evidence.metric)} {formatMetricNumber(evidence.value, evidence.metric, "compact")}</span>
          </button>;
        })}
      </div>
    </section>
  );
}

function matrixMetricOptions(component: ComponentKind) {
  if (component === "residual") {
    return [
      { id: "residual_direction", label: "Direction alignment" },
      { id: "residual_norm", label: "Activation norm" }
    ];
  }
  if (component === "attention") {
    return [{ id: "attention_concentration", label: "Attention concentration" }];
  }
  return [{ id: "mlp_magnitude", label: "Mean absolute activation" }];
}

function resolveMatrixMetric(component: ComponentKind, requested: string) {
  const options = matrixMetricOptions(component);
  return options.some((option) => option.id === requested) ? requested : options[0].id;
}

function resolveMlpMetric(requested: string) {
  const metrics = [
    "mlp_signed_activation",
    "mlp_absolute_activation",
    "mlp_normalized_activation"
  ];
  return metrics.includes(requested) ? requested : metrics[0];
}

function resolveNlaMetric(requested: string): "cosine" | "mse" | "fve" {
  if (requested === "nla_mse") return "mse";
  if (requested === "nla_fve") return "fve";
  return "cosine";
}

function mlpMetricValue(value: number, maximum: number, metric: string) {
  if (metric === "mlp_absolute_activation") {
    return Math.abs(value);
  }
  if (metric === "mlp_normalized_activation") {
    return Math.abs(value) / Math.max(maximum, 1e-12);
  }
  return value;
}

function mlpMetricLabel(metric: string) {
  if (metric === "mlp_absolute_activation") return "absolute raw activation";
  if (metric === "mlp_normalized_activation") return "normalized activation magnitude";
  return "signed raw activation";
}

function buildInspectorEvidence({
  run,
  view,
  selectedToken,
  selectedSourceToken,
  selectedLayer,
  selectedNlaComponent,
  selectedHead,
  selectedNeuron,
  selectedAttributionMethod,
  metric,
  normalization,
  sourceArtifact
}: {
  run: ExplorerRun;
  view: WorkspaceView;
  selectedToken: number;
  selectedSourceToken: number;
  selectedLayer: number;
  selectedNlaComponent: NLARow["component"];
  selectedHead: AttentionHead;
  selectedNeuron?: MLPNeuron;
  selectedAttributionMethod: AttributionMethod;
  metric: string;
  normalization: NormalizationMode;
  sourceArtifact: string;
}): InspectorEvidence {
  const token = run.tokens[selectedToken] ?? run.tokens[0];
  const residual = run.residualCells.find(
    (cell) => cell.layer === selectedLayer && cell.tokenIndex === selectedToken
  );
  const nla = matchingNla(run.nla, selectedToken, selectedLayer, selectedNlaComponent);
  const attributionRow = selectedAttributionMethod.rows.find(
    (row) => row.layer === selectedLayer
  ) ?? selectedAttributionMethod.rows[0];
  const failure = matchingAnalysisFailure(run.metadata, view, selectedToken, selectedLayer);
  let status: InspectorEvidence["status"] = "available";
  let statusReason = "Exact evidence is available for the selected token and layer.";
  let primaryLabel = "Safety proxy";
  let rawValue = "not stored";
  let displayValue = formatMetricNumber(token.risk, "tokenRisk", "exact");
  let units = "normalized score";
  let cacheKey = `layer_${selectedLayer}.resid_post[${selectedToken}]`;
  let shape = `scalar from [${run.nlaCompatibility.dModel}]`;
  let provenance = run.metricProvenance.tokenRisk;
  const warnings: string[] = [];

  if (view === "overview") {
    warnings.push("Run-relative proxy; it is not a calibrated safety probability or causal effect.");
  }

  if (view === "residual") {
    provenance = matrixProvenance(run, "residual", metric);
    primaryLabel = provenance.label;
    cacheKey = `layer_${selectedLayer}.resid_post[${selectedToken}]`;
    shape = `[${run.nlaCompatibility.dModel}] residual vector`;
    units = metric === "residual_norm" ? "L2 norm" : "projection";
    if (!residual) {
      status = "unavailable";
      statusReason = "No exact residual cell exists for the selected token and layer.";
      rawValue = "n/a";
      displayValue = "n/a";
    } else if (metric === "residual_norm") {
      rawValue = formatMetricNumber(residual.norm, "residual_norm", "exact");
      displayValue = formatMetricNumber(
        normalization === "raw" ? residual.norm : residual.semanticDensity,
        normalization === "raw" ? "residual_norm" : "normalized",
        "exact"
      );
    } else {
      rawValue = formatMetricNumber(residual.rawDirection, "residual_direction", "exact");
      displayValue = formatMetricNumber(
        normalization === "raw" ? residual.rawDirection : residual.riskDirection,
        normalization === "raw" ? "residual_direction" : "normalized",
        "exact"
      );
      warnings.push("Directional alignment is diagnostic projection, not causal contribution.");
    }
  }

  if (view === "attention") {
    provenance = attentionHeadProvenance(selectedHead, run.metricProvenance.attentionHeatmap);
    const value = selectedHead.distributionByToken[selectedToken]?.[selectedSourceToken];
    primaryLabel = selectedHead.difference
      ? "Retained-head probability difference"
      : selectedHead.rollout
        ? "Retained attention rollout"
      : selectedHead.aggregation
        ? attentionAggregationLabel(selectedHead.aggregation)
        : "Attention probability";
    const attentionMetric = attentionHeadMetric(selectedHead);
    rawValue = formatMetricNumber(value, attentionMetric, "exact");
    displayValue = rawValue;
    units = selectedHead.difference
      ? "selected minus baseline probability"
      : selectedHead.rollout
        ? "retained rollout path weight"
      : selectedHead.aggregation === "max"
      ? "maximum retained-head probability"
      : selectedHead.aggregation
        ? "weighted retained-head probability"
        : "softmax probability";
    cacheKey = attentionHeadSourceKey(selectedHead, selectedToken, selectedSourceToken);
    shape = `[${run.tokens.length} × ${run.tokens.length}]`;
    if (value === undefined) {
      status = "unavailable";
      statusReason = "The exact source/destination attention cell is unavailable.";
    } else if (selectedHead.difference) {
      statusReason = `Client-derived ${selectedHead.difference.selectedHeadId} minus ${selectedHead.difference.baselineHeadId} cell.`;
      warnings.push("This signed difference covers two retained artifact heads only and is not causal evidence.");
    } else if (selectedHead.rollout) {
      statusReason = `Client-derived retained-head rollout through L${selectedHead.layer}.`;
      warnings.push("This rollout uses artifact-retained heads only and is not full-model or causal evidence.");
    } else if (selectedHead.aggregation) {
      statusReason = `Client-derived ${selectedHead.aggregation} cell over ${selectedHead.memberHeadIds?.length ?? 0} retained heads.`;
      warnings.push("This aggregate covers retained artifact heads only, not every head in the model.");
    }
    warnings.push("Attention probability is descriptive and must not be read as causal attribution.");
  }

  if (view === "mlp") {
    provenance = run.metricProvenance.mlpNeuronActivation;
    const value = selectedNeuron?.activationsByToken[selectedToken];
    primaryLabel = "MLP activation";
    rawValue = formatMetricNumber(value, "mlp_signed_activation", "exact");
    const displayed = value === undefined
      ? undefined
      : mlpMetricValue(value, selectedNeuron?.maxAbsoluteActivation ?? 1, metric);
    displayValue = formatMetricNumber(displayed, metric, "exact");
    units = metric === "mlp_normalized_activation" ? "normalized magnitude" : "activation";
    cacheKey = selectedNeuron
      ? `layer_${selectedNeuron.layer}.post[${selectedToken},${selectedNeuron.neuron}]`
      : `layer_${selectedLayer}.post[${selectedToken},?]`;
    shape = `[${run.tokens.length} × retained neurons]`;
    if (value === undefined) {
      status = "unavailable";
      statusReason = "No retained neuron strictly matches the selected layer and token.";
    }
    warnings.push("Activation magnitude is not logit contribution, probe contribution, or ablation effect.");
  }

  if (view === "nla") {
    const nlaJob = latestNlaJob(run.metadata);
    provenance = {
      label: "NLA fidelity",
      method: nlaJob
        ? `${String(nlaJob.profile)} AV/AR · ${String(nlaJob.actorRevision)} / ${String(nlaJob.reconstructorRevision)}`
        : "exact NLA decoder reconstruction",
      semantics: "Exact token/layer/component reconstruction fidelity for a compatible profile.",
      normalization: "stored method metric",
      kind: "safety_method"
    };
    const value = metric === "nla_mse" ? nla?.mse : metric === "nla_fve" ? nla?.fve : nla?.cosine;
    primaryLabel = metric === "nla_mse" ? "NLA MSE" : metric === "nla_fve" ? "NLA FVE" : "NLA cosine";
    rawValue = nla?.status === "unavailable" ? "n/a" : formatMetricNumber(value, metric, "exact");
    displayValue = rawValue;
    units = "fidelity metric";
    cacheKey = nla?.source ?? `nla[L${selectedLayer},T${selectedToken}]`;
    shape = "scalar fidelity + explanation";
    const compatible = run.nlaCompatibility.profiles.some((profile) => profile.status === "compatible");
    if (!nla || nla.status === "unavailable") {
      status = compatible ? "not-computed" : "incompatible";
      statusReason = nla?.explanation ?? "No exact NLA result artifact was computed for this cell.";
      warnings.push(nla?.explanation ?? "A compatible NLA artifact is required.");
    } else if (value === undefined) {
      status = "not-computed";
      statusReason = `${primaryLabel} was not stored for this otherwise available NLA row.`;
    }
    if (nlaJob) {
      warnings.push(
        `Exact ${String(nlaJob.profile)} result for L${String(nlaJob.layer)} / ` +
        `${String(nlaJob.component)}; trust_remote_code=${String(nlaJob.trustRemoteCode)}.`
      );
    }
  }

  if (view === "attribution") {
    provenance = selectedAttributionMethod.id === "integrated_gradients" && run.metricProvenance.integratedGradients
      ? run.metricProvenance.integratedGradients
      : {
      label: selectedAttributionMethod.label,
      method: selectedAttributionMethod.id,
      semantics: selectedAttributionMethod.description,
      normalization: selectedAttributionMethod.normalization,
      kind: selectedAttributionMethod.evidenceKind
      };
    const attributionJob = selectedAttributionMethod.id === "integrated_gradients"
      ? latestAttributionJob(run.metadata)
      : undefined;
    const value = attributionRow?.values[selectedToken];
    const rawStored = Array.isArray(attributionJob?.rawValues)
      ? attributionJob.rawValues[selectedToken]
      : undefined;
    const normalized = value === undefined
      ? undefined
      : normalizeAttribution(value, selectedAttributionMethod.rows, selectedAttributionMethod.signed);
    primaryLabel = selectedAttributionMethod.label;
    rawValue = formatMetricNumber(
      typeof rawStored === "number" ? rawStored : value,
      selectedAttributionMethod.id,
      "exact"
    );
    const displayedAttribution = normalization === "raw" ? value : normalized;
    displayValue = formatMetricNumber(
      displayedAttribution,
      normalization === "raw" ? selectedAttributionMethod.id : "normalized",
      "exact"
    );
    units = selectedAttributionMethod.signed ? "signed contribution" : "unsigned proxy";
    cacheKey = attributionRow?.sourceKey ?? `${selectedAttributionMethod.id}[${selectedToken}]`;
    shape = `[${selectedAttributionMethod.rows.length} × ${run.tokens.length}]`;
    if (!selectedAttributionMethod.available) {
      status = "not-computed";
      statusReason = selectedAttributionMethod.unavailableReason ?? "Method output was not computed.";
    } else if (value === undefined) {
      status = "unavailable";
      statusReason = "The selected attribution method has no exact value for this token.";
    }
    if (!selectedAttributionMethod.signed) {
      warnings.push("Unsigned proxy values do not encode positive versus negative causal contribution.");
    }
    if (attributionJob) {
      const target = typeof attributionJob.targetTokenText === "string"
        ? attributionJob.targetTokenText
        : attributionJob.targetTokenId;
      warnings.push(
        `Target: ${String(target)} at response[${String(attributionJob.targetResponseIndex)}]; ` +
        `baseline: ${String(attributionJob.baseline)}; steps: ${String(attributionJob.nSteps)}.`
      );
      if (Array.isArray(attributionJob.responseContextAttributions) && attributionJob.responseContextAttributions.length) {
        warnings.push(
          `${attributionJob.responseContextAttributions.length} preceding response-context token attribution(s) ` +
          "are retained in job metadata but omitted from this prompt-token matrix."
        );
      }
    }
  }

  if (view === "patching") {
    const experiment = run.patching;
    const cell = experiment?.cells.find(
      (candidate) => candidate.layer === selectedLayer && candidate.tokenIndex === selectedToken
    );
    provenance = patchingProvenance(run, metric);
    primaryLabel = provenance.label;
    const value = patchingMetricValue(cell, metric);
    rawValue = formatMetricNumber(cell?.patchedScore, "patching_score", "exact");
    displayValue = formatMetricNumber(value, metric, "exact");
    units = metric === "patching_recovery" ? "percent recovery" : "target-token logit";
    cacheKey = cell?.sourceKey ?? `patching[L${selectedLayer},T${selectedToken}]`;
    shape = experiment ? `[${experiment.layers.length} × ${experiment.positions.length}] causal grid` : "not computed";
    if (!experiment) {
      status = "not-computed";
      statusReason = "This Run does not contain an activation patching experiment.";
    } else if (!cell) {
      status = "not-computed";
      statusReason = "The selected layer/token cell was not included in this patch grid.";
    } else if (metric === "patching_recovery" && cell.recoveryPercentage === null) {
      status = "unavailable";
      statusReason = "Recovery is undefined because clean and corrupted target logits are effectively equal.";
      warnings.push("Use causal effect or patched logit for this experiment; percentage recovery has a near-zero denominator.");
    } else {
      statusReason = "Exact causal evidence from one clean-activation replacement forward pass.";
      warnings.push(
        `Clean logit ${experiment.cleanScore.toFixed(6)}; corrupted logit ${experiment.corruptedScore.toFixed(6)}; ` +
        `patched logit ${cell.patchedScore.toFixed(6)}.`
      );
    }
  }

  if (view === "intervention") {
    const experiment = run.intervention;
    provenance = interventionProvenance(run);
    primaryLabel = provenance.label;
    rawValue = formatMetricNumber(experiment?.steered.targetLogit, "intervention_target_logit", "exact");
    displayValue = formatMetricNumber(experiment?.deltas.targetLogit, "intervention_logit_delta", "exact");
    units = "raw target-token logit delta";
    cacheKey = experiment?.vector.sourceKey ?? `intervention[L${selectedLayer}]`;
    shape = experiment ? `[${experiment.vector.dimension}] normalized steering vector` : "not computed";
    if (!experiment) {
      status = "not-computed";
      statusReason = "This Run does not contain an intervention comparison.";
    } else {
      statusReason = "Exact original-versus-steered delta with matched seed and generation parameters.";
      warnings.push(
        `Original logit ${experiment.original.targetLogit.toFixed(6)}; steered logit ` +
        `${experiment.steered.targetLogit.toFixed(6)}; token edit distance ${experiment.deltas.tokenEditDistance}.`
      );
      warnings.push(experiment.deltas.probeReason);
      if (experiment.deltas.lexicalRisk !== 0) {
        warnings.push("Lexical risk delta is a fixed term-match proxy, not a trained probe score.");
      }
    }
  }

  if (failure) {
    status = "failed";
    statusReason = failure;
    warnings.unshift(failure);
  }
  if (normalization === "normalized" && rawValue !== displayValue && displayValue !== "n/a") {
    warnings.push(`Displayed value uses: ${provenance.normalization}.`);
  }

  const objectContext = view === "attention"
    ? `${attentionHeadLabel(selectedHead)} · source ${selectedSourceToken} → destination ${selectedToken}`
    : view === "mlp"
      ? selectedNeuron?.id ?? "no retained neuron"
      : view === "attribution"
        ? selectedAttributionMethod.label
      : view === "patching"
        ? run.patching?.component ?? "no experiment"
      : view === "intervention"
        ? run.intervention?.component ?? "no experiment"
        : view === "nla"
          ? nla?.component ?? "no exact component"
          : "resid_post";

  return {
    title: token.text || "␠",
    subtitle: `${workspaceViewLabel(view)} · L${selectedLayer} · ${objectContext}`,
    status,
    statusReason,
    primaryLabel,
    primaryValue: displayValue,
    rawValue,
    displayValue,
    units,
    evidenceClass: provenance.kind,
    method: provenance.method,
    normalization: provenance.normalization,
    cacheKey,
    shape,
    sourceArtifact,
    runId: run.runId,
    sampleId: run.sampleId,
    modelName: run.modelName,
    warnings: [...new Set(warnings)],
    reproduction: {
      schema_version: "1.0",
      run_id: run.runId,
      sample_id: run.sampleId,
      model: run.modelName,
      selection: {
        view,
        token: selectedToken,
        source_token: view === "attention" ? selectedSourceToken : undefined,
        layer: selectedLayer,
        nla_component: view === "nla" ? selectedNlaComponent : undefined,
        metric,
        normalization
      },
      evidence: { raw_value: rawValue, display_value: displayValue, units, cache_key: cacheKey },
      provenance
    }
  };
}

function latestAttributionJob(metadata: ExplorerRun["metadata"]) {
  const jobs = metadata?.attributionJobs;
  if (!Array.isArray(jobs) || jobs.length === 0) return undefined;
  const candidate = jobs[jobs.length - 1];
  return candidate && typeof candidate === "object" && !Array.isArray(candidate)
    ? candidate as Record<string, unknown>
    : undefined;
}

function latestNlaJob(metadata: ExplorerRun["metadata"]) {
  const jobs = metadata?.nlaJobs;
  if (!Array.isArray(jobs) || jobs.length === 0) return undefined;
  const candidate = jobs[jobs.length - 1];
  return candidate && typeof candidate === "object" && !Array.isArray(candidate)
    ? candidate as Record<string, unknown>
    : undefined;
}

function normalizeAttribution(
  value: number,
  rows: AttributionMethod["rows"],
  signed: boolean
) {
  const values = rows.flatMap((row) => row.values);
  if (signed) {
    const maximum = Math.max(1e-12, ...values.map((item) => Math.abs(item)));
    return value / maximum;
  }
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  return Math.abs(maximum - minimum) < 1e-12 ? 0 : (value - minimum) / (maximum - minimum);
}

function matchingAnalysisFailure(
  metadata: Record<string, unknown> | undefined,
  view: WorkspaceView,
  token: number,
  layer: number
) {
  const failures = metadata?.analysisFailures;
  if (!Array.isArray(failures)) return undefined;
  const match = failures.find((candidate) => {
    if (!candidate || typeof candidate !== "object") return false;
    const record = candidate as Record<string, unknown>;
    return record.view === view &&
      (record.token === undefined || record.token === token) &&
      (record.layer === undefined || record.layer === layer);
  }) as Record<string, unknown> | undefined;
  return typeof match?.message === "string" ? match.message : undefined;
}

function evidenceProvenance(
  explorerRun: ExplorerRun,
  view: WorkspaceView,
  metric: string
): MetricProvenance {
  if (view === "overview") return explorerRun.metricProvenance.tokenRisk;
  if (view === "residual") return matrixProvenance(explorerRun, "residual", metric);
  if (view === "attention") return explorerRun.metricProvenance.attentionHeatmap;
  if (view === "mlp") return explorerRun.metricProvenance.mlpNeuronActivation;
  if (view === "patching") return patchingProvenance(explorerRun, metric);
  if (view === "intervention") return interventionProvenance(explorerRun);
  return explorerRun.metricProvenance.tokenAttribution ?? explorerRun.metricProvenance.tokenRisk;
}

function matrixCellsForComponent(
  explorerRun: ExplorerRun,
  component: ComponentKind,
  metric: string
) {
  if (component === "attention") {
    return explorerRun.attentionCells.map((cell) => ({
      row: cell.layer,
      column: cell.tokenIndex,
      value: cell.value,
      rawValue: cell.rawValue,
      metric: cell.metric,
      sourceKey: cell.sourceKey
    }));
  }
  if (component === "mlp") {
    return explorerRun.mlpCells.map((cell) => ({
      row: cell.layer,
      column: cell.tokenIndex,
      value: cell.value,
      rawValue: cell.rawValue,
      metric: cell.metric,
      sourceKey: cell.sourceKey
    }));
  }
  return explorerRun.residualCells.map((cell) => ({
    row: cell.layer,
    column: cell.tokenIndex,
    value: metric === "residual_norm" ? cell.semanticDensity : cell.riskDirection,
    rawValue: metric === "residual_norm" ? cell.norm : cell.rawDirection,
    metric:
      metric === "residual_norm"
        ? "residual_l2_norm"
        : "residual_direction_projection",
    sourceKey: `layer_${cell.layer}.resid_post`
  }));
}

function matrixProvenance(
  explorerRun: ExplorerRun,
  component: ComponentKind,
  metric: string
): MetricProvenance {
  if (component === "residual" && metric === "residual_norm") {
    return {
      label: "Residual activation norm",
      method: "L2 norm over the resid_post model dimension",
      semantics: "Raw activation magnitude; high norm does not imply high safety risk.",
      normalization: "min-max over all layer-token residual norms",
      kind: "raw"
    };
  }
  return explorerRun.metricProvenance[heatmapMetricKey(component)];
}

function heatmapMetricKey(component: ComponentKind) {
  if (component === "attention") {
    return "attentionHeatmap";
  }
  if (component === "mlp") {
    return "mlpHeatmap";
  }
  return "residualHeatmap";
}

function topEvidenceTokens(tokens: Array<{ index: number; risk: number }>) {
  return [...tokens]
    .sort((left, right) => right.risk - left.risk)
    .slice(0, 3)
    .map((token) => token.index);
}

function nlaSummary(row: NLARow) {
  if (row.status === "unavailable") {
    return "NLA unavailable for this model. Current real run uses tiny-gpt2; public NLA profiles target Qwen/Gemma.";
  }
  return row.explanation;
}

function metadataText(
  metadata: Record<string, unknown> | undefined,
  key: string,
  fallback: string
) {
  const value = metadata?.[key];
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  return fallback;
}

function filterEvidenceRows(
  rows: Array<{ tokenIndex: number; score: number; reason: string }>,
  selectedToken: number,
  filter: EvidenceFilter
) {
  if (filter === "neighborhood") {
    return rows
      .filter((row) => Math.abs(row.tokenIndex - selectedToken) <= 2)
      .sort((left, right) => right.score - left.score);
  }
  if (filter === "all") {
    return [...rows].sort((left, right) => left.tokenIndex - right.tokenIndex);
  }
  return [...rows].sort((left, right) => right.score - left.score).slice(0, 8);
}

function filterEvidenceRowsByMagnitude(
  rows: Array<{ tokenIndex: number; score: number; reason: string }>,
  selectedToken: number,
  filter: EvidenceFilter
) {
  if (filter === "neighborhood") {
    return rows
      .filter((row) => Math.abs(row.tokenIndex - selectedToken) <= 2)
      .sort((left, right) => Math.abs(right.score) - Math.abs(left.score));
  }
  if (filter === "all") {
    return [...rows].sort((left, right) => left.tokenIndex - right.tokenIndex);
  }
  return [...rows]
    .sort((left, right) => Math.abs(right.score) - Math.abs(left.score))
    .slice(0, 8);
}

function attentionReason(explorerRun: ExplorerRun, tokenIndex: number, selectedToken: number) {
  if (tokenIndex === selectedToken) {
    return "query token";
  }
  if (Math.abs(tokenIndex - selectedToken) <= 2) {
    return "local context";
  }
  if (explorerRun.nla.some((row) => row.tokenIndex === tokenIndex)) {
    return "cached evidence";
  }
  return "attended source";
}

function matchingNla(
  rows: NLARow[],
  tokenIndex: number,
  layer: number,
  component: NLARow["component"]
) {
  return rows.find(
    (row) =>
      row.tokenIndex === tokenIndex &&
      row.layer === layer &&
      row.component === component
  );
}

function componentForView(view: WorkspaceView): ComponentKind {
  if (view === "attention") {
    return "attention";
  }
  if (view === "mlp") {
    return "mlp";
  }
  return "residual";
}

function selectionContextSummary({
  view,
  tokenText,
  tokenIndex,
  sourceTokenIndex,
  tokenRange,
  layer,
  metric,
  normalization,
  headId,
  neuronId,
  nlaComponent,
  attributionMethod,
  attentionEdgeMode
}: {
  view: WorkspaceView;
  tokenText: string;
  tokenIndex: number;
  sourceTokenIndex: number;
  tokenRange?: [number, number];
  layer: number;
  metric: string;
  normalization: NormalizationMode;
  headId: string;
  neuronId?: string;
  nlaComponent: NLARow["component"];
  attributionMethod: string;
  attentionEdgeMode: "incoming" | "outgoing";
}) {
  const compactToken = tokenText.replace(/\s+/g, " ").trim() || "whitespace";
  const tokenLabel = compactToken.length > 18
    ? `${compactToken.slice(0, 17)}…`
    : compactToken;
  const metricLabel = metric.replace(/_/g, " ");
  const location = tokenRange
    ? `tokens ${tokenRange[0]}–${tokenRange[1]}`
    : view === "attention"
      ? `${sourceTokenIndex} → ${tokenIndex} “${tokenLabel}”`
      : `token ${tokenIndex} “${tokenLabel}”`;
  const object = view === "attention"
    ? `${headId} · ${attentionEdgeMode} · ${metricLabel}`
    : view === "mlp"
      ? `${neuronId ?? "no retained neuron"} · ${metricLabel}`
      : view === "nla"
        ? `${nlaComponent} · ${metricLabel}`
        : view === "attribution"
          ? attributionMethod
          : metricLabel;
  return {
    signature: [
      view,
      tokenIndex,
      sourceTokenIndex,
      tokenRange?.join("-") ?? "",
      layer,
      metric,
      normalization,
      view === "attention" ? `${headId}:${attentionEdgeMode}` : "",
      view === "mlp" ? neuronId ?? "" : "",
      view === "nla" ? nlaComponent : "",
      view === "attribution" ? attributionMethod : ""
    ].join("|"),
    message: `${workspaceViewLabel(view)} · L${layer} · ${location} · ${object} · ${normalization}`
  };
}

function workspaceViewLabel(view: WorkspaceView) {
  const labels: Record<WorkspaceView, string> = {
    overview: "Overview",
    residual: "Residual",
    attention: "Attention",
    mlp: "MLP",
    nla: "NLA",
    patching: "Patching",
    intervention: "Intervention",
    attribution: "Attribution"
  };
  return labels[view];
}

function buildInspectorNextActions(
  view: WorkspaceView,
  evidence: InspectorEvidence
): InspectorNextAction[] {
  if (evidence.status === "loading" || evidence.status === "cancelled") return [];
  const actions: InspectorNextAction[] = [];
  const add = (action: InspectorNextAction) => {
    if (!actions.some((candidate) => candidate.id === action.id)) actions.push(action);
  };
  const gap = evidence.status !== "available";

  if (gap && view === "attribution") {
    add({
      id: "configure_attribution",
      kind: "attribution",
      label: "Configure Integrated Gradients",
      description: "Choose a response target, baseline, and integration steps."
    });
  } else if (gap && view === "nla") {
    add({
      id: "configure_nla",
      kind: "nla",
      label: "Configure NLA job",
      description: "Check profile compatibility and compute an exact explanation."
    });
  } else if (gap && view === "patching") {
    add({
      id: "configure_patching",
      kind: "patching",
      label: "Configure causal patching",
      description: "Select a changed prompt, component, layer, and target."
    });
  } else if (gap && view === "intervention") {
    add({
      id: "configure_intervention",
      kind: "intervention",
      label: "Configure intervention",
      description: "Define the contrast, scale, position range, and generation target."
    });
  } else if (gap) {
    add(overviewInspectorAction());
  }

  if (evidence.evidenceClass === "causal") {
    if (view !== "intervention") {
      add({
        id: "open_intervention",
        kind: "intervention",
        label: "Open intervention comparison",
        description: "Inspect whether a controlled steering change alters generation."
      });
    }
    if (view !== "overview") add(overviewInspectorAction());
    if (view !== "attribution") add(attributionInspectorAction());
  } else {
    if (view !== "patching") add(patchingInspectorAction());
    if (view !== "attribution") add(attributionInspectorAction());
    if (view !== "nla") add(nlaInspectorAction());
    if (view !== "overview") add(overviewInspectorAction());
  }
  return actions.slice(0, 3);
}

function patchingInspectorAction(): InspectorNextAction {
  return {
    id: "open_patching",
    kind: "patching",
    label: "Run causal patching",
    description: "Measure a replacement effect instead of inferring causality from a proxy."
  };
}

function attributionInspectorAction(): InspectorNextAction {
  return {
    id: "open_attribution",
    kind: "attribution",
    label: "Open target attribution",
    description: "Inspect signed or target-specific token evidence."
  };
}

function nlaInspectorAction(): InspectorNextAction {
  return {
    id: "open_nla",
    kind: "nla",
    label: "Open exact NLA",
    description: "Check activation explanation, compatibility, and decoder fidelity."
  };
}

function overviewInspectorAction(): InspectorNextAction {
  return {
    id: "open_overview",
    kind: "overview",
    label: "Return to evidence map",
    description: "Review available, supporting, and contradictory evidence together."
  };
}

function inspectorActionTarget(actionId: string): { view: WorkspaceView; anchorId?: string } | undefined {
  if (actionId === "configure_attribution" || actionId === "open_attribution") {
    return { view: "attribution", anchorId: "attribution-job" };
  }
  if (actionId === "configure_nla" || actionId === "open_nla") {
    return { view: "nla", anchorId: "nla-job" };
  }
  if (actionId === "configure_patching" || actionId === "open_patching") {
    return { view: "patching", anchorId: "patching-job" };
  }
  if (actionId === "configure_intervention" || actionId === "open_intervention") {
    return { view: "intervention", anchorId: "intervention-job" };
  }
  if (actionId === "open_overview") return { view: "overview" };
  return undefined;
}

function focusElementWhenAvailable(id: string, attempts = 40) {
  const element = document.getElementById(id);
  if (element) {
    element.scrollIntoView({ block: "start" });
    element.focus({ preventScroll: true });
    return;
  }
  if (attempts > 1) {
    window.setTimeout(() => focusElementWhenAvailable(id, attempts - 1), 25);
  }
}

function sanitizeSessionSelection(
  session: ExplorerSession,
  run: ExplorerRun,
  current: ExplorerSelectionState
): ExplorerSelectionState {
  const tokenIndices = new Set(run.tokens.map((token) => token.index));
  const requestedTarget = session.selection.targetTokenIndex ?? session.selection.tokenIndex;
  const tokenIndex = tokenIndices.has(requestedTarget)
    ? requestedTarget
    : tokenIndices.has(session.selection.tokenIndex)
      ? session.selection.tokenIndex
      : run.tokens[0]?.index ?? current.tokenIndex;
  const requestedSource = session.selection.sourceTokenIndex ?? tokenIndex;
  const sourceTokenIndex = tokenIndices.has(requestedSource)
    ? Math.min(requestedSource, tokenIndex)
    : tokenIndex;
  const layer = run.layers.includes(session.selection.layer)
    ? session.selection.layer
    : run.layers[run.layers.length - 1] ?? current.layer;
  const requestedRange = session.selection.tokenRange;
  const tokenRange = requestedRange && tokenIndices.has(requestedRange[0]) && tokenIndices.has(requestedRange[1])
    ? ([Math.min(...requestedRange), Math.max(...requestedRange)] as [number, number])
    : undefined;
  const layerHeads = run.attentionHeads.filter((head) => head.layer === layer);
  const layerNeurons = run.mlpNeurons.filter((neuron) => neuron.layer === layer);
  const availableTracks = run.attributionMethods.filter((method) => method.available);
  const trackName = run.attributionMethods.some((method) => method.id === session.selection.trackName)
    ? session.selection.trackName
    : availableTracks[0]?.id ?? current.trackName;

  return {
    ...session.selection,
    tokenIndex,
    sourceTokenIndex,
    targetTokenIndex: tokenIndex,
    tokenRange,
    layer,
    headId: layerHeads.some((head) => head.id === session.selection.headId) ||
      Boolean(parseAttentionAggregation(session.selection.headId)) ||
      Boolean(parseAttentionRollout(session.selection.headId)) ||
      isAttentionDifferenceAvailable(layerHeads, session.selection.headId)
      ? session.selection.headId
      : layerHeads[0]?.id ?? current.headId,
    attentionEdgeMode: session.selection.attentionEdgeMode ?? "incoming",
    nlaComponent: session.selection.nlaComponent ?? current.nlaComponent,
    neuronId: layerNeurons.some((neuron) => neuron.id === session.selection.neuronId)
      ? session.selection.neuronId
      : layerNeurons[0]?.id ?? current.neuronId,
    trackName,
    metric: session.selection.view === "attribution" && session.selection.metric === session.selection.trackName
      ? trackName
      : session.selection.metric,
    pinnedItems: session.pinnedItems.slice(-4)
  };
}

function sanitizeSessionTimeline(session: ExplorerSession, run: ExplorerRun): TimelineState {
  const requested = session.timeline ?? { mode: "token", metric: "risk", query: "" };
  return {
    mode: requested.mode,
    metric: requested.metric === "probe" && !run.tokens.some((token) => token.probeScore !== undefined)
      ? "risk"
      : requested.metric,
    query: requested.query.slice(0, 256)
  };
}

const matrixViewportSizeBounds: Record<MatrixViewportKey, readonly [number, number]> = {
  residual: [10, 34],
  attention: [14, 36],
  mlp: [20, 42],
  attribution: [14, 38],
  nla: [14, 38],
  patching: [32, 64]
};

function sanitizeSessionMatrixViewports(
  requested: MatrixViewportSnapshots | undefined
): MatrixViewportSnapshots {
  if (!requested) return {};
  const sanitized: MatrixViewportSnapshots = {};
  for (const key of Object.keys(matrixViewportSizeBounds) as MatrixViewportKey[]) {
    const snapshot = requested[key];
    if (!snapshot) continue;
    const [minimum, maximum] = matrixViewportSizeBounds[key];
    sanitized[key] = {
      ...snapshot,
      size: Math.max(minimum, Math.min(maximum, snapshot.size))
    } satisfies MatrixViewportSnapshot;
  }
  return sanitized;
}

function resolvePatchingMetric(metric: string): PatchingMetric {
  if (metric === "patching_effect") return "effect";
  if (metric === "patching_score") return "score";
  return "recovery";
}

function patchingMetricValue(
  cell: ExplorerRun["patching"] extends infer _P ? NonNullable<ExplorerRun["patching"]>["cells"][number] | undefined : never,
  metric: string
) {
  if (!cell) return undefined;
  if (metric === "patching_effect") return cell.causalEffect;
  if (metric === "patching_score") return cell.patchedScore;
  return cell.recoveryPercentage;
}

function patchingProvenance(run: ExplorerRun, metric: string): MetricProvenance {
  const key = metric === "patching_effect"
    ? "patchingCausalEffect"
    : metric === "patching_score"
      ? "patchingPatchedScore"
      : "patchingRecovery";
  return run.metricProvenance[key] ?? {
    label: "Activation patching",
    method: "clean activation replacement",
    semantics: "Causal target-logit response to one activation replacement.",
    normalization: "none",
    kind: "causal"
  };
}

function interventionProvenance(run: ExplorerRun): MetricProvenance {
  return run.metricProvenance.interventionTargetLogitDelta ?? {
    label: "Target logit delta",
    method: "normalized contrastive activation steering",
    semantics: "Steered target-token logit minus the original target-token logit.",
    normalization: "none; raw logit difference",
    kind: "causal"
  };
}

const MAX_PIN_PROFILE_POINTS = 256;
const MAX_PIN_MATRIX_AXIS = 64;

function buildAttentionMatrixSnapshot(
  head: AttentionHead,
  tokens: ExplorerRun["tokens"],
  selectedSourceToken: number,
  selectedDestinationToken: number
): AttentionMatrixSnapshot | undefined {
  if (tokens.length === 0) return undefined;
  const axis = sampleTokenAxis(
    tokens,
    [selectedSourceToken, selectedDestinationToken],
    MAX_PIN_MATRIX_AXIS
  ).map((token) => ({
    tokenIndex: token.index,
    tokenId: token.tokenId,
    tokenText: token.text
  }));
  const values = axis.map((destination) => axis.map((source) => {
    if (source.tokenIndex > destination.tokenIndex) return null;
    const value = head.distributionByToken[destination.tokenIndex]?.[source.tokenIndex];
    return Number.isFinite(value) && value !== undefined && value >= 0 && value <= 1
      ? value
      : null;
  }));
  const complete = values.every((row, destination) => row.every((value, source) =>
    axis[source].tokenIndex > axis[destination].tokenIndex || value !== null
  ));
  if (!complete) return undefined;
  return {
    schemaVersion: "1.0",
    kind: "attention_matrix",
    label: `${attentionHeadLabel(head)} · ${tokens.length}×${tokens.length}`,
    originalSize: tokens.length,
    sampled: axis.length < tokens.length,
    axis,
    values
  };
}

function sampleTokenAxis(
  tokens: ExplorerRun["tokens"],
  preserveTokenIndices: number[],
  limit: number
) {
  if (tokens.length <= limit) return tokens;
  const sampledIndices = new Set<number>();
  for (let index = 0; index < limit; index += 1) {
    sampledIndices.add(Math.round(index * (tokens.length - 1) / (limit - 1)));
  }
  const protectedIndices = new Set([0, tokens.length - 1]);
  for (const tokenIndex of preserveTokenIndices) {
    const preservedPosition = tokens.findIndex((token) => token.index === tokenIndex);
    if (preservedPosition < 0) continue;
    protectedIndices.add(preservedPosition);
    if (sampledIndices.has(preservedPosition)) continue;
    const replaceablePosition = [...sampledIndices]
      .filter((position) => !protectedIndices.has(position))
      .sort((left, right) =>
        Math.abs(left - preservedPosition) - Math.abs(right - preservedPosition)
      )[0];
    if (replaceablePosition !== undefined) sampledIndices.delete(replaceablePosition);
    sampledIndices.add(preservedPosition);
  }
  return [...sampledIndices]
    .sort((left, right) => left - right)
    .map((position) => tokens[position]);
}

function buildEvidenceProfile({
  kind,
  label,
  axis,
  signed,
  tokens,
  values,
  preserveTokenIndex
}: {
  kind: EvidenceProfileSnapshot["kind"];
  label: string;
  axis: EvidenceProfileSnapshot["axis"];
  signed: boolean;
  tokens: ExplorerRun["tokens"];
  values: number[];
  preserveTokenIndex: number;
}): EvidenceProfileSnapshot | undefined {
  const allPoints = tokens.flatMap((token) => {
    const value = values[token.index];
    return Number.isFinite(value)
      ? [{ tokenIndex: token.index, tokenId: token.tokenId, tokenText: token.text, value }]
      : [];
  });
  if (allPoints.length === 0) return undefined;

  let points = allPoints;
  if (allPoints.length > MAX_PIN_PROFILE_POINTS) {
    const sampledIndices = new Set<number>();
    for (let index = 0; index < MAX_PIN_PROFILE_POINTS; index += 1) {
      sampledIndices.add(Math.round(index * (allPoints.length - 1) / (MAX_PIN_PROFILE_POINTS - 1)));
    }
    const preservedIndex = allPoints.findIndex((point) => point.tokenIndex === preserveTokenIndex);
    if (preservedIndex >= 0 && !sampledIndices.has(preservedIndex)) {
      const replaceableIndex = [...sampledIndices]
        .filter((index) => index !== 0 && index !== allPoints.length - 1)
        .sort((left, right) =>
          Math.abs(left - preservedIndex) - Math.abs(right - preservedIndex)
        )[0];
      if (replaceableIndex !== undefined) sampledIndices.delete(replaceableIndex);
      sampledIndices.add(preservedIndex);
    }
    points = [...sampledIndices]
      .sort((left, right) => left - right)
      .map((index) => allPoints[index]);
  }

  return {
    schemaVersion: "1.0",
    kind,
    label,
    axis,
    signed,
    originalLength: allPoints.length,
    sampled: points.length < allPoints.length,
    points
  };
}

function componentLabel(component: ComponentKind) {
  if (component === "attention") {
    return "attention head";
  }
  if (component === "mlp") {
    return "MLP layer neuron";
  }
  return "residual stream output";
}

function selectionComponentLabel(
  component: ComponentKind,
  head: AttentionHead,
  neuron?: MLPNeuron
) {
  if (component === "attention") {
    return attentionHeadLabel(head);
  }
  if (component === "mlp") {
    return neuron?.id ?? "MLP";
  }
  return "resid_post";
}

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
