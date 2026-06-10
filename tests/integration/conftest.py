import uuid
from collections.abc import Iterator

import pytest
import sqlalchemy as sa

from db_mcp_server.backends.sqlalchemy import PostgresBackendConfig


@pytest.fixture
def test_id() -> str:
    return str(uuid.uuid4()).split("-", maxsplit=1)[0]


@pytest.fixture
def schema_name(test_id) -> str:
    return f"mcp_test_{test_id}"


@pytest.fixture
def pg_config(schema_name: str) -> PostgresBackendConfig:
    return PostgresBackendConfig(db_schema=schema_name)


@pytest.fixture
def engine(pg_config: PostgresBackendConfig) -> Iterator[sa.Engine]:
    engine = sa.create_engine(
        sa.URL.create(
            drivername="postgresql+psycopg2",
            host=pg_config.host,
            port=pg_config.port,
            username=pg_config.username,
            password=pg_config.password.get_secret_value(),
            database=pg_config.db,
        )
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def pg_setup(
    engine: sa.Engine, pg_config: PostgresBackendConfig
) -> Iterator[PostgresBackendConfig]:
    with engine.begin() as conn:
        conn.execute(sa.text(f"CREATE SCHEMA {pg_config.db_schema}"))

    try:
        schema = pg_config.db_schema
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    f"CREATE TABLE {schema}.users (  id SERIAL PRIMARY KEY,  name TEXT NOT NULL)"
                )
            )
            conn.execute(sa.text(f"COMMENT ON TABLE {schema}.users IS 'Users Table Description'"))
            conn.execute(
                sa.text(f"COMMENT ON COLUMN {schema}.users.name IS 'User Name Column Description'")
            )
        yield pg_config
    finally:
        with engine.begin() as conn:
            conn.execute(sa.text(f"DROP SCHEMA {pg_config.db_schema} CASCADE"))
