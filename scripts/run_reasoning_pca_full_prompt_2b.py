#!/usr/bin/env python3
"""Evaluate BBH reasoning MCQs and sweep PCA correctness steering on Gemma 2 2B."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from collections import Counter
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "yjr_local_test/build_benchmark/trustworthy_benchmark_success (1).json"
DEFAULT_MODEL = os.environ.get("SAFELENS_GEMMA_2_2B_IT_MODEL", "google/gemma-2-2b-it")
SOURCE_LAYERS = [14, 20]
INJECT_LAYERS = [14, 20]
ALPHAS = [100.0, 130.0, 160.0, 190.0, 220.0, 250.0, 280.0, 310.0, 340.0]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass
class Example:
    example_id: int
    source: str
    prompt: str
    answer: str
    option_count: int


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


def wait_for(paths: list[Path], timeout: float = 86400.0) -> None:
    started = time.monotonic()
    while not all(path.exists() for path in paths):
        if time.monotonic() - started > timeout:
            missing = [str(path) for path in paths if not path.exists()]
            raise TimeoutError(f"Timed out waiting for {missing}")
        time.sleep(2)


def parse_letter(text: str, option_count: int) -> str | None:
    cleaned = text.strip()
    patterns = [
        r"^(?:answer\s*[:=-]\s*)?[\(\[\{*]*([A-Z])(?:[\)\]\}*.:,\s]|$)",
        r"^(?:the\s+)?(?:correct\s+)?answer\s+is\s+[\(\[\{*]*([A-Z])(?:[\)\]\}*.:,\s]|$)",
    ]
    for pattern in patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            letter = match.group(1).upper()
            if letter in LETTERS[:option_count]:
                return letter
    return None


def load_examples(path: Path) -> list[Example]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    examples = []
    for row in rows:
        if row.get("category") != "reasoning":
            continue
        raw = row["input"].rstrip()
        option_letters = re.findall(r"(?m)^\s*\(([A-Z])\)\s*", raw)
        answer = re.sub(r"[^A-Z]", "", str(row["ground_truth"]).upper())
        if not option_letters or len(answer) != 1 or answer not in option_letters:
            raise ValueError(f"Malformed example id={row.get('id')}")
        prompt = (
            "Choose the correct answer. Reply with only the option letter.\n\n"
            f"{raw}\n\nAnswer:"
        )
        examples.append(
            Example(
                example_id=int(row["id"]),
                source=str(row.get("source", "")),
                prompt=prompt,
                answer=answer,
                option_count=len(option_letters),
            )
        )
    if len({x.example_id for x in examples}) != len(examples):
        raise ValueError("Reasoning example IDs are not unique")
    return examples


def render_prompt(tokenizer: Any, example: Example) -> str:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": example.prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )


def make_batches(
    tokenizer: Any,
    examples: list[Example],
    max_batch_tokens: int,
    max_batch_size: int,
) -> list[dict[str, Any]]:
    items = []
    for example in examples:
        ids = tokenizer(render_prompt(tokenizer, example), add_special_tokens=False)["input_ids"]
        items.append((len(ids), example, ids))
    items.sort(key=lambda item: item[0])
    raw_batches: list[list[tuple[int, Example, list[int]]]] = []
    batch: list[tuple[int, Example, list[int]]] = []
    for item in items:
        proposed_size = len(batch) + 1
        if batch and (
            proposed_size > max_batch_size or proposed_size * item[0] > max_batch_tokens
        ):
            raw_batches.append(batch)
            batch = [item]
        else:
            batch.append(item)
    if batch:
        raw_batches.append(batch)

    result = []
    for batch in raw_batches:
        width = max(item[0] for item in batch)
        input_ids = torch.full((len(batch), width), tokenizer.pad_token_id, dtype=torch.long)
        attention_mask = torch.zeros_like(input_ids)
        for i, (_, _, ids) in enumerate(batch):
            input_ids[i, -len(ids):] = torch.tensor(ids)
            attention_mask[i, -len(ids):] = 1
        result.append(
            {
                "examples": [item[1] for item in batch],
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            }
        )
    return result


def steering_hook(
    module: Any,
    module_inputs: Any,
    module_output: Any,
    alpha: float,
    vector: torch.Tensor,
) -> Any:
    hidden = module_output[0] if isinstance(module_output, tuple) else module_output
    rest = module_output[1:] if isinstance(module_output, tuple) else None
    hidden = hidden + alpha * vector.to(device=hidden.device, dtype=hidden.dtype)
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
                partial(steering_hook, alpha=alpha, vector=vector)
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
            generated[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )
        for example, response in zip(batch["examples"], responses):
            prediction = parse_letter(response, example.option_count)
            records.append(
                {
                    "example_id": example.example_id,
                    "answer": example.answer,
                    "prediction": prediction,
                    "response": response,
                    "correct": prediction == example.answer,
                }
            )
    return records


def paired_balanced_samples(
    rows: list[dict[str, Any]], seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    by_status: dict[bool, dict[str, list[dict[str, Any]]]] = {True: {}, False: {}}
    labels = sorted({row["answer"] for row in rows})
    for status in [True, False]:
        for label in labels:
            candidates = [
                row for row in rows if bool(row["correct"]) == status and row["answer"] == label
            ]
            random.Random(f"{seed}:{status}:{label}").shuffle(candidates)
            by_status[status][label] = candidates
    capacity = {
        label: min(len(by_status[True][label]), len(by_status[False][label])) for label in labels
    }
    quota = {label: 0 for label in labels}
    for _ in range(20):
        available = [label for label in labels if quota[label] < capacity[label]]
        if not available:
            raise ValueError(f"Cannot draw 20 paired label-balanced examples; capacities={capacity}")
        label = min(available, key=lambda x: (quota[x], x))
        quota[label] += 1
    positive, negative = [], []
    for label in labels:
        positive.extend(by_status[True][label][:quota[label]])
        negative.extend(by_status[False][label][:quota[label]])
    return positive, negative, {key: value for key, value in quota.items() if value}


@torch.inference_mode()
def capture_hidden(
    model: Any,
    tokenizer: Any,
    examples: list[Example],
    layers: list[int],
    device: torch.device,
) -> dict[int, torch.Tensor]:
    prompts = [render_prompt(tokenizer, example) for example in examples]
    inputs = tokenizer(
        prompts, return_tensors="pt", padding=True, add_special_tokens=False, truncation=False
    ).to(device)
    captured: dict[int, torch.Tensor] = {}
    handles = []

    def hook(layer: int, module: Any, module_inputs: Any, module_output: Any) -> None:
        hidden = module_output[0] if isinstance(module_output, tuple) else module_output
        captured[layer] = hidden[:, -1, :].detach().float().cpu()

    for layer in layers:
        handles.append(model.model.layers[layer].register_forward_hook(partial(hook, layer)))
    try:
        model.model(**inputs, use_cache=False, return_dict=True)
    finally:
        for handle in handles:
            handle.remove()
    return captured


def build_pca_vectors(
    model: Any,
    tokenizer: Any,
    positive: list[Example],
    negative: list[Example],
    device: torch.device,
) -> tuple[dict[int, torch.Tensor], dict[str, Any]]:
    hidden = capture_hidden(model, tokenizer, positive + negative, SOURCE_LAYERS, device)
    vectors, metadata = {}, {}
    n = len(positive)
    for layer in SOURCE_LAYERS:
        delta = hidden[layer][:n] - hidden[layer][n:]
        mean = delta.mean(dim=0)
        _, singular_values, vh = torch.linalg.svd(delta, full_matrices=False)
        vector = vh[0]
        if torch.dot(vector, mean) < 0:
            vector = -vector
        vectors[layer] = vector.to(torch.bfloat16)
        metadata[str(layer)] = {
            "source_layer": layer,
            "norm": float(vector.norm()),
            "top_singular_value": float(singular_values[0]),
            "sign_aligned_to_mean": True,
        }
    return vectors, metadata


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", default="yjr_local_test/results/reasoning_pca_full_prompt_gemma2_2b")
    parser.add_argument("--seed", type=int, default=42)
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
    print(f"[RANK {rank}] loaded model; reasoning_examples={len(examples)}", flush=True)

    # Both GPUs evaluate disjoint baseline shards, then rank 0 merges them.
    shard = examples[rank::world_size]
    baseline_shard = generate_predictions(
        model,
        tokenizer,
        make_batches(tokenizer, shard, args.max_batch_tokens, args.max_batch_size),
        device,
    )
    shard_path = output_dir / f"baseline.rank{rank}.json"
    atomic_json(shard_path, baseline_shard)
    baseline_path = output_dir / "baseline.json"
    shard_paths = [output_dir / f"baseline.rank{i}.json" for i in range(world_size)]
    if rank == 0:
        wait_for(shard_paths)
        details = []
        for path in shard_paths:
            details.extend(json.loads(path.read_text(encoding="utf-8")))
        details.sort(key=lambda row: row["example_id"])
        baseline = {
            "model": args.model,
            "dataset": str(Path(args.dataset).resolve()),
            "prompt": "Native input prefixed with a one-letter instruction and suffixed with Answer:",
            "total": len(details),
            "correct": sum(row["correct"] for row in details),
            "accuracy": sum(row["correct"] for row in details) / len(details),
            "valid_outputs": sum(row["prediction"] is not None for row in details),
            "prediction_counts": dict(Counter(str(row["prediction"]) for row in details)),
            "details": details,
        }
        atomic_json(baseline_path, baseline)
        print(
            f"[BASELINE] correct={baseline['correct']}/{baseline['total']} "
            f"accuracy={baseline['accuracy']:.6f} valid={baseline['valid_outputs']}",
            flush=True,
        )
    wait_for([baseline_path])
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    positive_rows, negative_rows, quotas = paired_balanced_samples(baseline["details"], args.seed)
    positive_ids = [row["example_id"] for row in positive_rows]
    negative_ids = [row["example_id"] for row in negative_rows]
    vectors, vector_metadata = build_pca_vectors(
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
    test_examples = [
        example_by_id[row["example_id"]]
        for row in baseline["details"]
        if not row["correct"] and row["example_id"] not in train_negative_ids
    ]
    # These tensor batches are reused exactly for alpha=0 and every sweep point.
    test_batches = make_batches(tokenizer, test_examples, args.max_batch_tokens, args.max_batch_size)
    fixed_baseline = generate_predictions(model, tokenizer, test_batches, device)
    eligible_ids = {row["example_id"] for row in fixed_baseline if not row["correct"]}
    removed = sorted(row["example_id"] for row in fixed_baseline if row["correct"])
    if rank == 0:
        atomic_json(
            output_dir / "metadata.json",
            {
                "method": "pca_minus_neg",
                "scope": "prompt_and_decode",
                "source_layers": SOURCE_LAYERS,
                "inject_layers": INJECT_LAYERS,
                "alphas": ALPHAS,
                "seed": args.seed,
                "train_positive_ids": positive_ids,
                "train_negative_ids": negative_ids,
                "paired_gold_label_quotas": quotas,
                "test_negative_ids": sorted(eligible_ids),
                "removed_batch_sensitive_ids": removed,
                "counts": {
                    "train_positive": len(positive_ids),
                    "train_negative": len(negative_ids),
                    "test_negative": len(eligible_ids),
                },
            },
        )
        atomic_json(
            output_dir / "baseline_validation.json",
            {
                "total": len(fixed_baseline),
                "still_wrong": len(eligible_ids),
                "removed_batch_sensitive_ids": removed,
                "details": fixed_baseline,
            },
        )

    configs = [
        (source_layer, inject_layer, alpha)
        for source_layer in SOURCE_LAYERS
        for inject_layer in INJECT_LAYERS
        for alpha in ALPHAS
    ]
    assigned = [(i, config) for i, config in enumerate(configs) if i % world_size == rank]
    results_path = output_dir / f"sweep.rank{rank}.jsonl"
    existing = read_jsonl(results_path)
    completed = {
        (row["source_layer"], row["inject_layer"], float(row["alpha"])) for row in existing
    }
    print(
        f"[RANK {rank} SWEEP START] fixed_wrong={len(eligible_ids)} batches={len(test_batches)} "
        f"assigned={len(assigned)} already_done={len(completed)} quotas={quotas}",
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
            test_batches,
            device,
            inject_layer=inject_layer,
            alpha=alpha,
            vector=vectors[source_layer],
        )
        scored = [row for row in predictions if row["example_id"] in eligible_ids]
        repaired = [row["example_id"] for row in scored if row["correct"]]
        invalid = [row["example_id"] for row in scored if row["prediction"] is None]
        result = {
            "kind": "config",
            "config_index": config_index,
            "method": "pca_minus_neg",
            "scope": "prompt_and_decode",
            "source_layer": source_layer,
            "inject_layer": inject_layer,
            "alpha": alpha,
            "repaired": len(repaired),
            "total": len(scored),
            "repair_rate": len(repaired) / len(scored) if scored else 0.0,
            "valid_outputs": len(scored) - len(invalid),
            "repaired_ids": repaired,
            "invalid_ids": invalid,
            "prediction_counts": dict(Counter(str(row["prediction"]) for row in scored)),
        }
        append_jsonl(results_path, result)
        completed.add(key)
        print(
            f"[RANK {rank}] {position}/{len(assigned)} elapsed={time.monotonic()-started:.0f}s "
            f"src={source_layer} inj={inject_layer} alpha={alpha:g} "
            f"repair={result['repaired']}/{result['total']} ({result['repair_rate']:.3f})",
            flush=True,
        )

    done_path.write_text("done\n", encoding="utf-8")
    print(f"[RANK {rank} DONE]", flush=True)
    if rank == 0:
        wait_for([output_dir / f"done.rank{i}" for i in range(world_size)])
        rows = []
        for i in range(world_size):
            rows.extend(read_jsonl(output_dir / f"sweep.rank{i}.jsonl"))
        latest = {}
        for row in rows:
            key = (row["source_layer"], row["inject_layer"], float(row["alpha"]))
            latest[key] = row
        rows = sorted(latest.values(), key=lambda row: row["config_index"])
        merged_path = output_dir / "sweep.jsonl"
        merged_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        best = max(rows, key=lambda row: (row["repair_rate"], -row["alpha"]))
        atomic_json(
            output_dir / "summary.json",
            {
                "baseline_correct": baseline["correct"],
                "baseline_total": baseline["total"],
                "baseline_accuracy": baseline["accuracy"],
                "test_negative_count": len(eligible_ids),
                "config_count": len(rows),
                "best": best,
            },
        )
        print(f"[ALL DONE] best={json.dumps(best, ensure_ascii=False)}", flush=True)


if __name__ == "__main__":
    main()
