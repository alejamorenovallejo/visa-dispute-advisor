# VISA Dispute Advisor

A merchant dispute advisory system powered by the **VISA Dispute Management Guidelines**.

Given a dispute case, the system retrieves the applicable VISA conditions,
reasons over the merchant's response options and past dispute history, and
returns a structured recommendation.

Deployed as a **Model Context Protocol (MCP) server** — any MCP-compatible
client (GitHub Copilot, Claude Desktop, etc.) connects and drives the
reasoning loop using the two provided tools.

---

## Architecture

```
MCP Client (GitHub Copilot / Claude Desktop / …)
  │  calls tools over MCP stdio transport
  ▼
FastMCP Server
  ├─► ChromaDB  (sentence-transformers embeddings — local, no API key)
  │     semantic search over VISA Dispute Management Guidelines PDF chunks
  └─► SQLite    (SQLAlchemy)
        merchant dispute history warehouse
```

No LLM runs server-side. The server is a pure retrieval layer.

---

## Tools

| Tool | Purpose |
| --- | --- |
| `search_visa_rules` | Semantic search over VISA Guidelines — start here |
| `query_warehouse` | Merchant dispute history lookup by merchant ID |

---

## Prerequisites

* [uv](https://docs.astral.sh/uv/) ≥ 0.5
* Python ≥ 3.11
* `data/visa_rules.pdf` — your copy of the VISA Dispute Management Guidelines PDF

---

## Setup

```bash
# 1. Clone
git clone https://github.com/your-username/visa-dispute-advisor.git
cd visa-dispute-advisor

# 2. Install dependencies
uv sync

# 3. Configure paths (defaults work out-of-the-box)
cp .env.example .env

# 4. Place VISA PDF
cp /path/to/merchants-dispute-management-guidelines.pdf data/visa_rules.pdf

# 5. Ingest VISA rules into vector store
uv run python -m visa_dispute_advisor.ingest

# 6. Seed demo merchant dispute history
uv run python scripts/seed_merchants.py
```

---

## Running the server

```bash
# stdio transport — for MCP clients
uv run visa-advisor

# HTTP transport with browser inspector — for development
uv run fastmcp dev src/visa_dispute_advisor/server.py
```

---

## Connecting a client

### GitHub Copilot (VS Code)

Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "visa-dispute-advisor": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "visa-advisor"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "visa-dispute-advisor": {
      "command": "uv",
      "args": ["run", "visa-advisor"],
      "cwd": "/absolute/path/to/visa-dispute-advisor"
    }
  }
}
```

---

## Typical advisory session

```
Dispute case:
  Merchant ID: MER-001 (Tech Store Guatemala)
  Cardholder claim: Item not received. Ordered a laptop online on
  2026-03-01, expected delivery 2026-03-10. Tracking shows "delivered"
  but customer denies receiving it. Amount: $450.00.
  Merchant response: Has carrier tracking proof showing delivery to
  the billing address.

Agent calls:
  1. search_visa_rules("customer claims item not received, merchant has tracking proof")
  2. query_warehouse("MER-001")

Recommendation: REJECT DISPUTE (favor merchant)
  Applicable rule: Condition 13.1 — Merchandise/Services Not Received.
  Merchant can provide tracking documentation proving delivery to the
  agreed address. Under Condition 13.1, this constitutes valid compelling
  evidence to dispute the chargeback.

  Merchant risk profile: LOW RISK — 2 of 3 prior disputes resolved in
  merchant's favor. No pattern of fraudulent behavior detected.

  Next steps:
  1. Request signed proof of delivery from carrier.
  2. Submit tracking number and delivery confirmation to acquirer.
  3. If cardholder insists, escalate to Visa arbitration.
```

---

## Development

```bash
uv run ruff check --fix src/
uv run ruff format src/
uv run pytest
```

See [AGENTS.md](AGENTS.md) for full contributor and agent guidance.

---

## License

MIT
