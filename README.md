# MCP Coding Challenge

MCP server exposing read-only SQL access to a database. Three tools — `list_tables`, `get_table_metadata`, `execute_query`. SQLite and Postgres are wired up today - Extendable to other backends (Snowflake, BigQuery, ...) without changes to the MCP/Tool layer.

## Setup

By default the server uses the SQLite backend pointed at `data/titanic.db`. Drop the Titanic SQLite file there and no further config is required to start the server.

To change the defaults, e.g. switch to Postgres, point at a different SQLite file or rename the server, set the corresponding `DB_MCP__*` environment variables. For local development, copying `.env.example` to `.env` is the easiest way. 

```
cp .env.example .env
```
In production, inject the vars via the respective runtime platform.

## Dev

```
uv sync
uv run uvicorn db_mcp_server.asgi:create_app --factory --reload --reload-dir src --port 8000
```

## Connecting

The server runs at `http://localhost:8000/<name>/mcp`, where `<name>` is `DB_MCP__NAME` (default `titanic`). 

Easiest way to test is via the MCP Inspector: `npx @modelcontextprotocol/inspector`

## Tests

Unit tests use SQLite + a dummy MCP backend. Fast and self-contained:

```
uv run pytest
```

### Integration tests

Integration tests run end-to-end against a real Postgres (in an isolated schema) and are excluded by default. Bring one up via Docker first (see below), then:

```
uv run pytest -m integration
```

## Docker

The compose manifest defines two services: `postgres` and `mcp`. Bring them up separately so data can be loaded in between:
```
docker compose up -d postgres
```

Load the Titanic data with pgloader:
```
brew install pgloader
pgloader \
  sqlite://$(pwd)/data/titanic.db \
  postgresql://postgres:postgres@localhost:5432/default
```

Start the MCP
```
docker compose up mcp
```

## Submission Notes

The biggest gap in the current implementation is, I think, **missing authorization**. I planned to implement it in a basic form and wire up a dummy IdP for testing but didn't get there considering a ~8h timeframe. The DB user is read-only, so writes are rejected at the engine level. For production I'd add identity via e.g. an Identity Aware Proxy or similar for access control plus FastMCP-native scopes for per-tool authorization. Both take real time to do properly and I prioritized code architecture and extensibility instead.
