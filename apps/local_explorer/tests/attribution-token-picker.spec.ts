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
        maxNewTokens: 64
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
        tokens: pieces.map((text, index) => ({ index, tokenId: 2_000 + index, text })),
        truncated: false
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

test("renders clickable tokens from the response and updates the selected target", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");

  await page.getByLabel("Analysis prompt").fill(generatedRun.prompt);
  await page.getByLabel("Run analysis").click();
  await expect(page.getByText("Activation cache ready")).toBeVisible();

  await page.getByRole("button", { name: /Attribute/ }).click();
  const picker = page.getByRole("group", { name: "Response tokens" });
  await expect(picker).toBeVisible();
  await expect(picker.getByRole("button")).toHaveCount(9);
  await expect(picker.getByRole("button", { name: /The/ })).toHaveAttribute("aria-pressed", "true");

  await picker.getByRole("button", { name: /residual/ }).click();
  await expect(picker.getByRole("button", { name: /residual/ })).toHaveAttribute("aria-pressed", "true");
});

test("clamps the selected target when the response shrinks", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");

  await page.getByLabel("Analysis prompt").fill(generatedRun.prompt);
  await page.getByLabel("Run analysis").click();
  await expect(page.getByText("Activation cache ready")).toBeVisible();

  await page.getByRole("button", { name: /Attribute/ }).click();
  const picker = page.getByRole("group", { name: "Response tokens" });
  await picker.getByRole("button", { name: /alignment/ }).click();
  await expect(picker.getByRole("button", { name: /alignment/ })).toHaveAttribute("aria-pressed", "true");

  await page.getByLabel("Attribution response").fill("Short answer.");
  await expect(picker.getByRole("button")).toHaveCount(3);
  await expect(picker.getByRole("button", { name: /\./ })).toHaveAttribute("aria-pressed", "true");
});
