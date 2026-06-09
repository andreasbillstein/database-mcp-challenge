import abc
from collections.abc import Iterator
from typing import Any

import pydantic


class AbstractDatabaseBackend(abc.ABC):
    @abc.abstractmethod
    def list_tables(self) -> list[str]: ...

    @abc.abstractmethod
    def get_table_metadata(self, tables: list[str] | None) -> list[TableMetadata]: ...

    @abc.abstractmethod
    def execute_query(self, query: str) -> Iterator[dict[str, Any]]: ...

    @abc.abstractmethod
    def close(self) -> None: ...


class TableMetadata(pydantic.BaseModel):
    name: str
    columns: list[ColumnInfo]
    primary_key: PK
    foreign_keys: list[FK]
    indexes: list[Index]


class ColumnInfo(pydantic.BaseModel):
    name: str
    type: str
    nullable: bool
    description: str | None


class PK(pydantic.BaseModel):
    name: str | None
    constrained_columns: list[str]


class FK(pydantic.BaseModel):
    name: str | None
    constrained_columns: list[str]
    referred_table: str
    referred_columns: list[str]


class Index(pydantic.BaseModel):
    name: str | None
    columns: list[str | None]


class BackendError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
