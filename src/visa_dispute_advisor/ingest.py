"""PDF → ChromaDB + SQLite ingestion pipeline.

Usage:
    uv run python -m visa_dispute_advisor.ingest
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

import pdfplumber
import polars as pl
from dotenv import load_dotenv

from visa_dispute_advisor import chroma_store, sqlite_store

load_dotenv()

VISA_PDF_PATH = os.getenv(
    "VISA_PDF_PATH", "data/merchants-dispute-management-guidelines.pdf"
)
CHUNK_MAX_CHARS = 1_200
CHUNK_OVERLAP_CHARS = 200

# Regex to detect VISA condition headings like "13.1", "11.2.3", etc.
_CONDITION_PATTERN = re.compile(
    r"^(?P<id>\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\s+(?P<title>.+)$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _chunk_text(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split *text* into overlapping chunks of at most *max_chars* characters."""
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def chunk_pdf(pdf_path: str) -> list[tuple[str, str, str]]:
    """Parse *pdf_path* and return a list of (condition_id, title, text) tuples.

    Each tuple represents one searchable chunk.  Sections without a detected
    condition heading receive an empty condition_id.
    """
    raw_pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            raw_pages.append(page_text)

    full_text = "\n".join(raw_pages)

    # Split on detected condition headings to associate text with conditions
    segments: list[tuple[str, str, str]] = []  # (condition_id, title, body)
    last_end = 0
    current_id = ""
    current_title = "Preamble"

    for match in _CONDITION_PATTERN.finditer(full_text):
        body = full_text[last_end : match.start()].strip()
        if body:
            segments.append((current_id, current_title, body))
        current_id = match.group("id")
        current_title = match.group("title").strip()
        last_end = match.end()

    # trailing text
    tail = full_text[last_end:].strip()
    if tail:
        segments.append((current_id, current_title, tail))

    # Convert segments to a Polars DataFrame for transforms, then explode chunks
    df = pl.DataFrame(
        {
            "condition_id": [s[0] for s in segments],
            "title": [s[1] for s in segments],
            "body": [s[2] for s in segments],
        }
    )

    # Explode each body into overlapping sub-chunks
    rows: list[tuple[str, str, str]] = []
    for row in df.iter_rows(named=True):
        sub_chunks = _chunk_text(row["body"], CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS)
        for chunk in sub_chunks:
            rows.append((row["condition_id"], row["title"], chunk))

    return rows


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


def _make_chunk_id(condition_id: str, title: str, text: str, idx: int) -> str:
    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    safe_cid = re.sub(r"[^a-zA-Z0-9_-]", "_", condition_id or "preamble")
    return f"{safe_cid}_{idx}_{digest}"


def ingest_pdf(pdf_path: str) -> int:
    """Parse *pdf_path*, embed chunks and store them in ChromaDB.

    Returns the number of chunks ingested.
    """
    if not os.path.exists(pdf_path):
        print(f"[ingest] ERROR: PDF not found at {pdf_path}", file=sys.stderr)
        return 0

    print(f"[ingest] Parsing {pdf_path} …")
    raw_chunks = chunk_pdf(pdf_path)
    print(f"[ingest] Extracted {len(raw_chunks)} chunks")

    chroma_store.reset_collection()

    batch_size = 100
    total = 0
    for batch_start in range(0, len(raw_chunks), batch_size):
        batch = raw_chunks[batch_start : batch_start + batch_size]
        prepared = [
            (
                _make_chunk_id(c[0], c[1], c[2], batch_start + i),
                c[0],
                c[1],
                c[2],
            )
            for i, c in enumerate(batch)
        ]
        chroma_store.upsert_chunks(prepared)
        total += len(prepared)
        print(f"[ingest]   upserted {total}/{len(raw_chunks)} chunks", end="\r")

    print(f"\n[ingest] ChromaDB ingestion complete — {total} chunks stored")
    return total


def ingest_csv(csv_path: str) -> int:
    """Load *csv_path* into SQLite using Polars.

    Returns the number of rows processed.
    """
    if not os.path.exists(csv_path):
        print(f"[ingest] No CSV found at {csv_path}, skipping.", file=sys.stderr)
        return 0

    print(f"[ingest] Loading {csv_path} …")
    df = pl.read_csv(csv_path)

    # Normalise column names to lower_snake_case
    df = df.rename({c: c.lower().replace(" ", "_") for c in df.columns})

    required = {"merchant_id", "case_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    sqlite_store.ensure_schema()
    count = 0
    for row in df.iter_rows(named=True):
        sqlite_store.upsert_case(
            merchant_id=str(row["merchant_id"]),
            case_id=str(row["case_id"]),
            merchant_name=row.get("merchant_name"),
            dispute_date=str(row["dispute_date"]) if row.get("dispute_date") else None,
            amount=float(row["amount"]) if row.get("amount") is not None else None,
            dispute_type=row.get("dispute_type"),
            resolution=row.get("resolution"),
            notes=row.get("notes"),
        )
        count += 1

    print(f"[ingest] SQLite ingestion complete — {count} rows upserted")
    return count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    pdf_path = VISA_PDF_PATH
    csv_path = os.getenv("DISPUTE_CSV_PATH", "data/dispute_cases.csv")

    ingest_pdf(pdf_path)
    ingest_csv(csv_path)
    print("[ingest] Done.")


if __name__ == "__main__":
    main()
