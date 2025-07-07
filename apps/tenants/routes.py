import random
import string
from typing import Set
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from passlib.utils import generate_password
from sqlalchemy.orm import Session
from starlette import status

from apps.tenants.schema import TenantRead, TenantCreate
from apps.users.routes import create_db_user
from apps.users.schema import UserRead, AdminCreate
from core.auth import is_global_admin
from core.database import get_db
from core.models import Tenant, User, Role
from core.utils import hash_password
from utils.emailer import send_email

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
async def create_tenant(tenant: TenantCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_tenant = db.query(Tenant).filter(Tenant.name == tenant.name).first()

    if db_tenant:
        raise HTTPException(status_code=400, detail="Tenant already exists")

    codes = get_created_code(db)

    db_tenant = Tenant(**tenant.model_dump(exclude={'admin_name'}), code=generate_unique_initials(tenant.name, codes))
    db.add(db_tenant)
    db.flush()

    password = generate_password()

    admin = User(
        tenant_id=db_tenant.id,
        name=tenant.admin_name,
        email=db_tenant.email,
        phone_number=db_tenant.phone_number,
        role_id=get_admin_role(db).id,
        hashed_password=hash_password(password),
    )

    background_tasks.add_task(send_email, admin.email, "New account created", f"Your password is: {password}")

    db.add(admin)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


def get_admin_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.name == "admin").first()
    if not role:
        role = Role(name="admin")
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


def get_created_code(db: Session) -> Set[str]:
    tenants = db.query(Tenant).all()
    return {tenant.code for tenant in tenants}


def generate_unique_initials(name: str, codes: Set[str]) -> str:
    initials = ''.join(word[0].upper() for word in name.strip().split() if word)

    while True:
        digits = ''.join(random.choices(string.digits, k=4))
        result = initials + digits
        if result not in codes:
            return result


@router.post("/{tenant_id}/users", status_code=status.HTTP_201_CREATED, response_model=UserRead,
             dependencies=[Depends(is_global_admin)])
def create_tenant_admin(tenant_id: UUID, user: AdminCreate, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return create_db_user(user, db, tenant_id)
