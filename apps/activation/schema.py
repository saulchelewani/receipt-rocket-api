from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TerminalActivationRequest(BaseModel):
    terminal_activation_code: str


class TerminalConfigurationOut(BaseModel):
    label: str
    email: str
    phone: str
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

class TerminalConfigurationRead(BaseModel):
    id: UUID
    label: str
    email: str
    phone_number: str
    trading_name: str