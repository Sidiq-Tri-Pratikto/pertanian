"""Baseline service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.assets.dependencies import AssetServiceDep
from app.baseline.service.service import BaselineService
from app.core.database import SessionDep
from app.energy.dependencies import EnergyServiceDep
from app.energy.repository.sqlalchemy.repository import SqlAlchemySlotRepository


def get_baseline_service(session: SessionDep, energy: EnergyServiceDep, assets: AssetServiceDep) -> BaselineService:
    """Build the baseline service on the request session.

    Args:
        session (AsyncSession): The request's session.
        energy (EnergyService): Window rules.
        assets (AssetService): Asset model.

    Returns:
        BaselineService: The service.
    """
    return BaselineService(SqlAlchemySlotRepository(session), energy, assets)


BaselineServiceDep = Annotated[BaselineService, Depends(get_baseline_service)]
