# PDF RAG WebSocket Chat — Backend

Real-time websocket chat that answers questions about the contents of a PDF using RAG
(Retrieval Augmented Generation). The whole pipeline is free and runs locally: no API keys,
no paid services.

## Prerequisites

1. Python 3.10+
2. [Ollama](https://ollama.com/download) installed (free)
3. The Ollama model pulled once:
   ```
   ollama pull llama3.2
   ```

## Installation

```
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

1. Put your PDF in the `data/` folder (there should already be one there).
2. Run ingestion once (extracts text, chunks it, generates embeddings, stores them in
   Qdrant):
   ```
   python ingest.py
   ```
   On a large PDF (tested with a 1608-page book) extraction takes seconds, but generating
   embeddings for every chunk can take 10-15 minutes on CPU — that's expected, not a hang.
3. Start the chat server:
   ```
   python server.py
   ```
4. Connect with any websocket client to `ws://localhost:8765` and send questions about the
   PDF's content as plain text messages. Quick test client:
   ```
   python -c "
   import asyncio, websockets

   async def test():
       async with websockets.connect('ws://localhost:8765') as ws:
           await ws.send('your question here')
           print(await ws.recv())

   asyncio.run(test())
   "
   ```

**Response time:** expect roughly 30-90 seconds per answer when running Ollama on CPU
only (no GPU). The pipeline itself (embedding the question, searching Qdrant) is fast —
the LLM generation step is what takes most of that time. This is normal, not a bug.

## Architecture

See
[`docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md`](../docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md)
for the full design, and
[`docs/superpowers/plans/2026-07-04-pdf-rag-websocket-chat.md`](../docs/superpowers/plans/2026-07-04-pdf-rag-websocket-chat.md)
for the step-by-step implementation plan.

Summary: `ingest.py` (Phase 1, offline) extracts the PDF's text with **PyMuPDF**, chunks it,
counts tokens with `tiktoken`, generates one embedding per chunk with a **multilingual**
`sentence-transformers` model, and stores everything in an embedded Qdrant collection
(`qdrant_storage/`, no Docker required). `server.py` (Phase 2) listens for websocket
connections; each question is embedded with the same model, the most relevant chunks are
retrieved from Qdrant, and a prompt combining those chunks with the question is sent to a
local Ollama model (`llama3.2`) to generate the final answer.

### Decisions made during implementation (and why)

- **PDF extraction: PyMuPDF, not pypdf or pdfplumber.** All three were tested against the
  real PDF (1608 pages). `pypdf` silently inserted stray spaces inside words
  (`"pronom inales"` instead of `"pronominales"`). `pdfplumber` extracted clean text but
  took ~15 minutes for 1608 pages. `PyMuPDF` takes ~11 seconds (with the same order of
  occasional noise as `pypdf`) — for a practice project, the speed is worth the small
  cosmetic noise.
- **Embeddings: a multilingual model, not `all-MiniLM-L6-v2`.** The initial model (aimed
  mostly at English) produced inverted semantic similarity on Spanish text (a sentence
  about a car scored as "more similar" to a sentence about a cat than another sentence
  about a feline did). Switched to `paraphrase-multilingual-MiniLM-L12-v2`, which correctly
  captures Spanish semantics and keeps the same vector dimension (384).
- **The RAG call runs in a worker thread (`asyncio.to_thread`), not inline in the
  websocket handler.** `answer_question()` is blocking (embeddings, Qdrant, and the Ollama
  call are all synchronous). Running it directly inside the `async` handler froze the
  event loop for the whole duration, so the client's keepalive ping never got a pong and
  `websockets` dropped the connection with "keepalive ping timeout". Wrapping the call in
  `asyncio.to_thread(...)` keeps the event loop free to answer pings while the blocking
  work happens off-loop.
- Spanish text sometimes shows up as `�` when printed in a Windows console — that's just
  the console failing to render Unicode, not an actual data problem (verified by reading
  the characters' Unicode code points directly).
- A cosmetic exception trace can appear at the end of short scripts
  (`ModuleNotFoundError: import of msvcrt halted...` from `QdrantClient.__del__`). It's a
  known Windows interpreter-shutdown artifact and doesn't affect the process's exit code or
  results.

## Notes

- Nothing in this project calls a paid API. Answer generation runs on your own machine via
  Ollama.
- The source PDF itself is not committed to git (see `.gitignore`) — only code and
  configuration are tracked.
