"""Scheduling state per pitch, for whose turn it is (027). It imports no pitch or discussion service."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.discussion.service.next_action import ScheduleState
from app.scheduling.repository.sqlalchemy.repository import SqlAlchemySchedulingRepository
from app.scheduling.service.expiry import expire_if_due


async def schedule_states(session: AsyncSession, pitch_ids: list[UUID]) -> dict[UUID, ScheduleState]:
    """Read open proposals and meetings of pitches, expiring proposals whose time is up.

    Args:
        session (AsyncSession): The request's session.
        pitch_ids (list[UUID]): Pitches.

    Returns:
        dict[UUID, ScheduleState]: State per pitch that has a proposal or a meeting.
    """
    if not pitch_ids:
        return {}
    repository = SqlAlchemySchedulingRepository(session)
    now = clock.now()
    proposals = await repository.proposals(pitch_ids)
    slots = defaultdict(list)
    for slot in await repository.slots([proposal.id for proposal in proposals if proposal.state == "OPEN"]):
        slots[slot.proposal_id].append(slot)
    meetings = await repository.meetings(pitch_ids)
    outcomes = defaultdict(set)
    for outcome in await repository.outcomes([meeting.id for meeting in meetings if meeting.state == "CONFIRMED"]):
        outcomes[outcome.meeting_id].add(outcome.party_id)
    states: dict[UUID, ScheduleState] = {}
    for pitch_id in pitch_ids:
        open_by = next(
            (
                proposal.proposed_by_party_id
                for proposal in proposals
                if proposal.pitch_id == pitch_id
                and not expire_if_due(proposal, slots[proposal.id], now)
                and proposal.state == "OPEN"
            ),
            None,
        )
        mine = [meeting for meeting in meetings if meeting.pitch_id == pitch_id]
        confirmed = next((meeting for meeting in mine if meeting.state == "CONFIRMED"), None)
        completed = any(meeting.state == "COMPLETED" for meeting in mine)
        if open_by or confirmed or completed:
            states[pitch_id] = ScheduleState(
                open_proposal_by=open_by,
                meeting_starts_passed=None if confirmed is None else confirmed.starts_at <= now,
                outcomes_by=frozenset(outcomes[confirmed.id]) if confirmed else frozenset(),
                completed=completed,
            )
    await session.flush()
    return states
