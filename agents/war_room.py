"""
War Room Agent — the AI thinking partner for Markivio consultants.

This agent does NOT generate client-facing outputs autonomously.
It deliberates with the consultant, surfaces patterns, tries angles,
and drafts content — all of which the consultant reviews before anything
reaches the client portal.

The consultant is always the final gate.
"""

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import settings
from db.client import get_supabase
from retrieval.corpus import retrieve_corpus, format_corpus_for_prompt
from agents.brand_file import get_brand_file, format_brand_file_for_prompt, extract_and_update_brand_file
from agents.competitive_intel import get_latest_competitive_scan, format_scan_for_prompt
from schemas.models import (
    Brief,
    BriefStageContent,
    BriefStageType,
    ClientPortalView,
    StageReleaseRequest,
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

# ── Per-stage structured output schemas ───────────────────────────────────────

STAGE_SCHEMAS: dict[str, dict[str, Any]] = {
    "debrief": {
        "description": "Debrief — confirm understanding of the client's situation before any work begins",
        "fields": {
            "headline": "One strong sentence the client will remember — the essence of what we heard",
            "body": "3 paragraphs: (1) the situation as we understand it, (2) the core tension or challenge, (3) what we will focus on and why",
            "icp": {
                "primary_segment": "The single most important target customer — specific, not broad",
                "psychographics": "What drives them — beliefs, fears, aspirations relevant to this brand",
                "jobs_to_be_done": ["Job 1", "Job 2", "Job 3"],
            },
            "key_tensions": ["Tension 1 — specific to this brief", "Tension 2"],
            "consultant_flags": ["Flag 1 — something the consultant should probe further"],
            "internal_note": "One sentence for the consultant — what is most delicate or uncertain about this debrief",
        },
        "output_schema": """{
  "headline": "<one strong sentence — the essence of what we heard>",
  "body": "<paragraph 1: situation as we understand it>\\n\\n<paragraph 2: core tension>\\n\\n<paragraph 3: what we will focus on and why>",
  "icp": {
    "primary_segment": "<specific target customer description>",
    "psychographics": "<beliefs, fears, aspirations relevant to this brand>",
    "jobs_to_be_done": ["<functional job>", "<emotional job>", "<social job>"]
  },
  "key_tensions": ["<tension 1>", "<tension 2>"],
  "consultant_flags": ["<something to probe further>"],
  "internal_note": "<one sentence for the consultant only>"
}""",
    },

    "situation": {
        "description": "Situation — the strategic problem statement. What is true, what has changed, what it means.",
        "fields": {
            "headline": "One sentence that names the situation precisely — the consultant's single most important claim",
            "body": "3 paragraphs using Pyramid Principle: (1) Context — undisputed facts, (2) Complication — what has changed or is wrong, (3) Implication — what this means and why it demands a response now",
            "situation_statement": "2-3 sentences max — the cleanest articulation of the situation",
            "evidence": ["3 specific supporting points — facts, observations, or patterns"],
            "so_what": "The strategic implication — what must be decided as a result",
            "internal_note": "One sentence for the consultant",
        },
        "output_schema": """{
  "headline": "<one sentence naming the situation precisely>",
  "body": "<paragraph 1: Context — undisputed facts>\\n\\n<paragraph 2: Complication — what has changed or is wrong>\\n\\n<paragraph 3: Implication — what this means and why it demands a response now>",
  "situation_statement": "<2-3 sentences — the cleanest articulation>",
  "evidence": ["<supporting point 1>", "<supporting point 2>", "<supporting point 3>"],
  "so_what": "<the strategic implication — what must be decided>",
  "internal_note": "<one sentence for the consultant only>"
}""",
    },

    "strategy": {
        "description": "Strategy — the strategic direction and positioning. The choice being made, not the tactics.",
        "fields": {
            "headline": "One sentence stating the strategic direction — confident, not hedged",
            "body": "3 paragraphs: (1) The strategic choice being made and why, (2) The positioning — where the brand will play and how it will win, (3) What this rules out and why that is the right trade-off",
            "strategic_direction": "The single most important strategic move",
            "positioning_statement": "For [target], [brand] is the [category frame] that [benefit] because [RTB]",
            "key_messages": ["3 messages that flow from the positioning — not slogans, strategic claims"],
            "rationale": "The decisive argument for this direction over the alternatives",
            "internal_note": "One sentence for the consultant",
        },
        "output_schema": """{
  "headline": "<one sentence stating the strategic direction — confident, not hedged>",
  "body": "<paragraph 1: The strategic choice and why>\\n\\n<paragraph 2: Where the brand will play and how it will win>\\n\\n<paragraph 3: What this rules out and why that is the right trade-off>",
  "strategic_direction": "<the single most important strategic move>",
  "positioning_statement": "For [target], [brand] is the [category] that [benefit] because [RTB]",
  "key_messages": ["<strategic claim 1>", "<strategic claim 2>", "<strategic claim 3>"],
  "rationale": "<the decisive argument for this direction>",
  "internal_note": "<one sentence for the consultant only>"
}""",
    },

    "recommendation": {
        "description": "Recommendation — specific, earned, ready to act on. Everything before this has been building to here.",
        "fields": {
            "headline": "The headline recommendation — one sentence, direct, no hedging",
            "body": "3 paragraphs: (1) The recommendation and the argument for it, (2) The priority actions in sequence — what to do first and why order matters, (3) What success looks like and how we will know it is working",
            "priority_actions": [{"action": "string", "rationale": "string", "timeframe": "string"}],
            "measurement_framework": [{"metric": "string", "target": "string", "timeframe": "string"}],
            "what_success_looks_like": "A vivid, specific description of the outcome if this works",
            "internal_note": "One sentence for the consultant",
        },
        "output_schema": """{
  "headline": "<the headline recommendation — one sentence, direct>",
  "body": "<paragraph 1: The recommendation and argument for it>\\n\\n<paragraph 2: Priority actions in sequence — what to do first and why order matters>\\n\\n<paragraph 3: What success looks like and how we will know it is working>",
  "priority_actions": [
    {"action": "<specific action>", "rationale": "<why this action>", "timeframe": "<30/60/90 days>"}
  ],
  "measurement_framework": [
    {"metric": "<what to measure>", "target": "<specific target>", "timeframe": "<when>"}
  ],
  "what_success_looks_like": "<vivid, specific description of the outcome>",
  "internal_note": "<one sentence for the consultant only>"
}""",
    },
}

# Stages that don't have client-facing schemas (internal only)
STAGE_SCHEMAS["read"] = {
    "description": "Read — internal competitive and category analysis. Never shown to client.",
    "output_schema": """{
  "headline": "<internal synthesis headline>",
  "body": "<internal analysis — full detail, consultant-only>",
  "category_summary": "<how the category is structured>",
  "competitor_positions": [{"name": "<competitor>", "claim": "<their claim>", "weakness": "<their weakness>"}],
  "white_space": "<the gap in the market>",
  "consultant_synthesis": "<the strategic read from all of the above>",
  "internal_note": "<one sentence for the consultant>"
}""",
}


def _get_stage_prompt_instruction(stage: str) -> str:
    """Return the stage-specific schema instruction for draft prompts."""
    schema = STAGE_SCHEMAS.get(stage)
    if not schema:
        return ""
    return f"""Stage purpose: {schema['description']}

You MUST return a JSON object matching this exact schema:
{schema['output_schema']}

Requirements:
- headline: one strong sentence — specific to this client, not generic
- body: clean narrative paragraphs separated by \\n\\n — NO bullet points, NO headers, NO framework names
- All other fields: complete and specific to this brief
- internal_note: consultant-only — never seen by client"""


# ── JSON parsing with retry ────────────────────────────────────────────────────

def _strip_json(raw: str) -> str:
    return raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


async def _invoke_with_retry(messages: list, schema_description: str, max_retries: int = 2) -> dict:
    """Call the LLM and retry up to max_retries times if JSON schema validation fails."""
    from langchain_core.messages import HumanMessage

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = await llm.ainvoke(messages)
            raw = _strip_json(response.content)
            data = json.loads(raw)

            # Basic validation: must be a dict with at least headline and body
            if not isinstance(data, dict):
                raise ValueError("Response is not a JSON object")
            if "message" not in data and "headline" not in data and "situation_read" not in data:
                raise ValueError(f"Missing required fields. Got keys: {list(data.keys())}")

            return data

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            logger.warning(f"Schema validation failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                correction = HumanMessage(
                    content=f"Your previous response did not produce valid JSON matching the required schema.\n"
                            f"Error: {e}\n"
                            f"Required schema: {schema_description}\n"
                            f"Please regenerate your response as valid JSON only — no markdown, no explanation."
                )
                messages = messages + [correction]

    raise ValueError(f"Failed to produce valid JSON after {max_retries + 1} attempts: {last_error}")


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

    # Inject Brand File if this client has been here before
    brand_file = get_brand_file(brief.client_name)
    brand_file_block = format_brand_file_for_prompt(brand_file) if brand_file else ""

    # Retrieve relevant expert corpus chunks for this brief
    corpus_chunks = await retrieve_corpus(
        brief_text=f"{brief.client_name} {brief.industry} {brief.raw_input}",
        stage="debrief",
        top_k=8,
    )
    corpus_block = format_corpus_for_prompt(corpus_chunks)
    context_blocks = brief_context
    if brand_file_block:
        context_blocks += f"\n\n{brand_file_block}"
    if corpus_block:
        context_blocks += f"\n\n{corpus_block}"

    prompt = OPENING_BRIEFING_PROMPT.format(brief_context=context_blocks)

    data = await _invoke_with_retry(
        [SystemMessage(content=WAR_ROOM_SYSTEM), HumanMessage(content=prompt)],
        schema_description="Opening briefing JSON with situation_read, core_tension, angles[], key_questions[], corpus_patterns[]",
    )

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

{stage_schema_instruction}

Writing rules (apply to headline and body always):
- Clean narrative prose — no bullet points, no headers, no numbered lists
- Do NOT name any companies, frameworks, or techniques in client-facing text
- Tone: senior advisor who has thought carefully and is choosing every word precisely
- Be specific to this client — never generic
- The headline must be something the client will remember and quote back"""


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

    # Brand File — inject accumulated client knowledge first
    brand_file = get_brand_file(brief.client_name)
    brand_file_block = format_brand_file_for_prompt(brand_file) if brand_file else ""

    # Corpus RAG — retrieve relevant expert chunks
    corpus_query = f"{brief.industry} {brief.raw_input} {turn.message}"
    corpus_chunks = await retrieve_corpus(
        brief_text=corpus_query,
        stage=turn.target_stage or "situation",
        top_k=6,
    )
    corpus_block = format_corpus_for_prompt(corpus_chunks)

    # Competitive scan — inject for Read/Situation/Strategy stages
    comp_scan = None
    if turn.target_stage in ("read", "situation", "strategy") or turn.request_type in ("explore_angle", "corpus_search", "devil_advocate", "draft_stage"):
        comp_scan = get_latest_competitive_scan(turn.brief_id)
    comp_block = format_scan_for_prompt(comp_scan) if comp_scan else ""

    if brand_file_block:
        brief_context += f"\n\n{brand_file_block}"
    if comp_block:
        brief_context += f"\n\n{comp_block}"
    if corpus_block:
        brief_context += f"\n\n{corpus_block}"

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
    schema_hint = "JSON with message and message_type fields"
    if turn.request_type == "draft_stage" and turn.target_stage:
        direction_summary = "\n".join(
            f"{'AI' if m.role == 'ai' else 'Consultant'}: {m.content[:200]}…"
            for m in history_msgs[-6:]
        )
        stage_schema = STAGE_SCHEMAS.get(turn.target_stage, {})
        schema_hint = stage_schema.get("output_schema", schema_hint)
        prompt = DRAFT_STAGE_PROMPT.format(
            stage=turn.target_stage,
            brief_context=brief_context,
            direction_summary=direction_summary,
            stage_schema_instruction=_get_stage_prompt_instruction(turn.target_stage),
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

    # Call LLM with retry on schema validation failure
    messages = [SystemMessage(content=WAR_ROOM_SYSTEM)] + lc_history + [HumanMessage(content=prompt)]
    data = await _invoke_with_retry(messages, schema_description=schema_hint)

    ai_message_content = data.get("message", raw)
    message_type = data.get("message_type", "standard")

    # If it's a draft, create a BriefStageContent object
    draft_content = None
    if turn.request_type == "draft_stage" and turn.target_stage:
        # Collect all structured fields beyond headline/body for the ai_angles store
        extra_fields = {k: v for k, v in data.items() if k not in ("headline", "body", "internal_note", "message", "message_type")}
        draft_content = BriefStageContent(
            brief_id=turn.brief_id,
            stage=turn.target_stage,
            headline=data.get("headline", ""),
            body=data.get("body", ""),
            internal_notes=data.get("internal_note", ""),
            ai_angles=[extra_fields] if extra_fields else [],
            is_released=False,
        )
        db.table("brief_stages").upsert(draft_content.model_dump()).execute()
        message_type = "draft_content"
        logger.info(f"Drafted stage {turn.target_stage} for brief {turn.brief_id}")

        # Async: update Brand File from this draft (non-blocking)
        import asyncio
        asyncio.create_task(extract_and_update_brand_file(
            brief_id=turn.brief_id,
            client_name=brief.client_name,
            industry=brief.industry,
            stage=turn.target_stage,
            stage_data=data,
        ))

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

    # Async: update Brand File on release (non-blocking)
    import asyncio
    brief_result = db.table("briefs").select("*").eq("brief_id", brief_id).single().execute()
    brief_obj = Brief(**brief_result.data)
    asyncio.create_task(extract_and_update_brand_file(
        brief_id=brief_id,
        client_name=brief_obj.client_name,
        industry=brief_obj.industry,
        stage=stage,
        stage_data=stage_data,
    ))

    # Return the updated client portal view
    return await get_client_portal_view(brief_id)


async def get_client_portal_view(brief_id: str) -> ClientPortalView:
    """Build what the client sees — only released stages."""
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
