# Frontend — PDF Chat UI

Angular chat interface for talking to the backend's RAG pipeline over websockets.

## Prerequisites

- Node.js 18+ and npm.
- The backend running (see [`../backend/README.md`](../backend/README.md)) — it needs the
  PDF already ingested and `python server.py` listening on `ws://localhost:8765`.

## Install and run

```
npm install
npx ng serve
```

Open `http://localhost:4200`. The status dot in the header shows whether there's an active
connection to the backend's websocket server.

**Response time:** the backend can take roughly 30-90 seconds per answer when Ollama runs
on CPU only. The "typing..." indicator stays visible the whole time — that's expected, not
a stuck connection.

## Structure

- `src/app/core/websocket/` — `ChatWebsocket`, the service wrapping the native websocket
  connection.
- `src/app/features/chat/` — the chat screen's components (`ChatPage`, `MessageList`,
  `MessageInput`).
- `src/app/shared/models/` — the `ChatMessage` model.
- `src/styles/` — color and typography tokens, global reset.
- `src/config/websocket.config.ts` — the websocket server URL.

## Visual design

Dark theme: black background (`#0a0a0a`), amber/gold accent (`#e0a458`) for the assistant
and buttons, muted teal accent (`#4a8f8c`) for the user's own messages. Headings and UI
chrome use **Space Grotesk**; message text uses **Inter** for readability on long answers.

## Naming convention note

This project uses Angular 21 (via `@angular/cli@21`, chosen because the `latest` CLI
version required a newer Node.js than the one installed on the dev machine). Angular 21
dropped the type suffix from generated file and class names (`chat-page.ts` +
`class ChatPage`, not `chat-page.component.ts` + `class ChatPageComponent`); every
hand-written file in this project follows that same convention for consistency.
