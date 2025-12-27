# Local Dual-Mode LLM Chatbot (Ollama + FastAPI + RAG)

This project provides a **dual‑mode local LLM chatbot with retrieval** for PCI DSS v4 assessment workflows. It runs entirely on an Apple Silicon Mac using **Docker**, **FastAPI**, and **Ollama**.

You get:
- One project folder (`qsa-local-chat/`)
- One command to bring the stack up: `docker compose up -d`
- A local web UI at `http://localhost:8080` with two modes:
  - **General**: faster drafting / explanation
  - **Reasoning**: slower, deeper analysis
- A persistent **document store** for ingested evidence and retrieval‑augmented chat

---

## Prerequisites

- Apple Silicon Mac (e.g., M3 Max, 64 GB RAM recommended)
- macOS "Tahoe" 26.2 or later
- Docker Desktop for Mac (Apple chip build) – installed from [docker.com](http://docker.com), **no Homebrew**.
- Ollama installed in the `ollama` container via `docker compose` (this repo handles that).

---

## Project Layout
```text
qsa-local-chat/
├─ docker-compose.yml
├─ .env.example
├─ .gitignore
├─ scripts/
│  ├─ dev-up.sh
│  ├─ dev-down.sh
│  └─ dev-reset.sh
└─ chat-api/
├─ Dockerfile
├─ settings.py
├─ ollama_client.py
├─ doc_store.py
├─ main.py
└─ templates/
└─ index.html
```

---

## Configuration

Configuration is centralized in `chat-api/settings.py` and can be overridden via environment variables (for example with a `.env` file based on `.env.example`). Key settings:

- `GENERAL_MODEL` – baseline chat model (default `llama3.1:8b`)
- `REASONING_MODEL` – deeper reasoning model (default `deepseek-r1:8b`)
- `EMBED_MODEL` – embedding model for retrieval (default `llama3.1:8b`)
- `MAX_CHARS_PER_CHUNK`, `TOP_K_CHUNKS`
- `TEMPERATURE`, `TOP_P`, `MAX_TOKENS`
- `PROMPT_VERSION` – prompt behavior / schema version string

`OLLAMA_HOST` is set to `http://ollama:11434` via `docker-compose.yml` for container‑to‑container calls.

---

## Quick Start

From the project root (`qsa-local-chat/`):
```bash
# Bring the stack up (build images on first run)
./scripts/[dev-up.sh](http://dev-up.sh)

# Or, without scripts
# docker compose up -d --build
```

Then, pull models inside the `ollama` container (one‑time per model):
```bash
docker exec -it ollama ollama pull llama3.1:8b
docker exec -it ollama ollama pull deepseek-r1:8b
```

Open the UI:

- Browser → `http://localhost:8080`

---

## Usage

The UI has two main panels:

1. **Ingest Evidence**
   - Upload 1..N files (`.pdf`, `.docx`, `.txt`).
   - The API extracts text, chunks it, embeds it, and stores chunks in JSONL under `/app/doc_store`.
   - Returns a `doc_id` you can reuse in later chats.

2. **Chat**
   - Choose `mode` = `general` or `reasoning`.
   - Optionally specify an existing `doc_id` and/or attach ad‑hoc evidence files.
   - Ask questions like:
     - *"Draft a PCI DSS v4 10.4 narrative based on this evidence."*
     - *"Given this evidence set for 10.4.1, is it sufficient? Call out missing items."*

Under the hood:

- `/ingest` → extracts text, chunks, embeds, and writes JSONL files (`DOC-*.jsonl`).
- `/chat` → collects stored + ad‑hoc chunks, retrieves top‑K via cosine similarity, and calls Ollama with an evidence‑aware prompt.

---

## Day‑to‑Day Commands

From `qsa-local-chat/`:
```bash
# Bring stack up (build + up)
./scripts/dev-up.sh

# Bring stack down (keep volumes)
./scripts/dev-down.sh

# Full reset (containers + volumes, including model cache)
./scripts/dev-reset.sh
```


Without scripts:
```bash
docker compose up -d --build
docker compose down
docker compose down -v
```

---

## Troubleshooting

- **UI not reachable at `http://localhost:8080`**
  - Check: `docker compose ps` → `chat-api` should be `running` and exposing `0.0.0.0:8080->8080`.
  - If not, run: `docker compose up -d --build`.

- **Ollama / httpx protocol errors**
  - `Request URL is missing a protocol` usually means `OLLAMA_HOST` is empty or invalid.
  - Ensure `OLLAMA_HOST` is set to `http://ollama:11434` in `docker-compose.yml` and rebuild.

- **Model not found**
  - Inside the container: `docker exec -it ollama ollama list`.
  - Ensure `GENERAL_MODEL` / `REASONING_MODEL` in `settings.py` match installed models.

- **Evidence ignored (`doc_id` seems unused)**
  - Confirm the UI copied `Last ingested doc_id` into the Chat form.
  - Call `GET /docs` (e.g., `curl http://localhost:8080/docs`) to list known documents.

---

## Scope & Safety

This stack is intended as a **local lab** tool:

- No authentication
- No TLS termination
- Not suitable for production or real PCI evidence without additional hardening

If you expose it beyond localhost or use real client data, you must add:

- Authentication and transport security
- Hardened container images and base OS
- Integrated secrets and logging controls

---

## License

TBD – insert preferred license here.
