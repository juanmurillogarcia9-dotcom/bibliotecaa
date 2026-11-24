from typing import cast

from fastapi import HTTPException
from psycopg import sql
from psycopg_pool import AsyncConnectionPool

from backend.models.records import MemberRecord
from backend.schemas.usuarios import MemberCreate, MemberRead, MemberUpdate, PaginatedMembers


async def create_member(
    payload: MemberCreate, pool: AsyncConnectionPool
) -> MemberRead:
    async with pool.connection() as conn:
        cursor = await conn.execute(
            """
            INSERT INTO members (name, email, phone, active)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, email, phone, active
            """,
            (payload.name, str(payload.email), payload.phone, payload.active),
        )
        return MemberRead.model_validate(cast(MemberRecord, await cursor.fetchone()))


async def list_members(
    pool: AsyncConnectionPool,
    page: int,
    page_size: int,
    search: str | None,
    active: bool | None,
) -> PaginatedMembers:
    clauses: list[str] = []
    params: list[object] = []
    if search:
        clauses.append("(name ILIKE %s OR email ILIKE %s)")
        pattern = f"%{search.strip()}%"
        params.extend([pattern, pattern])
    if active is not None:
        clauses.append("active = %s")
        params.append(active)
    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""

    async with pool.connection() as conn:
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) AS total FROM members{where_clause}", params
        )
        total = (await count_cursor.fetchone())["total"]
        rows_cursor = await conn.execute(
            f"""
            SELECT id, name, email, phone, active
            FROM members{where_clause}
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        )
        items = [
            MemberRead.model_validate(cast(MemberRecord, row))
            for row in await rows_cursor.fetchall()
        ]
    return PaginatedMembers(items=items, total=total, page=page, page_size=page_size)


async def get_member(member_id: int, pool: AsyncConnectionPool) -> MemberRead:
    async with pool.connection() as conn:
        cursor = await conn.execute(
            "SELECT id, name, email, phone, active FROM members WHERE id = %s",
            (member_id,),
        )
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return MemberRead.model_validate(cast(MemberRecord, row))


async def update_member(
    member_id: int, payload: MemberUpdate, pool: AsyncConnectionPool
) -> MemberRead:
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes and changes["email"] is not None:
        changes["email"] = str(changes["email"])
    async with pool.connection() as conn:
        query = sql.SQL(
            "UPDATE members SET {} WHERE id = %s "
            "RETURNING id, name, email, phone, active"
        ).format(
            sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(column)) for column in changes
            )
        )
        cursor = await conn.execute(query, [*changes.values(), member_id])
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return MemberRead.model_validate(cast(MemberRecord, row))


async def delete_member(member_id: int, pool: AsyncConnectionPool) -> None:
    async with pool.connection() as conn:
        cursor = await conn.execute("DELETE FROM members WHERE id = %s", (member_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado.")
