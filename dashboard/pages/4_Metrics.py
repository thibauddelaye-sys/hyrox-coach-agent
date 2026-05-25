"""Training volume and body metrics charts."""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st
import altair as alt
import pandas as pd
from datetime import date, timedelta

from dashboard.lib.styles import inject_bg
inject_bg("bg_metrics.jpg")
from dashboard.lib import airtable_client as db

st.set_page_config(page_title="Metrics · Hyrox Coach", page_icon="📊", layout="wide")
st.title("📊 Training Metrics")

if st.button("🔄 Refresh"):
    db.get_daily_logs.clear()
    db.get_body_metrics.clear()
    st.rerun()

today = date.today()

# ── Training volume (daily_logs) ───────────────────────────────────────────────
st.subheader("🏃 Training volume — last 4 weeks")

logs = db.get_daily_logs(
    (today - timedelta(days=28)).isoformat(),
    today.isoformat(),
)

if logs:
    df_logs = pd.DataFrame(logs)
    df_logs["date"] = pd.to_datetime(df_logs["date"]).dt.date
    df_logs["duration_min"] = pd.to_numeric(df_logs.get("duration_min", 0), errors="coerce").fillna(0)
    df_logs["distance_km"]  = pd.to_numeric(df_logs.get("distance_km",  0), errors="coerce").fillna(0)

    total_hours = df_logs["duration_min"].sum() / 60
    num_activities = len(df_logs)
    total_km = df_logs["distance_km"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total training time", f"{total_hours:.1f} h")
    m2.metric("Activities", num_activities)
    m3.metric("Total distance", f"{total_km:.1f} km")

    col1, col2 = st.columns(2)
    with col1:
        chart = (
            alt.Chart(df_logs)
            .mark_bar(color="#3498db", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("date:T", title="Date", axis=alt.Axis(format="%d %b")),
                y=alt.Y("duration_min:Q", title="Duration (min)"),
                color=alt.Color(
                    "activity_type:N",
                    legend=alt.Legend(title="Activity type"),
                ) if "activity_type" in df_logs.columns else alt.value("#3498db"),
                tooltip=["date:T", "activity_type:N", "duration_min:Q", "distance_km:Q"],
            )
            .properties(title="Duration per activity", height=280)
        )
        st.altair_chart(chart, use_container_width=True)

    with col2:
        df_week = df_logs.copy()
        df_week["week"] = pd.to_datetime(df_week["date"]).dt.to_period("W").dt.start_time.dt.strftime("%d %b")
        weekly = df_week.groupby("week", sort=False)["duration_min"].sum().reset_index()
        weekly.columns = ["week", "total_min"]

        chart2 = (
            alt.Chart(weekly)
            .mark_bar(color="#2ecc71", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("week:O", title="Week", sort=None),
                y=alt.Y("total_min:Q", title="Total (min)"),
                tooltip=["week:O", "total_min:Q"],
            )
            .properties(title="Weekly volume", height=280)
        )
        st.altair_chart(chart2, use_container_width=True)

    st.subheader("📋 Recent activities")
    display_cols = [c for c in ["date","activity_type","duration_min","distance_km","avg_heart_rate","perceived_effort"] if c in df_logs.columns]
    st.dataframe(
        df_logs[display_cols].sort_values("date", ascending=False).head(20),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No activity logs found. Activities sync from Strava via Workflow D.")

# ── Body metrics ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("⚖️ Body metrics")

metrics = db.get_body_metrics(limit=30)
if metrics:
    df_metrics = pd.DataFrame(metrics)
    df_metrics["date"] = pd.to_datetime(df_metrics["date"]).dt.date

    if "weight_kg" in df_metrics.columns:
        df_metrics["weight_kg"] = pd.to_numeric(df_metrics["weight_kg"], errors="coerce")
        chart3 = (
            alt.Chart(df_metrics.dropna(subset=["weight_kg"]))
            .mark_line(point=True, color="#e74c3c")
            .encode(
                x=alt.X("date:T", title="Date", axis=alt.Axis(format="%d %b")),
                y=alt.Y("weight_kg:Q", title="Weight (kg)", scale=alt.Scale(zero=False)),
                tooltip=["date:T", "weight_kg:Q"],
            )
            .properties(title="Body weight", height=250)
        )
        st.altair_chart(chart3, use_container_width=True)

    if "body_fat_pct" in df_metrics.columns and df_metrics["body_fat_pct"].notna().any():
        chart4 = (
            alt.Chart(df_metrics.dropna(subset=["body_fat_pct"]))
            .mark_line(point=True, color="#9b59b6")
            .encode(
                x=alt.X("date:T", title="Date", axis=alt.Axis(format="%d %b")),
                y=alt.Y("body_fat_pct:Q", title="Body fat (%)", scale=alt.Scale(zero=False)),
                tooltip=["date:T", "body_fat_pct:Q"],
            )
            .properties(title="Body fat %", height=250)
        )
        st.altair_chart(chart4, use_container_width=True)
else:
    st.info("No body metrics found. Send a Withings screenshot via Telegram to log measurements.")

# ── Training plan adherence ────────────────────────────────────────────────────
st.divider()
st.subheader("✅ Training plan adherence — last 4 weeks")

plan_sessions = db.get_training_sessions(
    (today - timedelta(days=28)).isoformat(),
    today.isoformat(),
)
if plan_sessions:
    status_counts = pd.Series([s.get("status","planned") for s in plan_sessions]).value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    colors = {"planned":"#95a5a6","done":"#2ecc71","skipped":"#e74c3c","modified":"#f39c12"}
    chart5 = (
        alt.Chart(status_counts)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color("status:N", scale=alt.Scale(
                domain=list(colors.keys()), range=list(colors.values())
            )),
            tooltip=["status:N","count:Q"],
        )
        .properties(title="Session status breakdown", height=250)
    )
    st.altair_chart(chart5, use_container_width=False)
