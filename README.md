# MCP Coding Challenge

MCP server exposing read-only SQL access to a database. Three tools — `list_tables`, `get_table_metadata`, `execute_query`. SQLite and Postgres are wired up today - Extendable to other backends (Snowflake, BigQuery, ...) without changes to the MCP/Tool layer.

## Setup

`.env` and the data file are not in the repo. Two one-off steps:

```
cp .env.example .env
```

Drop the Titanic SQLite file at `data/titanic.db`.

For the Postgres path, uncomment the Postgres block in `.env` and either bring up Postgres via Docker (see below) or point at any existing instance.

## Dev

```
uv sync
uv run uvicorn db_mcp_server.asgi:app --reload --reload-dir src --port 8000
```

## Connecting

The server runs at `http://localhost:8000/<name>/mcp`, where `<name>` is `DB_MCP__NAME` from `.env` (default `titanic`). 

Easiest way to test is via the MCP Inspector: `npx @modelcontextprotocol/inspector`

## Tests

```
uv run pytest
```

Unit tests use SQLite + a dummy MCP backend. 

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
  postgresql://titanic:titanic@localhost:5432/titanic
```

Start the MCP
```
docker compose up mcp
```
