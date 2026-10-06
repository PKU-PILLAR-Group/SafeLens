#!/usr/bin/env python3
"""Run the correctness PCA-minus-negative full-prompt sweep on Qwen3-4B."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import run_correctness_steering as core


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = os.environ.get("SAFELENS_QWEN3_4B_MODEL", "Qwen/Qwen3-4B")
BASELINE_PATH = ROOT / "yjr_local_test/results/qwen3-4b_direct_choice_generation.json"
OUTPUT_DIR = ROOT / "yjr_local_test/results/qwen3-4b_correctness_pca"
SOURCE_LAYERS = [19, 28]
INJECT_LAYERS = [19, 28]
ALPHAS = [25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0,
          250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0]


def render_prompt(tokenizer: Any, example: core.Example) -> str:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": example.prompt}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


@torch.inference_mode()
def build_vectors(
    model: Any,
    tokenizer: Any,
    pos_examples: list[core.Example],
    neg_examples: list[core.Example],
    saes: dict[int, Any],
    device: torch.device,
) -> tuple[dict[tuple[str, int], torch.Tensor], dict[str, Any]]:
    del saes
    prompts = [render_prompt(tokenizer, x) for x in pos_examples + neg_examples]
    hidden = core.capture_boundary_hidden(model, tokenizer, prompts, SOURCE_LAYERS, device)
    vectors: dict[tuple[str, int], torch.Tensor] = {}
    metadata: dict[str, Any] = {}
    n_pos = len(pos_examples)
    for layer in SOURCE_LAYERS:
        delta = hidden[layer][:n_pos] - hidden[layer][n_pos:]
        mean = delta.mean(dim=0)
        _, singular_values, vh = torch.linalg.svd(delta, full_matrices=False)
        pc = vh[0]
        if torch.dot(pc, mean) < 0:
            pc = -pc
        vectors[("pca_minus_neg", layer)] = pc.to(torch.bfloat16)
        metadata[f"pca_minus_neg:{layer}"] = {
            "source_layer": layer,
            "norm": float(pc.norm()),
            "top_singular_value": float(singular_values[0]),
            "sign_aligned_to_mean": True,
            "construction": "top PC of 20 label-matched (positive - negative) boundary activations",
        }
    return vectors, metadata


def main() -> None:
    global SOURCE_LAYERS, INJECT_LAYERS, ALPHAS
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_PATH)
    parser.add_argument("--baseline", default=str(BASELINE_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-batch-tokens", type=int, default=65536)
    parser.add_argument("--max-batch-size", type=int, default=384)
    parser.add_argument("--tasks", nargs="*", choices=core.TASK_ORDER)
    parser.add_argument("--source-layers", nargs="*", type=int)
    parser.add_argument("--inject-layers", nargs="*", type=int)
    parser.add_argument("--alphas", nargs="*", type=float)
    args = parser.parse_args()

    SOURCE_LAYERS = args.source_layers or SOURCE_LAYERS
    INJECT_LAYERS = args.inject_layers or INJECT_LAYERS
    ALPHAS = args.alphas or ALPHAS

    core.SOURCE_LAYERS = SOURCE_LAYERS
    core.INJECT_LAYERS = INJECT_LAYERS
    core.SAE_SPECS = {}
    core.ALPHAS = {"pca_minus_neg": ALPHAS}
    core.SCOPES = ["prompt_and_decode"]
    core.render_prompt = render_prompt
    core.build_vectors = build_vectors

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
    all_examples = core.load_examples(core.CURRENT_TQA, core.V1_TQA, core.WIKI_FACTOR, args.seed)
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    requested = args.tasks or core.TASK_ORDER
    if world_size == 2 and not args.tasks:
        assigned = ["wiki_factor"] if rank == 0 else [
            task for task in core.TASK_ORDER if task != "wiki_factor"
        ]
    else:
        assigned = requested[rank::world_size]
    print(f"[RANK {rank}] assigned={assigned}", flush=True)
    for task in assigned:
        core.process_task(task, model, tokenizer, all_examples, baseline, {}, args, device)


if __name__ == "__main__":
    main()
