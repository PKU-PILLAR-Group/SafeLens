import { useEffect, useMemo, useState } from "react";
import { ExternalLink, Plus, RotateCcw, Search, Send, Trash2, X } from "lucide-react";

import {
  fetchSAESteeringConfig,
  scanSAESteering,
  submitSAESteering,
  type SAESteeringConfig,
  type SAESteeringFeature,
  type SAESteeringResponse,
  type SAESteeringScan
} from "../api/explorerClient";

const DEFAULT_PROMPT = "Explain how to build a safe and helpful AI assistant.";

export function SAESteeringDemo({ onBack }: { onBack?: () => void }) {
  const [config, setConfig] = useState<SAESteeringConfig | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [features, setFeatures] = useState<SAESteeringFeature[]>([]);
  const [maxNewTokens, setMaxNewTokens] = useState(64);
  const [temperature, setTemperature] = useState(0);
  const [seed, setSeed] = useState(0);
  const [result, setResult] = useState<SAESteeringResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scan, setScan] = useState<SAESteeringScan | null>(null);
  const [scanRunning, setScanRunning] = useState(false);
  const [steerPosition, setSteerPosition] = useState<"all" | "prompt" | "generated" | "prompt_position">("all");
  const [promptPosition, setPromptPosition] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    void fetchSAESteeringConfig(controller.signal).then(setConfig).catch((reason) => {
      if (!controller.signal.aborted) setConfigError(reason instanceof Error ? reason.message : "SAE configuration unavailable.");
    });
    return () => controller.abort();
  }, []);

  const featureLimit = config?.featureCount ?? 131_072;
  const canRun = prompt.trim().length > 0 && !running;
  const selectedIds = useMemo(() => new Set(features.map((feature) => feature.featureIndex)), [features]);

  function loadPreset(preset: SAESteeringConfig["presets"][number]) {
    setFeatures(
      (preset.features.length > 0 ? preset.features : [{
        featureIndex: preset.featureIndex,
        strength: preset.strength,
        layer: preset.layer
      }]).map((feature) => ({
        featureIndex: feature.featureIndex,
        strength: feature.strength,
        layer: feature.layer
      }))
    );
    setResult(null);
    setError(null);
  }

  function addFeature() {
    let index = 0;
    while (selectedIds.has(index) && index < featureLimit) index += 1;
    if (index >= featureLimit) return;
    setFeatures((current) => [...current, { featureIndex: index, strength: 1, layer: 9 }]);
  }

  function updateFeature(position: number, patch: Partial<SAESteeringFeature>) {
    setFeatures((current) => current.map((feature, index) => index === position ? { ...feature, ...patch } : feature));
  }

  async function scanPrompt() {
    if (!prompt.trim() || scanRunning) return;
    setScanRunning(true);
    setError(null);
    try {
      setScan(await scanSAESteering({ prompt: prompt.trim(), limit: 12 }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "SAE activation scan failed.");
    } finally {
      setScanRunning(false);
    }
  }

  function selectScannedFeature(feature: SAESteeringScan["features"][number]) {
    setFeatures([{ featureIndex: feature.featureIndex, strength: feature.suggestedStrength, layer: 9 }]);
    setResult(null);
    setError(null);
  }

  async function run() {
    if (!canRun) return;
    setRunning(true);
    setError(null);
    try {
      setResult(await submitSAESteering({ prompt: prompt.trim(), features, maxNewTokens, temperature, seed, steerPosition, promptPosition: steerPosition === "prompt_position" ? promptPosition : null }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "SAE steering failed.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="sae-demo-page">
      <header className="sae-demo-header">
        <div>
          <p className="eyebrow">SAE / STEERING</p>
          <h1>Gemma-2-9B-it feature steering</h1>
          <p>Neuronpedia-compatible GemmaScope residual stream · layers 9 / 20 / 31 · 131,072 features · JumpReLU</p>
        </div>
        {onBack && <button className="icon-action" type="button" aria-label="Back to Explorer" title="Back to Explorer" onClick={onBack}><X size={16} /></button>}
      </header>

      <div className="sae-demo-layout">
        <section className="sae-demo-controls surface" aria-label="SAE steering controls">
          <label className="sae-demo-prompt"><span>Prompt</span><textarea value={prompt} rows={5} onChange={(event) => setPrompt(event.target.value)} /></label>
          <div className="sae-demo-section-heading"><strong>Features</strong><div className="sae-demo-heading-actions"><button type="button" className="sae-scan-feature" disabled={scanRunning || !prompt.trim()} onClick={() => void scanPrompt()}><Search size={15} /> {scanRunning ? "Scanning..." : "Scan prompt"}</button><button type="button" className="sae-add-feature" onClick={addFeature}><Plus size={15} /> Add feature</button></div></div>
          <div className="sae-demo-presets" role="list" aria-label="GemmaScope demo presets">
            {(config?.presets ?? []).map((preset) => (
              <button type="button" key={preset.id} className={features.some((feature) => (preset.features.length > 0 ? preset.features : [{ featureIndex: preset.featureIndex, layer: preset.layer }]).some((item) => item.featureIndex === feature.featureIndex && item.layer === feature.layer)) ? "active" : ""} onClick={() => loadPreset(preset)}>
                <strong>{preset.label}</strong><small>{(preset.features.length > 0 ? preset.features : [{ featureIndex: preset.featureIndex, strength: preset.strength, layer: preset.layer }]).map((feature) => `L${feature.layer} F${feature.featureIndex} ${feature.strength > 0 ? "+" : ""}${feature.strength}`).join(" · ")}</small><span>{preset.description}</span>
              </button>
            ))}
          </div>
          <div className="sae-demo-feature-list" aria-label="Selected steering features">
            {features.length === 0 && <p className="sae-demo-empty">No features selected. Choose a preset or add a feature ID.</p>}
            {features.map((feature, index) => (
              <div className="sae-demo-feature-row" key={`${index}-${feature.featureIndex}`}>
                <label><span>Feature</span><input aria-label={`Feature ${index + 1} index`} type="number" min={0} max={featureLimit - 1} value={feature.featureIndex} onChange={(event) => updateFeature(index, { featureIndex: clampInt(event.target.value, 0, featureLimit - 1) })} /></label>
                <label><span>Layer</span><input aria-label={`Feature ${index + 1} layer`} type="number" min={0} max={41} value={feature.layer} onChange={(event) => updateFeature(index, { layer: clampInt(event.target.value, 0, 41) })} /></label>
                <label><span>Strength</span><input aria-label={`Feature ${index + 1} strength`} type="number" min={-9000} max={9000} step={1} value={feature.strength} onChange={(event) => updateFeature(index, { strength: clampFloat(event.target.value, -9000, 9000) })} /></label>
                <button type="button" className="icon-action" aria-label={`Remove feature ${feature.featureIndex}`} title="Remove feature" onClick={() => setFeatures((current) => current.filter((_, itemIndex) => itemIndex !== index))}><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
          {scan && <section className="sae-demo-scan" aria-label="Prompt feature activations"><header><strong>Active features</strong><span>{scan.tokens.length} prompt tokens</span></header><div className="sae-demo-scan-list">{scan.features.map((feature) => <button type="button" key={feature.featureIndex} className="sae-demo-scan-row" onClick={() => selectScannedFeature(feature)}><span className="sae-demo-scan-main"><strong>F{feature.featureIndex}</strong><em>{feature.label}</em><small>peak {feature.peakTokenText || "token"}</small></span><span className="sae-demo-scan-values"><b>{feature.maxActivation.toFixed(2)}</b><small>prompt activation</small><small>NP max {feature.maxActApprox == null ? "n/a" : feature.maxActApprox.toFixed(2)} · steer {feature.vectorDefaultSteerStrength == null ? "n/a" : feature.vectorDefaultSteerStrength.toFixed(0)}</small></span></button>)}</div></section>}
          <div className="sae-demo-steer-mode"><label><span>Steer scope</span><select value={steerPosition} onChange={(event) => setSteerPosition(event.target.value as typeof steerPosition)}><option value="all">Prompt and generated tokens</option><option value="prompt">Prompt tokens only</option><option value="generated">Generated tokens only</option><option value="prompt_position">One prompt position</option></select></label>{steerPosition === "prompt_position" && <label><span>Prompt position</span><input type="number" min={0} value={promptPosition} onChange={(event) => setPromptPosition(clampInt(event.target.value, 0, 4096))} /></label>}</div>
          <div className="sae-demo-generation-grid">
            <label><span>New tokens</span><input type="number" min={1} max={512} value={maxNewTokens} onChange={(event) => setMaxNewTokens(clampInt(event.target.value, 1, 512))} /></label>
            <label><span>Temperature</span><input type="number" min={0} max={2} step={0.1} value={temperature} onChange={(event) => setTemperature(clampFloat(event.target.value, 0, 2))} /></label>
            <label><span>Seed</span><input type="number" min={0} value={seed} onChange={(event) => setSeed(clampInt(event.target.value, 0, 2_147_483_647))} /></label>
          </div>
          <button className="sae-demo-run" type="button" disabled={!canRun} onClick={() => void run()}><Send size={15} /> {running ? "Generating..." : "Generate comparison"}</button>
          {(error || configError) && <p className="sae-demo-error" role="alert">{error ?? configError}</p>}
          {config && <p className={`sae-demo-runtime ${config.checkpointPresent ? "ready" : "missing"}`}>{config.checkpointPresent ? "SAE checkpoint ready" : "SAE checkpoint not found"} · {config.device} · {config.dtype}</p>}
          {config && <a className="sae-demo-download" href={config.saeUrl} target="_blank" rel="noreferrer">Checkpoint source <ExternalLink size={13} /></a>}
        </section>

        <section className="sae-demo-results" aria-label="Default and steered generations">
          {!result ? <div className="sae-demo-result-empty"><RotateCcw size={18} /><p>Run a comparison to see the default and steered continuations side by side.</p></div> : (
            <>
              <header className="sae-demo-result-header"><div><strong>Generation comparison</strong><span>{(result.layers.length > 0 ? result.layers : [result.layer]).map((layer) => `L${layer}`).join(" / ")} · {result.hookName}</span></div><span className={result.generationChanged ? "changed" : "unchanged"}>{result.generationChanged ? "Changed" : "Same tokens"}</span></header>
              <div className="sae-demo-output-grid"><Output title="Default" output={result.default} /><Output title="Steered" output={result.steered} steered /></div>
              <footer className="sae-demo-result-meta"><span>{result.features.length} feature{result.features.length === 1 ? "" : "s"} · {result.features.map((feature) => `L${feature.layer} F${feature.featureIndex} ${feature.strength > 0 ? "+" : ""}${feature.strength}`).join(" · ") || "no injection"}</span><span>seed {result.seed} · {result.maxNewTokens} max tokens</span></footer>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function Output({ title, output, steered = false }: { title: string; output: SAESteeringResponse["default"]; steered?: boolean }) {
  return <article className={`sae-demo-output ${steered ? "is-steered" : ""}`}><header><strong>{title}</strong><span>{output.tokenIds.length} tokens</span></header><p>{output.text || "No continuation"}</p><div>{output.tokens.map((token) => <span key={token.index} title={`token ${token.index} · id ${token.tokenId}`}>{token.text || " "}</span>)}</div></article>;
}

function clampInt(value: string, minimum: number, maximum: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(minimum, Math.min(maximum, Math.round(parsed))) : minimum;
}

function clampFloat(value: string, minimum: number, maximum: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(minimum, Math.min(maximum, parsed)) : minimum;
}
