#!/usr/bin/env python3
"""Run the reasoning PCA full-prompt sweep with Gemma 2 9B layer settings."""

import os

import run_reasoning_pca_full_prompt_2b as experiment


experiment.DEFAULT_MODEL = os.environ.get(
    "SAFELENS_GEMMA_2_9B_IT_MODEL", "google/gemma-2-9b-it"
)
experiment.SOURCE_LAYERS = [22, 32]
experiment.INJECT_LAYERS = [22, 32]


if __name__ == "__main__":
    experiment.main()
