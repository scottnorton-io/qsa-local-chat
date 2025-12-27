#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "[qsa-local-chat] Rebuilding stack with --no-cache…"
docker compose down
docker compose build --no-cache
docker compose up -d

echo "[qsa-local-chat] Stack is starting. To view logs:"
echo "  docker compose logs -f chat-api"
echo "  docker compose logs -f ollama"
