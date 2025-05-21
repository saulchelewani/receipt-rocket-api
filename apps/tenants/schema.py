from uuid import UUID

from pydantic import BaseModel


class TenantBase(BaseModel):
    name: str
    code: str

class TenantRead(TenantBase):
    id: UUID

class TenantCreate(TenantBase):
    pass