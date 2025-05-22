import secrets
import string


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