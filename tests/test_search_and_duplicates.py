import shutil

from core.duplicates import find_duplicates
from core.scanner import scan_folder
from core.search import search_files


def test_keyword_search_matches_spacing_variants(sample_folder):
    files = scan_folder(sample_folder)
    results = search_files(files, [], ["cyber security"])
    names = [r.file.name for r in results]
    assert "lecture1.pdf" in names   # contains "Cybersecurity"
    assert "todo.txt" in names       # contains "cyber security"


def test_search_filters_by_type_and_reports_page(sample_folder):
    files = scan_folder(sample_folder)
    results = search_files(files, ["pdf"], ["firewall"])
    assert [r.file.name for r in results] == ["lecture1.pdf"]
    assert results[0].page == 2
    assert "firewall" in results[0].snippet.lower()


def test_type_only_search_lists_all_of_that_type(sample_folder):
    files = scan_folder(sample_folder)
    assert [r.file.name for r in search_files(files, ["docx"], [])] == ["db_notes.docx"]


def test_duplicates_keep_the_original_name(sample_folder):
    shutil.copy(sample_folder / "todo.txt", sample_folder / "todo - Copy.txt")
    shutil.copy(sample_folder / "todo.txt", sample_folder / "todo (1).txt")
    groups = find_duplicates(scan_folder(sample_folder))
    assert len(groups) == 1
    assert groups[0][0].name == "todo.txt"
    assert len(groups[0]) == 3


def test_no_duplicates(sample_folder):
    assert find_duplicates(scan_folder(sample_folder)) == []
