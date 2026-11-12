import streamlit as st

from app.common import clear_scan_cache, require_ai, scan
from core import summarizer
from core.file_manager import (ALLOWED_EXTENSIONS, UPLOAD_DIR, get_saved_documents,
                               save_uploaded_files)

ICONS = {"pdf": "📕", "docx": "📘", "pptx": "📙", "txt": "📄", "md": "📝"}

st.title("📁 Document Manager")
st.write("Upload documents into SYNAPSE AI's own workspace, read them and get AI summaries.")

st.divider()
st.subheader("Upload Documents")

uploads = st.file_uploader(
    "Choose PDF, Word, PowerPoint, text or Markdown files",
    type=[e.lstrip(".") for e in sorted(ALLOWED_EXTENSIONS)],
    accept_multiple_files=True,
    help="Maximum file size: 20 MB per document.",
)

if st.button("Save Documents", type="primary"):
    if uploads:
        try:
            saved = save_uploaded_files(uploads)
            if saved:
                st.success(f"{len(saved)} document(s) saved successfully!")
                for item in saved:
                    st.write("📄", item["name"])
                clear_scan_cache()
            else:
                st.warning("No files were saved. Check file types and sizes.")
        except Exception as error:
            st.error(f"Unable to save documents: {error}")
    else:
        st.warning("Please select documents first.")

st.divider()
st.subheader("Saved Documents")

documents = get_saved_documents()
if not documents:
    st.info("No documents saved yet.")
    st.stop()

st.write(f"Total documents: {len(documents)}")
for document in documents:
    col1, col2 = st.columns([3, 1])
    col1.write(f"{ICONS.get(document.suffix.lower().lstrip('.'), '📄')} {document.name}")
    col2.caption(f"{document.stat().st_size / 1024:.1f} KB")

st.divider()
st.subheader("📖 Read & Summarize")

files = {f.name: f for f in scan(UPLOAD_DIR)}
names = [d.name for d in documents if d.name in files]
choice = st.selectbox("Select a document", names)
selected = files[choice]

col1, col2 = st.columns(2)
show_text = col1.button("Show Document Text", width="stretch")
make_summary = col2.button("✨ Summarize with AI", type="primary", width="stretch")

if show_text:
    if selected.text.strip():
        st.text_area("Extracted Document Content", value=selected.text, height=350)
    else:
        st.warning("No readable text found in this document. It may contain scanned images.")

if make_summary:
    require_ai()
    bar = st.progress(0.0, text="Reading...")
    try:
        summary = summarizer.summarize(selected, progress=lambda p, t: bar.progress(p, text=t))
        bar.empty()
        with st.container(border=True):
            st.markdown(f"### Summary: {selected.name}")
            st.markdown(summary)
    except Exception as error:
        bar.empty()
        st.error(str(error))
