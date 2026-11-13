# Contributing to SYNAPSE AI

Thanks for your interest! Bug reports, ideas and pull requests are all welcome.

## Reporting a bug or suggesting a feature

Open an [issue](https://github.com/muhammadabdullahdogar01/Synapse-AI/issues) and include:
- what you did (the instruction you typed, the file types involved)
- what you expected, and what happened instead
- any error message shown in the app or the terminal

## Making a change

1. Fork the repository and create a branch: `git checkout -b feature/my-change`
2. Set up the project (see the README), then install the test tools:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Make your change. Please follow the existing structure:
   - **`core/`** holds the logic and must not import Streamlit.
   - **`app/`** holds the pages. Keep them thin and call functions in `core/`.
4. Add or update tests in `tests/`. Tests must not need Ollama: replace AI calls with fakes, as `tests/test_semantic.py` does. Mark tests that use the real model with `@pytest.mark.ai`.
5. Run `pytest` and make sure everything passes.
6. Commit with a clear message, e.g. `Add OCR for scanned PDFs`, and open a pull request explaining what changed and why.

## Safety rules (please keep these)

- Never delete user files.
- Never overwrite a file. Use `unique_destination()`.
- Every change to the file system must be logged with `history.log_action()` so it can be undone.
- The AI may only *propose* changes. The user approves them.
- No document content may be sent to online services.

## Code style

- Clear names and short functions, with a docstring on every public function.
- Comments explain *why*, not *what*.
