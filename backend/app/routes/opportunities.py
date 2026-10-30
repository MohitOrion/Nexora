from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db import get_db
from app.models.opportunity import Opportunity

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


@router.get("/")
def get_opportunities(
    category: str | None = None,
    search: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Opportunity)

        # Filter by category
        if category and category.strip():
            query = query.filter(
                Opportunity.category.ilike(category.strip())
            )

        # Search title, organization, or description
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Opportunity.title.ilike(term),
                    Opportunity.organization.ilike(term),
                    Opportunity.description.ilike(term),
                )
            )

        # Count matching records before pagination
        total = query.count()

        # Show newest records first
        records = (
            query
            .order_by(Opportunity.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "opportunities": [
                {
                    "id": item.id,
                    "title": item.title,
                    "category": item.category,
                    "organization": item.organization,
                    "description": item.description,
                    "location": item.location,
                    "work_mode": item.work_mode,
                    "stipend_monthly": item.stipend_monthly,
                    "salary_annual": item.salary_annual,
                    "deadline": item.deadline,
                    "eligibility": item.eligibility,
                    "required_documents": item.required_documents,
                    "source_url": item.source_url,
                    "verified": item.verified,
                    "created_at": (
                        item.created_at.isoformat()
                        if item.created_at
                        else None
                    ),
                }
                for item in records
            ],
        }

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve opportunities.",
        ) from exc


@router.get("/{opportunity_id}")
def get_opportunity_detail(
    opportunity_id: int,
    db: Session = Depends(get_db),
):
    opportunity = (
        db.query(Opportunity)
        .filter(Opportunity.id == opportunity_id)
        .first()
    )

    if opportunity is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found",
        )

    return {
        "id": opportunity.id,
        "title": opportunity.title,
        "category": opportunity.category,
        "organization": opportunity.organization,
        "description": opportunity.description,
        "location": opportunity.location,
        "work_mode": opportunity.work_mode,
        "stipend_monthly": opportunity.stipend_monthly,
        "salary_annual": opportunity.salary_annual,
        "eligibility": opportunity.eligibility,
        "required_documents": opportunity.required_documents,
        "deadline": opportunity.deadline,
        "source_url": opportunity.source_url,
        "verified": opportunity.verified,
        "created_at": (
            opportunity.created_at.isoformat()
            if opportunity.created_at
            else None
        ),
    }