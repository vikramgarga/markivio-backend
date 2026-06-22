"""
Corpus embedding pipeline — run once (and re-run when personas change).

Usage:
    python scripts/embed_corpus.py

What it does:
1. Reads all 75 .md persona files from /skills/
2. Splits each into semantic chunks by section heading
3. Embeds each chunk using OpenAI text-embedding-3-small
4. Upserts to Supabase corpus_chunks table

Cost: ~$0.02 for all 75 personas at text-embedding-3-small pricing.
"""

import os
import re
import sys
import time
import json
import hashlib
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SKILLS_DIR = Path(__file__).parent.parent / "skills"
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dims, matches table schema
BATCH_SIZE = 20  # embeddings per API call
RATE_LIMIT_SLEEP = 0.5  # seconds between batches


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def extract_expertise_domain(content: str, filename: str) -> str:
    """Pull the expertise domain from filename or first heading."""
    # Try to get from the H1
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return filename.replace("-", " ").replace(".md", "").title()


def chunk_persona(file_path: Path) -> list[dict]:
    """
    Split a persona .md file into chunks by section (## heading).
    Each chunk = one section. If a section is > 600 chars, split further.
    Returns list of chunk dicts.
    """
    content = file_path.read_text(encoding="utf-8")
    filename = file_path.stem  # e.g. brand-positioning-expert

    persona_name = extract_expertise_domain(content, filename)
    persona_id = slugify(persona_name)
    expertise_domain = persona_name

    # Split by ## headings
    sections = re.split(r"\n(?=## )", content)
    chunks = []
    chunk_index = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Get section name
        section_match = re.match(r"^#{1,2}\s+(.+)$", section, re.MULTILINE)
        section_name = section_match.group(1) if section_match else "Overview"

        # Clean markdown for embedding (keep text, remove syntax)
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", section)  # bold
        clean = re.sub(r"\*(.+?)\*", r"\1", clean)          # italic
        clean = re.sub(r"^#{1,3}\s+", "", clean, flags=re.MULTILINE)  # headings
        clean = re.sub(r"^\s*[-*]\s+", "- ", clean, flags=re.MULTILINE)  # bullets
        clean = clean.strip()

        if len(clean) < 30:  # skip near-empty sections
            continue

        # Prepend persona context to every chunk so retrieval is self-contained
        chunk_text = f"Expert: {persona_name}\nSection: {section_name}\n\n{clean}"

        # Split long sections (> 800 chars) into sub-chunks
        if len(chunk_text) > 800:
            sub_chunks = _split_long_section(chunk_text, persona_name, section_name)
            for sc in sub_chunks:
                chunks.append({
                    "persona_id": persona_id,
                    "persona_name": persona_name,
                    "expertise_domain": expertise_domain,
                    "section": section_name,
                    "chunk_text": sc,
                    "chunk_index": chunk_index,
                    "metadata": {"source_file": filename},
                })
                chunk_index += 1
        else:
            chunks.append({
                "persona_id": persona_id,
                "persona_name": persona_name,
                "expertise_domain": expertise_domain,
                "section": section_name,
                "chunk_text": chunk_text,
                "chunk_index": chunk_index,
                "metadata": {"source_file": filename},
            })
            chunk_index += 1

    return chunks


def _split_long_section(text: str, persona_name: str, section_name: str) -> list[str]:
    """Split a long section at sentence or bullet boundaries."""
    lines = text.split("\n")
    sub_chunks = []
    current = []
    current_len = 0

    for line in lines:
        current.append(line)
        current_len += len(line)
        if current_len > 500 and (line.startswith("- ") or line == ""):
            chunk = "\n".join(current).strip()
            if chunk:
                sub_chunks.append(chunk)
            current = [f"Expert: {persona_name}\nSection: {section_name} (continued)"]
            current_len = len(current[0])

    if current:
        remainder = "\n".join(current).strip()
        if remainder and len(remainder) > 30:
            sub_chunks.append(remainder)

    return sub_chunks if sub_chunks else [text]


def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of embedding vectors."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def main():
    print("=== Markivio Corpus Embedding Pipeline ===\n")

    # Init clients
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_KEY"]
    openai_key = os.environ["OPENAI_API_KEY"]

    db = create_client(supabase_url, supabase_key)
    oai = OpenAI(api_key=openai_key)

    # Load all persona files
    skill_files = sorted(SKILLS_DIR.glob("*.md"))
    print(f"Found {len(skill_files)} persona files\n")

    # Chunk all personas
    all_chunks = []
    for f in skill_files:
        chunks = chunk_persona(f)
        all_chunks.extend(chunks)
        print(f"  {f.stem}: {len(chunks)} chunks")

    print(f"\nTotal chunks to embed: {len(all_chunks)}")
    print(f"Estimated cost: ${len(all_chunks) * 0.00002:.4f} (text-embedding-3-small)\n")

    # Clear existing corpus (full re-embed)
    print("Clearing existing corpus_chunks...")
    db.table("corpus_chunks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    # Embed in batches and upsert
    total = len(all_chunks)
    embedded = 0

    for i in range(0, total, BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        texts = [c["chunk_text"] for c in batch]

        try:
            vectors = embed_batch(oai, texts)
        except Exception as e:
            print(f"  ERROR embedding batch {i//BATCH_SIZE + 1}: {e}")
            continue

        rows = []
        for chunk, vector in zip(batch, vectors):
            row = {**chunk, "embedding": vector, "metadata": json.dumps(chunk["metadata"])}
            rows.append(row)

        db.table("corpus_chunks").insert(rows).execute()
        embedded += len(batch)
        print(f"  Embedded and upserted {embedded}/{total} chunks", end="\r")

        if i + BATCH_SIZE < total:
            time.sleep(RATE_LIMIT_SLEEP)

    print(f"\n\nDone. {embedded} chunks embedded and stored in corpus_chunks.")
    print("Run `python scripts/verify_corpus.py` to test retrieval.")


if __name__ == "__main__":
    main()
