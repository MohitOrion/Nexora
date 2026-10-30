
import json
import re

from ai.gemma_client import generate_text


def extract_opportunity(text: str) -> dict:
    """
    Extract structured scholarship, internship, or other
    opportunity information from raw text using Gemma.
    """

    if not text or not text.strip():
        raise ValueError("Opportunity text cannot be empty.")

    prompt = f"""
Extract opportunity information from the text below.

Return ONLY valid JSON with these keys:
- title
- category: scholarship, internship, job, fellowship, or other
- organization
- description
- deadline
- eligibility:
    - minimum_marks
    - maximum_family_income
    - eligible_categories
    - eligible_courses
    - other_requirements
- required_documents
- source_uncertainties

Use null for unknown scalar values and empty lists
for unknown list values. Do not invent information.
Use YYYY-MM-DD for a deadline when its exact date is known.

Source text:
{text}
"""

    response = generate_text(prompt)

    if not response or not response.strip():
        raise RuntimeError("Gemma returned an empty response.")

    # Remove Markdown code fences if Gemma adds them.
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

    if category not in allowed_categories:
        raise ValueError("Opportunity category is invalid.")

    result["title"] = title.strip()

    # Ensure expected optional fields exist.
    result.setdefault("organization", None)
    result.setdefault("description", None)
    result.setdefault("deadline", None)
    result.setdefault("eligibility", {})
    result.setdefault("required_documents", [])
    result.setdefault("source_uncertainties", [])

    return result
