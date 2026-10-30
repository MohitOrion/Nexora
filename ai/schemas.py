"""Pydantic and dataclass-compatible schemas for aventra.

Covers Opportunities, Eligibility Gates, Student Profiles, Match Results,
and Policy Conflict information.
"""

from __future__ import annotations

import builtins
import json
from enum import Enum
from typing import Any

try:
    from pydantic import BaseModel
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    # Lightweight fallback compatible with Pydantic BaseModel interface
    class BaseModel:
        def __init__(self, **data: Any):
            for k, v in data.items():
                setattr(self, k, v)

        def model_dump(self) -> builtins.dict[str, Any]:
            res = {}
            for k, v in self.__dict__.items():
                if hasattr(v, "model_dump"):
                    res[k] = v.model_dump()
                elif isinstance(v, list):
                    res[k] = [i.model_dump() if hasattr(i, "model_dump") else i for i in v]
                else:
                    res[k] = v
            return res

        def dict(self) -> builtins.dict[str, Any]:
            return self.model_dump()

        def model_dump_json(self) -> str:
            return json.dumps(self.model_dump(), default=str)


class OpportunityCategory(str, Enum):
    SCHOLARSHIP = "scholarship"
    HACKATHON = "hackathon"
    INTERNSHIP = "internship"
    CLOUD_CREDIT = "cloud_credit"
    DEV_PERK = "dev_perk"


class CollegeTier(str, Enum):
    TIER_1 = "tier1"
    TIER_2 = "tier2"
    TIER_3 = "tier3"
    ANY = "any"


class EligibilityGates(BaseModel):
    max_family_income: float | None = None  # in INR e.g. 600000 or 800000
    min_cgpa: float | None = None
    allowed_states: list[str] = []  # e.g. ["Delhi"] or empty for Pan-India  # noqa: RUF012
    eligible_courses: list[str] = []  # e.g. ["B.Tech", "MCA", "B.Sc"]  # noqa: RUF012
    eligible_years: list[int] = []  # e.g. [1, 2, 3, 4]  # noqa: RUF012
    gender_restriction: str | None = None  # e.g. "female" or None
    min_nirf_rank: int | None = None
    target_tier: str = CollegeTier.ANY.value
    is_full_tuition_grant: bool = False  # e.g. Bharti Airtel, Delhi MCM
    is_stackable: bool = True  # e.g. Google Gemini, Adobe CC
    conflict_notes: str | None = None


class Opportunity(BaseModel):
    id: str
    title: str
    provider: str  # Unstop, Devfolio, Buddy4Study, e-District Delhi, etc.
    category: str = OpportunityCategory.SCHOLARSHIP.value
    description: str = ""
    deadline: str | None = None  # ISO format string e.g. 2026-11-15T23:59:59Z
    apply_url: str = ""
    is_active: bool = True  # TinyFish button health verified
    required_skills: list[str] = []  # noqa: RUF012
    gates: EligibilityGates = EligibilityGates()
    embedding: list[float] | None = None
    raw_text: str | None = ""


class StudentProfile(BaseModel):
    student_id: str
    name: str = ""
    college: str = ""
    college_tier: str = CollegeTier.TIER_2.value
    nirf_rank: int | None = None
    state_domicile: str = "Delhi"
    degree: str = "B.Tech"
    year_of_study: int = 3
    cgpa: float = 8.0
    family_income: float = 500000.0  # in INR
    skills: list[str] = []  # noqa: RUF012
    current_grants: list[str] = []  # Existing active grants  # noqa: RUF012
    resume_text: str | None = ""
    embedding: list[float] | None = None


class MatchBreakdown(BaseModel):
    # 4-factor scoring: Score = 35*Academic + 25*Domicile + 25*Skills + 15*Gates
    academic_score: float = 0.0  # max 35
    domicile_score: float = 0.0  # max 25
    skills_score: float = 0.0    # max 25
    gates_score: float = 0.0     # max 15
    total_score: float = 0.0     # max 100
    passed_gates: bool = True
    gate_failures: list[str] = []  # noqa: RUF012
    conflict_detected: bool = False
    conflict_reason: str | None = None


class MatchResult(BaseModel):
    opportunity: Opportunity
    breakdown: MatchBreakdown
    is_eligible: bool = True
    recommended: bool = True
