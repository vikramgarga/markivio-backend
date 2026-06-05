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

INSPIRATION_BRAND_OPTIONS: list[str] = [
    # Global icons
    "Apple — simplicity, premium design, cult loyalty",
    "Nike — emotional storytelling, athlete identity",
    "Airbnb — community, belonging, trust-first design",
    "Patagonia — purpose-led brand, radical transparency",
    "Dove — real beauty, inclusivity, social impact",
    "Red Bull — extreme lifestyle, content as marketing",
    "Oatly — radical honesty, anti-corporate tone of voice",
    "Glossier — community-built brand, skin-first beauty",
    "Warby Parker — affordable premium, social mission",
    "Tesla — cult product, zero paid advertising",
    "Spotify — personalisation at scale, data-driven storytelling",
    "Duolingo — gamification, viral personality-led social",
    "Notion — bottoms-up PLG, community evangelism",
    "Lego — co-creation, nostalgia, multi-generational appeal",
    "IKEA — democratising design, flat-pack storytelling",
    # Indian brands
    "Amul — mass-market wit, consistency over decades",
    "Zomato — irreverent social voice, hyper-local humour",
    "boAt — aspirational youth, affordable cool",
    "Mamaearth — D2C trust-building, cause marketing",
    "Paper Boat — nostalgia, storytelling through packaging",
    "Nykaa — category creation, content-to-commerce",
    "Tanishq — emotional occasion marketing, cultural depth",
    "Fevicol — iconic rural-urban humour, product-as-hero",
    "D2C challenger (e.g. Bombay Shaving Company, Pilgrim)",
    "Other — I'll describe it",
]

INNOVATION_TECHNIQUE_OPTIONS: list[str] = [
    # Strategy frameworks
    "Blue Ocean Strategy — create uncontested market space",
    "Ansoff Growth Matrix — market/product expansion planning",
    "Porter's Five Forces — competitive landscape analysis",
    "BCG Growth-Share Matrix — portfolio prioritisation",
    "SWOT Analysis — strengths, weaknesses, opportunities, threats",
    "PESTLE Analysis — macro-environment scan",
    # Customer & insight frameworks
    "Jobs-to-be-Done (JTBD) — what job is the customer hiring this for?",
    "Design Thinking — empathise, define, ideate, prototype, test",
    "Value Proposition Canvas — fit between customer pains and your gains",
    "Empathy Mapping — deep dive into customer feelings and motivations",
    "Customer Journey Mapping — end-to-end experience design",
    # Brand & positioning frameworks
    "STP — Segmentation, Targeting, Positioning",
    "Brand Archetypes — align brand personality to universal character",
    "Golden Circle (Simon Sinek) — Why → How → What",
    "Brand Pyramid — essence, values, personality, benefits, attributes",
    "Perceptual Mapping — visual competitive positioning",
    # Innovation & ideation frameworks
    "Lean Startup / MVP — build-measure-learn loop",
    "SCAMPER — substitute, combine, adapt, modify, eliminate, reverse",
    "Six Thinking Hats — parallel thinking for group ideation",
    "Reverse Brainstorming — invert the problem to find solutions",
    "Disruptive Innovation (Christensen) — targeting over-served or non-consumers",
    # Growth frameworks
    "Pirate Metrics (AARRR) — acquisition, activation, retention, referral, revenue",
    "Flywheel Model — compounding growth loops",
    "ICE Scoring — impact, confidence, ease for prioritisation",
    "No specific technique — use your best judgement",
    "Other — I'll describe it",
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

    # Brand inspiration — select from INSPIRATION_BRAND_OPTIONS; if "Other — I'll describe it", populate inspiration_brand_other
    inspiration_brand_option: str | None = None      # selected item from INSPIRATION_BRAND_OPTIONS
    inspiration_brand_other: str | None = None       # free text when "Other — I'll describe it" is selected
    inspiration_admiration: str | None = None        # what specifically they admire (always free text)

    # Innovation technique or framework — select from INNOVATION_TECHNIQUE_OPTIONS; if "Other — I'll describe it", populate innovation_technique_other
    innovation_technique: str | None = None          # selected item from INNOVATION_TECHNIQUE_OPTIONS
    innovation_technique_other: str | None = None    # free text when "Other — I'll describe it" is selected

    budget_inr: int | None = None
    timeline_weeks: int | None = None


class CaseFile(BaseModel):
    case_id: str
    client_name: str
    industry: str
    challenges: list[str] = Field(default_factory=list)
    inspiration_brand: str | None = None       # resolved label (from dropdown or free text)
    inspiration_admiration: str | None = None
    innovation_technique: str | None = None    # resolved label (from dropdown or free text)
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
