import pytest
from pydantic import TypeAdapter, ValidationError

from db_mcp_server.backends.sqlalchemy import PostgresBackendConfig, SQLiteBackendConfig
from db_mcp_server.config import BackendConfig

_adapter = TypeAdapter(BackendConfig)


def test_backend_discriminator_resolves_sqlite():
    backend = _adapter.validate_python({"kind": "sqlite", "file": "/tmp/test.db"})
    assert isinstance(backend, SQLiteBackendConfig)
    assert str(backend.file) == "/tmp/test.db"


def test_backend_discriminator_resolves_postgres():
    backend = _adapter.validate_python(
        {
            "kind": "postgres",
            "host": "localhost",
            "port": 5432,
            "db": "mydb",
            "db_schema": "public",
            "username": "postgres",
            "password": "postgres",
        }
    )
    assert isinstance(backend, PostgresBackendConfig)
    assert backend.host == "localhost"
    assert backend.db_schema == "public"


def test_backend_discriminator_rejects_unknown_kind():
    with pytest.raises(ValidationError):
        _adapter.validate_python({"kind": "mysql", "file": "/tmp/test.db"})


def test_backend_discriminator_rejects_missing_sqlite_field():
    with pytest.raises(ValidationError):
        _adapter.validate_python({"kind": "sqlite"})
