"""Shared suspension checks for public projections and new listing actions."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import codes
from app.core.errors.base import AppError
from app.moderation.repository.sqlalchemy.repository import SqlAlchemyModerationRepository


class ListingSuspendedError(AppError):
    """A new action is blocked while a listing is suspended."""

    code = codes.APP_LISTING_SUSPENDED


async def is_suspended(session: AsyncSession, subject_type: str, subject_id: UUID) -> bool:
    """Return whether a suspension is currently active for the listing."""
    return await SqlAlchemyModerationRepository(session).active_suspension(subject_type, subject_id) is not None


async def require_unsuspended(session: AsyncSession, subject_type: str, subject_id: UUID) -> None:
    """Guard new actions while preserving access to ongoing work."""
    if await is_suspended(session, subject_type, subject_id):
        raise ListingSuspendedError()


async def suspended_listings(session: AsyncSession, subject_type: str, ids: list[UUID]) -> set[UUID]:
    """Return suspended members of a batch for a public list."""
    return await SqlAlchemyModerationRepository(session).suspended_among(subject_type, ids)
