# SYNAPSE AI: notes for Claude

OSSD semester project (deadline Jan 10, 2027), built by one developer. A Streamlit app with a local AI model through Ollama.

- Run: `venv\Scripts\python.exe -m streamlit run main.py` (or `run.bat`)
- Test: `venv\Scripts\python.exe -m pytest -m "not ai"` (fast). Run `-m ai` to use the real model.
- `core/` holds the logic and has NO Streamlit imports. `app/` holds one file per page. `main.py` handles navigation.
- Models: `qwen3:4b-instruct` (preferred, chosen in `core/ai.py`) and `nomic-embed-text` (embeddings).
- The laptop CPU is slow: about 5–25 s per AI call. Keep AI calls few and show progress bars.

Safety rules: never delete user files, never overwrite (`unique_destination`), log every change
with `history.log_action` so it can be undone, and the AI only proposes while the user approves.
Tests must not need Ollama (use fakes, as in `tests/test_semantic.py`).
