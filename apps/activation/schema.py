from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, constr, EmailStr

from core.utils.helpers import phone_number_regex


class TerminalActivationRequest(BaseModel):
    terminal_activation_code: constr(pattern=r"([A-Z0-9]{4}-){3}[A-Z0-9]{4}")


class TerminalConfigurationOut(BaseModel):
    label: str
    email: EmailStr
    phone: constr(pattern=phone_number_regex)
    trading_name: str


class TaxRateOut(BaseModel):
    rate_id: str
    name: str
    rate: float
    charge_mode: str


class TerminalConfirmationRequest(BaseModel):
    terminal_id: UUID


class TerminalRead(BaseModel):
    id: UUID
    terminal_id: str
    confirmed_at: datetime
    terminal_id: str
    confirmed_at: datetime | None = None
    trading_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    label: str
    device_id: str | None = None
    config_version: int
    address_lines: list[str] | None = []
    is_blocked: bool | None = None
    site_name: str | None = None
    activation_code: str | None = None

class TerminalConfigurationRead(BaseModel):
    id: UUID
    label: str
    email: EmailStr
    phone_number: constr(pattern=phone_number_regex)
    trading_name: str
    device_id: constr(pattern=r"\w{16}")
