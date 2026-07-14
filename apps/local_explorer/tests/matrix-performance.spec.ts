import { expect, test, type Locator } from "@playwright/test";

import { realRun } from "../src/realRunData";

test("keeps a 200k-cell matrix viewport-rendered and interactive", async ({ page }, testInfo) => {
  test.setTimeout(60_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  const run = performanceRun(2_000, 100);
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "performance-fixture",
        runs: [{
          runId: run.runId,
          sampleId: run.sampleId,
          modelName: run.modelName,
          modelSource: run.modelSource,
          tokenCount: run.tokens.length,
          layerCount: run.layers.length,
          artifactId: "perf-200k",
          sourceName: "perf-200k.explorer.json",
          modifiedAt: "2026-07-13T12:00:00+00:00",
          sizeBytes: 20_000_000
        }],
        diagnostics: []
      }
    });
  });
  await page.route("**/api/runs/perf-200k/samples/canvas-200k", async (route) => {
    await route.fulfill({ json: run });
  });

  const started = Date.now();
  await page.goto("/?run=perf-200k&sample=canvas-200k&view=residual&token=10&layer=999");
  const canvas = page.locator(".matrix-canvas");
  await expect(canvas).toBeVisible({ timeout: 30_000 });
  await expect.poll(async () => page.evaluate(
    () => performance.getEntriesByName("safelens:first-usable").length
  )).toBeGreaterThan(0);
  const firstUsableMs = await page.evaluate(() => {
    const entry = performance.getEntriesByName("safelens:first-usable")[0];
    return entry?.startTime ?? Number.POSITIVE_INFINITY;
  });
  expect(firstUsableMs).toBeLessThan(10_000);
  const readyView = await page.evaluate(() => {
    const entry = performance.getEntriesByName("safelens:view-ready").at(-1) as PerformanceMark | undefined;
    return (entry?.detail as { view?: string } | undefined)?.view;
  });
  expect(readyView).toBe("residual");
  const layerSelector = page.getByLabel("Selected layer", { exact: true });
  await expect(layerSelector).toHaveValue("999");
  expect(Date.now() - started).toBeLessThan(10_000);
  expect(pageErrors).toEqual([]);
  await expect(page.locator(".matrix-cell")).toHaveCount(0);
  await expect(page.getByLabel("Matrix rendering status")).toContainText("canvas");
  const overview = page.getByRole("button", { name: "Navigate Canvas matrix overview" });
  await expect(overview).toBeVisible();
  const overviewBox = await overview.boundingBox();
  expect(overviewBox?.width).toBeLessThanOrEqual(210);
  expect(overviewBox?.height).toBe(56);
  const overviewPainted = await overview.locator("canvas").evaluate((element) => {
    const canvas = element as HTMLCanvasElement;
    const context = canvas.getContext("2d");
    if (!context) return false;
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    for (let index = 0; index < pixels.length; index += 64) {
      if (pixels[index] < 235 || pixels[index + 1] < 235 || pixels[index + 2] < 235) return true;
    }
    return false;
  });
  expect(overviewPainted).toBe(true);
  const matrixScroll = page.locator(".matrix-scroll");
  await overview.focus();
  await overview.press("Home");
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBe(0);
  await overview.click({ position: { x: overviewBox!.width / 2, y: overviewBox!.height / 2 } });
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await overview.press("Home");
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBe(0);
  await overview.press("End");
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await expect(canvas).toHaveAttribute("data-column-header-sticky", "true");
  const headerSelectionUrl = page.url();
  await canvas.click({ position: { x: 140, y: 10 } });
  expect(page.url()).toBe(headerSelectionUrl);
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await overview.press("Home");
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBe(0);

  await expect.poll(async () => Number(await canvas.getAttribute("data-visible-cells"))).toBeGreaterThan(0);
  const visibleCells = Number(await canvas.getAttribute("data-visible-cells"));
  const drawMs = Number(await canvas.getAttribute("data-draw-ms"));
  expect(visibleCells).toBeLessThan(3_000);
  expect(drawMs).toBeLessThan(100);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    await page.evaluate(() => window.innerWidth)
  );

  const hasPaintedPixels = await canvas.evaluate((element) => {
    const context = (element as HTMLCanvasElement).getContext("2d");
    if (!context) return false;
    const pixels = context.getImageData(0, 0, element.width, element.height).data;
    for (let index = 0; index < pixels.length; index += 64) {
      if (pixels[index] < 245 || pixels[index + 1] < 245 || pixels[index + 2] < 245) return true;
    }
    return false;
  });
  expect(hasPaintedPixels).toBe(true);

  await layerSelector.selectOption("0");
  await expect(page).toHaveURL(/layer=0/);
  const matrixControls = page.getByLabel("Matrix controls");
  await matrixControls.getByLabel("Pan matrix").click();
  const residualSelectionUrl = page.url();
  await matrixScroll.scrollIntoViewIfNeeded();
  const residualViewportBox = await matrixScroll.boundingBox();
  expect(residualViewportBox).not.toBeNull();
  await page.mouse.move(
    residualViewportBox!.x + residualViewportBox!.width * 0.78,
    residualViewportBox!.y + residualViewportBox!.height * 0.78
  );
  await page.mouse.down();
  await page.mouse.move(
    residualViewportBox!.x + residualViewportBox!.width * 0.28,
    residualViewportBox!.y + residualViewportBox!.height * 0.28,
    { steps: 8 }
  );
  await page.mouse.up();
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  expect(page.url()).toBe(residualSelectionUrl);
  await matrixScroll.dblclick({ position: { x: 180, y: 120 } });
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollLeft)).toBe(0);
  await expect.poll(() => matrixScroll.evaluate((element) => element.scrollTop)).toBe(0);
  await expect(matrixControls.getByLabel("Select matrix cells")).toHaveAttribute("aria-pressed", "true");
  expect(page.url()).toBe(residualSelectionUrl);
  await canvas.hover({ position: { x: 56, y: 44 } });
  await expect.poll(async () => Number(await canvas.getAttribute("data-hover-ms"))).toBeLessThan(100);
  await expect.poll(async () => page.evaluate(
    () => performance.getEntriesByName("safelens:matrix-hover").length
  )).toBeGreaterThan(0);
  const hoverEvent = await page.evaluate(() => {
    const entry = performance.getEntriesByName("safelens:matrix-hover").at(-1) as PerformanceMark | undefined;
    return (entry?.detail as { latencyMs?: number } | undefined)?.latencyMs ?? Number.POSITIVE_INFINITY;
  });
  expect(hoverEvent).toBeLessThan(100);
  const diagnostics = await page.evaluate(() => ({
    count: window.__SAFELENS_PERFORMANCE__?.length ?? 0,
    latest: window.__SAFELENS_PERFORMANCE__?.at(-1)?.name
  }));
  expect(diagnostics.count).toBeGreaterThan(0);
  expect(diagnostics.count).toBeLessThanOrEqual(100);
  expect(diagnostics.latest).toBe("matrix-hover");
  await expect(page.locator(".matrix-tooltip")).toContainText("layer_0.resid_post");
  await expect(page.getByLabel("Copy hovered cache key")).toBeEnabled();
  await canvas.click({ position: { x: 56, y: 44 } });
  await expect(page).toHaveURL(/token=0/);
  await canvas.press("ArrowRight");
  await expect(page).toHaveURL(/token=1/);
  const descriptionId = await canvas.getAttribute("aria-describedby");
  const liveDescription = page.locator(`[id="${descriptionId}"]`);
  await expect(liveDescription).toContainText("token 1");
  await expect(liveDescription).toContainText("cache key layer_0.resid_post");
  await canvas.press("Shift+Enter");
  await expect(page.getByLabel("Matrix selection summary")).toContainText("L0 · token 1");
  await canvas.press("Space");
  await expect(page.getByLabel(/^Compare pinned evidence/)).toHaveAttribute("aria-label", /\(4\)/);

  const box = await canvas.boundingBox();
  expect(box).not.toBeNull();
  await page.mouse.move(box!.x + 56, box!.y + 44);
  await page.mouse.down();
  await page.mouse.move(box!.x + 113, box!.y + 44, { steps: 4 });
  await page.mouse.up();
  await expect(page).toHaveURL(/range=0-3/);
  await testInfo.attach("canvas-200k-desktop", {
    body: await page.screenshot(),
    contentType: "image/png"
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(canvas).toBeVisible();
  await canvas.scrollIntoViewIfNeeded();
  await expect.poll(async () => Number(await canvas.getAttribute("data-draw-ms"))).toBeLessThan(100);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  expect(Number(await canvas.getAttribute("data-visible-cells"))).toBeLessThan(2_000);
  await testInfo.attach("canvas-200k-mobile", {
    body: await page.screenshot(),
    contentType: "image/png"
  });

  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  expect(await canvas.evaluate((element) => getComputedStyle(element).forcedColorAdjust)).toBe("none");
  await canvas.focus();
  await expect(canvas).toBeFocused();
  await testInfo.attach("canvas-200k-forced-colors", {
    body: await page.screenshot(),
    contentType: "image/png"
  });
});

test("viewport-renders every large specialized matrix without losing selection semantics", async ({ page }, testInfo) => {
  test.setTimeout(60_000);
  const run = specializedPerformanceRun();
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "specialized-performance-fixture",
        runs: [{
          runId: run.runId,
          sampleId: run.sampleId,
          modelName: run.modelName,
          modelSource: run.modelSource,
          tokenCount: run.tokens.length,
          layerCount: run.layers.length,
          artifactId: "specialized-large",
          sourceName: "specialized-large.explorer.json",
          modifiedAt: "2026-07-13T12:00:00+00:00",
          sizeBytes: 4_000_000
        }],
        diagnostics: []
      }
    });
  });
  await page.route("**/api/runs/perf-specialized/samples/canvas-specialized", async (route) => {
    await route.fulfill({ json: run });
  });

  await page.goto("/?run=perf-specialized&sample=canvas-specialized&view=attention&layer=0&token=0&source=0&target=0");
  const attention = page.getByRole("grid", { name: /Attention pattern Canvas matrix/ });
  await assertViewportCanvas(attention, page, ".attention-pattern-cell");
  await expect(page.getByRole("button", { name: /Navigate Attention pattern Canvas matrix/ })).toBeVisible();
  const attentionTooltip = page.locator(".attention-pair-tooltip");
  await expect(attentionTooltip).toContainText("extraordinarily-long-specialized-token-fragment");
  await expect(attentionTooltip).toContainText("source position 0 · id 87654");
  await expect(attentionTooltip).toContainText("destination position 0 · id 87654");
  await dragCanvasRange(page, attention, { x: 85, y: 144 }, { x: 160, y: 144 });
  await expect(page.getByLabel("Source token range summary")).toContainText("0–3");
  await expect(page).toHaveURL(/range=0-3/);
  await expect(attention).toHaveAttribute("data-selected-range", "0-3");
  await page.getByLabel("Clear source token range").click();
  await attention.click({ position: { x: 112, y: 66 } });
  await expect(page).toHaveURL(/source=1/);
  await expect(page).toHaveURL(/target=1/);
  await attention.press("ArrowDown");
  await expect(page).toHaveURL(/target=2/);
  await expect(page.locator(".attention-pair-tooltip")).toContainText("probability");
  await attention.press("Shift+Enter");
  await expect(attention).toHaveAttribute("data-comparison-cell", "2:1");
  await attention.press("ArrowLeft");
  await expect(page).toHaveURL(/source=0/);
  await attention.press("Control+Enter");
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; sourceTokenIndex?: number }) =>
      pin.view === "attention" && pin.tokenIndex === 2 && pin.sourceTokenIndex === 0
    );
  })).toBe(true);
  await attention.press("ArrowRight");
  await expect(page).toHaveURL(/source=1/);
  const attentionPrimaryUrl = page.url();
  await attention.click({ position: { x: 137, y: 90 }, modifiers: ["Shift"] });
  expect(page.url()).toBe(attentionPrimaryUrl);
  await expect(page.getByLabel("Attention matrix selection summary")).toContainText("D2 · S2");
  await expect(attention).toHaveAttribute("data-comparison-cell", "2:2");
  await attention.click({ position: { x: 137, y: 90 }, modifiers: ["Control"] });
  expect(page.url()).toBe(attentionPrimaryUrl);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; sourceTokenIndex?: number }) =>
      pin.view === "attention" && pin.tokenIndex === 2 && pin.sourceTokenIndex === 2
    );
  })).toBe(true);
  await expect(attention).toHaveAttribute("aria-keyshortcuts", /Space/);
  await attention.press("Space");
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string }) => pin.view === "attention");
  })).toBe(true);
  const attentionViewport = page.locator(".attention-matrix-scroll");
  const attentionControls = page.getByLabel("Attention matrix controls", { exact: true });
  await attentionControls.getByLabel("Pan attention matrix").click();
  const attentionSelectionUrl = page.url();
  await attentionViewport.scrollIntoViewIfNeeded();
  const attentionViewportBox = await attentionViewport.boundingBox();
  expect(attentionViewportBox).not.toBeNull();
  await page.mouse.move(
    attentionViewportBox!.x + attentionViewportBox!.width * 0.78,
    attentionViewportBox!.y + attentionViewportBox!.height * 0.78
  );
  await page.mouse.down();
  await page.mouse.move(
    attentionViewportBox!.x + attentionViewportBox!.width * 0.28,
    attentionViewportBox!.y + attentionViewportBox!.height * 0.28,
    { steps: 8 }
  );
  await page.mouse.up();
  await expect.poll(() => attentionViewport.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  await expect.poll(() => attentionViewport.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  expect(page.url()).toBe(attentionSelectionUrl);
  await expect(attention).toHaveAttribute("data-column-header-sticky", "true");
  await attentionControls.getByLabel("Select attention matrix cells").click();
  await attention.click({ position: { x: 140, y: 10 } });
  expect(page.url()).toBe(attentionSelectionUrl);
  await expect.poll(() => attentionViewport.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await attentionViewport.dblclick({ position: { x: 180, y: 120 } });
  await expect.poll(() => attentionViewport.evaluate((element) => element.scrollLeft)).toBe(0);
  await expect.poll(() => attentionViewport.evaluate((element) => element.scrollTop)).toBe(0);
  await expect(attentionControls.getByLabel("Select attention matrix cells"))
    .toHaveAttribute("aria-pressed", "true");
  expect(page.url()).toBe(attentionSelectionUrl);

  await page.goto("/?run=perf-specialized&sample=canvas-specialized&view=mlp&layer=0&token=0&neuron=L0N0000&metric=mlp_signed_activation");
  const mlp = page.getByRole("grid", { name: /MLP activation Canvas matrix/ });
  await assertViewportCanvas(mlp, page, ".mlp-activation-cell");
  await expect(mlp).toHaveAttribute("aria-colcount", "2000");
  await expect(page.getByLabel("Neuron search results")).toHaveText("2000/2000");
  await expect(page.getByRole("button", { name: /Navigate MLP activation Canvas matrix/ })).toBeVisible();
  await mlp.focus();
  await expect(page.locator(".mlp-activation-tooltip"))
    .toContainText("extraordinarily-long-specialized-token-fragment");
  await expect(page.locator(".mlp-activation-tooltip"))
    .toContainText("token position 0 · id 87654");
  await dragCanvasRange(page, mlp, { x: 91, y: 65 }, { x: 91, y: 149 });
  await expect(page.getByLabel("Token range summary")).toContainText("1–4");
  await expect(page).toHaveURL(/range=1-4/);
  await expect(mlp).toHaveAttribute("data-selected-range", "1-4");
  await page.getByLabel("Clear token range").click();
  await mlp.click({ position: { x: 124, y: 65 } });
  await expect(page).toHaveURL(/token=1/);
  await expect(page).toHaveURL(/neuron=L0N0001/);
  await mlp.press("ArrowRight");
  await expect(page).toHaveURL(/neuron=L0N0002/);
  await expect(page.locator(".mlp-activation-tooltip")).toContainText("signed raw");
  const mlpPrimaryUrl = page.url();
  await mlp.click({ position: { x: 190, y: 93 }, modifiers: ["Shift"] });
  expect(page.url()).toBe(mlpPrimaryUrl);
  await expect(page.getByLabel("MLP matrix selection summary")).toContainText("T2 · L0N0003");
  await expect(mlp).toHaveAttribute("data-comparison-cell", "2:3");
  await mlp.click({ position: { x: 223, y: 121 }, modifiers: ["Control"] });
  expect(page.url()).toBe(mlpPrimaryUrl);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; neuronId?: string }) =>
      pin.view === "mlp" && pin.tokenIndex === 3 && pin.neuronId === "L0N0004"
    );
  })).toBe(true);
  await expect(mlp).toHaveAttribute("aria-keyshortcuts", /Space/);
  await mlp.press("Space");
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string }) => pin.view === "mlp");
  })).toBe(true);

  const mlpControls = page.getByLabel("MLP matrix controls", { exact: true });
  const mlpLegend = page.getByLabel("MLP activation legend");
  await mlpControls.getByRole("combobox").selectOption("mlp_absolute_activation");
  await expect(page).toHaveURL(/metric=mlp_absolute_activation/);
  await expect(page).toHaveURL(/token=1/);
  await expect(page).toHaveURL(/neuron=L0N0002/);
  await expect(mlpLegend).toHaveAttribute("data-domain", "sequential");
  await expect(mlpLegend).toContainText("sequential domain from zero");
  const mlpDescriptionId = await mlp.getAttribute("aria-describedby");
  expect(mlpDescriptionId).not.toBeNull();
  const mlpDescription = page.locator(`[id="${mlpDescriptionId}"]`);
  await expect(mlpDescription).toContainText("absolute raw activation");
  await expect(page.getByLabel("Selected MLP activation", { exact: true }))
    .toContainText("absolute raw activation");
  await mlpControls.getByRole("combobox").selectOption("mlp_normalized_activation");
  await expect(mlpLegend).toContainText("fixed 0–1 domain");
  await expect(mlpDescription).toContainText("normalized activation magnitude");
  await mlpControls.getByRole("combobox").selectOption("mlp_signed_activation");
  await expect(mlpLegend).toHaveAttribute("data-domain", "diverging");
  await expect(mlpLegend).toContainText("symmetric zero-centered domain");

  const neuronSearch = page.getByLabel("Search retained neurons");
  await neuronSearch.fill("1999");
  await expect(page.getByLabel("Neuron search results")).toHaveText("1/2000");
  await expect(page).toHaveURL(/neuron=L0N1999/);
  await expect(page.getByLabel("Selected MLP activation", { exact: true })).toContainText("L0N1999");
  await expect(page.locator(".mlp-neuron-label")).toHaveCount(1);

  await neuronSearch.fill("");
  const fullMlp = page.getByRole("grid", { name: /MLP activation Canvas matrix/ });
  await expect(fullMlp).toHaveAttribute("aria-colcount", "2000");
  await expect(page.getByLabel("Neuron search results")).toHaveText("2000/2000");
  await expect(page).toHaveURL(/neuron=L0N1999/);
  await expect.poll(() => page.locator(".mlp-matrix-scroll").evaluate((element) => element.scrollLeft))
    .toBeGreaterThan(0);
  expect(Number(await fullMlp.getAttribute("data-visible-cells"))).toBeLessThan(2_000);
  await fullMlp.press("ArrowLeft");
  await expect(page).toHaveURL(/neuron=L0N1998/);
  await testInfo.attach("mlp-2000-neurons-desktop", {
    body: await page.locator(".mlp-matrix-section").screenshot(),
    contentType: "image/png"
  });

  await page.goto("/?run=perf-specialized&sample=canvas-specialized&view=attribution&layer=0&token=0&track=residual_direction&metric=residual_direction&normalization=raw");
  const attribution = page.getByRole("grid", { name: /Residual direction projection Canvas attribution matrix/ });
  await assertViewportCanvas(attribution, page, ".attribution-value-cell");
  const negativeAttributionPixel = await sampleCanvasPixel(attribution, 84, 36);
  const positiveAttributionPixel = await sampleCanvasPixel(attribution, 489, 441);
  expect(negativeAttributionPixel.blue).toBeGreaterThan(negativeAttributionPixel.red);
  expect(positiveAttributionPixel.red).toBeGreaterThan(positiveAttributionPixel.blue);
  await expect(page.getByRole("button", { name: /Navigate Residual direction projection Canvas attribution matrix/ })).toBeVisible();
  await attribution.focus();
  await expect(page.locator(".attribution-tooltip"))
    .toContainText("extraordinarily-long-specialized-token-fragment");
  await expect(page.locator(".attribution-tooltip"))
    .toContainText("token position 0 · id 87654");
  await dragCanvasRange(page, attribution, { x: 111, y: 36 }, { x: 192, y: 36 });
  await expect(page.getByLabel("Token range summary")).toContainText("1–4");
  await expect(page).toHaveURL(/range=1-4/);
  await expect(attribution).toHaveAttribute("data-selected-range", "1-4");
  await page.getByLabel("Clear token range").click();
  await attribution.click({ position: { x: 111, y: 63 } });
  await expect(page).toHaveURL(/layer=1/);
  await expect(page).toHaveURL(/token=1/);
  await attribution.press("ArrowDown");
  await expect(page).toHaveURL(/layer=2/);
  await expect(page.locator(".attribution-tooltip")).toContainText("stored value");
  const attributionPrimaryUrl = page.url();
  await attribution.click({ position: { x: 139, y: 117 }, modifiers: ["Shift"] });
  expect(page.url()).toBe(attributionPrimaryUrl);
  await expect(page.getByLabel("Attribution matrix selection summary")).toContainText("L3 · T2");
  await expect(attribution).toHaveAttribute("data-comparison-cell", "3:2");
  await attribution.click({ position: { x: 166, y: 144 }, modifiers: ["Control"] });
  expect(page.url()).toBe(attributionPrimaryUrl);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; layer?: number }) =>
      pin.view === "attribution" && pin.tokenIndex === 3 && pin.layer === 4
    );
  })).toBe(true);
  await expect(attribution).toHaveAttribute("aria-keyshortcuts", /Space/);
  await attribution.press("Space");
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string }) => pin.view === "attribution");
  })).toBe(true);

  await page.getByLabel("Attribution matrix controls").getByRole("combobox")
    .selectOption("token_safety_proxy");
  const unsignedAttribution = page.getByRole("grid", { name: /Token safety proxy Canvas attribution matrix/ });
  await expect(unsignedAttribution).toBeVisible();
  await expect.poll(async () => Number(await unsignedAttribution.getAttribute("data-visible-cells")))
    .toBeGreaterThan(0);
  const unsignedAttributionPixel = await sampleCanvasPixel(unsignedAttribution, 489, 441);
  expect(unsignedAttributionPixel.red).toBeGreaterThan(unsignedAttributionPixel.blue);

  await page.goto("/?run=perf-specialized&sample=canvas-specialized&view=nla&layer=0&token=0&metric=nla_cosine");
  const nla = page.getByRole("grid", { name: /NLA fidelity Canvas matrix/ });
  await assertViewportCanvas(nla, page, ".nla-fidelity-cell");
  await expect(page.getByRole("button", { name: /Navigate NLA fidelity Canvas matrix/ })).toBeVisible();
  await nla.focus();
  await expect(page.locator(".nla-fidelity-tooltip"))
    .toContainText("extraordinarily-long-specialized-token-fragment");
  await expect(page.locator(".nla-fidelity-tooltip"))
    .toContainText("token position 0 · id 87654");
  await dragCanvasRange(page, nla, { x: 135, y: 41 }, { x: 216, y: 41 });
  await expect(page.getByLabel("Token range summary")).toContainText("1–4");
  await expect(page).toHaveURL(/range=1-4/);
  await expect(nla).toHaveAttribute("data-selected-range", "1-4");
  await page.getByLabel("Clear token range").click();
  const nlaPrimaryUrl = page.url();
  await nla.click({ position: { x: 135, y: 70 }, modifiers: ["Shift"] });
  expect(page.url()).toBe(nlaPrimaryUrl);
  await expect(page.getByLabel("NLA matrix selection summary")).toContainText("L1 resid · T1");
  await expect(nla).toHaveAttribute("data-comparison-cell", "1:1");
  await nla.click({ position: { x: 162, y: 100 }, modifiers: ["Control"] });
  expect(page.url()).toBe(nlaPrimaryUrl);
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string; tokenIndex?: number; layer?: number; component?: string }) =>
      pin.view === "nla" && pin.tokenIndex === 2 && pin.layer === 2 && pin.component === "resid_post"
    );
  })).toBe(true);
  await expect(nla).toHaveAttribute("aria-keyshortcuts", /Space/);
  await nla.press("Space");
  await expect.poll(() => page.evaluate(() => {
    const pins = JSON.parse(window.localStorage.getItem("safelens.localExplorer.pinnedEvidence.v2") ?? "[]");
    return pins.some((pin: { view?: string }) => pin.view === "nla");
  })).toBe(true);
  await nla.click({ position: { x: 135, y: 70 } });
  await expect(page).toHaveURL(/layer=1/);
  await expect(page).toHaveURL(/token=1/);
  await nla.press("ArrowDown");
  await expect(page).toHaveURL(/layer=2/);
  await expect(page.locator(".nla-fidelity-tooltip")).toContainText("no matrix cell focused");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    await page.evaluate(() => window.innerWidth)
  );
  await testInfo.attach("specialized-matrices-desktop", {
    body: await page.screenshot(),
    contentType: "image/png"
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?run=perf-specialized&sample=canvas-specialized&view=attention&layer=0&token=1&source=1&target=1");
  const mobileAttention = page.getByRole("grid", { name: /Attention pattern Canvas matrix/ });
  await assertViewportCanvas(mobileAttention, page, ".attention-pattern-cell", 2_000);
  const mobileOverview = page.getByRole("button", { name: /Navigate Attention pattern Canvas matrix/ });
  await expect(mobileOverview).toBeVisible();
  expect((await mobileOverview.boundingBox())?.width).toBeLessThanOrEqual(210);
  const mobileAttentionViewport = page.locator(".attention-matrix-scroll");
  const mobileAttentionControls = page.getByLabel("Attention matrix controls", { exact: true });
  await mobileAttentionControls.getByLabel("Pan attention matrix").click();
  const mobileAttentionUrl = page.url();
  await mobileAttentionViewport.scrollIntoViewIfNeeded();
  const mobileAttentionBox = await mobileAttentionViewport.boundingBox();
  expect(mobileAttentionBox).not.toBeNull();
  await page.mouse.move(
    mobileAttentionBox!.x + mobileAttentionBox!.width * 0.76,
    mobileAttentionBox!.y + mobileAttentionBox!.height * 0.76
  );
  await page.mouse.down();
  await page.mouse.move(
    mobileAttentionBox!.x + mobileAttentionBox!.width * 0.26,
    mobileAttentionBox!.y + mobileAttentionBox!.height * 0.26,
    { steps: 8 }
  );
  await page.mouse.up();
  await expect.poll(() => mobileAttentionViewport.evaluate((element) => element.scrollLeft))
    .toBeGreaterThan(0);
  await expect.poll(() => mobileAttentionViewport.evaluate((element) => element.scrollTop))
    .toBeGreaterThan(0);
  expect(page.url()).toBe(mobileAttentionUrl);
  await expect(mobileAttention).toHaveAttribute("data-column-header-sticky", "true");
  await mobileAttentionControls.getByLabel("Select attention matrix cells").click();
  await mobileAttention.click({ position: { x: 140, y: 10 } });
  expect(page.url()).toBe(mobileAttentionUrl);
  await expect.poll(() => mobileAttentionViewport.evaluate((element) => element.scrollTop))
    .toBeGreaterThan(0);
  await mobileAttentionControls.getByLabel("Reset attention matrix view").click();
  await expect.poll(() => mobileAttentionViewport.evaluate((element) => element.scrollLeft)).toBe(0);
  await expect.poll(() => mobileAttentionViewport.evaluate((element) => element.scrollTop)).toBe(0);
  await expect(mobileAttentionControls.getByLabel("Select attention matrix cells"))
    .toHaveAttribute("aria-pressed", "true");
  expect(page.url()).toBe(mobileAttentionUrl);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await testInfo.attach("specialized-matrices-mobile", {
    body: await page.screenshot(),
    contentType: "image/png"
  });

  await page.goto("/?run=perf-specialized&sample=canvas-specialized&view=mlp&layer=0&token=1&neuron=L0N1999&metric=mlp_signed_activation");
  const mobileMlp = page.getByRole("grid", { name: /MLP activation Canvas matrix/ });
  await assertViewportCanvas(mobileMlp, page, ".mlp-activation-cell", 2_000);
  await expect(mobileMlp).toHaveAttribute("aria-colcount", "2000");
  await expect(page.getByLabel("Neuron search results")).toHaveText("2000/2000");
  await expect(page.getByLabel("Selected MLP activation", { exact: true })).toContainText("L0N1999");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await testInfo.attach("mlp-2000-neurons-mobile", {
    body: await page.screenshot(),
    contentType: "image/png"
  });

  await page.goto("/?run=perf-specialized&sample=canvas-specialized&view=attention&layer=0&token=1&source=1&target=1");
  const forcedColorAttention = page.getByRole("grid", { name: /Attention pattern Canvas matrix/ });
  await expect(forcedColorAttention).toBeVisible();

  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  expect(await forcedColorAttention.evaluate(
    (element) => getComputedStyle(element).forcedColorAdjust
  )).toBe("none");
  await testInfo.attach("specialized-matrices-forced-colors", {
    body: await page.screenshot(),
    contentType: "image/png"
  });
});

async function assertViewportCanvas(
  canvas: import("@playwright/test").Locator,
  page: import("@playwright/test").Page,
  domCellSelector: string,
  maximumVisibleCells = 3_000
) {
  await expect(canvas).toBeVisible({ timeout: 30_000 });
  await expect(page.locator(domCellSelector)).toHaveCount(0);
  await expect.poll(async () => Number(await canvas.getAttribute("data-visible-cells"))).toBeGreaterThan(0);
  expect(Number(await canvas.getAttribute("data-visible-cells"))).toBeLessThan(maximumVisibleCells);
  expect(Number(await canvas.getAttribute("data-draw-ms"))).toBeLessThan(100);
  const hasPaintedPixels = await canvas.evaluate((element) => {
    const context = (element as HTMLCanvasElement).getContext("2d");
    if (!context) return false;
    const pixels = context.getImageData(0, 0, element.width, element.height).data;
    for (let index = 0; index < pixels.length; index += 64) {
      if (pixels[index] < 245 || pixels[index + 1] < 245 || pixels[index + 2] < 245) return true;
    }
    return false;
  });
  expect(hasPaintedPixels).toBe(true);
}

async function dragCanvasRange(
  page: import("@playwright/test").Page,
  canvas: Locator,
  start: { x: number; y: number },
  end: { x: number; y: number }
) {
  await canvas.scrollIntoViewIfNeeded();
  const box = await canvas.boundingBox();
  expect(box).not.toBeNull();
  await page.mouse.move(box!.x + start.x, box!.y + start.y);
  await page.mouse.down();
  await page.mouse.move(box!.x + end.x, box!.y + end.y, { steps: 8 });
  await page.mouse.up();
}

async function sampleCanvasPixel(
  canvas: Locator,
  x: number,
  y: number
) {
  return canvas.evaluate((element, point) => {
    const target = element as HTMLCanvasElement;
    const context = target.getContext("2d");
    if (!context) throw new Error("Canvas context unavailable");
    const scaleX = target.width / Math.max(1, target.clientWidth);
    const scaleY = target.height / Math.max(1, target.clientHeight);
    const pixel = context.getImageData(
      Math.max(0, Math.min(target.width - 1, Math.round(point.x * scaleX))),
      Math.max(0, Math.min(target.height - 1, Math.round(point.y * scaleY))),
      1,
      1
    ).data;
    return { red: pixel[0], green: pixel[1], blue: pixel[2], alpha: pixel[3] };
  }, { x, y });
}

function performanceRun(rowCount: number, columnCount: number) {
  const tokens = Array.from({ length: columnCount }, (_, index) => ({
    ...realRun.tokens[index % realRun.tokens.length],
    index,
    text: ` t${index}`,
    tokenId: 30_000 + index,
    source: "prompt" as const,
    risk: (index % 100) / 100,
    attribution: (index % 37) / 37
  }));
  const layers = Array.from({ length: rowCount }, (_, index) => index);
  return {
    ...realRun,
    runId: "perf-200k",
    sampleId: "canvas-200k",
    tokens,
    layers,
    residualCells: layers.flatMap((layer) => tokens.map((token) => ({
      layer,
      tokenIndex: token.index,
      norm: 1,
      rawDirection: ((layer + token.index) % 100) / 100,
      riskDirection: ((layer + token.index) % 100) / 100,
      semanticDensity: 0.5
    }))),
    attentionHeads: [{
      ...realRun.attentionHeads[0],
      id: "L0H0",
      layer: 0,
      distributionByToken: Array.from({ length: columnCount }, (_, destination) =>
        Array.from({ length: columnCount }, (_, source) =>
          source <= destination ? 1 / (destination + 1) : 0
        )
      )
    }],
    mlpNeurons: [{
      ...realRun.mlpNeurons[0],
      id: "L0N0",
      layer: 0,
      activationsByToken: tokens.map((_, index) => (index % 21 - 10) / 10),
      topTokens: [0],
      positiveTopTokens: [0],
      negativeTopTokens: [1],
      maxAbsoluteActivation: 1
    }],
    attentionCells: [{ layer: 0, tokenIndex: 0, value: 0, rawValue: 0, metric: "attention", sourceKey: "perf" }],
    mlpCells: [{ layer: 0, tokenIndex: 0, value: 0, rawValue: 0, metric: "mlp", sourceKey: "perf" }],
    attributionTracks: realRun.attributionTracks.map((track) => ({
      ...track,
      values: tokens.map((token) => token.attribution)
    })),
    attributionMethods: realRun.attributionMethods.map((method) => ({
      ...method,
      rows: method.rows.map((row) => ({
        ...row,
        layer: row.layer < 0 ? row.layer : 0,
        values: tokens.map((token) => token.attribution)
      }))
    })),
    logitLens: [{ ...realRun.logitLens[0], layer: 0, tokenIndex: 0 }],
    nla: realRun.nla.slice(0, 1).map((row) => ({ ...row, layer: 0, tokenIndex: 0 })),
    nlaCompatibility: { ...realRun.nlaCompatibility, availableLayers: layers }
  };
}

function specializedPerformanceRun() {
  const baseRun = performanceRun(30, 100);
  const run = {
    ...baseRun,
    tokens: baseRun.tokens.map((token, index) => index === 0
      ? {
          ...token,
          text: " extraordinarily-long-specialized-token-fragment",
          tokenId: 87_654
        }
      : token)
  };
  const neurons = Array.from({ length: 2_000 }, (_, neuron) => ({
    ...realRun.mlpNeurons[0],
    id: `L0N${String(neuron).padStart(4, "0")}`,
    layer: 0,
    neuron,
    activationsByToken: run.tokens.map((_, token) => ((token + neuron) % 21 - 10) / 10),
    topTokens: [0],
    positiveTopTokens: [10],
    negativeTopTokens: [0],
    maxAbsoluteActivation: 1
  }));
  return {
    ...run,
    runId: "perf-specialized",
    sampleId: "canvas-specialized",
    mlpNeurons: neurons,
    attributionMethods: realRun.attributionMethods.map((method) => ({
      ...method,
      rows: method.available
        ? Array.from({ length: 30 }, (_, layer) => ({
            ...method.rows[layer % method.rows.length],
            layer,
            label: `L${layer}`,
            sourceKey: `layer_${layer}.resid_post`,
            values: run.tokens.map((_, token) => ((layer + token) % 31 - 15) / 15)
          }))
        : []
    })),
    nla: [
      { layer: 0, tokenIndex: 0, cosine: 0.94, mse: 0.04, fve: 0.91 },
      { layer: 1, tokenIndex: 1, cosine: 0.88, mse: 0.08, fve: 0.84 },
      { layer: 2, tokenIndex: 2, cosine: 0.81, mse: 0.12, fve: 0.76 }
    ].map((value) => ({
      ...realRun.nla[0],
      ...value,
      component: "resid_post" as const,
      status: "available" as const,
      token: run.tokens[value.tokenIndex]?.text ?? `T${value.tokenIndex}`,
      source: `layer_${value.layer}.resid_post[${value.tokenIndex}]`
    }))
  };
}
