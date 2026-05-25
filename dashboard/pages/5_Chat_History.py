"""Paginated view of conversation history from Airtable."""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st
from dashboard.lib.styles import inject_bg
inject_bg("bg_chat.jpg")
from dashboard.lib import airtable_client as db

st.set_page_config(page_title="Chat History · Hyrox Coach", page_icon="📜", layout="wide")
st.title("📜 Chat History")

if st.button("🔄 Refresh"):
    db.get_chat_history.clear()
    st.rerun()

messages = db.get_chat_history(limit=200)

if not messages:
    st.info("No conversation history yet. Start chatting via Telegram or the Chat page.")
    st.stop()

st.caption(f"{len(messages)} messages loaded.")

# ── Render messages ────────────────────────────────────────────────────────────
for msg in messages:
    role    = msg.get("role", "user")
    content = msg.get("content", "")
    ts      = str(msg.get("timestamp", ""))[:16].replace("T", " ")

    with st.chat_message(role):
        st.markdown(content)
        st.caption(ts)
