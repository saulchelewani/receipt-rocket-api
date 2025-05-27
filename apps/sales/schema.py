from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    CHECK = "check"
    BANK_TRANSFER = "bank_transfer"


class InvoiceLineItem(BaseModel):
    product_code: str
    description: str
    unit_price: float
    quantity: int
    discount: float
    total: float
    total_vat: float
    tax_rate_id: str
    is_product: bool


class TransactionRequest(BaseModel):
    buyer_tin: str | None = None
    buyer_name: str | None = None
    buyer_authorization_code: str | None = None
    is_relief_supply: bool | None = False
    payment_method: PaymentMethod
    invoice_line_items: list[InvoiceLineItem]

    @field_validator("payment_method")
    def validate_payment_method(cls, value):
        return value.upper() if isinstance(value, str) else value


class TransactionResponse(BaseModel):
    invoice_number: str
    invoice_date: datetime
