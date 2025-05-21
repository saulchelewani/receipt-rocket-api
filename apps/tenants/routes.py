from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.tenants.schema import TenantRead, TenantCreate
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