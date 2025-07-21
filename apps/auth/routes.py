from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette import status

from apps.config.schema import TerminalRead
from core.auth import create_access_token, verify_password, create_refresh_token, SECRET_KEY, ALGORITHM
from core.database import get_db
from core.enums import Scope, StatusEnum
from core.models import User, Dictionary, Terminal
from core.settings import settings

router = APIRouter(prefix="/auth", tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expiry: datetime
    terminals: list[TerminalRead]


@router.post("/login", response_model=AuthToken)
@limiter.limit("5/minute")
async def login(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.status is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not in active state")

    if user.status != StatusEnum.ACTIVE:
        dictionary = db.query(Dictionary).filter(Dictionary.term == user.status).first()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Login failed: {dictionary.definition}")

    token_data = {
        "sub": user.email,
        "tenant_id": str(user.tenant_id),
        "is_global": user.scope == Scope.GLOBAL
    }

    if user.scope == Scope.TENANT:
        terminals = db.query(Terminal).filter(Terminal.tenant_id == user.tenant_id).all()

    delta = timedelta(minutes=float(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    expiry = datetime.now() + delta
    access_token = create_access_token(token_data, delta)
    refresher = create_refresh_token(user_id=user.id, token_version=user.refresh_token_version)

    user.last_login = datetime.now()
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresher,
        "token_type": "bearer",
        "user": user,
        "terminals": get_tenant_terminals(db, user),
        "expiry": expiry.isoformat()
    }


def get_tenant_terminals(db: Session, user):
    if user.scope == Scope.GLOBAL:
        return []
    return db.query(Terminal).filter(Terminal.tenant_id == user.tenant_id).all()


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(refresher: str, db: Session = Depends(get_db)):
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(refresher, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        token_version = int(payload.get("ver"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.refresh_token_version != token_version:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token(user.id, user.refresh_token_version)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
