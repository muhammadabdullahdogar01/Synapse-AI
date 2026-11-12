import streamlit as st

from app.common import folder_picker, prepare_semantic, require_ai, scan
from core import chat

st.title("💬 Chat with Documents")
st.write("Ask questions about your files. Every answer shows which file and page it came from.")

folder = folder_picker("chat")

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []  # dicts: role, content, sources
messages = st.session_state["chat_messages"]

if messages and st.button("🧹 Clear chat"):
    messages.clear()
    st.rerun()

for m in messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("📚 Sources"):
                for line in m["sources"]:
                    st.caption(line)

question = st.chat_input("e.g. What are the main points of my networking notes?")
if question:
    require_ai()
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            files = scan(folder)
        except NotADirectoryError as error:
            st.error(str(error))
            st.stop()
        if not prepare_semantic(files):
            st.error("Chat needs the embedding model. Run:  `ollama pull nomic-embed-text`")
            st.stop()

        with st.spinner("Searching your documents..."):
            sources = chat.find_sources(files, question)

        if not sources:
            answer = "I couldn't find anything about this in the documents in this folder."
            st.markdown(answer)
            source_lines = []
        else:
            previous = [(messages[i]["content"], messages[i + 1]["content"])
                        for i in range(0, len(messages) - 1, 2)]
            answer = st.write_stream(chat.stream_answer(question, sources, previous))
            source_lines = [f"[{i}] {chat.format_source(c)} · relevance {c['score']:.0%}"
                            for i, c in enumerate(sources, start=1)]
            with st.expander("📚 Sources"):
                for line in source_lines:
                    st.caption(line)

    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": answer, "sources": source_lines})
