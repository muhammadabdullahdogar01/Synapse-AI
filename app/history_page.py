from pathlib import Path

import streamlit as st

from app.common import clear_scan_cache
from core.history import get_actions, get_operations, undo_operation

st.title("🕘 Activity History")
st.write("Every change SYNAPSE AI makes is recorded here and can be undone.")

if "undo_result" in st.session_state:
    restored, errors = st.session_state.pop("undo_result")
    st.success(f"Restored {restored} file(s) to how they were.")
    for error in errors:
        st.warning(error)

operations = get_operations()
if not operations:
    st.info("No changes made yet.")

for op in operations:
    with st.container(border=True):
        col1, col2 = st.columns([5, 1])
        col1.markdown(f"**#{op['id']} · {op['instruction']}**")
        col1.caption(f"{op['created_at']} · {op['action_count']} file(s) · status: **{op['status']}**")

        if op["status"] == "completed" and op["action_count"]:
            if col2.button("↩️ Undo", key=f"undo_{op['id']}", width="stretch"):
                st.session_state["undo_result"] = undo_operation(op["id"])
                clear_scan_cache()
                st.rerun()

        with st.expander("Show details"):
            for a in get_actions(op["id"]):
                source, destination = Path(a["source"]), Path(a["destination"])
                if a["action_type"] == "rename":
                    st.write(f"✏️ **{source.name}** → **{destination.name}**  \n`{source.parent}`")
                else:
                    st.write(f"📄 **{source.name}**  \n`{source.parent}` → `{destination.parent}`")
