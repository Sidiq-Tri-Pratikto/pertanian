"""Sanitize diagnostics before they reach any sink."""

import re
from collections.abc import Mapping
from itertools import islice
from typing import Any

REDACTED = "[Filtered]"
_UNAVAILABLE = "[unavailable]"
_MAX_DEPTH = 8
_MAX_ITEMS = 100
_MAX_TEXT = 2048

_SENSITIVE_KEY_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "body",
    "content",
    "cookie",
    "input",
    "messages",
    "password",
    "proof",
    "prompt",
    "secret",
    "token",
)
_BEARER = re.compile(r"(?i)\bBearer\s+[^\s,;]+")
_URL_USERINFO = re.compile(r"(?i)(\b[a-z][a-z0-9+.-]*://)[^/\s]*@")
_PRIVATE_FIELD = re.compile(
    r"(?i)[\"']?(?:api[_-]?key|password|passwd|token|access[_-]?token|refresh[_-]?token|secret|proof|"
    r"authorization|cookie|prompt|input|body|content|messages)(?:[_-][A-Za-z0-9]+)*[\"']?\s*[:=]"
)
_API_TOKEN = re.compile(r"(?i)\b(?:sk-|hdd_)[A-Za-z0-9_-]{4,}")
_EMAIL = re.compile(r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def redact_text(value: str) -> str:
    """Redact credentials and emails from diagnostic text.

    Args:
        value (str): Raw text.

    Returns:
        str: Single-line, bounded, redacted text. Text holding a private field is dropped whole.
    """
    try:
        if _PRIVATE_FIELD.search(value):
            return REDACTED
        text = _URL_USERINFO.sub(lambda match: f"{match[1]}{REDACTED}@", value)
        text = _BEARER.sub(f"Bearer {REDACTED}", text)
        text = _API_TOKEN.sub(REDACTED, text)
        text = _EMAIL.sub(REDACTED, text)
        return text.replace("\r", " ").replace("\n", " ")[:_MAX_TEXT]
    except Exception:  # noqa: BLE001 - error handling must not fail while handling an error (EH-10)
        return _UNAVAILABLE


def sanitize(value: Any, *, _depth: int = 0) -> Any:
    """Return a bounded safe copy of a value.

    Args:
        value (Any): Scalar or nested mapping and sequence.

    Returns:
        Any: The sanitized copy. Unsupported types become the redaction marker.
    """
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return redact_text(value)
    if _depth >= _MAX_DEPTH:
        return REDACTED
    if isinstance(value, Mapping):
        return {
            redact_text(str(key))[:128]: REDACTED if _is_sensitive_key(str(key)) else sanitize(item, _depth=_depth + 1)
            for key, item in islice(value.items(), _MAX_ITEMS)
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item, _depth=_depth + 1) for item in islice(value, _MAX_ITEMS)]
    return REDACTED


def build_debug_info(error: BaseException) -> dict[str, str]:
    """Build the minimum diagnostic schema for a raw error.

    Args:
        error (BaseException): The raw error.

    Returns:
        dict[str, str]: ``error_type`` and the sanitized ``original_message``.
    """
    try:
        message = redact_text(str(error)[:_MAX_TEXT])
    except Exception:  # noqa: BLE001 - error handling must not fail while handling an error (EH-10)
        message = _UNAVAILABLE
    return {"error_type": type(error).__name__[:128], "original_message": message}


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)
