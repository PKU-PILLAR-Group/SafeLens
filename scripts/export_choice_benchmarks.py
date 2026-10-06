#!/usr/bin/env python3
"""Export the three evaluated multiple-choice formats into one JSONL file."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import pandas as pd


LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def shuffled(options: list[tuple[str, int]], seed: int, task: str, index: int):
    result = list(options)
    random.Random(f"{seed}:{task}:{index}").shuffle(result)
    return result


def make_prompt(instruction: str, stem_label: str, stem: str, options: list[str]) -> str:
    rendered = "\n".join(f"{LETTERS[i]}. {text}" for i, text in enumerate(options))
    return f"{instruction}\n\n{stem_label}:\n{stem}\n\nOptions:\n{rendered}\n\nAnswer:"


def make_record(
    *,
    task: str,
    index: int,
    source: str,
    stem_type: str,
    stem: str,
    options_with_labels: list[tuple[str, int]],
    seed: int,
) -> dict[str, Any]:
    options_with_labels = shuffled(options_with_labels, seed, task, index)
    labels = [label for _, label in options_with_labels]
    if sum(labels) != 1:
        raise ValueError(f"{task}:{index} does not contain exactly one correct answer")
    options = [text for text, _ in options_with_labels]
    correct_index = labels.index(1)
    instruction = (
        "Choose the factually correct continuation of the passage. Reply with only the option letter."
        if task == "wiki_factor"
        else "Choose the truthful answer. Reply with only the option letter."
    )
    return {
        "id": f"{task}:{index}",
        "task": task,
        "source": source,
        "source_index": index,
        "stem_type": stem_type,
        "stem": stem,
        "options": options,
        "option_labels": list(LETTERS[: len(options)]),
        "answer": LETTERS[correct_index],
        "answer_index": correct_index,
        "answer_text": options[correct_index],
        "prompt": make_prompt(instruction, stem_type.title(), stem, options),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truthfulqa", default="yjr_local_test/external/TruthfulQA/data/mc_task.json")
    parser.add_argument("--wiki-factor", default="yjr_local_test/external/factor/data/wiki_factor.csv")
    parser.add_argument("--output", default="data/choice_benchmarks.jsonl")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    truthful = json.loads(Path(args.truthfulqa).read_text(encoding="utf-8"))
    wiki = pd.read_csv(args.wiki_factor)
    records: list[dict[str, Any]] = []

    for i, row in enumerate(truthful):
        records.append(
            make_record(
                task="truthfulqa_binary",
                index=i,
                source="TruthfulQA/data/mc_task.json (current, 790 questions)",
                stem_type="question",
                stem=row["question"],
                options_with_labels=list(row["mc0_targets"].items()),
                seed=args.seed,
            )
        )
        records.append(
            make_record(
                task="truthfulqa_mc1",
                index=i,
                source="TruthfulQA/data/mc_task.json (current, 790 questions)",
                stem_type="question",
                stem=row["question"],
                options_with_labels=list(row["mc1_targets"].items()),
                seed=args.seed,
            )
        )

    for i, row in wiki.iterrows():
        candidates = [(str(row["completion"]).lstrip(" "), 1)] + [
            (str(row[f"contradiction_{j}"]).lstrip(" "), 0) for j in range(3)
        ]
        record = make_record(
            task="wiki_factor",
            index=int(i),
            source="AI21Labs/factor/data/wiki_factor.csv (2994 questions)",
            stem_type="passage",
            stem=str(row["turncated_prefixes"]),
            options_with_labels=candidates,
            seed=args.seed,
        )
        record["document_id"] = int(row["doc_id"])
        records.append(record)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    counts = {task: sum(record["task"] == task for record in records) for task in {
        "truthfulqa_binary", "truthfulqa_mc1", "wiki_factor"
    }}
    print(json.dumps({"output": str(output), "total": len(records), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
