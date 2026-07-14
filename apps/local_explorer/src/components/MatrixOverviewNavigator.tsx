import { useEffect, useId, useRef } from "react";

interface MatrixOverviewNavigatorProps {
  scrollRef: React.RefObject<HTMLDivElement | null>;
  rowCount: number;
  columnCount: number;
  totalWidth: number;
  totalHeight: number;
  selectedRow: number;
  selectedColumn: number;
  label: string;
  revision?: string | number;
  cellColor: (row: number, column: number) => string;
}

export function MatrixOverviewNavigator({
  scrollRef,
  rowCount,
  columnCount,
  totalWidth,
  totalHeight,
  selectedRow,
  selectedColumn,
  label,
  revision,
  cellColor
}: MatrixOverviewNavigatorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const colorRef = useRef(cellColor);
  const descriptionId = useId();
  colorRef.current = cellColor;

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
      const width = Math.max(1, canvas.clientWidth);
      const height = Math.max(1, canvas.clientHeight);
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      const context = canvas.getContext("2d", { alpha: false });
      if (!context) return;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.fillStyle = "#eef3f4";
      context.fillRect(0, 0, width, height);

      const sampledColumns = Math.max(1, Math.min(columnCount, 96));
      const sampledRows = Math.max(1, Math.min(rowCount, 28));
      const sampleWidth = width / sampledColumns;
      const sampleHeight = height / sampledRows;
      for (let row = 0; row < sampledRows; row += 1) {
        const sourceRow = Math.min(rowCount - 1, Math.floor((row / sampledRows) * rowCount));
        for (let column = 0; column < sampledColumns; column += 1) {
          const sourceColumn = Math.min(
            columnCount - 1,
            Math.floor((column / sampledColumns) * columnCount)
          );
          context.fillStyle = colorRef.current(sourceRow, sourceColumn);
          context.fillRect(column * sampleWidth, row * sampleHeight, sampleWidth + 0.5, sampleHeight + 0.5);
        }
      }

      const viewportX = (viewport.scrollLeft / Math.max(1, totalWidth)) * width;
      const viewportY = (viewport.scrollTop / Math.max(1, totalHeight)) * height;
      const viewportWidth = Math.min(width, (viewport.clientWidth / Math.max(1, totalWidth)) * width);
      const viewportHeight = Math.min(height, (viewport.clientHeight / Math.max(1, totalHeight)) * height);
      context.fillStyle = "rgba(255, 255, 255, 0.24)";
      context.fillRect(viewportX, viewportY, viewportWidth, viewportHeight);
      context.strokeStyle = "#102f38";
      context.lineWidth = 2;
      context.strokeRect(
        Math.max(1, viewportX + 1),
        Math.max(1, viewportY + 1),
        Math.max(2, viewportWidth - 2),
        Math.max(2, viewportHeight - 2)
      );

      const selectedX = ((selectedColumn + 0.5) / Math.max(1, columnCount)) * width;
      const selectedY = ((selectedRow + 0.5) / Math.max(1, rowCount)) * height;
      context.fillStyle = "#ffffff";
      context.strokeStyle = "#102f38";
      context.lineWidth = 1.5;
      context.beginPath();
      context.arc(selectedX, selectedY, 3, 0, Math.PI * 2);
      context.fill();
      context.stroke();

      canvas.dataset.viewportX = viewportX.toFixed(2);
      canvas.dataset.viewportY = viewportY.toFixed(2);
    }

    viewport.addEventListener("scroll", scheduleDraw, { passive: true });
    const observer = new ResizeObserver(scheduleDraw);
    observer.observe(viewport);
    observer.observe(canvas);
    scheduleDraw();
    return () => {
      window.cancelAnimationFrame(frame);
      viewport.removeEventListener("scroll", scheduleDraw);
      observer.disconnect();
    };
  }, [columnCount, revision, rowCount, scrollRef, selectedColumn, selectedRow, totalHeight, totalWidth]);

  function navigate(clientX: number, clientY: number, target: HTMLElement) {
    const viewport = scrollRef.current;
    if (!viewport) return;
    const bounds = target.getBoundingClientRect();
    const x = clamp((clientX - bounds.left) / Math.max(1, bounds.width), 0, 1);
    const y = clamp((clientY - bounds.top) / Math.max(1, bounds.height), 0, 1);
    viewport.scrollTo({
      left: x * totalWidth - viewport.clientWidth / 2,
      top: y * totalHeight - viewport.clientHeight / 2,
      behavior: "auto"
    });
  }

  return (
    <div className="matrix-overview-sticky">
      <button
        className="matrix-overview-navigator"
        aria-label={`Navigate ${label} overview`}
        aria-describedby={descriptionId}
        aria-keyshortcuts="ArrowLeft ArrowRight ArrowUp ArrowDown Home End"
        title="Navigate matrix overview"
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture(event.pointerId);
          navigate(event.clientX, event.clientY, event.currentTarget);
        }}
        onPointerMove={(event) => {
          if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
          navigate(event.clientX, event.clientY, event.currentTarget);
        }}
        onKeyDown={(event) => {
          const viewport = scrollRef.current;
          if (!viewport) return;
          if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
          event.preventDefault();
          event.stopPropagation();
          if (event.key === "Home") viewport.scrollTo({ left: 0, top: 0 });
          else if (event.key === "End") viewport.scrollTo({ left: totalWidth, top: totalHeight });
          else viewport.scrollBy({
            left: event.key === "ArrowLeft" ? -viewport.clientWidth * 0.75 : event.key === "ArrowRight" ? viewport.clientWidth * 0.75 : 0,
            top: event.key === "ArrowUp" ? -viewport.clientHeight * 0.75 : event.key === "ArrowDown" ? viewport.clientHeight * 0.75 : 0
          });
        }}
      >
        <canvas ref={canvasRef} aria-hidden="true" />
      </button>
      <span id={descriptionId} className="visually-hidden">
        Low-resolution matrix overview. Click or drag to move the viewport; use arrow keys for incremental navigation.
      </span>
    </div>
  );
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.max(minimum, Math.min(maximum, value));
}
