from typing import cast

from fastapi import HTTPException
from psycopg import sql
from psycopg_pool import AsyncConnectionPool

from backend.models.records import BookRecord
from backend.schemas.libros import BookCreate, BookRead, BookUpdate, PaginatedBooks


async def create_book(payload: BookCreate, pool: AsyncConnectionPool) -> BookRead:
    async with pool.connection() as conn:
        cursor = await conn.execute(
            """
            INSERT INTO books (title, author, isbn, category, stock_total, stock_available)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, author, isbn, category, stock_total, stock_available
            """,
            (
                payload.title,
                payload.author,
                payload.isbn,
                payload.category,
                payload.stock_total,
                payload.stock_total,
            ),
        )
        return BookRead.model_validate(cast(BookRecord, await cursor.fetchone()))


async def list_books(
    pool: AsyncConnectionPool,
    page: int,
    page_size: int,
    search: str | None,
    category: str | None,
) -> PaginatedBooks:
    clauses: list[str] = []
    params: list[str] = []
    if search:
        clauses.append("(title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s)")
        pattern = f"%{search.strip()}%"
        params.extend([pattern, pattern, pattern])
    if category:
        clauses.append("category ILIKE %s")
        params.append(category.strip())
    where_clause = f" WHERE {' AND '.join(clauses)}" if clauses else ""

    async with pool.connection() as conn:
        count_cursor = await conn.execute(
            f"SELECT COUNT(*) AS total FROM books{where_clause}", params
        )
        total = (await count_cursor.fetchone())["total"]
        rows_cursor = await conn.execute(
            f"""
            SELECT id, title, author, isbn, category, stock_total, stock_available
            FROM books{where_clause}
            ORDER BY id
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        )
        items = [
            BookRead.model_validate(cast(BookRecord, row))
            for row in await rows_cursor.fetchall()
        ]
    return PaginatedBooks(items=items, total=total, page=page, page_size=page_size)


async def get_book(book_id: int, pool: AsyncConnectionPool) -> BookRead:
    async with pool.connection() as conn:
        cursor = await conn.execute(
            """
            SELECT id, title, author, isbn, category, stock_total, stock_available
            FROM books WHERE id = %s
            """,
            (book_id,),
        )
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    return BookRead.model_validate(cast(BookRecord, row))


async def update_book(
    book_id: int, payload: BookUpdate, pool: AsyncConnectionPool
) -> BookRead:
    changes = payload.model_dump(exclude_unset=True)
    async with pool.connection() as conn:
        cursor = await conn.execute(
            "SELECT stock_total, stock_available FROM books WHERE id = %s FOR UPDATE",
            (book_id,),
        )
        current = await cursor.fetchone()
        if current is None:
            raise HTTPException(status_code=404, detail="Libro no encontrado.")

        total = changes.get("stock_total", current["stock_total"])
        available = changes.get("stock_available", current["stock_available"])
        if available > total:
            raise HTTPException(
                status_code=400,
                detail="El stock disponible no puede superar el stock total.",
            )
        if total < current["stock_total"] - current["stock_available"]:
            raise HTTPException(
                status_code=400,
                detail="El stock total no puede ser menor que los ejemplares prestados.",
            )
        if "stock_total" in changes and "stock_available" not in changes:
            changes["stock_available"] = (
                current["stock_available"] + total - current["stock_total"]
            )

        query = sql.SQL(
            "UPDATE books SET {} WHERE id = %s "
            "RETURNING id, title, author, isbn, category, stock_total, stock_available"
        ).format(
            sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(column)) for column in changes
            )
        )
        updated_cursor = await conn.execute(query, [*changes.values(), book_id])
        return BookRead.model_validate(
            cast(BookRecord, await updated_cursor.fetchone())
        )


async def delete_book(book_id: int, pool: AsyncConnectionPool) -> None:
    async with pool.connection() as conn:
        cursor = await conn.execute("DELETE FROM books WHERE id = %s", (book_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Libro no encontrado.")
