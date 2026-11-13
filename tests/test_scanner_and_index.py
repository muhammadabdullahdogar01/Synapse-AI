import os

from core import index
from core.scanner import folder_signature, scan_folder


def test_scan_skips_hidden_temp_and_system_files(sample_folder):
    names = {f.name for f in scan_folder(sample_folder)}
    assert names == {"lecture1.pdf", "db_notes.docx", "slides.pptx", "todo.txt", "photo.jpg"}


def test_scan_reads_text_only_for_supported_types(sample_folder):
    files = {f.name: f for f in scan_folder(sample_folder)}
    assert "firewall" in files["lecture1.pdf"].text
    assert files["photo.jpg"].text == ""
    assert files["lecture1.pdf"].text_hash


def test_unchanged_files_are_not_read_again(sample_folder, monkeypatch):
    scan_folder(sample_folder)  # first scan fills the index

    calls = []
    monkeypatch.setattr(index, "extract_document_text", lambda p: calls.append(p) or "")
    scan_folder(sample_folder)
    assert calls == []  # everything came from the index


def test_changed_file_is_read_again(sample_folder):
    scan_folder(sample_folder)
    note = sample_folder / "todo.txt"
    note.write_text("New content about databases", encoding="utf-8")
    os.utime(note, (1_900_000_000, 1_900_000_000))  # make sure the timestamp changes

    files = {f.name: f for f in scan_folder(sample_folder)}
    assert "databases" in files["todo.txt"].text


def test_signature_changes_when_a_file_is_added(sample_folder):
    before = folder_signature(sample_folder)
    (sample_folder / "new.txt").write_text("hello", encoding="utf-8")
    assert folder_signature(sample_folder) != before


def test_stats_and_prune(sample_folder):
    scan_folder(sample_folder)
    assert index.get_stats()["documents"] == 4  # readable files only
    (sample_folder / "todo.txt").unlink()
    assert index.prune_missing() == 1
    assert index.get_stats()["documents"] == 3
