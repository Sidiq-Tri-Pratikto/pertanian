"""Insight domain models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

POLICY_ID = "change"
POLICY_VERSION = 1


class InsightModel(BaseModel):
    """A stable observation identity: one kind, asset and period within a site."""

    id: UUID
    site_id: UUID
    kind: str
    asset_id: UUID
    period_start: datetime
    period_end: datetime
    identity_key: str
    current_revision: int
    active: bool


class InsightRevisionModel(BaseModel):
    """One frozen evidence snapshot."""

    insight_id: UUID
    revision: int
    evidence: dict[str, Any]
    evidence_hash: str
    policy_id: str
    policy_version: int
    generated_at: datetime
    superseded_at: datetime | None


class Candidate(BaseModel):
    """An observation the rules produced for the current inputs."""

    identity_key: str
    kind: str
    asset_id: UUID
    period_start: datetime
    period_end: datetime
    evidence: dict[str, Any]
    evidence_hash: str
    delta_mwh_sort: float
