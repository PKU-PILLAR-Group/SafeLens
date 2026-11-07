import { useEffect, useMemo, useState } from "react";
import { Copy, Download } from "lucide-react";

import { fetchBuildVersion, type BuildVersion } from "../api/explorerClient";
import type { ExplorerRun } from "../types";

function objectValue(value: unknown) {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : undefined;
}

function provenanceConfig(run: ExplorerRun, mode: string) {
  const promptRunner = objectValue(run.metadata?.promptRunner);
  const parentRun = objectValue(run.metadata?.parentRun);
  const interventionJobs = run.metadata?.interventionJobs;
  const attributionJobs = run.metadata?.attributionJobs;
  const patchingJobs = run.metadata?.patchingJobs;
  const nlaJobs = run.metadata?.nlaJobs;
  return {
    mode,
    runId: run.runId,
    sampleId: run.sampleId,
    model: run.modelName,
    modelSource: run.modelSource,
    promptTokens: run.tokens.length,
    layers: run.layers,
    seed: promptRunner?.seed ?? null,
    maxNewTokens: promptRunner?.maxNewTokens ?? null,
    template: promptRunner?.template ?? null,
    parentRun: parentRun ?? null,
    intervention: run.intervention
      ? {
          mode: run.intervention.mode,
          layer: run.intervention.layer,
          sourceLayer: run.intervention.sourceLayer,
          injectLayer: run.intervention.injectLayer,
          component: run.intervention.component,
          scale: run.intervention.scale,
          positionStart: run.intervention.positionStart,
          positionEnd: run.intervention.positionEnd,
          targetTokenId: run.intervention.targetTokenId,
          targetTokenText: run.intervention.targetTokenText,
          feature: run.intervention.feature
            ? {
                id: run.intervention.feature.id,
                label: run.intervention.feature.label,
                operation: run.intervention.feature.operation,
                layer: run.intervention.feature.layer,
                neuron: run.intervention.feature.neuron,
                featureIndex: run.intervention.feature.featureIndex
              }
            : undefined
        }
      : undefined,
    jobs: {
      intervention: Array.isArray(interventionJobs)
        ? interventionJobs[interventionJobs.length - 1]
        : undefined,
      attribution: Array.isArray(attributionJobs)
        ? attributionJobs[attributionJobs.length - 1]
        : undefined,
      patching: Array.isArray(patchingJobs) ? patchingJobs[patchingJobs.length - 1] : undefined,
      nla: Array.isArray(nlaJobs) ? nlaJobs[nlaJobs.length - 1] : undefined
    }
  };
}

function downloadJson(name: string, value: unknown) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function RunProvenanceCard({ run, mode }: { run: ExplorerRun; mode: string }) {
  const [build, setBuild] = useState<BuildVersion | null>(null);
  const [copied, setCopied] = useState(false);
  const config = useMemo(() => provenanceConfig(run, mode), [mode, run]);
  const json = useMemo(() => JSON.stringify(config, null, 2), [config]);

  useEffect(() => {
    const controller = new AbortController();
    void fetchBuildVersion(controller.signal)
      .then((value) => setBuild(value))
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  async function copyConfig() {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  }

  return (
    <details className="chat-run-provenance">
      <summary>
        <span>Run configuration</span>
        <small>
          {run.modelName} · {run.tokens.length} tokens · {run.layers.length} layers
          {build ? ` · v${build.version}${build.commit ? ` (${build.commit})` : ""}` : ""}
        </small>
      </summary>
      <div className="chat-run-provenance-body">
        <dl>
          <div><dt>Run</dt><dd>{run.runId}</dd></div>
          <div><dt>Sample</dt><dd>{run.sampleId}</dd></div>
          <div><dt>Model source</dt><dd>{run.modelSource}</dd></div>
          <div><dt>Seed / max tokens</dt><dd>{String(config.seed ?? "—")} / {String(config.maxNewTokens ?? "—")}</dd></div>
          <div><dt>Build</dt><dd>{build ? `v${build.version}${build.commit ? ` · ${build.commit}` : ""}` : "loading"}</dd></div>
        </dl>
        <div className="chat-run-provenance-actions">
          <button type="button" onClick={() => void copyConfig()}>
            <Copy size={13} /> {copied ? "Copied" : "Copy JSON"}
          </button>
          <button
            type="button"
            onClick={() => downloadJson(`safelens-${run.runId}-${run.sampleId}.json`, config)}
          >
            <Download size={13} /> Export JSON
          </button>
        </div>
        <pre>{json}</pre>
      </div>
    </details>
  );
}
