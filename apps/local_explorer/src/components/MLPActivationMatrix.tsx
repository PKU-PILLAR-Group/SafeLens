import { useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, GitFork, LoaderCircle, Pin, Search } from "lucide-react";

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
import { formatMetricDelta as formatRegisteredDelta, formatMetricNumber } from "../metricFormatting";
import type { MLPNeuron, TokenInfo } from "../types";

interface MLPActivationMatrixProps {
  tokens: TokenInfo[];
  neurons: MLPNeuron[];
  selectedToken: number;
  selectedNeuronId: string;
  partialProfiles: boolean;
  metric: string;
  selectedRange?: [number, number];
  onMetricChange: (metric: string) => void;
  onSelectToken: (token: number) => void;
  onSelectNeuron: (neuronId: string) => void;
  onRangeSelect: (range?: [number, number]) => void;
  onHoverToken: (token: number | null) => void;
  onPin: () => void;
  onPinActivation: (token: number, neuronId: string) => void;
}

interface ClusterWorkerResult {
  id: number;
  clusters?: Array<{ indices: number[]; height: number }>;
  error?: string;
}

interface MLPClusterGroup {
  members: Array<{
    neuron: MLPNeuron;
    correlation: number;
  }>;
  representative: MLPNeuron;
  meanAbsoluteCorrelation: number;
  height: number;
  selected: boolean;
}

const MAX_CLUSTER_NEURONS = 64;

interface HoveredActivation {
  neuron: MLPNeuron;
  tokenIndex: number;
  value: number;
}

export function MLPActivationMatrix({
  tokens,
  neurons,
  selectedToken,
  selectedNeuronId,
  partialProfiles,
  metric,
  selectedRange,
  onMetricChange,
  onSelectToken,
  onSelectNeuron,
  onRangeSelect,
  onHoverToken,
  onPin,
  onPinActivation
}: MLPActivationMatrixProps) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [threshold, setThreshold] = useState(0);
  const [hovered, setHovered] = useState<HoveredActivation | null>(null);
  const [comparisonActivation, setComparisonActivation] = useState<{
    tokenIndex: number;
    neuronId: string;
  } | null>(null);
  const [clusterSimilarity, setClusterSimilarity] = useState(0.8);
  const [clusterStatus, setClusterStatus] = useState<"loading" | "ready" | "error">("loading");
  const [clusterError, setClusterError] = useState("");
  const [rawClusters, setRawClusters] = useState<Array<{ indices: number[]; height: number }>>([]);
  const gridRef = useRef<HTMLDivElement>(null);
  const clusterWorkerRef = useRef<Worker | null>(null);
  const clusterRequestRef = useRef(0);
  const maximum = useMemo(() => {
    let result = 1e-12;
    for (const neuron of neurons) {
      for (const value of neuron.activationsByToken) result = Math.max(result, Math.abs(value));
    }
    return result;
  }, [neurons]);
  const neuronSearchIndex = useMemo(() => neurons.map((neuron) => ({
    neuron,
    searchable: `${neuron.id.toLowerCase()} ${neuron.neuron}`
  })), [neurons]);
  useEffect(() => {
    setComparisonActivation(null);
  }, [neurons, tokens]);
  const visibleNeurons = useMemo(() => {
    const normalizedQuery = deferredQuery.trim().toLowerCase();
    return neuronSearchIndex.flatMap((entry) =>
      normalizedQuery.length === 0 || entry.searchable.includes(normalizedQuery)
        ? [entry.neuron]
        : []
    );
  }, [deferredQuery, neuronSearchIndex]);
  useEffect(() => {
    if (deferredQuery !== query) return;
    if (
      visibleNeurons.length > 0 &&
      !visibleNeurons.some((neuron) => neuron.id === selectedNeuronId)
    ) {
      onSelectNeuron(visibleNeurons[0].id);
    }
  }, [deferredQuery, onSelectNeuron, query, selectedNeuronId, visibleNeurons]);
  const selectedNeuron = useMemo(
    () => neurons.find((neuron) => neuron.id === selectedNeuronId) ?? neurons[0],
    [neurons, selectedNeuronId]
  );
  const clusteringTokenIndices = useMemo(() => {
    if (!partialProfiles) return tokens.map((token) => token.index);
    const loaded = tokens
      .map((token) => token.index)
      .filter((tokenIndex) => neurons.some(
        (neuron) => Math.abs(neuron.activationsByToken[tokenIndex] ?? 0) > 1e-12
      ));
    return loaded.length > 0 ? loaded : tokens.map((token) => token.index);
  }, [neurons, partialProfiles, tokens]);
  const clusterSamplingAnchor = useMemo(() => {
    if (neurons.length <= MAX_CLUSTER_NEURONS) return "";
    const baseline = [...neurons]
      .sort(
        (left, right) => right.maxAbsoluteActivation - left.maxAbsoluteActivation || left.neuron - right.neuron
      )
      .slice(0, MAX_CLUSTER_NEURONS);
    return baseline.some((neuron) => neuron.id === selectedNeuronId) ? "" : selectedNeuronId;
  }, [neurons, selectedNeuronId]);
  const clusterNeurons = useMemo(() => {
    const byPeak = [...neurons].sort(
      (left, right) => right.maxAbsoluteActivation - left.maxAbsoluteActivation || left.neuron - right.neuron
    );
    const retained = byPeak.slice(0, MAX_CLUSTER_NEURONS);
    const samplingAnchor = clusterSamplingAnchor
      ? neurons.find((neuron) => neuron.id === clusterSamplingAnchor)
      : undefined;
    if (samplingAnchor) {
      retained[Math.max(0, retained.length - 1)] = samplingAnchor;
    }
    return retained;
  }, [clusterSamplingAnchor, neurons]);

  useEffect(() => {
    const worker = new Worker(new URL("../workers/mlpCluster.worker.ts", import.meta.url), {
      type: "module"
    });
    clusterWorkerRef.current = worker;
    worker.addEventListener("message", (event: MessageEvent<ClusterWorkerResult>) => {
      if (event.data.id !== clusterRequestRef.current) return;
      if (event.data.error) {
        setClusterStatus("error");
        setClusterError(event.data.error);
        return;
      }
      setRawClusters(event.data.clusters ?? []);
      setClusterStatus("ready");
      setClusterError("");
    });
    worker.addEventListener("error", () => {
      setClusterStatus("error");
      setClusterError("The clustering worker could not be loaded.");
    });
    return () => {
      worker.terminate();
      clusterWorkerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const worker = clusterWorkerRef.current;
    if (!worker) return;
    const id = clusterRequestRef.current + 1;
    clusterRequestRef.current = id;
    setClusterStatus("loading");
    setClusterError("");
    worker.postMessage({
      id,
      similarityThreshold: clusterSimilarity,
      profiles: clusterNeurons.map((neuron) =>
        clusteringTokenIndices.map((tokenIndex) => neuron.activationsByToken[tokenIndex] ?? 0)
      )
    });
  }, [clusterNeurons, clusterSimilarity, clusteringTokenIndices]);

  const clusterGroups = useMemo<MLPClusterGroup[]>(() => rawClusters
    .map((cluster) => {
      const neuronsInCluster = cluster.indices.flatMap((index) =>
        clusterNeurons[index] ? [clusterNeurons[index]] : []
      );
      const representative = neuronsInCluster.find((neuron) => neuron.id === selectedNeuronId) ??
        [...neuronsInCluster].sort(
          (left, right) => right.maxAbsoluteActivation - left.maxAbsoluteActivation
        )[0];
      if (!representative) return undefined;
      const members = neuronsInCluster
        .map((neuron) => ({
          neuron,
          correlation: pearsonForTokens(
            representative.activationsByToken,
            neuron.activationsByToken,
            clusteringTokenIndices
          )
        }))
        .sort((left, right) =>
          Math.abs(right.correlation) - Math.abs(left.correlation) || left.neuron.neuron - right.neuron.neuron
        );
      return {
        members,
        representative,
        meanAbsoluteCorrelation: members.reduce(
          (total, member) => total + Math.abs(member.correlation),
          0
        ) / Math.max(1, members.length),
        height: cluster.height,
        selected: members.some((member) => member.neuron.id === selectedNeuronId)
      };
    })
    .filter((cluster): cluster is MLPClusterGroup => Boolean(cluster))
    .sort((left, right) =>
      Number(right.selected) - Number(left.selected) ||
      right.members.length - left.members.length ||
      left.representative.neuron - right.representative.neuron
    ), [clusterNeurons, clusteringTokenIndices, rawClusters, selectedNeuronId]);
  const selectedValue = selectedNeuron?.activationsByToken[selectedToken] ?? 0;
  const selectedNormalized = Math.abs(selectedValue) / maximum;
  const comparisonNeuron = comparisonActivation
    ? neurons.find((neuron) => neuron.id === comparisonActivation.neuronId)
    : undefined;
  const comparisonValue = comparisonActivation && comparisonNeuron
    ? comparisonNeuron.activationsByToken[comparisonActivation.tokenIndex] ?? 0
    : undefined;
  const comparisonNormalized = comparisonValue === undefined ? undefined : Math.abs(comparisonValue) / maximum;
  const neuronRankings = useMemo(() => {
    const entries = neurons.map((neuron) => ({
      neuron,
      value: neuron.activationsByToken[selectedToken] ?? 0
    }));
    return {
      positive: entries
        .filter((entry) => entry.value > 0)
        .sort((left, right) => right.value - left.value)
        .slice(0, 5),
      negative: entries
        .filter((entry) => entry.value < 0)
        .sort((left, right) => left.value - right.value)
        .slice(0, 5),
      maximum: Math.max(1e-12, ...entries.map((entry) => Math.abs(entry.value)))
    };
  }, [neurons, selectedToken]);
  const viewport = useMatrixViewport({
    initialSize: 30,
    minimumSize: 20,
    maximumSize: 42,
    itemCount: visibleNeurons.length,
    labelWidth: 76,
    sessionKey: "mlp"
  });
  const rangeBrush = useMatrixRangeBrush({
    enabled: viewport.mode === "select",
    selectedRange,
    onRangeSelect
  });
  const cellSize = viewport.size;
  const keyboardNeuronId = visibleNeurons.some((neuron) => neuron.id === selectedNeuronId)
    ? selectedNeuronId
    : visibleNeurons[0]?.id;
  const minGridWidth = 76 + visibleNeurons.length * cellSize + (visibleNeurons.length + 1) * 3;
  const renderMode = tokens.length * visibleNeurons.length >= SPECIALIZED_CANVAS_CELL_THRESHOLD
    ? "canvas"
    : "dom";
  const selectedTokenPosition = Math.max(0, tokens.findIndex((token) => token.index === selectedToken));
  const selectedNeuronPosition = Math.max(
    0,
    visibleNeurons.findIndex((neuron) => neuron.id === keyboardNeuronId)
  );

  function moveActivationFocus(tokenIndex: number, neuronId: string, key: string) {
    const tokenPosition = Math.max(0, tokens.findIndex((token) => token.index === tokenIndex));
    const neuronPosition = Math.max(
      0,
      visibleNeurons.findIndex((neuron) => neuron.id === neuronId)
    );
    let nextToken = tokenPosition;
    let nextNeuron = neuronPosition;
    if (key === "ArrowLeft") nextNeuron = Math.max(0, neuronPosition - 1);
    if (key === "ArrowRight") nextNeuron = Math.min(visibleNeurons.length - 1, neuronPosition + 1);
    if (key === "ArrowUp") nextToken = Math.max(0, tokenPosition - 1);
    if (key === "ArrowDown") nextToken = Math.min(tokens.length - 1, tokenPosition + 1);
    if (key === "Home") nextNeuron = 0;
    if (key === "End") nextNeuron = visibleNeurons.length - 1;
    const nextTokenIndex = tokens[nextToken]?.index;
    const nextNeuronId = visibleNeurons[nextNeuron]?.id;
    if (nextTokenIndex === undefined || nextNeuronId === undefined) return;
    onSelectToken(nextTokenIndex);
    onSelectNeuron(nextNeuronId);
    window.requestAnimationFrame(() => {
      gridRef.current
        ?.querySelector<HTMLButtonElement>(
          `[data-token="${nextTokenIndex}"][data-neuron="${nextNeuronId}"]`
        )
        ?.focus();
    });
  }

  return (
    <section className="surface mlp-matrix-section">
      <div className="surface-header">
        <div>
          <h3>MLP activation matrix</h3>
          <p>Signed hook_post activations across tokens and retained neurons.</p>
        </div>
        <span className="evidence-kind">raw activation</span>
      </div>

      <div className="mlp-matrix-toolbar" aria-label="MLP matrix controls">
        <label className="mlp-metric-control">
          <span>Display</span>
          <select value={metric} onChange={(event) => onMetricChange(event.target.value)}>
            <option value="mlp_signed_activation">Signed raw</option>
            <option value="mlp_absolute_activation">Absolute raw</option>
            <option value="mlp_normalized_activation">Normalized magnitude</option>
          </select>
        </label>
        <label className="mlp-search-control">
          <span>
            <span><Search size={12} /> Neuron search</span>
            <output aria-label="Neuron search results" aria-live="polite">
              {deferredQuery !== query ? "..." : `${visibleNeurons.length}/${neurons.length}`}
            </output>
          </span>
          <input
            aria-label="Search retained neurons"
            value={query}
            placeholder="e.g. N0004 or 4"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <label className="mlp-threshold-control">
          <span>Threshold <b>{threshold.toFixed(2)}</b></span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={threshold}
            onChange={(event) => setThreshold(Number(event.target.value))}
          />
        </label>
        <div className="toolbar-actions">
          <MatrixViewportControls viewport={viewport} label="MLP matrix" />
          <button aria-label="Pin selected MLP activation" onClick={onPin}>
            <Pin size={14} />
          </button>
        </div>
      </div>

      <div className="mlp-selection-summary" aria-label="Selected MLP activation">
        <span><b>{tokens[selectedToken]?.text || "␠"}</b>token {selectedToken}</span>
        <span><b>{selectedNeuron?.id ?? "none"}</b>neuron</span>
        <span><b>{displayValue(selectedValue, selectedNormalized, metric)}</b>{metricLabel(metric)}</span>
        <span><b>{selectedValue.toFixed(6)}</b>signed raw source</span>
      </div>
      <MatrixComparisonSummary
        label="MLP matrix"
        primary={`T${selectedToken} · ${selectedNeuron?.id ?? "none"}`}
        anchor={comparisonActivation
          ? `T${comparisonActivation.tokenIndex} · ${comparisonActivation.neuronId}`
          : undefined}
        delta={comparisonValue === undefined || comparisonNormalized === undefined
          ? undefined
          : formatMetricDelta(
              metricNumericValue(selectedValue, selectedNormalized, metric) -
              metricNumericValue(comparisonValue, comparisonNormalized, metric),
              metric
            )}
        deltaLabel="display delta"
        onClear={() => setComparisonActivation(null)}
      />
      <MatrixRangeSummary label="Token" range={selectedRange} onClear={() => onRangeSelect(undefined)} />

      <section className="mlp-neuron-rankings" aria-labelledby="mlp-neuron-rankings-title">
        <div className="mlp-neuron-rankings-heading">
          <div>
            <h4 id="mlp-neuron-rankings-title">Neuron polarity ranking</h4>
            <p>Selected token · retained neurons in layer {selectedNeuron?.layer ?? "n/a"}</p>
          </div>
          <span>raw activation</span>
        </div>
        <div className="mlp-neuron-ranking-columns">
          <MLPNeuronRankingList
            title="Top positive neurons"
            tone="positive"
            entries={neuronRankings.positive}
            maximum={neuronRankings.maximum}
            selectedNeuronId={selectedNeuronId}
            onSelect={(neuronId) => {
              setQuery("");
              onSelectNeuron(neuronId);
            }}
          />
          <MLPNeuronRankingList
            title="Top negative neurons"
            tone="negative"
            entries={neuronRankings.negative}
            maximum={neuronRankings.maximum}
            selectedNeuronId={selectedNeuronId}
            onSelect={(neuronId) => {
              setQuery("");
              onSelectNeuron(neuronId);
            }}
          />
        </div>
        <p className="mlp-neuron-ranking-note">
          Signed activation ranks response at this token only; it is not logit, probe, or causal contribution.
        </p>
      </section>

      <section className="mlp-cluster-explorer" aria-labelledby="mlp-cluster-title">
        <div className="mlp-cluster-heading">
          <div>
            <h4 id="mlp-cluster-title">Neuron profile clusters</h4>
            <p>Average-link AGNES over absolute Pearson activation-profile distance.</p>
          </div>
          <span>
            <GitFork size={13} /> {clusterGroups.length} group{clusterGroups.length === 1 ? "" : "s"}
          </span>
        </div>
        <div className="mlp-cluster-controls">
          <label>
            <span>Minimum |r| <b>{clusterSimilarity.toFixed(2)}</b></span>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={clusterSimilarity}
              onChange={(event) => setClusterSimilarity(Number(event.target.value))}
            />
          </label>
          <div className="mlp-cluster-coverage" aria-label="MLP cluster coverage">
            <span><b>{clusterNeurons.length}/{neurons.length}</b>retained neurons clustered</span>
            <span><b>{clusteringTokenIndices.length}/{tokens.length}</b>{partialProfiles ? "loaded positions only" : "full token axis"}</span>
            <span><b>{neurons.length > MAX_CLUSTER_NEURONS ? "sampled" : "complete"}</b>coverage mode</span>
          </div>
        </div>
        {clusterStatus === "loading" ? (
          <div className="mlp-cluster-status" role="status">
            <LoaderCircle size={17} className="spin" />
            <span><b>Clustering retained profiles</b>Worker computation is updating the groups.</span>
          </div>
        ) : clusterStatus === "error" ? (
          <div className="mlp-cluster-status error" role="status">
            <AlertTriangle size={17} />
            <span><b>Profile clustering unavailable</b>{clusterError}</span>
          </div>
        ) : (
          <>
            <div className="mlp-cluster-list" aria-label="MLP neuron profile clusters">
              {clusterGroups.slice(0, 8).map((cluster, index) => (
                <MLPClusterRow
                  key={cluster.members.map((member) => member.neuron.id).join(":")}
                  index={index}
                  cluster={cluster}
                  selectedNeuronId={selectedNeuronId}
                  onSelect={(neuronId) => {
                    setQuery("");
                    onSelectNeuron(neuronId);
                  }}
                />
              ))}
            </div>
            {clusterGroups.length > 8 && (
              <p className="mlp-cluster-overflow">
                {clusterGroups.length - 8} additional singleton/small groups omitted from this compact view.
              </p>
            )}
          </>
        )}
        <p className="mlp-cluster-note">
          Clusters group similar activation shapes only. A negative r means an inverse profile; neither cluster
          membership nor correlation is logit contribution, probe weight, or causal ablation evidence.
        </p>
      </section>

      {selectedNeuron && (
        <MLPActivationProfile
          tokens={tokens}
          neuron={selectedNeuron}
          selectedToken={selectedToken}
          metric={metric}
          onSelectToken={onSelectToken}
        />
      )}

      {visibleNeurons.length > 0 ? (
        <div
          ref={viewport.scrollRef}
          className={`mlp-matrix-scroll ${renderMode === "canvas" ? "specialized-canvas-mode" : ""} ${viewport.mode === "pan" ? "pan-mode" : ""}`}
          {...viewport.viewportProps}
        >
          {renderMode === "canvas" ? (
            <SpecializedMatrixCanvas
              scrollRef={viewport.scrollRef}
              rowCount={tokens.length}
              columnCount={visibleNeurons.length}
              rowHeight={25}
              columnWidth={cellSize}
              rowLabelWidth={76}
              axesPinned={viewport.axesPinned}
              selectedRow={selectedTokenPosition}
              selectedColumn={selectedNeuronPosition}
              comparisonRow={comparisonActivation
                ? tokens.findIndex((token) => token.index === comparisonActivation.tokenIndex)
                : undefined}
              comparisonColumn={comparisonActivation
                ? visibleNeurons.findIndex((neuron) => neuron.id === comparisonActivation.neuronId)
                : undefined}
              rangeAxis="row"
              selectedRange={tokenRangeToPositions(tokens, selectedRange)}
              rangeEnabled={viewport.mode === "select"}
              ariaLabel={`MLP activation Canvas matrix, ${tokens.length} token rows by ${visibleNeurons.length} neuron columns`}
              selectedDescription={`Selected token ${selectedToken}, neuron ${selectedNeuron?.id ?? "none"}, ${metricLabel(metric)} ${displayValue(selectedValue, selectedNormalized, metric)}, signed raw source ${selectedValue.toFixed(6)}.`}
              overviewRevision={`${metric}:${threshold}:${query}`}
              cornerLabel="token"
              rowLabel={(row) => `${tokens[row]?.index ?? row} ${tokens[row]?.text || "␠"}`}
              columnLabel={(column) => `N${visibleNeurons[column]?.neuron ?? column}`}
              cell={(row, column) => {
                const token = tokens[row]?.index ?? row;
                const neuron = visibleNeurons[column];
                const value = neuron?.activationsByToken[token] ?? 0;
                const normalized = Math.abs(value) / maximum;
                const opacity = normalized < threshold ? 0.08 : 0.12 + normalized * 0.8;
                return {
                  fill: isSignedMetric(metric)
                    ? value < 0
                      ? `rgba(179, 63, 103, ${opacity})`
                      : `rgba(24, 130, 103, ${opacity})`
                    : `rgba(35, 116, 138, ${opacity})`,
                  label: `${neuron?.id ?? "neuron"}, token ${token}, ${metricLabel(metric)} ${displayValue(value, normalized, metric)}, signed raw source ${value.toFixed(6)}`
                };
              }}
              onSelect={(row, column, modifiers) => {
                const token = tokens[row]?.index;
                const neuron = visibleNeurons[column];
                if (token === undefined || !neuron) return;
                if (modifiers.anchor) {
                  setComparisonActivation({ tokenIndex: token, neuronId: neuron.id });
                } else if (modifiers.pin) {
                  onPinActivation(token, neuron.id);
                } else {
                  onSelectToken(token);
                  onSelectNeuron(neuron.id);
                }
              }}
              onRangeSelect={(range) => onRangeSelect(positionRangeToTokens(tokens, range))}
              onPin={onPin}
              onHover={(row, column) => {
                const tokenIndex = tokens[row]?.index;
                const neuron = visibleNeurons[column];
                if (tokenIndex === undefined || !neuron) return;
                const value = neuron.activationsByToken[tokenIndex] ?? 0;
                setHovered({ neuron, tokenIndex, value });
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
            className={`mlp-activation-grid ${viewport.axesPinned ? "axes-pinned" : ""}`}
            style={{
              gridTemplateColumns: `76px repeat(${visibleNeurons.length}, ${cellSize}px)`,
              minWidth: `${minGridWidth}px`
            }}
            {...rangeBrush.gridProps}
          >
            <div className="mlp-grid-corner">token ↓</div>
            {visibleNeurons.map((neuron) => (
              <button
                key={`label-${neuron.id}`}
                className={`mlp-neuron-label ${neuron.id === selectedNeuronId ? "selected" : ""}`}
                title={`${neuron.id} · peak |activation| ${neuron.maxAbsoluteActivation.toFixed(6)}`}
                onClick={() => onSelectNeuron(neuron.id)}
                tabIndex={-1}
              >
                N{neuron.neuron}
              </button>
            ))}
            {tokens.map((token) => (
              <MLPActivationRow
                key={token.index}
                token={token}
                neurons={visibleNeurons}
                maximum={maximum}
                threshold={threshold}
                metric={metric}
                selectedToken={selectedToken}
                selectedNeuronId={selectedNeuronId}
                comparisonActivation={comparisonActivation}
                keyboardNeuronId={keyboardNeuronId}
                inRange={rangeBrush.inRange}
                onSelect={(neuron) => {
                  onSelectToken(token.index);
                  onSelectNeuron(neuron.id);
                }}
                onSelectToken={onSelectToken}
                onSetComparison={setComparisonActivation}
                onPinActivation={onPinActivation}
                onPin={onPin}
                onMoveFocus={moveActivationFocus}
                onHover={(activation) => {
                  setHovered(activation);
                  onHoverToken(activation?.tokenIndex ?? null);
                }}
              />
            ))}
          </div>
          )}
        </div>
      ) : (
        <div className="mlp-no-results">No retained neuron matches “{query}”.</div>
      )}

      <MLPActivationTooltip
        activation={hovered}
        maximum={maximum}
        metric={metric}
        tokens={tokens}
      />

      <MLPActivationLegend metric={metric} maximum={maximum} threshold={threshold} />
    </section>
  );
}

function MLPActivationRow({
  token,
  neurons,
  maximum,
  threshold,
  metric,
  selectedToken,
  selectedNeuronId,
  comparisonActivation,
  keyboardNeuronId,
  inRange,
  onSelect,
  onSelectToken,
  onSetComparison,
  onPinActivation,
  onPin,
  onMoveFocus,
  onHover
}: {
  token: TokenInfo;
  neurons: MLPNeuron[];
  maximum: number;
  threshold: number;
  metric: string;
  selectedToken: number;
  selectedNeuronId: string;
  comparisonActivation: { tokenIndex: number; neuronId: string } | null;
  keyboardNeuronId?: string;
  inRange: (token: number) => boolean;
  onSelect: (neuron: MLPNeuron) => void;
  onSelectToken: (token: number) => void;
  onSetComparison: (activation: { tokenIndex: number; neuronId: string }) => void;
  onPinActivation: (token: number, neuronId: string) => void;
  onPin: () => void;
  onMoveFocus: (token: number, neuronId: string, key: string) => void;
  onHover: (activation: HoveredActivation | null) => void;
}) {
  return (
    <>
      <button
        className={`mlp-token-label ${selectedToken === token.index ? "selected" : ""} ${inRange(token.index) ? "in-range" : ""}`}
        data-range-token={token.index}
        onClick={() => onSelectToken(token.index)}
        tabIndex={-1}
        title={matrixTokenTitle(token)}
      >
        <span>{token.index}</span><b>{token.text || "␠"}</b>
      </button>
      {neurons.map((neuron) => {
        const value = neuron.activationsByToken[token.index] ?? 0;
        const normalized = Math.abs(value) / maximum;
        const signed = isSignedMetric(metric);
        const filtered = normalized < threshold;
        const selected = selectedToken === token.index && selectedNeuronId === neuron.id;
        const comparison =
          comparisonActivation?.tokenIndex === token.index && comparisonActivation.neuronId === neuron.id;
        return (
          <button
            key={`${token.index}:${neuron.id}`}
            data-token={token.index}
            data-neuron={neuron.id}
            data-range-token={token.index}
            className={[
              "mlp-activation-cell",
              signed ? (value < 0 ? "negative" : "positive") : "magnitude",
              filtered ? "filtered" : "",
              selected ? "selected" : "",
              comparison ? "comparison" : "",
              inRange(token.index) ? "in-range" : ""
            ].join(" ")}
            style={{ "--magnitude": normalized } as React.CSSProperties}
            aria-label={`${neuron.id}, token ${token.index}, ${metricLabel(metric)} ${displayValue(value, normalized, metric)}, signed raw source ${value.toFixed(6)}`}
            aria-keyshortcuts="ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter Space"
            tabIndex={selectedToken === token.index && keyboardNeuronId === neuron.id ? 0 : -1}
            onClick={(event) => {
              if (event.shiftKey) {
                onSetComparison({ tokenIndex: token.index, neuronId: neuron.id });
              } else if (event.metaKey || event.ctrlKey) {
                onPinActivation(token.index, neuron.id);
              } else {
                onSelect(neuron);
              }
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && event.shiftKey) {
                event.preventDefault();
                event.stopPropagation();
                onSetComparison({ tokenIndex: token.index, neuronId: neuron.id });
                return;
              }
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                event.stopPropagation();
                onPinActivation(token.index, neuron.id);
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
              onMoveFocus(token.index, neuron.id, event.key);
            }}
            onMouseEnter={() => onHover({ neuron, tokenIndex: token.index, value })}
            onMouseLeave={() => onHover(null)}
            onFocus={() => onHover({ neuron, tokenIndex: token.index, value })}
            onBlur={() => onHover(null)}
            title={displayValue(value, normalized, metric)}
          />
        );
      })}
    </>
  );
}

function MLPActivationTooltip({
  activation,
  maximum,
  metric,
  tokens
}: {
  activation: HoveredActivation | null;
  maximum: number;
  metric: string;
  tokens: TokenInfo[];
}) {
  if (!activation) {
    return <div className="mlp-activation-tooltip empty">Activation details · no matrix cell focused.</div>;
  }
  const normalized = Math.abs(activation.value) / maximum;
  return (
    <div className="mlp-activation-tooltip">
      <MatrixTokenDetail tokens={tokens} tokenIndex={activation.tokenIndex} />
      <span><b>{activation.neuron.id}</b>neuron {activation.neuron.neuron}</span>
      <span><b>{formatMetricNumber(activation.value, "mlp_signed_activation", "exact")}</b>signed raw</span>
      <span><b>{formatMetricNumber(Math.abs(activation.value), "mlp_absolute_activation", "exact")}</b>absolute raw</span>
      <span><b>{formatMetricNumber(normalized, "mlp_normalized_activation", "exact")}</b>normalized magnitude</span>
      <span className="mlp-tooltip-source"><b>{`layer_${activation.neuron.layer}.post[:, ${activation.neuron.neuron}]`}</b>cache key</span>
      <span className="mlp-tooltip-source"><b>raw activation</b>{metricLabel(metric)}</span>
    </div>
  );
}

function displayValue(value: number, normalized: number, metric: string) {
  return formatMetricNumber(
    metric === "mlp_absolute_activation"
      ? Math.abs(value)
      : metric === "mlp_normalized_activation"
        ? normalized
        : value,
    metric,
    "compact"
  );
}

function metricNumericValue(value: number, normalized: number, metric: string) {
  if (metric === "mlp_absolute_activation") return Math.abs(value);
  if (metric === "mlp_normalized_activation") return normalized;
  return value;
}

function formatMetricDelta(value: number, metric: string) {
  return formatRegisteredDelta(value, metric, "compact");
}

function metricLabel(metric: string) {
  if (metric === "mlp_absolute_activation") return "absolute raw activation";
  if (metric === "mlp_normalized_activation") return "normalized activation magnitude";
  return "signed raw activation";
}

function isSignedMetric(metric: string) {
  return metric === "mlp_signed_activation";
}

function MLPActivationLegend({
  metric,
  maximum,
  threshold
}: {
  metric: string;
  maximum: number;
  threshold: number;
}) {
  const signed = isSignedMetric(metric);
  const normalized = metric === "mlp_normalized_activation";
  const domainMaximum = normalized ? 1 : maximum;
  const cutoff = threshold * domainMaximum;

  return (
    <div
      className={`mlp-diverging-legend ${signed ? "signed" : "magnitude"}`}
      aria-label="MLP activation legend"
      data-domain={signed ? "diverging" : "sequential"}
    >
      {signed ? (
        <>
          <span><i className="mlp-negative-high" />{formatActivation(-maximum)}</span>
          <span><i className="mlp-zero" />0</span>
          <span><i className="mlp-positive-high" />+{formatActivation(maximum)}</span>
        </>
      ) : (
        <>
          <span><i className="mlp-magnitude-low" />0</span>
          <span><i className="mlp-magnitude-mid" />{formatActivation(domainMaximum / 2)}</span>
          <span><i className="mlp-magnitude-high" />{formatActivation(domainMaximum)}</span>
        </>
      )}
      <span><i className="mlp-filtered" />below {formatActivation(cutoff)}</span>
      <b>
        {metricLabel(metric)} · {signed ? "symmetric zero-centered domain" : normalized ? "fixed 0–1 domain" : "sequential domain from zero"}
      </b>
    </div>
  );
}

function MLPNeuronRankingList({
  title,
  tone,
  entries,
  maximum,
  selectedNeuronId,
  onSelect
}: {
  title: string;
  tone: "positive" | "negative";
  entries: Array<{ neuron: MLPNeuron; value: number }>;
  maximum: number;
  selectedNeuronId: string;
  onSelect: (neuronId: string) => void;
}) {
  const listRef = useRef<HTMLOListElement>(null);
  const selectedPosition = entries.findIndex((entry) => entry.neuron.id === selectedNeuronId);
  const keyboardPosition = selectedPosition >= 0 ? selectedPosition : 0;

  function move(position: number, key: string) {
    let next = position;
    if (key === "ArrowLeft" || key === "ArrowUp") next = Math.max(0, position - 1);
    if (key === "ArrowRight" || key === "ArrowDown") next = Math.min(entries.length - 1, position + 1);
    if (key === "Home") next = 0;
    if (key === "End") next = entries.length - 1;
    const neuronId = entries[next]?.neuron.id;
    if (!neuronId) return;
    onSelect(neuronId);
    window.requestAnimationFrame(() => {
      listRef.current?.querySelector<HTMLButtonElement>(`[data-ranked-neuron="${neuronId}"]`)?.focus();
    });
  }

  return (
    <div className={`mlp-neuron-ranking-list ${tone}`}>
      <div className="mlp-neuron-ranking-title">
        <span>{title}</span>
        <b>{entries.length} retained</b>
      </div>
      {entries.length > 0 ? (
        <ol ref={listRef} aria-label={title}>
          {entries.map((entry, index) => {
            const selected = entry.neuron.id === selectedNeuronId;
            return (
              <li key={entry.neuron.id}>
                <button
                  type="button"
                  aria-pressed={selected}
                  aria-label={`${entry.neuron.id}, rank ${index + 1}, signed raw activation ${formatActivation(entry.value)}`}
                  data-ranked-neuron={entry.neuron.id}
                  tabIndex={index === keyboardPosition ? 0 : -1}
                  onClick={() => onSelect(entry.neuron.id)}
                  onKeyDown={(event) => {
                    if (!isNavigationKey(event.key)) return;
                    event.preventDefault();
                    move(index, event.key);
                  }}
                >
                  <span>{index + 1}</span>
                  <strong>{entry.neuron.id}</strong>
                  <i aria-hidden="true"><b style={{ width: `${Math.abs(entry.value) / maximum * 100}%` }} /></i>
                  <em>{formatActivation(entry.value)}</em>
                </button>
              </li>
            );
          })}
        </ol>
      ) : (
        <p>No {tone} retained activation at this token.</p>
      )}
    </div>
  );
}

function MLPClusterRow({
  index,
  cluster,
  selectedNeuronId,
  onSelect
}: {
  index: number;
  cluster: MLPClusterGroup;
  selectedNeuronId: string;
  onSelect: (neuronId: string) => void;
}) {
  const membersRef = useRef<HTMLDivElement>(null);
  const selectedPosition = cluster.members.findIndex(
    (member) => member.neuron.id === selectedNeuronId
  );
  const keyboardPosition = selectedPosition >= 0 ? selectedPosition : 0;

  function move(position: number, key: string) {
    let next = position;
    if (key === "ArrowLeft" || key === "ArrowUp") next = Math.max(0, position - 1);
    if (key === "ArrowRight" || key === "ArrowDown") {
      next = Math.min(cluster.members.length - 1, position + 1);
    }
    if (key === "Home") next = 0;
    if (key === "End") next = cluster.members.length - 1;
    const neuronId = cluster.members[next]?.neuron.id;
    if (!neuronId) return;
    onSelect(neuronId);
    window.requestAnimationFrame(() => {
      membersRef.current
        ?.querySelector<HTMLButtonElement>(`[data-cluster-neuron="${neuronId}"]`)
        ?.focus();
    });
  }

  return (
    <div
      className={`mlp-cluster-row ${cluster.selected ? "selected" : ""}`}
      role="group"
      aria-label={`Profile cluster ${index + 1}, ${cluster.members.length} neurons`}
    >
      <div className="mlp-cluster-row-heading">
        <span><b>Group {index + 1}</b>{cluster.members.length} neuron{cluster.members.length === 1 ? "" : "s"}</span>
        <span><b>{cluster.meanAbsoluteCorrelation.toFixed(3)}</b>mean |r| to representative</span>
        <em>{cluster.representative.id} representative</em>
      </div>
      <div ref={membersRef} className="mlp-cluster-members">
        {cluster.members.map((member, position) => {
          const selected = member.neuron.id === selectedNeuronId;
          return (
            <button
              key={member.neuron.id}
              type="button"
              aria-pressed={selected}
              aria-label={`${member.neuron.id}, Pearson correlation ${formatCorrelation(member.correlation)} to ${cluster.representative.id}, ${member.correlation < 0 ? "inverse" : "same-direction"} profile`}
              data-cluster-neuron={member.neuron.id}
              tabIndex={position === keyboardPosition ? 0 : -1}
              onClick={() => onSelect(member.neuron.id)}
              onKeyDown={(event) => {
                if (!isNavigationKey(event.key)) return;
                event.preventDefault();
                move(position, event.key);
              }}
            >
              <strong>{member.neuron.id}</strong>
              <span>{formatCorrelation(member.correlation)}</span>
              <em>{member.correlation < 0 ? "inverse" : "same direction"}</em>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function MLPActivationProfile({
  tokens,
  neuron,
  selectedToken,
  metric,
  onSelectToken
}: {
  tokens: TokenInfo[];
  neuron: MLPNeuron;
  selectedToken: number;
  metric: string;
  onSelectToken: (token: number) => void;
}) {
  const railRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const rail = railRef.current;
    if (!rail) return;
    const revealSelected = () => {
      const selected = rail.querySelector<HTMLButtonElement>(
        `[data-profile-token="${selectedToken}"]`
      );
      if (selected) scrollElementInlineCenter(rail, selected);
    };
    revealSelected();
    const observer = new ResizeObserver(revealSelected);
    observer.observe(rail);
    return () => observer.disconnect();
  }, [selectedToken]);
  const signed = metric === "mlp_signed_activation";
  const points = tokens.map((token) => {
    const raw = neuron.activationsByToken[token.index] ?? 0;
    return {
      token,
      raw,
      value: metric === "mlp_absolute_activation"
        ? Math.abs(raw)
        : metric === "mlp_normalized_activation"
          ? Math.abs(raw) / Math.max(neuron.maxAbsoluteActivation, 1e-12)
          : raw
    };
  });
  const maximum = Math.max(1e-12, ...points.map((point) => Math.abs(point.value)));
  const baselineY = signed ? 70 : 124;
  const chartPoints = points.map((point, index) => ({
    ...point,
    x: points.length === 1 ? 360 : 22 + index * 676 / (points.length - 1),
    y: signed
      ? baselineY - point.value / maximum * 52
      : baselineY - point.value / maximum * 104
  }));
  const path = chartPoints.map((point, index) =>
    `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
  ).join(" ");
  const selectedPoint = chartPoints.find((point) => point.token.index === selectedToken) ?? chartPoints[0];
  const positivePeak = points.reduce((peak, point) => point.raw > peak.raw ? point : peak, points[0]);
  const negativePeak = points.reduce((peak, point) => point.raw < peak.raw ? point : peak, points[0]);

  function moveToken(key: string) {
    const current = Math.max(0, tokens.findIndex((token) => token.index === selectedToken));
    let next = current;
    if (key === "ArrowLeft" || key === "ArrowUp") next = Math.max(0, current - 1);
    if (key === "ArrowRight" || key === "ArrowDown") next = Math.min(tokens.length - 1, current + 1);
    if (key === "Home") next = 0;
    if (key === "End") next = tokens.length - 1;
    const tokenIndex = tokens[next]?.index;
    if (tokenIndex === undefined) return;
    onSelectToken(tokenIndex);
    window.requestAnimationFrame(() => {
      railRef.current
        ?.querySelector<HTMLButtonElement>(`[data-profile-token="${tokenIndex}"]`)
        ?.focus();
    });
  }

  return (
    <section className="mlp-activation-profile" aria-labelledby="mlp-profile-title">
      <div className="mlp-profile-heading">
        <div>
          <h4 id="mlp-profile-title">Neuron activation profile</h4>
          <p>{neuron.id} across the retained token axis · descriptive activation</p>
        </div>
        <span>{metricLabel(metric)}</span>
      </div>
      <div className="mlp-profile-chart-wrap">
        <svg
          className="mlp-profile-chart"
          viewBox="0 0 720 140"
          preserveAspectRatio="none"
          role="img"
          aria-label={`${neuron.id} ${metricLabel(metric)} profile across ${points.length} tokens`}
        >
          <line className="mlp-profile-zero-line" x1="22" y1={baselineY} x2="698" y2={baselineY} />
          <path className="mlp-profile-area" d={`${path} L 698 ${baselineY} L 22 ${baselineY} Z`} />
          <path className="mlp-profile-line" d={path} />
          {selectedPoint && (
            <>
              <line className="mlp-profile-selection-line" x1={selectedPoint.x} y1="12" x2={selectedPoint.x} y2="128" />
              <circle className="mlp-profile-selected-point" cx={selectedPoint.x} cy={selectedPoint.y} r="5" />
            </>
          )}
        </svg>
        <div className="mlp-profile-bounds" aria-hidden="true">
          <span>{signed ? formatActivation(maximum) : formatActivation(maximum)}</span>
          <span>{signed ? formatActivation(-maximum) : "0"}</span>
        </div>
      </div>
      <div className="mlp-profile-stats">
        <span><b>{formatActivation(selectedPoint?.value ?? 0)}</b>selected display · T{selectedToken}</span>
        <button onClick={() => onSelectToken(positivePeak.token.index)}>
          <b>{formatActivation(positivePeak.raw)}</b>positive peak · T{positivePeak.token.index} {visibleToken(positivePeak.token.text)}
        </button>
        <button onClick={() => onSelectToken(negativePeak.token.index)}>
          <b>{formatActivation(negativePeak.raw)}</b>negative peak · T{negativePeak.token.index} {visibleToken(negativePeak.token.text)}
        </button>
      </div>
      <div
        ref={railRef}
        className="mlp-profile-token-rail"
        role="radiogroup"
        aria-label="Neuron activation profile tokens"
      >
        {chartPoints.map((point) => (
          <button
            key={point.token.index}
            type="button"
            role="radio"
            aria-checked={point.token.index === selectedToken}
            aria-label={`${visibleToken(point.token.text)}, token ${point.token.index}, ${metricLabel(metric)} ${formatActivation(point.value)}`}
            data-profile-token={point.token.index}
            tabIndex={point.token.index === selectedToken ? 0 : -1}
            onClick={() => onSelectToken(point.token.index)}
            onKeyDown={(event) => {
              if (!isNavigationKey(event.key)) return;
              event.preventDefault();
              moveToken(event.key);
            }}
          >
            <span>{point.token.index}</span>
            <b>{visibleToken(point.token.text)}</b>
            <i className={point.raw < 0 ? "negative" : "positive"}>{formatActivation(point.value)}</i>
          </button>
        ))}
      </div>
    </section>
  );
}

function formatActivation(value: number) {
  if (value !== 0 && Math.abs(value) < 0.001) return value.toExponential(2);
  return value.toFixed(4);
}

function visibleToken(value: string) {
  return value || "␠";
}

function pearsonForTokens(left: number[], right: number[], tokenIndices: number[]) {
  if (tokenIndices.length === 0) return 0;
  let leftMean = 0;
  let rightMean = 0;
  for (const tokenIndex of tokenIndices) {
    leftMean += left[tokenIndex] ?? 0;
    rightMean += right[tokenIndex] ?? 0;
  }
  leftMean /= tokenIndices.length;
  rightMean /= tokenIndices.length;
  let numerator = 0;
  let leftSquare = 0;
  let rightSquare = 0;
  for (const tokenIndex of tokenIndices) {
    const leftCentered = (left[tokenIndex] ?? 0) - leftMean;
    const rightCentered = (right[tokenIndex] ?? 0) - rightMean;
    numerator += leftCentered * rightCentered;
    leftSquare += leftCentered * leftCentered;
    rightSquare += rightCentered * rightCentered;
  }
  const denominator = Math.sqrt(leftSquare * rightSquare);
  if (denominator <= 1e-12) return left === right ? 1 : 0;
  return Math.max(-1, Math.min(1, numerator / denominator));
}

function formatCorrelation(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
}

function isNavigationKey(key: string) {
  return ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(key);
}
