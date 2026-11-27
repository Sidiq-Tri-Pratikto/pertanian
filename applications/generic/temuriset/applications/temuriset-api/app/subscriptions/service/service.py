"""Quick subscriptions: double opt-in, manage links, topic alerts, the weekly digest and teasers (spec 046)."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.service import find_party
from app.core import clock
from app.core.errors.base import FieldsInvalidError, NotFoundError
from app.core.locale import locale
from app.core.settings import get_settings
from app.documents.service.public_image import CleanImage
from app.documents.service.service import public_image
from app.identity.service.mailbox_service import DisabledMailbox, MailReference, MailUnavailableError, mailbox_for
from app.identity.service.service import RateLimitedError, hash_address
from app.platform.service.outbox import enqueue_job
from app.portfolio.service.service import (
    PortfolioService,
    digest_candidates,
    public_page_settings,
)
from app.subscriptions.model.schema import (
    SubscribeRequest,
    SubscribeResponse,
    SubscriptionResponse,
    TeaserPhoto,
    TeaserResponse,
    Topics,
)
from app.subscriptions.repository.sqlalchemy.models import (
    InvestorSubscriptionRecord,
    SubscriptionLinkRecord,
    SubscriptionRequestRecord,
)
from app.subscriptions.repository.sqlalchemy.repository import SqlAlchemySubscriptionRepository
from app.subscriptions.service import mail
from app.subscriptions.service.matching import Match, match

DIGEST_JOB = "subscriptions.weekly_digest"
CONFIRM_LIFETIME = timedelta(days=7)
MANAGE_LIFETIME = timedelta(days=90)
ALERTS_PER_DAY = 3
DIGEST_ITEMS = 5
PER_EMAIL_PER_HOUR = 3
PER_ADDRESS_PER_HOUR = 20
# Monday 09:00 Asia/Jakarta is Monday 02:00 UTC.
_DIGEST_WEEKDAY, _DIGEST_HOUR_UTC = 0, 2


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def next_digest_at(now: datetime) -> datetime:
    """Return the next Monday 09:00 Asia/Jakarta after a moment.

    Args:
        now (datetime): Product time.

    Returns:
        datetime: The UTC instant.
    """
    base = now.astimezone(UTC).replace(hour=_DIGEST_HOUR_UTC, minute=0, second=0, microsecond=0)
    ahead = (_DIGEST_WEEKDAY - base.weekday()) % 7
    candidate = base + timedelta(days=ahead)
    return candidate if candidate > now else candidate + timedelta(days=7)


async def ensure_digest_scheduled(session: AsyncSession) -> None:
    """Queue the next weekly digest once; the job queues the following one itself (FR-006).

    Args:
        session (AsyncSession): The session.
    """
    at = next_digest_at(clock.now())
    await enqueue_job(session, DIGEST_JOB, {"at": at.isoformat()}, run_after=at, dedupe_key=f"digest:{at.date()}")


async def subscription_deliverable(session: AsyncSession, subscription_id: UUID, to_email: str) -> bool:
    """Whether a queued relay message may still go out: same email, not unsubscribed.

    Args:
        session (AsyncSession): The worker's session.
        subscription_id (UUID): The subscription.
        to_email (str): The address in the sealed message.

    Returns:
        bool: True when it may be delivered.
    """
    record = await SqlAlchemySubscriptionRepository(session).find(subscription_id)
    return record is not None and record.email == to_email and record.status != "UNSUBSCRIBED"


def masked(email: str) -> str:
    """Show enough of an email to recognize it.

    Args:
        email (str): The email.

    Returns:
        str: For example ``ra***@example.com``.
    """
    name, _, domain = email.partition("@")
    return f"{name[:2]}***@{domain}"


class SubscriptionService:
    """Everything a quick subscriber can do, without an account."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.settings = get_settings()
        self.repository = SqlAlchemySubscriptionRepository(session)
        self.mailbox = mailbox_for(self.settings)

    async def _link(self, record: InvestorSubscriptionRecord, purpose: str, lifetime: timedelta) -> str:
        token = secrets.token_urlsafe(32)
        await self.repository.add(
            SubscriptionLinkRecord(
                subscription_id=record.id,
                purpose=purpose,
                token_sha256=_hash(token),
                expires_at=clock.now() + lifetime,
            )
        )
        return token

    async def _send(self, record: InvestorSubscriptionRecord, subject: str, body: str) -> None:
        reference = MailReference(kind="subscription", id=record.id, expires_at=clock.now() + timedelta(hours=1))
        await self.mailbox.send(self.session, to_email=record.email, subject=subject, body=body, reference=reference)

    async def _rate_limit(self, email: str, client_address: str) -> None:
        now = clock.now()
        since = now - timedelta(hours=1)
        email_hash, address_hash = _hash(email), hash_address(client_address)
        for times, cap in (
            (await self.repository.requests_since(email_sha256=email_hash, since=since), PER_EMAIL_PER_HOUR),
            (await self.repository.requests_since(address_sha256=address_hash, since=since), PER_ADDRESS_PER_HOUR),
        ):
            if len(times) >= cap:
                raise RateLimitedError(max(int((times[0] + timedelta(hours=1) - now).total_seconds()) + 1, 1))
        await self.repository.add(SubscriptionRequestRecord(email_sha256=email_hash, address_sha256=address_hash))

    @staticmethod
    def _topics(topics: Topics) -> dict[str, Any]:
        if not (topics.sectors or topics.stages or topics.keywords):
            raise FieldsInvalidError(
                [
                    {
                        "loc": ["body", "topics"],
                        "msg": "Choose at least one sector, stage or keyword."
                        if locale() == "en"
                        else "Pilih setidaknya satu sektor, tahap, atau kata kunci.",
                        "type": "topics",
                    }
                ]
            )
        return {
            "sectors": list(dict.fromkeys(topics.sectors)),
            "stages": list(dict.fromkeys(topics.stages)),
            "keywords": list(dict.fromkeys(keyword.lower() for keyword in topics.keywords)),
        }

    async def subscribe(self, request: SubscribeRequest, client_address: str) -> SubscribeResponse:
        """Store a pending subscription and email a confirmation link. The answer never reveals what exists.

        An active subscription keeps its topics; its owner gets a manage link instead, so nobody else can change them.

        Args:
            request (SubscribeRequest): Email, topics and locale.
            client_address (str): The caller's address, for the rate limit.

        Returns:
            SubscribeResponse: Always ``check_email``.

        Raises:
            MailUnavailableError: When this deployment sends no email.
            RateLimitedError: When one email or one address asks too often.
            FieldsInvalidError: When no topic is chosen.
        """
        if isinstance(self.mailbox, DisabledMailbox):
            raise MailUnavailableError()
        topics = self._topics(request.topics)
        email = request.email.lower()
        await self._rate_limit(email, client_address)
        record = await self.repository.by_email(email)
        if record is None:
            try:
                async with self.session.begin_nested():
                    record = await self.repository.add(
                        InvestorSubscriptionRecord(email=email, topics=topics, locale=request.locale)
                    )
            except IntegrityError:
                # A parallel request for the same email won; it sent its own confirmation.
                return SubscribeResponse()
        if record.status == "ACTIVE":
            token = await self._link(record, "manage", MANAGE_LIFETIME)
            subject, body = mail.already_subscribed(self.settings.web_origin, token, record.locale)
        else:
            record.topics, record.status, record.locale = topics, "PENDING", request.locale
            record.version += 1
            token = await self._link(record, "confirm", CONFIRM_LIFETIME)
            subject, body = mail.confirm(self.settings.web_origin, token, topics, request.locale)
        await self.session.flush()
        await self._send(record, subject, body)
        return SubscribeResponse()

    async def _by_token(
        self, token: str, purposes: tuple[str, ...]
    ) -> tuple[InvestorSubscriptionRecord, SubscriptionLinkRecord]:
        link = await self.repository.link(_hash(token))
        if link is None or link.purpose not in purposes or link.expires_at <= clock.now():
            raise NotFoundError()
        if link.purpose == "confirm" and link.used_at is not None:
            raise NotFoundError()
        record = await self.repository.find(link.subscription_id)
        if record is None:
            raise NotFoundError()
        return record, link

    def _view(self, record: InvestorSubscriptionRecord, manage_token: str | None = None) -> SubscriptionResponse:
        return SubscriptionResponse(
            email=masked(record.email),
            topics=Topics.model_validate(record.topics),
            status=record.status,  # type: ignore[arg-type]
            confirmed_at=record.confirmed_at,
            manage_token=manage_token,
        )

    async def confirm(self, token: str) -> SubscriptionResponse:
        """Activate a subscription from its confirmation link, by a deliberate POST (FR-001).

        Args:
            token (str): The confirmation token.

        Returns:
            SubscriptionResponse: The subscription, with a manage token.

        Raises:
            NotFoundError: For an unknown, used or expired link.
        """
        record, link = await self._by_token(token, ("confirm",))
        link.used_at = clock.now()
        record.status, record.confirmed_at, record.unsubscribed_at = "ACTIVE", clock.now(), None
        record.version += 1
        await self.session.flush()
        await ensure_digest_scheduled(self.session)
        return self._view(record, await self._link(record, "manage", MANAGE_LIFETIME))

    async def read(self, token: str) -> SubscriptionResponse:
        """Read a subscription through a manage link.

        Args:
            token (str): The manage token.

        Returns:
            SubscriptionResponse: The subscription.
        """
        record, _ = await self._by_token(token, ("manage",))
        return self._view(record)

    async def update(self, token: str, topics: Topics) -> SubscriptionResponse:
        """Change topics through a manage link.

        Args:
            token (str): The manage token.
            topics (Topics): The new topics.

        Returns:
            SubscriptionResponse: The subscription.
        """
        record, _ = await self._by_token(token, ("manage",))
        record.topics = self._topics(topics)
        record.version += 1
        await self.session.flush()
        return self._view(record)

    async def unsubscribe(self, token: str) -> SubscriptionResponse:
        """Stop everything to this email; queued relay messages recheck this before going out.

        Args:
            token (str): A manage token.

        Returns:
            SubscriptionResponse: The subscription, ``UNSUBSCRIBED``.
        """
        record, _ = await self._by_token(token, ("manage",))
        if record.status != "UNSUBSCRIBED":
            record.status, record.unsubscribed_at = "UNSUBSCRIBED", clock.now()
            record.version += 1
            await self.session.flush()
        return self._view(record)

    async def _public(self, invention_id: UUID, gate: Literal["digest", "page"] = "digest") -> dict[str, Any] | None:
        """The public projection of an invention, or None when it must not be shown.

        ``digest`` (alerts and digests) needs the investor-alert switch; ``page`` (the signed-out page) needs either
        switch, so publishing the page never puts an invention into investor emails (051).
        """
        settings = await public_page_settings(self.session, invention_id)
        if settings is None:
            return None
        allowed = settings.investor_digest or (gate == "page" and settings.public_page)
        if not allowed:
            return None
        try:
            view = await PortfolioService(self.session).public_view(invention_id)
        except NotFoundError:
            return None
        party = await find_party(self.session, view.managing_party_id)
        anonymous = party is None or not party.profile_published
        return {
            "id": view.id,
            "title": view.title,
            "summary": view.summary,
            "sector": view.sector,
            "stage": view.stage,
            "keywords": view.keywords,
            "inventor_name": mail.ANONYMOUS_INVENTOR["id"] if anonymous else party.display_name,
            "anonymous": anonymous,
            "public_page": settings.public_page,
            "field_test": settings.public_field_test,
            "photo_version_id": settings.public_photo_version_id,
            "photo": (settings.public_photo_alt, settings.public_photo_width, settings.public_photo_height),
            "orientation": settings.public_photo_orientation or 1,
            "content_locale": settings.public_content_locale,
            "published_at": view.published_at,
        }

    async def teaser(self, invention_id: UUID) -> TeaserResponse:
        """What anyone may see of an included invention, signed out (US2).

        Args:
            invention_id (UUID): The invention.

        Returns:
            TeaserResponse: Title, summary, sector, stage, keywords and the inventor's public name.

        Raises:
            NotFoundError: When it is not published, not included, archived or suspended.
        """
        found = await self._public(invention_id, gate="page")
        if found is None:
            raise NotFoundError()
        page = found["public_page"]
        alt, width, height = found["photo"]
        photo = None
        # The photo and field-test summary belong to the public page; alerts alone show only the brief summary.
        if page and found["photo_version_id"] is not None and width and height:
            photo = TeaserPhoto(
                url=f"/api/v1/teasers/inventions/{invention_id}/photo?v={str(found['photo_version_id'])[:8]}",
                alt=alt or "",
                width=width,
                height=height,
                orientation=found["orientation"],
            )
        return TeaserResponse(
            id=found["id"],
            title=found["title"],
            summary=found["summary"],
            sector=found["sector"],
            stage=found["stage"],
            keywords=found["keywords"],
            inventor_name=mail.ANONYMOUS_INVENTOR[locale()] if found["anonymous"] else found["inventor_name"],
            published_at=found["published_at"],
            follow_enabled=page,
            field_test_summary=found["field_test"] if page else None,
            photo=photo,
            content_locale=found["content_locale"],
        )

    async def teaser_photo(self, invention_id: UUID) -> CleanImage:
        """The public page's photo without metadata; checked again on every request (051).

        Args:
            invention_id (UUID): The invention.

        Returns:
            CleanImage: The photo bytes and media type.

        Raises:
            NotFoundError: When the page is off, the invention is not public, or the photo is gone.
        """
        found = await self._public(invention_id, gate="page")
        if found is None or not found["public_page"] or found["photo_version_id"] is None:
            raise NotFoundError()
        image = await public_image(self.session, found["photo_version_id"])
        if image is None:
            raise NotFoundError()
        return image

    async def alert(self, invention_id: UUID) -> int:
        """Send a direct alert to every active subscriber whose topics all match, within the daily cap (FR-005).

        Args:
            invention_id (UUID): A newly published or newly included invention.

        Returns:
            int: Alerts sent.
        """
        invention = await self._public(invention_id)
        if invention is None:
            return 0
        now, sent = clock.now(), 0
        for record in await self.repository.active():
            found = match(record.topics, invention, record.locale)
            if found is None or found.level != "ALERT":
                continue
            if await self.repository.alerts_since(record.id, now - timedelta(days=1)) >= ALERTS_PER_DAY:
                continue
            if not await self.repository.record_delivery(record.id, invention_id, "ALERT", now):
                continue
            token = await self._link(record, "manage", MANAGE_LIFETIME)
            subject, body = mail.alert(self.settings, invention, found, record, token)
            await self._send(record, subject, body)
            sent += 1
        return sent

    async def digest(self) -> int:
        """Send each active subscriber one digest of up to five matching inventions it has not received.

        Returns:
            int: Digests sent; a subscriber with nothing new gets no email.
        """
        now = clock.now()
        candidates = []
        for invention_id in await digest_candidates(self.session, now - timedelta(days=7)):
            found = await self._public(invention_id)
            if found is not None:
                candidates.append(found)
        sent = 0
        for record in await self.repository.active():
            done = await self.repository.delivered(record.id)
            picked: list[tuple[dict[str, Any], Match]] = []
            for invention in candidates:
                found = match(record.topics, invention, record.locale)
                if found is not None and invention["id"] not in done:
                    picked.append((invention, found))
            picked.sort(key=lambda pair: pair[1].level != "ALERT")
            items = []
            for invention, found in picked[:DIGEST_ITEMS]:
                if await self.repository.record_delivery(record.id, invention["id"], "DIGEST", now):
                    items.append((invention, found))
            if not items:
                continue
            token = await self._link(record, "manage", MANAGE_LIFETIME)
            subject, body = mail.digest(self.settings, items, record, token)
            await self._send(record, subject, body)
            sent += 1
        return sent
