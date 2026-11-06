"""Opaque demo credentials. Only digests are stored; the token is derived again for a proven replay."""

import hashlib
import hmac
import re
from uuid import UUID

TOKEN_PREFIX = "hdd_"
OPERATION_ID = re.compile(r"^[A-Za-z0-9_-]{22,128}$")  # at least 128 bits as base64url
REPLAY_PROOF = re.compile(r"^[A-Za-z0-9_-]{43,256}$")  # at least 256 bits as base64url
_DOMAIN = b"hematdaya-demo-create-v1"


def digest(value: str) -> bytes:
    """Return the stored digest of a high-entropy secret.

    Args:
        value (str): A token or replay proof.

    Returns:
        bytes: SHA-256 digest.
    """
    return hashlib.sha256(value.encode()).digest()


def _field(value: bytes) -> bytes:
    return len(value).to_bytes(4, "big") + value


def derive_token(key: bytes, key_version: str, session_id: UUID, operation_id: str, replay_proof: str) -> str:
    """Derive the bearer token with HMAC-SHA-256 over a length-prefixed encoding, so fields cannot shift.

    Args:
        key (bytes): The versioned HMAC key.
        key_version (str): Its version, carried in the token.
        session_id (UUID): The session.
        operation_id (str): The creation operation.
        replay_proof (str): The client's replay proof.

    Returns:
        str: The opaque bearer token.
    """
    message = _DOMAIN + _field(session_id.bytes) + _field(operation_id.encode()) + _field(replay_proof.encode())
    mac = hmac.new(key, message, hashlib.sha256).hexdigest()
    return f"{TOKEN_PREFIX}{key_version}_{mac}"
