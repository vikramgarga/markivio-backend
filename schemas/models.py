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
    # ── Consumer Tech & Hardware ───────────────────────────────────────────────
    "Apple [Consumer Tech] — simplicity, premium design, end-to-end ecosystem",
    "Dyson [Consumer Tech] — engineering-as-brand, reinventing mundane categories",
    "Samsung [Consumer Tech] — mass-premium, global scale with local relevance",
    "Sonos [Consumer Tech] — premium audio, seamless UX, home ecosystem play",
    "GoPro [Consumer Tech] — community-generated content, lifestyle identity",
    "Nest/Google [Consumer Tech] — smart home, design-led hardware",
    # ── SaaS / B2B Technology ─────────────────────────────────────────────────
    "Salesforce [B2B SaaS] — category creation, ecosystem & Ohana culture",
    "HubSpot [B2B SaaS] — inbound marketing as a category, education-led growth",
    "Slack [B2B SaaS] — bottom-up viral adoption, product-led growth",
    "Notion [B2B SaaS] — community evangelism, flexible tool for all team types",
    "Figma [B2B SaaS] — collaboration-first design, community & templates",
    "Canva [B2B/B2C SaaS] — democratising design, freemium to team plans",
    "Stripe [B2B SaaS] — developer-first GTM, docs as marketing",
    "Shopify [B2B/B2C] — empowering the underdog merchant, ecosystem play",
    "Atlassian [B2B SaaS] — PLG, self-serve, low-touch enterprise expansion",
    "Zoho [B2B SaaS, India] — integrated suite, frugal innovation, SME focus",
    "Freshworks [B2B SaaS, India] — David vs Goliath positioning, SMB empathy",
    # ── E-commerce & Retail ───────────────────────────────────────────────────
    "Amazon [E-commerce] — customer obsession, flywheel, logistics as moat",
    "Warby Parker [E-commerce] — affordable premium, social mission, DTC model",
    "Chewy [E-commerce] — emotional customer service, pet parent identity",
    "Zappos [E-commerce] — culture-as-brand, WOW customer service",
    "Etsy [E-commerce] — artisan community, trust between maker and buyer",
    "Nykaa [E-commerce, India] — category creation, content-to-commerce",
    "Meesho [E-commerce, India] — social commerce, Tier 2/3 India, reseller empowerment",
    # ── FMCG / Consumer Goods ─────────────────────────────────────────────────
    "P&G [FMCG] — purpose-led brands at scale, mother-brand architecture",
    "Unilever [FMCG] — Sustainable Living Plan, brand with purpose at scale",
    "Nestlé [FMCG] — nutrition repositioning, trust through heritage",
    "Oatly [FMCG] — radical honesty, anti-corporate tone of voice",
    "Impossible Foods [FMCG] — science-led storytelling, category disruption",
    "Amul [FMCG, India] — mass-market wit, cooperative model, topical advertising",
    "Dabur [FMCG, India] — Ayurveda modernised, rural-urban bridge",
    "Marico [FMCG, India] — portfolio migration, premiumisation of commodities",
    "Fevicol/Pidilite [FMCG, India] — product-as-hero humour, rural penetration",
    # ── Food & Beverage ───────────────────────────────────────────────────────
    "Starbucks [F&B] — third place concept, personalisation, ritual creation",
    "Chipotle [F&B] — transparent supply chain, food integrity brand",
    "Blue Bottle Coffee [F&B] — craft as luxury, anti-chain positioning",
    "Red Bull [F&B] — content & events as the real product",
    "Paper Boat [F&B, India] — nostalgia marketing, packaging as storytelling",
    "Chai Point [F&B, India] — organised chai, scalable desi experience",
    # ── Fashion & Apparel ─────────────────────────────────────────────────────
    "Nike [Fashion] — emotional storytelling, athlete as identity",
    "Patagonia [Fashion] — radical purpose, anti-consumerism as brand",
    "Zara [Fashion] — fast fashion data loop, near-zero advertising",
    "Supreme [Fashion] — scarcity, drop culture, community gatekeeping",
    "boAt [Fashion/Audio, India] — aspirational youth, affordable cool",
    # ── Beauty & Personal Care ────────────────────────────────────────────────
    "Dove [Beauty] — real beauty, inclusivity, sustained social impact",
    "Glossier [Beauty] — community-built brand, skin-first, VC of customer voice",
    "Fenty Beauty [Beauty] — radical inclusivity as product strategy",
    "The Ordinary [Beauty] — ingredient transparency, anti-marketing marketing",
    "Mamaearth [Beauty, India] — D2C trust-building, toxin-free cause marketing",
    "Bombay Shaving Company [Beauty, India] — male grooming, storytelling DTC",
    # ── Automotive ────────────────────────────────────────────────────────────
    "Tesla [Auto] — software-first car, zero paid advertising, cult community",
    "Toyota [Auto] — Kaizen, quality & reliability as brand promise",
    "BYD [Auto] — vertical integration, EV at mass-market price",
    "BMW [Auto] — engineering heritage, driving pleasure as tagline",
    # ── Industrial / Manufacturing / B2B ─────────────────────────────────────
    "3M [Industrial] — innovation culture, 15% time, 60,000-product portfolio",
    "Siemens [Industrial B2B] — engineering trust, digital twin leadership",
    "Caterpillar [Industrial B2B] — iron brand, dealer network as moat",
    "Bosch [Industrial B2B] — quality across categories, Invented for life",
    "John Deere [AgriTech] — precision farming, connected equipment ecosystem",
    "Honeywell [Industrial B2B] — industrial IoT, safety-as-brand positioning",
    # ── Healthcare & Pharma ───────────────────────────────────────────────────
    "Johnson & Johnson [Healthcare] — credo-led trust, multi-category brand",
    "Philips [Healthcare] — health tech pivot from consumer electronics",
    "Medtronic [Healthcare B2B] — patient outcomes as brand KPI",
    "Apollo Hospitals [Healthcare, India] — quality + scale, medical tourism",
    # ── Financial Services & Fintech ──────────────────────────────────────────
    "Visa [Fintech] — B2B2C network effect, invisible infrastructure brand",
    "Stripe [Fintech B2B] — developer trust, API-first business model",
    "Chime [Fintech] — no-fee banking, underbanked empathy",
    "Zerodha [Fintech, India] — low-cost disruption, community & education-led",
    "HDFC Bank [Banking, India] — consistent service quality, trusted premium",
    # ── Travel, Hospitality & Logistics ──────────────────────────────────────
    "Airbnb [Travel] — community, belonging, trust-first peer marketplace",
    "Marriott/Ritz-Carlton [Hospitality] — service culture, employee-first brand",
    "Maersk [Logistics B2B] — supply chain trust, digital transformation story",
    "DHL [Logistics B2B] — reliability, yellow brand consistency at global scale",
    "IndiGo [Aviation, India] — on-time, low-cost, operational excellence as brand",
    # ── Media, Entertainment & Education ─────────────────────────────────────
    "Netflix [Media] — personalisation, original content, global-local strategy",
    "Spotify [Media] — data storytelling (Wrapped), playlist as identity",
    "Disney [Media] — IP universe, multi-generational emotional connection",
    "Duolingo [EdTech] — gamification, unhinged social personality, habit loops",
    "Khan Academy [EdTech] — free world-class education, mission as brand",
    "BYJU's [EdTech, India] — aggressive growth, celebrity-fronted aspiration",
    # ── India-specific Conglomerates & Challengers ────────────────────────────
    "Tata Group [Conglomerate, India] — trust, nation-building, diverse portfolio",
    "Godrej [Conglomerate, India] — legacy + innovation, green agenda",
    "Jio [Telecom, India] — price disruption, ecosystem lock-in at mass scale",
    "Zomato [India] — irreverent social voice, brand courage, hyper-local humour",
    "Tanishq [Jewellery, India] — emotional occasion marketing, cultural depth",
    "Lenskart [D2C, India] — omni-channel, tech-first eyewear",
    "Other — I'll describe it",
]

INNOVATION_TECHNIQUE_OPTIONS: list[str] = [
    # ── Design Thinking & Human-Centred Design ────────────────────────────────
    "Design Thinking (Stanford d.school) — Empathise → Define → Ideate → Prototype → Test",
    "Double Diamond (Design Council) — Discover, Define, Develop, Deliver",
    "Human-Centred Design (IDEO) — deep empathy with end users drives every decision",
    "Service Design — designing the full service experience, front and backstage",
    "Participatory Design / Co-design — involving users as active co-creators",
    "Experience Prototyping — simulate service or product experiences before building",
    # ── Discovery & Insight Frameworks ───────────────────────────────────────
    "Jobs-to-be-Done (JTBD) — what progress is the customer trying to make?",
    "Empathy Mapping — what users say, think, do, and feel",
    "Customer Journey Mapping — end-to-end touchpoint analysis",
    "Ethnographic Research — observing users in their natural context",
    "Voice of Customer (VoC) — structured listening across channels",
    "Kano Model — categorise features by delight vs. expectation",
    "5 Whys — root cause analysis through iterative questioning",
    "How Might We (HMW) — reframe problems as opportunity questions",
    "Assumption Mapping — surface and test hidden project assumptions",
    # ── Strategy & Competitive Frameworks ────────────────────────────────────
    "Blue Ocean Strategy — create uncontested market space, make competition irrelevant",
    "Disruptive Innovation (Christensen) — target over-served or non-consumers",
    "Ansoff Growth Matrix — market penetration, development, product dev, diversification",
    "Porter's Five Forces — competitive intensity and profit potential analysis",
    "BCG Growth-Share Matrix — portfolio prioritisation (Stars, Cash Cows, Dogs, ?)",
    "McKinsey 3 Horizons — manage core, grow adjacencies, create new ventures simultaneously",
    "Wardley Mapping — situational awareness for strategy, map value chains",
    "Platform & Ecosystem Strategy — design for network effects and multi-sided markets",
    "Crossing the Chasm (Moore) — bridge early adopters to mainstream market",
    "First Principles Thinking — deconstruct to fundamentals, rebuild from scratch",
    "Inversion (Munger) — think backwards; avoid failure rather than pursue success",
    # ── Brand & Positioning Frameworks ───────────────────────────────────────
    "STP — Segmentation, Targeting, Positioning",
    "Brand Archetypes (Jung) — align personality to one of 12 universal characters",
    "Golden Circle (Simon Sinek) — Why → How → What",
    "Brand Resonance Model (Keller) — identity, meaning, response, resonance pyramid",
    "Brand Pyramid — essence, values, personality, functional & emotional benefits",
    "Perceptual Mapping — visual plot of brand vs. competitors on key axes",
    "Distinctive Assets (Ehrenberg-Bass) — build memory structures, not differentiation",
    "Mental & Physical Availability — be easy to think of and easy to buy",
    "Category Entry Points — own the moments when buyers enter your category",
    "Lovemark Framework (Kevin Roberts) — high love + high respect = irreplaceable brand",
    # ── Ideation & Creative Problem-Solving ──────────────────────────────────
    "SCAMPER — Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse",
    "Six Thinking Hats (de Bono) — structured parallel thinking across six perspectives",
    "Lateral Thinking (de Bono) — indirect, creative approaches to problem-solving",
    "Reverse Brainstorming — how would we make the problem worse? Then invert",
    "Crazy 8s (Google Ventures) — 8 sketches in 8 minutes, force quantity of ideas",
    "Brainwriting 6-3-5 — 6 people, 3 ideas, 5 rounds; silent ideation at scale",
    "TRIZ — Theory of Inventive Problem Solving; contradiction-based innovation",
    "Biomimicry — solve human problems by emulating nature's patterns",
    "Morphological Analysis — systematically explore all combinations of variables",
    "Random Stimulus — use unrelated words/images to break mental fixedness",
    # ── Lean, Agile & Product Development ────────────────────────────────────
    "Lean Startup (Eric Ries) — Build → Measure → Learn loop",
    "Design Sprint (Google Ventures) — 5-day structured problem-solving sprint",
    "MVP (Minimum Viable Product) — fastest path to validated learning",
    "MLP (Minimum Lovable Product) — minimum that users actually love, not just tolerate",
    "Shape Up (Basecamp) — 6-week cycles, fixed appetite, variable scope",
    "Agile / Scrum — iterative delivery, sprint-based prioritisation",
    "Rapid Prototyping — lo-fi physical or digital mock-ups to test early",
    # ── Growth & Marketing Frameworks ────────────────────────────────────────
    "Pirate Metrics AARRR — Acquisition, Activation, Retention, Referral, Revenue",
    "Flywheel Model — identify compounding loops that self-reinforce growth",
    "Product-Led Growth (PLG) — product itself is the primary acquisition channel",
    "Community-Led Growth — engaged community as distribution and retention engine",
    "Hook Model (Nir Eyal) — Trigger → Action → Variable Reward → Investment",
    "ICE Scoring — Impact, Confidence, Ease; fast prioritisation of growth ideas",
    "RICE Scoring — Reach, Impact, Confidence, Effort; more rigorous than ICE",
    "Jobs-Based Segmentation — segment by the job to be done, not demographics",
    # ── Systems & Organisational Thinking ────────────────────────────────────
    "Systems Thinking / Causal Loop Diagrams — map feedback loops and leverage points",
    "Theory of Constraints (Goldratt) — identify and exploit the system's bottleneck",
    "McKinsey 7S — strategy, structure, systems, shared values, skills, style, staff",
    "Balanced Scorecard — financial, customer, process, and learning perspectives",
    "OKRs — Objectives and Key Results; align teams to ambitious measurable goals",
    "Scenario Planning — develop multiple plausible futures and strategy for each",
    # ── Business Model Innovation ─────────────────────────────────────────────
    "Business Model Canvas (Osterwalder) — nine-block visual of how value is created",
    "Value Proposition Canvas — zoom in on customer jobs, pains, and gains",
    "Lean Canvas — startup-adapted BMC with unfair advantage and key metrics",
    "Value Chain Analysis (Porter) — identify where you create and capture value",
    "SWOT Analysis — internal strengths/weaknesses, external opportunities/threats",
    "PESTLE Analysis — Political, Economic, Social, Tech, Legal, Environmental scan",
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
