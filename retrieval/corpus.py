"""
Corpus retrieval — semantic search over the embedded expert persona chunks.

Called at every War Room turn to inject the most relevant expert context
into the prompt, rather than injecting all 75 personas as flat text.
"""

import logging
from functools import lru_cache

from openai import AsyncOpenAI
from config import settings
from db.client import get_supabase

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"

# Stage → domain hints to bias retrieval toward relevant expertise
STAGE_DOMAIN_HINTS: dict[str, list[str]] = {
    "debrief":        ["brand", "consumer", "insight", "research"],
    "read":           ["competitive", "category", "intelligence", "market"],
    "situation":      ["strategy", "positioning", "brand", "marketing"],
    "strategy":       ["positioning", "brand", "strategy", "gtm"],
    "recommendation": ["gtm", "growth", "digital", "performance", "revenue"],
}


@lru_cache(maxsize=1)
def _get_oai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def _embed_query(text: str) -> list[float]:
    client = _get_oai_client()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:2000],  # cap query length
    )
    return response.data[0].embedding


async def retrieve_corpus(
    brief_text: str,
    stage: str | None = None,
    top_k: int = 8,
) -> list[dict]:
    """
    Retrieve the top-K most relevant expert persona chunks for a given brief + stage.

    Returns a list of chunk dicts with keys:
      persona_name, expertise_domain, section, chunk_text, similarity
    """
    try:
        query_embedding = await _embed_query(brief_text)
    except Exception as e:
        logger.warning(f"Corpus retrieval embedding failed: {e}")
        return []

    db = get_supabase()

    try:
        # Use the match_corpus_chunks Postgres function
        result = db.rpc(
            "match_corpus_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "filter_domain": None,
            },
        ).execute()

        chunks = result.data or []
        return chunks

    except Exception as e:
        logger.warning(f"Corpus retrieval DB call failed: {e}")
        return []


def format_corpus_for_prompt(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a compact prompt block.
    Groups by persona to avoid repetition.
    """
    if not chunks:
        return ""

    seen_personas: dict[str, list[str]] = {}
    for chunk in chunks:
        persona = chunk.get("persona_name", "Unknown Expert")
        text = chunk.get("chunk_text", "")
        if persona not in seen_personas:
            seen_personas[persona] = []
        seen_personas[persona].append(text)

    lines = ["RELEVANT EXPERT CONTEXT (retrieved from corpus — use as thinking input, not citation source)"]
    lines.append("=" * 70)

    for persona, texts in seen_personas.items():
        lines.append(f"\n[{persona}]")
        for text in texts:
            # Strip the "Expert: X\nSection: Y\n\n" prefix that was added for embedding
            clean = text
            if "\n\n" in text:
                clean = text.split("\n\n", 1)[1]
            lines.append(clean.strip())

    lines.append("=" * 70)
    return "\n".join(lines)
