import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from matcher import build_matches, call_gemini

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "schemes.json"

st.set_page_config(
    page_title="ScholarMatch AI",
    page_icon="🎓",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main {
        padding-top: 1.5rem;
    }

    .hero {
        padding: 1.5rem 1.8rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #111827, #1f2937);
        color: white;
        margin-bottom: 1.2rem;
    }

    .hero h1 {
        margin-bottom: .3rem;
    }

    .match-card {
        padding: 1rem 1.1rem;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        margin: .7rem 0;
        background: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🎓 ScholarMatch AI</h1>
        <p>Find welfare schemes and scholarships that fit your student profile.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Hackathon demo: the database is a curated prototype. "
    "Always verify the current official guidelines before applying."
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    schemes = json.load(f)


# ---------------------------------------------------------
# STUDENT PROFILE
# ---------------------------------------------------------

st.sidebar.header("👤 Student Profile")

income = st.sidebar.slider(
    "Annual household income (₹ lakh)",
    min_value=0.5,
    max_value=20.0,
    value=2.5,
    step=0.5,
)

marks_12 = st.sidebar.slider(
    "Class 12 percentage",
    min_value=0,
    max_value=100,
    value=82,
    step=1,
)

year = st.sidebar.selectbox(
    "Current year of study",
    ["1st Year", "2nd Year", "3rd Year", "4th Year"],
)

course = st.sidebar.selectbox(
    "Course",
    [
        "B.E.",
        "B.Tech",
        "B.Sc",
        "B.Com",
        "B.A.",
        "Other",
        "Diploma",
        "M.E.",
        "M.Tech",
        "M.Sc",
    ],
)

state = st.sidebar.selectbox(
    "State",
    [
        "Tamil Nadu",
        "Kerala",
        "Karnataka",
        "Andhra Pradesh",
        "Telangana",
        "Maharashtra",
        "Delhi",
        "Other",
    ],
)

city = st.sidebar.text_input(
    "City",
    value="Chennai",
)

category = st.sidebar.selectbox(
    "Category",
    [
        "General",
        "SC",
        "ST",
        "OBC",
        "EBC",
        "DNT",
        "Other",
    ],
)

gender = st.sidebar.selectbox(
    "Gender",
    [
        "Male",
        "Female",
        "Other / Prefer not to say",
    ],
)

disability = st.sidebar.selectbox(
    "Person with benchmark disability?",
    [
        "No",
        "Yes",
    ],
)

exam = st.sidebar.selectbox(
    "Entrance / qualifying exam",
    [
        "None",
        "JEE Main",
        "SAEEE",
        "VITEEE",
        "NEET",
        "Other",
    ],
)

full_time = st.sidebar.checkbox(
    "Regular full-time programme",
    value=True,
)

st.sidebar.caption(
    "For the demo, use a fictional profile. Do not enter Aadhaar, bank details, "
    "passwords, or other sensitive information."
)


# ---------------------------------------------------------
# CREATE PROFILE
# ---------------------------------------------------------

profile = {
    "income_lakh": income,
    "marks_12": marks_12,
    "year": year,
    "course": course,
    "state": state,
    "city": city,
    "category": category,
    "gender": gender,
    "disability": disability == "Yes",
    "exam": exam,
    "full_time": full_time,
}


# ---------------------------------------------------------
# PROFILE SUMMARY
# ---------------------------------------------------------

st.subheader("1. Tell ScholarMatch about the student")

st.write(
    f"**Demo profile:** {year} • {course} • {state} • "
    f"₹{income:.1f} lakh household income • {marks_12}% in Class 12"
)


# ---------------------------------------------------------
# FIND MATCHES
# ---------------------------------------------------------

if st.button(
    "🔎 Find My Best Matches",
    type="primary",
    use_container_width=True,
):

    with st.spinner(
        "Checking eligibility rules and asking Gemini to rank the matches..."
    ):

        # Step 1:
        # Use transparent Python rules to remove clearly
        # incompatible scholarships.

        candidates = build_matches(
            profile,
            schemes,
        )

        # -------------------------------------------------
        # NO CANDIDATES
        # -------------------------------------------------

        if not candidates:

            st.warning(
                "No strong matches were found from the prototype database. "
                "Try changing the demo profile."
            )

        else:

            ai_matches = []
            fallback_used = False
            gemini_error = None

            # -------------------------------------------------
            # STEP 2:
            # ASK GEMINI TO RANK AND EXPLAIN
            # -------------------------------------------------

            try:

                ai_matches = call_gemini(
                    profile,
                    candidates,
                )

            except Exception as exc:

                fallback_used = True
                gemini_error = str(exc)

                # -------------------------------------------------
                # RULE-BASED FALLBACK
                # -------------------------------------------------

                ai_matches = []

                for candidate in candidates:

                    ai_matches.append(
                        {
                            "scheme_id": candidate["scheme_id"],
                            "score": 85,
                            "verdict": "Rule-based match",
                            "why": [
                                "Passed all hard eligibility rules.",
                                "The student profile fits the available criteria.",
                            ],
                            "action": (
                                "Verify the current official eligibility "
                                "requirements before applying."
                            ),
                        }
                    )

            # -------------------------------------------------
            # SHOW GEMINI STATUS
            # -------------------------------------------------

            if fallback_used:

                st.warning(
                    "⚠️ Gemini could not be reached, so ScholarMatch is "
                    "showing the rule-based fallback ranking."
                )

                with st.expander("🔧 Technical details"):

                    st.write(
                        "The application itself is working. "
                        "Gemini returned an error, so the deterministic "
                        "matching engine was used instead."
                    )

                    st.code(
                        gemini_error,
                        language="text",
                    )

            else:

                st.success(
                    "✨ Gemini successfully ranked and explained the matches."
                )


            # -------------------------------------------------
            # RESULTS
            # -------------------------------------------------

            st.subheader("2. Recommended opportunities")

            if fallback_used:

                st.caption(
                    "Ranking engine: Transparent rule-based fallback"
                )

            else:

                st.caption(
                    "Ranking engine: Gemini AI"
                )


            # -------------------------------------------------
            # DISPLAY EACH MATCH
            # -------------------------------------------------

            for match in ai_matches:

                scheme_info = next(
                    (
                        scheme
                        for scheme in candidates
                        if scheme["scheme_id"] == match["scheme_id"]
                    ),
                    None,
                )

                if not scheme_info:
                    continue


                with st.container():

                    st.markdown(
                        '<div class="match-card">',
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        f"### 🎓 {scheme_info['name']}"
                    )

                    score = int(
                        match.get(
                            "score",
                            0,
                        )
                    )

                    st.progress(
                        score / 100
                    )

                    st.markdown(
                        f"**Match score:** {score}/100"
                    )

                    st.markdown(
                        f"**Verdict:** {match.get('verdict', 'Potential match')}"
                    )

                    st.markdown(
                        f"**Provider:** {scheme_info['provider']}"
                    )

                    st.markdown(
                        "**Why it matched:**"
                    )

                    reasons = match.get(
                        "why",
                        [],
                    )

                    for reason in reasons:

                        st.markdown(
                            f"✅ {reason}"
                        )

                    st.markdown(
                        f"**💡 Next step:** "
                        f"{match.get('action', 'Verify the official guidelines.')}"
                    )

                    st.markdown(
                        f"**📍 Location relevance:** "
                        f"{scheme_info.get('location_relevance', 'India-wide')}"
                    )

                    st.markdown(
                        f"**💰 Benefit:** "
                        f"{scheme_info.get('benefit', 'Check official source')}"
                    )

                    st.markdown(
                        f"**📅 Deadline:** "
                        f"{scheme_info.get('deadline', 'Check official source')}"
                    )

                    st.link_button(
                        "🌐 Open official source",
                        scheme_info.get("source_url") or scheme_info.get("link") or scheme_info.get("url") or "https://scholarships.gov.in",
                    )

                    st.markdown(
                        "</div>",
                        unsafe_allow_html=True,
                    )


# ---------------------------------------------------------
# HOW THE AI WORKS
# ---------------------------------------------------------

st.divider()

st.subheader(
    "💡 Why this is an AI project, not just a filter"
)

st.write(
    "ScholarMatch first uses transparent Python eligibility rules "
    "to remove obviously incompatible opportunities. Gemini then "
    "analyzes the remaining schemes, compares them with the student's "
    "profile, ranks the opportunities, assigns match scores, and "
    "explains the recommendations in plain language."
)

st.caption(
    "Important: Scholarship rules and deadlines can change. "
    "This prototype is for discovery and demonstration, "
    "not a final eligibility decision."
)
