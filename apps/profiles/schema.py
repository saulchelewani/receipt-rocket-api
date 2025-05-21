from uuid import UUID

from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    business_name: str = Field(...)
    address: str = Field(...)
    phone: str = Field(...)
    email: str | None = Field(default=None)
    website: str | None = Field(default=None)
    tin: str = Field(...)

class ProfileCreate(ProfileBase):
    pass

class ProfileRead(ProfileBase):
    id: UUID