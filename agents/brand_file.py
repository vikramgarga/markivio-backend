"""
Brand File — persistent, per-client knowledge store.

Grows with every engagement. When a client returns, the War Room opens
already knowing their brand — ICP, past positioning, what worked, what failed.

The consultant is the product. This is the system's institutional memory.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from db.client import get_supabase

logger = logging.getLogger(__name__)

_extractor_llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=settings.anthropic_api_key,
    max_tokens=1024,
)


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ── Read ───────────────────────────────────────────────────────────────────────

def get_brand_file(client_name: str) -> dict | None:
    """Fetch the Brand File for a client. Returns None if first engagement."""
    db = get_supabase()
    client_id = _slugify(client_name)
    try:
        result = (
            db.table("brand_files")
            .select("*")
            .eq("client_id", client_id)
            .maybe_single()
            .execute()
        )
        return result.data
    except Exception as e:
        logger.warning(f"Brand file fetch failed for {client_name}: {e}")
        return None


def format_brand_file_for_prompt(bf: dict) -> str:
    """Format a brand file as a compact context block for prompt injection."""
    if not bf:
        return ""

    lines = [
        "CLIENT BRAND FILE (accumulated knowledge from past engagements)",
        "=" * 70,
        f"Brand: {bf.get('brand_name', '—')}",
        f"Category: {bf.get('category', '—')}",
        f"Industry: {bf.get('industry', '—')}",
    ]

    icp = bf.get("icp") or {}
    if icp:
        lines.append("\nKNOWN ICP:")
        if icp.get("primary_segment"):
            lines.append(f"  Target: {icp['primary_segment']}")
        if icp.get("psychographics"):
            lines.append(f"  Psychographics: {icp['psychographics']}")
        jtbd = icp.get("jobs_to_be_done", [])
        if jtbd:
            lines.append(f"  Jobs to be done: {'; '.join(jtbd)}")

    voice = bf.get("brand_voice") or {}
    if voice:
        lines.append("\nBRAND VOICE:")
        if voice.get("tone"):
            lines.append(f"  Tone: {voice['tone']}")
        if voice.get("avoid"):
            lines.append(f"  Avoid: {voice['avoid']}")

    positioning_history = bf.get("positioning_history") or []
    if positioning_history:
        lines.append("\nPAST POSITIONING:")
        for p in positioning_history[-3:]:  # last 3 only
            lines.append(f"  [{p.get('date', '—')}] {p.get('position_statement', '')}")

    worked = bf.get("what_has_worked") or []
    if worked:
        lines.append(f"\nWHAT HAS WORKED: {'; '.join(worked[:5])}")

    failed = bf.get("what_has_failed") or []
    if failed:
        lines.append(f"WHAT HAS FAILED: {'; '.join(failed[:5])}")

    notes = bf.get("consultant_notes") or []
    if notes:
        lines.append("\nCONSULTANT NOTES:")
        for n in notes[-5:]:
            lines.append(f"  — {n}")

    lines.append("=" * 70)
    return "\n".join(lines)


# ── Write / update ─────────────────────────────────────────────────────────────

def upsert_brand_file(client_name: str, industry: str, brief_id: str, updates: dict) -> dict:
    """Create or update the brand file for a client."""
    db = get_supabase()
    client_id = _slugify(client_name)
    now = datetime.utcnow().isoformat()

    existing = get_brand_file(client_name)

    if existing:
        # Merge arrays, overwrite scalar fields
        merged = {**existing, **updates, "updated_at": now}

        # Append brief_id if not already present
        brief_ids = existing.get("brief_ids") or []
        if brief_id not in brief_ids:
            brief_ids.append(brief_id)
        merged["brief_ids"] = brief_ids

        # Merge positioning history (append, not overwrite)
        if "positioning_history" in updates:
            history = existing.get("positioning_history") or []
            history.extend(updates["positioning_history"])
            merged["positioning_history"] = history

        # Merge past situations
        if "past_situations" in updates:
            situs = existing.get("past_situations") or []
            situs.extend(updates["past_situations"])
            merged["past_situations"] = situs

        # Merge past recommendations
        if "past_recommendations" in updates:
            recs = existing.get("past_recommendations") or []
            recs.extend(updates["past_recommendations"])
            merged["past_recommendations"] = recs

        # Merge what_has_worked / what_has_failed (deduplicate)
        for field in ("what_has_worked", "what_has_failed"):
            if field in updates:
                existing_list = existing.get(field) or []
                new_items = [i for i in (updates[field] or []) if i not in existing_list]
                merged[field] = existing_list + new_items

        db.table("brand_files").update(merged).eq("client_id", client_id).execute()
        result = db.table("brand_files").select("*").eq("client_id", client_id).single().execute()
        return result.data

    else:
        new_record = {
            "client_id": client_id,
            "brand_name": client_name,
            "industry": industry,
            "category": updates.get("category", ""),
            "icp": updates.get("icp", {}),
            "brand_voice": updates.get("brand_voice", {}),
            "positioning_history": updates.get("positioning_history", []),
            "past_situations": updates.get("past_situations", []),
            "past_recommendations": updates.get("past_recommendations", []),
            "what_has_worked": updates.get("what_has_worked", []),
            "what_has_failed": updates.get("what_has_failed", []),
            "consultant_notes": updates.get("consultant_notes", []),
            "brief_ids": [brief_id],
            "created_at": now,
            "updated_at": now,
        }
        db.table("brand_files").insert(new_record).execute()
        result = db.table("brand_files").select("*").eq("client_id", client_id).single().execute()
        return result.data


# ── Auto-population from stage outputs ────────────────────────────────────────

_EXTRACT_SYSTEM = """You extract structured brand knowledge from a strategy stage output.
Return only valid JSON — no explanation, no markdown. Be specific and concise."""

_EXTRACT_DEBRIEF = """From this Debrief stage output, extract brand knowledge to persist.

Stage output:
{stage_json}

Return JSON:
{{
  "icp": {{
    "primary_segment": "<specific target — 1 sentence>",
    "psychographics": "<beliefs/fears/aspirations — 1 sentence>",
    "jobs_to_be_done": ["<job 1>", "<job 2>", "<job 3>"]
  }},
  "brand_voice": {{
    "tone": "<2-3 tone descriptors>",
    "vocabulary": "<words/phrases that fit the brand>",
    "avoid": "<words/phrases to avoid>"
  }},
  "category": "<the category this brand competes in>",
  "what_has_worked": [],
  "what_has_failed": []
}}"""

_EXTRACT_SITUATION = """From this Situation stage output, extract the situation statement to persist.

Stage output:
{stage_json}

Return JSON:
{{
  "past_situations": [
    {{
      "date": "{date}",
      "situation_statement": "<the core situation in 2 sentences max>"
    }}
  ]
}}"""

_EXTRACT_STRATEGY = """From this Strategy stage output, extract positioning to persist.

Stage output:
{stage_json}

Return JSON:
{{
  "positioning_history": [
    {{
      "date": "{date}",
      "position_statement": "<the positioning statement>",
      "strategic_direction": "<the strategic direction in 1 sentence>",
      "outcome": "pending"
    }}
  ],
  "brand_voice": {{
    "tone": "<tone implied by this positioning>",
    "vocabulary": "<language that fits>",
    "avoid": "<language to avoid>"
  }}
}}"""

_EXTRACT_RECOMMENDATION = """From this Recommendation stage output, extract learnings to persist.

Stage output:
{stage_json}

Return JSON:
{{
  "past_recommendations": [
    {{
      "date": "{date}",
      "recommendation_summary": "<the headline recommendation in 1-2 sentences>"
    }}
  ],
  "what_has_worked": ["<specific thing that is being recommended — implies it should work>"],
  "what_has_failed": []
}}"""

_STAGE_EXTRACT_PROMPTS = {
    "debrief": _EXTRACT_DEBRIEF,
    "situation": _EXTRACT_SITUATION,
    "strategy": _EXTRACT_STRATEGY,
    "recommendation": _EXTRACT_RECOMMENDATION,
}


async def extract_and_update_brand_file(
    brief_id: str,
    client_name: str,
    industry: str,
    stage: str,
    stage_data: dict,
) -> None:
    """
    After a stage is drafted or released, extract brand knowledge from the
    stage output and persist it to the Brand File. Uses Haiku — fast and cheap.
    Runs as a background task — never blocks the consultant's workflow.
    """
    prompt_template = _STAGE_EXTRACT_PROMPTS.get(stage)
    if not prompt_template:
        return

    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        prompt = prompt_template.format(
            stage_json=json.dumps(stage_data, indent=2),
            date=today,
        )

        response = await _extractor_llm.ainvoke([
            SystemMessage(content=_EXTRACT_SYSTEM),
            HumanMessage(content=prompt),
        ])

        raw = response.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        updates = json.loads(raw)

        upsert_brand_file(client_name, industry, brief_id, updates)
        logger.info(f"Brand file updated for {client_name} after {stage} stage")

    except Exception as e:
        logger.warning(f"Brand file extraction failed for {stage}/{client_name}: {e}")
        # Never raise — this is non-blocking
