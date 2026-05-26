"""Log a screenshot via OpenAI Vision — body metrics, nutrition, or training summary."""

import sys
import base64
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import streamlit as st
from datetime import date
from openai import OpenAI

from dashboard.lib.styles import inject_bg
inject_bg("bg_nutrition.jpg")
from dashboard.lib import airtable_client as db

st.set_page_config(page_title="Log Screenshot · Hyrox Coach", page_icon="📸", layout="wide")
st.title("📸 Log Screenshot")
st.caption("Upload a screenshot or take a photo — body metrics, meals, and training summaries are extracted automatically.")

tab_upload, tab_camera = st.tabs(["📁 Upload file", "📷 Take photo"])

with tab_upload:
    uploaded = st.file_uploader(
        "Upload screenshot",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

with tab_camera:
    camera_photo = st.camera_input("Take a photo", label_visibility="collapsed")

source = uploaded or camera_photo

if not source:
    st.info("Upload a screenshot or take a photo to get started.")
    st.stop()

img_bytes = source.read()
mime = source.type or "image/jpeg"
data_url = f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LABEL = {
    "body_metrics": "⚖️ Body metrics",
    "nutrition":    "🥗 Nutrition / meal",
    "other":        "❓ Other",
}


def vision(prompt: str, max_tokens: int = 300) -> str:
    resp = client.chat.completions.create(
        model="gpt-4.1",
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
    )
    return resp.choices[0].message.content.strip()


def parse_json(raw: str) -> dict:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def llm(prompt: str, max_tokens: int = 400) -> str:
    resp = client.chat.completions.create(
        model="gpt-4.1",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


# ── Auto-classify on upload (cached by image fingerprint) ───────────────────
img_key = hashlib.md5(img_bytes).hexdigest()

if st.session_state.get("img_key") != img_key:
    with st.spinner("Analysing image…"):
        raw_cls = vision(
            "Look at this image. Classify it as ONE of: "
            "body_metrics, nutrition, other.\n"
            "- body_metrics: scale/Withings/Garmin showing weight, body fat %, muscle mass\n"
            "- nutrition: food photos, restaurant menus, nutrition labels, meal app screenshots\n"
            "- other: anything else (training summaries, maps, etc.)\n\n"
            "Reply with ONLY the category name, nothing else.",
            max_tokens=20,
        )
        valid = {"body_metrics", "nutrition"}
        c = raw_cls.strip().lower()
        st.session_state.classification = c if c in valid else "other"
        st.session_state.img_key = img_key

classification = st.session_state.classification

# ── Date picker dialog ────────────────────────────────────────────────────────
_date_key = f"log_date_{img_key}"

@st.dialog("📅 When was this?")
def _pick_date():
    d = st.date_input("Date", value=date.today(), label_visibility="collapsed")
    if st.button("Confirm", type="primary", use_container_width=True):
        st.session_state[_date_key] = d
        st.rerun()

if classification != "other" and _date_key not in st.session_state:
    _pick_date()
    st.stop()

log_date = st.session_state.get(_date_key, date.today())

# ── Layout ───────────────────────────────────────────────────────────────────
col_img, col_result = st.columns([1, 2])

with col_img:
    label = source.name if uploaded else "Camera capture"
    st.image(img_bytes, caption=label, use_container_width=True)
    st.info(f"Detected: **{LABEL[classification]}**")

with col_result:
    if classification == "other":
        st.warning(
            "I can't extract structured data from this screenshot type. "
            "Try a Withings body scan or a food photo. "
            "Training activities are synced automatically via Strava."
        )
        st.stop()

    # ── Date — shown as a caption with a change button ───────────────────────
    col_date, col_change = st.columns([3, 1])
    col_date.caption(f"📅 Logging for **{log_date.strftime('%A %d %b %Y')}**")
    if col_change.button("Change date", use_container_width=True):
        del st.session_state[_date_key]
        st.rerun()

    # Meal-specific fields — only rendered when the image is a meal
    meal_type_override = "lunch"
    meal_description = ""
    if classification == "nutrition":
        meal_type_override = st.selectbox(
            "Meal type",
            options=["breakfast", "lunch", "dinner", "snack"],
            index=1,
            format_func=lambda x: x.capitalize(),
        )
        meal_description = st.text_area(
            "Describe your meal (optional — helps the AI be more accurate)",
            placeholder="e.g. chicken breast with rice and broccoli, ~200g chicken",
            height=80,
        )

    if st.button("📥 Log", type="primary", use_container_width=True):

        if classification == "body_metrics":
            with st.spinner("Extracting body metrics…"):
                raw = vision(
                    'Extract these fields. Return ONLY valid JSON, no markdown:\n\n'
                    '{"weight_kg": <number or null>, "body_fat_pct": <number or null>, '
                    '"muscle_mass_kg": <number or null>, '
                    '"screenshot_source": "withings" or "garmin" or "other"}\n\n'
                    'Set to null if not visible. Assume metric units.',
                    max_tokens=200,
                )
            try:
                data = parse_json(raw)
            except Exception:
                st.error(f"Could not parse LLM response:\n\n{raw}")
                st.stop()

            record = {k: v for k, v in {
                "date":              log_date.isoformat(),
                "weight_kg":         data.get("weight_kg"),
                "body_fat_pct":      data.get("body_fat_pct"),
                "muscle_mass_kg":    data.get("muscle_mass_kg"),
                "screenshot_source": data.get("screenshot_source", "other"),
            }.items() if v is not None}

            try:
                db.insert_body_metrics(record)
            except ValueError as e:
                st.error(str(e))
                st.stop()

            st.success("✅ Body metrics logged!")
            c1, c2, c3 = st.columns(3)
            if data.get("weight_kg"):      c1.metric("Weight",      f"{data['weight_kg']} kg")
            if data.get("body_fat_pct"):   c2.metric("Body fat",    f"{data['body_fat_pct']} %")
            if data.get("muscle_mass_kg"): c3.metric("Muscle mass", f"{data['muscle_mass_kg']} kg")

        elif classification == "nutrition":
            user_hint = f'\nThe user describes the meal as: "{meal_description}"' if meal_description.strip() else ""
            with st.spinner("Extracting meal data…"):
                raw = vision(
                    'Extract meal information. Return ONLY valid JSON, no markdown:\n\n'
                    '{"meal_type": "breakfast" or "lunch" or "dinner" or "snack", '
                    '"description": "<max 150 chars>", '
                    '"estimated_kcal": <number>, "estimated_protein_g": <number>, '
                    '"estimated_carbs_g": <number>, "estimated_fat_g": <number>}\n\n'
                    'Use exact values if shown in an app. Estimate for food photos.'
                    + user_hint,
                    max_tokens=300,
                )
            try:
                data = parse_json(raw)
            except Exception:
                st.error(f"Could not parse LLM response:\n\n{raw}")
                st.stop()

            record = {k: v for k, v in {
                "date":                log_date.isoformat(),
                "meal_type":           meal_type_override,
                "description":         data.get("description", ""),
                "estimated_kcal":      data.get("estimated_kcal"),
                "estimated_protein_g": data.get("estimated_protein_g"),
                "estimated_carbs_g":   data.get("estimated_carbs_g"),
                "estimated_fat_g":     data.get("estimated_fat_g"),
                "source":              "photo",
            }.items() if v is not None}

            try:
                db.insert_nutrition_log(record)
            except ValueError as e:
                st.error(str(e))
                st.stop()

            st.success(f"✅ {record.get('meal_type', 'Meal').capitalize()} logged!")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Calories", f"{data.get('estimated_kcal', '?')} kcal")
            c2.metric("Protein",  f"{data.get('estimated_protein_g', '?')} g")
            c3.metric("Carbs",    f"{data.get('estimated_carbs_g', '?')} g")
            c4.metric("Fat",      f"{data.get('estimated_fat_g', '?')} g")
            if record.get("description"):
                st.caption(record["description"])

            st.divider()
            with st.spinner("Assessing meal vs your training day…"):
                session = db.find_session_by_date(log_date.isoformat())
                session_context = (
                    f"Today's planned session: {session.get('session_type', session.get('activity_type', 'unknown'))} — "
                    f"{session.get('focus', '')} {session.get('notes', '')}".strip()
                    if session else "No training session planned today (rest day)."
                )
                assessment = llm(
                    f"You are a sports nutritionist coaching a Hyrox athlete.\n\n"
                    f"{session_context}\n\n"
                    f"The athlete just logged a {meal_type_override}:\n"
                    f"- Calories: {data.get('estimated_kcal', '?')} kcal\n"
                    f"- Protein: {data.get('estimated_protein_g', '?')} g\n"
                    f"- Carbs: {data.get('estimated_carbs_g', '?')} g\n"
                    f"- Fat: {data.get('estimated_fat_g', '?')} g\n"
                    f"- Description: {data.get('description', meal_description or 'not specified')}\n\n"
                    f"Give a brief 2-3 sentence assessment: is this meal well-suited to today's training? "
                    f"One concrete suggestion if needed. Be direct and practical.",
                    max_tokens=150,
                )
            st.markdown(f"""
<div style="border-left:3px solid rgba(255,255,255,0.6);padding:.75rem 1rem;background:rgba(255,255,255,0.08);border-radius:4px">
<strong>Nutrition assessment</strong><br><br>{assessment}
</div>
""", unsafe_allow_html=True)

