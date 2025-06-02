from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from apps.tenants.schema import TenantRead, TenantCreate
from apps.users.routes import create_db_user
from apps.users.schema import UserRead, AdminCreate
from core.auth import is_global_admin
from core.database import get_db
from core.models import Tenant

router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[TenantRead], dependencies=[Depends(is_global_admin)])
async def list_tenants(db: Session = Depends(get_db)):
    tenants = db.query(Tenant).all()
    return tenants


@router.post("/", response_model=TenantRead, dependencies=[Depends(is_global_admin)])
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    db_tenant = db.query(Tenant).filter(Tenant.name == tenant.name).first()

    if db_tenant:
        raise HTTPException(status_code=400, detail="Tenant already exists")

    tenant = Tenant(**tenant.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/{tenant_id}/users", status_code=status.HTTP_201_CREATED, response_model=UserRead,
             dependencies=[Depends(is_global_admin)])
def create_tenant_admin(tenant_id: UUID, user: AdminCreate, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return create_db_user(user, db, tenant_id)
