import { z } from "zod";

import { explorerRunSchema } from "../schemas/explorerArtifact";
import type { ExplorerRun } from "../types";

const API_BASE = "/api";

const remoteSummarySchema = z.object({
  runId: z.string().min(1),
  sampleId: z.string().min(1),
  modelName: z.string().min(1),
  modelSource: z.string().min(1),
  tokenCount: z.number().int().positive(),
  layerCount: z.number().int().positive(),
  artifactId: z.string().min(1),
  sourceName: z.string().min(1),
  modifiedAt: z.string().min(1),
  sizeBytes: z.number().int().nonnegative(),
  promptPreview: z.string().max(160).nullable().optional(),
  parentRun: z.object({ runId: z.string().min(1), sampleId: z.string().min(1) }).nullable().optional(),
  conversationId: z.string().min(1).nullable().optional(),
  turnIndex: z.number().int().nonnegative().nullable().optional(),
  chunkProtocol: z.literal("safelens-chunks-v1").optional()
});

const runIndexSchema = z.object({
  schemaVersion: z.literal("1.0"),
  source: z.literal("local-workspace"),
  rootName: z.string(),
  runs: z.array(remoteSummarySchema),
  diagnostics: z.array(z.object({
    sourceName: z.string(),
    code: z.string(),
    message: z.string()
  }))
});

export type RemoteRunSummary = z.infer<typeof remoteSummarySchema>;

const chunkComponentSchema = z.enum([
  "residualCells",
  "logitLens",
  "jLens",
  "attentionHeads",
  "attentionCells",
  "mlpNeurons",
  "mlpCells",
  "attributionTracks",
  "attributionMethods",
  "nla",
  "patching",
  "intervention"
]);

const runMetadataSchema = z.object({
  schemaVersion: z.literal("1.0"),
  protocol: z.literal("safelens-chunks-v1"),
  runId: z.string().min(1),
  sampleId: z.string().min(1),
  artifactId: z.string().min(1),
  version: z.string().min(1),
  base: z.record(z.string(), z.unknown()),
  chunks: z.array(z.object({
    component: chunkComponentSchema,
    itemCount: z.number().int().nonnegative(),
    rangeAxis: z.enum(["token", "token-square", "token-values", "none"]),
    layerFilter: z.boolean(),
    selectorFilter: z.boolean()
  }))
});

const runChunkSchema = z.object({
  schemaVersion: z.literal("1.0"),
  protocol: z.literal("safelens-chunks-v1"),
  runId: z.string().min(1),
  sampleId: z.string().min(1),
  artifactId: z.string().min(1),
  version: z.string().min(1),
  component: chunkComponentSchema,
  tokenRange: z.tuple([z.number().int().nonnegative(), z.number().int().positive()]),
  sourceRange: z.tuple([z.number().int().nonnegative(), z.number().int().positive()]).nullable().optional(),
  layer: z.number().int().nonnegative().nullable(),
  selector: z.string().nullable(),
  data: z.unknown()
});

export type RunMetadata = z.infer<typeof runMetadataSchema>;
export type ChunkComponent = z.infer<typeof chunkComponentSchema>;
export type RunChunk = z.infer<typeof runChunkSchema>;

export interface ChunkRequest {
  component: ChunkComponent;
  tokenStart: number;
  tokenEnd: number;
  sourceStart?: number;
  sourceEnd?: number;
  layer?: number;
  selector?: string;
}

interface CachedResponse<T> {
  etag: string;
  value: T;
}

const metadataCache = new Map<string, CachedResponse<RunMetadata>>();
const chunkCache = new Map<string, CachedResponse<RunChunk>>();
const inFlightRequests = new Map<string, SharedRequest<unknown>>();
const MAX_METADATA_CACHE_ENTRIES = 32;
const MAX_CHUNK_CACHE_ENTRIES = 96;

interface SharedRequest<T> {
  controller: AbortController;
  promise: Promise<T>;
  subscribers: number;
  settled: boolean;
  abortTimer?: ReturnType<typeof setTimeout>;
}

function sharedRequest<T>(
  key: string,
  signal: AbortSignal,
  factory: (signal: AbortSignal) => Promise<T>
): Promise<T> {
  if (signal.aborted) return Promise.reject(abortError());
  let entry = inFlightRequests.get(key) as SharedRequest<T> | undefined;
  if (entry?.controller.signal.aborted) {
    inFlightRequests.delete(key);
    entry = undefined;
  }
  if (!entry) {
    const controller = new AbortController();
    entry = {
      controller,
      promise: factory(controller.signal),
      subscribers: 0,
      settled: false
    };
    inFlightRequests.set(key, entry as SharedRequest<unknown>);
    entry.promise.then(
      () => finishSharedRequest(key, entry!),
      () => finishSharedRequest(key, entry!)
    );
  }
  if (entry.abortTimer !== undefined) {
    clearTimeout(entry.abortTimer);
    entry.abortTimer = undefined;
  }
  entry.subscribers += 1;
  return new Promise<T>((resolve, reject) => {
    let finished = false;
    const release = (cancelled: boolean) => {
      if (finished) return;
      finished = true;
      signal.removeEventListener("abort", onAbort);
      entry!.subscribers = Math.max(0, entry!.subscribers - 1);
      if (cancelled && entry!.subscribers === 0 && !entry!.settled) {
        entry!.abortTimer = setTimeout(() => {
          if (entry!.subscribers === 0 && !entry!.settled) entry!.controller.abort();
        }, 0);
      }
    };
    const onAbort = () => {
      release(true);
      reject(abortError());
    };
    signal.addEventListener("abort", onAbort, { once: true });
    entry!.promise.then(
      (value) => { release(false); resolve(value); },
      (error) => { release(false); reject(error); }
    );
  });
}

function finishSharedRequest(key: string, entry: SharedRequest<unknown>) {
  entry.settled = true;
  if (inFlightRequests.get(key) === entry) inFlightRequests.delete(key);
}

function abortError() {
  return new DOMException("The artifact request was cancelled.", "AbortError");
}

function cacheGet<T>(cache: Map<string, T>, key: string) {
  const value = cache.get(key);
  if (value !== undefined) {
    cache.delete(key);
    cache.set(key, value);
  }
  return value;
}

function cacheSet<T>(cache: Map<string, T>, key: string, value: T, maximum: number) {
  cache.delete(key);
  cache.set(key, value);
  while (cache.size > maximum) cache.delete(cache.keys().next().value!);
}

export interface RemoteRunPayload {
  summary: RemoteRunSummary;
  run: ExplorerRun;
}

export interface RemoteRunResult {
  runs: RemoteRunPayload[];
  rootName: string;
  diagnostics: string[];
}

export interface RemoteRunIndexResult {
  summaries: RemoteRunSummary[];
  rootName: string;
  diagnostics: string[];
}

export async function fetchRemoteRunIndex(signal: AbortSignal): Promise<RemoteRunIndexResult> {
  const indexResponse = await fetch(`${API_BASE}/runs`, {
    signal,
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!indexResponse.ok) {
    throw new ExplorerApiError(
      "http_error",
      `Explorer API returned HTTP ${indexResponse.status} for the run index.`
    );
  }
  const indexResult = runIndexSchema.safeParse(await indexResponse.json());
  if (!indexResult.success) {
    throw new ExplorerApiError(
      "invalid_index",
      `Explorer API index failed validation: ${indexResult.error.issues[0]?.message ?? "unknown error"}`
    );
  }
  return {
    summaries: indexResult.data.runs,
    rootName: indexResult.data.rootName,
    diagnostics: indexResult.data.diagnostics.map(
      (item) => `${item.sourceName} [${item.code}]: ${item.message}`
    )
  };
}

export async function fetchRemoteRun(
  summary: RemoteRunSummary,
  signal: AbortSignal
): Promise<ExplorerRun> {
  const response = await fetch(
    `${API_BASE}/runs/${encodeURIComponent(summary.runId)}/samples/${encodeURIComponent(summary.sampleId)}`,
    { signal, headers: { Accept: "application/json" }, cache: "no-store" }
  );
  if (!response.ok) {
    throw new ExplorerApiError(
      "sample_error",
      `Could not load ${summary.runId}/${summary.sampleId}: HTTP ${response.status}.`
    );
  }
  const parsed = explorerRunSchema.safeParse(await response.json());
  if (!parsed.success) {
    const issue = parsed.error.issues[0];
    throw new ExplorerApiError(
      "invalid_sample",
      `${summary.runId}/${summary.sampleId} failed at ${issue?.path.join(".") || "artifact"}: ${issue?.message || "invalid sample"}.`
    );
  }
  return parsed.data as ExplorerRun;
}

export function fetchRemoteRunMetadata(
  summary: RemoteRunSummary,
  signal: AbortSignal
): Promise<RunMetadata> {
  const key = [
    summary.artifactId,
    summary.modifiedAt,
    summary.sizeBytes,
    summary.runId,
    summary.sampleId
  ].join(":");
  return sharedRequest(`metadata:${key}`, signal, (sharedSignal) =>
    fetchRemoteRunMetadataUnshared(summary, key, sharedSignal)
  );
}

async function fetchRemoteRunMetadataUnshared(
  summary: RemoteRunSummary,
  key: string,
  signal: AbortSignal
) {
  const cached = cacheGet(metadataCache, key);
  const response = await fetch(
    `${API_BASE}/runs/${encodeURIComponent(summary.runId)}/samples/${encodeURIComponent(summary.sampleId)}/metadata`,
    {
      signal,
      headers: {
        Accept: "application/json",
        ...(cached ? { "If-None-Match": cached.etag } : {})
      },
      cache: "no-cache"
    }
  );
  if (response.status === 304 && cached) return cached.value;
  if (!response.ok) {
    throw new ExplorerApiError(
      "metadata_error",
      `Could not load metadata for ${summary.runId}/${summary.sampleId}: HTTP ${response.status}.`
    );
  }
  const parsed = runMetadataSchema.safeParse(await response.json());
  if (!parsed.success || parsed.data.runId !== summary.runId || parsed.data.sampleId !== summary.sampleId) {
    throw new ExplorerApiError(
      "invalid_metadata",
      `${summary.runId}/${summary.sampleId} returned invalid or mismatched chunk metadata.`
    );
  }
  const etag = response.headers.get("ETag") ?? `"${parsed.data.version}"`;
  cacheSet(metadataCache, key, { etag, value: parsed.data }, MAX_METADATA_CACHE_ENTRIES);
  return parsed.data;
}

export function fetchRemoteRunChunk(
  summary: RemoteRunSummary,
  request: ChunkRequest,
  signal: AbortSignal
): Promise<RunChunk> {
  if (
    !Number.isInteger(request.tokenStart) ||
    !Number.isInteger(request.tokenEnd) ||
    request.tokenStart < 0 ||
    request.tokenEnd <= request.tokenStart ||
    request.tokenEnd - request.tokenStart > 512
  ) {
    throw new ExplorerApiError(
      "invalid_chunk_range",
      "Chunk range must be an integer half-open interval of at most 512 tokens."
    );
  }
  if (
    (request.sourceStart === undefined) !== (request.sourceEnd === undefined) ||
    (request.sourceStart !== undefined && (
      !Number.isInteger(request.sourceStart) ||
      !Number.isInteger(request.sourceEnd) ||
      request.sourceStart < 0 ||
      request.sourceEnd! <= request.sourceStart ||
      request.sourceEnd! - request.sourceStart > 512
    ))
  ) {
    throw new ExplorerApiError(
      "invalid_source_range",
      "Attention source range must be an integer half-open interval of at most 512 tokens."
    );
  }
  const params = new URLSearchParams({
    tokenStart: String(request.tokenStart),
    tokenEnd: String(request.tokenEnd)
  });
  if (request.layer !== undefined) params.set("layer", String(request.layer));
  if (request.selector) params.set("selector", request.selector);
  if (request.sourceStart !== undefined) params.set("sourceStart", String(request.sourceStart));
  if (request.sourceEnd !== undefined) params.set("sourceEnd", String(request.sourceEnd));
  const key = [
    summary.artifactId,
    summary.modifiedAt,
    summary.sizeBytes,
    summary.runId,
    summary.sampleId,
    request.component,
    request.tokenStart,
    request.tokenEnd,
    request.sourceStart ?? request.tokenStart,
    request.sourceEnd ?? request.tokenEnd,
    request.layer ?? "all",
    request.selector ?? "all"
  ].join(":");
  return sharedRequest(`chunk:${key}`, signal, (sharedSignal) =>
    fetchRemoteRunChunkUnshared(summary, request, params, key, sharedSignal)
  );
}

async function fetchRemoteRunChunkUnshared(
  summary: RemoteRunSummary,
  request: ChunkRequest,
  params: URLSearchParams,
  key: string,
  signal: AbortSignal
) {
  const cached = cacheGet(chunkCache, key);
  const response = await fetch(
    `${API_BASE}/runs/${encodeURIComponent(summary.runId)}/samples/${encodeURIComponent(summary.sampleId)}/chunks/${request.component}?${params}`,
    {
      signal,
      headers: {
        Accept: "application/json",
        ...(cached ? { "If-None-Match": cached.etag } : {})
      },
      cache: "no-cache"
    }
  );
  if (response.status === 304 && cached) return cached.value;
  if (!response.ok) {
    throw new ExplorerApiError(
      "chunk_error",
      `Could not load ${request.component} chunk: HTTP ${response.status}.`
    );
  }
  const parsed = runChunkSchema.safeParse(await response.json());
  if (
    !parsed.success ||
    parsed.data.runId !== summary.runId ||
    parsed.data.sampleId !== summary.sampleId ||
    parsed.data.component !== request.component
  ) {
    throw new ExplorerApiError(
      "invalid_chunk",
      `${summary.runId}/${summary.sampleId} returned a mismatched ${request.component} chunk.`
    );
  }
  const etag = response.headers.get("ETag") ?? `"${parsed.data.version}:${key}"`;
  cacheSet(chunkCache, key, { etag, value: parsed.data }, MAX_CHUNK_CACHE_ENTRIES);
  return parsed.data;
}

export function clearRemoteArtifactCache(artifactId?: string) {
  for (const cache of [metadataCache, chunkCache]) {
    for (const key of cache.keys()) {
      if (!artifactId || key.startsWith(`${artifactId}:`)) cache.delete(key);
    }
  }
  for (const [key, request] of inFlightRequests) {
    if (!artifactId || key.includes(`:${artifactId}:`)) {
      request.controller.abort();
      inFlightRequests.delete(key);
    }
  }
}

export async function fetchRemoteRuns(signal: AbortSignal): Promise<RemoteRunResult> {
  const indexResult = await fetchRemoteRunIndex(signal);

  const settled = await Promise.allSettled(indexResult.summaries.map(async (summary) => ({
    summary,
    run: await fetchRemoteRun(summary, signal)
  })));

  const loaded = settled.flatMap((result) =>
    result.status === "fulfilled" ? [result.value] : []
  );
  const sampleDiagnostics = settled.flatMap((result) =>
    result.status === "rejected"
      ? [result.reason instanceof Error ? result.reason.message : "A remote sample could not be loaded."]
      : []
  );

  return {
    runs: loaded,
    rootName: indexResult.rootName,
    diagnostics: [
      ...indexResult.diagnostics,
      ...sampleDiagnostics
    ]
  };
}

export class ExplorerApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly httpStatus?: number,
    public readonly serverCode?: string
  ) {
    super(message);
    this.name = "ExplorerApiError";
  }
}

const promptMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().min(1)
});

export const promptJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("prompt-run"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    prompt: z.string(),
    template: z.enum(["plain", "chat"]),
    model: z.string(),
    seed: z.number().int(),
    maxNewTokens: z.number().int(),
    temperature: z.number(),
    messages: z.array(promptMessageSchema).default([])
  }),
  result: explorerRunSchema.nullable(),
  error: z.string().nullable()
});

export type PromptMessage = z.infer<typeof promptMessageSchema>;
export type PromptJob = z.infer<typeof promptJobSchema>;
export type PromptRunInput = PromptJob["request"];

const promptOptionsSchema = z.object({
  models: z.array(z.string().min(1)).min(1),
  templates: z.array(z.enum(["plain", "chat"])),
  maxNewTokens: z.number().int().positive()
});

export type PromptOptions = z.infer<typeof promptOptionsSchema>;

const datasetMetricSchema = z.object({
  name: z.string().min(1),
  shortName: z.string().min(1),
  definition: z.string().min(1),
  threshold: z.number().min(0).max(1)
});

const datasetSampleSchema = z.object({
  id: z.string().min(1),
  category: z.string().min(1),
  prompt: z.string().nullable().optional(),
  cleanPrompt: z.string().nullable().optional(),
  corruptedPrompt: z.string().nullable().optional(),
  desiredPrompt: z.string().nullable().optional(),
  undesiredPrompt: z.string().nullable().optional(),
  targetText: z.string().nullable().optional(),
  expected: z.string().min(1)
});

const datasetDefinitionSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  version: z.string().min(1),
  task: z.string().min(1),
  description: z.string().min(1),
  source: z.string().min(1),
  metric: datasetMetricSchema,
  samples: z.array(datasetSampleSchema).min(1)
});

const datasetAlgorithmSchema = z.object({
  id: z.enum(["steering", "patching"]),
  name: z.string().min(1),
  kind: z.literal("optimization"),
  description: z.string().min(1),
  paperTitle: z.string().min(1),
  paperUrl: z.string().url(),
  implementation: z.string().min(1),
  supportedDatasetIds: z.array(z.string().min(1)).min(1)
});

const datasetCatalogSchema = z.object({
  datasets: z.array(datasetDefinitionSchema).min(1),
  algorithms: z.array(datasetAlgorithmSchema).min(1)
});

const datasetTestRowSchema = z.object({
  sampleId: z.string().min(1),
  category: z.string().min(1),
  prompt: z.string(),
  status: z.enum(["complete", "error"]),
  passed: z.boolean(),
  detail: z.string(),
  original: z.string().optional(),
  steered: z.string().optional(),
  patched: z.string().optional(),
  diagnostics: z.record(z.string(), z.unknown()).optional()
});

const datasetTestResultSchema = z.object({
  dataset: z.object({
    id: z.string(), name: z.string(), version: z.string(), sampleCount: z.number().int()
  }),
  algorithm: z.object({
    id: z.enum(["steering", "patching"]),
    name: z.string(),
    implementation: z.string()
  }),
  execution: z.object({
    mode: z.string().optional(),
    source: z.literal("real-local-model"),
    model: z.string(),
    modelSource: z.string().optional(),
    revision: z.string().optional(),
    device: z.string().optional(),
    dtype: z.string().optional(),
    seed: z.number().int().optional(),
    layer: z.number().int().optional(),
    requestedLayer: z.number().int().optional(),
    component: z.string().optional(),
    maxNewTokens: z.number().int().optional()
  }),
  metric: datasetMetricSchema.extend({
    passed: z.number().int().nonnegative(),
    completed: z.number().int().nonnegative(),
    errors: z.number().int().nonnegative(),
    accuracy: z.number().min(0).max(1),
    meetsThreshold: z.boolean()
  }),
  rows: z.array(datasetTestRowSchema)
});

export const datasetTestJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("dataset-test"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    datasetId: z.string(),
    algorithmId: z.enum(["steering", "patching"]),
    model: z.string(),
    sampleIds: z.array(z.string()),
    layer: z.number().int(),
    strength: z.number(),
    seed: z.number().int(),
    maxNewTokens: z.number().int()
  }),
  result: datasetTestResultSchema.nullable(),
  error: z.string().nullable()
});

export type DatasetCatalog = z.infer<typeof datasetCatalogSchema>;
export type DatasetDefinition = z.infer<typeof datasetDefinitionSchema>;
export type DatasetAlgorithm = z.infer<typeof datasetAlgorithmSchema>;
export type DatasetTestJob = z.infer<typeof datasetTestJobSchema>;
export type DatasetTestResult = z.infer<typeof datasetTestResultSchema>;
export type DatasetTestInput = DatasetTestJob["request"];

const tokenizeResponseSchema = z.object({
  modelName: z.string().min(1),
  text: z.string(),
  tokens: z.array(z.object({
    index: z.number().int().nonnegative(),
    tokenId: z.number().int().nonnegative(),
    text: z.string()
  })),
  truncated: z.boolean()
});

export type TokenizedResponse = z.infer<typeof tokenizeResponseSchema>;

export const attributionJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("attribution"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    sourceRun: z.object({
      runId: z.string(),
      sampleId: z.string(),
      modelName: z.string()
    }),
    response: z.string(),
    objective: z.literal("response_token_logit"),
    targetResponseIndex: z.number().int().nonnegative(),
    baseline: z.enum(["pad_token", "zero_token_id"]),
    nSteps: z.number().int()
  }),
  result: explorerRunSchema.nullable(),
  error: z.string().nullable()
});

export type AttributionJob = z.infer<typeof attributionJobSchema>;
export type AttributionRunInput = Omit<AttributionJob["request"], "sourceRun"> & { run: ExplorerRun };

const nlaProfileSchema = z.object({
  name: z.string(),
  base_model: z.string(),
  layer: z.number().int(),
  component: z.string(),
  d_model: z.number().int().positive(),
  av_repo: z.string(),
  ar_repo: z.string().nullable(),
  av_revision: z.string().nullable().default(null),
  ar_revision: z.string().nullable().default(null),
  gated: z.boolean(),
  description: z.string()
});

export const nlaPreflightSchema = z.object({
  profile: z.string(),
  baseModel: z.string(),
  layer: z.number().int(),
  component: z.string(),
  dModel: z.number().int(),
  avRepo: z.string(),
  arRepo: z.string().nullable(),
  gated: z.boolean(),
  tokenConfigured: z.boolean(),
  modelMatches: z.boolean(),
  layerAvailable: z.boolean(),
  dModelMatches: z.boolean(),
  status: z.enum(["compatible", "incompatible", "authorization_required"]),
  canSubmit: z.boolean(),
  reason: z.string()
});

export const nlaJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("nla"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    profile: z.string(),
    positions: z.array(z.number().int()).min(1).max(8),
    revision: z.string(),
    maxNewTokens: z.number().int(),
    loadReconstructor: z.literal(true),
    confirmGatedAccess: z.boolean(),
    sourceRun: z.object({ runId: z.string(), sampleId: z.string(), modelName: z.string() }),
    preflight: nlaPreflightSchema
  }),
  result: explorerRunSchema.nullable(),
  error: z.string().nullable()
});

export type NLAProfile = z.infer<typeof nlaProfileSchema>;
export type NLAPreflight = z.infer<typeof nlaPreflightSchema>;
export type NLAJob = z.infer<typeof nlaJobSchema>;
export interface NLARunInput {
  run: ExplorerRun;
  profile: string;
  positions: number[];
  revision: string;
  maxNewTokens: number;
  loadReconstructor: true;
  confirmGatedAccess: boolean;
}

export const jLensOptionsSchema = z.object({
  packageInstalled: z.boolean(),
  defaultModel: z.string(),
  defaultSource: z.string(),
  defaultFilename: z.string().min(1),
  defaultRevision: z.string().min(1),
  profiles: z.array(z.object({
    name: z.string().min(1),
    baseModel: z.string().min(1),
    source: z.string().min(1),
    filename: z.string().min(1),
    revision: z.string().min(1),
    dModel: z.number().int().positive(),
    sourceLayers: z.array(z.number().int().nonnegative()).min(1),
    defaultLayer: z.number().int().nonnegative(),
    nPrompts: z.number().int().positive(),
    description: z.string().min(1)
  })).default([])
});

export const jLensPreflightSchema = z.object({
  packageInstalled: z.boolean(),
  modelAllowed: z.boolean(),
  layerAvailable: z.boolean(),
  positionValid: z.boolean(),
  lensConfigured: z.boolean(),
  artifactChecked: z.boolean(),
  fittedLayers: z.array(z.number().int().nonnegative()),
  lensDModel: z.number().int().positive().nullable(),
  canSubmit: z.boolean(),
  reason: z.string().min(1)
});

export const jLensJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("jlens"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    layer: z.number().int().nonnegative(),
    position: z.number().int().nonnegative(),
    lensSource: z.string().min(1),
    filename: z.string().min(1),
    revision: z.string().min(1),
    topK: z.number().int().min(3).max(50),
    sourceRun: z.object({ runId: z.string(), sampleId: z.string(), modelName: z.string() }),
    preflight: jLensPreflightSchema
  }),
  result: explorerRunSchema.nullable(),
  error: z.string().nullable()
});

export type JLensOptions = z.infer<typeof jLensOptionsSchema>;
export type JLensPreflight = z.infer<typeof jLensPreflightSchema>;
export type JLensJob = z.infer<typeof jLensJobSchema>;
export interface JLensRunInput {
  run: ExplorerRun;
  layer: number;
  position: number;
  lensSource: string;
  filename: string;
  revision: string;
  topK: number;
}

export const patchingPreflightSchema = z.object({
  modelAllowed: z.boolean(),
  promptsDiffer: z.boolean(),
  tokenCountMatches: z.boolean(),
  targetTokenValid: z.boolean(),
  componentSupported: z.boolean(),
  cleanTokenCount: z.number().int().positive(),
  corruptedTokenCount: z.number().int().nonnegative(),
  changedPositions: z.array(z.number().int().nonnegative()),
  targetTokenId: z.number().int().nonnegative(),
  targetTokenText: z.string(),
  corruptedTokens: z.array(z.object({
    index: z.number().int().nonnegative(),
    tokenId: z.number().int().nonnegative(),
    text: z.string(),
    changed: z.boolean()
  })),
  canSubmit: z.boolean(),
  reason: z.string()
});

export type ActivationComponent = "resid_post" | "attn_out" | "mlp_out";
export type PatchingComponent = ActivationComponent | "z";
export type PatchingPreflight = z.infer<typeof patchingPreflightSchema>;
export interface PatchingPreflightInput {
  modelName: string;
  cleanPrompt: string;
  corruptedPrompt: string;
  cleanTokenIds: number[];
  layers: number[];
  component: PatchingComponent;
  targetTokenId: number;
}

export const patchingJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("patching"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    corruptedPrompt: z.string(),
    component: z.enum(["resid_post", "attn_out", "z", "mlp_out"]),
    layers: z.array(z.number().int()).min(1),
    positions: z.array(z.number().int()).min(1),
    head: z.number().int().nonnegative().optional(),
    targetTokenId: z.number().int().nonnegative(),
    sourceRun: z.object({ runId: z.string(), sampleId: z.string(), modelName: z.string() }),
    preflight: patchingPreflightSchema
  }),
  result: explorerRunSchema.nullable(),
  error: z.string().nullable()
});

export type PatchingJob = z.infer<typeof patchingJobSchema>;
export interface PatchingRunInput {
  run: ExplorerRun;
  corruptedPrompt: string;
  component: PatchingComponent;
  layers: number[];
  positions: number[];
  head?: number;
  targetTokenId: number;
}

export const interventionPreflightSchema = z.object({
  mode: z.enum(["direction", "neuron", "sae_feature"]).default("direction"),
  modelAllowed: z.boolean(),
  layerAvailable: z.boolean(),
  componentSupported: z.boolean(),
  positionRangeValid: z.boolean(),
  targetTokenValid: z.boolean(),
  referencesDiffer: z.boolean(),
  featureAvailable: z.boolean().default(true),
  saeProfileValid: z.boolean().default(true),
  saeRuntimeAvailable: z.boolean().default(true),
  targetTokenId: z.number().int().nonnegative(),
  targetTokenText: z.string(),
  positionStart: z.number().int().nonnegative(),
  positionEnd: z.number().int().positive(),
  canSubmit: z.boolean(),
  reason: z.string()
});

export type InterventionPreflight = z.infer<typeof interventionPreflightSchema>;
export interface InterventionPreflightInput {
  mode?: "direction" | "neuron" | "sae_feature";
  modelName: string;
  promptTokenCount: number;
  availableLayers: number[];
  layer: number;
  sourceLayer?: number;
  injectLayer?: number;
  component: ActivationComponent;
  positionStart: number;
  positionEnd: number;
  targetTokenId: number;
  desiredPrompt?: string;
  undesiredPrompt?: string;
  positivePrompts?: string[];
  negativePrompts?: string[];
  activationReduce?: "last_token" | "mean";
  neuron?: number;
  availableNeurons?: number[];
  saeRelease?: string;
  saeId?: string;
  featureIndex?: number;
  saeOperation?: "add" | "ablate";
}

const saeProfileSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  modelName: z.string().min(1),
  release: z.string().min(1),
  saeId: z.string().min(1),
  layer: z.number().int().nonnegative(),
  component: z.literal("resid_post"),
  width: z.number().int().positive(),
  architecture: z.literal("jump_relu"),
  source: z.string().min(1)
});

export type SAEProfile = z.infer<typeof saeProfileSchema>;

const saeFeatureInfoSchema = z.object({
  modelName: z.string().min(1),
  layer: z.number().int().nonnegative(),
  featureIndex: z.number().int().nonnegative(),
  label: z.string().min(1),
  source: z.enum(["neuronpedia", "index"]),
  url: z.string().url().nullable().optional(),
  positiveTokens: z.array(z.string()).default([]),
  negativeTokens: z.array(z.string()).default([])
});

export type SAEFeatureInfo = z.infer<typeof saeFeatureInfoSchema>;

const saeFeatureCandidateSchema = z.object({
  featureIndex: z.number().int().nonnegative(),
  label: z.string().min(1),
  source: z.enum(["neuronpedia", "index"]),
  url: z.string().url().nullable().optional(),
  positiveTokens: z.array(z.string()).default([]),
  negativeTokens: z.array(z.string()).default([]),
  maxActivation: z.number().nonnegative(),
  meanActivation: z.number(),
  activeTokenCount: z.number().int().nonnegative(),
  peakTokenIndex: z.number().int().nonnegative(),
  peakTokenText: z.string(),
  recommendedDelta: z.number().positive()
});

const saeFeatureDiscoveryResultSchema = z.object({
  runId: z.string().min(1),
  sampleId: z.string().min(1),
  modelName: z.string().min(1),
  layer: z.number().int().nonnegative(),
  component: z.literal("resid_post"),
  release: z.string().min(1),
  saeId: z.string().min(1),
  positionStart: z.number().int().nonnegative(),
  positionEnd: z.number().int().positive(),
  candidates: z.array(saeFeatureCandidateSchema).max(20)
});

export type SAEFeatureCandidate = z.infer<typeof saeFeatureCandidateSchema>;
export type SAEFeatureDiscoveryResult = z.infer<typeof saeFeatureDiscoveryResultSchema>;

export const saeFeatureDiscoveryJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("sae-discovery"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    layer: z.number().int().nonnegative(),
    component: z.literal("resid_post"),
    saeRelease: z.string().min(1),
    saeId: z.string().min(1),
    positionStart: z.number().int().nonnegative(),
    positionEnd: z.number().int().positive(),
    limit: z.number().int().min(1).max(20),
    sourceRun: z.object({ runId: z.string(), sampleId: z.string(), modelName: z.string() })
  }),
  result: saeFeatureDiscoveryResultSchema.nullable(),
  error: z.string().nullable()
});

export type SAEFeatureDiscoveryJob = z.infer<typeof saeFeatureDiscoveryJobSchema>;
export interface SAEFeatureDiscoveryInput {
  run: ExplorerRun;
  layer: number;
  component: "resid_post";
  saeRelease: string;
  saeId: string;
  positionStart: number;
  positionEnd: number;
  limit: number;
}

export const interventionJobSchema = z.object({
  id: z.string().min(1),
  kind: z.literal("intervention"),
  status: z.enum(["idle", "loading", "ready", "error", "cancelled"]),
  stage: z.string(),
  progress: z.number().int().min(0).max(100),
  detail: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  request: z.object({
    mode: z.enum(["direction", "neuron", "sae_feature"]).default("direction"),
    desiredPrompt: z.string(),
    undesiredPrompt: z.string(),
    positivePrompts: z.array(z.string()).min(1).optional(),
    negativePrompts: z.array(z.string()).min(1).optional(),
    activationReduce: z.enum(["last_token", "mean"]).default("last_token"),
    layer: z.number().int().nonnegative(),
    sourceLayer: z.number().int().nonnegative().optional(),
    injectLayer: z.number().int().nonnegative().optional(),
    component: z.enum(["resid_post", "attn_out", "mlp_out"]),
    scale: z.number(),
    positionStart: z.number().int().nonnegative(),
    positionEnd: z.number().int().positive(),
    targetTokenId: z.number().int().nonnegative(),
    seed: z.number().int().nonnegative(),
    maxNewTokens: z.number().int().positive(),
    temperature: z.number().nonnegative(),
    neuron: z.number().int().nonnegative().nullish().transform((value) => value ?? undefined),
    saeRelease: z.string().min(1).nullish().transform((value) => value ?? undefined),
    saeId: z.string().min(1).nullish().transform((value) => value ?? undefined),
    featureIndex: z.number().int().nonnegative().nullish().transform((value) => value ?? undefined),
    saeOperation: z.enum(["add", "ablate"]).nullish().transform((value) => value ?? undefined),
    sourceRun: z.object({ runId: z.string(), sampleId: z.string(), modelName: z.string() }),
    preflight: interventionPreflightSchema
  }),
  result: explorerRunSchema.nullable(),
  error: z.string().nullable()
});

export type InterventionJob = z.infer<typeof interventionJobSchema>;
export interface InterventionRunInput {
  mode?: "direction" | "neuron" | "sae_feature";
  run: ExplorerRun;
  desiredPrompt?: string;
  undesiredPrompt?: string;
  positivePrompts?: string[];
  negativePrompts?: string[];
  activationReduce?: "last_token" | "mean";
  layer: number;
  sourceLayer?: number;
  injectLayer?: number;
  component: ActivationComponent;
  scale: number;
  positionStart: number;
  positionEnd: number;
  targetTokenId: number;
  seed: number;
  maxNewTokens: number;
  temperature: number;
  neuron?: number;
  saeRelease?: string;
  saeId?: string;
  featureIndex?: number;
  saeOperation?: "add" | "ablate";
}

export async function submitPromptJob(input: PromptRunInput): Promise<PromptJob> {
  const response = await fetch(`${API_BASE}/jobs/prompt`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    throw await jobResponseError(response, "prompt_submit_error");
  }
  return parsePromptJob(await response.json());
}

export async function fetchPromptOptions(signal?: AbortSignal): Promise<PromptOptions> {
  const response = await fetch(`${API_BASE}/prompt/options`, {
    headers: { Accept: "application/json" },
    signal
  });
  if (!response.ok) {
    throw await jobResponseError(response, "prompt_options_error");
  }
  const parsed = promptOptionsSchema.safeParse(await response.json());
  if (!parsed.success) {
    throw new ExplorerApiError(
      "prompt_options_invalid_schema",
      "Prompt options failed validation.",
      response.status
    );
  }
  return parsed.data;
}

export async function fetchDatasetCatalog(signal?: AbortSignal): Promise<DatasetCatalog> {
  const response = await fetch(`${API_BASE}/datasets`, {
    signal,
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!response.ok) throw await jobResponseError(response, "dataset_catalog_error");
  const parsed = datasetCatalogSchema.safeParse(await response.json());
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_dataset_catalog",
      `Dataset catalog failed validation: ${parsed.error.issues[0]?.message ?? "unknown error"}`
    );
  }
  return parsed.data;
}

export async function submitDatasetTestJob(input: DatasetTestInput): Promise<DatasetTestJob> {
  const response = await fetch(`${API_BASE}/jobs/dataset-test`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw await jobResponseError(response, "dataset_test_submit_error");
  return parseDatasetTestJob(await response.json());
}

export async function fetchDatasetTestJob(jobId: string): Promise<DatasetTestJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!response.ok) throw await jobResponseError(response, "dataset_test_status_error");
  return parseDatasetTestJob(await response.json());
}

export async function cancelDatasetTestJob(jobId: string): Promise<DatasetTestJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) throw await jobResponseError(response, "dataset_test_cancel_error");
  return parseDatasetTestJob(await response.json());
}

export async function fetchTokenizedResponse(
  modelName: string,
  text: string,
  signal?: AbortSignal
): Promise<TokenizedResponse> {
  const response = await fetch(`${API_BASE}/tokenize`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ modelName, text }),
    signal
  });
  if (!response.ok) {
    throw await jobResponseError(response, "tokenize_error");
  }
  const parsed = tokenizeResponseSchema.safeParse(await response.json());
  if (!parsed.success) {
    throw new ExplorerApiError("tokenize_invalid_schema", "Response tokenization failed validation.", response.status);
  }
  return parsed.data;
}

export async function cancelPromptJob(jobId: string): Promise<PromptJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw await jobResponseError(response, "prompt_cancel_error");
  }
  return parsePromptJob(await response.json());
}

export function promptJobEventsUrl(jobId: string) {
  return `${API_BASE}/jobs/${encodeURIComponent(jobId)}/events`;
}

export async function submitAttributionJob(input: AttributionRunInput): Promise<AttributionJob> {
  const response = await fetch(`${API_BASE}/jobs/attribution`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    throw await jobResponseError(response, "attribution_submit_error");
  }
  return parseAttributionJob(await response.json());
}

export async function cancelAttributionJob(jobId: string): Promise<AttributionJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw await jobResponseError(response, "attribution_cancel_error");
  }
  return parseAttributionJob(await response.json());
}

export async function fetchNlaProfiles(signal?: AbortSignal): Promise<NLAProfile[]> {
  const response = await fetch(`${API_BASE}/nla/profiles`, {
    signal,
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!response.ok) throw new ExplorerApiError("nla_profiles_error", await responseDetail(response));
  const parsed = z.array(nlaProfileSchema).safeParse(await response.json());
  if (!parsed.success) throw new ExplorerApiError("invalid_nla_profiles", parsed.error.message);
  return parsed.data;
}

export async function fetchNlaPreflight(
  input: { modelName: string; dModel: number; availableLayers: number[]; profile: string },
  signal?: AbortSignal
): Promise<NLAPreflight> {
  const response = await fetch(`${API_BASE}/nla/preflight`, {
    method: "POST",
    signal,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw new ExplorerApiError("nla_preflight_error", await responseDetail(response));
  const parsed = nlaPreflightSchema.safeParse(await response.json());
  if (!parsed.success) throw new ExplorerApiError("invalid_nla_preflight", parsed.error.message);
  return parsed.data;
}

export async function submitNlaJob(input: NLARunInput): Promise<NLAJob> {
  const response = await fetch(`${API_BASE}/jobs/nla`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw await jobResponseError(response, "nla_submit_error");
  return parseNlaJob(await response.json());
}

export async function cancelNlaJob(jobId: string): Promise<NLAJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) throw await jobResponseError(response, "nla_cancel_error");
  return parseNlaJob(await response.json());
}

export async function fetchJLensOptions(signal?: AbortSignal): Promise<JLensOptions> {
  const response = await fetch(`${API_BASE}/jlens/options`, {
    signal,
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!response.ok) throw new ExplorerApiError("jlens_options_error", await responseDetail(response));
  const parsed = jLensOptionsSchema.safeParse(await response.json());
  if (!parsed.success) throw new ExplorerApiError("invalid_jlens_options", parsed.error.message);
  return parsed.data;
}

export async function fetchJLensPreflight(
  input: Omit<JLensRunInput, "run" | "topK"> & {
    modelName: string;
    dModel: number;
    availableLayers: number[];
    tokenCount: number;
  },
  signal?: AbortSignal
): Promise<JLensPreflight> {
  const response = await fetch(`${API_BASE}/jlens/preflight`, {
    method: "POST",
    signal,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw new ExplorerApiError("jlens_preflight_error", await responseDetail(response));
  const parsed = jLensPreflightSchema.safeParse(await response.json());
  if (!parsed.success) throw new ExplorerApiError("invalid_jlens_preflight", parsed.error.message);
  return parsed.data;
}

export async function submitJLensJob(input: JLensRunInput): Promise<JLensJob> {
  const response = await fetch(`${API_BASE}/jobs/jlens`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw await jobResponseError(response, "jlens_submit_error");
  return parseJLensJob(await response.json());
}

export async function cancelJLensJob(jobId: string): Promise<JLensJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) throw await jobResponseError(response, "jlens_cancel_error");
  return parseJLensJob(await response.json());
}

export async function fetchPatchingPreflight(
  input: PatchingPreflightInput,
  signal?: AbortSignal
): Promise<PatchingPreflight> {
  const response = await fetch(`${API_BASE}/patching/preflight`, {
    method: "POST",
    signal,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw new ExplorerApiError("patching_preflight_error", await responseDetail(response));
  const parsed = patchingPreflightSchema.safeParse(await response.json());
  if (!parsed.success) throw new ExplorerApiError("invalid_patching_preflight", parsed.error.message);
  return parsed.data;
}

export async function submitPatchingJob(input: PatchingRunInput): Promise<PatchingJob> {
  const response = await fetch(`${API_BASE}/jobs/patching`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw await jobResponseError(response, "patching_submit_error");
  return parsePatchingJob(await response.json());
}

export async function cancelPatchingJob(jobId: string): Promise<PatchingJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) throw await jobResponseError(response, "patching_cancel_error");
  return parsePatchingJob(await response.json());
}

export async function fetchInterventionPreflight(
  input: InterventionPreflightInput,
  signal?: AbortSignal
): Promise<InterventionPreflight> {
  const response = await fetch(`${API_BASE}/intervention/preflight`, {
    method: "POST",
    signal,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw new ExplorerApiError("intervention_preflight_error", await responseDetail(response));
  const parsed = interventionPreflightSchema.safeParse(await response.json());
  if (!parsed.success) throw new ExplorerApiError("invalid_intervention_preflight", parsed.error.message);
  return parsed.data;
}

export async function fetchSAEProfiles(
  modelName: string,
  signal?: AbortSignal
): Promise<SAEProfile[]> {
  const params = new URLSearchParams({ modelName });
  const response = await fetch(`${API_BASE}/intervention/sae-profiles?${params}`, {
    signal,
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new ExplorerApiError("sae_profiles_error", await responseDetail(response));
  }
  const parsed = z.array(saeProfileSchema).safeParse(await response.json());
  if (!parsed.success) {
    throw new ExplorerApiError("invalid_sae_profiles", parsed.error.message);
  }
  return parsed.data;
}

export async function fetchSAEFeatureInfo(
  modelName: string,
  layer: number,
  featureIndex: number,
  signal?: AbortSignal
): Promise<SAEFeatureInfo> {
  const params = new URLSearchParams({
    modelName,
    layer: String(layer),
    featureIndex: String(featureIndex)
  });
  const response = await fetch(`${API_BASE}/intervention/sae-feature-info?${params}`, {
    signal,
    headers: { Accept: "application/json" },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new ExplorerApiError("sae_feature_info_error", await responseDetail(response));
  }
  const parsed = saeFeatureInfoSchema.safeParse(await response.json());
  if (!parsed.success) {
    throw new ExplorerApiError("invalid_sae_feature_info", parsed.error.message);
  }
  return parsed.data;
}

export async function submitSAEFeatureDiscoveryJob(
  input: SAEFeatureDiscoveryInput
): Promise<SAEFeatureDiscoveryJob> {
  const response = await fetch(`${API_BASE}/jobs/sae-discovery`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw await jobResponseError(response, "sae_discovery_submit_error");
  return parseSAEFeatureDiscoveryJob(await response.json());
}

export async function cancelSAEFeatureDiscoveryJob(
  jobId: string
): Promise<SAEFeatureDiscoveryJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) throw await jobResponseError(response, "sae_discovery_cancel_error");
  return parseSAEFeatureDiscoveryJob(await response.json());
}

export async function submitInterventionJob(input: InterventionRunInput): Promise<InterventionJob> {
  const response = await fetch(`${API_BASE}/jobs/intervention`, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) throw await jobResponseError(response, "intervention_submit_error");
  return parseInterventionJob(await response.json());
}

export async function cancelInterventionJob(jobId: string): Promise<InterventionJob> {
  const response = await fetch(`${API_BASE}/jobs/${encodeURIComponent(jobId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) throw await jobResponseError(response, "intervention_cancel_error");
  return parseInterventionJob(await response.json());
}

function parsePromptJob(input: unknown): PromptJob {
  const parsed = promptJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_job",
      `Prompt job response failed validation: ${parsed.error.issues[0]?.message ?? "unknown error"}`
    );
  }
  return parsed.data;
}

function parseAttributionJob(input: unknown): AttributionJob {
  const parsed = attributionJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_attribution_job",
      `Attribution job response failed validation: ${parsed.error.issues[0]?.message ?? "unknown error"}`
    );
  }
  return parsed.data;
}

function parseNlaJob(input: unknown): NLAJob {
  const parsed = nlaJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError("invalid_nla_job", `NLA job response failed validation: ${parsed.error.message}`);
  }
  return parsed.data;
}

function parseJLensJob(input: unknown): JLensJob {
  const parsed = jLensJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_jlens_job",
      `J-Lens job response failed validation: ${parsed.error.message}`
    );
  }
  return parsed.data;
}

function parsePatchingJob(input: unknown): PatchingJob {
  const parsed = patchingJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_patching_job",
      `Patching job response failed validation: ${parsed.error.message}`
    );
  }
  return parsed.data;
}

function parseInterventionJob(input: unknown): InterventionJob {
  const parsed = interventionJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_intervention_job",
      `Intervention job response failed validation: ${parsed.error.message}`
    );
  }
  return parsed.data;
}

function parseSAEFeatureDiscoveryJob(input: unknown): SAEFeatureDiscoveryJob {
  const parsed = saeFeatureDiscoveryJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_sae_discovery_job",
      `SAE feature discovery job failed validation: ${parsed.error.message}`
    );
  }
  return parsed.data;
}

function parseDatasetTestJob(input: unknown): DatasetTestJob {
  const parsed = datasetTestJobSchema.safeParse(input);
  if (!parsed.success) {
    throw new ExplorerApiError(
      "invalid_dataset_test_job",
      `Dataset test job failed validation: ${parsed.error.issues[0]?.message ?? "unknown error"}`
    );
  }
  return parsed.data;
}

async function responseDetail(response: Response) {
  try {
    const body = await response.json() as { detail?: string | { message?: string } };
    if (typeof body.detail === "string") return body.detail;
    if (body.detail?.message) return body.detail.message;
  } catch {
    // Fall through to the status label.
  }
  return `Explorer API returned HTTP ${response.status}.`;
}

async function jobResponseError(response: Response, fallbackCode: string) {
  let message = `Explorer API returned HTTP ${response.status}.`;
  let serverCode: string | undefined;
  try {
    const body = await response.json() as {
      detail?: string | { code?: string; message?: string };
    };
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (body.detail) {
      if (typeof body.detail.message === "string") message = body.detail.message;
      if (typeof body.detail.code === "string") serverCode = body.detail.code;
    }
  } catch {
    // The status remains useful even when an upstream proxy returns non-JSON.
  }
  return new ExplorerApiError(fallbackCode, message, response.status, serverCode);
}
