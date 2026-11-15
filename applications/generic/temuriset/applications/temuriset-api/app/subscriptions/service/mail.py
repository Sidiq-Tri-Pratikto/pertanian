"""The plain-text emails a quick subscriber receives. Brief on purpose: the details need a normal signup."""

from typing import Any

from app.core.settings import Settings
from app.subscriptions.repository.sqlalchemy.models import InvestorSubscriptionRecord
from app.subscriptions.service.matching import STAGE_LABEL, Match

_SUMMARY_CHARS = 240


def _origin(settings_or_origin: Settings | str) -> str:
    origin = settings_or_origin if isinstance(settings_or_origin, str) else settings_or_origin.web_origin
    return origin.rstrip("/")


def _short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _SUMMARY_CHARS else text[: _SUMMARY_CHARS - 1].rstrip() + "…"


def topics_line(topics: dict[str, Any]) -> str:
    """Describe a subscriber's topics in one line.

    Args:
        topics (dict[str, Any]): ``sectors``, ``stages`` and ``keywords``.

    Returns:
        str: For example ``sektor Air dan sanitasi; tahap Prototipe``.
    """
    parts = []
    if topics.get("sectors"):
        parts.append("sektor " + ", ".join(topics["sectors"]))
    if topics.get("stages"):
        parts.append("tahap " + ", ".join(STAGE_LABEL.get(stage, stage) for stage in topics["stages"]))
    if topics.get("keywords"):
        parts.append("kata kunci " + ", ".join(topics["keywords"]))
    return "; ".join(parts)


def _footer(settings: Settings, record: InvestorSubscriptionRecord, token: str) -> str:
    since = record.confirmed_at.strftime("%d-%m-%Y") if record.confirmed_at else "-"
    return (
        "\n—\n"
        f"Anda menerima email ini karena berlangganan kabar inovasi TemuRiset sejak {since} "
        f"dengan minat: {topics_line(record.topics)}.\n"
        f"Ubah minat atau berhenti berlangganan: {_origin(settings)}/langganan/atur?token={token}\n"
    )


def _item(settings: Settings, invention: dict[str, Any], found: Match) -> str:
    stage = STAGE_LABEL.get(invention["stage"], "") if invention["stage"] else ""
    facts = " · ".join(part for part in (invention["sector"], stage) if part)
    return (
        f"{invention['title']}\n"
        f"{_short(invention['summary'])}\n"
        f"{facts}\n"
        f"Inovator: {invention['inventor_name']}\n"
        f"Mengapa Anda menerima ini: cocok dengan minat Anda, {', '.join(found.reasons)}.\n"
        f"Lihat ringkasan: {_origin(settings)}/temuan/{invention['id']}\n"
    )


def _demo(settings: Settings) -> str:
    return "Demo · Data fiktif\n\n" if settings.demo_mode else ""


def confirm(origin: str, token: str, topics: dict[str, Any]) -> tuple[str, str]:
    """The double opt-in email.

    Args:
        origin (str): The web origin.
        token (str): The confirmation token.
        topics (dict[str, Any]): The requested topics.

    Returns:
        tuple[str, str]: Subject and body.
    """
    return (
        "Konfirmasi langganan kabar inovasi TemuRiset",
        "Seseorang meminta kabar inovasi TemuRiset ke email ini dengan minat: "
        f"{topics_line(topics)}.\n\n"
        f"Konfirmasi dalam 7 hari: {_origin(origin)}/langganan/konfirmasi?token={token}\n\n"
        "Jika bukan Anda, abaikan email ini. Tidak ada yang dikirim tanpa konfirmasi.\n",
    )


def already_subscribed(origin: str, token: str) -> tuple[str, str]:
    """Sent instead of a new confirmation when the email is already subscribed.

    Args:
        origin (str): The web origin.
        token (str): A manage token.

    Returns:
        tuple[str, str]: Subject and body.
    """
    return (
        "Anda sudah berlangganan kabar inovasi TemuRiset",
        "Email ini sudah berlangganan. Minat Anda tidak diubah.\n\n"
        f"Ubah minat atau berhenti berlangganan: {_origin(origin)}/langganan/atur?token={token}\n",
    )


def alert(
    settings: Settings, invention: dict[str, Any], found: Match, record: InvestorSubscriptionRecord, token: str
) -> tuple[str, str]:
    """A direct alert for one invention that matches every topic group.

    Args:
        settings (Settings): Settings.
        invention (dict[str, Any]): The public projection.
        found (Match): How it matched.
        record (InvestorSubscriptionRecord): The subscriber.
        token (str): A manage token.

    Returns:
        tuple[str, str]: Subject and body.
    """
    return (
        f"Inovasi sesuai minat Anda: {invention['title']}"[:150],
        _demo(settings)
        + _item(settings, invention, found)
        + "\nUntuk detail dan menghubungi inovator, daftar akun investor di TemuRiset.\n"
        + _footer(settings, record, token),
    )


def digest(
    settings: Settings, items: list[tuple[dict[str, Any], Match]], record: InvestorSubscriptionRecord, token: str
) -> tuple[str, str]:
    """The weekly digest of up to five inventions.

    Args:
        settings (Settings): Settings.
        items (list[tuple[dict[str, Any], Match]]): Inventions and how each matched.
        record (InvestorSubscriptionRecord): The subscriber.
        token (str): A manage token.

    Returns:
        tuple[str, str]: Subject and body.
    """
    body = "\n".join(_item(settings, invention, found) for invention, found in items)
    return (
        f"Kabar inovasi mingguan TemuRiset: {len(items)} inovasi sesuai minat Anda",
        _demo(settings)
        + body
        + "\nUntuk detail dan menghubungi inovator, daftar akun investor di TemuRiset.\n"
        + _footer(settings, record, token),
    )
