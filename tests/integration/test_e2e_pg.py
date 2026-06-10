from collections.abc import AsyncGenerator

import pytest
from mcp import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

import db_mcp_server.config
import db_mcp_server.server
from db_mcp_server.backends.sqlalchemy import PostgresBackendConfig
from db_mcp_server.bootstrap import bootstrap_db_backend
from db_mcp_server.db import TableMetadata

pytestmark = pytest.mark.integration


@pytest.fixture
async def client_session(
    pg_setup: PostgresBackendConfig,
) -> AsyncGenerator[ClientSession]:
    config = db_mcp_server.config.Config(
        backend=pg_setup, name="test_server", description="test description"
    )
    backend = bootstrap_db_backend(config)
    mcp_server = db_mcp_server.server.build(
        backend=backend,
        name=config.name,
        dialect=config.backend.kind,
        content_description=config.description,
    )
    async with create_connected_server_and_client_session(
        mcp_server, raise_exceptions=True
    ) as _session:
        yield _session


@pytest.mark.anyio
async def test_mcp_postgres_table_not_found_raises_descriptive_backend_error(
    client_session: ClientSession,
):
    tool_result = await client_session.call_tool("get_table_metadata", {"tables": ["i_dont_exist"]})
    assert tool_result.isError
    assert any(
        "NoSuchTableError" in content_block.text
        for content_block in tool_result.content
        if content_block.type == "text"
    )


@pytest.mark.anyio
async def test_mcp_postgres_table_and_column_descriptions_populate(client_session: ClientSession):
    tool_result = await client_session.call_tool("get_table_metadata", {"tables": ["users"]})

    assert tool_result.structuredContent is not None

    tables = {
        t["name"]: TableMetadata.model_validate(t) for t in tool_result.structuredContent["result"]
    }
    users_table = tables["users"]
    assert users_table.description == "Users Table Description"

    columns = {c.name: c for c in users_table.columns}
    assert columns["name"].description == "User Name Column Description"


@pytest.mark.anyio
async def test_mcp_postgres_readonly_user_rejects_writes(client_session: ClientSession):
    tool_result = await client_session.call_tool(
        "execute_query", {"query": "INSERT INTO users (name) VALUES ('New Name')"}
    )
    assert tool_result.isError
