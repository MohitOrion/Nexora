
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.opportunity import Opportunity

router = APIRouter(
    prefix="/matching",
    tags=["Eligibility Matching"],
)


class UserProfile(BaseModel):
    course: str = Field(min_length=1)
    marks_percentage: float | None = Field(
        default=None, ge=0, le=100
    )
    annual_family_income: float | None = Field(
        default=None, ge=0
    )
    category: str | None = None


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
            eligibility = scholarship.eligibility or {}

            if not isinstance(eligibility, dict):
                eligibility = {}

            reasons = []
            missing_information = []
            mismatches = []

            # Compare course
            eligible_courses = eligibility.get(
                "eligible_courses", []
            )

            if isinstance(eligible_courses, list) and eligible_courses:
                course_matches = any(
                    profile.course.strip().casefold()
                    in str(course).casefold()
                    or str(course).casefold()
                    in profile.course.strip().casefold()
                    for course in eligible_courses
                )

                if course_matches:
                    reasons.append("Course appears to match")
                else:
                    mismatches.append(
                        "Course may not match the listed eligible courses"
                    )
            else:
                missing_information.append(
                    "Eligible courses are not specified"
                )

            # Compare minimum marks
            minimum_marks = eligibility.get("minimum_marks")

            if minimum_marks is not None:
                try:
                    minimum_marks = float(minimum_marks)

                    if profile.marks_percentage is None:
                        missing_information.append(
                            "Your marks percentage is needed"
                        )
                    elif profile.marks_percentage >= minimum_marks:
                        reasons.append(
                            "Marks meet the listed minimum"
                        )
                    else:
                        mismatches.append(
                            "Marks are below the listed minimum"
                        )
                except (TypeError, ValueError):
                    missing_information.append(
                        "The minimum marks requirement needs review"
                    )

            # Compare maximum family income
            maximum_income = eligibility.get(
                "maximum_family_income"
            )

            if maximum_income is not None:
                try:
                    maximum_income = float(maximum_income)

                    if profile.annual_family_income is None:
                        missing_information.append(
                            "Your annual family income is needed"
                        )
                    elif profile.annual_family_income <= maximum_income:
                        reasons.append(
                            "Family income meets the listed limit"
                        )
                    else:
                        mismatches.append(
                            "Family income exceeds the listed limit"
                        )
                except (TypeError, ValueError):
                    missing_information.append(
                        "The income requirement needs review"
                    )

            # Compare eligible categories
            eligible_categories = eligibility.get(
                "eligible_categories", []
            )

            if (
                profile.category
                and isinstance(eligible_categories, list)
                and eligible_categories
            ):
                category_matches = any(
                    profile.category.strip().casefold()
                    in str(item).casefold()
                    for item in eligible_categories
                )

                if category_matches:
                    reasons.append(
                        "Category appears to match"
                    )
                else:
                    mismatches.append(
                        "Category may not match the listed categories"
                    )
            elif eligible_categories:
                missing_information.append(
                    "Your category or the category requirements need clarification"
                )

            # Do not label a scholarship as confirmed eligible.
            if mismatches:
                status = "possible_mismatch"
            elif missing_information:
                status = "needs_more_information"
            else:
                status = "potential_match"

            results.append(
                {
                    "id": scholarship.id,
                    "title": scholarship.title,
                    "organization": scholarship.organization,
                    "deadline": scholarship.deadline,
                    "source_url": scholarship.source_url,
                    "verified": scholarship.verified,
                    "match_status": status,
                    "matching_reasons": reasons,
                    "mismatches": mismatches,
                    "missing_information": missing_information,
                }
            )

        return {
            "message": "Matching completed",
            "total_scholarships_checked": len(scholarships),
            "results": results,
            "note": (
                "These are preliminary matches, not confirmation "
                "of eligibility. Verify the official scholarship "
                "rules before applying."
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to match scholarships.",
        ) from exc
