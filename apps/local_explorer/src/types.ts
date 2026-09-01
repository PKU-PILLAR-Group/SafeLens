export type ComponentKind = "residual" | "attention" | "mlp";
export type NormalizationMode = "raw" | "normalized";
export type WorkspaceView =
  | "overview"
  | "residual"
  | "attention"
  | "mlp"
  | "nla"
  | "patching"
  | "intervention"
  | "attribution";

export interface TokenInfo {
  index: number;
  text: string;
  tokenId: number;
  source: "prompt" | "reply";
  risk: number;
  attribution: number;
  isSpecial?: boolean;
  generationStep?: number;
  probeScore?: number;
  monitorHit?: boolean;
}

export interface NLARow {
  tokenIndex: number;
  layer: number;
  component: "resid_post" | "attn_result" | "mlp_out";
  explanation: string;
  cosine: number;
  mse: number;
  fve?: number;
  activationNorm: number;
  status?: "available" | "unavailable";
  profile?: string | null;
  source?: string;
  token?: string;
  generation?: {
    complete: boolean;
    finishReason: "end_tag" | "eos" | "length" | "unknown";
    generatedTokenCount: number;
    requestedMaxNewTokens: number;
  };
}

export interface NLAProfileCompatibility {
  name: string;
  baseModel: string;
  layer: number;
  component: string;
  dModel: number;
  modelMatches: boolean;
  layerAvailable: boolean;
  dModelMatches: boolean;
  status: "compatible" | "artifact_missing" | "incompatible";
  reason: string;
}

export interface NLACompatibility {
  modelName: string;
  dModel: number;
  availableLayers: number[];
  profiles: NLAProfileCompatibility[];
}

export type AttentionAggregation = "mean" | "max" | "entropy_weighted";
export type AttentionEdgeMode = "incoming" | "outgoing";

export interface AttentionDifference {
  selectedHeadId: string;
  baselineHeadId: string;
}

export interface AttentionRollout {
  fusion: "retained_mean";
  residual: "identity";
  layers: number[];
  memberHeadIds: string[];
}

export interface AttentionHead {
  id: string;
  layer: number;
  head: number;
  role: string;
  riskContribution: number;
  entropy: number;
  distributionByToken: number[][];
  aggregation?: AttentionAggregation;
  difference?: AttentionDifference;
  rollout?: AttentionRollout;
  memberHeadIds?: string[];
}

export interface MLPNeuron {
  id: string;
  layer: number;
  neuron: number;
  label: string;
  activation: number;
  riskContribution: number;
  topTokens: number[];
  positiveTopTokens: number[];
  negativeTopTokens: number[];
  activationsByToken: number[];
  maxAbsoluteActivation: number;
}

export interface ResidualCell {
  layer: number;
  tokenIndex: number;
  norm: number;
  rawDirection: number;
  riskDirection: number;
  semanticDensity: number;
}

export interface LogitLensPrediction {
  tokenId: number;
  tokenText: string;
  logit: number;
  probability: number;
}

export interface LogitLensRow {
  layer: number;
  tokenIndex: number;
  targetTokenId: number;
  targetTokenText: string;
  targetLogit: number;
  targetProbability: number;
  targetRank: number;
  topPredictions: LogitLensPrediction[];
  sourceKey: string;
}

export interface JLensRow extends LogitLensRow {
  modelTopPredictions: LogitLensPrediction[];
  lensSource: string;
  filename: string;
  revision: string;
  nPrompts: number;
}

export interface ComponentCell {
  layer: number;
  tokenIndex: number;
  value: number;
  rawValue: number;
  metric: string;
  sourceKey: string;
}

export interface MetricProvenance {
  label: string;
  method: string;
  semantics: string;
  normalization: string;
  kind: "raw" | "derived_proxy" | "safety_method" | "causal";
}

export interface EvidenceProfilePoint {
  tokenIndex: number;
  tokenId?: number;
  tokenText: string;
  value: number;
}

export interface EvidenceProfileSnapshot {
  schemaVersion: "1.0";
  kind: "attention_source_profile" | "signed_attribution_profile" | "mlp_activation_profile";
  label: string;
  axis: "source_token" | "token";
  signed: boolean;
  originalLength: number;
  sampled: boolean;
  points: EvidenceProfilePoint[];
}

export interface EvidenceMatrixAxisPoint {
  tokenIndex: number;
  tokenId?: number;
  tokenText: string;
}

export interface AttentionMatrixSnapshot {
  schemaVersion: "1.0";
  kind: "attention_matrix";
  label: string;
  originalSize: number;
  sampled: boolean;
  axis: EvidenceMatrixAxisPoint[];
  values: Array<Array<number | null>>;
}

export interface InterventionGenerationSnapshot {
  schemaVersion: "1.0";
  sourceRun: { runId: string; sampleId: string };
  layer: number;
  component: InterventionExperiment["component"];
  scale: number;
  positionStart: number;
  positionEnd: number;
  targetTokenId: number;
  targetTokenText: string;
  seed: number;
  maxNewTokens: number;
  temperature: number;
  original: Omit<InterventionOutput, "tokenIds">;
  steered: Omit<InterventionOutput, "tokenIds">;
  tokenEditDistance: number;
  generationChanged: boolean;
  diff: InterventionExperiment["diff"];
}

export interface EvidenceAssessment {
  schemaVersion: "1.0";
  status: "available" | "unavailable" | "incompatible" | "not-computed" | "failed" | "loading" | "cancelled";
  statusReason: string;
  primaryLabel: string;
  primaryValue: string;
  rawValue: string;
  displayValue: string;
  units: string;
  evidenceClass: MetricProvenance["kind"];
  method: string;
  normalization: string;
  cacheKey: string;
  shape: string;
  sourceArtifact: string;
  warnings: string[];
  reproduction: Record<string, unknown>;
}

export interface PinnedEvidence {
  id: string;
  runId: string;
  sampleId: string;
  tokenIndex: number;
  tokenText: string;
  tokenId?: number;
  tokenSource?: TokenInfo["source"];
  modelName?: string;
  modelSource?: string;
  layer: number;
  view: WorkspaceView;
  component: string;
  metric: string;
  value: number;
  normalization: NormalizationMode;
  headId?: string;
  neuronId?: string;
  trackName?: string;
  sourceTokenIndex?: number;
  sourceKey?: string;
  provenance?: MetricProvenance;
  profile?: EvidenceProfileSnapshot;
  matrix?: AttentionMatrixSnapshot;
  generation?: InterventionGenerationSnapshot;
  assessment?: EvidenceAssessment;
  capturedAt?: string;
}

export interface ExplorerSelectionState {
  view: WorkspaceView;
  tokenIndex: number;
  sourceTokenIndex?: number;
  targetTokenIndex?: number;
  tokenRange?: [number, number];
  layer: number;
  headId: string;
  attentionEdgeMode: AttentionEdgeMode;
  nlaComponent: NLARow["component"];
  neuronId: string;
  trackName: string;
  metric: string;
  normalization: NormalizationMode;
  pinnedItems: PinnedEvidence[];
}

export interface AttributionTrack {
  name: string;
  values: number[];
}

export interface AttributionMethodRow {
  layer: number;
  label: string;
  values: number[];
  sourceKey: string;
}

export interface AttributionMethod {
  id: string;
  label: string;
  description: string;
  evidenceKind: MetricProvenance["kind"];
  signed: boolean;
  normalization: string;
  available: boolean;
  unavailableReason?: string;
  rows: AttributionMethodRow[];
}

export interface PatchingToken {
  index: number;
  tokenId: number;
  text: string;
  changed: boolean;
}

export interface PatchingCell {
  layer: number;
  tokenIndex: number;
  patchedScore: number;
  causalEffect: number;
  recoveryPercentage: number | null;
  sourceKey: string;
}

export interface PatchingExperiment {
  cleanPrompt: string;
  corruptedPrompt: string;
  component: "resid_post" | "attn_out" | "z" | "mlp_out";
  head?: number;
  targetTokenId: number;
  targetTokenText: string;
  cleanScore: number;
  corruptedScore: number;
  denominator: number;
  layers: number[];
  positions: number[];
  corruptedTokens: PatchingToken[];
  cells: PatchingCell[];
  sourceRun: { runId: string; sampleId: string };
  sourceKey: string;
}

export interface InterventionOutput {
  text: string;
  tokenIds: number[];
  tokens: Array<{ index: number; tokenId: number; text: string }>;
  targetLogit: number;
  lexicalRisk: number;
}

export interface InterventionExperiment {
  mode: "direction" | "neuron" | "sae_feature";
  feature?: {
    kind: "mlp_neuron" | "sae_feature";
    id: string;
    label: string;
    layer: number;
    neuron?: number;
    featureIndex?: number;
    baselineActivation: number;
    meanActivation?: number;
    activeTokenCount?: number;
    operation: "suppress" | "reduce" | "enhance" | "invert" | "add" | "ablate";
    release?: string;
    saeId?: string;
    width?: number;
    architecture?: "jump_relu";
    source?: string;
    conceptLabel?: string | null;
    conceptSource?: "neuronpedia" | "index";
    conceptUrl?: string | null;
    positiveTokens?: string[];
    negativeTokens?: string[];
  };
  vector: {
    algorithmVersion?: string;
    method: string;
    desiredPrompt: string;
    undesiredPrompt: string;
    positivePrompts?: string[];
    negativePrompts?: string[];
    positiveCount?: number;
    negativeCount?: number;
    activationReduce: string;
    rawNorm: number;
    normalized: boolean;
    dimension: number;
    sourceKey: string;
    injectionKey?: string;
    injectionPhase?: "generation" | "prompt" | "prompt_and_generation";
    referenceTemplate?: string;
    desiredTokenCount?: number;
    undesiredTokenCount?: number;
    sourceActivationNorm?: number;
    appliedVectorNorm?: number;
    relativeStrength?: number;
  };
  layer: number;
  sourceLayer?: number;
  injectLayer?: number;
  component: "resid_post" | "attn_out" | "mlp_out";
  scale: number;
  positionStart: number;
  positionEnd: number;
  targetTokenId: number;
  targetTokenText: string;
  seed: number;
  maxNewTokens: number;
  temperature: number;
  original: InterventionOutput;
  steered: InterventionOutput;
  deltas: {
    targetLogit: number;
    lexicalRisk: number;
    tokenEditDistance: number;
    generationChanged: boolean;
    firstDivergenceIndex?: number | null;
    maxAbsLogit?: number;
    meanAbsLogit?: number;
    changedVocabularyLogits?: number;
    topChangedTokenId?: number;
    topChangedTokenDelta?: number;
    directionProjectionDelta?: number;
    featureActivationDelta?: number;
    effectStatus?: "changed" | "no_change";
    probeScore: number | null;
    probeReason: string;
  };
  diff: Array<{
    kind: "equal" | "replace" | "delete" | "insert";
    originalStart: number;
    originalEnd: number;
    steeredStart: number;
    steeredEnd: number;
  }>;
  sourceRun: { runId: string; sampleId: string };
}

export interface ExplorerRun {
  runId: string;
  modelName: string;
  modelSource: string;
  sampleId: string;
  prompt: string;
  tokens: TokenInfo[];
  layers: number[];
  nla: NLARow[];
  nlaCompatibility: NLACompatibility;
  attentionHeads: AttentionHead[];
  mlpNeurons: MLPNeuron[];
  residualCells: ResidualCell[];
  logitLens: LogitLensRow[];
  jLens: JLensRow[];
  attentionCells: ComponentCell[];
  mlpCells: ComponentCell[];
  attributionTracks: AttributionTrack[];
  attributionMethods: AttributionMethod[];
  patching?: PatchingExperiment;
  intervention?: InterventionExperiment;
  metricProvenance: Record<string, MetricProvenance>;
  metadata?: Record<string, unknown>;
}
