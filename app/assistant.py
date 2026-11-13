from pathlib import Path

import pandas as pd
import streamlit as st

from app.common import (clear_scan_cache, folder_picker, prepare_semantic,
                        render_search_result, require_ai, scan)
from core import chat, db, summarizer
from core.duplicates import find_duplicates
from core.file_manager import UPLOAD_DIR
from core.organizer import DEFAULT_SUBJECTS, apply_moves, propose_moves
from core.planner import make_plan
from core.renamer import apply_renames, propose_renames
from core.semantic import hybrid_search

MAX_RENAME_FILES = 25  # each suggestion is an AI call; keep it quick

st.title("🤖 AI Assistant")
st.write("Tell SYNAPSE AI what to do in plain English. Nothing is changed until you approve it.")

folder = folder_picker("assistant")


def save_subjects():
    db.set_setting("subjects", st.session_state["subjects_box"])


if "subjects_box" not in st.session_state:
    st.session_state["subjects_box"] = db.get_setting("subjects", ", ".join(DEFAULT_SUBJECTS))
subjects_text = st.text_input(
    "Your subjects (used when organizing)", key="subjects_box", on_change=save_subjects,
    help="Comma-separated. The AI will only sort files into these folders. Saved automatically.",
)

with st.expander("💡 Example instructions"):
    st.markdown("""
- *Find all PDF files related to cybersecurity*
- *Organize my documents by subject*
- *Summarize my database lecture notes*
- *What is the difference between TCP and UDP according to my notes?*
- *Are there any duplicate files here?*
- *Give my Word files proper names*
""")

command = st.text_area("Your instruction", placeholder="Example: Organize my documents by subject")


def files_of_type(files, plan):
    return [f for f in files if not plan["file_types"] or f.extension in plan["file_types"]]


def new_proposal(kind, rows):
    st.session_state["proposal"] = {
        "id": pd.Timestamp.now().value, "kind": kind, "folder": folder,
        "instruction": command, "rows": rows,
    }


if st.button("Submit Command", type="primary"):
    if not command.strip():
        st.warning("Please enter an instruction.")
        st.stop()
    require_ai()
    st.session_state.pop("proposal", None)

    # Step 1: AI understands the instruction
    with st.spinner("Understanding your instruction..."):
        try:
            plan = make_plan(command)
        except Exception as error:
            st.error(f"AI engine error: {error}")
            st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Task", plan["intent"].replace("_", " ").title())
    col2.metric("File types", ", ".join(plan["file_types"]) or "All")
    col3.metric("Keywords", ", ".join(plan["keywords"]) or "None")

    # Step 2: scan the folder
    with st.spinner("Scanning files..."):
        try:
            files = scan(folder)
        except NotADirectoryError as error:
            st.error(str(error))
            st.stop()
    intent = plan["intent"]

    # Step 3: carry out the task
    if intent == "search":
        smart = prepare_semantic(files)
        results = hybrid_search(files, plan["file_types"], plan["keywords"], use_semantic=smart)
        st.subheader(f"🔎 {len(results)} matching file(s) out of {len(files)} scanned")
        if not smart:
            st.caption("Keyword search only. Install `nomic-embed-text` for search by meaning.")
        if not results:
            st.info("No matching files found. Try different words or another folder.")
        for r in results:
            render_search_result(r)

    elif intent == "summarize":
        candidates = files_of_type([f for f in files if f.text.strip()], plan)
        if plan["keywords"]:
            smart = prepare_semantic(candidates)
            matches = hybrid_search(candidates, plan["file_types"], plan["keywords"], use_semantic=smart)
            candidates = [r.file for r in matches]
        if not candidates:
            st.info("No readable document matches that. Try naming the topic or file.")
            st.stop()
        if len(candidates) > 3:
            st.caption(f"{len(candidates)} documents match. Summarizing the best 3 — "
                       "use the Documents page to summarize any single file.")
        for f in candidates[:3]:
            with st.container(border=True):
                st.markdown(f"### 📄 {f.name}")
                bar = st.progress(0.0, text="Reading...")
                try:
                    summary = summarizer.summarize(f, progress=lambda p, t: bar.progress(p, text=t))
                    bar.empty()
                    st.markdown(summary)
                except Exception as error:
                    bar.empty()
                    st.error(str(error))

    elif intent == "ask":
        if not prepare_semantic(files):
            st.error("Answering questions needs the embedding model: `ollama pull nomic-embed-text`")
            st.stop()
        sources = chat.find_sources(files, command)
        st.subheader("💬 Answer")
        if not sources:
            st.info("I couldn't find anything about this in the documents in this folder.")
            st.stop()
        st.write_stream(chat.stream_answer(command, sources))
        with st.expander("📚 Sources"):
            for i, c in enumerate(sources, start=1):
                st.markdown(f"**[{i}] {chat.format_source(c)}** · relevance {c['score']:.0%}")
                st.caption(c["text"][:300] + "…")

    elif intent == "organize":
        if Path(folder).resolve() == UPLOAD_DIR.resolve():
            st.warning("The uploads folder is managed by the Documents page. "
                       "Choose another folder to organize.")
            st.stop()
        targets = files_of_type(files, plan)
        if not targets:
            st.info("No files to organize in this folder.")
            st.stop()
        subjects = [s.strip() for s in subjects_text.split(",") if s.strip()]
        bar = st.progress(0.0, text="AI is reading your files...")
        try:
            proposals = propose_moves(targets, folder, subjects,
                                      progress=lambda p, name: bar.progress(p, text=f"Reading: {name}"))
        except Exception as error:
            st.error(f"AI engine error: {error}")
            st.stop()
        bar.empty()
        new_proposal("move", proposals)

    elif intent == "find_duplicates":
        with st.spinner("Comparing file contents..."):
            groups = find_duplicates(files_of_type(files, plan))
        if not groups:
            st.success(f"No duplicates found among {len(files)} files. 🎉")
            st.stop()
        wasted_kb = sum(f.size_kb for g in groups for f in g[1:])
        st.subheader(f"🗂️ {len(groups)} group(s) of identical files · "
                     f"{wasted_kb / 1024:.2f} MB could be freed")
        for i, group in enumerate(groups, start=1):
            with st.container(border=True):
                st.markdown(f"**Group {i}** · {len(group)} identical copies · {group[0].size_kb} KB each")
                for j, f in enumerate(group):
                    label = "🟢 keep (original)" if j == 0 else "⚪ extra copy"
                    st.write(f"{label} — **{f.name}**  \n`{f.path.parent}`")
        # Propose moving the extra copies aside (never deleting)
        new_proposal("move", [
            {"move": True, "file": f.name, "category": "_duplicates",
             "reason": f"Identical to {g[0].name}", "source": str(f.path)}
            for g in groups for f in g[1:]
        ])

    elif intent == "rename":
        targets = [f for f in files_of_type(files, plan) if f.text.strip()]
        if not targets:
            st.info("No readable documents to rename in this folder.")
            st.stop()
        if len(targets) > MAX_RENAME_FILES:
            st.caption(f"Suggesting names for the first {MAX_RENAME_FILES} of {len(targets)} files.")
            targets = targets[:MAX_RENAME_FILES]
        bar = st.progress(0.0, text="AI is reading your files...")
        try:
            proposals = propose_renames(targets, progress=lambda p, name: bar.progress(p, text=f"Reading: {name}"))
        except Exception as error:
            st.error(f"AI engine error: {error}")
            st.stop()
        bar.empty()
        new_proposal("rename", proposals)


# ---------- Review and approve (stays on screen between clicks) ----------

if "last_result" in st.session_state:
    op_id, count, verb, errors = st.session_state.pop("last_result")
    st.success(f"✅ {verb} {count} file(s). You can undo this on the History page (operation #{op_id}).")
    for name, error in errors:
        st.error(f"{name}: {error}")

proposal = st.session_state.get("proposal")
if proposal:
    st.divider()
    st.subheader("📋 Proposed changes — review before approving")
    is_rename = proposal.get("kind") == "rename"
    check = "rename" if is_rename else "move"

    if not proposal["rows"]:
        st.success("Nothing needs to change. Everything already looks good.")
        if st.button("OK"):
            del st.session_state["proposal"]
            st.rerun()
    else:
        if is_rename:
            columns = ["rename", "file", "new_name"]
            config = {
                "rename": st.column_config.CheckboxColumn("Rename?"),
                "file": st.column_config.TextColumn("Current name", disabled=True),
                "new_name": st.column_config.TextColumn("New name (editable)"),
            }
        else:
            columns = ["move", "file", "category", "reason"]
            config = {
                "move": st.column_config.CheckboxColumn("Move?"),
                "file": st.column_config.TextColumn("File", disabled=True),
                "category": st.column_config.TextColumn("New folder (editable)"),
                "reason": st.column_config.TextColumn("Why", disabled=True),
            }
        edited = st.data_editor(
            pd.DataFrame(proposal["rows"]), column_order=columns, column_config=config,
            hide_index=True, width="stretch", key=f"editor_{proposal['id']}",
        )
        selected = edited[edited[check]].to_dict("records")
        where = "renamed in place" if is_rename else f"moved into subfolders of {proposal['folder']}"
        st.caption(f"{len(selected)} of {len(edited)} file(s) will be {where}. **Nothing has changed yet.**")

        col1, col2 = st.columns(2)
        if col1.button(f"✅ Approve {len(selected)} change(s)", type="primary",
                       disabled=not selected, width="stretch"):
            if is_rename:
                op_id, done, errors = apply_renames(selected, proposal["folder"], proposal["instruction"])
                verb = "Renamed"
            else:
                op_id, done, errors = apply_moves(selected, proposal["folder"], proposal["instruction"])
                verb = "Moved"
            clear_scan_cache()
            del st.session_state["proposal"]
            st.session_state["last_result"] = (op_id, len(done), verb, errors)
            st.rerun()

        if col2.button("❌ Cancel", width="stretch"):
            del st.session_state["proposal"]
            st.rerun()
