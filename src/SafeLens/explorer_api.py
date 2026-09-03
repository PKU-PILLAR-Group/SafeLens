"""Local HTTP data plane and constrained job runner for SafeLens Explorer."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import queue
import re
import subprocess
import sys
import threading
import uuid
import webbrowser
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, TypeVar

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, model_validator

from SafeLens.explorer_chunks import MANIFEST_PROTOCOL

DEFAULT_ARTIFACT_ROOT = Path("outputs/local-explorer")
DEFAULT_MAX_FILE_BYTES = 128 * 1024 * 1024
DEFAULT_PROMPT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
TINYGPT2_MODEL = "sshleifer/tiny-gpt2"
DEFAULT_EXPLORER_HOST = "127.0.0.1"
DEFAULT_EXPLORER_PORT = 7860
LOCAL_EXPLORER_HOSTS = {"127.0.0.1", "localhost", "::1"}
TERMINAL_JOB_STATES = {"ready", "error", "cancelled"}


def _default_allowed_models() -> tuple[str, ...]:
    from SafeLens.nla import list_nla_profiles
    from SafeLens.sae_profiles import list_sae_profiles

    models = [DEFAULT_PROMPT_MODEL, TINYGPT2_MODEL]
    models.extend(str(profile["base_model"]) for profile in list_nla_profiles())
    # Include every exact SAE base model in the picker. Gemma-2-9B can be used
    # both by the standalone demo and as a normal multi-turn Chat model.
    models.extend(profile.model_name for profile in list_sae_profiles())
    return tuple(dict.fromkeys(models))


class RemoteParentRun(BaseModel):
    runId: str
    sampleId: str


class RemoteRunSummary(BaseModel):
    runId: str
    sampleId: str
    modelName: str
    modelSource: str
    tokenCount: int = Field(ge=1)
    layerCount: int = Field(ge=1)
    artifactId: str
    sourceName: str
    modifiedAt: str
    sizeBytes: int = Field(ge=0)
    promptPreview: str | None = None
    parentRun: RemoteParentRun | None = None
    conversationId: str | None = None
    turnIndex: int | None = Field(default=None, ge=0)
    chunkProtocol: Literal["safelens-chunks-v1"] = "safelens-chunks-v1"


class ArtifactDiagnostic(BaseModel):
    sourceName: str
    code: str
    message: str


class RunIndexResponse(BaseModel):
    schemaVersion: str = "1.0"
    source: str = "local-workspace"
    rootName: str
    runs: list[RemoteRunSummary]
    diagnostics: list[ArtifactDiagnostic]


ChunkComponent = Literal[
    "residualCells",
    "logitLens",
    "jLens",
    "attentionHeads",
    "attentionCells",
    "mlpNeurons",
    "mlpCells",
    "attributionTracks",
    "attributionMethods",
    "nla",
    "patching",
    "intervention",
]
CHUNK_COMPONENTS: tuple[ChunkComponent, ...] = (
    "residualCells",
    "logitLens",
    "jLens",
    "attentionHeads",
    "attentionCells",
    "mlpNeurons",
    "mlpCells",
    "attributionTracks",
    "attributionMethods",
    "nla",
    "patching",
    "intervention",
)
ModelT = TypeVar("ModelT", bound=BaseModel)


class ChunkDescriptor(BaseModel):
    component: ChunkComponent
    itemCount: int = Field(ge=0)
    rangeAxis: Literal["token", "token-square", "token-values", "none"]
    layerFilter: bool
    selectorFilter: bool


class RunMetadataResponse(BaseModel):
    schemaVersion: str = "1.0"
    protocol: Literal["safelens-chunks-v1"] = "safelens-chunks-v1"
    runId: str
    sampleId: str
    artifactId: str
    version: str
    base: dict[str, Any]
    chunks: list[ChunkDescriptor]


class RunChunkResponse(BaseModel):
    schemaVersion: str = "1.0"
    protocol: Literal["safelens-chunks-v1"] = "safelens-chunks-v1"
    runId: str
    sampleId: str
    artifactId: str
    version: str
    component: ChunkComponent
    tokenRange: tuple[int, int]
    sourceRange: tuple[int, int] | None = None
    layer: int | None
    selector: str | None
    data: Any


class HealthResponse(BaseModel):
    status: str = "ok"
    artifactAccessReadOnly: bool = True
    promptJobsEnabled: bool = True
    attributionJobsEnabled: bool = True
    nlaJobsEnabled: bool = True
    jLensJobsEnabled: bool = True
    patchingJobsEnabled: bool = True
    interventionJobsEnabled: bool = True
    datasetTestJobsEnabled: bool = True
    rootExists: bool
    artifactCount: int = Field(ge=0)


class PromptMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8_000)


class PromptRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8_000)
    template: Literal["plain", "chat"] = "plain"
    model: str = DEFAULT_PROMPT_MODEL
    seed: int = Field(default=0, ge=0, le=2_147_483_647)
    maxNewTokens: int = Field(default=128, ge=1, le=512)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    messages: list[PromptMessage] = Field(default_factory=list, max_length=24)

    @model_validator(mode="after")
    def validate_context_size(self) -> PromptRunRequest:
        total_chars = len(self.prompt) + sum(len(message.content) for message in self.messages)
        if total_chars > 32_000:
            raise ValueError("conversation context exceeds the 32,000 character limit")
        return self


class PromptOptionsResponse(BaseModel):
    models: list[str]
    templates: list[str] = ["plain", "chat"]
    maxNewTokens: int = 512


class DatasetMetricResponse(BaseModel):
    name: str
    shortName: str
    definition: str
    threshold: float = Field(ge=0.0, le=1.0)


class DatasetSampleResponse(BaseModel):
    id: str
    category: str
    prompt: str | None = None
    cleanPrompt: str | None = None
    corruptedPrompt: str | None = None
    desiredPrompt: str | None = None
    undesiredPrompt: str | None = None
    targetText: str | None = None
    expected: str


class DatasetDefinitionResponse(BaseModel):
    id: str
    name: str
    version: str
    task: str
    description: str
    source: str
    metric: DatasetMetricResponse
    samples: list[DatasetSampleResponse]


class DatasetAlgorithmResponse(BaseModel):
    id: Literal["steering", "patching"]
    name: str
    kind: Literal["optimization"]
    description: str
    paperTitle: str
    paperUrl: str
    implementation: str
    supportedDatasetIds: list[str]


class DatasetCatalogResponse(BaseModel):
    datasets: list[DatasetDefinitionResponse]
    algorithms: list[DatasetAlgorithmResponse]


class DatasetTestRequest(BaseModel):
    datasetId: str = Field(min_length=1, max_length=128)
    algorithmId: Literal["steering", "patching"]
    model: str = DEFAULT_PROMPT_MODEL
    sampleIds: list[str] = Field(default_factory=list, max_length=20)
    layer: int = Field(default=12, ge=0, le=127)
    strength: float = Field(default=1.0, ge=-20.0, le=20.0)
    seed: int = Field(default=0, ge=0, le=2_147_483_647)
    maxNewTokens: int = Field(default=24, ge=1, le=64)


class TokenizeRequest(BaseModel):
    modelName: str = Field(min_length=1)
    text: str = Field(min_length=1, max_length=4_000)


class TokenizedToken(BaseModel):
    index: int = Field(ge=0)
    tokenId: int = Field(ge=0)
    text: str


class TokenizeResponse(BaseModel):
    modelName: str
    text: str
    tokens: list[TokenizedToken]
    truncated: bool = False


class AttributionRunRequest(BaseModel):
    run: dict[str, Any]
    response: str = Field(min_length=1, max_length=4_000)
    objective: Literal["response_token_logit"] = "response_token_logit"
    targetResponseIndex: int = Field(default=0, ge=0, le=63)
    baseline: Literal["pad_token", "zero_token_id"] = "pad_token"
    nSteps: int = Field(default=32, ge=4, le=128)


class NLAPreflightRequest(BaseModel):
    modelName: str = Field(min_length=1)
    dModel: int = Field(gt=0)
    availableLayers: list[int]
    profile: str = Field(min_length=1)


class NLAPreflightResponse(BaseModel):
    profile: str
    baseModel: str
    layer: int
    component: str
    dModel: int
    avRepo: str
    arRepo: str | None
    gated: bool
    tokenConfigured: bool
    modelMatches: bool
    layerAvailable: bool
    dModelMatches: bool
    status: Literal["compatible", "incompatible", "authorization_required"]
    canSubmit: bool
    reason: str


class NLARunRequest(BaseModel):
    run: dict[str, Any]
    profile: str = Field(min_length=1)
    positions: list[int] = Field(min_length=1, max_length=8)
    revision: str = Field(default="main", min_length=1, max_length=128)
    maxNewTokens: int = Field(default=256, ge=8, le=512)
    loadReconstructor: bool = True
    confirmGatedAccess: bool = False


class JLensOptionsResponse(BaseModel):
    packageInstalled: bool
    defaultModel: str
    defaultSource: str
    defaultFilename: str
    defaultRevision: str
    profiles: list[dict[str, Any]] = Field(default_factory=list)


class JLensPreflightRequest(BaseModel):
    modelName: str = Field(min_length=1)
    dModel: int | None = Field(default=None, gt=0)
    availableLayers: list[int] = Field(min_length=1, max_length=128)
    layer: int = Field(ge=0)
    tokenCount: int = Field(ge=1, le=4_096)
    position: int = Field(ge=0)
    lensSource: str = Field(min_length=1, max_length=1_024)
    filename: str = Field(default="lens.pt", min_length=1, max_length=512)
    revision: str = Field(default="main", min_length=1, max_length=128)


class JLensPreflightResponse(BaseModel):
    packageInstalled: bool
    modelAllowed: bool
    layerAvailable: bool
    positionValid: bool
    lensConfigured: bool
    artifactChecked: bool
    fittedLayers: list[int]
    lensDModel: int | None
    canSubmit: bool
    reason: str


class JLensRunRequest(BaseModel):
    run: dict[str, Any]
    layer: int = Field(ge=0)
    position: int = Field(ge=0)
    lensSource: str = Field(min_length=1, max_length=1_024)
    filename: str = Field(default="lens.pt", min_length=1, max_length=512)
    revision: str = Field(default="main", min_length=1, max_length=128)
    topK: int = Field(default=10, ge=3, le=50)


class PatchingPreflightRequest(BaseModel):
    modelName: str = Field(min_length=1)
    cleanPrompt: str = Field(min_length=1, max_length=8_000)
    corruptedPrompt: str = Field(min_length=1, max_length=8_000)
    cleanTokenIds: list[int] = Field(min_length=1, max_length=4_096)
    layers: list[int] = Field(min_length=1, max_length=128)
    component: Literal["resid_post", "attn_out", "z", "mlp_out"]
    targetTokenId: int = Field(ge=0)


class PatchingToken(BaseModel):
    index: int
    tokenId: int
    text: str
    changed: bool


class PatchingPreflightResponse(BaseModel):
    modelAllowed: bool
    promptsDiffer: bool
    tokenCountMatches: bool
    targetTokenValid: bool
    componentSupported: bool
    cleanTokenCount: int
    corruptedTokenCount: int
    changedPositions: list[int]
    targetTokenId: int
    targetTokenText: str
    corruptedTokens: list[PatchingToken]
    canSubmit: bool
    reason: str


class PatchingRunRequest(BaseModel):
    run: dict[str, Any]
    corruptedPrompt: str = Field(min_length=1, max_length=8_000)
    component: Literal["resid_post", "attn_out", "z", "mlp_out"]
    layers: list[int] = Field(min_length=1, max_length=64)
    positions: list[int] = Field(min_length=1, max_length=128)
    head: int | None = Field(default=None, ge=0)
    targetTokenId: int = Field(ge=0)


class SAEProfileResponse(BaseModel):
    id: str
    label: str
    modelName: str
    release: str
    saeId: str
    layer: int = Field(ge=0)
    component: Literal["resid_post"]
    width: int = Field(gt=0)
    architecture: Literal["jump_relu"]
    source: str


class SAEFeatureInfoResponse(BaseModel):
    modelName: str
    layer: int = Field(ge=0)
    featureIndex: int = Field(ge=0)
    label: str
    source: Literal["neuronpedia", "index"]
    url: str | None = None
    positiveTokens: list[str] = Field(default_factory=list)
    negativeTokens: list[str] = Field(default_factory=list)
    maxActApprox: float | None = None
    vectorDefaultSteerStrength: float | None = None


class SAESteeringFeatureRequest(BaseModel):
    """One decoder feature used by the standalone Gemma steering demo."""

    featureIndex: int = Field(ge=0, le=131_071)
    strength: float = Field(ge=-9_000.0, le=9_000.0)
    layer: int = Field(default=9, ge=0, le=41)


class SAEInterventionFeatureRequest(BaseModel):
    """One Neuronpedia feature used by the Explorer SAE workbench."""

    featureIndex: int = Field(ge=0, le=131_071)
    strength: float = Field(ge=-9_000.0, le=9_000.0)
    layer: int = Field(default=9, ge=0, le=41)


class SAESteeringRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8_000)
    features: list[SAESteeringFeatureRequest] = Field(default_factory=list, max_length=32)
    maxNewTokens: int = Field(default=64, ge=1, le=512)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    seed: int = Field(default=0, ge=0, le=2_147_483_647)
    steerPosition: Literal["all", "prompt", "generated", "prompt_position"] = "all"
    promptPosition: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_prompt_and_features(self) -> SAESteeringRequest:
        self.prompt = self.prompt.strip()
        if not self.prompt:
            raise ValueError("prompt must not be empty")
        indices = [(item.layer, item.featureIndex) for item in self.features]
        if len(indices) != len(set(indices)):
            raise ValueError("features must not contain duplicate featureIndex values")
        if self.steerPosition == "prompt_position" and self.promptPosition is None:
            raise ValueError("promptPosition is required when steerPosition is prompt_position")
        return self


class SAESteeringGenerationResponse(BaseModel):
    text: str
    tokenIds: list[int]
    tokens: list[dict[str, Any]]


class SAESteeringResponse(BaseModel):
    modelName: str
    modelPath: str
    saeRelease: str
    saeId: str
    layer: int
    layers: list[int] = Field(default_factory=list)
    hookName: str
    hooks: list[str] = Field(default_factory=list)
    featureCount: int
    hiddenSize: int
    features: list[SAESteeringFeatureRequest]
    prompt: str
    default: SAESteeringGenerationResponse
    steered: SAESteeringGenerationResponse
    generationChanged: bool
    seed: int
    maxNewTokens: int
    temperature: float
    steerPosition: Literal["all", "prompt", "generated", "prompt_position"] = "all"
    promptPosition: int | None = None


class SAESteeringScanRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8_000)
    limit: int = Field(default=12, ge=1, le=32)

    @model_validator(mode="after")
    def validate_prompt(self) -> SAESteeringScanRequest:
        self.prompt = self.prompt.strip()
        if not self.prompt:
            raise ValueError("prompt must not be empty")
        return self


class SAESteeringScanResponse(BaseModel):
    modelName: str
    saeRelease: str
    saeId: str
    layer: int = Field(ge=0)
    hookName: str
    featureCount: int = Field(gt=0)
    prompt: str
    tokens: list[dict[str, Any]]
    features: list[dict[str, Any]]


def _clean_intervention_prompts(prompts: list[str], field_name: str) -> list[str]:
    cleaned = [prompt.strip() for prompt in prompts]
    if not cleaned or any(not prompt for prompt in cleaned):
        raise ValueError(f"{field_name} must contain at least one non-empty prompt")
    if any(len(prompt) > 8_000 for prompt in cleaned):
        raise ValueError(f"each {field_name} item must be at most 8000 characters")
    return cleaned


class InterventionPreflightRequest(BaseModel):
    mode: Literal["direction", "neuron", "sae_feature"] = "direction"
    modelName: str = Field(min_length=1)
    promptTokenCount: int = Field(ge=1, le=4_096)
    availableLayers: list[int] = Field(min_length=1, max_length=128)
    layer: int = Field(ge=0)
    sourceLayer: int | None = Field(default=None, ge=0)
    injectLayer: int | None = Field(default=None, ge=0)
    component: Literal["resid_post", "attn_out", "mlp_out"]
    positionStart: int = Field(ge=0)
    positionEnd: int = Field(ge=1)
    targetTokenId: int = Field(ge=0)
    desiredPrompt: str | None = Field(default=None, min_length=1, max_length=8_000)
    undesiredPrompt: str | None = Field(default=None, min_length=1, max_length=8_000)
    positivePrompts: list[str] = Field(default_factory=list, max_length=64)
    negativePrompts: list[str] = Field(default_factory=list, max_length=64)
    activationReduce: Literal["last_token", "mean"] = "last_token"
    neuron: int | None = Field(default=None, ge=0)
    availableNeurons: list[int] = Field(default_factory=list, max_length=256)
    saeRelease: str | None = Field(default=None, min_length=1, max_length=200)
    saeId: str | None = Field(default=None, min_length=1, max_length=200)
    featureIndex: int | None = Field(default=None, ge=0)
    saeOperation: Literal["add", "ablate"] = "add"

    @model_validator(mode="after")
    def normalize_references(self) -> InterventionPreflightRequest:
        self.positivePrompts = _clean_intervention_prompts(
            self.positivePrompts or ([self.desiredPrompt] if self.desiredPrompt else []),
            "positivePrompts",
        )
        self.negativePrompts = _clean_intervention_prompts(
            self.negativePrompts or ([self.undesiredPrompt] if self.undesiredPrompt else []),
            "negativePrompts",
        )
        self.desiredPrompt = self.desiredPrompt or self.positivePrompts[0]
        self.undesiredPrompt = self.undesiredPrompt or self.negativePrompts[0]
        return self


class InterventionPreflightResponse(BaseModel):
    mode: Literal["direction", "neuron", "sae_feature"]
    modelAllowed: bool
    layerAvailable: bool
    componentSupported: bool
    positionRangeValid: bool
    targetTokenValid: bool
    referencesDiffer: bool
    featureAvailable: bool
    saeProfileValid: bool = True
    saeRuntimeAvailable: bool = True
    targetTokenId: int
    targetTokenText: str
    positionStart: int
    positionEnd: int
    canSubmit: bool
    reason: str


class InterventionRunRequest(BaseModel):
    run: dict[str, Any]
    mode: Literal["direction", "neuron", "sae_feature"] = "direction"
    desiredPrompt: str | None = Field(default=None, min_length=1, max_length=8_000)
    undesiredPrompt: str | None = Field(default=None, min_length=1, max_length=8_000)
    positivePrompts: list[str] = Field(default_factory=list, max_length=64)
    negativePrompts: list[str] = Field(default_factory=list, max_length=64)
    activationReduce: Literal["last_token", "mean"] = "last_token"
    layer: int = Field(ge=0)
    sourceLayer: int | None = Field(default=None, ge=0)
    injectLayer: int | None = Field(default=None, ge=0)
    component: Literal["resid_post", "attn_out", "mlp_out"]
    scale: float = Field(ge=-1_000.0, le=1_000.0)
    positionStart: int = Field(ge=0)
    positionEnd: int = Field(ge=1)
    targetTokenId: int = Field(ge=0)
    seed: int = Field(default=0, ge=0, le=2_147_483_647)
    maxNewTokens: int = Field(default=64, ge=1, le=128)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    neuron: int | None = Field(default=None, ge=0)
    saeRelease: str | None = Field(default=None, min_length=1, max_length=200)
    saeId: str | None = Field(default=None, min_length=1, max_length=200)
    featureIndex: int | None = Field(default=None, ge=0)
    saeOperation: Literal["add", "ablate"] = "add"
    saeFeatures: list[SAEInterventionFeatureRequest] = Field(default_factory=list, max_length=32)

    @model_validator(mode="after")
    def normalize_references(self) -> InterventionRunRequest:
        if self.mode != "sae_feature" and abs(self.scale) > 20:
            raise ValueError("direction and neuron intervention scale must be between -20 and 20")
        self.positivePrompts = _clean_intervention_prompts(
            self.positivePrompts or ([self.desiredPrompt] if self.desiredPrompt else []),
            "positivePrompts",
        )
        self.negativePrompts = _clean_intervention_prompts(
            self.negativePrompts or ([self.undesiredPrompt] if self.undesiredPrompt else []),
            "negativePrompts",
        )
        self.desiredPrompt = self.desiredPrompt or self.positivePrompts[0]
        self.undesiredPrompt = self.undesiredPrompt or self.negativePrompts[0]
        if self.mode == "sae_feature" and not self.saeFeatures and self.featureIndex is not None:
            self.saeFeatures = [
                SAEInterventionFeatureRequest(
                    featureIndex=self.featureIndex,
                    strength=self.scale,
                    layer=self.layer,
                )
            ]
        return self


class SAEFeatureDiscoveryRequest(BaseModel):
    run: dict[str, Any]
    layer: int = Field(ge=0)
    component: Literal["resid_post"] = "resid_post"
    saeRelease: str = Field(min_length=1, max_length=200)
    saeId: str = Field(min_length=1, max_length=200)
    positionStart: int = Field(ge=0)
    positionEnd: int = Field(ge=1)
    limit: int = Field(default=8, ge=1, le=20)


class JobSnapshot(BaseModel):
    id: str
    kind: Literal[
        "prompt-run",
        "attribution",
        "nla",
        "jlens",
        "patching",
        "intervention",
        "sae-discovery",
        "dataset-test",
    ]
    status: Literal["idle", "loading", "ready", "error", "cancelled"]
    stage: str
    progress: int = Field(ge=0, le=100)
    detail: str
    createdAt: str
    updatedAt: str
    request: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None


JobProgress = Callable[[int, str, str], None]
JobRunner = Callable[[Any, threading.Event, JobProgress], dict[str, Any]]
PromptRunner = Callable[[PromptRunRequest, threading.Event, JobProgress], dict[str, Any]]
AttributionRunner = Callable[[AttributionRunRequest, threading.Event, JobProgress], dict[str, Any]]


@dataclass(frozen=True)
class IndexedSample:
    summary: RemoteRunSummary
    payload: dict[str, Any] | None
    physical: PhysicalIndexedSample | None = None


@dataclass(frozen=True)
class PhysicalIndexedSample:
    manifest_path: Path
    source_path: Path
    source_sha256: str
    base: dict[str, Any]
    components: dict[str, dict[str, Any]]


@dataclass
class _ExplorerJob:
    snapshot: JobSnapshot
    payload: BaseModel
    cancel_event: threading.Event


class ExplorerJobManager:
    """Single-worker queue that keeps model jobs isolated and cancellable."""

    def __init__(
        self,
        runner: JobRunner,
        *,
        kind: Literal[
            "prompt-run",
            "attribution",
            "nla",
            "jlens",
            "patching",
            "intervention",
            "sae-discovery",
            "dataset-test",
        ],
        ready_detail: str,
        error_detail: str,
    ) -> None:
        self._runner = runner
        self._kind = kind
        self._ready_detail = ready_detail
        self._error_detail = error_detail
        self._jobs: dict[str, _ExplorerJob] = {}
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._lock = threading.Lock()
        self._active_job_id: str | None = None
        self._worker = threading.Thread(target=self._work, daemon=True)
        self._worker.start()

    def submit(
        self,
        payload: BaseModel,
        *,
        public_request: dict[str, Any] | None = None,
    ) -> JobSnapshot:
        job_id = uuid.uuid4().hex
        now = _utc_now()
        with self._lock:
            jobs_ahead = self._queue.qsize() + int(self._active_job_id is not None)
            queue_detail = (
                f"Queued behind {jobs_ahead} local model job{'' if jobs_ahead == 1 else 's'}."
                if jobs_ahead
                else "Waiting for the local model worker."
            )
            job = _ExplorerJob(
                snapshot=JobSnapshot(
                    id=job_id,
                    kind=self._kind,
                    status="idle",
                    stage="queued",
                    progress=0,
                    detail=queue_detail,
                    createdAt=now,
                    updatedAt=now,
                    request=public_request or payload.model_dump(),
                ),
                payload=payload,
                cancel_event=threading.Event(),
            )
            self._jobs[job_id] = job
        self._queue.put(job_id)
        return job.snapshot.model_copy(deep=True)

    def get(self, job_id: str) -> JobSnapshot:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            return job.snapshot.model_copy(deep=True)

    def cancel(self, job_id: str) -> JobSnapshot:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if job.snapshot.status in TERMINAL_JOB_STATES:
                return job.snapshot.model_copy(deep=True)
            job.cancel_event.set()
            job.snapshot = job.snapshot.model_copy(
                update={
                    "status": "cancelled",
                    "stage": "cancelled",
                    "detail": "Cancellation requested. No result was added to the Run Library.",
                    "updatedAt": _utc_now(),
                }
            )
            snapshot = job.snapshot.model_copy(deep=True)
        return snapshot

    def _work(self) -> None:
        while True:
            job_id = self._queue.get()
            if job_id is None:
                return
            with self._lock:
                job = self._jobs.get(job_id)
                if job is None or job.cancel_event.is_set():
                    continue
                self._active_job_id = job_id
                job.snapshot = job.snapshot.model_copy(
                    update={
                        "status": "loading",
                        "stage": "starting",
                        "progress": 2,
                        "detail": "Starting the isolated model process.",
                        "updatedAt": _utc_now(),
                    }
                )

            progress = self._progress_callback(job_id)

            try:
                result = self._runner(job.payload, job.cancel_event, progress)
                with self._lock:
                    current = self._jobs[job_id]
                    if current.cancel_event.is_set():
                        continue
                    current.snapshot = current.snapshot.model_copy(
                        update={
                            "status": "ready",
                            "stage": "complete",
                            "progress": 100,
                            "detail": self._ready_detail,
                            "result": result,
                            "updatedAt": _utc_now(),
                        }
                    )
            except BaseException as exc:
                with self._lock:
                    current = self._jobs[job_id]
                    if current.cancel_event.is_set():
                        continue
                    current.snapshot = current.snapshot.model_copy(
                        update={
                            "status": "error",
                            "stage": "failed",
                            "detail": self._error_detail,
                            "error": str(exc),
                            "updatedAt": _utc_now(),
                        }
                    )
            finally:
                with self._lock:
                    if self._active_job_id == job_id:
                        self._active_job_id = None

    def _progress_callback(self, job_id: str) -> JobProgress:
        def progress(value: int, stage: str, detail: str) -> None:
            with self._lock:
                current = self._jobs.get(job_id)
                if current is None or current.cancel_event.is_set():
                    return
                current.snapshot = current.snapshot.model_copy(
                    update={
                        "status": "loading",
                        "stage": stage,
                        "progress": max(0, min(99, value)),
                        "detail": detail,
                        "updatedAt": _utc_now(),
                    }
                )

        return progress


def create_app(
    artifact_root: str | Path | None = None,
    *,
    web_root: str | Path | None = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    prompt_runner: PromptRunner | None = None,
    attribution_runner: AttributionRunner | None = None,
    nla_runner: JobRunner | None = None,
    jlens_runner: JobRunner | None = None,
    patching_runner: JobRunner | None = None,
    patching_tokenizer_loader: Callable[[str], Any] | None = None,
    intervention_runner: JobRunner | None = None,
    intervention_tokenizer_loader: Callable[[str], Any] | None = None,
    sae_discovery_runner: JobRunner | None = None,
    dataset_test_runner: JobRunner | None = None,
    allowed_models: tuple[str, ...] | None = None,
) -> FastAPI:
    """Create a localhost-oriented API constrained to one artifact root."""
    if allowed_models is None:
        allowed_models = _default_allowed_models()
    configured_root = (
        artifact_root or os.environ.get("SAFELENS_EXPLORER_ARTIFACT_ROOT") or DEFAULT_ARTIFACT_ROOT
    )
    root = Path(configured_root).expanduser().resolve()
    app = FastAPI(
        title="SafeLens Explorer API",
        version="0.1.0",
        description="Artifact access plus an explicitly constrained local prompt job queue.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Accept", "Content-Type", "If-None-Match", "Last-Event-ID"],
    )
    prompt_manager = ExplorerJobManager(
        prompt_runner or _subprocess_prompt_runner(root=root),
        kind="prompt-run",
        ready_detail="Explorer run is ready and indexed in the workspace.",
        error_detail="Prompt analysis failed. Inspect the diagnostic and retry.",
    )
    attribution_manager = ExplorerJobManager(
        attribution_runner or _subprocess_attribution_runner(root=root),
        kind="attribution",
        ready_detail="Integrated Gradients evidence is ready in a derived Explorer run.",
        error_detail=(
            "Attribution failed. Inspect the target, baseline, and diagnostic before retrying."
        ),
    )
    nla_manager = ExplorerJobManager(
        nla_runner or _subprocess_nla_runner(root=root),
        kind="nla",
        ready_detail="Exact NLA explanations and fidelity rows are ready in a derived run.",
        error_detail="NLA failed. Inspect profile compatibility, authorization, and diagnostics.",
    )
    jlens_manager = ExplorerJobManager(
        jlens_runner or _subprocess_jlens_runner(root=root),
        kind="jlens",
        ready_detail="Jacobian Lens vocabulary readout is ready in a derived run.",
        error_detail="Jacobian Lens failed. Inspect the lens artifact and model compatibility.",
    )
    patching_manager = ExplorerJobManager(
        patching_runner or _subprocess_patching_runner(root=root),
        kind="patching",
        ready_detail="Activation patching causal grid is ready in a derived Explorer run.",
        error_detail=(
            "Activation patching failed. Inspect token alignment, objective, and diagnostics."
        ),
    )
    intervention_manager = ExplorerJobManager(
        intervention_runner or _subprocess_intervention_runner(root=root),
        kind="intervention",
        ready_detail="Intervention comparison is ready in a derived Explorer run.",
        error_detail="Intervention failed. Inspect the vector references, range, and diagnostic.",
    )
    sae_discovery_manager = ExplorerJobManager(
        sae_discovery_runner or _subprocess_sae_discovery_runner(root=root),
        kind="sae-discovery",
        ready_detail="Active SAE features are ready for selection.",
        error_detail="SAE feature discovery failed. Inspect the checkpoint and token range.",
    )
    dataset_manager = ExplorerJobManager(
        dataset_test_runner or _local_dataset_test_runner(allowed_models=allowed_models),
        kind="dataset-test",
        ready_detail="Dataset test is complete. Review the metric and individual samples.",
        error_detail="Dataset test failed. Inspect model availability and the diagnostic.",
    )
    managers = (
        prompt_manager,
        attribution_manager,
        nla_manager,
        jlens_manager,
        patching_manager,
        intervention_manager,
        sae_discovery_manager,
        dataset_manager,
    )
    load_patching_tokenizer = patching_tokenizer_loader or _default_patching_tokenizer_loader
    load_response_tokenizer = patching_tokenizer_loader or _default_patching_tokenizer_loader
    load_intervention_tokenizer = (
        intervention_tokenizer_loader or _default_patching_tokenizer_loader
    )
    jlens_package_installed = (
        jlens_runner is not None or importlib.util.find_spec("jlens") is not None
    )

    @app.on_event("startup")
    def _preload_gemma_sae_runtime() -> None:
        """Warm the standalone 9B SAE runtime once when complete local assets exist."""
        enabled = os.environ.get("SAFELENS_GEMMA_SAE_PRELOAD", "1").strip().lower()
        if enabled in {"0", "false", "no", "off"}:
            return
        try:
            from SafeLens.gemma_sae_steering import (
                GemmaSteeringConfig,
                get_gemma_steering_runtime,
            )

            config = GemmaSteeringConfig.from_env()
            checkpoint = Path(config.sae_path).expanduser()
            model_path = Path(config.model_path).expanduser()
            # Avoid surprising heavyweight downloads for a server that has not
            # been configured yet. A real canonical checkpoint is >3 GiB.
            if (
                not model_path.is_dir()
                or not checkpoint.is_file()
                or checkpoint.stat().st_size < 100 * 1024 * 1024
            ):
                return
            get_gemma_steering_runtime(config)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
            # Keep the HTTP service available so the config endpoint can show
            # the actionable error and a later request can retry the load.
            print(f"SafeLens Gemma SAE preload skipped: {exc}", file=sys.stderr)

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        candidates = list(_artifact_candidates(root))
        return HealthResponse(rootExists=root.is_dir(), artifactCount=len(candidates))

    @app.get("/api/prompt/options", response_model=PromptOptionsResponse)
    def prompt_options() -> PromptOptionsResponse:
        return PromptOptionsResponse(models=list(allowed_models))

    @app.get("/api/datasets", response_model=DatasetCatalogResponse)
    def datasets() -> DatasetCatalogResponse:
        from SafeLens.dataset_eval import dataset_catalog

        return DatasetCatalogResponse.model_validate(dataset_catalog())

    @app.post("/api/jobs/dataset-test", response_model=JobSnapshot, status_code=202)
    def submit_dataset_test(payload: DatasetTestRequest) -> JobSnapshot:
        from SafeLens.dataset_eval import get_algorithm, get_dataset

        dataset = get_dataset(payload.datasetId)
        algorithm = get_algorithm(payload.algorithmId)
        if dataset is None:
            raise HTTPException(
                status_code=422,
                detail={"code": "unknown_dataset", "message": "Select a known dataset."},
            )
        if algorithm is None or payload.datasetId not in algorithm["supportedDatasetIds"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "incompatible_dataset_algorithm",
                    "message": "The selected algorithm does not support this dataset.",
                },
            )
        if payload.model not in allowed_models:
            raise HTTPException(
                status_code=422,
                detail={"code": "model_not_allowed", "message": "Select an allowed model."},
            )
        available_ids = {str(sample["id"]) for sample in dataset["samples"]}
        if len(set(payload.sampleIds)) != len(payload.sampleIds) or any(
            sample_id not in available_ids for sample_id in payload.sampleIds
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_dataset_samples",
                    "message": "Sample IDs must be unique members of the selected dataset.",
                },
            )
        return dataset_manager.submit(payload)

    @app.post("/api/tokenize", response_model=TokenizeResponse)
    def tokenize_response(payload: TokenizeRequest) -> TokenizeResponse:
        if payload.modelName not in allowed_models:
            raise HTTPException(
                status_code=422,
                detail={"code": "model_not_allowed", "message": "Select an allowed local model."},
            )
        try:
            tokenizer = load_response_tokenizer(payload.modelName)
            token_ids = [
                int(token_id)
                for token_id in tokenizer.encode(
                    payload.text,
                    add_special_tokens=False,
                )
            ]
            truncated = len(token_ids) > 64
            token_ids = token_ids[:64]
            tokens = [
                TokenizedToken(
                    index=index,
                    tokenId=token_id,
                    text=str(
                        tokenizer.decode(
                            [token_id],
                            clean_up_tokenization_spaces=False,
                        )
                    ),
                )
                for index, token_id in enumerate(token_ids)
            ]
            return TokenizeResponse(
                modelName=payload.modelName,
                text=payload.text,
                tokens=tokens,
                truncated=truncated,
            )
        except (OSError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "tokenize_error", "message": str(exc)},
            ) from exc

    @app.get("/api/nla/profiles")
    def nla_profiles() -> list[dict[str, Any]]:
        from SafeLens.nla import list_nla_profiles

        return list_nla_profiles()

    @app.get("/api/jlens/options", response_model=JLensOptionsResponse)
    def jlens_options() -> JLensOptionsResponse:
        from SafeLens.jlens_profiles import (
            QWEN25_7B_INSTRUCT_JLENS,
            list_jlens_profiles,
        )

        bundled_lens = root / "jlens" / "sshleifer-tiny-gpt2" / "lens.pt"
        configured_source = os.environ.get("SAFELENS_JLENS_SOURCE", "")
        default_source = configured_source or QWEN25_7B_INSTRUCT_JLENS.source
        default_model = os.environ.get(
            "SAFELENS_JLENS_MODEL",
            QWEN25_7B_INSTRUCT_JLENS.base_model,
        )
        default_filename = os.environ.get(
            "SAFELENS_JLENS_FILENAME",
            QWEN25_7B_INSTRUCT_JLENS.filename,
        )
        default_revision = os.environ.get(
            "SAFELENS_JLENS_REVISION",
            QWEN25_7B_INSTRUCT_JLENS.revision,
        )
        profiles = list_jlens_profiles()
        if bundled_lens.is_file():
            profiles.append(
                {
                    "name": "tiny-gpt2-bundled-smoke",
                    "baseModel": TINYGPT2_MODEL,
                    "source": str(bundled_lens),
                    "filename": "lens.pt",
                    "revision": "local",
                    "dModel": 2,
                    "sourceLayers": [0],
                    "defaultLayer": 0,
                    "nPrompts": 1,
                    "description": "Bundled TinyGPT2 smoke-test checkpoint.",
                }
            )
        return JLensOptionsResponse(
            packageInstalled=jlens_package_installed,
            defaultModel=default_model,
            defaultSource=default_source,
            defaultFilename=default_filename,
            defaultRevision=default_revision,
            profiles=profiles,
        )

    @app.post("/api/jlens/preflight", response_model=JLensPreflightResponse)
    def jlens_preflight(payload: JLensPreflightRequest) -> JLensPreflightResponse:
        return _jlens_preflight(
            payload,
            package_installed=jlens_package_installed,
            allowed_models=allowed_models,
            artifact_root=root,
        )

    @app.post("/api/nla/preflight", response_model=NLAPreflightResponse)
    def nla_preflight(payload: NLAPreflightRequest) -> NLAPreflightResponse:
        try:
            return _nla_preflight(payload)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "unknown_nla_profile", "message": str(exc)},
            ) from exc

    @app.post("/api/patching/preflight", response_model=PatchingPreflightResponse)
    def patching_preflight(payload: PatchingPreflightRequest) -> PatchingPreflightResponse:
        if payload.modelName not in allowed_models:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "model_not_allowed",
                    "message": "Run model is not enabled for jobs.",
                },
            )
        try:
            tokenizer = load_patching_tokenizer(payload.modelName)
            return _patching_preflight(payload, tokenizer, allowed_models=allowed_models)
        except (OSError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "patching_preflight_error", "message": str(exc)},
            ) from exc

    @app.get("/api/intervention/sae-profiles", response_model=list[SAEProfileResponse])
    def intervention_sae_profiles(
        modelName: str | None = Query(default=None, min_length=1),
    ) -> list[SAEProfileResponse]:
        from SafeLens.sae_profiles import list_sae_profiles

        return [
            SAEProfileResponse.model_validate(profile.to_api())
            for profile in list_sae_profiles(model_name=modelName)
        ]

    @app.get(
        "/api/intervention/sae-feature-info",
        response_model=SAEFeatureInfoResponse,
        response_model_exclude_none=True,
    )
    def intervention_sae_feature_info(
        modelName: str = Query(min_length=1),
        layer: int = Query(ge=0),
        featureIndex: int = Query(ge=0),
    ) -> SAEFeatureInfoResponse:
        from SafeLens.explorer_sae import neuronpedia_feature_info
        from SafeLens.sae_profiles import list_sae_profiles

        profile = next(
            (item for item in list_sae_profiles(model_name=modelName) if item.layer == layer),
            None,
        )
        if profile is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "sae_profile_missing",
                    "message": "No compatible SAE profile is available for this model and layer.",
                },
            )
        if featureIndex >= profile.width:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "sae_feature_out_of_range",
                    "message": f"Feature index must be below {profile.width}.",
                },
            )
        info = neuronpedia_feature_info(
            model_name=profile.model_name,
            layer=profile.layer,
            sae_id=profile.sae_id,
            feature_index=featureIndex,
        )
        return SAEFeatureInfoResponse(
            modelName=profile.model_name,
            layer=profile.layer,
            featureIndex=featureIndex,
            label=str(info["label"]),
            source="neuronpedia" if info.get("source") == "neuronpedia" else "index",
            url=info.get("url"),
            positiveTokens=list(info.get("positiveTokens", [])),
            negativeTokens=list(info.get("negativeTokens", [])),
            maxActApprox=info.get("maxActApprox"),
            vectorDefaultSteerStrength=info.get("vectorDefaultSteerStrength"),
        )

    @app.get("/api/sae-steering/config")
    def sae_steering_config() -> dict[str, Any]:
        """Return the configured Gemma-2-9B-it demo runtime and presets."""
        from SafeLens.gemma_sae_steering import runtime_status

        return runtime_status()

    @app.post("/api/sae-steering", response_model=SAESteeringResponse)
    def sae_steering(payload: SAESteeringRequest) -> SAESteeringResponse:
        """Generate default and multi-feature steered Gemma continuations."""
        from SafeLens.gemma_sae_steering import SAEFeature, steer_gemma_prompt

        try:
            result = steer_gemma_prompt(
                payload.prompt,
                [
                    SAEFeature(
                        feature_index=item.featureIndex,
                        strength=item.strength,
                        layer=item.layer,
                    )
                    for item in payload.features
                ],
                max_new_tokens=payload.maxNewTokens,
                temperature=payload.temperature,
                seed=payload.seed,
                steer_position=payload.steerPosition,
                prompt_position=payload.promptPosition,
            )
            return SAESteeringResponse.model_validate(result)
        except (
            ImportError,
            FileNotFoundError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "sae_steering_error", "message": str(exc)},
            ) from exc

    @app.post("/api/sae-steering/scan", response_model=SAESteeringScanResponse)
    def sae_steering_scan(payload: SAESteeringScanRequest) -> SAESteeringScanResponse:
        """Encode a prompt with the canonical GemmaScope JumpReLU SAE."""
        from concurrent.futures import ThreadPoolExecutor

        from SafeLens.explorer_sae import neuronpedia_feature_info
        from SafeLens.gemma_sae_steering import scan_gemma_prompt

        try:
            result = scan_gemma_prompt(payload.prompt, limit=payload.limit)
            feature_rows = list(result.get("features", []))

            def enrich(row: dict[str, Any]) -> dict[str, Any]:
                info = neuronpedia_feature_info(
                    model_name=result["modelName"],
                    layer=int(result["layer"]),
                    sae_id=result["saeId"],
                    feature_index=int(row["featureIndex"]),
                )
                max_activation = float(row["maxActivation"])
                default_strength = info.get("vectorDefaultSteerStrength")
                return {
                    **row,
                    "label": str(info["label"]),
                    "source": "neuronpedia" if info.get("source") == "neuronpedia" else "index",
                    "url": info.get("url"),
                    "positiveTokens": list(info.get("positiveTokens", [])),
                    "negativeTokens": list(info.get("negativeTokens", [])),
                    "maxActApprox": info.get("maxActApprox"),
                    "vectorDefaultSteerStrength": default_strength,
                    # The UI can use this exact value as the initial coefficient
                    # while still showing the measured prompt activation above.
                    "suggestedStrength": float(default_strength)
                    if isinstance(default_strength, (int, float))
                    else max_activation,
                }

            if feature_rows:
                with ThreadPoolExecutor(max_workers=min(8, len(feature_rows))) as executor:
                    result["features"] = list(executor.map(enrich, feature_rows))
            return SAESteeringScanResponse.model_validate(result)
        except (
            ImportError,
            FileNotFoundError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "sae_scan_error", "message": str(exc)},
            ) from exc

    @app.post("/api/intervention/preflight", response_model=InterventionPreflightResponse)
    def intervention_preflight(
        payload: InterventionPreflightRequest,
    ) -> InterventionPreflightResponse:
        if payload.modelName not in allowed_models:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "model_not_allowed",
                    "message": "Run model is not enabled for jobs.",
                },
            )
        try:
            if payload.mode == "sae_feature" and intervention_tokenizer_loader is None:
                _require_sae_base_model_snapshot(payload.modelName)
            tokenizer = load_intervention_tokenizer(payload.modelName)
            return _intervention_preflight(payload, tokenizer, allowed_models=allowed_models)
        except HTTPException:
            raise
        except (OSError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "intervention_preflight_error", "message": str(exc)},
            ) from exc

    @app.post("/api/jobs/prompt", response_model=JobSnapshot, status_code=202)
    def submit_prompt(payload: PromptRunRequest) -> JobSnapshot:
        if payload.model not in allowed_models:
            raise HTTPException(
                status_code=422,
                detail={"code": "model_not_allowed", "message": "Select an allowed local model."},
            )
        return prompt_manager.submit(payload)

    @app.post("/api/jobs/attribution", response_model=JobSnapshot, status_code=202)
    def submit_attribution(payload: AttributionRunRequest) -> JobSnapshot:
        encoded_size = len(json.dumps(payload.run).encode("utf-8"))
        if encoded_size > max_file_bytes:
            raise HTTPException(
                status_code=413,
                detail={"code": "run_too_large", "message": "Run exceeds the compact job limit."},
            )
        try:
            _require_sample_metadata(payload.run, index=0)
        except ArtifactReadError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc
        if payload.run["modelName"] not in allowed_models:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "model_not_allowed",
                    "message": "Run model is not enabled for jobs.",
                },
            )
        job_payload = _hydrate_workspace_job_payload(
            payload,
            root=root,
            max_file_bytes=max_file_bytes,
        )
        return attribution_manager.submit(
            job_payload,
            public_request={
                **payload.model_dump(exclude={"run"}),
                "sourceRun": {
                    "runId": payload.run["runId"],
                    "sampleId": payload.run["sampleId"],
                    "modelName": payload.run["modelName"],
                },
            },
        )

    @app.post("/api/jobs/nla", response_model=JobSnapshot, status_code=202)
    def submit_nla(payload: NLARunRequest) -> JobSnapshot:
        encoded_size = len(json.dumps(payload.run).encode("utf-8"))
        if encoded_size > max_file_bytes:
            raise HTTPException(
                status_code=413,
                detail={"code": "run_too_large", "message": "Run exceeds the compact job limit."},
            )
        try:
            _require_sample_metadata(payload.run, index=0)
            compatibility = payload.run["nlaCompatibility"]
            preflight = _nla_preflight(
                NLAPreflightRequest(
                    modelName=payload.run["modelName"],
                    dModel=int(compatibility["dModel"]),
                    availableLayers=list(compatibility["availableLayers"]),
                    profile=payload.profile,
                )
            )
        except (ArtifactReadError, KeyError, TypeError, ValueError) as exc:
            code = exc.code if isinstance(exc, ArtifactReadError) else "invalid_nla_request"
            raise HTTPException(
                status_code=422,
                detail={"code": code, "message": str(exc)},
            ) from exc
        if not preflight.canSubmit:
            raise HTTPException(
                status_code=409,
                detail={"code": preflight.status, "message": preflight.reason},
            )
        if not payload.loadReconstructor:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "reconstructor_required",
                    "message": "Explorer NLA jobs require AR reconstruction fidelity.",
                },
            )
        if preflight.gated and not payload.confirmGatedAccess:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "gated_confirmation_required",
                    "message": "Confirm gated profile access before submitting the NLA job.",
                },
            )
        token_count = len(payload.run["tokens"])
        if len(set(payload.positions)) != len(payload.positions) or any(
            position < 0 or position >= token_count for position in payload.positions
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_positions",
                    "message": "Positions must be unique token indices.",
                },
            )
        job_payload = _hydrate_workspace_job_payload(
            payload,
            root=root,
            max_file_bytes=max_file_bytes,
        )
        return nla_manager.submit(
            job_payload,
            public_request={
                **payload.model_dump(exclude={"run"}),
                "sourceRun": {
                    "runId": payload.run["runId"],
                    "sampleId": payload.run["sampleId"],
                    "modelName": payload.run["modelName"],
                },
                "preflight": preflight.model_dump(),
            },
        )

    @app.post("/api/jobs/jlens", response_model=JobSnapshot, status_code=202)
    def submit_jlens(payload: JLensRunRequest) -> JobSnapshot:
        encoded_size = len(json.dumps(payload.run).encode("utf-8"))
        if encoded_size > max_file_bytes:
            raise HTTPException(
                status_code=413,
                detail={"code": "run_too_large", "message": "Run exceeds the compact job limit."},
            )
        try:
            _require_sample_metadata(payload.run, index=0)
            preflight = _jlens_preflight(
                JLensPreflightRequest(
                    modelName=payload.run["modelName"],
                    dModel=payload.run.get("nlaCompatibility", {}).get("dModel"),
                    availableLayers=[int(layer) for layer in payload.run["layers"]],
                    layer=payload.layer,
                    tokenCount=len(payload.run["tokens"]),
                    position=payload.position,
                    lensSource=payload.lensSource,
                    filename=payload.filename,
                    revision=payload.revision,
                ),
                package_installed=jlens_package_installed,
                allowed_models=allowed_models,
                artifact_root=root,
            )
        except (ArtifactReadError, KeyError, TypeError, ValueError) as exc:
            code = exc.code if isinstance(exc, ArtifactReadError) else "invalid_jlens_request"
            raise HTTPException(
                status_code=422,
                detail={"code": code, "message": str(exc)},
            ) from exc
        if not preflight.canSubmit:
            raise HTTPException(
                status_code=409,
                detail={"code": "jlens_preflight_failed", "message": preflight.reason},
            )
        job_payload = _hydrate_workspace_job_payload(
            payload,
            root=root,
            max_file_bytes=max_file_bytes,
        )
        return jlens_manager.submit(
            job_payload,
            public_request={
                **payload.model_dump(exclude={"run"}),
                "sourceRun": {
                    "runId": payload.run["runId"],
                    "sampleId": payload.run["sampleId"],
                    "modelName": payload.run["modelName"],
                },
                "preflight": preflight.model_dump(),
            },
        )

    @app.post("/api/jobs/patching", response_model=JobSnapshot, status_code=202)
    def submit_patching(payload: PatchingRunRequest) -> JobSnapshot:
        encoded_size = len(json.dumps(payload.run).encode("utf-8"))
        if encoded_size > max_file_bytes:
            raise HTTPException(
                status_code=413,
                detail={"code": "run_too_large", "message": "Run exceeds the compact job limit."},
            )
        try:
            _require_sample_metadata(payload.run, index=0)
            if payload.run["modelName"] not in allowed_models:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": "model_not_allowed",
                        "message": "Run model is not enabled for jobs.",
                    },
                )
            preflight_request = PatchingPreflightRequest(
                modelName=payload.run["modelName"],
                cleanPrompt=payload.run["prompt"],
                corruptedPrompt=payload.corruptedPrompt,
                cleanTokenIds=[int(token["tokenId"]) for token in payload.run["tokens"]],
                layers=[int(layer) for layer in payload.run["layers"]],
                component=payload.component,
                targetTokenId=payload.targetTokenId,
            )
            tokenizer = load_patching_tokenizer(payload.run["modelName"])
            preflight = _patching_preflight(
                preflight_request, tokenizer, allowed_models=allowed_models
            )
        except HTTPException:
            raise
        except (ArtifactReadError, KeyError, OSError, TypeError, ValueError) as exc:
            code = exc.code if isinstance(exc, ArtifactReadError) else "invalid_patching_request"
            raise HTTPException(
                status_code=422,
                detail={"code": code, "message": str(exc)},
            ) from exc
        if not preflight.canSubmit:
            raise HTTPException(
                status_code=409,
                detail={"code": "patching_preflight_failed", "message": preflight.reason},
            )
        if len(set(payload.layers)) != len(payload.layers) or any(
            layer not in payload.run["layers"] for layer in payload.layers
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_layers",
                    "message": "Patch layers must be unique cached layers.",
                },
            )
        if payload.component == "z":
            if len(payload.layers) != 1:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": "invalid_head_patch_layer",
                        "message": "Attention-head patching requires exactly one layer.",
                    },
                )
            head_count = _artifact_attention_head_count(payload.run, payload.layers[0])
            if payload.head is None or (head_count is not None and payload.head >= head_count):
                detail = (
                    f"Head must be between 0 and {head_count - 1} for layer {payload.layers[0]}."
                    if head_count is not None
                    else "Attention-head patching requires a non-negative head index."
                )
                raise HTTPException(
                    status_code=422,
                    detail={"code": "invalid_attention_head", "message": detail},
                )
        if len(set(payload.positions)) != len(payload.positions) or any(
            position < 0 or position >= preflight.cleanTokenCount for position in payload.positions
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_positions",
                    "message": "Patch positions must be unique aligned tokens.",
                },
            )
        if len(payload.layers) * len(payload.positions) > 2_048:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "patch_grid_too_large",
                    "message": "Patch grid exceeds 2048 cells.",
                },
            )
        job_payload = _hydrate_workspace_job_payload(
            payload,
            root=root,
            max_file_bytes=max_file_bytes,
        )
        return patching_manager.submit(
            job_payload,
            public_request={
                **payload.model_dump(exclude={"run"}, exclude_none=True),
                "sourceRun": {
                    "runId": payload.run["runId"],
                    "sampleId": payload.run["sampleId"],
                    "modelName": payload.run["modelName"],
                },
                "preflight": preflight.model_dump(),
            },
        )

    @app.post("/api/jobs/intervention", response_model=JobSnapshot, status_code=202)
    def submit_intervention(payload: InterventionRunRequest) -> JobSnapshot:
        encoded_size = len(json.dumps(payload.run).encode("utf-8"))
        if encoded_size > max_file_bytes:
            raise HTTPException(
                status_code=413,
                detail={"code": "run_too_large", "message": "Run exceeds the compact job limit."},
            )
        try:
            payload = _hydrate_workspace_job_payload(
                payload, root=root, max_file_bytes=max_file_bytes
            )
            _require_sample_metadata(payload.run, index=0)
            if payload.run["modelName"] not in allowed_models:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": "model_not_allowed",
                        "message": "Run model is not enabled for jobs.",
                    },
                )
            preflight_request = InterventionPreflightRequest(
                mode=payload.mode,
                modelName=payload.run["modelName"],
                promptTokenCount=len(payload.run["tokens"]),
                availableLayers=[int(layer) for layer in payload.run["layers"]],
                layer=payload.layer,
                sourceLayer=payload.sourceLayer,
                injectLayer=payload.injectLayer,
                component=payload.component,
                positionStart=payload.positionStart,
                positionEnd=payload.positionEnd,
                targetTokenId=payload.targetTokenId,
                desiredPrompt=payload.desiredPrompt,
                undesiredPrompt=payload.undesiredPrompt,
                positivePrompts=payload.positivePrompts,
                negativePrompts=payload.negativePrompts,
                activationReduce=payload.activationReduce,
                neuron=payload.neuron,
                availableNeurons=[
                    int(item["neuron"])
                    for item in payload.run.get("mlpNeurons", [])
                    if isinstance(item, dict)
                    and isinstance(item.get("neuron"), int)
                    and int(item.get("layer", -1)) == payload.layer
                ],
                saeRelease=payload.saeRelease,
                saeId=payload.saeId,
                featureIndex=payload.featureIndex,
                saeOperation=payload.saeOperation,
            )
            if payload.mode == "sae_feature" and intervention_tokenizer_loader is None:
                _require_sae_base_model_snapshot(payload.run["modelName"])
            tokenizer = load_intervention_tokenizer(payload.run["modelName"])
            preflight = _intervention_preflight(
                preflight_request,
                tokenizer,
                allowed_models=allowed_models,
            )
        except HTTPException:
            raise
        except (ArtifactReadError, KeyError, OSError, TypeError, ValueError) as exc:
            code = (
                exc.code if isinstance(exc, ArtifactReadError) else "invalid_intervention_request"
            )
            raise HTTPException(
                status_code=422,
                detail={"code": code, "message": str(exc)},
            ) from exc
        if not preflight.canSubmit:
            raise HTTPException(
                status_code=409,
                detail={"code": "intervention_preflight_failed", "message": preflight.reason},
            )
        job_payload = _hydrate_workspace_job_payload(
            payload,
            root=root,
            max_file_bytes=max_file_bytes,
        )
        return intervention_manager.submit(
            job_payload,
            public_request={
                **payload.model_dump(exclude={"run"}, exclude_none=True),
                "sourceRun": {
                    "runId": payload.run["runId"],
                    "sampleId": payload.run["sampleId"],
                    "modelName": payload.run["modelName"],
                },
                "preflight": preflight.model_dump(),
            },
        )

    @app.post("/api/jobs/sae-discovery", response_model=JobSnapshot, status_code=202)
    def submit_sae_discovery(payload: SAEFeatureDiscoveryRequest) -> JobSnapshot:
        from SafeLens.sae_profiles import get_sae_profile

        encoded_size = len(json.dumps(payload.run).encode("utf-8"))
        if encoded_size > max_file_bytes:
            raise HTTPException(
                status_code=413,
                detail={"code": "run_too_large", "message": "Run exceeds the compact job limit."},
            )
        try:
            payload = _hydrate_workspace_job_payload(
                payload, root=root, max_file_bytes=max_file_bytes
            )
            _require_sample_metadata(payload.run, index=0)
            profile = get_sae_profile(
                model_name=str(payload.run["modelName"]),
                release=payload.saeRelease,
                sae_id=payload.saeId,
            )
            if profile is None:
                raise ValueError(
                    "Model, release, and SAE ID are not an enabled Gemma Scope profile."
                )
            if payload.layer != profile.layer or payload.component != profile.component:
                raise ValueError("Gemma Scope profile does not match the requested layer and site.")
            if payload.layer not in payload.run["layers"]:
                raise ValueError(f"Layer L{payload.layer} is not available in the source run.")
            token_count = len(payload.run["tokens"])
            if not 0 <= payload.positionStart < payload.positionEnd <= token_count:
                raise ValueError("Feature discovery range must stay inside the source prompt.")
            if sae_discovery_runner is None:
                _require_sae_base_model_snapshot(str(payload.run["modelName"]))
        except HTTPException:
            raise
        except (ArtifactReadError, KeyError, OSError, TypeError, ValueError) as exc:
            code = (
                exc.code if isinstance(exc, ArtifactReadError) else "invalid_sae_discovery_request"
            )
            raise HTTPException(
                status_code=422,
                detail={"code": code, "message": str(exc)},
            ) from exc
        return sae_discovery_manager.submit(
            payload,
            public_request={
                **payload.model_dump(exclude={"run"}),
                "sourceRun": {
                    "runId": payload.run["runId"],
                    "sampleId": payload.run["sampleId"],
                    "modelName": payload.run["modelName"],
                },
            },
        )

    @app.get("/api/jobs/{job_id}", response_model=JobSnapshot)
    def get_job(job_id: str) -> JobSnapshot:
        try:
            return _manager_for_job(managers, job_id).get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "job_not_found"}) from exc

    @app.delete("/api/jobs/{job_id}", response_model=JobSnapshot)
    def cancel_job(job_id: str) -> JobSnapshot:
        try:
            return _manager_for_job(managers, job_id).cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "job_not_found"}) from exc

    @app.get("/api/jobs/{job_id}/events")
    async def job_events(job_id: str, request: Request) -> StreamingResponse:
        try:
            manager = _manager_for_job(managers, job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail={"code": "job_not_found"}) from exc

        async def stream() -> AsyncIterator[str]:
            previous = ""
            while not await request.is_disconnected():
                snapshot = manager.get(job_id)
                encoded = snapshot.model_dump_json()
                if encoded != previous:
                    yield f"event: job\ndata: {encoded}\n\n"
                    previous = encoded
                if snapshot.status in TERMINAL_JOB_STATES:
                    return
                import asyncio

                await asyncio.sleep(0.15)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/runs", response_model=RunIndexResponse)
    def list_runs(limit: int = Query(default=100, ge=1, le=100)) -> RunIndexResponse:
        samples, diagnostics = _scan_artifacts(root, max_file_bytes=max_file_bytes)
        deduplicated: dict[tuple[str, str], IndexedSample] = {}
        for sample in samples:
            key = (sample.summary.runId, sample.summary.sampleId)
            deduplicated.setdefault(key, sample)
        selected = list(deduplicated.values())[:limit]
        return RunIndexResponse(
            rootName=root.name,
            runs=[sample.summary for sample in selected],
            diagnostics=diagnostics,
        )

    @app.get("/api/runs/{run_id}/samples/{sample_id}/metadata")
    def get_sample_metadata(run_id: str, sample_id: str, request: Request) -> Response:
        sample = _find_indexed_sample(
            root,
            run_id,
            sample_id,
            max_file_bytes=max_file_bytes,
        )
        etag = _sample_version_etag(sample.summary)
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        if sample.physical is not None:
            base = sample.physical.base
            descriptors = _physical_chunk_descriptors(sample.physical)
        else:
            assert sample.payload is not None
            chunk_fields = set(CHUNK_COMPONENTS)
            base = {key: value for key, value in sample.payload.items() if key not in chunk_fields}
            descriptors = _chunk_descriptors(sample.payload)
        response = RunMetadataResponse(
            runId=sample.summary.runId,
            sampleId=sample.summary.sampleId,
            artifactId=sample.summary.artifactId,
            version=etag.strip('"'),
            base=base,
            chunks=descriptors,
        )
        return JSONResponse(
            content=response.model_dump(mode="json"),
            headers={
                "Cache-Control": "no-cache",
                "ETag": etag,
                "X-SafeLens-Artifact": sample.summary.artifactId,
                "X-SafeLens-Chunk-Protocol": "safelens-chunks-v1",
                "X-SafeLens-Storage": "physical" if sample.physical else "embedded",
            },
        )

    @app.get("/api/runs/{run_id}/samples/{sample_id}/chunks/{component}")
    def get_sample_chunk(
        run_id: str,
        sample_id: str,
        component: ChunkComponent,
        request: Request,
        token_start: int = Query(default=0, ge=0, alias="tokenStart"),
        token_end: int | None = Query(default=None, ge=1, alias="tokenEnd"),
        source_start: int | None = Query(default=None, ge=0, alias="sourceStart"),
        source_end: int | None = Query(default=None, ge=1, alias="sourceEnd"),
        layer: int | None = Query(default=None, ge=0),
        selector: str | None = Query(default=None, min_length=1, max_length=256),
    ) -> Response:
        sample = _find_indexed_sample(
            root,
            run_id,
            sample_id,
            max_file_bytes=max_file_bytes,
        )
        token_count = sample.summary.tokenCount
        end = token_end if token_end is not None else min(token_count, token_start + 512)
        if token_start >= token_count or end > token_count or end <= token_start:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_chunk_range",
                    "message": f"Require 0 <= tokenStart < tokenEnd <= {token_count}.",
                },
            )
        if end - token_start > 512:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "chunk_range_too_large",
                    "message": "One chunk may contain at most 512 token positions.",
                },
            )
        resolved_source_start = source_start if source_start is not None else token_start
        resolved_source_end = source_end if source_end is not None else end
        if component == "attentionHeads" and (
            resolved_source_start >= token_count
            or resolved_source_end > token_count
            or resolved_source_end <= resolved_source_start
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_source_range",
                    "message": f"Require 0 <= sourceStart < sourceEnd <= {token_count}.",
                },
            )
        if component == "attentionHeads" and resolved_source_end - resolved_source_start > 512:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "source_range_too_large",
                    "message": "One attention chunk may contain at most 512 source positions.",
                },
            )
        version_etag = _sample_version_etag(sample.summary)
        chunk_key = (
            f"{version_etag}:{component}:{token_start}:{end}:"
            f"{resolved_source_start}:{resolved_source_end}:{layer}:{selector}"
        )
        chunk_etag = f'"{hashlib.sha256(chunk_key.encode("utf-8")).hexdigest()}"'
        if request.headers.get("if-none-match") == chunk_etag:
            return Response(status_code=304, headers={"ETag": chunk_etag})
        response = RunChunkResponse(
            runId=run_id,
            sampleId=sample_id,
            artifactId=sample.summary.artifactId,
            version=version_etag.strip('"'),
            component=component,
            tokenRange=(token_start, end),
            sourceRange=(
                (resolved_source_start, resolved_source_end)
                if component == "attentionHeads"
                else None
            ),
            layer=layer,
            selector=selector,
            data=_sample_chunk_data(
                sample,
                root=root,
                component=component,
                token_start=token_start,
                token_end=end,
                source_start=resolved_source_start,
                source_end=resolved_source_end,
                layer=layer,
                selector=selector,
            ),
        )
        return JSONResponse(
            content=response.model_dump(mode="json"),
            headers={
                "Cache-Control": "no-cache",
                "ETag": chunk_etag,
                "X-SafeLens-Artifact": sample.summary.artifactId,
                "X-SafeLens-Chunk-Protocol": "safelens-chunks-v1",
                "X-SafeLens-Storage": "physical" if sample.physical else "embedded",
            },
        )

    @app.get("/api/runs/{run_id}/samples/{sample_id}")
    def get_sample(run_id: str, sample_id: str) -> JSONResponse:
        sample = _find_indexed_sample(
            root,
            run_id,
            sample_id,
            max_file_bytes=max_file_bytes,
        )
        payload = _full_sample_payload(sample)
        etag = _payload_etag(payload)
        return JSONResponse(
            content=payload,
            headers={
                "Cache-Control": "no-store",
                "ETag": etag,
                "X-SafeLens-Artifact": sample.summary.artifactId,
                "X-SafeLens-Storage": "physical-source" if sample.physical else "embedded",
            },
        )

    resolved_web_root = resolve_explorer_web_root(web_root)
    if resolved_web_root is not None:
        assets_root = resolved_web_root / "assets"
        index_path = resolved_web_root / "index.html"

        @app.api_route(
            "/assets/{asset_path:path}", methods=["GET", "HEAD"], include_in_schema=False
        )
        def explorer_asset(asset_path: str) -> FileResponse:
            candidate = _safe_web_file(assets_root, asset_path)
            if candidate is None:
                raise HTTPException(status_code=404, detail="Explorer asset not found")
            return FileResponse(
                candidate,
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                    "X-Content-Type-Options": "nosniff",
                },
            )

        @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
        @app.api_route("/{client_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
        def explorer_spa(client_path: str = "") -> FileResponse:
            if client_path == "api" or client_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API route not found")
            candidate = _safe_web_file(resolved_web_root, client_path)
            response_path = candidate if candidate is not None else index_path
            return FileResponse(
                response_path,
                headers={
                    "Cache-Control": "no-cache",
                    "X-Content-Type-Options": "nosniff",
                },
            )

    return app


def resolve_explorer_web_root(web_root: str | Path | None = None) -> Path | None:
    """Resolve a built Explorer frontend from an override, source tree, or wheel."""
    configured = web_root or os.environ.get("SAFELENS_EXPLORER_WEB_ROOT")
    if configured is not None:
        candidate = Path(configured).expanduser().resolve()
        return candidate if (candidate / "index.html").is_file() else None

    source_candidate = Path(__file__).resolve().parents[2] / "apps" / "local_explorer" / "dist"
    packaged_candidate = Path(__file__).resolve().with_name("explorer_web")
    for candidate in (source_candidate, packaged_candidate):
        if (candidate / "index.html").is_file():
            return candidate.resolve()
    return None


def _safe_web_file(root: Path, relative_path: str) -> Path | None:
    if not relative_path:
        return None
    try:
        candidate = (root / relative_path).resolve(strict=True)
        candidate.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return candidate if candidate.is_file() else None


def _manager_for_job(managers: tuple[ExplorerJobManager, ...], job_id: str) -> ExplorerJobManager:
    for manager in managers:
        try:
            manager.get(job_id)
            return manager
        except KeyError:
            continue
    raise KeyError(job_id)


def _local_dataset_test_runner(*, allowed_models: tuple[str, ...]) -> JobRunner:
    def run(
        payload: DatasetTestRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        from SafeLens.dataset_eval import run_dataset_test

        return run_dataset_test(
            payload,
            cancel_event,
            progress,
            allowed_models=allowed_models,
        )

    return run


def _explorer_worker(name: str) -> tuple[Path, Path]:
    repository_root = Path(__file__).resolve().parents[2]
    source_worker = repository_root / "scripts" / name
    if source_worker.is_file():
        return source_worker, repository_root
    packaged_worker = Path(__file__).resolve().with_name("explorer_workers") / name
    if packaged_worker.is_file():
        return packaged_worker, Path.cwd()
    raise RuntimeError(
        f"Explorer worker {name!r} is missing. Reinstall a wheel that includes Explorer assets."
    )


def _subprocess_prompt_runner(*, root: Path) -> PromptRunner:
    script, working_directory = _explorer_worker("build_local_explorer_real_run.py")

    def run(
        payload: PromptRunRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        job_suffix = uuid.uuid4().hex[:10]
        run_id = f"prompt-{job_suffix}"
        sample_id = f"seed-{payload.seed}"
        output_dir = root / ".jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        ts_output = output_dir / f"{job_suffix}.ts"
        prompt_input = output_dir / f"{job_suffix}.prompt.json"
        temp_artifact = output_dir / f"{job_suffix}.tmp.json"
        final_artifact = root / "generated" / f"{run_id}.explorer.json"
        final_artifact.parent.mkdir(parents=True, exist_ok=True)
        prompt_input.write_text(
            json.dumps(
                {
                    "prompt": payload.prompt,
                    "template": payload.template,
                    "messages": [message.model_dump(mode="json") for message in payload.messages],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        from SafeLens.explorer_model import explorer_job_device

        configured_device = explorer_job_device()
        device_label = "GPU" if configured_device.lower().startswith("cuda") else "CPU"
        progress(8, "model", f"Loading {payload.model} on the local {device_label} worker.")
        command = [
            sys.executable,
            str(script),
            "--model",
            payload.model,
            "--prompt-input",
            str(prompt_input),
            "--output",
            str(ts_output),
            "--artifact-output",
            str(temp_artifact),
            "--run-id",
            run_id,
            "--sample-id",
            sample_id,
            "--seed",
            str(payload.seed),
            "--max-new-tokens",
            str(payload.maxNewTokens),
            "--temperature",
            str(payload.temperature),
        ]
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            progress(
                35,
                "forward",
                f"Running generation and collecting model activations on {device_label}; "
                "progress is coarse during the model forward pass.",
            )
            while True:
                try:
                    stdout, stderr = process.communicate(timeout=0.1)
                    break
                except subprocess.TimeoutExpired:
                    if cancel_event.is_set():
                        process.terminate()
                        try:
                            process.communicate(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.communicate()
                        raise RuntimeError("Prompt job cancelled") from None
            _require_not_cancelled(cancel_event)
            if process.returncode != 0:
                diagnostic = (stderr or stdout or "model subprocess failed").strip()
                raise RuntimeError(diagnostic[-2_000:])
            progress(88, "artifact", "Validating and indexing the generated Explorer artifact.")
            artifact = json.loads(temp_artifact.read_text(encoding="utf-8"))
            sample = _extract_samples(artifact)[0]
            metadata = sample.setdefault("metadata", {})
            metadata["promptRunner"] = {
                "jobVersion": "1.0",
                "template": payload.template,
                "model": payload.model,
                "seed": payload.seed,
                "maxNewTokens": payload.maxNewTokens,
                "temperature": payload.temperature,
                "contextMessages": [
                    message.model_dump(mode="json") for message in payload.messages
                ],
                "userPrompt": payload.prompt,
            }
            artifact["samples"] = [sample]
            _require_not_cancelled(cancel_event)
            temp_artifact.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
            _require_not_cancelled(cancel_event)
            temp_artifact.replace(final_artifact)
            return sample
        finally:
            ts_output.unlink(missing_ok=True)
            prompt_input.unlink(missing_ok=True)
            temp_artifact.unlink(missing_ok=True)

    return run


def _subprocess_attribution_runner(*, root: Path) -> AttributionRunner:
    script, working_directory = _explorer_worker("run_local_explorer_attribution.py")

    def run(
        payload: AttributionRunRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        job_suffix = uuid.uuid4().hex[:10]
        derived_run_id = f"{payload.run['runId']}-ig-{job_suffix}"
        output_dir = root / ".jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path = output_dir / f"{job_suffix}.attribution-input.json"
        result_path = output_dir / f"{job_suffix}.attribution-result.json"
        final_artifact = root / "generated" / f"attribution-{job_suffix}.explorer.json"
        final_artifact.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(
            json.dumps(
                {
                    "run": payload.run,
                    "request": payload.model_dump(exclude={"run"}),
                }
            ),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(script),
            "--input",
            str(input_path),
            "--output",
            str(result_path),
            "--model",
            str(payload.run["modelName"]),
            "--run-id",
            derived_run_id,
        ]
        progress(8, "model", f"Loading {payload.run['modelName']} for Captum attribution.")
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            progress(
                30,
                "integrated-gradients",
                f"Integrating {payload.nSteps} steps against {payload.baseline}.",
            )
            stdout, stderr = _communicate_cancellable(process, cancel_event)
            _require_not_cancelled(cancel_event)
            if process.returncode != 0:
                diagnostic = (stderr or stdout or "attribution subprocess failed").strip()
                raise RuntimeError(diagnostic[-2_000:])
            progress(88, "artifact", "Validating target alignment and attribution provenance.")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            _require_sample_metadata(result, index=0)
            _require_not_cancelled(cancel_event)
            envelope = {
                "schema_version": "1.0",
                "run": {
                    "run_id": result["runId"],
                    "model_name": result["modelName"],
                    "model_source": result["modelSource"],
                },
                "samples": [result],
                "metrics": sorted(result.get("metricProvenance", {})),
                "artifacts": {"embedded": True, "derived": "captum-attribution"},
            }
            result_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
            _require_not_cancelled(cancel_event)
            result_path.replace(final_artifact)
            return result
        finally:
            input_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)

    return run


def _nla_preflight(payload: NLAPreflightRequest) -> NLAPreflightResponse:
    from SafeLens.nla import get_nla_profile

    profile = get_nla_profile(payload.profile)
    model_matches = payload.modelName.lower() == profile.base_model.lower()
    layer_available = profile.layer in payload.availableLayers
    d_model_matches = payload.dModel == profile.d_model
    token_configured = bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"))
    structural = model_matches and layer_available and d_model_matches
    authorization_required = structural and profile.gated and not token_configured
    status: Literal["compatible", "incompatible", "authorization_required"]
    if not structural:
        failures = []
        if not model_matches:
            failures.append(f"model requires {profile.base_model}")
        if not layer_available:
            failures.append(f"layer L{profile.layer} is not cached")
        if not d_model_matches:
            failures.append(f"d_model requires {profile.d_model}, run has {payload.dModel}")
        status = "incompatible"
        reason = "; ".join(failures)
    elif authorization_required:
        status = "authorization_required"
        reason = "This gated profile requires an HF token configured in the local API process."
    else:
        status = "compatible"
        reason = "Model, layer, component profile and d_model are compatible."
    return NLAPreflightResponse(
        profile=profile.name,
        baseModel=profile.base_model,
        layer=profile.layer,
        component=profile.component,
        dModel=profile.d_model,
        avRepo=profile.av_repo,
        arRepo=profile.ar_repo,
        gated=profile.gated,
        tokenConfigured=token_configured,
        modelMatches=model_matches,
        layerAvailable=layer_available,
        dModelMatches=d_model_matches,
        status=status,
        canSubmit=status == "compatible",
        reason=reason,
    )


def _jlens_preflight(
    payload: JLensPreflightRequest,
    *,
    package_installed: bool,
    allowed_models: tuple[str, ...],
    artifact_root: Path,
) -> JLensPreflightResponse:
    from SafeLens.jlens_profiles import find_jlens_profile

    model_allowed = payload.modelName in allowed_models
    layer_available = payload.layer in payload.availableLayers
    position_valid = payload.position < payload.tokenCount
    source = payload.lensSource.strip()
    filename = Path(payload.filename)
    filename_valid = not filename.is_absolute() and ".." not in filename.parts
    artifact_checked = False
    fitted_layers: list[int] = []
    lens_d_model: int | None = None
    artifact_error: str | None = None
    source_path = Path(source).expanduser()
    local_requested = (
        source_path.is_absolute() or source.startswith((".", "~")) or source_path.exists()
    )
    source_valid = bool(source)
    local_candidate: Path | None = None
    if local_requested:
        try:
            resolved_source = source_path.resolve(strict=True)
            resolved_source.relative_to(artifact_root)
            local_candidate = (
                resolved_source / filename if resolved_source.is_dir() else resolved_source
            )
            local_candidate = local_candidate.resolve(strict=True)
            local_candidate.relative_to(artifact_root)
        except (OSError, ValueError):
            source_valid = False
            artifact_error = "Local lens artifacts must exist inside the Explorer artifact root."
    elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*", source):
        source_valid = False
        artifact_error = "Use a Hugging Face repository ID or a path inside the artifact root."
    registered_profile = find_jlens_profile(source, payload.filename)
    if registered_profile is not None:
        fitted_layers = list(registered_profile.source_layers)
        lens_d_model = registered_profile.d_model
        if payload.revision != registered_profile.revision:
            artifact_error = (
                "The registered J-Lens must use its pinned checkpoint revision "
                f"{registered_profile.revision}."
            )
        elif payload.modelName != registered_profile.base_model:
            artifact_error = (
                f"This registered lens fits {registered_profile.base_model}, not "
                f"{payload.modelName}."
            )
    lens_configured = source_valid and filename_valid
    if local_candidate is not None and local_candidate.is_file():
        artifact_checked = True
        try:
            import torch

            checkpoint = torch.load(local_candidate, map_location="cpu", weights_only=True)
            jacobians = checkpoint.get("J") if isinstance(checkpoint, dict) else None
            if not isinstance(jacobians, dict) or not jacobians:
                raise ValueError("checkpoint does not contain fitted Jacobian matrices")
            fitted_layers = sorted(int(layer) for layer in jacobians)
            lens_d_model = int(checkpoint["d_model"])
        except (ImportError, KeyError, OSError, TypeError, ValueError) as exc:
            artifact_error = f"The local lens artifact is invalid: {exc}."
    checks = {
        "Install the SafeLens J-Lens extra before running this analysis.": package_installed,
        "The selected model is not enabled for local jobs.": model_allowed,
        f"Layer L{payload.layer} is not available in the source Run.": layer_available,
        "The selected token position is outside the source prompt.": position_valid,
        "Configure a lens artifact and a relative checkpoint filename.": lens_configured,
        artifact_error or "The local lens artifact is readable.": artifact_error is None,
        f"Layer L{payload.layer} is not fitted in this local lens.": (
            (not artifact_checked and registered_profile is None) or payload.layer in fitted_layers
        ),
        "The local lens width does not match the source model.": (
            lens_d_model is None or payload.dModel is None or lens_d_model == payload.dModel
        ),
    }
    failures = [message for message, passed in checks.items() if not passed]
    return JLensPreflightResponse(
        packageInstalled=package_installed,
        modelAllowed=model_allowed,
        layerAvailable=layer_available,
        positionValid=position_valid,
        lensConfigured=lens_configured,
        artifactChecked=artifact_checked,
        fittedLayers=fitted_layers,
        lensDModel=lens_d_model,
        canSubmit=not failures,
        reason=(
            "Jacobian Lens package, artifact, model, layer, and token are ready."
            if not failures
            else " ".join(failures)
        ),
    )


@lru_cache(maxsize=4)
def _default_patching_tokenizer_loader(model_name: str) -> Any:
    from transformers import AutoTokenizer

    from SafeLens.explorer_model import (
        DEFAULT_EXPLORER_MODEL_CACHE,
        resolve_explorer_pretrained_path,
    )

    pretrained_path, local_files_only, _source = resolve_explorer_pretrained_path(
        model_name,
        cache_dir=DEFAULT_EXPLORER_MODEL_CACHE,
    )
    return AutoTokenizer.from_pretrained(
        pretrained_path,
        cache_dir=DEFAULT_EXPLORER_MODEL_CACHE,
        local_files_only=local_files_only,
        trust_remote_code=False,
    )


def _require_sae_base_model_snapshot(model_name: str) -> None:
    """Resolve the base model before an SAE job enters the worker queue."""
    from SafeLens.explorer_model import (
        DEFAULT_EXPLORER_MODEL_CACHE,
        resolve_explorer_pretrained_path,
    )

    try:
        pretrained_path, local_files_only, source = resolve_explorer_pretrained_path(
            model_name,
            cache_dir=DEFAULT_EXPLORER_MODEL_CACHE,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "sae_base_model_missing",
                "message": (
                    f"Gemma base model {model_name} could not be resolved from the configured "
                    f"local provider: {exc}"
                ),
            },
        ) from exc
    if not local_files_only or not Path(pretrained_path).is_dir():
        raise HTTPException(
            status_code=422,
            detail={
                "code": "sae_base_model_missing",
                "message": (
                    f"Gemma base model {model_name} is not available as a complete local "
                    f"snapshot (resolved provider: {source})."
                ),
            },
        )


def _patching_preflight(
    payload: PatchingPreflightRequest,
    tokenizer: Any,
    *,
    allowed_models: tuple[str, ...],
) -> PatchingPreflightResponse:
    encoded = tokenizer.encode(payload.corruptedPrompt, add_special_tokens=False)
    corrupted_ids = [int(token_id) for token_id in encoded]
    clean_ids = [int(token_id) for token_id in payload.cleanTokenIds]
    prompts_differ = payload.cleanPrompt != payload.corruptedPrompt
    token_count_matches = len(clean_ids) == len(corrupted_ids)
    changed_positions = [
        index
        for index, (clean_id, corrupted_id) in enumerate(
            zip(clean_ids, corrupted_ids, strict=False)
        )
        if clean_id != corrupted_id
    ]
    model_allowed = payload.modelName in allowed_models
    component_supported = payload.component in {"resid_post", "attn_out", "z", "mlp_out"}
    try:
        vocab_size = int(len(tokenizer))
    except (TypeError, AttributeError):
        vocab_size = int(getattr(tokenizer, "vocab_size", 0))
    target_token_valid = 0 <= payload.targetTokenId < vocab_size

    def decode_token(token_id: int) -> str:
        value = tokenizer.decode([token_id], clean_up_tokenization_spaces=False)
        return str(value)

    corrupted_tokens = [
        PatchingToken(
            index=index,
            tokenId=token_id,
            text=decode_token(token_id),
            changed=index < len(clean_ids) and clean_ids[index] != token_id,
        )
        for index, token_id in enumerate(corrupted_ids)
    ]
    target_text = decode_token(payload.targetTokenId) if target_token_valid else ""
    checks = {
        "model is not enabled for local jobs": model_allowed,
        "clean and corrupted prompts are identical": prompts_differ,
        "token counts do not match": token_count_matches,
        "no aligned token changed": bool(changed_positions),
        "target token is outside the tokenizer vocabulary": target_token_valid,
        "component is not supported": component_supported,
    }
    failures = [message for message, passed in checks.items() if not passed]
    can_submit = not failures
    reason = (
        "Prompts are positionally aligned and ready for causal activation patching."
        if can_submit
        else "; ".join(failures)
    )
    return PatchingPreflightResponse(
        modelAllowed=model_allowed,
        promptsDiffer=prompts_differ,
        tokenCountMatches=token_count_matches,
        targetTokenValid=target_token_valid,
        componentSupported=component_supported,
        cleanTokenCount=len(clean_ids),
        corruptedTokenCount=len(corrupted_ids),
        changedPositions=changed_positions,
        targetTokenId=payload.targetTokenId,
        targetTokenText=target_text,
        corruptedTokens=corrupted_tokens,
        canSubmit=can_submit,
        reason=reason,
    )


def _artifact_attention_head_count(run: dict[str, Any], layer: int) -> int | None:
    metadata = run.get("metadata")
    if isinstance(metadata, dict):
        coverage = metadata.get("attentionHeadCoverage")
        if isinstance(coverage, dict):
            available_by_layer = coverage.get("availableByLayer")
            if isinstance(available_by_layer, dict):
                value = available_by_layer.get(str(layer), available_by_layer.get(layer))
                if isinstance(value, int) and value > 0:
                    return value
    heads = run.get("attentionHeads")
    if not isinstance(heads, list):
        return None
    indices: list[int] = [
        item["head"]
        for item in heads
        if isinstance(item, dict)
        and item.get("layer") == layer
        and isinstance(item.get("head"), int)
        and item["head"] >= 0
    ]
    return max(indices) + 1 if indices else None


def _intervention_preflight(
    payload: InterventionPreflightRequest,
    tokenizer: Any,
    *,
    allowed_models: tuple[str, ...],
) -> InterventionPreflightResponse:
    from SafeLens.sae_profiles import get_sae_profile

    model_allowed = payload.modelName in allowed_models
    sae_profile = (
        get_sae_profile(
            model_name=payload.modelName,
            release=payload.saeRelease or "",
            sae_id=payload.saeId or "",
        )
        if payload.mode == "sae_feature"
        else None
    )
    sae_profile_valid = payload.mode != "sae_feature" or sae_profile is not None
    source_layer = payload.sourceLayer if payload.sourceLayer is not None else payload.layer
    inject_layer = payload.injectLayer if payload.injectLayer is not None else payload.layer
    source_layer_available = source_layer in payload.availableLayers
    inject_layer_available = inject_layer in payload.availableLayers
    layer_available = (
        source_layer_available
        and inject_layer_available
        and (
            sae_profile is None
            or (source_layer == sae_profile.layer and inject_layer == sae_profile.layer)
        )
    )
    component_supported = payload.component in {"resid_post", "attn_out", "mlp_out"} and (
        sae_profile is None or payload.component == sae_profile.component
    )
    position_range_valid = (
        0 <= payload.positionStart < payload.positionEnd <= payload.promptTokenCount
    )
    references_differ = (
        payload.mode != "direction" or payload.positivePrompts != payload.negativePrompts
    )
    if payload.mode == "neuron":
        feature_available = (
            payload.neuron is not None and payload.neuron in payload.availableNeurons
        )
    elif payload.mode == "sae_feature":
        feature_available = (
            sae_profile is not None
            and payload.featureIndex is not None
            and payload.featureIndex < sae_profile.width
        )
    else:
        feature_available = True
    if payload.mode == "sae_feature" and sae_profile is not None:
        from SafeLens.explorer_sae import gemma_scope_local_checkpoint_available

        sae_runtime_available = bool(
            importlib.util.find_spec("sae_lens") is not None
            or gemma_scope_local_checkpoint_available(
                model_name=sae_profile.model_name,
                release=sae_profile.release,
                sae_id=sae_profile.sae_id,
            )
        )
    else:
        sae_runtime_available = payload.mode != "sae_feature"
    try:
        vocab_size = int(len(tokenizer))
    except (TypeError, AttributeError):
        vocab_size = int(getattr(tokenizer, "vocab_size", 0))
    target_token_valid = 0 <= payload.targetTokenId < vocab_size
    target_text = (
        str(
            tokenizer.decode(
                [payload.targetTokenId],
                clean_up_tokenization_spaces=False,
            )
        )
        if target_token_valid
        else ""
    )
    checks: dict[str, bool] = {
        "model is not enabled for local jobs": model_allowed,
        f"source layer L{source_layer} is not available in the source Run": source_layer_available,
        f"inject layer L{inject_layer} is not available in the source Run": inject_layer_available,
        "component is not supported": component_supported,
        "position range must stay inside the source prompt": position_range_valid,
        "target token is outside the tokenizer vocabulary": target_token_valid,
        "desired and undesired references are identical": references_differ,
    }
    if payload.mode == "neuron":
        checks["selected MLP neuron is not available in the source run"] = feature_available
    elif payload.mode == "sae_feature":
        checks["model, release, and SAE ID are not an enabled Gemma Scope profile"] = (
            sae_profile_valid
        )
        checks["SAE feature index is outside the selected dictionary"] = feature_available
        checks[
            "Gemma Scope SAE checkpoint is unavailable (install the `sae` extra or "
            "download the public checkpoint)"
        ] = (
            sae_runtime_available
        )
    failures = [message for message, passed in checks.items() if not passed]
    can_submit = not failures
    return InterventionPreflightResponse(
        mode=payload.mode,
        modelAllowed=model_allowed,
        layerAvailable=layer_available,
        componentSupported=component_supported,
        positionRangeValid=position_range_valid,
        targetTokenValid=target_token_valid,
        referencesDiffer=references_differ,
        featureAvailable=feature_available,
        saeProfileValid=sae_profile_valid,
        saeRuntimeAvailable=sae_runtime_available,
        targetTokenId=payload.targetTokenId,
        targetTokenText=target_text,
        positionStart=payload.positionStart,
        positionEnd=payload.positionEnd,
        canSubmit=can_submit,
        reason=(
            "Intervention references, source/inject layers, activation target, "
            "and objective are ready."
            if can_submit
            else "; ".join(failures)
        ),
    )


def _subprocess_nla_runner(*, root: Path) -> JobRunner:
    script, working_directory = _explorer_worker("run_local_explorer_nla.py")

    def run(
        payload: NLARunRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        job_suffix = uuid.uuid4().hex[:10]
        derived_run_id = f"{payload.run['runId']}-nla-{job_suffix}"
        output_dir = root / ".jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path = output_dir / f"{job_suffix}.nla-input.json"
        result_path = output_dir / f"{job_suffix}.nla-result.json"
        final_artifact = root / "generated" / f"nla-{job_suffix}.explorer.json"
        final_artifact.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(
            json.dumps(
                {
                    "run": payload.run,
                    "request": payload.model_dump(exclude={"run", "confirmGatedAccess"}),
                }
            ),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(script),
            "--input",
            str(input_path),
            "--output",
            str(result_path),
            "--run-id",
            derived_run_id,
        ]
        progress(5, "base-model", "Loading the compatible base model and exact activation layer.")
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            progress(
                25,
                "nla-av-ar",
                f"Loading {payload.profile} AV/AR at revision {payload.revision}.",
            )
            stdout, stderr = _communicate_cancellable(process, cancel_event)
            _require_not_cancelled(cancel_event)
            if process.returncode != 0:
                diagnostic = (stderr or stdout or "NLA subprocess failed").strip()
                raise RuntimeError(diagnostic[-2_000:])
            progress(90, "artifact", "Validating exact NLA rows and checkpoint provenance.")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            _require_sample_metadata(result, index=0)
            _require_not_cancelled(cancel_event)
            envelope = {
                "schema_version": "1.0",
                "run": {
                    "run_id": result["runId"],
                    "model_name": result["modelName"],
                    "model_source": result["modelSource"],
                },
                "samples": [result],
                "metrics": sorted(result.get("metricProvenance", {})),
                "artifacts": {"embedded": True, "derived": "nla-av-ar"},
            }
            result_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
            _require_not_cancelled(cancel_event)
            result_path.replace(final_artifact)
            return result
        finally:
            input_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)

    return run


def _subprocess_jlens_runner(*, root: Path) -> JobRunner:
    script, working_directory = _explorer_worker("run_local_explorer_jlens.py")

    def run(
        payload: JLensRunRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        job_suffix = uuid.uuid4().hex[:10]
        derived_run_id = f"{payload.run['runId']}-jlens-{job_suffix}"
        output_dir = root / ".jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path = output_dir / f"{job_suffix}.jlens-input.json"
        result_path = output_dir / f"{job_suffix}.jlens-result.json"
        final_artifact = root / "generated" / f"jlens-{job_suffix}.explorer.json"
        final_artifact.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(
            json.dumps({"run": payload.run, "request": payload.model_dump(exclude={"run"})}),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(script),
            "--input",
            str(input_path),
            "--output",
            str(result_path),
            "--run-id",
            derived_run_id,
        ]
        from SafeLens.explorer_model import explorer_job_device

        device = explorer_job_device()
        progress(5, "base-model", f"Loading the source model on {device}.")
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            progress(30, "jlens-artifact", f"Loading Jacobian lens {payload.filename}.")
            stdout, stderr = _communicate_cancellable(process, cancel_event)
            _require_not_cancelled(cancel_event)
            if process.returncode != 0:
                diagnostic = (stderr or stdout or "Jacobian Lens subprocess failed").strip()
                raise RuntimeError(diagnostic[-2_000:])
            progress(90, "artifact", "Validating Jacobian Lens rows and provenance.")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            _require_sample_metadata(result, index=0)
            rows = result.get("jLens")
            if not isinstance(rows, list) or not rows:
                raise ValueError("Jacobian Lens worker did not return a result row.")
            _require_not_cancelled(cancel_event)
            envelope = {
                "schema_version": "1.0",
                "run": {
                    "run_id": result["runId"],
                    "model_name": result["modelName"],
                    "model_source": result["modelSource"],
                },
                "samples": [result],
                "metrics": sorted(result.get("metricProvenance", {})),
                "artifacts": {"embedded": True, "derived": "jacobian-lens"},
            }
            result_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
            _require_not_cancelled(cancel_event)
            result_path.replace(final_artifact)
            return result
        finally:
            input_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)

    return run


def _subprocess_patching_runner(*, root: Path) -> JobRunner:
    script, working_directory = _explorer_worker("run_local_explorer_patching.py")

    def run(
        payload: PatchingRunRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        job_suffix = uuid.uuid4().hex[:10]
        derived_run_id = f"{payload.run['runId']}-patch-{job_suffix}"
        output_dir = root / ".jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path = output_dir / f"{job_suffix}.patching-input.json"
        result_path = output_dir / f"{job_suffix}.patching-result.json"
        final_artifact = root / "generated" / f"patching-{job_suffix}.explorer.json"
        final_artifact.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(
            json.dumps(
                {
                    "run": payload.run,
                    "request": payload.model_dump(exclude={"run"}, exclude_none=True),
                }
            ),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(script),
            "--input",
            str(input_path),
            "--output",
            str(result_path),
            "--run-id",
            derived_run_id,
        ]
        progress(6, "base-model", f"Loading {payload.run['modelName']} for activation patching.")
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            progress(
                28,
                "patch-grid",
                f"Evaluating {len(payload.layers) * len(payload.positions)} causal patch cells.",
            )
            stdout, stderr = _communicate_cancellable(process, cancel_event)
            _require_not_cancelled(cancel_event)
            if process.returncode != 0:
                diagnostic = (stderr or stdout or "patching subprocess failed").strip()
                raise RuntimeError(diagnostic[-2_000:])
            progress(90, "artifact", "Validating causal scores, recovery, and source provenance.")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            _require_sample_metadata(result, index=0)
            patching = result.get("patching")
            if not isinstance(patching, dict) or not isinstance(patching.get("cells"), list):
                raise ValueError("Patching worker did not produce a causal cell grid.")
            _require_not_cancelled(cancel_event)
            envelope = {
                "schema_version": "1.0",
                "run": {
                    "run_id": result["runId"],
                    "model_name": result["modelName"],
                    "model_source": result["modelSource"],
                },
                "samples": [result],
                "metrics": sorted(result.get("metricProvenance", {})),
                "artifacts": {"embedded": True, "derived": "activation-patching"},
            }
            result_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
            _require_not_cancelled(cancel_event)
            result_path.replace(final_artifact)
            return result
        finally:
            input_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)

    return run


def _subprocess_intervention_runner(*, root: Path) -> JobRunner:
    script, working_directory = _explorer_worker("run_local_explorer_intervention.py")

    def run(
        payload: InterventionRunRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        job_suffix = uuid.uuid4().hex[:10]
        derived_run_id = f"{payload.run['runId']}-intervene-{job_suffix}"
        output_dir = root / ".jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path = output_dir / f"{job_suffix}.intervention-input.json"
        result_path = output_dir / f"{job_suffix}.intervention-result.json"
        final_artifact = root / "generated" / f"intervention-{job_suffix}.explorer.json"
        final_artifact.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(
            json.dumps(
                {
                    "run": payload.run,
                    "request": payload.model_dump(exclude={"run"}),
                }
            ),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(script),
            "--input",
            str(input_path),
            "--output",
            str(result_path),
            "--run-id",
            derived_run_id,
        ]
        progress(5, "base-model", f"Loading {payload.run['modelName']} for intervention.")
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if payload.mode == "neuron":
                progress(24, "neuron-intervention", "Preparing the selected MLP neuron hook.")
            elif payload.mode == "sae_feature":
                progress(24, "sae-feature", "Loading the validated Gemma Scope SAE feature.")
            else:
                progress(24, "steering-vector", "Building the chat-aligned contrastive direction.")
            stdout, stderr = _communicate_cancellable(process, cancel_event)
            _require_not_cancelled(cancel_event)
            if process.returncode != 0:
                diagnostic = (stderr or stdout or "intervention subprocess failed").strip()
                raise RuntimeError(diagnostic[-2_000:])
            progress(90, "artifact", "Validating output alignment, causal deltas, and provenance.")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            _require_sample_metadata(result, index=0)
            intervention = result.get("intervention")
            if not isinstance(intervention, dict):
                raise ValueError("Intervention worker did not produce a comparison artifact.")
            if not isinstance(intervention.get("original"), dict) or not isinstance(
                intervention.get("steered"), dict
            ):
                raise ValueError("Intervention output must contain original and steered results.")
            _require_not_cancelled(cancel_event)
            envelope = {
                "schema_version": "1.0",
                "run": {
                    "run_id": result["runId"],
                    "model_name": result["modelName"],
                    "model_source": result["modelSource"],
                },
                "samples": [result],
                "metrics": sorted(result.get("metricProvenance", {})),
                "artifacts": {"embedded": True, "derived": "contrastive-intervention"},
            }
            result_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
            _require_not_cancelled(cancel_event)
            result_path.replace(final_artifact)
            return result
        finally:
            input_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)

    return run


def _subprocess_sae_discovery_runner(*, root: Path) -> JobRunner:
    script, working_directory = _explorer_worker("run_local_explorer_sae_discovery.py")

    def run(
        payload: SAEFeatureDiscoveryRequest,
        cancel_event: threading.Event,
        progress: JobProgress,
    ) -> dict[str, Any]:
        job_suffix = uuid.uuid4().hex[:10]
        output_dir = root / ".jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        input_path = output_dir / f"{job_suffix}.sae-discovery-input.json"
        result_path = output_dir / f"{job_suffix}.sae-discovery-result.json"
        input_path.write_text(
            json.dumps(
                {
                    "run": payload.run,
                    "request": payload.model_dump(exclude={"run"}),
                }
            ),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(script),
            "--input",
            str(input_path),
            "--output",
            str(result_path),
        ]
        progress(8, "base-model", f"Loading {payload.run['modelName']} for SAE discovery.")
        try:
            process = subprocess.Popen(
                command,
                cwd=working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            progress(35, "sae-encode", "Encoding the selected tokens with Gemma Scope SAE.")
            stdout, stderr = _communicate_cancellable(process, cancel_event)
            _require_not_cancelled(cancel_event)
            if process.returncode != 0:
                diagnostic = (stderr or stdout or "SAE discovery subprocess failed").strip()
                raise RuntimeError(diagnostic[-2_000:])
            progress(90, "feature-metadata", "Validating active features and concept metadata.")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            candidates = result.get("candidates")
            if not isinstance(candidates, list):
                raise ValueError("SAE discovery worker did not return a candidate list.")
            if any(
                not isinstance(candidate, dict)
                or not isinstance(candidate.get("featureIndex"), int)
                or not isinstance(candidate.get("maxActivation"), int | float)
                for candidate in candidates
            ):
                raise ValueError("SAE discovery returned an invalid candidate row.")
            _require_not_cancelled(cancel_event)
            return result
        finally:
            input_path.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)

    return run


def _communicate_cancellable(
    process: subprocess.Popen[str], cancel_event: threading.Event
) -> tuple[str, str]:
    while True:
        try:
            return process.communicate(timeout=0.1)
        except subprocess.TimeoutExpired:
            if not cancel_event.is_set():
                continue
            process.terminate()
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
            raise RuntimeError("Explorer job cancelled") from None


def _render_prompt(
    prompt: str,
    template: str,
    messages: list[PromptMessage] | None = None,
) -> str:
    cleaned = prompt.strip()
    if template != "chat" or not messages:
        return cleaned if template == "plain" else f"User: {cleaned}\nAssistant:"
    history = "\n".join(
        f"{'User' if message.role == 'user' else 'Assistant'}: {message.content.strip()}"
        for message in messages
    )
    return f"{history}\nUser: {cleaned}\nAssistant:"


def _require_not_cancelled(cancel_event: threading.Event) -> None:
    if cancel_event.is_set():
        raise RuntimeError("Prompt job cancelled")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _scan_artifacts(
    root: Path,
    *,
    max_file_bytes: int,
) -> tuple[list[IndexedSample], list[ArtifactDiagnostic]]:
    samples, diagnostics, physical_sources = _scan_physical_manifests(root)
    candidates = sorted(
        _artifact_candidates(root),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    for path in candidates:
        relative_name = path.relative_to(root).as_posix()
        if relative_name in physical_sources:
            continue
        try:
            stat = path.stat()
            size = stat.st_size
            if size > max_file_bytes:
                raise ArtifactReadError(
                    "artifact_too_large",
                    f"{size} bytes exceeds the {max_file_bytes}-byte compact artifact limit",
                )
            run_payloads = _read_artifact_cached(
                str(path),
                stat.st_mtime_ns,
                size,
            )
            modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            artifact_id = hashlib.sha256(relative_name.encode("utf-8")).hexdigest()[:16]
            for sample in run_payloads:
                samples.append(
                    IndexedSample(
                        summary=_sample_summary(
                            sample,
                            artifact_id=artifact_id,
                            source_name=relative_name,
                            modified_at=modified,
                            size_bytes=size,
                        ),
                        payload=sample,
                        physical=None,
                    )
                )
        except (ArtifactReadError, json.JSONDecodeError, OSError, UnicodeError) as exc:
            code = exc.code if isinstance(exc, ArtifactReadError) else "artifact_read_error"
            diagnostics.append(
                ArtifactDiagnostic(sourceName=relative_name, code=code, message=str(exc))
            )
    return samples, diagnostics


@lru_cache(maxsize=64)
def _read_artifact_cached(
    path_text: str,
    _modified_ns: int,
    _size_bytes: int,
) -> tuple[dict[str, Any], ...]:
    payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
    return tuple(_extract_samples(payload))


def _scan_physical_manifests(
    root: Path,
) -> tuple[list[IndexedSample], list[ArtifactDiagnostic], set[str]]:
    samples: list[IndexedSample] = []
    diagnostics: list[ArtifactDiagnostic] = []
    covered_sources: set[str] = set()
    for manifest_path in sorted(_manifest_candidates(root)):
        relative_manifest = manifest_path.relative_to(root).as_posix()
        try:
            stat = manifest_path.stat()
            manifest = _read_manifest_cached(str(manifest_path), stat.st_mtime_ns, stat.st_size)
            if (
                manifest.get("schema_version") != "1.0"
                or manifest.get("protocol") != MANIFEST_PROTOCOL
            ):
                raise ArtifactReadError(
                    "invalid_chunk_manifest", "unsupported physical chunk manifest protocol"
                )
            source = manifest.get("source")
            if not isinstance(source, dict) or not isinstance(source.get("path"), str):
                raise ArtifactReadError("invalid_chunk_manifest", "manifest source is missing")
            source_candidate = manifest_path.parent / source["path"]
            if _path_uses_symlink(source_candidate, manifest_path.parent):
                raise ArtifactReadError(
                    "invalid_chunk_manifest", "manifest source may not be a symlink"
                )
            source_path = source_candidate.resolve(strict=True)
            source_path.relative_to(root)
            if not source_path.is_file():
                raise ArtifactReadError(
                    "invalid_chunk_manifest", "manifest source is not a regular file"
                )
            source_stat = source_path.stat()
            if source_stat.st_size != source.get(
                "sizeBytes"
            ) or source_stat.st_mtime_ns != source.get("mtimeNs"):
                raise ArtifactReadError(
                    "stale_chunk_manifest",
                    "source size or mtime differs; rebuild the physical chunk sidecar",
                )
            source_sha = source.get("sha256")
            if not isinstance(source_sha, str) or len(source_sha) != 64:
                raise ArtifactReadError("invalid_chunk_manifest", "source sha256 is invalid")
            manifest_samples = manifest.get("samples")
            if not isinstance(manifest_samples, list) or not manifest_samples:
                raise ArtifactReadError("invalid_chunk_manifest", "manifest samples are missing")
            relative_source = source_path.relative_to(root).as_posix()
            artifact_id = source_sha[:16]
            modified = datetime.fromtimestamp(source_stat.st_mtime, tz=timezone.utc).isoformat()
            pending: list[IndexedSample] = []
            for index, sample in enumerate(manifest_samples):
                if not isinstance(sample, dict) or not isinstance(sample.get("base"), dict):
                    raise ArtifactReadError(
                        "invalid_chunk_manifest", f"samples[{index}] base is missing"
                    )
                base = sample["base"]
                _require_sample_metadata(base, index=index)
                components = sample.get("components")
                if not isinstance(components, dict):
                    raise ArtifactReadError(
                        "invalid_chunk_manifest", f"samples[{index}] components are missing"
                    )
                pending.append(
                    IndexedSample(
                        summary=_sample_summary(
                            base,
                            artifact_id=artifact_id,
                            source_name=relative_source,
                            modified_at=modified,
                            size_bytes=source_stat.st_size,
                        ),
                        payload=None,
                        physical=PhysicalIndexedSample(
                            manifest_path=manifest_path,
                            source_path=source_path,
                            source_sha256=source_sha,
                            base=base,
                            components=components,
                        ),
                    )
                )
            samples.extend(pending)
            covered_sources.add(relative_source)
        except (ArtifactReadError, json.JSONDecodeError, OSError, UnicodeError, ValueError) as exc:
            code = exc.code if isinstance(exc, ArtifactReadError) else "chunk_manifest_error"
            diagnostics.append(
                ArtifactDiagnostic(sourceName=relative_manifest, code=code, message=str(exc))
            )
    return samples, diagnostics, covered_sources


@lru_cache(maxsize=64)
def _read_manifest_cached(path_text: str, _modified_ns: int, _size_bytes: int) -> dict[str, Any]:
    payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ArtifactReadError("invalid_chunk_manifest", "manifest root must be an object")
    return payload


def _manifest_candidates(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    for candidate in root.rglob("*.explorer.manifest.json"):
        if candidate.is_symlink() or not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            continue
        yield resolved


def _artifact_candidates(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    for candidate in root.rglob("*.explorer.json"):
        if candidate.is_symlink() or not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            continue
        yield resolved


def _extract_samples(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ArtifactReadError("invalid_artifact", "artifact root must be a JSON object")
    if "schema_version" in payload:
        if payload.get("schema_version") != "1.0":
            raise ArtifactReadError(
                "unsupported_schema",
                f"expected schema_version '1.0', received {payload.get('schema_version')!r}",
            )
        samples = payload.get("samples")
        if not isinstance(samples, list) or not samples:
            raise ArtifactReadError(
                "invalid_artifact", "versioned artifact must contain a non-empty samples array"
            )
    else:
        samples = [payload]
    output: list[dict[str, Any]] = []
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise ArtifactReadError("invalid_sample", f"samples[{index}] must be an object")
        _require_sample_metadata(sample, index=index)
        output.append(sample)
    return output


def _require_sample_metadata(sample: dict[str, Any], *, index: int) -> None:
    required = {
        "runId": str,
        "sampleId": str,
        "modelName": str,
        "modelSource": str,
        "tokens": list,
        "layers": list,
    }
    for field_name, field_type in required.items():
        value = sample.get(field_name)
        if not isinstance(value, field_type) or (field_type is str and not value.strip()):
            raise ArtifactReadError(
                "invalid_sample",
                f"samples[{index}].{field_name} must be a non-empty {field_type.__name__}",
            )
    if not sample["tokens"] or not sample["layers"]:
        raise ArtifactReadError(
            "invalid_sample", f"samples[{index}] must contain tokens and layers"
        )


def _sample_summary(
    sample: dict[str, Any],
    *,
    artifact_id: str,
    source_name: str,
    modified_at: str,
    size_bytes: int,
) -> RemoteRunSummary:
    prompt = _sample_user_prompt(sample)
    prompt_preview = " ".join(prompt.split())[:160] if isinstance(prompt, str) else None
    metadata_value = sample.get("metadata")
    metadata: dict[str, Any] = metadata_value if isinstance(metadata_value, dict) else {}
    parent = metadata.get("parentRun")
    parent_run = (
        RemoteParentRun(runId=parent["runId"], sampleId=parent["sampleId"])
        if isinstance(parent, dict)
        and isinstance(parent.get("runId"), str)
        and isinstance(parent.get("sampleId"), str)
        else None
    )
    conversation_id = metadata.get("conversationId")
    turn_index = metadata.get("turnIndex")
    return RemoteRunSummary(
        runId=sample["runId"],
        sampleId=sample["sampleId"],
        modelName=sample["modelName"],
        modelSource=sample["modelSource"],
        tokenCount=len(sample["tokens"]),
        layerCount=len(sample["layers"]),
        artifactId=artifact_id,
        sourceName=source_name,
        modifiedAt=modified_at,
        sizeBytes=size_bytes,
        promptPreview=prompt_preview or None,
        parentRun=parent_run,
        conversationId=conversation_id if isinstance(conversation_id, str) else None,
        turnIndex=(
            turn_index
            if isinstance(turn_index, int) and not isinstance(turn_index, bool) and turn_index >= 0
            else None
        ),
    )


def _sample_user_prompt(sample: dict[str, Any]) -> str | None:
    metadata = sample.get("metadata")
    if isinstance(metadata, dict):
        prompt_runner = metadata.get("promptRunner")
        if isinstance(prompt_runner, dict):
            user_prompt = prompt_runner.get("userPrompt")
            if isinstance(user_prompt, str) and user_prompt.strip():
                return user_prompt.strip()

    prompt = sample.get("prompt")
    if not isinstance(prompt, str):
        return None
    patterns = (
        r"<\|im_start\|>user\n(.*?)<\|im_end\|>",
        r"<start_of_turn>user\n(.*?)<end_of_turn>",
        r"(?:^|\n)User:\s*(.*?)(?=\nAssistant:|\Z)",
    )
    for pattern in patterns:
        matches = re.findall(pattern, prompt, flags=re.DOTALL)
        if matches:
            candidate = matches[-1].strip()
            if candidate:
                return candidate
    return prompt.strip() or None


def _find_indexed_sample(
    root: Path,
    run_id: str,
    sample_id: str,
    *,
    max_file_bytes: int,
) -> IndexedSample:
    samples, _diagnostics = _scan_artifacts(root, max_file_bytes=max_file_bytes)
    for sample in samples:
        if sample.summary.runId == run_id and sample.summary.sampleId == sample_id:
            return sample
    raise HTTPException(
        status_code=404,
        detail={
            "code": "sample_not_found",
            "message": f"No indexed sample matches run={run_id!r}, sample={sample_id!r}.",
        },
    )


def _sample_version_etag(summary: RemoteRunSummary) -> str:
    version = ":".join(
        (
            summary.artifactId,
            summary.modifiedAt,
            str(summary.sizeBytes),
            summary.runId,
            summary.sampleId,
        )
    )
    return f'"{hashlib.sha256(version.encode("utf-8")).hexdigest()}"'


def _chunk_descriptors(payload: dict[str, Any]) -> list[ChunkDescriptor]:
    range_axes: dict[str, Literal["token", "token-square", "token-values", "none"]] = {
        "residualCells": "token",
        "logitLens": "token",
        "jLens": "token",
        "attentionHeads": "token-square",
        "attentionCells": "token",
        "mlpNeurons": "token-values",
        "mlpCells": "token",
        "attributionTracks": "token-values",
        "attributionMethods": "token-values",
        "nla": "token",
        "patching": "token",
        "intervention": "none",
    }
    layer_filters = {
        "residualCells",
        "logitLens",
        "jLens",
        "attentionHeads",
        "attentionCells",
        "mlpNeurons",
        "mlpCells",
        "attributionMethods",
        "nla",
        "patching",
    }
    selector_filters = {
        "attentionHeads",
        "mlpNeurons",
        "attributionTracks",
        "attributionMethods",
        "nla",
    }
    descriptors: list[ChunkDescriptor] = []
    for component in CHUNK_COMPONENTS:
        value = payload.get(component)
        item_count = len(value) if isinstance(value, list) else int(value is not None)
        descriptors.append(
            ChunkDescriptor(
                component=component,
                itemCount=item_count,
                rangeAxis=range_axes[component],
                layerFilter=component in layer_filters,
                selectorFilter=component in selector_filters,
            )
        )
    return descriptors


def _physical_chunk_descriptors(physical: PhysicalIndexedSample) -> list[ChunkDescriptor]:
    descriptors: list[ChunkDescriptor] = []
    for component in CHUNK_COMPONENTS:
        item = physical.components.get(component, {})
        try:
            descriptors.append(
                ChunkDescriptor(
                    component=component,
                    itemCount=int(item.get("itemCount", 0)),
                    rangeAxis=item.get("rangeAxis", "none"),
                    layerFilter=bool(item.get("layerFilter", False)),
                    selectorFilter=bool(item.get("selectorFilter", False)),
                )
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "invalid_chunk_manifest",
                    "message": f"Invalid descriptor for {component}: {exc}",
                },
            ) from exc
    return descriptors


def _full_sample_payload(sample: IndexedSample) -> dict[str, Any]:
    if sample.payload is not None:
        return sample.payload
    assert sample.physical is not None
    stat = sample.physical.source_path.stat()
    for payload in _read_physical_source_cached(
        str(sample.physical.source_path),
        stat.st_mtime_ns,
        stat.st_size,
        sample.physical.source_sha256,
    ):
        if (
            payload.get("runId") == sample.summary.runId
            and payload.get("sampleId") == sample.summary.sampleId
        ):
            return payload
    raise HTTPException(
        status_code=409,
        detail={"code": "physical_source_mismatch", "message": "Source sample is missing."},
    )


_JOB_REQUIRED_COMPONENTS = (
    "attentionHeads",
    "mlpNeurons",
    "residualCells",
    "logitLens",
    "attentionCells",
    "mlpCells",
    "attributionMethods",
)
_JOB_RUN_IDENTITY_FIELDS = (
    "runId",
    "sampleId",
    "modelName",
    "modelSource",
    "prompt",
    "tokens",
    "layers",
)


def _hydrate_workspace_job_payload(
    payload: ModelT,
    *,
    root: Path,
    max_file_bytes: int,
) -> ModelT:
    run = getattr(payload, "run", None)
    if not isinstance(run, dict) or not _job_run_needs_hydration(run):
        return payload
    try:
        indexed = _find_indexed_sample(
            root,
            str(run.get("runId", "")),
            str(run.get("sampleId", "")),
            max_file_bytes=max_file_bytes,
        )
    except HTTPException as exc:
        if exc.status_code == 404:
            return payload
        raise
    full_run = _full_sample_payload(indexed)
    if any(full_run.get(field) != run.get(field) for field in _JOB_RUN_IDENTITY_FIELDS):
        return payload
    return payload.model_copy(update={"run": full_run})


def _job_run_needs_hydration(run: dict[str, Any]) -> bool:
    for component in _JOB_REQUIRED_COMPONENTS:
        rows = run.get(component)
        if not isinstance(rows, list) or not rows:
            return True
        if any(isinstance(row, dict) and row.get("id") == "__chunk_pending__" for row in rows):
            return True
    return False


@lru_cache(maxsize=32)
def _read_physical_source_cached(
    path_text: str,
    _modified_ns: int,
    _size_bytes: int,
    expected_sha256: str,
) -> tuple[dict[str, Any], ...]:
    encoded = Path(path_text).read_bytes()
    actual = hashlib.sha256(encoded).hexdigest()
    if actual != expected_sha256:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "physical_source_checksum_mismatch",
                "message": f"Expected source sha256 {expected_sha256}, received {actual}",
            },
        )
    return tuple(_extract_samples(json.loads(encoded)))


def _sample_chunk_data(
    sample: IndexedSample,
    *,
    root: Path,
    component: ChunkComponent,
    token_start: int,
    token_end: int,
    source_start: int,
    source_end: int,
    layer: int | None,
    selector: str | None,
) -> Any:
    if sample.physical is None:
        assert sample.payload is not None
        return _slice_component(
            sample.payload,
            component,
            token_start=token_start,
            token_end=token_end,
            source_start=source_start,
            source_end=source_end,
            layer=layer,
            selector=selector,
        )
    try:
        descriptor = sample.physical.components.get(component)
        if not isinstance(descriptor, dict) or not isinstance(descriptor.get("blocks"), list):
            raise ArtifactReadError("physical_chunk_missing", f"No blocks for {component}")
        block = next(
            (
                item
                for item in descriptor["blocks"]
                if isinstance(item, dict)
                and item.get("tokenStart", -1) <= token_start
                and item.get("tokenEnd", -1) >= token_end
                and (
                    component != "attentionHeads"
                    or (
                        item.get("sourceStart", -1) <= source_start
                        and item.get("sourceEnd", -1) >= source_end
                    )
                )
            ),
            None,
        )
        if block is None:
            raise ArtifactReadError(
                "physical_chunk_missing",
                f"No physical {component} block covers token range [{token_start}, {token_end})",
            )
        path_text = block.get("path")
        checksum = block.get("sha256")
        size_bytes = block.get("sizeBytes")
        if (
            not isinstance(path_text, str)
            or not isinstance(checksum, str)
            or not isinstance(size_bytes, int)
        ):
            raise ArtifactReadError("invalid_chunk_manifest", "block metadata is invalid")
        block_candidate = sample.physical.manifest_path.parent / path_text
        if _path_uses_symlink(block_candidate, sample.physical.manifest_path.parent):
            raise ArtifactReadError("invalid_chunk_path", "physical block may not be a symlink")
        block_path = block_candidate.resolve(strict=True)
        try:
            block_path.relative_to(root)
        except ValueError as exc:
            raise ArtifactReadError(
                "invalid_chunk_path", "physical block resolves outside the artifact root"
            ) from exc
        if not block_path.is_file():
            raise ArtifactReadError("invalid_chunk_path", "block is not a regular in-root file")
        stat = block_path.stat()
        if stat.st_size != size_bytes:
            raise ArtifactReadError(
                "chunk_size_mismatch", f"Physical block size differs for {path_text}"
            )
        data = _read_physical_block_cached(
            str(block_path), stat.st_mtime_ns, stat.st_size, checksum
        )
        return _slice_physical_block(
            component,
            data,
            block,
            token_start=token_start,
            token_end=token_end,
            source_start=source_start,
            source_end=source_end,
            layer=layer,
            selector=selector,
        )
    except ArtifactReadError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "physical_chunk_error", "message": str(exc)},
        ) from exc


def _path_uses_symlink(path: Path, stop: Path) -> bool:
    current = path
    while True:
        if current.is_symlink():
            return True
        if current == stop or current.parent == current:
            return False
        current = current.parent


@lru_cache(maxsize=256)
def _read_physical_block_cached(
    path_text: str,
    _modified_ns: int,
    _size_bytes: int,
    expected_sha256: str,
) -> Any:
    encoded = Path(path_text).read_bytes()
    actual = hashlib.sha256(encoded).hexdigest()
    if actual != expected_sha256:
        raise ArtifactReadError(
            "chunk_checksum_mismatch",
            f"Expected block sha256 {expected_sha256}, received {actual}",
        )
    return json.loads(encoded)


def _slice_physical_block(
    component: ChunkComponent,
    data: Any,
    block: dict[str, Any],
    *,
    token_start: int,
    token_end: int,
    source_start: int,
    source_end: int,
    layer: int | None,
    selector: str | None,
) -> Any:
    block_start = int(block["tokenStart"])
    if component == "intervention":
        return data
    if component == "patching":
        if not isinstance(data, dict):
            return data
        return {
            **data,
            "cells": _filter_position_rows(
                data.get("cells", []), token_start, token_end, layer=layer
            ),
            "positions": [
                item for item in data.get("positions", []) if token_start <= item < token_end
            ],
            "corruptedTokens": [
                item
                for item in data.get("corruptedTokens", [])
                if token_start <= item.get("index", -1) < token_end
            ],
            "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
        }
    if component in {"residualCells", "logitLens", "jLens", "attentionCells", "mlpCells", "nla"}:
        rows = _filter_position_rows(data, token_start, token_end, layer=layer)
        if component == "nla" and selector is not None:
            rows = [row for row in rows if row.get("component") == selector]
        return rows
    if component == "attentionHeads":
        local_row_start = token_start - block_start
        local_row_end = token_end - block_start
        block_source_start = int(block["sourceStart"])
        local_source_start = source_start - block_source_start
        local_source_end = source_end - block_source_start
        output = []
        for head in _filter_layer_and_selector(data, layer=layer, selector=selector, id_field="id"):
            item = dict(head)
            item["distributionByToken"] = [
                row[local_source_start:local_source_end]
                for row in head.get("distributionByToken", [])[local_row_start:local_row_end]
            ]
            item["chunk"] = {
                "destinationStart": token_start,
                "destinationEnd": token_end,
                "sourceStart": source_start,
                "sourceEnd": source_end,
            }
            output.append(item)
        return output
    local_start = token_start - block_start
    local_end = token_end - block_start
    if component == "mlpNeurons":
        output = []
        for neuron in _filter_layer_and_selector(
            data, layer=layer, selector=selector, id_field="id"
        ):
            item = dict(neuron)
            item["activationsByToken"] = neuron.get("activationsByToken", [])[local_start:local_end]
            item["chunk"] = {"tokenStart": token_start, "tokenEnd": token_end}
            output.append(item)
        return output
    if component == "attributionTracks":
        return [
            {
                **track,
                "values": track.get("values", [])[local_start:local_end],
                "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
            }
            for track in _filter_layer_and_selector(
                data, layer=None, selector=selector, id_field="name"
            )
        ]
    if component == "attributionMethods":
        output = []
        for method in _filter_layer_and_selector(
            data, layer=None, selector=selector, id_field="id"
        ):
            item = dict(method)
            item["rows"] = [
                {
                    **row,
                    "values": row.get("values", [])[local_start:local_end],
                    "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
                }
                for row in method.get("rows", [])
                if layer is None or row.get("layer") == layer
            ]
            output.append(item)
        return output
    raise ArtifactReadError("physical_chunk_error", f"Unsupported component {component}")


def _slice_component(
    payload: dict[str, Any],
    component: ChunkComponent,
    *,
    token_start: int,
    token_end: int,
    source_start: int,
    source_end: int,
    layer: int | None,
    selector: str | None,
) -> Any:
    value = payload.get(component)
    if component == "intervention":
        return value
    if component == "patching":
        if not isinstance(value, dict):
            return value
        result = dict(value)
        result["cells"] = _filter_position_rows(
            value.get("cells", []), token_start, token_end, layer=layer
        )
        result["positions"] = [
            position
            for position in value.get("positions", [])
            if token_start <= position < token_end
        ]
        result["corruptedTokens"] = [
            token
            for token in value.get("corruptedTokens", [])
            if token_start <= token.get("index", -1) < token_end
        ]
        result["chunk"] = {"tokenStart": token_start, "tokenEnd": token_end}
        return result
    if component in {"residualCells", "logitLens", "jLens", "attentionCells", "mlpCells", "nla"}:
        rows = _filter_position_rows(value, token_start, token_end, layer=layer)
        if component == "nla" and selector is not None:
            rows = [row for row in rows if row.get("component") == selector]
        return rows
    if component == "attentionHeads":
        heads = _filter_layer_and_selector(value, layer=layer, selector=selector, id_field="id")
        output = []
        for head in heads:
            item = dict(head)
            matrix = head.get("distributionByToken", [])
            item["distributionByToken"] = [
                row[source_start:source_end] for row in matrix[token_start:token_end]
            ]
            item["chunk"] = {
                "destinationStart": token_start,
                "destinationEnd": token_end,
                "sourceStart": source_start,
                "sourceEnd": source_end,
            }
            output.append(item)
        return output
    if component == "mlpNeurons":
        neurons = _filter_layer_and_selector(value, layer=layer, selector=selector, id_field="id")
        output = []
        for neuron in neurons:
            item = dict(neuron)
            item["activationsByToken"] = neuron.get("activationsByToken", [])[token_start:token_end]
            item["chunk"] = {"tokenStart": token_start, "tokenEnd": token_end}
            output.append(item)
        return output
    if component == "attributionTracks":
        tracks = _filter_layer_and_selector(value, layer=None, selector=selector, id_field="name")
        return [
            {
                **track,
                "values": track.get("values", [])[token_start:token_end],
                "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
            }
            for track in tracks
        ]
    if component == "attributionMethods":
        methods = _filter_layer_and_selector(value, layer=None, selector=selector, id_field="id")
        output = []
        for method in methods:
            item = dict(method)
            item["rows"] = [
                {
                    **row,
                    "values": row.get("values", [])[token_start:token_end],
                    "chunk": {"tokenStart": token_start, "tokenEnd": token_end},
                }
                for row in method.get("rows", [])
                if layer is None or row.get("layer") == layer
            ]
            output.append(item)
        return output
    raise ValueError(f"Unsupported chunk component {component!r}")


def _filter_position_rows(
    value: Any,
    token_start: int,
    token_end: int,
    *,
    layer: int | None,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [
        row
        for row in value
        if isinstance(row, dict)
        and token_start <= row.get("tokenIndex", -1) < token_end
        and (layer is None or row.get("layer") == layer)
    ]


def _filter_layer_and_selector(
    value: Any,
    *,
    layer: int | None,
    selector: str | None,
    id_field: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [
        item
        for item in value
        if isinstance(item, dict)
        and (layer is None or item.get("layer") == layer)
        and (selector is None or item.get(id_field) == selector)
    ]


def _payload_etag(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f'"{hashlib.sha256(encoded).hexdigest()}"'


class ArtifactReadError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def serve_explorer(
    *,
    artifact_root: str | Path = DEFAULT_ARTIFACT_ROOT,
    host: str = DEFAULT_EXPLORER_HOST,
    port: int = DEFAULT_EXPLORER_PORT,
    web_root: str | Path | None = None,
    open_browser: bool = True,
    allow_remote: bool = False,
    log_level: str = "info",
) -> None:
    if host not in LOCAL_EXPLORER_HOSTS and not allow_remote:
        raise ValueError(
            "Non-local Explorer binding requires --allow-remote. "
            "The Explorer has no built-in authentication or TLS."
        )
    root = Path(artifact_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    resolved_web_root = resolve_explorer_web_root(web_root)
    if resolved_web_root is None:
        raise RuntimeError(
            "Built Explorer frontend not found. Run "
            "`python scripts/prepare_explorer_distribution.py` or reinstall SafeLens."
        )
    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{browser_host}:{port}"
    print(f"SafeLens Explorer: {url}")
    print(f"Artifact workspace: {root}")
    if host not in LOCAL_EXPLORER_HOSTS:
        print(
            "WARNING: Explorer is remotely bound without built-in authentication or TLS.",
            file=sys.stderr,
        )
    if open_browser:
        timer = threading.Timer(0.8, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    import uvicorn

    uvicorn.run(
        create_app(root, web_root=resolved_web_root),
        host=host,
        port=port,
        log_level=log_level,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serve the SafeLens Explorer workspace.")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--host", default=DEFAULT_EXPLORER_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_EXPLORER_PORT)
    parser.add_argument("--web-root", type=Path)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow a non-local bind. Explorer does not provide authentication or TLS.",
    )
    parser.add_argument(
        "--log-level",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        default="info",
    )
    args = parser.parse_args(argv)
    try:
        serve_explorer(
            artifact_root=args.artifact_root,
            host=args.host,
            port=args.port,
            web_root=args.web_root,
            open_browser=not args.no_browser,
            allow_remote=args.allow_remote,
            log_level=args.log_level,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
