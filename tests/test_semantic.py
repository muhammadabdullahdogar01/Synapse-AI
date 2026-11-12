"""Semantic search tests use a fake embedding model, so they run without Ollama."""
import numpy as np
import pytest

from core import semantic
from core.scanner import scan_folder

TOPICS = ["network", "database", "operating", "milk"]


def fake_embed(texts):
    """A tiny pretend 'embedding': one dimension per topic word."""
    vectors = []
    for t in texts:
        t = t.lower()
        v = np.array([t.count(word) for word in TOPICS] + [0.01], dtype=np.float32)
        vectors.append(v / np.linalg.norm(v))
    return np.vstack(vectors)


@pytest.fixture
def fake_model(monkeypatch):
    monkeypatch.setattr(semantic, "_embed", fake_embed)
    monkeypatch.setattr(semantic, "MIN_SCORE", 0.5)


def test_split_into_chunks_keeps_pages():
    text = "\n--- Page 1 ---\n" + "alpha " * 200 + "\n--- Page 2 ---\n" + "beta " * 10
    chunks = semantic.split_into_chunks(text, chunk_words=100, overlap=20)
    assert {page for page, _ in chunks} == {1, 2}
    assert all(len(c.split()) <= 100 for _, c in chunks)
    assert chunks[-1] == (2, " ".join(["beta"] * 10))


def test_split_plain_text_has_no_page():
    chunks = semantic.split_into_chunks("just a short note about something useful")
    assert chunks == [(None, "just a short note about something useful")]


def test_finds_by_meaning_and_embeds_only_once(sample_folder, fake_model):
    files = scan_folder(sample_folder)
    assert semantic.ensure_embeddings(files) == 4
    assert semantic.ensure_embeddings(files) == 0  # already done

    results = semantic.semantic_search(files, "database")
    assert results[0].file.name == "db_notes.docx"
    assert results[0].relevance > 0.9


def test_hybrid_search_combines_keyword_and_meaning(sample_folder, fake_model):
    files = scan_folder(sample_folder)
    semantic.ensure_embeddings(files)
    results = semantic.hybrid_search(files, [], ["network"])
    assert results[0].file.name == "lecture1.pdf"
    assert "network" in results[0].matched


def test_moved_file_keeps_its_vectors(sample_folder, fake_model, monkeypatch):
    files = scan_folder(sample_folder)
    semantic.ensure_embeddings(files)
    (sample_folder / "Databases").mkdir()
    (sample_folder / "db_notes.docx").rename(sample_folder / "Databases" / "db_notes.docx")

    calls = []
    monkeypatch.setattr(semantic, "_embed", lambda t: calls.append(t) or fake_embed(t))
    assert semantic.ensure_embeddings(scan_folder(sample_folder)) == 0
