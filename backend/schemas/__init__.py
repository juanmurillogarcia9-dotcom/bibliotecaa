from backend.schemas.libros import BookCreate, BookRead, BookUpdate, PaginatedBooks
from backend.schemas.prestamos import LoanCreate, LoanRead, LoanStatus
from backend.schemas.usuarios import MemberCreate, MemberRead, MemberUpdate, PaginatedMembers

__all__ = [
    "BookCreate",
    "BookRead",
    "BookUpdate",
    "LoanCreate",
    "LoanRead",
    "LoanStatus",
    "MemberCreate",
    "MemberRead",
    "MemberUpdate",
    "PaginatedBooks",
    "PaginatedMembers",
]
