import { expect, test, type Page } from "@playwright/test";

async function openHome(page: Page) {
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "test-workspace",
        runs: []
      }
    });
  });
  await page.goto("/");
}

test("opens on a focused home with runs, NLA profiles, and the visualization library", async ({ page }) => {
  await openHome(page);

  await expect(page.getByRole("heading", { name: "SafeLens", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recent runs" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "NLA profiles" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Visualization library" })).toBeVisible();
  await expect(page.locator(".home-viz-card")).toHaveCount(10);
  await expect(page.getByText("Qwen2.5-7B · L20")).toBeVisible();

  const width = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth
  }));
  expect(width.document).toBeLessThanOrEqual(width.viewport);
});

test("filters the visualization catalog and opens a live workspace view", async ({ page }) => {
  await openHome(page);

  await page.getByRole("tab", { name: "Explanations" }).click();
  await expect(page.locator(".home-viz-card")).toHaveCount(2);
  await expect(page.getByRole("button", { name: /NLA result browser/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /NLA fidelity heatmap/ })).toBeVisible();

  await page.getByRole("tab", { name: "Attention" }).click();
  await page.getByRole("button", { name: /Attention pattern browser/ }).click();
  await expect(page).toHaveURL(/\/explorer\?.*view=attention/);
  await expect(page.getByRole("tab", { name: "Attention" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("heading", { name: "Attention Pattern" })).toBeVisible();
});

test("starts a new analysis and returns to home without a reload", async ({ page }) => {
  await openHome(page);

  await page.getByRole("button", { name: "New analysis" }).click();
  await expect(page).toHaveURL(/\/explorer\?.*setup=prompt/);
  await expect(page.getByRole("dialog", { name: "Runs and samples" })).toBeVisible();
  await page.getByRole("button", { name: "Close run library" }).click();
  await page.getByRole("button", { name: "Return to SafeLens home" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Visualization library" })).toBeVisible();
});

for (const viewport of [
  { name: "mobile", width: 390, height: 844 },
  { name: "narrow", width: 320, height: 800 }
]) {
  test(`keeps the ${viewport.name} home interactive without horizontal overflow`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await openHome(page);

    await expect(page.getByRole("button", { name: "New analysis" })).toBeVisible();
    await expect(page.locator(".home-viz-card")).toHaveCount(10);
    const layout = await page.evaluate(() => ({
      viewport: window.innerWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    }));
    expect(layout.document).toBeLessThanOrEqual(layout.viewport);
    expect(layout.body).toBeLessThanOrEqual(layout.viewport);

    await page.getByRole("tab", { name: "Causal" }).click();
    await expect(page.locator(".home-viz-card")).toHaveCount(2);
  });
}
