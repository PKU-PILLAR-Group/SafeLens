# Local Explorer Setup

This is the operational guide for starting the SafeLens Explorer from a fresh
checkout. The Explorer is a local FastAPI server that serves the compiled React
workbench, the artifact API, and the local job queue from one port. The normal
address is `http://127.0.0.1:7860`.

## 1. Install SafeLens

Use Python 3.10 or newer. A virtual environment keeps the Explorer dependencies
separate from other research environments:

```bash
git clone https://github.com/PKU-PILLAR-Group/SafeLens.git
cd SafeLens
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[explorer,models,sae,attribution,nla,jlens]"
```

The extras have deliberately separate responsibilities:

| Extra | Required for |
| --- | --- |
| `explorer` | FastAPI server, static web app, artifact API, and job queue |
| `models` | Real Hugging Face/Transformers model jobs |
| `sae` | SAELens, Hugging Face Hub, and Gemma Scope SAE loading/downloads |
| `attribution` | Captum Integrated Gradients |
| `nla` | NLA artifact loading and reconstruction jobs |
| `jlens` | Jacobian Lens jobs and the pinned J-Lens checkpoint loader |
| `modelscope` | Optional ModelScope provider for supported Gemma 3 models |

For a viewer-only install, `python -m pip install -e ".[explorer]"` is enough.
For the complete real-model workbench, install the command above and restart the
server after adding any missing extra. A CPU-only installation is valid; CUDA is
optional.

Check the installation before starting:

```bash
python -c "import torch; print('torch', torch.__version__); print('cuda', torch.cuda.is_available())"
safelens explorer --help
```

## 2. Start The Packaged Explorer

From the repository root, run:

```bash
safelens explorer \
  --artifact-root outputs/local-explorer \
  --host 127.0.0.1 \
  --port 7860
```

The server creates the artifact directory if it does not exist and opens a
browser. On a headless machine use `--no-browser`:

```bash
safelens explorer --artifact-root outputs/local-explorer --no-browser
```

`safelens-explorer` and `python -m SafeLens.explorer_api` are equivalent entry
points. The packaged frontend does not require Node.js at runtime. Open the URL
printed by the server and confirm the API is alive:

```bash
curl -fsS http://127.0.0.1:7860/api/health
```

The response should contain `"status":"ok"`. The bundled tiny-GPT-2 run is
available immediately, even when no real model has been downloaded. Files named
`*.explorer.json` under `outputs/local-explorer` are indexed in the Run Library.
Generated prompt and analysis results are written under the same artifact root.

For a background process on a local machine:

```bash
mkdir -p outputs/local-explorer
nohup safelens explorer --artifact-root outputs/local-explorer --no-browser \
  > outputs/local-explorer/explorer.log 2>&1 &
echo $! > outputs/local-explorer/explorer.pid
```

Stop it with `kill "$(cat outputs/local-explorer/explorer.pid)"` after checking
that the PID belongs to the Explorer process.

## 3. GPU And Model Placement

Explorer jobs use `SAFELENS_EXPLORER_JOB_DEVICE=auto` by default. `auto` selects
`cuda:0` when `torch.cuda.is_available()` is true and otherwise selects `cpu`.
The dtype defaults to `bfloat16` on CUDA and `float32` on CPU. Override these
only when the machine or model requires it:

```bash
export SAFELENS_EXPLORER_JOB_DEVICE=auto       # or cpu, cuda:0, cuda:1
export SAFELENS_EXPLORER_JOB_DTYPE=bfloat16    # or float32, float16
```

The process must be restarted after changing these variables. A CUDA-enabled
PyTorch build and a working NVIDIA driver are required for GPU execution; a
GPU visible to the host is not enough if `torch.cuda.is_available()` is false.

Explorer resolves real models in this order:

1. An explicit local directory from `SAFELENS_GEMMA_2_9B_IT_MODEL_PATH` or
   `SAFELENS_EXPLORER_MODEL_PATHS`.
2. A complete local Hugging Face cache snapshot.
3. The configured provider (`huggingface` by default, or ModelScope for the
   supported Gemma 3 models when `modelscope` is installed).

For an explicit model directory, set a path containing `config.json`, tokenizer
metadata, and all model weight shards:

```bash
export SAFELENS_GEMMA_2_9B_IT_MODEL_PATH=/data/models/gemma-2-9b-it
```

Alternatively leave the variable unset and select `gemma-2-9b-it` in the chat
model picker. With Hugging Face access configured, the first real prompt job
downloads the model into `.cache/safelens/local-explorer-real-flow`. Gemma
checkpoints require accepting Google's model terms and running `hf auth login`
when the Hub requests authentication.

## 4. Gemma SAE Workbench

The SAE controls are inside a conversation turn: choose the `gemma-2-9b-it`
chat model, run a prompt, click `SAE`, and then choose either `Find active
features` or a `Neuronpedia mode`. The preset selector is enabled only for a
Gemma-2-9B-it run. It contains the public Cats, Chinese, Pirate, Shakespeare,
Poetry, San Francisco, Positivity, Negativity, Music, and British English
modes. There is no separate `/sae-steer` page.

The Gemma-2-9B-it presets use public canonical Gemma Scope residual-stream
checkpoints at L9, L20, and L31. L9 is loaded first; L20 and L31 are downloaded
lazily when a preset needs them. To make the service fully offline, put all
three files under one cache root:

```text
/data/safelens-cache/gemma-scope-9b-it-res/
  layer_9/width_131k/average_l0_121/params.npz
  layer_20/width_131k/average_l0_81/params.npz
  layer_31/width_131k/average_l0_109/params.npz
```

Then set:

```bash
export SAFELENS_GEMMA_SAE_CACHE=/data/safelens-cache
```

The L9 helper is:

```bash
python scripts/download_gemma_scope_9b_it_sae.py \
  --output /data/safelens-cache/gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz
```

On a machine with the local Gemma model and L9 checkpoint already in the
standard paths, `scripts/run_gemma_sae_demo.sh` is a convenience wrapper around
the same Explorer server. It defaults to the same automatic device/dtype policy
as the main command and accepts the normal Explorer flags:

```bash
scripts/run_gemma_sae_demo.sh --port 7860
```

For L20 and L31, use the Hub CLI while online:

```bash
hf download google/gemma-scope-9b-it-res \
  layer_20/width_131k/average_l0_81/params.npz \
  --local-dir /data/safelens-cache/gemma-scope-9b-it-res
hf download google/gemma-scope-9b-it-res \
  layer_31/width_131k/average_l0_109/params.npz \
  --local-dir /data/safelens-cache/gemma-scope-9b-it-res
```

The default `SAFELENS_GEMMA_SAE_DEVICE` is also `auto`; it follows the same
CUDA-first policy. Set it explicitly only to force the standalone SAE runtime:

```bash
export SAFELENS_GEMMA_SAE_DEVICE=auto
# Leave SAFELENS_GEMMA_SAE_DTYPE unset for the automatic CPU/GPU dtype.
```

The official `sae` extra is recommended for checkpoint downloads and SAELens
compatibility. SafeLens also has a local JumpReLU loader for the official NPZ
files, so an old `ModuleNotFoundError: sae_lens` message usually means a stale
worker or bundle is running. Rebuild/stage the distribution and restart the
server as described in the next section.

## 5. Rebuild After Frontend Changes

A normal checkout already contains a packaged web bundle. Node.js is needed only
when changing the React app or regenerating the bundle:

```bash
cd apps/local_explorer
npm ci
npm run build
cd ../..
python scripts/prepare_explorer_distribution.py --skip-web-build
```

The staging command copies `apps/local_explorer/dist` and all Explorer workers
into `src/SafeLens/explorer_web` and `src/SafeLens/explorer_workers`. Restart
the running `safelens explorer` process after staging. To build and stage in one
step, run `python scripts/prepare_explorer_distribution.py` from the repository
root; this invokes `npm run build` itself.

For frontend development, use two ports:

```bash
# terminal 1
cd apps/local_explorer
npm ci
npm run dev                         # http://127.0.0.1:7860

# terminal 2, from the repository root
python -m SafeLens.explorer_api \
  --artifact-root outputs/local-explorer \
  --web-root apps/local_explorer/dist \
  --host 127.0.0.1 \
  --port 7861 \
  --no-browser
```

Vite proxies `/api` from port 7860 to the FastAPI process on port 7861. Do not
start the production server on 7860 at the same time as Vite.

## 6. Remote Or Container Use

The default bind is localhost and is intentional. Explorer has no built-in
authentication or TLS. Do not expose it directly to an untrusted network. If a
reverse proxy provides authentication and HTTPS, explicitly opt into a remote
bind:

```bash
safelens explorer \
  --artifact-root /data/safelens \
  --host 0.0.0.0 \
  --port 7860 \
  --allow-remote \
  --no-browser
```

The repository Dockerfile builds the frontend and starts this same packaged
server. A minimal container run is:

```bash
docker build -t safelens-explorer .
docker volume create safelens-data
docker run --rm -p 127.0.0.1:7860:7860 \
  -v safelens-data:/data safelens-explorer
```

The image is a viewer/API image. Add the real-model extras in the image build
if container-side prompt, SAE, attribution, NLA, or J-Lens jobs are required.

## 7. Troubleshooting

| Symptom | Check/fix |
| --- | --- |
| `Built Explorer frontend not found` | Run `python scripts/prepare_explorer_distribution.py` or reinstall the package. |
| Page loads but no real model appears | Install `.[models]`, check `/api/prompt/options`, and verify the model snapshot or Hub access. |
| Send shows no answer immediately | The first model job loads weights in a subprocess. Watch the in-page progress and server log; do not start a second server on the same port. |
| `Run`/`Find active features` is disabled | Wait for preflight to finish, select a compatible model/profile and feature, and keep the token range inside the prompt. |
| `SAE Lens is unavailable` or `No module named sae_lens` | Install `.[sae]` for the official loader, then rebuild/stage workers and restart. The official local NPZ fallback is also supported. |
| SAE preset is disabled | The Neuronpedia presets require `google/gemma-2-9b-it`; switch the chat model from Qwen, tiny-GPT-2, or Gemma 3. |
| SAE checkpoint not found | Set `SAFELENS_GEMMA_SAE_CACHE` to the parent containing `gemma-scope-9b-it-res/`, or set the explicit L9 path. Checkpoint downloads require `huggingface-hub`. |
| Service uses CPU unexpectedly | Run `python -c "import torch; print(torch.cuda.is_available())"`; install a CUDA PyTorch build, check the driver, unset a forced `SAFELENS_EXPLORER_JOB_DEVICE=cpu`, and restart. |
| Port 7860 is occupied | Use `--port 7861` (and a matching proxy/URL), or stop the process that owns 7860 after verifying it is safe to stop. |
| Remote bind is rejected | Add `--allow-remote`, and put authentication/TLS in front of the service. |

Useful final checks:

```bash
curl -fsS http://127.0.0.1:7860/api/health
curl -fsS http://127.0.0.1:7860/api/prompt/options
curl -fsS 'http://127.0.0.1:7860/api/intervention/sae-profiles?modelName=google%2Fgemma-2-9b-it'
curl -fsS http://127.0.0.1:7860/api/sae-steering/config
```

The last two requests should show the three 9B profiles (L9/L20/L31) and the
ten Neuronpedia modes when the current code and packaged bundle are loaded.

## 8. Verification Before Handoff

Run these checks after changing the startup path or frontend bundle:

```bash
ruff check src/SafeLens tests
python -m py_compile src/SafeLens/explorer_api.py src/SafeLens/explorer_sae.py
pytest -q
cd apps/local_explorer && npm run build
```

For a full package check, stage the bundle and run the wheel verification script:

```bash
cd ../..
python scripts/prepare_explorer_distribution.py --skip-web-build
python -m build
python scripts/verify_explorer_wheel.py
```
