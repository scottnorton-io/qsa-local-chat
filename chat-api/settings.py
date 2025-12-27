# chat-api/settings.py
import os
from pathlib import Path

# Project root is the directory containing this file (inside the Docker image)
PROJECT_ROOT = Path(__file__).resolve().parent

# ---- Connectivity to Ollama --------------------------------------------------

# Where FastAPI (in Docker) reaches Ollama.
# In docker-compose.yml, set OLLAMA_HOST=http://ollama:11434 for container-to-container calls.
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "<http://ollama:11434>")

# ---- Model configuration -----------------------------------------------------

# Chat models
GENERAL_MODEL: str = os.getenv("GENERAL_MODEL", "llama3.1:8b")
REASONING_MODEL: str = os.getenv("REASONING_MODEL", "deepseek-r1:8b")

# Embedding model (must be available in Ollama)
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "llama3.1:8b")

# ---- Retrieval configuration -------------------------------------------------

# Maximum characters per text chunk before embedding/storing.
MAX_CHARS_PER_CHUNK: int = int(os.getenv("MAX_CHARS_PER_CHUNK", "1500"))

# How many top chunks to use when building evidence context.
TOP_K_CHUNKS: int = int(os.getenv("TOP_K_CHUNKS", "12"))

# Directory where JSONL document chunks are stored inside the container.
DOC_STORE_PATH: Path = PROJECT_ROOT.parent / "doc_store"
DOC_STORE_PATH.mkdir(parents=True, exist_ok=True)

# ---- Generation controls -----------------------------------------------------

# Conservative defaults aimed at assessment / evidence work.
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
TOP_P: float = float(os.getenv("TOP_P", "0.9"))
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))

# Prompt schema / behavior versioning for auditability.
PROMPT_VERSION: str = os.getenv("PROMPT_VERSION", "bench-rag-v1")

def summary() -> dict:
    """Small helper for debugging / /docs-style endpoints (no secrets)."""
    return {
        "ollama_host": OLLAMA_HOST,
        "general_model": GENERAL_MODEL,
        "reasoning_model": REASONING_MODEL,
        "embed_model": EMBED_MODEL,
        "max_chars_per_chunk": MAX_CHARS_PER_CHUNK,
        "top_k_chunks": TOP_K_CHUNKS,
        "doc_store_path": str(DOC_STORE_PATH),
        "prompt_version": PROMPT_VERSION,
    }
