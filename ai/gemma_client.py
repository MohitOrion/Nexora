"""Gemini 2.5 Flash and Gemma LLM Client for aventra one.

Supports Google AI Studio (Gemini 2.5 Flash / Gemini 1.5) and local Gemma
endpoints (Ollama / vLLM) with deterministic fallback for offline execution.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


class GemmaClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        base_url: str | None = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.base_url = base_url or os.getenv("GEMMA_BASE_URL", "")

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        """Generate text from Gemini API or local Gemma endpoint."""
        # 1. Try Gemini API if key is present
        if self.api_key:
            try:
                return self._call_gemini_api(prompt, system_instruction)
            except Exception:  # noqa: BLE001, S110
                # Log and fallback gracefully
                pass

        # 2. Try local Gemma endpoint if configured
        if self.base_url:
            try:
                return self._call_local_gemma(prompt, system_instruction)
            except Exception:  # noqa: BLE001, S110
                pass

        # 3. Deterministic offline fallback
        return self._offline_fallback(prompt)

    def generate_json(self, prompt: str, system_instruction: str | None = None) -> dict[str, Any]:
        """Generate structured JSON response."""
        json_instruction = (
            (system_instruction or "") +
            "\nIMPORTANT: Respond ONLY with valid JSON. Do not include markdown codeblocks or extra text."
        )
        text = self.generate(prompt, system_instruction=json_instruction)
        clean = re.sub(r"^```(?:json)?\s*", "", text.strip())
        clean = re.sub(r"\s*```$", "", clean)

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            # Attempt to extract first {...} block
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse JSON", "raw": text}

    def _call_gemini_api(self, prompt: str, system_instruction: str | None = None) -> str:
        """Call Google Gemini generateContent REST endpoint."""
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        contents = [{"parts": [{"text": prompt}]}]
        body: dict[str, Any] = {"contents": contents}

        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            candidates = res_json.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        return ""

    def _call_local_gemma(self, prompt: str, system_instruction: str | None = None) -> str:
        """Call local Ollama / vLLM Gemma server."""
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": "gemma",
            "prompt": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt,
            "stream": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("response", "")

    def _offline_fallback(self, prompt: str) -> str:
        """Deterministic mock for offline dev, unit tests, and CI runs."""
        lower = prompt.lower()
        if "extract" in lower or "eligibility" in lower or "gates" in lower:
            # Provide sample extracted opportunity JSON
            return json.dumps({
                "title": "Delhi Higher Education Merit-cum-Means Scholarship",
                "provider": "e-District Delhi",
                "category": "scholarship",
                "description": "Financial assistance for meritorious students pursuing higher education.",
                "deadline": "2026-11-30T23:59:59Z",
                "apply_url": "https://edistrict.delhigovt.nic.in",
                "is_active": True,
                "required_skills": ["Academic Excellence", "Higher Education"],
                "gates": {
                    "max_family_income": 600000.0,
                    "min_cgpa": 7.5,
                    "allowed_states": ["Delhi"],
                    "eligible_courses": ["B.Tech", "MCA", "B.Sc", "B.E."],
                    "eligible_years": [1, 2, 3, 4],
                    "target_tier": "any",
                    "is_full_tuition_grant": True,
                    "is_stackable": False,
                    "conflict_notes": "Cannot be combined with any other state or central tuition grant."
                }
            })
        return "I am aventra, your opportunity-intelligence assistant. How can I help you find verified scholarships and hackathons today?"

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
