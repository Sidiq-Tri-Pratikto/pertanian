"""Audit repository over SQLAlchemy."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.model.models import AuditEventModel
from app.audit.repository.base_repository import AuditRepository
from app.audit.repository.sqlalchemy.models import AuditEventRecord


class SqlAlchemyAuditRepository(AuditRepository):
    """Audit events in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add(self, event: AuditEventModel) -> None:
        """Append an event; it commits or rolls back with the change it describes.

        Args:
            event (AuditEventModel): The event.
        """
        self.session.add(AuditEventRecord(**event.model_dump()))
        await self.session.flush()
