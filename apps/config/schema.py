from uuid import UUID

from pydantic import BaseModel

from apps.tenants.schema import TenantRead


class TaxRateRead(BaseModel):
    rate_id: str
    name: str
    rate: float | None
    ordinal: int
    change_mode: str | None = None


class TaxPayerRead(BaseModel):
    id: UUID
    tin: str
    version: int
    tax_office_code: str
    tax_office_name: str
    vat_registered: bool
    activated_tax_rate_ids: list[str]


class TerminalRead(BaseModel):
    terminal_id: str
    confirmed_at: str | None = None
    trading_name: str
    email: str
    phone_number: str
    label: str
    version: int
    address_lines: list[str]
    offline_limit_hours: int
    offline_limit_amount: float


class ConfigResponse(BaseModel):
    tax_rates: list[TaxRateRead]
    tax_payer: TenantRead
    terminal: TerminalRead
