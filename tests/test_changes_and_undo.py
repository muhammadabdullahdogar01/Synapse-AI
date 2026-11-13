"""The most important guarantees: approved changes happen, nothing is
overwritten, and every change can be undone."""
from core import history
from core.file_manager import unique_destination
from core.organizer import apply_moves, clean_folder_name
from core.renamer import apply_renames, clean_file_name


def test_unique_destination_never_overwrites(tmp_path):
    (tmp_path / "report.pdf").write_text("a")
    (tmp_path / "report (1).pdf").write_text("b")
    assert unique_destination(tmp_path / "report.pdf").name == "report (2).pdf"
    assert unique_destination(tmp_path / "new.pdf").name == "new.pdf"


def test_clean_names():
    assert clean_folder_name("Databases / SQL") == "Databases"
    assert clean_folder_name('Bad:"Name?"') == "BadName"
    assert clean_folder_name("") == "Uncategorized"
    assert clean_file_name('Notes: TCP/IP? "v2".pdf') == "Notes TCP IP v2"
    assert clean_file_name("CON") == "CON file"
    assert clean_file_name("   ") == ""


def test_move_then_undo(sample_folder):
    source = sample_folder / "todo.txt"
    rows = [{"file": "todo.txt", "category": "Personal", "source": str(source)}]

    op_id, done, errors = apply_moves(rows, sample_folder, "organize")
    assert errors == [] and len(done) == 1
    assert (sample_folder / "Personal" / "todo.txt").exists()
    assert not source.exists()

    restored, errors = history.undo_operation(op_id)
    assert restored == 1 and errors == []
    assert source.exists()
    assert not (sample_folder / "Personal").exists()  # empty folder removed
    assert history.get_operations()[0]["status"] == "undone"


def test_move_into_folder_with_same_name_file(sample_folder):
    (sample_folder / "Personal").mkdir()
    (sample_folder / "Personal" / "todo.txt").write_text("other file")
    rows = [{"file": "todo.txt", "category": "Personal", "source": str(sample_folder / "todo.txt")}]
    apply_moves(rows, sample_folder, "organize")
    assert (sample_folder / "Personal" / "todo (1).txt").exists()
    assert (sample_folder / "Personal" / "todo.txt").read_text() == "other file"


def test_rename_then_undo(sample_folder):
    source = sample_folder / "db_notes.docx"
    rows = [{"file": source.name, "new_name": "Database Normalization Notes.docx", "source": str(source)}]

    op_id, done, errors = apply_renames(rows, sample_folder, "rename")
    assert errors == []
    renamed = sample_folder / "Database Normalization Notes.docx"
    assert renamed.exists() and not source.exists()
    assert history.get_actions(op_id)[0]["action_type"] == "rename"

    restored, errors = history.undo_operation(op_id)
    assert restored == 1 and errors == []
    assert source.exists() and not renamed.exists()


def test_missing_file_is_reported_not_crashed(sample_folder):
    rows = [{"file": "gone.txt", "category": "X", "source": str(sample_folder / "gone.txt")}]
    _, done, errors = apply_moves(rows, sample_folder, "organize")
    assert done == [] and len(errors) == 1


def test_undo_refuses_to_overwrite(sample_folder):
    source = sample_folder / "todo.txt"
    op_id, _, _ = apply_moves(
        [{"file": "todo.txt", "category": "Personal", "source": str(source)}], sample_folder, "organize")
    source.write_text("a new file with the same name")
    restored, errors = history.undo_operation(op_id)
    assert restored == 0 and len(errors) == 1
    assert source.read_text() == "a new file with the same name"
