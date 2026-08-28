import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  ChevronLeft,
  ChevronRight,
  MessageSquareText,
  Search,
  WholeWord,
  X
} from "lucide-react";

import type { ExplorerRun, TokenInfo } from "../types";
import { formatMetricNumber } from "../metricFormatting";
import { recordExplorerPerformance } from "../state/useExplorerPerformance";

export type TimelineMode = "token" | "word";
export type TimelineMetric = "risk" | "attribution" | "residual" | "nla" | "probe";
export interface TimelineState {
  mode: TimelineMode;
  metric: TimelineMetric;
  query: string;
}
type Marker = "risk" | "attribution" | "nla" | "probe" | "monitor" | "pinned";
interface MarkerIndex {
  nla: ReadonlySet<number>;
  pinned: ReadonlySet<number>;
}

interface TimelineItem {
  key: string;
  tokens: TokenInfo[];
  text: string;
  source: TokenInfo["source"];
  start: number;
  end: number;
  generationStart?: number;
  generationEnd?: number;
  isSpecial: boolean;
  normalizedText: string;
}

interface TokenTimelineProps {
  run: ExplorerRun;
  selectedToken: number;
  selectedLayer: number;
  selectedRange?: [number, number];
  setSelectedToken: (index: number) => void;
  setSelectedRange: (range?: [number, number]) => void;
  hoveredToken: number | null;
  setHoveredToken: (index: number | null) => void;
  pulseToken: number | null;
  pinToken: (index: number) => void;
  pinned: number[];
  timeline: TimelineState;
  onTimelineChange: (timeline: TimelineState) => void;
}

const DESKTOP_RENDER_WINDOW = 180;
const MOBILE_RENDER_WINDOW = 60;

export function TokenTimeline({
  run,
  selectedToken,
  selectedLayer,
  selectedRange,
  setSelectedToken,
  setSelectedRange,
  hoveredToken,
  setHoveredToken,
  pulseToken,
  pinToken,
  pinned,
  timeline,
  onTimelineChange
}: TokenTimelineProps) {
  const [renderWindowSize, setRenderWindowSize] = useState(() =>
    window.matchMedia("(max-width: 760px)").matches
      ? MOBILE_RENDER_WINDOW
      : DESKTOP_RENDER_WINDOW
  );
  const { mode, metric, query } = timeline;
  const rootRef = useRef<HTMLElement>(null);
  const pendingFocusRef = useRef<{
    start: number;
    onFocused?: () => void;
  } | null>(null);
  const items = useMemo(() => timelineItems(run.tokens, mode), [mode, run.tokens]);
  const tokenMetrics = useMemo(
    () => buildTokenMetrics(run, selectedLayer, metric),
    [metric, run, selectedLayer]
  );
  const selectedItemIndex = Math.max(
    0,
    items.findIndex((item) => item.tokens.some((token) => token.index === selectedToken))
  );
  const windowStart = items.length <= renderWindowSize
    ? 0
    : clamp(
        selectedItemIndex - Math.floor(renderWindowSize / 2),
        0,
        items.length - renderWindowSize
      );
  const visibleItems = items.slice(windowStart, windowStart + renderWindowSize);
  const normalizedQuery = query.trim().toLowerCase();
  const matchingItems = useMemo(
    () => normalizedQuery.length === 0
      ? []
      : items.filter((item) => itemMatches(item, normalizedQuery)),
    [items, normalizedQuery]
  );
  const currentMatch = matchingItems.findIndex((item) =>
    item.tokens.some((token) => token.index === selectedToken)
  );
  const availableMetrics: Array<{ id: TimelineMetric; label: string }> = [
    { id: "risk", label: "Safety proxy" },
    { id: "attribution", label: "Attribution" },
    { id: "residual", label: "Residual norm" },
    { id: "nla", label: "NLA fidelity" },
    ...(run.tokens.some((token) => token.probeScore !== undefined)
      ? [{ id: "probe" as const, label: "Probe score" }]
      : [])
  ];
  const markerIndex = useMemo(() => buildMarkerIndex(run, pinned), [pinned, run]);
  const markerSet = new Set(
    items.flatMap((item) => markersForItem(item, markerIndex))
  );
  const groups = groupBySource(visibleItems);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      recordExplorerPerformance("timeline-ready", {
        tokens: run.tokens.length,
        items: items.length,
        renderedItems: visibleItems.length,
        mode
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [items.length, mode, run.tokens.length, visibleItems.length]);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)");
    const update = () => setRenderWindowSize(
      media.matches ? MOBILE_RENDER_WINDOW : DESKTOP_RENDER_WINDOW
    );
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useLayoutEffect(() => {
    const pending = pendingFocusRef.current;
    if (!pending) return;
    const target = rootRef.current
      ?.querySelector<HTMLButtonElement>(`[data-timeline-start="${pending.start}"]`);
    if (!target) return;
    target.focus();
    pendingFocusRef.current = null;
    pending.onFocused?.();
  }, [selectedToken, windowStart]);

  function focusItem(item: TimelineItem, onFocused?: () => void) {
    const target = item.tokens.some((token) => token.index === selectedToken)
      ? selectedToken
      : item.tokens[0]?.index;
    if (target === undefined) return;
    pendingFocusRef.current = { start: item.start, onFocused };
    setSelectedToken(target);
    if (target === selectedToken) {
      const visibleTarget = rootRef.current
        ?.querySelector<HTMLButtonElement>(`[data-timeline-start="${item.start}"]`);
      if (visibleTarget) {
        visibleTarget.focus();
        pendingFocusRef.current = null;
        onFocused?.();
      }
    }
  }

  function moveSearch(direction: -1 | 1) {
    if (matchingItems.length === 0) return;
    const base = currentMatch >= 0 ? currentMatch : direction > 0 ? -1 : 0;
    const next = (base + direction + matchingItems.length) % matchingItems.length;
    const started = performance.now();
    const target = matchingItems[next];
    focusItem(target, () => {
      recordExplorerPerformance("timeline-search-jump", {
        durationMs: performance.now() - started,
        token: target.start,
        tokens: run.tokens.length
      });
    });
  }

  function moveItem(item: TimelineItem, direction: -1 | 1) {
    const index = items.findIndex((candidate) => candidate.key === item.key);
    const next = items[clamp(index + direction, 0, items.length - 1)];
    if (next) focusItem(next);
  }

  return (
    <section ref={rootRef} className="token-timeline-shell" aria-label="Token timeline">
      <div className={`token-timeline-toolbar${normalizedQuery ? " has-query" : ""}`}>
        <label className="timeline-search">
          <span>
            <Search size={12} /> Search
            {normalizedQuery && (
              <em className="timeline-search-match-count">
                {matchingItems.length} {matchingItems.length === 1 ? "match" : "matches"}
              </em>
            )}
          </span>
          <div>
            <input
              id="token-timeline-search"
              value={query}
              placeholder="text, position, or token id"
              aria-label="Search tokens"
              onChange={(event) => onTimelineChange({ ...timeline, query: event.target.value })}
            />
            {query && (
              <button aria-label="Clear token search" onClick={() => onTimelineChange({ ...timeline, query: "" })}>
                <X size={13} />
              </button>
            )}
          </div>
        </label>
        <div className="toolbar-segment" aria-label="Timeline granularity">
          <button className={mode === "token" ? "active" : ""} onClick={() => onTimelineChange({ ...timeline, mode: "token" })}>
            Token
          </button>
          <button className={mode === "word" ? "active" : ""} onClick={() => onTimelineChange({ ...timeline, mode: "word" })}>
            <WholeWord size={13} /> Word
          </button>
        </div>
        <label className="timeline-metric">
          <span>Color</span>
          <select
            aria-label="Token color metric"
            value={metric}
            onChange={(event) => onTimelineChange({
              ...timeline,
              metric: event.target.value as TimelineMetric
            })}
          >
            {availableMetrics.map((option) => (
              <option key={option.id} value={option.id}>{option.label}</option>
            ))}
          </select>
        </label>
        <div className="timeline-search-status" aria-label="Token search results">
          <span>{normalizedQuery ? `${matchingItems.length} matches` : `${items.length} ${mode}s`}</span>
          <button aria-label="Previous token search result" disabled={!matchingItems.length} onClick={() => moveSearch(-1)}>
            <ChevronLeft size={14} />
          </button>
          <button aria-label="Next token search result" disabled={!matchingItems.length} onClick={() => moveSearch(1)}>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {markerSet.size > 0 && (
        <div className="timeline-marker-legend" aria-label="Token evidence markers">
          {markerOrder.filter((marker) => markerSet.has(marker)).map((marker) => (
            <span key={marker}>
              <i
                className={`token-marker marker-${marker}`}
                data-marker={marker}
                data-shape={markerShape(marker)}
                aria-hidden="true"
              />
              {markerLabel(marker)}
            </span>
          ))}
        </div>
      )}

      {items.length > renderWindowSize && (
        <div className="timeline-window-status" aria-label="Timeline render window">
          <button
            aria-label="Previous token window"
            disabled={windowStart === 0}
            onClick={() => focusItem(items[Math.max(0, windowStart - renderWindowSize)])}
          >
            <ChevronLeft size={14} />
          </button>
          <span>{windowStart + 1}–{windowStart + visibleItems.length} / {items.length}</span>
          <button
            aria-label="Next token window"
            disabled={windowStart + visibleItems.length >= items.length}
            onClick={() => focusItem(items[Math.min(items.length - 1, windowStart + renderWindowSize)])}
          >
            <ChevronRight size={14} />
          </button>
        </div>
      )}

      <div className="timeline-groups">
        {groups.map((group) => (
          <section key={group.source} className={`timeline-source-group source-${group.source}`}>
            <header>
              <div className="timeline-source-identity">
                <span className="timeline-source-icon" aria-hidden="true">
                  {group.source === "prompt" ? <MessageSquareText size={14} /> : <Bot size={14} />}
                </span>
                <div>
                  <strong>{group.source === "prompt" ? "User prompt" : "Assistant reply"}</strong>
                  <span>{group.source === "prompt" ? "Input context" : "Generated continuation"}</span>
                </div>
              </div>
              <SourceSummary tokens={run.tokens} source={group.source} />
            </header>
            <div className="token-timeline" aria-label={`${group.source} tokens`}>
              {group.items.map((item) => {
                const primary = item.tokens.find((token) => token.index === selectedToken) ?? item.tokens[0];
                const aggregate = aggregateMetric(item, tokenMetrics);
                const itemMarkers = markersForItem(item, markerIndex);
                const selected = item.tokens.some((token) => token.index === selectedToken);
                const hovered = item.tokens.some((token) => token.index === hoveredToken);
                const pulsed = item.tokens.some((token) => token.index === pulseToken);
                const inRange = selectedRange !== undefined &&
                  item.end >= selectedRange[0] && item.start <= selectedRange[1];
                const searchMatch = normalizedQuery.length > 0 && itemMatches(item, normalizedQuery);
                return (
                  <button
                    key={item.key}
                    data-timeline-start={item.start}
                    className={[
                      "token-pill",
                      `metric-${metric}`,
                      selected ? "selected" : "",
                      hovered ? "hovered" : "",
                      pulsed ? "pulse" : "",
                      inRange ? "in-range" : "",
                      searchMatch ? "search-match" : "",
                      itemMarkers.includes("pinned") ? "pinned" : "",
                      item.isSpecial ? "special" : "",
                      aggregate.value === undefined ? "metric-unavailable" : ""
                    ].join(" ")}
                    aria-label={timelineItemLabel(item, aggregate.value, metric, itemMarkers)}
                    aria-keyshortcuts="ArrowLeft ArrowRight Space Control+Enter Meta+Enter"
                    aria-current={selected ? "true" : undefined}
                    tabIndex={selected ? 0 : -1}
                    style={{ "--signal": aggregate.signal } as React.CSSProperties}
                    onClick={(event) => {
                      if (event.metaKey || event.ctrlKey) {
                        pinToken(primary.index);
                        return;
                      }
                      if (event.shiftKey) {
                        setSelectedRange(normalizeRange(selectedToken, item.end));
                        return;
                      }
                      setSelectedToken(primary.index);
                    }}
                    onDoubleClick={() => pinToken(primary.index)}
                    onKeyDown={(event) => {
                      if (event.key === " ") {
                        event.preventDefault();
                        event.stopPropagation();
                        pinToken(primary.index);
                        return;
                      }
                      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
                      event.preventDefault();
                      event.stopPropagation();
                      moveItem(item, event.key === "ArrowLeft" ? -1 : 1);
                    }}
                    onMouseEnter={() => {
                      const started = performance.now();
                      setHoveredToken(primary.index);
                      window.requestAnimationFrame(() => {
                        recordExplorerPerformance("timeline-hover", {
                          durationMs: performance.now() - started,
                          token: primary.index,
                          tokens: run.tokens.length
                        });
                      });
                    }}
                    onMouseLeave={() => setHoveredToken(null)}
                    onFocus={() => setHoveredToken(primary.index)}
                    onBlur={() => setHoveredToken(null)}
                  >
                    <span className="token-pill-content">
                      <b>{item.text || "␠"}</b>
                      {mode === "word" && item.tokens.length > 1 && <em>{item.tokens.length} tokens</em>}
                    </span>
                    {(item.isSpecial || item.generationStart !== undefined) && (
                      <span className="token-role-badges" aria-hidden="true">
                        {item.isSpecial && <span className="token-role-badge special-badge" title="Special token">Special</span>}
                        {item.generationStart !== undefined && (
                          <span className="token-role-badge generation-badge" title={generationDescription(item)}>
                            {generationBadge(item)}
                          </span>
                        )}
                      </span>
                    )}
                    <i className="token-value">
                      {aggregate.value === undefined ? "n/a" : formatMetricValue(aggregate.value, metric)}
                    </i>
                    {itemMarkers.length > 0 && (
                      <small className="token-marker-row" aria-hidden="true">
                        {itemMarkers.map((marker) => (
                          <i
                            key={marker}
                            className={`token-marker marker-${marker}`}
                            data-marker={marker}
                            data-shape={markerShape(marker)}
                          />
                        ))}
                      </small>
                    )}
                  </button>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}

function timelineItems(tokens: TokenInfo[], mode: TimelineMode): TimelineItem[] {
  const replySteps = new Map<number, number>();
  tokens.filter((token) => token.source === "reply").forEach((token, index) => {
    replySteps.set(token.index, token.generationStep ?? index);
  });
  if (mode === "token") {
    return tokens.map((token) => itemFromTokens([token], replySteps));
  }
  const groups: TokenInfo[][] = [];
  for (const token of tokens) {
    const current = groups[groups.length - 1];
    const beginsWord = /^\s/.test(token.text);
    const followsSpecial = current?.some((currentToken) => currentToken.isSpecial) ?? false;
    if (!current || current[0].source !== token.source || token.isSpecial || followsSpecial || beginsWord) {
      groups.push([token]);
    } else {
      current.push(token);
    }
  }
  return groups.map((group) => itemFromTokens(group, replySteps));
}

function itemFromTokens(tokens: TokenInfo[], replySteps: Map<number, number>): TimelineItem {
  const first = tokens[0];
  const last = tokens[tokens.length - 1] ?? first;
  const text = tokens.map((token) => token.text).join("").trim();
  const generationSteps = tokens.flatMap((token) => {
    const step = replySteps.get(token.index);
    return step === undefined ? [] : [step];
  });
  return {
    key: `${first.source}:${first.index}-${last.index}`,
    tokens,
    text,
    normalizedText: text.toLowerCase(),
    source: first.source,
    start: first.index,
    end: last.index,
    generationStart: generationSteps[0],
    generationEnd: generationSteps[generationSteps.length - 1],
    isSpecial: tokens.some((token) => token.isSpecial)
  };
}

function buildTokenMetrics(run: ExplorerRun, layer: number, metric: TimelineMetric) {
  const values = new Map<number, number | undefined>();
  const residualByToken = metric === "residual"
    ? new Map(
        run.residualCells
          .filter((cell) => cell.layer === layer)
          .map((cell) => [cell.tokenIndex, cell.norm] as const)
      )
    : undefined;
  const nlaByToken = new Map<number, number>();
  if (metric === "nla") {
    for (const row of run.nla) {
      if (row.layer !== layer || row.status === "unavailable") continue;
      const current = nlaByToken.get(row.tokenIndex);
      if (current === undefined || row.cosine > current) nlaByToken.set(row.tokenIndex, row.cosine);
    }
  }
  for (const token of run.tokens) {
    if (metric === "risk") values.set(token.index, token.risk);
    if (metric === "attribution") values.set(token.index, token.attribution);
    if (metric === "probe") values.set(token.index, token.probeScore);
    if (metric === "residual") {
      values.set(token.index, residualByToken?.get(token.index));
    }
    if (metric === "nla") {
      values.set(token.index, nlaByToken.get(token.index));
    }
  }
  const finite = [...values.values()].filter((value): value is number => value !== undefined);
  const minimum = finite.length ? Math.min(...finite) : 0;
  const maximum = finite.length ? Math.max(...finite) : 1;
  return new Map(run.tokens.map((token) => {
    const value = values.get(token.index);
    const signal = value === undefined
      ? 0
      : metric === "risk" || metric === "attribution" || metric === "nla"
        ? clamp(value, 0, 1)
        : normalize(value, minimum, maximum);
    return [token.index, { value, signal }] as const;
  }));
}

function aggregateMetric(
  item: TimelineItem,
  metrics: Map<number, { value: number | undefined; signal: number }>
) {
  return item.tokens.reduce(
    (best, token) => {
      const candidate = metrics.get(token.index) ?? { value: undefined, signal: 0 };
      return candidate.signal > best.signal ? candidate : best;
    },
    metrics.get(item.tokens[0].index) ?? { value: undefined, signal: 0 }
  );
}

function buildMarkerIndex(run: ExplorerRun, pinned: number[]): MarkerIndex {
  return {
    nla: new Set(run.nla.filter((row) => row.status === "available").map((row) => row.tokenIndex)),
    pinned: new Set(pinned)
  };
}

function markersForItem(item: TimelineItem, index: MarkerIndex): Marker[] {
  const markers = new Set<Marker>();
  for (const token of item.tokens) {
    if (token.risk >= 0.7) markers.add("risk");
    if (Math.abs(token.attribution) >= 0.7) markers.add("attribution");
    if (token.probeScore !== undefined) markers.add("probe");
    if (token.monitorHit) markers.add("monitor");
    if (index.pinned.has(token.index)) markers.add("pinned");
    if (index.nla.has(token.index)) markers.add("nla");
  }
  return markerOrder.filter((marker) => markers.has(marker));
}

const markerOrder: Marker[] = ["risk", "attribution", "nla", "probe", "monitor", "pinned"];

function markerLabel(marker: Marker) {
  if (marker === "risk") return "Safety proxy";
  if (marker === "attribution") return "Attribution";
  if (marker === "nla") return "NLA evidence";
  if (marker === "probe") return "Probe";
  if (marker === "monitor") return "Monitor";
  return "Pinned";
}

function markerShape(marker: Marker) {
  if (marker === "risk") return "triangle";
  if (marker === "attribution") return "diamond";
  if (marker === "nla") return "ring";
  if (marker === "probe") return "pentagon";
  if (marker === "monitor") return "cross";
  return "square";
}

function groupBySource(items: TimelineItem[]) {
  const sources: TokenInfo["source"][] = ["prompt", "reply"];
  return sources
    .map((source) => ({ source, items: items.filter((item) => item.source === source) }))
    .filter((group) => group.items.length > 0);
}

function SourceSummary({ tokens, source }: { tokens: TokenInfo[]; source: TokenInfo["source"] }) {
  const sourceTokens = tokens.filter((token) => token.source === source);
  const first = sourceTokens[0];
  const last = sourceTokens[sourceTokens.length - 1];
  const generationSteps = sourceTokens.flatMap((token, index) =>
    source === "reply" ? [token.generationStep ?? index] : []
  );
  const tokenRange = first && last
    ? first.index === last.index ? `T${first.index}` : `T${first.index}–T${last.index}`
    : "No tokens";
  const generationRange = generationSteps.length > 0
    ? generationSteps[0] === generationSteps[generationSteps.length - 1]
      ? `G${generationSteps[0]}`
      : `G${generationSteps[0]}–G${generationSteps[generationSteps.length - 1]}`
    : undefined;
  return (
    <div className="timeline-source-summary" aria-label={`${source === "prompt" ? "Prompt" : "Reply"} sequence summary`}>
      <span>{tokenRange}</span>
      {generationRange && <span>{generationRange}</span>}
      <span>{sourceTokens.length} {sourceTokens.length === 1 ? "token" : "tokens"}</span>
    </div>
  );
}

function generationBadge(item: TimelineItem) {
  if (item.generationStart === undefined) return "";
  return item.generationEnd === undefined || item.generationEnd === item.generationStart
    ? `G${item.generationStart}`
    : `G${item.generationStart}–${item.generationEnd}`;
}

function generationDescription(item: TimelineItem) {
  if (item.generationStart === undefined) return "";
  return item.generationEnd === undefined || item.generationEnd === item.generationStart
    ? `Generation step ${item.generationStart}`
    : `Generation steps ${item.generationStart} to ${item.generationEnd}`;
}

function itemMatches(item: TimelineItem, query: string) {
  const positionMatch = query.match(/^(?:token(?:-|:|#|\s)?|#)(\d+)$/);
  const idMatch = query.match(/^id(?::|#|\s)?(\d+)$/);
  return item.normalizedText.includes(query) || item.tokens.some((token) =>
    String(token.index) === query ||
    String(token.tokenId) === query ||
    (positionMatch !== null && token.index === Number(positionMatch[1])) ||
    (idMatch !== null && token.tokenId === Number(idMatch[1]))
  );
}

function timelineItemLabel(
  item: TimelineItem,
  value: number | undefined,
  metric: TimelineMetric,
  markers: Marker[]
) {
  const positions = item.start === item.end ? `token ${item.start}` : `tokens ${item.start} to ${item.end}`;
  const metricValue = value === undefined ? "unavailable" : formatMetricValue(value, metric);
  const role = item.source === "prompt" ? "user prompt" : "assistant reply";
  const metadata = [
    role,
    item.isSpecial ? "special token" : undefined,
    item.generationStart !== undefined ? generationDescription(item).toLowerCase() : undefined,
    markers.length > 0 ? `evidence markers: ${markers.map(markerLabel).join(", ")}` : undefined
  ].filter((value): value is string => value !== undefined).join(", ");
  return `${item.text || "blank"}, ${positions}, ${metadata}, ${metricLabel(metric)} ${metricValue}`;
}

function metricLabel(metric: TimelineMetric) {
  if (metric === "risk") return "safety proxy";
  if (metric === "attribution") return "attribution";
  if (metric === "residual") return "residual norm";
  if (metric === "nla") return "NLA fidelity";
  return "probe score";
}

function formatMetricValue(value: number, metric: TimelineMetric) {
  const metricId = metric === "risk"
    ? "tokenRisk"
    : metric === "residual"
      ? "residual_norm"
      : metric === "nla"
        ? "nla_cosine"
        : metric;
  return formatMetricNumber(value, metricId, "compact");
}

function normalize(value: number, minimum: number, maximum: number) {
  return Math.abs(maximum - minimum) < 1e-12 ? 0 : (value - minimum) / (maximum - minimum);
}

function normalizeRange(left: number, right: number): [number, number] {
  return left <= right ? [left, right] : [right, left];
}

function clamp(value: number, minimum: number, maximum: number) {
  return Math.max(minimum, Math.min(maximum, value));
}
