import fitz  # PyMuPDF


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF, one page at a time, joined with newlines.

    Uses PyMuPDF (fitz): on a 1608-page test document it extracted the full
    text in ~11 seconds versus ~15 minutes for pdfplumber. It occasionally
    inserts a stray space inside a word (e.g. "tratam iento" instead of
    "tratamiento") on documents with unusual embedded fonts, but does not
    corrupt accented characters and is dramatically faster — an accepted
    tradeoff for this practice project.
    """
    pages_text = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pages_text.append(page.get_text())
    return "\n".join(pages_text)
