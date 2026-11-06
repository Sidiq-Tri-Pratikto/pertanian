"""Energy service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.assets.dependencies import AssetServiceDep
from app.core.database import SessionDep
from app.energy.repository.sqlalchemy.repository import SqlAlchemyEnergyRepository
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
