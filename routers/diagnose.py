from fastapi import APIRouter, HTTPException
from schemas.models import DiagnoseRequest, DiagnosisResult
from agents.diagnostic import run_diagnostic

router = APIRouter()


@router.post("/diagnose", response_model=DiagnosisResult)
async def diagnose(request: DiagnoseRequest) -> DiagnosisResult:
    try:
        return await run_diagnostic(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
