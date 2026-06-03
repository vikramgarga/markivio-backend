from fastapi import APIRouter, HTTPException
from schemas.models import SynthesizeRequest, SynthesisResult
from agents.synthesizer import run_synthesizer

router = APIRouter()


@router.post("/synthesize", response_model=SynthesisResult)
async def synthesize(request: SynthesizeRequest) -> SynthesisResult:
    try:
        return await run_synthesizer(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
