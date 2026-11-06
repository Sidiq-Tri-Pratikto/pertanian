"""Principal repository over SQLAlchemy."""

from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.model.models import PrincipalKind, PrincipalModel
from app.identity.repository.base_repository import PrincipalRepository
from app.identity.repository.sqlalchemy.models import PrincipalRecord


class SqlAlchemyPrincipalRepository(PrincipalRepository):
    """Principals in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add(self, kind: PrincipalKind) -> PrincipalModel:
        """Create a principal.

        Args:
            kind (PrincipalKind): Demo or user.

        Returns:
            PrincipalModel: The stored principal.
        """
        record = PrincipalRecord(kind=kind.value)
        self.session.add(record)
        await self.session.flush()
        return PrincipalModel(id=record.id, kind=PrincipalKind(record.kind))

    async def delete(self, principal_ids: list[UUID]) -> None:
        """Delete principals.

        Args:
            principal_ids (list[UUID]): Principals to remove.
        """
        if principal_ids:
            await self.session.execute(delete(PrincipalRecord).where(PrincipalRecord.id.in_(principal_ids)))
