import { useEffect, useReducer, useRef } from "react";

import type {
  ExplorerSelectionState,
  AttentionEdgeMode,
  NLARow,
  NormalizationMode,
  PinnedEvidence,
  WorkspaceView
} from "../types";

const STORAGE_KEY = "safelens.localExplorer.pinnedEvidence.v2";

interface SelectionDefaults {
  runId: string;
  sampleId: string;
  tokenIndex: number;
  tokenIndices: number[];
  layers: number[];
  layer: number;
  view: WorkspaceView;
  headId: string;
  nlaComponent: NLARow["component"];
  neuronId: string;
  trackName: string;
  metric: string;
  initialPinnedItems?: PinnedEvidence[];
}

type SelectionAction =
  | { type: "select_token"; tokenIndex: number }
  | { type: "select_source_token"; tokenIndex: number }
  | { type: "select_attention_pair"; sourceTokenIndex: number; targetTokenIndex: number }
  | { type: "select_range"; tokenRange?: [number, number] }
  | { type: "select_layer"; layer: number }
  | { type: "select_view"; view: WorkspaceView }
  | { type: "select_head"; headId: string }
  | { type: "select_attention_edge_mode"; mode: AttentionEdgeMode }
  | { type: "select_nla_component"; component: NLARow["component"] }
  | { type: "select_neuron"; neuronId: string }
  | { type: "select_track"; trackName: string }
  | { type: "select_metric"; metric: string }
  | { type: "set_normalization"; normalization: NormalizationMode }
  | { type: "toggle_pin"; evidence: PinnedEvidence }
  | { type: "restore_pin"; evidence: PinnedEvidence }
  | { type: "restore_session"; selection: ExplorerSelectionState }
  | { type: "restore_url"; selection: ExplorerSelectionState };

type HistoryMode = "push" | "replace";

const VIEWS: WorkspaceView[] = [
  "overview",
  "residual",
  "attention",
  "mlp",
  "nla",
  "patching",
  "intervention",
  "attribution"
];

function selectionReducer(
  state: ExplorerSelectionState,
  action: SelectionAction
): ExplorerSelectionState {
  switch (action.type) {
    case "select_token":
      return {
        ...state,
        tokenIndex: action.tokenIndex,
        sourceTokenIndex: Math.min(state.sourceTokenIndex ?? action.tokenIndex, action.tokenIndex),
        targetTokenIndex: action.tokenIndex,
        tokenRange: undefined
      };
    case "select_source_token":
      return {
        ...state,
        sourceTokenIndex: Math.min(action.tokenIndex, state.targetTokenIndex ?? state.tokenIndex)
      };
    case "select_attention_pair":
      return {
        ...state,
        tokenIndex: action.targetTokenIndex,
        sourceTokenIndex: action.sourceTokenIndex,
        targetTokenIndex: action.targetTokenIndex,
        tokenRange: undefined
      };
    case "select_range":
      return { ...state, tokenRange: action.tokenRange };
    case "select_layer":
      return { ...state, layer: action.layer };
    case "select_view":
      return {
        ...state,
        view: action.view,
        metric: defaultMetric(action.view, state.trackName),
        normalization:
          action.view === "attention" || action.view === "mlp" || action.view === "attribution" || action.view === "intervention"
            ? "raw"
            : state.normalization
      };
    case "select_head":
      return { ...state, headId: action.headId };
    case "select_attention_edge_mode":
      return { ...state, attentionEdgeMode: action.mode };
    case "select_nla_component":
      return { ...state, nlaComponent: action.component };
    case "select_neuron":
      return { ...state, neuronId: action.neuronId };
    case "select_track":
      return {
        ...state,
        trackName: action.trackName,
        metric: state.view === "attribution" ? action.trackName : state.metric
      };
    case "select_metric":
      return { ...state, metric: action.metric };
    case "set_normalization":
      return { ...state, normalization: action.normalization };
    case "toggle_pin": {
      const exists = state.pinnedItems.some((item) => item.id === action.evidence.id);
      return {
        ...state,
        pinnedItems: exists
          ? state.pinnedItems.filter((item) => item.id !== action.evidence.id)
          : [...state.pinnedItems, action.evidence].slice(-4)
      };
    }
    case "restore_pin":
      return {
        ...state,
        tokenIndex: action.evidence.tokenIndex,
        sourceTokenIndex: action.evidence.sourceTokenIndex ?? state.sourceTokenIndex,
        targetTokenIndex: action.evidence.tokenIndex,
        tokenRange: undefined,
        layer: action.evidence.layer,
        view: action.evidence.view,
        headId: action.evidence.headId ?? state.headId,
        nlaComponent:
          action.evidence.view === "nla" && isNlaComponent(action.evidence.component)
            ? action.evidence.component
            : state.nlaComponent,
        neuronId: action.evidence.neuronId ?? state.neuronId,
        trackName:
          action.evidence.trackName ??
          (action.evidence.view === "attribution" ? action.evidence.metric : state.trackName),
        metric: action.evidence.metric,
        normalization: action.evidence.normalization
      };
    case "restore_session":
    case "restore_url":
      return action.selection;
  }
}

function initialSelection(defaults: SelectionDefaults): ExplorerSelectionState {
  return selectionFromLocation(defaults, loadPinnedItems(defaults));
}

function selectionFromLocation(
  defaults: SelectionDefaults,
  pinnedItems: PinnedEvidence[]
): ExplorerSelectionState {
  const params = new URLSearchParams(window.location.search);
  const requestedView = params.get("view") ?? params.get("mode");
  const requestedToken = parseInteger(params.get("token"));
  const requestedSource = parseInteger(params.get("source"));
  const requestedTarget = parseInteger(params.get("target"));
  const requestedLayer = parseInteger(params.get("layer"));
  const requestedNormalization = params.get("normalization");
  const requestedRange = parseRange(params.get("range"));
  const requestedEdgeMode = params.get("edge");
  const requestedNlaComponent = params.get("nlaComponent");
  const selectedView = VIEWS.includes(requestedView as WorkspaceView)
    ? (requestedView as WorkspaceView)
    : defaults.view;
  const selectedTrack = params.get("track") ?? defaults.trackName;
  const selectedToken =
    requestedTarget !== undefined && defaults.tokenIndices.includes(requestedTarget)
      ? requestedTarget
      : requestedToken !== undefined && defaults.tokenIndices.includes(requestedToken)
        ? requestedToken
        : defaults.tokenIndex;
  const selectedSource =
    requestedSource !== undefined && defaults.tokenIndices.includes(requestedSource)
      ? requestedSource
      : selectedToken;
  const selectedRange = requestedRange &&
    defaults.tokenIndices.includes(requestedRange[0]) &&
    defaults.tokenIndices.includes(requestedRange[1])
      ? requestedRange
      : undefined;

  return {
    view: selectedView,
    tokenIndex: selectedToken,
    sourceTokenIndex: Math.min(selectedSource, selectedToken),
    targetTokenIndex: selectedToken,
    tokenRange: selectedRange,
    layer:
      requestedLayer !== undefined && defaults.layers.includes(requestedLayer)
        ? requestedLayer
        : defaults.layer,
    headId: params.get("head") ?? defaults.headId,
    attentionEdgeMode: requestedEdgeMode === "outgoing" ? "outgoing" : "incoming",
    nlaComponent: isNlaComponent(requestedNlaComponent)
      ? requestedNlaComponent
      : defaults.nlaComponent,
    neuronId: params.get("neuron") ?? defaults.neuronId,
    trackName: selectedTrack,
    metric: params.get("metric") ?? defaultMetric(selectedView, selectedTrack),
    normalization:
      requestedNormalization === "raw" || requestedNormalization === "normalized"
        ? requestedNormalization
        : selectedView === "attention" || selectedView === "intervention"
          ? "raw"
          : "normalized",
    pinnedItems
  };
}

export function useExplorerSelection(defaults: SelectionDefaults) {
  const [state, dispatch] = useReducer(selectionReducer, defaults, initialSelection);
  const defaultsRef = useRef(defaults);
  const pinnedItemsRef = useRef(state.pinnedItems);
  const historyModeRef = useRef<HistoryMode>("replace");
  defaultsRef.current = defaults;
  pinnedItemsRef.current = state.pinnedItems;

  function dispatchWithHistory(action: SelectionAction, historyMode: HistoryMode = "push") {
    historyModeRef.current = historyMode;
    dispatch(action);
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requestedRun = params.get("run");
    const requestedSample = params.get("sample");
    if (
      (requestedRun && requestedRun !== defaults.runId) ||
      (requestedSample && requestedSample !== defaults.sampleId)
    ) {
      return;
    }
    params.set("view", state.view);
    params.set("token", String(state.tokenIndex));
    params.set("layer", String(state.layer));
    params.set("normalization", state.normalization);
    if (state.headId) {
      params.set("head", state.headId);
    }
    if (state.neuronId) {
      params.set("neuron", state.neuronId);
    }
    if (state.trackName) {
      params.set("track", state.trackName);
    }
    if (state.metric) {
      params.set("metric", state.metric);
    }
    if (state.tokenRange) {
      params.set("range", `${state.tokenRange[0]}-${state.tokenRange[1]}`);
    } else {
      params.delete("range");
    }
    if (state.view === "attention") {
      params.set("source", String(state.sourceTokenIndex ?? state.tokenIndex));
      params.set("target", String(state.targetTokenIndex ?? state.tokenIndex));
      params.set("edge", state.attentionEdgeMode);
    } else {
      params.delete("source");
      params.delete("target");
      params.delete("edge");
    }
    if (state.view === "nla") {
      params.set("nlaComponent", state.nlaComponent);
    } else {
      params.delete("nlaComponent");
    }
    params.delete("mode");
    const nextLocation = `${window.location.pathname}?${params.toString()}${window.location.hash}`;
    const currentLocation = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    const historyMode = historyModeRef.current;
    historyModeRef.current = "replace";
    if (nextLocation === currentLocation) return;
    if (historyMode === "push") {
      window.history.pushState(window.history.state, "", nextLocation);
    } else {
      window.history.replaceState(window.history.state, "", nextLocation);
    }
  }, [defaults.runId, defaults.sampleId, state.attentionEdgeMode, state.headId, state.layer, state.metric, state.neuronId, state.nlaComponent, state.normalization, state.sourceTokenIndex, state.targetTokenIndex, state.tokenIndex, state.tokenRange, state.trackName, state.view]);

  useEffect(() => {
    function restoreSelectionFromHistory() {
      const currentDefaults = defaultsRef.current;
      const params = new URLSearchParams(window.location.search);
      const requestedRun = params.get("run");
      const requestedSample = params.get("sample");
      if (
        (requestedRun && requestedRun !== currentDefaults.runId) ||
        (requestedSample && requestedSample !== currentDefaults.sampleId)
      ) {
        return;
      }
      historyModeRef.current = "replace";
      dispatch({
        type: "restore_url",
        selection: selectionFromLocation(currentDefaults, pinnedItemsRef.current)
      });
    }

    window.addEventListener("popstate", restoreSelectionFromHistory);
    return () => window.removeEventListener("popstate", restoreSelectionFromHistory);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.pinnedItems));
  }, [state.pinnedItems]);

  return {
    state,
    selectToken: (tokenIndex: number, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_token", tokenIndex }, historyMode),
    selectSourceToken: (tokenIndex: number, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_source_token", tokenIndex }, historyMode),
    selectAttentionPair: (
      sourceTokenIndex: number,
      targetTokenIndex: number,
      historyMode?: HistoryMode
    ) => dispatchWithHistory(
      { type: "select_attention_pair", sourceTokenIndex, targetTokenIndex },
      historyMode
    ),
    selectRange: (tokenRange?: [number, number], historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_range", tokenRange }, historyMode),
    selectLayer: (layer: number, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_layer", layer }, historyMode),
    selectView: (view: WorkspaceView, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_view", view }, historyMode),
    selectHead: (headId: string, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_head", headId }, historyMode),
    selectAttentionEdgeMode: (mode: AttentionEdgeMode, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_attention_edge_mode", mode }, historyMode),
    selectNlaComponent: (component: NLARow["component"], historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_nla_component", component }, historyMode),
    selectNeuron: (neuronId: string, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_neuron", neuronId }, historyMode),
    selectTrack: (trackName: string, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_track", trackName }, historyMode),
    selectMetric: (metric: string, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "select_metric", metric }, historyMode),
    setNormalization: (normalization: NormalizationMode, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "set_normalization", normalization }, historyMode),
    togglePin: (evidence: PinnedEvidence) => dispatch({ type: "toggle_pin", evidence }),
    restorePin: (evidence: PinnedEvidence, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "restore_pin", evidence }, historyMode),
    restoreSession: (selection: ExplorerSelectionState, historyMode?: HistoryMode) =>
      dispatchWithHistory({ type: "restore_session", selection }, historyMode)
  };
}

function isNlaComponent(value: string | null): value is NLARow["component"] {
  return value === "resid_post" || value === "attn_result" || value === "mlp_out";
}

function defaultMetric(view: WorkspaceView, trackName: string) {
  if (view === "residual") return "residual_direction";
  if (view === "attention") return "attention_probability";
  if (view === "mlp") return "mlp_signed_activation";
  if (view === "nla") return "nla_cosine";
  if (view === "patching") return "patching_recovery";
  if (view === "intervention") return "intervention_logit_delta";
  if (view === "attribution") return trackName;
  return "tokenRisk";
}

function parseInteger(value: string | null) {
  if (value === null || !/^\d+$/.test(value)) {
    return undefined;
  }
  return Number(value);
}

function parseRange(value: string | null): [number, number] | undefined {
  const match = value?.match(/^(\d+)-(\d+)$/);
  if (!match) {
    return undefined;
  }
  const start = Number(match[1]);
  const end = Number(match[2]);
  return start <= end ? [start, end] : [end, start];
}

function loadPinnedItems(defaults: SelectionDefaults) {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
    if (!Array.isArray(parsed)) {
      return defaults.initialPinnedItems ?? [];
    }
    const valid = parsed.filter(isPinnedEvidence);
    return valid.length > 0 ? valid.slice(-4) : defaults.initialPinnedItems ?? [];
  } catch {
    return defaults.initialPinnedItems ?? [];
  }
}

function isPinnedEvidence(item: unknown): item is PinnedEvidence {
  if (!item || typeof item !== "object") return false;
  const candidate = item as Partial<PinnedEvidence>;
  return typeof candidate.id === "string" &&
    typeof candidate.runId === "string" &&
    typeof candidate.sampleId === "string" &&
    Number.isInteger(candidate.tokenIndex) &&
    typeof candidate.tokenText === "string" &&
    Number.isInteger(candidate.layer) &&
    typeof candidate.view === "string" &&
    typeof candidate.metric === "string" &&
    typeof candidate.value === "number" &&
    (candidate.normalization === "raw" || candidate.normalization === "normalized") &&
    (candidate.profile === undefined || isEvidenceProfile(candidate.profile)) &&
    (candidate.matrix === undefined || isAttentionMatrix(candidate.matrix, candidate)) &&
    (candidate.generation === undefined || isInterventionGeneration(candidate.generation));
}

function isEvidenceProfile(profile: unknown) {
  if (!profile || typeof profile !== "object") return false;
  const candidate = profile as NonNullable<PinnedEvidence["profile"]>;
  if (
    candidate.schemaVersion !== "1.0" ||
    (
      candidate.kind !== "attention_source_profile" &&
      candidate.kind !== "signed_attribution_profile" &&
      candidate.kind !== "mlp_activation_profile"
    ) ||
    (candidate.axis !== "source_token" && candidate.axis !== "token") ||
    typeof candidate.label !== "string" ||
    typeof candidate.signed !== "boolean" ||
    !Number.isInteger(candidate.originalLength) ||
    candidate.originalLength < 1 ||
    typeof candidate.sampled !== "boolean" ||
    !Array.isArray(candidate.points) ||
    candidate.points.length < 1 ||
    candidate.points.length > 256 ||
    candidate.originalLength < candidate.points.length ||
    (candidate.sampled === (candidate.originalLength === candidate.points.length))
  ) {
    return false;
  }
  return candidate.points.every((point) =>
    point !== null &&
    typeof point === "object" &&
    Number.isInteger(point.tokenIndex) &&
    point.tokenIndex >= 0 &&
    (point.tokenId === undefined || Number.isInteger(point.tokenId)) &&
    typeof point.tokenText === "string" &&
    Number.isFinite(point.value)
  );
}

function isInterventionGeneration(generation: unknown) {
  if (!generation || typeof generation !== "object") return false;
  const candidate = generation as NonNullable<PinnedEvidence["generation"]>;
  if (
    candidate.schemaVersion !== "1.0" ||
    !candidate.sourceRun ||
    typeof candidate.sourceRun.runId !== "string" ||
    typeof candidate.sourceRun.sampleId !== "string" ||
    !Number.isInteger(candidate.layer) || candidate.layer < 0 ||
    !["resid_post", "attn_out", "mlp_out"].includes(candidate.component) ||
    !Number.isFinite(candidate.scale) ||
    !Number.isInteger(candidate.positionStart) || candidate.positionStart < 0 ||
    !Number.isInteger(candidate.positionEnd) || candidate.positionEnd <= candidate.positionStart ||
    !Number.isInteger(candidate.targetTokenId) ||
    typeof candidate.targetTokenText !== "string" ||
    !Number.isInteger(candidate.seed) ||
    !Number.isInteger(candidate.maxNewTokens) || candidate.maxNewTokens < 1 || candidate.maxNewTokens > 256 ||
    !Number.isFinite(candidate.temperature) || candidate.temperature < 0 ||
    !Number.isInteger(candidate.tokenEditDistance) || candidate.tokenEditDistance < 0 ||
    candidate.generationChanged !== (candidate.tokenEditDistance > 0) ||
    !Array.isArray(candidate.diff) || candidate.diff.length > 512 ||
    !isGenerationOutput(candidate.original, candidate.maxNewTokens) ||
    !isGenerationOutput(candidate.steered, candidate.maxNewTokens)
  ) {
    return false;
  }

  let originalCursor = 0;
  let steeredCursor = 0;
  for (const row of candidate.diff) {
    if (!row || typeof row !== "object") return false;
    const originalLength = row.originalEnd - row.originalStart;
    const steeredLength = row.steeredEnd - row.steeredStart;
    if (
      !["equal", "replace", "delete", "insert"].includes(row.kind) ||
      !Number.isInteger(row.originalStart) || !Number.isInteger(row.originalEnd) ||
      !Number.isInteger(row.steeredStart) || !Number.isInteger(row.steeredEnd) ||
      row.originalStart !== originalCursor || row.steeredStart !== steeredCursor ||
      originalLength < 0 || steeredLength < 0 ||
      (row.kind === "equal" && (originalLength === 0 || originalLength !== steeredLength)) ||
      (row.kind === "replace" && (originalLength === 0 || steeredLength === 0)) ||
      (row.kind === "delete" && (originalLength === 0 || steeredLength !== 0)) ||
      (row.kind === "insert" && (originalLength !== 0 || steeredLength === 0))
    ) {
      return false;
    }
    originalCursor = row.originalEnd;
    steeredCursor = row.steeredEnd;
  }
  return originalCursor === candidate.original.tokens.length &&
    steeredCursor === candidate.steered.tokens.length;
}

function isAttentionMatrix(
  matrix: unknown,
  evidence: Partial<PinnedEvidence>
) {
  if (!matrix || typeof matrix !== "object") return false;
  const candidate = matrix as NonNullable<PinnedEvidence["matrix"]>;
  if (
    candidate.schemaVersion !== "1.0" ||
    candidate.kind !== "attention_matrix" ||
    typeof candidate.label !== "string" ||
    !Number.isInteger(candidate.originalSize) || candidate.originalSize < 1 ||
    typeof candidate.sampled !== "boolean" ||
    !Array.isArray(candidate.axis) || candidate.axis.length < 1 || candidate.axis.length > 64 ||
    candidate.originalSize < candidate.axis.length ||
    candidate.sampled === (candidate.originalSize === candidate.axis.length) ||
    !Array.isArray(candidate.values) || candidate.values.length !== candidate.axis.length ||
    evidence.view !== "attention" || typeof evidence.headId !== "string"
  ) {
    return false;
  }
  const axisValid = candidate.axis.every((point, index) =>
    point !== null &&
    typeof point === "object" &&
    Number.isInteger(point.tokenIndex) && point.tokenIndex >= 0 &&
    (point.tokenId === undefined || Number.isInteger(point.tokenId)) &&
    typeof point.tokenText === "string" &&
    (index === 0 || point.tokenIndex > candidate.axis[index - 1].tokenIndex)
  );
  if (!axisValid) return false;
  const tokenIndices = new Set(candidate.axis.map((point) => point.tokenIndex));
  if (
    !tokenIndices.has(evidence.tokenIndex ?? -1) ||
    evidence.sourceTokenIndex === undefined ||
    !tokenIndices.has(evidence.sourceTokenIndex)
  ) {
    return false;
  }
  return candidate.values.every((row, destination) =>
    Array.isArray(row) &&
    row.length === candidate.axis.length &&
    row.every((value, source) => {
      const masked = candidate.axis[source].tokenIndex > candidate.axis[destination].tokenIndex;
      return masked
        ? value === null
        : typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1;
    })
  );
}

function isGenerationOutput(
  output: NonNullable<PinnedEvidence["generation"]>["original"] | undefined,
  maxNewTokens: number
) {
  return Boolean(
    output &&
    typeof output.text === "string" &&
    Array.isArray(output.tokens) &&
    output.tokens.length <= maxNewTokens &&
    Number.isFinite(output.targetLogit) &&
    Number.isFinite(output.lexicalRisk) &&
    output.tokens.every((token, index) =>
      token !== null &&
      typeof token === "object" &&
      token.index === index &&
      Number.isInteger(token.tokenId) &&
      typeof token.text === "string"
    )
  );
}
