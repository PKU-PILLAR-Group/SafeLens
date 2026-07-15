import { useEffect, useMemo, useRef, useState } from "react";
import { MoveDown, MoveRight, Network, Pin, ShieldAlert } from "lucide-react";

import { MatrixViewportControls, useMatrixViewport } from "./MatrixViewportControls";
import {
  SPECIALIZED_CANVAS_CELL_THRESHOLD,
  SpecializedMatrixCanvas
} from "./SpecializedMatrixCanvas";
import { MatrixTokenDetail, matrixTokenTitle } from "./MatrixTokenDetail";
import { MatrixComparisonSummary } from "./MatrixComparisonSummary";
import { MatrixRangeSummary } from "./MatrixRangeSummary";
import { scrollElementInlineCenter } from "./scrollElementInlineCenter";
import {
  positionRangeToTokens,
  tokenRangeToPositions,
  useMatrixRangeBrush
} from "./useMatrixRangeBrush";
import {
  ATTENTION_AGGREGATION_OPTIONS,
  attentionAggregationId,
  attentionAggregationLabel,
  attentionDifferenceId,
  attentionHeadLabel,
  attentionHeadMetric,
  attentionHeadSourceKey,
  attentionRolloutId,
  parseAttentionDifference
} from "../attentionAggregation";
import { formatMetricDelta, formatMetricNumber } from "../metricFormatting";
import type { AttentionEdgeMode, AttentionHead, TokenInfo } from "../types";

interface AttentionPatternMatrixProps {
  heads: AttentionHead[];
  selectedHead: AttentionHead;
  tokens: TokenInfo[];
  selectedSource: number;
  selectedDestination: number;
  edgeMode: AttentionEdgeMode;
  selectedRange?: [number, number];
  onHeadChange: (headId: string) => void;
  onEdgeModeChange: (mode: AttentionEdgeMode) => void;
  onSelectPair: (sourceToken: number, destinationToken: number) => void;
  onRangeSelect: (range?: [number, number]) => void;
  onHoverSource: (token: number | null) => void;
  onPin: () => void;
  onPinPair: (source: number, destination: number) => void;
}

interface HoveredPair {
  source: number;
  destination: number;
  value: number;
}

interface AttentionTokenMarker {
  token: TokenInfo;
  riskRank?: number;
  monitorHit: boolean;
}

export function AttentionPatternMatrix({
  heads,
  selectedHead,
  tokens,
  selectedSource,
  selectedDestination,
  edgeMode,
  selectedRange,
  onHeadChange,
  onEdgeModeChange,
  onSelectPair,
  onRangeSelect,
  onHoverSource,
  onPin,
  onPinPair
}: AttentionPatternMatrixProps) {
  const [hovered, setHovered] = useState<HoveredPair | null>(null);
  const [comparisonPair, setComparisonPair] = useState<{ source: number; destination: number } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const displayGroupRef = useRef<HTMLDivElement>(null);
  const lastIndividualHeadId = useRef(heads[0]?.id ?? "");
  const difference = selectedHead.difference ?? parseAttentionDifference(selectedHead.id);
  const differenceMode = Boolean(difference);
  const rolloutMode = Boolean(selectedHead.rollout);
  const viewport = useMatrixViewport({
    initialSize: 22,
    minimumSize: 14,
    maximumSize: 36,
    itemCount: tokens.length,
    labelWidth: 74,
    sessionKey: "attention"
  });
  const cellSize = viewport.size;
  const rangeBrush = useMatrixRangeBrush({
    enabled: viewport.mode === "select",
    selectedRange,
    onRangeSelect
  });
  const selectedValue =
    selectedHead.distributionByToken[selectedDestination]?.[selectedSource] ?? 0;
  const comparisonValue = comparisonPair
    ? selectedHead.distributionByToken[comparisonPair.destination]?.[comparisonPair.source] ?? 0
    : undefined;
  const maxValue = useMemo(() => {
    let maximum = 1e-9;
    for (const row of selectedHead.distributionByToken) {
      for (const value of row) maximum = Math.max(maximum, differenceMode ? Math.abs(value) : value);
    }
    return maximum;
  }, [differenceMode, selectedHead]);
  const minimumWidth = 74 + tokens.length * cellSize + (tokens.length + 1) * 3;
  const renderMode = tokens.length * tokens.length >= SPECIALIZED_CANVAS_CELL_THRESHOLD
    ? "canvas"
    : "dom";
  const selectedSourcePosition = Math.max(0, tokens.findIndex((token) => token.index === selectedSource));
  const selectedDestinationPosition = Math.max(
    0,
    tokens.findIndex((token) => token.index === selectedDestination)
  );
  const tokenMarkers = useMemo(() => buildAttentionTokenMarkers(tokens), [tokens]);
  const markerByToken = useMemo(
    () => new Map(tokenMarkers.map((marker) => [marker.token.index, marker])),
    [tokenMarkers]
  );
  const overviewMaximum = useMemo(() => {
    let maximum = 1e-9;
    for (const head of heads) {
      for (const row of head.distributionByToken) {
        for (const value of row) maximum = Math.max(maximum, value);
      }
    }
    return maximum;
  }, [heads]);

  useEffect(() => {
    setComparisonPair(null);
  }, [tokens]);

  useEffect(() => {
    if (difference) {
      lastIndividualHeadId.current = difference.selectedHeadId;
    } else if (!selectedHead.aggregation && !selectedHead.rollout) {
      lastIndividualHeadId.current = selectedHead.id;
    } else if (!heads.some((head) => head.id === lastIndividualHeadId.current)) {
      lastIndividualHeadId.current = heads[0]?.id ?? "";
    }
  }, [difference, heads, selectedHead.aggregation, selectedHead.id, selectedHead.rollout]);

  function selectDisplayOption(position: number) {
    const nextPosition = Math.max(
      0,
      Math.min(ATTENTION_AGGREGATION_OPTIONS.length - 1, position)
    );
    const option = ATTENTION_AGGREGATION_OPTIONS[nextPosition];
    if (option.id === "individual") {
      onHeadChange(difference?.selectedHeadId ?? (lastIndividualHeadId.current || heads[0]?.id || ""));
    } else if (option.id === "difference") {
      const selectedHeadId = difference?.selectedHeadId ?? (lastIndividualHeadId.current || heads[0]?.id || "");
      const baselineHeadId = resolveBaselineHeadId(heads, selectedHeadId, difference?.baselineHeadId);
      if (selectedHeadId && baselineHeadId !== selectedHeadId) {
        onHeadChange(attentionDifferenceId(selectedHeadId, baselineHeadId));
      }
    } else if (option.id === "rollout") {
      onHeadChange(attentionRolloutId());
    } else {
      onHeadChange(attentionAggregationId(option.id));
    }
    window.requestAnimationFrame(() => {
      displayGroupRef.current
        ?.querySelector<HTMLButtonElement>(`[data-display-position="${nextPosition}"]`)
        ?.focus();
    });
  }

  function selectDifferenceHead(headId: string) {
    if (!difference) {
      onHeadChange(headId);
      return;
    }
    const baselineHeadId = resolveBaselineHeadId(heads, headId, difference.baselineHeadId);
    onHeadChange(attentionDifferenceId(headId, baselineHeadId));
  }

  function movePairFocus(source: number, destination: number, key: string) {
    const sourcePosition = Math.max(0, tokens.findIndex((token) => token.index === source));
    const destinationPosition = Math.max(
      0,
      tokens.findIndex((token) => token.index === destination)
    );
    let nextSource = sourcePosition;
    let nextDestination = destinationPosition;
    if (key === "ArrowLeft") nextSource = Math.max(0, sourcePosition - 1);
    if (key === "ArrowRight") {
      nextSource = Math.min(destinationPosition, sourcePosition + 1);
    }
    if (key === "ArrowUp") nextDestination = Math.max(0, destinationPosition - 1);
    if (key === "ArrowDown") {
      nextDestination = Math.min(tokens.length - 1, destinationPosition + 1);
    }
    if (key === "Home") nextSource = 0;
    if (key === "End") nextSource = destinationPosition;
    nextSource = Math.min(nextSource, nextDestination);
    const sourceToken = tokens[nextSource]?.index;
    const destinationToken = tokens[nextDestination]?.index;
    if (sourceToken === undefined || destinationToken === undefined) return;
    onSelectPair(sourceToken, destinationToken);
    window.requestAnimationFrame(() => {
      gridRef.current
        ?.querySelector<HTMLButtonElement>(
          `[data-source="${sourceToken}"][data-destination="${destinationToken}"]`
        )
        ?.focus();
    });
  }

  return (
    <section className="surface attention-pattern-section">
      <div className="surface-header attention-pattern-header">
        <div>
          <h3>Attention pattern</h3>
          <p>
            {differenceMode
              ? "Destination × source probability delta for two retained heads."
              : rolloutMode
                ? "Retained-head mean + identity residual, multiplied from the first layer through this layer."
                : "Destination × source values from one cached head or a retained-head aggregate."}
          </p>
        </div>
        <span className="evidence-kind">
          <Network size={13} /> {selectedHead.aggregation || differenceMode || rolloutMode ? "derived attention" : "raw attention"}
        </span>
      </div>

      <div className={`attention-pattern-toolbar ${differenceMode ? "difference-mode" : ""}`} aria-label="Attention matrix controls">
        <label>
          <span>{differenceMode ? "Selected head" : "Head"}</span>
          <select
            value={difference?.selectedHeadId ?? (selectedHead.aggregation || rolloutMode ? "" : selectedHead.id)}
            onChange={(event) => selectDifferenceHead(event.target.value)}
          >
            <option value="" disabled>Derived display</option>
            {heads.map((head) => (
              <option key={head.id} value={head.id}>{head.id}</option>
            ))}
          </select>
        </label>
        {difference && (
          <label className="attention-difference-baseline">
            <span>Baseline</span>
            <select
              value={difference.baselineHeadId}
              onChange={(event) => onHeadChange(
                attentionDifferenceId(difference.selectedHeadId, event.target.value)
              )}
            >
              {heads.map((head) => (
                <option
                  key={head.id}
                  value={head.id}
                  disabled={head.id === difference.selectedHeadId}
                >
                  {head.id}
                </option>
              ))}
            </select>
          </label>
        )}
        <div className="attention-aggregation-control">
          <span>Display</span>
          <div
            ref={displayGroupRef}
            className="toolbar-segment"
            role="radiogroup"
            aria-label="Attention head display"
          >
            {ATTENTION_AGGREGATION_OPTIONS.map((option, position) => {
              const selected = option.id === "individual"
                ? !selectedHead.aggregation && !differenceMode && !rolloutMode
                : option.id === "difference"
                  ? differenceMode
                  : option.id === "rollout"
                    ? rolloutMode
                    : selectedHead.aggregation === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  className={selected ? "active" : ""}
                  data-display-position={position}
                  tabIndex={selected ? 0 : -1}
                  disabled={option.id === "difference" && heads.length < 2}
                  title={option.description}
                  onClick={() => selectDisplayOption(position)}
                  onKeyDown={(event) => {
                    let nextPosition = position;
                    if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextPosition -= 1;
                    else if (event.key === "ArrowRight" || event.key === "ArrowDown") nextPosition += 1;
                    else if (event.key === "Home") nextPosition = 0;
                    else if (event.key === "End") nextPosition = ATTENTION_AGGREGATION_OPTIONS.length - 1;
                    else return;
                    event.preventDefault();
                    event.stopPropagation();
                    selectDisplayOption(nextPosition);
                  }}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>
        <div className="attention-pair-summary" aria-label="Selected attention pair">
          <span><b>{tokenLabel(tokens, selectedDestination)}</b>destination {selectedDestination}</span>
          <i>←</i>
          <span><b>{tokenLabel(tokens, selectedSource)}</b>source {selectedSource}</span>
          <strong className={differenceMode ? (selectedValue < 0 ? "negative" : "positive") : ""}>
            {differenceMode
              ? formatMetricDelta(selectedValue, attentionHeadMetric(selectedHead), "compact")
              : formatMetricNumber(selectedValue, attentionHeadMetric(selectedHead), "compact")}
          </strong>
        </div>
        <div className="toolbar-actions">
          <MatrixViewportControls viewport={viewport} label="attention matrix" />
          <button onClick={onPin}><Pin size={14} /> Pin pair</button>
        </div>
      </div>

      <AttentionHeadOverview
        heads={heads}
        selectedHead={selectedHead}
        tokens={tokens}
        selectedSource={selectedSource}
        selectedDestination={selectedDestination}
        maximum={overviewMaximum}
        onHeadChange={selectDifferenceHead}
      />

      <AttentionRiskPositionRail
        markers={tokenMarkers}
        selectedSource={selectedSource}
        selectedDestination={selectedDestination}
        onSelectSource={(tokenIndex) => onSelectPair(
          tokenIndex,
          Math.max(selectedDestination, tokenIndex)
        )}
        onSelectDestination={(tokenIndex) => onSelectPair(
          Math.min(selectedSource, tokenIndex),
          tokenIndex
        )}
      />

      <AttentionEdgeProfile
        head={selectedHead}
        tokens={tokens}
        mode={edgeMode}
        selectedSource={selectedSource}
        selectedDestination={selectedDestination}
        onModeChange={onEdgeModeChange}
        onSelectPair={onSelectPair}
      />

      <div className="attention-axis-label attention-source-axis">Source token →</div>
      <MatrixComparisonSummary
        label="Attention matrix"
        primary={`D${selectedDestination} · S${selectedSource}`}
        anchor={comparisonPair ? `D${comparisonPair.destination} · S${comparisonPair.source}` : undefined}
        delta={comparisonValue === undefined
          ? undefined
          : formatMetricDelta(selectedValue - comparisonValue, attentionHeadMetric(selectedHead), "compact")}
        deltaLabel="display delta"
        onClear={() => setComparisonPair(null)}
      />
      <MatrixRangeSummary label="Source token" range={selectedRange} onClear={() => onRangeSelect(undefined)} />
      <div
        ref={viewport.scrollRef}
        className={`attention-matrix-scroll ${renderMode === "canvas" ? "specialized-canvas-mode" : ""} ${viewport.mode === "pan" ? "pan-mode" : ""}`}
        {...viewport.viewportProps}
      >
        {renderMode === "canvas" ? (
          <SpecializedMatrixCanvas
            scrollRef={viewport.scrollRef}
            rowCount={tokens.length}
            columnCount={tokens.length}
            rowHeight={24}
            columnWidth={cellSize}
            rowLabelWidth={74}
            axesPinned={viewport.axesPinned}
            selectedRow={selectedDestinationPosition}
            selectedColumn={selectedSourcePosition}
            comparisonRow={comparisonPair
              ? tokens.findIndex((token) => token.index === comparisonPair.destination)
              : undefined}
            comparisonColumn={comparisonPair
              ? tokens.findIndex((token) => token.index === comparisonPair.source)
              : undefined}
            rangeAxis="column"
            selectedRange={tokenRangeToPositions(tokens, selectedRange)}
            rangeEnabled={viewport.mode === "select"}
            ariaLabel={`Attention pattern Canvas matrix, ${tokens.length} destination rows by ${tokens.length} source columns`}
            selectedDescription={`Selected ${attentionHeadLabel(selectedHead)}, destination ${selectedDestination}, source ${selectedSource}, ${differenceMode ? "attention probability delta" : "attention value"} ${selectedValue.toFixed(6)}.`}
            overviewRevision={`${selectedHead.id}:${maxValue}`}
            cornerLabel="dest"
            rowLabel={(row) => {
              const token = tokens[row];
              return `D${token?.index ?? row}${attentionMarkerSuffix(token ? markerByToken.get(token.index) : undefined)}`;
            }}
            columnLabel={(column) => {
              const token = tokens[column];
              return `${token?.index ?? column}${attentionMarkerSuffix(token ? markerByToken.get(token.index) : undefined)}`;
            }}
            cell={(row, column) => {
              const destination = tokens[row]?.index ?? row;
              const source = tokens[column]?.index ?? column;
              const masked = source > destination;
              const value = selectedHead.distributionByToken[destination]?.[source] ?? 0;
              return {
                fill: masked ? "#f5f7f7" : attentionCellColor(value, maxValue, differenceMode),
                hatch: masked ? "#d8e1e2" : undefined,
                disabled: masked,
                label: masked
                  ? `Destination ${destination}, source ${source}, causal mask`
                  : `Destination ${destination}, source ${source}, ${differenceMode ? "attention probability delta" : "attention"} ${value.toFixed(6)}`
              };
            }}
            navigate={({ row, column }, key) => {
              let nextRow = row;
              let nextColumn = column;
              if (key === "ArrowLeft") nextColumn -= 1;
              if (key === "ArrowRight") nextColumn += 1;
              if (key === "ArrowUp") nextRow -= 1;
              if (key === "ArrowDown") nextRow += 1;
              if (key === "Home") nextColumn = 0;
              if (key === "End") nextColumn = nextRow;
              nextRow = Math.max(0, Math.min(tokens.length - 1, nextRow));
              nextColumn = Math.max(0, Math.min(nextRow, nextColumn));
              return { row: nextRow, column: nextColumn };
            }}
            onSelect={(row, column, modifiers) => {
              const destination = tokens[row]?.index;
              const source = tokens[column]?.index;
              if (source === undefined || destination === undefined) return;
              if (modifiers.anchor) {
                setComparisonPair({ source, destination });
              } else if (modifiers.pin) {
                onPinPair(source, destination);
              } else {
                onSelectPair(source, destination);
              }
            }}
            onRangeSelect={(range) => onRangeSelect(positionRangeToTokens(tokens, range))}
            onPin={onPin}
            onHover={(row, column) => {
              const destination = tokens[row]?.index;
              const source = tokens[column]?.index;
              if (source === undefined || destination === undefined || source > destination) return;
              const value = selectedHead.distributionByToken[destination]?.[source] ?? 0;
              setHovered({ source, destination, value });
              onHoverSource(source);
            }}
            onHoverEnd={() => {
              setHovered(null);
              onHoverSource(null);
            }}
          />
        ) : (
        <div
          ref={gridRef}
          className={`attention-pattern-grid ${viewport.axesPinned ? "axes-pinned" : ""}`}
          style={{
            gridTemplateColumns: `74px repeat(${tokens.length}, ${cellSize}px)`,
            minWidth: `${minimumWidth}px`
          }}
          {...rangeBrush.gridProps}
        >
          <div className="attention-grid-corner">dest ↓</div>
          {tokens.map((token) => (
            <div
              key={`source-${token.index}`}
              className={`attention-source-label ${markerByToken.has(token.index) ? "marked" : ""} ${markerByToken.get(token.index)?.monitorHit ? "monitor" : ""} ${selectedSource === token.index ? "selected" : ""} ${rangeBrush.inRange(token.index) ? "in-range" : ""}`}
              data-range-token={token.index}
              data-marker-token={markerByToken.has(token.index) ? token.index : undefined}
              title={attentionMarkerTitle(token, markerByToken.get(token.index), "source")}
            >
              <span>{token.index}</span>
              {markerByToken.has(token.index) && (
                <i>{attentionMarkerShortLabel(markerByToken.get(token.index)!)}</i>
              )}
            </div>
          ))}
          {tokens.map((destination) => (
            <AttentionRow
              key={`destination-${destination.index}`}
              destination={destination}
              tokens={tokens}
              values={selectedHead.distributionByToken[destination.index] ?? []}
              marker={markerByToken.get(destination.index)}
              maxValue={maxValue}
              signed={differenceMode}
              selectedSource={selectedSource}
              selectedDestination={selectedDestination}
              comparisonPair={comparisonPair}
              inRange={rangeBrush.inRange}
              onSelectPair={onSelectPair}
              onSetComparison={setComparisonPair}
              onPinPair={onPinPair}
              onPin={onPin}
              onMoveFocus={movePairFocus}
              onHover={(pair) => {
                setHovered(pair);
                onHoverSource(pair?.source ?? null);
              }}
            />
          ))}
        </div>
        )}
      </div>

      <AttentionPairTooltip
        pair={hovered ?? {
          source: selectedSource,
          destination: selectedDestination,
          value: selectedValue
        }}
        focused={hovered !== null}
        tokens={tokens}
        heads={heads}
        head={selectedHead}
      />

      <div className={`attention-pattern-legend ${differenceMode ? "difference" : ""}`}>
        {differenceMode && <span><i className="attention-legend-negative" />{formatMetricDelta(-maxValue, attentionHeadMetric(selectedHead), "compact")}</span>}
        <span><i className="attention-legend-zero" />0</span>
        {!differenceMode && <span><i className="attention-legend-mid" />{(maxValue / 2).toFixed(2)}</span>}
        <span><i className="attention-legend-high" />{differenceMode
          ? formatMetricDelta(maxValue, attentionHeadMetric(selectedHead), "compact")
          : formatMetricNumber(maxValue, attentionHeadMetric(selectedHead), "compact")}</span>
        <span><i className="attention-legend-mask" />causal mask</span>
        <b>
          {difference
            ? `${difference.selectedHeadId} - ${difference.baselineHeadId} · raw probability delta`
            : selectedHead.rollout
              ? `retained mean + identity residual rollout · L${selectedHead.rollout.layers[0]}–L${selectedHead.layer}`
            : selectedHead.aggregation
            ? `${attentionAggregationLabel(selectedHead.aggregation)} · retained raw probabilities`
            : `raw softmax probability · ${selectedHead.id}`}
        </b>
      </div>
    </section>
  );
}

function AttentionRiskPositionRail({
  markers,
  selectedSource,
  selectedDestination,
  onSelectSource,
  onSelectDestination
}: {
  markers: AttentionTokenMarker[];
  selectedSource: number;
  selectedDestination: number;
  onSelectSource: (tokenIndex: number) => void;
  onSelectDestination: (tokenIndex: number) => void;
}) {
  const monitorCount = markers.filter((marker) => marker.monitorHit).length;
  return (
    <section className="attention-risk-markers" aria-labelledby="attention-risk-markers-title">
      <header>
        <div>
          <h4 id="attention-risk-markers-title">Risk-position markers</h4>
          <p>Top 3 run-relative safety proxy positions · explicit monitor hits remain separate</p>
        </div>
        <span><ShieldAlert size={13} /> {monitorCount} monitor {monitorCount === 1 ? "hit" : "hits"}</span>
      </header>
      <div className="attention-risk-marker-list" role="list" aria-label="Attention risk-position markers">
        {markers.map((marker) => (
          <article
            key={marker.token.index}
            className={`${marker.monitorHit ? "monitor" : ""} ${marker.riskRank ? "proxy" : ""}`}
            data-risk-marker-token={marker.token.index}
            role="listitem"
          >
            <div>
              <span>T{marker.token.index}</span>
              <strong>{visibleToken(marker.token.text)}</strong>
              <small>
                {marker.riskRank ? `proxy #${marker.riskRank} · ${marker.token.risk.toFixed(3)}` : "outside proxy top 3"}
                {marker.monitorHit ? " · explicit monitor hit" : ""}
              </small>
            </div>
            <div className="attention-risk-marker-actions">
              <button
                type="button"
                aria-label={`Use token ${marker.token.index} ${visibleToken(marker.token.text)} as attention source`}
                aria-pressed={selectedSource === marker.token.index}
                title="Use as source token"
                onClick={() => onSelectSource(marker.token.index)}
              >
                <MoveRight size={14} />
              </button>
              <button
                type="button"
                aria-label={`Use token ${marker.token.index} ${visibleToken(marker.token.text)} as attention destination`}
                aria-pressed={selectedDestination === marker.token.index}
                title="Use as destination token"
                onClick={() => onSelectDestination(marker.token.index)}
              >
                <MoveDown size={14} />
              </button>
            </div>
          </article>
        ))}
      </div>
      <div className="attention-risk-marker-legend" aria-label="Risk-position marker legend">
        <span><i className="proxy" />run-relative proxy rank</span>
        <span><i className="monitor" />explicit monitor hit</span>
        <b>Markers locate tokens only; they do not change or explain attention values.</b>
      </div>
    </section>
  );
}

function AttentionEdgeProfile({
  head,
  tokens,
  mode,
  selectedSource,
  selectedDestination,
  onModeChange,
  onSelectPair
}: {
  head: AttentionHead;
  tokens: TokenInfo[];
  mode: AttentionEdgeMode;
  selectedSource: number;
  selectedDestination: number;
  onModeChange: (mode: AttentionEdgeMode) => void;
  onSelectPair: (source: number, destination: number) => void;
}) {
  const modeRef = useRef<HTMLDivElement>(null);
  const railRef = useRef<HTMLDivElement>(null);
  const signed = Boolean(head.difference);
  const points = useMemo(() => mode === "incoming"
    ? tokens
        .filter((token) => token.index <= selectedDestination)
        .map((token) => ({
          token,
          value: head.distributionByToken[selectedDestination]?.[token.index] ?? 0
        }))
    : tokens
        .filter((token) => token.index >= selectedSource)
        .map((token) => ({
          token,
          value: head.distributionByToken[token.index]?.[selectedSource] ?? 0
        })), [head, mode, selectedDestination, selectedSource, tokens]);
  const selectedPointToken = mode === "incoming" ? selectedSource : selectedDestination;
  const maximum = Math.max(1e-12, ...points.map((point) => Math.abs(point.value)));
  const total = points.reduce((sum, point) => sum + point.value, 0);
  const peak = points.reduce(
    (best, point) => Math.abs(point.value) > Math.abs(best.value) ? point : best,
    points[0] ?? { token: tokens[0], value: 0 }
  );
  const selectedPoint = points.find((point) => point.token.index === selectedPointToken);

  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    const revealSelected = () => {
      const selected = rail.querySelector<HTMLButtonElement>(
        `[data-edge-token="${selectedPointToken}"]`
      );
      if (selected) scrollElementInlineCenter(rail, selected);
    };
    revealSelected();
    const observer = new ResizeObserver(revealSelected);
    observer.observe(rail);
    return () => observer.disconnect();
  }, [mode, selectedPointToken]);

  function selectMode(position: number) {
    const nextMode: AttentionEdgeMode = position <= 0 ? "incoming" : "outgoing";
    onModeChange(nextMode);
    window.requestAnimationFrame(() => {
      modeRef.current
        ?.querySelector<HTMLButtonElement>(`[data-edge-mode="${nextMode}"]`)
        ?.focus({ preventScroll: true });
    });
  }

  function selectPoint(position: number) {
    const point = points[Math.max(0, Math.min(points.length - 1, position))];
    if (!point) return;
    if (mode === "incoming") onSelectPair(point.token.index, selectedDestination);
    else onSelectPair(selectedSource, point.token.index);
    window.requestAnimationFrame(() => {
      railRef.current
        ?.querySelector<HTMLButtonElement>(`[data-edge-token="${point.token.index}"]`)
        ?.focus({ preventScroll: true });
    });
  }

  return (
    <section className={`attention-edge-profile ${signed ? "signed" : ""}`} aria-labelledby="attention-edge-profile-title">
      <header>
        <div>
          <h4 id="attention-edge-profile-title">Attention edge profile</h4>
          <p>
            {mode === "incoming"
              ? `Incoming sources for destination D${selectedDestination}`
              : `Outgoing destinations for source S${selectedSource}`}
            {signed ? " · signed selected-minus-baseline delta" : " · displayed attention values"}
          </p>
        </div>
        <div
          ref={modeRef}
          className="toolbar-segment attention-edge-mode"
          role="radiogroup"
          aria-label="Attention edge direction"
        >
          {(["incoming", "outgoing"] as AttentionEdgeMode[]).map((option, position) => (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={mode === option}
              className={mode === option ? "active" : ""}
              data-edge-mode={option}
              tabIndex={mode === option ? 0 : -1}
              onClick={() => selectMode(position)}
              onKeyDown={(event) => {
                if (event.key === "ArrowLeft" || event.key === "ArrowUp" || event.key === "Home") {
                  event.preventDefault();
                  selectMode(0);
                } else if (event.key === "ArrowRight" || event.key === "ArrowDown" || event.key === "End") {
                  event.preventDefault();
                  selectMode(1);
                }
              }}
            >
              {option === "incoming" ? "Incoming" : "Outgoing"}
            </button>
          ))}
        </div>
      </header>
      <div className="attention-edge-summary" aria-label="Attention edge profile summary">
        <span><b>{formatEdgeValue(total, signed)}</b>{signed ? "net profile delta" : "profile sum"}</span>
        <span><b>{peak ? `T${peak.token?.index ?? "n/a"} · ${formatEdgeValue(peak.value, signed)}` : "n/a"}</b>peak |value|</span>
        <span><b>{formatEdgeValue(selectedPoint?.value ?? 0, signed)}</b>selected pair</span>
        <span><b>{points.length}</b>{mode === "incoming" ? "eligible sources" : "eligible destinations"}</span>
      </div>
      <div
        ref={railRef}
        className="attention-edge-token-rail"
        role="radiogroup"
        aria-label={`${mode === "incoming" ? "Incoming source" : "Outgoing destination"} token profile`}
      >
        {points.map((point, position) => {
          const selected = point.token.index === selectedPointToken;
          const strength = Math.abs(point.value) / maximum;
          return (
            <button
              key={point.token.index}
              type="button"
              role="radio"
              aria-checked={selected}
              aria-label={`${mode === "incoming" ? "Source" : "Destination"} token ${point.token.index} ${visibleToken(point.token.text)}, ${signed ? "attention probability delta" : "attention value"} ${formatEdgeValue(point.value, signed)}`}
              className={`${point.value < 0 ? "negative" : "positive"} ${selected ? "selected" : ""}`}
              data-edge-token={point.token.index}
              tabIndex={selected ? 0 : -1}
              style={{ "--edge-strength": strength } as React.CSSProperties}
              onClick={() => selectPoint(position)}
              onKeyDown={(event) => {
                let next = position;
                if (event.key === "ArrowLeft" || event.key === "ArrowUp") next -= 1;
                else if (event.key === "ArrowRight" || event.key === "ArrowDown") next += 1;
                else if (event.key === "Home") next = 0;
                else if (event.key === "End") next = points.length - 1;
                else return;
                event.preventDefault();
                selectPoint(next);
              }}
            >
              <span><i>{point.token.index}</i><strong>{visibleToken(point.token.text)}</strong></span>
              <b aria-hidden="true"><i /></b>
              <em>{formatEdgeValue(point.value, signed)}</em>
            </button>
          );
        })}
      </div>
      <div className="attention-edge-legend" aria-label="Attention edge profile legend">
        {signed ? (
          <>
            <span><i className="negative" />baseline more</span>
            <span><i className="zero" />zero delta</span>
            <span><i className="positive" />selected more</span>
          </>
        ) : (
          <><span><i className="zero" />zero</span><span><i className="positive" />displayed value</span></>
        )}
        <b>{attentionHeadLabel(head)} · descriptive edge profile</b>
      </div>
    </section>
  );
}

interface HeadRowSummary {
  head: AttentionHead;
  entropy: number;
  peakSource: number;
  peakValue: number;
}

function AttentionHeadOverview({
  heads,
  selectedHead,
  tokens,
  selectedSource,
  selectedDestination,
  maximum,
  onHeadChange
}: {
  heads: AttentionHead[];
  selectedHead: AttentionHead;
  tokens: TokenInfo[];
  selectedSource: number;
  selectedDestination: number;
  maximum: number;
  onHeadChange: (headId: string) => void;
}) {
  const groupRef = useRef<HTMLDivElement>(null);
  const summaries = useMemo(
    () => heads.map((head) => summarizeHeadRow(head, tokens, selectedDestination)),
    [heads, selectedDestination, tokens]
  );

  function selectHead(position: number) {
    const nextPosition = Math.max(0, Math.min(summaries.length - 1, position));
    const next = summaries[nextPosition];
    if (!next) return;
    onHeadChange(next.head.id);
    window.requestAnimationFrame(() => {
      groupRef.current
        ?.querySelector<HTMLButtonElement>(`[data-head-position="${nextPosition}"]`)
        ?.focus();
    });
  }

  function handleHeadKey(position: number, key: string) {
    if (key === "ArrowLeft" || key === "ArrowUp") selectHead(position - 1);
    else if (key === "ArrowRight" || key === "ArrowDown") selectHead(position + 1);
    else if (key === "Home") selectHead(0);
    else if (key === "End") selectHead(summaries.length - 1);
    else return false;
    return true;
  }

  return (
    <section className="attention-head-overview" aria-labelledby="attention-head-overview-title">
      <header>
        <div>
          <h4 id="attention-head-overview-title">Head overview</h4>
          <p>Same matrix scale · selected destination row D{selectedDestination}</p>
        </div>
        <span>{heads.length} retained · L{selectedHead.layer}</span>
      </header>
      <div
        ref={groupRef}
        className="attention-head-multiples"
        role="group"
        aria-label={`Attention heads at layer ${selectedHead.layer}`}
      >
        {summaries.map((summary, position) => {
          const selected = selectedHead.difference
            ? summary.head.id === selectedHead.difference.selectedHeadId
            : summary.head.id === selectedHead.id;
          const baseline = selectedHead.difference?.baselineHeadId === summary.head.id;
          const peakToken = tokens.find((token) => token.index === summary.peakSource);
          return (
            <button
              key={summary.head.id}
              type="button"
              aria-pressed={selected}
              aria-label={`${summary.head.id}, destination ${selectedDestination}, row entropy ${summary.entropy.toFixed(3)} nats, peak source ${summary.peakSource}, peak probability ${summary.peakValue.toFixed(4)}`}
              className={`attention-head-multiple ${selected ? "selected" : ""} ${baseline ? "baseline" : ""}`}
              data-head-position={position}
              tabIndex={selected || ((selectedHead.aggregation || selectedHead.rollout) && position === 0) ? 0 : -1}
              onClick={() => onHeadChange(summary.head.id)}
              onKeyDown={(event) => {
                if (!handleHeadKey(position, event.key)) return;
                event.preventDefault();
                event.stopPropagation();
              }}
            >
              <span className="attention-head-multiple-title">
                <strong>{summary.head.id}</strong>
                <small>{selected ? "Selected" : baseline ? "Baseline" : summary.head.role}</small>
              </span>
              <span className="attention-head-multiple-body">
                <AttentionHeadThumbnail
                  head={summary.head}
                  tokens={tokens}
                  selectedSource={selectedSource}
                  selectedDestination={selectedDestination}
                  maximum={maximum}
                />
                <span className="attention-head-multiple-stats">
                  <span><small>Row entropy</small><b>{summary.entropy.toFixed(3)}</b></span>
                  <span title={peakToken?.text || "space"}>
                    <small>Peak source</small><b>{summary.peakSource} · {visibleToken(peakToken?.text)}</b>
                  </span>
                  <span><small>Peak probability</small><b>{summary.peakValue.toFixed(4)}</b></span>
                </span>
              </span>
            </button>
          );
        })}
      </div>
      <div className="attention-head-overview-scale" aria-label={`Shared head overview scale from 0 to ${maximum.toFixed(4)}`}>
        <span>0</span><i /><span>{maximum.toFixed(2)}</span><b>raw probability</b>
      </div>
    </section>
  );
}

function AttentionHeadThumbnail({
  head,
  tokens,
  selectedSource,
  selectedDestination,
  maximum
}: {
  head: AttentionHead;
  tokens: TokenInfo[];
  selectedSource: number;
  selectedDestination: number;
  maximum: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context || tokens.length === 0) return;
    const width = canvas.width;
    const height = canvas.height;
    const image = context.createImageData(width, height);
    for (let y = 0; y < height; y += 1) {
      const rowPosition = Math.min(tokens.length - 1, Math.floor(y / height * tokens.length));
      const destination = tokens[rowPosition]?.index ?? rowPosition;
      for (let x = 0; x < width; x += 1) {
        const columnPosition = Math.min(tokens.length - 1, Math.floor(x / width * tokens.length));
        const source = tokens[columnPosition]?.index ?? columnPosition;
        const offset = (y * width + x) * 4;
        if (source > destination) {
          image.data[offset] = 244;
          image.data[offset + 1] = 247;
          image.data[offset + 2] = 247;
        } else {
          const value = head.distributionByToken[destination]?.[source] ?? 0;
          const strength = Math.max(0, Math.min(1, value / maximum));
          const blend = 0.1 + strength * 0.9;
          image.data[offset] = Math.round(237 + (20 - 237) * blend);
          image.data[offset + 1] = Math.round(243 + (123 - 243) * blend);
          image.data[offset + 2] = Math.round(243 + (118 - 243) * blend);
        }
        image.data[offset + 3] = 255;
      }
    }
    context.putImageData(image, 0, 0);

    const destinationPosition = Math.max(0, tokens.findIndex((token) => token.index === selectedDestination));
    const sourcePosition = Math.max(0, tokens.findIndex((token) => token.index === selectedSource));
    const rowY = (destinationPosition + 0.5) / tokens.length * height;
    const pointX = (sourcePosition + 0.5) / tokens.length * width;
    context.strokeStyle = "#f4c15d";
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(0, rowY);
    context.lineTo(width, rowY);
    context.stroke();
    context.fillStyle = "#8f4c12";
    context.beginPath();
    context.arc(pointX, rowY, 2.4, 0, Math.PI * 2);
    context.fill();
  }, [head, maximum, selectedDestination, selectedSource, tokens]);

  return (
    <canvas
      ref={canvasRef}
      className="attention-head-thumbnail"
      width={76}
      height={76}
      aria-hidden="true"
    />
  );
}

function summarizeHeadRow(
  head: AttentionHead,
  tokens: TokenInfo[],
  selectedDestination: number
): HeadRowSummary {
  const row = head.distributionByToken[selectedDestination] ?? [];
  const available = tokens
    .filter((token) => token.index <= selectedDestination)
    .map((token) => ({ source: token.index, value: Math.max(0, row[token.index] ?? 0) }));
  const total = available.reduce((sum, item) => sum + item.value, 0);
  let entropy = 0;
  if (total > 0) {
    for (const item of available) {
      const probability = item.value / total;
      if (probability > 0) entropy -= probability * Math.log(probability);
    }
  }
  const peak = available.reduce(
    (best, item) => item.value > best.value ? item : best,
    available[0] ?? { source: selectedDestination, value: 0 }
  );
  return { head, entropy, peakSource: peak.source, peakValue: peak.value };
}

function visibleToken(value: string | undefined) {
  return value?.trim() ? value : "space";
}

function AttentionRow({
  destination,
  tokens,
  values,
  marker,
  maxValue,
  signed,
  selectedSource,
  selectedDestination,
  comparisonPair,
  inRange,
  onSelectPair,
  onSetComparison,
  onPinPair,
  onPin,
  onMoveFocus,
  onHover
}: {
  destination: TokenInfo;
  tokens: TokenInfo[];
  values: number[];
  marker?: AttentionTokenMarker;
  maxValue: number;
  signed: boolean;
  selectedSource: number;
  selectedDestination: number;
  comparisonPair: { source: number; destination: number } | null;
  inRange: (token: number) => boolean;
  onSelectPair: (source: number, destination: number) => void;
  onSetComparison: (pair: { source: number; destination: number }) => void;
  onPinPair: (source: number, destination: number) => void;
  onPin: () => void;
  onMoveFocus: (source: number, destination: number, key: string) => void;
  onHover: (pair: HoveredPair | null) => void;
}) {
  return (
    <>
      <button
        className={`attention-destination-label ${marker ? "marked" : ""} ${marker?.monitorHit ? "monitor" : ""} ${selectedDestination === destination.index ? "selected" : ""}`}
        data-marker-token={marker ? destination.index : undefined}
        onClick={() => onSelectPair(Math.min(selectedSource, destination.index), destination.index)}
        tabIndex={-1}
        title={attentionMarkerTitle(destination, marker, "destination")}
      >
        <span>{destination.index}</span>
        <b>{destination.text || "␠"}</b>
        {marker && <i>{attentionMarkerShortLabel(marker)}</i>}
      </button>
      {tokens.map((source) => {
        const masked = source.index > destination.index;
        const value = values[source.index] ?? 0;
        const selected =
          selectedSource === source.index && selectedDestination === destination.index;
        const comparison =
          comparisonPair?.source === source.index && comparisonPair.destination === destination.index;
        return (
          <button
            key={`${destination.index}:${source.index}`}
            data-source={source.index}
            data-destination={destination.index}
            data-range-token={source.index}
            className={`attention-pattern-cell ${signed ? "difference" : ""} ${signed && value < 0 ? "negative" : "positive"} ${masked ? "masked" : ""} ${selected ? "selected" : ""} ${comparison ? "comparison" : ""} ${inRange(source.index) ? "in-range" : ""}`}
            style={{ "--attention": masked ? 0 : Math.abs(value) / maxValue } as React.CSSProperties}
            aria-label={
              masked
                ? `Destination ${destination.index}, source ${source.index}, causal mask`
                : `Destination ${destination.index}, source ${source.index}, ${signed ? "attention probability delta" : "attention"} ${value.toFixed(4)}`
            }
            disabled={masked}
            tabIndex={selected ? 0 : -1}
            aria-keyshortcuts={masked ? undefined : "ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter Space"}
            onClick={(event) => {
              if (event.shiftKey) {
                onSetComparison({ source: source.index, destination: destination.index });
              } else if (event.metaKey || event.ctrlKey) {
                onPinPair(source.index, destination.index);
              } else {
                onSelectPair(source.index, destination.index);
              }
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
                onSetComparison({ source: source.index, destination: destination.index });
                return;
              }
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                event.stopPropagation();
                onPinPair(source.index, destination.index);
                return;
              }
              if (event.key === " ") {
                event.preventDefault();
                event.stopPropagation();
                onPin();
                return;
              }
              if (!isNavigationKey(event.key)) return;
              event.preventDefault();
              event.stopPropagation();
              onMoveFocus(source.index, destination.index, event.key);
            }}
            onMouseEnter={() => {
              if (!masked) onHover({ source: source.index, destination: destination.index, value });
            }}
            onMouseLeave={() => onHover(null)}
            onFocus={() => {
              if (!masked) onHover({ source: source.index, destination: destination.index, value });
            }}
            onBlur={() => onHover(null)}
          />
        );
      })}
    </>
  );
}

function AttentionPairTooltip({
  pair,
  focused,
  tokens,
  heads,
  head
}: {
  pair: HoveredPair;
  focused: boolean;
  tokens: TokenInfo[];
  heads: AttentionHead[];
  head: AttentionHead;
}) {
  const stats = attentionPairStats(head, heads, tokens, pair);
  return (
    <div className="attention-pair-tooltip" aria-label="Attention pair details" aria-live="polite">
      <MatrixTokenDetail tokens={tokens} tokenIndex={pair.source} roleLabel="source" />
      <MatrixTokenDetail tokens={tokens} tokenIndex={pair.destination} roleLabel="destination" />
      <span><b>{head.difference
        ? formatMetricDelta(pair.value, attentionHeadMetric(head), "exact")
        : formatMetricNumber(pair.value, attentionHeadMetric(head), "exact")}</b>{head.difference ? "probability delta" : "probability"}</span>
      <span><b>{attentionHeadLabel(head)}</b>{head.aggregation || head.difference || head.rollout ? "display" : "head"}</span>
      <span title={stats.entropyTitle}><b>{stats.entropyValue}</b>{stats.entropyLabel}</span>
      <span><b>#{stats.sourceRank} / {stats.sourceCount}</b>{head.difference ? "|delta| source rank" : "source rank"}</span>
      <span><b>{focused ? "focused cell" : "selected pair"}</b>interaction state</span>
      <span className="attention-cache-key">
        <b>{attentionHeadSourceKey(head, pair.destination, pair.source)}</b>source key
      </span>
    </div>
  );
}

function attentionPairStats(
  head: AttentionHead,
  heads: AttentionHead[],
  tokens: TokenInfo[],
  pair: HoveredPair
) {
  const eligible = tokens
    .filter((token) => token.index <= pair.destination)
    .map((token) => ({
      tokenIndex: token.index,
      value: head.distributionByToken[pair.destination]?.[token.index] ?? 0
    }));
  const ranked = [...eligible].sort((left, right) =>
    (head.difference ? Math.abs(right.value) - Math.abs(left.value) : right.value - left.value) ||
    left.tokenIndex - right.tokenIndex
  );
  const sourceRank = Math.max(1, ranked.findIndex((item) => item.tokenIndex === pair.source) + 1);
  if (head.difference) {
    const selected = heads.find((candidate) => candidate.id === head.difference?.selectedHeadId);
    const baseline = heads.find((candidate) => candidate.id === head.difference?.baselineHeadId);
    const selectedEntropy = attentionRowEntropy(
      selected?.distributionByToken[pair.destination] ?? [],
      pair.destination
    );
    const baselineEntropy = attentionRowEntropy(
      baseline?.distributionByToken[pair.destination] ?? [],
      pair.destination
    );
    return {
      entropyValue: `${selectedEntropy.toFixed(3)} / ${baselineEntropy.toFixed(3)}`,
      entropyLabel: "selected / baseline row entropy",
      entropyTitle: `Row entropy delta ${formatSigned(selectedEntropy - baselineEntropy, 3)} nats`,
      sourceRank,
      sourceCount: eligible.length
    };
  }
  const entropy = attentionRowEntropy(
    head.distributionByToken[pair.destination] ?? [],
    pair.destination
  );
  return {
    entropyValue: `${entropy.toFixed(3)} nats`,
    entropyLabel: "destination row entropy",
    entropyTitle: "Entropy after normalizing the displayed non-negative destination row.",
    sourceRank,
    sourceCount: eligible.length
  };
}

function attentionRowEntropy(row: number[], destination: number) {
  const values = row.slice(0, destination + 1).map((value) => Math.max(0, value));
  const total = values.reduce((sum, value) => sum + value, 0);
  if (total <= 0) return 0;
  return values.reduce((entropy, value) => {
    const probability = value / total;
    return probability > 0 ? entropy - probability * Math.log(probability) : entropy;
  }, 0);
}

function tokenLabel(tokens: TokenInfo[], index: number) {
  return tokens.find((token) => token.index === index)?.text || "␠";
}

function buildAttentionTokenMarkers(tokens: TokenInfo[]) {
  const topRisk = [...tokens]
    .sort((left, right) => right.risk - left.risk || left.index - right.index)
    .slice(0, Math.min(3, tokens.length));
  const riskRanks = new Map(topRisk.map((token, index) => [token.index, index + 1]));
  return tokens
    .filter((token) => riskRanks.has(token.index) || token.monitorHit)
    .map((token) => ({
      token,
      riskRank: riskRanks.get(token.index),
      monitorHit: Boolean(token.monitorHit)
    }))
    .sort((left, right) =>
      (left.riskRank ?? Number.MAX_SAFE_INTEGER) - (right.riskRank ?? Number.MAX_SAFE_INTEGER) ||
      left.token.index - right.token.index
    );
}

function attentionMarkerShortLabel(marker: AttentionTokenMarker) {
  return `${marker.riskRank ? `R${marker.riskRank}` : ""}${marker.monitorHit ? "M" : ""}`;
}

function attentionMarkerSuffix(marker: AttentionTokenMarker | undefined) {
  return marker ? `·${attentionMarkerShortLabel(marker)}` : "";
}

function attentionMarkerTitle(
  token: TokenInfo,
  marker: AttentionTokenMarker | undefined,
  axis: "source" | "destination"
) {
  const details = [
    matrixTokenTitle(token, axis),
    marker?.riskRank ? `run-relative safety proxy rank ${marker.riskRank}, score ${token.risk.toFixed(3)}` : "",
    marker?.monitorHit ? "explicit monitor hit" : ""
  ].filter(Boolean);
  return details.join(" · ");
}

function resolveBaselineHeadId(
  heads: AttentionHead[],
  selectedHeadId: string,
  preferredBaselineId?: string
) {
  if (
    preferredBaselineId &&
    preferredBaselineId !== selectedHeadId &&
    heads.some((head) => head.id === preferredBaselineId)
  ) {
    return preferredBaselineId;
  }
  return heads.find((head) => head.id !== selectedHeadId)?.id ?? selectedHeadId;
}

function attentionCellColor(value: number, maximum: number, signed: boolean) {
  const strength = Math.min(1, Math.abs(value) / Math.max(maximum, 1e-12));
  if (!signed) return `rgba(20, 123, 118, ${0.08 + 0.82 * strength})`;
  if (Math.abs(value) < 1e-12) return "#edf3f3";
  return value > 0
    ? `rgba(24, 130, 103, ${0.12 + 0.82 * strength})`
    : `rgba(179, 63, 103, ${0.12 + 0.82 * strength})`;
}

function formatSigned(value: number, digits = 4) {
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}`;
}

function formatEdgeValue(value: number, signed: boolean) {
  return signed
    ? formatMetricDelta(value, "attention_retained_head_difference", "compact")
    : formatMetricNumber(value, "attention_probability", "compact");
}

function isNavigationKey(key: string) {
  return ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(key);
}
