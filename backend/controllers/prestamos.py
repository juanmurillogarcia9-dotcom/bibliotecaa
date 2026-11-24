from datetime import date, timedelta
from typing import cast

from fastapi import HTTPException
from psycopg_pool import AsyncConnectionPool

from backend.models.records import LoanRecord
from backend.schemas.prestamos import LoanCreate, LoanRead, LoanStatus


async def create_loan(payload: LoanCreate, pool: AsyncConnectionPool) -> LoanRead:
    due_date = payload.due_date or (date.today() + timedelta(days=14))
    async with pool.connection() as conn:
        async with conn.transaction():
            member_cursor = await conn.execute(
                "SELECT active FROM members WHERE id = %s FOR SHARE",
                (payload.member_id,),
            )
            member = await member_cursor.fetchone()
            if member is None:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            if not member["active"]:
                raise HTTPException(status_code=400, detail="El usuario está inactivo.")

            book_cursor = await conn.execute(
                "SELECT stock_available FROM books WHERE id = %s FOR UPDATE",
                (payload.book_id,),
            )
            book = await book_cursor.fetchone()
            if book is None:
                raise HTTPException(status_code=404, detail="Libro no encontrado.")
            if book["stock_available"] < 1:
                raise HTTPException(status_code=400, detail="No hay ejemplares disponibles.")

            await conn.execute(
                "UPDATE books SET stock_available = stock_available - 1 WHERE id = %s",
                (payload.book_id,),
            )
            loan_cursor = await conn.execute(
                """
                INSERT INTO loans (book_id, member_id, due_date)
                VALUES (%s, %s, %s)
                RETURNING id, book_id, member_id, loan_date, due_date, returned_at
                """,
                (payload.book_id, payload.member_id, due_date),
            )
            loan = cast(LoanRecord, await loan_cursor.fetchone())
    return LoanRead.model_validate(loan)


async def list_loans(
    pool: AsyncConnectionPool,
    loan_status: LoanStatus,
    page: int,
    page_size: int,
) -> list[LoanRead]:
    conditions = {
        LoanStatus.active: "returned_at IS NULL",
        LoanStatus.overdue: "returned_at IS NULL AND due_date < CURRENT_DATE",
        LoanStatus.all: "TRUE",
    }
    async with pool.connection() as conn:
        cursor = await conn.execute(
            f"""
            SELECT id, book_id, member_id, loan_date, due_date, returned_at
            FROM loans
            WHERE {conditions[loan_status]}
            ORDER BY due_date, id
            LIMIT %s OFFSET %s
            """,
            (page_size, (page - 1) * page_size),
        )
        rows = await cursor.fetchall()
    return [
        LoanRead.model_validate(cast(LoanRecord, row))
        for row in rows
    ]


async def return_loan(loan_id: int, pool: AsyncConnectionPool) -> LoanRead:
    async with pool.connection() as conn:
        async with conn.transaction():
            cursor = await conn.execute(
                """
                SELECT id, book_id, member_id, loan_date, due_date, returned_at
                FROM loans WHERE id = %s FOR UPDATE
                """,
                (loan_id,),
            )
            loan = await cursor.fetchone()
            if loan is None:
                raise HTTPException(status_code=404, detail="Préstamo no encontrado.")
            if loan["returned_at"] is not None:
                raise HTTPException(status_code=400, detail="El préstamo ya fue devuelto.")

            return_cursor = await conn.execute(
                """
                UPDATE loans SET returned_at = CURRENT_DATE
                WHERE id = %s
                RETURNING id, book_id, member_id, loan_date, due_date, returned_at
                """,
                (loan_id,),
            )
            updated_loan = await return_cursor.fetchone()
            await conn.execute(
                "UPDATE books SET stock_available = stock_available + 1 WHERE id = %s",
                (loan["book_id"],),
            )
    return LoanRead.model_validate(cast(LoanRecord, updated_loan))
