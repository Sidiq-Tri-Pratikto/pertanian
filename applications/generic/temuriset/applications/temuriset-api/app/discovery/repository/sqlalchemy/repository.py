"""Search projection queries. Every filter is a hard condition; nothing here broadens a search."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, Numeric, and_, delete, func, or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.discovery.repository.sqlalchemy.models import (
    AliasTermRecord,
    RelevanceFeedbackRecord,
    SavedItemRecord,
    SearchDocumentRecord,
)

# Filter name to the JSON list it must be in.
LIST_FILTERS = {
    "sector": "sectors",
    "stage": "stages",
    "support_form": "support_forms",
    "region": "regions",
    "purpose": "relationship_forms",
}


@dataclass
class SearchQuery:
    """What one discovery search asks for.

    Attributes:
        subject_type (str): ``INVENTION``, ``FUNDING_REQUEST`` or ``PARTNER``.
        party_id (UUID): The searching party; its own subjects and hidden items stay out.
        words (list[list[str]]): Each query word with its aliases; every word must match.
        text (str): The raw query, for title similarity.
        filters (dict[str, Any]): Active filters by name.
        saved_only (bool): Only the party's saved items.
    """

    subject_type: str
    party_id: UUID
    words: list[list[str]] = field(default_factory=list)
    text: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    saved_only: bool = False


class SqlAlchemyDiscoveryRepository:
    """Reads and writes the search projection, saved items and feedback."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's or worker's session.
        """
        self.session = session

    async def lock_updates(self, *, exclusive: bool = False) -> None:
        """Let moderation replace the projection between worker writes, never during a stale rebuild."""
        key = func.hashtextextended("temuriset.discovery", 0)
        lock = func.pg_advisory_xact_lock if exclusive else func.pg_advisory_xact_lock_shared
        await self.session.execute(select(lock(key)))

    async def upsert(
        self,
        *,
        subject_type: str,
        subject_id: UUID,
        version_id: UUID | None,
        owner_party_id: UUID,
        title: str,
        body: str,
        filters: dict[str, Any],
        card: dict[str, Any],
        published_at: datetime | None,
    ) -> None:
        """Write one subject's row. A null ``published_at`` keeps the first one; ``curated`` is never touched.

        Args:
            subject_type (str): Subject type.
            subject_id (UUID): Subject.
            version_id (UUID | None): The published version, when the subject has versions.
            owner_party_id (UUID): Who owns it.
            title (str): Title.
            body (str): Searchable published text.
            filters (dict[str, Any]): Filter values.
            card (dict[str, Any]): What a result card shows.
            published_at (datetime | None): When it was published, or None to keep the stored time.
        """
        now = clock.now()
        values = {
            "version_id": version_id,
            "owner_party_id": owner_party_id,
            "title": title[:200],
            "body": body,
            "filters": filters,
            "card": card,
            "updated_at": now,
        }
        statement = insert(SearchDocumentRecord).values(
            subject_type=subject_type,
            subject_id=subject_id,
            published_at=published_at or now,
            created_at=now,
            **values,
        )
        changes = {**values, "version": SearchDocumentRecord.version + 1}
        if published_at is not None:
            changes["published_at"] = published_at
        await self.session.execute(
            statement.on_conflict_do_update(index_elements=["subject_type", "subject_id"], set_=changes)
        )

    async def remove(self, subject_type: str, subject_id: UUID) -> None:
        """Remove a subject's row.

        Args:
            subject_type (str): Subject type.
            subject_id (UUID): Subject.
        """
        await self.session.execute(
            delete(SearchDocumentRecord).where(
                SearchDocumentRecord.subject_type == subject_type, SearchDocumentRecord.subject_id == subject_id
            )
        )

    async def find(self, subject_type: str, subject_id: UUID) -> SearchDocumentRecord | None:
        """Find a subject's row.

        Args:
            subject_type (str): Subject type.
            subject_id (UUID): Subject.

        Returns:
            SearchDocumentRecord | None: The row.
        """
        return await self.session.scalar(
            select(SearchDocumentRecord).where(
                SearchDocumentRecord.subject_type == subject_type, SearchDocumentRecord.subject_id == subject_id
            )
        )

    async def raises_showing(self, invention_id: UUID) -> list[UUID]:
        """Find cards still showing an invention even when the live funding link has changed."""
        row = SearchDocumentRecord
        statement = select(row.subject_id).where(
            row.subject_type == "FUNDING_REQUEST",
            row.card["inventions"].contains([{"invention_id": str(invention_id)}]),
        )
        return list(await self.session.scalars(statement))

    async def owned(self, subject_type: str, party_id: UUID) -> list[SearchDocumentRecord]:
        """List a party's own rows of one type, for its stated preferences.

        Args:
            subject_type (str): Subject type.
            party_id (UUID): The party.

        Returns:
            list[SearchDocumentRecord]: Rows.
        """
        query = select(SearchDocumentRecord).where(
            SearchDocumentRecord.subject_type == subject_type, SearchDocumentRecord.owner_party_id == party_id
        )
        return list(await self.session.scalars(query.limit(100)))

    async def aliases(self, words: list[str]) -> dict[str, list[str]]:
        """Return the Indonesian words each query word also matches.

        Args:
            words (list[str]): Lower-case words.

        Returns:
            dict[str, list[str]]: Aliases per word that has any.
        """
        if not words:
            return {}
        rows = await self.session.execute(
            select(AliasTermRecord.term, AliasTermRecord.canonical).where(AliasTermRecord.term.in_(words))
        )
        found: dict[str, list[str]] = {}
        for term, canonical in rows:
            found.setdefault(term, []).extend(canonical.split())
        return found

    def _conditions(self, query: SearchQuery) -> list[ColumnElement[bool]]:
        row = SearchDocumentRecord
        conditions: list[ColumnElement[bool]] = [
            row.subject_type == query.subject_type,
            row.owner_party_id != query.party_id,
            ~tuple_(row.subject_type, row.subject_id).in_(
                select(RelevanceFeedbackRecord.subject_type, RelevanceFeedbackRecord.subject_id).where(
                    RelevanceFeedbackRecord.party_id == query.party_id
                )
            ),
        ]
        if query.saved_only:
            conditions.append(
                tuple_(row.subject_type, row.subject_id).in_(
                    select(SavedItemRecord.subject_type, SavedItemRecord.subject_id).where(
                        SavedItemRecord.party_id == query.party_id
                    )
                )
            )
        if query.words:
            # Every word must match, as itself or an alias; prefixes match so "filt" finds "filter".
            expression = " & ".join("(" + " | ".join(f"{word}:*" for word in options) + ")" for options in query.words)
            conditions.append(
                or_(row.tsv.op("@@")(func.to_tsquery("simple", expression)), row.title.op("%")(query.text))
            )
        for name, key in LIST_FILTERS.items():
            if query.filters.get(name):
                conditions.append(row.filters[key].contains([query.filters[name]]))
        if query.filters.get("intake"):
            conditions.append(row.filters["intake"].astext == query.filters["intake"])
        if query.filters.get("currency"):
            conditions.extend(self._money(query.filters))
        return conditions

    @staticmethod
    def _money(filters: dict[str, Any]) -> list[ColumnElement[bool]]:
        """Compare amounts only within one currency and basis; nothing is converted."""
        row = SearchDocumentRecord
        conditions: list[ColumnElement[bool]] = [row.filters["currency"].astext == filters["currency"]]
        if filters.get("basis"):
            conditions.append(row.filters["basis"].astext == filters["basis"])
        low, high = row.filters["amount_min"].astext.cast(Numeric), row.filters["amount_max"].astext.cast(Numeric)
        wanted_min: Decimal | None = filters.get("amount_min")
        wanted_max: Decimal | None = filters.get("amount_max")
        if wanted_max is not None:
            conditions.append(low <= wanted_max)
        if wanted_min is not None:
            conditions.append(high >= wanted_min)
        return conditions

    async def search(
        self, query: SearchQuery, *, after: tuple[datetime, UUID] | None, limit: int
    ) -> list[SearchDocumentRecord]:
        """Return one page, newest publication first.

        Args:
            query (SearchQuery): The search.
            after (tuple[datetime, UUID] | None): Position of the previous page's last row.
            limit (int): Rows to return.

        Returns:
            list[SearchDocumentRecord]: Rows.
        """
        row = SearchDocumentRecord
        conditions = self._conditions(query)
        if after is not None:
            conditions.append(tuple_(row.published_at, row.id) < tuple_(*after))
        statement = select(row).where(and_(*conditions)).order_by(row.published_at.desc(), row.id.desc()).limit(limit)
        return list(await self.session.scalars(statement))

    async def count(self, query: SearchQuery) -> int:
        """Count every row a search matches.

        Args:
            query (SearchQuery): The search.

        Returns:
            int: The count.
        """
        return (
            await self.session.scalar(
                select(func.count()).select_from(SearchDocumentRecord).where(and_(*self._conditions(query)))
            )
            or 0
        )

    async def keys_of(self, model: type, party_id: UUID) -> set[tuple[str, UUID]]:
        """Return the subjects a party saved or hid.

        Args:
            model (type): ``SavedItemRecord`` or ``RelevanceFeedbackRecord``.
            party_id (UUID): The party.

        Returns:
            set[tuple[str, UUID]]: Subject type and id pairs.
        """
        rows = await self.session.execute(
            select(model.subject_type, model.subject_id)
            .join(
                SearchDocumentRecord,
                and_(
                    model.subject_type == SearchDocumentRecord.subject_type,
                    model.subject_id == SearchDocumentRecord.subject_id,
                ),
            )
            .where(model.party_id == party_id)  # type: ignore[attr-defined]
        )
        return {(subject_type, subject_id) for subject_type, subject_id in rows}

    async def mark(self, model: type, party_id: UUID, subject_type: str, subject_id: UUID) -> None:
        """Save or hide a subject for a party; doing it twice changes nothing.

        Args:
            model (type): ``SavedItemRecord`` or ``RelevanceFeedbackRecord``.
            party_id (UUID): The party.
            subject_type (str): Subject type.
            subject_id (UUID): Subject.
        """
        statement = insert(model).values(
            party_id=party_id, subject_type=subject_type, subject_id=subject_id, created_at=clock.now()
        )
        await self.session.execute(statement.on_conflict_do_nothing())

    async def unmark(self, model: type, party_id: UUID, subject_type: str, subject_id: UUID) -> bool:
        """Undo a save or a hide.

        Args:
            model (type): ``SavedItemRecord`` or ``RelevanceFeedbackRecord``.
            party_id (UUID): The party.
            subject_type (str): Subject type.
            subject_id (UUID): Subject.

        Returns:
            bool: Whether there was one to undo.
        """
        result = await self.session.execute(
            delete(model).where(
                model.party_id == party_id,  # type: ignore[attr-defined]
                model.subject_type == subject_type,  # type: ignore[attr-defined]
                model.subject_id == subject_id,  # type: ignore[attr-defined]
            )
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def set_curated(self, subject_type: str, subject_id: UUID, curated: bool) -> bool:
        """Set the operator's curated flag on a row.

        Args:
            subject_type (str): Subject type.
            subject_id (UUID): Subject.
            curated (bool): The flag.

        Returns:
            bool: Whether the row exists.
        """
        record = await self.find(subject_type, subject_id)
        if record is None:
            return False
        record.curated = curated
        await self.session.flush()
        return True
