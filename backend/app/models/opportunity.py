\
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean
from sqlalchemy import DateTime, Float
from sqlalchemy.sql import func

from app.db import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)

    # Basic opportunity information
    title = Column(String(300), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    organization = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)

    # Existing flexible eligibility data
    eligibility = Column(JSON, nullable=True)
    required_documents = Column(JSON, nullable=True)

    # New structured fields for matching
    required_skills = Column(JSON, nullable=True)
    eligible_degrees = Column(JSON, nullable=True)
    eligible_years = Column(JSON, nullable=True)

    location = Column(String(300), nullable=True)
    work_mode = Column(String(50), nullable=True)

    minimum_experience_years = Column(Float, nullable=True)
    stipend_monthly = Column(Float, nullable=True)
    salary_annual = Column(Float, nullable=True)
    duration_months = Column(Integer, nullable=True)

    # Dates and source
    deadline = Column(String(50), nullable=True)
    start_date = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)

    # Never mark AI-extracted data verified automatically
    verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
