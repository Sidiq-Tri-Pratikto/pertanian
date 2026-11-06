"""Asset service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.assets.repository.sqlalchemy.repository import SqlAlchemyAssetRepository
from app.assets.service.service import AssetService
from app.audit.repository.sqlalchemy.repository import SqlAlchemyAuditRepository
from app.audit.service.service import AuditService
from app.core.database import SessionDep
from app.sites.dependencies import SiteServiceDep


def get_asset_service(session: SessionDep, sites: SiteServiceDep) -> AssetService:
    """Build the asset service on the request session.

    Args:
        session (AsyncSession): The request's session.
        sites (SiteService): Site rules.

    Returns:
        AssetService: The service.
    """
    return AssetService(SqlAlchemyAssetRepository(session), sites, AuditService(SqlAlchemyAuditRepository(session)))


AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]
