from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from psycopg_pool import AsyncConnectionPool

from backend.controllers import prestamos as controller
from backend.core.database import get_db_pool
from backend.schemas.prestamos import LoanCreate, LoanRead, LoanStatus

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])
DbPool = Annotated[AsyncConnectionPool, Depends(get_db_pool)]


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
async def create_loan(payload: LoanCreate, pool: DbPool) -> LoanRead:
    return await controller.create_loan(payload, pool)


@router.get("", response_model=list[LoanRead])
async def list_loans(
    pool: DbPool,
    loan_status: Annotated[LoanStatus, Query(alias="status")] = LoanStatus.active,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[LoanRead]:
    return await controller.list_loans(pool, loan_status, page, page_size)


@router.post("/{loan_id}/devolucion", response_model=LoanRead)
async def return_loan(loan_id: int, pool: DbPool) -> LoanRead:
    return await controller.return_loan(loan_id, pool)
