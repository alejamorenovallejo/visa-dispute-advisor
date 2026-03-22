from __future__ import annotations

"""Integration tests for the two MCP tool functions."""

import os

import pytest


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    db = tmp_path / "test_warehouse.db"
    monkeypatch.setenv("WAREHOUSE_DB_PATH", str(db))
    monkeypatch.setenv("CHROMA_PATH", str(tmp_path / "chroma"))
    import visa_dispute_advisor.sqlite_store as store
    store._engine = None
    store._SessionLocal = None
    yield
    store._engine = None
    store._SessionLocal = None


def test_query_warehouse_returns_dict():
    from visa_dispute_advisor.server import query_warehouse
    from visa_dispute_advisor import sqlite_store

    sqlite_store.upsert_case(
        merchant_id="MER-001",
        case_id="CASE-001",
        merchant_name="Tech Store Guatemala",
        dispute_date="2026-01-01",
        amount=450.0,
        dispute_type="Merchandise Not Received",
        resolution="merchant_won",
    )
    result = query_warehouse("MER-001")
    assert isinstance(result, dict)
    assert result["merchant_id"] == "MER-001"
    assert result["total_cases"] == 1
    assert "resolutions" in result
    assert "cases" in result


def test_query_warehouse_unknown_merchant():
    from visa_dispute_advisor.server import query_warehouse

    result = query_warehouse("MER-NONE")
    assert result["total_cases"] == 0
    assert result["cases"] == []


def test_search_visa_rules_returns_list_when_empty():
    from visa_dispute_advisor.server import search_visa_rules

    # Empty collection — should return [] not raise
    result = search_visa_rules("unauthorized transaction")
    assert isinstance(result, list)
