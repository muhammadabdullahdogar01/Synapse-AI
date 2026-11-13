"""Smart renaming: suggest clear names based on what a document contains."""
import json
import re
from pathlib import Path

from core import ai, history
from core.file_manager import unique_destination

RENAME_PROMPT = """You suggest a clear, descriptive file name for a student's document,
based on its content.
- 3 to 8 words, in Title Case, e.g. "Database Normalization Lecture Notes"
  or "Computer Networks Assignment 2" or "Ali Khan Resume".
- Say what the document is about and what kind of document it is.
- Only include a date or number if it appears in the content.
- Base the name on the CONTENT. Do not reuse the current file name unless it
  already describes the content well.
- Do NOT include a file extension."""

SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
}

WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                    *(f"lpt{i}" for i in range(1, 10))}


def clean_file_name(name, max_length=80):
    """Make any text safe to use as a Windows file name (without extension)."""
    name = re.sub(r"\.(pdf|docx|pptx|txt|md)$", "", name.strip(), flags=re.IGNORECASE)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    name = name[:max_length].rstrip(" .")
    if not name:
        return ""
    if name.lower() in WINDOWS_RESERVED:
        name = f"{name} file"
    return name


def suggest_name(file):
    content = file.text[:1500]
    response = ai.chat([
        {"role": "system", "content": RENAME_PROMPT},
        {"role": "user", "content": f"Document content:\n{content}\n\n(Current file name: {file.name})"},
    ], schema=SCHEMA)
    return clean_file_name(json.loads(response.message.content)["name"])


def propose_renames(files, progress=None):
    """Suggest a new name for each readable file. Renames NOTHING."""
    readable = [f for f in files if f.text.strip()]
    proposals = []
    for i, f in enumerate(readable, start=1):
        if progress:
            progress(i / len(readable), f.name)
        new_stem = suggest_name(f)
        if not new_stem or new_stem.lower() == f.path.stem.lower():
            continue
        proposals.append({
            "rename": True,
            "file": f.name,
            "new_name": new_stem + f.path.suffix.lower(),
            "source": str(f.path),
        })
    return proposals


def apply_renames(proposals, folder, instruction):
    """Carry out APPROVED renames and record each one for undo."""
    operation_id = history.start_operation(instruction, folder)
    done, errors = [], []
    for p in proposals:
        source = Path(p["source"])
        try:
            if not source.exists():
                raise FileNotFoundError("file no longer exists")
            stem = clean_file_name(p["new_name"])  # also strips a typed extension
            if not stem:
                raise ValueError("the new name is empty")
            target = source.with_name(stem + source.suffix.lower())
            if target.name.lower() == source.name.lower():
                continue  # nothing to change
            destination = unique_destination(target)
            source.rename(destination)
            history.log_action(operation_id, "rename", source, destination)
            done.append((source, destination))
        except Exception as error:
            errors.append((source.name, str(error)))
    return operation_id, done, errors
