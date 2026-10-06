#!/usr/bin/env python3
"""Mean full-prompt steering on baseline-wrong BBH reasoning examples only."""

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
    DEFAULT_DATASET,
    DEFAULT_MODEL,
    INJECT_LAYERS,
    SOURCE_LAYERS,
    atomic_json,
    append_jsonl,
    generate_predictions,
    load_examples,
    make_batches,
    read_jsonl,
    wait_for,
)
from run_truthfulqa_mean_full_prompt_wrong_only_2b import MEAN_ALPHAS, build_mean_vectors


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = ROOT / "yjr_local_test/results/reasoning_pca_full_prompt_gemma2_2b"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--pca-results", default=str(DEFAULT_REFERENCE))
    parser.add_argument(
        "--output-dir", default="yjr_local_test/results/reasoning_mean_full_prompt_wrong_only_gemma2_2b"
    )
    parser.add_argument("--max-batch-tokens", type=int, default=98304)
    parser.add_argument("--max-batch-size", type=int, default=384)
    args = parser.parse_args()

    rank = int(os.environ.get("RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    done_path = output_dir / f"done.rank{rank}"
    done_path.unlink(missing_ok=True)

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

    examples = load_examples(Path(args.dataset))
    example_by_id = {example.example_id: example for example in examples}
    reference_dir = Path(args.pca_results).resolve()
    baseline = json.loads((reference_dir / "baseline.json").read_text(encoding="utf-8"))
    reference_meta = json.loads((reference_dir / "metadata.json").read_text(encoding="utf-8"))
    positive_ids = reference_meta["train_positive_ids"]
    negative_ids = reference_meta["train_negative_ids"]

    vectors, vector_metadata = build_mean_vectors(
        model,
        tokenizer,
        [example_by_id[x] for x in positive_ids],
        [example_by_id[x] for x in negative_ids],
        device,
    )
    if rank == 0:
        torch.save({str(layer): vector for layer, vector in vectors.items()}, output_dir / "vectors.pt")
        atomic_json(output_dir / "vector_metadata.json", vector_metadata)

    train_negative_ids = set(negative_ids)
    initial_wrong_rows = [
        row
        for row in baseline["details"]
        if not row["correct"] and row["example_id"] not in train_negative_ids
    ]
    wrong_examples = [example_by_id[row["example_id"]] for row in initial_wrong_rows]
    batches = make_batches(tokenizer, wrong_examples, args.max_batch_tokens, args.max_batch_size)
    fixed_baseline = generate_predictions(model, tokenizer, batches, device)
    eligible_ids = {row["example_id"] for row in fixed_baseline if not row["correct"]}
    removed_ids = sorted(row["example_id"] for row in fixed_baseline if row["correct"])
    baseline_by_id = {row["example_id"]: row for row in baseline["details"]}
    eligible_gold = Counter(baseline_by_id[x]["answer"] for x in eligible_ids)
    if rank == 0:
        atomic_json(
            output_dir / "metadata.json",
            {
                "task": "reasoning",
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
    assigned = [(i, config) for i, config in enumerate(configs) if i % world_size == rank]
    results_path = output_dir / f"sweep.rank{rank}.jsonl"
    existing = read_jsonl(results_path)
    completed = {
        (row["source_layer"], row["inject_layer"], float(row["alpha"])) for row in existing
    }
    print(
        f"[RANK {rank} SWEEP START] reasoning wrong_only={len(eligible_ids)} "
        f"batches={len(batches)} assigned={len(assigned)} gold={dict(eligible_gold)}",
        flush=True,
    )
    started = time.monotonic()
    for position, (config_index, (source_layer, inject_layer, alpha)) in enumerate(assigned, 1):
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
        result: dict[str, Any] = {
            "kind": "config",
            "config_index": config_index,
            "task": "reasoning",
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
            f"[RANK {rank}] {position}/{len(assigned)} elapsed={time.monotonic()-started:.0f}s "
            f"src={source_layer} inj={inject_layer} alpha={alpha:g} "
            f"repair={len(repaired)}/{len(scored)} ({result['repair_rate']:.3f}) "
            f"max_option_share={max_prediction_share:.3f}",
            flush=True,
        )

    done_path.write_text("done\n", encoding="utf-8")
    print(f"[RANK {rank} DONE]", flush=True)
    if rank == 0:
        wait_for([output_dir / f"done.rank{i}" for i in range(world_size)])
        latest = {}
        for i in range(world_size):
            for row in read_jsonl(output_dir / f"sweep.rank{i}.jsonl"):
                key = (row["source_layer"], row["inject_layer"], float(row["alpha"]))
                latest[key] = row
        rows = sorted(latest.values(), key=lambda row: row["config_index"])
        (output_dir / "sweep.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
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
                "task": "reasoning",
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
        print(f"[ALL DONE] best={json.dumps(best_raw, ensure_ascii=False)}", flush=True)


if __name__ == "__main__":
    main()
