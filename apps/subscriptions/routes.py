from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from apps.subscriptions.schema import SubscriptionRead
from core import Tenant, Subscription
from core.auth import get_current_user, get_tenant
from core.database import get_db

router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", dependencies=[Depends(get_current_user)], response_model=SubscriptionRead)
async def get_subscriptions(
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db)
):
    subscription = (db.query(Subscription)
                    .filter(Subscription.end_date >= datetime.now())
                    .filter(Subscription.tenant_id == tenant.id).first())

    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There is no active subscription")

    return subscription
