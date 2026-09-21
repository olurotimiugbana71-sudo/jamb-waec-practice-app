"""
config.py
---------
All constants for the app live here, plus the API key loader. Keeping this
in one small file means you only ever have to look in one place to change
pricing, subjects, or limits later.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # loads variables from a local .env file, if one exists

APP_NAME = "ExamPrep AI"
FREE_QUESTIONS_PER_DAY = 15
SELAR_SUBJECT_PACK_URL = "https://selar.co/apexdynamics"
SITE_URL = "https://apexdynamics-solutions.vercel.app"
WHATSAPP_NUMBER = "2348065209323"

SUBJECTS = [
    "Mathematics", "English Language", "Physics", "Chemistry", "Biology",
    "Economics", "Government", "Literature in English", "Financial Accounting",
]

EXAM_TYPES = ["JAMB (UTME)", "WAEC", "NECO"]

GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _get_api_key():
    """
    Reads the key from Streamlit Cloud's secrets manager first (that's how
    it works once deployed), and falls back to a local .env file (that's
    how it works on your machine). Same code, both places.
    """
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")


GROQ_API_KEY = _get_api_key()