from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.params import Depends
from pygments.styles.dracula import background
from sqlalchemy.orm import Session
from starlette import status

from apps.users.schema import UserRead, UserCreate, AdminCreate
from core.auth import get_current_user, has_permission, get_current_tenant_or_none
from core.database import get_db
from core.enums import Scope
from core.models import Tenant, User, Role
from core.utils.emailer import send_email
from core.utils.helpers import generate_password, hash_password

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(get_current_user), Depends(has_permission)])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant_or_none),
                admin: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role or role.name == "global_admin" and not admin.scope == Scope.GLOBAL:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not logged in as a global admin")

    # FIX: Pass the tenant_id to correctly associate the new user with the creator's tenant.
    tenant_id = tenant.id if tenant else None
    return create_db_user(user, db, tenant_id=tenant_id)


@router.get("/", response_model=list[UserRead])
def read_users(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant_or_none)):
    if not tenant:
        return db.query(User).all()
    return db.query(User).filter(User.tenant_id == tenant.id).all()


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: UUID, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant_or_none)):
    """
    Retrieves a single user by their ID.
    - A global admin can retrieve any user.
    - A tenant-scoped user can only retrieve users from within their own tenant.
    """
    query = db.query(User).filter(User.id == user_id)

    if tenant:
        query = query.filter(User.tenant_id == tenant.id)

    db_user = query.first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return db_user


def create_db_user(user: UserCreate | AdminCreate, db: Session, tenant_id: UUID | None = None):
    db_user = db.query(User).filter(User.email == user.email).first()

    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    password = generate_password()

    db_user = User(
        email=str(user.email),
        role_id=user.role_id,
        tenant_id=tenant_id,
        name=user.name,
        status=1002,
        phone_number=user.phone_number,
        hashed_password=hash_password(password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    background_tasks = BackgroundTasks()
    background_tasks.add_task(send_email, db_user.email, "New account created", "welcome_email.html", {
        "name": db_user.name,
        "username": db_user.email,
        "password": password
    })
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant_or_none)):
    # REFACTOR: Apply same tenancy logic as read_user to allow global admins to delete users
    # and prevent tenant-scoped users from deleting users outside their tenant.
    query = db.query(User).filter(User.id == user_id)
    if tenant:
        query = query.filter(User.tenant_id == tenant.id)

    db_user = query.first()

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(db_user)
    db.commit()
    return
