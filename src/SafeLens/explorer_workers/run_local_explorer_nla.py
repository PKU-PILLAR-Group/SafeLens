from __future__ import annotations

# ruff: noqa: E402
import argparse
import gc
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from SafeLens.core.base import PipelineConfig
from SafeLens.nla import NLAClient, get_nla_profile
from SafeLens.utils import HuggingFaceModelWrapper, build_model_wrapper


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exact NLA AV/AR for an Explorer sample.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    run = payload["run"]
    request = payload["request"]
    profile = get_nla_profile(request["profile"])
    wrapper = _load_base_model(profile.base_model)
    try:
        vectors = _capture_vectors(
            wrapper,
            prompt=str(run["prompt"]),
            layer=profile.layer,
            component=profile.component,
            positions=request["positions"],
        )
    finally:
        wrapper.remove_hooks()
        del wrapper
        gc.collect()
        _empty_cuda_cache()

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    nla_cache_dir = ".cache/safelens/nla"
    runtime_profile, local_files_only = _localize_nla_profile(profile, nla_cache_dir)
    requested_revision = str(request["revision"])
    actor_revision = profile.av_revision or requested_revision
    reconstructor_revision = profile.ar_revision or requested_revision
    client = NLAClient.from_profile(
        runtime_profile,
        load_reconstructor=True,
        cache_dir=nla_cache_dir,
        local_files_only=local_files_only,
        token=token,
        revision=actor_revision,
        reconstructor_revision=reconstructor_revision,
        device=os.environ.get("SAFELENS_EXPLORER_JOB_DEVICE", "cpu"),
        dtype=os.environ.get("SAFELENS_EXPLORER_JOB_DTYPE", "auto"),
        trust_remote_code=False,
    )
    token_texts = [str(token_row["text"]) for token_row in run["tokens"]]
    results = client.explain_activations(
        vectors,
        tokens=[token_texts[position] for position in request["positions"]],
        positions=list(range(len(request["positions"]))),
        sample_id=str(run["sampleId"]),
        source=f"layer_{profile.layer}.{profile.component}",
        max_new_tokens=int(request["maxNewTokens"]),
        do_sample=False,
    )
    derived = _merge_results(
        run,
        [result.to_dict() for result in results],
        profile=profile,
        positions=[int(position) for position in request["positions"]],
        revision=requested_revision,
        actor_checkpoint=client.verbalizer.checkpoint,
        reconstructor_checkpoint=(
            client.reconstructor.checkpoint if client.reconstructor is not None else None
        ),
        run_id=args.run_id,
        max_new_tokens=int(request["maxNewTokens"]),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(derived, indent=2), encoding="utf-8")


def _load_base_model(model_id: str) -> HuggingFaceModelWrapper:
    cache_dir = os.environ.get(
        "SAFELENS_EXPLORER_MODEL_CACHE",
        ".cache/safelens/local-explorer-real-flow",
    )
    local_snapshot = _complete_hf_snapshot(model_id, cache_dir)
    load_kwargs: dict[str, Any] = {}
    tokenizer_kwargs: dict[str, Any] = {}
    if local_snapshot is not None:
        load_kwargs["local_files_only"] = True
        tokenizer_kwargs["local_files_only"] = True
    config = PipelineConfig.model_validate(
        {
            "model": {
                "source": "local" if local_snapshot is not None else "huggingface",
                "name": model_id,
                "local_dir": str(local_snapshot) if local_snapshot is not None else None,
                "device": os.environ.get("SAFELENS_EXPLORER_JOB_DEVICE", "cpu"),
                "dtype": "auto",
                "cache_dir": cache_dir,
                "load_kwargs": load_kwargs,
                "tokenizer_kwargs": tokenizer_kwargs,
                "trust_remote_code": False,
            }
        }
    )
    wrapper = build_model_wrapper(config.model)
    if not isinstance(wrapper, HuggingFaceModelWrapper):
        raise TypeError(f"expected HuggingFaceModelWrapper, got {type(wrapper).__name__}")
    wrapper.load_model()
    return wrapper


def _complete_hf_snapshot(model_id: str, cache_dir: str) -> Path | None:
    repository = Path(cache_dir) / f"models--{model_id.replace('/', '--')}"
    reference = repository / "refs" / "main"
    if not reference.is_file():
        return None
    revision = reference.read_text(encoding="utf-8").strip()
    snapshot = repository / "snapshots" / revision
    if (
        not (snapshot / "config.json").is_file()
        or not (snapshot / "tokenizer_config.json").is_file()
    ):
        return None
    weight_files: list[Path] = []
    for index_name in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        index_path = snapshot / index_name
        if not index_path.is_file():
            continue
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            filenames = set(index["weight_map"].values())
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            return None
        if not filenames or not all(isinstance(name, str) and name for name in filenames):
            return None
        weight_files.extend(snapshot / name for name in sorted(filenames))
    if not weight_files:
        weight_files = list(snapshot.glob("*.safetensors")) + list(
            snapshot.glob("pytorch_model*.bin")
        )
    if not weight_files or not all(
        path.is_file() and path.stat().st_size > 0 for path in weight_files
    ):
        return None
    return snapshot


def _localize_nla_profile(profile: Any, cache_dir: str) -> tuple[Any, bool]:
    av_snapshot = _complete_hf_snapshot(profile.av_repo, cache_dir)
    ar_snapshot = (
        _complete_hf_snapshot(profile.ar_repo, cache_dir)
        if profile.ar_repo is not None
        else None
    )
    localized = replace(
        profile,
        av_repo=str(av_snapshot) if av_snapshot is not None else profile.av_repo,
        ar_repo=(
            str(ar_snapshot)
            if ar_snapshot is not None
            else profile.ar_repo
        ),
    )
    complete = av_snapshot is not None and (
        profile.ar_repo is None or ar_snapshot is not None
    )
    return localized, complete


def _capture_vectors(
    wrapper: HuggingFaceModelWrapper,
    *,
    prompt: str,
    layer: int,
    component: str,
    positions: list[int],
) -> Any:
    key = f"layer_{layer}.{component}"
    tokens = wrapper.to_tokens(prompt, prepend_bos=False)
    _output, cache = wrapper.run_with_cache({"input_ids": tokens}, layers=[key])
    activation = cache[key]
    if activation.ndim == 3:
        activation = activation[0]
    if activation.ndim != 2:
        raise ValueError(f"NLA activation {key} must have shape [pos, d_model].")
    if max(positions) >= activation.shape[0]:
        raise ValueError("Requested NLA position is outside the rerun token sequence.")
    return activation[positions].float().detach().cpu()


def _empty_cuda_cache() -> None:
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _merge_results(
    run: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    profile: Any,
    positions: list[int],
    revision: str,
    actor_checkpoint: str | None,
    reconstructor_checkpoint: str | None,
    run_id: str,
    max_new_tokens: int,
) -> dict[str, Any]:
    rows = [
        row
        for row in run.get("nla", [])
        if not (
            int(row.get("layer", -1)) == profile.layer
            and row.get("component") == profile.component
            and int(row.get("tokenIndex", -1)) in positions
        )
    ]
    for position, result in zip(positions, results, strict=True):
        if result.get("cosine") is None or result.get("mse_nrm") is None:
            raise ValueError("NLA AR fidelity is required; result did not contain cosine and MSE.")
        rows.append(
            {
                "tokenIndex": position,
                "layer": profile.layer,
                "component": profile.component,
                "explanation": result["explanation"],
                "cosine": float(result["cosine"]),
                "mse": float(result["mse_nrm"]),
                "activationNorm": float(result["activation_norm"]),
                "status": "available",
                "profile": profile.name,
                "source": f"layer_{profile.layer}.{profile.component}",
                "token": run["tokens"][position]["text"],
            }
        )
    run["nla"] = rows
    for candidate in run["nlaCompatibility"]["profiles"]:
        if candidate["name"] == profile.name:
            candidate["status"] = "compatible"
            candidate["reason"] = "Exact AV/AR artifact result is loaded for this derived run."
    source_run = {"runId": run["runId"], "sampleId": run["sampleId"]}
    run["runId"] = run_id
    metadata = run.setdefault("metadata", {})
    jobs = list(metadata.get("nlaJobs", []))
    jobs.append(
        {
            "jobVersion": "1.0",
            "profile": profile.name,
            "baseModel": profile.base_model,
            "layer": profile.layer,
            "component": profile.component,
            "dModel": profile.d_model,
            "avRepo": profile.av_repo,
            "arRepo": profile.ar_repo,
            "requestedRevision": revision,
            "actorRevision": _checkpoint_revision(actor_checkpoint),
            "reconstructorRevision": _checkpoint_revision(reconstructor_checkpoint),
            "positions": positions,
            "maxNewTokens": max_new_tokens,
            "trustRemoteCode": False,
            "sourceRun": source_run,
        }
    )
    metadata["nlaJobs"] = jobs
    metadata["parentRun"] = source_run
    return run


def _checkpoint_revision(checkpoint: str | None) -> str | None:
    if not checkpoint:
        return None
    path = Path(checkpoint)
    return path.name if path.parent.name == "snapshots" else str(checkpoint)


if __name__ == "__main__":
    main()
