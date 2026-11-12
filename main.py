

from core.document_reader import extract_document_text
import streamlit as st

from core.file_manager import (
    save_uploaded_files,
    get_saved_documents
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

# Sidebar
st.sidebar.title("🧠 SYNAPSE AI")
st.sidebar.caption("Intelligent Desktop Assistant")
st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    ["Dashboard", "AI Assistant", "Documents", "About"]
)

st.sidebar.divider()
st.sidebar.caption("SYSTEM STATUS")
st.sidebar.info("AI Engine: Not Connected")
st.sidebar.success("Application: Running")

# Dashboard
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
        st.metric("AI Engine", "Offline")

    with col2:
        st.metric("Documents", "0")

    with col3:
        st.metric("System", "Ready")

    st.divider()

    st.subheader("🚀 Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🤖 AI Assistant")
            st.write("Give instructions using natural language.")
            if st.button("Open AI Assistant", use_container_width=True):
                st.session_state["page"] = "AI Assistant"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("📁 Document Manager")
            st.write("Upload and manage your university documents.")
            if st.button("Open Documents", use_container_width=True):
                st.session_state["page"] = "Documents"
                st.rerun()

    st.divider()

    st.subheader("What can SYNAPSE AI do?")
    st.write("• Organize documents by subject")
    st.write("• Search for files")
    st.write("• Read PDF and Word documents")
    st.write("• Summarize documents using AI")
    st.write("• Identify duplicate files")

# AI Assistant
elif page == "AI Assistant":

    st.title("🤖 AI Assistant")
    st.write("Give SYNAPSE AI an instruction.")

    command = st.text_area(
        "Your instruction",
        placeholder="Example: Organize my university documents by subject..."
    )

    if st.button("Submit Command", type="primary"):
        if command.strip():
            st.session_state["last_command"] = command
            st.success("Command received successfully!")
            st.write("Your instruction:", command)
            st.info("AI processing will be connected in a later development stage.")
        else:
            st.warning("Please enter an instruction.")


# Documents
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
                    st.success(
                        f"{len(saved)} document(s) saved successfully!"
                    )

                    for item in saved:
                        st.write("📄", item["name"])
                else:
                    st.warning(
                        "No files were saved. Check file types and sizes."
                    )

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

    documents = get_saved_documents()

    if documents:

        selected_document = st.selectbox(
            "Select a document",
            documents,
            format_func=lambda file: file.name
        )

        if st.button("Extract Document Text"):

            try:
                extracted_text = extract_document_text(
                    selected_document
                )

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


# About
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

