# rag-ingestion

RAG knowledge base ingestion for the **Hyrox Coach Agent** project.

---

## Setup

```bash
pip install openai pinecone pypdf tiktoken python-dotenv
```

Make sure your `.env` file at the project root contains:

```
OPENAI_API_KEY=sk-proj-XXX
OPENAI_MODEL_EMBEDDING=text-embedding-3-small
PINECONE_API_KEY=pcsk_XXX
PINECONE_INDEX_NAME=hyrox-knowledge-base
PINECONE_ENVIRONMENT=us-east-1-aws
```

> **Important:** Create the Pinecone index manually in the Pinecone web UI  
> before running the script. Settings: **dimensions=1536, metric=cosine, serverless on AWS us-east-1**.  
> The script will NOT create the index — it only connects and upserts.

---

## How to run

From the **project root** (not from inside `rag-ingestion/`):

```bash
python rag-ingestion/ingest.py
```

The script will:

1. Scan `knowledge-base/sources/*.pdf` (sorted alphabetically)
2. Extract text from every page, skipping broken pages with a warning
3. Chunk each document into ~500-token segments with 50-token overlap
4. Embed each chunk via the OpenAI API (`text-embedding-3-small`)
5. Upsert all vectors to your Pinecone index in batches of 100

Progress is printed to the console every batch. You should see output like:

```
📂  Found 9 PDFs in 'knowledge-base/sources'
📄  Processing: 01_hyrox_training_manual.pdf  →  'HYROX Training Manual'
    Pages: 42  |  Chunks: 127
…
✅  Total chunks across all sources: 372
🚀  Starting embedding + upsert …
  🔢  Embedded 100/372 chunks …
  🔢  Embedded 200/372 chunks …
…
🏁  Ingestion complete in 148.3s — 372 chunks upserted.
```

### Expected runtime

**2–5 minutes** for ~137 pages (≈ 300–400 chunks), depending on OpenAI API latency.

### Idempotent re-runs

Running the script twice is safe. Chunk IDs are deterministic  
(`{source_id}__{chunk_index_zero_padded_4}`), so Pinecone simply overwrites  
existing vectors with the same content — no duplicates accumulate.

---

## Validating retrieval after ingestion

Run the smoke-test script with any free-text query:

```bash
python rag-ingestion/test_retrieve.py "carbohydrate loading before a race"
```

You will see the top-5 matching chunks with their source document, estimated page number, cosine similarity score, and a 300-character text preview.

---

## Inspecting results in the Pinecone web UI

After ingestion you can verify the index via the Pinecone console or with a quick Python snippet:

```python
from pinecone import Pinecone
import os
from dotenv import load_dotenv

load_dotenv()
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX_NAME"])

stats = index.describe_index_stats()
print(stats)
# Expected output:
# {'dimension': 1536, 'index_fullness': 0.0, 'namespaces': {'': {'vector_count': ~350}},
#  'total_vector_count': ~350}
```

`total_vector_count` should be in the **300–400 range** for the 9 base PDFs.
