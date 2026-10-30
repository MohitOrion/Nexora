
from ai.matcher import rank_opportunities
from ai.schemas import Opportunity, StudentProfile, EligibilityGates


STUDENT = StudentProfile(
    student_id="student-1",
    name="Test Student",
    college_tier="tier2",
    state_domicile="Delhi",
    degree="B.Tech",
    year_of_study=1,
    cgpa=8.0,
    family_income=300000,
    skills=["Python", "FastAPI"],
    resume_text="Python FastAPI backend development",
)


MATCHING_OPPORTUNITY = Opportunity(
    id="intern-1",
    title="Python Backend Intern",
    provider="Example Company",
    category="internship",
    description="Work on Python backend APIs with FastAPI",
    required_skills=["Python", "FastAPI"],
    gates=EligibilityGates(
        target_tier="any",
        allowed_states=["India"],
        eligible_courses=["B.Tech"],
        eligible_years=[1, 2],
        max_family_income=500000,
    ),
)


UNRELATED_OPPORTUNITY = Opportunity(
    id="job-1",
    title="Senior Java Engineer",
    provider="Example Company",
    category="internship",
    description="Senior Java and Spring Boot engineering",
    required_skills=["Java", "Spring Boot"],
    gates=EligibilityGates(
        target_tier="any",
        allowed_states=["India"],
        eligible_courses=["B.Tech"],
        eligible_years=[3, 4],
    ),
)


def test_matching_opportunity_is_returned():
    results = rank_opportunities(STUDENT, [MATCHING_OPPORTUNITY])

    titles = [item.opportunity.title for item in results]
    assert "Python Backend Intern" in titles


def test_matching_opportunity_is_ranked_first():
    results = rank_opportunities(
        STUDENT,
        [UNRELATED_OPPORTUNITY, MATCHING_OPPORTUNITY],
    )

    assert results
    assert results[0].opportunity.title == "Python Backend Intern"


def test_empty_opportunities_return_empty_list():
    assert rank_opportunities(STUDENT, []) == []


def test_inactive_opportunities_are_skipped():
    inactive = MATCHING_OPPORTUNITY.model_copy(
        update={"is_active": False}
    )

    results = rank_opportunities(STUDENT, [inactive])

    assert all(item.opportunity.id != inactive.id for item in results)


def test_ineligible_opportunity_is_not_eligible():
    results = rank_opportunities(STUDENT, [UNRELATED_OPPORTUNITY])

    assert results
    assert results[0].is_eligible is False
