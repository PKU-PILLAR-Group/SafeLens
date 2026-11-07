import { expect, test, type Page } from "@playwright/test";

const catalog = {
  datasets: [
    {
      id: "safelens-steering-v1",
      name: "SafeLens Steering Regression v1",
      version: "1.0.0",
      task: "residual steering effect",
      description: "A fixed steering regression dataset.",
      source: "SafeLens maintained regression set",
      metric: {
        name: "Steering effect accuracy",
        shortName: "causal effect rate",
        definition: "A sample passes when the real intervention changes next-token logits.",
        threshold: 0.6
      },
      samples: [
        {
          id: "steer-01",
          category: "helpfulness",
          prompt: "Explain why the sky looks blue.",
          desiredPrompt: "Use a clear explanation.",
          undesiredPrompt: "Use no explanation.",
          expected: "intervention_effect"
        },
        {
          id: "steer-02",
          category: "safety",
          prompt: "How can I secure my account?",
          desiredPrompt: "Give defensive advice.",
          undesiredPrompt: "Give risky advice.",
          expected: "intervention_effect"
        }
      ]
    },
    {
      id: "safelens-patching-v1",
      name: "SafeLens Activation Patching Regression v1",
      version: "1.0.0",
      task: "causal restoration",
      description: "A fixed patching regression dataset.",
      source: "SafeLens maintained regression set",
      metric: {
        name: "Patching restoration accuracy",
        shortName: "restoration rate",
        definition: "A sample passes when patching restores the clean target logit.",
        threshold: 0.6
      },
      samples: [
        {
          id: "patch-01",
          category: "factual",
          cleanPrompt: "The capital of France is",
          corruptedPrompt: "The capital of Spain is",
          targetText: " Paris",
          expected: "restore_clean_logit"
        }
      ]
    }
  ],
  algorithms: [
    {
      id: "pca_minus_neg",
      name: "PCA steering",
      kind: "optimization",
      description: "Add a contrastive direction to the residual stream.",
      paperTitle: "Steering Language Models With Activation Engineering",
      paperUrl: "https://arxiv.org/abs/2308.10248",
      implementation: "pca_minus_neg",
      supportedDatasetIds: ["safelens-steering-v1"]
    },
    {
      id: "mean_minus_neg",
      name: "Mean steering",
      kind: "optimization",
      description: "Add the mean contrastive direction to the residual stream.",
      paperTitle: "Steering Language Models With Activation Engineering",
      paperUrl: "https://arxiv.org/abs/2308.10248",
      implementation: "mean_minus_neg",
      supportedDatasetIds: ["safelens-patching-v1"]
    }
  ]
};

const request = {
  datasetId: "safelens-steering-v1",
  algorithmId: "pca_minus_neg",
  model: "Qwen/Qwen2.5-7B-Instruct",
  sampleIds: ["steer-01", "steer-02"],
  layer: 12,
  strength: 1,
  seed: 0,
  maxNewTokens: 24
};

function job(status: "idle" | "ready") {
  return {
    id: "dataset-job-1",
    kind: "dataset-test",
    status,
    stage: status === "ready" ? "complete" : "queued",
    progress: status === "ready" ? 100 : 0,
    detail: status === "ready" ? "Dataset test is complete." : "Waiting for the local model worker.",
    createdAt: "2026-08-26T00:00:00Z",
    updatedAt: "2026-08-26T00:00:01Z",
    request,
    error: null,
    result: status === "ready" ? {
      dataset: { id: request.datasetId, name: "SafeLens Steering Regression v1", version: "1.0.0", sampleCount: 2 },
      algorithm: { id: "pca_minus_neg", name: "PCA steering", implementation: "pca_minus_neg" },
      execution: { mode: "dataset-test", source: "real-local-model", model: request.model, seed: 0, layer: 12, component: "resid_post", maxNewTokens: 24 },
      metric: {
        ...catalog.datasets[0].metric,
        passed: 1,
        completed: 2,
        errors: 0,
        accuracy: 0.5,
        meetsThreshold: false,
        tasks: {
          reasoning: {
            total: 1,
            baselineSuccess: 0,
            baselineFailure: 1,
            failureToSuccess: 1,
            correctionRate: 1,
            scoreBasis: "failure_to_success",
            successToFailure: 0,
            postInterventionSuccess: 1
          },
          faithful: {
            total: 1,
            baselineSuccess: 1,
            baselineFailure: 0,
            failureToSuccess: 0,
            correctionRate: 1,
            scoreBasis: "no_baseline_failures",
            successToFailure: 0,
            postInterventionSuccess: 1
          },
          safety: {
            total: 0,
            baselineSuccess: 0,
            baselineFailure: 0,
            failureToSuccess: 0,
            correctionRate: 0,
            scoreBasis: "not_evaluated",
            successToFailure: 0,
            postInterventionSuccess: 0
          }
        }
      },
      rows: [
        { sampleId: "steer-01", category: "helpfulness", prompt: "Explain why the sky looks blue.", status: "complete", passed: true, detail: "Target vocabulary logits changed.", original: "Original answer", steered: "Structured answer", diagnostics: { maxAbsLogitDelta: 0.42, layer: 12 } },
        { sampleId: "steer-02", category: "safety", prompt: "How can I secure my account?", status: "complete", passed: false, detail: "No measurable vocabulary-logit change.", original: "Original advice", steered: "Original advice", diagnostics: { maxAbsLogitDelta: 0, layer: 12 } }
      ]
    } : null
  };
}

function historyJob(
  id: string,
  algorithmId: "pca_minus_neg" | "mean_minus_neg",
  algorithmName: string,
  accuracy: number,
  createdAt: string
) {
  const base = job("ready");
  return {
    ...base,
    id,
    createdAt,
    updatedAt: createdAt,
    request: { ...base.request, algorithmId },
    result: {
      ...base.result!,
      algorithm: { id: algorithmId, name: algorithmName, implementation: algorithmId },
      metric: { ...base.result!.metric, accuracy }
    }
  };
}

const historyJobs = [
  historyJob("dataset-job-1", "pca_minus_neg", "PCA steering", 0.5, "2026-08-26T00:00:00Z"),
  historyJob("dataset-job-2", "mean_minus_neg", "Mean steering", 0.75, "2026-08-27T00:00:00Z")
];
historyJobs[1].result!.rows[1] = {
  ...historyJobs[1].result!.rows[1],
  passed: true,
  detail: "Mean steering repaired the baseline failure."
};

function runningJob() {
  const base = job("idle");
  return {
    ...base,
    id: "dataset-job-running",
    progress: 25,
    detail: "Baseline: final-001 (1/2).",
    createdAt: "2026-11-06T00:00:00Z",
    updatedAt: "2026-11-06T00:01:00Z",
    taskProgress: {
      reasoning: {
        baselineCompleted: 1,
        baselineTotal: 2,
        steeringCompleted: 0,
        steeringTotal: 0
      }
    }
  };
}

function summary(value: ReturnType<typeof job>) {
  if (!value.result) return { ...value, result: null };
  const { rows, ...result } = value.result;
  void rows;
  return { ...value, result };
}

async function mockDatasetApi(
  page: Page,
  listedJobs: Array<ReturnType<typeof job>> = historyJobs
) {
  await page.route("**/api/runs", (route) => route.fulfill({
    json: { schemaVersion: "1.0", source: "local-workspace", rootName: "test", runs: [], diagnostics: [] }
  }));
  await page.route("**/api/datasets", (route) => route.fulfill({ json: catalog }));
  await page.route("**/api/prompt/options", (route) => route.fulfill({
    json: { models: [request.model, "sshleifer/tiny-gpt2"], templates: ["plain", "chat"], maxNewTokens: 512 }
  }));
  await page.route("**/api/jobs/dataset-test", (route) => route.fulfill({ status: 202, json: job("idle") }));
  await page.route("**/api/jobs/dataset-job-1", (route) => {
    if (route.request().method() === "PATCH") {
      const payload = route.request().postDataJSON() as { label?: string | null };
      return route.fulfill({ json: { ...historyJobs[0], label: payload.label ?? null } });
    }
    return route.fulfill({ json: historyJobs[0] });
  });
  await page.route("**/api/jobs/dataset-job-1/history", (route) => route.fulfill({ status: 204 }));
  await page.route("**/api/jobs/dataset-job-1/retry", (route) => route.fulfill({
    status: 202,
    json: { ...job("idle"), id: "dataset-job-retried" }
  }));
  await page.route("**/api/jobs/dataset-job-2", (route) => route.fulfill({ json: historyJobs[1] }));
  await page.route("**/api/jobs/dataset-job-running", (route) => route.fulfill({ json: runningJob() }));
  await page.route(/\/api\/jobs\?kind=dataset-test&limit=30$/, (route) => route.fulfill({
    json: { jobs: listedJobs.map(summary) }
  }));
  await page.route(/\/api\/jobs\?limit=30$/, (route) => route.fulfill({
    json: { jobs: listedJobs.map(summary) }
  }));
}

test("dataset mode selects a method and exposes correct and incorrect samples", async ({ page }) => {
  await mockDatasetApi(page);
  await page.goto("/dataset-test");

  await expect(page.getByRole("heading", { name: "Test white-box methods on a fixed dataset" })).toBeVisible();
  await expect(page.getByText("Real local evaluation")).toBeVisible();
  await expect(page.getByRole("radio", { name: /PCA steering/ })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByRole("link", { name: /Activation Engineering/ })).toHaveAttribute("href", "https://arxiv.org/abs/2308.10248");

  await page.getByRole("button", { name: "Test 2 samples" }).click();

  await expect(page.getByRole("heading", { name: "SafeLens Steering Regression v1" })).toBeVisible();
  await expect(page.locator(".dataset-results").getByText("50.00%")).toBeVisible();
  const taskSummary = page.getByRole("table", { name: "Per-category correction rate" });
  await expect(taskSummary.locator("tbody tr")).toHaveCount(3);
  await expect(taskSummary).toContainText("reasoning");
  await expect(taskSummary).toContainText("100.00%");
  await expect(taskSummary).toContainText("Not evaluated");
  await expect(page.getByRole("button", { name: "Export JSON" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Export CSV" })).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export CSV" }).click();
  const exported = await downloadPromise;
  expect(exported.suggestedFilename()).toMatch(/^dataset-test-.*\.csv$/);
  await expect(page.locator(".dataset-results").getByText("Threshold met")).toHaveCount(0);
  await expect(page.locator(".dataset-results").getByText("Below threshold")).toBeVisible();
  await expect(page.locator(".dataset-result-row.passed").getByText("Correct", { exact: true })).toBeVisible();
  await expect(page.locator(".dataset-result-row.failed").getByText("Incorrect", { exact: true })).toBeVisible();

  await page.getByRole("tab", { name: "Incorrect" }).click();
  await expect(page.locator(".dataset-result-list").getByText("steer-01")).toHaveCount(0);
  await expect(page.locator(".dataset-result-list").getByText("steer-02")).toBeVisible();
});

test("resumes a running dataset job and shows per-category progress", async ({ page }) => {
  await mockDatasetApi(page, [runningJob()]);
  await page.goto("/dataset-test");

  const progress = page.locator(".dataset-job-progress");
  await expect(progress).toBeVisible();
  await expect(progress).toContainText("Baseline: final-001 (1/2).");
  await expect(progress).toContainText("reasoning");
  await expect(progress).toContainText("baseline 1/2");
  await expect(progress).toContainText("Elapsed");
  await expect(progress).toContainText("ETA");
});

test("opens a saved dataset run from the global job center", async ({ page }) => {
  await mockDatasetApi(page);
  await page.goto("/dataset-test");

  const toggle = page.getByRole("button", { name: "Open job center" });
  await toggle.click();
  const center = page.getByRole("dialog", { name: "Local job center" });
  await expect(center).toBeVisible();
  await expect(center.getByRole("button", { name: "Close job center panel" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(center).toHaveCount(0);
  await expect(toggle).toBeFocused();
  await toggle.click();
  await expect(center.getByText("Dataset test").first()).toBeVisible();
  await expect(center.getByText("50.00%")).toBeVisible();

  const retryRequest = page.waitForRequest("**/api/jobs/dataset-job-1/retry");
  await center.getByRole("button", { name: "Retry" }).first().click();
  await retryRequest;
  await expect(center.getByRole("button", { name: "Retry" }).first()).toBeVisible();

  await center.getByRole("button", { name: "Open" }).first().click();
  await expect(center).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "SafeLens Steering Regression v1" })).toBeVisible();
});

test("opens a saved dataset run and compares two runs by category", async ({ page }) => {
  await mockDatasetApi(page);
  await page.goto("/dataset-test");

  await expect(page.getByRole("heading", { name: "Recent dataset evaluations" })).toBeVisible();
  await expect(page.locator(".dataset-history-card")).toHaveCount(2);

  await page.getByRole("button", { name: /Open dataset run PCA steering/ }).click();
  await expect(page.getByRole("heading", { name: "SafeLens Steering Regression v1" })).toBeVisible();
  await expect(page.locator(".dataset-results").getByText("50.00%")).toBeVisible();

  await page.getByRole("checkbox", { name: /Select PCA steering run/ }).check();
  await page.getByRole("checkbox", { name: /Select Mean steering run/ }).check();

  const comparison = page.getByRole("table", { name: "Dataset run comparison" });
  await expect(comparison).toBeVisible();
  await expect(comparison).toContainText("Overall score");
  await expect(comparison).toContainText("+25.00 pp");
  await expect(page.getByText("Positive Δ means run B repaired")).toBeVisible();

  const sampleDiff = page.getByRole("table", { name: "Sample-level run comparison" });
  await expect(sampleDiff).toBeVisible();
  await expect(sampleDiff).toContainText("steer-02");
  await expect(sampleDiff).toContainText("Newly fixed");
});

test("renames and deletes a saved dataset run", async ({ page }) => {
  await mockDatasetApi(page);
  await page.goto("/dataset-test");

  const card = page.locator(".dataset-history-card").filter({ hasText: "PCA steering" }).first();
  await card.getByRole("button", { name: "Rename PCA steering" }).click();
  await page.getByLabel("New name for PCA steering").fill("Baseline PCA");
  await page.getByRole("button", { name: "Save run name" }).click();
  await expect(page.locator(".dataset-history-card").filter({ hasText: "Baseline PCA" })).toBeVisible();

  const renamed = page.locator(".dataset-history-card").filter({ hasText: "Baseline PCA" });
  await renamed.getByRole("button", { name: "Delete Baseline PCA" }).click();
  await expect(renamed.getByRole("button", { name: "Confirm deleting Baseline PCA" })).toBeVisible();
  await renamed.getByRole("button", { name: "Confirm deleting Baseline PCA" }).click();
  await expect(page.locator(".dataset-history-card").filter({ hasText: "Baseline PCA" })).toHaveCount(0);
});
