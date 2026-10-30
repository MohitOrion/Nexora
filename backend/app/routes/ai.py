
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.opportunity import Opportunity
from app.services.gemma_service import analyze_opportunity

router = APIRouter(prefix="/ai", tags=["AI"])


class ExtractionRequest(BaseModel):
    text: str = Field(min_length=20, max_length=30000)
    source_url: HttpUrl | None = None


@router.post("/extract-opportunity")
def extract_opportunity_route(
    request: ExtractionRequest,
    db: Session = Depends(get_db),
):
    try:
        # 1. Normalize the submitted source URL.
        source_url = (
            str(request.source_url).rstrip("/")
            if request.source_url
            else None
        )

        # 2. Prevent duplicate source URLs from being saved.
        if source_url:
            existing = (
                db.query(Opportunity)
                .filter(Opportunity.source_url == source_url)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "This opportunity URL already exists.",
                        "existing_id": existing.id,
                        "title": existing.title,
                        "verified": existing.verified,
                    },
                )

        # 3. Extract structured information using Gemma.
        result = analyze_opportunity(request.text)

        # 4. Prepare the database record.
        opportunity = Opportunity(
            title=result["title"],
            category=result["category"],
            organization=result.get("organization"),
            description=result.get("description"),
            deadline=result.get("deadline"),
            start_date=result.get("start_date"),
            eligibility=result.get("eligibility", {}),
            required_documents=result.get("required_documents", []),
            required_skills=result.get("required_skills", []),
            eligible_degrees=result.get("eligible_degrees", []),
            eligible_years=result.get("eligible_years", []),
            location=result.get("location"),
            work_mode=result.get("work_mode"),
            minimum_experience_years=result.get(
                "minimum_experience_years"
            ),
            stipend_monthly=result.get("stipend_monthly"),
            salary_annual=result.get("salary_annual"),
            duration_months=result.get("duration_months"),
            source_url=source_url,
            verified=False,
        )

        # 5. Save to Neon PostgreSQL.
        db.add(opportunity)
        db.commit()
        db.refresh(opportunity)

        # 6. Return the saved database values.
        return {
            "status": "saved",
            "verified": opportunity.verified,
            "id": opportunity.id,
            "source_url": opportunity.source_url,
            "opportunity": {
                "title": opportunity.title,
                "category": opportunity.category,
                "organization": opportunity.organization,
                "description": opportunity.description,
                "deadline": opportunity.deadline,
                "start_date": opportunity.start_date,
                "location": opportunity.location,
                "work_mode": opportunity.work_mode,
                "duration_months": opportunity.duration_months,
                "stipend_monthly": opportunity.stipend_monthly,
                "salary_annual": opportunity.salary_annual,
                "minimum_experience_years": (
                    opportunity.minimum_experience_years
                ),
                "required_skills": opportunity.required_skills,
                "eligible_degrees": opportunity.eligible_degrees,
                "eligible_years": opportunity.eligible_years,
                "eligibility": opportunity.eligibility,
                "required_documents": opportunity.required_documents,
                "source_uncertainties": result.get(
                    "source_uncertainties", []
                ),
            },
        }

    except HTTPException:
        db.rollback()
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save the opportunity to the database.",
        ) from exc
