"""Transactional mailbox port and development-only loopback relay."""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Protocol
from uuid import UUID, uuid4

from httpx import (
    AsyncClient,
    HTTPError,
    HTTPStatusError,
    InvalidURL,
    NetworkError,
    RemoteProtocolError,
    TimeoutException,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.core.errors import codes
from app.core.errors.base import AppError
from app.core.secret_envelope import seal
from app.core.settings import Settings
from app.identity.repository.sqlalchemy.models import MailboxMessageRecord
from app.platform.service.outbox import enqueue_job

SECRET_DELIVERY = "email.secret_delivery"
NOTIFICATION_DELIVERY = "email.notification_delivery"
SECRET_PURPOSE = "temuriset:email:delivery:v1"
SECRET_RETENTION = timedelta(minutes=10)
NOTIFICATION_RETRY_WINDOW = timedelta(minutes=15)
_REQUEST_TIMEOUT_SECONDS = 5.0
_MAX_MESSAGE_BYTES = 8192


@dataclass(frozen=True)
class MailReference:
    """Originating state that must remain usable at delivery time."""

    kind: Literal["code", "invitation"]
    id: UUID
    expires_at: datetime


class MailboxAdapter(Protocol):
    """Accepts one message in the caller's transaction."""

    async def send(
        self, session: AsyncSession, *, to_email: str, subject: str, body: str, reference: MailReference | None = None
    ) -> None:
        """Accept plain text mail, with the originating record for secret delivery."""


class DevelopmentMailbox:
    """Writes messages to ``mailbox_messages``, readable only in development and tests."""

    async def send(
        self, session: AsyncSession, *, to_email: str, subject: str, body: str, reference: MailReference | None = None
    ) -> None:
        """Store the message in the request's transaction."""
        session.add(MailboxMessageRecord(to_email=to_email, subject=subject, body=body))
        await session.flush()


class MailUnavailableError(AppError):
    """The deployment has no configured outbound email delivery."""

    code = codes.APP_MAIL_UNAVAILABLE


class MailRelayRetryError(AppError):
    """A relay attempt can safely be retried with the same idempotency key."""

    code = codes.APP_MAIL_RELAY_RETRY


class MailRelayRejectedError(AppError):
    """The relay or the delivery contract refused this message permanently."""

    code = codes.APP_MAIL_RELAY_REJECTED


class DisabledMailbox:
    """Fail before giving any caller a false delivery acknowledgement."""

    async def send(
        self, session: AsyncSession, *, to_email: str, subject: str, body: str, reference: MailReference | None = None
    ) -> None:
        """Refuse an email-dependent operation with a safe public error."""
        raise MailUnavailableError()


class LoopbackMailbox:
    """Queue encrypted material without contacting the relay inside the caller's transaction."""

    def __init__(self, key: str) -> None:
        """Bind the purpose-specific encryption key."""
        self.key = key

    async def send(
        self, session: AsyncSession, *, to_email: str, subject: str, body: str, reference: MailReference | None = None
    ) -> None:
        """Write the sealed message and deadline to a job in the caller's transaction."""
        if reference is None:
            raise MailRelayRejectedError()
        deadline = min(reference.expires_at, clock.now() + SECRET_RETENTION)
        delivery_key = uuid4().hex
        message = _message_bytes(
            {
                "to": to_email,
                "subject": subject,
                "body": body,
                "source_kind": reference.kind,
                "source_id": str(reference.id),
            }
        )
        envelope = seal(self.key, f"{SECRET_PURPOSE}:{delivery_key}", message)
        await enqueue_job(
            session,
            SECRET_DELIVERY,
            {"key": delivery_key, "envelope": envelope.decode("ascii")},
            input_expires_at=deadline,
        )


def loopback_mail_enabled(settings: Settings) -> bool:
    """Whether this validated deployment selected the loopback relay."""
    return settings.environment == "development" and settings.mailbox_adapter == "loopback-relay"


def mailbox_for(settings: Settings) -> MailboxAdapter:
    """Choose the deployment's validated outbound-mail mode."""
    if loopback_mail_enabled(settings):
        if settings.email_envelope_key is None:
            return DisabledMailbox()
        return LoopbackMailbox(settings.email_envelope_key.get_secret_value())
    return privacy_mailbox_for(settings)


def privacy_mailbox_for(settings: Settings) -> DevelopmentMailbox | DisabledMailbox:
    """Use only local storage or disabled behavior for an erasure receipt."""
    if settings.environment == "development" and settings.mailbox_adapter != "disabled":
        return DevelopmentMailbox()
    return DisabledMailbox()


def _message_bytes(fields: dict[str, str]) -> bytes:
    payload = json.dumps(fields, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > _MAX_MESSAGE_BYTES:
        raise MailRelayRejectedError()
    return payload


def _resolve_relay_failure(error: HTTPError | InvalidURL | TimeoutError) -> AppError:
    status = error.response.status_code if isinstance(error, HTTPStatusError) else None
    temporary = (
        isinstance(error, (NetworkError, RemoteProtocolError, TimeoutException, TimeoutError))
        or status == 429
        or (status is not None and 500 <= status <= 599)
    )
    failure = MailRelayRetryError() if temporary else MailRelayRejectedError()
    # Relay bodies and transport messages can echo message content. Keep only protocol facts.
    failure.debug_info["error_type"] = type(error).__name__
    failure.debug_info["original_message"] = f"Relay returned HTTP {status}." if status else "Relay request failed."
    return failure


async def deliver_to_relay(settings: Settings, *, delivery_key: str, to_email: str, subject: str, body: str) -> None:
    """Post one bounded text message. The relay deduplicates acceptance by delivery key."""
    if not loopback_mail_enabled(settings) or settings.email_relay_url is None or settings.email_relay_sender is None:
        raise MailUnavailableError()
    payload = _message_bytes(
        {"from": settings.email_relay_sender.get_secret_value(), "to": to_email, "subject": subject, "body": body}
    )
    try:
        async with (
            asyncio.timeout(_REQUEST_TIMEOUT_SECONDS),
            AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS, follow_redirects=False, trust_env=False) as client,
            client.stream(
                "POST",
                settings.email_relay_url.get_secret_value(),
                content=payload,
                headers={"Content-Type": "application/json", "Idempotency-Key": delivery_key},
            ) as response,
        ):
            response.raise_for_status()
    except (HTTPError, InvalidURL, TimeoutError) as error:
        raise _resolve_relay_failure(error) from error
