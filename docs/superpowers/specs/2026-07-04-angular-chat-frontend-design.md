# Angular Chat Frontend — Diseño

## Contexto

El backend (Python, RAG sobre PDF + servidor websocket, ver
`docs/superpowers/specs/2026-07-04-pdf-rag-websocket-chat-design.md`) ya funciona y está
verificado end-to-end. Ahora se añade un frontend para poder probarlo desde el navegador en
vez de con scripts de Python sueltos. El repo pasa a ser un monorepo.

## Requisitos

- Angular + TypeScript + SCSS.
- Fondo negro; resto de colores y tipografía a elección (ver sección de diseño visual).
- Monorepo: backend y frontend conviven en el mismo repo, bien organizados en carpetas
  separadas.
- Conecta al servidor websocket existente (`ws://localhost:8765`) y permite chatear en
  tiempo real con el pipeline RAG.
- Sin tests automatizados (mismo criterio ya aprobado para el backend): solo verificación
  manual en el navegador.

## Reestructuración del monorepo

Todo el Python que hoy vive en la raíz del repo se mueve a `backend/`, sin cambiar su
contenido interno (solo la ubicación):

```
pdf-rag-websocket-chat/
├── backend/
│   ├── data/                  # PDF fuente (gitignored, ya existente)
│   ├── qdrant_storage/        # datos de Qdrant (gitignored, ya existente)
│   ├── .venv/                 # entorno virtual (gitignored, ya existente)
│   ├── pdf_utils.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── ingest.py
│   ├── llm.py
│   ├── rag.py
│   ├── server.py
│   ├── requirements.txt
│   └── README.md              # instrucciones específicas del backend (movidas del README raíz)
├── frontend/                  # Angular, nuevo
│   └── ... (ver más abajo)
├── docs/
│   └── superpowers/{specs,plans}/
├── README.md                  # overview del monorepo (nuevo, enlaza a backend/README.md y frontend/README.md)
└── .gitignore                 # actualizado con rutas relativas a backend/ y frontend/
```

El `.gitignore` raíz pasa a ignorar `backend/.venv/`, `backend/qdrant_storage/`,
`backend/data/*.pdf`, y además `frontend/node_modules/`, `frontend/dist/`,
`frontend/.angular/`.

## Frontend — arquitectura

Angular con **standalone components** (sin `NgModule`), que es el enfoque estándar para
proyectos nuevos. Angular CLI por defecto, TypeScript, SCSS.

```
frontend/
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   └── websocket/
│   │   │       └── chat-websocket.service.ts
│   │   ├── features/
│   │   │   └── chat/
│   │   │       ├── chat-page/
│   │   │       │   ├── chat-page.component.ts
│   │   │       │   ├── chat-page.component.html
│   │   │       │   └── chat-page.component.scss
│   │   │       ├── message-list/
│   │   │       │   ├── message-list.component.ts
│   │   │       │   ├── message-list.component.html
│   │   │       │   └── message-list.component.scss
│   │   │       └── message-input/
│   │   │           ├── message-input.component.ts
│   │   │           ├── message-input.component.html
│   │   │           └── message-input.component.scss
│   │   ├── shared/
│   │   │   └── models/
│   │   │       └── chat-message.model.ts
│   │   ├── app.component.ts
│   │   ├── app.component.html
│   │   ├── app.component.scss
│   │   ├── app.config.ts
│   │   └── app.routes.ts
│   ├── styles/
│   │   ├── _variables.scss    # tokens de color y tipografía
│   │   └── _reset.scss        # reset mínimo
│   ├── config/
│   │   └── websocket.config.ts  # export const WS_URL = 'ws://localhost:8765'
│   ├── index.html
│   ├── main.ts
│   └── styles.scss            # entry point global, importa variables + reset
├── angular.json
├── package.json
├── tsconfig.json
└── README.md
```

### Componentes

- **`ChatWebsocketService`** (`core/websocket/`, `providedIn: 'root'`): envuelve el
  `WebSocket` nativo del navegador.
  - Expone `connectionStatus: Signal<'connecting' | 'connected' | 'disconnected'>`.
  - Expone `messages$: Observable<string>` (o un signal equivalente) que emite cada mensaje
    de texto recibido del servidor.
  - Método `send(question: string): void` — envía el texto tal cual por el socket.
  - Abre la conexión en su constructor (se instancia una vez, singleton de raíz).
- **`ChatMessage`** (`shared/models/chat-message.model.ts`): interfaz
  `{ role: 'user' | 'assistant'; text: string; timestamp: Date }`.
- **`ChatPageComponent`** (`features/chat/chat-page/`): componente contenedor de la página.
  - Mantiene `messages: Signal<ChatMessage[]>` y `isWaitingForResponse: Signal<boolean>`.
  - Se suscribe a `ChatWebsocketService.messages$`; al llegar un mensaje, lo añade como
    `ChatMessage` con `role: 'assistant'` y pone `isWaitingForResponse` a `false`.
  - Al recibir un evento `send` de `MessageInputComponent`, añade el mensaje del usuario al
    array, pone `isWaitingForResponse` a `true`, y llama a
    `ChatWebsocketService.send(question)`.
  - Muestra en la cabecera el estado de conexión (punto de color + texto).
- **`MessageListComponent`** (`features/chat/message-list/`): recibe `messages` e
  `isWaitingForResponse` como `input()`; pinta burbujas de chat (alineadas a la derecha para
  `user`, a la izquierda para `assistant`) y, si `isWaitingForResponse` es true, una burbuja
  adicional con un indicador "escribiendo..." (animación simple de puntos).
- **`MessageInputComponent`** (`features/chat/message-input/`): input de texto + botón
  enviar. Emite un `output()` `send: string` al enviar (Enter o click). El input y el botón
  se deshabilitan si `connectionStatus() !== 'connected'` (recibido como `input()`).

### Flujo de datos

```
Usuario escribe pregunta → MessageInputComponent emite (send) →
ChatPageComponent: añade ChatMessage{role:'user'} al array, isWaitingForResponse=true →
ChatWebsocketService.send(question) → servidor Python procesa RAG →
servidor responde por el mismo socket → ChatWebsocketService.messages$ emite el texto →
ChatPageComponent: añade ChatMessage{role:'assistant'}, isWaitingForResponse=false →
MessageListComponent repinta con el nuevo mensaje
```

## Diseño visual

- **Fondo**: negro (`#0a0a0a`), superficies de tarjetas/burbujas un negro ligeramente más
  claro (`#161616`).
- **Texto**: blanco roto (`#f2f2f0`) para texto principal, gris (`#9a9a94`) para texto
  secundario (timestamps, placeholders).
- **Acento primario** (asistente, botones, foco): ámbar/dorado `#e0a458`.
- **Acento secundario** (burbujas de usuario): azul-verdoso apagado `#4a8f8c`.
- **Estado de conexión**: verde `#5fb87a` (conectado), rojo `#d9645f` (desconectado/error),
  ámbar (conectando).
- **Tipografía**: `Space Grotesk` (vía Google Fonts, cargada en `index.html`) para
  cabecera/UI (títulos, botones, estado de conexión); `Inter` para el texto de los mensajes
  del chat (máxima legibilidad en párrafos largos, ya que las respuestas del RAG pueden ser
  extensas).

## Manejo de errores

- Si el websocket falla al conectar o se cierra, `connectionStatus` pasa a `'disconnected'`;
  la UI muestra el punto en rojo, el texto "Sin conexión con el servidor", y deshabilita el
  input y el botón de enviar.
- No hay reconexión automática (fuera de alcance) — recargar la página reintenta la
  conexión desde cero.
- Si el servidor envía un mensaje de error como texto plano (p. ej. "Error al generar la
  respuesta: ..."), se muestra igual que cualquier otro mensaje del asistente — no se
  distingue especialmente, ya que el propio backend ya formatea esos errores como texto
  legible.

## Testing / verificación

Sin tests automatizados, igual que el backend. Verificación manual: levantar el backend
(`python server.py` con Ollama corriendo y el PDF ya ingerido), levantar el frontend
(`ng serve` en `frontend/`), abrir `http://localhost:4200` y hacer 2-3 preguntas reales
sobre el contenido del PDF, comprobando que aparecen en el historial con el rol correcto y
que el indicador de conexión y el de "escribiendo..." se comportan como se espera.

## Fuera de alcance

- Reconexión automática del websocket.
- Múltiples conversaciones/sesiones, historial persistente entre recargas.
- Renderizado de Markdown en las respuestas (se muestran como texto plano).
- Despliegue — solo uso local (`ng serve` + servidor Python en local).
- Autenticación o multi-usuario.
