from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


# ── Intake dropdown options ────────────────────────────────────────────────────

INDUSTRY_OPTIONS: list[str] = [
    "FMCG / Consumer Goods",
    "Food & Beverage",
    "Fashion & Apparel",
    "Beauty & Personal Care",
    "Healthcare & Pharma",
    "Retail & E-commerce",
    "Technology & SaaS",
    "Financial Services & Fintech",
    "Education & EdTech",
    "Real Estate & Construction",
    "Automotive",
    "Travel & Hospitality",
    "Media & Entertainment",
    "Agriculture & AgrTech",
    "Manufacturing & Industrial",
    "Non-Profit & Social Impact",
    "Professional Services",
    "Other",
]

CHALLENGE_OPTIONS: list[str] = [
    "Low brand awareness",
    "Poor customer retention / high churn",
    "Unclear brand positioning",
    "Ineffective digital presence",
    "Weak lead generation",
    "High customer acquisition cost",
    "Entering a new market or geography",
    "Launching a new product or category",
    "Competing against a dominant incumbent",
    "Rebranding or repositioning",
    "Inconsistent brand experience across channels",
    "Building a B2B sales pipeline",
    "Growing in a price-sensitive market",
    "Limited marketing budget",
    "Team lacks marketing capability",
    "Other",
]

INSPIRATION_CATEGORY_OPTIONS: list[str] = [
    "FMCG / Consumer Goods",
    "Food & Beverage",
    "Fashion & Apparel",
    "Beauty & Personal Care",
    "Healthcare & Pharma",
    "Technology / SaaS",
    "Financial Services",
    "Retail / E-commerce",
    "Automotive",
    "Travel & Hospitality",
    "Education",
    "Non-Profit / Social Impact",
    "Other",
]

INNOVATION_TECHNIQUE_OPTIONS: list[str] = [
    "Design Thinking",
    "Jobs-to-be-Done (JTBD)",
    "Blue Ocean Strategy",
    "Lean Startup / MVP approach",
    "SCAMPER",
    "Ansoff Growth Matrix",
    "Porter's Five Forces",
    "Value Proposition Canvas",
    "Brand Archetypes",
    "STP (Segmentation, Targeting, Positioning)",
    "No specific technique — use your best judgement",
    "Other",
]


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
    case_id: str | None = None   # auto-generated if not provided
    raw_input: str = Field(..., min_length=10)
    client_name: str

    # Industry — one of INDUSTRY_OPTIONS; if "Other", populate industry_other
    industry: str
    industry_other: str | None = None

    # Challenges — one or more from CHALLENGE_OPTIONS; if "Other" selected, populate challenges_other
    challenges: list[str] = Field(default_factory=list)
    challenges_other: str | None = None

    # Brand inspiration from another category
    inspiration_category: str | None = None          # from INSPIRATION_CATEGORY_OPTIONS
    inspiration_category_other: str | None = None    # if "Other" selected
    inspiration_brand: str | None = None             # name of the brand they admire
    inspiration_admiration: str | None = None        # what specifically they admire

    # Innovation technique or framework to apply
    innovation_technique: str | None = None          # from INNOVATION_TECHNIQUE_OPTIONS
    innovation_technique_other: str | None = None    # if "Other" selected

    budget_inr: int | None = None
    timeline_weeks: int | None = None


class CaseFile(BaseModel):
    case_id: str
    client_name: str
    industry: str
    challenges: list[str] = Field(default_factory=list)
    inspiration_brand: str | None = None
    inspiration_category: str | None = None
    inspiration_admiration: str | None = None
    innovation_technique: str | None = None
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
    case_id: str | None = None   # auto-generated if not provided
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
