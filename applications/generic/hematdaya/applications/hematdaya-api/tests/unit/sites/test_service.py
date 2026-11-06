"""Site rules with an in-memory repository."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.core.errors.base import NotFoundError
from app.identity.model.models import PrincipalKind, PrincipalModel
from app.sites.model.models import SiteContext, SiteKind, SiteModel
from app.sites.model.schema import UpdateSiteRequest
from app.sites.repository.base_repository import SiteRepository
from app.sites.service.service import SiteService


class FakeSiteRepository(SiteRepository):
    """Sites in a dict."""

    def __init__(self) -> None:
        self.sites: dict[UUID, SiteModel] = {}
        self.updates = 0

    async def get_owned(self, site_id: UUID, owner_id: UUID, *, lock: bool = False) -> SiteModel | None:
        site = self.sites.get(site_id)
        return site if site is not None and site.owner_principal_id == owner_id else None

    async def lock(self, site_id: UUID) -> SiteModel | None:
        return self.sites.get(site_id)

    async def add(self, **fields: Any) -> SiteModel:
        site = SiteModel(id=uuid4(), owner_principal_id=fields.pop("owner_id"), **fields)
        self.sites[site.id] = site
        return site

    async def advance_revision(self, site_id: UUID, column: str) -> None:
        self.sites[site_id] = self.sites[site_id].model_copy(update={column: getattr(self.sites[site_id], column) + 1})

    async def update(self, site_id: UUID, values: dict[str, Any]) -> SiteModel:
        self.updates += 1
        self.sites[site_id] = self.sites[site_id].model_copy(update=values)
        return self.sites[site_id]


def _principal() -> PrincipalModel:
    return PrincipalModel(id=uuid4(), kind=PrincipalKind.DEMO)


async def test_new_site_defaults_are_neutral() -> None:
    """
    Condition:
    - A site is created with no context, timezone or currency.

    Expected:
    - Context unspecified, Asia/Jakarta, IDR.
    """
    site = await SiteService(FakeSiteRepository()).create(_principal(), kind=SiteKind.STANDARD, name="Rumah")

    assert (site.context, site.timezone, site.currency) == (SiteContext.UNSPECIFIED, "Asia/Jakarta", "IDR")


async def test_foreign_site_is_not_found_and_unchanged() -> None:
    """
    Condition:
    - B reads and updates A's site.

    Expected:
    - Both fail with NotFoundError and nothing is written.
    """
    repository = FakeSiteRepository()
    service = SiteService(repository)
    site = await service.create(
        _principal(), kind=SiteKind.DEMO, name="Rumah", virtual_now=datetime(2026, 10, 25, 17, tzinfo=UTC)
    )
    intruder = _principal()

    with pytest.raises(NotFoundError):
        await service.get_owned(site.id, intruder)
    with pytest.raises(NotFoundError):
        await service.update(site.id, intruder, UpdateSiteRequest(name="Diambil"))
    assert repository.updates == 0


async def test_unchanged_values_write_nothing() -> None:
    """
    Condition:
    - The owner saves the values the site already has.

    Expected:
    - No update is issued.
    """
    repository = FakeSiteRepository()
    service = SiteService(repository)
    owner = _principal()
    site = await service.create(owner, kind=SiteKind.STANDARD, name="Rumah")

    await service.update(site.id, owner, UpdateSiteRequest(name="Rumah", timezone="Asia/Jakarta"))

    assert repository.updates == 0


@pytest.mark.parametrize("timezone", ["UTC+7", "+07:00", "../../etc/passwd", "Asia/Bandung", ""])
def test_timezone_must_be_iana(timezone: str) -> None:
    """
    Condition:
    - A fixed offset, a path, an unknown zone or an empty value.

    Expected:
    - Validation fails with the timezone error type.
    """
    with pytest.raises(ValidationError) as error:
        UpdateSiteRequest(timezone=timezone)

    assert error.value.errors()[0]["type"] == "timezone_invalid"
