"""Snooze time on both clocks."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.feedback.service import service as feedback_service
from app.sites.model.models import SiteContext, SiteKind, SiteModel


def _site(kind: SiteKind, virtual_now: datetime | None, timezone: str = "Asia/Jakarta") -> SiteModel:
    return SiteModel(
        id=uuid4(),
        owner_principal_id=uuid4(),
        kind=kind,
        name="Rumah",
        context=SiteContext.UNSPECIFIED,
        timezone=timezone,
        currency="IDR",
        virtual_now=virtual_now,
    )


def test_demo_snooze_ends_at_the_next_virtual_local_midnight() -> None:
    """
    Condition:
    - A demo site at 26 Oktober 00.00 WIB.

    Expected:
    - 27 Oktober 00.00 WIB, from the virtual clock.
    """
    site = _site(SiteKind.DEMO, datetime(2026, 10, 25, 17, tzinfo=UTC))

    assert feedback_service.next_local_midnight(site) == datetime(2026, 10, 26, 17, tzinfo=UTC)


def test_standard_snooze_uses_the_wall_clock_across_dst(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Condition:
    - A standard Berlin site on 24 Oktober 2026 at 23.30 local, the night before clocks go back.

    Expected:
    - 25 Oktober 00.00 CEST, from the wall clock.
    """
    monkeypatch.setattr("app.sites.service.clock.wall_now", lambda: datetime(2026, 10, 24, 21, 30, tzinfo=UTC))
    site = _site(SiteKind.STANDARD, None, "Europe/Berlin")

    assert feedback_service.next_local_midnight(site) == datetime(2026, 10, 24, 22, tzinfo=UTC)
