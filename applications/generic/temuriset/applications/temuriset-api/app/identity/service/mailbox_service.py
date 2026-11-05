"""Email delivery port. Until spec 042 the only adapter writes to a development table."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import codes
from app.core.errors.base import AppError
from app.core.settings import Settings
from app.identity.repository.sqlalchemy.models import MailboxMessageRecord


class MailboxAdapter(Protocol):
    """Sends one message."""

    async def send(self, session: AsyncSession, *, to_email: str, subject: str, body: str) -> None:
        """Send a message.

        Args:
            session (AsyncSession): The request's session.
            to_email (str): Recipient.
            subject (str): Subject.
            body (str): Plain text body.
        """


class DevelopmentMailbox:
    """Writes messages to ``mailbox_messages``, readable only in development and tests."""

    async def send(self, session: AsyncSession, *, to_email: str, subject: str, body: str) -> None:
        """Store the message in the request's transaction.

        Args:
            session (AsyncSession): The request's session.
            to_email (str): Recipient.
            subject (str): Subject.
            body (str): Plain text body.
        """
        session.add(MailboxMessageRecord(to_email=to_email, subject=subject, body=body))
        await session.flush()


class MailUnavailableError(AppError):
    """The deployment has no configured outbound email delivery."""

    code = codes.APP_MAIL_UNAVAILABLE


class DisabledMailbox:
    """Fail before giving any caller a false delivery acknowledgement."""

    async def send(self, session: AsyncSession, *, to_email: str, subject: str, body: str) -> None:
        """Refuse an email-dependent operation with a safe public error."""
        raise MailUnavailableError()


def mailbox_for(settings: Settings) -> MailboxAdapter:
    """Choose the deployment's explicit outbound-mail mode."""
    if settings.mailbox_adapter == "development" and settings.environment == "development":
        return DevelopmentMailbox()
    return DisabledMailbox()
