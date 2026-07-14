import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Check, Pin, Search, X } from "lucide-react";

import { MatrixViewportControls, useMatrixViewport } from "./MatrixViewportControls";
import {
  SPECIALIZED_CANVAS_CELL_THRESHOLD,
  SpecializedMatrixCanvas
} from "./SpecializedMatrixCanvas";
import { MatrixTokenDetail, matrixTokenTitle } from "./MatrixTokenDetail";
import { MatrixComparisonSummary } from "./MatrixComparisonSummary";
import { MatrixRangeSummary } from "./MatrixRangeSummary";
import {
  positionRangeToTokens,
  tokenRangeToPositions,
  useMatrixRangeBrush
} from "./useMatrixRangeBrush";
import { formatMetricDelta, formatMetricNumber, type MetricFormatMode } from "../metricFormatting";
import type { NLACompatibility, NLARow, TokenInfo } from "../types";

type FidelityMetric = "cosine" | "mse" | "fve";
type ReviewMode = "all" | "low_fidelity" | "norm_outlier";

interface NLAFidelityMatrixProps {
  rows: NLARow[];
  compatibility: NLACompatibility;
  layers: number[];
  tokens: TokenInfo[];
  selectedToken: number;
  selectedLayer: number;
  selectedComponent: NLARow["component"];
  metric: FidelityMetric;
  selectedRange?: [number, number];
  onMetricChange: (metric: FidelityMetric) => void;
  onSelectCell: (layer: number, token: number, component: NLARow["component"]) => void;
  onRangeSelect: (range?: [number, number]) => void;
  onHoverToken: (token: number | null) => void;
  onPin?: () => void;
  onPinCell: (layer: number, token: number, component: NLARow["component"]) => void;
}

interface MatrixRow {
  layer: number;
  component: NLARow["component"];
}

export function NLAFidelityMatrix({
  rows,
  compatibility,
  layers,
  tokens,
  selectedToken,
  selectedLayer,
  selectedComponent,
  metric,
  selectedRange,
  onMetricChange,
  onSelectCell,
  onRangeSelect,
  onHoverToken,
  onPin,
  onPinCell
}: NLAFidelityMatrixProps) {
  const [componentFilter, setComponentFilter] = useState("all");
  const [threshold, setThreshold] = useState(0.8);
  const [query, setQuery] = useState("");
  const [reviewMode, setReviewMode] = useState<ReviewMode>("all");
  const [hovered, setHovered] = useState<NLARow | null>(null);
  const [comparisonCell, setComparisonCell] = useState<{ rowIndex: number; tokenIndex: number } | null>(null);
  const [keyboardRowIndex, setKeyboardRowIndex] = useState(0);
  const [pendingFocus, setPendingFocus] = useState<{ rowIndex: number; token: number } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const reviewModeRef = useRef<HTMLDivElement>(null);
  const viewport = useMatrixViewport({
    initialSize: 24,
    minimumSize: 14,
    maximumSize: 38,
    itemCount: tokens.length,
    labelWidth: 96,
    sessionKey: "nla"
  });
  const rangeBrush = useMatrixRangeBrush({
    enabled: viewport.mode === "select",
    selectedRange,
    onRangeSelect
  });
  const components = useMemo(
    () => unique(rows.map((row) => row.component)),
    [rows]
  );
  const matrixRows: MatrixRow[] = useMemo(
    () => layers.flatMap((layer) =>
      (componentFilter === "all" ? components : [componentFilter as NLARow["component"]]).map(
        (rowComponent) => ({ layer, component: rowComponent })
      )
    ),
    [componentFilter, components, layers]
  );
  const rowLookup = useMemo(
    () => new Map(rows.map((row) => [`${row.layer}:${row.component}:${row.tokenIndex}`, row])),
    [rows]
  );
  const availableRows = useMemo(
    () => rows.filter((row) => row.status !== "unavailable"),
    [rows]
  );
  const normOutlierKeys = useMemo(() => activationNormOutlierKeys(availableRows), [availableRows]);
  const lowFidelityRows = useMemo(
    () => availableRows.filter((row) =>
      fidelityValue(row, metric) !== undefined && !passesFidelityThreshold(row, metric, threshold)
    ),
    [availableRows, metric, threshold]
  );
  const worstFidelityRow = useMemo(
    () => [...lowFidelityRows].sort((left, right) =>
      metric === "mse"
        ? (fidelityValue(right, metric) ?? -Infinity) - (fidelityValue(left, metric) ?? -Infinity)
        : (fidelityValue(left, metric) ?? Infinity) - (fidelityValue(right, metric) ?? Infinity)
    )[0],
    [lowFidelityRows, metric]
  );
  const largestNormOutlier = useMemo(
    () => [...availableRows]
      .filter((row) => normOutlierKeys.has(nlaRowKey(row)))
      .sort((left, right) => right.activationNorm - left.activationNorm)[0],
    [availableRows, normOutlierKeys]
  );
  const searchCandidates = rows.filter((row) => {
    const normalized = query.trim().toLowerCase();
    return normalized.length === 0 ||
      row.token?.toLowerCase().includes(normalized) ||
      row.explanation.toLowerCase().includes(normalized) ||
      row.component.toLowerCase().includes(normalized);
  });
  const visibleCandidates = searchCandidates.filter((row) => {
    if (reviewMode === "low_fidelity") return lowFidelityRows.includes(row);
    if (reviewMode === "norm_outlier") return normOutlierKeys.has(nlaRowKey(row));
    return true;
  });
  const compatibleProfiles = compatibility.profiles.filter(
    (profile) => profile.status === "compatible"
  ).length;
  const expectedCells = matrixRows.length * tokens.length;
  const coveredCells = matrixRows.reduce(
    (count, matrixRow) =>
      count + rows.filter(
        (row) => row.layer === matrixRow.layer && row.component === matrixRow.component
      ).length,
    0
  );
  const selectedLayerRow = matrixRows.findIndex(
    (matrixRow) => matrixRow.layer === selectedLayer && matrixRow.component === selectedComponent
  );
  const fallbackLayerRow = matrixRows.findIndex((matrixRow) => matrixRow.layer === selectedLayer);
  const recommendedKeyboardRow = Math.max(0, selectedLayerRow >= 0 ? selectedLayerRow : fallbackLayerRow);
  const selectedTokenPosition = Math.max(0, tokens.findIndex((token) => token.index === selectedToken));
  const selectedExactRow = rowLookup.get(
    `${selectedLayer}:${selectedComponent}:${selectedToken}`
  );
  const comparisonMatrixRow = comparisonCell ? matrixRows[comparisonCell.rowIndex] : undefined;
  const comparisonExactRow = comparisonCell && comparisonMatrixRow
    ? rowLookup.get(`${comparisonMatrixRow.layer}:${comparisonMatrixRow.component}:${comparisonCell.tokenIndex}`)
    : undefined;
  const selectedMetricValue = selectedExactRow ? fidelityValue(selectedExactRow, metric) : undefined;
  const comparisonMetricValue = comparisonExactRow ? fidelityValue(comparisonExactRow, metric) : undefined;
  const renderMode = matrixRows.length * tokens.length >= SPECIALIZED_CANVAS_CELL_THRESHOLD
    ? "canvas"
    : "dom";

  useEffect(() => {
    setComparisonCell(null);
  }, [matrixRows, rows, tokens]);

  useEffect(() => {
    setKeyboardRowIndex(recommendedKeyboardRow);
  }, [recommendedKeyboardRow, selectedComponent, selectedLayer, componentFilter]);

  useEffect(() => {
    if (!pendingFocus) return;
    const matrixRow = matrixRows[pendingFocus.rowIndex];
    if (
      !matrixRow ||
      selectedLayer !== matrixRow.layer ||
      selectedComponent !== matrixRow.component ||
      selectedToken !== pendingFocus.token
    ) {
      return;
    }
    const frame = window.requestAnimationFrame(() => {
      gridRef.current
        ?.querySelector<HTMLButtonElement>(
          `[data-row-index="${pendingFocus.rowIndex}"][data-token="${pendingFocus.token}"]`
        )
        ?.focus();
      setPendingFocus(null);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [matrixRows, pendingFocus, selectedComponent, selectedLayer, selectedToken]);

  function moveFidelityFocus(rowIndex: number, tokenIndex: number, key: string) {
    const tokenPosition = Math.max(0, tokens.findIndex((token) => token.index === tokenIndex));
    let nextRow = rowIndex;
    let nextToken = tokenPosition;
    if (key === "ArrowLeft") nextToken = Math.max(0, tokenPosition - 1);
    if (key === "ArrowRight") nextToken = Math.min(tokens.length - 1, tokenPosition + 1);
    if (key === "ArrowUp") nextRow = Math.max(0, rowIndex - 1);
    if (key === "ArrowDown") nextRow = Math.min(matrixRows.length - 1, rowIndex + 1);
    if (key === "Home") nextToken = 0;
    if (key === "End") nextToken = tokens.length - 1;
    const matrixRow = matrixRows[nextRow];
    const token = tokens[nextToken]?.index;
    if (!matrixRow || token === undefined) return;
    setKeyboardRowIndex(nextRow);
    setPendingFocus({ rowIndex: nextRow, token });
    onSelectCell(matrixRow.layer, token, matrixRow.component);
  }

  function changeMetric(nextMetric: FidelityMetric) {
    onMetricChange(nextMetric);
    setThreshold(nextMetric === "mse" ? 0.2 : 0.8);
  }

  function selectReviewMode(position: number) {
    const options: ReviewMode[] = ["all", "low_fidelity", "norm_outlier"];
    const nextPosition = Math.max(0, Math.min(options.length - 1, position));
    setReviewMode(options[nextPosition]);
    window.requestAnimationFrame(() => {
      reviewModeRef.current
        ?.querySelector<HTMLButtonElement>(`[data-review-position="${nextPosition}"]`)
        ?.focus();
    });
  }

  return (
    <section className="surface nla-fidelity-section">
      <div className="surface-header">
        <div>
          <h3>NLA fidelity coverage</h3>
          <p>Exact Layer × Token × Component artifact coverage; no nearest-row substitution.</p>
        </div>
        <span className="evidence-kind">safety method</span>
      </div>

      <div className="nla-fidelity-toolbar" aria-label="NLA fidelity controls">
        <label>
          <span>Metric</span>
          <select value={metric} onChange={(event) => changeMetric(event.target.value as FidelityMetric)}>
            <option value="cosine">Cosine fidelity</option>
            <option value="mse">Reconstruction MSE</option>
            <option value="fve">Fraction variance explained</option>
          </select>
        </label>
        <label>
          <span>Component</span>
          <select value={componentFilter} onChange={(event) => setComponentFilter(event.target.value)}>
            <option value="all">All cached components</option>
            {components.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label className="nla-threshold-control">
          <span>{metric === "mse" ? "Maximum MSE" : "Minimum fidelity"} <b>{threshold.toFixed(2)}</b></span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={threshold}
            onChange={(event) => setThreshold(Number(event.target.value))}
          />
        </label>
        <label className="nla-search-control">
          <span><Search size={12} /> Explanation search</span>
          <input
            value={query}
            placeholder="token, component, explanation"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <div className="nla-viewport-actions toolbar-actions">
          <MatrixViewportControls viewport={viewport} label="NLA matrix" />
          {onPin && (
            <button
              type="button"
              aria-label="Pin selected NLA evidence"
              title="Pin selected NLA evidence"
              onClick={onPin}
            >
              <Pin size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="nla-coverage-summary" aria-label="NLA coverage summary">
        <span><b>{availableRows.length}</b>available fidelity rows</span>
        <span><b>{coveredCells}/{expectedCells}</b>candidate coverage</span>
        <span><b>{compatibleProfiles}/{compatibility.profiles.length}</b>compatible profiles</span>
        <span><b>{compatibility.dModel}</b>run d_model</span>
      </div>
      <MatrixComparisonSummary
        label="NLA matrix"
        primary={`L${selectedLayer} ${shortComponent(selectedComponent)} · T${selectedToken}`}
        anchor={comparisonCell && comparisonMatrixRow
          ? `L${comparisonMatrixRow.layer} ${shortComponent(comparisonMatrixRow.component)} · T${comparisonCell.tokenIndex}`
          : undefined}
        delta={selectedMetricValue === undefined || comparisonMetricValue === undefined
          ? undefined
          : formatFidelityDelta(selectedMetricValue - comparisonMetricValue, metric)}
        deltaLabel={`${metric} delta`}
        onClear={() => setComparisonCell(null)}
      />
      <MatrixRangeSummary label="Token" range={selectedRange} onClear={() => onRangeSelect(undefined)} />

      <section className="nla-review-queue" aria-labelledby="nla-review-title">
        <header>
          <div>
            <h4 id="nla-review-title">NLA review queue</h4>
            <p>Threshold failures and run-relative activation norm outliers remain separate signals.</p>
          </div>
          <span>{lowFidelityRows.length} low fidelity · {normOutlierKeys.size} norm outliers</span>
        </header>
        <div className="nla-review-actions">
          <button
            type="button"
            disabled={!worstFidelityRow}
            onClick={() => worstFidelityRow && onSelectCell(worstFidelityRow.layer, worstFidelityRow.tokenIndex, worstFidelityRow.component)}
          >
            <AlertTriangle size={14} />
            <span>
              <b>{worstFidelityRow ? `${worstFidelityRow.token || `T${worstFidelityRow.tokenIndex}`} · ${metricValue(worstFidelityRow, metric)}` : "No threshold failures"}</b>
              review lowest fidelity
            </span>
          </button>
          <button
            type="button"
            disabled={!largestNormOutlier}
            onClick={() => largestNormOutlier && onSelectCell(largestNormOutlier.layer, largestNormOutlier.tokenIndex, largestNormOutlier.component)}
          >
            <Search size={14} />
            <span>
              <b>{largestNormOutlier ? `${largestNormOutlier.token || `T${largestNormOutlier.tokenIndex}`} · ${largestNormOutlier.activationNorm.toFixed(3)}` : "No norm outliers"}</b>
              review activation norm outlier
            </span>
          </button>
        </div>
        <div
          ref={reviewModeRef}
          className="toolbar-segment nla-review-mode"
          role="radiogroup"
          aria-label="NLA candidate review filter"
        >
          {([
            ["all", "All"],
            ["low_fidelity", `Low fidelity (${lowFidelityRows.length})`],
            ["norm_outlier", `Norm outlier (${normOutlierKeys.size})`]
          ] as Array<[ReviewMode, string]>).map(([option, label], position) => (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={reviewMode === option}
              className={reviewMode === option ? "active" : ""}
              data-review-position={position}
              tabIndex={reviewMode === option ? 0 : -1}
              onClick={() => selectReviewMode(position)}
              onKeyDown={(event) => {
                let nextPosition = position;
                if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextPosition -= 1;
                else if (event.key === "ArrowRight" || event.key === "ArrowDown") nextPosition += 1;
                else if (event.key === "Home") nextPosition = 0;
                else if (event.key === "End") nextPosition = 2;
                else return;
                event.preventDefault();
                selectReviewMode(nextPosition);
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      <div className="nla-compatibility-banner">
        <AlertTriangle size={17} />
        <div>
          <strong>
            {availableRows.length > 0
              ? `${availableRows.length} exact NLA rows loaded`
              : "No compatible NLA result artifact is loaded"}
          </strong>
          <p>
            Run model: {compatibility.modelName} · d_model {compatibility.dModel} · cached layers {compatibility.availableLayers.map((layer) => `L${layer}`).join(", ")}
          </p>
        </div>
      </div>

      <div
        ref={viewport.scrollRef}
        className={`nla-matrix-scroll ${renderMode === "canvas" ? "specialized-canvas-mode" : ""} ${viewport.mode === "pan" ? "pan-mode" : ""}`}
        {...viewport.viewportProps}
      >
        {renderMode === "canvas" ? (
          <SpecializedMatrixCanvas
            scrollRef={viewport.scrollRef}
            rowCount={matrixRows.length}
            columnCount={tokens.length}
            rowHeight={27}
            columnWidth={viewport.size}
            rowLabelWidth={96}
            axesPinned={viewport.axesPinned}
            selectedRow={recommendedKeyboardRow}
            selectedColumn={selectedTokenPosition}
            comparisonRow={comparisonCell?.rowIndex}
            comparisonColumn={comparisonCell
              ? tokens.findIndex((token) => token.index === comparisonCell.tokenIndex)
              : undefined}
            rangeAxis="column"
            selectedRange={tokenRangeToPositions(tokens, selectedRange)}
            rangeEnabled={viewport.mode === "select"}
            ariaLabel={`NLA fidelity Canvas matrix, ${matrixRows.length} layer-component rows by ${tokens.length} token columns`}
            selectedDescription={selectedExactRow
              ? `Selected layer ${selectedExactRow.layer}, ${selectedExactRow.component}, token ${selectedToken}, ${metricValue(selectedExactRow, metric)}.`
              : `Selected layer ${selectedLayer}, token ${selectedToken}, no exact NLA artifact.`}
            overviewRevision={`${metric}:${threshold}:${componentFilter}`}
            cornerLabel="layer / comp"
            rowLabel={(rowIndex) => {
              const row = matrixRows[rowIndex];
              return row ? `L${row.layer} ${shortComponent(row.component)}` : String(rowIndex);
            }}
            columnLabel={(column) => String(tokens[column]?.index ?? column)}
            cell={(rowIndex, column) => {
              const matrixRow = matrixRows[rowIndex];
              const token = tokens[column]?.index ?? column;
              const row = matrixRow
                ? rowLookup.get(`${matrixRow.layer}:${matrixRow.component}:${token}`)
                : undefined;
              const value = row ? fidelityValue(row, metric) : undefined;
              const available = row !== undefined && row.status !== "unavailable";
              const passes = value !== undefined && (metric === "mse" ? value <= threshold : value >= threshold);
              const normOutlier = row ? normOutlierKeys.has(nlaRowKey(row)) : false;
              if (!row) return { fill: "#f5f7f6", hatch: "#dde5e3", label: `Token ${token}, no exact artifact` };
              if (!available) return { fill: "#fff5dc", hatch: "#d9a84c", label: `Token ${token}, incompatible candidate` };
              return {
                fill: passes ? "#b78322" : "#d99a8e",
                label: `L${row.layer} ${row.component}, token ${token}, ${metricValue(row, metric)}${normOutlier ? ", activation norm outlier" : ""}`
              };
            }}
            onSelect={(rowIndex, column, modifiers) => {
              const matrixRow = matrixRows[rowIndex];
              const token = tokens[column]?.index;
              if (!matrixRow || token === undefined) return;
              const exactRow = rowLookup.get(`${matrixRow.layer}:${matrixRow.component}:${token}`);
              if (modifiers.anchor) {
                if (exactRow?.status === "available" && fidelityValue(exactRow, metric) !== undefined) {
                  setComparisonCell({ rowIndex, tokenIndex: token });
                }
              } else if (modifiers.pin) {
                if (exactRow?.status === "available") {
                  onPinCell(matrixRow.layer, token, matrixRow.component);
                }
              } else {
                setKeyboardRowIndex(rowIndex);
                onSelectCell(matrixRow.layer, token, matrixRow.component);
              }
            }}
            onRangeSelect={(range) => onRangeSelect(positionRangeToTokens(tokens, range))}
            onPin={onPin}
            onHover={(rowIndex, column) => {
              const matrixRow = matrixRows[rowIndex];
              const token = tokens[column]?.index;
              const row = matrixRow && token !== undefined
                ? rowLookup.get(`${matrixRow.layer}:${matrixRow.component}:${token}`)
                : undefined;
              setHovered(row ?? null);
              onHoverToken(row?.tokenIndex ?? null);
            }}
            onHoverEnd={() => {
              setHovered(null);
              onHoverToken(null);
            }}
          />
        ) : (
        <div
          ref={gridRef}
          className={`nla-fidelity-grid ${viewport.axesPinned ? "axes-pinned" : ""}`}
          style={{
            gridTemplateColumns: `96px repeat(${tokens.length}, ${viewport.size}px)`,
            minWidth: `${99 + tokens.length * (viewport.size + 3)}px`
          }}
          {...rangeBrush.gridProps}
        >
          <div className="nla-grid-corner">layer / comp</div>
          {tokens.map((token) => (
            <div
              key={`nla-token-${token.index}`}
              className={`nla-token-label ${token.index === selectedToken ? "selected" : ""} ${rangeBrush.inRange(token.index) ? "in-range" : ""}`}
              data-range-token={token.index}
              title={matrixTokenTitle(token)}
            >
              {token.index}
            </div>
          ))}
          {matrixRows.map((matrixRow, rowIndex) => (
            <NLAHeatmapRow
              key={`${matrixRow.layer}-${matrixRow.component}`}
              matrixRow={matrixRow}
              rowIndex={rowIndex}
              rows={rows}
              tokens={tokens}
              metric={metric}
              threshold={threshold}
              normOutlierKeys={normOutlierKeys}
              selectedToken={selectedToken}
              selectedLayer={selectedLayer}
              selectedComponent={selectedComponent}
              keyboardRowIndex={keyboardRowIndex}
              comparisonCell={comparisonCell}
              inRange={rangeBrush.inRange}
              onSelectCell={onSelectCell}
              onSetComparison={setComparisonCell}
              onPinCell={onPinCell}
              onPin={onPin}
              onMoveFocus={moveFidelityFocus}
              onHover={(row) => {
                setHovered(row);
                onHoverToken(row?.tokenIndex ?? null);
              }}
            />
          ))}
        </div>
        )}
      </div>

      <NLAFidelityTooltip
        row={hovered}
        metric={metric}
        normOutlier={hovered ? normOutlierKeys.has(nlaRowKey(hovered)) : false}
        tokens={tokens}
      />

      <div className="nla-fidelity-legend">
        <span><i className="nla-high" />passes threshold</span>
        <span><i className="nla-low" />low fidelity</span>
        <span><i className="nla-norm-outlier" />activation norm outlier</span>
        <span><i className="nla-incompatible" />incompatible candidate</span>
        <span><i className="nla-missing" />no exact artifact</span>
        <b>{metricLabel(metric)} · exact-match only</b>
      </div>

      <section className="nla-profile-diagnostics" aria-label="NLA profile compatibility">
        <div className="inline-heading">
          <h4>Profile compatibility</h4>
          <span>{compatibility.profiles.length} registered profiles</span>
        </div>
        <div className="nla-profile-list">
          {compatibility.profiles.map((profile) => (
            <article key={profile.name}>
              <div>
                <strong>{profile.name}</strong>
                <span>{profile.baseModel} · L{profile.layer} · d_model {profile.dModel}</span>
              </div>
              <CompatibilityCheck label="model" matches={profile.modelMatches} />
              <CompatibilityCheck label="layer" matches={profile.layerAvailable} />
              <CompatibilityCheck label="d_model" matches={profile.dModelMatches} />
              <p>{profile.reason}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="nla-candidate-list" aria-label="NLA cached candidates">
        <div className="inline-heading">
          <h4>Cached activation candidates</h4>
          <span>{visibleCandidates.length} exact rows</span>
        </div>
        {visibleCandidates.length > 0 ? visibleCandidates.map((row) => {
          const normOutlier = normOutlierKeys.has(nlaRowKey(row));
          const lowFidelity = row.status !== "unavailable" && lowFidelityRows.includes(row);
          return (
          <button
            key={`${row.layer}-${row.component}-${row.tokenIndex}`}
            className={`${row.tokenIndex === selectedToken && row.layer === selectedLayer && row.component === selectedComponent ? "selected" : ""} ${normOutlier ? "norm-outlier" : ""} ${lowFidelity ? "low-fidelity" : ""}`}
            onClick={() => onSelectCell(row.layer, row.tokenIndex, row.component)}
          >
            <strong>{row.token || tokens[row.tokenIndex]?.text}</strong>
            <span>L{row.layer} · {row.component}</span>
            <span className="nla-candidate-norm">
              activation norm {row.activationNorm.toFixed(3)}
              {normOutlier && <i>outlier</i>}
            </span>
            <b>{row.status === "unavailable" ? "decoder unavailable" : metricValue(row, metric)}</b>
          </button>
          );
        }) : (
          <div className="nla-no-candidates">
            {query
              ? `No exact cached candidate matches “${query}”.`
              : reviewMode === "all"
                ? "No exact cached candidates are available."
                : `No candidates match the ${reviewMode === "low_fidelity" ? "low fidelity" : "norm outlier"} review filter.`}
          </div>
        )}
      </section>
    </section>
  );
}

function NLAHeatmapRow({
  matrixRow,
  rowIndex,
  rows,
  tokens,
  metric,
  threshold,
  normOutlierKeys,
  selectedToken,
  selectedLayer,
  selectedComponent,
  keyboardRowIndex,
  comparisonCell,
  inRange,
  onSelectCell,
  onSetComparison,
  onPinCell,
  onPin,
  onMoveFocus,
  onHover
}: {
  matrixRow: MatrixRow;
  rowIndex: number;
  rows: NLARow[];
  tokens: TokenInfo[];
  metric: FidelityMetric;
  threshold: number;
  normOutlierKeys: Set<string>;
  selectedToken: number;
  selectedLayer: number;
  selectedComponent: NLARow["component"];
  keyboardRowIndex: number;
  comparisonCell: { rowIndex: number; tokenIndex: number } | null;
  inRange: (token: number) => boolean;
  onSelectCell: (layer: number, token: number, component: NLARow["component"]) => void;
  onSetComparison: (cell: { rowIndex: number; tokenIndex: number }) => void;
  onPinCell: (layer: number, token: number, component: NLARow["component"]) => void;
  onPin?: () => void;
  onMoveFocus: (rowIndex: number, token: number, key: string) => void;
  onHover: (row: NLARow | null) => void;
}) {
  return (
    <>
      <button
        className={`nla-row-label ${matrixRow.layer === selectedLayer && matrixRow.component === selectedComponent ? "selected" : ""}`}
        onClick={() => onSelectCell(matrixRow.layer, selectedToken, matrixRow.component)}
        tabIndex={-1}
      >
        <b>L{matrixRow.layer}</b><span>{shortComponent(matrixRow.component)}</span>
      </button>
      {tokens.map((token) => {
        const row = rows.find(
          (item) => item.layer === matrixRow.layer &&
            item.component === matrixRow.component &&
            item.tokenIndex === token.index
        );
        const available = row !== undefined && row.status !== "unavailable";
        const value = row ? fidelityValue(row, metric) : undefined;
        const metricAvailable = value !== undefined;
        const passes = value !== undefined && (metric === "mse" ? value <= threshold : value >= threshold);
        const selected =
          matrixRow.layer === selectedLayer &&
          matrixRow.component === selectedComponent &&
          token.index === selectedToken;
        const comparison = comparisonCell?.rowIndex === rowIndex && comparisonCell.tokenIndex === token.index;
        const cellClass = !row
          ? "missing"
          : !available
            ? "incompatible"
            : !metricAvailable || !passes
              ? "low"
              : "high";
        const normOutlier = row ? normOutlierKeys.has(nlaRowKey(row)) : false;
        return (
          <button
            key={`${matrixRow.layer}-${matrixRow.component}-${token.index}`}
            className={`nla-fidelity-cell ${cellClass} ${selected ? "selected" : ""} ${comparison ? "comparison" : ""} ${normOutlier ? "norm-outlier" : ""} ${inRange(token.index) ? "in-range" : ""}`}
            data-layer={matrixRow.layer}
            data-row-index={rowIndex}
            data-component={matrixRow.component}
            data-token={token.index}
            data-range-token={token.index}
            aria-label={
              row
                ? `L${matrixRow.layer} ${matrixRow.component}, token ${token.index}, ${row.status === "unavailable" ? "incompatible" : metricValue(row, metric)}${normOutlier ? ", activation norm outlier" : ""}`
                : `L${matrixRow.layer} ${matrixRow.component}, token ${token.index}, no artifact`
            }
            tabIndex={keyboardRowIndex === rowIndex && token.index === selectedToken ? 0 : -1}
            aria-keyshortcuts={onPin
              ? "ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter Space"
              : "ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter"}
            onClick={(event) => {
              if (event.shiftKey) {
                if (row?.status === "available" && metricAvailable) {
                  onSetComparison({ rowIndex, tokenIndex: token.index });
                }
              } else if (event.metaKey || event.ctrlKey) {
                if (row?.status === "available") {
                  onPinCell(matrixRow.layer, token.index, matrixRow.component);
                }
              } else {
                onSelectCell(matrixRow.layer, token.index, matrixRow.component);
              }
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
                if (row?.status === "available" && metricAvailable) {
                  onSetComparison({ rowIndex, tokenIndex: token.index });
                }
                return;
              }
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                event.stopPropagation();
                if (row?.status === "available") {
                  onPinCell(matrixRow.layer, token.index, matrixRow.component);
                }
                return;
              }
              if (event.key === " " && onPin) {
                event.preventDefault();
                event.stopPropagation();
                onPin();
                return;
              }
              if (!isNavigationKey(event.key)) return;
              event.preventDefault();
              event.stopPropagation();
              onMoveFocus(rowIndex, token.index, event.key);
            }}
            onMouseEnter={() => onHover(row ?? null)}
            onMouseLeave={() => onHover(null)}
            onFocus={() => onHover(row ?? null)}
            onBlur={() => onHover(null)}
          />
        );
      })}
    </>
  );
}

function NLAFidelityTooltip({
  row,
  metric,
  normOutlier,
  tokens
}: {
  row: NLARow | null;
  metric: FidelityMetric;
  normOutlier: boolean;
  tokens: TokenInfo[];
}) {
  if (!row) {
    return <div className="nla-fidelity-tooltip empty">Fidelity details · no matrix cell focused.</div>;
  }
  return (
    <div className="nla-fidelity-tooltip">
      <MatrixTokenDetail
        tokens={tokens}
        tokenIndex={row.tokenIndex}
        fallbackText={row.token}
      />
      <span><b>L{row.layer}</b>{row.component}</span>
      <span><b>{row.status === "unavailable" ? "unavailable" : metricValue(row, metric, "exact")}</b>{metricLabel(metric)}</span>
      <span><b>{formatMetricNumber(row.activationNorm, "residual_norm", "exact")}</b>activation norm{normOutlier ? " · IQR outlier" : ""}</span>
      <span className="nla-tooltip-explanation"><b>{row.profile ?? "no matching profile"}</b>{row.explanation}</span>
    </div>
  );
}

function CompatibilityCheck({ label, matches }: { label: string; matches: boolean }) {
  return (
    <span className={matches ? "matches" : "fails"}>
      {matches ? <Check size={11} /> : <X size={11} />}{label}
    </span>
  );
}

function fidelityValue(row: NLARow, metric: FidelityMetric) {
  if (metric === "cosine") return row.cosine;
  if (metric === "mse") return row.mse;
  return row.fve;
}

function passesFidelityThreshold(row: NLARow, metric: FidelityMetric, threshold: number) {
  const value = fidelityValue(row, metric);
  return value !== undefined && (metric === "mse" ? value <= threshold : value >= threshold);
}

function nlaRowKey(row: NLARow) {
  return `${row.layer}:${row.component}:${row.tokenIndex}`;
}

function activationNormOutlierKeys(rows: NLARow[]) {
  if (rows.length < 4) return new Set<string>();
  const values = rows.map((row) => row.activationNorm).sort((left, right) => left - right);
  const q1 = quantile(values, 0.25);
  const q3 = quantile(values, 0.75);
  const iqr = q3 - q1;
  if (!Number.isFinite(iqr) || iqr <= 1e-12) return new Set<string>();
  const lower = q1 - 1.5 * iqr;
  const upper = q3 + 1.5 * iqr;
  return new Set(rows
    .filter((row) => row.activationNorm < lower || row.activationNorm > upper)
    .map(nlaRowKey));
}

function quantile(values: number[], fraction: number) {
  const position = (values.length - 1) * fraction;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  const weight = position - lower;
  return values[lower] * (1 - weight) + values[upper] * weight;
}

function metricValue(row: NLARow, metric: FidelityMetric, mode: MetricFormatMode = "compact") {
  const value = fidelityValue(row, metric);
  return value === undefined ? "metric unavailable" : formatMetricNumber(value, `nla_${metric}`, mode);
}

function metricLabel(metric: FidelityMetric) {
  if (metric === "mse") return "reconstruction MSE";
  if (metric === "fve") return "fraction variance explained";
  return "cosine fidelity";
}

function formatFidelityDelta(value: number, metric: FidelityMetric) {
  return formatMetricDelta(value, `nla_${metric}`, "compact");
}

function shortComponent(component: NLARow["component"]) {
  if (component === "resid_post") return "resid";
  if (component === "attn_result") return "attn";
  return "mlp";
}

function unique<T>(values: T[]) {
  return [...new Set(values)];
}

function isNavigationKey(key: string) {
  return ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(key);
}
