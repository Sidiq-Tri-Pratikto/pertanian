"""Purpose-bound authenticated encryption for opaque adapter secrets."""

from base64 import b64decode, urlsafe_b64encode
from binascii import Error
from hashlib import sha256
from hmac import compare_digest

from cryptography.fernet import Fernet, InvalidToken


class InvalidEnvelopeError(ValueError):
    """A secret envelope failed authentication or purpose validation."""


def validated_key(key: str | bytes) -> bytes:
    """Return a canonical URL-safe Fernet key or raise ValueError."""
    try:
        encoded = key.encode("ascii") if isinstance(key, str) else key
        decoded = b64decode(encoded, altchars=b"-_", validate=True)
    except (UnicodeError, Error):
        raise ValueError("Invalid secret envelope key") from None
    if len(decoded) != 32 or urlsafe_b64encode(decoded) != encoded:
        raise ValueError("Invalid secret envelope key")
    return encoded


def seal(key: str | bytes, purpose: str, value: bytes) -> bytes:
    """Encrypt bytes for one purpose under a validated Fernet key."""
    purpose_digest = sha256(purpose.encode("utf-8")).digest()
    return Fernet(validated_key(key)).encrypt(purpose_digest + value)


def open_sealed(key: str | bytes, purpose: str, envelope: bytes) -> bytes:
    """Decrypt authenticated bytes or raise InvalidEnvelopeError for a mismatched envelope."""
    cipher = Fernet(validated_key(key))
    try:
        plaintext = cipher.decrypt(envelope)
    except InvalidToken:
        raise InvalidEnvelopeError("Invalid secret envelope") from None
    purpose_digest = sha256(purpose.encode("utf-8")).digest()
    if not compare_digest(plaintext[: len(purpose_digest)], purpose_digest):
        raise InvalidEnvelopeError("Invalid secret envelope")
    return plaintext[len(purpose_digest) :]
