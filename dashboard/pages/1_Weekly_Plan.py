"""Weekly training plan view."""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from dashboard.lib.styles import inject_bg
inject_bg("bg_weekly.jpg")
from dashboard.lib import airtable_client as db

st.set_page_config(page_title="Weekly Plan · Hyrox Coach", page_icon="📆", layout="wide")
st.title("📆 Weekly Training Plan")

# ── Week selector ──────────────────────────────────────────────────────────────
today = date.today()
this_monday = today - timedelta(days=today.weekday())

week_offset = st.select_slider(
    "Week",
    options=[-1, 0, 1],
    value=0,
    format_func=lambda x: {-1: "Last week", 0: "This week", 1: "Next week"}[x],
)
week_start = this_monday + timedelta(weeks=week_offset)
week_end   = week_start + timedelta(days=6)

st.caption(f"📅 {week_start.strftime('%d %b')} — {week_end.strftime('%d %b %Y')}")

# ── Load data ──────────────────────────────────────────────────────────────────
sessions = db.get_training_sessions(week_start.isoformat(), week_end.isoformat())

if st.button("🔄 Refresh"):
    db.get_training_sessions.clear()
    st.rerun()

# ── Summary stats ──────────────────────────────────────────────────────────────
if sessions:
    total_min = sum(s.get("duration_min", 0) or 0 for s in sessions)
    hard_count = sum(1 for s in sessions if s.get("intensity") in ("hard", "max"))
    done_count = sum(1 for s in sessions if s.get("status") == "done")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total sessions", len(sessions))
    c2.metric("Total volume", f"{total_min} min")
    c3.metric("Hard/max sessions", hard_count)
    c4.metric("Completed", f"{done_count}/{len(sessions)}")
    st.divider()

# ── Day-by-day cards ──────────────────────────────────────────────────────────
INTENSITY_COLOR = {
    "easy": "#2ecc71", "moderate": "#f39c12", "hard": "#e74c3c", "max": "#8e44ad"
}
STATUS_ICON = {"planned": "📋", "done": "✅", "skipped": "⏭️", "modified": "✏️"}

if sessions:
    for i in range(7):
        day = week_start + timedelta(days=i)
        session = next((s for s in sessions if s.get("date", "")[:10] == day.isoformat()), None)
        is_today = day == today

        with st.expander(
            f"{'**' if is_today else ''}{day.strftime('%A %d %B')}{'**' if is_today else ''}"
            + (f" — {session.get('session_type','?')}" if session else " — Rest / No session"),
            expanded=(is_today or week_offset == 0 and i == today.weekday()),
        ):
            if session:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    intensity = session.get("intensity", "")
                    color = INTENSITY_COLOR.get(intensity, "#95a5a6")
                    st.markdown(
                        f'<span style="background:{color};color:white;padding:2px 8px;'
                        f'border-radius:4px;font-size:0.8em">{intensity.upper()}</span>'
                        f'&nbsp; ⏱ {session.get("duration_min","?")} min',
                        unsafe_allow_html=True,
                    )
                    st.markdown(session.get("description", "_No description_"))
                    if session.get("notes"):
                        st.caption(f"💡 {session['notes']}")
                with col_b:
                    status = session.get("status", "planned")
                    st.markdown(f"**Status:** {STATUS_ICON.get(status,'')} {status}")
                    st.caption(f"Phase: {session.get('phase','—')}")
                    st.caption(f"Week #{session.get('week_number','—')}")
            else:
                st.caption("No session planned for this day.")
else:
    st.warning("No sessions found for this week. Generate a plan with Workflow E first.")

# ── Table view ─────────────────────────────────────────────────────────────────
if sessions:
    with st.expander("📊 Table view"):
        df = pd.DataFrame(sessions)
        cols_to_show = [c for c in ["date","session_type","duration_min","intensity","status","phase","week_number"] if c in df.columns]
        st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)
