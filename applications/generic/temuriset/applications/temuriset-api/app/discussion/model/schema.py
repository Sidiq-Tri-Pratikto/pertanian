"""Discussion requests and responses."""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.discussion.service.next_action import NextAction


class SendMessageRequest(BaseModel):
    """One message to the room."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class MessageResponse(BaseModel):
    """One message, with who wrote it."""

    id: UUID
    author_party_id: UUID
    author_name: str
    mine: bool
    text: str
    created_at: datetime
    operation_id: UUID | None = None


class CreateTaskRequest(BaseModel):
    """A clarification task for one of the two parties."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    owner_party_id: UUID
    due_date: date | None = None
    reference: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] = ""


class CompleteTaskRequest(BaseModel):
    """Mark a task done against the version the client saw."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int


class TaskResponse(BaseModel):
    """One task."""

    id: UUID
    title: str
    owner_party_id: UUID
    owner_name: str
    due_date: date | None
    reference: str
    status: Literal["OPEN", "DONE"]
    version: int
    created_at: datetime
    operation_id: UUID | None = None


class NotificationResponse(BaseModel):
    """One in-app notification."""

    id: UUID
    pitch_id: UUID | None
    text: str
    tab: str
    created_at: datetime
    read: bool


class QueueItem(NextAction):
    """One pitch waiting on someone, for Beranda."""

    pitch_id: UUID
    subject_title: str
    opportunity_title: str
    updated_at: datetime
