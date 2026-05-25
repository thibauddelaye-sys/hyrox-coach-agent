"""Airtable data access layer — all reads/writes go through here."""

import os
from datetime import date, timedelta
from typing import Optional
import streamlit as st
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

# Base ID — extract only the app ID (first segment) from the env var
_raw_base = os.getenv("AIRTABLE_BASE_ID", "appqP1oYIhYTh1Hgr")
_BASE_ID  = _raw_base.split("/")[0]

# Table IDs — env vars override the hardcoded defaults
_PROFILE_TABLE   = os.getenv("AIRTABLE_PROFILE_TABLE",   "tbloi8D9r6OWC5jXp")
_TRAINING_TABLE  = os.getenv("AIRTABLE_TRAINING_TABLE",  "tblCfdZNzkVH3heRm")
_LOGS_TABLE      = os.getenv("AIRTABLE_LOGS_TABLE",      "tblHOfZ0PU1zGkeLU")
_CHAT_TABLE      = os.getenv("AIRTABLE_CHAT_TABLE",      "tbls3jjCO1m5fio0c")
_NUTRITION_TABLE      = os.getenv("AIRTABLE_NUTRITION_TABLE",      "")
_NUTRITION_LOGS_TABLE = os.getenv("AIRTABLE_NUTRITION_LOGS_TABLE", "")
_METRICS_TABLE        = os.getenv("AIRTABLE_METRICS_TABLE",        "")


def _api() -> Api:
    token = os.getenv("AIRTABLE_TOKEN") or os.environ["AIRTABLE_API_KEY"]
    return Api(token)


def _table(table_id: str):
    return _api().table(_BASE_ID, table_id)


# ── Reads ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_athlete_profile() -> dict:
    records = _table(_PROFILE_TABLE).all(max_records=1)
    if not records:
        return {}
    r = records[0]
    return {"id": r["id"], **r.get("fields", {})}


@st.cache_data(ttl=300)
def get_training_sessions(start: str, end: str) -> list[dict]:
    formula = (
        f"AND(NOT(IS_BEFORE({{date}},'{start}')), "
        f"NOT(IS_AFTER({{date}},'{end}')))"
    )
    records = _table(_TRAINING_TABLE).all(
        formula=formula,
        sort=["date"],
    )
    return [{"id": r["id"], **r.get("fields", {})} for r in records]


@st.cache_data(ttl=300)
def get_nutrition_plans(start: str, end: str) -> list[dict]:
    if not _NUTRITION_TABLE:
        return []
    try:
        formula = (
            f"AND(NOT(IS_BEFORE({{date}},'{start}')), "
            f"NOT(IS_AFTER({{date}},'{end}')))"
        )
        records = _table(_NUTRITION_TABLE).all(formula=formula)
        return [{"id": r["id"], **r.get("fields", {})} for r in records]
    except Exception:
        return []


@st.cache_data(ttl=300)
def get_daily_logs(start: str, end: str) -> list[dict]:
    try:
        formula = (
            f"AND(NOT(IS_BEFORE({{date}},'{start}')), "
            f"NOT(IS_AFTER({{date}},'{end}')))"
        )
        records = _table(_LOGS_TABLE).all(formula=formula)
        return [{"id": r["id"], **r.get("fields", {})} for r in records]
    except Exception:
        return []


@st.cache_data(ttl=300)
def get_body_metrics(limit: int = 30) -> list[dict]:
    if not _METRICS_TABLE:
        return []
    try:
        records = _table(_METRICS_TABLE).all(
            sort=["-date"],
            max_records=limit,
        )
        return [{"id": r["id"], **r.get("fields", {})} for r in records]
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_chat_history(limit: int = 100) -> list[dict]:
    records = _table(_CHAT_TABLE).all(
        sort=["-timestamp"],
        max_records=limit,
    )
    return [{"id": r["id"], **r.get("fields", {})} for r in reversed(records)]


# ── Writes (no cache) ──────────────────────────────────────────────────────────

def update_training_session(record_id: str, fields: dict) -> dict:
    result = _table(_TRAINING_TABLE).update(record_id, fields, typecast=True)
    get_training_sessions.clear()
    return result.get("fields", {})


def find_session_by_date(session_date: str) -> Optional[dict]:
    formula = f"IS_SAME({{date}},'{session_date}','day')"
    records = _table(_TRAINING_TABLE).all(formula=formula, max_records=1)
    if not records:
        return None
    r = records[0]
    return {"id": r["id"], **r.get("fields", {})}


def delete_sessions_by_date_range(start: str, end: str, status_filter: str = "planned") -> int:
    formula = (
        f"AND({{status}}='{status_filter}', "
        f"NOT(IS_BEFORE({{date}},'{start}')), "
        f"NOT(IS_AFTER({{date}},'{end}')))"
    )
    records = _table(_TRAINING_TABLE).all(formula=formula)
    ids = [r["id"] for r in records]
    for rid in ids:
        _table(_TRAINING_TABLE).delete(rid)
    get_training_sessions.clear()
    return len(ids)


def insert_sessions(sessions: list[dict]) -> None:
    tbl = _table(_TRAINING_TABLE)
    for s in sessions:
        tbl.create(s, typecast=True)
    get_training_sessions.clear()


def insert_nutrition_plans(plans: list[dict]) -> None:
    if not _NUTRITION_TABLE:
        return
    tbl = _table(_NUTRITION_TABLE)
    for p in plans:
        tbl.create(p, typecast=True)
    get_nutrition_plans.clear()


def delete_nutrition_by_date_range(start: str, end: str) -> int:
    if not _NUTRITION_TABLE:
        return 0
    formula = (
        f"AND(NOT(IS_BEFORE({{date}},'{start}')), "
        f"NOT(IS_AFTER({{date}},'{end}')))"
    )
    records = _table(_NUTRITION_TABLE).all(formula=formula)
    ids = [r["id"] for r in records]
    for rid in ids:
        _table(_NUTRITION_TABLE).delete(rid)
    get_nutrition_plans.clear()
    return len(ids)


def insert_body_metrics(record: dict) -> None:
    if not _METRICS_TABLE:
        raise ValueError("AIRTABLE_METRICS_TABLE not set in .env")
    _table(_METRICS_TABLE).create(record, typecast=True)
    get_body_metrics.clear()


def insert_nutrition_log(record: dict) -> None:
    if not _NUTRITION_LOGS_TABLE:
        raise ValueError("AIRTABLE_NUTRITION_LOGS_TABLE not set in .env")
    _table(_NUTRITION_LOGS_TABLE).create(record, typecast=True)


def insert_daily_log(record: dict) -> None:
    _table(_LOGS_TABLE).create(record, typecast=True)
    get_daily_logs.clear()


def log_chat_message(role: str, content: str, session_id: str) -> None:
    from datetime import datetime, timezone
    _table(_CHAT_TABLE).create({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": content,
        "session_id": session_id,
    }, typecast=True)
    get_chat_history.clear()
