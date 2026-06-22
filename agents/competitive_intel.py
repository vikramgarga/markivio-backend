"""
Competitive Intelligence — Stage 2 (Read) support.

Scrapes competitor pages, extracts positioning signals, and runs a structured
LLM analysis to produce: positioning map, white space, category language patterns.

Internal only — never shown to the client. Disciplines the Situation formation.
"""

import json
import logging
import re
import asyncio
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, urljoin

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from db.client import get_supabase

logger = logging.getLogger(__name__)

_llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    max_tokens=4096,
)

_haiku = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=settings.anthropic_api_key,
    max_tokens=1024,
)

MAX_COMPETITORS = 10
MAX_PAGE_CHARS = 6000   # cap per page before passing to LLM
SCRAPE_TIMEOUT = 10     # seconds per request


# ── Scraper ────────────────────────────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)


def _clean_html(html: str) -> str:
    """Strip HTML to readable text."""
    text = _SCRIPT_STYLE_RE.sub(" ", html)
    text = _HTML_TAG_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _get_candidate_urls(base_url: str) -> list[str]:
    """Return homepage + likely /about and /pricing pages."""
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    return [
        root,
        urljoin(root, "/about"),
        urljoin(root, "/about-us"),
        urljoin(root, "/pricing"),
    ]


async def _scrape_url(client: httpx.AsyncClient, url: str) -> str:
    """Fetch a URL and return cleaned text. Returns empty string on failure."""
    try:
        r = await client.get(url, timeout=SCRAPE_TIMEOUT, follow_redirects=True)
        if r.status_code == 200:
            return _clean_html(r.text)[:MAX_PAGE_CHARS]
    except Exception as e:
        logger.debug(f"Scrape failed for {url}: {e}")
    return ""


async def scrape_competitor(url: str) -> dict:
    """
    Scrape a competitor's homepage + about + pricing.
    Returns dict with url and combined page text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Markivio/1.0; research bot)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    candidate_urls = _get_candidate_urls(url)

    async with httpx.AsyncClient(headers=headers) as client:
        pages = await asyncio.gather(*[_scrape_url(client, u) for u in candidate_urls])

    combined = "\n\n---\n\n".join(p for p in pages if p)
    return {
        "url": url,
        "raw_text": combined[:MAX_PAGE_CHARS * 2],
        "pages_scraped": len([p for p in pages if p]),
    }


# ── Per-competitor extraction ──────────────────────────────────────────────────

_EXTRACT_COMPETITOR_PROMPT = """Analyse this competitor's website text and extract their positioning signals.

Competitor URL: {url}
Website text:
---
{text}
---

Return JSON:
{{
  "url": "{url}",
  "brand_name": "<inferred brand name>",
  "headline_claim": "<their most prominent value proposition — what they lead with>",
  "target_audience": "<who they seem to be targeting — be specific>",
  "category_frame": "<how they define the category they're in>",
  "key_differentiators": ["<differentiator 1>", "<differentiator 2>", "<differentiator 3>"],
  "pricing_tier": "<premium | mid-market | value | not clear>",
  "category_language": ["<term or phrase they use>", "<term 2>", "<term 3>"],
  "apparent_weakness": "<what gap or weakness is implied by what they don't say or emphasise>",
  "confidence": "<high | medium | low — how much usable content was available>"
}}

If the page has insufficient content, set confidence to low and fill fields with best guesses."""


async def extract_competitor_positioning(scraped: dict) -> dict:
    """Run Haiku over scraped text to extract positioning signals."""
    if not scraped["raw_text"]:
        return {
            "url": scraped["url"],
            "brand_name": scraped["url"],
            "headline_claim": "Could not scrape",
            "target_audience": "Unknown",
            "category_frame": "Unknown",
            "key_differentiators": [],
            "pricing_tier": "not clear",
            "category_language": [],
            "apparent_weakness": "Unknown",
            "confidence": "low",
        }

    prompt = _EXTRACT_COMPETITOR_PROMPT.format(
        url=scraped["url"],
        text=scraped["raw_text"][:4000],
    )

    try:
        response = await _haiku.ainvoke([
            SystemMessage(content="You are a competitive intelligence analyst. Return only valid JSON."),
            HumanMessage(content=prompt),
        ])
        raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Competitor extraction failed for {scraped['url']}: {e}")
        return {"url": scraped["url"], "confidence": "low", "error": str(e)}


# ── Synthesis ──────────────────────────────────────────────────────────────────

_SYNTHESIS_PROMPT = """You are a competitive intelligence specialist conducting a market analysis for a strategy engagement.

CLIENT BRIEF:
{brief_summary}

COMPETITOR ANALYSIS:
{competitor_json}

Synthesise the competitive landscape. Be specific. Be opinionated. Name patterns.

Return JSON:
{{
  "positioning_map": {{
    "dominant_claim": "<what claim or positioning most competitors share>",
    "category_definition": "<how the category is currently being defined by competitors>",
    "price_quality_axis": "<where competitors cluster on the premium-to-value axis>",
    "audience_patterns": "<who competitors are mainly targeting — and who they're ignoring>"
  }},
  "white_space": [
    "<specific gap or positioning territory no competitor owns — be precise, not generic>",
    "<white space 2>",
    "<white space 3>"
  ],
  "category_language": [
    "<term or phrase that appears repeatedly across competitors>",
    "<term 2>",
    "<term 3>",
    "<term 4>"
  ],
  "competitive_risks": [
    "<the competitor most likely to be a direct threat and why>",
    "<second risk>"
  ],
  "strategic_implication": "<the single most important strategic implication of this competitive landscape for the client — what it means for their positioning direction>",
  "scan_summary": "<3-4 sentence narrative summary of the competitive landscape — write as a senior analyst briefing the consultant, not a list>"
}}"""


async def synthesise_competitive_landscape(
    brief_summary: str,
    competitors: list[dict],
) -> dict:
    """Run Sonnet over all competitor analyses to produce synthesis."""
    prompt = _SYNTHESIS_PROMPT.format(
        brief_summary=brief_summary,
        competitor_json=json.dumps(competitors, indent=2),
    )

    try:
        response = await _llm.ainvoke([
            SystemMessage(content="You are a competitive intelligence specialist. Return only valid JSON."),
            HumanMessage(content=prompt),
        ])
        raw = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Competitive synthesis failed: {e}")
        return {
            "white_space": [],
            "category_language": [],
            "scan_summary": f"Synthesis failed: {e}",
            "strategic_implication": "",
        }


# ── Orchestrator ───────────────────────────────────────────────────────────────

async def run_competitive_scan(brief_id: str, competitor_urls: list[str]) -> dict:
    """
    Full pipeline: scrape → extract → synthesise → persist.
    Returns the completed scan record.
    """
    db = get_supabase()
    urls = competitor_urls[:MAX_COMPETITORS]
    now = datetime.utcnow().isoformat()

    # Fetch brief for context
    brief_result = db.table("briefs").select("*").eq("brief_id", brief_id).single().execute()
    brief_data = brief_result.data
    brief_summary = (
        f"Client: {brief_data['client_name']}\n"
        f"Industry: {brief_data['industry']}\n"
        f"Brief: {brief_data['raw_input'][:500]}"
    )

    # Create scan record (pending)
    scan_record = {
        "brief_id": brief_id,
        "client_id": brief_data["client_name"],
        "competitor_urls": urls,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    insert_result = db.table("competitive_scans").insert(scan_record).execute()
    scan_id = insert_result.data[0]["id"]

    try:
        # Scrape all competitors in parallel
        logger.info(f"Scraping {len(urls)} competitors for brief {brief_id}")
        scraped_pages = await asyncio.gather(*[scrape_competitor(u) for u in urls])

        # Extract positioning from each (Haiku — fast and cheap)
        logger.info("Extracting competitor positioning signals")
        competitor_analyses = await asyncio.gather(
            *[extract_competitor_positioning(page) for page in scraped_pages]
        )
        competitor_analyses = [c for c in competitor_analyses if c]

        # Synthesise (Sonnet — one call over all competitors)
        logger.info("Synthesising competitive landscape")
        synthesis = await synthesise_competitive_landscape(brief_summary, competitor_analyses)

        # Persist completed scan
        update = {
            "competitors": json.dumps(competitor_analyses),
            "positioning_map": json.dumps(synthesis.get("positioning_map", {})),
            "white_space": synthesis.get("white_space", []),
            "category_language": synthesis.get("category_language", []),
            "scan_summary": synthesis.get("scan_summary", ""),
            "status": "complete",
            "updated_at": datetime.utcnow().isoformat(),
        }
        db.table("competitive_scans").update(update).eq("id", scan_id).execute()

        # Return full record
        result = db.table("competitive_scans").select("*").eq("id", scan_id).single().execute()
        return result.data

    except Exception as e:
        logger.error(f"Competitive scan failed: {e}")
        db.table("competitive_scans").update({
            "status": "failed",
            "scan_summary": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", scan_id).execute()
        raise


def get_latest_competitive_scan(brief_id: str) -> Optional[dict]:
    """Fetch the most recent completed scan for a brief."""
    db = get_supabase()
    try:
        result = (
            db.table("competitive_scans")
            .select("*")
            .eq("brief_id", brief_id)
            .eq("status", "complete")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.warning(f"Could not fetch competitive scan for {brief_id}: {e}")
        return None


def format_scan_for_prompt(scan: dict) -> str:
    """Format competitive scan as a prompt context block for Stage 2 injection."""
    if not scan:
        return ""

    white_space = scan.get("white_space") or []
    category_language = scan.get("category_language") or []
    positioning_map = scan.get("positioning_map") or {}

    lines = [
        "COMPETITIVE INTELLIGENCE (internal only — do not reference brands by name in client outputs)",
        "=" * 70,
    ]

    if scan.get("scan_summary"):
        lines.append(f"\n{scan['scan_summary']}")

    if positioning_map:
        lines.append("\nCOMPETITIVE POSITIONING MAP:")
        for k, v in positioning_map.items():
            if v:
                lines.append(f"  {k.replace('_', ' ').title()}: {v}")

    if white_space:
        lines.append("\nWHITE SPACE (unowned positioning territory):")
        for ws in white_space:
            lines.append(f"  → {ws}")

    if category_language:
        lines.append(f"\nCATEGORY LANGUAGE IN USE: {', '.join(category_language)}")

    lines.append("=" * 70)
    return "\n".join(lines)
