# Skill: RAG ingestion

## When to use

Modifying `rag-ingestion/ingest.py`, adding documents to `knowledge-base/`, or debugging retrieval quality.

## Project-specific conventions

### Knowledge base scope

The KB has exactly 5 sources at MVP:

1. Hyrox Training Guide (official PDF)
2. Joe Friel — Triathlete's Training Bible (selected extracts on periodization)
3. ISSN Position Stand: Nutrient Timing (open-access academic paper)
4. Asker Jeukendrup — Sport Nutrition (extracted web articles from mysportscience.com)
5. Community articles on first-time Hyrox prep (2-3 articles)

Adding a new source requires:
- Confirming the source is freely re-distributable or used in extract form (not full re-distribution)
- Adding it to `knowledge-base/SOURCES.md` with title, author, URL, and date accessed
- Re-running `ingest.py` (the script is idempotent thanks to deterministic IDs)

### Chunking strategy

- Chunk size: 500 tokens, 50-token overlap
- Use `tiktoken` for token counting (`cl100k_base` encoding — works fine for Claude content despite being an OpenAI tokenizer)
- One chunk = one Pinecone vector
- Chunk ID format: `<source_slug>__<chunk_index>` (e.g. `hyrox-guide__0042`). Deterministic so re-running ingest doesn't duplicate.

### Embeddings

Use OpenAI `text-embedding-3-small` via the official `openai` Python client. Cost is negligible for this volume (~$0.005 for the full corpus). Document the choice in the script header.

### Retrieval flow

1. Query → embed
2. Pinecone top-k (k=10)
3. Cohere rerank → top 3
4. Return the 3 chunks with source title, chunk text, and similarity score

### Metadata on each vector

```json
{
  "source": "hyrox-guide",
  "source_title": "Hyrox Training Guide 2025",
  "page": 42,
  "chunk_index": 17,
  "text": "<the chunk content>"
}
```

The `source_title` is what the agent will cite. Keep it human-readable.

## Quality bar

After ingestion, manually run these 3 queries and confirm relevance:

1. "best meal pre-workout for Hyrox training"
2. "how to pace the SkiErg in a Hyrox race"
3. "taper protocol for a first Hyrox"

If any of these returns clearly irrelevant top-3 results, do not ship — re-tune chunking or rerank parameters first.
