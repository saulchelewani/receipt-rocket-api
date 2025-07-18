import uuid
from datetime import timedelta, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session, Mapped

from core.database import get_db
from core.enums import RoleEnum, Scope
from core.models import User, Tenant, Route
from core.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_URL = "token"
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def raise_credentials_exception():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return raise_credentials_exception()
    except JWTError:
        return raise_credentials_exception()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return raise_credentials_exception()
    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": datetime.now()
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id, token_version: int = 1, expires_delta: timedelta = timedelta(days=30)):
    to_encode = {
        "sub": str(user_id),
        "ver": token_version,
        "exp": datetime.now() + expires_delta,
        "iat": datetime.now(),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_tenant_or_none(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("tenant_id"): return None
        tenant_id: UUID = UUID(payload.get("tenant_id"))
        if not tenant_id: return None
    except JWTError:
        return None
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant


async def get_tenant(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user or not user.tenant_id:
        raise HTTPException(status_code=400, detail="User not found")
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")
    return tenant


async def is_global_admin(user: User = Depends(get_current_user)):
    if user.role.name != RoleEnum.GLOBAL_ADMIN or not user.scope == Scope.GLOBAL:
        raise HTTPException(status_code=403, detail="User is not a global admin user")
    return user


async def is_admin(user: User = Depends(get_current_user)):
    if user.role.name != "admin":
        raise HTTPException(status_code=403, detail="User is not an admin user")
    return user


async def has_permission(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    path = request.url.path
    route = request.scope.get("route")
    path = route.path if route else path
    method = request.method
    route = db.query(Route).filter(Route.path == path, Route.method == method).first()
    if not route or current_user.scope == Scope.GLOBAL or current_user.role in route.roles:
        return True

    raise HTTPException(status_code=403, detail="Forbidden")


def verify_password(plain_password: str, hashed_password: str | Mapped[str]):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)
