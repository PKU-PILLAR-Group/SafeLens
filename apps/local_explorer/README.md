# SafeLens Local Explorer

Local Explorer is the first frontend implementation of the SafeLens interactive
workspace described in `docs/local_explorer_plan.md`.

## Quick Start

The production frontend is bundled in the Python package. From the repository
root, launch the complete web application and API with one command:

```bash
python -m pip install -e ".[explorer]"
safelens explorer --artifact-root outputs/local-explorer
```

The browser opens `http://127.0.0.1:7860`. Node.js is not needed to run the
packaged application. Use `safelens-explorer` as an equivalent standalone
entry point, or add `--no-browser` for a headless machine.

The lightweight install includes all visualization components, the artifact
library, and job APIs. Executing real-model Prompt, Attribution, NLA, Patching,
and Intervention jobs requires the corresponding ML dependencies:

```bash
python -m pip install -e ".[explorer,models,attribution,nla]"
```

## Docker

Build and run an isolated, non-root container from the repository root:

```bash
docker build -t safelens-explorer .
docker volume create safelens-data
docker run --rm -p 127.0.0.1:7860:7860 \
  -v safelens-data:/data safelens-explorer
```

The named volume persists server-generated artifacts and files placed under `/data`.
Browser-imported artifacts remain in that browser's local storage.
`GET /api/health` is the container health check. The default image is the
lightweight viewer/API image; build an environment with the model extras when
server-side real-model jobs are required.

Do not expose port 7860 directly to an untrusted network. Explorer has no
built-in authentication or TLS. Put authentication and HTTPS in a reverse
proxy, or keep the host mapping on `127.0.0.1` and use an SSH tunnel.

## Frontend Development

Only frontend development uses two processes. Install dependencies and start
Vite on port 7860:

```bash
cd apps/local_explorer
npm ci
npm run dev
```

In another terminal, start the API on port 7861 from the repository root:

```bash
python -m pip install -e ".[explorer]"
python -m SafeLens.explorer_api \
  --artifact-root outputs/local-explorer \
  --web-root apps/local_explorer/dist \
  --port 7861 \
  --no-browser
```

Vite proxies `/api` to `http://127.0.0.1:7861`. Production mode does not use
this proxy: FastAPI serves both the built frontend and `/api` on port 7860.

## Interaction Model

The standalone module opens in **Focus** mode. The token timeline and active
analysis canvas stay visible, while supporting evidence is progressively
disclosed:

- Click a token or matrix cell to open its contextual action bar.
- Use **Analyze** to switch the selected token across Overview, Residual,
  Attention, MLP, NLA, Attribution, Patching, and Intervention.
- Use **Inspect** for evidence values and provenance, **Context** for supporting
  panels, and **Pin / Compare** for cross-selection analysis.
- Experiment forms are mounted only after an explicit configure action.
- Use the layout button in the top bar to switch to **Dense** mode when the
  complete expert workspace should remain visible.

Build the distributable resources after frontend changes:

```bash
python scripts/prepare_explorer_distribution.py
```

The Run Library reports
connecting, ready, offline, error, and cancelled states and always preserves
bundled and browser-imported runs as an offline fallback. On mobile, open the
database button beside the quick run selector to access the full Run Library.

The server listens on localhost by default, limits artifact reads and writes to
the configured root, ignores symlinks, rejects oversized compact files, and
never accepts arbitrary filesystem paths from the browser. A non-local bind is
rejected unless `--allow-remote` is explicitly supplied.

## Test

```bash
cd apps/local_explorer
npm run build
npm run test:e2e
npm run test:performance
```

Install the local Chromium runtime once with `npx playwright install chromium`
if Playwright reports that the browser executable is missing.

## Real Model Data

The checked-in `src/realRunData.ts` is generated from a real SafeLens
HuggingFace model flow using `sshleifer/tiny-gpt2` on CPU. The generation step
loads the model, tokenizes the prompt, captures residual stream outputs,
attention patterns, MLP post activations, and writes only compact visualization
metrics.

```bash
cd apps/local_explorer
npm run build:real-run
```

Use a different compatible HuggingFace causal LM:

```bash
python ../../scripts/build_local_explorer_real_run.py --model sshleifer/tiny-gpt2
```

NLA AV/AR is not run for `tiny-gpt2` because SafeLens only has registered public
NLA profiles for matching Qwen/Gemma checkpoints. The UI shows this as an NLA
status row instead of fabricating an explanation.

## Local Artifact Library

The Run Library imports either a versioned artifact envelope or one legacy
`ExplorerRun` object. Versioned files use:

```json
{
  "schema_version": "1.0",
  "run": { "run_id": "run-id" },
  "samples": [{ "runId": "run-id", "sampleId": "sample-id" }]
}
```

Each sample must contain the complete compact `ExplorerRun` payload. Zod checks
all required collections plus cross-field token counts, layer references,
attention matrix dimensions, neuron profiles, and attribution row lengths.
Files are limited to 4 MB; up to six imported samples are kept in browser local
storage. Use **Export current Explorer artifact** for a round-trip-compatible
file. The separate evidence export is intentionally not a run artifact.

Workspace artifacts use the same schema and are indexed at `GET /api/runs`;
individual validated samples are loaded from
`GET /api/runs/{run_id}/samples/{sample_id}`. A malformed sample is reported as
a diagnostic without preventing other valid workspace samples from loading.

## Current Scope

- Real model cache-backed token, residual, attention, and MLP metrics.
- Strict token/layer matching: missing NLA or retained-neuron data is shown as
  unavailable instead of borrowing a nearby result.
- Metric provenance for every displayed proxy, including its derivation,
  normalization, and interpretation limits.
- Layer-synchronized attention-head selection and component heatmaps backed by
  matching cache keys.
- A source-aware Token Timeline with prompt/reply and special-token semantics,
  searchable text/position/token IDs, Token/Word aggregation, evidence markers,
  metric coloring, range selection, modifier-key Pin, and a 180-item render
  window for long sequences.
- A global cross-run comparison workspace with token/model/provenance snapshots,
  exact/text-only/position-only alignment diagnostics, strict delta gating,
  selectable baselines, source-context restoration, and versioned comparison
  JSON export.
- A unified evidence Inspector with explicit available/unavailable/incompatible/
  not-computed/failed states, raw versus displayed values, units, method,
  normalization, cache key, shape, artifact/run/model provenance, warnings,
  reproducible context copy, and a mobile bottom drawer.
- A real cached per-head attention pattern matrix with destination×source
  selection, causal-mask semantics, source/destination URL state, zoom, pair
  tooltips, and pair-level evidence pinning.
- A real residual logit lens generated by applying the model final norm and
  unembedding to every cached `resid_post`, including top-k vocabulary tokens,
  raw logits, probabilities, observed-next-token ranks, and layer transitions.
- A signed MLP token×neuron activation matrix backed by real `hook_post`
  profiles, with raw/absolute/normalized modes, neuron search, threshold
  filtering, divergent colors, neuron URL state, and activation-level Pin.
- A method-aware Attribution matrix that preserves signed residual-direction
  projections, keeps unsigned attention/safety proxies separate, exposes raw
  and display-normalized values, and explains unavailable Captum artifacts.
- An exact-match NLA fidelity workspace with Layer×Token×Component coverage,
  cosine/MSE/FVE controls, thresholds, explanation search, low-fidelity states,
  and structured model/layer/d_model profile diagnostics.
- JSON export for the current token/layer/component evidence selection.
- One URL-synchronized selection store for view, token, token range, layer,
  head, track, metric, and normalization state.
- Reloadable and shareable analysis URLs such as
  `?view=residual&token=10&layer=1&metric=residual_norm&normalization=raw`.
- Reusable matrix controls with metric switching, raw/normalized display,
  zoom, drag-to-select token ranges, reset, provenance tooltips, and cache-key
  copy actions.
- Persistent evidence pins that restore the complete view/token/layer/metric
  context instead of restoring only a token.
- A responsive Compare Drawer for 2–4 pinned evidence contexts, with a baseline,
  compatible deltas, explicit incompatible-scale states, provenance, removal,
  and one-click context restoration.
- A validated local Run/Sample library with schema-version diagnostics, JSON
  import/export, recent imported runs, persistence, removal, URL run/sample
  state, and a mobile-accessible quick selector.
- Responsive research-workbench layout with wide-screen sticky inspectors,
  overlap-safe medium breakpoints, and a single-column mobile flow.
- Previous/next token navigation, keyboard arrow navigation, and explicit token
  pinning from the inspector.
- Compact unavailable states that avoid repeating incompatible NLA messages.
- One unified analysis navigation for Overview, Residual, Attention, MLP, NLA,
  and Attribution; layer selection is shared across every view.
- View-specific evidence panels and inspector content, avoiding unrelated NLA
  or attribution details in component-focused workflows.
- Distinct heatmap color semantics: red for safety-direction proxies, teal for
  attention concentration, and green for MLP activation.
- NLA status cards and token inspector integration.
- Attention head distribution interaction.
- Input attribution interaction.
- Three neural component views: residual stream output, attention head, and MLP neuron.

## Matrix Interaction

- Hover a cell to inspect its token, layer, raw and normalized values, metric,
  evidence class, provenance, and cache key.
- Click a cell to select the matching token and layer.
- Press and drag across cells to select a token range; use **Clear range** or
  **Reset** to return to a single-token selection.
- Use **Raw / Normalized** to change the displayed value. Raw mode still uses
  the visible matrix bounds for color mapping, so the legend remains readable.
- Use **Pin current evidence** to keep up to four complete evidence contexts.
  Selecting a pin restores its original view and controls.
- Open **Compare pinned evidence** in the top bar to compare all pins. The first
  card is the baseline; deltas are shown only when metric and normalization are
  compatible.
- In **Attention**, rows are destination/query tokens and columns are source/key
  tokens. Masked future-source cells are hatched and cannot be selected. A cell
  click updates both `source` and `target` in the URL.
- In **Residual**, the logit-lens panel compares layer-wise vocabulary
  projections. Toggle Logit/Probability and select a layer card to synchronize
  the rest of the workspace. These projections are diagnostic, not causal.
- In **MLP**, green and magenta represent positive and negative signed
  activations. Search retained neurons, raise the normalized threshold to mute
  weak cells, and click a cell to synchronize both token and neuron.
- In **Attribution**, choose a method before interpreting colors. Orange/teal
  are positive/negative only for signed methods; attention and safety proxies
  remain explicitly unsigned. Selecting Integrated Gradients shows the missing
  job requirements instead of fabricating values.
- In **NLA**, hatched cells distinguish incompatible cached candidates from
  completely missing artifacts. Profile diagnostics show model, layer, and
  d_model checks independently; nearby tokens or layers are never substituted.

## Metric Semantics

The bundled tiny-GPT-2 run is an interpretability smoke test, not a calibrated
safety classifier. In particular:

- `Safety proxy` is a min-max-normalized residual projection onto a selected
  safety-token direction.
- `Attention proxy` is final-query attention and is descriptive rather than
  causal attribution.
- The attention heatmap shows mean per-head attention concentration for each
  query token.
- The MLP heatmap shows normalized mean absolute `hook_post` activation.

Hover a provenance row or heatmap cell to inspect the metric meaning and source
cache key. Exported evidence JSON includes the complete provenance block.
