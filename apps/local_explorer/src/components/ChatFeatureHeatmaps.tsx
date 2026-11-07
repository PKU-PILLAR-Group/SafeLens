import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Download, Search } from "lucide-react";

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

function downloadTextFile(name: string, mime: string, content: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

function csvValue(value: unknown) {
  const text = value === undefined || value === null ? "" : String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
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
  const [hovered, setHovered] = useState<{
    row: HeatmapRow;
    token: TokenInfo;
    value: number;
    missing: boolean;
  } | null>(null);
  const [windowSize, setWindowSize] = useState(0);
  const [zoom, setZoom] = useState(1);
  const selectedTokenIndex = tokens.findIndex((token) => token.index >= selectedRange[0]);
  const anchorIndex = selectedTokenIndex >= 0 ? selectedTokenIndex : 0;
  const windowStart = windowSize > 0
    ? Math.min(
        Math.max(0, anchorIndex - Math.floor(windowSize / 2)),
        Math.max(0, tokens.length - windowSize)
      )
    : 0;
  const visibleTokens = windowSize > 0
    ? tokens.slice(windowStart, windowStart + windowSize)
    : tokens;
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
    "--heatmap-cell": `${cellWidth * zoom}px`,
    "--heatmap-row-height": `${rowHeight}px`
  } as CSSProperties;
  const exportSlug = ariaLabel.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  function focusCell(rowIndex: number, tokenIndex: number) {
    scrollRef.current
      ?.querySelector<HTMLButtonElement>(
        `button.feature-heatmap-cell[data-row-index="${rowIndex}"][data-token-index="${tokenIndex}"]`
      )
      ?.focus();
  }

  function handleCellKeyDown(
    event: React.KeyboardEvent<HTMLButtonElement>,
    rowIndex: number,
    tokenPosition: number
  ) {
    let nextRow = rowIndex;
    let nextToken = tokenPosition;
    if (event.key === "ArrowLeft") nextToken -= 1;
    else if (event.key === "ArrowRight") nextToken += 1;
    else if (event.key === "ArrowUp") nextRow -= 1;
    else if (event.key === "ArrowDown") nextRow += 1;
    else if (event.key === "Home") nextToken = 0;
    else if (event.key === "End") nextToken = visibleTokens.length - 1;
    else return;
    nextRow = Math.max(0, Math.min(rows.length - 1, nextRow));
    nextToken = Math.max(0, Math.min(visibleTokens.length - 1, nextToken));
    if (nextRow === rowIndex && nextToken === tokenPosition) return;
    event.preventDefault();
    focusCell(nextRow, visibleTokens[nextToken].index);
  }

  function exportCsv() {
    const header = [
      cornerLabel,
      ...visibleTokens.map((token) => `T${token.index} ${tokenText(token)}`)
    ];
    const lines = [
      header.map(csvValue).join(","),
      ...rows.map((row) => [
        row.title,
        ...visibleTokens.map((token) => {
          const value = row.values[token.index];
          return value === undefined || !Number.isFinite(value) ? "" : value;
        })
      ].map(csvValue).join(","))
    ];
    downloadTextFile(`${exportSlug}.csv`, "text/csv", lines.join("\n"));
  }

  function exportPng() {
    const scale = Math.min(2, Math.max(1, 8000 / Math.max(1, rowHeaderWidth + visibleTokens.length * cellWidth * zoom)));
    const cell = cellWidth * zoom;
    const headerHeight = 52;
    const labelWidth = Math.max(72, rowHeaderWidth);
    const canvas = document.createElement("canvas");
    canvas.width = Math.ceil((labelWidth + visibleTokens.length * cell) * scale);
    canvas.height = Math.ceil((headerHeight + rows.length * rowHeight) * scale);
    const context = canvas.getContext("2d");
    if (!context) return;
    context.scale(scale, scale);
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#34433f";
    context.font = "600 10px sans-serif";
    context.textAlign = "left";
    context.textBaseline = "middle";
    context.fillText(ariaLabel, 6, 13);
    context.fillStyle = "#7b8985";
    context.font = "8px sans-serif";
    rows.forEach((row, rowIndex) => {
      context.fillText(row.label, 6, headerHeight + rowIndex * rowHeight + rowHeight / 2);
    });
    visibleTokens.forEach((token, tokenIndex) => {
      context.save();
      context.translate(labelWidth + tokenIndex * cell + cell / 2, headerHeight - 4);
      context.rotate(-Math.PI / 4);
      context.fillStyle = "#7b8985";
      context.textAlign = "right";
      context.fillText(shortToken(token), 0, 0);
      context.restore();
    });
    rows.forEach((row, rowIndex) => {
      visibleTokens.forEach((token, tokenIndex) => {
        const raw = row.values[token.index];
        const missing = raw === undefined || !Number.isFinite(raw);
        const value = raw !== undefined && Number.isFinite(raw) ? raw : 0;
        context.fillStyle = missing
          ? "#f5f6f6"
          : heatColor(value, min, max, signed, color);
        context.fillRect(
          labelWidth + tokenIndex * cell,
          headerHeight + rowIndex * rowHeight,
          Math.max(1, cell - 1),
          Math.max(1, rowHeight - 1)
        );
      });
    });
    canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${exportSlug}.png`;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  }

  return (
    <>
      <div className="feature-heatmap-toolbar">
        <span>
          {visibleTokens.length} of {tokens.length} tokens · {rows.length} rows
        </span>
        <div className="feature-heatmap-toolbar-controls">
          <label>
            Window
            <select
              aria-label={`${ariaLabel} token window`}
              value={windowSize}
              onChange={(event) => setWindowSize(Number(event.target.value))}
            >
              <option value={0}>All tokens</option>
              <option value={30}>30 tokens</option>
              <option value={60}>60 tokens</option>
            </select>
          </label>
          <label>
            Zoom
            <select
              aria-label={`${ariaLabel} zoom`}
              value={zoom}
              onChange={(event) => setZoom(Number(event.target.value))}
            >
              <option value={0.8}>80%</option>
              <option value={1}>100%</option>
              <option value={1.3}>130%</option>
            </select>
          </label>
          <button type="button" aria-label={`Export ${ariaLabel} CSV`} onClick={exportCsv}>
            <Download size={12} /> CSV
          </button>
          <button type="button" aria-label={`Export ${ariaLabel} PNG`} onClick={exportPng}>
            <Download size={12} /> PNG
          </button>
        </div>
      </div>
      <div ref={scrollRef} className="feature-heatmap-scroll" style={{ maxHeight }}>
        <table className="feature-heatmap-table" style={tableStyle} aria-label={ariaLabel}>
        <thead>
          <tr>
            <th className="feature-heatmap-corner" scope="col">{cornerLabel}</th>
            {visibleTokens.map((token) => (
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
          {rows.map((row, rowIndex) => (
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
              {visibleTokens.map((token, tokenPosition) => {
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
                      data-row-index={rowIndex}
                      data-token-index={token.index}
                      className={`feature-heatmap-cell${missing ? " missing" : ""}${!missing && value > max ? " outlier" : ""}`}
                      style={missing ? undefined : { backgroundColor: heatColor(value, min, max, signed, color) }}
                      aria-label={label}
                      title={label}
                      onMouseEnter={() => setHovered({ row, token, value, missing })}
                      onFocus={() => setHovered({ row, token, value, missing })}
                      onMouseLeave={() => setHovered(null)}
                      onKeyDown={(event) => handleCellKeyDown(event, rowIndex, tokenPosition)}
                      onClick={() => {
                        setHovered({ row, token, value, missing });
                        onSelectCell(row.key, token.index);
                      }}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
        </table>
      </div>
      <div
        className="feature-heatmap-inspector"
        aria-label={`${ariaLabel} cell details`}
        aria-live="polite"
      >
        {hovered ? (
          <>
            <strong>{hovered.row.title}</strong>
            <span>T{hovered.token.index} {tokenText(hovered.token)}</span>
            <b>{hovered.missing ? "not loaded" : format(hovered.value)}</b>
            {!hovered.missing && hovered.value > max && <em>above color range</em>}
            {!hovered.missing && hovered.value < min && <em className="below">below color range</em>}
          </>
        ) : (
          <span>Hover a cell for exact values</span>
        )}
      </div>
    </>
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
  const [query, setQuery] = useState("");
  const [sortMode, setSortMode] = useState<"peak" | "index">("peak");
  const rows = useMemo(() => {
    const ordered = [...neurons].sort((left, right) =>
      sortMode === "index"
        ? left.neuron - right.neuron
        : right.maxAbsoluteActivation - left.maxAbsoluteActivation || left.neuron - right.neuron
    );
    const normalized = query.trim().toLowerCase();
    const exactNeuron = /^\d+$/.test(normalized) ? Number(normalized) : null;
    const matching = normalized
      ? ordered.filter((neuron) =>
          exactNeuron !== null
            ? neuron.neuron === exactNeuron
            : `${neuron.neuron} ${neuron.label} ${neuron.id}`.toLowerCase().includes(normalized)
        )
      : ordered;
    const selected = ordered.find((neuron) => neuron.neuron === selectedNeuron);
    let visible = matching.slice(0, MAX_MLP_ROWS);
    if (
      selected &&
      (!normalized || matching.some((neuron) => neuron.neuron === selected.neuron)) &&
      !visible.some((neuron) => neuron.neuron === selected.neuron)
    ) {
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
  }, [layer, neurons, onSelectNeuron, query, selectedNeuron, sortMode]);

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
        <div className="chat-feature-visual-controls-group">
          <label className="chat-feature-visual-controls chat-feature-heatmap-search">
            <Search size={12} />
            <input
              aria-label="Search MLP neurons"
              placeholder="Search neuron"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="chat-feature-visual-controls">
            Sort
            <select
              aria-label="Sort MLP neurons"
              value={sortMode}
              onChange={(event) => setSortMode(event.target.value as "peak" | "index")}
            >
              <option value="peak">Peak activation</option>
              <option value="index">Neuron index</option>
            </select>
          </label>
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
        <p className="feature-heatmap-empty">No MLP neurons match the current search for this layer.</p>
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
  const [scaleMode, setScaleMode] = useState<"robust" | "full">("robust");
  const [layerOrder, setLayerOrder] = useState<"asc" | "desc">("asc");
  const meta = RESIDUAL_METRICS.find((item) => item.id === metric) ?? RESIDUAL_METRICS[0];
  const layers = useMemo(
    () => [...new Set(cells.map((cell) => cell.layer))].sort((left, right) =>
      layerOrder === "asc" ? left - right : right - left
    ),
    [cells, layerOrder]
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
    if (scaleMode === "full") {
      const minimum = Math.min(...finite);
      const maximum = Math.max(...finite);
      return { min: minimum, max: maximum > minimum ? maximum : minimum + 1, clipped: false };
    }
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
  }, [cells, metric, scaleMode]);
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
        <div className="chat-feature-visual-controls-group">
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
          <label className="chat-feature-visual-controls">
            Scale
            <select
              aria-label="Residual heatmap scale"
              value={scaleMode}
              onChange={(event) => setScaleMode(event.target.value as "robust" | "full")}
            >
              <option value="robust">Robust p2–p95</option>
              <option value="full">Full range</option>
            </select>
          </label>
          <label className="chat-feature-visual-controls">
            Order
            <select
              aria-label="Residual heatmap layer order"
              value={layerOrder}
              onChange={(event) => setLayerOrder(event.target.value as "asc" | "desc")}
            >
              <option value="asc">Layer ↑</option>
              <option value="desc">Layer ↓</option>
            </select>
          </label>
        </div>
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
