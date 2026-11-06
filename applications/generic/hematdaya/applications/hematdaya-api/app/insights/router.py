"""Insight endpoints."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.energy.service.periods import Preset
from app.energy.service.summary import PeriodQuery
from app.identity.dependencies import PrincipalDep
from app.insights.dependencies import InsightServiceDep
from app.insights.model.schema import InsightListResponse, InsightResponse

router = APIRouter(tags=["insights"])


@router.get("/sites/{site_id}/insights", summary="Observations and notices for a period")
async def site_insights(
    site_id: UUID,
    principal: PrincipalDep,
    service: InsightServiceDep,
    preset: Preset | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> InsightListResponse:
    """Evaluate the period and return active observations ranked by additional kWh, plus data-quality notices.

    Args:
        site_id (UUID): The site.
        principal (PrincipalModel): The acting principal.
        service (InsightService): Insight rules.
        preset (Preset | None, optional): A named period. Defaults to None.
        start_date (date | None, optional): First local date. Defaults to None.
        end_date (date | None, optional): Last local date. Defaults to None.

    Returns:
        InsightListResponse: Observations, notices and counts.
    """
    return await service.site_insights(site_id, principal, PeriodQuery(preset, start_date, end_date))


@router.get("/insights/{insight_id}", summary="Read an insight")
async def get_insight(
    insight_id: UUID,
    principal: PrincipalDep,
    service: InsightServiceDep,
    revision: Annotated[int | None, Query(ge=1)] = None,
) -> InsightResponse:
    """Return the current revision after re-evaluation, or a frozen revision with its supersession status.

    Args:
        insight_id (UUID): The insight.
        principal (PrincipalModel): The acting principal.
        service (InsightService): Insight rules.
        revision (int | None, optional): A specific revision. Defaults to None.

    Returns:
        InsightResponse: The revision.
    """
    return await service.get(insight_id, principal, revision)
