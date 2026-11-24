import asyncio
import logging
from pathlib import Path

from psycopg import AsyncConnection

from backend.core.config import get_settings
from backend.core.database import build_connection_string

logger = logging.getLogger(__name__)
BACKEND_DIR = Path(__file__).resolve().parent


async def execute_sql_file(conn: AsyncConnection, path: Path) -> None:
    for statement in path.read_text(encoding="utf-8").split(";"):
        statement = statement.strip()
        if statement:
            await conn.execute(statement)


async def bootstrap_database() -> None:
    settings = get_settings()
    async with await AsyncConnection.connect(build_connection_string(settings)) as conn:
        async with conn.transaction():
            await execute_sql_file(conn, BACKEND_DIR / "sql" / "schema.sql")
            await execute_sql_file(conn, BACKEND_DIR / "sql" / "seed.sql")
    logger.info("Esquema de 9 tablas y datos de demostracion aplicados.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
        runner.run(bootstrap_database())
