#!/usr/bin/env python3
"""Mean correctness steering on baseline-wrong TruthfulQA examples only."""

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
    INJECT_LAYERS,
    SOURCE_LAYERS,
    atomic_json,
    append_jsonl,
    capture_hidden,
    generate_predictions,
    make_batches,
    read_jsonl,
)
from run_truthfulqa_pca_full_prompt_2b import DEFAULT_DATASET, DEFAULT_MODEL, TASKS, load_examples


ROOT = Path(__file__).resolve().parents[1]
MEAN_ALPHAS = [1.0, 1.5, 2.0, 2.5, 3.0]
DEFAULT_PCA_RESULTS = ROOT / "yjr_local_test/results/truthfulqa_pca_full_prompt_gemma2_2b"


@torch.inference_mode()
def build_mean_vectors(
    model: Any,
    tokenizer: Any,
    positive: list[Any],
    negative: list[Any],
    device: torch.device,
) -> tuple[dict[int, torch.Tensor], dict[str, Any]]:
    hidden = capture_hidden(model, tokenizer, positive + negative, SOURCE_LAYERS, device)
    n = len(positive)
    vectors, metadata = {}, {}
    for layer in SOURCE_LAYERS:
        vector = (hidden[layer][:n] - hidden[layer][n:]).mean(dim=0)
        vectors[layer] = vector.to(torch.bfloat16)
        metadata[str(layer)] = {
            "source_layer": layer,
            "norm": float(vector.norm()),
            "construction": "mean(positive_hidden - paired_negative_hidden)",
        }
    return vectors, metadata


def process_task(
    task: str,
    examples: list[Any],
    model: Any,
    tokenizer: Any,
    device: torch.device,
    args: argparse.Namespace,
) -> None:
    reference_dir = Path(args.pca_results).resolve() / task
    baseline = json.loads((reference_dir / "baseline.json").read_text(encoding="utf-8"))
    reference_meta = json.loads((reference_dir / "metadata.json").read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir).resolve() / task
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "done").unlink(missing_ok=True)

    example_by_id = {example.example_id: example for example in examples}
    positive_ids = reference_meta["train_positive_ids"]
    negative_ids = reference_meta["train_negative_ids"]
    vectors, vector_metadata = build_mean_vectors(
        model,
        tokenizer,
        [example_by_id[x] for x in positive_ids],
        [example_by_id[x] for x in negative_ids],
        device,
    )
    torch.save({str(layer): vector for layer, vector in vectors.items()}, output_dir / "vectors.pt")
    atomic_json(output_dir / "vector_metadata.json", vector_metadata)

    train_negative_ids = set(negative_ids)
    initial_wrong_rows = [
        row
        for row in baseline["details"]
        if not row["correct"] and row["example_id"] not in train_negative_ids
    ]
    wrong_examples = [example_by_id[row["example_id"]] for row in initial_wrong_rows]
    # Exact same tensor batches are reused for alpha=0 and every steering setting.
    batches = make_batches(tokenizer, wrong_examples, args.max_batch_tokens, args.max_batch_size)
    fixed_baseline = generate_predictions(model, tokenizer, batches, device)
    eligible_ids = {row["example_id"] for row in fixed_baseline if not row["correct"]}
    removed_ids = sorted(row["example_id"] for row in fixed_baseline if row["correct"])
    baseline_by_id = {row["example_id"]: row for row in baseline["details"]}
    eligible_gold = Counter(baseline_by_id[x]["answer"] for x in eligible_ids)
    atomic_json(
        output_dir / "metadata.json",
        {
            "task": task,
            "model": args.model,
            "method": "mean_minus_neg",
            "scope": "prompt_and_decode",
            "source_layers": SOURCE_LAYERS,
            "inject_layers": INJECT_LAYERS,
            "alphas": MEAN_ALPHAS,
            "training_sample_reference": str(reference_dir / "metadata.json"),
            "train_positive_ids": positive_ids,
            "train_negative_ids": negative_ids,
            "paired_gold_label_quotas": reference_meta["paired_gold_label_quotas"],
            "initial_heldout_wrong_count": len(initial_wrong_rows),
            "fixed_batch_wrong_count": len(eligible_ids),
            "removed_batch_sensitive_ids": removed_ids,
            "eligible_gold_counts": dict(sorted(eligible_gold.items())),
        },
    )
    atomic_json(
        output_dir / "baseline_validation.json",
        {
            "initial_heldout_wrong_count": len(initial_wrong_rows),
            "fixed_batch_wrong_count": len(eligible_ids),
            "removed_batch_sensitive_ids": removed_ids,
            "details": fixed_baseline,
        },
    )

    configs = [
        (source_layer, inject_layer, alpha)
        for source_layer in SOURCE_LAYERS
        for inject_layer in INJECT_LAYERS
        for alpha in MEAN_ALPHAS
    ]
    results_path = output_dir / "sweep.jsonl"
    previous = read_jsonl(results_path)
    completed = {
        (row["source_layer"], row["inject_layer"], float(row["alpha"])) for row in previous
    }
    print(
        f"[SWEEP START {task}] wrong_only={len(eligible_ids)} batches={len(batches)} "
        f"configs={len(configs)} already_done={len(completed)} gold={dict(eligible_gold)}",
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
            batches,
            device,
            inject_layer=inject_layer,
            alpha=alpha,
            vector=vectors[source_layer],
        )
        scored = [row for row in predictions if row["example_id"] in eligible_ids]
        repaired = [row for row in scored if row["correct"]]
        invalid = [row for row in scored if row["prediction"] is None]
        prediction_counts = Counter(str(row["prediction"]) for row in scored)
        repaired_gold_counts = Counter(row["answer"] for row in repaired)
        max_prediction_share = max(prediction_counts.values(), default=0) / len(scored)
        result = {
            "kind": "config",
            "config_index": index,
            "task": task,
            "method": "mean_minus_neg",
            "scope": "prompt_and_decode",
            "source_layer": source_layer,
            "inject_layer": inject_layer,
            "alpha": alpha,
            "repaired": len(repaired),
            "total": len(scored),
            "repair_rate": len(repaired) / len(scored),
            "valid_outputs": len(scored) - len(invalid),
            "max_prediction_share": max_prediction_share,
            "repaired_ids": [row["example_id"] for row in repaired],
            "invalid_ids": [row["example_id"] for row in invalid],
            "prediction_counts": dict(prediction_counts),
            "repaired_gold_counts": dict(sorted(repaired_gold_counts.items())),
        }
        append_jsonl(results_path, result)
        completed.add(key)
        print(
            f"[{task}] {index+1}/{len(configs)} elapsed={time.monotonic()-started:.0f}s "
            f"src={source_layer} inj={inject_layer} alpha={alpha:g} "
            f"repair={len(repaired)}/{len(scored)} ({result['repair_rate']:.3f}) "
            f"max_option_share={max_prediction_share:.3f}",
            flush=True,
        )

    latest = {}
    for row in read_jsonl(results_path):
        latest[(row["source_layer"], row["inject_layer"], float(row["alpha"]))] = row
    rows = sorted(latest.values(), key=lambda row: row["config_index"])
    best_raw = max(rows, key=lambda row: (row["repair_rate"], -row["alpha"]))
    noncollapsed = [row for row in rows if row["max_prediction_share"] < 0.95]
    best_noncollapsed = (
        max(noncollapsed, key=lambda row: (row["repair_rate"], -row["alpha"]))
        if noncollapsed
        else None
    )
    atomic_json(
        output_dir / "summary.json",
        {
            "task": task,
            "original_full_baseline_correct": baseline["correct"],
            "original_full_baseline_total": baseline["total"],
            "original_full_baseline_accuracy": baseline["accuracy"],
            "wrong_only_test_count": len(eligible_ids),
            "wrong_only_gold_counts": dict(sorted(eligible_gold.items())),
            "config_count": len(rows),
            "best_raw_repair": best_raw,
            "best_with_max_prediction_share_below_0.95": best_noncollapsed,
        },
    )
    (output_dir / "done").write_text("done\n", encoding="utf-8")
    print(f"[TASK DONE] {task}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--pca-results", default=str(DEFAULT_PCA_RESULTS))
    parser.add_argument(
        "--output-dir", default="yjr_local_test/results/truthfulqa_mean_full_prompt_wrong_only_gemma2_2b"
    )
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
