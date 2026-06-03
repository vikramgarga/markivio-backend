from fastapi import APIRouter, HTTPException
from schemas.models import ResearchRequest, ResearchResult
from agents.researcher import run_researcher

router = APIRouter()


@router.post("/research", response_model=ResearchResult)
async def research(request: ResearchRequest) -> ResearchResult:
    try:
        return await run_researcher(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
