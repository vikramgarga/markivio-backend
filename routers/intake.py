from fastapi import APIRouter, HTTPException
from schemas.models import (
    IntakeRequest,
    CaseFile,
    INDUSTRY_OPTIONS,
    CHALLENGE_OPTIONS,
    INSPIRATION_BRAND_OPTIONS,
    INNOVATION_TECHNIQUE_OPTIONS,
)
from agents.intake import run_intake

router = APIRouter()


@router.get("/intake/options")
async def intake_options() -> dict:
    """Return all dropdown option lists for the intake form."""
    return {
        "industries": INDUSTRY_OPTIONS,
        "challenges": CHALLENGE_OPTIONS,
        "inspiration_brands": INSPIRATION_BRAND_OPTIONS,
        "innovation_techniques": INNOVATION_TECHNIQUE_OPTIONS,
    }


@router.post("/intake", response_model=CaseFile)
async def intake(request: IntakeRequest) -> CaseFile:
    try:
        return await run_intake(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
