import itertools
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import pydantic
from mcp import ServerSession
from mcp.server.fastmcp import Context, FastMCP

from db_mcp_server.db import AbstractDatabaseBackend, TableMetadata


class QueryResult(pydantic.BaseModel):
    rows: list[dict[str, Any]]
    count: int
    truncated: bool


def build(
    backend: AbstractDatabaseBackend, name: str, dialect: str, content_description: str
) -> FastMCP:

    @dataclass
    class MCPContext:
        backend: AbstractDatabaseBackend

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[MCPContext]:
        yield MCPContext(backend=backend)

    mcp = FastMCP(
        name,
        instructions=(
            f"Read-only SQL access. Dataset: {content_description}\n"
            f"SQL dialect: {dialect}\n"
            "\n"
            "Recommended Workflow:\n"
            "  1. `list_tables` to discover what's available.\n"
            "  2. `get_table_metadata` to learn columns, keys, "
            "      and (if the backend supports it) table/column descriptions.\n"
            "  3. `execute_query` with a SELECT statement. "
            "\n"
            "Write-operations are rejected by the read-only database user."
        ),
        lifespan=lifespan,
        stateless_http=True,
    )

    @mcp.tool()
    def list_tables(ctx: Context[ServerSession, MCPContext]) -> list[str]:
        """List all table names in the connected database.

        Use this as the first step when exploring an unfamiliar database. The
        returned names can be passed to `get_table_metadata` to learn the structure
        of specific tables before writing queries.
        """
        backend = ctx.request_context.lifespan_context.backend
        return backend.list_tables()

    @mcp.tool()
    def get_table_metadata(
        ctx: Context[ServerSession, MCPContext], tables: list[str] | None = None
    ) -> list[TableMetadata]:
        """Return structural metadata (columns, primary key, foreign keys, indexes)
        for one or more tables.

        Call this before writing queries that use joins, filters, or aggregations
        so you know the exact column names, types, and join keys. If `tables` is
        omitted, returns metadata for every table in the database.
        """
        backend = ctx.request_context.lifespan_context.backend
        return backend.get_table_metadata(tables)

    @mcp.tool()
    def execute_query(
        ctx: Context[ServerSession, MCPContext], query: str, limit: int | None = 100
    ) -> QueryResult:
        """Execute a read-only SQL SELECT statement.

        Each row is a `{column_name: value}` dict. Results are capped at `limit`
        rows. When `truncated` is true, refine the query (add `WHERE` or aggregate).
        Raise the limit with caution to prevent context bloat.

        Write operations are rejected by the read-only database user.
        """
        backend = ctx.request_context.lifespan_context.backend
        raw_rows = backend.execute_query(query)

        if limit is None:
            rows = list(raw_rows)
            truncated = False
        else:
            fetched = list(itertools.islice(raw_rows, limit + 1))
            truncated = len(fetched) > limit
            rows = fetched[:limit]

        return QueryResult(rows=rows, count=len(rows), truncated=truncated)

    return mcp
