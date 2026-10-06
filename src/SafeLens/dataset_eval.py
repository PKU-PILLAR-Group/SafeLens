"""Compatibility exports for the final-300 dataset evaluator."""

from SafeLens.final_dataset_eval import (
    ALGORITHM_CATALOG,
    DATASET_CATALOG,
    FINAL_DATASET_ID,
    METHOD_CONFIGS,
    dataset_catalog,
    get_algorithm,
    get_dataset,
    run_dataset_test,
)

__all__ = [
    "ALGORITHM_CATALOG",
    "DATASET_CATALOG",
    "FINAL_DATASET_ID",
    "METHOD_CONFIGS",
    "dataset_catalog",
    "get_algorithm",
    "get_dataset",
    "run_dataset_test",
]
