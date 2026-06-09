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
    """Metadata information for one database table: Columns, primary key,
    foreign keys, and indexes. Describes the table's shape."""

    name: str
    description: str | None = pydantic.Field(
        default=None,
        description=(
            "Free-text description of the table (If supported by the underlying database)."
            "`None` for backends that don't expose descriptions/comments "
            "or tables with no comment set."
        ),
    )
    columns: list[ColumnInfo]
    primary_key: PK
    foreign_keys: list[FK]
    indexes: list[Index]


class ColumnInfo(pydantic.BaseModel):
    """One column of a database table: name, data type, and nullability."""

    name: str
    type: str = pydantic.Field(
        description=(
            "Stringified SQL type as reported by the underlying database "
            "Exact wording varies by backend."
        )
    )
    nullable: bool
    description: str | None = pydantic.Field(
        default=None,
        description=(
            "Free-text description of the column (If supported by the underlying database)."
            "`None` for backends that don't expose descriptions/comments "
            "or tables with no comment set."
        ),
    )


class PK(pydantic.BaseModel):
    """Primary key constraint for a table."""

    name: str | None = pydantic.Field(
        description=(
            "Constraint name. May be None for primary keys without an "
            "explicit name (e.g. implicit single-column PKs)."
        )
    )
    constrained_columns: list[str] = pydantic.Field(
        description=(
            "Columns forming the primary key, in declaration order. Order "
            "matters for composite primary keys."
        )
    )


class FK(pydantic.BaseModel):
    """Foreign key constraint from this table's columns to another table's columns."""

    name: str | None = pydantic.Field(description=("Constraint name as declared in the schema."))
    constrained_columns: list[str] = pydantic.Field(
        description="Columns in this table that participate in the foreign key."
    )
    referred_table: str = pydantic.Field(
        description="Name of the table this foreign key points to."
    )
    referred_columns: list[str] = pydantic.Field(
        description=(
            "Columns in the referred table that this foreign key maps to, "
            "positionally aligned with `constrained_columns`."
        )
    )


class Index(pydantic.BaseModel):
    """A database index over one or more columns."""

    name: str | None = pydantic.Field(
        description="Index name. May be None for auto-generated indexes."
    )
    columns: list[str | None] = pydantic.Field(
        description=(
            "Columns covered by the index, in declaration order. None for expression-based indexes"
        )
    )


class BackendError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
