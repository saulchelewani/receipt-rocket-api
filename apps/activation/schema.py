from pydantic import BaseModel
from typing import List

class TerminalActivationRequest(BaseModel):
    terminalActivationCode: str

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
