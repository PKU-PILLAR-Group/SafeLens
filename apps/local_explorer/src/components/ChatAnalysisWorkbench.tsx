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
  fetchPatchingPreflight,
  type ActivationComponent,
  type AttributionJob,
  type AttributionRunInput,
  type InterventionJob,
  type InterventionPreflight,
  type JLensJob,
  type NLAJob,
  type PatchingComponent,
  type PatchingJob,
  type PatchingPreflight,
  type RemoteRunSummary
} from "../api/explorerClient";
import { useAttributionRunner } from "../state/useAttributionRunner";
import { useInterventionRunner } from "../state/useInterventionRunner";
import { usePatchingRunner } from "../state/usePatchingRunner";
import type {
  AttributionMethod,
  ExplorerRun,
  InterventionExperiment,
  PatchingCell,
  PatchingExperiment
} from "../types";
import { ChatAttentionWorkbench } from "./ChatAttentionWorkbench";
import { ChatExplanationWorkbench } from "./ChatExplanationWorkbench";
import { PresetSuggestTextarea } from "./PresetSuggestTextarea";
import { ResponseTokenPicker } from "./ResponseTokenPicker";

interface ChatAnalysisWorkbenchProps {
  mode: "steering" | "attribution" | "patching" | "explanation" | "attention";
  run: ExplorerRun;
  remoteSummary?: RemoteRunSummary;
  savedRun?: ExplorerRun;
  suggestionQuery?: string;
  onRunReady: (run: ExplorerRun, job: AttributionJob | InterventionJob | PatchingJob | NLAJob | JLensJob) => void;
}

export function ChatAnalysisWorkbench({ mode, run, remoteSummary, savedRun, suggestionQuery, onRunReady }: ChatAnalysisWorkbenchProps) {
  if (mode === "steering") {
    return <SteeringWorkbench run={run} savedRun={savedRun} suggestionQuery={suggestionQuery} onRunReady={onRunReady} />;
  }
  if (mode === "attribution") {
    return <AttributionWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  if (mode === "patching") {
    return <PatchingWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  if (mode === "explanation") {
    return <ChatExplanationWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  return <ChatAttentionWorkbench run={run} remoteSummary={remoteSummary} />;
}

function PatchingWorkbench({
  run,
  savedRun,
  onRunReady
}: Omit<ChatAnalysisWorkbenchProps, "mode">) {
  const prior = savedRun?.patching ?? run.patching;
  const [corruptedPrompt, setCorruptedPrompt] = useState(prior?.corruptedPrompt ?? run.prompt);
  const [component, setComponent] = useState<PatchingComponent>(prior?.component ?? "resid_post");
  const [layers, setLayers] = useState<number[]>(prior?.layers ?? defaultPatchingLayers(run.layers));
  const [head, setHead] = useState(prior?.head ?? 0);
  const [positions, setPositions] = useState<number[]>(prior?.positions ?? []);
  const targetOptions = useMemo(() => steeringTargetOptions(run), [run]);
  const [targetTokenId, setTargetTokenId] = useState(
    prior?.targetTokenId ?? targetOptions[0]?.tokenId ?? 0
  );
  const [preflight, setPreflight] = useState<PatchingPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [result, setResult] = useState<ExplorerRun | null>(
    savedRun?.patching ? savedRun : prior ? run : null
  );
  const sourceTokenIds = useMemo(() => run.tokens.map((token) => token.tokenId), [run.tokens]);

  const handleReady = useCallback((derived: ExplorerRun, job: PatchingJob) => {
    setResult(derived);
    onRunReady(derived, job);
  }, [onRunReady]);
  const runner = usePatchingRunner(handleReady);
  const running = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";

  useEffect(() => {
    const controller = new AbortController();
    setPreflight(null);
    setPreflightError(null);
    const timer = window.setTimeout(() => {
      void fetchPatchingPreflight({
        modelName: run.modelName,
        cleanPrompt: run.prompt,
        corruptedPrompt,
        cleanTokenIds: sourceTokenIds,
        layers: run.layers,
        component,
        targetTokenId
      }, controller.signal).then((next) => {
        setPreflight(next);
        setPositions((current) => {
          const valid = current.filter((position) => position < next.cleanTokenCount).slice(0, 8);
          return valid.length > 0 ? valid : next.changedPositions.slice(0, 8);
        });
      }).catch((error) => {
        if (!controller.signal.aborted) {
          setPreflightError(error instanceof Error ? error.message : "Patching preflight failed.");
        }
      });
    }, 260);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [component, corruptedPrompt, run.layers, run.modelName, run.prompt, sourceTokenIds, targetTokenId]);

  const patchCount = layers.length * positions.length;
  const headCount = attentionHeadCount(run, layers[0] ?? run.layers[0] ?? 0);
  const canRun = Boolean(preflight?.canSubmit && patchCount > 0 && patchCount <= 64 && !running);

  useEffect(() => {
    setHead((current) => Math.min(current, Math.max(0, headCount - 1)));
  }, [headCount]);

  function toggleLayer(layer: number) {
    if (component === "z") {
      setLayers([layer]);
      return;
    }
    setLayers((current) => current.includes(layer)
      ? current.length === 1 ? current : current.filter((item) => item !== layer)
      : current.length >= 8 ? current : [...current, layer].sort((left, right) => left - right));
  }

  function selectComponent(next: PatchingComponent) {
    setComponent(next);
    if (next === "z") setLayers((current) => [current[0] ?? run.layers[0] ?? 0]);
  }

  function togglePosition(position: number) {
    setPositions((current) => current.includes(position)
      ? current.length === 1 ? current : current.filter((item) => item !== position)
      : current.length >= 8 ? current : [...current, position].sort((left, right) => left - right));
  }

  function submit() {
    if (!canRun) return;
    setResult(null);
    void runner.submit({
      run,
      corruptedPrompt,
      component,
      layers,
      positions,
      ...(component === "z" ? { head } : {}),
      targetTokenId
    });
  }

  return (
    <section className="chat-analysis-workbench chat-patching-workbench" aria-label="Activation patching workbench">
      <header className="chat-workbench-heading">
        <span><GitCompareArrows size={17} /></span>
        <div>
          <h2>Activation patching</h2>
          <p>Clean activation replacement</p>
        </div>
        <StatusDot ready={Boolean(preflight?.canSubmit)} pending={!preflight && !preflightError} />
      </header>

      <div className="chat-patching-prompts">
        <label className="is-clean">
          <span>Clean <small>current run</small></span>
          <textarea aria-label="Clean patching input" rows={4} value={run.prompt} readOnly />
        </label>
        <label className="is-corrupt">
          <span>Corrupt <small>editable</small></span>
          <textarea
            aria-label="Corrupt patching input"
            rows={4}
            value={corruptedPrompt}
            disabled={running}
            aria-invalid={preflight && !preflight.canSubmit ? true : undefined}
            onChange={(event) => setCorruptedPrompt(event.target.value)}
          />
        </label>
      </div>

      <div className="chat-patching-controls">
        <fieldset>
          <legend>Activation site</legend>
          <div role="group" aria-label="Patching activation site">
            {(["resid_post", "attn_out", "z", "mlp_out"] as const).map((item) => (
              <button
                type="button"
                key={item}
                className={component === item ? "active" : ""}
                aria-pressed={component === item}
                disabled={running}
                onClick={() => selectComponent(item)}
              >{patchingComponentLabel(item)}</button>
            ))}
          </div>
        </fieldset>
        {component === "z" && (
          <label>
            <span>Attention head</span>
            <select aria-label="Patching attention head" value={head} disabled={running} onChange={(event) => setHead(Number(event.target.value))}>
              {Array.from({ length: headCount }, (_, index) => <option key={index} value={index}>H{index}</option>)}
            </select>
          </label>
        )}
        <label>
          <span>Tracked output token</span>
          <select aria-label="Patching tracked output token" value={targetTokenId} disabled={running} onChange={(event) => setTargetTokenId(Number(event.target.value))}>
            {targetOptions.map((option) => (
              <option key={option.tokenId} value={option.tokenId}>{visibleToken(option.tokenText)} · #{option.tokenId}</option>
            ))}
          </select>
        </label>
        <div className={`chat-patching-alignment ${preflight?.canSubmit ? "ready" : "blocked"}`} aria-live="polite">
          <strong>{preflight?.canSubmit ? "Aligned" : preflight ? "Needs alignment" : "Checking"}</strong>
          <span>{preflight ? `${preflight.cleanTokenCount} clean · ${preflight.corruptedTokenCount} corrupt · ${preflight.changedPositions.length} changed` : "Tokenizing both inputs"}</span>
        </div>
      </div>

      {preflight?.corruptedTokens.length ? (
        <div className="chat-patching-positions">
          <header>
            <span>Patch positions</span>
            <small>{positions.length}/8 selected</small>
          </header>
          <div role="group" aria-label="Patching token positions">
            {preflight.corruptedTokens.map((token) => (
              <button
                type="button"
                key={token.index}
                className={`${token.changed ? "changed" : ""} ${positions.includes(token.index) ? "active" : ""}`}
                aria-label={`Patch token ${token.index}: ${visibleToken(run.tokens[token.index]?.text ?? "")} to ${visibleToken(token.text)}`}
                aria-pressed={positions.includes(token.index)}
                disabled={running || !preflight.tokenCountMatches || (!positions.includes(token.index) && positions.length >= 8)}
                onClick={() => togglePosition(token.index)}
              >
                <small>T{token.index}</small>
                <span>{visibleToken(run.tokens[token.index]?.text ?? "")}</span>
                <ArrowRight size={12} />
                <b>{visibleToken(token.text)}</b>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div className="chat-patching-layers">
        <header>
          <span>Layers</span>
          <small>{component === "z" ? `H${head} · one layer` : `${layers.length}/8 selected`} · {patchCount} patches</small>
        </header>
        <div role="group" aria-label="Patching layers">
          {run.layers.map((layer) => (
            <button
              type="button"
              key={layer}
              className={layers.includes(layer) ? "active" : ""}
              aria-pressed={layers.includes(layer)}
              disabled={running || (component !== "z" && !layers.includes(layer) && layers.length >= 8)}
              onClick={() => toggleLayer(layer)}
            >L{layer}</button>
          ))}
        </div>
      </div>

      <WorkbenchActions
        running={running}
        disabled={!canRun}
        runLabel={`Run ${patchCount || ""} patch${patchCount === 1 ? "" : "es"}`.replace("  ", " ")}
        status={runner.error?.message ?? preflightError ?? runner.job?.detail ?? preflight?.reason}
        progress={runner.job?.progress}
        onRun={submit}
        onCancel={() => void runner.cancel()}
        onReset={runner.reset}
        failed={Boolean(runner.error)}
      />

      {result?.patching && <PatchingResult experiment={result.patching} />}
    </section>
  );
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
  const [component, setComponent] = useState<ActivationComponent>(prior?.component ?? "resid_post");
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
          <select aria-label="Steering activation site" value={component} disabled={running} onChange={(event) => setComponent(event.target.value as ActivationComponent)}>
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

function PatchingResult({ experiment }: { experiment: PatchingExperiment }) {
  const strongest = [...experiment.cells].sort((left, right) =>
    patchingCellStrength(right) - patchingCellStrength(left)
  )[0];
  const [selected, setSelected] = useState<PatchingCell | undefined>(strongest);
  const maximum = Math.max(1e-8, ...experiment.cells.map(patchingCellStrength));

  return (
    <section className="chat-patching-result" aria-label="Activation patching result">
      <header>
        <div><GitCompareArrows size={16} /><strong>Causal recovery</strong></div>
        <span>{experiment.component === "z" ? `L${experiment.layers[0]}H${experiment.head} · ` : ""}Target {visibleToken(experiment.targetTokenText)} · #{experiment.targetTokenId}</span>
      </header>
      <div className="chat-patching-baselines">
        <span className="clean"><small>Clean logit</small><b>{experiment.cleanScore.toFixed(3)}</b></span>
        <span className="corrupt"><small>Corrupt logit</small><b>{experiment.corruptedScore.toFixed(3)}</b></span>
        <span><small>Clean-corrupt gap</small><b>{signed(experiment.denominator)}</b></span>
      </div>
      <div className="chat-patching-matrix" role="region" aria-label="Patching recovery matrix">
        <table>
          <thead>
            <tr>
              <th>Layer</th>
              {experiment.positions.map((position) => (
                <th key={position} title={experiment.corruptedTokens[position]?.text}>T{position}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {experiment.layers.map((layer) => (
              <tr key={layer}>
                <th>L{layer}</th>
                {experiment.positions.map((position) => {
                  const cell = experiment.cells.find((item) => item.layer === layer && item.tokenIndex === position);
                  const value = cell ? cell.recoveryPercentage : null;
                  const intensity = cell ? patchingCellStrength(cell) / maximum : 0;
                  const active = selected?.layer === layer && selected?.tokenIndex === position;
                  return (
                    <td key={position}>
                      {cell ? (
                        <button
                          type="button"
                          className={`${(value ?? cell.causalEffect) < 0 ? "negative" : "positive"} ${active ? "active" : ""}`}
                          style={{ "--strength": intensity } as React.CSSProperties}
                          aria-label={`Layer ${layer}, token ${position}, ${value === null ? `${signed(cell.causalEffect)} causal effect` : `${value.toFixed(1)} percent recovery`}`}
                          aria-pressed={active}
                          onClick={() => setSelected(cell)}
                        >{value === null ? signed(cell.causalEffect) : `${value.toFixed(1)}%`}</button>
                      ) : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected && (
        <footer aria-label="Selected patch result">
          <strong>L{selected.layer}{experiment.component === "z" ? `H${experiment.head}` : ""} · T{selected.tokenIndex}</strong>
          <span>Patched logit <b>{selected.patchedScore.toFixed(3)}</b></span>
          <span>Causal effect <b>{signed(selected.causalEffect)}</b></span>
          <span>Recovery <b>{selected.recoveryPercentage === null ? "n/a" : `${selected.recoveryPercentage.toFixed(1)}%`}</b></span>
        </footer>
      )}
    </section>
  );
}

function defaultLayer(run: ExplorerRun) {
  return run.layers[Math.max(0, Math.floor(run.layers.length * 0.7) - 1)] ?? run.layers[0] ?? 0;
}

function defaultPatchingLayers(layers: number[]) {
  if (layers.length <= 3) return layers;
  return [...new Set([0.25, 0.5, 0.75].map((fraction) =>
    layers[Math.min(layers.length - 1, Math.floor(layers.length * fraction))]
  ))];
}

function patchingComponentLabel(component: PatchingComponent) {
  if (component === "resid_post") return "Residual";
  if (component === "attn_out") return "Attention output";
  if (component === "z") return "Attention head";
  return "MLP";
}

function attentionHeadCount(run: ExplorerRun, layer: number) {
  const coverage = run.metadata?.attentionHeadCoverage;
  if (coverage && typeof coverage === "object" && !Array.isArray(coverage)) {
    const byLayer = (coverage as Record<string, unknown>).availableByLayer;
    if (byLayer && typeof byLayer === "object" && !Array.isArray(byLayer)) {
      const count = Number((byLayer as Record<string, unknown>)[String(layer)]);
      if (Number.isInteger(count) && count > 0) return count;
    }
  }
  const heads = run.attentionHeads
    .filter((item) => item.layer === layer && !item.aggregation && !item.difference && !item.rollout)
    .map((item) => item.head);
  return heads.length > 0 ? Math.max(...heads) + 1 : 1;
}

function patchingCellStrength(cell: PatchingCell) {
  return Math.abs(cell.recoveryPercentage ?? cell.causalEffect);
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
