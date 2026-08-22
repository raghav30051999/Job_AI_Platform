import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # reads local .env on your machine; no-op on Streamlit Cloud


def _get(name, default=None):
    """Streamlit Secrets (cloud) → environment/.env (local) → default."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


# --- Gemini ---
GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-3.1-flash-lite")

# --- Mailtrap POP3 (reading) ---
POP3_HOST = _get("POP3_HOST")
POP3_PORT = _get("POP3_PORT", "995")
POP3_USER = _get("POP3_USER")
POP3_PASS = _get("POP3_PASS")

# --- Mailtrap SMTP (injecting test emails) ---
SMTP_HOST = _get("SMTP_HOST")
SMTP_PORT = _get("SMTP_PORT", "587")
SMTP_USER = _get("SMTP_USER")
SMTP_PASS = _get("SMTP_PASS")