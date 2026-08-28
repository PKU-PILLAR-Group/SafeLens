import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Activity,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  GitCompareArrows,
  LoaderCircle,
  Plus,
  RotateCcw,
  ScanSearch,
  Send,
  SlidersHorizontal,
  Square,
  Trash2
} from "lucide-react";

import {
  fetchInterventionPreflight,
  fetchPatchingPreflight,
  fetchSAEFeatureInfo,
  fetchSAEProfiles,
  type ActivationComponent,
  type AttributionJob,
  type AttributionRunInput,
  type InterventionJob,
  type InterventionPreflight,
  type InterventionRunInput,
  type JLensJob,
  type NLAJob,
  type PatchingComponent,
  type PatchingJob,
  type PatchingPreflight,
  type RemoteRunSummary,
  type SAEFeatureCandidate,
  type SAEFeatureInfo,
  type SAEProfile
} from "../api/explorerClient";
import { useAttributionRunner } from "../state/useAttributionRunner";
import { useInterventionRunner } from "../state/useInterventionRunner";
import { usePatchingRunner } from "../state/usePatchingRunner";
import { useSAEFeatureDiscovery } from "../state/useSAEFeatureDiscovery";
import { HYBRID_STEERING_BATCHES } from "../state/steeringHybridPresets";
import { pairedSteeringPreset, type SteeringPreset } from "../state/steeringPresets";
import type {
  AttributionMethod,
  ExplorerRun,
  InterventionExperiment,
  PatchingCell,
  PatchingExperiment
} from "../types";
import { generatedResponseText } from "../generatedResponse";
import { ChatAttentionWorkbench } from "./ChatAttentionWorkbench";
import { ChatExplanationWorkbench } from "./ChatExplanationWorkbench";
import { PresetSuggestTextarea } from "./PresetSuggestTextarea";
import { ResponseTokenPicker } from "./ResponseTokenPicker";

interface ChatAnalysisWorkbenchProps {
  mode: "steering" | "attribution" | "patching" | "neuron" | "feature" | "explanation" | "attention";
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
  if (mode === "neuron") {
    return <NeuronInterventionWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  if (mode === "feature") {
    return <FeatureInterventionWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  if (mode === "explanation") {
    return <ChatExplanationWorkbench run={run} savedRun={savedRun} onRunReady={onRunReady} />;
  }
  return <ChatAttentionWorkbench run={run} remoteSummary={remoteSummary} />;
}

function NeuronInterventionWorkbench({
  run,
  savedRun,
  onRunReady
}: Omit<ChatAnalysisWorkbenchProps, "mode">) {
  const prior = savedRun?.intervention?.mode === "neuron" ? savedRun.intervention : undefined;
  const featureLayers = useMemo(
    () => [...new Set(run.mlpNeurons.map((item) => item.layer))].sort((a, b) => a - b),
    [run.mlpNeurons]
  );
  const [layer, setLayer] = useState(
    prior?.feature?.layer ?? featureLayers[featureLayers.length - 1] ?? run.layers[run.layers.length - 1] ?? 0
  );
  const neurons = useMemo(
    () => run.mlpNeurons
      .filter((item) => item.layer === layer)
      .sort((a, b) => b.maxAbsoluteActivation - a.maxAbsoluteActivation),
    [layer, run.mlpNeurons]
  );
  const [neuron, setNeuron] = useState(prior?.feature?.neuron ?? neurons[0]?.neuron ?? 0);
  const [scale, setScale] = useState(prior?.scale ?? 0);
  const [positionStart, setPositionStart] = useState(prior?.positionStart ?? 0);
  const [positionEnd, setPositionEnd] = useState(prior?.positionEnd ?? run.tokens.length);
  const targetOptions = useMemo(() => steeringTargetOptions(run), [run]);
  const [targetTokenId, setTargetTokenId] = useState(
    prior?.targetTokenId ?? targetOptions[0]?.tokenId ?? 0
  );
  const [preflight, setPreflight] = useState<InterventionPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [result, setResult] = useState<ExplorerRun | null>(
    savedRun?.intervention?.mode === "neuron" ? savedRun : null
  );
  const handleReady = useCallback((derived: ExplorerRun, job: InterventionJob) => {
    setResult(derived);
    onRunReady(derived, job);
  }, [onRunReady]);
  const runner = useInterventionRunner(handleReady);
  const running = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const selectedNeuron = neurons.find((item) => item.neuron === neuron) ?? neurons[0];

  useEffect(() => {
    if (!neurons.some((item) => item.neuron === neuron)) setNeuron(neurons[0]?.neuron ?? 0);
  }, [neuron, neurons]);

  useEffect(() => {
    if (!featureLayers.includes(layer) && featureLayers.length) {
      setLayer(featureLayers[featureLayers.length - 1]);
    }
  }, [featureLayers, layer]);

  useEffect(() => {
    const controller = new AbortController();
    setPreflight(null);
    setPreflightError(null);
    const timer = window.setTimeout(() => {
      void fetchInterventionPreflight({
        mode: "neuron",
        modelName: run.modelName,
        promptTokenCount: run.tokens.length,
        availableLayers: run.layers,
        layer,
        component: "mlp_out",
        positionStart,
        positionEnd,
        targetTokenId,
        neuron,
        availableNeurons: neurons.map((item) => item.neuron),
        desiredPrompt: "Enhance selected MLP neuron",
        undesiredPrompt: "Suppress selected MLP neuron"
      }, controller.signal).then(setPreflight).catch((error) => {
        if (!controller.signal.aborted) {
          setPreflightError(error instanceof Error ? error.message : "Neuron preflight failed.");
        }
      });
    }, 180);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [layer, neuron, neurons, positionEnd, positionStart, run.layers, run.modelName, run.tokens.length, targetTokenId]);

  function setRange(start: number, end: number) {
    const nextStart = Math.max(0, Math.min(run.tokens.length - 1, start));
    setPositionStart(nextStart);
    setPositionEnd(Math.max(nextStart + 1, Math.min(run.tokens.length, end)));
  }

  function submit() {
    if (!preflight?.canSubmit || running || !selectedNeuron) return;
    setResult(null);
    const input: InterventionRunInput = {
      run,
      mode: "neuron",
      desiredPrompt: "Enhance selected MLP neuron",
      undesiredPrompt: "Suppress selected MLP neuron",
      layer,
      component: "mlp_out",
      neuron,
      scale,
      positionStart,
      positionEnd,
      targetTokenId,
      seed: 0,
      maxNewTokens: 16,
      temperature: 0
    };
    void runner.submit(input);
  }

  if (featureLayers.length === 0) {
    return (
      <section className="chat-analysis-workbench chat-feature-workbench" aria-label="MLP neuron intervention workbench">
        <header className="chat-workbench-heading">
          <span><Activity size={17} /></span>
          <div><h2>Neuron intervention</h2><p>This run does not expose MLP neuron activations.</p></div>
        </header>
      </section>
    );
  }

  return (
    <section className="chat-analysis-workbench chat-feature-workbench" aria-label="MLP neuron intervention workbench">
      <header className="chat-workbench-heading">
        <span><Activity size={17} /></span>
        <div><h2>Neuron intervention</h2><p>Scale one real MLP post-activation and compare the model output</p></div>
        <StatusDot ready={Boolean(preflight?.canSubmit)} pending={!preflight && !preflightError} />
      </header>
      <div className="chat-feature-controls">
        <label><span>Layer</span><select aria-label="Neuron intervention layer" value={layer} disabled={running} onChange={(event) => setLayer(Number(event.target.value))}>{featureLayers.map((item) => <option key={item} value={item}>L{item}</option>)}</select></label>
        <label><span>MLP neuron</span><select aria-label="MLP neuron" value={neuron} disabled={running} onChange={(event) => setNeuron(Number(event.target.value))}>{neurons.map((item) => <option key={item.neuron} value={item.neuron}>N{item.neuron} · {item.label}</option>)}</select></label>
        <label><span>Tracked output token</span><select aria-label="Neuron tracked output token" value={targetTokenId} disabled={running} onChange={(event) => setTargetTokenId(Number(event.target.value))}>{targetOptions.map((option) => <option key={option.tokenId} value={option.tokenId}>{visibleToken(option.tokenText)} · #{option.tokenId}</option>)}</select></label>
        <label className="chat-feature-strength"><span>Activation factor <b>{scale.toFixed(1)}</b></span><input aria-label="Neuron activation factor" type="range" min={-2} max={4} step={0.1} value={scale} disabled={running} onChange={(event) => setScale(Number(event.target.value))} /></label>
      </div>
      <div className="chat-feature-operations" role="group" aria-label="Neuron intervention operation">
        {[{ label: "Suppress", value: 0 }, { label: "Reduce", value: 0.25 }, { label: "Enhance", value: 2 }, { label: "Invert", value: -1 }].map((item) => <button key={item.label} type="button" className={Math.abs(scale - item.value) < 1e-6 ? "active" : ""} aria-pressed={Math.abs(scale - item.value) < 1e-6} disabled={running} onClick={() => setScale(item.value)}>{item.label}</button>)}
      </div>
      <div className="chat-token-range"><header><span>Apply to</span><div><button className={positionStart === 0 && positionEnd === run.tokens.length ? "active" : ""} aria-pressed={positionStart === 0 && positionEnd === run.tokens.length} disabled={running} onClick={() => setRange(0, run.tokens.length)}>Entire input</button><button className={positionStart === run.tokens.length - 1 && positionEnd === run.tokens.length ? "active" : ""} aria-pressed={positionStart === run.tokens.length - 1 && positionEnd === run.tokens.length} disabled={running} onClick={() => setRange(run.tokens.length - 1, run.tokens.length)}>Last token</button></div><small>T{positionStart}–T{positionEnd - 1}</small></header><div aria-label="Neuron intervention token range">{run.tokens.map((token) => <button key={token.index} className={token.index >= positionStart && token.index < positionEnd ? "active" : ""} aria-pressed={token.index >= positionStart && token.index < positionEnd} disabled={running} onClick={() => setRange(token.index, token.index + 1)}>{visibleToken(token.text)}</button>)}</div></div>
      <div className="chat-feature-selected"><strong>{selectedNeuron?.id}</strong><span>{selectedNeuron?.label}</span><small>peak activation {selectedNeuron?.maxAbsoluteActivation.toFixed(4)} · factor {scale.toFixed(1)}</small></div>
      <WorkbenchActions running={running} disabled={!preflight?.canSubmit || !selectedNeuron} runLabel="Run neuron intervention" status={runner.error?.message ?? preflightError ?? preflight?.reason} progress={runner.job?.progress} onRun={submit} onCancel={() => void runner.cancel()} onReset={runner.reset} failed={Boolean(runner.error)} />
      {result?.intervention && <SteeringResult experiment={result.intervention} />}
    </section>
  );
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

function FeatureInterventionWorkbench({
  run,
  savedRun,
  onRunReady
}: Omit<ChatAnalysisWorkbenchProps, "mode">) {
  const prior = savedRun?.intervention?.mode === "sae_feature"
    ? savedRun.intervention
    : run.intervention?.mode === "sae_feature"
      ? run.intervention
      : undefined;
  const [profiles, setProfiles] = useState<SAEProfile[]>([]);
  const [profilesReady, setProfilesReady] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileId, setProfileId] = useState("");
  const [featureIndex, setFeatureIndex] = useState(prior?.feature?.featureIndex ?? 0);
  const [operation, setOperation] = useState<"add" | "ablate">(
    prior?.feature?.operation === "ablate" ? "ablate" : "add"
  );
  const outputBoundary = Math.max(0, run.tokens.length - 1);
  const discoveryRange = useMemo(() => saeUserTokenRange(run), [run]);
  const [scale, setScale] = useState(prior?.scale ?? 100);
  const [positionStart, setPositionStart] = useState(prior?.positionStart ?? outputBoundary);
  const [positionEnd, setPositionEnd] = useState(prior?.positionEnd ?? run.tokens.length);
  const [outputTokens, setOutputTokens] = useState(prior?.maxNewTokens ?? 64);
  const targetOptions = useMemo(() => steeringTargetOptions(run), [run]);
  const [targetTokenId, setTargetTokenId] = useState(prior?.targetTokenId ?? targetOptions[0]?.tokenId ?? 0);
  const [preflight, setPreflight] = useState<InterventionPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [featureInfo, setFeatureInfo] = useState<SAEFeatureInfo | null>(null);
  const [candidates, setCandidates] = useState<SAEFeatureCandidate[]>([]);
  const [result, setResult] = useState<ExplorerRun | null>(
    savedRun?.intervention?.mode === "sae_feature" ? savedRun : null
  );
  const handleReady = useCallback((derived: ExplorerRun, job: InterventionJob) => {
    setResult(derived);
    onRunReady(derived, job);
  }, [onRunReady]);
  const runner = useInterventionRunner(handleReady);
  const handleDiscoveryReady = useCallback((discoveryResult: { candidates: SAEFeatureCandidate[] }) => {
    setCandidates(discoveryResult.candidates);
  }, []);
  const discovery = useSAEFeatureDiscovery(handleDiscoveryReady);
  const running = runner.submitting || runner.job?.status === "idle" || runner.job?.status === "loading";
  const discoveryRunning = discovery.running;
  const selectedProfile = profiles.find((profile) => profile.id === profileId)
    ?? profiles.find((profile) => profile.layer === 12)
    ?? profiles[0];
  const selectedCandidate = candidates.find((candidate) => candidate.featureIndex === featureIndex);
  const scaleLimit = Math.min(
    1_000,
    Math.max(100, Math.ceil(Math.max(Math.abs(scale), selectedCandidate?.recommendedDelta ?? 0) * 1.5 / 50) * 50)
  );

  useEffect(() => {
    const controller = new AbortController();
    setProfiles([]);
    setProfilesReady(false);
    setProfileError(null);
    void fetchSAEProfiles(run.modelName, controller.signal).then((next) => {
      setProfiles(next);
      const priorProfile = next.find((profile) => profile.saeId === prior?.feature?.saeId);
      const defaultProfile = priorProfile ?? next.find((profile) => profile.layer === 12) ?? next[0];
      setProfileId(defaultProfile?.id ?? "");
      setCandidates([]);
      setProfilesReady(true);
    }).catch((error) => {
      if (!controller.signal.aborted) {
        setProfileError(error instanceof Error ? error.message : "SAE profiles failed to load.");
        setProfilesReady(true);
      }
    });
    return () => controller.abort();
  }, [prior?.feature?.saeId, run.modelName]);

  useEffect(() => {
    if (selectedProfile && featureIndex >= selectedProfile.width) setFeatureIndex(0);
  }, [featureIndex, selectedProfile]);

  useEffect(() => {
    if (!selectedProfile) {
      setPreflight(null);
      setFeatureInfo(null);
      return;
    }
    const controller = new AbortController();
    setPreflight(null);
    setPreflightError(null);
    const timer = window.setTimeout(() => {
      void fetchInterventionPreflight({
        mode: "sae_feature",
        modelName: run.modelName,
        promptTokenCount: run.tokens.length,
        availableLayers: run.layers,
        layer: selectedProfile.layer,
        component: selectedProfile.component,
        positionStart,
        positionEnd,
        targetTokenId,
        saeRelease: selectedProfile.release,
        saeId: selectedProfile.saeId,
        featureIndex,
        saeOperation: operation,
        desiredPrompt: "Enhance selected SAE feature",
        undesiredPrompt: "Suppress selected SAE feature"
      }, controller.signal).then(setPreflight).catch((error) => {
        if (!controller.signal.aborted) setPreflightError(error instanceof Error ? error.message : "SAE preflight failed.");
      });
    }, 180);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [featureIndex, operation, positionEnd, positionStart, run.layers, run.modelName, run.tokens.length, selectedProfile, targetTokenId]);

  useEffect(() => {
    if (!selectedProfile) {
      setFeatureInfo(null);
      return;
    }
    const controller = new AbortController();
    setFeatureInfo(null);
    const timer = window.setTimeout(() => {
      void fetchSAEFeatureInfo(
        run.modelName,
        selectedProfile.layer,
        featureIndex,
        controller.signal
      ).then(setFeatureInfo).catch(() => {
        if (!controller.signal.aborted) setFeatureInfo(null);
      });
    }, 180);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [featureIndex, run.modelName, selectedProfile]);

  function setRange(start: number, end: number) {
    const nextStart = Math.max(0, Math.min(run.tokens.length - 1, start));
    setPositionStart(nextStart);
    setPositionEnd(Math.max(nextStart + 1, Math.min(run.tokens.length, end)));
  }

  function selectProfile(nextProfileId: string) {
    setProfileId(nextProfileId);
    setCandidates([]);
    discovery.reset();
    setResult(null);
  }

  function discoverFeatures() {
    if (!selectedProfile || discoveryRunning) return;
    setCandidates([]);
    void discovery.submit({
      run,
      layer: selectedProfile.layer,
      component: selectedProfile.component,
      saeRelease: selectedProfile.release,
      saeId: selectedProfile.saeId,
      positionStart: discoveryRange.start,
      positionEnd: discoveryRange.end,
      limit: 12
    });
  }

  function selectCandidate(candidate: SAEFeatureCandidate) {
    setFeatureIndex(candidate.featureIndex);
    setFeatureInfo({
      modelName: run.modelName,
      layer: selectedProfile?.layer ?? 0,
      featureIndex: candidate.featureIndex,
      label: candidate.label,
      source: candidate.source,
      url: candidate.url,
      positiveTokens: candidate.positiveTokens,
      negativeTokens: candidate.negativeTokens
    });
    setOperation("add");
    setScale(candidate.recommendedDelta);
    setRange(outputBoundary, run.tokens.length);
    setResult(null);
  }

  function applySuggestedScale(multiplier: number) {
    const basis = selectedCandidate?.recommendedDelta ?? 100;
    setScale(Math.max(-1_000, Math.min(1_000, Math.round(basis * multiplier))));
  }

  function selectOperation(nextOperation: "add" | "ablate") {
    setOperation(nextOperation);
    if (nextOperation === "add") {
      setRange(outputBoundary, run.tokens.length);
    } else if (selectedCandidate) {
      setRange(selectedCandidate.peakTokenIndex, selectedCandidate.peakTokenIndex + 1);
    } else {
      setRange(0, run.tokens.length);
    }
    setResult(null);
  }

  function submit() {
    if (!preflight?.canSubmit || running || !selectedProfile) return;
    setResult(null);
    const input: InterventionRunInput = {
      run,
      mode: "sae_feature",
      desiredPrompt: "Enhance selected SAE feature",
      undesiredPrompt: "Suppress selected SAE feature",
      layer: selectedProfile.layer,
      component: selectedProfile.component,
      saeRelease: selectedProfile.release,
      saeId: selectedProfile.saeId,
      featureIndex,
      saeOperation: operation,
      scale,
      positionStart,
      positionEnd,
      targetTokenId,
      seed: 0,
      maxNewTokens: outputTokens,
      temperature: 0
    };
    void runner.submit(input);
  }

  if (profilesReady && profiles.length === 0) {
    return (
      <section className="chat-analysis-workbench chat-feature-workbench" aria-label="SAE feature intervention workbench">
        <header className="chat-workbench-heading">
          <span><Activity size={17} /></span>
          <div><h2>Gemma Scope SAE</h2><p>No compatible SAE for {run.modelName}</p></div>
        </header>
        <p className="chat-sae-empty">Select <b>google/gemma-3-270m-it</b> for a new chat run.</p>
      </section>
    );
  }
  return (
    <section className="chat-analysis-workbench chat-feature-workbench" aria-label="SAE feature intervention workbench">
      <header className="chat-workbench-heading">
        <span><Activity size={17} /></span>
        <div><h2>Gemma Scope SAE</h2><p>Sparse feature intervention · residual stream</p></div>
        <StatusDot ready={Boolean(preflight?.canSubmit)} pending={discoveryRunning || (!preflight && !preflightError)} />
      </header>
      <section className="chat-sae-discovery" aria-label="Active SAE features">
        <header>
          <div>
            <strong>Active features in this prompt</strong>
            <small>L{selectedProfile?.layer ?? "..."} · user tokens T{discoveryRange.start}–T{discoveryRange.end - 1}</small>
          </div>
          <button
            type="button"
            className={discoveryRunning ? "pending" : ""}
            disabled={!selectedProfile || running}
            onClick={discoveryRunning ? () => void discovery.cancel() : discoverFeatures}
          >
            {discoveryRunning ? <Square size={14} /> : <ScanSearch size={15} />}
            {discoveryRunning ? "Cancel scan" : candidates.length > 0 ? "Scan again" : "Find active features"}
          </button>
        </header>
        {discoveryRunning && (
          <div className="chat-sae-discovery-progress">
            <span><i style={{ width: `${discovery.job?.progress ?? 4}%` }} /></span>
            <small>{discovery.job?.detail ?? "Loading the model and SAE checkpoint..."}</small>
          </div>
        )}
        {discovery.error && <p className="chat-sae-discovery-error"><AlertCircle size={14} />{discovery.error.message}</p>}
        {candidates.length > 0 && (
          <div className="chat-sae-candidates" role="radiogroup" aria-label="SAE feature candidates">
            {candidates.map((candidate) => (
              <button
                type="button"
                role="radio"
                aria-checked={selectedCandidate?.featureIndex === candidate.featureIndex}
                className={selectedCandidate?.featureIndex === candidate.featureIndex ? "active" : ""}
                key={candidate.featureIndex}
                disabled={running}
                onClick={() => selectCandidate(candidate)}
              >
                <span><b>F{candidate.featureIndex}</b><em>peak {formatActivation(candidate.maxActivation)}</em></span>
                <strong>{candidate.label}</strong>
                <small>T{candidate.peakTokenIndex} · {visibleToken(candidate.peakTokenText)} · active on {candidate.activeTokenCount} token{candidate.activeTokenCount === 1 ? "" : "s"}</small>
                <i>Suggested {signed(candidate.recommendedDelta)}</i>
              </button>
            ))}
          </div>
        )}
      </section>
      <div className="chat-feature-controls">
        <label className="chat-sae-profile"><span>SAE checkpoint</span><select aria-label="SAE checkpoint" value={selectedProfile?.id ?? ""} disabled={running || discoveryRunning || profiles.length === 0} onChange={(event) => selectProfile(event.target.value)}>{profiles.map((profile) => <option key={profile.id} value={profile.id}>L{profile.layer} · 16k · L0 small</option>)}</select></label>
        <label><span>Feature</span><input aria-label="SAE feature index" type="number" min={0} max={(selectedProfile?.width ?? 1) - 1} value={featureIndex} disabled={running || discoveryRunning || !selectedProfile} onChange={(event) => setFeatureIndex(Math.max(0, Math.min((selectedProfile?.width ?? 1) - 1, Number(event.target.value) || 0)))} /></label>
        <label><span>Tracked output token</span><select aria-label="SAE tracked output token" value={targetTokenId} disabled={running} onChange={(event) => setTargetTokenId(Number(event.target.value))}>{targetOptions.map((option) => <option key={option.tokenId} value={option.tokenId}>{visibleToken(option.tokenText)} · #{option.tokenId}</option>)}</select></label>
        <label><span>Output tokens</span><input aria-label="SAE output tokens" type="number" min={1} max={128} value={outputTokens} disabled={running} onChange={(event) => setOutputTokens(Math.max(1, Math.min(128, Number(event.target.value) || 1)))} /></label>
      </div>
      <div className="chat-feature-adjustment">
        <div className="chat-feature-operations" role="group" aria-label="SAE feature operation">
          <button type="button" className={operation === "add" ? "active" : ""} aria-pressed={operation === "add"} disabled={running} onClick={() => selectOperation("add")}>Add activation</button>
          <button type="button" className={operation === "ablate" ? "active" : ""} aria-pressed={operation === "ablate"} disabled={running} onClick={() => selectOperation("ablate")}>Ablate feature</button>
        </div>
        <label className="chat-feature-strength">
          <span>Feature delta <b>{operation === "ablate" ? "zero" : signed(scale)}</b></span>
          <input aria-label="SAE feature delta" type="range" min={-scaleLimit} max={scaleLimit} step={5} value={scale} disabled={running || operation === "ablate"} onChange={(event) => setScale(Number(event.target.value))} />
        </label>
        <input className="chat-feature-strength-number" aria-label="SAE feature delta value" type="number" min={-1000} max={1000} step={5} value={scale} disabled={running || operation === "ablate"} onChange={(event) => setScale(Math.max(-1000, Math.min(1000, Number(event.target.value) || 0)))} />
        <div className="chat-feature-strength-presets" role="group" aria-label="SAE strength presets">
          <button type="button" disabled={running || operation === "ablate"} onClick={() => applySuggestedScale(0.5)}>Subtle</button>
          <button type="button" disabled={running || operation === "ablate"} onClick={() => applySuggestedScale(1)}>Suggested</button>
          <button type="button" disabled={running || operation === "ablate"} onClick={() => applySuggestedScale(1.5)}>Strong</button>
        </div>
      </div>
      <div className="chat-token-range"><header><span>Apply to</span><div><button className={positionStart === outputBoundary && positionEnd === run.tokens.length ? "active" : ""} aria-pressed={positionStart === outputBoundary && positionEnd === run.tokens.length} disabled={running} onClick={() => setRange(outputBoundary, run.tokens.length)}>Output boundary</button><button className={positionStart === 0 && positionEnd === run.tokens.length ? "active" : ""} aria-pressed={positionStart === 0 && positionEnd === run.tokens.length} disabled={running} onClick={() => setRange(0, run.tokens.length)}>Entire input</button></div><small>T{positionStart}–T{positionEnd - 1}</small></header><div aria-label="SAE intervention token range">{run.tokens.map((token) => <button key={token.index} className={token.index >= positionStart && token.index < positionEnd ? "active" : ""} aria-pressed={token.index >= positionStart && token.index < positionEnd} disabled={running} onClick={() => setRange(token.index, token.index + 1)}>{visibleToken(token.text)}</button>)}</div></div>
      <div className="chat-feature-selected">
        <div className="chat-feature-selected-id"><strong>F{featureIndex}</strong><span>L{selectedProfile?.layer ?? "..."} · resid_post</span><small>{selectedProfile?.saeId ?? "Loading checkpoint"}</small></div>
        <div className="chat-feature-concept">
          <span>Concept label</span>
          <strong>{featureInfo?.label ?? prior?.feature?.conceptLabel ?? "Loading explanation..."}</strong>
          <small>
            {featureInfo?.source === "neuronpedia" || prior?.feature?.conceptSource === "neuronpedia"
              ? "Neuronpedia explanation"
              : "No canonical label is bundled with the SAE checkpoint"}
            {(featureInfo?.url ?? prior?.feature?.conceptUrl) && (
              <> · <a href={featureCardUrl(featureInfo?.url ?? prior?.feature?.conceptUrl)} target="_blank" rel="noreferrer">Open feature card</a></>
            )}
          </small>
          {(featureInfo?.positiveTokens.length ?? 0) > 0 && <small className="chat-feature-evidence"><b>Positive</b>{featureInfo?.positiveTokens.slice(0, 6).join(" · ")}</small>}
          {(featureInfo?.negativeTokens.length ?? 0) > 0 && <small className="chat-feature-evidence"><b>Negative</b>{featureInfo?.negativeTokens.slice(0, 6).join(" · ")}</small>}
        </div>
      </div>
      <WorkbenchActions running={running} disabled={!preflight?.canSubmit || !selectedProfile} runLabel="Run SAE intervention" status={runner.error?.message ?? profileError ?? preflightError ?? preflight?.reason} progress={runner.job?.progress} onRun={submit} onCancel={() => void runner.cancel()} onReset={runner.reset} failed={Boolean(runner.error)} />
      {result?.intervention && <SteeringResult experiment={result.intervention} />}
    </section>
  );
}

type SteeringConcept = "Custom" | "Reject" | "Angry" | "Happy" | "Emoji" | "Dog" | "Music";
type SteeringSampleDirection = "positive" | "negative";

const STEERING_CONCEPTS: SteeringConcept[] = ["Custom", "Reject", "Angry", "Happy", "Emoji", "Dog", "Music"];
const STEERING_BATCHES = HYBRID_STEERING_BATCHES;

function SteeringWorkbench({
  run,
  savedRun,
  suggestionQuery,
  onRunReady
}: Omit<ChatAnalysisWorkbenchProps, "mode">) {
  const prior = savedRun?.intervention ?? run.intervention;
  const [expanded, setExpanded] = useState(false);
  const [concept, setConcept] = useState<SteeringConcept>("Custom");
  const [positivePreset, setPositivePreset] = useState("Custom samples");
  const [negativePreset, setNegativePreset] = useState("Custom samples");
  const [positivePrompts, setPositivePrompts] = useState<string[]>(
    prior?.vector.positivePrompts ?? [prior?.vector.desiredPrompt ?? "Provide a safe, policy-compliant and helpful response."]
  );
  const [negativePrompts, setNegativePrompts] = useState<string[]>(
    prior?.vector.negativePrompts ?? [prior?.vector.undesiredPrompt ?? "Provide a response that bypasses safety guidance."]
  );
  const [activationReduce, setActivationReduce] = useState<"last_token" | "mean">(
    prior?.vector.activationReduce === "mean" ? "mean" : "last_token"
  );
  const steeringDefaultLayer = defaultSteeringLayer(run);
  const [sourceLayer, setSourceLayer] = useState(prior?.sourceLayer ?? prior?.layer ?? steeringDefaultLayer);
  const [injectLayer, setInjectLayer] = useState(prior?.injectLayer ?? prior?.layer ?? steeringDefaultLayer);
  const [component, setComponent] = useState<ActivationComponent>(prior?.component ?? "resid_post");
  const [scale, setScale] = useState(prior?.scale ?? 1);
  const [outputTokens, setOutputTokens] = useState(128);
  const targetOptions = useMemo(() => steeringTargetOptions(run), [run]);
  const [targetTokenId, setTargetTokenId] = useState(prior?.targetTokenId ?? targetOptions[0]?.tokenId ?? 0);
  const [preflight, setPreflight] = useState<InterventionPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [result, setResult] = useState<ExplorerRun | null>(savedRun?.intervention ? savedRun : prior ? run : null);
  const positiveRequest = useMemo(() => positivePrompts.map((prompt) => prompt.trim()).filter(Boolean), [positivePrompts]);
  const negativeRequest = useMemo(() => negativePrompts.map((prompt) => prompt.trim()).filter(Boolean), [negativePrompts]);

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
    if (positiveRequest.length === 0 || negativeRequest.length === 0) {
      setPreflightError("Add at least one non-empty sample to each direction.");
      return () => controller.abort();
    }
    const timer = window.setTimeout(() => {
      void fetchInterventionPreflight({
        modelName: run.modelName,
        promptTokenCount: run.tokens.length,
        availableLayers: run.layers,
        layer: injectLayer,
        sourceLayer,
        injectLayer,
        component,
        positionStart: 0,
        positionEnd: run.tokens.length,
        targetTokenId,
        positivePrompts: positiveRequest,
        negativePrompts: negativeRequest,
        activationReduce
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
  }, [activationReduce, component, injectLayer, negativeRequest, positiveRequest, run.layers, run.modelName, run.tokens.length, sourceLayer, targetTokenId]);

  const canRun = Boolean(preflight?.canSubmit && !running);

  function selectConcept(next: SteeringConcept) {
    setConcept(next);
    if (next === "Custom") {
      setPositivePreset("Custom samples");
      setNegativePreset("Custom samples");
      return;
    }
    setPositivePrompts([...STEERING_BATCHES[next].positive]);
    setNegativePrompts([...STEERING_BATCHES[next].negative]);
    setPositivePreset(`${next} positive batch`);
    setNegativePreset(`${next} negative batch`);
  }

  function selectBatch(direction: SteeringSampleDirection, value: string) {
    if (direction === "positive") setPositivePreset(value);
    else setNegativePreset(value);
    if (value === "Custom samples") return;
    const batchConcept = STEERING_CONCEPTS.find((item) => value.startsWith(`${item} `));
    if (!batchConcept || batchConcept === "Custom") return;
    const prompts = [...STEERING_BATCHES[batchConcept][direction]];
    if (direction === "positive") setPositivePrompts(prompts);
    else setNegativePrompts(prompts);
  }

  function replacePrimarySample(direction: SteeringSampleDirection, text: string) {
    const update = (prompts: string[]) => prompts.length > 0
      ? [text, ...prompts.slice(1)]
      : [text];
    setConcept("Custom");
    if (direction === "positive") {
      setPositivePreset("Custom samples");
      setPositivePrompts(update);
    } else {
      setNegativePreset("Custom samples");
      setNegativePrompts(update);
    }
  }

  function applyPairedPreset(preset: SteeringPreset) {
    replacePrimarySample(preset.direction === "toward" ? "positive" : "negative", preset.text);
    const paired = pairedSteeringPreset(preset);
    if (paired) {
      replacePrimarySample(paired.direction === "toward" ? "positive" : "negative", paired.text);
    }
  }

  function submit() {
    if (!canRun) return;
    setResult(null);
    void runner.submit({
      run,
      desiredPrompt: positiveRequest[0],
      undesiredPrompt: negativeRequest[0],
      positivePrompts: positiveRequest,
      negativePrompts: negativeRequest,
      activationReduce,
      layer: injectLayer,
      sourceLayer,
      injectLayer,
      component,
      scale,
      positionStart: 0,
      positionEnd: run.tokens.length,
      targetTokenId,
      seed: 0,
      maxNewTokens: outputTokens,
      temperature: 0
    });
  }

  const conceptControl = (
    <label className="chat-steering-concept">
      <span>Steering concept</span>
      <select aria-label="Steering concept" value={concept} disabled={running} onChange={(event) => selectConcept(event.target.value as SteeringConcept)}>
        {STEERING_CONCEPTS.map((item) => <option key={item} value={item}>{item}</option>)}
      </select>
    </label>
  );
  const advancedToggle = (
    <button type="button" className="chat-steering-advanced-toggle" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>
      <SlidersHorizontal size={16} />
      {expanded ? "Hide advanced settings" : "Advanced settings"}
      {expanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
    </button>
  );

  return (
    <section className={`chat-analysis-workbench chat-steering-workbench ${expanded ? "is-expanded" : "is-compact"}`} aria-label="Steering workbench">
      {expanded ? (
        <>
          <div className="chat-steering-expanded-top">{conceptControl}{advancedToggle}</div>
          <div className="chat-steering-references">
            <SteeringSamples direction="positive" prompts={positivePrompts} preset={positivePreset} running={running} suggestionQuery={suggestionQuery} onPreset={selectBatch} onSelectPreset={applyPairedPreset} onChange={setPositivePrompts} />
            <SteeringSamples direction="negative" prompts={negativePrompts} preset={negativePreset} running={running} suggestionQuery={suggestionQuery} onPreset={selectBatch} onSelectPreset={applyPairedPreset} onChange={setNegativePrompts} />
          </div>
          <div className="chat-steering-controls">
            <label>
              <span>Sample activation</span>
              <select aria-label="Steering sample activation" value={activationReduce} disabled={running} onChange={(event) => setActivationReduce(event.target.value as "last_token" | "mean")}>
                <option value="last_token">Last token</option>
                <option value="mean">Token average</option>
              </select>
            </label>
            <label>
              <span>Source layer</span>
              <select aria-label="Steering source layer" value={sourceLayer} disabled={running} onChange={(event) => setSourceLayer(Number(event.target.value))}>
                {run.layers.map((item) => <option key={item} value={item}>L{item}</option>)}
              </select>
            </label>
            <label>
              <span>Inject layer</span>
              <select aria-label="Steering inject layer" value={injectLayer} disabled={running} onChange={(event) => setInjectLayer(Number(event.target.value))}>
                {run.layers.map((item) => <option key={item} value={item}>L{item}</option>)}
              </select>
            </label>
            <label>
              <span>Component</span>
              <select aria-label="Steering activation site" value={component} disabled={running} onChange={(event) => setComponent(event.target.value as ActivationComponent)}>
                <option value="resid_post">Residual stream</option>
                <option value="attn_out">Attention output</option>
                <option value="mlp_out">MLP output</option>
              </select>
            </label>
            <label>
              <span>Objective</span>
              <select aria-label="Steering diagnostic token" value={targetTokenId} disabled={running} onChange={(event) => setTargetTokenId(Number(event.target.value))}>
                {targetOptions.map((option) => <option key={option.tokenId} value={option.tokenId}>{visibleToken(option.tokenText)} · #{option.tokenId}</option>)}
              </select>
            </label>
            <label className="chat-steering-strength">
              <span>Strength <b>{scale.toFixed(1)}</b></span>
              <input aria-label="Steering strength" type="range" min={0} max={2.5} step={0.1} value={scale} disabled={running} onChange={(event) => setScale(Number(event.target.value))} />
            </label>
            <label>
              <span>Output tokens</span>
              <input aria-label="Steering output tokens" type="number" min={1} max={128} step={1} value={outputTokens} disabled={running} onChange={(event) => setOutputTokens(Math.max(1, Math.min(128, Number(event.target.value) || 1)))} />
            </label>
          </div>
        </>
      ) : (
        <div className="chat-steering-quick-controls">
          {conceptControl}
          <label className="chat-steering-strength">
            <span>Strength <b>{scale.toFixed(1)}</b></span>
            <input aria-label="Steering strength" type="range" min={0} max={2.5} step={0.1} value={scale} disabled={running} onChange={(event) => setScale(Number(event.target.value))} />
          </label>
          {advancedToggle}
        </div>
      )}
      <WorkbenchActions running={running} disabled={!canRun} runLabel="Run steering" status={runner.error?.message ?? preflightError ?? preflight?.reason} progress={runner.job?.progress} onRun={submit} onCancel={() => void runner.cancel()} onReset={runner.reset} failed={Boolean(runner.error)} />
      {result?.intervention && <SteeringResult experiment={result.intervention} />}
    </section>
  );
}

function SteeringSamples({
  direction,
  prompts,
  preset,
  running,
  suggestionQuery,
  onPreset,
  onSelectPreset,
  onChange
}: {
  direction: SteeringSampleDirection;
  prompts: string[];
  preset: string;
  running: boolean;
  suggestionQuery?: string;
  onPreset: (direction: SteeringSampleDirection, value: string) => void;
  onSelectPreset: (preset: SteeringPreset) => void;
  onChange: (prompts: string[]) => void;
}) {
  const title = direction === "positive" ? "Steer toward" : "Steer away from";
  const updatePrompt = (index: number, value: string) => onChange(prompts.map((prompt, item) => item === index ? value : prompt));
  const removePrompt = (index: number) => {
    if (prompts.length === 1) return;
    onChange(prompts.filter((_prompt, item) => item !== index));
  };
  return (
    <section className="chat-steering-samples">
      <header><strong>{title} samples</strong><span>{prompts.length}</span></header>
      <label className="chat-steering-preset">
        <span>Sample preset</span>
        <select aria-label={`${title} sample preset`} value={preset} disabled={running} onChange={(event) => onPreset(direction, event.target.value)}>
          <option value="Custom samples">Custom samples</option>
          {STEERING_CONCEPTS.filter((item) => item !== "Custom").map((item) => <option key={item} value={`${item} ${direction} batch`}>{item} {direction} batch</option>)}
        </select>
      </label>
      <div className="chat-steering-sample-list">
        <PresetSuggestTextarea
          ariaLabel={direction === "positive" ? "Steering desired behavior" : "Steering undesired behavior"}
          label={title}
          direction={direction === "positive" ? "toward" : "away"}
          contextQuery={suggestionQuery}
          value={prompts[0] ?? ""}
          disabled={running}
          onChange={(value) => updatePrompt(0, value)}
          onSelectPreset={onSelectPreset}
        />
        {prompts.slice(1).map((prompt, offset) => {
          const index = offset + 1;
          return (
          <label key={index}>
            <span>Sample {index + 1}</span>
            <div>
              <textarea aria-label={`${title} sample ${index + 1}`} value={prompt} disabled={running} onChange={(event) => updatePrompt(index, event.target.value)} />
              <button type="button" aria-label={`Remove ${title.toLowerCase()} sample ${index + 1}`} disabled={running || prompts.length === 1} onClick={() => removePrompt(index)}><Trash2 size={15} /></button>
            </div>
          </label>
          );
        })}
      </div>
      <button type="button" className="chat-steering-add-sample" disabled={running || prompts.length >= 64} onClick={() => onChange([...prompts, ""])}><Plus size={15} />Add sample</button>
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
          <p>Show which input tokens support or suppress the selected output token</p>
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
  const isFeature = experiment.mode === "neuron" || experiment.mode === "sae_feature";
  const isSAE = experiment.mode === "sae_feature";
  const isLegacyDirection = !isFeature && experiment.vector.normalized;
  const layerLabel = experiment.sourceLayer !== undefined || experiment.injectLayer !== undefined
    ? `source L${experiment.sourceLayer ?? experiment.layer} → inject L${experiment.injectLayer ?? experiment.layer}`
    : `L${experiment.layer}`;
  const maxLogitDelta = experiment.deltas.maxAbsLogit;
  const firstDivergence = experiment.deltas.firstDivergenceIndex;
  const relativeStrength = experiment.vector.relativeStrength;
  return (
    <section className="chat-steering-result" aria-label="Steering comparison">
      <header>
        <div>{isFeature ? <Activity size={16} /> : <GitCompareArrows size={16} />}<strong>{isSAE ? "SAE feature comparison" : isFeature ? "Neuron intervention comparison" : "Steering generation comparison"}</strong></div>
        <span>{isFeature && experiment.feature ? `${experiment.feature.id} · ${experiment.feature.operation}` : `${layerLabel} · ${experiment.component}`}{isSAE && experiment.feature?.operation === "ablate" ? "" : ` · factor ${signed(experiment.scale)}`}</span>
      </header>
      {isSAE && experiment.feature && (
        <div className="chat-sae-concept-result">
          <span>Concept label</span>
          <strong>{experiment.feature.conceptLabel ?? experiment.feature.label}</strong>
          <small>
            {experiment.feature.conceptSource === "neuronpedia"
              ? "External explanation metadata; the SAE weights only contain the numeric feature index."
              : "No canonical explanation was bundled; this is an index-only feature."}
            {experiment.feature.conceptUrl && (
              <> <a href={featureCardUrl(experiment.feature.conceptUrl)} target="_blank" rel="noreferrer">Open feature card</a></>
            )}
          </small>
          {((experiment.feature.positiveTokens?.length ?? 0) > 0 || (experiment.feature.negativeTokens?.length ?? 0) > 0) && (
            <div className="chat-sae-concept-evidence">
              {experiment.feature.positiveTokens?.length ? <span><b>Positive logits</b>{experiment.feature.positiveTokens.slice(0, 5).join(" · ")}</span> : null}
              {experiment.feature.negativeTokens?.length ? <span><b>Negative logits</b>{experiment.feature.negativeTokens.slice(0, 5).join(" · ")}</span> : null}
            </div>
          )}
        </div>
      )}
      <div className="chat-steering-output">
        <article className="is-original">
          <span>Original</span>
          <p>{experiment.original.text || "No continuation"}</p>
          <small>Diagnostic token logit {experiment.original.targetLogit.toFixed(3)}</small>
        </article>
        <div className="chat-steering-transition" title="Diagnostic token logit delta">
          <ArrowRight size={20} />
          <span>{signed(experiment.deltas.targetLogit)}</span>
        </div>
        <article className="is-steered">
          <span>Steered</span>
          <p>{experiment.steered.text || "No continuation"}</p>
          <small>Diagnostic token logit {experiment.steered.targetLogit.toFixed(3)}</small>
        </article>
      </div>
      <p className={`chat-steering-verdict ${experiment.deltas.generationChanged ? "changed" : "unchanged"}`}>
        {isLegacyDirection
          ? "This saved result used legacy unit-vector steering. Run steering again to use the calibrated contrastive algorithm."
          : experiment.deltas.generationChanged
          ? `Generation diverged at output token ${firstDivergence ?? 0}.`
          : maxLogitDelta && maxLogitDelta > 0
            ? "The intervention changed next-token logits, but not enough to change greedy decoding in this window. Increase strength or choose another layer."
            : "No measurable intervention effect was recorded. Check the selected layer and activation site."}
      </p>
      <footer>
        <span><b>{signed(experiment.deltas.targetLogit)}</b> diagnostic logit</span>
        <span><b>{experiment.deltas.tokenEditDistance}</b> token edits</span>
        {maxLogitDelta !== undefined && <span><b>{maxLogitDelta.toFixed(3)}</b> max vocabulary change</span>}
        {relativeStrength !== undefined && <span><b>{(relativeStrength * 100).toFixed(1)}%</b> relative injection</span>}
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
  const positive = run.tokens
    .map((token, index) => ({ token, value: values[index] ?? 0 }))
    .filter((item) => item.value > 0)
    .sort((left, right) => right.value - left.value)
    .slice(0, 5);
  const negative = run.tokens
    .map((token, index) => ({ token, value: values[index] ?? 0 }))
    .filter((item) => item.value < 0)
    .sort((left, right) => left.value - right.value)
    .slice(0, 5);
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
      <footer className="chat-attribution-rankings">
        <section aria-label="Positive attribution tokens"><header><i className="positive" /><strong>Supports target</strong></header>{positive.length ? positive.map(({ token, value }) => <span key={token.index}><small>T{token.index}</small><b>{visibleToken(token.text)}</b><em className="positive-value">{signed(value)}</em></span>) : <p>No positive token contribution.</p>}</section>
        <section aria-label="Negative attribution tokens"><header><i className="negative" /><strong>Suppresses target</strong></header>{negative.length ? negative.map(({ token, value }) => <span key={token.index}><small>T{token.index}</small><b>{visibleToken(token.text)}</b><em className="negative-value">{signed(value)}</em></span>) : <p>No negative token contribution.</p>}</section>
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

function defaultSteeringLayer(run: ExplorerRun) {
  const sourceGridLayer = Math.floor((2 * run.layers.length) / 4) + 1;
  return run.layers.includes(sourceGridLayer) ? sourceGridLayer : defaultLayer(run);
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
  return generatedResponseText(run);
}

function attributionTargetIndex(run: ExplorerRun) {
  const jobs = run.metadata?.attributionJobs;
  if (!Array.isArray(jobs)) return undefined;
  const latest = jobs[jobs.length - 1];
  if (!latest || typeof latest !== "object") return undefined;
  const value = (latest as Record<string, unknown>).targetResponseIndex;
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : undefined;
}

function saeUserTokenRange(run: ExplorerRun) {
  const tokens = run.tokens;
  if (tokens.length === 0) return { start: 0, end: 0 };
  let roleIndex = -1;
  for (let index = tokens.length - 1; index >= 0; index -= 1) {
    if (tokens[index].text.trim().toLowerCase() === "user") {
      roleIndex = index;
      break;
    }
  }
  if (roleIndex < 0) return { start: 0, end: tokens.length };
  let start = roleIndex + 1;
  while (start < tokens.length && tokens[start].text.trim() === "") start += 1;
  let end = tokens.length;
  for (let index = start; index < tokens.length; index += 1) {
    const text = tokens[index].text.trim().toLowerCase();
    if (text === "<end_of_turn>" || text === "<|im_end|>" || text === "assistant" || text === "model") {
      end = index;
      break;
    }
  }
  while (end > start && tokens[end - 1].text.trim() === "") end -= 1;
  return start < end ? { start, end } : { start: 0, end: tokens.length };
}

function visibleToken(value: string) {
  return value.trim() || "space";
}

function formatActivation(value: number) {
  if (Math.abs(value) >= 100) return value.toFixed(0);
  if (Math.abs(value) >= 10) return value.toFixed(1);
  return value.toFixed(2);
}

function featureCardUrl(value: string | undefined) {
  return value?.replace("/api/feature/", "/") ?? "";
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${Math.abs(value) < 0.001 && value !== 0 ? value.toExponential(2) : value.toFixed(3)}`;
}
