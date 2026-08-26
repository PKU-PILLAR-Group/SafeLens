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
      id: "steering",
      name: "Residual steering",
      kind: "optimization",
      description: "Add a contrastive direction to the residual stream.",
      paperTitle: "Steering Language Models With Activation Engineering",
      paperUrl: "https://arxiv.org/abs/2308.10248",
      implementation: "contrastive_mean_difference",
      supportedDatasetIds: ["safelens-steering-v1"]
    },
    {
      id: "patching",
      name: "Activation patching",
      kind: "optimization",
      description: "Replace corrupt residual activations with clean activations.",
      paperTitle: "Towards Best Practices of Activation Patching in Language Models: Metrics and Methods",
      paperUrl: "https://arxiv.org/abs/2309.16042",
      implementation: "residual_stream_replacement",
      supportedDatasetIds: ["safelens-patching-v1"]
    }
  ]
};

const request = {
  datasetId: "safelens-steering-v1",
  algorithmId: "steering",
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
      algorithm: { id: "steering", name: "Residual steering", implementation: "contrastive_mean_difference" },
      execution: { mode: "dataset-test", source: "real-local-model", model: request.model, seed: 0, layer: 12, component: "resid_post", maxNewTokens: 24 },
      metric: { ...catalog.datasets[0].metric, passed: 1, completed: 2, errors: 0, accuracy: 0.5, meetsThreshold: false },
      rows: [
        { sampleId: "steer-01", category: "helpfulness", prompt: "Explain why the sky looks blue.", status: "complete", passed: true, detail: "Target vocabulary logits changed.", original: "Original answer", steered: "Structured answer", diagnostics: { maxAbsLogitDelta: 0.42, layer: 12 } },
        { sampleId: "steer-02", category: "safety", prompt: "How can I secure my account?", status: "complete", passed: false, detail: "No measurable vocabulary-logit change.", original: "Original advice", steered: "Original advice", diagnostics: { maxAbsLogitDelta: 0, layer: 12 } }
      ]
    } : null
  };
}

async function mockDatasetApi(page: Page) {
  await page.route("**/api/runs", (route) => route.fulfill({
    json: { schemaVersion: "1.0", source: "local-workspace", rootName: "test", runs: [], diagnostics: [] }
  }));
  await page.route("**/api/datasets", (route) => route.fulfill({ json: catalog }));
  await page.route("**/api/prompt/options", (route) => route.fulfill({
    json: { models: [request.model, "sshleifer/tiny-gpt2"], templates: ["plain", "chat"], maxNewTokens: 512 }
  }));
  await page.route("**/api/jobs/dataset-test", (route) => route.fulfill({ status: 202, json: job("idle") }));
  await page.route("**/api/jobs/dataset-job-1", (route) => route.fulfill({ json: job("ready") }));
}

test("dataset mode selects a method and exposes correct and incorrect samples", async ({ page }) => {
  await mockDatasetApi(page);
  await page.goto("/dataset-test");

  await expect(page.getByRole("heading", { name: "Test white-box methods on a fixed dataset" })).toBeVisible();
  await expect(page.getByText("Real local evaluation")).toBeVisible();
  await expect(page.getByRole("radio", { name: /Residual steering/ })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByRole("link", { name: /Activation Engineering/ })).toHaveAttribute("href", "https://arxiv.org/abs/2308.10248");

  await page.getByRole("button", { name: "Test 2 samples" }).click();

  await expect(page.getByRole("heading", { name: "SafeLens Steering Regression v1" })).toBeVisible();
  await expect(page.getByText("50%")).toBeVisible();
  await expect(page.getByText("Threshold met")).toHaveCount(0);
  await expect(page.getByText("Below threshold")).toBeVisible();
  await expect(page.locator(".dataset-result-row.passed").getByText("Correct", { exact: true })).toBeVisible();
  await expect(page.locator(".dataset-result-row.failed").getByText("Incorrect", { exact: true })).toBeVisible();

  await page.getByRole("tab", { name: "Incorrect" }).click();
  await expect(page.locator(".dataset-result-list").getByText("steer-01")).toHaveCount(0);
  await expect(page.locator(".dataset-result-list").getByText("steer-02")).toBeVisible();
});
