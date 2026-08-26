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

## Install and run

```bash
pip install -e '.[sae,explorer]'
python -m SafeLens.explorer_api --host 127.0.0.1 --port 7860
```

The Gemma base model is gated on Hugging Face. Accept Google's model terms and
log in with `hf auth login` (or provide the normal Hugging Face token) before
starting a Gemma chat. The first SAE intervention downloads its checkpoint;
subsequent runs use the local Hugging Face cache.

Gemma Scope SAEs are not compatible with Qwen or other base models. Selecting
the SAE analysis on a non-Gemma run therefore shows no compatible profile
instead of silently applying an unrelated dictionary.
