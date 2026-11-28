"""Render ``EmailContent`` to a single-column inline-styled HTML email using stdlib only (spec 060)."""

from html import escape

from app.subscriptions.service.email import tokens
from app.subscriptions.service.email.content import Card, EmailContent


def _esc(value: str) -> str:
    return escape(value, quote=True)


def _button(label: str, url: str) -> str:
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0">'
        "<tr>"
        f'<td style="background:{tokens.BRAND};border-radius:8px">'
        f'<a href="{_esc(url)}" style="display:inline-block;padding:12px 20px;min-height:20px;line-height:20px;'
        f"font-family:{tokens.FONT_STACK};font-size:{tokens.BODY_SIZE};font-weight:600;"
        f'color:{tokens.BRAND_TEXT};text-decoration:none;border-radius:8px">{_esc(label)}</a>'
        "</td>"
        "</tr>"
        "</table>"
    )


def _chips(reasons: list[str]) -> str:
    return " ".join(
        f'<span style="display:inline-block;margin:0 6px 6px 0;padding:4px 10px;'
        f"background:{tokens.CHIP_BG};color:{tokens.CHIP_TEXT};border-radius:999px;"
        f'font-size:13px;line-height:1.3;font-weight:500">{_esc(reason)}</span>'
        for reason in reasons
    )


def _render_card(card: Card, content: EmailContent) -> str:
    parts: list[str] = []
    if card.photo_url:
        alt = card.photo_alt if card.photo_alt is not None else card.title
        parts.append(
            f'<img src="{_esc(card.photo_url)}" alt="{_esc(alt)}" '
            'style="display:block;width:100%;height:auto;border:0;border-radius:8px;margin:0 0 16px 0">'
        )
    parts.append(
        f'<h2 style="margin:0 0 8px 0;font-size:{tokens.TITLE_SIZE};line-height:1.3;font-weight:700;'
        f'color:{tokens.TEXT}">'
        f'<a href="{_esc(card.url)}" style="color:{tokens.TEXT};text-decoration:none">{_esc(card.title)}</a>'
        "</h2>"
    )
    if card.facts:
        parts.append(
            f'<p style="margin:0 0 8px 0;font-size:{tokens.SMALL_SIZE};line-height:1.4;color:{tokens.MUTED}">'
            f"{_esc(' · '.join(card.facts))}</p>"
        )
    if card.inventor:
        parts.append(
            f'<p style="margin:0 0 12px 0;font-size:{tokens.SMALL_SIZE};line-height:1.4;color:{tokens.MUTED}">'
            f"{_esc(content.inventor_label)}: {_esc(card.inventor)}</p>"
        )
    if card.summary:
        parts.append(
            f'<p style="margin:0 0 12px 0;font-size:{tokens.BODY_SIZE};line-height:{tokens.LINE_HEIGHT};'
            f'color:{tokens.TEXT}">{_esc(card.summary)}</p>'
        )
    if card.field_test:
        parts.append(
            f'<p style="margin:0 0 12px 0;font-size:{tokens.SMALL_SIZE};line-height:{tokens.LINE_HEIGHT};'
            f'color:{tokens.MUTED}"><strong style="color:{tokens.TEXT}">{_esc(content.field_test_label)}:</strong> '
            f"{_esc(card.field_test)}</p>"
        )
    if card.reasons:
        parts.append(
            f'<p style="margin:0 0 6px 0;font-size:13px;line-height:1.4;color:{tokens.MUTED};font-weight:600">'
            f"{_esc(content.reasons_heading)}</p>"
            f'<div style="margin:0 0 16px 0">{_chips(card.reasons)}</div>'
        )
    primary_label, primary_url = card.primary
    actions = _button(primary_label, primary_url)
    if card.secondary is not None:
        sec_label, sec_url = card.secondary
        actions += (
            f'<p style="margin:12px 0 0 0;font-size:{tokens.SMALL_SIZE};line-height:1.4">'
            f'<a href="{_esc(sec_url)}" style="color:{tokens.BRAND};font-weight:600;text-decoration:underline">'
            f"{_esc(sec_label)}</a></p>"
        )
    parts.append(actions)

    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="margin:0 0 16px 0;background:{tokens.BG};border:1px solid {tokens.BORDER};border-radius:12px">'
        f'<tr><td style="padding:24px">{"".join(parts)}</td></tr>'
        "</table>"
    )


def render_html(content: EmailContent) -> str:
    """Render an ``EmailContent`` instance to responsive single-column inline-styled HTML."""
    lang = "en" if content.lang == "en" else "id"
    sections: list[str] = []

    demo_badge = (
        f' <span style="display:inline-block;margin-left:8px;padding:2px 8px;background:{tokens.DEMO_BG};'
        f'color:{tokens.DEMO_TEXT};border-radius:999px;font-size:12px;font-weight:600;vertical-align:middle">'
        f"{_esc(content.demo_label)}</span>"
        if content.demo
        else ""
    )
    sections.append(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 16px 0">'
        '<tr><td style="padding:0">'
        f'<span style="font-size:20px;font-weight:700;letter-spacing:-0.01em;color:{tokens.BRAND}">TemuRiset</span>'
        f"{demo_badge}"
        "</td></tr></table>"
    )

    if content.lead:
        sections.append(
            f'<p style="margin:0 0 20px 0;font-size:{tokens.BODY_SIZE};line-height:{tokens.LINE_HEIGHT};'
            f'color:{tokens.TEXT}">{_esc(content.lead)}</p>'
        )

    if content.action is not None:
        action_label, action_url = content.action
        sections.append(f'<div style="margin:0 0 20px 0">{_button(action_label, action_url)}</div>')

    for card in content.cards:
        sections.append(_render_card(card, content))

    if content.digest_cta is not None:
        cta_label, cta_url = content.digest_cta
        sections.append(
            f'<p style="margin:0 0 16px 0;font-size:{tokens.BODY_SIZE};line-height:{tokens.LINE_HEIGHT}">'
            f'<a href="{_esc(cta_url)}" style="color:{tokens.BRAND};font-weight:600;text-decoration:underline">'
            f"{_esc(cta_label)}</a></p>"
        )

    if content.note:
        sections.append(
            f'<p style="margin:0 0 20px 0;font-size:{tokens.SMALL_SIZE};line-height:{tokens.LINE_HEIGHT};'
            f'color:{tokens.MUTED}">{_esc(content.note)}</p>'
        )

    footer_links: list[str] = []
    if content.manage_url:
        footer_links.append(
            f'<a href="{_esc(content.manage_url)}" style="color:{tokens.BRAND};text-decoration:underline">'
            f"{_esc(content.manage_label)}</a>"
        )
    if content.unsubscribe_url:
        footer_links.append(
            f'<a href="{_esc(content.unsubscribe_url)}" style="color:{tokens.BRAND};text-decoration:underline">'
            f"{_esc(content.unsubscribe_label)}</a>"
        )
    if content.language_url:
        footer_links.append(
            f'<a href="{_esc(content.language_url)}" style="color:{tokens.BRAND};text-decoration:underline">'
            f"{_esc(content.language_label)}</a>"
        )

    footer_parts: list[str] = []
    if content.footer_reason:
        footer_parts.append(
            f'<p style="margin:0 0 8px 0;font-size:13px;line-height:1.5;color:{tokens.MUTED}">'
            f"{_esc(content.footer_reason)}</p>"
        )
    if footer_links:
        footer_parts.append(
            f'<p style="margin:0 0 8px 0;font-size:13px;line-height:1.5;color:{tokens.MUTED}">'
            f"{' · '.join(footer_links)}</p>"
        )
    if content.tagline:
        footer_parts.append(
            f'<p style="margin:0;font-size:13px;line-height:1.5;color:{tokens.MUTED}">{_esc(content.tagline)}</p>'
        )

    if footer_parts:
        sections.append(
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="margin-top:8px;border-top:1px solid {tokens.BORDER}">'
            f'<tr><td style="padding:16px 0 0 0">{"".join(footer_parts)}</td></tr>'
            "</table>"
        )

    preheader = (
        f'<div style="display:none;max-height:0;overflow:hidden;opacity:0">{_esc(content.preheader)}</div>'
        if content.preheader
        else ""
    )

    return (
        "<!DOCTYPE html>"
        f'<html lang="{lang}">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark">'
        f"<title>{_esc(content.subject)}</title>"
        "</head>"
        f'<body style="margin:0;padding:0;background:{tokens.SURFACE};color:{tokens.TEXT};'
        f'font-family:{tokens.FONT_STACK};font-size:{tokens.BODY_SIZE};line-height:{tokens.LINE_HEIGHT}">'
        f"{preheader}"
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="background:{tokens.SURFACE}">'
        '<tr><td align="center" style="padding:24px 12px">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'style="max-width:{tokens.MAX_WIDTH};width:100%;margin:0 auto">'
        f'<tr><td style="padding:0;text-align:left">{"".join(sections)}</td></tr>'
        "</table>"
        "</td></tr>"
        "</table>"
        "</body>"
        "</html>"
    )
