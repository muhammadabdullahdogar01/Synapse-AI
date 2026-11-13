import streamlit as st

from app.common import ai_status
from core import index
from core.history import get_operations

st.markdown('<div class="main-title">Welcome to SYNAPSE AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your private, AI-powered workspace for documents. '
            'Everything runs on this computer.</div>', unsafe_allow_html=True)
st.divider()

status = ai_status()
stats = index.get_stats()
operations = get_operations()

col1, col2, col3, col4 = st.columns(4)
col1.metric("AI Engine", "Online" if status["online"] and status["chat_model"] else "Offline")
col2.metric("Documents indexed", stats["documents"], help="Files whose text SYNAPSE AI has read")
col3.metric("Smart-search ready", f"{stats['semantic_ready']} / {stats['documents']}",
            help="Documents that can be found by meaning and used in chat")
col4.metric("Changes made", sum(1 for op in operations if op["status"] == "completed"),
            help="Operations you can still undo")

if stats["by_type"]:
    st.caption("Indexed by type: " + " · ".join(
        f"**{t.upper()}** {n}" for t, n in stats["by_type"].most_common()
    ) + f" · {stats['total_mb']:.1f} MB in total")

st.divider()
st.subheader("🚀 Quick Actions")

col1, col2, col3 = st.columns(3)
with col1.container(border=True):
    st.markdown("**🤖 AI Assistant**")
    st.caption("Organize, search, rename or find duplicates with one instruction.")
    st.page_link("app/assistant.py", label="Open AI Assistant", icon="➡️")
with col2.container(border=True):
    st.markdown("**💬 Chat with Documents**")
    st.caption("Ask questions and get answers with file and page references.")
    st.page_link("app/chat.py", label="Start chatting", icon="➡️")
with col3.container(border=True):
    st.markdown("**📁 Documents**")
    st.caption("Upload files, read them and get AI summaries.")
    st.page_link("app/documents.py", label="Open Documents", icon="➡️")

st.divider()
st.subheader("🕘 Recent Activity")
if not operations:
    st.info("No changes yet. Try: *“Organize my documents by subject”* in the AI Assistant.")
for op in operations[:5]:
    st.write(f"**#{op['id']}** {op['instruction']}  \n"
             f"<small>{op['created_at']} · {op['action_count']} file(s) · {op['status']}</small>",
             unsafe_allow_html=True)
if operations:
    st.page_link("app/history_page.py", label="See full history", icon="🕘")
