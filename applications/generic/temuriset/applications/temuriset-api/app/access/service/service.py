"""Parties and, from spec 007, organizations, memberships and invitations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.repository.sqlalchemy.models import PartyRecord


async def create_personal_party(session: AsyncSession, *, account_id: UUID, display_name: str) -> UUID:
    """Create the one personal party of an account, in the caller's transaction.

    Args:
        session (AsyncSession): The request's session.
        account_id (UUID): The account.
        display_name (str): Shown wherever the party acts.

    Returns:
        UUID: The party id.
    """
    record = PartyRecord(kind="personal", display_name=display_name, account_id=account_id)
    session.add(record)
    await session.flush()
    return record.id


async def personal_party_id(session: AsyncSession, account_id: UUID) -> UUID:
    """Return the personal party of an account.

    Args:
        session (AsyncSession): The request's session.
        account_id (UUID): The account.

    Returns:
        UUID: The party id.
    """
    party_id = await session.scalar(select(PartyRecord.id).where(PartyRecord.account_id == account_id))
    assert party_id is not None, "every verified account has a personal party"  # noqa: S101
    return party_id
