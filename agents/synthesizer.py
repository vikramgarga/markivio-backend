import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from db.client import get_supabase
from schemas.models import SynthesizeRequest, SynthesisResult, StrategicPillar
from prompts.synthesizer import SYNTHESIZER_SYSTEM, SYNTHESIZER_USER

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    max_tokens=4096,
)


class SynthesisState(TypedDict):
    request: SynthesizeRequest
    raw_output: str
    result: SynthesisResult | None


async def generate_synthesis(state: SynthesisState) -> SynthesisState:
    req = state["request"]

    case_file_json = req.case_file.model_dump_json(indent=2) if req.case_file else "{}"
    research_json = req.research_result.model_dump_json(indent=2) if req.research_result else "{}"

    user_msg = SYNTHESIZER_USER.format(
        case_file_json=case_file_json,
        research_json=research_json,
    )
    response = await llm.ainvoke(
        [SystemMessage(content=SYNTHESIZER_SYSTEM), HumanMessage(content=user_msg)]
    )
    return {**state, "raw_output": response.content}


async def parse_and_save(state: SynthesisState) -> SynthesisState:
    req = state["request"]
    raw = state["raw_output"].strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)

    pillars = [
        StrategicPillar(
            pillar=p["pillar"],
            rationale=p["rationale"],
            actions=p["actions"],
            kpis=p["kpis"],
        )
        for p in data["strategic_pillars"]
    ]

    result = SynthesisResult(
        case_id=req.case_id,
        executive_summary=data["executive_summary"],
        strategic_pillars=pillars,
        quick_wins=data["quick_wins"],
        risks=data["risks"],
        recommended_timeline=data["recommended_timeline"],
    )

    db = get_supabase()
    db.table("syntheses").upsert(
        {
            "case_id": req.case_id,
            "recommendation": result.model_dump(),
        }
    ).execute()

    return {**state, "result": result}


def build_synthesizer_graph() -> StateGraph:
    g = StateGraph(SynthesisState)
    g.add_node("generate", generate_synthesis)
    g.add_node("save", parse_and_save)
    g.set_entry_point("generate")
    g.add_edge("generate", "save")
    g.add_edge("save", END)
    return g.compile()


_graph = build_synthesizer_graph()


async def run_synthesizer(request: SynthesizeRequest) -> SynthesisResult:
    state = await _graph.ainvoke({"request": request, "raw_output": "", "result": None})
    return state["result"]
