
# from sqlalchemy.orm import Session
# from app.models.student_profile import StudentProfile


# def get_profile(db: Session, user_id: str):
#     return (
#         db.query(StudentProfile)
#         .filter(StudentProfile.user_id == user_id)
#         .first()
#     )


# def create_profile(db: Session, user_id: str, data: dict):
#     existing = get_profile(db, user_id)

#     if existing:
#         return None

#     profile = StudentProfile(user_id=user_id, **data)

#     db.add(profile)
#     db.commit()
#     db.refresh(profile)

#     return profile


# def update_profile(db: Session, user_id: str, data: dict):
#     profile = get_profile(db, user_id)

#     if not profile:
#         return None

#     for key, value in data.items():
#         setattr(profile, key, value)

#     db.commit()
#     db.refresh(profile)

#     return profile
