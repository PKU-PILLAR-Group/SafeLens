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
        models: ["sshleifer/tiny-gpt2"],
        templates: ["plain", "chat"],
        maxNewTokens: 512
      }
    });
  });
  await page.route("**/api/intervention/preflight", async (route) => {
    await route.fulfill({
      json: {
        modelAllowed: true,
        layerAvailable: true,
        componentSupported: true,
        positionRangeValid: true,
        targetTokenValid: true,
        referencesDiffer: true,
        targetTokenId: 0,
        targetTokenText: "target",
        positionStart: 0,
        positionEnd: generatedRun.tokens.length,
        canSubmit: true,
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
  await page.route("**/api/jobs/prompt", async (route) => {
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
}

test("shows built-in steering preset suggestions and inserts them on click", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");

  await page.getByLabel("Analysis prompt").fill(generatedRun.prompt);
  await page.getByLabel("Run analysis").click();
  await expect(page.getByText("Activation cache ready")).toBeVisible();

  await page.getByRole("button", { name: /Steer/ }).click();
  const toward = page.getByLabel("Steering desired behavior");
  await toward.click();
  await expect(page.getByRole("option", { name: /Refuse unsafe/ })).toBeVisible();
  await toward.fill("concise");
  await expect(page.getByRole("option", { name: /Be concise/ })).toBeVisible();
  await page.getByRole("option", { name: /Be concise/ }).click();
  await expect(toward).toHaveValue("Answer briefly and directly without filler.");
});

test("saves a custom steering preset and reuses it", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");

  await page.getByLabel("Analysis prompt").fill(generatedRun.prompt);
  await page.getByLabel("Run analysis").click();
  await expect(page.getByText("Activation cache ready")).toBeVisible();

  await page.getByRole("button", { name: /Steer/ }).click();
  const toward = page.getByLabel("Steering desired behavior");
  await toward.fill("Always answer in one word.");
  await page.getByRole("button", { name: /Save current Steer toward/ }).click();
  await page.getByLabel("Preset label").fill("One word");
  await page.getByRole("button", { name: "Save", exact: true }).click();

  await toward.fill("");
  await toward.click();
  await expect(page.getByRole("option", { name: /One word/ })).toBeVisible();

  await page.reload();
  await page.locator(".chat-history-open").first().click();
  await page.getByRole("button", { name: /Steer/ }).click();
  const towardAfterReload = page.getByLabel("Steering desired behavior");
  await towardAfterReload.fill("one");
  await expect(page.getByRole("option", { name: /One word/ })).toBeVisible();
});
