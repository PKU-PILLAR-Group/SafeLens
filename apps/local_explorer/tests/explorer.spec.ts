import { expect, test, type CDPSession } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { realRun } from "../src/realRunData";
import { explorerRunSchema, parseExplorerArtifact } from "../src/schemas/explorerArtifact";
import { explorerSessionSchema } from "../src/schemas/explorerSession";
import {
  formatMetricDelta,
  formatMetricNumber,
  metricDisplayLabel
} from "../src/metricFormatting";
import type { ExplorerRun } from "../src/types";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("safelens-workspace-layout", "dense");
  });
});

function remoteIndex(run: typeof realRun, sourceName = "remote-validation.explorer.json") {
  return {
    schemaVersion: "1.0",
    source: "local-workspace",
    rootName: "test-artifacts",
    runs: [{
      runId: run.runId,
      sampleId: run.sampleId,
      modelName: run.modelName,
      modelSource: run.modelSource,
      tokenCount: run.tokens.length,
      layerCount: run.layers.length,
      artifactId: "fixture-artifact",
      sourceName,
      modifiedAt: "2026-07-13T12:00:00+00:00",
      sizeBytes: 1024
    }],
    diagnostics: []
  };
}

async function downloadJson(download: import("@playwright/test").Download) {
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function chunkMetadata(run: ExplorerRun) {
  const {
    residualCells: _residualCells,
    logitLens: _logitLens,
    attentionHeads: _attentionHeads,
    attentionCells: _attentionCells,
    mlpNeurons: _mlpNeurons,
    mlpCells: _mlpCells,
    attributionTracks: _attributionTracks,
    attributionMethods: _attributionMethods,
    nla: _nla,
    patching: _patching,
    intervention: _intervention,
    ...base
  } = run;
  const components = [
    "residualCells", "logitLens", "attentionHeads", "attentionCells", "mlpNeurons",
    "mlpCells", "attributionTracks", "attributionMethods", "nla", "patching", "intervention"
  ];
  return {
    schemaVersion: "1.0",
    protocol: "safelens-chunks-v1",
    runId: run.runId,
    sampleId: run.sampleId,
    artifactId: "fixture-artifact",
    version: "metadata-v1",
    base,
    chunks: components.map((component) => ({
      component,
      itemCount: Array.isArray(run[component as keyof ExplorerRun])
        ? (run[component as keyof ExplorerRun] as unknown[]).length
        : Number(Boolean(run[component as keyof ExplorerRun])),
      rangeAxis: component === "attentionHeads"
        ? "token-square"
        : ["mlpNeurons", "attributionTracks", "attributionMethods"].includes(component)
          ? "token-values"
          : component === "intervention" ? "none" : "token",
      layerFilter: !["attributionTracks", "intervention"].includes(component),
      selectorFilter: ["attentionHeads", "mlpNeurons", "attributionTracks", "attributionMethods", "nla"].includes(component)
    }))
  };
}

function chunkResponse(run: ExplorerRun, component: string, params: URLSearchParams) {
  const tokenStart = Number(params.get("tokenStart"));
  const tokenEnd = Number(params.get("tokenEnd"));
  const sourceStart = params.has("sourceStart") ? Number(params.get("sourceStart")) : tokenStart;
  const sourceEnd = params.has("sourceEnd") ? Number(params.get("sourceEnd")) : tokenEnd;
  const layer = params.has("layer") ? Number(params.get("layer")) : null;
  const inRange = (row: { layer?: number; tokenIndex: number }) =>
    row.tokenIndex >= tokenStart && row.tokenIndex < tokenEnd &&
    (layer === null || row.layer === layer);
  let data: unknown = null;
  if (["residualCells", "logitLens", "attentionCells", "mlpCells", "nla"].includes(component)) {
    data = (run[component as keyof ExplorerRun] as Array<{ layer?: number; tokenIndex: number }>).filter(inRange);
  } else if (component === "attentionHeads") {
    data = run.attentionHeads.filter((head) => layer === null || head.layer === layer).map((head) => ({
      ...head,
      distributionByToken: head.distributionByToken
        .slice(tokenStart, tokenEnd)
        .map((row) => row.slice(sourceStart, sourceEnd)),
      chunk: {
        destinationStart: tokenStart,
        destinationEnd: tokenEnd,
        sourceStart,
        sourceEnd
      }
    }));
  } else if (component === "mlpNeurons") {
    data = run.mlpNeurons.filter((neuron) => layer === null || neuron.layer === layer).map((neuron) => ({
      ...neuron,
      activationsByToken: neuron.activationsByToken.slice(tokenStart, tokenEnd),
      chunk: { tokenStart, tokenEnd }
    }));
  } else if (component === "attributionTracks") {
    data = run.attributionTracks.map((track) => ({
      ...track,
      values: track.values.slice(tokenStart, tokenEnd),
      chunk: { tokenStart, tokenEnd }
    }));
  } else if (component === "attributionMethods") {
    data = run.attributionMethods.map((method) => ({
      ...method,
      rows: method.rows.map((row) => ({
        ...row,
        values: row.values.slice(tokenStart, tokenEnd),
        chunk: { tokenStart, tokenEnd }
      }))
    }));
  } else if (component === "patching") data = run.patching ?? null;
  else if (component === "intervention") data = run.intervention ?? null;
  return {
    schemaVersion: "1.0",
    protocol: "safelens-chunks-v1",
    runId: run.runId,
    sampleId: run.sampleId,
    artifactId: "fixture-artifact",
    version: "metadata-v1",
    component,
    tokenRange: [tokenStart, tokenEnd],
    sourceRange: component === "attentionHeads" ? [sourceStart, sourceEnd] : null,
    layer,
    selector: params.get("selector"),
    data
  };
}

function promptJob(
  status: "idle" | "loading" | "ready" | "error" | "cancelled",
  result: typeof realRun | null = null
) {
  return {
    id: "prompt-job-12345678",
    kind: "prompt-run",
    status,
    stage: status === "ready" ? "complete" : status === "cancelled" ? "cancelled" : "queued",
    progress: status === "ready" ? 100 : status === "loading" || status === "cancelled" ? 45 : 0,
    detail: status === "ready"
      ? "Explorer run is ready and indexed in the workspace."
      : status === "cancelled"
        ? "Cancellation requested. No result was added to the Run Library."
        : "Waiting for the local model worker.",
    createdAt: "2026-07-13T12:00:00+00:00",
    updatedAt: "2026-07-13T12:00:01+00:00",
    request: {
      prompt: "Analyze a generated safety response.",
      template: "chat",
      model: "sshleifer/tiny-gpt2",
      seed: 23,
      maxNewTokens: 12,
      temperature: 0.4
    },
    result,
    error: null
  };
}

function attributionJob(
  status: "idle" | "loading" | "ready" | "error" | "cancelled",
  run: typeof realRun,
  result: typeof realRun | null = null
) {
  return {
    id: "attribution-job-87654321",
    kind: "attribution",
    status,
    stage: status === "ready" ? "complete" : status === "cancelled" ? "cancelled" : "integrated-gradients",
    progress: status === "ready" ? 100 : status === "loading" || status === "cancelled" ? 55 : 0,
    detail: status === "ready"
      ? "Integrated Gradients evidence is ready in a derived Explorer run."
      : status === "cancelled"
        ? "Cancellation requested. No result was added to the Run Library."
        : "Computing signed token scores.",
    createdAt: "2026-07-13T12:00:00+00:00",
    updatedAt: "2026-07-13T12:00:01+00:00",
    request: {
      sourceRun: { runId: run.runId, sampleId: run.sampleId, modelName: run.modelName },
      response: " stairs stairs",
      objective: "response_token_logit",
      targetResponseIndex: 1,
      baseline: "pad_token",
      nSteps: 16
    },
    result,
    error: null
  };
}

const qwenNlaProfile = {
  name: "qwen2.5-7b-l20",
  base_model: "Qwen/Qwen2.5-7B-Instruct",
  layer: 20,
  component: "resid_post",
  d_model: 3584,
  av_repo: "kitft/nla-qwen2.5-7b-L20-av",
  ar_repo: "kitft/nla-qwen2.5-7b-L20-ar",
  gated: false,
  description: "Public Qwen NLA pair."
};

function nlaPreflight(compatible: boolean) {
  return {
    profile: qwenNlaProfile.name,
    baseModel: qwenNlaProfile.base_model,
    layer: 20,
    component: "resid_post",
    dModel: 3584,
    avRepo: qwenNlaProfile.av_repo,
    arRepo: qwenNlaProfile.ar_repo,
    gated: false,
    tokenConfigured: false,
    modelMatches: compatible,
    layerAvailable: compatible,
    dModelMatches: compatible,
    status: compatible ? "compatible" : "incompatible",
    canSubmit: compatible,
    reason: compatible
      ? "Model, layer, component profile and d_model are compatible."
      : "model requires Qwen/Qwen2.5-7B-Instruct; layer L20 is not cached; d_model requires 3584, run has 2"
  };
}

function nlaJob(
  status: "idle" | "loading" | "ready" | "error" | "cancelled",
  sourceRun: typeof realRun,
  result: typeof realRun | null = null
) {
  const preflight = nlaPreflight(true);
  return {
    id: "nla-job-24681357",
    kind: "nla",
    status,
    stage: status === "ready" ? "complete" : status === "cancelled" ? "cancelled" : "nla-av-ar",
    progress: status === "ready" ? 100 : status === "loading" || status === "cancelled" ? 60 : 0,
    detail: status === "ready"
      ? "Exact NLA explanations and fidelity rows are ready in a derived run."
      : status === "cancelled"
        ? "Cancellation requested. No result was added to the Run Library."
        : "Explaining exact activation.",
    createdAt: "2026-07-13T12:00:00+00:00",
    updatedAt: "2026-07-13T12:00:01+00:00",
    request: {
      profile: qwenNlaProfile.name,
      positions: [10],
      revision: "commit-abc123",
      maxNewTokens: 64,
      loadReconstructor: true,
      confirmGatedAccess: false,
      sourceRun: {
        runId: sourceRun.runId,
        sampleId: sourceRun.sampleId,
        modelName: sourceRun.modelName
      },
      preflight
    },
    result,
    error: null
  };
}

function patchingPreflight(run: typeof realRun, corruptedPrompt: string) {
  const differs = corruptedPrompt !== run.prompt;
  return {
    modelAllowed: true,
    promptsDiffer: differs,
    tokenCountMatches: true,
    targetTokenValid: true,
    componentSupported: true,
    cleanTokenCount: run.tokens.length,
    corruptedTokenCount: run.tokens.length,
    changedPositions: differs ? [10] : [],
    targetTokenId: run.logitLens[0].targetTokenId,
    targetTokenText: run.logitLens[0].targetTokenText,
    corruptedTokens: run.tokens.map((token) => ({
      index: token.index,
      tokenId: token.tokenId + (differs && token.index === 10 ? 1 : 0),
      text: differs && token.index === 10 ? " changed" : token.text,
      changed: differs && token.index === 10
    })),
    canSubmit: differs,
    reason: differs
      ? "Prompts are positionally aligned and ready for causal activation patching."
      : "clean and corrupted prompts are identical; no aligned token changed"
  };
}

function patchingJob(
  status: "idle" | "loading" | "ready" | "error" | "cancelled",
  sourceRun: typeof realRun,
  result: typeof realRun | null = null
) {
  const preflight = patchingPreflight(sourceRun, "Corrupted aligned prompt");
  return {
    id: "patching-job-13572468",
    kind: "patching",
    status,
    stage: status === "ready" ? "complete" : status === "cancelled" ? "cancelled" : "patch-grid",
    progress: status === "ready" ? 100 : status === "loading" || status === "cancelled" ? 58 : 0,
    detail: status === "ready"
      ? "Activation patching causal grid is ready in a derived Explorer run."
      : "Evaluating one causal patch cell.",
    createdAt: "2026-07-13T12:00:00+00:00",
    updatedAt: "2026-07-13T12:00:01+00:00",
    request: {
      corruptedPrompt: "Corrupted aligned prompt",
      component: "resid_post",
      layers: [1],
      positions: [10],
      targetTokenId: preflight.targetTokenId,
      sourceRun: {
        runId: sourceRun.runId,
        sampleId: sourceRun.sampleId,
        modelName: sourceRun.modelName
      },
      preflight
    },
    result,
    error: null
  };
}

function interventionPreflight(run: typeof realRun, desiredPrompt: string, undesiredPrompt: string) {
  const differs = desiredPrompt.trim() !== undesiredPrompt.trim();
  return {
    modelAllowed: true,
    layerAvailable: true,
    componentSupported: true,
    positionRangeValid: true,
    targetTokenValid: true,
    referencesDiffer: differs,
    targetTokenId: run.logitLens[0].targetTokenId,
    targetTokenText: run.logitLens[0].targetTokenText,
    positionStart: 10,
    positionEnd: 11,
    canSubmit: differs,
    reason: differs
      ? "Intervention references, activation target, range, and objective are ready."
      : "desired and undesired references are identical"
  };
}

function interventionJob(
  status: "idle" | "loading" | "ready" | "error" | "cancelled",
  sourceRun: typeof realRun,
  result: typeof realRun | null = null
) {
  const desiredPrompt = "Provide a safe and helpful response.";
  const undesiredPrompt = "Bypass safety guidance.";
  return {
    id: "intervention-job-97531864",
    kind: "intervention",
    status,
    stage: status === "ready" ? "complete" : status === "cancelled" ? "cancelled" : "generation",
    progress: status === "ready" ? 100 : status === "loading" || status === "cancelled" ? 62 : 0,
    detail: status === "ready"
      ? "Intervention comparison is ready in a derived Explorer run."
      : status === "cancelled"
        ? "Cancellation requested. No result was added to the Run Library."
        : "Comparing matched generation outputs.",
    createdAt: "2026-07-13T12:00:00+00:00",
    updatedAt: "2026-07-13T12:00:01+00:00",
    request: {
      desiredPrompt,
      undesiredPrompt,
      layer: 1,
      component: "resid_post",
      scale: 1,
      positionStart: 10,
      positionEnd: 11,
      targetTokenId: sourceRun.logitLens[0].targetTokenId,
      seed: 0,
      maxNewTokens: 16,
      temperature: 0,
      sourceRun: { runId: sourceRun.runId, sampleId: sourceRun.sampleId, modelName: sourceRun.modelName },
      preflight: interventionPreflight(sourceRun, desiredPrompt, undesiredPrompt)
    },
    result,
    error: null
  };
}

function expandedTimelineRun(tokenCount: number) {
  const tokens = Array.from({ length: tokenCount }, (_, index) => ({
    ...realRun.tokens[index % realRun.tokens.length],
    index,
    text: ` item-${index}`,
    tokenId: 20_000 + index,
    source: "prompt" as const,
    risk: index === 0 ? 1 : Math.max(0, 0.8 - index / tokenCount),
    attribution: (index % 11) / 10
  }));
  const cells = (metric: string, sourceKey: string) => realRun.layers.flatMap((layer) =>
    tokens.map((token) => ({
      layer,
      tokenIndex: token.index,
      value: token.risk,
      rawValue: token.risk,
      metric,
      sourceKey
    }))
  );
  return {
    ...realRun,
    runId: "long-timeline-validation",
    sampleId: "sample-260",
    prompt: "Long timeline validation sample",
    tokens,
    attentionHeads: realRun.attentionHeads
      .filter((head) => head.head === 0)
      .map((head) => ({
        ...head,
        distributionByToken: Array.from({ length: tokenCount }, (_, destination) =>
          Array.from({ length: tokenCount }, (_, source) =>
            source <= destination ? 1 / (destination + 1) : 0
          )
        )
      })),
    mlpNeurons: realRun.mlpNeurons
      .filter((neuron) => neuron.neuron === realRun.mlpNeurons.find(
        (candidate) => candidate.layer === neuron.layer
      )?.neuron)
      .map((neuron) => ({
        ...neuron,
        activationsByToken: tokens.map((token) => (token.index % 9 - 4) / 10)
      })),
    residualCells: realRun.layers.flatMap((layer) => tokens.map((token) => ({
      layer,
      tokenIndex: token.index,
      norm: 0.1 + token.index / tokenCount,
      rawDirection: token.risk,
      riskDirection: token.risk,
      semanticDensity: token.index / tokenCount
    }))),
    attentionCells: cells("attention", "timeline.attention"),
    mlpCells: cells("mlp", "timeline.mlp"),
    attributionTracks: realRun.attributionTracks.map((track) => ({
      ...track,
      values: tokens.map((token) => token.attribution)
    })),
    attributionMethods: realRun.attributionMethods.map((method) => ({
      ...method,
      rows: method.rows.map((row) => ({
        ...row,
        values: tokens.map((token) => token.attribution - 0.5)
      }))
    }))
  };
}

test("loads a requested workspace run without overwriting its URL while discovery is pending", async ({ page }) => {
  const remoteRun = {
    ...realRun,
    runId: "remote-validation-run",
    sampleId: "remote-sample",
    prompt: "Workspace API sample prompt",
    tokens: realRun.tokens.map((token) =>
      token.index === 10 ? { ...token, text: "REMOTE_BREAK" } : token
    )
  };
  let releaseIndex: (() => void) | undefined;
  const indexGate = new Promise<void>((resolve) => { releaseIndex = resolve; });
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await indexGate;
    await route.fulfill({ json: remoteIndex(remoteRun) });
  });
  await page.route(/\/api\/runs\/remote-validation-run\/samples\/remote-sample$/, async (route) => {
    await route.fulfill({ json: remoteRun });
  });

  await page.goto("/explorer?run=remote-validation-run&sample=remote-sample&view=overview");
  await expect(page).toHaveURL(/run=remote-validation-run/);
  await expect(page).toHaveURL(/sample=remote-sample/);
  await expect(page.getByLabel("Workspace API status")).toContainText("Connecting to workspace");

  releaseIndex?.();
  await expect(page.getByLabel("Workspace API status")).toContainText("test-artifacts · 1 ready");
  await expect(page.getByLabel("Run and sample selector")).toHaveValue(
    "remote-validation-run::remote-sample"
  );
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);
  await expect(page.locator(".active-run-card")).toContainText("workspace");
  await expect(page.locator(".token-pill").filter({ hasText: "REMOTE_BREAK" })).toBeVisible();
  await expect(page.getByLabel("Prompt runner text")).toHaveValue("Workspace API sample prompt");
});

test("keeps bundled data usable and retries workspace discovery after an API error", async ({ page }) => {
  const remoteRun = {
    ...realRun,
    runId: "retry-validation-run",
    sampleId: "retry-sample"
  };
  let apiReady = false;
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    if (!apiReady) {
      await route.fulfill({ status: 503, json: { detail: "temporarily unavailable" } });
      return;
    }
    await route.fulfill({ json: remoteIndex(remoteRun, "retry.explorer.json") });
  });
  await page.route(/\/api\/runs\/retry-validation-run\/samples\/retry-sample$/, async (route) => {
    await route.fulfill({ json: remoteRun });
  });

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText("Workspace API error");
  await expect(page.getByRole("heading", { name: "Token Timeline" })).toBeVisible();
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(1);

  apiReady = true;
  await page.getByLabel("Retry workspace discovery").click();
  await expect(page.getByLabel("Workspace API status")).toContainText("test-artifacts · 1 ready");
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);
});

test("distinguishes offline transport from schema errors while preserving local runs", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const localRun = {
    ...realRun,
    runId: "offline-local-run",
    sampleId: "offline-local-sample",
    prompt: "Local analysis remains available while workspace is offline"
  };
  const remoteRun = {
    ...realRun,
    runId: "recovered-workspace-run",
    sampleId: "recovered-workspace-sample"
  };
  let phase: "offline" | "schema" | "ready" = "offline";
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    if (phase === "offline") {
      await route.abort("connectionrefused");
      return;
    }
    if (phase === "schema") {
      await route.fulfill({
        json: {
          schemaVersion: "9.0",
          source: "local-workspace",
          rootName: "invalid-workspace",
          runs: []
        }
      });
      return;
    }
    await route.fulfill({ json: remoteIndex(remoteRun, "recovered.explorer.json") });
  });

  await page.goto("/explorer");
  let status = page.getByLabel("Workspace API status");
  await expect(status).toContainText("Workspace offline");
  await expect(status).toContainText("Bundled and imported runs remain available");
  await expect(page.getByLabel("Retry workspace discovery")).toBeVisible();

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "offline-local.explorer.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(localRun))
  });
  await expect(page.getByLabel("Run and sample selector"))
    .toHaveValue("offline-local-run::offline-local-sample");
  await expect(page.getByLabel("Prompt runner text")).toHaveValue(localRun.prompt);
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);

  phase = "schema";
  await page.getByLabel("Retry workspace discovery").click();
  await expect(status).toContainText("Workspace schema error");
  await expect(status).toContainText("Explorer API index failed validation");
  await expect(page.getByLabel("Run and sample selector"))
    .toHaveValue("offline-local-run::offline-local-sample");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByLabel("Open run library").click();
  const drawer = page.getByRole("dialog", { name: "Runs and samples" });
  status = drawer.getByLabel("Workspace API status");
  await expect(status).toContainText("Workspace schema error");
  const statusBox = await status.boundingBox();
  expect(statusBox).not.toBeNull();
  expect(statusBox!.width).toBeLessThanOrEqual(356);
  for (const control of [
    drawer.getByLabel("Run and sample selector"),
    drawer.getByRole("button", { name: "Import JSON" }),
    drawer.getByLabel("Search available runs"),
    drawer.getByLabel("Filter runs by source"),
    drawer.getByLabel("Next run window")
  ]) {
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThan(43.5);
  }
  for (const control of [
    drawer.getByLabel("Close run library"),
    drawer.getByLabel("Retry workspace discovery")
  ]) {
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThan(43.5);
    expect(box!.width).toBeGreaterThan(43.5);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".async-state-panel")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);

  phase = "ready";
  await drawer.getByLabel("Retry workspace discovery").click();
  await expect(status).toContainText("test-artifacts · 1 ready");
  const selector = drawer.getByLabel("Run and sample selector");
  await expect(selector.locator("option")).toHaveCount(3);
  await expect(selector).toHaveValue("offline-local-run::offline-local-sample");
  await expect(drawer.getByLabel("Prompt runner text")).toHaveValue(localRun.prompt);
});

test("indexes workspace runs without downloading samples until selection", async ({ page }) => {
  const remoteRun = {
    ...realRun,
    runId: "lazy-workspace-run",
    sampleId: "lazy-sample",
    prompt: "Loaded only after explicit selection"
  };
  let sampleRequests = 0;
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({ json: remoteIndex(remoteRun, "lazy.explorer.json") });
  });
  await page.route(/\/api\/runs\/lazy-workspace-run\/samples\/lazy-sample$/, async (route) => {
    sampleRequests += 1;
    await route.fulfill({ json: remoteRun });
  });

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText("test-artifacts · 1 ready");
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);
  expect(sampleRequests).toBe(0);

  await page.getByLabel("Run and sample selector").selectOption("lazy-workspace-run::lazy-sample");
  await expect(page.getByLabel("Run and sample selector")).toHaveValue(
    "lazy-workspace-run::lazy-sample"
  );
  await expect(page.getByLabel("Prompt runner text")).toHaveValue(
    "Loaded only after explicit selection"
  );
  expect(sampleRequests).toBe(1);
});

test("explains bundled-over-workspace source conflicts without mixing artifacts", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  const duplicateIndex = remoteIndex(realRun, "workspace-duplicate.explorer.json");
  duplicateIndex.runs[0].tokenCount = realRun.tokens.length + 7;
  let sampleRequests = 0;
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({ json: duplicateIndex });
  });
  await page.route(
    new RegExp(`/api/runs/${realRun.runId}/samples/${realRun.sampleId}$`),
    async (route) => {
      sampleRequests += 1;
      await route.fulfill({ json: realRun });
    }
  );

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText("test-artifacts · 1 ready");
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(1);
  const active = page.locator(".active-run-card");
  await expect(active.locator(".status-pill")).toContainText("bundled");
  await expect(active.locator(".status-pill")).toContainText("2 sources");
  const resolution = active.locator(".run-source-resolution");
  await expect(resolution.locator("summary")).toContainText("2 indexed sources");
  await expect(resolution.locator("summary")).toContainText("using bundled");
  await resolution.locator("summary").click();
  await expect(resolution).toContainText("Bundled → browser artifact → workspace API");
  const candidates = resolution.getByRole("list", { name: "Run source candidates" });
  await expect(candidates.getByRole("listitem")).toHaveCount(2);
  await expect(candidates.getByRole("listitem").nth(0)).toContainText("bundled · bundled real model cache");
  await expect(candidates.getByRole("listitem").nth(0)).toContainText("selected");
  await expect(candidates.getByRole("listitem").nth(1)).toContainText("workspace · workspace-duplicate.explorer.json");
  await expect(candidates.getByRole("listitem").nth(1)).toContainText("metadata differs");
  await expect(resolution).toContainText("values are never mixed across artifacts");
  expect(sampleRequests).toBe(0);

  const recent = page.getByLabel("Available workspace and imported runs");
  await expect(recent.locator(":scope > div")).toHaveCount(1);
  await expect(recent).toContainText("2 sources");
  await expect(recent).toContainText("using bundled over workspace");
  const recentButton = recent.getByRole("button").first();
  const recentHeading = recentButton.locator(".recent-run-heading");
  const recentBadge = recentHeading.locator(".status-pill");
  const [buttonBox, headingBox, badgeBox] = await Promise.all([
    recentButton.boundingBox(),
    recentHeading.boundingBox(),
    recentBadge.boundingBox()
  ]);
  expect(buttonBox).not.toBeNull();
  expect(headingBox).not.toBeNull();
  expect(badgeBox).not.toBeNull();
  expect(headingBox!.x).toBeGreaterThanOrEqual(buttonBox!.x);
  expect(headingBox!.x + headingBox!.width).toBeLessThanOrEqual(buttonBox!.x + buttonBox!.width);
  expect(badgeBox!.x).toBeGreaterThanOrEqual(headingBox!.x);
  expect(badgeBox!.x + badgeBox!.width).toBeLessThanOrEqual(headingBox!.x + headingBox!.width);
  expect(await recentButton.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  expect(await recentHeading.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  expect(await recentBadge.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  const screenshotPath = testInfo.outputPath("read-only-source-conflict-card.png");
  await recent.locator(":scope > div").screenshot({ path: screenshotPath });
  await testInfo.attach("read-only-source-conflict-card", {
    path: screenshotPath,
    contentType: "image/png"
  });
  await page.getByLabel("Filter runs by source").selectOption("remote");
  await expect(recent.locator(":scope > div")).toHaveCount(1);
  await page.getByLabel("Search available runs").fill("workspace-duplicate");
  await expect(recent.locator(":scope > div")).toHaveCount(1);
  expect(sampleRequests).toBe(0);
});

test("shows browser-over-workspace source resolution in the mobile run library", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => window.localStorage.clear());
  const remoteRun = {
    ...realRun,
    runId: "mobile-source-conflict-run",
    sampleId: "mobile-source-conflict-sample",
    prompt: "Workspace duplicate should remain shadowed"
  };
  const localRun = {
    ...remoteRun,
    prompt: "Browser artifact wins source conflict"
  };
  let sampleRequests = 0;
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({ json: remoteIndex(remoteRun, "workspace-mobile-duplicate.json") });
  });
  await page.route(
    /\/api\/runs\/mobile-source-conflict-run\/samples\/mobile-source-conflict-sample$/,
    async (route) => {
      sampleRequests += 1;
      await route.fulfill({ json: remoteRun });
    }
  );

  await page.goto("/explorer");
  await expect(page.getByLabel("Quick run selector").locator("option")).toHaveCount(2);
  await page.getByLabel("Open run library").click();
  let drawer = page.getByRole("dialog", { name: "Runs and samples" });
  await drawer.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "browser-mobile-duplicate.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(localRun))
  });
  await expect(page.getByLabel("Quick run selector"))
    .toHaveValue("mobile-source-conflict-run::mobile-source-conflict-sample");
  await expect(page.getByLabel("Prompt runner text"))
    .toHaveValue("Browser artifact wins source conflict");
  expect(sampleRequests).toBe(0);

  await page.getByLabel("Open run library").click();
  drawer = page.getByRole("dialog", { name: "Runs and samples" });
  const active = drawer.locator(".active-run-card");
  await expect(active.locator(".status-pill")).toContainText("local");
  await expect(active.locator(".status-pill")).toContainText("2 sources");
  const summary = active.locator(".run-source-resolution summary");
  await expect(summary).toContainText("using local");
  const summaryBox = await summary.boundingBox();
  expect(summaryBox).not.toBeNull();
  expect(summaryBox!.height).toBeGreaterThan(43.5);
  await summary.click();
  const candidates = active.getByRole("list", { name: "Run source candidates" });
  await expect(candidates.getByRole("listitem")).toHaveCount(2);
  await expect(candidates.getByRole("listitem").nth(0)).toContainText("local · browser-mobile-duplicate.json");
  await expect(candidates.getByRole("listitem").nth(0)).toContainText("selected");
  await expect(candidates.getByRole("listitem").nth(1)).toContainText("workspace · workspace-mobile-duplicate.json");
  await expect(candidates.getByRole("listitem").nth(1)).toContainText("lower priority");
  const recentCard = drawer.getByLabel("Available workspace and imported runs")
    .locator(":scope > div.active");
  await expect(recentCard.locator(".recent-run-context"))
    .toContainText("mobile-source-conflict-sample · sshleifer/tiny-gpt2");
  await expect(recentCard.locator(".recent-run-dimensions"))
    .toContainText("20 tokens · 2 layers · browser-mobile-duplicate.json");
  await expect(recentCard.locator(".recent-run-times")).toContainText("Opened");
  await expect(recentCard.locator(".recent-run-times")).toContainText("Updated");
  const recentCardBox = await recentCard.getByRole("button").first().boundingBox();
  expect(recentCardBox).not.toBeNull();
  expect(recentCardBox!.height).toBeGreaterThan(73.5);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".run-library-panel")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  expect(sampleRequests).toBe(0);
});

test("orders the run browser by persisted last-used time with complete metadata", async ({ page }) => {
  const remoteRuns = [0, 1, 2].map((index) => ({
    ...realRun,
    runId: `recency-run-${index}`,
    sampleId: `recency-sample-${index}`,
    prompt: `Recency sample ${index}`
  }));
  const modifiedAt = [
    "2026-07-10T12:00:00Z",
    "2026-07-13T12:00:00Z",
    "2026-07-12T12:00:00Z"
  ];
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        ...remoteIndex(realRun),
        rootName: "recency-workspace",
        runs: remoteRuns.map((run, index) => ({
          ...remoteIndex(run, `recency-${index}.explorer.json`).runs[0],
          modifiedAt: modifiedAt[index]
        }))
      }
    });
  });
  await page.route(/\/api\/runs\/recency-run-0\/samples\/recency-sample-0$/, async (route) => {
    await route.fulfill({ json: remoteRuns[0] });
  });

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText("recency-workspace · 3 ready");
  let recent = page.getByLabel("Available workspace and imported runs");
  await expect(recent.locator(":scope > div").nth(0)).toContainText("recency-run-1");
  await expect(recent.locator(":scope > div").nth(1)).toContainText("recency-run-2");
  await expect(recent.locator(":scope > div").nth(2)).toContainText("recency-run-0");

  await page.getByLabel("Run and sample selector").selectOption("recency-run-0::recency-sample-0");
  await expect(page.getByLabel("Prompt runner text")).toHaveValue("Recency sample 0");
  await page.getByLabel("Quick run selector").selectOption(`${realRun.runId}::${realRun.sampleId}`);
  await expect(page.getByLabel("Prompt runner text")).toHaveValue(realRun.prompt);

  const first = recent.locator(":scope > div").nth(0);
  await expect(first).toContainText("recency-run-0");
  await expect(first.locator(".recent-run-context"))
    .toContainText("recency-sample-0 · sshleifer/tiny-gpt2");
  await expect(first.locator(".recent-run-dimensions"))
    .toContainText("20 tokens · 2 layers · recency-0.explorer.json");
  const times = first.locator(".recent-run-times");
  await expect(times).toContainText("Opened");
  await expect(times).toContainText("Updated");
  await expect(times.getByText("07-10 12:00 UTC", { exact: true })).toBeVisible();
  await expect(times.locator("time")).toHaveCount(2);
  const openedAt = await times.locator("time").nth(0).getAttribute("datetime");
  expect(Number.isFinite(Date.parse(openedAt ?? ""))).toBe(true);
  expect(await times.locator("time").nth(1).getAttribute("datetime"))
    .toBe("2026-07-10T12:00:00.000Z");
  const storedUsage = await page.evaluate(() => JSON.parse(
    window.localStorage.getItem("safelens.localExplorer.runUsage.v1") ?? "{}"
  ));
  expect(storedUsage["recency-run-0::recency-sample-0"]).toBeTruthy();

  await page.reload();
  await expect(page.getByLabel("Workspace API status")).toContainText("recency-workspace · 3 ready");
  recent = page.getByLabel("Available workspace and imported runs");
  await expect(recent.locator(":scope > div").nth(0)).toContainText("recency-run-0");
  await expect(recent.locator(":scope > div").nth(0).locator(".recent-run-times"))
    .toContainText("Opened");

  const search = page.getByLabel("Search available runs");
  await expect(search).toHaveAttribute("placeholder", "run, sample, model, date");
  await search.fill("07-12 12:00 UTC");
  await expect(recent.locator(":scope > div")).toHaveCount(1);
  await expect(recent).toContainText("recency-run-2");
  await search.fill("07-10 12:00 UTC");
  await expect(recent.locator(":scope > div")).toHaveCount(1);
  await expect(recent).toContainText("recency-run-0");
});

test("searches, filters, and windows a large workspace run library", async ({ page }) => {
  let sampleRequests = 0;
  page.on("request", (request) => {
    if (/\/api\/runs\/[^/]+\/samples\//.test(request.url())) sampleRequests += 1;
  });
  const summaries = Array.from({ length: 37 }, (_, index) => ({
    ...remoteIndex(realRun).runs[0],
    runId: `workspace-run-${String(index).padStart(2, "0")}`,
    sampleId: `sample-${String(index).padStart(2, "0")}`,
    artifactId: `workspace-artifact-${index}`,
    sourceName: index === 31 ? "target-evaluation.explorer.json" : `batch-${index}.explorer.json`
  }));
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        ...remoteIndex(realRun),
        rootName: "large-workspace",
        runs: summaries
      }
    });
  });

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText("large-workspace · 37 ready");
  const list = page.getByLabel("Available workspace and imported runs");
  await expect(list.locator(":scope > div")).toHaveCount(8);
  await expect(page.getByLabel("Run browser window")).toContainText("1-8 of 37");

  await page.getByLabel("Next run window").click();
  await expect(page.getByLabel("Run browser window")).toContainText("9-16 of 37");
  await expect(list).toContainText("workspace-run-08");
  await expect(list).not.toContainText("workspace-run-00");

  const search = page.getByLabel("Search available runs");
  await search.fill("target-evaluation");
  await expect(page.getByLabel("Run browser window")).toContainText("1-1 of 1");
  await expect(list.locator(":scope > div")).toHaveCount(1);
  await expect(list).toContainText("workspace-run-31");

  await page.getByLabel("Filter runs by source").selectOption("generated");
  await expect(page.getByText("No runs match this filter.")).toBeVisible();
  await page.getByLabel("Filter runs by source").selectOption("remote");
  await expect(list).toContainText("workspace-run-31");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByLabel("Open run library").click();
  const drawer = page.locator(".mobile-library-drawer");
  await expect(drawer.getByLabel("Available workspace and imported runs").locator(":scope > div")).toHaveCount(8);
  const mobileNext = drawer.getByLabel("Next run window");
  await expect(mobileNext).toBeVisible();
  expect((await mobileNext.boundingBox())?.height).toBe(44);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  expect(sampleRequests).toBe(0);
});

test("virtualizes searchable selectors for a thousand-run workspace", async ({ page }) => {
  const selectedRun = {
    ...realRun,
    runId: "virtual-run-1199",
    sampleId: "virtual-sample-1199",
    prompt: "Loaded from the virtual run selector"
  };
  const summaries = Array.from({ length: 1_200 }, (_, index) => ({
    ...remoteIndex(realRun).runs[0],
    runId: `virtual-run-${String(index).padStart(4, "0")}`,
    sampleId: `virtual-sample-${String(index).padStart(4, "0")}`,
    artifactId: `virtual-artifact-${index}`,
    sourceName: `virtual-batch-${index}.explorer.json`
  }));
  let sampleRequests = 0;
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        ...remoteIndex(realRun),
        rootName: "thousand-run-workspace",
        runs: summaries
      }
    });
  });
  await page.route(
    /\/api\/runs\/virtual-run-1199\/samples\/virtual-sample-1199$/,
    async (route) => {
      sampleRequests += 1;
      await route.fulfill({ json: selectedRun });
    }
  );

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText(
    "thousand-run-workspace · 1200 ready"
  );
  const selector = page.getByRole("combobox", { name: "Run and sample selector", exact: true });
  await expect(selector).toHaveAttribute("role", "combobox");
  await expect(selector).toHaveAttribute("aria-expanded", "false");
  expect(await page.locator("option").count()).toBeLessThan(50);

  await selector.focus();
  await expect(selector).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByRole("listbox", { name: "Run and sample selector results", exact: true }).getByRole("option")).toHaveCount(8);
  const accessibility = await new AxeBuilder({ page })
    .include(".run-library-panel")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await selector.fill("virtual-run-1199");
  const results = page.getByRole("listbox", { name: "Run and sample selector results", exact: true });
  await expect(results.getByRole("option")).toHaveCount(1);
  await expect(results).toContainText("virtual-sample-1199");
  await selector.press("ArrowDown");
  await selector.press("Enter");

  await expect(page.getByLabel("Prompt runner text")).toHaveValue(
    "Loaded from the virtual run selector"
  );
  const quickSelector = page.getByRole("combobox", { name: "Quick run selector", exact: true });
  await expect(quickSelector).toHaveValue(
    "virtual-run-1199 / virtual-sample-1199"
  );
  await quickSelector.focus();
  const quickResults = page.getByRole("listbox", { name: "Quick run selector results", exact: true });
  await expect(quickResults.getByRole("option")).toHaveCount(8);
  expect((await quickResults.boundingBox())?.width).toBeLessThanOrEqual(360);
  await quickSelector.press("Escape");
  await expect(quickSelector).toHaveAttribute("aria-expanded", "false");
  await page.setViewportSize({ width: 390, height: 844 });
  await quickSelector.click();
  await expect(quickSelector).toHaveAttribute("aria-expanded", "true");
  const mobileResultsBox = await quickResults.boundingBox();
  expect(mobileResultsBox).not.toBeNull();
  expect(mobileResultsBox!.x).toBeGreaterThanOrEqual(0);
  expect(mobileResultsBox!.x + mobileResultsBox!.width).toBeLessThanOrEqual(390);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await quickSelector.press("Escape");
  expect(sampleRequests).toBe(1);
});

test("imports, replays, and exports a cross-run analysis session", async ({ page }) => {
  const remoteRun = {
    ...realRun,
    runId: "session-replay-run",
    sampleId: "session-replay-sample",
    prompt: "Session replay target prompt"
  };
  let sampleRequests = 0;
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({ json: remoteIndex(remoteRun, "session-replay.explorer.json") });
  });
  await page.route(
    /\/api\/runs\/session-replay-run\/samples\/session-replay-sample$/,
    async (route) => {
      sampleRequests += 1;
      await route.fulfill({ json: remoteRun });
    }
  );
  const session = {
    kind: "safelens-explorer-session",
    schemaVersion: "1.0",
    exportedAt: "2026-07-13T18:00:00.000Z",
    workspace: {
      runId: remoteRun.runId,
      sampleId: remoteRun.sampleId,
      modelName: remoteRun.modelName,
      modelSource: remoteRun.modelSource,
      sourceName: "session-replay.explorer.json",
      artifactId: "fixture-artifact"
    },
    selection: {
      view: "attention",
      tokenIndex: 10,
      sourceTokenIndex: 1,
      targetTokenIndex: 10,
      tokenRange: [8, 12],
      layer: 1,
      headId: "L1H0",
      neuronId: "L1N0",
      trackName: "residual_direction",
      metric: "attention_probability",
      normalization: "raw"
    },
    pinnedItems: [],
    timeline: {
      mode: "word",
      metric: "residual",
      query: "jail"
    },
    matrices: {
      attention: {
        size: 63,
        mode: "pan",
        axesPinned: false,
        fitMode: "manual"
      }
    },
    filters: { evidence: "all" }
  };

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText("test-artifacts · 1 ready");
  const importInput = page.getByLabel("Import Explorer artifact JSON");
  await importInput.setInputFiles({
    name: "invalid-analysis-session.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify({
      ...session,
      selection: { ...session.selection, tokenIndex: "ten" }
    }))
  });
  await expect(page.getByText("Analysis session validation failed")).toBeVisible();
  expect(sampleRequests).toBe(0);

  const legacySession = JSON.parse(JSON.stringify(session));
  delete legacySession.timeline;
  await importInput.setInputFiles({
    name: "legacy-analysis-session.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(legacySession))
  });

  await expect(page.getByLabel("Quick run selector")).toHaveValue(
    "session-replay-run::session-replay-sample"
  );
  await expect(page.getByRole("heading", { name: "Attention pattern" })).toBeVisible();
  await expect(page).toHaveURL(/edge=incoming/);
  await expect(page.getByRole("radiogroup", { name: "Attention edge direction" })
    .getByRole("radio", { name: "Incoming" })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByLabel("Search tokens")).toHaveValue("");
  await expect(page.getByLabel("Token color metric")).toHaveValue("risk");
  await expect(page.getByLabel("Timeline granularity").getByRole("button", { name: "Token" })).toHaveClass(/active/);
  expect(sampleRequests).toBe(1);

  await importInput.setInputFiles({
    name: "analysis-session.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(session))
  });
  await expect(page.getByText("Analysis session restored")).toBeVisible();
  await expect(page).toHaveURL(/view=attention/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page).toHaveURL(/source=1/);
  await expect(page).toHaveURL(/range=8-12/);
  await expect(page.getByLabel("Evidence filter").getByRole("button", { name: "All" })).toHaveClass(/active/);
  await expect(page.getByLabel("Search tokens")).toHaveValue("jail");
  await expect(page.getByLabel("Token color metric")).toHaveValue("residual");
  await expect(page.getByLabel("Timeline granularity").getByRole("button", { name: "Word" })).toHaveClass(/active/);
  await expect(page.getByLabel("Pan attention matrix")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Pin attention matrix axes")).toHaveAttribute("aria-pressed", "false");
  const attentionGrid = page.locator(".attention-pattern-grid");
  await expect(attentionGrid).toHaveCSS("grid-template-columns", /36px/);
  const fitAttention = page.getByLabel("Fit attention matrix to width");
  await fitAttention.click();
  await expect(fitAttention).toHaveAttribute("aria-pressed", "true");
  const desktopColumns = await attentionGrid.evaluate(
    (element) => getComputedStyle(element).gridTemplateColumns
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => attentionGrid.evaluate(
    (element) => getComputedStyle(element).gridTemplateColumns
  )).not.toBe(desktopColumns);
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(0\)/);
  expect(sampleRequests).toBe(1);

  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const exported = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(exported.kind).toBe("safelens-explorer-session");
  expect(exported.workspace).toMatchObject({
    runId: "session-replay-run",
    sampleId: "session-replay-sample"
  });
  expect(exported.selection).toMatchObject({
    view: "attention",
    tokenIndex: 10,
    sourceTokenIndex: 1,
    layer: 1,
    attentionEdgeMode: "incoming",
    metric: "attention_probability",
    normalization: "raw"
  });
  expect(exported.selection.tokenRange).toEqual([8, 12]);
  expect(exported.timeline).toEqual({
    mode: "word",
    metric: "residual",
    query: "jail"
  });
  expect(exported.matrices.attention).toMatchObject({
    mode: "pan",
    axesPinned: false,
    fitMode: "fit"
  });
  expect(exported.filters).toEqual({ evidence: "all" });
});

test("hydrates chunk-v1 views and loads the full sample for experiments or matrix pins", async ({ page }, testInfo) => {
  const chunkRun = {
    ...realRun,
    runId: "chunk-hydration-run",
    sampleId: "chunk-hydration-sample",
    prompt: "Metadata-first chunk hydration prompt"
  };
  const index = remoteIndex(chunkRun, "chunk-hydration.explorer.json");
  let fullSampleRequests = 0;
  let nlaRequests = 0;
  const requestedComponents: string[] = [];
  let releaseAttention: (() => void) | undefined;
  const attentionGate = new Promise<void>((resolve) => { releaseAttention = resolve; });
  let releaseFullSample: (() => void) | undefined;
  const fullSampleGate = new Promise<void>((resolve) => { releaseFullSample = resolve; });
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        ...index,
        runs: index.runs.map((summary) => ({
          ...summary,
          chunkProtocol: "safelens-chunks-v1"
        }))
      }
    });
  });
  await page.route(
    /\/api\/runs\/chunk-hydration-run\/samples\/chunk-hydration-sample\/metadata$/,
    async (route) => {
      await route.fulfill({
        headers: { ETag: '"metadata-v1"' },
        json: chunkMetadata(chunkRun)
      });
    }
  );
  await page.route(
    /\/api\/runs\/chunk-hydration-run\/samples\/chunk-hydration-sample\/chunks\/[^?]+/,
    async (route) => {
      const url = new URL(route.request().url());
      const component = url.pathname.split("/").at(-1)!;
      requestedComponents.push(component);
      if (component === "attentionHeads" || component === "attentionCells") {
        await attentionGate;
      }
      if (component === "nla") {
        nlaRequests += 1;
        if (nlaRequests === 1) {
          await route.fulfill({ status: 500, json: { detail: "temporary NLA chunk failure" } });
          return;
        }
      }
      await route.fulfill({
        headers: { ETag: `"${component}-v1"` },
        json: chunkResponse(chunkRun, component, url.searchParams)
      }).catch(() => undefined);
    }
  );
  await page.route(
    /\/api\/runs\/chunk-hydration-run\/samples\/chunk-hydration-sample$/,
    async (route) => {
      fullSampleRequests += 1;
      await fullSampleGate;
      await route.fulfill({ json: chunkRun });
    }
  );

  await page.goto(
    "/?run=chunk-hydration-run&sample=chunk-hydration-sample&view=mlp&layer=1&token=10&metric=mlp_signed_activation"
  );
  await expect(page.getByLabel("Run and sample selector")).toHaveValue(
    "chunk-hydration-run::chunk-hydration-sample"
  );
  await expect(page.getByRole("heading", { name: "MLP activation matrix" })).toBeVisible();
  await expect(page.locator(".active-run-card .status-pill")).toContainText("range");
  expect(requestedComponents.sort()).toEqual(["mlpCells", "mlpNeurons", "residualCells"]);
  expect(fullSampleRequests).toBe(0);

  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await expect(page.getByText("Loading Attention data")).toBeVisible();
  const chunkLoadingState = page.locator(".view-chunk-state.loading");
  const chunkSkeleton = chunkLoadingState.locator(".analysis-loading-skeleton");
  await expect(chunkSkeleton).toBeVisible();
  expect((await chunkLoadingState.boundingBox())?.height).toBeGreaterThanOrEqual(320);
  expect((await chunkSkeleton.locator(".analysis-loading-stage").boundingBox())?.height)
    .toBeGreaterThanOrEqual(220);
  const loadingAccessibility = await new AxeBuilder({ page })
    .include(".view-chunk-state.loading")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(loadingAccessibility.violations).toEqual([]);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(chunkSkeleton.locator(".analysis-loading-toolbar span").first())
    .toHaveCSS("animation-name", "none");
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await expect(page.getByLabel("Evidence inspector").locator(".evidence-status")).toHaveText(
    "loading"
  );
  await page.locator(".view-chunk-state").getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByText("Attention loading cancelled")).toBeVisible();
  await expect(page.locator(".view-chunk-state .analysis-loading-skeleton")).toHaveCount(0);
  expect((await page.locator(".view-chunk-state.cancelled").boundingBox())?.height)
    .toBeLessThan(180);
  await expect.poll(async () => page.evaluate(
    () => performance.getEntriesByName("safelens:cancel-feedback").length
  )).toBeGreaterThan(0);
  const cancelFeedbackMs = await page.evaluate(() => {
    const entry = performance.getEntriesByName("safelens:cancel-feedback").at(-1) as PerformanceMark | undefined;
    return (entry?.detail as { latencyMs?: number } | undefined)?.latencyMs ?? Number.POSITIVE_INFINITY;
  });
  expect(cancelFeedbackMs).toBeLessThan(300);
  await expect(page.getByLabel("Evidence inspector").locator(".evidence-status")).toHaveText(
    "cancelled"
  );
  releaseAttention?.();
  await page.locator(".view-chunk-state").getByRole("button", { name: "Retry" }).click();
  await expect(page.getByRole("heading", { name: "Attention pattern" })).toBeVisible();
  expect(requestedComponents).toEqual(expect.arrayContaining(["attentionCells", "attentionHeads"]));
  expect(fullSampleRequests).toBe(0);

  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  await expect(page.getByText("NLA data could not be loaded")).toBeVisible();
  await expect(page.getByLabel("Evidence inspector").locator(".evidence-status")).toHaveText(
    "failed"
  );
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByLabel("NLA results")).toContainText("No NLA artifact yet");
  expect(nlaRequests).toBe(2);
  expect(requestedComponents).toContain("nla");
  expect(fullSampleRequests).toBe(0);

  await page.getByRole("tab", { name: "Patching", exact: true }).click();
  await expect(page.getByText("No causal patch grid in this run")).toBeVisible();
  expect(requestedComponents).toContain("patching");
  expect(fullSampleRequests).toBe(0);

  await page.getByRole("tab", { name: "Intervention", exact: true }).click();
  await expect(page.getByText("No intervention comparison in this run")).toBeVisible();
  expect(requestedComponents).toContain("intervention");
  expect(fullSampleRequests).toBe(0);

  await page.getByRole("tab", { name: "Attribution", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Attribution matrix" })).toBeVisible();
  await expect(page.getByText("Full Run required for experiments")).toBeVisible();
  expect(requestedComponents).toEqual(expect.arrayContaining([
    "attributionMethods", "attributionTracks"
  ]));
  expect(fullSampleRequests).toBe(0);
  await expect(page.getByLabel("NLA cosine metric")).toContainText("n/a");
  const desktopPath = testInfo.outputPath("chunk-hydration-desktop.png");
  await page.locator(".analysis-grid").screenshot({ path: desktopPath });
  await testInfo.attach("chunk-hydration-desktop", { path: desktopPath, contentType: "image/png" });

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText("Full Run required for experiments")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const mobilePath = testInfo.outputPath("chunk-hydration-mobile.png");
  await page.screenshot({ path: mobilePath, fullPage: true });
  await testInfo.attach("chunk-hydration-mobile", { path: mobilePath, contentType: "image/png" });

  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Attention pattern" })).toBeVisible();
  expect(fullSampleRequests).toBe(0);
  await page.getByRole("radiogroup", { name: "Attention head display" })
    .getByRole("radio", { name: "Rollout" })
    .click();
  await expect(page.getByText("Loading complete attention for rollout")).toBeVisible();
  await expect.poll(() => fullSampleRequests).toBe(1);
  releaseFullSample?.();
  await expect(page.getByRole("radio", { name: "Rollout" })).toHaveAttribute("aria-checked", "true");
  await expect(page.locator(".active-run-card .status-pill")).not.toContainText("range");
  const mobileEvidenceActions = page.getByRole("region", { name: "Current evidence actions" });
  await mobileEvidenceActions.getByLabel("Pin current evidence").click();
  expect(fullSampleRequests).toBe(1);
  await expect(mobileEvidenceActions.getByLabel(/^Open evidence comparison/)).toHaveAttribute("aria-label", /\(4\)/);

  await page.getByRole("tab", { name: "Attribution", exact: true }).click();

  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export current Explorer artifact").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const exported = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(parseExplorerArtifact(exported).success).toBe(true);
  await expect(page.getByRole("heading", { name: "Integrated Gradients job" })).toBeVisible();
  await expect(page.locator(".active-run-card .status-pill")).not.toContainText("range");
  expect(fullSampleRequests).toBe(1);
});

test("prefetches one adjacent token block without duplicate chunk requests", async ({ page }) => {
  const prefetchRun = {
    ...expandedTimelineRun(600),
    runId: "chunk-prefetch-run",
    sampleId: "chunk-prefetch-sample"
  };
  const index = remoteIndex(prefetchRun, "chunk-prefetch.explorer.json");
  const requests: string[] = [];
  let fullSampleRequests = 0;
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        ...index,
        runs: index.runs.map((summary) => ({
          ...summary,
          chunkProtocol: "safelens-chunks-v1"
        }))
      }
    });
  });
  await page.route(
    /\/api\/runs\/chunk-prefetch-run\/samples\/chunk-prefetch-sample\/metadata$/,
    async (route) => route.fulfill({
      headers: { ETag: '"prefetch-metadata-v1"' },
      json: chunkMetadata(prefetchRun)
    })
  );
  await page.route(
    /\/api\/runs\/chunk-prefetch-run\/samples\/chunk-prefetch-sample\/chunks\/[^?]+/,
    async (route) => {
      const url = new URL(route.request().url());
      const component = url.pathname.split("/").at(-1)!;
      requests.push(`${component}:${url.searchParams.get("tokenStart")}-${url.searchParams.get("tokenEnd")}`);
      await route.fulfill({
        headers: { ETag: `"${component}-${url.searchParams.get("tokenStart")}"` },
        json: chunkResponse(prefetchRun, component, url.searchParams)
      });
    }
  );
  await page.route(
    /\/api\/runs\/chunk-prefetch-run\/samples\/chunk-prefetch-sample$/,
    async (route) => {
      fullSampleRequests += 1;
      await route.fulfill({ json: prefetchRun });
    }
  );

  await page.goto(
    "/?run=chunk-prefetch-run&sample=chunk-prefetch-sample&view=residual&layer=1&token=10"
  );
  await expect(page.getByLabel("Matrix controls")).toBeVisible();
  await expect.poll(() => requests.filter((item) => item.endsWith("512-600")).sort()).toEqual([
    "logitLens:512-600",
    "residualCells:512-600"
  ]);
  expect(requests.filter((item) => item === "residualCells:0-512")).toHaveLength(1);
  expect(requests.filter((item) => item === "logitLens:0-512")).toHaveLength(1);
  expect(fullSampleRequests).toBe(0);
});

test("cancels workspace discovery without disabling local analysis", async ({ page }) => {
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 2_000));
    await route.fulfill({ json: remoteIndex(realRun) }).catch(() => undefined);
  });

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toHaveAttribute("aria-busy", "true");
  await expect(page.getByLabel("Workspace API status")).toContainText("Connecting to workspace");
  await page.getByLabel("Cancel workspace discovery").click();
  await expect(page.getByLabel("Workspace API status")).toContainText(
    "Workspace discovery cancelled"
  );
  await expect(page.getByRole("heading", { name: "Token Timeline" })).toBeVisible();
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(1);
});

test("reports an empty workspace as an actionable empty state", async ({ page }) => {
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "empty-artifacts",
        runs: [],
        diagnostics: []
      }
    });
  });

  await page.goto("/explorer");
  const status = page.getByLabel("Workspace API status");
  await expect(status).toContainText("empty-artifacts · no runs found");
  await expect(status).toHaveAttribute("aria-busy", "false");
  await expect(page.getByLabel("Retry workspace discovery")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Token Timeline" })).toBeVisible();
});

test("keeps the newest workspace response when refresh requests overlap", async ({ page }) => {
  const staleRun = { ...realRun, runId: "stale-run", sampleId: "stale-sample" };
  const freshRun = { ...realRun, runId: "fresh-run", sampleId: "fresh-sample" };
  let phase: "initial" | "stale" | "fresh" = "initial";
  let releaseStale: (() => void) | undefined;
  const staleGate = new Promise<void>((resolve) => { releaseStale = resolve; });

  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    if (phase === "initial") {
      await route.fulfill({
        json: {
          schemaVersion: "1.0",
          source: "local-workspace",
          rootName: "race-test",
          runs: [],
          diagnostics: []
        }
      });
      return;
    }
    if (phase === "stale") {
      await staleGate;
      await route.fulfill({ json: remoteIndex(staleRun, "stale.explorer.json") }).catch(() => undefined);
      return;
    }
    await route.fulfill({ json: remoteIndex(freshRun, "fresh.explorer.json") });
  });
  await page.route(/\/api\/runs\/fresh-run\/samples\/fresh-sample$/, async (route) => {
    await route.fulfill({ json: freshRun });
  });

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText("race-test · no runs found");
  phase = "stale";
  await page.getByLabel("Retry workspace discovery").click();
  await expect(page.getByLabel("Workspace API status")).toHaveAttribute("aria-busy", "true");
  await expect(page.getByLabel("Workspace API status")).toContainText("Connecting to workspace");
  await page.getByLabel("Cancel workspace discovery").click();
  await expect(page.getByLabel("Workspace API status")).toContainText("Workspace discovery cancelled");
  phase = "fresh";
  await page.getByLabel("Retry workspace discovery").click();
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);
  await expect(page.getByLabel("Run and sample selector").locator("option").nth(1)).toContainText(
    "fresh-run / fresh-sample"
  );

  releaseStale?.();
  await page.waitForTimeout(100);
  await expect(page.getByLabel("Run and sample selector").locator("option").nth(1)).toContainText(
    "fresh-run / fresh-sample"
  );
});

test("runs a prompt job over SSE and adds validated output to the Run Library", async ({ page }) => {
  const generatedRun = {
    ...realRun,
    runId: "prompt-generated-run",
    sampleId: "seed-23",
    prompt: "User: Analyze a generated safety response.\nAssistant:",
    metadata: {
      ...realRun.metadata,
      promptRunner: {
        jobVersion: "1.0",
        template: "chat",
        model: "sshleifer/tiny-gpt2",
        seed: 23,
        maxNewTokens: 12,
        temperature: 0.4
      }
    }
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/prompt", async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: promptJob("idle") });
  });
  await page.route("**/api/jobs/prompt-job-12345678/events", async (route) => {
    const body = `event: job\ndata: ${JSON.stringify(promptJob("ready", generatedRun))}\n\n`;
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: { "Cache-Control": "no-cache" },
      body
    });
  });

  await page.goto("/explorer");
  await page.getByLabel("Prompt runner text").fill("Analyze a generated safety response.");
  await page.getByLabel("Prompt template").selectOption("chat");
  await page.getByLabel("Generation seed").fill("23");
  await page.getByLabel("Maximum new tokens").fill("12");
  await page.getByLabel("Generation temperature").fill("0.4");
  await page.getByRole("button", { name: "Run analysis" }).click();

  await expect(page.getByLabel("Quick run selector")).toHaveValue("prompt-generated-run::seed-23");
  await expect(page.locator(".active-run-card")).toContainText("generated");
  await expect(page.getByText("Prompt analysis added to the Run Library")).toBeVisible();
  await expect(page.locator(".prompt-run-provenance")).toContainText("Current generated run");
  await expect(page.locator(".prompt-run-provenance")).toContainText("Seed23");
  await expect(page).toHaveURL(/run=prompt-generated-run/);
  await expect(page).toHaveURL(/sample=seed-23/);
  const removeGenerated = page.getByLabel(
    "Review removal of browser artifact prompt-generated-run seed-23"
  );
  await removeGenerated.click();
  const removalDialog = page.getByRole("dialog", { name: "Remove browser artifact?" });
  await expect(removalDialog).toContainText("Generated result");
  await expect(removalDialog).toContainText("prompt-generated-run");
  await expect(removalDialog.getByRole("button", { name: "Cancel" })).toBeFocused();
  await removalDialog.getByRole("button", { name: "Cancel" }).click();
  await expect(removalDialog).toBeHidden();
  await expect(removeGenerated).toBeFocused();
  expect(submitted).toEqual({
    prompt: "Analyze a generated safety response.",
    template: "chat",
    model: "sshleifer/tiny-gpt2",
    seed: 23,
    maxNewTokens: 12,
    temperature: 0.4,
    messages: []
  });
});

test("cancels a prompt job without adding a generated run", async ({ page }) => {
  const startedAt = new Date().toISOString();
  await page.route("**/api/jobs/prompt", async (route) => {
    await route.fulfill({
      status: 202,
      json: { ...promptJob("loading"), createdAt: startedAt, updatedAt: startedAt }
    });
  });
  await page.route("**/api/jobs/prompt-job-12345678/events", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(promptJob("loading"))}\n\n`
    }).catch(() => undefined);
  });
  await page.route("**/api/jobs/prompt-job-12345678", async (route) => {
    await route.fulfill({
      json: {
        ...promptJob("cancelled"),
        createdAt: startedAt,
        updatedAt: new Date(Date.parse(startedAt) + 1_000).toISOString()
      }
    });
  });

  await page.goto("/explorer");
  await expect(page.getByLabel("Workspace API status")).toContainText(
    /ready|no runs found|Workspace data error|Workspace API error/
  );
  const originalOptions = await page.getByLabel("Quick run selector").locator("option").count();
  await page.getByRole("button", { name: "Run analysis" }).click();
  await expect(page.getByLabel("Prompt job status")).toContainText("Prompt job running");
  const progress = page.getByLabel("Prompt job progress", { exact: true });
  await expect(progress).toContainText("StageQueuedProgress45%Elapsed");
  await expect(page.getByRole("progressbar", { name: "Prompt job progress completion" }))
    .toHaveAttribute("aria-valuetext", /45% complete; Queued; elapsed/);
  await expect(progress.locator("time")).toHaveText(/^[01]s$/);
  await page.waitForTimeout(1_050);
  await expect(progress.locator("time")).toHaveText(/^[12]s$/);
  await page.locator(".prompt-cancel-button").click();
  await expect(page.getByLabel("Prompt job status")).toContainText("Prompt job cancelled");
  await expect(progress).toContainText("StageCancelledProgress45%Elapsed1s");
  await page.waitForTimeout(1_050);
  await expect(progress.locator("time")).toHaveText("1s");
  await expect(page.getByLabel("Quick run selector").locator("option")).toHaveCount(originalOptions);
});

test("classifies submission failures, copies safe diagnostics, and retries without reload", async ({
  page,
  context
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  let attempts = 0;
  await page.route("**/api/jobs/prompt", async (route) => {
    attempts += 1;
    if (attempts === 1) {
      await route.fulfill({
        status: 422,
        json: {
          detail: {
            code: "model_not_allowed",
            message: "The selected model is not enabled for local jobs."
          }
        }
      });
      return;
    }
    if (attempts === 2) {
      await route.abort("failed");
      return;
    }
    await route.fulfill({ status: 202, json: promptJob("loading") });
  });
  await page.route("**/api/jobs/prompt-job-12345678/events", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(promptJob("loading"))}\n\n`
    }).catch(() => undefined);
  });
  await page.route("**/api/jobs/prompt-job-12345678", async (route) => {
    await route.fulfill({ json: promptJob("cancelled") });
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explorer");
  await page.getByLabel("Open run library").click();
  const drawer = page.locator(".mobile-library-drawer");
  const runner = drawer.locator(".prompt-runner-panel");
  const timeOrigin = await page.evaluate(() => performance.timeOrigin);
  await runner.getByRole("button", { name: "Run analysis" }).click();
  await expect(runner.getByLabel("Prompt job status")).toContainText("Job inputs are incompatible");
  const failure = runner.locator(".job-failure-details");
  await expect(failure.locator("summary")).toContainText("Compatibility");
  await failure.locator("summary").click();
  await expect(failure).toContainText("model_not_allowed");
  await expect(failure).toContainText("HTTP422");
  await expect(failure).toContainText("Choose a compatible model");
  await failure.getByRole("button", { name: "Copy diagnostics" }).click();
  const diagnostics = JSON.parse(await page.evaluate(() => navigator.clipboard.readText()));
  expect(diagnostics).toMatchObject({
    schemaVersion: "1.0",
    kind: "safelens-job-error",
    category: "compatibility",
    phase: "submission",
    code: "prompt_submit_error",
    serverCode: "model_not_allowed",
    httpStatus: 422,
    job: null,
    context: "Prompt job"
  });
  expect(diagnostics).not.toHaveProperty("request");
  expect(JSON.stringify(diagnostics)).not.toContain("Analyze a generated safety response");

  await runner.getByRole("button", { name: "Retry analysis" }).click();
  await expect(runner.getByLabel("Prompt job status")).toContainText("Workspace connection interrupted");
  await expect(failure.locator("summary")).toContainText("Network");
  await failure.locator("summary").click();
  await expect(failure.getByRole("button", { name: "Copy diagnostics" })).toBeVisible();

  await expect.poll(() => page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth
  }))).toEqual({ viewport: 390, document: 390 });
  const retryBox = await runner.getByRole("button", { name: "Retry analysis" }).boundingBox();
  expect(retryBox?.width).toBeGreaterThanOrEqual(44);
  expect(retryBox?.height).toBeGreaterThanOrEqual(44);
  const copyBox = await failure.getByRole("button", { name: "Copy diagnostics" }).boundingBox();
  expect(copyBox?.height).toBeGreaterThanOrEqual(44);
  const axeResults = await new AxeBuilder({ page })
    .include(".mobile-library-drawer .prompt-runner-panel")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);

  await runner.getByRole("button", { name: "Retry analysis" }).click();
  await expect(runner.getByLabel("Prompt job status")).toContainText("Prompt job running");
  expect(attempts).toBe(3);
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(timeOrigin);
  await runner.locator(".prompt-cancel-button").click();
  await expect(runner.getByLabel("Prompt job status")).toContainText("Prompt job cancelled");
});

test("reports invalid progress streams as protocol failures without duplicating a running job", async ({ page }) => {
  await page.route("**/api/jobs/prompt", async (route) => {
    await route.fulfill({ status: 202, json: promptJob("loading") });
  });
  await page.route("**/api/jobs/prompt-job-12345678/events", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: "event: job\ndata: not-json\n\n"
    });
  });
  await page.route("**/api/jobs/prompt-job-12345678", async (route) => {
    await route.fulfill({ json: promptJob("cancelled") });
  });

  await page.goto("/explorer");
  const sourceRun = await page.getByLabel("Quick run selector").inputValue();
  await page.getByRole("button", { name: "Run analysis" }).click();
  await expect(page.getByLabel("Prompt job status")).toContainText("Job response is invalid");
  const failure = page.locator(".prompt-runner-panel .job-failure-details");
  await expect(failure.locator("summary")).toContainText("Protocol");
  await failure.locator("summary").click();
  await expect(failure).toContainText("prompt_stream_invalid_json");
  await expect(failure).toContainText("Retry once");
  await expect(page.getByRole("button", { name: "Retry analysis" })).toHaveCount(0);
  await expect(page.locator(".prompt-cancel-button")).toBeVisible();
  await page.locator(".prompt-cancel-button").click();
  await expect(page.getByLabel("Prompt job status")).toContainText("Prompt job cancelled");
  await expect(page.getByLabel("Quick run selector")).toHaveValue(sourceRun);
});

test("classifies worker failures as computation errors and retries a new generation", async ({ page }) => {
  let submissions = 0;
  let streams = 0;
  await page.route("**/api/jobs/prompt", async (route) => {
    submissions += 1;
    await route.fulfill({ status: 202, json: promptJob("loading") });
  });
  await page.route("**/api/jobs/prompt-job-12345678/events", async (route) => {
    streams += 1;
    if (streams === 1) {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: `event: job\ndata: ${JSON.stringify({
          ...promptJob("error"),
          stage: "failed",
          progress: 45,
          detail: "The isolated model process failed.",
          error: "CUDA allocation failed in the local worker."
        })}\n\n`
      });
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(promptJob("loading"))}\n\n`
    }).catch(() => undefined);
  });
  await page.route("**/api/jobs/prompt-job-12345678", async (route) => {
    await route.fulfill({ json: promptJob("cancelled") });
  });

  await page.goto("/explorer");
  const sourceRun = await page.getByLabel("Quick run selector").inputValue();
  await page.getByRole("button", { name: "Run analysis" }).click();
  await expect(page.getByLabel("Prompt job status")).toContainText("Job computation failed");
  const failure = page.locator(".prompt-runner-panel .job-failure-details");
  await expect(failure.locator("summary")).toContainText("Computation");
  await failure.locator("summary").click();
  await expect(failure).toContainText("prompt-run_execution_error");
  await expect(failure).toContainText("worker stopped without replacing the source Run");
  await expect(page.getByLabel("Prompt job progress", { exact: true })).toContainText("FailedProgress45%");
  await expect(page.getByLabel("Quick run selector")).toHaveValue(sourceRun);

  await page.getByRole("button", { name: "Retry analysis" }).click();
  await expect(page.getByLabel("Prompt job status")).toContainText("Prompt job running");
  expect(submissions).toBe(2);
  await page.locator(".prompt-cancel-button").click();
  await expect(page.getByLabel("Prompt job status")).toContainText("Prompt job cancelled");
});

test("runs Captum attribution and opens the causal method in a derived run", async ({ page }) => {
  const values = realRun.tokens.map((_, index) => index % 2 === 0 ? 0.5 : -0.25);
  const derivedRun = {
    ...realRun,
    runId: "real-run-ig-derived",
    attributionMethods: realRun.attributionMethods.map((method) => method.id === "integrated_gradients"
      ? {
          ...method,
          available: true,
          unavailableReason: undefined,
          normalization: "raw embedding attribution with max-absolute stored display values",
          rows: [{
            layer: -1,
            label: "Input",
            values,
            sourceKey: "captum.layer_integrated_gradients[target=16046,response_index=1]"
          }]
        }
      : method),
    attributionTracks: [
      ...realRun.attributionTracks,
      { name: "Integrated Gradients", values }
    ],
    metricProvenance: {
      ...realRun.metricProvenance,
      integratedGradients: {
        label: "Integrated Gradients",
        method: "Captum LayerIntegratedGradients 0.9.0",
        semantics: "Signed contribution of preceding input tokens to one response-token logit.",
        normalization: "raw scores retained in job metadata; matrix values max-absolute normalized",
        kind: "causal" as const
      }
    },
    metadata: {
      ...realRun.metadata,
      parentRun: { runId: realRun.runId, sampleId: realRun.sampleId },
      attributionJobs: [{
        objective: "response_token_logit",
        targetTokenId: 16046,
        targetTokenText: " stairs",
        targetResponseIndex: 1,
        baseline: "pad_token",
        nSteps: 16,
        convergenceDelta: 0.00125,
        rawValues: values.map((value) => value / 10)
      }]
    }
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/attribution", async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: attributionJob("idle", realRun) });
  });
  await page.route("**/api/jobs/attribution-job-87654321/events", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(attributionJob("ready", realRun, derivedRun))}\n\n`
    });
  });

  await page.goto("/explorer?view=attribution&track=integrated_gradients");
  await page.getByLabel("Attribution response text").fill(" stairs stairs");
  await page.getByLabel("Target response token index").fill("1");
  await page.getByLabel("Attribution baseline").selectOption("pad_token");
  await page.getByLabel("Attribution integration steps").selectOption("16");
  await page.getByRole("button", { name: "Run Integrated Gradients" }).click();

  await expect(page.getByLabel("Quick run selector")).toHaveValue("real-run-ig-derived::real-forward-cache-001");
  await expect(page.getByRole("tab", { name: "Attribution", exact: true })).toHaveClass(/active/);
  await expect(page.locator(".attribution-matrix-toolbar select")).toHaveValue("integrated_gradients");
  await expect(page.getByRole("region", { name: "Evidence inspector" })).toContainText("available");
  await expect(page.getByRole("region", { name: "Evidence inspector" })).toContainText("causal");
  await expect(page.getByText("Attribution added to the Run Library")).toBeVisible();
  const accounting = page.getByLabel("Attribution accounting");
  await expect(accounting).toContainText("raw job values · 20 input positions");
  await expect(accounting).toContainText("+0.5000positive sum");
  await expect(accounting).toContainText("-0.2500negative sum");
  await expect(accounting).toContainText("+0.2500net sum");
  await expect(accounting).toContainText("66.7%sign cancellation");
  await expect(accounting).toContainText("stairsresponse[1]");
  await expect(accounting).toContainText("pad_tokenbaseline");
  await expect(accounting).toContainText("16integration steps");
  await expect(accounting).toContainText("1.250e-3convergence delta");
  await expect(page.getByLabel("Attribution methods").getByRole("button")
    .filter({ hasText: "Integrated Gradients" })).toContainText("+0.5000");
  expect(submitted?.response).toBe(" stairs stairs");
  expect(submitted?.targetResponseIndex).toBe(1);
  expect(submitted?.baseline).toBe("pad_token");
  expect(submitted?.nSteps).toBe(16);
  expect((submitted?.run as { runId?: string }).runId).toBe(realRun.runId);
});

test("cancels Captum attribution without replacing the source run", async ({ page }) => {
  await page.route("**/api/jobs/attribution", async (route) => {
    await route.fulfill({ status: 202, json: attributionJob("loading", realRun) });
  });
  await page.route("**/api/jobs/attribution-job-87654321/events", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(attributionJob("loading", realRun))}\n\n`
    }).catch(() => undefined);
  });
  await page.route("**/api/jobs/attribution-job-87654321", async (route) => {
    await route.fulfill({ json: attributionJob("cancelled", realRun) });
  });

  await page.goto("/explorer?view=attribution&track=integrated_gradients");
  const sourceRun = await page.getByLabel("Quick run selector").inputValue();
  await page.getByRole("button", { name: "Run Integrated Gradients" }).click();
  await expect(page.getByLabel("Attribution job status")).toContainText("Attribution running");
  await expect(page.getByLabel("Attribution job progress", { exact: true })).toContainText("Integrated Gradients");
  await expect(page.getByRole("progressbar", { name: "Attribution job progress completion" }))
    .toHaveAttribute("aria-valuenow", "55");
  await page.locator(".attribution-cancel-button").click();
  await expect(page.getByLabel("Attribution job status")).toContainText("Attribution cancelled");
  await expect(page.getByLabel("Quick run selector")).toHaveValue(sourceRun);
  await expect(page.locator(".attribution-unavailable")).toBeVisible();
});

test("blocks NLA submission when the selected profile is structurally incompatible", async ({ page }) => {
  await page.route("**/api/nla/profiles", async (route) => {
    await route.fulfill({ json: [qwenNlaProfile] });
  });
  await page.route("**/api/nla/preflight", async (route) => {
    await route.fulfill({ json: nlaPreflight(false) });
  });
  let submitted = false;
  await page.route("**/api/jobs/nla", async (route) => {
    submitted = true;
    await route.abort();
  });

  await page.goto("/explorer?view=nla&token=10");
  const preflight = page.getByLabel("NLA job preflight");
  await expect(preflight).toContainText("incompatible");
  await expect(preflight.locator(".failed")).toHaveCount(3);
  const revision = page.getByLabel("NLA checkpoint revision");
  await revision.fill("   ");
  await expect(revision).toHaveAttribute("aria-invalid", "true");
  await expect(revision).toHaveAttribute("aria-describedby", "nla-revision-error");
  await expect(page.getByRole("alert")).toContainText("Checkpoint revision is required");
  await expect(page.getByRole("button", { name: "Run exact NLA" })).toBeDisabled();
  await expect(page.locator(".nla-job-blocked")).toContainText("model requires Qwen");
  expect(submitted).toBe(false);
});

test("blocks activation patching until the corrupted prompt is positionally aligned and changed", async ({ page }) => {
  await page.route("**/api/patching/preflight", async (route) => {
    const request = route.request().postDataJSON() as { corruptedPrompt: string };
    await route.fulfill({ json: patchingPreflight(realRun, request.corruptedPrompt) });
  });
  let submitted = false;
  await page.route("**/api/jobs/patching", async (route) => {
    submitted = true;
    await route.abort();
  });

  await page.goto("/explorer?view=patching&token=10&layer=1");
  await expect(page.getByLabel("Patching preflight")).toContainText("blocked");
  await expect(page.getByLabel("Patching preflight")).toContainText("prompts are identical");
  const corruptedPrompt = page.getByLabel("Corrupted patching prompt");
  await expect(corruptedPrompt).toHaveAttribute("aria-invalid", "true");
  await expect(corruptedPrompt).toHaveAttribute("aria-describedby", "patching-preflight-reason");
  await expect(page.getByRole("button", { name: /Run .* patches/ })).toBeDisabled();
  expect(submitted).toBe(false);
});

test("runs activation patching and opens exact causal evidence in a derived run", async ({ page }) => {
  const target = realRun.logitLens[0];
  const derivedRun = {
    ...realRun,
    runId: "real-run-patch-derived",
    patching: {
      cleanPrompt: realRun.prompt,
      corruptedPrompt: "Corrupted aligned prompt",
      component: "resid_post" as const,
      targetTokenId: target.targetTokenId,
      targetTokenText: target.targetTokenText,
      cleanScore: 4.5,
      corruptedScore: 2.5,
      denominator: 2,
      layers: [1],
      positions: [10],
      corruptedTokens: patchingPreflight(realRun, "Corrupted aligned prompt").corruptedTokens,
      cells: [{
        layer: 1,
        tokenIndex: 10,
        patchedScore: 3.5,
        causalEffect: 1,
        recoveryPercentage: 50,
        sourceKey: "layer_1.resid_post"
      }],
      sourceRun: { runId: realRun.runId, sampleId: realRun.sampleId },
      sourceKey: `activation_patching.resid_post[target=${target.targetTokenId}]`
    },
    metricProvenance: {
      ...realRun.metricProvenance,
      patchingCausalEffect: {
        label: "Causal effect",
        method: "Clean activation replacement",
        semantics: "Patched logit minus corrupted logit.",
        normalization: "none",
        kind: "causal" as const
      },
      patchingRecovery: {
        label: "Recovery",
        method: "Activation patching recovery ratio",
        semantics: "Recovered clean-corrupted target-logit difference.",
        normalization: "percentage",
        kind: "causal" as const
      },
      patchingPatchedScore: {
        label: "Patched score",
        method: "Activation patching forward pass",
        semantics: "Raw target-token logit after replacement.",
        normalization: "none",
        kind: "causal" as const
      }
    }
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/patching/preflight", async (route) => {
    const request = route.request().postDataJSON() as { corruptedPrompt: string };
    await route.fulfill({ json: patchingPreflight(realRun, request.corruptedPrompt) });
  });
  await page.route("**/api/jobs/patching", async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: patchingJob("idle", realRun) });
  });
  await page.route("**/api/jobs/patching-job-13572468/events", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(patchingJob("ready", realRun, derivedRun))}\n\n`
    });
  });

  await page.goto("/explorer?view=patching&token=10&layer=1");
  await page.getByLabel("Corrupted patching prompt").fill("Corrupted aligned prompt");
  await expect(page.getByLabel("Patching preflight")).toContainText("ready");
  await page.getByRole("button", { name: /Run 1 patches/ }).click();

  await expect(page.getByLabel("Quick run selector")).toHaveValue("real-run-patch-derived::real-forward-cache-001");
  await expect(page.getByRole("tab", { name: "Patching", exact: true })).toHaveClass(/active/);
  await expect(page.getByText("Activation patching added to the Run Library")).toBeVisible();
  await expect(page.getByLabel("Layer by token activation patching matrix")).toBeVisible();
  const controls = page.getByLabel("Patching matrix controls");
  const grid = page.getByLabel("Layer by token activation patching matrix");
  const gridRow = grid.locator(".patching-grid-row").first();
  const causalCell = grid.locator('[data-layer="1"][data-token="10"]');
  await expect(controls.getByLabel("Select patching matrix cells")).toHaveAttribute("aria-pressed", "true");
  await expect(controls.getByLabel("Pin patching matrix axes")).toHaveAttribute("aria-pressed", "true");
  await expect(causalCell).toHaveAttribute(
    "aria-keyshortcuts",
    "ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Control+Enter Meta+Enter Space"
  );
  const patchSelectionUrl = page.url();
  await causalCell.click({ modifiers: ["Shift"] });
  expect(page.url()).toBe(patchSelectionUrl);
  await expect(page.getByLabel("Patching matrix selection summary")).toContainText("L1 · T10");
  await expect(page.getByLabel("Patching matrix selection summary").locator("span").nth(2))
    .not.toContainText("n/a");
  await expect(causalCell).toHaveClass(/comparison/);
  await causalCell.click({ modifiers: ["Control"] });
  expect(page.url()).toBe(patchSelectionUrl);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; layer?: number }) =>
      pin.view === "patching" && pin.tokenIndex === 10 && pin.layer === 1
    );
  })).toBe(true);
  await causalCell.focus();
  await expect(page.locator(".patching-cell-details")).toContainText("layer_1.resid_post");
  await page.keyboard.press("Space");
  await page.keyboard.press("Space");
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(4\)/);

  const patchRangeStart = grid.locator('[role="columnheader"][data-range-token="8"]');
  const patchRangeEnd = grid.locator('[role="columnheader"][data-range-token="10"]');
  await patchRangeStart.scrollIntoViewIfNeeded();
  const patchRangeStartBox = await patchRangeStart.boundingBox();
  const patchRangeEndBox = await patchRangeEnd.boundingBox();
  expect(patchRangeStartBox).not.toBeNull();
  expect(patchRangeEndBox).not.toBeNull();
  await page.mouse.move(
    patchRangeStartBox!.x + patchRangeStartBox!.width / 2,
    patchRangeStartBox!.y + patchRangeStartBox!.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    patchRangeEndBox!.x + patchRangeEndBox!.width / 2,
    patchRangeEndBox!.y + patchRangeEndBox!.height / 2,
    { steps: 8 }
  );
  await page.mouse.up();
  await expect(page.getByLabel("Token range summary")).toContainText("8–10");
  await expect(page).toHaveURL(/range=8-10/);
  await expect(grid.locator("[data-range-token].in-range")).not.toHaveCount(0);
  await page.getByLabel("Clear token range").click();
  await expect(page).not.toHaveURL(/range=/);

  await controls.getByLabel("Zoom in patching matrix").click();
  await expect(gridRow).toHaveCSS("grid-template-columns", /54px 54px/);
  await controls.getByLabel("Pan patching matrix").click();
  await controls.getByLabel("Pin patching matrix axes").click();
  await expect(controls.getByLabel("Pan patching matrix")).toHaveAttribute("aria-pressed", "true");
  await expect(controls.getByLabel("Pin patching matrix axes")).toHaveAttribute("aria-pressed", "false");
  const patchingViewport = page.locator(".patching-grid-scroll");
  const viewportSize = await patchingViewport.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth
  }));
  expect(viewportSize.scrollWidth).toBeGreaterThan(viewportSize.clientWidth);
  const viewportBox = await patchingViewport.boundingBox();
  expect(viewportBox).not.toBeNull();
  await page.mouse.move(viewportBox!.x + viewportBox!.width * 0.75, viewportBox!.y + 34);
  await page.mouse.down();
  await page.mouse.move(viewportBox!.x + viewportBox!.width * 0.25, viewportBox!.y + 34, { steps: 8 });
  await page.mouse.up();
  expect(await patchingViewport.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);

  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const exportedSession = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(exportedSession.matrices.patching).toEqual({
    size: 54,
    mode: "pan",
    axesPinned: false,
    fitMode: "manual"
  });

  await controls.getByLabel("Reset patching matrix view").click();
  await controls.getByLabel("Pin patching matrix axes").click();
  await expect(gridRow).toHaveCSS("grid-template-columns", /54px 52px/);
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "patching-analysis-session.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(exportedSession))
  });
  await expect(page.getByText("Analysis session restored")).toBeVisible();
  await expect(controls.getByLabel("Pan patching matrix")).toHaveAttribute("aria-pressed", "true");
  await expect(controls.getByLabel("Pin patching matrix axes")).toHaveAttribute("aria-pressed", "false");
  await expect(gridRow).toHaveCSS("grid-template-columns", /54px 54px/);
  await controls.getByLabel("Fit patching matrix to width").click();
  await expect(controls.getByLabel("Fit patching matrix to width")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Patching matrix legend")).toContainText("not computed");
  const inspector = page.getByRole("region", { name: "Evidence inspector" });
  await expect(inspector).toContainText("causal");
  await expect(inspector).toContainText("50.000000");
  const axeResults = await new AxeBuilder({ page })
    .include(".patching-matrix")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth
  }))).toEqual({ viewport: 390, document: 390 });
  const mobileControlBox = await controls.getByLabel("Select patching matrix cells").boundingBox();
  expect(mobileControlBox?.width).toBeGreaterThanOrEqual(44);
  expect(mobileControlBox?.height).toBeGreaterThanOrEqual(44);
  expect(submitted?.corruptedPrompt).toBe("Corrupted aligned prompt");
  expect(submitted?.component).toBe("resid_post");
  expect(submitted?.layers).toEqual([1]);
  expect(submitted?.positions).toEqual([10]);
});

test("cancels activation patching while preserving its last progress", async ({ page }) => {
  await page.route("**/api/patching/preflight", async (route) => {
    const request = route.request().postDataJSON() as { corruptedPrompt: string };
    await route.fulfill({ json: patchingPreflight(realRun, request.corruptedPrompt) });
  });
  await page.route("**/api/jobs/patching", async (route) => {
    await route.fulfill({ status: 202, json: patchingJob("loading", realRun) });
  });
  await page.route("**/api/jobs/patching-job-13572468/events", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(patchingJob("loading", realRun))}\n\n`
    }).catch(() => undefined);
  });
  await page.route("**/api/jobs/patching-job-13572468", async (route) => {
    await route.fulfill({ json: patchingJob("cancelled", realRun) });
  });

  await page.goto("/explorer?view=patching&token=10&layer=1");
  const sourceRun = await page.getByLabel("Quick run selector").inputValue();
  await page.getByLabel("Corrupted patching prompt").fill("Corrupted aligned prompt");
  await expect(page.getByLabel("Patching preflight")).toContainText("ready");
  await page.getByRole("button", { name: "Run 1 patches" }).click();
  await expect(page.getByLabel("Patching job status")).toContainText("Patching job running");
  await expect(page.getByLabel("Patching job progress", { exact: true })).toContainText("Patch Grid");
  const progressbar = page.getByRole("progressbar", { name: "Patching job progress completion" });
  await expect(progressbar).toHaveAttribute("aria-valuenow", "58");
  await page.locator(".patching-cancel").click();
  await expect(page.getByLabel("Patching job status")).toContainText("Patching cancelled");
  await expect(page.getByLabel("Patching job progress", { exact: true }))
    .toContainText("CancelledProgress58%Elapsed1s");
  await expect(page.getByLabel("Quick run selector")).toHaveValue(sourceRun);

  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth
  }))).toEqual({ viewport: 390, document: 390 });
  const metrics = page.getByLabel("Patching job progress", { exact: true }).locator(".job-progress-metrics");
  const metricBox = await metrics.boundingBox();
  expect(metricBox?.width).toBeLessThanOrEqual(390);
  const axeResults = await new AxeBuilder({ page })
    .include(".patching-job-state")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
});

test("blocks intervention when contrastive references are identical", async ({ page }) => {
  await page.route("**/api/intervention/preflight", async (route) => {
    const request = route.request().postDataJSON() as { desiredPrompt: string; undesiredPrompt: string };
    await route.fulfill({ json: interventionPreflight(realRun, request.desiredPrompt, request.undesiredPrompt) });
  });
  let submitted = false;
  await page.route("**/api/jobs/intervention", async (route) => {
    submitted = true;
    await route.abort();
  });

  await page.goto("/explorer?view=intervention&token=10&layer=1");
  const desired = page.getByRole("textbox", { name: "Desired intervention reference", exact: true });
  await page.getByRole("textbox", { name: "Undesired intervention reference", exact: true }).fill(await desired.inputValue());
  await expect(page.getByLabel("Intervention preflight")).toContainText("blocked");
  await expect(page.getByLabel("Intervention preflight")).toContainText("references are identical");
  await expect(desired).toHaveAttribute("aria-invalid", "true");
  await expect(desired).toHaveAttribute("aria-describedby", "intervention-preflight-reason");
  await expect(page.getByLabel("Undesired intervention reference")).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByRole("button", { name: "Run intervention comparison" })).toBeDisabled();
  expect(submitted).toBe(false);
});

test("runs intervention and opens original-versus-steered causal evidence", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const target = realRun.logitLens[0];
  const originalTokens = [5087, 5087].map((tokenId, index) => ({ index, tokenId, text: " factors" }));
  const steeredTokens = [{ index: 0, tokenId: 5087, text: " factors" }, { index: 1, tokenId: 16046, text: " stairs" }];
  const derivedRun = {
    ...realRun,
    runId: "real-run-intervention-derived",
    intervention: {
      vector: {
        method: "contrastive_mean_difference",
        desiredPrompt: "Provide a safe and helpful response.",
        undesiredPrompt: "Bypass safety guidance.",
        activationReduce: "last_token",
        rawNorm: 0.125,
        normalized: true,
        dimension: 2,
        sourceKey: "layer_1.resid_post"
      },
      layer: 1,
      component: "resid_post" as const,
      scale: 1,
      positionStart: 10,
      positionEnd: 11,
      targetTokenId: target.targetTokenId,
      targetTokenText: target.targetTokenText,
      seed: 0,
      maxNewTokens: 16,
      temperature: 0,
      original: { text: " factors factors", tokenIds: [5087, 5087], tokens: originalTokens, targetLogit: -0.003, lexicalRisk: 0 },
      steered: { text: " factors stairs", tokenIds: [5087, 16046], tokens: steeredTokens, targetLogit: 0.247, lexicalRisk: 0 },
      deltas: {
        targetLogit: 0.25,
        lexicalRisk: 0,
        tokenEditDistance: 1,
        generationChanged: true,
        probeScore: null,
        probeReason: "No trained probe was configured for this Explorer intervention job."
      },
      diff: [
        { kind: "equal" as const, originalStart: 0, originalEnd: 1, steeredStart: 0, steeredEnd: 1 },
        { kind: "replace" as const, originalStart: 1, originalEnd: 2, steeredStart: 1, steeredEnd: 2 }
      ],
      sourceRun: { runId: realRun.runId, sampleId: realRun.sampleId }
    },
    metricProvenance: {
      ...realRun.metricProvenance,
      interventionTargetLogitDelta: {
        label: "Target logit delta",
        method: "Normalized contrastive activation steering",
        semantics: "Steered target-token logit minus original target-token logit.",
        normalization: "none; raw logit difference",
        kind: "causal" as const
      },
      interventionTokenEditDistance: {
        label: "Generation edit distance",
        method: "Levenshtein distance over generated token IDs",
        semantics: "Minimum token edit operations.",
        normalization: "none",
        kind: "causal" as const
      },
      interventionLexicalRiskDelta: {
        label: "Lexical risk proxy delta",
        method: "Fixed risk-term match rate",
        semantics: "Steered minus original lexical rate.",
        normalization: "matched terms per word",
        kind: "derived_proxy" as const
      }
    }
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/intervention/preflight", async (route) => {
    const request = route.request().postDataJSON() as { desiredPrompt: string; undesiredPrompt: string };
    await route.fulfill({ json: interventionPreflight(realRun, request.desiredPrompt, request.undesiredPrompt) });
  });
  await page.route("**/api/jobs/intervention", async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: interventionJob("idle", realRun) });
  });
  await page.route("**/api/jobs/intervention-job-97531864/events", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(interventionJob("ready", realRun, derivedRun))}\n\n`
    });
  });

  await page.goto("/explorer?view=intervention&token=10&layer=1");
  await expect(page.getByLabel("Intervention preflight")).toContainText("ready");
  await page.getByRole("button", { name: "Run intervention comparison" }).click();

  await expect(page.getByLabel("Quick run selector")).toHaveValue("real-run-intervention-derived::real-forward-cache-001");
  await expect(page.getByRole("tab", { name: "Intervention", exact: true })).toHaveClass(/active/);
  await expect(page.getByRole("heading", { name: "Original vs intervention" })).toBeVisible();
  await expect(page.getByLabel("Intervention metric changes")).toContainText("+0.2500");
  const inspector = page.getByRole("region", { name: "Evidence inspector" });
  await expect(inspector).toContainText("causal");
  await expect(inspector).toContainText("0.250000");
  await expect(page.getByText("Intervention comparison added to the Run Library")).toBeVisible();
  expect(submitted?.positionStart).toBe(10);
  expect(submitted?.positionEnd).toBe(11);
  expect(submitted?.layer).toBe(1);

  await page.getByLabel("Pin intervention comparison").click();
  const scaleRun = {
    ...derivedRun,
    runId: "real-run-intervention-scale-2",
    intervention: {
      ...derivedRun.intervention,
      scale: 2,
      steered: {
        ...derivedRun.intervention.steered,
        text: " factors stairs extra",
        tokenIds: [5087, 16046, 262],
        tokens: [...steeredTokens, { index: 2, tokenId: 262, text: " extra" }]
      },
      deltas: {
        ...derivedRun.intervention.deltas,
        tokenEditDistance: 2
      },
      diff: [
        { kind: "equal" as const, originalStart: 0, originalEnd: 1, steeredStart: 0, steeredEnd: 1 },
        { kind: "replace" as const, originalStart: 1, originalEnd: 2, steeredStart: 1, steeredEnd: 2 },
        { kind: "insert" as const, originalStart: 2, originalEnd: 2, steeredStart: 2, steeredEnd: 3 }
      ]
    }
  };
  const seedRun = {
    ...derivedRun,
    runId: "real-run-intervention-seed-1",
    intervention: {
      ...derivedRun.intervention,
      seed: 1,
      steered: {
        ...derivedRun.intervention.steered,
        text: " factors",
        tokenIds: [5087],
        tokens: [steeredTokens[0]]
      },
      diff: [
        { kind: "equal" as const, originalStart: 0, originalEnd: 1, steeredStart: 0, steeredEnd: 1 },
        { kind: "delete" as const, originalStart: 1, originalEnd: 2, steeredStart: 1, steeredEnd: 1 }
      ]
    }
  };
  const importInput = page.getByLabel("Import Explorer artifact JSON");
  await importInput.setInputFiles({
    name: "intervention-scale-2.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(scaleRun))
  });
  await page.getByRole("tab", { name: "Intervention", exact: true }).click();
  await page.getByLabel("Pin intervention comparison").click();
  await importInput.setInputFiles({
    name: "intervention-seed-1.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(seedRun))
  });
  await page.getByRole("tab", { name: "Intervention", exact: true }).click();
  await page.getByLabel("Pin intervention comparison").click();

  await page.getByLabel(/^Compare pinned evidence/).click();
  let drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const baselineCard = drawer.locator(".compare-card.compare-intervention")
    .filter({ hasText: derivedRun.runId });
  await baselineCard.getByLabel(/Use .* as baseline/).click();
  const generationSection = drawer.locator(".compare-generation-diff");
  await expect(generationSection.getByRole("heading", { name: "Intervention generation differences" })).toBeVisible();
  const generationRows = generationSection.locator(".compare-generation-row");
  await expect(generationRows).toHaveCount(3);
  await expect(generationSection.locator(".compare-generation-heading")).toContainText("2/3 baseline-compatible");
  const baselineGeneration = generationRows.filter({ hasText: derivedRun.runId });
  const scaleGeneration = generationRows.filter({ hasText: scaleRun.runId });
  const seedGeneration = generationRows.filter({ hasText: seedRun.runId });
  await expect(baselineGeneration.locator(".compare-generation-tokens .replace")).toHaveCount(2);
  await expect(scaleGeneration.locator(".compare-generation-tokens .insert")).toHaveCount(1);
  await expect(scaleGeneration.locator(".compare-generation-row-heading em")).toHaveText("baseline-compatible");
  await expect(scaleGeneration).toContainText("Matched model, source, target, generation parameters");
  await expect(seedGeneration.locator(".compare-generation-tokens .delete")).toHaveCount(1);
  await expect(seedGeneration.locator(".compare-generation-row-heading em")).toHaveText("standalone diff");
  await expect(seedGeneration).toContainText("Generation seed, token budget, or temperature differs.");

  const comparisonDownload = page.waitForEvent("download");
  await drawer.getByLabel("Export evidence comparison").click();
  const comparisonStream = await (await comparisonDownload).createReadStream();
  const comparisonChunks: Buffer[] = [];
  for await (const chunk of comparisonStream) comparisonChunks.push(Buffer.from(chunk));
  const comparison = JSON.parse(Buffer.concat(comparisonChunks).toString("utf8"));
  const scaleComparison = comparison.comparisons.find(
    (item: { item_id: string }) => item.item_id.includes(scaleRun.runId)
  );
  const seedComparison = comparison.comparisons.find(
    (item: { item_id: string }) => item.item_id.includes(seedRun.runId)
  );
  expect(scaleComparison.generation_difference).toMatchObject({
    available: true,
    baseline_compatible: true,
    token_edit_distance: 2,
    generation_changed: true
  });
  expect(scaleComparison.generation_difference.diff).toHaveLength(3);
  expect(seedComparison.generation_difference).toMatchObject({
    available: true,
    baseline_compatible: false,
    reason: "Generation seed, token budget, or temperature differs."
  });

  await drawer.getByLabel("Close evidence comparison").click();
  const sessionDownload = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const sessionStream = await (await sessionDownload).createReadStream();
  const sessionChunks: Buffer[] = [];
  for await (const chunk of sessionStream) sessionChunks.push(Buffer.from(chunk));
  const sessionBuffer = Buffer.concat(sessionChunks);
  const session = JSON.parse(sessionBuffer.toString("utf8"));
  const savedGenerations = session.pinnedItems.filter(
    (item: { generation?: unknown }) => item.generation !== undefined
  );
  expect(savedGenerations).toHaveLength(3);
  expect(savedGenerations.find((item: { runId: string }) => item.runId === scaleRun.runId).generation)
    .toMatchObject({
      schemaVersion: "1.0",
      sourceRun: { runId: realRun.runId, sampleId: realRun.sampleId },
      scale: 2,
      tokenEditDistance: 2,
      generationChanged: true
    });

  const invalidSession = structuredClone(session);
  invalidSession.pinnedItems.find(
    (item: { generation?: unknown }) => item.generation !== undefined
  ).generation.diff[0].originalEnd = 99;
  await importInput.setInputFiles({
    name: "invalid-generation-session.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(invalidSession))
  });
  await expect(page.getByText("Analysis session validation failed")).toBeVisible();

  await importInput.setInputFiles({
    name: "generation-session.json",
    mimeType: "application/json",
    buffer: sessionBuffer
  });
  await expect(page.getByText("Analysis session restored")).toBeVisible();
  await page.getByLabel(/^Compare pinned evidence/).click();
  drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer.locator(".compare-card").first()).toContainText(derivedRun.runId);
  await expect(drawer.locator(".compare-generation-row")).toHaveCount(3);

  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(async () => {
    const box = await drawer.boundingBox();
    return box ? { x: Math.round(box.x), width: Math.round(box.width) } : null;
  }).toEqual({ x: 0, width: 390 });
  expect(await drawer.evaluate((element) => element.scrollWidth)).toBe(390);
  const mobileOutputs = drawer.locator(".compare-generation-outputs").first().locator(".compare-generation-output");
  const originalBox = await mobileOutputs.first().boundingBox();
  const steeredBox = await mobileOutputs.last().boundingBox();
  expect(originalBox).not.toBeNull();
  expect(steeredBox).not.toBeNull();
  expect(originalBox!.y + originalBox!.height).toBeLessThanOrEqual(steeredBox!.y);
  const axeResults = await new AxeBuilder({ page })
    .include(".compare-drawer")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
  await page.emulateMedia({ forcedColors: "active" });
  await expect(drawer.locator(".compare-generation-tokens .replace").first()).toHaveCSS(
    "forced-color-adjust",
    "none"
  );

  const storedPinCount = await page.evaluate(() => {
    const key = "safelens.localExplorer.pinnedEvidence.v2";
    const pins = JSON.parse(window.localStorage.getItem(key) ?? "[]");
    const generationPin = pins.find((item: { generation?: unknown }) => item.generation !== undefined);
    generationPin.generation.diff[0].originalEnd = 99;
    window.localStorage.setItem(key, JSON.stringify(pins));
    return pins.length;
  });
  expect(storedPinCount).toBe(4);
  await page.reload();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(3\)/);
});

test("cancels intervention without replacing the source run", async ({ page }) => {
  await page.route("**/api/intervention/preflight", async (route) => {
    const request = route.request().postDataJSON() as { desiredPrompt: string; undesiredPrompt: string };
    await route.fulfill({ json: interventionPreflight(realRun, request.desiredPrompt, request.undesiredPrompt) });
  });
  await page.route("**/api/jobs/intervention", async (route) => {
    await route.fulfill({ status: 202, json: interventionJob("loading", realRun) });
  });
  await page.route("**/api/jobs/intervention-job-97531864/events", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(interventionJob("loading", realRun))}\n\n`
    }).catch(() => undefined);
  });
  await page.route("**/api/jobs/intervention-job-97531864", async (route) => {
    await route.fulfill({ json: interventionJob("cancelled", realRun) });
  });

  await page.goto("/explorer?view=intervention&token=10&layer=1");
  const sourceRun = await page.getByLabel("Quick run selector").inputValue();
  await page.getByRole("button", { name: "Run intervention comparison" }).click();
  await expect(page.getByLabel("Intervention job status")).toContainText("Intervention running");
  await expect(page.getByLabel("Intervention job progress", { exact: true })).toContainText("Generation");
  await expect(page.getByRole("progressbar", { name: "Intervention job progress completion" }))
    .toHaveAttribute("aria-valuenow", "62");
  await page.locator(".intervention-cancel").click();
  await expect(page.getByLabel("Intervention job status")).toContainText("Intervention cancelled");
  await expect(page.getByLabel("Quick run selector")).toHaveValue(sourceRun);
});

test("runs exact NLA and opens fidelity evidence in a derived run", async ({ page }) => {
  const compatibleRun = {
    ...realRun,
    modelName: "Qwen/Qwen2.5-7B-Instruct",
    layers: [0, 1, 20],
    nlaCompatibility: {
      modelName: "Qwen/Qwen2.5-7B-Instruct",
      dModel: 3584,
      availableLayers: [0, 1, 20],
      profiles: [{
        name: qwenNlaProfile.name,
        baseModel: qwenNlaProfile.base_model,
        layer: 20,
        component: "resid_post",
        dModel: 3584,
        modelMatches: true,
        layerAvailable: true,
        dModelMatches: true,
        status: "artifact_missing" as const,
        reason: "Profile structure matches; artifact not generated."
      }]
    }
  };
  const derivedRun = {
    ...compatibleRun,
    runId: "qwen-run-nla-derived",
    nla: [{
      tokenIndex: 10,
      layer: 20,
      component: "resid_post" as const,
      explanation: "A feature representing jailbreak-oriented instruction breaking.",
      cosine: 0.91,
      mse: 0.04,
      activationNorm: 42.5,
      status: "available" as const,
      profile: qwenNlaProfile.name,
      source: "layer_20.resid_post",
      token: "break"
    }],
    nlaCompatibility: {
      ...compatibleRun.nlaCompatibility,
      profiles: compatibleRun.nlaCompatibility.profiles.map((profile) => ({
        ...profile,
        status: "compatible" as const,
        reason: "Exact AV/AR artifact result is loaded for this derived run."
      }))
    },
    metadata: {
      ...compatibleRun.metadata,
      parentRun: { runId: compatibleRun.runId, sampleId: compatibleRun.sampleId },
      nlaJobs: [{
        profile: qwenNlaProfile.name,
        layer: 20,
        component: "resid_post",
        actorRevision: "abc123",
        reconstructorRevision: "def456",
        positions: [10]
      }]
    }
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/nla/profiles", async (route) => {
    await route.fulfill({ json: [qwenNlaProfile] });
  });
  await page.route("**/api/nla/preflight", async (route) => {
    await route.fulfill({ json: nlaPreflight(true) });
  });
  await page.route("**/api/jobs/nla", async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: nlaJob("idle", compatibleRun) });
  });
  await page.route("**/api/jobs/nla-job-24681357/events", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(nlaJob("ready", compatibleRun, derivedRun))}\n\n`
    });
  });

  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({ json: remoteIndex(compatibleRun) });
  });
  await page.route(/\/api\/runs\/real-hf-tiny-gpt2-local-explorer\/samples\/real-forward-cache-001$/, async (route) => {
    await route.fulfill({ json: compatibleRun });
  });
  await page.goto("/explorer?run=real-hf-tiny-gpt2-local-explorer&sample=real-forward-cache-001&view=nla&token=10&layer=20");
  await expect(page.getByLabel("NLA job preflight")).toContainText("compatible");
  await page.getByLabel("NLA checkpoint revision").fill("commit-abc123");
  await page.getByLabel("NLA maximum new tokens").fill("64");
  await page.getByRole("button", { name: "Run exact NLA" }).click();

  await expect(page.getByLabel("Quick run selector")).toHaveValue("qwen-run-nla-derived::real-forward-cache-001");
  await expect(page.getByRole("tab", { name: "NLA", exact: true })).toHaveClass(/active/);
  await expect(page.getByRole("region", { name: "Evidence inspector" })).toContainText("available");
  await expect(page.getByRole("region", { name: "Evidence inspector" })).toContainText("0.910000");
  await expect(page.getByText("NLA added to the Run Library")).toBeVisible();
  expect(submitted?.profile).toBe(qwenNlaProfile.name);
  expect(submitted?.positions).toEqual([10]);
  expect(submitted?.revision).toBe("commit-abc123");
});

test("cancels a compatible NLA job without changing unavailable source evidence", async ({ page }) => {
  await page.route("**/api/nla/profiles", async (route) => route.fulfill({ json: [qwenNlaProfile] }));
  await page.route("**/api/nla/preflight", async (route) => route.fulfill({ json: nlaPreflight(true) }));
  await page.route("**/api/jobs/nla", async (route) => {
    await route.fulfill({ status: 202, json: nlaJob("loading", realRun) });
  });
  await page.route("**/api/jobs/nla-job-24681357/events", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_000));
    await route.fulfill({
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(nlaJob("loading", realRun))}\n\n`
    }).catch(() => undefined);
  });
  await page.route("**/api/jobs/nla-job-24681357", async (route) => {
    await route.fulfill({ json: nlaJob("cancelled", realRun) });
  });

  await page.goto("/explorer?view=nla&token=10");
  const sourceRun = await page.getByLabel("Quick run selector").inputValue();
  await page.getByRole("button", { name: "Run exact NLA" }).click();
  await expect(page.getByLabel("NLA job status")).toContainText("NLA job running");
  await expect(page.getByLabel("NLA job progress", { exact: true })).toContainText("NLA AV AR");
  await expect(page.getByRole("progressbar", { name: "NLA job progress completion" }))
    .toHaveAttribute("aria-valuenow", "60");
  await page.locator(".nla-job-cancel").click();
  await expect(page.getByLabel("NLA job status")).toContainText("NLA job cancelled");
  await expect(page.getByLabel("Quick run selector")).toHaveValue(sourceRun);
});

test("restores the complete matrix selection from the URL", async ({ page }) => {
  await page.goto(
    "/?view=residual&token=10&layer=1&metric=residual_norm&normalization=raw&range=8-12"
  );

  await expect(page.getByRole("tab", { name: "Residual", exact: true })).toHaveClass(
    /active/
  );
  await expect(page.getByLabel("Layer selector").getByRole("radio", { name: "L1" })).toHaveClass(
    /active/
  );
  await expect(page.getByLabel("Matrix controls").getByRole("combobox")).toHaveValue(
    "residual_norm"
  );
  await expect(page.getByRole("button", { name: "Raw", exact: true })).toHaveClass(/active/);
  await expect(page.getByText("Token range 8–12")).toBeVisible();
  await expect(page).toHaveURL(/view=residual/);
  await expect(page).toHaveURL(/normalization=raw/);
  const legend = page.getByLabel("Matrix legend");
  await expect(legend).toHaveAttribute("data-domain", "sequential");
  await expect(legend).toContainText(/min -?\d/);
  await expect(legend).toContainText(/mid -?\d/);
  await expect(legend).toContainText(/max -?\d/);
  await page.getByRole("button", { name: "Normalized", exact: true }).click();
  await expect(page).toHaveURL(/normalization=normalized/);
  await expect(legend).toContainText("min 0.000");
  await expect(legend).toContainText("mid 0.500");
  await expect(legend).toContainText("max 1.000");
  await page.getByRole("button", { name: "Raw", exact: true }).click();
  await expect(page).toHaveURL(/normalization=raw/);
});

test("imports, persists, switches, and removes a validated Explorer artifact", async ({ page }) => {
  await page.goto("/explorer");
  await page.evaluate(() => window.localStorage.clear());
  let releaseIndex!: () => void;
  const indexGate = new Promise<void>((resolve) => { releaseIndex = resolve; });
  await page.route("**/api/runs", async (route) => {
    await indexGate;
    await route.fulfill({ json: remoteIndex(realRun) });
  });
  await page.reload();
  const importedRun = {
    ...realRun,
    runId: "imported-validation-run",
    sampleId: "sample-b",
    prompt: "Imported sample prompt",
    tokens: realRun.tokens.map((token) =>
      token.index === 10 ? { ...token, text: "IMPORTED_BREAK" } : token
    )
  };
  const artifact = JSON.stringify({ schema_version: "1.0", samples: [importedRun] });

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "validated-run.json",
    mimeType: "application/json",
    buffer: Buffer.from(artifact)
  });

  await expect(page.getByText("1 sample loaded")).toBeVisible();
  releaseIndex();
  await expect(page.getByLabel("Workspace API status")).toContainText("test-artifacts · 1 ready");
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);
  await expect(page.getByLabel(
    `Review removal of browser artifact ${realRun.runId} ${realRun.sampleId}`
  )).toHaveCount(0);
  await expect(page.getByLabel("Quick run selector")).toHaveValue(
    "imported-validation-run::sample-b"
  );
  await expect(page).toHaveURL(/run=imported-validation-run/);
  await expect(page).toHaveURL(/sample=sample-b/);
  await expect(page.getByRole("heading", { name: "Token Timeline" })).toBeVisible();
  await expect(page.locator(".token-pill").filter({ hasText: "IMPORTED_BREAK" })).toBeVisible();
  await expect(page.getByLabel("Prompt runner text")).toHaveValue("Imported sample prompt");
  const storedRuns = await page.evaluate(() => JSON.parse(
    window.localStorage.getItem("safelens.localExplorer.importedRuns.v1") ?? "[]"
  ));
  expect(storedRuns).toHaveLength(1);
  const storedValidation = explorerRunSchema.safeParse(storedRuns[0].run);
  expect(
    storedValidation.success,
    storedValidation.success ? "" : JSON.stringify(storedValidation.error.issues, null, 2)
  ).toBe(true);

  await page.reload();
  await expect(page.getByLabel("Run and sample selector")).toHaveValue(
    "imported-validation-run::sample-b"
  );
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);

  await page.getByLabel("Quick run selector").selectOption(
    `${realRun.runId}::${realRun.sampleId}`
  );
  await expect(page).toHaveURL(new RegExp(`run=${realRun.runId}`));
  await expect(page).toHaveURL(/view=overview/);
  await page.getByLabel("Run and sample selector").selectOption(
    "imported-validation-run::sample-b"
  );
  const removeImported = page.getByLabel(
    "Review removal of browser artifact imported-validation-run sample-b"
  );
  await removeImported.click();
  let removalDialog = page.getByRole("dialog", { name: "Remove browser artifact?" });
  await expect(removalDialog).toContainText("Imported artifact");
  await expect(removalDialog).toContainText("validated-run.json");
  await expect(removalDialog).toContainText(
    "Workspace files and the bundled package remain unchanged"
  );
  await expect(removalDialog).toContainText(
    "This is the active Run. SafeLens will return to the bundled Run."
  );
  await expect(removalDialog.getByRole("button", { name: "Cancel" })).toBeFocused();
  await expect(page.locator(".workspace")).toHaveAttribute("inert", "");
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);
  await removalDialog.getByRole("button", { name: "Cancel" }).click();
  await expect(removalDialog).toBeHidden();
  await expect(removeImported).toBeFocused();
  await expect(page.locator(".workspace")).not.toHaveAttribute("inert", "");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByLabel("Open run library").click();
  const drawer = page.getByRole("dialog", { name: "Runs and samples" });
  const mobileRemoveImported = drawer.getByLabel(
    "Review removal of browser artifact imported-validation-run sample-b"
  );
  await mobileRemoveImported.click();
  removalDialog = page.getByRole("dialog", { name: "Remove browser artifact?" });
  const removalBox = await removalDialog.boundingBox();
  expect(removalBox).not.toBeNull();
  expect(removalBox!.width).toBeLessThanOrEqual(358);
  for (const action of [
    removalDialog.getByRole("button", { name: "Close removal confirmation" }),
    removalDialog.getByRole("button", { name: "Cancel" }),
    removalDialog.getByRole("button", { name: "Remove browser copy" })
  ]) {
    const box = await action.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThan(43.5);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".run-removal-dialog")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await removalDialog.getByRole("button", { name: "Remove browser copy" }).click();
  await expect(drawer).toBeHidden();
  await expect(page.getByLabel("Open run library")).toBeFocused();
  await expect(page.getByLabel("Quick run selector").locator("option")).toHaveCount(1);
  await expect(page).toHaveURL(new RegExp(`run=${realRun.runId}`));
  expect(await page.evaluate(() => JSON.parse(
    window.localStorage.getItem("safelens.localExplorer.importedRuns.v1") ?? "[]"
  ))).toEqual([]);
  const storedUsageAfterRemoval = await page.evaluate(() => JSON.parse(
    window.localStorage.getItem("safelens.localExplorer.runUsage.v1") ?? "{}"
  ));
  expect(storedUsageAfterRemoval["imported-validation-run::sample-b"]).toBeUndefined();
});

test("reports JSON and artifact schema errors without changing the active run", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  const selector = page.getByLabel("Run and sample selector");
  const initialValue = await selector.inputValue();

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "broken.json",
    mimeType: "application/json",
    buffer: Buffer.from("{not valid json")
  });
  await expect(page.getByRole("alert")).toContainText("Artifact is not valid JSON");
  let diagnostics = page.getByRole("list", { name: "Artifact validation diagnostics" });
  let diagnostic = diagnostics.getByRole("listitem").first();
  await expect(diagnostic).toContainText("artifact");
  await expect(diagnostic).toContainText("invalid_json");
  await expect(diagnostic).toContainText("Expectedvalid JSON document");
  await expect(diagnostic).toContainText("Actual");
  await expect(selector).toHaveValue(initialValue);

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "future.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify({ schema_version: "9.0", samples: [] }))
  });
  await expect(page.getByRole("alert")).toContainText("unsupported schema version");
  diagnostics = page.getByRole("list", { name: "Artifact validation diagnostics" });
  diagnostic = diagnostics.getByRole("listitem").first();
  await expect(diagnostic).toContainText("schema_version");
  await expect(diagnostic).toContainText("unsupported_schema_version");
  await expect(diagnostic).toContainText('Expected"1.0"');
  await expect(diagnostic).toContainText('Actual"9.0"');
  await expect(selector.locator("option")).toHaveCount(1);

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "invalid-shape.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify({
      schema_version: "1.0",
      samples: [{ runId: "incomplete", sampleId: "sample" }]
    }))
  });
  await expect(page.getByRole("alert")).toContainText("Artifact schema validation failed");
  await expect(page.getByRole("alert")).toContainText("samples.0.tokens");
  diagnostics = page.getByRole("list", { name: "Artifact validation diagnostics" });
  diagnostic = diagnostics.getByRole("listitem").filter({ hasText: "samples.0.tokens" });
  await expect(diagnostic).toContainText("invalid_type");
  await expect(diagnostic).toContainText("Expectedarray");
  await expect(diagnostic).toContainText("Actualmissing");
  await expect(selector).toHaveValue(initialValue);

  const malformedMatrix = {
    ...realRun,
    runId: "malformed-matrix",
    attentionHeads: realRun.attentionHeads.map((head, index) =>
      index === 0
        ? { ...head, distributionByToken: head.distributionByToken.slice(1) }
        : head
    )
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "malformed-matrix.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(malformedMatrix))
  });
  await expect(page.getByRole("alert")).toContainText("destination×source matrix");
  diagnostics = page.getByRole("list", { name: "Artifact validation diagnostics" });
  diagnostic = diagnostics.getByRole("listitem").filter({
    hasText: "attentionHeads.0.distributionByToken"
  });
  await expect(diagnostic).toContainText("custom");
  await expect(diagnostic).toContainText("Expectedmust be a 20×20 destination×source matrix");
  await expect(diagnostic).toContainText("Actualarray(length 19)");
  await expect(selector.locator("option")).toHaveCount(1);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByLabel("Open run library").click();
  const drawer = page.getByRole("dialog", { name: "Runs and samples" });
  const mobileMessage = drawer.getByRole("alert");
  await expect(mobileMessage).toContainText("attentionHeads.0.distributionByToken");
  const messageBox = await mobileMessage.boundingBox();
  expect(messageBox).not.toBeNull();
  expect(messageBox!.width).toBeLessThanOrEqual(356);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".run-library-message")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("exports a schema-valid Explorer artifact", async ({ page }) => {
  await page.goto("/explorer");
  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export current Explorer artifact").click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("explorer-artifact.json");
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const artifact = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  const parsed = parseExplorerArtifact(artifact);
  expect(parsed.success, parsed.success ? "" : JSON.stringify(parsed.diagnostics)).toBe(true);
  if (parsed.success) {
    expect(parsed.schemaVersion).toBe("1.0");
    expect(parsed.runs[0].runId).toBe(realRun.runId);
  }
});

test("keeps view, token, and normalization synchronized to the URL", async ({ page }) => {
  await page.goto("/explorer");

  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await expect(page).toHaveURL(/view=attention/);
  await expect(page.getByRole("heading", { name: "Attention pattern" })).toBeVisible();
  await expect(page).toHaveURL(/metric=attention_probability/);
  await expect(page).toHaveURL(/normalization=raw/);

  await page.locator(".token-pill").filter({ hasText: "jail" }).click();
  await expect(page).toHaveURL(/token=9/);

  await expect(page).toHaveURL(/source=9/);
  await expect(page).toHaveURL(/target=9/);
});

test("confirms analysis context changes without interrupting selection", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=overview&token=10&layer=1");
  const visualNotice = page.locator(".context-change-notice");
  const liveNotice = page.getByRole("log", { name: "Analysis context changes" });

  await expect(visualNotice).toBeHidden();
  await expect(liveNotice).toHaveText("");
  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await expect(visualNotice).toBeVisible();
  await expect(visualNotice).toContainText("Context updated");
  await expect(visualNotice).toContainText("Attention · L1 · 10 → 10");
  await expect(liveNotice).toContainText("Context updated: Attention · L1 · 10 → 10");

  await page.locator(".token-pill").filter({ hasText: "jail" }).click();
  await page.getByRole("radiogroup", { name: "Analysis layer" })
    .getByRole("radio", { name: "L0" })
    .click();
  await expect(visualNotice).toContainText("Attention · L0 · 9 → 9");
  await expect(liveNotice).toContainText("Attention · L0 · 9 → 9");

  await page.goBack();
  await expect(visualNotice).toContainText("Attention · L1 · 9 → 9");
  await expect(liveNotice).toContainText("Attention · L1 · 9 → 9");
  await page.waitForTimeout(2050);
  await expect(visualNotice).toBeHidden();
  await expect(liveNotice).toContainText("Attention · L1 · 9 → 9");
});

test("confirms run changes and keeps the notice inside a mobile viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  const importedRun = {
    ...realRun,
    runId: "context-notice-run",
    sampleId: "context-notice-sample",
    prompt: "Context notice mobile sample"
  };

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "context-notice.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(importedRun))
  });
  const visualNotice = page.locator(".context-change-notice");
  const liveNotice = page.getByRole("log", { name: "Analysis context changes" });
  await expect(visualNotice).toBeVisible();
  await expect(visualNotice).toHaveAttribute("data-kind", "run");
  await expect(visualNotice).toContainText("Run changed");
  await expect(visualNotice).toContainText("context-notice-sample");
  await expect(liveNotice).toContainText("Run changed: context-notice-sample");

  const box = await visualNotice.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(390);
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.y + box!.height).toBeLessThanOrEqual(844);
  expect(box!.height).toBeGreaterThanOrEqual(44);
  await expect(visualNotice).toHaveCSS("position", "fixed");
  expect(844 - (box!.y + box!.height)).toBeGreaterThanOrEqual(0);
  expect(844 - (box!.y + box!.height)).toBeLessThanOrEqual(24);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".context-change-notice")
    .include('[aria-label="Analysis context changes"]')
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("starts incompatible Runs with a clean active context while retaining comparison snapshots", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=residual&token=10&layer=1&range=8-999");
  await expect.poll(() => new URL(page.url()).searchParams.get("range")).toBeNull();

  await page.goto(
    "/?view=attention&token=10&source=8&target=10&range=8-12&layer=0" +
    "&head=L0H0&neuron=L1N0&track=residual_direction&metric=attention_probability&normalization=raw"
  );
  await page.getByLabel("Search tokens").fill("jail");
  await page.getByLabel("Attention matrix controls", { exact: true })
    .getByLabel("Zoom in attention matrix")
    .click();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(3\)/);

  const incompatibleRun = {
    ...realRun,
    runId: "clean-context-run",
    sampleId: "clean-context-sample",
    prompt: "A structurally incompatible selection context",
    tokens: realRun.tokens.map((token) => ({
      ...token,
      risk: token.index === 3 ? 1 : 0.01
    })),
    attentionHeads: realRun.attentionHeads.map((head) => ({
      ...head,
      id: `next-${head.id}`
    })),
    mlpNeurons: realRun.mlpNeurons.map((neuron) => ({
      ...neuron,
      id: `next-${neuron.id}`
    })),
    attributionTracks: realRun.attributionTracks.map((track) => ({
      ...track,
      name: `next-${track.name}`
    })),
    attributionMethods: realRun.attributionMethods.map((method) => ({
      ...method,
      id: `next-${method.id}`,
      label: `Next ${method.label}`
    }))
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "clean-context-run.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(incompatibleRun))
  });

  const notice = page.locator(".context-change-notice.visible");
  await expect(notice).toContainText("Run changed");
  await expect(notice).toContainText("clean-context-sample · Overview · T3 · L1 · fresh selection");
  await expect(page.getByRole("tab", { name: "Overview", exact: true }))
    .toHaveAttribute("aria-selected", "true");
  await expect(page.locator('.token-pill[aria-current="true"]')).toContainText("a");
  await expect(page.getByRole("radiogroup", { name: "Analysis layer" })
    .getByRole("radio", { name: "L1" }))
    .toHaveAttribute("aria-checked", "true");
  await expect(page.getByLabel("Search tokens")).toHaveValue("");
  await expect(page.getByLabel("Token evidence markers")).not.toContainText("Pinned");
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(3\)/);

  await expect.poll(() => {
    const params = new URL(page.url()).searchParams;
    return {
      view: params.get("view"),
      token: params.get("token"),
      layer: params.get("layer"),
      range: params.get("range"),
      source: params.get("source"),
      target: params.get("target"),
      edge: params.get("edge"),
      head: params.get("head"),
      neuron: params.get("neuron"),
      track: params.get("track")
    };
  }).toEqual({
    view: "overview",
    token: "3",
    layer: "1",
    range: null,
    source: null,
    target: null,
    edge: null,
    head: expect.stringMatching(/^next-/),
    neuron: expect.stringMatching(/^next-/),
    track: expect.stringMatching(/^next-/)
  });

  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const session = await downloadJson(await downloadPromise);
  expect(session.selection).toMatchObject({
    view: "overview",
    tokenIndex: 3,
    sourceTokenIndex: 3,
    targetTokenIndex: 3,
    layer: 1,
    headId: expect.stringMatching(/^next-/),
    neuronId: expect.stringMatching(/^next-/),
    trackName: expect.stringMatching(/^next-/)
  });
  expect(session.selection.tokenRange).toBeUndefined();
  expect(session.matrices).toEqual({});
  expect(session.timeline.query).toBe("");
  expect(session.pinnedItems).toHaveLength(3);
  expect(session.pinnedItems.every((item: { runId: string }) => item.runId === realRun.runId)).toBe(true);
});

test("restores view, token, and layer through browser history", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=overview&token=10&layer=1");

  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await page.locator(".token-pill").filter({ hasText: "jail" }).click();
  await page.getByRole("radiogroup", { name: "Analysis layer" })
    .getByRole("radio", { name: "L0" })
    .click();
  await expect(page).toHaveURL(/view=attention/);
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/layer=0/);

  await page.goBack();
  await expect(page).toHaveURL(/view=attention/);
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/layer=1/);
  await expect(page.locator('.token-pill[aria-current="true"]')).toContainText("jail");
  await expect(page.getByRole("radiogroup", { name: "Analysis layer" })
    .getByRole("radio", { name: "L1" }))
    .toHaveAttribute("aria-checked", "true");

  await page.goBack();
  await expect(page).toHaveURL(/view=attention/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page.getByRole("tab", { name: "Attention", exact: true }))
    .toHaveAttribute("aria-selected", "true");

  await page.goBack();
  await expect(page).toHaveURL(/view=overview/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page.getByRole("tab", { name: "Overview", exact: true }))
    .toHaveAttribute("aria-selected", "true");

  await page.goForward();
  await page.goForward();
  await page.goForward();
  await expect(page).toHaveURL(/view=attention/);
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/layer=0/);
  await expect(page.getByRole("radiogroup", { name: "Analysis layer" })
    .getByRole("radio", { name: "L0" }))
    .toHaveAttribute("aria-checked", "true");
});

test("restores run and selection context through browser history", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=residual&token=9&layer=0&metric=residual_norm&normalization=raw");
  const importedRun = {
    ...realRun,
    runId: "history-imported-run",
    sampleId: "history-imported-sample",
    prompt: "Imported browser history sample"
  };

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "history-imported.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(importedRun))
  });
  await expect(page.getByLabel("Quick run selector"))
    .toHaveValue("history-imported-run::history-imported-sample");
  await expect(page).toHaveURL(/run=history-imported-run/);
  await expect(page).toHaveURL(/view=overview/);

  await page.goBack();
  await expect(page.getByLabel("Quick run selector"))
    .toHaveValue(`${realRun.runId}::${realRun.sampleId}`);
  await expect(page).toHaveURL(new RegExp(`run=${realRun.runId}`));
  await expect(page).toHaveURL(/view=residual/);
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/layer=0/);
  await expect(page.getByRole("tab", { name: "Residual", exact: true }))
    .toHaveAttribute("aria-selected", "true");
  await expect(page.locator('.token-pill[aria-current="true"]')).toContainText("jail");

  await page.goForward();
  await expect(page.getByLabel("Quick run selector"))
    .toHaveValue("history-imported-run::history-imported-sample");
  await expect(page).toHaveURL(/run=history-imported-run/);
  await expect(page).toHaveURL(/view=overview/);
  await expect(page.getByLabel("Prompt runner text"))
    .toHaveValue("Imported browser history sample");
});

test("restores a loaded workspace run from history without refetching it", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const workspaceRun = {
    ...realRun,
    runId: "history-workspace-run",
    sampleId: "history-workspace-sample",
    prompt: "Workspace browser history sample"
  };
  let sampleRequests = 0;
  await page.route("**/api/runs", async (route) => {
    await route.fulfill({ json: remoteIndex(workspaceRun) });
  });
  await page.route(
    /\/api\/runs\/history-workspace-run\/samples\/history-workspace-sample$/,
    async (route) => {
      sampleRequests += 1;
      await route.fulfill({ json: workspaceRun });
    }
  );

  await page.goto("/explorer?view=residual&token=9&layer=0");
  await expect(page.getByLabel("Run and sample selector").locator("option")).toHaveCount(2);
  await page.getByLabel("Run and sample selector")
    .selectOption("history-workspace-run::history-workspace-sample");
  await expect(page.getByLabel("Quick run selector"))
    .toHaveValue("history-workspace-run::history-workspace-sample");
  await expect(page.getByLabel("Prompt runner text"))
    .toHaveValue("Workspace browser history sample");
  expect(sampleRequests).toBe(1);

  await page.goBack();
  await expect(page.getByLabel("Quick run selector"))
    .toHaveValue(`${realRun.runId}::${realRun.sampleId}`);
  await expect(page).toHaveURL(/view=residual/);
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/layer=0/);

  await page.goForward();
  await expect(page.getByLabel("Quick run selector"))
    .toHaveValue("history-workspace-run::history-workspace-sample");
  await expect(page.getByLabel("Prompt runner text"))
    .toHaveValue("Workspace browser history sample");
  expect(sampleRequests).toBe(1);
});

test("restores mobile analysis context through browser history", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=overview&token=10&layer=1");

  await page.getByRole("tab", { name: "Residual", exact: true }).click();
  await page.locator(".token-pill").filter({ hasText: "jail" }).click();
  await expect(page).toHaveURL(/view=residual/);
  await expect(page).toHaveURL(/token=9/);

  await page.goBack();
  await expect(page).toHaveURL(/view=residual/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page.getByRole("tab", { name: "Residual", exact: true }))
    .toHaveAttribute("aria-selected", "true");

  await page.goBack();
  await expect(page).toHaveURL(/view=overview/);
  await expect(page.getByRole("tab", { name: "Overview", exact: true }))
    .toHaveAttribute("aria-selected", "true");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});

test("navigates analysis views and layers as roving keyboard controls", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=overview&token=10&layer=1");

  const tabs = page.getByRole("tablist", { name: "Analysis view" });
  await expect(tabs.getByRole("tab")).toHaveCount(8);
  await expect(tabs.locator('[role="tab"][tabindex="0"]')).toHaveCount(1);
  const overview = tabs.getByRole("tab", { name: "Overview" });
  await overview.focus();
  await page.keyboard.press("ArrowRight");
  const residual = tabs.getByRole("tab", { name: "Residual" });
  await expect(residual).toBeFocused();
  await expect(residual).toHaveAttribute("aria-selected", "true");
  await expect(page).toHaveURL(/view=residual/);
  await expect(page.getByRole("tabpanel", { name: "Residual" })).toBeVisible();
  expect(new URL(page.url()).searchParams.get("token")).toBe("10");

  await page.keyboard.press("End");
  const attribution = tabs.getByRole("tab", { name: "Attribution" });
  await expect(attribution).toBeFocused();
  await expect(attribution).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Home");
  await expect(overview).toBeFocused();

  const layers = page.getByRole("radiogroup", { name: "Analysis layer" });
  await expect(layers.locator('[role="radio"][tabindex="0"]')).toHaveCount(1);
  const layerOne = layers.getByRole("radio", { name: "L1" });
  await layerOne.focus();
  await page.keyboard.press("ArrowLeft");
  const layerZero = layers.getByRole("radio", { name: "L0" });
  await expect(layerZero).toBeFocused();
  await expect(layerZero).toHaveAttribute("aria-checked", "true");
  await expect(page).toHaveURL(/layer=0/);
  expect(new URL(page.url()).searchParams.get("token")).toBe("10");
});

test("completes analysis, pin, and compare using only the keyboard", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=overview&token=10&layer=1");

  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to analysis workspace" });
  await expect(skipLink).toBeFocused();
  await page.keyboard.press("Enter");
  const workspace = page.getByRole("region", { name: "Analysis workspace" });
  await expect(workspace).toBeFocused();

  let selectedTimelineToken = page.locator('.token-pill[aria-current="true"]');
  for (let index = 0; index < 12; index += 1) {
    await page.keyboard.press("Tab");
    if (await selectedTimelineToken.evaluate((element) => element === document.activeElement)) break;
  }
  await expect(selectedTimelineToken).toBeFocused();
  await expect(selectedTimelineToken).toHaveAttribute(
    "aria-keyshortcuts",
    "ArrowLeft ArrowRight Space Control+Enter Meta+Enter"
  );

  await page.keyboard.press("ArrowRight");
  selectedTimelineToken = page.locator('.token-pill[aria-current="true"]');
  await expect(selectedTimelineToken).toBeFocused();
  await expect(selectedTimelineToken).toContainText("strategy");
  await expect(page).toHaveURL(/token=11/);

  const compareTrigger = page.getByLabel(/^Compare pinned evidence/).first();
  await expect(compareTrigger).toHaveAttribute("aria-label", /\(3\)/);
  await expect(compareTrigger).toHaveAttribute("aria-keyshortcuts", "Alt+Shift+C");
  await page.keyboard.press("Space");
  await expect(selectedTimelineToken).toBeFocused();
  await expect(compareTrigger).toHaveAttribute("aria-label", /\(4\)/);
  await expect(page.getByLabel("Token evidence markers")).toContainText("Pinned");

  await page.keyboard.press("Alt+Shift+C");
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByLabel("Close evidence comparison")).toBeFocused();
  await expect(drawer.getByText("token 11")).toBeVisible();
  await expect(page.locator(".topbar")).toHaveAttribute("inert", "");
  await expect(page.locator(".workspace")).toHaveAttribute("inert", "");
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(compareTrigger).toBeFocused();

  const prompt = page.getByLabel("Prompt runner text");
  await prompt.focus();
  const promptBefore = await prompt.inputValue();
  await page.keyboard.press("Alt+Shift+C");
  await expect(drawer).toBeHidden();
  expect(await prompt.inputValue()).toBe(promptBefore);

  const search = page.getByLabel("Search tokens");
  await search.focus();
  await page.keyboard.press("Alt+Shift+C");
  await expect(drawer).toBeHidden();

  const axeResults = await new AxeBuilder({ page })
    .include("#analysis-workspace")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
});

test("executes contextual quick actions with complete modal and mobile focus flows", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=residual&token=10&layer=1");

  const trigger = page.getByLabel("Open quick actions");
  await trigger.click();
  let dialog = page.getByRole("dialog", { name: "Quick actions" });
  const close = dialog.getByLabel("Close quick actions");
  await expect(dialog).toBeVisible();
  await expect(close).toBeFocused();
  await expect(dialog.getByText(realRun.runId, { exact: true })).toBeVisible();
  await expect(dialog.getByText(realRun.sampleId, { exact: true })).toBeVisible();
  await expect(dialog.getByText("Residual", { exact: true })).toBeVisible();
  await expect(dialog.getByText("L1", { exact: true })).toBeVisible();
  await expect(dialog.getByText("break", { exact: true })).toBeVisible();
  await expect(dialog.getByRole("button", { name: /Compare pinned evidence/ })).toContainText("3 items ready");
  await expect(page.locator(".topbar")).toHaveAttribute("inert", "");
  await expect(page.locator(".workspace")).toHaveAttribute("inert", "");

  const lastAction = dialog.getByRole("button", { name: /Export current evidence/ });
  await lastAction.focus();
  await page.keyboard.press("Tab");
  await expect(close).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(lastAction).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();

  await trigger.click();
  await page.getByRole("dialog", { name: "Quick actions" })
    .getByRole("button", { name: /Find a token/ })
    .click();
  await expect(page.getByLabel("Search tokens")).toBeFocused();

  await trigger.click();
  await page.getByRole("dialog", { name: "Quick actions" })
    .getByRole("button", { name: /Open Overview/ })
    .click();
  await expect(page.getByRole("tab", { name: "Overview" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("region", { name: "Analysis workspace" })).toBeFocused();

  await trigger.click();
  await page.getByRole("dialog", { name: "Quick actions" })
    .getByRole("button", { name: /Runs and samples/ })
    .click();
  const library = page.getByRole("dialog", { name: "Runs and samples" });
  await expect(library).toBeVisible();
  await expect(library.getByLabel("Close run library")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();

  await trigger.click();
  await page.getByRole("dialog", { name: "Quick actions" })
    .getByRole("button", { name: /Compare pinned evidence/ })
    .click();
  const compare = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(compare).toBeVisible();
  await expect(compare.getByLabel("Close evidence comparison")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByLabel(/^Compare pinned evidence/).first()).toBeFocused();

  await trigger.click();
  const sessionDownload = page.waitForEvent("download");
  await page.getByRole("dialog", { name: "Quick actions" })
    .getByRole("button", { name: /Export analysis session/ })
    .click();
  expect((await sessionDownload).suggestedFilename()).toBe(
    `${realRun.runId}-${realRun.sampleId}-analysis-session.json`
  );

  await trigger.click();
  const evidenceDownload = page.waitForEvent("download");
  await page.getByRole("dialog", { name: "Quick actions" })
    .getByRole("button", { name: /Export current evidence/ })
    .click();
  expect((await evidenceDownload).suggestedFilename()).toBe(`${realRun.runId}-token-10-layer-1.json`);

  await page.setViewportSize({ width: 390, height: 844 });
  await trigger.click();
  dialog = page.getByRole("dialog", { name: "Quick actions" });
  await expect(dialog).toBeVisible();
  const dialogBox = await dialog.boundingBox();
  expect(dialogBox).not.toBeNull();
  expect(dialogBox!.x).toBe(0);
  expect(dialogBox!.width).toBe(390);
  expect(dialogBox!.y + dialogBox!.height).toBeCloseTo(844, 0);
  const actionSizes = await dialog.locator(".quick-actions-list > button").evaluateAll((buttons) => (
    buttons.map((button) => {
      const box = button.getBoundingClientRect();
      return { width: box.width, height: box.height };
    })
  ));
  expect(actionSizes.every(({ width, height }) => width >= 44 && height >= 44)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);

  const axeResults = await new AxeBuilder({ page })
    .include(".quick-actions-dialog")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);

  const screenshotPath = testInfo.outputPath("quick-actions-mobile.png");
  await page.screenshot({ path: screenshotPath });
  await testInfo.attach("quick-actions-mobile", { path: screenshotPath, contentType: "image/png" });
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
});

test("reveals overflowed analysis views with mobile tab scroll controls", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explorer?view=overview&token=10&layer=1");

  const tabs = page.getByRole("tablist", { name: "Analysis view" });
  const next = page.getByLabel("Show more analysis views");
  const previous = page.getByLabel("Show previous analysis views");
  async function visibleTabGeometry() {
    return tabs.evaluate((element) => {
      const viewport = element.getBoundingClientRect();
      const visible = [...element.querySelectorAll<HTMLElement>('[role="tab"]')]
        .map((tab) => {
          const rect = tab.getBoundingClientRect();
          return {
            label: tab.textContent?.trim() ?? "",
            left: rect.left,
            right: rect.right,
            clientWidth: tab.clientWidth,
            scrollWidth: tab.scrollWidth
          };
        })
        .filter((tab) => tab.right > viewport.left + 1 && tab.left < viewport.right - 1);
      return {
        visible,
        whole: visible.every((tab) =>
          tab.left >= viewport.left - 1 && tab.right <= viewport.right + 1
        )
      };
    });
  }
  await expect(next).toBeVisible();
  await expect(next).toBeEnabled();
  await expect(previous).toBeVisible();
  await expect(previous).toBeDisabled();
  expect(await tabs.evaluate((element) => element.scrollLeft)).toBe(0);
  const nextInitialBox = await next.boundingBox();
  expect(nextInitialBox?.width).toBeGreaterThanOrEqual(44);
  expect(nextInitialBox?.height).toBeGreaterThanOrEqual(44);
  await expect.poll(visibleTabGeometry).toMatchObject({ whole: true });
  expect((await visibleTabGeometry()).visible).toHaveLength(3);
  for (const tab of (await visibleTabGeometry()).visible) {
    expect(tab.scrollWidth).toBeLessThanOrEqual(tab.clientWidth);
  }

  await next.click();
  await expect.poll(() => tabs.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  await expect(previous).toBeEnabled();
  const [previousBox, tabsBox, nextBox] = await Promise.all([
    previous.boundingBox(),
    tabs.boundingBox(),
    next.boundingBox()
  ]);
  expect(previousBox!.x + previousBox!.width).toBeLessThanOrEqual(tabsBox!.x);
  expect(tabsBox!.x + tabsBox!.width).toBeLessThanOrEqual(nextBox!.x);
  await expect.poll(visibleTabGeometry).toMatchObject({ whole: true });
  expect(new URL(page.url()).searchParams.get("view")).toBe("overview");
  await testInfo.attach("analysis-view-tabs-390", {
    body: await page.locator(".main-header").screenshot(),
    contentType: "image/png"
  });

  for (let attempt = 0; attempt < 5 && await next.isEnabled(); attempt += 1) {
    await next.click();
    await page.waitForTimeout(250);
  }
  await expect(next).toBeDisabled();
  const attribution = tabs.getByRole("tab", { name: "Attribution" });
  await expect(attribution).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(attribution).toHaveAttribute("aria-selected", "true");
  await expect(page).toHaveURL(/view=attribution/);

  await page.reload();
  await expect(attribution).toHaveAttribute("aria-selected", "true");
  await expect.poll(async () => {
    const [tabBox, listBox] = await Promise.all([attribution.boundingBox(), tabs.boundingBox()]);
    return Boolean(
      tabBox && listBox &&
      tabBox.x >= listBox.x - 1 &&
      tabBox.x + tabBox.width <= listBox.x + listBox.width + 1
    );
  }).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  const axeResults = await new AxeBuilder({ page })
    .include(".main-header")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);

  await page.setViewportSize({ width: 768, height: 844 });
  await page.goto("/explorer?view=overview&token=10&layer=1");
  await expect(next).toBeVisible();
  await expect.poll(visibleTabGeometry).toMatchObject({ whole: true });
  expect((await visibleTabGeometry()).visible).toHaveLength(6);
  await next.click();
  await expect.poll(() => tabs.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  const [mediumPreviousBox, mediumTabsBox, mediumNextBox] = await Promise.all([
    previous.boundingBox(),
    tabs.boundingBox(),
    next.boundingBox()
  ]);
  expect(mediumPreviousBox!.x + mediumPreviousBox!.width).toBeLessThanOrEqual(mediumTabsBox!.x);
  expect(mediumTabsBox!.x + mediumTabsBox!.width).toBeLessThanOrEqual(mediumNextBox!.x);
  await expect.poll(visibleTabGeometry).toMatchObject({ whole: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(768);
  await testInfo.attach("analysis-view-tabs-768", {
    body: await page.locator(".main-header").screenshot(),
    contentType: "image/png"
  });
});

test("keeps mobile deep links at the page context while profile rails reveal selections", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.setViewportSize({ width: 390, height: 844 });
  const views = [
    ["overview", "Overview"],
    ["residual", "Residual"],
    ["attention", "Attention"],
    ["mlp", "MLP"],
    ["nla", "NLA"],
    ["patching", "Patching"],
    ["intervention", "Intervention"],
    ["attribution", "Attribution"]
  ] as const;

  for (const [view, label] of views) {
    await page.goto(`/explorer?view=${view}&token=10&layer=1`);
    await expect(page.getByRole("tab", { name: label })).toHaveAttribute("aria-selected", "true");
    if (view === "nla") {
      await expect(page.getByRole("group", { name: "NLA token positions" })).toBeVisible();
    } else {
      await expect(page.getByRole("region", { name: "Token timeline" })).toBeVisible();
    }
    await page.waitForTimeout(500);
    expect(await page.evaluate(() => window.scrollY), `${label} moved the document on mount`).toBe(0);
    await expect(page.locator(".topbar")).toBeVisible();
  }

  await page.goto("/explorer?view=attention&token=10&source=1&target=10&layer=1&head=L1H0");
  const rail = page.getByRole("radiogroup", { name: "Incoming source token profile" });
  await rail.scrollIntoViewIfNeeded();
  const pageScrollBeforeNavigation = await page.evaluate(() => window.scrollY);
  const selected = rail.getByRole("radio", { checked: true });
  await selected.focus();
  await selected.press("End");
  await expect(rail.getByRole("radio").last()).toBeChecked();
  await expect.poll(() => rail.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  expect(await page.evaluate(() => window.scrollY)).toBe(pageScrollBeforeNavigation);
});

test("skips directly to analysis and scopes global token navigation", async ({ page }) => {
  await page.goto("/explorer?view=overview&token=10&layer=1");
  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to analysis workspace" });
  await expect(skipLink).toBeFocused();
  await expect(skipLink).toBeVisible();
  await page.keyboard.press("Enter");

  const workspace = page.getByRole("region", { name: "Analysis workspace" });
  await expect(workspace).toBeFocused();
  await expect(workspace).toHaveAttribute("aria-keyshortcuts", "ArrowLeft ArrowRight");
  await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL(/token=11/);

  const exportButton = page.getByLabel("Export current evidence as JSON");
  await exportButton.focus();
  await page.keyboard.press("ArrowRight");
  expect(new URL(page.url()).searchParams.get("token")).toBe("11");

  await page.getByLabel("Search tokens").focus();
  await page.keyboard.press("ArrowLeft");
  expect(new URL(page.url()).searchParams.get("token")).toBe("11");
});

test("keeps mobile selection, pin, compare, and inspector actions sticky", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explorer?view=overview&token=10&layer=1");

  const summary = page.getByRole("region", { name: "Current evidence actions" });
  await expect(summary).toBeVisible();
  await page.getByText("Trace evidence", { exact: true }).scrollIntoViewIfNeeded();
  const stickyBox = await summary.boundingBox();
  expect(stickyBox).not.toBeNull();
  expect(stickyBox!.y).toBeGreaterThanOrEqual(7);
  expect(stickyBox!.y).toBeLessThanOrEqual(10);

  const pin = summary.getByLabel("Unpin current evidence");
  await expect(pin).toHaveAttribute("aria-pressed", "true");
  await pin.click();
  await expect(summary.getByLabel("Pin current evidence")).toHaveAttribute("aria-pressed", "false");

  const compare = summary.getByLabel(/^Open evidence comparison/);
  await compare.click();
  await expect(page.getByRole("dialog", { name: "Compare pinned evidence" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(compare).toBeFocused();

  await summary.getByLabel("Open evidence inspector").click();
  await expect(page.getByRole("dialog", { name: "Evidence details" })).toBeVisible();
});

test("keeps evidence actions within reach at compact desktop widths", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto("/explorer?view=attention&token=10&source=1&target=10&layer=1&head=L1H0");

  const workspace = page.getByRole("region", { name: "Analysis workspace" });
  const actions = page.getByRole("region", { name: "Current evidence actions" });
  await expect(actions).toBeVisible();
  await expect(page.locator(".right-panel")).toBeHidden();
  const [workspaceBox, actionsBox] = await Promise.all([
    workspace.boundingBox(),
    actions.boundingBox()
  ]);
  expect(workspaceBox).not.toBeNull();
  expect(actionsBox).not.toBeNull();
  expect(actionsBox!.x).toBeGreaterThanOrEqual(workspaceBox!.x);
  expect(actionsBox!.x + actionsBox!.width).toBeLessThanOrEqual(workspaceBox!.x + workspaceBox!.width);

  await page.getByRole("heading", { name: "Attention edge profile" }).scrollIntoViewIfNeeded();
  await expect.poll(async () => (await actions.boundingBox())?.y ?? -1).toBeGreaterThanOrEqual(7);
  expect((await actions.boundingBox())!.y).toBeLessThanOrEqual(10);
  const actionButtons = actions.locator(":scope > button");
  await expect(actionButtons).toHaveCount(3);
  for (const button of await actionButtons.all()) {
    const box = await button.boundingBox();
    expect(box?.width).toBeGreaterThanOrEqual(44);
    expect(box?.height).toBeGreaterThanOrEqual(44);
  }

  const inspectorTrigger = actions.getByLabel("Open evidence inspector");
  await inspectorTrigger.click();
  const drawer = page.getByRole("dialog", { name: "Evidence details" });
  await expect(drawer).toBeVisible();
  const drawerBox = await drawer.boundingBox();
  expect(drawerBox).not.toBeNull();
  expect(drawerBox!.x).toBeGreaterThanOrEqual(0);
  expect(drawerBox!.x + drawerBox!.width).toBeLessThanOrEqual(1024);
  await drawer.getByLabel("Show full evidence details").click();
  await expect(drawer).toHaveAttribute("data-detail-level", "full");
  await expect(drawer.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();
  expect(await drawer.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  const [drawerBounds, titleBounds] = await Promise.all([
    drawer.boundingBox(),
    drawer.getByRole("heading", { name: "Evidence details" }).boundingBox()
  ]);
  expect(titleBounds!.x).toBeGreaterThanOrEqual(drawerBounds!.x);
  expect(titleBounds!.x + titleBounds!.width).toBeLessThanOrEqual(drawerBounds!.x + drawerBounds!.width);
  const accessibility = await new AxeBuilder({ page })
    .include(".mobile-inspector-drawer")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  const screenshotPath = testInfo.outputPath("compact-desktop-evidence-actions.png");
  await page.screenshot({ path: screenshotPath });
  await testInfo.attach("compact-desktop-evidence-actions", {
    path: screenshotPath,
    contentType: "image/png"
  });
  await drawer.getByLabel("Close evidence inspector").click();
  await expect(inspectorTrigger).toBeFocused();
});

test("meets automated WCAG A and AA checks in the primary analysis workspace", async ({ page }) => {
  test.setTimeout(60_000);
  await page.addInitScript(() => window.localStorage.clear());
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/explorer?view=overview&token=10&layer=1");
  async function expectNoViolations() {
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  }

  await expectNoViolations();
  for (const view of ["Residual", "Attention", "MLP", "NLA", "Patching", "Intervention", "Attribution"]) {
    await page.getByRole("tab", { name: view }).click();
    await expectNoViolations();
  }
  await page.getByRole("tab", { name: "Overview" }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await expectNoViolations();

  await page.getByLabel("Open run library").click();
  await expectNoViolations();
  await page.keyboard.press("Escape");
  await page.getByLabel("Open evidence inspector").click();
  await expectNoViolations();
  await page.keyboard.press("Escape");
  await page.getByLabel(/^Compare pinned evidence/).click();
  await expectNoViolations();
});

test("honors reduced motion across loading, selection, notices, drawers, and tab scrolling", async ({ page }) => {
  let releaseRemote: (() => void) | undefined;
  const remoteGate = new Promise<void>((resolve) => {
    releaseRemote = resolve;
  });
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await remoteGate;
    await route.fulfill({ json: remoteIndex(realRun) });
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/explorer?view=overview&token=10&layer=1");

  const workspaceStatus = page.getByLabel("Workspace API status");
  await expect(workspaceStatus).toHaveAttribute("aria-busy", "true");
  const loadingSpinner = workspaceStatus.locator(".spin");
  await expect(loadingSpinner).toBeVisible();
  await expect(loadingSpinner).toHaveCSS("animation-name", "none");
  releaseRemote?.();
  await expect(workspaceStatus).toHaveAttribute("aria-busy", "false");

  const jail = page.locator(".token-pill").filter({ hasText: "jail" });
  await jail.click();
  await expect(page.locator(".token-pill.pulse")).toHaveCount(0);
  await expect(jail).toHaveCSS("transition-duration", "0s");
  const notice = page.locator(".context-change-notice.visible");
  await expect(notice).toBeVisible();
  await expect(notice).toHaveCSS("transition-duration", "0s");

  await page.emulateMedia({ reducedMotion: "no-preference" });
  const breakToken = page.locator(".token-pill").filter({ hasText: "break" });
  await breakToken.click();
  await expect(breakToken).toHaveClass(/pulse/);
  await expect(breakToken).toHaveCSS("animation-name", "token-pulse");

  await page.emulateMedia({ reducedMotion: "reduce" });
  await jail.click();
  await expect(page.locator(".token-pill.pulse")).toHaveCount(0);

  const compareTrigger = page.getByLabel(/^Compare pinned evidence/).first();
  await compareTrigger.click();
  await expect(page.locator(".compare-backdrop")).toHaveCSS("animation-name", "none");
  await expect(page.locator(".compare-drawer")).toHaveCSS("animation-name", "none");
  await page.keyboard.press("Escape");
  await expect(compareTrigger).toBeFocused();

  await page.setViewportSize({ width: 390, height: 844 });
  const tabList = page.getByRole("tablist", { name: "Analysis view" });
  await tabList.evaluate((element) => {
    const original = element.scrollBy.bind(element);
    Object.defineProperty(element, "scrollBy", {
      configurable: true,
      value: (options: ScrollToOptions) => {
        (window as unknown as { __safelensScrollBehavior?: ScrollBehavior })
          .__safelensScrollBehavior = options.behavior;
        original(options);
      }
    });
  });
  await page.getByLabel("Show more analysis views").click();
  expect(await page.evaluate(() => (
    window as unknown as { __safelensScrollBehavior?: ScrollBehavior }
  ).__safelensScrollBehavior)).toBe("auto");

  await page.getByLabel("Open run library").click();
  await expect(page.locator(".mobile-library-backdrop")).toHaveCSS("animation-name", "none");
  await expect(page.locator(".mobile-library-drawer")).toHaveCSS("animation-name", "none");
  await page.getByLabel("Close run library").click();
});

test("presents an actionable overview evidence map without overstating missing evidence", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=overview&token=10&layer=1");

  const map = page.getByRole("region", { name: "Evidence map" });
  await expect(map.getByRole("heading", { name: "Evidence map" })).toBeVisible();
  await expect(map.getByRole("heading", { name: /Token 10 ranks 1 of 20/ })).toBeVisible();
  await expect(map.getByText("derived proxy", { exact: true }).first()).toBeVisible();
  await expect(map.getByText("exploratory", { exact: true }).first()).toBeVisible();

  const supporting = map.getByRole("region", { name: "Supporting evidence" });
  const contradicting = map.getByRole("region", { name: "Contradicting evidence" });
  await expect(supporting.getByRole("button")).toHaveCount(2);
  await expect(supporting).toContainText("Residual direction");
  await expect(supporting).toContainText("Attention proxy");
  await expect(contradicting.getByRole("button")).toHaveCount(0);
  await expect(contradicting).toContainText(
    "No contradictory measure is loaded; absence is not confirmation."
  );
  await expect(map.getByRole("region", { name: "Limitations" }).getByRole("listitem"))
    .toHaveCount(3);
  const recommendations = map.getByRole("region", { name: "Recommended analysis" });
  await expect(recommendations.getByRole("button")).toHaveCount(3);

  const accessibility = await new AxeBuilder({ page })
    .include(".overview-evidence-map")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await testInfo.attach("overview-evidence-map-desktop", {
    body: await map.screenshot(),
    contentType: "image/png"
  });

  await recommendations.getByRole("button", { name: /Inspect residual trajectory/ }).click();
  await expect(page).toHaveURL(/view=residual/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page).toHaveURL(/layer=1/);
  await page.getByRole("tab", { name: "Overview", exact: true }).click();

  await page.setViewportSize({ width: 390, height: 844 });
  const primary = page.locator(".overview-primary-finding");
  await primary.evaluate((element) => element.scrollIntoView({ block: "start" }));
  const stickyBox = await page.locator(".mobile-selection-summary").boundingBox();
  const primaryBox = await primary.boundingBox();
  expect(stickyBox).not.toBeNull();
  expect(primaryBox).not.toBeNull();
  expect(primaryBox!.y).toBeGreaterThanOrEqual(stickyBox!.y + stickyBox!.height);
  for (const button of await recommendations.getByRole("button").all()) {
    const box = await button.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await testInfo.attach("overview-evidence-map-mobile", {
    body: await map.screenshot(),
    contentType: "image/png"
  });
});

test("routes contradictory proxies and exact causal evidence from the overview map", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const target = realRun.logitLens[0];
  const contradictoryRun = {
    ...realRun,
    runId: "overview-contradictory-run",
    sampleId: "overview-contradictory-sample",
    tokens: realRun.tokens.map((token) =>
      token.index === 10 ? { ...token, attribution: 0.1 } : token
    ),
    residualCells: realRun.residualCells.map((cell) =>
      cell.layer === 1 && cell.tokenIndex === 10
        ? { ...cell, riskDirection: 0.2 }
        : cell
    ),
    patching: {
      cleanPrompt: realRun.prompt,
      corruptedPrompt: "Corrupted aligned prompt",
      component: "resid_post" as const,
      targetTokenId: target.targetTokenId,
      targetTokenText: target.targetTokenText,
      cleanScore: 4.5,
      corruptedScore: 2.5,
      denominator: 2,
      layers: [1],
      positions: [10],
      corruptedTokens: patchingPreflight(realRun, "Corrupted aligned prompt").corruptedTokens,
      cells: [{
        layer: 1,
        tokenIndex: 10,
        patchedScore: 2.1,
        causalEffect: -0.4,
        recoveryPercentage: -20,
        sourceKey: "layer_1.resid_post"
      }],
      sourceRun: { runId: realRun.runId, sampleId: realRun.sampleId },
      sourceKey: `activation_patching.resid_post[target=${target.targetTokenId}]`
    }
  };
  await page.goto("/explorer");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "overview-contradictory.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(contradictoryRun))
  });

  const map = page.getByRole("region", { name: "Evidence map" });
  const supporting = map.getByRole("region", { name: "Supporting evidence" });
  const contradicting = map.getByRole("region", { name: "Contradicting evidence" });
  await expect(supporting.getByRole("button")).toHaveCount(0);
  await expect(supporting).toContainText("No loaded measure currently supports");
  await expect(contradicting.getByRole("button")).toHaveCount(3);
  await expect(contradicting).toContainText("Residual direction");
  await expect(contradicting).toContainText("Attention proxy");
  const causalNode = contradicting.getByRole("button", { name: /Activation patch effect/ });
  await expect(causalNode).toContainText("causal evidence");
  await expect(causalNode).toContainText("-0.400");
  await causalNode.click();
  await expect(page).toHaveURL(/view=patching/);
  await expect(page.getByLabel("Layer by token activation patching matrix")).toBeVisible();
});

test("keeps visualization and selection states visible in forced colors", async ({ page }, testInfo) => {
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await page.goto("/explorer?view=attention&token=10&layer=1");

  const selectedTab = page.getByRole("tab", { name: "Attention" });
  await expect(selectedTab).toHaveAttribute("aria-selected", "true");
  expect(await selectedTab.evaluate((element) => getComputedStyle(element).backgroundColor)).not.toBe("rgba(0, 0, 0, 0)");
  const selectedLayer = page.getByRole("radio", { name: "L1", exact: true });
  await expect(selectedLayer).toHaveAttribute("aria-checked", "true");

  const attentionCells = page.locator(".attention-pattern-cell");
  await expect(attentionCells.first()).toBeVisible();
  expect(await attentionCells.first().evaluate((element) => getComputedStyle(element).forcedColorAdjust)).toBe("none");
  const selectedCell = page.locator(".attention-pattern-cell.selected");
  await expect(selectedCell).toBeVisible();
  expect(await selectedCell.evaluate((element) => getComputedStyle(element).outlineWidth)).toBe("3px");

  for (const view of ["MLP", "NLA", "Attribution"]) {
    await page.getByRole("tab", { name: view }).click();
    const selector = view === "MLP"
      ? ".mlp-activation-cell"
      : view === "NLA"
        ? ".nla-empty-candidates button"
        : ".attribution-value-cell";
    await expect(page.locator(selector).first()).toBeVisible();
    expect(await page.locator(selector).first().evaluate(
      (element) => getComputedStyle(element).forcedColorAdjust
    )).toBe("none");
  }

  await testInfo.attach("forced-colors-visualizations", {
    body: await page.screenshot(),
    contentType: "image/png"
  });
});

test("associates required long-form errors with their fields", async ({ page }) => {
  await page.goto("/explorer?view=overview&token=10&layer=1");
  const prompt = page.getByLabel("Prompt runner text");
  await prompt.fill("   ");
  await expect(prompt).toHaveAttribute("aria-invalid", "true");
  await expect(prompt).toHaveAttribute("aria-describedby", "prompt-runner-required");
  await expect(page.locator("#prompt-runner-required")).toContainText("Prompt text is required");
  await expect(page.getByRole("button", { name: "Run analysis" })).toBeDisabled();

  await page.getByRole("tab", { name: "Attribution" }).click();
  const response = page.getByLabel("Attribution response text");
  await response.fill("   ");
  await expect(response).toHaveAttribute("aria-invalid", "true");
  await expect(response).toHaveAttribute("aria-describedby", "attribution-response-required");
  await expect(page.locator("#attribution-response-required")).toContainText("Response text is required");
  await expect(page.getByRole("button", { name: "Run Integrated Gradients" })).toBeDisabled();
});

test("isolates and retries a failed lazy view module without reloading the workspace", async ({ page, context }, testInfo) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  let releaseModule!: () => void;
  const moduleGate = new Promise<void>((resolve) => { releaseModule = resolve; });
  await page.addInitScript(() => {
    window.__SAFELENS_TEST_LAZY_TIMEOUT_MS__ = 1200;
  });
  await page.route("**/*", async (route) => {
    if (!route.request().url().includes("/src/components/AttentionPatternMatrix.tsx")) {
      await route.continue();
      return;
    }
    await moduleGate;
    await route.continue();
  });

  await page.goto("/explorer?view=overview&token=10&layer=1");
  const originalDocument = await page.evaluate(() => performance.timeOrigin);
  await page.getByRole("tab", { name: "Attention", exact: true }).click();

  const moduleLoading = page.getByLabel("Loading Attention view");
  await expect(moduleLoading).toBeVisible();
  await expect(moduleLoading.locator(".analysis-loading-skeleton")).toBeVisible();
  expect((await moduleLoading.boundingBox())?.height).toBeGreaterThanOrEqual(320);
  expect((await moduleLoading.locator(".analysis-loading-stage").boundingBox())?.height)
    .toBeGreaterThanOrEqual(220);

  const errorState = page.getByRole("alert", { name: "Attention view error" });
  await expect(errorState).toBeVisible();
  releaseModule();
  await expect(errorState).toBeFocused();
  await expect(errorState).toContainText("Your run, token selection, Timeline, pins, and Inspector are unchanged.");
  await expect(page.getByLabel("Token timeline")).toBeVisible();
  await expect(page.getByRole("region", { name: "Evidence inspector" })).toContainText("break");
  await expect(page).toHaveURL(/view=attention/);
  await expect(page).toHaveURL(/token=10/);
  await testInfo.attach("view-error-desktop", {
    body: await errorState.screenshot(),
    contentType: "image/png"
  });

  await errorState.getByText("Technical detail").click();
  await expect(errorState.locator("code")).toContainText("Lazy module AttentionPatternMatrix timed out");
  await errorState.getByRole("button", { name: "Copy diagnostics" }).click();
  await expect(errorState.getByRole("button", { name: "Copied" })).toBeVisible();
  const diagnostics = JSON.parse(await page.evaluate(() => navigator.clipboard.readText()));
  expect(diagnostics.kind).toBe("safelens-view-render-error");
  expect(diagnostics.view).toBe("Attention");
  expect(diagnostics.context).toContain(":attention:");

  await page.setViewportSize({ width: 390, height: 844 });
  await errorState.scrollIntoViewIfNeeded();
  for (const button of await errorState.getByRole("button").all()) {
    expect((await button.boundingBox())?.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await testInfo.attach("view-error-mobile", {
    body: await page.screenshot(),
    contentType: "image/png"
  });
  const errorAxe = await new AxeBuilder({ page })
    .include(".view-error-state")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(errorAxe.violations).toEqual([]);

  await errorState.getByRole("button", { name: "Open Overview" }).click();
  await expect(page.getByRole("tab", { name: "Overview", exact: true })).toHaveAttribute("aria-selected", "true");
  await expect(page).toHaveURL(/view=overview/);
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(originalDocument);

  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await expect(errorState).toBeVisible();
  await errorState.getByRole("button", { name: "Retry view" }).click();
  await expect(page.getByRole("heading", { name: "Attention pattern" })).toBeVisible();
  await expect(page.getByRole("alert", { name: "Attention view error" })).toHaveCount(0);
  expect(await page.evaluate(() => performance.timeOrigin)).toBe(originalDocument);
});

test("searches, groups, ranges, and pins from the token timeline", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  const timeline = page.getByLabel("Token timeline");
  await expect(timeline.getByText("User prompt")).toBeVisible();
  await expect(timeline.locator(".source-prompt > header")).toContainText("20 tokens");
  await expect(timeline.getByLabel("Token evidence markers")).toContainText("Safety proxy");
  await expect(timeline.locator('.token-pill[tabindex="0"]')).toHaveCount(1);

  await timeline.getByLabel("Search tokens").fill("jail");
  await expect(timeline.getByLabel("Token search results")).toContainText("1 matches");
  await timeline.getByLabel("Next token search result").click();
  await expect(page).toHaveURL(/token=9/);
  await expect(timeline.locator('[data-timeline-start="9"]')).toBeFocused();

  await timeline.locator('[data-timeline-start="12"]').click({ modifiers: ["Shift"] });
  await expect(page).toHaveURL(/range=9-12/);
  await expect(timeline.locator(".token-pill.in-range")).toHaveCount(4);

  const compareTrigger = page.getByLabel(/^Compare pinned evidence/);
  await expect(compareTrigger).toHaveAttribute("aria-label", /\(3\)/);
  await timeline.locator('[data-timeline-start="0"]').click({ modifiers: ["Control"] });
  await expect(compareTrigger).toHaveAttribute("aria-label", /\(4\)/);
  await expect(timeline.getByLabel("Token evidence markers")).toContainText("Pinned");

  await timeline.getByLabel("Token color metric").selectOption("residual");
  await expect(timeline.locator(".token-pill.metric-residual")).toHaveCount(20);
  await timeline.getByRole("button", { name: "Word", exact: true }).click();
  expect(await timeline.locator(".token-pill").count()).toBeLessThan(20);
  await expect(timeline.locator('[data-timeline-start="0"]')).toContainText("User:");
});

test("shows reply, special, generation, probe, and monitor metadata when present", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  const metadataRun = {
    ...realRun,
    runId: "timeline-metadata-validation",
    sampleId: "reply-sample",
    nla: realRun.nla.map((row, index) => index === 0
      ? { ...row, status: "available" as const, cosine: 0.73, profile: "timeline-marker-fixture" }
      : row),
    tokens: realRun.tokens.map((token) => ({
      ...token,
      source: token.index >= 17 ? "reply" as const : "prompt" as const,
      text: token.index === 17 ? " generated" : token.index === 18 ? "ly" : token.index === 19 ? " response" : token.text,
      isSpecial: token.index === 0,
      generationStep: token.index >= 17 ? token.index - 17 : undefined,
      probeScore: token.index === 18 ? 0.82 : undefined,
      monitorHit: token.index === 18
    }))
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "timeline-metadata.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(metadataRun))
  });

  const timeline = page.getByLabel("Token timeline");
  await expect(timeline.getByText("User prompt")).toBeVisible();
  await expect(timeline.getByText("Assistant reply")).toBeVisible();
  const promptHeader = timeline.locator(".source-prompt > header");
  const replyHeader = timeline.locator(".source-reply > header");
  await expect(promptHeader).toContainText("Input context");
  await expect(promptHeader.getByLabel("Prompt sequence summary")).toContainText("T0–T16");
  await expect(replyHeader).toContainText("Generated continuation");
  await expect(replyHeader.getByLabel("Reply sequence summary")).toContainText("T17–T19");
  await expect(replyHeader.getByLabel("Reply sequence summary")).toContainText("G0–G2");
  await expect(replyHeader).toContainText("3 tokens");
  const special = timeline.locator(".token-pill.special");
  await expect(special).toHaveCount(1);
  await expect(special.locator(".special-badge")).toHaveText("Special");
  await expect(special).toHaveAttribute("aria-label", /user prompt, special token/);
  await expect(timeline.getByLabel("Token evidence markers")).toContainText("Probe");
  await expect(timeline.getByLabel("Token evidence markers")).toContainText("Monitor");
  await timeline.locator('[data-timeline-start="18"]').click({ modifiers: ["Control"] });
  const markerLegend = timeline.getByLabel("Token evidence markers");
  const markerShapes = {
    risk: "triangle",
    attribution: "diamond",
    nla: "ring",
    probe: "pentagon",
    monitor: "cross",
    pinned: "square"
  } as const;
  for (const [marker, shape] of Object.entries(markerShapes)) {
    await expect(markerLegend.locator(`[data-marker="${marker}"]`)).toHaveAttribute("data-shape", shape);
  }
  const shapeSignatures = await markerLegend.locator(".token-marker").evaluateAll((markers) =>
    markers.map((marker) => {
      const style = getComputedStyle(marker);
      return `${style.clipPath}|${style.borderRadius}|${style.borderStyle}|${style.borderWidth}`;
    })
  );
  expect(new Set(shapeSignatures).size).toBe(Object.keys(markerShapes).length);
  await expect(timeline.getByLabel("Token color metric").locator('option[value="probe"]')).toHaveCount(1);
  const generationStep = timeline.locator('[data-timeline-start="18"]');
  await expect(generationStep.locator(".generation-badge")).toHaveText("G1");
  await expect(generationStep).toHaveAttribute("aria-label", /assistant reply, generation step 1/);
  await expect(generationStep).toHaveAttribute("aria-label", /evidence markers: Probe, Monitor/);

  await timeline.getByRole("button", { name: "Word", exact: true }).click();
  const specialWord = timeline.locator('[data-timeline-start="0"]');
  await expect(specialWord.locator(".special-badge")).toHaveText("Special");
  await expect(specialWord).not.toContainText("2 tokens");
  await expect(timeline.locator('[data-timeline-start="1"]')).toBeVisible();
  const combinedWord = timeline.locator('[data-timeline-start="17"]');
  await expect(combinedWord).toContainText("2 tokens");
  await expect(combinedWord.locator(".generation-badge")).toHaveText("G0–1");
  await expect(combinedWord).toHaveAttribute("aria-label", /generation steps 0 to 1/);

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(replyHeader).toBeVisible();
  const compactToolbar = timeline.locator(".token-timeline-toolbar");
  const granularity = timeline.getByLabel("Timeline granularity");
  const colorMetric = timeline.getByLabel("Token color metric");
  const searchStatus = timeline.getByLabel("Token search results");
  await expect(searchStatus).toBeHidden();
  const compactToolbarBox = await compactToolbar.boundingBox();
  const granularityBox = await granularity.boundingBox();
  const colorMetricBox = await colorMetric.boundingBox();
  expect(compactToolbarBox).not.toBeNull();
  expect(granularityBox).not.toBeNull();
  expect(colorMetricBox).not.toBeNull();
  expect(compactToolbarBox!.height).toBeLessThan(170);
  expect(Math.abs(granularityBox!.y - colorMetricBox!.y)).toBeLessThanOrEqual(1);
  expect(granularityBox!.x + granularityBox!.width).toBeLessThanOrEqual(colorMetricBox!.x);

  await timeline.getByLabel("Search tokens").fill("generated");
  await expect(timeline.locator(".timeline-search-match-count")).toHaveText("1 match");
  await expect(searchStatus).toBeVisible();
  for (const button of await searchStatus.getByRole("button").all()) {
    expect((await button.boundingBox())?.height).toBeGreaterThanOrEqual(44);
  }
  const queriedToolbarWidth = await compactToolbar.evaluate((element) => ({
    client: element.clientWidth,
    scroll: element.scrollWidth
  }));
  expect(queriedToolbarWidth.scroll).toBeLessThanOrEqual(queriedToolbarWidth.client);
  for (const control of await compactToolbar.locator("button:visible, select:visible").all()) {
    const dimensions = await control.evaluate((element) => ({
      client: element.clientWidth,
      scroll: element.scrollWidth
    }));
    expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.client);
  }
  await timeline.getByLabel("Clear token search").click();
  await expect(searchStatus).toBeHidden();
  const timelineWidths = await timeline.evaluate((element) => ({
    client: element.clientWidth,
    scroll: element.scrollWidth
  }));
  expect(timelineWidths.scroll).toBeLessThanOrEqual(timelineWidths.client);
  const accessibility = await new AxeBuilder({ page })
    .include('[aria-label="Token timeline"]')
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);

  await page.emulateMedia({ forcedColors: "active" });
  const forcedColorShapes = await markerLegend.locator(".token-marker").evaluateAll((markers) =>
    markers.map((marker) => getComputedStyle(marker).clipPath)
  );
  expect(new Set(forcedColorShapes).size).toBeGreaterThanOrEqual(5);

  await page.emulateMedia({ forcedColors: "none" });
  await page.setViewportSize({ width: 768, height: 900 });
  await expect(searchStatus).toBeHidden();
  const tabletGranularity = await granularity.boundingBox();
  const tabletMetric = await colorMetric.boundingBox();
  expect(tabletGranularity).not.toBeNull();
  expect(tabletMetric).not.toBeNull();
  expect(Math.abs(tabletGranularity!.y - tabletMetric!.y)).toBeLessThanOrEqual(1);
  expect(await compactToolbar.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
});

test("windows long token timelines and jumps to offscreen search results", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const longRun = expandedTimelineRun(260);
  await page.goto("/explorer");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "long-timeline.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(longRun))
  });

  const timeline = page.getByLabel("Token timeline");
  await expect(timeline.getByLabel("Timeline render window")).toBeVisible();
  await expect(timeline.locator(".token-pill")).toHaveCount(180);
  await timeline.getByLabel("Search tokens").fill("token-250");
  await timeline.getByLabel("Next token search result").click();
  await expect(page).toHaveURL(/token=250/);
  await expect(timeline.locator('.token-pill[data-timeline-start="250"]')).toBeVisible();
  await expect(timeline.locator(".token-pill")).toHaveCount(180);
  await expect(timeline.getByLabel("Timeline render window")).toContainText("260");
});

test("selects and pins a source-destination attention pair", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto(
    "/?view=attention&token=10&source=1&target=10&layer=1&head=L1H0&metric=attention_probability&normalization=raw"
  );

  const anchorCell = page.locator(
    '.attention-pattern-cell[data-source="9"][data-destination="12"]'
  );
  await anchorCell.scrollIntoViewIfNeeded();
  await anchorCell.click({ modifiers: ["Shift"] });
  await expect(page).toHaveURL(/source=1/);
  await expect(page).toHaveURL(/target=10/);
  await expect(page.getByLabel("Attention matrix selection summary")).toContainText("D12 · S9");
  await expect(page.getByLabel("Attention matrix selection summary").locator("span").nth(2))
    .not.toContainText("n/a");
  await expect(anchorCell).toHaveClass(/comparison/);

  const directPinCell = page.locator(
    '.attention-pattern-cell[data-source="8"][data-destination="12"]'
  );
  await directPinCell.click({ modifiers: ["Control"] });
  await expect(page).toHaveURL(/source=1/);
  await expect(page).toHaveURL(/target=10/);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; sourceTokenIndex?: number }) =>
      pin.view === "attention" && pin.tokenIndex === 12 && pin.sourceTokenIndex === 8
    );
  })).toBe(true);
  await page.getByLabel("Clear Attention matrix comparison anchor").click();
  await expect(anchorCell).not.toHaveClass(/comparison/);
  await expect(page.getByLabel("Attention matrix selection summary").locator("span").nth(1))
    .toContainText("none");

  const cell = page.locator(
    '.attention-pattern-cell[data-source="9"][data-destination="12"]'
  );
  await cell.scrollIntoViewIfNeeded();
  await cell.click();
  await expect(page).toHaveURL(/source=9/);
  await expect(page).toHaveURL(/target=12/);
  await expect(page).toHaveURL(/token=12/);
  await expect(page.getByLabel("Selected attention pair")).toContainText("source 9");
  await expect(page.getByLabel("Selected attention pair")).toContainText("destination 12");

  await page.setViewportSize({ width: 390, height: 844 });
  await directPinCell.click({ modifiers: ["Shift"] });
  const mobileSummary = page.getByLabel("Attention matrix selection summary");
  await mobileSummary.scrollIntoViewIfNeeded();
  const [summaryBox, stickyBox, clearBox] = await Promise.all([
    mobileSummary.boundingBox(),
    page.locator(".mobile-selection-summary").boundingBox(),
    mobileSummary.getByRole("button").boundingBox()
  ]);
  expect(summaryBox!.y).toBeGreaterThanOrEqual(stickyBox!.y + stickyBox!.height);
  expect(clearBox!.width).toBeGreaterThanOrEqual(44);
  expect(clearBox!.height).toBeGreaterThanOrEqual(44);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  await page.getByRole("button", { name: "Pin pair" }).click();
  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer.getByText("pair 9→12")).toBeVisible();
});

test("keeps every attention display mode legible across responsive workspaces", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());

  for (const width of [390, 1024, 1280, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/explorer?view=attention&token=10&source=1&target=10&layer=1&head=L1H0");
    const controls = page.getByLabel("Attention matrix controls", { exact: true });
    const display = controls.getByRole("radiogroup", { name: "Attention head display" });
    await expect(display).toBeVisible();

    async function displayGeometry() {
      return display.getByRole("radio").evaluateAll((buttons) => buttons.map((button) => {
        const rect = button.getBoundingClientRect();
        return {
          label: button.textContent?.trim() ?? "",
          left: Math.round(rect.left),
          top: Math.round(rect.top),
          clientWidth: button.clientWidth,
          scrollWidth: button.scrollWidth
        };
      }));
    }

    let geometry = await displayGeometry();
    expect(geometry.map(({ label }) => label)).toEqual([
      "Head", "Difference", "Mean", "Max", "Rollout", "Entropy"
    ]);
    expect(geometry.every(({ clientWidth, scrollWidth }) => scrollWidth <= clientWidth)).toBe(true);
    expect(new Set(geometry.map(({ left }) => left)).size).toBe(3);
    expect(new Set(geometry.map(({ top }) => top)).size).toBe(2);

    await display.getByRole("radio", { name: "Difference" }).click();
    await expect(display.getByRole("radio", { name: "Difference" }))
      .toHaveAttribute("aria-checked", "true");
    geometry = await displayGeometry();
    expect(geometry.every(({ clientWidth, scrollWidth }) => scrollWidth <= clientWidth)).toBe(true);
    expect(new Set(geometry.map(({ left }) => left)).size).toBe(3);
    expect(new Set(geometry.map(({ top }) => top)).size).toBe(2);
    const notice = page.locator(".context-change-notice.visible");
    await expect(notice).toBeVisible();
    const [noticeBox, controlsBox] = await Promise.all([
      notice.boundingBox(),
      controls.boundingBox()
    ]);
    expect(noticeBox).not.toBeNull();
    expect(controlsBox).not.toBeNull();
    const overlapWidth = Math.min(
      noticeBox!.x + noticeBox!.width,
      controlsBox!.x + controlsBox!.width
    ) - Math.max(noticeBox!.x, controlsBox!.x);
    const overlapHeight = Math.min(
      noticeBox!.y + noticeBox!.height,
      controlsBox!.y + controlsBox!.height
    ) - Math.max(noticeBox!.y, controlsBox!.y);
    expect(overlapWidth > 0 && overlapHeight > 0).toBe(false);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);

    if (width === 1440) {
      const screenshotPath = testInfo.outputPath("attention-display-modes-1440.png");
      await controls.screenshot({ path: screenshotPath });
      await testInfo.attach("attention-display-modes-1440", {
        path: screenshotPath,
        contentType: "image/png"
      });
    }
  }
});

test("compares retained attention heads with shared-scale small multiples", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto(
    "/?view=attention&token=10&source=1&target=10&layer=1&head=L1H0&metric=attention_probability&normalization=raw"
  );

  const overview = page.getByLabel("Attention heads at layer 1");
  const heads = overview.getByRole("button");
  await expect(heads).toHaveCount(2);
  await expect(heads.nth(0)).toHaveAttribute("aria-pressed", "true");
  await expect(heads.nth(0)).toHaveAccessibleName(/row entropy .* peak source .* peak probability/);
  await expect(page.getByLabel(/Shared head overview scale from 0 to/)).toContainText("raw probability");

  const thumbnail = overview.locator("canvas").first();
  await expect(thumbnail).toBeVisible();
  const thumbnailColors = await thumbnail.evaluate((canvas: HTMLCanvasElement) => {
    const context = canvas.getContext("2d");
    if (!context) return 0;
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    const colors = new Set<string>();
    for (let offset = 0; offset < pixels.length; offset += 16) {
      colors.add(`${pixels[offset]}:${pixels[offset + 1]}:${pixels[offset + 2]}:${pixels[offset + 3]}`);
    }
    return colors.size;
  });
  expect(thumbnailColors).toBeGreaterThan(4);

  await heads.nth(1).click();
  await expect(page).toHaveURL(/head=L1H1/);
  await expect(heads.nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Selected attention pair")).toContainText("destination 10");
  await expect(page.getByLabel("Selected attention pair")).toContainText("source 1");

  await heads.nth(1).press("ArrowLeft");
  await expect(page).toHaveURL(/head=L1H0/);
  await expect(heads.nth(0)).toBeFocused();
  await expect(heads.nth(0)).toHaveAttribute("aria-pressed", "true");
  await heads.nth(0).press("ArrowLeft");
  await expect(heads.nth(0)).toBeFocused();
  await heads.nth(0).press("End");
  await expect(page).toHaveURL(/head=L1H1/);
  await expect(heads.nth(1)).toBeFocused();
  await heads.nth(1).press("Home");
  await expect(page).toHaveURL(/head=L1H0/);
  await expect(heads.nth(0)).toBeFocused();

  const accessibility = await new AxeBuilder({ page })
    .include(".attention-head-overview")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);

  await testInfo.attach("attention-head-overview-desktop", {
    body: await overview.screenshot(),
    contentType: "image/png"
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await overview.scrollIntoViewIfNeeded();
  await expect(overview.getByRole("button")).toHaveCount(2);
  const mobileBox = await page.locator(".attention-head-overview").boundingBox();
  expect(mobileBox).not.toBeNull();
  expect(mobileBox!.x).toBeGreaterThanOrEqual(0);
  expect(mobileBox!.x + mobileBox!.width).toBeLessThanOrEqual(390);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await testInfo.attach("attention-head-overview-mobile", {
    body: await page.locator(".attention-head-overview").screenshot(),
    contentType: "image/png"
  });
});

test("aggregates retained attention heads with reproducible derived provenance", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const aggregateRun = {
    ...realRun,
    runId: "attention-aggregate-run",
    sampleId: "attention-aggregate-sample",
    attentionHeads: realRun.attentionHeads.map((head) => {
      if (head.id !== "L1H1") return head;
      return {
        ...head,
        entropy: 0.5,
        distributionByToken: head.distributionByToken.map((row, destination) =>
          destination === 10
            ? row.map((_, source) => source === 0 ? 0.25 : source === 10 ? 0.75 : 0)
            : row
        )
      };
    })
  };
  await page.goto("/explorer?view=attention&token=10&source=1&target=10&layer=1&head=L1H0");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "attention-aggregate.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(aggregateRun))
  });
  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Attention pattern" })).toBeVisible();
  const sourceOne = page.locator('.attention-pattern-cell[data-source="1"][data-destination="10"]');
  await sourceOne.scrollIntoViewIfNeeded();
  await sourceOne.click();

  const display = page.getByRole("radiogroup", { name: "Attention head display" });
  const mean = display.getByRole("radio", { name: "Mean" });
  const maximum = display.getByRole("radio", { name: "Max" });
  const entropy = display.getByRole("radio", { name: "Entropy" });
  const single = display.getByRole("radio", { name: "Head" });
  await expect(single).toHaveAttribute("aria-checked", "true");

  const h0 = aggregateRun.attentionHeads.find((head) => head.id === "L1H0")!;
  const h1 = aggregateRun.attentionHeads.find((head) => head.id === "L1H1")!;
  const h0Value = h0.distributionByToken[10][1];
  const h1Value = h1.distributionByToken[10][1];
  await mean.click();
  expect(new URL(page.url()).searchParams.get("head")).toBe("aggregate:mean");
  await expect(mean).toHaveAttribute("aria-checked", "true");
  await expect(page.locator(".attention-pattern-toolbar select")).toHaveValue("");
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText(
    ((h0Value + h1Value) / 2).toFixed(4)
  );
  await expect(page.getByText("Mean retained heads", { exact: true }).first()).toBeVisible();
  await expect(page.getByLabel("Current evidence summary")).toContainText("derived proxy");
  await expect(page.getByText(/Client-derived mean cell over 2 retained heads/)).toBeVisible();
  await expect(page.getByText(/derived\.attention\.mean\[L1H0,L1H1\]/).first()).toBeVisible();
  await expect(page.getByLabel("Attention heads at layer 1").getByRole("button").nth(0))
    .toHaveAttribute("aria-pressed", "false");

  await maximum.click();
  expect(new URL(page.url()).searchParams.get("head")).toBe("aggregate:max");
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText(
    Math.max(h0Value, h1Value).toFixed(4)
  );

  await entropy.click();
  expect(new URL(page.url()).searchParams.get("head")).toBe("aggregate:entropy_weighted");
  const h0Weight = 1 / h0.entropy;
  const h1Weight = 1 / h1.entropy;
  const entropyValue = (h0Value * h0Weight + h1Value * h1Weight) / (h0Weight + h1Weight);
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText(
    entropyValue.toFixed(4)
  );
  await entropy.press("Home");
  await expect(single).toBeFocused();
  expect(new URL(page.url()).searchParams.get("head")).toBe("L1H0");
  await single.press("End");
  await expect(entropy).toBeFocused();
  expect(new URL(page.url()).searchParams.get("head")).toBe("aggregate:entropy_weighted");

  await mean.click();
  await page.getByRole("button", { name: "Pin pair" }).click();
  await maximum.click();
  await page.getByRole("button", { name: "Pin pair" }).click();
  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const meanCard = drawer.locator(".compare-card").filter({ hasText: "head Mean retained heads" });
  const maxCard = drawer.locator(".compare-card").filter({ hasText: "head Max retained heads" });
  await expect(meanCard).toHaveCount(1);
  await expect(maxCard).toHaveCount(1);
  await meanCard.getByLabel(/Use .* as baseline/).click();
  await expect(maxCard.locator(".compare-value em")).toHaveText("Different metric; no delta.");
  await drawer.getByLabel("Close evidence comparison").click();
  await mean.click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const session = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(session.selection.headId).toBe("aggregate:mean");
  const aggregatePin = session.pinnedItems.find(
    (item: { headId?: string }) => item.headId === "aggregate:mean"
  );
  expect(aggregatePin).toMatchObject({
    metric: "attention_retained_mean",
    headId: "aggregate:mean",
    sourceKey: "derived.attention.mean[L1H0,L1H1]",
    provenance: { kind: "derived_proxy" },
    profile: { kind: "attention_source_profile" },
    matrix: { kind: "attention_matrix" }
  });

  await page.reload();
  await expect(mean).toHaveAttribute("aria-checked", "true");
  expect(new URL(page.url()).searchParams.get("head")).toBe("aggregate:mean");
  await page.getByRole("radio", { name: "L0", exact: true }).click();
  await expect(mean).toHaveAttribute("aria-checked", "true");
  expect(new URL(page.url()).searchParams.get("head")).toBe("aggregate:mean");
  await expect(page.getByText(/retained · L0/).first()).toBeVisible();
  await page.getByRole("radio", { name: "L1", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await display.scrollIntoViewIfNeeded();
  for (const control of await display.getByRole("radio").all()) {
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".attention-pattern-section")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("computes retained attention rollout through preceding layers with explicit provenance", async ({ page }) => {
  await page.addInitScript(() => {
    if (window.sessionStorage.getItem("attention-rollout-test-started")) return;
    window.localStorage.clear();
    window.sessionStorage.setItem("attention-rollout-test-started", "true");
  });
  const rolloutRun: ExplorerRun = {
    ...realRun,
    runId: "attention-rollout-run",
    sampleId: "attention-rollout-sample",
    attentionHeads: realRun.attentionHeads.map((head) => ({
      ...head,
      distributionByToken: head.distributionByToken.map((row, destination) =>
        row.map((_, source) => {
          if (head.layer === 1 && destination === 10) {
            if (source === 0) return 0.8;
            if (source === 10) return 0.2;
            return 0;
          }
          return source === destination ? 1 : 0;
        })
      )
    }))
  };

  await page.goto("/explorer?view=attention&token=10&source=0&target=10&layer=1&head=L1H0");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "attention-rollout.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(rolloutRun))
  });
  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  const display = page.getByRole("radiogroup", { name: "Attention head display" });
  const rollout = display.getByRole("radio", { name: "Rollout" });
  await rollout.click();

  expect(new URL(page.url()).searchParams.get("head")).toBe("rollout:retained_mean_identity");
  await expect(rollout).toHaveAttribute("aria-checked", "true");
  const sourceZero = page.locator('.attention-pattern-cell[data-source="0"][data-destination="10"]');
  await sourceZero.scrollIntoViewIfNeeded();
  await sourceZero.click();
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText("0.4000");
  await expect(page.locator(".attention-pattern-legend")).toContainText(
    "retained mean + identity residual rollout · L0–L1"
  );
  await expect(page.getByLabel("Current evidence summary")).toContainText("derived proxy");
  await expect(page.getByText(/Client-derived retained-head rollout through L1/)).toBeVisible();
  await expect(page.getByText(
    /derived\.attention\.rollout\.retained_mean_identity\[L0,L1;L0H0,L0H1,L1H0,L1H1\]/
  ).first()).toBeVisible();
  const overviewHeads = page.getByLabel("Attention heads at layer 1").getByRole("button");
  await expect(overviewHeads).toHaveCount(2);
  await expect(overviewHeads.nth(0)).toHaveAttribute("aria-pressed", "false");
  await expect(overviewHeads.nth(0)).toHaveAttribute("tabindex", "0");

  const selfPair = page.locator('.attention-pattern-cell[data-source="10"][data-destination="10"]');
  await selfPair.scrollIntoViewIfNeeded();
  await selfPair.click();
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText("0.6000");
  await page.getByRole("button", { name: "Pin pair" }).click();
  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer.locator(".compare-card").filter({ hasText: "head Retained attention rollout" }))
    .toHaveCount(1);
  await drawer.getByLabel("Close evidence comparison").click();

  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const session = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(session.selection.headId).toBe("rollout:retained_mean_identity");
  const rolloutPin = session.pinnedItems.find(
    (item: { headId?: string }) => item.headId === "rollout:retained_mean_identity"
  );
  expect(rolloutPin).toMatchObject({
    metric: "attention_retained_rollout_mean_identity",
    sourceKey: "derived.attention.rollout.retained_mean_identity[L0,L1;L0H0,L0H1,L1H0,L1H1]",
    provenance: { kind: "derived_proxy" },
    profile: { kind: "attention_source_profile", signed: false },
    matrix: { kind: "attention_matrix" }
  });

  await page.reload();
  await expect(display.getByRole("radio", { name: "Rollout" })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText("0.6000");
  await rollout.press("ArrowLeft");
  await expect(display.getByRole("radio", { name: "Max" })).toBeFocused();
  await expect(display.getByRole("radio", { name: "Max" })).toHaveAttribute("aria-checked", "true");
  await display.getByRole("radio", { name: "Max" }).press("ArrowRight");
  await expect(rollout).toBeFocused();

  await page.getByRole("radio", { name: "L0", exact: true }).click();
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText("1.0000");
  await page.setViewportSize({ width: 390, height: 844 });
  await display.scrollIntoViewIfNeeded();
  for (const control of await display.getByRole("radio").all()) {
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".attention-pattern-section")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("renders and compares signed retained-head difference matrices", async ({ page }, testInfo) => {
  await page.addInitScript(() => {
    if (window.sessionStorage.getItem("attention-difference-test-started")) return;
    window.localStorage.clear();
    window.sessionStorage.setItem("attention-difference-test-started", "true");
  });
  const differenceRun = {
    ...realRun,
    runId: "attention-difference-run",
    sampleId: "attention-difference-sample",
    attentionHeads: realRun.attentionHeads.map((head) => {
      if (head.id !== "L1H0" && head.id !== "L1H1") return head;
      return {
        ...head,
        distributionByToken: head.distributionByToken.map((row, destination) =>
          destination === 10
            ? row.map((_, source) => {
                if (head.id === "L1H0") return source === 0 ? 0.8 : source === 1 ? 0.2 : 0;
                return source === 0 ? 0.1 : source === 1 ? 0.9 : 0;
              })
            : row
        )
      };
    })
  };
  await page.goto("/explorer?view=attention&token=10&source=1&target=10&layer=1&head=L1H0");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "attention-difference.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(differenceRun))
  });
  await page.getByRole("tab", { name: "Attention", exact: true }).click();

  await page.getByLabel(/^Compare pinned evidence/).click();
  const initialDrawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(initialDrawer).toBeVisible();
  await expect(initialDrawer.getByLabel(/^Remove .* from comparison$/).first()).toBeVisible();
  while (await initialDrawer.getByLabel(/^Remove .* from comparison$/).count()) {
    await initialDrawer.getByLabel(/^Remove .* from comparison$/).first().click();
  }
  await initialDrawer.getByLabel("Close evidence comparison").click();

  const controls = page.getByLabel("Attention matrix controls", { exact: true });
  const display = controls.getByRole("radiogroup", { name: "Attention head display" });
  const difference = display.getByRole("radio", { name: "Difference" });
  const selectedPairCell = page.locator(
    '.attention-pattern-cell[data-source="1"][data-destination="10"]'
  );
  await selectedPairCell.scrollIntoViewIfNeeded();
  await selectedPairCell.click();
  await difference.click();
  expect(new URL(page.url()).searchParams.get("head")).toBe("difference:L1H0:L1H1");
  await expect(difference).toHaveAttribute("aria-checked", "true");
  await expect(controls.getByLabel("Selected head")).toHaveValue("L1H0");
  await expect(controls.getByLabel("Baseline")).toHaveValue("L1H1");
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText("-0.7000");
  const pairDetails = page.getByLabel("Attention pair details");
  const entropyOf = (values: number[]) => {
    const total = values.reduce((sum, value) => sum + value, 0);
    return values.reduce((entropy, value) => {
      const probability = value / total;
      return probability > 0 ? entropy - probability * Math.log(probability) : entropy;
    }, 0);
  };
  const selectedEntropy = entropyOf([0.8, 0.2]);
  const baselineEntropy = entropyOf([0.1, 0.9]);
  await expect(pairDetails).toContainText(
    `${selectedEntropy.toFixed(3)} / ${baselineEntropy.toFixed(3)}`
  );
  await expect(pairDetails).toContainText("selected / baseline row entropy");
  await expect(pairDetails).toContainText("#2 / 11");
  await expect(pairDetails.locator("span[title]")).toHaveAttribute(
    "title",
    `Row entropy delta +${(selectedEntropy - baselineEntropy).toFixed(3)} nats`
  );
  await expect(pairDetails).toContainText("selected pair");
  await expect(page.locator('.attention-pattern-cell[data-source="0"][data-destination="10"]'))
    .toHaveClass(/difference positive/);
  await expect(page.locator('.attention-pattern-cell[data-source="1"][data-destination="10"]'))
    .toHaveClass(/difference negative/);
  await page.locator('.attention-pattern-cell[data-source="0"][data-destination="10"]').hover();
  await expect(pairDetails).toContainText("focused cell");
  await expect(pairDetails).toContainText("#1 / 11");
  await expect(pairDetails).toContainText("+0.700000");
  await page.mouse.move(0, 0);
  await expect(pairDetails).toContainText("selected pair");
  const signedEdgeProfile = page.locator(".attention-edge-profile");
  await expect(signedEdgeProfile).toHaveClass(/signed/);
  await expect(signedEdgeProfile.locator('.attention-edge-token-rail button[data-edge-token="0"]'))
    .toHaveClass(/positive/);
  await expect(signedEdgeProfile.locator('.attention-edge-token-rail button[data-edge-token="1"]'))
    .toHaveClass(/negative/);
  await expect(page.locator(".attention-pattern-legend")).toContainText("L1H0 - L1H1 · raw probability delta");
  await expect(page.getByLabel("Attention heads at layer 1").getByRole("button").nth(0))
    .toContainText("Selected");
  await expect(page.getByLabel("Attention heads at layer 1").getByRole("button").nth(1))
    .toContainText("Baseline");
  await expect(page.getByText(/derived\.attention\.difference\[L1H0-L1H1\]/).first()).toBeVisible();
  await expect(page.getByLabel("Current evidence summary")).toContainText("derived proxy");

  await page.getByRole("button", { name: "Pin pair" }).click();
  await controls.getByLabel("Selected head").selectOption("L1H1");
  expect(new URL(page.url()).searchParams.get("head")).toBe("difference:L1H1:L1H0");
  await expect(controls.getByLabel("Baseline")).toHaveValue("L1H0");
  await expect(page.getByLabel("Selected attention pair").locator("strong")).toHaveText("+0.7000");
  await page.getByRole("button", { name: "Pin pair" }).click();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(2\)/);

  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const session = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(session.selection.headId).toBe("difference:L1H1:L1H0");
  const differencePin = session.pinnedItems.find(
    (item: { headId?: string }) => item.headId === "difference:L1H1:L1H0"
  );
  expect(differencePin).toMatchObject({
    metric: "attention_retained_head_difference",
    sourceKey: "derived.attention.difference[L1H1-L1H0]",
    provenance: { kind: "derived_proxy" },
    profile: { kind: "attention_source_profile", signed: true }
  });
  expect(differencePin.matrix).toBeUndefined();

  await page.reload();
  await expect(display.getByRole("radio", { name: "Difference" })).toHaveAttribute("aria-checked", "true");
  expect(new URL(page.url()).searchParams.get("head")).toBe("difference:L1H1:L1H0");
  await display.getByRole("radio", { name: "Difference" }).press("ArrowLeft");
  await expect(display.getByRole("radio", { name: "Head" })).toBeFocused();
  expect(new URL(page.url()).searchParams.get("head")).toBe("L1H1");
  await display.getByRole("radio", { name: "Head" }).press("ArrowRight");
  await expect(display.getByRole("radio", { name: "Difference" })).toBeFocused();
  expect(new URL(page.url()).searchParams.get("head")).toBe("difference:L1H1:L1H0");
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(2\)/);
  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const profilePlot = drawer.locator(".compare-profile-plot");
  await expect(profilePlot.getByRole("heading", { name: "Attention row difference" })).toBeVisible();
  const profileRow = profilePlot.getByLabel("Token profile differences").getByRole("listitem");
  await expect(profileRow).toHaveCount(1);
  await expect(profileRow).toContainText("11 aligned");
  await expect(profileRow).not.toHaveClass(/incompatible/);
  await expect(drawer.locator(".compare-matrix-difference")).toHaveCount(0);
  await drawer.getByLabel("Close evidence comparison").click();

  await page.setViewportSize({ width: 390, height: 844 });
  await controls.scrollIntoViewIfNeeded();
  for (const radio of await display.getByRole("radio").all()) {
    const box = await radio.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  for (const select of await controls.getByRole("combobox").all()) {
    const box = await select.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".attention-pattern-section")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await testInfo.attach("attention-head-difference-mobile", {
    body: await controls.screenshot(),
    contentType: "image/png"
  });
});

test("marks run-relative risk positions and explicit monitor hits on attention axes", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  const markerRun = {
    ...realRun,
    runId: "attention-marker-run",
    sampleId: "attention-marker-sample",
    tokens: realRun.tokens.map((token) =>
      token.index === 18 ? { ...token, monitorHit: true } : token
    )
  };
  await page.goto("/explorer?view=attention&token=10&source=1&target=10&layer=1&head=L1H0");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "attention-markers.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(markerRun))
  });
  await page.getByRole("tab", { name: "Attention", exact: true }).click();

  const rail = page.locator(".attention-risk-markers");
  await expect(rail.getByRole("heading", { name: "Risk-position markers" })).toBeVisible();
  await expect(rail).toContainText("Top 3 run-relative safety proxy positions");
  await expect(rail).toContainText("1 monitor hit");
  const items = rail.getByRole("listitem");
  await expect(items).toHaveCount(4);
  await expect(items.nth(0)).toContainText("T10");
  await expect(items.nth(0)).toContainText("proxy #1 · 1.000");
  await expect(items.nth(1)).toContainText("T17");
  await expect(items.nth(1)).toContainText("proxy #2 · 0.881");
  await expect(items.nth(2)).toContainText("T1");
  await expect(items.nth(2)).toContainText("proxy #3 · 0.846");
  await expect(items.nth(3)).toContainText("T18");
  await expect(items.nth(3)).toContainText("outside proxy top 3 · explicit monitor hit");

  const sourceRisk = page.locator('.attention-source-label[data-marker-token="10"]');
  const destinationRisk = page.locator('.attention-destination-label[data-marker-token="10"]');
  const sourceMonitor = page.locator('.attention-source-label[data-marker-token="18"]');
  const destinationMonitor = page.locator('.attention-destination-label[data-marker-token="18"]');
  await expect(sourceRisk).toContainText("R1");
  await expect(destinationRisk).toContainText("R1");
  await expect(sourceRisk).toHaveAttribute("title", /run-relative safety proxy rank 1, score 1\.000/);
  await expect(sourceMonitor).toContainText("M");
  await expect(destinationMonitor).toContainText("M");
  await expect(sourceMonitor).toHaveAttribute("title", /explicit monitor hit/);

  await rail.getByRole("button", { name: /Use token 17 .* as attention source/ }).click();
  await expect(page).toHaveURL(/source=17/);
  await expect(page).toHaveURL(/target=17/);
  await rail.getByRole("button", { name: /Use token 10 .* as attention destination/ }).click();
  await expect(page).toHaveURL(/source=10/);
  await expect(page).toHaveURL(/target=10/);
  await expect(rail.getByRole("button", { name: /Use token 10 .* as attention source/ }))
    .toHaveAttribute("aria-pressed", "true");
  await expect(rail.getByRole("button", { name: /Use token 10 .* as attention destination/ }))
    .toHaveAttribute("aria-pressed", "true");
  await rail.getByRole("button", { name: /Use token 18 .* as attention destination/ }).click();
  await expect(page).toHaveURL(/source=10/);
  await expect(page).toHaveURL(/target=18/);

  const accessibility = await new AxeBuilder({ page })
    .include(".attention-risk-markers")
    .include(".attention-matrix-scroll")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);

  await page.setViewportSize({ width: 390, height: 844 });
  await rail.scrollIntoViewIfNeeded();
  const actionBox = await rail.getByRole("button").first().boundingBox();
  expect(actionBox).not.toBeNull();
  expect(actionBox!.width).toBeGreaterThanOrEqual(44);
  expect(actionBox!.height).toBeGreaterThanOrEqual(44);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await testInfo.attach("attention-risk-position-markers-mobile", {
    body: await rail.screenshot(),
    contentType: "image/png"
  });
  await page.emulateMedia({ forcedColors: "active" });
  await expect(items.first()).toHaveCSS("forced-color-adjust", "none");
});

test("switches between incoming rows and outgoing attention columns", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto(
    "/?view=attention&token=10&source=1&target=10&layer=1&head=L1H0&edge=incoming"
  );

  const head = realRun.attentionHeads.find((candidate) => candidate.id === "L1H0")!;
  const profile = page.locator(".attention-edge-profile");
  const direction = profile.getByRole("radiogroup", { name: "Attention edge direction" });
  const incoming = direction.getByRole("radio", { name: "Incoming" });
  const outgoing = direction.getByRole("radio", { name: "Outgoing" });
  await expect(incoming).toHaveAttribute("aria-checked", "true");
  expect(new URL(page.url()).searchParams.get("edge")).toBe("incoming");
  await expect(profile).toContainText("Incoming sources for destination D10");

  const incomingRail = profile.getByRole("radiogroup", { name: "Incoming source token profile" });
  await expect(incomingRail.getByRole("radio")).toHaveCount(11);
  const selectedIncoming = incomingRail.getByRole("radio", { name: /Source token 1 / });
  await expect(selectedIncoming).toHaveAttribute("aria-checked", "true");
  const incomingValues = head.distributionByToken[10].slice(0, 11);
  const incomingTotal = incomingValues.reduce((sum, value) => sum + value, 0);
  const incomingPeak = incomingValues.reduce(
    (peak, value, index, values) => Math.abs(value) > Math.abs(values[peak]) ? index : peak,
    0
  );
  const summary = profile.getByLabel("Attention edge profile summary");
  await expect(summary).toContainText(incomingTotal.toFixed(4));
  await expect(summary).toContainText(`T${incomingPeak} · ${incomingValues[incomingPeak].toFixed(4)}`);
  await expect(summary).toContainText(head.distributionByToken[10][1].toFixed(4));
  const rawEntropy = (() => {
    const total = incomingValues.reduce((sum, value) => sum + value, 0);
    return incomingValues.reduce((entropy, value) => {
      const probability = value / total;
      return probability > 0 ? entropy - probability * Math.log(probability) : entropy;
    }, 0);
  })();
  const rawPairDetails = page.getByLabel("Attention pair details");
  await expect(rawPairDetails).toContainText(`${rawEntropy.toFixed(3)} nats`);
  await expect(rawPairDetails).toContainText("destination row entropy");
  await expect(rawPairDetails).toContainText("#2 / 11");
  await expect(rawPairDetails).toContainText("selected pair");

  await incoming.focus();
  await incoming.press("ArrowRight");
  await expect(outgoing).toBeFocused();
  await expect(outgoing).toHaveAttribute("aria-checked", "true");
  expect(new URL(page.url()).searchParams.get("edge")).toBe("outgoing");
  await expect(profile).toContainText("Outgoing destinations for source S1");

  const outgoingRail = profile.getByRole("radiogroup", { name: "Outgoing destination token profile" });
  await expect(outgoingRail.getByRole("radio")).toHaveCount(realRun.tokens.length - 1);
  const selectedOutgoing = outgoingRail.getByRole("radio", { name: /Destination token 10 / });
  await expect(selectedOutgoing).toHaveAttribute("aria-checked", "true");
  await selectedOutgoing.focus();
  await selectedOutgoing.press("ArrowRight");
  const destinationEleven = outgoingRail.getByRole("radio", { name: /Destination token 11 / });
  await expect(destinationEleven).toBeFocused();
  await expect(destinationEleven).toHaveAttribute("aria-checked", "true");
  await expect(page).toHaveURL(/source=1/);
  await expect(page).toHaveURL(/target=11/);
  await destinationEleven.press("End");
  await expect(page).toHaveURL(/target=19/);
  await expect(outgoingRail.getByRole("radio", { name: /Destination token 19 / })).toBeFocused();

  const downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const session = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(session.selection.attentionEdgeMode).toBe("outgoing");

  await page.reload();
  await expect(outgoing).toHaveAttribute("aria-checked", "true");
  expect(new URL(page.url()).searchParams.get("edge")).toBe("outgoing");
  await expect(page).toHaveURL(/target=19/);

  await page.setViewportSize({ width: 390, height: 844 });
  await profile.scrollIntoViewIfNeeded();
  for (const mode of await direction.getByRole("radio").all()) {
    const box = await mode.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  const selectedMobilePoint = profile.locator('.attention-edge-token-rail button[aria-checked="true"]');
  const pointBox = await selectedMobilePoint.boundingBox();
  const railBox = await profile.locator(".attention-edge-token-rail").boundingBox();
  expect(pointBox).not.toBeNull();
  expect(railBox).not.toBeNull();
  expect(pointBox!.width).toBeGreaterThanOrEqual(44);
  expect(pointBox!.height).toBeGreaterThanOrEqual(44);
  expect(pointBox!.x).toBeGreaterThanOrEqual(railBox!.x);
  expect(pointBox!.x + pointBox!.width).toBeLessThanOrEqual(railBox!.x + railBox!.width);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".attention-edge-profile")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await testInfo.attach("attention-outgoing-edge-profile-mobile", {
    body: await profile.screenshot(),
    contentType: "image/png"
  });
});

test("keeps DOM matrix row and column headings visible while scrolling", async ({ page }) => {
  const layers = Array.from({ length: 80 }, (_, index) => index);
  const tokens = realRun.tokens.map((token, index) => index === 0
    ? { ...token, text: " extraordinarily-long-token-fragment-for-axis-validation", tokenId: 98_765 }
    : token
  );
  const run = {
    ...realRun,
    runId: "dom-sticky-axis-run",
    sampleId: "dom-sticky-axis-sample",
    prompt: "DOM sticky axis validation sample",
    tokens,
    layers,
    residualCells: layers.flatMap((layer) => tokens.map((token) => ({
      ...realRun.residualCells[token.index % realRun.residualCells.length],
      layer,
      tokenIndex: token.index,
      rawDirection: ((layer + token.index) % 31) / 15 - 1,
      riskDirection: ((layer + token.index) % 29) / 28
    })))
  };
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({ json: remoteIndex(run, "dom-sticky-axis.explorer.json") });
  });
  await page.route(
    /\/api\/runs\/dom-sticky-axis-run\/samples\/dom-sticky-axis-sample$/,
    async (route) => route.fulfill({ json: run })
  );

  await page.goto(
    "/?run=dom-sticky-axis-run&sample=dom-sticky-axis-sample&view=residual&layer=40&token=0"
  );
  await expect(page.getByLabel("Prompt runner text"))
    .toHaveValue("DOM sticky axis validation sample");
  await expect(page.getByLabel("Matrix rendering status")).toContainText("dom");
  const matrixScroll = page.locator(".matrix-scroll");
  await matrixScroll.scrollIntoViewIfNeeded();
  const firstColumn = page.locator(".matrix-column-label").first();
  await expect(firstColumn).toHaveAttribute(
    "title",
    " extraordinarily-long-token-fragment-for-axis-validation · token 0 · id 98765"
  );

  async function assertStickyAxes() {
    await matrixScroll.evaluate((element) => {
      element.scrollLeft = 180;
      element.scrollTop = 640;
    });
    await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBe(640);
    const viewportBox = await matrixScroll.boundingBox();
    const cornerBox = await page.locator(".matrix-corner").boundingBox();
    const columnBox = await page.locator(".matrix-column-label").nth(10).boundingBox();
    const rowBox = await page.locator(".matrix-row-label").filter({ hasText: "L20" }).boundingBox();
    expect(viewportBox).not.toBeNull();
    expect(cornerBox).not.toBeNull();
    expect(columnBox).not.toBeNull();
    expect(rowBox).not.toBeNull();
    expect(Math.abs(cornerBox!.x - viewportBox!.x)).toBeLessThanOrEqual(2);
    expect(Math.abs(cornerBox!.y - viewportBox!.y)).toBeLessThanOrEqual(2);
    expect(Math.abs(columnBox!.y - viewportBox!.y)).toBeLessThanOrEqual(2);
    expect(Math.abs(rowBox!.x - viewportBox!.x)).toBeLessThanOrEqual(2);
    expect(rowBox!.y).toBeGreaterThanOrEqual(columnBox!.y + columnBox!.height - 2);
  }

  await assertStickyAxes();
  await page.setViewportSize({ width: 390, height: 844 });
  await matrixScroll.scrollIntoViewIfNeeded();
  await assertStickyAxes();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});

test("brushes a token range directly on the matrix", async ({ page }) => {
  await page.goto("/explorer?view=residual&token=10&layer=1");

  const cells = page.locator(".matrix-cell");
  await cells.nth(8).scrollIntoViewIfNeeded();
  const start = await cells.nth(8).boundingBox();
  const end = await cells.nth(12).boundingBox();
  expect(start).not.toBeNull();
  expect(end).not.toBeNull();

  await page.mouse.move(start!.x + start!.width / 2, start!.y + start!.height / 2);
  await page.mouse.down();
  await page.mouse.move(end!.x + end!.width / 2, end!.y + end!.height / 2, { steps: 8 });
  await page.mouse.up();

  await expect(page.getByText("Token range 8–12")).toBeVisible();
  await expect(page).toHaveURL(/range=8-12/);
});

test("uses registered compact and exact precision across evidence surfaces", async ({ page }) => {
  expect(formatMetricNumber(0.12345678, "attention_probability", "compact")).toBe("0.1235");
  expect(formatMetricNumber(0.12345678, "attention_probability", "exact")).toBe("0.123457");
  expect(formatMetricNumber(50, "patching_recovery", "compact")).toBe("50.0");
  expect(formatMetricNumber(-0, "residual_direction", "exact")).toBe("0.000000");
  expect(formatMetricNumber(0.0000000042, "integrated_gradients", "exact")).toBe("4.200000e-9");
  expect(formatMetricDelta(0.125, "nla_cosine", "compact")).toBe("+0.1250");
  expect(metricDisplayLabel("patching_effect")).toBe("causal effect");

  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=residual&token=10&layer=1&metric=residual_direction&normalization=raw");
  const residual = realRun.residualCells.find((cell) => cell.layer === 1 && cell.tokenIndex === 10)!;
  const compact = formatMetricNumber(residual.rawDirection, "residual_direction", "compact");
  const exact = formatMetricNumber(residual.rawDirection, "residual_direction", "exact");

  const cell = page.locator('.matrix-cell[data-row="1"][data-column="10"]');
  await cell.focus();
  await expect(page.locator(".matrix-tooltip")).toContainText(exact);
  const inspector = page.getByRole("region", { name: "Evidence inspector" });
  await expect(inspector.getByText(exact, { exact: true })).toHaveCount(3);

  await page.getByRole("button", { name: "Pin current evidence" }).click();
  const pin = page.locator(".pinned-strip-items button").filter({ hasText: "Residual" });
  await expect(pin).toContainText(`direction alignment ${compact}`);
  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const residualCard = drawer.locator(".compare-card").filter({ hasText: "direction alignment" });
  await expect(residualCard.locator(".compare-value strong")).toHaveText(compact);
  await expect(residualCard.locator(".compare-context")).toContainText("direction alignment");
});

test("brushes and synchronizes token ranges across specialized matrices", async ({ page }) => {
  await page.goto("/explorer?view=attention&token=10&source=8&layer=1");

  async function dragBetween(startSelector: string, endSelector: string) {
    const startLocator = page.locator(startSelector);
    const endLocator = page.locator(endSelector);
    await startLocator.scrollIntoViewIfNeeded();
    const start = await startLocator.boundingBox();
    const end = await endLocator.boundingBox();
    expect(start).not.toBeNull();
    expect(end).not.toBeNull();
    await page.mouse.move(start!.x + start!.width / 2, start!.y + start!.height / 2);
    await page.mouse.down();
    await page.mouse.move(end!.x + end!.width / 2, end!.y + end!.height / 2, { steps: 8 });
    await page.mouse.up();
  }

  await dragBetween(
    '.attention-source-label[data-range-token="8"]',
    '.attention-source-label[data-range-token="12"]'
  );
  await expect(page.getByLabel("Source token range summary")).toContainText("8–12");
  await expect(page).toHaveURL(/range=8-12/);

  await page.getByRole("tab", { name: "MLP", exact: true }).click();
  await expect(page.getByLabel("Token range summary")).toContainText("8–12");
  await expect(page.locator(".mlp-token-label.in-range")).toHaveCount(5);
  await page.getByLabel("Clear token range").click();
  await expect(page).not.toHaveURL(/range=/);

  const matrices = [
    {
      view: "MLP",
      start: '.mlp-token-label[data-range-token="6"]',
      end: '.mlp-token-label[data-range-token="10"]'
    },
    {
      view: "Attribution",
      start: '.attribution-token-label[data-range-token="6"]',
      end: '.attribution-token-label[data-range-token="10"]'
    }
  ];
  for (const matrix of matrices) {
    await page.getByRole("tab", { name: matrix.view, exact: true }).click();
    await dragBetween(matrix.start, matrix.end);
    await expect(page.getByLabel("Token range summary")).toContainText("6–10");
    await expect(page).toHaveURL(/range=6-10/);
    await page.getByLabel("Clear token range").click();
  }

  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  const attentionControls = page.getByLabel("Attention matrix controls", { exact: true });
  await attentionControls.getByLabel("Pan attention matrix").click();
  await dragBetween(
    '.attention-source-label[data-range-token="6"]',
    '.attention-source-label[data-range-token="10"]'
  );
  await expect(page).not.toHaveURL(/range=/);

  await attentionControls.getByLabel("Select attention matrix cells").click();
  await dragBetween(
    '.attention-source-label[data-range-token="8"]',
    '.attention-source-label[data-range-token="12"]'
  );
  await page.setViewportSize({ width: 390, height: 844 });
  const clear = page.getByLabel("Clear source token range");
  await clear.scrollIntoViewIfNeeded();
  const clearBox = await clear.boundingBox();
  expect(clearBox?.width).toBe(44);
  expect(clearBox?.height).toBe(44);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await clear.click();
  await page.evaluate(() => {
    const start = document.querySelector<HTMLElement>('.attention-source-label[data-range-token="8"]');
    const end = document.querySelector<HTMLElement>('.attention-source-label[data-range-token="12"]');
    if (!start || !end) throw new Error("Touch range fixtures unavailable");
    const startBox = start.getBoundingClientRect();
    const endBox = end.getBoundingClientRect();
    const event = (type: string, target: HTMLElement, box: DOMRect) => target.dispatchEvent(
      new PointerEvent(type, {
        bubbles: true,
        pointerId: 77,
        pointerType: "touch",
        button: 0,
        clientX: box.x + box.width / 2,
        clientY: box.y + box.height / 2
      })
    );
    event("pointerdown", start, startBox);
    event("pointermove", end, endBox);
    event("pointerup", end, endBox);
  });
  await expect(page).not.toHaveURL(/range=/);
});

test("navigates, anchors, and pins exact matrix cells with keyboard modifiers", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=residual&token=10&layer=1&metric=residual_direction");

  const selected = page.locator('.matrix-cell[data-row="1"][data-column="10"]');
  await selected.focus();
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(/token=9/);
  await expect(page.locator('.matrix-cell[data-row="1"][data-column="9"]')).toBeFocused();
  await page.keyboard.press("ArrowUp");
  await expect(page).toHaveURL(/layer=0/);
  await expect(page.locator('.matrix-cell[data-row="0"][data-column="9"]')).toBeFocused();
  await expect(page.locator('.matrix-cell[tabindex="0"]')).toHaveCount(1);

  const anchor = page.locator('.matrix-cell[data-row="1"][data-column="12"]');
  await anchor.click({ modifiers: ["Shift"] });
  await expect(page.getByLabel("Matrix selection summary")).toContainText("L1 · token 12");
  await expect(anchor).toHaveClass(/comparison/);
  await expect(page).toHaveURL(/token=9/);

  const compareTrigger = page.getByLabel(/^Compare pinned evidence/);
  await expect(compareTrigger).toHaveAttribute("aria-label", /\(3\)/);
  await page.locator('.matrix-cell[data-row="0"][data-column="5"]').click({
    modifiers: ["Control"]
  });
  await expect(compareTrigger).toHaveAttribute("aria-label", /\(4\)/);
  await compareTrigger.click();
  await expect(page.getByRole("dialog").getByText("token 5")).toBeVisible();
});

test("pans an enlarged matrix and fits it back to the viewport", async ({ page }) => {
  await page.goto("/explorer?view=residual&token=10&layer=1");
  const controls = page.getByLabel("Matrix controls");
  for (let index = 0; index < 9; index += 1) {
    await controls.getByLabel("Zoom in").click();
  }
  const viewport = page.locator(".matrix-scroll");
  const dimensions = await viewport.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth
  }));
  expect(dimensions.scrollWidth).toBeGreaterThan(dimensions.clientWidth);

  await controls.getByLabel("Pan matrix").click();
  await viewport.scrollIntoViewIfNeeded();
  const box = await viewport.boundingBox();
  expect(box).not.toBeNull();
  await page.mouse.move(box!.x + box!.width * 0.72, box!.y + box!.height * 0.65);
  await page.mouse.down();
  await page.mouse.move(box!.x + box!.width * 0.28, box!.y + box!.height * 0.65, { steps: 8 });
  await page.mouse.up();
  expect(await viewport.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);

  await controls.getByLabel("Fit matrix to width").click();
  await expect.poll(() => viewport.evaluate((element) => element.scrollLeft)).toBe(0);
  await expect(controls.getByLabel("Pin matrix axes")).toHaveAttribute("aria-pressed", "true");
});

test("keeps viewport controls consistent across specialized matrices", async ({ page }) => {
  await page.goto("/explorer?view=attention&token=10&source=9&layer=1");
  const matrices = [
    {
      view: "Attention",
      controls: "Attention matrix controls",
      label: "attention matrix",
      viewport: ".attention-matrix-scroll"
    },
    {
      view: "MLP",
      controls: "MLP matrix controls",
      label: "MLP matrix",
      viewport: ".mlp-matrix-scroll"
    },
    {
      view: "Attribution",
      controls: "Attribution matrix controls",
      label: "attribution matrix",
      viewport: ".attribution-matrix-scroll"
    }
  ];

  for (const matrix of matrices) {
    await page.getByRole("tab", { name: matrix.view, exact: true }).click();
    const controls = page.getByLabel(matrix.controls, { exact: true });
    await expect(controls.getByLabel(`Select ${matrix.label} cells`)).toHaveAttribute(
      "aria-pressed",
      "true"
    );
    await expect(controls.getByLabel(`Pin ${matrix.label} axes`)).toHaveAttribute(
      "aria-pressed",
      "true"
    );
    await controls.getByLabel(`Pan ${matrix.label}`).click();
    await expect(controls.getByLabel(`Pan ${matrix.label}`)).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator(matrix.viewport)).toHaveClass(/pan-mode/);
    await controls.getByLabel(`Fit ${matrix.label} to width`).click();
    await controls.getByLabel(`Reset ${matrix.label} view`).click();
    await expect(controls.getByLabel(`Select ${matrix.label} cells`)).toHaveAttribute(
      "aria-pressed",
      "true"
    );
  }
});

test("shows complete token metadata from specialized matrix headers and keyboard focus", async ({ page }, testInfo) => {
  const tokenText = " extraordinarily-long-specialized-token-metadata-fragment";
  const tokenId = 98_765;
  const selectedNeuron = realRun.mlpNeurons.find((neuron) => neuron.layer === 1)
    ?? realRun.mlpNeurons[0]!;
  const run = {
    ...realRun,
    runId: "specialized-token-metadata-run",
    sampleId: "specialized-token-metadata-sample",
    prompt: "Specialized token metadata validation sample",
    tokens: realRun.tokens.map((token) => token.index === 10
      ? { ...token, text: tokenText, tokenId }
      : token),
    nla: [{
      ...realRun.nla[0],
      layer: 1,
      component: "resid_post" as const,
      tokenIndex: 10,
      token: tokenText,
      status: "available" as const
    }]
  };
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({ json: remoteIndex(run, "specialized-token-metadata.explorer.json") });
  });
  await page.route(
    /\/api\/runs\/specialized-token-metadata-run\/samples\/specialized-token-metadata-sample$/,
    async (route) => route.fulfill({ json: run })
  );

  async function openView(query: string) {
    await page.goto(
      `/?run=specialized-token-metadata-run&sample=specialized-token-metadata-sample&${query}`
    );
    await expect(page.getByLabel("Prompt runner text"))
      .toHaveValue("Specialized token metadata validation sample");
  }

  await openView("view=attention&layer=1&token=10&source=10&target=10&head=L1H0");
  await expect(page.locator(".attention-source-label").nth(10)).toHaveAttribute(
    "title",
    new RegExp(`source position 10 · id ${tokenId} · text\\s+${tokenText.trim()}`)
  );
  await expect(page.locator(".attention-destination-label").nth(10)).toHaveAttribute(
    "title",
    new RegExp(`destination position 10 · id ${tokenId} · text\\s+${tokenText.trim()}`)
  );
  await page.locator(".attention-pattern-cell.selected").focus();
  await expect(page.locator(".attention-pattern-cell.selected"))
    .toHaveAttribute("aria-keyshortcuts", /Space/);
  await expect(page.locator(".attention-pair-tooltip")).toContainText(tokenText.trim());
  await expect(page.locator(".attention-pair-tooltip"))
    .toContainText(`source position 10 · id ${tokenId}`);
  await expect(page.locator(".attention-pair-tooltip"))
    .toContainText(`destination position 10 · id ${tokenId}`);
  await page.keyboard.press("Space");
  await expect(page.getByLabel("Compare pinned evidence (4)")).toBeVisible();

  await openView(`view=mlp&layer=1&token=10&neuron=${selectedNeuron.id}&metric=mlp_signed_activation`);
  await expect(page.locator(".mlp-token-label").nth(10)).toHaveAttribute(
    "title",
    `token position 10 · id ${tokenId} · text ${tokenText}`
  );
  await page.locator(".mlp-activation-cell.selected").focus();
  await expect(page.locator(".mlp-activation-cell.selected"))
    .toHaveAttribute("aria-keyshortcuts", /Space/);
  await expect(page.locator(".mlp-activation-tooltip")).toContainText(tokenText.trim());
  await expect(page.locator(".mlp-activation-tooltip"))
    .toContainText(`token position 10 · id ${tokenId}`);
  await page.keyboard.press("Space");
  await expect(page.getByLabel("Compare pinned evidence (4)")).toBeVisible();

  await openView(
    "view=attribution&layer=1&token=10&track=residual_direction&metric=residual_direction&normalization=raw"
  );
  await expect(page.locator(".attribution-token-label").nth(10)).toHaveAttribute(
    "title",
    `token position 10 · id ${tokenId} · text ${tokenText}`
  );
  await page.locator(".attribution-value-cell.selected").focus();
  await expect(page.locator(".attribution-value-cell.selected"))
    .toHaveAttribute("aria-keyshortcuts", /Space/);
  await expect(page.locator(".attribution-tooltip")).toContainText(tokenText.trim());
  await expect(page.locator(".attribution-tooltip"))
    .toContainText(`token position 10 · id ${tokenId}`);
  await page.keyboard.press("Space");
  await expect(page.getByLabel("Compare pinned evidence (4)")).toBeVisible();

  await openView("view=nla&layer=1&token=10&nlaComponent=resid_post&metric=nla_cosine");
  await expect(page.getByLabel("Pin selected NLA evidence")).toBeVisible();
  await expect(page.locator(".nla-token-label").nth(10)).toHaveAttribute(
    "title",
    `token position 10 · id ${tokenId} · text ${tokenText}`
  );
  await page.locator(".nla-fidelity-cell.selected").focus();
  await expect(page.locator(".nla-fidelity-cell.selected"))
    .toHaveAttribute("aria-keyshortcuts", /Space/);
  const nlaTooltip = page.locator(".nla-fidelity-tooltip");
  await expect(nlaTooltip).toContainText(tokenText.trim());
  await expect(nlaTooltip).toContainText(`token position 10 · id ${tokenId}`);
  await page.keyboard.press("Space");
  await expect(page.getByLabel("Compare pinned evidence (4)")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await nlaTooltip.scrollIntoViewIfNeeded();
  const tooltipBox = await nlaTooltip.boundingBox();
  expect(tooltipBox).not.toBeNull();
  expect(tooltipBox!.width).toBeLessThanOrEqual(358);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".nla-fidelity-section")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  const nlaPinBox = await page.getByLabel("Pin selected NLA evidence").boundingBox();
  expect(nlaPinBox?.width).toBeGreaterThanOrEqual(44);
  expect(nlaPinBox?.height).toBeGreaterThanOrEqual(44);
  await testInfo.attach("nla-keyboard-pin-mobile", {
    body: await page.locator(".nla-fidelity-section").screenshot(),
    contentType: "image/png"
  });

  await page.getByLabel("Compare pinned evidence (4)").click();
  const compareCards = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(compareCards.locator(".compare-card")).toHaveCount(4);
  await expect(compareCards.locator(".compare-card.compare-attention")).toHaveCount(1);
  await expect(compareCards.locator(".compare-card.compare-mlp")).toHaveCount(1);
  await expect(compareCards.locator(".compare-card.compare-attribution")).toHaveCount(1);
  await expect(compareCards.locator(".compare-card.compare-nla")).toHaveCount(1);
});

test("uses one keyboard entry point in every specialized matrix", async ({ page }) => {
  await page.goto("/explorer?view=attention&token=10&source=9&target=10&layer=1&head=L1H0");
  let cells = page.locator('.attention-pattern-cell[tabindex="0"]');
  await expect(cells).toHaveCount(1);
  await cells.focus();
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(/source=8/);
  await expect(page.locator('.attention-pattern-cell[data-source="8"][data-destination="10"]')).toBeFocused();
  await page.keyboard.press("Shift+Enter");
  await expect(page.getByLabel("Attention matrix selection summary")).toContainText("D10 · S8");
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(/source=7/);
  await page.keyboard.press("Control+Enter");
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; sourceTokenIndex?: number }) =>
      pin.view === "attention" && pin.tokenIndex === 10 && pin.sourceTokenIndex === 7
    );
  })).toBe(true);

  await page.getByRole("tab", { name: "MLP", exact: true }).click();
  cells = page.locator('.mlp-activation-cell[tabindex="0"]');
  await expect(cells).toHaveCount(1);
  await cells.focus();
  await page.keyboard.press("ArrowDown");
  await expect(page).toHaveURL(/token=11/);
  await expect(page.locator('.mlp-activation-cell[data-token="11"][tabindex="0"]')).toBeFocused();

  await page.getByRole("tab", { name: "Attribution", exact: true }).click();
  cells = page.locator('.attribution-value-cell[tabindex="0"]');
  await expect(cells).toHaveCount(1);
  await cells.focus();
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(/token=10/);
  await expect(page.locator('.attribution-value-cell[data-token="10"][tabindex="0"]')).toBeFocused();

  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  await expect(page.getByLabel("NLA results")).toContainText("No NLA artifact yet");
  await expect(page.getByLabel("Pin selected NLA evidence")).toHaveCount(0);
  const nlaCandidates = page.getByLabel("NLA cached candidates").getByRole("button");
  await expect(nlaCandidates).toHaveCount(3);
  await nlaCandidates.filter({ hasText: "strategy" }).click();
  await expect(page).toHaveURL(/token=11/);
  await expect(page).toHaveURL(/nlaComponent=mlp_out/);
});

test("shows real residual logit-lens predictions and trajectories by layer", async ({ page }, testInfo) => {
  await page.goto("/explorer?view=residual&token=10&layer=1&metric=residual_direction");

  const lens = page.getByLabel("Residual logit lens");
  await expect(lens).toBeVisible();
  await expect(lens.getByText("strategy", { exact: true }).first()).toBeVisible();
  await expect(lens.locator(".lens-layer")).toHaveCount(2);
  const trajectory = lens.getByRole("region", { name: "Target trajectory" });
  await expect(trajectory.locator("svg")).toHaveCount(2);
  await expect(trajectory.locator("path").first()).toHaveAttribute("d", /M.*L/);
  await expect(trajectory.locator("circle")).toHaveCount(4);
  await expect(trajectory.locator("circle.selected")).toHaveCount(2);
  await expect(trajectory).toContainText("rank path");
  await expect(trajectory).toContainText("best rank");

  const display = lens.getByRole("radiogroup", { name: "Logit lens display" });
  const logit = display.getByRole("radio", { name: "Logit" });
  const probability = display.getByRole("radio", { name: "Probability" });
  await probability.click();
  await expect(probability).toHaveAttribute("aria-checked", "true");
  await expect(trajectory.getByText("Target probability", { exact: true })).toBeVisible();
  await probability.press("ArrowLeft");
  await expect(logit).toBeFocused();
  await expect(logit).toHaveAttribute("aria-checked", "true");

  const layers = trajectory.getByRole("radiogroup", { name: "Logit lens trajectory layer" });
  const layerOne = layers.getByRole("radio", { name: /^Layer 1,/ });
  await layerOne.focus();
  await layerOne.press("Home");
  await expect(page).toHaveURL(/layer=0/);
  await expect(layers.getByRole("radio", { name: /^Layer 0,/ })).toBeFocused();
  await page.keyboard.press("End");
  await expect(page).toHaveURL(/layer=1/);
  await expect(layerOne).toBeFocused();

  const accessibility = await new AxeBuilder({ page })
    .include(".lens-trajectory")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await testInfo.attach("residual-target-trajectory-desktop", {
    body: await trajectory.screenshot(),
    contentType: "image/png"
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await trajectory.scrollIntoViewIfNeeded();
  for (const button of await layers.getByRole("radio").all()) {
    const box = await button.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeGreaterThanOrEqual(44);
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await testInfo.attach("residual-target-trajectory-mobile", {
    body: await trajectory.screenshot(),
    contentType: "image/png"
  });
});

test("filters, selects, and pins a signed MLP neuron activation", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=mlp&token=10&layer=1&metric=mlp_signed_activation");

  const controls = page.getByLabel("MLP matrix controls", { exact: true });
  await expect(controls).toBeVisible();
  await controls.getByPlaceholder("e.g. N0004 or 4").fill("N0004");
  await expect(page.locator(".mlp-neuron-label")).toHaveCount(1);
  await expect(page.getByLabel("Neuron search results")).toHaveText("1/8");
  await expect(page).toHaveURL(/neuron=L1N0004/);
  await expect(page.getByLabel("Selected MLP activation", { exact: true })).toContainText("L1N0004");
  await controls.getByLabel("Search retained neurons").fill("missing-neuron");
  await expect(page.getByLabel("Neuron search results")).toHaveText("0/8");
  await expect(page.getByText("No retained neuron matches “missing-neuron”.")).toBeVisible();
  await expect(page).toHaveURL(/neuron=L1N0004/);
  await controls.getByLabel("Search retained neurons").fill("N0004");
  await expect(page.getByLabel("Neuron search results")).toHaveText("1/8");

  const anchorCell = page.locator(
    '.mlp-activation-cell[data-token="8"][data-neuron="L1N0004"]'
  );
  await anchorCell.click({ modifiers: ["Shift"] });
  await expect(page).toHaveURL(/token=10/);
  await expect(page.getByLabel("MLP matrix selection summary")).toContainText("T8 · L1N0004");
  await expect(page.getByLabel("MLP matrix selection summary").locator("span").nth(2))
    .not.toContainText("n/a");
  await expect(anchorCell).toHaveClass(/comparison/);

  const directPinCell = page.locator(
    '.mlp-activation-cell[data-token="9"][data-neuron="L1N0004"]'
  );
  await directPinCell.click({ modifiers: ["Control"] });
  await expect(page).toHaveURL(/token=10/);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; neuronId?: string }) =>
      pin.view === "mlp" && pin.tokenIndex === 9 && pin.neuronId === "L1N0004"
    );
  })).toBe(true);

  const cell = page.locator(
    '.mlp-activation-cell[data-token="9"][data-neuron="L1N0004"]'
  );
  await cell.click();
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/neuron=L1N0004/);

  await controls.getByRole("combobox").selectOption("mlp_absolute_activation");
  await expect(page).toHaveURL(/metric=mlp_absolute_activation/);
  await expect(page).toHaveURL(/normalization=raw/);
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/neuron=L1N0004/);
  expect(await page.locator(".mlp-activation-cell.magnitude").count()).toBeGreaterThan(0);
  await expect(page.locator(".mlp-activation-cell.negative, .mlp-activation-cell.positive")).toHaveCount(0);
  const legend = page.getByLabel("MLP activation legend");
  await expect(legend).toHaveAttribute("data-domain", "sequential");
  await expect(legend).toContainText("absolute raw activation");
  await expect(legend).toContainText("sequential domain from zero");
  await expect(page.getByLabel("Selected MLP activation", { exact: true }))
    .toContainText("absolute raw activation");

  await controls.getByRole("combobox").selectOption("mlp_normalized_activation");
  await expect(page).toHaveURL(/metric=mlp_normalized_activation/);
  await expect(page).toHaveURL(/token=9/);
  await expect(page).toHaveURL(/neuron=L1N0004/);
  await expect(legend).toHaveAttribute("data-domain", "sequential");
  await expect(legend).toContainText("0.5000");
  await expect(legend).toContainText("1.0000");
  await expect(legend).toContainText("fixed 0–1 domain");

  await controls.getByRole("combobox").selectOption("mlp_signed_activation");
  await expect(page).toHaveURL(/metric=mlp_signed_activation/);
  await expect(page.locator(".mlp-activation-cell.magnitude")).toHaveCount(0);
  expect(await page.locator(".mlp-activation-cell.negative").count()).toBeGreaterThan(0);
  expect(await page.locator(".mlp-activation-cell.positive").count()).toBeGreaterThan(0);
  await expect(legend).toHaveAttribute("data-domain", "diverging");
  await expect(legend).toContainText("symmetric zero-centered domain");

  await controls.getByRole("combobox").selectOption("mlp_absolute_activation");
  await controls.locator('input[type="range"]').fill("0.5");
  expect(await page.locator(".mlp-activation-cell.filtered").count()).toBeGreaterThan(0);
  await expect(legend).toContainText("below");
  const axeResults = await new AxeBuilder({ page })
    .include(".mlp-matrix-section")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
  await testInfo.attach("mlp-absolute-sequential-domain", {
    body: await page.locator(".mlp-matrix-section").screenshot(),
    contentType: "image/png"
  });

  await page.getByLabel("Pin selected MLP activation").click();
  await page.getByLabel(/^Compare pinned evidence/).click();
  await expect(page.getByRole("dialog").getByText("neuron L1N0004")).toHaveCount(2);
});

test("navigates and compares retained MLP neuron activation profiles", async ({ page }, testInfo) => {
  await page.addInitScript(() => {
    if (window.sessionStorage.getItem("mlp-profile-test-started")) return;
    window.localStorage.clear();
    window.sessionStorage.setItem("mlp-profile-test-started", "true");
  });
  await page.goto("/explorer?view=mlp&token=10&layer=1&neuron=L1N0004&metric=mlp_signed_activation");

  await page.getByLabel(/^Compare pinned evidence/).click();
  const initialDrawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(initialDrawer).toBeVisible();
  await expect(initialDrawer.getByLabel(/^Remove .* from comparison$/).first()).toBeVisible();
  while (await initialDrawer.getByLabel(/^Remove .* from comparison$/).count()) {
    await initialDrawer.getByLabel(/^Remove .* from comparison$/).first().click();
  }
  await initialDrawer.getByLabel("Close evidence comparison").click();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(0\)/);

  const neuron = realRun.mlpNeurons.find((candidate) => candidate.id === "L1N0004")!;
  const profile = page.locator(".mlp-activation-profile");
  const rankings = page.locator(".mlp-neuron-rankings");
  const positiveRanking = page.getByRole("list", { name: "Top positive neurons" });
  const negativeRanking = page.getByRole("list", { name: "Top negative neurons" });
  const layerNeurons = realRun.mlpNeurons.filter((candidate) => candidate.layer === 1);
  const positiveExpected = layerNeurons
    .map((candidate) => ({ candidate, value: candidate.activationsByToken[10] }))
    .filter((entry) => entry.value > 0)
    .sort((left, right) => right.value - left.value)
    .slice(0, 5);
  const negativeExpected = layerNeurons
    .map((candidate) => ({ candidate, value: candidate.activationsByToken[10] }))
    .filter((entry) => entry.value < 0)
    .sort((left, right) => left.value - right.value)
    .slice(0, 5);
  await expect(rankings.getByRole("heading", { name: "Neuron polarity ranking" })).toBeVisible();
  await expect(positiveRanking.getByRole("listitem")).toHaveCount(positiveExpected.length);
  await expect(negativeRanking.getByRole("listitem")).toHaveCount(negativeExpected.length);
  await expect(positiveRanking.getByRole("listitem").first()).toContainText(positiveExpected[0].candidate.id);
  await expect(positiveRanking.getByRole("listitem").first()).toContainText(positiveExpected[0].value.toFixed(4));
  await expect(negativeRanking.getByRole("listitem").first()).toContainText(negativeExpected[0].candidate.id);

  const search = page.getByLabel("MLP matrix controls", { exact: true }).getByLabel("Search retained neurons");
  await search.fill("N0004");
  await expect(page.locator(".mlp-neuron-label")).toHaveCount(1);
  await positiveRanking.getByRole("button").first().click();
  await expect(search).toHaveValue("");
  await expect(page).toHaveURL(new RegExp(`neuron=${positiveExpected[0].candidate.id}`));
  await expect(page.locator(".mlp-neuron-label")).toHaveCount(layerNeurons.length);
  await expect(profile).toContainText(`${positiveExpected[0].candidate.id} across the retained token axis`);

  if (positiveExpected.length > 1) {
    const firstPositive = positiveRanking.getByRole("button").first();
    await firstPositive.focus();
    await firstPositive.press("ArrowRight");
    const secondPositive = positiveRanking.getByRole("button").nth(1);
    await expect(secondPositive).toBeFocused();
    await expect(secondPositive).toHaveAttribute("aria-pressed", "true");
    await expect(page).toHaveURL(new RegExp(`neuron=${positiveExpected[1].candidate.id}`));
  }
  const restoreNeuron = negativeRanking.getByRole("button", { name: /^L1N0004,/ });
  await restoreNeuron.click();
  await expect(restoreNeuron).toHaveAttribute("aria-pressed", "true");
  await expect(page).toHaveURL(/neuron=L1N0004/);

  await expect(profile.getByRole("heading", { name: "Neuron activation profile" })).toBeVisible();
  await expect(profile).toContainText("L1N0004 across the retained token axis");
  await expect(profile).toContainText("signed raw activation");
  const path = await profile.locator(".mlp-profile-line").getAttribute("d");
  expect(path).toMatch(/^M /);
  expect(path).not.toContain("NaN");
  await expect(profile.locator(".mlp-profile-selected-point")).toHaveCount(1);

  const rail = profile.getByRole("radiogroup", { name: "Neuron activation profile tokens" });
  await expect(rail.getByRole("radio")).toHaveCount(realRun.tokens.length);
  const initiallySelected = rail.getByRole("radio", { name: /token 10,/ });
  await expect(initiallySelected).toHaveAttribute("aria-checked", "true");
  await expect(initiallySelected).toContainText(neuron.activationsByToken[10].toFixed(4));

  const positiveIndex = neuron.activationsByToken.reduce(
    (peak, value, index, values) => value > values[peak] ? index : peak,
    0
  );
  const positivePeak = profile.locator(".mlp-profile-stats button").first();
  await expect(positivePeak).toContainText(`positive peak · T${positiveIndex}`);
  await positivePeak.click();
  await expect(page).toHaveURL(new RegExp(`token=${positiveIndex}`));
  const peakRadio = rail.getByRole("radio", { name: new RegExp(`token ${positiveIndex},`) });
  await expect(peakRadio).toHaveAttribute("aria-checked", "true");

  const moveKey = positiveIndex === realRun.tokens.length - 1 ? "ArrowLeft" : "ArrowRight";
  const movedIndex = positiveIndex === realRun.tokens.length - 1 ? positiveIndex - 1 : positiveIndex + 1;
  await peakRadio.focus();
  await peakRadio.press(moveKey);
  const movedRadio = rail.getByRole("radio", { name: new RegExp(`token ${movedIndex},`) });
  await expect(movedRadio).toBeFocused();
  await expect(movedRadio).toHaveAttribute("aria-checked", "true");
  await expect(page).toHaveURL(new RegExp(`token=${movedIndex}`));

  await page.getByLabel("Pin selected MLP activation").click();
  const controls = page.getByLabel("MLP matrix controls", { exact: true });
  await controls.getByLabel("Search retained neurons").fill("N0005");
  await expect(page).toHaveURL(/neuron=L1N0005/);
  await expect(profile).toContainText("L1N0005 across the retained token axis");
  await page.getByLabel("Pin selected MLP activation").click();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(2\)/);

  await page.reload();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(2\)/);
  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const difference = drawer.locator(".compare-profile-plot");
  await expect(difference.getByRole("heading", { name: "MLP activation profile difference" })).toBeVisible();
  const comparisonRow = difference.getByLabel("Token profile differences").getByRole("listitem");
  await expect(comparisonRow).toHaveCount(1);
  await expect(comparisonRow).toContainText("20 aligned");
  await expect(comparisonRow).not.toHaveClass(/incompatible/);
  const differencePath = await comparisonRow.locator(".compare-profile-line").first().getAttribute("d");
  expect(differencePath).toMatch(/^M /);
  expect(differencePath).not.toContain("NaN");
  await drawer.getByLabel("Close evidence comparison").click();

  await page.setViewportSize({ width: 390, height: 844 });
  await profile.scrollIntoViewIfNeeded();
  const selectedMobileToken = profile.locator('.mlp-profile-token-rail button[aria-checked="true"]');
  const mobileBox = await selectedMobileToken.boundingBox();
  const railBox = await profile.locator(".mlp-profile-token-rail").boundingBox();
  const mobileRankedNeuron = positiveRanking.getByRole("button").first();
  const rankedBox = await mobileRankedNeuron.boundingBox();
  expect(mobileBox).not.toBeNull();
  expect(railBox).not.toBeNull();
  expect(rankedBox).not.toBeNull();
  expect(mobileBox!.width).toBeGreaterThanOrEqual(44);
  expect(mobileBox!.height).toBeGreaterThanOrEqual(44);
  expect(rankedBox!.height).toBeGreaterThanOrEqual(44);
  expect(mobileBox!.x).toBeGreaterThanOrEqual(railBox!.x);
  expect(mobileBox!.x + mobileBox!.width).toBeLessThanOrEqual(railBox!.x + railBox!.width);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const axeResults = await new AxeBuilder({ page })
    .include(".mlp-activation-profile")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
  await testInfo.attach("mlp-activation-profile-mobile", {
    body: await profile.screenshot(),
    contentType: "image/png"
  });
});

test("clusters retained MLP activation profiles with signed Pearson orientation", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const ramp = realRun.tokens.map((_, index) => index - (realRun.tokens.length - 1) / 2);
  const makeNeuron = (id: number, profile: number[]) => ({
    id: `L1N${String(id).padStart(4, "0")}`,
    layer: 1,
    neuron: id,
    label: `Retained neuron ${id}`,
    activation: profile[10] ?? 0,
    riskContribution: 0,
    topTokens: [],
    positiveTopTokens: [],
    negativeTopTokens: [],
    activationsByToken: profile,
    maxAbsoluteActivation: Math.max(...profile.map((value) => Math.abs(value)))
  });
  const clusterRun: ExplorerRun = {
    ...realRun,
    runId: "mlp-cluster-run",
    sampleId: "mlp-cluster-sample",
    mlpNeurons: [
      makeNeuron(100, ramp),
      makeNeuron(101, ramp.map((value) => value * 2)),
      makeNeuron(102, ramp.map((value) => -value)),
      makeNeuron(103, ramp.map((_, index) => index % 2 === 0 ? 1 : -1))
    ]
  };

  await page.goto("/explorer?view=mlp&token=10&layer=1&neuron=L1N0100");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "mlp-clusters.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(clusterRun))
  });
  await page.getByRole("tab", { name: "MLP", exact: true }).click();

  const clusters = page.getByLabel("MLP neuron profile clusters");
  await expect(clusters.getByRole("group")).toHaveCount(2);
  await expect(page.getByLabel("MLP cluster coverage")).toContainText("4/4retained neurons clustered");
  await expect(page.getByLabel("MLP cluster coverage")).toContainText("20/20full token axis");
  await expect(page.getByLabel("MLP cluster coverage")).toContainText("completecoverage mode");
  const selectedCluster = page.locator(".mlp-cluster-row.selected");
  await expect(selectedCluster).toContainText("3 neurons");
  await expect(selectedCluster.getByRole("button").filter({ hasText: "L1N0100" })).toContainText("+1.000");
  await expect(selectedCluster.getByRole("button").filter({ hasText: "L1N0101" })).toContainText("+1.000");
  const inverse = selectedCluster.getByRole("button").filter({ hasText: "L1N0102" });
  await expect(inverse).toContainText("-1.000inverse");
  await expect(clusters.getByRole("group").filter({ hasText: "L1N0103" })).toContainText("1 neuron");

  await inverse.click();
  await expect(page).toHaveURL(/neuron=L1N0102/);
  await expect(page.getByLabel("Selected MLP activation", { exact: true })).toContainText("L1N0102");
  const selectedMember = page.locator('.mlp-cluster-members button[aria-pressed="true"]');
  await selectedMember.focus();
  await selectedMember.press("ArrowLeft");
  await expect(page).toHaveURL(/neuron=L1N0101/);
  await expect(page.locator('[data-cluster-neuron="L1N0101"]')).toBeFocused();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator(".mlp-cluster-explorer").scrollIntoViewIfNeeded();
  for (const button of await page.locator(".mlp-cluster-members button").all()) {
    const box = await button.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".mlp-cluster-explorer")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);

  const sampledRun: ExplorerRun = {
    ...clusterRun,
    runId: "mlp-cluster-sampled-run",
    sampleId: "mlp-cluster-sampled-sample",
    mlpNeurons: Array.from({ length: 70 }, (_, index) =>
      makeNeuron(index, ramp.map((value) => value * (1 + index / 100)))
    )
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "mlp-clusters-sampled.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(sampledRun))
  });
  await page.getByRole("tab", { name: "MLP", exact: true }).click();
  await expect(page.getByLabel("MLP cluster coverage")).toContainText("64/70retained neurons clustered");
  await expect(page.getByLabel("MLP cluster coverage")).toContainText("sampledcoverage mode");
  await expect(page.getByLabel("MLP neuron profile clusters").getByRole("group")).toHaveCount(1);
});

test("pins and restores a complete evidence context", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  await page.getByRole("tab", { name: "Residual", exact: true }).click();
  await page.getByRole("button", { name: "Pin current evidence" }).click();

  const residualPin = page.locator(".pinned-strip button").filter({ hasText: "Residual" });
  await expect(residualPin).toBeVisible();

  await page.getByRole("tab", { name: "MLP", exact: true }).click();
  await expect(page).toHaveURL(/view=mlp/);
  await residualPin.click();
  await expect(page).toHaveURL(/view=residual/);
  await expect(page).toHaveURL(/metric=residual_direction/);
});

test("restores the pinned attribution track", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  await page.getByRole("tab", { name: "Attribution", exact: true }).click();
  const methods = page.getByLabel("Attribution methods");
  await methods.getByRole("button").filter({ hasText: "Token safety proxy" }).click();
  await page.getByLabel("Pin selected attribution").click();

  const attentionMethod = methods.getByRole("button").filter({ hasText: "Final-token attention" });
  await attentionMethod.click();
  await expect(attentionMethod).toHaveClass(/active/);
  await page.locator(".pinned-strip-items button").filter({ hasText: "Attribution" }).click();

  await expect(methods.getByRole("button").filter({ hasText: "Token safety proxy" })).toHaveClass(/active/);
  await expect(page).toHaveURL(/track=token_safety_proxy/);
});

test("separates signed attribution from unavailable methods", async ({ page }) => {
  await page.goto(
    "/?view=attribution&token=10&layer=1&track=residual_direction&metric=residual_direction&normalization=raw"
  );

  const controls = page.getByLabel("Attribution matrix controls");
  await expect(controls).toBeVisible();
  expect(await page.locator(".attribution-value-cell.positive").count()).toBeGreaterThan(0);
  expect(await page.locator(".attribution-value-cell.negative").count()).toBeGreaterThan(0);

  const anchorCell = page.locator('.attribution-value-cell[data-layer="0"][data-token="9"]');
  await anchorCell.click({ modifiers: ["Shift"] });
  await expect(page).toHaveURL(/layer=1/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page.getByLabel("Attribution matrix selection summary")).toContainText("L0 · T9");
  await expect(page.getByLabel("Attribution matrix selection summary").locator("span").nth(2))
    .not.toContainText("n/a");
  await expect(anchorCell).toHaveClass(/comparison/);

  await page.locator('.attribution-value-cell[data-layer="0"][data-token="8"]')
    .click({ modifiers: ["Control"] });
  await expect(page).toHaveURL(/layer=1/);
  await expect(page).toHaveURL(/token=10/);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; layer?: number; sourceKey?: string }) =>
      pin.view === "attribution" && pin.tokenIndex === 8 && pin.layer === 0 && pin.sourceKey?.startsWith("layer_0.resid_post")
    );
  })).toBe(true);

  await page.locator('.attribution-value-cell[data-layer="0"][data-token="9"]').click();
  await expect(page).toHaveURL(/layer=0/);
  await expect(page).toHaveURL(/token=9/);
  await controls.getByRole("button", { name: "Normalized", exact: true }).click();
  await expect(page).toHaveURL(/normalization=normalized/);

  await controls.getByRole("combobox").selectOption("integrated_gradients");
  await expect(page.getByRole("region", { name: "Integrated Gradients is not available for this run" }))
    .toContainText("Configure Integrated Gradients");
  await expect(page.getByLabel("Pin selected attribution")).toBeDisabled();
  await expect(page).toHaveURL(/track=integrated_gradients/);
  await expect(page).toHaveURL(/metric=integrated_gradients/);
});

test("audits attribution balance and compares method snapshots without cross-scale deltas", async ({ page }) => {
  await page.goto(
    "/?view=attribution&token=10&layer=1&track=residual_direction&metric=residual_direction&normalization=raw"
  );

  const methods = page.getByLabel("Attribution methods");
  await expect(methods.getByRole("button")).toHaveCount(4);
  await expect(methods.getByRole("button").filter({ hasText: "Residual direction projection" }))
    .toContainText("+0.0699");
  await expect(methods.getByRole("button").filter({ hasText: "Final-token attention proxy" }))
    .toContainText("+1.0000");
  await expect(methods.getByRole("button").filter({ hasText: "Integrated Gradients" }))
    .toContainText("n/a");
  await expect(page.getByText(/different methods and scales do not produce a direct delta/)).toBeVisible();

  let accounting = page.getByLabel("Attribution accounting");
  await expect(accounting).toContainText("stored method row · 20 input positions");
  await expect(accounting).toContainText("positive sum");
  await expect(accounting).toContainText("negative sum");
  await expect(accounting).toContainText("net sum");
  await expect(accounting).toContainText("sign cancellation");
  await expect(accounting).toContainText("No target/baseline contract");
  await expect(accounting).toContainText("do not prove completeness");

  await methods.getByRole("button").filter({ hasText: "Token safety proxy" }).click();
  await expect(page).toHaveURL(/track=token_safety_proxy/);
  accounting = page.getByLabel("Attribution accounting");
  await expect(accounting).toContainText("unsigned mass");
  await expect(accounting).toContainText("stored mass");
  await expect(accounting).toContainText("selected share");
  await expect(accounting).toContainText("nonesign semantics");

  await page.setViewportSize({ width: 390, height: 844 });
  await methods.scrollIntoViewIfNeeded();
  for (const button of await methods.getByRole("button").all()) {
    const box = await button.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".attribution-distribution")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("diagnoses exact NLA coverage without substituting nearby rows", async ({ page }) => {
  await page.goto("/explorer?view=nla&token=10&layer=1&metric=nla_cosine");

  const emptyResults = page.getByLabel("NLA results");
  await expect(emptyResults).toContainText("No NLA artifact yet");
  await expect(emptyResults).toContainText("Activation");
  await expect(emptyResults).toContainText("Explanation");
  await expect(emptyResults).toContainText("Reconstruction");
  await expect(emptyResults).toContainText("Fidelity");
  await expect(emptyResults).toContainText("3 exact activations");
  await expect(page.getByLabel("NLA fidelity controls")).toHaveCount(0);
  await expect(page.locator(".nla-fidelity-cell")).toHaveCount(0);
  const candidates = page.getByLabel("NLA cached candidates").getByRole("button");
  await expect(candidates).toHaveCount(3);
  await expect(page.getByLabel("Pin inspector evidence")).toBeDisabled();

  await candidates.filter({ hasText: "break" }).click();
  await expect(page).toHaveURL(/token=10/);
  await expect(page).toHaveURL(/layer=1/);
  await expect(page).toHaveURL(/nlaComponent=attn_result/);
  await expect(page.getByRole("heading", { name: "Exact NLA evidence" })).toBeVisible();
  await expect(page.getByText("Activation is cached; NLA decoding is unavailable")).toBeVisible();
});

test("triages low-fidelity NLA rows and robust activation norm outliers", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const reviewRows = [
    { tokenIndex: 1, cosine: 0.95, mse: 0.02, fve: 0.94, activationNorm: 1.0, token: "alpha" },
    { tokenIndex: 2, cosine: 0.90, mse: 0.05, fve: 0.88, activationNorm: 1.1, token: "beta" },
    { tokenIndex: 3, cosine: 0.85, mse: 0.08, fve: 0.82, activationNorm: 0.9, token: "gamma" },
    { tokenIndex: 4, cosine: 0.40, mse: 0.40, fve: 0.20, activationNorm: 1.05, token: "weak" },
    { tokenIndex: 10, cosine: 0.92, mse: 0.04, fve: 0.90, activationNorm: 10.0, token: "outlier" }
  ].map((row) => ({
    ...row,
    layer: 1,
    component: "resid_post" as const,
    explanation: `${row.token} exact NLA explanation`,
    status: "available" as const,
    profile: "review-profile",
    source: `layer_1.resid_post[${row.tokenIndex}]`
  }));
  const reviewRun: ExplorerRun = {
    ...realRun,
    runId: "nla-review-run",
    sampleId: "nla-review-sample",
    nla: reviewRows,
    nlaCompatibility: {
      ...realRun.nlaCompatibility,
      availableLayers: [1],
      profiles: [{
        name: "review-profile",
        baseModel: realRun.modelName,
        layer: 1,
        component: "resid_post",
        dModel: realRun.nlaCompatibility.dModel,
        modelMatches: true,
        layerAvailable: true,
        dModelMatches: true,
        status: "compatible",
        reason: "Exact review fixture rows are loaded."
      }]
    }
  };

  await page.goto("/explorer?view=nla&token=10&layer=1&metric=nla_cosine");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "nla-review.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(reviewRun))
  });
  await page.getByRole("tab", { name: "NLA", exact: true }).click();

  const queue = page.getByLabel("NLA review queue");
  await expect(queue).toContainText("1 low fidelity · 1 norm outliers");
  await expect(page.locator('.nla-fidelity-cell[data-token="10"].norm-outlier')).toHaveCount(1);
  const outlierCell = page.locator(
    '.nla-fidelity-cell[data-layer="1"][data-component="resid_post"][data-token="10"]'
  );
  await outlierCell.hover();
  await expect(page.locator(".nla-fidelity-tooltip")).toContainText("activation norm · IQR outlier");

  const nlaSelectionUrl = page.url();
  const weakCell = page.locator(
    '.nla-fidelity-cell[data-layer="1"][data-component="resid_post"][data-token="4"]'
  );
  await weakCell.click({ modifiers: ["Shift"] });
  expect(page.url()).toBe(nlaSelectionUrl);
  await expect(page.getByLabel("NLA matrix selection summary")).toContainText("L1 resid · T4");
  await expect(page.getByLabel("NLA matrix selection summary").locator("span").nth(2))
    .not.toContainText("n/a");
  await expect(weakCell).toHaveClass(/comparison/);

  await page.locator(
    '.nla-fidelity-cell[data-layer="1"][data-component="resid_post"][data-token="3"]'
  ).click({ modifiers: ["Control"] });
  expect(page.url()).toBe(nlaSelectionUrl);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; layer?: number; component?: string }) =>
      pin.view === "nla" && pin.tokenIndex === 3 && pin.layer === 1 && pin.component === "resid_post"
    );
  })).toBe(true);

  await queue.getByRole("button", { name: /review lowest fidelity/ }).click();
  await expect(page).toHaveURL(/token=4/);
  await queue.getByRole("button", { name: /review activation norm outlier/ }).click();
  await expect(page).toHaveURL(/token=10/);

  const reviewFilter = page.getByRole("radiogroup", { name: "NLA candidate review filter" });
  const lowFidelity = reviewFilter.getByRole("radio", { name: "Low fidelity (1)" });
  await lowFidelity.click();
  const candidates = page.getByLabel("NLA cached candidates").getByRole("button");
  await expect(candidates).toHaveCount(1);
  await expect(candidates).toContainText("weak");
  await lowFidelity.press("ArrowRight");
  const normOutlier = reviewFilter.getByRole("radio", { name: "Norm outlier (1)" });
  await expect(normOutlier).toBeFocused();
  await expect(candidates).toHaveCount(1);
  await expect(candidates).toContainText("outlier");
  await expect(candidates).toContainText("outlier", { useInnerText: true });

  const controls = page.getByLabel("NLA fidelity controls");
  await controls.getByRole("combobox").first().selectOption("mse");
  await expect(queue).toContainText("1 low fidelity · 1 norm outliers");
  await reviewFilter.getByRole("radio", { name: "All" }).click();
  await controls.locator('input[type="range"]').fill("0.05");
  await expect(queue).toContainText("2 low fidelity · 1 norm outliers");

  await page.setViewportSize({ width: 390, height: 844 });
  await queue.scrollIntoViewIfNeeded();
  for (const button of await queue.getByRole("button").all()) {
    const box = await button.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".nla-fidelity-section")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("keeps exact NLA components through deep links, pins, sessions, and context views", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const componentRun: ExplorerRun = {
    ...realRun,
    runId: "nla-component-run",
    sampleId: "nla-component-sample",
    nla: [
      {
        tokenIndex: 10,
        layer: 1,
        component: "resid_post",
        explanation: "Residual component explanation for the exact activation.",
        cosine: 0.91,
        mse: 0.04,
        fve: 0.89,
        activationNorm: 1.1,
        status: "available",
        profile: "component-profile",
        source: "layer_1.resid_post[10]",
        token: "break"
      },
      {
        tokenIndex: 10,
        layer: 1,
        component: "attn_result",
        explanation: "Attention result explanation for the exact activation.",
        cosine: 0.82,
        mse: 0.09,
        fve: 0.77,
        activationNorm: 2.2,
        status: "available",
        profile: "component-profile",
        source: "layer_1.attn_result[10]",
        token: "break"
      },
      {
        tokenIndex: 10,
        layer: 1,
        component: "mlp_out",
        explanation: "MLP output explanation for the exact activation.",
        cosine: 0.73,
        mse: 0.16,
        fve: 0.65,
        activationNorm: 3.3,
        status: "available",
        profile: "component-profile",
        source: "layer_1.mlp_out[10]",
        token: "break"
      }
    ],
    nlaCompatibility: {
      ...realRun.nlaCompatibility,
      availableLayers: [1],
      profiles: [{
        name: "component-profile",
        baseModel: realRun.modelName,
        layer: 1,
        component: "resid_post",
        dModel: realRun.nlaCompatibility.dModel,
        modelMatches: true,
        layerAvailable: true,
        dModelMatches: true,
        status: "compatible",
        reason: "Three exact component rows are loaded at the same token and layer."
      }]
    }
  };

  await page.goto("/explorer?view=nla&token=10&layer=1&metric=nla_cosine");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "nla-components.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(componentRun))
  });
  await page.getByRole("tab", { name: "NLA", exact: true }).click();

  await page.locator(
    '.nla-fidelity-cell[data-layer="1"][data-component="attn_result"][data-token="10"]'
  ).click();
  await expect(page).toHaveURL(/nlaComponent=attn_result/);
  const exactEvidence = page.locator(".nla-evidence-detail");
  await expect(exactEvidence).toContainText("attn_result · strict match");
  await expect(exactEvidence).toContainText("Attention result explanation for the exact activation.");
  await expect(page.getByRole("region", { name: "Evidence inspector" }))
    .toContainText("layer_1.attn_result[10]");
  await expect(page.locator('.nla-fidelity-cell[data-layer="1"][data-component="attn_result"][data-token="10"]'))
    .toHaveClass(/selected/);

  await page.getByLabel("Pin inspector evidence").click();
  const pinnedNla = page.locator(".pinned-strip-items button").filter({ hasText: "attn_result" });
  await expect(pinnedNla).toHaveCount(1);

  await exactEvidence.getByRole("button", { name: "Open Attention at layer 1, token 10" }).click();
  await expect(page).toHaveURL(/view=attention/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page).toHaveURL(/layer=1/);
  await expect(page).not.toHaveURL(/nlaComponent=/);
  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  await expect(page).toHaveURL(/nlaComponent=attn_result/);
  await expect(exactEvidence).toContainText("Attention result explanation for the exact activation.");

  await page.locator(
    '.nla-fidelity-cell[data-layer="1"][data-component="mlp_out"][data-token="10"]'
  ).click();
  await expect(page).toHaveURL(/nlaComponent=mlp_out/);
  await expect(exactEvidence).toContainText("MLP output explanation for the exact activation.");
  await pinnedNla.click();
  await expect(page).toHaveURL(/nlaComponent=attn_result/);
  await expect(exactEvidence).toContainText("Attention result explanation for the exact activation.");

  const sessionDownload = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const stream = await (await sessionDownload).createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const session = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(session.selection.nlaComponent).toBe("attn_result");
  expect(session.pinnedItems.find((item: { view: string }) => item.view === "nla").component)
    .toBe("attn_result");

  await page.reload();
  await expect(page).toHaveURL(/nlaComponent=attn_result/);
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "nla-components-reloaded.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(componentRun))
  });
  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  await expect(page.locator(".nla-evidence-detail"))
    .toContainText("Attention result explanation for the exact activation.");

  await page.setViewportSize({ width: 390, height: 844 });
  const contextLinks = page.getByRole("group", { name: "Activation context views" });
  await contextLinks.scrollIntoViewIfNeeded();
  for (const button of await contextLinks.getByRole("button").all()) {
    const box = await button.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const accessibility = await new AxeBuilder({ page })
    .include(".nla-evidence-detail")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("shows unified inspector values, provenance, statuses, and copy actions", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/explorer?view=overview&token=10&layer=1");
  const inspector = page.getByLabel("Evidence inspector");
  await expect(inspector.getByRole("heading", { name: "Summary" })).toBeVisible();
  await expect(inspector.getByRole("heading", { name: "Evidence" })).toBeVisible();
  await expect(inspector.getByRole("heading", { name: "Actions" })).toBeVisible();
  await expect(inspector.locator(".evidence-status")).toHaveText("available");
  await expect(inspector.getByText("not stored", { exact: true })).toBeVisible();
  await expect(inspector.getByText("bundled real model cache", { exact: false })).toBeVisible();

  await page.getByRole("tab", { name: "Residual", exact: true }).click();
  await expect(inspector.locator(".inspector-primary-value")).toContainText("Residual direction alignment");
  await inspector.getByLabel("Copy inspector cache key").click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain("resid_post");
  await inspector.getByLabel("Copy reproducible evidence context").click();
  const contextPayload = JSON.parse(await page.evaluate(() => navigator.clipboard.readText()));
  expect(contextPayload.selection).toMatchObject({ view: "residual", token: 10, layer: 1 });
  expect(contextPayload.evidence.cache_key).toContain("resid_post");

  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await expect(inspector.locator(".inspector-heading")).toContainText("source 10 → destination 10");
  await expect(inspector.getByLabel("Evidence warnings")).toContainText("not be read as causal");

  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  await expect(inspector.locator(".evidence-status")).toHaveText("incompatible");

  await page.getByRole("tab", { name: "Attribution", exact: true }).click();
  await page.getByLabel("Attribution matrix controls").getByRole("combobox").selectOption(
    "integrated_gradients"
  );
  await expect(inspector.locator(".evidence-status")).toHaveText("not computed");
  await expect(inspector.locator(".inspector-status-reason")).toContainText("Captum");
  await expect(inspector.getByLabel("Pin inspector evidence")).toBeDisabled();
});

test("keeps Inspector trust assessments identical across evidence, session, pin, and comparison exports", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=attention&token=10&source=9&target=10&layer=1&head=L1H0&normalization=raw");

  const inspector = page.getByLabel("Evidence inspector", { exact: true });
  const status = await inspector.locator(".evidence-status").textContent();
  const reason = await inspector.locator(".inspector-status-reason").innerText();
  const warning = await inspector.getByLabel("Evidence warnings").locator("p").first().innerText();
  const method = await inspector.locator(".inspector-provenance-list dd").nth(0).innerText();
  const normalization = await inspector.locator(".inspector-provenance-list dd").nth(1).innerText();
  const evidenceClass = await inspector.locator(".inspector-primary-value em").textContent();

  let downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export current evidence as JSON").click();
  let payload = await downloadJson(await downloadPromise);
  expect(payload.evidenceAssessment).toMatchObject({
    schemaVersion: "1.0",
    status,
    statusReason: reason,
    method,
    normalization,
    evidenceClass: evidenceClass?.replace(" ", "_"),
    rawValue: "0.091000",
    displayValue: "0.091000",
    units: "softmax probability"
  });
  expect(payload.evidenceAssessment.warnings).toContain(warning);
  expect(payload.evidenceAssessment.reproduction.selection).toMatchObject({
    view: "attention",
    token: 10,
    source_token: 9,
    layer: 1,
    normalization: "raw"
  });

  await page.getByRole("tab", { name: "Residual", exact: true }).click();
  await page.getByLabel("Normalization").getByRole("button", { name: "Raw", exact: true }).click();
  const residualInspectorNormalization = await inspector.locator(".inspector-provenance-list dd").nth(1).innerText();
  await page.getByRole("button", { name: "Pin current evidence" }).click();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(4\)/);

  downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const session = await downloadJson(await downloadPromise);
  const parsedSession = explorerSessionSchema.safeParse(session);
  expect(parsedSession.success, parsedSession.success ? "" : JSON.stringify(parsedSession.error.issues)).toBe(true);
  expect(session.pinnedItems.every(
    (item: { assessment?: { schemaVersion?: string } }) => item.assessment?.schemaVersion === "1.0"
  )).toBe(true);
  expect(session.pinnedItems.filter((item: { view: string }) => item.view === "overview").every(
    (item: { assessment: { warnings: string[] } }) => item.assessment.warnings.includes(
      "Run-relative proxy; it is not a calibrated safety probability or causal effect."
    )
  )).toBe(true);
  expect(session.activeEvidenceAssessment).toMatchObject({
    schemaVersion: "1.0",
    status: "available",
    normalization: residualInspectorNormalization
  });
  expect(session.selection.normalization).toBe("raw");
  const residualPin = session.pinnedItems.find((item: { view: string }) => item.view === "residual");
  expect(residualPin).toMatchObject({ normalization: "raw" });
  expect(residualPin.assessment).toMatchObject({
    schemaVersion: "1.0",
    status: "available",
    rawValue: residualPin.assessment.displayValue,
    normalization: residualInspectorNormalization
  });
  expect(residualPin.assessment.warnings).toContain(
    "Directional alignment is diagnostic projection, not causal contribution."
  );

  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  downloadPromise = page.waitForEvent("download");
  await drawer.getByLabel("Export evidence comparison").click();
  const comparison = await downloadJson(await downloadPromise);
  expect(comparison.items.every(
    (item: { assessment?: { schemaVersion?: string } }) => item.assessment?.schemaVersion === "1.0"
  )).toBe(true);
  const comparisonResidual = comparison.items.find((item: { view: string }) => item.view === "residual");
  expect(comparisonResidual.normalization).toBe("raw");
  expect(comparisonResidual.assessment).toEqual(residualPin.assessment);
  await drawer.getByLabel("Close evidence comparison").click();

  const unavailableRun = {
    ...realRun,
    runId: "unavailable-export-assessment-run",
    sampleId: "unavailable-export-assessment-sample",
    mlpNeurons: realRun.mlpNeurons.filter((neuron) => neuron.layer === 0)
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "unavailable-export-assessment.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(unavailableRun))
  });
  await page.getByRole("tab", { name: "MLP", exact: true }).click();
  const unavailableInspector = page.getByLabel("Evidence inspector", { exact: true });
  const unavailableReason = await unavailableInspector.locator(".inspector-status-reason").innerText();
  downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export current evidence as JSON").click();
  payload = await downloadJson(await downloadPromise);
  expect(payload.evidenceAssessment).toMatchObject({
    schemaVersion: "1.0",
    status: "unavailable",
    statusReason: unavailableReason
  });
  expect(payload.evidenceAssessment.warnings).toContain(
    "Activation magnitude is not logit contribution, probe contribution, or ablation effect."
  );

  const failedRun = {
    ...realRun,
    runId: "failed-export-assessment-run",
    sampleId: "failed-export-assessment-sample",
    metadata: {
      ...realRun.metadata,
      analysisFailures: [{
        view: "residual",
        token: 10,
        layer: 1,
        message: "Residual analysis failed: CUDA OOM"
      }]
    }
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "failed-export-assessment.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(failedRun))
  });
  await page.getByRole("tab", { name: "Residual", exact: true }).click();
  const failedInspector = page.getByLabel("Evidence inspector", { exact: true });
  const failedReason = await failedInspector.locator(".inspector-status-reason").innerText();
  downloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export current evidence as JSON").click();
  payload = await downloadJson(await downloadPromise);
  expect(payload.evidenceAssessment).toMatchObject({
    schemaVersion: "1.0",
    status: "failed",
    statusReason: failedReason
  });
  expect(payload.evidenceAssessment.warnings[0]).toBe(failedReason);
});

test("routes Inspector evidence gaps to focused next-analysis workflows", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=attention&token=10&source=10&target=10&layer=1&head=L1H0");

  let inspector = page.getByLabel("Evidence inspector", { exact: true });
  let recommendations = inspector.getByLabel("Recommended next analysis");
  await expect(recommendations.getByRole("button")).toHaveCount(3);
  await expect(recommendations.getByRole("button").nth(0)).toContainText("Run causal patching");
  await expect(recommendations).toContainText("instead of inferring causality from a proxy");
  await expect(recommendations).toContainText("Open target attribution");
  await expect(recommendations).toContainText("Open exact NLA");

  const firstAction = recommendations.getByRole("button").nth(0);
  await firstAction.focus();
  await page.keyboard.press("Tab");
  await expect(recommendations.getByRole("button").nth(1)).toBeFocused();
  await firstAction.click();
  await expect(page).toHaveURL(/view=patching/);
  await expect(page).toHaveURL(/token=10/);
  await expect(page).toHaveURL(/layer=1/);
  await expect(page.locator("#patching-job")).toBeFocused();

  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  inspector = page.getByLabel("Evidence inspector", { exact: true });
  recommendations = inspector.getByLabel("Recommended next analysis");
  await expect(inspector.locator(".evidence-status")).toHaveText("incompatible");
  await expect(recommendations.getByRole("button").first()).toContainText("Configure NLA job");
  await recommendations.getByRole("button").first().click();
  await expect(page.locator("#nla-job")).toBeFocused();

  await page.getByRole("tab", { name: "Attribution", exact: true }).click();
  await page.getByLabel("Attribution matrix controls").getByRole("combobox")
    .selectOption("integrated_gradients");
  inspector = page.getByLabel("Evidence inspector", { exact: true });
  recommendations = inspector.getByLabel("Recommended next analysis");
  await expect(inspector.locator(".evidence-status")).toHaveText("not computed");
  await expect(recommendations.getByRole("button").first())
    .toContainText("Configure Integrated Gradients");
  await recommendations.getByRole("button").first().click();
  await expect(page.locator("#attribution-job")).toBeFocused();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  await page.getByLabel("Open evidence inspector").click();
  const drawer = page.getByRole("dialog", { name: "Evidence details" });
  await drawer.getByLabel("Show full evidence details").click();
  recommendations = drawer.getByLabel("Recommended next analysis");
  for (const button of await recommendations.getByRole("button").all()) {
    const box = await button.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  }
  const accessibility = await new AxeBuilder({ page })
    .include(".inspector-next-actions")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await recommendations.getByRole("button").first().click();
  await expect(drawer).toBeHidden();
  await expect(page.locator("#nla-job")).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test("progressively discloses mobile Inspector provenance with buttons and vertical swipes", async ({ page, context }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explorer?view=attention&token=10&source=9&target=10&layer=1&head=L1H0");

  const trigger = page.getByLabel("Open evidence inspector");
  await trigger.click();
  const drawer = page.getByRole("dialog", { name: "Evidence details" });
  const close = drawer.getByLabel("Close evidence inspector");
  const expand = drawer.getByLabel("Show full evidence details");
  await expect(drawer).toHaveAttribute("data-detail-level", "compact");
  await expect(close).toBeFocused();
  await expect(drawer.getByRole("heading", { name: "Summary" })).toBeVisible();
  await expect(drawer.getByRole("heading", { name: "Actions" })).toBeVisible();
  await expect(drawer.getByRole("heading", { name: "Evidence", exact: true })).toHaveCount(0);
  await expect(drawer.getByLabel("Recommended next analysis")).toHaveCount(0);
  await expect(expand).toHaveAttribute("aria-expanded", "false");
  await page.waitForTimeout(240);
  const compactBox = await drawer.boundingBox();
  expect(compactBox).not.toBeNull();
  expect(Math.abs(compactBox!.y + compactBox!.height - 844)).toBeLessThanOrEqual(2);
  expect(compactBox!.height).toBeLessThanOrEqual(541);
  const compactAxe = await new AxeBuilder({ page })
    .include(".mobile-inspector-drawer")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(compactAxe.violations).toEqual([]);
  const compactPath = testInfo.outputPath("mobile-inspector-compact.png");
  await drawer.screenshot({ path: compactPath });
  await testInfo.attach("mobile-inspector-compact", { path: compactPath, contentType: "image/png" });

  await expand.click();
  await expect(drawer).toHaveAttribute("data-detail-level", "full");
  await expect(drawer.getByLabel("Show compact evidence summary")).toHaveAttribute("aria-expanded", "true");
  await expect(drawer.getByRole("heading", { name: "Evidence", exact: true })).toBeVisible();
  await expect(drawer.getByLabel("Recommended next analysis")).toBeVisible();
  await expect(drawer.getByText("source 9 → destination 10", { exact: false })).toBeVisible();
  await page.waitForTimeout(200);
  const fullBox = await drawer.boundingBox();
  expect(fullBox).not.toBeNull();
  expect(fullBox!.height).toBeGreaterThan(compactBox!.height);
  expect(Math.abs(fullBox!.y + fullBox!.height - 844)).toBeLessThanOrEqual(2);
  const fullAxe = await new AxeBuilder({ page })
    .include(".mobile-inspector-drawer")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(fullAxe.violations).toEqual([]);
  const fullPath = testInfo.outputPath("mobile-inspector-full.png");
  await drawer.screenshot({ path: fullPath });
  await testInfo.attach("mobile-inspector-full", { path: fullPath, contentType: "image/png" });

  await drawer.getByLabel("Show compact evidence summary").click();
  await expect(drawer).toHaveAttribute("data-detail-level", "compact");
  await page.waitForTimeout(200);
  const header = drawer.locator(":scope > header");
  const headerBox = await header.boundingBox();
  expect(headerBox).not.toBeNull();
  const client = await context.newCDPSession(page);
  await touchSwipe(client, headerBox!.x + 70, headerBox!.y + 45, headerBox!.y - 20);
  await expect(drawer).toHaveAttribute("data-detail-level", "full");

  await page.waitForTimeout(200);
  const expandedHeaderBox = await header.boundingBox();
  expect(expandedHeaderBox).not.toBeNull();
  await touchSwipe(client, expandedHeaderBox!.x + 70, expandedHeaderBox!.y + 16, expandedHeaderBox!.y + 80);
  await expect(drawer).toHaveAttribute("data-detail-level", "compact");

  await close.click();
  await expect(trigger).toBeFocused();
  await trigger.click();
  await expect(drawer).toHaveAttribute("data-detail-level", "compact");
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

async function touchSwipe(
  client: CDPSession,
  x: number,
  startY: number,
  endY: number
) {
  await client.send("Input.dispatchTouchEvent", {
    type: "touchStart",
    touchPoints: [{ x, y: startY }]
  });
  await client.send("Input.dispatchTouchEvent", {
    type: "touchMove",
    touchPoints: [{ x, y: endY }]
  });
  await client.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
}

test("turns advanced-view result gaps into focused executable empty states", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=patching&token=10&layer=1");

  let emptyState = page.getByRole("region", { name: "No causal patch grid in this run" });
  await expect(emptyState).toContainText("L1 / token 10");
  await emptyState.getByRole("button", { name: "Configure causal patching" }).click();
  await expect(page.locator("#patching-job")).toBeFocused();

  await page.getByRole("tab", { name: "Intervention", exact: true }).click();
  emptyState = page.getByRole("region", { name: "No intervention comparison in this run" });
  await expect(emptyState).toContainText("matched generation");
  await emptyState.getByRole("button", { name: "Configure intervention" }).click();
  await expect(page.locator("#intervention-job")).toBeFocused();

  await page.goto("/explorer?view=nla&token=9&layer=1&nlaComponent=resid_post");
  emptyState = page.getByRole("region", {
    name: "Activation is cached; NLA decoding is unavailable"
  });
  await expect(emptyState).toContainText("Activation norm");
  await emptyState.getByRole("button", { name: "Configure exact NLA" }).click();
  await expect(page.locator("#nla-job")).toBeFocused();

  await page.goto("/explorer?view=attribution&token=10&layer=1&track=integrated_gradients");
  const attributionStates = page.getByRole("region", {
    name: "Integrated Gradients is not available for this run"
  });
  await expect(attributionStates).toHaveCount(1);
  await attributionStates.getByRole("button", { name: "Configure Integrated Gradients" }).click();
  await expect(page.locator("#attribution-job")).toBeFocused();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("tab", { name: "Patching", exact: true }).click();
  emptyState = page.getByRole("region", { name: "No causal patch grid in this run" });
  await emptyState.scrollIntoViewIfNeeded();
  const action = emptyState.getByRole("button", { name: "Configure causal patching" });
  const actionBox = await action.boundingBox();
  expect(actionBox).not.toBeNull();
  expect(actionBox!.height).toBeGreaterThanOrEqual(44);
  expect(actionBox!.width).toBeGreaterThanOrEqual(44);
  await expect(emptyState.locator(".actionable-empty-facts > div")).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  const axeResults = await new AxeBuilder({ page })
    .include(".actionable-empty")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);

  const screenshotPath = testInfo.outputPath("actionable-empty-state-mobile.png");
  await emptyState.screenshot({ path: screenshotPath });
  await testInfo.attach("actionable-empty-state-mobile", {
    path: screenshotPath,
    contentType: "image/png"
  });
});

test("classifies failed evidence and exposes the mobile inspector drawer", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  const failedRun = {
    ...realRun,
    runId: "failed-inspector-run",
    sampleId: "failed-sample",
    metadata: {
      ...realRun.metadata,
      analysisFailures: [{
        view: "residual",
        token: 10,
        layer: 1,
        message: "Residual analysis failed: CUDA OOM"
      }]
    }
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "failed-inspector.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(failedRun))
  });
  await page.getByRole("tab", { name: "Residual", exact: true }).click();
  await expect(page.locator(".right-panel")).toBeHidden();

  await page.getByLabel("Open evidence inspector").click();
  const detailDrawer = page.getByRole("dialog", { name: "Evidence details" });
  await expect(detailDrawer).toBeVisible();
  await expect(detailDrawer.locator(".evidence-status")).toHaveText("failed");
  await expect(detailDrawer).toContainText("Residual analysis failed: CUDA OOM");

  await detailDrawer.getByRole("button", { name: "Compare" }).click();
  await expect(detailDrawer).toBeHidden();
  await expect(page.getByRole("dialog", { name: "Compare pinned evidence" })).toBeVisible();
  await page.getByLabel("Close evidence comparison").click();
  await page.getByLabel("Open evidence inspector").click();
  await page.keyboard.press("Escape");
  await expect(detailDrawer).toBeHidden();
});

test("classifies an exact missing component as unavailable", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  const missingLayerRun = {
    ...realRun,
    runId: "unavailable-inspector-run",
    sampleId: "missing-layer-neurons",
    mlpNeurons: realRun.mlpNeurons.filter((neuron) => neuron.layer === 0)
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "unavailable-inspector.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(missingLayerRun))
  });
  await page.getByRole("tab", { name: "MLP", exact: true }).click();
  const inspector = page.getByLabel("Evidence inspector");
  await expect(inspector.locator(".evidence-status")).toHaveText("unavailable");
  await expect(inspector.locator(".inspector-status-reason")).toContainText("No retained neuron");
  await expect(inspector.getByLabel("Pin inspector evidence")).toBeDisabled();
});

test("preloads the comparison visualization and exposes a stable loading dialog", async ({ page }) => {
  let compareRequests = 0;
  let releaseCompare!: () => void;
  const compareGate = new Promise<void>((resolve) => { releaseCompare = resolve; });
  await page.route(/\/src\/components\/CompareDrawer\.tsx(?:\?.*)?$/, async (route) => {
    compareRequests += 1;
    await compareGate;
    await route.continue();
  });

  await page.goto("/explorer");
  expect(compareRequests).toBe(0);
  const trigger = page.getByLabel(/^Compare pinned evidence/);
  await trigger.focus();
  await expect.poll(() => compareRequests).toBe(1);
  await trigger.click();
  await expect(page.getByRole("dialog", { name: "Loading evidence comparison" })).toBeVisible();

  releaseCompare();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByLabel("Baseline-centered evidence deltas")).toBeVisible();
  expect(compareRequests).toBe(1);
});

test("recovers a stalled comparison module inside the modal flow", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  let releaseCompare!: () => void;
  const compareGate = new Promise<void>((resolve) => { releaseCompare = resolve; });
  await page.addInitScript(() => {
    window.__SAFELENS_TEST_LAZY_TIMEOUT_MS__ = 100;
  });
  await page.route(/\/src\/components\/CompareDrawer\.tsx(?:\?.*)?$/, async (route) => {
    await compareGate;
    await route.continue();
  });

  await page.goto("/explorer");
  const trigger = page.getByLabel(/^Compare pinned evidence/);
  await trigger.focus();
  await trigger.click();
  await expect(page.getByRole("dialog", { name: "Loading evidence comparison" })).toBeVisible();

  const errorDialog = page.getByRole("dialog", { name: "Evidence comparison error" });
  await expect(errorDialog).toBeVisible();
  await expect(errorDialog).toBeFocused();
  await expect(errorDialog).toContainText("The workspace and pinned evidence are unchanged.");
  await errorDialog.getByText("Technical detail").click();
  await expect(errorDialog.locator("code")).toContainText("Lazy module CompareDrawer timed out");

  await errorDialog.press("Shift+Tab");
  await expect(errorDialog.getByRole("button", { name: "Copy diagnostics" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(errorDialog.getByRole("button", { name: "Close evidence comparison error" })).toBeFocused();
  await errorDialog.getByRole("button", { name: "Copy diagnostics" }).click();
  const diagnostics = JSON.parse(await page.evaluate(() => navigator.clipboard.readText()));
  expect(diagnostics.kind).toBe("safelens-dialog-render-error");
  expect(diagnostics.view).toBe("Evidence comparison");

  await page.setViewportSize({ width: 390, height: 844 });
  for (const button of await errorDialog.getByRole("button").all()) {
    expect((await button.boundingBox())?.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  const errorAxe = await new AxeBuilder({ page })
    .include(".compare-error-drawer")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(errorAxe.violations).toEqual([]);

  releaseCompare();
  await errorDialog.getByRole("button", { name: "Retry comparison" }).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toHaveCount(0);
  await expect(trigger).toBeFocused();
});

test("compares pinned evidence and restores a card context", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");

  await page.getByRole("tab", { name: "Residual", exact: true }).click();
  await page.getByRole("button", { name: "Pin current evidence" }).click();
  await page.getByLabel(/^Compare pinned evidence/).click();

  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByText("4", { exact: true }).first()).toBeVisible();
  await expect(drawer.getByText("Different metric; no delta.").first()).toBeVisible();
  const deltaPlot = drawer.getByLabel("Baseline-centered evidence deltas");
  await expect(deltaPlot).toBeVisible();
  await expect(deltaPlot.getByRole("listitem")).toHaveCount(4);
  await expect(deltaPlot.getByRole("listitem").first()).toContainText("0 baseline");
  await expect(deltaPlot.locator(".delta-incompatible")).toHaveCount(1);
  await expect(deltaPlot.locator(".delta-incompatible .compare-delta-bar")).toHaveCount(0);
  const axeResults = await new AxeBuilder({ page })
    .include(".compare-drawer")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
  await page.emulateMedia({ forcedColors: "active" });
  await expect(deltaPlot.locator(".compare-delta-track").first()).toHaveCSS("forced-color-adjust", "none");

  const secondCard = drawer.locator(".compare-card").nth(1);
  await secondCard.getByRole("button", { name: /Restore context/ }).click();
  await expect(drawer).toBeHidden();
  await expect(page).toHaveURL(/view=overview/);
  await expect(page).toHaveURL(/token=17/);
});

test("compares versioned attention profiles and restores them from an analysis session", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const profileRun = {
    ...realRun,
    runId: "attention-profile-run",
    sampleId: "attention-profile-sample",
    attentionHeads: realRun.attentionHeads.map((head) => {
      if (head.id !== "L1H1") return head;
      return {
        ...head,
        distributionByToken: head.distributionByToken.map((row, destination) => {
          if (destination !== 10) return row;
          const weights = row.map((_, source) => source <= destination ? source + 1 : 0);
          const total = weights.reduce((sum, value) => sum + value, 0);
          return weights.map((value) => value / total);
        })
      };
    })
  };

  await page.goto("/explorer");
  const importInput = page.getByLabel("Import Explorer artifact JSON");
  await importInput.setInputFiles({
    name: "attention-profile-run.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(profileRun))
  });
  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  const headSelect = page.locator(".attention-pattern-toolbar select");
  await headSelect.selectOption("L1H0");
  await page.getByLabel("Pin inspector evidence").click();
  await headSelect.selectOption("L1H1");
  await page.getByLabel("Pin inspector evidence").click();

  await page.getByLabel(/^Compare pinned evidence/).click();
  let drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const baselineCard = drawer.locator(".compare-card").filter({ hasText: "head L1H0" });
  await baselineCard.getByLabel(/Use .* as baseline/).click();

  const profilePlot = drawer.locator(".compare-profile-plot");
  await expect(profilePlot.getByRole("heading", { name: "Attention row difference" })).toBeVisible();
  await expect(profilePlot).toContainText("L1H0 · destination token 10 · 11 points");
  const profileRows = profilePlot.getByLabel("Token profile differences").getByRole("listitem");
  await expect(profileRows).toHaveCount(1);
  await expect(profileRows.first()).toContainText("L1H1 · destination token 10");
  await expect(profileRows.first()).toContainText("11 aligned");
  await expect(profileRows.first()).not.toHaveClass(/incompatible/);
  const profileLabel = await profileRows.first().getAttribute("aria-label");
  expect(profileLabel).toMatch(/mean absolute delta (?!0\.000)/);
  const chartPath = await profileRows.first().locator(".compare-profile-line").first().getAttribute("d");
  expect(chartPath).toMatch(/^M /);
  expect(chartPath).not.toContain("NaN");

  const matrixDifference = drawer.locator(".compare-matrix-difference");
  await expect(matrixDifference.getByRole("heading", { name: "Attention matrix difference" })).toBeVisible();
  const matrixRows = matrixDifference.locator(".compare-matrix-row");
  await expect(matrixRows).toHaveCount(1);
  await expect(matrixRows.first()).toContainText("20×20 full");
  const differenceCanvas = matrixRows.first().locator("canvas.specialized-matrix-canvas");
  await expect(differenceCanvas).toBeVisible();
  await expect(differenceCanvas).toHaveAttribute("data-render-mode", "canvas");
  expect(await differenceCanvas.evaluate((canvas) => {
    const element = canvas as HTMLCanvasElement;
    const context = element.getContext("2d");
    if (!context) return false;
    const pixels = context.getImageData(0, 0, element.width, element.height).data;
    for (let index = 0; index < pixels.length; index += 64) {
      if (pixels[index] < 245 || pixels[index + 1] < 245 || pixels[index + 2] < 245) return true;
    }
    return false;
  })).toBe(true);
  await differenceCanvas.focus();
  await page.keyboard.press("Home");
  await expect(matrixRows.first().locator(".compare-matrix-cell-detail")).toContainText("User · 0");

  const comparisonDownload = page.waitForEvent("download");
  await drawer.getByLabel("Export evidence comparison").click();
  const comparisonStream = await (await comparisonDownload).createReadStream();
  const comparisonChunks: Buffer[] = [];
  for await (const chunk of comparisonStream) comparisonChunks.push(Buffer.from(chunk));
  const comparisonArtifact = JSON.parse(Buffer.concat(comparisonChunks).toString("utf8"));
  const headComparison = comparisonArtifact.comparisons.find(
    (item: { item_id: string }) => item.item_id.includes(":L1H1:")
  );
  expect(headComparison.profile_difference).toMatchObject({
    comparable: true,
    aligned_points: 11
  });
  expect(headComparison.profile_difference.max_absolute_delta).toBeGreaterThan(0);
  expect(headComparison.profile_difference.deltas).toHaveLength(11);
  expect(headComparison.matrix_difference).toMatchObject({
    comparable: true,
    sampled: false,
    aligned_size: 20
  });
  expect(headComparison.matrix_difference.max_absolute_delta).toBeGreaterThan(0);
  expect(headComparison.matrix_difference.axis).toHaveLength(20);
  expect(headComparison.matrix_difference.cells).toHaveLength(20);

  await drawer.getByLabel("Close evidence comparison").click();
  const sessionDownload = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const sessionStream = await (await sessionDownload).createReadStream();
  const sessionChunks: Buffer[] = [];
  for await (const chunk of sessionStream) sessionChunks.push(Buffer.from(chunk));
  const sessionBuffer = Buffer.concat(sessionChunks);
  const sessionArtifact = JSON.parse(sessionBuffer.toString("utf8"));
  const savedProfile = sessionArtifact.pinnedItems.find(
    (item: { headId?: string }) => item.headId === "L1H1"
  ).profile;
  expect(savedProfile).toMatchObject({
    schemaVersion: "1.0",
    kind: "attention_source_profile",
    axis: "source_token",
    originalLength: 11,
    sampled: false
  });
  expect(savedProfile.points).toHaveLength(11);
  const savedMatrix = sessionArtifact.pinnedItems.find(
    (item: { headId?: string }) => item.headId === "L1H1"
  ).matrix;
  expect(savedMatrix).toMatchObject({
    schemaVersion: "1.0",
    kind: "attention_matrix",
    originalSize: 20,
    sampled: false
  });
  expect(savedMatrix.axis).toHaveLength(20);
  expect(savedMatrix.values).toHaveLength(20);
  expect(savedMatrix.values[0][1]).toBeNull();

  const invalidSession = structuredClone(sessionArtifact);
  invalidSession.pinnedItems.find(
    (item: { headId?: string }) => item.headId === "L1H1"
  ).matrix.values[0][1] = 0;
  await importInput.setInputFiles({
    name: "invalid-attention-matrix-session.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(invalidSession))
  });
  await expect(page.getByText("Analysis session validation failed")).toBeVisible();

  await importInput.setInputFiles({
    name: "attention-profile-session.json",
    mimeType: "application/json",
    buffer: sessionBuffer
  });
  await expect(page.getByText("Analysis session restored")).toBeVisible();
  await page.getByLabel(/^Compare pinned evidence/).click();
  drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer.getByRole("heading", { name: "Attention row difference" })).toBeVisible();
  await expect(drawer.getByRole("heading", { name: "Attention matrix difference" })).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(async () => {
    const box = await drawer.boundingBox();
    return box ? { x: Math.round(box.x), width: Math.round(box.width) } : null;
  }).toEqual({ x: 0, width: 390 });
  expect(await drawer.evaluate((element) => element.scrollWidth)).toBe(390);
  const mobileMatrix = drawer.locator(".compare-attention-matrix-scroll").first();
  const mobileOverview = drawer.locator(".compare-matrix-overview").first();
  const mobileMatrixBox = await mobileMatrix.boundingBox();
  const mobileOverviewBox = await mobileOverview.boundingBox();
  expect(mobileMatrixBox).not.toBeNull();
  expect(mobileOverviewBox).not.toBeNull();
  expect(mobileMatrixBox!.x + mobileMatrixBox!.width).toBeLessThanOrEqual(390);
  expect(mobileOverviewBox!.y + mobileOverviewBox!.height).toBeLessThanOrEqual(mobileMatrixBox!.y);
  const axeResults = await new AxeBuilder({ page })
    .include(".compare-drawer")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
  await page.emulateMedia({ forcedColors: "active" });
  await expect(drawer.locator(".compare-profile-line").first()).toHaveCSS(
    "forced-color-adjust",
    "none"
  );
  await expect(drawer.locator(".compare-attention-matrix canvas").first()).toHaveCSS(
    "forced-color-adjust",
    "none"
  );

  const storedPinCount = await page.evaluate(() => {
    const key = "safelens.localExplorer.pinnedEvidence.v2";
    const pins = JSON.parse(window.localStorage.getItem(key) ?? "[]");
    const matrixPin = pins.find((item: { matrix?: unknown }) => item.matrix !== undefined);
    matrixPin.matrix.values[0][1] = 0;
    window.localStorage.setItem(key, JSON.stringify(pins));
    return pins.length;
  });
  expect(storedPinCount).toBe(4);
  await page.reload();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(3\)/);
});

test("rejects cross-run profile deltas when the full token axis is not exact", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=attention&token=10&source=9&layer=1");
  await page.getByLabel("Pin inspector evidence").click();

  const mismatchedAxisRun = {
    ...realRun,
    runId: "profile-axis-mismatch-run",
    sampleId: "profile-axis-mismatch-sample",
    tokens: realRun.tokens.map((token) => token.index === 1
      ? { ...token, tokenId: token.tokenId + 5000 }
      : token)
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "profile-axis-mismatch.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(mismatchedAxisRun))
  });
  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  await page.locator(".attention-pattern-toolbar select").selectOption("L1H0");
  await page.getByLabel("Pin inspector evidence").click();

  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const baselineCard = drawer.locator(".compare-card")
    .filter({ hasText: realRun.runId })
    .filter({ hasText: "head L1H0" });
  await baselineCard.getByLabel(/Use .* as baseline/).click();
  const mismatchedRow = drawer.getByLabel("Token profile differences").getByRole("listitem");
  await expect(mismatchedRow).toHaveCount(1);
  await expect(mismatchedRow).toHaveClass(/incompatible/);
  await expect(mismatchedRow).toContainText(
    "Cross-run profiles require an exact point-by-point tokenizer and token sequence match."
  );
  await expect(mismatchedRow.locator(".compare-profile-chart")).toHaveCount(0);
  const mismatchedMatrixRow = drawer.locator(".compare-matrix-rows").getByRole("listitem");
  await expect(mismatchedMatrixRow).toHaveCount(1);
  await expect(mismatchedMatrixRow).toHaveClass(/incompatible/);
  await expect(mismatchedMatrixRow).toContainText(
    "Cross-run matrices require exact model/tokenizer and point-by-point token axes."
  );
  await expect(mismatchedMatrixRow.locator("canvas")).toHaveCount(0);
});

test("compares signed attribution token profiles across layers", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer?view=attribution&token=10&layer=0&track=residual_direction");
  await page.getByLabel("Pin inspector evidence").click();
  await page.getByLabel("Layer selector").getByRole("radio", { name: "L1" }).click();
  await page.getByLabel("Pin inspector evidence").click();

  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  const attributionCards = drawer.locator(".compare-card.compare-attribution");
  await expect(attributionCards).toHaveCount(2);
  await attributionCards.first().getByLabel(/Use .* as baseline/).click();
  const profilePlot = drawer.locator(".compare-profile-plot");
  await expect(profilePlot.getByRole("heading", { name: "Signed attribution difference" })).toBeVisible();
  const profileRow = profilePlot.getByLabel("Token profile differences").getByRole("listitem");
  await expect(profileRow).toHaveCount(1);
  await expect(profileRow).toContainText("20 aligned");
  await expect(profileRow.locator(".compare-profile-chart")).toBeVisible();

  await drawer.getByLabel("Close evidence comparison").click();
  const sessionDownload = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const stream = await (await sessionDownload).createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const session = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  const profiles = session.pinnedItems
    .filter((item: { view: string }) => item.view === "attribution")
    .map((item: { profile: unknown }) => item.profile);
  expect(profiles).toHaveLength(2);
  expect(profiles).toEqual(expect.arrayContaining([
    expect.objectContaining({
      kind: "signed_attribution_profile",
      axis: "token",
      signed: true,
      originalLength: 20,
      sampled: false
    })
  ]));
});

test("bounds long pinned profiles and matrices while retaining full-axis provenance", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  const baseLongRun = expandedTimelineRun(300);
  const layerOneHead = baseLongRun.attentionHeads.find((head) => head.id === "L1H0")!;
  const longRun = {
    ...baseLongRun,
    attentionHeads: [
      ...baseLongRun.attentionHeads,
      {
        ...layerOneHead,
        id: "L1H1",
        head: 1,
        distributionByToken: layerOneHead.distributionByToken.map((row, destination) => {
          const denominator = (destination + 1) * (destination + 2) / 2;
          return row.map((_, source) => source <= destination ? (source + 1) / denominator : 0);
        })
      }
    ]
  };
  await page.goto("/explorer");
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "long-profile-run.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(longRun))
  });
  await page.getByRole("tab", { name: "Attribution", exact: true }).click();
  await page.getByLabel("Pin inspector evidence").click();
  await page.getByRole("tab", { name: "Attention", exact: true }).click();
  const attentionCanvas = page.getByRole("grid", { name: /Attention pattern Canvas matrix/ });
  await attentionCanvas.focus();
  for (let index = 0; index < 7; index += 1) await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Home");
  for (let index = 0; index < 3; index += 1) await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL(/token=7/);
  await expect(page).toHaveURL(/source=3/);
  await page.getByLabel("Pin inspector evidence").click();
  await page.locator(".attention-pattern-toolbar select").selectOption("L1H1");
  await page.getByLabel("Pin inspector evidence").click();

  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await drawer.locator(".compare-card").filter({ hasText: "head L1H0" })
    .getByLabel(/Use .* as baseline/).click();
  const sampledMatrixRow = drawer.locator(".compare-matrix-row");
  await expect(sampledMatrixRow).toHaveCount(1);
  await expect(sampledMatrixRow).toContainText("64×64 sampled");
  const sampledCanvas = sampledMatrixRow.locator("canvas.specialized-matrix-canvas");
  await expect(sampledCanvas).toBeVisible();
  await expect.poll(async () => Number(await sampledCanvas.getAttribute("data-visible-cells")))
    .toBeGreaterThan(0);
  expect(Number(await sampledCanvas.getAttribute("data-visible-cells"))).toBeLessThan(4_096);
  await drawer.getByLabel("Close evidence comparison").click();

  const sessionDownload = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const stream = await (await sessionDownload).createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const session = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  const profile = session.pinnedItems.find(
    (item: { runId: string; view: string }) =>
      item.runId === longRun.runId && item.view === "attribution"
  ).profile;
  expect(profile).toMatchObject({
    schemaVersion: "1.0",
    kind: "signed_attribution_profile",
    originalLength: 300,
    sampled: true
  });
  expect(profile.points).toHaveLength(256);
  expect(profile.points[0].tokenIndex).toBe(0);
  expect(profile.points.at(-1).tokenIndex).toBe(299);
  expect(profile.points.some(
    (point: { tokenIndex: number }) => point.tokenIndex === session.selection.tokenIndex
  )).toBe(true);
  const attentionPins = session.pinnedItems.filter(
    (item: { runId: string; view: string }) =>
      item.runId === longRun.runId && item.view === "attention"
  );
  expect(attentionPins).toHaveLength(2);
  const attentionPin = attentionPins.find((item: { headId?: string }) => item.headId === "L1H0");
  expect(attentionPin.matrix).toMatchObject({
    schemaVersion: "1.0",
    kind: "attention_matrix",
    originalSize: 300,
    sampled: true
  });
  expect(attentionPin.matrix.axis).toHaveLength(64);
  expect(attentionPin.matrix.axis[0].tokenIndex).toBe(0);
  expect(attentionPin.matrix.axis.at(-1).tokenIndex).toBe(299);
  expect(attentionPin.matrix.axis.some(
    (point: { tokenIndex: number }) => point.tokenIndex === 7
  )).toBe(true);
  expect(attentionPin.matrix.axis.some(
    (point: { tokenIndex: number }) => point.tokenIndex === 3
  )).toBe(true);
  expect(attentionPin.matrix.values).toHaveLength(64);
  expect(attentionPin.matrix.values.every((row: unknown[]) => row.length === 64)).toBe(true);
});

test("aligns cross-run tokens, switches baseline, exports, and restores source context", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");

  await page.getByLabel(/^Compare pinned evidence/).click();
  let drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await drawer.locator(".compare-card").nth(1).getByLabel(/^Remove /).click();
  await drawer.locator(".compare-card").nth(1).getByLabel(/^Remove /).click();
  await drawer.getByLabel("Close evidence comparison").click();

  const textAlignedRun = {
    ...realRun,
    runId: "text-aligned-run",
    sampleId: "text-aligned-sample",
    tokens: realRun.tokens.map((token) =>
      token.index === 10
        ? { ...token, tokenId: token.tokenId + 1000, risk: 0.95 }
        : { ...token, risk: Math.min(token.risk, 0.9) }
    )
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "text-aligned.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(textAlignedRun))
  });
  await expect(page).toHaveURL(/run=text-aligned-run/);
  await expect(page).toHaveURL(/token=10/);
  await page.getByRole("button", { name: "Pin current evidence" }).click();

  const positionOnlyRun = {
    ...realRun,
    runId: "position-only-run",
    sampleId: "position-only-sample",
    tokens: realRun.tokens.map((token) =>
      token.index === 10
        ? { ...token, text: "DIFFERENT_TOKEN", tokenId: token.tokenId + 2000, risk: 0.96 }
        : { ...token, risk: Math.min(token.risk, 0.9) }
    )
  };
  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "position-only.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(positionOnlyRun))
  });
  await expect(page).toHaveURL(/run=position-only-run/);
  await page.getByRole("button", { name: "Pin current evidence" }).click();

  await page.getByLabel(/^Compare pinned evidence/).click();
  drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer.getByLabel("Comparison summary")).toContainText("3runs / samples");
  const textCard = drawer.locator(".compare-card").filter({ hasText: "text-aligned-run" });
  const positionCard = drawer.locator(".compare-card").filter({ hasText: "position-only-run" });
  await expect(textCard.locator(".compare-alignment")).toContainText("Text-only alignment");
  await expect(textCard.locator(".compare-value em")).toContainText("vs baseline");
  await expect(positionCard.locator(".compare-alignment")).toContainText("Position-only match");
  await expect(positionCard.locator(".compare-value em")).toContainText("no delta is calculated");
  const crossRunPlot = drawer.getByLabel("Baseline-centered evidence deltas");
  const positionPlotRow = crossRunPlot.getByRole("listitem", { name: /DIFFERENT_TOKEN/ });
  await expect(positionPlotRow).toHaveClass(/delta-incompatible/);
  await expect(positionPlotRow).toContainText("not comparable");
  await expect(positionPlotRow.locator(".compare-delta-bar")).toHaveCount(0);

  await textCard.getByLabel(/Use text-aligned-run .* as baseline/).click();
  await expect(drawer.locator(".compare-card").first()).toContainText("text-aligned-run");
  await expect(crossRunPlot.getByRole("listitem").first()).toContainText("text-aligned-run");
  await expect(crossRunPlot.getByRole("listitem").first()).toContainText("0 baseline");

  const downloadPromise = page.waitForEvent("download");
  await drawer.getByLabel("Export evidence comparison").click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const artifact = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(artifact.kind).toBe("safelens-comparison");
  expect(artifact.baseline_id).toContain("text-aligned-run");
  expect(artifact.comparisons.map((item: { alignment: { status: string } }) => item.alignment.status))
    .toEqual(expect.arrayContaining(["baseline", "text-only", "position-only"]));

  await drawer.getByLabel("Close evidence comparison").click();
  const sessionDownloadPromise = page.waitForEvent("download");
  await page.getByLabel("Export analysis session").click();
  const sessionDownload = await sessionDownloadPromise;
  const sessionStream = await sessionDownload.createReadStream();
  const sessionChunks: Buffer[] = [];
  for await (const chunk of sessionStream) sessionChunks.push(Buffer.from(chunk));
  const sessionBuffer = Buffer.concat(sessionChunks);
  const savedSession = JSON.parse(sessionBuffer.toString("utf8"));
  expect(savedSession.compare.baselineId).toContain("text-aligned-run");

  await page.getByLabel(/^Compare pinned evidence/).click();
  drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await drawer.locator(".compare-card")
    .filter({ hasText: "position-only-run" })
    .getByLabel(/Use position-only-run .* as baseline/)
    .click();
  await expect(drawer.locator(".compare-card").first()).toContainText("position-only-run");
  await drawer.getByLabel("Close evidence comparison").click();

  await page.getByLabel("Import Explorer artifact JSON").setInputFiles({
    name: "saved-comparison-session.json",
    mimeType: "application/json",
    buffer: sessionBuffer
  });
  await expect(page.getByText("Analysis session restored")).toBeVisible();
  await page.getByLabel(/^Compare pinned evidence/).click();
  drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer.locator(".compare-card").first()).toContainText("text-aligned-run");

  await drawer.locator(".compare-card").first().getByRole("button", { name: /Restore context/ }).click();
  await expect(page).toHaveURL(/run=text-aligned-run/);
  await expect(page).toHaveURL(/sample=text-aligned-sample/);
  await expect(page).toHaveURL(/token=10/);
  await page.reload();
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(3\)/);
});

test("removes comparison items and closes the drawer with Escape", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("/explorer");
  await page.getByLabel(/^Compare pinned evidence/).click();

  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await drawer.getByLabel("Remove break from comparison").click();
  await expect(drawer.getByText("2", { exact: true }).first()).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
});

test("traps modal focus and returns it to each drawer trigger", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explorer?view=overview&token=10&layer=1");

  const libraryTrigger = page.getByLabel("Open run library");
  await libraryTrigger.click();
  const libraryDrawer = page.getByRole("dialog", { name: "Runs and samples" });
  await expect(libraryDrawer.getByLabel("Close run library")).toBeFocused();
  await expect(page.locator(".topbar")).toHaveAttribute("inert", "");
  await expect(page.locator(".workspace")).toHaveAttribute("inert", "");
  const libraryButtons = libraryDrawer.locator("button:visible");
  await libraryButtons.last().focus();
  await page.keyboard.press("Tab");
  await expect(libraryButtons.first()).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(libraryTrigger).toBeFocused();
  await expect(page.locator(".topbar")).not.toHaveAttribute("inert", "");
  await expect(page.locator(".workspace")).not.toHaveAttribute("inert", "");

  const inspectorTrigger = page.getByLabel("Open evidence inspector");
  await inspectorTrigger.click();
  const inspectorDrawer = page.getByRole("dialog", { name: "Evidence details" });
  await expect(inspectorDrawer.getByLabel("Close evidence inspector")).toBeFocused();
  const tokenBefore = new URL(page.url()).searchParams.get("token");
  await page.keyboard.press("ArrowRight");
  expect(new URL(page.url()).searchParams.get("token")).toBe(tokenBefore);
  await page.keyboard.press("Escape");
  await expect(inspectorTrigger).toBeFocused();

  const compareTrigger = page.getByLabel(/^Compare pinned evidence/);
  await compareTrigger.click();
  const compareDrawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(compareDrawer.getByLabel("Close evidence comparison")).toBeFocused();
  const compareButtons = compareDrawer.locator("button:visible:not([disabled])");
  await compareButtons.last().focus();
  await page.keyboard.press("Tab");
  await expect(compareButtons.first()).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(compareTrigger).toBeFocused();
});

test("keeps visualization controls usable at 320 and 360 pixels", async ({ page }) => {
  for (const width of [320, 360]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/explorer?view=attention&token=10&source=9&layer=1");
    await expect(page.getByRole("heading", { name: "Token Timeline" })).toBeVisible();
    await expect(page.locator(".mobile-current-run")).toBeVisible();
    await expect(page.locator(".mobile-current-run strong"))
      .toHaveAttribute("title", realRun.runId);
    await expect(page.locator(".mobile-current-run strong")).toHaveText(realRun.runId);
    await expect(page.locator(".mobile-run-context-label")).toHaveText("Sample");
    await expect(page.getByLabel("Quick run selector").locator("option:checked"))
      .toHaveText(realRun.sampleId);

    const runStatus = await page.locator(".run-status").boundingBox();
    const runMeta = await page.locator(".run-meta").boundingBox();
    const metricCards = await page.locator(".run-meta .metric").evaluateAll((elements) =>
      elements.map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          left: rect.left,
          right: rect.right,
          width: rect.width,
          height: rect.height,
          clientWidth: element.clientWidth,
          scrollWidth: element.scrollWidth
        };
      })
    );
    expect(runStatus).not.toBeNull();
    expect(runMeta).not.toBeNull();
    expect(runStatus!.x).toBeGreaterThanOrEqual(0);
    expect(runStatus!.x + runStatus!.width).toBeLessThanOrEqual(width);
    expect(metricCards).toHaveLength(3);
    for (const card of metricCards) {
      expect(card.left).toBeGreaterThanOrEqual(runMeta!.x);
      expect(card.right).toBeLessThanOrEqual(runMeta!.x + runMeta!.width);
      expect(card.width).toBeGreaterThan(80);
      expect(card.height).toBeLessThanOrEqual(60);
      expect(card.scrollWidth).toBeLessThanOrEqual(card.clientWidth);
    }
    await expect(page.locator(".run-meta .metric-label-short:visible")).toHaveCount(3);
    await expect(page.getByLabel("Max safety proxy metric")).toContainText("Safety max");
    await expect(page.getByLabel("Mean attention proxy metric")).toContainText("Attention mean");

    for (const locator of [
      page.getByLabel("Quick run selector"),
      page.getByLabel("Open run library")
    ]) {
      const box = await locator.boundingBox();
      expect(box?.width).toBeGreaterThanOrEqual(44);
      expect(box?.height).toBeGreaterThanOrEqual(44);
    }

    const selectionBar = await page.locator(".mobile-selection-summary").boundingBox();
    const timelineHeader = await page.locator(".main-header").boundingBox();
    expect(selectionBar).not.toBeNull();
    expect(timelineHeader).not.toBeNull();
    expect(selectionBar!.x + selectionBar!.width).toBeLessThanOrEqual(width);
    expect(timelineHeader!.y).toBeLessThan(800);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);

    if (width === 320) {
      const timelineMetric = await page.locator(".timeline-metric").boundingBox();
      const timelineResults = await page.getByLabel("Token search results").boundingBox();
      expect(timelineMetric).not.toBeNull();
      expect(timelineResults).not.toBeNull();
      expect(timelineMetric!.width).toBeGreaterThan(200);
      expect(timelineMetric!.y + timelineMetric!.height).toBeLessThanOrEqual(timelineResults!.y);
      const axeResults = await new AxeBuilder({ page })
        .include(".topbar")
        .include(".main-panel")
        .withTags(["wcag2a", "wcag2aa"])
        .analyze();
      expect(axeResults.violations).toEqual([]);
    }

    await page.getByLabel(/^Compare pinned evidence/).click();
    const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
    await expect(drawer).toBeVisible();
    await expect.poll(async () => {
      const box = await drawer.boundingBox();
      return box ? { x: Math.round(box.x), width: Math.round(box.width) } : null;
    }).toEqual({ x: 0, width });
    expect(await drawer.evaluate((element) => element.scrollWidth)).toBe(width);
    await drawer.getByLabel("Close evidence comparison").click();
  }
});

test("keeps primary visualization controls at mobile touch size", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explorer?view=attention&token=10&source=9&layer=1");

  for (const locator of [
    page.locator(".metric strong").first(),
    page.locator(".mobile-selection-summary b").first(),
    page.locator(".specialized-comparison-summary").first()
  ]) {
    await expect(locator).toBeVisible();
    expect(await locator.evaluate((element) => getComputedStyle(element).fontVariantNumeric))
      .toContain("tabular-nums");
  }

  async function expectTouchHeight(locator: ReturnType<typeof page.locator>) {
    await expect(locator.first()).toBeVisible();
    const boxes = await locator.evaluateAll((elements) => elements.map((element) => {
      const rect = element.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    }));
    expect(boxes.length).toBeGreaterThan(0);
    for (const box of boxes) expect(box.height).toBeGreaterThanOrEqual(44);
  }

  async function expectSquareTouchTargets(locator: ReturnType<typeof page.locator>) {
    await expect(locator.first()).toBeVisible();
    const boxes = await locator.evaluateAll((elements) => elements.map((element) => {
      const rect = element.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    }));
    expect(boxes.length).toBeGreaterThan(0);
    for (const box of boxes) {
      expect(box.width).toBeGreaterThanOrEqual(44);
      expect(box.height).toBeGreaterThanOrEqual(44);
    }
  }

  await expectTouchHeight(page.getByLabel("Quick run selector"));
  await expect(page.locator(".mobile-current-run strong"))
    .toHaveAttribute("title", realRun.runId);
  await expect(page.locator(".mobile-run-context-label")).toHaveText("Sample");
  await expectSquareTouchTargets(page.locator(".topbar-actions .icon-button:visible"));
  await expectTouchHeight(page.getByRole("tab"));
  const tabList = page.getByRole("tablist", { name: "Analysis view" });
  const tabViewport = await tabList.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth
  }));
  expect(tabViewport.scrollWidth).toBeGreaterThan(tabViewport.clientWidth);
  await expectTouchHeight(page.locator(".main-layer-picker button"));
  await expectTouchHeight(page.getByLabel("Timeline granularity").getByRole("button"));
  await expectTouchHeight(page.getByLabel("Search tokens"));
  await expectTouchHeight(page.getByLabel("Token color metric"));
  const firstTokenBox = await page.locator(".token-pill").first().boundingBox();
  expect(firstTokenBox).not.toBeNull();
  expect(firstTokenBox!.y).toBeLessThan(844);

  await page.goto("/explorer?view=attribution&token=10&layer=1");
  const attributionTab = page.getByRole("tab", { name: "Attribution", exact: true });
  await expect(attributionTab).toHaveAttribute("aria-selected", "true");
  await expect.poll(() => tabList.evaluate((element) => {
    const selected = element.querySelector<HTMLElement>('[aria-selected="true"]');
    if (!selected) return false;
    const viewport = element.getBoundingClientRect();
    const tab = selected.getBoundingClientRect();
    return tab.left >= viewport.left - 4 && tab.right <= viewport.right + 4;
  })).toBe(true);
  await attributionTab.focus();
  await page.keyboard.press("Home");
  await expect(page.getByRole("tab", { name: "Overview", exact: true })).toHaveAttribute("aria-selected", "true");
  await expect.poll(() => tabList.evaluate((element) => element.scrollLeft)).toBe(0);

  const matrices = [
    { view: "Residual", controls: "Matrix controls" },
    { view: "Attention", controls: "Attention matrix controls" },
    { view: "MLP", controls: "MLP matrix controls" },
    { view: "Attribution", controls: "Attribution matrix controls" }
  ];
  for (const matrix of matrices) {
    await page.getByRole("tab", { name: matrix.view, exact: true }).click();
    const controls = page.getByLabel(matrix.controls, { exact: true });
    await expect(controls).toBeVisible();
    await expectSquareTouchTargets(controls.locator(".toolbar-actions button:visible"));
    const segmentedButtons = controls.locator(".toolbar-segment button:visible");
    if (await segmentedButtons.count()) await expectTouchHeight(segmentedButtons);
    const formControls = controls.locator("input:visible, select:visible");
    if (await formControls.count()) await expectTouchHeight(formControls);
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  }
  await page.getByRole("tab", { name: "NLA", exact: true }).click();
  const nlaPositions = page.getByRole("group", { name: "NLA token positions" }).getByRole("button");
  await expectTouchHeight(nlaPositions);
  await expectTouchHeight(page.getByRole("button", { name: "Run exact NLA" }));
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  const axeResults = await new AxeBuilder({ page })
    .include(".main-panel")
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(axeResults.violations).toEqual([]);
});

test("keeps the unified controls usable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/explorer?view=mlp&token=10&layer=1");

  for (const label of ["Overview", "Residual", "Attention", "MLP", "NLA", "Patching", "Intervention", "Attribution"]) {
    await expect(page.getByRole("tab", { name: label, exact: true })).toBeVisible();
  }
  await expect(page.getByLabel("MLP matrix controls", { exact: true })).toBeVisible();
  const hasPageOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth
  );
  expect(hasPageOverflow).toBe(false);

  await page.getByLabel("Open run library").click();
  const runDrawer = page.getByRole("dialog", { name: "Runs and samples" });
  await expect(runDrawer).toBeVisible();
  await expect(runDrawer.getByLabel("Run and sample selector")).toBeVisible();
  await expect(runDrawer.getByRole("button", { name: "Import JSON" })).toBeVisible();
  await expect(runDrawer.getByText("Data provenance", { exact: true })).toBeVisible();
  await expect(runDrawer.getByText("Evidence", { exact: true })).toBeVisible();
  await expect(page.locator(".left-panel")).toBeHidden();
  await page.keyboard.press("Escape");
  await expect(runDrawer).toBeHidden();

  await page.getByLabel(/^Compare pinned evidence/).click();
  const drawer = page.getByRole("dialog", { name: "Compare pinned evidence" });
  await expect(drawer).toBeVisible();
  expect(await drawer.locator(".compare-value strong").first()
    .evaluate((element) => getComputedStyle(element).fontVariantNumeric))
    .toContain("tabular-nums");
  const columns = await drawer.locator(".compare-grid").evaluate(
    (element) => getComputedStyle(element).gridTemplateColumns.split(" ").length
  );
  expect(columns).toBe(1);
  const hasDrawerOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth
  );
  expect(hasDrawerOverflow).toBe(false);
});

test("keeps run selection and metrics aligned at intermediate widths", async ({ page }) => {
  for (const width of [1024, 768, 700]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/explorer?view=attention&token=10&source=9&layer=1");
    const topbar = await page.locator(".topbar").boundingBox();
    const runStatus = await page.locator(".run-status").boundingBox();
    const metrics = await page.locator(".run-meta").boundingBox();
    const workspace = await page.getByRole("region", { name: "Analysis workspace" }).boundingBox();
    expect(topbar).not.toBeNull();
    expect(runStatus).not.toBeNull();
    expect(metrics).not.toBeNull();
    expect(workspace).not.toBeNull();
    expect(topbar!.height).toBeLessThan(160);
    await expect(page.locator(".mobile-current-run")).toBeHidden();
    await expect(page.locator(".brand-block p")).toHaveText(realRun.runId);
    expect(Math.abs(
      runStatus!.y + runStatus!.height / 2 - (metrics!.y + metrics!.height / 2)
    )).toBeLessThanOrEqual(2);
    expect(runStatus!.x + runStatus!.width).toBeLessThanOrEqual(metrics!.x);
    expect(workspace!.y).toBeLessThan(180);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(width);
  }
});

test("keeps the inspector visible beside the workspace at a common desktop width", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/explorer?view=residual&token=10&layer=1");
  const mainBox = await page.locator(".main-panel").boundingBox();
  const inspectorBox = await page.locator(".right-panel").boundingBox();
  expect(mainBox).not.toBeNull();
  expect(inspectorBox).not.toBeNull();
  expect(inspectorBox!.x).toBeGreaterThan(mainBox!.x + mainBox!.width);
  expect(inspectorBox!.y).toBeLessThan(160);
  await expect(page.getByRole("region", { name: "Evidence inspector" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
});

test("keeps the focus layout centered and reveals supporting tools on demand", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/explorer?layout=focus&view=overview&token=10&layer=1");

  await expect(page.locator(".app-shell")).toHaveClass(/layout-focus/);
  await expect(page.locator(".left-panel")).toBeHidden();
  await expect(page.locator(".right-panel")).toBeHidden();
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Attribution", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(1440);

  await page.getByLabel("Open run library").click();
  const dataDrawer = page.getByRole("dialog", { name: "Runs and samples" });
  await expect(dataDrawer).toBeVisible();
  await expect(dataDrawer.getByText("Prompt runner", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");

  await page.getByLabel("Inspect selected evidence").click();
  const evidenceDrawer = page.getByRole("dialog", { name: "Evidence details" });
  await expect(evidenceDrawer).toBeVisible();
  await expect(evidenceDrawer).toContainText("break");
  await page.keyboard.press("Escape");

  await page.getByLabel("Open quick actions").click();
  const quickActions = page.getByRole("dialog", { name: "Quick actions" });
  await expect(quickActions).toBeVisible();
  await expect(quickActions.getByRole("button", { name: /Export Explorer artifact/ })).toBeVisible();
  await page.keyboard.press("Escape");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.locator(".run-meta")).toBeHidden();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test("turns a token selection into an interactive analysis workflow in focus mode", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/explorer?layout=focus&view=overview&token=10&layer=1");

  const workbench = page.getByRole("region", { name: "Selected token actions" });
  await expect(workbench).toBeHidden();
  await expect(page.locator(".trace-panel")).toHaveCount(0);
  await expect(page.locator(".digest-panel")).toHaveCount(0);
  await expect(page.locator(".pinned-strip")).toHaveCount(0);
  await expect(page.locator(".overview-evidence-map")).toHaveCount(0);

  await page.locator(".token-pill").filter({ hasText: "jail" }).click();
  await expect(workbench).toBeVisible();
  await expect(workbench).toContainText("jail");
  await expect(workbench.getByText("T9", { exact: true })).toBeVisible();

  const analyze = workbench.getByRole("button", { name: "Analyze" });
  await analyze.click();
  await expect(analyze).toHaveAttribute("aria-expanded", "true");
  const methodMenu = page.getByRole("menu", { name: "Analyze selected token" });
  await expect(methodMenu).toBeVisible();
  await methodMenu.getByRole("menuitemradio", { name: "Attention" }).click();
  await expect(page.getByRole("heading", { name: "Attention", exact: true })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Attention", exact: true })).toHaveAttribute("aria-selected", "true");
  await expect(methodMenu).toBeHidden();

  const context = workbench.getByRole("button", { name: "Context" });
  await context.click();
  await expect(context).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator(".trace-panel")).toBeVisible();
  await expect(page.locator(".digest-panel")).toBeVisible();
  await expect(page.locator(".pinned-strip")).toBeVisible();
  await expect(page.locator(".attention-distribution")).toBeVisible();

  await analyze.click();
  await methodMenu.getByRole("menuitemradio", { name: "Attribution" }).click();
  await expect(page.locator(".attribution-job-panel")).toHaveCount(0);
  await page.locator(".attribution-matrix-toolbar select").selectOption("integrated_gradients");
  await page.getByRole("button", { name: "Configure Integrated Gradients" }).first().click();
  await expect(page.locator(".attribution-job-panel")).toBeVisible();
  await page.getByRole("button", { name: "Close experiment setup" }).click();
  await expect(page.locator(".attribution-job-panel")).toHaveCount(0);

  await workbench.getByRole("button", { name: "Inspect" }).click();
  await expect(page.getByRole("dialog", { name: "Evidence details" })).toBeVisible();
  await page.keyboard.press("Escape");

  await page.setViewportSize({ width: 320, height: 800 });
  await expect(workbench).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(320);
});
