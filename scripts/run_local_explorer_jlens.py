from __future__ import annotations

import argparse
import gc
import json
import os
from pathlib import Path
from typing import Any

from SafeLens.explorer_model import resolve_explorer_pretrained_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an exact Jacobian Lens readout.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    run = payload["run"]
    request = payload["request"]
    derived = _run_jlens(run, request, run_id=args.run_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(derived, indent=2), encoding="utf-8")


def _run_jlens(run: dict[str, Any], request: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    try:
        import jlens
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Jacobian Lens is not installed. Install SafeLens with the 'jlens' extra."
        ) from exc

    model_name = str(run["modelName"])
    device = os.environ.get("SAFELENS_EXPLORER_JOB_DEVICE", "cpu")
    dtype_name = os.environ.get(
        "SAFELENS_EXPLORER_JOB_DTYPE",
        "float32" if device == "cpu" else "bfloat16",
    )
    dtype = getattr(torch, dtype_name, "auto") if dtype_name != "auto" else "auto"
    cache_dir = os.environ.get(
        "SAFELENS_EXPLORER_MODEL_CACHE",
        ".cache/safelens/local-explorer-real-flow",
    )
    model_source, local_files_only, _model_provider = resolve_explorer_pretrained_path(
        model_name,
        cache_dir=cache_dir,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_source,
        cache_dir=cache_dir,
        local_files_only=local_files_only,
        trust_remote_code=False,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_source,
        cache_dir=cache_dir,
        dtype=dtype,
        local_files_only=local_files_only,
        low_cpu_mem_usage=device != "cpu",
        trust_remote_code=False,
    )
    model.to(device)  # type: ignore[arg-type]
    lens_model = jlens.from_hf(model, tokenizer, force_bos=False)
    lens = _load_lens(
        jlens,
        str(request["lensSource"]),
        filename=str(request["filename"]),
        revision=str(request["revision"]),
        cache_dir=os.environ.get(
            "SAFELENS_EXPLORER_JLENS_CACHE",
            ".cache/safelens/jlens",
        ),
    )
    layer = int(request["layer"])
    position = int(request["position"])
    try:
        if lens.d_model != lens_model.d_model:
            raise ValueError(
                f"Lens width {lens.d_model} does not match model width {lens_model.d_model}."
            )
        if layer not in lens.source_layers:
            raise ValueError(
                f"Layer L{layer} is not fitted; available J-Lens layers are {lens.source_layers}."
            )
        lens_logits, model_logits, input_ids = lens.apply(
            lens_model,
            str(run["prompt"]),
            layers=[layer],
            positions=[position],
            max_seq_len=max(1, len(run["tokens"])),
            use_jacobian=True,
        )
        expected_ids = [int(token["tokenId"]) for token in run["tokens"]]
        actual_ids = [int(token_id) for token_id in input_ids[0].detach().cpu().tolist()]
        if actual_ids != expected_ids:
            raise ValueError(
                "J-Lens tokenization does not match the source Run; no position was evaluated."
            )
        row = _result_row(
            run,
            tokenizer,
            lens_logits[layer][0],
            model_logits[0],
            layer=layer,
            position=position,
            top_k=int(request["topK"]),
            lens_source=str(request["lensSource"]),
            filename=str(request["filename"]),
            revision=str(request["revision"]),
            n_prompts=int(lens.n_prompts),
        )
    finally:
        del lens
        del lens_model
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    existing = [
        item
        for item in run.get("jLens", [])
        if not (
            int(item.get("layer", -1)) == layer
            and int(item.get("tokenIndex", -1)) == position
        )
    ]
    run["jLens"] = [*existing, row]
    source_run = {"runId": run["runId"], "sampleId": run["sampleId"]}
    run["runId"] = run_id
    metadata = run.setdefault("metadata", {})
    jobs = list(metadata.get("jLensJobs", []))
    jobs.append(
        {
            "jobVersion": "1.0",
            "method": "average-input-output-jacobian",
            "layer": layer,
            "position": position,
            "lensSource": request["lensSource"],
            "filename": request["filename"],
            "revision": request["revision"],
            "topK": request["topK"],
            "sourceRun": source_run,
        }
    )
    metadata["jLensJobs"] = jobs
    metadata["parentRun"] = source_run
    return run


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


def _load_lens(
    jlens: Any,
    source: str,
    *,
    filename: str,
    revision: str,
    cache_dir: str,
) -> Any:
    source_path = Path(source).expanduser()
    if source_path.is_file() or source_path.is_dir():
        return jlens.JacobianLens.from_pretrained(
            str(source_path),
            filename=filename,
            revision=revision,
        )

    cached_checkpoint = _cached_lens_checkpoint(
        source,
        filename=filename,
        revision=revision,
        cache_dir=cache_dir,
    )
    if cached_checkpoint is not None:
        return jlens.JacobianLens.load(str(cached_checkpoint))

    from huggingface_hub import snapshot_download

    snapshot = snapshot_download(
        source,
        allow_patterns=[filename],
        revision=revision,
        cache_dir=cache_dir,
    )
    checkpoint = Path(snapshot) / filename
    if not checkpoint.is_file() or checkpoint.stat().st_size == 0:
        raise FileNotFoundError(
            f"J-Lens checkpoint {filename!r} was not downloaded from {source!r}."
        )
    return jlens.JacobianLens.load(str(checkpoint))


def _cached_lens_checkpoint(
    source: str,
    *,
    filename: str,
    revision: str,
    cache_dir: str,
) -> Path | None:
    repository = Path(cache_dir) / f"models--{source.replace('/', '--')}"
    snapshot_revision = revision
    reference = repository / "refs" / revision
    if reference.is_file():
        snapshot_revision = reference.read_text(encoding="utf-8").strip()
    checkpoint = repository / "snapshots" / snapshot_revision / filename
    if checkpoint.is_file() and checkpoint.stat().st_size > 0:
        return checkpoint
    return None


def _result_row(
    run: dict[str, Any],
    tokenizer: Any,
    lens_logits: Any,
    model_logits: Any,
    *,
    layer: int,
    position: int,
    top_k: int,
    lens_source: str,
    filename: str,
    revision: str,
    n_prompts: int,
) -> dict[str, Any]:
    import torch

    lens_logits = lens_logits.float().cpu()
    model_logits = model_logits.float().cpu()
    target_id = (
        int(run["tokens"][position + 1]["tokenId"])
        if position + 1 < len(run["tokens"])
        else int(model_logits.argmax().item())
    )
    probabilities = torch.softmax(lens_logits, dim=-1)
    target_logit = float(lens_logits[target_id].item())
    target_rank = int((lens_logits > lens_logits[target_id]).sum().item()) + 1
    return {
        "layer": layer,
        "tokenIndex": position,
        "targetTokenId": target_id,
        "targetTokenText": _decode_token(tokenizer, target_id),
        "targetLogit": target_logit,
        "targetProbability": float(probabilities[target_id].item()),
        "targetRank": target_rank,
        "topPredictions": _top_predictions(tokenizer, lens_logits, top_k),
        "modelTopPredictions": _top_predictions(tokenizer, model_logits, top_k),
        "lensSource": lens_source,
        "filename": filename,
        "revision": revision,
        "nPrompts": n_prompts,
        "sourceKey": f"jlens:{lens_source}:{filename}@{revision}",
    }


def _top_predictions(tokenizer: Any, logits: Any, top_k: int) -> list[dict[str, Any]]:
    import torch

    probabilities = torch.softmax(logits, dim=-1)
    values, ids = torch.topk(logits, k=min(top_k, int(logits.shape[-1])))
    return [
        {
            "tokenId": int(token_id),
            "tokenText": _decode_token(tokenizer, int(token_id)),
            "logit": float(value),
            "probability": float(probabilities[int(token_id)].item()),
        }
        for value, token_id in zip(values.tolist(), ids.tolist(), strict=True)
    ]


def _decode_token(tokenizer: Any, token_id: int) -> str:
    return str(tokenizer.decode([token_id], clean_up_tokenization_spaces=False))


if __name__ == "__main__":
    main()
