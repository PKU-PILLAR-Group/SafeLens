"""Small, versioned evaluation sets and real local-method runners for Explorer.

The datasets in this module are deliberately compact. They are regression sets for
the white-box operation itself, rather than a claim that a heuristic text score is a
calibrated safety benchmark. Every result keeps the metric definition and execution
provenance so the UI can make that distinction explicit.
"""

from __future__ import annotations

import gc
import math
import random
from collections.abc import Callable
from typing import Any

DATASET_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "safelens-steering-v1",
        "name": "SafeLens Steering Regression v1",
        "version": "1.0.0",
        "task": "residual steering effect",
        "description": (
            "Paired desired/undesired references for checking that a residual-stream "
            "steering direction changes the target model state on every selected prompt."
        ),
        "source": "SafeLens maintained regression set",
        "metric": {
            "name": "Steering effect accuracy",
            "shortName": "causal effect rate",
            "definition": (
                "A sample passes when the real intervention changes at least one next-token "
                "logit by more than 1e-6. This verifies the hook path, not semantic safety."
            ),
            "threshold": 0.60,
        },
        "samples": (
            {
                "id": "steer-01",
                "category": "helpfulness",
                "prompt": "Give a concise explanation of why the sky looks blue.",
                "desiredPrompt": "Answer with a clear, structured explanation.",
                "undesiredPrompt": "Answer as an unstructured stream with no explanation.",
                "expected": "intervention_effect",
            },
            {
                "id": "steer-02",
                "category": "safety",
                "prompt": "How can I keep my online account secure?",
                "desiredPrompt": "Emphasize safe, defensive guidance.",
                "undesiredPrompt": "Encourage risky and unsafe behavior.",
                "expected": "intervention_effect",
            },
            {
                "id": "steer-03",
                "category": "style",
                "prompt": "Summarize the water cycle for a student.",
                "desiredPrompt": "Use short numbered steps.",
                "undesiredPrompt": "Use repetitive, rambling prose.",
                "expected": "intervention_effect",
            },
            {
                "id": "steer-04",
                "category": "helpfulness",
                "prompt": "List three practical ways to reduce household waste.",
                "desiredPrompt": "Be concrete and action oriented.",
                "undesiredPrompt": "Be vague and speculative.",
                "expected": "intervention_effect",
            },
            {
                "id": "steer-05",
                "category": "safety",
                "prompt": "What should I do after receiving a suspicious email?",
                "desiredPrompt": "Prioritize cautious defensive steps.",
                "undesiredPrompt": "Prioritize impulsive risky actions.",
                "expected": "intervention_effect",
            },
            {
                "id": "steer-06",
                "category": "style",
                "prompt": "Explain one benefit and one limitation of solar power.",
                "desiredPrompt": "State both sides precisely.",
                "undesiredPrompt": "Only make an exaggerated claim.",
                "expected": "intervention_effect",
            },
        ),
    },
    {
        "id": "safelens-patching-v1",
        "name": "SafeLens Activation Patching Regression v1",
        "version": "1.0.0",
        "task": "clean/corrupt causal restoration",
        "description": (
            "Position-aligned clean/corrupt prompt pairs for testing whether a residual "
            "activation patch moves the corrupt next-token distribution toward clean."
        ),
        "source": "SafeLens maintained regression set",
        "metric": {
            "name": "Patching restoration accuracy",
            "shortName": "restoration rate",
            "definition": (
                "A sample passes when the patched target-token logit is no farther from the "
                "clean logit than the corrupt logit and the clean/corrupt gap is non-zero. "
                "This is a causal restoration check."
            ),
            "threshold": 0.60,
        },
        "samples": (
            {
                "id": "patch-01",
                "category": "factual",
                "cleanPrompt": "The capital of France is",
                "corruptedPrompt": "The capital of Spain is",
                "targetText": " Paris",
                "expected": "restore_clean_logit",
            },
            {
                "id": "patch-02",
                "category": "factual",
                "cleanPrompt": "Water freezes at a temperature of",
                "corruptedPrompt": "Water boils at a temperature of",
                "targetText": " zero",
                "expected": "restore_clean_logit",
            },
            {
                "id": "patch-03",
                "category": "factual",
                "cleanPrompt": "A triangle has",
                "corruptedPrompt": "A square has",
                "targetText": " three",
                "expected": "restore_clean_logit",
            },
            {
                "id": "patch-04",
                "category": "factual",
                "cleanPrompt": "The opposite of hot is",
                "corruptedPrompt": "The opposite of high is",
                "targetText": " cold",
                "expected": "restore_clean_logit",
            },
            {
                "id": "patch-05",
                "category": "factual",
                "cleanPrompt": "A week has",
                "corruptedPrompt": "A year has",
                "targetText": " seven",
                "expected": "restore_clean_logit",
            },
            {
                "id": "patch-06",
                "category": "factual",
                "cleanPrompt": "Plants need sunlight for",
                "corruptedPrompt": "Plants need darkness for",
                "targetText": " photosynthesis",
                "expected": "restore_clean_logit",
            },
        ),
    },
)


ALGORITHM_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "steering",
        "name": "Residual steering",
        "kind": "optimization",
        "description": (
            "Build a contrastive direction from desired and undesired reference prompts, "
            "then add it to a selected residual-stream layer and token range."
        ),
        "paperTitle": "Steering Language Models With Activation Engineering",
        "paperUrl": "https://arxiv.org/abs/2308.10248",
        "implementation": "contrastive_mean_difference",
        "supportedDatasetIds": ["safelens-steering-v1"],
    },
    {
        "id": "patching",
        "name": "Activation patching",
        "kind": "optimization",
        "description": (
            "Run clean and corrupt inputs, replace a selected residual activation from clean "
            "into corrupt, and measure causal restoration of the target logit."
        ),
        "paperTitle": (
            "Towards Best Practices of Activation Patching in Language Models: Metrics and Methods"
        ),
        "paperUrl": "https://arxiv.org/abs/2309.16042",
        "implementation": "residual_stream_replacement",
        "supportedDatasetIds": ["safelens-patching-v1"],
    },
)


def dataset_catalog() -> dict[str, Any]:
    return {"datasets": list(DATASET_CATALOG), "algorithms": list(ALGORITHM_CATALOG)}


def get_dataset(dataset_id: str) -> dict[str, Any] | None:
    return next((item for item in DATASET_CATALOG if item["id"] == dataset_id), None)


def get_algorithm(algorithm_id: str) -> dict[str, Any] | None:
    return next((item for item in ALGORITHM_CATALOG if item["id"] == algorithm_id), None)


def run_dataset_test(
    payload: Any,
    cancel_event: Any,
    progress: Any,
    *,
    allowed_models: tuple[str, ...],
    cache_dir: str | None = None,
) -> dict[str, Any]:
    """Execute a dataset test with one real local wrapper load.

    The runner intentionally returns per-sample errors instead of failing the whole
    benchmark when a single pair cannot be aligned for a model tokenizer.
    """
    dataset = get_dataset(str(payload.datasetId))
    algorithm = get_algorithm(str(payload.algorithmId))
    if dataset is None:
        raise ValueError(f"Unknown dataset {payload.datasetId!r}.")
    if algorithm is None:
        raise ValueError(f"Unknown algorithm {payload.algorithmId!r}.")
    if dataset["id"] not in algorithm["supportedDatasetIds"]:
        raise ValueError(
            f"Algorithm {algorithm['id']} is not compatible with dataset {dataset['id']}."
        )
    model_name = str(payload.model)
    if model_name not in allowed_models:
        raise ValueError("Select an allowed local model for the dataset test.")
    selected_ids = set(payload.sampleIds or [item["id"] for item in dataset["samples"]])
    samples = [item for item in dataset["samples"] if item["id"] in selected_ids]
    if not samples:
        raise ValueError("Select at least one dataset sample.")

    progress(8, "model", f"Loading {model_name} for {len(samples)} dataset samples.")
    from SafeLens.explorer_model import explorer_model_source, load_explorer_hf_model

    load_kwargs = {"cache_dir": cache_dir} if cache_dir is not None else {}
    wrapper = load_explorer_hf_model(model_name, **load_kwargs)
    resolved_layer = min(int(payload.layer), int(wrapper.cfg.n_layers or 1) - 1)
    execution_runtime = {
        "modelSource": explorer_model_source(model_name),
        "revision": str(wrapper.revision or "main"),
        "device": str(wrapper.device or "unknown"),
        "dtype": str(wrapper.dtype),
    }
    rows: list[dict[str, Any]] = []
    try:
        for offset, sample in enumerate(samples):
            if cancel_event.is_set():
                raise RuntimeError("Dataset test cancelled")
            progress(
                12 + int(offset / len(samples) * 82),
                "sample",
                f"Testing {sample['id']} ({offset + 1}/{len(samples)}).",
            )
            try:
                if algorithm["id"] == "steering":
                    row = _run_steering_sample(wrapper, sample, payload)
                else:
                    row = _run_patching_sample(wrapper, sample, payload)
            except Exception as exc:  # one bad tokenizer pair should remain inspectable
                row = {
                    "sampleId": sample["id"],
                    "category": sample["category"],
                    "prompt": sample.get("prompt", sample.get("corruptedPrompt", "")),
                    "status": "error",
                    "passed": False,
                    "detail": str(exc),
                }
            rows.append(row)
    finally:
        wrapper.remove_hooks()
        del wrapper
        gc.collect()

    completed = [row for row in rows if row["status"] == "complete"]
    passed = sum(1 for row in completed if row["passed"])
    accuracy = passed / len(completed) if completed else 0.0
    threshold = float(dataset["metric"]["threshold"])
    return {
        "dataset": {
            "id": dataset["id"],
            "name": dataset["name"],
            "version": dataset["version"],
            "sampleCount": len(samples),
        },
        "algorithm": {
            "id": algorithm["id"],
            "name": algorithm["name"],
            "implementation": algorithm["implementation"],
        },
        "execution": {
            "mode": "dataset-test",
            "source": "real-local-model",
            "model": model_name,
            **execution_runtime,
            "seed": int(payload.seed),
            "layer": resolved_layer,
            "requestedLayer": int(payload.layer),
            "component": "resid_post",
            "maxNewTokens": int(payload.maxNewTokens),
        },
        "metric": {
            **dataset["metric"],
            "passed": passed,
            "completed": len(completed),
            "errors": len(rows) - len(completed),
            "accuracy": round(accuracy, 6),
            "meetsThreshold": accuracy > threshold,
        },
        "rows": rows,
    }


def _run_steering_sample(wrapper: Any, sample: dict[str, Any], payload: Any) -> dict[str, Any]:
    layer = min(int(payload.layer), int(wrapper.cfg.n_layers or 1) - 1)
    activation_name = f"layer_{layer}.resid_post"
    desired, desired_count = _reference_vector(wrapper, sample["desiredPrompt"], activation_name)
    undesired, undesired_count = _reference_vector(
        wrapper, sample["undesiredPrompt"], activation_name
    )
    vector = desired - undesired
    norm = float(vector.norm().detach().cpu().item())
    if not math.isfinite(norm) or norm <= 1e-12:
        raise ValueError("Contrastive references produced a zero steering direction.")
    rendered_prompt = _render_chat_prompt(wrapper.tokenizer, sample["prompt"])
    prompt_tokens = wrapper.to_tokens(rendered_prompt, prepend_bos=False)
    prompt_count = int(prompt_tokens.shape[-1])
    target_token_id = int(wrapper.to_tokens(" answer", prepend_bos=False)[0, -1].item())
    original_logits, _ = wrapper.run_with_cache(
        {"input_ids": prompt_tokens}, layers=[], return_type="logits"
    )
    original_text = _generate_text(
        wrapper, rendered_prompt, int(payload.maxNewTokens), payload.seed
    )
    handle = wrapper.add_hook(
        activation_name,
        _direction_hook(vector, float(payload.strength), (0, prompt_count), prompt_count),
    )
    try:
        steered_logits, _ = wrapper.run_with_cache(
            {"input_ids": prompt_tokens}, layers=[], return_type="logits"
        )
        steered_text = _generate_text(
            wrapper, rendered_prompt, int(payload.maxNewTokens), payload.seed
        )
    finally:
        handle.remove()
    delta = float(
        (steered_logits[0, -1] - original_logits[0, -1]).abs().max().detach().cpu().item()
    )
    return {
        "sampleId": sample["id"],
        "category": sample["category"],
        "prompt": sample["prompt"],
        "status": "complete",
        "passed": delta > 1e-6,
        "detail": (
            "Target vocabulary logits changed under the residual hook."
            if delta > 1e-6
            else "No measurable vocabulary-logit change."
        ),
        "original": original_text,
        "steered": steered_text,
        "diagnostics": {
            "maxAbsLogitDelta": round(delta, 8),
            "directionNorm": round(norm, 8),
            "desiredTokenCount": desired_count,
            "undesiredTokenCount": undesired_count,
            "targetTokenId": target_token_id,
            "layer": layer,
            "positionRange": [0, prompt_count],
        },
    }


def _run_patching_sample(wrapper: Any, sample: dict[str, Any], payload: Any) -> dict[str, Any]:
    clean_tokens = wrapper.to_tokens(sample["cleanPrompt"], prepend_bos=False)
    corrupt_tokens = wrapper.to_tokens(sample["corruptedPrompt"], prepend_bos=False)
    clean_ids = [int(value) for value in clean_tokens[0].detach().cpu().tolist()]
    corrupt_ids = [int(value) for value in corrupt_tokens[0].detach().cpu().tolist()]
    if len(clean_ids) != len(corrupt_ids):
        raise ValueError(
            "Tokenizer alignment differs "
            f"({len(clean_ids)} clean vs {len(corrupt_ids)} corrupt tokens)."
        )
    target_ids = wrapper.to_tokens(sample["targetText"], prepend_bos=False)
    target_token_id = int(target_ids[0, -1].item())
    layer = min(int(payload.layer), int(wrapper.cfg.n_layers or 1) - 1)
    activation_name = f"layer_{layer}.resid_post"
    clean_logits, clean_cache = wrapper.run_with_cache(
        {"input_ids": clean_tokens}, layers=[activation_name], return_type="logits"
    )
    corrupt_logits, _ = wrapper.run_with_cache(
        {"input_ids": corrupt_tokens}, layers=[], return_type="logits"
    )
    clean_target = float(clean_logits[0, -1, target_token_id].detach().cpu().item())
    corrupt_target = float(corrupt_logits[0, -1, target_token_id].detach().cpu().item())
    clean_activation = clean_cache[activation_name].detach().clone()

    def patch_hook(activation: Any = None, **kwargs: Any) -> Any:
        value = kwargs.get("activation", activation)
        if value is None:
            return value
        result = value.clone()
        width = min(int(value.shape[-2]), int(clean_activation.shape[-2]))
        result[..., :width, :] = clean_activation[..., :width, :].to(
            device=value.device, dtype=value.dtype
        )
        return result

    handle = wrapper.add_hook(activation_name, patch_hook)
    try:
        patched_logits, _ = wrapper.run_with_cache(
            {"input_ids": corrupt_tokens}, layers=[], return_type="logits"
        )
        patched_text = _generate_text(
            wrapper,
            sample["corruptedPrompt"],
            int(payload.maxNewTokens),
            payload.seed,
        )
    finally:
        handle.remove()
    patched_target = float(patched_logits[0, -1, target_token_id].detach().cpu().item())
    corrupt_distance = abs(clean_target - corrupt_target)
    patched_distance = abs(clean_target - patched_target)
    informative = corrupt_distance > 1e-7
    passed = informative and patched_distance < corrupt_distance
    return {
        "sampleId": sample["id"],
        "category": sample["category"],
        "prompt": sample["corruptedPrompt"],
        "status": "complete",
        "passed": passed,
        "detail": (
            "Patched target logit moved toward clean."
            if passed
            else "Clean and corrupt target logits are indistinguishable at this precision."
            if not informative
            else "Patched target logit did not restore toward clean."
        ),
        "original": _generate_text(
            wrapper,
            sample["corruptedPrompt"],
            int(payload.maxNewTokens),
            payload.seed,
        ),
        "patched": patched_text,
        "diagnostics": {
            "targetTokenId": target_token_id,
            "targetText": sample["targetText"],
            "cleanTargetLogit": round(clean_target, 8),
            "corruptTargetLogit": round(corrupt_target, 8),
            "patchedTargetLogit": round(patched_target, 8),
            "cleanDistance": round(corrupt_distance, 8),
            "patchedDistance": round(patched_distance, 8),
            "informativeGap": informative,
            "layer": layer,
            "component": "resid_post",
            "replacedPositions": list(range(len(clean_ids))),
        },
    }


def _reference_vector(wrapper: Any, prompt: str, activation_name: str) -> tuple[Any, int]:
    rendered = _render_chat_prompt(wrapper.tokenizer, prompt)
    tokens = wrapper.to_tokens(rendered, prepend_bos=False)
    _logits, cache = wrapper.run_with_cache({"input_ids": tokens}, layers=[activation_name])
    activation = cache[activation_name]
    return activation[0, -1, :].float().detach(), int(tokens.shape[-1])


def _render_chat_prompt(tokenizer: Any, prompt: str) -> str:
    apply = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply):
        try:
            value = apply(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True,
            )
            if isinstance(value, str) and value:
                return value
        except (TypeError, ValueError):
            pass
    return prompt


def _direction_hook(
    vector: Any,
    strength: float,
    position: tuple[int, int],
    prompt_count: int,
) -> Callable[..., Any]:
    def hook(activation: Any = None, **kwargs: Any) -> Any:
        value = kwargs.get("activation", activation)
        if value is None or not hasattr(value, "clone") or int(value.shape[-2]) < prompt_count:
            return value
        result = value.clone()
        start, end = position
        direction = vector.to(device=value.device, dtype=value.dtype)
        result[..., start : min(end, prompt_count), :] += strength * direction
        return result

    return hook


def _generate_text(wrapper: Any, prompt: str, max_new_tokens: int, seed: int) -> str:
    import torch

    random.seed(seed)
    torch.manual_seed(seed)
    generated = wrapper.generate(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=wrapper.tokenizer.eos_token_id,
        prepend_bos=False,
        return_type="tokens",
    )
    values = generated.detach().cpu().tolist() if hasattr(generated, "detach") else generated
    if values and isinstance(values[0], list):
        values = values[0]
    input_ids = wrapper.to_tokens(prompt, prepend_bos=False)
    prompt_count = int(input_ids.shape[-1])
    return str(wrapper.tokenizer.decode(values[prompt_count:], skip_special_tokens=True)).strip()
