export type MetricFormatMode = "compact" | "exact";

interface MetricFormatRule {
  matches: (metric: string) => boolean;
  compactDigits: number;
  exactDigits: number;
}

const METRIC_FORMAT_RULES: MetricFormatRule[] = [
  rule(["patching_recovery"], 1, 6),
  prefixRule("attention_", 4, 6),
  rule(["residual_direction"], 4, 6),
  rule(["residual_norm", "mlp_normalized_activation"], 3, 6),
  prefixRule("mlp_", 4, 6),
  prefixRule("nla_", 4, 6),
  prefixRule("patching_", 4, 6),
  prefixRule("intervention_", 4, 6),
  rule(["tokenRisk", "risk", "probe", "token_safety_proxy"], 3, 6),
  rule(["attribution", "integrated_gradients"], 4, 6)
];

const DEFAULT_RULE: MetricFormatRule = {
  matches: () => true,
  compactDigits: 3,
  exactDigits: 6
};

export function formatMetricNumber(
  value: number | null | undefined,
  metric: string,
  mode: MetricFormatMode = "compact"
) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "n/a";
  const normalized = Object.is(value, -0) ? 0 : value;
  const rule = METRIC_FORMAT_RULES.find((candidate) => candidate.matches(metric)) ?? DEFAULT_RULE;
  const digits = mode === "exact" ? rule.exactDigits : rule.compactDigits;
  const scientificThreshold = 10 ** -(digits + (mode === "exact" ? 1 : 0));
  if (normalized !== 0 && Math.abs(normalized) < scientificThreshold) {
    return normalized.toExponential(mode === "exact" ? 6 : 2);
  }
  return normalized.toFixed(digits);
}

export function formatMetricDelta(
  value: number | null | undefined,
  metric: string,
  mode: MetricFormatMode = "compact"
) {
  const formatted = formatMetricNumber(value, metric, mode);
  if (formatted === "n/a" || value === null || value === undefined) return formatted;
  return value > 0 ? `+${formatted}` : formatted;
}

export function metricDisplayLabel(metric: string) {
  const labels: Record<string, string> = {
    tokenRisk: "safety proxy",
    risk: "safety proxy",
    probe: "probe score",
    residual_direction: "direction alignment",
    residual_norm: "activation norm",
    attention_probability: "attention probability",
    attention_concentration: "attention concentration",
    mlp_signed_activation: "signed activation",
    mlp_absolute_activation: "absolute activation",
    mlp_normalized_activation: "normalized activation",
    nla_cosine: "NLA cosine",
    nla_mse: "NLA MSE",
    nla_fve: "NLA FVE",
    patching_recovery: "patching recovery",
    patching_effect: "causal effect",
    patching_score: "patched logit",
    intervention_logit_delta: "intervention logit delta",
    integrated_gradients: "integrated gradients"
  };
  return labels[metric] ?? metric.replace(/_/g, " ");
}

function rule(metrics: string[], compactDigits: number, exactDigits: number): MetricFormatRule {
  const values = new Set(metrics);
  return { matches: (metric) => values.has(metric), compactDigits, exactDigits };
}

function prefixRule(prefix: string, compactDigits: number, exactDigits: number): MetricFormatRule {
  return { matches: (metric) => metric.startsWith(prefix), compactDigits, exactDigits };
}
