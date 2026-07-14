import { useEffect, useRef } from "react";
import { Crosshair, Hand, Maximize2, PanelLeft, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import {
  useMatrixViewportSession,
  type MatrixViewportKey
} from "../state/matrixViewportSession";

interface MatrixViewportOptions {
  initialSize: number;
  minimumSize: number;
  maximumSize: number;
  itemCount: number;
  labelWidth: number;
  gap?: number;
  sessionKey: MatrixViewportKey;
  managePan?: boolean;
}

export function useMatrixViewport({
  initialSize,
  minimumSize,
  maximumSize,
  itemCount,
  labelWidth,
  gap = 3,
  sessionKey,
  managePan = true
}: MatrixViewportOptions) {
  const session = useMatrixViewportSession(sessionKey, {
    size: initialSize,
    mode: "select",
    axesPinned: true,
    fitMode: "manual"
  });
  const { size, mode, axesPinned, fitMode } = session.snapshot;
  const scrollRef = useRef<HTMLDivElement>(null);
  const panRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    scrollLeft: number;
    scrollTop: number;
  } | null>(null);
  const didPanRef = useRef(false);

  useEffect(() => {
    if (!managePan) return;
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
  }, [managePan]);

  useEffect(() => {
    const viewport = scrollRef.current;
    if (!viewport || fitMode !== "fit") return;
    const fit = () => {
      const fitted = fittedSize(viewport.clientWidth, itemCount, labelWidth, gap);
      const nextSize = clamp(fitted, minimumSize, maximumSize);
      if (nextSize !== session.snapshot.size) {
        session.update({ ...session.snapshot, size: nextSize });
      }
    };
    const observer = new ResizeObserver(fit);
    observer.observe(viewport);
    fit();
    return () => observer.disconnect();
  }, [fitMode, gap, itemCount, labelWidth, maximumSize, minimumSize, session.snapshot]);

  function zoomBy(delta: number) {
    session.update({
      ...session.snapshot,
      size: clamp(size + delta, minimumSize, maximumSize),
      fitMode: "manual"
    });
  }

  function fitToWidth() {
    const available = scrollRef.current?.clientWidth ?? 0;
    const fitted = fittedSize(available, itemCount, labelWidth, gap);
    session.update({
      ...session.snapshot,
      size: clamp(fitted, minimumSize, maximumSize),
      fitMode: "fit"
    });
    if (scrollRef.current) scrollRef.current.scrollLeft = 0;
  }

  function reset() {
    session.update({
      ...session.snapshot,
      size: initialSize,
      mode: "select",
      fitMode: "manual"
    });
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = 0;
      scrollRef.current.scrollTop = 0;
    }
  }

  function setMode(next: React.SetStateAction<"select" | "pan">) {
    const value = typeof next === "function" ? next(mode) : next;
    session.update({ ...session.snapshot, mode: value });
  }

  function setAxesPinned(next: React.SetStateAction<boolean>) {
    const value = typeof next === "function" ? next(axesPinned) : next;
    session.update({ ...session.snapshot, axesPinned: value });
  }

  return {
    size,
    mode,
    axesPinned,
    fitMode,
    scrollRef,
    setMode,
    setAxesPinned,
    zoomBy,
    fitToWidth,
    reset,
    viewportProps: {
      onDoubleClick: reset,
      onWheel: (event: React.WheelEvent<HTMLDivElement>) => {
        if (!event.ctrlKey && !event.metaKey) return;
        event.preventDefault();
        zoomBy(event.deltaY < 0 ? 2 : -2);
      },
      onPointerDownCapture: (event: React.PointerEvent<HTMLDivElement>) => {
        if (!managePan || mode !== "pan") return;
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
      },
      onClickCapture: (event: React.MouseEvent<HTMLDivElement>) => {
        if (!didPanRef.current) return;
        event.preventDefault();
        event.stopPropagation();
      }
    }
  };
}

export type MatrixViewport = ReturnType<typeof useMatrixViewport>;

export function MatrixViewportControls({
  viewport,
  label
}: {
  viewport: MatrixViewport;
  label: string;
}) {
  return (
    <>
      <button
        className={viewport.mode === "select" ? "active" : ""}
        aria-label={`Select ${label} cells`}
        aria-pressed={viewport.mode === "select"}
        title="Select cells"
        onClick={() => viewport.setMode("select")}
      >
        <Crosshair size={14} />
      </button>
      <button
        className={viewport.mode === "pan" ? "active" : ""}
        aria-label={`Pan ${label}`}
        aria-pressed={viewport.mode === "pan"}
        title="Drag to pan"
        onClick={() => viewport.setMode("pan")}
      >
        <Hand size={14} />
      </button>
      <button aria-label={`Zoom out ${label}`} title="Zoom out" onClick={() => viewport.zoomBy(-2)}>
        <ZoomOut size={14} />
      </button>
      <button
        className={viewport.fitMode === "fit" ? "active" : ""}
        aria-label={`Fit ${label} to width`}
        aria-pressed={viewport.fitMode === "fit"}
        title="Fit to width"
        onClick={viewport.fitToWidth}
      >
        <Maximize2 size={14} />
      </button>
      <button
        className={viewport.axesPinned ? "active" : ""}
        aria-label={`Pin ${label} axes`}
        aria-pressed={viewport.axesPinned}
        title={viewport.axesPinned ? "Unpin row labels" : "Pin row labels"}
        onClick={() => viewport.setAxesPinned((current) => !current)}
      >
        <PanelLeft size={14} />
      </button>
      <button aria-label={`Zoom in ${label}`} title="Zoom in" onClick={() => viewport.zoomBy(2)}>
        <ZoomIn size={14} />
      </button>
      <button aria-label={`Reset ${label} view`} title="Reset view" onClick={viewport.reset}>
        <RotateCcw size={14} />
      </button>
    </>
  );
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.max(minimum, Math.min(maximum, value));
}

function fittedSize(available: number, itemCount: number, labelWidth: number, gap: number) {
  return Math.floor(
    (available - labelWidth - (itemCount + 1) * gap) / Math.max(1, itemCount)
  );
}
