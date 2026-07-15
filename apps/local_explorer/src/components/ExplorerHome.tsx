import { useMemo, useState } from "react";
import {
  ArrowUpRight,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleDashed,
  Clock3,
  Cpu,
  Database,
  Plus,
  Search,
  Sparkles
} from "lucide-react";

import type { RemoteRunState, RunRecord } from "../state/useRunLibrary";
import type { ExplorerRun, WorkspaceView } from "../types";

type VisualizationCategory = "all" | "activations" | "attention" | "explanations" | "causal";
type PreviewKind =
  | "cache"
  | "attention"
  | "logits"
  | "mlp"
  | "attribution"
  | "nla-list"
  | "nla-grid"
  | "patching"
  | "next-token"
  | "components";

interface VisualizationSpec {
  id: string;
  title: string;
  api: string;
  category: Exclude<VisualizationCategory, "all">;
  view: WorkspaceView;
  preview: PreviewKind;
}

const visualizations: VisualizationSpec[] = [
  {
    id: "activation-cache",
    title: "Activation cache browser",
    api: "plot_activation_cache_browser",
    category: "activations",
    view: "overview",
    preview: "cache"
  },
  {
    id: "attention-browser",
    title: "Attention pattern browser",
    api: "plot_attention_browser",
    category: "attention",
    view: "attention",
    preview: "attention"
  },
  {
    id: "logit-lens",
    title: "Residual logit lens",
    api: "plot_logit_lens",
    category: "activations",
    view: "residual",
    preview: "logits"
  },
  {
    id: "mlp-neurons",
    title: "MLP neuron browser",
    api: "plot_mlp_neuron_topk_browser",
    category: "activations",
    view: "mlp",
    preview: "mlp"
  },
  {
    id: "input-attribution",
    title: "Input attribution",
    api: "render_input_attribution_html",
    category: "causal",
    view: "attribution",
    preview: "attribution"
  },
  {
    id: "nla-results",
    title: "NLA result browser",
    api: "plot_nla_result_browser",
    category: "explanations",
    view: "nla",
    preview: "nla-list"
  },
  {
    id: "nla-fidelity",
    title: "NLA fidelity heatmap",
    api: "plot_nla_fidelity_heatmap",
    category: "explanations",
    view: "nla",
    preview: "nla-grid"
  },
  {
    id: "activation-patching",
    title: "Activation patching grid",
    api: "plot_activation_patching_grid",
    category: "causal",
    view: "patching",
    preview: "patching"
  },
  {
    id: "next-token",
    title: "Next-token browser",
    api: "plot_next_token_browser",
    category: "activations",
    view: "residual",
    preview: "next-token"
  },
  {
    id: "component-scores",
    title: "Component score explorer",
    api: "plot_component_scores",
    category: "attention",
    view: "overview",
    preview: "components"
  }
];

const categories: Array<{ id: VisualizationCategory; label: string }> = [
  { id: "all", label: "All" },
  { id: "activations", label: "Activations" },
  { id: "attention", label: "Attention" },
  { id: "explanations", label: "Explanations" },
  { id: "causal", label: "Causal" }
];

interface ExplorerHomeProps {
  records: RunRecord[];
  activeRecord: RunRecord & { run: ExplorerRun };
  remoteState: RemoteRunState;
  onOpenRun: (key: string, view?: WorkspaceView) => void;
  onNewAnalysis: () => void;
}

export function ExplorerHome({
  records,
  activeRecord,
  remoteState,
  onOpenRun,
  onNewAnalysis
}: ExplorerHomeProps) {
  const [runQuery, setRunQuery] = useState("");
  const [category, setCategory] = useState<VisualizationCategory>("all");
  const normalizedQuery = runQuery.trim().toLowerCase();
  const filteredRecords = useMemo(
    () => records.filter((record) => !normalizedQuery || [
      record.runId,
      record.sampleId,
      record.modelName,
      record.sourceName
    ].some((value) => value.toLowerCase().includes(normalizedQuery))),
    [normalizedQuery, records]
  );
  const visibleVisualizations = category === "all"
    ? visualizations
    : visualizations.filter((item) => item.category === category);
  const nlaReadyCount = records.filter((record) => nlaState(record).kind !== "incompatible").length;

  return (
    <div className="home-shell">
      <header className="home-topbar">
        <a className="home-brand" href="/" aria-label="SafeLens home">
          <span><BrainCircuit size={21} /></span>
          <strong>SafeLens</strong>
        </a>
        <nav aria-label="Home navigation">
          <a href="#runs">Runs</a>
          <a href="#visualizations">Visualizations</a>
        </nav>
        <button className="home-open-explorer" onClick={() => onOpenRun(activeRecord.key)}>
          Open Explorer <ArrowUpRight size={15} />
        </button>
      </header>

      <main className="home-main">
        <section className="home-intro" aria-labelledby="home-title">
          <div className="home-intro-copy">
            <span>Local interpretability workspace</span>
            <h1 id="home-title">SafeLens</h1>
            <p>{activeRecord.modelName}</p>
          </div>
          <div className="home-intro-actions">
            <button onClick={onNewAnalysis}><Plus size={16} /> New analysis</button>
            <button onClick={() => onOpenRun(activeRecord.key)}>
              Continue run <ChevronRight size={16} />
            </button>
          </div>
          <dl className="home-stats" aria-label="Workspace summary">
            <div><dt>Runs</dt><dd>{records.length}</dd></div>
            <div><dt>Visualizations</dt><dd>{visualizations.length}</dd></div>
            <div><dt>NLA-ready</dt><dd>{nlaReadyCount}</dd></div>
            <div><dt>Workspace</dt><dd>{workspaceStateLabel(remoteState)}</dd></div>
          </dl>
        </section>

        <div className="home-primary-grid">
          <section id="runs" className="home-runs" aria-labelledby="home-runs-title">
            <header className="home-section-header">
              <div>
                <span>Workspace</span>
                <h2 id="home-runs-title">Recent runs</h2>
              </div>
              <label className="home-run-search">
                <Search size={14} />
                <input
                  aria-label="Search home runs"
                  value={runQuery}
                  placeholder="Search runs"
                  onChange={(event) => setRunQuery(event.target.value)}
                />
              </label>
            </header>

            <div className="home-run-list">
              {filteredRecords.slice(0, 6).map((record) => {
                const state = nlaState(record);
                return (
                  <button
                    key={record.key}
                    className={record.key === activeRecord.key ? "active" : ""}
                    onClick={() => onOpenRun(record.key)}
                  >
                    <span className="home-run-icon"><Database size={16} /></span>
                    <span className="home-run-name">
                      <strong>{record.runId}</strong>
                      <small>{record.sampleId}</small>
                    </span>
                    <span className="home-run-model"><Cpu size={13} />{record.modelName}</span>
                    <span className="home-run-size">
                      <b>{record.tokenCount}</b> tokens
                      <b>{record.layerCount}</b> layers
                    </span>
                    <span className={`home-run-nla ${state.kind}`}>
                      <NlaStateIcon kind={state.kind} />{state.label}
                    </span>
                    <ChevronRight size={16} />
                  </button>
                );
              })}
              {filteredRecords.length === 0 && (
                <div className="home-run-empty">No runs match the current search.</div>
              )}
            </div>
          </section>

          <aside className="home-nla-panel" aria-labelledby="home-nla-title">
            <header>
              <span><Sparkles size={15} /> Natural Language Autoencoder</span>
              <h2 id="home-nla-title">NLA profiles</h2>
            </header>
            <div className="home-nla-profile compatible">
              <span>Public</span>
              <strong>Qwen2.5-7B · L20</strong>
              <small>resid_post · d_model 3584</small>
              <b><CheckCircle2 size={13} /> AV + AR</b>
            </div>
            <div className="home-nla-profile gated">
              <span>Gated</span>
              <strong>Gemma 3 12B · L32</strong>
              <small>resid_post · d_model 3840</small>
              <b><Clock3 size={13} /> token required</b>
            </div>
            <button onClick={() => onOpenRun(activeRecord.key, "nla")}>
              Open NLA workspace <ChevronRight size={15} />
            </button>
          </aside>
        </div>

        <section id="visualizations" className="home-visualizations" aria-labelledby="home-visualizations-title">
          <header className="home-section-header">
            <div>
              <span>SafeLens.viz</span>
              <h2 id="home-visualizations-title">Visualization library</h2>
            </div>
            <div className="home-category-tabs" role="tablist" aria-label="Visualization category">
              {categories.map((item) => (
                <button
                  key={item.id}
                  role="tab"
                  aria-selected={category === item.id}
                  className={category === item.id ? "active" : ""}
                  onClick={() => setCategory(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </header>

          <div className="home-viz-grid">
            {visibleVisualizations.map((item) => {
              const state = visualizationState(item, activeRecord.run);
              return (
                <button
                  key={item.id}
                  className="home-viz-card"
                  onClick={() => onOpenRun(activeRecord.key, item.view)}
                >
                  <VisualizationPreview kind={item.preview} run={activeRecord.run} />
                  <span className="home-viz-card-body">
                    <span className="home-viz-card-heading">
                      <strong>{item.title}</strong>
                      <ArrowUpRight size={15} />
                    </span>
                    <code>{item.api}</code>
                    <span className={`home-viz-status ${state.kind}`}>{state.label}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}

function NlaStateIcon({ kind }: { kind: ReturnType<typeof nlaState>["kind"] }) {
  if (kind === "available") return <CheckCircle2 size={13} />;
  if (kind === "compatible" || kind === "gated") return <Clock3 size={13} />;
  return <CircleDashed size={13} />;
}

function workspaceStateLabel(state: RemoteRunState) {
  if (state.status === "ready") return "online";
  if (state.status === "loading") return "connecting";
  if (state.status === "error") return "local only";
  if (state.status === "empty") return "local";
  return state.status;
}

function nlaState(record: RunRecord): {
  kind: "available" | "compatible" | "gated" | "incompatible";
  label: string;
} {
  if (record.run?.nla.some((row) => row.status === "available")) {
    return { kind: "available", label: "NLA result" };
  }
  if (record.modelName.toLowerCase() === "qwen/qwen2.5-7b-instruct".toLowerCase()) {
    return { kind: "compatible", label: "NLA ready" };
  }
  if (record.modelName.toLowerCase() === "google/gemma-3-12b-it") {
    return { kind: "gated", label: "NLA gated" };
  }
  return { kind: "incompatible", label: "No NLA profile" };
}

function visualizationState(spec: VisualizationSpec, run: ExplorerRun) {
  if (spec.view === "nla") {
    return run.nla.some((row) => row.status === "available")
      ? { kind: "ready", label: "Ready" }
      : { kind: "setup", label: "NLA required" };
  }
  if (spec.view === "patching") {
    return run.patching
      ? { kind: "ready", label: "Ready" }
      : { kind: "setup", label: "Configure" };
  }
  if (spec.view === "attribution") {
    return run.attributionMethods.some((method) => method.id === "integrated_gradients" && method.available)
      ? { kind: "ready", label: "Causal result" }
      : { kind: "proxy", label: "Proxy loaded" };
  }
  return { kind: "ready", label: "Ready" };
}

function VisualizationPreview({ kind, run }: { kind: PreviewKind; run: ExplorerRun }) {
  if (kind === "attention") {
    const head = run.attentionHeads[0];
    const values = head?.distributionByToken.flat().slice(0, 49) ?? [];
    return <div className="home-viz-preview preview-grid teal">{previewCells(values, 49)}</div>;
  }

  if (kind === "cache" || kind === "components") {
    const values = kind === "cache"
      ? run.residualCells.slice(0, 48).map((cell) => cell.riskDirection)
      : run.attentionCells.slice(0, 48).map((cell) => cell.value);
    return <div className={`home-viz-preview preview-grid ${kind === "cache" ? "rose" : "teal"}`}>{previewCells(values, 48)}</div>;
  }

  if (kind === "mlp") {
    const values = run.mlpNeurons[0]?.activationsByToken.slice(0, 18) ?? [];
    const scale = Math.max(1e-8, ...values.map((value) => Math.abs(value)));
    return (
      <div className="home-viz-preview preview-bars">
        {fill(values, 18).map((value, index) => (
          <i
            key={index}
            className={value < 0 ? "negative" : "positive"}
            style={{ height: `${12 + 68 * Math.abs(value) / scale}%` }}
          />
        ))}
      </div>
    );
  }

  if (kind === "logits" || kind === "next-token") {
    const row = run.logitLens[run.logitLens.length - 1];
    const predictions = row?.topPredictions.slice(0, 5) ?? [];
    const scale = Math.max(1e-8, ...predictions.map((item) => item.probability));
    return (
      <div className="home-viz-preview preview-ranks">
        {predictions.map((item) => (
          <span key={item.tokenId}>
            <b>{item.tokenText.trim() || "space"}</b>
            <i style={{ width: `${Math.max(8, 100 * item.probability / scale)}%` }} />
            <small>{item.probability.toFixed(3)}</small>
          </span>
        ))}
      </div>
    );
  }

  if (kind === "attribution") {
    const method = run.attributionMethods.find((item) => item.available);
    const values = method?.rows[method.rows.length - 1]?.values ?? run.tokens.map((token) => token.attribution);
    return (
      <div className="home-viz-preview preview-tokens">
        {run.tokens.slice(0, 10).map((token, index) => (
          <span
            key={token.index}
            className={(values[index] ?? 0) < 0 ? "negative" : "positive"}
            style={{ opacity: 0.42 + 0.58 * normalizedMagnitude(values[index] ?? 0, values) }}
          >
            {token.text.trim() || "·"}
          </span>
        ))}
      </div>
    );
  }

  if (kind === "nla-list") {
    const rows = run.nla.filter((row) => row.status === "available").slice(0, 3);
    return (
      <div className="home-viz-preview preview-nla-list">
        {(rows.length ? rows : run.nla.slice(0, 3)).map((row, index) => (
          <span key={`${row.layer}:${row.tokenIndex}:${index}`}>
            <b>{row.token?.trim() || `T${row.tokenIndex}`}</b>
            <i>{row.status === "available" ? row.cosine.toFixed(3) : "pending"}</i>
          </span>
        ))}
      </div>
    );
  }

  if (kind === "nla-grid") {
    const values = run.nla.map((row) => row.status === "available" ? row.cosine : 0);
    return <div className="home-viz-preview preview-grid teal">{previewCells(values, 40)}</div>;
  }

  const values = run.patching?.cells.map((cell) => Math.abs(cell.causalEffect)) ?? [];
  return <div className="home-viz-preview preview-grid amber">{previewCells(values, 48)}</div>;
}

function previewCells(values: number[], count: number) {
  const filled = fill(values, count);
  const minimum = Math.min(0, ...filled);
  const maximum = Math.max(1e-8, ...filled);
  return filled.map((value, index) => (
    <i key={index} style={{ opacity: 0.13 + 0.87 * normalize(value, minimum, maximum) }} />
  ));
}

function fill(values: number[], count: number) {
  return Array.from({ length: count }, (_, index) => values[index % Math.max(1, values.length)] ?? 0);
}

function normalize(value: number, minimum: number, maximum: number) {
  return maximum === minimum ? 0 : Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum)));
}

function normalizedMagnitude(value: number, values: number[]) {
  const scale = Math.max(1e-8, ...values.map((item) => Math.abs(item)));
  return Math.min(1, Math.abs(value) / scale);
}
