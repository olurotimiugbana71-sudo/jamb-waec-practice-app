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
    }

    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        raw_text = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(raw_text)
        return data["questions"]
    except Exception as e:
        st.error(f"Couldn't generate questions right now ({e}). Try again in a moment.")
        return []