"""Hyrox Coach Dashboard — entry point."""

import sys
import os
from pathlib import Path

# Make dashboard/ importable as a package from the project root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st


st.set_page_config(
    page_title="Hyrox Coach",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.lib.styles import inject_bg
inject_bg("bg_hyrox.jpg")

from dashboard.lib import airtable_client as db
from datetime import date, timedelta

if st.sidebar.button("🔄 Refresh data"):
    db.get_athlete_profile.clear()
    db.get_training_sessions.clear()
    db.get_nutrition_plans.clear()
    st.rerun()

# ── Sidebar ────────────────────────────────────────────────────────────────────
athlete = db.get_athlete_profile()
if athlete:
    from math import ceil
    target_raw = athlete.get("hyrox_target_date", "2026-08-15")
    target_date = date.fromisoformat(target_raw[:10])
    weeks_to_race = ceil((target_date - date.today()).days / 7)
    phase = (
        "Taper" if weeks_to_race <= 2 else
        "Peak"  if weeks_to_race <= 5 else
        "Build" if weeks_to_race <= 12 else "Base"
    )
    st.sidebar.title(f"🏃 {athlete.get('name', 'Athlete')}")
    st.sidebar.metric("Phase", phase)
    st.sidebar.metric("Weeks to race", weeks_to_race)
    st.sidebar.metric("Target date", target_raw[:10])
    st.sidebar.divider()
    st.sidebar.caption("Navigate using the pages above.")
else:
    st.sidebar.warning("Athlete profile not found.")

# ── Home page (Today) ──────────────────────────────────────────────────────────
st.title("🏃 Hyrox Coach Dashboard")

today_str = date.today().isoformat()
week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
week_end   = (date.today() + timedelta(days=6 - date.today().weekday())).isoformat()

sessions = db.get_training_sessions(week_start, week_end)
today_session = next((s for s in sessions if s.get("date", "")[:10] == today_str), None)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📅 {date.today().strftime('%A, %d %B %Y')}")

    if today_session:
        intensity_color = {
            "easy": "🟢", "moderate": "🟡", "hard": "🔴", "max": "🔥"
        }.get(today_session.get("intensity", ""), "⚪")

        status_icon = {
            "planned": "📋", "done": "✅", "skipped": "⏭️", "modified": "✏️"
        }.get(today_session.get("status", "planned"), "📋")

        st.markdown(f"""
**{status_icon} {today_session.get('session_type', 'Session')}** &nbsp;
{intensity_color} {today_session.get('intensity', '').capitalize()} &nbsp;
⏱ {today_session.get('duration_min', '?')} min
""")
        st.markdown(today_session.get("description", ""))
        if today_session.get("notes"):
            st.caption(f"💡 {today_session['notes']}")
    else:
        st.info("No session planned for today.")

with col2:
    if today_session:
        intensity = today_session.get("intensity", "easy")
        kcal_range = {
            "easy": "2100–2400", "moderate": "2400–2700",
            "hard": "2700–3100", "max": "2700–3100"
        }.get(intensity, "2000–2300")
        st.metric("Caloric target", f"~{kcal_range} kcal")
        st.metric("Session", today_session.get("session_type", "—"))
        st.metric("Phase", today_session.get("phase", "—"))

# ── This week mini-overview ────────────────────────────────────────────────────
st.divider()
st.subheader("📆 This week at a glance")

if sessions:
    cols = st.columns(7)
    for i, col in enumerate(cols):
        d = date.today() - timedelta(days=date.today().weekday()) + timedelta(days=i)
        s = next((x for x in sessions if x.get("date", "")[:10] == d.isoformat()), None)
        with col:
            is_today = d == date.today()
            label = f"**{d.strftime('%a')}**" if is_today else d.strftime("%a")
            st.markdown(label)
            if s:
                status_icon = {"planned":"📋","done":"✅","skipped":"⏭️","modified":"✏️"}.get(s.get("status","planned"),"📋")
                st.caption(f"{status_icon} {s.get('session_type','?')[:12]}")
                st.caption(f"⏱ {s.get('duration_min','?')}min")
            else:
                st.caption("—")
else:
    st.info("No sessions this week. Run Workflow E to generate the plan.")
