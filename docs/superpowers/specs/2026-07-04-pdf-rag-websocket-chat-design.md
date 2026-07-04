# PDF RAG WebSocket Chat — Diseño

## Contexto

Ejercicio de clase (segunda parte de un ejercicio de chat con websockets). Objetivo: ampliar
un chat websocket simple para que responda preguntas sobre el contenido de un PDF usando RAG
(Retrieval Augmented Generation). Es un proyecto de práctica — prioridad: **coste cero**,
simplicidad y que el usuario entienda cada pieza del pipeline.

PDF de prueba ya colocado en `data/` (una gramática descriptiva del español, ~46MB).

## Requisito no negociable: todo gratis

Ningún componente puede depender de una API de pago, ni siquiera de céntimos por request.
Esto descarta la API de Claude/Anthropic para la generación de respuestas (se consideró y se
descartó explícitamente a petición del usuario). Todo el pipeline corre en local.

## Stack elegido

| Pieza | Elección | Por qué |
|---|---|---|
| Extracción de texto PDF | `pypdf` | Ligera, pura Python, suficiente para texto plano |
| Chunking | Splitter manual (por caracteres + solapamiento) | Sin dependencias extra, fácil de entender |
| Conteo de tokens | `tiktoken` (cl100k_base) | Aproximación estándar, gratis, local, solo para dimensionar chunks/contexto |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local, gratis, rápido en CPU, buen soporte multilingüe básico |
| Base de datos vectorial | `qdrant-client` en modo embebido (local, sin Docker) | Cero configuración, sin servidor aparte, gratis |
| Generación de respuesta (LLM) | **Ollama** local (modelo `llama3.2`) | Gratis, corre en local, sin API key, calidad razonable para práctica |
| Servidor tiempo real | Librería `websockets` (Python) | Ligera, directa, ideal para aprender el protocolo sin capas extra |
| Entrada del PDF | Ruta local fija (`data/*.pdf`) | Ya lo puso el usuario ahí; no hace falta UI de subida |

**Nota sobre Ollama:** requiere tener instalado el binario de Ollama (https://ollama.com,
gratis) y haber hecho `ollama pull llama3.2` una vez. Si el usuario no lo tiene instalado,
ese es el único paso "externo" del proyecto — se documentará claramente en el README.

## Arquitectura — dos fases

### Fase 1: Ingesta (offline, un script, se corre una vez por PDF)

```
PDF (data/*.pdf)
  → extraer texto (pypdf)
  → trocear en chunks con overlap (splitter manual)
  → contar tokens por chunk (tiktoken, informativo/logging)
  → generar embedding por chunk (sentence-transformers)
  → guardar (vector + texto + metadata) en Qdrant (local, embebido)
```

### Fase 2: Servidor de chat (websocket, tiempo real)

```
Cliente conecta por WS
  → usuario envía pregunta (texto)
  → embedding de la pregunta (mismo modelo que en ingesta)
  → búsqueda top-k en Qdrant (similitud coseno)
  → construir prompt: system + chunks recuperados + pregunta
  → llamar a Ollama (local) con ese prompt
  → enviar respuesta de vuelta al cliente por WS
```

## Estructura de carpetas

```
pdf-rag-websocket-chat/
├── data/
│   └── *.pdf                      # PDF fuente (ya presente)
├── qdrant_storage/                # datos de Qdrant embebido (autogenerado, en .gitignore)
├── ingest.py                      # Fase 1 completa
├── rag.py                         # funciones compartidas (embed, search, build_prompt, call_ollama)
├── server.py                      # Fase 2: servidor websocket
├── requirements.txt
├── .gitignore
└── README.md
```

## Manejo de errores (alcance práctica, no producción)

- PDF no encontrado / carpeta `data/` vacía → el script de ingesta falla con mensaje claro,
  no intenta adivinar.
- Colección de Qdrant vacía cuando arranca el servidor (no se ha corrido `ingest.py` antes)
  → el servidor avisa por consola y por WS al primer mensaje, no crashea silenciosamente.
- Ollama no disponible (no instalado / servicio no corriendo) → error claro devuelto por WS
  explicando cómo arrancarlo (`ollama serve` / instalar el modelo).
- Errores por mensaje de un cliente websocket no tumban el servidor ni afectan a otros clientes
  conectados.

## Testing / verificación

No se plantean tests automatizados formales (fuera de alcance para el ejercicio). Verificación
manual: correr `ingest.py` sobre el PDF de `data/`, comprobar que la colección de Qdrant tiene
puntos; levantar `server.py`, conectar con un cliente websocket simple (ej. `websocat` o un
script de prueba) y hacer 2-3 preguntas sobre el contenido del PDF, comprobando que las
respuestas citan/reflejan contenido real del documento.

## Fuera de alcance

- Despliegue en Render/hosting — explícitamente descartado por el usuario, solo local.
- UI web de chat — el ejercicio es sobre el protocolo websocket + RAG, no sobre frontend.
- Autenticación, múltiples PDFs simultáneos, multi-usuario con aislamiento de datos.
