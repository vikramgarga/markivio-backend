"""
War Room Agent — the AI thinking partner for Markivio consultants.

This agent does NOT generate client-facing outputs autonomously.
It deliberates with the consultant, surfaces patterns, tries angles,
and drafts content — all of which the consultant reviews before anything
reaches the client portal.

The consultant is always the final gate.
"""

import json
import uuid
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import settings
from db.client import get_supabase
from schemas.models import (
    Brief,
    BriefStageContent,
    BriefStageType,
    WarRoomMessage,
    WarRoomTurn,
    WarRoomResponse,
    OpeningBriefingRequest,
)

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    max_tokens=4096,
)


# ── Prompts ────────────────────────────────────────────────────────────────────

WAR_ROOM_SYSTEM = """You are Markivio Intelligence — the AI thinking partner for a senior marketing strategy consultant.

Your role is to think alongside the consultant, NOT to generate client-facing outputs autonomously.

You operate inside a private War Room. The client never sees this conversation.

Your character:
- You think like a BCG/McKinsey senior associate who has done deep research on the brief
- You surface patterns, contradictions, and opportunities — you do not just summarise
- You suggest angles and hypotheses for the consultant to react to — you hold them loosely
- You draw from a rich corpus of cross-industry brand and strategy precedents
- You are comfortable being wrong and being redirected
- You never name the frameworks or inspiration sources you are drawing from in client-facing drafts

When the consultant asks you to draft content for the client:
- Write in clean, confident narrative prose — no bullet points, no headers, no jargon
- Do NOT mention any company names, frameworks, or techniques unless the consultant explicitly approves
- The tone is: a very senior advisor who has thought carefully and is choosing words precisely
- Maximum 3 short paragraphs for situation/strategy stages

When surfacing corpus patterns:
- Describe the pattern and what it implies — do not name the source brand
- Frame as "a precedent in [sector]" or "a pattern across [N] cases"

When suggesting angles:
- Give each angle a sharp thesis (one sentence)
- State the strategic implication
- State the key risk
- Be honest about which angle you find most compelling and why

Always respond in valid JSON matching the schema the router expects."""


def _build_brief_context(brief: Brief) -> str:
    challenges = "\n".join(f"  - {c}" for c in brief.challenges) or "  Not specified"
    return f"""CLIENT BRIEF CONTEXT
====================
Client: {brief.client_name}
Industry: {brief.industry}
Budget: {'₹{:,}'.format(brief.budget_inr) if brief.budget_inr else 'Not specified'}
Timeline: {brief.timeline_weeks or 'Not specified'} weeks

Challenges selected:
{challenges}

Inspiration: {brief.inspiration_brand or 'None provided'}
What they admire: {brief.inspiration_admiration or 'Not specified'}
Technique preference: {brief.innovation_technique or 'None specified'}

Their words (raw brief):
\"\"\"{brief.raw_input}\"\"\""""


def _build_conversation_history(messages: list[WarRoomMessage]) -> list:
    """Convert stored messages into LangChain message format."""
    history = []
    for msg in messages:
        if msg.role == "ai":
            history.append(AIMessage(content=msg.content))
        else:
            history.append(HumanMessage(content=msg.content))
    return history


# ── Opening Briefing ───────────────────────────────────────────────────────────

OPENING_BRIEFING_PROMPT = """Generate the opening briefing for this brief.

{brief_context}

Return a JSON object with this exact structure:
{{
  "situation_read": "<2-3 sentence read of the situation as you see it — include one bold claim>",
  "core_tension": "<one sentence identifying the central strategic tension>",
  "angles": [
    {{
      "number": 1,
      "label": "<short angle name>",
      "thesis": "<one sentence thesis>",
      "implication": "<what this angle means strategically>",
      "risk": "<primary risk of this angle>",
      "suggested": true
    }},
    {{
      "number": 2,
      "label": "<short angle name>",
      "thesis": "<one sentence thesis>",
      "implication": "<what this angle means strategically>",
      "risk": "<primary risk of this angle>",
      "suggested": false
    }},
    {{
      "number": 3,
      "label": "<short angle name>",
      "thesis": "<one sentence thesis>",
      "implication": "<what this angle means strategically>",
      "risk": "<primary risk of this angle>",
      "suggested": false
    }}
  ],
  "key_questions": [
    "<question 1 to resolve before committing to a direction>",
    "<question 2>",
    "<question 3>"
  ],
  "corpus_patterns": [
    {{
      "sector": "<sector label — no brand names>",
      "pattern": "<what the pattern is>",
      "relevance": "<why it matters for this brief>"
    }}
  ]
}}

Be specific. Be opinionated. Surface the non-obvious tension. Do not be generic."""


async def generate_opening_briefing(request: OpeningBriefingRequest) -> WarRoomResponse:
    """Generate the AI's structured opening briefing for a new brief."""
    db = get_supabase()

    # Fetch the brief
    result = db.table("briefs").select("*").eq("brief_id", request.brief_id).single().execute()
    brief_data = result.data
    brief = Brief(**brief_data)

    brief_context = _build_brief_context(brief)
    prompt = OPENING_BRIEFING_PROMPT.format(brief_context=brief_context)

    response = await llm.ainvoke([
        SystemMessage(content=WAR_ROOM_SYSTEM),
        HumanMessage(content=prompt),
    ])

    raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)

    # Format the opening briefing as a rich message
    message_content = json.dumps(data)

    # Store the AI's opening message
    ai_msg = WarRoomMessage(
        brief_id=request.brief_id,
        role="ai",
        content=message_content,
        message_type="opening_briefing",
    )
    db.table("war_room_messages").insert(ai_msg.model_dump()).execute()

    # Update brief status to read_in_progress
    db.table("briefs").update({
        "status": "read_in_progress",
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("brief_id", request.brief_id).execute()

    return WarRoomResponse(
        brief_id=request.brief_id,
        message=message_content,
        message_type="opening_briefing",
        corpus_references=data.get("corpus_patterns", []),
    )


# ── War Room Conversation Turn ─────────────────────────────────────────────────

DRAFT_STAGE_PROMPT = """The consultant has asked you to draft content for the client portal — Stage: {stage}.

{brief_context}

Conversation so far has established this direction:
{direction_summary}

Write the client-facing content for this stage. Remember:
- Clean narrative prose only — no bullet points, no headers
- Maximum 3 paragraphs
- Do NOT name any companies, frameworks, or techniques
- Tone: senior advisor, precise, confident, warm
- For 'situation': articulate the tension clearly — no recommendations yet
- For 'strategy': frame the strategic choice — still no tactics
- For 'recommendation': specific moves, grounded in everything that came before

Return JSON:
{{
  "headline": "<one strong sentence — the single most important thing to say>",
  "body": "<3 paragraphs of narrative prose>",
  "internal_note": "<one sentence for the consultant — what you think is most delicate about this draft>"
}}"""


STANDARD_TURN_PROMPT = """The consultant says:
{consultant_message}

Brief context:
{brief_context}

Conversation history is provided. Continue the deliberation.

Return JSON:
{{
  "message": "<your response — think out loud, be specific, reference the brief>",
  "message_type": "standard",
  "surfaces_pattern": false,
  "pattern_detail": null
}}"""


ANGLE_EXPLORATION_PROMPT = """The consultant wants to explore this angle more deeply:
{consultant_message}

Brief context:
{brief_context}

Go deep on this angle. What does the corpus show? What's the sequencing? What are the hidden risks? What would the first 30 days look like if we committed to this direction?

Return JSON:
{{
  "message": "<deep exploration of this angle>",
  "message_type": "angle_suggestion",
  "corpus_patterns": [
    {{
      "sector": "<sector — no brand names>",
      "pattern": "<what the pattern is>",
      "relevance": "<why it matters here>"
    }}
  ],
  "sequencing": "<how this would unfold — phases and timing>",
  "commitment_test": "<the one question that would confirm this is the right angle>"
}}"""


CORPUS_SEARCH_PROMPT = """The consultant wants to surface corpus patterns relevant to:
{consultant_message}

Brief context:
{brief_context}

Surface the most relevant cross-industry patterns from your knowledge. Be specific about what the pattern is and why it transfers.

Return JSON:
{{
  "message": "<synthesis of what the corpus shows>",
  "message_type": "corpus_reference",
  "patterns": [
    {{
      "sector": "<sector — no brand names>",
      "pattern_title": "<short name for this pattern>",
      "what_happened": "<what the brand/case did>",
      "what_it_means": "<the transferable principle>",
      "relevance_to_brief": "<why this matters for this specific client>",
      "match_strength": "<high | medium | low>"
    }}
  ]
}}"""


DEVIL_ADVOCATE_PROMPT = """The consultant wants you to challenge the current direction.

Current direction being discussed:
{consultant_message}

Brief context:
{brief_context}

Play devil's advocate. What's the strongest argument against this direction? What are we missing? What assumption are we making that could be wrong?

Return JSON:
{{
  "message": "<the steelman case against the current direction>",
  "message_type": "standard",
  "core_challenge": "<the single sharpest challenge>",
  "what_we_might_be_missing": "<the blind spot>",
  "alternative_read": "<how a smart person who disagrees would see this brief>"
}}"""


async def war_room_turn(turn: WarRoomTurn) -> WarRoomResponse:
    """Process a consultant message in the War Room and return the AI's response."""
    db = get_supabase()

    # Fetch brief
    result = db.table("briefs").select("*").eq("brief_id", turn.brief_id).single().execute()
    brief = Brief(**result.data)
    brief_context = _build_brief_context(brief)

    # Fetch conversation history (last 20 messages for context)
    history_result = (
        db.table("war_room_messages")
        .select("*")
        .eq("brief_id", turn.brief_id)
        .order("created_at", desc=False)
        .limit(20)
        .execute()
    )
    history_msgs = [WarRoomMessage(**m) for m in history_result.data]
    lc_history = _build_conversation_history(history_msgs)

    # Save consultant's message
    consultant_msg = WarRoomMessage(
        brief_id=turn.brief_id,
        role="consultant",
        content=turn.message,
        message_type="consultant_message",
    )
    db.table("war_room_messages").insert(consultant_msg.model_dump()).execute()

    # Build prompt based on request type
    if turn.request_type == "draft_stage" and turn.target_stage:
        direction_summary = "\n".join(
            f"{'AI' if m.role == 'ai' else 'Consultant'}: {m.content[:200]}…"
            for m in history_msgs[-6:]
        )
        prompt = DRAFT_STAGE_PROMPT.format(
            stage=turn.target_stage,
            brief_context=brief_context,
            direction_summary=direction_summary,
        )
    elif turn.request_type == "explore_angle":
        prompt = ANGLE_EXPLORATION_PROMPT.format(
            consultant_message=turn.message,
            brief_context=brief_context,
        )
    elif turn.request_type == "corpus_search":
        prompt = CORPUS_SEARCH_PROMPT.format(
            consultant_message=turn.message,
            brief_context=brief_context,
        )
    elif turn.request_type == "devil_advocate":
        prompt = DEVIL_ADVOCATE_PROMPT.format(
            consultant_message=turn.message,
            brief_context=brief_context,
        )
    else:
        prompt = STANDARD_TURN_PROMPT.format(
            consultant_message=turn.message,
            brief_context=brief_context,
        )

    # Call LLM with full conversation context
    messages = [SystemMessage(content=WAR_ROOM_SYSTEM)] + lc_history + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(messages)

    raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)

    ai_message_content = data.get("message", raw)
    message_type = data.get("message_type", "standard")

    # If it's a draft, create a BriefStageContent object
    draft_content = None
    if turn.request_type == "draft_stage" and turn.target_stage:
        draft_content = BriefStageContent(
            brief_id=turn.brief_id,
            stage=turn.target_stage,
            headline=data.get("headline", ""),
            body=data.get("body", ""),
            internal_notes=data.get("internal_note", ""),
            is_released=False,
        )
        # Persist draft
        db.table("brief_stages").upsert({
            **draft_content.model_dump(),
            "is_released": False,
        }).execute()
        message_type = "draft_content"

    # Store AI response
    ai_msg = WarRoomMessage(
        brief_id=turn.brief_id,
        role="ai",
        content=json.dumps(data),
        message_type=message_type,
    )
    db.table("war_room_messages").insert(ai_msg.model_dump()).execute()

    corpus_refs = data.get("corpus_patterns", data.get("patterns", []))

    return WarRoomResponse(
        brief_id=turn.brief_id,
        message=ai_message_content,
        message_type=message_type,
        draft_content=draft_content,
        corpus_references=corpus_refs,
    )


# ── Stage Release ──────────────────────────────────────────────────────────────

_STAGE_TO_STATUS = {
    "debrief": "debrief_sent",
    "situation": "situation_released",
    "strategy": "strategy_released",
    "recommendation": "recommendation_released",
}

_NEXT_SIGNAL = {
    "debrief": "Once you've confirmed the brief, we'll begin our analysis. We'll be in touch when we have our initial read ready.",
    "situation": "We're developing our strategic view — the choices we believe need to be made. We'll notify you when it's ready.",
    "strategy": "We're now working on our specific recommendations. This is the culmination of everything we've been thinking through. We'll be in touch shortly.",
    "recommendation": "This is our full recommendation. We're here to discuss, refine, and work through the next steps together.",
}


async def release_stage(
    brief_id: str,
    stage: BriefStageType,
    headline: str | None = None,
    body: str | None = None,
) -> ClientPortalView:
    """Consultant releases a stage to the client portal. The gate."""
    from schemas.models import ClientPortalView, StageReleaseRequest

    db = get_supabase()
    now = datetime.utcnow().isoformat()

    # Fetch the stage draft
    stage_result = (
        db.table("brief_stages")
        .select("*")
        .eq("brief_id", brief_id)
        .eq("stage", stage)
        .single()
        .execute()
    )
    stage_data = stage_result.data

    # Apply any consultant edits
    if headline:
        stage_data["headline"] = headline
    if body:
        stage_data["body"] = body

    # Mark as released
    stage_data["is_released"] = True
    stage_data["released_at"] = now

    db.table("brief_stages").upsert(stage_data).execute()

    # Update brief status
    new_status = _STAGE_TO_STATUS.get(stage, "read_in_progress")
    db.table("briefs").update({
        "status": new_status,
        "updated_at": now,
    }).eq("brief_id", brief_id).execute()

    # Return the updated client portal view
    return await get_client_portal_view(brief_id)


async def get_client_portal_view(brief_id: str) -> ClientPortalView:
    """Build what the client sees — only released stages."""
    from schemas.models import ClientPortalView

    db = get_supabase()

    brief_result = db.table("briefs").select("*").eq("brief_id", brief_id).single().execute()
    brief = Brief(**brief_result.data)

    stages_result = (
        db.table("brief_stages")
        .select("*")
        .eq("brief_id", brief_id)
        .eq("is_released", True)
        .order("created_at", desc=False)
        .execute()
    )
    released = [BriefStageContent(**s) for s in stages_result.data]
    current_stage = released[-1].stage if released else None

    return ClientPortalView(
        brief_id=brief_id,
        client_name=brief.client_name,
        raw_input=brief.raw_input,
        released_stages=released,
        current_stage=current_stage,
        next_signal=_NEXT_SIGNAL.get(current_stage or "debrief",
                                     "We're working on the next stage. We'll be in touch."),
        status=brief.status,
    )
