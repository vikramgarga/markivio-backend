from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


# ── Diagnose ──────────────────────────────────────────────────────────────────

class DiagnoseRequest(BaseModel):
    problem: str = Field(..., min_length=10, description="Raw problem statement from the client")
    client_name: str | None = None
    industry: str | None = None
    case_id: str | None = None


class DiagnosisResult(BaseModel):
    case_id: str
    category: str
    severity: str  # low | medium | high | critical
    root_causes: list[str]
    key_questions: list[str]
    recommended_next_step: str
    confidence: float


# ── Intake ────────────────────────────────────────────────────────────────────

class IntakeRequest(BaseModel):
    case_id: str
    raw_input: str = Field(..., min_length=10)
    client_name: str
    industry: str
    budget_inr: int | None = None
    timeline_weeks: int | None = None


class CaseFile(BaseModel):
    case_id: str
    client_name: str
    industry: str
    problem_summary: str
    business_context: str
    target_audience: str
    current_situation: str
    desired_outcome: str
    constraints: list[str]
    success_metrics: list[str]
    priority_level: str  # low | medium | high | urgent
    budget_inr: int | None
    timeline_weeks: int | None


# ── Research ──────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    case_id: str
    query: str = Field(..., min_length=5)
    category: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class Precedent(BaseModel):
    id: str
    title: str
    summary: str
    category: str
    similarity: float
    metadata: dict[str, Any] = {}


class ResearchResult(BaseModel):
    case_id: str
    query: str
    precedents: list[Precedent]
    synthesis_note: str


# ── Synthesize ────────────────────────────────────────────────────────────────

class SynthesizeRequest(BaseModel):
    case_id: str
    case_file: CaseFile | None = None
    research_result: ResearchResult | None = None


class StrategicPillar(BaseModel):
    pillar: str
    rationale: str
    actions: list[str]
    kpis: list[str]


class SynthesisResult(BaseModel):
    case_id: str
    executive_summary: str
    strategic_pillars: list[StrategicPillar]
    quick_wins: list[str]
    risks: list[str]
    recommended_timeline: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
