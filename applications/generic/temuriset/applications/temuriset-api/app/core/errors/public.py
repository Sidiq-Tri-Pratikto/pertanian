"""Public error definitions: the one place internal codes map to what clients see."""

from dataclasses import dataclass, field, replace
from typing import Any

from app.core.errors import codes
from app.core.locale import locale

_FALLBACK_MESSAGE = "Permintaan belum dapat diselesaikan. Hubungi dukungan dan sebutkan ID referensi yang ditampilkan."
_FALLBACK_MESSAGE_EN = "The request could not be completed. Contact support and quote the reference ID shown."


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


_FIXED_FIELDS = frozenset({"code", "message", "request_id", "recovery"})

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
    codes.APP_MAIL_UNAVAILABLE: PublicError(
        "MAIL_UNAVAILABLE",
        503,
        "Pengiriman email belum tersedia. Hubungi pengelola layanan.",
    ),
    codes.APP_MAIL_RELAY_RETRY: PublicError(
        "MAIL_RELAY_RETRY",
        503,
        "Pengiriman email tertunda. Tunggu hingga layanan mencoba lagi.",
        {"retryable": True, "retry_after_seconds": 5, "max_attempts": 8},
    ),
    codes.APP_MAIL_RELAY_REJECTED: PublicError(
        "MAIL_RELAY_REJECTED",
        503,
        "Email tidak dapat dikirim. Hubungi pengelola layanan.",
    ),
    codes.APP_CALENDAR_UNAVAILABLE: PublicError(
        "CALENDAR_UNAVAILABLE", 503, "Kalender luar belum dapat diakses. Periksa sambungan kalender Anda."
    ),
    codes.APP_CALENDAR_CALLBACK_INVALID: PublicError(
        "CALENDAR_CALLBACK_INVALID", 400, "Kalender belum tersambung. Mulai lagi dari pengaturan kalender."
    ),
    codes.APP_STORAGE_UNAVAILABLE: PublicError(
        "STORAGE_UNAVAILABLE",
        503,
        "Penyimpanan berkas belum dapat diakses. Coba lagi nanti.",
    ),
    codes.APP_CAPABILITY_UNAVAILABLE: PublicError(
        "CAPABILITY_UNAVAILABLE",
        403,
        "Fitur ini tidak tersedia pada layanan ini. Hubungi pengelola layanan bila Anda memerlukannya.",
    ),
    codes.APP_UNAUTHENTICATED: PublicError(
        "UNAUTHENTICATED", 401, "Anda perlu masuk terlebih dahulu. Masuk lalu coba lagi."
    ),
    codes.APP_STALE_VERSION: PublicError(
        "STALE_VERSION",
        409,
        "Data ini sudah diubah sejak Anda membukanya. Muat ulang versi terbaru lalu ulangi perubahan Anda.",
    ),
    codes.APP_IDEMPOTENCY_CONFLICT: PublicError(
        "IDEMPOTENCY_CONFLICT",
        409,
        "Kunci permintaan ini sudah dipakai untuk isi berbeda. Gunakan kunci baru untuk permintaan baru.",
    ),
    codes.APP_FORBIDDEN: PublicError(
        "FORBIDDEN", 403, "Anda tidak memiliki akses untuk permintaan ini. Hubungi pemilik data bila perlu akses."
    ),
    codes.APP_CODE_INVALID: PublicError(
        "CODE_INVALID", 422, "Kode verifikasi tidak cocok. Periksa kode di email Anda lalu coba lagi."
    ),
    codes.APP_CODE_EXPIRED: PublicError(
        "CODE_EXPIRED", 422, "Kode verifikasi sudah tidak berlaku. Minta kode baru lalu masukkan kode tersebut."
    ),
    codes.APP_RATE_LIMITED: PublicError(
        "RATE_LIMITED",
        429,
        "Terlalu banyak permintaan kode. Tunggu sebentar lalu coba lagi.",
        {"retryable": True, "retry_after_seconds": 60, "max_attempts": 3},
    ),
    codes.APP_STALE_CONTEXT: PublicError(
        "STALE_CONTEXT",
        409,
        "Anda kini bertindak sebagai pihak lain di tab berbeda. Muat ulang halaman lalu ulangi tindakan Anda.",
    ),
    codes.APP_INVITATION_EXPIRED: PublicError(
        "INVITATION_EXPIRED",
        410,
        "Undangan ini sudah tidak berlaku. Minta undangan baru kepada pengelola organisasi.",
    ),
    codes.APP_PUBLICATION_INVALID: PublicError(
        "VALIDATION_FAILED", 422, "Draf belum siap diterbitkan. Lengkapi isian yang ditandai lalu terbitkan lagi."
    ),
    codes.APP_FILE_TOO_LARGE: PublicError(
        "FILE_TOO_LARGE", 422, "Berkas melebihi batas ukuran. Kecilkan berkas lalu unggah lagi."
    ),
    codes.APP_FILE_TYPE_UNSUPPORTED: PublicError(
        "FILE_TYPE_UNSUPPORTED", 422, "Jenis berkas ini tidak didukung. Unggah PDF, DOCX, PNG, JPEG atau WEBP."
    ),
    codes.APP_FILE_NOT_AVAILABLE: PublicError(
        "FILE_NOT_AVAILABLE",
        409,
        "Berkas ini belum tersedia atau ditolak saat pemeriksaan. Tunggu pemeriksaan selesai.",
    ),
    codes.APP_GRANT_REVOKED: PublicError(
        "GRANT_REVOKED",
        403,
        "Akses ke dokumen ini sudah dicabut. Salinan yang sudah diunduh sebelumnya tidak dapat ditarik kembali.",
    ),
    codes.APP_FIELDS_INVALID: PublicError(
        "VALIDATION_FAILED", 422, "Ada isian yang belum valid. Perbaiki isian yang ditandai lalu simpan lagi."
    ),
    codes.APP_INVALID_TRANSITION: PublicError(
        "INVALID_TRANSITION",
        409,
        "Status ini tidak dapat diubah dengan cara itu. Muat ulang untuk melihat status terbaru.",
    ),
    codes.APP_DUPLICATE_PITCH: PublicError(
        "DUPLICATE_PITCH",
        409,
        "Pitching untuk kebutuhan dan mandat ini sudah ada. Buka pitching yang ada untuk melanjutkannya.",
    ),
    codes.APP_TARGET_CLOSED: PublicError(
        "TARGET_CLOSED",
        409,
        "Mandat ini tidak lagi menerima pitching baru. Diskusi yang sudah berjalan tetap berlanjut.",
    ),
    codes.APP_PREFLIGHT_STALE: PublicError(
        "PREFLIGHT_STALE",
        409,
        "Ada yang berubah sejak pemeriksaan. Periksa ulang sebelum mengirim; brief Anda tetap tersimpan.",
    ),
    codes.APP_NOT_READY: PublicError(
        "NOT_READY",
        422,
        "Masih ada syarat pengajuan yang belum selesai. Lengkapi syarat yang disebutkan lalu periksa ulang.",
    ),
    codes.APP_REQUIRED_ANSWERS_MISSING: PublicError(
        "REQUIRED_ANSWERS_MISSING",
        422,
        "Masih ada pertanyaan wajib yang belum dijawab. Jawab pertanyaan yang ditandai lalu kirim ulang.",
    ),
    codes.APP_BOOKING_CONFLICT: PublicError(
        "BOOKING_CONFLICT",
        409,
        "Waktu ini bentrok dengan jadwal peserta. Pilih waktu lain atau usulkan waktu baru.",
    ),
    codes.APP_PROPOSAL_CLOSED: PublicError(
        "PROPOSAL_CLOSED",
        409,
        "Usulan waktu ini sudah tidak terbuka. Muat ulang untuk melihat usulan terbaru.",
    ),
    codes.APP_ENTITY_REQUIRED: PublicError(
        "ENTITY_REQUIRED",
        422,
        "Kerja Sama ekuitas memerlukan badan usaha yang sudah berdiri. Pilih jenis lain atau dirikan badan usaha dulu.",
    ),
    codes.APP_MEETING_NOT_COMPLETED: PublicError(
        "MEETING_NOT_COMPLETED",
        409,
        "Ringkasan Kerja Sama diusulkan setelah pertemuan selesai. Catat hasil pertemuan bersama pihak lain dulu.",
    ),
    codes.APP_LISTING_SUSPENDED: PublicError(
        "LISTING_SUSPENDED",
        409,
        "Daftar ini sedang ditangguhkan. Hubungi pengelola layanan bila Anda merasa ini keliru.",
    ),
    codes.APP_SUMMARY_REFUSED: PublicError(
        "SUMMARY_REFUSED", 200, "Ringkasan otomatis ditolak. Lanjutkan dengan menyunting brief."
    ),
    codes.APP_SUMMARY_UNAVAILABLE: PublicError(
        "SUMMARY_UNAVAILABLE", 200, "Ringkasan otomatis tidak tersedia. Lanjutkan dengan menyunting brief."
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


# English for every message above, keyed like the Indonesian source; codes and recovery stay language-neutral.
_EN_BY_CODE: dict[str, str] = {
    codes.APP_UNKNOWN: _FALLBACK_MESSAGE_EN,
    codes.APP_REQUEST_INVALID: "The request could not be processed. Check your entries and try again.",
    codes.APP_NOT_FOUND: "The requested item was not found. Check the address and try again.",
    codes.APP_CONFLICT: "The request conflicts with the current state. Review the data and try again.",
    codes.APP_DB_ERROR: "The request failed because of a data error. Contact support and quote the reference ID.",
    codes.APP_DB_UNAVAILABLE: "The data service is unavailable right now. Try again in a few minutes.",
    codes.APP_MAIL_UNAVAILABLE: "Email delivery is not available yet. Contact the service operator.",
    codes.APP_MAIL_RELAY_RETRY: "Email delivery is delayed. Wait while the service retries.",
    codes.APP_MAIL_RELAY_REJECTED: "The email could not be sent. Contact the service operator.",
    codes.APP_CALENDAR_UNAVAILABLE: "The external calendar cannot be reached. Check your calendar connection.",
    codes.APP_CALENDAR_CALLBACK_INVALID: "The calendar is not connected. Start again from the calendar settings.",
    codes.APP_STORAGE_UNAVAILABLE: "File storage cannot be reached. Try again later.",
    codes.APP_CAPABILITY_UNAVAILABLE: (
        "This feature is not available on this service. Contact the operator if you need it."
    ),
    codes.APP_UNAUTHENTICATED: "You need to sign in first. Sign in and try again.",
    codes.APP_STALE_VERSION: "This was changed after you opened it. Reload the latest version and repeat your change.",
    codes.APP_IDEMPOTENCY_CONFLICT: "This request key was used for different content. Use a new key for a new request.",
    codes.APP_FORBIDDEN: "You do not have access to this request. Ask the data owner if you need access.",
    codes.APP_CODE_INVALID: "The verification code does not match. Check the code in your email and try again.",
    codes.APP_CODE_EXPIRED: "The verification code has expired. Request a new code and enter it.",
    codes.APP_RATE_LIMITED: "Too many code requests. Wait a moment and try again.",
    codes.APP_STALE_CONTEXT: "You now act as another party in a different tab. Reload the page and repeat your action.",
    codes.APP_INVITATION_EXPIRED: "This invitation has expired. Ask the organization manager for a new one.",
    codes.APP_PUBLICATION_INVALID: "The draft is not ready to publish. Complete the marked fields and publish again.",
    codes.APP_FILE_TOO_LARGE: "The file is over the size limit. Make it smaller and upload it again.",
    codes.APP_FILE_TYPE_UNSUPPORTED: "This file type is not supported. Upload a PDF, DOCX, PNG, JPEG or WEBP.",
    codes.APP_FILE_NOT_AVAILABLE: (
        "This file is not available yet or was rejected by the check. Wait for the check to finish."
    ),
    codes.APP_GRANT_REVOKED: "Access to this document was revoked. Copies downloaded earlier cannot be recalled.",
    codes.APP_FIELDS_INVALID: "Some entries are not valid. Fix the marked entries and save again.",
    codes.APP_INVALID_TRANSITION: "This status cannot be changed that way. Reload to see the latest status.",
    codes.APP_DUPLICATE_PITCH: "A pitch for this need and mandate already exists. Open it to continue.",
    codes.APP_TARGET_CLOSED: "This mandate no longer accepts new pitches. Discussions already under way continue.",
    codes.APP_PREFLIGHT_STALE: "Something changed since the check. Check again before sending; your brief is kept.",
    codes.APP_NOT_READY: (
        "Some submission requirements are not complete. Complete the named requirement and check again."
    ),
    codes.APP_REQUIRED_ANSWERS_MISSING: (
        "Some required questions are unanswered. Answer the marked questions and resubmit."
    ),
    codes.APP_BOOKING_CONFLICT: (
        "This time clashes with a participant's schedule. Choose another time or propose a new one."
    ),
    codes.APP_PROPOSAL_CLOSED: "This time proposal is no longer open. Reload to see the latest proposal.",
    codes.APP_ENTITY_REQUIRED: (
        "An equity partnership needs an incorporated company. Choose another type or incorporate first."
    ),
    codes.APP_MEETING_NOT_COMPLETED: (
        "A partnership summary follows a completed meeting. Record the meeting outcome with the other party first."
    ),
    codes.APP_LISTING_SUSPENDED: (
        "This listing is suspended. Contact the service operator if you think this is a mistake."
    ),
    codes.APP_SUMMARY_REFUSED: "The automatic summary was refused. Continue by editing the brief.",
    codes.APP_SUMMARY_UNAVAILABLE: "The automatic summary is not available. Continue by editing the brief.",
}

_EN_BY_STATUS: dict[int, str] = {
    400: "The request could not be processed. Check your entries and try again.",
    401: "You need to sign in first. Sign in and try again.",
    403: "You do not have access to this request. Ask the data owner if you need access.",
    404: "The requested item was not found. Check the address and try again.",
    405: "This request method is not supported. Use a supported method.",
    409: "The request conflicts with the current state. Review the data and try again.",
    422: "Some entries are not valid. Fix them and try again.",
    429: "Too many requests were received. Wait a moment and try again.",
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
_DEFAULT_FIELD_MESSAGE_EN = "This value is not valid. Check it and try again."
_FIELD_MESSAGES_EN = {
    "missing": "This field is required.",
    "string_type": "Enter text.",
    "string_too_short": "This entry is too short.",
    "string_too_long": "This entry is too long.",
    "int_type": "Enter a whole number.",
    "int_parsing": "Enter a whole number.",
    "float_type": "Enter a number.",
    "float_parsing": "Enter a number.",
    "decimal_type": "Enter a decimal number.",
    "decimal_parsing": "Enter a decimal number.",
    "bool_type": "Choose true or false.",
    "bool_parsing": "Choose true or false.",
    "uuid_type": "This identifier is not valid.",
    "uuid_parsing": "This identifier is not valid.",
    "date_parsing": "Enter a valid date.",
    "datetime_parsing": "Enter a valid date and time.",
    "greater_than": "The value is too small.",
    "greater_than_equal": "The value is too small.",
    "less_than": "The value is too large.",
    "less_than_equal": "The value is too large.",
    "enum": "Choose one of the available values.",
    "literal_error": "Choose one of the available values.",
    "json_invalid": "The request body is not valid JSON.",
}


def field_message(error_type: str) -> str:
    """Resolve a validation error type to a field message in the request's language.

    Args:
        error_type (str): The validator's error type.

    Returns:
        str: The field message, or a safe default for an unmapped type.
    """
    if locale() == "en":
        return _FIELD_MESSAGES_EN.get(error_type, _DEFAULT_FIELD_MESSAGE_EN)
    return _FIELD_MESSAGES.get(error_type, _DEFAULT_FIELD_MESSAGE)


def public_error_for_code(code: str) -> PublicError:
    """Resolve an internal code to its public definition, worded in the request's language.

    Args:
        code (str): Internal error code.

    Returns:
        PublicError: The mapped definition, or the fallback for an unregistered code.
    """
    public = PUBLIC_ERROR_BY_CODE.get(code, FALLBACK_PUBLIC_ERROR)
    if locale() == "en":
        return replace(public, message=_EN_BY_CODE.get(code, _FALLBACK_MESSAGE_EN))
    return public


def public_error_for_status(status_code: int) -> PublicError:
    """Resolve a framework HTTP status to a fixed public definition in the request's language.

    Args:
        status_code (int): HTTP status raised by the framework.

    Returns:
        PublicError: A safe definition carrying that status.
    """
    english = locale() == "en"
    known = PUBLIC_ERROR_BY_STATUS.get(status_code)
    if known is not None:
        return replace(known, message=_EN_BY_STATUS[status_code]) if english else known
    code = "INTERNAL_ERROR" if status_code >= 500 else "HTTP_ERROR"
    return PublicError(code, status_code, _FALLBACK_MESSAGE_EN if english else _FALLBACK_MESSAGE)


def error_response(
    public: PublicError,
    request_id: str,
    *,
    details: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """Build the public envelope.

    Args:
        public (PublicError): The public definition.
        request_id (str): The failure's reference ID.
        details (list[dict[str, Any]] | None, optional): Safe field errors for validation failures. Defaults to None.
        extra (dict[str, Any] | None, optional): Safe typed fields such as ``current_version``; they never replace
            the fixed fields. Defaults to None.

    Returns:
        dict: The response body.
    """
    error: dict[str, Any] = {
        "code": public.code,
        "message": public.message,
        "request_id": request_id,
        "recovery": dict(public.recovery),
    }
    error.update({key: value for key, value in (extra or {}).items() if key not in _FIXED_FIELDS})
    if details is not None:
        error["details"] = details
    return {"error": error}
