from uuid import UUID

from pydantic import BaseModel, EmailStr, constr

from core.utils import phone_number_regex


class TenantBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone_number: constr(pattern=phone_number_regex)


class TenantRead(TenantBase):
    id: UUID
    code: str


class TenantCreate(TenantBase):
    admin_name: str
