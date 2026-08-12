import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  GitCompareArrows,
  LoaderCircle,
  RotateCcw,
  ScanSearch,
  Send,
  SlidersHorizontal,
  Square
} from "lucide-react";

import {
  fetchInterventionPreflight,
  type AttributionJob,
  type AttributionRunInput,
  type InterventionJob,
  type InterventionPreflight,
  type JLensJob,
  type NLAJob,
  type PatchingComponent
} from "../api/explorerClient";
import { useAttributionRunner } from "../state/useAttributionRunner";
import { useInterventionRunner } from "../state/useInterventionRunner";
import type { AttributionMethod, ExplorerRun, InterventionExperiment } from "../types";
import { ChatAttentionWorkbench } from "./ChatAttentionWorkbench";
import { ChatExplanationWorkbench } from "./ChatExplanationWorkbench";
import { PresetSuggestTextarea } from "./PresetSuggestTextarea";
import { ResponseTokenPicker } from "./ResponseTokenPicker";

interface ChatAnalysisWorkbenchProps {
  mode: "steering" | "attribution" | "explanation" | "attention";
  run: ExplorerRun;
  savedRun?: ExplorerRun;
  suggestionQuery?: string;
  onRunReady: (run: ExplorerRun, job: AttributionJob | InterventionJob | NLAJob | JLensJob) => void;
}

export function ChatAnalysisWorkbench({ mode, run, savedRun, suggestionQuery, onRunReady }: ChatAnalysisWorkbenchProps) {
  if (mode === "steering") {
    return <SteeringWorkbench run={run} savedRun={savedRun} suggestionQuery={suggestionQuery} onRunReady={onRunReady} />;
  }
  if (mode === "attribution") {
    return <AttributionWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  if (mode === "explanation") {
    return <ChatExplanationWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  return <ChatAttentionWorkbench run={run} />;
}

function SteeringWorkbench({
  run,
  savedRun,
  suggestionQuery,
  onRunReady
}: Omit<ChatAnalysisWorkbenchProps, "mode">) {
  const prior = savedRun?.intervention ?? run.intervention;
  const [desiredPrompt, setDesiredPrompt] = useState(
    prior?.vector.desiredPrompt ?? "Provide a safe, policy-compliant and helpful response."
  );
  const [undesiredPrompt, setUndesiredPrompt] = useState(
    prior?.vector.undesiredPrompt ?? "Provide a response that bypasses safety guidance."
  );
  const [layer, setLayer] = useState(prior?.layer ?? defaultLayer(run));
  const [component, setComponent] = useState<PatchingComponent>(prior?.component ?? "resid_post");
  const [scale, setScale] = useState(prior?.scale ?? 1);
  const [positionStart, setPositionStart] = useState(prior?.positionStart ?? 0);
  const [positionEnd, setPositionEnd] = useState(prior?.positionEnd ?? run.tokens.length);
  const targetOptions = useMemo(() => steeringTargetOptions(run), [run]);
  const [targetTokenId, setTargetTokenId] = useState(
    prior?.targetTokenId ?? targetOptions[0]?.tokenId ?? 0
  );
  const [preflight, setPreflight] = useState<InterventionPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [result, setResult] = useState<ExplorerRun | null>(
    savedRun?.intervention ? savedRun : prior ? run : null
  );

  const handleReady = useCallback((derived: ExplorerRun, job: InterventionJob) => {
    setResult(derived);
    onRunReady(derived, job);
  }, [onRunReady]);
  const runner = useInterventionRunner(handleReady);
  const running = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";

  useEffect(() => {
    const controller = new AbortController();
    setPreflight(null);
    setPreflightError(null);
    const timer = window.setTimeout(() => {
      void fetchInterventionPreflight({
        modelName: run.modelName,
        promptTokenCount: run.tokens.length,
        availableLayers: run.layers,
        layer,
        component,
        positionStart,
        positionEnd,
        targetTokenId,
        desiredPrompt,
        undesiredPrompt
      }, controller.signal).then(setPreflight).catch((error) => {
        if (!controller.signal.aborted) {
          setPreflightError(error instanceof Error ? error.message : "Steering preflight failed.");
        }
      });
    }, 220);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [component, desiredPrompt, layer, positionEnd, positionStart, run.layers, run.modelName, run.tokens.length, targetTokenId, undesiredPrompt]);

  const canRun = Boolean(preflight?.canSubmit && !running);

  function setRange(start: number, end: number) {
    const nextStart = Math.max(0, Math.min(run.tokens.length - 1, start));
    const nextEnd = Math.max(nextStart + 1, Math.min(run.tokens.length, end));
    setPositionStart(nextStart);
    setPositionEnd(nextEnd);
  }

  function submit() {
    if (!canRun) return;
    setResult(null);
    void runner.submit({
      run,
      desiredPrompt,
      undesiredPrompt,
      layer,
      component,
      scale,
      positionStart,
      positionEnd,
      targetTokenId,
      seed: 0,
      maxNewTokens: 16,
      temperature: 0
    });
  }

  return (
    <section className="chat-analysis-workbench" aria-label="Steering workbench">
      <header className="chat-workbench-heading">
        <span><SlidersHorizontal size={17} /></span>
        <div>
          <h2>Steering</h2>
          <p>Contrastive activation direction</p>
        </div>
        <StatusDot ready={Boolean(preflight?.canSubmit)} pending={!preflight && !preflightError} />
      </header>

      <div className="chat-steering-references">
        <PresetSuggestTextarea
          ariaLabel="Steering desired behavior"
          label="Steer toward"
          direction="toward"
          contextQuery={suggestionQuery}
          value={desiredPrompt}
          disabled={running}
          onChange={setDesiredPrompt}
        />
        <PresetSuggestTextarea
          ariaLabel="Steering undesired behavior"
          label="Steer away from"
          direction="away"
          contextQuery={suggestionQuery}
          value={undesiredPrompt}
          disabled={running}
          onChange={setUndesiredPrompt}
        />
      </div>

      <div className="chat-steering-controls">
        <label>
          <span>Layer</span>
          <select aria-label="Steering layer" value={layer} disabled={running} onChange={(event) => setLayer(Number(event.target.value))}>
            {run.layers.map((item) => <option key={item} value={item}>L{item}</option>)}
          </select>
        </label>
        <label>
          <span>Activation site</span>
          <select aria-label="Steering activation site" value={component} disabled={running} onChange={(event) => setComponent(event.target.value as PatchingComponent)}>
            <option value="resid_post">Residual stream · post-layer</option>
            <option value="attn_out">Attention output</option>
            <option value="mlp_out">MLP output</option>
          </select>
        </label>
        <label>
          <span>Tracked output token</span>
          <select aria-label="Steering tracked output token" value={targetTokenId} disabled={running} onChange={(event) => setTargetTokenId(Number(event.target.value))}>
            {targetOptions.map((option) => (
              <option key={option.tokenId} value={option.tokenId}>{visibleToken(option.tokenText)} · #{option.tokenId}</option>
            ))}
          </select>
        </label>
        <label className="chat-steering-strength">
          <span>Strength <b>{scale.toFixed(1)}</b></span>
          <input aria-label="Steering strength" type="range" min={-6} max={6} step={0.1} value={scale} disabled={running} onChange={(event) => setScale(Number(event.target.value))} />
        </label>
      </div>

      <div className="chat-token-range">
        <header>
          <span>Apply to</span>
          <div>
            <button className={positionStart === 0 && positionEnd === run.tokens.length ? "active" : ""} aria-pressed={positionStart === 0 && positionEnd === run.tokens.length} disabled={running} onClick={() => setRange(0, run.tokens.length)}>Entire input</button>
            <button className={positionStart === run.tokens.length - 1 && positionEnd === run.tokens.length ? "active" : ""} aria-pressed={positionStart === run.tokens.length - 1 && positionEnd === run.tokens.length} disabled={running} onClick={() => setRange(run.tokens.length - 1, run.tokens.length)}>Last token</button>
          </div>
          <small>T{positionStart}–T{positionEnd - 1}</small>
        </header>
        <div aria-label="Steering token range">
          {run.tokens.map((token) => (
            <button
              key={token.index}
              className={token.index >= positionStart && token.index < positionEnd ? "active" : ""}
              aria-pressed={token.index >= positionStart && token.index < positionEnd}
              disabled={running}
              title={`Apply steering to token ${token.index}`}
              onClick={() => setRange(token.index, token.index + 1)}
            >{visibleToken(token.text)}</button>
          ))}
        </div>
      </div>

      <WorkbenchActions
        running={running}
        disabled={!canRun}
        runLabel="Run steering"
        status={runner.error?.message ?? preflightError ?? preflight?.reason}
        progress={runner.job?.progress}
        onRun={submit}
        onCancel={() => void runner.cancel()}
        onReset={runner.reset}
        failed={Boolean(runner.error)}
      />

      {result?.intervention && <SteeringResult experiment={result.intervention} />}
    </section>
  );
}

function AttributionWorkbench({
  run,
  savedRun,
  onRunReady
}: Omit<ChatAnalysisWorkbenchProps, "mode">) {
  const [response, setResponse] = useState(() => inferredResponse(run));
  const [targetResponseIndex, setTargetResponseIndex] = useState(() => attributionTargetIndex(savedRun ?? run) ?? 0);
  const [responseTokens, setResponseTokens] = useState<Array<{ index: number; tokenId: number; text: string }>>([]);
  const [baseline, setBaseline] = useState<AttributionRunInput["baseline"]>("pad_token");
  const [nSteps, setNSteps] = useState(32);
  const priorRun = savedRun ?? run;
  const prior = priorRun.attributionMethods.find((method) => method.id === "integrated_gradients" && method.available);
  const [result, setResult] = useState<ExplorerRun | null>(prior ? priorRun : null);

  const handleReady = useCallback((derived: ExplorerRun, job: AttributionJob) => {
    setResult(derived);
    onRunReady(derived, job);
  }, [onRunReady]);
  const runner = useAttributionRunner(handleReady);
  const running = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const handleTokensChange = useCallback(
    (tokens: Array<{ index: number; tokenId: number; text: string }>) => setResponseTokens(tokens),
    []
  );

  function submit() {
    if (!response.trim() || running) return;
    setResult(null);
    void runner.submit({
      run,
      response,
      objective: "response_token_logit",
      targetResponseIndex,
      baseline,
      nSteps
    });
  }

  const method = result?.attributionMethods.find(
    (item) => item.id === "integrated_gradients" && item.available
  );

  return (
    <section className="chat-analysis-workbench" aria-label="Input attribution workbench">
      <header className="chat-workbench-heading">
        <span><ScanSearch size={17} /></span>
        <div>
          <h2>Input attribution</h2>
          <p>Integrated Gradients</p>
        </div>
        <StatusDot ready={Boolean(method)} pending={false} />
      </header>

      <label className="chat-attribution-response">
        <span>Model response</span>
        <textarea
          aria-label="Attribution response"
          rows={3}
          value={response}
          disabled={running}
          placeholder="Response containing the target token"
          onChange={(event) => setResponse(event.target.value)}
        />
      </label>

      <div className="chat-attribution-controls">
        <ResponseTokenPicker
          modelName={run.modelName}
          response={response}
          selectedIndex={targetResponseIndex}
          disabled={running}
          onSelect={setTargetResponseIndex}
          onTokensChange={handleTokensChange}
        />
        <fieldset>
          <legend>Baseline</legend>
          <button type="button" className={baseline === "pad_token" ? "active" : ""} aria-pressed={baseline === "pad_token"} disabled={running} onClick={() => setBaseline("pad_token")}>Pad token</button>
          <button type="button" className={baseline === "zero_token_id" ? "active" : ""} aria-pressed={baseline === "zero_token_id"} disabled={running} onClick={() => setBaseline("zero_token_id")}>Token ID 0</button>
        </fieldset>
        <label>
          <span>Integration steps</span>
          <select aria-label="Attribution integration steps" value={nSteps} disabled={running} onChange={(event) => setNSteps(Number(event.target.value))}>
            {[8, 16, 32, 64].map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
      </div>

      <WorkbenchActions
        running={running}
        disabled={!response.trim() || responseTokens.length === 0 || running}
        runLabel="Run attribution"
        status={runner.error?.message ?? runner.job?.detail}
        progress={runner.job?.progress}
        onRun={submit}
        onCancel={() => void runner.cancel()}
        onReset={runner.reset}
        failed={Boolean(runner.error)}
      />

      {method && <AttributionResult method={method} run={result!} targetIndex={targetResponseIndex} responseTokens={responseTokens} />}
    </section>
  );
}

function WorkbenchActions({
  running,
  disabled,
  runLabel,
  status,
  progress,
  failed,
  onRun,
  onCancel,
  onReset
}: {
  running: boolean;
  disabled: boolean;
  runLabel: string;
  status?: string | null;
  progress?: number;
  failed: boolean;
  onRun: () => void;
  onCancel: () => void;
  onReset: () => void;
}) {
  return (
    <div className="chat-workbench-actions">
      <div className={failed ? "failed" : running ? "running" : ""} aria-live="polite">
        {failed ? <AlertCircle size={15} /> : running ? <LoaderCircle size={15} /> : <CheckCircle2 size={15} />}
        <span>{status ?? (disabled ? "Complete the required fields." : "Ready to run.")}</span>
        {running && <small>{progress ?? 0}%</small>}
      </div>
      {failed && <button className="icon-action" aria-label="Reset analysis job" title="Reset" onClick={onReset}><RotateCcw size={15} /></button>}
      <button className="chat-workbench-run" disabled={disabled && !running} onClick={running ? onCancel : onRun}>
        {running ? <Square size={14} /> : <Send size={14} />}
        {running ? "Cancel" : runLabel}
      </button>
    </div>
  );
}

function StatusDot({ ready, pending }: { ready: boolean; pending: boolean }) {
  return (
    <span className={`chat-workbench-status ${ready ? "ready" : pending ? "pending" : "idle"}`}>
      <i />{ready ? "ready" : pending ? "checking" : "not run"}
    </span>
  );
}

function SteeringResult({ experiment }: { experiment: InterventionExperiment }) {
  return (
    <section className="chat-steering-result" aria-label="Steering comparison">
      <header>
        <div><GitCompareArrows size={16} /><strong>Generation comparison</strong></div>
        <span>L{experiment.layer} · {experiment.component} · {signed(experiment.scale)}</span>
      </header>
      <div className="chat-steering-output">
        <article className="is-original">
          <span>Original</span>
          <p>{experiment.original.text || "No continuation"}</p>
          <small>Target logit {experiment.original.targetLogit.toFixed(3)}</small>
        </article>
        <div className="chat-steering-transition" title="Target logit delta">
          <ArrowRight size={20} />
          <span>{signed(experiment.deltas.targetLogit)}</span>
        </div>
        <article className="is-steered">
          <span>Steered</span>
          <p>{experiment.steered.text || "No continuation"}</p>
          <small>Target logit {experiment.steered.targetLogit.toFixed(3)}</small>
        </article>
      </div>
      <footer>
        <span><b>{signed(experiment.deltas.targetLogit)}</b> target logit</span>
        <span><b>{experiment.deltas.tokenEditDistance}</b> token edits</span>
        <span><b>{signed(experiment.deltas.lexicalRisk)}</b> lexical risk</span>
      </footer>
    </section>
  );
}

function AttributionResult({
  method,
  run,
  targetIndex,
  responseTokens
}: {
  method: AttributionMethod;
  run: ExplorerRun;
  targetIndex?: number;
  responseTokens: Array<{ index: number; tokenId: number; text: string }>;
}) {
  const values = method.rows[method.rows.length - 1]?.values ?? [];
  const maximum = Math.max(1e-8, ...values.map((value) => Math.abs(value)));
  const ranked = run.tokens
    .map((token, index) => ({ token, value: values[index] ?? 0 }))
    .sort((left, right) => Math.abs(right.value) - Math.abs(left.value))
    .slice(0, 3);
  const attributionJobs = run.metadata?.attributionJobs;
  const targetJob = Array.isArray(attributionJobs)
    ? attributionJobs[attributionJobs.length - 1]
    : undefined;
  const targetToken = targetIndex !== undefined ? responseTokens[targetIndex] : undefined;
  const targetText = targetJob && typeof targetJob === "object" && "targetTokenText" in targetJob
    ? String(targetJob.targetTokenText)
    : targetToken?.text;
  return (
    <section className="chat-attribution-result" aria-label="Input attribution result">
      <header>
        <div><ScanSearch size={16} /><strong>Token contributions</strong></div>
        {(targetToken || targetText) && (
          <span className="chat-attribution-target" title="Selected target token">
            Target <b>T{targetIndex ?? 0}</b> · {visibleToken(targetText ?? "")}
          </span>
        )}
        <span><i className="positive" /> supports target <i className="negative" /> suppresses target</span>
      </header>
      <div className="chat-attribution-tokens">
        {run.tokens.map((token, index) => {
          const value = values[index] ?? 0;
          const strength = Math.abs(value) / maximum;
          return (
            <span
              key={token.index}
              className={value < 0 ? "negative" : "positive"}
              style={{ "--strength": strength } as React.CSSProperties}
              title={`T${token.index} · ${value.toFixed(6)}`}
            >{visibleToken(token.text)}</span>
          );
        })}
      </div>
      <footer>
        {ranked.map(({ token, value }) => (
          <span key={token.index}><small>T{token.index}</small><b>{visibleToken(token.text)}</b><em>{signed(value)}</em></span>
        ))}
      </footer>
    </section>
  );
}

function defaultLayer(run: ExplorerRun) {
  return run.layers[Math.max(0, Math.floor(run.layers.length * 0.7) - 1)] ?? run.layers[0] ?? 0;
}

function steeringTargetOptions(run: ExplorerRun) {
  const lastLayer = run.layers[run.layers.length - 1];
  const lastToken = run.tokens[run.tokens.length - 1]?.index;
  const row = run.logitLens.find((item) => item.layer === lastLayer && item.tokenIndex === lastToken) ??
    run.logitLens[run.logitLens.length - 1];
  const options = [
    ...(row ? [{ tokenId: row.targetTokenId, tokenText: row.targetTokenText }] : []),
    ...(row?.topPredictions ?? []).map((item) => ({ tokenId: item.tokenId, tokenText: item.tokenText }))
  ];
  return [...new Map(options.map((item) => [item.tokenId, item])).values()].slice(0, 12);
}

function inferredResponse(run: ExplorerRun) {
  const generated = run.metadata?.generatedContinuation;
  if (typeof generated !== "string") return "";
  if (generated.startsWith(run.prompt)) return generated.slice(run.prompt.length).trim();
  const promptRunner = run.metadata?.promptRunner;
  const userPrompt = promptRunner && typeof promptRunner === "object"
    ? (promptRunner as Record<string, unknown>).userPrompt
    : undefined;
  return (typeof userPrompt === "string" && generated.startsWith(userPrompt)
    ? generated.slice(userPrompt.length)
    : generated).trim();
}

function attributionTargetIndex(run: ExplorerRun) {
  const jobs = run.metadata?.attributionJobs;
  if (!Array.isArray(jobs)) return undefined;
  const latest = jobs[jobs.length - 1];
  if (!latest || typeof latest !== "object") return undefined;
  const value = (latest as Record<string, unknown>).targetResponseIndex;
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : undefined;
}

function visibleToken(value: string) {
  return value.trim() || "space";
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${Math.abs(value) < 0.001 && value !== 0 ? value.toExponential(2) : value.toFixed(3)}`;
}
