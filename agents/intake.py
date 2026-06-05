import json
import uuid
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from db.client import get_supabase
from schemas.models import IntakeRequest, CaseFile
from prompts.intake import INTAKE_SYSTEM, INTAKE_USER

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    max_tokens=2048,
)


class IntakeState(TypedDict):
    request: IntakeRequest
    raw_output: str
    case_file: CaseFile | None


def _resolve_industry(req: IntakeRequest) -> str:
    if req.industry == "Other" and req.industry_other:
        return req.industry_other
    return req.industry


def _build_challenges_text(req: IntakeRequest) -> str:
    items = [c for c in req.challenges if c != "Other"]
    if req.challenges_other:
        items.append(req.challenges_other)
    return "\n".join(f"- {c}" for c in items) if items else "Not specified"


def _build_inspiration_text(req: IntakeRequest) -> str:
    if not req.inspiration_brand and not req.inspiration_category:
        return "None provided"
    category = req.inspiration_category or ""
    if category == "Other" and req.inspiration_category_other:
        category = req.inspiration_category_other
    parts = []
    if req.inspiration_brand:
        parts.append(f"Brand: {req.inspiration_brand}")
    if category:
        parts.append(f"Category: {category}")
    if req.inspiration_admiration:
        parts.append(f"What they admire: {req.inspiration_admiration}")
    return "\n".join(parts)


def _resolve_technique(req: IntakeRequest) -> str:
    if not req.innovation_technique:
        return "Not specified"
    if req.innovation_technique == "Other" and req.innovation_technique_other:
        return req.innovation_technique_other
    return req.innovation_technique


async def extract_case_file(state: IntakeState) -> IntakeState:
    req = state["request"]
    user_msg = INTAKE_USER.format(
        client_name=req.client_name,
        industry=_resolve_industry(req),
        budget_inr=f"₹{req.budget_inr:,}" if req.budget_inr else "Not specified",
        timeline_weeks=req.timeline_weeks or "Not specified",
        challenges=_build_challenges_text(req),
        inspiration=_build_inspiration_text(req),
        innovation_technique=_resolve_technique(req),
        raw_input=req.raw_input,
    )
    response = await llm.ainvoke(
        [SystemMessage(content=INTAKE_SYSTEM), HumanMessage(content=user_msg)]
    )
    return {**state, "raw_output": response.content}


async def parse_and_save(state: IntakeState) -> IntakeState:
    req = state["request"]
    case_id = req.case_id or str(uuid.uuid4())
    raw = state["raw_output"].strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)

    resolved_industry = _resolve_industry(req)
    resolved_challenges = [c for c in req.challenges if c != "Other"]
    if req.challenges_other:
        resolved_challenges.append(req.challenges_other)

    resolved_inspiration_category = req.inspiration_category
    if resolved_inspiration_category == "Other" and req.inspiration_category_other:
        resolved_inspiration_category = req.inspiration_category_other

    resolved_technique = _resolve_technique(req)

    case_file = CaseFile(
        case_id=case_id,
        client_name=req.client_name,
        industry=resolved_industry,
        challenges=resolved_challenges,
        inspiration_brand=req.inspiration_brand,
        inspiration_category=resolved_inspiration_category,
        inspiration_admiration=req.inspiration_admiration,
        innovation_technique=resolved_technique if resolved_technique != "Not specified" else None,
        problem_summary=data["problem_summary"],
        business_context=data["business_context"],
        target_audience=data["target_audience"],
        current_situation=data["current_situation"],
        desired_outcome=data["desired_outcome"],
        constraints=data["constraints"],
        success_metrics=data["success_metrics"],
        priority_level=data["priority_level"],
        budget_inr=req.budget_inr,
        timeline_weeks=req.timeline_weeks,
    )

    db = get_supabase()
    db.table("intakes").upsert(
        {
            "case_id": case_file.case_id,
            "client_name": case_file.client_name,
            "industry": case_file.industry,
            "raw_input": req.raw_input,
            "structured_data": case_file.model_dump(),
        }
    ).execute()

    return {**state, "case_file": case_file}


def build_intake_graph() -> StateGraph:
    g = StateGraph(IntakeState)
    g.add_node("extract", extract_case_file)
    g.add_node("save", parse_and_save)
    g.set_entry_point("extract")
    g.add_edge("extract", "save")
    g.add_edge("save", END)
    return g.compile()


_graph = build_intake_graph()


async def run_intake(request: IntakeRequest) -> CaseFile:
    state = await _graph.ainvoke({"request": request, "raw_output": "", "case_file": None})
    return state["case_file"]
