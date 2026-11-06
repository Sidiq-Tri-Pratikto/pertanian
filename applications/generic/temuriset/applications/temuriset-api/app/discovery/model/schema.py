"""Discovery requests and responses."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel

ResultType = Literal["inventions", "funding", "partners"]
SubjectType = Literal["INVENTION", "FUNDING_REQUEST", "PARTNER"]
SectionId = Literal["relevant", "new", "curated"]

SUBJECT_OF: dict[str, str] = {"inventions": "INVENTION", "funding": "FUNDING_REQUEST", "partners": "PARTNER"}


class DiscoveryItem(BaseModel):
    """One result card. ``card`` holds what the owner published, by subject type."""

    subject_type: SubjectType
    subject_id: UUID
    title: str
    card: dict[str, Any]
    curated: bool
    saved: bool
    reasons: list[str]


class DiscoverySection(BaseModel):
    """A labelled group of results. No section is ever ordered by activity."""

    id: SectionId
    title: str
    items: list[DiscoveryItem]


class Relaxation(BaseModel):
    """A filter to remove deliberately when nothing matched; the search is never broadened by itself."""

    remove: str
    label: str
    total_estimate: int


class DiscoveryResponse(BaseModel):
    """One page of discovery results, with the filters that produced it."""

    type: ResultType
    sections: list[DiscoverySection]
    filters: dict[str, Any]
    next_cursor: str | None
    total_estimate: int
    relaxation: Relaxation | None


class MarkedItem(BaseModel):
    """A saved or hidden subject."""

    subject_type: SubjectType
    subject_id: UUID
