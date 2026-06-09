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


def build(backend: AbstractDatabaseBackend, name: str) -> FastMCP:

    @dataclass
    class MCPContext:
        backend: AbstractDatabaseBackend

    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[MCPContext]:
        yield MCPContext(backend=backend)

    mcp = FastMCP(
        name,
        lifespan=lifespan,
    )

    @mcp.tool()
    def list_tables(ctx: Context[ServerSession, MCPContext]) -> list[str]:
        backend = ctx.request_context.lifespan_context.backend
        return backend.list_tables()

    @mcp.tool()
    def get_table_metadata(
        ctx: Context[ServerSession, MCPContext], tables: list[str] | None = None
    ) -> list[TableMetadata]:
        backend = ctx.request_context.lifespan_context.backend
        return backend.get_table_metadata(tables)

    @mcp.tool()
    def execute_query(
        ctx: Context[ServerSession, MCPContext], query: str, limit: int | None = 100
    ) -> QueryResult:
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
