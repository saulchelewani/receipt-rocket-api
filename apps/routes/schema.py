from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class RouteBase(BaseModel):
    path: str
    method: str
    action: str

    model_config = {
        "from_attributes": True  # Enables ORM mode (formerly `orm_mode`)
    }


class RouteCreate(RouteBase):
    pass


class RouteRead(RouteBase):
    id: UUID
    name: str


class RoleWithRoutesRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    routes: List[RouteRead]

    model_config = {
        "from_attributes": True
    }
