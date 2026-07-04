from dataclasses import dataclass

import tiktoken

_encoder = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    text: str
    index: int
    token_count: int


def count_tokens(text: str) -> int:
    """Approximate token count for a piece of text (cl100k_base encoding).

    This is not Claude's exact tokenizer, but it's a standard, free, local
    estimator good enough for sizing chunks and context windows.
    """
    return len(_encoder.encode(text))


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[Chunk]:
    """Split text into overlapping character-based chunks.

    chunk_size and overlap are measured in characters, not tokens — this
    keeps the splitter dependency-free and easy to reason about.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    index = 0
    text_length = len(text)
    while start < text_length:
        end = start + chunk_size
        piece = text[start:end].strip()
        if piece:
            chunks.append(Chunk(text=piece, index=index, token_count=count_tokens(piece)))
            index += 1
        start += chunk_size - overlap
    return chunks
