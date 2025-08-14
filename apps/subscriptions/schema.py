from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PackageRead(BaseModel):
    id: UUID
    name: str
    number_of_months: int
    price: float


class SubscriptionBase(BaseModel):
    start_date: datetime
    end_date: datetime
    is_active: bool
    package: PackageRead


class SubscriptionRead(SubscriptionBase):
    id: UUID
