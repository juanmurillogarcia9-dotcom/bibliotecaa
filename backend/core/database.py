from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Request
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from backend.core.config import Settings


def build_connection_string(settings: Settings) -> str:
    if settings.database_url:
        return settings.database_url
    return make_conninfo(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


@asynccontextmanager
async def lifespan_context(app, settings: Settings) -> AsyncGenerator[None, None]:
    if settings.db_pool_min_size < 1:
        raise ValueError("DB_POOL_MIN_SIZE debe ser al menos 1.")
    if settings.db_pool_max_size < settings.db_pool_min_size:
        raise ValueError("DB_POOL_MAX_SIZE debe ser mayor o igual al tamaño mínimo.")

    pool = AsyncConnectionPool(
        conninfo=build_connection_string(settings),
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        kwargs={"row_factory": dict_row},
        open=False,
    )
    await pool.open()
    await pool.wait()
    app.state.db_pool = pool
    try:
        yield
    finally:
        await pool.close()


async def get_db_pool(request: Request) -> AsyncConnectionPool:
    return request.app.state.db_pool
