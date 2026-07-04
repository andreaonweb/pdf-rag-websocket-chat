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
