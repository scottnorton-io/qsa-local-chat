# chat-api/ollama_client.py
from typing import List

import httpx

import settings

class OllamaError(RuntimeError):
    """Raised when calls to Ollama fail or return unexpected data."""
    
def _client(timeout_seconds: int = 120) -> httpx.Client:
    """Create an HTTPX client with a bounded timeout."""
    return httpx.Client(timeout=timeout_seconds)

def embed_text(text: str) -> List[float]:
    """Compute an embedding for the given text using Ollama /api/embeddings.

    Returns a dense vector as a list of floats, or raises OllamaError on failure.
    """
    payload = {
        "model": settings.EMBED_MODEL,
        "prompt": text,
        "stream": False,
    }
    url = f"{settings.OLLAMA_HOST}/api/embeddings"

    try:
        with _client(timeout_seconds=60) as client:
            resp = client.post(url, json=payload)
    except httpx.HTTPError as exc:  # network / transport errors
        raise OllamaError(
            f"Failed to reach Ollama embeddings endpoint: {exc}"
        ) from exc

    if resp.status_code != 200:
        raise OllamaError(
            f"Ollama embeddings error: status={resp.status_code}, "
            f"body={resp.text[:500]}"
        )

    try:
        data = resp.json()
        # Ollama embeddings responses are typically either:
        # { "embedding": [...] }  or  { "data": [ { "embedding": [...] } ] }
        if isinstance(data, dict):
            if "embedding" in data:
                return [float(x) for x in data["embedding"]]
            if "data" in data and data["data"]:
                return [float(x) for x in data["data"][0]["embedding"]]
    except Exception as exc:  # JSON / shape errors
        raise OllamaError(
            f"Unexpected embeddings payload from Ollama: {exc}"
        ) from exc

    raise OllamaError("No embedding vector found in Ollama response")
    
    def call_ollama(model: str, system_prompt: str, user_message: str) -> str:
        """Call Ollama /api/chat and return the assistant's reply text.

        Uses non-streaming mode for simplicity. Raises OllamaError on any
        connectivity or payload issues.
        """
        url = f"{settings.OLLAMA_HOST}/api/chat"

        payload = {
            "model": model,
            "stream": False,
            "options": {
            # Generation controls from central settings
            "temperature": settings.TEMPERATURE,
            "top_p": settings.TOP,
            "num_predict": settings.MAX_TOKENS,
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    f"[prompt_version={settings.PROMPT_VERSION}] "
                    f"{system_prompt}"
                ),
            },
            {"role": "user", "content": user_message},
        ],
    }

    try:
        with _client(timeout_seconds=settings.MAX_TOKENS * 2) as client:
            resp = client.post(url, json=payload)
    except httpx.HTTPError as exc:
        raise OllamaError(
            f"Failed to reach Ollama chat endpoint: {exc}"
        ) from exc

    if resp.status_code != 200:
        raise OllamaError(
            f"Ollama chat error: status={resp.status_code}, "
            f"body={resp.text[:500]}"
        )

    try:
        data = resp.json()
        # Common Ollama chat shape: { "message": { "content": "..." }, ... }
        if isinstance(data, dict):
            msg = data.get("message")
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str):
                    return content

            # Fallback: some variants return a list of messages
            messages = data.get("messages")
            if isinstance(messages, list):
                for m in messages:
                    if (
                        isinstance(m, dict)
                        and m.get("role") == "assistant"
                        and isinstance(m.get("content"), str)
                    ):
                        return m["content"]
    except Exception as exc:
        raise OllamaError(
            f"Unexpected chat payload from Ollama: {exc}"
        ) from exc

    raise OllamaError("No assistant content found in Ollama chat response")
