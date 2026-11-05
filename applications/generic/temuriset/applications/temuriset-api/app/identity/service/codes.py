"""One-time codes and session tokens: generated with ``secrets``, stored only as hashes."""

import hashlib
import hmac
import secrets

CODE_DIGITS = 6
MAX_CODE_ATTEMPTS = 5


def new_code() -> str:
    """Return a uniformly random six-digit code.

    Returns:
        str: The code, zero-padded.
    """
    return f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"


def new_salt() -> str:
    """Return a per-code salt.

    Returns:
        str: 32 hex characters.
    """
    return secrets.token_hex(16)


def hash_code(code: str, salt: str) -> str:
    """Hash a code with its salt.

    Args:
        code (str): The code.
        salt (str): The code's salt.

    Returns:
        str: Hex SHA-256.
    """
    return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()


def code_matches(code: str, salt: str, stored_sha256: str) -> bool:
    """Compare a submitted code in constant time.

    Args:
        code (str): Submitted code.
        salt (str): The stored salt.
        stored_sha256 (str): The stored hash.

    Returns:
        bool: True when it matches.
    """
    return hmac.compare_digest(hash_code(code, salt), stored_sha256)


def new_token() -> str:
    """Return an opaque 32-byte session or invitation token.

    Returns:
        str: URL-safe token.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for storage and lookup.

    Args:
        token (str): The token.

    Returns:
        str: Hex SHA-256.
    """
    return hashlib.sha256(token.encode()).hexdigest()
