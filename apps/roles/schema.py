from uuid import UUID

from pydantic import BaseModel

from apps.routes.schema import RouteRead


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    routes: list[RouteRead]
    id: UUID

    model_config = {
        "from_attributes": True
    }
