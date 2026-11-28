"""Following one invention by email, without an account (spec 053).

Same rules as quick subscriptions (046): double opt-in, the same ``check_email`` answer for every address, links
stored only as hashes and carried in request bodies, and shared rate limits. A follower gets each public update
(052) at most once, and only updates first published after they confirmed. Every queued email is checked again
just before delivery, so unfollowing, archiving, or withdrawing the update stops it.
"""

import secrets
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.core.errors.base import NotFoundError
from app.core.settings import get_settings
from app.identity.service.mailbox_service import DisabledMailbox, MailReference, MailUnavailableError, mailbox_for
from app.portfolio.repository.sqlalchemy.models import InventionUpdateRecord
from app.portfolio.repository.sqlalchemy.repository import SqlAlchemyPortfolioRepository
from app.subscriptions.model.schema import FollowRequest, FollowResponse, SubscribeResponse
from app.subscriptions.repository.sqlalchemy.models import (
    InventionFollowDeliveryRecord,
    InventionFollowLinkRecord,
    InventionFollowRecord,
)
from app.subscriptions.service import mail
from app.subscriptions.service.service import (
    CONFIRM_LIFETIME,
    MANAGE_LIFETIME,
    SubscriptionService,
    _hash,
    masked,
    rate_limit,
)
from app.subscriptions.service.unsubscribe import mint_unsubscribe_token
from app.worker.registry import registry

FANOUT_CONSUMER = "follows.update_fanout"


async def _followable(session: AsyncSession, invention_id: UUID) -> dict[str, Any] | None:
    """The public projection when the invention's public page is on, else None."""
    found = await SubscriptionService(session)._public(invention_id, gate="page")  # noqa: SLF001 - the page's own gate
    return found if found is not None and found["public_page"] else None


async def _title(session: AsyncSession, invention_id: UUID) -> str:
    """The published title, kept readable on a manage page after the invention left the public page."""
    repository = SqlAlchemyPortfolioRepository(session)
    invention = await repository.find(invention_id)
    version = await repository.version(invention.published_version_id) if invention is not None else None
    return version.title if version is not None else ""


async def follow_deliverable(session: AsyncSession, follow_id: UUID, to_email: str, updates: list[UUID]) -> bool:
    """Whether a queued follow email may still go out.

    Args:
        session (AsyncSession): The worker's session.
        follow_id (UUID): The follow.
        to_email (str): The address in the sealed message.
        updates (list[UUID]): The update the message carries; none for a confirmation or manage link.

    Returns:
        bool: True while the follow stands, and the update and the public page are still published.
    """
    record = await session.get(InventionFollowRecord, follow_id)
    if record is None or record.email != to_email or record.status == "UNSUBSCRIBED":
        return False
    for update_id in updates:
        update = await session.get(InventionUpdateRecord, update_id)
        if update is None or update.status != "PUBLISHED" or await _followable(session, update.invention_id) is None:
            return False
    return True


class FollowService:
    """Everything a follower can do with an email and the links sent to it."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.settings = get_settings()
        self.mailbox = mailbox_for(self.settings)

    async def _link(self, record: InventionFollowRecord, purpose: str, lifetime: timedelta) -> str:
        token = secrets.token_urlsafe(32)
        self.session.add(
            InventionFollowLinkRecord(
                follow_id=record.id, purpose=purpose, token_sha256=_hash(token), expires_at=clock.now() + lifetime
            )
        )
        await self.session.flush()
        return token

    async def _send(
        self,
        record: InventionFollowRecord,
        subject: str,
        body: str,
        update_id: UUID | None = None,
        *,
        html: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        reference = MailReference(
            kind="follow",
            id=record.id,
            expires_at=clock.now() + timedelta(hours=1),
            subjects=(update_id,) if update_id is not None else (),
        )
        await self.mailbox.send(
            self.session,
            to_email=record.email,
            subject=subject,
            body=body,
            html=html,
            headers=headers,
            reference=reference,
        )

    async def follow(self, request: FollowRequest, client_address: str) -> SubscribeResponse:
        """Store a pending follow and email a confirmation link; the answer never reveals what exists.

        An address that already follows gets a manage link instead.

        Args:
            request (FollowRequest): The invention, email and language.
            client_address (str): The caller's address, for the rate limit.

        Returns:
            SubscribeResponse: Always ``check_email``.

        Raises:
            MailUnavailableError: When this deployment sends no email.
            RateLimitedError: When one email or one address asks too often.
            NotFoundError: When the invention has no public page.
        """
        if isinstance(self.mailbox, DisabledMailbox):
            raise MailUnavailableError()
        invention = await _followable(self.session, request.invention_id)
        if invention is None:
            raise NotFoundError()
        email = request.email.lower()
        await rate_limit(self.session, email, client_address)
        record = await self.session.scalar(
            select(InventionFollowRecord).where(
                InventionFollowRecord.invention_id == request.invention_id, InventionFollowRecord.email == email
            )
        )
        if record is None:
            try:
                async with self.session.begin_nested():
                    record = InventionFollowRecord(
                        invention_id=request.invention_id, email=email, locale=request.locale
                    )
                    self.session.add(record)
                    await self.session.flush()
            except IntegrityError:
                # A parallel request for the same address won; it sent its own confirmation.
                return SubscribeResponse()
        origin = self.settings.web_origin
        if record.status == "ACTIVE":
            token = await self._link(record, "manage", MANAGE_LIFETIME)
            subject, body, html, headers = mail.already_following(
                origin, token, invention["title"], record.locale, demo=self.settings.demo_mode
            )
        else:
            record.status, record.locale = "PENDING", request.locale
            record.version += 1
            token = await self._link(record, "confirm", CONFIRM_LIFETIME)
            subject, body, html, headers = mail.follow_confirm(
                origin, token, invention["title"], request.locale, demo=self.settings.demo_mode
            )
        await self.session.flush()
        await self._send(record, subject, body, html=html, headers=headers)
        return SubscribeResponse()

    async def _by_token(self, token: str, purpose: str) -> tuple[InventionFollowRecord, InventionFollowLinkRecord]:
        link = await self.session.scalar(
            select(InventionFollowLinkRecord)
            .where(InventionFollowLinkRecord.token_sha256 == _hash(token))
            .with_for_update()
        )
        if link is None or link.purpose != purpose or link.expires_at <= clock.now():
            raise NotFoundError()
        record = await self.session.get(InventionFollowRecord, link.follow_id, with_for_update=True)
        if record is None:
            raise NotFoundError()
        return record, link

    async def _view(self, record: InventionFollowRecord, manage_token: str | None = None) -> FollowResponse:
        return FollowResponse(
            invention_id=record.invention_id,
            invention_title=await _title(self.session, record.invention_id),
            email=masked(record.email),
            status=record.status,  # type: ignore[arg-type]
            locale=record.locale,  # type: ignore[arg-type]
            confirmed_at=record.confirmed_at,
            manage_token=manage_token,
        )

    async def preview(self, token: str) -> FollowResponse:
        """Show what a confirmation link would confirm, without confirming; mail scanners may open links.

        Args:
            token (str): The confirmation token.

        Returns:
            FollowResponse: The follow.

        Raises:
            NotFoundError: For an unknown, used or expired link.
        """
        record, link = await self._by_token(token, "confirm")
        if link.used_at is not None:
            raise NotFoundError()
        return await self._view(record)

    async def confirm(self, token: str) -> FollowResponse:
        """Start following, by a deliberate POST; only updates first published from now on are sent.

        Args:
            token (str): The confirmation token.

        Returns:
            FollowResponse: The follow and a manage token.

        Raises:
            NotFoundError: For an unknown, used or expired link.
        """
        record, link = await self._by_token(token, "confirm")
        if link.used_at is not None:
            raise NotFoundError()
        link.used_at = clock.now()
        record.status, record.confirmed_at, record.unsubscribed_at = "ACTIVE", clock.now(), None
        record.version += 1
        await self.session.flush()
        return await self._view(record, await self._link(record, "manage", MANAGE_LIFETIME))

    async def read(self, token: str) -> FollowResponse:
        """Read a follow through a manage link.

        Args:
            token (str): The manage token.

        Returns:
            FollowResponse: The follow.
        """
        record, _ = await self._by_token(token, "manage")
        return await self._view(record)

    async def set_language(self, token: str, language: str) -> FollowResponse:
        """Change the language of future update emails.

        Args:
            token (str): The manage token.
            language (str): ``id`` or ``en``.

        Returns:
            FollowResponse: The follow.
        """
        record, _ = await self._by_token(token, "manage")
        if record.locale != language:
            record.locale = language
            record.version += 1
            await self.session.flush()
        return await self._view(record)

    async def unfollow(self, token: str) -> FollowResponse:
        """Stop updates for this invention to this email; queued emails are dropped before delivery.

        Args:
            token (str): A manage token.

        Returns:
            FollowResponse: The follow, ``UNSUBSCRIBED``.
        """
        record, _ = await self._by_token(token, "manage")
        if record.status != "UNSUBSCRIBED":
            record.status, record.unsubscribed_at = "UNSUBSCRIBED", clock.now()
            record.version += 1
            await self.session.flush()
        return await self._view(record)

    async def fan_out(self, update_id: UUID) -> int:
        """Email one newly published update to every follower who confirmed before it was published.

        The delivery row is written first and is unique per follower and update, so a retried event sends nothing
        twice.

        Args:
            update_id (UUID): The update.

        Returns:
            int: Emails queued.
        """
        update = await self.session.get(InventionUpdateRecord, update_id)
        if update is None or update.status != "PUBLISHED" or update.published_at is None:
            return 0
        invention = await _followable(self.session, update.invention_id)
        if invention is None:
            return 0
        # ponytail: one transaction for the whole fan-out; page through followers past about a thousand.
        followers = await self.session.scalars(
            select(InventionFollowRecord).where(
                InventionFollowRecord.invention_id == update.invention_id,
                InventionFollowRecord.status == "ACTIVE",
                InventionFollowRecord.confirmed_at <= update.published_at,
            )
        )
        sent = 0
        for record in list(followers):
            claimed = await self.session.scalar(
                insert(InventionFollowDeliveryRecord)
                .values(follow_id=record.id, update_id=update.id)
                .on_conflict_do_nothing(index_elements=["follow_id", "update_id"])
                .returning(InventionFollowDeliveryRecord.id)
            )
            if claimed is None:
                continue
            token = await self._link(record, "manage", MANAGE_LIFETIME)
            unsub_token = await mint_unsubscribe_token(self.session, "follow", record.id)
            subject, body, html, headers = mail.follow_update(
                self.settings,
                str(update.invention_id),
                invention["title"],
                update.title,
                update.body,
                token,
                record.locale,
                unsubscribe_token=unsub_token,
            )
            await self._send(record, subject, body, update.id, html=html, headers=headers)
            sent += 1
        return sent


@registry.consumer("invention.update_published", FANOUT_CONSUMER)
async def _fan_out(session: AsyncSession, payload: dict[str, Any]) -> None:
    await FollowService(session).fan_out(UUID(payload["update_id"]))
