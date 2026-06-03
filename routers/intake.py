from fastapi import APIRouter, HTTPException
from schemas.models import IntakeRequest, CaseFile
from agents.intake import run_intake

router = APIRouter()


@router.post("/intake", response_model=CaseFile)
async def intake(request: IntakeRequest) -> CaseFile:
    try:
        return await run_intake(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
