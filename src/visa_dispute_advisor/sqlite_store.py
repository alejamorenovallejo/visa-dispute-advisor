from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Date,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

WAREHOUSE_DB_PATH = os.getenv("WAREHOUSE_DB_PATH", "data/warehouse.db")

_engine: Any = None
_SessionLocal: Any = None


def _get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{WAREHOUSE_DB_PATH}",
            connect_args={"check_same_thread": False},
        )
        _SessionLocal = sessionmaker(bind=_engine)
        Base.metadata.create_all(_engine)
    return _engine


def _get_session() -> Session:
    _get_engine()
    return _SessionLocal()


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


class DisputeCase(Base):
    __tablename__ = "dispute_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String(64), nullable=False, index=True)
    case_id = Column(String(64), nullable=False)
    merchant_name = Column(String(256), nullable=True)
    dispute_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=True)
    dispute_type = Column(String(128), nullable=True)
    # merchant_won | merchant_lost | settled | pending
    resolution = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("merchant_id", "case_id", name="uq_merchant_case"),
        Index("ix_merchant_id", "merchant_id"),
    )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


_ALLOWED_RESOLUTIONS = {"merchant_won", "merchant_lost", "settled", "pending"}
_BLOCKED_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "pragma",
    "attach",
)


def execute_readonly(raw_sql: str) -> list[dict]:
    """Execute *raw_sql* only if it is a SELECT statement.

    Raises ValueError for any non-SELECT or potentially destructive statement.
    Returns a list of row dicts.
    """
    normalised = raw_sql.strip().lower()
    if not normalised.startswith("select"):
        raise ValueError(f"Only SELECT statements are allowed. Got: {raw_sql[:80]!r}")
    for kw in _BLOCKED_KEYWORDS:
        if f" {kw} " in f" {normalised} ":
            raise ValueError(f"Blocked keyword '{kw}' detected in query.")

    with _get_session() as session:
        rows = session.execute(text(raw_sql)).mappings().all()
        return [dict(r) for r in rows]


def upsert_case(
    merchant_id: str,
    case_id: str,
    merchant_name: str | None = None,
    dispute_date: str | None = None,
    amount: float | None = None,
    dispute_type: str | None = None,
    resolution: str | None = None,
    notes: str | None = None,
) -> None:
    """Insert or update a dispute case (UNIQUE on merchant_id, case_id)."""
    from datetime import date

    if resolution and resolution not in _ALLOWED_RESOLUTIONS:
        raise ValueError(
            f"Invalid resolution: {resolution!r}. Must be one of {_ALLOWED_RESOLUTIONS}"
        )

    parsed_date: date | None = None
    if dispute_date:
        parsed_date = date.fromisoformat(dispute_date)

    _get_engine()
    with Session(_engine) as session:
        existing = (
            session.query(DisputeCase)
            .filter_by(merchant_id=merchant_id, case_id=case_id)
            .first()
        )
        if existing:
            if merchant_name is not None:
                existing.merchant_name = merchant_name
            if parsed_date is not None:
                existing.dispute_date = parsed_date
            if amount is not None:
                existing.amount = amount
            if dispute_type is not None:
                existing.dispute_type = dispute_type
            if resolution is not None:
                existing.resolution = resolution
            if notes is not None:
                existing.notes = notes
        else:
            session.add(
                DisputeCase(
                    merchant_id=merchant_id,
                    case_id=case_id,
                    merchant_name=merchant_name,
                    dispute_date=parsed_date,
                    amount=amount,
                    dispute_type=dispute_type,
                    resolution=resolution,
                    notes=notes,
                )
            )
        session.commit()


def get_merchant_history(merchant_id: str) -> dict:
    """Return dispute history for *merchant_id* as a structured dict.

    Returns:
        {
            merchant_id: str,
            merchant_name: str | None,
            total_cases: int,
            resolutions: {merchant_won: int, merchant_lost: int, settled: int},
            cases: list[dict],
        }
    """
    _get_engine()
    with Session(_engine) as session:
        rows = (
            session.query(DisputeCase)
            .filter_by(merchant_id=merchant_id)
            .order_by(DisputeCase.dispute_date.desc())
            .all()
        )

    if not rows:
        return {
            "merchant_id": merchant_id,
            "merchant_name": None,
            "total_cases": 0,
            "resolutions": {
                "merchant_won": 0,
                "merchant_lost": 0,
                "settled": 0,
                "pending": 0,
            },
            "cases": [],
        }

    resolutions: dict[str, int] = {
        "merchant_won": 0,
        "merchant_lost": 0,
        "settled": 0,
        "pending": 0,
    }
    cases_list: list[dict] = []
    merchant_name: str | None = None

    for row in rows:
        if merchant_name is None and row.merchant_name:
            merchant_name = row.merchant_name
        res = row.resolution or "pending"
        resolutions[res] = resolutions.get(res, 0) + 1
        cases_list.append(
            {
                "case_id": row.case_id,
                "dispute_date": (
                    row.dispute_date.isoformat() if row.dispute_date else None
                ),
                "amount": row.amount,
                "dispute_type": row.dispute_type,
                "resolution": row.resolution,
                "notes": row.notes,
            }
        )

    return {
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "total_cases": len(rows),
        "resolutions": resolutions,
        "cases": cases_list,
    }


def ensure_schema() -> None:
    """Create tables if they don't exist yet."""
    _get_engine()
