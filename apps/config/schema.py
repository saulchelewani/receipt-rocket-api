from datetime import datetime
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
    confirmed_at: datetime | None = None
    trading_name: str
    email: str
    phone_number: str
    label: str
    device_id: str | None = None
    config_version: int
    address_lines: list[str]
    is_blocked: bool | None = None
    site_name: str | None = None
    activation_code: str | None = None


class ConfigResponse(BaseModel):
    tax_rates: list[TaxRateRead]
    tax_payer: TenantRead
    terminal: TerminalRead
