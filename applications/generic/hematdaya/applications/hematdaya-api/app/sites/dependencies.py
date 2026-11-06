"""Site service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.audit.repository.sqlalchemy.repository import SqlAlchemyAuditRepository
from app.audit.service.service import AuditService
from app.core.database import SessionDep
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from app.sites.service.service import SiteService


def get_site_service(session: SessionDep) -> SiteService:
    """Build the site service on the request session.

    Args:
        session (AsyncSession): The request's session.

    Returns:
        SiteService: The service.
    """
    return SiteService(SqlAlchemySiteRepository(session), AuditService(SqlAlchemyAuditRepository(session)))


SiteServiceDep = Annotated[SiteService, Depends(get_site_service)]
