"""The plain-text emails a quick subscriber receives, in the subscriber's language (Indonesian or English).

Brief on purpose: the details need a normal signup. English links open the ``/en`` pages, which serve the same flow.
"""

from typing import Any

from app.core.settings import Settings
from app.subscriptions.repository.sqlalchemy.models import InvestorSubscriptionRecord
from app.subscriptions.service.matching import Match, stage_label

_SUMMARY_CHARS = 240
# Shown instead of the inventor's name until they publish their public profile.
ANONYMOUS_INVENTOR = {"id": "Inovator di TemuRiset", "en": "An inventor on TemuRiset"}

# Web paths per language; the web proxy serves ``/en/...`` from the same pages as the Indonesian paths.
_PATHS = {
    "id": {"confirm": "/langganan/konfirmasi", "manage": "/langganan/atur", "invention": "/temuan"},
    "en": {"confirm": "/en/subscribe/confirm", "manage": "/en/subscribe/manage", "invention": "/en/inventions"},
}

_TEXT = {
    "id": {
        "sector": "sektor",
        "stage": "tahap",
        "keyword": "kata kunci",
        "footer": (
            "Anda menerima email ini karena berlangganan kabar inovasi TemuRiset sejak {since} dengan minat: {topics}."
        ),
        "manage": "Ubah minat atau berhenti berlangganan",
        "inventor": "Inovator",
        "why": "Mengapa Anda menerima ini: cocok dengan minat Anda, {reasons}.",
        "view": "Lihat ringkasan",
        "demo": "Demo · Data fiktif",
        "confirm_subject": "Konfirmasi langganan kabar inovasi TemuRiset",
        "confirm_body": "Seseorang meminta kabar inovasi TemuRiset ke email ini dengan minat: {topics}.",
        "confirm_link": "Konfirmasi dalam 7 hari",
        "confirm_ignore": "Jika bukan Anda, abaikan email ini. Tidak ada yang dikirim tanpa konfirmasi.",
        "already_subject": "Anda sudah berlangganan kabar inovasi TemuRiset",
        "already_body": "Email ini sudah berlangganan. Minat Anda tidak diubah.",
        "alert_subject": "Inovasi sesuai minat Anda: {title}",
        "digest_subject": "Kabar inovasi mingguan TemuRiset: {count} inovasi sesuai minat Anda",
        "signup": "Untuk detail dan menghubungi inovator, daftar akun investor di TemuRiset.",
    },
    "en": {
        "sector": "sector",
        "stage": "stage",
        "keyword": "keyword",
        "footer": "You receive this email because you subscribed to TemuRiset invention news on {since} for: {topics}.",
        "manage": "Change your interests or unsubscribe",
        "inventor": "Inventor",
        "why": "Why you received this: it matches your interests, {reasons}.",
        "view": "View the summary",
        "demo": "Demo · Fictional data",
        "confirm_subject": "Confirm your TemuRiset invention news subscription",
        "confirm_body": "Someone asked for TemuRiset invention news at this email for: {topics}.",
        "confirm_link": "Confirm within 7 days",
        "confirm_ignore": "If this was not you, ignore this email. Nothing is sent without confirmation.",
        "already_subject": "You already subscribe to TemuRiset invention news",
        "already_body": "This email is already subscribed. Your interests were not changed.",
        "alert_subject": "An invention that matches your interests: {title}",
        "digest_subject": "TemuRiset weekly invention news: {count} inventions match your interests",
        "signup": "For the details and to contact the inventor, sign up for an investor account on TemuRiset.",
    },
}


def _lang(value: str | None) -> str:
    return "en" if value == "en" else "id"


def _origin(settings_or_origin: Settings | str) -> str:
    origin = settings_or_origin if isinstance(settings_or_origin, str) else settings_or_origin.web_origin
    return origin.rstrip("/")


def _short(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _SUMMARY_CHARS else text[: _SUMMARY_CHARS - 1].rstrip() + "…"


def topics_line(topics: dict[str, Any], lang: str = "id") -> str:
    """Describe a subscriber's topics in one line.

    Args:
        topics (dict[str, Any]): ``sectors``, ``stages`` and ``keywords``.
        lang (str, optional): ``id`` or ``en``. Defaults to ``id``.

    Returns:
        str: For example ``sektor Air dan sanitasi; tahap Prototipe``.
    """
    words = _TEXT[_lang(lang)]
    parts = []
    if topics.get("sectors"):
        parts.append(f"{words['sector']} " + ", ".join(topics["sectors"]))
    if topics.get("stages"):
        parts.append(f"{words['stage']} " + ", ".join(stage_label(stage, lang) for stage in topics["stages"]))
    if topics.get("keywords"):
        parts.append(f"{words['keyword']} " + ", ".join(topics["keywords"]))
    return "; ".join(parts)


def _footer(settings: Settings, record: InvestorSubscriptionRecord, token: str) -> str:
    lang = _lang(record.locale)
    words = _TEXT[lang]
    since = record.confirmed_at.strftime("%d-%m-%Y") if record.confirmed_at else "-"
    return (
        "\n—\n"
        + words["footer"].format(since=since, topics=topics_line(record.topics, lang))
        + f"\n{words['manage']}: {_origin(settings)}{_PATHS[lang]['manage']}?token={token}\n"
    )


def _item(settings: Settings, invention: dict[str, Any], found: Match, lang: str) -> str:
    words = _TEXT[lang]
    stage = stage_label(invention["stage"], lang) if invention["stage"] else ""
    facts = " · ".join(part for part in (invention["sector"], stage) if part)
    inventor = ANONYMOUS_INVENTOR[lang] if invention.get("anonymous") else invention["inventor_name"]
    return (
        f"{invention['title']}\n"
        f"{_short(invention['summary'])}\n"
        f"{facts}\n"
        f"{words['inventor']}: {inventor}\n"
        + words["why"].format(reasons=", ".join(found.reasons))
        + f"\n{words['view']}: {_origin(settings)}{_PATHS[lang]['invention']}/{invention['id']}\n"
    )


def _demo(settings: Settings, lang: str) -> str:
    return f"{_TEXT[lang]['demo']}\n\n" if settings.demo_mode else ""


def confirm(origin: str, token: str, topics: dict[str, Any], lang: str = "id") -> tuple[str, str]:
    """The double opt-in email.

    Args:
        origin (str): The web origin.
        token (str): The confirmation token.
        topics (dict[str, Any]): The requested topics.
        lang (str, optional): ``id`` or ``en``. Defaults to ``id``.

    Returns:
        tuple[str, str]: Subject and body.
    """
    lang = _lang(lang)
    words = _TEXT[lang]
    return (
        words["confirm_subject"],
        words["confirm_body"].format(topics=topics_line(topics, lang))
        + f"\n\n{words['confirm_link']}: {_origin(origin)}{_PATHS[lang]['confirm']}?token={token}\n\n"
        + f"{words['confirm_ignore']}\n",
    )


def already_subscribed(origin: str, token: str, lang: str = "id") -> tuple[str, str]:
    """Sent instead of a new confirmation when the email is already subscribed.

    Args:
        origin (str): The web origin.
        token (str): A manage token.
        lang (str, optional): ``id`` or ``en``. Defaults to ``id``.

    Returns:
        tuple[str, str]: Subject and body.
    """
    lang = _lang(lang)
    words = _TEXT[lang]
    return (
        words["already_subject"],
        f"{words['already_body']}\n\n{words['manage']}: {_origin(origin)}{_PATHS[lang]['manage']}?token={token}\n",
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
    lang = _lang(record.locale)
    words = _TEXT[lang]
    return (
        words["alert_subject"].format(title=invention["title"])[:150],
        _demo(settings, lang)
        + _item(settings, invention, found, lang)
        + f"\n{words['signup']}\n"
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
    lang = _lang(record.locale)
    words = _TEXT[lang]
    body = "\n".join(_item(settings, invention, found, lang) for invention, found in items)
    return (
        words["digest_subject"].format(count=len(items)),
        _demo(settings, lang) + body + f"\n{words['signup']}\n" + _footer(settings, record, token),
    )
