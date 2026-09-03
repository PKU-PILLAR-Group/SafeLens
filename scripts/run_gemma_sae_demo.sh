#!/usr/bin/env bash
set -euo pipefail

# Configure SAFELENS_GEMMA_* variables before calling this helper.  The
# defaults match the local assets on the SafeLens development host while all
# paths remain overridable for deployment.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
if [[ -z "${SAFELENS_GEMMA_2_9B_IT_MODEL_PATH:-}" && -d /ssd/models/Gemma2-9b-it ]]; then
  export SAFELENS_GEMMA_2_9B_IT_MODEL_PATH=/ssd/models/Gemma2-9b-it
fi
if [[ -z "${SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH:-}" && -f /ssd/yqy/cache/safelens/gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz ]]; then
  export SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH=/ssd/yqy/cache/safelens/gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz
else
  export SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH="${SAFELENS_GEMMA_SCOPE_9B_IT_SAE_PATH:-${ROOT}/.cache/safelens/gemma-scope-9b-it-res/layer_9/width_131k/average_l0_121/params.npz}"
fi
export SAFELENS_GEMMA_SAE_DEVICE="${SAFELENS_GEMMA_SAE_DEVICE:-auto}"
if [[ -z "${SAFELENS_GEMMA_SAE_DTYPE:-}" ]]; then
  if python -c 'import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)' 2>/dev/null; then
    export SAFELENS_GEMMA_SAE_DTYPE=bfloat16
  else
    export SAFELENS_GEMMA_SAE_DTYPE=float32
  fi
fi
export SAFELENS_GEMMA_SAE_PRELOAD="${SAFELENS_GEMMA_SAE_PRELOAD:-1}"

exec python -m SafeLens.explorer_api \
  --artifact-root "${SAFELENS_ARTIFACT_ROOT:-outputs/local-explorer}" \
  --no-browser \
  "$@"
