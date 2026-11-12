import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "workspace" / "synapse.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS operations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    instruction TEXT NOT NULL,
    folder      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'completed'
);
CREATE TABLE IF NOT EXISTS actions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id INTEGER NOT NULL REFERENCES operations(id),
    action_type  TEXT NOT NULL,
    source       TEXT NOT NULL,
    destination  TEXT NOT NULL
);
"""


@contextmanager
def _db():
    """Open the database, commit on success, always close."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def start_operation(instruction, folder):
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO operations (created_at, instruction, folder) VALUES (?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), instruction, str(folder)),
        )
        return cur.lastrowid


def log_action(operation_id, action_type, source, destination):
    with _db() as conn:
        conn.execute(
            "INSERT INTO actions (operation_id, action_type, source, destination) VALUES (?, ?, ?, ?)",
            (operation_id, action_type, str(source), str(destination)),
        )


def get_operations():
    with _db() as conn:
        rows = conn.execute("""
            SELECT o.*, COUNT(a.id) AS action_count
            FROM operations o LEFT JOIN actions a ON a.operation_id = o.id
            GROUP BY o.id ORDER BY o.id DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_actions(operation_id):
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM actions WHERE operation_id = ? ORDER BY id", (operation_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def undo_operation(operation_id):
    """Move every file of an operation back to where it was (newest first)."""
    restored, errors = 0, []
    for action in reversed(get_actions(operation_id)):
        source, destination = Path(action["source"]), Path(action["destination"])
        try:
            if not destination.exists():
                raise FileNotFoundError(f"{destination.name} is no longer in {destination.parent}")
            if source.exists():
                raise FileExistsError(f"a file already exists at {source}")
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))
            restored += 1
            try:
                destination.parent.rmdir()  # only succeeds if the folder is now empty
            except OSError:
                pass
        except Exception as error:
            errors.append(str(error))

    with _db() as conn:
        status = "undone" if not errors else "partially undone"
        conn.execute("UPDATE operations SET status = ? WHERE id = ?", (status, operation_id))
    return restored, errors