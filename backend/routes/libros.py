from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from psycopg_pool import AsyncConnectionPool

from backend.controllers import libros as controller
from backend.core.database import get_db_pool
from backend.schemas.libros import BookCreate, BookRead, BookUpdate, PaginatedBooks

router = APIRouter(prefix="/libros", tags=["Libros"])
DbPool = Annotated[AsyncConnectionPool, Depends(get_db_pool)]


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def create_book(payload: BookCreate, pool: DbPool) -> BookRead:
    return await controller.create_book(payload, pool)


@router.get("", response_model=PaginatedBooks)
async def list_books(
    pool: DbPool,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    category: str | None = None,
) -> PaginatedBooks:
    return await controller.list_books(pool, page, page_size, search, category)


@router.get("/{book_id}", response_model=BookRead)
async def get_book(book_id: int, pool: DbPool) -> BookRead:
    return await controller.get_book(book_id, pool)


@router.patch("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int, payload: BookUpdate, pool: DbPool
) -> BookRead:
    return await controller.update_book(book_id, payload, pool)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, pool: DbPool) -> None:
    await controller.delete_book(book_id, pool)
