from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core import BillingCycle


class SubscriptionBase(BaseModel):
    description: str | None = None
    billing_cycle: BillingCycle
    device_limit: int
    start_date: datetime
    end_date: datetime
    is_active: bool


class SubscriptionRead(SubscriptionBase):
    id: UUID
