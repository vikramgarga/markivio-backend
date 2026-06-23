import re 
import json
import uuid
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from schemas.models import DiagnoseRequest, DiagnosisResult
from prompts.diagnostic import DIAGNOSTIC_SYSTEM, DIAGNOSTIC_USER

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    max_tokens=1024,
)


class DiagnosticState(TypedDict):
    request: DiagnoseRequest
    raw_diagnosis: str
    result: DiagnosisResult | None


async def classify_and_diagnose(state: DiagnosticState) -> DiagnosticState:
    req = state["request"]
    user_msg = DIAGNOSTIC_USER.format(
        problem=req.problem,
        client_name=req.client_name or "Unknown",
        industry=req.industry or "Unknown",
    )
    response = await llm.ainvoke(
        [SystemMessage(content=DIAGNOSTIC_SYSTEM), HumanMessage(content=user_msg)]
    )
    return {**state, "raw_diagnosis": response.content}


async def parse_diagnosis(state: DiagnosticState) -> DiagnosticState:
    req = state["request"]
    case_id = req.case_id or str(uuid.uuid4())
    raw = state["raw_diagnosis"]

        # Extract JSON from response robustly
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    clean = match.group(0) if match else raw.strip()
    data = json.loads(clean)

    result = DiagnosisResult(
        case_id=case_id,
        category=data["category"],
        severity=data["severity"],
        root_causes=data["root_causes"],
        key_questions=data["key_questions"],
        recommended_next_step=data["recommended_next_step"],
        confidence=float(data["confidence"]),
    )
    return {**state, "result": result}


def build_diagnostic_graph() -> StateGraph:
    g = StateGraph(DiagnosticState)
    g.add_node("diagnose", classify_and_diagnose)
    g.add_node("parse", parse_diagnosis)
    g.set_entry_point("diagnose")
    g.add_edge("diagnose", "parse")
    g.add_edge("parse", END)
    return g.compile()


_graph = build_diagnostic_graph()


async def run_diagnostic(request: DiagnoseRequest) -> DiagnosisResult:
    state = await _graph.ainvoke({"request": request, "raw_diagnosis": "", "result": None})
    return state["result"]
