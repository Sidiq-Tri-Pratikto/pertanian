"""Insight service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.assets.dependencies import AssetServiceDep
from app.baseline.dependencies import BaselineServiceDep
from app.core.database import SessionDep
from app.energy.dependencies import EnergyServiceDep
from app.insights.repository.sqlalchemy.repository import SqlAlchemyInsightRepository
from app.insights.service.service import InsightService
from app.sites.dependencies import SiteServiceDep


def get_insight_service(
    session: SessionDep,
    sites: SiteServiceDep,
    assets: AssetServiceDep,
    energy: EnergyServiceDep,
    baseline: BaselineServiceDep,
) -> InsightService:
    """Build the insight service on the request session.

    Args:
        session (AsyncSession): The request's session.
        sites (SiteService): Ownership and lock.
        assets (AssetService): Asset model.
        energy (EnergyService): Windows and summaries.
        baseline (BaselineService): Matched baseline.

    Returns:
        InsightService: The service.
    """
    return InsightService(
        SqlAlchemyInsightRepository(session), sites=sites, assets=assets, energy=energy, baseline=baseline
    )


InsightServiceDep = Annotated[InsightService, Depends(get_insight_service)]
