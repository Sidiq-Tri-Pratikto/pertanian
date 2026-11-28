"""Render ``EmailContent`` to a readable plain-text email with every fact, link and footer (spec 060)."""

from app.subscriptions.service.email.content import Card, EmailContent


def _render_card(card: Card, content: EmailContent) -> str:
    lines: list[str] = [card.title]
    if card.facts:
        lines.append(" · ".join(card.facts))
    if card.inventor:
        lines.append(f"{content.inventor_label}: {card.inventor}")
    if card.summary:
        lines.append(card.summary)
    if card.field_test:
        lines.append(f"{content.field_test_label}: {card.field_test}")
    if card.reasons:
        lines.append(content.reasons_text_template.format(reasons=", ".join(card.reasons)))
    primary_label, primary_url = card.primary
    lines.append(f"{primary_label}: {primary_url}")
    if card.secondary is not None:
        sec_label, sec_url = card.secondary
        lines.append(f"{sec_label}: {sec_url}")
    return "\n".join(lines)


def render_text(content: EmailContent) -> str:
    """Render an ``EmailContent`` instance to plain text."""
    blocks: list[str] = []
    if content.demo:
        blocks.append(content.demo_label)
    if content.lead:
        blocks.append(content.lead)
    if content.action is not None:
        label, url = content.action
        blocks.append(f"{label}: {url}")
    for card in content.cards:
        blocks.append(_render_card(card, content))
    if content.digest_cta is not None:
        cta_label, cta_url = content.digest_cta
        blocks.append(f"{cta_label}: {cta_url}")
    if content.note:
        blocks.append(content.note)

    footer_lines: list[str] = []
    if content.footer_reason:
        footer_lines.append(content.footer_reason)
    if content.manage_url:
        footer_lines.append(f"{content.manage_label}: {content.manage_url}")
    if content.unsubscribe_url:
        footer_lines.append(f"{content.unsubscribe_label}: {content.unsubscribe_url}")
    if content.language_url:
        footer_lines.append(f"{content.language_label}: {content.language_url}")
    if content.tagline:
        footer_lines.append(content.tagline)

    body = "\n\n".join(blocks)
    if footer_lines:
        body += "\n\n—\n" + "\n".join(footer_lines)
    return body + "\n"
