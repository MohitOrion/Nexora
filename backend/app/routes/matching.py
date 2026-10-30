
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.opportunity import Opportunity

router = APIRouter(
    prefix="/matching",
    tags=["Eligibility Matching"],
)


# --------------------------------------------------
# Request models
# --------------------------------------------------

class UserProfile(BaseModel):
    course: str = Field(min_length=1)
    marks_percentage: float | None = Field(default=None, ge=0, le=100)
    annual_family_income: float | None = Field(default=None, ge=0)
    category: str | None = None


class GeneralUserProfile(BaseModel):
    category: Literal[
        "scholarship", "internship", "job", "fellowship"
    ]

    course: str | None = None
    marks_percentage: float | None = Field(default=None, ge=0, le=100)
    annual_family_income: float | None = Field(default=None, ge=0)
    student_category: str | None = None

    skills: list[str] = Field(default_factory=list)
    degree: str | None = None
    year_of_study: str | None = None
    location: str | None = None
    work_mode: str | None = None
    expected_stipend: float | None = Field(default=None, ge=0)
    experience_years: float | None = Field(default=None, ge=0)
    expected_salary: float | None = Field(default=None, ge=0)
    research_interests: list[str] = Field(default_factory=list)


# --------------------------------------------------
# Shared helpers
# --------------------------------------------------

def get_eligibility_data(opportunity: Opportunity) -> dict:
    data = opportunity.eligibility or {}
    return data if isinstance(data, dict) else {}


def determine_status(mismatches: list, missing_information: list) -> str:
    if mismatches:
        return "possible_mismatch"
    if missing_information:
        return "needs_more_information"
    return "potential_match"


def normalize(value: str | None) -> str:
    return (value or "").strip().casefold()


def as_list(value) -> list:
    return value if isinstance(value, list) else []


def contains_match(user_value: str, requirements: list) -> bool:
    """Use a conservative case-insensitive partial text match."""
    user_value = normalize(user_value)

    if not user_value:
        return False

    return any(
        user_value == normalize(str(item))
        or user_value in normalize(str(item))
        or normalize(str(item)) in user_value
        for item in requirements
        if str(item).strip()
    )


def category_matches_requirement(
    user_value: str,
    requirements: list,
) -> bool:
    return normalize(user_value) in {
        normalize(str(item)) for item in requirements
    }


def compare_text_requirement(
    user_value: str | None,
    requirements: list,
    label: str,
    reasons: list,
    mismatches: list,
    missing_information: list,
):
    """Compare a profile value with a structured list of requirements."""
    requirements = [
        str(item).strip()
        for item in requirements
        if str(item).strip()
    ]

    if not requirements:
        missing_information.append(
            f"{label} requirements are not specified in the listing"
        )
    elif not user_value:
        missing_information.append(f"Your {label.lower()} is needed")
    elif contains_match(user_value, requirements):
        reasons.append(f"{label} appears to match")
    else:
        mismatches.append(f"{label} may not meet the listed requirement")


# --------------------------------------------------
# Scholarship matching helpers
# --------------------------------------------------

def match_scholarship_requirements(
    profile,
    opportunity: Opportunity,
    reasons: list,
    mismatches: list,
    missing_information: list,
    student_category: str | None = None,
):
    eligibility = get_eligibility_data(opportunity)

    # Course
    eligible_courses = as_list(eligibility.get("eligible_courses"))

    if eligible_courses:
        if not profile.course:
            missing_information.append("Your course is needed")
        elif contains_match(profile.course, eligible_courses):
            reasons.append("Course appears to match")
        else:
            mismatches.append("Course may not match the eligible courses")
    else:
        missing_information.append("Eligible courses are not specified")

    # Marks
    minimum_marks = eligibility.get("minimum_marks")

    if minimum_marks is not None:
        try:
            minimum_marks = float(minimum_marks)

            if profile.marks_percentage is None:
                missing_information.append("Your marks percentage is needed")
            elif profile.marks_percentage >= minimum_marks:
                reasons.append("Marks meet the listed minimum")
            else:
                mismatches.append("Marks are below the listed minimum")
        except (TypeError, ValueError):
            missing_information.append("Minimum marks need verification")

    # Family income
    maximum_income = eligibility.get("maximum_family_income")

    if maximum_income is not None:
        try:
            maximum_income = float(maximum_income)

            if profile.annual_family_income is None:
                missing_information.append("Annual family income is needed")
            elif profile.annual_family_income <= maximum_income:
                reasons.append("Family income meets the listed limit")
            else:
                mismatches.append("Family income exceeds the listed limit")
        except (TypeError, ValueError):
            missing_information.append("Income limit needs verification")

    # Student category: uncertain extracted categories are not automatic rejections.
    eligible_categories = as_list(
        eligibility.get("eligible_categories")
    )

    if eligible_categories:
        if not student_category:
            missing_information.append("Your student category is needed")
        elif category_matches_requirement(
            student_category, eligible_categories
        ):
            reasons.append("Student category appears to match")
        else:
            missing_information.append(
                "Student category requirements need verification"
            )


# --------------------------------------------------
# Existing scholarship endpoint (preserved)
# --------------------------------------------------

@router.post("/scholarships")
def match_scholarships(
    profile: UserProfile,
    db: Session = Depends(get_db),
):
    try:
        scholarships = (
            db.query(Opportunity)
            .filter(Opportunity.category.ilike("scholarship"))
            .all()
        )

        results = []

        for scholarship in scholarships:
            reasons = []
            mismatches = []
            missing_information = []

            match_scholarship_requirements(
                profile,
                scholarship,
                reasons,
                mismatches,
                missing_information,
                student_category=profile.category,
            )

            results.append({
                "id": scholarship.id,
                "title": scholarship.title,
                "organization": scholarship.organization,
                "deadline": scholarship.deadline,
                "source_url": scholarship.source_url,
                "verified": scholarship.verified,
                "match_status": determine_status(
                    mismatches, missing_information
                ),
                "matching_reasons": reasons,
                "mismatches": mismatches,
                "missing_information": missing_information,
            })

        return {
            "message": "Matching completed",
            "total_scholarships_checked": len(scholarships),
            "results": results,
            "note": (
                "Preliminary matching only. Verify the official "
                "scholarship rules before applying."
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to match scholarships.",
        ) from exc


# --------------------------------------------------
# General matching: scholarships, internships, jobs,
# and fellowships
# --------------------------------------------------

@router.post("/opportunities")
def match_opportunities(
    profile: GeneralUserProfile,
    db: Session = Depends(get_db),
):
    try:
        opportunities = (
            db.query(Opportunity)
            .filter(Opportunity.category.ilike(profile.category))
            .all()
        )

        results = []

        for opportunity in opportunities:
            reasons = []
            mismatches = []
            missing_information = []
            eligibility = get_eligibility_data(opportunity)

            if profile.category == "scholarship":
                match_scholarship_requirements(
                    profile,
                    opportunity,
                    reasons,
                    mismatches,
                    missing_information,
                    student_category=profile.student_category,
                )

            else:
                # Skills: use structured requirements first.
                required_skills = as_list(opportunity.required_skills)

                if required_skills:
                    if not profile.skills:
                        missing_information.append(
                            "Add your skills to assess this opportunity"
                        )
                    else:
                        matched_skills = [
                            skill for skill in profile.skills
                            if contains_match(skill, required_skills)
                        ]

                        if matched_skills:
                            reasons.append(
                                "Matching skills: "
                                + ", ".join(matched_skills)
                            )
                        else:
                            missing_information.append(
                                "None of your skills matched the listed skills"
                            )
                else:
                    missing_information.append(
                        "Required skills are not specified in the listing"
                    )

                # Degree
                compare_text_requirement(
                    profile.degree,
                    as_list(opportunity.eligible_degrees),
                    "Degree",
                    reasons,
                    mismatches,
                    missing_information,
                )

                # Year of study
                compare_text_requirement(
                    profile.year_of_study,
                    as_list(opportunity.eligible_years),
                    "Year of study",
                    reasons,
                    mismatches,
                    missing_information,
                )

                # Location
                listing_location = opportunity.location

                if profile.location:
                    if not listing_location:
                        missing_information.append(
                            "Opportunity location is not specified"
                        )
                    elif (
                        normalize(profile.location) in normalize(listing_location)
                        or normalize(listing_location) in normalize(profile.location)
                    ):
                        reasons.append("Location appears to match")
                    else:
                        mismatches.append(
                            "Opportunity location may not match your preference"
                        )

                # Work mode
                if profile.work_mode:
                    listing_mode = normalize(opportunity.work_mode)
                    user_mode = normalize(profile.work_mode)

                    if not listing_mode:
                        missing_information.append(
                            "Opportunity work mode is not specified"
                        )
                    elif user_mode == listing_mode:
                        reasons.append("Work mode matches your preference")
                    else:
                        mismatches.append(
                            "Work mode differs from your preference"
                        )

                # Minimum experience
                minimum_experience = opportunity.minimum_experience_years

                if minimum_experience is not None:
                    if profile.experience_years is None:
                        missing_information.append(
                            "Your years of experience are needed"
                        )
                    elif profile.experience_years >= minimum_experience:
                        reasons.append(
                            "Experience meets the listed minimum"
                        )
                    else:
                        mismatches.append(
                            "Experience is below the listed minimum"
                        )

                # Expected minimum monthly stipend
                if profile.expected_stipend is not None:
                    stipend = opportunity.stipend_monthly

                    if stipend is None:
                        missing_information.append(
                            "Monthly stipend is not specified"
                        )
                    elif stipend >= profile.expected_stipend:
                        reasons.append(
                            "Monthly stipend meets your expectation"
                        )
                    else:
                        mismatches.append(
                            "Monthly stipend is below your expectation"
                        )

                # Expected minimum annual salary
                if profile.expected_salary is not None:
                    salary = opportunity.salary_annual

                    if salary is None:
                        missing_information.append(
                            "Annual salary is not specified"
                        )
                    elif salary >= profile.expected_salary:
                        reasons.append(
                            "Annual salary meets your expectation"
                        )
                    else:
                        mismatches.append(
                            "Annual salary is below your expectation"
                        )

                # Research interests: listing text is only weak evidence.
                if profile.research_interests:
                    listing_text = " ".join([
                        opportunity.title or "",
                        opportunity.description or "",
                        str(eligibility),
                    ]).casefold()

                    matched_interests = [
                        interest for interest in profile.research_interests
                        if interest.strip()
                        and interest.casefold() in listing_text
                    ]

                    if matched_interests:
                        reasons.append(
                            "Related interests mentioned: "
                            + ", ".join(matched_interests)
                        )
                    else:
                        missing_information.append(
                            "Research-interest compatibility needs review"
                        )

            results.append({
                "id": opportunity.id,
                "title": opportunity.title,
                "category": opportunity.category,
                "organization": opportunity.organization,
                "description": opportunity.description,
                "deadline": opportunity.deadline,
                "source_url": opportunity.source_url,
                "verified": opportunity.verified,
                "location": opportunity.location,
                "work_mode": opportunity.work_mode,
                "stipend_monthly": opportunity.stipend_monthly,
                "salary_annual": opportunity.salary_annual,
                "match_status": determine_status(
                    mismatches, missing_information
                ),
                "matching_reasons": reasons,
                "mismatches": mismatches,
                "missing_information": missing_information,
            })

        return {
            "message": "Matching completed",
            "category": profile.category,
            "total_opportunities_checked": len(opportunities),
            "results": results,
            "note": (
                "These are preliminary matches, not confirmation "
                "of eligibility. Check the original source before applying."
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to match opportunities.",
        ) from exc
