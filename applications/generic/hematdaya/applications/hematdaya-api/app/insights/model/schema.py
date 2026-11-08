"""Insight response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.locale import Locale
from app.energy.model.schema import WindowResponse


class PolicyResponse(BaseModel):
    """The versioned rule that produced the evidence."""

    id: str
    version: int


class InsightCopyResponse(BaseModel):
    """Text built from the snapshot."""

    title: str
    observed: str
    pct_note: str | None
    comparison: str
    unknown: str
    step: str


class FeedbackStateResponse(BaseModel):
    """The owner's feedback on this revision. A newer revision starts without it."""

    rating: str | None
    visibility: str
    until: datetime | None


class InsightResponse(BaseModel):
    """One observation at one revision. A superseded revision stays readable."""

    id: UUID
    revision: int
    current_revision: int
    kind: str
    direction: str
    asset_id: UUID
    active: bool
    superseded: bool
    generated_at: datetime
    policy: PolicyResponse
    evidence: dict[str, Any]
    text: InsightCopyResponse
    text_by_locale: dict[Locale, InsightCopyResponse] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    feedback: FeedbackStateResponse | None = None
    earlier_feedback: bool = False


class NoticeCopyResponse(BaseModel):
    """Localized presentation of a data notice."""

    title: str
    body: str


class NoticeResponse(BaseModel):
    """A data-quality notice, ranked apart from observations."""

    id: str
    kind: str
    asset_id: UUID | None
    title: str
    body: str
    copy_by_locale: dict[Locale, NoticeCopyResponse] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class InsightListResponse(BaseModel):
    """Active observations for a period, with notices and how many assets could be compared."""

    window: WindowResponse
    observations: list[InsightResponse]
    notices: list[NoticeResponse]
    learning_count: int
    comparable_count: int
    hidden_count: int = 0


class HiddenInsightsResponse(BaseModel):
    """Observations the owner hid or snoozed for a period, so they can be restored."""

    window: WindowResponse
    observations: list[InsightResponse]
