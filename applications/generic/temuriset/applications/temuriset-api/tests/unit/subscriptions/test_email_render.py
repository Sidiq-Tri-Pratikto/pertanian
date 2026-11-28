"""Unit tests for multipart investor email rendering (spec 060)."""

import re
from datetime import UTC, datetime

import pytest
from pydantic import SecretStr

from app.core.settings import Settings
from app.subscriptions.repository.sqlalchemy.models import InvestorSubscriptionRecord
from app.subscriptions.service import mail
from app.subscriptions.service.matching import Match

_TEMPLATES = ("confirm", "already", "alert", "digest", "follow_confirm", "follow_already", "follow_update")


def _settings(*, demo: bool = False, sender: str | None = "no-reply@temuriset.test") -> Settings:
    return Settings(
        web_origin="https://temuriset.test",
        demo_mode=demo,
        email_relay_sender=SecretStr(sender) if sender else None,
    )


def _record(lang: str) -> InvestorSubscriptionRecord:
    return InvestorSubscriptionRecord(
        email="investor@example.test",
        topics={"sectors": ["Air dan sanitasi"], "stages": ["PROTOTYPE"], "keywords": ["air"]},
        status="ACTIVE",
        locale=lang,
        confirmed_at=datetime(2026, 4, 1, 2, 0, tzinfo=UTC),
    )


def _sample_invention(*, title: str = "Filter Air Surya", photo: bool = True) -> dict:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "title": title,
        "summary": "Penyaring air tenaga surya untuk desa tanpa listrik stabil, hemat perawatan.",
        "sector": "Air dan sanitasi",
        "stage": "PROTOTYPE",
        "tkt_level": 4,
        "inventor_name": "Rina Kusuma",
        "anonymous": False,
        "public_page": True,
        "field_test": "Uji coba 30 hari di dua desa Jawa Barat.",
        "photo_version_id": "22222222-2222-2222-2222-222222222222" if photo else None,
        "photo": ("Unit filter di lapangan", 800, 600) if photo else (None, None, None),
    }


def _render(template: str, lang: str, *, settings: Settings | None = None, invention: dict | None = None):
    cfg = settings or _settings()
    record = _record(lang)
    inv = invention or _sample_invention()
    found = Match(level="ALERT", reasons=["Air dan sanitasi", "Prototipe", "air"])
    if template == "confirm":
        return mail.confirm(cfg.web_origin, "tok-confirm-1234567890123456", record.topics, lang, demo=cfg.demo_mode)
    if template == "already":
        return mail.already_subscribed(cfg.web_origin, "tok-manage-1234567890123456", lang, demo=cfg.demo_mode)
    if template == "alert":
        return mail.alert(cfg, inv, found, record, "tok-manage-1234567890123456", unsubscribe_token="tok-unsub-123456")
    if template == "digest":
        second = {
            **_sample_invention(title="Sensor Tanah Hemat Daya", photo=False),
            "id": "33333333-3333-3333-3333-333333333333",
        }
        return mail.digest(
            cfg,
            [(inv, found), (second, Match(level="DIGEST", reasons=["Air dan sanitasi"]))],
            record,
            "tok-manage-1234567890123456",
            unsubscribe_token="tok-unsub-123456",
        )
    if template == "follow_confirm":
        return mail.follow_confirm(
            cfg.web_origin, "tok-confirm-1234567890123456", inv["title"], lang, demo=cfg.demo_mode
        )
    if template == "follow_already":
        return mail.already_following(
            cfg.web_origin, "tok-manage-1234567890123456", inv["title"], lang, demo=cfg.demo_mode
        )
    return mail.follow_update(
        cfg,
        inv["id"],
        inv["title"],
        "Uji lapangan tahap 2 selesai",
        "Debit air stabil selama 30 hari.",
        "tok-manage-1234567890123456",
        lang,
        unsubscribe_token="tok-unsub-123456",
    )


@pytest.mark.parametrize("template", _TEMPLATES)
@pytest.mark.parametrize("lang", ("id", "en"))
def test_every_template_renders_valid_html_and_text_under_100kb(template: str, lang: str) -> None:
    subject, text, html, headers = _render(template, lang)
    assert subject
    assert text.strip()
    assert html.startswith("<!DOCTYPE html>")
    assert f'<html lang="{lang}">' in html
    assert '<meta name="color-scheme" content="light dark">' in html
    assert 'role="presentation"' in html
    assert "<style" not in html.lower()
    assert "<script" not in html.lower()
    assert 'href=""' not in html
    assert len(html.encode("utf-8")) < 100 * 1024

    # Every https link in the text part also appears in the HTML part.
    for url in re.findall(r"https://[^\s]+", text):
        assert url in html

    if template in {"alert", "digest", "follow_update"}:
        assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
        assert "https://temuriset.test/api/v1/unsubscribe/one-click?t=tok-unsub-123456" in headers["List-Unsubscribe"]
        assert "mailto:no-reply@temuriset.test" in headers["List-Unsubscribe"]
    else:
        assert headers == {}


def test_alert_escapes_html_and_respects_optional_photo_and_demo_badge() -> None:
    dangerous = _sample_invention(title='<script>alert("xss")</script> Filter', photo=False)
    subject, text, html, _ = _render("alert", "id", settings=_settings(demo=True), invention=dangerous)
    assert "<script>" not in html
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in html
    assert "<img" not in html
    assert "TKT 4" in html and "TKT 4" in text
    assert "Demo · Data fiktif" in html and "Demo · Data fiktif" in text

    _, _, html_with_photo, _ = _render("alert", "en", invention=_sample_invention(photo=True))
    assert '<img src="https://temuriset.test/api/v1/teasers/inventions/' in html_with_photo
    assert 'alt="Unit filter di lapangan"' in html_with_photo
    assert "View summary" in html_with_photo


def test_digest_subject_and_preheader_match_spec() -> None:
    subject_id, _, html_id, _ = _render("digest", "id")
    assert subject_id == "2 inovasi sesuai minat Anda minggu ini"
    assert "Filter Air Surya · Sensor Tanah Hemat Daya" in html_id

    subject_en, _, html_en, _ = _render("digest", "en")
    assert subject_en == "2 inventions match your interests this week"
    assert "Filter Air Surya · Sensor Tanah Hemat Daya" in html_en
