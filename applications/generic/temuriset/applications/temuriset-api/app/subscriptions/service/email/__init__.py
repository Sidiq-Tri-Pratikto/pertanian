"""Multipart investor email content model and text/HTML renderers (spec 060)."""

from app.subscriptions.service.email.content import Card, EmailContent, truncate_words
from app.subscriptions.service.email.render_html import render_html
from app.subscriptions.service.email.render_text import render_text

__all__ = ["Card", "EmailContent", "render_html", "render_text", "truncate_words"]
