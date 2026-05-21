"""OpenAI chat engine with function-calling tools for the Streamlit dashboard."""

import json
import os
from datetime import date, timedelta
from typing import Generator

import cohere
from openai import OpenAI
from pinecone import Pinecone

from dashboard.lib import airtable_client as db

_OPENAI_MODEL = os.getenv("OPENAI_MODEL_CHAT", "gpt-4o-mini")
_EMBED_MODEL  = os.getenv("OPENAI_MODEL_EMBEDDING", "text-embedding-3-small")
_PINECONE_INDEX = os.environ["PINECONE_INDEX_NAME"]

SYSTEM_MESSAGE = """\
You are Hyrox Coach, an AI providing personalised training and nutrition coaching \
to a single athlete preparing for Hyrox races. You are a strength & conditioning coach, \
endurance coach, and sports nutritionist in one — but not a medical replacement.

OPERATING PRINCIPLES:
1. Be specific and numbers-backed. Never generic.
2. Use the athlete's context (phase, recent sessions, injuries) in every reply.
3. Cite the knowledge base for periodization, nutrient timing, Hyrox-specific programming.
4. Honor coach_tone and coach_severity from the athlete profile.
5. Default to safety: report pain or unusual fatigue → recommend rest and/or medical advice.
6. Stay in scope: Hyrox prep, training, nutrition, recovery only.
7. Replies under 200 words unless the athlete asks for a detailed plan.

TOOLS — when and how to use them:
- search_knowledge_base: use for "why" questions, periodization or nutrition specifics.
- update_training_session: call FIRST when the athlete wants to modify a single session, \
then confirm using the tool's return value. NEVER say "done" before calling this tool.
- replan_week: call FIRST when the athlete wants to change multiple sessions or the whole \
week. MANDATORY: call the tool before writing any plan text. Use the recap from the tool \
result in your reply.

IMPORTANT: A Hyrox training week = 7 days, Monday through Sunday, weekends fully included.\
"""

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the Hyrox knowledge base for training, nutrition, or recovery information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_training_session",
            "description": (
                "Saves a changed training session to Airtable. Call FIRST — before any reply "
                "describing the change. Do NOT say 'updated' or 'done' before this tool returns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date":         {"type": "string", "description": "YYYY-MM-DD"},
                    "session_type": {"type": "string"},
                    "description":  {"type": "string"},
                    "duration_min": {"type": "integer"},
                    "intensity":    {"type": "string", "enum": ["easy", "moderate", "hard", "max"]},
                    "notes":        {"type": "string"},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replan_week",
            "description": (
                "Generates a new 7-day training plan and saves it to Airtable. "
                "Call FIRST — before writing any plan in the response. "
                "Returns a recap string to include in the reply."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Short reason for replanning"}
                },
                "required": ["reason"],
            },
        },
    },
]


# ── Tool implementations ───────────────────────────────────────────────────────

def _search_knowledge_base(query: str) -> str:
    openai_client = OpenAI()
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(_PINECONE_INDEX)
    co = cohere.Client(os.environ["COHERE_API_KEY"])

    embedding = openai_client.embeddings.create(
        model=_EMBED_MODEL, input=[query]
    ).data[0].embedding

    results = index.query(vector=embedding, top_k=10, include_metadata=True)
    matches = results.get("matches", [])
    if not matches:
        return "No relevant results found."

    docs = [m["metadata"].get("text", "") for m in matches]
    reranked = co.rerank(query=query, documents=docs, top_n=3, model="rerank-english-v3.0")

    snippets = []
    for r in reranked.results:
        source = matches[r.index]["metadata"].get("source", "unknown")
        snippets.append(f"[{source}] {docs[r.index][:400]}")
    return "\n\n".join(snippets)


def _update_training_session(date_str: str, **fields) -> str:
    session = db.find_session_by_date(date_str)
    if not session:
        return f"No session found for {date_str}."

    update_fields = {k: v for k, v in fields.items() if v is not None and v != ""}
    update_fields["status"] = "modified"

    db.update_training_session(session["id"], update_fields)
    changed = ", ".join(f"{k}={v}" for k, v in update_fields.items() if k != "status")
    return f"Session on {date_str} updated: {changed}. Status set to modified."


def _replan_week(reason: str, athlete_profile: dict) -> str:
    from math import ceil

    today = date.today()
    dow = today.weekday()  # 0=Mon
    days_to_monday = 0 if dow <= 1 else (7 - dow)
    week_start = today + timedelta(days=days_to_monday)
    week_end = week_start + timedelta(days=6)
    week_dates = [(week_start + timedelta(days=i)).isoformat() for i in range(7)]

    target_raw = athlete_profile.get("hyrox_target_date", "2026-08-15")
    target_date = date.fromisoformat(target_raw[:10])
    weeks_to_race = ceil((target_date - today).days / 7)
    if weeks_to_race <= 2:
        phase = "Taper"
    elif weeks_to_race <= 5:
        phase = "Peak"
    elif weeks_to_race <= 12:
        phase = "Build"
    else:
        phase = "Base"
    week_number = max(1, 20 - weeks_to_race + 1)

    existing_sessions = db.get_training_sessions(week_start.isoformat(), week_end.isoformat())
    done_summary = "\n".join(
        f"- {s['date']}: {s.get('session_type','?')} ({s.get('status','?')})"
        for s in existing_sessions
        if s.get("status") in ("done", "skipped")
    ) or "None so far"

    recent_logs = db.get_daily_logs(
        (today - timedelta(days=14)).isoformat(), today.isoformat()
    )
    recent_summary = "\n".join(
        f"- {l.get('date','?')}: {l.get('activity_type','?')} "
        f"({l.get('duration_min','?')}min)"
        for l in recent_logs[-10:]
    ) or "No recent activities"

    equipment = athlete_profile.get("equipment_home", "")
    if isinstance(equipment, list):
        equipment = ", ".join(equipment)

    prompt = (
        f"Athlete: {athlete_profile.get('name','Athlete')}\n"
        f"Phase: {phase} (Week {week_number}, {weeks_to_race} weeks to race)\n"
        f"Reason for replan: {reason}\n"
        f"Equipment at home: {equipment}\n\n"
        f"Dates to plan (Mon–Sun): {json.dumps(week_dates)}\n\n"
        f"Sessions already done this week (DO NOT replan):\n{done_summary}\n\n"
        f"Recent training:\n{recent_summary}\n\n"
        "Produce a 7-day plan for ALL listed dates. Return JSON: "
        '{"sessions": [...], "recap": "..."} where each session has: '
        "date, session_type, description, duration_min, intensity, notes, status='planned', "
        f"phase='{phase}', week_number={week_number}."
    )

    client = OpenAI()
    response = client.chat.completions.create(
        model=_OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a Hyrox training planner. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    plan = json.loads(response.choices[0].message.content)
    sessions = plan.get("sessions", [])
    recap = plan.get("recap", "Week replanned.")

    db.delete_sessions_by_date_range(week_start.isoformat(), week_end.isoformat())
    db.delete_nutrition_by_date_range(week_start.isoformat(), week_end.isoformat())
    db.insert_sessions(sessions)

    lines = "\n".join(
        f"• {s['date']}: {s.get('session_type','?')} — {s.get('duration_min','?')}min, {s.get('intensity','?')}"
        for s in sessions
    )
    return f"{recap}\n\nUpdated sessions:\n{lines}"


# ── Main chat function ─────────────────────────────────────────────────────────

def build_context_message(athlete: dict, sessions: list[dict], logs: list[dict]) -> str:
    today = date.today().isoformat()

    target_raw = athlete.get("hyrox_target_date", "2026-08-15")
    target_date = date.fromisoformat(target_raw[:10])
    from math import ceil
    weeks_to_race = ceil((target_date - date.today()).days / 7)
    phase = (
        "Taper" if weeks_to_race <= 2 else
        "Peak"  if weeks_to_race <= 5 else
        "Build" if weeks_to_race <= 12 else "Base"
    )

    plan_str = "\n".join(
        f"- {s.get('date','?')}: {s.get('session_type','?')} "
        f"({s.get('duration_min','?')}min, {s.get('intensity','?')}) — "
        f"{str(s.get('description',''))[:80]}"
        for s in sessions
    ) or "No sessions in range"

    logs_str = "\n".join(
        f"- {l.get('date','?')}: {l.get('activity_type','?')} "
        f"({l.get('duration_min','?')}min)"
        for l in logs[-10:]
    ) or "No recent activities"

    return (
        f"Athlete: {athlete.get('name','Athlete')}\n"
        f"Date: {today}\n"
        f"Phase: {phase} ({weeks_to_race} weeks to race)\n"
        f"Coach tone: {athlete.get('coach_tone','supportive')} / {athlete.get('coach_severity','balanced')}\n"
        f"Active injuries: {athlete.get('injuries_active','none')}\n"
        f"Equipment at home: {athlete.get('equipment_home','')}\n"
        f"Target race date: {athlete.get('hyrox_target_date','')}\n\n"
        f"Current week plan:\n{plan_str}\n\n"
        f"Recent training:\n{logs_str}"
    )


def chat(
    messages: list[dict],
    athlete: dict,
    sessions: list[dict],
    logs: list[dict],
) -> Generator[str, None, None]:
    client = OpenAI()

    context = build_context_message(athlete, sessions, logs)
    full_messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user",   "content": context},
        {"role": "assistant", "content": "Understood. I have your context. How can I help?"},
    ] + messages

    while True:
        response = client.chat.completions.create(
            model=_OPENAI_MODEL,
            messages=full_messages,
            tools=_TOOLS,
            tool_choice="auto",
            stream=False,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            yield msg.content or ""
            break

        full_messages.append(msg.model_dump())

        for tc in msg.tool_calls:
            fn   = tc.function.name
            args = json.loads(tc.function.arguments)

            if fn == "search_knowledge_base":
                result = _search_knowledge_base(args["query"])
            elif fn == "update_training_session":
                date_arg = args.pop("date")
                result = _update_training_session(date_arg, **args)
            elif fn == "replan_week":
                result = _replan_week(args["reason"], athlete)
            else:
                result = f"Unknown tool: {fn}"

            full_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
