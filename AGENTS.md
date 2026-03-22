# AGENTS.md — VISA Dispute Advisor

Instruction material for AI coding agents (GitHub Copilot, Claude, etc.)
working on this repository.

---

## Project purpose

A **read-only MCP server** that surfaces VISA Dispute Management Guidelines data and a
merchant history warehouse as two structured tools. The agent reasoning loop
lives entirely in the **MCP client** (GitHub Copilot, Claude Desktop, …).
This server is the data and retrieval layer only — no LLM calls are made
server-side.

---

## Repository layout

```
src/visa_dispute_advisor/
  server.py          ← FastMCP tool definitions (authoritative interface)
  chroma_store.py    ← ChromaDB wrapper for semantic search over VISA PDF
  sqlite_store.py    ← SQLAlchemy DDL + CRUD helpers
  ingest.py          ← PDF → ChromaDB + SQLite ingestion pipeline

scripts/
  seed_merchants.py  ← Seeds demo merchant dispute data into SQLite

data/
  visa_rules.pdf     ← VISA Dispute Management Guidelines (not committed — add locally)
  dispute_cases.csv  ← Merchant dispute history seed data
  chroma/            ← Persisted ChromaDB vector store (generated)
  warehouse.db       ← SQLite database (generated)
```

---

## Tool contract (never break these signatures)

| Tool | Python signature | Returns |
| --- | --- | --- |
| `search_visa_rules` | `(scenario: str)` | `list[dict]` — candidates with condition_id, title, snippet, score |
| `query_warehouse` | `(merchant_id: str)` | `dict` — dispute history with total_cases, resolutions, cases list |

All tools are synchronous and return JSON-serialisable values. Do not add
`async` to tool functions without updating the FastMCP configuration.

---

## Technology choices

| Concern | Choice | Rationale |
| --- | --- | --- |
| MCP server | `fastmcp` | Pythonic, minimal boilerplate |
| Vector store | `chromadb` (persistent) | Local, no external service |
| Embeddings | `chromadb` `DefaultEmbeddingFunction` (`all-MiniLM-L6-v2` via ONNXRuntime) | No PyTorch / CUDA required |
| Relational DB | SQLite via `sqlalchemy` | Zero-config, file-based |
| PDF parsing | `pdfplumber` | Handles VISA PDF multi-column layout |
| Data transforms | `polars` | All ingestion transforms use Polars DataFrames |
| Package manager | `uv` | Fast, reproducible, single lock file |

---

## Coding conventions

* Python ≥ 3.11. Use `from __future__ import annotations` in every module.
* All data transformations in `ingest.py` and array/table operations in
  `seed_merchants.py` must use **Polars** — never pandas.
* Format with `ruff format`, lint with `ruff check --fix`.
* No secrets in source — all paths come from environment variables loaded
  via `python-dotenv` (see `.env.example`).
* `query_warehouse` must reject any non-SELECT statement before touching
  the database. The guard is in `sqlite_store.py::execute_readonly`.
* `dispute_cases` table has a UNIQUE constraint on `(merchant_id, case_id)`.
  Always use `upsert_case`, never raw INSERT in new code.

---

## Development commands

```bash
# Install all dependencies (creates .venv automatically)
uv sync

# Run the MCP server — stdio transport (default for MCP clients)
uv run visa-advisor

# Run with FastMCP dev inspector — browser UI on http://localhost:5173
uv run fastmcp dev src/visa_dispute_advisor/server.py

# Lint + format
uv run ruff check --fix src/
uv run ruff format src/

# Tests
uv run pytest
```

---

## Data pipeline commands

```bash
# 1. Place VISA PDF in data/
cp /path/to/merchants-dispute-management-guidelines.pdf data/visa_rules.pdf

# 2. Run ingestion (PDF → ChromaDB + SQLite)
uv run python -m visa_dispute_advisor.ingest

# 3. Seed demo merchant dispute history
uv run python scripts/seed_merchants.py
```

---

## Agent reasoning flow

The MCP client is expected to follow this sequence:

```
dispute case (free text, includes merchant_id)
  └─► search_visa_rules        ← always first; returns ranked VISA conditions
        └─► query_warehouse    ← call with merchant_id from the case
              └─► emit structured recommendation:
                    ACCEPT DISPUTE | REJECT DISPUTE | REQUEST MORE EVIDENCE
                    + applicable VISA condition(s) and required response steps
                    + merchant risk profile based on history
                    + recommended next steps for the acquirer
```

---

## Extending the system

### Adding a new tool

1. Define it as a `@mcp.tool()` decorated function in `server.py`.
2. Add its signature to the Tool contract table above.
3. Write a unit test in `tests/`.

### Improving semantic search coverage

Add new chunking strategies to the `chunk_pdf` function in `ingest.py`.
Chunks should follow the pattern `(condition_id, title, text)` so that
`search_visa_rules` can always return a structured `condition_id` alongside
the snippet. Re-run ingestion after any change to rebuild the collection.

### Changing the embedding model

Update `EMBEDDING_MODEL` in `chroma_store.py`, then delete `data/chroma/`
and re-run ingestion so the collection is rebuilt with the new model's
vector space.

---

## MCP client configuration

### GitHub Copilot (VS Code) — `.vscode/mcp.json`

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

### Generic MCP client — `mcp_config.json`

```json
{
  "mcpServers": {
    "visa-dispute-server": {
      "command": "uv",
      "args": ["run", "visa-advisor"],
      "cwd": "/absolute/path/to/visa-dispute-advisor",
      "env": {
        "WAREHOUSE_DB_PATH": "data/warehouse.db",
        "CHROMA_PATH": "data/chroma",
        "VISA_PDF_PATH": "data/visa_rules.pdf"
      }
    }
  }
}
```
