"""One SQLite database for everything SYNAPSE AI remembers."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "workspace" / "synapse.db"

SCHEMA = """
-- Activity history (every change can be undone)
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
    action_type  TEXT NOT NULL,          -- 'move' or 'rename'
    source       TEXT NOT NULL,
    destination  TEXT NOT NULL
);

-- Document index: extracted text, so unchanged files are never re-read
CREATE TABLE IF NOT EXISTS documents (
    path       TEXT PRIMARY KEY,
    mtime      REAL NOT NULL,
    size       INTEGER NOT NULL,
    text_hash  TEXT NOT NULL,
    text       TEXT NOT NULL,
    indexed_at TEXT NOT NULL
);

-- Semantic search: pieces of text and their embedding vectors.
-- Keyed by text_hash (not path), so moving or renaming a file keeps its vectors.
CREATE TABLE IF NOT EXISTS chunks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    text_hash TEXT NOT NULL,
    chunk_no  INTEGER NOT NULL,
    page      INTEGER,
    text      TEXT NOT NULL,
    embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(text_hash);

-- Cached AI summaries
CREATE TABLE IF NOT EXISTS summaries (
    text_hash  TEXT PRIMARY KEY,
    summary    TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- User settings (e.g. subject list)
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_initialized = set()


@contextmanager
def connect():
    """Open the database, commit on success, always close."""
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    if str(path) not in _initialized:
        conn.executescript(SCHEMA)
        _initialized.add(str(path))
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_setting(key, default=None):
    with connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key, value):
    with connect() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
