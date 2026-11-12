import streamlit as st

st.title("About SYNAPSE AI")

st.markdown("""
SYNAPSE AI is an open-source intelligent desktop assistant that helps you
organize, search and understand your documents using plain-English instructions.

### How it works
1. **You give an instruction** in normal English.
2. **The local AI model** (Qwen 3 4B via Ollama) turns it into a structured plan.
3. **SYNAPSE AI scans the folder**: file names, types and document contents.
4. **It proposes actions**: folders, moves, new names. *Nothing changes yet.*
5. **You review and approve** each change.
6. **Every change is recorded** and can be undone from the History page.

### Privacy and safety
- The AI runs **entirely on your computer**. No file content is sent to the internet.
- Files are **never deleted**. Duplicates are moved to a `_duplicates` folder.
- Existing files are **never overwritten**: names get `(1)`, `(2)`... instead.

### Technologies
Python · Streamlit · Ollama · Qwen 3 4B · nomic-embed-text · SQLite ·
PyMuPDF · python-docx · python-pptx · NumPy · pytest

**Project:** OSSD Semester Project · **License:** MIT
""")
