# Angular Chat Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the repo into a monorepo (backend/ + frontend/) and build an Angular chat UI that connects to the existing websocket RAG server so the pipeline can be tested from a browser.

**Architecture:** Standalone Angular components (no NgModules), a singleton `ChatWebsocketService` wrapping the native `WebSocket` API with signals/RxJS, and three feature components (`ChatPageComponent`, `MessageListComponent`, `MessageInputComponent`) composed under a single page — no routing needed for a one-screen app.

**Tech Stack:** Angular (latest via `@angular/cli`), TypeScript, SCSS, RxJS (already an Angular dependency). No new backend dependencies.

## Global Constraints

- Dark theme: background `#0a0a0a` (see Task 3 for the full color/typography token list) — per `docs/superpowers/specs/2026-07-04-angular-chat-frontend-design.md`.
- Monorepo: existing Python backend moves into `backend/`; Angular app lives in `frontend/`. Both share the same git repo and history.
- No automated tests anywhere in the frontend (`--skip-tests` on scaffold, no `.spec.ts` files) — matches the already-approved backend decision. Verification is manual (compile checks + browser checks).
- WebSocket server address is fixed at `ws://localhost:8765` (already implemented and verified in `backend/server.py`).
- No routing, no reconnection logic, no Markdown rendering, no persistence across reloads — explicitly out of scope per the spec.

---

## File Structure

```
pdf-rag-websocket-chat/
├── backend/                       # Task 1 — existing Python, moved here unchanged
│   ├── data/, qdrant_storage/, .venv/
│   ├── *.py, requirements.txt
│   └── README.md                  # Task 1 — moved from repo root
├── frontend/                      # Task 2 — new Angular app
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/websocket/chat-websocket.service.ts      # Task 5
│   │   │   ├── features/chat/
│   │   │   │   ├── chat-page/chat-page.component.{ts,html,scss}       # Task 8
│   │   │   │   ├── message-list/message-list.component.{ts,html,scss} # Task 7
│   │   │   │   └── message-input/message-input.component.{ts,html,scss} # Task 6
│   │   │   ├── shared/models/chat-message.model.ts           # Task 4
│   │   │   ├── app.component.{ts,html,scss}                  # Task 2 (scaffold) + Task 8 (wiring)
│   │   │   └── app.config.ts                                 # Task 2, untouched after
│   │   ├── styles/_variables.scss, _reset.scss                # Task 3
│   │   ├── config/websocket.config.ts                         # Task 4
│   │   ├── index.html                                          # Task 2 (scaffold) + Task 3 (fonts)
│   │   ├── main.ts                                             # Task 2, untouched
│   │   └── styles.scss                                         # Task 3
│   ├── angular.json, package.json, tsconfig.json               # Task 2
│   └── README.md                                                # Task 9
├── docs/
└── README.md                       # Task 9 — new monorepo overview
```

No `app.routes.ts` — the spec listed one, but a single-screen chat app needs no routing, so it's dropped (YAGNI). `AppComponent` renders `ChatPageComponent` directly.

---

### Task 1: Restructure into a monorepo (backend/ + prep for frontend/)

**Files:**
- Move: `pdf_utils.py`, `chunking.py`, `embeddings.py`, `vector_store.py`, `ingest.py`, `llm.py`, `rag.py`, `server.py`, `requirements.txt`, `README.md` → `backend/`
- Move (filesystem, not git — these are gitignored/untracked): `data/`, `qdrant_storage/`, `.venv/`, `__pycache__/` → `backend/`
- Modify: `.gitignore`
- Create: `README.md` (new monorepo overview at repo root)

**Interfaces:**
- Consumes: nothing new — pure relocation, no code changes inside the moved files.
- Produces: a `backend/` directory that behaves exactly like the repo root did before, just one level deeper. Every backend command from here on is run with `backend/` as the working directory.

- [ ] **Step 1: Create the backend directory and move tracked files with git**

Run (from repo root, PowerShell):
```
New-Item -ItemType Directory -Force backend
git mv pdf_utils.py backend/pdf_utils.py
git mv chunking.py backend/chunking.py
git mv embeddings.py backend/embeddings.py
git mv vector_store.py backend/vector_store.py
git mv ingest.py backend/ingest.py
git mv llm.py backend/llm.py
git mv rag.py backend/rag.py
git mv server.py backend/server.py
git mv requirements.txt backend/requirements.txt
git mv README.md backend/README.md
```
Expected: each `git mv` prints nothing on success; `git status` afterwards shows all ten as renames (`renamed: X -> backend/X`).

- [ ] **Step 2: Move the untracked/gitignored folders with a plain filesystem move**

These are not tracked by git (they're in `.gitignore`), so `git mv` doesn't apply — move them directly:
```
Move-Item data backend/data
Move-Item qdrant_storage backend/qdrant_storage
Move-Item .venv backend/.venv
if (Test-Path __pycache__) { Move-Item __pycache__ backend/__pycache__ }
```
Expected: no errors. `Get-ChildItem backend` now shows `data`, `qdrant_storage`, `.venv` alongside the moved `.py` files.

- [ ] **Step 3: Update `.gitignore` for the new layout**

Replace the contents of `.gitignore` with:
```
backend/qdrant_storage/
backend/data/*.pdf
backend/.venv/
**/__pycache__/
*.pyc
frontend/node_modules/
frontend/dist/
frontend/.angular/
```

- [ ] **Step 4: Write the new root `README.md` (monorepo overview)**

```markdown
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
```

- [ ] **Step 5: Update `backend/README.md` to account for the new working directory**

Open `backend/README.md` and replace the "Instalación" and "Uso" code blocks so every command
assumes you're already inside `backend/` (the paths themselves — `data/`, `qdrant_storage/`,
`ingest.py`, etc. — are unchanged, since they're relative to `backend/` now, not the repo root):

```markdown
## Instalación

```
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
```

(The rest of `backend/README.md` — Uso, Arquitectura, Decisiones, Notas — stays as-is; only
the `cd backend` line is new, added before the existing `python -m venv .venv` line.)

- [ ] **Step 6: Verify the backend still works from its new location**

Run (PowerShell, from repo root):
```
cd backend
.venv\Scripts\python.exe -c "from vector_store import VectorStore; print(VectorStore().count())"
cd ..
```
Expected: prints `8119` (the same point count as before the move) — confirms the relative
paths (`qdrant_storage`, `data`) still resolve correctly now that everything lives under
`backend/`.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: restructure into a monorepo (move backend into backend/)"
```

---

### Task 2: Scaffold the Angular app

**Files:**
- Create: `frontend/` (entire Angular CLI scaffold — `src/app/app.component.*`, `src/app/app.config.ts`, `src/main.ts`, `src/index.html`, `src/styles.scss`, `angular.json`, `package.json`, `tsconfig.json`, etc.)

**Interfaces:**
- Consumes: nothing.
- Produces: a working `ng serve`-able Angular app with the default welcome page, ready for later tasks to add components into. `AppComponent` at `frontend/src/app/app.component.ts` is the file Task 8 will modify last.

- [ ] **Step 1: Run the Angular CLI scaffold from the repo root**

Run (PowerShell, from repo root):
```
npx @angular/cli@latest new frontend --style=scss --skip-tests --routing=false --ssr=false --skip-git --package-manager=npm
```
If the CLI still prompts interactively for anything not covered by these flags, accept the
default for each prompt. Expected: creates `frontend/`, runs `npm install` automatically, and
ends with a message like `✔ Packages installed successfully` (exact wording varies by CLI
version). `frontend/node_modules/` will exist afterward.

- [ ] **Step 2: Verify the scaffold builds and serves**

Run:
```
cd frontend
npx ng build
cd ..
```
Expected: build completes with no errors, prints an output bundle summary. This confirms the
scaffold itself is sound before we start adding our own code.

- [ ] **Step 3: Commit**

```bash
git add frontend
git commit -m "chore: scaffold Angular frontend app"
```

---

### Task 3: Global styles — color/typography tokens, reset, fonts

**Files:**
- Create: `frontend/src/styles/_variables.scss`
- Create: `frontend/src/styles/_reset.scss`
- Modify: `frontend/src/styles.scss`
- Modify: `frontend/src/index.html`

**Interfaces:**
- Consumes: nothing.
- Produces: SCSS variables (`$color-background`, `$color-surface`, `$color-border`,
  `$color-text-primary`, `$color-text-secondary`, `$color-accent-primary`,
  `$color-accent-secondary`, `$color-status-connected`, `$color-status-disconnected`,
  `$font-heading`, `$font-body`) importable from any component via
  `@use '<relative-path>/styles/variables' as *;` — every later component task uses these
  exact names.

- [ ] **Step 1: Write `frontend/src/styles/_variables.scss`**

```scss
// Colors
$color-background: #0a0a0a;
$color-surface: #161616;
$color-border: #2a2a2a;

$color-text-primary: #f2f2f0;
$color-text-secondary: #9a9a94;

$color-accent-primary: #e0a458;
$color-accent-secondary: #4a8f8c;

$color-status-connected: #5fb87a;
$color-status-disconnected: #d9645f;

// Typography
$font-heading: 'Space Grotesk', sans-serif;
$font-body: 'Inter', sans-serif;
```

- [ ] **Step 2: Write `frontend/src/styles/_reset.scss`**

```scss
*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
}

body {
  background-color: #0a0a0a;
}
```

- [ ] **Step 3: Overwrite `frontend/src/styles.scss`** (Angular CLI scaffolds this file empty or with a placeholder comment — replace its full contents)

```scss
@use 'styles/variables' as *;
@use 'styles/reset';

body {
  font-family: $font-body;
}
```

- [ ] **Step 4: Add Google Fonts links to `frontend/src/index.html`**

Open `frontend/src/index.html` and add these three lines inside `<head>`, right before the
closing `</head>` tag:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap"
  rel="stylesheet"
/>
```

- [ ] **Step 5: Verify the app still builds**

Run:
```
cd frontend
npx ng build
cd ..
```
Expected: build succeeds with no SCSS errors (confirms `@use 'styles/variables'` resolves
correctly from `src/styles.scss`).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/styles frontend/src/styles.scss frontend/src/index.html
git commit -m "style: add dark theme tokens, reset, and Google Fonts"
```

---

### Task 4: Shared chat message model + websocket config

**Files:**
- Create: `frontend/src/app/shared/models/chat-message.model.ts`
- Create: `frontend/src/config/websocket.config.ts`

**Interfaces:**
- Produces: `ChatMessage` interface (`{ role: 'user' | 'assistant'; text: string; timestamp: Date }`) — used by Task 5, 7, 8. `WS_URL` constant (`'ws://localhost:8765'`) — used by Task 5.

- [ ] **Step 1: Write `frontend/src/app/shared/models/chat-message.model.ts`**

```typescript
export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}
```

- [ ] **Step 2: Write `frontend/src/config/websocket.config.ts`**

```typescript
export const WS_URL = 'ws://localhost:8765';
```

- [ ] **Step 3: Verify the app still builds**

Run:
```
cd frontend
npx ng build
cd ..
```
Expected: build succeeds (these two files aren't imported by anything yet, so this just
confirms no syntax errors).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/shared frontend/src/config
git commit -m "feat: add chat message model and websocket config"
```

---

### Task 5: ChatWebsocketService

**Files:**
- Create: `frontend/src/app/core/websocket/chat-websocket.service.ts`

**Interfaces:**
- Consumes: `WS_URL` from `../../../config/websocket.config` (Task 4).
- Produces: `ChatWebsocketService` (`providedIn: 'root'`) with `connectionStatus: Signal<'connecting' | 'connected' | 'disconnected'>`, `messages$: Observable<string>`, and `send(question: string): void` — used by `ChatPageComponent` (Task 8).

- [ ] **Step 1: Write `frontend/src/app/core/websocket/chat-websocket.service.ts`**

```typescript
import { Injectable, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { WS_URL } from '../../../config/websocket.config';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

@Injectable({ providedIn: 'root' })
export class ChatWebsocketService {
  private readonly socket: WebSocket;
  private readonly messagesSubject = new Subject<string>();

  readonly connectionStatus = signal<ConnectionStatus>('connecting');
  readonly messages$ = this.messagesSubject.asObservable();

  constructor() {
    this.socket = new WebSocket(WS_URL);

    this.socket.addEventListener('open', () => {
      this.connectionStatus.set('connected');
    });

    this.socket.addEventListener('message', (event: MessageEvent<string>) => {
      this.messagesSubject.next(event.data);
    });

    this.socket.addEventListener('close', () => {
      this.connectionStatus.set('disconnected');
    });

    this.socket.addEventListener('error', () => {
      this.connectionStatus.set('disconnected');
    });
  }

  send(question: string): void {
    this.socket.send(question);
  }
}
```

- [ ] **Step 2: Verify the app still builds**

Run:
```
cd frontend
npx ng build
cd ..
```
Expected: build succeeds. This service isn't injected anywhere yet (that happens in Task 8),
so this step only confirms the file itself compiles cleanly.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/core
git commit -m "feat: add ChatWebsocketService"
```

---

### Task 6: MessageInputComponent

**Files:**
- Create: `frontend/src/app/features/chat/message-input/message-input.component.ts`
- Create: `frontend/src/app/features/chat/message-input/message-input.component.html`
- Create: `frontend/src/app/features/chat/message-input/message-input.component.scss`

**Interfaces:**
- Consumes: `$color-*`, `$font-*` variables (Task 3).
- Produces: `MessageInputComponent` (selector `app-message-input`) with `input<boolean>() disabled` and `output<string>() send` — used by `ChatPageComponent` (Task 8).

- [ ] **Step 1: Write `message-input.component.ts`**

```typescript
import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-message-input',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './message-input.component.html',
  styleUrl: './message-input.component.scss',
})
export class MessageInputComponent {
  readonly disabled = input<boolean>(false);
  readonly send = output<string>();

  questionText = '';

  submit(): void {
    const trimmed = this.questionText.trim();
    if (!trimmed || this.disabled()) {
      return;
    }
    this.send.emit(trimmed);
    this.questionText = '';
  }
}
```

- [ ] **Step 2: Write `message-input.component.html`**

```html
<form class="message-input" (ngSubmit)="submit()">
  <input
    type="text"
    class="message-input__field"
    [(ngModel)]="questionText"
    name="question"
    placeholder="Escribe tu pregunta sobre el PDF..."
    [disabled]="disabled()"
    autocomplete="off"
  />
  <button
    type="submit"
    class="message-input__button"
    [disabled]="disabled() || !questionText.trim()"
  >
    Enviar
  </button>
</form>
```

- [ ] **Step 3: Write `message-input.component.scss`**

```scss
@use '../../../../styles/variables' as *;

.message-input {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background-color: $color-surface;
  border-top: 1px solid $color-border;

  &__field {
    flex: 1;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    border: 1px solid $color-border;
    background-color: $color-background;
    color: $color-text-primary;
    font-family: $font-body;
    font-size: 1rem;

    &::placeholder {
      color: $color-text-secondary;
    }

    &:focus {
      outline: none;
      border-color: $color-accent-primary;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &__button {
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    border: none;
    background-color: $color-accent-primary;
    color: $color-background;
    font-family: $font-heading;
    font-weight: 600;
    cursor: pointer;

    &:hover:not(:disabled) {
      opacity: 0.9;
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  }
}
```

- [ ] **Step 4: Verify the app still builds**

Run:
```
cd frontend
npx ng build
cd ..
```
Expected: build succeeds. Not yet used by `AppComponent`, so this only confirms the
component itself compiles (template, styles, and `FormsModule` import all resolve).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/chat/message-input
git commit -m "feat: add MessageInputComponent"
```

---

### Task 7: MessageListComponent

**Files:**
- Create: `frontend/src/app/features/chat/message-list/message-list.component.ts`
- Create: `frontend/src/app/features/chat/message-list/message-list.component.html`
- Create: `frontend/src/app/features/chat/message-list/message-list.component.scss`

**Interfaces:**
- Consumes: `ChatMessage` from `../../../shared/models/chat-message.model` (Task 4); `$color-*`, `$font-*` variables (Task 3).
- Produces: `MessageListComponent` (selector `app-message-list`) with `input.required<ChatMessage[]>() messages` and `input<boolean>() isWaitingForResponse` — used by `ChatPageComponent` (Task 8).

- [ ] **Step 1: Write `message-list.component.ts`**

```typescript
import { Component, input } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ChatMessage } from '../../../shared/models/chat-message.model';

@Component({
  selector: 'app-message-list',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './message-list.component.html',
  styleUrl: './message-list.component.scss',
})
export class MessageListComponent {
  readonly messages = input.required<ChatMessage[]>();
  readonly isWaitingForResponse = input<boolean>(false);
}
```

- [ ] **Step 2: Write `message-list.component.html`**

```html
<div class="message-list">
  @for (message of messages(); track message.timestamp.getTime() + message.text) {
    <div
      class="message-list__bubble"
      [class.message-list__bubble--user]="message.role === 'user'"
      [class.message-list__bubble--assistant]="message.role === 'assistant'"
    >
      <p class="message-list__text">{{ message.text }}</p>
      <span class="message-list__time">{{ message.timestamp | date: 'HH:mm' }}</span>
    </div>
  }

  @if (isWaitingForResponse()) {
    <div class="message-list__bubble message-list__bubble--assistant message-list__bubble--typing">
      <span class="message-list__dot"></span>
      <span class="message-list__dot"></span>
      <span class="message-list__dot"></span>
    </div>
  }
</div>
```

- [ ] **Step 3: Write `message-list.component.scss`**

```scss
@use '../../../../styles/variables' as *;

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;

  &__bubble {
    max-width: 70%;
    padding: 0.75rem 1rem;
    border-radius: 0.75rem;
    font-family: $font-body;
    line-height: 1.5;

    &--user {
      align-self: flex-end;
      background-color: $color-accent-secondary;
      color: $color-background;
    }

    &--assistant {
      align-self: flex-start;
      background-color: $color-surface;
      color: $color-text-primary;
      border: 1px solid $color-border;
    }

    &--typing {
      display: flex;
      gap: 0.3rem;
      align-items: center;
      padding: 1rem;
    }
  }

  &__text {
    margin: 0;
    white-space: pre-wrap;
  }

  &__time {
    display: block;
    margin-top: 0.35rem;
    font-size: 0.7rem;
    opacity: 0.6;
  }

  &__dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background-color: $color-text-secondary;
    animation: message-list-typing 1.2s infinite ease-in-out;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes message-list-typing {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}
```

- [ ] **Step 4: Verify the app still builds**

Run:
```
cd frontend
npx ng build
cd ..
```
Expected: build succeeds — confirms the `@for`/`@if` control flow, the `DatePipe` import,
and the SCSS all compile correctly.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/chat/message-list
git commit -m "feat: add MessageListComponent"
```

---

### Task 8: ChatPageComponent — wire everything together

**Files:**
- Create: `frontend/src/app/features/chat/chat-page/chat-page.component.ts`
- Create: `frontend/src/app/features/chat/chat-page/chat-page.component.html`
- Create: `frontend/src/app/features/chat/chat-page/chat-page.component.scss`
- Modify: `frontend/src/app/app.component.ts`
- Modify: `frontend/src/app/app.component.html`
- Modify: `frontend/src/app/app.component.scss`

**Interfaces:**
- Consumes: `ChatWebsocketService` (Task 5), `ChatMessage` (Task 4), `MessageListComponent` (Task 7), `MessageInputComponent` (Task 6).
- Produces: `ChatPageComponent` (selector `app-chat-page`) — the last piece; nothing later depends on it programmatically, `AppComponent` just renders it.

- [ ] **Step 1: Write `chat-page.component.ts`**

```typescript
import { Component, inject, signal } from '@angular/core';
import { ChatWebsocketService } from '../../../core/websocket/chat-websocket.service';
import { ChatMessage } from '../../../shared/models/chat-message.model';
import { MessageListComponent } from '../message-list/message-list.component';
import { MessageInputComponent } from '../message-input/message-input.component';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [MessageListComponent, MessageInputComponent],
  templateUrl: './chat-page.component.html',
  styleUrl: './chat-page.component.scss',
})
export class ChatPageComponent {
  // inject() (not constructor injection) so field initializer order below
  // is guaranteed: this field runs before `connectionStatus` reads it.
  private readonly chatWebsocketService = inject(ChatWebsocketService);

  readonly messages = signal<ChatMessage[]>([]);
  readonly isWaitingForResponse = signal(false);
  readonly connectionStatus = this.chatWebsocketService.connectionStatus;

  constructor() {
    this.chatWebsocketService.messages$.subscribe((text) => {
      this.messages.update((current) => [
        ...current,
        { role: 'assistant', text, timestamp: new Date() },
      ]);
      this.isWaitingForResponse.set(false);
    });
  }

  onSend(question: string): void {
    this.messages.update((current) => [
      ...current,
      { role: 'user', text: question, timestamp: new Date() },
    ]);
    this.isWaitingForResponse.set(true);
    this.chatWebsocketService.send(question);
  }
}
```

- [ ] **Step 2: Write `chat-page.component.html`**

```html
<div class="chat-page">
  <header class="chat-page__header">
    <h1 class="chat-page__title">Chat con el PDF</h1>
    <div class="chat-page__status">
      <span
        class="chat-page__status-dot"
        [class.chat-page__status-dot--connected]="connectionStatus() === 'connected'"
        [class.chat-page__status-dot--disconnected]="connectionStatus() === 'disconnected'"
      ></span>
      @switch (connectionStatus()) {
        @case ('connected') {
          <span>Conectado</span>
        }
        @case ('disconnected') {
          <span>Sin conexión con el servidor</span>
        }
        @default {
          <span>Conectando...</span>
        }
      }
    </div>
  </header>

  <app-message-list [messages]="messages()" [isWaitingForResponse]="isWaitingForResponse()" />

  <app-message-input [disabled]="connectionStatus() !== 'connected'" (send)="onSend($event)" />
</div>
```

- [ ] **Step 3: Write `chat-page.component.scss`**

```scss
@use '../../../../styles/variables' as *;

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: $color-background;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid $color-border;
  }

  &__title {
    margin: 0;
    font-family: $font-heading;
    font-size: 1.25rem;
    color: $color-text-primary;
  }

  &__status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: $font-heading;
    font-size: 0.85rem;
    color: $color-text-secondary;
  }

  &__status-dot {
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    background-color: $color-accent-primary;

    &--connected {
      background-color: $color-status-connected;
    }

    &--disconnected {
      background-color: $color-status-disconnected;
    }
  }
}
```

- [ ] **Step 4: Overwrite `app.component.ts`**

```typescript
import { Component } from '@angular/core';
import { ChatPageComponent } from './features/chat/chat-page/chat-page.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ChatPageComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {}
```

- [ ] **Step 5: Overwrite `app.component.html`**

```html
<app-chat-page />
```

- [ ] **Step 6: Overwrite `app.component.scss`**

```scss
:host {
  display: block;
  height: 100vh;
}
```

- [ ] **Step 7: Verify the app builds**

Run:
```
cd frontend
npx ng build
cd ..
```
Expected: build succeeds with no errors — this is the first point where every piece is
wired together and type-checked as a whole.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/app/features/chat/chat-page frontend/src/app/app.component.ts frontend/src/app/app.component.html frontend/src/app/app.component.scss
git commit -m "feat: add ChatPageComponent and wire it into AppComponent"
```

---

### Task 9: Root README, frontend README, and full manual end-to-end verification

**Files:**
- Create: `frontend/README.md`
- Verify only (no changes expected): everything from Tasks 1-8.

**Interfaces:**
- Consumes: the entire frontend app (Task 2-8) and the already-working backend (`backend/server.py`).
- Produces: nothing importable — this is the final integration check.

- [ ] **Step 1: Write `frontend/README.md`**

```markdown
# Frontend — Chat con el PDF

Interfaz Angular para chatear con el pipeline RAG del backend por websocket.

## Requisitos

- Node.js 18+ y npm.
- El backend corriendo (ver `../backend/README.md`) — necesita el PDF ya ingerido y
  `python server.py` escuchando en `ws://localhost:8765`.

## Instalación y arranque

```
npm install
ng serve
```

Abre `http://localhost:4200`. El punto de estado en la cabecera indica si hay conexión con
el servidor websocket del backend.

## Estructura

- `src/app/core/websocket/` — servicio que envuelve la conexión websocket nativa.
- `src/app/features/chat/` — componentes de la pantalla de chat (lista de mensajes, input,
  página contenedora).
- `src/app/shared/models/` — el modelo `ChatMessage`.
- `src/styles/` — tokens de color y tipografía, reset global.
- `src/config/websocket.config.ts` — URL del servidor websocket.
```

- [ ] **Step 2: Start the backend server**

Run (PowerShell, from repo root, in its own terminal — leave it running):
```
cd backend
.venv\Scripts\python.exe server.py
```
Expected: prints `Servidor websocket escuchando en ws://localhost:8765` (or is silently
running — output may be buffered; either way the process stays alive).

- [ ] **Step 3: Start the frontend dev server**

Run (PowerShell, from repo root, in a second terminal — leave it running):
```
cd frontend
npx ng serve
```
Expected: prints a message like `Local: http://localhost:4200/` and keeps running.

- [ ] **Step 4: Manually verify in the browser**

Open `http://localhost:4200` in a browser. Expected:
- The page has a black background, the title "Chat con el PDF", and a status indicator that
  turns green with the text "Conectado" within a second or two of loading.
- Type a real question about the ingested PDF (e.g. "¿qué es un sintagma nominal?") and
  press Enter or click "Enviar". The question appears immediately as a right-aligned bubble.
- A "typing" indicator (three animated dots) appears in a left-aligned bubble while waiting.
- Within a few seconds to ~1 minute (Ollama generation time), the typing indicator is
  replaced by the actual answer text in a left-aligned bubble.
- Ask a second, unrelated question (e.g. "¿cuál es la capital de Francia?") and confirm the
  same flow works and the input box remains usable across multiple turns.

- [ ] **Step 5: Stop both dev servers**

In each terminal, press `Ctrl+C` to stop `ng serve` and `python server.py`.

- [ ] **Step 6: Commit**

```bash
git add frontend/README.md
git commit -m "docs: add frontend README and complete end-to-end verification"
```
