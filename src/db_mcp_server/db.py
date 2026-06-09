import abc
from collections.abc import Iterator
from typing import Any


class AbstractDatabaseBackend(abc.ABC):
    @abc.abstractmethod
    def list_tables(self) -> list[str]: ...

    @abc.abstractmethod
    def get_table_metadata(self, tables: list[str] | None) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def execute_query(self, query: str) -> Iterator[dict[str, Any]]: ...

    @abc.abstractmethod
    def close(self) -> None: ...
