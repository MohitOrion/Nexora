
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.gemma_service import analyze_opportunity

router = APIRouter(prefix="/ai", tags=["AI"])


class ExtractionRequest(BaseModel):
    text: str = Field(min_length=20, max_length=30000)


@router.post("/extract-opportunity")
def extract_opportunity_route(request: ExtractionRequest):
    try:
        result = analyze_opportunity(request.text)
        return {
            "status": "extracted",
            "verified": False,
            "opportunity": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
