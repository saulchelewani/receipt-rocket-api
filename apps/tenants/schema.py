from uuid import UUID

from pydantic import BaseModel, EmailStr, constr

from core.utils.helpers import phone_number_regex, tenant_code_regex


class TenantBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone_number: constr(pattern=phone_number_regex)
    tin: constr(pattern=r"^[0-9]{4,8}$")


class TenantRead(TenantBase):
    id: UUID
    code: constr(pattern=tenant_code_regex)


class TenantCreate(TenantBase):
    admin_name: str
    password: str
