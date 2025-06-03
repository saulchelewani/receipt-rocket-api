from uuid import UUID

from pydantic import BaseModel, EmailStr, constr


class TenantBase(BaseModel):
    name: str
    code: str
    email: EmailStr | None = None
    phone_number: constr(pattern="^(265|0)[89]{2}[0-9]{7}$")

class TenantRead(TenantBase):
    id: UUID

class TenantCreate(TenantBase):
    pass