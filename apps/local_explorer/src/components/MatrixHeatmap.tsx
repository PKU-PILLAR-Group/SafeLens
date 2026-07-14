import { useEffect, useId, useMemo, useRef, useState } from "react";
import {
  Check,
  Copy,
  Crosshair,
  GitCompareArrows,
  Hand,
  Maximize2,
  PanelLeft,
  Pin,
  RotateCcw,
  X,
  ZoomIn,
  ZoomOut
} from "lucide-react";

import type { MetricProvenance, NormalizationMode, TokenInfo } from "../types";
import { formatMetricDelta, formatMetricNumber } from "../metricFormatting";
import { recordExplorerPerformance } from "../state/useExplorerPerformance";
import { MatrixOverviewNavigator } from "./MatrixOverviewNavigator";
import { useMatrixViewport } from "./MatrixViewportControls";

export const MATRIX_CANVAS_CELL_THRESHOLD = 2_500;
const MATRIX_ROW_HEIGHT = 29;
const MATRIX_GAP = 3;
const MATRIX_ROW_LABEL_WIDTH = 48;

export interface MatrixCellDatum {
  row: number;
  column: number;
  value: number;
  rawValue: number;
  metric: string;
  sourceKey: string;
  available?: boolean;
}

export interface MetricOption {
  id: string;
  label: string;
}

interface MatrixHeatmapProps {
  title: string;
  subtitle: string;
  rows: number[];
  columns: TokenInfo[];
  cells: MatrixCellDatum[];
  metric: string;
  metricOptions: MetricOption[];
  provenance: MetricProvenance;
  normalization: NormalizationMode;
  selectedRow: number;
  selectedColumn: number;
  selectedRange?: [number, number];
  hoveredColumn: number | null;
  color: "residual" | "attention" | "mlp" | "nla" | "causal";
  onMetricChange: (metric: string) => void;
  onNormalizationChange: (normalization: NormalizationMode) => void;
  onSelectCell: (row: number, column: number) => void;
  onRangeSelect: (range?: [number, number]) => void;
  onHoverColumn: (column: number | null) => void;
  onPin: () => void;
  onPinCell: (row: number, column: number) => void;
}

export function MatrixHeatmap({
  title,
  subtitle,
  rows,
  columns,
  cells,
  metric,
  metricOptions,
  provenance,
  normalization,
  selectedRow,
  selectedColumn,
  selectedRange,
  hoveredColumn,
  color,
  onMetricChange,
  onNormalizationChange,
  onSelectCell,
  onRangeSelect,
  onHoverColumn,
  onPin,
  onPinCell
}: MatrixHeatmapProps) {
  const viewport = useMatrixViewport({
    initialSize: 16,
    minimumSize: 10,
    maximumSize: 34,
    itemCount: columns.length,
    labelWidth: MATRIX_ROW_LABEL_WIDTH,
    gap: MATRIX_GAP,
    sessionKey: "residual",
    managePan: false
  });
  const cellWidth = viewport.size;
  const interactionMode = viewport.mode;
  const axesPinned = viewport.axesPinned;
  const [comparisonCell, setComparisonCell] = useState<MatrixCellDatum | null>(null);
  const [hoveredCell, setHoveredCell] = useState<MatrixCellDatum | null>(null);
  const [brushStart, setBrushStart] = useState<number | null>(null);
  const [brushEnd, setBrushEnd] = useState<number | null>(null);
  const brushStartRef = useRef<number | null>(null);
  const brushEndRef = useRef<number | null>(null);
  const didBrushRef = useRef(false);
  const didPanRef = useRef(false);
  const panRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    scrollLeft: number;
    scrollTop: number;
  } | null>(null);
  const scrollRef = viewport.scrollRef;
  const gridRef = useRef<HTMLDivElement>(null);
  const canvasFocusRef = useRef<(() => void) | null>(null);
  const rangeSelectRef = useRef(onRangeSelect);
  rangeSelectRef.current = onRangeSelect;
  const [copied, setCopied] = useState(false);
  const [canvasStats, setCanvasStats] = useState({ visibleCells: 0, drawMs: 0, hoverMs: 0 });

  const logicalCellCount = rows.length * columns.length;
  const renderMode = logicalCellCount >= MATRIX_CANVAS_CELL_THRESHOLD ? "canvas" : "dom";

  const cellMap = useMemo(
    () => new Map(cells.map((cell) => [`${cell.row}:${cell.column}`, cell])),
    [cells]
  );
  const rawBounds = useMemo(() => {
    let minimum = Number.POSITIVE_INFINITY;
    let maximum = Number.NEGATIVE_INFINITY;
    for (const cell of cells) {
      if (cell.available === false) continue;
      minimum = Math.min(minimum, cell.rawValue);
      maximum = Math.max(maximum, cell.rawValue);
    }
    return Number.isFinite(minimum) ? [minimum, maximum] : [0, 1];
  }, [cells]);
  const legendBounds = normalization === "raw"
    ? rawBounds
    : [0, 1];
  const legendMidpoint = (legendBounds[0] + legendBounds[1]) / 2;

  useEffect(() => {
    function columnAtPointer(event: PointerEvent) {
      if (renderMode === "canvas") return null;
      const target = document
        .elementFromPoint(event.clientX, event.clientY)
        ?.closest<HTMLElement>(".matrix-cell");
      const column = Number(target?.dataset.column);
      return Number.isInteger(column) ? column : null;
    }
    function updateBrush(event: PointerEvent) {
      if (brushStartRef.current === null) {
        return;
      }
      const column = columnAtPointer(event);
      if (column !== null) {
        brushEndRef.current = column;
        didBrushRef.current = column !== brushStartRef.current;
        setBrushEnd(column);
      }
    }
    function finishBrush(event: PointerEvent) {
      const start = brushStartRef.current;
      const end = columnAtPointer(event) ?? brushEndRef.current;
      if (start === null || end === null) {
        setBrushStart(null);
        setBrushEnd(null);
        return;
      }
      if (start !== end) {
        didBrushRef.current = true;
        rangeSelectRef.current(normalizeRange(start, end));
      }
      brushStartRef.current = null;
      brushEndRef.current = null;
      setBrushStart(null);
      setBrushEnd(null);
      window.setTimeout(() => {
        didBrushRef.current = false;
      }, 0);
    }
    window.addEventListener("pointermove", updateBrush);
    window.addEventListener("pointerup", finishBrush);
    return () => {
      window.removeEventListener("pointermove", updateBrush);
      window.removeEventListener("pointerup", finishBrush);
    };
  }, [renderMode]);

  useEffect(() => {
    function updatePan(event: PointerEvent) {
      const pan = panRef.current;
      const viewport = scrollRef.current;
      if (!pan || !viewport || pan.pointerId !== event.pointerId) return;
      const deltaX = event.clientX - pan.startX;
      const deltaY = event.clientY - pan.startY;
      didPanRef.current = Math.hypot(deltaX, deltaY) > 3;
      viewport.scrollLeft = pan.scrollLeft - deltaX;
      viewport.scrollTop = pan.scrollTop - deltaY;
    }
    function finishPan(event: PointerEvent) {
      if (panRef.current?.pointerId !== event.pointerId) return;
      panRef.current = null;
      window.setTimeout(() => { didPanRef.current = false; }, 0);
    }
    window.addEventListener("pointermove", updatePan);
    window.addEventListener("pointerup", finishPan);
    window.addEventListener("pointercancel", finishPan);
    return () => {
      window.removeEventListener("pointermove", updatePan);
      window.removeEventListener("pointerup", finishPan);
      window.removeEventListener("pointercancel", finishPan);
    };
  }, []);

  const activeRange =
    brushStart !== null && brushEnd !== null
      ? normalizeRange(brushStart, brushEnd)
      : selectedRange;
  const minGridWidth =
    MATRIX_ROW_LABEL_WIDTH +
    columns.length * cellWidth +
    (columns.length + 1) * MATRIX_GAP;

  async function copyCacheKey() {
    if (!hoveredCell) {
      return;
    }
    await navigator.clipboard.writeText(hoveredCell.sourceKey);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 900);
  }

  function resetView() {
    viewport.reset();
    setComparisonCell(null);
    onRangeSelect(undefined);
  }

  function fitToWidth() {
    viewport.fitToWidth();
  }

  function moveFocus(row: number, column: number, key: string) {
    const rowIndex = Math.max(0, rows.indexOf(row));
    const columnIndex = Math.max(0, columns.findIndex((item) => item.index === column));
    let nextRow = rowIndex;
    let nextColumn = columnIndex;
    if (key === "ArrowLeft") nextColumn = Math.max(0, columnIndex - 1);
    if (key === "ArrowRight") nextColumn = Math.min(columns.length - 1, columnIndex + 1);
    if (key === "ArrowUp") nextRow = Math.max(0, rowIndex - 1);
    if (key === "ArrowDown") nextRow = Math.min(rows.length - 1, rowIndex + 1);
    if (key === "Home") nextColumn = 0;
    if (key === "End") nextColumn = columns.length - 1;
    const targetRow = rows[nextRow];
    const targetColumn = columns[nextColumn]?.index;
    if (targetRow === undefined || targetColumn === undefined) return;
    onSelectCell(targetRow, targetColumn);
    window.requestAnimationFrame(() => {
      if (renderMode === "canvas") {
        canvasFocusRef.current?.();
        return;
      }
      gridRef.current
        ?.querySelector<HTMLButtonElement>(
          `.matrix-cell[data-row="${targetRow}"][data-column="${targetColumn}"]`
        )
        ?.focus();
    });
  }

  return (
    <section className={`surface matrix-section matrix-${color}`}>
      <div className="surface-header matrix-header">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
        <span className="evidence-kind">{provenance.kind.replace("_", " ")}</span>
      </div>

      <div className="matrix-toolbar" aria-label="Matrix controls">
        <label>
          <span>Metric</span>
          <select value={metric} onChange={(event) => onMetricChange(event.target.value)}>
            {metricOptions.map((option) => (
              <option key={option.id} value={option.id}>{option.label}</option>
            ))}
          </select>
        </label>
        <div className="toolbar-segment" aria-label="Normalization">
          <button
            className={normalization === "normalized" ? "active" : ""}
            onClick={() => onNormalizationChange("normalized")}
          >
            Normalized
          </button>
          <button
            className={normalization === "raw" ? "active" : ""}
            onClick={() => onNormalizationChange("raw")}
          >
            Raw
          </button>
        </div>
        <div className="toolbar-segment" aria-label="Matrix interaction mode">
          <button
            className={interactionMode === "select" ? "active" : ""}
            aria-label="Select matrix cells"
            aria-pressed={interactionMode === "select"}
            title="Select and brush"
            onClick={() => viewport.setMode("select")}
          >
            <Crosshair size={14} />
          </button>
          <button
            className={interactionMode === "pan" ? "active" : ""}
            aria-label="Pan matrix"
            aria-pressed={interactionMode === "pan"}
            title="Drag to pan"
            onClick={() => viewport.setMode("pan")}
          >
            <Hand size={14} />
          </button>
        </div>
        <div className="toolbar-actions">
          <button
            aria-label="Zoom out"
            title="Zoom out"
            onClick={() => viewport.zoomBy(-2)}
          >
            <ZoomOut size={15} />
          </button>
          <button
            className={viewport.fitMode === "fit" ? "active" : ""}
            aria-label="Fit matrix to width"
            aria-pressed={viewport.fitMode === "fit"}
            title="Fit to width"
            onClick={fitToWidth}
          >
            <Maximize2 size={14} />
          </button>
          <button
            className={axesPinned ? "active" : ""}
            aria-label="Pin matrix axes"
            aria-pressed={axesPinned}
            title={axesPinned ? "Unpin row labels" : "Pin row labels"}
            onClick={() => viewport.setAxesPinned((pinned) => !pinned)}
          >
            <PanelLeft size={14} />
          </button>
          <button
            aria-label="Zoom in"
            title="Zoom in"
            onClick={() => viewport.zoomBy(2)}
          >
            <ZoomIn size={15} />
          </button>
          <button
            aria-label="Reset matrix view"
            title="Reset zoom and range"
            onClick={() => {
              resetView();
            }}
          >
            <RotateCcw size={14} />
          </button>
          <button aria-label="Pin current evidence" title="Pin current evidence" onClick={onPin}>
            <Pin size={14} />
          </button>
          <button
            aria-label="Copy hovered cache key"
            title={hoveredCell ? "Copy hovered cache key" : "Hover a cell to copy its cache key"}
            disabled={!hoveredCell}
            onClick={copyCacheKey}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        </div>
        <span
          className={`matrix-render-status mode-${renderMode}`}
          aria-label="Matrix rendering status"
          title={renderMode === "canvas" ? "Viewport-rendered Canvas mode" : "Accessible DOM cell mode"}
        >
          <b>{renderMode}</b>
          {renderMode === "canvas"
            ? `${canvasStats.visibleCells.toLocaleString()} / ${logicalCellCount.toLocaleString()} visible · ${canvasStats.drawMs.toFixed(1)}ms`
            : `${logicalCellCount.toLocaleString()} cells`}
        </span>
      </div>

      <div className={`range-summary ${activeRange ? "" : "idle"}`}>
        {activeRange ? (
          <>
            <span>Token range {activeRange[0]}–{activeRange[1]}</span>
            <button onClick={() => onRangeSelect(undefined)}>Clear</button>
          </>
        ) : (
          <span>Token range · all tokens</span>
        )}
      </div>

      <div className="matrix-selection-summary" aria-label="Matrix selection summary">
        <span><b>Primary</b>L{selectedRow} · token {selectedColumn}</span>
        <span className={comparisonCell ? "active" : ""}>
          <GitCompareArrows size={13} />
          <b>Anchor</b>
          {comparisonCell ? `L${comparisonCell.row} · token ${comparisonCell.column}` : "none"}
        </span>
        <button
          aria-label="Clear matrix comparison anchor"
          title="Clear comparison anchor"
          disabled={!comparisonCell}
          onClick={() => setComparisonCell(null)}
        >
          <X size={13} />
        </button>
      </div>

      <div
        ref={scrollRef}
        className={`matrix-scroll ${renderMode === "canvas" ? "canvas-mode" : ""} ${interactionMode === "pan" ? "pan-mode" : ""}`}
        onDoubleClick={resetView}
        onWheel={(event) => {
          if (!event.ctrlKey && !event.metaKey) return;
          event.preventDefault();
          viewport.zoomBy(event.deltaY < 0 ? 2 : -2);
        }}
        onPointerDownCapture={(event) => {
          if (interactionMode !== "pan") return;
          event.preventDefault();
          event.stopPropagation();
          panRef.current = {
            pointerId: event.pointerId,
            startX: event.clientX,
            startY: event.clientY,
            scrollLeft: event.currentTarget.scrollLeft,
            scrollTop: event.currentTarget.scrollTop
          };
          didPanRef.current = false;
        }}
      >
        {renderMode === "canvas" ? (
          <CanvasMatrix
            scrollRef={scrollRef}
            focusRef={canvasFocusRef}
            rows={rows}
            columns={columns}
            cellMap={cellMap}
            rawBounds={rawBounds as [number, number]}
            normalization={normalization}
            selectedRow={selectedRow}
            selectedColumn={selectedColumn}
            comparisonCell={comparisonCell}
            hoveredColumn={hoveredColumn}
            activeRange={activeRange}
            axesPinned={axesPinned}
            cellWidth={cellWidth}
            minGridWidth={minGridWidth}
            color={color}
            interactionMode={interactionMode}
            onHover={(cell, latency) => {
              setHoveredCell(cell);
              onHoverColumn(cell?.column ?? null);
              setCanvasStats((current) => ({ ...current, hoverMs: latency }));
              if (cell) {
                recordExplorerPerformance("matrix-hover", {
                  latencyMs: latency,
                  renderMode: "canvas",
                  row: cell.row,
                  column: cell.column
                });
              }
            }}
            onSelect={(row, column, modifiers) => {
              const cell = cellMap.get(`${row}:${column}`);
              if (modifiers.pin) {
                if (cell?.available !== false) onPinCell(row, column);
                return;
              }
              if (modifiers.anchor) {
                if (cell?.available !== false) setComparisonCell(cell ?? null);
                return;
              }
              onSelectCell(row, column);
            }}
            onRangeSelect={onRangeSelect}
            onStats={(stats) => setCanvasStats((current) => ({ ...current, ...stats }))}
          />
        ) : (
          <div
            ref={gridRef}
            className={`matrix-grid ${axesPinned ? "axes-pinned" : ""}`}
            style={{
              gridTemplateColumns: `${MATRIX_ROW_LABEL_WIDTH}px repeat(${columns.length}, ${cellWidth}px)`,
              minWidth: `${minGridWidth}px`
            }}
          >
            <div className="matrix-corner" />
            {columns.map((token) => (
              <div
                key={token.index}
                className={`matrix-column-label ${inRange(token.index, activeRange) ? "in-range" : ""}`}
                title={`${token.text} · token ${token.index} · id ${token.tokenId}`}
              >
                {token.index}
              </div>
            ))}
            {rows.map((row) => (
              <MatrixRow
                key={row}
                row={row}
                columns={columns}
                cellMap={cellMap}
                rawBounds={rawBounds as [number, number]}
                normalization={normalization}
                selectedRow={selectedRow}
                selectedColumn={selectedColumn}
                comparisonCell={comparisonCell}
                hoveredColumn={hoveredColumn}
                activeRange={activeRange}
                onBrushStart={(column) => {
                  if (interactionMode !== "select") return;
                  didBrushRef.current = false;
                  brushStartRef.current = column;
                  brushEndRef.current = column;
                  setBrushStart(column);
                  setBrushEnd(column);
                }}
                onHover={(cell) => {
                  setHoveredCell(cell);
                  onHoverColumn(cell?.column ?? null);
                }}
                onSelectCell={(row, column, event) => {
                  if (didBrushRef.current || didPanRef.current) return;
                  const cell = cellMap.get(`${row}:${column}`);
                  if (event.metaKey || event.ctrlKey) {
                    if (cell?.available !== false) onPinCell(row, column);
                    return;
                  }
                  if (event.shiftKey) {
                    if (cell?.available !== false) setComparisonCell(cell ?? null);
                    return;
                  }
                  onSelectCell(row, column);
                }}
                onMoveFocus={moveFocus}
              />
            ))}
          </div>
        )}
      </div>

      <MatrixTooltip
        cell={hoveredCell}
        token={
          hoveredCell
            ? columns.find((column) => column.index === hoveredCell.column)
            : undefined
        }
        normalization={normalization}
        provenance={provenance}
        comparisonCell={comparisonCell}
      />

      <div
        className="matrix-legend"
        aria-label="Matrix legend"
        data-domain="sequential"
      >
        <div>
          <span><i className="legend-swatch legend-low" />min {formatLegendValue(legendBounds[0], normalization, metric)}</span>
          <span><i className="legend-swatch legend-mid" />mid {formatLegendValue(legendMidpoint, normalization, metric)}</span>
          <span><i className="legend-swatch legend-high" />max {formatLegendValue(legendBounds[1], normalization, metric)}</span>
          <span><i className="legend-swatch legend-missing" />Unavailable</span>
        </div>
        <b>{normalization === "raw" ? "raw values · min-max color" : provenance.normalization}</b>
      </div>
    </section>
  );
}

interface CanvasMatrixProps {
  scrollRef: React.RefObject<HTMLDivElement | null>;
  focusRef: React.MutableRefObject<(() => void) | null>;
  rows: number[];
  columns: TokenInfo[];
  cellMap: Map<string, MatrixCellDatum>;
  rawBounds: [number, number];
  normalization: NormalizationMode;
  selectedRow: number;
  selectedColumn: number;
  comparisonCell: MatrixCellDatum | null;
  hoveredColumn: number | null;
  activeRange?: [number, number];
  axesPinned: boolean;
  cellWidth: number;
  minGridWidth: number;
  color: MatrixHeatmapProps["color"];
  interactionMode: "select" | "pan";
  onHover: (cell: MatrixCellDatum | null, latency: number) => void;
  onSelect: (
    row: number,
    column: number,
    modifiers: { pin: boolean; anchor: boolean }
  ) => void;
  onRangeSelect: (range?: [number, number]) => void;
  onStats: (stats: { visibleCells: number; drawMs: number }) => void;
}

function CanvasMatrix({
  scrollRef,
  focusRef,
  rows,
  columns,
  cellMap,
  rawBounds,
  normalization,
  selectedRow,
  selectedColumn,
  comparisonCell,
  hoveredColumn,
  activeRange,
  axesPinned,
  cellWidth,
  minGridWidth,
  color,
  interactionMode,
  onHover,
  onSelect,
  onRangeSelect,
  onStats
}: CanvasMatrixProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const descriptionId = useId();
  const statsRef = useRef(onStats);
  const hoverRef = useRef(onHover);
  const selectRef = useRef(onSelect);
  const rangeRef = useRef(onRangeSelect);
  const hoveredKeyRef = useRef<string | null>(null);
  const dragRef = useRef<{
    pointerId: number;
    row: number;
    startColumn: number;
    endColumn: number;
    pin: boolean;
    anchor: boolean;
  } | null>(null);
  statsRef.current = onStats;
  hoverRef.current = onHover;
  selectRef.current = onSelect;
  rangeRef.current = onRangeSelect;
  const rowStride = MATRIX_ROW_HEIGHT + MATRIX_GAP;
  const columnStride = cellWidth + MATRIX_GAP;
  const totalHeight = MATRIX_ROW_HEIGHT + rows.length * rowStride + MATRIX_GAP;
  const selectedCell = cellMap.get(`${selectedRow}:${selectedColumn}`);

  focusRef.current = () => canvasRef.current?.focus();

  useEffect(() => {
    const viewport = scrollRef.current as HTMLDivElement;
    const canvas = canvasRef.current as HTMLCanvasElement;
    if (!viewport || !canvas) return;
    let frame = 0;

    function scheduleDraw() {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(draw);
    }

    function draw() {
      const started = performance.now();
      const width = Math.max(1, viewport.clientWidth);
      const height = Math.max(1, viewport.clientHeight);
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const backingWidth = Math.round(width * dpr);
      const backingHeight = Math.round(height * dpr);
      if (canvas.width !== backingWidth || canvas.height !== backingHeight) {
        canvas.width = backingWidth;
        canvas.height = backingHeight;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
      }
      canvas.style.transform = `translate(${viewport.scrollLeft}px, ${viewport.scrollTop}px)`;
      const context = canvas.getContext("2d", { alpha: false });
      if (!context) return;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.clearRect(0, 0, width, height);
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, width, height);

      const firstColumn = clampInteger(
        Math.floor((viewport.scrollLeft - MATRIX_ROW_LABEL_WIDTH) / columnStride) - 1,
        0,
        columns.length - 1
      );
      const lastColumn = clampInteger(
        Math.ceil((viewport.scrollLeft + width - MATRIX_ROW_LABEL_WIDTH) / columnStride) + 1,
        0,
        columns.length - 1
      );
      const firstRow = clampInteger(
        Math.floor((viewport.scrollTop - MATRIX_ROW_HEIGHT) / rowStride) - 1,
        0,
        rows.length - 1
      );
      const lastRow = clampInteger(
        Math.ceil((viewport.scrollTop + height - MATRIX_ROW_HEIGHT) / rowStride) + 1,
        0,
        rows.length - 1
      );
      const accent = matrixAccent(color);
      let visibleCells = 0;

      context.font = "10px Inter, sans-serif";
      context.textBaseline = "middle";
      for (let rowIndex = firstRow; rowIndex <= lastRow; rowIndex += 1) {
        const row = rows[rowIndex];
        if (row === undefined) continue;
        const y = MATRIX_ROW_HEIGHT + rowIndex * rowStride - viewport.scrollTop;
        const labelX = axesPinned ? 0 : -viewport.scrollLeft;
        context.fillStyle = selectedRow === row ? "#dcefeb" : "#eef3f5";
        context.fillRect(labelX, y, MATRIX_ROW_LABEL_WIDTH, MATRIX_ROW_HEIGHT);
        context.fillStyle = selectedRow === row ? "#12464d" : "#314751";
        context.textAlign = "center";
        context.fillText(`L${row}`, labelX + MATRIX_ROW_LABEL_WIDTH / 2, y + MATRIX_ROW_HEIGHT / 2);

        for (let columnIndex = firstColumn; columnIndex <= lastColumn; columnIndex += 1) {
          const token = columns[columnIndex];
          if (!token) continue;
          const x = MATRIX_ROW_LABEL_WIDTH + columnIndex * columnStride - viewport.scrollLeft;
          const cell = cellMap.get(`${row}:${token.index}`);
          const available = cell !== undefined && cell.available !== false;
          const signal = cell
            ? normalization === "raw"
              ? normalizeRaw(cell.rawValue, rawBounds)
              : cell.value
            : 0;
          context.fillStyle = available
            ? mixHex("#edf1f4", accent, Math.max(0, Math.min(1, signal)) * 0.8)
            : "#e4e9eb";
          context.fillRect(x, y, cellWidth, MATRIX_ROW_HEIGHT);
          visibleCells += 1;
          if (!available) {
            context.strokeStyle = "#c6d0d4";
            context.lineWidth = 1;
            for (let offset = -MATRIX_ROW_HEIGHT; offset < cellWidth; offset += 6) {
              context.beginPath();
              context.moveTo(x + offset, y + MATRIX_ROW_HEIGHT);
              context.lineTo(x + offset + MATRIX_ROW_HEIGHT, y);
              context.stroke();
            }
          }
          if (inRange(token.index, activeRange)) {
            context.fillStyle = "#d49a29";
            context.fillRect(x, y + MATRIX_ROW_HEIGHT - 3, cellWidth, 3);
          }
          if (hoveredColumn === token.index) {
            context.strokeStyle = "#294b54";
            context.lineWidth = 1;
            context.strokeRect(x + 0.5, y + 0.5, cellWidth - 1, MATRIX_ROW_HEIGHT - 1);
          }
          const selected = selectedRow === row && selectedColumn === token.index;
          const compared = comparisonCell?.row === row && comparisonCell.column === token.index;
          if (selected || compared) {
            context.save();
            context.strokeStyle = selected ? "#153f48" : "#c1841d";
            context.lineWidth = 2;
            if (compared && !selected) context.setLineDash([4, 2]);
            context.strokeRect(x + 1, y + 1, cellWidth - 2, MATRIX_ROW_HEIGHT - 2);
            context.restore();
          }
        }
      }

      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, width, MATRIX_ROW_HEIGHT);
      context.font = "10px Inter, sans-serif";
      context.textAlign = "center";
      context.textBaseline = "middle";
      for (let columnIndex = firstColumn; columnIndex <= lastColumn; columnIndex += 1) {
        const token = columns[columnIndex];
        if (!token) continue;
        const x = MATRIX_ROW_LABEL_WIDTH + columnIndex * columnStride - viewport.scrollLeft;
        const selected = token.index === selectedColumn;
        if (selected || inRange(token.index, activeRange)) {
          context.fillStyle = selected ? "#e1f1ee" : "#fff4da";
          context.fillRect(x, 0, cellWidth, MATRIX_ROW_HEIGHT);
        }
        context.fillStyle = selected ? "#155f59" : "#687681";
        context.fillText(String(token.index), x + cellWidth / 2, MATRIX_ROW_HEIGHT / 2);
      }
      context.strokeStyle = "rgba(30, 49, 58, 0.16)";
      context.beginPath();
      context.moveTo(0, MATRIX_ROW_HEIGHT - 0.5);
      context.lineTo(width, MATRIX_ROW_HEIGHT - 0.5);
      context.stroke();

      if (axesPinned) {
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, MATRIX_ROW_LABEL_WIDTH, Math.min(MATRIX_ROW_HEIGHT, height));
        context.strokeStyle = "rgba(30, 49, 58, 0.12)";
        context.beginPath();
        context.moveTo(MATRIX_ROW_LABEL_WIDTH - 0.5, 0);
        context.lineTo(MATRIX_ROW_LABEL_WIDTH - 0.5, height);
        context.stroke();
      }
      const drawMs = performance.now() - started;
      canvas.dataset.visibleCells = String(visibleCells);
      canvas.dataset.drawMs = drawMs.toFixed(3);
      canvas.dataset.columnHeaderSticky = "true";
      statsRef.current({ visibleCells, drawMs });
    }

    viewport.addEventListener("scroll", scheduleDraw, { passive: true });
    const observer = new ResizeObserver(scheduleDraw);
    observer.observe(viewport);
    scheduleDraw();
    return () => {
      window.cancelAnimationFrame(frame);
      viewport.removeEventListener("scroll", scheduleDraw);
      observer.disconnect();
    };
  }, [activeRange, axesPinned, cellMap, cellWidth, color, columns, comparisonCell, hoveredColumn, normalization, rawBounds, rows, scrollRef, selectedColumn, selectedRow]);

  useEffect(() => {
    const viewport = scrollRef.current;
    if (!viewport) return;
    const rowIndex = rows.indexOf(selectedRow);
    const columnIndex = columns.findIndex((column) => column.index === selectedColumn);
    if (rowIndex < 0 || columnIndex < 0) return;
    const x = MATRIX_ROW_LABEL_WIDTH + columnIndex * columnStride;
    const y = MATRIX_ROW_HEIGHT + rowIndex * rowStride;
    if (x < viewport.scrollLeft + MATRIX_ROW_LABEL_WIDTH) {
      viewport.scrollLeft = Math.max(0, x - MATRIX_ROW_LABEL_WIDTH);
    } else if (x + cellWidth > viewport.scrollLeft + viewport.clientWidth) {
      viewport.scrollLeft = x + cellWidth - viewport.clientWidth;
    }
    if (y < viewport.scrollTop + MATRIX_ROW_HEIGHT) {
      viewport.scrollTop = Math.max(0, y - MATRIX_ROW_HEIGHT);
    } else if (y + MATRIX_ROW_HEIGHT > viewport.scrollTop + viewport.clientHeight) {
      viewport.scrollTop = y + MATRIX_ROW_HEIGHT - viewport.clientHeight;
    }
  }, [cellWidth, columnStride, columns, rowStride, rows, scrollRef, selectedColumn, selectedRow]);

  function hitCell(event: React.PointerEvent<HTMLCanvasElement>) {
    const viewport = scrollRef.current;
    if (!viewport) return null;
    const rect = event.currentTarget.getBoundingClientRect();
    if (event.clientY - rect.top < MATRIX_ROW_HEIGHT) return null;
    const globalX = event.clientX - rect.left + viewport.scrollLeft;
    const globalY = event.clientY - rect.top + viewport.scrollTop;
    const columnIndex = Math.floor((globalX - MATRIX_ROW_LABEL_WIDTH) / columnStride);
    const rowIndex = Math.floor((globalY - MATRIX_ROW_HEIGHT) / rowStride);
    if (columnIndex < 0 || rowIndex < 0 || columnIndex >= columns.length || rowIndex >= rows.length) {
      return null;
    }
    const withinColumn = (globalX - MATRIX_ROW_LABEL_WIDTH) % columnStride;
    const withinRow = (globalY - MATRIX_ROW_HEIGHT) % rowStride;
    if (withinColumn >= cellWidth || withinRow >= MATRIX_ROW_HEIGHT) return null;
    const row = rows[rowIndex];
    const column = columns[columnIndex]?.index;
    return row === undefined || column === undefined ? null : { row, column };
  }

  function moveSelection(key: string, pin = false, anchor = false) {
    const rowIndex = Math.max(0, rows.indexOf(selectedRow));
    const columnIndex = Math.max(0, columns.findIndex((item) => item.index === selectedColumn));
    let nextRow = rowIndex;
    let nextColumn = columnIndex;
    if (key === "ArrowLeft") nextColumn = Math.max(0, columnIndex - 1);
    if (key === "ArrowRight") nextColumn = Math.min(columns.length - 1, columnIndex + 1);
    if (key === "ArrowUp") nextRow = Math.max(0, rowIndex - 1);
    if (key === "ArrowDown") nextRow = Math.min(rows.length - 1, rowIndex + 1);
    if (key === "Home") nextColumn = 0;
    if (key === "End") nextColumn = columns.length - 1;
    const row = rows[nextRow];
    const column = columns[nextColumn]?.index;
    if (row !== undefined && column !== undefined) selectRef.current(row, column, { pin, anchor });
  }

  return <>
    <MatrixOverviewNavigator
      scrollRef={scrollRef}
      rowCount={rows.length}
      columnCount={columns.length}
      totalWidth={minGridWidth}
      totalHeight={totalHeight}
      selectedRow={Math.max(0, rows.indexOf(selectedRow))}
      selectedColumn={Math.max(0, columns.findIndex((column) => column.index === selectedColumn))}
      label="Canvas matrix"
      revision={`${normalization}:${color}:${cellMap.size}`}
      cellColor={(rowIndex, columnIndex) => {
        const row = rows[rowIndex];
        const token = columns[columnIndex];
        const cell = row === undefined || !token ? undefined : cellMap.get(`${row}:${token.index}`);
        if (!cell || cell.available === false) return "#dfe6e8";
        const signal = normalization === "raw"
          ? normalizeRaw(cell.rawValue, rawBounds)
          : cell.value;
        return mixHex(
          "#edf1f4",
          matrixAccent(color),
          Math.max(0, Math.min(1, signal)) * 0.8
        );
      }}
    />
    <div
      className="matrix-canvas-spacer"
      style={{ width: `${minGridWidth}px`, height: `${totalHeight}px` }}
    >
      <div id={descriptionId} className="visually-hidden" aria-live="polite">
        {selectedCell && selectedCell.available !== false
          ? `Selected layer ${selectedRow}, token ${selectedColumn}, displayed value ${formatValue(selectedCell, normalization, "exact")}, raw value ${formatMetricNumber(selectedCell.rawValue, selectedCell.metric, "exact")}, cache key ${selectedCell.sourceKey}.`
          : `Selected layer ${selectedRow}, token ${selectedColumn}, unavailable.`}
      </div>
      <canvas
        ref={canvasRef}
        className="matrix-canvas"
        role="grid"
        tabIndex={0}
        aria-label={`Canvas matrix, ${rows.length} rows by ${columns.length} columns; selected layer ${selectedRow}, token ${selectedColumn}`}
        aria-rowcount={rows.length}
        aria-colcount={columns.length}
        aria-describedby={descriptionId}
        aria-keyshortcuts="ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Space"
        data-render-mode="canvas"
        onKeyDown={(event) => {
          if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) {
            event.preventDefault();
            event.stopPropagation();
            moveSelection(event.key);
          } else if (event.key === "Enter") {
            event.preventDefault();
            moveSelection("", false, event.shiftKey);
          } else if (event.key === " ") {
            event.preventDefault();
            moveSelection("", true, false);
          }
        }}
        onPointerDown={(event) => {
          if (interactionMode !== "select") return;
          const hit = hitCell(event);
          if (!hit) return;
          event.currentTarget.setPointerCapture(event.pointerId);
          dragRef.current = {
            pointerId: event.pointerId,
            row: hit.row,
            startColumn: hit.column,
            endColumn: hit.column,
            pin: event.metaKey || event.ctrlKey,
            anchor: event.shiftKey
          };
        }}
        onPointerMove={(event) => {
          const started = performance.now();
          const hit = hitCell(event);
          const key = hit ? `${hit.row}:${hit.column}` : null;
          if (key !== hoveredKeyRef.current) {
            hoveredKeyRef.current = key;
            const hoverMs = performance.now() - started;
            event.currentTarget.dataset.hoverMs = hoverMs.toFixed(3);
            hoverRef.current(
              hit ? cellMap.get(`${hit.row}:${hit.column}`) ?? null : null,
              hoverMs
            );
          }
          const drag = dragRef.current;
          if (drag?.pointerId === event.pointerId && hit) drag.endColumn = hit.column;
        }}
        onPointerUp={(event) => {
          const drag = dragRef.current;
          if (!drag || drag.pointerId !== event.pointerId) return;
          dragRef.current = null;
          if (drag.startColumn !== drag.endColumn && !drag.pin && !drag.anchor) {
            rangeRef.current(normalizeRange(drag.startColumn, drag.endColumn));
          } else {
            selectRef.current(drag.row, drag.endColumn, { pin: drag.pin, anchor: drag.anchor });
          }
        }}
        onPointerCancel={() => { dragRef.current = null; }}
        onPointerLeave={() => {
          hoveredKeyRef.current = null;
          hoverRef.current(null, 0);
        }}
      />
    </div>
  </>;
}

interface MatrixRowProps {
  row: number;
  columns: TokenInfo[];
  cellMap: Map<string, MatrixCellDatum>;
  rawBounds: [number, number];
  normalization: NormalizationMode;
  selectedRow: number;
  selectedColumn: number;
  comparisonCell: MatrixCellDatum | null;
  hoveredColumn: number | null;
  activeRange?: [number, number];
  onBrushStart: (column: number) => void;
  onHover: (cell: MatrixCellDatum | null) => void;
  onSelectCell: (row: number, column: number, event: React.MouseEvent) => void;
  onMoveFocus: (row: number, column: number, key: string) => void;
}

function MatrixRow({
  row,
  columns,
  cellMap,
  rawBounds,
  normalization,
  selectedRow,
  selectedColumn,
  comparisonCell,
  hoveredColumn,
  activeRange,
  onBrushStart,
  onHover,
  onSelectCell,
  onMoveFocus
}: MatrixRowProps) {
  return (
    <>
      <button
        className={`matrix-row-label ${selectedRow === row ? "selected" : ""}`}
        onClick={(event) => onSelectCell(row, selectedColumn, event)}
      >
        L{row}
      </button>
      {columns.map((token) => {
        const cell = cellMap.get(`${row}:${token.index}`);
        const available = cell !== undefined && cell.available !== false;
        const signal = cell
          ? normalization === "raw"
            ? normalizeRaw(cell.rawValue, rawBounds)
            : cell.value
          : 0;
        const selected = selectedRow === row && selectedColumn === token.index;
        const compared = comparisonCell?.row === row && comparisonCell.column === token.index;
        const rangeSelected = inRange(token.index, activeRange);
        return (
          <button
            key={`${row}:${token.index}`}
            data-column={token.index}
            className={[
              "matrix-cell",
              selected ? "selected" : "",
              compared ? "comparison" : "",
              hoveredColumn === token.index ? "column-hover" : "",
              rangeSelected ? "in-range" : "",
              available ? "" : "unavailable"
            ].join(" ")}
            data-row={row}
            aria-label={
              available
                ? `Layer ${row}, token ${token.index}, value ${formatValue(cell, normalization, "exact")}`
                : `Layer ${row}, token ${token.index}, unavailable`
            }
            aria-current={selected ? "true" : undefined}
            aria-pressed={selected || compared}
            tabIndex={selected ? 0 : -1}
            style={{ "--signal": signal } as React.CSSProperties}
            onClick={(event) => onSelectCell(row, token.index, event)}
            onKeyDown={(event) => {
              if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) {
                event.preventDefault();
                event.stopPropagation();
                onMoveFocus(row, token.index, event.key);
              }
            }}
            onPointerDown={(event) => {
              if (!event.shiftKey && !event.metaKey && !event.ctrlKey) {
                onBrushStart(token.index);
              }
            }}
            onPointerEnter={() => {
              if (cell) {
                onHover(cell);
              }
            }}
            onPointerLeave={() => onHover(null)}
            onFocus={() => {
              if (cell) onHover(cell);
            }}
            onBlur={() => onHover(null)}
          />
        );
      })}
    </>
  );
}

function MatrixTooltip({
  cell,
  token,
  normalization,
  provenance,
  comparisonCell
}: {
  cell: MatrixCellDatum | null;
  token?: TokenInfo;
  normalization: NormalizationMode;
  provenance: MetricProvenance;
  comparisonCell: MatrixCellDatum | null;
}) {
  if (!cell || !token) {
    return (
      <div className="matrix-tooltip matrix-tooltip-empty">
        Cell details · no matrix cell focused.
      </div>
    );
  }
  return (
    <div className="matrix-tooltip">
      <span><b>{token.text || "␠"}</b>token {token.index} · id {token.tokenId}</span>
      <span><b>L{cell.row}</b>{cell.metric}</span>
      <span><b>{formatMetricNumber(cell.rawValue, cell.metric, "exact")}</b>raw</span>
      <span><b>{formatMetricNumber(cell.value, "normalized", "exact")}</b>normalized</span>
      <span><b>{formatValue(cell, normalization, "exact")}</b>displayed</span>
      {comparisonCell && (
        <span>
          <b>{formatMetricDelta(cell.rawValue - comparisonCell.rawValue, cell.metric, "exact")}</b>
          raw delta vs L{comparisonCell.row}/T{comparisonCell.column}
        </span>
      )}
      <span className="tooltip-source"><b>{cell.sourceKey}</b>cache key</span>
      <span className="tooltip-source"><b>{provenance.kind.replace("_", " ")}</b>evidence class</span>
    </div>
  );
}

function normalizeRange(left: number, right: number): [number, number] {
  return left <= right ? [left, right] : [right, left];
}

function inRange(value: number, range?: [number, number]) {
  return range !== undefined && value >= range[0] && value <= range[1];
}

function normalizeRaw(value: number, bounds: [number, number]) {
  const [minimum, maximum] = bounds;
  if (Math.abs(maximum - minimum) < 1e-12) {
    return 0;
  }
  return Math.max(0, Math.min(1, (value - minimum) / (maximum - minimum)));
}

function clampInteger(value: number, minimum: number, maximum: number) {
  if (maximum < minimum) return minimum;
  return Math.max(minimum, Math.min(maximum, value));
}

function matrixAccent(color: MatrixHeatmapProps["color"]) {
  if (color === "attention") return "#23748a";
  if (color === "mlp") return "#3c7b55";
  if (color === "nla") return "#a46d16";
  if (color === "causal") return "#c25428";
  return "#b42335";
}

function mixHex(left: string, right: string, amount: number) {
  const parse = (value: string) => [
    Number.parseInt(value.slice(1, 3), 16),
    Number.parseInt(value.slice(3, 5), 16),
    Number.parseInt(value.slice(5, 7), 16)
  ];
  const leftRgb = parse(left);
  const rightRgb = parse(right);
  const mixed = leftRgb.map((value, index) =>
    Math.round(value + (rightRgb[index] - value) * amount)
  );
  return `rgb(${mixed[0]}, ${mixed[1]}, ${mixed[2]})`;
}

function formatValue(
  cell: MatrixCellDatum | undefined,
  normalization: NormalizationMode,
  mode: "compact" | "exact" = "compact"
) {
  if (!cell) {
    return "n/a";
  }
  return formatMetricNumber(
    normalization === "raw" ? cell.rawValue : cell.value,
    normalization === "raw" ? cell.metric : "normalized",
    mode
  );
}

function formatLegendValue(value: number, normalization: NormalizationMode, metric: string) {
  return formatMetricNumber(value, normalization === "raw" ? metric : "normalized", "compact");
}
