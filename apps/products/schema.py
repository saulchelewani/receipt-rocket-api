from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    unit_price: float | None = None
    quantity: int | None = None
    unit_of_measure: str | None = None
    site_id: UUID | None = None
    expiry_date: datetime | None = None
    minimum_stock_level: int | None = None
    tax_rate_id: str | None = None


class ProductRead(ProductBase):
    id: UUID | None
