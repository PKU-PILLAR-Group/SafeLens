import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

import type { MLPNeuron, ResidualCell, TokenInfo } from "../types";

const MAX_MLP_ROWS = 16;

export type ResidualMetric = "norm" | "rawDirection" | "riskDirection" | "semanticDensity";

const RESIDUAL_METRICS: Array<{
  id: ResidualMetric;
  label: string;
  color: string;
  digits: number;
}> = [
  { id: "norm", label: "Norm", color: "20, 124, 120", digits: 2 },
  { id: "rawDirection", label: "Raw direction", color: "37, 99, 235", digits: 3 },
  { id: "riskDirection", label: "Risk direction", color: "190, 70, 40", digits: 3 },
  { id: "semanticDensity", label: "Semantic density", color: "126, 80, 180", digits: 3 }
];

interface HeatmapRow {
  key: string;
  label: string;
  title: string;
  values: Array<number | undefined>;
  selected: boolean;
  onSelect?: () => void;
}

interface HeatmapTableProps {
  ariaLabel: string;
  cornerLabel: string;
  tokens: TokenInfo[];
  rows: HeatmapRow[];
  min: number;
  max: number;
  signed: boolean;
  color: string;
  format: (value: number) => string;
  selectedRange: [number, number];
  selectedRowKey: string;
  rowHeaderWidth: number;
  cellWidth: number;
  rowHeight: number;
  maxHeight: number;
  onSelectCell: (rowKey: string, tokenIndex: number) => void;
}

function tokenText(token: TokenInfo) {
  return token.text
    .replace(/\r/g, "\\r")
    .replace(/\n/g, "\\n")
    .replace(/\t/g, "\\t");
}

function shortToken(token: TokenInfo) {
  const text = tokenText(token);
  if (!text) return `T${token.index}`;
  return text.length > 7 ? `${text.slice(0, 6)}…` : text;
}

function formatActivation(value: number) {
  if (!Number.isFinite(value)) return "—";
  const absolute = Math.abs(value);
  if (absolute === 0) return "0";
  if (absolute >= 100) return value.toFixed(1);
  if (absolute >= 1) return value.toFixed(2);
  if (absolute >= 0.01) return value.toFixed(3);
  return value.toExponential(2);
}

function heatColor(
  value: number,
  min: number,
  max: number,
  signed: boolean,
  color: string
) {
  if (!Number.isFinite(value)) return "#f5f6f6";
  if (signed) {
    const bound = Math.max(Math.abs(min), Math.abs(max), 1e-9);
    const ratio = Math.max(-1, Math.min(1, value / bound));
    if (Math.abs(ratio) < 0.01) return "#f5f6f6";
    const alpha = 0.12 + 0.78 * Math.abs(ratio);
    return ratio > 0
      ? `rgba(190, 40, 70, ${alpha.toFixed(3)})`
      : `rgba(38, 92, 190, ${alpha.toFixed(3)})`;
  }
  const ratio = max > min ? (value - min) / (max - min) : 0.5;
  const alpha = 0.08 + 0.82 * Math.max(0, Math.min(1, ratio));
  return `rgba(${color}, ${alpha.toFixed(3)})`;
}

function HeatmapTable({
  ariaLabel,
  cornerLabel,
  tokens,
  rows,
  min,
  max,
  signed,
  color,
  format,
  selectedRange,
  selectedRowKey,
  rowHeaderWidth,
  cellWidth,
  rowHeight,
  maxHeight,
  onSelectCell
}: HeatmapTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const inRange = (tokenIndex: number) =>
    tokenIndex >= selectedRange[0] && tokenIndex < selectedRange[1];
  useEffect(() => {
    const container = scrollRef.current;
    const row = container
      ?.querySelector<HTMLElement>(".feature-heatmap-row.selected")
      ?.closest("tr");
    if (!container || !row) return;
    const containerRect = container.getBoundingClientRect();
    const rowRect = row.getBoundingClientRect();
    if (rowRect.top < containerRect.top || rowRect.bottom > containerRect.bottom) {
      container.scrollTop +=
        rowRect.top - containerRect.top - container.clientHeight / 2 + rowRect.height / 2;
    }
  }, [selectedRowKey, rows.length]);
  const tableStyle = {
    "--heatmap-row-header": `${rowHeaderWidth}px`,
    "--heatmap-cell": `${cellWidth}px`,
    "--heatmap-row-height": `${rowHeight}px`
  } as CSSProperties;

  return (
    <div ref={scrollRef} className="feature-heatmap-scroll" style={{ maxHeight }}>
      <table className="feature-heatmap-table" style={tableStyle} aria-label={ariaLabel}>
        <thead>
          <tr>
            <th className="feature-heatmap-corner" scope="col">{cornerLabel}</th>
            {tokens.map((token) => (
              <th
                key={token.index}
                scope="col"
                className={`feature-heatmap-token${inRange(token.index) ? " in-range" : ""}`}
                title={`T${token.index} ${tokenText(token)}`}
              >
                <span>{shortToken(token)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <th
                scope="row"
                className={`feature-heatmap-row${row.selected ? " selected" : ""}`}
                title={row.title}
              >
                {row.onSelect ? (
                  <button type="button" onClick={row.onSelect}>{row.label}</button>
                ) : (
                  <span>{row.label}</span>
                )}
              </th>
              {tokens.map((token) => {
                const raw = row.values[token.index];
                const missing = raw === undefined || !Number.isFinite(raw);
                const value = raw !== undefined && Number.isFinite(raw) ? raw : 0;
                const label = missing
                  ? `${row.title} · T${token.index} ${tokenText(token)} · not loaded`
                  : `${row.title} · T${token.index} ${tokenText(token)} · ${format(value)}`;
                return (
                  <td key={token.index} className={inRange(token.index) ? "in-range" : ""}>
                    <button
                      type="button"
                      className={`feature-heatmap-cell${missing ? " missing" : ""}`}
                      style={missing ? undefined : { backgroundColor: heatColor(value, min, max, signed, color) }}
                      aria-label={label}
                      title={label}
                      onClick={() => onSelectCell(row.key, token.index)}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function percentile(values: number[], ratio: number) {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(
    sorted.length - 1,
    Math.max(0, Math.round(ratio * (sorted.length - 1)))
  );
  return sorted[index];
}

function HeatmapLegend({
  signed,
  min,
  max,
  color,
  format,
  clipped = false
}: {
  signed: boolean;
  min: number;
  max: number;
  color: string;
  format: (value: number) => string;
  clipped?: boolean;
}) {
  const background = signed
    ? "linear-gradient(90deg, #265cbe, #f5f6f6, #be2846)"
    : `linear-gradient(90deg, rgba(${color}, 0.08), rgba(${color}, 0.9))`;
  const lower = clipped ? `≤${format(min)}` : format(min);
  const upper = clipped ? `≥${format(max)}` : format(max);
  return (
    <div
      className="feature-heatmap-legend"
      aria-hidden="true"
      title={clipped ? "Color domain clipped to the 2nd–95th percentile; hover cells for raw values." : undefined}
    >
      <span>{signed ? `−${format(Math.max(Math.abs(min), Math.abs(max)))}` : lower}</span>
      <i className="feature-heatmap-legend-bar" style={{ background }} />
      <span>{signed ? `+${format(Math.max(Math.abs(min), Math.abs(max)))}` : upper}</span>
    </div>
  );
}

export function MLPActivationHeatmap({
  tokens,
  neurons,
  layer,
  selectedNeuron,
  selectedRange,
  onSelectNeuron,
  onSelectToken
}: {
  tokens: TokenInfo[];
  neurons: MLPNeuron[];
  layer: number;
  selectedNeuron: number;
  selectedRange: [number, number];
  onSelectNeuron: (neuron: number) => void;
  onSelectToken: (tokenIndex: number) => void;
}) {
  const rows = useMemo(() => {
    const ordered = [...neurons].sort(
      (left, right) =>
        right.maxAbsoluteActivation - left.maxAbsoluteActivation || left.neuron - right.neuron
    );
    const selected = ordered.find((neuron) => neuron.neuron === selectedNeuron);
    let visible = ordered.slice(0, MAX_MLP_ROWS);
    if (selected && !visible.some((neuron) => neuron.neuron === selected.neuron)) {
      visible = [...visible.slice(0, MAX_MLP_ROWS - 1), selected];
    }
    return visible.map((neuron) => ({
      key: neuron.id,
      label: `N${neuron.neuron}`,
      title: `L${layer}N${neuron.neuron} · peak ${formatActivation(neuron.maxAbsoluteActivation)}`,
      values: neuron.activationsByToken,
      selected: neuron.neuron === selectedNeuron,
      onSelect: () => onSelectNeuron(neuron.neuron)
    }));
  }, [layer, neurons, onSelectNeuron, selectedNeuron]);

  const maxAbsolute = useMemo(() => {
    let bound = 1e-9;
    for (const row of rows) {
      for (const value of row.values) {
        if (typeof value === "number" && Number.isFinite(value)) {
          bound = Math.max(bound, Math.abs(value));
        }
      }
    }
    return bound;
  }, [rows]);

  return (
    <section className="chat-feature-visual" aria-label="MLP activation visualization">
      <header>
        <div>
          <h3>MLP activation heatmap</h3>
          <p>
            Layer L{layer} · {rows.length} of {neurons.length} neurons × {tokens.length} tokens ·
            signed post-activation
          </p>
        </div>
      </header>
      {rows.length > 0 ? (
        <>
          <HeatmapTable
            ariaLabel="MLP activation heatmap"
            cornerLabel="Neuron"
            tokens={tokens}
            rows={rows}
            min={-maxAbsolute}
            max={maxAbsolute}
            signed
            color="20, 124, 120"
            format={formatActivation}
            selectedRange={selectedRange}
            selectedRowKey={rows.find((row) => row.selected)?.key ?? ""}
            rowHeaderWidth={54}
            cellWidth={30}
            rowHeight={20}
            maxHeight={Math.min(520, 72 + rows.length * 21 + 12)}
            onSelectCell={(rowKey, tokenIndex) => {
              const next = neurons.find((neuron) => neuron.id === rowKey);
              if (next) onSelectNeuron(next.neuron);
              onSelectToken(tokenIndex);
            }}
          />
          <HeatmapLegend
            signed
            min={-maxAbsolute}
            max={maxAbsolute}
            color="20, 124, 120"
            format={formatActivation}
          />
        </>
      ) : (
        <p className="feature-heatmap-empty">No MLP neuron activations are available for this layer.</p>
      )}
    </section>
  );
}

export function ResidualStreamHeatmap({
  tokens,
  cells,
  selectedLayer,
  selectedRange,
  onSelectLayer,
  onSelectToken
}: {
  tokens: TokenInfo[];
  cells: ResidualCell[];
  selectedLayer: number;
  selectedRange: [number, number];
  onSelectLayer: (layer: number) => void;
  onSelectToken: (tokenIndex: number) => void;
}) {
  const [metric, setMetric] = useState<ResidualMetric>("norm");
  const meta = RESIDUAL_METRICS.find((item) => item.id === metric) ?? RESIDUAL_METRICS[0];
  const layers = useMemo(
    () => [...new Set(cells.map((cell) => cell.layer))].sort((left, right) => left - right),
    [cells]
  );
  const values = useMemo(() => {
    const map = new Map<string, number>();
    for (const cell of cells) map.set(`${cell.layer}:${cell.tokenIndex}`, cell[metric]);
    return map;
  }, [cells, metric]);
  const domain = useMemo(() => {
    const finite = cells
      .map((cell) => cell[metric])
      .filter((value) => Number.isFinite(value));
    if (finite.length === 0) return { min: 0, max: 1, clipped: false };
    const lower = percentile(finite, 0.02);
    const upper = percentile(finite, 0.95);
    if (!(upper > lower)) {
      const minimum = Math.min(...finite);
      const maximum = Math.max(...finite);
      return { min: minimum, max: maximum > minimum ? maximum : minimum + 1, clipped: false };
    }
    return {
      min: lower,
      max: upper,
      clipped: finite.some((value) => value < lower || value > upper)
    };
  }, [cells, metric]);
  const format = (value: number) => Number.isFinite(value) ? value.toFixed(meta.digits) : "—";
  const rows: HeatmapRow[] = layers.map((layer) => ({
    key: `L${layer}`,
    label: `L${layer}`,
    title: `Residual stream L${layer}`,
    values: tokens.map((token) => values.get(`${layer}:${token.index}`)),
    selected: layer === selectedLayer,
    onSelect: () => onSelectLayer(layer)
  }));

  return (
    <section className="chat-feature-visual" aria-label="Residual stream visualization">
      <header>
        <div>
          <h3>Residual stream heatmap</h3>
          <p>
            {layers.length} layers × {tokens.length} tokens · click a cell to inspect that layer
            and token
            {domain.clipped ? " · color domain clipped to p2–p95; hover cells for raw values" : ""}
          </p>
        </div>
        <label className="chat-feature-visual-controls">
          Metric
          <select
            aria-label="Residual heatmap metric"
            value={metric}
            onChange={(event) => setMetric(event.target.value as ResidualMetric)}
          >
            {RESIDUAL_METRICS.map((item) => (
              <option key={item.id} value={item.id}>{item.label}</option>
            ))}
          </select>
        </label>
      </header>
      {rows.length > 0 ? (
        <>
          <HeatmapTable
            ariaLabel="Residual stream heatmap"
            cornerLabel="Layer"
            tokens={tokens}
            rows={rows}
            min={domain.min}
            max={domain.max}
            signed={false}
            color={meta.color}
            format={format}
            selectedRange={selectedRange}
            selectedRowKey={`L${selectedLayer}`}
            rowHeaderWidth={44}
            cellWidth={30}
            rowHeight={18}
            maxHeight={Math.min(740, 72 + rows.length * 19 + 12)}
            onSelectCell={(rowKey, tokenIndex) => {
              onSelectLayer(Number(rowKey.slice(1)));
              onSelectToken(tokenIndex);
            }}
          />
          <HeatmapLegend
            signed={false}
            min={domain.min}
            max={domain.max}
            color={meta.color}
            format={format}
            clipped={domain.clipped}
          />
        </>
      ) : (
        <p className="feature-heatmap-empty">This run does not expose residual stream cells.</p>
      )}
    </section>
  );
}
