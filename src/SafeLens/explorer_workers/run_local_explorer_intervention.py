from __future__ import annotations

# ruff: noqa: E402
import argparse
import difflib
import gc
import json
import math
import random
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.explorer_model import load_explorer_hf_model
from SafeLens.explorer_sae import explorer_sae_converter, neuronpedia_feature_info
from SafeLens.sae_profiles import get_sae_profile
from SafeLens.utils import HuggingFaceModelWrapper

RISK_TERMS = ("jail", "break", "attack", "harm", "weapon", "malware", "bypass", "exploit")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a contrastive steering intervention.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    run = payload["run"]
    request = payload["request"]
    wrapper = load_explorer_hf_model(str(run["modelName"]))
    sae: Any | None = None
    try:
        prompt_tokens = wrapper.to_tokens(str(run["prompt"]), prepend_bos=False)
        prompt_ids = _flat_token_ids(prompt_tokens)
        expected_ids = [int(token["tokenId"]) for token in run["tokens"]]
        if prompt_ids != expected_ids:
            raise ValueError("Source prompt token IDs no longer match the Explorer artifact.")

        mode = str(request.get("mode", "direction"))
        requested_layer = int(request["layer"])
        source_layer = _optional_layer(request.get("sourceLayer"), requested_layer)
        inject_layer = _optional_layer(request.get("injectLayer"), requested_layer)
        source_activation_name = f"layer_{source_layer}.{request['component']}"
        inject_activation_name = f"layer_{inject_layer}.{request['component']}"
        activation_name = inject_activation_name
        feature: dict[str, Any] | None = None
        if mode == "neuron":
            selected = next(
                (
                    item for item in run.get("mlpNeurons", [])
                    if isinstance(item, dict)
                    and int(item.get("layer", -1)) == int(request["layer"])
                    and int(item.get("neuron", -1)) == int(request.get("neuron", -1))
                ),
                None,
            )
            if selected is None:
                raise ValueError("Selected MLP neuron is not available in the source run.")
            source_layer = requested_layer
            inject_layer = requested_layer
            source_activation_name = f"layer_{requested_layer}.post"
            inject_activation_name = source_activation_name
            activation_name = inject_activation_name
            factor = float(request["scale"])
            baseline_activation = selected.get(
                "maxAbsoluteActivation", selected.get("activation", 0.0)
            )
            feature = {
                "kind": "mlp_neuron",
                "id": str(selected.get("id", f"L{request['layer']}N{request['neuron']}")),
                "label": str(selected.get("label", "MLP neuron")),
                "layer": int(request["layer"]),
                "neuron": int(request["neuron"]),
                "baselineActivation": float(baseline_activation or 0.0),
                "operation": _neuron_operation(factor),
            }
        elif mode == "sae_feature":
            profile = get_sae_profile(
                model_name=str(run["modelName"]),
                release=str(request.get("saeRelease", "")),
                sae_id=str(request.get("saeId", "")),
            )
            if profile is None:
                raise ValueError(
                    "Model, release, and SAE ID are not an enabled Gemma Scope profile."
                )
            if int(request["layer"]) != profile.layer or request["component"] != profile.component:
                raise ValueError("Gemma Scope profile does not match the requested layer and site.")
            source_layer = profile.layer
            inject_layer = profile.layer
            activation_name = f"layer_{profile.layer}.{profile.component}"
            source_activation_name = activation_name
            inject_activation_name = activation_name
            sae = _load_sae(
                wrapper,
                release=profile.release,
                sae_id=profile.sae_id,
                expected_model_name=profile.model_name,
            )
            feature_index = int(request.get("featureIndex", -1))
            feature_width = _sae_feature_width(sae)
            if feature_index < 0 or feature_index >= feature_width:
                raise ValueError(
                    f"SAE feature {feature_index} is outside dictionary width {feature_width}."
                )
            feature_stats = _source_sae_feature_stats(
                wrapper,
                sae,
                str(run["prompt"]),
                activation_name,
                feature_index=feature_index,
                position=(int(request["positionStart"]), int(request["positionEnd"])),
            )
            concept = neuronpedia_feature_info(
                model_name=profile.model_name,
                layer=profile.layer,
                sae_id=profile.sae_id,
                feature_index=feature_index,
            )
            operation = str(request.get("saeOperation", "add"))
            if operation not in {"add", "ablate"}:
                raise ValueError(f"Unsupported SAE feature operation: {operation!r}.")
            feature = {
                "kind": "sae_feature",
                "id": f"F{feature_index}",
                "label": concept["label"],
                "layer": profile.layer,
                "featureIndex": feature_index,
                "baselineActivation": feature_stats["maxActivation"],
                "meanActivation": feature_stats["meanActivation"],
                "activeTokenCount": feature_stats["activeTokenCount"],
                "operation": operation,
                "release": profile.release,
                "saeId": profile.sae_id,
                "width": feature_width,
                "architecture": profile.architecture,
                "source": profile.source,
                "conceptLabel": concept["label"] if concept["source"] == "neuronpedia" else None,
                "conceptSource": concept["source"],
                "conceptUrl": concept["url"],
                "positiveTokens": concept["positiveTokens"],
                "negativeTokens": concept["negativeTokens"],
            }
        else:
            positive_prompts = _request_prompt_batch(
                request, "positivePrompts", "desiredPrompt"
            )
            negative_prompts = _request_prompt_batch(
                request, "negativePrompts", "undesiredPrompt"
            )
            activation_reduce = str(request.get("activationReduce", "last_token"))
            desired_vector, desired_token_counts, reference_template = _reference_centroid(
                wrapper,
                positive_prompts,
                source_activation_name,
                activation_reduce=activation_reduce,
            )
            undesired_vector, undesired_token_counts, _ = _reference_centroid(
                wrapper,
                negative_prompts,
                source_activation_name,
                activation_reduce=activation_reduce,
            )
            vector, raw_norm = _contrastive_direction(desired_vector, undesired_vector)
            source_activation_norm = _source_activation_norm(
                wrapper,
                str(run["prompt"]),
                inject_activation_name,
                position=(int(request["positionStart"]), int(request["positionEnd"])),
            )
        position = (int(request["positionStart"]), int(request["positionEnd"]))
        original, original_logits = _run_condition(
            wrapper,
            prompt=str(run["prompt"]),
            prompt_token_count=len(prompt_ids),
            target_token_id=int(request["targetTokenId"]),
            seed=int(request["seed"]),
            max_new_tokens=int(request["maxNewTokens"]),
            temperature=float(request["temperature"]),
        )
        if mode in {"neuron", "sae_feature"}:
            if mode == "neuron":
                hook = _make_neuron_hook(
                    neuron=int(request["neuron"]),
                    factor=float(request["scale"]),
                    position=position,
                    prompt_token_count=len(prompt_ids),
                )
            else:
                if sae is None:
                    raise RuntimeError("Gemma Scope SAE was not loaded.")
                hook = _make_sae_feature_hook(
                    sae=sae,
                    feature_index=int(request["featureIndex"]),
                    operation=str(request.get("saeOperation", "add")),
                    scale=float(request["scale"]),
                    position=position,
                    prompt_token_count=len(prompt_ids),
                )
            handle = wrapper.add_hook(activation_name, hook)
            try:
                steered, steered_logits = _run_condition(
                    wrapper,
                    prompt=str(run["prompt"]),
                    prompt_token_count=len(prompt_ids),
                    target_token_id=int(request["targetTokenId"]),
                    seed=int(request["seed"]),
                    max_new_tokens=int(request["maxNewTokens"]),
                    temperature=float(request["temperature"]),
                )
            finally:
                handle.remove()
        else:
            steered, steered_logits = _run_condition(
                wrapper,
                prompt=str(run["prompt"]),
                prompt_token_count=len(prompt_ids),
                target_token_id=int(request["targetTokenId"]),
                seed=int(request["seed"]),
                max_new_tokens=int(request["maxNewTokens"]),
                temperature=float(request["temperature"]),
                generation_hook=(
                    inject_activation_name,
                    _make_generation_direction_hook(
                        vector=vector,
                        scale=float(request["scale"]),
                    ),
                ),
            )

        target_text = str(
            wrapper.tokenizer.decode(
                [int(request["targetTokenId"])],
                clean_up_tokenization_spaces=False,
            )
        )
        comparison = {
            "mode": mode,
            **({"feature": feature} if feature is not None else {}),
            "vector": {
                "algorithmVersion": "3.0",
                "method": _intervention_method(mode, request),
                "desiredPrompt": str(request["desiredPrompt"]),
                "undesiredPrompt": str(request["undesiredPrompt"]),
                **(
                    {
                        "positivePrompts": positive_prompts,
                        "negativePrompts": negative_prompts,
                        "positiveCount": len(positive_prompts),
                        "negativeCount": len(negative_prompts),
                    }
                    if mode == "direction"
                    else {}
                ),
                "activationReduce": (
                    "selected_neuron"
                    if mode == "neuron"
                    else f"sae_feature_{request['featureIndex']}"
                    if mode == "sae_feature"
                    else activation_reduce
                ),
                "rawNorm": round(
                    _feature_reference_norm(feature, sae)
                    if feature is not None
                    else raw_norm,
                    10,
                ),
                "normalized": False,
                "dimension": (
                    1
                    if mode == "neuron"
                    else int(_sae_decoder_direction(sae, int(request["featureIndex"])).shape[-1])
                    if mode == "sae_feature" and sae is not None
                    else int(vector.shape[-1])
                ),
                "sourceKey": source_activation_name if mode == "direction" else activation_name,
                **(
                    {
                        "referenceTemplate": reference_template,
                        "injectionKey": inject_activation_name,
                        "injectionPhase": "generation",
                        "desiredTokenCount": desired_token_counts[0],
                        "undesiredTokenCount": undesired_token_counts[0],
                        "sourceActivationNorm": round(source_activation_norm, 10),
                        "appliedVectorNorm": round(abs(float(request["scale"])) * raw_norm, 10),
                        "relativeStrength": round(
                            abs(float(request["scale"])) * raw_norm
                            / max(source_activation_norm, 1e-12),
                            10,
                        ),
                    }
                    if mode == "direction"
                    else {}
                ),
            },
            "layer": inject_layer,
            "sourceLayer": source_layer,
            "injectLayer": inject_layer,
            "component": str(request["component"]),
            "scale": float(request["scale"]),
            "positionStart": position[0],
            "positionEnd": position[1],
            "targetTokenId": int(request["targetTokenId"]),
            "targetTokenText": target_text,
            "seed": int(request["seed"]),
            "maxNewTokens": int(request["maxNewTokens"]),
            "temperature": float(request["temperature"]),
            "original": original,
            "steered": steered,
            "deltas": {
                "targetLogit": round(steered["targetLogit"] - original["targetLogit"], 10),
                "lexicalRisk": round(steered["lexicalRisk"] - original["lexicalRisk"], 8),
                "tokenEditDistance": _levenshtein(original["tokenIds"], steered["tokenIds"]),
                "generationChanged": original["tokenIds"] != steered["tokenIds"],
                "firstDivergenceIndex": _first_divergence_index(
                    original["tokenIds"], steered["tokenIds"]
                ),
                **(
                    {
                        "directionProjectionDelta": round(
                            float(request["scale"]) * raw_norm, 10
                        )
                    }
                    if mode == "direction"
                    else {
                        "featureActivationDelta": (
                            round(float(request["scale"]), 10)
                            if str(request.get("saeOperation", "add")) == "add"
                            else round(-float(feature["meanActivation"]), 10)
                        )
                    }
                    if mode == "sae_feature" and feature is not None
                    else {}
                ),
                **_logit_delta_summary(original_logits, steered_logits),
                "probeScore": None,
                "probeReason": (
                    "No trained probe was configured for this Explorer intervention job."
                ),
            },
            "diff": _diff_rows(original["tokenIds"], steered["tokenIds"]),
            "sourceRun": {"runId": run["runId"], "sampleId": run["sampleId"]},
        }
        derived = _merge_intervention_result(run, comparison, run_id=args.run_id)
    finally:
        wrapper.remove_hooks()
        if sae is not None:
            del sae
        del wrapper
        gc.collect()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(derived, indent=2), encoding="utf-8")


def _load_sae(
    wrapper: HuggingFaceModelWrapper,
    *,
    release: str,
    sae_id: str,
    expected_model_name: str,
) -> Any:
    try:
        from sae_lens import SAE
    except ImportError as exc:
        raise RuntimeError(
            "SAE Lens is required for Gemma Scope interventions. Install SafeLens with "
            "`pip install -e '.[sae]'`."
        ) from exc

    model = getattr(wrapper, "model", None)
    if model is None:
        raise RuntimeError("The base model must be loaded before the Gemma Scope SAE.")
    try:
        model_device = str(next(model.parameters()).device)
    except (AttributeError, StopIteration) as exc:
        raise RuntimeError("Could not determine the base model device for SAE loading.") from exc
    loaded = SAE.from_pretrained(
        release=release,
        sae_id=sae_id,
        device=model_device,
        converter=explorer_sae_converter(release),
    )
    sae = loaded[0] if isinstance(loaded, tuple) else loaded
    metadata = getattr(getattr(sae, "cfg", None), "metadata", None)
    recorded_model = getattr(metadata, "model_name", None) or getattr(
        getattr(sae, "cfg", None), "model_name", None
    )
    if recorded_model and str(recorded_model) != expected_model_name:
        raise ValueError(
            f"SAE was trained for {recorded_model}, not {expected_model_name}."
        )
    if not callable(getattr(sae, "encode", None)) or not callable(getattr(sae, "decode", None)):
        raise TypeError("Loaded Gemma Scope object does not expose SAE encode/decode methods.")
    _sae_feature_width(sae)
    return sae


def _sae_decoder_direction(sae: Any, feature_index: int) -> Any:
    decoder = getattr(sae, "W_dec", None)
    if decoder is None or getattr(decoder, "ndim", 0) != 2:
        raise ValueError("Loaded SAE does not expose a two-dimensional decoder matrix.")
    if feature_index < 0 or feature_index >= int(decoder.shape[0]):
        raise ValueError(
            f"SAE feature {feature_index} is outside dictionary width {decoder.shape[0]}."
        )
    return decoder[feature_index]


def _sae_feature_width(sae: Any) -> int:
    decoder = getattr(sae, "W_dec", None)
    if decoder is None or getattr(decoder, "ndim", 0) != 2:
        raise ValueError("Loaded SAE does not expose a two-dimensional decoder matrix.")
    return int(decoder.shape[0])


def _sae_dtype(sae: Any) -> Any:
    try:
        return next(sae.parameters()).dtype
    except (AttributeError, StopIteration):
        return getattr(sae.W_dec, "dtype", None)


def _source_sae_feature_stats(
    wrapper: HuggingFaceModelWrapper,
    sae: Any,
    prompt: str,
    activation_name: str,
    *,
    feature_index: int,
    position: tuple[int, int],
) -> dict[str, float | int]:
    import torch

    tokens = wrapper.to_tokens(prompt, prepend_bos=False)
    _output, cache = wrapper.run_with_cache(
        {"input_ids": tokens},
        layers=[activation_name],
    )
    activation = cache[activation_name]
    start, end = position
    selected = activation[:, start:min(end, activation.shape[-2]), :]
    if selected.numel() == 0:
        raise ValueError("SAE position range did not select any source activations.")
    decoder = _sae_decoder_direction(sae, feature_index)
    if int(selected.shape[-1]) != int(decoder.shape[-1]):
        raise ValueError(
            "SAE input width does not match the selected base-model residual stream: "
            f"{decoder.shape[-1]} != {selected.shape[-1]}."
        )
    with torch.no_grad():
        encoded = sae.encode(
            selected.to(device=decoder.device, dtype=_sae_dtype(sae))
        )[..., feature_index]
    values = encoded.float().detach().cpu()
    return {
        "maxActivation": float(values.max().item()),
        "meanActivation": float(values.mean().item()),
        "activeTokenCount": int((values > 0).sum().item()),
    }


def _make_sae_feature_hook(
    *,
    sae: Any,
    feature_index: int,
    operation: str,
    scale: float,
    position: tuple[int, int],
    prompt_token_count: int,
) -> Callable[..., Any]:
    import torch

    if operation not in {"add", "ablate"}:
        raise ValueError(f"Unsupported SAE feature operation: {operation!r}.")
    decoder = _sae_decoder_direction(sae, feature_index)

    def hook(activation: Any = None, **kwargs: Any) -> Any:
        value = kwargs.get("activation", activation)
        if value is None or not hasattr(value, "clone") or getattr(value, "ndim", 0) < 2:
            return value
        sequence_length = int(value.shape[-2])
        if sequence_length < prompt_token_count:
            return value
        start, end = position
        bounded_end = min(end, sequence_length, prompt_token_count)
        if start >= bounded_end:
            return value
        result = value.clone()
        selected = (
            value[:, start:bounded_end, :]
            if value.ndim >= 3
            else value[start:bounded_end, :]
        )
        if int(selected.shape[-1]) != int(decoder.shape[-1]):
            raise ValueError(
                "SAE decoder width does not match the hooked residual activation: "
                f"{decoder.shape[-1]} != {selected.shape[-1]}."
            )
        with torch.no_grad():
            sae_input = selected.to(device=decoder.device, dtype=_sae_dtype(sae))
            original_features = sae.encode(sae_input)
            modified_features = original_features.clone()
            if operation == "ablate":
                modified_features[..., feature_index] = 0
            else:
                modified_features[..., feature_index] += scale
            residual_delta = sae.decode(modified_features) - sae.decode(original_features)
        delta = residual_delta.to(device=value.device, dtype=value.dtype)
        if value.ndim >= 3:
            result[:, start:bounded_end, :] += delta
        else:
            result[start:bounded_end, :] += delta
        return result

    return hook


def _feature_reference_norm(feature: dict[str, Any], sae: Any | None) -> float:
    if feature.get("kind") == "sae_feature" and sae is not None:
        direction = _sae_decoder_direction(sae, int(feature["featureIndex"]))
        return max(float(direction.float().norm().detach().cpu().item()), 1e-12)
    return max(abs(float(feature["baselineActivation"])), 1e-12)


def _intervention_method(mode: str, request: dict[str, Any]) -> str:
    if mode == "neuron":
        return "mlp_neuron_activation_scaling"
    if mode == "sae_feature":
        operation = str(request.get("saeOperation", "add"))
        return f"gemma_scope_sae_feature_{operation}"
    return "contrastive_mean_difference"


def _reference_vector(
    wrapper: HuggingFaceModelWrapper,
    prompt: str,
    activation_name: str,
    *,
    activation_reduce: str = "last_token",
) -> tuple[Any, int, str]:
    rendered_prompt, template = _render_reference_prompt(wrapper.tokenizer, prompt)
    tokens = wrapper.to_tokens(rendered_prompt, prepend_bos=False)
    _output, cache = wrapper.run_with_cache(
        {"input_ids": tokens},
        layers=[activation_name],
    )
    activation = cache[activation_name]
    if activation.ndim < 2:
        raise ValueError(f"Steering activation {activation_name} must include a model dimension.")
    return (
        _reduce_reference_activation(activation, activation_reduce),
        len(_flat_token_ids(tokens)),
        template,
    )


def _reduce_reference_activation(activation: Any, activation_reduce: str) -> Any:
    if activation_reduce == "last_token":
        return activation[0, -1, :].float().detach()
    if activation_reduce == "mean":
        return activation[0, :, :].float().mean(dim=0).detach()
    raise ValueError(f"Unsupported sample activation reduction: {activation_reduce}")


def _reference_centroid(
    wrapper: HuggingFaceModelWrapper,
    prompts: list[str],
    activation_name: str,
    *,
    activation_reduce: str,
) -> tuple[Any, list[int], str]:
    import torch

    vectors = []
    token_counts = []
    reference_template = "plain"
    for prompt in prompts:
        vector, token_count, template = _reference_vector(
            wrapper,
            prompt,
            activation_name,
            activation_reduce=activation_reduce,
        )
        vectors.append(vector)
        token_counts.append(token_count)
        reference_template = template
    return torch.stack(vectors, dim=0).mean(dim=0), token_counts, reference_template


def _request_prompt_batch(
    request: dict[str, Any], batch_key: str, legacy_key: str
) -> list[str]:
    prompts = request.get(batch_key)
    if not isinstance(prompts, list) or not prompts:
        prompts = [request[legacy_key]]
    cleaned = [str(prompt).strip() for prompt in prompts]
    if any(not prompt for prompt in cleaned):
        raise ValueError(f"{batch_key} must contain non-empty prompts.")
    return cleaned


def _render_reference_prompt(tokenizer: Any, prompt: str) -> tuple[str, str]:
    stripped = prompt.lstrip()
    if stripped.startswith(
        ("<|im_start|>", "<bos><start_of_turn>", "<|begin_of_text|><|start_header_id|>")
    ):
        return stripped, "preformatted_chat_template"
    apply_chat_template = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply_chat_template):
        try:
            rendered = apply_chat_template(
                [{"role": "user", "content": prompt.strip()}],
                tokenize=False,
                add_generation_prompt=True,
            )
        except (TypeError, ValueError):
            rendered = None
        if isinstance(rendered, str) and rendered:
            return rendered, "tokenizer.apply_chat_template"
    return prompt, "plain"


def _contrastive_direction(desired: Any, undesired: Any) -> tuple[Any, float]:
    vector = desired.float() - undesired.float()
    norm = float(vector.norm().detach().cpu().item())
    if math.isclose(norm, 0.0, abs_tol=1e-12):
        raise ValueError("Desired and undesired references produced a zero steering direction.")
    return vector.detach(), norm


def _source_activation_norm(
    wrapper: HuggingFaceModelWrapper,
    prompt: str,
    activation_name: str,
    *,
    position: tuple[int, int],
) -> float:
    tokens = wrapper.to_tokens(prompt, prepend_bos=False)
    _output, cache = wrapper.run_with_cache(
        {"input_ids": tokens},
        layers=[activation_name],
    )
    activation = cache[activation_name]
    if activation.ndim < 2:
        raise ValueError(f"Steering activation {activation_name} must include a model dimension.")
    start, end = position
    selected = activation[0, start:min(end, activation.shape[-2]), :].float()
    if selected.numel() == 0:
        raise ValueError("Steering position range did not select any source activations.")
    return float(selected.norm(dim=-1).median().detach().cpu().item())


def _run_condition(
    wrapper: HuggingFaceModelWrapper,
    *,
    prompt: str,
    prompt_token_count: int,
    target_token_id: int,
    seed: int,
    max_new_tokens: int,
    temperature: float,
    generation_hook: tuple[str, Any] | None = None,
) -> tuple[dict[str, Any], Any]:
    import torch

    random.seed(seed)
    torch.manual_seed(seed)
    prompt_tokens = wrapper.to_tokens(prompt, prepend_bos=False)
    logits, _cache = wrapper.run_with_cache(
        {"input_ids": prompt_tokens},
        layers=[],
        return_type="logits",
    )
    target_logit = float(logits[0, -1, target_token_id].detach().cpu().item())
    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "pad_token_id": wrapper.tokenizer.eos_token_id,
        "prepend_bos": False,
        "return_type": "model_output",
        "return_dict_in_generate": True,
        "output_scores": True,
        "use_cache": True,
    }
    if temperature > 0:
        generation_kwargs["temperature"] = temperature
    handle = None
    if generation_hook is not None:
        hook_name, hook_fn = generation_hook
        handle = wrapper.add_hook(hook_name, hook_fn)
    try:
        generated_output = wrapper.generate(prompt, **generation_kwargs)
    finally:
        if handle is not None:
            handle.remove()
    generated = getattr(generated_output, "sequences", generated_output)
    generated_ids = _flat_token_ids(generated)
    continuation_ids = generated_ids[prompt_token_count:]
    continuation_text = str(
        wrapper.tokenizer.decode(
            continuation_ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
    )
    result = {
        "text": continuation_text,
        "tokenIds": continuation_ids,
        "tokens": [
            {
                "index": index,
                "tokenId": token_id,
                "text": str(
                    wrapper.tokenizer.decode([token_id], clean_up_tokenization_spaces=False)
                ),
            }
            for index, token_id in enumerate(continuation_ids)
        ],
        "targetLogit": round(target_logit, 10),
        "lexicalRisk": _lexical_risk(continuation_text),
    }
    return result, _generation_score_matrix(
        generated_output,
        fallback=logits[0, -1, :].float().detach().cpu(),
    )


def _make_neuron_hook(
    *,
    neuron: int,
    factor: float,
    position: tuple[int, int],
    prompt_token_count: int | None = None,
) -> Callable[..., Any]:
    def hook(activation: Any = None, **kwargs: Any) -> Any:
        value = kwargs.get("activation", activation)
        if value is None or not hasattr(value, "clone") or getattr(value, "ndim", 0) < 2:
            return value
        if neuron < 0 or neuron >= value.shape[-1]:
            raise ValueError(f"MLP neuron {neuron} is outside activation width {value.shape[-1]}.")
        if prompt_token_count is not None and int(value.shape[-2]) < prompt_token_count:
            return value
        start, end = position
        result = value.clone()
        if value.ndim == 2:
            result[:, neuron] *= factor
        else:
            result[:, max(0, start):min(value.shape[-2], end), neuron] *= factor
        return result
    return hook


def _make_generation_direction_hook(
    *,
    vector: Any,
    scale: float,
) -> Callable[..., Any]:
    state = {"is_first_forward": True}

    def hook(activation: Any = None, **kwargs: Any) -> Any:
        value = kwargs.get("activation", activation)
        if value is None or not hasattr(value, "clone") or getattr(value, "ndim", 0) < 2:
            return value
        # Match the source-grid runtime: leave the prompt prefill untouched, then
        # add the direction on every cached autoregressive decoding forward.
        if state["is_first_forward"]:
            state["is_first_forward"] = False
            return value
        result = value.clone()
        direction = vector.to(device=value.device, dtype=value.dtype)
        if value.ndim >= 3:
            result[:, :, :] += scale * direction
        else:
            result[:, :] += scale * direction
        return result
    return hook


def _neuron_operation(factor: float) -> str:
    if factor < 0:
        return "invert"
    if math.isclose(factor, 0.0, abs_tol=1e-8):
        return "suppress"
    if factor <= 1:
        return "reduce"
    return "enhance"


def _logit_delta_summary(original: Any, steered: Any) -> dict[str, Any]:
    if original.shape[-1] != steered.shape[-1]:
        raise ValueError("Original and steered generation scores have different vocabularies.")
    if original.ndim > 1 or steered.ndim > 1:
        original = original.reshape(-1, original.shape[-1])
        steered = steered.reshape(-1, steered.shape[-1])
        shared_steps = min(original.shape[0], steered.shape[0])
        original = original[:shared_steps]
        steered = steered[:shared_steps]
    signed_delta = steered.float() - original.float()
    delta = signed_delta.abs()
    maximum = float(delta.max().item()) if delta.numel() else 0.0
    top_flat_index = int(delta.argmax().item()) if delta.numel() else 0
    vocabulary_size = int(delta.shape[-1]) if delta.ndim else 0
    top_index = top_flat_index % vocabulary_size if vocabulary_size else 0
    changed_vocabulary_logits = (
        int((delta > 1e-6).any(dim=0).sum().item())
        if delta.ndim > 1
        else int((delta > 1e-6).sum().item())
    )
    return {
        "maxAbsLogit": round(maximum, 10),
        "meanAbsLogit": round(float(delta.mean().item()) if delta.numel() else 0.0, 10),
        "changedVocabularyLogits": changed_vocabulary_logits,
        "topChangedTokenId": top_index,
        "topChangedTokenDelta": round(
            float(signed_delta.reshape(-1)[top_flat_index].item())
            if signed_delta.numel()
            else 0.0,
            10,
        ),
        "effectStatus": "changed" if maximum > 1e-6 else "no_change",
    }


def _generation_score_matrix(generated_output: Any, *, fallback: Any) -> Any:
    import torch

    scores = getattr(generated_output, "scores", None)
    if not scores:
        return fallback
    return torch.stack(
        [score[0].float().detach().cpu() for score in scores],
        dim=0,
    )


def _optional_layer(value: Any, fallback: int) -> int:
    return fallback if value is None else int(value)


def _first_divergence_index(left: list[int], right: list[int]) -> int | None:
    for index, (left_token, right_token) in enumerate(zip(left, right, strict=False)):
        if left_token != right_token:
            return index
    return min(len(left), len(right)) if len(left) != len(right) else None


def _flat_token_ids(tokens: Any) -> list[int]:
    value = tokens.detach().cpu().tolist() if hasattr(tokens, "detach") else tokens
    if value and isinstance(value[0], list):
        if len(value) != 1:
            raise ValueError("Intervention jobs support one prompt at a time.")
        value = value[0]
    return [int(token_id) for token_id in value]


def _lexical_risk(text: str) -> float:
    lowered = text.lower()
    words = max(1, len(lowered.split()))
    hits = sum(lowered.count(term) for term in RISK_TERMS)
    return round(hits / words, 8)


def _levenshtein(left: list[int], right: list[int]) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_value != right_value),
                )
            )
        previous = current
    return previous[-1]


def _diff_rows(left: list[int], right: list[int]) -> list[dict[str, Any]]:
    matcher = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
    return [
        {
            "kind": kind,
            "originalStart": left_start,
            "originalEnd": left_end,
            "steeredStart": right_start,
            "steeredEnd": right_end,
        }
        for kind, left_start, left_end, right_start, right_end in matcher.get_opcodes()
    ]


def _merge_intervention_result(
    run: dict[str, Any],
    comparison: dict[str, Any],
    *,
    run_id: str,
) -> dict[str, Any]:
    source_run = {"runId": run["runId"], "sampleId": run["sampleId"]}
    run["intervention"] = comparison
    provenance = run.setdefault("metricProvenance", {})
    mode = str(comparison.get("mode", "direction"))
    method_label = {
        "neuron": "MLP post-activation neuron scaling",
        "sae_feature": "Gemma Scope SAE feature intervention",
    }.get(mode, "Generation-time raw contrastive activation steering")
    provenance["interventionTargetLogitDelta"] = {
        "label": "Target logit delta",
        "method": method_label,
        "semantics": "Intervened target-token logit minus the original target-token logit.",
        "normalization": "none; raw logit difference",
        "kind": "causal",
    }
    provenance["interventionTokenEditDistance"] = {
        "label": "Generation edit distance",
        "method": "Levenshtein distance over generated token IDs",
        "semantics": "Minimum token insertions, deletions, and substitutions between outputs.",
        "normalization": "none; integer token operations",
        "kind": "causal",
    }
    provenance["interventionLexicalRiskDelta"] = {
        "label": "Lexical risk proxy delta",
        "method": "Fixed risk-term match rate",
        "semantics": "Steered minus original matched risk terms per whitespace-delimited word.",
        "normalization": "matched terms divided by output word count",
        "kind": "derived_proxy",
    }
    provenance["interventionMaxVocabularyLogitDelta"] = {
        "label": "Maximum vocabulary logit delta",
        "method": method_label,
        "semantics": "Largest absolute next-token logit change across the complete vocabulary.",
        "normalization": "none; maximum absolute raw logit difference",
        "kind": "causal",
    }
    if "directionProjectionDelta" in comparison.get("deltas", {}):
        provenance["interventionDirectionProjectionDelta"] = {
            "label": "Applied direction projection",
            "method": method_label,
            "semantics": (
                "Signed L2 magnitude injected along the desired-minus-undesired direction."
            ),
            "normalization": "none; scale multiplied by the raw contrast-vector norm",
            "kind": "causal",
        }
    run["runId"] = run_id
    metadata = run.setdefault("metadata", {})
    jobs = list(metadata.get("interventionJobs", []))
    jobs.append(
        {
            "jobVersion": str(comparison["vector"].get("algorithmVersion", "1.0")),
            "method": comparison["vector"]["method"],
            "mode": comparison.get("mode", "direction"),
            **({"feature": comparison["feature"]} if "feature" in comparison else {}),
            "layer": comparison["layer"],
            "sourceLayer": comparison.get("sourceLayer", comparison["layer"]),
            "injectLayer": comparison.get("injectLayer", comparison["layer"]),
            "injectionPhase": comparison["vector"].get("injectionPhase", "prompt"),
            "component": comparison["component"],
            "scale": comparison["scale"],
            "positionStart": comparison["positionStart"],
            "positionEnd": comparison["positionEnd"],
            "targetTokenId": comparison["targetTokenId"],
            "targetTokenText": comparison["targetTokenText"],
            "seed": comparison["seed"],
            "maxNewTokens": comparison["maxNewTokens"],
            "temperature": comparison["temperature"],
            "sourceRun": source_run,
            "sourceKey": comparison["vector"]["sourceKey"],
            "trustRemoteCode": False,
        }
    )
    metadata["interventionJobs"] = jobs
    metadata["parentRun"] = source_run
    return run


if __name__ == "__main__":
    main()
