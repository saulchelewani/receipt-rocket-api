from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from core.auth import create_access_token, verify_password
from core.database import get_db
from core.enums import Scope
from core.models import User
from core.settings import settings

router = APIRouter(prefix="/auth", tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


class AuthToken(BaseModel):
    access_token: str
    token_type: str
    expiry: datetime


@router.post("/login", response_model=AuthToken)
@limiter.limit("5/minute")
async def login(request: Request, db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "sub": user.email,
        "tenant_id": str(user.tenant_id),
        "is_global": user.scope == Scope.GLOBAL
    }

    delta = timedelta(minutes=float(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    expiry = datetime.now() + delta
    token = create_access_token(token_data, delta)

    return {"access_token": token, "token_type": "bearer", "user": user, "expiry": expiry.isoformat()}
