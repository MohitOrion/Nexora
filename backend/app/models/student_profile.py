
from sqlalchemy import Column, Integer, String, Float, JSON
from app.db import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Connect each profile to its authenticated user.
    # Must be unique so each user has one profile.
    user_id = Column(String, unique=True, index=True, nullable=False)

    course = Column(String, nullable=False)
    degree = Column(String, nullable=False)
    year_of_study = Column(String, nullable=False)
    marks_percentage = Column(Float, nullable=False)
    annual_family_income = Column(Float, nullable=False)

    skills = Column(JSON, default=list, nullable=False)
    interests = Column(JSON, default=list, nullable=False)

    preferred_location = Column(String, nullable=True)
    preferred_work_mode = Column(String, nullable=True)
    expected_stipend = Column(Float, default=0, nullable=False)
