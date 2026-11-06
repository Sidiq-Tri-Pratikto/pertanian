"""Relationship state per pitch, for whose turn it is (027). It imports no pitch or discussion service."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.relationships.repository.sqlalchemy.repository import SqlAlchemyRelationshipRepository


async def partnership_states(session: AsyncSession, pitch_ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
    """Read each pitch's relationship: current version number, status and who confirmed it.

    Args:
        session (AsyncSession): The request's session.
        pitch_ids (list[UUID]): Pitches.

    Returns:
        dict[UUID, dict[str, Any]]: ``ScheduleState`` fields per pitch that has a relationship.
    """
    if not pitch_ids:
        return {}
    repository = SqlAlchemyRelationshipRepository(session)
    partnerships = await repository.of_pitches(pitch_ids)
    if not partnerships:
        return {}
    versions = await repository.versions([partnership.id for partnership in partnerships])
    current = {version.partnership_id: version for version in versions}
    confirmations = await repository.confirmations([version.id for version in current.values()])
    states = {}
    for partnership in partnerships:
        version = current[partnership.id]
        states[partnership.pitch_id] = {
            "partnership_number": version.number,
            "partnership_status": version.status,
            "partnership_confirmed_by": frozenset(
                item.party_id for item in confirmations if item.version_id == version.id
            ),
        }
    return states
