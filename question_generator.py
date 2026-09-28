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


def _normalize_question(q):
    """
    The AI occasionally returns a question with a missing or renamed field
    (e.g. "correct_answer" instead of "correct_option"). This repairs what it
    can and returns None for anything unusable, so one bad question never
    crashes the quiz.
    """
    if not isinstance(q, dict):
        return None

    question = q.get("question")
    options = q.get("options")
    if isinstance(options, list) and len(options) == 4:
        options = dict(zip("ABCD", options))
    if not isinstance(question, str) or not isinstance(options, dict):
        return None

    options = {str(k).strip().strip("().:").upper(): str(v) for k, v in options.items()}
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

    return {
        "question": question.strip(),
        "options": options,
        "correct_option": letter,
        "explanation": str(q.get("explanation") or "No explanation provided."),
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