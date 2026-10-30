
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Find the Nexora project root and load backend/.env.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / "backend" / ".env"

load_dotenv(ENV_FILE)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemma-4-26b-a4b-it"


def generate_text(prompt: str) -> str:
    """Send a prompt to Gemma and return its text response."""

    if not API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from backend/.env"
        )

    client = genai.Client(api_key=API_KEY)

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
    except errors.APIError as exc:
        # Show the provider's error instead of hiding its details.
        raise RuntimeError(
            f"Gemma API error (code={exc.code}): {exc.message}"
        ) from exc

    answer = response.text

    if not answer or not answer.strip():
        raise RuntimeError("Gemma returned an empty response.")

    return answer.strip()
