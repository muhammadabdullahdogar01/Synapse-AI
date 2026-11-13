import re
from pathlib import Path

from core.document_reader import SUPPORTED_EXTENSIONS

# Project storage directory
PROJECT_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_DIR / "workspace" / "uploads"

ALLOWED_EXTENSIONS = SUPPORTED_EXTENSIONS
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def unique_destination(destination):
    """Never overwrite: report.pdf -> report (1).pdf -> report (2).pdf ..."""
    destination = Path(destination)
    if not destination.exists():
        return destination
    counter = 1
    while True:
        candidate = destination.with_name(f"{destination.stem} ({counter}){destination.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def save_uploaded_files(uploaded_files):
    """Save uploaded PDF and DOCX files to the project workspace."""

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    saved_files = []

    for uploaded_file in uploaded_files:
        original_name = Path(uploaded_file.name).name
        extension = Path(original_name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            continue

        file_data = uploaded_file.getvalue()

        if len(file_data) > MAX_FILE_SIZE:
            continue

        # Clean filename
        safe_name = re.sub(
            r"[^A-Za-z0-9._-]",
            "_",
            Path(original_name).stem
        )

        safe_name = safe_name.strip("._") or "document"

        filename = safe_name + extension
        destination = UPLOAD_DIR / filename

        # Avoid overwriting existing files
        counter = 1

        while destination.exists():
            filename = f"{safe_name}_{counter}{extension}"
            destination = UPLOAD_DIR / filename
            counter += 1

        # Save a copy of the uploaded document
        with destination.open("xb") as file:
            file.write(file_data)

        saved_files.append({
            "name": filename,
            "path": str(destination),
            "size": len(file_data)
        })

    return saved_files


def get_saved_documents():
    """Return saved PDF and DOCX documents."""

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    return sorted(
        [
            file for file in UPLOAD_DIR.iterdir()
            if file.is_file()
            and file.suffix.lower() in ALLOWED_EXTENSIONS
        ],
        key=lambda file: file.name.lower()
    )
