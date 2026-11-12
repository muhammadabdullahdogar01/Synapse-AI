import json
import re
import shutil
from pathlib import Path

import ollama

from core import history
from core.planner import MODEL

CATEGORY_SCHEMA = {
    "type": "object",
    "properties": {"category": {"type": "string"}},
    "required": ["category"],
}

CATEGORY_PROMPT = """You sort university files into subject folders.
Given a file name and the start of its content, reply with ONE short folder name
(1-3 words, Title Case) for its subject, e.g. "Computer Networks", "Databases",
"Cybersecurity", "Mathematics", "Personal".
If one of the existing folders fits, reuse its EXACT name.
If the subject is unclear, use "Uncategorized"."""


def clean_folder_name(name):
    """Remove characters Windows doesn't allow in folder names."""
    name = re.sub(r'[<>:"/\\|?*]', "", name).strip(" .")
    return name[:40] or "Uncategorized"


def suggest_category(file, existing):
    content = file.text[:600] if file.text else "(no readable text)"
    message = (
        f"Existing folders: {', '.join(existing) or 'none yet'}\n\n"
        f"File name: {file.name}\n"
        f"Content start:\n{content}"
    )
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": CATEGORY_PROMPT},
            {"role": "user", "content": message},
        ],
        format=CATEGORY_SCHEMA,
        think=False,
        options={"temperature": 0},
    )
    return clean_folder_name(json.loads(response.message.content)["category"])


def propose_moves(files, base_folder, progress=None):
    """Ask the AI for a folder for each file. Moves NOTHING."""
    base = Path(base_folder)
    existing = sorted(p.name for p in base.iterdir() if p.is_dir())
    proposals = []

    for i, f in enumerate(files, start=1):
        if progress:
            progress(i / len(files), f.name)

        category = suggest_category(f, existing)
        if category not in existing:
            existing.append(category)  # helps the AI stay consistent

        if f.path.parent == base / category:
            continue  # already in the right place

        proposals.append({
            "move": True,
            "file": f.name,
            "category": category,
            "source": str(f.path),
        })
    return proposals


def unique_destination(destination):
    """Never overwrite: report.pdf -> report (1).pdf -> report (2).pdf ..."""
    if not destination.exists():
        return destination
    counter = 1
    while True:
        candidate = destination.with_name(f"{destination.stem} ({counter}){destination.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def apply_moves(proposals, base_folder, instruction):
    """Carry out APPROVED moves and record each one for undo."""
    base = Path(base_folder)
    operation_id = history.start_operation(instruction, base)
    done, errors = [], []

    for p in proposals:
        source = Path(p["source"])
        try:
            if not source.exists():
                raise FileNotFoundError("file no longer exists")
            target_dir = base / clean_folder_name(p["category"])
            target_dir.mkdir(exist_ok=True)
            destination = unique_destination(target_dir / source.name)
            shutil.move(str(source), str(destination))
            history.log_action(operation_id, "move", source, destination)
            done.append((source, destination))
        except Exception as error:
            errors.append((source.name, str(error)))

    return operation_id, done, errors
