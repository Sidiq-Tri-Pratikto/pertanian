"""Insight response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

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


class NoticeResponse(BaseModel):
    """A data-quality notice, ranked apart from observations."""

    id: str
    kind: str
    asset_id: UUID | None
    title: str
    body: str


class InsightListResponse(BaseModel):
    """Active observations for a period, with notices and how many assets could be compared."""

    window: WindowResponse
    observations: list[InsightResponse]
    notices: list[NoticeResponse]
    learning_count: int
    comparable_count: int
