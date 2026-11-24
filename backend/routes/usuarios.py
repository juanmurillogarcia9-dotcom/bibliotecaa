from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from psycopg_pool import AsyncConnectionPool

from backend.controllers import usuarios as controller
from backend.core.database import get_db_pool
from backend.schemas.usuarios import MemberCreate, MemberRead, MemberUpdate, PaginatedMembers

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
DbPool = Annotated[AsyncConnectionPool, Depends(get_db_pool)]


@router.post("", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
async def create_member(payload: MemberCreate, pool: DbPool) -> MemberRead:
    return await controller.create_member(payload, pool)


@router.get("", response_model=PaginatedMembers)
async def list_members(
    pool: DbPool,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
    active: bool | None = None,
) -> PaginatedMembers:
    return await controller.list_members(pool, page, page_size, search, active)


@router.get("/{member_id}", response_model=MemberRead)
async def get_member(member_id: int, pool: DbPool) -> MemberRead:
    return await controller.get_member(member_id, pool)


@router.patch("/{member_id}", response_model=MemberRead)
async def update_member(
    member_id: int, payload: MemberUpdate, pool: DbPool
) -> MemberRead:
    return await controller.update_member(member_id, payload, pool)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: int, pool: DbPool) -> None:
    await controller.delete_member(member_id, pool)
