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

    # Call the pgvector retrieval function deployed in Supabase
    params: dict = {"query_embedding": embedding, "match_count": top_k}
    if category:
        params["filter_category"] = category

    try:
        result = db.rpc("match_corpus_cases", params).execute()
        rows = result.data or []
    except Exception:
        # Fallback: plain text search if vector function signature differs
        result = db.rpc("match_corpus_cases", {"query_embedding": embedding, "match_count": top_k}).execute()
        rows = result.data or []

    precedents = []
    for row in rows:
        precedents.append(
            Precedent(
                id=str(row.get("id", "")),
                title=row.get("title", ""),
                summary=row.get("content", row.get("summary", "")),
                category=row.get("category", "general"),
                similarity=float(row.get("similarity", 0.0)),
                metadata=row.get("metadata", {}),
            )
        )
    return precedents
