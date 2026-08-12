# NLA Research Notes for SafeLens Visualization Integration

NLA means **Natural Language Autoencoder** in the current mechanistic
interpretability literature. The relevant work is Anthropic/Transformer
Circuits' 2026 release, **"Natural Language Autoencoders Produce Unsupervised
Explanations of LLM Activations"**.

## Primary Sources

| Type | Link | Notes |
| --- | --- | --- |
| Paper / Transformer Circuits post | <https://transformer-circuits.pub/2026/nla/> | Main technical writeup and citation target |
| Anthropic research post | <https://www.anthropic.com/research/natural-language-autoencoders> | Higher-level explanation and use cases |
| Full training repository | <https://github.com/kitft/natural_language_autoencoders> | Data generation, SFT, RL, checkpoint conversion, sidecars |
| Lightweight inference repository | <https://github.com/kitft/nla-inference> | Single-file `NLAClient` and `NLACritic`, worked examples |
| Released model collection | <https://huggingface.co/collections/kitft/nla-models> | Public AV/AR checkpoints for Qwen, Gemma, Llama |
| Neuronpedia frontend | <https://www.neuronpedia.org/nla> | Public interactive NLA demos |
| Neuronpedia blog | <https://www.neuronpedia.org/blog/nlas> | Frontend/context notes and contribution paths |

## Core Idea

An NLA is a pair of fine-tuned language models that form an autoencoder over
residual-stream activations:

| Component | Direction | Mechanism |
| --- | --- | --- |
| AV, activation verbalizer | vector -> text | Inject one activation vector as a single token embedding into a fixed prompt, then generate a natural-language explanation |
| AR, activation reconstructor | text -> vector | Feed explanation text into a truncated LM plus `Linear(d, d)` value head, then reconstruct the activation vector |

The training objective is round-trip reconstruction. Both original and
reconstructed vectors are L2-normalized before comparison, so the reported
direction MSE is:

```text
MSE(reconstructed, original) = 2 * (1 - cosine_similarity)
```

This makes the AR score a **direction-fidelity score**, not a raw-magnitude
score. Low MSE / high cosine means the generated text preserved enough
information for the AR to reconstruct the activation direction.

## Released Checkpoints

The public checkpoint collection currently contains four AV/AR pairs:

| Base model | Activation layer | d_model | AV checkpoint | AR checkpoint |
| --- | --- | --- | --- | --- |
| Qwen2.5-7B-Instruct | 20 / 28 | 3584 | `kitft/nla-qwen2.5-7b-L20-av` | `kitft/nla-qwen2.5-7b-L20-ar` |
| Gemma-3-12B-IT | 32 / 48 | 3840 | `kitft/nla-gemma3-12b-L32-av` | `kitft/nla-gemma3-12b-L32-ar` |
| Gemma-3-27B-IT | 41 / 62 | 5376 | `kitft/nla-gemma3-27b-L41-av` | `kitft/nla-gemma3-27b-L41-ar` |
| Llama-3.3-70B-Instruct | 53 / 80 | 8192 | `kitft/Llama-3.3-70B-NLA-L53-av` | `kitft/Llama-3.3-70B-NLA-L53-ar` |

Important implication for SafeLens: these NLAs are model/layer/dimension
specific. Our Qwen3-0.6B notebook activations are **not** in-distribution for
the released Qwen2.5-7B layer-20 NLA. For a correct demo, use one of the
released base models and extraction layers, or train a SafeLens-specific NLA.

## Runtime Interface

The lightweight inference repo exposes two concepts:

- `NLAClient`: AV inference, activation vector -> explanation text.
- `NLACritic`: AR inference, explanation text -> reconstructed vector and
  `(mse, cosine)` score against the original activation.

Minimum data needed for a SafeLens visualization row:

```python
{
    "sample_id": str,
    "token_index": int,
    "token": str,
    "source": "prompt" | "reply" | "unknown",
    "model_name": str,
    "layer": int,
    "component": "resid_post",
    "activation_norm": float,
    "explanation": str,
    "mse_nrm": float | None,
    "cosine": float | None,
    "fve_nrm": float | None,
}
```

For integration, keep the visualization decoupled from heavy inference:

1. A pure visualization should accept precomputed rows like the schema above.
2. An optional inference helper can generate these rows from SafeLens
   `run_with_cache` output.
3. The notebook can either load cached NLA rows or run live inference if an
   SGLang server is available.

## Inference Requirements

Core Python dependencies from the inference repo:

```bash
pip install torch transformers safetensors httpx orjson pyyaml numpy
pip install "sglang[all]>=0.5.6"
pip install pyarrow  # optional, only needed for parquet inputs
```

Serving requirements:

```bash
python -m sglang.launch_server \
  --model-path kitft/nla-qwen2.5-7b-L20-av \
  --port 30000 \
  --disable-radix-cache \
  --trust-remote-code
```

Critical details:

- Load `nla_meta.yaml`; do not hardcode prompt templates, token IDs, or scale
  factors.
- Send `input_embeds` to SGLang. For SafeLens inference, do not also send
  `input_ids`.
- Use `--disable-radix-cache`; radix cache keys on token IDs and can alias
  different embed sequences.
- `injection_scale` is mandatory. Raw activation magnitudes are not what the AV
  expects.
- Gemma checkpoints require embedding post-scale `sqrt(hidden_size)` when
  loading raw embedding weights directly.
- Gemma/Llama checkpoints may require gated HF access (`HF_TOKEN`).
- Gemma-3 SGLang serving may require `--attention-backend fa3`.

## Interpretation Caveats

NLA explanations are useful but should not be treated as ground truth.

- High AR fidelity means the explanation lets the AR reconstruct the vector
  direction. It does **not** prove the explanation is the only or exact human
  interpretation of that activation.
- Low fidelity can come from poor explanation quality, out-of-distribution
  activations, model/layer mismatch, early-token under-sampling, or injection
  failure.
- Released NLAs were trained on selected residual-stream layers around two
  thirds depth. Other layers/components are out-of-distribution.
- Early prompt/system positions can be under-sampled in training; examples show
  worse or less meaningful decodes there.
- Raw norm outliers are diagnostic. The AV normalizes magnitude at injection,
  but unusual vector directions can still decode poorly.
- Explanations can be verbose, speculative, or partially confabulatory. The UI
  should surface fidelity metrics and not present text as an oracle.

## Recommended SafeLens Visualization

### 1. NLA Token Timeline

Purpose: show how the model's internal residual-stream content evolves across
tokens.

Inputs:

- token labels
- NLA explanation per token
- raw activation norm
- optional `mse_nrm`, `cosine`, `fve_nrm`

UI:

- token strip with color by fidelity or norm
- click token -> explanation panel
- badges for layer/component/model
- metric chips: `||v||`, `mse_nrm`, `cos`, `fve_nrm`
- warning badge for low fidelity or outlier norm

This is the highest-value first integration because it maps directly onto
SafeLens' existing token browsers.

### 2. Layer x Token NLA Fidelity Heatmap

Purpose: compare where NLA explanations are reliable or unreliable.

Inputs:

- matrix `[layer, token]` of `cosine`, `mse_nrm`, or `fve_nrm`
- per-cell explanation payload

UI:

- heatmap over layer x token
- metric selector
- click cell -> explanation and reconstruction score
- optional token filter: prompt/reply/all

This generalizes when we later train NLAs for multiple layers.

### 3. Explanation Search / Semantic Browser

Purpose: make long NLA runs navigable.

Inputs:

- list of explanation rows

UI:

- search box over explanation text
- filters for token range, source, fidelity threshold, norm percentile
- table/list with token, layer, score, summary
- click row -> token highlight and full explanation

### 4. NLA vs Existing SafeLens Views

Purpose: connect textual explanations to numeric internals already visualized
by SafeLens.

Possible links:

- click an NLA token -> show residual dimension browser for the same token
- click an NLA token -> show attention heads feeding that token
- click an NLA row -> show MLP contribution for the same position
- compare NLA text with next-token prediction distribution

## SafeLens Implementation

SafeLens now includes a first real-weight NLA integration in `SafeLens.nla`.
The implementation is dependency-light at import time and only requires the
`nla` optional dependencies when loading official weights:

```bash
pip install "SafeLens[nla]"
```

Supported public profiles:

```python
from SafeLens import list_nla_profiles

list_nla_profiles()
```

Current profiles:

- `qwen2.5-7b-l20`: `Qwen/Qwen2.5-7B-Instruct`, layer 20 `resid_post`,
  AV `kitft/nla-qwen2.5-7b-L20-av`, AR `kitft/nla-qwen2.5-7b-L20-ar`.
- `gemma3-12b-l32`: `google/gemma-3-12b-it`, layer 32 `resid_post`,
  AV `kitft/nla-gemma3-12b-L32-av`, AR `kitft/nla-gemma3-12b-L32-ar`.

Live local inference:

```python
from SafeLens import NLAClient

client = NLAClient.from_profile(
    "qwen2.5-7b-l20",
    load_reconstructor=True,
    device="cuda",
    dtype="bfloat16",
)

result = client.explain_activation(
    activation_vector,
    sample_id="prompt-0",
    token_index=42,
    token="answer",
)
```

The actor path loads the official AV checkpoint with `transformers`, reads
`nla_meta.yaml`, tokenizes the sidecar prompt, scales the activation vector to
the sidecar `injection_scale`, injects it as `inputs_embeds`, and generates the
NLA explanation. The reconstructor path loads the official AR checkpoint,
applies the trained `value_head.safetensors`, and returns normalized MSE plus
cosine similarity.

The Qwen profile pins AV revision
`b88469162777ae6553bc14208eb0cb579336f8f4` and AR revision
`e2c9e57eac213d37a31612087f645ab6332c1bb6` independently. This matters because
the two public checkpoints live in separate repositories and do not share one
commit identifier.

Cache integration:

```python
rows = client.explain_cache(
    cache,
    tokens=str_tokens,
    positions=[42, 43, 44],
)
```

Visualization:

```python
from SafeLens import plot_nla_fidelity_heatmap, plot_nla_result_browser

plot_nla_result_browser(rows)
plot_nla_fidelity_heatmap(rows, metric="cosine")
```

`examples/nla_interactive_visualization_showcase.ipynb` demonstrates the API
and includes executed output using lightweight example rows. Set
`RUN_REAL_NLA=True` in that notebook to load official weights.

## Remaining Work

- Add an SGLang backend for higher-throughput AV generation. The current
  implementation uses local `transformers.generate(inputs_embeds=...)`.
- Add a helper that extracts matching Qwen2.5/Gemma activations from SafeLens
  wrappers and immediately runs NLA on selected token positions.
- Add JSON/Parquet import-export for large NLA runs.
- Link selected NLA rows directly to attention, MLP, and residual browsers in
  the large visualization notebook.

## Open Questions Before Coding Live Inference

- Do we want SafeLens to depend on SGLang, or only provide a client for a
  user-managed SGLang server?
- Should NLA rows be stored in JSON for notebooks or Parquet for large runs?
- Which released model should be the first supported live demo? Qwen2.5-7B is
  the most practical public checkpoint; Gemma/Llama are gated and larger.
- Do we want to support AV-only mode, or require AR scoring for every displayed
  explanation?
- Should low-fidelity explanations be hidden by default or shown with warnings?

## Practical First Target

For SafeLens, the best first feature is:

```text
plot_nla_token_timeline(precomputed_rows)
```

It gives immediate value, avoids optional serving dependencies, and fits the
existing notebook/showcase style. Live NLA inference can come next as an
optional integration once the UI contract is stable.
