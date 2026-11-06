"""The port through which the owner's feedback decides what a list shows. The feedback module implements it."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel


class FeedbackView(BaseModel):
    """The owner's feedback on one revision."""

    revision: int
    rating: str | None
    visibility: str
    until: datetime | None


class VisibilityReader(Protocol):
    """Reads feedback without the insights module depending on how it is stored."""

    async def feedback(self, principal_id: UUID, insight_ids: list[UUID]) -> dict[UUID, list[FeedbackView]]:
        """Return the owner's feedback on every revision of these insights."""
        ...
