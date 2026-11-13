# 🧠 SYNAPSE AI

**An open-source, private desktop assistant that organizes, searches and explains your documents. You tell it what you want in plain English.**

> *"Organize my university documents by subject."*
> *"Find my notes about firewall rules."*
> *"What is the difference between TCP and UDP according to my notes?"*

SYNAPSE AI runs a language model **on your own computer** through [Ollama](https://ollama.com). Your files never leave your machine, and you don't need an API key or a subscription. It never changes a file without your approval, and every change can be undone.

![Tests](https://github.com/muhammadabdullahdogar01/Synapse-AI/actions/workflows/tests.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

---

## ✨ Features

| Feature | What it does |
|---|---|
| 🤖 **Plain-English instructions** | A local AI model turns your instruction into a structured plan (JSON-schema constrained, so the output is always valid). |
| 🔎 **Smart search** | Combines keyword matching with **semantic search** (embeddings), so it finds files by *meaning* even when the words differ. Shows the matching passage and page. |
| 💬 **Chat with your documents** | Ask questions and get answers built **only** from your files, with citations like *[1] DB_Lecture3.pdf, page 4*. |
| 🗂️ **AI organizer** | Sorts files into your subject folders and explains **why** it picked each one. |
| ✏️ **Smart renaming** | Suggests descriptive names (`doc1.docx` → `Jordan Smith Resume.docx`). |
| ✨ **Summaries** | Overview and key points for any document. Long documents are summarized section by section. Results are cached. |
| 🧬 **Duplicate detection** | Finds identical files by SHA-256 content hash. Keeps the original and moves the copies aside, **never deletes**. |
| ✅ **Review before changing** | Every move and rename is shown in an editable table first. Nothing happens until you approve. |
| ↩️ **Undo everything** | Every change is logged in SQLite and can be reversed from the History page. |
| ⚡ **Persistent index** | Extracted text and vectors are stored, so unchanged files are never re-read. Moved files keep their vectors. |

**Supported files:** PDF, Word (`.docx`), PowerPoint (`.pptx`), text (`.txt`) and Markdown (`.md`).

---

## 🚀 Quick start (Windows)

1. Install **Python 3.11+** from [python.org](https://www.python.org/downloads/) and **Ollama** from [ollama.com](https://ollama.com).
2. Download the project:
   ```bash
   git clone https://github.com/muhammadabdullahdogar01/Synapse-AI.git
   cd Synapse-AI
   ```
3. Double-click **`run.bat`**. The first run creates the virtual environment, installs the libraries, downloads the AI models (about 2.8 GB) and opens the app in your browser.

### Manual setup (any OS)

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:4b-instruct    # language model (2.5 GB)
ollama pull nomic-embed-text     # search model (274 MB)
streamlit run main.py
```

> **Why `qwen3:4b-instruct`?** The default `qwen3:4b` tag is a *thinking* model that writes a long chain of reasoning before every answer, which made it about 7× slower in our tests on a laptop CPU. SYNAPSE AI uses the Instruct version when it's installed and falls back to `qwen3:4b` otherwise.

---

## 🏗️ How it works

```
 "Organize my notes by subject"
              │
              ▼
   ┌─────────────────────┐   JSON schema     ┌──────────────────────┐
   │  Planner (Qwen 3)   │ ────────────────▶ │ {"intent":"organize", │
   └─────────────────────┘                   │  "file_types": [], ...}│
              │                              └──────────────────────┘
              ▼
   ┌─────────────────────┐   unchanged files come from the SQLite index
   │ Scanner + Readers   │   PDF · DOCX · PPTX · TXT · MD
   └─────────────────────┘
              │
              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │ search · ask · summarize · organize · rename · duplicates    │
   │ (semantic search: nomic-embed-text vectors + cosine scores)  │
   └─────────────────────────────────────────────────────────────┘
              │
              ▼
   ┌─────────────────────┐      ┌─────────────────────┐
   │ Review table (user  │ ───▶ │ Apply + log to      │ ───▶ ↩️ Undo
   │ edits / approves)   │      │ SQLite history      │
   └─────────────────────┘      └─────────────────────┘
```

### Project structure

```
├── main.py               # Streamlit entry point: navigation and sidebar status
├── app/                  # One file per page
│   ├── dashboard.py, assistant.py, chat.py, documents.py, history_page.py, about.py
│   └── common.py         # Shared UI helpers (folder picker, cached scan, ...)
├── core/                 # All logic, with no Streamlit code (easy to test)
│   ├── ai.py             # Ollama connection and model selection
│   ├── planner.py        # Instruction → JSON plan
│   ├── document_reader.py# Text extraction for every file type
│   ├── scanner.py        # Walks folders, uses the index
│   ├── index.py          # Persistent text index (SQLite)
│   ├── search.py         # Keyword search with snippets and pages
│   ├── semantic.py       # Embeddings, semantic and hybrid search
│   ├── chat.py           # Question answering with citations
│   ├── summarizer.py     # Summaries for documents of any length
│   ├── organizer.py      # Folder suggestions and safe moves
│   ├── renamer.py        # Name suggestions and safe renames
│   ├── duplicates.py     # SHA-256 duplicate finder
│   ├── history.py        # Change log and undo
│   └── db.py             # Database schema and connection
├── tests/                # pytest suite (runs without Ollama)
└── run.bat               # One-click launcher
```

---

## 🛡️ Safety design

- **Approve first:** the AI only *proposes*. Moves and renames happen only after you approve them.
- **Never deletes:** duplicates go to a `_duplicates` folder.
- **Never overwrites:** if a name is taken, the file becomes `report (1).pdf`.
- **Undo:** every change records its old and new path. Undo refuses to overwrite a file that has since appeared in the original location.
- **Constrained AI output:** folder choices are limited to an allowed list using JSON-schema `enum`s, so the model can't invent paths.
- **Private:** all AI runs locally, and no document content is sent over the internet.

---

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest                  # all tests; the AI tests skip automatically if Ollama isn't running
pytest -m "not ai"      # fast unit tests only
pytest -m ai            # check the real model understands instructions
```

Tests run automatically on every push with GitHub Actions, on Windows and Ubuntu.

---

## 🗺️ Roadmap

- [ ] OCR for scanned PDFs
- [ ] Folder watcher (automatically index new files)
- [ ] Settings page (choose the model, folders to skip)
- [ ] Export activity reports

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

[MIT](LICENSE) © 2026 Muhammad Abdullah Dogar. Built as an Open Source Software Development (OSSD) semester project.
