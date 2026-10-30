
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.db import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(300), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)

    organization = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)

    # Store flexible eligibility details as JSON
    eligibility = Column(JSON, nullable=True)
    required_documents = Column(JSON, nullable=True)

    deadline = Column(String(50), nullable=True)
    source_url = Column(Text, nullable=True)

    # Extracted data is not automatically verified
    verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
