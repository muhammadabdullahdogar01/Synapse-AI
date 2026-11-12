from pathlib import Path

import pandas as pd
import streamlit as st

from core.planner import make_plan, is_ai_available
from core.document_reader import extract_document_text
from core.scanner import scan_folder
from core.search import search_files
from core.organizer import propose_moves, apply_moves, DEFAULT_SUBJECTS
from core.duplicates import find_duplicates
from core.history import get_operations, get_actions, undo_operation
from core.file_manager import (
    save_uploaded_files,
    get_saved_documents,
    UPLOAD_DIR
)

st.set_page_config(
    page_title="SYNAPSE AI",
    page_icon="🧠",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
.stApp {
    background-color: #0E1117;
}
.block-container {
    padding-top: 2rem;
}
.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #FFFFFF;
}
.subtitle {
    color: #A0AAB8;
    font-size: 16px;
}
div[data-testid="stMetric"] {
    background: #191F2B;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #293244;
}
</style>
""", unsafe_allow_html=True)


# ---------- Helpers ----------

PAGES = ["Dashboard", "AI Assistant", "Documents", "History", "About"]


def go_to(page_name):
    """Switch page (used by Dashboard buttons)."""
    st.session_state["page"] = page_name


@st.cache_data(ttl=30)
def check_ai():
    """Check Ollama at most once every 30 seconds."""
    return is_ai_available()


@st.cache_data(ttl=60, show_spinner=False)
def cached_scan(folder):
    """Scan a folder, reusing the result for 60 seconds."""
    return scan_folder(folder)


ai_online = check_ai()


# ---------- Sidebar ----------

st.sidebar.title("🧠 SYNAPSE AI")
st.sidebar.caption("Intelligent Desktop Assistant")
st.sidebar.divider()

page = st.sidebar.radio("NAVIGATION", PAGES, key="page")

st.sidebar.divider()
st.sidebar.caption("SYSTEM STATUS")
if ai_online:
    st.sidebar.success("AI Engine: Connected (qwen3:4b)")
else:
    st.sidebar.error("AI Engine: Offline — start Ollama")
st.sidebar.success("Application: Running")


# ---------- Dashboard ----------

if page == "Dashboard":

    st.markdown('<div class="main-title">Welcome to SYNAPSE AI</div>',
                unsafe_allow_html=True)

    st.markdown(
        '<div class="subtitle">Your intelligent workspace for documents and automation.</div>',
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("AI Engine", "Online" if ai_online else "Offline")

    with col2:
        st.metric("Documents", len(get_saved_documents()))

    with col3:
        st.metric("Operations", len(get_operations()))

    st.divider()

    st.subheader("🚀 Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🤖 AI Assistant")
            st.write("Give instructions using natural language.")
            st.button("Open AI Assistant", use_container_width=True,
                      on_click=go_to, args=("AI Assistant",))

    with col2:
        with st.container(border=True):
            st.subheader("📁 Document Manager")
            st.write("Upload and manage your university documents.")
            st.button("Open Documents", use_container_width=True,
                      on_click=go_to, args=("Documents",))

    st.divider()

    st.subheader("What can SYNAPSE AI do?")
    st.write("• Organize documents by subject")
    st.write("• Search for files")
    st.write("• Read PDF and Word documents")
    st.write("• Summarize documents using AI")
    st.write("• Identify duplicate files")


# ---------- AI Assistant ----------

elif page == "AI Assistant":

    st.title("🤖 AI Assistant")
    st.write("Give SYNAPSE AI an instruction.")

    folder = st.text_input(
        "Folder to work in",
        value=str(UPLOAD_DIR),
        help="Paste any folder path, e.g. C:\\Users\\You\\Documents\\University"
    )

    subjects_text = st.text_input(
        "Your subjects (used when organizing)",
        value=", ".join(DEFAULT_SUBJECTS),
        help="Comma-separated. The AI will only sort files into these folders."
    )

    command = st.text_area(
        "Your instruction",
        placeholder="Example: Organize my documents by subject"
    )

    if st.button("Submit Command", type="primary"):
        if not command.strip():
            st.warning("Please enter an instruction.")
            st.stop()
        if not ai_online:
            st.error("AI engine is offline. Open the Ollama app and refresh this page.")
            st.stop()

        # Step 1: AI understands the instruction
        with st.spinner("Understanding your instruction..."):
            try:
                plan = make_plan(command)
            except Exception as error:
                st.error(f"AI engine error: {error}")
                st.stop()

        st.success("Instruction understood!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Task", plan["intent"].replace("_", " ").title())
        col2.metric("File types", ", ".join(plan["file_types"]) or "All")
        col3.metric("Keywords", ", ".join(plan["keywords"]) or "None")

        # Step 2: scan the folder
        with st.spinner("Scanning files..."):
            try:
                files = cached_scan(folder)
            except NotADirectoryError as error:
                st.error(str(error))
                st.stop()

        # Step 3: carry out the task
        if plan["intent"] == "search":
            results = search_files(files, plan["file_types"], plan["keywords"])

            st.subheader(f"🔎 {len(results)} matching file(s) out of {len(files)} scanned")

            if not results:
                st.info("No matching files found. Try different words or another folder.")

            for r in results:
                with st.container(border=True):
                    st.markdown(f"**📄 {r.file.name}**")
                    st.caption(
                        f"{r.file.size_kb} KB · modified {r.file.modified:%d %b %Y} · "
                        f"matched: {', '.join(r.matched) or 'file type'}"
                    )
                    if r.snippet:
                        page_note = f" *(page {r.page})*" if r.page else ""
                        st.write(f"“…{r.snippet}…”{page_note}")

        elif plan["intent"] == "organize":
            if Path(folder).resolve() == UPLOAD_DIR.resolve():
                st.warning("The uploads folder is managed by the Documents page. "
                           "Choose another folder to organize.")
                st.stop()

            targets = [f for f in files
                       if not plan["file_types"] or f.extension in plan["file_types"]]
            if not targets:
                st.info("No files to organize in this folder.")
                st.stop()

            subjects = [s.strip() for s in subjects_text.split(",") if s.strip()]

            bar = st.progress(0.0, text="AI is reading your files...")
            try:
                proposals = propose_moves(
                    targets, folder, subjects,
                    progress=lambda frac, name: bar.progress(frac, text=f"Reading: {name}")
                )
            except Exception as error:
                st.error(f"AI engine error: {error}")
                st.stop()
            bar.empty()

            st.session_state["proposal"] = {
                "id": pd.Timestamp.now().value,
                "folder": folder,
                "instruction": command,
                "rows": proposals,
            }

        elif plan["intent"] == "find_duplicates":
            with st.spinner("Comparing file contents..."):
                groups = find_duplicates(files)

            if not groups:
                st.success(f"No duplicates found among {len(files)} files. 🎉")
                st.stop()

            wasted_kb = sum(f.size_kb for g in groups for f in g[1:])
            st.subheader(f"🗂️ {len(groups)} group(s) of identical files · "
                         f"{wasted_kb / 1024:.2f} MB could be freed")

            for i, group in enumerate(groups, start=1):
                with st.container(border=True):
                    st.markdown(f"**Group {i}** · {len(group)} identical copies · "
                                f"{group[0].size_kb} KB each")
                    for j, f in enumerate(group):
                        label = "🟢 keep (oldest)" if j == 0 else "⚪ extra copy"
                        st.write(f"{label} — **{f.name}**  \n`{f.path.parent}`")

            # Propose moving the extra copies aside (never deleting)
            st.session_state["proposal"] = {
                "id": pd.Timestamp.now().value,
                "folder": folder,
                "instruction": command,
                "rows": [
                    {"move": True, "file": f.name, "category": "_duplicates", "source": str(f.path)}
                    for g in groups for f in g[1:]
                ],
            }

        else:
            st.info(
                f"Scanned {len(files)} files. The "
                f"'{plan['intent'].replace('_', ' ')}' feature is coming in the next stage."
            )

    # ----- Review and approve (stays on screen between clicks) -----

    if "last_result" in st.session_state:
        op_id, moved, errors = st.session_state.pop("last_result")
        st.success(f"✅ Moved {moved} file(s). You can undo this on the History page (operation #{op_id}).")
        for name, error in errors:
            st.error(f"{name}: {error}")

    proposal = st.session_state.get("proposal")
    if proposal:
        st.divider()
        st.subheader("📋 Proposed changes — review before approving")

        if not proposal["rows"]:
            st.success("Everything is already organized. Nothing to move.")
            if st.button("OK"):
                del st.session_state["proposal"]
                st.rerun()
        else:
            edited = st.data_editor(
                pd.DataFrame(proposal["rows"]),
                column_order=["move", "file", "category"],
                column_config={
                    "move": st.column_config.CheckboxColumn("Move?"),
                    "file": st.column_config.TextColumn("File", disabled=True),
                    "category": st.column_config.TextColumn("New folder (editable)"),
                },
                hide_index=True,
                use_container_width=True,
                key=f"editor_{proposal['id']}",
            )

            selected = edited[edited["move"]].to_dict("records")
            st.caption(
                f"{len(selected)} of {len(edited)} file(s) will be moved into subfolders of "
                f"{proposal['folder']}. **Nothing has changed yet.**"
            )

            col1, col2 = st.columns(2)
            if col1.button(f"✅ Approve {len(selected)} move(s)", type="primary",
                           disabled=not selected, use_container_width=True):
                op_id, done, errors = apply_moves(selected, proposal["folder"], proposal["instruction"])
                cached_scan.clear()
                del st.session_state["proposal"]
                st.session_state["last_result"] = (op_id, len(done), errors)
                st.rerun()

            if col2.button("❌ Cancel", use_container_width=True):
                del st.session_state["proposal"]
                st.rerun()


# ---------- Documents ----------

elif page == "Documents":

    st.title("📁 Document Manager")
    st.write("Upload and manage your university documents.")

    st.divider()

    st.subheader("Upload Documents")

    files = st.file_uploader(
        "Choose PDF or Word documents",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Maximum file size: 20 MB per document."
    )

    if st.button("Save Documents", type="primary"):
        if files:
            try:
                saved = save_uploaded_files(files)

                if saved:
                    st.success(f"{len(saved)} document(s) saved successfully!")
                    for item in saved:
                        st.write("📄", item["name"])
                    cached_scan.clear()  # new files: forget the old scan
                else:
                    st.warning("No files were saved. Check file types and sizes.")

            except Exception as error:
                st.error(f"Unable to save documents: {error}")
        else:
            st.warning("Please select documents first.")

    st.divider()

    st.subheader("Saved Documents")

    documents = get_saved_documents()

    if documents:
        st.write(f"Total documents: {len(documents)}")

        for document in documents:
            size_kb = document.stat().st_size / 1024
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 {document.name}")
            with col2:
                st.caption(f"{size_kb:.1f} KB")
    else:
        st.info("No documents saved yet.")

    st.divider()

    st.subheader("📖 Read Documents")

    if documents:
        selected_document = st.selectbox(
            "Select a document",
            documents,
            format_func=lambda file: file.name
        )

        if st.button("Extract Document Text"):
            try:
                extracted_text = extract_document_text(selected_document)

                if extracted_text.strip():
                    st.success("Document read successfully!")
                    st.text_area(
                        "Extracted Document Content",
                        value=extracted_text,
                        height=350
                    )
                else:
                    st.warning(
                        "No readable text found in this document. "
                        "It may contain scanned images."
                    )

            except Exception as error:
                st.error(f"Error reading document: {error}")
    else:
        st.info("Upload a document first.")


# ---------- History ----------

elif page == "History":

    st.title("🕘 Activity History")
    st.write("Every change SYNAPSE AI makes is recorded here and can be undone.")

    operations = get_operations()

    if not operations:
        st.info("No changes made yet.")

    for op in operations:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"**#{op['id']} · {op['instruction']}**")
            col1.caption(
                f"{op['created_at']} · {op['action_count']} file(s) · "
                f"status: **{op['status']}**"
            )

            if op["status"] == "completed" and op["action_count"]:
                if col2.button("↩️ Undo", key=f"undo_{op['id']}", use_container_width=True):
                    restored, errors = undo_operation(op["id"])
                    cached_scan.clear()
                    st.success(f"Restored {restored} file(s) to their original folders.")
                    for error in errors:
                        st.warning(error)

            with st.expander("Show details"):
                for a in get_actions(op["id"]):
                    st.write(
                        f"📄 **{Path(a['source']).name}**  \n"
                        f"`{Path(a['source']).parent}` → `{Path(a['destination']).parent}`"
                    )


# ---------- About ----------

elif page == "About":

    st.title("About SYNAPSE AI")

    st.write("""
    SYNAPSE AI is an open-source intelligent desktop assistant
    designed to simplify document management through
    natural-language instructions.

    **Technologies**
    - Python
    - Streamlit
    - Ollama
    - SQLite
    - PyMuPDF
    - python-docx

    **Project:** OSSD Semester Project
    """)