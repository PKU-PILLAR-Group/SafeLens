import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Pin } from "lucide-react";

import { ActionableEmptyState } from "./ActionableEmptyState";
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
import { formatMetricDelta, formatMetricNumber } from "../metricFormatting";
import type { AttributionMethod, NormalizationMode, TokenInfo } from "../types";

interface SignedAttributionMatrixProps {
  methods: AttributionMethod[];
  selectedMethod: AttributionMethod;
  tokens: TokenInfo[];
  selectedToken: number;
  selectedLayer: number;
  normalization: NormalizationMode;
  selectedRange?: [number, number];
  onMethodChange: (methodId: string) => void;
  onNormalizationChange: (normalization: NormalizationMode) => void;
  onSelectCell: (layer: number, token: number) => void;
  onRangeSelect: (range?: [number, number]) => void;
  onHoverToken: (token: number | null) => void;
  onPin: () => void;
  onPinCell: (layer: number, token: number) => void;
  onConfigureIntegratedGradients?: () => void;
}

interface HoveredAttribution {
  layer: number;
  label: string;
  tokenIndex: number;
  value: number;
  sourceKey: string;
}

export function SignedAttributionMatrix({
  methods,
  selectedMethod,
  tokens,
  selectedToken,
  selectedLayer,
  normalization,
  selectedRange,
  onMethodChange,
  onNormalizationChange,
  onSelectCell,
  onRangeSelect,
  onHoverToken,
  onPin,
  onPinCell,
  onConfigureIntegratedGradients
}: SignedAttributionMatrixProps) {
  const [hovered, setHovered] = useState<HoveredAttribution | null>(null);
  const [comparisonCell, setComparisonCell] = useState<{ rowIndex: number; tokenIndex: number } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const viewport = useMatrixViewport({
    initialSize: 24,
    minimumSize: 14,
    maximumSize: 38,
    itemCount: tokens.length,
    labelWidth: 72,
    sessionKey: "attribution"
  });
  const rangeBrush = useMatrixRangeBrush({
    enabled: viewport.mode === "select",
    selectedRange,
    onRangeSelect
  });
  const cellWidth = viewport.size;
  const values = selectedMethod.rows.flatMap((row) => row.values);
  const bounds = useMemo(() => valueBounds(values), [values]);
  const selectedRow =
    selectedMethod.rows.find((row) => row.layer === selectedLayer) ?? selectedMethod.rows[0];
  const selectedValue = selectedRow?.values[selectedToken] ?? 0;
  const comparisonRow = comparisonCell ? selectedMethod.rows[comparisonCell.rowIndex] : undefined;
  const comparisonValue = comparisonCell && comparisonRow
    ? comparisonRow.values[comparisonCell.tokenIndex] ?? 0
    : undefined;
  const positiveCount = values.filter((value) => value > 0).length;
  const negativeCount = values.filter((value) => value < 0).length;
  const keyboardRowIndex = Math.max(
    0,
    selectedMethod.rows.findIndex((row) => row.layer === selectedLayer || row.layer < 0)
  );
  useEffect(() => {
    setComparisonCell(null);
  }, [selectedMethod.id, tokens]);
  const minGridWidth = 72 + tokens.length * cellWidth + (tokens.length + 1) * 3;
  const renderMode = selectedMethod.rows.length * tokens.length >= SPECIALIZED_CANVAS_CELL_THRESHOLD
    ? "canvas"
    : "dom";
  const selectedTokenPosition = Math.max(0, tokens.findIndex((token) => token.index === selectedToken));

  function moveAttributionFocus(rowIndex: number, tokenIndex: number, key: string) {
    const tokenPosition = Math.max(0, tokens.findIndex((token) => token.index === tokenIndex));
    let nextRow = rowIndex;
    let nextToken = tokenPosition;
    if (key === "ArrowLeft") nextToken = Math.max(0, tokenPosition - 1);
    if (key === "ArrowRight") nextToken = Math.min(tokens.length - 1, tokenPosition + 1);
    if (key === "ArrowUp") nextRow = Math.max(0, rowIndex - 1);
    if (key === "ArrowDown") nextRow = Math.min(selectedMethod.rows.length - 1, rowIndex + 1);
    if (key === "Home") nextToken = 0;
    if (key === "End") nextToken = tokens.length - 1;
    const row = selectedMethod.rows[nextRow];
    const token = tokens[nextToken]?.index;
    if (!row || token === undefined) return;
    onSelectCell(row.layer, token);
    window.requestAnimationFrame(() => {
      gridRef.current
        ?.querySelector<HTMLButtonElement>(
          `[data-row-index="${nextRow}"][data-token="${token}"]`
        )
        ?.focus();
    });
  }

  return (
    <section className="surface attribution-matrix-section">
      <div className="surface-header attribution-matrix-header">
        <div>
          <h3>Attribution matrix</h3>
          <p>Method-aware token evidence with signed and unsigned semantics kept separate.</p>
        </div>
        <span className={`evidence-kind attribution-kind-${selectedMethod.evidenceKind}`}>
          {selectedMethod.evidenceKind.replace("_", " ")}
        </span>
      </div>

      <div className="attribution-matrix-toolbar" aria-label="Attribution matrix controls">
        <label>
          <span>Method</span>
          <select value={selectedMethod.id} onChange={(event) => onMethodChange(event.target.value)}>
            {methods.map((method) => (
              <option key={method.id} value={method.id}>
                {method.label}{method.available ? "" : " (not run)"}
              </option>
            ))}
          </select>
        </label>
        <div className="toolbar-segment" aria-label="Attribution normalization">
          <button
            className={normalization === "raw" ? "active" : ""}
            onClick={() => onNormalizationChange("raw")}
          >
            {selectedMethod.signed ? "Raw" : "Stored"}
          </button>
          <button
            className={normalization === "normalized" ? "active" : ""}
            onClick={() => onNormalizationChange("normalized")}
          >
            Normalized
          </button>
        </div>
        <div className="attribution-method-summary">
          <span><b>{selectedMethod.signed ? "Signed" : "Unsigned"}</b>value domain</span>
          <span><b>{selectedMethod.rows.length}</b>matrix rows</span>
          <span><b>{selectedValue.toFixed(6)}</b>selected stored value</span>
        </div>
        <div className="toolbar-actions">
          <MatrixViewportControls viewport={viewport} label="attribution matrix" />
          <button aria-label="Pin selected attribution" disabled={!selectedMethod.available} onClick={onPin}>
            <Pin size={14} />
          </button>
        </div>
      </div>

      <div className="attribution-method-note">
        <strong>{selectedMethod.label}</strong>
        <p>{selectedMethod.description}</p>
        <span>{selectedMethod.normalization}</span>
      </div>

      {!selectedMethod.available ? (
        selectedMethod.id === "integrated_gradients" && onConfigureIntegratedGradients ? (
          <ActionableEmptyState
            compact
            className="attribution-unavailable"
            icon={<Activity size={20} />}
            title={`${selectedMethod.label} is not available for this run`}
            description={selectedMethod.unavailableReason ?? "No target-specific attribution artifact was computed."}
            facts={[
              { label: "Method", value: "Integrated Gradients" },
              { label: "Required", value: "target + baseline + convergence" }
            ]}
            actionLabel="Configure Integrated Gradients"
            actionIcon={<Activity size={16} />}
            onAction={onConfigureIntegratedGradients}
          />
        ) : (
          <div className="attribution-unavailable" role="status">
            <Activity size={20} />
            <div>
              <strong>{selectedMethod.label} is not available for this run</strong>
              <p>{selectedMethod.unavailableReason}</p>
              <span>Required artifact: method output + target objective + convergence metadata</span>
            </div>
          </div>
        )
      ) : (
        <>
          <div className="attribution-sign-summary" aria-label="Attribution sign summary">
            <span><b>{positiveCount}</b>positive cells</span>
            <span><b>{negativeCount}</b>negative cells</span>
            <span><b>{values.length - positiveCount - negativeCount}</b>zero cells</span>
            <span><b>{selectedRow?.label ?? "n/a"}</b>selected row</span>
          </div>
          <MatrixComparisonSummary
            label="Attribution matrix"
            primary={`${selectedRow?.label ?? "row"} · T${selectedToken}`}
            anchor={comparisonCell && comparisonRow
              ? `${comparisonRow.label} · T${comparisonCell.tokenIndex}`
              : undefined}
            delta={comparisonValue === undefined
              ? undefined
              : formatSignedDelta(selectedValue - comparisonValue)}
            deltaLabel="raw delta"
            onClear={() => setComparisonCell(null)}
          />
          <MatrixRangeSummary label="Token" range={selectedRange} onClear={() => onRangeSelect(undefined)} />

          <div
            ref={viewport.scrollRef}
            className={`attribution-matrix-scroll ${renderMode === "canvas" ? "specialized-canvas-mode" : ""} ${viewport.mode === "pan" ? "pan-mode" : ""}`}
            {...viewport.viewportProps}
          >
            {renderMode === "canvas" ? (
              <SpecializedMatrixCanvas
                scrollRef={viewport.scrollRef}
                rowCount={selectedMethod.rows.length}
                columnCount={tokens.length}
                rowHeight={24}
                columnWidth={cellWidth}
                rowLabelWidth={72}
                axesPinned={viewport.axesPinned}
                selectedRow={keyboardRowIndex}
                selectedColumn={selectedTokenPosition}
                comparisonRow={comparisonCell?.rowIndex}
                comparisonColumn={comparisonCell
                  ? tokens.findIndex((token) => token.index === comparisonCell.tokenIndex)
                  : undefined}
                rangeAxis="column"
                selectedRange={tokenRangeToPositions(tokens, selectedRange)}
                rangeEnabled={viewport.mode === "select"}
                ariaLabel={`${selectedMethod.label} Canvas attribution matrix, ${selectedMethod.rows.length} rows by ${tokens.length} token columns`}
                selectedDescription={`Selected ${selectedRow?.label ?? "row"}, token ${selectedToken}, stored attribution ${selectedValue.toFixed(6)}.`}
                overviewRevision={`${selectedMethod.id}:${normalization}`}
                cornerLabel="row"
                rowLabel={(rowIndex) => selectedMethod.rows[rowIndex]?.label ?? String(rowIndex)}
                columnLabel={(column) => String(tokens[column]?.index ?? column)}
                cell={(rowIndex, column) => {
                  const row = selectedMethod.rows[rowIndex];
                  const token = tokens[column]?.index ?? column;
                  const value = row?.values[token] ?? 0;
                  const display = normalizeValue(value, bounds, selectedMethod.signed);
                  const strength = Math.max(0, Math.min(1, Math.abs(display)));
                  return {
                    fill: selectedMethod.signed
                      ? value < 0
                        ? `rgba(57, 127, 145, ${0.08 + strength * 0.82})`
                        : `rgba(198, 104, 47, ${0.08 + strength * 0.82})`
                      : `rgba(198, 104, 47, ${0.08 + strength * 0.82})`,
                    label: `${row?.label ?? "row"}, token ${token}, attribution ${value.toFixed(6)}`
                  };
                }}
                onSelect={(rowIndex, column, modifiers) => {
                  const row = selectedMethod.rows[rowIndex];
                  const token = tokens[column]?.index;
                  if (!row || token === undefined) return;
                  if (modifiers.anchor) {
                    setComparisonCell({ rowIndex, tokenIndex: token });
                  } else if (modifiers.pin) {
                    onPinCell(row.layer, token);
                  } else {
                    onSelectCell(row.layer, token);
                  }
                }}
                onRangeSelect={(range) => onRangeSelect(positionRangeToTokens(tokens, range))}
                onPin={onPin}
                onHover={(rowIndex, column) => {
                  const row = selectedMethod.rows[rowIndex];
                  const tokenIndex = tokens[column]?.index;
                  if (!row || tokenIndex === undefined) return;
                  const value = row.values[tokenIndex] ?? 0;
                  setHovered({
                    layer: row.layer,
                    label: row.label,
                    tokenIndex,
                    value,
                    sourceKey: row.sourceKey
                  });
                  onHoverToken(tokenIndex);
                }}
                onHoverEnd={() => {
                  setHovered(null);
                  onHoverToken(null);
                }}
              />
            ) : (
            <div
              ref={gridRef}
              className={`attribution-value-grid ${viewport.axesPinned ? "axes-pinned" : ""}`}
              style={{
                gridTemplateColumns: `72px repeat(${tokens.length}, ${cellWidth}px)`,
                minWidth: `${minGridWidth}px`
              }}
              {...rangeBrush.gridProps}
            >
              <div className="attribution-grid-corner">row ↓</div>
              {tokens.map((token) => (
                <div
                  key={`attribute-token-${token.index}`}
                  className={`attribution-token-label ${selectedToken === token.index ? "selected" : ""} ${rangeBrush.inRange(token.index) ? "in-range" : ""}`}
                  data-range-token={token.index}
                  title={matrixTokenTitle(token)}
                >
                  {token.index}
                </div>
              ))}
              {selectedMethod.rows.map((row, rowIndex) => (
                <AttributionRow
                  key={`${selectedMethod.id}-${row.layer}`}
                  row={row}
                  rowIndex={rowIndex}
                  tokens={tokens}
                  bounds={bounds}
                  signed={selectedMethod.signed}
                  normalization={normalization}
                  selectedToken={selectedToken}
                  selectedLayer={selectedLayer}
                  keyboardRowIndex={keyboardRowIndex}
                  comparisonCell={comparisonCell}
                  inRange={rangeBrush.inRange}
                  onSelectCell={onSelectCell}
                  onSetComparison={setComparisonCell}
                  onPinCell={onPinCell}
                  onPin={onPin}
                  onMoveFocus={moveAttributionFocus}
                  onHover={(value) => {
                    setHovered(value);
                    onHoverToken(value?.tokenIndex ?? null);
                  }}
                />
              ))}
            </div>
            )}
          </div>

          <AttributionTooltip
            value={hovered}
            method={selectedMethod}
            bounds={bounds}
            normalization={normalization}
            tokens={tokens}
          />

          <div className={`attribution-legend ${selectedMethod.signed ? "signed" : "unsigned"}`}>
            {selectedMethod.signed ? (
              <>
                <span><i className="attribution-negative" />negative</span>
                <span><i className="attribution-zero" />zero</span>
                <span><i className="attribution-positive" />positive</span>
              </>
            ) : (
              <>
                <span><i className="attribution-low" />low</span>
                <span><i className="attribution-mid" />mid</span>
                <span><i className="attribution-high" />high</span>
              </>
            )}
            <b>{normalization === "raw" ? selectedMethod.normalization : "display-normalized within method"}</b>
          </div>
        </>
      )}
    </section>
  );
}

function AttributionRow({
  row,
  rowIndex,
  tokens,
  bounds,
  signed,
  normalization,
  selectedToken,
  selectedLayer,
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
  row: AttributionMethod["rows"][number];
  rowIndex: number;
  tokens: TokenInfo[];
  bounds: [number, number];
  signed: boolean;
  normalization: NormalizationMode;
  selectedToken: number;
  selectedLayer: number;
  keyboardRowIndex: number;
  comparisonCell: { rowIndex: number; tokenIndex: number } | null;
  inRange: (token: number) => boolean;
  onSelectCell: (layer: number, token: number) => void;
  onSetComparison: (cell: { rowIndex: number; tokenIndex: number }) => void;
  onPinCell: (layer: number, token: number) => void;
  onPin: () => void;
  onMoveFocus: (rowIndex: number, token: number, key: string) => void;
  onHover: (value: HoveredAttribution | null) => void;
}) {
  return (
    <>
      <button
        className={`attribution-row-label ${row.layer === selectedLayer || row.layer < 0 ? "selected" : ""}`}
        onClick={() => onSelectCell(row.layer, selectedToken)}
        tabIndex={-1}
      >
        {row.label}
      </button>
      {tokens.map((token) => {
        const value = row.values[token.index] ?? 0;
        const display = normalizeValue(value, bounds, signed);
        const selected = selectedToken === token.index && (row.layer === selectedLayer || row.layer < 0);
        const comparison = comparisonCell?.rowIndex === rowIndex && comparisonCell.tokenIndex === token.index;
        return (
          <button
            key={`${row.layer}:${token.index}`}
            className={[
              "attribution-value-cell",
              signed ? (value < 0 ? "negative" : "positive") : "unsigned",
              selected ? "selected" : "",
              comparison ? "comparison" : "",
              inRange(token.index) ? "in-range" : ""
            ].join(" ")}
            data-layer={row.layer}
            data-row-index={rowIndex}
            data-token={token.index}
            data-range-token={token.index}
            style={{ "--attribution": Math.abs(display) } as React.CSSProperties}
            aria-label={`${row.label}, token ${token.index}, attribution ${value.toFixed(6)}`}
            aria-keyshortcuts="ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter Space"
            title={(normalization === "raw" ? value : display).toFixed(6)}
            tabIndex={keyboardRowIndex === rowIndex && selectedToken === token.index ? 0 : -1}
            onClick={(event) => {
              if (event.shiftKey) {
                onSetComparison({ rowIndex, tokenIndex: token.index });
              } else if (event.metaKey || event.ctrlKey) {
                onPinCell(row.layer, token.index);
              } else {
                onSelectCell(row.layer, token.index);
              }
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
                onSetComparison({ rowIndex, tokenIndex: token.index });
                return;
              }
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                event.stopPropagation();
                onPinCell(row.layer, token.index);
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
              onMoveFocus(rowIndex, token.index, event.key);
            }}
            onMouseEnter={() => onHover({
              layer: row.layer,
              label: row.label,
              tokenIndex: token.index,
              value,
              sourceKey: row.sourceKey
            })}
            onMouseLeave={() => onHover(null)}
            onFocus={() => onHover({
              layer: row.layer,
              label: row.label,
              tokenIndex: token.index,
              value,
              sourceKey: row.sourceKey
            })}
            onBlur={() => onHover(null)}
          />
        );
      })}
    </>
  );
}

function AttributionTooltip({
  value,
  method,
  bounds,
  normalization,
  tokens
}: {
  value: HoveredAttribution | null;
  method: AttributionMethod;
  bounds: [number, number];
  normalization: NormalizationMode;
  tokens: TokenInfo[];
}) {
  if (!value) {
    return <div className="attribution-tooltip empty">Attribution details · no matrix cell focused.</div>;
  }
  const normalized = normalizeValue(value.value, bounds, method.signed);
  return (
    <div className="attribution-tooltip">
      <MatrixTokenDetail tokens={tokens} tokenIndex={value.tokenIndex} />
      <span><b>{value.label}</b>row</span>
      <span><b>{formatMetricNumber(value.value, method.id, "exact")}</b>stored value</span>
      <span><b>{formatMetricNumber(normalized, "normalized", "exact")}</b>display normalized</span>
      <span><b>{formatMetricNumber(normalization === "raw" ? value.value : normalized, normalization === "raw" ? method.id : "normalized", "exact")}</b>displayed</span>
      <span className="attribution-tooltip-source"><b>{value.sourceKey}</b>source</span>
      <span className="attribution-tooltip-source"><b>{method.evidenceKind.replace("_", " ")}</b>evidence class</span>
    </div>
  );
}

function valueBounds(values: number[]): [number, number] {
  if (values.length === 0) return [0, 1];
  let minimum = values[0] ?? 0;
  let maximum = minimum;
  for (let index = 1; index < values.length; index += 1) {
    minimum = Math.min(minimum, values[index]);
    maximum = Math.max(maximum, values[index]);
  }
  return [minimum, maximum];
}

function normalizeValue(value: number, bounds: [number, number], signed: boolean) {
  if (signed) {
    const maximum = Math.max(Math.abs(bounds[0]), Math.abs(bounds[1]), 1e-12);
    return value / maximum;
  }
  const width = bounds[1] - bounds[0];
  return Math.abs(width) < 1e-12 ? 0 : (value - bounds[0]) / width;
}

function formatSignedDelta(value: number) {
  return formatMetricDelta(value, "attribution", "compact");
}

function isNavigationKey(key: string) {
  return ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(key);
}
