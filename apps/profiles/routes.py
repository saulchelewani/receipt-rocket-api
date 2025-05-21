from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from apps.profiles.schema import ProfileCreate, ProfileRead
from core.auth import get_tenant
from core.database import get_db
from core.models import Tenant, Profile

router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(profile: ProfileCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    profile = Profile(**profile.model_dump(), tenant_id=tenant.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
