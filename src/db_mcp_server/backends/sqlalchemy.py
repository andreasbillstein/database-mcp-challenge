import pathlib
from collections.abc import Iterator
from functools import wraps
from typing import Any, Literal

import pydantic
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from db_mcp_server.db import (
    FK,
    PK,
    AbstractDatabaseBackend,
    BackendError,
    ColumnInfo,
    Index,
    TableMetadata,
)


def _translate_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            raise BackendError(f"{type(e).__name__}: {e!s}") from e

    return wrapper


def _safe_table_comment(inspector: sa.Inspector, table_name: str) -> str | None:
    try:
        return inspector.get_table_comment(table_name).get("text")
    except NotImplementedError:
        return None


class SQLAlchemyBackend(AbstractDatabaseBackend):
    def __init__(self, engine: sa.Engine):
        self._engine = engine

    @_translate_errors
    def get_table_metadata(self, tables: list[str] | None) -> list[TableMetadata]:
        table_names = tables or self.list_tables()
        engine_inspector = sa.inspect(self._engine)
        metadata = [
            TableMetadata(
                name=table_name,
                description=_safe_table_comment(engine_inspector, table_name),
                columns=[
                    ColumnInfo(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=col["nullable"],
                        description=col.get("comment"),
                    )
                    for col in engine_inspector.get_columns(table_name)
                ],
                foreign_keys=[
                    FK(
                        name=fk["name"],
                        constrained_columns=fk["constrained_columns"],
                        referred_table=fk["referred_table"],
                        referred_columns=fk["referred_columns"],
                    )
                    for fk in engine_inspector.get_foreign_keys(table_name)
                ],
                primary_key=PK(
                    name=engine_inspector.get_pk_constraint(table_name).get("name"),
                    constrained_columns=engine_inspector.get_pk_constraint(table_name)[
                        "constrained_columns"
                    ],
                ),
                indexes=[
                    Index(name=idx["name"], columns=idx["column_names"])
                    for idx in engine_inspector.get_indexes(table_name)
                ],
            )
            for table_name in table_names
        ]
        return metadata

    @_translate_errors
    def list_tables(self) -> list[str]:
        return sa.inspect(self._engine).get_table_names()

    @_translate_errors
    def execute_query(self, query: str) -> Iterator[dict[str, Any]]:
        with self._engine.begin() as conn:
            for row in conn.execute(sa.text(query)).mappings():
                yield (dict(row))

    def close(self) -> None:
        self._engine.dispose()


class SQLiteBackendConfig(pydantic.BaseModel):
    kind: Literal["sqlite"] = "sqlite"
    file: pathlib.Path = pathlib.Path(__file__).resolve().parents[3] / "data" / "titanic.db"


class PostgresBackendConfig(pydantic.BaseModel):
    kind: Literal["postgres"] = "postgres"
    host: str = "localhost"
    port: int = 5432
    db: str = "default"
    db_schema: str = "public"
    username: str = "postgres"
    password: pydantic.SecretStr = pydantic.SecretStr("postgres")
