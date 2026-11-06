"""Tests for authenticated envelopes shared by gated adapters."""

import base64

import pytest
from cryptography.fernet import Fernet

from app.core.secret_envelope import InvalidEnvelopeError, open_sealed, seal, validated_key


def test_envelope_separates_purposes_and_keys() -> None:
    """
    Condition:
    - A binary value is sealed for a specific key and purpose.

    Expected:
    - Only the original key and purpose open the value, and tampering is rejected.
    """
    key = Fernet.generate_key()
    value = b"synthetic-value\x00\xff"
    envelope = seal(key, "email:v1", value)
    assert value not in envelope
    assert open_sealed(key.decode("ascii"), "email:v1", envelope) == value
    tampered = bytearray(base64.urlsafe_b64decode(envelope))
    tampered[-1] ^= 1
    for wrong_key, purpose, token in (
        (key, "calendar:v1", envelope),
        (Fernet.generate_key(), "email:v1", envelope),
        (key, "email:v1", base64.urlsafe_b64encode(tampered)),
    ):
        with pytest.raises(InvalidEnvelopeError, match="Invalid secret envelope"):
            open_sealed(wrong_key, purpose, token)


def test_key_validation_is_strict() -> None:
    """
    Condition:
    - The configured key is valid, malformed, or contains trailing data.

    Expected:
    - Only a canonical Fernet key is accepted.
    """
    key = Fernet.generate_key()
    assert validated_key(key.decode("ascii")) == key
    for invalid in ("wrong length", "☃", key + b"!", key.replace(b"=", b"")):
        with pytest.raises(ValueError, match="Invalid secret envelope key"):
            validated_key(invalid)
