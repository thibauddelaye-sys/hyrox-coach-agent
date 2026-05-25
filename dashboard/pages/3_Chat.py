"""Conversational chat with full tool support."""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st
from datetime import date, timedelta

from dashboard.lib.styles import inject_bg
inject_bg("bg_chat.jpg")
from dashboard.lib import airtable_client as db
from dashboard.lib import chat_engine

st.set_page_config(page_title="Chat · Hyrox Coach", page_icon="💬", layout="wide")
st.title("💬 Hyrox Coach Chat")
st.caption("Ask anything about training, nutrition, recovery, or request changes to your plan.")

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar tools ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("🛠️ Tools available")
    st.markdown("""
- 🔍 **Knowledge base** — Hyrox training & nutrition research
- ✏️ **Update session** — Modify a single session in Airtable
- 🔄 **Replan week** — Regenerate the full week's plan
""")
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Changes made via chat are saved directly to Airtable.")

# ── Load context once ──────────────────────────────────────────────────────────
athlete  = db.get_athlete_profile()
today    = date.today()
mon      = today - timedelta(days=today.weekday())
sessions = db.get_training_sessions(
    (mon - timedelta(days=7)).isoformat(),
    (mon + timedelta(days=13)).isoformat(),
)
logs = db.get_daily_logs(
    (today - timedelta(days=14)).isoformat(),
    today.isoformat(),
)

# ── Display chat history ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask your coach..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = ""
            for chunk in chat_engine.chat(
                messages=st.session_state.messages[:-1] + [{"role":"user","content":prompt}],
                athlete=athlete,
                sessions=sessions,
                logs=logs,
            ):
                response_text += chunk

            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})

    # Refresh Airtable caches if tools may have written data
    if any(kw in response_text.lower() for kw in ["updated", "replanned", "saved", "modified"]):
        db.get_training_sessions.clear()
        db.get_nutrition_plans.clear()
