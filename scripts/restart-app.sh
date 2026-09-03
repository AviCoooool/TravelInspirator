#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d --force-recreate
echo "Restarted. Open http://localhost:8000 and hard-refresh (Ctrl+Shift+R)."
