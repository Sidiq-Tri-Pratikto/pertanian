"""When an open proposal expires: at 72 hours of age, or when every slot has started (policy ``proposal-expiry`` v1)."""

from datetime import datetime, timedelta

from app.scheduling.repository.sqlalchemy.models import ScheduleProposalRecord, ScheduleSlotRecord

PROPOSAL_LIFETIME = timedelta(hours=72)


def expires_at(proposal: ScheduleProposalRecord, slots: list[ScheduleSlotRecord]) -> datetime:
    """Return when a proposal stops being open, whichever comes first.

    Args:
        proposal (ScheduleProposalRecord): The proposal.
        slots (list[ScheduleSlotRecord]): Its slots.

    Returns:
        datetime: The instant.
    """
    return min([proposal.created_at + PROPOSAL_LIFETIME, *[slot.starts_at for slot in slots]] or [proposal.created_at])


def expire_if_due(proposal: ScheduleProposalRecord, slots: list[ScheduleSlotRecord], now: datetime) -> bool:
    """Expire an open proposal whose time is up. The pitch stays approved for discussion either way.

    Args:
        proposal (ScheduleProposalRecord): The proposal.
        slots (list[ScheduleSlotRecord]): Its slots.
        now (datetime): Product time.

    Returns:
        bool: Whether it changed.
    """
    if proposal.state != "OPEN":
        return False
    if now - proposal.created_at >= PROPOSAL_LIFETIME:
        proposal.expired_reason = "AGE"
    elif slots and all(slot.starts_at <= now for slot in slots):
        proposal.expired_reason = "ALL_PAST"
    else:
        return False
    proposal.state = "EXPIRED"
    proposal.version += 1
    return True
