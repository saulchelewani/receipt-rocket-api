import base64
import hashlib
import hmac
import secrets
import string
from datetime import datetime

import rstr


def get_sequence_number(length=16):
    """Generates a cryptographically secure random string.

    Args:
        length: The length of the string to generate (default: 16).

    Returns:
        A cryptographically secure random string.
    """
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


def get_random_number(length=16):
    """Generates a cryptographically secure random string.

    Args:
        length: The length of the string to generate (default: 16).

    Returns:
        A cryptographically secure random string.
    """
    return "".join(secrets.choice(string.digits) for _ in range(length))


def sign_hmac_sha512(message: str, secret_key: str) -> str:
    """
    Generate a base64-encoded HMAC-SHA512 signature.

    :param message: The message to be signed (usually a JSON string).
    :param secret_key: The secret key used for signing.
    :return: Base64-encoded signature string.
    """
    byte_key = secret_key.encode('utf-8')
    byte_message = message.encode('utf-8')

    signature = hmac.new(byte_key, byte_message, hashlib.sha512).digest()
    return base64.b64encode(signature).decode('utf-8')


def create_fake_mac_address() -> str:
    """
    Generate a random MAC address in the format XX:XX:XX:XX:XX:XX.

    :return: A random MAC address in the format XX:XX:XX:XX:XX:XX.
    """
    return rstr.xeger(mac_address_regex)


phone_number_regex = r'^(\+?265|0)[89]{2}[0-9]{7}$'
mac_address_regex = r'^([0-9A-Fa-f]{2}([-:])){5}([0-9A-Fa-f]{2})$'
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


def generate_invoice_number():
    return "INV" + datetime.now().strftime("%Y%m%d%H%M%S")


def calculate_tax(amount, tax_rate) -> float:
    return amount / (1 + tax_rate / 100)
