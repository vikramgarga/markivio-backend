import json
from openai import AsyncOpenAI
from config import settings
from db.client import get_supabase
from schemas.models import Precedent

_openai = AsyncOpenAI(api_key=settings.openai_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"


async def embed(text: str) -> list[float]:
    response = await _openai.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


async def search_precedents(query: str, top_k: int = 5, category: str | None = None) -> list[Precedent]:
    embedding = await embed(query)

    db = get_supabase()

    # RPC function is match_corpus_cases (table: corpus_cases)
    # Returns: case_id, title, brand, summary, key_insight, similarity
    params: dict = {"query_embedding": embedding, "match_count": top_k}

    result = db.rpc("match_corpus_cases", params).execute()
    rows = result.data or []

    precedents = []
    for row in rows:
        # Build a rich summary from the available fields
        brand = row.get("brand", "")
        summary = row.get("summary", "")
        key_insight = row.get("key_insight", "")
        full_summary = f"{summary} Key insight: {key_insight}".strip() if key_insight else summary

        precedents.append(
            Precedent(
                id=str(row.get("case_id", row.get("id", ""))),
                title=f"{brand} — {row.get('title', '')}" if brand else row.get("title", ""),
                summary=full_summary,
                category=row.get("industry", row.get("category", "general")),
                similarity=float(row.get("similarity", 0.0)),
                metadata={
                    "brand": brand,
                    "key_insight": key_insight,
                },
            )
        )
    return precedents
