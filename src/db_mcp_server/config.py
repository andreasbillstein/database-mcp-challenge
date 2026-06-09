from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from db_mcp_server.backends.sqlalchemy import PostgresBackendConfig, SQLiteBackendConfig

BackendConfig = Annotated[
    SQLiteBackendConfig | PostgresBackendConfig,
    Field(discriminator="kind"),
]


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_prefix="DB_MCP__",
        env_nested_delimiter="__",
    )

    backend: BackendConfig
    name: str = Field(
        pattern=r"^[a-z][a-z0-9_-]*$",
        min_length=1,
        max_length=64,
        description="Database identifier. Used as the MCP mount base path.",
    )
