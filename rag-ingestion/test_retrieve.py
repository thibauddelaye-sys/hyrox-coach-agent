# rag-ingestion/test_retrieve.py

"""
Quick retrieval smoke-test — run AFTER ingestion.
Usage:  python rag-ingestion/test_retrieve.py "your query here"

Embeds the query, queries Pinecone for the top-5 matches,
and prints each result with its source and a text preview.
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

TOP_K = 5
PREVIEW_CHARS = 300  # How many characters of the chunk text to display


def main() -> None:
    load_dotenv()

    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print("Usage: python rag-ingestion/test_retrieve.py \"your query here\"")
        sys.exit(1)

    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
    embed_model = os.environ["OPENAI_MODEL_EMBEDDING"]

    print(f"\n🔍  Query: \"{query}\"")
    print(f"    Embedding with {embed_model} …")

    response = openai_client.embeddings.create(model=embed_model, input=[query])
    query_vector = response.data[0].embedding

    print(f"    Querying Pinecone for top-{TOP_K} matches …\n")

    results = index.query(
        vector=query_vector,
        top_k=TOP_K,
        include_metadata=True,
    )

    matches = results.get("matches", [])
    if not matches:
        print("❌  No results returned. Check that ingestion completed successfully.")
        return

    print(f"{'─'*70}")
    for rank, match in enumerate(matches, start=1):
        meta = match.get("metadata", {})
        score = match.get("score", 0.0)
        source = meta.get("source_name_human", meta.get("source_id", "Unknown"))
        page = meta.get("page_estimate", "?")
        chunk_idx = meta.get("chunk_index", "?")
        text_preview = meta.get("text", "")[:PREVIEW_CHARS].replace("\n", " ")

        print(f"#{rank}  Score: {score:.4f}  |  Source: {source}  |  Page ~{page}  |  Chunk #{chunk_idx}")
        print(f"    {text_preview}{'…' if len(meta.get('text','')) > PREVIEW_CHARS else ''}")
        print(f"{'─'*70}")

    print(f"\n✅  Top-{TOP_K} results retrieved successfully.")


if __name__ == "__main__":
    main()
