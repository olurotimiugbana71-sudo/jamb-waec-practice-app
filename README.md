# ExamPrep AI

Free daily JAMB / WAEC / NECO CBT practice, graded instantly by AI.
Built with Streamlit + Google Gemini's free tier. Zero-cost to run and host.

## Project files

- `app.py` — the Streamlit page (run this one)
- `question_generator.py` — the AI prompt and API call
- `config.py` — constants and API key loading
- `requirements.txt` — dependencies
- `.env.example` — copy to `.env` and add your own key (never commit `.env`)

## Run locally

1. `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and paste in your free Gemini API key
   (get one at https://aistudio.google.com)
5. `streamlit run app.py`

## Deploy for free

Push this repo to GitHub, then connect it at https://share.streamlit.io
(Streamlit Community Cloud). Add `GEMINI_API_KEY` under the app's
**Secrets** settings — don't rely on the `.env` file once deployed.