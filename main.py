"""SYNAPSE AI — start the app with:  streamlit run main.py"""
import streamlit as st

from app.common import ai_status
from core import ai

st.set_page_config(page_title="SYNAPSE AI", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.main-title { font-size: 38px; font-weight: 800; }
.subtitle { color: #A0AAB8; font-size: 16px; }
div[data-testid="stMetric"] {
    background: rgba(128, 140, 160, 0.08);
    padding: 18px;
    border-radius: 12px;
    border: 1px solid rgba(128, 140, 160, 0.25);
}
</style>
""", unsafe_allow_html=True)

pages = [
    st.Page("app/dashboard.py", title="Dashboard", icon="🏠", default=True),
    st.Page("app/assistant.py", title="AI Assistant", icon="🤖"),
    st.Page("app/chat.py", title="Chat with Documents", icon="💬"),
    st.Page("app/documents.py", title="Documents", icon="📁"),
    st.Page("app/history_page.py", title="History", icon="🕘"),
    st.Page("app/about.py", title="About", icon="ℹ️"),
]
navigation = st.navigation(pages)

# ---------- Sidebar status ----------
st.sidebar.title("🧠 SYNAPSE AI")
st.sidebar.caption("Intelligent Desktop Assistant")
st.sidebar.divider()
st.sidebar.caption("SYSTEM STATUS")

status = ai_status()
if not status["online"]:
    st.sidebar.error("AI Engine: Offline — start Ollama")
else:
    if status["chat_model"]:
        st.sidebar.success(f"AI Engine: {status['model']}")
    else:
        st.sidebar.warning(f"Missing model: ollama pull {ai.MODEL}")
    if status["embed_model"]:
        st.sidebar.success("Smart search: Ready")
    else:
        st.sidebar.warning("Smart search off: ollama pull nomic-embed-text")

st.sidebar.caption("🔒 Everything runs locally. Your files never leave this computer.")

navigation.run()
