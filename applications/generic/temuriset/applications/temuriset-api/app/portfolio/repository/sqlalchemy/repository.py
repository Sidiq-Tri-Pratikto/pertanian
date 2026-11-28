"""Portfolio data access. Writes join the caller's transaction."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.service.service import available_document_version_number
from app.portfolio.model.schema import (
    ClaimResponse,
    DocumentVersionChoice,
    FactResponse,
    InventionVersionResponse,
    ReadinessResponse,
)
from app.portfolio.repository.sqlalchemy.models import (
    InventionClaimRecord,
    InventionFactRecord,
    InventionReadinessRecord,
    InventionRecord,
    InventionVersionRecord,
)

_CONTENT = ("title", "summary", "problem", "solution", "intended_users", "sector", "stage", "keywords", "private_notes")


class SqlAlchemyPortfolioRepository:
    """Inventions and versions over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to a session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add_invention(self, managing_party_id: UUID) -> InventionRecord:
        """Insert an invention with an empty draft, version 1.

        Args:
            managing_party_id (UUID): The managing party.

        Returns:
            InventionRecord: The invention.
        """
        invention = InventionRecord(managing_party_id=managing_party_id, status="DRAFT")
        self.session.add(invention)
        await self.session.flush()
        draft = InventionVersionRecord(invention_id=invention.id, number=1, state="draft")
        self.session.add(draft)
        await self.session.flush()
        invention.draft_version_id = draft.id
        await self.session.flush()
        return invention

    async def find(self, invention_id: UUID, *, lock: bool = False) -> InventionRecord | None:
        """Find an invention.

        Args:
            invention_id (UUID): The invention.
            lock (bool, optional): Lock it for this transaction. Defaults to False.

        Returns:
            InventionRecord | None: The invention.
        """
        query = select(InventionRecord).where(InventionRecord.id == invention_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def of_party(self, party_id: UUID) -> list[InventionRecord]:
        """List a party's inventions, newest change first.

        Args:
            party_id (UUID): The managing party.

        Returns:
            list[InventionRecord]: Inventions.
        """
        rows = await self.session.scalars(
            select(InventionRecord)
            .where(InventionRecord.managing_party_id == party_id)
            .order_by(InventionRecord.updated_at.desc())
        )
        return list(rows)

    async def published_titles(self, party_ids: set[UUID]) -> list[tuple[UUID, UUID, str]]:
        """Read the current public titles, independent of the discovery worker.

        Args:
            party_ids (set[UUID]): Parties managing the inventions.

        Returns:
            list[tuple[UUID, UUID, str]]: Manager, invention and title, newest first.
        """
        query = (
            select(InventionRecord.managing_party_id, InventionRecord.id, InventionVersionRecord.title)
            .join(InventionVersionRecord, InventionRecord.published_version_id == InventionVersionRecord.id)
            .where(InventionRecord.managing_party_id.in_(party_ids), InventionRecord.status != "ARCHIVED")
            .order_by(InventionVersionRecord.published_at.desc(), InventionRecord.id)
        )
        rows = (await self.session.execute(query)).all()
        return [(party_id, invention_id, title) for party_id, invention_id, title in rows]

    async def version(self, version_id: UUID | None) -> InventionVersionResponse | None:
        """Read one version with its facts and claims.

        Args:
            version_id (UUID | None): The version.

        Returns:
            InventionVersionResponse | None: The version.
        """
        if version_id is None:
            return None
        record = await self.session.get(InventionVersionRecord, version_id)
        if record is None:
            return None
        facts = await self.session.scalars(
            select(InventionFactRecord)
            .where(InventionFactRecord.version_id == version_id)
            .order_by(InventionFactRecord.position)
        )
        claims = await self.session.scalars(
            select(InventionClaimRecord)
            .where(InventionClaimRecord.version_id == version_id)
            .order_by(InventionClaimRecord.position)
        )
        readiness_row = await self.session.scalar(
            select(InventionReadinessRecord).where(InventionReadinessRecord.version_id == version_id)
        )
        readiness = None
        if readiness_row is not None:
            available = (
                await available_document_version_number(self.session, readiness_row.evidence_version_id)
                if readiness_row.evidence_version_id is not None
                else None
            )
            readiness = ReadinessResponse(
                tkt_level=readiness_row.tkt_level,
                note=readiness_row.note,
                has_evidence=available is not None,
                evidence=(
                    DocumentVersionChoice(document_id=available[0], version=available[1])
                    if available is not None
                    else None
                ),
            )
        return InventionVersionResponse(
            number=record.number,
            state=record.state,
            facts=[FactResponse.model_validate(fact, from_attributes=True) for fact in facts],
            claims=[ClaimResponse.model_validate(claim, from_attributes=True) for claim in claims],
            published_at=record.published_at,
            readiness=readiness,
            **{field: getattr(record, field) for field in _CONTENT},
        )

    async def numbers(self, invention_id: UUID) -> list[int]:
        """List every version number of an invention.

        Args:
            invention_id (UUID): The invention.

        Returns:
            list[int]: Ascending.
        """
        rows = await self.session.scalars(
            select(InventionVersionRecord.number)
            .where(InventionVersionRecord.invention_id == invention_id)
            .order_by(InventionVersionRecord.number)
        )
        return list(rows)

    async def write_draft(
        self, invention: InventionRecord, content: dict[str, Any], facts: list[dict], claims: list[dict]
    ) -> None:
        """Replace the draft's content, starting a successor draft when only a published version exists.

        Args:
            invention (InventionRecord): The locked invention.
            content (dict[str, Any]): Version fields.
            facts (list[dict]): Facts in order.
            claims (list[dict]): Claims in order.
        """
        if invention.draft_version_id is None:
            last = await self.session.scalar(
                select(func.max(InventionVersionRecord.number)).where(
                    InventionVersionRecord.invention_id == invention.id
                )
            )
            draft = InventionVersionRecord(invention_id=invention.id, number=(last or 0) + 1, state="draft", **content)
            self.session.add(draft)
            await self.session.flush()
            invention.draft_version_id = draft.id
        else:
            await self.session.execute(
                update(InventionVersionRecord)
                .where(InventionVersionRecord.id == invention.draft_version_id)
                .values(version=InventionVersionRecord.version + 1, **content)
            )
            await self.session.execute(
                delete(InventionFactRecord).where(InventionFactRecord.version_id == invention.draft_version_id)
            )
            await self.session.execute(
                delete(InventionClaimRecord).where(InventionClaimRecord.version_id == invention.draft_version_id)
            )
        for position, fact in enumerate(facts):
            self.session.add(InventionFactRecord(version_id=invention.draft_version_id, position=position, **fact))
        for position, claim in enumerate(claims):
            self.session.add(InventionClaimRecord(version_id=invention.draft_version_id, position=position, **claim))
        await self.session.flush()

    async def set_version_state(self, version_id: UUID, **values: Any) -> None:
        """Change a version's lifecycle fields (state, publication time). Content never changes after publication.

        Args:
            version_id (UUID): The version.
            **values (Any): Column values.
        """
        await self.session.execute(
            update(InventionVersionRecord).where(InventionVersionRecord.id == version_id).values(**values)
        )

    async def set_readiness(
        self,
        version_id: UUID,
        tkt_level: int | None,
        note: str = "",
        evidence_version_id: UUID | None = None,
    ) -> None:
        """Upsert or clear TKT readiness for one draft version (055).

        Args:
            version_id (UUID): The draft version.
            tkt_level (int | None): Level 1-9, or None to delete any stored readiness.
            note (str, optional): Optional note. Defaults to empty string.
            evidence_version_id (UUID | None, optional): Optional owned evidence document version id.
        """
        existing = await self.session.scalar(
            select(InventionReadinessRecord).where(InventionReadinessRecord.version_id == version_id)
        )
        if tkt_level is None:
            if existing is not None:
                await self.session.delete(existing)
                await self.session.flush()
            return
        if existing is None:
            self.session.add(
                InventionReadinessRecord(
                    version_id=version_id,
                    tkt_level=tkt_level,
                    note=note,
                    evidence_version_id=evidence_version_id,
                )
            )
        else:
            existing.tkt_level = tkt_level
            existing.note = note
            existing.evidence_version_id = evidence_version_id
            existing.version += 1
        await self.session.flush()

    async def copy_readiness(self, from_version_id: UUID, to_version_id: UUID) -> None:
        """Copy TKT readiness from a published version to its new draft successor (055).

        Args:
            from_version_id (UUID): Source version.
            to_version_id (UUID): New draft version.
        """
        existing = await self.session.scalar(
            select(InventionReadinessRecord).where(InventionReadinessRecord.version_id == from_version_id)
        )
        if existing is None:
            return
        await self.set_readiness(
            to_version_id,
            existing.tkt_level,
            existing.note,
            existing.evidence_version_id,
        )
