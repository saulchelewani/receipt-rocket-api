import base64
import hashlib
import hmac
import secrets
import string
from datetime import datetime

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


def calculate_tax(amount, tax_rate) -> float:
    return amount / (1 + tax_rate / 100)


def b10_2_b64(number: int) -> str:
    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    if number == 0:
        return "A"
    result = ""
    while number > 0:
        remainder = number % 64
        result = base64_chars[remainder] + result
        number //= 64
    return result


def to_julian_date(date: datetime) -> int:
    year = date.year
    month = date.month
    day = date.day

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + (a // 4)

    return int((365.25 * (year + 4716))) + int((30.6001 * (month + 1))) + day + b - 1524


def generate_combined_string(
        taxpayer_id: int,
        position: int,
        julian_date: int,
        transaction_count: int
) -> str:
    return f"{b10_2_b64(taxpayer_id)}-{b10_2_b64(position)}-{b10_2_b64(julian_date)}-{b10_2_b64(transaction_count)}"


def generate_invoice_number(
        taxpayer_id: int,
        position: int,
        transaction_date: datetime,
        transaction_count: int
) -> str:
    return generate_combined_string(taxpayer_id, position, to_julian_date(transaction_date), transaction_count)


def generate_password(length=12) -> str:
    if length < 6:
        raise ValueError("Password length should be at least 6 characters")

    characters = (
            string.ascii_letters +  # a-zA-Z
            string.digits +  # 0-9
            string.punctuation  # !@#$%^&*()_+-=[]{} etc.
    )

    # Ensure at least one character from each category
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation)
    ]

    # Fill the rest of the password length with random choices
    password += [secrets.choice(characters) for _ in range(length - 4)]

    # Shuffle to avoid predictable order
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
