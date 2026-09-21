"""
app.py
------
The main Streamlit page. This is the file you run with `streamlit run app.py`.
It handles: session state, the setup screen, the quiz screen, the results
screen, and the free-limit paywall.
"""

import streamlit as st
from datetime import date

from config import APP_NAME, FREE_QUESTIONS_PER_DAY, SELAR_SUBJECT_PACK_URL, SITE_URL, SUBJECTS, EXAM_TYPES
from question_generator import generate_questions

# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

def init_state():
    defaults = {
        "quiz": [],
        "current_q": 0,
        "score": 0,
        "answers": {},
        "quiz_started": False,
        "quiz_finished": False,
        "questions_used_today": 0,
        "last_used_date": str(date.today()),
        "unlocked": False,   # True after share-to-unlock or payment
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # reset the daily counter on a new day
    if st.session_state.last_used_date != str(date.today()):
        st.session_state.questions_used_today = 0
        st.session_state.last_used_date = str(date.today())
        st.session_state.unlocked = False


def free_questions_remaining():
    return max(0, FREE_QUESTIONS_PER_DAY - st.session_state.questions_used_today)


# ---------------------------------------------------------------------------
# SCREENS
# ---------------------------------------------------------------------------

def render_header():
    st.set_page_config(page_title=APP_NAME, page_icon="📘", layout="centered")
    st.title(f"📘 {APP_NAME}")
    st.caption("Free daily JAMB / WAEC / NECO practice, graded instantly by AI.")


def render_setup_screen():
    st.subheader("Start a practice quiz")

    remaining = free_questions_remaining()
    if remaining <= 0 and not st.session_state.unlocked:
        render_paywall()
        return

    st.info(f"You have {remaining} free questions left today.")

    col1, col2 = st.columns(2)
    with col1:
        exam_type = st.selectbox("Exam", EXAM_TYPES)
    with col2:
        subject = st.selectbox("Subject", SUBJECTS)

    topic = st.text_input("Topic (optional - leave blank for general coverage)")
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")

    num_questions = min(5, remaining) if not st.session_state.unlocked else 5

    if st.button("Start quiz", type="primary", use_container_width=True):
        with st.spinner("Building your quiz..."):
            questions = generate_questions(exam_type, subject, topic, difficulty, num_questions)
        if questions:
            st.session_state.quiz = questions
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.answers = {}
            st.session_state.quiz_started = True
            st.session_state.quiz_finished = False
            st.session_state.questions_used_today += len(questions)
            st.rerun()


def render_quiz_screen():
    quiz = st.session_state.quiz
    i = st.session_state.current_q
    q = quiz[i]

    st.progress(i / len(quiz), text=f"Question {i + 1} of {len(quiz)}")
    st.subheader(q["question"])

    choice = st.radio(
        "Choose an answer",
        options=list(q["options"].keys()),
        format_func=lambda k: f"{k}. {q['options'][k]}",
        key=f"choice_{i}",
        index=None,
    )

    if st.button("Submit answer", type="primary"):
        if choice is None:
            st.warning("Pick an option first.")
        else:
            st.session_state.answers[i] = choice
            if choice == q["correct_option"]:
                st.session_state.score += 1
                st.success("Correct! " + q["explanation"])
            else:
                st.error(f"Not quite. Correct answer: {q['correct_option']}. " + q["explanation"])

            if i + 1 < len(quiz):
                st.session_state.current_q += 1
            else:
                st.session_state.quiz_finished = True
            st.rerun()


def render_results_screen():
    score = st.session_state.score
    total = len(st.session_state.quiz)
    st.subheader("Quiz complete")
    st.metric("Your score", f"{score}/{total}")

    if score / total >= 0.7:
        st.success("Strong performance — keep this streak going tomorrow.")
    else:
        st.info("Review the explanations above, then try another topic.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Practice another topic", use_container_width=True):
            st.session_state.quiz_started = False
            st.rerun()
    with col2:
        share_text = f"I scored {score}/{total} on {APP_NAME}! Try it free:"
        wa_link = f"https://wa.me/?text={share_text}%20{SITE_URL}"
        st.link_button("Share my score", wa_link, use_container_width=True)


def render_paywall():
    st.warning("You've used today's free questions.")
    st.write("Unlock unlimited practice for the rest of today by:")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Option A - Share to unlock**")
        invite_link = f"https://wa.me/?text=Practice free JAMB/WAEC questions with AI: {SITE_URL}"
        st.link_button("Invite 3 friends", invite_link, use_container_width=True)
        if st.button("I've shared - unlock now", use_container_width=True):
            st.session_state.unlocked = True
            st.rerun()
    with col2:
        st.markdown("**Option B - Buy a subject pack**")
        st.link_button("Buy pack - Selar", SELAR_SUBJECT_PACK_URL, use_container_width=True)

    st.caption("Free questions reset tomorrow either way.")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    init_state()
    render_header()

    if not st.session_state.quiz_started:
        render_setup_screen()
    elif st.session_state.quiz_finished:
        render_results_screen()
    else:
        render_quiz_screen()


if __name__ == "__main__":
    main()