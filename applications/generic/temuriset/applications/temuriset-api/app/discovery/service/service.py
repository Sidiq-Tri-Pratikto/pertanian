"""Discovery: search the public projection, sections, saved items and private relevance feedback (spec 018)."""

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context
from app.capabilities.service.service import SUPPORTED_CURRENCIES, select_capabilities
from app.core.errors.base import FieldsInvalidError, NotFoundError
from app.core.settings import get_settings
from app.core.types import decode_cursor, encode_cursor, parse_decimal
from app.discovery.model.schema import (
    SUBJECT_OF,
    DiscoveryItem,
    DiscoveryResponse,
    DiscoverySection,
    MarkedItem,
    Relaxation,
)
from app.discovery.repository.sqlalchemy.models import RelevanceFeedbackRecord, SavedItemRecord, SearchDocumentRecord
from app.discovery.repository.sqlalchemy.repository import SearchQuery, SqlAlchemyDiscoveryRepository
from app.identity.model.models import Principal

MAX_WORDS = 8
_WORD = re.compile(r"\w+", re.UNICODE)
_SECTION_TITLES = {"relevant": "Sesuai profil Anda", "new": "Baru diterbitkan", "curated": "Pilihan kurator"}
_FILTER_LABELS = {
    "q": "Hapus kata kunci",
    "sector": "Hapus filter sektor",
    "stage": "Hapus filter tahap",
    "support_form": "Hapus filter bentuk dukungan",
    "region": "Hapus filter wilayah",
    "purpose": "Hapus filter tujuan kerja sama",
    "intake": "Hapus filter status penerimaan",
    "currency": "Hapus filter kisaran dana",
    "saved": "Tampilkan semua, bukan hanya yang disimpan",
}
_MONEY_FILTERS = ("currency", "basis", "amount_min", "amount_max")
_CURATED_REASON = "Pilihan kurator, bukan peringkat"


def query_words(text: str) -> list[str]:
    """Split a query into lower-case words that are safe inside a ``tsquery``.

    Args:
        text (str): The query as typed.

    Returns:
        list[str]: At most eight words.
    """
    return _WORD.findall(text.lower())[:MAX_WORDS]


def _money_filters(filters: dict[str, Any]) -> dict[str, Any]:
    """Parse the amount filters exactly, or refuse them per field.

    Raises:
        FieldsInvalidError: When an amount is malformed or has no currency.
    """
    errors: list[dict] = []
    parsed = dict(filters)
    for name in ("amount_min", "amount_max"):
        if filters.get(name) in (None, ""):
            parsed.pop(name, None)
            continue
        value = parse_decimal(filters[name])
        if value is None or value < 0:
            errors.append({"loc": ["query", name], "msg": "Isi angka desimal, misalnya 20000.", "type": "filter"})
        parsed[name] = value
    has_amount = "amount_min" in parsed or "amount_max" in parsed
    currency = filters.get("currency")
    if has_amount and not currency:
        errors.append({"loc": ["query", "currency"], "msg": "Pilih mata uang kisaran.", "type": "filter"})
    if currency and currency not in SUPPORTED_CURRENCIES:
        errors.append({"loc": ["query", "currency"], "msg": "Pilih IDR atau USD.", "type": "filter"})
    if errors:
        raise FieldsInvalidError(errors)
    return parsed


async def published_inventions(session: AsyncSession, party_ids: list[UUID]) -> list[dict[str, Any]]:
    """Return the published inventions parties manage, from the public projection only, for profiles (031).

    Args:
        session (AsyncSession): The request's session.
        party_ids (list[UUID]): Parties.

    Returns:
        list[dict[str, Any]]: ``id``, ``title`` and ``owner_party_id`` per invention, newest first.
    """
    rows = await session.scalars(
        select(SearchDocumentRecord)
        .where(SearchDocumentRecord.subject_type == "INVENTION", SearchDocumentRecord.owner_party_id.in_(party_ids))
        .order_by(SearchDocumentRecord.published_at.desc())
    )
    return [{"id": row.subject_id, "title": row.title, "owner_party_id": row.owner_party_id} for row in rows]


class DiscoveryService:
    """What a party finds, saves and hides. Results come from ``search_documents`` only."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyDiscoveryRepository(session)

    async def _query(self, principal: Principal, result_type: str, text: str, filters: dict[str, Any], saved: bool):
        words = query_words(text)
        aliases = await self.repository.aliases(words)
        return SearchQuery(
            subject_type=SUBJECT_OF[result_type],
            party_id=principal.active_party_id,
            words=[[word, *aliases.get(word, [])] for word in words],
            text=text.strip(),
            filters=filters,
            saved_only=saved,
        )

    async def _relaxation(
        self, principal: Principal, result_type: str, text: str, filters: dict[str, Any], saved: bool
    ) -> Relaxation | None:
        """Suggest one filter to remove on purpose, checking that removing it finds something."""
        candidates: list[tuple[str, str, dict[str, Any], bool]] = []
        if text.strip():
            candidates.append(("q", "", filters, saved))
        for name in filters:
            if name in _FILTER_LABELS:
                without = {key: value for key, value in filters.items() if key != name}
                if name == "currency":
                    without = {key: value for key, value in without.items() if key not in _MONEY_FILTERS}
                candidates.append((name, text, without, saved))
        if saved:
            candidates.append(("saved", text, filters, False))
        for name, kept_text, kept_filters, kept_saved in candidates:
            total = await self.repository.count(
                await self._query(principal, result_type, kept_text, kept_filters, kept_saved)
            )
            if total:
                return Relaxation(remove=name, label=_FILTER_LABELS[name], total_estimate=total)
        if len(candidates) > 1:
            total = await self.repository.count(await self._query(principal, result_type, "", {}, False))
            if total:
                return Relaxation(remove="all", label="Hapus semua filter", total_estimate=total)
        return None

    async def _preferences(self, party_id: UUID) -> set[str]:
        """Sectors the party stated itself, on its partner profile or its published inventions."""
        sectors: set[str] = set()
        for subject_type in ("PARTNER", "INVENTION"):
            for row in await self.repository.owned(subject_type, party_id):
                sectors.update(row.filters.get("sectors", []))
        return sectors

    async def search(  # noqa: PLR0913 - one argument per query parameter of the route
        self,
        principal: Principal,
        result_type: str,
        *,
        text: str = "",
        filters: dict[str, Any] | None = None,
        saved: bool = False,
        cursor: str | None = None,
        limit: int = 20,
    ) -> DiscoveryResponse:
        """Search one result type, grouped into sections, with the active filters echoed back.

        Args:
            principal (Principal): Who is searching.
            result_type (str): ``inventions``, ``funding`` or ``partners``.
            text (str, optional): Query text. Defaults to "".
            filters (dict[str, Any] | None, optional): Filters by name. Defaults to None.
            saved (bool, optional): Only saved items. Defaults to False.
            cursor (str | None, optional): Position from a previous page. Defaults to None.
            limit (int, optional): Page size, at most 100. Defaults to 20.

        Returns:
            DiscoveryResponse: The page.
        """
        active = {key: value for key, value in (filters or {}).items() if value not in (None, "")}
        echoed = {**active, **({"q": text.strip()} if text.strip() else {}), **({"saved": True} if saved else {})}
        parsed = _money_filters(active)
        empty = DiscoveryResponse(
            type=result_type,  # type: ignore[arg-type]
            sections=[DiscoverySection(id=key, title=title, items=[]) for key, title in _SECTION_TITLES.items()],  # type: ignore[arg-type]
            filters=echoed,
            next_cursor=None,
            total_estimate=0,
            relaxation=None,
        )
        settings = get_settings()
        if result_type == "funding" and "company_funding" not in select_capabilities(
            settings.composition, settings.composition_overrides
        ):
            return empty
        after = None
        if cursor:
            position = decode_cursor(cursor)
            after = (datetime.fromisoformat(position["published_at"]), UUID(position["id"]))
        query = await self._query(principal, result_type, text, parsed, saved)
        rows = await self.repository.search(query, after=after, limit=limit + 1)
        total = await self.repository.count(query)
        if not rows and after is None:
            empty.relaxation = await self._relaxation(principal, result_type, text, parsed, saved) if echoed else None
            return empty
        page, more = rows[:limit], len(rows) > limit
        saved_keys = await self.repository.keys_of(SavedItemRecord, principal.active_party_id)
        preferences = await self._preferences(principal.active_party_id)
        groups: dict[str, list[DiscoveryItem]] = {key: [] for key in _SECTION_TITLES}
        for row in page:
            matching = sorted(preferences & set(row.filters.get("sectors", [])))
            reasons = [f"Sesuai sektor pada profil Anda: {', '.join(matching)}"] if matching else []
            if row.curated:
                reasons.append(_CURATED_REASON)
            item = DiscoveryItem(
                subject_type=row.subject_type,  # type: ignore[arg-type]
                subject_id=row.subject_id,
                title=row.title,
                card=row.card,
                curated=row.curated,
                saved=(row.subject_type, row.subject_id) in saved_keys,
                reasons=reasons,
            )
            groups["curated" if row.curated else "relevant" if matching else "new"].append(item)
        last = page[-1]
        return DiscoveryResponse(
            type=result_type,  # type: ignore[arg-type]
            sections=[
                DiscoverySection(id=key, title=title, items=groups[key])  # type: ignore[arg-type]
                for key, title in _SECTION_TITLES.items()
            ],
            filters=echoed,
            next_cursor=encode_cursor({"published_at": last.published_at.isoformat(), "id": str(last.id)})
            if more
            else None,
            total_estimate=total,
            relaxation=None,
        )

    async def _visible(self, subject_type: str, subject_id: UUID) -> SearchDocumentRecord:
        record = await self.repository.find(subject_type, subject_id)
        if record is None:
            raise NotFoundError()
        return record

    async def list_marked(self, principal: Principal, model: type) -> list[MarkedItem]:
        """List what the acting party saved or hid.

        Args:
            principal (Principal): Who is signed in.
            model (type): ``SavedItemRecord`` or ``RelevanceFeedbackRecord``.

        Returns:
            list[MarkedItem]: Subjects.
        """
        keys = await self.repository.keys_of(model, principal.active_party_id)
        return [MarkedItem(subject_type=kind, subject_id=subject) for kind, subject in sorted(keys, key=str)]  # type: ignore[arg-type]

    async def mark(
        self, principal: Principal, acting_party_id: UUID, model: type, subject_type: str, subject_id: UUID
    ) -> MarkedItem:
        """Save or hide a published subject for the acting party only.

        Args:
            principal (Principal): Who is signed in.
            acting_party_id (UUID): The party the client acts as.
            model (type): ``SavedItemRecord`` or ``RelevanceFeedbackRecord``.
            subject_type (str): Subject type.
            subject_id (UUID): Subject.

        Returns:
            MarkedItem: The subject.

        Raises:
            NotFoundError: When the subject is not published.
        """
        check_context(principal, acting_party_id)
        await self._visible(subject_type, subject_id)
        await self.repository.mark(model, principal.active_party_id, subject_type, subject_id)
        return MarkedItem(subject_type=subject_type, subject_id=subject_id)  # type: ignore[arg-type]

    async def unmark(
        self, principal: Principal, acting_party_id: UUID, model: type, subject_type: str, subject_id: UUID
    ) -> None:
        """Undo a save or a hide.

        Args:
            principal (Principal): Who is signed in.
            acting_party_id (UUID): The party the client acts as.
            model (type): ``SavedItemRecord`` or ``RelevanceFeedbackRecord``.
            subject_type (str): Subject type.
            subject_id (UUID): Subject.

        Raises:
            NotFoundError: When there was nothing to undo.
        """
        check_context(principal, acting_party_id)
        if not await self.repository.unmark(model, principal.active_party_id, subject_type, subject_id):
            raise NotFoundError()

    async def set_curated(self, subject_type: str, subject_id: UUID, curated: bool) -> None:
        """Set the operator's curated flag (FR-005). Never computed from activity; no route sets it yet.

        Args:
            subject_type (str): Subject type.
            subject_id (UUID): Subject.
            curated (bool): The flag.

        Raises:
            NotFoundError: When the subject is not in the projection.
        """
        if not await self.repository.set_curated(subject_type, subject_id, curated):
            raise NotFoundError()


SAVED = SavedItemRecord
HIDDEN = RelevanceFeedbackRecord
