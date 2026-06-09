import pathlib
from collections.abc import Iterator
from typing import Any, Literal

import pydantic
import sqlalchemy as sa

from db_mcp_server.db import AbstractDatabaseBackend


class SQLAlchemyBackend(AbstractDatabaseBackend):
    def __init__(self, engine: sa.Engine):
        self._engine = engine

    def get_table_metadata(self, tables: list[str] | None) -> list[dict[str, Any]]:
        table_names = tables or self.list_tables()
        engine_inspector = sa.inspect(self._engine)
        metadata = [
            dict(
                name=table_name,
                columns=[
                    dict(
                        name=col["name"],
                        type=str(col["type"]),
                        nullable=col["nullable"],
                        description=col.get("comment"),
                    )
                    for col in engine_inspector.get_columns(table_name)
                ],
                foreign_keys=[
                    dict(
                        name=fk["name"],
                        constrained_columns=fk["constrained_columns"],
                        referred_table=fk["referred_table"],
                        referred_columns=fk["referred_columns"],
                    )
                    for fk in engine_inspector.get_foreign_keys(table_name)
                ],
                primary_key=dict(
                    name=engine_inspector.get_pk_constraint(table_name).get("name"),
                    constrained_columns=engine_inspector.get_pk_constraint(table_name)[
                        "constrained_columns"
                    ],
                ),
                indexes=[
                    dict(name=idx["name"], columns=idx["column_names"])
                    for idx in engine_inspector.get_indexes(table_name)
                ],
            )
            for table_name in table_names
        ]
        return metadata

    def list_tables(self) -> list[str]:
        return sa.inspect(self._engine).get_table_names()

    def execute_query(self, query: str) -> Iterator[dict[str, Any]]:
        with self._engine.begin() as conn:
            rows = conn.execute(sa.text(query)).mappings()
        return (dict(row) for row in rows)

    def close(self) -> None:
        self._engine.dispose()


class SQLiteBackendConfig(pydantic.BaseModel):
    kind: Literal["sqlite"] = "sqlite"
    file: pathlib.Path


class PostgresBackendConfig(pydantic.BaseModel):
    kind: Literal["postgres"] = "postgres"
    host: str
    port: int
    db: str
    db_schema: str
    username: str
    password: pydantic.SecretStr
