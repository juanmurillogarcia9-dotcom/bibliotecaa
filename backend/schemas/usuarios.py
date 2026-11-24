from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    active: bool = True

    @field_validator("name", "phone")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío.")
        return value


class MemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    active: bool | None = None

    @field_validator("name", "phone")
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
        for field in ("name", "email", "active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"El campo {field} no puede ser nulo.")
        return self


class MemberRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    active: bool


class PaginatedMembers(BaseModel):
    items: list[MemberRead]
    total: int
    page: int
    page_size: int
