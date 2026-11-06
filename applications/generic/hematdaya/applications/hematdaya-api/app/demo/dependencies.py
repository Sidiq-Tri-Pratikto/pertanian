"""Demo service wiring and the demo credential resolver."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.assets.repository.sqlalchemy.repository import SqlAlchemyAssetRepository
from app.assets.service.service import AssetService
from app.audit.repository.sqlalchemy.repository import SqlAlchemyAuditRepository
from app.audit.service.service import AuditService
from app.core.database import SessionDep
from app.core.settings import get_settings
from app.demo.repository.sqlalchemy.repository import SqlAlchemyDemoRepository
from app.demo.service.service import DemoService
from app.demo.service.tokens import TOKEN_PREFIX
from app.identity.model.models import PrincipalModel
from app.identity.repository.sqlalchemy.repository import SqlAlchemyPrincipalRepository
from app.identity.service.service import PrincipalService
from app.measurements.dependencies import build_ingest_service
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from app.sites.service.service import SiteService


def build_demo_service(session: AsyncSession) -> DemoService:
    """Build the demo service on one session, so a whole workspace commits together.

    Args:
        session (AsyncSession): The request's session.

    Returns:
        DemoService: The service.
    """
    audit = AuditService(SqlAlchemyAuditRepository(session))
    sites = SiteService(SqlAlchemySiteRepository(session), audit)
    return DemoService(
        SqlAlchemyDemoRepository(session),
        sites=sites,
        principals=PrincipalService(SqlAlchemyPrincipalRepository(session)),
        assets=AssetService(SqlAlchemyAssetRepository(session), sites, audit),
        ingest=build_ingest_service(session),
        settings=get_settings(),
    )


def get_demo_service(session: SessionDep) -> DemoService:
    """Build the demo service for a request.

    Args:
        session (AsyncSession): The request's session.

    Returns:
        DemoService: The service.
    """
    return build_demo_service(session)


DemoServiceDep = Annotated[DemoService, Depends(get_demo_service)]


async def resolve_demo_principal(token: str, session: AsyncSession) -> PrincipalModel | None:
    """Accept demo tokens for ``get_current_principal``.

    Args:
        token (str): The bearer token.
        session (AsyncSession): The request's session.

    Returns:
        PrincipalModel | None: The principal, or None for a token that is not a live demo token.
    """
    if not token.startswith(TOKEN_PREFIX):
        return None
    return await build_demo_service(session).resolve(token)
