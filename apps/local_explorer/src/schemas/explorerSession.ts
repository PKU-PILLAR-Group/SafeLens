import { z } from "zod";

import type { ExplorerSelectionState, PinnedEvidence } from "../types";

export const EXPLORER_SESSION_KIND = "safelens-explorer-session";

const workspaceViewSchema = z.enum([
  "overview",
  "residual",
  "attention",
  "mlp",
  "nla",
  "patching",
  "intervention",
  "attribution"
]);

const provenanceSchema = z.object({
  label: z.string(),
  method: z.string(),
  semantics: z.string(),
  normalization: z.string(),
  kind: z.enum(["raw", "derived_proxy", "safety_method", "causal"])
});

const evidenceAssessmentSchema = z.object({
  schemaVersion: z.literal("1.0"),
  status: z.enum(["available", "unavailable", "incompatible", "not-computed", "failed", "loading", "cancelled"]),
  statusReason: z.string(),
  primaryLabel: z.string(),
  primaryValue: z.string(),
  rawValue: z.string(),
  displayValue: z.string(),
  units: z.string(),
  evidenceClass: z.enum(["raw", "derived_proxy", "safety_method", "causal"]),
  method: z.string(),
  normalization: z.string(),
  cacheKey: z.string(),
  shape: z.string(),
  sourceArtifact: z.string(),
  warnings: z.array(z.string()),
  reproduction: z.record(z.string(), z.unknown())
});

const evidenceProfileSchema = z.object({
  schemaVersion: z.literal("1.0"),
  kind: z.enum([
    "attention_source_profile",
    "signed_attribution_profile",
    "mlp_activation_profile"
  ]),
  label: z.string().min(1),
  axis: z.enum(["source_token", "token"]),
  signed: z.boolean(),
  originalLength: z.number().int().positive(),
  sampled: z.boolean(),
  points: z.array(z.object({
    tokenIndex: z.number().int().nonnegative(),
    tokenId: z.number().int().optional(),
    tokenText: z.string(),
    value: z.number().finite()
  })).min(1).max(256)
});

const matrixAxisPointSchema = z.object({
  tokenIndex: z.number().int().nonnegative(),
  tokenId: z.number().int().optional(),
  tokenText: z.string()
});

const attentionMatrixSchema = z.object({
  schemaVersion: z.literal("1.0"),
  kind: z.literal("attention_matrix"),
  label: z.string().min(1),
  originalSize: z.number().int().positive(),
  sampled: z.boolean(),
  axis: z.array(matrixAxisPointSchema).min(1).max(64),
  values: z.array(z.array(z.number().finite().min(0).max(1).nullable()).max(64)).max(64)
}).superRefine((matrix, context) => {
  if (matrix.originalSize < matrix.axis.length) {
    context.addIssue({ code: "custom", path: ["originalSize"], message: "must cover the stored axis" });
  }
  if (matrix.sampled === (matrix.originalSize === matrix.axis.length)) {
    context.addIssue({ code: "custom", path: ["sampled"], message: "must agree with originalSize" });
  }
  matrix.axis.forEach((point, index) => {
    if (index > 0 && point.tokenIndex <= matrix.axis[index - 1].tokenIndex) {
      context.addIssue({ code: "custom", path: ["axis", index, "tokenIndex"], message: "must be strictly increasing" });
    }
  });
  if (matrix.values.length !== matrix.axis.length) {
    context.addIssue({ code: "custom", path: ["values"], message: "row count must match axis" });
  }
  matrix.values.forEach((row, destination) => {
    if (row.length !== matrix.axis.length) {
      context.addIssue({ code: "custom", path: ["values", destination], message: "column count must match axis" });
      return;
    }
    row.forEach((value, source) => {
      const masked = matrix.axis[source].tokenIndex > matrix.axis[destination].tokenIndex;
      if ((masked && value !== null) || (!masked && value === null)) {
        context.addIssue({
          code: "custom",
          path: ["values", destination, source],
          message: masked ? "causal mask must be null" : "unmasked attention must be finite"
        });
      }
    });
  });
});

const generationOutputSnapshotSchema = z.object({
  text: z.string(),
  tokens: z.array(z.object({
    index: z.number().int().nonnegative(),
    tokenId: z.number().int(),
    text: z.string()
  })).max(256),
  targetLogit: z.number().finite(),
  lexicalRisk: z.number().finite()
});

const interventionGenerationSchema = z.object({
  schemaVersion: z.literal("1.0"),
  sourceRun: z.object({
    runId: z.string().min(1),
    sampleId: z.string().min(1)
  }),
  layer: z.number().int().nonnegative(),
  component: z.enum(["resid_post", "attn_out", "mlp_out"]),
  scale: z.number().finite(),
  positionStart: z.number().int().nonnegative(),
  positionEnd: z.number().int().positive(),
  targetTokenId: z.number().int(),
  targetTokenText: z.string(),
  seed: z.number().int(),
  maxNewTokens: z.number().int().min(1).max(256),
  temperature: z.number().finite().nonnegative(),
  original: generationOutputSnapshotSchema,
  steered: generationOutputSnapshotSchema,
  tokenEditDistance: z.number().int().nonnegative(),
  generationChanged: z.boolean(),
  diff: z.array(z.object({
    kind: z.enum(["equal", "replace", "delete", "insert"]),
    originalStart: z.number().int().nonnegative(),
    originalEnd: z.number().int().nonnegative(),
    steeredStart: z.number().int().nonnegative(),
    steeredEnd: z.number().int().nonnegative()
  })).max(512)
}).superRefine((generation, context) => {
  if (generation.positionEnd <= generation.positionStart) {
    context.addIssue({ code: "custom", path: ["positionEnd"], message: "must be greater than positionStart" });
  }
  for (const side of ["original", "steered"] as const) {
    const output = generation[side];
    if (output.tokens.length > generation.maxNewTokens) {
      context.addIssue({ code: "custom", path: [side, "tokens"], message: "exceeds maxNewTokens" });
    }
    output.tokens.forEach((token, index) => {
      if (token.index !== index) {
        context.addIssue({ code: "custom", path: [side, "tokens", index, "index"], message: "must be contiguous" });
      }
    });
  }
  if (generation.generationChanged !== (generation.tokenEditDistance > 0)) {
    context.addIssue({ code: "custom", path: ["generationChanged"], message: "must agree with tokenEditDistance" });
  }
  let originalCursor = 0;
  let steeredCursor = 0;
  generation.diff.forEach((row, index) => {
    const path = ["diff", index];
    const originalLength = row.originalEnd - row.originalStart;
    const steeredLength = row.steeredEnd - row.steeredStart;
    if (row.originalStart !== originalCursor || row.steeredStart !== steeredCursor) {
      context.addIssue({ code: "custom", path, message: "opcodes must cover both sequences contiguously" });
    }
    if (
      originalLength < 0 || steeredLength < 0 ||
      (row.kind === "equal" && (originalLength === 0 || originalLength !== steeredLength)) ||
      (row.kind === "replace" && (originalLength === 0 || steeredLength === 0)) ||
      (row.kind === "delete" && (originalLength === 0 || steeredLength !== 0)) ||
      (row.kind === "insert" && (originalLength !== 0 || steeredLength === 0))
    ) {
      context.addIssue({ code: "custom", path, message: "opcode span does not match its kind" });
    }
    originalCursor = row.originalEnd;
    steeredCursor = row.steeredEnd;
  });
  if (
    originalCursor !== generation.original.tokens.length ||
    steeredCursor !== generation.steered.tokens.length
  ) {
    context.addIssue({ code: "custom", path: ["diff"], message: "opcodes must cover every generated token" });
  }
});

const pinnedEvidenceSchema = z.object({
  id: z.string().min(1),
  runId: z.string().min(1),
  sampleId: z.string().min(1),
  tokenIndex: z.number().int().nonnegative(),
  tokenText: z.string(),
  tokenId: z.number().int().optional(),
  tokenSource: z.enum(["prompt", "reply"]).optional(),
  modelName: z.string().optional(),
  modelSource: z.string().optional(),
  layer: z.number().int().nonnegative(),
  view: workspaceViewSchema,
  component: z.string(),
  metric: z.string().min(1),
  value: z.number().finite(),
  normalization: z.enum(["raw", "normalized"]),
  headId: z.string().optional(),
  neuronId: z.string().optional(),
  trackName: z.string().optional(),
  sourceTokenIndex: z.number().int().nonnegative().optional(),
  sourceKey: z.string().optional(),
  provenance: provenanceSchema.optional(),
  profile: evidenceProfileSchema.optional(),
  matrix: attentionMatrixSchema.optional(),
  generation: interventionGenerationSchema.optional(),
  assessment: evidenceAssessmentSchema.optional(),
  capturedAt: z.string().optional()
}).superRefine((evidence, context) => {
  if (!evidence.matrix) return;
  if (evidence.view !== "attention" || !evidence.headId) {
    context.addIssue({ code: "custom", path: ["matrix"], message: "matrix snapshot requires attention head evidence" });
  }
  const tokenIndices = new Set(evidence.matrix.axis.map((point) => point.tokenIndex));
  if (!tokenIndices.has(evidence.tokenIndex)) {
    context.addIssue({ code: "custom", path: ["matrix", "axis"], message: "must include selected destination token" });
  }
  if (evidence.sourceTokenIndex === undefined || !tokenIndices.has(evidence.sourceTokenIndex)) {
    context.addIssue({ code: "custom", path: ["matrix", "axis"], message: "must include selected source token" });
  }
});

const selectionSchema = z.object({
  view: workspaceViewSchema,
  tokenIndex: z.number().int().nonnegative(),
  sourceTokenIndex: z.number().int().nonnegative().optional(),
  targetTokenIndex: z.number().int().nonnegative().optional(),
  tokenRange: z.tuple([
    z.number().int().nonnegative(),
    z.number().int().nonnegative()
  ]).optional(),
  layer: z.number().int().nonnegative(),
  headId: z.string(),
  attentionEdgeMode: z.enum(["incoming", "outgoing"]).default("incoming"),
  nlaComponent: z.enum(["resid_post", "attn_result", "mlp_out"]).default("resid_post"),
  neuronId: z.string(),
  trackName: z.string(),
  metric: z.string().min(1),
  normalization: z.enum(["raw", "normalized"])
});

const matrixViewportSchema = z.object({
  size: z.number().int().min(8).max(64),
  mode: z.enum(["select", "pan"]),
  axesPinned: z.boolean(),
  fitMode: z.enum(["manual", "fit"])
});

export const explorerSessionSchema = z.object({
  kind: z.literal(EXPLORER_SESSION_KIND),
  schemaVersion: z.literal("1.0"),
  exportedAt: z.string(),
  workspace: z.object({
    runId: z.string().min(1),
    sampleId: z.string().min(1),
    modelName: z.string().optional(),
    modelSource: z.string().optional(),
    sourceName: z.string().optional(),
    artifactId: z.string().optional()
  }),
  selection: selectionSchema,
  pinnedItems: z.array(pinnedEvidenceSchema).max(4),
  timeline: z.object({
    mode: z.enum(["token", "word"]),
    metric: z.enum(["risk", "attribution", "residual", "nla", "probe"]),
    query: z.string().max(256)
  }).optional(),
  compare: z.object({
    baselineId: z.string().optional()
  }).optional(),
  activeEvidenceAssessment: evidenceAssessmentSchema.optional(),
  matrices: z.object({
    residual: matrixViewportSchema.optional(),
    attention: matrixViewportSchema.optional(),
    mlp: matrixViewportSchema.optional(),
    attribution: matrixViewportSchema.optional(),
    nla: matrixViewportSchema.optional(),
    patching: matrixViewportSchema.optional()
  }).optional(),
  filters: z.object({
    evidence: z.enum(["top", "neighborhood", "all"])
  })
});

export type ExplorerSession = Omit<z.infer<typeof explorerSessionSchema>, "selection" | "pinnedItems"> & {
  selection: Omit<ExplorerSelectionState, "pinnedItems">;
  pinnedItems: PinnedEvidence[];
};

export function isExplorerSessionCandidate(value: unknown) {
  return Boolean(
    value &&
    typeof value === "object" &&
    (value as { kind?: unknown }).kind === EXPLORER_SESSION_KIND
  );
}
