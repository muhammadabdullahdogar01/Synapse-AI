import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core import index
from core.db import connect
from core.document_reader import SUPPORTED_EXTENSIONS

# Folders we never look inside
SKIP_DIRS = {"venv", ".venv", ".git", "__pycache__", "node_modules", "_duplicates"}

# File types we can read the text of
READABLE = SUPPORTED_EXTENSIONS


@dataclass
class FileInfo:
    path: Path
    name: str
    extension: str
    size_kb: float
    modified: datetime
    text: str = ""
    text_hash: str = ""


def _walk(folder):
    """Yield every visible file path under a folder, skipping system folders."""
    for root, dirs, filenames in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for filename in filenames:
            if filename.startswith(".") or filename.startswith("~$"):
                continue  # hidden files and Word temp files
            yield Path(root) / filename


def scan_folder(folder, read_content=True):
    """Walk a folder (and subfolders) and collect information about each file.
    Text comes from the document index, so unchanged files are not re-read."""
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder not found: {folder}")

    files = []
    with connect() as conn:
        for path in _walk(folder):
            try:
                stat = path.stat()
            except OSError:
                continue

            text, digest = "", ""
            if read_content and path.suffix.lower() in READABLE:
                text, digest = index.get_text(conn, path, stat)

            files.append(FileInfo(
                path=path,
                name=path.name,
                extension=path.suffix.lower().lstrip("."),
                size_kb=round(stat.st_size / 1024, 1),
                modified=datetime.fromtimestamp(stat.st_mtime),
                text=text,
                text_hash=digest,
            ))
    return files


def folder_signature(folder):
    """A quick fingerprint of a folder: changes when any file is added,
    removed, renamed or edited. Doesn't open the files, so it's fast."""
    entries = []
    for path in _walk(folder):
        try:
            info = path.stat()
            entries.append((str(path), info.st_mtime, info.st_size))
        except OSError:
            continue
    return hash(tuple(sorted(entries)))
