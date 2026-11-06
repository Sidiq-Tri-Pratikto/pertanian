"""Energy service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.assets.dependencies import AssetServiceDep
from app.core.database import SessionDep
from app.energy.repository.sqlalchemy.repository import SqlAlchemyEnergyRepository
from app.energy.service.history import HistoryService
from app.energy.service.summary import EnergyService
from app.sites.dependencies import SiteServiceDep


def get_energy_service(session: SessionDep, sites: SiteServiceDep, assets: AssetServiceDep) -> EnergyService:
    """Build the energy service on the request session.

    Args:
        session (AsyncSession): The request's session.
        sites (SiteService): Site rules.
        assets (AssetService): Asset model.

    Returns:
        EnergyService: The service.
    """
    return EnergyService(SqlAlchemyEnergyRepository(session), sites, assets)


EnergyServiceDep = Annotated[EnergyService, Depends(get_energy_service)]


def get_history_service(session: SessionDep, energy: EnergyServiceDep, assets: AssetServiceDep) -> HistoryService:
    """Build the history service on the request session.

    Args:
        session (AsyncSession): The request's session.
        energy (EnergyService): Window rules.
        assets (AssetService): Asset model.

    Returns:
        HistoryService: The service.
    """
    return HistoryService(SqlAlchemyEnergyRepository(session), energy, assets)


HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]
