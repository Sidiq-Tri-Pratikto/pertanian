"""Feedback request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.feedback.model.models import FeedbackAction, Visibility


class FeedbackRequest(BaseModel):
    """One action on one evidence revision."""

    action: FeedbackAction
    revision: int = Field(ge=1)


class FeedbackResponse(BaseModel):
    """The confirmed state of that revision for the owner."""

    insight_id: UUID
    revision: int
    action: FeedbackAction
    rating: str | None
    visibility: Visibility
    until: datetime | None
