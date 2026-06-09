import sqlalchemy as sa

from db_mcp_server.backends.sqlalchemy import (
    PostgresBackendConfig,
    SQLAlchemyBackend,
    SQLiteBackendConfig,
)
from db_mcp_server.config import Config
from db_mcp_server.db import AbstractDatabaseBackend


def bootstrap_db_backend(config: Config) -> AbstractDatabaseBackend:
    backend = config.backend
    if isinstance(backend, SQLiteBackendConfig):
        engine = sa.create_engine(
            sa.URL.create(drivername="sqlite", database=str(backend.file.resolve()))
        )
    elif isinstance(backend, PostgresBackendConfig):
        engine = sa.create_engine(
            sa.URL.create(
                drivername="postgresql+psycopg2",
                host=backend.host,
                port=backend.port,
                username=backend.username,
                password=backend.password.get_secret_value(),
                database=backend.db,
            ),
            connect_args={"options": f"-c search_path={backend.db_schema}"},
        )
    else:
        raise AssertionError(f"Unknown backend {type(backend)}")

    return SQLAlchemyBackend(engine)
