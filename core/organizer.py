import json
import re
import shutil
from pathlib import Path

from core import ai, history
from core.file_manager import unique_destination

DEFAULT_SUBJECTS = [
    "Programming",
    "Databases",
    "Computer Networks",
    "Computer Architecture",
    "Operating Systems",
    "Cybersecurity",
    "Artificial Intelligence",
    "Software Engineering",
    "Mathematics",
    "Personal",
]

CATEGORY_PROMPT = """You sort university files into subject folders.
Read the file name and the start of its content, then choose the ONE folder
from the allowed list that best matches the file's subject.
- Use "Personal" for CVs, resumes, certificates, ID documents and similar.
- Use "Uncategorized" if no subject fits, or the content is only sample/placeholder text.
- In "reason", explain your choice in under 12 words (e.g. "Covers SQL joins and normalization")."""


def clean_folder_name(name):
    """Turn any text into a short, valid Windows folder name."""
    name = re.split(r"[/\\>|,]", name)[0]
    name = re.sub(r'[<>:"?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip(" .-")
    name = " ".join(name.split()[:3])
    return name or "Uncategorized"


def suggest_category(file, choices):
    """Ask the AI to pick ONE folder from the allowed choices, and say why."""
    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": choices},
            "reason": {"type": "string"},
        },
        "required": ["category", "reason"],
    }
    content = file.text[:600] if file.text else "(no readable text)"
    message = (
        f"Allowed folders: {', '.join(choices)}\n\n"
        f"File name: {file.name}\n"
        f"Content start:\n{content}"
    )
    response = ai.chat([
        {"role": "system", "content": CATEGORY_PROMPT},
        {"role": "user", "content": message},
    ], schema=schema)
    result = json.loads(response.message.content)
    category = result["category"] if result["category"] in choices else "Uncategorized"
    return category, result.get("reason", "").strip()


def propose_moves(files, base_folder, subjects, progress=None):
    """Ask the AI for a folder for each file. Moves NOTHING."""
    base = Path(base_folder)
    existing = [p.name for p in base.iterdir()
                if p.is_dir() and not p.name.startswith("_")]

    # User's subjects + folders that already exist + a fallback, without repeats
    choices = list(dict.fromkeys(
        [clean_folder_name(s) for s in subjects] + existing + ["Uncategorized"]
    ))

    proposals = []
    for i, f in enumerate(files, start=1):
        if progress:
            progress(i / len(files), f.name)

        category, reason = suggest_category(f, choices)

        if f.path.parent == base / category:
            continue  # already in the right place

        proposals.append({
            "move": True,
            "file": f.name,
            "category": category,
            "reason": reason,
            "source": str(f.path),
        })
    return proposals


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