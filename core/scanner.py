import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.document_reader import extract_document_text

# Folders we never look inside
SKIP_DIRS = {"venv", ".venv", ".git", "__pycache__", "node_modules", "_duplicates"}

# File types we can read the text of
READABLE = {".pdf", ".docx"}


@dataclass
class FileInfo:
    path: Path
    name: str
    extension: str
    size_kb: float
    modified: datetime
    text: str = ""


def scan_folder(folder, read_content=True):
    """Walk a folder (and subfolders) and collect information about each file."""
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder not found: {folder}")

    files = []
    for root, dirs, filenames in os.walk(folder):
        # Skip hidden and system folders
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for filename in filenames:
            if filename.startswith(".") or filename.startswith("~$"):
                continue  # hidden files and Word temp files
            path = Path(root) / filename
            try:
                stat = path.stat()
            except OSError:
                continue

            text = ""
            if read_content and path.suffix.lower() in READABLE:
                try:
                    text = extract_document_text(path)
                except Exception:
                    text = ""  # corrupted or password-protected: skip, don't crash

            files.append(FileInfo(
                path=path,
                name=path.name,
                extension=path.suffix.lower().lstrip("."),
                size_kb=round(stat.st_size / 1024, 1),
                modified=datetime.fromtimestamp(stat.st_mtime),
                text=text,
            ))
    return files

def folder_signature(folder):
    """A quick fingerprint of a folder: changes when any file is added,
    removed, renamed or edited. Doesn't open the files, so it's fast."""
    entries = []
    for root, dirs, filenames in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            try:
                info = os.stat(os.path.join(root, name))
                entries.append((root, name, info.st_mtime, info.st_size))
            except OSError:
                continue
    return hash(tuple(sorted(entries)))