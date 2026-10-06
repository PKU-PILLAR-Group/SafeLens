#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLATFORM_HOME="${SAFELENS_PLATFORM_HOME:-$(dirname "$ROOT")}"
PYTHON="${SAFELENS_PYTHON:-$ROOT/.venv/bin/python}"
PORT="${SAFELENS_PORT:-7860}"
ARTIFACT_ROOT="${SAFELENS_ARTIFACT_ROOT:-$ROOT/outputs/local-explorer}"
LOG_DIR="$ROOT/outputs/platform"
NODE="${SAFELENS_NODE:-$(command -v node || true)}"
PROXY="${SAFELENS_PLATFORM_PROXY:-$PLATFORM_HOME/ws-proxy.js}"
mkdir -p "$LOG_DIR" "$ARTIFACT_ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

health() {
  "$PYTHON" - "$1" <<'PY'
import json, sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=3) as response:
        assert json.load(response)['status'] == 'ok'
except Exception:
    sys.exit(1)
PY
}

if ! health "http://127.0.0.1:$PORT/api/health"; then
  setsid nohup "$PYTHON" -m SafeLens.explorer_api \
    --host 127.0.0.1 --port "$PORT" --no-browser \
    --artifact-root "$ARTIFACT_ROOT" \
    > "$LOG_DIR/explorer.log" 2>&1 < /dev/null &
  echo $! > "$LOG_DIR/explorer.pid"
  ready=0
  for attempt in {1..30}; do
    if health "http://127.0.0.1:$PORT/api/health"; then ready=1; break; fi
    if ! kill -0 "$(cat "$LOG_DIR/explorer.pid")" 2>/dev/null; then break; fi
    sleep 1
  done
  if [ "$ready" != 1 ]; then tail -60 "$LOG_DIR/explorer.log"; exit 1; fi
fi

PROXY_HEALTH="http://127.0.0.1:30000/V1/__proxy/$PORT/api/health"
if ! health "$PROXY_HEALTH"; then
  if [[ -z "$NODE" || ! -x "$NODE" ]]; then
    echo 'Node.js was not found; set SAFELENS_NODE to its executable.' >&2
    exit 1
  fi
  if [[ ! -f "$PROXY" ]]; then
    echo 'Platform proxy was not found; set SAFELENS_PLATFORM_PROXY to ws-proxy.js.' >&2
    exit 1
  fi
  if "$PYTHON" -c "import socket; s=socket.create_connection(('127.0.0.1',30000),2); s.close()" >/dev/null 2>&1; then
    echo 'Port 30000 is occupied, but the existing proxy does not serve SafeLens.' >&2
    exit 1
  fi
  setsid nohup "$NODE" "$PROXY" > "$LOG_DIR/proxy.log" 2>&1 < /dev/null &
  echo $! > "$LOG_DIR/proxy.pid"
  sleep 1
  health "$PROXY_HEALTH"
fi

echo "SafeLens is ready: append /V1/__proxy/$PORT/ to the platform's 30000 URL."
echo "Logs: $LOG_DIR/explorer.log"
