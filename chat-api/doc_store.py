# chat-api/doc_store.py
import io
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

from pypdf import PdfReader
import docx  # python-docx

import settings
import ollama_client
from ollama_client import embed_text

@dataclass
class Chunk:
    doc_id: str
    file_name: str
    index: int
    text: str
    embedding: List[float] | None = None

def doc_path(doc_id: str) -> Path:
    return settings.DOC_STORE_PATH / f"{doc_id}.jsonl"

def list_docs() -> List[dict]:
    """Return a list of {doc_id, chunks} entries for all ingested documents."""
    docs: List[dict] = []
    for path in settings.DOC_STORE_PATH.glob("DOC-*.jsonl"):
        try:
            count = sum(1 for _ in path.open("r", encoding="utf-8"))
            docs.append({"doc_id": path.stem, "chunks": count})
        except OSError:
            # Skip unreadable files but do not fail the entire listing
            continue
    return sorted(docs, key=lambda d: d["doc_id"])
    
def _read_txt_bytes(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")

def _read_pdf_bytes(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    texts: List[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t:
            texts.append(t)
    return "\\n\\n".join(texts)

def _read_docx_bytes(data: bytes) -> str:
    f = io.BytesIO(data)
    document = docx.Document(f)
    return "\\n".join(p.text for p in document.paragraphs)

def extract_text_from_upload(file_name: str, data: bytes) -> str:
    """Extract plain text from an uploaded file based on extension."""
    name_lower = (file_name or "").lower()
    if name_lower.endswith(".pdf"):
        return _read_pdf_bytes(data)
    if name_lower.endswith(".docx"):
        return _read_docx_bytes(data)
    # Default to treating as UTF-8 text (covers .txt, .log, etc.).
    return _read_txt_bytes(data)

def chunk_text(doc_id: str, file_name: str, text: str) -> List[Chunk]:
    """Break text into roughly MAX_CHARS_PER_CHUNK-sized chunks."""
    max_chars = settings.MAX_CHARS_PER_CHUNK
    chunks: List[Chunk] = []

    if not text.strip():
        return chunks

    # Simple character-window chunking with soft boundaries on newlines
    start = 0
    index = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        # Try to backtrack to the last newline for a cleaner split
        split_at = text.rfind("\\n", start, end)
        if split_at == -1 or split_at <= start + max_chars // 3:
            split_at = end
        chunk_text_str = text[start:split_at].strip()
        if chunk_text_str:
            chunks.append(
                Chunk(
                    doc_id=doc_id,
                    file_name=file_name,
                    index=index,
                    text=chunk_text_str,
                )
            )
            index += 1
        start = split_at

    return chunks

def save_chunks(chunks: Iterable[Chunk]) -> int:
    """Append chunks to their document file; returns number of chunks written."""
    chunks_list = list(chunks)
    if not chunks_list:
        return 0

    # All chunks share the same doc_id
    path = doc_path(chunks_list[0].doc_id)
    with path.open("a", encoding="utf-8") as f:
        for ch in chunks_list:
            f.write(json.dumps(asdict(ch), ensure_ascii=False) + "\\n")
    return len(chunks_list)

def load_doc_chunks(doc_id: str) -> List[Chunk]:
    path = doc_path(doc_id)
    if not path.exists():
        return []

    chunks: List[Chunk] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                chunks.append(
                    Chunk(
                        doc_id=obj.get("doc_id", doc_id),
                        file_name=obj.get("file_name", "unknown"),
                        index=int(obj.get("index", 0)),
                        text=obj.get("text", ""),
                        embedding=obj.get("embedding"),
                    )
                )
            except json.JSONDecodeError:
                continue
    return chunks

def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)

def retrieve_relevant_chunks(question: str, chunks: List[Chunk]) -> List[Chunk]:
    """Embed the question + any unembedded chunks and return top-K by cosine."""
    if not chunks:
        return []

    # Ensure all chunks have embeddings
    for ch in chunks:
        if ch.embedding is None:
            ch.embedding = embed_text(ch.text)

    q_vec = embed_text(question)
    scored: List[tuple[float, Chunk]] = []
    for ch in chunks:
        if ch.embedding:
            scored.append((cosine(q_vec, ch.embedding), ch))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_k = settings.TOP_K_CHUNKS
    return [ch for _score, ch in scored[:top_k]]
