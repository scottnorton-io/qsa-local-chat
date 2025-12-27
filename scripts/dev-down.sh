#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "[qsa-local-chat] Bringing stack down (containers only, keep volumes)…"
docker compose down

echo "[qsa-local-chat] Done."
