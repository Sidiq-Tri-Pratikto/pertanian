"""Scheduling requests and responses. Every instant is UTC; screens format it in each viewer's zone."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import available_timezones

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

_ZONES = frozenset(available_timezones())


def _zone(value: str) -> str:
    if value not in _ZONES:
        raise ValueError("Pilih zona waktu IANA, misalnya Asia/Jakarta.")
    return value


TimeZone = Annotated[str, AfterValidator(_zone)]
HttpsLink = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500, pattern=r"^https://\S+$")]


class ProposeRequest(BaseModel):
    """Offer 2–5 times for one meeting, or for a replacement of a confirmed one."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    slots: Annotated[list[AwareDatetime], Field(min_length=2, max_length=5)]
    minutes: Literal[30, 60]
    time_zone: TimeZone
    agenda: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    link: HttpsLink | None = None
    replaces_meeting_id: UUID | None = None


class AcceptRequest(BaseModel):
    """Confirm one slot of the proposal version the client saw."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    slot_id: UUID
    expected_version: int


class VersionedRequest(BaseModel):
    """A change against the version the client saw."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int


class OutcomeRequest(BaseModel):
    """What the acting party says happened."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    result: Literal["COMPLETED", "NO_SHOW"]
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""


class SlotResponse(BaseModel):
    """One offered interval."""

    id: UUID
    position: int
    starts_at: datetime
    ends_at: datetime


class ProposalResponse(BaseModel):
    """A proposal and its state, with expiry evaluated on read."""

    id: UUID
    proposed_by_party_id: UUID
    proposed_by_name: str
    mine: bool
    minutes: int
    time_zone: str
    agenda: str
    link: str | None
    state: Literal["OPEN", "ACCEPTED", "SUPERSEDED", "EXPIRED", "CANCELLED"]
    expired_reason: Literal["AGE", "ALL_PAST"] | None
    replaces_meeting_id: UUID | None
    accepted_slot_id: UUID | None
    version: int
    created_at: datetime
    expires_at: datetime
    slots: list[SlotResponse]
    operation_id: UUID | None = None


class OutcomeResponse(BaseModel):
    """One party's outcome."""

    party_id: UUID
    party_name: str
    result: Literal["COMPLETED", "NO_SHOW"]
    note: str


class MeetingResponse(BaseModel):
    """A meeting with each party's outcome."""

    id: UUID
    proposal_id: UUID
    starts_at: datetime
    ends_at: datetime
    time_zone: str
    agenda: str
    link: str | None
    state: Literal["CONFIRMED", "COMPLETED", "CANCELLED", "NO_SHOW_REPORTED"]
    version: int
    started: bool
    outcomes: list[OutcomeResponse]
    disagreement: bool = Field(description="Both parties recorded outcomes that differ; it stays visible.")
    operation_id: UUID | None = None


class ScheduleResponse(BaseModel):
    """Everything scheduled for one pitch."""

    proposals: list[ProposalResponse]
    meetings: list[MeetingResponse]
    can_schedule: bool
    external_calendar: Literal["unknown"] = Field(
        default="unknown", description="No calendar is connected, so outside availability is unknown (AC68)."
    )
