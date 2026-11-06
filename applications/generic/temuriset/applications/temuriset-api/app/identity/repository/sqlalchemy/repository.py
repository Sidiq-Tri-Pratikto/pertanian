"""Identity data access. Writes join the caller's transaction."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.identity.model.models import AccountModel, EmailCodeModel, SessionModel
from app.identity.repository.sqlalchemy.models import (
    AccountRecord,
    EmailCodeRecord,
    MailboxMessageRecord,
    SessionRecord,
)


def _account(record: AccountRecord) -> AccountModel:
    return AccountModel.model_validate(record, from_attributes=True)


def _email_eligible() -> tuple[ColumnElement[bool], ...]:
    return (
        AccountRecord.email_notifications.is_(True),
        AccountRecord.email_verified_at.is_not(None),
        AccountRecord.status == "active",
        AccountRecord.kind == "user",
    )


class SqlAlchemyIdentityRepository:
    """Accounts, codes, sessions and mailbox over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to a session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def find_account_by_email(self, email: str, *, lock: bool = False) -> AccountModel | None:
        """Find an account by normalized email.

        Args:
            email (str): Trimmed, lower-case email.

        Returns:
            AccountModel | None: The account.
        """
        query = select(AccountRecord).where(AccountRecord.email == email)
        record = await self.session.scalar(query.with_for_update() if lock else query)
        return _account(record) if record is not None else None

    async def find_account(self, account_id: UUID, *, lock: bool = False) -> AccountModel | None:
        """Find an account by id.

        Args:
            account_id (UUID): The account.

        Returns:
            AccountModel | None: The account.
        """
        record = await self.session.get(AccountRecord, account_id, with_for_update=lock)
        return _account(record) if record is not None else None

    async def is_account_active(self, account_id: UUID) -> bool:
        """Read the current account status for work authorized outside the session."""
        status = await self.session.scalar(select(AccountRecord.status).where(AccountRecord.id == account_id))
        return status == "active"

    async def email_notification_accounts(self, account_ids: list[UUID]) -> list[UUID]:
        """Resolve opted-in account IDs without loading any email addresses."""
        if not account_ids:
            return []
        return list(
            await self.session.scalars(
                select(AccountRecord.id).where(*_email_eligible(), AccountRecord.id.in_(account_ids))
            )
        )

    async def email_notification_address(self, account_id: UUID) -> str | None:
        """Return an address only while the account is eligible for optional email."""
        return await self.session.scalar(
            select(AccountRecord.email).where(*_email_eligible(), AccountRecord.id == account_id)
        )

    async def create_account(self, **values: Any) -> AccountModel:
        """Insert an account.

        Args:
            **values (Any): Column values.

        Returns:
            AccountModel: The account.
        """
        record = AccountRecord(**values)
        self.session.add(record)
        await self.session.flush()
        return _account(record)

    async def update_account(self, account_id: UUID, expected_version: int, **values: Any) -> AccountModel | None:
        """Change an account only if it is still at ``expected_version``.

        Args:
            account_id (UUID): The account.
            expected_version (int): The version the client changed.
            **values (Any): Column values.

        Returns:
            AccountModel | None: The updated account, or None when the version moved on.
        """
        record = await self.session.scalar(
            update(AccountRecord)
            .where(AccountRecord.id == account_id, AccountRecord.version == expected_version)
            .values(version=AccountRecord.version + 1, **values)
            .returning(AccountRecord)
        )
        return _account(record) if record is not None else None

    async def count_codes(self, *, since: datetime, email: str | None = None, address_sha256: str | None = None) -> int:
        """Count code requests in a window, by email or by client address.

        Args:
            since (datetime): Window start.
            email (str | None, optional): Normalized email. Defaults to None.
            address_sha256 (str | None, optional): Hashed client address. Defaults to None.

        Returns:
            int: Requests in the window.
        """
        query = select(func.count()).select_from(EmailCodeRecord).where(EmailCodeRecord.created_at > since)
        if email is not None:
            query = query.where(EmailCodeRecord.email == email)
        if address_sha256 is not None:
            query = query.where(EmailCodeRecord.requester_address_sha256 == address_sha256)
        return await self.session.scalar(query) or 0

    async def oldest_code_time(self, *, since: datetime, email: str | None, address_sha256: str | None) -> datetime:
        """Return when the oldest request in the window was made, to say when the window frees up.

        Args:
            since (datetime): Window start.
            email (str | None): Normalized email, or None.
            address_sha256 (str | None): Hashed client address, or None.

        Returns:
            datetime: The oldest request time.
        """
        query = select(func.min(EmailCodeRecord.created_at)).where(EmailCodeRecord.created_at > since)
        if email is not None:
            query = query.where(EmailCodeRecord.email == email)
        if address_sha256 is not None:
            query = query.where(EmailCodeRecord.requester_address_sha256 == address_sha256)
        oldest = await self.session.scalar(query)
        assert oldest is not None  # noqa: S101 - only called when the window holds requests
        return oldest

    async def add_code(self, **values: Any) -> UUID:
        """Store a code.

        Args:
            **values (Any): Column values.
        """
        record = EmailCodeRecord(**values)
        self.session.add(record)
        await self.session.flush()
        return record.id

    async def latest_open_code(self, email: str) -> EmailCodeModel | None:
        """Lock the newest unconsumed code for an email.

        Args:
            email (str): Normalized email.

        Returns:
            EmailCodeModel | None: The code, locked for this transaction.
        """
        record = await self.session.scalar(
            select(EmailCodeRecord)
            .where(EmailCodeRecord.email == email, EmailCodeRecord.consumed_at.is_(None))
            .order_by(EmailCodeRecord.created_at.desc())
            .limit(1)
            .with_for_update()
        )
        return EmailCodeModel.model_validate(record, from_attributes=True) if record is not None else None

    async def count_attempt(self, code_id: UUID) -> None:
        """Record one wrong guess.

        Args:
            code_id (UUID): The code.
        """
        await self.session.execute(
            update(EmailCodeRecord).where(EmailCodeRecord.id == code_id).values(attempts=EmailCodeRecord.attempts + 1)
        )

    async def consume_codes(self, email: str, now: datetime) -> None:
        """Retire every open code for an email once one is used.

        Args:
            email (str): Normalized email.
            now (datetime): Product time.
        """
        await self.session.execute(
            update(EmailCodeRecord)
            .where(EmailCodeRecord.email == email, EmailCodeRecord.consumed_at.is_(None))
            .values(consumed_at=now)
        )

    async def add_session(self, **values: Any) -> None:
        """Store a session.

        Args:
            **values (Any): Column values.
        """
        self.session.add(SessionRecord(**values))
        await self.session.flush()

    async def find_live_session(self, token_sha256: str, now: datetime) -> SessionModel | None:
        """Find an unrevoked, unexpired session by token hash.

        Args:
            token_sha256 (str): Hashed token.
            now (datetime): Product time.

        Returns:
            SessionModel | None: The session.
        """
        record = await self.session.scalar(
            select(SessionRecord).where(
                SessionRecord.token_sha256 == token_sha256,
                SessionRecord.revoked_at.is_(None),
                SessionRecord.expires_at > now,
            )
        )
        return SessionModel.model_validate(record, from_attributes=True) if record is not None else None

    async def update_session(self, session_id: UUID, **values: Any) -> None:
        """Change a session.

        Args:
            session_id (UUID): The session.
            **values (Any): Column values.
        """
        await self.session.execute(update(SessionRecord).where(SessionRecord.id == session_id).values(**values))

    async def remove_sign_in_records(self, account_id: UUID, email: str) -> None:
        """Remove the account's login credentials and previously issued development messages."""
        await self.session.execute(delete(SessionRecord).where(SessionRecord.account_id == account_id))
        await self.session.execute(delete(EmailCodeRecord).where(EmailCodeRecord.email == email))
        await self.session.execute(delete(MailboxMessageRecord).where(MailboxMessageRecord.to_email == email))

    async def mailbox(self, email: str, limit: int = 10) -> list[MailboxMessageRecord]:
        """Read the newest development mailbox messages for an email.

        Args:
            email (str): Normalized email.
            limit (int, optional): Maximum messages. Defaults to 10.

        Returns:
            list[MailboxMessageRecord]: Newest first.
        """
        rows = await self.session.scalars(
            select(MailboxMessageRecord)
            .where(MailboxMessageRecord.to_email == email)
            .order_by(MailboxMessageRecord.created_at.desc())
            .limit(limit)
        )
        return list(rows)
