"""Email delivery port. Until spec 042 the only adapter writes to a development table."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

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
