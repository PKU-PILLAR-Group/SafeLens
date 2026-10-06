#!/usr/bin/env python3
"""Export the minimal reasoning data and configs needed for final analysis."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "yjr_local_test/build_benchmark/trustworthy_benchmark_success (1).json"
PCA_DIR = ROOT / "yjr_local_test/results/reasoning_pca_full_prompt_gemma2_9b"
MEAN_DIR = ROOT / "yjr_local_test/results/reasoning_mean_full_prompt_gemma2_9b"
OUTPUT_DIR = ROOT / "yjr_local_test/build_benchmark/for_final/reasoning"
SEED = 42


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact_source(row: dict[str, Any]) -> dict[str, Any]:
    answer = "".join(c for c in str(row["ground_truth"]).upper() if "A" <= c <= "Z")
    return {
        "id": int(row["id"]),
        "source": row.get("source"),
        "input": row["input"],
        "ground_truth": answer,
    }


def main() -> None:
    source_rows = read_json(DATASET)
    reasoning_by_id = {
        int(row["id"]): row for row in source_rows if row.get("category") == "reasoning"
    }
    baseline = read_json(PCA_DIR / "baseline.json")
    baseline_by_id = {int(row["example_id"]): row for row in baseline["details"]}
    pca_meta = read_json(PCA_DIR / "metadata.json")
    pca_summary = read_json(PCA_DIR / "summary.json")
    mean_summary = read_json(MEAN_DIR / "summary.json")

    train_positive_ids = [int(x) for x in pca_meta["train_positive_ids"]]
    train_negative_ids = [int(x) for x in pca_meta["train_negative_ids"]]
    test_negative_ids = [int(x) for x in pca_meta["test_negative_ids"]]
    pca_best = pca_summary["best"]
    mean_best = mean_summary["best_raw_repair"]
    pca_repaired = {int(x) for x in pca_best["repaired_ids"]}
    mean_repaired = {int(x) for x in mean_best["repaired_ids"]}

    assert set(train_negative_ids).isdisjoint(test_negative_ids)
    assert len(train_negative_ids) == 20 and len(test_negative_ids) == 77
    assert pca_repaired <= set(test_negative_ids)
    assert mean_repaired <= set(test_negative_ids)

    wrong_cases = []
    for example_id in sorted(train_negative_ids + test_negative_ids):
        baseline_row = baseline_by_id[example_id]
        record = compact_source(reasoning_by_id[example_id])
        is_test = example_id in set(test_negative_ids)
        record.update(
            {
                "baseline_prediction": baseline_row["prediction"],
                "split": "repair_test" if is_test else "steering_train_negative",
                "pca_full_prompt_repaired": example_id in pca_repaired if is_test else None,
                "mean_full_prompt_repaired": example_id in mean_repaired if is_test else None,
            }
        )
        wrong_cases.append(record)

    all_correct_ids = sorted(
        int(row["example_id"]) for row in baseline["details"] if row["correct"]
    )
    remaining_correct_ids = [x for x in all_correct_ids if x not in set(train_positive_ids)]
    sampled_ids = random.Random(SEED).sample(remaining_correct_ids, 80)
    selected_correct_ids = set(train_positive_ids + sampled_ids)
    assert len(selected_correct_ids) == 100
    correct_cases = []
    for example_id in sorted(selected_correct_ids):
        baseline_row = baseline_by_id[example_id]
        record = compact_source(reasoning_by_id[example_id])
        record.update(
            {
                "baseline_prediction": baseline_row["prediction"],
                "split": (
                    "steering_train_positive"
                    if example_id in set(train_positive_ids)
                    else "reference_correct"
                ),
            }
        )
        correct_cases.append(record)

    config = {
        "dataset": {
            "path": str(DATASET),
            "filter": {"category": "reasoning"},
            "total_examples": 237,
        },
        "model": "google/gemma-2-9b-it",
        "prompt_and_decoding": {
            "user_prompt": "Choose the correct answer. Reply with only the option letter.\n\n{native_input}\n\nAnswer:",
            "chat_template": "Gemma tokenizer.apply_chat_template(add_generation_prompt=True)",
            "decoding": "greedy, do_sample=False, max_new_tokens=8",
            "answer_parser": "first valid option letter, limited by each question's option count",
        },
        "vector_extraction": {
            "position": "final token of the rendered prompt (the Answer: boundary)",
            "train_positive_count": 20,
            "train_negative_count": 20,
            "paired_gold_label_quotas": pca_meta["paired_gold_label_quotas"],
            "train_positive_ids": train_positive_ids,
            "train_negative_ids": train_negative_ids,
        },
        "evaluation": {
            "full_direct_answer_baseline": {
                "correct": baseline["correct"],
                "total": baseline["total"],
                "accuracy": baseline["accuracy"],
            },
            "repair_test": "77 held-out baseline-wrong examples; baseline repair accuracy is 0/77",
            "injection_scope": "all prompt tokens during prefill and every generated token during decoding",
            "layer_indexing": "zero-based model.model.layers indices",
        },
        "pca_full_prompt": {
            "construction": "top right singular vector of paired (positive_hidden - negative_hidden), sign-aligned to the mean delta; unit norm",
            "source_layer": int(pca_best["source_layer"]),
            "injection_layer": int(pca_best["inject_layer"]),
            "alpha": float(pca_best["alpha"]),
            "scan": {
                "source_layers": [22, 32],
                "injection_layers": [22, 32],
                "alphas": [100, 130, 160, 190, 220, 250, 280, 310, 340],
            },
            "best_result": {"repaired": len(pca_repaired), "total": 77},
        },
        "mean_full_prompt": {
            "construction": "mean(positive_hidden - paired_negative_hidden), without unit normalization",
            "source_layer": int(mean_best["source_layer"]),
            "injection_layer": int(mean_best["inject_layer"]),
            "alpha": float(mean_best["alpha"]),
            "scan": {
                "source_layers": [22, 32],
                "injection_layers": [22, 32],
                "alphas": [1.0, 1.5, 2.0, 2.5, 3.0],
            },
            "best_result": {"repaired": len(mean_repaired), "total": 77},
        },
        "repair_overlap": {
            "pca_repaired": len(pca_repaired),
            "mean_repaired": len(mean_repaired),
            "intersection": len(pca_repaired & mean_repaired),
            "union": len(pca_repaired | mean_repaired),
        },
        "export": {
            "correct_cases_selection": "all 20 steering positives plus 80 sampled without replacement from the other baseline-correct examples",
            "random_seed": SEED,
            "null_repair_flag": "not evaluated because the example belongs to steering-vector training",
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "wrong_cases.json", wrong_cases)
    write_json(OUTPUT_DIR / "correct_cases_100.json", correct_cases)
    write_json(OUTPUT_DIR / "steering_configs.json", config)
    print(
        json.dumps(
            {
                "output_dir": str(OUTPUT_DIR),
                "wrong_cases": len(wrong_cases),
                "repair_test_cases": len(test_negative_ids),
                "correct_cases": len(correct_cases),
                "pca_repaired": len(pca_repaired),
                "mean_repaired": len(mean_repaired),
                "union": len(pca_repaired | mean_repaired),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
