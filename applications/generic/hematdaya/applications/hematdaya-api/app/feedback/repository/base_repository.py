"""Feedback storage interface."""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.feedback.model.models import FeedbackAction, FeedbackOperationModel, FeedbackStateModel


class FeedbackRepository(ABC):
    """Stores feedback state per revision and owner, and the idempotent operations that changed it."""

    @abstractmethod
    async def claim(
        self, principal_id: UUID, key: str, insight_id: UUID, revision: int, action: FeedbackAction
    ) -> bool:
        """Reserve a key for one payload; False when the key already exists."""

    @abstractmethod
    async def operation(self, principal_id: UUID, key: str) -> FeedbackOperationModel:
        """Return a claimed operation."""

    @abstractmethod
    async def complete(self, principal_id: UUID, key: str, response: dict[str, Any]) -> None:
        """Store an operation's outcome."""

    @abstractmethod
    async def states(self, principal_id: UUID, insight_ids: list[UUID]) -> list[FeedbackStateModel]:
        """Return the owner's feedback on every revision of these insights."""

    @abstractmethod
    async def save(self, principal_id: UUID, state: FeedbackStateModel) -> None:
        """Insert or replace the owner's feedback on one revision."""
