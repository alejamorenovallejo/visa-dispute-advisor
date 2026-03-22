from __future__ import annotations

"""Tests for sqlite_store — readonly guard and upsert logic."""

import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Point WAREHOUSE_DB_PATH at a temp file for each test."""
    db = tmp_path / "test_warehouse.db"
    monkeypatch.setenv("WAREHOUSE_DB_PATH", str(db))
    # Reset the cached engine so each test gets a fresh DB
    import visa_dispute_advisor.sqlite_store as store
    store._engine = None
    store._SessionLocal = None
    yield
    store._engine = None
    store._SessionLocal = None


def test_upsert_and_retrieve():
    from visa_dispute_advisor import sqlite_store

    sqlite_store.upsert_case(
        merchant_id="MER-TEST",
        case_id="CASE-001",
        merchant_name="Test Merchant",
        dispute_date="2026-01-01",
        amount=100.0,
        dispute_type="Merchandise Not Received",
        resolution="merchant_won",
        notes="Test note",
    )
    result = sqlite_store.get_merchant_history("MER-TEST")
    assert result["total_cases"] == 1
    assert result["merchant_name"] == "Test Merchant"
    assert result["resolutions"]["merchant_won"] == 1
    assert result["cases"][0]["case_id"] == "CASE-001"


def test_upsert_is_idempotent():
    from visa_dispute_advisor import sqlite_store

    for _ in range(3):
        sqlite_store.upsert_case(
            merchant_id="MER-TEST",
            case_id="CASE-001",
            merchant_name="Test Merchant",
            dispute_date="2026-01-01",
            amount=100.0,
            dispute_type="Merchandise Not Received",
            resolution="merchant_won",
        )
    result = sqlite_store.get_merchant_history("MER-TEST")
    assert result["total_cases"] == 1


def test_unknown_merchant_returns_empty():
    from visa_dispute_advisor import sqlite_store

    result = sqlite_store.get_merchant_history("MER-UNKNOWN")
    assert result["total_cases"] == 0
    assert result["cases"] == []


def test_execute_readonly_rejects_insert():
    from visa_dispute_advisor import sqlite_store

    with pytest.raises(ValueError, match="Only SELECT"):
        sqlite_store.execute_readonly("INSERT INTO dispute_cases VALUES (1)")


def test_execute_readonly_rejects_drop():
    from visa_dispute_advisor import sqlite_store

    with pytest.raises(ValueError):
        sqlite_store.execute_readonly("DROP TABLE dispute_cases")


def test_execute_readonly_accepts_select():
    from visa_dispute_advisor import sqlite_store

    sqlite_store.ensure_schema()
    rows = sqlite_store.execute_readonly("SELECT 1 AS val")
    assert rows == [{"val": 1}]


def test_invalid_resolution_raises():
    from visa_dispute_advisor import sqlite_store

    with pytest.raises(ValueError, match="Invalid resolution"):
        sqlite_store.upsert_case(
            merchant_id="MER-TEST",
            case_id="CASE-BAD",
            resolution="unknown_status",
        )
