from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    author: str = Field(min_length=1, max_length=200)
    isbn: str = Field(min_length=1, max_length=20)
    category: str | None = Field(default=None, max_length=100)
    stock_total: int = Field(ge=0)

    @field_validator("title", "author", "isbn", "category")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío.")
        return value


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    author: str | None = Field(default=None, min_length=1, max_length=200)
    isbn: str | None = Field(default=None, min_length=1, max_length=20)
    category: str | None = Field(default=None, max_length=100)
    stock_total: int | None = Field(default=None, ge=0)
    stock_available: int | None = Field(default=None, ge=0)

    @field_validator("title", "author", "isbn", "category")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío.")
        return value

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set:
            raise ValueError("Debe enviar al menos un campo para actualizar.")
        for field in ("title", "author", "isbn", "stock_total", "stock_available"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"El campo {field} no puede ser nulo.")
        return self


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    category: str | None
    stock_total: int
    stock_available: int


class PaginatedBooks(BaseModel):
    items: list[BookRead]
    total: int
    page: int
    page_size: int
