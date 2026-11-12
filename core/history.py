import shutil
from datetime import datetime
from pathlib import Path

from core.db import connect


def start_operation(instruction, folder):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO operations (created_at, instruction, folder) VALUES (?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), instruction, str(folder)),
        )
        return cur.lastrowid


def log_action(operation_id, action_type, source, destination):
    with connect() as conn:
        conn.execute(
            "INSERT INTO actions (operation_id, action_type, source, destination) VALUES (?, ?, ?, ?)",
            (operation_id, action_type, str(source), str(destination)),
        )


def get_operations():
    with connect() as conn:
        rows = conn.execute("""
            SELECT o.*, COUNT(a.id) AS action_count
            FROM operations o LEFT JOIN actions a ON a.operation_id = o.id
            GROUP BY o.id ORDER BY o.id DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_actions(operation_id):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM actions WHERE operation_id = ? ORDER BY id", (operation_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def undo_operation(operation_id):
    """Put every file of an operation back where it was (newest change first).
    Works for both moves and renames, because each action stores the old and new path."""
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
            if destination.parent != source.parent:
                try:
                    destination.parent.rmdir()  # only succeeds if the folder is now empty
                except OSError:
                    pass
        except Exception as error:
            errors.append(str(error))

    with connect() as conn:
        status = "undone" if not errors else "partially undone"
        conn.execute("UPDATE operations SET status = ? WHERE id = ?", (status, operation_id))
    return restored, errors
