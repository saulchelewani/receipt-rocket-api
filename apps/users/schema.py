from uuid import UUID

from pydantic import BaseModel, EmailStr, constr

from apps.roles.schema import RoleRead
from core.utils.helpers import phone_number_regex


class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone_number: constr(pattern=phone_number_regex)


class UserCreate(UserBase):
    role_id: UUID


class AdminCreate(UserBase):
    role_id: UUID


class UserRead(UserBase):
    id: UUID
    role: RoleRead
    # tenant: TenantRead | None
    # scope: str

    model_config = {
        "from_attributes": True
    }
