import json

from core import ai

INTENTS = ["organize", "search", "summarize", "ask", "find_duplicates", "rename"]

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": INTENTS},
        "file_types": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["intent", "file_types", "keywords"],
}

SYSTEM_PROMPT = """You convert a user's file-management instruction into a JSON plan.

Choose exactly one intent:
- organize: sort or move files into folders (by subject, type, date...)
- search: find or list files matching a topic, name or type
- summarize: give an overview or summary of a document
- ask: answer a specific question using what is written inside the documents
- find_duplicates: ONLY when the user asks about duplicate, copied or identical files
- rename: give files better or clearer names

file_types: lowercase extensions without dots (pdf, docx, pptx, txt, md).
Only fill this when the user names a specific type. "slides" or "presentation" means pptx,
"Word" means docx, "PDF" means pdf. General words like "documents", "files", "notes"
or "papers" are NOT a file type: use an empty list.
keywords: important topic words from the instruction. Empty list if none.

Examples:
"Find all PDF files related to cybersecurity"
-> {"intent": "search", "file_types": ["pdf"], "keywords": ["cybersecurity"]}

"Find documents about text formatting"
-> {"intent": "search", "file_types": [], "keywords": ["text formatting"]}

"Organize my university documents by subject"
-> {"intent": "organize", "file_types": [], "keywords": ["university", "subject"]}

"Are there any duplicate files in my Downloads?"
-> {"intent": "find_duplicates", "file_types": [], "keywords": []}

"Summarize my database lecture notes"
-> {"intent": "summarize", "file_types": [], "keywords": ["database", "lecture notes"]}

"What is the difference between TCP and UDP according to my notes?"
-> {"intent": "ask", "file_types": [], "keywords": ["TCP", "UDP"]}

"Give my Word files proper names"
-> {"intent": "rename", "file_types": ["docx"], "keywords": []}
"""


def make_plan(instruction: str) -> dict:
    """Turn a natural-language instruction into a structured plan."""
    response = ai.chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": instruction},
    ], schema=SCHEMA)
    plan = json.loads(response.message.content)
    plan["file_types"] = [t.lower().lstrip(".") for t in plan["file_types"]]
    return plan


def is_ai_available() -> bool:
    """Check whether Ollama is running and reachable."""
    return ai.status()["online"]
