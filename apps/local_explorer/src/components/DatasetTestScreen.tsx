import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  CheckSquare2,
  Clock3,
  Database,
  Download,
  ExternalLink,
  FileCheck2,
  GitCompareArrows,
  LoaderCircle,
  Play,
  RefreshCw,
  Search,
  Square,
  StopCircle,
  X,
  XCircle
} from "lucide-react";

import {
  cancelDatasetTestJob,
  fetchDatasetCatalog,
  fetchDatasetTestJob,
  fetchDatasetTestJobs,
  submitDatasetTestJob,
  type DatasetAlgorithm,
  type DatasetDefinition,
  type DatasetTestJob,
  type DatasetTestJobSummary,
  type DatasetTestResult
} from "../api/explorerClient";
import { JobCenter } from "./JobCenter";

const DEFAULT_MODEL = "google/gemma-2-9b-it";

export function DatasetTestScreen({
  onOpenChat,
  initialJobId = null
}: {
  onOpenChat: () => void;
  initialJobId?: string | null;
}) {
  const [datasets, setDatasets] = useState<DatasetDefinition[]>([]);
  const [algorithms, setAlgorithms] = useState<DatasetAlgorithm[]>([]);
  const [algorithmId, setAlgorithmId] = useState<DatasetAlgorithm["id"]>("pca_minus_neg");
  const [datasetId, setDatasetId] = useState("safelens-final-300-v1.1");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const model = DEFAULT_MODEL;
  const [job, setJob] = useState<DatasetTestJob | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [resultFilter, setResultFilter] = useState<"all" | "passed" | "failed">("all");
  const [history, setHistory] = useState<DatasetTestJobSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const bootstrapRef = useRef(true);
  const resultsRef = useRef<HTMLDivElement>(null);

  const algorithm = algorithms.find((item) => item.id === algorithmId);
  const compatibleDatasets = useMemo(
    () => datasets.filter((item) => algorithm?.supportedDatasetIds.includes(item.id)),
    [algorithm, datasets]
  );
  const dataset = compatibleDatasets.find((item) => item.id === datasetId) ?? compatibleDatasets[0];
  const running = job?.status === "idle" || job?.status === "loading";

  useEffect(() => {
    const controller = new AbortController();
    fetchDatasetCatalog(controller.signal).then((catalog) => {
      setDatasets(catalog.datasets);
      setAlgorithms(catalog.algorithms);
      const first = catalog.datasets.find((item) => item.id === "safelens-final-300-v1.1") ?? catalog.datasets[0];
      setDatasetId(first.id);
      setSelectedIds(new Set(first.samples.map((sample) => sample.id)));
    }).catch((error) => {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setCatalogError(error instanceof Error ? error.message : "Dataset catalog is unavailable.");
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!running || !job) return;
    let disposed = false;
    const timer = window.setInterval(() => {
      void fetchDatasetTestJob(job.id).then((next) => {
        if (!disposed) setJob(next);
      }).catch((error) => {
        if (!disposed) setRunError(error instanceof Error ? error.message : "Could not refresh the job.");
      });
    }, 650);
    return () => {
      disposed = true;
      window.clearInterval(timer);
    };
  }, [job?.id, running]);

  const refreshHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      setHistory(await fetchDatasetTestJobs(30));
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : "Dataset history is unavailable.");
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    let disposed = false;
    async function bootstrap() {
      setHistoryLoading(true);
      setHistoryError(null);
      try {
        const jobs = await fetchDatasetTestJobs(30);
        if (disposed) return;
        setHistory(jobs);
        const targetId = initialJobId ??
          jobs.find((item) => item.status === "idle" || item.status === "loading")?.id;
        if (targetId && (initialJobId || bootstrapRef.current)) {
          const full = await fetchDatasetTestJob(targetId);
          if (disposed) return;
          setJob((current) => initialJobId ? full : current ?? full);
          setAlgorithmId(full.request.algorithmId);
          setDatasetId(full.request.datasetId);
        }
      } catch (error) {
        if (!disposed) {
          setHistoryError(error instanceof Error ? error.message : "Dataset history is unavailable.");
        }
      } finally {
        if (!disposed) setHistoryLoading(false);
      }
    }
    void bootstrap();
    return () => {
      disposed = true;
    };
  }, [initialJobId]);

  useEffect(() => {
    if (!job || !["ready", "error", "cancelled"].includes(job.status)) return;
    void refreshHistory();
  }, [job?.id, job?.status, refreshHistory]);

  async function openHistoryJob(jobId: string) {
    setRunError(null);
    setResultFilter("all");
    try {
      const full = await fetchDatasetTestJob(jobId);
      setJob(full);
      setAlgorithmId(full.request.algorithmId);
      setDatasetId(full.request.datasetId);
      window.setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 60);
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "This dataset run could not be opened.");
    }
  }

  function toggleComparison(jobId: string) {
    setCompareIds((current) => {
      if (current.includes(jobId)) return current.filter((id) => id !== jobId);
      if (current.length < 2) return [...current, jobId];
      return [current[1], jobId];
    });
  }

  function chooseAlgorithm(next: DatasetAlgorithm) {
    bootstrapRef.current = false;
    const nextDataset = datasets.find((item) => next.supportedDatasetIds.includes(item.id));
    setAlgorithmId(next.id);
    setJob(null);
    setRunError(null);
    setResultFilter("all");
    if (nextDataset) {
      setDatasetId(nextDataset.id);
      setSelectedIds(new Set(nextDataset.samples.map((sample) => sample.id)));
    }
  }

  function chooseDataset(nextId: string) {
    bootstrapRef.current = false;
    const next = datasets.find((item) => item.id === nextId);
    setDatasetId(nextId);
    setJob(null);
    setSelectedIds(new Set(next?.samples.map((sample) => sample.id) ?? []));
  }

  function toggleSample(sampleId: string) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(sampleId)) next.delete(sampleId);
      else next.add(sampleId);
      return next;
    });
  }

  async function runTest() {
    if (!dataset || !algorithm || selectedIds.size === 0) return;
    bootstrapRef.current = false;
    setRunError(null);
    setResultFilter("all");
    try {
      const next = await submitDatasetTestJob({
        datasetId: dataset.id,
        algorithmId: algorithm.id,
        model,
        sampleIds: dataset.samples.filter((item) => selectedIds.has(item.id)).map((item) => item.id),
        layer: 22,
        sourceLayer: null,
        strength: 1,
        seed: 0,
        maxNewTokens: 160
      });
      setJob(next);
      void refreshHistory();
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Dataset test could not start.");
    }
  }

  async function cancelTest() {
    if (!job) return;
    try {
      setJob(await cancelDatasetTestJob(job.id));
      void refreshHistory();
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Dataset test could not be cancelled.");
    }
  }

  const comparisonRuns = compareIds
    .map((id) => history.find((item) => item.id === id))
    .filter((item): item is DatasetTestJobSummary => item !== undefined);

  return (
    <div className="dataset-test-screen">
      <header className="dataset-test-header">
        <button className="dataset-test-brand" onClick={onOpenChat} aria-label="Open SafeLens chat">
          <span><BrainCircuit size={21} /></span>
          <strong>SafeLens</strong>
        </button>
        <nav aria-label="SafeLens modes">
          <button onClick={onOpenChat}><ArrowLeft size={16} /> Chat</button>
          <button className="active" aria-current="page"><Database size={16} /> Dataset test</button>
          <JobCenter inline onOpenDatasetJob={(jobId) => void openHistoryJob(jobId)} />
        </nav>
        <span className="dataset-live-badge"><i /> Real local evaluation</span>
      </header>

      <main className="dataset-test-main">
        <section className="dataset-test-intro" aria-labelledby="dataset-test-title">
          <div>
            <span>Evaluation mode</span>
            <h1 id="dataset-test-title">Test white-box methods on a fixed dataset</h1>
          </div>
          <dl>
            <div><dt>Samples</dt><dd>{dataset?.samples.length ?? 0}</dd></div>
            <div><dt>Selected</dt><dd>{selectedIds.size}</dd></div>
            <div><dt>Repair rate</dt><dd>{formatPercent(dataset?.metric.threshold ?? 0)}</dd></div>
          </dl>
        </section>

        {catalogError ? (
          <div className="dataset-error" role="alert"><XCircle size={18} /> {catalogError}</div>
        ) : (
          <div className="dataset-test-setup">
            <section className="dataset-source-panel" aria-labelledby="dataset-source-title">
              <header>
                <div>
                  <span>1 / Dataset</span>
                  <h2 id="dataset-source-title">Choose evaluation samples</h2>
                </div>
                <label>
                  <span>Dataset</span>
                  <select value={dataset?.id ?? ""} onChange={(event) => chooseDataset(event.target.value)}>
                    {compatibleDatasets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </label>
              </header>
              {dataset && (
                <>
                  <div className="dataset-description">
                    <p>{dataset.description}</p>
                    <span>{dataset.source} / v{dataset.version}</span>
                  </div>
                  <div className="dataset-sample-toolbar">
                    <strong>{selectedIds.size} of {dataset.samples.length} selected</strong>
                    <button onClick={() => setSelectedIds(
                      selectedIds.size === dataset.samples.length
                        ? new Set()
                        : new Set(dataset.samples.map((sample) => sample.id))
                    )}>
                      {selectedIds.size === dataset.samples.length ? <CheckSquare2 size={15} /> : <Square size={15} />}
                      {selectedIds.size === dataset.samples.length ? "Clear all" : "Select all"}
                    </button>
                  </div>
                  <div className="dataset-sample-list">
                    {dataset.samples.map((sample) => (
                      <button
                        key={sample.id}
                        className={selectedIds.has(sample.id) ? "selected" : ""}
                        aria-pressed={selectedIds.has(sample.id)}
                        onClick={() => toggleSample(sample.id)}
                      >
                        {selectedIds.has(sample.id) ? <CheckSquare2 size={17} /> : <Square size={17} />}
                        <span>
                          <small>{sample.id} / {sample.task ?? sample.category} / {sample.source}</small>
                          <strong>{sample.prompt ?? sample.corruptedPrompt}</strong>
                          {sample.groundTruth && <em>Ground truth: {sample.groundTruth}</em>}
                          {sample.cleanPrompt && <em>Clean: {sample.cleanPrompt}</em>}
                          {sample.desiredPrompt && <em>Toward: {sample.desiredPrompt}</em>}
                        </span>
                      </button>
                    ))}
                  </div>
                </>
              )}
            </section>

            <section className="dataset-method-panel" aria-labelledby="dataset-method-title">
              <header>
                <span>2 / Method</span>
                <h2 id="dataset-method-title">Select an optimization algorithm</h2>
              </header>
              <div className="dataset-method-tabs" role="radiogroup" aria-label="Optimization algorithm">
                {algorithms.map((item) => (
                  <button
                    key={item.id}
                    role="radio"
                    aria-checked={item.id === algorithmId}
                    className={item.id === algorithmId ? "active" : ""}
                    onClick={() => chooseAlgorithm(item)}
                  >
                    {item.id === "pca_minus_neg" ? <BrainCircuit size={18} /> : <FileCheck2 size={18} />}
                    <span><strong>{item.name}</strong><small>{item.implementation.replace(/_/g, " ")}</small></span>
                  </button>
                ))}
              </div>
              {algorithm && (
                <div className="dataset-method-summary">
                  <p>{algorithm.description}</p>
                  <a href={algorithm.paperUrl} target="_blank" rel="noreferrer">
                    <span><small>Method reference</small><strong>{algorithm.paperTitle}</strong></span>
                    <ExternalLink size={16} />
                  </a>
                </div>
              )}
              {dataset && (
                <div className="dataset-metric-note">
                  <strong>{dataset.metric.name}</strong>
                  <p>{dataset.metric.definition}</p>
                  <span>Required repair rate &gt; {formatPercent(dataset.metric.threshold)}</span>
                </div>
              )}
              <div className="dataset-run-controls">
                <label className="wide"><span>Local model</span><select value={model} disabled><option value={DEFAULT_MODEL}>{shortModelName(DEFAULT_MODEL)}</option></select></label>
                <p className="wide">The run first evaluates every selected sample without intervention, then applies steering only to baseline failures. Layer, alpha, and injection scope use the fixed final_300 protocol.</p>
              </div>
              <button className="dataset-run-button" disabled={running || !dataset || selectedIds.size === 0} onClick={runTest}>
                {running ? <LoaderCircle size={18} className="spin" /> : <Play size={18} fill="currentColor" />}
                {running
                  ? "Running dataset test"
                  : `Test ${selectedIds.size} ${selectedIds.size === 1 ? "sample" : "samples"}`}
              </button>
              {running && job && <button className="dataset-cancel-button" onClick={cancelTest}><StopCircle size={16} /> Cancel</button>}
              {runError && <div className="dataset-error" role="alert"><XCircle size={17} /> {runError}</div>}
            </section>
          </div>
        )}

        <section className="dataset-history" aria-labelledby="dataset-history-title">
          <header>
            <div>
              <span>Run library</span>
              <h2 id="dataset-history-title">Recent dataset evaluations</h2>
              <p>Reopen a saved result or choose two runs to compare per-category repair rates.</p>
            </div>
            <button
              type="button"
              className="dataset-history-refresh"
              onClick={() => void refreshHistory()}
              disabled={historyLoading}
            >
              <RefreshCw size={15} className={historyLoading ? "spin" : ""} /> Refresh
            </button>
          </header>
          {historyError && (
            <div className="dataset-error" role="alert"><XCircle size={17} /> {historyError}</div>
          )}
          {historyLoading && history.length === 0 ? (
            <p className="dataset-history-empty">Loading saved runs...</p>
          ) : history.length === 0 ? (
            <p className="dataset-history-empty">
              No saved runs yet. Start a test above; completed runs stay available here.
            </p>
          ) : (
            <div className="dataset-history-list">
              {history.map((item) => {
                const metric = item.result?.metric;
                const active = job?.id === item.id;
                const selectedForComparison = compareIds.includes(item.id);
                const statusLabel = metric
                  ? metric.partial
                    ? "Partial"
                    : metric.meetsThreshold
                      ? "Threshold met"
                      : "Below threshold"
                  : historyStatusLabel(item.status);
                return (
                  <article
                    key={item.id}
                    className={`dataset-history-card${active ? " active" : ""}${selectedForComparison ? " selected" : ""}`}
                  >
                    <button
                      type="button"
                      className="dataset-history-open"
                      aria-label={`Open dataset run ${datasetAlgorithmName(item.request.algorithmId, algorithms)} from ${formatDate(item.createdAt)}`}
                      onClick={() => void openHistoryJob(item.id)}
                    >
                      <span className="dataset-history-algorithm">
                        {datasetAlgorithmName(item.request.algorithmId, algorithms)}
                      </span>
                      <strong>{metric ? formatPercent(metric.accuracy) : historyStatusLabel(item.status)}</strong>
                      <small>{formatDate(item.createdAt)} · {shortModelName(item.request.model)}</small>
                      <small>
                        {item.request.sampleIds.length} sample
                        {item.request.sampleIds.length === 1 ? "" : "s"}
                        {metric ? ` · ${metric.failureToSuccess ?? 0}/${metric.baselineFailure ?? 0} repaired` : ""}
                      </small>
                      <span className={`dataset-history-state ${item.status}`}>{statusLabel}</span>
                    </button>
                    <label className="dataset-history-compare">
                      <input
                        type="checkbox"
                        checked={selectedForComparison}
                        aria-label={`Select ${datasetAlgorithmName(item.request.algorithmId, algorithms)} run from ${formatDate(item.createdAt)} for comparison`}
                        onChange={() => toggleComparison(item.id)}
                      />
                      Compare
                    </label>
                  </article>
                );
              })}
            </div>
          )}
          {comparisonRuns.length > 0 && (
            <div className="dataset-history-compare-hint" role="status">
              <GitCompareArrows size={14} />
              {comparisonRuns.length === 1
                ? "Select one more run to compare."
                : "Comparing the two selected runs."}
            </div>
          )}
          {comparisonRuns.length === 2 && (
            <DatasetRunComparison runs={[comparisonRuns[0], comparisonRuns[1]]} />
          )}
        </section>

        <div ref={resultsRef} className="dataset-results-anchor">
          {job && <DatasetJobResults job={job} filter={resultFilter} onFilter={setResultFilter} />}
        </div>
      </main>
    </div>
  );
}

const DATASET_TASKS = ["reasoning", "faithful", "safety"] as const;

type DatasetTaskResult = NonNullable<DatasetTestResult["metric"]["tasks"]>[string];

function DatasetTaskSummary({ tasks }: { tasks: DatasetTestResult["metric"]["tasks"] }) {
  if (!tasks) return null;
  const orderedKeys = [
    ...DATASET_TASKS.filter((task) => tasks[task]),
    ...Object.keys(tasks).filter((task) => !DATASET_TASKS.includes(task as typeof DATASET_TASKS[number]))
  ];
  if (orderedKeys.length === 0) return null;
  return (
    <section className="dataset-task-summary" aria-label="Per-category correction rate">
      <header>
        <div>
          <strong>Per-category correction rate</strong>
          <small>C/F = repaired baseline failures / baseline failures</small>
        </div>
      </header>
      <table aria-label="Per-category correction rate">
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col">N</th>
            <th scope="col">Baseline failures F</th>
            <th scope="col">Repaired C</th>
            <th scope="col">Correction rate C/F</th>
            <th scope="col">Post-intervention success</th>
          </tr>
        </thead>
        <tbody>
          {orderedKeys.map((taskName) => {
            const task: DatasetTaskResult = tasks[taskName];
            const evaluated = task.total > 0;
            return (
              <tr key={taskName}>
                <th scope="row">{formatKey(taskName)}</th>
                <td>{task.total}</td>
                <td>{evaluated ? task.baselineFailure : "—"}</td>
                <td>{evaluated ? task.failureToSuccess : "—"}</td>
                <td className={evaluated ? "" : "unevaluated"}>
                  {evaluated ? formatPercent(task.correctionRate) : "Not evaluated"}
                  {evaluated && task.baselineFailure === 0 && <small>no baseline failures</small>}
                </td>
                <td>{evaluated ? `${task.postInterventionSuccess ?? 0}/${task.total}` : "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function DatasetRunComparison({
  runs
}: {
  runs: [DatasetTestJobSummary, DatasetTestJobSummary];
}) {
  const [left, right] = runs;
  const leftResult = left.result;
  const rightResult = right.result;
  if (!leftResult || !rightResult) {
    return (
      <section className="dataset-comparison" aria-label="Dataset run comparison">
        <p>Both selected runs need a completed result before they can be compared.</p>
      </section>
    );
  }
  const taskNames = [
    ...new Set([
      ...Object.keys(leftResult.metric.tasks ?? {}),
      ...Object.keys(rightResult.metric.tasks ?? {})
    ])
  ].sort();
  const visibleTasks = taskNames.filter((task) => {
    const leftTask = leftResult.metric.tasks?.[task];
    const rightTask = rightResult.metric.tasks?.[task];
    return (leftTask?.total ?? 0) > 0 || (rightTask?.total ?? 0) > 0;
  });
  const overallDelta = rightResult.metric.accuracy - leftResult.metric.accuracy;
  const comparisonPartial = Boolean(
    leftResult.metric.partial ||
    rightResult.metric.partial ||
    leftResult.metric.missingTasks?.length ||
    rightResult.metric.missingTasks?.length
  );
  return (
    <section className="dataset-comparison" aria-labelledby="dataset-comparison-title">
      <header>
        <div>
          <span>Comparison</span>
          <h3 id="dataset-comparison-title">
            {leftResult.algorithm.name}
            {" vs "}
            {rightResult.algorithm.name}
          </h3>
          <p>
            {shortModelName(left.request.model)} · {formatDate(left.createdAt)}
            {" → "}
            {shortModelName(right.request.model)} · {formatDate(right.createdAt)}
          </p>
        </div>
        <div className={`dataset-comparison-delta ${overallDelta >= 0 ? "positive" : "negative"}`}>
          <small>Overall Δ</small>
          <strong>{formatRateDelta(overallDelta)}</strong>
          <span>B − A</span>
        </div>
      </header>
      {comparisonPartial && (
        <p className="dataset-comparison-warning" role="status">
          <AlertTriangle size={14} /> One or both selected runs are partial; only evaluated
          categories are comparable.
        </p>
      )}
      <div className="dataset-comparison-scroll">
        <table aria-label="Dataset run comparison">
          <thead>
            <tr>
              <th scope="col">Category</th>
              <th scope="col">A · {left.id.slice(0, 8)}</th>
              <th scope="col">B · {right.id.slice(0, 8)}</th>
              <th scope="col">Δ B − A</th>
            </tr>
          </thead>
          <tbody>
            <tr className="overall">
              <th scope="row">Overall score</th>
              <td>{formatPercent(leftResult.metric.accuracy)}</td>
              <td>{formatPercent(rightResult.metric.accuracy)}</td>
              <td className={overallDelta >= 0 ? "positive" : "negative"}>
                {formatRateDelta(overallDelta)}
              </td>
            </tr>
            {visibleTasks.map((task) => {
              const leftTask = leftResult.metric.tasks?.[task];
              const rightTask = rightResult.metric.tasks?.[task];
              const leftRate = leftTask && leftTask.total > 0 ? leftTask.correctionRate : null;
              const rightRate = rightTask && rightTask.total > 0 ? rightTask.correctionRate : null;
              const delta = leftRate !== null && rightRate !== null ? rightRate - leftRate : null;
              return (
                <tr key={task}>
                  <th scope="row">{formatKey(task)}</th>
                  <td>{formatTaskRate(leftTask, leftRate)}</td>
                  <td>{formatTaskRate(rightTask, rightRate)}</td>
                  <td className={delta === null ? "" : delta >= 0 ? "positive" : "negative"}>
                    {delta === null ? "—" : formatRateDelta(delta)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="dataset-comparison-note">
        Positive Δ means run B repaired a larger share of baseline failures. Overall score is the
        benchmark macro score, not raw sample accuracy.
      </p>
    </section>
  );
}

function formatTaskRate(task: DatasetTaskResult | undefined, rate: number | null) {
  if (!task || task.total === 0) return "Not evaluated";
  if (rate === null) return "—";
  if (task.baselineFailure === 0) return `${formatPercent(rate)} (no failures)`;
  return `${formatPercent(rate)} (${task.failureToSuccess}/${task.baselineFailure})`;
}

function formatRateDelta(value: number) {
  const points = value * 100;
  return `${points > 0 ? "+" : ""}${points.toFixed(2)} pp`;
}

function datasetAlgorithmName(id: DatasetAlgorithm["id"], algorithms: DatasetAlgorithm[]) {
  return algorithms.find((item) => item.id === id)?.name ??
    (id === "pca_minus_neg" ? "PCA steering" : "Mean steering");
}

function historyStatusLabel(status: DatasetTestJobSummary["status"]) {
  switch (status) {
    case "idle": return "Queued";
    case "loading": return "Running";
    case "ready": return "Complete";
    case "error": return "Failed";
    case "cancelled": return "Cancelled";
  }
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatDuration(seconds: number) {
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function csvValue(value: unknown) {
  const text = value === undefined || value === null ? "" : String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function downloadTextFile(name: string, mime: string, content: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportDatasetJson(job: DatasetTestJob) {
  if (!job.result) return;
  downloadTextFile(
    `dataset-test-${job.id.slice(0, 8)}-${job.result.algorithm.id}.json`,
    "application/json",
    JSON.stringify({
      exportedAt: new Date().toISOString(),
      job: { id: job.id, createdAt: job.createdAt, request: job.request },
      result: job.result
    }, null, 2)
  );
}

function exportDatasetCsv(job: DatasetTestJob) {
  if (!job.result) return;
  const columns = [
    "sampleId",
    "category",
    "task",
    "status",
    "passed",
    "baselinePrediction",
    "steeredPrediction",
    "baselineSuccess",
    "steeredSuccess",
    "steeringApplied",
    "original",
    "steered",
    "detail"
  ];
  const lines = [
    columns.join(","),
    ...job.result.rows.map((row) => {
      const record = row as unknown as Record<string, unknown>;
      return columns.map((column) => csvValue(record[column])).join(",");
    })
  ];
  downloadTextFile(
    `dataset-test-${job.id.slice(0, 8)}-${job.result.algorithm.id}.csv`,
    "text/csv",
    lines.join("\n")
  );
}

function DatasetJobResults({
  job,
  filter,
  onFilter
}: {
  job: DatasetTestJob;
  filter: "all" | "passed" | "failed";
  onFilter: (filter: "all" | "passed" | "failed") => void;
}) {
  const [taskFilter, setTaskFilter] = useState("all");
  const [resultQuery, setResultQuery] = useState("");
  const [visibleLimit, setVisibleLimit] = useState(50);
  const elapsed = useElapsed(
    job.createdAt,
    job.status === "idle" || job.status === "loading"
  );
  const taskOptions = useMemo(
    () => [...new Set((job.result?.rows ?? []).map((row) => row.task ?? row.category))].sort(),
    [job.result]
  );
  useEffect(() => {
    setVisibleLimit(50);
  }, [filter, taskFilter, resultQuery, job.id]);
  if (job.status !== "ready" || !job.result) {
    const running = job.status === "idle" || job.status === "loading";
    const eta = running && job.progress > 2
      ? Math.max(0, Math.round(elapsed * (100 - job.progress) / job.progress))
      : null;
    return (
      <section className="dataset-job-progress" aria-live="polite">
        <header><span>3 / Test run</span><strong>{job.detail}</strong><b>{job.progress}%</b></header>
        <div><i style={{ width: `${job.progress}%` }} /></div>
        <div className="dataset-job-progress-meta">
          <span><Clock3 size={13} /> Elapsed {formatDuration(elapsed)}</span>
          {eta !== null && <span>ETA ~{formatDuration(eta)}</span>}
          <span>Stage: {formatKey(job.stage)}</span>
        </div>
        {job.taskProgress && <DatasetTaskProgress tasks={job.taskProgress} />}
        {job.error && <p>{job.error}</p>}
      </section>
    );
  }
  const result = job.result;
  const query = resultQuery.trim().toLowerCase();
  const filteredRows = result.rows.filter((row) => {
    if (filter !== "all" && (filter === "passed" ? !row.passed : row.passed)) return false;
    const category = row.task ?? row.category;
    if (taskFilter !== "all" && category !== taskFilter) return false;
    if (!query) return true;
    return `${row.sampleId} ${row.prompt} ${row.category} ${row.task ?? ""} ${row.detail}`
      .toLowerCase()
      .includes(query);
  });
  const rows = filteredRows.slice(0, visibleLimit);
  const missingTasks = result.metric.missingTasks ?? [];
  const partial = result.metric.partial === true || missingTasks.length > 0;
  const scoreLabel = missingTasks.length > 0
    ? "Incomplete result"
    : partial
      ? "Partial result"
      : result.metric.meetsThreshold
        ? "Threshold met"
        : "Below threshold";
  return (
    <section className="dataset-results" aria-labelledby="dataset-results-title">
      <header className={result.metric.meetsThreshold ? "passed" : "failed"}>
        <div>
          <span>3 / Results</span>
          <h2 id="dataset-results-title">{result.dataset.name}</h2>
          <p>
            {result.execution.model} / {result.execution.layer === undefined
              ? "fixed task layers"
              : `L${result.execution.layer}`}
            {result.execution.requestedLayer !== undefined &&
              result.execution.requestedLayer !== result.execution.layer
              ? ` (requested L${result.execution.requestedLayer})`
              : ""} / {result.execution.source}
            {result.execution.device ? ` / ${result.execution.device}` : ""}
            {result.execution.dtype ? ` / ${result.execution.dtype}` : ""}
            {result.execution.judgeModel ? ` / judge ${result.execution.judgeModel}` : ""}
          </p>
        </div>
        <div className="dataset-score">
          {result.metric.meetsThreshold ? <CheckCircle2 size={24} /> : <XCircle size={24} />}
          <strong>{formatPercent(result.metric.accuracy)}</strong>
          <span>{scoreLabel}</span>
        </div>
        <dl>
          <div><dt>Baseline failures</dt><dd>{result.metric.baselineFailure ?? 0}</dd></div>
          <div><dt>Repaired</dt><dd>{result.metric.failureToSuccess ?? 0}</dd></div>
          <div><dt>Completed</dt><dd>{result.metric.completed}</dd></div>
          <div><dt>Errors</dt><dd>{result.metric.errors}</dd></div>
          <div><dt>Repair target</dt><dd>{formatPercent(result.metric.threshold)}</dd></div>
        </dl>
      </header>
      {partial && (
        <div className="dataset-partial-warning" role="status">
          <AlertTriangle size={17} />
          <span>
            {missingTasks.length > 0
              ? `${missingTasks.join(", ")} ${missingTasks.length === 1 ? "task was" : "tasks were"} not evaluated.`
              : "Some samples were not evaluated."}
            {result.metric.errors > 0
              ? ` ${result.metric.errors} sample${result.metric.errors === 1 ? "" : "s"} reported errors.`
              : ""}
            {" "}The displayed score covers only evaluated tasks and cannot satisfy the benchmark threshold.
          </span>
        </div>
      )}
      <DatasetTaskSummary tasks={result.metric.tasks} />
      <div className="dataset-result-toolbar">
        <div role="tablist" aria-label="Result filter">
          {(["all", "passed", "failed"] as const).map((item) => (
            <button key={item} role="tab" aria-selected={filter === item} className={filter === item ? "active" : ""} onClick={() => onFilter(item)}>{item === "all" ? "All samples" : item === "passed" ? "Correct" : "Incorrect"}</button>
          ))}
        </div>
        <div className="dataset-result-meta">
          <span><Database size={14} /> {result.dataset.version} / {result.algorithm.implementation.replace(/_/g, " ")}</span>
          <div className="dataset-export-actions">
            <button type="button" aria-label="Export JSON" onClick={() => exportDatasetJson(job)}><Download size={14} /> JSON</button>
            <button type="button" aria-label="Export CSV" onClick={() => exportDatasetCsv(job)}><Download size={14} /> CSV</button>
          </div>
        </div>
      </div>
      <div className="dataset-result-filters">
        <label>
          <span>Category</span>
          <select
            aria-label="Filter results by category"
            value={taskFilter}
            onChange={(event) => setTaskFilter(event.target.value)}
          >
            <option value="all">All categories</option>
            {taskOptions.map((task) => <option key={task} value={task}>{formatKey(task)}</option>)}
          </select>
        </label>
        <div className="dataset-result-search">
          <Search size={14} />
          <input
            aria-label="Search dataset results"
            placeholder="Search sample or prompt"
            value={resultQuery}
            onChange={(event) => setResultQuery(event.target.value)}
          />
          {resultQuery && (
            <button type="button" aria-label="Clear dataset result search" onClick={() => setResultQuery("")}>
              <X size={13} />
            </button>
          )}
        </div>
        <span>Showing {rows.length} of {filteredRows.length}</span>
      </div>
      <div className="dataset-result-list">
        {rows.map((row) => <DatasetResultRow key={row.sampleId} row={row} result={result} />)}
        {!rows.length && <p className="dataset-empty-filter">No samples match the current filters.</p>}
        {filteredRows.length > visibleLimit && (
          <button
            type="button"
            className="dataset-load-more"
            onClick={() => setVisibleLimit((current) => current + 50)}
          >
            Show {Math.min(50, filteredRows.length - visibleLimit)} more samples
          </button>
        )}
      </div>
    </section>
  );
}

function useElapsed(createdAt: string, active: boolean) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [active]);
  const started = Date.parse(createdAt);
  return Number.isFinite(started) ? Math.max(0, (now - started) / 1000) : 0;
}

function DatasetTaskProgress({
  tasks
}: {
  tasks: NonNullable<DatasetTestJob["taskProgress"]>;
}) {
  const entries = Object.entries(tasks).filter(
    ([, counts]) => counts.baselineTotal > 0 || counts.steeringTotal > 0
  );
  if (entries.length === 0) return null;
  return (
    <div className="dataset-task-progress" aria-label="Per-category progress">
      {entries.map(([task, counts]) => (
        <span key={task}>
          <strong>{formatKey(task)}</strong>
          {counts.baselineTotal > 0 && (
            <small>baseline {counts.baselineCompleted}/{counts.baselineTotal}</small>
          )}
          {counts.steeringTotal > 0 && (
            <small>steered {counts.steeringCompleted}/{counts.steeringTotal}</small>
          )}
        </span>
      ))}
    </div>
  );
}

function DatasetResultRow({ row, result }: {
  row: DatasetTestResult["rows"][number];
  result: DatasetTestResult;
}) {
  const modified = row.steered ?? row.patched;
  return (
    <article className={`dataset-result-row ${row.passed ? "passed" : "failed"}`}>
      <header>
        {row.passed ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
        <div><strong>{row.sampleId}</strong><span>{row.category}</span></div>
        <b>{row.status === "error" ? "Error" : row.passed ? "Correct" : "Incorrect"}</b>
      </header>
      <p className="dataset-result-prompt">{row.prompt}</p>
      <p className="dataset-result-detail">{row.detail}</p>
      {(row.original !== undefined || modified !== undefined) && (
        <div className="dataset-output-compare">
          <div><span>Original</span><p>{row.original || "No visible continuation"}</p></div>
          <div><span>Steered</span><p>{row.steeringApplied === false ? "Not run (baseline successful)" : modified || "No visible continuation"}</p></div>
        </div>
      )}
      {row.diagnostics && (
        <dl className="dataset-diagnostics">
          {Object.entries(row.diagnostics).slice(0, 6).map(([key, value]) => (
            <div key={key}><dt>{formatKey(key)}</dt><dd>{formatDiagnostic(value)}</dd></div>
          ))}
        </dl>
      )}
    </article>
  );
}

function shortModelName(model: string) {
  const parts = model.split("/");
  return parts[parts.length - 1] || model;
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function formatKey(value: string) {
  return value.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/_/g, " ");
}

function formatDiagnostic(value: unknown) {
  if (Array.isArray(value)) return value.length > 8 ? `${value.slice(0, 8).join(", ")}...` : value.join(", ");
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(5);
  return String(value);
}
