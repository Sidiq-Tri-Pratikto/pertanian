"""Account facts other modules may read, without reaching into the identity repository."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.repository.sqlalchemy.repository import SqlAlchemyIdentityRepository


async def account_email(session: AsyncSession, account_id: UUID) -> str:
    """Return an account's normalized email.

    Args:
        session (AsyncSession): The request's session.
        account_id (UUID): The account.

    Returns:
        str: The email.
    """
    account = await SqlAlchemyIdentityRepository(session).find_account(account_id)
    assert account is not None  # noqa: S101 - callers pass a signed-in or member account
    return account.email


async def display_names(session: AsyncSession, account_ids: list[UUID]) -> dict[UUID, str]:
    """Return display names for accounts.

    Args:
        session (AsyncSession): The request's session.
        account_ids (list[UUID]): The accounts.

    Returns:
        dict[UUID, str]: Name per account.
    """
    repository = SqlAlchemyIdentityRepository(session)
    names = {}
    for account_id in account_ids:
        account = await repository.find_account(account_id)
        if account is not None:
            names[account_id] = account.display_name
    return names


async def account_is_active(session: AsyncSession, account_id: UUID) -> bool:
    """Recheck a recorded requester without depending on a browser session."""
    return await SqlAlchemyIdentityRepository(session).is_account_active(account_id)


async def email_notification_accounts(session: AsyncSession, account_ids: list[UUID]) -> list[UUID]:
    """Return candidate IDs that opted in and hold verified, active, non-demo accounts."""
    return await SqlAlchemyIdentityRepository(session).email_notification_accounts(account_ids)


async def email_notification_address(session: AsyncSession, account_id: UUID) -> str | None:
    """Read the address just before send, while the account remains eligible."""
    return await SqlAlchemyIdentityRepository(session).email_notification_address(account_id)


async def account_is_demo(session: AsyncSession, account_id: UUID) -> bool:
    """Check the stored demo classification of a signed-in account."""
    account = await SqlAlchemyIdentityRepository(session).find_account(account_id)
    return account is not None and account.kind == "demo"
