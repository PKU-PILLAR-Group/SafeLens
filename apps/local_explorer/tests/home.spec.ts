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
      normalized: false,
      dimension: 768,
      sourceKey: "test:steering",
      referenceTemplate: "tokenizer.apply_chat_template",
      sourceActivationNorm: 24.8,
      appliedVectorNorm: 12.4,
      relativeStrength: 0.5
    },
    layer: generatedRun.layers[0],
    component: "resid_post" as const,
    scale: 1,
    positionStart: 0,
    positionEnd: generatedRun.tokens.length,
    targetTokenId: generatedRun.logitLens[0]?.targetTokenId ?? 0,
    targetTokenText: generatedRun.logitLens[0]?.targetTokenText ?? "target",
    seed: 0,
    maxNewTokens: 64,
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
      firstDivergenceIndex: 0,
      probeScore: null,
      probeReason: "No probe configured."
    },
    diff: [{ kind: "replace" as const, originalStart: 0, originalEnd: 2, steeredStart: 0, steeredEnd: 2 }],
    sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId }
  }
};

const gemmaRun: ExplorerRun = {
  ...generatedRun,
  runId: "chat-gemma-source",
  modelName: "google/gemma-3-270m-it",
  modelSource: "modelscope",
  layers: [0, 1, 5, 9, 12, 15],
  metadata: {
    ...generatedRun.metadata,
    promptRunner: {
      jobVersion: "1.0",
      template: "chat",
      model: "google/gemma-3-270m-it",
      seed: 0,
      maxNewTokens: 64,
      temperature: 0
    }
  }
};

const saeDerivedRun: ExplorerRun = {
  ...gemmaRun,
  runId: "chat-gemma-sae-derived",
  intervention: {
    ...steeringRun.intervention,
    mode: "sae_feature",
    feature: {
      kind: "sae_feature",
      id: "F8439",
      label: "SAE feature F8439",
      layer: 12,
      featureIndex: 8439,
      baselineActivation: 402.25,
      meanActivation: 48.3,
      activeTokenCount: 2,
      operation: "add",
      release: "gemma-scope-2-270m-it-res",
      saeId: "layer_12_width_16k_l0_small",
      width: 16_384,
      architecture: "jump_relu",
      source: "google/gemma-scope-2-270m-it",
      conceptLabel: "descriptive sentence structure",
      conceptSource: "neuronpedia",
      conceptUrl: "https://www.neuronpedia.org/gemma-3-270m-it/12-gemmascope-res-16k/8439",
      positiveTokens: [" sentence", " description"],
      negativeTokens: []
    },
    layer: 12,
    scale: 850,
    positionStart: gemmaRun.tokens.length - 1,
    positionEnd: gemmaRun.tokens.length,
    maxNewTokens: 96,
    original: { ...steeringRun.intervention.original, text: "Original Gemma response." },
    steered: { ...steeringRun.intervention.steered, text: "Feature-amplified Gemma response." },
    deltas: {
      ...steeringRun.intervention.deltas,
      targetLogit: 7.25,
      tokenEditDistance: 8,
      generationChanged: true,
      maxAbsLogit: 48.75,
      meanAbsLogit: 0.91,
      changedVocabularyLogits: 12_000,
      featureActivationDelta: 850,
      effectStatus: "changed"
    },
    sourceRun: { runId: gemmaRun.runId, sampleId: gemmaRun.sampleId }
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
    status: "available",
    generation: {
      complete: true,
      finishReason: "end_tag",
      generatedTokenCount: 74,
      requestedMaxNewTokens: 256
    }
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
    const referencesDiffer = Array.isArray(request.positivePrompts) && Array.isArray(request.negativePrompts)
      ? JSON.stringify(request.positivePrompts) !== JSON.stringify(request.negativePrompts)
      : request.desiredPrompt !== request.undesiredPrompt;
    await route.fulfill({
      json: {
        modelAllowed: true,
        layerAvailable: true,
        componentSupported: true,
        positionRangeValid: true,
        targetTokenValid: true,
        referencesDiffer,
        targetTokenId: request.targetTokenId,
        targetTokenText: "target",
        positionStart: request.positionStart,
        positionEnd: request.positionEnd,
        canSubmit: referencesDiffer,
        reason: "Steering inputs are ready."
      }
    });
  });
  await page.route("**/api/patching/preflight", async (route) => {
    const request = route.request().postDataJSON() as {
      cleanPrompt: string;
      corruptedPrompt: string;
      cleanTokenIds: number[];
      targetTokenId: number;
    };
    const differs = request.cleanPrompt !== request.corruptedPrompt;
    const changedPositions = differs ? [Math.min(2, request.cleanTokenIds.length - 1)] : [];
    await route.fulfill({
      json: {
        modelAllowed: true,
        promptsDiffer: differs,
        tokenCountMatches: true,
        targetTokenValid: true,
        componentSupported: true,
        cleanTokenCount: request.cleanTokenIds.length,
        corruptedTokenCount: request.cleanTokenIds.length,
        changedPositions,
        targetTokenId: request.targetTokenId,
        targetTokenText: " target",
        corruptedTokens: generatedRun.tokens.map((token, index) => ({
          index,
          tokenId: token.tokenId + (changedPositions.includes(index) ? 1 : 0),
          text: changedPositions.includes(index) ? " changed" : token.text,
          changed: changedPositions.includes(index)
        })),
        canSubmit: differs,
        reason: differs
          ? "Prompts are positionally aligned and ready for causal activation patching."
          : "Clean and corrupted prompts must differ."
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
    const answer = index === 1
      ? "First answer from the model. User: This leaked turn must be ignored. Assistant: ignored"
      : "Second answer uses the prior turn.";
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
      maxNewTokens: 64,
      temperature: 0,
      neuron: null,
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

async function mockReadySAEFeatureFlow(page: Page) {
  const profile = {
    id: "gemma-scope-2-270m-it-resid-post-l12-16k-small",
    label: "Gemma Scope 2 · L12 · residual · 16k · L0 small",
    modelName: gemmaRun.modelName,
    release: "gemma-scope-2-270m-it-res",
    saeId: "layer_12_width_16k_l0_small",
    layer: 12,
    component: "resid_post",
    width: 16_384,
    architecture: "jump_relu",
    source: "google/gemma-scope-2-270m-it"
  };
  const candidate = {
    featureIndex: 8439,
    label: "descriptive sentence structure",
    source: "neuronpedia",
    url: "https://www.neuronpedia.org/gemma-3-270m-it/12-gemmascope-res-16k/8439",
    positiveTokens: [" sentence", " description"],
    negativeTokens: [],
    maxActivation: 402.25,
    meanActivation: 48.3,
    activeTokenCount: 2,
    peakTokenIndex: 2,
    peakTokenText: " model",
    recommendedDelta: 850
  };
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/intervention/sae-profiles?*", async (route) => {
    await route.fulfill({ json: [profile] });
  });
  await page.route("**/api/intervention/sae-feature-info?*", async (route) => {
    const featureIndex = Number(new URL(route.request().url()).searchParams.get("featureIndex"));
    await route.fulfill({
      json: {
        modelName: gemmaRun.modelName,
        layer: 12,
        featureIndex,
        label: featureIndex === candidate.featureIndex ? candidate.label : `Feature ${featureIndex}`,
        source: featureIndex === candidate.featureIndex ? "neuronpedia" : "index",
        url: featureIndex === candidate.featureIndex ? candidate.url : null,
        positiveTokens: featureIndex === candidate.featureIndex ? candidate.positiveTokens : [],
        negativeTokens: []
      }
    });
  });
  await page.route("**/api/jobs/sae-discovery", async (route) => {
    const input = route.request().postDataJSON() as Record<string, unknown>;
    const request = {
      ...input,
      run: undefined,
      sourceRun: { runId: gemmaRun.runId, sampleId: gemmaRun.sampleId, modelName: gemmaRun.modelName }
    };
    delete request.run;
    await route.fulfill({ status: 202, json: derivedJob("sae-discovery-home-job", "sae-discovery", request, null, "idle") });
  });
  await page.route("**/api/jobs/sae-discovery-home-job/events", async (route) => {
    const request = {
      layer: 12,
      component: "resid_post",
      saeRelease: profile.release,
      saeId: profile.saeId,
      positionStart: 0,
      positionEnd: gemmaRun.tokens.length,
      limit: 12,
      sourceRun: { runId: gemmaRun.runId, sampleId: gemmaRun.sampleId, modelName: gemmaRun.modelName }
    };
    const result = {
      runId: gemmaRun.runId,
      sampleId: gemmaRun.sampleId,
      modelName: gemmaRun.modelName,
      layer: 12,
      component: "resid_post",
      release: profile.release,
      saeId: profile.saeId,
      positionStart: 0,
      positionEnd: gemmaRun.tokens.length,
      candidates: [candidate]
    };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(derivedJob("sae-discovery-home-job", "sae-discovery", request, result, "ready"))}\n\n`
    });
  });
  await page.route("**/api/jobs/intervention", async (route) => {
    submitted = route.request().postDataJSON();
    const request = {
      ...submitted,
      sourceRun: { runId: gemmaRun.runId, sampleId: gemmaRun.sampleId, modelName: gemmaRun.modelName },
      preflight: {
        mode: "sae_feature",
        modelAllowed: true,
        layerAvailable: true,
        componentSupported: true,
        positionRangeValid: true,
        targetTokenValid: true,
        referencesDiffer: true,
        featureAvailable: true,
        saeProfileValid: true,
        saeRuntimeAvailable: true,
        targetTokenId: submitted?.targetTokenId,
        targetTokenText: "target",
        positionStart: submitted?.positionStart,
        positionEnd: submitted?.positionEnd,
        canSubmit: true,
        reason: "SAE feature intervention is ready."
      }
    };
    await route.fulfill({ status: 202, json: derivedJob("sae-intervention-home-job", "intervention", request, null, "idle") });
  });
  await page.route("**/api/jobs/sae-intervention-home-job/events", async (route) => {
    const request = {
      mode: "sae_feature",
      desiredPrompt: "Enhance selected SAE feature",
      undesiredPrompt: "Suppress selected SAE feature",
      activationReduce: "last_token",
      layer: 12,
      component: "resid_post",
      scale: 850,
      positionStart: gemmaRun.tokens.length - 1,
      positionEnd: gemmaRun.tokens.length,
      targetTokenId: gemmaRun.logitLens[0]?.targetTokenId ?? 0,
      seed: 0,
      maxNewTokens: 96,
      temperature: 0,
      saeRelease: profile.release,
      saeId: profile.saeId,
      featureIndex: candidate.featureIndex,
      saeOperation: "add",
      sourceRun: { runId: gemmaRun.runId, sampleId: gemmaRun.sampleId, modelName: gemmaRun.modelName },
      preflight: {
        mode: "sae_feature",
        modelAllowed: true,
        layerAvailable: true,
        componentSupported: true,
        positionRangeValid: true,
        targetTokenValid: true,
        referencesDiffer: true,
        featureAvailable: true,
        saeProfileValid: true,
        saeRuntimeAvailable: true,
        targetTokenId: gemmaRun.logitLens[0]?.targetTokenId ?? 0,
        targetTokenText: "target",
        positionStart: gemmaRun.tokens.length - 1,
        positionEnd: gemmaRun.tokens.length,
        canSubmit: true,
        reason: "SAE feature intervention is ready."
      }
    };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(derivedJob("sae-intervention-home-job", "intervention", request, saeDerivedRun, "ready"))}\n\n`
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
      maxNewTokens: 256,
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

async function mockReadyPatchingJob(page: Page) {
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/api/jobs/patching", async (route) => {
    submitted = route.request().postDataJSON();
    const request = patchingRequest(submitted);
    await route.fulfill({
      status: 202,
      json: derivedJob("patching-home-job", "patching", request, null, "idle")
    });
  });
  await page.route("**/api/jobs/patching-home-job/events", async (route) => {
    const request = patchingRequest(submitted ?? {});
    const layers = request.layers as number[];
    const positions = request.positions as number[];
    const corruptedTokens = generatedRun.tokens.map((token, index) => ({
      index,
      tokenId: token.tokenId + (positions.includes(index) ? 1 : 0),
      text: positions.includes(index) ? " changed" : token.text,
      changed: positions.includes(index)
    }));
    const patchingRun: ExplorerRun = {
      ...generatedRun,
      runId: "chat-patching-derived",
      metadata: {
        ...generatedRun.metadata,
        parentRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId }
      },
      patching: {
        cleanPrompt: generatedRun.prompt,
        corruptedPrompt: String(request.corruptedPrompt),
        component: request.component as "resid_post" | "attn_out" | "z" | "mlp_out",
        ...(request.head === undefined ? {} : { head: Number(request.head) }),
        targetTokenId: Number(request.targetTokenId),
        targetTokenText: " target",
        cleanScore: 2.4,
        corruptedScore: 0.4,
        denominator: 2,
        layers,
        positions,
        corruptedTokens,
        cells: layers.flatMap((layer, layerIndex) => positions.map((position, positionIndex) => ({
          layer,
          tokenIndex: position,
          patchedScore: 1.8 - layerIndex * 0.1 - positionIndex * 0.05,
          causalEffect: 1.4 - layerIndex * 0.1 - positionIndex * 0.05,
          recoveryPercentage: 70 - layerIndex * 5 - positionIndex * 2.5,
          sourceKey: `layer_${layer}.${request.component}`
        }))),
        sourceRun: { runId: generatedRun.runId, sampleId: generatedRun.sampleId },
        sourceKey: `activation_patching.${request.component}`
      }
    };
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: `event: job\ndata: ${JSON.stringify(derivedJob("patching-home-job", "patching", request, patchingRun, "ready"))}\n\n`
    });
  });
  return () => submitted;
}

function patchingRequest(submitted: Record<string, unknown>) {
  return {
    corruptedPrompt: submitted.corruptedPrompt,
    component: submitted.component,
    layers: submitted.layers ?? [],
    positions: submitted.positions ?? [],
    ...(submitted.head === undefined ? {} : { head: submitted.head }),
    targetTokenId: submitted.targetTokenId,
    sourceRun: {
      runId: generatedRun.runId,
      sampleId: generatedRun.sampleId,
      modelName: generatedRun.modelName
    },
    preflight: {
      modelAllowed: true,
      promptsDiffer: true,
      tokenCountMatches: true,
      targetTokenValid: true,
      componentSupported: true,
      cleanTokenCount: generatedRun.tokens.length,
      corruptedTokenCount: generatedRun.tokens.length,
      changedPositions: [2],
      targetTokenId: submitted.targetTokenId,
      targetTokenText: " target",
      corruptedTokens: generatedRun.tokens.map((token, index) => ({
        index,
        tokenId: token.tokenId + (index === 2 ? 1 : 0),
        text: index === 2 ? " changed" : token.text,
        changed: index === 2
      })),
      canSubmit: true,
      reason: "Prompts are positionally aligned and ready for causal activation patching."
    }
  };
}

function derivedJob(
  id: string,
  kind: "attribution" | "intervention" | "patching" | "nla" | "jlens" | "sae-discovery",
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
  await expect(page.getByLabel("Analysis model")).toHaveValue("Qwen/Qwen2.5-7B-Instruct");
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

test("submits from an ordinary HTTP preview without crypto.randomUUID", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.addInitScript(() => {
    Object.defineProperty(globalThis.crypto, "randomUUID", {
      configurable: true,
      value: undefined
    });
  });
  await page.goto("/");

  await runReadyAnalysis(page, "Hello from an HTTP preview");

  await expect(page.locator(".chat-turn-card")).toHaveCount(1);
  await expect(page.locator(".chat-assistant-message")).toContainText("strongest residual alignment");
});

test("runs the real prompt-job protocol and keeps the conversation above two focused analyses", async ({ page }) => {
  await prepareHome(page);
  const submitted = await mockReadyPromptJob(page);
  await page.goto("/");
  await page.getByLabel("Maximum new tokens").fill("192");
  await runReadyAnalysis(page);

  await expect(page.locator(".chat-user-message")).toHaveText(generatedRun.prompt);
  await expect(page.locator(".chat-assistant-message")).toContainText("strongest residual alignment");
  await expect(page.locator(".chat-turn-explore-bar > button")).toHaveCount(7);
  await expect(page.getByRole("button", { name: /Neuron/ })).toBeVisible();
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
    model: "Qwen/Qwen2.5-7B-Instruct",
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
  await expect(page.locator(".chat-turn-explore-bar")).toHaveCount(1);
  await expect(page.locator(".chat-turn-card").first().locator(".chat-turn-explore-bar")).toHaveCount(0);
  await expect(page.locator(".chat-assistant-message").last()).toContainText("Second answer uses the prior turn.");
  await expect(page.locator(".chat-assistant-message").first()).not.toContainText("leaked turn");

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
  await expect(page.getByLabel("Steering workbench")).toBeVisible();
  await expect(page.getByLabel("Steering strength")).toHaveValue("1");
  await page.getByRole("button", { name: "Advanced settings" }).click();
  await expect(page.getByLabel("Steering output tokens")).toHaveValue("128");
  await expect(page.getByLabel("Steering desired behavior")).toBeVisible();
  const savePreset = page.getByRole("button", {
    name: "Save current Steer toward text as a preset"
  });
  const savePresetBox = await savePreset.boundingBox();
  expect(savePresetBox).not.toBeNull();
  expect(savePresetBox!.width).toBeGreaterThan(90);
  const workbenchBox = await page.getByLabel("Steering workbench").boundingBox();
  const composerBox = await page.getByLabel("Run a SafeLens analysis").boundingBox();
  expect(workbenchBox).not.toBeNull();
  expect(composerBox).not.toBeNull();
  expect(composerBox!.y).toBeGreaterThanOrEqual(workbenchBox!.y + workbenchBox!.height - 1);
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileWorkbenchBox = await page.getByLabel("Steering workbench").boundingBox();
  const mobileComposerBox = await page.getByLabel("Run a SafeLens analysis").boundingBox();
  expect(mobileWorkbenchBox).not.toBeNull();
  expect(mobileComposerBox).not.toBeNull();
  expect(mobileComposerBox!.y).toBeGreaterThanOrEqual(
    mobileWorkbenchBox!.y + mobileWorkbenchBox!.height - 1
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await page.setViewportSize({ width: 1280, height: 720 });

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
  await expect(page.getByLabel("NLA explanation tokens")).toHaveValue("256");
  await expect(page.getByRole("button", { name: "Run NLA" })).toBeEnabled();
  await page.getByRole("button", { name: "Run NLA" }).click();

  const output = page.getByLabel("NLA output");
  await expect(output).toContainText("contrast between benign safety language and jailbreak framing");
  await expect(output).toContainText("0.9100");
  expect(submitted()).toMatchObject({
    profile: "qwen2.5-7b-l20",
    positions: [2],
    revision: "main",
    maxNewTokens: 256,
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
  await expect(page.getByLabel("Attention token heatmap")).toBeVisible();
  await expect(page.getByText("View complete attention pattern")).toBeVisible();
  await page.getByText("View complete attention pattern").click();
  const canvas = page.getByRole("img", { name: /L0H1 attention heatmap/ });
  await expect(canvas).toBeVisible();
  expect(await canvas.evaluate((element) => {
    const context = (element as HTMLCanvasElement).getContext("2d");
    if (!context) return 0;
    return context.getImageData(0, 0, 40, 40).data.filter((value, index) => index % 4 !== 3 && value !== 0).length;
  })).toBeGreaterThan(0);
});

test("hydrates every available attention head for a restored workspace turn", async ({ page }) => {
  const runId = "workspace-attention-run";
  const sampleId = "workspace-attention-sample";
  const artifactId = "workspace-attention-artifact";
  const prompt = "Inspect every attention head in this restored run.";
  const tokenCount = generatedRun.tokens.length;
  const layer = generatedRun.layers[generatedRun.layers.length - 1];
  const sourceHeads = generatedRun.attentionHeads.filter((head) => head.layer === layer);
  const heads = Array.from({ length: 4 }, (_, index) => ({
    ...sourceHeads[index % sourceHeads.length],
    id: `L${layer}H${index}`,
    head: index,
    chunk: {
      destinationStart: 0,
      destinationEnd: tokenCount,
      sourceStart: 0,
      sourceEnd: tokenCount
    }
  }));
  let attentionRequests = 0;

  await page.route(/\/api\/runs(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        source: "local-workspace",
        rootName: "test-workspace",
        diagnostics: [],
        runs: [{
          runId,
          sampleId,
          modelName: generatedRun.modelName,
          modelSource: generatedRun.modelSource,
          tokenCount,
          layerCount: generatedRun.layers.length,
          artifactId,
          sourceName: "generated/prompt-workspace-attention.explorer.json",
          modifiedAt: "2026-08-12T12:00:00Z",
          sizeBytes: 8_192,
          promptPreview: prompt,
          parentRun: null,
          chunkProtocol: "safelens-chunks-v1"
        }]
      }
    });
  });
  await page.route(`**/api/runs/${runId}/samples/${sampleId}/metadata`, async (route) => {
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        protocol: "safelens-chunks-v1",
        runId,
        sampleId,
        artifactId,
        version: "test-version",
        base: {
          runId,
          sampleId,
          modelName: generatedRun.modelName,
          modelSource: generatedRun.modelSource,
          prompt,
          tokens: generatedRun.tokens,
          layers: generatedRun.layers,
          nlaCompatibility: generatedRun.nlaCompatibility,
          metricProvenance: generatedRun.metricProvenance,
          metadata: {
            ...generatedRun.metadata,
            generatedContinuation: `${prompt} Restored response.`,
            promptRunner: { ...generatedRun.metadata?.promptRunner, userPrompt: prompt },
            attentionHeadCoverage: {
              complete: true,
              availableHeadCount: 8,
              storedHeadCount: 8,
              availableByLayer: { "0": 4, "1": 4 },
              storedByLayer: { "0": 4, "1": 4 }
            }
          }
        },
        chunks: [
          { component: "attentionHeads", itemCount: 8, rangeAxis: "token-square", layerFilter: true, selectorFilter: false },
          { component: "residualCells", itemCount: 0, rangeAxis: "token", layerFilter: false, selectorFilter: false },
          { component: "logitLens", itemCount: 0, rangeAxis: "token", layerFilter: false, selectorFilter: false }
        ]
      }
    });
  });
  await page.route(`**/api/runs/${runId}/samples/${sampleId}/chunks/*`, async (route) => {
    const url = new URL(route.request().url());
    const component = url.pathname.split("/").at(-1);
    if (component === "attentionHeads") attentionRequests += 1;
    await route.fulfill({
      json: {
        schemaVersion: "1.0",
        protocol: "safelens-chunks-v1",
        runId,
        sampleId,
        artifactId,
        version: "test-version",
        component,
        tokenRange: [0, tokenCount],
        sourceRange: component === "attentionHeads" ? [0, tokenCount] : null,
        layer: component === "attentionHeads" ? layer : null,
        selector: null,
        data: component === "attentionHeads" ? heads : []
      }
    });
  });
  await page.route("**/api/prompt/options", async (route) => {
    await route.fulfill({ json: { models: [generatedRun.modelName], templates: ["plain", "chat"], maxNewTokens: 512 } });
  });

  await page.goto("/");
  await page.locator(".chat-history-row").filter({ hasText: "Inspect every attention" }).locator(".chat-history-open").click();
  await expect(page.locator(".chat-user-message")).toHaveText(prompt);
  await page.getByRole("button", { name: /Attention/ }).click();

  await expect(page.locator(".chat-head-overview > header > span")).toHaveText("4 / 4 heads · complete");
  await expect(page.getByLabel("Attention head", { exact: true }).locator("option")).toHaveCount(5);
  await expect(page.getByLabel("Attention head", { exact: true })).toHaveValue(`L${layer}AVG`);
  await expect(page.getByLabel("Attention head choices").getByRole("radio")).toHaveCount(5);
  expect(attentionRequests).toBe(1);
});

test("keeps Neuron, Explanation, and Attention usable on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Neuron/ }).click();
  await expect(page.getByRole("heading", { name: "Neuron intervention" })).toBeVisible();
  await expect(page.getByLabel("MLP neuron", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  await page.getByRole("button", { name: /Explain/ }).click();
  await page.getByRole("tab", { name: /J-Lens/ }).click();
  await expect(page.getByLabel("J-Lens output")).toBeVisible();
  await expect(page.getByLabel("Explanation token position").getByRole("radio").first()).toHaveCSS("min-height", "44px");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);

  await page.getByRole("button", { name: /Attention/ }).click();
  await expect(page.getByLabel("Attention token heatmap")).toBeVisible();
  await page.getByText("View complete attention pattern").click();
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
  await page.getByRole("button", { name: "Advanced settings" }).click();
  await expect(page.getByLabel("Steering output tokens")).toHaveValue("128");
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
    maxNewTokens: 128,
    temperature: 0
  });
});

test("opens real MLP neuron intervention from Chat", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Neuron/ }).click();
  await expect(page.getByRole("heading", { name: "Neuron intervention" })).toBeVisible();
  await expect(page.getByLabel("MLP neuron", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Neuron activation factor")).toHaveValue("0");
  await expect(page.getByRole("button", { name: "Suppress", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Run neuron intervention" })).toBeEnabled();
});

test("discovers active SAE features and runs a scale-aware intervention from Chat", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await prepareHome(page);
  await mockReadyPromptJob(page, gemmaRun);
  const submitted = await mockReadySAEFeatureFlow(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /SAE/ }).click();
  await expect(page.getByRole("heading", { name: "Gemma Scope SAE" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Output boundary" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("SAE output tokens")).toHaveValue("64");
  await page.getByRole("button", { name: "Find active features" }).click();

  const candidate = page.getByLabel("SAE feature candidates").getByRole("radio", { name: /F8439/ });
  await expect(candidate).toContainText("descriptive sentence structure");
  await expect(candidate).toContainText("Suggested +850.000");
  await candidate.click();
  await expect(page.getByLabel("SAE feature index")).toHaveValue("8439");
  await expect(page.getByLabel("SAE feature delta value")).toHaveValue("850");
  await expect(page.getByText("sentence · description")).toBeVisible();
  await page.getByRole("button", { name: "Ablate feature" }).click();
  await expect(page.getByLabel("SAE intervention token range").getByRole("button").nth(2)).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Add activation" }).click();
  await expect(page.getByRole("button", { name: "Output boundary" })).toHaveAttribute("aria-pressed", "true");
  await page.getByLabel("SAE output tokens").fill("96");
  await page.getByRole("button", { name: "Run SAE intervention" }).click();

  await expect(page.getByLabel("Steering comparison")).toContainText("Original Gemma response.");
  await expect(page.getByLabel("Steering comparison")).toContainText("Feature-amplified Gemma response.");
  expect(submitted()).toMatchObject({
    mode: "sae_feature",
    layer: 12,
    featureIndex: 8439,
    scale: 850,
    positionStart: gemmaRun.tokens.length - 1,
    positionEnd: gemmaRun.tokens.length,
    maxNewTokens: 96,
    saeOperation: "add"
  });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test("keeps clean/corrupt patching and single attention-head selection in Chat", async ({ page }) => {
  await prepareHome(page);
  await mockReadyPromptJob(page);
  const submitted = await mockReadyPatchingJob(page);
  await page.goto("/");
  await runReadyAnalysis(page);

  await page.getByRole("button", { name: /Patch/ }).click();
  await expect(page.getByRole("heading", { name: "Activation patching" })).toBeVisible();
  await page.getByRole("button", { name: "Attention head", exact: true }).click();
  const headPicker = page.getByLabel("Patching attention head");
  await expect(headPicker.locator("option")).toHaveCount(2);
  await headPicker.selectOption("1");
  const layers = page.getByLabel("Patching layers").getByRole("button");
  await layers.nth(0).click();
  await expect(layers.nth(0)).toHaveAttribute("aria-pressed", "true");
  await expect(layers.nth(1)).toHaveAttribute("aria-pressed", "false");
  await page.getByLabel("Corrupt patching input").fill("Corrupted aligned prompt");
  const runPatches = page.getByRole("button", { name: /Run \d+ patch/ });
  await expect(runPatches).toBeEnabled();
  await runPatches.click();
  await expect(page.getByLabel("Activation patching result")).toContainText("L0H1");
  expect(submitted()).toMatchObject({ component: "z", head: 1, layers: [0], positions: [2] });
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
