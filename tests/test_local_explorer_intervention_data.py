from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/run_local_explorer_intervention.py"
SPEC = importlib.util.spec_from_file_location("run_local_explorer_intervention", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_intervention_diff_distance_and_lexical_proxy_are_explicit() -> None:
    assert MODULE._levenshtein([1, 2, 3], [1, 4, 3, 5]) == 2
    assert MODULE._diff_rows([1, 2], [1, 3]) == [
        {
            "kind": "equal",
            "originalStart": 0,
            "originalEnd": 1,
            "steeredStart": 0,
            "steeredEnd": 1,
        },
        {
            "kind": "replace",
            "originalStart": 1,
            "originalEnd": 2,
            "steeredStart": 1,
            "steeredEnd": 2,
        },
    ]
    assert MODULE._lexical_risk("harm exploit neutral") == 0.66666667


def test_merge_intervention_result_preserves_causal_and_proxy_provenance() -> None:
    source = {
        "runId": "source-run",
        "sampleId": "sample-a",
        "metricProvenance": {},
        "metadata": {},
    }
    comparison = {
        "vector": {
            "algorithmVersion": "3.0",
            "method": "contrastive_mean_difference",
            "sourceKey": "layer_1.resid_post",
            "injectionPhase": "generation",
        },
        "layer": 1,
        "sourceLayer": 0,
        "injectLayer": 1,
        "component": "resid_post",
        "scale": 1.5,
        "positionStart": 2,
        "positionEnd": 5,
        "targetTokenId": 42,
        "targetTokenText": " answer",
        "seed": 7,
        "maxNewTokens": 8,
        "temperature": 0.0,
        "original": {"text": "original"},
        "steered": {"text": "steered"},
        "deltas": {"targetLogit": 0.5, "directionProjectionDelta": 12.0},
    }

    derived = MODULE._merge_intervention_result(
        source,
        comparison,
        run_id="derived-run",
    )

    assert derived["runId"] == "derived-run"
    assert derived["intervention"] is comparison
    assert derived["metadata"]["parentRun"] == {
        "runId": "source-run",
        "sampleId": "sample-a",
    }
    assert derived["metadata"]["interventionJobs"][0]["jobVersion"] == "3.0"
    assert derived["metadata"]["interventionJobs"][0]["sourceLayer"] == 0
    assert derived["metadata"]["interventionJobs"][0]["injectLayer"] == 1
    assert derived["metadata"]["interventionJobs"][0]["injectionPhase"] == "generation"
    assert derived["metricProvenance"]["interventionTargetLogitDelta"]["kind"] == "causal"
    assert derived["metricProvenance"]["interventionLexicalRiskDelta"]["kind"] == "derived_proxy"
    assert derived["metricProvenance"]["interventionDirectionProjectionDelta"] == {
        "label": "Applied direction projection",
        "method": "Generation-time raw contrastive activation steering",
        "semantics": "Signed L2 magnitude injected along the desired-minus-undesired direction.",
        "normalization": "none; scale multiplied by the raw contrast-vector norm",
        "kind": "causal",
    }


def test_neuron_hook_scales_only_the_selected_neuron_and_position_range() -> None:
    torch = pytest.importorskip("torch")
    activation = torch.tensor(
        [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]
    )
    hook = MODULE._make_neuron_hook(neuron=1, factor=0.25, position=(1, 3))

    patched = hook(activation=activation)

    assert patched is not activation
    assert torch.equal(
        activation,
        torch.tensor([[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]),
    )
    assert torch.equal(
        patched,
        torch.tensor([[[1.0, 2.0, 3.0], [4.0, 1.25, 6.0], [7.0, 2.0, 9.0]]]),
    )


def test_logit_delta_summary_detects_full_vocabulary_effect() -> None:
    torch = pytest.importorskip("torch")
    summary = MODULE._logit_delta_summary(
        torch.tensor([0.0, 1.0, 2.0, 3.0]),
        torch.tensor([0.0, 1.5, 2.0, 2.75]),
    )

    assert summary == {
        "maxAbsLogit": 0.5,
        "meanAbsLogit": 0.1875,
        "changedVocabularyLogits": 2,
        "topChangedTokenId": 1,
        "topChangedTokenDelta": 0.5,
        "effectStatus": "changed",
    }


def test_logit_delta_summary_uses_real_generation_steps_and_vocab_ids() -> None:
    torch = pytest.importorskip("torch")
    summary = MODULE._logit_delta_summary(
        torch.tensor([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]]),
        torch.tensor([[0.0, 1.0, 2.0], [3.0, 3.5, 7.0]]),
    )

    assert summary == {
        "maxAbsLogit": 2.0,
        "meanAbsLogit": pytest.approx(2.5 / 6),
        "changedVocabularyLogits": 2,
        "topChangedTokenId": 2,
        "topChangedTokenDelta": 2.0,
        "effectStatus": "changed",
    }


def test_generation_score_matrix_prefers_generate_output_scores() -> None:
    torch = pytest.importorskip("torch")

    class Generated:
        scores = (torch.tensor([[1.0, 2.0]]), torch.tensor([[3.0, 4.0]]))

    scores = MODULE._generation_score_matrix(
        Generated(),
        fallback=torch.tensor([9.0, 9.0]),
    )

    assert torch.equal(scores, torch.tensor([[1.0, 2.0], [3.0, 4.0]]))


def test_optional_layer_treats_serialized_null_as_default() -> None:
    assert MODULE._optional_layer(None, 18) == 18
    assert MODULE._optional_layer(0, 18) == 0


def test_direction_hook_skips_prefill_then_applies_raw_contrast_during_generation() -> None:
    torch = pytest.importorskip("torch")
    desired = torch.tensor([4.0, 8.0])
    undesired = torch.tensor([1.0, 2.0])
    vector, raw_norm = MODULE._contrastive_direction(desired, undesired)
    hook = MODULE._make_generation_direction_hook(
        vector=vector,
        scale=1.0,
    )

    prefill = torch.zeros((1, 3, 2))
    incremental = torch.zeros((1, 1, 2))

    assert raw_norm == pytest.approx(6.7082039)
    assert torch.equal(hook(activation=prefill), prefill)
    assert torch.equal(
        hook(activation=incremental),
        torch.tensor([[[3.0, 6.0]]]),
    )
    assert torch.equal(
        hook(activation=incremental),
        torch.tensor([[[3.0, 6.0]]]),
    )


def test_sae_feature_hook_adds_one_decoded_feature_on_selected_prompt_tokens() -> None:
    torch = pytest.importorskip("torch")

    class FakeSAE:
        W_dec = torch.eye(2)

        def encode(self, activation):
            return activation

        def decode(self, features):
            return features

    hook = MODULE._make_sae_feature_hook(
        sae=FakeSAE(),
        feature_index=1,
        operation="add",
        scale=3.0,
        position=(1, 3),
        prompt_token_count=3,
    )
    activation = torch.tensor([[[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]])

    patched = hook(activation=activation)

    assert torch.equal(
        patched,
        torch.tensor([[[1.0, 2.0], [3.0, 7.0], [5.0, 9.0]]]),
    )
    assert torch.equal(hook(activation=torch.zeros((1, 1, 2))), torch.zeros((1, 1, 2)))


def test_sae_feature_hook_keeps_output_boundary_active_during_cached_generation() -> None:
    torch = pytest.importorskip("torch")

    class FakeSAE:
        W_dec = torch.eye(2)

        def encode(self, activation):
            return activation

        def decode(self, features):
            return features

    hook = MODULE._make_sae_feature_hook(
        sae=FakeSAE(),
        feature_index=1,
        operation="add",
        scale=3.0,
        position=(2, 3),
        prompt_token_count=3,
    )

    # A cached generation call contains only the newest token. The output
    # boundary range must still receive the feature delta on every such call.
    incremental = torch.tensor([[[1.0, 2.0]]])

    assert torch.equal(
        hook(activation=incremental),
        torch.tensor([[[1.0, 5.0]]]),
    )


def test_sae_feature_hook_ablates_encoded_feature_without_replacing_reconstruction() -> None:
    torch = pytest.importorskip("torch")

    class FakeSAE:
        W_dec = torch.eye(2)

        def encode(self, activation):
            return activation

        def decode(self, features):
            return features

    hook = MODULE._make_sae_feature_hook(
        sae=FakeSAE(),
        feature_index=0,
        operation="ablate",
        scale=20.0,
        position=(0, 1),
        prompt_token_count=2,
    )
    activation = torch.tensor([[[4.0, 2.0], [7.0, 5.0]]])

    patched = hook(activation=activation)

    assert torch.equal(patched, torch.tensor([[[0.0, 2.0], [7.0, 5.0]]]))


def test_reference_prompt_uses_native_chat_template_when_available() -> None:
    class Tokenizer:
        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert messages == [{"role": "user", "content": "Use structure."}]
            assert tokenize is False
            assert add_generation_prompt is True
            return "<user>Use structure.</user><assistant>"

    rendered, method = MODULE._render_reference_prompt(Tokenizer(), " Use structure. ")

    assert rendered == "<user>Use structure.</user><assistant>"
    assert method == "tokenizer.apply_chat_template"


def test_reference_prompt_preserves_preformatted_chat_template() -> None:
    class Tokenizer:
        def apply_chat_template(self, *_args, **_kwargs):
            raise AssertionError("preformatted prompts must not be wrapped again")

    prompt = "<|im_start|>user\nQuestion<|im_end|>\n<|im_start|>assistant\n"
    rendered, method = MODULE._render_reference_prompt(Tokenizer(), prompt)

    assert rendered == prompt
    assert method == "preformatted_chat_template"


def test_reference_activation_can_use_last_token_or_token_average() -> None:
    torch = pytest.importorskip("torch")
    activation = torch.tensor([[[1.0, 3.0], [5.0, 7.0]]])

    assert torch.equal(
        MODULE._reduce_reference_activation(activation, "last_token"),
        torch.tensor([5.0, 7.0]),
    )
    assert torch.equal(
        MODULE._reduce_reference_activation(activation, "mean"),
        torch.tensor([3.0, 5.0]),
    )


def test_first_divergence_index_reports_change_or_matching_prefix() -> None:
    assert MODULE._first_divergence_index([1, 2, 3], [1, 4, 3]) == 1
    assert MODULE._first_divergence_index([1, 2], [1, 2, 3]) == 2
    assert MODULE._first_divergence_index([1, 2], [1, 2]) is None
