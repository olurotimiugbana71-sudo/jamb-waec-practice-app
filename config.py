"""
config.py
---------
All constants for the app live here, plus the API key / secret loaders.
Keeping this in one small file means you only ever have to look in one
place to change pricing, subjects, branding, or limits later.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # loads variables from a local .env file, if one exists

APP_NAME = "ExamPrep AI"

# --- Branding / contact ------------------------------------------------
BRAND_NAME = "ApexDynamics Solutions"
CONTACT_EMAIL = "olurotimiugbana71@gmail.com"
TELEGRAM_HANDLE = "ApexDynamics Solutions"
WHATSAPP_NUMBER = "2348065209323"
WHATSAPP_LINK = f"https://wa.me/{WHATSAPP_NUMBER}"

# --- Quiz settings -------------------------------------------------------
FREE_QUESTIONS_PER_DAY = 15
ADVANCED_MIN_QUESTIONS = 40
ADVANCED_MAX_QUESTIONS = 50

SITE_URL = "https://apexdynamics-solutions.vercel.app"

SUBJECTS = [
    "Mathematics", "English Language", "Physics", "Chemistry", "Biology",
    "Economics", "Government", "Literature in English", "Financial Accounting",
]

EXAM_TYPES = ["JAMB (UTME)", "WAEC", "NECO"]

GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- Payment links ---------------------------------------------------------
# Local (Naira, cards, bank transfer):
SELAR_SUBJECT_PACK_URL = "https://selar.co/apexdynamics"
# International (USD, cards, PayPal) - see the guide for setup:
INTERNATIONAL_PAYMENT_URL = "https://your-lemonsqueezy-or-payhip-link-here"


def _get_secret(name):
    """
    Reads a secret from Streamlit Cloud's secrets manager first (that's
    how it works once deployed), and falls back to a local .env file
    (that's how it works on your machine). Same code, both places.
    """
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, "")


GROQ_API_KEY = _get_secret("GROQ_API_KEY")
LICENSE_SECRET = _get_secret("LICENSE_SECRET")