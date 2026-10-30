import json
from unittest.mock import patch

import pytest

from ai.extractor import extract_opportunity


VALID_RESPONSE = {
    "title": "Python Backend Intern",
    "category": "internship",
    "organization": "Example Company",
    "description": "Work on backend APIs",
    "deadline": "2026-11-30",
    "start_date": None,
    "location": "India",
    "work_mode": "remote",
    "required_skills": ["Python", "FastAPI"],
    "eligible_degrees": ["BTech"],
    "eligible_years": ["1st year", "2nd year"],
    "eligibility": {
        "minimum_marks": None,
        "maximum_family_income": None,
        "eligible_categories": [],
        "eligible_courses": ["Computer Science"],
        "other_requirements": [],
    },
    "required_documents": ["Resume"],
    "source_uncertainties": [],
}


def test_extract_valid_opportunity():
    """A valid Gemma response should become a Python dictionary."""
    response = json.dumps(VALID_RESPONSE)

    with patch("ai.extractor.generate_text", return_value=response):
        result = extract_opportunity("Python internship for BTech students")

    assert result["title"] == "Python Backend Intern"
    assert result["category"] == "internship"
    assert result["organization"] == "Example Company"
    assert "Python" in result["required_skills"]


def test_empty_source_text_is_rejected():
    """Empty source text should not be sent to Gemma."""
    with pytest.raises(ValueError):
        extract_opportunity("")


def test_whitespace_source_text_is_rejected():
    """Text containing only spaces should be rejected."""
    with pytest.raises(ValueError):
        extract_opportunity("   \n   ")


def test_invalid_json_is_rejected():
    """Malformed JSON should raise a useful error."""
    with patch("ai.extractor.generate_text", return_value="not valid JSON"):
        with pytest.raises(ValueError):
            extract_opportunity("Python internship")


def test_non_object_response_is_rejected():
    """A JSON list is not a valid opportunity object."""
    with patch("ai.extractor.generate_text", return_value='["internship"]'):
        with pytest.raises(ValueError):
            extract_opportunity("Python internship")


def test_missing_title_is_rejected():
    """An opportunity must have a title."""
    response_data = VALID_RESPONSE.copy()
    response_data.pop("title")

    with patch(
        "ai.extractor.generate_text",
        return_value=json.dumps(response_data),
    ):
        with pytest.raises(ValueError):
            extract_opportunity("Python internship")


def test_invalid_category_is_rejected():
    """Only supported opportunity categories should be accepted."""
    response_data = VALID_RESPONSE.copy()
    response_data["category"] = "vacation"

    with patch(
        "ai.extractor.generate_text",
        return_value=json.dumps(response_data),
    ):
        with pytest.raises(ValueError):
            extract_opportunity("Python internship")


def test_category_is_normalized():
    """Category capitalization should be normalized."""
    response_data = VALID_RESPONSE.copy()
    response_data["category"] = "INTERNSHIP"

    with patch(
        "ai.extractor.generate_text",
        return_value=json.dumps(response_data),
    ):
        result = extract_opportunity("Python internship")

    assert result["category"] == "internship"


def test_missing_optional_fields_get_defaults():
    """Unknown optional information should not crash extraction."""
    response_data = {
        "title": "Python Intern",
        "category": "internship",
    }

    with patch(
        "ai.extractor.generate_text",
        return_value=json.dumps(response_data),
    ):
        result = extract_opportunity("Python internship")

    assert result["required_skills"] == []
    assert result["eligible_degrees"] == []
    assert result["eligibility"]["eligible_courses"] == []


def test_empty_gemma_response_is_rejected():
    """An empty response from Gemma should raise an error."""
    with patch("ai.extractor.generate_text", return_value=""):
        with pytest.raises((ValueError, RuntimeError)):
            extract_opportunity("Python internship")