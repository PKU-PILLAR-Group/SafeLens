#!/usr/bin/env python3
"""Extract correctness vectors and steer baseline-wrong multiple-choice examples."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import Counter
from functools import partial
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
STEERING_MINIMAL_ROOT = Path(
    os.environ.get("SAFELENS_STEERING_MINIMAL_ROOT", ROOT.parent / "steering_minimal")
).expanduser()
if STEERING_MINIMAL_ROOT.is_dir():
    sys.path.insert(0, str(STEERING_MINIMAL_ROOT))

from eval_direct_choice_generation import Example, load_examples, parse_letter  # noqa: E402
from some_SAEs import GemmaScope1SAE  # noqa: E402


MODEL_PATH = os.environ.get("SAFELENS_GEMMA_2_9B_IT_MODEL", "google/gemma-2-9b-it")
BASELINE_PATH = ROOT / "yjr_local_test/results/gemma-2-9b-it_direct_choice_generation.json"
CURRENT_TQA = ROOT / "yjr_local_test/external/TruthfulQA/data/mc_task.json"
V1_TQA = ROOT / "yjr_local_test/external/TruthfulQA/data/v1/mc_task.json"
WIKI_FACTOR = ROOT / "yjr_local_test/external/factor/data/wiki_factor.csv"
SAE_SPECS = {
    20: ROOT / "yjr_local_test/external/SAEs/gemma-scope-9b-it-res-layer_20-width_16k-average_l0_91/params.npz",
    31: Path(
        os.environ.get(
            "SAFELENS_GEMMA_SCOPE_L31_SAE",
            ROOT.parent
            / "models/SAEs/"
            "gemma-scope-9b-it-res-layer_31-width_16k-average_l0_76/params.npz",
        )
    ).expanduser(),
}
SOURCE_LAYERS = [22, 32]
INJECT_LAYERS = [22, 32]
ALPHAS = {
    "mean_minus_neg": [1.0, 1.5, 2.0, 2.5, 3.0],
    "pca_minus_neg": [100.0, 130.0, 160.0, 190.0, 220.0, 250.0, 280.0, 310.0, 340.0],
    "sae": [200.0, 250.0, 300.0, 350.0, 400.0, 500.0],
}
SCOPES = ["answer_boundary_and_decode", "prompt_and_decode"]
TASK_ORDER = [
    "wiki_factor",
    "truthfulqa_binary_790",
    "truthfulqa_mc1_790",
    "truthfulqa_mc1_v1_817",
]


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    pending.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending.replace(path)


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def balanced_sample(
    rows: list[dict[str, Any]], wanted_correct: bool, task: str, seed: int
) -> list[dict[str, Any]]:
    labels = ["A", "B"] if "binary" in task else ["A", "B", "C", "D"]
    quota = 20 // len(labels)
    picked: list[dict[str, Any]] = []
    for label in labels:
        candidates = [
            row for row in rows if bool(row["correct"]) == wanted_correct and row["answer"] == label
        ]
        random.Random(f"{seed}:{task}:{wanted_correct}:{label}").shuffle(candidates)
        if len(candidates) < quota:
            raise ValueError(f"Not enough {task} correct={wanted_correct} gold={label}: {len(candidates)}")
        picked.extend(candidates[:quota])
    return picked


def prepare_task(
    task: str, all_examples: list[Example], baseline: dict[str, Any], seed: int
) -> dict[str, Any]:
    examples = {example.example_id: example for example in all_examples if example.task == task}
    rows = [row for row in baseline["details"] if row["task"] == task]
    if len(rows) != len(examples):
        raise ValueError(f"Baseline/example mismatch for {task}: {len(rows)} vs {len(examples)}")
    train_pos = balanced_sample(rows, True, task, seed)
    train_neg = balanced_sample(rows, False, task, seed)
    held_out_neg = [
        row
        for row in rows
        if not row["correct"] and row["example_id"] not in {x["example_id"] for x in train_neg}
    ]
    return {
        "train_pos": train_pos,
        "train_neg": train_neg,
        "test_neg": held_out_neg,
        "pos_examples": [examples[row["example_id"]] for row in train_pos],
        "neg_examples": [examples[row["example_id"]] for row in train_neg],
        "test_examples": [examples[row["example_id"]] for row in held_out_neg],
    }


def render_prompt(tokenizer: Any, example: Example) -> str:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": example.prompt}], tokenize=False, add_generation_prompt=True
    )


@torch.inference_mode()
def capture_boundary_hidden(
    model: Any,
    tokenizer: Any,
    prompts: list[str],
    layers: list[int],
    device: torch.device,
) -> dict[int, torch.Tensor]:
    tokenizer.padding_side = "left"
    inputs = tokenizer(
        prompts, return_tensors="pt", padding=True, add_special_tokens=False, truncation=False
    ).to(device)
    captured: dict[int, torch.Tensor] = {}
    handles = []
    model_layers = model.model.layers

    def hook(layer_idx: int, module: Any, module_inputs: Any, module_output: Any):
        hidden = module_output[0] if isinstance(module_output, tuple) else module_output
        captured[layer_idx] = hidden[:, -1, :].detach().float().cpu()

    for layer_idx in layers:
        handles.append(model_layers[layer_idx].register_forward_hook(partial(hook, layer_idx)))
    try:
        model.model(**inputs, use_cache=False, return_dict=True)
    finally:
        for handle in handles:
            handle.remove()
    return captured


@torch.inference_mode()
def build_vectors(
    model: Any,
    tokenizer: Any,
    pos_examples: list[Example],
    neg_examples: list[Example],
    saes: dict[int, Any],
    device: torch.device,
) -> tuple[dict[tuple[str, int], torch.Tensor], dict[str, Any]]:
    prompts = [render_prompt(tokenizer, x) for x in pos_examples + neg_examples]
    all_source_layers = sorted(set(SOURCE_LAYERS + list(saes)))
    hidden = capture_boundary_hidden(model, tokenizer, prompts, all_source_layers, device)
    vectors: dict[tuple[str, int], torch.Tensor] = {}
    metadata: dict[str, Any] = {}
    n_pos = len(pos_examples)

    for layer in SOURCE_LAYERS:
        pos = hidden[layer][:n_pos]
        neg = hidden[layer][n_pos:]
        delta = pos - neg
        mean = delta.mean(dim=0)
        vectors[("mean_minus_neg", layer)] = mean.to(torch.bfloat16)
        _, singular_values, vh = torch.linalg.svd(delta, full_matrices=False)
        pc = vh[0]
        if torch.dot(pc, mean) < 0:
            pc = -pc
        vectors[("pca_minus_neg", layer)] = pc.to(torch.bfloat16)
        metadata[f"mean_minus_neg:{layer}"] = {
            "source_layer": layer,
            "norm": float(mean.norm()),
        }
        metadata[f"pca_minus_neg:{layer}"] = {
            "source_layer": layer,
            "norm": float(pc.norm()),
            "top_singular_value": float(singular_values[0]),
            "sign_aligned_to_mean": True,
        }

    for layer, sae in saes.items():
        source = hidden[layer].to(device=device, dtype=sae.W_enc.dtype).unsqueeze(1)
        activations = sae.encode(source)[:, 0, :].float()
        pos_act = activations[:n_pos]
        neg_act = activations[n_pos:]
        support = (pos_act > 1.0).float().mean(dim=0)
        pos_mean = pos_act.mean(dim=0)
        neg_mean = neg_act.mean(dim=0)
        candidates = torch.nonzero(support >= 0.85, as_tuple=False).flatten()
        fallback = False
        if candidates.numel() == 0:
            candidates = torch.arange(pos_act.shape[1], device=device)
            fallback = True
        top_count = min(20, candidates.numel())
        consensus = candidates[torch.topk(pos_mean[candidates], k=top_count).indices]
        contrast = pos_mean[consensus] - neg_mean[consensus]
        feature = int(consensus[torch.argmax(contrast)].item())
        vector = sae.W_dec[feature].detach().cpu().to(torch.bfloat16)
        vectors[("sae", layer)] = vector
        metadata[f"sae:{layer}"] = {
            "source_layer": layer,
            "feature": feature,
            "norm": float(vector.float().norm()),
            "positive_support": float(support[feature]),
            "positive_mean_activation": float(pos_mean[feature]),
            "negative_mean_activation": float(neg_mean[feature]),
            "activation_contrast": float(pos_mean[feature] - neg_mean[feature]),
            "consensus_candidate_count": int(candidates.numel()),
            "top_consensus_features": [int(x) for x in consensus.tolist()],
            "fallback_without_support_threshold": fallback,
        }
        del source, activations, pos_act, neg_act
    return vectors, metadata


def make_batches(
    tokenizer: Any,
    examples: list[Example],
    max_batch_tokens: int,
    max_batch_size: int,
) -> list[dict[str, Any]]:
    items = []
    for example in examples:
        prompt = render_prompt(tokenizer, example)
        ids = tokenizer(prompt, add_special_tokens=False, truncation=False)["input_ids"]
        items.append((len(ids), example, ids))
    items.sort(key=lambda x: x[0])
    raw_batches: list[list[tuple[int, Example, list[int]]]] = []
    batch: list[tuple[int, Example, list[int]]] = []
    for item in items:
        size = len(batch) + 1
        width = item[0]
        if batch and (size > max_batch_size or size * width > max_batch_tokens):
            raw_batches.append(batch)
            batch = [item]
        else:
            batch.append(item)
    if batch:
        raw_batches.append(batch)

    result = []
    for batch in raw_batches:
        width = max(item[0] for item in batch)
        ids_tensor = torch.full((len(batch), width), tokenizer.pad_token_id, dtype=torch.long)
        mask = torch.zeros_like(ids_tensor)
        for i, (_, _, ids) in enumerate(batch):
            ids_tensor[i, -len(ids) :] = torch.tensor(ids)
            mask[i, -len(ids) :] = 1
        result.append({
            "examples": [item[1] for item in batch],
            "input_ids": ids_tensor,
            "attention_mask": mask,
        })
    return result


def steering_hook(
    module: Any,
    module_inputs: Any,
    module_output: Any,
    alpha: float,
    vector: torch.Tensor,
    state: dict[str, Any],
    scope: str,
):
    hidden = module_output[0] if isinstance(module_output, tuple) else module_output
    rest = module_output[1:] if isinstance(module_output, tuple) else None
    steering = vector.to(device=hidden.device, dtype=hidden.dtype)
    if state["first"]:
        state["first"] = False
        if scope == "answer_boundary_and_decode":
            hidden = hidden.clone()
            hidden[:, -1, :] += alpha * steering
        elif scope == "prompt_and_decode":
            hidden = hidden + alpha * steering
        else:
            raise ValueError(scope)
    else:
        hidden = hidden + alpha * steering
    return (hidden, *rest) if rest is not None else hidden


@torch.inference_mode()
def generate_predictions(
    model: Any,
    tokenizer: Any,
    batches: list[dict[str, Any]],
    device: torch.device,
    inject_layer: int | None = None,
    alpha: float = 0.0,
    vector: torch.Tensor | None = None,
    scope: str = "answer_boundary_and_decode",
) -> list[dict[str, Any]]:
    records = []
    for batch in batches:
        inputs = {
            "input_ids": batch["input_ids"].to(device),
            "attention_mask": batch["attention_mask"].to(device),
        }
        handle = None
        if inject_layer is not None and vector is not None and alpha != 0:
            handle = model.model.layers[inject_layer].register_forward_hook(
                partial(
                    steering_hook,
                    alpha=alpha,
                    vector=vector,
                    state={"first": True},
                    scope=scope,
                )
            )
        try:
            generated = model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=8,
                use_cache=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        finally:
            if handle is not None:
                handle.remove()
        responses = tokenizer.batch_decode(
            generated[:, inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        for example, response in zip(batch["examples"], responses):
            prediction = parse_letter(response, example.option_count)
            records.append({
                "example_id": example.example_id,
                "answer": example.answer,
                "prediction": prediction,
                "response": response,
                "correct": bool(prediction == example.answer),
            })
    return records


def config_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["method"], row["source_layer"], row["inject_layer"], row["alpha"], row["scope"]
    )


def load_completed(path: Path) -> tuple[set[tuple[Any, ...]], list[dict[str, Any]]]:
    if not path.exists():
        return set(), []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    configs = [row for row in rows if row.get("kind") == "config"]
    return {config_key(row) for row in configs}, configs


def process_task(
    task: str,
    model: Any,
    tokenizer: Any,
    all_examples: list[Example],
    baseline: dict[str, Any],
    saes: dict[int, Any],
    args: argparse.Namespace,
    device: torch.device,
) -> None:
    print(f"[TASK START] {task}", flush=True)
    task_dir = Path(args.output_dir) / task
    task_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = task_dir / "metadata.json"
    results_path = task_dir / "sweep.jsonl"
    summary_path = task_dir / "summary.json"
    task_examples = [example for example in all_examples if example.task == task]
    full_batches = make_batches(
        tokenizer, task_examples, args.max_batch_tokens, args.max_batch_size
    )
    fresh_baseline_details = generate_predictions(model, tokenizer, full_batches, device)
    for row in fresh_baseline_details:
        row["task"] = task
    saved_rows = {
        row["example_id"]: row
        for row in baseline["details"]
        if row["task"] == task
    }
    full_baseline_mismatch = sum(
        row["prediction"] != saved_rows[row["example_id"]]["prediction"]
        for row in fresh_baseline_details
    )
    fresh_baseline = {"details": fresh_baseline_details}
    data = prepare_task(task, all_examples, fresh_baseline, args.seed)
    train_meta = {
        "task": task,
        "seed": args.seed,
        "model": args.model,
        "source_layers": SOURCE_LAYERS,
        "sae_source_layers": list(SAE_SPECS),
        "inject_layers": INJECT_LAYERS,
        "alphas": ALPHAS,
        "scopes": SCOPES,
        "train_positive": data["train_pos"],
        "train_negative": data["train_neg"],
        "test_negative_ids": [row["example_id"] for row in data["test_neg"]],
        "counts": {"train_positive": 20, "train_negative": 20, "test_negative": len(data["test_neg"])},
    }
    vectors, vector_meta = build_vectors(
        model, tokenizer, data["pos_examples"], data["neg_examples"], saes, device
    )
    torch.save({f"{method}:{layer}": vector for (method, layer), vector in vectors.items()}, task_dir / "vectors.pt")
    atomic_json(task_dir / "vector_metadata.json", vector_meta)
    # Keep these batches bit-for-bit fixed for alpha=0 and every steering config.
    # A few near-tie BF16 predictions can depend on batch shape; score only IDs
    # that are wrong in this exact fixed-batch baseline without repacking tensors.
    batches = make_batches(
        tokenizer, data["test_examples"], args.max_batch_tokens, args.max_batch_size
    )
    baseline_now = generate_predictions(model, tokenizer, batches, device)
    eligible_ids = {row["example_id"] for row in baseline_now if not row["correct"]}
    removed_batch_sensitive_ids = sorted(
        row["example_id"] for row in baseline_now if row["correct"]
    )
    train_meta["test_negative_ids"] = sorted(eligible_ids)
    train_meta["counts"]["test_negative"] = len(eligible_ids)
    train_meta["full_baseline_prediction_mismatches_vs_previous_run"] = full_baseline_mismatch
    train_meta["removed_batch_sensitive_ids"] = removed_batch_sensitive_ids
    atomic_json(metadata_path, train_meta)
    atomic_json(
        task_dir / "baseline_validation.json",
        {
            "full_task_baseline_total": len(fresh_baseline_details),
            "full_task_baseline_correct": sum(row["correct"] for row in fresh_baseline_details),
            "full_task_baseline_prediction_mismatches_vs_previous_run": full_baseline_mismatch,
            "removed_batch_sensitive_ids": removed_batch_sensitive_ids,
            "total": len(baseline_now),
            "still_wrong": sum(not row["correct"] for row in baseline_now),
            "details": baseline_now,
        },
    )

    completed, sweep_rows = load_completed(results_path)
    configs = []
    for (method, source_layer), vector in vectors.items():
        for inject_layer in INJECT_LAYERS:
            for alpha in ALPHAS[method]:
                for scope in SCOPES:
                    configs.append((method, source_layer, inject_layer, alpha, scope, vector))
    print(
        f"[TASK PLAN] {task} test={len(eligible_ids)} batches={len(batches)} "
        f"configs={len(configs)} completed={len(completed)}",
        flush=True,
    )
    started = time.monotonic()
    for index, (method, source_layer, inject_layer, alpha, scope, vector) in enumerate(configs, 1):
        key = (method, source_layer, inject_layer, alpha, scope)
        if key in completed:
            continue
        predictions = generate_predictions(
            model,
            tokenizer,
            batches,
            device,
            inject_layer=inject_layer,
            alpha=alpha,
            vector=vector,
            scope=scope,
        )
        scored = [row for row in predictions if row["example_id"] in eligible_ids]
        repaired = [row["example_id"] for row in scored if row["correct"]]
        invalid = [row["example_id"] for row in scored if row["prediction"] is None]
        row = {
            "kind": "config",
            "task": task,
            "method": method,
            "source_layer": source_layer,
            "inject_layer": inject_layer,
            "alpha": alpha,
            "scope": scope,
            "repaired": len(repaired),
            "total": len(scored),
            "repair_rate": len(repaired) / len(scored),
            "valid_outputs": len(scored) - len(invalid),
            "repaired_ids": repaired,
            "invalid_ids": invalid,
            "prediction_counts": dict(Counter(str(x["prediction"]) for x in scored)),
        }
        append_jsonl(results_path, row)
        sweep_rows.append(row)
        completed.add(key)
        if index % 5 == 0 or index == len(configs):
            elapsed = time.monotonic() - started
            print(
                f"[{task}] {index}/{len(configs)} elapsed={elapsed:.0f}s "
                f"{method} src={source_layer} inj={inject_layer} alpha={alpha:g} "
                f"scope={scope} repair={row['repair_rate']:.3f}",
                flush=True,
            )

    best = {}
    for method in ALPHAS:
        for scope in SCOPES:
            eligible = [
                row for row in sweep_rows if row["method"] == method and row["scope"] == scope
            ]
            winner = max(eligible, key=lambda row: (row["repair_rate"], -row["alpha"]))
            best[f"{method}:{scope}"] = winner
    summary = {
        "task": task,
        "test_negative_count": len(eligible_ids),
        "config_count": len(sweep_rows),
        "best": best,
    }
    atomic_json(summary_path, summary)
    print(f"[TASK DONE] {task} best={json.dumps(best)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_PATH)
    parser.add_argument("--baseline", default=str(BASELINE_PATH))
    parser.add_argument("--output-dir", default="yjr_local_test/results/correctness_steering_v2")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-batch-tokens", type=int, default=49152)
    parser.add_argument("--max-batch-size", type=int, default=256)
    parser.add_argument("--tasks", nargs="*", choices=TASK_ORDER)
    args = parser.parse_args()

    rank = int(os.environ.get("RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)
    tokenizer = AutoTokenizer.from_pretrained(args.model, padding_side="left", use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16, attn_implementation="sdpa", low_cpu_mem_usage=True
    ).to(device).eval()
    model.config.use_cache = True
    print(f"[RANK {rank}] loading SAEs", flush=True)
    saes = {
        layer: GemmaScope1SAE(str(path), device=device, dtype=torch.bfloat16).eval()
        for layer, path in SAE_SPECS.items()
    }
    all_examples = load_examples(CURRENT_TQA, V1_TQA, WIKI_FACTOR, args.seed)
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    requested = args.tasks or TASK_ORDER
    if world_size == 2 and not args.tasks:
        assigned = ["wiki_factor"] if rank == 0 else [task for task in TASK_ORDER if task != "wiki_factor"]
    else:
        assigned = requested[rank::world_size]
    print(f"[RANK {rank}] assigned={assigned}", flush=True)
    for task in assigned:
        process_task(task, model, tokenizer, all_examples, baseline, saes, args, device)


if __name__ == "__main__":
    main()
