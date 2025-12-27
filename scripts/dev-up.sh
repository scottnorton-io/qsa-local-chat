#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "[qsa-local-chat] Bringing stack up (build + up)…"
docker compose up -d --build

echo "[qsa-local-chat] Stack is starting. To view logs:"
echo "  docker compose logs -f chat-api"
echo "  docker compose logs -f ollama"
