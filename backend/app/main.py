
from fastapi import FastAPI

from app.db import Base, engine
from app.models.opportunity import Opportunity
from app.routes.ai import router as ai_router

app = FastAPI(title="Aventra API")

# Create database tables that do not already exist
Base.metadata.create_all(bind=engine)

app.include_router(ai_router)


@app.get("/")
def home():
    return {"message": "Aventra API is running"}
