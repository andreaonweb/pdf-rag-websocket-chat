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
            # answer_question() is blocking (embeddings, Qdrant, Ollama call).
            # Running it inline would freeze the event loop for the whole
            # duration, so the client's keepalive ping never gets a pong and
            # websockets drops the connection ("keepalive ping timeout").
            # asyncio.to_thread() runs it off-loop so pings keep flowing.
            answer = await asyncio.to_thread(answer_question, question, store)
        except Exception as exc:
            answer = f"Error al generar la respuesta: {exc}"
        await websocket.send(answer)


async def main() -> None:
    async with websockets.serve(handler, HOST, PORT):
        print(f"Servidor websocket escuchando en ws://{HOST}:{PORT}")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
