# PDF RAG WebSocket Chat

Monorepo con dos partes:

- **`backend/`** — pipeline RAG en Python (extracción de PDF, chunking, embeddings,
  Qdrant, servidor websocket, Ollama). Ver `backend/README.md` para instrucciones.
- **`frontend/`** — chat en Angular para probar el backend desde el navegador. Ver
  `frontend/README.md` para instrucciones.

## Arranque rápido

1. Backend: sigue `backend/README.md` (instalar dependencias, ingerir el PDF, levantar
   `python server.py`).
2. Frontend: sigue `frontend/README.md` (`npm install`, `ng serve`).
3. Abre `http://localhost:4200` y chatea con el PDF.

## Documentación de diseño

- `docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md` — diseño del backend.
- `docs/superpowers/specs/2026-07-04-angular-chat-frontend-design.md` — diseño del frontend.
