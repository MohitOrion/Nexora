
# from typing import Optional
# from pydantic import BaseModel, Field
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from app.db import get_db
# from app.services.profile_service import (
#     create_profile,
#     get_profile,
#     update_profile,
# )

# router = APIRouter(prefix="/profile", tags=["Student Profile"])


# class ProfileInput(BaseModel):
#     course: str
#     degree: str
#     year_of_study: str
#     marks_percentage: float = Field(ge=0, le=100)
#     annual_family_income: float = Field(ge=0)

#     skills: list[str] = []
#     interests: list[str] = []

#     preferred_location: Optional[str] = None
#     preferred_work_mode: Optional[str] = None
#     expected_stipend: float = Field(default=0, ge=0)


# # Temporary demo identity. Replace with your real authentication
# # dependency before using this with real users.
# def get_demo_user_id():
#     return "demo-student-1"


# @router.post("/")
# def save_profile(
#     data: ProfileInput,
#     db: Session = Depends(get_db),
#     user_id: str = Depends(get_demo_user_id),
# ):
#     profile = create_profile(db, user_id, data.model_dump())

#     if not profile:
#         raise HTTPException(
#             status_code=409,
#             detail="Profile already exists. Use PUT to update it.",
#         )

#     return {"message": "Profile saved", "profile": profile}


# @router.get("/me")
# def read_profile(
#     db: Session = Depends(get_db),
#     user_id: str = Depends(get_demo_user_id),
# ):
#     profile = get_profile(db, user_id)

#     if not profile:
#         raise HTTPException(status_code=404, detail="Profile not found")

#     return profile


# @router.put("/me")
# def edit_profile(
#     data: ProfileInput,
#     db: Session = Depends(get_db),
#     user_id: str = Depends(get_demo_user_id),
# ):
#     profile = update_profile(db, user_id, data.model_dump())

#     if not profile:
#         raise HTTPException(status_code=404, detail="Profile not found")

#     return {"message": "Profile updated", "profile": profile}
