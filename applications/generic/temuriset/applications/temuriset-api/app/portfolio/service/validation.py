"""Publication rules (PRD FR03). A draft may be anything; a published version must say these things."""

from app.core.errors import codes
from app.core.errors.base import AppError
from app.portfolio.model.schema import VersionResponse

TITLE_MIN, TITLE_MAX, SUMMARY_MAX = 5, 120, 350


class PublicationInvalidError(AppError):
    """The draft is not ready to publish; ``details`` names each field in Indonesian."""

    code = codes.APP_PUBLICATION_INVALID

    def __init__(self, details: list[dict]) -> None:
        """Carry the field errors.

        Args:
            details (list[dict]): ``loc``, ``msg`` and ``type`` per field.
        """
        super().__init__(public_fields={"details": details})


def publication_errors(draft: VersionResponse) -> list[dict]:
    """List what stops a draft from being published, in field order.

    Args:
        draft (VersionResponse): The draft.

    Returns:
        list[dict]: Field errors; empty when the draft may be published.
    """
    checks = [
        ("title", not TITLE_MIN <= len(draft.title) <= TITLE_MAX, "Judul perlu 5 sampai 120 karakter."),
        ("summary", len(draft.summary) > SUMMARY_MAX, "Ringkasan paling banyak 350 karakter."),
        ("problem", not draft.problem, "Isi masalah yang diselesaikan."),
        ("solution", not draft.solution, "Isi solusi saat ini."),
        ("intended_users", not draft.intended_users, "Isi siapa penggunanya."),
        ("stage", draft.stage is None, "Pilih tahap inovasi."),
        (
            "facts",
            not any(fact.timing == "CURRENT" for fact in draft.facts),
            "Tambahkan setidaknya satu kemampuan yang sudah ada saat ini.",
        ),
    ]
    return [
        {"loc": ["body", field], "msg": message, "type": "publication"} for field, failed, message in checks if failed
    ]
