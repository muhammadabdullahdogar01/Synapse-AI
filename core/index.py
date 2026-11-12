"""Persistent document index: remembers extracted text in SQLite so that
files are only re-read when they actually change."""
import hashlib
from collections import Counter
from datetime import datetime
from pathlib import Path

from core.db import connect
from core.document_reader import extract_document_text


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def get_text(conn, path, stat):
    """Return (text, hash) for a file, using the saved copy if the file is unchanged."""
    key = str(path)
    row = conn.execute(
        "SELECT mtime, size, text, text_hash FROM documents WHERE path = ?", (key,)
    ).fetchone()
    if row and row["mtime"] == stat.st_mtime and row["size"] == stat.st_size:
        return row["text"], row["text_hash"]

    try:
        text = extract_document_text(path)
    except Exception:
        text = ""  # corrupted or password-protected: skip, don't crash

    digest = text_hash(text)
    conn.execute(
        """INSERT INTO documents (path, mtime, size, text_hash, text, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(path) DO UPDATE SET mtime = excluded.mtime, size = excluded.size,
               text_hash = excluded.text_hash, text = excluded.text, indexed_at = excluded.indexed_at""",
        (key, stat.st_mtime, stat.st_size, digest, text, datetime.now().isoformat(timespec="seconds")),
    )
    return text, digest


def prune_missing():
    """Forget files that no longer exist, and vectors/summaries nobody uses."""
    with connect() as conn:
        paths = [r["path"] for r in conn.execute("SELECT path FROM documents")]
        gone = [(p,) for p in paths if not Path(p).exists()]
        conn.executemany("DELETE FROM documents WHERE path = ?", gone)
        conn.execute("DELETE FROM chunks WHERE text_hash NOT IN (SELECT text_hash FROM documents)")
        conn.execute("DELETE FROM summaries WHERE text_hash NOT IN (SELECT text_hash FROM documents)")
    return len(gone)


def get_stats():
    """Numbers for the dashboard."""
    with connect() as conn:
        rows = conn.execute("SELECT path, size, text_hash FROM documents").fetchall()
        embedded = {r[0] for r in conn.execute("SELECT DISTINCT text_hash FROM chunks")}
    existing = [r for r in rows if Path(r["path"]).exists()]
    return {
        "documents": len(existing),
        "total_mb": sum(r["size"] for r in existing) / (1024 * 1024),
        "by_type": Counter(Path(r["path"]).suffix.lower().lstrip(".") for r in existing),
        "semantic_ready": sum(1 for r in existing if r["text_hash"] in embedded),
    }
