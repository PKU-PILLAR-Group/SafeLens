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

## Gemma-2-9B-it steering demo

SafeLens also ships a prompt-oriented steering demo at `/sae-steer`. It is
configured for `google/gemma-2-9b-it` and the canonical GemmaScope release
`gemma-scope-9b-it-res-canonical`, SAE id `layer_9/width_131k/canonical`, and hook
`blocks.9.hook_resid_post`. The canonical downloaded file is:

```text
layer_9/width_131k/average_l0_121/params.npz
```

Download it with:

```bash
python scripts/download_gemma_scope_9b_it_sae.py \
  --output /ssd/yqy/cache/safelens/gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz
```

On this server the model is `/ssd/models/Gemma2-9b-it` and the downloaded
checkpoint is `/ssd/yqy/cache/safelens/gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz`.
Set `SAFELENS_GEMMA_2_9B_IT_MODEL_PATH` and
`SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH` to these (or deployment-specific) paths,
then choose `SAFELENS_GEMMA_SAE_DEVICE` (`cpu` or `cuda`) and
`SAFELENS_GEMMA_SAE_DTYPE` (`float32` or `bfloat16`). The service caches the
model and decoder once per process. Each request can add one or more feature
directions; the decoder delta is `strength * W_dec[feature]` at every generated
token. Built-in examples are Cats (62610, +192), Chinese (121465, +74), and
Pirate (29917, +166), matching the layer-9 examples on the Neuronpedia demo.
When `SAFELENS_GEMMA_SAE_DEVICE` is omitted or set to `auto`, the runtime uses
`cuda:0` when CUDA is available and otherwise falls back to CPU.

The dedicated demo also exposes `POST /api/sae-steering/scan`. It encodes the
rendered prompt with the checkpoint's `W_enc`, `b_enc`, and `threshold` using
the published JumpReLU rule:

```python
pre = activations @ W_enc + b_enc
feature_acts = pre * (pre > threshold)
```

The response ranks positive features by their measured prompt activation and
includes the peak token, active-token count, Neuronpedia `maxActApprox`, and
`vectorDefaultSteerStrength` when the metadata endpoint is reachable. The
weights for this scan are loaded lazily, so a steering-only deployment keeps
only the decoder resident. Network failures fall back to index-only feature
labels without sending prompt text to Neuronpedia.

Steering scope can be selected in the UI or request body with
`steerPosition=all|prompt|generated|prompt_position`; the latter additionally
accepts a zero-based `promptPosition`. This mirrors Neuronpedia's distinction
between prompt positions and generated-token steering while preserving the
original `all` behavior as the default.
instead of silently applying an unrelated dictionary.
