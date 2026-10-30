"""Structured opportunity and eligibility gate extractor for aventra one.

Uses Gemini 2.5 Flash / Gemma to parse raw markdown, circular PDFs, and web DOM
into deterministic Pydantic Opportunity schemas.
"""

from __future__ import annotations

import re
import uuid

try:
    from .gemma_client import GemmaClient
    from .prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_PROMPT
    from .resume_parser import INDIAN_STATES, extract_text_from_pdf
    from .schemas import CollegeTier, EligibilityGates, Opportunity, OpportunityCategory
except ImportError:  # pragma: no cover - supports direct script execution
    from gemma_client import GemmaClient
    from prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_PROMPT
    from resume_parser import INDIAN_STATES, extract_text_from_pdf
    from schemas import CollegeTier, EligibilityGates, Opportunity, OpportunityCategory


class OpportunityExtractor:
    def __init__(self, client: GemmaClient | None = None):
        self.client = client or GemmaClient()

    def extract_from_text(self, text: str, source_url: str = "") -> Opportunity:
        """Extract deterministic opportunity schema from raw text."""
        prompt = EXTRACTION_USER_PROMPT.format(source_url=source_url, raw_text=text[:8000])
        parsed_json = self.client.generate_json(prompt, system_instruction=EXTRACTION_SYSTEM_PROMPT)

        if not parsed_json or "error" in parsed_json:
            return self._heuristic_fallback(text, source_url)

        gates_dict = parsed_json.get("gates", {})
        gates = EligibilityGates(
            max_family_income=gates_dict.get("max_family_income"),
            min_cgpa=gates_dict.get("min_cgpa"),
            allowed_states=gates_dict.get("allowed_states", []),
            eligible_courses=gates_dict.get("eligible_courses", []),
            eligible_years=gates_dict.get("eligible_years", []),
            target_tier=gates_dict.get("target_tier", CollegeTier.ANY.value),
            min_nirf_rank=gates_dict.get("min_nirf_rank"),
            is_full_tuition_grant=gates_dict.get("is_full_tuition_grant", False),
            is_stackable=gates_dict.get("is_stackable", True),
            conflict_notes=gates_dict.get("conflict_notes")
        )

        return Opportunity(
            id=f"opp_{uuid.uuid4().hex[:8]}",
            title=parsed_json.get("title", "Verified Opportunity"),
            provider=parsed_json.get("provider", "Direct Ingestion"),
            category=parsed_json.get("category", OpportunityCategory.SCHOLARSHIP.value),
            description=parsed_json.get("description", ""),
            deadline=parsed_json.get("deadline"),
            apply_url=parsed_json.get("apply_url") or source_url,
            is_active=parsed_json.get("is_active", True),
            required_skills=parsed_json.get("required_skills", []),
            gates=gates,
            raw_text=text[:1000]
        )

    def extract_from_pdf(self, pdf_path: str, source_url: str = "") -> Opportunity:
        """Extract opportunity from multi-page PDF notification or circular."""
        text = extract_text_from_pdf(pdf_path)
        return self.extract_from_text(text, source_url=source_url)

    def _heuristic_fallback(self, text: str, source_url: str) -> Opportunity:
        """Regex-based deterministic extraction when LLM is offline."""
        title = "National Merit & State MCM Scholarship"
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        if len(first_line) > 5 and len(first_line) < 100:
            title = first_line

        # Income cap e.g. ₹6 Lakh or ₹8,00,000
        max_income = None
        inc_match = re.search(r"(?:income|cap)\s*[:=-]?\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|lpa|inr)?", text, re.IGNORECASE)
        if inc_match:
            try:
                val = float(inc_match.group(1).replace(",", ""))
                max_income = val * 100000.0 if val < 100 else val
            except ValueError:
                pass

        # CGPA cutoff
        min_cgpa = None
        cgpa_match = re.search(r"(?:cgpa|gpa|cutoff)\s*[:=-]?\s*(\d(?:\.\d+)?)", text, re.IGNORECASE)
        if cgpa_match:
            try:
                min_cgpa = float(cgpa_match.group(1))
            except ValueError:
                pass

        # Domicile state
        allowed_states = []
        for state in INDIAN_STATES:
            if re.search(r"\b" + re.escape(state) + r"\b", text, re.IGNORECASE):
                allowed_states.append(state)

        # Full tuition vs stackable perk
        is_full_tuition = bool(re.search(r"full\s*tuition|100%\s*fee\s*reimbursement|tuition\s*waiver", text, re.IGNORECASE))
        is_stackable = not is_full_tuition or bool(re.search(r"credit|cloud|perk|swag|hackathon", text, re.IGNORECASE))

        return Opportunity(
            id=f"opp_{uuid.uuid4().hex[:8]}",
            title=title,
            provider="e-District Delhi" if "delhi" in text.lower() else "National Portal",
            category=OpportunityCategory.SCHOLARSHIP.value if is_full_tuition else OpportunityCategory.HACKATHON.value,
            description="Extracted opportunity with deterministic eligibility gates.",
            deadline="2026-11-30T23:59:59Z",
            apply_url=source_url or "https://edistrict.delhigovt.nic.in",
            is_active=True,
            required_skills=["Python", "Web Development"] if not is_full_tuition else [],
            gates=EligibilityGates(
                max_family_income=max_income or 600000.0,
                min_cgpa=min_cgpa or 7.0,
                allowed_states=allowed_states,
                eligible_courses=["B.Tech", "MCA", "B.E."],
                eligible_years=[1, 2, 3, 4],
                target_tier=CollegeTier.ANY.value,
                is_full_tuition_grant=is_full_tuition,
                is_stackable=is_stackable,
                conflict_notes="Exclusive grant" if is_full_tuition else None
            ),
            raw_text=text[:1000]
        )
