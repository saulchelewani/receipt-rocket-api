from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from apps.roles.schema import RoleRead, RoleCreate
from apps.routes.schema import RoleWithRoutesRead
from core.auth import is_global_admin, get_current_user, has_permission
from core.database import get_db
from core.models import Role, Route

router = APIRouter(prefix="/roles", tags=["Roles"], dependencies=[Depends(get_current_user), Depends(has_permission)])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=RoleRead,
    dependencies=[Depends(is_global_admin)]
)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    dupl = db.query(Role).filter(Role.name == role.name).first()
    if dupl:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")

    db_role = Role(**role.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


@router.put("/{role_id}/routes", dependencies=[Depends(is_global_admin)], response_model=RoleWithRoutesRead)
async def assign_routes_to_role(role_id: UUID, route_ids: list[UUID], db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    unique_route_ids = list(set(route_ids))

    routes = db.query(Route).filter(Route.id.in_(unique_route_ids)).all()

    # Check if all unique route_ids exist
    if len(routes) != len(unique_route_ids):
        found_ids = {route.id for route in routes}
        missing_ids = [rid for rid in unique_route_ids if rid not in found_ids]
        raise HTTPException(
            status_code=400,
            detail=f"Routes not found for IDs: {missing_ids}"
        )

    # Identify routes not already assigned to the role
    existing_route_ids = {route.id for route in role.routes}
    new_routes = [route for route in routes if route.id not in existing_route_ids]

    # Append new routes to the role
    role.routes.extend(new_routes)

    db.commit()
    db.refresh(role)  # Refresh to load the updated relationships

    return role


@router.delete("/{role_id}/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(is_global_admin)])
async def remove_route_from_role(role_id: UUID, route_id: UUID, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    if not route in role.routes:
        raise HTTPException(
            status_code=400,
            detail="Route is not assigned to role"
        )

    role.routes.remove(route)
    db.commit()
    return


@router.get("/{role_id}", response_model=RoleWithRoutesRead, dependencies=[Depends(is_global_admin)])
async def get_role(role_id: UUID, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.get("/", response_model=List[RoleWithRoutesRead])
async def get_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return roles


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(is_global_admin)])
async def delete_role(role_id: UUID, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role.name == 'global_admin' or role.name == 'admin' or role.name == 'user':
        raise HTTPException(status_code=400, detail=f"Cannot delete {role.name} role")

    db.delete(role)
    db.commit()
    return


@router.patch("/{role_id}", response_model=RoleWithRoutesRead, dependencies=[Depends(is_global_admin)])
async def update_role(role_id: UUID, role: RoleCreate, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    for key, value in role.model_dump().items():
        setattr(db_role, key, value)

    db.commit()
    db.refresh(db_role)
    return db_role
