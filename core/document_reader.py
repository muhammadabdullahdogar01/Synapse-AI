
import pymupdf as fitz
from docx import Document
from pathlib import Path


def read_pdf(file_path):
    """Extract text from a PDF document."""

    text = []

    with fitz.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            page_text = page.get_text()

            text.append(
                f"\n--- Page {page_number} ---\n{page_text}"
            )

    return "\n".join(text)


def read_docx(file_path):
    """Extract text from a Word document."""

    document = Document(file_path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def extract_document_text(file_path):
    """Choose the correct reader based on file extension."""

    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return read_pdf(file_path)

    elif extension == ".docx":
        return read_docx(file_path)

    else:
        raise ValueError("Unsupported document format.")
