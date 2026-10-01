"""
question_generator.py
----------------------
This is the only file that talks to the AI. The prompt is split into a
fixed SYSTEM_INSTRUCTIONS block (rules that never change) and a
USER_PROMPT_TEMPLATE (the bits that change per request: exam, subject,
topic, difficulty). Groq's API is OpenAI-compatible, so this uses the
standard chat-completions shape with JSON mode forced on.
"""

import json
import re
import requests
import streamlit as st
from config import GROQ_CHAT_URL, GROQ_API_KEY, GROQ_MODEL

SYSTEM_INSTRUCTIONS = """You are an exam question generator for Nigerian secondary
school students preparing for JAMB, WAEC, or NECO.

Rules:
- Match the real syllabus and difficulty level of the specified exam board.
- Every question must be answerable from the syllabus alone, with exactly
  one unambiguously correct option.
- Distractors (wrong options) must be plausible, not silly - they should
  reflect common student mistakes.
- Explanations must be short (1-3 sentences), student-friendly, and state
  WHY the correct answer is right, not just restate it.
- Write all maths in plain text using Unicode symbols (x², √, ½, ×, ÷, π).
  Never use LaTeX or the ^ symbol for powers.
- Return ONLY valid JSON. No markdown, no commentary, no code fences.
"""

USER_PROMPT_TEMPLATE = """Generate {num_questions} multiple-choice questions.

Exam: {exam_type}
Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}

Return JSON in exactly this shape:
{{
  "questions": [
    {{
      "question": "string",
      "options": {{"A": "string", "B": "string", "C": "string", "D": "string"}},
      "correct_option": "A",
      "explanation": "string"
    }}
  ]
}}
"""

_SUPERSCRIPTS = {"0": "\u2070", "1": "\u00b9", "2": "\u00b2", "3": "\u00b3",
                 "4": "\u2074", "5": "\u2075", "6": "\u2076", "7": "\u2077",
                 "8": "\u2078", "9": "\u2079"}


def _clean_text(s):
    """
    Repairs small AI-generation glitches that have shown up in practice:
    stray backslash/garbage prefixes like "A.//e ", and "^2" written as a
    caret instead of a proper superscript. Returns None if the text still
    looks corrupted after cleanup, so the caller can drop that question.
    """
    if not isinstance(s, str):
        return None
    s = s.strip()

    # Strip a leading option-letter-like artifact, e.g. "A.//e 2x^2..." -> "2x^2..."
    s = re.sub(r"^[A-D][.)]\s*(?:/{1,}\s*\w*\s*)?", "", s)

    # Convert simple "^2" / "^12" power notation to real superscript characters
    s = re.sub(r"\^(\d{1,2})", lambda m: "".join(_SUPERSCRIPTS.get(c, c) for c in m.group(1)), s)

    s = s.strip()
    if len(s) < 3 or re.search(r"[\\/]{2,}", s):
        return None
    return s


def _normalize_question(q):
    """
    The AI occasionally returns a question with a missing or renamed field
    (e.g. "correct_answer" instead of "correct_option"). This repairs what it
    can and returns None for anything unusable, so one bad question never
    crashes the quiz.
    """
    if not isinstance(q, dict):
        return None

    question = _clean_text(q.get("question"))
    options = q.get("options")
    if isinstance(options, list) and len(options) == 4:
        options = dict(zip("ABCD", options))
    if question is None or not isinstance(options, dict):
        return None

    cleaned_options = {}
    for k, v in options.items():
        cleaned_v = _clean_text(str(v))
        if cleaned_v is None:
            return None
        cleaned_options[str(k).strip().strip("().:").upper()] = cleaned_v
    options = cleaned_options
    if set(options) != set("ABCD"):
        return None

    raw = q.get("correct_option") or q.get("correct_answer") or q.get("answer") or q.get("correct")
    if raw is None:
        return None
    raw = str(raw).strip()

    letter = None
    if raw.strip("().: ").upper() in options:
        letter = raw.strip("().: ").upper()
    else:
        m = re.match(r"^\(?([A-Da-d])[\).:]", raw)
        if m:
            letter = m.group(1).upper()
        else:
            hits = [k for k, v in options.items() if v.strip().lower() == raw.lower()]
            if len(hits) == 1:
                letter = hits[0]
    if letter is None:
        return None

    explanation = _clean_text(str(q.get("explanation") or "")) or "No explanation provided."

    return {
        "question": question,
        "options": options,
        "correct_option": letter,
        "explanation": explanation,
    }


def generate_questions(exam_type, subject, topic, difficulty="Medium", num_questions=5):
    """Calls Groq's free tier and returns a list of question dicts."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        num_questions=num_questions,
        exam_type=exam_type,
        subject=subject,
        topic=topic or "general syllabus coverage",
        difficulty=difficulty,
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
        "max_tokens": min(8000, 200 * num_questions + 500),
    }

    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        raw_text = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(raw_text)
        cleaned = [c for c in map(_normalize_question, data.get("questions", [])) if c]
        if not cleaned:
            raise ValueError("the AI returned questions in an unexpected format")
        return cleaned
    except Exception as e:
        st.error(f"Couldn't generate questions right now ({e}). Try again in a moment.")
        return []