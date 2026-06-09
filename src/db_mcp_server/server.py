from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp import ServerSession
from mcp.server.fastmcp import Context, FastMCP

from db_mcp_server.bootstrap import bootstrap_db_backend
from db_mcp_server.config import Config
from db_mcp_server.db import AbstractDatabaseBackend


@dataclass
class MCPContext:
    backend: AbstractDatabaseBackend


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[MCPContext]:
    config = Config()
    backend = bootstrap_db_backend(config)
    yield MCPContext(backend=backend)


mcp = FastMCP(
    lifespan=lifespan,
)


@mcp.tool()
def list_tables(ctx: Context[ServerSession, MCPContext]) -> list[str]:
    backend = ctx.request_context.lifespan_context.backend
    return backend.list_tables()


@mcp.tool()
def get_table_metadata(
    ctx: Context[ServerSession, MCPContext], tables: list[str] | None = None
) -> list[dict[str, Any]]:
    backend = ctx.request_context.lifespan_context.backend
    return backend.get_table_metadata(tables)


@mcp.tool()
def execute_query(ctx: Context[ServerSession, MCPContext], query: str) -> list[dict[str, Any]]:
    backend = ctx.request_context.lifespan_context.backend
    return list(backend.execute_query(query))


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
