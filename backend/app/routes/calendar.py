
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.opportunity import Opportunity

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"],
)


def parse_deadline(value):
    """Convert a supported deadline string into YYYY-MM-DD."""
    if not value:
        return None

    value = value.strip()

    # Handle dates such as 2026-10-31.
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        pass

    # Handle ISO datetimes such as 2026-10-31T23:59:00.
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date().isoformat()
    except ValueError:
        return None


@router.get("/events")
def get_calendar_events(
    db: Session = Depends(get_db),
):
    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.deadline.isnot(None))
        .order_by(Opportunity.deadline.asc())
        .all()
    )

    events = []

    for item in opportunities:
        event_date = parse_deadline(item.deadline)

        # Skip empty or unsupported deadline formats.
        if event_date is None:
            continue

        events.append({
            "id": f"opportunity-{item.id}",
            "title": f"{item.title} deadline",
            "date": event_date,
            "url": None,
            "extendedProps": {
                "opportunity_id": item.id,
                "organization": item.organization,
                "category": item.category,
                "source_url": item.source_url,
                "verified": item.verified,
            },
        })

    return events
