"""Public updates: short news the managing party writes, publishes on the public page, and may withdraw (052).

An update is announced once. ``published_at`` is set on the first publication and never reset, and only that first
publication emits ``invention.update_published``; corrections and a later republication stay quiet, so followers
(053) never get the same update twice.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require
from app.core import clock
from app.core.errors.base import ConflictError, InvalidTransitionError, NotFoundError
from app.core.locale import locale
from app.identity.model.models import Principal
from app.moderation.service.suspension import is_suspended
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.platform.service.versions import check_expected
from app.portfolio.model.schema import (
    EditUpdateRequest,
    InventionUpdateResponse,
    UpdateRequest,
    VersionedActionRequest,
)
from app.portfolio.repository.sqlalchemy.models import InventionPublicPageRecord, InventionRecord, InventionUpdateRecord
from app.portfolio.repository.sqlalchemy.repository import SqlAlchemyPortfolioRepository

_ARCHIVED = {
    "id": "Inovasi ini sudah diarsipkan. Kabarnya tetap dapat dibaca, tetapi tidak dapat ditambah atau diubah.",
    "en": "This invention is archived. Its updates stay readable but cannot be added or changed.",
}
_NOT_PUBLIC = {
    "id": "Kabar hanya dapat diterbitkan saat inovasi terbit dan halaman publiknya aktif. "
    "Aktifkan halaman publik dulu.",
    "en": "Updates can be published only while the invention is published and its public page is on. "
    "Turn on the public page first.",
}
_NOT_PUBLISHED = {
    "id": "Hanya kabar yang sedang terbit yang dapat ditarik. Muat ulang untuk melihat statusnya.",
    "en": "Only a published update can be withdrawn. Reload to see its status.",
}
# ponytail: the owner list is capped, not paged; add a cursor if an invention ever carries more updates.
_OWNER_LIMIT = 100


class UpdateService:
    """Public updates of the acting party's inventions."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def _invention(
        self, principal: Principal, invention_id: UUID, acting_party_id: UUID | None = None
    ) -> InventionRecord:
        if acting_party_id is not None:
            check_context(principal, acting_party_id)
        # Writes lock the invention, so a publish never races the owner switching the public page off.
        invention = await SqlAlchemyPortfolioRepository(self.session).find(
            invention_id, lock=acting_party_id is not None
        )
        if invention is None or invention.managing_party_id != principal.active_party_id:
            raise NotFoundError()
        require(principal, Capability.EDIT_PORTFOLIO, invention.managing_party_id)
        return invention

    async def _update(self, invention: InventionRecord, update_id: UUID) -> InventionUpdateRecord:
        update = await self.session.get(InventionUpdateRecord, update_id, with_for_update=True)
        if update is None or update.invention_id != invention.id:
            raise NotFoundError()
        return update

    async def _audit(self, principal: Principal, action: str, update: InventionUpdateRecord) -> None:
        await record_audit(
            self.session,
            action=action,
            subject_type="invention_update",
            subject_id=str(update.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
            detail={"invention_id": str(update.invention_id)},
        )

    async def list_for_owner(self, principal: Principal, invention_id: UUID) -> list[InventionUpdateResponse]:
        """List an invention's updates, newest first, drafts and withdrawn ones included.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.

        Returns:
            list[InventionUpdateResponse]: Up to 100 updates.
        """
        invention = await self._invention(principal, invention_id)
        rows = await self.session.scalars(
            select(InventionUpdateRecord)
            .where(InventionUpdateRecord.invention_id == invention.id)
            .order_by(InventionUpdateRecord.created_at.desc())
            .limit(_OWNER_LIMIT)
        )
        return [InventionUpdateResponse.model_validate(row) for row in rows]

    async def create(self, principal: Principal, invention_id: UUID, request: UpdateRequest) -> InventionUpdateResponse:
        """Save a new update as a draft; nothing is shown or sent yet.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.
            request (UpdateRequest): Acting party, title, body and language.

        Returns:
            InventionUpdateResponse: The draft.

        Raises:
            ConflictError: The invention is archived.
        """
        invention = await self._invention(principal, invention_id, request.acting_party_id)
        if invention.status == "ARCHIVED":
            raise ConflictError(_ARCHIVED[locale()])
        update = InventionUpdateRecord(
            invention_id=invention.id,
            author_account_id=principal.account_id,
            author_party_id=principal.active_party_id,
            title=request.title,
            body=request.body,
            content_locale=request.content_locale,
        )
        self.session.add(update)
        await self.session.flush()
        await self._audit(principal, "invention_update.created", update)
        return InventionUpdateResponse.model_validate(update)

    async def edit(
        self, principal: Principal, invention_id: UUID, update_id: UUID, request: EditUpdateRequest
    ) -> InventionUpdateResponse:
        """Correct an update's text; a published update stays published and is never announced again.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.
            update_id (UUID): The update.
            request (EditUpdateRequest): The corrected text and ``expected_version``.

        Returns:
            InventionUpdateResponse: The update.

        Raises:
            ConflictError: The invention is archived.
        """
        invention = await self._invention(principal, invention_id, request.acting_party_id)
        update = await self._update(invention, update_id)
        if invention.status == "ARCHIVED":
            raise ConflictError(_ARCHIVED[locale()])
        check_expected(update.version, request.expected_version)
        update.title, update.body, update.content_locale = request.title, request.body, request.content_locale
        update.version += 1
        await self.session.flush()
        await self._audit(principal, "invention_update.edited", update)
        return InventionUpdateResponse.model_validate(update)

    async def publish(
        self, principal: Principal, invention_id: UUID, update_id: UUID, request: VersionedActionRequest
    ) -> InventionUpdateResponse:
        """Show the update on the public page; the first publication alone emits ``invention.update_published``.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.
            update_id (UUID): The update.
            request (VersionedActionRequest): Acting party and ``expected_version``.

        Returns:
            InventionUpdateResponse: The published update; unchanged when it already was.

        Raises:
            InvalidTransitionError: The invention is not published, its public page is off, or it is suspended.
        """
        invention = await self._invention(principal, invention_id, request.acting_party_id)
        update = await self._update(invention, update_id)
        check_expected(update.version, request.expected_version)
        if update.status == "PUBLISHED":
            return InventionUpdateResponse.model_validate(update)
        if (
            invention.status != "PUBLISHED"
            or not await self._page_enabled(invention.id)
            or await is_suspended(self.session, "INVENTION", invention.id)
        ):
            raise InvalidTransitionError(_NOT_PUBLIC[locale()])
        first = update.published_at is None
        update.status, update.withdrawn_at = "PUBLISHED", None
        if first:
            update.published_at = clock.now()
        update.version += 1
        await self.session.flush()
        if first:
            await publish(
                self.session,
                "invention.update_published",
                {"invention_id": str(invention.id), "update_id": str(update.id)},
            )
        await self._audit(principal, "invention_update.published", update)
        return InventionUpdateResponse.model_validate(update)

    async def _page_enabled(self, invention_id: UUID) -> bool:
        """Whether the invention's public page (051) is switched on; no page row means off."""
        enabled = await self.session.scalar(
            select(InventionPublicPageRecord.enabled).where(InventionPublicPageRecord.invention_id == invention_id)
        )
        return bool(enabled)

    async def withdraw(
        self, principal: Principal, invention_id: UUID, update_id: UUID, request: VersionedActionRequest
    ) -> InventionUpdateResponse:
        """Take a published update off the public page; its first publication time is kept.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.
            update_id (UUID): The update.
            request (VersionedActionRequest): Acting party and ``expected_version``.

        Returns:
            InventionUpdateResponse: The withdrawn update; unchanged when it already was.

        Raises:
            InvalidTransitionError: The update is a draft.
        """
        invention = await self._invention(principal, invention_id, request.acting_party_id)
        update = await self._update(invention, update_id)
        check_expected(update.version, request.expected_version)
        if update.status == "WITHDRAWN":
            return InventionUpdateResponse.model_validate(update)
        if update.status != "PUBLISHED":
            raise InvalidTransitionError(_NOT_PUBLISHED[locale()])
        update.status, update.withdrawn_at = "WITHDRAWN", clock.now()
        update.version += 1
        await self.session.flush()
        await self._audit(principal, "invention_update.withdrawn", update)
        return InventionUpdateResponse.model_validate(update)


async def published_updates(session: AsyncSession, invention_id: UUID, limit: int = 3) -> list[InventionUpdateRecord]:
    """The newest published updates of an invention, for the public page.

    The caller decides whether the page itself may be shown.

    Args:
        session (AsyncSession): A session.
        invention_id (UUID): The invention.
        limit (int, optional): How many. Defaults to 3.

    Returns:
        list[InventionUpdateRecord]: Newest first by first publication.
    """
    rows = await session.scalars(
        select(InventionUpdateRecord)
        .where(InventionUpdateRecord.invention_id == invention_id, InventionUpdateRecord.status == "PUBLISHED")
        .order_by(InventionUpdateRecord.published_at.desc())
        .limit(limit)
    )
    return list(rows)
