import { useEffect, useRef } from "react";

export interface ExplorerPerformanceEvent {
  name: string;
  at: number;
  [key: string]: number | string | boolean | undefined;
}

const MAX_EVENTS = 100;
const events: ExplorerPerformanceEvent[] = [];

declare global {
  interface Window {
    __SAFELENS_PERFORMANCE__?: readonly ExplorerPerformanceEvent[];
  }
}

if (typeof window !== "undefined") {
  window.__SAFELENS_PERFORMANCE__ = events;
}

/**
 * Keep performance diagnostics in the browser's Performance timeline and in a
 * small in-memory buffer so local runs can inspect them without a telemetry
 * backend or network request.
 */
export function recordExplorerPerformance(
  name: string,
  detail: Record<string, number | string | boolean | undefined> = {}
) {
  const event: ExplorerPerformanceEvent = { name, at: performance.now(), ...detail };
  events.push(event);
  if (events.length > MAX_EVENTS) events.splice(0, events.length - MAX_EVENTS);
  const markName = `safelens:${name}`;
  performance.clearMarks(markName);
  performance.mark(markName, { detail: event });
  window.dispatchEvent(new CustomEvent("safelens:performance", { detail: event }));
}

export function explorerPerformanceEvents() {
  return events.slice();
}

export function useExplorerPerformance({
  rootRef,
  view,
  ready
}: {
  rootRef: React.RefObject<HTMLElement | null>;
  view: string;
  ready: boolean;
}) {
  const firstUsableRecorded = useRef(false);

  useEffect(() => {
    if (!ready || !rootRef.current) return;
    const root = rootRef.current;
    let settled = false;
    let frame = 0;

    const recordWhenPainted = () => {
      if (settled || root.querySelector(".view-module-loading")) return;
      settled = true;
      frame = window.requestAnimationFrame(() => {
        recordExplorerPerformance("view-ready", { view });
        if (!firstUsableRecorded.current) {
          firstUsableRecorded.current = true;
          recordExplorerPerformance("first-usable", { view });
        }
      });
    };

    const observer = new MutationObserver(recordWhenPainted);
    observer.observe(root, { childList: true, subtree: true });
    recordWhenPainted();
    return () => {
      settled = true;
      window.cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [ready, rootRef, view]);
}
