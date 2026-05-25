"""Shared CSS utilities for the Hyrox Coach dashboard."""

import base64
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def inject_bg(filename: str, overlay_opacity: float = 0.55) -> None:
    """Inject a full-page background image with a dark overlay."""
    path = ASSETS / filename
    if not path.exists():
        return
    b64 = base64.b64encode(path.read_bytes()).decode()
    ext = path.suffix.lstrip(".")
    data_url = f"data:image/{ext};base64,{b64}"
    alpha = overlay_opacity
    st.markdown(f"""
<style>
.stApp {{
    background-image: linear-gradient(rgba(0,0,0,{alpha}), rgba(0,0,0,{alpha})),
                      url("{data_url}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}}
.stApp > .main,
section[data-testid="stMain"],
.block-container,
[data-testid="block-container"] {{
    background: transparent !important;
}}
[data-testid="stSidebar"] {{
    background-color: rgba(12, 12, 12, 0.85) !important;
}}
</style>
""", unsafe_allow_html=True)
