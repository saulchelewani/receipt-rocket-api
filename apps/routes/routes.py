from uuid import UUID

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.routes.schema import RouteCreate, RouteRead
from core.auth import is_global_admin
from core.database import get_db
from core.models import Route

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RouteRead,
             dependencies=[Depends(is_global_admin)])
def create_route(route: RouteCreate, db: Session = Depends(get_db)):
    ex_route = db.query(Route).filter(Route.path == route.path, Route.method == route.method).first()
    if ex_route:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Route already registered")

    db_route = Route(**route.model_dump(), name=f"{route.method}:{route.path}")
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@router.get("/", response_model=list[RouteRead], dependencies=[Depends(is_global_admin)])
def read_routes(db: Session = Depends(get_db)):
    routes = db.query(Route).all()
    return routes


@router.get("/{route_id}", response_model=RouteRead, dependencies=[Depends(is_global_admin)])
def read_route(route_id: UUID, db: Session = Depends(get_db)):
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    return route


@router.patch("/{route_id}", status_code=status.HTTP_200_OK, response_model=RouteRead,
              dependencies=[Depends(is_global_admin)])
def update_route(route_id: UUID, route: RouteCreate, db: Session = Depends(get_db)):
    db_route = db.get(Route, route_id)
    if not db_route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    for key, value in route.model_dump().items():
        setattr(db_route, key, value)

    db_route.name = f"{db_route.method}:{db_route.path}"
    db.commit()
    db.refresh(db_route)
    return db_route


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(is_global_admin)])
def delete_route(route_id: UUID, db: Session = Depends(get_db)):
    db_route = db.get(Route, route_id)
    if not db_route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    db.delete(db_route)
    db.commit()
    return
