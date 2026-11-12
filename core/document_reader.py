from pathlib import Path

import pymupdf as fitz
from docx import Document
from pptx import Presentation

# Every file type SYNAPSE AI can read the text of
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}


def read_pdf(file_path):
    """Extract text from a PDF, marking where each page starts."""
    text = []
    with fitz.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text.append(f"\n--- Page {page_number} ---\n{page.get_text()}")
    return "\n".join(text)


def read_docx(file_path):
    """Extract text from a Word document: paragraphs, then tables."""
    document = Document(file_path)
    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def read_pptx(file_path):
    """Extract text from a PowerPoint file. Each slide is treated as a page."""
    presentation = Presentation(file_path)
    text = []
    for number, slide in enumerate(presentation.slides, start=1):
        lines = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                lines.extend(p.text for p in shape.text_frame.paragraphs if p.text.strip())
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                lines.append(f"Notes: {notes}")
        text.append(f"\n--- Page {number} ---\n" + "\n".join(lines))
    return "\n".join(text)


def read_text_file(file_path):
    """Read a plain text or Markdown file."""
    return Path(file_path).read_text(encoding="utf-8", errors="replace")


READERS = {
    ".pdf": read_pdf,
    ".docx": read_docx,
    ".pptx": read_pptx,
    ".txt": read_text_file,
    ".md": read_text_file,
}


def extract_document_text(file_path):
    """Choose the correct reader based on file extension."""
    file_path = Path(file_path)
    reader = READERS.get(file_path.suffix.lower())
    if reader is None:
        raise ValueError("Unsupported document format.")
    return reader(file_path)
