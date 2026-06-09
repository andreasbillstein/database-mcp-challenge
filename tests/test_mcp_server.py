import unittest
from collections.abc import AsyncGenerator, Iterator
from typing import Any

import pytest
from mcp import ClientSession
from mcp.server import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session

from db_mcp_server import server
from db_mcp_server.db import PK, AbstractDatabaseBackend, TableMetadata
from db_mcp_server.server import QueryResult


def _stub_table(name: str) -> TableMetadata:
    return TableMetadata(
        name=name,
        columns=[],
        primary_key=PK(name=None, constrained_columns=[]),
        foreign_keys=[],
        indexes=[],
    )


@pytest.fixture
def mcp_server_success_responses() -> FastMCP:

    class DummyBackendSuccess(AbstractDatabaseBackend):
        def __init__(self) -> None:
            super().__init__()
            self._tables: list[TableMetadata] = [
                _stub_table("users"),
                _stub_table("orders"),
            ]

        def list_tables(self) -> list[str]:
            return [t.name for t in self._tables]

        def get_table_metadata(self, tables: list[str] | None) -> list[TableMetadata]:
            return self._tables if tables is None else [t for t in self._tables if t.name in tables]

        def execute_query(self, query: str) -> Iterator[dict[str, Any]]:
            return ({"user_id": i, "name": f"user_{i}", "query": query} for i in range(10))

        def close(self) -> None: ...

    backend = DummyBackendSuccess()
    return server.build(backend, "")


@pytest.fixture
async def client_session_success_responses(
    mcp_server_success_responses: FastMCP,
) -> AsyncGenerator[ClientSession]:
    async with create_connected_server_and_client_session(
        mcp_server_success_responses, raise_exceptions=True
    ) as _session:
        yield _session


@pytest.mark.anyio
async def test_mcp_server_tool_list(client_session_success_responses: ClientSession):
    tool_list = (await client_session_success_responses.list_tools()).tools
    unittest.TestCase().assertCountEqual(
        [tool.name for tool in tool_list], ["list_tables", "get_table_metadata", "execute_query"]
    )


@pytest.mark.anyio
async def test_mcp_server_list_tables(client_session_success_responses: ClientSession):
    result = await client_session_success_responses.call_tool("list_tables", {})

    assert result.structuredContent is not None
    unittest.TestCase().assertCountEqual(
        result.structuredContent["result"],
        ["users", "orders"],
    )


@pytest.mark.anyio
async def test_mcp_server_get_table_metadata_all(client_session_success_responses: ClientSession):
    result = await client_session_success_responses.call_tool("get_table_metadata", {})

    assert result.structuredContent is not None
    tables = [TableMetadata.model_validate(t) for t in result.structuredContent["result"]]
    assert {t.name for t in tables} == {"users", "orders"}


@pytest.mark.anyio
async def test_mcp_server_get_table_metadata_filters_by_name(
    client_session_success_responses: ClientSession,
):
    result = await client_session_success_responses.call_tool(
        "get_table_metadata", {"tables": ["orders"]}
    )

    assert result.structuredContent is not None
    tables = [TableMetadata.model_validate(t) for t in result.structuredContent["result"]]
    assert len(tables) == 1
    assert tables[0].name == "orders"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "query,limit,expected_result",
    [
        pytest.param("dummy query", 0, QueryResult(rows=[], count=0, truncated=True)),
        pytest.param(
            "dummy query",
            5,
            QueryResult(
                rows=[
                    {"user_id": i, "name": f"user_{i}", "query": "dummy query"} for i in range(5)
                ],
                count=5,
                truncated=True,
            ),
        ),
        pytest.param(
            "dummy query",
            10,
            QueryResult(
                rows=[
                    {"user_id": i, "name": f"user_{i}", "query": "dummy query"} for i in range(10)
                ],
                count=10,
                truncated=False,
            ),
        ),
        pytest.param(
            "dummy query",
            15,
            QueryResult(
                rows=[
                    {"user_id": i, "name": f"user_{i}", "query": "dummy query"} for i in range(10)
                ],
                count=10,
                truncated=False,
            ),
        ),
        pytest.param(
            "dummy query",
            None,
            QueryResult(
                rows=[
                    {"user_id": i, "name": f"user_{i}", "query": "dummy query"} for i in range(10)
                ],
                count=10,
                truncated=False,
            ),
        ),
    ],
)
async def test_mcp_server_execute_query_limit(
    client_session_success_responses: ClientSession,
    query: str,
    limit: int | None,
    expected_result: QueryResult,
):
    result = await client_session_success_responses.call_tool(
        "execute_query", {"query": query, "limit": limit}
    )
    assert QueryResult.model_validate(result.structuredContent) == expected_result
