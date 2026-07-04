from sentence_transformers import SentenceTransformer

# all-MiniLM-L6-v2 (English-centric) was tested first and gave backwards
# similarity scores on Spanish text (a "gato"/"coche" pair scored higher
# than "gato"/"felino"). This multilingual model fixes that: 0.833 for the
# related pair vs 0.122 for the unrelated one. Still 384-dim, similar size.
_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = load_model()
    vectors = model.encode(texts, show_progress_bar=False)
    return vectors.tolist()
