# PDF RAG WebSocket Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a websocket chat server that answers questions about the contents of a PDF using RAG, with every component running free and local.

**Architecture:** A two-phase pipeline. Phase 1 (`ingest.py`, run once) extracts text from the PDF in `data/`, chunks it, counts tokens, embeds each chunk, and stores everything in an embedded (no-server) Qdrant collection. Phase 2 (`server.py`) is a `websockets` server: each incoming message is embedded with the same model, used to search Qdrant for the top-k most relevant chunks, and those chunks are stuffed into a prompt sent to a local Ollama model, whose reply is sent back over the socket.

**Tech Stack:** Python, `pypdf`, `tiktoken`, `sentence-transformers` (`all-MiniLM-L6-v2`), `qdrant-client` (embedded/local mode), `ollama` (Python client, `llama3.2` model), `websockets`.

## Global Constraints

- Every component must run free and local — no paid API, no cloud service, no Anthropic/OpenAI calls anywhere in this project (per `docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md`).
- Qdrant runs in embedded mode (`QdrantClient(path=...)`) — no Docker, no separate server process.
- The PDF lives at `data/*.pdf` (already placed by the user) and is discovered by glob, not hardcoded by filename.
- The PDF file itself must NOT be committed to git (`data/*.pdf` is gitignored) — it's large (tens of MB) and the repo has a public GitHub remote already configured.
- Testing approach is manual verification (`print()`-based smoke checks run by hand), not an automated pytest suite — this was an explicit, already-approved design decision for this practice project, not an oversight. Each task's "test" step is a small manual command with an expected observable output.
- Ollama must be installed separately by the user (`https://ollama.com`, free) with the `llama3.2` model pulled (`ollama pull llama3.2`) — this is the one external dependency outside `pip install`, and is called out in the README (Task 10).

---

## File Structure

```
pdf-rag-websocket-chat/
├── data/
│   └── *.pdf                # already present, gitignored
├── qdrant_storage/           # created by vector_store.py on first run, gitignored
├── pdf_utils.py               # Task 2 — PDF text extraction
├── chunking.py                 # Task 3 — chunk_text(), Chunk dataclass, token counting
├── embeddings.py                # Task 4 — sentence-transformers wrapper
├── vector_store.py               # Task 5 — Qdrant embedded wrapper (VectorStore class)
├── ingest.py                       # Task 6 — Phase 1 orchestration script
├── llm.py                            # Task 7 — Ollama call wrapper
├── rag.py                              # Task 8 — prompt building + answer_question()
├── server.py                             # Task 9 — websocket server
├── requirements.txt            # Task 1
├── .gitignore                  # Task 1
└── README.md                   # Task 10
```

Each file has one job. `ingest.py`, `rag.py`, and `server.py` are thin orchestrators that import
from the single-purpose modules — this mirrors the pipeline stages the user is learning
(extracción → chunking → tokens → embeddings → Qdrant → websocket → consulta → respuesta), one
file per concept.

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`

**Interfaces:**
- Produces: nothing importable — this task just prepares the environment for every later task.

- [ ] **Step 1: Write `requirements.txt`**

```
pypdf
tiktoken
sentence-transformers
qdrant-client>=1.9
websockets
ollama
```

- [ ] **Step 2: Write `.gitignore`**

```
qdrant_storage/
data/*.pdf
__pycache__/
*.pyc
.venv/
venv/
```

- [ ] **Step 3: Create and activate a virtual environment, then install dependencies**

Run (PowerShell):
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Expected: all six packages install without error. `sentence-transformers` will pull in `torch` —
this can take a few minutes and a few hundred MB on first install; that's expected.

- [ ] **Step 4: Verify the installs**

Run: `python -c "import pypdf, tiktoken, sentence_transformers, qdrant_client, websockets, ollama; print('ok')"`
Expected: prints `ok` with no `ImportError`.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore
git commit -m "chore: scaffold project dependencies and gitignore"
```

---

### Task 2: PDF text extraction

**Files:**
- Create: `pdf_utils.py`

**Interfaces:**
- Consumes: nothing (first pipeline stage).
- Produces: `extract_text(pdf_path: str) -> str` — used by `ingest.py` (Task 6).

- [ ] **Step 1: Write `pdf_utils.py`**

```python
from pypdf import PdfReader


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF, one page at a time, joined with newlines."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text)
```

- [ ] **Step 2: Manually verify against the real PDF in `data/`**

Run:
```
python -c "from pathlib import Path; from pdf_utils import extract_text; p = next(Path('data').glob('*.pdf')); t = extract_text(str(p)); print(f'{len(t)} caracteres extraidos'); print(t[:300])"
```
Expected: prints a character count in the hundreds of thousands (it's a large grammar reference
book) followed by a readable snippet of Spanish text — not garbled binary or an empty string.

- [ ] **Step 3: Commit**

```bash
git add pdf_utils.py
git commit -m "feat: add PDF text extraction"
```

---

### Task 3: Chunking and token counting

**Files:**
- Create: `chunking.py`

**Interfaces:**
- Consumes: nothing directly (operates on the `str` produced by `pdf_utils.extract_text`).
- Produces: `Chunk` dataclass (`text: str`, `index: int`, `token_count: int`), `chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[Chunk]`, `count_tokens(text: str) -> int` — used by `ingest.py` (Task 6) and re-exported `Chunk` used by `vector_store.py` (Task 5).

- [ ] **Step 1: Write `chunking.py`**

```python
from dataclasses import dataclass

import tiktoken

_encoder = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    text: str
    index: int
    token_count: int


def count_tokens(text: str) -> int:
    """Approximate token count for a piece of text (cl100k_base encoding).

    This is not Claude's exact tokenizer, but it's a standard, free, local
    estimator good enough for sizing chunks and context windows.
    """
    return len(_encoder.encode(text))


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[Chunk]:
    """Split text into overlapping character-based chunks.

    chunk_size and overlap are measured in characters, not tokens — this
    keeps the splitter dependency-free and easy to reason about.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    index = 0
    text_length = len(text)
    while start < text_length:
        end = start + chunk_size
        piece = text[start:end].strip()
        if piece:
            chunks.append(Chunk(text=piece, index=index, token_count=count_tokens(piece)))
            index += 1
        start += chunk_size - overlap
    return chunks
```

- [ ] **Step 2: Manually verify with a small inline string**

Run:
```
python -c "from chunking import chunk_text; chunks = chunk_text('Hola mundo. ' * 200, chunk_size=100, overlap=20); print(len(chunks)); print(chunks[0]); print(chunks[1].text[:50])"
```
Expected: prints a chunk count greater than 1, then a `Chunk(text=..., index=0, token_count=...)`
for the first chunk, then the start of the second chunk's text — which should visibly overlap
with the tail of the first chunk's text.

- [ ] **Step 3: Manually verify against the real extracted PDF text**

Run:
```
python -c "from pathlib import Path; from pdf_utils import extract_text; from chunking import chunk_text; p = next(Path('data').glob('*.pdf')); text = extract_text(str(p)); chunks = chunk_text(text); total_tokens = sum(c.token_count for c in chunks); print(f'{len(chunks)} chunks, ~{total_tokens} tokens total')"
```
Expected: prints a chunk count in the hundreds/thousands with a total token count, no errors.

- [ ] **Step 4: Commit**

```bash
git add chunking.py
git commit -m "feat: add text chunking with token counting"
```

---

### Task 4: Embeddings

**Files:**
- Create: `embeddings.py`

**Interfaces:**
- Consumes: nothing (operates on plain strings).
- Produces: `embed_texts(texts: list[str]) -> list[list[float]]` — used by `ingest.py` (Task 6) and `rag.py` (Task 8). Vectors are 384-dimensional (the `all-MiniLM-L6-v2` output size), a fact `vector_store.py` (Task 5) hardcodes as `VECTOR_SIZE`.

- [ ] **Step 1: Write `embeddings.py`**

```python
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = load_model()
    vectors = model.encode(texts, show_progress_bar=False)
    return vectors.tolist()
```

- [ ] **Step 2: Manually verify**

Run:
```
python -c "from embeddings import embed_texts; vecs = embed_texts(['el gato duerme', 'un felino descansa', 'el coche es rojo']); print(len(vecs), len(vecs[0]))"
```
Expected: first run downloads the `all-MiniLM-L6-v2` model (~90MB, one-time, needs internet the
first time only). Prints `3 384` — three vectors of 384 dimensions each.

- [ ] **Step 3: Sanity-check semantic similarity**

Run:
```
python -c "
import numpy as np
from embeddings import embed_texts
vecs = embed_texts(['el gato duerme', 'un felino descansa', 'el coche es rojo'])
a, b, c = (np.array(v) for v in vecs)
sim_ab = a @ b / (np.linalg.norm(a) * np.linalg.norm(b))
sim_ac = a @ c / (np.linalg.norm(a) * np.linalg.norm(c))
print(f'gato/felino similarity: {sim_ab:.3f}')
print(f'gato/coche similarity: {sim_ac:.3f}')
"
```
Expected: the gato/felino similarity score is noticeably higher than gato/coche — confirming the
model places semantically related sentences closer together.

- [ ] **Step 4: Commit**

```bash
git add embeddings.py
git commit -m "feat: add sentence-transformers embedding wrapper"
```

---

### Task 5: Vector store (embedded Qdrant)

**Files:**
- Create: `vector_store.py`

**Interfaces:**
- Consumes: `Chunk` from `chunking.py` (Task 3, for type reference only — `add_chunks` takes any object with `.index`, `.text`, `.token_count`).
- Produces: `VectorStore` class with `__init__(self, path: str = "qdrant_storage")`, `add_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None`, `search(self, query_vector: list[float], top_k: int = 4) -> list[str]`, `count(self) -> int` — used by `ingest.py` (Task 6), `rag.py` (Task 8), and `server.py` (Task 9).

- [ ] **Step 1: Write `vector_store.py`**

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION_NAME = "pdf_chunks"
VECTOR_SIZE = 384  # output size of all-MiniLM-L6-v2


class VectorStore:
    def __init__(self, path: str = "qdrant_storage"):
        self.client = QdrantClient(path=path)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def add_chunks(self, chunks, vectors: list[list[float]]) -> None:
        points = [
            PointStruct(
                id=chunk.index,
                vector=vector,
                payload={"text": chunk.text, "token_count": chunk.token_count},
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self.client.upsert(collection_name=COLLECTION_NAME, points=points)

    def search(self, query_vector: list[float], top_k: int = 4) -> list[str]:
        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
        ).points
        return [r.payload["text"] for r in results]

    def count(self) -> int:
        return self.client.count(collection_name=COLLECTION_NAME).count
```

- [ ] **Step 2: Manually verify with dummy vectors (isolated test path, doesn't touch real data)**

Run:
```
python -c "
from chunking import Chunk
from vector_store import VectorStore

store = VectorStore(path='qdrant_storage_test')
chunks = [Chunk(text='chunk uno', index=0, token_count=2), Chunk(text='chunk dos', index=1, token_count=2)]
vectors = [[0.1] * 384, [0.9] * 384]
store.add_chunks(chunks, vectors)
print('count:', store.count())
results = store.search([0.1] * 384, top_k=1)
print('search result:', results)
"
```
Expected: `count: 2`, then `search result: ['chunk uno']` (the vector closest to `[0.1]*384`).

- [ ] **Step 3: Clean up the test collection folder**

Run (PowerShell): `Remove-Item -Recurse -Force qdrant_storage_test`
Expected: folder removed, no error.

- [ ] **Step 4: Commit**

```bash
git add vector_store.py
git commit -m "feat: add embedded Qdrant vector store wrapper"
```

---

### Task 6: Ingestion script (Phase 1)

**Files:**
- Create: `ingest.py`

**Interfaces:**
- Consumes: `extract_text` (Task 2), `chunk_text` (Task 3), `embed_texts` (Task 4), `VectorStore` (Task 5).
- Produces: a populated `qdrant_storage/` collection on disk — consumed by `rag.py` (Task 8) and `server.py` (Task 9) at runtime, not imported directly.

- [ ] **Step 1: Write `ingest.py`**

```python
from pathlib import Path

from chunking import chunk_text
from embeddings import embed_texts
from pdf_utils import extract_text
from vector_store import VectorStore

DATA_DIR = Path("data")


def find_pdf() -> Path:
    pdfs = list(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"No se encontró ningún PDF en {DATA_DIR}/. Coloca un archivo .pdf ahí primero."
        )
    return pdfs[0]


def main() -> None:
    pdf_path = find_pdf()
    print(f"Procesando: {pdf_path}")

    text = extract_text(str(pdf_path))
    print(f"Texto extraído: {len(text)} caracteres")

    chunks = chunk_text(text)
    total_tokens = sum(c.token_count for c in chunks)
    print(f"Chunks generados: {len(chunks)} (~{total_tokens} tokens en total)")

    print("Generando embeddings (esto puede tardar varios minutos en un PDF grande)...")
    vectors = embed_texts([c.text for c in chunks])
    print(f"Embeddings generados: {len(vectors)} vectores de dimensión {len(vectors[0])}")

    store = VectorStore()
    store.add_chunks(chunks, vectors)
    print(f"Guardado en Qdrant. Total de puntos en la colección: {store.count()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full ingestion against the real PDF**

Run: `python ingest.py`
Expected: prints each pipeline stage's progress (character count → chunk/token count → embedding
count → final Qdrant point count). For a ~46MB grammar reference PDF this can take several
minutes, mostly in the embedding step — that's expected, not a hang. The final printed point
count must be greater than 0 and equal to the printed chunk count.

- [ ] **Step 3: Verify persistence — reopen the store in a fresh process**

Run: `python -c "from vector_store import VectorStore; print(VectorStore().count())"`
Expected: prints the same point count as the end of Step 2, confirming `qdrant_storage/` persisted
to disk correctly and survives a new Python process.

- [ ] **Step 4: Commit**

```bash
git add ingest.py
git commit -m "feat: add Phase 1 ingestion script (PDF to Qdrant)"
```

---

### Task 7: LLM call via Ollama

**Files:**
- Create: `llm.py`

**Interfaces:**
- Consumes: nothing (wraps the external `ollama` package).
- Produces: `call_ollama(prompt: str) -> str` — used by `rag.py` (Task 8).

- [ ] **Step 1: Write `llm.py`**

```python
import ollama

MODEL_NAME = "llama3.2"


def call_ollama(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]
```

- [ ] **Step 2: Confirm Ollama is installed and the model is available**

Run: `ollama list`
Expected: `llama3.2` appears in the list. If Ollama itself isn't installed, install it from
`https://ollama.com` first; if the model isn't listed, run `ollama pull llama3.2` (a few GB
download, one-time) before continuing.

- [ ] **Step 3: Manually verify the wrapper**

Run: `python -c "from llm import call_ollama; print(call_ollama('Responde solo con la palabra: hola'))"`
Expected: prints a short response from the model containing something like "hola" — confirms the
Python↔Ollama connection works end to end. If this errors with a connection refused, run
`ollama serve` in a separate terminal first (recent Ollama installs usually run this as a
background service automatically, so this is only needed if the connection fails).

- [ ] **Step 4: Commit**

```bash
git add llm.py
git commit -m "feat: add Ollama LLM call wrapper"
```

---

### Task 8: RAG orchestration

**Files:**
- Create: `rag.py`

**Interfaces:**
- Consumes: `embed_texts` (Task 4), `VectorStore` (Task 5), `call_ollama` (Task 7).
- Produces: `build_prompt(question: str, retrieved_chunks: list[str]) -> str`, `answer_question(question: str, store: VectorStore, top_k: int = 4) -> str` — used by `server.py` (Task 9).

- [ ] **Step 1: Write `rag.py`**

```python
from embeddings import embed_texts
from llm import call_ollama
from vector_store import VectorStore

SYSTEM_PROMPT = (
    "Eres un asistente que responde preguntas basándose ÚNICAMENTE en el contexto "
    "proporcionado a continuación, extraído de un documento PDF. Si la respuesta no "
    "está en el contexto, dilo explícitamente en vez de inventar información."
)


def build_prompt(question: str, retrieved_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(retrieved_chunks)
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"CONTEXTO:\n{context}\n\n"
        f"PREGUNTA: {question}\n\n"
        f"RESPUESTA:"
    )


def answer_question(question: str, store: VectorStore, top_k: int = 4) -> str:
    query_vector = embed_texts([question])[0]
    retrieved_chunks = store.search(query_vector, top_k=top_k)
    prompt = build_prompt(question, retrieved_chunks)
    return call_ollama(prompt)
```

- [ ] **Step 2: Manually verify against the ingested PDF**

Run (use a question relevant to your PDF's actual content — for the Spanish grammar reference,
something like "¿qué es un sintagma nominal?" is a reasonable smoke test; adjust to your PDF):
```
python -c "
from vector_store import VectorStore
from rag import answer_question

store = VectorStore()
print(answer_question('¿qué es un sintagma nominal?', store))
"
```
Expected: a coherent answer in Spanish that reflects real content from the PDF (not a generic
"I don't have information" answer, assuming the topic is actually covered in the document) — this
confirms retrieval is pulling relevant chunks and the model is grounding its answer in them.

- [ ] **Step 3: Verify the "not in the document" path**

Run:
```
python -c "
from vector_store import VectorStore
from rag import answer_question

store = VectorStore()
print(answer_question('¿cuál es la capital de Australia?', store))
"
```
Expected: the model says it doesn't know / the document doesn't cover this, rather than
confidently answering "Canberra" from its own training knowledge — confirms the system prompt is
actually constraining the model to the retrieved context.

- [ ] **Step 4: Commit**

```bash
git add rag.py
git commit -m "feat: add RAG prompt building and question answering"
```

---

### Task 9: WebSocket server (Phase 2)

**Files:**
- Create: `server.py`

**Interfaces:**
- Consumes: `VectorStore` (Task 5), `answer_question` (Task 8).
- Produces: a running websocket server on `ws://localhost:8765` — this is the final user-facing entry point, nothing later depends on it programmatically.

- [ ] **Step 1: Write `server.py`**

```python
import asyncio

import websockets

from rag import answer_question
from vector_store import VectorStore

HOST = "localhost"
PORT = 8765

store = VectorStore()


async def handler(websocket) -> None:
    if store.count() == 0:
        await websocket.send(
            "Aviso: la colección de Qdrant está vacía. Ejecuta 'python ingest.py' "
            "antes de hacer preguntas."
        )
    async for message in websocket:
        question = message.strip()
        if not question:
            continue
        try:
            answer = answer_question(question, store)
        except Exception as exc:
            answer = f"Error al generar la respuesta: {exc}"
        await websocket.send(answer)


async def main() -> None:
    async with websockets.serve(handler, HOST, PORT):
        print(f"Servidor websocket escuchando en ws://{HOST}:{PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Start the server**

Run: `python server.py`
Expected: prints `Servidor websocket escuchando en ws://localhost:8765` and keeps running
(this terminal is now occupied by the server — open a second terminal for the next step).

- [ ] **Step 3: Connect a test client and ask a question**

In a second terminal, with the same virtual environment activated:
```
python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8765') as ws:
        await ws.send('¿qué es un sintagma nominal?')
        print(await ws.recv())

asyncio.run(test())
"
```
Expected: prints a coherent Spanish answer reflecting real PDF content — same behavior as Task 8
Step 2, but now arriving over the actual websocket connection end to end.

- [ ] **Step 4: Stop the server**

In the first terminal, press `Ctrl+C`.
Expected: the process exits cleanly.

- [ ] **Step 5: Commit**

```bash
git add server.py
git commit -m "feat: add websocket chat server for RAG queries"
```

---

### Task 10: README and final commit

**Files:**
- Create: `README.md`

**Interfaces:**
- Produces: nothing importable — documentation only.

- [ ] **Step 1: Write `README.md`**

```markdown
# PDF RAG WebSocket Chat

Chat en tiempo real por websockets que responde preguntas sobre el contenido de un PDF,
usando RAG (Retrieval Augmented Generation). Todo el pipeline es gratis y corre en local:
sin API keys, sin servicios de pago.

## Requisitos previos

1. Python 3.10+
2. [Ollama](https://ollama.com) instalado (gratis)
3. El modelo de Ollama descargado una vez:
   ```
   ollama pull llama3.2
   ```

## Instalación

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

1. Coloca tu PDF en la carpeta `data/` (ya debería haber uno ahí).
2. Ejecuta la ingesta una vez (extrae texto, trocea, genera embeddings, guarda en Qdrant):
   ```
   python ingest.py
   ```
   Puede tardar varios minutos en un PDF grande — el grueso del tiempo es la generación de
   embeddings.
3. Levanta el servidor de chat:
   ```
   python server.py
   ```
4. Conéctate con cualquier cliente websocket a `ws://localhost:8765` y envía preguntas sobre
   el contenido del PDF como mensajes de texto.

## Arquitectura

Ver `docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md` para el diseño completo.

Resumen: `ingest.py` (Fase 1, offline) extrae el texto del PDF, lo trocea, cuenta tokens,
genera un embedding por chunk con `sentence-transformers` y lo guarda en una colección de
Qdrant embebida (`qdrant_storage/`, sin Docker). `server.py` (Fase 2) escucha conexiones
websocket; cada pregunta se convierte en embedding con el mismo modelo, se buscan los chunks
más relevantes en Qdrant, y se construye un prompt que se envía a un modelo local de Ollama
(`llama3.2`) para generar la respuesta final.

## Notas

- Nada de este proyecto llama a una API de pago. La generación de respuestas corre en tu
  máquina vía Ollama.
- El PDF original no se sube a git (ver `.gitignore`) — solo el código y la configuración.
```

- [ ] **Step 2: Verify the full pipeline one more time from scratch (sanity check)**

Run: `python -c "from vector_store import VectorStore; print('puntos en la colección:', VectorStore().count())"`
Expected: prints a point count greater than 0, confirming the whole system is in a working,
demoable state after all tasks.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```
