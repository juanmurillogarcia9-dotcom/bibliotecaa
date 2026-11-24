from datetime import date
from typing import TypedDict


class BookRecord(TypedDict):
    id: int
    title: str
    author: str
    isbn: str
    category: str | None
    stock_total: int
    stock_available: int


class MemberRecord(TypedDict):
    id: int
    name: str
    email: str
    phone: str | None
    active: bool


class LoanRecord(TypedDict):
    id: int
    book_id: int
    member_id: int
    loan_date: date
    due_date: date
    returned_at: date | None
