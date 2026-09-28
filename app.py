"""
app.py
------
The main Streamlit page. This is the file you run with `streamlit run app.py`.
It handles: session state, the setup screen, the quiz screen, the results
screen, the free-limit paywall, the branded footer, and the Advanced Access
license unlock.
"""

import streamlit as st
from datetime import date

from config import (
    APP_NAME, BRAND_NAME, CONTACT_EMAIL, TELEGRAM_HANDLE, WHATSAPP_LINK,
    FREE_QUESTIONS_PER_DAY, ADVANCED_MIN_QUESTIONS, ADVANCED_MAX_QUESTIONS,
    SELAR_SUBJECT_PACK_URL, INTERNATIONAL_PAYMENT_URL, SITE_URL,
    SUBJECTS, EXAM_TYPES, LICENSE_SECRET,
)
from question_generator import generate_questions
from license import verify_license_key

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
        "answered": False,          # True once the current question is submitted
        "questions_used_today": 0,
        "last_used_date": str(date.today()),
        "unlocked": False,          # True after share-to-unlock or a Selar pack
        "advanced_unlocked": False,  # True after a verified license key
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.last_used_date != str(date.today()):
        st.session_state.questions_used_today = 0
        st.session_state.last_used_date = str(date.today())
        st.session_state.unlocked = False
        # advanced_unlocked is NOT reset daily - a license is a one-time unlock


def free_questions_remaining():
    return max(0, FREE_QUESTIONS_PER_DAY - st.session_state.questions_used_today)


# ---------------------------------------------------------------------------
# HEADER / FOOTER (branding)
# ---------------------------------------------------------------------------

def render_header():
    st.set_page_config(page_title=APP_NAME, page_icon="📘", layout="centered")
    st.title(f"📘 {APP_NAME}")
    st.caption("Free daily JAMB / WAEC / NECO practice, graded instantly by AI.")


def render_footer():
    st.divider()
    st.caption(
        f"Designed by **{BRAND_NAME}**  \n"
        f"📧 {CONTACT_EMAIL}  ·  📱 Telegram: {TELEGRAM_HANDLE}  ·  "
        f"💬 [WhatsApp]({WHATSAPP_LINK})"
    )


def render_advanced_access_sidebar():
    """Email + license key entry, and a bit of upsell copy, in the sidebar."""
    with st.sidebar:
        st.subheader("🔑 Advanced Access")

        if st.session_state.advanced_unlocked:
            st.success("Advanced Access is active — up to 50 questions per quiz.")
            return

        st.write(
            f"Unlock **{ADVANCED_MIN_QUESTIONS}–{ADVANCED_MAX_QUESTIONS} questions per "
            "quiz** with no daily limit."
        )

        with st.expander("I already have a license key"):
            email = st.text_input("Email used at purchase", key="license_email")
            key = st.text_input("License key", key="license_key_input")
            if st.button("Verify key"):
                if verify_license_key(email, key, LICENSE_SECRET):
                    st.session_state.advanced_unlocked = True
                    st.success("Verified! Advanced Access is now active.")
                    st.rerun()
                else:
                    st.error("That email/key combination isn't valid. Double-check both.")

        with st.expander("Get a license key"):
            st.markdown(f"**🇳🇬 Local (Naira, card/bank transfer):**")
            st.link_button("Pay with Selar", SELAR_SUBJECT_PACK_URL, use_container_width=True)
            st.markdown(f"**🌍 International (USD, card/PayPal):**")
            st.link_button("Pay internationally", INTERNATIONAL_PAYMENT_URL, use_container_width=True)
            st.caption(
                "After payment, message us with your payment receipt and the email "
                f"you paid with: 📧 {CONTACT_EMAIL} or 💬 [WhatsApp]({WHATSAPP_LINK}). "
                "We'll send your license key."
            )


# ---------------------------------------------------------------------------
# SCREENS
# ---------------------------------------------------------------------------

def render_setup_screen():
    st.subheader("Start a practice quiz")

    advanced = st.session_state.advanced_unlocked

    if not advanced:
        remaining = free_questions_remaining()
        if remaining <= 0:
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

    if advanced:
        num_questions = st.slider(
            "Number of questions",
            min_value=ADVANCED_MIN_QUESTIONS,
            max_value=ADVANCED_MAX_QUESTIONS,
            value=ADVANCED_MIN_QUESTIONS,
        )
    else:
        num_questions = min(5, free_questions_remaining())

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
            st.session_state.answered = False
            if not advanced:
                st.session_state.questions_used_today += len(questions)
            st.rerun()


def render_quiz_screen():
    quiz = st.session_state.quiz
    i = st.session_state.current_q
    q = quiz[i]
    answered = st.session_state.answered

    st.progress(i / len(quiz), text=f"Question {i + 1} of {len(quiz)}")
    st.subheader(q["question"])

    choice = st.radio(
        "Choose an answer",
        options=list(q["options"].keys()),
        format_func=lambda k: f"{k}. {q['options'][k]}",
        key=f"choice_{i}",
        index=None,
        disabled=answered,
    )

    if not answered:
        if st.button("Submit answer", type="primary"):
            if choice is None:
                st.warning("Pick an option first.")
            else:
                st.session_state.answers[i] = choice
                if choice == q["correct_option"]:
                    st.session_state.score += 1
                st.session_state.answered = True
                st.rerun()
    else:
        # Feedback stays on screen until the student clicks Next
        picked = st.session_state.answers.get(i)
        if picked == q["correct_option"]:
            st.success("Correct! " + q["explanation"])
        else:
            st.error(
                f"Not quite. The correct answer is {q['correct_option']}. "
                + q["explanation"]
            )

        is_last = i + 1 >= len(quiz)
        if st.button("See results" if is_last else "Next question", type="primary"):
            st.session_state.answered = False
            if is_last:
                st.session_state.quiz_finished = True
            else:
                st.session_state.current_q += 1
            st.rerun()


def render_results_screen():
    quiz = st.session_state.quiz
    score = st.session_state.score
    total = len(quiz)
    st.subheader("Quiz complete")
    st.metric("Your score", f"{score}/{total}")

    if score / total >= 0.7:
        st.success("Strong performance — keep this streak going tomorrow.")
    else:
        st.info("Review the explanations below, then try another topic.")

    st.markdown("### Review your answers")
    for idx, q in enumerate(quiz):
        picked = st.session_state.answers.get(idx)
        correct = q["correct_option"]
        is_right = picked == correct
        icon = "✅" if is_right else "❌"
        with st.expander(f"{icon} Question {idx + 1}: {q['question']}", expanded=not is_right):
            picked_text = f"{picked}. {q['options'][picked]}" if picked in q["options"] else "No answer"
            st.write(f"**Your answer:** {picked_text}")
            st.write(f"**Correct answer:** {correct}. {q['options'][correct]}")
            st.write(f"**Explanation:** {q['explanation']}")

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
    st.write("Continue practicing today by:")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Option A - Share to unlock**")
        invite_link = f"https://wa.me/?text=Practice free JAMB/WAEC questions with AI: {SITE_URL}"
        st.link_button("Invite 3 friends", invite_link, use_container_width=True)
        if st.button("I've shared - unlock now", use_container_width=True):
            st.session_state.unlocked = True
            st.rerun()
    with col2:
        st.markdown("**Option B - Go Advanced**")
        st.write(f"{ADVANCED_MIN_QUESTIONS}-{ADVANCED_MAX_QUESTIONS} Qs, no daily limit.")
        st.caption("See the sidebar 🔑 Advanced Access panel to purchase a license key.")

    st.caption("Free daily questions reset tomorrow either way.")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    init_state()
    render_header()
    render_advanced_access_sidebar()

    if not st.session_state.quiz_started:
        render_setup_screen()
    elif st.session_state.quiz_finished:
        render_results_screen()
    else:
        render_quiz_screen()

    render_footer()


if __name__ == "__main__":
    main()