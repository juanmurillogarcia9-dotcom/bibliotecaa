from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class LoanCreate(BaseModel):
    book_id: int = Field(gt=0)
    member_id: int = Field(gt=0)
    due_date: date | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_must_not_be_in_past(cls, value: date | None) -> date | None:
        if value is not None and value < date.today():
            raise ValueError("La fecha de vencimiento no puede estar en el pasado.")
        return value


class LoanRead(BaseModel):
    id: int
    book_id: int
    member_id: int
    loan_date: date
    due_date: date
    returned_at: date | None


class LoanStatus(str, Enum):
    active = "active"
    overdue = "overdue"
    all = "all"
