"""Energy read endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter

from app.energy.dependencies import EnergyServiceDep
from app.energy.model.schema import SummaryResponse
from app.energy.service.periods import Preset
from app.energy.service.summary import PeriodQuery
from app.identity.dependencies import PrincipalDep

router = APIRouter(tags=["energy"])


@router.get("/sites/{site_id}/summary", summary="Recorded energy for a site")
async def site_summary(
    site_id: UUID,
    principal: PrincipalDep,
    service: EnergyServiceDep,
    preset: Preset | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> SummaryResponse:
    """Return recorded energy for every active asset, with coverage and any reason the total is withheld.

    Pass ``preset`` or both ``start_date`` and ``end_date`` (inclusive local dates, at most 366 days).

    Args:
        site_id (UUID): The site.
        principal (PrincipalModel): The acting principal.
        service (EnergyService): Energy reads.
        preset (Preset | None, optional): A named period. Defaults to None.
        start_date (date | None, optional): First local date. Defaults to None.
        end_date (date | None, optional): Last local date. Defaults to None.

    Returns:
        SummaryResponse: The summary.
    """
    return await service.site_summary(site_id, principal, PeriodQuery(preset, start_date, end_date))


@router.get("/assets/{asset_id}/summary", summary="Recorded energy for one asset")
async def asset_summary(
    asset_id: UUID,
    principal: PrincipalDep,
    service: EnergyServiceDep,
    preset: Preset | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> SummaryResponse:
    """Return one asset's recorded energy in the summary shape; a parent meter alone is valid.

    Args:
        asset_id (UUID): The asset.
        principal (PrincipalModel): The acting principal.
        service (EnergyService): Energy reads.
        preset (Preset | None, optional): A named period. Defaults to None.
        start_date (date | None, optional): First local date. Defaults to None.
        end_date (date | None, optional): Last local date. Defaults to None.

    Returns:
        SummaryResponse: The summary.
    """
    return await service.asset_summary(asset_id, principal, PeriodQuery(preset, start_date, end_date))
