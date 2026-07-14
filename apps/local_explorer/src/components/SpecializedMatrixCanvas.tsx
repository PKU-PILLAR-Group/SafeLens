import { useEffect, useId, useRef, useState } from "react";
import { recordExplorerPerformance } from "../state/useExplorerPerformance";
import { MatrixOverviewNavigator } from "./MatrixOverviewNavigator";

export const SPECIALIZED_CANVAS_CELL_THRESHOLD = 2_500;

export interface SpecializedCanvasCell {
  fill: string;
  hatch?: string;
  disabled?: boolean;
  label: string;
}

interface MatrixPosition {
  row: number;
  column: number;
}

export interface MatrixInteractionModifiers {
  anchor: boolean;
  pin: boolean;
}

interface SpecializedMatrixCanvasProps {
  scrollRef: React.RefObject<HTMLDivElement | null>;
  rowCount: number;
  columnCount: number;
  rowHeight: number;
  columnWidth: number;
  rowLabelWidth: number;
  gap?: number;
  axesPinned: boolean;
  selectedRow: number;
  selectedColumn: number;
  comparisonRow?: number;
  comparisonColumn?: number;
  rangeAxis?: "row" | "column";
  selectedRange?: [number, number];
  rangeEnabled?: boolean;
  ariaLabel: string;
  selectedDescription: string;
  overviewRevision?: string | number;
  showOverview?: boolean;
  cornerLabel: string;
  rowLabel: (row: number) => string;
  columnLabel: (column: number) => string;
  cell: (row: number, column: number) => SpecializedCanvasCell;
  navigate?: (position: MatrixPosition, key: string) => MatrixPosition;
  onSelect: (row: number, column: number, modifiers: MatrixInteractionModifiers) => void;
  onRangeSelect?: (range?: [number, number]) => void;
  onPin?: () => void;
  onHover: (row: number, column: number, latency: number) => void;
  onHoverEnd: () => void;
}

export function SpecializedMatrixCanvas({
  scrollRef,
  rowCount,
  columnCount,
  rowHeight,
  columnWidth,
  rowLabelWidth,
  gap = 3,
  axesPinned,
  selectedRow,
  selectedColumn,
  comparisonRow = -1,
  comparisonColumn = -1,
  rangeAxis,
  selectedRange,
  rangeEnabled = false,
  ariaLabel,
  selectedDescription,
  overviewRevision,
  showOverview = true,
  cornerLabel,
  rowLabel,
  columnLabel,
  cell,
  navigate,
  onSelect,
  onRangeSelect,
  onPin,
  onHover,
  onHoverEnd
}: SpecializedMatrixCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const descriptionId = useId();
  const cellRef = useRef(cell);
  const selectRef = useRef(onSelect);
  const pinRef = useRef(onPin);
  const hoverRef = useRef(onHover);
  const hoverEndRef = useRef(onHoverEnd);
  const rangeSelectRef = useRef(onRangeSelect);
  const hoveredRef = useRef<string | null>(null);
  const rangeDragRef = useRef<{
    pointerId: number;
    start: number;
    current: number;
    hit: MatrixPosition;
  } | null>(null);
  const [previewRange, setPreviewRange] = useState<[number, number] | undefined>();
  const activeRange = previewRange ?? selectedRange;
  cellRef.current = cell;
  selectRef.current = onSelect;
  pinRef.current = onPin;
  hoverRef.current = onHover;
  hoverEndRef.current = onHoverEnd;
  rangeSelectRef.current = onRangeSelect;

  const rowStride = rowHeight + gap;
  const columnStride = columnWidth + gap;
  const totalWidth = rowLabelWidth + columnCount * columnStride + gap;
  const totalHeight = rowHeight + rowCount * rowStride + gap;

  useEffect(() => {
    const viewport = scrollRef.current;
    const canvas = canvasRef.current;
    if (!viewport || !canvas) return;
    let frame = 0;

    function scheduleDraw() {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(draw);
    }

    function draw() {
      if (!viewport || !canvas) return;
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
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, width, height);

      const firstColumn = clamp(
        Math.floor((viewport.scrollLeft - rowLabelWidth) / columnStride) - 1,
        0,
        Math.max(0, columnCount - 1)
      );
      const lastColumn = clamp(
        Math.ceil((viewport.scrollLeft + width - rowLabelWidth) / columnStride) + 1,
        0,
        Math.max(0, columnCount - 1)
      );
      const firstRow = clamp(
        Math.floor((viewport.scrollTop - rowHeight) / rowStride) - 1,
        0,
        Math.max(0, rowCount - 1)
      );
      const lastRow = clamp(
        Math.ceil((viewport.scrollTop + height - rowHeight) / rowStride) + 1,
        0,
        Math.max(0, rowCount - 1)
      );
      let visibleCells = 0;

      context.font = "10px Inter, sans-serif";
      context.textBaseline = "middle";
      for (let row = firstRow; row <= lastRow; row += 1) {
        const y = rowHeight + row * rowStride - viewport.scrollTop;
        const labelX = axesPinned ? 0 : -viewport.scrollLeft;
        const rowInRange = rangeAxis === "row" && isInRange(row, activeRange);
        context.fillStyle = row === selectedRow ? "#dcefeb" : rowInRange ? "#fff1cf" : "#eef3f3";
        context.fillRect(labelX, y, rowLabelWidth, rowHeight);
        context.fillStyle = row === selectedRow ? "#155f59" : "#465d65";
        context.textAlign = "center";
        context.fillText(rowLabel(row), labelX + rowLabelWidth / 2, y + rowHeight / 2);

        for (let column = firstColumn; column <= lastColumn; column += 1) {
          const x = rowLabelWidth + column * columnStride - viewport.scrollLeft;
          const datum = cellRef.current(row, column);
          context.fillStyle = datum.fill;
          context.fillRect(x, y, columnWidth, rowHeight);
          visibleCells += 1;
          if (datum.hatch) drawHatch(context, x, y, columnWidth, rowHeight, datum.hatch);
          if (
            (rangeAxis === "row" && isInRange(row, activeRange)) ||
            (rangeAxis === "column" && isInRange(column, activeRange))
          ) {
            context.fillStyle = "rgba(197, 139, 34, 0.14)";
            context.fillRect(x, y, columnWidth, rowHeight);
            context.fillStyle = "#c58b22";
            context.fillRect(x, y + rowHeight - 3, columnWidth, 3);
          }
          if (row === selectedRow && column === selectedColumn) {
            context.strokeStyle = "#193f48";
            context.lineWidth = 2;
            context.strokeRect(x + 1, y + 1, columnWidth - 2, rowHeight - 2);
          }
          if (
            row === comparisonRow &&
            column === comparisonColumn &&
            (row !== selectedRow || column !== selectedColumn)
          ) {
            context.save();
            context.strokeStyle = "#9a6818";
            context.lineWidth = 2;
            context.setLineDash([4, 3]);
            context.strokeRect(x + 2, y + 2, columnWidth - 4, rowHeight - 4);
            context.restore();
          }
        }
      }

      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, width, rowHeight);
      context.font = "10px Inter, sans-serif";
      context.textAlign = "center";
      context.textBaseline = "middle";
      for (let column = firstColumn; column <= lastColumn; column += 1) {
        const x = rowLabelWidth + column * columnStride - viewport.scrollLeft;
        const columnInRange = rangeAxis === "column" && isInRange(column, activeRange);
        if (column === selectedColumn || columnInRange) {
          context.fillStyle = column === selectedColumn ? "#e1f1ee" : "#fff1cf";
          context.fillRect(x, 0, columnWidth, rowHeight);
        }
        context.fillStyle = column === selectedColumn ? "#155f59" : "#687681";
        context.fillText(columnLabel(column), x + columnWidth / 2, rowHeight / 2);
      }
      context.strokeStyle = "rgba(30, 49, 58, 0.16)";
      context.beginPath();
      context.moveTo(0, rowHeight - 0.5);
      context.lineTo(width, rowHeight - 0.5);
      context.stroke();

      if (axesPinned) {
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, rowLabelWidth, Math.min(rowHeight, height));
        context.fillStyle = "#49646c";
        context.textAlign = "center";
        context.fillText(cornerLabel, rowLabelWidth / 2, Math.min(rowHeight, height) / 2);
        context.strokeStyle = "rgba(30, 49, 58, 0.12)";
        context.beginPath();
        context.moveTo(rowLabelWidth - 0.5, 0);
        context.lineTo(rowLabelWidth - 0.5, height);
        context.stroke();
      }
      canvas.dataset.visibleCells = String(visibleCells);
      canvas.dataset.drawMs = (performance.now() - started).toFixed(3);
      canvas.dataset.columnHeaderSticky = "true";
      canvas.dataset.selectedRange = activeRange ? `${activeRange[0]}-${activeRange[1]}` : "";
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
  }, [activeRange, axesPinned, columnCount, columnLabel, columnStride, columnWidth, comparisonColumn, comparisonRow, cornerLabel, rangeAxis, rowCount, rowHeight, rowLabel, rowLabelWidth, rowStride, scrollRef, selectedColumn, selectedRow]);

  useEffect(() => {
    const viewport = scrollRef.current;
    if (!viewport || selectedRow < 0 || selectedColumn < 0) return;
    const x = rowLabelWidth + selectedColumn * columnStride;
    const y = rowHeight + selectedRow * rowStride;
    if (x < viewport.scrollLeft + rowLabelWidth) viewport.scrollLeft = Math.max(0, x - rowLabelWidth);
    else if (x + columnWidth > viewport.scrollLeft + viewport.clientWidth) {
      viewport.scrollLeft = x + columnWidth - viewport.clientWidth;
    }
    if (y < viewport.scrollTop + rowHeight) viewport.scrollTop = Math.max(0, y - rowHeight);
    else if (y + rowHeight > viewport.scrollTop + viewport.clientHeight) {
      viewport.scrollTop = y + rowHeight - viewport.clientHeight;
    }
  }, [columnStride, columnWidth, rowHeight, rowLabelWidth, rowStride, scrollRef, selectedColumn, selectedRow]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || document.activeElement !== canvas) return;
    hoverRef.current(selectedRow, selectedColumn, 0);
  }, [selectedColumn, selectedRow]);

  function hitCell(event: React.PointerEvent<HTMLCanvasElement>) {
    const viewport = scrollRef.current;
    if (!viewport) return null;
    const rect = event.currentTarget.getBoundingClientRect();
    if (event.clientY - rect.top < rowHeight) return null;
    const x = event.clientX - rect.left + viewport.scrollLeft - rowLabelWidth;
    const y = event.clientY - rect.top + viewport.scrollTop - rowHeight;
    const column = Math.floor(x / columnStride);
    const row = Math.floor(y / rowStride);
    if (row < 0 || column < 0 || row >= rowCount || column >= columnCount) return null;
    if (x % columnStride >= columnWidth || y % rowStride >= rowHeight) return null;
    return { row, column };
  }

  function moveSelection(key: string) {
    const current = {
      row: clamp(selectedRow, 0, Math.max(0, rowCount - 1)),
      column: clamp(selectedColumn, 0, Math.max(0, columnCount - 1))
    };
    const next = navigate ? navigate(current, key) : defaultNavigation(current, key, rowCount, columnCount);
    selectRef.current(
      clamp(next.row, 0, Math.max(0, rowCount - 1)),
      clamp(next.column, 0, Math.max(0, columnCount - 1)),
      { anchor: false, pin: false }
    );
  }

  return <>
    {showOverview && (
      <MatrixOverviewNavigator
        scrollRef={scrollRef}
        rowCount={rowCount}
        columnCount={columnCount}
        totalWidth={totalWidth}
        totalHeight={totalHeight}
        selectedRow={selectedRow}
        selectedColumn={selectedColumn}
        label={ariaLabel}
        revision={overviewRevision}
        cellColor={(row, column) => cellRef.current(row, column).fill}
      />
    )}
    <div
      className="specialized-matrix-canvas-spacer"
      style={{ width: `${totalWidth}px`, height: `${totalHeight}px` }}
    >
      <div id={descriptionId} className="visually-hidden" aria-live="polite">{selectedDescription}</div>
      <canvas
        ref={canvasRef}
        className="specialized-matrix-canvas"
        role="grid"
        tabIndex={0}
        aria-label={ariaLabel}
        aria-rowcount={rowCount}
        aria-colcount={columnCount}
        aria-describedby={descriptionId}
        aria-keyshortcuts={onPin
          ? "ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter Space"
          : "ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter"}
        data-render-mode="canvas"
        data-comparison-cell={comparisonRow >= 0 && comparisonColumn >= 0
          ? `${comparisonRow}:${comparisonColumn}`
          : undefined}
        onKeyDown={(event) => {
          if (event.key === "Enter" && event.shiftKey) {
            event.preventDefault();
            event.stopPropagation();
            selectRef.current(selectedRow, selectedColumn, { anchor: true, pin: false });
            return;
          }
          if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            event.preventDefault();
            event.stopPropagation();
            selectRef.current(selectedRow, selectedColumn, { anchor: false, pin: true });
            return;
          }
          if (event.key === "Enter") {
            event.preventDefault();
            event.stopPropagation();
            selectRef.current(selectedRow, selectedColumn, { anchor: false, pin: false });
            return;
          }
          if (event.key === " " && pinRef.current) {
            event.preventDefault();
            event.stopPropagation();
            pinRef.current();
            return;
          }
          if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
          event.preventDefault();
          event.stopPropagation();
          moveSelection(event.key);
        }}
        onPointerDown={(event) => {
          const hit = hitCell(event);
          if (!hit || cellRef.current(hit.row, hit.column).disabled) return;
          event.currentTarget.focus();
          const modified = event.shiftKey || event.metaKey || event.ctrlKey;
          if (
            rangeEnabled &&
            rangeAxis &&
            rangeSelectRef.current &&
            event.button === 0 &&
            event.pointerType !== "touch" &&
            !modified
          ) {
            const position = rangeAxis === "row" ? hit.row : hit.column;
            rangeDragRef.current = {
              pointerId: event.pointerId,
              start: position,
              current: position,
              hit
            };
            event.currentTarget.setPointerCapture(event.pointerId);
            return;
          }
          selectRef.current(hit.row, hit.column, {
            anchor: event.shiftKey,
            pin: event.metaKey || event.ctrlKey
          });
        }}
        onPointerMove={(event) => {
          const drag = rangeDragRef.current;
          if (drag && drag.pointerId === event.pointerId && rangeAxis) {
            const dragHit = hitCell(event);
            if (dragHit) {
              drag.current = rangeAxis === "row" ? dragHit.row : dragHit.column;
              if (drag.current !== drag.start) {
                event.preventDefault();
                setPreviewRange(normalizeRange(drag.start, drag.current));
              }
            }
          }
          const started = performance.now();
          const hit = hitCell(event);
          const key = hit ? `${hit.row}:${hit.column}` : null;
          if (key === hoveredRef.current) return;
          hoveredRef.current = key;
          const hoverMs = performance.now() - started;
          event.currentTarget.dataset.hoverMs = hoverMs.toFixed(3);
          if (hit) {
            recordExplorerPerformance("matrix-hover", {
              latencyMs: hoverMs,
              renderMode: "canvas",
              row: hit.row,
              column: hit.column
            });
            hoverRef.current(hit.row, hit.column, hoverMs);
          }
          else hoverEndRef.current();
        }}
        onPointerUp={(event) => {
          const drag = rangeDragRef.current;
          if (!drag || drag.pointerId !== event.pointerId) return;
          if (event.currentTarget.hasPointerCapture(event.pointerId)) {
            event.currentTarget.releasePointerCapture(event.pointerId);
          }
          rangeDragRef.current = null;
          setPreviewRange(undefined);
          if (drag.current !== drag.start) {
            rangeSelectRef.current?.(normalizeRange(drag.start, drag.current));
          } else {
            selectRef.current(drag.hit.row, drag.hit.column, { anchor: false, pin: false });
          }
        }}
        onPointerCancel={(event) => {
          const drag = rangeDragRef.current;
          if (!drag || drag.pointerId !== event.pointerId) return;
          rangeDragRef.current = null;
          setPreviewRange(undefined);
        }}
        onPointerLeave={() => {
          hoveredRef.current = null;
          hoverEndRef.current();
        }}
        onFocus={() => hoverRef.current(selectedRow, selectedColumn, 0)}
        onBlur={() => hoverEndRef.current()}
      />
    </div>
  </>;
}

function defaultNavigation(position: MatrixPosition, key: string, rows: number, columns: number) {
  let { row, column } = position;
  if (key === "ArrowLeft") column -= 1;
  if (key === "ArrowRight") column += 1;
  if (key === "ArrowUp") row -= 1;
  if (key === "ArrowDown") row += 1;
  if (key === "Home") column = 0;
  if (key === "End") column = columns - 1;
  return { row: clamp(row, 0, rows - 1), column: clamp(column, 0, columns - 1) };
}

function drawHatch(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  color: string
) {
  context.save();
  context.beginPath();
  context.rect(x, y, width, height);
  context.clip();
  context.strokeStyle = color;
  context.lineWidth = 1;
  for (let offset = -height; offset < width; offset += 6) {
    context.beginPath();
    context.moveTo(x + offset, y + height);
    context.lineTo(x + offset + height, y);
    context.stroke();
  }
  context.restore();
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.max(minimum, Math.min(maximum, value));
}

function normalizeRange(left: number, right: number): [number, number] {
  return left <= right ? [left, right] : [right, left];
}

function isInRange(value: number, range?: [number, number]) {
  return Boolean(range && value >= range[0] && value <= range[1]);
}
