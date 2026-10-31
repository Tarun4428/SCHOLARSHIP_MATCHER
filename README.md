# ScholarMatch AI

A Streamlit hackathon prototype for matching students with welfare schemes and scholarships.

## Stack
- Python
- Streamlit
- Google Gemini API (`google-genai`)
- JSON prototype database

## Run
1. Create a virtual environment.
2. Install `requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Put your Gemini API key in `.env`.
5. Run `streamlit run app.py`.

The prototype uses a transparent rule-based first pass, then Gemini to rank and explain candidate matches.

IMPORTANT: Scholarship data changes. Verify current eligibility, dates, amounts, and required documents on the official provider/NSP page before applying.
