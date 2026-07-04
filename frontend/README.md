# Frontend — Chat con el PDF

Interfaz Angular para chatear con el pipeline RAG del backend por websocket.

## Requisitos

- Node.js 18+ y npm.
- El backend corriendo (ver `../backend/README.md`) — necesita el PDF ya ingerido y
  `python server.py` escuchando en `ws://localhost:8765`.

## Instalación y arranque

```
npm install
npx ng serve
```

Abre `http://localhost:4200`. El punto de estado en la cabecera indica si hay conexión con
el servidor websocket del backend.

## Estructura

- `src/app/core/websocket/` — servicio (`ChatWebsocket`) que envuelve la conexión websocket
  nativa.
- `src/app/features/chat/` — componentes de la pantalla de chat (`ChatPage`, `MessageList`,
  `MessageInput`).
- `src/app/shared/models/` — el modelo `ChatMessage`.
- `src/styles/` — tokens de color y tipografía, reset global.
- `src/config/websocket.config.ts` — URL del servidor websocket.

## Nota sobre convenciones de nombres

Este proyecto usa Angular 21 (vía `@angular/cli@21`, elegido porque la versión `latest`
requería una versión de Node más reciente de la instalada). Angular 21 eliminó el sufijo de
tipo en los nombres de archivo y clase (`chat-page.ts` + `class ChatPage`, no
`chat-page.component.ts` + `class ChatPageComponent`); todo el código de este proyecto sigue
esa convención de forma consistente.
