import pytest

from core.document_reader import extract_document_text


def test_reads_pdf_with_page_markers(sample_folder):
    text = extract_document_text(sample_folder / "lecture1.pdf")
    assert "--- Page 1 ---" in text and "--- Page 2 ---" in text
    assert "firewall" in text


def test_reads_docx(sample_folder):
    text = extract_document_text(sample_folder / "db_notes.docx")
    assert "Database normalization" in text
    assert "SQL joins" in text


def test_reads_pptx_slides_as_pages(sample_folder):
    text = extract_document_text(sample_folder / "slides.pptx")
    assert "--- Page 1 ---" in text
    assert "Operating Systems" in text and "Processes and threads" in text


def test_reads_txt(sample_folder):
    assert "milk" in extract_document_text(sample_folder / "todo.txt")


def test_rejects_unsupported_type(sample_folder):
    with pytest.raises(ValueError):
        extract_document_text(sample_folder / "photo.jpg")
