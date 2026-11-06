"""Energy read endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter

from app.energy.dependencies import EnergyServiceDep, HistoryServiceDep
from app.energy.model.schema import HistoryResponse, SummaryResponse
from app.energy.service.history import Granularity
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


@router.get("/assets/{asset_id}/measurements", summary="Bucketed history for one asset")
async def asset_history(
    asset_id: UUID,
    principal: PrincipalDep,
    service: HistoryServiceDep,
    bucket: Granularity = Granularity.DAY,
    preset: Preset | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> HistoryResponse:
    """Return day or hour buckets in local time with UTC bounds, state and coverage; at most 1,000 buckets.

    Args:
        asset_id (UUID): The asset.
        principal (PrincipalModel): The acting principal.
        service (HistoryService): History reads.
        bucket (Granularity, optional): ``day`` or ``hour``. Defaults to day.
        preset (Preset | None, optional): A named period. Defaults to None.
        start_date (date | None, optional): First local date. Defaults to None.
        end_date (date | None, optional): Last local date. Defaults to None.

    Returns:
        HistoryResponse: The series.
    """
    return await service.asset_history(asset_id, principal, PeriodQuery(preset, start_date, end_date), bucket)
