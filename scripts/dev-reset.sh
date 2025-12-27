#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "[qsa-local-chat] Stopping stack and removing containers + volumes…"
docker compose down -v

echo "[qsa-local-chat] Removing Ollama model cache volume (if present)…"
# Adjust volume name if your project dir name differs
VOLUME_NAME="$(docker volume ls --format '.Name' | grep -E '^qsa-local-chat_ollama-data$' || true)"
if [[ -n "$VOLUME_NAME" ]]; then
  docker volume rm "$VOLUME_NAME" || true
  echo "[qsa-local-chat] Removed volume: $VOLUME_NAME"
else
  echo "[qsa-local-chat] No qsa-local-chat_ollama-data volume found."
fi

echo "[qsa-local-chat] Reset complete."
