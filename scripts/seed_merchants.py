from __future__ import annotations

"""Seed demo merchant dispute data into SQLite.

Uses Polars for all data transforms.

Usage:
    uv run python scripts/seed_merchants.py
"""

import os
import sys

# Allow running from the project root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import polars as pl
from dotenv import load_dotenv

load_dotenv()

from visa_dispute_advisor import sqlite_store  # noqa: E402

CSV_PATH = os.getenv("DISPUTE_CSV_PATH", "data/dispute_cases.csv")


def load_and_transform(csv_path: str) -> pl.DataFrame:
    """Load dispute_cases.csv and apply Polars transforms.

    Transforms applied:
        - Normalise column names to lower_snake_case
        - Cast amount to Float64
        - Fill null notes with empty string
        - Filter out rows missing merchant_id or case_id
    """
    df = pl.read_csv(csv_path, infer_schema_length=1000)

    # Normalise column names
    df = df.rename({c: c.lower().replace(" ", "_") for c in df.columns})

    # Cast types
    df = df.with_columns(
        pl.col("amount").cast(pl.Float64, strict=False),
    )

    # Fill nulls
    if "notes" in df.columns:
        df = df.with_columns(pl.col("notes").fill_null(""))

    # Drop rows without a key
    df = df.filter(
        pl.col("merchant_id").is_not_null() & pl.col("case_id").is_not_null()
    )

    return df


def seed(csv_path: str) -> int:
    """Read *csv_path* and upsert all rows into SQLite.

    Returns the number of rows seeded.
    """
    if not os.path.exists(csv_path):
        print(f"[seed] CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    df = load_and_transform(csv_path)
    print(f"[seed] Loaded {len(df)} rows from {csv_path}")

    sqlite_store.ensure_schema()
    count = 0
    for row in df.iter_rows(named=True):
        sqlite_store.upsert_case(
            merchant_id=str(row["merchant_id"]),
            case_id=str(row["case_id"]),
            merchant_name=row.get("merchant_name"),
            dispute_date=str(row["dispute_date"]) if row.get("dispute_date") else None,
            amount=row.get("amount"),
            dispute_type=row.get("dispute_type"),
            resolution=row.get("resolution"),
            notes=row.get("notes") or None,
        )
        count += 1

    print(f"[seed] Seeded {count} cases into SQLite")
    return count


def main() -> None:
    seeded = seed(CSV_PATH)

    # Summary using Polars
    df = load_and_transform(CSV_PATH)
    summary = (
        df.group_by("merchant_id")
        .agg(
            pl.len().alias("total_cases"),
            (pl.col("resolution") == "merchant_won").sum().alias("won"),
            (pl.col("resolution") == "merchant_lost").sum().alias("lost"),
            (pl.col("resolution") == "settled").sum().alias("settled"),
        )
        .sort("merchant_id")
    )
    print("\n[seed] Merchant summary:")
    import io
    buf = io.StringIO()
    summary.write_csv(buf)
    print(buf.getvalue())
    print(f"\n[seed] Done — {seeded} rows upserted.")


if __name__ == "__main__":
    main()
