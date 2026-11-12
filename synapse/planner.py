import json
import ollama

MODEL = "qwen3:4b"

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["organize", "search", "summarize", "find_duplicates", "rename"]},
        "file_types": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["intent", "file_types", "keywords"],
}

SYSTEM_PROMPT = """You convert a user's file-management instruction into a JSON plan.

Choose exactly one intent:
- organize: sort or move files into folders (by subject, type, date...)
- search: find or list files matching a topic, name or type
- summarize: explain or summarize the content of documents
- find_duplicates: ONLY when the user asks about duplicate, copied or identical files
- rename: give files better or clearer names

file_types: lowercase extensions without dots (pdf, docx, pptx...). Empty list if none mentioned.
keywords: important topic words from the instruction. Empty list if none.

Examples:
"Find all PDF files related to cybersecurity"
-> {"intent": "search", "file_types": ["pdf"], "keywords": ["cybersecurity"]}

"Organize my university documents by subject"
-> {"intent": "organize", "file_types": [], "keywords": ["university", "subject"]}

"Are there any duplicate files in my Downloads?"
-> {"intent": "find_duplicates", "file_types": [], "keywords": []}

"Summarize my database lecture notes"
-> {"intent": "summarize", "file_types": [], "keywords": ["database", "lecture notes"]}

"Give my Word files proper names"
-> {"intent": "rename", "file_types": ["docx"], "keywords": []}
"""


def make_plan(instruction: str) -> dict:
    """Turn a natural-language instruction into a structured plan."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": instruction},
        ],
        format=SCHEMA,
        think=False,
        options={"temperature": 0},
    )
    return json.loads(response.message.content)