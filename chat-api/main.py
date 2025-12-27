<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Local QSA Chat – Dual-Mode RAG</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      padding: 1.5rem;
      background: #0f172a;
      color: #e5e7eb;
    }
    h1, h2, h3 {
      margin-top: 0;
    }
    a {
      color: #38bdf8;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
      gap: 1.5rem;
    }
    @media (max-width: 900px) {
      .layout {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    .card {
      background: #020617;
      border-radius: 0.75rem;
      padding: 1.25rem 1.5rem;
      border: 1px solid #1f2937;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.7);
    }
    .card h2 {
      font-size: 1rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #9ca3af;
      margin-bottom: 0.75rem;
    }
    label {
      display: block;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #9ca3af;
      margin-bottom: 0.25rem;
    }
    input[type="text"],
    select,
    textarea {
      width: 100%;
      box-sizing: border-box;
      background: #020617;
      color: #e5e7eb;
      border-radius: 0.375rem;
      border: 1px solid #4b5563;
      padding: 0.5rem 0.6rem;
      font-size: 0.9rem;
    }
    textarea {
      min-height: 7rem;
      resize: vertical;
      font-family: inherit;
    }
    input[type="file"] {
      width: 100%;
      color: #e5e7eb;
      font-size: 0.85rem;
    }
    .row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.75rem;
    }
    .field {
      margin-bottom: 0.75rem;
    }
    button {
      border: none;
      border-radius: 999px;
      padding: 0.5rem 1.1rem;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    .btn-primary {
      background: #22c55e;
      color: #022c22;
    }
    .btn-secondary {
      background: #111827;
      color: #e5e7eb;
      border: 1px solid #374151;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.15rem 0.6rem;
      border-radius: 999px;
      background: #111827;
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #9ca3af;
    }
    .status {
      font-size: 0.8rem;
      color: #9ca3af;
      margin-top: 0.3rem;
    }
    .reply-box {
      white-space: pre-wrap;
      font-size: 0.9rem;
      line-height: 1.4;
    }
    .meta {
      font-size: 0.8rem;
      color: #9ca3af;
      margin-bottom: 0.5rem;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
      margin-top: 0.4rem;
    }
    .chip {
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      border: 1px solid #374151;
      font-size: 0.7rem;
      color: #9ca3af;
      background: #020617;
    }
  </style>
</head>
<body>
  <header style="margin-bottom: 1.5rem;">
    <div class="pill">
      <span>LOCAL LAB</span>
      <span>PCI DSS v4</span>
    </div>
    <h1 style="margin: 0.4rem 0 0.2rem;">Local QSA Chat – Dual-Mode RAG</h1>
    <p style="margin: 0; font-size: 0.9rem; color: #9ca3af;">
      Ingest evidence, get assessor-grade narratives, and run gap checks locally via Ollama.
    </p>
  </header>

  <main class="layout">
    <!-- Ingest panel -->
    <section class="card">
      <h2>Ingest Evidence</h2>
      <p class="meta">
        Upload 1..N files to create a reusable <code>doc_id</code> for a client,
        requirement family, or test set.
      </p>
      <form id="ingest-form">
        <div class="field">
          <label for="ingest-files">Evidence files (.pdf, .docx, .txt)</label>
          <input id="ingest-files" name="files" type="file" multiple />
        </div>

        <button type="submit" class="btn-primary">
          ⬆ Ingest files
        </button>

        <div id="ingest-status" class="status"></div>

        <div class="field" style="margin-top: 0.75rem;">
          <label>Last ingested doc_id</label>
          <input id="last-doc-id" type="text" readonly />
          <div class="status">
            This will be copied into the Chat form for reuse.
          </div>
        </div>

        <div class="field">
          <label>Known documents</label>
          <div id="known-docs" class="chips"></div>
        </div>
      </form>
    </section>

    <!-- Chat panel -->
    <section class="card">
      <h2>Chat</h2>
      <p class="meta">
        Choose a mode, optionally attach evidence (via <code>doc_id</code> and/or files),
        and ask your question.
      </p>
      <form id="chat-form">
        <div class="row">
          <div class="field">
            <label for="mode">Mode</label>
            <select id="mode" name="mode">
              <option value="general">General – drafting &amp; explanation</option>
              <option value="reasoning">Reasoning – slower, deeper analysis</option>
            </select>
          </div>
          <div class="field">
            <label for="doc-id">Existing doc_id (optional)</label>
            <input
              id="doc-id"
              name="doc_id"
              type="text"
              placeholder="DOC-xxxxxx"
            />
          </div>
        </div>

        <div class="field">
          <label for="chat-files">Ad-hoc evidence files (optional)</label>
          <input id="chat-files" name="files" type="file" multiple />
          <div class="status">
            These files are used for this question only; they are not persisted.
          </div>
        </div>

        <div class="field">
          <label for="message">Message</label>
          <textarea
            id="message"
            name="message"
            placeholder="Ask an assessment question, draft a narrative, or request a gap analysis…"
          ></textarea>
        </div>

        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <button type="submit" class="btn-primary">
            ▶ Send
          </button>
          <button type="button" id="copy-doc-id" class="btn-secondary">
            Copy last doc_id into Chat
          </button>
        </div>

        <div id="chat-status" class="status"></div>

        <hr style="margin: 1rem 0; border-color: #111827;" />

        <div class="meta" id="chat-meta"></div>
        <div id="chat-reply" class="reply-box"></div>
      </form>
    </section>
  </main>

  <script>
    async function fetchJSON(url, options) {
      const resp = await fetch(url, options);
      const text = await resp.text();
      try {
        const data = text ? JSON.parse(text) : {};
        return { ok: resp.ok, status: resp.status, data };
      } catch (e) {
        return { ok: resp.ok, status: resp.status, data: { raw: text } };
      }
    }

    async function refreshDocs() {
      const knownDocsEl = document.getElementById("known-docs");
      knownDocsEl.innerHTML = "";
      const res = await fetchJSON("/docs");
      if (!res.ok) return;
      const docs = res.data.documents || [];
      docs.forEach((d) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip";
        chip.textContent = d.doc_id + " (" + d.chunks + ")";
        chip.addEventListener("click", () => {
          document.getElementById("doc-id").value = d.doc_id;
        });
        knownDocsEl.appendChild(chip);
      });
    }

    document.addEventListener("DOMContentLoaded", () => {
      const ingestForm = document.getElementById("ingest-form");
      const ingestStatus = document.getElementById("ingest-status");
      const lastDocIdInput = document.getElementById("last-doc-id");
      const copyDocIdBtn = document.getElementById("copy-doc-id");
      const chatForm = document.getElementById("chat-form");
      const chatStatus = document.getElementById("chat-status");
      const chatMeta = document.getElementById("chat-meta");
      const chatReply = document.getElementById("chat-reply");

      refreshDocs();

      ingestForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        ingestStatus.textContent = "Ingesting…";
        const formData = new FormData(ingestForm);
        const res = await fetchJSON("/ingest", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          ingestStatus.textContent =
            "Ingest failed: " +
            (res.data && res.data.error ? res.data.error : res.status);
          return;
        }
        const { doc_id, chunks } = res.data;
        lastDocIdInput.value = doc_id || "";
        ingestStatus.textContent =
          "Ingested " + (chunks || 0) + " chunks into " + doc_id;
        await refreshDocs();
      });

      copyDocIdBtn.addEventListener("click", () => {
        const last = lastDocIdInput.value.trim();
        if (last) {
          document.getElementById("doc-id").value = last;
          chatStatus.textContent = "Copied last doc_id into Chat form.";
        } else {
          chatStatus.textContent = "No last doc_id available yet.";
        }
      });

      chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        chatStatus.textContent = "Sending…";
        chatMeta.textContent = "";
        chatReply.textContent = "";

        const formData = new FormData(chatForm);
        const res = await fetchJSON("/chat", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err =
            (res.data && res.data.error) || "Unexpected error from /chat.";
          chatStatus.textContent = "Error: " + err;
          return;
        }

        const { mode, doc_id, used_chunks, reply } = res.data;
        chatStatus.textContent = "";

        const metaParts = [];
        if (mode) metaParts.push("Mode: " + mode);
        if (doc_id) metaParts.push("doc_id: " + doc_id);
        if (used_chunks && used_chunks.length) {
          metaParts.push("Chunks used: " + used_chunks.length);
        }
        chatMeta.textContent = metaParts.join(" | ");
        chatReply.textContent = reply || "";
      });
    });
  </script>
</body>
</html>
