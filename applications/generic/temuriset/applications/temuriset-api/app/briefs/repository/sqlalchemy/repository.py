"""Preflight and brief storage."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.briefs.repository.sqlalchemy.models import BriefRecord, PreflightRecord


class SqlAlchemyBriefRepository:
    """Writes and reads preflights and briefs."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add(self, record: PreflightRecord | BriefRecord) -> PreflightRecord | BriefRecord:
        """Insert a record.

        Args:
            record (PreflightRecord | BriefRecord): The record.

        Returns:
            PreflightRecord | BriefRecord: The stored record with its id.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def preflight_by_token(self, token_sha256: str) -> PreflightRecord | None:
        """Find a preflight by its token's digest.

        Args:
            token_sha256 (str): SHA-256 of the token.

        Returns:
            PreflightRecord | None: The preflight.
        """
        return await self.session.scalar(select(PreflightRecord).where(PreflightRecord.token_sha256 == token_sha256))

    async def brief(self, brief_id: UUID) -> BriefRecord | None:
        """Find a brief.

        Args:
            brief_id (UUID): The brief.

        Returns:
            BriefRecord | None: The brief.
        """
        return await self.session.get(BriefRecord, brief_id)

    async def brief_of(self, preflight_id: UUID) -> BriefRecord | None:
        """Find a preflight's brief.

        Args:
            preflight_id (UUID): The preflight.

        Returns:
            BriefRecord | None: The brief.
        """
        return await self.session.scalar(select(BriefRecord).where(BriefRecord.preflight_id == preflight_id))

    async def preflight(self, preflight_id: UUID) -> PreflightRecord | None:
        """Find a preflight.

        Args:
            preflight_id (UUID): The preflight.

        Returns:
            PreflightRecord | None: The preflight.
        """
        return await self.session.get(PreflightRecord, preflight_id)
