from uuid import UUID

from pydantic import BaseModel, EmailStr

from apps.roles.schema import RoleRead


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    role_id: UUID
    password: str


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
