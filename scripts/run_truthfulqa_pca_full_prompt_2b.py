#!/usr/bin/env python3
"""Run direct-choice baselines and PCA full-prompt steering on local TruthfulQA JSONL."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from run_reasoning_pca_full_prompt_2b import (
    ALPHAS,
    INJECT_LAYERS,
    SOURCE_LAYERS,
    Example,
    atomic_json,
    append_jsonl,
    build_pca_vectors,
    generate_predictions,
    make_batches,
    paired_balanced_samples,
    read_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "yjr_local_test/data/truthfulqa_binary_mc1_790_seed42.jsonl"
DEFAULT_MODEL = os.environ.get("SAFELENS_GEMMA_2_2B_IT_MODEL", "google/gemma-2-2b-it")
TASKS = ["truthfulqa_binary_790", "truthfulqa_mc1_790"]


def load_examples(path: Path) -> dict[str, list[Example]]:
    result = {task: [] for task in TASKS}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            task = row["task"]
            if task not in result:
                continue
            options = row["options"]
            labels = [item["label"] for item in options]
            if labels != [chr(ord("A") + i) for i in range(len(labels))]:
                raise ValueError(f"Non-contiguous option labels in {row['id']}: {labels}")
            if row["answer"] not in labels:
                raise ValueError(f"Invalid answer in {row['id']}: {row['answer']}")
            # This file already contains the exact direct-answer prompt, including Answer:.
            result[task].append(
                Example(
                    example_id=row["id"],
                    source=task,
                    prompt=row["prompt"],
                    answer=row["answer"],
                    option_count=len(options),
                )
            )
    for task, examples in result.items():
        if len(examples) != 790:
            raise ValueError(f"Expected 790 rows for {task}, found {len(examples)}")
    return result


def completed_keys(path: Path) -> set[tuple[int, int, float]]:
    return {
        (row["source_layer"], row["inject_layer"], float(row["alpha"]))
        for row in read_jsonl(path)
    }


def process_task(
    task: str,
    examples: list[Example],
    model: Any,
    tokenizer: Any,
    device: torch.device,
    args: argparse.Namespace,
) -> None:
    task_dir = Path(args.output_dir).resolve() / task
    task_dir.mkdir(parents=True, exist_ok=True)
    print(f"[TASK START] {task} examples={len(examples)}", flush=True)

    full_batches = make_batches(tokenizer, examples, args.max_batch_tokens, args.max_batch_size)
    baseline_details = generate_predictions(model, tokenizer, full_batches, device)
    baseline = {
        "task": task,
        "model": args.model,
        "dataset": str(Path(args.dataset).resolve()),
        "prompt_protocol": "Use the JSONL prompt verbatim; it ends in Answer: and requests only a letter.",
        "total": len(baseline_details),
        "correct": sum(row["correct"] for row in baseline_details),
        "accuracy": sum(row["correct"] for row in baseline_details) / len(baseline_details),
        "valid_outputs": sum(row["prediction"] is not None for row in baseline_details),
        "prediction_counts": dict(Counter(str(row["prediction"]) for row in baseline_details)),
        "details": baseline_details,
    }
    atomic_json(task_dir / "baseline.json", baseline)
    print(
        f"[BASELINE {task}] {baseline['correct']}/{baseline['total']} "
        f"accuracy={baseline['accuracy']:.6f} valid={baseline['valid_outputs']}",
        flush=True,
    )

    positive_rows, negative_rows, quotas = paired_balanced_samples(baseline_details, args.seed)
    positive_ids = [row["example_id"] for row in positive_rows]
    negative_ids = [row["example_id"] for row in negative_rows]
    example_by_id = {example.example_id: example for example in examples}
    vectors, vector_metadata = build_pca_vectors(
        model,
        tokenizer,
        [example_by_id[x] for x in positive_ids],
        [example_by_id[x] for x in negative_ids],
        device,
    )
    torch.save({str(layer): vector for layer, vector in vectors.items()}, task_dir / "vectors.pt")
    atomic_json(task_dir / "vector_metadata.json", vector_metadata)

    train_ids = set(positive_ids + negative_ids)
    heldout_examples = [example for example in examples if example.example_id not in train_ids]
    # Never repack these tensors: alpha=0 and every steering config use identical batches.
    heldout_batches = make_batches(
        tokenizer, heldout_examples, args.max_batch_tokens, args.max_batch_size
    )
    fixed_baseline = generate_predictions(model, tokenizer, heldout_batches, device)
    fixed_by_id = {row["example_id"]: row for row in fixed_baseline}
    wrong_ids = {row["example_id"] for row in fixed_baseline if not row["correct"]}
    correct_ids = {row["example_id"] for row in fixed_baseline if row["correct"]}
    baseline_mismatches = sum(
        fixed_by_id[row["example_id"]]["prediction"] != row["prediction"]
        for row in baseline_details
        if row["example_id"] in fixed_by_id
    )
    atomic_json(
        task_dir / "metadata.json",
        {
            "task": task,
            "method": "pca_minus_neg",
            "scope": "prompt_and_decode",
            "source_layers": SOURCE_LAYERS,
            "inject_layers": INJECT_LAYERS,
            "alphas": ALPHAS,
            "seed": args.seed,
            "train_positive_ids": positive_ids,
            "train_negative_ids": negative_ids,
            "paired_gold_label_quotas": quotas,
            "heldout_ids": sorted(fixed_by_id),
            "heldout_wrong_ids": sorted(wrong_ids),
            "heldout_correct_ids": sorted(correct_ids),
            "counts": {
                "train_positive": len(positive_ids),
                "train_negative": len(negative_ids),
                "heldout": len(fixed_baseline),
                "heldout_wrong": len(wrong_ids),
                "heldout_correct": len(correct_ids),
            },
            "full_vs_fixed_batch_prediction_mismatches": baseline_mismatches,
        },
    )
    atomic_json(
        task_dir / "baseline_validation.json",
        {
            "total": len(fixed_baseline),
            "correct": len(correct_ids),
            "accuracy": len(correct_ids) / len(fixed_baseline),
            "full_vs_fixed_batch_prediction_mismatches": baseline_mismatches,
            "details": fixed_baseline,
        },
    )

    configs = [
        (source_layer, inject_layer, alpha)
        for source_layer in SOURCE_LAYERS
        for inject_layer in INJECT_LAYERS
        for alpha in ALPHAS
    ]
    results_path = task_dir / "sweep.jsonl"
    completed = completed_keys(results_path)
    print(
        f"[SWEEP START {task}] heldout={len(fixed_baseline)} wrong={len(wrong_ids)} "
        f"correct={len(correct_ids)} batches={len(heldout_batches)} configs={len(configs)} "
        f"already_done={len(completed)} quotas={quotas}",
        flush=True,
    )
    started = time.monotonic()
    for index, (source_layer, inject_layer, alpha) in enumerate(configs):
        key = (source_layer, inject_layer, alpha)
        if key in completed:
            continue
        predictions = generate_predictions(
            model,
            tokenizer,
            heldout_batches,
            device,
            inject_layer=inject_layer,
            alpha=alpha,
            vector=vectors[source_layer],
        )
        repaired_ids = [
            row["example_id"] for row in predictions if row["example_id"] in wrong_ids and row["correct"]
        ]
        damaged_ids = [
            row["example_id"] for row in predictions if row["example_id"] in correct_ids and not row["correct"]
        ]
        correct_after = sum(row["correct"] for row in predictions)
        invalid_ids = [row["example_id"] for row in predictions if row["prediction"] is None]
        result = {
            "kind": "config",
            "config_index": index,
            "task": task,
            "method": "pca_minus_neg",
            "scope": "prompt_and_decode",
            "source_layer": source_layer,
            "inject_layer": inject_layer,
            "alpha": alpha,
            "repaired": len(repaired_ids),
            "wrong_before": len(wrong_ids),
            "repair_rate": len(repaired_ids) / len(wrong_ids),
            "damaged": len(damaged_ids),
            "correct_before": len(correct_ids),
            "preservation_rate": (len(correct_ids) - len(damaged_ids)) / len(correct_ids),
            "net_correct_gain": len(repaired_ids) - len(damaged_ids),
            "correct_after": correct_after,
            "heldout_total": len(predictions),
            "heldout_accuracy": correct_after / len(predictions),
            "valid_outputs": len(predictions) - len(invalid_ids),
            "repaired_ids": repaired_ids,
            "damaged_ids": damaged_ids,
            "invalid_ids": invalid_ids,
            "prediction_counts": dict(Counter(str(row["prediction"]) for row in predictions)),
        }
        append_jsonl(results_path, result)
        completed.add(key)
        print(
            f"[{task}] {index+1}/{len(configs)} elapsed={time.monotonic()-started:.0f}s "
            f"src={source_layer} inj={inject_layer} alpha={alpha:g} "
            f"repair={len(repaired_ids)} damage={len(damaged_ids)} "
            f"net={result['net_correct_gain']:+d} acc={result['heldout_accuracy']:.4f}",
            flush=True,
        )

    rows = read_jsonl(results_path)
    latest = {}
    for row in rows:
        latest[(row["source_layer"], row["inject_layer"], float(row["alpha"]))] = row
    rows = sorted(latest.values(), key=lambda row: row["config_index"])
    best_accuracy = max(
        rows, key=lambda row: (row["heldout_accuracy"], row["repair_rate"], -row["alpha"])
    )
    best_repair = max(
        rows, key=lambda row: (row["repair_rate"], row["net_correct_gain"], -row["alpha"])
    )
    atomic_json(
        task_dir / "summary.json",
        {
            "task": task,
            "baseline_correct": baseline["correct"],
            "baseline_total": baseline["total"],
            "baseline_accuracy": baseline["accuracy"],
            "heldout_baseline_correct": len(correct_ids),
            "heldout_total": len(fixed_baseline),
            "heldout_baseline_accuracy": len(correct_ids) / len(fixed_baseline),
            "config_count": len(rows),
            "best_by_heldout_accuracy": best_accuracy,
            "best_by_wrong_repair_rate": best_repair,
        },
    )
    (task_dir / "done").write_text("done\n", encoding="utf-8")
    print(f"[TASK DONE] {task}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", default="yjr_local_test/results/truthfulqa_pca_full_prompt_gemma2_2b")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-batch-tokens", type=int, default=98304)
    parser.add_argument("--max-batch-size", type=int, default=384)
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
        args.model,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        low_cpu_mem_usage=True,
    ).to(device).eval()
    model.config.use_cache = True
    by_task = load_examples(Path(args.dataset))
    assigned = TASKS[rank::world_size]
    print(f"[RANK {rank}] model loaded; assigned={assigned}", flush=True)
    for task in assigned:
        process_task(task, by_task[task], model, tokenizer, device, args)


if __name__ == "__main__":
    main()
