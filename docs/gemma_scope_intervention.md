# Gemma Scope SAE intervention

SafeLens exposes Gemma Scope 2 features as a separate `sae_feature`
intervention. The first supported profile is:

```text
base model: google/gemma-3-270m-it
SAELens release: gemma-scope-2-270m-it-res
SAE: layer_12_width_16k_l0_small
hook: resid_post at layer 12
```

The `res` release name is the current SAELens registry alias for the
`resid_post` folder. The profile is intentionally allow-listed so an SAE
trained for another model, layer, or site cannot be attached accidentally.

## Official loading example

The Gemma Scope model card uses SAELens. The current SAELens registry form is:

```python
from sae_lens import SAE

sae = SAE.from_pretrained(
    release="gemma-scope-2-270m-it-res",
    sae_id="layer_12_width_16k_l0_small",
    device="cuda",
)
```

For an activation tensor `x` from Gemma 3 270M IT's layer-12 residual stream,
SAELens exposes the standard feature operations:

```python
feature_acts = sae.encode(x)
reconstruction = sae.decode(feature_acts)
```

SafeLens performs an intervention by encoding the selected token activations,
changing one feature coordinate, decoding both versions, and injecting only
the decoded delta back into `resid_post`. `Add activation` increments the
feature coordinate by the requested strength; `Ablate feature` sets it to
zero. The result records the SAE release, SAE ID, feature index, activation
statistics, logit deltas, and generated-token diff.

In Chat, **Find active features** defaults to the output boundary, where an
intervention can directly influence generation, and ranks features by their
measured positive activation. The UI also keeps a user-input scan for features
that are active only in the prompt. Each row shows its peak token, activation,
coverage, optional Neuronpedia concept, and a calibrated strength. Selecting a
row fills the feature and strength fields. `Add activation` defaults to the
output boundary; `Ablate feature` defaults to the feature's measured peak token
so it does not silently ablate an inactive coordinate. The suggested delta is
approximately twice the observed peak (bounded to `100..1000`); **Subtle**
applies half that value and all fields remain editable.

For the output-boundary range, the decoded SAE delta is applied during prompt
prefill and every cached autoregressive generation step. This keeps the
intervention active after the first generated token instead of changing only a
single next-token logit.

## Install and run

```bash
pip install -e '.[sae,explorer]'
python -m SafeLens.explorer_api --host 127.0.0.1 --port 7860
```

SafeLens first uses an available local Hugging Face snapshot and can fall back
to the configured ModelScope cache for both the Gemma base model and Gemma
Scope checkpoint. When only Hugging Face is configured, accept Google's model
terms and log in with `hf auth login` before starting a Gemma chat. The first
SAE scan or intervention may download its checkpoint; subsequent runs use the
local cache.

Gemma Scope SAEs are not compatible with Qwen or other base models. Selecting
the SAE analysis on a non-Gemma run therefore shows no compatible profile
instead of silently applying an unrelated dictionary.
