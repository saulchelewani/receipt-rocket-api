from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator, conlist


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    CHECK = "check"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"


class InvoiceLineItem(BaseModel):
    product_code: str
    quantity: int
    discount: float = 0


class TransactionRequest(BaseModel):
    buyer_tin: str | None = None
    buyer_name: str | None = None
    buyer_authorization_code: str | None = None
    is_relief_supply: bool | None = False
    payment_method: PaymentMethod
    invoice_line_items: conlist(InvoiceLineItem, min_length=1)

    @field_validator("payment_method")
    def validate_payment_method(cls, value):
        return value.upper() if isinstance(value, str) else value


class TransactionResponse(BaseModel):
    invoice_number: str
    invoice_date: datetime
