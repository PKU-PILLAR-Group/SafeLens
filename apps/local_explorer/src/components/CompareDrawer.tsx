import { useRef, useState, type CSSProperties, type RefObject } from "react";
import {
  ArrowRight,
  Download,
  GitCompareArrows,
  Link2,
  RotateCcw,
  Target,
  Trash2,
  Unlink,
  X
} from "lucide-react";

import type {
  EvidenceProfilePoint,
  MetricProvenance,
  PinnedEvidence,
  TokenInfo
} from "../types";
import {
  attentionAggregationLabel,
  parseAttentionAggregation,
  parseAttentionDifference,
  parseAttentionRollout
} from "../attentionAggregation";
import { useModalDialog } from "../state/useModalDialog";
import {
  formatMetricDelta as formatRegisteredDelta,
  formatMetricNumber,
  metricDisplayLabel
} from "../metricFormatting";
import { SpecializedMatrixCanvas } from "./SpecializedMatrixCanvas";
import { MatrixOverviewNavigator } from "./MatrixOverviewNavigator";

interface CompareDrawerProps {
  open: boolean;
  pinned: PinnedEvidence[];
  tokens: TokenInfo[];
  metricProvenance: Record<string, MetricProvenance>;
  currentRunKey: string;
  availableRunKeys: Set<string>;
  baselineId?: string;
  returnFocusRef?: RefObject<HTMLElement>;
  onClose: () => void;
  onRestore: (evidence: PinnedEvidence) => void;
  onRemove: (evidence: PinnedEvidence) => void;
  onBaselineChange: (id: string) => void;
}

export function CompareDrawer({
  open,
  pinned,
  tokens,
  metricProvenance,
  currentRunKey,
  availableRunKeys,
  baselineId,
  returnFocusRef,
  onClose,
  onRestore,
  onRemove,
  onBaselineChange
}: CompareDrawerProps) {
  const closeButton = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLElement>(null);
  useModalDialog({
    open,
    dialogRef: dialog,
    initialFocusRef: closeButton,
    returnFocusRef,
    onClose
  });

  if (!open) {
    return null;
  }

  const baseline = pinned.find((item) => item.id === baselineId) ?? pinned[0];
  const orderedPinned = baseline
    ? [baseline, ...pinned.filter((item) => item.id !== baseline.id)]
    : pinned;
  const distinctTokens = new Set(pinned.map((item) => item.tokenIndex)).size;
  const distinctRuns = new Set(pinned.map(runKey)).size;
  const comparableCount = baseline
    ? pinned.filter((item) => comparisonAssessment(item, baseline).comparable).length
    : 0;

  function exportComparison() {
    if (!baseline) return;
    const payload = {
      schema_version: "1.0",
      kind: "safelens-comparison",
      exported_at: new Date().toISOString(),
      baseline_id: baseline.id,
      items: orderedPinned,
      comparisons: orderedPinned.map((item) => {
        const alignment = alignTokens(item, baseline);
        const assessment = comparisonAssessment(item, baseline);
        const profileDifference = compareProfiles(item, baseline);
        const matrixDifference = compareAttentionMatrices(item, baseline);
        const generationDifference = compareGenerations(item, baseline);
        return {
          item_id: item.id,
          alignment,
          comparable: assessment.comparable,
          reason: assessment.reason,
          delta: assessment.comparable ? item.value - baseline.value : null,
          profile_difference: profileDifference.comparable
            ? {
                comparable: true,
                reason: profileDifference.reason,
                aligned_points: profileDifference.points.length,
                mean_absolute_delta: meanAbsoluteDelta(profileDifference.points),
                max_absolute_delta: maxAbsoluteDelta(profileDifference.points),
                deltas: profileDifference.points
              }
            : {
                comparable: false,
                reason: profileDifference.reason
              },
          matrix_difference: matrixDifference.comparable
            ? {
                comparable: true,
                reason: matrixDifference.reason,
                sampled: matrixDifference.sampled,
                axis: matrixDifference.axis,
                aligned_size: matrixDifference.axis.length,
                mean_absolute_delta: meanMatrixDelta(matrixDifference.cells),
                max_absolute_delta: maxMatrixDelta(matrixDifference.cells),
                cells: matrixDifference.cells
              }
            : {
                comparable: false,
                reason: matrixDifference.reason
              },
          generation_difference: item.generation
            ? {
                available: true,
                baseline_compatible: generationDifference.comparable,
                reason: generationDifference.reason,
                token_edit_distance: item.generation.tokenEditDistance,
                generation_changed: item.generation.generationChanged,
                diff: item.generation.diff
              }
            : {
                available: false,
                baseline_compatible: false,
                reason: generationDifference.reason
              }
        };
      })
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `safelens-comparison-${baseline.runId}-${baseline.sampleId}.json`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  return (
    <div
      className="compare-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <aside
        ref={dialog}
        className="compare-drawer"
        role="dialog"
        tabIndex={-1}
        aria-modal="true"
        aria-labelledby="compare-title"
      >
        <header className="compare-header">
          <div>
            <span className="compare-eyebrow"><GitCompareArrows size={14} /> Evidence workspace</span>
            <h2 id="compare-title">Compare pinned evidence</h2>
            <p>The first pinned item is the comparison baseline.</p>
          </div>
          <div className="compare-header-actions">
            <button
              aria-label="Export evidence comparison"
              title="Export comparison artifact"
              disabled={!pinned.length}
              onClick={exportComparison}
            >
              <Download size={17} />
            </button>
            <button ref={closeButton} aria-label="Close evidence comparison" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </header>

        {pinned.length > 0 ? (
          <>
            <section className="compare-summary" aria-label="Comparison summary">
              <span><b>{pinned.length}</b>evidence items</span>
              <span><b>{distinctRuns}</b>runs / samples</span>
              <span><b>{distinctTokens}</b>token positions</span>
              <span>
                <b>{comparableCount}/{pinned.length}</b>
                baseline-compatible
              </span>
            </section>

            {baseline && pinned.length > 1 && (
              <ComparisonDeltaPlot items={orderedPinned} baseline={baseline} />
            )}

            {baseline && pinned.length > 1 && (
              <AttentionMatrixDifferenceView items={orderedPinned} baseline={baseline} />
            )}

            {baseline && pinned.length > 1 && (
              <ProfileDifferencePlot items={orderedPinned} baseline={baseline} />
            )}

            {baseline && pinned.some((item) => item.generation) && (
              <GenerationDifferenceView items={orderedPinned} baseline={baseline} />
            )}

            {pinned.length < 2 && (
              <div className="compare-guidance">
                Comparison requires at least two evidence items.
              </div>
            )}

            <section className="compare-grid" aria-label="Pinned evidence comparison">
              {orderedPinned.map((evidence, index) => {
                const evidenceRunKey = runKey(evidence);
                const token = evidenceRunKey === currentRunKey
                  ? tokens.find((item) => item.index === evidence.tokenIndex)
                  : undefined;
                const provenance = resolveProvenance(evidence, metricProvenance);
                const alignment = baseline ? alignTokens(evidence, baseline) : undefined;
                const assessment = baseline
                  ? comparisonAssessment(evidence, baseline)
                  : { comparable: false, reason: "No baseline selected." };
                const delta = baseline && assessment.comparable
                  ? evidence.value - baseline.value
                  : undefined;
                const sourceAvailable = availableRunKeys.has(evidenceRunKey);
                return (
                  <article
                    key={evidence.id}
                    className={`compare-card compare-${evidence.view} ${index === 0 ? "baseline" : ""}`}
                  >
                    <div className="compare-card-heading">
                      <span className="compare-index">{index === 0 ? "Baseline" : `Item ${index + 1}`}</span>
                      <div>
                        <button
                          aria-label={`Use ${evidence.runId} ${evidence.tokenText} as baseline`}
                          title="Use as comparison baseline"
                          disabled={evidence.id === baseline?.id}
                          onClick={() => onBaselineChange(evidence.id)}
                        >
                          <Target size={14} />
                        </button>
                        <button
                          aria-label={`Remove ${evidence.tokenText} from comparison`}
                          title="Remove from comparison"
                          onClick={() => onRemove(evidence)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                    <div className="compare-run-context">
                      <strong>{evidence.runId}</strong>
                      <span>{evidence.sampleId}</span>
                      <em>{evidence.modelName ?? "model unavailable"}</em>
                    </div>

                    <div className="compare-token">
                      <strong>{evidence.tokenText || "␠"}</strong>
                      <span>token {evidence.tokenIndex} · id {evidence.tokenId ?? token?.tokenId ?? "n/a"}</span>
                    </div>

                    {alignment && (
                      <div className={`compare-alignment alignment-${alignment.status}`}>
                        {alignment.compatible ? <Link2 size={14} /> : <Unlink size={14} />}
                        <div><strong>{alignment.label}</strong><span>{alignment.reason}</span></div>
                      </div>
                    )}

                    <dl className="compare-context">
                      <div><dt>View</dt><dd>{labelView(evidence.view)}</dd></div>
                      <div><dt>Layer</dt><dd>L{evidence.layer}</dd></div>
                      <div><dt>Metric</dt><dd>{formatMetric(evidence.metric)}</dd></div>
                      <div><dt>Mode</dt><dd>{evidence.normalization}</dd></div>
                    </dl>

                    <div className="compare-value">
                      <span>Displayed value</span>
                      <strong>{formatValue(evidence.value, evidence.metric)}</strong>
                      <em className={deltaTone(delta, assessment.comparable)}>
                        {index === 0
                          ? "comparison baseline"
                          : assessment.comparable
                            ? `${formatDelta(delta ?? 0, evidence.metric)} vs baseline`
                            : assessment.reason}
                      </em>
                    </div>

                    {(evidence.headId || evidence.neuronId || evidence.sourceTokenIndex !== undefined) && (
                      <div className="compare-component">
                        {evidence.headId && <span>head {formatHeadSelection(evidence.headId)}</span>}
                        {evidence.neuronId && <span>neuron {evidence.neuronId}</span>}
                        {evidence.sourceTokenIndex !== undefined && (
                          <span>pair {evidence.sourceTokenIndex}→{evidence.tokenIndex}</span>
                        )}
                      </div>
                    )}

                    <div className="compare-provenance">
                      <span>{provenance.kind.replace("_", " ")}</span>
                      <strong>{provenance.label}</strong>
                      <p>{provenance.semantics}</p>
                    </div>

                    <button
                      className="compare-restore"
                      disabled={!sourceAvailable}
                      title={sourceAvailable ? "Restore evidence context" : "Source run is not loaded"}
                      onClick={() => {
                        onRestore(evidence);
                        onClose();
                      }}
                    >
                      <RotateCcw size={14} /> Restore context <ArrowRight size={14} />
                    </button>
                  </article>
                );
              })}
            </section>
          </>
        ) : (
          <div className="compare-empty">
            <GitCompareArrows size={28} />
            <h3>No pinned evidence</h3>
            <p>Pin a matrix cell or use the inspector pin button to start a comparison.</p>
          </div>
        )}
      </aside>
    </div>
  );
}

interface AttentionMatrixDeltaCell {
  destinationTokenIndex: number;
  sourceTokenIndex: number;
  baselineValue: number;
  itemValue: number;
  delta: number;
}

interface AttentionMatrixComparison {
  comparable: boolean;
  reason: string;
  sampled: boolean;
  axis: NonNullable<PinnedEvidence["matrix"]>["axis"];
  cells: Array<Array<AttentionMatrixDeltaCell | null>>;
}

function AttentionMatrixDifferenceView({
  items,
  baseline
}: {
  items: PinnedEvidence[];
  baseline: PinnedEvidence;
}) {
  const candidates = items.filter((item) =>
    item.id !== baseline.id &&
    (item.matrix !== undefined || comparisonAssessment(item, baseline).comparable)
  );
  if (!baseline.matrix && !candidates.some((item) => item.matrix)) return null;
  const rows = candidates.map((evidence) => ({
    evidence,
    itemNumber: items.findIndex((item) => item.id === evidence.id) + 1,
    comparison: compareAttentionMatrices(evidence, baseline)
  }));
  const comparableRows = rows.filter((row) => row.comparison.comparable);
  const measuredMaximum = Math.max(
    0,
    ...comparableRows.flatMap((row) =>
      row.comparison.cells.flatMap((matrixRow) =>
        matrixRow.flatMap((cell) => cell ? [Math.abs(cell.delta)] : [])
      )
    )
  );
  const scaleMaximum = Math.max(1e-12, measuredMaximum);

  return (
    <section className="compare-matrix-difference" aria-labelledby="compare-matrix-title">
      <div className="compare-matrix-heading">
        <div>
          <h3 id="compare-matrix-title">Attention matrix difference</h3>
          <p>{baseline.matrix?.label ?? "Baseline has no versioned matrix snapshot"}</p>
        </div>
        <span>{comparableRows.length}/{rows.length} aligned</span>
      </div>
      <div className="compare-matrix-scale" aria-label="Attention matrix difference scale">
        <span>{measuredMaximum === 0 ? "0" : formatDelta(-measuredMaximum)}</span>
        <i>zero delta</i>
        <span>{measuredMaximum === 0 ? "0" : formatDelta(measuredMaximum)}</span>
      </div>
      <div className="compare-matrix-rows" role="list" aria-label="Attention matrix differences">
        {rows.map(({ evidence, itemNumber, comparison }) => {
          if (!comparison.comparable) {
            return (
              <div
                key={evidence.id}
                className="compare-matrix-row incompatible"
                role="listitem"
                aria-label={`Item ${itemNumber}, attention matrix not comparable: ${comparison.reason}`}
              >
                <div className="compare-matrix-row-heading">
                  <b>Item {itemNumber} · {evidence.matrix?.label ?? evidence.tokenText}</b>
                  <span>not comparable</span>
                </div>
                <p>{comparison.reason}</p>
              </div>
            );
          }
          const peak = peakMatrixDelta(comparison.cells);
          return (
            <article
              key={evidence.id}
              className="compare-matrix-row"
              role="listitem"
              aria-label={`Item ${itemNumber}, ${comparison.axis.length} by ${comparison.axis.length} aligned attention matrix, maximum absolute delta ${formatValue(Math.abs(peak.delta))}`}
            >
              <div className="compare-matrix-row-heading">
                <b>Item {itemNumber} · {evidence.matrix?.label ?? evidence.tokenText}</b>
                <span>{comparison.axis.length}×{comparison.axis.length} {comparison.sampled ? "sampled" : "full"}</span>
              </div>
              <dl className="compare-matrix-stats">
                <div><dt>Mean |delta|</dt><dd>{formatValue(meanMatrixDelta(comparison.cells))}</dd></div>
                <div><dt>Max |delta|</dt><dd>{formatValue(Math.abs(peak.delta))}</dd></div>
                <div><dt>Peak pair</dt><dd>{peak.sourceTokenIndex}→{peak.destinationTokenIndex}</dd></div>
                <div><dt>Alignment</dt><dd>{comparison.axis.length}/{baseline.matrix?.originalSize ?? comparison.axis.length}</dd></div>
              </dl>
              <AttentionDifferenceCanvas
                evidence={evidence}
                comparison={comparison}
                scaleMaximum={scaleMaximum}
              />
              <p className="compare-matrix-contract">{comparison.reason}</p>
            </article>
          );
        })}
      </div>
      <div className="compare-matrix-legend" aria-label="Attention matrix difference legend">
        <span><i className="matrix-negative-swatch" />below baseline</span>
        <span><i className="matrix-zero-swatch" />zero delta</span>
        <span><i className="matrix-positive-swatch" />above baseline</span>
        <span><i className="matrix-mask-swatch" />causal mask</span>
      </div>
    </section>
  );
}

function AttentionDifferenceCanvas({
  evidence,
  comparison,
  scaleMaximum
}: {
  evidence: PinnedEvidence;
  comparison: AttentionMatrixComparison;
  scaleMaximum: number;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const initialRow = Math.max(0, comparison.axis.findIndex((point) => point.tokenIndex === evidence.tokenIndex));
  const initialColumn = Math.max(
    0,
    comparison.axis.findIndex((point) => point.tokenIndex === evidence.sourceTokenIndex)
  );
  const [selected, setSelected] = useState({ row: initialRow, column: initialColumn });
  const [hovered, setHovered] = useState<{ row: number; column: number } | null>(null);
  const active = hovered ?? selected;
  const activeCell = comparison.cells[active.row]?.[active.column] ?? null;
  const destination = comparison.axis[active.row];
  const source = comparison.axis[active.column];
  const selectedDescription = activeCell
    ? `Destination ${activeCell.destinationTokenIndex}, source ${activeCell.sourceTokenIndex}, baseline ${formatValue(activeCell.baselineValue)}, item ${formatValue(activeCell.itemValue)}, delta ${formatDelta(activeCell.delta)}.`
    : `Destination ${destination?.tokenIndex ?? "n/a"}, source ${source?.tokenIndex ?? "n/a"}, causal mask.`;
  const totalWidth = 58 + comparison.axis.length * 24 + 2;
  const totalHeight = 22 + comparison.axis.length * 24 + 2;
  const cellColor = (row: number, column: number) => {
    const datum = comparison.cells[row]?.[column] ?? null;
    return datum ? matrixDeltaColor(datum.delta, scaleMaximum) : "#f4f6f6";
  };

  return (
    <div className="compare-attention-matrix">
      <div className="compare-matrix-overview">
        <MatrixOverviewNavigator
          scrollRef={scrollRef}
          rowCount={comparison.axis.length}
          columnCount={comparison.axis.length}
          totalWidth={totalWidth}
          totalHeight={totalHeight}
          selectedRow={selected.row}
          selectedColumn={selected.column}
          label={`${evidence.runId} attention difference matrix`}
          revision={`${evidence.id}:${scaleMaximum}`}
          cellColor={cellColor}
        />
      </div>
      <div ref={scrollRef} className="compare-attention-matrix-scroll specialized-canvas-mode">
        <SpecializedMatrixCanvas
          scrollRef={scrollRef}
          rowCount={comparison.axis.length}
          columnCount={comparison.axis.length}
          rowHeight={22}
          columnWidth={22}
          rowLabelWidth={58}
          gap={2}
          axesPinned
          selectedRow={selected.row}
          selectedColumn={selected.column}
          ariaLabel={`${evidence.runId} attention difference matrix, ${comparison.axis.length} destination rows by ${comparison.axis.length} source columns`}
          selectedDescription={selectedDescription}
          overviewRevision={`${evidence.id}:${scaleMaximum}`}
          showOverview={false}
          cornerLabel="dest"
          rowLabel={(row) => `D${comparison.axis[row]?.tokenIndex ?? row}`}
          columnLabel={(column) => String(comparison.axis[column]?.tokenIndex ?? column)}
          cell={(row, column) => {
            const datum = comparison.cells[row]?.[column] ?? null;
            return datum
              ? {
                  fill: cellColor(row, column),
                  label: `Destination ${datum.destinationTokenIndex}, source ${datum.sourceTokenIndex}, delta ${formatDelta(datum.delta)}`
                }
              : {
                  fill: "#f4f6f6",
                  hatch: "#cfd9dc",
                  disabled: true,
                  label: "Causal mask"
                };
          }}
          navigate={(position, key) => navigateCausalMatrix(position, key, comparison.axis.length)}
          onSelect={(row, column) => setSelected({ row, column })}
          onHover={(row, column) => setHovered({ row, column })}
          onHoverEnd={() => setHovered(null)}
        />
      </div>
      <div className="compare-matrix-cell-detail" aria-live="polite">
        <span><b>Destination</b>{destination ? `${visibleToken(destination.tokenText)} · ${destination.tokenIndex}` : "n/a"}</span>
        <span><b>Source</b>{source ? `${visibleToken(source.tokenText)} · ${source.tokenIndex}` : "n/a"}</span>
        <span><b>Baseline</b>{activeCell ? formatValue(activeCell.baselineValue) : "causal mask"}</span>
        <span><b>Item</b>{activeCell ? formatValue(activeCell.itemValue) : "causal mask"}</span>
        <span><b>Delta</b>{activeCell ? formatDelta(activeCell.delta) : "unavailable"}</span>
      </div>
    </div>
  );
}

function compareAttentionMatrices(item: PinnedEvidence, baseline: PinnedEvidence): AttentionMatrixComparison {
  const pointAssessment = comparisonAssessment(item, baseline);
  if (!pointAssessment.comparable) {
    return { comparable: false, reason: pointAssessment.reason, sampled: false, axis: [], cells: [] };
  }
  if (!baseline.matrix) {
    return { comparable: false, reason: "Baseline has no versioned attention matrix snapshot.", sampled: false, axis: [], cells: [] };
  }
  if (!item.matrix) {
    return { comparable: false, reason: "Item has no versioned attention matrix snapshot.", sampled: false, axis: [], cells: [] };
  }
  if (
    item.matrix.schemaVersion !== baseline.matrix.schemaVersion ||
    item.matrix.kind !== baseline.matrix.kind
  ) {
    return { comparable: false, reason: "Matrix kind or schema version differs.", sampled: false, axis: [], cells: [] };
  }

  let axis = baseline.matrix.axis;
  let itemPositions = new Map(item.matrix.axis.map((point, index) => [point.tokenIndex, index]));
  if (runKey(item) === runKey(baseline)) {
    axis = baseline.matrix.axis.filter((point) => itemPositions.has(point.tokenIndex));
    const minimumCoverage = Math.ceil(Math.min(baseline.matrix.axis.length, item.matrix.axis.length) * 0.9);
    if (axis.length < Math.max(2, minimumCoverage)) {
      return { comparable: false, reason: "Matrix snapshots do not cover the same token axes.", sampled: false, axis: [], cells: [] };
    }
  } else {
    const exactAxes = item.modelName !== undefined && item.modelName === baseline.modelName &&
      item.matrix.originalSize === baseline.matrix.originalSize &&
      item.matrix.axis.length === baseline.matrix.axis.length &&
      baseline.matrix.axis.every((point, index) => {
        const candidate = item.matrix?.axis[index];
        return candidate !== undefined &&
          point.tokenIndex === candidate.tokenIndex &&
          point.tokenId !== undefined && candidate.tokenId !== undefined &&
          point.tokenId === candidate.tokenId &&
          normalizeTokenText(point.tokenText) === normalizeTokenText(candidate.tokenText);
      });
    if (!exactAxes) {
      return {
        comparable: false,
        reason: "Cross-run matrices require exact model/tokenizer and point-by-point token axes.",
        sampled: false,
        axis: [],
        cells: []
      };
    }
    itemPositions = new Map(item.matrix.axis.map((point, index) => [point.tokenIndex, index]));
  }

  const baselinePositions = new Map(baseline.matrix.axis.map((point, index) => [point.tokenIndex, index]));
  const cells = axis.map((destination) => axis.map((source) => {
    const baselineRow = baselinePositions.get(destination.tokenIndex);
    const baselineColumn = baselinePositions.get(source.tokenIndex);
    const itemRow = itemPositions.get(destination.tokenIndex);
    const itemColumn = itemPositions.get(source.tokenIndex);
    if (
      baselineRow === undefined || baselineColumn === undefined ||
      itemRow === undefined || itemColumn === undefined
    ) return null;
    const baselineValue = baseline.matrix!.values[baselineRow]?.[baselineColumn];
    const itemValue = item.matrix!.values[itemRow]?.[itemColumn];
    if (baselineValue === null || baselineValue === undefined || itemValue === null || itemValue === undefined) {
      return null;
    }
    return {
      destinationTokenIndex: destination.tokenIndex,
      sourceTokenIndex: source.tokenIndex,
      baselineValue,
      itemValue,
      delta: itemValue - baselineValue
    };
  }));
  if (!cells.some((row) => row.some((cell) => cell !== null))) {
    return { comparable: false, reason: "Aligned matrices contain no comparable causal cells.", sampled: false, axis: [], cells: [] };
  }
  return {
    comparable: true,
    reason: runKey(item) === runKey(baseline)
      ? "Aligned by exact token index within the same sample."
      : "Aligned by exact model/tokenizer and point-by-point token identity across runs.",
    sampled: baseline.matrix.sampled || item.matrix.sampled || axis.length < baseline.matrix.originalSize,
    axis,
    cells
  };
}

function matrixDeltaColor(delta: number, maximum: number) {
  const strength = Math.min(1, Math.abs(delta) / maximum);
  if (Math.abs(delta) < 1e-12) return "#edf2f2";
  return delta > 0
    ? `rgba(24, 122, 113, ${0.16 + strength * 0.78})`
    : `rgba(163, 63, 104, ${0.16 + strength * 0.78})`;
}

function navigateCausalMatrix(
  position: { row: number; column: number },
  key: string,
  size: number
) {
  let { row, column } = position;
  if (key === "ArrowLeft") column -= 1;
  if (key === "ArrowRight") column += 1;
  if (key === "ArrowUp") row -= 1;
  if (key === "ArrowDown") row += 1;
  if (key === "Home") column = 0;
  if (key === "End") column = row;
  row = Math.max(0, Math.min(size - 1, row));
  column = Math.max(0, Math.min(row, column));
  return { row, column };
}

function matrixCells(cells: AttentionMatrixComparison["cells"]) {
  return cells.flatMap((row) => row.flatMap((cell) => cell ? [cell] : []));
}

function meanMatrixDelta(cells: AttentionMatrixComparison["cells"]) {
  const available = matrixCells(cells);
  return available.reduce((total, cell) => total + Math.abs(cell.delta), 0) / Math.max(1, available.length);
}

function maxMatrixDelta(cells: AttentionMatrixComparison["cells"]) {
  return matrixCells(cells).reduce((maximum, cell) => Math.max(maximum, Math.abs(cell.delta)), 0);
}

function peakMatrixDelta(cells: AttentionMatrixComparison["cells"]) {
  const available = matrixCells(cells);
  return available.reduce((peak, cell) =>
    Math.abs(cell.delta) > Math.abs(peak.delta) ? cell : peak
  , available[0]);
}

function GenerationDifferenceView({
  items,
  baseline
}: {
  items: PinnedEvidence[];
  baseline: PinnedEvidence;
}) {
  const rows = items.flatMap((evidence, index) => evidence.generation
    ? [{ evidence, itemNumber: index + 1, generation: evidence.generation }]
    : []
  );
  const compatibleCount = rows.filter((row) => compareGenerations(row.evidence, baseline).comparable).length;

  return (
    <section className="compare-generation-diff" aria-labelledby="compare-generation-title">
      <div className="compare-generation-heading">
        <div>
          <h3 id="compare-generation-title">Intervention generation differences</h3>
          <p>Authoritative original→steered token edits</p>
        </div>
        <span>{compatibleCount}/{rows.length} baseline-compatible</span>
      </div>
      <div className="compare-generation-rows" role="list" aria-label="Intervention generation differences">
        {rows.map(({ evidence, itemNumber, generation }) => {
          const assessment = compareGenerations(evidence, baseline);
          const originalKinds = generationTokenKinds(generation, "original");
          const steeredKinds = generationTokenKinds(generation, "steered");
          const summary = generationDiffSummary(generation.diff);
          return (
            <article
              key={evidence.id}
              className={`compare-generation-row ${evidence.id === baseline.id ? "baseline" : ""}`}
              role="listitem"
              aria-label={`${evidence.id === baseline.id ? "Baseline" : `Item ${itemNumber}`}, ${generation.generationChanged ? "generation changed" : "generation unchanged"}, token edit distance ${generation.tokenEditDistance}`}
            >
              <header className="compare-generation-row-heading">
                <div>
                  <span>{evidence.id === baseline.id ? "Baseline" : `Item ${itemNumber}`}</span>
                  <strong>{evidence.runId} · L{generation.layer} · {generation.component} · scale {formatValue(generation.scale)}</strong>
                </div>
                <em className={assessment.comparable ? "compatible" : "standalone"}>
                  {evidence.id === baseline.id
                    ? "baseline config"
                    : assessment.comparable
                      ? "baseline-compatible"
                      : "standalone diff"}
                </em>
              </header>
              <dl className="compare-generation-metrics">
                <div><dt>Edit distance</dt><dd>{generation.tokenEditDistance}</dd></div>
                <div><dt>Target logit Δ</dt><dd>{formatDelta(generation.steered.targetLogit - generation.original.targetLogit)}</dd></div>
                <div><dt>Token edits</dt><dd>{summary.changed}</dd></div>
                <div><dt>Output</dt><dd>{generation.generationChanged ? "changed" : "unchanged"}</dd></div>
              </dl>
              <div className="compare-generation-outputs">
                <GenerationOutput title="Original" output={generation.original} kinds={originalKinds} />
                <GenerationOutput title="Steered" output={generation.steered} kinds={steeredKinds} />
              </div>
              <div className="compare-generation-contract">
                <span>{assessment.reason}</span>
                <span>
                  seed {generation.seed} · {generation.maxNewTokens} tokens · temp {formatValue(generation.temperature)} · target {visibleToken(generation.targetTokenText)} ({generation.targetTokenId})
                </span>
                <span>
                  source {generation.sourceRun.runId} / {generation.sourceRun.sampleId} · {summary.equal} equal · {summary.replace} replace · {summary.insert} insert · {summary.delete} delete
                </span>
              </div>
            </article>
          );
        })}
      </div>
      <div className="compare-generation-legend" aria-label="Generation difference legend">
        <span><i className="generation-equal-swatch" />equal</span>
        <span><i className="generation-replace-swatch" />replace</span>
        <span><i className="generation-insert-swatch" />insert</span>
        <span><i className="generation-delete-swatch" />delete</span>
      </div>
    </section>
  );
}

function GenerationOutput({
  title,
  output,
  kinds
}: {
  title: string;
  output: NonNullable<PinnedEvidence["generation"]>["original"];
  kinds: Map<number, "equal" | "replace" | "delete" | "insert">;
}) {
  return (
    <div className="compare-generation-output">
      <header>
        <strong>{title}</strong>
        <span>logit {formatValue(output.targetLogit)} · lexical {formatValue(output.lexicalRisk)}</span>
      </header>
      <p>{output.text || "No continuation text"}</p>
      <div className="compare-generation-tokens" aria-hidden="true">
        {output.tokens.length > 0
          ? output.tokens.map((token) => (
              <span
                key={token.index}
                className={kinds.get(token.index) ?? "equal"}
                title={`token ${token.index} · id ${token.tokenId}`}
              >
                <b>{token.index}</b>{visibleToken(token.text)}
              </span>
            ))
          : <span className="empty">empty</span>}
      </div>
    </div>
  );
}

function compareGenerations(item: PinnedEvidence, baseline: PinnedEvidence) {
  if (!item.generation) {
    return { comparable: false, reason: "Item has no versioned generation snapshot." };
  }
  if (item.id === baseline.id) {
    return { comparable: true, reason: "Reference generation configuration." };
  }
  if (!baseline.generation) {
    return { comparable: false, reason: "Selected baseline has no generation snapshot." };
  }
  if (!item.modelName || item.modelName !== baseline.modelName) {
    return { comparable: false, reason: "Model/tokenizer differs from the baseline." };
  }
  if (
    item.generation.sourceRun.runId !== baseline.generation.sourceRun.runId ||
    item.generation.sourceRun.sampleId !== baseline.generation.sourceRun.sampleId
  ) {
    return { comparable: false, reason: "Source Run/Sample differs from the baseline." };
  }
  if (item.generation.targetTokenId !== baseline.generation.targetTokenId) {
    return { comparable: false, reason: "Target token differs from the baseline." };
  }
  if (
    item.generation.seed !== baseline.generation.seed ||
    item.generation.maxNewTokens !== baseline.generation.maxNewTokens ||
    item.generation.temperature !== baseline.generation.temperature
  ) {
    return { comparable: false, reason: "Generation seed, token budget, or temperature differs." };
  }
  if (!sameGeneratedTokens(item.generation.original.tokens, baseline.generation.original.tokens)) {
    return { comparable: false, reason: "Original generation tokens differ from the baseline." };
  }
  return {
    comparable: true,
    reason: "Matched model, source, target, generation parameters, and original token sequence."
  };
}

function sameGeneratedTokens(
  left: NonNullable<PinnedEvidence["generation"]>["original"]["tokens"],
  right: NonNullable<PinnedEvidence["generation"]>["original"]["tokens"]
) {
  return left.length === right.length && left.every((token, index) => {
    const candidate = right[index];
    return candidate !== undefined && token.tokenId === candidate.tokenId && token.text === candidate.text;
  });
}

function generationTokenKinds(
  generation: NonNullable<PinnedEvidence["generation"]>,
  side: "original" | "steered"
) {
  const result = new Map<number, "equal" | "replace" | "delete" | "insert">();
  for (const row of generation.diff) {
    const start = side === "original" ? row.originalStart : row.steeredStart;
    const end = side === "original" ? row.originalEnd : row.steeredEnd;
    for (let index = start; index < end; index += 1) result.set(index, row.kind);
  }
  return result;
}

function generationDiffSummary(diff: NonNullable<PinnedEvidence["generation"]>["diff"]) {
  const result = { equal: 0, replace: 0, insert: 0, delete: 0, changed: 0 };
  for (const row of diff) {
    const originalLength = row.originalEnd - row.originalStart;
    const steeredLength = row.steeredEnd - row.steeredStart;
    if (row.kind === "equal") result.equal += originalLength;
    if (row.kind === "replace") result.replace += Math.max(originalLength, steeredLength);
    if (row.kind === "insert") result.insert += steeredLength;
    if (row.kind === "delete") result.delete += originalLength;
  }
  result.changed = result.replace + result.insert + result.delete;
  return result;
}

function visibleToken(value: string) {
  return value || "␠";
}

interface ProfileDeltaPoint extends EvidenceProfilePoint {
  baselineValue: number;
  itemValue: number;
  delta: number;
}

interface ProfileComparison {
  comparable: boolean;
  reason: string;
  points: ProfileDeltaPoint[];
}

function ProfileDifferencePlot({
  items,
  baseline
}: {
  items: PinnedEvidence[];
  baseline: PinnedEvidence;
}) {
  const candidates = items.filter((item) =>
    item.id !== baseline.id &&
    (item.profile !== undefined || comparisonAssessment(item, baseline).comparable)
  );
  if (!baseline.profile && !candidates.some((item) => item.profile)) return null;

  const rows = candidates.map((evidence) => ({
    evidence,
    itemNumber: items.findIndex((item) => item.id === evidence.id) + 1,
    comparison: compareProfiles(evidence, baseline)
  }));
  const comparableRows = rows.filter((row) => row.comparison.comparable);
  const measuredMaximum = Math.max(
    0,
    ...comparableRows.flatMap((row) => row.comparison.points.map((point) => Math.abs(point.delta)))
  );
  const maximum = Math.max(1e-12, measuredMaximum);
  const title = baseline.profile?.kind === "attention_source_profile"
    ? "Attention row difference"
    : baseline.profile?.kind === "signed_attribution_profile"
      ? "Signed attribution difference"
      : baseline.profile?.kind === "mlp_activation_profile"
        ? "MLP activation profile difference"
      : "Profile difference";

  return (
    <section className="compare-profile-plot" aria-labelledby="compare-profile-title">
      <div className="compare-profile-heading">
        <div>
          <h3 id="compare-profile-title">{title}</h3>
          <p>
            {baseline.profile?.label ?? "Baseline has no profile snapshot"}
            {baseline.profile?.sampled
              ? ` · ${baseline.profile.points.length}/${baseline.profile.originalLength} sampled points`
              : baseline.profile
                ? ` · ${baseline.profile.originalLength} points`
                : ""}
          </p>
        </div>
        <span>{comparableRows.length}/{rows.length} aligned</span>
      </div>
      <div className="compare-profile-scale" aria-hidden="true">
        <span>{measuredMaximum === 0 ? "0" : formatDelta(-measuredMaximum)}</span>
        <i>zero delta</i>
        <span>{measuredMaximum === 0 ? "0" : formatDelta(measuredMaximum)}</span>
      </div>
      <div className="compare-profile-rows" role="list" aria-label="Token profile differences">
        {rows.map(({ evidence, itemNumber, comparison }, index) => {
          if (!comparison.comparable) {
            return (
              <div
                key={evidence.id}
                className="compare-profile-row incompatible"
                role="listitem"
                aria-label={`${evidence.tokenText}, profile not comparable: ${comparison.reason}`}
              >
                <div className="compare-profile-row-heading">
                  <b>Item {itemNumber} · {evidence.profile?.label ?? evidence.tokenText}</b>
                  <span>not comparable</span>
                </div>
                <p>{comparison.reason}</p>
              </div>
            );
          }

          const mean = meanAbsoluteDelta(comparison.points);
          const peak = peakProfileDelta(comparison.points);
          const path = profilePath(comparison.points, maximum);
          return (
            <div
              key={evidence.id}
              className="compare-profile-row"
              role="listitem"
              aria-label={`${evidence.profile?.label ?? evidence.tokenText}, ${comparison.points.length} aligned points, mean absolute delta ${formatValue(mean)}, peak ${formatDelta(peak.delta)} at token ${peak.tokenIndex}`}
            >
              <div className="compare-profile-row-heading">
                <b>Item {itemNumber} · {evidence.profile?.label ?? evidence.tokenText}</b>
                <span>{comparison.points.length} aligned</span>
              </div>
              <svg
                className="compare-profile-chart"
                viewBox="0 0 640 88"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <defs>
                  <clipPath id={`profile-positive-${index}`}><rect x="0" y="0" width="640" height="44" /></clipPath>
                  <clipPath id={`profile-negative-${index}`}><rect x="0" y="44" width="640" height="44" /></clipPath>
                </defs>
                <line className="compare-profile-zero" x1="0" y1="44" x2="640" y2="44" />
                <path className="compare-profile-area" d={`${path} L 640 44 L 0 44 Z`} />
                <path className="compare-profile-line positive" d={path} clipPath={`url(#profile-positive-${index})`} />
                <path className="compare-profile-line negative" d={path} clipPath={`url(#profile-negative-${index})`} />
              </svg>
              <dl className="compare-profile-stats">
                <div><dt>Mean |delta|</dt><dd>{formatValue(mean)}</dd></div>
                <div><dt>Peak delta</dt><dd>{formatDelta(peak.delta)}</dd></div>
                <div><dt>Peak token</dt><dd>{peak.tokenText || "␠"} · {peak.tokenIndex}</dd></div>
              </dl>
            </div>
          );
        })}
      </div>
      <div className="compare-profile-legend" aria-label="Profile difference legend">
        <span><i className="profile-positive-swatch" />above baseline</span>
        <span><i className="profile-negative-swatch" />below baseline</span>
        <span><i className="profile-zero-swatch" />zero delta</span>
      </div>
    </section>
  );
}

function compareProfiles(item: PinnedEvidence, baseline: PinnedEvidence): ProfileComparison {
  const pointAssessment = comparisonAssessment(item, baseline);
  if (!pointAssessment.comparable) {
    return { comparable: false, reason: pointAssessment.reason, points: [] };
  }
  if (!baseline.profile) {
    return { comparable: false, reason: "Baseline has no versioned profile snapshot.", points: [] };
  }
  if (!item.profile) {
    return { comparable: false, reason: "Item has no versioned profile snapshot.", points: [] };
  }
  if (
    item.profile.schemaVersion !== baseline.profile.schemaVersion ||
    item.profile.kind !== baseline.profile.kind ||
    item.profile.axis !== baseline.profile.axis ||
    item.profile.signed !== baseline.profile.signed
  ) {
    return { comparable: false, reason: "Profile kind, axis, or signedness differs.", points: [] };
  }

  if (runKey(item) === runKey(baseline)) {
    const itemByToken = new Map(item.profile.points.map((point) => [point.tokenIndex, point]));
    const points = baseline.profile.points.flatMap((baselinePoint) => {
      const itemPoint = itemByToken.get(baselinePoint.tokenIndex);
      if (!itemPoint) return [];
      return [{
        ...baselinePoint,
        baselineValue: baselinePoint.value,
        itemValue: itemPoint.value,
        delta: itemPoint.value - baselinePoint.value
      }];
    });
    const minimumCoverage = Math.ceil(Math.min(baseline.profile.points.length, item.profile.points.length) * 0.9);
    if (points.length < Math.max(2, minimumCoverage)) {
      return { comparable: false, reason: "Profile snapshots do not cover the same token axis.", points: [] };
    }
    return {
      comparable: true,
      reason: "Aligned by exact token index within the same sample.",
      points
    };
  }

  const exactAxis = baseline.profile.originalLength === item.profile.originalLength &&
    baseline.profile.points.length === item.profile.points.length &&
    item.modelName !== undefined &&
    item.modelName === baseline.modelName &&
    baseline.profile.points.every((baselinePoint, index) => {
      const itemPoint = item.profile?.points[index];
      return itemPoint !== undefined &&
        itemPoint.tokenId !== undefined &&
        baselinePoint.tokenId !== undefined &&
        itemPoint.tokenId === baselinePoint.tokenId &&
        normalizeTokenText(itemPoint.tokenText) === normalizeTokenText(baselinePoint.tokenText);
    });
  if (!exactAxis) {
    return {
      comparable: false,
      reason: "Cross-run profiles require an exact point-by-point tokenizer and token sequence match.",
      points: []
    };
  }
  return {
    comparable: true,
    reason: "Aligned by exact point-by-point token identity across runs.",
    points: baseline.profile.points.map((baselinePoint, index) => {
      const itemPoint = item.profile!.points[index];
      return {
        ...baselinePoint,
        baselineValue: baselinePoint.value,
        itemValue: itemPoint.value,
        delta: itemPoint.value - baselinePoint.value
      };
    })
  };
}

function profilePath(points: ProfileDeltaPoint[], maximum: number) {
  return points.map((point, index) => {
    const x = points.length === 1 ? 320 : index * 640 / (points.length - 1);
    const y = 44 - point.delta / maximum * 38;
    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
}

function meanAbsoluteDelta(points: ProfileDeltaPoint[]) {
  return points.reduce((total, point) => total + Math.abs(point.delta), 0) / Math.max(1, points.length);
}

function maxAbsoluteDelta(points: ProfileDeltaPoint[]) {
  return points.reduce((maximum, point) => Math.max(maximum, Math.abs(point.delta)), 0);
}

function peakProfileDelta(points: ProfileDeltaPoint[]) {
  return points.reduce((peak, point) =>
    Math.abs(point.delta) > Math.abs(peak.delta) ? point : peak
  , points[0]);
}

function ComparisonDeltaPlot({
  items,
  baseline
}: {
  items: PinnedEvidence[];
  baseline: PinnedEvidence;
}) {
  const rows = items.map((evidence) => {
    const assessment = comparisonAssessment(evidence, baseline);
    return {
      evidence,
      assessment,
      delta: assessment.comparable ? evidence.value - baseline.value : undefined
    };
  });
  const maximum = Math.max(
    1e-12,
    ...rows.flatMap((row) => row.delta === undefined ? [] : [Math.abs(row.delta)])
  );
  const comparableRows = rows.filter((row) => row.assessment.comparable);
  const distinctLayers = new Set(comparableRows.map((row) => row.evidence.layer)).size;
  const sameToken = comparableRows.every((row) =>
    normalizeTokenText(row.evidence.tokenText) === normalizeTokenText(baseline.tokenText)
  );
  const title = distinctLayers > 1 && sameToken
    ? "Layer delta profile"
    : baseline.view === "attention"
      ? "Attention delta profile"
      : baseline.view === "attribution"
        ? "Attribution delta profile"
        : "Baseline delta profile";

  return (
    <section className="compare-delta-plot" aria-labelledby="compare-delta-title">
      <div className="compare-delta-heading">
        <div>
          <h3 id="compare-delta-title">{title}</h3>
          <p>{formatMetric(baseline.metric)} · {baseline.normalization} · centered on {formatValue(baseline.value)}</p>
        </div>
        <span>{comparableRows.length}/{rows.length} comparable</span>
      </div>
      <div className="compare-delta-axis" aria-hidden="true">
        <span>negative</span><i>baseline</i><span>positive</span>
      </div>
      <div className="compare-delta-rows" role="list" aria-label="Baseline-centered evidence deltas">
        {rows.map(({ evidence, assessment, delta }, index) => {
          const baselineRow = evidence.id === baseline.id;
          const direction = delta === undefined
            ? "incompatible"
            : Math.abs(delta) < 1e-12
              ? "zero"
              : delta > 0 ? "positive" : "negative";
          return (
            <div
              key={evidence.id}
              className={`compare-delta-row delta-${direction} ${baselineRow ? "baseline" : ""}`}
              role="listitem"
              aria-label={baselineRow
                ? `${evidence.tokenText}, baseline value ${formatValue(evidence.value)}`
                : assessment.comparable
                  ? `${evidence.tokenText}, ${formatDelta(delta ?? 0)} versus baseline`
                  : `${evidence.tokenText}, not comparable: ${assessment.reason}`}
            >
              <span className="compare-delta-label">
                <b>{baselineRow ? "Baseline" : `Item ${index + 1}`}</b>
                <em title={`${evidence.runId} / ${evidence.sampleId} · ${evidence.tokenText || "␠"} · L${evidence.layer}`}>
                  {evidence.runId} · {evidence.tokenText || "␠"} · L{evidence.layer}
                </em>
              </span>
              <span
                className="compare-delta-track"
                aria-hidden="true"
                style={{
                  "--delta-fraction": delta === undefined ? 0 : Math.abs(delta) / maximum
                } as CSSProperties}
              >
                <i className="compare-delta-center" />
                {assessment.comparable && !baselineRow && <b className="compare-delta-bar" />}
                {baselineRow && <b className="compare-delta-baseline-marker" />}
              </span>
              <span className="compare-delta-exact">
                {baselineRow
                  ? "0 baseline"
                  : assessment.comparable
                    ? formatDelta(delta ?? 0)
                    : "not comparable"}
              </span>
            </div>
          );
        })}
      </div>
      <div className="compare-delta-legend" aria-label="Delta plot legend">
        <span><i className="delta-negative-swatch" />negative delta</span>
        <span><i className="delta-positive-swatch" />positive delta</span>
        <span><i className="delta-incompatible-swatch" />not comparable</span>
      </div>
    </section>
  );
}

interface TokenAlignment {
  status: "baseline" | "same-sample" | "exact" | "text-only" | "position-only" | "unaligned";
  label: string;
  reason: string;
  compatible: boolean;
}

function alignTokens(item: PinnedEvidence, baseline: PinnedEvidence): TokenAlignment {
  if (item.id === baseline.id) {
    return {
      status: "baseline",
      label: "Baseline token",
      reason: "Reference evidence for this comparison.",
      compatible: true
    };
  }
  if (runKey(item) === runKey(baseline)) {
    return {
      status: "same-sample",
      label: "Same sample",
      reason: "Both observations come from the same token sequence.",
      compatible: true
    };
  }
  const sameTokenizer = item.modelName !== undefined && item.modelName === baseline.modelName;
  const sameTokenId = item.tokenId !== undefined && item.tokenId === baseline.tokenId;
  const sameText = normalizeTokenText(item.tokenText) === normalizeTokenText(baseline.tokenText);
  if (sameTokenizer && sameTokenId && sameText) {
    return {
      status: "exact",
      label: "Exact token alignment",
      reason: "Model/tokenizer, token id, and decoded text match across runs.",
      compatible: true
    };
  }
  if (sameText) {
    return {
      status: "text-only",
      label: "Text-only alignment",
      reason: "Decoded text matches, but tokenizer identity or token id differs.",
      compatible: true
    };
  }
  if (item.tokenIndex === baseline.tokenIndex) {
    return {
      status: "position-only",
      label: "Position-only match",
      reason: "Positions match but token text differs; no delta is calculated.",
      compatible: false
    };
  }
  return {
    status: "unaligned",
    label: "Unaligned token",
    reason: "No exact or decoded-text token alignment is available.",
    compatible: false
  };
}

function comparisonAssessment(item: PinnedEvidence, baseline: PinnedEvidence) {
  const alignment = alignTokens(item, baseline);
  if (item.metric !== baseline.metric) {
    return { comparable: false, reason: "Different metric; no delta." };
  }
  if (item.normalization !== baseline.normalization) {
    return { comparable: false, reason: "Different normalization; no delta." };
  }
  const itemKind = item.provenance?.kind;
  const baselineKind = baseline.provenance?.kind;
  if (itemKind && baselineKind && itemKind !== baselineKind) {
    return { comparable: false, reason: "Different evidence class; no delta." };
  }
  if (!alignment.compatible) {
    return { comparable: false, reason: alignment.reason };
  }
  return { comparable: true, reason: "Comparable with the selected baseline." };
}

function formatValue(value: number, metric?: string) {
  if (metric) return formatMetricNumber(value, metric, "compact");
  if (Math.abs(value) >= 100) {
    return value.toFixed(1);
  }
  if (Math.abs(value) < 0.01 && value !== 0) {
    return value.toExponential(2);
  }
  return value.toFixed(3);
}

function formatHeadSelection(headId: string) {
  const difference = parseAttentionDifference(headId);
  if (difference) return `${difference.selectedHeadId} - ${difference.baselineHeadId}`;
  if (parseAttentionRollout(headId)) return "Retained attention rollout";
  const aggregation = parseAttentionAggregation(headId);
  return aggregation ? attentionAggregationLabel(aggregation) : headId;
}

function formatDelta(value: number, metric?: string) {
  if (metric) return formatRegisteredDelta(value, metric, "compact");
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${formatValue(value)}`;
}

function deltaTone(delta: number | undefined, canCompare: boolean) {
  if (!canCompare || delta === undefined || Math.abs(delta) < 1e-9) {
    return "neutral";
  }
  return delta > 0 ? "positive" : "negative";
}

function formatMetric(metric: string) {
  return metricDisplayLabel(metric);
}

function labelView(view: PinnedEvidence["view"]) {
  return view.charAt(0).toUpperCase() + view.slice(1);
}

function resolveProvenance(
  evidence: PinnedEvidence,
  provenance: Record<string, MetricProvenance>
): MetricProvenance {
  if (evidence.provenance) return evidence.provenance;
  if (evidence.metric === "residual_norm") {
    return {
      label: "Residual activation norm",
      method: "L2 norm over resid_post",
      semantics: "Raw activation magnitude; high norm does not imply high safety risk.",
      normalization: "min-max over layer-token values",
      kind: "raw"
    };
  }
  const key =
    evidence.metric === "tokenRisk" || evidence.metric === "token_safety_proxy"
      ? "tokenRisk"
      : evidence.metric === "residual_direction"
        ? "residualHeatmap"
        : evidence.metric === "attention_concentration" || evidence.metric === "attention_probability"
          ? "attentionHeatmap"
          : evidence.metric.startsWith("mlp_")
            ? "mlpNeuronActivation"
            : evidence.metric === "final_attention_proxy" || evidence.view === "attribution"
              ? "tokenAttribution"
              : "tokenRisk";
  return provenance[key] ?? provenance.tokenRisk;
}

function runKey(evidence: Pick<PinnedEvidence, "runId" | "sampleId">) {
  return `${evidence.runId}::${evidence.sampleId}`;
}

function normalizeTokenText(value: string) {
  return value.replace(/\s+/g, " ").trim();
}
