"""Import service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.assets.dependencies import AssetServiceDep
from app.core.database import SessionDep
from app.imports.repository.sqlalchemy.repository import SqlAlchemyImportRepository
from app.imports.service.preview import ImportPreviewService
from app.measurements.dependencies import build_ingest_service
from app.sites.dependencies import SiteServiceDep


def get_import_preview_service(
    session: SessionDep, sites: SiteServiceDep, assets: AssetServiceDep
) -> ImportPreviewService:
    """Build the preview service on the request session.

    Args:
        session (AsyncSession): The request's session.
        sites (SiteService): Site ownership.
        assets (AssetService): The site's assets, sources and bindings.

    Returns:
        ImportPreviewService: The service.
    """
    return ImportPreviewService(SqlAlchemyImportRepository(session), sites, assets, build_ingest_service(session))


ImportPreviewServiceDep = Annotated[ImportPreviewService, Depends(get_import_preview_service)]
