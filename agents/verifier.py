"""
Brand Guardianship Verifier — quality gate before drafts reach the consultant.

Runs after every stage draft generation using Claude Haiku (fast, cheap).
Checks three things:
  1. Brand alignment — does it contradict the client's Brand File?
  2. Differentiation — does it mirror competitor language or claims?
  3. Actionability — is it specific enough to act on, or is it generic?

The consultant sees the result as a warning banner and can override or regenerate.
Their judgment always wins. This is a quality prompt, not a blocker.
"""

import json
import logging
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from db.client import get_supabase

logger = logging.getLogger(__name__)

_haiku = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=settings.anthropic_api_key,
    max_tokens=512,
)

_VERIFIER_SYSTEM = """You are a brand quality reviewer for a premium strategy consultancy.
Your job is to catch problems before they reach the consultant — not to block work, but to flag genuine issues.
Be precise and specific. Do not flag things that are fine. Return only valid JSON."""

_VERIFIER_PROMPT = """Review this {stage} stage draft against three quality criteria.

DRAFT:
Headline: {headline}
Body: {body}

BRAND FILE (what we know about this client):
{brand_file_summary}

COMPETITIVE LANDSCAPE (what competitors claim):
{competitive_summary}

Check each criterion:

1. BRAND ALIGNMENT: Does the draft contradict or ignore something important from the Brand File?
   — Only flag if there is a genuine conflict, not just a missing detail.

2. DIFFERENTIATION: Does the headline or body use the same language, claim the same territory, or make the same promise as a known competitor?
   — Only flag if there is a real overlap, not superficial similarity.

3. ACTIONABILITY: Is this draft specific enough to this client to be useful? Or is it generic enough to apply to any brand in any category?
   — Flag only if it reads like a template rather than specific strategic counsel.

Return JSON:
{{
  "passes": <true if no significant issues, false if any criterion fails>,
  "checks": {{
    "brand_alignment": {{ "pass": <true/false>, "note": "<one sentence — what the issue is, or 'Clear' if fine>" }},
    "differentiation": {{ "pass": <true/false>, "note": "<one sentence — what the issue is, or 'Clear' if fine>" }},
    "actionability": {{ "pass": <true/false>, "note": "<one sentence — what the issue is, or 'Clear' if fine>" }}
  }},
  "issues": [<failing criterion notes only — empty list if passes: true>],
  "suggested_edits": [<one specific suggested fix per issue — empty list if passes: true>]
}}"""


def _summarise_brand_file(brand_file: dict | None) -> str:
    if not brand_file:
        return "No Brand File available for this client."
    parts = []
    icp = brand_file.get("icp") or {}
    if icp.get("primary_segment"):
        parts.append(f"Target: {icp['primary_segment']}")
    voice = brand_file.get("brand_voice") or {}
    if voice.get("tone"):
        parts.append(f"Tone: {voice['tone']}")
    if voice.get("avoid"):
        parts.append(f"Avoid: {voice['avoid']}")
    history = brand_file.get("positioning_history") or []
    if history:
        last = history[-1]
        parts.append(f"Last positioning: {last.get('position_statement', '')}")
    failed = brand_file.get("what_has_failed") or []
    if failed:
        parts.append(f"What has failed: {'; '.join(failed[:3])}")
    return "\n".join(parts) if parts else "Brand File exists but has no structured content yet."


def _summarise_competitive_scan(comp_scan: dict | None) -> str:
    if not comp_scan:
        return "No competitive scan available."
    parts = []
    pos_map = comp_scan.get("positioning_map") or {}
    if pos_map.get("dominant_claim"):
        parts.append(f"Dominant competitor claim: {pos_map['dominant_claim']}")
    if pos_map.get("category_definition"):
        parts.append(f"How category is defined: {pos_map['category_definition']}")
    lang = comp_scan.get("category_language") or []
    if lang:
        parts.append(f"Category language in use: {', '.join(lang[:6])}")
    ws = comp_scan.get("white_space") or []
    if ws:
        parts.append(f"White space: {'; '.join(ws[:2])}")
    return "\n".join(parts) if parts else "Competitive scan exists but has no structured content."


async def verify_stage_draft(
    brief_id: str,
    stage: str,
    headline: str,
    body: str,
    brand_file: dict | None = None,
    comp_scan: dict | None = None,
) -> dict:
    """
    Run the verification pass. Returns:
    {
      passes: bool,
      checks: { brand_alignment, differentiation, actionability },
      issues: str[],
      suggested_edits: str[],
    }
    Never raises — returns a passes=True result on failure so the consultant is never blocked.
    """
    if not headline and not body:
        return {"passes": True, "checks": {}, "issues": [], "suggested_edits": []}

    brand_summary = _summarise_brand_file(brand_file)
    comp_summary = _summarise_competitive_scan(comp_scan)

    prompt = _VERIFIER_PROMPT.format(
        stage=stage,
        headline=headline,
        body=body[:1500],
        brand_file_summary=brand_summary,
        competitive_summary=comp_summary,
    )

    try:
        response = await _haiku.ainvoke([
            SystemMessage(content=_VERIFIER_SYSTEM),
            HumanMessage(content=prompt),
        ])
        raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)

        # Log to Supabase
        _log_verification(brief_id, stage, result)

        return result

    except Exception as e:
        logger.warning(f"Verification failed for {stage}/{brief_id}: {e}")
        # On any failure: pass silently — never block the consultant
        return {"passes": True, "checks": {}, "issues": [], "suggested_edits": [], "_error": str(e)}


def _log_verification(brief_id: str, stage: str, result: dict) -> None:
    """Persist verification result for later analysis."""
    try:
        db = get_supabase()
        db.table("verification_logs").insert({
            "brief_id": brief_id,
            "stage": stage,
            "passes": result.get("passes", True),
            "issues": result.get("issues", []),
            "suggested_edits": result.get("suggested_edits", []),
            "consultant_overrode": False,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        logger.debug(f"Verification log write failed: {e}")


def mark_consultant_override(brief_id: str, stage: str) -> None:
    """Consultant chose to proceed despite verification issues. Log it."""
    try:
        db = get_supabase()
        # Update the most recent failing log for this brief+stage
        result = (
            db.table("verification_logs")
            .select("id")
            .eq("brief_id", brief_id)
            .eq("stage", stage)
            .eq("passes", False)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            db.table("verification_logs").update({"consultant_overrode": True}).eq(
                "id", result.data[0]["id"]
            ).execute()
    except Exception as e:
        logger.debug(f"Override log failed: {e}")
