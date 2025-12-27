# chat-api/main.py
import uuid
from typing import List, Optional

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from . import settings
from .ollama_client import call_ollama, OllamaError
from .doc_store import (
    Chunk,
    list_docs,
    extract_text_from_upload,
    chunk_text,
    save_chunks,
    load_doc_chunks,
    retrieve_relevant_chunks,
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

GENERAL_SYSTEM_PROMPT = (
    "You are a helpful assistant for PCI DSS v4 assessment and evidence review. "
    "Write concise, assessor-grade responses with clear assumptions."
)

REASONING_SYSTEM_PROMPT = (
    "You are a careful PCI DSS v4 assessment assistant. "
    "Think through edge cases and missing evidence explicitly. "
    "Lay out reasoning in clear, numbered steps before conclusions."
)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/docs")
async def get_docs():
    """List ingested documents and their chunk counts."""
    return {"documents": list_docs()}

@app.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    """Ingest one or more files and return a new doc_id + chunk count.

    All files in a single request are grouped under one doc_id.
    """
    if not files:
        return JSONResponse(
            status_code=400,
            content={"error": "No files uploaded"},
        )

    doc_id = f"DOC-{uuid.uuid4().hex[:8]}"
    all_chunks: List[Chunk] = []

    for uf in files:
        data = await [uf.read](<http://uf.read>)()
        text = extract_text_from_upload(uf.filename or "upload", data)
        file_chunks = chunk_text(
            doc_id=doc_id,
            file_name=uf.filename or "upload",
            text=text,
        )
        all_chunks.extend(file_chunks)

    written = save_chunks(all_chunks)

    return {"doc_id": doc_id, "chunks": written}

@app.post("/chat")
async def chat(
    mode: str = Form("general"),
    message: str = Form(...),
    doc_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
):
    """Dual-mode chat endpoint with retrieval over stored + ad-hoc evidence."""
    message = (message or "").strip()
    if not message:
        return JSONResponse(
            status_code=400,
            content={"error": "Message is required"},
        )

    # 1) Gather candidate chunks: stored by doc_id + new uploads in this request
    candidate_chunks: List[Chunk] = []

    if doc_id:
        candidate_chunks.extend(load_doc_chunks(doc_id))

    if files:
        # Ad-hoc evidence: not persisted, only used for this request
        for uf in files:
            data = await [uf.read](<http://uf.read>)()
            text = extract_text_from_upload(uf.filename or "upload", data)
            candidate_chunks.extend(
                chunk_text(
                    doc_id=doc_id or "ADHOC",
                    file_name=uf.filename or "upload",
                    text=text,
                )
            )

    # 2) Retrieve relevant chunks (if any)
    relevant_chunks: List[Chunk] = []
    if candidate_chunks:
        relevant_chunks = retrieve_relevant_chunks(message, candidate_chunks)
    
    # 3) Build evidence context block
    evidence_blocks: List[str] = []
    for ch in relevant_chunks:
        evidence_blocks.append(
            f"[doc={ch.doc_id} file={ch.file_name} idx={ch.index}]\\n"
            f"{ch.text.strip()}"
        )

    evidence_context = "\\n\\n".join(evidence_blocks)

    if evidence_context:
        user_prompt = (
            "You have access to retrieved evidence chunks below. "
             "Use them when relevant, and call out when evidence is missing or ambiguous.\\n\\n"
            "=== EVIDENCE START ===\\n"
            f"{evidence_context}\\n"
            "=== EVIDENCE END ===\\n\\n"
            f"User question: {message}"
         )
    else:
         user_prompt = message

   # 4) Select model + system prompt
    if mode == "reasoning":
        model = settings.REASONING_MODEL
        system_prompt = REASONING_SYSTEM_PROMPT
    else:
        model = settings.GENERAL_MODEL
        system_prompt = GENERAL_SYSTEM_PROMPT

    # 5) Call Ollama
    try:
        reply_text = call_ollama(
            model=model,
            system_prompt=system_prompt,
            user_message=user_prompt,
        )
    except OllamaError as exc:
        # Do not leak evidence contents; return a high-level error
        return JSONResponse(
            status_code=502,
            content={
                "error": "Upstream Ollama error",
                "detail": str(exc)[:300],
            },
        )

    return {
        "mode": mode,
        "doc_id": doc_id,
        "used_chunks": [
            {
                "doc_id": ch.doc_id,
                "file_name": ch.file_name,
                "index": ch.index,
            }
            for ch in relevant_chunks
        ],
        "reply": reply_text,
    }

