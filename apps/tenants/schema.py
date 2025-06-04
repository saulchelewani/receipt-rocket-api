from uuid import UUID

from pydantic import BaseModel, EmailStr, constr

from core.utils import phone_number_regex


class TenantBase(BaseModel):
    name: str
    code: str
    email: EmailStr | None = None
    phone_number: constr(pattern=phone_number_regex)

class TenantRead(TenantBase):
    id: UUID

class TenantCreate(TenantBase):
    pass