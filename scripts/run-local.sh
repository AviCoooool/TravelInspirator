#!/usr/bin/env bash
# Run TravelInspirator on the host (recommended with Coforge VPN).
# Docker often cannot resolve quasarmarket.coforge.com even when VPN is up.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
# Prefer project venv if present
if [[ -x /Users/avinash/.venv-ai-travel-inspirator/bin/uvicorn ]]; then
  PY=/Users/avinash/.venv-ai-travel-inspirator/bin/uvicorn
elif [[ -x .venv/bin/uvicorn ]]; then
  PY=.venv/bin/uvicorn
else
  PY=uvicorn
fi
PORT="${APP_PORT:-8000}"
echo "Starting on http://localhost:${PORT}  (health: /health  ping: /api/llm-ping)"
exec "$PY" app.main:app --host 0.0.0.0 --port "$PORT" --reload
