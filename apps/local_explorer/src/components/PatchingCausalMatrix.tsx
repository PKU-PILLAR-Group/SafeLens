import { useEffect, useRef, useState, type CSSProperties } from "react";
import { FlaskConical, Pin } from "lucide-react";

import { MatrixViewportControls, useMatrixViewport } from "./MatrixViewportControls";
import { MatrixComparisonSummary } from "./MatrixComparisonSummary";
import { MatrixRangeSummary } from "./MatrixRangeSummary";
import { useMatrixRangeBrush } from "./useMatrixRangeBrush";
import { formatMetricDelta, formatMetricNumber, type MetricFormatMode } from "../metricFormatting";
import type { PatchingExperiment, TokenInfo } from "../types";

export type PatchingMetric = "recovery" | "effect" | "score";

interface PatchingCausalMatrixProps {
  experiment: PatchingExperiment;
  tokens: TokenInfo[];
  selectedLayer: number;
  selectedToken: number;
  metric: PatchingMetric;
  selectedRange?: [number, number];
  onMetricChange: (metric: PatchingMetric) => void;
  onSelectCell: (layer: number, token: number) => void;
  onRangeSelect: (range?: [number, number]) => void;
  onPin: () => void;
  onPinCell: (layer: number, token: number) => void;
}

export function PatchingCausalMatrix({
  experiment,
  tokens,
  selectedLayer,
  selectedToken,
  metric,
  selectedRange,
  onMetricChange,
  onSelectCell,
  onRangeSelect,
  onPin,
  onPinCell
}: PatchingCausalMatrixProps) {
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const [comparisonKey, setComparisonKey] = useState<string | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const viewport = useMatrixViewport({
    initialSize: 52,
    minimumSize: 32,
    maximumSize: 64,
    itemCount: tokens.length,
    labelWidth: 54,
    gap: 1,
    sessionKey: "patching"
  });
  const rangeBrush = useMatrixRangeBrush({
    enabled: viewport.mode === "select",
    selectedRange,
    onRangeSelect
  });
  const values = experiment.cells.flatMap((cell) => {
    const value = metricValue(cell, metric);
    return value === null ? [] : [value];
  });
  const maxAbsolute = Math.max(1e-12, ...values.map((value) => Math.abs(value)));
  const byCell = new Map(experiment.cells.map((cell) => [`${cell.layer}:${cell.tokenIndex}`, cell]));
  const selectedKey = `${selectedLayer}:${selectedToken}`;
  const keyboardLayer = byCell.has(selectedKey) ? selectedLayer : experiment.layers[0];
  const keyboardToken = byCell.has(selectedKey) ? selectedToken : experiment.positions[0];
  const detailKey = hoveredKey ?? (byCell.has(selectedKey) ? selectedKey : null);
  const detailCell = detailKey ? byCell.get(detailKey) : undefined;
  const comparisonCell = comparisonKey ? byCell.get(comparisonKey) : undefined;
  const selectedCell = byCell.get(selectedKey);
  const selectedMetricValue = selectedCell ? metricValue(selectedCell, metric) : null;
  const comparisonMetricValue = comparisonCell ? metricValue(comparisonCell, metric) : null;
  const gridRowStyle = {
    gridTemplateColumns: `54px repeat(${tokens.length}, ${viewport.size}px)`
  };

  useEffect(() => {
    setComparisonKey(null);
  }, [experiment]);

  function moveCellFocus(layer: number, token: number, key: string) {
    const layerPosition = Math.max(0, experiment.layers.indexOf(layer));
    const tokenPosition = Math.max(0, experiment.positions.indexOf(token));
    let nextLayer = layerPosition;
    let nextToken = tokenPosition;
    if (key === "ArrowLeft") nextToken = Math.max(0, tokenPosition - 1);
    if (key === "ArrowRight") nextToken = Math.min(experiment.positions.length - 1, tokenPosition + 1);
    if (key === "ArrowUp") nextLayer = Math.max(0, layerPosition - 1);
    if (key === "ArrowDown") nextLayer = Math.min(experiment.layers.length - 1, layerPosition + 1);
    if (key === "Home") nextToken = 0;
    if (key === "End") nextToken = experiment.positions.length - 1;
    const nextLayerValue = experiment.layers[nextLayer];
    const nextTokenValue = experiment.positions[nextToken];
    if (nextLayerValue === undefined || nextTokenValue === undefined) return;
    onSelectCell(nextLayerValue, nextTokenValue);
    window.requestAnimationFrame(() => {
      gridRef.current
        ?.querySelector<HTMLButtonElement>(
          `[data-layer="${nextLayerValue}"][data-token="${nextTokenValue}"]`
        )
        ?.focus();
    });
  }

  return (
    <section className="surface patching-matrix">
      <div className="surface-header patching-matrix-header">
        <div>
          <h3>Activation patching causal grid</h3>
          <p>{experiment.component === "z" ? `attention head · L${experiment.layers[0]}H${experiment.head}` : experiment.component} · target {visibleToken(experiment.targetTokenText)} ({experiment.targetTokenId})</p>
        </div>
        <span className="evidence-kind"><FlaskConical size={13} /> causal evidence</span>
      </div>
      <div className="patching-baselines">
        <span><b>{experiment.cleanScore.toFixed(4)}</b>clean logit</span>
        <span><b>{experiment.corruptedScore.toFixed(4)}</b>corrupted logit</span>
        <span><b>{experiment.denominator.toFixed(4)}</b>recovery denominator</span>
        <span><b>{experiment.cells.length}</b>causal runs</span>
      </div>
      <MatrixComparisonSummary
        label="Patching matrix"
        primary={`L${selectedLayer} · T${selectedToken}`}
        anchor={comparisonCell ? `L${comparisonCell.layer} · T${comparisonCell.tokenIndex}` : undefined}
        delta={selectedMetricValue === null || comparisonMetricValue === null
          ? undefined
          : formatSignedMetricDelta(selectedMetricValue - comparisonMetricValue, metric)}
        deltaLabel={`${metricLabel(metric)} delta`}
        onClear={() => setComparisonKey(null)}
      />
      <MatrixRangeSummary label="Token" range={selectedRange} onClear={() => onRangeSelect(undefined)} />
      <div className="patching-matrix-toolbar" aria-label="Patching matrix controls">
        <div className="patching-metric-tabs" role="group" aria-label="Patching matrix metric">
          <button className={metric === "recovery" ? "active" : ""} aria-pressed={metric === "recovery"} onClick={() => onMetricChange("recovery")}>Recovery %</button>
          <button className={metric === "effect" ? "active" : ""} aria-pressed={metric === "effect"} onClick={() => onMetricChange("effect")}>Causal effect</button>
          <button className={metric === "score" ? "active" : ""} aria-pressed={metric === "score"} onClick={() => onMetricChange("score")}>Patched logit</button>
        </div>
        <div className="toolbar-actions">
          <MatrixViewportControls viewport={viewport} label="patching matrix" />
          <button aria-label="Pin selected patching cell" title="Pin selected cell" onClick={onPin}>
            <Pin size={14} />
          </button>
        </div>
      </div>
      <div
        ref={viewport.scrollRef}
        className={`patching-grid-scroll ${viewport.mode === "pan" ? "pan-mode" : ""}`}
        {...viewport.viewportProps}
      >
        <div
          ref={gridRef}
          className={`patching-grid ${viewport.axesPinned ? "axes-pinned" : ""}`}
          role="grid"
          aria-label="Layer by token activation patching matrix"
          style={{
            "--patching-cell-size": `${viewport.size}px`
          } as CSSProperties}
          {...rangeBrush.gridProps}
        >
          <div className="patching-grid-row patching-grid-header-row" role="row" style={gridRowStyle}>
            <span className="patching-grid-corner" role="columnheader">L / T</span>
            {tokens.map((token) => (
              <span
                key={`header-${token.index}`}
                role="columnheader"
                className={`${experiment.positions.includes(token.index) ? "computed" : ""} ${rangeBrush.inRange(token.index) ? "in-range" : ""}`}
                data-range-token={token.index}
              >
                <b>{token.index}</b><i>{token.text || "␠"}</i>
              </span>
            ))}
          </div>
          {experiment.layers.map((layer) => (
            <div key={`layer-${layer}`} className="patching-grid-row" role="row" style={gridRowStyle}>
              <strong role="rowheader">L{layer}</strong>
              {tokens.map((token) => {
              const cell = byCell.get(`${layer}:${token.index}`);
              const value = cell ? metricValue(cell, metric) : null;
              const selected = layer === selectedLayer && token.index === selectedToken;
              const comparison = comparisonKey === `${layer}:${token.index}`;
              return (
                <button
                  key={`${layer}:${token.index}`}
                  role="gridcell"
                  className={`${selected ? "selected" : ""} ${comparison ? "comparison" : ""} ${cell ? "computed" : "empty"} ${rangeBrush.inRange(token.index) ? "in-range" : ""}`}
                  disabled={!cell}
                  data-layer={layer}
                  data-token={token.index}
                  data-range-token={token.index}
                  aria-label={cell ? `Layer ${layer}, token ${token.index}, ${metricLabel(metric)} ${formatValue(value, metric)}` : `Layer ${layer}, token ${token.index}, not computed`}
                  aria-current={selected ? "true" : undefined}
                  aria-keyshortcuts={cell ? "ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter Space" : undefined}
                  tabIndex={cell && layer === keyboardLayer && token.index === keyboardToken ? 0 : -1}
                  title={cell ? `${cell.sourceKey}\n${metricLabel(metric)}: ${formatValue(value, metric)}` : "Not included in this patch grid"}
                  style={cell && value !== null ? cellColor(value, maxAbsolute, metric) : undefined}
                  onClick={(event) => {
                    if (!cell) return;
                    if (event.shiftKey) {
                      setComparisonKey(`${layer}:${token.index}`);
                    } else if (event.metaKey || event.ctrlKey) {
                      onPinCell(layer, token.index);
                    } else {
                      onSelectCell(layer, token.index);
                    }
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && event.shiftKey) {
                      event.preventDefault();
                      event.stopPropagation();
                      setComparisonKey(`${layer}:${token.index}`);
                    } else if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                      event.preventDefault();
                      event.stopPropagation();
                      onPinCell(layer, token.index);
                    } else if (isNavigationKey(event.key)) {
                      event.preventDefault();
                      event.stopPropagation();
                      moveCellFocus(layer, token.index, event.key);
                    } else if (event.key === " ") {
                      event.preventDefault();
                      event.stopPropagation();
                      onPin();
                    }
                  }}
                  onMouseEnter={() => setHoveredKey(cell ? `${layer}:${token.index}` : null)}
                  onMouseLeave={() => setHoveredKey(null)}
                  onFocus={() => setHoveredKey(cell ? `${layer}:${token.index}` : null)}
                  onBlur={() => setHoveredKey(null)}
                >{cell ? formatValue(value, metric) : "·"}</button>
              );
              })}
            </div>
          ))}
        </div>
      </div>
      <PatchingCellDetails
        cell={detailCell}
        token={detailCell ? tokens.find((token) => token.index === detailCell.tokenIndex) : undefined}
        metric={metric}
      />
      <div className="patching-matrix-legend" aria-label="Patching matrix legend">
        <span><i className="patching-legend-negative" />negative</span>
        <span><i className="patching-legend-zero" />zero</span>
        <span><i className="patching-legend-positive" />positive</span>
        <span><i className="patching-legend-missing" />not computed</span>
        <b>diverging scale · ±{formatValue(maxAbsolute, metric)}</b>
      </div>
      <div className="patching-matrix-note">
        <FlaskConical size={15} />
        <span>Each cell is a separate forward pass replacing one corrupted activation with its clean counterpart.</span>
      </div>
    </section>
  );
}

function PatchingCellDetails({
  cell,
  token,
  metric
}: {
  cell?: PatchingExperiment["cells"][number];
  token?: TokenInfo;
  metric: PatchingMetric;
}) {
  if (!cell) {
    return <div className="patching-cell-details empty">Causal cell details · no computed cell focused.</div>;
  }
  return (
    <div className="patching-cell-details" aria-live="polite">
      <span><b>L{cell.layer}</b>layer</span>
      <span><b>{visibleToken(token?.text ?? "")}</b>token {cell.tokenIndex}</span>
      <span><b>{formatValue(metricValue(cell, metric), metric, "exact")}</b>{metricLabel(metric)}</span>
      <span><b>causal</b>evidence class</span>
      <span className="patching-detail-source"><b>{cell.sourceKey}</b>cache key</span>
    </div>
  );
}

function metricValue(cell: PatchingExperiment["cells"][number], metric: PatchingMetric) {
  if (metric === "recovery") return cell.recoveryPercentage;
  if (metric === "effect") return cell.causalEffect;
  return cell.patchedScore;
}

function metricLabel(metric: PatchingMetric) {
  if (metric === "recovery") return "recovery";
  if (metric === "effect") return "causal effect";
  return "patched logit";
}

function formatValue(value: number | null, metric: PatchingMetric, mode: MetricFormatMode = "compact") {
  const formatted = formatMetricNumber(value, `patching_${metric}`, mode);
  return metric === "recovery" && formatted !== "n/a" ? `${formatted}%` : formatted;
}

function formatSignedMetricDelta(value: number, metric: PatchingMetric) {
  const formatted = formatMetricDelta(value, `patching_${metric}`, "compact");
  return metric === "recovery" ? `${formatted}%` : formatted;
}

function cellColor(value: number, maxAbsolute: number, metric: PatchingMetric) {
  const normalized = Math.min(1, Math.abs(value) / maxAbsolute);
  const alpha = 0.12 + normalized * 0.68;
  const positive = metric === "score" ? value >= 0 : value > 0;
  return {
    backgroundColor: positive ? `rgba(20, 126, 113, ${alpha})` : `rgba(190, 58, 75, ${alpha})`,
    color: normalized > 0.56 ? "#fff" : "var(--text-primary)"
  };
}

function visibleToken(value: string) {
  return value || "␠";
}

function isNavigationKey(key: string) {
  return ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(key);
}
