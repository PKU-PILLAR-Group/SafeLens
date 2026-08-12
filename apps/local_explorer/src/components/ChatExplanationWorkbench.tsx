import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  KeyRound,
  LoaderCircle,
  Send,
  Sparkles,
  Square
} from "lucide-react";

import {
  fetchNlaPreflight,
  fetchNlaProfiles,
  fetchJLensOptions,
  fetchJLensPreflight,
  type JLensJob,
  type JLensPreflight,
  type NLAJob,
  type NLAPreflight,
  type NLAProfile
} from "../api/explorerClient";
import { useJLensRunner } from "../state/useJLensRunner";
import { useNlaRunner } from "../state/useNlaRunner";
import type { ExplorerRun, JLensRow, NLARow } from "../types";

type ExplanationMode = "nla" | "j-lens";

interface ChatExplanationWorkbenchProps {
  run: ExplorerRun;
  savedRun?: ExplorerRun;
  onRunReady: (run: ExplorerRun, job: NLAJob | JLensJob) => void;
}

interface ProfileOption {
  name: string;
  baseModel: string;
  layer: number;
  component: string;
  dModel: number;
  gated: boolean;
  compatible: boolean;
}

export function ChatExplanationWorkbench({
  run,
  savedRun,
  onRunReady
}: ChatExplanationWorkbenchProps) {
  const initialLayer = preferredNlaLayer(savedRun ?? run);
  const [mode, setMode] = useState<ExplanationMode>("nla");
  const [selectedLayer, setSelectedLayer] = useState(initialLayer);
  const [selectedToken, setSelectedToken] = useState(() => preferredToken(savedRun ?? run, initialLayer));
  const [profiles, setProfiles] = useState<NLAProfile[]>([]);
  const [profilesError, setProfilesError] = useState<string | null>(null);
  const [preflight, setPreflight] = useState<NLAPreflight | null>(null);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const [confirmGatedAccess, setConfirmGatedAccess] = useState(false);
  const [jLensSource, setJLensSource] = useState("");
  const [jLensFilename, setJLensFilename] = useState("lens.pt");
  const [jLensRevision, setJLensRevision] = useState("main");
  const [jLensPreflight, setJLensPreflight] = useState<JLensPreflight | null>(null);
  const [jLensPreflightError, setJLensPreflightError] = useState<string | null>(null);
  const [jLensPreflightLoading, setJLensPreflightLoading] = useState(false);
  const [result, setResult] = useState<ExplorerRun | null>(savedRun ?? null);

  const handleNlaReady = useCallback((derived: ExplorerRun, job: NLAJob) => {
    setResult(derived);
    onRunReady(derived, job);
  }, [onRunReady]);
  const handleJLensReady = useCallback((derived: ExplorerRun, job: JLensJob) => {
    setResult(derived);
    onRunReady(derived, job);
  }, [onRunReady]);
  const nlaRunner = useNlaRunner(handleNlaReady);
  const jLensRunner = useJLensRunner(handleJLensReady);
  const currentRun = result ?? savedRun ?? run;
  const profileOptions = useMemo(
    () => mergeProfileOptions(run, profiles),
    [profiles, run]
  );
  const selectedProfile = profileOptions.find((profile) =>
    profile.layer === selectedLayer && profile.compatible
  );
  const selectedNlaRow = bestNlaRow(currentRun.nla, selectedLayer, selectedToken);
  const selectedLensRow = currentRun.jLens.find((row) =>
    row.layer === selectedLayer && row.tokenIndex === selectedToken
  );
  const nlaRunning = nlaRunner.submitting || nlaRunner.job?.status === "idle" || nlaRunner.job?.status === "loading";
  const jLensRunning = jLensRunner.submitting || jLensRunner.job?.status === "idle" || jLensRunner.job?.status === "loading";
  const running = mode === "nla" ? nlaRunning : jLensRunning;
  const canRunNla = Boolean(
    selectedProfile && preflight?.canSubmit && (!preflight.gated || confirmGatedAccess) && !nlaRunning
  );
  const canRunJLens = Boolean(jLensPreflight?.canSubmit && !jLensRunning);

  useEffect(() => {
    const controller = new AbortController();
    void fetchNlaProfiles(controller.signal).then((items) => {
      setProfiles(items);
      setProfilesError(null);
    }).catch((error) => {
      if (!controller.signal.aborted) {
        setProfilesError(error instanceof Error ? error.message : "Could not load NLA profiles.");
      }
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void fetchJLensOptions(controller.signal).then((options) => {
      const profile = options.profiles.find((candidate) => candidate.baseModel === run.modelName);
      const matchesDefault = !options.defaultModel || options.defaultModel === run.modelName;
      setJLensSource(matchesDefault ? options.defaultSource : profile?.source ?? "");
      setJLensFilename(matchesDefault ? options.defaultFilename : profile?.filename ?? options.defaultFilename);
      setJLensRevision(matchesDefault ? options.defaultRevision : profile?.revision ?? options.defaultRevision);
      setJLensPreflightError(null);
    }).catch((error) => {
      if (!controller.signal.aborted) {
        setJLensPreflightError(error instanceof Error ? error.message : "Could not load J-Lens options.");
      }
    });
    return () => controller.abort();
  }, [run.modelName]);

  useEffect(() => {
    setPreflight(null);
    setPreflightError(null);
    setConfirmGatedAccess(false);
    if (!selectedProfile) {
      setPreflightLoading(false);
      return;
    }
    const controller = new AbortController();
    setPreflightLoading(true);
    void fetchNlaPreflight({
      modelName: run.modelName,
      dModel: run.nlaCompatibility.dModel,
      availableLayers: run.nlaCompatibility.availableLayers,
      profile: selectedProfile.name
    }, controller.signal).then(setPreflight).catch((error) => {
      if (!controller.signal.aborted) {
        setPreflightError(error instanceof Error ? error.message : "NLA preflight failed.");
      }
    }).finally(() => {
      if (!controller.signal.aborted) setPreflightLoading(false);
    });
    return () => controller.abort();
  }, [run.modelName, run.nlaCompatibility.availableLayers, run.nlaCompatibility.dModel, selectedProfile]);

  useEffect(() => {
    setJLensPreflight(null);
    if (!jLensSource.trim() || !jLensFilename.trim() || !jLensRevision.trim()) {
      setJLensPreflightLoading(false);
      return;
    }
    const controller = new AbortController();
    setJLensPreflightLoading(true);
    const timer = window.setTimeout(() => {
      void fetchJLensPreflight({
        modelName: run.modelName,
        dModel: run.nlaCompatibility.dModel,
        availableLayers: run.layers,
        layer: selectedLayer,
        tokenCount: run.tokens.length,
        position: selectedToken,
        lensSource: jLensSource.trim(),
        filename: jLensFilename.trim(),
        revision: jLensRevision.trim()
      }, controller.signal).then((value) => {
        setJLensPreflight(value);
        setJLensPreflightError(null);
      }).catch((error) => {
        if (!controller.signal.aborted) {
          setJLensPreflightError(error instanceof Error ? error.message : "J-Lens preflight failed.");
        }
      }).finally(() => {
        if (!controller.signal.aborted) setJLensPreflightLoading(false);
      });
    }, 220);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [jLensFilename, jLensRevision, jLensSource, run.layers, run.modelName, run.tokens.length, selectedLayer, selectedToken]);

  function selectMode(next: ExplanationMode) {
    setMode(next);
    if (next === "nla") {
      const layer = preferredNlaLayer(currentRun);
      setSelectedLayer(layer);
      setSelectedToken(preferredToken(currentRun, layer));
      return;
    }
    const layer = preferredLensLayer(currentRun);
    setSelectedLayer(layer);
    setSelectedToken(preferredLensToken(currentRun, layer));
  }

  function selectLayer(layer: number) {
    setSelectedLayer(layer);
    const rows = mode === "nla"
      ? currentRun.nla.filter((row) => row.layer === layer)
      : currentRun.jLens.filter((row) => row.layer === layer);
    if (!rows.some((row) => row.tokenIndex === selectedToken)) {
      setSelectedToken(rows[rows.length - 1]?.tokenIndex ?? currentRun.tokens[0]?.index ?? 0);
    }
  }

  function submitNla() {
    if (!selectedProfile || !canRunNla) return;
    setResult(null);
    void nlaRunner.submit({
      run,
      profile: selectedProfile.name,
      positions: [selectedToken],
      revision: "main",
      maxNewTokens: 96,
      loadReconstructor: true,
      confirmGatedAccess
    });
  }

  function submitJLens() {
    if (!canRunJLens) return;
    setResult(null);
    void jLensRunner.submit({
      run,
      layer: selectedLayer,
      position: selectedToken,
      lensSource: jLensSource.trim(),
      filename: jLensFilename.trim(),
      revision: jLensRevision.trim(),
      topK: 10
    });
  }

  return (
    <section className="chat-analysis-workbench chat-explanation-workbench" aria-label="Explanation workbench">
      <header className="chat-workbench-heading">
        <span><Sparkles size={17} /></span>
        <div>
          <h2>Explanation</h2>
          <p>Natural-language and Jacobian readouts</p>
        </div>
        <span className={`chat-workbench-status ${selectedNlaRow?.status === "available" || selectedLensRow ? "ready" : "idle"}`}>
          <i />{mode === "nla" ? "NLA" : "J-LENS"}
        </span>
      </header>

      <div className="chat-explanation-tabs" role="tablist" aria-label="Explanation method">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "nla"}
          className={mode === "nla" ? "active" : ""}
          onClick={() => selectMode("nla")}
        >
          <Sparkles size={16} /><span><b>NLA</b><small>Natural-language explanation</small></span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "j-lens"}
          className={mode === "j-lens" ? "active" : ""}
          onClick={() => selectMode("j-lens")}
        >
          <BarChart3 size={16} /><span><b>J-Lens</b><small>Jacobian vocabulary readout</small></span>
        </button>
      </div>

      <div className="chat-explanation-selection">
        <label>
          <span><b>1</b> Layer</span>
          <select
            aria-label="Explanation layer"
            value={selectedLayer}
            disabled={running}
            onChange={(event) => selectLayer(Number(event.target.value))}
          >
            {run.layers.map((layer) => <option key={layer} value={layer}>Layer {layer}</option>)}
          </select>
        </label>
        <div className="chat-explanation-token-picker">
          <header><span><b>2</b> Token position</span><small>T{selectedToken} · {visibleToken(tokenText(run, selectedToken))}</small></header>
          <div role="radiogroup" aria-label="Explanation token position">
            {run.tokens.map((token) => (
              <button
                key={token.index}
                type="button"
                role="radio"
                aria-checked={selectedToken === token.index}
                aria-label={`Token ${token.index} ${visibleToken(token.text)}`}
                className={selectedToken === token.index ? "active" : ""}
                disabled={running}
                onClick={() => setSelectedToken(token.index)}
              >
                <small>{token.index}</small><span>{visibleToken(token.text)}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {mode === "nla" ? (
        <NlaOutput
          run={run}
          row={selectedNlaRow}
          profile={selectedProfile}
          preflight={preflight}
          preflightLoading={preflightLoading}
          error={nlaRunner.error?.message ?? preflightError ?? profilesError}
          progress={nlaRunner.job?.progress}
          running={nlaRunning}
          canRun={canRunNla}
          confirmGatedAccess={confirmGatedAccess}
          onConfirmGatedAccess={setConfirmGatedAccess}
          onRun={submitNla}
          onCancel={() => void nlaRunner.cancel()}
        />
      ) : (
        <JLenseOutput
          row={selectedLensRow}
          source={jLensSource}
          filename={jLensFilename}
          revision={jLensRevision}
          preflight={jLensPreflight}
          preflightLoading={jLensPreflightLoading}
          error={jLensRunner.error?.message ?? jLensPreflightError}
          progress={jLensRunner.job?.progress}
          running={jLensRunning}
          canRun={canRunJLens}
          onSourceChange={setJLensSource}
          onFilenameChange={setJLensFilename}
          onRevisionChange={setJLensRevision}
          onRun={submitJLens}
          onCancel={() => void jLensRunner.cancel()}
        />
      )}
    </section>
  );
}

function NlaOutput({
  run,
  row,
  profile,
  preflight,
  preflightLoading,
  error,
  progress,
  running,
  canRun,
  confirmGatedAccess,
  onConfirmGatedAccess,
  onRun,
  onCancel
}: {
  run: ExplorerRun;
  row?: NLARow;
  profile?: ProfileOption;
  preflight: NLAPreflight | null;
  preflightLoading: boolean;
  error: string | null;
  progress?: number;
  running: boolean;
  canRun: boolean;
  confirmGatedAccess: boolean;
  onConfirmGatedAccess: (value: boolean) => void;
  onRun: () => void;
  onCancel: () => void;
}) {
  const available = row?.status === "available";
  const compatibilityReason = preflight?.reason ?? compatibilityMessage(run, profile, row);
  return (
    <div className="chat-explanation-output" role="tabpanel" aria-label="NLA output">
      <div className="chat-explanation-provenance">
        <span><small>Profile</small><b>{profile?.name ?? row?.profile ?? "not registered"}</b></span>
        <span><small>Component</small><b>{row?.component ?? profile?.component ?? "resid_post"}</b></span>
        <span><small>Evidence</small><b>{available ? "AV + AR" : "not computed"}</b></span>
      </div>

      {available ? (
        <article className="chat-nla-result">
          <header><CheckCircle2 size={17} /><span>Natural-language explanation</span></header>
          <p>{row.explanation}</p>
          <dl>
            <div><dt>Cosine</dt><dd>{formatMetric(row.cosine)}</dd></div>
            <div><dt>FVE</dt><dd>{row.fve === undefined ? "n/a" : formatMetric(row.fve)}</dd></div>
            <div><dt>MSE</dt><dd>{formatMetric(row.mse)}</dd></div>
            <div><dt>Activation norm</dt><dd>{formatMetric(row.activationNorm)}</dd></div>
          </dl>
        </article>
      ) : (
        <div className="chat-nla-empty">
          <AlertCircle size={18} />
          <div>
            <strong>No exact NLA explanation at this layer and token.</strong>
            <p>{compatibilityReason}</p>
          </div>
        </div>
      )}

      {preflight?.gated && (
        <label className="chat-nla-gated">
          <input
            type="checkbox"
            checked={confirmGatedAccess}
            disabled={!preflight.tokenConfigured || running}
            onChange={(event) => onConfirmGatedAccess(event.target.checked)}
          />
          <KeyRound size={14} /> Confirm local access to this gated profile
        </label>
      )}

      {!available && (
        <div className="chat-nla-actions">
          <span aria-live="polite" className={error ? "failed" : ""}>
            {running ? <LoaderCircle size={15} /> : error ? <AlertCircle size={15} /> : <CheckCircle2 size={15} />}
            {running ? `${progress ?? 0}% · ${preflight?.reason ?? "Generating explanation"}` : error ?? (preflightLoading ? "Checking NLA compatibility" : compatibilityReason)}
          </span>
          <button type="button" disabled={!canRun && !running} onClick={running ? onCancel : onRun}>
            {running ? <Square size={14} /> : <Send size={14} />}
            {running ? "Cancel" : "Run NLA"}
          </button>
        </div>
      )}
    </div>
  );
}

function JLenseOutput({
  row,
  source,
  filename,
  revision,
  preflight,
  preflightLoading,
  error,
  progress,
  running,
  canRun,
  onSourceChange,
  onFilenameChange,
  onRevisionChange,
  onRun,
  onCancel
}: {
  row?: JLensRow;
  source: string;
  filename: string;
  revision: string;
  preflight: JLensPreflight | null;
  preflightLoading: boolean;
  error: string | null;
  progress?: number;
  running: boolean;
  canRun: boolean;
  onSourceChange: (value: string) => void;
  onFilenameChange: (value: string) => void;
  onRevisionChange: (value: string) => void;
  onRun: () => void;
  onCancel: () => void;
}) {
  const maximum = Math.max(1e-12, ...(row?.topPredictions ?? []).map((item) => Math.abs(item.logit)));
  return (
    <div className="chat-explanation-output" role="tabpanel" aria-label="J-Lens output">
      <details className="chat-jlens-config" open={!source}>
        <summary>Lens artifact</summary>
        <div>
          <label><span>Repository or local path</span><input aria-label="J-Lens artifact source" value={source} disabled={running} placeholder="organization/lens-repository" onChange={(event) => onSourceChange(event.target.value)} /></label>
          <label><span>Checkpoint file</span><input aria-label="J-Lens checkpoint file" value={filename} disabled={running} onChange={(event) => onFilenameChange(event.target.value)} /></label>
          <label><span>Revision</span><input aria-label="J-Lens artifact revision" value={revision} disabled={running} onChange={(event) => onRevisionChange(event.target.value)} /></label>
        </div>
      </details>

      {row ? (
        <>
          <div className="chat-jlens-target">
            <span><small>Observed next token</small><b>{visibleToken(row.targetTokenText)}</b></span>
            <span><small>Target rank</small><b>#{row.targetRank.toLocaleString()}</b></span>
            <span><small>Target logit</small><b>{formatMetric(row.targetLogit)}</b></span>
            <span><small>Probability</small><b>{formatProbability(row.targetProbability)}</b></span>
          </div>
          <section className="chat-jlens-predictions" aria-label="J-Lens vocabulary predictions">
            <header><strong>Top vocabulary outputs</strong><span>J(layer) x residual -&gt; final norm -&gt; unembed</span></header>
            {row.topPredictions.map((prediction, index) => (
              <div key={`${prediction.tokenId}-${index}`}>
                <small>{index + 1}</small>
                <b>{visibleToken(prediction.tokenText)}</b>
                <i><span style={{ width: `${Math.max(4, Math.abs(prediction.logit) / maximum * 100)}%` }} /></i>
                <em>{formatMetric(prediction.logit)}</em>
              </div>
            ))}
          </section>
          <p className="chat-explanation-note">Jacobian lens fitted on {row.nPrompts.toLocaleString()} prompts. {row.sourceKey}</p>
        </>
      ) : (
        <div className="chat-nla-empty">
          <AlertCircle size={18} />
          <div><strong>No Jacobian Lens result at this layer and token.</strong><p>{source ? preflight?.reason ?? "Check the configured lens artifact." : "Configure a fitted Jacobian lens artifact."}</p></div>
        </div>
      )}

      {!row && (
        <div className="chat-nla-actions">
          <span aria-live="polite" className={error ? "failed" : ""}>
            {running ? <LoaderCircle size={15} /> : error || !preflight?.canSubmit ? <AlertCircle size={15} /> : <CheckCircle2 size={15} />}
            {running ? `${progress ?? 0}% · ${preflight?.reason ?? "Computing Jacobian readout"}` : error ?? (preflightLoading ? "Checking J-Lens configuration" : preflight?.reason ?? "Configure a lens artifact")}
          </span>
          <button type="button" disabled={!canRun && !running} onClick={running ? onCancel : onRun}>
            {running ? <Square size={14} /> : <Send size={14} />}
            {running ? "Cancel" : "Run J-Lens"}
          </button>
        </div>
      )}
    </div>
  );
}

function mergeProfileOptions(run: ExplorerRun, profiles: NLAProfile[]): ProfileOption[] {
  const merged = new Map<string, ProfileOption>();
  for (const profile of run.nlaCompatibility.profiles) {
    merged.set(profile.name, {
      name: profile.name,
      baseModel: profile.baseModel,
      layer: profile.layer,
      component: profile.component,
      dModel: profile.dModel,
      gated: false,
      compatible: profile.status !== "incompatible"
    });
  }
  for (const profile of profiles) {
    const prior = merged.get(profile.name);
    merged.set(profile.name, {
      name: profile.name,
      baseModel: profile.base_model,
      layer: profile.layer,
      component: profile.component,
      dModel: profile.d_model,
      gated: profile.gated,
      compatible: prior?.compatible ?? (
        profile.base_model === run.modelName &&
        profile.d_model === run.nlaCompatibility.dModel &&
        run.layers.includes(profile.layer)
      )
    });
  }
  return [...merged.values()];
}

function bestNlaRow(rows: NLARow[], layer: number, token: number) {
  const matches = rows.filter((row) => row.layer === layer && row.tokenIndex === token);
  return matches.find((row) => row.status === "available" && row.component === "resid_post") ??
    matches.find((row) => row.status === "available") ??
    matches.find((row) => row.component === "resid_post") ?? matches[0];
}

function preferredNlaLayer(run: ExplorerRun) {
  return run.nla.find((row) => row.status === "available")?.layer ??
    run.nlaCompatibility.profiles.find((profile) => profile.status !== "incompatible")?.layer ??
    run.nla[0]?.layer ?? run.layers[run.layers.length - 1] ?? 0;
}

function preferredLensLayer(run: ExplorerRun) {
  const nlaLayer = preferredNlaLayer(run);
  return run.jLens[run.jLens.length - 1]?.layer ??
    (run.layers.includes(nlaLayer) ? nlaLayer : run.layers[0] ?? 0);
}

function preferredToken(run: ExplorerRun, layer: number) {
  return run.nla.find((row) => row.layer === layer && row.status === "available")?.tokenIndex ??
    run.nla.find((row) => row.layer === layer)?.tokenIndex ??
    run.tokens[run.tokens.length - 1]?.index ?? 0;
}

function preferredLensToken(run: ExplorerRun, layer: number) {
  const rows = run.jLens.filter((row) => row.layer === layer);
  return rows[rows.length - 1]?.tokenIndex ?? run.tokens[run.tokens.length - 1]?.index ?? 0;
}

function compatibilityMessage(run: ExplorerRun, profile?: ProfileOption, row?: NLARow) {
  if (profile) return `Profile ${profile.name} is registered; run compatibility must pass before generation.`;
  const reason = run.nlaCompatibility.profiles.find((candidate) => candidate.layer === row?.layer)?.reason;
  return reason ?? `No registered NLA profile matches ${run.modelName} at this layer.`;
}

function tokenText(run: ExplorerRun, tokenIndex: number) {
  return run.tokens.find((token) => token.index === tokenIndex)?.text ?? "";
}

function visibleToken(value: string) {
  return value.trim() || "space";
}

function formatMetric(value: number) {
  return Math.abs(value) > 0 && Math.abs(value) < 0.001 ? value.toExponential(2) : value.toFixed(4);
}

function formatProbability(value: number) {
  return value < 0.001 ? value.toExponential(2) : `${(value * 100).toFixed(2)}%`;
}
