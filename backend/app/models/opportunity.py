from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.db import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Core Information (Used in search & category filters)
    title = Column(String(300), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    organization = Column(String(300), nullable=True, index=True)
    description = Column(Text, nullable=True)

    # JSON Fields for flexible data structures
    eligibility = Column(JSON, nullable=True)
    required_documents = Column(JSON, nullable=True)
    required_skills = Column(JSON, nullable=True)
    eligible_degrees = Column(JSON, nullable=True)
    eligible_years = Column(JSON, nullable=True)

    # Location & Work Modality
    location = Column(String(300), nullable=True)
    work_mode = Column(String(50), nullable=True)  # e.g., Remote, Hybrid, On-site

    # Financials & Duration
    minimum_experience_years = Column(Float, nullable=True)
    stipend_monthly = Column(Float, nullable=True)
    salary_annual = Column(Float, nullable=True)
    duration_months = Column(Integer, nullable=True)

    # Dates & Metadata
    deadline = Column(String(50), nullable=True)
    start_date = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)
    
    # Verification flag (Never mark AI-extracted data verified automatically)
    verified = Column(Boolean, default=False, nullable=False)

    # Timestamp for sorting newest records first (query uses this!)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )