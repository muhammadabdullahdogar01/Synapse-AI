# Changelog

All notable changes to SYNAPSE AI are listed here.
Format based on [Keep a Changelog](https://keepachangelog.com/), versions follow [Semantic Versioning](https://semver.org/).

## [0.2.0] — 2026-11-12

### Added
- **Semantic search** with `nomic-embed-text` embeddings, combined with keyword search (hybrid ranking).
- **Chat with Documents** page: answers built only from your files, with file and page citations.
- **Summaries** for documents of any length, cached in the database.
- **Smart renaming** with an editable review table and undo.
- Organizer explains **why** it chose each folder.
- **Persistent document index**: unchanged files are never re-read, and moved files keep their vectors.
- Support for **PowerPoint (.pptx), .txt and .md** files, plus Word tables.
- "Ask" intent: questions typed in the AI Assistant are answered from your documents.
- Native **folder picker** (Browse button), saved subject list.
- Dashboard with real statistics and recent activity.
- `run.bat` one-click launcher.
- pytest test suite (35 tests) and a GitHub Actions workflow.
- README, MIT license, contributing guide, this changelog.

### Changed
- Default model is now `qwen3:4b-instruct` (about 7× faster than the thinking variant), with an automatic fallback to `qwen3:4b`.
- App split into one file per page using Streamlit navigation.
- One shared SQLite database module (`core/db.py`).

### Fixed
- Planner no longer treats general words like "documents" as a file-type filter.
- Missing `pandas` dependency. Versions are now pinned.

## [0.1.0] — 2026-11-11

### Added
- AI planner (instruction → JSON plan), folder scanner, keyword search with snippets.
- AI organizer with approval table, SQLite history and undo.
- Duplicate detection (SHA-256) that keeps the original.
- PDF and Word reading, document upload.
