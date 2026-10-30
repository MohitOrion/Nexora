
import json
import re

from ai.gemma_client import generate_text


def extract_opportunity(text: str) -> dict:
    """
    Extract structured opportunity information using Gemma.

    AI-extracted data is not independently verified.
    Unknown information must remain null or an empty list.
    """

    if not text or not text.strip():
        raise ValueError("Opportunity text cannot be empty.")

    prompt = f"""
Extract structured information from the opportunity source text.

Return ONLY one valid JSON object with exactly these fields:

- title: string
- category: scholarship, internship, job, fellowship, or other
- organization: string or null
- description: string or null
- deadline: YYYY-MM-DD or null
- start_date: YYYY-MM-DD or null
- location: string or null
- work_mode: remote, hybrid, onsite, or null
- duration_months: number or null
- stipend_monthly: number or null
- salary_annual: number or null
- minimum_experience_years: number or null
- required_skills: list of strings
- eligible_degrees: list of strings
- eligible_years: list of strings
- eligibility:
    - minimum_marks: number or null
    - maximum_family_income: number or null
    - eligible_categories: list of strings
    - eligible_courses: list of strings
    - other_requirements: list of strings
- required_documents: list of strings
- source_uncertainties: list of strings

Rules:
1. Do not invent details that are absent from the source.
2. Use null for unknown scalar values and [] for unknown lists.
3. Do not confuse an opportunity's category with a student's category.
4. Keep the application deadline and start date separate.
5. Convert stipend and salary to numbers only when the amount and period
   are clear. Monthly stipend must be monthly; annual salary must be annual.
6. Do not claim an opportunity is government-verified merely because
   the text says so. Record uncertainty if independent verification is absent.
7. If dates conflict or seem unusual, preserve the stated dates and explain
   the inconsistency in source_uncertainties.
8. Return valid JSON only, without Markdown code fences.

Source text:
{text}
"""

    response = generate_text(prompt)

    if not response or not response.strip():
        raise RuntimeError("Gemma returned an empty response.")

    cleaned = response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemma returned invalid JSON. Try again."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("Gemma response must be a JSON object.")

    title = result.get("title")
    category = result.get("category")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Opportunity title is missing.")

    allowed_categories = {
        "scholarship",
        "internship",
        "job",
        "fellowship",
        "other",
    }

    if not isinstance(category, str) or category.lower() not in allowed_categories:
        raise ValueError("Opportunity category is invalid.")

    result["title"] = title.strip()
    result["category"] = category.lower()

    # Ensure optional fields have consistent defaults.
    scalar_fields = [
        "organization",
        "description",
        "deadline",
        "start_date",
        "location",
        "work_mode",
        "duration_months",
        "stipend_monthly",
        "salary_annual",
        "minimum_experience_years",
    ]

    list_fields = [
        "required_skills",
        "eligible_degrees",
        "eligible_years",
        "required_documents",
        "source_uncertainties",
    ]

    for field in scalar_fields:
        result.setdefault(field, None)

    for field in list_fields:
        if not isinstance(result.get(field), list):
            result[field] = []

    eligibility = result.get("eligibility")
    if not isinstance(eligibility, dict):
        eligibility = {}

    eligibility.setdefault("minimum_marks", None)
    eligibility.setdefault("maximum_family_income", None)
    eligibility.setdefault("eligible_categories", [])
    eligibility.setdefault("eligible_courses", [])
    eligibility.setdefault("other_requirements", [])

    for field in ["eligible_categories", "eligible_courses", "other_requirements"]:
        if not isinstance(eligibility[field], list):
            eligibility[field] = []

    result["eligibility"] = eligibility

    return result
