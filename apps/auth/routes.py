from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.auth import create_access_token, verify_password, create_refresh_token, SECRET_KEY, ALGORITHM
from core.database import get_db
from core.enums import Scope
from core.models import User, Dictionary
from core.settings import settings

router = APIRouter(prefix="/auth", tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expiry: datetime


@router.post("/login", response_model=AuthToken)
@limiter.limit("5/minute")
async def login(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status != 1001:
        status = db.query(Dictionary).filter(Dictionary.term == user.status).first()
        raise HTTPException(status_code=401, detail=f"Login failed: {status.definition}")

    token_data = {
        "sub": user.email,
        "tenant_id": str(user.tenant_id),
        "is_global": user.scope == Scope.GLOBAL
    }

    delta = timedelta(minutes=float(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    expiry = datetime.now() + delta
    access_token = create_access_token(token_data, delta)
    refresh_token = create_refresh_token(user_id=user.id, token_version=user.refresh_token_version)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
        "expiry": expiry.isoformat()
    }


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
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
