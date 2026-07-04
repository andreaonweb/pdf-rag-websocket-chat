# PDF RAG WebSocket Chat

A real-time chat that answers questions about the contents of a PDF using RAG (Retrieval
Augmented Generation). Every part of the pipeline runs free and local: no paid APIs, no
cloud services, no API keys.

This is a monorepo with two parts:

- **[`backend/`](backend/README.md)** — Python RAG pipeline: PDF text extraction, chunking,
  token counting, embeddings, a local Qdrant vector store, and a websocket server that ties
  it all together with a local Ollama model.
- **[`frontend/`](frontend/README.md)** — an Angular chat UI to talk to the backend from a
  browser instead of raw scripts.

## Quick start

1. **Backend** — follow [`backend/README.md`](backend/README.md): install dependencies,
   ingest your PDF once, then start `python server.py`.
2. **Frontend** — follow [`frontend/README.md`](frontend/README.md): `npm install`, then
   `npx ng serve`.
3. Open `http://localhost:4200` and start chatting with your PDF.

## Design documentation

- [`docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md`](docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md) — backend design.
- [`docs/superpowers/specs/2026-07-04-angular-chat-frontend-design.md`](docs/superpowers/specs/2026-07-04-angular-chat-frontend-design.md) — frontend design.
- [`docs/superpowers/plans/`](docs/superpowers/plans/) — the step-by-step implementation plans for both.
