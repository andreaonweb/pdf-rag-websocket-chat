# PDF RAG WebSocket Chat

Chat en tiempo real por websockets que responde preguntas sobre el contenido de un PDF,
usando RAG (Retrieval Augmented Generation). Todo el pipeline es gratis y corre en local:
sin API keys, sin servicios de pago.

## Requisitos previos

1. Python 3.10+
2. [Ollama](https://ollama.com/download) instalado (gratis)
3. El modelo de Ollama descargado una vez:
   ```
   ollama pull llama3.2
   ```

## Instalación

```
cd backend
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
   En un PDF grande (probado con uno de 1608 páginas) la extracción tarda segundos, pero
   generar los embeddings de todos los chunks puede tardar 10-15 minutos en CPU — es
   normal, no es que se haya colgado.
3. Levanta el servidor de chat:
   ```
   python server.py
   ```
4. Conéctate con cualquier cliente websocket a `ws://localhost:8765` y envía preguntas sobre
   el contenido del PDF como mensajes de texto. Ejemplo rápido de cliente de prueba:
   ```
   python -c "
   import asyncio, websockets

   async def test():
       async with websockets.connect('ws://localhost:8765') as ws:
           await ws.send('tu pregunta aqui')
           print(await ws.recv())

   asyncio.run(test())
   "
   ```

## Arquitectura

Ver `docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md` para el diseño
completo, y `docs/superpowers/plans/2026-07-04-pdf-rag-websocket-chat.md` para el plan de
implementación paso a paso.

Resumen: `ingest.py` (Fase 1, offline) extrae el texto del PDF con **PyMuPDF**, lo trocea,
cuenta tokens con `tiktoken`, genera un embedding por chunk con un modelo **multilingüe**
de `sentence-transformers` y lo guarda en una colección de Qdrant embebida
(`qdrant_storage/`, sin Docker). `server.py` (Fase 2) escucha conexiones websocket; cada
pregunta se convierte en embedding con el mismo modelo, se buscan los chunks más relevantes
en Qdrant, y se construye un prompt que se envía a un modelo local de Ollama (`llama3.2`)
para generar la respuesta final.

### Decisiones tomadas durante la implementación (y por qué)

- **Extracción de PDF: PyMuPDF, no pypdf ni pdfplumber.** Se probaron los tres contra el PDF
  real (1608 páginas). `pypdf` insertaba espacios erróneos dentro de palabras
  (`"pronom inales"` en vez de `"pronominales"`) de forma silenciosa. `pdfplumber` extraía
  texto limpio pero tardaba ~15 minutos en las 1608 páginas. `PyMuPDF` tarda ~11 segundos
  (mismo orden de ruido ocasional que pypdf) — para un proyecto de práctica, la velocidad
  compensa el pequeño ruido cosmético.
- **Embeddings: modelo multilingüe, no `all-MiniLM-L6-v2`.** El modelo inicial (pensado
  sobre todo para inglés) daba resultados de similitud semántica invertidos en español
  (una frase sobre un coche resultaba "más parecida" a una sobre un gato que otra frase
  sobre un felino). Se cambió a `paraphrase-multilingual-MiniLM-L12-v2`, que sí captura
  correctamente la semántica en español y mantiene la misma dimensión de vector (384).
- El texto en español a veces se ve como `�` en la consola de Windows al imprimir — es solo
  un problema de la consola mostrando Unicode, no un problema real de los datos (se verificó
  leyendo los caracteres por su código de punto Unicode).
- Puede aparecer una traza de excepción cosmética al final de scripts cortos
  (`ModuleNotFoundError: import of msvcrt halted...` desde el `__del__` de `QdrantClient`).
  Es un artefacto conocido del cierre del intérprete en Windows y no afecta el código de
  salida del proceso ni los resultados.

## Notas

- Nada de este proyecto llama a una API de pago. La generación de respuestas corre en tu
  máquina vía Ollama.
- El PDF original no se sube a git (ver `.gitignore`) — solo el código y la configuración.
