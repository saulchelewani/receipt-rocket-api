import datetime
import hashlib
import hmac
from dataclasses import dataclass
from typing import Tuple

from core.utils.helpers import b10_2_b64

BASE64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def base64_to_base10(encoded: str) -> int:
    result = 0
    for char in encoded:
        index = BASE64_CHARS.find(char)
        if index == -1:
            raise ValueError(f"Invalid base64 character: {char}")
        result = result * 64 + index
    return result


def to_julian_date(date: datetime.date) -> int:
    year = date.year
    month = date.month
    day = date.day
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    return int((365.25 * (year + 4716)) + (30.6001 * (month + 1)) + day + b - 1524)


@dataclass
class InvoiceGenerationRequest:
    transaction_count: int
    transaction_date: datetime.datetime
    invoice_total: float
    vat_amount: float
    num_items: int
    business_id: int  # TODO not available on the activation response
    terminal_position: int


class InvoiceGenerator:

    @staticmethod
    def generate_combined_string(
            taxpayer_id: int,  # TODO not available on the activation response
            position: int,
            julian_date: int,
            transaction_count: int
    ) -> str:
        return "-".join([
            b10_2_b64(taxpayer_id),
            b10_2_b64(position),
            b10_2_b64(julian_date),
            b10_2_b64(transaction_count)
        ])

    def generate_invoice_number(self, req: InvoiceGenerationRequest) -> str:
        julian_date = to_julian_date(req.transaction_date.date())
        return self.generate_combined_string(req.business_id, req.terminal_position, julian_date, req.transaction_count)

    def generate_signature_url(self, req: InvoiceGenerationRequest, secret_key: str, base_url: str) -> Tuple[str, str]:
        julian_date = to_julian_date(req.transaction_date.date())
        invoice_number = self.generate_combined_string(
            req.business_id,
            req.terminal_position,
            julian_date,
            req.transaction_count
        )
        julian_base64 = b10_2_b64(julian_date)

        query_string = (
            f"TI={invoice_number}&"
            f"N={req.num_items}&"
            f"I={req.invoice_total}&"
            f"V={req.vat_amount}&"
            f"T={julian_base64}"
        )

        signature = hmac.new(secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        url = f"{base_url}?{query_string}&S={signature}"

        return signature, url
