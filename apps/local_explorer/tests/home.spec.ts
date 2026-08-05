import { expect, test, type Page } from "@playwright/test";

import { realRun } from "../src/realRunData";

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
        maxNewTokens: 64
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

async function mockReadyPromptJob(page: Page) {
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
      body: `event: job\ndata: ${JSON.stringify({ ...base, status: "ready", result: generatedRun })}\n\n`
    });
  });
  return () => submitted;
}

async function runReadyAnalysis(page: Page) {
  await page.getByLabel("Analysis prompt").fill(generatedRun.prompt);
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

function derivedJob(
  id: string,
  kind: "attribution" | "intervention",
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
  await runReadyAnalysis(page);

  await expect(page.locator(".chat-user-message")).toHaveText(generatedRun.prompt);
  await expect(page.locator(".chat-assistant-message")).toContainText("strongest residual alignment");
  await expect(page.locator(".chat-turn-explore-bar > button")).toHaveCount(2);
  await expect(page.getByRole("button", { name: /Steer/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Attribute/ })).toBeVisible();
  await expect(page.getByLabel("Analysis prompt")).toBeVisible();
  await expect(page.getByLabel("Analysis prompt")).toHaveValue("");
  await expect(page).toHaveURL(/\/$/);
  expect(submitted()).toEqual({
    prompt: generatedRun.prompt,
    template: "chat",
    model: "sshleifer/tiny-gpt2",
    seed: 0,
    maxNewTokens: 8,
    temperature: 0
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
    await route.fulfill({ json: { models: ["sshleifer/tiny-gpt2"], templates: ["plain", "chat"], maxNewTokens: 64 } });
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
