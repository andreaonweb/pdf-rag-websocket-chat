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
