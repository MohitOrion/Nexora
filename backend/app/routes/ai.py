
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
        # Step 1: Extract opportunity information using Gemma
        result = analyze_opportunity(request.text)

        # Step 2: Prepare the database record
        opportunity = Opportunity(
            title=result["title"],
            category=result["category"],
            organization=result.get("organization"),
            description=result.get("description"),
            deadline=result.get("deadline"),
            eligibility=result.get("eligibility"),
            required_documents=result.get("required_documents", []),
            source_url=(
                str(request.source_url)
                if request.source_url
                else None
            ),
            verified=False,
        )

        # Step 3: Save the record to Neon PostgreSQL
        db.add(opportunity)
        db.commit()
        db.refresh(opportunity)

        # Step 4: Return the saved record
        return {
            "status": "saved",
            "verified": opportunity.verified,
            "id": opportunity.id,
            "source_url": opportunity.source_url,
            "opportunity": result,
        }

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
