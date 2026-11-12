"""Helpers shared by all pages."""
import subprocess
import sys

import streamlit as st

from core import ai
from core.file_manager import UPLOAD_DIR
from core.scanner import folder_signature, scan_folder
from core.semantic import ensure_embeddings


@st.cache_data(ttl=30, show_spinner=False)
def ai_status():
    """Check Ollama at most once every 30 seconds."""
    return ai.status()


@st.cache_data(show_spinner=False)
def cached_scan(folder, signature):
    """Re-scan only when the folder's contents have changed."""
    return scan_folder(folder)


def scan(folder):
    return cached_scan(folder, folder_signature(folder))


def clear_scan_cache():
    cached_scan.clear()


# ---------- Folder chooser (shared between pages) ----------

PICK_SCRIPT = (
    "import tkinter as tk\n"
    "from tkinter import filedialog\n"
    "root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)\n"
    "print(filedialog.askdirectory(title='Choose a folder for SYNAPSE AI') or '')\n"
)


def _browse(box_key):
    """Open the Windows folder dialog in a separate process (tkinter and
    Streamlit don't share a thread safely)."""
    try:
        result = subprocess.run([sys.executable, "-c", PICK_SCRIPT],
                                capture_output=True, text=True, timeout=300)
        chosen = result.stdout.strip()
    except Exception:
        chosen = ""
    if chosen:
        st.session_state["work_folder"] = chosen
        st.session_state[box_key] = chosen


def _sync(box_key):
    st.session_state["work_folder"] = st.session_state[box_key]


def folder_picker(page_key):
    """Text box + Browse button. The chosen folder is remembered across pages."""
    box_key = f"{page_key}_folder_box"
    if box_key not in st.session_state:
        st.session_state[box_key] = st.session_state.get("work_folder", str(UPLOAD_DIR))

    col1, col2 = st.columns([5, 1], vertical_alignment="bottom")
    col1.text_input(
        "Folder to work in", key=box_key, on_change=_sync, args=(box_key,),
        help="Paste a folder path, or click Browse.",
    )
    col2.button("📂 Browse", key=f"{page_key}_browse", on_click=_browse,
                args=(box_key,), width="stretch")
    return st.session_state[box_key]


def prepare_semantic(files):
    """Make sure every readable file has vectors, with a progress bar."""
    if not ai_status()["embed_model"]:
        return False
    bar = st.empty()

    def progress(fraction, name):
        bar.progress(fraction, text=f"Indexing for smart search (first time only): {name}")

    try:
        ensure_embeddings(files, progress=progress)
    except Exception as error:
        st.warning(f"Smart search unavailable: {error}")
        return False
    finally:
        bar.empty()
    return True


def require_ai():
    """Stop the page with a helpful message if the AI engine isn't ready."""
    status = ai_status()
    if not status["online"]:
        st.error("AI engine is offline. Open the Ollama app, then refresh this page.")
        st.stop()
    if not status["chat_model"]:
        st.error(f"No AI model installed. Run:  `ollama pull {ai.MODEL}`")
        st.stop()


def render_search_result(r):
    with st.container(border=True):
        st.markdown(f"**📄 {r.file.name}**")
        details = [f"{r.file.size_kb} KB", f"modified {r.file.modified:%d %b %Y}"]
        if r.relevance is not None:
            details.append(f"relevance {r.relevance:.0%}")
        if r.matched:
            details.append(f"keywords: {', '.join(r.matched)}")
        st.caption(" · ".join(details))
        if r.snippet:
            page_note = f" *(page {r.page})*" if r.page else ""
            st.write(f"“…{r.snippet}…”{page_note}")
        st.caption(f"`{r.file.path.parent}`")
