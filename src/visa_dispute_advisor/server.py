"""FastMCP server — VISA Dispute Advisor.

Exposes two read-only tools:
    search_visa_rules(scenario)  → list[dict]
    query_warehouse(merchant_id) → dict

Run with:
    uv run visa-advisor
"""

from __future__ import annotations

from dotenv import load_dotenv
from fastmcp import FastMCP

from visa_dispute_advisor import chroma_store, sqlite_store

load_dotenv()

mcp = FastMCP(
    name="visa-dispute-advisor",
    instructions=(
        "You are a VISA dispute advisory assistant. "
        "Always call search_visa_rules first to find applicable VISA conditions, "
        "then call query_warehouse with the merchant_id to retrieve the merchant's "
        "dispute history. Combine both results to emit a structured recommendation: "
        "ACCEPT DISPUTE | REJECT DISPUTE | REQUEST MORE EVIDENCE."
    ),
)


@mcp.tool()
def search_visa_rules(scenario: str) -> list[dict]:
    """Search VISA Dispute Management Guidelines for rules relevant to a dispute.

    Args:
        scenario: Free-text description of the dispute (cardholder claim, merchant
                  response, transaction type, etc.).

    Returns:
        A ranked list of matching VISA rule candidates, each containing:
            condition_id  – e.g. "13.1"
            title         – section heading
            snippet       – relevant text excerpt
            score         – cosine similarity score (0–1, higher = more relevant)
    """
    return chroma_store.search(scenario)


@mcp.tool()
def query_warehouse(merchant_id: str) -> dict:
    """Retrieve the dispute history for a merchant from the data warehouse.

    Args:
        merchant_id: The merchant identifier (e.g. "MER-001").

    Returns:
        A dict containing:
            merchant_id   – the queried ID
            merchant_name – registered name (or None)
            total_cases   – total number of dispute cases on record
            resolutions   – breakdown: {merchant_won, merchant_lost, settled, pending}
            cases         – list of individual case records (date, amount, type, res)
    """
    return sqlite_store.get_merchant_history(merchant_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
