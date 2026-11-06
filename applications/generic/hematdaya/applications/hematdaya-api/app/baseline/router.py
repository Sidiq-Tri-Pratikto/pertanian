"""Comparison endpoint."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter

from app.baseline.dependencies import BaselineServiceDep
from app.baseline.model.schema import ComparisonResponse
from app.energy.service.periods import Preset
from app.energy.service.summary import PeriodQuery
from app.identity.dependencies import PrincipalDep

router = APIRouter(tags=["baseline"])


@router.get("/assets/{asset_id}/comparison", summary="Compare a period with its matched baseline")
async def asset_comparison(
    asset_id: UUID,
    principal: PrincipalDep,
    service: BaselineServiceDep,
    preset: Preset | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> ComparisonResponse:
    """Compare up to seven days with the same local weekdays and times in the previous three weeks.

    Args:
        asset_id (UUID): The asset.
        principal (PrincipalModel): The acting principal.
        service (BaselineService): Comparison.
        preset (Preset | None, optional): A named period. Defaults to None.
        start_date (date | None, optional): First local date. Defaults to None.
        end_date (date | None, optional): Last local date. Defaults to None.

    Returns:
        ComparisonResponse: State, reason and, when valid, every number on the common mask.
    """
    return await service.asset_comparison(asset_id, principal, PeriodQuery(preset, start_date, end_date))
