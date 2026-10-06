from __future__ import annotations

import math
import threading
from types import SimpleNamespace

import SafeLens.final_dataset_eval as final_eval
from SafeLens.final_dataset_eval import (
    FINAL_DATASET_ID,
    METHOD_CONFIGS,
    PACKAGE_VECTOR_ROOT,
    _parse_letter,
    _summarize,
    dataset_catalog,
)


def test_final_300_catalog_has_fixed_dataset_and_two_methods() -> None:
    catalog = dataset_catalog()
    dataset = catalog["datasets"][0]

    assert dataset["id"] == FINAL_DATASET_ID
    assert len(dataset["samples"]) == 300
    assert {sample["task"] for sample in dataset["samples"]} == {
        "reasoning",
        "faithful",
        "safety",
    }
    assert {
        task: sum(sample["task"] == task for sample in dataset["samples"])
        for task in ("reasoning", "faithful", "safety")
    } == {"reasoning": 100, "faithful": 100, "safety": 100}
    assert {algorithm["id"] for algorithm in catalog["algorithms"]} == {
        "pca_minus_neg",
        "mean_minus_neg",
    }


def test_final_300_method_parameters_match_fixed_experiment() -> None:
    assert METHOD_CONFIGS["pca_minus_neg"]["reasoning"]["alpha"] == 310.0
    assert METHOD_CONFIGS["pca_minus_neg"]["faithful"]["alpha"] == 160.0
    assert METHOD_CONFIGS["mean_minus_neg"]["safety"] == {
        "source_layer": 32,
        "injection_layer": 22,
        "alpha": 4.0,
        "vector": "final_300_safety.pt",
        "key": ("mean_minus_neg", 32),
    }
    assert all(
        (PACKAGE_VECTOR_ROOT / config["vector"]).is_file()
        for method in METHOD_CONFIGS.values()
        for config in method.values()
    )


def test_choice_parser_and_correction_summary_follow_protocol() -> None:
    assert _parse_letter("Answer: C", 4) == "C"
    assert _parse_letter("E", 4) is None
    rows = []
    for task in ("reasoning", "faithful", "safety"):
        rows.extend(
            {
                "task": task,
                "status": "complete",
                "baselineSuccess": False,
                "steeredSuccess": repaired,
            }
            for repaired in (True, True, True, True, False)
        )
    metric = _summarize(
        rows,
        {
            "name": "Correction",
            "shortName": "correction",
            "definition": "fixture",
            "threshold": 0.6,
        },
    )

    assert math.isclose(metric["accuracy"], 0.8)
    assert metric["failureToSuccess"] == 12
    assert metric["successToFailure"] == 0
    assert metric["meetsThreshold"] is True


def test_correction_rate_always_uses_baseline_failures_as_denominator() -> None:
    rows = []
    for task in ("reasoning", "faithful", "safety"):
        rows.extend(
            [
                {
                    "task": task,
                    "status": "complete",
                    "baselineSuccess": True,
                },
                {
                    "task": task,
                    "status": "complete",
                    "baselineSuccess": False,
                    "steeredSuccess": True,
                },
                {
                    "task": task,
                    "status": "complete",
                    "baselineSuccess": False,
                    "steeredSuccess": False,
                },
            ]
        )
    metric = _summarize(
        rows,
        {
            "name": "Correction",
            "shortName": "correction",
            "definition": "fixture",
            "threshold": 0.6,
        },
    )

    assert metric["accuracy"] == 0.5
    assert metric["baselineFailure"] == 6
    assert metric["failureToSuccess"] == 3
    assert all(task["correctionRate"] == 0.5 for task in metric["tasks"].values())


def test_dataset_runner_steers_only_baseline_failures(monkeypatch) -> None:
    samples = list(final_eval.DATASET_CATALOG[0]["samples"][:3])
    baseline_success_id = samples[0]["id"]
    steered_ids: list[str] = []

    class FakeWrapper:
        pretrained_path = None
        revision = "test"
        device = "cpu"
        dtype = "float32"

        def remove_hooks(self) -> None:
            pass

    monkeypatch.setattr(
        "SafeLens.explorer_model.load_explorer_hf_model", lambda *_args, **_kwargs: FakeWrapper()
    )
    monkeypatch.setattr("SafeLens.explorer_model.explorer_model_source", lambda _model: "test")
    monkeypatch.setattr(final_eval, "_empty_cuda_cache", lambda: None)
    monkeypatch.setattr(
        final_eval,
        "_load_method_vectors",
        lambda _method: {task: {} for task in ("reasoning", "faithful", "safety")},
    )

    def baseline(_wrapper, sample, _payload):
        success = sample["id"] == baseline_success_id
        return {
            "sampleId": sample["id"],
            "category": sample["task"],
            "task": sample["task"],
            "prompt": sample["prompt"],
            "groundTruth": sample["groundTruth"],
            "status": "baseline_complete",
            "passed": False,
            "detail": "",
            "original": "A",
            "baselineSuccess": success,
            "steeringApplied": False,
        }

    def steer(_wrapper, row, _sample, _payload, _config):
        steered_ids.append(row["sampleId"])
        row.update(status="complete", steeredSuccess=True, steeringApplied=True)

    monkeypatch.setattr(final_eval, "_run_baseline_sample", baseline)
    monkeypatch.setattr(final_eval, "_run_steered_failure", steer)
    payload = SimpleNamespace(
        datasetId=FINAL_DATASET_ID,
        algorithmId="pca_minus_neg",
        model="google/gemma-2-9b-it",
        sampleIds=[sample["id"] for sample in samples],
        seed=0,
    )

    result = final_eval.run_dataset_test(
        payload,
        threading.Event(),
        lambda *_args: None,
        allowed_models=("google/gemma-2-9b-it",),
    )

    assert steered_ids == [sample["id"] for sample in samples[1:]]
    assert result["execution"]["baselineSamples"] == 3
    assert result["execution"]["steeredSamples"] == 2
    assert result["metric"]["baselineFailure"] == 2
    assert result["metric"]["failureToSuccess"] == 2
