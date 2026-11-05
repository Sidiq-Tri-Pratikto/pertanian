"""Public error definitions: the one place internal codes map to what clients see."""

from dataclasses import dataclass, field
from typing import Any

from app.core.errors import codes

_FALLBACK_MESSAGE = "Permintaan belum dapat diselesaikan. Hubungi dukungan dan sebutkan ID referensi yang ditampilkan."


@dataclass(frozen=True)
class PublicError:
    """Safe public representation of a failure.

    Attributes:
        code (str): Documented public code.
        http_status (int): Response status.
        message (str): Two-clause message: what happened, what to do next.
        recovery (dict[str, Any]): Retry guidance.
    """

    code: str
    http_status: int
    message: str
    recovery: dict[str, Any] = field(default_factory=lambda: {"retryable": False})


FALLBACK_PUBLIC_ERROR = PublicError("INTERNAL_ERROR", 500, _FALLBACK_MESSAGE)

PUBLIC_ERROR_BY_CODE: dict[str, PublicError] = {
    codes.APP_UNKNOWN: FALLBACK_PUBLIC_ERROR,
    codes.APP_REQUEST_INVALID: PublicError(
        "BAD_REQUEST", 400, "Permintaan belum dapat diproses. Periksa isian Anda lalu coba lagi."
    ),
    codes.APP_NOT_FOUND: PublicError(
        "NOT_FOUND", 404, "Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi."
    ),
    codes.APP_CONFLICT: PublicError(
        "CONFLICT", 409, "Permintaan bertentangan dengan kondisi saat ini. Tinjau datanya lalu coba lagi."
    ),
    codes.APP_DB_ERROR: PublicError(
        "DATA_ERROR",
        500,
        "Permintaan gagal karena kesalahan data. Hubungi dukungan dan sebutkan ID referensi.",
    ),
    codes.APP_DB_UNAVAILABLE: PublicError(
        "DATABASE_UNAVAILABLE",
        503,
        "Layanan data sedang tidak tersedia. Coba lagi beberapa menit lagi.",
        {"retryable": True, "retry_after_seconds": 30, "max_attempts": 3},
    ),
    codes.APP_CAPABILITY_UNAVAILABLE: PublicError(
        "CAPABILITY_UNAVAILABLE",
        403,
        "Fitur ini tidak tersedia pada layanan ini. Hubungi pengelola layanan bila Anda memerlukannya.",
    ),
}

PUBLIC_ERROR_BY_STATUS: dict[int, PublicError] = {
    400: PublicError("BAD_REQUEST", 400, "Permintaan belum dapat diproses. Periksa isian Anda lalu coba lagi."),
    401: PublicError("UNAUTHORIZED", 401, "Anda perlu masuk terlebih dahulu. Masuk lalu coba lagi."),
    403: PublicError(
        "FORBIDDEN", 403, "Anda tidak memiliki akses untuk permintaan ini. Hubungi pemilik data bila perlu akses."
    ),
    404: PublicError("NOT_FOUND", 404, "Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi."),
    405: PublicError("METHOD_NOT_ALLOWED", 405, "Metode permintaan ini tidak didukung. Gunakan metode yang didukung."),
    409: PublicError(
        "CONFLICT", 409, "Permintaan bertentangan dengan kondisi saat ini. Tinjau datanya lalu coba lagi."
    ),
    422: PublicError("VALIDATION_FAILED", 422, "Ada isian yang belum valid. Perbaiki isian tersebut lalu coba lagi."),
    429: PublicError(
        "RATE_LIMITED",
        429,
        "Terlalu banyak permintaan diterima. Tunggu sebentar lalu coba lagi.",
        {"retryable": True, "retry_after_seconds": 60, "max_attempts": 3},
    ),
}


_DEFAULT_FIELD_MESSAGE = "Nilai isian ini belum valid. Periksa lalu coba lagi."
_FIELD_MESSAGES = {
    "missing": "Isian ini wajib diisi.",
    "string_type": "Isi dengan teks.",
    "string_too_short": "Isian ini terlalu pendek.",
    "string_too_long": "Isian ini terlalu panjang.",
    "int_type": "Isi dengan bilangan bulat.",
    "int_parsing": "Isi dengan bilangan bulat.",
    "float_type": "Isi dengan angka.",
    "float_parsing": "Isi dengan angka.",
    "decimal_type": "Isi dengan angka desimal.",
    "decimal_parsing": "Isi dengan angka desimal.",
    "bool_type": "Pilih benar atau salah.",
    "bool_parsing": "Pilih benar atau salah.",
    "uuid_type": "Pengenal ini tidak valid.",
    "uuid_parsing": "Pengenal ini tidak valid.",
    "date_parsing": "Isi dengan tanggal yang valid.",
    "datetime_parsing": "Isi dengan tanggal dan waktu yang valid.",
    "greater_than": "Nilai terlalu kecil.",
    "greater_than_equal": "Nilai terlalu kecil.",
    "less_than": "Nilai terlalu besar.",
    "less_than_equal": "Nilai terlalu besar.",
    "enum": "Pilih salah satu nilai yang tersedia.",
    "literal_error": "Pilih salah satu nilai yang tersedia.",
    "json_invalid": "Isi permintaan bukan JSON yang valid.",
}


def field_message(error_type: str) -> str:
    """Resolve a validation error type to an Indonesian field message.

    Args:
        error_type (str): The validator's error type.

    Returns:
        str: The field message, or a safe default for an unmapped type.
    """
    return _FIELD_MESSAGES.get(error_type, _DEFAULT_FIELD_MESSAGE)


def public_error_for_code(code: str) -> PublicError:
    """Resolve an internal code to its public definition.

    Args:
        code (str): Internal error code.

    Returns:
        PublicError: The mapped definition, or the fallback for an unregistered code.
    """
    return PUBLIC_ERROR_BY_CODE.get(code, FALLBACK_PUBLIC_ERROR)


def public_error_for_status(status_code: int) -> PublicError:
    """Resolve a framework HTTP status to a fixed public definition.

    Args:
        status_code (int): HTTP status raised by the framework.

    Returns:
        PublicError: A safe definition carrying that status.
    """
    known = PUBLIC_ERROR_BY_STATUS.get(status_code)
    if known is not None:
        return known
    code = "INTERNAL_ERROR" if status_code >= 500 else "HTTP_ERROR"
    return PublicError(code, status_code, _FALLBACK_MESSAGE)


def error_response(public: PublicError, request_id: str, *, details: list[dict[str, Any]] | None = None) -> dict:
    """Build the public envelope.

    Args:
        public (PublicError): The public definition.
        request_id (str): The failure's reference ID.
        details (list[dict[str, Any]] | None, optional): Safe field errors for validation failures. Defaults to None.

    Returns:
        dict: The response body.
    """
    error: dict[str, Any] = {
        "code": public.code,
        "message": public.message,
        "request_id": request_id,
        "recovery": dict(public.recovery),
    }
    if details is not None:
        error["details"] = details
    return {"error": error}
