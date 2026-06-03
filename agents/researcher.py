import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from db.client import get_supabase
from schemas.models import ResearchRequest, ResearchResult, Precedent
from retrieval.search import search_precedents
from prompts.researcher import RESEARCHER_SYSTEM, RESEARCHER_USER

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=settings.anthropic_api_key,
    max_tokens=512,
)


class ResearchState(TypedDict):
    request: ResearchRequest
    precedents: list[Precedent]
    synthesis_note: str
    result: ResearchResult | None


async def retrieve_precedents(state: ResearchState) -> ResearchState:
    req = state["request"]
    precedents = await search_precedents(
        query=req.query,
        top_k=req.top_k,
        category=req.category,
    )
    return {**state, "precedents": precedents}


async def synthesise_precedents(state: ResearchState) -> ResearchState:
    precedents = state["precedents"]
    req = state["request"]

    if not precedents:
        return {**state, "synthesis_note": "No relevant precedents found in the knowledge base for this query."}

    precedents_json = json.dumps(
        [{"title": p.title, "summary": p.summary, "category": p.category, "similarity": p.similarity} for p in precedents],
        indent=2,
    )
    user_msg = RESEARCHER_USER.format(query=req.query, precedents_json=precedents_json)
    response = await llm.ainvoke(
        [SystemMessage(content=RESEARCHER_SYSTEM), HumanMessage(content=user_msg)]
    )
    raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)
    return {**state, "synthesis_note": data["synthesis_note"]}


async def assemble_and_save(state: ResearchState) -> ResearchState:
    req = state["request"]
    result = ResearchResult(
        case_id=req.case_id,
        query=req.query,
        precedents=state["precedents"],
        synthesis_note=state["synthesis_note"],
    )

    db = get_supabase()
    db.table("research_results").upsert(
        {
            "case_id": req.case_id,
            "query": req.query,
            "results": result.model_dump(),
        }
    ).execute()

    return {**state, "result": result}


def build_researcher_graph() -> StateGraph:
    g = StateGraph(ResearchState)
    g.add_node("retrieve", retrieve_precedents)
    g.add_node("synthesise", synthesise_precedents)
    g.add_node("save", assemble_and_save)
    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "synthesise")
    g.add_edge("synthesise", "save")
    g.add_edge("save", END)
    return g.compile()


_graph = build_researcher_graph()


async def run_researcher(request: ResearchRequest) -> ResearchResult:
    state = await _graph.ainvoke(
        {"request": request, "precedents": [], "synthesis_note": "", "result": None}
    )
    return state["result"]
