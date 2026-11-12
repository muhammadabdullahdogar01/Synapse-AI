"""AI summaries of documents. Long documents are summarized section by
section, then the section notes are combined. Results are cached."""
from datetime import datetime

from core import ai
from core.db import connect

SECTION_CHARS = 12000   # about 3,000 tokens: fits comfortably in the model's context
MAX_SECTIONS = 6        # limit the time spent on very long documents

SUMMARY_PROMPT = """You summarize a student's document.
Write in clear, simple English using Markdown:

**Overview:** 2-3 sentences on what the document is and what it covers.

**Key points:**
- 3 to 7 bullet points with the most important ideas, facts or definitions.

Only use information from the document. Do not invent anything."""

NOTES_PROMPT = """Write 3-6 short bullet points with the key information in this
section of a document. Only use information from the text."""


def _ask(system, content):
    response = ai.chat([
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ], temperature=0.2)
    return ai.strip_thinking(response.message.content)


def get_cached(digest):
    with connect() as conn:
        row = conn.execute("SELECT summary FROM summaries WHERE text_hash = ?", (digest,)).fetchone()
        return row["summary"] if row else None


def summarize(file, progress=None):
    """Return a Markdown summary of a scanned file (FileInfo)."""
    text = file.text.strip()
    if not text:
        raise ValueError("This document has no readable text (it may be a scanned image).")

    cached = get_cached(file.text_hash)
    if cached:
        return cached

    sections = [text[i:i + SECTION_CHARS] for i in range(0, len(text), SECTION_CHARS)]
    note = ""
    if len(sections) > MAX_SECTIONS:
        note = f"\n\n*Summary based on the first {MAX_SECTIONS * SECTION_CHARS // 1000}k characters of a long document.*"
        sections = sections[:MAX_SECTIONS]

    if len(sections) == 1:
        if progress:
            progress(0.5, "Summarizing...")
        summary = _ask(SUMMARY_PROMPT, f"File name: {file.name}\n\n{sections[0]}")
    else:
        notes = []
        for i, section in enumerate(sections, start=1):
            if progress:
                progress(i / (len(sections) + 1), f"Reading part {i} of {len(sections)}...")
            notes.append(_ask(NOTES_PROMPT, section))
        if progress:
            progress(1.0, "Combining...")
        summary = _ask(
            SUMMARY_PROMPT,
            f"File name: {file.name}\n\nNotes from each part of the document:\n\n" + "\n\n".join(notes),
        )

    summary += note
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO summaries (text_hash, summary, created_at) VALUES (?, ?, ?)",
            (file.text_hash, summary, datetime.now().isoformat(timespec="seconds")),
        )
    return summary
