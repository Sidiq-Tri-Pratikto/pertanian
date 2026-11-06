"""Ingestion wiring for internal callers."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.measurements.repository.sqlalchemy.repository import SqlAlchemyMeasurementRepository
from app.measurements.service.service import IngestService
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from app.sites.service.service import SiteService


def build_ingest_service(session: AsyncSession) -> IngestService:
    """Build the ingestion service on a session, sharing the caller's transaction.

    Args:
        session (AsyncSession): The caller's session.

    Returns:
        IngestService: The service.
    """
    return IngestService(SqlAlchemyMeasurementRepository(session), SiteService(SqlAlchemySiteRepository(session)))
