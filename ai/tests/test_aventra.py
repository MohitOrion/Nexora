"""Comprehensive test suite for IRIS one AI modules.

Tests:
1. Schemas serialization and validation.
2. Fast Resume parsing (<50ms).
3. Vector embeddings & SQLite WAL cache.
4. Gemini 2.5 Flash / heuristic extraction.
5. 4-factor match engine (35 + 25 + 25 + 15 = 100).
6. Policy Conflict Shield & RFC 5545 Calendar generation (72h & 24h alarms).
7. Ask Iris RAG Assistant.
"""

import os
import sys
import time

# Ensure the workspace root and ai package are importable when running from repo or package contexts.
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Nexora.ai.aventra import AskIrisAssistant
from Nexora.ai.conflict_shield import PolicyConflictShield, generate_ics_calendar
from Nexora.ai.embeddings import VectorCache, cosine_similarity, get_embedding
from Nexora.ai.extractor import OpportunityExtractor
from Nexora.ai.matcher import calculate_match
from Nexora.ai.resume_parser import parse_resume
from Nexora.ai.schemas import (
    CollegeTier,
    EligibilityGates,
    Opportunity,
    OpportunityCategory,
    StudentProfile,
)


def test_resume_parser():
    print("[1/7] Testing Resume Parser...")
    sample_resume = """
    Priya Verma
    Netaji Subhas University of Technology (NSUT)
    B.Tech in Information Technology - 3rd Year
    CGPA: 9.15
    Domicile: Delhi
    Annual Family Income: ₹4,50,000
    Technical Skills: Python, FastAPI, React, Docker, PostgreSQL, Machine Learning, Git
    """
    start_t = time.perf_counter()
    profile = parse_resume(sample_resume)
    duration_ms = (time.perf_counter() - start_t) * 1000.0

    assert profile.name == "Priya Verma", f"Expected Priya Verma, got {profile.name}"
    assert profile.cgpa == 9.15, f"Expected 9.15, got {profile.cgpa}"
    assert profile.college_tier == CollegeTier.TIER_1.value
    assert profile.state_domicile == "Delhi"
    assert profile.year_of_study == 3
    assert profile.degree == "B.Tech"
    assert profile.family_income == 450000.0
    assert "Python" in profile.skills
    assert "Fastapi" in profile.skills or "FastAPI" in profile.skills
    assert duration_ms < 50.0, f"Parsing took {duration_ms:.2f}ms, expected < 50ms"
    print(f"  -> Resume parsed in {duration_ms:.2f}ms (< 50ms). Profile valid.")


def test_embeddings_and_cache():
    print("[2/7] Testing Vector Embeddings and SQLite WAL Cache...")
    v1 = get_embedding("Python FastAPI Machine Learning Docker")
    v2 = get_embedding("Python FastAPI PyTorch AI")
    v3 = get_embedding("Culinary arts cooking baking pastry")

    sim_high = cosine_similarity(v1, v2)
    sim_low = cosine_similarity(v1, v3)

    assert sim_high > sim_low, f"Expected {sim_high} > {sim_low}"

    # Test SQLite WAL cache
    cache = VectorCache(db_path=":memory:")
    cache.store("test_1", "Delhi MCM", "scholarship", "Delhi merit scholarship", v1)
    retrieved = cache.get_embedding("test_1")
    assert retrieved is not None
    assert len(retrieved) == len(v1)
    print("  -> Vector embeddings and cache verified.")


def test_extractor():
    print("[3/7] Testing Opportunity Extractor...")
    extractor = OpportunityExtractor()
    raw_circular = """
    Delhi Higher Education Merit-cum-Means (MCM) Scholarship 2026
    Eligibility: Annual family income must not exceed ₹6,00,000.
    Minimum CGPA required is 7.5.
    Must be a resident of Delhi pursuing B.Tech, MCA or approved degrees.
    Full tuition fee reimbursement for Category 1 students.
    Deadline: 2026-11-30. Apply at https://edistrict.delhigovt.nic.in
    """
    opp = extractor.extract_from_text(
        raw_circular, source_url="https://edistrict.delhigovt.nic.in"
    )
    assert opp.gates.max_family_income == 600000.0
    assert opp.gates.min_cgpa == 7.5
    assert "Delhi" in opp.gates.allowed_states
    assert opp.gates.is_full_tuition_grant is True
    print("  -> Extraction passed with deterministic gates.")


def test_4_factor_matcher():
    print("[4/7] Testing 4-Factor Match Engine (35 + 25 + 25 + 15 = 100)...")
    student = StudentProfile(
        student_id="stu_001",
        name="Priya Verma",
        college="NSUT Delhi",
        college_tier=CollegeTier.TIER_1.value,
        state_domicile="Delhi",
        degree="B.Tech",
        year_of_study=3,
        cgpa=9.0,
        family_income=500000.0,
        skills=["Python", "React", "FastAPI", "Docker", "PostgreSQL"],
        current_grants=[],
    )

    opp = Opportunity(
        id="opp_delhi_mcm",
        title="Delhi MCM Scholarship",
        provider="e-District Delhi",
        category=OpportunityCategory.SCHOLARSHIP.value,
        is_active=True,
        required_skills=[],  # General scholarship
        gates=EligibilityGates(
            max_family_income=600000.0,
            min_cgpa=8.0,
            allowed_states=["Delhi"],
            eligible_courses=["B.Tech"],
            eligible_years=[1, 2, 3, 4],
            target_tier=CollegeTier.TIER_1.value,
            is_full_tuition_grant=True,
            is_stackable=False,
        ),
    )

    res = calculate_match(student, opp)
    b = res.breakdown

    assert b.academic_score == 35.0, f"Expected 35.0, got {b.academic_score}"
    assert b.domicile_score == 25.0, f"Expected 25.0, got {b.domicile_score}"
    assert b.skills_score == 25.0, f"Expected 25.0, got {b.skills_score}"
    assert b.gates_score == 15.0, f"Expected 15.0, got {b.gates_score}"
    assert b.total_score == 100.0, f"Expected 100.0, got {b.total_score}"
    assert b.passed_gates is True
    assert res.is_eligible is True
    print("  -> 4-Factor Match Engine validated at 100.0/100 score.")


def test_policy_conflict_shield():
    print("[5/7] Testing Policy Conflict Shield...")
    student_with_airtel = StudentProfile(
        student_id="stu_002",
        name="Rohan Gupta",
        state_domicile="Delhi",
        current_grants=["Bharti Airtel Scholarship"],
    )

    conflicting_opp = Opportunity(
        id="opp_delhi_mcm",
        title="Delhi Merit-cum-Means Fee Reimbursement",
        provider="e-District Delhi",
        gates=EligibilityGates(is_full_tuition_grant=True, is_stackable=False),
    )

    has_conflict, reason = PolicyConflictShield.check_conflict(
        student_with_airtel, conflicting_opp
    )
    assert has_conflict is True, (
        "Expected conflict detection between Airtel & Delhi MCM"
    )
    assert "Policy Conflict Detected" in reason

    stackable_perk = Opportunity(
        id="opp_gemini_credits",
        title="Google Gemini API Student Developer Credits",
        provider="Google",
        category=OpportunityCategory.CLOUD_CREDIT.value,
        gates=EligibilityGates(is_full_tuition_grant=False, is_stackable=True),
    )

    perk_conflict, _ = PolicyConflictShield.check_conflict(
        student_with_airtel, stackable_perk
    )
    assert perk_conflict is False, "Dev perks must remain 100% stackable"
    print("  -> Dual-tuition grant clash detected; stackable perks permitted.")


def test_calendar_sync():
    print("[6/7] Testing RFC 5545 .ics Calendar Sync with 72h & 24h Alarms...")
    opp = Opportunity(
        id="opp_hackathon_01",
        title="National Innovation Hackathon 2026",
        provider="Devfolio",
        deadline="2026-11-20T18:00:00Z",
        apply_url="https://devfolio.co/hackathon",
    )
    ics = generate_ics_calendar(opp)

    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "TRIGGER:-PT72H" in ics, "Missing 72h alarm"
    assert "TRIGGER:-PT24H" in ics, "Missing 24h alarm"
    assert "END:VCALENDAR" in ics
    print("  -> RFC 5545 calendar generated with automated 72h & 24h alarms.")


def test_ask_iris():
    print("[7/7] Testing Ask Iris Assistant...")
    assistant = AskIrisAssistant()
    student = StudentProfile(
        student_id="stu_003",
        name="Sneha Rao",
        college="DTU",
        state_domicile="Delhi",
        cgpa=9.2,
        current_grants=["Bharti Airtel Scholarship"],
    )

    opps = [
        Opportunity(
            id="opp_1",
            title="Delhi MCM Scholarship",
            provider="e-District Delhi",
            deadline="2026-11-25T23:59:59Z",
            gates=EligibilityGates(
                allowed_states=["Delhi"], is_full_tuition_grant=True, is_stackable=False
            ),
        ),
        Opportunity(
            id="opp_2",
            title="Google Gemini Cloud Credits",
            provider="Google",
            gates=EligibilityGates(is_stackable=True),
        ),
    ]

    res = assistant.generate_response("Can I apply for Delhi MCM?", student, opps)
    assert "response" in res
    assert len(res["conflicts"]) > 0, "Expected policy conflict warning in response"
    print("  -> Ask Iris generated context-aware guidance with conflict warnings.")


if __name__ == "__main__":
    test_resume_parser()
    test_embeddings_and_cache()
    test_extractor()
    test_4_factor_matcher()
    test_policy_conflict_shield()
    test_calendar_sync()
    test_ask_iris()
    print("\nALL 7 IRIS ONE SUITES PASSED SUCCESSFULLY!")
