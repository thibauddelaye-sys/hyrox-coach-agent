# rag-ingestion/ingest.py

"""
Ingest 9 Hyrox knowledge base PDFs into Pinecone.
Run from project root: python rag-ingestion/ingest.py
"""

import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv
import tiktoken
from pypdf import PdfReader
from openai import OpenAI
from pinecone import Pinecone

# --- Config ---
SOURCES_DIR = Path("knowledge-base/sources")
CHUNK_TOKENS = 500
OVERLAP_TOKENS = 50
EMBED_BATCH_SIZE = 100   # OpenAI accepts up to 2048, but 100 is safer for rate limits
UPSERT_BATCH_SIZE = 100  # Pinecone upsert limit

# Acronym overrides for humanize_source_id()
ACRONYM_OVERRIDES = {
    "Issn": "ISSN",
    "Hyrox": "HYROX",
    "Goruck": "GORUCK",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: Path) -> tuple[str, int]:
    """
    Extract concatenated text from all pages of a PDF.
    Skips broken/malformed pages with a warning instead of crashing.
    Returns (full_text, total_pages_attempted).
    """
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    pages_text: list[str] = []

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
            pages_text.append(text)
        except Exception as exc:
            print(f"  ⚠️  WARNING: skipping page {page_num}/{total_pages} of "
                  f"'{pdf_path.name}' — {exc}")

    return "\n".join(pages_text), total_pages


def chunk_text(
    text: str,
    tokenizer: tiktoken.Encoding,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """
    Sliding-window token-based chunking.
    Encodes full text → slides a window of `chunk_size` tokens
    with a `overlap`-token step-back between chunks.
    Decodes each window back to a string before returning.
    """
    tokens = tokenizer.encode(text)
    chunks: list[str] = []

    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_str = tokenizer.decode(chunk_tokens)
        # Only keep non-empty, non-whitespace chunks
        if chunk_str.strip():
            chunks.append(chunk_str)
        # Advance by (chunk_size - overlap) so the next chunk shares `overlap` tokens
        start += chunk_size - overlap

    return chunks


def source_id_from_filename(filename: str) -> str:
    """
    '03_issn_nutrient_timing_2017.pdf'  →  '03_issn_nutrient_timing_2017'
    """
    return Path(filename).stem


def humanize_source_id(source_id: str) -> str:
    """
    '03_issn_nutrient_timing_2017'  →  'ISSN Nutrient Timing 2017'

    Steps:
      1. Strip the leading NN_ numeric prefix.
      2. Replace underscores with spaces.
      3. Title-case the result.
      4. Apply acronym overrides dict.
    """
    # Remove leading digits and underscore, e.g. "03_"
    label = re.sub(r"^\d+_", "", source_id)
    label = label.replace("_", " ").title()

    # Apply acronym overrides (e.g. "Issn" → "ISSN")
    for original, replacement in ACRONYM_OVERRIDES.items():
        label = label.replace(original, replacement)

    return label


def embed_with_retry(
    client: OpenAI,
    model: str,
    texts: list[str],
    retry_wait: float = 5.0,
) -> list[list[float]]:
    """
    Call the OpenAI Embeddings API.
    On the first failure, waits `retry_wait` seconds and tries once more.
    Raises on the second consecutive failure so we never silently corrupt the index.
    """
    for attempt in range(2):
        try:
            response = client.embeddings.create(model=model, input=texts)
            # The API returns embeddings in the same order as the input
            return [item.embedding for item in response.data]
        except Exception as exc:
            if attempt == 0:
                print(f"  ⚠️  Embedding API error (attempt 1): {exc} — retrying in {retry_wait}s …")
                time.sleep(retry_wait)
            else:
                raise RuntimeError(
                    f"Embedding API failed twice in a row: {exc}"
                ) from exc
    # Unreachable, but keeps type checker happy
    raise RuntimeError("embed_with_retry: unexpected exit")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    start_time = time.time()

    load_dotenv()
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index = pc.Index(os.environ["PINECONE_INDEX_NAME"])
    embed_model = os.environ["OPENAI_MODEL_EMBEDDING"]

    tokenizer = tiktoken.get_encoding("cl100k_base")

    pdfs = sorted(SOURCES_DIR.glob("*.pdf"))
    print(f"\n📂  Found {len(pdfs)} PDFs in '{SOURCES_DIR}'")
    if not pdfs:
        print("No PDFs found — check SOURCES_DIR path. Exiting.")
        return

    # -----------------------------------------------------------------------
    # Step 1 — Extract text from each PDF and build chunks
    # -----------------------------------------------------------------------
    # Each element: (chunk_id: str, text: str, metadata: dict)
    all_chunks: list[tuple[str, str, dict]] = []

    for pdf_path in pdfs:
        source_id = source_id_from_filename(pdf_path.name)
        source_name = humanize_source_id(source_id)

        print(f"\n📄  Processing: {pdf_path.name}  →  '{source_name}'")

        full_text, total_pages = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(full_text, tokenizer, CHUNK_TOKENS, OVERLAP_TOKENS)
        total_chunks_this_doc = len(chunks)

        print(f"    Pages: {total_pages}  |  Chunks: {total_chunks_this_doc}")

        for chunk_idx, chunk_text_str in enumerate(chunks):
            chunk_id = f"{source_id}__{chunk_idx:04d}"

            # Heuristic page estimate: distribute chunks evenly over pages
            page_estimate = (
                round(chunk_idx * total_pages / total_chunks_this_doc) + 1
                if total_chunks_this_doc > 0
                else 1
            )

            metadata = {
                "source_id": source_id,
                "source_name_human": source_name,
                "chunk_index": chunk_idx,
                "page_estimate": page_estimate,
                "text": chunk_text_str,
            }

            all_chunks.append((chunk_id, chunk_text_str, metadata))

    total = len(all_chunks)
    print(f"\n✅  Total chunks across all sources: {total}")

    # -----------------------------------------------------------------------
    # Step 2 — Embed in batches, then upsert to Pinecone
    # -----------------------------------------------------------------------
    print(f"\n🚀  Starting embedding + upsert  (embed_batch={EMBED_BATCH_SIZE}, "
          f"upsert_batch={UPSERT_BATCH_SIZE})")

    upsert_buffer: list[dict] = []

    for batch_start in range(0, total, EMBED_BATCH_SIZE):
        batch = all_chunks[batch_start: batch_start + EMBED_BATCH_SIZE]
        texts = [c[1] for c in batch]

        # --- Embed ---
        embeddings = embed_with_retry(openai_client, embed_model, texts)

        # --- Build Pinecone vectors ---
        vectors = [
            {
                "id": chunk_id,
                "values": embedding,
                "metadata": metadata,
            }
            for (chunk_id, _text, metadata), embedding in zip(batch, embeddings)
        ]
        upsert_buffer.extend(vectors)

        # Log progress every 10 chunks (approximately)
        chunks_done = batch_start + len(batch)
        if (batch_start // EMBED_BATCH_SIZE) % max(1, (10 // EMBED_BATCH_SIZE)) == 0 or chunks_done >= total:
            print(f"  🔢  Embedded {chunks_done}/{total} chunks …")

        # --- Upsert when buffer is full or we've finished all chunks ---
        while len(upsert_buffer) >= UPSERT_BATCH_SIZE:
            to_upsert = upsert_buffer[:UPSERT_BATCH_SIZE]
            index.upsert(vectors=to_upsert)
            upsert_buffer = upsert_buffer[UPSERT_BATCH_SIZE:]

    # Flush remaining vectors
    if upsert_buffer:
        index.upsert(vectors=upsert_buffer)
        print(f"  📤  Flushed final {len(upsert_buffer)} vectors to Pinecone.")

    elapsed = time.time() - start_time
    print(f"\n🏁  Ingestion complete in {elapsed:.1f}s — {total} chunks upserted.")


if __name__ == "__main__":
    main()
