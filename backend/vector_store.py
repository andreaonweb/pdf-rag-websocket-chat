from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION_NAME = "pdf_chunks"
VECTOR_SIZE = 384  # output size of paraphrase-multilingual-MiniLM-L12-v2


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
