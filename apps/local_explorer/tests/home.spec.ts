import { expect, test, type Page } from "@playwright/test";

import { realRun } from "../src/realRunData";
import type { ExplorerRun } from "../src/types";

const generatedRun = {
  ...realRun,
  runId: "chat-home-generated",
  sampleId: "seed-0",
  prompt: "Why does the model focus on this token?",
  metadata: {
    ...realRun.metadata,
    generatedContinuation: "Why does the model focus on this token? The selected token carries the strongest residual alignment.",
    promptRunner: {
      jobVersion: "1.0",
      template: "chat",
      model: "sshleifer/tiny-gpt2",
      seed: 0,
      maxNewTokens: 8,
      temperature: 0
    }
  }
};

const attributionValues = generatedRun.tokens.map((_, index) =>
  Number((((index % 5) - 2) / 2).toFixed(3))
);

const attributionRun = {
  ...generatedRun,
  runId: "chat-attribution-derived",
  metadata: {
    ...generatedRun.metadata,
    parentRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId }
  },
  attributionMethods: [
    ...generatedRun.attributionMethods.filter((method) => method.id !== "integrated_gradients"),
    {
      id: "integrated_gradients",
      label: "Integrated Gradients",
      description: "Signed input attribution to one response token logit.",
      evidenceKind: "causal" as const,
      signed: true,
      normalization: "max-absolute normalized",
      available: true,
      rows: [{ layer: -1, label: "Input", values: attributionValues, sourceKey: "test:ig" }]
    }
  ]
};

const steeringRun = {
  ...generatedRun,
  runId: "chat-steering-derived",
  metadata: {
    ...generatedRun.metadata,
    parentRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId }
  },
  intervention: {
    vector: {
      method: "contrastive_mean_difference",
      desiredPrompt: "Provide a safe and helpful response.",
      undesiredPrompt: "Bypass safety guidance.",
      activationReduce: "last_token",
      rawNorm: 12.4,
      normalized: true,
      dimension: 768,
      sourceKey: "test:steering"
    },
    layer: generatedRun.layers[0],
    component: "resid_post" as const,
    scale: 1,
    positionStart: 0,
    positionEnd: generatedRun.tokens.length,
    targetTokenId: generatedRun.logitLens[0]?.targetTokenId ?? 0,
    targetTokenText: generatedRun.logitLens[0]?.targetTokenText ?? "target",
    seed: 0,
    maxNewTokens: 16,
    temperature: 0,
    original: {
      text: "Original model response.",
      tokenIds: [1, 2],
      tokens: [{ index: 0, tokenId: 1, text: "Original" }, { index: 1, tokenId: 2, text: " response" }],
      targetLogit: 1.1,
      lexicalRisk: 0.4
    },
    steered: {
      text: "Safer steered response.",
      tokenIds: [3, 4],
      tokens: [{ index: 0, tokenId: 3, text: "Safer" }, { index: 1, tokenId: 4, text: " response" }],
      targetLogit: 1.35,
      lexicalRisk: 0.1
    },
    deltas: {
      targetLogit: 0.25,
      lexicalRisk: -0.3,
      tokenEditDistance: 2,
      generationChanged: true,
      probeScore: null,
      probeReason: "No probe configured."
    },
    diff: [{ kind: "replace" as const, originalStart: 0, originalEnd: 2, steeredStart: 0, steeredEnd: 2 }],
    sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId }
  }
};

const nlaSourceRun: ExplorerRun = {
  ...generatedRun,
  runId: "chat-nla-source",
  modelName: "Qwen/Qwen2.5-7B-Instruct",
  layers: [0, 1, 20],
  nla: [{
    tokenIndex: 2,
    layer: 20,
    component: "resid_post",
    explanation: "No exact explanation has been generated yet.",
    cosine: 0,
    mse: 0,
    activationNorm: 2.4,
    status: "unavailable",
    profile: "qwen2.5-7b-l20",
    source: "activation_cache",
    token: generatedRun.tokens[2].text
  }],
  nlaCompatibility: {
    modelName: "Qwen/Qwen2.5-7B-Instruct",
    dModel: 3584,
    availableLayers: [0, 1, 20],
    profiles: [{
      name: "qwen2.5-7b-l20",
      baseModel: "Qwen/Qwen2.5-7B-Instruct",
      layer: 20,
      component: "resid_post",
      dModel: 3584,
      modelMatches: true,
      layerAvailable: true,
      dModelMatches: true,
      status: "artifact_missing",
      reason: "Compatible activation cache; generate an exact NLA explanation."
    }]
  }
};

const nlaDerivedRun: ExplorerRun = {
  ...nlaSourceRun,
  runId: "chat-nla-derived",
  metadata: {
    ...nlaSourceRun.metadata,
    parentRun: { runId: nlaSourceRun.runId, sampleId: nlaSourceRun.sampleId }
  },
  nla: [{
    ...nlaSourceRun.nla[0],
    explanation: "This activation tracks the contrast between benign safety language and jailbreak framing.",
    cosine: 0.91,
    mse: 0.04,
    fve: 0.84,
    status: "available"
  }]
};

const jLensBaseRow = generatedRun.logitLens.find((row) => row.layer === 0 && row.tokenIndex === 2)!;
const jLensDerivedRun: ExplorerRun = {
  ...generatedRun,
  runId: "chat-jlens-derived",
  metadata: {
    ...generatedRun.metadata,
    parentRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId }
  },
  jLens: [{
    ...jLensBaseRow,
    targetRank: 7,
    targetLogit: 3.125,
    targetProbability: 0.072,
    topPredictions: jLensBaseRow.topPredictions.map((prediction, index) => ({
      ...prediction,
      logit: prediction.logit + 0.75 - index * 0.04
    })),
    modelTopPredictions: jLensBaseRow.topPredictions,
    lensSource: "research/test-jlens",
    filename: "tiny-gpt2/lens.pt",
    revision: "test-revision",
    nPrompts: 128,
    sourceKey: "jlens:research/test-jlens:tiny-gpt2/lens.pt@test-revision"
  }]
};

async function prepareHome(page: Page) {
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "test-workspace",
        runs: [],
        diagnostics: []
      }
    });
  });
  await page.route("**/api/prompt/options", async (route) => {
    await route.fulfill({
      json: {
        models: ["sshleifer/tiny-gpt2", "Qwen/Qwen2.5-7B-Instruct"],
        templates: ["plain", "chat"],
        maxNewTokens: 512
      }
    });
  });
  await page.route("**/api/tokenize", async (route) => {
    const request = route.request().postDataJSON() as { modelName: string; text: string };
    const pieces = request.text.match(/[A-Za-z0-9_]+|[^\sA-Za-z0-9_]/g) ?? [];
    await route.fulfill({
      json: {
        modelName: request.modelName,
        text: request.text,
        tokens: pieces.map((text, index) => ({ index, tokenId: 1_000 + index, text })),
        truncated: false
      }
    });
  });
  await page.route("**/api/nla/profiles", async (route) => {
    await route.fulfill({ json: [] });
  });
  await page.route("**/api/jlens/options", async (route) => {
    await route.fulfill({
      json: {
        packageInstalled: true,
        defaultModel: "sshleifer/tiny-gpt2",
        defaultSource: "research/test-jlens",
        defaultFilename: "tiny-gpt2/lens.pt",
        defaultRevision: "test-revision"
      }
    });
  });
  await page.route("**/api/jlens/preflight", async (route) => {
    await route.fulfill({
      json: {
        packageInstalled: true,
        modelAllowed: true,
        layerAvailable: true,
        positionValid: true,
        lensConfigured: true,
        artifactChecked: false,
        fittedLayers: [],
        lensDModel: null,
        canSubmit: true,
        reason: "Jacobian Lens package, artifact, model, layer, and token are ready."
      }
    });
  });
  await page.route("**/api/intervention/preflight", async (route) => {
    const request = route.request().postDataJSON();
    await route.fulfill({
      json: {
        modelAllowed: true,
        layerAvailable: true,
        componentSupported: true,
        positionRangeValid: true,
        targetTokenValid: true,
        referencesDiffer: request.desiredPrompt !== request.undesiredPrompt,
        targetTokenId: request.targetTokenId,
        targetTokenText: "target",
        positionStart: request.positionStart,
        positionEnd: request.positionEnd,
        canSubmit: request.desiredPrompt !== request.undesiredPrompt,
        reason: "Steering inputs are ready."
      }
    });
  });
}

async function mockReadyPromptJob(page: Page, result: ExplorerRun = generatedRun) {
  const request = {
    prompt: generatedRun.prompt,
    template: "chat" as const,
    model: "sshleifer/tiny-gpt2",
    seed: 0,
    maxNewTokens: 8,
    temperature: 0
  };
  const base = {
    id: "chat-home-job",
    kind: "prompt-run" as const,
    stage: "complete",
    progress: 100,
    detail: "Analysis ready.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    request,
    error: null
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/prompt", async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({
      status: 202,
      json: { ...base, status: "idle", stage: "queued", progress: 0, result: null }
    });
  });
  await page.route("**/api/jobs/chat-home-job/events", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: { "Cache-Control": "no-cache" },
      body: `event: job\ndata: ${JSON.stringify({ ...base, status: "ready", result })}\n\n`
    });
  });
  return () => submitted;
}

async function mockReadyPromptSequence(page: Page) {
  const submissions: Array<Record<string, unknown>> = [];
  const jobs = new Map<string, { request: Record<string, unknown>; result: typeof generatedRun }>();
  await page.route("**/api/jobs/prompt", async (route) => {
    const request = route.request().postDataJSON() as Record<string, unknown>;
    submissions.push(request);
    const index = submissions.length;
    const id = `chat-sequence-${index}`;
    const prompt = String(request.prompt);
    const messages = Array.isArray(request.messages)
      ? request.messages as Array<{ role: "user" | "assistant"; content: string }>
      : [];
    const rendered = [
      ...messages.map((message) => `${message.role === "user" ? "User" : "Assistant"}: ${message.content}`),
      `User: ${prompt}`,
      "Assistant:"
    ].join("\n");
    const answer = index === 1 ? "First answer from the model." : "Second answer uses the prior turn.";
    const result = {
      ...generatedRun,
      runId: `chat-sequence-run-${index}`,
      prompt: rendered,
      metadata: {
        ...generatedRun.metadata,
        generatedContinuation: `${rendered} ${answer}`,
        promptRunner: {
          ...generatedRun.metadata.promptRunner,
          contextMessages: messages,
          userPrompt: prompt
        }
      }
    };
    jobs.set(id, { request, result });
    await route.fulfill({
      status: 202,
      json: promptJob(id, request, null, "idle")
    });
  });
  await page.route(/\/api\/jobs\/chat-sequence-\d+\/events$/, async (route) => {
    const id = new URL(route.request().url()).pathname.split("/").at(-2) ?? "";
    const job = jobs.get(id);
    if (!job) {
      await route.fulfill({ status: 404 });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(promptJob(id, job.request, job.result, "ready"))}\n\n`
    });
  });
  return submissions;
}

function promptJob(
  id: string,
  request: Record<string, unknown>,
  result: typeof generatedRun | null,
  status: "idle" | "ready"
) {
  return {
    id,
    kind: "prompt-run",
    status,
    stage: status === "ready" ? "complete" : "queued",
    progress: status === "ready" ? 100 : 0,
    detail: status === "ready" ? "Analysis ready." : "Waiting for the local model worker.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    request,
    result,
    error: null
  };
}

async function runReadyAnalysis(page: Page, prompt = generatedRun.prompt) {
  await page.getByLabel("Analysis prompt").fill(prompt);
  await page.getByLabel("Run analysis").click();
  await expect(page.getByText("Activation cache ready")).toBeVisible();
}

async function mockReadyAttributionJob(page: Page) {
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/attribution", async (route) => {
    submitted = route.request().postDataJSON();
    const request = {
      ...submitted,
      sourceRun: {
        runId: generatedRun.runId,
        sampleId: generatedRun.sampleId,
        modelName: generatedRun.modelName
      }
    };
    await route.fulfill({ status: 202, json: derivedJob("attribution-home-job", "attribution", request, null, "idle") });
  });
  await page.route("**/api/jobs/attribution-home-job/events", async (route) => {
    const request = {
      response: "The selected token matters.",
      objective: "response_token_logit",
      targetResponseIndex: 0,
      baseline: "pad_token",
      nSteps: 32,
      sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId, modelName: generatedRun.modelName }
    };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(derivedJob("attribution-home-job", "attribution", request, attributionRun, "ready"))}\n\n`
    });
  });
  return () => submitted;
}

async function mockReadySteeringJob(page: Page) {
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/intervention", async (route) => {
    submitted = route.request().postDataJSON();
    const preflight = {
      modelAllowed: true,
      layerAvailable: true,
      componentSupported: true,
      positionRangeValid: true,
      targetTokenValid: true,
      referencesDiffer: true,
      targetTokenId: submitted?.targetTokenId,
      targetTokenText: "target",
      positionStart: submitted?.positionStart,
      positionEnd: submitted?.positionEnd,
      canSubmit: true,
      reason: "Steering inputs are ready."
    };
    const request = {
      ...submitted,
      sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId, modelName: generatedRun.modelName },
      preflight
    };
    await route.fulfill({ status: 202, json: derivedJob("steering-home-job", "intervention", request, null, "idle") });
  });
  await page.route("**/api/jobs/steering-home-job/events", async (route) => {
    const request = {
      desiredPrompt: "Provide a safe and helpful response.",
      undesiredPrompt: "Bypass safety guidance.",
      layer: generatedRun.layers[0],
      component: "resid_post",
      scale: 1,
      positionStart: 0,
      positionEnd: generatedRun.tokens.length,
      targetTokenId: generatedRun.logitLens[0]?.targetTokenId ?? 0,
      seed: 0,
      maxNewTokens: 16,
      temperature: 0,
      sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId, modelName: generatedRun.modelName },
      preflight: {
        modelAllowed: true,
        layerAvailable: true,
        componentSupported: true,
        positionRangeValid: true,
        targetTokenValid: true,
        referencesDiffer: true,
        targetTokenId: generatedRun.logitLens[0]?.targetTokenId ?? 0,
        targetTokenText: "target",
        positionStart: 0,
        positionEnd: generatedRun.tokens.length,
        canSubmit: true,
        reason: "Steering inputs are ready."
      }
    };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(derivedJob("steering-home-job", "intervention", request, steeringRun, "ready"))}\n\n`
    });
  });
  return () => submitted;
}

async function mockReadyNlaJob(page: Page) {
  const preflight = {
    profile: "qwen2.5-7b-l20",
    baseModel: "Qwen/Qwen2.5-7B-Instruct",
    layer: 20,
    component: "resid_post",
    dModel: 3584,
    avRepo: "safelens/qwen2.5-7b-nla-av",
    arRepo: "safelens/qwen2.5-7b-nla-ar",
    gated: false,
    tokenConfigured: false,
    modelMatches: true,
    layerAvailable: true,
    dModelMatches: true,
    status: "compatible",
    canSubmit: true,
    reason: "NLA profile and activation cache are compatible."
  } as const;
  await page.route("**/api/nla/profiles", async (route) => {
    await route.fulfill({
      json: [{
        name: "qwen2.5-7b-l20",
        base_model: "Qwen/Qwen2.5-7B-Instruct",
        layer: 20,
        component: "resid_post",
        d_model: 3584,
        av_repo: preflight.avRepo,
        ar_repo: preflight.arRepo,
        gated: false,
        description: "Qwen NLA profile"
      }]
    });
  });
  await page.route("**/api/nla/preflight", async (route) => {
    await route.fulfill({ json: preflight });
  });
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/nla", async (route) => {
    submitted = route.request().postDataJSON();
    const request = {
      profile: submitted?.profile,
      positions: submitted?.positions,
      revision: submitted?.revision,
      maxNewTokens: submitted?.maxNewTokens,
      loadReconstructor: true,
      confirmGatedAccess: false,
      sourceRun: { runId: nlaSourceRun.runId, sampleId: nlaSourceRun.sampleId, modelName: nlaSourceRun.modelName },
      preflight
    };
    await route.fulfill({ status: 202, json: derivedJob("nla-home-job", "nla", request, null, "idle") });
  });
  await page.route("**/api/jobs/nla-home-job/events", async (route) => {
    const request = {
      profile: "qwen2.5-7b-l20",
      positions: [2],
      revision: "main",
      maxNewTokens: 96,
      loadReconstructor: true,
      confirmGatedAccess: false,
      sourceRun: { runId: nlaSourceRun.runId, sampleId: nlaSourceRun.sampleId, modelName: nlaSourceRun.modelName },
      preflight
    };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(derivedJob("nla-home-job", "nla", request, nlaDerivedRun, "ready"))}\n\n`
    });
  });
  return () => submitted;
}

async function mockReadyJLensJob(page: Page) {
  const preflight = {
    packageInstalled: true,
    modelAllowed: true,
    layerAvailable: true,
    positionValid: true,
    lensConfigured: true,
    artifactChecked: false,
    fittedLayers: [],
    lensDModel: null,
    canSubmit: true,
    reason: "Jacobian Lens package, artifact, model, layer, and token are ready."
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/jlens", async (route) => {
    submitted = route.request().postDataJSON();
    const request = {
      layer: submitted?.layer,
      position: submitted?.position,
      lensSource: submitted?.lensSource,
      filename: submitted?.filename,
      revision: submitted?.revision,
      topK: submitted?.topK,
      sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId, modelName: generatedRun.modelName },
      preflight
    };
    await route.fulfill({ status: 202, json: derivedJob("jlens-home-job", "jlens", request, null, "idle") });
  });
  await page.route("**/api/jobs/jlens-home-job/events", async (route) => {
    const request = {
      layer: 0,
      position: 2,
      lensSource: "research/test-jlens",
      filename: "tiny-gpt2/lens.pt",
      revision: "test-revision",
      topK: 10,
      sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId, modelName: generatedRun.modelName },
      preflight
    };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(derivedJob("jlens-home-job", "jlens", request, jLensDerivedRun, "ready"))}\n\n`
    });
  });
  return () => submitted;
}

function derivedJob(
  id: string,
  kind: "attribution" | "intervention" | "nla" | "jlens",
  request: Record<string, unknown>,
  result: unknown,
  status: "idle" | "ready"
) {
  return {
    id,
    kind,
    status,
    stage: status === "ready" ? "complete" : "queued",
    progress: status === "ready" ? 100 : 0,
    detail: status === "ready" ? "Analysis ready." : "Waiting for the local model worker.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    request,
    result,
    error: null
  };
}

test("opens as the minimal Chat interface shown in the reference figures", async ({ page }) => {
  await prepareHome(page);
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "What would you like to inspect?" })).toBeVisible();
  await expect(page.getByLabel("Analysis prompt")).toBeVisible();
  await expect(page.getByLabel("Analysis model")).toHaveValue("sshleifer/tiny-gpt2");
  await expect(page.getByLabel("Maximum new tokens")).toHaveValue("128");
  await expect(page.getByRole("complementary", { name: "Chat history" })).toBeVisible();
  await expect(page.getByLabel("Conversation history").locator(".chat-history-row")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "New chat" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Work" })).toHaveCount(0);
  await expect(page.getByLabel("Preloaded dataset")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Run analysis" })).toBeDisabled();
  await expect(page.locator(".home-stats, .home-viz-grid, .home-nla-panel")).toHaveCount(0);

  const layout = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }));
  expect(layout.document).toBeLessThanOrEqual(layout.viewport);
});

test("runs the real prompt-job protocol and keeps the conversation above two focused analyses", async ({ page }) => {
  await prepareHome(page);
  const submitted = await mockReadyPromptJob(page);
  await page.goto("/");
  await page.getByLabel("Maximum new tokens").fill("192");
  await runReadyAnalysis(page);

  await expect(page.locator(".chat-user-message")).toHaveText(generatedRun.prompt);
  await expect(page.locator(".chat-assistant-message")).toContainText("strongest residual alignment");
  await expect(page.locator(".chat-turn-explore-bar > button")).toHaveCount(4);
  await expect(page.getByRole("button", { name: /Steer/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Attribute/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Explain/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Attention/ })).toBeVisible();
  await expect(page.getByLabel("Analysis prompt")).toBeVisible();
  await expect(page.getByLabel("Analysis prompt")).toHaveValue("");
  await expect(page).toHaveURL(/\/$/);
  expect(submitted()).toEqual({
    prompt: generatedRun.prompt,
    template: "chat",
    model: "sshleifer/tiny-gpt2",
    seed: 0,
    maxNewTokens: 192,
    temperature: 0,
    messages: []
  });
});

test("sends prior user and assistant turns as real model context", async ({ page }) => {
  await prepareHome(page);
  const submissions = await mockReadyPromptSequence(page);
  await page.goto("/");

  await page.getByLabel("Analysis prompt").fill("First question?");
  await page.getByLabel("Run analysis").click();
  await expect(page.locator(".chat-assistant-message")).toContainText("First answer from the model.");

  await page.getByLabel("Analysis prompt").fill("What follows from that?");
  await page.getByLabel("Run analysis").click();
  await expect(page.locator(".chat-turn-card")).toHaveCount(2);
  await expect(page.locator(".chat-assistant-message").last()).toContainText("Second answer uses the prior turn.");

  expect(submissions).toHaveLength(2);
  expect(submissions[1]).toMatchObject({
    prompt: "What follows from that?",
    messages: [
      { role: "user", content: "First question?" },
      { role: "assistant", content: "First answer from the model." }
    ]
  });
});

test("switches between steering and input attribution inside the current chat", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Steer/ }).click();
  await expect(page.getByRole("heading", { name: "Steering" })).toBeVisible();
  await expect(page.getByLabel("Steering desired behavior")).toBeVisible();
  await expect(page.getByLabel("Steering strength")).toHaveValue("1");

  await page.getByRole("button", { name: /Attribute/ }).click();
  await expect(page.getByRole("heading", { name: "Input attribution" })).toBeVisible();
  await expect(page.getByLabel("Attribution response")).toBeVisible();
  await expect(page.getByLabel("Attribution integration steps")).toHaveValue("32");
  await expect(page.getByRole("button", { name: "Open Explorer" })).toHaveCount(0);
  expect(await page.evaluate(() => window.location.pathname)).toBe("/");
});

test("selects a layer and token for NLA and J-Lens explanations in Chat", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  const submitted = await mockReadyJLensJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Explain/ }).click();
  await expect(page.getByRole("heading", { name: "Explanation" })).toBeVisible();
  await expect(page.getByRole("tab", { name: /NLA/ })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByLabel("Explanation layer")).toBeVisible();
  await expect(page.getByLabel("Explanation token position")).toBeVisible();
  await expect(page.getByLabel("NLA output")).toContainText("No exact NLA explanation");

  await page.getByRole("tab", { name: /J-Lens/ }).click();
  await page.getByLabel("Explanation layer").selectOption("0");
  await page.getByRole("radio", { name: "Token 2 Compare" }).click();
  await expect(page.getByRole("button", { name: "Run J-Lens" })).toBeEnabled();
  await page.getByRole("button", { name: "Run J-Lens" }).click();
  const expected = jLensDerivedRun.jLens[0];
  const output = page.getByLabel("J-Lens output");
  await expect(output).toContainText(expected.targetTokenText.trim());
  await expect(output).toContainText(`#${expected.targetRank.toLocaleString()}`);
  await expect(output.getByLabel("J-Lens vocabulary predictions")).toContainText(
    expected.topPredictions[0].tokenText.trim()
  );
  await expect(output).toContainText("fitted on 128 prompts");
  expect(submitted()).toMatchObject({
    layer: 0,
    position: 2,
    lensSource: "research/test-jlens",
    filename: "tiny-gpt2/lens.pt",
    revision: "test-revision",
    topK: 10
  });
});

test("runs exact NLA for the selected layer and token and renders the derived explanation", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page, nlaSourceRun);
  const submitted = await mockReadyNlaJob(page);
  await page.goto("/");
  await page.getByLabel("Analysis model").selectOption("Qwen/Qwen2.5-7B-Instruct");
  await runReadyAnalysis(page, nlaSourceRun.prompt);

  await page.getByRole("button", { name: /Explain/ }).click();
  await expect(page.getByLabel("Explanation layer")).toHaveValue("20");
  await expect(page.getByRole("radio", { name: "Token 2 Compare" })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByRole("button", { name: "Run NLA" })).toBeEnabled();
  await page.getByRole("button", { name: "Run NLA" }).click();

  const output = page.getByLabel("NLA output");
  await expect(output).toContainText("contrast between benign safety language and jailbreak framing");
  await expect(output).toContainText("0.9100");
  expect(submitted()).toMatchObject({
    profile: "qwen2.5-7b-l20",
    positions: [2],
    revision: "main",
    maxNewTokens: 96,
    loadReconstructor: true,
    confirmGatedAccess: false
  });
});

test("visualizes real attention heads and updates the selected layer, head, and token", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Attention/ }).click();
  await expect(page.getByRole("heading", { name: "Attention heads" })).toBeVisible();
  await page.getByLabel("Attention heads layer").selectOption("0");
  await page.getByLabel("Attention head", { exact: true }).selectOption("L0H1");
  await page.getByRole("radio", { name: "Destination token 10 break" }).click();
  await expect(page.getByLabel("Selected attention pair")).toContainText("T10 · break");
  await expect(page.getByLabel("Attention head choices").getByRole("radio", { name: /L0H1/ }))
    .toHaveAttribute("aria-checked", "true");
  const canvas = page.getByRole("img", { name: /L0H1 attention heatmap/ });
  await expect(canvas).toBeVisible();
  expect(await canvas.evaluate((element) => {
    const context = (element as HTMLCanvasElement).getContext("2d");
    if (!context) return 0;
    return context.getImageData(0, 0, 40, 40).data.filter((value, index) => index % 4 !== 3 && value !== 0).length;
  })).toBeGreaterThan(0);
});

test("keeps Explanation and Attention usable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Explain/ }).click();
  await page.getByRole("tab", { name: /J-Lens/ }).click();
  await expect(page.getByLabel("J-Lens output")).toBeVisible();
  await expect(page.getByLabel("Explanation token position").getByRole("radio").first()).toHaveCSS("min-height", "44px");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  await page.getByRole("button", { name: /Attention/ }).click();
  await expect(page.getByRole("img", { name: /attention heatmap/ })).toBeVisible();
  const box = await page.getByLabel("Attention head heatmap").boundingBox();
  expect(box).not.toBeNull();
  expect(box!.width).toBeLessThanOrEqual(390);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test("runs input attribution from Chat and renders signed token contributions", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  const submitted = await mockReadyAttributionJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Attribute/ }).click();
  await page.getByLabel("Attribution response").fill("The selected token matters.");
  await page.getByRole("button", { name: "Run attribution" }).click();

  await expect(page.getByLabel("Input attribution result")).toBeVisible();
  await expect(page.getByLabel("Input attribution result").locator(".chat-attribution-tokens span"))
    .toHaveCount(generatedRun.tokens.length);
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator(".chat-history-row")).toHaveCount(2);
  const attributionRecords = await page.evaluate(() => JSON.parse(
    window.localStorage.getItem("safelens.localExplorer.importedRuns.v1") ?? "[]"
  ));
  expect(attributionRecords[0].sourceName).toContain("attribution job");
  expect(submitted()).toMatchObject({
    response: "The selected token matters.",
    objective: "response_token_logit",
    targetResponseIndex: 0,
    baseline: "pad_token",
    nSteps: 32
  });
});

test("runs steering from Chat and compares original with steered generation", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  const submitted = await mockReadySteeringJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Steer/ }).click();
  await expect(page.getByRole("button", { name: "Run steering" })).toBeEnabled();
  await page.getByRole("button", { name: "Run steering" }).click();

  const result = page.getByLabel("Steering comparison");
  await expect(result).toContainText("Original model response.");
  await expect(result).toContainText("Safer steered response.");
  await expect(result).toContainText("+0.250");
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator(".chat-history-row")).toHaveCount(2);
  const steeringRecords = await page.evaluate(() => JSON.parse(
    window.localStorage.getItem("safelens.localExplorer.importedRuns.v1") ?? "[]"
  ));
  expect(steeringRecords[0].sourceName).toContain("intervention job");
  expect(submitted()).toMatchObject({
    component: "resid_post",
    scale: 1,
    positionStart: 0,
    positionEnd: generatedRun.tokens.length,
    seed: 0,
    maxNewTokens: 16,
    temperature: 0
  });
});

test("restores a previous conversation and its analysis entry points", async ({ page }) => {
  await prepareHome(page);
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Work" })).toHaveCount(0);
  await page.locator(".chat-history-open").click();
  await expect(page.locator(".chat-turn-card")).toBeVisible();
  await expect(page.getByText("Activation cache ready")).toBeVisible();
  expect(await page.evaluate(() => window.location.pathname)).toBe("/");
});

test("restores a workspace NLA artifact inside its parent chat turn", async ({ page }) => {
  await prepareHome(page);
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "test-workspace",
        diagnostics: [],
        runs: [
          {
            runId: nlaDerivedRun.runId,
            sampleId: nlaDerivedRun.sampleId,
            modelName: nlaDerivedRun.modelName,
            modelSource: nlaDerivedRun.modelSource,
            tokenCount: nlaDerivedRun.tokens.length,
            layerCount: nlaDerivedRun.layers.length,
            artifactId: "nla-artifact",
            sourceName: "generated/nla-chat-nla-derived.explorer.json",
            modifiedAt: "2026-08-11T12:00:01Z",
            sizeBytes: 4_096,
            promptPreview: nlaDerivedRun.prompt,
            parentRun: { runId: nlaSourceRun.runId, sampleId: nlaSourceRun.sampleId }
          },
          {
            runId: nlaSourceRun.runId,
            sampleId: nlaSourceRun.sampleId,
            modelName: nlaSourceRun.modelName,
            modelSource: nlaSourceRun.modelSource,
            tokenCount: nlaSourceRun.tokens.length,
            layerCount: nlaSourceRun.layers.length,
            artifactId: "prompt-artifact",
            sourceName: "generated/prompt-chat-nla-source.explorer.json",
            modifiedAt: "2026-08-11T12:00:00Z",
            sizeBytes: 4_096,
            promptPreview: nlaSourceRun.prompt
          }
        ]
      }
    });
  });
  await page.route("**/api/runs/chat-nla-derived/samples/seed-0", async (route) => {
    await route.fulfill({ json: nlaDerivedRun });
  });
  await page.goto("/");

  const conversation = page.locator(".chat-history-row").filter({ hasText: nlaSourceRun.prompt });
  await expect(conversation).toHaveCount(1);
  await conversation.locator(".chat-history-open").click();
  await page.getByRole("button", { name: "Explain", exact: true }).click();
  await page.getByRole("radio", { name: /Token 2/ }).click();
  await expect(page.getByLabel("NLA output")).toContainText(
    "contrast between benign safety language and jailbreak framing"
  );
});

test("hides the bundled example conversation without deleting its artifact", async ({ page }) => {
  await prepareHome(page);
  await page.goto("/");

  await page.getByLabel(
    `Delete conversation ${realRun.prompt.slice(0, 45).trimEnd()}...`
  ).click();
  const dialog = page.getByRole("dialog", { name: "Delete this conversation?" });
  await expect(dialog).toContainText("Compare a benign safety explanation");
  await dialog.getByRole("button", { name: "Delete conversation" }).click();
  await expect(page.locator(".chat-history-row")).toHaveCount(0);

  await page.reload();
  await expect(page.locator(".chat-history-row")).toHaveCount(0);
  const hidden = await page.evaluate(() => window.localStorage.getItem("safelens.localExplorer.hiddenWork.v1"));
  expect(hidden).toContain(realRun.runId);
});

test("restores and deletes a generated conversation after explicit confirmation", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await mockReadyAttributionJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Attribute/ }).click();
  await page.getByRole("button", { name: "Run attribution" }).click();
  await expect(page.getByLabel("Input attribution result")).toBeVisible();

  await expect(page.locator(".chat-history-row")).toHaveCount(2);
  await page.getByRole("button", { name: "New chat" }).click();
  await expect(page.getByRole("heading", { name: "What would you like to inspect?" })).toBeVisible();
  await page.locator(".chat-history-row").filter({ hasText: "Why does the model focus" })
    .locator(".chat-history-open").click();
  await expect(page.locator(".chat-assistant-message")).toContainText("strongest residual alignment");
  await page.getByRole("button", { name: /Attribute/ }).click();
  await expect(page.getByRole("heading", { name: "Input attribution" })).toBeVisible();
  await expect(page.getByLabel("Attribution response")).toHaveValue(/strongest residual alignment/);
  await page.getByRole("button", { name: "Run attribution" }).click();
  await expect(page.getByLabel("Input attribution result")).toBeVisible();

  await page.getByLabel(
    `Delete conversation ${generatedRun.prompt}`
  ).click();
  const dialog = page.getByRole("dialog", { name: "Delete this conversation?" });
  await expect(dialog).toContainText("Why does the model focus");
  await expect(dialog.getByRole("button", { name: "Cancel" })).toBeFocused();

  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(dialog).toBeHidden();
  await page.getByLabel(
    `Delete conversation ${generatedRun.prompt}`
  ).click();
  await page.getByRole("dialog", { name: "Delete this conversation?" })
    .getByRole("button", { name: "Delete conversation" }).click();

  await expect(page.locator(".chat-history-row")).toHaveCount(1);
  await expect(page.getByRole("heading", { name: "What would you like to inspect?" })).toBeVisible();
  await expect(page.getByText("chat-home-generated")).toHaveCount(0);
  const saved = await page.evaluate(() => window.localStorage.getItem("safelens.localExplorer.importedRuns.v1"));
  expect(saved).not.toContain("chat-home-generated");
  expect(saved).not.toContain("chat-attribution-derived");
});

test("persists removal of a read-only workspace entry from Chat", async ({ page }) => {
  const workspaceConversation = {
    ...generatedRun,
    runId: "workspace-history-run",
    sampleId: "workspace-sample",
    prompt: "Inspect this saved workspace conversation.",
    metadata: {
      ...generatedRun.metadata,
      generatedContinuation: "Inspect this saved workspace conversation. The cached response is restored from the workspace."
    }
  };
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "test-workspace",
        diagnostics: [],
        runs: [{
          runId: "workspace-history-run",
          sampleId: "workspace-sample",
          modelName: "sshleifer/tiny-gpt2",
          modelSource: "huggingface",
          tokenCount: 12,
          layerCount: 2,
          artifactId: "workspace-artifact",
          sourceName: "generated/prompt-workspace-history-run.explorer.json",
          modifiedAt: new Date().toISOString(),
          sizeBytes: 4096
        }]
      }
    });
  });
  await page.route("**/api/prompt/options", async (route) => {
    await route.fulfill({ json: { models: ["sshleifer/tiny-gpt2"], templates: ["plain", "chat"], maxNewTokens: 512 } });
  });
  await page.route("**/api/runs/workspace-history-run/samples/workspace-sample", async (route) => {
    await route.fulfill({ json: workspaceConversation });
  });
  await page.goto("/");
  await expect(page.locator(".chat-history-row")).toHaveCount(2);

  await page.locator(".chat-history-row").filter({ hasText: "workspace-history-run" })
    .locator(".chat-history-open").click();
  await expect(page.locator(".chat-user-message")).toHaveText(workspaceConversation.prompt);
  await expect(page.locator(".chat-assistant-message")).toContainText("restored from the workspace");

  await page.getByLabel("Delete conversation Inspect this saved workspace conversation.").click();
  await page.getByRole("dialog", { name: "Delete this conversation?" })
    .getByRole("button", { name: "Delete conversation" }).click();
  await expect(page.getByText("workspace-history-run")).toHaveCount(0);

  await page.reload();
  await expect(page.locator(".chat-history-row")).toHaveCount(1);
  const hidden = await page.evaluate(() => window.localStorage.getItem("safelens.localExplorer.hiddenWork.v1"));
  expect(hidden).toContain("workspace-history-run");
});

for (const viewport of [
  { name: "mobile", width: 390, height: 844 },
  { name: "narrow", width: 320, height: 800 }
]) {
  test(`keeps the ${viewport.name} Chat interface inside the viewport`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await prepareHome(page);
    await page.goto("/");

    await expect(page.getByLabel("Analysis prompt")).toBeVisible();
    await expect(page.getByLabel("Analysis model")).toBeVisible();
    await expect(page.getByLabel("Maximum new tokens")).toBeVisible();
    await expect(page.getByRole("button", { name: "Open chat history" })).toBeVisible();
    await page.getByRole("button", { name: "Open chat history" }).click();
    await expect(page.getByRole("complementary", { name: "Chat history" })).toHaveClass(/open/);
    await expect(page.getByRole("button", { name: "New chat" })).toBeVisible();
    await page.getByRole("button", { name: "Close chat history" }).first().click();
    const layout = await page.evaluate(() => ({
      viewport: innerWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    }));
    expect(layout.document).toBeLessThanOrEqual(layout.viewport);
    expect(layout.body).toBeLessThanOrEqual(layout.viewport);
  });
}
