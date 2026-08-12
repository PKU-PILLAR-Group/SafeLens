import { z } from "zod";

import type { ExplorerRun } from "../types";

const tokenSchema = z.object({
  index: z.number().int().nonnegative(),
  text: z.string(),
  tokenId: z.number().int(),
  source: z.enum(["prompt", "reply"]),
  risk: z.number().finite(),
  attribution: z.number().finite(),
  isSpecial: z.boolean().optional(),
  generationStep: z.number().int().nonnegative().optional(),
  probeScore: z.number().finite().optional(),
  monitorHit: z.boolean().optional()
});

const nlaRowSchema = z.object({
  tokenIndex: z.number().int().nonnegative(),
  layer: z.number().int().nonnegative(),
  component: z.enum(["resid_post", "attn_result", "mlp_out"]),
  explanation: z.string(),
  cosine: z.number().finite(),
  mse: z.number().finite(),
  fve: z.number().finite().optional(),
  activationNorm: z.number().finite(),
  status: z.enum(["available", "unavailable"]).optional(),
  profile: z.string().nullable().optional(),
  source: z.string().optional(),
  token: z.string().optional()
});

const nlaCompatibilitySchema = z.object({
  modelName: z.string().min(1),
  dModel: z.number().int().positive(),
  availableLayers: z.array(z.number().int().nonnegative()).min(1),
  profiles: z.array(z.object({
    name: z.string().min(1),
    baseModel: z.string().min(1),
    layer: z.number().int().nonnegative(),
    component: z.string().min(1),
    dModel: z.number().int().positive(),
    modelMatches: z.boolean(),
    layerAvailable: z.boolean(),
    dModelMatches: z.boolean(),
    status: z.enum(["compatible", "artifact_missing", "incompatible"]),
    reason: z.string().min(1)
  }))
});

const attentionHeadSchema = z.object({
  id: z.string().min(1),
  layer: z.number().int().nonnegative(),
  head: z.number().int().nonnegative(),
  role: z.string(),
  riskContribution: z.number().finite(),
  entropy: z.number().finite(),
  distributionByToken: z.array(z.array(z.number().finite()))
});

const mlpNeuronSchema = z.object({
  id: z.string().min(1),
  layer: z.number().int().nonnegative(),
  neuron: z.number().int().nonnegative(),
  label: z.string(),
  activation: z.number().finite(),
  riskContribution: z.number().finite(),
  topTokens: z.array(z.number().int().nonnegative()),
  positiveTopTokens: z.array(z.number().int().nonnegative()),
  negativeTopTokens: z.array(z.number().int().nonnegative()),
  activationsByToken: z.array(z.number().finite()),
  maxAbsoluteActivation: z.number().finite().nonnegative()
});

const residualCellSchema = z.object({
  layer: z.number().int().nonnegative(),
  tokenIndex: z.number().int().nonnegative(),
  norm: z.number().finite(),
  rawDirection: z.number().finite(),
  riskDirection: z.number().finite(),
  semanticDensity: z.number().finite()
});

const logitPredictionSchema = z.object({
  tokenId: z.number().int(),
  tokenText: z.string(),
  logit: z.number().finite(),
  probability: z.number().finite().nonnegative()
});

const logitLensSchema = z.object({
  layer: z.number().int().nonnegative(),
  tokenIndex: z.number().int().nonnegative(),
  targetTokenId: z.number().int(),
  targetTokenText: z.string(),
  targetLogit: z.number().finite(),
  targetProbability: z.number().finite().nonnegative(),
  targetRank: z.number().int().positive(),
  topPredictions: z.array(logitPredictionSchema).min(1),
  sourceKey: z.string().min(1)
});

export const jLensRowSchema = logitLensSchema.extend({
  modelTopPredictions: z.array(logitPredictionSchema).min(1),
  lensSource: z.string().min(1),
  filename: z.string().min(1),
  revision: z.string().min(1),
  nPrompts: z.number().int().positive()
});

const componentCellSchema = z.object({
  layer: z.number().int().nonnegative(),
  tokenIndex: z.number().int().nonnegative(),
  value: z.number().finite(),
  rawValue: z.number().finite(),
  metric: z.string().min(1),
  sourceKey: z.string().min(1)
});

const metricProvenanceSchema = z.object({
  label: z.string().min(1),
  method: z.string().min(1),
  semantics: z.string().min(1),
  normalization: z.string().min(1),
  kind: z.enum(["raw", "derived_proxy", "safety_method", "causal"])
});

const attributionMethodSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  description: z.string().min(1),
  evidenceKind: z.enum(["raw", "derived_proxy", "safety_method", "causal"]),
  signed: z.boolean(),
  normalization: z.string().min(1),
  available: z.boolean(),
  unavailableReason: z.string().optional(),
  rows: z.array(z.object({
    layer: z.number().int(),
    label: z.string().min(1),
    values: z.array(z.number().finite()),
    sourceKey: z.string().min(1)
  }))
}).superRefine((method, context) => {
  if (!method.available && !method.unavailableReason) {
    context.addIssue({
      code: "custom",
      path: ["unavailableReason"],
      message: "is required when the attribution method is unavailable"
    });
  }
});

const patchingExperimentSchema = z.object({
  cleanPrompt: z.string(),
  corruptedPrompt: z.string(),
  component: z.enum(["resid_post", "attn_out", "mlp_out"]),
  targetTokenId: z.number().int().nonnegative(),
  targetTokenText: z.string(),
  cleanScore: z.number().finite(),
  corruptedScore: z.number().finite(),
  denominator: z.number().finite(),
  layers: z.array(z.number().int().nonnegative()).min(1),
  positions: z.array(z.number().int().nonnegative()).min(1),
  corruptedTokens: z.array(z.object({
    index: z.number().int().nonnegative(),
    tokenId: z.number().int().nonnegative(),
    text: z.string(),
    changed: z.boolean()
  })).min(1),
  cells: z.array(z.object({
    layer: z.number().int().nonnegative(),
    tokenIndex: z.number().int().nonnegative(),
    patchedScore: z.number().finite(),
    causalEffect: z.number().finite(),
    recoveryPercentage: z.number().finite().nullable(),
    sourceKey: z.string().min(1)
  })).min(1),
  sourceRun: z.object({ runId: z.string().min(1), sampleId: z.string().min(1) }),
  sourceKey: z.string().min(1)
});

const interventionOutputSchema = z.object({
  text: z.string(),
  tokenIds: z.array(z.number().int().nonnegative()),
  tokens: z.array(z.object({
    index: z.number().int().nonnegative(),
    tokenId: z.number().int().nonnegative(),
    text: z.string()
  })),
  targetLogit: z.number().finite(),
  lexicalRisk: z.number().finite().nonnegative()
});

const interventionExperimentSchema = z.object({
  vector: z.object({
    method: z.string().min(1),
    desiredPrompt: z.string().min(1),
    undesiredPrompt: z.string().min(1),
    activationReduce: z.string().min(1),
    rawNorm: z.number().finite().positive(),
    normalized: z.boolean(),
    dimension: z.number().int().positive(),
    sourceKey: z.string().min(1)
  }),
  layer: z.number().int().nonnegative(),
  component: z.enum(["resid_post", "attn_out", "mlp_out"]),
  scale: z.number().finite(),
  positionStart: z.number().int().nonnegative(),
  positionEnd: z.number().int().positive(),
  targetTokenId: z.number().int().nonnegative(),
  targetTokenText: z.string(),
  seed: z.number().int().nonnegative(),
  maxNewTokens: z.number().int().positive(),
  temperature: z.number().finite().nonnegative(),
  original: interventionOutputSchema,
  steered: interventionOutputSchema,
  deltas: z.object({
    targetLogit: z.number().finite(),
    lexicalRisk: z.number().finite(),
    tokenEditDistance: z.number().int().nonnegative(),
    generationChanged: z.boolean(),
    probeScore: z.number().finite().nullable(),
    probeReason: z.string().min(1)
  }),
  diff: z.array(z.object({
    kind: z.enum(["equal", "replace", "delete", "insert"]),
    originalStart: z.number().int().nonnegative(),
    originalEnd: z.number().int().nonnegative(),
    steeredStart: z.number().int().nonnegative(),
    steeredEnd: z.number().int().nonnegative()
  })),
  sourceRun: z.object({ runId: z.string().min(1), sampleId: z.string().min(1) })
});

export const explorerRunCoreSchema = z.object({
  runId: z.string().min(1),
  modelName: z.string().min(1),
  modelSource: z.string().min(1),
  sampleId: z.string().min(1),
  prompt: z.string(),
  tokens: z.array(tokenSchema).min(1),
  layers: z.array(z.number().int().nonnegative()).min(1),
  nlaCompatibility: nlaCompatibilitySchema,
  metricProvenance: z.record(z.string(), metricProvenanceSchema),
  metadata: z.record(z.string(), z.unknown()).optional()
}).superRefine((run, context) => {
  if (new Set(run.layers).size !== run.layers.length) {
    context.addIssue({ code: "custom", path: ["layers"], message: "must not contain duplicates" });
  }
  run.tokens.forEach((token, index) => {
    if (token.index !== index) {
      context.addIssue({
        code: "custom",
        path: ["tokens", index, "index"],
        message: `must equal its array position (${index})`
      });
    }
  });
});

export const explorerRunSchema = z.object({
  runId: z.string().min(1),
  modelName: z.string().min(1),
  modelSource: z.string().min(1),
  sampleId: z.string().min(1),
  prompt: z.string(),
  tokens: z.array(tokenSchema).min(1),
  layers: z.array(z.number().int().nonnegative()).min(1),
  nla: z.array(nlaRowSchema),
  nlaCompatibility: nlaCompatibilitySchema,
  attentionHeads: z.array(attentionHeadSchema).min(1),
  mlpNeurons: z.array(mlpNeuronSchema).min(1),
  residualCells: z.array(residualCellSchema).min(1),
  logitLens: z.array(logitLensSchema).min(1),
  jLens: z.array(jLensRowSchema).default([]),
  attentionCells: z.array(componentCellSchema).min(1),
  mlpCells: z.array(componentCellSchema).min(1),
  attributionTracks: z.array(z.object({
    name: z.string().min(1),
    values: z.array(z.number().finite())
  })),
  attributionMethods: z.array(attributionMethodSchema).min(1),
  patching: patchingExperimentSchema.optional(),
  intervention: interventionExperimentSchema.optional(),
  metricProvenance: z.record(z.string(), metricProvenanceSchema),
  metadata: z.record(z.string(), z.unknown()).optional()
}).superRefine((run, context) => {
  const tokenCount = run.tokens.length;
  const layerSet = new Set(run.layers);
  run.tokens.forEach((token, index) => {
    if (token.index !== index) {
      context.addIssue({
        code: "custom",
        path: ["tokens", index, "index"],
        message: `must equal its array position (${index})`
      });
    }
  });
  if (layerSet.size !== run.layers.length) {
    context.addIssue({ code: "custom", path: ["layers"], message: "must not contain duplicates" });
  }
  run.attentionHeads.forEach((head, index) => {
    if (!layerSet.has(head.layer)) {
      context.addIssue({ code: "custom", path: ["attentionHeads", index, "layer"], message: "is not declared in layers" });
    }
    if (head.distributionByToken.length !== tokenCount || head.distributionByToken.some((row) => row.length !== tokenCount)) {
      context.addIssue({
        code: "custom",
        path: ["attentionHeads", index, "distributionByToken"],
        message: `must be a ${tokenCount}×${tokenCount} destination×source matrix`
      });
    }
  });
  run.mlpNeurons.forEach((neuron, index) => {
    if (neuron.activationsByToken.length !== tokenCount) {
      context.addIssue({
        code: "custom",
        path: ["mlpNeurons", index, "activationsByToken"],
        message: `must contain one value per token (${tokenCount})`
      });
    }
  });
  run.attributionMethods.forEach((method, methodIndex) => {
    method.rows.forEach((row, rowIndex) => {
      if (row.values.length !== tokenCount) {
        context.addIssue({
          code: "custom",
          path: ["attributionMethods", methodIndex, "rows", rowIndex, "values"],
          message: `must contain one value per token (${tokenCount})`
        });
      }
    });
  });
  for (const [collectionName, cells] of [
    ["residualCells", run.residualCells],
    ["attentionCells", run.attentionCells],
    ["mlpCells", run.mlpCells]
  ] as const) {
    cells.forEach((cell, index) => {
      if (!layerSet.has(cell.layer)) {
        context.addIssue({ code: "custom", path: [collectionName, index, "layer"], message: "is not declared in layers" });
      }
      if (cell.tokenIndex >= tokenCount) {
        context.addIssue({ code: "custom", path: [collectionName, index, "tokenIndex"], message: "is outside the token array" });
      }
    });
  }
});

const artifactEnvelopeSchema = z.object({
  schema_version: z.literal("1.0"),
  samples: z.array(explorerRunSchema).min(1)
});

export interface ArtifactDiagnostic {
  path: string;
  issueType: string;
  expected: string;
  actual: string;
  message: string;
}

export type ArtifactParseResult =
  | { success: true; schemaVersion: "1.0" | "legacy"; runs: ExplorerRun[] }
  | { success: false; diagnostics: ArtifactDiagnostic[] };

export function parseExplorerArtifact(input: unknown): ArtifactParseResult {
  if (isRecord(input) && "schema_version" in input) {
    if (input.schema_version !== "1.0") {
      return {
        success: false,
        diagnostics: [{
          path: "schema_version",
          issueType: "unsupported_schema_version",
          expected: '"1.0"',
          actual: describeDiagnosticValue(input.schema_version),
          message: `unsupported schema version ${JSON.stringify(input.schema_version)}; expected "1.0"`
        }]
      };
    }
    const parsed = artifactEnvelopeSchema.safeParse(input);
    return parsed.success
      ? { success: true, schemaVersion: "1.0", runs: parsed.data.samples as ExplorerRun[] }
      : { success: false, diagnostics: formatArtifactIssues(parsed.error.issues, input) };
  }

  const parsed = explorerRunSchema.safeParse(input);
  return parsed.success
    ? { success: true, schemaVersion: "legacy", runs: [parsed.data as ExplorerRun] }
    : { success: false, diagnostics: formatArtifactIssues(parsed.error.issues, input) };
}

export function formatArtifactIssues(
  issues: z.core.$ZodIssue[],
  input?: unknown
): ArtifactDiagnostic[] {
  return issues.slice(0, 12).map((issue) => ({
    path: issue.path.length > 0 ? issue.path.join(".") : "artifact",
    issueType: issue.code,
    expected: diagnosticExpectation(issue),
    actual: describeDiagnosticValue(valueAtDiagnosticPath(input, issue.path)),
    message: issue.message
  }));
}

function diagnosticExpectation(issue: z.core.$ZodIssue): string {
  switch (issue.code) {
    case "invalid_type":
      return issue.expected;
    case "invalid_value":
      return issue.values.map(describeDiagnosticValue).join(" or ");
    case "too_small":
      return `${issue.origin} ${issue.exact ? "length =" : issue.inclusive === false ? ">" : ">="} ${String(issue.minimum)}`;
    case "too_big":
      return `${issue.origin} ${issue.exact ? "length =" : issue.inclusive === false ? "<" : "<="} ${String(issue.maximum)}`;
    case "invalid_format":
      return `${issue.format} format`;
    case "not_multiple_of":
      return `multiple of ${issue.divisor}`;
    case "unrecognized_keys":
      return "declared schema fields only";
    case "invalid_union":
      return "one supported schema variant";
    case "invalid_key":
      return `valid ${issue.origin} key`;
    case "invalid_element":
      return `valid ${issue.origin} element`;
    case "custom":
      return typeof issue.params?.expected === "string" ? issue.params.expected : issue.message;
  }
}

function describeDiagnosticValue(value: unknown): string {
  if (value === undefined) return "missing";
  if (value === null) return "null";
  if (Array.isArray(value)) return `array(length ${value.length})`;
  if (typeof value === "string") return truncateDiagnosticValue(JSON.stringify(value));
  if (typeof value === "number" || typeof value === "boolean" || typeof value === "bigint") {
    return String(value);
  }
  if (typeof value === "object") {
    const keys = Object.keys(value);
    const preview = keys.slice(0, 4).join(", ");
    return `object(${keys.length} key${keys.length === 1 ? "" : "s"}${preview ? `: ${preview}${keys.length > 4 ? ", ..." : ""}` : ""})`;
  }
  return typeof value;
}

function truncateDiagnosticValue(value: string): string {
  return value.length <= 96 ? value : `${value.slice(0, 93)}...`;
}

function valueAtDiagnosticPath(input: unknown, path: PropertyKey[]): unknown {
  let current = input;
  for (const key of path) {
    if (current === null || typeof current !== "object") return undefined;
    current = (current as Record<PropertyKey, unknown>)[key];
  }
  return current;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
