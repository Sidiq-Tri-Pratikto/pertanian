"""Multipart (HTML + text) emails a quick subscriber or follower receives, in Indonesian or English (spec 060).

Every email is built once as ``EmailContent`` and rendered twice (``render_text`` and ``render_html``) so both parts
always carry the same facts, links, and footer.
"""

from typing import Any
from urllib.parse import quote

from app.core.settings import Settings
from app.subscriptions.repository.sqlalchemy.models import InvestorSubscriptionRecord
from app.subscriptions.service.email import Card, EmailContent, render_html, render_text, truncate_words
from app.subscriptions.service.matching import Match, stage_label

_SUMMARY_CHARS = 240
_PREHEADER_CHARS = 90
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
        "manage": "Atur langganan",
        "manage_interests": "Atur minat Anda",
        "unsubscribe": "Berhenti berlangganan",
        "switch_language": "Ganti bahasa email: English",
        "tagline": "TemuRiset — pertemuan inovasi dan investor",
        "inventor": "Inovator",
        "field_test": "Uji lapangan",
        "why_heading": "Mengapa Anda menerima ini",
        "why_text": "Mengapa Anda menerima ini: cocok dengan minat Anda, {reasons}.",
        "view": "Lihat ringkasan",
        "follow_cta": "Ikuti inovasi ini",
        "demo": "Demo · Data fiktif",
        "confirm_subject": "Konfirmasi langganan kabar inovasi TemuRiset",
        "confirm_preheader": "Konfirmasi dalam 7 hari untuk menerima kabar inovasi sesuai minat Anda.",
        "confirm_body": "Seseorang meminta kabar inovasi TemuRiset ke email ini dengan minat: {topics}.",
        "confirm_link": "Konfirmasi dalam 7 hari",
        "confirm_ignore": "Jika bukan Anda, abaikan email ini. Tidak ada yang dikirim tanpa konfirmasi.",
        "already_subject": "Anda sudah berlangganan kabar inovasi TemuRiset",
        "already_preheader": "Email ini sudah berlangganan. Atur minat atau berhenti kapan saja.",
        "already_body": "Email ini sudah berlangganan. Minat Anda tidak diubah.",
        "alert_subject": "Inovasi sesuai minat Anda: {title}",
        "alert_lead": "Inovasi baru yang sesuai minat Anda.",
        "digest_subject": "{count} inovasi sesuai minat Anda minggu ini",
        "digest_lead": "{count} inovasi minggu ini yang sesuai minat Anda.",
        "signup": "Untuk detail dan menghubungi inovator, daftar akun investor di TemuRiset.",
    },
    "en": {
        "sector": "sector",
        "stage": "stage",
        "keyword": "keyword",
        "footer": "You receive this email because you subscribed to TemuRiset invention news on {since} for: {topics}.",
        "manage": "Manage subscription",
        "manage_interests": "Manage your interests",
        "unsubscribe": "Unsubscribe",
        "switch_language": "Change email language: Bahasa Indonesia",
        "tagline": "TemuRiset — where inventions meet investors",
        "inventor": "Inventor",
        "field_test": "Field testing",
        "why_heading": "Why you received this",
        "why_text": "Why you received this: it matches your interests, {reasons}.",
        "view": "View summary",
        "follow_cta": "Follow this invention",
        "demo": "Demo · Fictional data",
        "confirm_subject": "Confirm your TemuRiset invention news subscription",
        "confirm_preheader": "Confirm within 7 days to receive invention news matching your interests.",
        "confirm_body": "Someone asked for TemuRiset invention news at this email for: {topics}.",
        "confirm_link": "Confirm within 7 days",
        "confirm_ignore": "If this was not you, ignore this email. Nothing is sent without confirmation.",
        "already_subject": "You already subscribe to TemuRiset invention news",
        "already_preheader": "This email is already subscribed. Manage interests or unsubscribe anytime.",
        "already_body": "This email is already subscribed. Your interests were not changed.",
        "alert_subject": "An invention that matches your interests: {title}",
        "alert_lead": "A new invention that matches your interests.",
        "digest_subject": "{count} inventions match your interests this week",
        "digest_lead": "{count} inventions this week that match your interests.",
        "signup": "For the details and to contact the inventor, sign up for an investor account on TemuRiset.",
    },
}

_FOLLOW_PATHS = {
    "id": {"confirm": "/ikuti/konfirmasi", "manage": "/ikuti/atur", "invention": "/temuan"},
    "en": {"confirm": "/en/follow/confirm", "manage": "/en/follow/manage", "invention": "/en/inventions"},
}

_FOLLOW_TEXT = {
    "id": {
        "confirm_subject": "Konfirmasi langganan Anda: {title}",
        "confirm_preheader": "Konfirmasi dalam 7 hari untuk mengikuti pembaruan {title}.",
        "confirm_body": (
            "Anda meminta pembaruan untuk “{title}”. Buka halaman konfirmasi untuk mulai mengikuti inovasi ini."
        ),
        "confirm_link": "Buka halaman konfirmasi (berlaku 7 hari)",
        "unrequested": "Anda dapat mengabaikan email ini jika Anda tidak meminta pembaruan.",
        "already_subject": "Anda sudah mengikuti {title}",
        "already_preheader": "Email ini sudah mengikuti {title}. Atur bahasa atau berhenti mengikuti.",
        "already_body": "Email ini sudah mengikuti “{title}”. Tidak ada yang diubah.",
        "update_subject": "Pembaruan dari {title}",
        "update_lead": "Pembaruan publik baru dari {title}.",
        "read": "Lihat pembaruan",
        "because": "Anda menerima email ini karena mengikuti {title}.",
        "manage": "Atur langganan",
        "unsubscribe": "Berhenti mengikuti",
    },
    "en": {
        "confirm_subject": "Confirm your subscription: {title}",
        "confirm_preheader": "Confirm within 7 days to follow updates from {title}.",
        "confirm_body": (
            "You asked to receive updates about “{title}”. "
            "Open the confirmation page to start following this invention."
        ),
        "confirm_link": "Open the confirmation page (valid for 7 days)",
        "unrequested": "You can ignore this email if you didn’t request updates.",
        "already_subject": "You already follow {title}",
        "already_preheader": "This email already follows {title}. Manage language or unfollow.",
        "already_body": "This email already follows “{title}”. Nothing was changed.",
        "update_subject": "An update from {title}",
        "update_lead": "A new public update from {title}.",
        "read": "View update",
        "because": "You received this email because you follow {title}.",
        "manage": "Manage subscription",
        "unsubscribe": "Unfollow",
    },
}


def _lang(value: str | None) -> str:
    return "en" if value == "en" else "id"


def _origin(settings_or_origin: Settings | str) -> str:
    origin = settings_or_origin if isinstance(settings_or_origin, str) else settings_or_origin.web_origin
    return origin.rstrip("/")


def _one_click_headers(settings: Settings, unsubscribe_token: str | None) -> dict[str, str]:
    if not unsubscribe_token:
        return {}
    origin = _origin(settings)
    url = f"{origin}/api/v1/unsubscribe/one-click?t={quote(unsubscribe_token, safe='')}"
    value = f"<{url}>"
    if settings.email_relay_sender is not None:
        value += f", <mailto:{settings.email_relay_sender.get_secret_value()}>"
    return {
        "List-Unsubscribe": value,
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def _render_pair(content: EmailContent, headers: dict[str, str] | None = None) -> tuple[str, str, str, dict[str, str]]:
    return content.subject, render_text(content), render_html(content), headers or {}


def topics_line(topics: dict[str, Any], lang: str = "id") -> str:
    """Describe a subscriber's topics in one line."""
    words = _TEXT[_lang(lang)]
    parts = []
    if topics.get("sectors"):
        parts.append(f"{words['sector']} " + ", ".join(topics["sectors"]))
    if topics.get("stages"):
        parts.append(f"{words['stage']} " + ", ".join(stage_label(stage, lang) for stage in topics["stages"]))
    if topics.get("keywords"):
        parts.append(f"{words['keyword']} " + ", ".join(topics["keywords"]))
    return "; ".join(parts)


def _invention_card(origin: str, invention: dict[str, Any], found: Match, lang: str) -> Card:
    words = _TEXT[lang]
    inv_id = quote(str(invention["id"]), safe="")
    url = f"{origin}{_PATHS[lang]['invention']}/{inv_id}"
    stage = stage_label(invention["stage"], lang) if invention.get("stage") else ""
    tkt = f"TKT {invention['tkt_level']}" if invention.get("tkt_level") else ""
    facts = [part for part in (invention.get("sector"), stage, tkt) if part]
    inventor = ANONYMOUS_INVENTOR[lang] if invention.get("anonymous") else invention.get("inventor_name")

    photo_url: str | None = None
    photo_alt: str | None = None
    if invention.get("public_page") and invention.get("photo_version_id") is not None:
        version_prefix = quote(str(invention["photo_version_id"])[:8], safe="")
        photo_url = f"{origin}/api/v1/teasers/inventions/{inv_id}/photo?v={version_prefix}"
        photo_meta = invention.get("photo")
        alt_text = photo_meta[0] if isinstance(photo_meta, (tuple, list)) and photo_meta else None
        photo_alt = alt_text or invention["title"]

    field_test = invention.get("field_test") if invention.get("public_page") else None
    secondary = (words["follow_cta"], f"{url}#ikuti") if invention.get("public_page") else None

    return Card(
        title=invention["title"],
        url=url,
        facts=facts,
        summary=truncate_words(invention.get("summary", ""), _SUMMARY_CHARS),
        reasons=list(found.reasons),
        photo_url=photo_url,
        photo_alt=photo_alt,
        field_test=field_test,
        primary=(words["view"], url),
        secondary=secondary,
        inventor=inventor,
    )


def _common_labels(lang: str) -> dict[str, str]:
    words = _TEXT[lang]
    return {
        "demo_label": words["demo"],
        "reasons_heading": words["why_heading"],
        "reasons_text_template": words["why_text"],
        "inventor_label": words["inventor"],
        "field_test_label": words["field_test"],
        "manage_label": words["manage"],
        "unsubscribe_label": words["unsubscribe"],
        "language_label": words["switch_language"],
        "tagline": words["tagline"],
    }


def confirm(
    origin: str, token: str, topics: dict[str, Any], lang: str = "id", *, demo: bool = False
) -> tuple[str, str, str, dict[str, str]]:
    """The double opt-in email for quick subscriptions."""
    lang = _lang(lang)
    words = _TEXT[lang]
    url = f"{_origin(origin)}{_PATHS[lang]['confirm']}?token={quote(token, safe='')}"
    content = EmailContent(
        lang=lang,
        subject=words["confirm_subject"],
        preheader=truncate_words(words["confirm_preheader"], _PREHEADER_CHARS),
        lead=words["confirm_body"].format(topics=topics_line(topics, lang)),
        action=(words["confirm_link"], url),
        note=words["confirm_ignore"],
        demo=demo,
        **_common_labels(lang),
    )
    return _render_pair(content)


def already_subscribed(
    origin: str, token: str, lang: str = "id", *, demo: bool = False
) -> tuple[str, str, str, dict[str, str]]:
    """Sent instead of a new confirmation when the email is already subscribed."""
    lang = _lang(lang)
    words = _TEXT[lang]
    manage_url = f"{_origin(origin)}{_PATHS[lang]['manage']}?token={quote(token, safe='')}"
    content = EmailContent(
        lang=lang,
        subject=words["already_subject"],
        preheader=truncate_words(words["already_preheader"], _PREHEADER_CHARS),
        lead=words["already_body"],
        action=(words["manage"], manage_url),
        manage_url=manage_url,
        unsubscribe_url=f"{manage_url}#berhenti",
        language_url=f"{manage_url}#bahasa-email",
        demo=demo,
        **_common_labels(lang),
    )
    return _render_pair(content)


def alert(
    settings: Settings,
    invention: dict[str, Any],
    found: Match,
    record: InvestorSubscriptionRecord,
    token: str,
    *,
    unsubscribe_token: str | None = None,
) -> tuple[str, str, str, dict[str, str]]:
    """A direct alert for one invention that matches every topic group."""
    lang = _lang(record.locale)
    words = _TEXT[lang]
    origin = _origin(settings)
    manage_url = f"{origin}{_PATHS[lang]['manage']}?token={quote(token, safe='')}"
    card = _invention_card(origin, invention, found, lang)
    since = record.confirmed_at.strftime("%d-%m-%Y") if record.confirmed_at else "-"
    preheader_parts = " · ".join(card.facts)
    reason_snippet = f" — {found.reasons[0]}" if found.reasons else ""
    preheader = truncate_words(
        f"{preheader_parts}{reason_snippet}" if preheader_parts else card.title, _PREHEADER_CHARS
    )

    content = EmailContent(
        lang=lang,
        subject=words["alert_subject"].format(title=invention["title"])[:150],
        preheader=preheader,
        lead=words["alert_lead"],
        cards=[card],
        note=words["signup"],
        footer_reason=words["footer"].format(since=since, topics=topics_line(record.topics, lang)),
        manage_url=manage_url,
        unsubscribe_url=f"{manage_url}#berhenti",
        language_url=f"{manage_url}#bahasa-email",
        demo=settings.demo_mode,
        **_common_labels(lang),
    )
    return _render_pair(content, _one_click_headers(settings, unsubscribe_token))


def digest(
    settings: Settings,
    items: list[tuple[dict[str, Any], Match]],
    record: InvestorSubscriptionRecord,
    token: str,
    *,
    unsubscribe_token: str | None = None,
) -> tuple[str, str, str, dict[str, str]]:
    """The weekly digest of up to five inventions."""
    lang = _lang(record.locale)
    words = _TEXT[lang]
    origin = _origin(settings)
    manage_url = f"{origin}{_PATHS[lang]['manage']}?token={quote(token, safe='')}"
    cards = [_invention_card(origin, invention, found, lang) for invention, found in items]
    since = record.confirmed_at.strftime("%d-%m-%Y") if record.confirmed_at else "-"
    first_titles = " · ".join(card.title for card in cards[:2])

    content = EmailContent(
        lang=lang,
        subject=words["digest_subject"].format(count=len(items)),
        preheader=truncate_words(first_titles, _PREHEADER_CHARS),
        lead=words["digest_lead"].format(count=len(items)),
        cards=cards,
        digest_cta=(words["manage_interests"], manage_url),
        note=words["signup"],
        footer_reason=words["footer"].format(since=since, topics=topics_line(record.topics, lang)),
        manage_url=manage_url,
        unsubscribe_url=f"{manage_url}#berhenti",
        language_url=f"{manage_url}#bahasa-email",
        demo=settings.demo_mode,
        **_common_labels(lang),
    )
    return _render_pair(content, _one_click_headers(settings, unsubscribe_token))


def follow_confirm(
    origin: str, token: str, title: str, lang: str = "id", *, demo: bool = False
) -> tuple[str, str, str, dict[str, str]]:
    """The double opt-in email for following one invention."""
    lang = _lang(lang)
    words = _FOLLOW_TEXT[lang]
    url = f"{_origin(origin)}{_FOLLOW_PATHS[lang]['confirm']}?token={quote(token, safe='')}"
    content = EmailContent(
        lang=lang,
        subject=words["confirm_subject"].format(title=title)[:150],
        preheader=truncate_words(words["confirm_preheader"].format(title=title), _PREHEADER_CHARS),
        lead=words["confirm_body"].format(title=title),
        action=(words["confirm_link"], url),
        note=words["unrequested"],
        demo=demo,
        **_common_labels(lang),
    )
    return _render_pair(content)


def already_following(
    origin: str, token: str, title: str, lang: str = "id", *, demo: bool = False
) -> tuple[str, str, str, dict[str, str]]:
    """Sent instead of a new confirmation when the email already follows the invention."""
    lang = _lang(lang)
    words = _FOLLOW_TEXT[lang]
    manage_url = f"{_origin(origin)}{_FOLLOW_PATHS[lang]['manage']}?token={quote(token, safe='')}"
    labels = {**_common_labels(lang), "manage_label": words["manage"], "unsubscribe_label": words["unsubscribe"]}
    content = EmailContent(
        lang=lang,
        subject=words["already_subject"].format(title=title)[:150],
        preheader=truncate_words(words["already_preheader"].format(title=title), _PREHEADER_CHARS),
        lead=words["already_body"].format(title=title),
        action=(words["manage"], manage_url),
        manage_url=manage_url,
        unsubscribe_url=f"{manage_url}#berhenti-mengikuti",
        language_url=f"{manage_url}#bahasa-email",
        demo=demo,
        **labels,
    )
    return _render_pair(content)


def follow_update(
    settings: Settings,
    invention_id: str,
    title: str,
    update_title: str,
    update_body: str,
    token: str,
    lang: str,
    *,
    unsubscribe_token: str | None = None,
) -> tuple[str, str, str, dict[str, str]]:
    """One public update, sent once to one follower."""
    lang = _lang(lang)
    words = _FOLLOW_TEXT[lang]
    origin = _origin(settings)
    inv_url = f"{origin}{_FOLLOW_PATHS[lang]['invention']}/{quote(invention_id, safe='')}"
    manage_url = f"{origin}{_FOLLOW_PATHS[lang]['manage']}?token={quote(token, safe='')}"
    labels = {**_common_labels(lang), "manage_label": words["manage"], "unsubscribe_label": words["unsubscribe"]}

    card = Card(
        title=update_title,
        url=inv_url,
        facts=[title],
        summary=truncate_words(update_body, _SUMMARY_CHARS),
        reasons=[],
        photo_url=None,
        photo_alt=None,
        field_test=None,
        primary=(words["read"], inv_url),
    )
    content = EmailContent(
        lang=lang,
        subject=words["update_subject"].format(title=title)[:150],
        preheader=truncate_words(f"{update_title} — {update_body}", _PREHEADER_CHARS),
        lead=words["update_lead"].format(title=title),
        cards=[card],
        footer_reason=words["because"].format(title=title),
        manage_url=manage_url,
        unsubscribe_url=f"{manage_url}#berhenti-mengikuti",
        language_url=f"{manage_url}#bahasa-email",
        demo=settings.demo_mode,
        **labels,
    )
    return _render_pair(content, _one_click_headers(settings, unsubscribe_token))
