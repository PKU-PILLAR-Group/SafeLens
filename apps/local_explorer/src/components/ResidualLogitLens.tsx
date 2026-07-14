import { useMemo, useRef, useState } from "react";
import { ArrowRight, ScanSearch } from "lucide-react";

import type { LogitLensRow } from "../types";

interface ResidualLogitLensProps {
  rows: LogitLensRow[];
  selectedLayer: number;
  onSelectLayer: (layer: number) => void;
}

type LensDisplay = "logit" | "probability";

export function ResidualLogitLens({
  rows,
  selectedLayer,
  onSelectLayer
}: ResidualLogitLensProps) {
  const [display, setDisplay] = useState<LensDisplay>("logit");
  const displayRef = useRef<HTMLDivElement>(null);
  const layerRailRef = useRef<HTMLDivElement>(null);
  const orderedRows = useMemo(
    () => [...rows].sort((left, right) => left.layer - right.layer),
    [rows]
  );
  const target = orderedRows[0];

  if (!target) {
    return null;
  }

  const selectedRow = orderedRows.find((row) => row.layer === selectedLayer) ?? target;
  const firstRow = orderedRows[0];
  const lastRow = orderedRows[orderedRows.length - 1];
  const bestRank = orderedRows.reduce(
    (best, row) => row.targetRank < best.targetRank ? row : best,
    target
  );
  const scorePoints = orderedRows.map((row) => ({
    layer: row.layer,
    value: display === "logit" ? row.targetLogit : row.targetProbability * 100,
    label: display === "logit" ? row.targetLogit.toFixed(4) : formatProbability(row.targetProbability)
  }));
  const rankPoints = orderedRows.map((row) => ({
    layer: row.layer,
    value: Math.log10(Math.max(1, row.targetRank)),
    label: `#${row.targetRank.toLocaleString()}`
  }));

  function selectDisplay(next: LensDisplay, focus = false) {
    setDisplay(next);
    if (focus) {
      window.requestAnimationFrame(() => {
        displayRef.current?.querySelector<HTMLButtonElement>(`[data-lens-display="${next}"]`)?.focus();
      });
    }
  }

  function selectLayer(position: number) {
    const nextPosition = Math.max(0, Math.min(orderedRows.length - 1, position));
    const next = orderedRows[nextPosition];
    onSelectLayer(next.layer);
    window.requestAnimationFrame(() => {
      layerRailRef.current
        ?.querySelector<HTMLButtonElement>(`[data-lens-layer="${next.layer}"]`)
        ?.focus();
    });
  }

  return (
    <section className="logit-lens" aria-label="Residual logit lens">
      <div className="logit-lens-heading">
        <div>
          <span><ScanSearch size={13} /> vocabulary projection</span>
          <h4>Residual logit lens</h4>
          <p>Each resid_post is passed through the model final norm and unembedding.</p>
        </div>
        <div ref={displayRef} className="toolbar-segment" role="radiogroup" aria-label="Logit lens display">
          <button
            role="radio"
            aria-checked={display === "logit"}
            tabIndex={display === "logit" ? 0 : -1}
            data-lens-display="logit"
            className={display === "logit" ? "active" : ""}
            onClick={() => selectDisplay("logit")}
            onKeyDown={(event) => {
              if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
              event.preventDefault();
              event.stopPropagation();
              selectDisplay(event.key === "Home" || event.key === "ArrowLeft" || event.key === "ArrowUp" ? "logit" : "probability", true);
            }}
          >
            Logit
          </button>
          <button
            role="radio"
            aria-checked={display === "probability"}
            tabIndex={display === "probability" ? 0 : -1}
            data-lens-display="probability"
            className={display === "probability" ? "active" : ""}
            onClick={() => selectDisplay("probability")}
            onKeyDown={(event) => {
              if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) return;
              event.preventDefault();
              event.stopPropagation();
              selectDisplay(event.key === "End" || event.key === "ArrowRight" || event.key === "ArrowDown" ? "probability" : "logit", true);
            }}
          >
            Probability
          </button>
        </div>
      </div>

      <div className="lens-target">
        <span>Observed next token</span>
        <strong>{target.targetTokenText || "␠"}</strong>
        <i>id {target.targetTokenId}</i>
      </div>

      <section className="lens-trajectory" aria-labelledby="lens-trajectory-title">
        <div className="lens-trajectory-heading">
          <div>
            <h5 id="lens-trajectory-title">Target trajectory</h5>
            <p>Cached layers for source token {target.tokenIndex}</p>
          </div>
          <div className="lens-trajectory-summary">
            <span>
              <small>{display === "logit" ? "logit delta" : "probability delta"}</small>
              <b>{formatScoreDelta(firstRow, lastRow, display)}</b>
            </span>
            <span>
              <small>rank path</small>
              <b>#{firstRow.targetRank.toLocaleString()} → #{lastRow.targetRank.toLocaleString()}</b>
            </span>
            <span><small>best rank</small><b>L{bestRank.layer} · #{bestRank.targetRank.toLocaleString()}</b></span>
          </div>
        </div>

        <div className="lens-trajectory-plots">
          <TrajectoryPlot
            label={`Target ${display} by layer`}
            title={display === "logit" ? "Target logit" : "Target probability"}
            points={scorePoints}
            selectedLayer={selectedLayer}
            tone="score"
            unit={display === "probability" ? "%" : ""}
          />
          <TrajectoryPlot
            label="Observed target vocabulary rank by layer, logarithmic display"
            title="Target rank · log display"
            points={rankPoints}
            selectedLayer={selectedLayer}
            tone="rank"
            lowerIsBetter
          />
        </div>

        <div
          ref={layerRailRef}
          className="lens-trajectory-layers"
          role="radiogroup"
          aria-label="Logit lens trajectory layer"
        >
          {orderedRows.map((row, position) => {
            const selected = row.layer === selectedRow.layer;
            return (
              <button
                key={row.layer}
                type="button"
                role="radio"
                aria-checked={selected}
                aria-label={`Layer ${row.layer}, target logit ${row.targetLogit.toFixed(4)}, probability ${formatProbability(row.targetProbability)}, rank ${row.targetRank}`}
                data-lens-layer={row.layer}
                tabIndex={selected ? 0 : -1}
                className={selected ? "active" : ""}
                onClick={() => onSelectLayer(row.layer)}
                onKeyDown={(event) => {
                  let nextPosition = position;
                  if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextPosition -= 1;
                  else if (event.key === "ArrowRight" || event.key === "ArrowDown") nextPosition += 1;
                  else if (event.key === "Home") nextPosition = 0;
                  else if (event.key === "End") nextPosition = orderedRows.length - 1;
                  else return;
                  event.preventDefault();
                  event.stopPropagation();
                  selectLayer(nextPosition);
                }}
              >
                L{row.layer}
              </button>
            );
          })}
        </div>
      </section>

      <div className="lens-layer-list">
        {orderedRows.map((row, index) => {
          const previous = orderedRows[index - 1];
          const changed =
            previous !== undefined &&
            previous.topPredictions[0]?.tokenId !== row.topPredictions[0]?.tokenId;
          const maximum = Math.max(
            1e-12,
            ...row.topPredictions.map((prediction) =>
              display === "logit" ? Math.abs(prediction.logit) : prediction.probability
            )
          );
          return (
            <article
              key={row.layer}
              className={`lens-layer ${selectedLayer === row.layer ? "selected" : ""}`}
            >
              <button className="lens-layer-select" onClick={() => onSelectLayer(row.layer)}>
                <span>L{row.layer}</span>
                <b>target rank #{row.targetRank.toLocaleString()}</b>
                <i>
                  {display === "logit"
                    ? `target logit ${row.targetLogit.toFixed(4)}`
                    : `target p ${formatProbability(row.targetProbability)}`}
                </i>
              </button>

              <div className="lens-predictions">
                {row.topPredictions.map((prediction, rank) => {
                  const value = display === "logit" ? prediction.logit : prediction.probability;
                  const width = Math.max(4, (Math.abs(value) / maximum) * 100);
                  const isTarget = prediction.tokenId === row.targetTokenId;
                  return (
                    <div
                      key={`${prediction.tokenId}-${rank}`}
                      className={`lens-prediction ${isTarget ? "target" : ""}`}
                      title={`token id ${prediction.tokenId} · logit ${prediction.logit.toFixed(6)} · probability ${prediction.probability.toExponential(3)}`}
                    >
                      <span>{rank + 1}</span>
                      <strong>{prediction.tokenText || "␠"}</strong>
                      <i>{display === "logit" ? prediction.logit.toFixed(4) : formatProbability(prediction.probability)}</i>
                      <em style={{ width: `${width}%` }} />
                    </div>
                  );
                })}
              </div>

              <div className="lens-transition">
                {index === 0 ? (
                  <span>first cached layer</span>
                ) : (
                  <span className={changed ? "changed" : "stable"}>
                    {changed ? "top prediction changed" : "top prediction stable"}
                  </span>
                )}
                <b>{row.sourceKey}</b>
              </div>
            </article>
          );
        })}
      </div>

      <div className="lens-provenance">
        <ArrowRight size={13} />
        <span><b>raw model evidence</b> resid_post → final norm → vocabulary logits</span>
        <p>Logit-lens predictions are diagnostic projections, not causal contributions.</p>
      </div>
    </section>
  );
}

function TrajectoryPlot({
  label,
  title,
  points,
  selectedLayer,
  tone,
  lowerIsBetter = false,
  unit = ""
}: {
  label: string;
  title: string;
  points: Array<{ layer: number; value: number; label: string }>;
  selectedLayer: number;
  tone: "score" | "rank";
  lowerIsBetter?: boolean;
  unit?: string;
}) {
  const coordinates = trajectoryCoordinates(points, lowerIsBetter);
  const selected = points.find((point) => point.layer === selectedLayer) ?? points[0];
  const selectedPoint = coordinates.find((point) => point.layer === selected.layer) ?? coordinates[0];
  const values = points.map((point) => point.value);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  return (
    <figure className={`lens-trajectory-plot ${tone}`}>
      <figcaption><span>{title}</span><b>{selected.label}</b></figcaption>
      <svg viewBox="0 0 260 84" preserveAspectRatio="none" role="img" aria-label={label}>
        <line x1="12" y1="14" x2="248" y2="14" />
        <line x1="12" y1="42" x2="248" y2="42" />
        <line x1="12" y1="70" x2="248" y2="70" />
        {selectedPoint && <line className="lens-trajectory-marker" x1={selectedPoint.x} y1="10" x2={selectedPoint.x} y2="74" />}
        <path d={trajectoryPath(coordinates)} />
        {coordinates.map((point) => (
          <circle
            key={point.layer}
            cx={point.x}
            cy={point.y}
            r={point.layer === selected.layer ? 4.2 : 2.8}
            className={point.layer === selected.layer ? "selected" : ""}
          >
            <title>{`Layer ${point.layer}: ${points.find((item) => item.layer === point.layer)?.label}`}</title>
          </circle>
        ))}
      </svg>
      <div>
        <span>{formatPlotBound(minimum, tone, maximum - minimum)}{unit}</span>
        <span>{tone === "rank" ? "lower is better" : "higher plotted upward"}</span>
        <span>{formatPlotBound(maximum, tone, maximum - minimum)}{unit}</span>
      </div>
    </figure>
  );
}

function trajectoryCoordinates(
  points: Array<{ layer: number; value: number }>,
  lowerIsBetter: boolean
) {
  const values = points.map((point) => point.value);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const span = Math.max(1e-12, maximum - minimum);
  return points.map((point, index) => {
    const normalized = (point.value - minimum) / span;
    const vertical = lowerIsBetter ? normalized : 1 - normalized;
    return {
      layer: point.layer,
      x: points.length === 1 ? 130 : 12 + index / (points.length - 1) * 236,
      y: maximum === minimum ? 42 : 14 + vertical * 56
    };
  });
}

function trajectoryPath(points: Array<{ x: number; y: number }>) {
  return points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" ");
}

function formatPlotBound(value: number, tone: "score" | "rank", span: number) {
  if (tone === "rank") return `#${Math.round(10 ** value).toLocaleString()}`;
  if (value !== 0 && Math.abs(value) < 0.0001) return value.toExponential(2);
  const precision = span > 0 && span < 0.001
    ? Math.min(8, Math.max(4, Math.ceil(-Math.log10(span)) + 1))
    : 4;
  return value.toFixed(precision);
}

function formatScoreDelta(first: LogitLensRow, last: LogitLensRow, display: LensDisplay) {
  const delta = display === "logit"
    ? last.targetLogit - first.targetLogit
    : (last.targetProbability - first.targetProbability) * 100;
  const formatted = display === "logit" && delta !== 0 && Math.abs(delta) < 0.0001
    ? delta.toExponential(2)
    : delta.toFixed(display === "logit" ? 4 : 2);
  return `${delta > 0 ? "+" : ""}${formatted}${display === "probability" ? " pp" : ""}`;
}

function formatProbability(value: number) {
  if (value < 0.001) {
    return value.toExponential(2);
  }
  return `${(value * 100).toFixed(2)}%`;
}
