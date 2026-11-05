"""Document data access. Writes join the caller's transaction."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.repository.sqlalchemy.models import (
    DocumentGrantRecord,
    DocumentRecord,
    DocumentVersionRecord,
    DownloadEventRecord,
    UploadIntentRecord,
)


class SqlAlchemyDocumentRepository:
    """Documents over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to a session.

        Args:
            session (AsyncSession): The request's or worker's session.
        """
        self.session = session

    async def add(self, record: Any) -> Any:
        """Insert a row.

        Args:
            record (Any): An ORM row.

        Returns:
            Any: The row with generated values.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def document(self, document_id: UUID) -> DocumentRecord | None:
        """Find a document.

        Args:
            document_id (UUID): The document.

        Returns:
            DocumentRecord | None: The document.
        """
        return await self.session.get(DocumentRecord, document_id)

    async def documents_of(self, party_id: UUID) -> list[DocumentRecord]:
        """List a party's documents, newest first.

        Args:
            party_id (UUID): The owner.

        Returns:
            list[DocumentRecord]: Documents.
        """
        rows = await self.session.scalars(
            select(DocumentRecord)
            .where(DocumentRecord.owner_party_id == party_id)
            .order_by(DocumentRecord.created_at.desc())
        )
        return list(rows)

    async def intent(self, intent_id: UUID) -> UploadIntentRecord | None:
        """Lock an upload intent.

        Args:
            intent_id (UUID): The intent.

        Returns:
            UploadIntentRecord | None: The intent.
        """
        return await self.session.scalar(
            select(UploadIntentRecord).where(UploadIntentRecord.id == intent_id).with_for_update()
        )

    async def versions(self, document_id: UUID) -> list[DocumentVersionRecord]:
        """List a document's versions, oldest first.

        Args:
            document_id (UUID): The document.

        Returns:
            list[DocumentVersionRecord]: Versions.
        """
        rows = await self.session.scalars(
            select(DocumentVersionRecord)
            .where(DocumentVersionRecord.document_id == document_id)
            .order_by(DocumentVersionRecord.number)
        )
        return list(rows)

    async def version(
        self, *, version_id: UUID | None = None, document_id: UUID | None = None, number: int | None = None
    ):
        """Find one version by id, or by document and number.

        Args:
            version_id (UUID | None, optional): The version. Defaults to None.
            document_id (UUID | None, optional): Its document. Defaults to None.
            number (int | None, optional): Its number. Defaults to None.

        Returns:
            DocumentVersionRecord | None: The version.
        """
        if version_id is not None:
            return await self.session.get(DocumentVersionRecord, version_id)
        return await self.session.scalar(
            select(DocumentVersionRecord).where(
                DocumentVersionRecord.document_id == document_id, DocumentVersionRecord.number == number
            )
        )

    async def next_number(self, document_id: UUID) -> int:
        """Return the next version number.

        Args:
            document_id (UUID): The document.

        Returns:
            int: One past the highest.
        """
        last = await self.session.scalar(
            select(func.max(DocumentVersionRecord.number)).where(DocumentVersionRecord.document_id == document_id)
        )
        return (last or 0) + 1

    async def update_version(self, version_id: UUID, **values: Any) -> None:
        """Change one version's states.

        Args:
            version_id (UUID): The version.
            **values (Any): Column values.
        """
        await self.session.execute(
            update(DocumentVersionRecord)
            .where(DocumentVersionRecord.id == version_id)
            .values(version=DocumentVersionRecord.version + 1, **values)
        )

    async def supersede_reviews(self, document_id: UUID, below: int) -> None:
        """A new version supersedes older review states, never their grants.

        Args:
            document_id (UUID): The document.
            below (int): The new version's number.
        """
        await self.session.execute(
            update(DocumentVersionRecord)
            .where(DocumentVersionRecord.document_id == document_id, DocumentVersionRecord.number < below)
            .values(review_state="SUPERSEDED")
        )

    async def grants_of(self, document_id: UUID) -> list[tuple[DocumentGrantRecord, int, int]]:
        """List a document's grants with the version number and the downloads each produced.

        Args:
            document_id (UUID): The document.

        Returns:
            list[tuple[DocumentGrantRecord, int, int]]: Grant, version number, download count.
        """
        downloads = (
            select(func.count())
            .select_from(DownloadEventRecord)
            .where(DownloadEventRecord.grant_id == DocumentGrantRecord.id)
            .scalar_subquery()
        )
        rows = await self.session.execute(
            select(DocumentGrantRecord, DocumentVersionRecord.number, downloads)
            .join(DocumentVersionRecord, DocumentVersionRecord.id == DocumentGrantRecord.document_version_id)
            .where(DocumentVersionRecord.document_id == document_id)
            .order_by(DocumentGrantRecord.created_at)
        )
        return [(grant, number, count) for grant, number, count in rows]

    async def grant(self, grant_id: UUID) -> DocumentGrantRecord | None:
        """Lock a grant.

        Args:
            grant_id (UUID): The grant.

        Returns:
            DocumentGrantRecord | None: The grant.
        """
        return await self.session.scalar(
            select(DocumentGrantRecord).where(DocumentGrantRecord.id == grant_id).with_for_update()
        )

    async def grants_for(self, version_id: UUID, grantee_party_id: UUID) -> list[DocumentGrantRecord]:
        """List a party's grants on one version, active ones first.

        Args:
            version_id (UUID): The version.
            grantee_party_id (UUID): The party.

        Returns:
            list[DocumentGrantRecord]: Grants.
        """
        rows = await self.session.scalars(
            select(DocumentGrantRecord)
            .where(
                DocumentGrantRecord.document_version_id == version_id,
                DocumentGrantRecord.grantee_party_id == grantee_party_id,
            )
            .order_by(DocumentGrantRecord.revoked_at.is_not(None), DocumentGrantRecord.created_at)
        )
        return list(rows)

    async def downloads_of(self, grant_id: UUID) -> int:
        """Count copies delivered under a grant.

        Args:
            grant_id (UUID): The grant.

        Returns:
            int: Download events.
        """
        return (
            await self.session.scalar(
                select(func.count()).select_from(DownloadEventRecord).where(DownloadEventRecord.grant_id == grant_id)
            )
            or 0
        )
