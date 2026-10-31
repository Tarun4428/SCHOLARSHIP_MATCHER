import json
import os
import time
from google import genai
from google.genai import types
from typing_extensions import TypedDict


class Match(TypedDict):
    scheme_id: str
    score: int
    verdict: str
    why: list[str]
    action: str


def rule_match(profile, scheme):
    """
    Transparent first-pass eligibility filter.
    This removes schemes that clearly do not fit.
    It is not a final eligibility decision.
    """

    rules = scheme.get("rules", {})

    # Full-time requirement
    if rules.get("full_time_only") and not profile["full_time"]:
        return False

    # Year requirement
    allowed_years = rules.get("years")

    if allowed_years and profile["year"] not in allowed_years:
        return False

    # Income requirement
    max_income = rules.get("max_income_lakh")

    if max_income is not None:
        if profile["income_lakh"] > max_income:
            return False

    # Class 12 marks requirement
    min_marks = rules.get("min_marks_12")

    if min_marks is not None:
        if profile["marks_12"] < min_marks:
            return False

    # Course requirement
    allowed_courses = rules.get("courses")

    if allowed_courses and "Any" not in allowed_courses:
        if profile["course"] not in allowed_courses:
            return False

    # State requirement
    allowed_states = rules.get("states")

    if allowed_states and "All India" not in allowed_states:
        if profile["state"] not in allowed_states:
            return False

    # Category requirement
    categories = rules.get("categories")

    if categories and "Any" not in categories:
        if profile["category"] not in categories:
            return False

    # Disability requirement
    disability_required = rules.get("disability_required")

    if disability_required is True and not profile["disability"]:
        return False

    # Gender requirement
    gender_required = rules.get("gender_required")

    if gender_required:
        if profile["gender"] != gender_required:
            return False

    return True


def build_matches(profile, schemes):
    """
    Find schemes that pass the transparent eligibility filter.
    """

    candidates = []

    for scheme in schemes:

        if rule_match(profile, scheme):

            candidates.append(
                {
                    "scheme_id": scheme["id"],
                    "name": scheme["name"],
                    "provider": scheme["provider"],
                    "eligibility": scheme["eligibility"],
                    "benefit": scheme["benefit"],
                    "deadline": scheme["deadline"],
                    "location_relevance": scheme.get(
                        "location_relevance",
                        "India-wide",
                    ),
                    "source_url": scheme.get("source_url", ""),
                }
            )

    return candidates


def call_gemini(profile, candidates, max_retries=2):
    """
    Ask Gemini to rank the eligible candidates
    and explain why each one matches, with built-in retry logic for 503 errors.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    client = genai.Client(api_key=api_key,http_options=types.HttpOptions(timeout=30000),)

    prompt = f"""
You are ScholarMatch AI, an educational opportunity discovery assistant.

Your job is to rank scholarship and welfare opportunities
for a student.

IMPORTANT RULES:

1. Only rank schemes provided in the candidate list.
2. Do not invent scholarships.
3. Do not invent eligibility requirements.
4. Do not invent scholarship amounts.
5. Do not invent deadlines.
6. Use the eligibility information supplied for each scheme.
7. Give a score from 0 to 100.
8. Give 2 to 4 short reasons explaining the match.
9. Give one practical next step.
10. If information needs verification, clearly say so.
11. Return ONLY valid JSON.
12. Keep explanations short and easy for a student to understand.

STUDENT PROFILE:

{json.dumps(profile, indent=2)}

CANDIDATE SCHOLARSHIPS:

{json.dumps(candidates, indent=2)}

Return a JSON array.

Each object must contain exactly:

{{
    "scheme_id": "string",
    "score": 0,
    "verdict": "string",
    "why": ["reason 1", "reason 2"],
    "action": "string"
}}

Rank the strongest matches first.
"""

    # Retry loop to handle temporary 503 Service Unavailable spikes during demo
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",  # Using a reliable production flash model
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[Match],
                ),
            )

            if response and response.text:
                return json.loads(response.text)
                
        except Exception as e:
            # If it's the last attempt, raise the error so fallback handles it gracefully
            if attempt == max_retries - 1:
                raise RuntimeError(f"Gemini API failed after {max_retries} attempts: {str(e)}")
            
            # Wait with exponential backoff before retrying (2s, then 4s)
            time.sleep(2 * (attempt + 1))

    raise RuntimeError("Gemini returned an empty response.")
