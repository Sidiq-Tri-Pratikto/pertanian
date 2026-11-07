"""Audit wiring for internal callers."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository.sqlalchemy.repository import SqlAlchemyAuditRepository
from app.audit.service.service import AuditService


def build_audit_service(session: AsyncSession) -> AuditService:
    """Build the audit service on a session, sharing the caller's transaction.

    Args:
        session (AsyncSession): The caller's session.

    Returns:
        AuditService: The service.
    """
    return AuditService(SqlAlchemyAuditRepository(session))
