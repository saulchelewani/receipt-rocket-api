from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette import status

from apps.users.schema import UserRead, UserCreate
from core.auth import get_current_user, has_permission, get_current_tenant_or_none
from core.database import get_db
from core.enums import Scope
from core.models import Tenant, User, Role

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(get_current_user), Depends(has_permission)])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant_or_none),
                admin: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role or role.name == "global_admin" and not admin.scope == Scope.GLOBAL:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not logged in as a global admin")

    return create_db_user(user, db)


@router.get("/", response_model=list[UserRead])
def read_users(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant_or_none)):
    if not tenant:
        return db.query(User).all()
    return db.query(User).filter(User.tenant_id == tenant.id).all()


def create_db_user(user, db, tenant_id: UUID | None = None):
    db_user = db.query(User).filter(User.email == user.email).first()

    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    db_user = User(email=str(user.email), role_id=user.role_id, tenant_id=tenant_id, name=user.name,
                   phone_number=user.phone_number, )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant_or_none)):
    db_user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant.id).first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(db_user)
    db.commit()
    return
