"""Feedback domain models."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class FeedbackAction(StrEnum):
    """What the owner said about one evidence revision. None of them touches data or equipment."""

    USEFUL = "useful"
    NOT_RELEVANT = "not_relevant"
    SNOOZE = "snooze"
    HIDE = "hide"
    RESTORE = "restore"


class Visibility(StrEnum):
    """Whether a revision shows in the owner's list."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    SNOOZED = "snoozed"


class FeedbackStateModel(BaseModel):
    """The owner's current feedback on one revision."""

    insight_id: UUID
    revision: int
    rating: str | None
    visibility: Visibility
    until: datetime | None


class FeedbackOperationModel(BaseModel):
    """One idempotent request, bound to its payload and original outcome."""

    insight_id: UUID
    revision: int
    action: FeedbackAction
    response: dict[str, Any] | None
