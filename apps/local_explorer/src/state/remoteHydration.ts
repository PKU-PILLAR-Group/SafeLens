import { z } from "zod";

import {
  fetchRemoteRunChunk,
  type ChunkRequest,
  type RemoteRunSummary,
  type RunChunk,
  type RunMetadata
} from "../api/explorerClient";
import { explorerRunCoreSchema } from "../schemas/explorerArtifact";
import { jLensRowSchema } from "../schemas/explorerArtifact";
import type { ExplorerRun, WorkspaceView } from "../types";

const TOKEN_BLOCK_SIZE = 512;

export interface PartialRunHydration {
  mode: "partial";
  metadata: RunMetadata;
  loadedScopes: string[];
  loadingScope?: string;
  errors: Record<string, string>;
  cancelledScopes: string[];
}

export interface FullRunHydration {
  mode: "full";
}

export type RunHydration = PartialRunHydration | FullRunHydration;

export function buildPartialExplorerRun(metadata: RunMetadata): ExplorerRun {
  const parsed = explorerRunCoreSchema.safeParse(metadata.base);
  if (!parsed.success) {
    const issue = parsed.error.issues[0];
    throw new Error(
      `Chunk metadata core failed at ${issue?.path.join(".") || "base"}: ${issue?.message || "invalid core"}.`
    );
  }
  if (parsed.data.runId !== metadata.runId || parsed.data.sampleId !== metadata.sampleId) {
    throw new Error("Chunk metadata core does not match its run/sample envelope.");
  }
  const defaultLayer = parsed.data.layers[parsed.data.layers.length - 1] ?? 0;
  return {
    ...parsed.data,
    attentionHeads: [{
      id: "__chunk_pending__",
      layer: defaultLayer,
      head: 0,
      role: "component data loading",
      riskContribution: 0,
      entropy: 0,
      distributionByToken: []
    }],
    mlpNeurons: [],
    residualCells: [],
    logitLens: [],
    jLens: [],
    attentionCells: [],
    mlpCells: [],
    attributionTracks: [],
    attributionMethods: [{
      id: "__chunk_pending__",
      label: "Component data loading",
      description: "The selected attribution chunk has not loaded yet.",
      evidenceKind: "raw",
      signed: false,
      normalization: "not loaded",
      available: false,
      unavailableReason: "Component data is loading; this is not an unavailable evidence result.",
      rows: []
    }],
    nla: []
  } as ExplorerRun;
}

export function hydrationScope(
  view: WorkspaceView,
  layer: number,
  tokenIndex: number,
  sourceTokenIndex = tokenIndex
) {
  const { start, end } = tokenBlock(tokenIndex);
  const layerPart = ["attention", "mlp"].includes(view) ? `:L${layer}` : "";
  const sourceBlock = tokenBlock(sourceTokenIndex);
  const sourcePart = view === "attention" ? `:S${sourceBlock.start}-${sourceBlock.end}` : "";
  return `${view}${layerPart}:T${start}-${end}${sourcePart}`;
}

export function isViewHydrated(
  hydration: RunHydration | undefined,
  view: WorkspaceView,
  layer: number,
  tokenIndex: number,
  sourceTokenIndex = tokenIndex
) {
  return !hydration || hydration.mode === "full" || hydration.loadedScopes.includes(
    hydrationScope(view, layer, tokenIndex, sourceTokenIndex)
  );
}

export function requestsForView(
  view: WorkspaceView,
  layer: number,
  tokenIndex: number,
  tokenCount: number,
  sourceTokenIndex = tokenIndex
): ChunkRequest[] {
  const block = tokenBlock(tokenIndex, tokenCount);
  const range = { tokenStart: block.start, tokenEnd: block.end };
  if (view === "overview") {
    return [
      { component: "residualCells", ...range },
      { component: "logitLens", ...range }
    ];
  }
  if (view === "residual") {
    return [
      { component: "residualCells", ...range },
      { component: "logitLens", ...range }
    ];
  }
  if (view === "attention") {
    const sourceBlock = tokenBlock(sourceTokenIndex, tokenCount);
    return [
      {
        component: "attentionHeads",
        layer,
        ...range,
        sourceStart: sourceBlock.start,
        sourceEnd: sourceBlock.end
      },
      { component: "attentionCells", layer, ...range },
      { component: "residualCells", ...range }
    ];
  }
  if (view === "mlp") {
    return [
      { component: "mlpNeurons", layer, ...range },
      { component: "mlpCells", layer, ...range },
      { component: "residualCells", ...range }
    ];
  }
  if (view === "attribution") {
    return [
      { component: "attributionMethods", ...range },
      { component: "attributionTracks", ...range },
      { component: "residualCells", ...range }
    ];
  }
  if (view === "nla") return [
    { component: "nla", ...range },
    { component: "residualCells", ...range }
  ];
  if (view === "patching") return [{ component: "patching", ...range }];
  return [{ component: "intervention", ...range }];
}

export async function hydrateView(
  run: ExplorerRun,
  summary: RemoteRunSummary,
  view: WorkspaceView,
  layer: number,
  tokenIndex: number,
  signal: AbortSignal,
  sourceTokenIndex = tokenIndex
) {
  const chunks = await fetchViewChunks(
    run,
    summary,
    view,
    layer,
    tokenIndex,
    signal,
    sourceTokenIndex
  );
  return chunks.reduce((current, chunk) => mergeRunChunk(current, chunk), run);
}

export async function fetchViewChunks(
  run: ExplorerRun,
  summary: RemoteRunSummary,
  view: WorkspaceView,
  layer: number,
  tokenIndex: number,
  signal: AbortSignal,
  sourceTokenIndex = tokenIndex
) {
  const requests = requestsForView(
    view,
    layer,
    tokenIndex,
    run.tokens.length,
    sourceTokenIndex
  );
  const chunks = await Promise.all(
    requests.map((request) => fetchRemoteRunChunk(summary, request, signal))
  );
  return chunks;
}

export function mergeRunChunk(run: ExplorerRun, chunk: RunChunk): ExplorerRun {
  if (chunk.component === "residualCells") {
    return { ...run, residualCells: mergePositionRows(run.residualCells, residualCellsSchema.parse(chunk.data)) };
  }
  if (chunk.component === "logitLens") {
    return { ...run, logitLens: mergePositionRows(run.logitLens, logitLensSchema.parse(chunk.data)) };
  }
  if (chunk.component === "jLens") {
    return { ...run, jLens: mergePositionRows(run.jLens, z.array(jLensRowSchema).parse(chunk.data)) };
  }
  if (chunk.component === "attentionCells") {
    return { ...run, attentionCells: mergePositionRows(run.attentionCells, componentCellsSchema.parse(chunk.data)) };
  }
  if (chunk.component === "mlpCells") {
    return { ...run, mlpCells: mergePositionRows(run.mlpCells, componentCellsSchema.parse(chunk.data)) };
  }
  if (chunk.component === "nla") {
    const rows = nlaRowsSchema.parse(chunk.data);
    const byKey = new Map(run.nla.map((row) => [`${row.layer}:${row.component}:${row.tokenIndex}`, row]));
    for (const row of rows) byKey.set(`${row.layer}:${row.component}:${row.tokenIndex}`, row);
    return { ...run, nla: [...byKey.values()] };
  }
  if (chunk.component === "attentionHeads") return mergeAttentionHeads(run, chunk.data);
  if (chunk.component === "mlpNeurons") return mergeMlpNeurons(run, chunk.data);
  if (chunk.component === "attributionTracks") return mergeAttributionTracks(run, chunk.data);
  if (chunk.component === "attributionMethods") return mergeAttributionMethods(run, chunk.data);
  if (chunk.component === "patching") {
    return { ...run, patching: chunk.data as ExplorerRun["patching"] };
  }
  return { ...run, intervention: chunk.data as ExplorerRun["intervention"] };
}

function mergeAttentionHeads(run: ExplorerRun, data: unknown): ExplorerRun {
  const heads = attentionHeadChunksSchema.parse(data);
  const byId = new Map(
    run.attentionHeads
      .filter((head) => head.id !== "__chunk_pending__")
      .map((head) => [head.id, head])
  );
  for (const incoming of heads) {
    const existing = byId.get(incoming.id);
    const matrix = existing?.distributionByToken.map((row) => row.slice()) ??
      Array.from({ length: run.tokens.length }, () => [] as number[]);
    incoming.distributionByToken.forEach((values, localRow) => {
      const rowIndex = incoming.chunk.destinationStart + localRow;
      const row = matrix[rowIndex]?.slice() ?? [];
      values.forEach((value, localColumn) => {
        row[incoming.chunk.sourceStart + localColumn] = value;
      });
      matrix[rowIndex] = row;
    });
    const { chunk: _chunk, ...head } = incoming;
    byId.set(incoming.id, { ...head, distributionByToken: matrix });
  }
  return { ...run, attentionHeads: [...byId.values()] };
}

function mergeMlpNeurons(run: ExplorerRun, data: unknown): ExplorerRun {
  const neurons = mlpNeuronChunksSchema.parse(data);
  const byId = new Map(run.mlpNeurons.map((neuron) => [neuron.id, neuron]));
  for (const incoming of neurons) {
    const existing = byId.get(incoming.id);
    const values = existing?.activationsByToken.slice() ?? [];
    incoming.activationsByToken.forEach((value, index) => {
      values[incoming.chunk.tokenStart + index] = value;
    });
    const { chunk: _chunk, ...neuron } = incoming;
    byId.set(incoming.id, { ...neuron, activationsByToken: values });
  }
  return { ...run, mlpNeurons: [...byId.values()] };
}

function mergeAttributionTracks(run: ExplorerRun, data: unknown): ExplorerRun {
  const tracks = attributionTrackChunksSchema.parse(data);
  const byName = new Map(run.attributionTracks.map((track) => [track.name, track]));
  for (const incoming of tracks) {
    const values = byName.get(incoming.name)?.values.slice() ?? [];
    incoming.values.forEach((value, index) => { values[incoming.chunk.tokenStart + index] = value; });
    byName.set(incoming.name, { name: incoming.name, values });
  }
  return { ...run, attributionTracks: [...byName.values()] };
}

function mergeAttributionMethods(run: ExplorerRun, data: unknown): ExplorerRun {
  const methods = attributionMethodChunksSchema.parse(data);
  const byId = new Map(
    run.attributionMethods
      .filter((method) => method.id !== "__chunk_pending__")
      .map((method) => [method.id, method])
  );
  for (const incoming of methods) {
    const existing = byId.get(incoming.id);
    const rows = new Map(existing?.rows.map((row) => [row.layer, row]) ?? []);
    for (const incomingRow of incoming.rows) {
      const values = rows.get(incomingRow.layer)?.values.slice() ?? [];
      incomingRow.values.forEach((value, index) => {
        values[incomingRow.chunk.tokenStart + index] = value;
      });
      const { chunk: _chunk, ...row } = incomingRow;
      rows.set(row.layer, { ...row, values });
    }
    byId.set(incoming.id, { ...incoming, rows: [...rows.values()] });
  }
  return { ...run, attributionMethods: [...byId.values()] };
}

function mergePositionRows<T extends { layer: number; tokenIndex: number }>(current: T[], incoming: T[]) {
  const rows = new Map(current.map((row) => [`${row.layer}:${row.tokenIndex}`, row]));
  for (const row of incoming) rows.set(`${row.layer}:${row.tokenIndex}`, row);
  return [...rows.values()];
}

function tokenBlock(tokenIndex: number, tokenCount = Number.MAX_SAFE_INTEGER) {
  const start = Math.floor(Math.max(0, tokenIndex) / TOKEN_BLOCK_SIZE) * TOKEN_BLOCK_SIZE;
  return { start, end: Math.min(tokenCount, start + TOKEN_BLOCK_SIZE) };
}

const residualCellsSchema = z.array(z.object({
  layer: z.number().int().nonnegative(), tokenIndex: z.number().int().nonnegative(),
  norm: z.number(), rawDirection: z.number(), riskDirection: z.number(), semanticDensity: z.number()
}));
const componentCellsSchema = z.array(z.object({
  layer: z.number().int().nonnegative(), tokenIndex: z.number().int().nonnegative(),
  value: z.number(), rawValue: z.number(), metric: z.string(), sourceKey: z.string()
}));
const logitLensSchema = z.array(z.object({
  layer: z.number().int().nonnegative(), tokenIndex: z.number().int().nonnegative(),
  targetTokenId: z.number().int(), targetTokenText: z.string(), targetLogit: z.number(),
  targetProbability: z.number(), targetRank: z.number().int(), sourceKey: z.string(),
  topPredictions: z.array(z.object({
    tokenId: z.number().int(), tokenText: z.string(), logit: z.number(), probability: z.number()
  }))
}));
const nlaRowsSchema = z.array(z.object({
  tokenIndex: z.number().int().nonnegative(), layer: z.number().int().nonnegative(),
  component: z.enum(["resid_post", "attn_result", "mlp_out"]), explanation: z.string(),
  cosine: z.number(), mse: z.number(), fve: z.number().optional(), activationNorm: z.number(),
  status: z.enum(["available", "unavailable"]).optional(), profile: z.string().nullable().optional(),
  source: z.string().optional(), token: z.string().optional()
}));
const chunkRangeSchema = z.object({ tokenStart: z.number().int(), tokenEnd: z.number().int() });
const attentionHeadChunksSchema = z.array(z.object({
  id: z.string(), layer: z.number().int(), head: z.number().int(), role: z.string(),
  riskContribution: z.number(), entropy: z.number(), distributionByToken: z.array(z.array(z.number())),
  chunk: z.object({
    destinationStart: z.number().int(), destinationEnd: z.number().int(),
    sourceStart: z.number().int(), sourceEnd: z.number().int()
  })
}));
const mlpNeuronChunksSchema = z.array(z.object({
  id: z.string(), layer: z.number().int(), neuron: z.number().int(), label: z.string(),
  activation: z.number(), riskContribution: z.number(), topTokens: z.array(z.number().int()),
  positiveTopTokens: z.array(z.number().int()), negativeTopTokens: z.array(z.number().int()),
  activationsByToken: z.array(z.number()), maxAbsoluteActivation: z.number(), chunk: chunkRangeSchema
}));
const attributionTrackChunksSchema = z.array(z.object({
  name: z.string(), values: z.array(z.number()), chunk: chunkRangeSchema
}));
const attributionMethodChunksSchema = z.array(z.object({
  id: z.string(), label: z.string(), description: z.string(),
  evidenceKind: z.enum(["raw", "derived_proxy", "safety_method", "causal"]),
  signed: z.boolean(), normalization: z.string(), available: z.boolean(),
  unavailableReason: z.string().optional(),
  rows: z.array(z.object({
    layer: z.number().int(), label: z.string(), values: z.array(z.number()),
    sourceKey: z.string(), chunk: chunkRangeSchema
  }))
}));
