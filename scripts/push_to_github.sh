#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env — add GITHUB_PERSONAL_ACCESS_TOKEN first."
  exit 1
fi

export GH_TOKEN="$(grep -E '^GITHUB_PERSONAL_ACCESS_TOKEN=' .env | cut -d= -f2- | tr -d '\r\"')"

if [[ -z "$GH_TOKEN" ]]; then
  echo "GITHUB_PERSONAL_ACCESS_TOKEN is empty in .env"
  exit 1
fi

GH="${GH_BIN:-/Users/avinash/Downloads/gh_2.86.0_macOS_amd64/bin/gh}"
if [[ ! -x "$GH" ]]; then
  GH="$(command -v gh || true)"
fi

echo "Checking GitHub authentication..."
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user)"

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "GitHub token rejected (HTTP $HTTP_CODE). Regenerate a PAT with repo scope."
  exit 1
fi

echo "Creating repo if needed..."
if [[ -x "$GH" ]]; then
  "$GH" repo view AviCoooool/AITravel >/dev/null 2>&1 \
    || "$GH" repo create AviCoooool/AITravel \
         --public \
         --description "AI Travel Inspirator - Emotion-first travel discovery powered by AI" \
         --source=. \
         --remote=origin
else
  echo "gh CLI not found — create https://github.com/AviCoooool/AITravel manually if needed."
fi

echo "Pushing to origin main..."
git push -u "https://x-access-token:${GH_TOKEN}@github.com/AviCoooool/AITravel.git" main

echo "Done: https://github.com/AviCoooool/AITravel"
