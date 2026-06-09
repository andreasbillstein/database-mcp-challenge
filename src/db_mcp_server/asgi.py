from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.routing import Mount

from db_mcp_server import server
from db_mcp_server.bootstrap import bootstrap_db_backend
from db_mcp_server.config import Config

config = Config()  # type: ignore
backend = bootstrap_db_backend(config)
mcp = server.build(backend=backend, name=config.name)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with mcp.session_manager.run():
        yield


app = Starlette(
    routes=[
        Mount(f"/{config.name}", mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
