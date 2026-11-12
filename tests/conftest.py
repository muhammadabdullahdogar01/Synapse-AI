"""Shared test setup: every test gets its own empty database and sample files."""
import sys
from pathlib import Path

import pymupdf
import pytest
from docx import Document
from pptx import Presentation

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core.db as db  # noqa: E402


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Never touch the real workspace/synapse.db during tests."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    yield tmp_path / "test.db"


def make_pdf(path, pages):
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def make_docx(path, paragraphs):
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(path)


def make_pptx(path, slides):
    prs = Presentation()
    for title, body in slides:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = title
        slide.placeholders[1].text = body
    prs.save(path)


@pytest.fixture
def sample_folder(tmp_path):
    """A small, realistic student folder."""
    folder = tmp_path / "University"
    folder.mkdir()
    make_pdf(folder / "lecture1.pdf", [
        "Introduction to networks",
        "A firewall filters traffic. Cybersecurity protects systems.",
    ])
    make_docx(folder / "db_notes.docx", ["Database normalization", "SQL joins combine tables"])
    make_pptx(folder / "slides.pptx", [("Operating Systems", "Processes and threads")])
    (folder / "todo.txt").write_text("Buy milk and study cyber security", encoding="utf-8")
    (folder / "photo.jpg").write_bytes(b"\xff\xd8 not really a jpeg")
    (folder / ".hidden.txt").write_text("secret", encoding="utf-8")
    (folder / "~$temp.docx").write_bytes(b"word lock file")
    skipped = folder / "venv"
    skipped.mkdir()
    (skipped / "inside.txt").write_text("should be skipped", encoding="utf-8")
    return folder
