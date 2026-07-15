import { expect, test, type CDPSession, type Page } from "@playwright/test";

import { realRun } from "../src/realRunData";

const VIEW_LABELS = [
  "Overview",
  "Residual",
  "Attention",
  "MLP",
  "NLA",
  "Patching",
  "Intervention",
  "Attribution"
] as const;

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ page, context }) => {
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "performance-budget",
        runs: [],
        diagnostics: []
      }
    });
  });
  const client = await context.newCDPSession(page);
  await client.send("Network.enable");
  await client.send("Network.setCacheDisabled", { cacheDisabled: true });
  await client.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 20,
    downloadThroughput: 1_250_000,
    uploadThroughput: 625_000,
    connectionType: "wifi"
  });
  await client.send("Emulation.setCPUThrottlingRate", { rate: 2 });
});

test("keeps the regular production workspace usable within two seconds", async ({ page }, testInfo) => {
  await page.goto("/explorer?view=overview&token=10&layer=1");
  await expect(page.getByRole("heading", { name: "Token Timeline" })).toBeVisible();
  await expect.poll(() => firstUsable(page)).toBeLessThan(2_000);

  const measurement = await page.evaluate(() => {
    const mark = performance.getEntriesByName("safelens:first-usable")[0] as PerformanceMark;
    return {
      firstUsableMs: mark.startTime,
      view: (mark.detail as { view?: string } | undefined)?.view,
      loadingModules: document.querySelectorAll(".view-module-loading").length
    };
  });
  expect(measurement.view).toBe("overview");
  expect(measurement.loadingModules).toBe(0);
  await testInfo.attach("first-usable-budget", {
    body: Buffer.from(JSON.stringify(measurement, null, 2)),
    contentType: "application/json"
  });
});

test("keeps a 2400-token chunked timeline windowed and responsive", async ({ page }, testInfo) => {
  test.setTimeout(60_000);
  const tokenCount = 2_400;
  const run = timelinePerformanceCore(tokenCount);
  const chunkRequests: string[] = [];
  let fullSampleRequests = 0;
  await page.unrouteAll({ behavior: "wait" });
  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "timeline-performance",
        runs: [{
          runId: run.runId,
          sampleId: run.sampleId,
          modelName: run.modelName,
          modelSource: run.modelSource,
          tokenCount,
          layerCount: 1,
          artifactId: "timeline-2400-artifact",
          sourceName: "timeline-2400.explorer.json",
          modifiedAt: "2026-07-14T00:00:00Z",
          sizeBytes: 12_000_000,
          chunkProtocol: "safelens-chunks-v1"
        }],
        diagnostics: []
      }
    });
  });
  await page.route("**/api/runs/timeline-2400/samples/chunked-2400/metadata", async (route) => {
    await route.fulfill({
      headers: { ETag: '"timeline-metadata-v1"' },
      json: timelineChunkMetadata(run)
    });
  });
  await page.route(/\/api\/runs\/timeline-2400\/samples\/chunked-2400\/chunks\/(?:residualCells|logitLens).*/, async (route) => {
    const url = new URL(route.request().url());
    const component = url.pathname.split("/").at(-1)!;
    const start = Number(url.searchParams.get("tokenStart"));
    const end = Number(url.searchParams.get("tokenEnd"));
    chunkRequests.push(`${component}:${start}-${end}`);
    await route.fulfill({
      headers: { ETag: `"${component}-${start}"` },
      json: timelineChunkResponse(run, component, start, end)
    });
  });
  await page.route("**/api/runs/timeline-2400/samples/chunked-2400", async (route) => {
    fullSampleRequests += 1;
    await route.abort();
  });

  await page.goto("/explorer?run=timeline-2400&sample=chunked-2400&view=overview&token=10&layer=0");
  const timeline = page.getByLabel("Token timeline");
  await expect(timeline.getByLabel("Timeline render window")).toContainText("2400");
  await expect(timeline.locator(".token-pill")).toHaveCount(180);
  await expect.poll(() => timelineEvent(page, "timeline-ready")).toMatchObject({
    tokens: tokenCount,
    renderedItems: 180
  });
  const ready = await timelineEvent(page, "timeline-ready");
  expect(ready.at).toBeLessThan(2_000);

  await timeline.getByLabel("Token color metric").selectOption("residual");
  await expect(timeline.locator(".token-pill.metric-residual")).toHaveCount(180);
  await timeline.getByLabel("Token color metric").selectOption("nla");
  await expect(timeline.locator(".token-pill.metric-nla")).toHaveCount(180);

  const searchStarted = Date.now();
  await timeline.getByLabel("Search tokens").fill("token-2350");
  await expect(timeline.getByLabel("Token search results")).toContainText("1 matches");
  await timeline.getByLabel("Next token search result").click();
  const target = timeline.locator('[data-timeline-start="2350"]');
  await expect(target).toBeFocused();
  await expect(page).toHaveURL(/token=2350/);
  await expect(timeline.locator(".token-pill")).toHaveCount(180);
  expect(Date.now() - searchStarted).toBeLessThan(1_000);
  const searchEvent = await timelineEvent(page, "timeline-search-jump");
  expect(searchEvent.durationMs).toBeLessThan(100);
  expect(searchEvent.token).toBe(2350);

  await target.hover();
  await expect.poll(() => timelineEvent(page, "timeline-hover")).toMatchObject({ token: 2350 });
  const hoverEvent = await timelineEvent(page, "timeline-hover");
  expect(hoverEvent.durationMs).toBeLessThan(100);
  await target.press("Space");
  await expect(target).toHaveClass(/pinned/);
  await expect(timeline.getByLabel("Token evidence markers")).toContainText("Pinned");

  await expect.poll(() => chunkRequests.filter((item) => item.endsWith("2048-2400")).sort()).toEqual([
    "logitLens:2048-2400",
    "residualCells:2048-2400"
  ]);
  expect(fullSampleRequests).toBe(0);
  expect(await page.evaluate(() => document.querySelectorAll(".token-pill").length)).toBe(180);
  expect(await page.evaluate(() => window.__SAFELENS_PERFORMANCE__?.length ?? 0)).toBeLessThanOrEqual(100);

  await testInfo.attach("timeline-2400-performance", {
    body: Buffer.from(JSON.stringify({
      ready,
      searchEvent,
      hoverEvent,
      chunkRequests,
      renderedItems: 180,
      fullSampleRequests
    }, null, 2)),
    contentType: "application/json"
  });
});

test("does not retain heap, DOM, listeners, canvases, or marks across view cycles", async ({ page, context }, testInfo) => {
  const client = await context.newCDPSession(page);
  await client.send("Performance.enable");
  await client.send("HeapProfiler.enable");
  await page.goto("/explorer?view=overview&token=10&layer=1");
  await expect.poll(() => firstUsable(page)).toBeLessThan(2_000);

  await cycleViews(page, 2);
  const baseline = await runtimeSnapshot(page, client);
  await cycleViews(page, 5);
  const final = await runtimeSnapshot(page, client);

  expect(final.heapBytes - baseline.heapBytes).toBeLessThan(4 * 1024 * 1024);
  expect(final.nodes - baseline.nodes).toBeLessThan(120);
  expect(final.listeners - baseline.listeners).toBeLessThan(24);
  expect(final.documents).toBeLessThanOrEqual(baseline.documents + 1);
  expect(final.canvases).toBeLessThanOrEqual(1);
  expect(final.performanceEvents).toBeLessThanOrEqual(100);
  expect(final.performanceMarks).toBeLessThanOrEqual(6);
  await testInfo.attach("view-cycle-runtime", {
    body: Buffer.from(JSON.stringify({ baseline, final }, null, 2)),
    contentType: "application/json"
  });
});

async function firstUsable(page: Page) {
  return page.evaluate(() => {
    const mark = performance.getEntriesByName("safelens:first-usable")[0];
    return mark?.startTime ?? Number.POSITIVE_INFINITY;
  });
}

async function timelineEvent(page: Page, name: string) {
  return page.evaluate((eventName) => {
    const event = window.__SAFELENS_PERFORMANCE__
      ?.filter((candidate) => candidate.name === eventName)
      .at(-1);
    return event ?? { name: eventName, at: Number.POSITIVE_INFINITY };
  }, name);
}

function timelinePerformanceCore(tokenCount: number) {
  const tokens = Array.from({ length: tokenCount }, (_, index) => ({
    ...realRun.tokens[index % realRun.tokens.length],
    index,
    text: ` token-${index}`,
    tokenId: 40_000 + index,
    source: "prompt" as const,
    risk: index === 2350 ? 0.98 : (index % 100) / 100,
    attribution: (index % 37) / 37,
    probeScore: index === 2350 ? 0.91 : undefined,
    monitorHit: index === 2350 || undefined
  }));
  return {
    runId: "timeline-2400",
    modelName: realRun.modelName,
    modelSource: realRun.modelSource,
    sampleId: "chunked-2400",
    prompt: "Chunked 2400 token timeline performance fixture",
    tokens,
    layers: [0],
    nlaCompatibility: {
      ...realRun.nlaCompatibility,
      availableLayers: [0],
      profiles: realRun.nlaCompatibility.profiles.map((profile) => ({
        ...profile,
        layer: 0,
        layerAvailable: true
      }))
    },
    metricProvenance: realRun.metricProvenance,
    metadata: { fixture: "timeline-performance" }
  };
}

function timelineChunkMetadata(run: ReturnType<typeof timelinePerformanceCore>) {
  return {
    schemaVersion: "1.0",
    protocol: "safelens-chunks-v1",
    runId: run.runId,
    sampleId: run.sampleId,
    artifactId: "timeline-2400-artifact",
    version: "timeline-metadata-v1",
    base: run,
    chunks: ["residualCells", "logitLens"].map((component) => ({
      component,
      itemCount: run.tokens.length,
      rangeAxis: "token",
      layerFilter: true,
      selectorFilter: false
    }))
  };
}

function timelineChunkResponse(
  run: ReturnType<typeof timelinePerformanceCore>,
  component: string,
  start: number,
  end: number
) {
  const data = run.tokens.slice(start, end).map((token) => component === "residualCells"
    ? {
        layer: 0,
        tokenIndex: token.index,
        norm: 0.5 + token.index / run.tokens.length,
        rawDirection: token.risk,
        riskDirection: token.risk,
        semanticDensity: token.attribution
      }
    : {
        layer: 0,
        tokenIndex: token.index,
        targetTokenId: 123,
        targetTokenText: " target",
        targetLogit: token.risk,
        targetProbability: 0.5,
        targetRank: 1,
        sourceKey: `layer_0.resid_post[${token.index}]`,
        topPredictions: [{
          tokenId: 123,
          tokenText: " target",
          logit: token.risk,
          probability: 0.5
        }]
      });
  return {
    schemaVersion: "1.0",
    protocol: "safelens-chunks-v1",
    runId: run.runId,
    sampleId: run.sampleId,
    artifactId: "timeline-2400-artifact",
    version: `${component}-${start}`,
    component,
    tokenRange: [start, end],
    sourceRange: null,
    layer: null,
    selector: null,
    data
  };
}

async function cycleViews(page: Page, cycles: number) {
  for (let cycle = 0; cycle < cycles; cycle += 1) {
    for (const label of VIEW_LABELS) {
      const tab = page.getByRole("tab", { name: label, exact: true });
      await tab.click();
      await expect(tab).toHaveAttribute("aria-selected", "true");
      await expect.poll(async () => page.evaluate(() => {
        const latest = window.__SAFELENS_PERFORMANCE__
          ?.filter((event) => event.name === "view-ready")
          .at(-1);
        return latest?.view;
      })).toBe(label.toLowerCase());
    }
  }
}

async function runtimeSnapshot(page: Page, client: CDPSession) {
  await client.send("HeapProfiler.collectGarbage");
  await page.waitForTimeout(50);
  const { metrics } = await client.send("Performance.getMetrics");
  const values = new Map(metrics.map((metric) => [metric.name, metric.value]));
  const dom = await page.evaluate(() => ({
    canvases: document.querySelectorAll("canvas").length,
    performanceEvents: window.__SAFELENS_PERFORMANCE__?.length ?? 0,
    performanceMarks: performance.getEntriesByType("mark").filter(
      (entry) => entry.name.startsWith("safelens:")
    ).length
  }));
  return {
    heapBytes: values.get("JSHeapUsedSize") ?? Number.POSITIVE_INFINITY,
    nodes: values.get("Nodes") ?? Number.POSITIVE_INFINITY,
    listeners: values.get("JSEventListeners") ?? Number.POSITIVE_INFINITY,
    documents: values.get("Documents") ?? Number.POSITIVE_INFINITY,
    ...dom
  };
}
