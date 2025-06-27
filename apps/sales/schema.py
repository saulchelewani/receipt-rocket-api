from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator, conlist


class PaymentMethod(str, Enum):
    CASH = "CASH"
    CARD = "CARD"
    CHECK = "CHECK"
    BANK_TRANSFER = "BANK_TRANSFER"
    MOBILE_MONEY = "MOBILE_MONEY"


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


class VAT5CertificateDetails(BaseModel):
    id: str
    projectNumber: str
    certificateNumber: str
    quantity: int


class InvoiceHeader(BaseModel):
    invoiceNumber: str
    invoiceDateTime: datetime
    sellerTIN: str
    buyerTIN: str | None
    buyerName: str | None
    buyerAuthorizationCode: str | None
    siteId: str
    globalConfigVersion: int
    taxpayerConfigVersion: int
    terminalConfigVersion: int
    isReliefSupply: bool
    vat5CertificateDetails: VAT5CertificateDetails | None
    paymentMethod: PaymentMethod


class InvoiceLineItemResponse(BaseModel):
    productCode: str
    quantity: int
    discount: float
    id: str
    description: str
    unitPrice: float
    total: float
    totalVAT: float
    taxRateId: str
    isProduct: bool


class TaxBreakdown(BaseModel):
    rateId: str
    taxableAmount: float
    taxAmount: float


class InvoiceSummary(BaseModel):
    taxBreakDown: list[TaxBreakdown]
    totalVAT: float
    offlineSignature: str | None
    invoiceTotal: float


class Invoice(BaseModel):
    invoiceHeader: InvoiceHeader
    invoiceLineItems: list[InvoiceLineItemResponse]
    invoiceSummary: InvoiceSummary


class TransactionResponse(BaseModel):
    validation_url: str
    remark: str
    invoice: Invoice
