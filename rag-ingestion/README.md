# RAG ingestion

One-shot script that reads `knowledge-base/`, chunks, embeds, and upserts vectors to Pinecone. Plus a retrieval helper used by both the n8n workflows (via HTTP) and the local dev workflow.

## Run

```bash
# From repo root
pip install -r requirements.txt
python rag-ingestion/ingest.py
python rag-ingestion/retrieve.py  # sanity check with the 3 test queries
```

## Files (to be added in S2-R2)

- `ingest.py` — the ingestion pipeline
- `retrieve.py` — `search_knowledge_base(query)` function + `__main__` test
- `strava-bootstrap.py` — one-shot script to generate the initial Strava refresh token (used in S1-C1)

See `skills/rag-ingestion/SKILL.md` for the conventions all scripts here must follow.
