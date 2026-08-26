import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  CheckSquare2,
  Database,
  ExternalLink,
  FileCheck2,
  FlaskConical,
  LoaderCircle,
  Play,
  Square,
  StopCircle,
  XCircle
} from "lucide-react";

import {
  cancelDatasetTestJob,
  fetchDatasetCatalog,
  fetchDatasetTestJob,
  fetchPromptOptions,
  submitDatasetTestJob,
  type DatasetAlgorithm,
  type DatasetDefinition,
  type DatasetTestJob,
  type DatasetTestResult
} from "../api/explorerClient";

const DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct";

export function DatasetTestScreen({ onOpenChat }: { onOpenChat: () => void }) {
  const [datasets, setDatasets] = useState<DatasetDefinition[]>([]);
  const [algorithms, setAlgorithms] = useState<DatasetAlgorithm[]>([]);
  const [algorithmId, setAlgorithmId] = useState<DatasetAlgorithm["id"]>("steering");
  const [datasetId, setDatasetId] = useState("safelens-steering-v1");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [models, setModels] = useState([DEFAULT_MODEL]);
  const [model, setModel] = useState(DEFAULT_MODEL);
  const [layer, setLayer] = useState(12);
  const [strength, setStrength] = useState(1);
  const [maxNewTokens, setMaxNewTokens] = useState(24);
  const [job, setJob] = useState<DatasetTestJob | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [resultFilter, setResultFilter] = useState<"all" | "passed" | "failed">("all");

  const algorithm = algorithms.find((item) => item.id === algorithmId);
  const compatibleDatasets = useMemo(
    () => datasets.filter((item) => algorithm?.supportedDatasetIds.includes(item.id)),
    [algorithm, datasets]
  );
  const dataset = compatibleDatasets.find((item) => item.id === datasetId) ?? compatibleDatasets[0];
  const running = job?.status === "idle" || job?.status === "loading";

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      fetchDatasetCatalog(controller.signal),
      fetchPromptOptions(controller.signal)
    ]).then(([catalog, options]) => {
      setDatasets(catalog.datasets);
      setAlgorithms(catalog.algorithms);
      setModels(options.models);
      if (!options.models.includes(DEFAULT_MODEL)) setModel(options.models[0]);
      const first = catalog.datasets.find((item) => item.id === "safelens-steering-v1") ?? catalog.datasets[0];
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

  function chooseAlgorithm(next: DatasetAlgorithm) {
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
    setRunError(null);
    setResultFilter("all");
    try {
      const next = await submitDatasetTestJob({
        datasetId: dataset.id,
        algorithmId: algorithm.id,
        model,
        sampleIds: dataset.samples.filter((item) => selectedIds.has(item.id)).map((item) => item.id),
        layer,
        strength,
        seed: 0,
        maxNewTokens
      });
      setJob(next);
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Dataset test could not start.");
    }
  }

  async function cancelTest() {
    if (!job) return;
    try {
      setJob(await cancelDatasetTestJob(job.id));
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Dataset test could not be cancelled.");
    }
  }

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
            <div><dt>Pass target</dt><dd>{formatPercent(dataset?.metric.threshold ?? 0)}</dd></div>
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
                          <small>{sample.id} / {sample.category}</small>
                          <strong>{sample.prompt ?? sample.corruptedPrompt}</strong>
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
                    {item.id === "steering" ? <FileCheck2 size={18} /> : <FlaskConical size={18} />}
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
                  <span>Required pass rate &gt; {formatPercent(dataset.metric.threshold)}</span>
                </div>
              )}
              <div className="dataset-run-controls">
                <label className="wide"><span>Local model</span><select value={model} disabled={running} onChange={(event) => setModel(event.target.value)}>{models.map((item) => <option key={item} value={item}>{shortModelName(item)}</option>)}</select></label>
                <label><span>Layer</span><input type="number" min={0} max={127} value={layer} disabled={running} onChange={(event) => setLayer(clampNumber(event.target.value, 0, 127))} /></label>
                <label><span>Output tokens</span><input type="number" min={1} max={64} value={maxNewTokens} disabled={running} onChange={(event) => setMaxNewTokens(clampNumber(event.target.value, 1, 64))} /></label>
                {algorithmId === "steering" && <label className="wide"><span>Steering strength <b>{strength.toFixed(1)}</b></span><input type="range" min={-5} max={5} step={0.5} value={strength} disabled={running} onChange={(event) => setStrength(Number(event.target.value))} /></label>}
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

        {job && <DatasetJobResults job={job} filter={resultFilter} onFilter={setResultFilter} />}
      </main>
    </div>
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
  if (job.status !== "ready" || !job.result) {
    return (
      <section className="dataset-job-progress" aria-live="polite">
        <header><span>3 / Test run</span><strong>{job.detail}</strong><b>{job.progress}%</b></header>
        <div><i style={{ width: `${job.progress}%` }} /></div>
        {job.error && <p>{job.error}</p>}
      </section>
    );
  }
  const result = job.result;
  const rows = result.rows.filter((row) =>
    filter === "all" || (filter === "passed" ? row.passed : !row.passed)
  );
  return (
    <section className="dataset-results" aria-labelledby="dataset-results-title">
      <header className={result.metric.meetsThreshold ? "passed" : "failed"}>
        <div>
          <span>3 / Results</span>
          <h2 id="dataset-results-title">{result.dataset.name}</h2>
          <p>
            {result.execution.model} / {result.execution.layer === undefined
              ? "automatic layer"
              : `L${result.execution.layer}`}
            {result.execution.requestedLayer !== undefined &&
              result.execution.requestedLayer !== result.execution.layer
              ? ` (requested L${result.execution.requestedLayer})`
              : ""} / {result.execution.source}
            {result.execution.device ? ` / ${result.execution.device}` : ""}
            {result.execution.dtype ? ` / ${result.execution.dtype}` : ""}
          </p>
        </div>
        <div className="dataset-score">
          {result.metric.meetsThreshold ? <CheckCircle2 size={24} /> : <XCircle size={24} />}
          <strong>{formatPercent(result.metric.accuracy)}</strong>
          <span>{result.metric.meetsThreshold ? "Threshold met" : "Below threshold"}</span>
        </div>
        <dl>
          <div><dt>Passed</dt><dd>{result.metric.passed}</dd></div>
          <div><dt>Completed</dt><dd>{result.metric.completed}</dd></div>
          <div><dt>Errors</dt><dd>{result.metric.errors}</dd></div>
          <div><dt>Target</dt><dd>{formatPercent(result.metric.threshold)}</dd></div>
        </dl>
      </header>
      <div className="dataset-result-toolbar">
        <div role="tablist" aria-label="Result filter">
          {(["all", "passed", "failed"] as const).map((item) => (
            <button key={item} role="tab" aria-selected={filter === item} className={filter === item ? "active" : ""} onClick={() => onFilter(item)}>{item === "all" ? "All samples" : item === "passed" ? "Correct" : "Incorrect"}</button>
          ))}
        </div>
        <span><Database size={14} /> {result.dataset.version} / {result.algorithm.implementation.replace(/_/g, " ")}</span>
      </div>
      <div className="dataset-result-list">
        {rows.map((row) => <DatasetResultRow key={row.sampleId} row={row} result={result} />)}
        {!rows.length && <p className="dataset-empty-filter">No samples in this result group.</p>}
      </div>
    </section>
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
          <div><span>{result.algorithm.id === "steering" ? "Steered" : "Patched"}</span><p>{modified || "No visible continuation"}</p></div>
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
  return `${Math.round(value * 100)}%`;
}

function clampNumber(value: string, minimum: number, maximum: number) {
  const parsed = Number.parseInt(value, 10);
  return Math.min(maximum, Math.max(minimum, Number.isFinite(parsed) ? parsed : minimum));
}

function formatKey(value: string) {
  return value.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/_/g, " ");
}

function formatDiagnostic(value: unknown) {
  if (Array.isArray(value)) return value.length > 8 ? `${value.slice(0, 8).join(", ")}...` : value.join(", ");
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(5);
  return String(value);
}
