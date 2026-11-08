"""Persisted scope selection models."""

from uuid import UUID

from pydantic import BaseModel


class AggregationSelectionModel(BaseModel):
    """One site's confirmed asset IDs and independent revision."""

    site_id: UUID
    asset_ids: list[UUID]
    revision: int
