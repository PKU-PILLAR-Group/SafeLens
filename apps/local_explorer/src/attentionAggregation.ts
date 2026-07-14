import type {
  AttentionAggregation,
  AttentionHead,
  MetricProvenance
} from "./types";

export const ATTENTION_AGGREGATION_OPTIONS: Array<{
  id: "individual" | "difference" | "rollout" | AttentionAggregation;
  label: string;
  description: string;
}> = [
  { id: "individual", label: "Head", description: "Show one retained attention head." },
  {
    id: "difference",
    label: "Difference",
    description: "Cell-wise selected retained head minus baseline retained head."
  },
  { id: "mean", label: "Mean", description: "Cell-wise mean over retained heads in this layer." },
  { id: "max", label: "Max", description: "Cell-wise maximum over retained heads in this layer." },
  {
    id: "rollout",
    label: "Rollout",
    description: "Retained-head mean with identity residual, multiplied through the current layer."
  },
  {
    id: "entropy_weighted",
    label: "Entropy",
    description: "Weighted mean using normalized inverse stored head entropy."
  }
];

const AGGREGATE_PREFIX = "aggregate:";
const DIFFERENCE_PREFIX = "difference:";
const ROLLOUT_ID = "rollout:retained_mean_identity";

export function attentionAggregationId(aggregation: AttentionAggregation) {
  return `${AGGREGATE_PREFIX}${aggregation}`;
}

export function parseAttentionAggregation(value: string | undefined): AttentionAggregation | undefined {
  if (!value?.startsWith(AGGREGATE_PREFIX)) return undefined;
  const aggregation = value.slice(AGGREGATE_PREFIX.length);
  return aggregation === "mean" || aggregation === "max" || aggregation === "entropy_weighted"
    ? aggregation
    : undefined;
}

export function attentionDifferenceId(selectedHeadId: string, baselineHeadId: string) {
  return `${DIFFERENCE_PREFIX}${encodeURIComponent(selectedHeadId)}:${encodeURIComponent(baselineHeadId)}`;
}

export function parseAttentionDifference(value: string | undefined) {
  if (!value?.startsWith(DIFFERENCE_PREFIX)) return undefined;
  const [selected, baseline, ...rest] = value.slice(DIFFERENCE_PREFIX.length).split(":");
  if (!selected || !baseline || rest.length > 0) return undefined;
  try {
    const selectedHeadId = decodeURIComponent(selected);
    const baselineHeadId = decodeURIComponent(baseline);
    return selectedHeadId !== baselineHeadId ? { selectedHeadId, baselineHeadId } : undefined;
  } catch {
    return undefined;
  }
}

export function attentionRolloutId() {
  return ROLLOUT_ID;
}

export function parseAttentionRollout(value: string | undefined) {
  return value === ROLLOUT_ID
    ? { fusion: "retained_mean" as const, residual: "identity" as const }
    : undefined;
}

export function attentionAggregationLabel(aggregation: AttentionAggregation) {
  if (aggregation === "entropy_weighted") return "Entropy-weighted retained heads";
  return `${aggregation === "mean" ? "Mean" : "Max"} retained heads`;
}

export function attentionHeadLabel(head: AttentionHead) {
  if (head.rollout) {
    return `Retained attention rollout · L${head.rollout.layers[0]}–L${head.layer}`;
  }
  if (head.difference) {
    return `${head.difference.selectedHeadId} - ${head.difference.baselineHeadId}`;
  }
  return head.aggregation ? attentionAggregationLabel(head.aggregation) : head.id;
}

export function resolveAttentionHead(
  heads: AttentionHead[],
  selectionId: string,
  rolloutHeads: AttentionHead[] = heads,
  targetLayer = heads[0]?.layer,
  rolloutLayers?: number[]
) {
  if (parseAttentionRollout(selectionId) && targetLayer !== undefined) {
    return rolloutAttentionHeads(rolloutHeads, targetLayer, rolloutLayers);
  }
  const difference = parseAttentionDifference(selectionId);
  if (difference) return differenceAttentionHeads(heads, difference.selectedHeadId, difference.baselineHeadId);
  const aggregation = parseAttentionAggregation(selectionId);
  if (aggregation) return aggregateAttentionHeads(heads, aggregation);
  return heads.find((head) => head.id === selectionId) ?? heads[0];
}

export function rolloutAttentionHeads(
  heads: AttentionHead[],
  targetLayer: number,
  expectedLayers?: number[]
): AttentionHead | undefined {
  const retainedHeads = heads.filter((head) =>
    head.layer <= targetLayer && !head.aggregation && !head.difference && !head.rollout
  );
  const layers = [...new Set(retainedHeads.map((head) => head.layer))].sort((left, right) => left - right);
  if (layers.length === 0 || layers[layers.length - 1] !== targetLayer) return undefined;
  const requiredLayers = [...new Set((expectedLayers ?? layers).filter((layer) => layer <= targetLayer))]
    .sort((left, right) => left - right);
  if (requiredLayers.length !== layers.length || requiredLayers.some((layer, index) => layer !== layers[index])) {
    return undefined;
  }
  const size = Math.max(
    0,
    ...retainedHeads.flatMap((head) => [
      head.distributionByToken.length,
      ...head.distributionByToken.map((row) => row.length)
    ])
  );
  if (size === 0) return undefined;

  let rollout = identityMatrix(size);
  for (const layer of layers) {
    const layerHeads = retainedHeads.filter((head) => head.layer === layer);
    const transition = Array.from({ length: size }, (_, row) => {
      const values = Array.from({ length: size }, (_, column) => {
        if (column > row) return 0;
        const mean = layerHeads.reduce(
          (total, head) => total + finiteProbability(head.distributionByToken[row]?.[column]),
          0
        ) / layerHeads.length;
        return mean + (row === column ? 1 : 0);
      });
      const total = values.reduce((sum, value) => sum + value, 0);
      return values.map((value) => total > 0 ? value / total : 0);
    });
    rollout = multiplyCausalMatrices(transition, rollout);
  }

  const memberHeadIds = retainedHeads.map((head) => head.id);
  return {
    id: attentionRolloutId(),
    layer: targetLayer,
    head: -1,
    role: `Retained-head mean + identity residual rollout · ${layers.length} layers · ${memberHeadIds.length} heads`,
    riskContribution: retainedHeads.reduce((sum, head) => sum + head.riskContribution, 0) / retainedHeads.length,
    entropy: meanRowEntropy(rollout),
    distributionByToken: rollout.map((row, rowIndex) => row.slice(0, rowIndex + 1)),
    rollout: {
      fusion: "retained_mean",
      residual: "identity",
      layers,
      memberHeadIds
    },
    memberHeadIds
  };
}

export function differenceAttentionHeads(
  heads: AttentionHead[],
  selectedHeadId: string,
  baselineHeadId: string
): AttentionHead | undefined {
  const selected = heads.find((head) => head.id === selectedHeadId);
  const baseline = heads.find((head) => head.id === baselineHeadId);
  if (!selected || !baseline || selected.id === baseline.id || selected.layer !== baseline.layer) return undefined;
  const rowCount = Math.max(selected.distributionByToken.length, baseline.distributionByToken.length);
  const distributionByToken = Array.from({ length: rowCount }, (_, row) => {
    const columnCount = Math.max(
      selected.distributionByToken[row]?.length ?? 0,
      baseline.distributionByToken[row]?.length ?? 0
    );
    return Array.from({ length: columnCount }, (_, column) =>
      finiteProbability(selected.distributionByToken[row]?.[column]) -
      finiteProbability(baseline.distributionByToken[row]?.[column])
    );
  });
  return {
    id: attentionDifferenceId(selected.id, baseline.id),
    layer: selected.layer,
    head: -1,
    role: `Cell-wise retained-head difference · ${selected.id} minus ${baseline.id}`,
    riskContribution: selected.riskContribution - baseline.riskContribution,
    entropy: selected.entropy - baseline.entropy,
    distributionByToken,
    difference: { selectedHeadId: selected.id, baselineHeadId: baseline.id },
    memberHeadIds: [selected.id, baseline.id]
  };
}

export function isAttentionDifferenceAvailable(heads: AttentionHead[], selectionId: string) {
  const difference = parseAttentionDifference(selectionId);
  return Boolean(
    difference &&
    heads.some((head) => head.id === difference.selectedHeadId) &&
    heads.some((head) => head.id === difference.baselineHeadId)
  );
}

export function aggregateAttentionHeads(
  heads: AttentionHead[],
  aggregation: AttentionAggregation
): AttentionHead | undefined {
  if (heads.length === 0) return undefined;
  const weights = aggregationWeights(heads, aggregation);
  const rowCount = Math.max(...heads.map((head) => head.distributionByToken.length));
  const distributionByToken = Array.from({ length: rowCount }, (_, row) => {
    const columnCount = Math.max(
      0,
      ...heads.map((head) => head.distributionByToken[row]?.length ?? 0)
    );
    return Array.from({ length: columnCount }, (_, column) => {
      const values = heads.map((head) => finiteProbability(
        head.distributionByToken[row]?.[column]
      ));
      if (aggregation === "max") return Math.max(...values);
      return values.reduce((total, value, index) => total + value * weights[index], 0);
    });
  });
  const aggregateScalar = (values: number[]) => aggregation === "max"
    ? Math.max(...values)
    : values.reduce((total, value, index) => total + value * weights[index], 0);
  return {
    id: attentionAggregationId(aggregation),
    layer: heads[0].layer,
    head: -1,
    role: `${attentionAggregationLabel(aggregation)} · derived from ${heads.length} retained heads`,
    riskContribution: aggregateScalar(heads.map((head) => head.riskContribution)),
    entropy: aggregateScalar(heads.map((head) => head.entropy)),
    distributionByToken,
    aggregation,
    memberHeadIds: heads.map((head) => head.id)
  };
}

export function attentionHeadSourceKey(head: AttentionHead, row?: number, column?: number) {
  const suffix = row === undefined
    ? ""
    : column === undefined
      ? `[${row}]`
      : `[${row},${column}]`;
  if (head.difference) {
    return `derived.attention.difference[${head.difference.selectedHeadId}-${head.difference.baselineHeadId}]${suffix}`;
  }
  if (head.rollout) {
    return `derived.attention.rollout.retained_mean_identity[L${head.rollout.layers.join(",L")};${head.rollout.memberHeadIds.join(",")}]${suffix}`;
  }
  if (!head.aggregation) {
    return `blocks.${head.layer}.attn.hook_pattern[${head.head}]${suffix}`;
  }
  return `derived.attention.${head.aggregation}[${head.memberHeadIds?.join(",") ?? "retained"}]${suffix}`;
}

export function attentionHeadMetric(head: AttentionHead) {
  if (head.rollout) return "attention_retained_rollout_mean_identity";
  if (head.difference) return "attention_retained_head_difference";
  return head.aggregation
    ? `attention_retained_${head.aggregation}`
    : "attention_probability";
}

export function attentionHeadProvenance(
  head: AttentionHead,
  rawProvenance: MetricProvenance
): MetricProvenance {
  if (head.rollout) {
    return {
      label: "Retained attention rollout",
      method: `per-layer retained-head arithmetic mean, identity residual addition, row normalization, then matrix product through layer ${head.layer}`,
      semantics:
        "Client-derived descriptive path proxy over only the artifact-retained heads and available layers. It is not a full-model rollout, attribution, or causal evidence.",
      normalization: "A_hat_l = row_normalize(mean_retained(A_l) + I); R_l = A_hat_l × R_(l-1); R_-1 = I",
      kind: "derived_proxy"
    };
  }
  if (head.difference) {
    return {
      label: "Retained-head probability difference",
      method: `cell-wise ${head.difference.selectedHeadId} minus ${head.difference.baselineHeadId}`,
      semantics:
        "Client-derived signed difference between two retained artifact heads in the same layer; positive cells favor the selected head and negative cells favor the baseline. It is descriptive, not causal evidence.",
      normalization: "none; subtraction of stored raw softmax probabilities on the exact token axes",
      kind: "derived_proxy"
    };
  }
  if (!head.aggregation) return rawProvenance;
  const memberCount = head.memberHeadIds?.length ?? 0;
  const operation = head.aggregation === "mean"
    ? "cell-wise arithmetic mean"
    : head.aggregation === "max"
      ? "cell-wise maximum"
      : "cell-wise weighted mean with normalized inverse stored head entropy";
  return {
    label: attentionAggregationLabel(head.aggregation),
    method: `${operation} over ${memberCount} retained artifact heads`,
    semantics:
      "Client-derived descriptive aggregate over the heads retained in this artifact; it is neither a full-model aggregate nor causal evidence.",
    normalization: "none; each source cell is aggregated from stored raw softmax probabilities",
    kind: "derived_proxy"
  };
}

function aggregationWeights(heads: AttentionHead[], aggregation: AttentionAggregation) {
  if (aggregation !== "entropy_weighted") return heads.map(() => 1 / heads.length);
  const inverseEntropy = heads.map((head) => 1 / Math.max(1e-6, head.entropy));
  const total = inverseEntropy.reduce((sum, value) => sum + value, 0);
  return inverseEntropy.map((value) => value / total);
}

function finiteProbability(value: number | undefined) {
  return Number.isFinite(value) ? Math.max(0, Math.min(1, value!)) : 0;
}

function identityMatrix(size: number) {
  return Array.from({ length: size }, (_, row): number[] =>
    Array.from({ length: size }, (_, column) => row === column ? 1 : 0)
  );
}

function multiplyCausalMatrices(left: number[][], right: number[][]) {
  return left.map((row, destination) =>
    row.map((_, source) => {
      if (source > destination) return 0;
      let value = 0;
      for (let intermediate = source; intermediate <= destination; intermediate += 1) {
        value += (left[destination]?.[intermediate] ?? 0) * (right[intermediate]?.[source] ?? 0);
      }
      return value;
    })
  );
}

function meanRowEntropy(matrix: number[][]) {
  if (matrix.length === 0) return 0;
  return matrix.reduce((total, row) => total + row.reduce(
    (entropy, value) => value > 0 ? entropy - value * Math.log(value) : entropy,
    0
  ), 0) / matrix.length;
}
