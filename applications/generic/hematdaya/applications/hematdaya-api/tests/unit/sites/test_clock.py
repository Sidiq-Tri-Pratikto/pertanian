"""One clock per site."""

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.sites.model.models import SiteContext, SiteKind, SiteModel
from app.sites.service.clock import site_clock

VIRTUAL_MONDAY = datetime(2026, 10, 25, 17, tzinfo=UTC)


def _site(kind: SiteKind, virtual_now: datetime | None) -> SiteModel:
    return SiteModel(
        id=uuid4(),
        owner_principal_id=uuid4(),
        kind=kind,
        name="Rumah",
        context=SiteContext.UNSPECIFIED,
        timezone="Asia/Jakarta",
        currency="IDR",
        virtual_now=virtual_now,
    )


def test_demo_site_runs_on_its_virtual_clock() -> None:
    """
    Condition:
    - A demo site at 2026-10-26 00.00 WIB.

    Expected:
    - Product time is that instant.
    """
    assert site_clock(_site(SiteKind.DEMO, VIRTUAL_MONDAY)) == VIRTUAL_MONDAY


def test_standard_site_runs_on_the_wall_clock() -> None:
    """
    Condition:
    - A standard site.

    Expected:
    - Product time is the wall clock.
    """
    wall = datetime(2027, 1, 1, tzinfo=UTC)

    with patch("app.sites.service.clock.wall_now", return_value=wall):
        assert site_clock(_site(SiteKind.STANDARD, None)) == wall


def test_demo_site_never_falls_back_to_the_wall_clock() -> None:
    """
    Condition:
    - A demo site somehow without a virtual time.

    Expected:
    - It fails instead of using the wall clock.
    """
    with pytest.raises(ValueError, match="virtual time"):
        site_clock(_site(SiteKind.DEMO, None))
